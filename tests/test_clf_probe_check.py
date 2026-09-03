"""Deterministic battery for the classifier-selected deficit-wave probe."""

from __future__ import annotations

import math

import torch


def test_registered_arms_and_calibration_are_plumbed():
    from scripts.clf_probe_check import ARM_SPECS, load_wave_calibration

    assert [name for name, _ in ARM_SPECS] == [
        "full",
        "evicted",
        "clf_pinned",
        "clf_pinned_echo",
        "clf_control",
        "clf_pinned_wave",
        "clf_pinned_wave_conf",
        "clf_pinned_echo_wave",
        "fv_inject",
        "fv_inject_echo",
        "fv_clear",
    ]
    calibration = load_wave_calibration()
    assert calibration["selected"] == "t30-b3"
    assert calibration["tau"] == 0.3
    assert calibration["b_max"] == 3.0
    assert len(calibration["sha256"]) == 64


def test_confidence_caps_are_linear_and_monotone():
    from scripts.clf_probe_check import confidence_cap

    probabilities = [0.5, 0.6, 0.75, 0.9, 1.0]
    caps = [confidence_cap(probability, 3.0) for probability in probabilities]
    assert caps == sorted(caps)
    assert caps[0] == 0.0
    assert caps[2] == 1.5
    assert caps[-1] == 3.0


def test_forced_deficit_bias_is_finite_nonzero_and_individually_capped():
    from stencil.qwen3 import _apply_deficit_gate

    attention = torch.zeros(1, 1, 1, 4)
    first = torch.tensor([True, False, False, False])
    second = torch.tensor([False, True, False, False])
    gated = _apply_deficit_gate(
        attention,
        [(first, 0.9, 0.7), (second, 0.9, 0.2)],
    )
    delta = gated - attention
    assert torch.isfinite(delta).all()
    assert 0.0 < delta[..., 0].item()
    assert 0.0 < delta[..., 1].item()
    assert delta[..., 0] <= torch.tensor(0.7)
    assert delta[..., 1] <= torch.tensor(0.2)
    assert torch.count_nonzero(delta[..., 2:]) == 0


def test_zero_deficit_logits_are_bitwise_identical_on_cpu():
    from stencil.qwen3 import Qwen3, Qwen3Config

    cfg = Qwen3Config(
        n_layer=1,
        n_head=2,
        n_kv_head=1,
        head_dim=4,
        d_model=8,
        d_ff=12,
        vocab=17,
        rope_theta=10_000.0,
        rms_eps=1e-6,
        n_ctx=16,
        tie_word_embeddings=True,
    )
    model = Qwen3(cfg).eval()
    tokens = torch.tensor([[1, 2, 3, 4]])
    span = torch.tensor([True, False, False, False])
    hook = (0, lambda _hidden: {0: [(span, 1e-9, 3.0)]})
    with torch.no_grad():
        baseline = model(tokens)
        gated = model(tokens, deficit_hook=hook)
    assert torch.equal(gated, baseline)


def test_zero_deficit_logits_are_bitwise_identical_on_registered_gpu_model():
    import pytest

    pytest.skip("GPU busy with registered 909 run; model process forbidden by brief")


def test_wave_arm_configuration_preserves_prequery_echo_ordering():
    from scripts.clf_probe_check import arm_configuration

    selected = [((2, 4), 0.75, 1)]
    configured = arm_configuration(
        "clf_pinned_echo_wave",
        ids=[10, 11, 12, 13, 50],
        echo_ids=[10, 11, 12, 13, 60, 50],
        evict_range=(1, 4),
        echo_evict_range=(1, 4),
        keep=[(2, 4)],
        selected=selected,
        tau=0.3,
        b_max=3.0,
        eviction_timing="pre-query",
    )
    assert configured["ids"] == [10, 11, 12, 13, 60, 50]
    assert configured["probe_arm"] == "pinned_echo"
    assert configured["eviction_timing"] == "pre-query"
    assert configured["evict_range"] == (1, 4)
    assert configured["keep"] == [(2, 4)]
    assert configured["deficit_spans"] == [((2, 4), 3.0)]
    assert configured["confidence_scaled"] is False


def test_echo_wave_run_evicts_before_current_turn_prefill_on_cpu():
    from torch import nn

    from scripts.ledger_kv_probe import run_arm
    from stencil.qwen3 import Qwen3Config

    events = []

    class Tokenizer:
        def decode(self, _ids, skip_special_tokens=False):
            del skip_special_tokens
            return "answer"

    class StubTrunk(nn.Module):
        def __init__(self):
            super().__init__()
            self.anchor = nn.Parameter(torch.zeros(()))
            self.cfg = Qwen3Config(
                1, 1, 1, 2, 2, 2, 151_646, 10_000.0, 1e-6, 16, True
            )

        def forward(
            self,
            tokens,
            *,
            cache,
            attn_bias=None,
            deficit_hook=None,
        ):
            values = tokens[0].tolist()
            prior_columns = 0 if cache.k[0] is None else cache.k[0].shape[2]
            events.append(
                (values, cache.length, prior_columns, deficit_hook is not None)
            )
            fresh = torch.zeros(1, 1, len(values), 2)
            cache.k[0] = (
                fresh if cache.k[0] is None else torch.cat([cache.k[0], fresh], 2)
            )
            cache.v[0] = cache.k[0].clone()
            cache.length += len(values)
            logits = torch.zeros(1, len(values), self.cfg.vocab)
            logits[0, -1, 7 if len(events) == 2 else 151_645] = 1.0
            return logits

    result = run_arm(
        StubTrunk(),
        Tokenizer(),
        [10, 11, 12, 13, 60, 50],
        "pinned_echo",
        [(2, 3)],
        (1, 4),
        0.0,
        2,
        5.0,
        eviction_timing="pre-query",
        deficit_spans=[((2, 3), 3.0)],
        deficit_tau=0.3,
    )
    assert events == [
        ([10, 11, 12, 13], 0, 0, False),
        ([60, 50], 4, 2, False),
        ([7], 6, 4, True),
    ]
    assert result["generated_token_ids"] == [7]


def test_confidence_formula_stays_finite_at_registered_bounds():
    from scripts.clf_probe_check import confidence_cap

    assert all(
        math.isfinite(confidence_cap(probability, 3.0))
        for probability in (0.5, 1.0)
    )
