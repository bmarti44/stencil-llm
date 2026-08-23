"""Registered Phase 3 matrix orchestration tests."""

from __future__ import annotations

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
