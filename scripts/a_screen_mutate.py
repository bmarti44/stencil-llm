"""Mutation-audit the candidate-A scorer (registration section 14.8).

Answers the question the Astra re-review called the whole issue: can a
session score J = 1 while the repository is actually wrong?  Every dict
``.get`` lookup and every store write-back in BOTH target files of every
SCREEN slot is broken one at a time in the checkpoint-2 gold, and each
mutation must be caught by some suite.  The audit found 12 undetected
mutations in pre-existing operations that no regression test pinned; after
those were pinned it runs at 0.  A new slot or a changed regression test
must keep it at 0.

Usage: ``uv run python scripts/a_screen_mutate.py``; exit 1 if any mutation
is undetected.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Iterator

from stencil import a_screen as A
from stencil.a_screen_pool import available_slots, load


def defaulted_fields(files: dict[str, str]) -> list[tuple[str, str]]:
    """(field, default) for every dataclass attribute in the project that has a default.
    Resetting one of these is how a reply silently erases an unrelated attribute."""
    out = []
    for src in files.values():
        if "@dataclass" not in src:
            continue
        for m in re.finditer(
            r"\n    (\w+): [^\n=]+ = ([^\n]+)", src
        ):
            out.append((m.group(1), m.group(2).strip()))
    return out


def mutants(src: str, defaults: list[tuple[str, str]]) -> Iterator[tuple[str, str]]:
    """Each (label, mutated source).  Four classes a plausible reply can
    produce, all of which leave the repository wrong (re-review round 3,
    registration section 14.9): a lookup that starts raising, a write-back
    that is gone, a write-back that REPLACES the whole mapping and so
    deletes unrelated records, and an update that resets an unrelated
    defaulted attribute."""
    for m in re.finditer(r"\.get\((\w+)\)", src):
        yield (
            f"get->[] @{m.start()}",
            src[: m.start()] + f"[{m.group(1)}]" + src[m.end() :],
        )
    for m in re.finditer(r"\n(\s+)(self\._(\w+)\[(\w+)\] = (\w+))\n", src):
        yield (
            f"drop write-back @{m.start()}",
            src[: m.start()] + "\n" + src[m.end() :],
        )
        indent, mapping, key, val = m.group(1), m.group(3), m.group(4), m.group(5)
        yield (
            f"write-back replaces the whole mapping @{m.start()}",
            src[: m.start()]
            + f"\n{indent}self._{mapping} = {{{key}: {val}}}\n"
            + src[m.end() :],
        )
    for m in re.finditer(r"replace\((\w+), ", src):
        for fname, default in defaults:
            if f"{fname}=" in src[m.end() : m.end() + 200]:
                continue  # the call already sets this field on purpose
            yield (
                f"reset {fname} to {default} @{m.start()}",
                src[: m.end()] + f"{fname}={default}, " + src[m.end() :],
            )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--slots", default="", help="comma-separated subset, default all 48"
    )
    a = ap.parse_args()
    slots = a.slots.split(",") if a.slots else available_slots()
    undetected: list[tuple[str, str, str]] = []
    total = 0
    for slot in slots:
        s = load(slot)
        f2 = A.gold_files(s, 2)
        base = A.score_checkpoint(s, 2, f2)
        if not base["all"]:
            print(f"{slot}: GOLD FAILS, cannot audit")
            undetected.append((slot, "-", "gold fails"))
            continue
        for path in sorted({r.target for r in s.requests}):
            for label, mut in mutants(f2[path], defaulted_fields(s.files)):
                if mut == f2[path]:
                    continue
                total += 1
                try:
                    res = A.score_checkpoint(s, 2, {**f2, path: mut})
                except Exception as exc:  # a crash is a detection, but say so
                    print(f"{slot} {path} {label}: scorer raised {type(exc).__name__}")
                    continue
                if res["all"]:
                    undetected.append((slot, path, label))
        print(f"{slot}: done ({total} mutations so far)")
    print(f"\nmutations applied: {total}   UNDETECTED: {len(undetected)}")
    for slot, path, label in undetected:
        print(f"   UNDETECTED {slot} {path} {label}")
    if undetected:
        sys.exit(1)


if __name__ == "__main__":
    main()
