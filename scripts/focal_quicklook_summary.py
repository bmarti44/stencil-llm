"""Summarise a focal quicklook JSON and apply the pilot continuation gate.

Gate (Astra root-cause §12, ledger 2026-09-12 20:55Z): a focal candidate continues
when its mean fraction beats ``before_compact`` by >= 10 points, it wins on >= 2 of 3
items, and it adds no net output failures (cap / no-parse / repeated-line runs).
This is a pilot reading on the exposed SETUP-LONG split, never a result.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def failures(a: dict) -> int:
    p = a.get("parse", {"parses": True, "repeated_line_runs": 0})
    return (
        int(a.get("truncated", False))
        + int(not p["parses"])
        + int(p["repeated_line_runs"] > 0)
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("path", nargs="?", default="results/focal/quicklook.json")
    ap.add_argument("--control", default="before_compact")
    args = ap.parse_args()
    recs = json.loads(Path(args.path).read_text())
    arms = list(recs[0]["arms"])
    print(f"{'item':8s} " + " ".join(f"{a[:20]:>20s}" for a in arms))
    for r in recs:
        row = []
        for a in arms:
            x = r["arms"].get(a)
            if x is None:
                row.append(f"{'-':>20s}")
                continue
            s = x["score"]["fraction"]
            p = x.get("parse", {"parses": True, "repeated_line_runs": 0})
            flag = "T" if x.get("truncated") else ("P" if not p["parses"] else "")
            flag += "L" if p["repeated_line_runs"] else ""
            flag += f"e{x['echoed_lines']}" if x.get("echoed_lines") else ""
            row.append(f"{s:6.3f} {x.get('insertions', 0):2d}i {flag:>6s}")
        print(f"{r['id']:8s} " + " ".join(f"{c:>20s}" for c in row))
    print()
    ctrl = args.control
    for a in arms:
        if a in (ctrl, "base"):
            continue
        pairs = [(r["arms"][a], r["arms"][ctrl]) for r in recs if a in r["arms"]]
        if not pairs:
            continue
        d = [x["score"]["fraction"] - c["score"]["fraction"] for x, c in pairs]
        wins = sum(v > 0 for v in d)
        fail = sum(failures(x) - failures(c) for x, c in pairs)
        mean = 100 * sum(d) / len(d)
        ok = mean >= 10 and wins >= 2 and fail <= 0
        print(
            f"{a:22s} vs {ctrl}: mean {mean:+6.1f} pts, wins {wins}/{len(d)}, "
            f"net failures {fail:+d} -> {'CONTINUE' if ok else 'no'}"
        )


if __name__ == "__main__":
    main()
