# ruff: noqa: E501
"""Consumer-path tests for scripts/ledger_eval.py (sol's verification,
results/ledger-verify-sol.md, findings 1/2/4/6/7).

The validity gate is exercised through the exact summarize() the runner
calls, with sol's two adversarial records (an empty-ledger identical-arms
record and a favorable partial record) and a complete synthetic run that
must PASS so the gate is proven non-vacuous, then every condition is broken
one at a time.  The CPU preflight builds the ledger for every turn of every
diagnostic conversation with the real salience path.
"""
import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
TOK_PATH = ROOT / "models" / "qwen3-1.7b-hf" / "tokenizer.json"
DATA_PATH = ROOT / "data" / "bench" / "multiif_en.jsonl"


@pytest.fixture(scope="module")
def ev():
    spec = importlib.util.spec_from_file_location("ledger_eval", ROOT / "scripts" / "ledger_eval.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["ledger_eval"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_registered_values_are_the_frozen_ones(ev):
    from stencil.bench import MAX_NEW
    assert ev.REGISTERED == {"top_k": 2, "dose": 3.0, "max_new": MAX_NEW, "deadline": 300.0}
    assert ev.REGISTERED_COHORT == 909 and ev.MARGIN_POINTS == 2.0
    assert ev.SEGMENTER_IDENTITY == "stencil.salience.split_sentences"


def test_provenance_manifest_covers_every_registered_dependency(ev):
    prov = ev.provenance_manifest()
    for key in ("salience_weights.json", "qwen3.py", "ctrb.py", "e2.py", "e2_multiif.py", "stats.py",
                "ledger.py", "salience.py", "tokenizer.json", "vendor/ifeval", "ledger_eval.py",
                "wave.py", "bench.py", "determinism.py"):  # sol round 2 finding 7: EOS / biased layers / seeds
        assert key in prov and len(prov[key]) == 64, key
    assert prov["wave.py"] == ev.sha(ROOT / "src" / "stencil" / "wave.py")
    assert prov["bench.py"] == ev.sha(ROOT / "src" / "stencil" / "bench.py")
    assert prov["determinism.py"] == ev.sha(ROOT / "src" / "stencil" / "determinism.py")
    # the tree hash is order-independent, content-dependent, and ignores __pycache__
    h = ev.tree_sha(ROOT / "vendor" / "ifeval")
    assert h == prov["vendor/ifeval"] == ev.tree_sha(ROOT / "vendor" / "ifeval")
    assert h != ev.tree_sha(ROOT / "src" / "stencil")


def test_resume_fails_closed_on_provenance_mismatch(ev, tmp_path):
    meta = {"schema": 2, "provenance": {"ledger.py": "a" * 64}, "registered": ev.REGISTERED}
    ev.check_or_write_meta(tmp_path / "meta.json", meta)
    ev.check_or_write_meta(tmp_path / "meta.json", copy.deepcopy(meta))  # identical -> ok
    with pytest.raises(RuntimeError, match="provenance"):
        ev.check_or_write_meta(tmp_path / "meta.json", {**meta, "provenance": {"ledger.py": "b" * 64}})


def test_resume_fails_closed_when_wave_bench_or_determinism_hash_changes(ev, tmp_path):
    prov = ev.provenance_manifest()
    meta = {"schema": 2, "provenance": prov, "registered": ev.REGISTERED}
    ev.check_or_write_meta(tmp_path / "meta.json", meta)
    for name in ("wave.py", "bench.py", "determinism.py"):
        with pytest.raises(RuntimeError, match="provenance"):
            ev.check_or_write_meta(tmp_path / "meta.json", {**meta, "provenance": {**prov, name: "0" * 64}})


# ------------------------------------------------------------------ records
IDS = ["keywords:existence", "punctuation:no_comma", "keywords:frequency"]  # 2 insertable, 1 not


def good_meta(ev):
    return {"schema": 2, "registered": dict(ev.REGISTERED), "top_k": 2, "dose": 3.0, "max_new": ev.REGISTERED["max_new"],
            "deadline": 300.0, "automatic": True, "salience_provenance": "salience",
            "segmenter": ev.SEGMENTER_IDENTITY, "segmenter_identity_asserted": True,
            "insertable_families": ["keywords:existence", "keywords:frequency"], "margin_points": 2.0}


def arm(per, *, added=0, measured=True, selected=(), timed_out=False, truncated=False):
    return {"per_constraint": list(per), "context_tokens_added": added, "context_tokens_measured": measured,
            "selected_entries": list(selected), "timed_out": timed_out, "truncated": truncated,
            "n_generated": 10, "biased_tokens": 0}


def turn_record(*, base, text, neural, spec, ledger, aged, selected, current_turn=2, origins=(1, 1, 2)):
    """One turn: three constraints, origin turns given, entries linked at origin-turn granularity."""
    constraints = []
    for j, (iid, origin) in enumerate(zip(IDS, origins, strict=True)):
        idx = [i for i, e in enumerate(ledger) if e["turn_introduced"] == origin]
        constraints.append({"index": j, "id": iid, "origin_turn": origin, "aged": origin < current_turn,
                            "insertable": iid in ("keywords:existence", "keywords:frequency"),
                            "entry_indices": idx, "entry_selected": any(i in selected for i in idx)})
    return {"instruction_ids": IDS, "constraints": constraints, "linkage_granularity": "origin_turn",
            "ledger": ledger, "aged_entry_indices": aged, "automatic": True,
            "ledger_active": any(i in aged for i in selected), "segmenter": "stencil.salience.split_sentences",
            "base": {"per_constraint": list(base), "timed_out": False, "truncated": False},
            "arms": {"text_ledger": arm(text, added=12, selected=aged), "neural_ledger": arm(neural, selected=selected),
                     "specificity": arm(spec)}}


ENTRY1 = {"text": "Include the keyword lantern.", "span": [3, 9], "turn_introduced": 1, "provenance": "salience", "instruction_ids": [IDS[0], IDS[1]]}
ENTRY2 = {"text": "Use the word bright twice.", "span": [30, 37], "turn_introduced": 2, "provenance": "salience", "instruction_ids": [IDS[2]]}


def record_config(ev):
    return {"top_k": 2, "dose": 3.0, "max_new": ev.REGISTERED["max_new"], "deadline": 300.0}


def make_record(ci, turn, *, diagnostic=False, ev=None, turns=None):
    """A record as the runner writes it: identity (ci, key) and the frozen configuration
    ECHOED per record (sol round 2 finding 1: identity was checked in meta only)."""
    return {"ci": ci, "key": f"k{ci}", "diagnostic": diagnostic, "turns": turns if turns is not None else {"2": turn},
            "arms": ["base", *ev.ARMS], "config": record_config(ev)}


def identity(n=909, turns=("2",)):
    """The registered cohort identity the runner derives from the data rows: key and the
    expected late turns of every conversation."""
    return {ci: {"key": f"k{ci}", "turns": list(turns)} for ci in range(n)}


def complete_run(ev, n=909):
    """A run that PASSES every gate: text beats base on eligible outcomes, neural ties text,
    the ledger is active everywhere, tokens measured zero, no timeouts."""
    recs = []
    for ci in range(n):
        base = [False, True, True] if ci % 3 == 0 else [True, True, True]
        text = [True, True, True]
        neural = [True, True, True] if ci % 40 else [True, True, False]  # a fresh-constraint miss: NOT eligible
        recs.append(make_record(ci, turn_record(base=base, text=text, neural=neural, spec=[True, False, True],
                                                ledger=[ENTRY1, ENTRY2], aged=[0], selected=[0]), ev=ev))
    return recs


def summ(ev, recs, meta=None, *, cohort_size=None, ident=None):
    return ev.summarize(recs, meta or good_meta(ev), cohort_size=cohort_size or ev.REGISTERED_COHORT,
                        identity=ident if ident is not None else identity())


def test_complete_valid_run_passes_and_reports_estimand(ev):
    s = summ(ev, complete_run(ev))
    assert s["primary_claim_valid"] is True, s["primary_claim_reasons"]
    el = s["eligible"]
    assert el["n"] == 909 and el["n_conversations"] == 909  # aged AND insertable: only keywords:existence at origin 1
    assert el["definition"].startswith("aged")
    p = s["primary"]
    assert p["clustered"]["method"] == "t_continuity" and p["non_inferior"] is True
    assert p["clustered"]["upper_bound"] == 100.0 / 909 and p["clustered"]["t_upper_bound_descriptive"] == 0.0
    assert s["validity"]["timeouts_truncations_le_2pct"] is True and s["timeouts_or_truncations"]["base"] == 0
    assert s["validity"]["records_identity"] is True and s["validity"]["records_echo_registered_config"] is True
    assert s["validity"]["expected_turns_present"] is True and s["turns"] == 909
    assert s["validity"]["ledger_coverage_ge_0.90"] is True and s["eligible"]["selected_fraction"] == 1.0
    assert s["validity"]["text_beats_base_selected_clustered"] is True and s["validity"]["unselected_not_all_failing"] is True
    assert s["unselected_text_vs_base"] is None and s["slice_role"] == "registered_cohort"
    assert s["neural_vs_specificity"]["control_incomplete_turns"] == 0
    assert p["tango_pooled_descriptive"]["n"] == 909
    assert s["text_vs_base[eligible]"]["n01"] == 303 and s["text_vs_base[eligible]"]["n10"] == 0
    assert s["validity"]["text_beats_base"] is True
    assert "neural_vs_specificity" in s and s["neural_vs_specificity"]["clustered"]["clusters"] == 909
    assert s["context_tokens_added_sum"]["neural_ledger"] == 0 and s["context_tokens_added_max"]["text_ledger"] == 12


def test_sol_adversarial_empty_ledger_identical_arms_is_invalid(ev):
    """Finding 1: 200 identical text/neural outcomes with an EMPTY ledger certified as valid."""
    recs = []
    for ci in range(909):
        t = turn_record(base=[True, True, True], text=[True, True, True], neural=[True, True, True],
                        spec=[True, True, True], ledger=[], aged=[], selected=[])
        recs.append(make_record(ci, t, ev=ev))
    s = summ(ev, recs)
    assert s["primary_claim_valid"] is False
    v = s["validity"]
    assert v["ledger_active_on_credited_turns"] is False and v["text_beats_base"] is False
    assert s["empty_ledger_turns"] == 909


def test_sol_adversarial_favorable_partial_record_is_invalid(ev):
    """Finding 1: a favorable four-cell partial record."""
    recs = complete_run(ev, n=4)
    s = summ(ev, recs)
    assert s["primary_claim_valid"] is False and s["validity"]["complete_cohort"] is False
    assert s["primary"]["clustered"]["method"] == "t_continuity" and s["primary"]["clustered"]["continuity_points"] == 25.0
    # and passing the partial count as the cohort size does not launder it: the registered size is checked
    s2 = summ(ev, recs, cohort_size=4, ident=identity(4))
    assert s2["primary_claim_valid"] is False and s2["validity"]["registered_cohort"] is False


# ---------------------------------------------- sol round 2 (results/ledger-reverify-sol.md, CRITICAL)
def test_sol2_wrong_conversation_identities_are_invalid(ev):
    """909 records with entirely wrong conversation IDs (unique, but not the cohort)."""
    recs = complete_run(ev)
    for r in recs:
        r["ci"] += 5000
    s = summ(ev, recs)
    assert s["primary_claim_valid"] is False and s["validity"]["records_identity"] is False
    assert "records_identity" in s["primary_claim_reasons"]
    # right ids, wrong keys (a different cohort's records renamed) is equally invalid
    recs = complete_run(ev)
    recs[300]["key"] = "not-the-registered-key"
    s = summ(ev, recs)
    assert s["primary_claim_valid"] is False and s["validity"]["records_identity"] is False
    # and a record from a different data file (key right, ci right) but wrong arm set
    recs = complete_run(ev)
    recs[10]["arms"] = ["base", "text_ledger", "neural_ledger"]
    s = summ(ev, recs)
    assert s["primary_claim_valid"] is False and s["validity"]["records_arm_set"] is False
    recs = complete_run(ev)
    del recs[10]["turns"]["2"]["arms"]["specificity"]
    s = summ(ev, recs)
    assert s["primary_claim_valid"] is False and s["validity"]["records_arm_set"] is False


def test_sol2_one_turn_records_when_cohort_requires_more_turns_are_invalid(ev):
    """909 one-turn records although the real cohort has 1,805 late turns."""
    recs = complete_run(ev)
    ident = identity()
    for ci in range(909):
        if ci % 2 == 0:
            ident[ci]["turns"] = ["2", "3"]
    assert sum(len(v["turns"]) for v in ident.values()) > 909
    s = summ(ev, recs, ident=ident)
    assert s["primary_claim_valid"] is False and s["validity"]["expected_turns_present"] is False
    assert "expected_turns_present" in s["primary_claim_reasons"]
    # an extra unexpected turn is invalid too (a record from a different context)
    recs = complete_run(ev)
    recs[3]["turns"]["3"] = copy.deepcopy(recs[3]["turns"]["2"])
    s = summ(ev, recs)
    assert s["validity"]["expected_turns_present"] is False


def test_sol2_base_timing_out_on_every_turn_is_invalid(ev):
    """the 2% timeouts/truncations cap must bind EVERY arm, base included."""
    recs = complete_run(ev)
    for r in recs:
        r["turns"]["2"]["base"]["timed_out"] = True
    s = summ(ev, recs)
    assert s["primary_claim_valid"] is False and s["validity"]["timeouts_truncations_le_2pct"] is False
    assert s["timeouts_or_truncations_fraction"]["base"] == 1.0
    recs = complete_run(ev)
    for r in recs[:19]:  # 2.09% of base truncated
        r["turns"]["2"]["base"]["truncated"] = True
    s = summ(ev, recs)
    assert s["validity"]["timeouts_truncations_le_2pct"] is False
    assert s["validity"]["timeouts_truncations_per_arm"]["base"] is False


def test_sol2_half_of_eligible_unselected_with_text_failing_the_same_half_is_invalid(ev):
    """half the eligible constraints had NO selected linked entry (another entry kept the
    ledger 'active'); text failed exactly those cells, so fail-closed credit costs nothing."""
    recs = complete_run(ev)
    for ci, r in enumerate(recs):
        t = r["turns"]["2"]
        if ci % 2 == 0:
            # another aged entry (unlinked to constraint 0) is selected -> ledger_active stays True
            t["ledger"] = [ENTRY1, {**ENTRY1, "text": "Other aged sentence.", "span": [12, 15], "instruction_ids": []}, ENTRY2]
            t["aged_entry_indices"] = [0, 1]
            t["arms"]["neural_ledger"]["selected_entries"] = [1]
            t["ledger_active"] = True
            for c in t["constraints"]:
                c["entry_indices"] = [0] if c["origin_turn"] == 1 else [2]
                c["entry_selected"] = False
            t["base"]["per_constraint"] = [False, True, True]                # base fails there as well
            t["arms"]["text_ledger"]["per_constraint"] = [False, True, True]  # text fails the unselected cell
            t["arms"]["neural_ledger"]["per_constraint"] = [False, True, True]
    s = summ(ev, recs)
    assert s["validity"]["ledger_active_on_credited_turns"] is True  # sol: the turn-level check is satisfied
    assert s["validity"]["text_beats_base"] is True                  # by the other half
    assert s["eligible"]["n_unselected"] == 455 and s["eligible"]["selected_fraction"] == 454 / 909
    assert s["primary_claim_valid"] is False
    assert s["validity"]["ledger_coverage_ge_0.90"] is False
    assert "ledger_coverage_below_0.90" in s["primary_claim_reasons"]


def unselect_conversations(recs, cis, *, text_fails=True):
    """sol's construction shape on the conversations ``cis``: the linked entry of the eligible
    constraint is NOT selected (another aged entry keeps the ledger active) and, when
    ``text_fails``, base/text/neural all fail that cell so fail-closed credit costs nothing."""
    for ci in cis:
        t = recs[ci]["turns"]["2"]
        t["ledger"] = [ENTRY1, {**ENTRY1, "text": "Other aged sentence.", "span": [12, 15], "instruction_ids": []}, ENTRY2]
        t["aged_entry_indices"] = [0, 1]
        t["arms"]["neural_ledger"]["selected_entries"] = [1]
        t["ledger_active"] = True
        for c in t["constraints"]:
            c["entry_indices"] = [0] if c["origin_turn"] == 1 else [2]
            c["entry_selected"] = False
        if text_fails:
            t["base"]["per_constraint"] = [False, True, True]
            t["arms"]["text_ledger"]["per_constraint"] = [False, True, True]
            t["arms"]["neural_ledger"]["per_constraint"] = [False, True, True]


def test_sol3_just_over_half_selected_with_text_failing_the_unselected_half_is_invalid(ev):
    """sol round 3 HIGH: the strict-majority gate admitted 902/1805 unselected (selected
    fraction 50.03%) with text failing exactly the unselected cells.  Registered ruling (i):
    a COVERAGE gate at >= 0.90; (ii) text must beat base WITHIN the selected subset and
    the unselected subset's cells are reported and must not be all-failing."""
    recs = complete_run(ev)
    unselect_conversations(recs, [ci for ci in range(909) if ci % 2 == 1])  # 454 unselected -> 455/909 selected
    s = summ(ev, recs)
    assert s["eligible"]["n_unselected"] == 454 and s["eligible"]["selected_fraction"] == 455 / 909  # 50.06%
    assert s["validity"]["ledger_active_on_credited_turns"] is True and s["validity"]["text_beats_base"] is True
    assert s["primary"]["clustered"]["upper_bound"] < 2.0            # the bound alone would pass
    assert s["primary_claim_valid"] is False
    assert s["validity"]["ledger_coverage_ge_0.90"] is False
    assert "ledger_coverage_below_0.90" in s["primary_claim_reasons"]
    # the unselected subset is reported separately: text failed 100% of it -> its own gate fails
    u = s["unselected_text_vs_base"]
    assert u["n"] == 454 and u["n01"] == 0 and u["n10"] == 0 and u["n00"] == 454
    assert s["validity"]["unselected_not_all_failing"] is False
    assert "unselected_not_all_failing" in s["primary_claim_reasons"]
    # and text-vs-base within the SELECTED subset is evaluated on its own
    assert s["validity"]["text_beats_base_selected_clustered"] is True
    assert s["selected_text_vs_base"]["n"] == 455 and s["selected_text_vs_base"]["n01"] > 0


def test_sol3_text_beating_base_only_on_unselected_cells_fails_the_selected_gate(ev):
    """text's advantage over base must come from cells where the ledger was actually
    exercised: here text beats base ONLY on unselected cells (5% of eligible)."""
    recs = complete_run(ev)
    unselected = list(range(0, 909, 20))[:45]
    for r in recs:  # selected cells: text == base everywhere
        r["turns"]["2"]["arms"]["text_ledger"]["per_constraint"] = list(r["turns"]["2"]["base"]["per_constraint"])
    unselect_conversations(recs, unselected, text_fails=False)
    for ci in unselected:  # unselected cells: base fails, text passes
        recs[ci]["turns"]["2"]["base"]["per_constraint"] = [False, True, True]
        recs[ci]["turns"]["2"]["arms"]["text_ledger"]["per_constraint"] = [True, True, True]
    s = summ(ev, recs)
    assert s["validity"]["ledger_coverage_ge_0.90"] is True
    assert s["validity"]["text_beats_base"] is True                 # the overall test is fooled
    assert s["validity"]["text_beats_base_selected_clustered"] is False       # the registered one is not
    assert s["selected_text_vs_base"]["n01"] == s["selected_text_vs_base"]["n10"]
    assert s["validity"]["unselected_not_all_failing"] is True and s["unselected_text_vs_base"]["n01"] == 45
    assert s["primary_claim_valid"] is False and "text_not_clustered_better_than_base_selected" in s["primary_claim_reasons"]


def test_coverage_of_0_95_with_mixed_unselected_outcomes_passes(ev):
    """45/909 unselected (coverage 0.9505 >= 0.90); text fails 40 of those cells and passes 5,
    so the unselected subset is not all-failing and the credited difference stays small."""
    recs = complete_run(ev)
    unselected = list(range(0, 909, 20))[:45]
    unselect_conversations(recs, unselected)
    for ci in unselected[:5]:
        recs[ci]["turns"]["2"]["arms"]["text_ledger"]["per_constraint"] = [True, True, True]
    s = summ(ev, recs)
    assert s["eligible"]["n_unselected"] == 45 and s["eligible"]["selected_fraction"] == 864 / 909
    assert s["eligible"]["selected_fraction"] >= ev.REGISTERED_COVERAGE == 0.90
    assert s["validity"]["ledger_coverage_ge_0.90"] is True
    u = s["unselected_text_vs_base"]
    assert u["n"] == 45 and u["n00"] == 40 and u["n01"] == 5
    assert s["validity"]["unselected_not_all_failing"] is True
    assert s["validity"]["text_beats_base_selected_clustered"] is True and s["validity"]["text_beats_base"] is True
    assert s["primary_claim_valid"] is True, s["primary_claim_reasons"]


def two_turn_run(ev, n=909, single_turn=()):
    """a complete run whose conversations have late turns 2 AND 3 (1 eligible outcome each,
    turn 3 a copy of turn 2 as in sol's constructions: 1,805 outcomes when 13 are single-turn)
    with text == base everywhere; returns (records, identity)."""
    recs = complete_run(ev, n=n)
    ident = identity(n)
    for ci, r in enumerate(recs):
        t = r["turns"]["2"]
        t["base"]["per_constraint"] = [True, True, True]
        t["arms"]["text_ledger"]["per_constraint"] = [True, True, True]
        t["arms"]["neural_ledger"]["per_constraint"] = [True, True, True]
        if ci not in single_turn:
            r["turns"]["3"] = copy.deepcopy(t)
            ident[ci]["turns"] = ["2", "3"]
    return recs, ident


def set_cell(rec, turn, *, base, text):
    """the eligible cell of one turn: base/text pass or fail; neural TIES text (diff 0)."""
    t = rec["turns"][turn]
    t["base"]["per_constraint"] = [base, True, True]
    t["arms"]["text_ledger"]["per_constraint"] = [text, True, True]
    t["arms"]["neural_ledger"]["per_constraint"] = [text, True, True]


def test_sol4_pooled_text_advantage_with_clustered_regression_is_invalid(ev):
    """sol round 4 HIGH (results/ledger-reverify4-sol.md): a complete 909-conversation /
    1,805-outcome record with pooled text-vs-base 606 improvements vs 605 regressions
    (+0.0554 points, McNemar p = 0.5) but text better in only 303 conversations and worse
    in 605: conversation-clustered mean text - base = -0.6601 points.  Every other gate
    passes.  ROUND 4 ruling: non-vacuity is CONVERSATION-CLUSTERED (registered one-sided
    95% lower bound of the per-conversation mean over selected eligible outcomes > 0);
    the pooled n01 > n10 is descriptive only.
    Shape: 13 single-turn conversations regress (-100); 592 two-turn conversations regress
    on one turn (-50); 303 two-turn conversations improve on both (+100); 1 tied."""
    recs, ident = two_turn_run(ev, single_turn=range(13))
    for ci in range(13):
        set_cell(recs[ci], "2", base=True, text=False)
    for ci in range(13, 605):
        set_cell(recs[ci], "2", base=True, text=False)
    for ci in range(605, 908):
        set_cell(recs[ci], "2", base=False, text=True)
        set_cell(recs[ci], "3", base=False, text=True)
    s = summ(ev, recs, ident=ident)
    assert s["turns"] == 1805 and s["eligible"]["n"] == 1805 and s["eligible"]["selected_fraction"] == 1.0
    assert s["validity"]["complete_cohort"] and s["validity"]["expected_turns_present"] and s["validity"]["records_identity"]
    pooled = s["selected_text_vs_base"]
    assert pooled["n"] == 1805 and pooled["n01"] == 606 and pooled["n10"] == 605
    assert abs(pooled["improve_points"] - 100.0 / 1805) < 1e-12 and abs(pooled["improve_points"] - 0.0554) < 5e-5
    assert pooled["mcnemar_improve_p_exploratory"] == 0.5
    assert s["validity"]["text_vs_base_selected_pooled"] is True          # the old pooled gate is fooled ...
    assert s["validity"]["text_beats_base"] is True
    cl = s["text_vs_base_selected_clustered"]
    assert cl["k"] == 909
    assert abs(cl["mean"] - (-600.0 / 909)) < 1e-9 and abs(cl["mean"] - (-0.6601)) < 5e-5
    assert cl["lower_bound"] < cl["mean"] < 0
    assert cl["conversations_text_better"] == 303 and cl["conversations_text_worse"] == 605
    assert s["validity"]["text_beats_base_selected_clustered"] is False  # ... the registered clustered one is not
    assert s["primary"]["clustered"]["upper_bound"] < 2.0                # neural ties text: NI alone would pass
    assert s["primary_claim_valid"] is False
    assert s["primary_claim_reasons"] == ["text_not_clustered_better_than_base_selected"]
    # and pooled-vs-clustered disagreement is exactly the lesson: n01 > n10 must not be a gate
    assert "text_vs_base_selected_pooled" not in s["primary_claim_reasons"]


def test_text_better_in_most_conversations_passes_the_clustered_gate(ev):
    """positive case: text improves the eligible cell on both turns of 600 conversations,
    regresses on one turn of 200 and ties on 109: a clear clustered margin."""
    recs, ident = two_turn_run(ev)
    for ci in range(600):
        set_cell(recs[ci], "2", base=False, text=True)
        set_cell(recs[ci], "3", base=False, text=True)
    for ci in range(600, 800):
        set_cell(recs[ci], "2", base=True, text=False)
    s = summ(ev, recs, ident=ident)
    cl = s["text_vs_base_selected_clustered"]
    assert cl["k"] == 909 and abs(cl["mean"] - (600 * 100.0 - 200 * 50.0) / 909) < 1e-9
    assert cl["conversations_text_better"] == 600 and cl["conversations_text_worse"] == 200
    assert cl["lower_bound"] > 0 and cl["lower_bound"] < cl["mean"]
    assert s["validity"]["text_beats_base_selected_clustered"] is True and s["validity"]["text_vs_base_selected_pooled"] is True
    assert s["primary_claim_valid"] is True, s["primary_claim_reasons"]


def test_tiny_positive_clustered_mean_with_nonpositive_lower_bound_fails(ev):
    """boundary: text better in ONE conversation of 909 (pooled n01 = 1 > n10 = 0, clustered
    mean +0.11 points) -> the continuity-corrected lower bound is <= 0 and the gate fails."""
    recs, ident = two_turn_run(ev)
    set_cell(recs[500], "2", base=False, text=True)
    s = summ(ev, recs, ident=ident)
    cl = s["text_vs_base_selected_clustered"]
    assert cl["k"] == 909 and abs(cl["mean"] - 50.0 / 909) < 1e-12 and cl["mean"] > 0
    assert cl["lower_bound"] <= 0
    assert s["validity"]["text_vs_base_selected_pooled"] is True and s["selected_text_vs_base"]["n01"] == 1
    assert s["validity"]["text_beats_base_selected_clustered"] is False
    assert s["primary_claim_valid"] is False
    assert "text_not_clustered_better_than_base_selected" in s["primary_claim_reasons"]
    # exact zero: text == base everywhere -> mean 0, lower bound = -100/k
    recs, ident = two_turn_run(ev)
    s = summ(ev, recs, ident=ident)
    cl = s["text_vs_base_selected_clustered"]
    assert cl["mean"] == 0.0 and cl["lower_bound"] == -100.0 / 909
    assert s["validity"]["text_beats_base_selected_clustered"] is False


def test_sub_registered_cohort_is_a_falsification_only_slice(ev):
    """Ruling (iii): a slice (cohort_size < 909) can REJECT non-inferiority but never
    establish it; every other condition is still reported so the slice shows what it meets."""
    recs = complete_run(ev, n=113)
    s = summ(ev, recs, cohort_size=113, ident=identity(113))
    assert s["slice_role"] == "falsification_only"
    assert s["primary_claim_valid"] is False
    assert "falsification_only_slice" in s["primary_claim_reasons"]
    v = s["validity"]
    assert v["registered_cohort"] is False and v["falsification_only_slice"] is False
    assert v["complete_cohort"] is True and v["records_identity"] is True and v["expected_turns_present"] is True
    assert v["ledger_coverage_ge_0.90"] is True and v["text_beats_base_selected_clustered"] is True
    assert v["clustered_bound_below_margin"] is True  # the slice's own bound, reported but not claimable
    # and the slice CAN still reject: neural drops the eligible constraint on 20/113 conversations
    for r in recs[:20]:
        r["turns"]["2"]["arms"]["neural_ledger"]["per_constraint"] = [False, True, True]
    s2 = summ(ev, recs, cohort_size=113, ident=identity(113))
    assert s2["primary"]["non_inferior"] is False and s2["slice_role"] == "falsification_only"
    # the full registered cohort is not a slice
    assert summ(ev, complete_run(ev))["slice_role"] == "registered_cohort"
    assert "falsification_only_slice" not in summ(ev, complete_run(ev))["primary_claim_reasons"]


def test_sol2_records_must_echo_the_registered_configuration(ev):
    for field, bad in (("top_k", 3), ("dose", 1.0), ("max_new", 64), ("deadline", 60.0)):
        recs = complete_run(ev)
        recs[42]["config"][field] = bad
        s = summ(ev, recs)
        assert s["primary_claim_valid"] is False and s["validity"]["records_echo_registered_config"] is False, field
    recs = complete_run(ev)
    del recs[42]["config"]
    assert summ(ev, recs)["validity"]["records_echo_registered_config"] is False


def test_control_incomplete_turns_are_excluded_from_neural_vs_specificity(ev):
    """finding 4 (conversation 145): a turn whose matched control could not be built for
    every selected span is disclosed and left out of the neural - specificity comparison."""
    recs = complete_run(ev, n=12)
    for r in recs:
        r["turns"]["2"]["arms"]["specificity"]["per_constraint"] = [False, True, True]
    recs[0]["turns"]["2"]["arms"]["specificity"]["control_incomplete"] = True
    recs[0]["turns"]["2"]["arms"]["specificity"]["control_tiers"] = ["none", "same_turn"]
    recs[0]["turns"]["2"]["arms"]["specificity"]["per_constraint"] = [True, True, True]  # would pull the mean down
    s = summ(ev, recs)
    ns = s["neural_vs_specificity"]
    assert ns["control_incomplete_turns"] == 1 and ns["clustered"]["clusters"] == 11 and ns["mean_points"] == 100.0


@pytest.mark.parametrize("break_", [
    "top_k", "dose", "max_new", "deadline", "heuristic", "segmenter", "unmeasured_tokens", "nonzero_tokens",
    "timeouts", "truncations", "text_not_better", "inactive_ledger", "bound", "duplicate_ci",
    "coverage", "unselected_all_failing", "text_not_better_selected",
])
def test_each_gate_condition_invalidates(ev, break_):
    recs, meta = complete_run(ev), good_meta(ev)
    if break_ in ("top_k", "dose", "max_new", "deadline"):
        meta[break_] = {"top_k": 3, "dose": 1.0, "max_new": 64, "deadline": 60.0}[break_]
    elif break_ == "heuristic":
        meta["automatic"] = False
        meta["salience_provenance"] = "heuristic"
    elif break_ == "segmenter":
        meta["segmenter"] = "stencil.ledger.segment_char_spans"
        meta["segmenter_identity_asserted"] = False
    elif break_ == "unmeasured_tokens":
        recs[5]["turns"]["2"]["arms"]["neural_ledger"]["context_tokens_measured"] = False
    elif break_ == "nonzero_tokens":
        recs[5]["turns"]["2"]["arms"]["neural_ledger"]["context_tokens_added"] = 1
    elif break_ == "timeouts":
        for r in recs[:19]:  # 19/909 = 2.09% > 2%
            r["turns"]["2"]["arms"]["neural_ledger"]["timed_out"] = True
    elif break_ == "truncations":
        for r in recs[:10]:
            r["turns"]["2"]["arms"]["text_ledger"]["timed_out"] = True
        for r in recs[10:19]:
            r["turns"]["2"]["arms"]["text_ledger"]["truncated"] = True
    elif break_ == "text_not_better":
        for r in recs:
            r["turns"]["2"]["arms"]["text_ledger"]["per_constraint"] = list(r["turns"]["2"]["base"]["per_constraint"])
    elif break_ == "inactive_ledger":
        t = recs[7]["turns"]["2"]
        t["arms"]["neural_ledger"]["selected_entries"] = []
        t["ledger_active"] = False
        for c in t["constraints"]:
            c["entry_selected"] = False
    elif break_ == "bound":
        for r in recs[:60]:  # neural drops the eligible constraint on 60 conversations: ~6.6 points
            r["turns"]["2"]["arms"]["neural_ledger"]["per_constraint"] = [False, True, True]
    elif break_ == "duplicate_ci":
        recs[1] = copy.deepcopy(recs[0])
    elif break_ == "coverage":  # 91 unselected with mixed outcomes: 818/909 = 0.8999 < 0.90
        unselect_conversations(recs, list(range(0, 909, 10))[:91])
        for ci in list(range(0, 909, 10))[:5]:
            recs[ci]["turns"]["2"]["arms"]["text_ledger"]["per_constraint"] = [True, True, True]
    elif break_ == "unselected_all_failing":  # coverage fine (0.99) but text fails 100% of the unselected
        unselect_conversations(recs, list(range(0, 909, 100)))
    elif break_ == "text_not_better_selected":  # text == base on selected cells, better only on 9 unselected
        for r in recs:
            r["turns"]["2"]["arms"]["text_ledger"]["per_constraint"] = list(r["turns"]["2"]["base"]["per_constraint"])
        unselect_conversations(recs, list(range(0, 909, 100)), text_fails=False)
        for ci in range(0, 909, 100):
            recs[ci]["turns"]["2"]["base"]["per_constraint"] = [False, True, True]
            recs[ci]["turns"]["2"]["arms"]["text_ledger"]["per_constraint"] = [True, True, True]
    s = summ(ev, recs, meta)
    assert s["primary_claim_valid"] is False, break_
    assert s["primary_claim_reasons"], break_
    if break_ == "bound":
        assert s["primary"]["clustered"]["upper_bound"] > 2.0 and s["primary"]["non_inferior"] is False
    if break_ in ("timeouts", "truncations"):
        assert s["validity"]["timeouts_truncations_le_2pct"] is False
    if break_ == "coverage":
        assert "ledger_coverage_below_0.90" in s["primary_claim_reasons"] and s["validity"]["unselected_not_all_failing"] is True
    if break_ == "unselected_all_failing":
        assert s["primary_claim_reasons"] == ["unselected_not_all_failing"]
    if break_ == "text_not_better_selected":
        assert s["primary_claim_reasons"] == ["text_not_clustered_better_than_base_selected"] and s["validity"]["text_beats_base"] is True


def test_estimand_excludes_fresh_and_noninsertable_and_credits_only_selected(ev):
    """Finding 2/4: fresh constraints (origin == current turn) and non-insertable families are
    out; a neural pass on an aged constraint whose entry was NOT selected is not credited."""
    # entry for turn 1 exists but selection picked nothing linked to constraint 0
    ledger = [ENTRY1, {**ENTRY1, "text": "Other aged sentence.", "span": [12, 15], "instruction_ids": []}, ENTRY2]
    t = turn_record(base=[False, False, False], text=[True, True, True], neural=[True, True, True],
                    spec=[True, True, True], ledger=ledger, aged=[0, 1], selected=[1])
    for c in t["constraints"]:
        c["entry_indices"] = [0] if c["origin_turn"] == 1 else [2]
        c["entry_selected"] = False
    rows = ev.outcome_rows(t)
    assert [(r["id"], r["eligible"]) for r in rows] == [(IDS[0], True), (IDS[1], False), (IDS[2], False)]
    el = [r for r in rows if r["eligible"]][0]
    assert el["text"] is True and el["neural_raw"] is True and el["neural"] is False and el["entry_selected"] is False
    assert el["diff_points"] == 100.0  # text - credited neural, in points
    # the same turn with the linked entry selected credits the pass
    t["constraints"][0]["entry_selected"] = True
    assert [r for r in ev.outcome_rows(t) if r["eligible"]][0]["neural"] is True


def test_neural_minus_specificity_is_reported_directly_with_clustered_bound(ev):
    recs = complete_run(ev, n=12)
    for r in recs:
        r["turns"]["2"]["arms"]["specificity"]["per_constraint"] = [False, True, True]
    s = summ(ev, recs)
    ns = s["neural_vs_specificity"]
    assert ns["sign"] == "neural - specificity (points; positive = neural better)"
    assert ns["mean_points"] == 100.0 and ns["clustered"]["method"] == "t_continuity" and ns["clustered"]["clusters"] == 12
    assert ns["lower_bound"] == 100.0 - 100.0 / 12 and ns["upper_bound"] == 100.0 + 100.0 / 12  # zero variance + one flip


@pytest.mark.skipif(not (TOK_PATH.exists() and DATA_PATH.exists()), reason="tokenizer/data not present")
def test_cpu_preflight_builds_every_diagnostic_turn_with_real_salience(ev):
    """Finding 3: the runner's path crashed on conversation 769 turns 2/3."""
    from tokenizers import Tokenizer

    from stencil import salience
    from stencil.ledger import resolve_salience
    tok = Tokenizer.from_file(str(TOK_PATH))
    rows = [json.loads(line) for line in DATA_PATH.read_text().splitlines()]
    todo = ev.diagnostic_indices(rows)
    assert len(todo) == 113 and 769 in todo
    sal = resolve_salience()
    assert ev.assert_real_segmenter(sal) == ev.SEGMENTER_IDENTITY
    assert sal.segment is salience.split_sentences
    base_dir = ROOT / "results" / "qwen" / "b4-multiif-base"
    base_records = ([json.loads((base_dir / f"conv-{i:03d}.json").read_text()) for i in range(len(rows))]
                    if (base_dir / "conv-908.json").exists() else None)  # the exact runner contexts when on disk
    stats = ev.preflight(rows, tok, sal, todo, base_records)
    assert stats["conversations"] == 113 and stats["turns"] == 221 and stats["errors"] == []
    assert stats["turns_with_aged_entries"] > 0 and stats["turns_with_aged_constraints"] > 0
    assert stats["linkage_granularity"] == {"origin_turn": 221}
    assert stats["segmenter"] == ev.SEGMENTER_IDENTITY
    # sol round 2 finding 4: the specificity control is DRY-CONSTRUCTED for every possible
    # top_k selection (every ordered choice of aged entries) of every turn; conversation 145
    # turn 2 (aged widths 34/19, longest free run 31) is reported incomplete, not a crash
    assert stats["control_dry_runs"] > 221 and stats["control_top_k"] == ev.REGISTERED["top_k"]
    assert {"ci": 145, "turn": 2} in stats["control_incomplete_turns"]
    assert stats["control_incomplete_turn_count"] == len(stats["control_incomplete_turns"]) >= 1
    assert base_records is not None, "the exact runner contexts are required for the control dry run"
    # sol round 3 ruling (i): the registered coverage gate (>= 0.90) is attainable on the slice:
    # 81/85 eligible constraints have a linked entry
    assert stats["eligible_constraints"] == 85 and stats["eligible_linked"] == 81
    assert stats["eligible_coverage"] == 81 / 85 and stats["eligible_coverage"] >= ev.REGISTERED_COVERAGE
    # and the bare-callable path sol found is NOT accepted by the identity assertion
    with pytest.raises(RuntimeError, match="segmenter"):
        ev.assert_real_segmenter(resolve_salience(sal.classify))


def test_preflight_fails_loudly_on_any_exception(ev, monkeypatch):
    from stencil.ledger import Salience

    def boom(text):
        raise RuntimeError("sentence not found in its own text")
    rows = [{"key": "k", "turn_1_prompt": json.dumps({"content": "a"}), "turn_1_instruction_id_list": "[]", "turn_1_kwargs": "[]",
             "turn_2_prompt": json.dumps({"content": "b"}), "turn_2_instruction_id_list": "[]", "turn_2_kwargs": "[]",
             "turn_3_prompt": ""}]

    class Tok:
        def encode(self, s):
            class E:
                ids = list(range(len(s)))
                offsets = [(i, i + 1) for i in range(len(s))]
            return E()
    with pytest.raises(RuntimeError, match=r"preflight.*ci=0.*turn=2.*sentence not found"):
        ev.preflight(rows, Tok(), Salience(lambda s: True, boom, "salience"), [0])


def test_preflight_dry_constructs_control_for_every_ordered_selection(ev, monkeypatch):
    """the dry run exercises matched_nonledger_control on the exact runner inputs for every
    ordered top_k choice of aged entries; an impossible window is COUNTED, an exception is raised."""
    import stencil.ledger as ledger_mod

    calls = []
    real = ledger_mod.matched_nonledger_control

    def spy(**kw):
        calls.append(kw)
        return real(**kw)
    monkeypatch.setattr(ledger_mod, "matched_nonledger_control", spy)
    rows = [{"key": "k", "turn_1_prompt": json.dumps({"content": "Use the word lantern. Do not use commas. Write in English."}),
             "turn_1_instruction_id_list": "[]", "turn_1_kwargs": "[]",
             "turn_2_prompt": json.dumps({"content": "Now shorter."}), "turn_2_instruction_id_list": "[]", "turn_2_kwargs": "[]",
             "turn_3_prompt": ""}]
    from tokenizers import Tokenizer
    if not TOK_PATH.exists():
        pytest.skip("tokenizer not present")
    from stencil.ledger import Salience, segment_char_spans
    stats = ev.preflight(rows, Tokenizer.from_file(str(TOK_PATH)), Salience(lambda s: True, segment_char_spans, "salience"), [0], top_k=2)
    assert stats["turns"] == 1 and stats["aged_entries"] == 3
    assert stats["control_dry_runs"] == len(calls) == 6  # 3 aged entries, ordered pairs
    assert all(len(c["selected"]) == 2 for c in calls)
    assert stats["control_incomplete_turn_count"] == 0 and stats["control_incomplete_turns"] == []

    def broken(**kw):
        raise ValueError("boom")
    monkeypatch.setattr(ledger_mod, "matched_nonledger_control", broken)
    with pytest.raises(RuntimeError, match=r"preflight.*ci=0.*turn=2.*boom"):
        ev.preflight(rows, Tokenizer.from_file(str(TOK_PATH)), Salience(lambda s: True, segment_char_spans, "salience"), [0], top_k=2)
