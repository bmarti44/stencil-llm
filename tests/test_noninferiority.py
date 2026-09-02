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


def test_cluster_bootstrap_is_seeded_and_sign_aware():
    from stencil.stats import cluster_bootstrap_upper_bound
    diffs = [0.0, 10.0, 0.0, 5.0, 20.0]
    assert 7.0 < cluster_bootstrap_upper_bound(diffs) <= 20.0  # a bootstrap quantile lies within the resampled means
    assert cluster_bootstrap_upper_bound(diffs) == cluster_bootstrap_upper_bound(diffs)  # seeded
    assert cluster_bootstrap_upper_bound([-x for x in diffs]) < 0.0  # sign carried through


# ---------------------------------------------------- sol round 2 (HIGH): boundary false-pass
# results/ledger-reverify-sol.md finding 2: 909 independent clusters, pure degradation exactly
# at the 2-point margin (each conversation's single eligible constraint is harmed with
# probability 0.02, a 100-point per-conversation difference; otherwise 0).  The number of
# harmed clusters is Binomial(909, 0.02) and every candidate bound is a deterministic
# function of it (binary data), so the boundary false-pass probability is EXACT: the
# binomial mass of the harmed counts the bound lets through.
K_SOL, P_SOL, MARGIN_SOL = 909, 0.02, 2.0


def _binom_pmf(n, p):
    from math import comb
    return [comb(n, h) * p ** h * (1 - p) ** (n - h) for h in range(n + 1)]


def _harmed(h, k=K_SOL):
    return [100.0] * h + [0.0] * (k - h)


def _exact_false_pass(passes):
    pmf = _binom_pmf(K_SOL, P_SOL)
    return sum(pmf[h] for h in range(K_SOL + 1) if passes(h))


def test_sol_reproduction_uncorrected_t_bound_false_pass_is_8_31_percent():
    """the BEFORE number: the plain t bound declares NI with 0-12 harmed clusters (sol: 8.31%)."""
    from stencil.stats import clustered_upper_bound
    pass_set = [h for h in range(40) if clustered_upper_bound(_harmed(h)) < MARGIN_SOL]
    assert pass_set == list(range(13))
    rate = _exact_false_pass(lambda h: h <= 12)
    assert abs(rate - 0.0831) < 5e-4, rate
    assert clustered_upper_bound([0.0] * K_SOL) == 0.0  # sol: zero-width bound on all-zero data


def test_candidate_a_percentile_cluster_bootstrap_is_rejected_by_simulation():
    """candidate (a), 4000 resamples: on binary cluster data the resampled mean is
    100/k * Binomial(k, h/k), so the percentile upper bound is its 0.95 quantile —
    the SAME pass set (0-12 harmed) and the same 8.31% (registered implementation,
    seed 0, Monte Carlo 60 trials: 5/60 = 0.083).  Not registered."""
    from math import comb

    def binom_quantile(n, q, prob):
        c = 0.0
        for x in range(n + 1):
            c += comb(n, x) * prob ** x * (1 - prob) ** (n - x)
            if c >= q:
                return x
        return n
    def passes(h):
        return h == 0 or 100.0 / K_SOL * binom_quantile(K_SOL, 0.95, h / K_SOL) < MARGIN_SOL
    assert [h for h in range(40) if passes(h)] == list(range(13))
    rate = _exact_false_pass(passes)
    assert rate > 0.05 and abs(rate - 0.0831) < 5e-4, rate


def test_registered_continuity_corrected_t_bound_false_pass_le_5_percent():
    """candidate (b), REGISTERED: t bound + one whole-cluster flip (100/k points).  Pass set
    0-11 harmed; exact boundary false-pass 4.90% <= 5%.  A half-flip (50/k) leaves 8.31%."""
    from stencil.stats import (
        CONTINUITY_POINTS,
        clustered_bound,
        clustered_upper_bound,
        clustered_upper_bound_corrected,
    )
    assert CONTINUITY_POINTS == 100.0
    pass_set = [h for h in range(40) if clustered_upper_bound_corrected(_harmed(h)) < MARGIN_SOL]
    assert pass_set == list(range(12))
    rate = _exact_false_pass(lambda h: h <= 11)
    assert rate <= 0.05 and abs(rate - 0.0490) < 5e-4, rate
    half = [h for h in range(40) if clustered_upper_bound(_harmed(h)) + 50.0 / K_SOL < MARGIN_SOL]
    assert half == list(range(13))
    # all-zero data: strictly positive width (one flip), never a zero-width bound
    assert clustered_upper_bound_corrected([0.0] * K_SOL) == 100.0 / K_SOL > 0.0
    # the registered dispatch applies the corrected bound ALWAYS (no cluster-count switch)
    for diffs in (_harmed(5), [0.0, 10.0, 0.0, 5.0, 20.0], list(range(1, 11))):
        b = clustered_bound(diffs)
        assert b["method"] == "t_continuity" and b["upper_bound"] == clustered_upper_bound_corrected(diffs)
        assert b["continuity_points"] == 100.0 / len(diffs)
        assert abs(b["t_upper_bound_descriptive"] - clustered_upper_bound(diffs)) < 1e-12
    assert abs(clustered_bound(list(range(1, 11)))["t_upper_bound_descriptive"] - 7.255073) < 1e-5
    assert clustered_bound([1.0])["upper_bound"] is None and clustered_bound([1.0])["error"]


def test_corrected_bound_false_pass_under_mixed_discordance_by_simulation():
    """secondary check at the registered size: drop exactly at the margin with two-sided
    discordance (p10 = 0.03, p01 = 0.01) — the corrected bound stays <= 5% + MC error."""
    import random

    from stencil.stats import clustered_upper_bound_corrected
    rng = random.Random(0)
    trials, fp = 400, 0
    for _ in range(trials):
        d = []
        for _ in range(K_SOL):
            r = rng.random()
            d.append(100.0 if r < 0.03 else (-100.0 if r < 0.04 else 0.0))
        fp += clustered_upper_bound_corrected(d) < MARGIN_SOL
    assert fp / trials <= 0.07, fp / trials  # 400 trials: MC se ~1.1 points


# ---------------------------------------------- ROUND 4 (results/ledger-reverify4-sol.md): clustered LOWER bound
def test_clustered_lower_bound_hand_computed_and_sign_relation():
    """the one-sided 95% LOWER bound uses the SAME registered continuity-corrected
    clustered machinery, sign-flipped: -clustered_bound(-diffs)["upper_bound"].
    Hand case 1..10: mean 5.5, sd 3.0276504, t_{0.95,9} = 1.8331129, half-width
    1.7550730 -> t lower 3.7449270, minus one whole-cluster flip 100/10 -> -6.2550730."""
    from stencil.stats import clustered_bound, clustered_lower_bound

    diffs = list(range(1, 11))
    lb = clustered_lower_bound(diffs)
    assert lb["method"] == "t_continuity" and lb["clusters"] == 10 and lb["alpha"] == 0.05
    assert abs(lb["mean"] - 5.5) < 1e-12
    assert abs(lb["t_lower_bound_descriptive"] - 3.744927) < 1e-5
    assert abs(lb["lower_bound"] - (-6.255073)) < 1e-5
    assert lb["continuity_points"] == 10.0
    # exact sign relation against the registered upper bound, on several shapes
    for d in (diffs, [0.0] * 20, [100.0] * 5 + [0.0] * 4, [-3.0, 2.5, 0.0, 7.0], [1e-3] * 3):
        assert clustered_lower_bound(d)["lower_bound"] == -clustered_bound([-x for x in d])["upper_bound"]
        assert clustered_lower_bound(d)["lower_bound"] < clustered_bound(d)["upper_bound"]
    # zero between-cluster variance: the flip alone sets the width
    assert clustered_lower_bound([100.0] * 25)["lower_bound"] == 100.0 - 4.0
    # fewer than two clusters fails closed like the upper bound
    one = clustered_lower_bound([5.0])
    assert one["lower_bound"] is None and one["error"]
