"""Registered v5 runtime and exact setup-stop consumer parity, CPU only."""

import copy

import numpy as np
import pytest

from scripts import focus3_gate_v5 as v5
from stencil import focus3 as f
from tests.test_focus3_gate_v4 import gold_records


class Classifier:
    def __init__(self, pnone=1.0, prule=0.99, label="none"):
        self.pnone, self.prule, self.label = pnone, prule, label
        self.pairs = []

    def relations(self, pairs):
        self.pairs.extend(pairs)
        p = [self.pnone, 1 - self.pnone, 0.0, 0.0, 0.0]
        if self.label != "none":
            p = [0.001] * 5
            p[f.LABELS.index(self.label)] = 0.996
        return [dict(probabilities=p, overflow=False) for _ in pairs]

    def admission(self, spans, previous):
        return [
            dict(probabilities=[1 - self.prule, self.prule, 0.0], overflow=False)
            for _ in spans
        ]


@pytest.mark.parametrize(
    "pnone,accepted", [(0.499999, False), (0.5, True), (0.9, True)]
)
def test_positive_side_none_guard_consumer(pnone, accepted):
    assert f.NONE_PAIR_THRESHOLD == 0.5
    c = Classifier(pnone=pnone)
    rt = f.Runtime(c)
    rt.register.add("Keep tag equal to 7.", "tag", "*", "sort", 0, 0)
    tr = rt.update("Always sort ascending for task Cedar.", 1)
    assert len(c.pairs) == 1
    assert tr["admissions"][0]["accepted"] is accepted
    assert len(rt.register.rows) == 1 + accepted


def test_scope_filter_excludes_wrong_task_before_scoring_without_losing_admission():
    class WrongTask(Classifier):
        def relations(self, pairs):
            assert all(p["old_rule"]["scope"] == "global" for p in pairs)
            return super().relations(pairs)

    c = WrongTask()
    rt = f.Runtime(c)
    rt.task = "CedarA"
    rt.register.add("Keep tag equal to 7.", "tag", "*", "sort", 0, 0)
    old = rt.register.add(
        "Always sort ascending for task CedarA.", "order", "CedarA", "sort", 0, 30
    )
    tr = rt.update("Work on task CedarB. Always sort descending for task CedarB.", 1)
    assert len(c.pairs) == 2  # Global survives; sibling task is never scored.
    assert tr["admissions"][1]["accepted"]
    assert old.status == "live"


def test_scope_is_per_span_in_message_with_multiple_tasks():
    c = Classifier(prule=0)
    rt = f.Runtime(c)
    for i, task in enumerate(["Cedar", "Maple"]):
        rt.register.add(
            f"Always sort ascending for task {task}.", task, task, "sort", 0, i
        )
    rt.update("Cancel the sorting rule for task Cedar. Work on task Maple.", 1)
    assert len(c.pairs) == 2
    assert [p["old_rule"]["scope"] for p in c.pairs] == ["task:Cedar", "task:Maple"]


@pytest.mark.parametrize(
    "span,prule,expected",
    [
        ("Restore the previous sorting requirement for task Cedar.", 0.9499, False),
        ("Restore the previous sorting requirement for task Cedar.", 0.95, True),
        ("Restore: Always sort ascending for task Cedar.", 0.01, True),
        ("Continue task Cedar;", 0.99, False),
        ("Work on task Cedar.", 0.99, False),
        ("Return to task Cedar;", 0.99, False),
        ("Reply exactly calm.", 0.01, False),
    ],
)
def test_reinstatement_requires_own_rule_bearing_span(span, prule, expected):
    c = Classifier(prule=prule, label="reinstates")
    rt = f.Runtime(c)
    rt.task = "Cedar"
    old = rt.register.add(
        "Always sort ascending for task Cedar.", "order", "Cedar", "sort", 0, 0
    )
    old.status = "cancelled"
    tr = rt.update(span, 1)
    applied = [p for p in tr["applied"] if p["label"] == "reinstates"]
    assert bool(applied) is expected
    assert len(c.pairs) == 1
    if expected:
        assert rt.register.rows[-1].text == old.text
        assert rt.register.rows[-1].status == "live"


def test_reinstatement_does_not_borrow_rule_admission_from_neighbor():
    class Neighbor(Classifier):
        def admission(self, spans, previous):
            return [
                dict(probabilities=[0.999, 0.001, 0.0], overflow=False),
                dict(probabilities=[0.001, 0.999, 0.0], overflow=False),
            ]

    rt = f.Runtime(Neighbor(label="reinstates"))
    rt.task = "Cedar"
    old = rt.register.add(
        "Always sort ascending for task Cedar.", "order", "Cedar", "sort", 0, 0
    )
    old.status = "cancelled"
    tr = rt.update("Continue task Cedar. Always sort ascending for task Cedar.", 1)
    assert len(tr["applied"]) == 1
    assert tr["applied"][0]["span"] == "Always sort ascending for task Cedar."


def test_unauthorized_counter_matches_label_target_span_and_multiplicity():
    _, records = gold_records()
    assert v5.eligibility_summary(records)["eligible"]
    baseline = copy.deepcopy(records)
    for mutation in ["target", "span", "label", "duplicate", "extra_admit"]:
        records = copy.deepcopy(baseline)
        r = next(
            r for r in records if any("target" in a for a in r["trace"]["applied"])
        )
        a = next(a for a in r["trace"]["applied"] if "target" in a)
        if mutation in ["target", "span", "label"]:
            a[mutation] = "wrong"
        elif mutation == "duplicate":
            r["trace"]["applied"].append(copy.deepcopy(a))
        else:
            r["trace"]["applied"].append(dict(label="admit", span="Unexpected rule."))
        result = v5.eligibility_summary(records)
        assert not result["eligible"]
        assert result["unauthorized"]["applications"] == 1
        assert result["unauthorized"]["records"] == 1
    records = copy.deepcopy(baseline)
    records[-1] = copy.deepcopy(records[-2])
    assert not v5.eligibility_summary(records)["complete"]


def test_per_label_stop_and_missing_support():
    _, records = gold_records()
    # One miss remains eligible at 11/12, three of four for its label.
    transitions = [
        c for r in records for c in r["event_checks"] if c["label"] == "supersedes"
    ]
    transitions[0]["passed"] = False
    assert v5.eligibility_summary(records)["eligible"]
    transitions[1]["passed"] = False
    result = v5.eligibility_summary(records)
    assert not result["eligible"] and not result["per_label_pass"]
    assert result["diagnostics"]["per_label"]["reinstates"]["recall"] is None


def test_dev_table_fixed_guard_does_not_choose_none_quantile():
    p = np.array([[0.6, 0.1, 0.1, 0.1, 0.1], [0.3, 0.6, 0.04, 0.03, 0.03]])
    result = v5.dev_tables(np.log(p), np.array([0, 1]), [False, False])
    row = result["guard"][0]
    assert row == dict(
        threshold=0.5, none_pass=1, none_total=1, positive_pass=0, positive_total=1
    )
    assert result["arms"]["C"] == f.THRESHOLDS
    assert result["arms"]["C'"]["supersedes"] == 0.8


def test_cpu_writer_audit_and_one_shot_consumer(tmp_path, monkeypatch):
    import json

    from scripts import focus3_gate as g

    class Fake:
        branches = {}

        @staticmethod
        def prediction(model_input, n):
            logits = np.array([8.0] + [0.0] * (n - 1))
            ex = np.exp(logits)
            return dict(
                logits=logits.tolist(),
                probabilities=(ex / ex.sum()).tolist(),
                model_input=list(model_input),
                overflow=False,
            )

        def relations(self, pairs):
            return [self.prediction(f.pair_input(p), 5) for p in pairs]

        def admission(self, spans, previous):
            return [self.prediction(p, 3) for p in f.admission_inputs(spans, previous)]

    monkeypatch.setattr(v5, "OUT", tmp_path)
    monkeypatch.setattr(v5, "verify_freeze", lambda: {})
    monkeypatch.setattr(f, "FrozenClassifier", Fake)
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "")
    g.write(tmp_path / "freeze.json", {})
    z = np.load(v5.v4.DEV, allow_pickle=False)
    g.write(
        tmp_path / "dev-tables.json",
        v5.dev_tables(z["logits"], z["labels"], z["overflow"]),
    )
    v5.replay()
    v5.audit()
    assert json.loads((tmp_path / "audit.json").read_text())["records"] == 96
    assert not json.loads((tmp_path / "summary.json").read_text())["eligible"]
    with pytest.raises(AssertionError, match="already replayed"):
        v5.replay()


def test_atomic_completes_trace_carries_span_for_unauthorized_consumer():
    rt = f.Runtime(Classifier(prule=0, label="completes"))
    rt.task = "Cedar"
    for i, text in enumerate(["Always sort ascending.", "Always include a tag."]):
        rt.register.add(text, str(i), "Cedar", "sort", 0, i)
    span = "Task Cedar is complete."
    tr = rt.update(span, 1)
    assert len(tr["applied"]) == 2
    assert all(p["span"] == span for p in tr["applied"])
    record = dict(
        episode="fixture",
        turn_index=1,
        trace=tr,
        turn=dict(
            events=[
                dict(label="completes", target=f"0:{i}", span=span) for i in range(2)
            ]
        ),
    )
    assert v5.unauthorized([record])["applications"] == 0
