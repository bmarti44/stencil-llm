#!/usr/bin/env python3
"""Own one bounded automatic-reasoning pilot; dry-run by default."""

import argparse
import fcntl
import hashlib
import json
import math
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import run_coding_competence as owned  # noqa: E402
from tools import run_qwen_thinking_tool_smoke as smoke_launcher  # noqa: E402

RESULTS_DIR = ROOT / "results/coding-auto-reasoning"
INPUT_ROOT = RESULTS_DIR
INPUT_PATHS = (
    RESULTS_DIR / "author-00/reviewed.json",
    RESULTS_DIR / "author-01/reviewed.json",
)
PREFLIGHT_PATH = RESULTS_DIR / "preflight.json"
PREVIEW_PATH = RESULTS_DIR / "preview.json"
RUN_FLAG = RESULTS_DIR / "RUNNING.flag"
REVIEW_LOCK = ROOT / ".review.lock"
TRUNK_HASHES_PATH = ROOT / "results/factorial-prep/current-trunk-hashes.json"
SMOKE_LIFECYCLE_PATH = ROOT / "results/coding-reasoning-smoke/run-01/lifecycle.json"
SMOKE_AUDIT_PATH = ROOT / "results/coding-reasoning-smoke/run-01/audit-astra.md"
DRIVER = ROOT / "scripts/coding_auto_reasoning.py"

RESERVATION_SECONDS = 3000
STARTUP_SECONDS = 600
CLEANUP_SECONDS = 60
CANDIDATE_CEILING_SECONDS = 3600
SMOKE_ACTUAL_SECONDS = 516.914703271992
MAX_MODEL_CALLS = 18
MAX_OUTPUT_TOKENS = 2048
THINKING_TOKEN_BUDGET = 1024
FINAL_ALLOWANCE_TOKENS = 1021
MIN_REFERENCE_SPARE = 128
CONTEXT_TOKENS = 32768

PREFLIGHT_CODE_FILES = (
    "scripts/coding_competence_dev.py",
    "scripts/coding_worker_dev.py",
    "src/stencil/focus/slab.py",
    "src/stencil/focus/slab_sandbox.py",
)
PREVIEW_CODE_FILES = (
    "scripts/coding_auto_reasoning.py",
    "src/stencil/focus/native_reasoning_tool.py",
    "scripts/coding_competence_run.py",
    *PREFLIGHT_CODE_FILES,
    *smoke_launcher.MODEL_METADATA_FILES,
)

DIRECT_SOURCE_FILES = (
    "src/stencil/focus/native_reasoning_tool.py",
    "scripts/coding_auto_reasoning.py",
    "tools/run_coding_auto_reasoning.py",
    "scripts/coding_competence_run.py",
    "scripts/coding_competence_dev.py",
    "scripts/coding_worker_dev.py",
    "src/stencil/focus/slab.py",
    "src/stencil/focus/slab_sandbox.py",
    "tools/run_coding_competence.py",
    "tools/run_qwen_thinking_tool_smoke.py",
    "scripts/qwen_thinking_tool_smoke.py",
)
TARGETED_TEST_FILES = (
    "tests/test_native_reasoning_tool.py",
    "tests/test_coding_auto_reasoning.py",
    "tests/test_run_coding_auto_reasoning.py",
)
ARTIFACT_FILES = (
    "results/coding-auto-reasoning/DESIGN.md",
    "results/coding-auto-reasoning/DATA-CONTRACT.md",
    "results/coding-auto-reasoning/RESOURCE-PLAN.md",
    "results/coding-auto-reasoning/preflight.json",
    "results/coding-auto-reasoning/preview.json",
    "results/coding-auto-reasoning/author-00/reviewed.json",
    "results/coding-auto-reasoning/author-01/reviewed.json",
)
REVIEW_FILES = (
    "results/coding-auto-reasoning/design-review-astra.md",
    "results/coding-auto-reasoning/client-review-astra.md",
    "results/coding-auto-reasoning/data-review-astra.md",
    "results/coding-auto-reasoning/review-astra.md",
)
SMOKE_EVIDENCE_FILES = (
    "results/coding-reasoning-smoke/run-01/lifecycle.json",
    "results/coding-reasoning-smoke/run-01/audit-astra.md",
)
TRACKED_BOUND_FILES = (
    *DIRECT_SOURCE_FILES,
    *TARGETED_TEST_FILES,
    *ARTIFACT_FILES,
    *REVIEW_FILES,
    *SMOKE_EVIDENCE_FILES,
    "results/factorial-prep/current-trunk-hashes.json",
)
MODEL_METADATA_FILES = smoke_launcher.MODEL_METADATA_FILES


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _read_json(path, label):
    try:
        return json.loads(Path(path).read_bytes())
    except Exception as exc:
        raise RuntimeError(f"{label} is not readable JSON: {exc}") from exc


def _snapshot(paths, *, root=ROOT):
    return {relative: _sha256(Path(root) / relative) for relative in paths}


def _input_receipt_matches(receipt, path):
    path = Path(path)
    return (
        type(receipt) is dict
        and Path(receipt.get("path", "")).resolve() == path.resolve()
        and type(receipt.get("bytes")) is int
        and receipt["bytes"] == path.stat().st_size
        and receipt.get("sha256") == _sha256(path)
        and _is_exact_int(receipt.get("documents"), 1)
        and receipt.get("read_error") is None
        and receipt.get("parse_error") is None
    )


def _input_receipts_match(receipts, paths):
    return (
        type(receipts) is list
        and len(receipts) == len(paths)
        and all(
            _input_receipt_matches(receipt, path)
            for receipt, path in zip(receipts, paths, strict=True)
        )
    )


def _require_source_snapshot(snapshot, expected_paths, root):
    if type(snapshot) is not dict or set(snapshot) != set(expected_paths):
        raise RuntimeError("artifact source snapshot has the wrong file set")
    for relative in expected_paths:
        path = Path(root) / relative
        if not path.is_file() or snapshot[relative] != _sha256(path):
            raise RuntimeError(f"artifact source snapshot mismatch: {relative}")


def _is_exact_int(value, expected):
    return type(value) is int and value == expected


def _finite_nonnegative(value):
    return (
        not isinstance(value, bool)
        and type(value) in {int, float}
        and math.isfinite(value)
        and value >= 0
    )


def _reviewed_projects(input_paths):
    documents = []
    episode_ids = []
    for path in input_paths:
        document = _read_json(path, "reviewed project")
        try:
            episode_id = document["public"]["episode_id"]
            public_rounds = document["public"]["rounds"]
            private_rounds = document["private"]["rounds"]
        except (KeyError, TypeError) as exc:
            raise RuntimeError("reviewed project structure is incomplete") from exc
        if (
            type(document) is not dict
            or not isinstance(episode_id, str)
            or not episode_id
            or type(public_rounds) is not list
            or type(private_rounds) is not list
            or len(public_rounds) != 3
            or len(private_rounds) != 3
            or any(type(item) is not dict for item in public_rounds)
            or any(type(item) is not dict for item in private_rounds)
            or any(
                not _is_exact_int(item.get("index"), index)
                for index, item in enumerate(public_rounds)
            )
            or any(
                not _is_exact_int(item.get("index"), index)
                for index, item in enumerate(private_rounds)
            )
        ):
            raise RuntimeError("reviewed project schedule is invalid")
        documents.append(document)
        episode_ids.append(episode_id)
    if len(set(episode_ids)) != 2:
        raise RuntimeError("reviewed project episode IDs are not unique")
    return documents, episode_ids


def _validate_project_preflight(project, path, episode_id, root):
    if (
        type(project) is not dict
        or not _is_exact_int(project.get("schema_version"), 1)
        or project.get("kind") != "coding-competence-cpu-preflight"
        or project.get("status") != "PASS"
        or not _is_exact_int(project.get("model_calls"), 0)
        or not _is_exact_int(project.get("documents"), 1)
        or not _input_receipts_match(project.get("inputs"), [path])
    ):
        raise RuntimeError("project CPU preflight did not pass")
    _require_source_snapshot(project.get("code_sha256"), PREFLIGHT_CODE_FILES, root)
    episodes = project.get("episodes")
    if type(episodes) is not list or len(episodes) != 1:
        raise RuntimeError("project CPU preflight has the wrong episode count")
    episode = episodes[0]
    if (
        type(episode) is not dict
        or episode.get("episode_id") != episode_id
        or episode.get("valid") is not True
        or episode.get("errors") != []
        or type(episode.get("rounds")) is not list
        or len(episode["rounds"]) != 3
        or any(type(item) is not dict for item in episode["rounds"])
        or any(
            not _is_exact_int(item.get("index"), index)
            for index, item in enumerate(episode["rounds"])
        )
        or type(project.get("execution_count")) is not int
        or project["execution_count"] <= 0
        or not _finite_nonnegative(project.get("elapsed_seconds"))
    ):
        raise RuntimeError("project CPU preflight schedule is invalid")


def _expected_reference_body(document, round_index, kind):
    private_round = document["private"]["rounds"][round_index]
    if kind == "replace_function":
        value = {"source": private_round["reference_patch"]}
    elif kind == "record_focus":
        value = {
            "obligations": [
                {"text": rule["text"], "source_ids": list(rule["source_ids"])}
                for rule in private_round["oracle"]["effective_rules"]
            ]
        }
    else:
        raise RuntimeError("preview reference action kind is invalid")
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def validate_artifacts(
    input_paths=INPUT_PATHS,
    preflight_path=PREFLIGHT_PATH,
    preview_path=PREVIEW_PATH,
    *,
    root=ROOT,
):
    """Reject a stale or non-passing zero-call qualification."""
    input_paths = tuple(Path(path) for path in input_paths)
    if len(input_paths) != 2:
        raise RuntimeError("exactly two reviewed project paths are required")
    documents, episode_ids = _reviewed_projects(input_paths)

    preflight = _read_json(preflight_path, "CPU preflight")
    if (
        type(preflight) is not dict
        or not _is_exact_int(preflight.get("schema_version"), 1)
        or preflight.get("kind") != "coding-auto-reasoning-cpu-preflight"
        or preflight.get("status") != "PASS"
        or not _is_exact_int(preflight.get("model_calls"), 0)
        or not _is_exact_int(preflight.get("documents"), 2)
        or not _input_receipts_match(preflight.get("inputs"), input_paths)
        or type(preflight.get("projects")) is not list
        or len(preflight["projects"]) != 2
    ):
        raise RuntimeError("CPU preflight is not a passing two-project receipt")
    for project, path, episode_id in zip(
        preflight["projects"], input_paths, episode_ids, strict=True
    ):
        _validate_project_preflight(project, path, episode_id, Path(root))
    if preflight.get("execution_count") != sum(
        project["execution_count"] for project in preflight["projects"]
    ) or not _finite_nonnegative(preflight.get("elapsed_seconds")):
        raise RuntimeError("CPU preflight accounting is invalid")

    preview = _read_json(preview_path, "preview")
    if (
        type(preview) is not dict
        or not _is_exact_int(preview.get("schema_version"), 1)
        or preview.get("kind") != "coding-auto-reasoning-preview"
        or preview.get("status") != "PASS"
        or not _is_exact_int(preview.get("model_calls"), 0)
        or not _is_exact_int(preview.get("documents"), 2)
        or not _is_exact_int(preview.get("scheduled_requests"), 6)
        or not _is_exact_int(preview.get("max_attempts_per_request"), 2)
        or not _is_exact_int(preview.get("max_model_calls"), MAX_MODEL_CALLS)
        or not _input_receipts_match(preview.get("inputs"), input_paths)
        or preview.get("preflight") != preflight
        or preview.get("all_cpu_preflight_passed") is not True
    ):
        raise RuntimeError("preview is not a passing receipt for the frozen schedule")
    _require_source_snapshot(preview.get("code_sha256"), PREVIEW_CODE_FILES, Path(root))

    settings = preview.get("settings")
    expected_settings = {
        "model": "/model",
        "max_output_tokens": MAX_OUTPUT_TOKENS,
        "reasoning_token_budget": THINKING_TOKEN_BUDGET,
        "available_final_tokens": FINAL_ALLOWANCE_TOKENS,
        "context_tokens": CONTEXT_TOKENS,
        "minimum_generation_headroom": MIN_REFERENCE_SPARE,
        "seed": 20260908,
        "temperature": 0.6,
        "top_p": 0.95,
        "top_k": 20,
        "min_p": 0.0,
    }
    if type(settings) is not dict or set(settings) != set(expected_settings):
        raise RuntimeError("preview settings are malformed")
    for key, expected in expected_settings.items():
        value = settings[key]
        if (
            isinstance(value, bool)
            or value != expected
            or (type(expected) is int and type(value) is not int)
            or (type(expected) is float and type(value) not in {int, float})
        ):
            raise RuntimeError(f"preview setting {key} is unqualified")

    document_by_id = dict(zip(episode_ids, documents, strict=True))
    actions = preview.get("reference_actions")
    if (
        preview.get("all_reference_actions_headroom") is not True
        or type(actions) is not list
        or len(actions) != 12
    ):
        raise RuntimeError("preview reference capacity is unqualified")
    action_schedule = set()
    for action in actions:
        if type(action) is not dict:
            raise RuntimeError("preview reference action is malformed")
        episode_id = action.get("episode_id")
        round_index = action.get("round_index")
        kind = action.get("kind")
        identity = (episode_id, round_index, kind)
        if type(round_index) is not int or not 0 <= round_index < 3:
            raise RuntimeError("preview reference action identity is invalid")
        try:
            body = _expected_reference_body(
                document_by_id[episode_id], round_index, kind
            )
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("preview reference action identity is invalid") from exc
        tokens = action.get("argument_tokens")
        headroom = action.get("generation_headroom")
        if (
            action.get("argument_body") != body.decode("utf-8")
            or action.get("argument_body_sha256") != hashlib.sha256(body).hexdigest()
            or action.get("argument_body_bytes") != len(body)
            or type(tokens) is not int
            or tokens < 0
            or not _is_exact_int(action.get("full_reasoning_bound_tokens"), 1024)
            or not _is_exact_int(action.get("reasoning_delimiter_and_eos_tokens"), 3)
            or not _is_exact_int(
                action.get("available_final_tokens"), FINAL_ALLOWANCE_TOKENS
            )
            or headroom != FINAL_ALLOWANCE_TOKENS - tokens
            or type(headroom) is not int
            or headroom < MIN_REFERENCE_SPARE
            or action.get("eligible") is not True
        ):
            raise RuntimeError("preview reference action accounting is invalid")
        action_schedule.add(identity)
    expected_actions = {
        (episode_id, round_index, kind)
        for episode_id in episode_ids
        for round_index in range(3)
        for kind in ("record_focus", "replace_function")
    }
    if action_schedule != expected_actions:
        raise RuntimeError("preview reference action schedule is incomplete")

    cold = preview.get("selector_cold_requests")
    if type(cold) is not list or len(cold) != 6:
        raise RuntimeError("preview cold selector schedule is incomplete")
    cold_schedule = set()
    for item in cold:
        if type(item) is not dict:
            raise RuntimeError("preview cold selector row is malformed")
        tokens = item.get("local_serialized_request_tokens")
        with_output = item.get("local_serialized_request_with_output")
        if (
            type(item.get("round_index")) is not int
            or type(tokens) is not int
            or tokens < 0
            or type(with_output) is not int
            or with_output != tokens + MAX_OUTPUT_TOKENS
            or with_output > CONTEXT_TOKENS
            or item.get("local_serialized_request_below_context") is not True
            or item.get("local_count_is_native_prompt_tokens") is not False
        ):
            raise RuntimeError("preview cold selector context is unqualified")
        cold_schedule.add((item.get("episode_id"), item.get("round_index")))
    expected_requests = {
        (episode_id, round_index)
        for episode_id in episode_ids
        for round_index in range(3)
    }
    if cold_schedule != expected_requests:
        raise RuntimeError("preview cold selector schedule is incomplete")

    growth = preview.get("conservative_growth")
    if (
        preview.get("future_actual_prompt_claim") is not False
        or preview.get("actual_native_render_required_before_every_generation")
        is not True
        or type(growth) is not list
        or len(growth) != 12
    ):
        raise RuntimeError("preview future-context qualification is invalid")
    growth_schedule = set()
    for item in growth:
        if type(item) is not dict:
            raise RuntimeError("preview growth row is malformed")
        round_index = item.get("round_index")
        attempt_index = item.get("attempt_index")
        prior_pairs = item.get("maximum_prior_worker_action_pairs")
        if (
            type(round_index) is not int
            or type(attempt_index) is not int
            or not 0 <= round_index < 3
            or not 0 <= attempt_index < 2
            or type(prior_pairs) is not int
            or prior_pairs != round_index * 2 + attempt_index
            or type(item.get("maximum_repeated_module_observations")) is not int
            or item.get("maximum_repeated_module_observations") != prior_pairs + 1
            or type(item.get("visible_authentic_source_bytes")) is not int
            or item["visible_authentic_source_bytes"] <= 0
            or type(item.get("module_byte_limit_each_observation")) is not int
            or item["module_byte_limit_each_observation"] <= 0
            or type(item.get("submitted_source_byte_limit_each_action")) is not int
            or item["submitted_source_byte_limit_each_action"] <= 0
            or item.get("universal_future_prompt_fit_claim") is not False
        ):
            raise RuntimeError("preview growth row is invalid")
        growth_schedule.add((item.get("episode_id"), round_index, attempt_index))
    expected_growth = {
        (episode_id, round_index, attempt_index)
        for episode_id in episode_ids
        for round_index in range(3)
        for attempt_index in range(2)
    }
    if growth_schedule != expected_growth:
        raise RuntimeError("preview growth schedule is incomplete")

    resource = preview.get("resource_bounds")
    if (
        type(resource) is not dict
        or not _is_exact_int(resource.get("maximum_render_requests"), 18)
        or not _is_exact_int(resource.get("maximum_generation_requests"), 18)
        or not _is_exact_int(resource.get("maximum_http_requests"), 36)
        or type(resource.get("maximum_sandbox_checks")) is not int
        or resource["maximum_sandbox_checks"] <= 0
        or not _is_exact_int(
            resource.get("maximum_prior_worker_action_pairs_per_prompt"), 5
        )
        or not _is_exact_int(
            resource.get("maximum_repeated_module_observations_per_prompt"), 6
        )
        or not _finite_nonnegative(preview.get("cpu_elapsed_seconds"))
    ):
        raise RuntimeError("preview resource bounds are invalid")

    return {
        "documents": 2,
        "scheduled_requests": 6,
        "max_model_calls": MAX_MODEL_CALLS,
        "input_sha256": {
            str(path.relative_to(Path(root))): _sha256(path) for path in input_paths
        },
        "preflight_sha256": _sha256(preflight_path),
        "preview_sha256": _sha256(preview_path),
        "minimum_reference_headroom": min(
            action["generation_headroom"] for action in actions
        ),
        "future_actual_prompt_claim": False,
    }


def validate_combined_budget(lifecycle):
    required = {
        "status": "DRIVER_EXITED",
        "driver_exit_code": 0,
        "cleaned": True,
        "cleanup_evidence_complete": True,
    }
    if type(lifecycle) is not dict or any(
        lifecycle.get(key) != value for key, value in required.items()
    ):
        raise RuntimeError("prior reasoning smoke lifecycle is not complete")
    actual = lifecycle.get("elapsed_seconds")
    if (
        isinstance(actual, bool)
        or type(actual) not in {int, float}
        or not math.isfinite(actual)
        or actual != SMOKE_ACTUAL_SECONDS
    ):
        raise RuntimeError("prior reasoning smoke charge is not the audited value")
    combined = actual + RESERVATION_SECONDS
    if combined > CANDIDATE_CEILING_SECONDS:
        raise RuntimeError("combined reservation exceeds the candidate ceiling")
    return {
        "prior_smoke_seconds": actual,
        "new_reservation_seconds": RESERVATION_SECONDS,
        "combined_candidate_seconds": combined,
        "candidate_ceiling_seconds": CANDIDATE_CEILING_SECONDS,
        "remaining_candidate_seconds": CANDIDATE_CEILING_SECONDS - combined,
    }


def validate_smoke_evidence(
    lifecycle_path=SMOKE_LIFECYCLE_PATH, audit_path=SMOKE_AUDIT_PATH
):
    lifecycle = _read_json(lifecycle_path, "reasoning smoke lifecycle")
    budget = validate_combined_budget(lifecycle)
    audit_path = Path(audit_path)
    if not audit_path.is_file():
        raise RuntimeError("reasoning smoke audit is absent")
    return {
        **budget,
        "lifecycle_sha256": _sha256(lifecycle_path),
        "audit_sha256": _sha256(audit_path),
    }


def _container_command(name):
    return smoke_launcher._container_command(name)


def make_plan(run_dir, *, container_name=None):
    if container_name is None:
        container_name = "stencil-coding-auto-reasoning-" + uuid.uuid4().hex[:12]
    run = Path(run_dir)
    return {
        "schema_version": 1,
        "kind": "coding-auto-reasoning-launch-plan",
        "execute": False,
        "run_dir": str(run),
        "container_name": container_name,
        "container_command": _container_command(container_name),
        "driver": str(DRIVER),
        "input": str(INPUT_ROOT),
        "input_paths": [str(path) for path in INPUT_PATHS],
        "output_dir": str(run / "calls"),
        "base_url": "http://127.0.0.1:18088",
        "model": "/model",
        "maximum_model_calls": MAX_MODEL_CALLS,
        "max_output_tokens": MAX_OUTPUT_TOKENS,
        "thinking_token_budget": THINKING_TOKEN_BUDGET,
        "context_window_tokens": CONTEXT_TOKENS,
        "reservation_seconds": RESERVATION_SECONDS,
        "startup_ceiling_seconds": STARTUP_SECONDS,
        "cleanup_reserve_seconds": CLEANUP_SECONDS,
        "prior_smoke_actual_seconds": SMOKE_ACTUAL_SECONDS,
        "combined_candidate_charge_seconds": (
            SMOKE_ACTUAL_SECONDS + RESERVATION_SECONDS
        ),
        "candidate_ceiling_seconds": CANDIDATE_CEILING_SECONDS,
        "tracked_bound_files": list(TRACKED_BOUND_FILES),
        "model_metadata_files": list(MODEL_METADATA_FILES),
    }


def _tracked_clean(relative, *, root=ROOT, command=owned.run_owned):
    smoke_launcher._tracked_clean(relative, root=root, command=command)


def qualify_environment(*, root=ROOT, container_name, command=owned.run_owned):
    root = Path(root)
    flags = owned._active_flags(root)
    if flags:
        raise RuntimeError(f"active run flag exists: {flags[0]}")
    if owned._active_review_lock(root / ".review.lock"):
        raise RuntimeError("review wrapper lock is active")
    containers = command(
        ["docker", "ps", "-q"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    if owned._text(containers).strip():
        raise RuntimeError("a running container already exists")
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
    if owned._text(gpu).strip():
        raise RuntimeError("a GPU compute process already exists")
    command(
        ["docker", "image", "inspect", owned.IMAGE],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    for relative in TRACKED_BOUND_FILES:
        _tracked_clean(relative, root=root, command=command)
    head = owned._text(
        command(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    ).strip()
    if len(head) != 40:
        raise RuntimeError("could not resolve exact current git HEAD")
    return {"git_head": head}


def recheck_resource_exclusivity(
    *,
    expected_head,
    expected_snapshot,
    expected_model_snapshot,
    command=owned.run_owned,
):
    other_flags = [path for path in owned._active_flags() if path != RUN_FLAG]
    if other_flags:
        raise RuntimeError(f"another run flag appeared: {other_flags[0]}")
    containers = command(
        ["docker", "ps", "-q"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    if owned._text(containers).strip():
        raise RuntimeError("a container appeared after resource qualification")
    gpu = command(
        ["nvidia-smi", "--query-compute-apps=pid", "--format=csv,noheader"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if owned._text(gpu).strip():
        raise RuntimeError("a GPU process appeared after resource qualification")
    head = owned._text(
        command(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    ).strip()
    if head != expected_head:
        raise RuntimeError("git HEAD changed after qualification")
    if _snapshot(TRACKED_BOUND_FILES) != expected_snapshot:
        raise RuntimeError("a bound file changed after original freeze")
    if _snapshot(MODEL_METADATA_FILES) != expected_model_snapshot:
        raise RuntimeError("model metadata changed after original freeze")
    owned.validate_trunk_hashes()


def _reserve_flag(run, name):
    payload = (
        json.dumps(
            {"pid": os.getpid(), "run_dir": str(run), "container": name},
            sort_keys=True,
        )
        + "\n"
    )
    descriptor = os.open(RUN_FLAG, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())


def prepare_execution(run_dir, *, root=ROOT, container_name, command=owned.run_owned):
    root = Path(root)
    artifacts = validate_artifacts(
        tuple(root / path.relative_to(ROOT) for path in INPUT_PATHS),
        root / PREFLIGHT_PATH.relative_to(ROOT),
        root / PREVIEW_PATH.relative_to(ROOT),
        root=root,
    )
    smoke = validate_smoke_evidence(
        root / SMOKE_LIFECYCLE_PATH.relative_to(ROOT),
        root / SMOKE_AUDIT_PATH.relative_to(ROOT),
    )
    trunk = owned.validate_trunk_hashes(
        root / TRUNK_HASHES_PATH.relative_to(ROOT), root=root
    )
    environment = qualify_environment(
        root=root, container_name=container_name, command=command
    )
    return {
        "artifacts": artifacts,
        "smoke": smoke,
        "trunk": trunk,
        "environment": environment,
        "run_dir": str(run_dir),
        "tracked_sha256": _snapshot(TRACKED_BOUND_FILES, root=root),
        "model_metadata_sha256": _snapshot(MODEL_METADATA_FILES, root=root),
    }


def _parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    return parser


def main(argv=None):
    args = _parser().parse_args(argv)
    run = args.run_dir.resolve()
    if run.parent != RESULTS_DIR or not run.name.startswith("run-"):
        raise ValueError(
            "run-dir must be a run-* direct child of results/coding-auto-reasoning"
        )
    if run.exists():
        raise FileExistsError(f"run directory already exists: {run}")
    plan = make_plan(run)
    if not args.execute:
        print(json.dumps(plan, ensure_ascii=True, indent=2, sort_keys=True))
        return 0

    owned.register_pid(os.getpid())
    qualification = prepare_execution(run, container_name=plan["container_name"])
    review_handle = owned.acquire_review_lock(REVIEW_LOCK)
    try:
        _reserve_flag(run, plan["container_name"])
        run_created = False
        try:
            run.mkdir(parents=False, exist_ok=False)
            run_created = True
            plan["execute"] = True
            owned._write_json(
                run / "freeze.json",
                {
                    "schema_version": 1,
                    "kind": "coding-auto-reasoning-original-freeze",
                    "plan": plan,
                    "qualification": qualification,
                    "frozen_unix": time.time(),
                },
            )
            recheck_resource_exclusivity(
                expected_head=qualification["environment"]["git_head"],
                expected_snapshot=qualification["tracked_sha256"],
                expected_model_snapshot=qualification["model_metadata_sha256"],
            )
            code, _lifecycle = owned.run_lifecycle(plan, run_flag=RUN_FLAG)
            return code
        except Exception:
            if run_created:
                owned._write_json(
                    run / "lifecycle.json",
                    {
                        "schema_version": 1,
                        "status": "INCOMPLETE_BEFORE_SERVER",
                        "ended_unix": time.time(),
                    },
                )
            RUN_FLAG.unlink(missing_ok=True)
            raise
    finally:
        fcntl.flock(review_handle, fcntl.LOCK_UN)
        review_handle.close()


if __name__ == "__main__":
    sys.exit(main())
