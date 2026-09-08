import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from tools import run_source_replay_qualification as launcher


def _review_block(subjects, *, round_index=4, score=96, disposition="ACCEPT", high=0):
    state = "none" if high == 0 else f"{high} high"
    payload = {
        "schema_version": 1,
        "canonical_topic": "source-replay",
        "round": round_index,
        "score": score,
        "disposition": disposition,
        "open_findings": {"high": high, "critical": 0},
        "subjects": subjects,
    }
    return (
        f"## Round {round_index}\n\n"
        f"Score: {score}/100\n\n"
        f"Disposition: {disposition} current implementation.\n"
        f"Open findings: {state}.\n\n"
        "<!-- SOURCE_REPLAY_REVIEW_MACHINE_V1\n"
        + json.dumps(payload, sort_keys=True)
        + "\n-->\n"
    )


def test_plan_reuses_owned_container_and_standard_driver_cli(tmp_path):
    plan = launcher.make_plan(tmp_path / "run", tmp_path / "fixture.json")

    assert plan["reservation_seconds"] == 600
    assert plan["startup_ceiling_seconds"] == 540
    assert plan["cleanup_reserve_seconds"] == 60
    assert "src/stencil/focus/renderer.py" in launcher.CORE_BOUND_FILES
    assert plan["driver"].endswith("scripts/source_replay_qualification.py")
    assert plan["input"] == str(tmp_path / "fixture.json")
    assert plan["base_url"] == "http://127.0.0.1:18088"
    command = plan["container_command"]
    assert command[0:3] == ["docker", "run", "--pull=never"]
    assert launcher.IMAGE in command
    assert any(
        value.startswith("stencil.owner=coding-competence:") for value in command
    )


def test_validate_freeze_binds_fixture_dependencies_and_acceptance_receipts(tmp_path):
    root = tmp_path
    paths = {
        "fixture.json": b"{}\n",
        "code.py": b"pass\n",
        "spec.md": b"spec\n",
        "tokenizer.json": b"{}\n",
    }
    for relative, body in paths.items():
        (root / relative).write_bytes(body)
    preflight = {
        "schema_version": 1,
        "kind": "source-replay-qualification-cpu-preflight",
        "status": "PASS",
        "model_calls": 0,
        "input": {"sha256": hashlib.sha256(paths["fixture.json"]).hexdigest()},
        "consumer_code_sha256": {
            "code.py": hashlib.sha256(paths["code.py"]).hexdigest()
        },
        "tokenizer": {
            "name": "test-tokenizer",
            "path": str(root / "tokenizer.json"),
            "sha256": hashlib.sha256(paths["tokenizer.json"]).hexdigest(),
        },
        "reference_action": {"eligible": True, "generation_headroom": 900},
        "all_reference_checks_passed": True,
    }
    preflight_body = json.dumps(preflight).encode("utf-8")
    (root / "qualification-preflight.json").write_bytes(preflight_body)
    paths["qualification-preflight.json"] = preflight_body
    subjects = {
        "specification": {"spec.md": hashlib.sha256(paths["spec.md"]).hexdigest()},
        "fixture": {"fixture.json": hashlib.sha256(paths["fixture.json"]).hexdigest()},
        "implementation": {"code.py": hashlib.sha256(paths["code.py"]).hexdigest()},
    }
    review_body = _review_block(subjects).encode("utf-8")
    (root / "review.md").write_bytes(review_body)
    paths["review.md"] = review_body
    freeze = {
        "schema_version": 1,
        "kind": "source-replay-qualification-freeze",
        "status": "ACCEPTED",
        "reservation_seconds": 600,
        "image": launcher.IMAGE,
        "model": "/model",
        "fixture": {
            "path": "fixture.json",
            "sha256": hashlib.sha256(paths["fixture.json"]).hexdigest(),
        },
        "preflight": {
            "path": "qualification-preflight.json",
            "sha256": hashlib.sha256(preflight_body).hexdigest(),
        },
        "bound_files": {
            name: hashlib.sha256(body).hexdigest() for name, body in paths.items()
        },
        "acceptances": [
            {
                "kind": kind,
                "path": "review.md",
                "sha256": hashlib.sha256(review_body).hexdigest(),
                "status": "ACCEPTED",
            }
            for kind in sorted(launcher.REQUIRED_ACCEPTANCES)
        ],
    }
    freeze_path = root / "freeze.json"
    freeze_path.write_text(json.dumps(freeze), encoding="utf-8")

    validated = launcher.validate_freeze(
        freeze_path,
        root=root,
        required_files=set(paths),
        required_subjects={key: set(value) for key, value in subjects.items()},
        canonical_review_path="review.md",
    )

    assert validated["fixture_path"] == root / "fixture.json"
    (root / "code.py").write_text("changed\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="hash mismatch"):
        launcher.validate_freeze(
            freeze_path,
            root=root,
            required_files=set(paths),
            required_subjects={key: set(value) for key, value in subjects.items()},
            canonical_review_path="review.md",
        )


@pytest.mark.parametrize(
    "latest,error",
    [
        (
            "## Round 5\n\nScore: 82/100\n\nDisposition: REJECT current "
            "implementation.\nOpen findings: 2 high.\n",
            "latest",
        ),
        ("machine-reject", "disposition"),
        ("machine-low", "score"),
        ("machine-open", "open"),
        ("wrong-subject", "subject"),
    ],
)
def test_validate_freeze_rejects_stale_or_mismatched_acceptance(
    tmp_path, latest, error
):
    root = tmp_path
    bodies = {
        "fixture.json": b"{}\n",
        "spec.md": b"spec\n",
        "code.py": b"pass\n",
        "tokenizer.json": b"{}\n",
    }
    for relative, body in bodies.items():
        (root / relative).write_bytes(body)
    subjects = {
        "specification": {"spec.md": hashlib.sha256(bodies["spec.md"]).hexdigest()},
        "fixture": {"fixture.json": hashlib.sha256(bodies["fixture.json"]).hexdigest()},
        "implementation": {"code.py": hashlib.sha256(bodies["code.py"]).hexdigest()},
    }
    accepted = _review_block(subjects)
    if latest == "machine-reject":
        review = accepted + _review_block(
            subjects, round_index=5, score=82, disposition="REJECT", high=2
        )
    elif latest == "machine-low":
        review = accepted + _review_block(subjects, round_index=5, score=89)
    elif latest == "machine-open":
        review = accepted + _review_block(subjects, round_index=5, high=1)
    elif latest == "wrong-subject":
        wrong = json.loads(json.dumps(subjects))
        wrong["implementation"]["code.py"] = "f" * 64
        review = accepted + _review_block(wrong, round_index=5)
    else:
        review = accepted + latest
    bodies["review.md"] = review.encode("utf-8")
    (root / "review.md").write_bytes(bodies["review.md"])
    preflight = {
        "schema_version": 1,
        "kind": "source-replay-qualification-cpu-preflight",
        "status": "PASS",
        "model_calls": 0,
        "input": {"sha256": hashlib.sha256(bodies["fixture.json"]).hexdigest()},
        "consumer_code_sha256": {
            "code.py": hashlib.sha256(bodies["code.py"]).hexdigest()
        },
        "tokenizer": {
            "name": "test-tokenizer",
            "path": str(root / "tokenizer.json"),
            "sha256": hashlib.sha256(bodies["tokenizer.json"]).hexdigest(),
        },
        "reference_action": {"eligible": True, "generation_headroom": 900},
        "all_reference_checks_passed": True,
    }
    bodies["qualification-preflight.json"] = json.dumps(preflight).encode("utf-8")
    (root / "qualification-preflight.json").write_bytes(
        bodies["qualification-preflight.json"]
    )
    freeze = {
        "schema_version": 1,
        "kind": "source-replay-qualification-freeze",
        "status": "ACCEPTED",
        "reservation_seconds": 600,
        "image": launcher.IMAGE,
        "model": "/model",
        "fixture": {
            "path": "fixture.json",
            "sha256": hashlib.sha256(bodies["fixture.json"]).hexdigest(),
        },
        "preflight": {
            "path": "qualification-preflight.json",
            "sha256": hashlib.sha256(
                bodies["qualification-preflight.json"]
            ).hexdigest(),
        },
        "bound_files": {
            relative: hashlib.sha256(body).hexdigest()
            for relative, body in bodies.items()
        },
        "acceptances": [
            {
                "kind": kind,
                "path": "review.md",
                "sha256": hashlib.sha256(bodies["review.md"]).hexdigest(),
                "status": "ACCEPTED",
            }
            for kind in sorted(launcher.REQUIRED_ACCEPTANCES)
        ],
    }
    freeze_path = root / "freeze.json"
    freeze_path.write_text(json.dumps(freeze), encoding="utf-8")

    with pytest.raises(RuntimeError, match=error):
        launcher.validate_freeze(
            freeze_path,
            root=root,
            required_files=set(bodies),
            required_subjects={key: set(value) for key, value in subjects.items()},
            canonical_review_path="review.md",
        )


def test_reused_lifecycle_cleans_after_docker_delivery_uses_startup_allowance(tmp_path):
    class Clock:
        now = 0.0

        def __call__(self):
            return self.now

    class Process:
        next_pid = 100

        def __init__(self, command, clock):
            self.command = command
            self.clock = clock
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

    def late_health(*_args, **_kwargs):
        raise TimeoutError("startup allowance consumed")

    run = tmp_path / "run"
    run.mkdir()
    run_flag = tmp_path / "RUNNING.flag"
    run_flag.write_text("owned\n", encoding="utf-8")
    plan = launcher.make_plan(run, tmp_path / "fixture.json", container_name="owned")

    code, lifecycle = launcher.owned.run_lifecycle(
        plan,
        run_flag=run_flag,
        start=start,
        wait_server=late_health,
        clock=clock,
        wall_clock=clock,
    )

    assert code == 2
    assert lifecycle["status"] == "INCOMPLETE_STARTUP"
    assert lifecycle["cleaned"] is True
    assert [command[:2] for command in commands[1:]] == [
        ["docker", "logs"],
        ["docker", "stop"],
        ["docker", "rm"],
    ]
    assert not run_flag.exists()


def test_final_publication_crossing_whole_deadline_is_ineligible(tmp_path):
    class Clock:
        now = 599.0

        def __call__(self):
            return self.now

    clock = Clock()
    writes = []

    def writer(_path, value):
        writes.append(json.loads(json.dumps(value)))
        if value["status"] == "ELIGIBLE":
            clock.now = 600.01

    lifecycle = {
        "status": "DRIVER_EXITED",
        "cleaned": True,
        "cleanup_evidence_complete": True,
        "elapsed_seconds": 599.0,
        "started_monotonic": 0.0,
        "driver_exit_code": 0,
    }
    manifest = {"status": "COMPLETE", "technical_eligible": True}

    terminal = launcher.publish_terminal(
        tmp_path / "terminal.json", lifecycle, manifest, clock=clock, writer=writer
    )

    assert terminal["status"] == "INELIGIBLE"
    assert terminal["technical_eligible"] is False
    assert "publication" in terminal["error"]
    assert writes[-1]["status"] == "INELIGIBLE"


@pytest.mark.parametrize(
    "change,error",
    [
        ({"cleaned": False}, "cleanup"),
        ({"cleanup_evidence_complete": False}, "evidence"),
        ({"elapsed_seconds": 600.01}, "deadline"),
    ],
)
def test_terminal_validation_rejects_cleanup_evidence_or_deadline(change, error):
    lifecycle = {
        "status": "DRIVER_EXITED",
        "cleaned": True,
        "cleanup_evidence_complete": True,
        "elapsed_seconds": 599.0,
        "driver_exit_code": 0,
    }
    lifecycle.update(change)
    manifest = {"status": "COMPLETE", "technical_eligible": True}

    with pytest.raises(RuntimeError, match=error):
        launcher.validate_terminal(lifecycle, manifest)


def test_execute_delegates_to_unchanged_lifecycle_interface(tmp_path):
    calls = []

    def fake_lifecycle(plan, *, run_flag):
        calls.append((plan, run_flag))
        return 0, {"status": "DRIVER_EXITED"}

    plan = launcher.make_plan(tmp_path / "run", tmp_path / "fixture.json")
    code, lifecycle = launcher.execute_lifecycle(
        plan, tmp_path / "RUNNING.flag", lifecycle_runner=fake_lifecycle
    )

    assert code == 0
    assert lifecycle == {"status": "DRIVER_EXITED"}
    assert calls == [(plan, tmp_path / "RUNNING.flag")]


def test_direct_help_and_dry_plan_work_outside_repository(tmp_path):
    script = Path(launcher.__file__).resolve()
    help_result = subprocess.run(
        [sys.executable, str(script), "--help"],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )
    dry_result = subprocess.run(
        [sys.executable, str(script), "--run-dir", str(tmp_path / "run")],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )

    assert help_result.returncode == 0
    assert "--execute" in help_result.stdout
    assert dry_result.returncode == 0
    plan = json.loads(dry_result.stdout)
    assert plan["execute"] is False
    assert plan["reservation_seconds"] == 600
    assert plan["freeze_status"] in {"missing", "present"}
