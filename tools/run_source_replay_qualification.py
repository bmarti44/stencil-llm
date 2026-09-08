#!/usr/bin/env python3
"""Own one source-replay qualification lifecycle; dry-run by default."""

import argparse
import fcntl
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import run_coding_competence as owned  # noqa: E402

RESULTS_DIR = ROOT / "results/source-replay"
DEFAULT_FREEZE = RESULTS_DIR / "qualification-freeze.json"
DEFAULT_FIXTURE = RESULTS_DIR / "qualification-fixture-reviewed.json"
DRIVER = ROOT / "scripts/source_replay_qualification.py"
IMAGE = owned.IMAGE
BASE_URL = owned.BASE_URL
RESERVATION_SECONDS = 600
STARTUP_SECONDS = 600
CLEANUP_SECONDS = 60
EFFECTIVE_STARTUP_SECONDS = min(STARTUP_SECONDS, RESERVATION_SECONDS - CLEANUP_SECONDS)
RUN_FLAG = RESULTS_DIR / "RUNNING.flag"
REQUIRED_ACCEPTANCES = {"specification", "fixture", "implementation"}
CANONICAL_REVIEW_PATH = "results/source-replay/review-astra.md"
SPECIFICATION_SUBJECT_FILES = {
    "results/source-replay/SPEC.md",
    "results/source-replay/DATA-CONTRACT.md",
    "results/source-replay/QUALIFICATION-BRIEF.md",
}
IMPLEMENTATION_SUBJECT_FILES = {
    "src/stencil/source_replay.py",
    "src/stencil/focus/native_source_selector.py",
    "scripts/source_replay_qualification.py",
    "tools/run_source_replay_qualification.py",
    "tests/test_source_replay.py",
    "tests/test_native_source_selector.py",
    "tests/test_source_replay_qualification.py",
    "tests/test_run_source_replay_qualification.py",
}
CORE_BOUND_FILES = {
    "src/stencil/source_replay.py",
    "src/stencil/focus/native_source_selector.py",
    "scripts/source_replay_qualification.py",
    "tools/run_source_replay_qualification.py",
    "tools/run_coding_competence.py",
    "scripts/coding_competence_run.py",
    "scripts/coding_competence_dev.py",
    "scripts/coding_worker_dev.py",
    "src/stencil/focus/slab.py",
    "src/stencil/focus/slab_sandbox.py",
    "src/stencil/focus/renderer.py",
    *IMPLEMENTATION_SUBJECT_FILES,
    "results/source-replay/SPEC.md",
    "results/source-replay/DATA-CONTRACT.md",
    "results/source-replay/QUALIFICATION-BRIEF.md",
    "results/factorial-prep/current-trunk-hashes.json",
    CANONICAL_REVIEW_PATH,
}
FREEZE_KEYS = {
    "schema_version",
    "kind",
    "status",
    "reservation_seconds",
    "image",
    "model",
    "fixture",
    "preflight",
    "bound_files",
    "acceptances",
}
ROUND_RE = re.compile(r"^## Round ([1-9][0-9]*)\s*$", re.MULTILINE)
SCORE_RE = re.compile(r"^Score:\s*([0-9]{1,3})/100\s*$", re.MULTILINE)
DISPOSITION_RE = re.compile(r"^Disposition:\s*(ACCEPT|REJECT)\b", re.MULTILINE)
MACHINE_RE = re.compile(
    r"<!-- SOURCE_REPLAY_REVIEW_MACHINE_V1\s*\n(.*?)\n-->", re.DOTALL
)


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _read_json(path, label):
    try:
        return json.loads(Path(path).read_bytes())
    except Exception as exc:
        raise RuntimeError(f"{label} is not readable JSON: {exc}") from exc


def _bound_path(root, relative, label):
    if not isinstance(relative, str) or not relative:
        raise RuntimeError(f"{label} path must be nonempty text")
    root = Path(root).resolve()
    path = (root / relative).resolve()
    if path == root or root not in path.parents:
        raise RuntimeError(f"{label} path escapes the repository")
    return path


def _valid_sha(value):
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _latest_review_state(text):
    rounds = list(ROUND_RE.finditer(text))
    if not rounds:
        raise RuntimeError("canonical review has no round sections")
    latest = rounds[-1]
    section = text[latest.start() :]
    blocks = MACHINE_RE.findall(section)
    if len(blocks) != 1:
        raise RuntimeError("latest canonical round lacks one machine block")
    try:
        state = json.loads(blocks[0])
    except Exception as exc:
        raise RuntimeError(
            f"latest review machine block is invalid JSON: {exc}"
        ) from exc
    required = {
        "schema_version",
        "canonical_topic",
        "round",
        "score",
        "disposition",
        "open_findings",
        "subjects",
    }
    if type(state) is not dict or set(state) != required:
        raise RuntimeError("latest review machine block has the wrong fields")
    heading_round = int(latest.group(1))
    visible_scores = SCORE_RE.findall(section)
    visible_dispositions = DISPOSITION_RE.findall(section)
    if (
        type(state["schema_version"]) is not int
        or state["schema_version"] != 1
        or state["canonical_topic"] != "source-replay"
        or type(state["round"]) is not int
        or state["round"] != heading_round
        or len(visible_scores) != 1
        or len(visible_dispositions) != 1
        or type(state["score"]) is not int
        or state["score"] != int(visible_scores[0])
        or state["disposition"] != visible_dispositions[0]
    ):
        raise RuntimeError("latest review machine block contradicts its round")
    return state


def _validate_review(text, bound, required_subjects):
    state = _latest_review_state(text)
    if state["disposition"] != "ACCEPT":
        raise RuntimeError("latest review disposition is not accepted")
    if not 90 <= state["score"] <= 100:
        raise RuntimeError("latest review score is below acceptance")
    open_findings = state["open_findings"]
    if (
        type(open_findings) is not dict
        or set(open_findings) != {"high", "critical"}
        or any(type(value) is not int or value < 0 for value in open_findings.values())
        or any(open_findings.values())
    ):
        raise RuntimeError("latest review has open high or critical findings")
    if (
        type(required_subjects) is not dict
        or set(required_subjects) != REQUIRED_ACCEPTANCES
    ):
        raise RuntimeError("required review subject groups are incomplete")
    expected = {}
    for kind, paths in required_subjects.items():
        if type(paths) not in {set, frozenset} or not paths:
            raise RuntimeError("required review subject set is invalid")
        if not set(paths) <= set(bound):
            raise RuntimeError("required review subject is absent from the freeze")
        expected[kind] = {path: bound[path] for path in sorted(paths)}
    if state["subjects"] != expected:
        raise RuntimeError("latest review subject hashes do not match frozen bytes")
    return state


def validate_freeze(
    freeze_path,
    *,
    root=ROOT,
    required_files=CORE_BOUND_FILES,
    required_acceptances=REQUIRED_ACCEPTANCES,
    required_subjects=None,
    canonical_review_path=CANONICAL_REVIEW_PATH,
):
    """Validate every declared byte binding and required acceptance receipt."""
    root = Path(root).resolve()
    freeze = _read_json(freeze_path, "qualification freeze")
    if type(freeze) is not dict or set(freeze) != FREEZE_KEYS:
        raise RuntimeError("qualification freeze has the wrong fields")
    if (
        type(freeze["schema_version"]) is not int
        or freeze["schema_version"] != 1
        or freeze["kind"] != "source-replay-qualification-freeze"
        or freeze["status"] != "ACCEPTED"
        or type(freeze["reservation_seconds"]) is not int
        or freeze["reservation_seconds"] != RESERVATION_SECONDS
        or freeze["image"] != IMAGE
        or freeze["model"] != "/model"
    ):
        raise RuntimeError("qualification freeze settings are not accepted")

    bound = freeze["bound_files"]
    if type(bound) is not dict or not set(required_files) <= set(bound):
        raise RuntimeError("qualification freeze omits required bound files")
    for relative, expected_hash in bound.items():
        path = _bound_path(root, relative, "bound file")
        if not _valid_sha(expected_hash) or not path.is_file():
            raise RuntimeError(
                f"bound file is missing or has an invalid hash: {relative}"
            )
        if _sha256(path) != expected_hash:
            raise RuntimeError(f"bound file hash mismatch: {relative}")

    fixture = freeze["fixture"]
    if type(fixture) is not dict or set(fixture) != {"path", "sha256"}:
        raise RuntimeError("fixture binding has the wrong fields")
    fixture_path = _bound_path(root, fixture["path"], "fixture")
    if fixture["path"] not in bound or fixture["sha256"] != bound[fixture["path"]]:
        raise RuntimeError("fixture is not identical to its bound-file receipt")
    if required_subjects is None:
        required_subjects = {
            "specification": SPECIFICATION_SUBJECT_FILES,
            "fixture": {fixture["path"]},
            "implementation": IMPLEMENTATION_SUBJECT_FILES,
        }

    preflight_binding = freeze["preflight"]
    if type(preflight_binding) is not dict or set(preflight_binding) != {
        "path",
        "sha256",
    }:
        raise RuntimeError("preflight binding has the wrong fields")
    preflight_path = _bound_path(root, preflight_binding["path"], "preflight")
    expected_preflight_path = fixture_path.with_name("qualification-preflight.json")
    if (
        preflight_path != expected_preflight_path
        or preflight_binding["path"] not in bound
        or preflight_binding["sha256"] != bound[preflight_binding["path"]]
    ):
        raise RuntimeError("preflight is not the fixture's bound sibling receipt")
    preflight = _read_json(preflight_path, "qualification CPU preflight")
    reference = preflight.get("reference_action") if type(preflight) is dict else None
    preflight_input = preflight.get("input") if type(preflight) is dict else None
    if (
        type(preflight) is not dict
        or preflight.get("schema_version") != 1
        or preflight.get("kind") != "source-replay-qualification-cpu-preflight"
        or preflight.get("status") != "PASS"
        or preflight.get("model_calls") != 0
        or preflight.get("all_reference_checks_passed") is not True
        or type(preflight_input) is not dict
        or preflight_input.get("sha256") != fixture["sha256"]
        or type(reference) is not dict
        or reference.get("eligible") is not True
        or type(reference.get("generation_headroom")) is not int
        or reference["generation_headroom"] < 128
    ):
        raise RuntimeError("qualification CPU preflight is not passing and eligible")
    consumer_hashes = preflight.get("consumer_code_sha256")
    if type(consumer_hashes) is not dict or not consumer_hashes:
        raise RuntimeError("qualification CPU preflight lacks consumer code identities")
    for relative, digest in consumer_hashes.items():
        if relative not in bound or digest != bound[relative]:
            raise RuntimeError("qualification CPU preflight code identity is unbound")
    tokenizer = preflight.get("tokenizer")
    if type(tokenizer) is not dict or set(tokenizer) != {"name", "path", "sha256"}:
        raise RuntimeError("qualification CPU preflight lacks tokenizer identity")
    tokenizer_path = Path(tokenizer["path"]).resolve()
    try:
        tokenizer_relative = str(tokenizer_path.relative_to(root))
    except ValueError as exc:
        raise RuntimeError("preflight tokenizer is outside the repository") from exc
    if (
        tokenizer_relative not in bound
        or tokenizer["sha256"] != bound[tokenizer_relative]
    ):
        raise RuntimeError("qualification CPU preflight tokenizer identity is unbound")

    acceptances = freeze["acceptances"]
    if type(acceptances) is not list:
        raise RuntimeError("freeze acceptances must be a list")
    observed = set()
    canonical_review_path = str(canonical_review_path)
    review_text = None
    for acceptance in acceptances:
        if type(acceptance) is not dict or set(acceptance) != {
            "kind",
            "path",
            "sha256",
            "status",
        }:
            raise RuntimeError("acceptance receipt has the wrong fields")
        kind = acceptance["kind"]
        relative = acceptance["path"]
        if (
            not isinstance(kind, str)
            or kind in observed
            or acceptance["status"] != "ACCEPTED"
            or relative != canonical_review_path
            or relative not in bound
            or acceptance["sha256"] != bound[relative]
        ):
            raise RuntimeError("acceptance receipt is not bound and accepted")
        if review_text is None:
            review_text = _bound_path(root, relative, "acceptance").read_text(
                encoding="utf-8"
            )
        observed.add(kind)
    if observed != set(required_acceptances):
        raise RuntimeError("qualification freeze lacks required acceptance evidence")
    review = _validate_review(review_text, bound, required_subjects)
    return {
        "freeze": freeze,
        "freeze_sha256": _sha256(freeze_path),
        "fixture_path": fixture_path,
        "preflight_path": preflight_path,
        "review": review,
    }


def make_plan(run_dir, fixture_path, *, container_name=None):
    """Build the unchanged lifecycle's exact plan interface."""
    if container_name is None:
        container_name = "stencil-source-replay-" + uuid.uuid4().hex[:12]
    run_dir = Path(run_dir)
    return {
        "schema_version": 1,
        "kind": "source-replay-qualification-launch-plan",
        "execute": False,
        "run_dir": str(run_dir),
        "container_name": container_name,
        "container_command": owned._container_command(container_name),
        "driver": str(DRIVER),
        "input": str(Path(fixture_path)),
        "output_dir": str(run_dir / "qualification"),
        "base_url": BASE_URL,
        "model": "/model",
        "reservation_seconds": RESERVATION_SECONDS,
        "startup_ceiling_seconds": EFFECTIVE_STARTUP_SECONDS,
        "cleanup_reserve_seconds": CLEANUP_SECONDS,
    }


def execute_lifecycle(plan, run_flag, *, lifecycle_runner=owned.run_lifecycle):
    """Delegate lifecycle ownership without changing its interface."""
    return lifecycle_runner(plan, run_flag=run_flag)


def validate_terminal(lifecycle, manifest):
    """Require timely cleanup evidence before publishing technical eligibility."""
    if type(lifecycle) is not dict or lifecycle.get("status") != "DRIVER_EXITED":
        raise RuntimeError("lifecycle did not reach a terminal driver exit")
    if lifecycle.get("cleaned") is not True:
        raise RuntimeError("qualification cleanup did not complete")
    if lifecycle.get("cleanup_evidence_complete") is not True:
        raise RuntimeError("qualification cleanup evidence is incomplete")
    elapsed = lifecycle.get("elapsed_seconds")
    if (
        isinstance(elapsed, bool)
        or type(elapsed) not in {int, float}
        or not math.isfinite(elapsed)
        or elapsed < 0
        or elapsed > RESERVATION_SECONDS
    ):
        raise RuntimeError("qualification exceeded its whole deadline")
    if lifecycle.get("driver_exit_code") != 0:
        raise RuntimeError("qualification driver did not exit successfully")
    if (
        type(manifest) is not dict
        or manifest.get("status") != "COMPLETE"
        or manifest.get("technical_eligible") is not True
    ):
        raise RuntimeError("qualification manifest is not technically eligible")
    return True


def publish_terminal(path, lifecycle, manifest, *, clock=time.monotonic, writer=None):
    """Publish eligibility only when the publication itself meets the whole cap."""
    if writer is None:
        writer = owned._write_json
    terminal = {
        "schema_version": 1,
        "status": "PENDING",
        "technical_eligible": False,
        "lifecycle": lifecycle,
        "manifest": manifest,
    }
    writer(path, terminal)
    try:
        validate_terminal(lifecycle, manifest)
        lifecycle_started = lifecycle.get("started_monotonic")
        if type(lifecycle_started) not in {int, float} or isinstance(
            lifecycle_started, bool
        ):
            raise RuntimeError("lifecycle lacks its whole-deadline origin")
        terminal.update(
            status="ELIGIBLE",
            technical_eligible=True,
            published_monotonic=clock(),
        )
        if terminal["published_monotonic"] - lifecycle_started > RESERVATION_SECONDS:
            raise RuntimeError("final publication exceeded the whole deadline")
        writer(path, terminal)
        ended = clock()
        if ended - lifecycle_started > RESERVATION_SECONDS:
            raise RuntimeError("final publication exceeded the whole deadline")
        return terminal
    except RuntimeError as exc:
        terminal.update(
            status="INELIGIBLE",
            technical_eligible=False,
            published_monotonic=clock(),
            error=f"RuntimeError: {exc}",
        )
        writer(path, terminal)
        return terminal


def _text(result):
    value = result.stdout
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value or ""


def _tracked_clean(relative, *, root, command):
    command(
        ["git", "-C", str(root), "ls-files", "--error-unmatch", "--", relative],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    status = command(
        [
            "git",
            "-C",
            str(root),
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
            "--",
            relative,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if _text(status).strip():
        raise RuntimeError(f"bound file is dirty or untracked: {relative}")


def qualify_environment(
    binding, *, root=ROOT, container_name=None, command=owned.run_owned
):
    """Check only resources and files needed by this owned launch."""
    root = Path(root).resolve()
    flags = owned._active_flags(root)
    if flags:
        raise RuntimeError(f"active run flag exists: {flags[0]}")
    if owned._active_review_lock(root / ".review.lock"):
        raise RuntimeError("review wrapper lock is active")
    containers = command(
        ["docker", "ps", "-q"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    if _text(containers).strip():
        raise RuntimeError("a running container already exists")
    if container_name is not None:
        existing = command(
            ["docker", "container", "inspect", container_name],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if existing.returncode == 0:
            raise RuntimeError("the reserved container name already exists")
    gpu = command(
        ["nvidia-smi", "--query-compute-apps=pid", "--format=csv,noheader"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if _text(gpu).strip():
        raise RuntimeError("a GPU compute process already exists")
    command(
        ["docker", "image", "inspect", IMAGE],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    for relative in binding["freeze"]["bound_files"]:
        if not relative.startswith("models/"):
            _tracked_clean(relative, root=root, command=command)
    trunk = owned.validate_trunk_hashes(
        root / "results/factorial-prep/current-trunk-hashes.json", root=root
    )
    return {"status": "PASS", "checked_unix": time.time(), "trunk": trunk}


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
    plan = make_plan(run, DEFAULT_FIXTURE)
    if not args.execute:
        plan["freeze"] = str(freeze_path)
        plan["freeze_status"] = "present" if freeze_path.is_file() else "missing"
        print(json.dumps(plan, ensure_ascii=True, indent=2, sort_keys=True))
        return 0

    if run.parent != RESULTS_DIR or not run.name.startswith("qualification-run-"):
        raise ValueError(
            "run-dir must be a qualification-run-* child of results/source-replay"
        )
    binding = validate_freeze(freeze_path)
    plan = make_plan(run, binding["fixture_path"])
    environment = qualify_environment(binding, container_name=plan["container_name"])
    owned.register_pid(os.getpid())
    review_handle = owned.acquire_review_lock(ROOT / ".review.lock")
    lifecycle_started = False
    try:
        _reserve_flag(RUN_FLAG, run, plan["container_name"])
        try:
            run.mkdir(parents=False, exist_ok=False)
            plan["execute"] = True
            owned._write_json(run / "launch-plan.json", plan)
            serializable_binding = {
                "freeze": binding["freeze"],
                "freeze_sha256": binding["freeze_sha256"],
                "fixture_path": str(binding["fixture_path"]),
                "preflight_path": str(binding["preflight_path"]),
            }
            owned._write_json(
                run / "launch-preflight.json",
                {
                    "schema_version": 1,
                    "binding": serializable_binding,
                    "environment": environment,
                },
            )
            current_binding = validate_freeze(freeze_path)
            if current_binding["freeze_sha256"] != binding["freeze_sha256"]:
                raise RuntimeError("qualification freeze changed before launch")
            owned.validate_trunk_hashes(
                ROOT / "results/factorial-prep/current-trunk-hashes.json",
                root=ROOT,
            )
            lifecycle_started = True
            code, lifecycle = execute_lifecycle(plan, RUN_FLAG)
            manifest_path = Path(plan["output_dir"]) / "manifest.json"
            manifest = _read_json(manifest_path, "qualification manifest")
            terminal = publish_terminal(
                run / "qualification-terminal.json", lifecycle, manifest
            )
            return code if terminal["technical_eligible"] else 2
        except Exception:
            if not lifecycle_started:
                RUN_FLAG.unlink(missing_ok=True)
            raise
    finally:
        fcntl.flock(review_handle, fcntl.LOCK_UN)
        review_handle.close()


if __name__ == "__main__":
    sys.exit(main())
