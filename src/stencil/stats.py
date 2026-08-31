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
