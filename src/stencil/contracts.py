"""Authored maintenance tasks governed by mutable project contracts (proposal rev 5).

A :class:`Task` is a small Python package, one coding request, the set of project
contracts currently in force (each from a closed family with a machine-checkable
state), and two groups of executable tests:

* ``functional`` tests: pass iff the request is implemented correctly, whatever the
  contract states;
* ``contract`` tests: pass iff the implementation honours the *current* state of each
  applicable contract (and fail under the alternative state, which the authoring
  self-check enforces).

Joint success ``J`` = every functional AND contract test passes.  Scoring runs the
tests in a fresh temporary directory with a subprocess timeout; nothing from
``data/bench/`` is involved.  The model's answer is the complete new content of the
target file, returned in one fenced block (``extract_file``).

Used by the registered competence pre-check (unmodified model, contracts stated in the
request) and later by the screen (contracts carried in a session history).
"""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class ContractState:
    family: str  # e.g. "missing-record policy"
    state: str  # e.g. "none" | "raise"
    text: str  # the instruction sentence as the model sees it


@dataclass
class Task:
    id: str
    project: str
    files: dict[str, str]  # path -> content, before the request
    target: str  # the file the model rewrites
    request: str
    contracts: list[ContractState]
    functional_tests: dict[str, str]
    contract_tests: dict[str, str]
    gold: str  # reference content of ``target`` satisfying request + contracts
    families: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.families:
            self.families = tuple(c.family for c in self.contracts)


_FENCE = re.compile(r"```(?:python)?\s*\n(.*?)```", re.DOTALL)


def extract_file(response: str) -> str | None:
    """The last fenced Python block of ``response`` (the complete target file)."""
    blocks = _FENCE.findall(response)
    if not blocks:
        return None
    return blocks[-1]


def render_request(
    task: Task, contracts_in_request: bool = True, mode: str = "plain"
) -> str:
    """Immediate-instruction rendering used by the pre-check: the project files, the
    contracts in force (optional), the request, and the output format.  ``mode``
    ``"explicit"`` adds a precedence note saying the contracts override any older
    convention visible in the existing code (the precedent-conflict probe)."""
    parts = ["You are maintaining a small Python package. Current files:\n"]
    for path, content in task.files.items():
        parts.append(f"### {path}\n```python\n{content.rstrip()}\n```\n")
    if contracts_in_request and task.contracts:
        parts.append("Project contracts currently in force (they override defaults):\n")
        for c in task.contracts:
            parts.append(f"- {c.text}\n")
        if mode == "explicit":
            parts.append(
                "\nThese contracts were changed recently. Existing code in the files "
                "above may still follow the OLD convention; do not copy that pattern. "
                "The contracts above take precedence over anything the existing code "
                "does. Before writing, check each contract against your new code.\n"
            )
    parts.append(f"\nTask: {task.request}\n")
    parts.append(
        f"\nReply with the complete new content of `{task.target}` in a single "
        "```python fenced block and nothing else. Keep existing behaviour that the "
        "task does not change."
    )
    return "".join(parts)


def run_tests(
    files: dict[str, str], tests: dict[str, str], timeout: float = 90.0
) -> tuple[bool, str]:
    """Write ``files`` and ``tests`` to a fresh directory and run pytest there.
    Returns ``(all_passed, short_summary)``; a timeout or crash counts as failure."""
    if not tests:
        return True, "no tests"
    with tempfile.TemporaryDirectory(prefix="stencil-contract-") as d:
        root = Path(d)
        for path, content in {**files, **tests}.items():
            p = root / path
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content)
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-x",
            "-p",
            "no:cacheprovider",
            *sorted(tests),
        ]
        try:
            r = subprocess.run(
                cmd,
                cwd=root,
                capture_output=True,
                text=True,
                timeout=timeout,
                env={"PYTHONPATH": str(root), "PATH": "/usr/bin:/bin", "HOME": d},
            )
        except subprocess.TimeoutExpired:
            return False, "timeout"
        tail = (r.stdout.strip().split("\n") or [""])[-1]
        return r.returncode == 0, tail[:200]


def score(task: Task, new_target: str | None) -> dict:
    """Functional-only and joint outcomes for a proposed new content of the target."""
    if new_target is None:
        return {"parsed": False, "functional": False, "contract": False, "J": False}
    files = {**task.files, task.target: new_target}
    f_ok, f_msg = run_tests(files, task.functional_tests)
    # Astra round 8: contract tests always run so both outcomes are reported
    # independently (J still requires both).
    c_ok, c_msg = run_tests(files, task.contract_tests)
    return {
        "parsed": True,
        "functional": f_ok,
        "contract": c_ok,
        "J": f_ok and c_ok,
        "functional_msg": f_msg,
        "contract_msg": c_msg,
    }
