"""Training-context and actual pre-gate stop consumer contracts; synthetic only."""

import copy
import json

import pytest

from scripts import focus3_gate as g
from scripts import focus3_gate_v3 as v3
from stencil import focus3 as f


def test_runtime_admission_uses_preceding_sentences_and_prefix():
    classifier = f.FrozenClassifier.__new__(f.FrozenClassifier)
    observed = []

    def infer(branch, inputs, limit):
        if branch == "relations":
            return [
                dict(probabilities=[1.0, 0.0, 0.0, 0.0, 0.0], overflow=False)
                for _ in inputs
            ]
        observed.extend(inputs)
        assert limit == 192
        return [
            dict(probabilities=[1.0, 0.0, 0.0], model_input=p, overflow=False)
            for p in inputs
        ]

    classifier.infer = infer
    runtime = f.Runtime(classifier)
    runtime.update("First. Second. Third. Fourth.", 0)
    runtime.update("Work on task Cedar. Always sort ascending for task Cedar.", 1)
    assert observed == [
        ("(no context)", "[user] First."),
        ("user: First.", "[user] Second."),
        ("user: First. user: Second.", "[user] Third."),
        ("user: First. user: Second. user: Third.", "[user] Fourth."),
        ("user: Second. user: Third. user: Fourth.", "[user] Work on task Cedar."),
        (
            "user: Third. user: Fourth. user: Work on task Cedar.",
            "[user] Always sort ascending for task Cedar.",
        ),
    ]


def test_relation_consumed_span_still_logs_admission():
    class Classifier:
        def relations(self, pairs):
            return [
                dict(probabilities=[0.0, 0.0, 1.0, 0.0, 0.0], overflow=False)
                for _ in pairs
            ]

        def admission(self, spans, previous):
            return [
                dict(probabilities=[0.02, 0.97, 0.01], overflow=False) for _ in spans
            ]

    runtime = f.Runtime(Classifier())
    runtime.register.add("Always sort ascending.", "order", "Cedar", "sort", 0, 0)
    runtime.task = "Cedar"
    trace = runtime.update("Cancel the sorting rule for task Cedar.", 1)
    assert trace["applied"][0]["label"] == "cancels"
    assert len(trace["admissions"]) == 1
    assert trace["admissions"][0]["probabilities"][1] == 0.97
    assert not trace["admissions"][0]["accepted"]


def gold_records():
    bank = g.build_bank(v3.author_fixture(), setup_seed=30311, gate_seed=30312)
    g.validate_bank(bank)
    records = []
    for ep in bank["setup"]:
        oracle = f.Oracle()
        for ti, turn in enumerate(ep["turns"]):
            gold = oracle.update(turn["text"], ti, turn["events"])
            trace = dict(gold, overflow=False)
            records.append(
                dict(
                    episode=ep["id"],
                    turn_index=ti,
                    trace=trace,
                    event_checks=v3.event_checks(turn, ti, trace, gold),
                )
            )
    return bank, records


def test_bank_and_eligibility_require_all_gold_events():
    bank, records = gold_records()
    assert {e["seed"] for e in bank["setup"]} == {30311}
    assert {e["seed"] for e in bank["gate"]} == {30312}
    assert len({e["template"] for e in bank["gate"]}) == 64
    result = v3.eligibility_summary(records)
    assert result["eligible"]
    assert result["counts"] == {
        "initial_order": {"passed": 16, "total": 16},
        "standing": {"passed": 40, "total": 40},
        "retirements": {"passed": 8, "total": 8},
    }
    assert not v3.eligibility_summary(records[:-1])["eligible"]
    for label in ("admit", "supersedes", "cancels", "completes"):
        bad = copy.deepcopy(records)
        next(c for r in bad for c in r["event_checks"] if c["label"] == label)[
            "passed"
        ] = False
        assert not v3.eligibility_summary(bad)["eligible"]


def test_retirement_requires_existing_correct_target_and_status():
    text = "Task Cedar is complete. Switch to task Maple."
    turn = dict(
        text=text,
        events=[dict(label="completes", target="0:0", span="Task Cedar is complete.")],
    )
    row = dict(
        id="0:0",
        text="Always sort ascending.",
        scope="Cedar",
        kind="sort",
        version=1,
        status="completed",
    )
    gold = dict(after=[row])
    trace = dict(after=[dict(row, status="live")], applied=turn["events"])
    assert not v3.event_checks(turn, 2, trace, gold)[0]["passed"]
    trace["after"] = []
    assert not v3.event_checks(turn, 2, trace, gold)[0]["passed"]
    trace["after"] = [row]
    assert v3.event_checks(turn, 2, trace, gold)[0]["passed"]
    trace["applied"] = [dict(label="completes", target="wrong")]
    assert not v3.event_checks(turn, 2, trace, gold)[0]["passed"]


def test_run_refuses_gpu_before_ineligible_admission(tmp_path, monkeypatch):
    monkeypatch.setattr(v3, "OUT", tmp_path)
    monkeypatch.setattr(v3, "verify_freeze", lambda: None)
    (tmp_path / "setup-admission").mkdir()
    (tmp_path / "setup-admission/summary.json").write_text(
        json.dumps(dict(eligible=False))
    )

    def forbidden():
        pytest.fail("GPU claim reached after admission failure")

    monkeypatch.setattr(g, "claim_gpu", forbidden)
    with pytest.raises(AssertionError, match="INELIGIBLE-ADMISSION"):
        v3.run()
    assert not (tmp_path / "started.json").exists()
