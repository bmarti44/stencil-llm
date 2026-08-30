# ruff: noqa: E501
"""T0.2 score families over trace events (PRESS-PLAN v3.2).

Each family maps an event to (score, chosen_candidate_index | None).
Registered semantics: candidate ranking is restricted to candidates of
the event's pred_type (the timing head names the type; the family
chooses among that type's candidates). live_minus_best is the
provenance CEILING (it reads source labels); structured presses iff
pred_type has a live ledger entry. Neither ceiling nor structured is an
autonomous family.
"""
import math

FAMILIES = ("raw_max", "top1_top2", "top1_logsumexp", "cos_max", "live_minus_best", "structured")


def _typed(event):
    """indices of candidates matching pred_type."""
    ty = event["pred_type"]
    return [i for i, c in enumerate(event["candidates"]) if c["type"] == ty]


def evaluate_event(family: str, event: dict):
    idx = _typed(event)
    if family == "structured":
        ty = event["pred_type"]
        live_val = event["ledger"].get(ty)
        if live_val is None:
            return 0.0, None
        j = next((i for i in idx if event["candidates"][i]["source"] == "live"), None)
        return (1.0, j) if j is not None else (0.0, None)
    if not idx:
        return float("-inf"), None
    qk = event["qk_scores"]
    if family == "live_minus_best":
        live = [i for i in idx if event["candidates"][i]["source"] == "live"]
        if not live:
            return float("-inf"), None
        j = max(live, key=lambda i: qk[i])
        others = [qk[i] for i in idx if i not in live]
        return (qk[j] - max(others)) if others else float("inf"), j
    if family == "cos_max":
        cos = event["cos_scores"]
        j = max(idx, key=lambda i: cos[i])
        return cos[j], j
    j = max(idx, key=lambda i: qk[i])
    if family == "raw_max":
        return qk[j], j
    rest = [qk[i] for i in idx if i != j]
    if family == "top1_top2":
        return (qk[j] - max(rest)) if rest else float("inf"), j
    if family == "top1_logsumexp":
        if not rest:
            return float("inf"), j
        mx = max(rest)
        return qk[j] - (mx + math.log(sum(math.exp(x - mx) for x in rest))), j
    raise ValueError(f"unknown family {family}")
