"""A name-level cross-check on the NAMING family.  Not a retention measure.

RETIRED INTERPRETATION (2026-09-13, Astra's back-on-track review).  This file
used to be headed "instruction retention, isolated from coding competence" and
claimed more power than the 48 binary J values.  Both claims are withdrawn, for
two demonstrated reasons:

  * it read the GOLD repository entering request 2 (`A.gold_files`), not the
    repository the arm's own request-1 reply produced.  The runner chains the
    arm's own edit, so for any arm whose first reply differs from gold the
    measure was scored against a repository that arm never saw;
  * it counted public function names in every family.  Checked over the frozen
    screen pool: in `missing_record` and `validation` the gold under the two
    states has IDENTICAL public method names in 32/32 requests -- the states
    differ in behaviour, not in naming.  So outside `naming` the classification
    was reading shared names and could only report "in-force".

What it does now, and all it does: on the 16 `naming` sessions, where the two
states genuinely differ by method name, report which convention's names the
reply introduced, against the arm's own entering repository.  That is a cheap
syntactic cross-check on stale2.py's executable verdict -- it should mostly
agree, and any disagreement is worth reading -- and nothing more.  The
executable contract-state measure in stale2.py is the evidence; this is a
second pair of eyes on one third of it.

    uv run python results/a-screen/analysis/names.py <run.jsonl>
"""

import ast
import json
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, "/home/bmarti44/stencil-llm/src")
from stale2 import alt_was_in_force, classify, replay  # noqa: E402

from stencil import a_screen as A  # noqa: E402
from stencil.a_screen_pool import load  # noqa: E402

FAMILY = "naming"


def pubs(src: str) -> set[str]:
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return set()
    out = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.ClassDef):
            for f in n.body:
                if isinstance(f, ast.FunctionDef) and not f.name.startswith("_"):
                    out.add(f.name)
        elif isinstance(n, ast.FunctionDef) and not n.name.startswith("_"):
            out.add(n.name)
    return out


def verdict(session, rec, base):
    """Which convention's NEW names the reply introduced, or neither."""
    k = rec["request"]
    req = session.requests[k - 1]
    state = session.state_at[k - 1]
    was = pubs(base.get(req.target, ""))
    want = pubs(req.gold[state]) - was
    stale = pubs(req.gold[session.other(state)]) - was
    if not (want or stale):
        return "vacuous"  # the states are not name-distinguishable here
    content = A.extract_file(rec["output"])
    got = (pubs(content) - was) if content else set()
    if want & got:
        return "in-force"
    if (stale - want) & got:
        return "alt"
    return "neither"


def run(path):
    by = defaultdict(dict)
    arm = None
    for line in open(path):
        d = json.loads(line)
        arm = d["arm"]
        by[d["session"]][d["request"]] = d
    tally, cells, agree = Counter(), defaultdict(Counter), Counter()
    rows = []
    for sid, recs in sorted(by.items()):
        s = load(sid)
        if s.target_family != FAMILY:
            continue
        entering = replay(s, recs)
        for k in sorted(recs):
            base = entering.get(k)
            if base is None:
                continue
            v = verdict(s, recs[k], base)
            x = classify(s, recs[k], base)
            tally[v] += 1
            cells[(k, alt_was_in_force(s, k))][v] += 1
            agree[(v, x)] += 1
            rows.append((sid, k, s.lifecycle, v, x))

    n = sum(tally.values())
    print(f"\n===== {arm}: names introduced on the {FAMILY} family ({n} requests, "
          f"{n // 2} sessions)")
    print("  NOT a retention measure -- see this file's docstring.")
    for v in ("in-force", "alt", "neither", "vacuous"):
        if tally[v]:
            print(f"    {v:9s} {tally[v]:3d}  ({100 * tally[v] / max(n, 1):.0f}%)")
    print("  by population (request, alternative was in force earlier):")
    for key in sorted(cells):
        t = cells[key]
        print(f"    req{key[0]} superseded={key[1]!s:5s} n={sum(t.values()):3d}  "
              + "  ".join(f"{v}={t[v]}" for v in
                          ("in-force", "alt", "neither", "vacuous") if t[v]))
    print("  agreement with the executable contract measure (stale2.classify):")
    same = sum(c for (v, x), c in agree.items() if v == x)
    print(f"    identical verdict on {same}/{n}")
    for (v, x), c in sorted(agree.items()):
        if v != x:
            print(f"    names={v:9s} contract={x:15s} {c}")
    dis = [r for r in rows if r[3] != r[4]]
    if dis:
        print("  the requests where they disagree (worth reading):")
        for sid, k, lc, v, x in dis:
            print(f"    {sid} req{k} {lc:14s} names={v:9s} contract={x}")


if __name__ == "__main__":
    for p in sys.argv[1:]:
        run(p)
