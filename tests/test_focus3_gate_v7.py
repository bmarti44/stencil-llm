"""CPU consumer checks of semantic key precedence and admission lineage."""

import pytest

from scripts import finetune_admission_v2 as a
from stencil import focus3 as f
from tests.test_focus3_gate_v5 import Classifier


@pytest.mark.parametrize("label", ["supersedes", "cancels", "completes", "reinstates"])
def test_cross_key_positive_dropped_and_new_rule_admitted(label):
    clf = Classifier(label=label)
    clf.key_identity = True
    clf.admission_bound = "positive_proposal"
    rt = f.Runtime(clf)
    old = rt.register.add("Keep tag equal to 7.", "tag", "*", "sort", 0, 0)
    if label == "reinstates":
        old.status = "cancelled"
    status = old.status
    trace = rt.update("Always sort ascending for task Cedar.", 1)
    assert trace["cross_key_proposals"] == 1
    assert trace["pairs"][0]["proposed"] == label
    assert trace["pairs"][0]["applied"] == "none"
    assert trace["admissions"][0]["accepted"]
    assert old.status == status
    assert rt.key_slugs[rt.register.rows[-1].id] == "sort-order"
    assert trace["applied"] == [
        dict(label="admit", span="Always sort ascending for task Cedar.")
    ]


def test_same_key_positive_still_vetoes_before_status():
    clf = Classifier(label="supersedes")
    clf.key_identity = True
    clf.admission_bound = "positive_proposal"
    rt = f.Runtime(clf)
    old = rt.register.add("Always sort descending.", "sort-order", "*", "sort", 0, 0)
    old.status = "cancelled"
    trace = rt.update("Always sort ascending for task Cedar.", 1)
    assert trace["cross_key_proposals"] == 0
    assert not trace["applied"] and not trace["admissions"][0]["accepted"]


def test_anaphoric_completion_inherits_target_key():
    clf = Classifier(label="completes")
    clf.key_identity = True
    rt = f.Runtime(clf)
    old = rt.register.add("Keep tag equal to 7.", "tag", "Cedar", "sort", 0, 0)
    trace = rt.update("Task Cedar is finished.", 1)
    assert old.status == "completed"
    assert trace["pairs"][0]["proposal_key"] == "tag"


def test_sentence_identity_split_groups_roles_labels_and_context():
    rows = [dict(text=f"Example {i}.", role="user", label="none") for i in range(50)]
    rows += [dict(rows[0], role="tool", label="fact", context="different")]
    for seed in range(3):
        fit, dev = a.split(rows, seed)
        assert fit and dev
        assert not (
            {a.identity(r["text"]) for r in fit} & {a.identity(r["text"]) for r in dev}
        )


def test_semantic_identity_preserves_cross_task_version_numbers():
    clf = Classifier(label="none")
    clf.key_identity = True
    clf.admission_bound = "positive_proposal"
    rt = f.Runtime(clf)
    rt.update("Always sort ascending for task Cedar.", 0)
    rt.update("Always sort descending for task Maple.", 1)
    assert len(rt.register.rows) == 2
    assert [r.version for r in rt.register.rows] == [1, 1]
    assert [r.key for r in rt.register.rows] == ["new:0:0", "new:1:0"]
    assert set(rt.key_slugs.values()) == {"sort-order"}
