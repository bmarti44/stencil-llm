"""Phase 2 model and plumbing proof tests."""

from __future__ import annotations

import json
import math
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest
import torch
from torch.nn import functional as F

from stencil.config import Config, load_config
from stencil.data import generate
from stencil.determinism import named_generator
from stencil.model import (
    DecayCell,
    OscillatorCell,
    StencilTransformer,
    assert_stable,
    build_matched_configs,
    count_params,
    discrete_invariant,
)

ROOT = Path(__file__).parents[1]
BASE_CONFIG = load_config(ROOT / "configs/test_tiny.json")
JAX_FIXTURE = ROOT / "tests/fixtures/jax_cells.npz"
JAX_SKIP_REASON = (
    "jax fixtures not yet generated — orchestrator runs scripts/gen_jax_fixtures.py"
)


def _draw(seed: int, stream: str, shape: tuple[int, ...], dtype=torch.float64):
    return torch.randn(shape, generator=named_generator(seed, stream), dtype=dtype)


def _cell(
    period: float,
    damping: float,
    *,
    dtype: torch.dtype,
) -> OscillatorCell:
    cell = OscillatorCell(
        input_dim=1,
        pairs=1,
        period_min=period,
        period_max=period,
        damping_learnable=damping != 0.0,
        generator=named_generator(0, "fixtures:b"),
        dtype=dtype,
    )
    with torch.no_grad():
        cell.B.fill_(1.0)
        if damping:
            cell.g_raw.copy_(torch.tensor([math.log(math.expm1(damping))], dtype=dtype))
    return cell


def _closed_form(
    period: float,
    damping: float,
    forcing: float,
    initial: torch.Tensor,
    steps: int,
) -> torch.Tensor:
    a = (2 * math.pi / period) ** 2
    denominator = 1 + damping
    matrix = torch.tensor(
        [[1 - a / denominator, 1 / denominator], [-a / denominator, 1 / denominator]],
        dtype=torch.float64,
    )
    drive = torch.tensor(
        [forcing / denominator, forcing / denominator], dtype=torch.float64
    )
    state = initial.clone()
    trajectory = []
    for _ in range(steps):
        state = matrix @ state + drive
        trajectory.append(state.clone())
    return torch.stack(trajectory)


def test_oscillator_matches_discrete_closed_form() -> None:
    """Run 12 cases: periods {8,64,4096} x G {0,1e-2} x zero/constant
    forcing for 1000 steps.  The fp64 cell/reference tolerance is rtol=1e-9,
    atol=1e-12; fp32/fp64 is rtol=1e-4 with per-case atol=1e-4 times
    max|fp64 reference| over the trajectory.  Zero-forcing initial states are
    nonzero N(0,1) from seed 0 stream ``fixtures:init``; constant forcing is
    b=u=1 from y0=z0=0.
    """
    cases = 0
    for period in (8.0, 64.0, 4096.0):
        for damping in (0.0, 1e-2):
            for forcing in (0.0, 1.0):
                initial = (
                    _draw(0, "fixtures:init", (2,))
                    if forcing == 0.0
                    else torch.zeros(2, dtype=torch.float64)
                )
                assert initial.numel() == 2
                if forcing == 0.0:
                    assert torch.count_nonzero(initial) == 2
                inputs64 = torch.full((1, 1000, 1), forcing, dtype=torch.float64)
                reference = _closed_form(period, damping, forcing, initial, 1000)
                cell64 = _cell(period, damping, dtype=torch.float64)
                y64, z64 = cell64(inputs64, initial=(initial[:1], initial[1:]))
                actual64 = torch.stack((y64[0, :, 0], z64[0, :, 0]), dim=-1)
                torch.testing.assert_close(actual64, reference, rtol=1e-9, atol=1e-12)

                cell32 = _cell(period, damping, dtype=torch.float32)
                y32, z32 = cell32(
                    inputs64.float(), initial=(initial[:1].float(), initial[1:].float())
                )
                actual32 = torch.stack((y32[0, :, 0], z32[0, :, 0]), dim=-1)
                fp32_atol = 1e-4 * actual64.abs().max().item()
                torch.testing.assert_close(
                    actual32.double(), actual64, rtol=1e-4, atol=fp32_atol
                )
                cases += 1
    assert cases == 12


def _energy_trajectory(dtype: torch.dtype, damping: float = 0.0):
    cell = OscillatorCell(
        input_dim=64,
        pairs=64,
        period_min=8,
        period_max=4096,
        damping_learnable=damping != 0,
        generator=named_generator(0, "fixtures:b"),
        dtype=dtype,
    )
    if damping:
        with torch.no_grad():
            cell.g_raw.fill_(math.log(math.expm1(damping)))
    initial = _draw(0, "fixtures:init", (2, 64), dtype=dtype)
    inputs = torch.zeros(1, 10_000, 64, dtype=dtype)
    y, z = cell(inputs, initial=(initial[0], initial[1]))
    return cell, initial, y[0], z[0]


def test_discrete_invariant_conserved() -> None:
    """Run 2 dtype cases (fp64/fp32), zero input for 10k steps, standard
    64-mode periods [8,4096], G=0, seed 0 ``fixtures:init`` state.  H_d drift
    is rtol=1e-5/1e-3 respectively; continuous H max is <4*H0 and its final
    five 1000-step window means have |least-squares slope| <1e-4*H0/window.
    """
    cases = 0
    for dtype, invariant_rtol in ((torch.float64, 1e-5), (torch.float32, 1e-3)):
        cell, initial, y, z = _energy_trajectory(dtype)
        assert y.numel() == z.numel() == 640_000
        hd0 = discrete_invariant(initial[0], initial[1], cell.A)
        hd = discrete_invariant(y, z, cell.A)
        torch.testing.assert_close(hd, hd0.expand_as(hd), rtol=invariant_rtol, atol=0)
        h0 = initial[1].square() + cell.A * initial[0].square()
        energy = z.square() + cell.A * y.square()
        assert torch.all(energy.max(dim=0).values < 4 * h0)
        means = energy.reshape(10, 1000, 64).mean(dim=(1, 2))
        x = torch.arange(5, dtype=torch.float64)
        slope = (
            (x - x.mean()) * (means[-5:].double() - means[-5:].double().mean())
        ).sum()
        slope /= (x - x.mean()).square().sum()
        assert abs(slope) < 1e-4 * h0.double().mean()
        cases += 1
    assert cases == 2


def test_damped_energy_decays() -> None:
    """Run 2 fp64, 10k-step zero-input cases from seed 0 ``fixtures:init``:
    G=1e-2 has strictly decreasing 1000-step means and H10000 <1e-2 H0;
    G=softplus(-9) has non-increasing means and H10000/H0 within [0.8,1.2]
    times the analytically exact modal factor (1+G)^-10000 (rtol=0, atol=0
    for the registered inequality bounds).
    """
    cases = 0
    for damping in (1e-2, float(F.softplus(torch.tensor(-9.0, dtype=torch.float64)))):
        cell, initial, y, z = _energy_trajectory(torch.float64, damping)
        energy = (z.square() + cell.A * y.square()).sum(dim=-1)
        h0 = (initial[1].square() + cell.A * initial[0].square()).sum()
        means = energy.reshape(10, 1000).mean(dim=1)
        if damping == 1e-2:
            assert torch.all(means[1:] < means[:-1])
            assert energy[-1] < 1e-2 * h0
        else:
            assert torch.all(means[1:] <= means[:-1])
            modal = (1 + damping) ** -10_000
            ratio = float((energy[-1] / h0).detach())
            assert 0.8 * modal <= ratio <= 1.2 * modal
        cases += 1
    assert cases == 2


def test_decay_ssm_energy_decays() -> None:
    """Run 1 case: B2 state dim 128, lambda=0.999, seed 0
    ``fixtures:init`` N(0,1) state, zero input, 10k steps.  The 1000-step
    state-norm-square means are non-increasing and the final/initial ratio is
    within [0.8,1.2] * lambda^(2*10000), with exact inequality comparisons.
    """
    cell = DecayCell(
        256, 128, generator=named_generator(0, "fixtures:b"), dtype=torch.float64
    )
    initial = _draw(0, "fixtures:init", (128,))
    states = cell(torch.zeros(1, 10_000, 256, dtype=torch.float64), initial=initial)[0]
    energy = states.square().sum(dim=-1)
    means = energy.reshape(10, 1000).mean(dim=1)
    expected = 0.999**20_000
    ratio = float((energy[-1] / initial.square().sum()).detach())
    assert states.numel() == 1_280_000
    assert torch.all(means[1:] <= means[:-1])
    assert 0.8 * expected <= ratio <= 1.2 * expected
    assert 1 == 1


def test_stability_bound() -> None:
    """Run 2 registered oscillator variants (M1/M1b), each with two cells and
    standard 64-mode periods [8,4096], asserting dt*sqrt(A)<2 elementwise at
    init (rtol=0, atol=0).  Also exercise one violating checkpoint negatively.
    """
    cases = 0
    configs = build_matched_configs()
    for variant in ("m1", "m1b"):
        model = StencilTransformer(configs[variant])
        assert_stable(model)
        assert len(model.controller.cells) == 2
        cases += 1
    bad = StencilTransformer(configs["m1"])
    with torch.no_grad():
        bad.controller.cells[0].a_raw.fill_(10.0)
    with pytest.raises(ValueError, match="stability bound"):
        assert_stable(bad)
    assert cases == 2


def test_damping_zero_matches_m1_bitwise() -> None:
    """Run 1 fp32 case: length 512 N(0,1) ``fixtures:input`` seed 0 and
    nonzero N(0,1) initial states from ``fixtures:init``.  M1b with the exact
    zero_damping bypass must have a nonzero trajectory bitwise equal to M1.
    """
    generator = named_generator(0, "fixtures:b")
    m1 = OscillatorCell(64, 64, 8, 4096, False, generator=generator)
    m1b = OscillatorCell(
        64, 64, 8, 4096, True, generator=named_generator(0, "fixtures:b")
    )
    with torch.no_grad():
        m1b.B.copy_(m1.B)
        m1b.a_raw.copy_(m1.a_raw)
    inputs = _draw(0, "fixtures:input", (1, 512, 64), dtype=torch.float32)
    state = _draw(0, "fixtures:init", (2, 64), dtype=torch.float32)
    left = m1(inputs, initial=(state[0], state[1]))
    right = m1b(inputs, initial=(state[0], state[1]), zero_damping=True)
    assert torch.count_nonzero(left[0]) > 0
    assert torch.count_nonzero(left[1]) > 0
    assert torch.equal(left[0], right[0])
    assert torch.equal(left[1], right[1])
    with pytest.raises(ValueError, match="only valid for learnable damping"):
        m1(inputs[:, :1], zero_damping=True)
    assert 1 == 1


@pytest.mark.skipif(
    not JAX_FIXTURE.exists(),
    reason=JAX_SKIP_REASON,
)
def test_cell_matches_jax_fixtures() -> None:
    """Run 4 fp64 cases: seeds {0,1} x G {0,1e-2}, m=64, length=512,
    A/B/GLU/input from named ``fixtures:a/b/glu/input`` streams; compare both
    cell trajectories to pinned LinOSS 05a8353 and D-LinOSS 450b546 fixtures
    at rtol=1e-5, atol=1e-8. Metadata pins JAX 0.4.35 and records NumPy.
    """
    archive = np.load(JAX_FIXTURE, allow_pickle=False)
    metadata = json.loads(str(archive["metadata"]))
    assert metadata["jax"] == "0.4.35"
    assert metadata["linoss_commit"] == "05a835355439ee5500b2c8f891132c53adf020c0"
    assert (
        metadata["damped_linoss_commit"] == "450b546f693918fe7cfe44082e88538fb29fbd64"
    )
    cases = 0
    for seed in (0, 1):
        for label, damping in (("undamped", 0.0), ("damped", 1e-2)):
            inputs = torch.from_numpy(archive[f"seed{seed}_inputs"])[None]
            b_stream = named_generator(seed, "fixtures:b")
            first = OscillatorCell(
                256, 64, 8, 4096, damping != 0, generator=b_stream, dtype=torch.float64
            )
            second = OscillatorCell(
                64, 64, 8, 4096, damping != 0, generator=b_stream, dtype=torch.float64
            )
            with torch.no_grad():
                a = torch.from_numpy(archive[f"seed{seed}_A"])
                first.a_raw.copy_(torch.log(torch.expm1(a)))
                second.a_raw.copy_(torch.log(torch.expm1(a)))
                first.B.copy_(torch.from_numpy(archive[f"seed{seed}_B1"]))
                second.B.copy_(torch.from_numpy(archive[f"seed{seed}_B2"]))
                if damping:
                    first.g_raw.fill_(math.log(math.expm1(damping)))
                    second.g_raw.fill_(math.log(math.expm1(damping)))
            initial = torch.from_numpy(archive[f"seed{seed}_initial"])
            y1, z1 = first(inputs, initial=(initial[0], initial[1]))
            wa = torch.from_numpy(archive[f"seed{seed}_Wa"])
            wb = torch.from_numpy(archive[f"seed{seed}_Wb"])
            glu = F.linear(y1, wa) * torch.sigmoid(F.linear(y1, wb))
            y2, z2 = second(glu, initial=(initial[2], initial[3]))
            for state_name, actual in (("y1", y1), ("z1", z1), ("y2", y2), ("z2", z2)):
                torch.testing.assert_close(
                    actual[0].numpy(force=True),
                    archive[f"seed{seed}_{label}_{state_name}"],
                    rtol=1e-5,
                    atol=1e-8,
                )
            cases += 1
    assert cases == 4


def _task_a_config(variant: str, seed: int = 0, task_n: int = 512) -> Config:
    config = build_matched_configs(seed_init=seed)[variant]
    return replace(
        config,
        seed_data=seed,
        task="a",
        task_N=task_n,
        task_k=8,
        context_len=task_n + 4,
    )


def test_gate_identity_recovers_baseline_bitwise() -> None:
    """Run 2 fp32 cases (M1 and B1): same seed_init=0 shared base init,
    identity-bypass gates exactly 1, one Task A (N=512,k=8,seed_rules=0,
    seed_data=0) batch of 8.  Nonzero logits must be bitwise equal to B0-local.
    """
    base_config = _task_a_config("b0_local")
    stream = generate(base_config)
    tokens = torch.stack([next(stream)[0] for _ in range(8)])
    with torch.no_grad():
        baseline = StencilTransformer(base_config)(tokens)
    cases = 0
    for variant in ("m1", "b1"):
        model = StencilTransformer(_task_a_config(variant))
        with torch.no_grad():
            logits = model(tokens, gate_identity=True)
        assert torch.count_nonzero(logits) > 0
        assert torch.equal(logits, baseline)
        cases += 1
    with pytest.raises(ValueError, match="has no gate"):
        StencilTransformer(base_config)(tokens, gate_identity=True)
    assert cases == 2


def _logit_jacobian(model: StencilTransformer, tokens: torch.Tensor) -> torch.Tensor:
    embeddings = model.token_embedding(tokens).detach()
    cue = embeddings[:, 0, :].clone().requires_grad_(True)
    injected = torch.cat((cue[:, None, :], embeddings[:, 1:, :]), dim=1)
    logits = model.forward_embeddings(injected)[:, -1, :].reshape(-1)
    gradient = torch.autograd.grad(
        logits,
        cue,
        grad_outputs=torch.eye(logits.numel()),
        is_grads_batched=True,
        allow_unused=True,
    )[0]
    assert gradient is not None
    assert gradient.numel() == logits.numel() * cue.numel()
    return gradient


def test_cue_unreachable_exact_zero_grad() -> None:
    """Run 90 fp32 cases: B0-local/B1 and M1/M1b/B2, seeds {0,1,2},
    N {512,2048}, first 3 seed_data eval-stream Task A (k=8, seed_rules=0)
    sequences. At each sole answer-decision position the full 64-logit Jacobian
    wrt cue-position activation is a connected real tensor: exactly zero for
    B0-local/B1 and nonzero for M1/M1b/B2 (exact comparisons, rtol=atol=0).
    """
    cases = 0
    for seed in (0, 1, 2):
        for task_n in (2048, 512):
            streams = {}
            for variant in ("m1", "m1b", "b2", "b0_local", "b1"):
                config = _task_a_config(variant, seed, task_n)
                streams[variant] = (StencilTransformer(config), generate(config))
            for variant, (model, stream) in streams.items():
                batch = []
                for _ in range(3):
                    tokens, mask, _ = next(stream)
                    assert torch.nonzero(mask).flatten().tolist() == [task_n + 2]
                    batch.append(tokens[:-1])
                jacobian = _logit_jacobian(model, torch.stack(batch))
                for sample in range(3):
                    sample_jacobian = jacobian[
                        sample * config.vocab : (sample + 1) * config.vocab,
                        sample,
                    ]
                    if variant in {"b0_local", "b1"}:
                        assert torch.count_nonzero(sample_jacobian) == 0
                    else:
                        assert torch.count_nonzero(sample_jacobian) > 0, (
                            f"zero recurrent Jacobian: {variant=}, {seed=}, "
                            f"N={task_n}, sample={sample}"
                        )
                    cases += 1
    assert cases == 90


def test_cue_reachable_when_close() -> None:
    """Run 3 fp32 B0-local cases, seeds {0,1,2}, with cue-to-answer-decision
    distance exactly model.receptive_field(); the connected full-vocab-logit
    Jacobian wrt cue activation is nonzero (exact comparison, rtol=atol=0).
    """
    cases = 0
    for seed in (0, 1, 2):
        config = _task_a_config("b0_local", seed, task_n=250)
        model = StencilTransformer(config)
        distance = model.receptive_field()
        tokens = torch.full((1, distance + 1), 50, dtype=torch.long)
        tokens[0, 0] = 1
        jacobian = _logit_jacobian(model, tokens)
        assert torch.count_nonzero(jacobian) > 0
        cases += 1
    assert cases == 3


def test_param_match_within_1pct() -> None:
    """Run 15 pairwise cases over configs for all six variants. Trainable
    counts (buffers excluded, embeddings included) must differ by <=1% of the
    larger count (rtol=0.01, atol=0); M1/M1b both use d_ff=1024 and remaining
    d_ff widths are the lexicographically first multiples of 8 satisfying it.
    """
    configs = build_matched_configs()
    assert list(configs) == ["b0_full", "b0_local", "b1", "b2", "m1", "m1b"]
    models = {name: StencilTransformer(config) for name, config in configs.items()}
    counts = {name: count_params(model) for name, model in models.items()}
    assert configs["m1"].d_ff == configs["m1b"].d_ff == 1024
    cases = 0
    names = list(configs)
    for index, left in enumerate(names):
        for right in names[index + 1 :]:
            assert abs(counts[left] - counts[right]) <= 0.01 * max(
                counts[left], counts[right]
            )
            cases += 1
    assert cases == 15
