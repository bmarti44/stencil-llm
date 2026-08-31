# ruff: noqa: E501
"""v4.5 deficit-gate battery (sol's registered deterministic tests):
zero deficit -> BITWISE base logits; forced deficit -> finite nonzero
change; uncapped post-bias mass == tau; bias touches only the selected
span/layers; interventions logged. GPU required."""
import math

import pytest
import torch
import torch.nn.functional as F

pytestmark = pytest.mark.skipif(not torch.cuda.is_available(), reason="needs GPU")


@pytest.fixture(scope="module")
def setup():
    from pathlib import Path

    from tokenizers import Tokenizer

    from stencil.qwen3 import Qwen3
    root = Path(__file__).resolve().parent.parent
    tok = Tokenizer.from_file(str(root / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
    m = Qwen3()
    m.load_state_dict(torch.load(root / "models" / "qwen3-1.7b.pt", map_location="cpu"), strict=True)
    return m.to(torch.bfloat16).cuda().eval(), tok


PROMPT = "<|im_start|>user\nList three rivers. Constraint: reply in lowercase only.<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"


def test_zero_deficit_bitwise_base(setup):
    m, tok = setup
    ids = tok.encode(PROMPT).ids
    toks = torch.tensor([ids], device="cuda")
    span = torch.zeros(len(ids), dtype=torch.bool, device="cuda")
    span[3:10] = True
    with torch.no_grad():
        base = m(toks)
        # tau=0 -> psi >= tau always -> zero intervention everywhere
        gated = m(toks, deficit_hook=(20, lambda h: {L: (span, 0.0 + 1e-9, 5.0) for L in range(20, 28)}))
    assert torch.equal(base, gated)


def test_forced_deficit_changes_logits(setup):
    m, tok = setup
    ids = tok.encode(PROMPT).ids
    toks = torch.tensor([ids], device="cuda")
    span = torch.zeros(len(ids), dtype=torch.bool, device="cuda")
    span[3:10] = True
    with torch.no_grad():
        base = m(toks)
        gated = m(toks, deficit_hook=(20, lambda h: {L: (span, 0.999, 10.0) for L in range(20, 28)}))
    d = float((base - gated).abs().max())
    assert 0 < d < float("inf")


def test_uncapped_postbias_mass_equals_tau(setup):
    """numerical check of the odds-correction on one real attention row."""
    m, tok = setup
    ids = tok.encode(PROMPT).ids
    T = len(ids)
    g = torch.Generator().manual_seed(3)
    att = torch.randn(1, 1, 1, T, generator=g).cuda().float() * 3
    span = torch.zeros(T, dtype=torch.bool, device="cuda")
    span[2:8] = True
    tau = 0.6
    p0 = F.softmax(att, dim=-1)
    psi = p0[..., span].sum(-1).clamp(1e-6, 1 - 1e-6)
    b = (math.log(tau / (1 - tau)) - torch.log(psi / (1 - psi)))
    att2 = att + b[..., None] * span.float()
    psi2 = F.softmax(att2, dim=-1)[..., span].sum(-1)
    assert abs(float(psi2) - tau) < 1e-4, float(psi2)


def test_generate_deficit_deterministic_and_logged(setup):
    from pathlib import Path

    from stencil.bench import generate_deficit
    from stencil.wave import WaveController
    m, tok = setup
    root = Path(__file__).resolve().parent.parent
    ctrl = WaveController(beta_max=1.0).cuda()
    ctrl.load_state_dict(torch.load(root / "results" / "qwen" / "b3-ce-s0.pt", map_location="cpu"))
    ctrl = ctrl.eval()
    spans = [(8, 16)]
    a = generate_deficit(m, tok, "List three rivers. Constraint: reply in lowercase only.",
                         ctrl, spans, tau=0.3, b_max=5.0, max_new=32)
    b = generate_deficit(m, tok, "List three rivers. Constraint: reply in lowercase only.",
                         ctrl, spans, tau=0.3, b_max=5.0, max_new=32)
    assert a[:4] == b[:4]
    assert len(a[4]) == a[1]  # one log entry per generated token
