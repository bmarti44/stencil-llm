# ruff: noqa: E501
"""T1 head (prereg v3 frozen architecture) — red-first.

Logit layout: index 0 = NULL, 1..n = typed candidates.
Hand-computed expectations use T=1 (t init softplus_inverse(1)).
"""
import math

import torch

from stencil.t1_head import T1Head, decide, margin_loss


def make_head():
    torch.manual_seed(0)
    return T1Head()


def test_temperature_starts_at_one():
    h = make_head()
    assert math.isclose(float(torch.nn.functional.softplus(h.t)), 1.0, rel_tol=1e-6)


def test_warm_start_matches_legacy_cosine():
    h = make_head()
    legacy = torch.load("results/qwen/t2b-selector.pt", map_location="cpu")
    Wq = torch.nn.Linear(2048, 64); Wq.load_state_dict(legacy["Wq"])
    Wk = torch.nn.Linear(2048, 64); Wk.load_state_dict(legacy["Wk"])
    h.warm_start(legacy)
    x = torch.randn(2048)
    C = torch.randn(3, 2048)
    logits = h(x, C)
    q = torch.nn.functional.normalize(Wq(x), dim=0)
    k = torch.nn.functional.normalize(Wk(C), dim=1)
    want = q @ k.T  # T = 1 at init
    assert torch.allclose(logits[1:], want, atol=1e-5)
    # NULL head zero-init -> NULL logit exactly 0
    assert float(logits[0]) == 0.0


def test_decide_rule():
    # decision_score = best candidate logit - NULL logit; > 0 -> candidate
    assert decide(torch.tensor([0.0, 0.5, 0.2])) == 0   # cand index 0 (logit 0.5)
    assert decide(torch.tensor([0.6, 0.5, 0.2])) is None  # NULL wins
    assert decide(torch.tensor([0.5, 0.5])) is None       # exact tie -> NULL
    assert decide(torch.tensor([0.0, 0.7, 0.7])) == 0     # cand tie -> first index
    assert decide(torch.tensor([0.0])) is None            # no candidates


def test_margin_loss_active():
    # active row; live is c1 = CANDIDATE index 0; logits [NULL, c1, c2]
    logits = torch.tensor([0.0, 0.3, 0.1])
    # live must beat max(NULL, best other) + 0.1: 0.3 >= max(0, 0.1)+0.1=0.2 -> satisfied, hinge 0
    assert float(margin_loss(logits, live_idx=0)) == 0.0
    logits = torch.tensor([0.25, 0.3, 0.1])
    # 0.3 vs max(0.25,0.1)+0.1=0.35 -> hinge 0.05
    assert math.isclose(float(margin_loss(logits, live_idx=0)), 0.05, rel_tol=1e-6)


def test_margin_loss_inactive():
    # inactive hard negative: NULL must beat strongest candidate + 0.1
    logits = torch.tensor([0.5, 0.3, 0.1])
    assert float(margin_loss(logits, live_idx=None)) == 0.0  # 0.5 >= 0.4
    logits = torch.tensor([0.35, 0.3, 0.1])
    assert math.isclose(float(margin_loss(logits, live_idx=None)), 0.05, rel_tol=1e-6)


def test_margin_loss_no_candidates():
    assert float(margin_loss(torch.tensor([0.7]), live_idx=None)) == 0.0
