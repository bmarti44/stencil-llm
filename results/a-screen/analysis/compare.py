"""Cross-arm contract-state comparison, validated by the REGISTERED consumer.

Rewritten 2026-09-13 (second time) after Astra mutated the real baseline and got
this file's own `validate()` to return clean on seven invalid comparisons:

  * a session removed from BOTH arms and from both declared session lists
    (completeness was checked against each file's own declaration, not the
    frozen manifest);
  * `hub_sha256` removed from BOTH arms (the identity loop compared the UNION of
    supplied keys, so a field absent on both sides was never compared -- the
    same `None == None` defect I had just fixed in preflight.py and left here);
  * every `repo_after` hash corrupted (only `repo_before` was verified);
  * all suite scores deleted (`.get()` then `bool()` turned each missing score
    into a silent False, and all 36 preservation outcomes became failures);
  * `pilot_adapter=true`, a timing-only adapter, accepted as an arm;
  * a trained arm with `adapter_steps` absent compared against one with 134,
    because "trained" was selected by truthiness;
  * an arbitrary runner hash admitted by ANY non-empty --runner-exception string.

The remedy Astra named is the one taken here: **one trustworthy comparison path,
not a third validation framework.**  `scripts/a_screen_summary.py` is the
registered consumer and already enforces every one of the above -- it binds each
record to the frozen manifest, refuses a pilot adapter, requires the identity's
session list to BE the manifest, requires each shared identity field to be
PRESENT rather than merely equal, and recomputes J and function_only from the
individual suites, refusing when a stored aggregate disagrees.  This file now
delegates per-file validation to it and adds only what it does not do:

  1. the repository replay, checking `repo_before` AND `repo_after`;
  2. the cross-arm identity comparison with the runner exception BOUND to the
     exact inspected hash pair rather than to any non-empty string;
  3. `adapter_steps` presence for every arm carrying an adapter, and equality
     across arms that do;
  4. the contract-state classification (in-force / alt / both / neither /
     output-failure) that the registered summary does not compute.

Reported outcomes, each with the exact McNemar p on discordant pairs and the
registered conservative paired interval (separate 97.5% Clopper-Pearson bounds
on b/N and c/N combined by the union bound):

    contract IN FORCE            the convention question on its own
    IN FORCE *and* functional    narrow: the new suite only
    followed the SUPERSEDED rule the error this work exists to remove
    function_only                recomputed from functional+regression+protected
    all six suites at request 2  the registered success measure at this request

READ THE SCREEN'S LIMITATION FIRST (results/a-screen/RESULTS-BASELINE.md): the
48-session screen can be passed by "obey the most recent rule statement and copy
the existing code", so a difference reported here is a difference in following
the latest instruction, not evidence of instruction retention.

The unchanged-convention population is printed beside the changed one as a
DESCRIPTIVE control, with no causal reading: 12 sessions cannot resolve a
difference of differences, and the populations differ in project, lifecycle and
request text as well as in whether the convention changed.
"""

import argparse
import json
import os
import sys
from collections import Counter
from itertools import combinations
from math import comb
from pathlib import Path

from scipy.stats import beta

ROOT = "/home/bmarti44/stencil-llm"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, f"{ROOT}/src")
sys.path.insert(0, f"{ROOT}/scripts")
from a_screen_summary import SHARED_IDENTITY  # noqa: E402
from a_screen_summary import load as registered_load  # noqa: E402
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

RUNNER_FIELD = "runner_sha256"
# The ONLY runner difference this file will admit, and only with the flag.  Astra:
# "an arbitrary runner hash with any nonempty exception string" was accepted.  The
# exception is a statement about ONE inspected pair, established by
# analysis/runner_equivalence.py and recorded in RUNNER-EXCEPTION.md; it is not a
# licence to compare across runner versions in general.
RUNNER_EXCEPTION_PAIR = frozenset({"4acdb8f044c25a48", "f27bc5bc0690a918"})
MANIFEST = f"{ROOT}/results/a-screen/manifest.json"


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


def expected_sessions():
    """The frozen manifest, not any run file's own claim about itself."""
    return sorted(r["session"] for r in json.load(open(MANIFEST))["sessions"])


def load_arm(path, arm, expected, problems):
    """Per-file validation, delegated in full to the registered consumer.

    a_screen_summary.load() raises SystemExit on the first defect; this converts
    that into a problem entry so every arm is reported rather than only the first.
    Nothing is re-implemented here -- that duplication is what produced the seven
    escapes Astra found.
    """
    try:
        return registered_load(Path(path), arm, set(expected))
    except SystemExit as e:
        problems.append(f"{path}: {e}")
    except Exception as e:  # a malformed file the registered loader did not expect
        problems.append(f"{path}: {type(e).__name__}: {e}")
    return {}


def verify_replay(recs, problems, path):
    """The repository chain, which the registered consumer does not check.

    Both hashes: `repo_before` is what the runner handed the request and
    `repo_after` is what it recorded keeping.  Astra corrupted every `repo_after`
    and this file reported a clean comparison.
    """
    for sid, rec in recs.items():
        try:
            session = load(sid)
        except Exception as e:
            problems.append(f"{path}: {sid} is not a pool session ({type(e).__name__})")
            continue
        rr = {q["request"]: q for q in rec["requests"]}
        files = dict(session.files)
        for k in sorted(rr):
            q = rr[k]
            if q.get("repo_before") != repo_hash(files):
                problems.append(f"{path}: {sid} request {k} repo_before disagrees")
            nxt = None
            if q["terminal_reason"] == "applied":
                nxt, _ = A.apply_reply(files, session.requests[k - 1], q["output"])
            files = nxt if nxt is not None else files  # the runner retains on failure
            if q.get("repo_after") != repo_hash(files):
                problems.append(f"{path}: {sid} request {k} repo_after disagrees")


def check_identity(idents, runner_exception, problems):
    """Cross-arm identity: presence first, then equality, with the runner
    exception bound to the ONE inspected hash pair."""
    for arm, ident in idents.items():
        absent = [k for k in SHARED_IDENTITY if k not in ident]
        if absent:
            problems.append(f"{arm}: identity is missing {absent}")
    for x, y in combinations(sorted(idents), 2):
        ix, iy = idents[x], idents[y]
        for f in SHARED_IDENTITY:
            if f not in ix or f not in iy:
                continue  # already reported as absent; never silently equal
            if ix[f] == iy[f]:
                continue
            if f == RUNNER_FIELD:
                pair = frozenset({ix[f], iy[f]})
                if not runner_exception:
                    problems.append(
                        f"{x} and {y} differ on identity.{f} and no "
                        f"--runner-exception was given"
                    )
                elif pair != RUNNER_EXCEPTION_PAIR:
                    problems.append(
                        f"{x}/{y} differ on identity.{f} ({sorted(pair)}); that is "
                        f"NOT the inspected pair {sorted(RUNNER_EXCEPTION_PAIR)} "
                        f"RUNNER-EXCEPTION.md establishes"
                    )
                else:
                    print(f"  runner exception in force for the inspected pair "
                          f"{sorted(pair)} -- {runner_exception}")
                continue
            problems.append(
                f"{x} and {y} differ on identity.{f}: {ix[f]!r} vs {iy[f]!r}"
            )


def check_adapters(idents, problems):
    """Every arm carrying an adapter must declare its step count, and arms that
    carry one must agree.  Astra compared a 120-step arm against one whose
    `adapter_steps` was absent, because 'trained' was selected by truthiness."""
    steps = {}
    for arm, ident in idents.items():
        adapter = ident.get("adapter", "none")
        if adapter in (None, "", "none"):
            continue
        if ident.get("adapter_steps") in (None, 0):
            problems.append(
                f"{arm}: carries adapter {adapter!r} but declares "
                f"adapter_steps={ident.get('adapter_steps')!r}"
            )
            continue
        steps[arm] = ident["adapter_steps"]
    if len(set(steps.values())) > 1:
        problems.append(f"trained arms are not step-matched: {steps}")


def score_arm(recs):
    """Contract-state categories plus the outcomes the registered consumer
    RECOMPUTED from individual suites (never the stored aggregate flags)."""
    changed, unchanged = {}, {}
    for sid, rec in recs.items():
        s = load(sid)
        rr = {q["request"]: q for q in rec["requests"]}
        entering = replay(s, rr)
        cat = classify(s, rr[2], entering.get(2))
        sc = rr[2]["scores"]
        row = {
            "cat": cat,
            "functional": bool(sc["functional"]),
            "function_only": bool(rec["function_only"]),
            "j": bool(rec["J"]),
        }
        (changed if alt_was_in_force(s, 2) else unchanged)[sid] = row
    return changed, unchanged


def validate(paths, runner_exception):
    problems, arms, data, idents = [], [], {}, {}
    expected = expected_sessions()
    for p in paths:
        try:
            arm = json.loads(open(p).readline())["arm"]
        except Exception as e:
            problems.append(f"{p}: unreadable first record ({e})")
            continue
        if arm in data:
            problems.append(
                f"arm label {arm!r} appears in two files; labels must be unique")
            continue
        recs = load_arm(p, arm, expected, problems)
        if not recs:
            continue
        missing = set(expected) - set(recs)
        if missing:
            problems.append(
                f"{p}: INCOMPLETE, {len(missing)} of {len(expected)} manifest "
                f"sessions absent (e.g. {sorted(missing)[:3]})"
            )
        verify_replay(recs, problems, p)
        arms.append(arm)
        data[arm] = (p, recs)
        idents[arm] = recs[next(iter(recs))]["identity"]
    if len(arms) < 2:
        problems.append("at least two arms are required")
        return arms, data, idents, problems
    check_identity(idents, runner_exception, problems)
    check_adapters(idents, problems)
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
