# ruff: noqa: E501
"""T0.2 score families — red-first. Each family maps one trace event to
(score, chosen_candidate_index or None). Hand-computed expectations.

Synthetic event: qk = [5.0, 3.0, 1.0], cos = [0.9, 0.8, 0.1],
candidates: 0 = live prefix 'calc', 1 = distractor prefix 'util',
2 = live hint 'int'. pred_type = 'prefix'.
"""
import math

from stencil.press_families import FAMILIES, evaluate_event

EVENT = {
    "pred_type": "prefix",
    "qk_scores": [5.0, 3.0, 1.0],
    "cos_scores": [0.9, 0.8, 0.1],
    "candidates": [
        {"type": "prefix", "value": "calc", "source": "live", "span": (5, 9)},
        {"type": "prefix", "value": "util", "source": "distractor", "span": (40, 44)},
        {"type": "hint", "value": "int", "source": "live", "span": (60, 63)},
    ],
    "ledger": {"prefix": "calc", "hint": "int"},
    "cell": "active",
}


def test_family_names_registered():
    assert set(FAMILIES) == {"raw_max", "top1_top2", "top1_logsumexp", "cos_max", "live_minus_best", "structured"}


def test_raw_max():
    s, j = evaluate_event("raw_max", EVENT)
    assert s == 5.0 and j == 0


def test_top1_top2():
    s, j = evaluate_event("top1_top2", EVENT)
    assert s == 2.0 and j == 0


def test_top1_logsumexp():
    # on EVENT only candidates 0,1 share pred_type -> rest=[3.0], s = 2.0
    s, j = evaluate_event("top1_logsumexp", EVENT)
    assert math.isclose(s, 2.0, rel_tol=1e-9) and j == 0
    # three same-type candidates: rest = [3.0, 1.0] -> distinguishes it from top1_top2
    ev = dict(EVENT, candidates=[dict(c, type="prefix") for c in EVENT["candidates"]])
    s, j = evaluate_event("top1_logsumexp", ev)
    assert math.isclose(s, 5.0 - math.log(math.exp(3.0) + math.exp(1.0)), rel_tol=1e-9)
    assert j == 0
    s2, _ = evaluate_event("top1_top2", ev)
    assert s2 == 2.0 and s < s2


def test_cos_max():
    s, j = evaluate_event("cos_max", EVENT)
    assert s == 0.9 and j == 0


def test_live_minus_best_ceiling():
    # live prefix qk=5.0; best same-type non-live = 3.0 -> margin 2.0, selects the live candidate
    s, j = evaluate_event("live_minus_best", EVENT)
    assert s == 2.0 and j == 0


def test_live_minus_best_no_live_of_type():
    ev = dict(EVENT, pred_type="doc")
    s, j = evaluate_event("live_minus_best", ev)
    assert j is None and s == float("-inf")


def test_structured():
    s, j = evaluate_event("structured", EVENT)
    assert s == 1.0 and j == 0  # pred_type has a live entry -> press it
    ev = dict(EVENT, pred_type="doc")
    s, j = evaluate_event("structured", ev)
    assert s == 0.0 and j is None


def test_margin_families_abstain_on_singleton():
    """G0 ruling (sol+fable HIGH): +inf on a singleton typed candidate set
    guaranteed a false press on single-lookalike inactive fixtures. The
    registered semantic is conservative abstention: no comparison
    candidate -> -inf (never press)."""
    ev = dict(EVENT, candidates=[EVENT["candidates"][0]], qk_scores=[5.0], cos_scores=[0.9])
    for fam in ("top1_top2", "top1_logsumexp"):
        s, j = evaluate_event(fam, ev)
        assert s == float("-inf") and j is None
    # live_minus_best with no same-type non-live comparison: also abstains
    s, j = evaluate_event("live_minus_best", ev)
    assert s == float("-inf") and j is None
    # raw_max and cos_max still press on singletons (score is absolute)
    assert evaluate_event("raw_max", ev) == (5.0, 0)
    assert evaluate_event("cos_max", ev) == (0.9, 0)


def test_counterfeit_hard_negative():
    """G0 registered construction: strip live same-type candidates from an
    active event -> what a conflicting-note-at-inactive-moment looks like."""
    from stencil.press_families import counterfeit_hard_negative
    hn = counterfeit_hard_negative(EVENT)
    assert hn is not None
    assert all(not (c["source"] == "live" and c["type"] == "prefix") for c in hn["candidates"])
    assert hn["cell"] == "counterfeit"
    assert len(hn["candidates"]) == 2 and len(hn["qk_scores"]) == 2
    # event with no same-type lookalike yields no counterfeit
    ev = dict(EVENT, candidates=[EVENT["candidates"][0], EVENT["candidates"][2]],
              qk_scores=[5.0, 1.0], cos_scores=[0.9, 0.1])
    assert counterfeit_hard_negative(ev) is None


def test_selection_restricted_to_pred_type():
    # even if a hint candidate scored highest, prefix pred_type only ranks prefix candidates
    ev = dict(EVENT, qk_scores=[1.0, 0.5, 9.0], cos_scores=[0.2, 0.1, 0.99])
    s, j = evaluate_event("raw_max", ev)
    assert j == 0 and s == 1.0
