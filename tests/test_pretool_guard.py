# ruff: noqa: E501
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
    ("python scripts/ledger_eval.py --refit-report data/bench/multiif_en.jsonl", {}, [], set(), None),
    ("python scripts/bfcl_mt.py --train-report data/bench/bfcl_v3_mt", {}, [], set(), None),
    ("python scripts/ledger_kv_probe.py --training-report data/bench/probe.jsonl", {}, [], set(), None),
    ("git log -S train -- data/bench/multiif_en.jsonl", {}, [], set(), None),
    ("ls data/bench/train-split.jsonl", {}, [], set(), None),
    ("sha256sum data/bench/refit.jsonl", {}, [], set(), None),
    ("python scripts/fit_finder.py data/bench/multiif_en.jsonl", {}, [], set(), "eval data used for fitting"),
    ("python scripts/training_job.py data/bench/multiif_en.jsonl", {}, [], set(), "eval data used for fitting"),
    ("python scripts/select.py --train results/qwen/b4-multiif-base", {}, [], set(), "eval data used for fitting"),
    ("python -m stencil.salience2 data/bench/bfcl_v3_mt", {}, [], set(), "eval data used for fitting"),
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
    # Prose mentioning process termination (heredoc briefs, commit messages) must not trip the guard.
    ("cat > brief.md <<'EOF'\nNever kill or signal any process.\nEOF", {}, [], set(), None),
    ("git commit -m 'guard: deny pkill by name; kill only owned pids'", {}, [], set(), None),
    ("echo done; kill 123", {}, [], set(), "pid"),
    ("sudo kill -9 123", {}, [], set(), "pid"),
    ("echo x | xargs kill", {}, [], set(), "pid"),
    ("command kill 123", {}, [], set(), "pid"),
    ("command kill 123", {}, [], {123}, None),
    ("builtin kill 123", {}, [], set(), "pid"),
    ("builtin kill 123", {}, [], {123}, None),
    (r"\kill 123", {}, [], set(), "pid"),
    (r"\kill 123", {}, [], {123}, None),
    ("kill -9 123", {}, [], {123}, None),
    ("kill -s TERM 123", {}, [], {123}, None),
    ("kill -SIGTERM 123", {}, [], {123}, None),
    # Every residual option-bearing wrapper form must locate the real command.
    ("sudo -u root kill 123", {}, [], set(), "pid"),
    ("sudo -u root kill 123", {}, [], {123}, None),
    ("sudo -n kill 123", {}, [], set(), "pid"),
    ("sudo -n kill 123", {}, [], {123}, None),
    ("env -u NAME kill 123", {}, [], set(), "pid"),
    ("env -u NAME kill 123", {}, [], {123}, None),
    ("env -i X=1 kill 123", {}, [], set(), "pid"),
    ("env -i X=1 kill 123", {}, [], {123}, None),
    ("printf 123 | xargs -n 1 kill", {}, [], set(), "pid"),
    ("printf 123 | xargs -n 1 kill", {}, [], {123}, None),
    ("printf 123 | xargs -I{} -n1 kill {}", {}, [], set(), "pid"),
    ("printf 123 | xargs -I{} -n1 kill {}", {}, [], {123}, None),
    ("command -p kill 123", {}, [], set(), "pid"),
    ("command -p kill 123", {}, [], {123}, None),
    ("nice -n 5 kill 123", {}, [], set(), "pid"),
    ("nice -n 5 kill 123", {}, [], {123}, None),
    ("timeout 5 kill 123", {}, [], set(), "pid"),
    ("timeout 5 kill 123", {}, [], {123}, None),
    ("kill -n 9 123", {}, [], set(), "pid"),
    ("kill -n 9 123", {}, [], {123}, None),
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


def test_textual_guard_boundary_is_explicit(guard):
    doc = guard.__doc__ or ""
    assert "Boundary" in doc
    for limitation in ("variable splitting", "eval", "base64", "defense in depth"):
        assert limitation in doc
