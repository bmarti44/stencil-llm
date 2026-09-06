"""Runtime values, calibration, target selection, and setup-stop consumers."""

import copy
import json

import numpy as np
import pytest

from scripts import focus3_gate as g
from scripts import focus3_gate_v4 as v4
from scripts import train_relations as trainer
from stencil import focus3 as f


class Capture:
    def __init__(self):
        self.pairs = []

    def relations(self, pairs):
        self.pairs.extend(pairs)
        return [
            dict(probabilities=[1.0, 0.0, 0.0, 0.0, 0.0], overflow=False) for _ in pairs
        ]

    def admission(self, spans, previous):
        return [dict(probabilities=[1.0, 0.0, 0.0], overflow=False) for _ in spans]


def test_every_runtime_pair_has_training_values_and_normalized_rendering():
    classifier = Capture()
    runtime = f.Runtime(classifier)
    for i, status in enumerate(("live", "superseded", "cancelled", "completed")):
        row = runtime.register.add(
            "Always sort ascending for task Cedar.",
            "opaque-secret-key",
            "Cedar",
            "sort",
            i,
            0,
        )
        row.status = status
    runtime.register.add(
        "Keep tag equal to 7 for all tasks.", "new:8:99", "*", "sort", 8, 99
    )
    runtime.previous = (
        "Earlier context. Keep this preceding sentence. "
        "Sort request for task Cedar: payload [3, 1]."
    )
    runtime.task = "Cedar"
    prose = "Task Cedar is complete. Work on task Maple."
    trace = runtime.update(
        prose + " Sort request for task Maple: payload [4, 2]; reply as compact JSON.",
        9,
    )
    assert (
        len(classifier.pairs) == 6
    )  # v5: Cedar addresses all five rows; Maple addresses only global.
    assert {p["old_rule"]["status"] for p in classifier.pairs} == {
        "live",
        "superseded",
        "cancelled",
        "completed",
    }
    assert {p["old_rule"]["scope"] for p in classifier.pairs} == {
        "global",
        "task:Cedar",
    }
    for p in classifier.pairs:
        rule = p["old_rule"]
        assert set(rule) == {"text", "status", "scope", "key"}
        assert rule["key"] in ("sort-order", "tag")
        assert p["prev_user"] == "Keep this preceding sentence."
        assert len(f.sentences(p["prev_user"])) == 1
        assert p["message"] == prose
        assert (
            p["message"][p["target_span"]["start"] : p["target_span"]["end"]]
            == p["target_span"]["text"]
        )
        row = dict(p, label="none", author="astra")
        normalized = trainer.normalize_row(row)
        assert not normalized["span_offsets_repaired"]
        assert f.pair_input(p) == trainer.render_pair(normalized)
    assert (
        len(trace["admissions"]) == 3
    )  # Original admission contract includes request.
    classifier.pairs.clear()
    runtime.update("Sort request for task Maple: payload [2, 1].", 10)
    assert classifier.pairs == []
    runtime.update(
        "Continue task Maple; Sort request for task Maple: payload [2, 1].", 11
    )
    assert len(classifier.pairs) == 1  # Only global overlaps Maple in v5.
    for p in classifier.pairs:
        assert p["prev_user"] is None
        assert p["message"] == "Continue task Maple;"
        assert f.pair_input(p) == trainer.render_pair(
            trainer.normalize_row(dict(p, label="none", author="astra"))
        )


def test_same_kind_highest_probability_target_wins_not_first():
    class Classifier(Capture):
        def relations(self, pairs):
            results = []
            for p in pairs:
                prob = {"tag": 0.90, "sort-order": 0.97, "instruction": 0.99}[
                    p["old_rule"]["key"]
                ]
                results.append(
                    dict(probabilities=[1 - prob, 0.0, prob, 0.0, 0.0], overflow=False)
                )
            return results

    runtime = f.Runtime(Classifier())
    tag = runtime.register.add("Keep tag equal to 7.", "tag", "*", "sort", 0, 0)
    order = runtime.register.add(
        "Always sort ascending.", "order", "Cedar", "sort", 0, 25
    )
    other = runtime.register.add("Write Python code.", "code", "Cedar", "code", 0, 60)
    runtime.task = "Cedar"
    trace = runtime.update("Cancel the sorting rule for task Cedar.", 1)
    assert trace["applied"] == [
        dict(
            label="cancels",
            target=order.id,
            span="Cancel the sorting rule for task Cedar.",
        )
    ]
    assert order.status == "cancelled"
    assert tag.status == other.status == "live"


def test_none_guard_runtime_boundary():
    class Classifier(Capture):
        pnone = f.NONE_PAIR_THRESHOLD

        def relations(self, pairs):
            return [
                dict(
                    probabilities=[self.pnone, 1 - self.pnone, 0.0, 0.0, 0.0],
                    overflow=False,
                )
                for _ in pairs
            ]

        def admission(self, spans, previous):
            return [
                dict(probabilities=[0.01, 0.99, 0.0], overflow=False) for _ in spans
            ]

    for offset, accepted in [(0.0, True), (-1e-8, False)]:
        c = Classifier()
        c.pnone += offset
        runtime = f.Runtime(c)
        runtime.register.add("Keep tag equal to 7.", "tag", "*", "sort", 0, 0)
        trace = runtime.update("Always sort ascending for task Cedar.", 1)
        assert trace["admissions"][0]["accepted"] is accepted
        assert len(runtime.register.rows) == 1 + accepted


def test_calibration_fallback_is_exact_registered_rule():
    none = np.linspace(0.1, 0.95, 100)
    positive = np.array([0.89] * 6 + [0.05] * 94)
    pnone = np.concatenate([none, positive])
    probabilities = np.column_stack([pnone] + [(1 - pnone) / 4] * 4)
    r = v4.calibration_rule(np.log(probabilities), [0] * 100 + [1] * 100, [False] * 200)
    assert r["candidates"][0]["positive_as_none"] == 6
    assert r["chosen"]["quantile"] == 0.95 and r["eligible"]
    assert r["chosen"]["threshold"] == pytest.approx(np.quantile(none, 0.95))
    with pytest.raises(AssertionError, match="overflow"):
        v4.calibration_rule(np.log(probabilities), [0] * 100 + [1] * 100, [True] * 200)


def gold_records():
    bank = g.build_bank(v4.author_fixture(), setup_seed=30321, gate_seed=30322)
    g.validate_bank(bank)
    records = []
    for ep in bank["setup"]:
        oracle = f.Oracle()
        for ti, turn in enumerate(ep["turns"]):
            gold = oracle.update(turn["text"], ti, turn["events"])
            trace = dict(gold, overflow=False, pairs=[])
            records.append(
                dict(
                    episode=ep["id"],
                    turn_index=ti,
                    turn=turn,
                    trace=trace,
                    event_checks=v4.event_checks(turn, ti, trace, gold),
                )
            )
    return bank, records


def test_setup_consumer_all_admissions_and_at_most_one_transition_miss():
    bank, records = gold_records()
    assert {e["seed"] for e in bank["setup"]} == {30321}
    assert {e["seed"] for e in bank["gate"]} == {30322}
    result = v4.eligibility_summary(records)
    assert result["eligible"]
    assert result["counts"]["admissions"] == dict(passed=36, total=36)
    assert result["counts"]["transitions"] == dict(passed=12, total=12)
    assert len(result["diagnostics"]["known_phrasings"]) == 3
    bad = copy.deepcopy(records)
    transitions = [c for r in bad for c in r["event_checks"] if c["label"] != "admit"]
    transitions[0]["passed"] = False
    assert v4.eligibility_summary(bad)["eligible"]
    transitions[1]["passed"] = False
    assert not v4.eligibility_summary(bad)["eligible"]
    bad = copy.deepcopy(records)
    next(c for r in bad for c in r["event_checks"] if c["label"] == "admit")[
        "passed"
    ] = False
    assert not v4.eligibility_summary(bad)["eligible"]
    assert not v4.eligibility_summary(records[:-1])["eligible"]


def test_replacement_requires_correct_source_status_not_just_new_row():
    bank, _ = gold_records()
    ep = bank["setup"][0]
    oracle = f.Oracle()
    for ti, turn in enumerate(ep["turns"][:3]):
        gold = oracle.update(turn["text"], ti, turn["events"])
    trace = copy.deepcopy(gold)
    target = turn["events"][0]["target"]
    next(r for r in trace["after"] if r["id"] == target)["status"] = "live"
    result = v4.event_checks(turn, ti, trace, gold)
    assert result[0]["state_matches"]  # New row alone is insufficient.
    assert not result[0]["source_state_matches"] and not result[0]["passed"]


def test_ineligible_preflight_prohibits_gpu_claim(tmp_path, monkeypatch):
    monkeypatch.setattr(v4, "OUT", tmp_path)
    monkeypatch.setattr(v4, "verify_freeze", lambda: None)
    (tmp_path / "setup-admission").mkdir()
    (tmp_path / "setup-admission/summary.json").write_text(
        json.dumps(dict(eligible=False))
    )
    monkeypatch.setattr(
        g, "claim_gpu", lambda: pytest.fail("GPU reached after setup failure")
    )
    with pytest.raises(AssertionError, match="INELIGIBLE-ADMISSION"):
        v4.run()


def test_enrichment_is_90_quarantined_relatives_without_verbatim_bank_rows():
    rows = [
        json.loads(line)
        for line in (g.ROOT / "data/classifier/relations/astra-enrich-2.jsonl")
        .read_text()
        .splitlines()
    ]
    assert len(rows) == 90 and len({r["message"] for r in rows}) == 90
    for label in ("supersedes", "cancels", "completes"):
        group = [r for r in rows if r["label"] == label]
        assert len(group) == 30 and len({r["scenario_id"] for r in group}) == 1
        assert all(r["parent_id"] == f"astra-enrich-2-{label}-00" for r in group)
        assert all(r["id"] != r["parent_id"] for r in group)
    for row in rows:
        assert row["evaluation_derived"] and row["use_requires_later_refit"]
        assert not row["eligible_for_heldout"]
        assert not trainer.normalize_row(row)["span_offsets_repaired"]


def test_foreground_preflight_writer_and_audit_consumer(tmp_path, monkeypatch):
    class Classifier:
        @staticmethod
        def prediction(model_input, n, winner):
            logits = np.zeros(n)
            logits[winner] = 8.0
            ex = np.exp(logits)
            return dict(
                logits=logits.tolist(),
                probabilities=(ex / ex.sum()).tolist(),
                model_input=model_input,
                overflow=False,
            )

        def relations(self, pairs):
            return [self.prediction(f.pair_input(p), 5, 0) for p in pairs]

        def admission(self, spans, previous):
            return [
                self.prediction(p, 3, 0) for p in f.admission_inputs(spans, previous)
            ]

    bank, _ = gold_records()
    calibration = json.loads((v4.OUT / "calibration.json").read_text())
    # Exercise the historical v4 writer/calibration consumer with its own
    # retired threshold; production v5 uses the separate v5 replay/audit.
    monkeypatch.setattr(f, "NONE_PAIR_THRESHOLD", calibration["chosen"]["threshold"])
    monkeypatch.setattr(v4, "OUT", tmp_path)
    monkeypatch.setattr(g, "OUT", tmp_path)
    monkeypatch.setattr(v4, "verify_freeze", lambda: dict(hashes={}))
    monkeypatch.setattr(v4, "source_hashes", lambda: {})
    monkeypatch.setattr(f, "FrozenClassifier", Classifier)
    g.write(tmp_path / "bank.json", bank)
    g.write(tmp_path / "freeze.json", {})
    g.write(tmp_path / "calibration.json", calibration)
    v4.preflight()
    assert len(list((tmp_path / "setup-admission/records").glob("*.json"))) == 96
    assert (
        json.loads((tmp_path / "summary.json").read_text())["verdict"]
        == "INELIGIBLE-ADMISSION"
    )
    v4.audit()
    assert json.loads((tmp_path / "audit.json").read_text())["audit"] == "PASS"
