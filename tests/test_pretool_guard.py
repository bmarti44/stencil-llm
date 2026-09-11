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
    (
        "python scripts/ledger_eval.py --refit-report data/bench/multiif_en.jsonl",
        {},
        [],
        set(),
        None,
    ),
    (
        "python scripts/bfcl_mt.py --train-report data/bench/bfcl_v3_mt",
        {},
        [],
        set(),
        None,
    ),
    (
        "python scripts/ledger_kv_probe.py --training-report data/bench/probe.jsonl",
        {},
        [],
        set(),
        None,
    ),
    ("git log -S train -- data/bench/multiif_en.jsonl", {}, [], set(), None),
    ("ls data/bench/train-split.jsonl", {}, [], set(), None),
    ("sha256sum data/bench/refit.jsonl", {}, [], set(), None),
    (
        "python scripts/fit_finder.py data/bench/multiif_en.jsonl",
        {},
        [],
        set(),
        "eval data used for fitting",
    ),
    (
        "python scripts/training_job.py data/bench/multiif_en.jsonl",
        {},
        [],
        set(),
        "eval data used for fitting",
    ),
    (
        "python scripts/select.py --train results/qwen/b4-multiif-base",
        {},
        [],
        set(),
        "eval data used for fitting",
    ),
    (
        "python -m stencil.salience2 data/bench/bfcl_v3_mt",
        {},
        [],
        set(),
        "eval data used for fitting",
    ),
    ("cat data/bench/ifeval_input_data.jsonl", {}, [], set(), "sealed"),
    ("rg needle data/bench/ifeval_input_data.jsonl", {}, [], set(), "sealed"),
    ("python scripts/b4_ifeval.py", {}, [], set(), None),
    (
        "uv run python scripts/b0_score_parity.py data/bench/ifeval_input_data.jsonl",
        {},
        [],
        set(),
        None,
    ),
    (
        "python scripts/b4_ifeval.py && cat data/bench/ifeval_input_data.jsonl",
        {},
        [],
        set(),
        "sealed",
    ),
    ("kill -TERM 123", {}, [], set(), "pid"),
    ("kill -TERM 123", {}, [], {123}, None),
    ("kill 123", {}, [], set(), "pid"),
    ("pkill python", {}, [], set(), "pid"),
    ("killall python", {}, [], set(), "pid"),
    (
        "python -c 'import os, signal; os.kill(123, signal.SIGTERM)'",
        {},
        [],
        set(),
        "pid",
    ),
    (
        "python -c 'import os, signal; os.kill(123, signal.SIGTERM)'",
        {},
        [],
        {123},
        None,
    ),
    ("python -c 'import torch'", {}, [999], set(), "GPU busy"),
    ("python -c 'print(\"cuda\")'", {}, [999], set(), "GPU busy"),
    (
        "uv run python scripts/ledger_eval.py --model models/qwen.pt",
        {},
        [999],
        set(),
        "GPU busy",
    ),
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
    (
        "cat > brief.md <<'EOF'\nNever kill or signal any process.\nEOF",
        {},
        [],
        set(),
        None,
    ),
    (
        "git commit -m 'guard: deny pkill by name; kill only owned pids'",
        {},
        [],
        set(),
        None,
    ),
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


def _tree(parents):
    return lambda pid: parents.get(pid)


def test_registry_pid_is_owned(guard, tmp_path):
    registry = tmp_path / "owned"
    registry.write_text("4242\n")
    assert (
        guard.decision(
            "kill -TERM 4242",
            env={},
            gpu_pids=[],
            registry=registry,
            parent_of=_tree({}),
        )
        is None
    )
    assert "pid" in guard.decision(
        "kill -TERM 4243", env={}, gpu_pids=[], registry=registry, parent_of=_tree({})
    )


def test_descendant_of_registered_pid_is_owned(guard, tmp_path):
    registry = tmp_path / "owned"
    registry.write_text("100\n")
    parents = {300: 200, 200: 100, 999: 1}
    assert (
        guard.decision(
            "kill -KILL 300",
            env={},
            gpu_pids=[],
            registry=registry,
            parent_of=_tree(parents),
        )
        is None
    )
    assert "pid" in guard.decision(
        "kill -KILL 999",
        env={},
        gpu_pids=[],
        registry=registry,
        parent_of=_tree(parents),
    )
    # Name-based termination stays denied regardless of ownership.
    assert "name-based" in guard.decision(
        "pkill codex", env={}, gpu_pids=[], registry=registry, parent_of=_tree(parents)
    )


def test_missing_registry_is_empty(guard, tmp_path):
    assert "pid" in guard.decision(
        "kill 7", env={}, gpu_pids=[], registry=tmp_path / "absent", parent_of=_tree({})
    )


def test_deny_payload_is_one_line_json(guard):
    payload = guard.deny_payload("sealed input denied")
    assert "\n" not in payload
    parsed = json.loads(payload)
    assert parsed["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert (
        parsed["hookSpecificOutput"]["permissionDecisionReason"]
        == "sealed input denied"
    )


def test_textual_guard_boundary_is_explicit(guard):
    doc = guard.__doc__ or ""
    assert "Boundary" in doc
    for limitation in ("variable splitting", "eval", "base64", "defense in depth"):
        assert limitation in doc


def test_shared_mode_tolerates_reserved_pids_only(guard, tmp_path):
    reservations = tmp_path / "res"
    reservations.write_text('{"name":"peer","pid":4152283,"peak_gb":12}\n')
    flag = tmp_path / "share"
    common = dict(
        owned_pids=set(),
        reservations=reservations,
        share_flag=flag,
        registry=tmp_path / "none",
    )
    cmd = "python -c 'import " + "torch'"
    assert "GPU busy" in guard.decision(cmd, env={}, gpu_pids=[4152283], **common)
    flag.write_text("1\n")
    assert guard.decision(cmd, env={}, gpu_pids=[4152283], **common) is None
    reason = guard.decision(cmd, env={}, gpu_pids=[4152283, 777], **common)
    assert "unreserved compute pid(s) 777" in reason
    env = {"STENCIL_GPU_FOREIGN_PIDS": "777"}
    assert guard.decision(cmd, env=env, gpu_pids=[4152283, 777], **common) is None
    flag.unlink()
    env = {"STENCIL_GPU_SHARE": "1"}
    assert guard.decision(cmd, env=env, gpu_pids=[4152283], **common) is None
    assert guard.decision(
        "nvidia-smi --gpu-reset", env=env, gpu_pids=[4152283], **common
    )


def test_shared_mode_accepts_descendants_of_reserved_pids(guard, tmp_path):
    reservations = tmp_path / "res"
    reservations.write_text('{"name":"peer","pid":100,"peak_gb":12}\n')
    common = dict(
        owned_pids=set(),
        reservations=reservations,
        share_flag=tmp_path / "share",
        registry=tmp_path / "none",
        parent_of=_tree({101: 100, 102: 101, 300: 1}),
    )
    env = {"STENCIL_GPU_SHARE": "1"}
    cmd = "python -c 'import " + "torch'"
    assert guard.decision(cmd, env=env, gpu_pids=[102], **common) is None
    assert "unreserved compute pid(s) 300" in guard.decision(
        cmd, env=env, gpu_pids=[102, 300], **common
    )


def test_shared_mode_accepts_session_members_of_reserved_pids(guard, tmp_path):
    """A reservation wrapper that exited leaves its child reparented to pid 1 but
    still in the wrapper's session (observed 2026-09-11, peer pid 358813)."""
    reservations = tmp_path / "res"
    reservations.write_text('{"name":"peer","pid":100,"peak_gb":12}\n')
    common = dict(
        owned_pids=set(),
        reservations=reservations,
        share_flag=tmp_path / "share",
        registry=tmp_path / "none",
        parent_of=_tree({102: 1, 300: 1}),
        session_of=lambda pid: {102: 100, 300: 300}.get(pid),
    )
    env = {"STENCIL_GPU_SHARE": "1"}
    cmd = "python -c 'import " + "torch'"
    assert guard.decision(cmd, env=env, gpu_pids=[102], **common) is None
    assert "unreserved compute pid(s) 300" in guard.decision(
        cmd, env=env, gpu_pids=[102, 300], **common
    )
