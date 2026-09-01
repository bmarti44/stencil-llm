# ruff: noqa: E501
"""Deterministic causal-moment branch rollouts for CTRB hazard labels."""

from __future__ import annotations

import random
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class BranchRollout:
    response: str
    continuation_ids: tuple[int, ...]
    truncated: bool
    timed_out: bool


@dataclass(frozen=True)
class CausalMomentLabel:
    label: str
    utility_delta: int
    native_scores: tuple[bool, ...]
    burst_scores: tuple[bool, ...]
    native: BranchRollout
    burst: BranchRollout


def classify_scores(
    native_scores: Sequence[bool], burst_scores: Sequence[bool]
) -> tuple[str, int]:
    """Map a per-constraint utility difference to the three causal labels."""
    if len(native_scores) != len(burst_scores):
        raise ValueError("branch scorer changed output width")
    delta = sum(bool(x) for x in burst_scores) - sum(bool(x) for x in native_scores)
    return ("helpful" if delta > 0 else "harmful" if delta < 0 else "neutral"), delta


def score_row_constraints(row: dict, response: str) -> tuple[bool, ...]:
    """Vendored deterministic per-constraint checker outcomes."""
    from ifeval import instructions_registry

    from stencil.bench import ifeval_utils  # establishes pinned vendor path

    del ifeval_utils  # import is deliberate: it pins langdetect and vendor path
    random.seed(row["key"])
    scores = []
    for iid, kw in zip(row["instruction_id_list"], row["kwargs"], strict=True):
        inst = instructions_registry.INSTRUCTION_DICT[iid](iid)
        inst.build_description(**{k: v for k, v in kw.items() if v})
        scores.append(bool(response.strip() and inst.check_following(response)))
    return tuple(scores)


def rollout_from_prefix(
    model,
    tokenizer,
    prompt: str,
    prefix_ids: Sequence[int],
    selected_span: tuple[int, int],
    *,
    burst: bool,
    dose: float = 1.0,
    burst_tokens: int = 4,
    extra_spans: tuple = (),
    max_new: int = 1024,
    deadline_s: float | None = None,
    raw_context: bool = False,
) -> BranchRollout:
    """Roll a frozen prefix to EOS/max_new, optionally bursting immediately."""
    import torch

    from stencil.bench import EOS, TMPL, WAVE_LAYERS
    from stencil.ctrb import _model_device, uniform_span_bias
    from stencil.qwen3 import KVCache

    prompt_ids = tokenizer.encode(prompt if raw_context else TMPL.format(p=prompt)).ids
    device = _model_device(model)
    frozen = list(prefix_ids)
    initial = prompt_ids + frozen
    cache = KVCache()
    continuation: list[int] = []
    current = initial
    t0 = time.monotonic()
    timed_out = False
    forward_step = 0

    with torch.no_grad():
        while len(frozen) + len(continuation) < max_new:
            if deadline_s is not None and time.monotonic() - t0 > deadline_s:
                timed_out = True
                break
            total = cache.length + len(current)

            def hook(h20, forward_step=forward_step, total=total):
                if not burst or forward_step >= burst_tokens:
                    return None
                row = uniform_span_bias(
                    h20.shape[1], total, selected_span, amount=dose, device=h20.device
                )
                for _sp in extra_spans:  # multi-span sustained arms (E2 oracle)
                    row = row + uniform_span_bias(
                        h20.shape[1], total, tuple(_sp), amount=dose, device=h20.device
                    )
                return {layer: row for layer in WAVE_LAYERS}

            logits = model(
                torch.tensor([current], device=device),
                cache=cache,
                bias_hook=(20, hook) if burst else None,
            )
            nxt = int(logits[0, -1].argmax())
            forward_step += 1
            if nxt in EOS:
                break
            continuation.append(nxt)
            current = [nxt]

    all_response_ids = frozen + continuation
    return BranchRollout(
        tokenizer.decode(all_response_ids),
        tuple(continuation),
        len(all_response_ids) >= max_new,
        timed_out,
    )


def label_causal_moment(
    *,
    model,
    tokenizer,
    prompt: str,
    prefix_ids: Sequence[int],
    selected_span: tuple[int, int],
    score_fn: Callable[[str], Sequence[bool]],
    dose: float = 1.0,
    burst_tokens: int = 4,
    max_new: int = 1024,
    deadline_s: float | None = None,
    raw_context: bool = False,
) -> CausalMomentLabel:
    """Native A=0 vs one-burst A=1 label from per-constraint utility."""
    common = dict(
        model=model,
        tokenizer=tokenizer,
        prompt=prompt,
        prefix_ids=prefix_ids,
        selected_span=selected_span,
        dose=dose,
        burst_tokens=burst_tokens,
        max_new=max_new,
        deadline_s=deadline_s,
        raw_context=raw_context,
    )
    native = rollout_from_prefix(**common, burst=False)
    focused = rollout_from_prefix(**common, burst=True)
    native_scores = tuple(bool(x) for x in score_fn(native.response))
    burst_scores = tuple(bool(x) for x in score_fn(focused.response))
    label, delta = classify_scores(native_scores, burst_scores)
    return CausalMomentLabel(label, delta, native_scores, burst_scores, native, focused)
