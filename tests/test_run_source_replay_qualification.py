import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from tools import run_source_replay_qualification as launcher


def test_plan_reuses_owned_container_and_standard_driver_cli(tmp_path):
    plan = launcher.make_plan(tmp_path / "run", tmp_path / "fixture.json")

    assert plan["reservation_seconds"] == 600
    assert plan["cleanup_reserve_seconds"] == 60
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
        "spec.md": b"Disposition: ACCEPT\nZero open high/critical findings.\n",
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
                "kind": "specification",
                "path": "spec.md",
                "sha256": hashlib.sha256(paths["spec.md"]).hexdigest(),
                "status": "ACCEPTED",
            }
        ],
    }
    freeze_path = root / "freeze.json"
    freeze_path.write_text(json.dumps(freeze), encoding="utf-8")

    validated = launcher.validate_freeze(
        freeze_path,
        root=root,
        required_files={"fixture.json", "code.py", "spec.md"},
        required_acceptances={"specification"},
    )

    assert validated["fixture_path"] == root / "fixture.json"
    (root / "code.py").write_text("changed\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="hash mismatch"):
        launcher.validate_freeze(
            freeze_path,
            root=root,
            required_files={"fixture.json", "code.py", "spec.md"},
            required_acceptances={"specification"},
        )


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
