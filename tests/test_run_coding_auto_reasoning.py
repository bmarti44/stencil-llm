import hashlib
import json
from pathlib import Path

import pytest

from tools import run_coding_auto_reasoning as launcher


class Process:
    next_pid = 12000

    def __init__(self, returncode=0, stdout=b"", stderr=b""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.pid = Process.next_pid
        Process.next_pid += 1

    def communicate(self, timeout=None):
        assert timeout is None or timeout >= 0
        return self.stdout, self.stderr

    def terminate(self):
        self.returncode = -15

    def kill(self):
        self.returncode = -9


def _sha(path):
    return launcher._sha256(Path(path))


def _receipt(path):
    path = Path(path)
    return {
        "path": str(path.resolve()),
        "bytes": path.stat().st_size,
        "sha256": _sha(path),
        "documents": 1,
        "read_error": None,
        "parse_error": None,
    }


def _write_qualification(root):
    root = Path(root)
    for relative in launcher.PREVIEW_CODE_FILES:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"source:{relative}\n", encoding="utf-8")

    input_paths = []
    documents = []
    for project_index in range(2):
        episode_id = f"auto-{project_index}"
        document = {
            "public": {
                "episode_id": episode_id,
                "rounds": [{"index": index} for index in range(3)],
            },
            "private": {
                "rounds": [
                    {
                        "index": index,
                        "reference_patch": (
                            f"def task_{index}(value):\n    return value\n"
                        ),
                        "oracle": {
                            "effective_rules": [
                                {
                                    "text": f"rule {project_index}-{index}",
                                    "source_ids": [f"source-{project_index}-{index}"],
                                }
                            ]
                        },
                    }
                    for index in range(3)
                ]
            },
        }
        path = (
            root
            / "results/coding-auto-reasoning"
            / f"author-{project_index:02d}/reviewed.json"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(document), encoding="utf-8")
        input_paths.append(path)
        documents.append(document)

    preflight_sources = {
        relative: _sha(root / relative) for relative in launcher.PREFLIGHT_CODE_FILES
    }
    projects = []
    for document, path in zip(documents, input_paths, strict=True):
        projects.append(
            {
                "schema_version": 1,
                "kind": "coding-competence-cpu-preflight",
                "status": "PASS",
                "model_calls": 0,
                "documents": 1,
                "inputs": [_receipt(path)],
                "code_sha256": preflight_sources,
                "episodes": [
                    {
                        "episode_id": document["public"]["episode_id"],
                        "valid": True,
                        "errors": [],
                        "rounds": [{"index": index} for index in range(3)],
                    }
                ],
                "execution_count": 10,
                "elapsed_seconds": 0.1,
            }
        )
    receipts = [_receipt(path) for path in input_paths]
    preflight = {
        "schema_version": 1,
        "kind": "coding-auto-reasoning-cpu-preflight",
        "status": "PASS",
        "model_calls": 0,
        "documents": 2,
        "inputs": receipts,
        "projects": projects,
        "execution_count": 20,
        "elapsed_seconds": 0.2,
    }

    actions = []
    cold = []
    growth = []
    for document in documents:
        episode_id = document["public"]["episode_id"]
        for round_index in range(3):
            cold.append(
                {
                    "episode_id": episode_id,
                    "round_index": round_index,
                    "local_serialized_request_tokens": 100,
                    "local_serialized_request_with_output": 2148,
                    "local_serialized_request_below_context": True,
                    "local_count_is_native_prompt_tokens": False,
                }
            )
            for kind in ("record_focus", "replace_function"):
                body = launcher._expected_reference_body(document, round_index, kind)
                actions.append(
                    {
                        "episode_id": episode_id,
                        "round_index": round_index,
                        "kind": kind,
                        "argument_body": body.decode("utf-8"),
                        "argument_body_sha256": hashlib.sha256(body).hexdigest(),
                        "argument_body_bytes": len(body),
                        "argument_tokens": 100,
                        "full_reasoning_bound_tokens": 1024,
                        "reasoning_delimiter_and_eos_tokens": 3,
                        "available_final_tokens": 1021,
                        "generation_headroom": 921,
                        "eligible": True,
                    }
                )
            for attempt_index in range(2):
                prior = round_index * 2 + attempt_index
                growth.append(
                    {
                        "episode_id": episode_id,
                        "round_index": round_index,
                        "attempt_index": attempt_index,
                        "visible_authentic_source_bytes": 100,
                        "maximum_prior_worker_action_pairs": prior,
                        "maximum_repeated_module_observations": prior + 1,
                        "module_byte_limit_each_observation": 1000,
                        "submitted_source_byte_limit_each_action": 1000,
                        "universal_future_prompt_fit_claim": False,
                    }
                )
    preview = {
        "schema_version": 1,
        "kind": "coding-auto-reasoning-preview",
        "status": "PASS",
        "model_calls": 0,
        "documents": 2,
        "scheduled_requests": 6,
        "max_attempts_per_request": 2,
        "max_model_calls": 18,
        "settings": {
            "model": "/model",
            "max_output_tokens": 2048,
            "reasoning_token_budget": 1024,
            "available_final_tokens": 1021,
            "context_tokens": 32768,
            "minimum_generation_headroom": 128,
            "seed": 20260908,
            "temperature": 0.6,
            "top_p": 0.95,
            "top_k": 20,
            "min_p": 0.0,
        },
        "inputs": receipts,
        "code_sha256": {
            relative: _sha(root / relative) for relative in launcher.PREVIEW_CODE_FILES
        },
        "preflight": preflight,
        "selector_cold_requests": cold,
        "reference_actions": actions,
        "all_reference_actions_headroom": True,
        "all_cpu_preflight_passed": True,
        "future_actual_prompt_claim": False,
        "actual_native_render_required_before_every_generation": True,
        "conservative_growth": growth,
        "resource_bounds": {
            "maximum_render_requests": 18,
            "maximum_generation_requests": 18,
            "maximum_http_requests": 36,
            "maximum_sandbox_checks": 42,
            "maximum_prior_worker_action_pairs_per_prompt": 5,
            "maximum_repeated_module_observations_per_prompt": 6,
        },
        "cpu_elapsed_seconds": 0.3,
    }
    result_base = root / "results/coding-auto-reasoning"
    preflight_path = result_base / "preflight.json"
    preview_path = result_base / "preview.json"
    preflight_path.write_text(json.dumps(preflight), encoding="utf-8")
    preview_path.write_text(json.dumps(preview), encoding="utf-8")
    return tuple(input_paths), preflight_path, preview_path


def test_plan_reuses_exact_reasoning_container_and_fixed_budget():
    run = launcher.RESULTS_DIR / "run-unit"
    plan = launcher.make_plan(run, container_name="auto-unit")

    assert plan["container_command"] == launcher.smoke_launcher._container_command(
        "auto-unit"
    )
    assert plan["driver"] == str(launcher.ROOT / "scripts/coding_auto_reasoning.py")
    assert plan["input"] == str(launcher.INPUT_ROOT)
    assert plan["maximum_model_calls"] == 18
    assert plan["max_output_tokens"] == 2048
    assert plan["thinking_token_budget"] == 1024
    assert plan["context_window_tokens"] == 32768
    assert plan["reservation_seconds"] == 3000
    assert plan["startup_ceiling_seconds"] == 600
    assert plan["cleanup_reserve_seconds"] == 60
    assert plan["combined_candidate_charge_seconds"] == pytest.approx(3516.914703271992)
    assert plan["candidate_ceiling_seconds"] == 3600


def test_artifacts_bind_two_inputs_cpu_preview_and_sources(tmp_path):
    input_paths, preflight, preview = _write_qualification(tmp_path)

    receipt = launcher.validate_artifacts(
        input_paths, preflight, preview, root=tmp_path
    )

    assert receipt["documents"] == 2
    assert receipt["scheduled_requests"] == 6
    assert receipt["max_model_calls"] == 18
    assert receipt["minimum_reference_headroom"] == 921


def test_prepare_rejects_stale_preview_before_environment(monkeypatch, tmp_path):
    _write_qualification(tmp_path)
    stale = tmp_path / "scripts/coding_auto_reasoning.py"
    stale.write_text("changed after preview\n", encoding="utf-8")
    monkeypatch.setattr(
        launcher,
        "validate_smoke_evidence",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("smoke validation must follow artifact validation")
        ),
    )
    monkeypatch.setattr(
        launcher,
        "qualify_environment",
        lambda **_kwargs: (_ for _ in ()).throw(
            AssertionError("environment startup checks must not run")
        ),
    )

    with pytest.raises(RuntimeError, match="source snapshot mismatch"):
        launcher.prepare_execution(
            tmp_path / "results/coding-auto-reasoning/run-unit",
            root=tmp_path,
            container_name="auto-unit",
        )


def test_dry_run_does_not_launch_or_create_state(monkeypatch, tmp_path, capsys):
    results = tmp_path / "coding-auto-reasoning"
    results.mkdir()
    run = results / "run-dry"
    flag = results / "RUNNING.flag"
    monkeypatch.setattr(launcher, "RESULTS_DIR", results)
    monkeypatch.setattr(launcher, "RUN_FLAG", flag)
    monkeypatch.setattr(
        launcher.owned,
        "register_pid",
        lambda _pid: (_ for _ in ()).throw(AssertionError("must be a no-op")),
    )

    assert launcher.main(["--run-dir", str(run)]) == 0
    plan = json.loads(capsys.readouterr().out)
    assert plan["execute"] is False
    assert not run.exists()
    assert not flag.exists()


def test_reused_lifecycle_forwards_remaining_deadline_and_driver_plan(tmp_path):
    run = tmp_path / "run"
    run.mkdir()
    flag = tmp_path / "RUNNING.flag"
    flag.write_text("owned\n", encoding="utf-8")
    plan = launcher.make_plan(run, container_name="auto-owned")
    commands = []

    def start(command, **_kwargs):
        commands.append(list(command))
        if command == plan["container_command"]:
            return Process(stdout=b"container-id\n")
        if command[0] == str(launcher.ROOT / ".venv/bin/python"):
            return Process(returncode=0)
        return Process(returncode=0)

    code, lifecycle = launcher.owned.run_lifecycle(
        plan,
        run_flag=flag,
        start=start,
        wait_server=lambda *_args, **_kwargs: None,
        clock=lambda: 10.0,
        wall_clock=lambda: 20.0,
    )

    assert code == 0
    assert lifecycle["cleaned"] is True
    driver = json.loads((run / "driver-command.json").read_text())
    assert driver == [
        str(launcher.ROOT / ".venv/bin/python"),
        str(launcher.ROOT / "scripts/coding_auto_reasoning.py"),
        "--input",
        str(launcher.INPUT_ROOT),
        "--output-dir",
        str(run / "calls"),
        "--base-url",
        "http://127.0.0.1:18088",
        "--model",
        "/model",
        "--deadline-seconds",
        "2940",
    ]
    assert not flag.exists()


def test_combined_candidate_budget_violation_rejects(monkeypatch):
    monkeypatch.setattr(launcher, "RESERVATION_SECONDS", 3100)
    with pytest.raises(RuntimeError, match="candidate ceiling"):
        launcher.validate_combined_budget(
            {
                "elapsed_seconds": launcher.SMOKE_ACTUAL_SECONDS,
                "status": "DRIVER_EXITED",
                "driver_exit_code": 0,
                "cleaned": True,
                "cleanup_evidence_complete": True,
            }
        )


def test_existing_run_sentinel_survives_execute_reservation(monkeypatch, tmp_path):
    results = tmp_path / "coding-auto-reasoning"
    run = results / "run-existing"
    run.mkdir(parents=True)
    sentinel_path = run / "lifecycle.json"
    sentinel = b'{"status":"EXISTING"}\n'
    sentinel_path.write_bytes(sentinel)
    flag = results / "RUNNING.flag"
    prepared = []
    monkeypatch.setattr(launcher, "RESULTS_DIR", results)
    monkeypatch.setattr(launcher, "RUN_FLAG", flag)
    monkeypatch.setattr(
        launcher,
        "prepare_execution",
        lambda *_args, **_kwargs: prepared.append(True),
    )

    with pytest.raises(FileExistsError, match="run directory already exists"):
        launcher.main(["--run-dir", str(run), "--execute"])

    assert prepared == []
    assert sentinel_path.read_bytes() == sentinel
    assert not flag.exists()


def test_prelaunch_failure_removes_only_owned_flag(monkeypatch, tmp_path):
    results = tmp_path / "coding-auto-reasoning"
    results.mkdir()
    run = results / "run-new"
    own_flag = results / "RUNNING.flag"
    other_flag = tmp_path / "other/RUNNING.flag"
    other_flag.parent.mkdir()
    other_flag.write_text("other\n", encoding="utf-8")
    snapshot = {"bound": "hash"}

    class Lock:
        def close(self):
            pass

    monkeypatch.setattr(launcher, "RESULTS_DIR", results)
    monkeypatch.setattr(launcher, "RUN_FLAG", own_flag)
    monkeypatch.setattr(launcher.owned, "register_pid", lambda _pid: None)
    monkeypatch.setattr(
        launcher,
        "prepare_execution",
        lambda *_args, **_kwargs: {
            "environment": {"git_head": "a" * 40},
            "tracked_sha256": snapshot,
            "model_metadata_sha256": {},
        },
    )
    monkeypatch.setattr(launcher.owned, "acquire_review_lock", lambda _path: Lock())
    monkeypatch.setattr(launcher.fcntl, "flock", lambda *_args: None)
    monkeypatch.setattr(
        launcher,
        "recheck_resource_exclusivity",
        lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("resource changed")),
    )

    with pytest.raises(RuntimeError, match="resource changed"):
        launcher.main(["--run-dir", str(run), "--execute"])

    assert run.exists()
    assert json.loads((run / "lifecycle.json").read_text())["status"] == (
        "INCOMPLETE_BEFORE_SERVER"
    )
    assert not own_flag.exists()
    assert other_flag.read_text() == "other\n"
