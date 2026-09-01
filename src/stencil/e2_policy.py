"""Frozen sustained E2 policy and its registered evaluation ablations."""

from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass(frozen=True)
class E2PolicyResult:
    text: str
    token_ids: tuple[int, ...]
    n_generated: int
    truncated: bool
    timed_out: bool
    interventions: tuple[dict, ...]
    trace: tuple[dict, ...]
    biased_tokens: int


def generate_e2_policy(
    model,
    tokenizer,
    prompt: str,
    ctrl,
    span_records,
    *,
    mode: str,
    gate=None,
    threshold: float = 0.5,
    dose: float = 3.0,
    periodic_onset: int | None = None,
    max_new: int = 1024,
    deadline_s: float | None = None,
    raw_context: bool = False,
) -> E2PolicyResult:
    """Generate under native, CTRB, periodic, or fixed-oldest policy.

    CTRB and fixed-oldest share the frozen six-feature trigger.  CTRB targets
    every live constraint span after one onset; fixed-oldest targets only the
    constraints originating in the oldest user turn.  Periodic consumes no
    conflict features and uses a frozen onset step.
    """
    import torch

    from stencil.bench import EOS, TMPL
    from stencil.ctrb import (
        WAVE_LAYERS,
        StepObservation,
        _mean_span_attention,
        _model_device,
        _select_span,
        _span_masks,
        distribution_observation,
        trajectory_vector,
        uniform_span_bias,
    )
    from stencil.qwen3 import KVCache

    if mode not in {"native", "ctrb", "fixed_oldest", "periodic"}:
        raise ValueError(f"unknown E2 mode {mode}")
    if mode in {"ctrb", "fixed_oldest"} and (gate is None or ctrl is None):
        raise ValueError("learned modes require controller and gate")
    if mode == "periodic" and (periodic_onset is None or periodic_onset < 0):
        raise ValueError("periodic mode requires a nonnegative onset")
    records = [dict(record) for record in span_records]
    spans = [tuple(record["span"]) for record in records]
    if not spans:
        raise ValueError("at least one live constraint span required")
    oldest = min(int(record["origin_turn"]) for record in records)
    oldest_spans = [
        span
        for span, record in zip(spans, records, strict=True)
        if int(record["origin_turn"]) == oldest
    ]
    ids = tokenizer.encode(prompt if raw_context else TMPL.format(p=prompt)).ids
    prompt_len = len(ids)
    device = _model_device(model)
    cache = KVCache()
    out = []
    history: list[StepObservation] = []
    trace = []
    events = []
    prompt_keys = None
    current = list(ids)
    onset = periodic_onset if mode == "periodic" else None
    onset_logged = False
    biased_tokens = 0
    started = time.monotonic()
    timed_out = False

    with torch.no_grad():
        for step in range(max_new):
            if deadline_s is not None and time.monotonic() - started > deadline_s:
                timed_out = True
                break
            active = onset is not None and step >= onset and mode != "native"
            if active and mode == "fixed_oldest":
                target_spans = oldest_spans
            elif active:
                target_spans = spans
            else:
                target_spans = []
            total = cache.length + len(current)
            need_features = mode in {"ctrb", "fixed_oldest"}
            masks = _span_masks(spans, total, device) if need_features else None
            sink = {}

            def hook(
                h20,
                total=total,
                target_spans=tuple(target_spans),
                need_features=need_features,
            ):
                nonlocal prompt_keys
                if prompt_keys is None and need_features:
                    prompt_keys = h20[0, :prompt_len].float()
                if not target_spans:
                    return None
                row = uniform_span_bias(
                    h20.shape[1],
                    total,
                    target_spans[0],
                    amount=dose,
                    device=h20.device,
                )
                for span in target_spans[1:]:
                    row = row + uniform_span_bias(
                        h20.shape[1], total, span, amount=dose, device=h20.device
                    )
                return {layer: row for layer in WAVE_LAYERS}

            if need_features:
                logits, h20 = model(
                    torch.tensor([current], device=device),
                    cache=cache,
                    capture_hidden=20,
                    bias_hook=(20, hook),
                    attn_probe=(masks, sink),
                )
                best, scores = _select_span(
                    ctrl, h20[0, -1:], prompt_keys, spans
                )
                masses = _mean_span_attention(sink, len(spans))
                observation = distribution_observation(
                    logits[0, -1], masses[best], best
                )
                vector = trajectory_vector(history, observation)
                history.append(observation)
                hazard = None if vector is None else gate.probability(vector)
                trace.append(
                    {
                        "step": step,
                        "selected_span": best,
                        "selected_origin": int(records[best]["origin_turn"]),
                        "span_scores": tuple(scores),
                        "features": vector,
                        "hazard": hazard,
                    }
                )
                if onset is None and hazard is not None and hazard >= threshold:
                    onset = step + 1
                    targets = records if mode == "ctrb" else [
                        record
                        for record in records
                        if int(record["origin_turn"]) == oldest
                    ]
                    events.append(
                        {
                            "kind": "onset",
                            "step": step,
                            "start": onset,
                            "selected_span": best,
                            "selected_origin": int(records[best]["origin_turn"]),
                            "target_origins": sorted(
                                {int(record["origin_turn"]) for record in targets}
                            ),
                            "hazard": hazard,
                        }
                    )
                    onset_logged = True
            else:
                logits = model(
                    torch.tensor([current], device=device),
                    cache=cache,
                    bias_hook=(20, hook) if mode == "periodic" else None,
                )
            if active and not onset_logged:
                events.append(
                    {
                        "kind": "onset",
                        "step": step - 1,
                        "start": onset,
                        "selected_span": None,
                        "selected_origin": None,
                        "target_origins": sorted(
                            {int(record["origin_turn"]) for record in records}
                        ),
                        "hazard": None,
                    }
                )
                onset_logged = True
            next_token = int(logits[0, -1].argmax())
            if active:
                biased_tokens += 1
            if next_token in EOS:
                break
            out.append(next_token)
            current = [next_token]

    return E2PolicyResult(
        tokenizer.decode(out),
        tuple(out),
        len(out),
        len(out) >= max_new,
        timed_out,
        tuple(events),
        tuple(trace),
        biased_tokens,
    )
