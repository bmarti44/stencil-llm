# ruff: noqa: E501
"""PRESS-PLAN P0 statistics helpers.

The registered risk budget replaces zero-false-press (PRESS-PLAN Frozen
rules): calibration bounds come from exact zero-event binomial upper
bounds, and the press decision threshold from the measured false-press
cost C rather than an assumed infinite one.
"""
import math


def zero_event_upper_bound(n: int, alpha: float = 0.05) -> float:
    """Exact one-sided upper confidence bound on the event rate after
    observing 0 events in n independent trials: 1 - alpha^(1/n).
    (The 'rule of three' 3/n is its large-n approximation at alpha=0.05.)"""
    if n <= 0:
        raise ValueError("n must be positive")
    return 1.0 - alpha ** (1.0 / n)


def bayes_press_threshold(B: float, H: float) -> float:
    """Press when P(press needed) exceeds this threshold: p* = H/(B+H).

    B: measured per-press benefit and H: measured per-press expected harm,
    BOTH from T0.3's paired single-intervention rollouts on the same unit
    and horizon (v2 review: policy-level aggregates like the oracle's
    +14.5 lift or 7/409 parse-loss are not valid inputs — no defaults)."""
    if B <= 0 or H < 0:
        raise ValueError("B must be > 0 and H >= 0")
    return H / (B + H)


def clopper_pearson_upper(k: int, n: int, alpha: float = 0.05) -> float:
    """Exact one-sided (1-alpha) upper confidence bound on a binomial
    rate after k events in n trials: the largest p with
    P(X <= k; n, p) > alpha, found by bisection on the binomial CDF."""
    if not 0 <= k <= n or n <= 0:
        raise ValueError("need 0 <= k <= n, n > 0")
    if k == n:
        return 1.0

    def binom_cdf_le_k(p: float) -> float:
        # sum_{i<=k} C(n,i) p^i (1-p)^(n-i), computed in log space
        total = 0.0
        for i in range(k + 1):
            total += math.exp(
                math.lgamma(n + 1) - math.lgamma(i + 1) - math.lgamma(n - i + 1)
                + i * math.log(p) + (n - i) * math.log1p(-p)
            ) if 0.0 < p < 1.0 else (1.0 if (p == 0.0 and i == 0) else 0.0)
        return total

    lo, hi = 0.0, 1.0 - 1e-15
    for _ in range(200):
        mid = (lo + hi) / 2
        if binom_cdf_le_k(mid) > alpha:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def roc_point(scored: list[tuple[float, bool]], threshold: float) -> tuple[float, float]:
    """(tpr, fpr) for the policy 'press iff score > threshold' over
    (score, is_positive) pairs. An empty class yields rate 0.0 — callers
    asserting on these must check class counts (vacuity fails loudly at
    the call site, not here)."""
    pos = [s for s, y in scored if y]
    neg = [s for s, y in scored if not y]
    tpr = sum(1 for s in pos if s > threshold) / len(pos) if pos else 0.0
    fpr = sum(1 for s in neg if s > threshold) / len(neg) if neg else 0.0
    return tpr, fpr
