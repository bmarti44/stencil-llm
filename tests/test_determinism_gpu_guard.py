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

    monkeypatch.setattr(determinism.subprocess, "run", lambda *a, **k: smi("2749844\n999\n"))
    with pytest.raises(RuntimeError, match="GPU busy"):
        determinism.assert_gpu_free_or_owned()


def test_nvidia_smi_failure_fails_closed(monkeypatch):
    monkeypatch.setattr(determinism.subprocess, "run", lambda *a, **k: smi("", returncode=9))
    with pytest.raises(RuntimeError, match="nvidia-smi"):
        determinism.assert_gpu_free_or_owned()
