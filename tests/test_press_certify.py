# ruff: noqa: E501
"""Pure certification-decision logic (impl-review fixes) — red-first.

Registered semantics (stricter than trace-time value-level selection,
disclosed): a decision above threshold is a FALSE SELECTION unless the
chosen span itself lies inside an authoritative ledger sentence span —
a historical copy of the live sentence (same value, different span)
counts as a failure and is never applied (sol impl review CRITICAL)."""
from stencil.press_certify import certify_decision, s0x_assertion_hit

SPANS = {"prefix": (2, 10)}


def test_below_threshold_abstains():
    assert certify_decision(0.5, 0.64, (3, 8), SPANS) == "abstain"


def test_authoritative_press():
    assert certify_decision(0.9, 0.64, (3, 8), SPANS) == "press"
    assert certify_decision(0.9, 0.64, (2, 10), SPANS) == "press"


def test_historical_same_value_span_is_false_selection_and_not_applied():
    # span outside the ledger region -> false selection even if its VALUE
    # equals the live value (value is not an input at all)
    assert certify_decision(0.9, 0.64, (40, 48), SPANS) == "false-selection"


def test_boundary_exact_threshold_abstains():
    assert certify_decision(0.64, 0.64, (3, 8), SPANS) == "abstain"  # strict >


def test_s0x_assertion_binding():
    # hit requires: targeted work turn, targeted type, some same-type
    # candidate present, and NO authoritative same-type candidate
    cands = [("prefix", "util", (40, 44), 0)]
    assert s0x_assertion_hit(wt=9, ty="prefix", target={"type": "prefix", "work_turn": 9},
                             typed_idx=[0], cands=cands, ledger_spans={})
    # wrong work turn -> no hit
    assert not s0x_assertion_hit(wt=5, ty="prefix", target={"type": "prefix", "work_turn": 9},
                                 typed_idx=[0], cands=cands, ledger_spans={})
    # wrong type -> no hit
    assert not s0x_assertion_hit(wt=9, ty="doc", target={"type": "prefix", "work_turn": 9},
                                 typed_idx=[0], cands=cands, ledger_spans={})
    # an authoritative same-type candidate present -> no hit
    assert not s0x_assertion_hit(wt=9, ty="prefix", target={"type": "prefix", "work_turn": 9},
                                 typed_idx=[0], cands=[("prefix", "calc", (3, 8), 0)],
                                 ledger_spans={"prefix": (2, 10)})
    # no same-type candidate at all -> no hit
    assert not s0x_assertion_hit(wt=9, ty="prefix", target={"type": "prefix", "work_turn": 9},
                                 typed_idx=[], cands=[], ledger_spans={})
