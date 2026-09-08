#!/usr/bin/env python3
"""Own one bounded Qwen coding-competence lifecycle; dry-run by default."""

import argparse
import base64
import fcntl
import hashlib
import json
import math
import os
import subprocess
import sys
import time
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results/coding-competence"
DATA_PATH = RESULTS_DIR / "kimi-dev-reviewed.json"
PREFLIGHT_PATH = RESULTS_DIR / "preflight.json"
PREVIEW_PATH = RESULTS_DIR / "preview.json"
TRUNK_HASHES_PATH = ROOT / "results/factorial-prep/current-trunk-hashes.json"
RUN_FLAG = RESULTS_DIR / "RUNNING.flag"
OWNED_PIDS = ROOT / ".stencil-owned-pids"
REVIEW_LOCK = ROOT / ".review.lock"
DRIVER = ROOT / "scripts/coding_competence_run.py"
IMAGE = (
    "vllm/vllm-openai@sha256:"
    "3dbe092ec5b2cef63b6104d33fa75d6ce53a7870962529ada69f78bbbc38e776"
)
BASE_URL = "http://127.0.0.1:18088"
RESERVATION_SECONDS = 2700
STARTUP_SECONDS = 600
CLEANUP_SECONDS = 60
MAX_OUTPUT_TOKENS = 1024
CONTEXT_TOKENS = 32768
MIN_HEADROOM = 128

PREFLIGHT_CODE_FILES = (
    "scripts/coding_competence_dev.py",
    "scripts/coding_worker_dev.py",
    "src/stencil/focus/slab.py",
    "src/stencil/focus/slab_sandbox.py",
)
RUNTIME_CODE_FILES = (
    "scripts/coding_competence_run.py",
    *PREFLIGHT_CODE_FILES,
)
CONTRACT_FILES = (
    "results/coding-competence/PROTOCOL.md",
    "results/coding-competence/NATIVE-CONTRACT.md",
    "results/coding-competence/DATA-CONTRACT.md",
    "results/coding-competence/RUNTIME-BRIEF.md",
)
REVIEW_FILES = (
    "results/coding-competence/data-review-astra.md",
    "results/coding-competence/runtime-review-astra.md",
)
BOUND_FILES = (
    "tools/run_coding_competence.py",
    *RUNTIME_CODE_FILES,
    *CONTRACT_FILES,
    *REVIEW_FILES,
    "results/coding-competence/kimi-dev-reviewed.json",
    "results/coding-competence/preflight.json",
    "results/coding-competence/preview.json",
    "results/factorial-prep/current-trunk-hashes.json",
)


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path, value):
    body = json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    with path.open("w", encoding="utf-8") as handle:
        handle.write(body)
        handle.flush()
        os.fsync(handle.fileno())


def _write_bytes(path, value):
    with Path(path).open("wb") as handle:
        handle.write(value)
        handle.flush()
        os.fsync(handle.fileno())


def _read_json(path, label):
    try:
        return json.loads(path.read_bytes())
    except Exception as exc:
        raise RuntimeError(f"{label} is not readable JSON: {exc}") from exc


def _input_is_bound(receipts, path, document_count):
    if type(receipts) is not list or len(receipts) != 1:
        return False
    receipt = receipts[0]
    return (
        type(receipt) is dict
        and Path(receipt.get("path", "")).resolve() == path.resolve()
        and receipt.get("bytes") == path.stat().st_size
        and receipt.get("sha256") == _sha256(path)
        and receipt.get("documents") == document_count
        and receipt.get("read_error") is None
        and receipt.get("parse_error") is None
    )


def _require_source_snapshot(snapshot, expected_paths, root):
    if type(snapshot) is not dict or set(snapshot) != set(expected_paths):
        raise RuntimeError("artifact source snapshot has the wrong file set")
    for relative in expected_paths:
        path = root / relative
        if not path.is_file() or snapshot[relative] != _sha256(path):
            raise RuntimeError(f"artifact source snapshot mismatch: {relative}")


def _setting(settings, primary, alias=None):
    if primary in settings:
        return settings[primary]
    if alias is not None:
        return settings.get(alias)
    return None


def _is_exact_int(value, expected):
    return type(value) is int and value == expected


def validate_artifacts(
    data_path=DATA_PATH,
    preflight_path=PREFLIGHT_PATH,
    preview_path=PREVIEW_PATH,
    *,
    root=ROOT,
):
    """Reject any non-passing or stale CPU qualification before a launch."""
    data_path = Path(data_path)
    preflight_path = Path(preflight_path)
    preview_path = Path(preview_path)
    documents = _read_json(data_path, "reviewed data")
    if type(documents) is not list or len(documents) != 4:
        raise RuntimeError("reviewed data must contain exactly four documents")
    episode_ids = []
    for document in documents:
        try:
            episode_id = document["public"]["episode_id"]
            public_rounds = document["public"]["rounds"]
            private_rounds = document["private"]["rounds"]
        except (KeyError, TypeError) as exc:
            raise RuntimeError("reviewed data structure is incomplete") from exc
        if (
            not isinstance(episode_id, str)
            or not episode_id
            or type(public_rounds) is not list
            or type(private_rounds) is not list
            or [item.get("index") for item in public_rounds] != [0, 1, 2]
            or [item.get("index") for item in private_rounds] != [0, 1, 2]
        ):
            raise RuntimeError("reviewed data schedule is invalid")
        episode_ids.append(episode_id)
    if len(set(episode_ids)) != 4:
        raise RuntimeError("reviewed data episode IDs are not unique")

    preflight = _read_json(preflight_path, "preflight")
    if (
        not _is_exact_int(preflight.get("schema_version"), 1)
        or preflight.get("kind") != "coding-competence-cpu-preflight"
        or preflight.get("status") != "PASS"
        or not _is_exact_int(preflight.get("model_calls"), 0)
        or not _is_exact_int(preflight.get("documents"), 4)
        or not _input_is_bound(preflight.get("inputs"), data_path, 4)
    ):
        raise RuntimeError("preflight is not a passing receipt for reviewed data")
    _require_source_snapshot(
        preflight.get("code_sha256"), PREFLIGHT_CODE_FILES, Path(root)
    )
    episodes = preflight.get("episodes")
    if type(episodes) is not list or len(episodes) != 4:
        raise RuntimeError("preflight must qualify all four episodes")
    observed = set()
    for episode in episodes:
        if (
            type(episode) is not dict
            or episode.get("valid") is not True
            or episode.get("errors") != []
            or type(episode.get("rounds")) is not list
            or len(episode["rounds"]) != 3
        ):
            raise RuntimeError("preflight episode did not pass")
        observed.add(episode.get("episode_id"))
        if [round_.get("index") for round_ in episode["rounds"]] != [0, 1, 2]:
            raise RuntimeError("preflight episode schedule is invalid")
        for round_ in episode["rounds"]:
            headroom = round_.get("provisional_generation_headroom")
            if type(headroom) is not int or headroom < MIN_HEADROOM:
                raise RuntimeError("preflight reference headroom is unqualified")
    elapsed = preflight.get("elapsed_seconds")
    if (
        observed != set(episode_ids)
        or type(preflight.get("execution_count")) is not int
        or preflight["execution_count"] <= 0
        or type(elapsed) not in {int, float}
        or isinstance(elapsed, bool)
        or not math.isfinite(elapsed)
        or elapsed < 0
    ):
        raise RuntimeError("preflight episode schedule is not bound to reviewed data")

    preview = _read_json(preview_path, "preview")
    if (
        not _is_exact_int(preview.get("schema_version"), 1)
        or preview.get("kind") != "coding-competence-native-preview"
        or preview.get("status") != "PASS"
        or not _is_exact_int(preview.get("model_calls"), 0)
        or not _is_exact_int(preview.get("documents"), 4)
        or not _is_exact_int(preview.get("scheduled_requests"), 12)
        or not _is_exact_int(preview.get("max_attempts_per_request"), 3)
        or not _is_exact_int(preview.get("max_model_calls"), 36)
        or not _input_is_bound(preview.get("inputs"), data_path, 4)
    ):
        raise RuntimeError("preview is not a passing receipt for the frozen schedule")
    _require_source_snapshot(
        preview.get("code_sha256"), RUNTIME_CODE_FILES, Path(root)
    )
    settings = preview.get("settings")
    if type(settings) is not dict:
        raise RuntimeError("preview settings are absent")
    required_settings = {
        "model": "/model",
        "seed": 20260908,
        "context_tokens": CONTEXT_TOKENS,
        "minimum_generation_headroom": MIN_HEADROOM,
    }
    for key, expected in required_settings.items():
        if settings.get(key) != expected:
            raise RuntimeError(f"preview setting {key} is unqualified")
    temperature = settings.get("temperature")
    if (
        isinstance(temperature, bool)
        or type(temperature) not in {int, float}
        or temperature != 0
    ):
        raise RuntimeError("preview setting temperature is unqualified")
    if not _is_exact_int(
        _setting(settings, "max_output_tokens", "max_tokens"), MAX_OUTPUT_TOKENS
    ):
        raise RuntimeError("preview setting max_output_tokens is unqualified")
    actions = preview.get("reference_actions")
    if (
        preview.get("all_reference_actions_headroom") is not True
        or type(actions) is not list
        or len(actions) != 12
    ):
        raise RuntimeError("preview reference headroom is unqualified")
    action_schedule = set()
    documents_by_id = {
        document["public"]["episode_id"]: document for document in documents
    }
    for action in actions:
        if type(action) is not dict:
            raise RuntimeError("preview reference action is malformed")
        headroom = action.get("generation_headroom")
        if (
            type(headroom) is not int
            or headroom < MIN_HEADROOM
            or action.get("eligible") is not True
        ):
            raise RuntimeError("preview reference headroom is unqualified")
        identity = (action.get("episode_id"), action.get("round_index"))
        action_schedule.add(identity)
        try:
            reference = documents_by_id[identity[0]]["private"]["rounds"][
                identity[1]
            ]["reference_patch"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("preview reference action identity is invalid") from exc
        expected_body = json.dumps(
            {"source": reference},
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        try:
            recorded_body = base64.b64decode(
                action.get("argument_body_base64", ""), validate=True
            )
        except Exception as exc:
            raise RuntimeError("preview reference action bytes are invalid") from exc
        argument_tokens = action.get("argument_tokens")
        response_tokens = action.get("response_tokens_with_eos")
        if (
            recorded_body != expected_body
            or action.get("argument_body") != expected_body.decode("utf-8")
            or action.get("argument_body_bytes") != len(expected_body)
            or action.get("argument_body_sha256")
            != hashlib.sha256(expected_body).hexdigest()
            or action.get("source_sha256")
            != hashlib.sha256(reference.encode("utf-8")).hexdigest()
            or type(argument_tokens) is not int
            or argument_tokens < 0
            or action.get("eos_allowance_tokens") != 1
            or response_tokens != argument_tokens + 1
            or headroom != MAX_OUTPUT_TOKENS - response_tokens
        ):
            raise RuntimeError("preview reference action accounting is invalid")
    expected_schedule = {
        (episode_id, index) for episode_id in episode_ids for index in range(3)
    }
    if action_schedule != expected_schedule:
        raise RuntimeError("preview reference action schedule is incomplete")
    context = preview.get("context_preflight")
    if type(context) is not dict:
        raise RuntimeError("preview context preflight is absent")
    cold = context.get("cold_requests")
    if (
        context.get("actual_cold_request_count") != 4
        or type(cold) is not list
        or len(cold) != 4
        or context.get("later_actual_requests_known") is not False
        or context.get("local_counts_are_provisional") is not True
        or context.get("all_local_cold_serializations_below_context") is not True
        or context.get("authoritative_render_required_before_every_model_call")
        is not True
    ):
        raise RuntimeError("preview context qualification is invalid")
    cold_schedule = set()
    for item in cold:
        with_output = item.get("local_serialized_request_with_output")
        if (
            type(item) is not dict
            or item.get("round_index") != 0
            or item.get("local_count_is_native_prompt_tokens") is not False
            or item.get("local_serialized_request_below_context") is not True
            or type(with_output) is not int
            or with_output > CONTEXT_TOKENS
        ):
            raise RuntimeError("preview cold context row is invalid")
        cold_schedule.add(item.get("episode_id"))
    if cold_schedule != set(episode_ids):
        raise RuntimeError("preview cold context schedule is incomplete")
    bounds = context.get("conservative_bounds")
    if (
        type(bounds) is not list
        or len(bounds) != 36
        or type(context.get("all_conservative_bounds_fit")) is not bool
        or not isinstance(context.get("bound_interpretation"), str)
        or not context["bound_interpretation"]
    ):
        raise RuntimeError("preview conservative context bounds are unqualified")
    bound_schedule = set()
    for item in bounds:
        if type(item) is not dict:
            raise RuntimeError("preview conservative context row is malformed")
        round_index = item.get("round_index")
        attempt_index = item.get("attempt_index")
        prior_actions = item.get("prior_action_pairs")
        module_observations = item.get("repeated_current_module_observations")
        output_bound = item.get("context_with_output_bound")
        if (
            type(round_index) is not int
            or type(attempt_index) is not int
            or not 0 <= round_index < 3
            or not 0 <= attempt_index < 3
            or prior_actions != round_index * 3 + attempt_index
            or module_observations != prior_actions + 1
            or type(item.get("public_outcome_slots")) is not int
            or item["public_outcome_slots"] < 0
            or type(output_bound) is not int
            or item.get("fits_context")
            is not (output_bound <= CONTEXT_TOKENS)
            or item.get("future_actual_prompt_claim") is not False
        ):
            raise RuntimeError("preview conservative context row is unqualified")
        bound_schedule.add((item.get("episode_id"), round_index, attempt_index))
    expected_bound_schedule = {
        (episode_id, round_index, attempt_index)
        for episode_id in episode_ids
        for round_index in range(3)
        for attempt_index in range(3)
    }
    if bound_schedule != expected_bound_schedule:
        raise RuntimeError("preview conservative context schedule is incomplete")
    calculated_fit = all(item["fits_context"] for item in bounds)
    if context["all_conservative_bounds_fit"] is not calculated_fit:
        raise RuntimeError("preview conservative context aggregate is inconsistent")
    resource = preview.get("resource_bounds")
    if (
        type(resource) is not dict
        or not _is_exact_int(resource.get("maximum_render_requests"), 36)
        or not _is_exact_int(resource.get("maximum_generation_requests"), 36)
        or not _is_exact_int(resource.get("maximum_http_requests"), 72)
        or type(resource.get("maximum_sandbox_checks")) is not int
        or resource["maximum_sandbox_checks"] <= 0
        or resource.get("maximum_prior_action_pairs_per_prompt") != 8
        or resource.get("maximum_repeated_module_observations_per_prompt") != 9
    ):
        raise RuntimeError("preview resource bounds are invalid")

    return {
        "documents": 4,
        "scheduled_requests": 12,
        "max_model_calls": 36,
        "data_sha256": _sha256(data_path),
        "preflight_sha256": _sha256(preflight_path),
        "preview_sha256": _sha256(preview_path),
        "minimum_reference_headroom": min(
            action["generation_headroom"] for action in actions
        ),
        "all_conservative_bounds_fit": context["all_conservative_bounds_fit"],
    }


def validate_trunk_hashes(path=TRUNK_HASHES_PATH, *, root=ROOT):
    receipt = _read_json(Path(path), "current trunk hashes")
    files = receipt.get("files")
    if type(files) is not list or not files:
        raise RuntimeError("current trunk hash receipt has no files")
    total = 0
    seen = set()
    for item in files:
        required = {"path", "bytes", "mtime_ns", "sha256"}
        if type(item) is not dict or set(item) < required:
            raise RuntimeError("current trunk hash receipt is malformed")
        relative = item["path"]
        if (
            type(relative) is not str
            or relative in seen
            or Path(relative).is_absolute()
            or ".." in Path(relative).parts
            or type(item["bytes"]) is not int
            or type(item["mtime_ns"]) is not int
            or type(item["sha256"]) is not str
            or len(item["sha256"]) != 64
        ):
            raise RuntimeError("current trunk hash receipt contains an invalid row")
        seen.add(relative)
        candidate = Path(root) / relative
        stat = candidate.stat()
        if (stat.st_size, stat.st_mtime_ns) != (item["bytes"], item["mtime_ns"]):
            raise RuntimeError(f"current trunk file changed: {relative}")
        total += stat.st_size
    if receipt.get("total_bytes") != total:
        raise RuntimeError("current trunk hash total is inconsistent")
    return {
        "receipt_sha256": _sha256(Path(path)),
        "files": len(files),
        "total_bytes": total,
    }


def register_pid(pid, registry=None):
    if registry is None:
        registry = OWNED_PIDS
    with Path(registry).open("a", encoding="ascii") as handle:
        handle.write(f"{pid}\n")
        handle.flush()
        os.fsync(handle.fileno())


def start_owned(command, **kwargs):
    process = subprocess.Popen(command, **kwargs)
    register_pid(process.pid)
    return process


def _communicate(process, timeout):
    stdout, stderr = process.communicate(timeout=max(0.01, timeout))
    return subprocess.CompletedProcess(
        [], process.returncode, stdout=stdout, stderr=stderr
    )


def run_owned(command, *, timeout=20, check=True, **kwargs):
    process = start_owned(command, **kwargs)
    try:
        result = _communicate(process, timeout)
    except subprocess.TimeoutExpired:
        _stop_client(process, 2)
        raise
    result.args = command
    if check and result.returncode != 0:
        raise subprocess.CalledProcessError(
            result.returncode, command, output=result.stdout, stderr=result.stderr
        )
    return result


def _active_review_lock(path=REVIEW_LOCK):
    with Path(path).open("a+") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return True
        fcntl.flock(handle, fcntl.LOCK_UN)
    return False


def _text(result):
    value = result.stdout
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value or ""


def _active_flags(root=ROOT):
    return sorted(path for path in (Path(root) / "results").rglob("RUNNING.flag"))


def _tracked_clean(relative, *, root=ROOT, command=run_owned):
    command(
        ["git", "-C", str(root), "ls-files", "--error-unmatch", "--", relative],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    status = command(
        [
            "git", "-C", str(root), "status", "--porcelain=v1",
            "--untracked-files=all", "--", relative,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if _text(status).strip():
        raise RuntimeError(f"bound file is dirty or untracked: {relative}")


def qualify_environment(*, root=ROOT, container_name=None, command=run_owned):
    flags = _active_flags(root)
    if flags:
        raise RuntimeError(f"active run flag exists: {flags[0]}")
    if _active_review_lock(Path(root) / ".review.lock"):
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
    for relative in BOUND_FILES:
        _tracked_clean(relative, root=Path(root), command=command)
    head = _text(
        command(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    ).strip()
    if len(head) != 40:
        raise RuntimeError("could not resolve the exact current git head")
    return {"git_head": head}


def recheck_resource_exclusivity(*, expected_head, command=run_owned):
    other_flags = [path for path in _active_flags() if path != RUN_FLAG]
    if other_flags:
        raise RuntimeError(f"another run flag appeared: {other_flags[0]}")
    containers = command(
        ["docker", "ps", "-q"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    if _text(containers).strip():
        raise RuntimeError("a container appeared after resource qualification")
    gpu = command(
        ["nvidia-smi", "--query-compute-apps=pid", "--format=csv,noheader"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if _text(gpu).strip():
        raise RuntimeError("a GPU process appeared after resource qualification")
    status = command(
        [
            "git", "-C", str(ROOT), "status", "--porcelain=v1",
            "--untracked-files=all", "--", *BOUND_FILES,
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if _text(status).strip():
        raise RuntimeError("a bound file became dirty after qualification")
    head = _text(
        command(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    ).strip()
    if head != expected_head:
        raise RuntimeError("git HEAD changed after qualification")


def acquire_review_lock(path=REVIEW_LOCK):
    handle = Path(path).open("a+")
    try:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as exc:
        handle.close()
        raise RuntimeError("review wrapper lock became active") from exc
    return handle


def _container_command(name):
    return [
        "docker", "run", "--pull=never", "-d", "--name", name,
        "--label", f"stencil.owner=coding-competence:{name}",
        "--device", "nvidia.com/gpu=0", "--ipc=host",
        "-p", "127.0.0.1:18088:8000", "-e", "VLLM_BATCH_INVARIANT=1",
        "-v", f"{ROOT}/models/qwen3-30b-a3b-hf:/model:ro", IMAGE,
        "--attention-backend", "TRITON_ATTN", "--model", "/model",
        "--dtype", "bfloat16", "--kv-cache-dtype", "auto",
        "--tensor-parallel-size", "1", "--max-model-len", "32768",
        "--max-num-seqs", "4", "--max-num-batched-tokens", "2048",
        "--gpu-memory-utilization", "0.70", "--enable-prefix-caching",
        "--generation-config", "vllm", "--enable-auto-tool-choice",
        "--tool-call-parser", "hermes",
    ]


def make_plan(run_dir, *, container_name=None):
    if container_name is None:
        container_name = "stencil-coding-competence-" + uuid.uuid4().hex[:12]
    return {
        "schema_version": 1,
        "kind": "coding-competence-launch-plan",
        "execute": False,
        "run_dir": str(Path(run_dir)),
        "container_name": container_name,
        "container_command": _container_command(container_name),
        "driver": str(DRIVER),
        "input": str(DATA_PATH),
        "output_dir": str(Path(run_dir) / "calls"),
        "base_url": BASE_URL,
        "model": "/model",
        "max_output_tokens": MAX_OUTPUT_TOKENS,
        "context_window_tokens": CONTEXT_TOKENS,
        "reservation_seconds": RESERVATION_SECONDS,
        "startup_ceiling_seconds": STARTUP_SECONDS,
        "cleanup_reserve_seconds": CLEANUP_SECONDS,
        "bound_files": list(BOUND_FILES),
    }


def wait_for_server(
    started,
    *,
    ceiling_seconds=STARTUP_SECONDS,
    deadline=None,
    clock=time.monotonic,
    opener=urllib.request.urlopen,
    sleeper=time.sleep,
):
    startup_deadline = started + ceiling_seconds
    if deadline is not None:
        startup_deadline = min(startup_deadline, deadline - CLEANUP_SECONDS)
    while True:
        now = clock()
        if now >= startup_deadline:
            raise TimeoutError("startup exceeded prospective ceiling")
        healthy = False
        try:
            timeout = max(0.01, min(2, startup_deadline - now))
            with opener(f"{BASE_URL}/health", timeout=timeout) as response:
                healthy = response.status == 200
        except OSError:
            pass
        if healthy:
            if clock() > startup_deadline:
                raise TimeoutError("startup exceeded prospective ceiling")
            return
        sleeper(min(1, max(0, startup_deadline - clock())))


def _snapshot(*, root=ROOT):
    return {relative: _sha256(Path(root) / relative) for relative in BOUND_FILES}


def prepare_execution(
    run_dir,
    *,
    data_path=DATA_PATH,
    preflight_path=PREFLIGHT_PATH,
    preview_path=PREVIEW_PATH,
    root=ROOT,
    container_name=None,
    command=run_owned,
):
    artifacts = validate_artifacts(
        data_path, preflight_path, preview_path, root=Path(root)
    )
    trunk_path = (
        Path(root) / "results/factorial-prep/current-trunk-hashes.json"
        if Path(root) != ROOT
        else TRUNK_HASHES_PATH
    )
    trunk = validate_trunk_hashes(trunk_path, root=Path(root))
    environment = qualify_environment(
        root=Path(root), container_name=container_name, command=command
    )
    return {
        "artifacts": artifacts,
        "trunk": trunk,
        "environment": environment,
        "run_dir": str(run_dir),
        "sha256": _snapshot(root=Path(root)),
    }


def _start_receipt(process, command, *, timeout):
    result = _communicate(process, timeout)
    return result, {
        "command": list(command),
        "pid": process.pid,
        "exit_code": result.returncode,
        "stdout_sha256": hashlib.sha256(result.stdout or b"").hexdigest(),
        "stderr_sha256": hashlib.sha256(result.stderr or b"").hexdigest(),
    }


def _remaining(deadline, clock, cap):
    return max(0.01, min(cap, deadline - clock()))


def _stop_client(process, timeout):
    if process.returncode is not None:
        return
    process.terminate()
    try:
        process.communicate(timeout=max(0.01, timeout))
    except subprocess.TimeoutExpired:
        process.kill()
        process.communicate(timeout=max(0.01, timeout))


def run_lifecycle(
    plan,
    *,
    run_flag,
    start=start_owned,
    wait_server=wait_for_server,
    clock=time.monotonic,
    wall_clock=time.time,
):
    """Run the already-qualified reservation and return (exit code, lifecycle)."""
    run = Path(plan["run_dir"])
    started = clock()
    deadline = started + plan["reservation_seconds"]
    lifecycle = {
        "schema_version": 1,
        "status": "STARTING",
        "started_unix": wall_clock(),
        "started_monotonic": started,
        "deadline_monotonic": deadline,
        "container": plan["container_name"],
        "cleaned": False,
    }
    _write_json(run / "container-command.json", plan["container_command"])
    _write_json(run / "lifecycle.json", lifecycle)
    exit_code = 2
    container_id = None
    container_attempted = False
    evidence_complete = True
    cleanup_receipts = []
    phase = "STARTUP"
    try:
        launch_started = wall_clock()
        process = start(
            plan["container_command"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        container_attempted = True
        try:
            result, receipt = _start_receipt(
                process,
                plan["container_command"],
                timeout=_remaining(
                    deadline, clock, plan["startup_ceiling_seconds"]
                ),
            )
        except subprocess.TimeoutExpired as exc:
            partial_stdout = exc.stdout or b""
            partial_stderr = exc.stderr or b""
            _stop_client(process, _remaining(deadline, clock, 5))
            if isinstance(partial_stdout, str):
                partial_stdout = partial_stdout.encode("utf-8", errors="replace")
            if isinstance(partial_stderr, str):
                partial_stderr = partial_stderr.encode("utf-8", errors="replace")
            _write_json(
                run / "server-launch.json",
                {
                    "command": plan["container_command"],
                    "pid": process.pid,
                    "started_unix": launch_started,
                    "ended_unix": wall_clock(),
                    "error": "TimeoutExpired: server container command",
                },
            )
            _write_bytes(
                run / "server-launch.log", partial_stdout + partial_stderr
            )
            raise TimeoutError(
                "server container command exceeded startup ceiling"
            ) from exc
        receipt.update(started_unix=launch_started, ended_unix=wall_clock())
        _write_json(run / "server-launch.json", receipt)
        _write_bytes(
            run / "server-launch.log",
            (result.stdout or b"") + (result.stderr or b"")
        )
        if result.returncode != 0:
            raise RuntimeError(f"server container command exited {result.returncode}")
        container_id = (result.stdout or b"").decode("utf-8", errors="replace").strip()
        if not container_id:
            raise RuntimeError("server container command returned no container ID")
        lifecycle.update(status="WAITING_FOR_SERVER", container_id=container_id)
        _write_json(run / "lifecycle.json", lifecycle)
        wait_server(
            started,
            ceiling_seconds=plan["startup_ceiling_seconds"],
            deadline=deadline,
            clock=clock,
        )
        remaining = math.floor(deadline - clock() - plan["cleanup_reserve_seconds"])
        if remaining <= 0:
            raise TimeoutError("no runtime reservation remains after cleanup reserve")
        driver_absolute_deadline = deadline - plan["cleanup_reserve_seconds"]
        phase = "DRIVER"
        driver = [
            str(ROOT / ".venv/bin/python"),
            plan["driver"],
            "--input", plan["input"],
            "--output-dir", plan["output_dir"],
            "--base-url", plan["base_url"],
            "--model", plan["model"],
            "--deadline-seconds", str(remaining),
        ]
        _write_json(run / "driver-command.json", driver)
        lifecycle.update(
            status="DRIVER_RUNNING",
            driver_deadline_seconds=remaining,
            driver_absolute_deadline_monotonic=driver_absolute_deadline,
        )
        _write_json(run / "lifecycle.json", lifecycle)
        driver_started = wall_clock()
        process = start(
            driver, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        try:
            result, receipt = _start_receipt(
                process,
                driver,
                timeout=_remaining(driver_absolute_deadline, clock, remaining),
            )
        except subprocess.TimeoutExpired as exc:
            partial_stdout = exc.stdout or b""
            partial_stderr = exc.stderr or b""
            _stop_client(process, _remaining(deadline, clock, 5))
            if isinstance(partial_stdout, str):
                partial_stdout = partial_stdout.encode("utf-8", errors="replace")
            if isinstance(partial_stderr, str):
                partial_stderr = partial_stderr.encode("utf-8", errors="replace")
            _write_json(
                run / "driver-exit.json",
                {
                    "command": driver,
                    "pid": process.pid,
                    "started_unix": driver_started,
                    "ended_unix": wall_clock(),
                    "error": "TimeoutExpired: owned runtime deadline",
                },
            )
            _write_bytes(run / "driver.log", partial_stdout + partial_stderr)
            raise TimeoutError("owned runtime exceeded its forwarded deadline") from exc
        receipt.update(started_unix=driver_started, ended_unix=wall_clock())
        _write_json(run / "driver-exit.json", receipt)
        _write_bytes(
            run / "driver.log",
            (result.stdout or b"") + (result.stderr or b"")
        )
        lifecycle["driver_exit_code"] = result.returncode
        if result.returncode in {0, 1, 2}:
            lifecycle["status"] = "DRIVER_EXITED"
            exit_code = result.returncode
        else:
            lifecycle.update(
                status="INCOMPLETE_DRIVER",
                error=f"unexpected driver exit code: {result.returncode}",
            )
            exit_code = 2
    except TimeoutError as exc:
        status = "INCOMPLETE_STARTUP" if phase == "STARTUP" else "INCOMPLETE_DRIVER"
        lifecycle.update(status=status, error=f"TimeoutError: {exc}")
        exit_code = 2
    except Exception as exc:
        lifecycle.update(
            status="INCOMPLETE_LIFECYCLE", error=f"{type(exc).__name__}: {exc}"
        )
        exit_code = 2
    finally:
        cleanup_owned = container_id is not None
        if container_attempted and not cleanup_owned:
            ownership_command = [
                "docker", "container", "inspect", "--format",
                '{{ index .Config.Labels "stencil.owner" }}',
                plan["container_name"],
            ]
            receipt = {"phase": "ownership_check", "command": ownership_command}
            if clock() >= deadline:
                receipt["error"] = "TimeoutError: lifecycle deadline exhausted"
                evidence_complete = False
            else:
                try:
                    process = start(
                        ownership_command,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )
                    result, process_receipt = _start_receipt(
                        process,
                        ownership_command,
                        timeout=_remaining(deadline, clock, 5),
                    )
                    receipt.update(process_receipt)
                    label = (result.stdout or b"").decode(
                        "utf-8", errors="replace"
                    ).strip()
                    expected_label = (
                        "coding-competence:" + plan["container_name"]
                    )
                    if result.returncode == 0 and label == expected_label:
                        cleanup_owned = True
                    elif result.returncode == 0:
                        receipt["ownership_error"] = "container label mismatch"
                        evidence_complete = False
                except Exception as exc:
                    receipt["error"] = f"{type(exc).__name__}: {exc}"
                    evidence_complete = False
            cleanup_receipts.append(receipt)
        if cleanup_owned:
            cleanup_commands = (
                ("logs", ["docker", "logs", plan["container_name"]], 10),
                ("stop", ["docker", "stop", "--time", "5", plan["container_name"]], 15),
                ("remove", ["docker", "rm", plan["container_name"]], 10),
            )
            removed = False
            for phase, command, cap in cleanup_commands:
                receipt = {"phase": phase, "command": command}
                if clock() >= deadline:
                    receipt["error"] = "TimeoutError: lifecycle deadline exhausted"
                    evidence_complete = False
                    cleanup_receipts.append(receipt)
                    continue
                try:
                    process = start(
                        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                    )
                    try:
                        result, process_receipt = _start_receipt(
                            process, command, timeout=_remaining(deadline, clock, cap)
                        )
                    except subprocess.TimeoutExpired:
                        _stop_client(process, _remaining(deadline, clock, 2))
                        raise
                    receipt.update(process_receipt)
                    if phase == "logs":
                        _write_bytes(
                            run / "server.log",
                            (result.stdout or b"") + (result.stderr or b"")
                        )
                    if phase == "remove" and result.returncode == 0:
                        removed = True
                    if result.returncode != 0:
                        evidence_complete = False
                except Exception as exc:
                    receipt["error"] = f"{type(exc).__name__}: {exc}"
                    evidence_complete = False
                cleanup_receipts.append(receipt)
            if not removed and clock() < deadline:
                command = ["docker", "rm", "-f", plan["container_name"]]
                receipt = {"phase": "force_remove", "command": command}
                try:
                    process = start(
                        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                    )
                    try:
                        result, process_receipt = _start_receipt(
                            process, command, timeout=_remaining(deadline, clock, 10)
                        )
                    except subprocess.TimeoutExpired:
                        _stop_client(process, _remaining(deadline, clock, 2))
                        raise
                    receipt.update(process_receipt)
                    removed = result.returncode == 0
                except Exception as exc:
                    receipt["error"] = f"{type(exc).__name__}: {exc}"
                cleanup_receipts.append(receipt)
            lifecycle["cleaned"] = removed
        elif not container_attempted or evidence_complete:
            lifecycle["cleaned"] = True
        _write_json(run / "cleanup-receipts.json", cleanup_receipts)
        ended = clock()
        lifecycle.update(
            ended_unix=wall_clock(),
            elapsed_seconds=ended - started,
            cleanup_evidence_complete=evidence_complete,
        )
        if ended > deadline:
            lifecycle["prior_status"] = lifecycle["status"]
            lifecycle["status"] = "BUDGET_EXCEEDED"
            exit_code = 2
        elif not lifecycle["cleaned"]:
            lifecycle["prior_status"] = lifecycle["status"]
            lifecycle["status"] = "CLEANUP_FAILED"
            exit_code = 2
        elif not evidence_complete:
            lifecycle["prior_status"] = lifecycle["status"]
            lifecycle["status"] = "EVIDENCE_INCOMPLETE"
            exit_code = 2
        _write_json(run / "lifecycle.json", lifecycle)
        if lifecycle["cleaned"]:
            Path(run_flag).unlink(missing_ok=True)
    return exit_code, lifecycle


def _reserve_flag(run, name):
    payload = json.dumps(
        {"pid": os.getpid(), "run_dir": str(run), "container": name},
        sort_keys=True,
    ) + "\n"
    descriptor = os.open(RUN_FLAG, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())


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
            "run-dir must be a run-* direct child of results/coding-competence"
        )
    plan = make_plan(run)
    if not args.execute:
        print(json.dumps(plan, ensure_ascii=True, indent=2, sort_keys=True))
        return 0

    register_pid(os.getpid())
    qualification = prepare_execution(run, container_name=plan["container_name"])
    review_handle = acquire_review_lock()
    try:
        _reserve_flag(run, plan["container_name"])
        try:
            run.mkdir(parents=False, exist_ok=False)
            plan["execute"] = True
            freeze = {
                "schema_version": 1,
                "kind": "coding-competence-original-freeze",
                "plan": plan,
                "qualification": qualification,
                "frozen_unix": time.time(),
            }
            _write_json(run / "freeze.json", freeze)
            recheck_resource_exclusivity(
                expected_head=qualification["environment"]["git_head"]
            )
            validate_trunk_hashes()
            if qualification["sha256"] != _snapshot():
                raise RuntimeError("a bound file changed after original freeze")
            code, _lifecycle = run_lifecycle(plan, run_flag=RUN_FLAG)
            return code
        except Exception:
            if run.exists():
                partial = {
                    "schema_version": 1,
                    "status": "INCOMPLETE_BEFORE_SERVER",
                    "ended_unix": time.time(),
                }
                _write_json(run / "lifecycle.json", partial)
            RUN_FLAG.unlink(missing_ok=True)
            raise
    finally:
        fcntl.flock(review_handle, fcntl.LOCK_UN)
        review_handle.close()


if __name__ == "__main__":
    sys.exit(main())
