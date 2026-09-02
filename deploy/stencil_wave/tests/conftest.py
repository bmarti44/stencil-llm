"""Shared fixtures. Two optional environments:

STENCIL_REPO       path to the research repo (src/stencil + models/qwen3-1.7b.pt
                   + results/qwen/b3-ce-s0.pt); the parity tests need it.
STENCIL_WAVE_MODEL HF id or local snapshot path for the HF side
                   (default Qwen/Qwen3-1.7B at the pinned revision).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

REPO = os.environ.get("STENCIL_REPO")
HF_MODEL = os.environ.get("STENCIL_WAVE_MODEL", "Qwen/Qwen3-1.7B")


def repo_path() -> Path | None:
    if not REPO:
        return None
    p = Path(REPO)
    if not (p / "src" / "stencil").is_dir():
        return None
    if str(p / "src") not in sys.path:
        sys.path.insert(0, str(p / "src"))
    return p


@pytest.fixture(scope="session")
def repo():
    p = repo_path()
    if p is None:
        pytest.skip("STENCIL_REPO not set (research repo needed)")
    return p


@pytest.fixture(scope="session")
def hf_tokenizer():
    from stencil_wave.model import MODEL_ID, REVISION
    from transformers import AutoTokenizer
    kw = {"revision": REVISION} if HF_MODEL == MODEL_ID else {}
    try:
        return AutoTokenizer.from_pretrained(HF_MODEL, **kw)
    except Exception as exc:  # offline / not downloaded
        pytest.skip(f"tokenizer unavailable: {exc.__class__.__name__}")
