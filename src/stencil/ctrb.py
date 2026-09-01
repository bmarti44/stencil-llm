# ruff: noqa: E501
"""Conflict-Triggered Readout Bursts (CTRB).

The frozen wave controller supplies *where* (a q/k readout over prompt
constraint spans).  A six-feature trajectory probe supplies *when*.  A fire
adds a fixed, contentless +1 attention-logit bias to one selected prompt span
at layers 20--27 for at most four generated tokens, followed by at least eight
clear tokens.  No verifier is used at inference.

This module is intentionally side-effect free: callers provide the frozen
trunk, tokenizer, controller, and fitted hazard gate.
"""

from __future__ import annotations

import math
import time
from collections.abc import Sequence
from dataclasses import dataclass

FEATURE_NAMES = (
    "delta5_conflict",
    "delta5_entropy",
    "neg_delta5_margin",
    "span_attention",
    "delta5_span_attention",
    "address_stability",
)
WAVE_LAYERS = range(20, 28)


def _model_device(model):
    try:
        return next(model.parameters()).device
    except (StopIteration, AttributeError):
        # Test doubles may expose a device without parameters.
        return getattr(model, "device", "cpu")


@dataclass(frozen=True)
class StepObservation:
    conflict: float
    entropy: float
    margin: float
    attention: float
    selected_span: int


def distribution_observation(
    logits, attention: float, selected_span: int, top_k: int = 8
) -> StepObservation:
    """Distribution statistics used by the registered trajectory vector.

    Conflict energy is the pair mass among the top-k alternatives,
    ``sum_{i<j} p_i p_j``.  Unlike entropy it concentrates on simultaneously
    live competitors rather than the long vocabulary tail.
    """
    import torch

    p = torch.softmax(logits.float(), dim=-1)
    k = min(top_k, p.numel())
    top = p.topk(k).values
    conflict = 0.5 * (top.sum().square() - top.square().sum())
    entropy = -(p * p.clamp_min(1e-30).log()).sum()
    two = p.topk(min(2, p.numel())).values
    margin = two[0] - (two[1] if two.numel() > 1 else 0.0)
    return StepObservation(
        float(conflict),
        float(entropy),
        float(margin),
        float(attention),
        int(selected_span),
    )


def trajectory_vector(
    history: Sequence[StepObservation], current: StepObservation, delta: int = 5
) -> tuple[float, ...] | None:
    """Six features at one step, or ``None`` until a delta-step baseline exists.

    Address stability is the fraction of the preceding ``delta`` selections
    equal to the current selection.  It is bounded, scale-free, and explicitly
    distinguishes a stable readout from q/k argmax thrashing.
    """
    if len(history) < delta:
        return None
    old = history[-delta]
    recent = history[-delta:]
    stability = sum(x.selected_span == current.selected_span for x in recent) / delta
    return (
        current.conflict - old.conflict,
        current.entropy - old.entropy,
        -(current.margin - old.margin),
        current.attention,
        current.attention - old.attention,
        stability,
    )


@dataclass(frozen=True)
class HazardGate:
    """Standardized deterministic logistic hazard probe."""

    mean: tuple[float, ...]
    scale: tuple[float, ...]
    weights: tuple[float, ...]
    bias: float

    @classmethod
    def constant(cls, probability: float) -> HazardGate:
        if not 0.0 <= probability <= 1.0:
            raise ValueError("probability must be in [0,1]")
        if probability == 0.0:
            b = -60.0
        elif probability == 1.0:
            b = 60.0
        else:
            b = math.log(probability / (1.0 - probability))
        return cls((0.0,) * 6, (1.0,) * 6, (0.0,) * 6, b)

    @classmethod
    def fit(
        cls,
        features: Sequence[Sequence[float]],
        labels: Sequence[int],
        *,
        l2: float = 1.0,
        iters: int = 500,
        lr: float = 0.1,
        seed: int = 0,
    ) -> HazardGate:
        """Zero-init full-batch GD, matching the deterministic EVF discipline."""
        del seed  # retained to make the determinism contract explicit
        if not features or len(features) != len(labels):
            raise ValueError("nonempty, equally-sized features and labels required")
        d = len(features[0])
        if d != len(FEATURE_NAMES) or any(len(x) != d for x in features):
            raise ValueError(
                f"every feature vector must have {len(FEATURE_NAMES)} values"
            )
        if any(y not in (0, 1) for y in labels):
            raise ValueError("labels must be binary")
        n = len(features)
        mean = tuple(sum(float(x[j]) for x in features) / n for j in range(d))
        scale = tuple(
            (sum((float(x[j]) - mean[j]) ** 2 for x in features) / n) ** 0.5 or 1.0
            for j in range(d)
        )
        X = [
            tuple((float(x[j]) - mean[j]) / scale[j] for j in range(d))
            for x in features
        ]
        w = [0.0] * d
        b = 0.0
        for _ in range(iters):
            gw = [l2 * v / n for v in w]
            gb = 0.0
            for x, y in zip(X, labels, strict=True):
                z = sum(a * q for a, q in zip(w, x, strict=True)) + b
                p = 1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, z))))
                err = p - y
                for j in range(d):
                    gw[j] += err * x[j] / n
                gb += err / n
            w = [v - lr * g for v, g in zip(w, gw, strict=True)]
            b -= lr * gb
        return cls(mean, scale, tuple(w), b)

    def probability(self, features: Sequence[float]) -> float:
        if len(features) != len(self.weights):
            raise ValueError("feature width mismatch")
        z = self.bias + sum(
            w * (float(x) - m) / s
            for w, x, m, s in zip(
                self.weights, features, self.mean, self.scale, strict=True
            )
        )
        return 1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, z))))


class BurstScheduler:
    """Mechanical <=N-token burst and post-burst refractory state machine."""

    def __init__(self, burst_tokens: int = 4, refractory_tokens: int = 8):
        if burst_tokens < 1 or refractory_tokens < 0:
            raise ValueError("invalid burst/refractory length")
        self.burst_tokens = burst_tokens
        self.refractory_tokens = refractory_tokens
        self._start = -1
        self._remaining = 0
        self._span: int | None = None
        self._next_allowed = 0

    def trigger(self, step: int, span: int) -> bool:
        if self._remaining or step < self._next_allowed:
            return False
        self._start = step
        self._remaining = self.burst_tokens
        self._span = int(span)
        return True

    def consume(self, step: int) -> int | None:
        if not self._remaining or step < self._start:
            return None
        span = self._span
        self._remaining -= 1
        if self._remaining == 0:
            # If the last applied step is s, the first legal new start is
            # s + refractory + 1: exactly `refractory` clear intervening tokens.
            self._next_allowed = step + self.refractory_tokens + 1
            self._span = None
        return span

    @property
    def next_allowed(self) -> int:
        return self._next_allowed


@dataclass(frozen=True)
class CTRBResult:
    text: str
    token_ids: tuple[int, ...]
    n_generated: int
    truncated: bool
    timed_out: bool
    interventions: tuple[dict, ...]
    trace: tuple[dict, ...]


def constraint_spans_of(tokenizer, prompt: str) -> list[tuple[int, int]]:
    """Token spans of all ``Constraint:`` sentences in the chat prompt."""
    from stencil.bench import TMPL

    rendered = TMPL.format(p=prompt)
    enc = tokenizer.encode(rendered)
    spans: list[tuple[int, int]] = []
    start = 0
    while True:
        i = rendered.find("Constraint:", start)
        if i < 0:
            break
        nxt = rendered.find("Constraint:", i + 1)
        end = nxt if nxt >= 0 else rendered.find("<|im_end|>", i)
        ids = [j for j, (a, b) in enumerate(enc.offsets) if a < end and b > i]
        if ids:
            spans.append((ids[0], ids[-1] + 1))
        start = i + 1
    return spans


def uniform_span_bias(
    query_len: int,
    total_len: int,
    span: tuple[int, int],
    *,
    amount: float = 1.0,
    device=None,
):
    """A last-row-only uniform attention-logit bias over one prompt span."""
    import torch

    a, b = span
    if not (0 <= a < b <= total_len):
        raise ValueError("span lies outside attention key axis")
    out = torch.zeros(query_len, total_len, device=device)
    out[-1, a:b] = amount
    return out


def _span_masks(spans, total, device):
    import torch

    masks = torch.zeros((len(spans), total), dtype=torch.bool, device=device)
    for i, (a, b) in enumerate(spans):
        masks[i, a:b] = True
    return masks


def _mean_span_attention(sink: dict, n_spans: int) -> list[float]:
    rows = [v for _, v in sorted(sink.items())]
    if not rows:
        return [0.0] * n_spans
    return [sum(float(row[j]) for row in rows) / len(rows) for j in range(n_spans)]


def _select_span(ctrl, query_h20, prompt_keys, spans):
    import torch.nn.functional as F

    q = F.normalize(ctrl.W_q(query_h20.float()), dim=-1)
    k = F.normalize(ctrl.W_k(prompt_keys.float()), dim=-1)
    token_scores = (q @ k.T)[0]
    scores = [float(token_scores[a:b].mean()) for a, b in spans]
    best = max(range(len(spans)), key=lambda i: (scores[i], -i))
    return best, scores


def _native_draft_confirms(
    model,
    ctrl,
    full_ids,
    first_token,
    prompt_len,
    spans,
    history,
    hazard_gate,
    threshold,
    draft_tokens,
):
    """Discarded native draft; require the hazard to persist at its last step.

    This path intentionally recomputes the short draft without a KV cache.  It
    cannot mutate the committed cache and is optional (``draft_tokens=0``).
    """
    import torch

    from stencil.bench import EOS

    if first_token in EOS:
        return False
    device = _model_device(model)
    # The candidate forward already produced the first native token.  Seed
    # the discarded draft with it, then measure after each of exactly
    # `draft_tokens` drafted tokens instead of measuring the candidate twice.
    trial = list(full_ids) + [int(first_token)]
    hist = list(history)
    last_p = 0.0
    for draft_i in range(draft_tokens):
        toks = torch.tensor([trial], device=device)
        masks = _span_masks(spans, len(trial), toks.device)
        sink = {}
        with torch.no_grad():
            logits, h20 = model(toks, capture_hidden=20, attn_probe=(masks, sink))
        best, _ = _select_span(ctrl, h20[0, -1:], h20[0, :prompt_len], spans)
        masses = _mean_span_attention(sink, len(spans))
        obs = distribution_observation(logits[0, -1], masses[best], best)
        vec = trajectory_vector(hist, obs)
        hist.append(obs)
        if vec is not None:
            last_p = hazard_gate.probability(vec)
        if draft_i == draft_tokens - 1:
            break
        nxt = int(logits[0, -1].argmax())
        if nxt in EOS:
            break
        trial.append(nxt)
    return last_p >= threshold


def generate_ctrb(
    model,
    tokenizer,
    prompt: str,
    ctrl,
    prompt_spans,
    hazard_gate: HazardGate,
    *,
    threshold: float = 0.5,
    dose: float = 1.0,
    burst_tokens: int = 4,
    refractory_tokens: int = 8,
    draft_tokens: int = 4,
    max_new: int = 1024,
    deadline_s: float | None = None,
    collect_prefixes: bool = False,
    raw_context: bool = False,
) -> CTRBResult:
    """KV-cached greedy generation with automatic conflict-triggered bursts.

    A hazard measured on step ``t`` schedules a burst beginning at ``t+1``;
    this preserves a single committed cache.  The optional discarded native
    draft confirms that the hazard persists before the burst is scheduled.
    """
    import torch

    from stencil.bench import EOS, TMPL
    from stencil.qwen3 import KVCache

    spans = [tuple(x) for x in prompt_spans]
    if not spans:
        raise ValueError("CTRB requires at least one prompt span")
    ids = tokenizer.encode(prompt if raw_context else TMPL.format(p=prompt)).ids
    device = _model_device(model)
    prompt_len = len(ids)
    cache = KVCache()
    out: list[int] = []
    history: list[StepObservation] = []
    trace: list[dict] = []
    events: list[dict] = []
    scheduler = BurstScheduler(burst_tokens, refractory_tokens)
    prompt_keys = None
    current = list(ids)
    t0 = time.monotonic()
    timed_out = False

    with torch.no_grad():
        for step in range(max_new + 1):
            if deadline_s is not None and time.monotonic() - t0 > deadline_s:
                timed_out = True
                break
            active_span = scheduler.consume(step)
            total = cache.length + len(current)
            masks = _span_masks(spans, total, device)
            sink = {}

            def hook(h20, active_span=active_span, total=total):
                nonlocal prompt_keys
                if prompt_keys is None:
                    prompt_keys = h20[0, :prompt_len].float()
                if active_span is None:
                    return None
                row = uniform_span_bias(
                    h20.shape[1],
                    total,
                    spans[active_span],
                    amount=dose,
                    device=h20.device,
                )
                return {layer: row for layer in WAVE_LAYERS}

            logits, h20 = model(
                torch.tensor([current], device=device),
                cache=cache,
                capture_hidden=20,
                bias_hook=(20, hook),
                attn_probe=(masks, sink),
            )
            if active_span is not None:
                events.append({"kind": "apply", "step": step, "span": active_span})
            best, scores = _select_span(ctrl, h20[0, -1:], prompt_keys, spans)
            masses = _mean_span_attention(sink, len(spans))
            obs = distribution_observation(logits[0, -1], masses[best], best)
            vec = trajectory_vector(history, obs)
            history.append(obs)
            rec = {
                "step": step,
                "selected_span": best,
                "span_scores": tuple(scores),
                "features": vec,
                "hazard": None,
            }
            nxt = int(logits[0, -1].argmax())
            if collect_prefixes and vec is not None:
                rec["prefix_ids"] = tuple(out)
            if vec is not None and active_span is None:
                p = hazard_gate.probability(vec)
                rec["hazard"] = p
                confirmed = p >= threshold
                if confirmed and draft_tokens:
                    confirmed = _native_draft_confirms(
                        model,
                        ctrl,
                        ids + out,
                        nxt,
                        prompt_len,
                        spans,
                        history,
                        hazard_gate,
                        threshold,
                        draft_tokens,
                    )
                if confirmed and scheduler.trigger(step + 1, best):
                    events.append(
                        {
                            "kind": "trigger",
                            "step": step,
                            "start": step + 1,
                            "span": best,
                            "hazard": p,
                        }
                    )
            trace.append(rec)
            if nxt in EOS or len(out) >= max_new:
                break
            out.append(nxt)
            current = [nxt]

    return CTRBResult(
        tokenizer.decode(out),
        tuple(out),
        len(out),
        len(out) >= max_new,
        timed_out,
        tuple(events),
        tuple(trace),
    )
