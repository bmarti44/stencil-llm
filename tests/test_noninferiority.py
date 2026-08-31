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
