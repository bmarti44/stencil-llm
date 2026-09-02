# ruff: noqa: E501
"""QWEN-PLAN P0 verifications: bitwise parity fixture + determinism."""
from pathlib import Path

import pytest
import torch

from stencil import determinism  # noqa: F401
from stencil.qwen3 import Qwen3

ROOT = Path(__file__).resolve().parent.parent
WEIGHTS = ROOT / "models" / "qwen3-1.7b.pt"
FIXTURE = ROOT / "tests" / "fixtures" / "qwen3_parity.pt"

needs_weights = pytest.mark.skipif(
    not WEIGHTS.exists() or not torch.cuda.is_available(),
    reason="needs converted weights and GPU",
)


def _load() -> Qwen3:
    model = Qwen3()
    sd = torch.load(WEIGHTS, map_location="cpu")
    missing, unexpected = model.load_state_dict(sd, strict=False)
    assert not missing and not unexpected
    return model.to(torch.bfloat16).cuda().eval()


@needs_weights
def test_qwen3_parity_bitwise() -> None:
    model = _load()
    captured = torch.load(FIXTURE, map_location="cpu")
    assert len(captured) == 8
    with torch.no_grad():
        for entry in captured.values():
            ids = torch.tensor([entry["ids"]], device="cuda")
            ours = model(ids)[0, -1].float().cpu()
            assert torch.equal(ours, entry["last_logits"]), "parity drift"


@needs_weights
def test_qwen3_forward_deterministic() -> None:
    model = _load()
    toks = torch.randint(0, 151936, (1, 256), generator=torch.Generator().manual_seed(3)).cuda()
    with torch.no_grad():
        a = model(toks)
        b = model(toks)
    assert torch.equal(a, b)


@needs_weights
def test_attn_bias_paths_bitwise_and_live() -> None:
    """Selector pre-tests: None bias == base bitwise; EXPLICIT zero bias ==
    base bitwise (exercised path, not a short-circuit); nonzero bias changes
    logits (non-vacuity)."""
    model = _load()
    toks = torch.randint(0, 151936, (1, 128), generator=torch.Generator().manual_seed(7)).cuda()
    t = toks.shape[1]
    zero = {L: torch.zeros(t, t, device="cuda") for L in range(20, 28)}
    spot = {L: torch.zeros(t, t, device="cuda") for L in range(20, 28)}
    for L in spot:
        spot[L][100:, 10:20] = 4.0
    with torch.no_grad():
        base = model(toks)
        assert torch.equal(model(toks, attn_bias=zero), base), "zero bias not identity"
        assert not torch.equal(model(toks, attn_bias=spot), base), "bias ignored (vacuous)"
