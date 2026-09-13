"""A behaviour-preserving private rename must still score J = 1 (round 4, medium).

The registered request asks a reply to keep existing behaviour; it does not name the
target's private attributes.  So a reply that consistently renames ``self._members`` to
``self._records`` is correct, and any suite that fails it is imposing an undocumented
implementation constraint -- a false J = 0 that costs the screen power and, worse, is
invisible.  Grepping the fixtures cannot find it either: the access can hide inside a
monkeypatch spy whose receiver is also spelled ``self``.  So this checks the property.

For every slot, each private attribute the target assigns in ``__init__`` is renamed
consistently through the PROJECT SOURCE of both checkpoint golds -- never in the
suites -- and the session must still score J = 1.  A failure names the slot, the
attribute and the suite that rejected it.

Usage: ``uv run python scripts/a_screen_rename.py [--slots S01,S02]``; exit 1 on any
rejection.
"""

from __future__ import annotations

import argparse
import re
import sys

from stencil import a_screen as A
from stencil.a_screen_pool import available_slots, load


def private_attrs(files: dict[str, str]) -> list[str]:
    """Private attributes assigned in an ``__init__``, i.e. the store's own state."""
    out: list[str] = []
    for src in files.values():
        for m in re.finditer(r"\n        self\.(_\w+)(?: *[:=])", src):
            if m.group(1) not in out:
                out.append(m.group(1))
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--slots", default="", help="comma-separated subset, default all 48"
    )
    a = ap.parse_args()
    slots = a.slots.split(",") if a.slots else available_slots()
    rejected: list[str] = []
    tried = 0
    for slot in slots:
        s = load(slot)
        golds = {k: A.gold_files(s, k) for k in (1, 2)}
        base = {k: A.score_checkpoint(s, k, golds[k]) for k in (1, 2)}
        if not (base[1]["all"] and base[2]["all"]):
            print(f"{slot}: GOLD FAILS, cannot check")
            rejected.append(f"{slot}: gold fails")
            continue
        for attr in private_attrs(golds[2]):
            tried += 1
            new = f"{attr}_renamed"
            scored = {}
            for k in (1, 2):
                files = {
                    p: re.sub(rf"\bself\.{attr}\b", f"self.{new}", src)
                    for p, src in golds[k].items()
                }
                scored[k] = A.score_checkpoint(s, k, files)
            if scored[1]["all"] and scored[2]["all"]:
                continue
            for k in (1, 2):
                bad = [
                    name
                    for name in A.SUITES
                    if scored[k].get(name) is False and base[k].get(name) is not False
                ]
                if bad:
                    rejected.append(f"{slot} self.{attr} @checkpoint {k}: {bad}")
        print(f"{slot}: done ({tried} renames so far)")
    print(f"\nrenames applied: {tried}   REJECTED: {len(rejected)}")
    for line in rejected:
        print(f"   REJECTED {line}")
    if rejected:
        sys.exit(1)


if __name__ == "__main__":
    main()
