# ruff: noqa: E501
"""T2 controller shape/contract tests (synthetic only — permitted before
the bakeoff per v3.1). Checks the frozen step contract
(z_pre = transition(z_prev, D); score from z_pre; write after), state
dims, score-before-write separation, and the oscillator's D-dependence."""
import torch

from stencil.t2_state import CONTROLLERS, make_controller

TYPES3 = 3


def test_all_registered_controllers_exist():
    assert set(CONTROLLERS) == {"osc", "static", "ema", "gru", "nullosc"}


def test_state_shapes_and_param_budget():
    counts = {}
    for name in CONTROLLERS:
        c = make_controller(name)
        z = c.init_state()
        assert z.shape == (TYPES3, 8)
        counts[name] = sum(p.numel() for p in c.parameters())
    # (a)-(d) within +-10% of each other; (e) exempt (control)
    vals = [counts[n] for n in ("osc", "static", "ema", "gru")]
    assert max(vals) <= 1.1 * min(vals), counts
    assert counts["nullosc"] < min(vals) / 5


def test_score_uses_pre_update_state():
    c = make_controller("osc")
    z = c.init_state()
    h20 = torch.randn(2048)
    z_pre = c.transition(z, D=5)
    aug1 = c.score_aug(z_pre)
    z_next = c.write(z_pre, h20, type_idx=1)
    aug2 = c.score_aug(z_pre)
    assert torch.equal(aug1[0], aug2[0]) and torch.equal(aug1[1], aug2[1])  # write mutated nothing scored
    assert not torch.equal(z_next, z_pre)  # write actually writes (fired type)
    assert torch.equal(z_next[0], z_pre[0]) and torch.equal(z_next[2], z_pre[2])  # only type 1 written


def test_oscillator_phase_depends_on_D():
    c = make_controller("osc")
    z = c.write(c.init_state(), torch.randn(2048), type_idx=0)
    a = c.transition(z, D=3)
    b = c.transition(z, D=17)
    assert not torch.allclose(a, b)  # elapsed steps matter


def test_nullosc_has_no_input_coupling():
    c = make_controller("nullosc")
    z = c.init_state()
    z2 = c.write(c.transition(z, D=4), torch.randn(2048), type_idx=0)
    assert torch.equal(z2, c.transition(z, D=4))  # write is a no-op


def test_static_has_no_recurrence():
    c = make_controller("static")
    z = c.init_state()
    assert torch.equal(c.transition(z, D=9), z)  # time does nothing


def test_score_aug_shapes():
    for name in CONTROLLERS:
        c = make_controller(name)
        null_add, q_add = c.score_aug(c.init_state())
        assert null_add.shape == () and q_add.shape == (64,)
