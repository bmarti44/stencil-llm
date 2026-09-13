# ruff: noqa: E501
"""Six-family candidate-A screen: stateful contract sessions, packing policy, scoring.

Registered in ``results/a-screen/REGISTRATION-A-SCREEN.md`` (2026-09-13; amendment 1 after
the Astra implementation review of the same day).  A :class:`Session` is a small Python
package, a frozen 16-turn prefix, a lifecycle event message and two live coding
:class:`Request` objects.  The target contract family has two states; ``state_at`` says
which is in force at each live checkpoint.  A supporting contract is stated once in the
prefix and never changes.

Prompt packing (registration §5, amendment 1): system line + the newest whole turns that
fit in ``PROMPT_BUDGET`` tokens.  Compaction evicts a superseded request and its reply
first (their result is already carried by the live request's file listing), then the oldest
remaining turns; the system line and the live request are never evicted.  Nothing is summarised and no current-rule answer is inserted.  The
history at request 2 is the ORIGINAL request-1 message (the files exactly as that request
showed them, Astra F2), the arm's verbatim first reply, the lifecycle event, and a
request-2 message carrying the CURRENT content of the files changed since request 1.
:func:`required_indices` names what must survive packing: every rule turn, the event and
the live request.  The earlier request and reply are ordinary history and may be evicted
when a reply is long; because the current repository state travels in the request-2
message, nothing the model needs to extend is lost (Astra F1).
``tests/test_a_screen.py`` qualifies every session at the permitted maximum reply length.

Outcome (registration §6, amendment 1 for Astra F7): at each checkpoint the functional,
regression, applicable target-contract and support-contract suites run independently in
a sandbox (:func:`stencil.contracts.run_tests`); at checkpoint 2 the request-1 suites
(functional, its contract under the state then in force, support) run again as the
PROTECTED suite, so an earlier operation that is renamed, re-validated or otherwise
altered by the second edit fails.  The session's ``J`` is 1 only if every suite passes at
both checkpoints.
"""

from __future__ import annotations

import hashlib
import json
import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from pathlib import Path

from stencil.contracts import extract_file, run_tests

MAX_NEW_TOKENS = 1536  # registered cap
PROMPT_BUDGET = 2560  # 4096 - MAX_NEW_TOKENS
SYSTEM = (
    "You are a careful software engineer maintaining a small Python package with "
    "the user. Follow the project's conventions as the user has stated them in this "
    "conversation."
)
LIFECYCLES = ("stable", "replacement", "scope", "reinstatement")
TARGET_FAMILIES = ("naming", "validation", "missing_record")
SUPPORT_FAMILIES = ("return_shape", "error_surface", "logging")
SUITES = (
    "functional",
    "regression",
    "contract",
    "support",
    "protected_function",
    "protected_contract",
)
SUITE_TIMEOUT_S = 90.0  # passed to run_tests so one hung suite cannot stall a session
TICK_S = 60.0  # spend-ledger progress mark interval; bounds nothing (round 7 F13)
# Registered per-arm evaluation ceiling, derived in ``arm_budget_min`` below (§19.3).
GEN_ESTIMATE_S = (
    15.0 * 1.5
)  # §15.5's registered per-generation estimate with its factor
SUITE_COST_S = 0.189  # §16.7's MEASURED seconds per suite invocation
LOAD_ALLOWANCE_S = 300.0  # allowance for import, tokenizer and weight load
START_MARGIN_MIN = 5  # plan section E: stop STARTING work with this much budget left


@dataclass(frozen=True)
class Turn:
    role: str  # "user" | "assistant"
    content: str


@dataclass
class Request:
    text: str
    target: str  # file the model rewrites
    functional_tests: dict[str, str]
    regression_tests: dict[str, str]
    contract_tests: dict[str, dict[str, str]]  # target state -> test files
    support_tests: dict[str, str]
    gold: dict[str, str]  # target state -> complete content of ``target``


@dataclass
class Session:
    id: str  # manifest slot, e.g. "S01"
    project: str
    target_family: str
    support_family: str
    lifecycle: str
    files: dict[str, str]  # initial repository
    prefix: list[Turn]  # exactly 16 authored turns
    states: tuple[str, str]  # the target family's two states (initial, alternative)
    state_at: tuple[str, str]  # state in force at checkpoint 1 and 2
    event: str  # message between the live requests (contract-irrelevant if stable)
    requests: tuple[Request, Request]
    rule_turns: tuple[int, ...]  # prefix indices that must survive packing
    irrelevant_event: str = ""  # counterfactual variant (training pools only)
    notes: str = ""
    tags: dict[str, str] = field(default_factory=dict)

    def other(self, state: str) -> str:
        a, b = self.states
        return b if state == a else a

    def validate(self) -> None:
        assert self.lifecycle in LIFECYCLES, self.lifecycle
        assert self.target_family in TARGET_FAMILIES, self.target_family
        assert self.support_family in SUPPORT_FAMILIES, self.support_family
        assert len(self.prefix) == 16, f"{self.id}: prefix has {len(self.prefix)} turns"
        assert all(t.role in ("user", "assistant") for t in self.prefix)
        assert set(self.state_at) <= set(self.states)
        if self.lifecycle == "stable":
            assert self.state_at[0] == self.state_at[1]
        else:
            assert self.state_at[0] != self.state_at[1], self.id
        for r in self.requests:
            assert set(r.gold) == set(self.states), f"{self.id}: gold per state"
            assert set(r.contract_tests) == set(self.states), (
                f"{self.id}: tests per state"
            )
            assert r.target in self.files, f"{self.id}: target {r.target} not in files"
        assert all(0 <= i < 16 for i in self.rule_turns)


# ------------------------------------------------------------------ rendering

FILES_HEADER = "Current files:\n"


def _fenced(files: dict[str, str]) -> str:
    return "".join(
        f"### {p}\n```python\n{c.rstrip()}\n```\n" for p, c in sorted(files.items())
    )


def render_request_message(request: Request, files: dict[str, str]) -> str:
    """Live request 1 as one user message: every file, the task, the output format."""
    return (
        f"{FILES_HEADER}{_fenced(files)}\nTask: {request.text}\n\n"
        f"Reply with the complete new content of `{request.target}` in a single "
        "```python fenced block and nothing else. Keep existing behaviour that the task "
        "does not change."
    )


def render_request2_message(
    request: Request,
    files0: dict[str, str],
    files1: dict[str, str],
) -> str:
    """Live request 2, rendered with the CURRENT content of EVERY file, exactly as request 1
    renders the repository.  Because the whole current state is carried here, packing may
    evict the earlier request and its reply without the model losing anything it needs.

    History (Astra F1, then its two re-reviews).  The first version rendered only the files
    CHANGED since request 1, which hid request 2's own target in the seven slots whose two
    requests edit different files.  The second added the target, which still hid the record
    definition the target depends on (S03: `Fine` and its ``frozen=True`` live in
    ``model.py``, so a reply that assigns in place raises ``FrozenInstanceError`` and the
    constraint was nowhere in the window).  Rendering every file ends the class of defect
    instead of patching instances of it, and it fits: over all 48 slots, the required
    messages plus every file need at most 2,383 of the 2,560-token budget.
    """
    changed = sorted(p for p in files1 if files1[p] != files0.get(p))
    note = (
        "Every file above is the current content.\n"
        if changed
        else "Every file above is the current content; the last reply was not applied.\n"
    )
    return (
        f"{FILES_HEADER}{_fenced(files1)}{note}"
        f"\nTask: {request.text}\n\n"
        f"Reply with the complete new content of `{request.target}` in a single "
        "```python fenced block and nothing else. Keep existing behaviour that the task "
        "does not change."
    )


def session_messages(
    session: Session,
    checkpoint: int,
    files0: dict[str, str],
    reply1: str | None = None,
    files1: dict[str, str] | None = None,
    event: str | None = None,
) -> list[dict[str, str]]:
    """Unpacked message list for the live request at ``checkpoint`` (1 or 2).  ``files0``
    is the repository as request 1 saw it; ``files1`` the arm's own repository after its
    first reply (equal to ``files0`` when the reply was not applied)."""
    msgs = [{"role": "system", "content": SYSTEM}]
    msgs += [{"role": t.role, "content": t.content} for t in session.prefix]
    r1, r2 = session.requests
    msgs.append({"role": "user", "content": render_request_message(r1, files0)})
    if checkpoint == 1:
        return msgs
    assert reply1 is not None and files1 is not None
    msgs.append({"role": "assistant", "content": reply1})
    msgs.append(
        {"role": "user", "content": event if event is not None else session.event}
    )
    msgs.append(
        {"role": "user", "content": render_request2_message(r2, files0, files1)}
    )
    return msgs


def pack(
    messages: list[dict[str, str]],
    count_tokens: Callable[[list[dict[str, str]]], int],
    budget: int = PROMPT_BUDGET,
    drop_first: tuple[int, ...] = (),
    protect: Iterable[int] = (),
) -> tuple[list[dict[str, str]], list[int]]:
    """Compact to ``budget`` tokens: evict the messages in ``drop_first`` (a superseded
    request and its reply, whose result the live request already carries), then the oldest
    remaining turns.  The system line and the live request are never evicted, and neither is
    anything in ``protect``.

    Re-review F1: ``protect`` carries the rule turns and the lifecycle event.  Without it the
    packer evicted in plain index order and dropped an early rule turn while keeping later,
    droppable prefix chatter -- the governing rule left the window even though the required
    messages fit the budget with room to spare."""
    keep = list(range(len(messages)))
    last = len(messages) - 1
    kept_always = set(protect) | {0, last}
    order = [i for i in drop_first if 0 < i < last and i not in kept_always]
    order += [i for i in range(1, last) if i not in order and i not in kept_always]
    while count_tokens([messages[i] for i in keep]) > budget:
        droppable = [i for i in order if i in keep]
        if not droppable:
            break
        keep.remove(droppable[0])
    return [messages[i] for i in keep], keep


def pack_session(
    session: Session,
    messages: list[dict[str, str]],
    checkpoint: int,
    count_tokens: Callable[[list[dict[str, str]]], int],
    budget: int = PROMPT_BUDGET,
) -> tuple[list[dict[str, str]], list[int]]:
    """The registered packing policy for one live request: evict the superseded request and
    reply first, never evict the system line, the live request, the rule turns or the
    lifecycle event.  Every caller goes through this so no call site can forget an argument
    (re-review F1)."""
    return pack(
        messages,
        count_tokens,
        budget=budget,
        drop_first=drop_first_order(checkpoint),
        protect=required_indices(session, checkpoint),
    )


def drop_first_order(checkpoint: int) -> tuple[int, ...]:
    """Indices evicted before conversation turns: at checkpoint 2 the earlier request (17)
    and the first reply (18), in that order."""
    return (17, 18) if checkpoint == 2 else ()


def surviving_prefix_turns(kept: list[int]) -> set[int]:
    """Prefix indices (0-based) among kept message indices (message 0 is the system)."""
    return {i - 1 for i in kept if 1 <= i <= 16}


def required_indices(session: Session, checkpoint: int) -> set[int]:
    """Message indices that must survive packing (Astra F1): every rule turn, and at
    checkpoint 2 the lifecycle event (19) and the live request (20).  The earlier request
    (17) and the first reply (18) are ordinary history and may be compacted away; the
    request-2 message carries the current repository state, so nothing the model needs is
    lost when they are."""
    req = {i + 1 for i in session.rule_turns}
    if checkpoint == 2:
        req |= {19, 20}
    else:
        req |= {17}
    return req


def synthetic_reply(tok, n_tokens: int, request: Request, state: str) -> str:
    """A syntactically valid reply of at least ``n_tokens`` tokens (the gold file plus
    trailing comment lines inside the fence), used to qualify rule survival at the
    permitted maximum reply length."""
    body = f"```python\n{request.gold[state].rstrip()}\n"
    line = "# note: reviewed line by line against the conventions stated above\n"
    while len(tok(body + "```", add_special_tokens=False)["input_ids"]) < n_tokens:
        body += line
    return body + "```"


# ------------------------------------------------------------------ scoring


def public_api(content: str) -> set[str]:
    """Public top-level functions/classes and public methods, as qualified names."""
    import ast

    names: set[str] = set()
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return names
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("_"):
                names.add(node.name)
        elif isinstance(node, ast.ClassDef):
            if node.name.startswith("_"):
                continue
            names.add(node.name)
            for sub in node.body:
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if not sub.name.startswith("_"):
                        names.add(f"{node.name}.{sub.name}")
    return names


_API_TEST = '''"""Every public name bound before the live requests must still resolve."""

import importlib

SPEC = {spec}


def test_public_bindings_preserved():
    missing = []
    for module_path, names in sorted(SPEC.items()):
        module = importlib.import_module(module_path)
        for name in names:
            if "." in name:
                holder, attr = name.split(".", 1)
                owner = getattr(module, holder, None)
                ok = owner is not None and hasattr(owner, attr)
            else:
                ok = hasattr(module, name)
            if not ok:
                missing.append(module_path + ":" + name)
    assert not missing, "public bindings gone: " + repr(missing)
'''


def api_test(session: Session) -> dict[str, str]:
    """A generated test asserting that every public name bound before the live requests is
    still RESOLVABLE on the imported module (Astra F7, re-review F17).

    The first implementation compared AST definition names, which rejected legitimate
    implementations (``count = _count`` inside the class, or an inherited method) while
    establishing nothing about behaviour.  A runtime binding check accepts any shape that
    actually exposes the name, and deletion still fails.  Behaviour preservation is the job
    of the PROTECTED regression and functional suites, not of this check."""
    spec: dict[str, list[str]] = {}
    for path in sorted({r.target for r in session.requests}):
        names = sorted(public_api(session.files.get(path, "")))
        if names:
            spec[path[:-3].replace("/", ".")] = names
    return {"test_public_api_preserved.py": _API_TEST.format(spec=repr(spec))}


def score_checkpoint(session: Session, k: int, files: dict[str, str]) -> dict:
    """Run every applicable suite at checkpoint ``k`` (1 or 2) on ``files``.  At
    checkpoint 2 the PROTECTED suite re-runs request 1's functional, contract (under the
    state in force at checkpoint 1) and support tests."""
    r = session.requests[k - 1]
    state = session.state_at[k - 1]
    out: dict = {"state": state}
    suites = [
        ("functional", r.functional_tests),
        ("regression", r.regression_tests),
        ("contract", r.contract_tests[state]),
        ("support", r.support_tests),
    ]
    # Re-review F16: the protected group is scored in TWO parts so that contract
    # compliance never enters the function-only measurement.  ``protected_function`` is
    # request 1's functional and regression tests plus the public-binding check;
    # ``protected_contract`` is its contract and support tests.  Re-review F7: request 1's
    # REGRESSION tests were missing, which awarded a verified false J.
    if k == 2:
        r1 = session.requests[0]
        s1 = session.state_at[0]
        pf, pc = {}, {}
        for group in (r1.functional_tests, r1.regression_tests, api_test(session)):
            for name, content in group.items():
                pf[f"protected_{name}"] = content
        for group in (r1.contract_tests[s1], r1.support_tests):
            for name, content in group.items():
                pc[f"protected_{name}"] = content
        suites.append(("protected_function", pf))
        suites.append(("protected_contract", pc))
    else:
        # at checkpoint 1 only the pre-existing public bindings can already be gone
        suites.append(("protected_function", api_test(session)))
        out["protected_contract"] = True
        out["protected_contract_msg"] = "n/a"
    for name, tests in suites:
        ok, msg = run_tests(files, tests, timeout=SUITE_TIMEOUT_S)
        out[name] = ok
        out[f"{name}_msg"] = msg
    out["protected"] = bool(out["protected_function"] and out["protected_contract"])
    out["all"] = all(out[n] for n in SUITES)
    out["function_only"] = bool(
        out["functional"] and out["regression"] and out["protected_function"]
    )
    return out


def apply_reply(
    files: dict[str, str], request: Request, reply: str
) -> tuple[dict[str, str] | None, str]:
    """Apply the model's reply (a fenced file) to the repository.  Returns the new
    repository or ``None`` with the terminal reason."""
    content = extract_file(reply)
    if content is None:
        return None, "parse_failure"
    if not content.strip():
        return None, "empty"
    try:
        compile(content, request.target, "exec")
    except SyntaxError:
        return None, "syntax_error"
    return {**files, request.target: content}, "applied"


def gold_files(session: Session, k: int, state: str | None = None) -> dict[str, str]:
    """Repository after applying the gold answers up to checkpoint ``k`` (each under the
    state in force, or ``state`` for the last one)."""
    files = dict(session.files)
    for i in range(k):
        r = session.requests[i]
        s = session.state_at[i] if (i < k - 1 or state is None) else state
        files[r.target] = r.gold[s]
    return files


def gold_reply(session: Session, k: int, state: str | None = None) -> str:
    r = session.requests[k - 1]
    s = state or session.state_at[k - 1]
    return f"```python\n{r.gold[s].rstrip()}\n```"


# ------------------------------------------------------------------ training pairs


@dataclass(frozen=True)
class Pair:
    session: str
    variant: str  # "event" | "irrelevant"
    messages: tuple[dict[str, str], ...]  # unpacked prompt (packed at training time)
    chosen: str
    rejected: str
    chosen_state: str
    rejected_state: str


def pairs_from_session(session: Session) -> list[Pair]:
    """Two counterfactual pairs per training session at checkpoint 2: the history with
    the lifecycle event (chosen = gold under the state then in force, rejected = gold under
    the stale state) and the irrelevant-history variant (chosen = gold under the unchanged
    state, rejected = gold under the other state).  Both directions are executable gold."""
    s1, s2 = session.state_at
    files0 = dict(session.files)
    files1 = gold_files(session, 1)
    reply1 = gold_reply(session, 1)
    r2 = session.requests[1]
    out = []
    ev = session_messages(session, 2, files0, reply1, files1)
    stale2 = s1 if s2 != s1 else session.other(s2)
    out.append(
        Pair(
            session.id,
            "event",
            tuple(ev),
            gold_text(r2, s2),
            gold_text(r2, stale2),
            s2,
            stale2,
        )
    )
    if session.irrelevant_event:
        ir = session_messages(
            session, 2, files0, reply1, files1, event=session.irrelevant_event
        )
        out.append(
            Pair(
                session.id,
                "irrelevant",
                tuple(ir),
                gold_text(r2, s1),
                gold_text(r2, session.other(s1)),
                s1,
                session.other(s1),
            )
        )
    return out


def gold_text(request: Request, state: str) -> str:
    return f"```python\n{request.gold[state].rstrip()}\n```"


def make_counter(tok) -> Callable[[list[dict[str, str]]], int]:
    """Token counter over the shipping chat template (thinking disabled, generation
    prompt appended), the exact prompt the harness feeds the model."""

    def count(msgs: list[dict[str, str]]) -> int:
        text = tok.apply_chat_template(
            msgs, add_generation_prompt=True, tokenize=False, enable_thinking=False
        )
        return len(tok(text, add_special_tokens=False)["input_ids"])

    return count


def render_prompt(tok, msgs: list[dict[str, str]]) -> str:
    return tok.apply_chat_template(
        msgs, add_generation_prompt=True, tokenize=False, enable_thinking=False
    )


def file_sha(path: Path) -> str:
    """Streaming sha256 of a file's actual bytes (first 16 hex chars)."""
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def dir_sha(d: Path) -> str:
    """Fingerprint a model directory by every file's ACTUAL BYTES (round 3 F15).

    An earlier version hashed JSON under 2 MB in full and everything else by size, so the
    11 MB tokenizer, the 2.7 MB vocabulary and all three weight shards were size-only:
    different content of the same length produced an identical fingerprint.  Shared by the
    harness and the trainer so an adapter can be bound to the trunk bytes it trained on
    (round 4 F15), not merely to a pathname.
    """
    return hashlib.sha256(
        "\n".join(
            f"{p.name}:{p.stat().st_size}:{file_sha(p)}"
            for p in sorted(d.iterdir())
            if p.is_file()
        ).encode()
    ).hexdigest()[:16]


# ---------------------------------------------------------------- launch spend ledger
# Round 4 F13: a record's ``resident_s`` only accounts for work that produced a record, so
# a launch that dies after its last record, or before writing any, contributed GPU time no
# record carries.  The sidecar below is a launch-level ledger: one line per checkpoint of a
# process, independent of the record file.
#
# Round 5 F13: the first version charged an unfinished launch its last checkpoint plus a
# 300 s grace, which is NOT an upper bound -- a checkpoint follows generation AND scoring,
# so the work after a mark can be a whole 300 s generation plus up to six 90 s suites.
#
# Round 6 F13: the replacement bounded the gap between marks by the work a checkpoint can
# follow, which is still not an upper bound anywhere that bound is not enforced.  Model
# loading had no enforced limit (a launch killed while loading at 900 s, read at 1,200 s,
# was charged 600 s), and the pilot runs 44 suite invocations between ``model_loaded`` and
# ``suite_cost_measured`` against a bound that assumed six.  Caps that termination does not
# enforce are gone.  A HEARTBEAT thread now writes a ``tick`` every ``TICK_S`` seconds from
# before the model load until exit, so the ledger carries a VERIFIED alive-timestamp for
# every interval of a launch's life: a launch whose marks have no gap wider than the slack
# was alive at its last mark and dead by ``last + slack``, and is charged that.  A launch
# whose heartbeat is NOT intact -- a gap wider than the slack, or no tick at all -- is
# charged its whole lifetime, uncapped, because nothing bounds what it did in the dark.
#
# Round 5 F13 also: a process killed mid-write leaves a torn final line, and the next
# launch's ``start`` line appended to it became ONE malformed line that the reader skipped
# -- so a launch that then died during loading was charged nothing.  ``ledger_repair``
# truncates a torn tail before anything is appended, and a malformed line anywhere else is
# refused rather than skipped.


def ledger_repair(path: Path) -> str | None:
    """Truncate a torn final line (a process killed mid-write) so the next append cannot
    be swallowed by it.  Returns the discarded text, or ``None`` if the tail was clean.
    Nothing is lost by discarding it: the launch that wrote it has no ``end`` line, so it
    is charged its lifetime, not its marks."""
    if not path.exists():
        return None
    data = path.read_bytes()
    if not data or data.endswith(b"\n"):
        return None
    cut = data.rfind(b"\n") + 1
    torn = data[cut:].decode("utf-8", "replace")
    path.write_bytes(data[:cut])
    return torn


def boot_id() -> str:
    """Identifier of the current boot, or ``""`` when the kernel does not expose one.

    ``time.monotonic()`` is only comparable within one boot, so a reading carried in a
    ledger line is usable only while this matches (round 9)."""
    try:
        return Path("/proc/sys/kernel/random/boot_id").read_text().strip()
    except OSError:
        return ""


def ledger_mark(
    path: Path, launch: str, event: str, t0: float, m0: float, **extra: object
) -> None:
    """Append one launch-level checkpoint.

    Round 9, high: every DURATION here is MONOTONIC.  ``t`` stays realtime because it is
    the calendar timestamp a human reads, but ``time.time()`` can be stepped -- by NTP or
    by hand -- and Astra stepped it 600 s backwards 360 s into a 900 s launch: the ledger
    charged **300 s**, and beside 2,400 s of other work the real summary printed GATE
    PASSED at 45 charged minutes against 55 spent.  The same step forwards made a
    legitimate 45-minute run charge 55 and report INCOMPLETE, so the error runs both ways.
    ``time.monotonic()`` cannot be stepped; ``boot`` records which boot its origin belongs
    to, because a reading from another boot means nothing here."""
    now, mono = time.time(), time.monotonic()
    rec = {
        "launch": launch,
        "event": event,
        "t": now,
        "m": mono,
        "boot": boot_id(),
        "elapsed_s": mono - m0,
        **extra,
    }
    with path.open("a") as fh:
        fh.write(json.dumps(rec) + "\n")
        fh.flush()


def ledger_pid(launch: str) -> int | None:
    """The OS pid inside a launch id (``{start}-{pid}``), or ``None`` if it has none."""
    tail = launch.rsplit("-", 1)[-1]
    return int(tail) if tail.isdigit() else None


def ledger_observe(
    path: Path,
    clock: Callable[[], float] = time.monotonic,
    mark: Callable | None = None,
    wall: Callable[[], float] = time.time,
) -> list[str]:
    """Record VERIFIED termination for every unfinished launch whose process is gone.

    Round 7 F13: the previous rule inferred death from the ABSENCE of a heartbeat, and
    absence is not evidence -- a ledger with ticks to 600 s is equally consistent with
    death at 600 s and with a ticker that failed at 600 s while the process ran to 1,200 s
    (Astra killed the ticker thread by injecting an append failure and the main thread
    carried on).  Silence now bounds nothing.  Instead, a process that is GONE at a known
    time cannot have lived past that time, so the observation itself is the evidence and it
    is written into the ledger once, after which the launch's charge never moves again.
    A launch still running, or one whose pid has been recycled, is not observed and keeps
    accruing its lifetime -- the conservative direction.  Returns the launches observed.

    Round 8 F13: the timestamp is sampled AFTER each successful probe, never before.  The
    caller used to sample it once and pass it in, so a process descheduled between the
    sample and the probe wrote a BACKDATED observation -- sampled at 300 s, probed at
    1,000 s, permanently charging 300 s for a launch that lived to 900.  What absence at
    the probe establishes is termination by the PROBE's time, so that is the time written.

    Round 9, high: the observation's ELAPSED is monotonic, by the same rule as
    :func:`ledger_charges` -- ``clock`` is ``time.monotonic`` and the realtime span is used
    only for a launch that carries no comparable monotonic origin."""
    if not path.exists():
        return []
    now_t = wall()
    boot = boot_id()
    seen: dict[str, dict] = {}
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(r, dict) or "launch" not in r:
            continue
        cur = seen.setdefault(
            r["launch"],
            {"first": float(r.get("t", now_t)), "done": False, "max": 0.0, "m": None},
        )
        cur["first"] = min(cur["first"], float(r.get("t", now_t)))
        cur["max"] = max(cur["max"], float(r.get("elapsed_s", 0.0)))
        cur["done"] = cur["done"] or r.get("event") in ("end", "observed_dead")
        if boot and r.get("boot") == boot and "m" in r:
            m = float(r["m"])
            cur["m"] = m if cur["m"] is None else min(cur["m"], m)
    out = []
    for launch, i in sorted(seen.items()):
        pid = ledger_pid(launch)
        if i["done"] or pid is None or Path(f"/proc/{pid}").exists():
            continue
        now = clock()  # the probe has just succeeded; THIS is the time it bounds
        span = now - i["m"] if i["m"] is not None else wall() - i["first"]
        rec = {
            "launch": launch,
            "event": "observed_dead",
            # never below a mark the launch actually wrote, so a clock that went backwards
            # cannot turn an observation into a zero charge
            "elapsed_s": max(span, i["max"]),
            "t": wall(),
            "m": now,
            "boot": boot,
        }
        with path.open("a") as fh:
            fh.write(json.dumps(rec) + "\n")
            fh.flush()
        out.append(launch)
        if mark is not None:
            mark("observed_dead_recorded", dead=launch, charged_s=rec["elapsed_s"])
    return out


def ledger_charges(
    path: Path,
    exclude: str,
    now: float,
    now_m: float | None = None,
) -> tuple[dict[str, float], int]:
    """``({launch: seconds charged}, malformed line count)`` for every launch but
    ``exclude``.

    Three cases, and only the first two are bounded by evidence (round 7 F13):
    a launch that wrote ``end`` is charged its real elapsed time; one whose termination was
    OBSERVED is charged through that observation; and one that is neither -- no end, no
    observation -- is charged its whole lifetime THROUGH ``now``, with no cap, because
    nothing establishes that it ever stopped.

    Round 9, high: that lifetime is measured on the MONOTONIC clock.  ``elapsed_s`` is
    already monotonic in every line the current runner writes, so the first two cases never
    touch a wall clock at all; the third compares ``now_m`` with the launch's earliest
    monotonic reading, which is meaningful only within one boot -- hence ``boot`` on every
    line.  ``now`` (realtime) is the fallback for a launch that carries no comparable
    monotonic origin: a ledger written before this amendment, or one from an earlier boot,
    where the realtime span also covers the downtime and therefore over-charges."""
    if not path.exists():
        return {}, 0
    now_m = time.monotonic() if now_m is None else now_m
    boot = boot_id()
    by: dict[str, dict] = {}
    malformed = 0
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            malformed += 1
            continue
        if not isinstance(r, dict) or "launch" not in r:
            malformed += 1
            continue
        if r["launch"] == exclude:
            continue
        cur = by.setdefault(
            r["launch"],
            {"first": float(r.get("t", now)), "max": 0.0, "fixed": None, "m": None},
        )
        cur["first"] = min(cur["first"], float(r.get("t", now)))
        cur["max"] = max(cur["max"], float(r.get("elapsed_s", 0.0)))
        if boot and r.get("boot") == boot and "m" in r:
            m = float(r["m"])
            cur["m"] = m if cur["m"] is None else min(cur["m"], m)
        if r.get("event") in ("end", "observed_dead"):
            cur["fixed"] = max(cur["fixed"] or 0.0, float(r.get("elapsed_s", 0.0)))
    out = {}
    for lid, i in by.items():
        # never below a mark the launch wrote, whichever case applies: a clock that went
        # backwards must not erase a launch, and an ``end`` cannot predate its own marks
        if i["fixed"] is not None:
            out[lid] = max(i["fixed"], i["max"])
        elif i["m"] is not None:
            out[lid] = max(i["max"], now_m - i["m"])
        else:
            out[lid] = max(i["max"], now - i["first"])
    return out, malformed


def ledger_tick(
    path: Path, launch: str, t0: float, m0: float, stop, interval: float = TICK_S
):
    """Body of the progress-mark thread: append a ``tick`` every ``interval`` seconds until
    ``stop`` is set.  Round 7 F13: these marks are a PROGRESS LOG and bound nothing -- a
    charge comes from ``end`` or from an observation, never from the last tick -- so a
    thread that dies silently costs no accuracy."""
    while True:
        ledger_mark(path, launch, "tick", t0, m0)
        if stop.wait(interval):
            return


def arm_budget_min(
    sessions: int = 48,
    gen_s: float = GEN_ESTIMATE_S,
    suite_s: float = SUITE_COST_S,
    load_s: float = LOAD_ALLOWANCE_S,
    margin_min: int = START_MARGIN_MIN,
) -> float:
    """The smallest per-arm ceiling under which the LAST request is still admitted.

    Round 7, medium: §18.2 sized the ceiling against total work and forgot that
    ``may_start`` refuses a request once less than ``margin_min`` remains, so the binding
    constraint is when the last request STARTS, not when the arm finishes.  Under the
    registered estimates a 45-minute ceiling left only 2.73 minutes for the model load and
    refused request 96 at 2,416 s.  Computed here instead of asserted: the run loads, then
    does every request but the last, and that moment must still be inside the margin."""
    work_1 = gen_s + 5 * suite_s  # checkpoint 1 scores five suites
    work_2 = gen_s + 6 * suite_s  # checkpoint 2 scores six
    before_last = load_s + sessions * (work_1 + work_2) - work_2
    return (before_last + margin_min * 60.0) / 60.0


ARM_BUDGET_MIN = 50.0  # >= arm_budget_min() = 47.27; §19.3 records the derivation


def write_status(path: Path, **fields: object) -> None:
    """Write the end-of-run status artifact (round 6 F12).  A run's budget eligibility has
    to outlive its console output: the summary reads this file and the spend ledger, and an
    arm with no COMPLETE status is not analysable no matter how many records it has."""
    path.write_text(json.dumps(fields, indent=1, sort_keys=True) + "\n")


def read_status(path: Path) -> tuple[dict | None, str | None]:
    """``(status, refusal)``: the parsed status artifact, or a one-line reason the arm is
    not analysable.  Independent of the records, which carry no eligibility."""
    if not path.exists():
        return None, (
            f"{path.name} is missing: the run left no end-of-run status, so it was killed "
            "or never finished and its budget eligibility is unknown"
        )
    try:
        st = json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        return None, f"{path.name} is not readable ({exc})"
    if not isinstance(st, dict):
        return None, f"{path.name} is not a status object"
    if st.get("pilot"):
        return st, f"{path.name} is a PILOT status (a session subset), not the screen"
    if st.get("status") != "COMPLETE":
        return st, f"{path.name} reports status {st.get('status')!r}"
    budget = float(st.get("budget_min") or 0.0)
    if not 0 < budget <= ARM_BUDGET_MIN:
        return st, (
            f"{path.name} ran under budget_min={st.get('budget_min')!r}, outside the "
            f"registered per-arm ceiling of {ARM_BUDGET_MIN:.0f} min"
        )
    if float(st.get("spent_min") or 0.0) > budget:
        return st, (
            f"{path.name} spent {st['spent_min']:.1f} min of its {budget:.0f} min budget"
        )
    return st, None


def ledger_spent_min(
    path: Path,
    launches: set[str] | None = None,
    now: float | None = None,
    now_m: float | None = None,
) -> tuple[float, list[str]]:
    """``(minutes charged across every launch, refusals)`` — the INDEPENDENT reading of an
    arm's spend, so the summary checks the ledger rather than trusting the status.

    Round 7 F12: a MISSING or EMPTY ledger read as zero spend, so deleting an ordinary
    sidecar turned an over-budget arm into ``GATE PASSED``.  Absent evidence is not evidence
    of nothing: the ledger must exist, be non-empty, parse completely, and account for every
    launch the RECORDS say produced them (``launches``).  Anything else is a refusal, not a
    zero."""
    refusals: list[str] = []
    if not path.exists():
        return 0.0, [
            f"{path.name} is missing: the arm's resident time cannot be accounted"
        ]
    if not path.read_text().strip():
        return 0.0, [
            f"{path.name} is empty: the arm's resident time cannot be accounted"
        ]
    charges, malformed = ledger_charges(
        path,
        exclude="",
        now=time.time() if now is None else now,
        now_m=now_m,
    )
    if malformed:
        refusals.append(
            f"{path.name} has {malformed} malformed line(s), so the arm's resident time "
            "cannot be accounted"
        )
    absent = sorted((launches or set()) - set(charges))
    if absent:
        refusals.append(
            f"{path.name} accounts for no spend by launch(es) {', '.join(absent)}, which "
            "the records say produced them"
        )
    return sum(charges.values()) / 60, refusals


def may_start(budget_min: float | None, spent_min: float, margin_min: float) -> bool:
    """Whether a request may START.  Round 5 F13: the harness guarded only the session
    start, so a session admitted with two minutes left ran a whole second request past the
    budget; every request start asks this now.  Work is admitted only while MORE than the
    margin remains, so the margin is what an admitted request may overrun by without the
    run being over budget."""
    if not budget_min:
        return True
    return budget_min - spent_min > margin_min


def run_status(
    not_started: list[str],
    request2_not_started: list[str],
    budget_min: float | None,
    spent_min: float,
) -> str:
    """``COMPLETE`` only when every session ran both requests AND the run stayed inside its
    budget.  Round 5 F13: the status used to consider only unstarted sessions, so an
    evaluation that exhausted its budget mid-session reported COMPLETE."""
    over = bool(budget_min) and spent_min > budget_min
    return "INCOMPLETE" if (not_started or request2_not_started or over) else "COMPLETE"
