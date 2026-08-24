"""Registered Phase 3 matrix orchestration tests."""

from __future__ import annotations

import threading
import time
from pathlib import Path

import pytest

from scripts.run_matrix import (
    MatrixCell,
    _watch_process,
    execute_pending,
    matrix_cells,
)


def test_run_matrix_resume(tmp_path: Path) -> None:
    """Skip one DONE cell and recreate one interrupted cell from scratch."""
    done = tmp_path / "done-id"
    done.mkdir()
    (done / "DONE").touch()
    (done / "keep").write_text("complete", encoding="utf-8")
    interrupted = tmp_path / "interrupted-id"
    interrupted.mkdir()
    (interrupted / "partial").write_text("stale", encoding="utf-8")
    cells = [
        MatrixCell(key="done", run_id="done-id", config=None),
        MatrixCell(key="interrupted", run_id="interrupted-id", config=None),
    ]
    launched: list[str] = []

    def launcher(
        cell: MatrixCell, run_dir: Path, timeout: float, stall_timeout: float
    ) -> None:
        assert not run_dir.exists()
        assert timeout == 17.0
        assert stall_timeout == 1200.0
        launched.append(cell.key)
        run_dir.mkdir()
        (run_dir / "fresh").touch()

    summary = execute_pending(cells, tmp_path, launcher, timeout=17.0)

    assert summary == {"skipped": 1, "launched": 1}
    assert launched == ["interrupted"]
    assert (done / "keep").read_text(encoding="utf-8") == "complete"
    assert not (interrupted / "partial").exists()
    assert (interrupted / "fresh").is_file()


def test_registered_matrix_has_114_unique_runs() -> None:
    cells = matrix_cells()

    assert len(cells) == 114
    assert len({cell.key for cell in cells}) == 114
    assert sum(cell.config.task == "a" for cell in cells) == 84
    assert sum(cell.config.task == "m" for cell in cells) == 30


def test_run_matrix_rejects_nonpositive_timeout(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="timeout"):
        execute_pending([], tmp_path, lambda *_: None, timeout=0.0)
    with pytest.raises(ValueError, match="jobs"):
        execute_pending([], tmp_path, lambda *_: None, timeout=1.0, jobs=0)
    with pytest.raises(ValueError, match="stagger"):
        execute_pending([], tmp_path, lambda *_: None, timeout=1.0, stagger=-1.0)
    with pytest.raises(ValueError, match="stall_timeout"):
        execute_pending([], tmp_path, lambda *_: None, timeout=1.0, stall_timeout=0.0)


def test_run_matrix_bounded_pool_queues_and_completes(tmp_path: Path) -> None:
    """Two cells overlap; the third waits for a slot and all write DONE."""
    cells = [
        MatrixCell(key=f"cell-{index}", run_id=f"run-{index}", config=None)
        for index in range(3)
    ]
    barrier = threading.Barrier(2)
    lock = threading.Lock()
    active = 0
    peak_active = 0
    completed: list[str] = []
    third_saw_completed = False

    def launcher(
        cell: MatrixCell, run_dir: Path, timeout: float, stall_timeout: float
    ) -> None:
        nonlocal active, peak_active, third_saw_completed
        assert timeout == 17.0
        assert stall_timeout == 1200.0
        with lock:
            active += 1
            peak_active = max(peak_active, active)
            if cell.key == "cell-2":
                third_saw_completed = bool(completed)
        if cell.key != "cell-2":
            barrier.wait(timeout=2.0)
        run_dir.mkdir()
        (run_dir / "DONE").touch()
        with lock:
            completed.append(cell.key)
            active -= 1

    summary = execute_pending(
        cells,
        tmp_path,
        launcher,
        timeout=17.0,
        jobs=2,
        stagger=0.0,
    )

    assert summary == {"skipped": 0, "launched": 3}
    assert peak_active == 2
    assert third_saw_completed
    assert set(completed) == {cell.key for cell in cells}
    assert all((tmp_path / cell.run_id / "DONE").is_file() for cell in cells)


def test_run_matrix_staggers_concurrent_launches(tmp_path: Path) -> None:
    cells = [
        MatrixCell(key=f"cell-{index}", run_id=f"run-{index}", config=None)
        for index in range(2)
    ]
    launched_at: list[float] = []

    def launcher(
        cell: MatrixCell, run_dir: Path, timeout: float, stall_timeout: float
    ) -> None:
        launched_at.append(time.monotonic())
        run_dir.mkdir()
        (run_dir / "DONE").touch()

    summary = execute_pending(
        cells,
        tmp_path,
        launcher,
        timeout=1.0,
        jobs=2,
        stagger=0.05,
    )

    assert summary == {"skipped": 0, "launched": 2}
    assert launched_at[1] - launched_at[0] >= 0.04


def test_run_matrix_watchdog_kills_and_requeues_stall_at_back(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    class FakeProcess:
        def __init__(self) -> None:
            self.terminated = False
            self.killed = False

        def poll(self) -> None:
            return None

        def terminate(self) -> None:
            self.terminated = True

        def wait(self, timeout: float | None = None) -> None:
            if not self.terminated:
                raise TimeoutError

        def kill(self) -> None:
            self.killed = True

    class CompletingProcess(FakeProcess):
        def __init__(self, metrics_path: Path) -> None:
            super().__init__()
            self.metrics_path = metrics_path
            self.polls = 0

        def poll(self) -> int | None:
            self.polls += 1
            if self.polls == 1:
                self.metrics_path.write_text("progress\n", encoding="utf-8")
                return None
            return 0

    cells = [
        MatrixCell(key="stall", run_id="stall-id", config=None),
        MatrixCell(key="normal", run_id="normal-id", config=None),
    ]
    launches: list[str] = []
    stalled_process: FakeProcess | None = None
    normal_process: CompletingProcess | None = None

    def launcher(
        cell: MatrixCell, run_dir: Path, timeout: float, stall_timeout: float
    ) -> None:
        nonlocal normal_process, stalled_process
        launches.append(cell.key)
        run_dir.mkdir()
        if cell.key == "stall" and launches.count("stall") == 1:
            (run_dir / "metrics.jsonl").write_text("fixed\n", encoding="utf-8")
            stalled_process = FakeProcess()
            _watch_process(
                stalled_process,
                run_dir / "metrics.jsonl",
                timeout=timeout,
                stall_timeout=stall_timeout,
                poll_interval=0.001,
            )
        if cell.key == "normal":
            normal_process = CompletingProcess(run_dir / "metrics.jsonl")
            assert (
                _watch_process(
                    normal_process,
                    run_dir / "metrics.jsonl",
                    timeout=timeout,
                    stall_timeout=stall_timeout,
                    poll_interval=0.001,
                )
                == 0
            )
        (run_dir / "DONE").touch()

    summary = execute_pending(
        cells,
        tmp_path,
        launcher,
        timeout=1.0,
        jobs=1,
        stall_timeout=0.01,
    )

    assert summary == {"skipped": 0, "launched": 2}
    assert launches == ["stall", "normal", "stall"]
    assert stalled_process is not None
    assert stalled_process.terminated
    assert not stalled_process.killed
    assert normal_process is not None
    assert not normal_process.terminated
    assert "STALLED stall" in capsys.readouterr().out
    assert all((tmp_path / cell.run_id / "DONE").is_file() for cell in cells)
