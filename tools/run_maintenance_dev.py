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
BOUND_FILES = (
    "tools/run_maintenance_dev.py", "scripts/maintenance_dev_check.py",
    "src/stencil/focus/maintenance_updater.py", "src/stencil/focus/maintenance_bank.py",
    "src/stencil/focus/register.py", "src/stencil/focus/loop.py",
    "src/stencil/focus/renderer.py", "src/stencil/focus/journal.py",
    "results/factorial-prep/DEV-UPDATER-CHECK.md",
    "results/factorial-prep/kimi-dev-reviewed.json",
    "results/factorial-prep/current-trunk-hashes.json",
)
COLD_BOUND_FILES = BOUND_FILES + (
    "scripts/maintenance_cold_diagnostic.py",
    "results/factorial-prep/COLD-DIAGNOSTIC.md",
)


def command(args, **kwargs):
    kwargs.setdefault("timeout", 20)
    return subprocess.run(args, check=True, text=True, capture_output=True, **kwargs)


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument(
        "--mode", choices=("maintenance", "cold"), default="maintenance"
    )
    args = parser.parse_args(argv)
    run = args.run_dir.resolve()
    if run.parent != ROOT / "results/quick-checks":
        parser.error("run-dir must be a direct child of results/quick-checks")
    cold = args.mode == "cold"
    bound_files = COLD_BOUND_FILES if cold else BOUND_FILES
    driver_script = (
        "scripts/maintenance_cold_diagnostic.py"
        if cold
        else "scripts/maintenance_dev_check.py"
    )
    name = "stencil-maintenance-" + ("cold-" if cold else "dev-")
    name += uuid.uuid4().hex[:12]
    container_command = [
        "docker", "run", "--pull=never", "-d", "--name", name,
        "--device", "nvidia.com/gpu=0", "--ipc=host",
        "-p", "127.0.0.1:18088:8000", "-e", "VLLM_BATCH_INVARIANT=1",
        "-v", f"{ROOT}/models/qwen3-30b-a3b-hf:/model:ro", IMAGE,
        "--attention-backend", "TRITON_ATTN", "--model", "/model",
        "--dtype", "bfloat16", "--kv-cache-dtype", "auto",
        "--tensor-parallel-size", "1", "--max-model-len", "32768",
        "--max-num-seqs", "4", "--max-num-batched-tokens", "2048",
        "--gpu-memory-utilization", "0.70", "--enable-prefix-caching",
        "--generation-config", "vllm",
    ]
    plan = dict(container_command=container_command, gpu_held_ceiling_seconds=900,
                input=str(INPUT), output_dir=str(run / "calls"), model="/model",
                base_url="http://127.0.0.1:18088", max_tokens=1024,
                startup_ceiling_seconds=600, cleanup_reserve_seconds=60,
                mode=args.mode, driver=str(ROOT / driver_script),
                bound_files=list(bound_files))
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
        print(json.dumps({"phase": "waiting_for_server", "container": name}),
              flush=True)
        while True:
            if time.monotonic() - started >= 600:
                raise TimeoutError("startup exceeded prospective ceiling")
            try:
                with urllib.request.urlopen(
                    "http://127.0.0.1:18088/health", timeout=2
                ) as response:
                    if response.status == 200:
                        break
            except OSError:
                pass
            time.sleep(1)
        remaining = int(900 - (time.monotonic() - started) - 60)
        if remaining <= 0:
            raise TimeoutError("no remaining inference budget")
        driver = [
            str(ROOT / ".venv/bin/python"), str(ROOT / driver_script),
            "--input", str(INPUT), "--output-dir", str(run / "calls"),
            "--base-url", plan["base_url"], "--model", "/model",
            "--max-tokens", "1024", "--deadline-seconds", str(remaining),
        ]
        write_json(run / "driver-command.json", driver)
        print(json.dumps({"phase": "driver", "deadline_seconds": remaining}),
              flush=True)
        with (run / "driver.log").open("w") as log:
            # The ordinary stop is the driver's cooperative deadline. This
            # backstop can terminate only this direct child we just launched.
            result = subprocess.run(driver, cwd=ROOT, stdout=log,
                                    stderr=subprocess.STDOUT,
                                    timeout=remaining + 5)
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
                    forced = subprocess.run(["docker", "rm", "-f", name],
                                            capture_output=True, timeout=10)
                    lifecycle["force_remove_exit_code"] = forced.returncode
                    cleaned = forced.returncode == 0
                except Exception as exc:
                    lifecycle["force_remove_error"] = f"{type(exc).__name__}: {exc}"
        else:
            cleaned = True
        lifecycle.update(ended_unix=time.time(),
                         gpu_held_seconds=time.monotonic() - started,
                         cleaned=cleaned)
        if not cleaned:
            lifecycle["prior_status"] = lifecycle["status"]
            lifecycle["status"] = "CLEANUP_FAILED"
        elif lifecycle["gpu_held_seconds"] > 900:
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
