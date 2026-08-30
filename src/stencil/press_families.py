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
        # G0 ruling: no comparison candidate -> conservative abstention
        return (qk[j] - max(others), j) if others else (float("-inf"), None)
    if family == "cos_max":
        cos = event["cos_scores"]
        j = max(idx, key=lambda i: cos[i])
        return cos[j], j
    j = max(idx, key=lambda i: qk[i])
    if family == "raw_max":
        return qk[j], j
    rest = [qk[i] for i in idx if i != j]
    # G0 ruling (sol+fable HIGH): +inf singleton semantics guaranteed a
    # false press on single-lookalike inactive fixtures -> abstain instead.
    if family == "top1_top2":
        return (qk[j] - max(rest), j) if rest else (float("-inf"), None)
    if family == "top1_logsumexp":
        if not rest:
            return float("-inf"), None
        mx = max(rest)
        return qk[j] - (mx + math.log(sum(math.exp(x - mx) for x in rest))), j
    raise ValueError(f"unknown family {family}")


def counterfeit_hard_negative(event: dict):
    """G0 registered construction: strip live candidates of the event's
    pred_type from an active event, simulating a conflicting-note-at-
    inactive-moment. Returns None when no same-type non-live lookalike
    remains (nothing to press). cell is marked "counterfeit"."""
    ty = event["pred_type"]
    keep = [i for i, c in enumerate(event["candidates"])
            if not (c["type"] == ty and c["source"] == "live")]
    if not any(event["candidates"][i]["type"] == ty for i in keep):
        return None
    return dict(event,
                candidates=[event["candidates"][i] for i in keep],
                qk_scores=[event["qk_scores"][i] for i in keep],
                cos_scores=[event["cos_scores"][i] for i in keep],
                cell="counterfeit")
