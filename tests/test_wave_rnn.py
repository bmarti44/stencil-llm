# ruff: noqa: E501
"""W1 recurrent wave — red-first (frozen contract v3 W1 + v3.1 H3).

s_t = GRU(h20_t, s_{t-1}) FIRST, then q_t/g_t from [h20_t; s_t]
(score-after-write, registered). State 64-d, reset per session, carried
across work turns with detach at turn boundaries (trainer's job).
Field equation unchanged (A2 peak-normalized via the same math)."""
import torch

from stencil.wave import WaveRNN


def test_state_shapes_and_carry():
    w = WaveRNN(beta_max=2.0)
    s = w.init_state()
    assert s.shape == (64,)
    K = torch.randn(20, 2048)
    b1, s1 = w.step(torch.randn(2048), s, K)
    b2, s2 = w.step(torch.randn(2048), s1, K)
    assert b1.shape == (20,) and b2.shape == (20,)
    assert not torch.equal(s1, s2)


def test_score_after_write():
    # the emitted row must depend on the CURRENT step's updated state:
    # same h20, different predecessor states -> different rows
    w = WaveRNN(beta_max=2.0)
    h = torch.randn(2048)
    K = torch.randn(9, 2048)
    b_a, _ = w.step(h, w.init_state(), K)
    s_alt = torch.randn(64)
    b_b, _ = w.step(h, s_alt, K)
    assert not torch.allclose(b_a, b_b)


def test_bounds_and_gradients():
    w = WaveRNN(beta_max=2.0)
    s = w.init_state()
    loss = torch.tensor(0.0)
    K = torch.randn(7, 2048)
    for _ in range(3):
        b, s = w.step(torch.randn(2048), s, K)
        assert float(b.min()) >= 0.0 and float(b.max()) <= 2.0 + 1e-5
        loss = loss + (b * torch.randn(7)).sum()
    loss.backward()
    for name, p in w.named_parameters():
        assert p.grad is not None and float(p.grad.abs().sum()) > 0, name


def test_registered_low_gain_init_preserved():
    w = WaveRNN(beta_max=2.0)
    b, _ = w.step(torch.zeros(2048), w.init_state(), torch.randn(5, 2048))
    # zero h20 + zero state -> gain head sees zeros through zero-init
    # weight -> exactly sigmoid(-2)*beta at the peak
    assert abs(float(b.max()) - 2.0 * 0.11920292) < 1e-5
