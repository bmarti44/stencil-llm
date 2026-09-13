# ruff: noqa: E501
"""Freeze the candidate-A SCREEN pool (registration §1-§2): per-slot content hashes,
module file hashes, manifest agreement, cell/lifecycle counts, and disjointness from the
TRAIN pool, the pre-check projects and the development projects (package names, module
paths, function names).  Writes ``results/a-screen/screen-pool.json``.  Refuses to write
if any slot is missing or any check fails.

Usage: ``uv run python scripts/a_screen_freeze.py``
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import sys
from collections import Counter
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stencil.a_screen_pool import screen_sessions  # noqa: E402
from stencil.a_train_pool import train_sessions  # noqa: E402

PRECHECK_PKGS = {
    "inventory",
    "mailer",
    "catalog",
    "auth",
    "ledger",
    "exporter",
    "settings",
    "queue",
}
DEV_PKGS = {"kvstore", "fileio", "users", "config"}


def sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def defs(files: dict[str, str]) -> set[str]:
    names = set()
    for content in files.values():
        try:
            tree = ast.parse(content)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                names.add(node.name)
    return names


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=str(ROOT / "results/a-screen/screen-pool.json"))
    a = ap.parse_args()
    sessions = screen_sessions(check_manifest=True)
    problems = []
    if len(sessions) != 48:
        problems.append(f"{len(sessions)} slots, expected 48")
    pkgs = Counter(s.project for s in sessions)
    dup = [p for p, n in pkgs.items() if n > 1]
    if dup:
        problems.append(f"duplicate package names {dup}")
    train = train_sessions()
    train_pkgs = {s.project for s in train}
    clash = set(pkgs) & (train_pkgs | PRECHECK_PKGS | DEV_PKGS)
    if clash:
        problems.append(f"package names shared with another pool: {sorted(clash)}")
    # module paths and public defs: a screen project may not reuse a train construction
    train_paths = {p for s in train for p in s.files}
    train_defs = set()
    for s in train:
        train_defs |= {n for n in defs(s.files) if not n.startswith("_")}
    for s in sessions:
        shared_paths = set(s.files) & train_paths
        if shared_paths:
            problems.append(
                f"{s.id}: module paths shared with TRAIN {sorted(shared_paths)}"
            )
        shared = {n for n in defs(s.files) if not n.startswith("_")} & train_defs
        generic = {"Backend", "find", "add", "write", "count", "all", "__init__"}
        shared -= generic
        if shared:
            problems.append(
                f"{s.id}: class/function names shared with TRAIN {sorted(shared)}"
            )
    cells = Counter((s.target_family, s.support_family) for s in sessions)
    lifec = Counter(s.lifecycle for s in sessions)
    out = {
        "n": len(sessions),
        "cells": {f"{t}|{u}": n for (t, u), n in sorted(cells.items())},
        "lifecycle": dict(sorted(lifec.items())),
        "support_states": dict(
            Counter(
                f"{s.support_family}={s.tags.get('support_state', '?')}"
                for s in sessions
            )
        ),
        "slots": {
            s.id: {
                "project": s.project,
                "target": s.target_family,
                "support": s.support_family,
                "lifecycle": s.lifecycle,
                "states": list(s.states),
                "state_at": list(s.state_at),
                "content_sha256": sha(json.dumps(asdict(s), sort_keys=True)),
                "module_sha256": sha(
                    (
                        ROOT / "src/stencil/a_screen_pool" / f"{s.id.lower()}.py"
                    ).read_text()
                ),
            }
            for s in sessions
        },
        "problems": problems,
    }
    out["pool_sha256"] = sha(
        "".join(v["content_sha256"] for v in out["slots"].values())
    )
    print(json.dumps({k: v for k, v in out.items() if k != "slots"}, indent=1))
    if problems:
        print("NOT FROZEN: problems above")
        sys.exit(1)
    Path(a.out).write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(f"frozen {out['n']} slots pool_sha256={out['pool_sha256']} -> {a.out}")


if __name__ == "__main__":
    main()
