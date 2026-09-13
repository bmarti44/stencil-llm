"""Freeze the six-family candidate-A screen assignment manifest.

Output: results/a-screen/manifest.json.
48 sessions: 3 target families x 3 supporting families; 6 sessions per diagonal cell,
5 per off-diagonal cell (Astra round 8, item 2); 12 sessions per lifecycle class
(stable, replacement, scope, reinstatement), spread as evenly as possible over the nine
cells by a fixed cyclic order. Deterministic; no randomness; run once before any project
is authored.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

TARGETS = ["naming", "validation", "missing_record"]
SUPPORTS = ["return_shape", "error_surface", "logging"]
LIFECYCLE = ["stable", "replacement", "scope", "reinstatement"]


def build() -> list[dict]:
    rows: list[dict] = []
    k = 0
    for i, t in enumerate(TARGETS):
        for j, s in enumerate(SUPPORTS):
            n = 6 if i == j else 5
            for _ in range(n):
                rows.append(
                    {
                        "session": f"S{len(rows) + 1:02d}",
                        "target": t,
                        "support": s,
                        "lifecycle": LIFECYCLE[k % 4],
                    }
                )
                k += 1
    counts = {c: sum(r["lifecycle"] == c for r in rows) for c in LIFECYCLE}
    assert len(rows) == 48 and all(v == 12 for v in counts.values()), counts
    assert all(sum(r["target"] == t for r in rows) == 16 for t in TARGETS)
    assert all(sum(r["support"] == s for r in rows) == 16 for s in SUPPORTS)
    return rows


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="results/a-screen/manifest.json")
    a = ap.parse_args()
    rows = build()
    body = json.dumps({"sessions": rows}, indent=1, sort_keys=True) + "\n"
    Path(a.out).write_text(body)
    print(a.out, hashlib.sha256(body.encode()).hexdigest()[:16])
    for c in LIFECYCLE:
        cells = {(r["target"], r["support"]) for r in rows if r["lifecycle"] == c}
        print(c, len(cells), "cells")


if __name__ == "__main__":
    main()
