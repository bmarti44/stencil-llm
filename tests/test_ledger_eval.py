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
                "ledger.py", "salience.py", "tokenizer.json", "vendor/ifeval", "ledger_eval.py"):
        assert key in prov and len(prov[key]) == 64, key
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


def make_record(ci, turn, *, diagnostic=False):
    return {"ci": ci, "key": f"k{ci}", "diagnostic": diagnostic, "turns": {"2": turn}}


def complete_run(ev, n=909):
    """A run that PASSES every gate: text beats base on eligible outcomes, neural ties text,
    the ledger is active everywhere, tokens measured zero, no timeouts."""
    recs = []
    for ci in range(n):
        base = [False, True, True] if ci % 3 == 0 else [True, True, True]
        text = [True, True, True]
        neural = [True, True, True] if ci % 40 else [True, True, False]  # a fresh-constraint miss: NOT eligible
        recs.append(make_record(ci, turn_record(base=base, text=text, neural=neural, spec=[True, False, True],
                                                ledger=[ENTRY1, ENTRY2], aged=[0], selected=[0])))
    return recs


def test_complete_valid_run_passes_and_reports_estimand(ev):
    s = ev.summarize(complete_run(ev), good_meta(ev), cohort_size=ev.REGISTERED_COHORT)
    assert s["primary_claim_valid"] is True, s["primary_claim_reasons"]
    el = s["eligible"]
    assert el["n"] == 909 and el["n_conversations"] == 909  # aged AND insertable: only keywords:existence at origin 1
    assert el["definition"].startswith("aged")
    p = s["primary"]
    assert p["clustered"]["method"] == "t" and p["clustered"]["upper_bound"] == 0.0 and p["non_inferior"] is True
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
        recs.append(make_record(ci, t))
    s = ev.summarize(recs, good_meta(ev), cohort_size=ev.REGISTERED_COHORT)
    assert s["primary_claim_valid"] is False
    v = s["validity"]
    assert v["ledger_active_on_credited_turns"] is False and v["text_beats_base"] is False
    assert s["empty_ledger_turns"] == 909


def test_sol_adversarial_favorable_partial_record_is_invalid(ev):
    """Finding 1: a favorable four-cell partial record."""
    recs = complete_run(ev, n=4)
    s = ev.summarize(recs, good_meta(ev), cohort_size=ev.REGISTERED_COHORT)
    assert s["primary_claim_valid"] is False and s["validity"]["complete_cohort"] is False
    assert s["primary"]["clustered"]["method"] == "cluster_bootstrap"
    # and passing the partial count as the cohort size does not launder it: the registered size is checked
    s2 = ev.summarize(recs, good_meta(ev), cohort_size=4)
    assert s2["primary_claim_valid"] is False and s2["validity"]["registered_cohort"] is False


@pytest.mark.parametrize("break_", [
    "top_k", "dose", "max_new", "deadline", "heuristic", "segmenter", "unmeasured_tokens", "nonzero_tokens",
    "timeouts", "truncations", "text_not_better", "inactive_ledger", "bound", "duplicate_ci",
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
    s = ev.summarize(recs, meta, cohort_size=ev.REGISTERED_COHORT)
    assert s["primary_claim_valid"] is False, break_
    assert s["primary_claim_reasons"], break_
    if break_ == "bound":
        assert s["primary"]["clustered"]["upper_bound"] > 2.0 and s["primary"]["non_inferior"] is False
    if break_ in ("timeouts", "truncations"):
        assert s["validity"]["timeouts_truncations_le_2pct"] is False


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
    s = ev.summarize(recs, good_meta(ev), cohort_size=ev.REGISTERED_COHORT)
    ns = s["neural_vs_specificity"]
    assert ns["sign"] == "neural - specificity (points; positive = neural better)"
    assert ns["mean_points"] == 100.0 and ns["clustered"]["method"] == "t" and ns["clustered"]["clusters"] == 12
    assert ns["lower_bound"] == 100.0 and ns["upper_bound"] == 100.0  # zero variance


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
