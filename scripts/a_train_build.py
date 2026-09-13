# ruff: noqa: E501
"""Build, self-check and freeze the candidate-A TRAIN pool (registration §1, §4).

Checks every generated session: gold reaches every suite at both checkpoints,
cross-state gold fails the applicable contract suite (and passes its own), the
unmodified target fails the functional suite, and the packing policy keeps every rule
turn while compacting before both live requests.  Writes
``results/a-screen/train-pool.json`` with per-session sha256 hashes, cell counts and
the counterbalance table.  Usage: ``uv run python scripts/a_train_build.py [--jobs 8]``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stencil import a_screen as A  # noqa: E402
from stencil.a_train_pool import make_session, train_sessions  # noqa: E402


def session_hash(s: A.Session) -> str:
    body = json.dumps(asdict(s), sort_keys=True)
    return hashlib.sha256(body.encode()).hexdigest()[:16]


def check_exec(key: tuple[str, str, str, int]) -> tuple[str, list[str]]:
    s = make_session(*key)
    problems = []
    f1 = A.gold_files(s, 1)
    r1 = A.score_checkpoint(s, 1, f1)
    if not r1["all"]:
        problems.append(f"gold@1 {r1}")
    f2 = A.gold_files(s, 2)
    r2 = A.score_checkpoint(s, 2, f2)
    if not r2["all"]:
        problems.append(f"gold@2 {r2}")
    for k in (1, 2):
        st = s.state_at[k - 1]
        ot = s.other(st)
        files = A.gold_files(s, k, state=ot)
        r = s.requests[k - 1]
        c_ok, _ = A.run_tests(files, r.contract_tests[st])
        if c_ok:
            problems.append(f"cross@{k} reaches contract")
        f_ok, msg = A.run_tests(files, r.functional_tests)
        if not f_ok:
            problems.append(f"cross@{k} not functional: {msg}")
        own, _ = A.run_tests(files, r.contract_tests[ot])
        if not own:
            problems.append(f"cross@{k} fails own contract")
    un1, _ = A.run_tests(dict(s.files), s.requests[0].functional_tests)
    if un1:
        problems.append("request 1 already satisfied")
    un2, _ = A.run_tests(f1, s.requests[1].functional_tests)
    if un2:
        problems.append("request 2 already satisfied")
    return s.id, problems


def check_packing(s: A.Session, count) -> list[str]:
    problems = []
    m1 = A.session_messages(s, 1, dict(s.files))
    kept1, idx1 = A.pack(m1, count)
    surv1 = A.surviving_prefix_turns(idx1)
    if not set(s.rule_turns) <= surv1:
        problems.append(f"rule turn dropped @1 {sorted(surv1)}")
    if len(surv1) >= 16:
        problems.append("no compaction @1")
    f1 = A.gold_files(s, 1)
    m2 = A.session_messages(s, 2, f1, A.gold_reply(s, 1), {s.requests[0].target})
    kept2, idx2 = A.pack(m2, count)
    surv2 = A.surviving_prefix_turns(idx2)
    if not set(s.rule_turns) <= surv2:
        problems.append(f"rule turn dropped @2 {sorted(surv2)}")
    if len(surv2) >= len(surv1):
        problems.append("no further compaction @2")
    if s.irrelevant_event:
        m3 = A.session_messages(
            s,
            2,
            f1,
            A.gold_reply(s, 1),
            {s.requests[0].target},
            event=s.irrelevant_event,
        )
        _, idx3 = A.pack(m3, count)
        if not set(s.rule_turns) <= A.surviving_prefix_turns(idx3):
            problems.append("rule turn dropped @2 (irrelevant variant)")
    return problems


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--jobs", type=int, default=8)
    ap.add_argument("--out", default=str(ROOT / "results/a-screen/train-pool.json"))
    ap.add_argument("--hub", default=str(ROOT / "deploy/stencil_focus/build/hub-4b"))
    ap.add_argument("--skip-exec", action="store_true")
    a = ap.parse_args()

    sessions = train_sessions()
    keys = [
        (s.target_family, s.support_family, s.lifecycle, int(s.id.rsplit("-", 1)[1]))
        for s in sessions
    ]
    problems: dict[str, list[str]] = {}
    if not a.skip_exec:
        with ProcessPoolExecutor(a.jobs) as ex:
            for sid, probs in ex.map(check_exec, keys, chunksize=4):
                if probs:
                    problems[sid] = probs
                    print(sid, probs, flush=True)
    from transformers import AutoTokenizer

    tok = AutoTokenizer.from_pretrained(a.hub, trust_remote_code=True)
    count = A.make_counter(tok)
    sizes = []
    for s in sessions:
        p = check_packing(s, count)
        if p:
            problems.setdefault(s.id, []).extend(p)
            print(s.id, p, flush=True)
        m1 = A.session_messages(s, 1, dict(s.files))
        sizes.append(count(m1))
    cells = Counter((s.target_family, s.support_family, s.lifecycle) for s in sessions)
    balance = Counter(
        (
            s.target_family,
            s.support_family,
            s.lifecycle,
            s.tags["precedent_matches_current"],
        )
        for s in sessions
    )
    out = {
        "n": len(sessions),
        "cells": len(cells),
        "per_cell": sorted(set(cells.values())),
        "counterbalance_per_cell": sorted(set(balance.values())),
        "prompt_tokens_at_request1": {
            "min": min(sizes),
            "max": max(sizes),
            "mean": sum(sizes) / len(sizes),
        },
        "problems": problems,
        "hashes": {s.id: session_hash(s) for s in sessions},
        "pool_sha256": hashlib.sha256(
            "".join(session_hash(s) for s in sessions).encode()
        ).hexdigest()[:16],
    }
    Path(a.out).write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(
        f"sessions={out['n']} cells={out['cells']} per_cell={out['per_cell']} "
        f"balance={out['counterbalance_per_cell']} problems={len(problems)} "
        f"tokens@1={out['prompt_tokens_at_request1']} pool={out['pool_sha256']}"
    )


if __name__ == "__main__":
    main()
