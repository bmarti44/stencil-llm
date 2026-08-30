# ruff: noqa: E501
"""Pure certification-decision logic for the sealed fixture jobs
(PRESS-PLAN G0; impl-review fixes 2026-08-30).

Semantics are provenance-by-span (STRICTER than the trace-time
value-level selection semantics — disclosed in the certificate): a
decision above threshold is a false selection unless the chosen span
lies inside an authoritative ledger sentence span, mirroring
t2_runner.span_in_ledger exactly.
"""
from .t2_runner import span_in_ledger


def certify_decision(score: float, threshold: float, chosen_span, ledger_spans) -> str:
    """-> "abstain" | "press" | "false-selection" (press means: apply)."""
    if score <= threshold:
        return "abstain"
    if span_in_ledger(chosen_span, ledger_spans):
        return "press"
    return "false-selection"


def s0x_assertion_hit(wt, ty, target, typed_idx, cands, ledger_spans) -> bool:
    """The registered non-vacuity event: at the TARGETED work turn, a
    timing fire of the TARGET type with >=1 same-type candidate and no
    authoritative same-type candidate."""
    if wt != target["work_turn"] or ty != target["type"] or not typed_idx:
        return False
    return not any(span_in_ledger(cands[i][2], ledger_spans) for i in typed_idx)
