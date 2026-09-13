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


def record_classes(files: dict[str, str]) -> dict[str, dict[str, str | None]]:
    """``{ClassName: {field: default or None}}`` for every dataclass in the project.

    Round 4, low: an earlier version pooled every default across every record type, so a
    mutation could name a field the updated type does not have.  That fails with
    "unexpected keyword argument", which detects a wrong keyword rather than an erased
    attribute, and `stencil.contracts.run_tests` returns pytest's short summary
    ("1 failed in 0.02s"), so the distinction is invisible downstream.  Fields are
    associated with their own class here and emitted only for that class.
    """
    out: dict[str, dict[str, str | None]] = {}
    for src in files.values():
        for m in re.finditer(
            r"@dataclass[^\n]*\nclass (\w+)[^\n]*:\n((?:    [^\n]*\n|\n)+)", src
        ):
            fields: dict[str, str | None] = {}
            for line in m.group(2).split("\n"):
                fm = re.match(r"    (\w+): [^=\n]+?(?: = (.+))?$", line)
                if fm and not line.strip().startswith("def "):
                    fields[fm.group(1)] = fm.group(2).strip() if fm.group(2) else None
            if fields:
                out[m.group(1)] = fields
    return out


def class_of(var: str, classes: dict[str, dict[str, str | None]]) -> str | None:
    """The record class a local variable holds, by this pool's naming convention
    (``hold`` -> ``Hold``, ``recipe`` -> ``Recipe``).  ``None`` when it cannot be
    resolved; the caller then labels the mutation type-unverified rather than guess."""
    for name in classes:
        if var.lower() == name.lower() or var.lower().endswith("_" + name.lower()):
            return name
    return None


def defaulted_fields(files: dict[str, str]) -> list[tuple[str, str]]:
    """(field, default) for every dataclass attribute in the project that has a default.
    Resetting one of these is how a reply silently erases an unrelated attribute."""
    out = []
    for cls in record_classes(files).values():
        for field, default in cls.items():
            if default is not None:
                out.append((field, default))
    return out


def required_fields(files: dict[str, str]) -> list[str]:
    """Every dataclass attribute with NO default — the record's identity and its
    other mandatory data.  Round 4's S01 escape changed one of these during an
    update (``replace(recipe, recipe_id=tag, ...)``): tags, servings, title and the
    neighbours were all preserved, so every suite passed while the record's own id
    had been replaced.  Audited separately from the defaulted fields."""
    out = []
    for src in files.values():
        if "@dataclass" not in src:
            continue
        for m in re.finditer(r"\n    (\w+): [^\n=]+(?= *\n)", src):
            name = m.group(1)
            if name not in out:
                out.append(name)
    return out


def counters(src: str) -> list[str]:
    """Attributes the target increments to allocate new ids (``self._counter += 1``).
    Resetting one disturbs no record already stored, so a fixture that only checks
    existing records cannot see it: the NEXT insertion silently reuses a live id and
    overwrites an earlier record (round 4)."""
    return sorted({m.group(1) for m in re.finditer(r"self\.(_\w+) \+= 1", src)})


def mutants(
    src: str, classes: dict[str, dict[str, str | None]]
) -> Iterator[tuple[str, str]]:
    """Each (label, mutated source).  Seven classes a plausible reply can produce, all
    of which leave the repository wrong: a lookup that starts raising; a write-back that
    is gone; a write-back that REPLACES the whole mapping and so deletes unrelated
    records; an update that resets an unrelated defaulted attribute, at a ``replace(``
    call site and again through a ``with_X(...)`` record helper; an update that changes
    a REQUIRED field, so the record keeps every other value but loses its identity; and
    a reset of the id allocator, which corrupts the next insertion rather than any
    record already stored.  The last two are round 4's demonstrated escapes."""
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
    # Classes 4-6: an update that keeps the visible change but additionally resets
    # an unrelated DEFAULTED attribute, or replaces a REQUIRED one (typically the
    # record's own id -- round 4's S01 escape).  Each call site's record type is
    # resolved first, so every emitted mutant names a field that type actually has: a
    # mutant naming a foreign field fails with "unexpected keyword argument", which is
    # a wrong keyword rather than an erased attribute, and pytest's short summary hides
    # the difference.
    sites: list[tuple[int, int, str, str, str]] = []
    for m in re.finditer(r"replace\((\w+), ", src):
        sites.append((m.start(), m.end(), m.group(1), "", ""))
    # A target that updates through a record helper (``rec.with_status(...)``) has no
    # ``replace(var, `` call site at all, so it needs its own form: wrap the helper's
    # result, same visible update, one extra field changed.  An explicit import is
    # prepended so the mutant always compiles and a failure means the suites caught the
    # change, not a NameError (group-8 agent report, round 3).
    for m in re.finditer(r"(\w+)\.with_\w+\([^()]*\)", src):
        sites.append((m.start(), m.end(), m.group(1), "helper ", m.group(0)))

    for start, end, var, kind, call in sites:
        cls = class_of(var, classes)
        if cls is None:
            continue  # unresolved type: a guessed field would be false coverage
        already = call if call else src[end : end + 200]
        for fname, default in classes[cls].items():
            if f"{fname}=" in already:
                continue  # the call already sets this field on purpose
            value = default if default is not None else '"_audit"'
            what = "reset" if default is not None else "set required"
            if call:
                mutated = (
                    "import dataclasses as _audit_dc\n"
                    + src[:start]
                    + f"_audit_dc.replace({call}, {fname}={value})"
                    + src[end:]
                )
            else:
                mutated = src[:end] + f"{fname}={value}, " + src[end:]
            yield (f"{kind}{what} {cls}.{fname} to {value} @{start}", mutated)

    # Class 7 (round 4): reset the id allocator at the top of a method that is not
    # itself the allocator.  Nothing already stored changes, so only a fixture that
    # CREATES a record after the update can see the new record reuse a live id.
    # Restricted to methods that already WRITE state: a reply might plausibly clobber a
    # counter while editing an update operation, but not inside a pure reader, and
    # generating the reader cases would inflate the count without adding coverage.
    for counter in counters(src):
        for m in re.finditer(r"\n    def (\w+)\(self[^\n]*\n", src):
            name = m.group(1)
            if name.startswith("_"):
                continue
            end = src.find("\n    def ", m.end())
            body = src[m.end() : end if end != -1 else len(src)]
            if f"self.{counter} += 1" in body or f"self.{counter} =" in body:
                continue  # this IS the allocator, or already assigns it
            if not re.search(r"self\._\w+(\[[^\]]*\])? *=|\.append\(|\.write", body):
                continue  # a pure reader: not a plausible place for a reply to do this
            yield (
                f"reset allocator self.{counter} in {name} @{m.start()}",
                src[: m.end()] + f"        self.{counter} = 0\n" + src[m.end() :],
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
        classes = record_classes(s.files)
        for path in sorted({r.target for r in s.requests}):
            for label, mut in mutants(f2[path], classes):
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
