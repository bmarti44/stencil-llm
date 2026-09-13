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

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field

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
    """Live request 2, self-contained with respect to the repository: the CURRENT content
    of every file changed since request 1 AND of the file this request asks the model to
    rewrite, plus a line saying the rest are unchanged.  Because the current state is
    carried here, packing may evict the earlier request and reply for a long first reply
    without the model losing the code it must extend (Astra F1).

    Re-review F1: rendering only the CHANGED files left request 2's own target invisible in
    the seven slots whose two requests edit different files, so the target is now always
    included even when the first reply did not touch it."""
    changed = sorted(p for p in files1 if files1[p] != files0.get(p))
    shown = sorted(set(changed) | {request.target})
    parts = [f"{FILES_HEADER}{_fenced({p: files1[p] for p in shown})}"]
    if changed:
        parts.append("All other files are unchanged from the earlier request.\n")
    else:
        parts.append(
            "The repository is unchanged from the earlier request (the last reply was "
            "not applied).\n"
        )
    return (
        "".join(parts) + f"\nTask: {request.text}\n\n"
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
        ok, msg = run_tests(files, tests)
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
