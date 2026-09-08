import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import qwen_thinking_tool_smoke as smoke
from tools import run_coding_competence as owned
from tools import run_qwen_thinking_tool_smoke as launcher


class Process:
    next_pid = 9000

    def __init__(self, returncode=0, stdout=b"", stderr=b""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        self.pid = Process.next_pid
        Process.next_pid += 1

    def communicate(self, timeout=None):
        del timeout
        return self.stdout, self.stderr

    def terminate(self):
        self.returncode = -15

    def kill(self):
        self.returncode = -9


def test_plan_fixes_reasoning_tool_and_owned_resource_contract(tmp_path):
    run = launcher.RESULTS_DIR / "run-unit-plan"
    plan = launcher.make_plan(run, container_name="unit-container")
    command = plan["container_command"]

    assert plan["input"] == smoke.FIXTURE_ID
    assert plan["maximum_model_calls"] == 2
    assert plan["max_output_tokens"] == 2048
    assert plan["thinking_token_budget"] == 512
    assert plan["reservation_seconds"] == 1200
    assert plan["startup_ceiling_seconds"] == 600
    assert plan["cleanup_reserve_seconds"] == 60
    assert "--pull=never" in command
    assert command[command.index("--reasoning-parser") + 1] == "qwen3"
    assert command[command.index("--tool-call-parser") + 1] == "hermes"
    assert "--enable-auto-tool-choice" in command
    config = json.loads(command[command.index("--reasoning-config") + 1])
    assert config == {
        "reasoning_start_str": "<think>",
        "reasoning_end_str": "</think>",
    }
    assert "stencil.owner=coding-competence:unit-container" in command
    assert str(tmp_path) not in json.dumps(plan)


def test_preview_validation_binds_fixture_settings_and_sources(tmp_path):
    path = tmp_path / "preview.json"
    value = smoke.preview(model="/model")
    path.write_text(json.dumps(value), encoding="utf-8")

    receipt = launcher.validate_preview(path)

    assert receipt["fixture_sha256"] == smoke._fixture_receipt()["sha256"]
    value["settings"]["thinking_token_budget"] = 511
    path.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(RuntimeError, match="fixed smoke settings"):
        launcher.validate_preview(path)


def test_readiness_report_is_bound_by_bytes_without_parsing_approval_prose(tmp_path):
    path = tmp_path / "review.md"
    path.write_text(
        "Final adjudication belongs to the orchestrator.\n", encoding="utf-8"
    )

    receipt = launcher.validate_review(path)

    assert receipt == {"review_sha256": launcher._sha256(path)}


@pytest.mark.parametrize("driver_exit", [0, 2])
def test_reused_lifecycle_wires_driver_and_cleans_owned_container(
    tmp_path, driver_exit
):
    run = tmp_path / "run-smoke"
    run.mkdir()
    flag = tmp_path / "RUNNING.flag"
    flag.write_text("owned\n", encoding="utf-8")
    plan = launcher.make_plan(run, container_name="unit-owned")
    commands = []

    def start(command, **_kwargs):
        commands.append(list(command))
        if command == plan["container_command"]:
            return Process(stdout=b"container-id\n")
        if command[0] == str(launcher.ROOT / ".venv/bin/python"):
            return Process(returncode=driver_exit)
        return Process(returncode=0)

    code, lifecycle = owned.run_lifecycle(
        plan,
        run_flag=flag,
        start=start,
        wait_server=lambda *_args, **_kwargs: None,
        clock=lambda: 10.0,
        wall_clock=lambda: 20.0,
    )

    assert code == driver_exit
    assert lifecycle["cleaned"] is True
    assert not flag.exists()
    driver = next(
        command
        for command in commands
        if command[0] == str(launcher.ROOT / ".venv/bin/python")
    )
    assert driver[driver.index("--input") + 1] == smoke.FIXTURE_ID
    assert driver[driver.index("--deadline-seconds") + 1] == "1140"
    assert ["docker", "rm", "unit-owned"] in commands


def test_launcher_dry_run_and_preview_never_start_a_process(tmp_path):
    script = Path(launcher.__file__).resolve()
    run = launcher.RESULTS_DIR / "run-dry-test"
    dry = subprocess.run(
        [sys.executable, str(script), "--run-dir", str(run)],
        cwd=tmp_path,
        env={"PATH": "/usr/bin:/bin"},
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert dry.returncode == 0, dry.stderr
    plan = json.loads(dry.stdout)
    assert plan["execute"] is False
    assert not run.exists()

    preview = subprocess.run(
        [sys.executable, str(script), "--preview"],
        cwd=tmp_path,
        env={"PATH": "/usr/bin:/bin"},
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert preview.returncode == 0, preview.stderr
    assert json.loads(preview.stdout)["model_calls"] == 0


def test_execute_preserves_an_existing_run_directory(monkeypatch, tmp_path):
    results = tmp_path / "coding-reasoning-smoke"
    results.mkdir()
    run = results / "run-existing"
    run.mkdir()
    lifecycle = run / "lifecycle.json"
    sentinel = b'{"status":"EXISTING"}\n'
    lifecycle.write_bytes(sentinel)
    run_flag = results / "RUNNING.flag"
    lifecycle_calls = []

    monkeypatch.setattr(launcher, "RESULTS_DIR", results)
    monkeypatch.setattr(launcher, "RUN_FLAG", run_flag)
    monkeypatch.setattr(owned, "register_pid", lambda _pid: None)
    monkeypatch.setattr(
        launcher,
        "prepare_execution",
        lambda *_args, **_kwargs: {"environment": {"git_head": "a" * 40}},
    )
    monkeypatch.setattr(
        owned,
        "acquire_review_lock",
        lambda _path: (tmp_path / "review.lock").open("a+"),
    )
    monkeypatch.setattr(
        owned,
        "run_lifecycle",
        lambda *_args, **_kwargs: lifecycle_calls.append(True),
    )

    with pytest.raises(FileExistsError):
        launcher.main(["--run-dir", str(run), "--execute"])

    assert lifecycle.read_bytes() == sentinel
    assert lifecycle_calls == []
    assert not run_flag.exists()
