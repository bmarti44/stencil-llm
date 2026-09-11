#!/usr/bin/env python3
"""Own one bounded local serving lifecycle for the registered DEV updater check.

Dry run is the default. No imports launch a process or read a bank.
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IMAGE = (
    "vllm/vllm-openai@sha256:"
    "3dbe092ec5b2cef63b6104d33fa75d6ce53a7870962529ada69f78bbbc38e776"
)
INPUT = ROOT / "results/factorial-prep/kimi-dev-reviewed.json"
PROSE_INPUT = ROOT / "results/prose-maintenance/kimi-dev-reviewed.json"
CODING_INPUT = ROOT / "results/coding-self-cue/kimi-dev-reviewed.json"
CODING_PREVIEW = ROOT / "results/coding-self-cue/preview.json"
BOUND_FILES = (
    "tools/run_maintenance_dev.py",
    "scripts/maintenance_dev_check.py",
    "src/stencil/focus/maintenance_updater.py",
    "src/stencil/focus/maintenance_bank.py",
    "src/stencil/focus/register.py",
    "src/stencil/focus/loop.py",
    "src/stencil/focus/renderer.py",
    "src/stencil/focus/journal.py",
    "results/factorial-prep/DEV-UPDATER-CHECK.md",
    "results/factorial-prep/kimi-dev-reviewed.json",
    "results/factorial-prep/current-trunk-hashes.json",
)
COLD_BOUND_FILES = BOUND_FILES + (
    "scripts/maintenance_cold_diagnostic.py",
    "results/factorial-prep/COLD-DIAGNOSTIC.md",
)
PROSE_BOUND_FILES = (
    "tools/run_maintenance_dev.py",
    "scripts/prose_maintenance_dev.py",
    "scripts/maintenance_dev_check.py",
    "src/stencil/focus/maintenance_bank.py",
    "src/stencil/focus/register.py",
    "src/stencil/focus/loop.py",
    "results/factorial-prep/current-trunk-hashes.json",
    "results/prose-maintenance/PROTOCOL.md",
    "results/prose-maintenance/kimi-dev-reviewed.json",
)
SOURCE_READER_BOUND_FILES = (
    "tools/run_maintenance_dev.py",
    "scripts/source_reader_dev.py",
    "scripts/prose_maintenance_dev.py",
    "scripts/maintenance_dev_check.py",
    "src/stencil/focus/maintenance_updater.py",
    "src/stencil/focus/maintenance_bank.py",
    "src/stencil/focus/register.py",
    "src/stencil/focus/loop.py",
    "src/stencil/focus/renderer.py",
    "src/stencil/focus/journal.py",
    "results/factorial-prep/current-trunk-hashes.json",
    "results/source-reader/PROTOCOL.md",
    "results/source-reader/preview.json",
    "results/prose-maintenance/kimi-dev-reviewed.json",
)
CODING_BOUND_FILES = (
    "tools/run_maintenance_dev.py",
    "scripts/coding_self_cue_run.py",
    "scripts/coding_worker_dev.py",
    "src/stencil/focus/renderer.py",
    "src/stencil/focus/slab.py",
    "src/stencil/focus/slab_sandbox.py",
    "results/factorial-prep/current-trunk-hashes.json",
    "results/coding-self-cue/PROTOCOL.md",
    "results/coding-self-cue/kimi-dev-reviewed.json",
    "results/coding-self-cue/preview.json",
)


def command(args, **kwargs):
    kwargs.setdefault("timeout", 20)
    return subprocess.run(args, check=True, text=True, capture_output=True, **kwargs)


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def validate_coding_artifacts(input_path=CODING_INPUT, preview_path=CODING_PREVIEW):
    input_body = input_path.read_bytes()
    documents = json.loads(input_body)
    if type(documents) is not list or len(documents) != 4:
        raise RuntimeError("coding bank must contain exactly four episodes")
    episode_ids = [item["episode"]["episode_id"] for item in documents]
    if len(set(episode_ids)) != 4:
        raise RuntimeError("coding bank episode IDs must be unique")
    preview = json.loads(preview_path.read_bytes())
    if preview.get("kind") != "coding-self-cue-native-preview":
        raise RuntimeError("coding preview kind is invalid")
    if preview.get("model_calls") != 0:
        raise RuntimeError("coding preview must be CPU-only")
    if preview.get("later_actual_prompts_known") is not False:
        raise RuntimeError("coding preview must not claim later actual prompts")
    cold = preview.get("cold_prompts")
    if type(cold) is not list or len(cold) != 12:
        raise RuntimeError("coding preview must contain exactly 12 cold prompts")
    expected_cold = {
        (episode_id, 0, arm) for episode_id in episode_ids for arm in ("H", "C", "M")
    }
    observed_cold = {
        (item.get("episode_id"), item.get("round_index"), item.get("arm"))
        for item in cold
        if type(item) is dict and item.get("actual_cold_prompt") is True
    }
    if observed_cold != expected_cold or preview.get("actual_cold_prompt_count") != 12:
        raise RuntimeError("coding preview cold schedule is invalid")
    bounds = preview.get("conservative_context_bounds")
    if type(bounds) is not list or len(bounds) != 72:
        raise RuntimeError("coding preview must contain 72 context bounds")
    if sum(item.get("actual_prompt") is True for item in bounds) != 12:
        raise RuntimeError("coding preview mislabels later prompts as actual")
    if preview.get("all_context_bounds_eligible") is not True or not all(
        type(item.get("context_with_output_bound")) is int
        and item["context_with_output_bound"] <= 32_768
        for item in bounds
    ):
        raise RuntimeError("coding preview exceeds the context capacity")
    input_sha256 = hashlib.sha256(input_body).hexdigest()
    receipts = preview.get("inputs")
    if type(receipts) is not list or not any(
        type(item) is dict
        and item.get("sha256") == input_sha256
        and item.get("documents") == 4
        for item in receipts
    ):
        raise RuntimeError("coding preview is not bound to the reviewed bank")
    code_sha256 = preview.get("code_sha256")
    source_paths = CODING_BOUND_FILES[1:6]
    if type(code_sha256) is not dict or any(
        code_sha256.get(path) != hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
        for path in source_paths
    ):
        raise RuntimeError("coding preview is not bound to its source snapshot")
    return {
        "episodes": 4,
        "scheduled_calls": 72,
        "actual_cold_prompts": 12,
        "bank_sha256": input_sha256,
        "preview_sha256": hashlib.sha256(preview_path.read_bytes()).hexdigest(),
    }


def wait_for_server(
    started,
    *,
    ceiling_seconds=600,
    clock=time.monotonic,
    opener=urllib.request.urlopen,
    sleeper=time.sleep,
):
    while True:
        if clock() - started >= ceiling_seconds:
            raise TimeoutError("startup exceeded prospective ceiling")
        healthy = False
        try:
            with opener("http://127.0.0.1:18088/health", timeout=2) as response:
                healthy = response.status == 200
        except OSError:
            pass
        if healthy:
            if clock() - started > ceiling_seconds:
                raise TimeoutError("startup exceeded prospective ceiling")
            return
        sleeper(1)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument(
        "--mode",
        choices=("maintenance", "cold", "prose", "source-reader", "coding"),
        default="maintenance",
    )
    args = parser.parse_args(argv)
    run = args.run_dir.resolve()
    if run.parent != ROOT / "results/quick-checks":
        parser.error("run-dir must be a direct child of results/quick-checks")
    if args.mode == "cold":
        bound_files = COLD_BOUND_FILES
        driver_script = "scripts/maintenance_cold_diagnostic.py"
        input_path = INPUT
        name_prefix = "cold-"
    elif args.mode == "prose":
        bound_files = PROSE_BOUND_FILES
        driver_script = "scripts/prose_maintenance_dev.py"
        input_path = PROSE_INPUT
        name_prefix = "prose-"
    elif args.mode == "source-reader":
        bound_files = SOURCE_READER_BOUND_FILES
        driver_script = "scripts/source_reader_dev.py"
        input_path = PROSE_INPUT
        name_prefix = "source-reader-"
    elif args.mode == "coding":
        bound_files = CODING_BOUND_FILES
        driver_script = "scripts/coding_self_cue_run.py"
        input_path = CODING_INPUT
        name_prefix = "coding-"
    else:
        bound_files = BOUND_FILES
        driver_script = "scripts/maintenance_dev_check.py"
        input_path = INPUT
        name_prefix = "dev-"
    name = "stencil-maintenance-" + name_prefix
    name += uuid.uuid4().hex[:12]
    container_command = [
        "docker",
        "run",
        "--pull=never",
        "-d",
        "--name",
        name,
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
        "32768",
        "--max-num-seqs",
        "4",
        "--max-num-batched-tokens",
        "2048",
        "--gpu-memory-utilization",
        "0.70",
        "--enable-prefix-caching",
        "--generation-config",
        "vllm",
    ]
    if args.mode == "coding":
        gpu_held_ceiling_seconds = 3600
        max_tokens = 768
    elif args.mode == "source-reader":
        gpu_held_ceiling_seconds = 2700
        max_tokens = 1024
    else:
        gpu_held_ceiling_seconds = 900
        max_tokens = 1024
    plan = dict(
        container_command=container_command,
        gpu_held_ceiling_seconds=gpu_held_ceiling_seconds,
        input=str(input_path),
        output_dir=str(run / "calls"),
        model="/model",
        base_url="http://127.0.0.1:18088",
        max_tokens=max_tokens,
        startup_ceiling_seconds=600,
        cleanup_reserve_seconds=60,
        mode=args.mode,
        driver=str(ROOT / driver_script),
        bound_files=list(bound_files),
    )
    if not args.execute:
        print(json.dumps(plan, indent=2))
        return 0
    flags = list((ROOT / "results").rglob("RUNNING.flag"))
    if flags or command(["docker", "ps", "-q"]).stdout.strip():
        raise RuntimeError("another flag or container exists; coordinate before launch")
    gpu = command(["nvidia-smi", "--query-compute-apps=pid", "--format=csv,noheader"])
    if gpu.stdout.strip():
        raise RuntimeError("GPU compute process exists; coordinate before launch")
    command(["docker", "image", "inspect", IMAGE])
    weights = json.loads(
        (ROOT / "results/factorial-prep/current-trunk-hashes.json").read_text()
    )
    for item in weights["files"]:
        stat = (ROOT / item["path"]).stat()
        if (stat.st_size, stat.st_mtime_ns) != (item["bytes"], item["mtime_ns"]):
            raise RuntimeError("trunk file changed after CPU hash receipt")
    for rel in bound_files:
        command(["git", "-C", str(ROOT), "ls-files", "--error-unmatch", "--", rel])
        if command(["git", "-C", str(ROOT), "status", "--porcelain", "--", rel]).stdout:
            raise RuntimeError(f"bound file is not committed clean: {rel}")
    if args.mode == "coding":
        plan["coding_artifacts"] = validate_coding_artifacts()
    run.mkdir(parents=False, exist_ok=False)
    flag = run / "RUNNING.flag"
    flag.write_text(json.dumps({"pid": os.getpid(), "container": name}) + "\n")
    if any(p != flag for p in (ROOT / "results").rglob("RUNNING.flag")):
        flag.unlink()
        raise RuntimeError("another experiment reserved resources concurrently")
    with (ROOT / ".stencil-owned-pids").open("a") as registry:
        registry.write(str(os.getpid()) + "\n")
    started = time.monotonic()
    lifecycle = dict(started_unix=time.time(), status="STARTING", container=name)
    attempted = False
    cleaned = False
    try:
        plan["git_head"] = command(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"]
        ).stdout.strip()
        plan["sha256"] = {
            p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in bound_files
        }
        write_json(run / "freeze.json", plan)
        write_json(run / "lifecycle.json", lifecycle)
        attempted = True
        lifecycle["container_id"] = command(container_command).stdout.strip()
        print(
            json.dumps({"phase": "waiting_for_server", "container": name}), flush=True
        )
        wait_for_server(started, ceiling_seconds=plan["startup_ceiling_seconds"])
        remaining = int(gpu_held_ceiling_seconds - (time.monotonic() - started) - 60)
        if remaining <= 0:
            raise TimeoutError("no remaining inference budget")
        driver = [
            str(ROOT / ".venv/bin/python"),
            str(ROOT / driver_script),
            "--input",
            str(input_path),
            "--output-dir",
            str(run / "calls"),
            "--base-url",
            plan["base_url"],
            "--model",
            "/model",
            "--max-tokens",
            str(plan["max_tokens"]),
            "--deadline-seconds",
            str(remaining),
        ]
        write_json(run / "driver-command.json", driver)
        print(
            json.dumps({"phase": "driver", "deadline_seconds": remaining}), flush=True
        )
        with (run / "driver.log").open("w") as log:
            # The ordinary stop is the driver's cooperative deadline. This
            # backstop can terminate only this direct child we just launched.
            result = subprocess.run(
                driver,
                cwd=ROOT,
                stdout=log,
                stderr=subprocess.STDOUT,
                timeout=remaining + 5,
            )
        lifecycle.update(status="DRIVER_EXITED", driver_exit_code=result.returncode)
        return result.returncode
    except subprocess.TimeoutExpired as exc:
        lifecycle.update(status="INCOMPLETE_DEADLINE", error=str(exc))
        return 124
    except Exception as exc:
        lifecycle.update(status="ERROR", error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        if attempted:
            for phase, cmd, timeout in (
                ("logs", ["docker", "logs", name], 10),
                ("stop", ["docker", "stop", "--time", "5", name], 15),
                ("remove", ["docker", "rm", name], 10),
            ):
                try:
                    result = subprocess.run(cmd, capture_output=True, timeout=timeout)
                    lifecycle[phase + "_exit_code"] = result.returncode
                    if phase == "logs":
                        (run / "server.log").write_bytes(result.stdout + result.stderr)
                    if phase == "remove":
                        cleaned = result.returncode == 0
                except Exception as exc:
                    lifecycle[phase + "_error"] = f"{type(exc).__name__}: {exc}"
            if not cleaned:
                try:
                    forced = subprocess.run(
                        ["docker", "rm", "-f", name], capture_output=True, timeout=10
                    )
                    lifecycle["force_remove_exit_code"] = forced.returncode
                    cleaned = forced.returncode == 0
                except Exception as exc:
                    lifecycle["force_remove_error"] = f"{type(exc).__name__}: {exc}"
        else:
            cleaned = True
        lifecycle.update(
            ended_unix=time.time(),
            gpu_held_seconds=time.monotonic() - started,
            cleaned=cleaned,
        )
        if not cleaned:
            lifecycle["prior_status"] = lifecycle["status"]
            lifecycle["status"] = "CLEANUP_FAILED"
        elif lifecycle["gpu_held_seconds"] > gpu_held_ceiling_seconds:
            lifecycle["prior_status"] = lifecycle["status"]
            lifecycle["status"] = "BUDGET_EXCEEDED"
        write_json(run / "lifecycle.json", lifecycle)
        if cleaned:
            flag.unlink()
        print(json.dumps(lifecycle), flush=True)
        if not cleaned:
            return 125  # noqa: B012 - cleanup failure must override driver status
        if lifecycle["status"] == "BUDGET_EXCEEDED":
            return 124  # noqa: B012 - hard resource cap must override driver status


if __name__ == "__main__":
    sys.exit(main())
