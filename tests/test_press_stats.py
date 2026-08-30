# ruff: noqa: E501
"""PRESS-PLAN P0 statistics helpers — written red-first (TDD).

Hand-computed expectations:
- rule of three: 0 events in n trials -> 95% one-sided upper bound ~ 3/n.
  Exact form: 1 - alpha^(1/n) with alpha=0.05. n=18 -> 1-0.05^(1/18)
  = 1 - exp(ln(0.05)/18) = 1 - exp(-0.16643) = 0.15329...
  n=300 -> 1 - 0.05^(1/300) = 0.009935...
- Bayes press threshold: press iff p*14.5 > (1-p)*0.017*C
  -> p* = 0.017C / (14.5 + 0.017C). C=100 -> 1.7/16.2 = 0.104938...
  C=500 -> 8.5/23.0 = 0.369565...
- roc_point: presses=[(score,is_positive)...], threshold t: press iff
  score > t. tpr = pressed positives / positives, fpr = pressed
  negatives / negatives.
"""
import math

from stencil.press_stats import bayes_press_threshold, roc_point, zero_event_upper_bound


def test_zero_event_upper_bound_exact():
    assert math.isclose(zero_event_upper_bound(18), 1 - 0.05 ** (1 / 18), rel_tol=1e-12)
    assert math.isclose(zero_event_upper_bound(18), 0.153318, abs_tol=5e-6)
    assert math.isclose(zero_event_upper_bound(300), 0.0099361, abs_tol=5e-7)
    # ~1% at 300 negatives, the plan's claim
    assert zero_event_upper_bound(300) < 0.01


def test_zero_event_upper_bound_alpha():
    # rule-of-three approximation holds at alpha=0.05 for large n
    assert math.isclose(zero_event_upper_bound(1000), 3 / 1000, rel_tol=0.01)
    # tighter alpha -> larger bound
    assert zero_event_upper_bound(100, alpha=0.01) > zero_event_upper_bound(100, alpha=0.05)


def test_bayes_press_threshold():
    # v2: B and H are REQUIRED measured per-press quantities (sol review:
    # the old defaults mixed policy aggregates with per-press estimands).
    assert math.isclose(bayes_press_threshold(B=14.5, H=1.7), 1.7 / 16.2, rel_tol=1e-12)
    assert math.isclose(bayes_press_threshold(B=14.5, H=8.5), 8.5 / 23.0, rel_tol=1e-12)
    # degenerate zero-false-press assumption: H -> inf drives p* -> 1
    assert bayes_press_threshold(B=14.5, H=1e12) > 0.999
    # no defaults exist
    import pytest
    with pytest.raises(TypeError):
        bayes_press_threshold(14.5)  # missing H


def test_clopper_pearson_upper():
    # values pinned in PRESS-PLAN.md Frozen rules (verified numerically)
    from stencil.press_stats import clopper_pearson_upper
    assert math.isclose(clopper_pearson_upper(0, 160), 0.0185, abs_tol=5e-4)
    assert math.isclose(clopper_pearson_upper(3, 160), 0.0477, abs_tol=5e-4)
    assert math.isclose(clopper_pearson_upper(4, 160), 0.0563, abs_tol=5e-4)
    # k=0 case must agree with the closed form 1 - alpha^(1/n)
    assert math.isclose(clopper_pearson_upper(0, 18), zero_event_upper_bound(18), rel_tol=1e-6)
    assert math.isclose(clopper_pearson_upper(0, 300), zero_event_upper_bound(300), rel_tol=1e-6)
    # monotone in k
    assert clopper_pearson_upper(2, 160) < clopper_pearson_upper(3, 160)


def test_roc_point():
    scored = [(0.9, True), (0.8, False), (0.7, True), (0.1, False)]
    tpr, fpr = roc_point(scored, threshold=0.75)
    assert tpr == 0.5 and fpr == 0.5
    tpr, fpr = roc_point(scored, threshold=0.95)
    assert tpr == 0.0 and fpr == 0.0
    tpr, fpr = roc_point(scored, threshold=0.0)
    assert tpr == 1.0 and fpr == 1.0


def test_roc_point_empty_classes():
    # no negatives -> fpr defined as 0.0, not a crash (vacuity must be loud elsewhere)
    tpr, fpr = roc_point([(0.5, True)], threshold=0.4)
    assert tpr == 1.0 and fpr == 0.0
