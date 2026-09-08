import hashlib
import json
from pathlib import Path

import pytest
from test_source_replay_screen_driver import preflight

from scripts import source_replay_screen as driver
from tools import run_source_replay_screen as launcher


def review_block(subjects, *, round_index=6, score=96, disposition="ACCEPT", high=0):
    payload = {
        "schema_version": 1,
        "canonical_topic": "source-replay",
        "round": round_index,
        "score": score,
        "disposition": disposition,
        "open_findings": {"high": high, "critical": 0},
        "subjects": subjects,
    }
    state = "none" if high == 0 else f"{high} high"
    return (
        f"## Round {round_index}\n\nScore: {score}/100\n\n"
        f"Disposition: {disposition} screen implementation.\n"
        f"Open findings: {state}.\n\n"
        "<!-- SOURCE_REPLAY_REVIEW_MACHINE_V1\n"
        + json.dumps(payload, sort_keys=True)
        + "\n-->\n"
    )


def freeze_fixture(tmp_path, *, latest=None):
    input_path, _ = preflight(tmp_path)
    input_value = json.loads(input_path.read_text(encoding="utf-8"))
    for relative in {
        *driver.PREFLIGHT_CODE_FILES,
        *launcher.IMPLEMENTATION_SUBJECT_FILES,
    }:
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((launcher.ROOT / relative).read_bytes())
    implementation = {
        relative: hashlib.sha256((tmp_path / relative).read_bytes()).hexdigest()
        for relative in launcher.IMPLEMENTATION_SUBJECT_FILES
    }
    for relative in launcher.SPECIFICATION_SUBJECT_FILES:
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((launcher.ROOT / relative).read_bytes())
    specification = {
        relative: hashlib.sha256((tmp_path / relative).read_bytes()).hexdigest()
        for relative in launcher.SPECIFICATION_SUBJECT_FILES
    }
    fixture_paths = {
        "screen-input.json",
        *(item["path"] for item in input_value["projects"]),
        input_value["source_review"]["path"],
        *(item["path"] for item in input_value["qualification"].values()),
    }
    fixture = {
        relative: hashlib.sha256((tmp_path / relative).read_bytes()).hexdigest()
        for relative in fixture_paths
    }
    subjects = {
        "specification": specification,
        "fixture": fixture,
        "implementation": implementation,
    }
    review = review_block(subjects)
    if latest is not None:
        review += latest
    review_path = tmp_path / "review.md"
    review_path.write_text(review, encoding="utf-8")
    tokenizer = json.loads((tmp_path / driver.PREFLIGHT_FILENAME).read_text())[
        "tokenizer"
    ]["path"]
    tokenizer_relative = str(Path(tokenizer).resolve().relative_to(tmp_path.resolve()))
    all_paths = {
        *driver.PREFLIGHT_CODE_FILES,
        *launcher.IMPLEMENTATION_SUBJECT_FILES,
        *launcher.SPECIFICATION_SUBJECT_FILES,
        *fixture_paths,
        driver.PREFLIGHT_FILENAME,
        tokenizer_relative,
        "review.md",
    }
    bound = {
        relative: hashlib.sha256((tmp_path / relative).read_bytes()).hexdigest()
        for relative in all_paths
    }
    freeze = {
        "schema_version": 1,
        "kind": "source-replay-screen-freeze",
        "status": "ACCEPTED",
        "reservation_seconds": 3000,
        "image": launcher.IMAGE,
        "model": "/model",
        "input": {"path": "screen-input.json", "sha256": bound["screen-input.json"]},
        "preflight": {
            "path": driver.PREFLIGHT_FILENAME,
            "sha256": bound[driver.PREFLIGHT_FILENAME],
        },
        "bound_files": bound,
        "acceptances": [
            {
                "kind": kind,
                "path": "review.md",
                "sha256": bound["review.md"],
                "status": "ACCEPTED",
            }
            for kind in sorted(launcher.REQUIRED_ACCEPTANCES)
        ],
    }
    freeze_path = tmp_path / "freeze.json"
    freeze_path.write_text(json.dumps(freeze), encoding="utf-8")
    return freeze_path, all_paths, {key: set(value) for key, value in subjects.items()}


def test_plan_uses_exact_owned_lifecycle_and_fixed_budget(tmp_path):
    plan = launcher.make_plan(
        tmp_path / "run", tmp_path / "screen-input.json", container_name="owned"
    )
    assert plan["reservation_seconds"] == 3000
    assert plan["startup_ceiling_seconds"] == 600
    assert plan["cleanup_reserve_seconds"] == 60
    assert plan["driver"].endswith("scripts/source_replay_screen.py")
    assert plan["input"] == str(tmp_path / "screen-input.json")
    assert plan["container_command"] == launcher.owned._container_command("owned")
    assert "src/stencil/focus/renderer.py" in launcher.CORE_BOUND_FILES


def test_freeze_binds_manifest_preflight_and_latest_exact_subjects(tmp_path):
    freeze_path, required, subjects = freeze_fixture(tmp_path)
    result = launcher.validate_freeze(
        freeze_path,
        root=tmp_path,
        required_files=required,
        required_subjects=subjects,
        canonical_review_path="review.md",
    )
    assert result["input_path"] == tmp_path / "screen-input.json"
    assert driver.PREFLIGHT_FILENAME not in subjects["fixture"]

    project_path = tmp_path / "projects/p1.json"
    project_path.write_text("{}", encoding="utf-8")
    with pytest.raises(RuntimeError, match="hash mismatch"):
        launcher.validate_freeze(
            freeze_path,
            root=tmp_path,
            required_files=required,
            required_subjects=subjects,
            canonical_review_path="review.md",
        )


def test_freeze_rejects_stale_latest_review_without_machine_block(tmp_path):
    latest = (
        "## Round 7\n\nScore: 82/100\n\nDisposition: REJECT screen.\n"
        "Open findings: 1 high.\n"
    )
    freeze_path, required, subjects = freeze_fixture(tmp_path, latest=latest)
    with pytest.raises(RuntimeError, match="latest"):
        launcher.validate_freeze(
            freeze_path,
            root=tmp_path,
            required_files=required,
            required_subjects=subjects,
            canonical_review_path="review.md",
        )


def test_reused_lifecycle_cleans_after_full_permitted_startup(tmp_path):
    class Clock:
        now = 0.0

        def __call__(self):
            return self.now

    class Process:
        next_pid = 200

        def __init__(self, command, clock):
            self.command, self.clock = command, clock
            self.pid = Process.next_pid
            Process.next_pid += 1
            self.returncode = None

        def communicate(self, timeout):
            if self.command[:3] == ["docker", "run", "--pull=never"]:
                self.clock.now += timeout
                stdout = b"owned-container-id\n"
            else:
                stdout = b""
            self.returncode = 0
            return stdout, b""

        def terminate(self):
            self.returncode = -15

        def kill(self):
            self.returncode = -9

    clock = Clock()
    commands = []

    def start(command, **_kwargs):
        commands.append(command)
        return Process(command, clock)

    def failed_health(*_args, **_kwargs):
        raise TimeoutError("startup allowance consumed")

    run = tmp_path / "run"
    run.mkdir()
    flag = tmp_path / "RUNNING.flag"
    flag.write_text("owned\n", encoding="utf-8")
    plan = launcher.make_plan(
        run, tmp_path / "screen-input.json", container_name="owned"
    )
    code, lifecycle = launcher.owned.run_lifecycle(
        plan,
        run_flag=flag,
        start=start,
        wait_server=failed_health,
        clock=clock,
        wall_clock=clock,
    )
    assert code == 2 and lifecycle["status"] == "INCOMPLETE_STARTUP"
    assert lifecycle["cleaned"] is True and not flag.exists()
    assert [command[:2] for command in commands[1:]] == [
        ["docker", "logs"],
        ["docker", "stop"],
        ["docker", "rm"],
    ]


def test_late_terminal_publication_is_incomplete(tmp_path):
    class Clock:
        now = 2999.0

        def __call__(self):
            return self.now

    clock = Clock()
    writes = []

    def writer(_path, value):
        writes.append(json.loads(json.dumps(value)))
        if value["status"] == "COMPLETE":
            clock.now = 3000.01

    lifecycle = {
        "status": "DRIVER_EXITED",
        "cleaned": True,
        "cleanup_evidence_complete": True,
        "elapsed_seconds": 2999.0,
        "started_monotonic": 0.0,
        "driver_exit_code": 0,
    }
    manifest = {"status": "COMPLETE", "gate_disposition": "PASS"}
    terminal = launcher.publish_terminal(
        tmp_path / "terminal.json", lifecycle, manifest, clock=clock, writer=writer
    )
    assert terminal["status"] == "INCOMPLETE"
    assert terminal["technically_eligible"] is False
    assert "publication" in terminal["error"]
    assert writes[-1]["status"] == "INCOMPLETE"


def test_launcher_help_and_dry_plan(capsys, tmp_path):
    with pytest.raises(SystemExit) as exc:
        launcher.main(["--help"])
    assert exc.value.code == 0
    capsys.readouterr()
    assert launcher.main(["--run-dir", str(tmp_path / "dry")]) == 0
    assert json.loads(capsys.readouterr().out)["execute"] is False
