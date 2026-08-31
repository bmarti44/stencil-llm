# ruff: noqa: E501
"""Conflict-Triggered Readout Bursts: pure contracts plus GPU plumbing.

The GPU tests deliberately use a non-sealed synthetic prompt.  They prove
consumer-path determinism and intervention reachability without touching any
registered benchmark split.
"""

import math

import pytest
import torch


def test_six_feature_vector_hand_fixture():
    from stencil.ctrb import StepObservation, trajectory_vector

    history = [
        StepObservation(
            conflict=0.10, entropy=1.20, margin=0.40, attention=0.20, selected_span=0
        ),
        StepObservation(
            conflict=0.11, entropy=1.21, margin=0.39, attention=0.21, selected_span=1
        ),
        StepObservation(
            conflict=0.12, entropy=1.22, margin=0.38, attention=0.22, selected_span=0
        ),
        StepObservation(
            conflict=0.13, entropy=1.23, margin=0.37, attention=0.23, selected_span=0
        ),
        StepObservation(
            conflict=0.14, entropy=1.24, margin=0.36, attention=0.24, selected_span=0
        ),
    ]
    cur = StepObservation(
        conflict=0.18, entropy=1.50, margin=0.25, attention=0.35, selected_span=0
    )
    got = trajectory_vector(history, cur, delta=5)
    # delta5 C, delta5 H, -delta5 margin, A, delta5 A, address stability.
    assert got == pytest.approx((0.08, 0.30, 0.15, 0.35, 0.15, 0.8))


def test_conflict_energy_is_pair_mass_over_topk():
    from stencil.ctrb import distribution_observation

    logits = torch.log(torch.tensor([0.5, 0.3, 0.2]))
    obs = distribution_observation(logits, attention=0.4, selected_span=2, top_k=3)
    assert obs.conflict == pytest.approx(0.5 * 0.3 + 0.5 * 0.2 + 0.3 * 0.2)
    assert obs.entropy == pytest.approx(
        -(0.5 * math.log(0.5) + 0.3 * math.log(0.3) + 0.2 * math.log(0.2))
    )
    assert obs.margin == pytest.approx(0.2)


def test_hazard_fit_is_zero_init_deterministic_and_separates():
    from stencil.ctrb import HazardGate

    X = [
        (-2.0, 0, 0, 0, 0, 0),
        (-1.0, 0, 0, 0, 0, 0),
        (1.0, 0, 0, 0, 0, 0),
        (2.0, 0, 0, 0, 0, 0),
    ]
    y = [0, 0, 1, 1]
    a = HazardGate.fit(X, y, iters=300)
    b = HazardGate.fit(X, y, iters=300)
    assert a == b
    assert max(a.probability(x) for x in X[:2]) < min(a.probability(x) for x in X[2:])


def test_burst_scheduler_caps_duration_and_enforces_refractory():
    from stencil.ctrb import BurstScheduler

    policy = BurstScheduler(burst_tokens=4, refractory_tokens=8)
    assert policy.trigger(step=3, span=1)
    applied = [s for s in range(20) if policy.consume(s) is not None]
    assert applied == [3, 4, 5, 6]
    assert not policy.trigger(step=7, span=0)
    assert not policy.trigger(step=14, span=0)
    assert policy.trigger(step=15, span=0)


@pytest.mark.parametrize(
    "native,burst,expected",
    [
        ((False, True), (True, True), "helpful"),
        ((True, True), (False, True), "harmful"),
        ((True, False), (False, True), "neutral"),
    ],
)
def test_causal_label_supports_all_three_outcomes(native, burst, expected):
    from stencil.causal_moments import classify_scores

    label, delta = classify_scores(native, burst)
    assert label == expected
    assert delta == sum(burst) - sum(native)


@pytest.fixture(scope="module")
def gpu_setup():
    if not torch.cuda.is_available():
        pytest.skip("needs GPU")
    from pathlib import Path

    from tokenizers import Tokenizer

    from stencil.qwen3 import Qwen3
    from stencil.wave import WaveController

    root = Path(__file__).resolve().parent.parent
    tok = Tokenizer.from_file(str(root / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
    m = Qwen3()
    m.load_state_dict(
        torch.load(root / "models" / "qwen3-1.7b.pt", map_location="cpu"), strict=True
    )
    m = m.to(torch.bfloat16).cuda().eval()
    ctrl = WaveController(beta_max=1.0).cuda()
    ctrl.load_state_dict(
        torch.load(root / "results" / "qwen" / "b3-ce-s0.pt", map_location="cpu")
    )
    return m, tok, ctrl.eval()


PROMPT = (
    "Write a short note about rain.\n"
    "Constraint: Include the exact word 'cedar'.\n"
    "Constraint: End with the exact sentence 'The work is complete.'"
)


class _Encoding:
    def __init__(self, text):
        self.ids = [ord(c) % 31 + 1 for c in text]
        self.offsets = [(i, i + 1) for i in range(len(text))]


class _CharTokenizer:
    def encode(self, text):
        return _Encoding(text)

    def decode(self, ids):
        return "".join(chr(65 + int(i) % 26) for i in ids)


class _TinyTrunk(torch.nn.Module):
    """Consumer-path double: cache, h20 hook, multi-span probe, live bias."""

    def __init__(self):
        super().__init__()
        self.anchor = torch.nn.Parameter(torch.zeros(()), requires_grad=False)

    def forward(
        self,
        tokens,
        *,
        cache=None,
        capture_hidden=None,
        bias_hook=None,
        attn_probe=None,
        **_kwargs,
    ):
        t = tokens.shape[1]
        past = cache.length if cache is not None else 0
        pos = torch.arange(past, past + t, device=tokens.device).float()
        h20 = torch.stack((torch.ones_like(pos), (pos % 5) / 5), dim=-1)[None]
        field = bias_hook[1](h20) if bias_hook is not None else None
        focused = field is not None and float(field[20][-1].sum()) > 0
        logits = torch.zeros(1, t, 16, device=tokens.device)
        logits[..., 1] = 2.0
        if focused:
            logits[..., 2] = 3.0
        if attn_probe is not None:
            masks, sink = attn_probe
            vals = [float(row.sum()) / max(1, row.numel()) for row in masks]
            for layer in range(20, 28):
                sink[layer] = vals
        if cache is not None:
            cache.length = past + t
        return (logits, h20) if capture_hidden is not None else logits


class _TinyController(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.W_q = torch.nn.Identity()
        self.W_k = torch.nn.Identity()


def test_cpu_consumer_path_zero_equals_base_and_forced_bursts_repeat():
    from stencil.bench import generate_cached
    from stencil.ctrb import HazardGate, constraint_spans_of, generate_ctrb

    model, tok, ctrl = _TinyTrunk(), _CharTokenizer(), _TinyController()
    prompt = "Constraint: include cedar."
    spans = constraint_spans_of(tok, prompt)
    base = generate_cached(model, tok, prompt, max_new=20)
    zero = generate_ctrb(
        model,
        tok,
        prompt,
        ctrl,
        spans,
        HazardGate.constant(0),
        max_new=20,
        draft_tokens=0,
    )
    assert zero.text == base[0]
    assert zero.token_ids == (1,) * 20
    assert zero.n_generated == base[1]
    assert not zero.interventions
    forced_a = generate_ctrb(
        model,
        tok,
        prompt,
        ctrl,
        spans,
        HazardGate.constant(1),
        max_new=20,
        draft_tokens=0,
    )
    forced_b = generate_ctrb(
        model,
        tok,
        prompt,
        ctrl,
        spans,
        HazardGate.constant(1),
        max_new=20,
        draft_tokens=0,
    )
    assert forced_a == forced_b
    assert forced_a.text != zero.text
    assert any(x["kind"] == "apply" for x in forced_a.interventions)


def test_cpu_causal_branch_is_deterministic_and_actuator_live():
    from stencil.causal_moments import label_causal_moment
    from stencil.ctrb import constraint_spans_of

    model, tok = _TinyTrunk(), _CharTokenizer()
    prompt = "Constraint: include cedar."
    span = constraint_spans_of(tok, prompt)[0]

    def score(text):
        return ("C" in text,)

    kwargs = dict(
        model=model,
        tokenizer=tok,
        prompt=prompt,
        prefix_ids=[],
        selected_span=span,
        score_fn=score,
        max_new=12,
    )
    a = label_causal_moment(**kwargs)
    b = label_causal_moment(**kwargs)
    assert a == b
    assert a.native.continuation_ids != a.burst.continuation_ids
    assert a.label == "helpful"


def test_zero_hazard_generation_is_bitwise_base(gpu_setup):
    from stencil.bench import EOS, TMPL, generate_cached
    from stencil.ctrb import HazardGate, constraint_spans_of, generate_ctrb
    from stencil.qwen3 import KVCache

    m, tok, ctrl = gpu_setup
    base = generate_cached(m, tok, PROMPT, max_new=20)
    ids = tok.encode(TMPL.format(p=PROMPT)).ids
    cache, base_ids = KVCache(), []
    with torch.no_grad():
        logits = m(torch.tensor([ids], device="cuda"), cache=cache)
        nxt = int(logits[0, -1].argmax())
        while nxt not in EOS and len(base_ids) < 20:
            base_ids.append(nxt)
            logits = m(torch.tensor([[nxt]], device="cuda"), cache=cache)
            nxt = int(logits[0, -1].argmax())
    got = generate_ctrb(
        m,
        tok,
        PROMPT,
        ctrl,
        constraint_spans_of(tok, PROMPT),
        HazardGate.constant(0.0),
        max_new=20,
        draft_tokens=0,
    )
    assert got.text == base[0]
    assert got.token_ids == tuple(base_ids)
    assert got.n_generated == base[1]
    assert got.truncated == base[2]
    assert not got.interventions


def test_forced_span_bias_changes_logits_and_generator_repeats(gpu_setup):
    from stencil.bench import TMPL, WAVE_LAYERS
    from stencil.ctrb import (
        HazardGate,
        constraint_spans_of,
        generate_ctrb,
        uniform_span_bias,
    )

    m, tok, ctrl = gpu_setup
    ids = tok.encode(TMPL.format(p=PROMPT)).ids
    spans = constraint_spans_of(tok, PROMPT)
    b = uniform_span_bias(len(ids), len(ids), spans[0], amount=1.0, device="cuda")
    toks = torch.tensor([ids], device="cuda")
    with torch.no_grad():
        native = m(toks)[0, -1]
        focused = m(toks, attn_bias={layer: b for layer in WAVE_LAYERS})[0, -1]
    assert torch.isfinite(focused).all()
    assert not torch.equal(native, focused)

    kw = dict(max_new=20, threshold=0.5, draft_tokens=0)
    a = generate_ctrb(m, tok, PROMPT, ctrl, spans, HazardGate.constant(1.0), **kw)
    z = generate_ctrb(m, tok, PROMPT, ctrl, spans, HazardGate.constant(1.0), **kw)
    assert a == z
    applied = [e["step"] for e in a.interventions if e["kind"] == "apply"]
    assert applied
    # Every contiguous run is at most four tokens; successive starts are at
    # least eight clear tokens beyond the preceding burst.
    runs = []
    for step in applied:
        if not runs or step != runs[-1][-1] + 1:
            runs.append([step])
        else:
            runs[-1].append(step)
    assert all(len(run) <= 4 for run in runs)
    assert all(b[0] - a[-1] >= 9 for a, b in zip(runs, runs[1:]))  # offset pairs; strict zip breaks on a single run


def test_causal_moment_branches_repeat_bitwise(gpu_setup):
    from stencil.causal_moments import label_causal_moment
    from stencil.ctrb import constraint_spans_of

    m, tok, _ctrl = gpu_setup
    spans = constraint_spans_of(tok, PROMPT)

    def score(text):
        return "cedar" in text.lower(), text.rstrip().endswith("The work is complete.")

    kwargs = dict(
        model=m,
        tokenizer=tok,
        prompt=PROMPT,
        prefix_ids=[],
        selected_span=spans[0],
        score_fn=score,
        max_new=16,
        burst_tokens=4,
        dose=1.0,
    )
    a = label_causal_moment(**kwargs)
    b = label_causal_moment(**kwargs)
    assert a == b
    assert a.label in {"helpful", "harmful", "neutral"}
    assert len(a.native_scores) == 2 == len(a.burst_scores)
