# ruff: noqa: E501
"""Deterministic verifications 1-4 for the GPT-2 retrofit (GPT2-PLAN.md)."""
from pathlib import Path

import pytest
import torch

from stencil import determinism  # noqa: F401
from stencil.gpt2 import GatedGPT2

ROOT = Path(__file__).resolve().parent.parent
WEIGHTS = ROOT / "models" / "gpt2-small.pt"
FIXTURE = ROOT / "tests" / "fixtures" / "gpt2_parity.pt"

needs_weights = pytest.mark.skipif(
    not WEIGHTS.exists(), reason="run scripts/convert_gpt2.py first"
)


def _load(arm: str, window: int | None = None) -> GatedGPT2:
    model = GatedGPT2(arm, window=window)
    sd = torch.load(WEIGHTS, map_location="cpu")
    missing, unexpected = model.load_state_dict(sd, strict=False)
    assert not unexpected
    assert all(m.startswith(("controller.", "gate_source.")) for m in missing)
    return model.eval()


@needs_weights
def test_gpt2_parity() -> None:
    """V1: converted model reproduces the frozen parity fixture BITWISE."""
    model = _load("vanilla")
    captured = torch.load(FIXTURE, map_location="cpu")
    assert len(captured) == 32
    checked = 0
    with torch.no_grad():
        for entry in captured.values():
            ids = torch.tensor([entry["ids"]])
            ours = model(ids)[0, -1]
            assert torch.equal(ours, entry["last_logits"]), "parity drift"
            checked += 1
    assert checked == 32


@needs_weights
def test_graft_inert_bitwise() -> None:
    """V3: gates bypassed => osc arm logits bitwise equal vanilla, windowed."""
    vanilla = _load("vanilla", window=64)
    osc = _load("osc", window=64)
    base = _load("base", window=64)
    toks = torch.randint(
        0, 50257, (2, 256),
        generator=torch.Generator().manual_seed(7),
    )
    with torch.no_grad():
        ref = vanilla(toks)
        assert torch.equal(osc(toks, gate_bypass=True), ref)
        assert torch.equal(base(toks, gate_bypass=True), ref)
        # and NOT bypassed still equals ref at init: gates are exactly 1.0
        # only when the preactivation is exactly 0 — bias starts 0 and weight
        # ~1e-3, so ungated differs; assert it differs to prove the gate path
        # is live (non-vacuity).
        assert not torch.equal(osc(toks), ref)


@needs_weights
def test_trunk_frozen_bitwise() -> None:
    """V4: a short fine-tune moves pathway params but no trunk tensor."""
    model = _load("osc", window=64)
    trunk_before = [p.detach().clone() for p in model.trunk_parameters()]
    path_before = [p.detach().clone() for p in model.pathway_parameters()]
    for p in model.trunk_parameters():
        p.requires_grad_(False)
    opt = torch.optim.AdamW(model.pathway_parameters(), lr=1e-3)
    toks = torch.randint(0, 50257, (2, 128), generator=torch.Generator().manual_seed(3))
    model.train()
    for _ in range(3):
        logits = model(toks)
        loss = logits[:, :-1].log_softmax(-1).gather(-1, toks[:, 1:, None]).mean().neg()
        loss.backward()
        opt.step()
        opt.zero_grad()
    for before, after in zip(trunk_before, model.trunk_parameters(), strict=True):
        assert torch.equal(before, after), "trunk moved"
    moved = any(
        not torch.equal(b, a)
        for b, a in zip(path_before, model.pathway_parameters(), strict=True)
    )
    assert moved, "pathway never trained — vacuous"


@needs_weights
def test_training_determinism_bitwise() -> None:
    """V2: two identical short fine-tunes are bitwise identical."""
    def one() -> tuple[list[float], list[torch.Tensor]]:
        model = _load("osc", window=64)
        for p in model.trunk_parameters():
            p.requires_grad_(False)
        opt = torch.optim.AdamW(model.pathway_parameters(), lr=1e-3)
        toks = torch.randint(0, 50257, (2, 128), generator=torch.Generator().manual_seed(11))
        losses = []
        model.train()
        for _ in range(3):
            logits = model(toks)
            loss = logits[:, :-1].log_softmax(-1).gather(-1, toks[:, 1:, None]).mean().neg()
            loss.backward()
            opt.step()
            opt.zero_grad()
            losses.append(loss.detach().clone())
        return losses, [p.detach().clone() for p in model.pathway_parameters()]

    l1, p1 = one()
    l2, p2 = one()
    assert all(torch.equal(a, b) for a, b in zip(l1, l2, strict=True))
    assert all(torch.equal(a, b) for a, b in zip(p1, p2, strict=True))


@needs_weights
def test_lora_inert_and_pathway_classified() -> None:
    """LoRA at init (B=0) must be bitwise inert; its params must be
    PATHWAY (trainable), never trunk (frozen)."""
    vanilla = _load("vanilla", window=64)
    lora = GatedGPT2("osc", window=64, lora_rank=4)
    sd = torch.load(WEIGHTS, map_location="cpu")
    lora.load_state_dict(sd, strict=False)
    lora.eval()
    toks = torch.randint(0, 50257, (2, 128), generator=torch.Generator().manual_seed(5))
    with torch.no_grad():
        assert torch.equal(lora(toks, gate_bypass=True), vanilla(toks))
    trunk_ids = {id(p) for p in lora.trunk_parameters()}
    lora_params = [p for n, p in lora.named_parameters() if "lora" in n]
    assert len(lora_params) == 24  # 12 layers x (A, B)
    assert all(id(p) not in trunk_ids for p in lora_params), "LoRA frozen as trunk!"
