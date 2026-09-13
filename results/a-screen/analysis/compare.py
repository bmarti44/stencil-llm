"""Cross-arm comparison on the primary population, paired by session id.

Validation comes before any statistic.  Astra's back-on-track review (2026-09-13)
found three high defects in the first version, all of them "it would have
computed a number anyway":

  * nothing required the arms to share the frozen 48-session set, so two runs
    over different sessions would have been paired on whatever they happened to
    have in common and the denominator would have shrunk silently;
  * nothing required distinct arm labels or unique (session, request) records,
    so a file compared with itself, or a run appended twice, would have printed
    a tidy zero-difference table;
  * nothing checked the run identity or the replay, so arms built from
    different pools, prompt budgets or scoring code would have been compared
    as if they differed only in the adapter.

So `validate()` refuses to report unless: each file's records are unique and
complete over its own declared session set; the declared session sets are
identical; and every identity field that is not the adapter is identical across
arms.  `runner_sha256` is the one field that may differ, and only with
--runner-exception plus the recorded reason, because the baseline `off` run was
produced on the pre-fix runner whose only difference lies inside `if a.adapter`
-- a branch an adapterless run never enters (see RUNNER-EXCEPTION.md).

Reported outcomes (Astra 7: a correctly-named but useless implementation passes
the contract measure, and J erases a contract improvement on one unrelated
competence failure, so neither alone is the answer):

    contract IN FORCE            the convention question on its own
    IN FORCE *and* functional    the reply a user would actually accept
    followed the SUPERSEDED rule the error this work exists to remove
    function_only                the runner's own functional-suite flag
    J (all six suites)           the screen's registered success measure

Each gets the exact McNemar p on the discordant pairs and the conservative
paired interval the program registered: separate 97.5% Clopper-Pearson bounds
on b/N and c/N combined by the union bound.

The unchanged-convention population is printed beside the changed one as a
DESCRIPTIVE control.  No causal reading is attached to the gap: with 12
unchanged sessions the difference of two differences has no useful precision,
and the two populations differ in project, request text and lifecycle as well
as in whether the convention changed.
"""

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from itertools import combinations
from math import comb

from scipy.stats import beta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, "/home/bmarti44/stencil-llm/src")
from stale2 import (  # noqa: E402
    CATS,
    alt_was_in_force,
    classify,
    replay,
    repo_hash,
    self_check,
)

from stencil import a_screen as A  # noqa: E402
from stencil.a_screen_pool import load  # noqa: E402

# identity fields that MUST agree across arms; the adapter fields are what vary
ADAPTER_FIELDS = {
    "adapter", "adapter_sha256", "adapter_steps", "adapter_config_sha256",
    "pilot_adapter",
}
RUNNER_FIELD = "runner_sha256"


def mcnemar_exact(b: int, c: int) -> float:
    """Two-sided exact binomial on the discordant pairs (p = 0.5)."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(comb(n, i) for i in range(0, k + 1)) / (2.0**n)
    return min(1.0, 2.0 * tail)


def clopper_pearson(k, n, conf=0.975):
    """Two-sided `conf` interval on k/n (so two of these union-bound to 95%)."""
    if n == 0:
        return (0.0, 1.0)
    a = (1 - conf) / 2
    lo = 0.0 if k == 0 else beta.ppf(a, k, n - k + 1)
    hi = 1.0 if k == n else beta.ppf(1 - a, k + 1, n - k)
    return (float(lo), float(hi))


def paired_interval(b, c, n):
    """Registered conservative interval on the paired difference (b - c)/n."""
    blo, bhi = clopper_pearson(b, n)
    clo, chi = clopper_pearson(c, n)
    return (blo - chi, bhi - clo)


def load_arm(path, problems):
    """Records for one arm, with every within-file check."""
    recs, ident, arm = {}, None, None
    for i, line in enumerate(open(path), 1):
        try:
            d = json.loads(line)
        except json.JSONDecodeError as e:
            problems.append(f"{path}:{i}: unparsable ({e})")
            continue
        key = (d["session"], d["request"])
        if key in recs:
            problems.append(f"{path}: duplicate record for {key[0]} request {key[1]}")
        recs[key] = d
        if arm is None:
            arm = d["arm"]
        elif d["arm"] != arm:
            problems.append(f"{path}: mixes arms {arm!r} and {d['arm']!r}")
        if ident is None:
            ident = d["identity"]
        elif d["identity"] != ident:
            problems.append(f"{path}:{i}: identity differs from the first record")
    if ident is None:
        problems.append(f"{path}: no records")
        return None, {}, {}
    want = {(s, k) for s in ident["sessions"] for k in (1, 2)}
    missing = want - set(recs)
    if missing:
        problems.append(
            f"{path}: INCOMPLETE, {len(missing)} of {len(want)} records missing "
            f"(e.g. {sorted(missing)[:3]})"
        )
    extra = set(recs) - want
    if extra:
        problems.append(
            f"{path}: {len(extra)} records outside the declared session set")
    return arm, recs, ident


def by_session(recs):
    by = defaultdict(dict)
    for (sid, k), d in recs.items():
        by[sid][k] = d
    return by


def verify_replay(recs, problems, path):
    """Cheap check -- no test execution -- that each record's repo_before is the
    repository the runner would have handed that request.  Runs inside validate()
    so a broken chain is refused before any pytest subprocess starts."""
    for sid, rr in by_session(recs).items():
        try:
            session = load(sid)
        except Exception as e:  # a session id the frozen pool does not contain
            problems.append(f"{path}: {sid} is not a pool session ({type(e).__name__})")
            continue
        entering = replay(session, rr)
        for k, rec in rr.items():
            if rec.get("repo_before") != repo_hash(entering.get(k, {})):
                problems.append(
                    f"{path}: {sid} request {k} replay disagrees with the record")


def score_arm(recs):
    """Categories, functional and J per session.  Runs the contract suites, so it
    is only called once validate() has passed."""
    changed, unchanged = {}, {}
    for sid, rr in by_session(recs).items():
        s = load(sid)
        entering = replay(s, rr)
        if 2 not in rr:
            continue
        cat = classify(s, rr[2], entering.get(2))
        sc = rr[2]["scores"]
        row = {
            "cat": cat,
            "functional": bool(sc.get("functional")),
            "function_only": bool(sc.get("function_only")),
            "j": all(sc.get(x) for x in A.SUITES),
        }
        (changed if alt_was_in_force(s, 2) else unchanged)[sid] = row
    return changed, unchanged


def validate(paths, runner_exception):
    problems, arms, data, idents = [], [], {}, {}
    for p in paths:
        arm, recs, ident = load_arm(p, problems)
        if arm is None:
            continue
        if arm in data:
            problems.append(
                f"arm label {arm!r} appears in two files; labels must be unique")
        verify_replay(recs, problems, p)
        arms.append(arm)
        data[arm] = (p, recs)
        idents[arm] = ident
    if len(arms) < 2:
        problems.append("at least two arms are required")
    for x, y in combinations(arms, 2):
        ix, iy = idents[x], idents[y]
        if ix["sessions"] != iy["sessions"]:
            problems.append(f"{x} and {y} declare different session sets")
        for f in sorted(set(ix) | set(iy)):
            if f in ADAPTER_FIELDS or f == "sessions":
                continue
            if ix.get(f) != iy.get(f):
                if f == RUNNER_FIELD and runner_exception:
                    print(f"  runner exception in force: {x} {ix.get(f)} vs "
                          f"{y} {iy.get(f)} -- {runner_exception}")
                    continue
                problems.append(f"{x} and {y} differ on identity.{f}: "
                                f"{ix.get(f)!r} vs {iy.get(f)!r}")
    trained = [a for a in arms if idents[a].get("adapter_steps")]
    if len(trained) > 1:
        steps = {a: idents[a]["adapter_steps"] for a in trained}
        if len(set(steps.values())) > 1:
            problems.append(f"trained arms are not step-matched: {steps}")
    return arms, data, idents, problems


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--runner-exception", default="",
                    help="reason a runner_sha256 difference is admissible")
    ap.add_argument("--allow-problems", action="store_true",
                    help="print the table anyway, with every problem restated")
    a = ap.parse_args(argv)

    print("validating before comparing")
    arms, data, idents, problems = validate(a.paths, a.runner_exception)
    if problems:
        print("\n  REFUSING TO COMPARE -- fix these first:")
        for p in problems:
            print(f"    * {p}")
        if not a.allow_problems:
            return 1
        print("\n  --allow-problems given; every number below is suspect")
    else:
        print("  identity, completeness, uniqueness and replay all verified")
    self_check()  # a measure that cannot pass is not evidence of failure
    scored, ctrl = {}, {}
    for arm in arms:
        scored[arm], ctrl[arm] = score_arm(data[arm][1])

    shared = sorted(set.intersection(*(set(scored[x]) for x in arms)))
    print(f"\npaired on {len(shared)} sessions whose convention CHANGED "
          f"(arms: {', '.join(arms)})")

    print("\n  category counts, fixed denominator")
    print(f"    {'arm':6} " + "  ".join(f"{c:>14}" for c in CATS))
    for x in arms:
        row = Counter(scored[x][s]["cat"] for s in shared)
        print(f"    {x:6} " + "  ".join(f"{row[c]:>14}" for c in CATS))

    outcomes = {
        "contract IN FORCE": lambda r: r["cat"] == "in-force",
        "IN FORCE *and* functional":
            lambda r: r["cat"] == "in-force" and r["functional"],
        "followed the SUPERSEDED convention": lambda r: r["cat"] == "alt",
        "function_only": lambda r: r["function_only"],
        "all six suites at request 2": lambda r: r["j"],
    }
    n = len(shared)
    for label, hit in outcomes.items():
        print(f"\n  '{label}'")
        for x in arms:
            print(f"    {x:6} {sum(hit(scored[x][s]) for s in shared):3d}/{n}")
        for x, y in combinations(arms, 2):
            b = sum(1 for s in shared if hit(scored[y][s]) and not hit(scored[x][s]))
            c = sum(1 for s in shared if hit(scored[x][s]) and not hit(scored[y][s]))
            lo, hi = paired_interval(b, c, n)
            print(f"      {y} vs {x}: {y}-only {b}, {x}-only {c}   net {b - c:+d}   "
                  f"exact McNemar p={mcnemar_exact(b, c):.4f}   "
                  f"95% paired interval [{100 * lo:+.1f}, {100 * hi:+.1f}] pts")

    cshared = sorted(set.intersection(*(set(ctrl[x]) for x in arms)))
    if cshared:
        print("\n  DESCRIPTIVE control: the same outcome where the convention did NOT")
        print("  change.  Reported side by side only; the populations also differ in")
        print("  project, lifecycle and request text, and 12 sessions cannot resolve a")
        print("  difference of differences, so no causal reading is attached.")
        for x in arms:
            ch = sum(1 for s in shared if scored[x][s]["cat"] == "in-force")
            un = sum(1 for s in cshared if ctrl[x][s]["cat"] == "in-force")
            print(f"    {x:6} changed {ch}/{len(shared)}   "
                  f"unchanged {un}/{len(cshared)}")

    print("\n  every session whose category moved")
    for x, y in combinations(arms, 2):
        for s in shared:
            if scored[x][s]["cat"] != scored[y][s]["cat"]:
                print(f"    {s}: {x}={scored[x][s]['cat']:10} -> "
                      f"{y}={scored[y][s]['cat']:10} "
                      f"(functional {scored[x][s]['functional']} -> "
                      f"{scored[y][s]['functional']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
