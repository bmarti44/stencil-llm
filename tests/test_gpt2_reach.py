# ruff: noqa: E501
"""Verification 5: the doorless room on GPT-2 (exact-zero Jacobian)."""
from pathlib import Path

import pytest
import torch

from stencil import determinism  # noqa: F401
from stencil.gpt2 import GatedGPT2

ROOT = Path(__file__).resolve().parent.parent
WEIGHTS = ROOT / "models" / "gpt2-small.pt"
needs_weights = pytest.mark.skipif(not WEIGHTS.exists(), reason="run convert_gpt2.py")


def _load(arm: str) -> GatedGPT2:
    model = GatedGPT2(arm, window=64)
    model.load_state_dict(torch.load(WEIGHTS, map_location="cpu"), strict=False)
    return model.eval()


def _grad_norm(model: GatedGPT2, t: int, src: int, dst: int) -> float:
    """|d logits[dst] / d embedding[src]| via input-embedding grad."""
    toks = torch.randint(0, 50257, (1, t), generator=torch.Generator().manual_seed(1))
    emb = model.wte(toks).detach().requires_grad_(True)
    pos = torch.arange(t)
    x = emb + model.wpe(pos)
    gates = None
    if model.arm != "vanilla":
        control = model.controller(emb) if model.arm == "osc" else emb
        control = control * torch.rsqrt(control.pow(2).mean(-1, keepdim=True) + 1e-8)
        g = model.gate_source(control)
        gates = g.view(1, t, 12, 12)
    mask = model._mask(t, toks.device)
    for i, block in enumerate(model.blocks):
        x = block(x, mask, None if gates is None else gates[:, :, i, :])
    x = model.ln_f(x)
    logits = x @ model.wte.weight.T
    scalar = logits[0, dst].pow(2).sum()
    (grad,) = torch.autograd.grad(scalar, emb)
    assert grad is not None
    return float(grad[0, src].abs().max())


@needs_weights
def test_unreachable_zero_grad_gpt2() -> None:
    """Beyond 12x63=756 tokens, base/vanilla gradients are EXACTLY zero;
    the osc arm's are nonzero (the wire is the only path).
    Also pin the boundary: within reach, vanilla is nonzero."""
    t, dst = 1000, 999
    beyond, within = dst - 800, dst - 700   # 800 > 756 >= 700
    vanilla = _load("vanilla")
    g_beyond = _grad_norm(vanilla, t, beyond, dst)
    g_within = _grad_norm(vanilla, t, within, dst)
    assert g_beyond == 0.0, f"reachability leak: {g_beyond}"
    assert g_within > 0.0, "boundary pin failed — window arithmetic wrong"

    base = _load("base")
    assert _grad_norm(base, t, beyond, dst) == 0.0, "stateless gate leaked reach"

    osc = _load("osc")
    g_osc = _grad_norm(osc, t, beyond, dst)
    assert g_osc > 0.0, "wire path not connected (vacuous)"
