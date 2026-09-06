"""Final-iteration lifecycle guards through the actual runtime consumer."""

import pytest

from stencil import focus3 as f
from tests.test_focus3_gate_v5 import Classifier


def runtime(label, prule=0.99):
    clf = Classifier(label=label, prule=prule)
    clf.key_identity = True
    clf.strict_lifecycle = True
    clf.admission_bound = "positive_proposal"
    rt = f.Runtime(clf)
    rt.task = "Cedar"
    return rt


@pytest.mark.parametrize("status", ["cancelled", "completed", "superseded", "live"])
def test_reinstate_requires_cancelled_or_completed_same_key(status):
    rt = runtime("reinstates")
    old = rt.register.add("Always sort ascending.", "order", "Cedar", "sort", 0, 0)
    old.status = status
    trace = rt.update("Restore the ascending sorting requirement for task Cedar.", 1)
    expected = status in ("cancelled", "completed")
    assert bool(trace["applied"]) is expected
    assert len(rt.register.rows) == 1 + expected
    if expected:
        assert trace["applied"][0]["label"] == "reinstates"
        assert rt.register.rows[-1].status == "live"
        assert rt.key_slugs[rt.register.rows[-1].id] == "sort-order"


def test_generic_admitted_span_cannot_borrow_retired_key():
    rt = runtime("reinstates")
    old = rt.register.add("Always sort ascending.", "order", "Cedar", "sort", 0, 0)
    old.status = "cancelled"
    trace = rt.update("Reply with the word peaceful.", 1)
    assert trace["pairs"][0]["proposed"] == "reinstates"
    assert trace["admissions"][0]["probabilities"][1] >= 0.95
    assert not trace["applied"]  # Rejected proposal still bounds new admission.
    assert old.status == "cancelled" and len(rt.register.rows) == 1


@pytest.mark.parametrize("prule", [0.01, 0.949999, 0.95])
def test_old_text_does_not_bypass_admission(prule):
    rt = runtime("reinstates", prule)
    old = rt.register.add("Always sort ascending.", "order", "Cedar", "sort", 0, 0)
    old.status = "completed"
    trace = rt.update("Restore: Always sort ascending.", 1)
    assert bool(trace["applied"]) is (prule >= 0.95)


def test_admission_overflow_blocks_reinstatement():
    rt = runtime("reinstates")
    original = rt.classifier.admission
    rt.classifier.admission = lambda spans, previous: [
        dict(row, overflow=True) for row in original(spans, previous)
    ]
    old = rt.register.add("Always sort ascending.", "order", "Cedar", "sort", 0, 0)
    old.status = "cancelled"
    trace = rt.update("Restore: Always sort ascending.", 1)
    assert trace["overflow"] and not trace["applied"]


@pytest.mark.parametrize(
    "text",
    [
        "Cancel the sorting requirement for task Cedar.",
        "Revoke the sorting requirement for task Cedar.",
        "Stop following the sorting requirement for task Cedar.",
        "Do not restore the sorting requirement for task Cedar.",
        "Cancel the other requirement. Restore the sorting requirement for task Cedar.",
    ],
)
def test_cancellation_message_cannot_reinstate(text):
    rt = runtime("reinstates")
    old = rt.register.add("Always sort ascending.", "order", "Cedar", "sort", 0, 0)
    old.status = "cancelled"
    trace = rt.update(text, 1)
    assert not any(a["label"] == "reinstates" for a in trace["applied"])
    assert old.status == "cancelled"


def test_cancels_proposal_elsewhere_in_message_vetoes_reinstatement():
    rt = runtime("reinstates")
    old = rt.register.add("Always sort ascending.", "order", "Cedar", "sort", 0, 0)
    old.status = "cancelled"
    other = rt.register.add("Keep tag equal to 8.", "tag", "*", "sort", 0, 20)
    original = rt.classifier.relations

    def relations(pairs):
        predictions = original(pairs)
        for pair, pred in zip(pairs, predictions, strict=True):
            if pair["target_id"] == other.id:
                pred["probabilities"] = [0.001, 0.001, 0.996, 0.001, 0.001]
        return predictions

    rt.classifier.relations = relations
    trace = rt.update("Restore the sorting requirement for task Cedar.", 1)
    assert any(p["proposed"] == "cancels" for p in trace["pairs"])
    assert not trace["applied"]


@pytest.mark.parametrize("multiple", [False, True])
def test_completion_filters_global_before_precedence(multiple):
    rt = runtime("completes", 0.01)
    global_row = rt.register.add("Always sort carefully.", "g", "*", "sort", 0, 0)
    task_row = rt.register.add("Always sort ascending.", "o", "Cedar", "sort", 0, 20)
    sibling = rt.register.add("Always sort descending.", "s", "Maple", "sort", 0, 40)
    rows = [task_row]
    if multiple:
        rows.append(
            rt.register.add("Keep tag equal to 8.", "t", "Cedar", "sort", 0, 60)
        )
    trace = rt.update("Task Cedar is finished.", 1)
    assert global_row.status == sibling.status == "live"
    assert all(r.status == "completed" for r in rows)
    assert {a["target"] for a in trace["applied"]} == {r.id for r in rows}
    assert any(p["input"]["target_id"] == global_row.id for p in trace["pairs"])
    assert not any(p["input"]["target_id"] == sibling.id for p in trace["pairs"])


def test_global_completion_scope_cannot_retire_task_rows():
    rt = runtime("completes", 0.01)
    old = rt.register.add("Always sort ascending.", "o", "Cedar", "sort", 0, 0)
    trace = rt.update("All tasks in this conversation are finished.", 1)
    assert not trace["applied"] and old.status == "live"


def test_global_only_completion_never_retires_global():
    rt = runtime("completes", 0.01)
    old = rt.register.add("Keep tag equal to 8.", "t", "*", "sort", 0, 0)
    trace = rt.update("Task Cedar is finished.", 1)
    assert not trace["applied"] and old.status == "live"


def test_v8_classifier_constructor_enables_only_registered_policy(monkeypatch):
    from scripts import focus3_gate_v8 as v8

    calls = []
    monkeypatch.setattr(f, "FrozenClassifier", lambda *args: calls.append(args))
    v8.classifier("C")
    args = calls.pop()
    assert args[0] == v8.v6.MODELS / "seed0"
    assert args[1] == dict(
        supersedes=0.90, cancels=0.50, completes=0.50, reinstates=0.50
    )
    assert args[2:] == ("positive_proposal", v8.a.MODELS / "seed0", True, True)


def test_v8_stop_prevents_gpu_claim(tmp_path, monkeypatch):
    from scripts import focus3_gate_v8 as v8

    (tmp_path / "summary.json").write_text('{"eligible": false}')
    monkeypatch.setattr(v8, "OUT", tmp_path)
    monkeypatch.setattr(v8, "verify_freeze", lambda: None)
    # Register existing bindings for restoration after the adapter changes them.
    for obj, name in [
        (v8.v6, "OUT"),
        (v8.v6, "verify_freeze"),
        (v8.v6, "classifier"),
        (v8.g, "claim_gpu"),
    ]:
        monkeypatch.setattr(obj, name, getattr(obj, name))
    monkeypatch.setattr(v8, "claim_gpu", lambda: pytest.fail("GPU claim after stop"))
    with pytest.raises(AssertionError, match="INELIGIBLE"):
        v8.run()
