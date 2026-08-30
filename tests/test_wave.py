# ruff: noqa: E501
"""Internal-wave controller shape/contract tests (synthetic only;
architecture params may still move at review — beta_max is a ctor arg).

Frozen contract (v3 + W0.05 selection A2): e = 8 * cos(q, k') with
q = W_q h20, k' = W_k K (64-d, F.normalize both);
b = g * softmax(e)/max(softmax(e)) (peak-normalized: per-token cap g);
g = beta_max * sigmoid(w_g h20), w_g weight zero / bias -2 init
(g0 = 0.238 * beta_max). Bounded per token, differentiable.
"""
import torch

from stencil.wave import WaveController


def test_bias_row_shape_and_bounds():
    w = WaveController(beta_max=2.0)
    h = torch.randn(2048)
    K = torch.randn(37, 2048)
    b = w(h, K)
    assert b.shape == (37,)
    assert float(b.min()) >= 0.0
    assert float(b.max()) <= 2.0 + 1e-5   # peak-normalized: per-token cap g
    assert abs(float(b.max()) - float(w.gain(h))) < 1e-5  # the peak IS g


def test_gradients_reach_all_params():
    # weighted positional functional (NOT b.sum(): with peak-normalization
    # a plain sum can still hide q/k connectivity — sol round-2 lesson)
    w = WaveController(beta_max=2.0)
    b = w(torch.randn(2048), torch.randn(5, 2048))
    (b * torch.tensor([1.0, -2.0, 3.0, 0.5, -1.0])).sum().backward()
    for name, p in w.named_parameters():
        assert p.grad is not None and float(p.grad.abs().sum()) > 0, name


def test_gain_saturates_at_beta_max():
    w = WaveController(beta_max=2.0)
    with torch.no_grad():
        w.w_g.weight.fill_(100.0)  # force sigmoid -> 1
    b = w(torch.ones(2048), torch.randn(4, 2048))
    assert abs(float(b.max()) - 2.0) < 1e-4


def test_registered_low_gain_init():
    w = WaveController(beta_max=2.0)
    g = float(w.gain(torch.randn(2048)))
    assert abs(g - 2.0 * 0.11920292) < 1e-6  # weight zero -> exactly sigmoid(-2)*beta


def test_field_mode_rows():
    """Teacher-forced training uses a whole field: T generation rows at once."""
    w = WaveController(beta_max=2.0)
    H = torch.randn(11, 2048)   # 11 generation positions
    K = torch.randn(37, 2048)
    B = w.field(H, K)
    assert B.shape == (11, 37)
    row = w(H[3], K)
    assert torch.allclose(B[3], row, atol=1e-5)


def test_param_count_matches_registered():
    w = WaveController(beta_max=2.0)
    n = sum(p.numel() for p in w.parameters())
    # W_q 2048*64+64, W_k 2048*64+64, w_g 2048+1
    assert n == (2048 * 64 + 64) * 2 + 2048 + 1, n
