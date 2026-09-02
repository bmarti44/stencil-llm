"""CPU tests for model-specific Qwen3 conversion plumbing."""

from pathlib import Path

from scripts.convert_qwen3 import ROOT, remap, resolve_paths
from stencil.qwen3 import Qwen3Config


def _cfg(tied: bool) -> Qwen3Config:
    return Qwen3Config(2, 4, 2, 4, 16, 32, 31, 10_000.0, 1e-6, 32, tied)


def test_model_selects_default_checkpoint_and_fixture() -> None:
    hf_dir, out, fixture = resolve_paths("4b", None, None)
    assert hf_dir == ROOT / "models/qwen3-4b-hf"
    assert out == ROOT / "models/qwen3-4b.pt"
    assert fixture == ROOT / "tests/fixtures/qwen3-4b_parity.pt"

    custom = Path("custom")
    assert resolve_paths("1.7b", custom, custom / "model.pt")[:2] == (
        custom,
        custom / "model.pt",
    )


def test_remap_tied_and_untied_lm_head() -> None:
    assert remap("lm_head.weight", _cfg(True)) is None
    assert remap("lm_head.weight", _cfg(False)) == "lm_head.weight"
    assert remap("model.layers.0.self_attn.q_proj.weight", _cfg(True)) == (
        "layers.0.q_proj.weight"
    )
