"""The step-1 construction gate, plus mutations proving the gate BITES.

Astra's gate for the scoped-instruction diagnostic:

    gold and valid alternatives pass; every shortcut fails its designated
    contrasts; source metadata cannot reach the automatic arm.

A gate that refuses everything would satisfy the second clause and be worthless,
so every mutation below is a fixture defect the gate must CATCH, and the
unmutated fixture must pass.
"""

import json
import sys
from dataclasses import replace
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from scoped_gate import gate  # noqa: E402

from stencil.scoped_blocks import (  # noqa: E402
    BASELINE,
    CODE_PATHS,
    KINDS,
    RIVALS,
    SUITES,
    Event,
    _matches,
    _specificity,
    arm_payload,
    evaluate,
    gold_candidate,
    history_variant,
    live_state,
    passes,
    resolve,
    resolve_events,
    shortcut_candidate,
    value_candidate,
)
from stencil.scoped_dev_blocks import BLOCKS  # noqa: E402


def _by_id(bid):
    return next(b for b in BLOCKS if b.id == bid)


# ----------------------------------------------------------------- the gate


def test_the_construction_gate_passes():
    problems, _rows, _defeated, _counts = gate()
    assert problems == [], problems


def test_every_required_shortcut_is_refuted_somewhere():
    _p, _r, defeated, _c = gate()
    for policy in ("always_newest", "always_oldest", "flip_on_cancel",
                   "copy_existing", "recency_general"):
        assert defeated[policy], policy


def test_the_scope_aware_rivals_both_survive_and_fail():
    """The anti-vacuity evidence: the oracle is not simply refusing non-gold."""
    _p, _r, defeated, _c = gate()
    for policy in RIVALS:
        assert 0 < len(defeated[policy]) < len(BLOCKS), (policy, defeated[policy])


# ------------------------------------------------------- the gate must bite


def test_a_block_whose_cases_need_the_same_value_is_caught():
    block = _by_id("S1")
    twin = replace(block, cases=(block.cases[0], block.cases[0]))
    problems, *_ = gate(tuple(twin if b.id == "S1" else b for b in BLOCKS))
    assert any("does not discriminate" in p for p in problems), problems


def test_an_unearned_defeat_claim_is_caught():
    """`scoped_recency` passes S1; claiming S1 defeats it must be refused."""
    block = _by_id("S1")
    liar = replace(block, defeats=(*block.defeats, "scoped_recency"))
    problems, *_ = gate(tuple(liar if b.id == "S1" else b for b in BLOCKS))
    assert any("scoped_recency" in p and "PASSES" in p for p in problems), problems


def test_specificity_ties_are_structurally_impossible():
    """`resolve` reports ambiguity; this proves the flag can never fire.

    For any (path, operation) request, the scopes that match form a chain of
    distinct depths, and the operation flag separates the two keys of any one
    scope.  So no two distinct live keys can share a specificity, and no
    measurement can depend on the tie-break.  The flag stays as a defensive
    assertion, not as a live semantic question.
    """
    scopes = ("*", "core", "compat", "compat.legacy")
    keys = [(s, k) for s in scopes for k in (None, *KINDS)]
    for path in CODE_PATHS:
        for kind in KINDS:
            hits = [k for k in keys if _matches(k[0], k[1], path, kind)]
            specs = [_specificity(*k) for k in hits]
            assert len(specs) == len(set(specs)), (path, kind, hits)


def test_resolution_ties_are_detected_by_resolve():
    history = (
        Event("a", "core raises.", "set", "core", None, "raise"),
        Event("b", "core lookups return None.", "set", "core", "lookup", "none"),
        Event("c", "Everywhere, DEFAULT.", "set", "*", None, "default"),
    )
    # (core, None) has depth 1; (core, lookup) has depth 1 + op -> more specific
    assert resolve(history, "core", "lookup")[0] == "none"
    assert resolve(history, "core", "bulk")[0] == "raise"


def test_a_block_count_other_than_sixteen_is_caught():
    problems, *_ = gate(BLOCKS[:15])
    assert any("not 16" in p for p in problems), problems


def test_a_wrong_value_never_passes_the_oracle():
    """The oracle is behavioural: a different policy value must be rejected."""
    block = _by_id("S1")
    case = block.cases[0]
    wrong = "raise" if resolve(block.history, case.path, case.fn_kind)[0] != "raise" \
        else "none"
    assert not passes(block, case, value_candidate(block, case, wrong))


# ------------------------------------------------------------ the semantics


def test_cancelling_a_replacement_does_not_revive_what_it_replaced():
    block = _by_id("C4")
    assert resolve(block.history, "core", "lookup")[0] == BASELINE
    assert BASELINE != "raise", "the baseline must differ from the superseded rule"


def test_cancelling_an_exception_exposes_the_still_live_enclosing_rule():
    block = _by_id("C1")
    assert resolve(block.history, "compat", "lookup")[0] == "raise"


def test_reinstatement_restores_by_reference_without_restating_a_value():
    """It may name the rule it is leaving; it may not name the one it restores."""
    for bid in ("R1", "R2", "R3"):
        block = _by_id(bid)
        reinstate = next(e for e in block.history if e.kind == "reinstate")
        referenced = next(e for e in block.history if e.id == reinstate.ref)
        assert reinstate.value is None
        assert referenced.value not in reinstate.text.lower(), bid
    assert resolve(_by_id("R1").history, "core", "lookup")[0] == "raise"


def test_reinstatement_does_not_point_at_the_first_statement_at_its_scope():
    """Astra's finding 1: every reinstatement referenced the first policy ever
    stated at its scope, so "always restore the first one" passed all 16."""
    block = _by_id("R1")
    reinstate = next(e for e in block.history if e.kind == "reinstate")
    same_scope = [e for e in block.history
                  if e.kind in ("set", "replace") and e.scope == "*"]
    assert same_scope[0].id != reinstate.ref
    assert same_scope[1].id == reinstate.ref


def test_restoring_a_global_rule_leaves_a_later_narrower_rule_in_force():
    block = _by_id("R2")
    assert resolve(block.history, "core", "lookup")[0] == "default"
    assert resolve(block.history, "compat", "lookup")[0] == "none"


def test_an_obligation_survives_the_cancellation_of_a_policy():
    block = _by_id("R3")
    _live, obligations = live_state(block.history)
    assert ("note", "compat") in obligations
    assert resolve(block.history, "compat", "lookup")[1] == ("note",)


def test_an_obligation_does_not_apply_outside_its_own_scope():
    """Astra's finding 1: treating every obligation as package-wide passed 16/16
    because the only scoped obligation had both its cases inside its scope."""
    block = _by_id("R3")
    assert resolve(block.history, "compat", "lookup")[1] == ("note",)
    assert resolve(block.history, "core", "lookup")[1] == ()
    source = next(e for e in block.history if e.kind == "obligate")
    assert "compat/" in source.text and "core.py does not need it" in source.text


def test_a_released_support_stops_appearing_among_the_live_supports():
    """Astra's finding 8: supports were selected by NAME, so a released
    package-wide statement kept appearing beside a live compat one."""
    history = (
        Event("o1", "Every public function in the package calls note().",
              "obligate", "*", name="note"),
        Event("o2", "Every public function in compat/ calls note().",
              "obligate", "compat", name="note"),
        Event("o3", "Drop the package-wide note() rule.",
              "release", "*", name="note"),
    )
    _winner, supports = resolve_events(history, "compat", "lookup")
    assert [e.id for e in supports] == ["o2"]
    assert resolve(history, "core", "lookup")[1] == ()


def test_releasing_an_obligation_is_prospective():
    block = _by_id("C3")
    assert resolve(block.history, "core", "lookup")[1] == ()
    assert "note" in block.entering_obligations


def test_a_broad_revision_clears_a_narrower_scope_only_when_it_says_so():
    g3, s1 = _by_id("G3"), _by_id("S1")
    assert resolve(g3.history, "compat", "lookup")[0] == "default"  # cleared
    assert resolve(s1.history, "compat", "lookup")[0] == "none"  # not cleared


def test_specificity_beats_recency():
    s2 = _by_id("S2")
    order = [e.id for e in s2.history]
    assert order.index("s2b") > order.index("s2a"), "the broad rule must come last"
    assert resolve(s2.history, "core", "lookup")[0] == "raise"


# -------------------------------------------------------- the oracle itself


@pytest.mark.parametrize("bid", [b.id for b in BLOCKS])
def test_gold_and_both_alternatives_pass_every_case(bid):
    block = _by_id(bid)
    for case in block.cases:
        for style in ("gold", "alt1", "alt2"):
            scores = evaluate(block, case, gold_candidate(block, case, style))
            assert all(scores.values()), (bid, case.name, style, scores)


def test_a_whole_state_rollback_fails_even_with_the_right_value():
    """git revert records a reversal; it does not delete the ancestry."""
    block = _by_id("R1")
    for case in block.cases:
        scores = evaluate(block, case, shortcut_candidate(block, case, "rollback"))
        assert not all(scores.values()), (case.name, scores)


def test_the_oracle_names_all_four_suites():
    block = _by_id("S1")
    scores = evaluate(block, block.cases[0], gold_candidate(block, block.cases[0]))
    assert set(scores) == set(SUITES)


# ---------------------------------------------------- the automatic arm's view


def test_the_arm_payload_carries_no_source_metadata():
    for block in BLOCKS:
        for case in block.cases:
            blob = json.loads(json.dumps(arm_payload(block, case)))
            assert set(blob) == {"messages", "repo", "request"}
            for msg in blob["messages"]:
                assert set(msg) == {"role", "text"}
            assert set(blob["request"]) == {"module", "function", "signature",
                                            "text"}
            assert block.id not in json.dumps(blob)
            for word in ("reinstate", "obligate", "rule_turns", "applicable",
                         "precedent", "defeats"):
                assert word not in json.dumps(blob).lower(), (block.id, word)


def test_the_arm_payload_repo_is_identical_for_both_cases_of_a_block():
    for block in BLOCKS:
        a, b = (arm_payload(block, c)["repo"] for c in block.cases)
        assert a == b, block.id


def test_the_three_history_variants_resolve_identically():
    """The economics contrast: direct, revised, and irrelevant-padded histories
    must leave the oracle's requirement unchanged."""
    for block in BLOCKS:
        for case in block.cases:
            want = resolve(block.history, case.path, case.fn_kind)[:2]
            for variant in ("revised", "direct", "irrelevant"):
                got = resolve(history_variant(block, variant), case.path,
                              case.fn_kind)[:2]
                assert got == want, (block.id, case.name, variant, got, want)


def test_the_direct_variant_is_shorter_than_the_revised_one_somewhere():
    """If `direct` were never shorter it would not be a different condition."""
    assert any(len(history_variant(b, "direct")) < len(b.history) for b in BLOCKS)
