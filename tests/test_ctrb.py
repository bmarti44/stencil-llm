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


def test_raw_context_matches_template_when_equivalent(gpu_setup):
    """E2 multi-turn support: raw_context=True consumes a PRE-RENDERED
    conversation string; passing the rendered single-turn template must
    reproduce the templated path bitwise."""
    from stencil.bench import TMPL
    from stencil.ctrb import HazardGate, constraint_spans_of, generate_ctrb
    m, tok, ctrl = gpu_setup
    spans = constraint_spans_of(tok, PROMPT)
    kw = dict(max_new=16, threshold=0.5, draft_tokens=0)
    a = generate_ctrb(m, tok, PROMPT, ctrl, spans, HazardGate.constant(0.0), **kw)
    b = generate_ctrb(m, tok, TMPL.format(p=PROMPT), ctrl, spans,
                      HazardGate.constant(0.0), raw_context=True, **kw)
    assert a.text == b.text and a.n_generated == b.n_generated


def test_causal_moment_accepts_raw_context(gpu_setup):
    from stencil.bench import TMPL
    from stencil.causal_moments import label_causal_moment
    from stencil.ctrb import constraint_spans_of
    m, tok, _ = gpu_setup
    spans = constraint_spans_of(tok, PROMPT)
    lab = label_causal_moment(
        model=m, tokenizer=tok, prompt=TMPL.format(p=PROMPT), prefix_ids=[],
        selected_span=spans[0], score_fn=lambda t: (("cedar" in t.lower()),),
        max_new=12, raw_context=True)
    assert lab.label in {"helpful", "harmful", "neutral"}


def test_context_spans_are_full_context_coordinates(gpu_setup):
    """E2 retraction fix: spans must index the PRE-RENDERED conversation,
    and the decoded span text must be the constraint sentence itself."""
    from stencil.ctrb import constraint_spans_in_context
    _, tok, _ = gpu_setup
    hist = ("<|im_start|>user\nWrite about rain. Constraint: mention cedar.<|im_end|>\n"
            "<|im_start|>assistant\nA reply about rain.<|im_end|>\n")
    ctx = hist + ("<|im_start|>user\nContinue. Constraint: end with 'Done.'<|im_end|>\n"
                  "<|im_start|>assistant\n<think>\n\n</think>\n\n")
    ids = tok.encode(ctx).ids
    all_spans = constraint_spans_in_context(tok, ctx)
    assert len(all_spans) == 2
    texts = [tok.decode(ids[a:b]) for a, b in all_spans]
    assert "cedar" in texts[0] and "Done." in texts[1]
    # NON-VACUITY (Opus FINDING-2): a span must not bleed past its own user
    # message into the assistant reply or the next turn
    for txt in texts:
        assert "assistant" not in txt, txt
        assert "<|im_end|>" not in txt, txt
        assert "im_start" not in txt, txt
        assert len(txt.split()) < 25, txt
    assert "Done." not in texts[0], texts[0]
    last = constraint_spans_in_context(tok, ctx, only_last_turn=True)
    assert len(last) == 1 and "Done." in tok.decode(ids[last[0][0]:last[0][1]])
    for a, b in all_spans:
        assert 0 <= a < b <= len(ids)


def test_extra_spans_add_bias_and_change_outcome(gpu_setup):
    """E2 oracle arms: extra_spans must actually add bias (multi-span
    sustained arm), not be silently ignored."""
    from stencil.bench import TMPL
    from stencil.causal_moments import rollout_from_prefix
    from stencil.ctrb import constraint_spans_of
    m, tok, _ = gpu_setup
    spans = constraint_spans_of(tok, PROMPT)
    common = dict(model=m, tokenizer=tok, prompt=TMPL.format(p=PROMPT), prefix_ids=[],
                  selected_span=spans[0], burst=True, dose=3.0, burst_tokens=10**6,
                  max_new=24, raw_context=True)
    one = rollout_from_prefix(**common)
    many = rollout_from_prefix(**common, extra_spans=tuple(spans[1:]))
    assert one.response != many.response  # the extra span reaches the logits


def test_e2_span_records_have_turn_origins_and_never_bleed(gpu_setup):
    from stencil.e2 import constraint_span_records

    _, tok, _ = gpu_setup
    ctx = (
        "<|im_start|>user\nTask one. Constraint: mention cedar.<|im_end|>\n"
        "<|im_start|>assistant\nA prior answer.<|im_end|>\n"
        "<|im_start|>user\nContinue. Constraint: end with Done. "
        "Constraint: use lowercase.<|im_end|>\n"
        "<|im_start|>assistant\n<think>\n\n</think>\n\n"
    )
    ids = tok.encode(ctx).ids
    recs = constraint_span_records(tok, ctx)
    assert [r["origin_turn"] for r in recs] == [1, 2, 2]
    assert [r["is_aged"] for r in recs] == [True, False, False]
    for r in recs:
        a, b = r["span"]
        text = tok.decode(ids[a:b])
        assert "assistant" not in text
        assert "<|im_end|>" not in text
        assert 0 <= a < b <= len(ids)


def test_e2_candidate_sampling_is_fixed_conflict_plus_temporal_union():
    from stencil.e2 import select_candidate_records

    trace = []
    for step in range(12):
        # All records are eligible. Conflict rank is deliberately unrelated
        # to temporal order so the union's two sources are both exercised.
        trace.append(
            {
                "step": step,
                "features": (float(20 - abs(step - 7)), 0, 0, 0, 0, 0),
                "prefix_ids": tuple(range(step)),
                "selected_span": step % 3,
            }
        )
    got = select_candidate_records(trace, top_k=2, temporal_k=4)
    steps = [r["step"] for r in got]
    # Temporal endpoints are present; conflict peak 7 is present; no dupes;
    # output is chronological so resume filenames are stable.
    assert 0 in steps and 11 in steps and 7 in steps
    assert len(steps) == len(set(steps))
    assert steps == sorted(steps)


def test_e2_opus_arm_specs_are_exact_and_control_excludes_constraints():
    from stencil.e2 import arm_specs, matched_nonconstraint_spans

    spans = [(10, 15), (30, 36), (50, 54)]
    control = matched_nonconstraint_spans(total_len=70, spans=spans, width=15)
    assert sum(b - a for a, b in control) == 15
    assert all(b <= x or y <= a for a, b in control for x, y in spans)
    specs = arm_specs(spans, selected_span=1, aged_indices=[0], control_spans=control)
    assert specs["registered"]["spans"] == ((30, 36),)
    assert specs["registered"]["dose"] == 1.0
    assert specs["registered"]["burst_tokens"] == 4
    assert specs["sustained_all"]["spans"] == tuple(spans)
    assert specs["sustained_all"]["dose"] == 3.0
    assert specs["sustained_all"]["burst_tokens"] > 1_000
    assert specs["sustained_aged"]["spans"] == ((10, 15),)
    assert specs["control"]["spans"] == tuple(control)


def test_e2_moment_record_schema_and_label_nonvacuity():
    from stencil.e2 import make_branch_record, make_moment_record

    native = make_branch_record("native reply", (True, False), 12, False, False)
    focused = make_branch_record("focused reply", (True, True), 13, False, False)
    harmful = make_branch_record("harmful reply", (False, False), 11, False, False)
    rec = make_moment_record(
        session=3,
        turn=2,
        step=9,
        features=(1, 2, 3, 4, 5, 6),
        response_position=0.25,
        selected_span=1,
        selected_origin=1,
        topic="topic",
        changed_family=("kw_exist",),
        native=native,
        arms={"sustained_all": focused, "control": harmful},
    )
    assert rec["label"] == "helpful"
    assert rec["utility_delta"] == 1
    assert len(rec["features"]) == 6
    assert rec["native"]["response_sha256"] != rec["arms"]["sustained_all"]["response_sha256"]
    assert rec["arms"]["control"]["label_vs_native"] == "harmful"
    assert "response" in rec["native"] and "response" in rec["arms"]["sustained_all"]


def test_e2_oracle_summary_derives_arm_best_without_phantom_field():
    from stencil.e2 import summarize_oracle_records

    records = [
        {
            "n_constraints": 2,
            "native_pass": 1,
            "oracle_best_pass": 2,
            "oracle_gain": 1,
            "trials": [
                {"arm": "registered", "n_pass": 1},
                {"arm": "sustained_all", "n_pass": 2},
            ],
        },
        {
            "n_constraints": 1,
            "native_pass": 0,
            "oracle_best_pass": 0,
            "oracle_gain": 0,
            "trials": [{"arm": "registered", "n_pass": 0}],
        },
    ]
    got = summarize_oracle_records(records, ("registered", "sustained_all"))
    assert got["native_pass_rate"] == pytest.approx(1 / 3)
    assert got["oracle_pass_rate"] == pytest.approx(2 / 3)
    assert got["by_arm_pass_rate"]["registered"] == pytest.approx(1 / 3)
    # Missing trials fail closed to native, rather than a nonexistent
    # precomputed `by_arm` field (the old aggregate-path crash).
    assert got["by_arm_pass_rate"]["sustained_all"] == pytest.approx(2 / 3)


def test_exact_kv_branch_native_reproduces_committed_trajectory(gpu_setup):
    """Causal labels must branch from the same prompt-once/token-at-a-time
    numerical path used by deployment, not a full prompt+prefix recompute."""
    from stencil.causal_moments import rollout_arms_from_prefix_exact
    from stencil.ctrb import HazardGate, constraint_spans_of, generate_ctrb

    model, tok, ctrl = gpu_setup
    spans = constraint_spans_of(tok, PROMPT)
    native = generate_ctrb(
        model,
        tok,
        PROMPT,
        ctrl,
        spans,
        HazardGate.constant(0),
        max_new=24,
        draft_tokens=0,
        collect_prefixes=True,
    )
    candidate = next(r for r in native.trace if r["step"] == 8)
    specs = {
        "registered": {
            "spans": (spans[candidate["selected_span"]],),
            "dose": 1.0,
            "burst_tokens": 4,
        }
    }
    first = rollout_arms_from_prefix_exact(
        model=model,
        tokenizer=tok,
        prompt=PROMPT,
        prefix_ids=candidate["prefix_ids"],
        arm_specs=specs,
        max_new=24,
    )
    second = rollout_arms_from_prefix_exact(
        model=model,
        tokenizer=tok,
        prompt=PROMPT,
        prefix_ids=candidate["prefix_ids"],
        arm_specs=specs,
        max_new=24,
    )
    assert first == second
    assert first["native"].response == native.text
    assert len(first["native"].continuation_ids) == 24 - len(candidate["prefix_ids"])
