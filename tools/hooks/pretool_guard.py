#!/usr/bin/env python3
"""Claude PreToolUse guard for sealed data, process, and GPU isolation."""

import ast
import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SEALED_NAME = "data/bench/ifeval_input_data.jsonl"
OWNED_PIDS_ENV = "STENCIL_OWNED_PIDS"


def _sealed_allowlist():
    """Load the single source of truth without importing the test module."""
    tree = ast.parse((ROOT / "tests" / "test_sealed_guard.py").read_text())
    for node in tree.body:
        is_allowlist = isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "ALLOWED"
            for target in node.targets
        )
        if is_allowlist:
            return set(ast.literal_eval(node.value))
    raise RuntimeError("sealed allowlist not found")


def _segments(command):
    return [
        part.strip()
        for part in re.split(r"&&|\|\||;|\n|(?<!&)&(?!&)", command)
        if part.strip()
    ]


def _allowed_sealed_segment(segment, allowlist):
    try:
        tokens = shlex.split(segment)
    except ValueError:
        return False
    normalized = [token.removeprefix("./") for token in tokens]
    hits = [i for i, token in enumerate(normalized) if token in allowlist]
    if not hits:
        return False
    launchers = {"python", "python3", "pytest"}
    for i in hits:
        if i == 0 and normalized[i].startswith(("scripts/", "tests/")):
            return True
        if any(Path(token).name in launchers for token in normalized[:i]):
            return True
    return False


def _owned_from_env(env):
    values = env.get(OWNED_PIDS_ENV, "")
    return {int(value) for value in re.findall(r"\d+", values)}


def _process_reason(command, owned_pids):
    """Reject process-control targets unless every literal PID is caller-owned."""
    # Command-position only: start of command, after ; | & ( or a newline, or after
    # sudo/exec/env/xargs. Prose inside quoted text or heredocs must not trip the guard.
    process_pattern = (r"(?:^|[;&|(]\s*|\n\s*|\b(?:sudo|exec|env|xargs)\s+)"
                       + r"(" + "p" + r"kill|kill" + "all" + r"|kill)(?=\s|$)")
    # Scan only the unquoted command surface: drop heredoc bodies and quoted strings first.
    scan = re.sub(r"<<-?\s*'?\"?(\w+)'?\"?\n.*?\n\1(?=\n|$)", " ", command, flags=re.S)
    scan = re.sub(r"'[^']*'|\"[^\"]*\"", " ", scan)
    words = [m.group(1) for m in re.finditer(process_pattern, scan)]
    python_api = ("os." + "kill(" in command) or ("signal." + "SIG" in command)
    if not words and not python_api:
        return None
    if any(word != "kill" for word in words):
        return "pid isolation: name-based process termination is denied"
    pids = {int(value) for value in re.findall(r"(?<![\w.])\d+(?![\w.])", command)}
    if not pids or not pids.issubset(owned_pids):
        return "pid isolation: target pid is not owned by this launch"
    return None


def _gpu_launch(command):
    lower = command.lower()
    if "nvidia-smi" in lower and "--gpu-reset" in lower:
        return True
    pythonish = bool(re.search(r"(?:^|\s)(?:uv\s+run\s+)?python(?:3)?(?:\s|$)", lower))
    explicit_cuda = "torch" in lower or "cuda" in lower
    scripted_model = bool(
        re.search(r"uv\s+run\s+python(?:3)?\s+scripts/\S+", lower)
    ) and bool(
        re.search(
            r"(?:^|[\s=])(?:models?/|\S+\.(?:pt|safetensors))(?:\s|$)", lower
        )
    )
    return pythonish and (explicit_cuda or scripted_model)


def _query_gpu_pids():
    result = subprocess.run(
        ["nvidia-smi", "--query-compute-apps=pid", "--format=csv,noheader"],
        capture_output=True, text=True, check=False,
    )
    if result.returncode:
        raise RuntimeError(f"nvidia-smi query failed ({result.returncode})")
    return [int(value) for value in re.findall(r"\d+", result.stdout)]


def _background_launch(command):
    return (bool(re.search(r"(?:^|\s)(?:nohup|setsid|disown)(?:\s|$)", command))
            or bool(re.search(r"(?<!&)&(?!&)", command)))


def decision(command, *, env=None, gpu_pids=None, owned_pids=None):
    """Return a deny reason, or ``None``. Injected state keeps CPU tests hermetic."""
    env = os.environ if env is None else env
    allowlist = _sealed_allowlist()
    for segment in _segments(command):
        if SEALED_NAME in segment and not _allowed_sealed_segment(segment, allowlist):
            return (
                "sealed input denied: invoking script is not in "
                "tests/test_sealed_guard.py ALLOWED"
            )

    owned = _owned_from_env(env) if owned_pids is None else set(owned_pids)
    process_reason = _process_reason(command, owned)
    if process_reason:
        return process_reason

    if env.get("STENCIL_SUBAGENT") == "1" and _background_launch(command):
        return "background launch denied for STENCIL_SUBAGENT=1"

    if _gpu_launch(command):
        try:
            active = _query_gpu_pids() if gpu_pids is None else list(gpu_pids)
        except (OSError, RuntimeError) as exc:
            return f"GPU busy guard failed closed: {exc}"
        if active:
            return f"GPU busy: active compute pid(s) {','.join(map(str, active))}"
    return None


def deny_payload(reason):
    return json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }, separators=(",", ":"))


def main():
    try:
        payload = json.load(sys.stdin)
        if payload.get("tool_name") != "Bash":
            return 0
        reason = decision(payload.get("tool_input", {}).get("command", ""))
    except Exception as exc:  # malformed hook input or guard failure: fail closed
        reason = f"isolation guard failed closed: {exc.__class__.__name__}: {exc}"
    if reason:
        print(deny_payload(reason))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
