# ruff: noqa: E501
"""Boundary + coverage tests for the restored Tango non-inferiority
bound (checkpoint-ii FINDING-1, both reviewers): the killed
Clopper-Pearson plug-in had type-I error ~0.50 at the margin and NaN
at n01=0; these tests pin the exact failure scenarios."""
import random

from stencil.stats import non_inferior, tango_upper_bound, tango_z


def test_perfect_agreement_passes():
    # the killed rule returned NaN here (fail-closed FAIL on a perfect run)
    u = tango_upper_bound(0, 0, 5330)
    assert 0.0 < u < 0.001
    assert non_inferior(0, 0, 5330, margin=0.005)


def test_all_harm_no_improvement():
    # (k, 0): the killed rule collapsed to the raw point estimate
    u = tango_upper_bound(13, 0, 1319)
    assert u > 13 / 1319  # a real bound sits strictly above the MLE
    assert not non_inferior(13, 0, 1319, margin=0.01)


def test_all_improvement_no_harm():
    u = tango_upper_bound(0, 13, 1319)
    assert u < 0.0
    assert non_inferior(0, 13, 1319, margin=0.01)


def test_monotone_in_evidence():
    assert tango_upper_bound(5, 5, 1000) < tango_upper_bound(10, 5, 1000)
    assert tango_upper_bound(10, 5, 10000) < tango_upper_bound(10, 5, 1000)


def test_z_decreasing_in_delta0():
    zs = [tango_z(10, 5, 1000, d) for d in (0.001, 0.01, 0.05, 0.1)]
    assert all(a > b for a, b in zip(zs, zs[1:]))


def _simulate_type1(n, p10, p01, margin, trials, seed):
    """true drop == margin: fraction of trials falsely declared non-inferior."""
    rng = random.Random(seed)
    false_pass = 0
    for _ in range(trials):
        n10 = n01 = 0
        for _ in range(n):
            r = rng.random()
            if r < p10:
                n10 += 1
            elif r < p10 + p01:
                n01 += 1
        if non_inferior(n10, n01, n, margin):
            false_pass += 1
    return false_pass / trials


def test_type1_error_at_margin_pure_degradation():
    # THE review counterexample: N=1319, p10=0.01, p01=0, margin 1pt.
    # Killed rule: 0.498-0.552 false-pass. Valid rule: <= ~0.05.
    rate = _simulate_type1(1319, 0.01, 0.0, 0.01, trials=400, seed=7)
    assert rate <= 0.08, f"type-I {rate} at the margin (pure degradation)"


def test_type1_error_at_margin_mixed():
    # balanced discordance, true drop exactly at margin
    rate = _simulate_type1(5330, 0.01, 0.005, 0.005, trials=300, seed=11)
    assert rate <= 0.08, f"type-I {rate} at the margin (mixed)"


def test_power_under_null_drop():
    # true drop 0, generous margin: should usually pass (sanity, not a gate)
    rate = _simulate_type1(5330, 0.005, 0.005, 0.005, trials=200, seed=13)
    assert rate >= 0.5


def test_type1_error_at_margin_pure_degradation_mmlu():
    # round-2 sol note: the PURE-degradation MMLU counterexample itself
    rate = _simulate_type1(5330, 0.005, 0.0, 0.005, trials=300, seed=17)
    assert rate <= 0.08, f"type-I {rate} at the MMLU margin (pure degradation)"


# ---------------------------------------------------------------- clustered
# LEDGER-PLAN amendment (2026-09-01): the primary bound is a conversation-
# clustered one-sided 95% upper bound on the mean paired difference (points).

def test_t_quantile_matches_tables():
    from stencil.stats import t_quantile
    assert abs(t_quantile(0.95, 9) - 1.8331129) < 1e-6
    assert abs(t_quantile(0.95, 1) - 6.3137515) < 1e-5
    assert abs(t_quantile(0.975, 30) - 2.0422725) < 1e-6
    assert abs(t_quantile(0.5, 4)) < 1e-7  # numerical noise at the median


def test_clustered_upper_bound_hand_computed():
    from stencil.stats import clustered_upper_bound
    diffs = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]  # mean 5.5, sd 3.02765, se 0.957427
    expect = 5.5 + 1.8331129 * 3.0276504 / 10 ** 0.5  # 7.255073
    assert abs(clustered_upper_bound(diffs) - expect) < 1e-5
    assert abs(clustered_upper_bound(diffs) - 7.255073) < 1e-5


def test_clustered_upper_bound_is_asymmetric_in_sign():
    """Catches a sign inversion: a drop must give a bound ABOVE the margin,
    an improvement a bound BELOW it, never symmetric."""
    from stencil.stats import clustered_upper_bound
    harm = [4.0, 5.0, 6.0, 4.0, 5.0, 6.0, 4.0, 5.0, 6.0, 5.0]        # neural worse (positive drop)
    gain = [-x for x in harm]
    assert clustered_upper_bound(harm) > 5.0 > 2.0
    assert clustered_upper_bound(gain) < -4.0 < 2.0
    assert clustered_upper_bound(harm) != -clustered_upper_bound(gain)
    tiny = [0.0] * 9 + [0.1]
    assert 0.0 < clustered_upper_bound(tiny) < 2.0


def test_clustered_upper_bound_needs_two_clusters_and_handles_zero_variance():
    import pytest

    from stencil.stats import clustered_upper_bound
    with pytest.raises(ValueError):
        clustered_upper_bound([1.0])
    assert clustered_upper_bound([3.0] * 12) == 3.0


def test_cluster_bootstrap_fallback_below_ten_clusters():
    from stencil.stats import cluster_bootstrap_upper_bound, clustered_bound
    diffs = [0.0, 10.0, 0.0, 5.0, 20.0]
    b = clustered_bound(diffs)
    assert b["method"] == "cluster_bootstrap" and b["clusters"] == 5 and b["resamples"] == 2000 and b["seed"] == 0
    assert b["upper_bound"] == cluster_bootstrap_upper_bound(diffs)
    assert 7.0 < b["upper_bound"] <= 20.0  # a bootstrap quantile lies within the resampled means
    assert cluster_bootstrap_upper_bound(diffs) == cluster_bootstrap_upper_bound(diffs)  # seeded
    assert cluster_bootstrap_upper_bound([-x for x in diffs]) < 0.0  # sign carried through
    t = clustered_bound(list(range(1, 11)))
    assert t["method"] == "t" and abs(t["upper_bound"] - 7.255073) < 1e-5
