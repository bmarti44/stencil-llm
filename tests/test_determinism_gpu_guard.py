from types import SimpleNamespace

import pytest

from stencil import determinism


def smi(stdout, returncode=0):
    return SimpleNamespace(stdout=stdout, stderr="", returncode=returncode)


def test_gpu_free_passes(monkeypatch):
    monkeypatch.delenv("STENCIL_GPU_OWNER", raising=False)
    monkeypatch.setattr(determinism.subprocess, "run", lambda *a, **k: smi(""))
    determinism.assert_gpu_free_or_owned()


def test_gpu_busy_without_matching_owner_raises(monkeypatch):
    monkeypatch.delenv("STENCIL_GPU_OWNER", raising=False)
    monkeypatch.setattr(determinism.subprocess, "run", lambda *a, **k: smi("2749844\n"))
    with pytest.raises(RuntimeError, match="GPU busy"):
        determinism.assert_gpu_free_or_owned()

    monkeypatch.setenv("STENCIL_GPU_OWNER", "123")
    with pytest.raises(RuntimeError, match="GPU busy"):
        determinism.assert_gpu_free_or_owned()


def test_gpu_busy_with_exact_owner_passes_but_other_apps_fail(monkeypatch):
    monkeypatch.setenv("STENCIL_GPU_OWNER", "2749844")
    monkeypatch.setattr(determinism.subprocess, "run", lambda *a, **k: smi("2749844\n"))
    determinism.assert_gpu_free_or_owned()

    monkeypatch.setattr(
        determinism.subprocess, "run", lambda *a, **k: smi("2749844\n999\n")
    )
    with pytest.raises(RuntimeError, match="GPU busy"):
        determinism.assert_gpu_free_or_owned()


def test_nvidia_smi_failure_fails_closed(monkeypatch):
    monkeypatch.setattr(
        determinism.subprocess, "run", lambda *a, **k: smi("", returncode=9)
    )
    with pytest.raises(RuntimeError, match="nvidia-smi"):
        determinism.assert_gpu_free_or_owned()


def test_shared_mode_allows_only_reserved_or_declared_pids(monkeypatch, tmp_path):
    reservations = tmp_path / "res"
    reservations.write_text('{"name":"peer","pid":4152283,"peak_gb":12}\n')
    monkeypatch.setattr(determinism, "RESERVATIONS", reservations)
    monkeypatch.delenv("STENCIL_GPU_OWNER", raising=False)
    monkeypatch.delenv("STENCIL_GPU_FOREIGN_PIDS", raising=False)
    monkeypatch.setattr(
        determinism.subprocess, "run", lambda *a, **k: smi("4152283\n777\n")
    )
    # exclusive default still denies
    monkeypatch.delenv("STENCIL_GPU_SHARE", raising=False)
    with pytest.raises(RuntimeError, match="GPU busy"):
        determinism.assert_gpu_free_or_owned()
    monkeypatch.setenv("STENCIL_GPU_SHARE", "1")
    with pytest.raises(RuntimeError, match="unreserved compute pid\\(s\\) 777"):
        determinism.assert_gpu_free_or_owned()
    monkeypatch.setenv("STENCIL_GPU_FOREIGN_PIDS", "777")
    determinism.assert_gpu_free_or_owned()
    monkeypatch.delenv("STENCIL_GPU_FOREIGN_PIDS")
    monkeypatch.setattr(determinism.subprocess, "run", lambda *a, **k: smi("4152283\n"))
    determinism.assert_gpu_free_or_owned()


def test_shared_mode_accepts_descendants_of_reserved_pids(monkeypatch, tmp_path):
    reservations = tmp_path / "res"
    reservations.write_text('{"name":"peer","pid":100,"peak_gb":12}\n')
    monkeypatch.setattr(determinism, "RESERVATIONS", reservations)
    monkeypatch.setattr(
        determinism, "_ancestors", lambda pid: {100, 101} if pid == 102 else set()
    )
    monkeypatch.delenv("STENCIL_GPU_OWNER", raising=False)
    monkeypatch.delenv("STENCIL_GPU_FOREIGN_PIDS", raising=False)
    monkeypatch.setenv("STENCIL_GPU_SHARE", "1")
    monkeypatch.setattr(determinism.subprocess, "run", lambda *a, **k: smi("102\n"))
    determinism.assert_gpu_free_or_owned()
    monkeypatch.setattr(
        determinism.subprocess, "run", lambda *a, **k: smi("102\n300\n")
    )
    with pytest.raises(RuntimeError, match="unreserved compute pid\\(s\\) 300"):
        determinism.assert_gpu_free_or_owned()


def test_shared_mode_accepts_session_members_of_reserved_pids(monkeypatch, tmp_path):
    reservations = tmp_path / "res"
    reservations.write_text('{"name":"peer","pid":100,"peak_gb":12}\n')
    monkeypatch.setattr(determinism, "RESERVATIONS", reservations)
    monkeypatch.setattr(determinism, "_ancestors", lambda pid: set())
    monkeypatch.setattr(
        determinism, "_session_of", lambda pid: {102: 100, 300: 300}.get(pid)
    )
    monkeypatch.delenv("STENCIL_GPU_OWNER", raising=False)
    monkeypatch.delenv("STENCIL_GPU_FOREIGN_PIDS", raising=False)
    monkeypatch.setenv("STENCIL_GPU_SHARE", "1")
    monkeypatch.setattr(determinism.subprocess, "run", lambda *a, **k: smi("102\n"))
    determinism.assert_gpu_free_or_owned()
    monkeypatch.setattr(
        determinism.subprocess, "run", lambda *a, **k: smi("102\n300\n")
    )
    with pytest.raises(RuntimeError, match="unreserved compute pid\\(s\\) 300"):
        determinism.assert_gpu_free_or_owned()
