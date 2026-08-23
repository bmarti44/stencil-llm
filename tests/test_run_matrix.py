"""Registered Phase 3 matrix orchestration tests."""

from __future__ import annotations

import threading
from pathlib import Path

import pytest

from scripts.run_matrix import MatrixCell, execute_pending, matrix_cells


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

    def launcher(cell: MatrixCell, run_dir: Path, timeout: float) -> None:
        assert not run_dir.exists()
        assert timeout == 17.0
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

    def launcher(cell: MatrixCell, run_dir: Path, timeout: float) -> None:
        nonlocal active, peak_active, third_saw_completed
        assert timeout == 17.0
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
    )

    assert summary == {"skipped": 0, "launched": 3}
    assert peak_active == 2
    assert third_saw_completed
    assert set(completed) == {cell.key for cell in cells}
    assert all((tmp_path / cell.run_id / "DONE").is_file() for cell in cells)
