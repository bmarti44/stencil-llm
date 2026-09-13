"""Check that a pool-fixture repair changed ONLY the executable fixtures (section 15.6).

Rebuilds every differing SCREEN slot's ``Session`` from a git ref and from the working
tree and compares every field of the session and of both requests EXCEPT each request's
``functional_tests`` and ``regression_tests``.  A difference anywhere else means a
repair round silently altered the evaluation itself — the project files, the request
text, the target, the gold, a contract or support suite, a prefix turn or a family
label — which would make the screen's result incomparable with its registration.  A
slot whose file differs without any suite body changing is also reported, so a stray
edit cannot hide.

Usage: ``uv run python scripts/a_screen_containment.py [--ref HEAD]``; exit 1 on any
violation.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import fields

from stencil.a_screen_pool import available_slots, load

EXEMPT = ("functional_tests", "regression_tests")


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], capture_output=True, text=True, check=True
    ).stdout


def build_at(ref: str, slot: str):
    src = _git("show", f"{ref}:src/stencil/a_screen_pool/{slot.lower()}.py")
    ns: dict = {"__name__": f"_{ref}_{slot.lower()}"}
    exec(compile(src, f"{ref}:{slot.lower()}.py", "exec"), ns)  # noqa: S102
    return ns["build"]()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ref", default="HEAD", help="git ref to compare against")
    a = ap.parse_args()

    changed = _git(
        "diff", "--name-only", a.ref, "--", "src/stencil/a_screen_pool/"
    ).split()
    slots = [p.rsplit("/", 1)[1][:-3].upper() for p in changed]
    print(f"slot modules differing from {a.ref}: {len(slots)}")

    bad: list[str] = []
    for slot in slots:
        old, new = build_at(a.ref, slot), load(slot)
        for f in fields(old):
            if f.name == "requests":
                continue
            if getattr(old, f.name) != getattr(new, f.name):
                bad.append(f"{slot}: Session.{f.name} changed")
        if len(old.requests) != len(new.requests):
            bad.append(f"{slot}: request count changed")
            continue
        for i, (ro, rn) in enumerate(zip(old.requests, new.requests), start=1):
            for f in fields(ro):
                if f.name in EXEMPT:
                    continue
                if getattr(ro, f.name) != getattr(rn, f.name):
                    bad.append(f"{slot}: request {i} .{f.name} changed")
        if all(
            getattr(ro, k) == getattr(rn, k)
            for ro, rn in zip(old.requests, new.requests)
            for k in EXEMPT
        ):
            bad.append(f"{slot}: file differs but no suite body changed")

    untouched = sorted(set(available_slots()) - set(slots))
    print(f"slots untouched: {len(untouched)} {untouched}")
    print(f"\nCONTAINMENT VIOLATIONS: {len(bad)}")
    for line in bad:
        print("  ", line)
    if bad:
        sys.exit(1)


if __name__ == "__main__":
    main()
