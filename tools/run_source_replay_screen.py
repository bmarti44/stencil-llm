#!/usr/bin/env python3
"""Own the fixed source-replay screen lifecycle; print a dry plan by default."""

import argparse
import fcntl
import hashlib
import json
import math
import os
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import source_replay_screen as driver  # noqa: E402
from tools import run_coding_competence as owned  # noqa: E402
from tools import run_source_replay_qualification as qualification  # noqa: E402

RESULTS_DIR = ROOT / "results/source-replay"
DEFAULT_INPUT = RESULTS_DIR / "screen-input.json"
DEFAULT_FREEZE = RESULTS_DIR / "screen-freeze.json"
RUN_FLAG = RESULTS_DIR / "SCREEN-RUNNING.flag"
DRIVER = ROOT / "scripts/source_replay_screen.py"
IMAGE = owned.IMAGE
BASE_URL = owned.BASE_URL
RESERVATION_SECONDS = 3000
STARTUP_SECONDS = 600
CLEANUP_SECONDS = 60
EFFECTIVE_STARTUP_SECONDS = min(STARTUP_SECONDS, RESERVATION_SECONDS - CLEANUP_SECONDS)
REQUIRED_ACCEPTANCES = ("specification", "fixture", "implementation")
CANONICAL_REVIEW = "results/source-replay/review-astra.md"
SPECIFICATION_SUBJECT_FILES = {
    "results/source-replay/SPEC.md",
    "results/source-replay/DATA-CONTRACT.md",
    "results/source-replay/SCREEN-IMPLEMENTATION-BRIEF.md",
}
IMPLEMENTATION_SUBJECT_FILES = {
    "src/stencil/source_replay_screen.py",
    "scripts/source_replay_screen.py",
    "tools/run_source_replay_screen.py",
    "tests/test_source_replay_screen.py",
    "tests/test_source_replay_screen_driver.py",
    "tests/test_run_source_replay_screen.py",
}
CORE_BOUND_FILES = {
    *SPECIFICATION_SUBJECT_FILES,
    *IMPLEMENTATION_SUBJECT_FILES,
    *driver.PREFLIGHT_CODE_FILES,
    "tools/run_coding_competence.py",
    "tools/run_source_replay_qualification.py",
    "results/source-replay/review-astra.md",
    "results/factorial-prep/current-trunk-hashes.json",
}
FREEZE_FIELDS = {
    "schema_version",
    "kind",
    "status",
    "reservation_seconds",
    "image",
    "model",
    "input",
    "preflight",
    "bound_files",
    "acceptances",
}


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _read_json(path, label):
    try:
        return json.loads(Path(path).read_bytes())
    except Exception as exc:
        raise RuntimeError(f"{label} is not readable JSON: {exc}") from exc


def _bound_path(root, relative, label):
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise RuntimeError(f"{label} must be repository-relative")
    root = Path(root).resolve()
    path = (root / relative).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise RuntimeError(f"{label} escapes the repository") from exc
    return path


def _valid_sha(value):
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _binding(value, label, bound):
    if type(value) is not dict or set(value) != {"path", "sha256"}:
        raise RuntimeError(f"{label} binding has the wrong fields")
    if value["path"] not in bound or value["sha256"] != bound[value["path"]]:
        raise RuntimeError(f"{label} binding is absent or inconsistent")


def _default_subjects(loaded, input_relative):
    fixture = {
        input_relative,
        *(item["path"] for item in loaded["manifest"]["projects"]),
        loaded["manifest"]["source_review"]["path"],
        *(item["path"] for item in loaded["manifest"]["qualification"].values()),
    }
    return {
        "specification": set(SPECIFICATION_SUBJECT_FILES),
        "fixture": fixture,
        "implementation": set(IMPLEMENTATION_SUBJECT_FILES),
    }


def validate_freeze(
    freeze_path,
    *,
    root=ROOT,
    required_files=None,
    required_subjects=None,
    canonical_review_path=CANONICAL_REVIEW,
):
    """Validate exact screen data/code/preflight and its latest launch approval."""
    root = Path(root).resolve()
    freeze_path = Path(freeze_path)
    freeze = _read_json(freeze_path, "screen freeze")
    if type(freeze) is not dict or set(freeze) != FREEZE_FIELDS:
        raise RuntimeError("screen freeze has the wrong fields")
    if (
        type(freeze["schema_version"]) is not int
        or freeze["schema_version"] != 1
        or freeze["kind"] != "source-replay-screen-freeze"
        or freeze["status"] != "ACCEPTED"
        or type(freeze["reservation_seconds"]) is not int
        or freeze["reservation_seconds"] != RESERVATION_SECONDS
        or freeze["image"] != IMAGE
        or freeze["model"] != "/model"
    ):
        raise RuntimeError("screen freeze settings are not accepted")
    bound = freeze["bound_files"]
    if type(bound) is not dict or not bound:
        raise RuntimeError("screen freeze bound_files must be a nonempty object")
    for relative, expected in bound.items():
        path = _bound_path(root, relative, "bound file")
        if not _valid_sha(expected) or not path.is_file():
            raise RuntimeError(
                f"bound file is missing or has an invalid hash: {relative}"
            )
        if _sha256(path) != expected:
            raise RuntimeError(f"bound file hash mismatch: {relative}")

    _binding(freeze["input"], "input", bound)
    _binding(freeze["preflight"], "preflight", bound)
    input_path = _bound_path(root, freeze["input"]["path"], "input")
    preflight_path = _bound_path(root, freeze["preflight"]["path"], "preflight")
    if preflight_path != input_path.with_name(driver.PREFLIGHT_FILENAME):
        raise RuntimeError(
            "screen preflight must be the input manifest's fixed sibling"
        )
    try:
        loaded = driver.load_inputs(input_path, root=root)
        preflight = driver._validate_preflight(preflight_path, loaded)
    except ValueError as exc:
        raise RuntimeError(f"screen preflight/input validation failed: {exc}") from exc
    if loaded["input_receipt"]["sha256"] != freeze["input"]["sha256"]:
        raise RuntimeError("screen input receipt differs from its freeze binding")
    for binding in [
        *loaded["manifest"]["projects"],
        loaded["manifest"]["source_review"],
        *loaded["manifest"]["qualification"].values(),
    ]:
        _binding(binding, "manifest subject", bound)
    for relative, digest in preflight["consumer_code_sha256"].items():
        if relative not in bound or bound[relative] != digest:
            raise RuntimeError("screen preflight code identity is unbound")
    tokenizer_path = Path(preflight["tokenizer"]["path"]).resolve()
    try:
        tokenizer_relative = str(tokenizer_path.relative_to(root))
    except ValueError as exc:
        raise RuntimeError(
            "screen preflight tokenizer is outside the repository"
        ) from exc
    if (
        tokenizer_relative not in bound
        or bound[tokenizer_relative] != preflight["tokenizer"]["sha256"]
    ):
        raise RuntimeError("screen preflight tokenizer identity is unbound")

    if required_subjects is None:
        required_subjects = _default_subjects(loaded, freeze["input"]["path"])
    if required_files is None:
        required_files = {
            *CORE_BOUND_FILES,
            freeze["input"]["path"],
            freeze["preflight"]["path"],
            tokenizer_relative,
            *(item["path"] for item in loaded["manifest"]["projects"]),
            loaded["manifest"]["source_review"]["path"],
            *(item["path"] for item in loaded["manifest"]["qualification"].values()),
        }
    if set(bound) != set(required_files):
        raise RuntimeError("screen freeze does not bind the exact required file set")

    acceptances = freeze["acceptances"]
    if type(acceptances) is not list:
        raise RuntimeError("screen freeze acceptances must be a list")
    observed = set()
    review_text = None
    for acceptance in acceptances:
        if type(acceptance) is not dict or set(acceptance) != {
            "kind",
            "path",
            "sha256",
            "status",
        }:
            raise RuntimeError("screen acceptance has the wrong fields")
        kind = acceptance["kind"]
        if (
            kind in observed
            or kind not in REQUIRED_ACCEPTANCES
            or acceptance["path"] != str(canonical_review_path)
            or acceptance["status"] != "ACCEPTED"
            or acceptance["path"] not in bound
            or acceptance["sha256"] != bound[acceptance["path"]]
        ):
            raise RuntimeError("screen acceptance is not exact and accepted")
        observed.add(kind)
        if review_text is None:
            review_text = _bound_path(
                root, acceptance["path"], "canonical review"
            ).read_text(encoding="utf-8")
    if observed != set(REQUIRED_ACCEPTANCES):
        raise RuntimeError("screen freeze lacks all three acceptance roles")
    review = qualification._validate_review(review_text, bound, required_subjects)
    return {
        "freeze": freeze,
        "freeze_sha256": _sha256(freeze_path),
        "input_path": input_path,
        "preflight_path": preflight_path,
        "review": review,
        "projection": preflight["projection"],
    }


def make_plan(run_dir, input_path=DEFAULT_INPUT, *, container_name=None):
    """Build the unchanged owner's exact standard driver plan."""
    if container_name is None:
        container_name = "stencil-source-replay-screen-" + uuid.uuid4().hex[:12]
    run = Path(run_dir)
    return {
        "schema_version": 1,
        "kind": "source-replay-screen-launch-plan",
        "execute": False,
        "run_dir": str(run),
        "container_name": container_name,
        "container_command": owned._container_command(container_name),
        "driver": str(DRIVER),
        "input": str(Path(input_path)),
        "output_dir": str(run / "screen"),
        "base_url": BASE_URL,
        "model": "/model",
        "reservation_seconds": RESERVATION_SECONDS,
        "startup_ceiling_seconds": EFFECTIVE_STARTUP_SECONDS,
        "cleanup_reserve_seconds": CLEANUP_SECONDS,
    }


def execute_lifecycle(plan, run_flag, *, lifecycle_runner=owned.run_lifecycle):
    return lifecycle_runner(plan, run_flag=run_flag)


def validate_terminal(lifecycle, manifest):
    if type(lifecycle) is not dict or lifecycle.get("status") != "DRIVER_EXITED":
        raise RuntimeError("screen lifecycle did not reach driver exit")
    if (
        lifecycle.get("cleaned") is not True
        or lifecycle.get("cleanup_evidence_complete") is not True
    ):
        raise RuntimeError("screen cleanup evidence is incomplete")
    elapsed = lifecycle.get("elapsed_seconds")
    if (
        isinstance(elapsed, bool)
        or type(elapsed) not in {int, float}
        or not math.isfinite(elapsed)
        or elapsed < 0
        or elapsed > RESERVATION_SECONDS
    ):
        raise RuntimeError("screen lifecycle exceeded its whole deadline")
    if lifecycle.get("driver_exit_code") not in {0, 1}:
        raise RuntimeError("screen driver did not produce a completed disposition")
    if (
        type(manifest) is not dict
        or manifest.get("status") != "COMPLETE"
        or manifest.get("gate_disposition") not in {"PASS", "FAIL"}
    ):
        raise RuntimeError("screen manifest is incomplete")
    return True


def publish_terminal(path, lifecycle, manifest, *, clock=time.monotonic, writer=None):
    """Include final terminal publication in the 3000-second lifecycle."""
    if writer is None:
        writer = owned._write_json
    terminal = {
        "schema_version": 1,
        "status": "PENDING",
        "technically_eligible": False,
        "screen_disposition": "INCOMPLETE",
        "lifecycle": lifecycle,
        "manifest": manifest,
    }
    writer(path, terminal)
    try:
        validate_terminal(lifecycle, manifest)
        started = lifecycle.get("started_monotonic")
        if isinstance(started, bool) or type(started) not in {int, float}:
            raise RuntimeError("lifecycle lacks its whole-deadline origin")
        terminal.update(
            status="COMPLETE",
            technically_eligible=True,
            screen_disposition="ADVANCE"
            if manifest["gate_disposition"] == "PASS"
            else "PARK",
            published_monotonic=clock(),
        )
        if terminal["published_monotonic"] - started > RESERVATION_SECONDS:
            raise RuntimeError("final publication exceeded the whole deadline")
        writer(path, terminal)
        if clock() - started > RESERVATION_SECONDS:
            raise RuntimeError("final publication exceeded the whole deadline")
        return terminal
    except RuntimeError as exc:
        terminal.update(
            status="INCOMPLETE",
            technically_eligible=False,
            screen_disposition="INCOMPLETE",
            published_monotonic=clock(),
            error=f"RuntimeError: {exc}",
        )
        writer(path, terminal)
        return terminal


def _reserve_flag(path, run_dir, container_name):
    payload = (
        json.dumps(
            {"pid": os.getpid(), "run_dir": str(run_dir), "container": container_name},
            sort_keys=True,
        )
        + "\n"
    )
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())


def _parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--freeze", type=Path, default=DEFAULT_FREEZE)
    parser.add_argument("--execute", action="store_true")
    return parser


def main(argv=None):
    args = _parser().parse_args(argv)
    run = args.run_dir.resolve()
    freeze_path = args.freeze.resolve()
    plan = make_plan(run, DEFAULT_INPUT)
    if not args.execute:
        plan["freeze"] = str(freeze_path)
        plan["freeze_status"] = "present" if freeze_path.is_file() else "missing"
        print(json.dumps(plan, ensure_ascii=True, indent=2, sort_keys=True))
        return 0
    if run.parent != RESULTS_DIR or not run.name.startswith("screen-run-"):
        raise ValueError(
            "run-dir must be a screen-run-* child of results/source-replay"
        )
    binding = validate_freeze(freeze_path)
    plan = make_plan(run, binding["input_path"])
    environment = qualification.qualify_environment(
        binding, container_name=plan["container_name"]
    )
    owned.register_pid(os.getpid())
    review_handle = owned.acquire_review_lock(ROOT / ".review.lock")
    lifecycle_started = False
    try:
        _reserve_flag(RUN_FLAG, run, plan["container_name"])
        try:
            run.mkdir(parents=False, exist_ok=False)
            plan["execute"] = True
            owned._write_json(run / "launch-plan.json", plan)
            owned._write_json(
                run / "launch-preflight.json",
                {
                    "schema_version": 1,
                    "binding": {
                        "freeze": binding["freeze"],
                        "freeze_sha256": binding["freeze_sha256"],
                        "input_path": str(binding["input_path"]),
                        "preflight_path": str(binding["preflight_path"]),
                    },
                    "environment": environment,
                },
            )
            current = validate_freeze(freeze_path)
            if current["freeze_sha256"] != binding["freeze_sha256"]:
                raise RuntimeError("screen freeze changed before launch")
            owned.validate_trunk_hashes(
                ROOT / "results/factorial-prep/current-trunk-hashes.json", root=ROOT
            )
            lifecycle_started = True
            code, lifecycle = execute_lifecycle(plan, RUN_FLAG)
            manifest = _read_json(
                Path(plan["output_dir"]) / "manifest.json", "screen manifest"
            )
            terminal = publish_terminal(
                run / "screen-terminal.json", lifecycle, manifest
            )
            return code if terminal["technically_eligible"] else 2
        except Exception:
            if not lifecycle_started:
                RUN_FLAG.unlink(missing_ok=True)
            raise
    finally:
        fcntl.flock(review_handle, fcntl.LOCK_UN)
        review_handle.close()


if __name__ == "__main__":
    sys.exit(main())
