"""Function-vector construction, injection, and registered result summaries."""

from __future__ import annotations

import re
import time
from collections.abc import Iterable, Sequence
from typing import Any

import torch

PREREGISTERED_READING = {
    "helps": "fv_inject >= 30/56; paired wins > losses vs evicted; not killed",
    "strong": "fv_inject_echo > 46/56; paired wins > losses; not killed",
    "harmful": "killed or fv_inject < evicted + 5",
}


def _constraint_clauses(prompt: str) -> list[str]:
    starts = [match.start() for match in re.finditer(r"(?<!\w)Constraint:", prompt)]
    return [
        prompt[
            start : starts[index + 1] if index + 1 < len(starts) else len(prompt)
        ].strip()
        for index, start in enumerate(starts)
    ]


def _without_clause(prompt: str, clause: str) -> str:
    start = prompt.index(clause)
    end = start + len(clause)
    return (prompt[:start].rstrip() + " " + prompt[end:].lstrip()).strip()


def build_minimal_pairs(
    rows: Iterable[dict[str, Any]],
    constraint_types: Iterable[str],
    *,
    n_per_type: int,
) -> dict[str, list[dict[str, Any]]]:
    """Build deterministic same-prompt pairs with one exact clause removed."""
    if n_per_type < 1:
        raise ValueError("n_per_type must be positive")
    requested = tuple(dict.fromkeys(constraint_types))
    pairs = {constraint_type: [] for constraint_type in requested}
    for row in rows:
        combo = row["combo"]
        clauses = _constraint_clauses(row["prompt"])
        if len(combo) != len(clauses):
            raise ValueError(
                f"row {row.get('key')} constraint clause count "
                f"{len(clauses)} != combo count {len(combo)}"
            )
        for constraint_type, clause in zip(combo, clauses, strict=True):
            if (
                constraint_type not in pairs
                or len(pairs[constraint_type]) >= n_per_type
            ):
                continue
            pairs[constraint_type].append(
                {
                    "source_key": row["key"],
                    "constraint_type": constraint_type,
                    "constraint_sentence": clause,
                    "with_prompt": row["prompt"],
                    "without_prompt": _without_clause(row["prompt"], clause),
                }
            )
    for constraint_type, type_pairs in pairs.items():
        if len(type_pairs) < n_per_type:
            raise ValueError(
                f"{constraint_type} has {len(type_pairs)} pairs; {n_per_type} required"
            )
    return pairs


def mean_difference(
    with_states: Sequence[torch.Tensor], without_states: Sequence[torch.Tensor]
) -> torch.Tensor:
    """Mean(with) - mean(without), accumulated in fp32."""
    if not with_states or len(with_states) != len(without_states):
        raise ValueError("paired, non-empty state sequences required")
    with_stack = torch.stack([state.detach().float() for state in with_states])
    without_stack = torch.stack([state.detach().float() for state in without_states])
    if with_stack.shape != without_stack.shape:
        raise ValueError("with/without state shapes differ")
    return with_stack.mean(dim=0) - without_stack.mean(dim=0)


def make_residual_hook(
    vector: torch.Tensor,
    *,
    alpha: float,
    layer: int,
    generated_position: int,
    clear_after: int | None = None,
    event_sink: list[dict[str, int]] | None = None,
):
    """Return a Qwen layer-input hook, or ``None`` when exactly inert."""
    if layer < 0 or generated_position < 0:
        raise ValueError("layer and generated_position must be nonnegative")
    if clear_after is not None and clear_after < 0:
        raise ValueError("clear_after must be nonnegative")
    if alpha == 0.0 or not bool(torch.count_nonzero(vector)):
        return None
    if clear_after is not None and generated_position >= clear_after:
        return None

    def inject(hidden: torch.Tensor) -> torch.Tensor:
        if hidden.shape[-1] != vector.numel():
            raise ValueError(
                f"function vector width {vector.numel()} != "
                f"hidden width {hidden.shape[-1]}"
            )
        if event_sink is not None:
            event_sink.append(
                {"layer": int(layer), "generated_position": int(generated_position)}
            )
        addition = vector.to(device=hidden.device, dtype=hidden.dtype)
        delta = torch.zeros_like(hidden)
        delta[:, -1, :] = addition * alpha
        return hidden + delta

    return layer, inject


def combine_vectors(
    vectors: dict[tuple[str, int], torch.Tensor],
    constraint_types: Iterable[str],
    layer: int,
) -> tuple[torch.Tensor | None, list[str]]:
    """Sum known type vectors once each and report unknown occurrences."""
    additions = []
    unknown = []
    for constraint_type in constraint_types:
        vector = vectors.get((constraint_type, layer))
        if vector is None:
            unknown.append(constraint_type)
        else:
            additions.append(vector)
    return (torch.stack(additions).sum(0) if additions else None), unknown


def cosine_similarity_report(
    vectors: dict[tuple[str, int], torch.Tensor], layers: Iterable[int]
) -> dict[str, dict[str, float]]:
    report = {}
    for layer in layers:
        keys = sorted(
            key for key, candidate_layer in vectors if candidate_layer == layer
        )
        layer_report = {}
        for left_index, left in enumerate(keys):
            for right in keys[left_index + 1 :]:
                value = torch.nn.functional.cosine_similarity(
                    vectors[(left, layer)].float(),
                    vectors[(right, layer)].float(),
                    dim=0,
                )
                layer_report[f"{left}|{right}"] = float(value)
        report[str(layer)] = layer_report
    return report


def _paired(rows: Iterable[dict[str, Any]], treatment: str, control: str):
    wins = losses = 0
    seen = False
    for row in rows:
        arms = row["arms"]
        if treatment not in arms or control not in arms:
            continue
        seen = True
        for treated, base in zip(
            arms[treatment]["scores"], arms[control]["scores"], strict=True
        ):
            wins += bool(treated) and not bool(base)
            losses += bool(base) and not bool(treated)
    return {"wins": wins, "losses": losses} if seen else None


def function_vector_summary(
    rows: list[dict[str, Any]],
    *,
    totals: dict[str, int],
    killed: dict[str, bool],
) -> dict[str, Any]:
    inject_paired = _paired(rows, "fv_inject", "evicted") or {"wins": 0, "losses": 0}
    echo_paired = _paired(rows, "fv_inject_echo", "clf_pinned_echo")
    helps = (
        totals["fv_inject"] >= 30
        and inject_paired["wins"] > inject_paired["losses"]
        and not killed["fv_inject"]
    )
    strong = bool(
        echo_paired
        and totals["fv_inject_echo"] > 46
        and echo_paired["wins"] > echo_paired["losses"]
        and not killed["fv_inject_echo"]
    )
    harmful = bool(
        killed["fv_inject"] or totals["fv_inject"] < totals["evicted"] + 5
    )
    return {
        "preregistered_reading": PREREGISTERED_READING,
        "unknown_vector_constraints": sum(
            int(row.get("unknown_vector_constraints", 0)) for row in rows
        ),
        "paired_fv_inject_vs_evicted": inject_paired,
        "paired_fv_inject_echo_vs_clf_pinned_echo": echo_paired,
        "reading": {"helps": helps, "strong": strong, "harmful": harmful},
    }


def repeated_4gram_fraction(token_ids: Sequence[int]) -> float:
    if len(token_ids) < 8:
        return 0.0
    grams = [tuple(token_ids[index : index + 4]) for index in range(len(token_ids) - 3)]
    return 1.0 - len(set(grams)) / len(grams)


def generate_injected(
    model,
    tokenizer,
    token_ids: Sequence[int],
    *,
    evict_range: tuple[int, int] | None,
    keep=(),
    vector: torch.Tensor | None,
    alpha: float,
    layer: int,
    clear_after: int | None,
    max_new: int,
    deadline_s: float,
    eos=(151645, 151643),
) -> dict[str, Any]:
    """Greedy pre-query generation with current-position residual additions."""
    from stencil.qwen3 import KVCache, prefill_with_eviction

    device = next(model.parameters()).device
    cache = KVCache(model.cfg)
    output = []
    started = time.monotonic()
    timed_out = False
    cache_rebuilt_at = None

    def hook(position: int):
        return (
            None
            if vector is None
            else make_residual_hook(
                vector,
                alpha=alpha,
                layer=layer,
                generated_position=position,
                clear_after=clear_after,
            )
        )

    with torch.no_grad():
        logits, index_map, _, _ = prefill_with_eviction(
            model,
            cache,
            torch.tensor([list(token_ids)], device=device),
            history_end=(evict_range[1] if evict_range is not None else 0),
            evict_range=evict_range,
            keep=keep,
            eviction_timing="pre-query",
            current_forward_kwargs={"residual_hook": hook(0)},
        )
        next_token = int(logits[0, -1].argmax())
        while next_token not in eos and len(output) < max_new:
            if time.monotonic() - started > deadline_s:
                timed_out = True
                break
            output.append(next_token)
            if clear_after is not None and len(output) == clear_after:
                # Earlier additions changed downstream cached K/V. Rebuild the
                # same conditional trajectory without the hook so clearing is
                # a true bitwise return to the unmodified forward thereafter.
                cache = KVCache(model.cfg)
                logits, _, _, _ = prefill_with_eviction(
                    model,
                    cache,
                    torch.tensor([list(token_ids)], device=device),
                    history_end=(evict_range[1] if evict_range is not None else 0),
                    evict_range=evict_range,
                    keep=keep,
                    eviction_timing="pre-query",
                )
                for replay_token in output:
                    logits = model(
                        torch.tensor([[replay_token]], device=device), cache=cache
                    )
                cache_rebuilt_at = clear_after
            else:
                logits = model(
                    torch.tensor([[next_token]], device=device),
                    cache=cache,
                    residual_hook=hook(len(output)),
                )
            next_token = int(logits[0, -1].argmax())
    text = tokenizer.decode(output, skip_special_tokens=False)
    return {
        "text": text,
        "n": len(output),
        "truncated": len(output) >= max_new,
        "timed_out": timed_out,
        "rep4": repeated_4gram_fraction(output),
        "generated_token_ids": output,
        "pinned_cols": sum(end - start for start, end in keep),
        "cache_cols": int(cache.k[0].shape[2]),
        "index_map": index_map,
        "cache_rebuilt_at": cache_rebuilt_at,
    }
