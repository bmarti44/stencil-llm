# ruff: noqa: E501
"""Static backstop: experiment code must never terminate another process."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CODE_SUFFIXES = {".py", ".sh", ".json", ".toml", ".yaml", ".yml"}
FORBIDDEN = (
    re.compile(r"os\.kill\("),
    re.compile(r"signal\.SIG"),
    re.compile(r"\bpkill\b"),
    re.compile(r"\bkillall\b"),
    re.compile(r"\bkill\s+-"),
)


def test_no_kill_or_cross_process_watchdog_patterns():
    hits = []
    for top in ("scripts", "src", "tools"):
        for path in (ROOT / top).rglob("*"):
            if not path.is_file() or path.suffix not in CODE_SUFFIXES or "archive" in path.parts:
                continue
            text = path.read_text(errors="ignore")
            for lineno, line in enumerate(text.splitlines(), 1):
                if any(pattern.search(line) for pattern in FORBIDDEN):
                    hits.append(f"{path.relative_to(ROOT)}:{lineno}")
                if ("watchdog" in line.lower() and
                        re.search(r"(?:terminate|send_signal|process\.kill)\s*\(", line)):
                    hits.append(f"{path.relative_to(ROOT)}:{lineno}:cross-process watchdog")
    assert not hits, f"process-termination patterns are forbidden: {hits}"
