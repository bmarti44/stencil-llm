"""Deterministic E2 hazard-fit and held-out inference contracts."""

import math

import pytest


def _record(i, x, label, utility, topic=None, family=None):
    return {
        "session": i,
        "topic": topic or f"topic-{i % 3}",
        "changed_family": family or [f"family-{i % 4}"],
        "features": [x, 0, 0, 0, 0, 0],
        "response_position": (i % 5) / 4,
        "label": label,
        "utility_delta": utility,
    }


def test_wilson_lower_bound_hand_cases():
    from stencil.e2_gate import wilson_lower

    assert wilson_lower(0, 0) == 0.0
    assert wilson_lower(0, 10) == 0.0
    assert wilson_lower(10, 10) == pytest.approx(0.7224672, rel=1e-6)
    assert wilson_lower(50, 100) < 0.5


def test_generic_logistic_fit_is_deterministic_and_nonvacuous():
    from stencil.e2_gate import LogisticProbe

    X = [[-2], [-1], [1], [2]]
    y = [0, 0, 1, 1]
    a = LogisticProbe.fit(X, y, iters=300)
    b = LogisticProbe.fit(X, y, iters=300)
    assert a == b
    assert a.probability([-1]) < a.probability([1])
    assert math.isfinite(a.bias) and any(abs(x) > 0 for x in a.weights)


def test_threshold_selection_uses_utility_and_is_deterministic():
    from stencil.e2_gate import select_threshold

    probabilities = [0.9, 0.8, 0.4, 0.1]
    labels = [1, 1, 0, 0]
    utility = [1, 1, -1, 0]
    a = select_threshold(probabilities, labels, utility)
    b = select_threshold(probabilities, labels, utility)
    assert a == b
    assert a >= 0.8
    fired = [p >= a for p in probabilities]
    assert fired == [True, True, False, False]


def test_grouped_cv_never_trains_on_held_out_group_and_repeats():
    from stencil.e2_gate import cross_validate

    records = []
    for i in range(60):
        positive = i % 2 == 0
        records.append(_record(i, 2 if positive else -2,
                               "helpful" if positive else "harmful",
                               1 if positive else -1))
    a = cross_validate(records, "session", "full")
    b = cross_validate(records, "session", "full")
    assert a == b
    assert len(a["probabilities"]) == len(records)
    assert all(f["train_groups_disjoint"] for f in a["folds"])
    assert a["metrics"]["ppv"] == 1.0
    assert a["metrics"]["recall"] == 1.0


def test_matched_rate_controls_fire_exactly_full_gate_count():
    from stencil.e2_gate import evaluate_discrimination

    records = []
    for i in range(120):
        positive = i % 3 == 0
        records.append(_record(i, 3 if positive else -1,
                               "helpful" if positive else "neutral",
                               1 if positive else 0))
    got = evaluate_discrimination(records)
    for scheme in ("session", "topic", "family"):
        full_n = got["schemes"][scheme]["full"]["metrics"]["n_fired"]
        for name, control in got["schemes"][scheme]["controls"].items():
            assert control["metrics"]["n_fired"] == full_n, (scheme, name)


def test_certification_fails_closed_on_real_label_counts():
    from stencil.e2_gate import certification_reasons

    reasons = certification_reasons(
        {"helpful": 100, "harmful": 99, "neutral": 500},
        {"schemes": {}},
    )
    assert any("harmful" in reason for reason in reasons)
