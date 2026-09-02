# ruff: noqa: E501
"""Registered paired non-inferiority machinery (BENCH-WAVE v2.2 Tango
bound; restored after checkpoint-ii FINDING-1 killed the invalid
Clopper-Pearson plug-in construction — coverage 0.45-0.50 at the
margin, NaN at n01=0).

delta = p10 - p01 is the population accuracy DROP (n10 = base right /
wave wrong, n01 = converse). tango_upper_bound returns the one-sided
(1-alpha) NOMINAL (asymptotic score) upper confidence limit on delta
by inverting Tango's score test — near-nominal in practice (recomputed
exact type-I at the registered scenarios: 0.048 GSM8K boundary, 0.050
MMLU boundary), but not an exact finite-sample interval and disclosed
as such; the constrained MLE of p01 under each delta0 is found by
direct bounded maximization of the trinomial log-likelihood (no
closed-form sign-convention risk). Fail-closed: any non-convergence
raises. NON-INFERIOR iff tango_upper_bound(...) < margin (STRICT,
as registered in v2.2)."""
import math

Z95 = 1.6448536269514722  # one-sided 95%


def _constrained_loglik(n10, n01, n, delta0):
    """max over p01 of the trinomial log-likelihood with p10 = p01 + delta0.
    Returns (loglik, p01_hat). Golden-section on the concave 1-D problem."""
    lo = max(0.0, -delta0) + 1e-12
    hi = (1.0 - delta0) / 2.0 - 1e-12
    if hi <= lo:
        raise ValueError(f"empty feasible set for delta0={delta0}")

    def ll(p01):
        p10 = p01 + delta0
        rest = 1.0 - p10 - p01
        if p10 <= 0 or p01 <= 0 or rest <= 0:
            return -math.inf
        return (n10 * math.log(p10) + n01 * math.log(p01)
                + (n - n10 - n01) * math.log(rest))

    # golden-section maximize (concave in p01 on the feasible interval)
    invphi = (math.sqrt(5.0) - 1.0) / 2.0
    a, b = lo, hi
    c, d = b - invphi * (b - a), a + invphi * (b - a)
    fc, fd = ll(c), ll(d)
    for _ in range(200):
        if fc >= fd:
            b, d, fd = d, c, fc
            c = b - invphi * (b - a)
            fc = ll(c)
        else:
            a, c, fc = c, d, fd
            d = a + invphi * (b - a)
            fd = ll(d)
    p01_hat = (a + b) / 2.0
    return ll(p01_hat), p01_hat


def tango_z(n10, n01, n, delta0):
    """Tango score statistic for H0: delta = delta0 (decreasing in delta0)."""
    _, p01_hat = _constrained_loglik(n10, n01, n, delta0)
    var = n * (2.0 * p01_hat + delta0 * (1.0 - delta0))
    if var <= 0:
        raise ValueError(f"nonpositive score variance at delta0={delta0}")
    return (n10 - n01 - n * delta0) / math.sqrt(var)


def tango_upper_bound(n10, n01, n, alpha=0.05):
    """one-sided (1-alpha) upper confidence limit on delta = p10 - p01.

    Solves tango_z(delta_U) = -z_{1-alpha} by bisection. Handles the
    degenerate all-concordant case (n10 = n01 = 0) exactly like any
    other: the bound is strictly positive but shrinks as 1/n."""
    if not (0 <= n10 and 0 <= n01 and n10 + n01 <= n and n > 0):
        raise ValueError("bad table")
    z_target = -Z95 if alpha == 0.05 else -_z_of(1 - alpha)
    lo = (n10 - n01) / n          # z(lo) ~ >= 0
    hi = 1.0 - 1e-9               # z -> -inf as delta0 -> 1
    if tango_z(n10, n01, n, max(lo, -1 + 1e-9) + 1e-12) < z_target:
        raise ValueError("score statistic below target at point estimate")
    f_lo = None
    a, b = max(lo, -1.0 + 1e-9) + 1e-12, hi
    for _ in range(500):
        mid = (a + b) / 2.0
        if tango_z(n10, n01, n, mid) > z_target:
            a = mid
        else:
            b = mid
        if b - a < 1e-10:
            return (a + b) / 2.0
    raise RuntimeError("tango_upper_bound failed to converge")  # fail-closed


def _z_of(p):
    """inverse standard normal CDF via Acklam's rational approximation
    (deterministic, dependency-free; |err| < 1.15e-9)."""
    if not 0 < p < 1:
        raise ValueError
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00,
         3.754408661907416e+00]
    plow, phigh = 0.02425, 1 - 0.02425
    if p < plow:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    if p > phigh:
        q = math.sqrt(-2 * math.log(1 - p))
        return -(((((c[0]*q+c[1])*q+c[2])*q+c[3])*q+c[4])*q+c[5]) / ((((d[0]*q+d[1])*q+d[2])*q+d[3])*q+1)
    q = p - 0.5
    r = q * q
    return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*q / (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)


def non_inferior(n10, n01, n, margin, alpha=0.05):
    """the registered do-no-harm gate: STRICT upper-bound < margin."""
    return tango_upper_bound(n10, n01, n, alpha) < margin


def mcnemar_exact_one_sided(n_improve, n_degrade):
    """one-sided exact McNemar: P(X >= n_improve | n = discordants, p = 1/2).
    Registered superiority test (v2/v4.5)."""
    n = n_improve + n_degrade
    if n == 0:
        return 1.0
    from math import comb
    return sum(comb(n, k) for k in range(n_improve, n + 1)) / (2 ** n)


# ------------------------------------------------------------ clustered NI
# LEDGER-PLAN amendment (2026-09-01, after results/ledger-verify-sol.md):
# paired per-constraint outcomes inside one conversation are correlated and
# cumulative constraints are scored again on later turns, so Tango on the
# pooled cells is descriptive only.  The registered primary bound is a
# CONVERSATION-clustered one-sided (1-alpha) upper bound on the mean of the
# per-conversation mean paired differences (points, reference - candidate,
# positive = a DROP), via Student t on the cluster means; a percentile
# cluster bootstrap (2000 resamples, seed 0) is the fallback below ten
# clusters, where the t approximation is least trustworthy.

def _betacf(a, b, x):
    """continued fraction for the regularized incomplete beta (NR 6.4)."""
    MAXIT, EPS, FPMIN = 500, 3e-16, 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    d = 1.0 / (d if abs(d) >= FPMIN else FPMIN)
    h = d
    for m in range(1, MAXIT + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) >= FPMIN else FPMIN)
        c = 1.0 + aa / c
        c = c if abs(c) >= FPMIN else FPMIN
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) >= FPMIN else FPMIN)
        c = 1.0 + aa / c
        c = c if abs(c) >= FPMIN else FPMIN
        de = d * c
        h *= de
        if abs(de - 1.0) < EPS:
            return h
    raise RuntimeError("incomplete beta continued fraction did not converge")


def _betainc(a, b, x):
    """regularized incomplete beta I_x(a, b)."""
    if not 0.0 <= x <= 1.0:
        raise ValueError("x outside [0, 1]")
    if x == 0.0 or x == 1.0:
        return x
    front = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
                     + a * math.log(x) + b * math.log(1.0 - x))
    if x < (a + 1.0) / (a + b + 2.0):
        return front * _betacf(a, b, x) / a
    return 1.0 - front * _betacf(b, a, 1.0 - x) / b


def t_cdf(t, df):
    """Student t CDF with df degrees of freedom (dependency-free)."""
    if df <= 0:
        raise ValueError("df must be positive")
    x = df / (df + t * t)
    tail = 0.5 * _betainc(df / 2.0, 0.5, x)
    return 1.0 - tail if t >= 0 else tail


def t_quantile(p, df):
    """inverse Student t CDF by bisection on t_cdf (|err| < 1e-9)."""
    if not 0.0 < p < 1.0:
        raise ValueError("p outside (0, 1)")
    lo, hi = -1e6, 1e6
    for _ in range(300):
        mid = (lo + hi) / 2.0
        if t_cdf(mid, df) < p:
            lo = mid
        else:
            hi = mid
        if hi - lo < 1e-10:
            break
    return (lo + hi) / 2.0


def _mean(xs):
    return sum(xs) / len(xs)


def clustered_upper_bound(per_cluster_mean_diffs, alpha=0.05):
    """one-sided (1-alpha) upper bound on the mean of the per-cluster mean
    paired differences via Student t: mean + t_{1-alpha, k-1} * sd / sqrt(k).
    Needs >= 2 clusters; zero between-cluster variance returns the mean."""
    diffs = [float(x) for x in per_cluster_mean_diffs]
    k = len(diffs)
    if k < 2:
        raise ValueError("clustered bound needs at least two clusters")
    m = _mean(diffs)
    var = sum((x - m) ** 2 for x in diffs) / (k - 1)
    if var == 0.0:
        return m
    return m + t_quantile(1.0 - alpha, k - 1) * math.sqrt(var / k)


def cluster_bootstrap_upper_bound(per_cluster_mean_diffs, alpha=0.05, n_resamples=2000, seed=0):
    """percentile cluster bootstrap: resample clusters with replacement,
    take the (1-alpha) quantile of the resampled means (deterministic seed)."""
    import random

    diffs = [float(x) for x in per_cluster_mean_diffs]
    k = len(diffs)
    if k < 2:
        raise ValueError("clustered bound needs at least two clusters")
    rng = random.Random(seed)
    means = sorted(_mean([diffs[rng.randrange(k)] for _ in range(k)]) for _ in range(n_resamples))
    idx = min(n_resamples - 1, max(0, math.ceil((1.0 - alpha) * n_resamples) - 1))
    return means[idx]


def clustered_bound(per_cluster_mean_diffs, alpha=0.05, min_clusters_for_t=10):
    """registered dispatch: t bound at >= min_clusters_for_t clusters, cluster
    bootstrap (2000 resamples, seed 0) below; returns the audit fields."""
    diffs = [float(x) for x in per_cluster_mean_diffs]
    k = len(diffs)
    out = {"clusters": k, "alpha": alpha, "mean": (_mean(diffs) if k else None)}
    if k < 2:
        return {**out, "method": None, "upper_bound": None, "error": "fewer than two clusters"}
    if k >= min_clusters_for_t:
        return {**out, "method": "t", "upper_bound": clustered_upper_bound(diffs, alpha)}
    return {**out, "method": "cluster_bootstrap", "resamples": 2000, "seed": 0,
            "upper_bound": cluster_bootstrap_upper_bound(diffs, alpha, 2000, 0)}
