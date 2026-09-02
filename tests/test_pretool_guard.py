"""CPU-only decision-table tests for the mechanical PreToolUse Bash guard."""
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
GUARD_PATH = ROOT / "tools" / "hooks" / "pretool_guard.py"


@pytest.fixture(scope="module")
def guard():
    spec = importlib.util.spec_from_file_location("pretool_guard", GUARD_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# command, environment, simulated GPU pids, pids launched by this caller, denied reason fragment
CASES = [
    ("uv run pytest -q tests/", {}, [], set(), None),
    ("python scripts/ledger_eval.py --preflight-only", {}, [], set(), None),
    ("cat data/bench/ifeval_input_data.jsonl", {}, [], set(), "sealed"),
    ("rg needle data/bench/ifeval_input_data.jsonl", {}, [], set(), "sealed"),
    ("python scripts/b4_ifeval.py", {}, [], set(), None),
    ("uv run python scripts/b0_score_parity.py data/bench/ifeval_input_data.jsonl", {}, [], set(), None),
    ("python scripts/b4_ifeval.py && cat data/bench/ifeval_input_data.jsonl", {}, [], set(), "sealed"),
    ("kill -TERM 123", {}, [], set(), "pid"),
    ("kill -TERM 123", {}, [], {123}, None),
    ("kill 123", {}, [], set(), "pid"),
    ("pkill python", {}, [], set(), "pid"),
    ("killall python", {}, [], set(), "pid"),
    ("python -c 'import os, signal; os.kill(123, signal.SIGTERM)'", {}, [], set(), "pid"),
    ("python -c 'import os, signal; os.kill(123, signal.SIGTERM)'", {}, [], {123}, None),
    ("python -c 'import torch'", {}, [999], set(), "GPU busy"),
    ("python -c 'print(\"cuda\")'", {}, [999], set(), "GPU busy"),
    ("uv run python scripts/ledger_eval.py --model models/qwen.pt", {}, [999], set(), "GPU busy"),
    ("nvidia-smi --gpu-reset", {}, [999], set(), "GPU busy"),
    ("python -c 'import torch'", {}, [], set(), None),
    ("python cpu_job.py", {}, [999], set(), None),
    ("nohup python cpu_job.py", {"STENCIL_SUBAGENT": "1"}, [], set(), "background"),
    ("python cpu_job.py &", {"STENCIL_SUBAGENT": "1"}, [], set(), "background"),
    ("setsid python cpu_job.py", {"STENCIL_SUBAGENT": "1"}, [], set(), "background"),
    ("disown", {"STENCIL_SUBAGENT": "1"}, [], set(), "background"),
    ("python cpu_job.py && echo done", {"STENCIL_SUBAGENT": "1"}, [], set(), None),
    ("nohup python cpu_job.py", {}, [], set(), None),
]


@pytest.mark.parametrize("command,env,gpu_pids,owned_pids,reason", CASES)
def test_decision_table(guard, command, env, gpu_pids, owned_pids, reason):
    got = guard.decision(command, env=env, gpu_pids=gpu_pids, owned_pids=owned_pids)
    assert (got is None) == (reason is None), (command, got)
    if reason is not None:
        assert reason in got


def test_deny_payload_is_one_line_json(guard):
    payload = guard.deny_payload("sealed input denied")
    assert "\n" not in payload
    parsed = json.loads(payload)
    assert parsed["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert parsed["hookSpecificOutput"]["permissionDecisionReason"] == "sealed input denied"
