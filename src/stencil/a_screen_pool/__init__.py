"""SCREEN pool of the six-family candidate-A screen: one module per manifest slot
(``s01.py`` … ``s48.py``), each exposing ``build() -> Session``.  Authored 2026-09-13+
for this program; evaluated-on only (never fit on); disjoint from the TRAIN pool
(:mod:`stencil.a_train_pool`), from the pre-check projects and from ``data/bench/``.
Frozen by hash list in ``results/a-screen/`` before any generation.
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path

from stencil.a_screen import Session

_HERE = Path(__file__).parent
MANIFEST = _HERE.parents[2] / "results" / "a-screen" / "manifest.json"


def available_slots() -> list[str]:
    return sorted(p.stem.upper() for p in _HERE.glob("s[0-9][0-9].py"))


def load(slot: str) -> Session:
    mod = importlib.import_module(f"stencil.a_screen_pool.{slot.lower()}")
    s = mod.build()
    s.validate()
    assert s.id == slot, f"{slot}: module builds {s.id}"
    return s


def screen_sessions(check_manifest: bool = True) -> list[Session]:
    sessions = [load(slot) for slot in available_slots()]
    if check_manifest and MANIFEST.exists():
        rows = {r["session"]: r for r in json.loads(MANIFEST.read_text())["sessions"]}
        for s in sessions:
            row = rows[s.id]
            for k in ("target", "support", "lifecycle"):
                want = row[k]
                got = {"target": s.target_family, "support": s.support_family}.get(
                    k, s.lifecycle
                )
                assert got == want, f"{s.id}: manifest {k}={want}, session has {got}"
    return sessions
