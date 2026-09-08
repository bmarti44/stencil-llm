import base64
import hashlib
import json

import pytest

from tools import run_coding_competence as launcher


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_qualified_artifacts(tmp_path):
    sources = {}
    for relative in launcher.RUNTIME_CODE_FILES:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# {relative}\n", encoding="utf-8")
        sources[relative] = _sha(path)

    data_path = tmp_path / "kimi-dev-reviewed.json"
    documents = [
        {
            "public": {
                "episode_id": f"episode-{index}",
                "rounds": [{"index": round_index} for round_index in range(3)],
            },
            "private": {
                "rounds": [
                    {
                        "index": value,
                        "reference_patch": (
                            f"def target_{value}(value):\n    return value\n"
                        ),
                    }
                    for value in range(3)
                ]
            },
        }
        for index in range(4)
    ]
    data_path.write_text(json.dumps(documents), encoding="utf-8")
    data_receipt = {
        "path": str(data_path),
        "bytes": data_path.stat().st_size,
        "sha256": _sha(data_path),
        "documents": 4,
        "read_error": None,
        "parse_error": None,
    }

    preflight_path = tmp_path / "preflight.json"
    preflight = {
        "schema_version": 1,
        "kind": "coding-competence-cpu-preflight",
        "model_calls": 0,
        "status": "PASS",
        "documents": 4,
        "inputs": [data_receipt],
        "code_sha256": {
            key: value
            for key, value in sources.items()
            if key in launcher.PREFLIGHT_CODE_FILES
        },
        "episodes": [
            {
                "episode_id": f"episode-{index}",
                "valid": True,
                "errors": [],
                "rounds": [
                    {
                        "index": round_index,
                        "provisional_generation_headroom": 128,
                    }
                    for round_index in range(3)
                ],
            }
            for index in range(4)
        ],
        "execution_count": 12,
        "elapsed_seconds": 0.5,
    }
    preflight_path.write_text(json.dumps(preflight), encoding="utf-8")

    preview_path = tmp_path / "preview.json"
    preview = {
        "schema_version": 1,
        "kind": "coding-competence-native-preview",
        "model_calls": 0,
        "status": "PASS",
        "documents": 4,
        "scheduled_requests": 12,
        "max_attempts_per_request": 3,
        "max_model_calls": 36,
        "inputs": [data_receipt],
        "code_sha256": sources,
        "settings": {
            "model": "/model",
            "seed": 20260908,
            "temperature": 0,
            "max_output_tokens": 1024,
            "context_tokens": 32768,
            "minimum_generation_headroom": 128,
        },
        "reference_actions": [],
        "all_reference_actions_headroom": True,
        "context_preflight": {
            "actual_cold_request_count": 4,
            "cold_requests": [
                {
                    "episode_id": f"episode-{episode}",
                    "round_index": 0,
                    "local_serialized_request_with_output": 2048,
                    "local_serialized_request_below_context": True,
                    "local_count_is_native_prompt_tokens": False,
                }
                for episode in range(4)
            ],
            "later_actual_requests_known": False,
            "local_counts_are_provisional": True,
            "all_local_cold_serializations_below_context": True,
            "authoritative_render_required_before_every_model_call": True,
            "conservative_bounds": [
                {
                    "episode_id": f"episode-{episode}",
                    "round_index": round_index,
                    "attempt_index": attempt,
                    "prior_action_pairs": round_index * 3 + attempt,
                    "repeated_current_module_observations": (
                        round_index * 3 + attempt + 1
                    ),
                    "public_outcome_slots": round_index * 2 + attempt,
                    "context_with_output_bound": 32000,
                    "fits_context": True,
                    "future_actual_prompt_claim": False,
                }
                for episode in range(4)
                for round_index in range(3)
                for attempt in range(3)
            ],
            "all_conservative_bounds_fit": True,
            "bound_interpretation": "Absolute allowed-size envelopes.",
        },
        "resource_bounds": {
            "maximum_render_requests": 36,
            "maximum_generation_requests": 36,
            "maximum_http_requests": 72,
            "maximum_sandbox_checks": 100,
            "maximum_prior_action_pairs_per_prompt": 8,
            "maximum_repeated_module_observations_per_prompt": 9,
        },
    }
    for episode in range(4):
        for round_index in range(3):
            source = documents[episode]["private"]["rounds"][round_index][
                "reference_patch"
            ]
            body = json.dumps(
                {"source": source},
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
            argument_tokens = 895
            preview["reference_actions"].append(
                {
                    "episode_id": f"episode-{episode}",
                    "round_index": round_index,
                    "argument_body": body.decode(),
                    "argument_body_base64": base64.b64encode(body).decode(),
                    "argument_body_sha256": hashlib.sha256(body).hexdigest(),
                    "argument_body_bytes": len(body),
                    "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
                    "argument_tokens": argument_tokens,
                    "eos_allowance_tokens": 1,
                    "response_tokens_with_eos": argument_tokens + 1,
                    "generation_headroom": 1024 - argument_tokens - 1,
                    "eligible": True,
                }
            )
    preview_path.write_text(json.dumps(preview), encoding="utf-8")
    return data_path, preflight_path, preview_path


def test_artifacts_reject_cap_or_binding_before_startup(tmp_path):
    data, preflight, preview = _write_qualified_artifacts(tmp_path)
    receipt = launcher.validate_artifacts(
        data,
        preflight,
        preview,
        root=tmp_path,
    )
    assert receipt["documents"] == 4
    assert receipt["scheduled_requests"] == 12

    value = json.loads(preview.read_text())
    value["settings"]["max_output_tokens"] = 1025
    preview.write_text(json.dumps(value), encoding="utf-8")
    started = False

    def forbidden_start(*_args, **_kwargs):
        nonlocal started
        started = True
        raise AssertionError("server must not start")

    with pytest.raises(RuntimeError, match="max_output_tokens"):
        launcher.prepare_execution(
            tmp_path / "run-cap",
            data_path=data,
            preflight_path=preflight,
            preview_path=preview,
            root=tmp_path,
            command=forbidden_start,
        )
    assert not started
    assert not (tmp_path / "run-cap").exists()


def test_unqualified_headroom_and_changed_source_are_rejected(tmp_path):
    data, preflight, preview = _write_qualified_artifacts(tmp_path)
    value = json.loads(preview.read_text())
    value["reference_actions"][3]["generation_headroom"] = 127
    preview.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(RuntimeError, match="headroom"):
        launcher.validate_artifacts(data, preflight, preview, root=tmp_path)

    data, preflight, preview = _write_qualified_artifacts(tmp_path)
    (tmp_path / launcher.RUNTIME_CODE_FILES[0]).write_text(
        "# changed after preview\n", encoding="utf-8"
    )
    with pytest.raises(RuntimeError, match="source snapshot"):
        launcher.validate_artifacts(data, preflight, preview, root=tmp_path)


def test_conservative_context_receipt_must_be_internally_consistent(tmp_path):
    data, preflight, preview = _write_qualified_artifacts(tmp_path)
    value = json.loads(preview.read_text())
    value["context_preflight"]["conservative_bounds"][0]["fits_context"] = False
    value["context_preflight"]["all_conservative_bounds_fit"] = False
    value["context_preflight"]["conservative_bounds"][0][
        "context_with_output_bound"
    ] = 32769
    preview.write_text(json.dumps(value), encoding="utf-8")
    receipt = launcher.validate_artifacts(data, preflight, preview, root=tmp_path)
    assert receipt["all_conservative_bounds_fit"] is False


def test_dirty_or_untracked_bound_file_is_rejected():
    calls = 0

    class Result:
        stdout = b""

    def command(_argv, **_kwargs):
        nonlocal calls
        calls += 1
        result = Result()
        if calls == 2:
            result.stdout = b"?? scripts/coding_competence_run.py\n"
        return result

    with pytest.raises(RuntimeError, match="dirty or untracked"):
        launcher._tracked_clean(
            "scripts/coding_competence_run.py", command=command
        )


def test_changed_current_trunk_receipt_is_rejected(tmp_path):
    model = tmp_path / "models/model.bin"
    model.parent.mkdir()
    model.write_bytes(b"frozen")
    stat = model.stat()
    receipt = tmp_path / "current-trunk-hashes.json"
    receipt.write_text(
        json.dumps(
            {
                "files": [
                    {
                        "path": "models/model.bin",
                        "bytes": stat.st_size,
                        "mtime_ns": stat.st_mtime_ns,
                        "sha256": _sha(model),
                    }
                ],
                "total_bytes": stat.st_size,
            }
        ),
        encoding="utf-8",
    )
    assert launcher.validate_trunk_hashes(receipt, root=tmp_path)["files"] == 1
    model.write_bytes(b"changed")
    with pytest.raises(RuntimeError, match="current trunk file changed"):
        launcher.validate_trunk_hashes(receipt, root=tmp_path)


def test_active_flag_refuses_before_any_process_start(tmp_path):
    flag = tmp_path / "results/other/RUNNING.flag"
    flag.parent.mkdir(parents=True)
    flag.write_text("active\n", encoding="utf-8")

    def forbidden(*_args, **_kwargs):
        raise AssertionError("resource process must not start")

    with pytest.raises(RuntimeError, match="active run flag"):
        launcher.qualify_environment(root=tmp_path, command=forbidden)


def test_wait_for_server_rejects_success_after_startup_ceiling():
    times = iter([599.0, 601.0])

    class Response:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    with pytest.raises(TimeoutError, match="startup exceeded"):
        launcher.wait_for_server(
            0.0,
            ceiling_seconds=600,
            clock=lambda: next(times),
            opener=lambda *_args, **_kwargs: Response(),
            sleeper=lambda _seconds: None,
        )


class _FakeProcess:
    def __init__(self, pid, returncode=0, stdout=b"", stderr=b""):
        self.pid = pid
        self.returncode = returncode
        self._stdout = stdout
        self._stderr = stderr

    def communicate(self, timeout=None):
        assert timeout is None or timeout >= 0
        return self._stdout, self._stderr


def test_remaining_deadline_and_driver_status_are_preserved(tmp_path):
    run = tmp_path / "run"
    run.mkdir()
    flag = tmp_path / "RUNNING.flag"
    flag.write_text("reserved\n", encoding="utf-8")
    plan = launcher.make_plan(run, container_name="owned-container")
    times = iter([100.0, 100.0, 150.2, 151.0, 151.5, 152.0, 152.5, 153.0])
    last_time = [100.0]

    def clock():
        last_time[0] = next(times, last_time[0])
        return last_time[0]
    starts = []

    def start(command, **kwargs):
        starts.append(list(command))
        if command[:2] == ["docker", "run"]:
            return _FakeProcess(10, stdout=b"container-id\n")
        if command[0].endswith("python"):
            return _FakeProcess(11, returncode=1)
        return _FakeProcess(12)

    code, lifecycle = launcher.run_lifecycle(
        plan,
        run_flag=flag,
        start=start,
        wait_server=lambda *_args, **_kwargs: None,
        clock=clock,
        wall_clock=lambda: 1000.0,
    )
    assert code == 1
    driver = json.loads((run / "driver-command.json").read_text())
    deadline_index = driver.index("--deadline-seconds") + 1
    assert int(driver[deadline_index]) == 2589
    assert lifecycle["driver_exit_code"] == 1
    assert starts[0] == plan["container_command"]
    assert not flag.exists()


def test_signal_driver_status_becomes_technical_incomplete(tmp_path):
    run = tmp_path / "run"
    run.mkdir()
    flag = tmp_path / "RUNNING.flag"
    flag.write_text("reserved\n", encoding="utf-8")
    plan = launcher.make_plan(run, container_name="owned-container")

    def start(command, **_kwargs):
        if command[:2] == ["docker", "run"]:
            return _FakeProcess(50, stdout=b"container-id\n")
        if command[0].endswith("python"):
            return _FakeProcess(51, returncode=-9, stderr=b"partial driver log")
        return _FakeProcess(52)

    code, lifecycle = launcher.run_lifecycle(
        plan,
        run_flag=flag,
        start=start,
        wait_server=lambda *_args, **_kwargs: None,
        clock=lambda: 10.0,
        wall_clock=lambda: 20.0,
    )
    assert code == 2
    assert lifecycle["status"] == "INCOMPLETE_DRIVER"
    assert lifecycle["driver_exit_code"] == -9
    assert (run / "driver.log").read_bytes() == b"partial driver log"
    assert len(json.loads((run / "cleanup-receipts.json").read_text())) == 3
    assert not flag.exists()


def test_startup_failure_persists_partial_receipts_and_cleans_owned_only(tmp_path):
    run = tmp_path / "run"
    run.mkdir()
    flag = tmp_path / "RUNNING.flag"
    flag.write_text("reserved\n", encoding="utf-8")
    plan = launcher.make_plan(run, container_name="only-this-container")
    commands = []

    def start(command, **_kwargs):
        commands.append(list(command))
        if command[:2] == ["docker", "run"]:
            return _FakeProcess(20, stdout=b"container-id\n")
        return _FakeProcess(21, returncode=0, stdout=b"server log")

    code, lifecycle = launcher.run_lifecycle(
        plan,
        run_flag=flag,
        start=start,
        wait_server=lambda *_args, **_kwargs: (_ for _ in ()).throw(
            TimeoutError("startup exceeded prospective ceiling")
        ),
        clock=lambda: 10.0,
        wall_clock=lambda: 20.0,
    )
    assert code == 2
    assert lifecycle["status"] == "INCOMPLETE_STARTUP"
    assert (run / "container-command.json").exists()
    assert (run / "server-launch.json").exists()
    assert (run / "server.log").read_bytes() == b"server log"
    cleanup = json.loads((run / "cleanup-receipts.json").read_text())
    assert [item["phase"] for item in cleanup] == ["logs", "stop", "remove"]
    assert all("only-this-container" in command for command in commands[1:])
    assert not (run / "driver-command.json").exists()
    assert not flag.exists()


def test_cleanup_failure_overrides_success_and_retains_flag(tmp_path):
    run = tmp_path / "run"
    run.mkdir()
    flag = tmp_path / "RUNNING.flag"
    flag.write_text("reserved\n", encoding="utf-8")
    plan = launcher.make_plan(run, container_name="owned-cleanup")

    def start(command, **_kwargs):
        if command[:2] == ["docker", "run"]:
            return _FakeProcess(30, stdout=b"container-id\n")
        if command[0].endswith("python"):
            return _FakeProcess(31, returncode=0)
        if command[:2] in (["docker", "rm"],):
            return _FakeProcess(32, returncode=1, stderr=b"remove failed")
        return _FakeProcess(33, returncode=0)

    code, lifecycle = launcher.run_lifecycle(
        plan,
        run_flag=flag,
        start=start,
        wait_server=lambda *_args, **_kwargs: None,
        clock=lambda: 10.0,
        wall_clock=lambda: 20.0,
    )
    assert code == 2
    assert lifecycle["status"] == "CLEANUP_FAILED"
    assert lifecycle["prior_status"] == "DRIVER_EXITED"
    assert flag.exists()
    cleanup = json.loads((run / "cleanup-receipts.json").read_text())
    assert cleanup[-1]["phase"] == "force_remove"
    assert cleanup[-1]["exit_code"] == 1


def test_failed_launch_never_removes_an_unowned_container(tmp_path):
    run = tmp_path / "run"
    run.mkdir()
    flag = tmp_path / "RUNNING.flag"
    flag.write_text("reserved\n", encoding="utf-8")
    plan = launcher.make_plan(run, container_name="candidate-name")
    commands = []

    def start(command, **_kwargs):
        commands.append(list(command))
        if command[:2] == ["docker", "run"]:
            return _FakeProcess(40, returncode=1, stderr=b"launch failed")
        if command[:3] == ["docker", "container", "inspect"]:
            return _FakeProcess(41, returncode=1, stderr=b"no such container")
        raise AssertionError("must not clean a container whose ownership is absent")

    code, lifecycle = launcher.run_lifecycle(
        plan,
        run_flag=flag,
        start=start,
        wait_server=lambda *_args, **_kwargs: None,
        clock=lambda: 10.0,
        wall_clock=lambda: 20.0,
    )
    assert code == 2
    assert lifecycle["cleaned"] is True
    assert [command[:3] for command in commands] == [
        ["docker", "run", "--pull=never"],
        ["docker", "container", "inspect"],
    ]
    cleanup = json.loads((run / "cleanup-receipts.json").read_text())
    assert [item["phase"] for item in cleanup] == ["ownership_check"]
    assert not flag.exists()


def test_dry_run_is_a_noop(tmp_path, capsys, monkeypatch):
    run = launcher.RESULTS_DIR / "run-test-dry-noop"
    run_flag = tmp_path / "RUNNING.flag"
    monkeypatch.setattr(launcher, "RUN_FLAG", run_flag)
    fake_uuid = type("U", (), {"hex": "a" * 32})()
    monkeypatch.setattr(launcher.uuid, "uuid4", lambda: fake_uuid)
    assert launcher.main(["--run-dir", str(run)]) == 0
    plan = json.loads(capsys.readouterr().out)
    assert plan["execute"] is False
    assert plan["container_name"].endswith("aaaaaaaaaaaa")
    assert "--enable-auto-tool-choice" in plan["container_command"]
    parser_index = plan["container_command"].index("--tool-call-parser")
    assert plan["container_command"][parser_index + 1] == "hermes"
    assert not run.exists()
    assert not run_flag.exists()
