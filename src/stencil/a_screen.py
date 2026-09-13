# ruff: noqa: E501
"""Six-family candidate-A screen: stateful contract sessions, packing policy, scoring.

Registered in ``results/a-screen/REGISTRATION-A-SCREEN.md`` (2026-09-13).  A
:class:`Session` is a small Python package, a frozen 16-turn prefix, a lifecycle event
message and two live coding :class:`Request` objects.  The target contract family has two
states; ``state_at`` says which is in force at each live checkpoint.  A supporting
contract is stated once in the prefix and never changes.

Prompt packing (registration §5): system line + the newest whole turns that fit in
``PROMPT_BUDGET`` tokens, dropped from the oldest turn first; the live request message is
never dropped.  Nothing is summarised and no current-rule answer is inserted.

Outcome (registration §6): at each checkpoint the functional, regression, applicable
target-contract and support-contract suites run independently in a sandbox
(:func:`stencil.contracts.run_tests`); the session's ``J`` is 1 only if every suite passes
at both checkpoints.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from stencil.contracts import extract_file, run_tests

PROMPT_BUDGET = 2560  # 4096 - 1536 reserved for the answer
MAX_NEW_TOKENS = 1536
SYSTEM = (
    "You are a careful software engineer maintaining a small Python package with "
    "the user. Follow the project's conventions as the user has stated them in this "
    "conversation."
)
LIFECYCLES = ("stable", "replacement", "scope", "reinstatement")
TARGET_FAMILIES = ("naming", "validation", "missing_record")
SUPPORT_FAMILIES = ("return_shape", "error_surface", "logging")


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


def render_request_message(
    request: Request, files: dict[str, str], changed: set[str] | None = None
) -> str:
    """The live request as one user message.  Checkpoint 1 shows every file; checkpoint 2
    shows only the files changed since checkpoint 1 plus the request's target, and says
    the rest are unchanged."""
    if changed is None:
        shown = files
        note = ""
    else:
        keys = set(changed) | {request.target}
        shown = {k: files[k] for k in keys if k in files}
        note = "All other files are unchanged from what you saw earlier.\n"
    return (
        f"{FILES_HEADER}{_fenced(shown)}{note}\nTask: {request.text}\n\n"
        f"Reply with the complete new content of `{request.target}` in a single "
        "```python fenced block and nothing else. Keep existing behaviour that the task "
        "does not change."
    )


def session_messages(
    session: Session,
    checkpoint: int,
    files: dict[str, str],
    reply1: str | None = None,
    changed: set[str] | None = None,
    event: str | None = None,
) -> list[dict[str, str]]:
    """Unpacked message list for the live request at ``checkpoint`` (1 or 2), given the
    arm's own repository ``files`` and, for checkpoint 2, its verbatim first reply."""
    msgs = [{"role": "system", "content": SYSTEM}]
    msgs += [{"role": t.role, "content": t.content} for t in session.prefix]
    r1, r2 = session.requests
    msgs.append({"role": "user", "content": render_request_message(r1, files)})
    if checkpoint == 1:
        return msgs
    assert reply1 is not None
    msgs.append({"role": "assistant", "content": reply1})
    msgs.append(
        {"role": "user", "content": event if event is not None else session.event}
    )
    msgs.append({"role": "user", "content": render_request_message(r2, files, changed)})
    return msgs


def pack(
    messages: list[dict[str, str]],
    count_tokens: Callable[[list[dict[str, str]]], int],
    budget: int = PROMPT_BUDGET,
) -> tuple[list[dict[str, str]], list[int]]:
    """Drop the oldest non-system, non-final turns until the rendered prompt fits.
    Returns the kept messages and the kept indices into ``messages``."""
    keep = list(range(len(messages)))
    while count_tokens([messages[i] for i in keep]) > budget:
        droppable = [i for i in keep if i != 0 and i != len(messages) - 1]
        if not droppable:
            break
        keep.remove(droppable[0])
    return [messages[i] for i in keep], keep


def surviving_prefix_turns(kept: list[int]) -> set[int]:
    """Prefix indices (0-based) among kept message indices (message 0 is the system)."""
    return {i - 1 for i in kept if 1 <= i <= 16}


# ------------------------------------------------------------------ scoring


def score_checkpoint(session: Session, k: int, files: dict[str, str]) -> dict:
    """Run every applicable suite at checkpoint ``k`` (1 or 2) on ``files``."""
    r = session.requests[k - 1]
    state = session.state_at[k - 1]
    out: dict = {"state": state}
    for name, tests in (
        ("functional", r.functional_tests),
        ("regression", r.regression_tests),
        ("contract", r.contract_tests[state]),
        ("support", r.support_tests),
    ):
        ok, msg = run_tests(files, tests)
        out[name] = ok
        out[f"{name}_msg"] = msg
    out["all"] = all(
        out[n] for n in ("functional", "regression", "contract", "support")
    )
    out["function_only"] = out["functional"] and out["regression"]
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
    files1 = gold_files(session, 1)
    reply1 = gold_reply(session, 1)
    changed = {session.requests[0].target}
    r2 = session.requests[1]
    out = []
    ev = session_messages(session, 2, files1, reply1, changed)
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
            session, 2, files1, reply1, changed, event=session.irrelevant_event
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
