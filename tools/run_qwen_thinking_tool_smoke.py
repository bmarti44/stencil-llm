#!/usr/bin/env python3
"""Own one bounded Qwen thinking/tool smoke lifecycle; dry-run by default."""

import argparse
import fcntl
import hashlib
import json
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import qwen_thinking_tool_smoke as smoke  # noqa: E402
from tools import run_coding_competence as owned  # noqa: E402

RESULTS_DIR = ROOT / "results/coding-reasoning-smoke"
PREVIEW_PATH = RESULTS_DIR / "preview.json"
REVIEW_PATH = RESULTS_DIR / "review-astra.md"
TRUNK_HASHES_PATH = ROOT / "results/factorial-prep/current-trunk-hashes.json"
RUN_FLAG = RESULTS_DIR / "RUNNING.flag"
REVIEW_LOCK = ROOT / ".review.lock"
DRIVER = ROOT / "scripts/qwen_thinking_tool_smoke.py"
IMAGE = owned.IMAGE
BASE_URL = "http://127.0.0.1:18088"
RESERVATION_SECONDS = 1200
STARTUP_SECONDS = 600
CLEANUP_SECONDS = 60

TRACKED_BOUND_FILES = (
    "scripts/qwen_thinking_tool_smoke.py",
    "tests/test_qwen_thinking_tool_smoke.py",
    "tools/run_qwen_thinking_tool_smoke.py",
    "tests/test_run_qwen_thinking_tool_smoke.py",
    "scripts/coding_competence_run.py",
    "scripts/coding_competence_dev.py",
    "scripts/coding_worker_dev.py",
    "src/stencil/focus/slab.py",
    "src/stencil/focus/slab_sandbox.py",
    "tools/run_coding_competence.py",
    "results/coding-reasoning-smoke/BRIEF.md",
    "results/coding-reasoning-smoke/RESOURCE-PLAN.md",
    "results/coding-reasoning-smoke/review-astra.md",
    "results/coding-reasoning-smoke/preview.json",
    "results/factorial-prep/current-trunk-hashes.json",
)
MODEL_METADATA_FILES = smoke.TOKENIZER_FILES


def _sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _read_json(path, label):
    try:
        return json.loads(Path(path).read_bytes())
    except Exception as exc:
        raise RuntimeError(f"{label} is not readable JSON: {exc}") from exc


def _snapshot(relative_paths, *, root=ROOT):
    return {
        relative: _sha256(Path(root) / relative) for relative in relative_paths
    }


def _container_command(name):
    reasoning_config = json.dumps(
        {
            "reasoning_start_str": "<think>",
            "reasoning_end_str": "</think>",
        },
        separators=(",", ":"),
    )
    return [
        "docker",
        "run",
        "--pull=never",
        "-d",
        "--name",
        name,
        "--label",
        f"stencil.owner=coding-competence:{name}",
        "--device",
        "nvidia.com/gpu=0",
        "--ipc=host",
        "-p",
        "127.0.0.1:18088:8000",
        "-e",
        "VLLM_BATCH_INVARIANT=1",
        "-v",
        f"{ROOT}/models/qwen3-30b-a3b-hf:/model:ro",
        IMAGE,
        "--attention-backend",
        "TRITON_ATTN",
        "--model",
        "/model",
        "--dtype",
        "bfloat16",
        "--kv-cache-dtype",
        "auto",
        "--tensor-parallel-size",
        "1",
        "--max-model-len",
        str(smoke.CONTEXT_TOKENS),
        "--max-num-seqs",
        "1",
        "--max-num-batched-tokens",
        str(smoke.MAX_OUTPUT_TOKENS),
        "--gpu-memory-utilization",
        "0.70",
        "--enable-prefix-caching",
        "--generation-config",
        "vllm",
        "--enable-auto-tool-choice",
        "--tool-call-parser",
        "hermes",
        "--reasoning-parser",
        "qwen3",
        "--reasoning-config",
        reasoning_config,
    ]


def make_plan(run_dir, *, container_name=None):
    if container_name is None:
        container_name = "stencil-qwen-thinking-tool-" + uuid.uuid4().hex[:12]
    run = Path(run_dir)
    return {
        "schema_version": 1,
        "kind": "qwen-thinking-tool-smoke-launch-plan",
        "execute": False,
        "run_dir": str(run),
        "container_name": container_name,
        "container_command": _container_command(container_name),
        "driver": str(DRIVER),
        "input": smoke.FIXTURE_ID,
        "output_dir": str(run / "calls"),
        "base_url": BASE_URL,
        "model": "/model",
        "max_output_tokens": smoke.MAX_OUTPUT_TOKENS,
        "thinking_token_budget": smoke.THINKING_TOKEN_BUDGET,
        "context_window_tokens": smoke.CONTEXT_TOKENS,
        "maximum_model_calls": smoke.MAX_CALLS,
        "reservation_seconds": RESERVATION_SECONDS,
        "startup_ceiling_seconds": STARTUP_SECONDS,
        "cleanup_reserve_seconds": CLEANUP_SECONDS,
        "tracked_bound_files": list(TRACKED_BOUND_FILES),
        "model_metadata_files": list(MODEL_METADATA_FILES),
        "preview_command": [
            str(ROOT / ".venv/bin/python"),
            str(DRIVER),
            "--input",
            smoke.FIXTURE_ID,
            "--preview",
        ],
    }


def validate_preview(path=PREVIEW_PATH, *, root=ROOT):
    preview = _read_json(path, "smoke preview")
    required = {
        "schema_version": 1,
        "kind": "qwen-thinking-tool-smoke-preview",
        "status": "PASS",
        "model_calls": 0,
        "fixture": smoke._fixture_receipt(),
        "reservation_seconds": RESERVATION_SECONDS,
        "startup_ceiling_seconds": STARTUP_SECONDS,
        "cleanup_reserve_seconds": CLEANUP_SECONDS,
        "authoritative_render_required_before_each_generation": True,
        "termination_cause_claimed": False,
        "semantic_competence_claimed": False,
    }
    for key, expected in required.items():
        if preview.get(key) != expected:
            raise RuntimeError(f"preview field {key} is not qualified")
    settings = preview.get("settings")
    expected_settings = {
        "model": "/model",
        "calls": smoke.MAX_CALLS,
        "render_requests": smoke.MAX_CALLS,
        "generation_requests": smoke.MAX_CALLS,
        "max_output_tokens": smoke.MAX_OUTPUT_TOKENS,
        "thinking_token_budget": smoke.THINKING_TOKEN_BUDGET,
        "context_tokens": smoke.CONTEXT_TOKENS,
        "temperature": smoke.TEMPERATURE,
        "top_p": smoke.TOP_P,
        "top_k": smoke.TOP_K,
        "min_p": smoke.MIN_P,
        "seed": smoke.SEED,
        "stream": False,
        "enable_thinking": True,
        "forced_tool": "replace_function",
    }
    if settings != expected_settings:
        raise RuntimeError("preview settings are not the fixed smoke settings")
    boundaries = preview.get("reasoning_boundaries")
    start_id, end_id = smoke._boundary_ids()
    if boundaries != {
        "start": "<think>",
        "start_token_id": start_id,
        "end": "</think>",
        "end_token_id": end_id,
        "prompt_boundaries_expected": False,
    }:
        raise RuntimeError("preview reasoning boundaries are not qualified")
    cold = preview.get("cold_request")
    if (
        type(cold) is not dict
        or cold.get("local_count_is_native_prompt_tokens") is not False
        or cold.get("provisionally_fits_context") is not True
        or cold.get("request_body_sha256")
        != hashlib.sha256(cold.get("request_body", "").encode("utf-8")).hexdigest()
    ):
        raise RuntimeError("preview cold request is not qualified")
    expected_hashes = {
        relative: _sha256(Path(root) / relative) for relative in smoke.SOURCE_FILES
    }
    if preview.get("code_sha256") != expected_hashes:
        raise RuntimeError("preview source hashes are stale")
    return {
        "preview_sha256": _sha256(path),
        "fixture_sha256": preview["fixture"]["sha256"],
        "cold_local_tokens": cold["local_serialized_request_tokens"],
    }


def validate_review(path=REVIEW_PATH):
    path = Path(path)
    if not path.is_file():
        raise RuntimeError("independent readiness review is absent")
    return {"review_sha256": _sha256(path)}


def _tracked_clean(relative, *, root=ROOT, command=owned.run_owned):
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
    if owned._text(status).strip():
        raise RuntimeError(f"bound file is dirty or untracked: {relative}")


def qualify_environment(*, root=ROOT, container_name, command=owned.run_owned):
    flags = owned._active_flags(root)
    if flags:
        raise RuntimeError(f"active run flag exists: {flags[0]}")
    if owned._active_review_lock(Path(root) / ".review.lock"):
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
        ["docker", "image", "inspect", IMAGE],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    for relative in TRACKED_BOUND_FILES:
        _tracked_clean(relative, root=Path(root), command=command)
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


def prepare_execution(run_dir, *, root=ROOT, container_name, command=owned.run_owned):
    root = Path(root)
    preview_path = root / PREVIEW_PATH.relative_to(ROOT)
    review_path = root / REVIEW_PATH.relative_to(ROOT)
    trunk_path = root / TRUNK_HASHES_PATH.relative_to(ROOT)
    preview = validate_preview(preview_path, root=root)
    review = validate_review(review_path)
    trunk = owned.validate_trunk_hashes(trunk_path, root=root)
    environment = qualify_environment(
        root=root, container_name=container_name, command=command
    )
    return {
        "preview": preview,
        "review": review,
        "trunk": trunk,
        "environment": environment,
        "run_dir": str(run_dir),
        "tracked_sha256": _snapshot(TRACKED_BOUND_FILES, root=root),
        "model_metadata_sha256": _snapshot(MODEL_METADATA_FILES, root=root),
    }


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
        raise RuntimeError("local model metadata changed after original freeze")
    owned.validate_trunk_hashes()


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
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--preview", action="store_true")
    return parser


def main(argv=None):
    args = _parser().parse_args(argv)
    if args.preview:
        if args.execute or args.run_dir is not None:
            raise ValueError("--preview cannot be combined with execution or run-dir")
        result = smoke.preview(model="/model")
        print(json.dumps(result, ensure_ascii=True, indent=2, sort_keys=True))
        return 0 if result["status"] == "PASS" else 2
    if args.run_dir is None:
        raise ValueError("--run-dir is required unless --preview is used")
    run = args.run_dir.resolve()
    if run.parent != RESULTS_DIR or not run.name.startswith("run-"):
        raise ValueError(
            "run-dir must be a run-* direct child of results/coding-reasoning-smoke"
        )
    plan = make_plan(run)
    if not args.execute:
        print(json.dumps(plan, ensure_ascii=True, indent=2, sort_keys=True))
        return 0

    owned.register_pid(os.getpid())
    qualification = prepare_execution(
        run, container_name=plan["container_name"]
    )
    review_handle = owned.acquire_review_lock(REVIEW_LOCK)
    try:
        _reserve_flag(run, plan["container_name"])
        run_created = False
        try:
            run.mkdir(parents=False, exist_ok=False)
            run_created = True
            plan["execute"] = True
            freeze = {
                "schema_version": 1,
                "kind": "qwen-thinking-tool-smoke-freeze",
                "plan": plan,
                "qualification": qualification,
                "frozen_unix": time.time(),
            }
            owned._write_json(run / "freeze.json", freeze)
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
