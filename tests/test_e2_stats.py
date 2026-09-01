"""Registered E2 audit and paired-inference arithmetic."""

import pytest


def test_exact_mcnemar_one_sided_hand_values():
    from stencil.e2_stats import mcnemar_one_sided

    assert mcnemar_one_sided(7, 0) == pytest.approx(1 / 128)
    assert mcnemar_one_sided(0, 7) == 1.0
    assert mcnemar_one_sided(5, 5) == pytest.approx(0.623046875)


def test_periodic_assignment_is_stable_and_rate_bounded():
    from stencil.e2_stats import periodic_assignment

    a = [periodic_assignment(f"k{i}", 2, rate=0.25, onset=17) for i in range(1000)]
    b = [periodic_assignment(f"k{i}", 2, rate=0.25, onset=17) for i in range(1000)]
    assert a == b
    fired = [x for x in a if x is not None]
    assert 200 <= len(fired) <= 300
    assert set(fired) == {17}


def test_audit_ranges_pass_and_fail_nonvacuously():
    from stencil.e2_stats import audit_reasons, summarize_policy_audit

    records = []
    # 20 rows per turn, 30% fire. Trigger origins cover aged and fresh.
    for turn in (2, 3):
        for i in range(20):
            fired = i < 6
            records.append(
                {
                    "turn": turn,
                    "fired": fired,
                    "onset_count": int(fired),
                    "selected_origin": (1 + i % turn) if fired else None,
                    "silent_identical": not fired,
                }
            )
    summary = summarize_policy_audit(records)
    assert not audit_reasons(summary)
    records[0]["onset_count"] = 2
    bad = audit_reasons(summarize_policy_audit(records))
    assert any("onset" in reason for reason in bad)


def test_cluster_bootstrap_is_fixed_seed_and_conversation_resampled():
    from stencil.e2_stats import cluster_bootstrap_delta

    rows = [
        {"conversation": 0, "base": [0, 0], "arm": [1, 1]},
        {"conversation": 1, "base": [1], "arm": [1]},
        {"conversation": 2, "base": [1, 1, 1], "arm": [0, 1, 1]},
    ]
    a = cluster_bootstrap_delta(rows, draws=500, seed=0)
    b = cluster_bootstrap_delta(rows, draws=500, seed=0)
    assert a == b
    assert a["point_delta"] == pytest.approx((2 - 1) / 6)
    assert a["clusters"] == 3


def test_safe_dose_gate_rejects_knife_edge_or_excess_harm():
    from stencil.e2_stats import safe_dose_reasons

    good = {
        str(dose): {
            "net_utility": 3,
            "harm_p_one_sided": 0.5,
            "arm_truncations": 1,
            "native_truncations": 1,
            "arm_timeouts": 0,
            "native_timeouts": 0,
            "decision_hash": "same",
        }
        for dose in (2.25, 3.0, 3.75)
    }
    assert not safe_dose_reasons(good)
    bad = {key: dict(value) for key, value in good.items()}
    bad["3.75"]["net_utility"] = 0
    bad["3.75"]["decision_hash"] = "changed"
    reasons = safe_dose_reasons(bad)
    assert any("3.75" in reason for reason in reasons)
    assert any("decisions" in reason for reason in reasons)
