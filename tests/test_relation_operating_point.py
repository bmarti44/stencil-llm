import numpy as np
import pytest

from stencil import relation_operating_point as op


def test_exact_fp_denominator_ties_and_consumer():
    probs = np.array(
        [[0.105, 0.895, 0, 0, 0]] * 13
        + [[0.96, 0.01, 0.01, 0.01, 0.01]] * 246
        + [[0.02, 0.95, 0.01, 0.01, 0.01]] * 30
    )
    # Use positive epsilon to form finite logits; tied false positives move together.
    logits = np.log(np.maximum(probs, 1e-20))
    labels = np.array([0] * 259 + [1] * 30)
    overflow = np.zeros(len(labels), dtype=bool)
    selected = op.select(logits, labels, overflow)
    assert selected["none_fp_allowance_per_class"] == 12
    assert selected["policy"]["thresholds"]["supersedes"] == 0.90
    assert selected["policy"]["thresholds"]["cancels"] == 1.01
    actual_probs, _, _ = op.inputs(logits, labels, overflow)
    predictions = op.predict(actual_probs, selected["policy"], overflow)
    assert np.array_equal(predictions, labels)
    assert selected["dev"]["per_class"]["supersedes"]["precision"] == 1


def test_margin_fallback_and_overflow_through_consumer():
    probs = np.array(
        [[0.8, 0.05, 0.05, 0.05, 0.05]] * 100 + [[0.15, 0.45, 0.15, 0.15, 0.1]] * 20
    )
    labels = np.array([0] * 100 + [1] * 20)
    overflow = np.zeros(120, dtype=bool)
    overflow[-1] = True
    selected = op.select(np.log(probs), labels, overflow)
    assert selected["policy"] == {"kind": "margin", "margin": 0.0}
    assert selected["qualified_on_dev"]
    assert selected["dev"]["correct_positive"] == 19
    assert selected["dev"]["correct_positive_recall"] == 0.95
    assert op.predict(probs, selected["policy"], overflow)[-1] == 0


def test_no_useful_policy_is_failure_not_vacuous_success():
    probs = np.tile([0.8, 0.05, 0.05, 0.05, 0.05], (20, 1))
    selected = op.select(
        np.log(probs), np.array([0] * 10 + [1] * 10), np.zeros(20, bool)
    )
    assert not selected["qualified_on_dev"]
    assert selected["policy"]["kind"] == "per_class"
    assert selected["dev"]["positive_precision"] is None
    assert selected["dev"]["correct_positive_recall"] == 0


def test_cutoff_equality_and_none_argmax_tie():
    probs = np.array([[0.5, 0.5, 0, 0, 0], [0.1, 0.5, 0.2, 0.1, 0.1]])
    policy = {"kind": "per_class", "thresholds": dict.fromkeys(op.LABELS[1:], 0.5)}
    assert op.predict(probs, policy, np.zeros(2, bool)).tolist() == [0, 1]


def test_invalid_and_missing_support_fail():
    for logits, labels in [
        (np.full((2, 5), np.nan), [0, 1]),
        (np.zeros((2, 5)), [0, 0]),
    ]:
        with pytest.raises(ValueError):
            op.select(logits, labels, np.zeros(2, bool))
