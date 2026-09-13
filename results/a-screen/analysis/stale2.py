"""Convention-in-force scoring.  Rebuilt twice: once after Astra's review of
stale.py, once after Astra's review of THIS file found its headline label false.

Correction 8 (2026-09-13, back-on-track review).  The previous version labelled
request 1 "no supersession yet" for every session.  That is FALSE for the 12
REINSTATEMENT sessions, whose authored prefix already contains a supersession:
rule turn 10 states states[0], rule turn 12 replaces it with states[1] (=
state_at[0], in force at request 1), and the event between the requests
reinstates states[0].  So at request 1 of a reinstatement session the
alternative state WAS in force and WAS explicitly superseded, and a reply that
follows it is a genuine stale-convention error.  All four request-1 "stale"
replies in the off arm (S12, S20, S36, S44) are reinstatement sessions, so the
old headline -- "stale replies appear even before anything is superseded" --
had no support at all.

The population key is now DERIVED, never assumed: for request k, was the
alternative state (`session.other(state_at[k-1])`) in force earlier in this
same session?

    k = 1:  true iff the prefix contains a supersession, i.e. three rule turns
            (equivalent to lifecycle == "reinstatement" on all 624 pool
            sessions; asserted here, tested in tests/).
    k = 2:  true iff state_at[0] != state_at[1], i.e. the event changed the
            convention; the alternative at request 2 IS state_at[0], which was
            in force at request 1.

The four cells that follow are the ones reported.  The word STALE is used only
where that flag is true; where it is false the same category is the alternative
state, which was never in force, and calling it stale would repeat the defect
this correction fixes.

Earlier corrections, kept:

 3a HIGH  The conditional rate in-force/(in-force+stale) is NOT a cross-arm
          comparison.  Astra's counterexample: (current, stale, neither) =
          (40,40,20) -> (40,10,50) lifts it from 50% to 80% without one extra
          current-rule success.  Denominators are FIXED per cell and every
          category is reported against them.
 3b MED   A reply can satisfy BOTH contract suites (S34: return None for an
          unknown id when the account holds tokens, raise KeyError otherwise --
          both suites use different setups and both pass).  BOTH is its own
          unresolved bucket, never "states agree".
 3c HIGH  Replay must follow the runner: apply ONLY records whose
          terminal_reason is "applied", and on a failed apply RETAIN the
          preceding repository rather than abandoning the session
          (a_screen_run.py:575).  Every reconstruction is checked against the
          repo_before hashes the runner recorded.
 7  MED   Contract compliance and functional success are reported ALONGSIDE
          each other, neither conditional on the other: 11 of the first 24
          in-force replies failed the functional suite, so "followed the
          convention" does not mean "wrote working code".

Writes results/a-screen/analysis/out/<arm>-states.json: one record per
(session, request) with the raw category, the population key, family,
lifecycle, direction and functional score, so a cross-arm comparison never has
to recompute the labels or trust this summary.
"""

import json
import os
import sys
from collections import Counter, defaultdict

from scipy.stats import fisher_exact

sys.path.insert(0, "/home/bmarti44/stencil-llm/src")
from stencil import a_screen as A  # noqa: E402
from stencil.a_screen_pool import load  # noqa: E402

CATS = ("in-force", "alt", "both", "neither", "output-failure")
OUT = "/home/bmarti44/stencil-llm/results/a-screen/analysis/out"


def repo_hash(files):
    """The runner's own hash (a_screen_run.py:68-73), so replay can be checked."""
    import hashlib

    return hashlib.sha256(
        json.dumps(files, sort_keys=True).encode()
    ).hexdigest()[:16]


def alt_was_in_force(session, k):
    """Was the alternative state at request k in force earlier in this session?

    The equivalence asserted here is checked over all 624 pool sessions by
    tests/test_a_screen_supersession.py; it is the whole basis of the labels.
    """
    three = len(session.rule_turns) == 3
    assert three == (session.lifecycle == "reinstatement"), session.id
    if k == 1:
        return three
    return session.state_at[0] != session.state_at[1]


def population(session, k):
    return (k, alt_was_in_force(session, k))


POP_NAME = {
    (1, False): "req1  alternative NEVER in force  (stable/replacement/scope)",
    (1, True): "req1  alternative SUPERSEDED in the prefix  (reinstatement)",
    (2, False): "req2  convention unchanged  (stable)",
    (2, True): "req2  convention CHANGED at the event  (repl/scope/reinst)",
}


def replay(session, recs):
    """The repository entering each request, exactly as the runner built it."""
    files = dict(session.files)
    entering = {1: files}
    for k in (1, 2):
        rec = recs.get(k)
        if rec is None:
            break
        nxt = None
        if rec["terminal_reason"] == "applied":
            nxt, _ = A.apply_reply(files, session.requests[k - 1], rec["output"])
        files = nxt if nxt is not None else files  # runner retains on failure
        entering[k + 1] = files
    return entering


def classify(session, rec, base):
    """in-force / alt / both / neither / output-failure for one reply."""
    if rec["terminal_reason"] != "applied":
        return "output-failure"
    k = rec["request"]
    req = session.requests[k - 1]
    state = session.state_at[k - 1]
    files, _ = A.apply_reply(base, req, rec["output"])
    if files is None:
        return "output-failure"
    now, _ = A.run_tests(files, req.contract_tests[state], timeout=90.0)
    alt, _ = A.run_tests(files, req.contract_tests[session.other(state)], timeout=90.0)
    if now and alt:
        return "both"
    if now:
        return "in-force"
    if alt:
        return "alt"
    return "neither"


def self_check(sample=3):
    """The measure must be able to FAIL and to PASS before any verdict is trusted.

    Found the hard way on 2026-09-13.  `stencil.contracts.run_tests` shells out to
    `sys.executable -m pytest`; under a bare `python3` that has no pytest, every
    suite returns (False, "") and EVERY reply classifies as "neither" -- a clean,
    plausible, entirely empty table, with the contrast at p=1.000.  A measure that
    cannot pass is not evidence of failure, so this refuses to run rather than
    report.  Run the analysis under `uv run python`.

    Two levels: the instrument answers both ways at all, and gold satisfies its own
    contract suite on real sessions (a suite nothing can pass measures nothing).
    """
    passing = {"test_p.py": "def test_p():\n    assert True\n"}
    ok, msg = A.run_tests({"m.py": "x = 1"}, passing)
    if not ok:
        raise SystemExit(
            f"INSTRUMENT DEAD: a trivially passing suite returned {(ok, msg)!r}.\n"
            f"  interpreter: {sys.executable}\n"
            f"  pytest is not importable there -- run this under `uv run python`."
        )
    failing = {"test_f.py": "def test_f():\n    assert False\n"}
    bad, _ = A.run_tests({"m.py": "x = 1"}, failing)
    if bad:
        raise SystemExit("INSTRUMENT DEAD: a failing suite reported success.")
    from stencil.a_screen_pool import available_slots

    for sid in available_slots()[:sample]:
        s = load(sid)
        for k in (1, 2):
            req = s.requests[k - 1]
            state = s.state_at[k - 1]
            base = dict(s.files) if k == 1 else A.gold_files(s, k - 1)
            files = {**base, req.target: req.gold[state]}
            ok, msg = A.run_tests(files, req.contract_tests[state], timeout=90.0)
            if not ok:
                raise SystemExit(
                    f"INSTRUMENT DEAD: {sid} request {k} gold under the state in "
                    f"force ({state}) fails its own contract suite: {msg}"
                )
    print(f"  self-check: the contract measure passes and fails correctly, and gold "
          f"satisfies its own suite on {sample} sessions")


def wilson(k, n, z=1.959963984540054):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5)
    return ((c - h) / d, (c + h) / d)


def scan(path):
    """Per-(session, request) records for one arm's run file."""
    by = defaultdict(dict)
    arm = None
    for line in open(path):
        d = json.loads(line)
        arm = d["arm"]
        by[d["session"]][d["request"]] = d
    out, mismatch = [], 0
    for sid, recs in sorted(by.items()):
        s = load(sid)
        entering = replay(s, recs)
        for k in sorted(recs):
            rec = recs[k]
            base = entering.get(k)
            if base is None:
                continue
            if rec.get("repo_before") != repo_hash(base):
                mismatch += 1
            state = s.state_at[k - 1]
            out.append({
                "arm": arm,
                "session": sid,
                "request": k,
                "category": classify(s, rec, base),
                "alt_was_in_force": alt_was_in_force(s, k),
                "lifecycle": s.lifecycle,
                "family": s.target_family,
                "state_in_force": state,
                "alternative": s.other(state),
                "direction": f"{s.other(state)}->{state}"
                             if alt_was_in_force(s, k) else f"(only {state})",
                "functional": rec["scores"].get("functional"),
                "j": all(rec["scores"].get(x) for x in A.SUITES),
                "terminal_reason": rec["terminal_reason"],
            })
    return arm, out, mismatch, len(by)


def alt_label(flag):
    return "STALE (superseded)" if flag else "alt (never in force)"


def report(arm, recs, mismatch, nsess, path):
    print(f"\n===== {arm}   ({nsess} sessions, {path})")
    if mismatch:
        print(f"  !! {mismatch} reconstructed repositories disagree with the record")
    else:
        print("  replay verified against every recorded repo_before hash")

    pops = defaultdict(Counter)
    for r in recs:
        pops[(r["request"], r["alt_was_in_force"])][r["category"]] += 1
    for key in sorted(pops, key=lambda k: (k[0], k[1])):
        tally = pops[key]
        n = sum(tally.values())
        print(f"  --- {POP_NAME[key]}   (fixed denominator n={n})")
        for c in CATS:
            if tally[c]:
                name = alt_label(key[1]) if c == "alt" else c
                lo, hi = wilson(tally[c], n)
                print(f"        {name:20s} {tally[c]:3d}   {100 * tally[c] / n:5.1f}%"
                      f"   [95% {100 * lo:.0f}-{100 * hi:.0f}]")

    print("\n  --- contrasts on the alternative-state rate (Fisher exact, two-sided)")
    for k, lbl in ((2, "request 2: changed vs unchanged"),
                   (1, "request 1: superseded-in-prefix vs never-in-force")):
        a, b = pops[(k, True)], pops[(k, False)]
        na, nb = sum(a.values()), sum(b.values())
        if not (na and nb):
            continue
        table = [[a["alt"], na - a["alt"]], [b["alt"], nb - b["alt"]]]
        _, p = fisher_exact(table)
        print(f"      {lbl}: {a['alt']}/{na} vs {b['alt']}/{nb}   p={p:.3f}")

    print("\n  --- breakdowns where the alternative was superseded")
    for dim in ("family", "lifecycle", "direction"):
        cells = defaultdict(Counter)
        for r in recs:
            if r["alt_was_in_force"]:
                cells[r[dim]][r["category"]] += 1
        print(f"      by {dim}:")
        for v in sorted(cells):
            t = cells[v]
            n = sum(t.values())
            print(f"        {v:22s} n={n:3d}  " + "  ".join(
                f"{c}={t[c]}" for c in CATS if t[c]))

    print("\n  --- convention AND working code, neither conditional on the other")
    cross = defaultdict(Counter)
    for r in recs:
        cross[(r["request"], r["alt_was_in_force"])][
            f"{r['category']}|functional={r['functional']}"] += 1
    for key in sorted(cross, key=lambda k: (k[0], k[1])):
        print(f"      {POP_NAME[key]}:")
        print("        " + "  ".join(f"{k}={v}" for k, v in sorted(cross[key].items())))

    print("\n  --- per-session table")
    print(f"      {'sess':5s} {'req':3s} {'lifecycle':14s} {'family':14s} "
          f"{'direction':22s} {'category':15s} func J")
    for r in recs:
        print(f"      {r['session']:5s} {r['request']:<3d} {r['lifecycle']:14s} "
              f"{r['family']:14s} {r['direction']:22s} {r['category']:15s} "
              f"{str(r['functional']):5s} {'J' if r['j'] else '.'}")


def run(path):
    self_check()
    arm, recs, mismatch, nsess = scan(path)
    report(arm, recs, mismatch, nsess, path)
    os.makedirs(OUT, exist_ok=True)
    dest = f"{OUT}/{os.path.basename(path).rsplit('.jsonl', 1)[0]}-states.json"
    with open(dest, "w") as fh:
        json.dump({"arm": arm, "source": path, "sessions": nsess,
                   "replay_mismatches": mismatch, "records": recs}, fh, indent=1)
    print(f"\n  wrote {dest}")


if __name__ == "__main__":
    for p in sys.argv[1:]:
        run(p)
