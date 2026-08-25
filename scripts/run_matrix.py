#!/usr/bin/env python3
"""Execute the registered 114-run Phase 3 matrix with exact resume semantics."""

from __future__ import annotations

import argparse
import fnmatch
import json
import shutil
import subprocess
import sys
import time
from collections import deque
from collections.abc import Callable, Sequence
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Protocol

from stencil import determinism as _determinism  # noqa: F401
from stencil.config import Config, GitIdentity, canonical_json, git_identity, run_id
from stencil.model import build_matched_configs


@dataclass(frozen=True)
class MatrixCell:
    key: str
    run_id: str
    config: Config | None


Launcher = Callable[[MatrixCell, Path, float, float], None]


class ChildProcess(Protocol):
    def poll(self) -> int | None: ...

    def terminate(self) -> None: ...

    def wait(self, timeout: float | None = None) -> int | None: ...

    def kill(self) -> None: ...


class StalledRun(RuntimeError):
    """A child stopped growing its metrics file and was terminated."""


class RunTimeout(RuntimeError):
    """A child exceeded its total runtime limit and was terminated."""

    def __init__(self, cell_key: str, elapsed: float, last_step: int | None) -> None:
        self.cell_key = cell_key
        self.elapsed = elapsed
        self.last_step = last_step
        super().__init__(
            f"{cell_key} exceeded total timeout after {elapsed:.3f}s; "
            f"last_step={last_step!r}"
        )


def _seeded(config: Config, seed: int) -> Config:
    return replace(
        config,
        seed_data=seed,
        seed_init=seed,
        seed_train=seed,
        seed_rules=0,
    )


def _task_a(config: Config, n: int, k: int, seed: int) -> Config:
    return replace(
        _seeded(config, seed),
        task="a",
        task_N=n,
        task_k=k,
        task_R=None,
        task_delay_min=None,
        task_delay_max=None,
        task_P=None,
        task_queries=None,
        task_placement=None,
        context_len=n + 4,
    )


def _task_m(config: Config, placement: str, seed: int) -> Config:
    gap = (
        config.n_layers * (config.window - 1) + 64
        if placement == "beyond_window"
        else 0
    )
    context_len = 2 * 32 + gap + 1 + 2 * 8
    return replace(
        _seeded(config, seed),
        task="m",
        task_N=None,
        task_k=None,
        task_R=None,
        task_delay_min=None,
        task_delay_max=None,
        task_P=32,
        task_queries=8,
        task_placement=placement,
        context_len=context_len,
    )


def matrix_cells(identity: GitIdentity | None = None) -> list[MatrixCell]:
    """Materialize the registered 84 Task-A plus 30 Task-M runs."""
    matched = build_matched_configs()
    cells: list[MatrixCell] = []
    for variant in matched:
        for seed in (0, 1, 2):
            for n, k in ((512, 8), (2048, 8), (2048, 32)):
                config = _task_a(matched[variant], n, k, seed)
                key = f"a:{variant}:N{n}:k{k}:s{seed}"
                cells.append(
                    MatrixCell(
                        key=key,
                        run_id=run_id(config, identity) if identity else "",
                        config=config,
                    )
                )
    for variant in ("b0_local", "m1", "m1b", "b2"):
        for seed in (0, 1, 2):
            config = _task_a(matched[variant], 128, 8, seed)
            key = f"a:{variant}:N128:k8:s{seed}"
            cells.append(
                MatrixCell(
                    key=key,
                    run_id=run_id(config, identity) if identity else "",
                    config=config,
                )
            )
    for variant in ("b0_full", "b0_local", "m1", "m1b", "b2"):
        for seed in (0, 1, 2):
            for placement in ("in_window", "beyond_window"):
                config = _task_m(matched[variant], placement, seed)
                key = f"m:{variant}:{placement}:s{seed}"
                cells.append(
                    MatrixCell(
                        key=key,
                        run_id=run_id(config, identity) if identity else "",
                        config=config,
                    )
                )
    if len(cells) != 114 or len({cell.key for cell in cells}) != 114:
        raise RuntimeError("registered matrix construction is not 114 unique runs")
    return cells


def execute_pending(
    cells: Sequence[MatrixCell],
    results_dir: Path,
    launcher: Launcher,
    *,
    timeout: float,
    jobs: int = 1,
    stagger: float = 120.0,
    stall_timeout: float = 1200.0,
    max_attempts: int = 3,
) -> dict[str, int | list[str]]:
    """Skip DONE runs and recreate interrupted run directories before launch."""
    if timeout <= 0:
        raise ValueError("timeout must be positive")
    if jobs < 1:
        raise ValueError("jobs must be positive")
    if stagger < 0:
        raise ValueError("stagger must be nonnegative")
    if stall_timeout <= 0:
        raise ValueError("stall_timeout must be positive")
    if max_attempts < 1:
        raise ValueError("max_attempts must be positive")
    results_dir.mkdir(parents=True, exist_ok=True)
    skipped = 0
    pending: list[tuple[MatrixCell, Path]] = []
    for cell in cells:
        if not cell.run_id:
            raise ValueError(f"cell {cell.key!r} has no resolved run_id")
        run_dir = results_dir / cell.run_id
        done = run_dir / "DONE"
        if done.is_file():
            skipped += 1
            continue
        if done.exists():
            raise RuntimeError(f"DONE marker is not a file: {done}")

        pending.append((cell, run_dir))

    def launch_pending(cell: MatrixCell, run_dir: Path) -> None:
        if run_dir.exists():
            safe_child = run_dir.parent.resolve() == results_dir.resolve()
            if not run_dir.is_dir() or not safe_child:
                raise RuntimeError(f"unsafe interrupted run path: {run_dir}")
            shutil.rmtree(run_dir)
        launcher(cell, run_dir, timeout, stall_timeout)

    attempts = {cell.key: 0 for cell, _ in pending}
    failed: list[str] = []

    def handle_failure(
        item: tuple[MatrixCell, Path], exc: Exception
    ) -> None:
        cell, _ = item
        will_retry = attempts[cell.key] < max_attempts
        if isinstance(exc, StalledRun) and will_retry:
            print(f"STALLED {cell.key}; requeued at back", flush=True)
        print(f"FAILED {cell.key}: {exc!r}", flush=True)
        if will_retry:
            queue.append(item)
        else:
            failed.append(cell.key)
            print(
                f"GIVING UP {cell.key} after {attempts[cell.key]} attempts",
                flush=True,
            )

    def handle_result(
        future: Future[None], item: tuple[MatrixCell, Path]
    ) -> None:
        try:
            future.result()
        except Exception as exc:
            handle_failure(item, exc)

    if jobs == 1:
        queue = deque(pending)
        while queue:
            item = queue.popleft()
            cell, run_dir = item
            attempts[cell.key] += 1
            try:
                launch_pending(cell, run_dir)
            except Exception as exc:
                handle_failure(item, exc)
    else:
        queue = deque(pending)
        in_flight: dict[Future[None], tuple[MatrixCell, Path]] = {}
        last_launch: float | None = None
        with ThreadPoolExecutor(max_workers=jobs) as pool:
            while queue or in_flight:
                while queue and len(in_flight) < jobs:
                    now = time.monotonic()
                    launch_delay = (
                        0.0
                        if last_launch is None
                        else max(0.0, stagger - (now - last_launch))
                    )
                    if launch_delay > 0:
                        break
                    item = queue.popleft()
                    attempts[item[0].key] += 1
                    future = pool.submit(launch_pending, *item)
                    in_flight[future] = item
                    last_launch = time.monotonic()

                if queue and len(in_flight) < jobs:
                    assert last_launch is not None
                    launch_delay = max(
                        0.0, stagger - (time.monotonic() - last_launch)
                    )
                    if not in_flight:
                        time.sleep(launch_delay)
                        continue
                    done, _ = wait(
                        in_flight,
                        timeout=launch_delay,
                        return_when=FIRST_COMPLETED,
                    )
                    for future in done:
                        item = in_flight.pop(future)
                        handle_result(future, item)
                    continue

                if in_flight:
                    done, _ = wait(in_flight, return_when=FIRST_COMPLETED)
                    for future in done:
                        item = in_flight.pop(future)
                        handle_result(future, item)
    return {"skipped": skipped, "launched": len(pending), "failed": failed}


def filter_cells(cells: Sequence[MatrixCell], only: str | None) -> list[MatrixCell]:
    if only is None:
        return list(cells)
    patterns = [item.strip() for item in only.split(",") if item.strip()]
    if not patterns:
        raise ValueError("--only requires at least one nonempty pattern")
    selected = [
        cell
        for cell in cells
        if any(fnmatch.fnmatchcase(cell.key, pattern) for pattern in patterns)
    ]
    if not selected:
        raise ValueError(f"--only matched no cells: {only}")
    return selected


def _stop_process(process: ChildProcess) -> None:
    process.terminate()
    try:
        process.wait(timeout=10.0)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


def _watch_process(
    process: ChildProcess,
    metrics_path: Path,
    *,
    cell_key: str,
    timeout: float,
    stall_timeout: float,
    poll_interval: float = 1.0,
) -> int:
    """Wait for a child while enforcing total-runtime and metrics-growth limits."""
    started = time.monotonic()
    last_growth = started
    last_size = metrics_path.stat().st_size if metrics_path.is_file() else 0
    while (returncode := process.poll()) is None:
        now = time.monotonic()
        size = metrics_path.stat().st_size if metrics_path.is_file() else 0
        if size > last_size:
            last_size = size
            last_growth = now
        if now - last_growth >= stall_timeout:
            _stop_process(process)
            raise StalledRun(f"metrics did not grow: {metrics_path}")
        if now - started >= timeout:
            _stop_process(process)
            last_step: int | None = None
            try:
                lines = metrics_path.read_text(encoding="utf-8").splitlines()
            except (OSError, UnicodeError):
                lines = []
            for line in reversed(lines):
                try:
                    candidate = json.loads(line).get("step")
                except (AttributeError, json.JSONDecodeError):
                    continue
                if type(candidate) is int:
                    last_step = candidate
                    break
            raise RunTimeout(cell_key, now - started, last_step)
        remaining = min(timeout - (now - started), stall_timeout - (now - last_growth))
        time.sleep(min(poll_interval, max(0.0, remaining)))
    return returncode


def _subprocess_launcher(
    root: Path, allow_dirty: bool, use_compiled_scan: bool
) -> Launcher:
    def launch(
        cell: MatrixCell,
        run_dir: Path,
        timeout: float,
        stall_timeout: float,
    ) -> None:
        if cell.config is None:
            raise ValueError("matrix cell has no config")
        config_path = root / "results" / f".matrix-{cell.run_id}.json"
        config_path.write_bytes(canonical_json(cell.config.as_dict()) + b"\n")
        command = [sys.executable, "-m", "stencil.train", str(config_path)]
        if allow_dirty:
            command.append("--allow-dirty")
        if use_compiled_scan:
            command.append("--compiled-scan")
        process: subprocess.Popen[bytes] | None = None
        try:
            process = subprocess.Popen(command, cwd=root)
            returncode = _watch_process(
                process,
                run_dir / "metrics.jsonl",
                cell_key=cell.key,
                timeout=timeout,
                stall_timeout=stall_timeout,
            )
            if returncode:
                raise subprocess.CalledProcessError(returncode, command)
        finally:
            if process is not None and process.poll() is None:
                _stop_process(process)
            config_path.unlink(missing_ok=True)
        if not (run_dir / "DONE").is_file():
            raise RuntimeError(f"run returned without DONE marker: {cell.key}")

    return launch


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", help="comma-separated exact or glob cell keys")
    parser.add_argument("--timeout", type=float, required=True, help="seconds per run")
    parser.add_argument(
        "--jobs", type=int, default=1, help="maximum concurrent run processes"
    )
    parser.add_argument(
        "--stagger", type=float, default=120.0, help="seconds between child launches"
    )
    parser.add_argument(
        "--stall-timeout",
        type=float,
        default=1200.0,
        help="seconds without metrics.jsonl growth before requeue",
    )
    parser.add_argument(
        "--max-attempts",
        type=int,
        default=3,
        help="maximum launch attempts per cell before giving up",
    )
    parser.add_argument("--allow-dirty", action="store_true")
    parser.add_argument("--compiled-scan", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    identity = git_identity(root)
    if identity.dirty and not args.allow_dirty:
        raise RuntimeError("dirty worktree requires --allow-dirty")
    cells = filter_cells(matrix_cells(identity), args.only)
    summary = execute_pending(
        cells,
        root / "results",
        _subprocess_launcher(root, args.allow_dirty, args.compiled_scan),
        timeout=args.timeout,
        jobs=args.jobs,
        stagger=args.stagger,
        stall_timeout=args.stall_timeout,
        max_attempts=args.max_attempts,
    )
    failed = summary["failed"]
    if not isinstance(failed, list):
        raise RuntimeError("execute_pending returned an invalid failed list")
    outcome = f"failed cells: {', '.join(failed)}" if failed else "all cells completed"
    print(
        f"launched={summary['launched']} skipped={summary['skipped']}; {outcome}",
        flush=True,
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
