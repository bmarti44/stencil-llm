"""Observe one registered FIT supervisor and its owned process group."""

import argparse
import hashlib
import json
import os
import signal
import subprocess
import time
from pathlib import Path


def write_json(path, value):
    temporary = path.with_name(path.name + ".tmp")
    with temporary.open("w") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def register(pid, registry):
    with registry.open("a") as stream:
        stream.write(str(pid) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def group_alive(pid):
    try:
        os.killpg(pid, 0)
        return True
    except ProcessLookupError:
        return False


def stop_group(child):
    # This group was created by this observer's own Popen below.
    if group_alive(child.pid):
        os.killpg(child.pid, signal.SIGTERM)
    try:
        child.wait(timeout=2)
    except subprocess.TimeoutExpired:
        pass
    if group_alive(child.pid):
        os.killpg(child.pid, signal.SIGKILL)
    child.wait(timeout=10)


def observe(plan):
    settings = plan["outer_observer"]
    root, run = Path(plan["cwd"]), Path(plan["run_dir"])
    receipt_path = Path(settings["receipt"])
    if receipt_path.exists() or run.exists():
        raise RuntimeError("observer receipt or run directory already exists")
    registry = root / ".stencil-owned-pids"
    register(os.getpid(), registry)
    child = None
    receipt = {
        "status": "STARTING",
        "observer_pid": os.getpid(),
        "command": plan["command"],
        "initial_training_observation": None,
    }
    started = time.monotonic()
    receipt.update(started_monotonic=started, started_unix=time.time())
    initial_deadline = started + settings["initial_training_seconds"]
    whole_deadline = started + settings["whole_process_seconds"]
    receipt.update(
        initial_deadline_monotonic=initial_deadline,
        whole_deadline_monotonic=whole_deadline,
    )
    try:
        write_json(receipt_path, receipt)
        child = subprocess.Popen(
            plan["command"], cwd=root, stdin=subprocess.DEVNULL, start_new_session=True
        )
        register(child.pid, registry)
        receipt.update(
            status="RUNNING", supervisor_pid=child.pid, owned_process_group=child.pid
        )
        write_json(receipt_path, receipt)
        while child.poll() is None:
            now = time.monotonic()
            initial_pending = receipt["initial_training_observation"] is None
            deadline = (
                min(initial_deadline, whole_deadline)
                if initial_pending
                else whole_deadline
            )
            if now >= deadline:
                receipt["status"] = (
                    "INCOMPLETE_INITIAL_TIMEOUT"
                    if initial_pending
                    else "INCOMPLETE_WHOLE_TIMEOUT"
                )
                stop_group(child)
                break
            if initial_pending:
                try:
                    stage = json.loads((run / "current-stage.json").read_bytes())
                except (OSError, ValueError):
                    stage = None
                observed = time.monotonic()
                # Check again AFTER reading, before accepting a durable transition.
                if observed >= deadline:
                    continue
                if (
                    stage
                    and stage.get("stage") in {"generation-base", "generation-adapter"}
                    and stage.get("status") in {"INTENT", "COMPLETION_PENDING"}
                ):
                    receipt["initial_training_observation"] = {
                        "observed_monotonic": observed,
                        "elapsed_seconds": observed - started,
                        "stage": stage,
                    }
                    write_json(receipt_path, receipt)
            try:
                child.wait(
                    timeout=max(
                        0, min(settings["poll_seconds"], deadline - time.monotonic())
                    )
                )
            except subprocess.TimeoutExpired:
                pass
        if group_alive(child.pid):
            receipt["status"] = "INCOMPLETE_OWNED_GROUP_REMAINS"
            stop_group(child)
        ended = time.monotonic()
        receipt.update(
            ended_monotonic=ended,
            ended_unix=time.time(),
            elapsed_seconds=ended - started,
            supervisor_exit_code=child.returncode,
            supervisor_exit_confirmed=child.poll() is not None,
            owned_group_absent=not group_alive(child.pid),
        )
        initial_bounded = (
            receipt["initial_training_observation"] is not None
            or ended <= initial_deadline
        )
        receipt["initial_training_bound_observed"] = initial_bounded
        if receipt["status"] == "RUNNING":
            lifecycle = json.loads((run / "lifecycle.json").read_bytes())
            receipt["inner_lifecycle"] = lifecycle
            passed = (
                child.returncode == 0
                and lifecycle.get("status") == "COMPLETE"
                and lifecycle.get("child_exit_confirmed") is True
                and initial_bounded
                and ended <= whole_deadline
                and receipt["owned_group_absent"]
            )
            receipt["status"] = (
                "COMPLETE_UNREVIEWED" if passed else "INCOMPLETE_TERMINAL"
            )
    except BaseException as exc:
        receipt.update(
            status="INCOMPLETE_OBSERVER_ERROR", error=f"{type(exc).__name__}: {exc}"
        )
        if child is not None:
            stop_group(child)
        receipt.update(
            ended_monotonic=time.monotonic(),
            ended_unix=time.time(),
            elapsed_seconds=time.monotonic() - started,
        )
    finally:
        write_json(receipt_path, receipt)
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    plan = json.loads(args.plan.read_bytes())
    for relative, binding in plan["bindings"].items():
        body = (Path(plan["cwd"]) / relative).read_bytes()
        if (
            hashlib.sha256(body).hexdigest() != binding["sha256"]
            or len(body) != binding["bytes"]
        ):
            raise RuntimeError(f"changed launch binding: {relative}")
    if not args.execute:
        print("PASS: launch bindings checked; no process launched")
        return 0
    if plan["status"] != "FROZEN_READY" or not plan.get("accepted_code_review"):
        raise RuntimeError("launch plan is not accepted and frozen")
    result = observe(plan)
    print(
        json.dumps(
            {
                key: result.get(key)
                for key in (
                    "status",
                    "elapsed_seconds",
                    "supervisor_pid",
                    "supervisor_exit_code",
                )
            }
        )
    )
    return 0 if result["status"] == "COMPLETE_UNREVIEWED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
