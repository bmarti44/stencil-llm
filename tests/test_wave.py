# ruff: noqa: E501
"""Internal-wave controller shape/contract tests (synthetic only;
architecture params may still move at review — beta_max is a ctor arg).

Contract (INTERNAL-WAVE-PLAN W0): controller reads h20_t [2048] and
prompt key features K [P, 2048]; emits a bias row over the P prompt
positions: b = g * softmax(q K'^T / 8) with q = W_q h20 (64-d),
K' = W_k K (64-d), g = beta_max * sigmoid(w_g . h20). Bounded,
differentiable, nonnegative.
"""
import torch

from stencil.wave import WaveController


def test_bias_row_shape_and_bounds():
    w = WaveController(beta_max=4.0)
    h = torch.randn(2048)
    K = torch.randn(37, 2048)
    b = w(h, K)
    assert b.shape == (37,)
    assert float(b.min()) >= 0.0
    assert float(b.sum()) <= 4.0 + 1e-5  # softmax sums to 1, so total bias <= g <= beta_max


def test_gradients_reach_all_params():
    w = WaveController(beta_max=2.0)
    b = w(torch.randn(2048), torch.randn(5, 2048))
    b.sum().backward()
    for name, p in w.named_parameters():
        assert p.grad is not None and float(p.grad.abs().sum()) > 0, name


def test_gain_saturates_at_beta_max():
    w = WaveController(beta_max=2.0)
    with torch.no_grad():
        w.w_g.weight.fill_(100.0)  # force sigmoid -> 1
    b = w(torch.ones(2048), torch.randn(4, 2048))
    assert abs(float(b.sum()) - 2.0) < 1e-4


def test_field_mode_rows():
    """Teacher-forced training uses a whole field: T generation rows at once."""
    w = WaveController(beta_max=4.0)
    H = torch.randn(11, 2048)   # 11 generation positions
    K = torch.randn(37, 2048)
    B = w.field(H, K)
    assert B.shape == (11, 37)
    row = w(H[3], K)
    assert torch.allclose(B[3], row, atol=1e-5)


def test_param_count_matches_registered():
    w = WaveController(beta_max=4.0)
    n = sum(p.numel() for p in w.parameters())
    # W_q 2048*64+64, W_k 2048*64+64, w_g 2048+1
    assert n == (2048 * 64 + 64) * 2 + 2048 + 1, n
