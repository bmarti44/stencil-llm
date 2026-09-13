"""How close is the screen's gold to the training pool's gold?

Decision-relevant, CPU-only, and prompted by the cf training curve: the run
reached CE 0.0006 while `epochs_completed` was still 0, so every example it
learned on was UNSEEN when it trained on it.  A near-zero loss on fresh examples
means the gold completion is close to determined by the prefix under this
generator.  If the screen's gold is also close to the training pool's gold, then
an adapter that wins the screen may be reproducing a template it has already
been fitted to, and the win would not be evidence about tracking which
convention is in force.

This measures the thing directly, with no model: for every SCREEN gold (48
sessions x 2 requests x 2 states) find the most similar TRAIN gold (576 x 2 x 2)
and report the distribution of that maximum.  Two measures, because either alone
is easy to fool:

  jaccard   over identifier/keyword tokens -- catches "same code, renamed"
  ratio     difflib on the source text, on the jaccard top-8 only -- catches
            "same text, reordered"

Read it as: a max similarity near 1.0 across the board means the screen is
largely a memorisation test.  A spread well below 1.0 means the screen asks for
code the adapter has not been shown.  Neither reading is a pass/fail gate; it is
a caveat that must travel with any positive result.

    uv run python results/a-screen/analysis/overlap.py
"""

import re
import statistics
import sys
from difflib import SequenceMatcher

sys.path.insert(0, "/home/bmarti44/stencil-llm/src")
from stencil.a_screen_pool import screen_sessions  # noqa: E402
from stencil.a_train_pool import train_sessions  # noqa: E402

TOKEN = re.compile(r"[A-Za-z_][A-Za-z_0-9]*")
TOPK = 8


def tokens(src):
    return frozenset(TOKEN.findall(src))


def golds(sessions):
    out = []
    for s in sessions:
        for k, req in enumerate(s.requests, 1):
            for state, src in sorted(req.gold.items()):
                out.append((s.id, k, state, s.target_family, src, tokens(src)))
    return out


def main():
    screen = golds(screen_sessions())
    train = golds(train_sessions())
    print(f"{len(screen)} screen golds vs {len(train)} train golds")

    rows = []
    for sid, k, state, family, src, toks in screen:
        scored = []
        for tid, _, _, tfam, tsrc, ttoks in train:
            inter = len(toks & ttoks)
            if not inter:
                continue
            scored.append((inter / len(toks | ttoks), tsrc, tid, tfam))
        scored.sort(reverse=True, key=lambda x: x[0])
        best_j = scored[0][0] if scored else 0.0
        best_r, best_id, best_fam = 0.0, "-", "-"
        for _j, tsrc, tid, tfam in scored[:TOPK]:
            r = SequenceMatcher(None, src, tsrc).ratio()
            if r > best_r:
                best_r, best_id, best_fam = r, tid, tfam
        rows.append((sid, k, state, family, best_j, best_r, best_id, best_fam))

    for name, idx in (("token jaccard", 4), ("difflib ratio", 5)):
        vals = sorted(r[idx] for r in rows)
        n = len(vals)
        print(f"\n  max {name} to ANY training gold, over {n} screen golds")
        print(f"    min {vals[0]:.3f}   p25 {vals[n // 4]:.3f}   "
              f"median {statistics.median(vals):.3f}   p75 {vals[3 * n // 4]:.3f}   "
              f"max {vals[-1]:.3f}")
        for bar in (0.95, 0.90, 0.80, 0.70):
            print(f"    >= {bar:.2f}: {sum(1 for v in vals if v >= bar):3d}/{n}")

    print("\n  by family (median of the max difflib ratio)")
    fams = sorted({r[3] for r in rows})
    for f in fams:
        vals = [r[5] for r in rows if r[3] == f]
        print(f"    {f:16s} n={len(vals):3d}  median {statistics.median(vals):.3f}  "
              f"max {max(vals):.3f}")

    print("\n  the 10 closest screen golds (the memorisation risk, if any)")
    for row in sorted(rows, key=lambda r: -r[5])[:10]:
        sid, k, state, family, j, r, tid, tfam = row
        print(f"    {sid} req{k} {state:10s} {family:14s} ratio {r:.3f} "
              f"jaccard {j:.3f}  nearest {tid} ({tfam})")


if __name__ == "__main__":
    main()
