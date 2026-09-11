"""Cleanup invariants: prove a behaviour-preserving cleanup changed no science output.

Computes a digest of (1) the Multi-IF 909 scorer re-applied to every saved
generation and the paired summary recomputed from the saved records, (2) the
synthetic T2 session generator's rendered prompts and ledgers for fixed seeds, and
(3) ``score_work`` applied to the canonical reference programs for those sessions.
``--write`` stores the digest (run it on the pre-cleanup tag), ``--check``
recomputes and compares (run it after every cleanup commit). Any difference is a
cleanup regression, not a style choice.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

MULTIIF_DIR = ROOT / "results" / "qwen" / "multiif-evict-909-prequery-v2"
MULTIIF_DATA = ROOT / "data" / "bench" / "multiif_en.jsonl"
DEFAULT_OUT = ROOT / "results" / "cleanup-invariants" / "digest.json"
T2_SEEDS = {
    "dev": [13_400_000 + i for i in range(4)],
    "final": [13_600_000 + i for i in range(4)],
}


def _load_multiif_module():
    spec = importlib.util.spec_from_file_location(
        "multiif_evict", ROOT / "scripts" / "multiif_evict.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _sha(obj: object) -> str:
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, default=str).encode()
    ).hexdigest()


def multiif_digest(limit: int | None) -> dict:
    mod = _load_multiif_module()
    rows = {}
    with open(MULTIIF_DATA, encoding="utf-8") as fh:
        for index, line in enumerate(fh):
            rows[index] = json.loads(line)
    records = []
    for path in sorted(MULTIIF_DIR.glob("conv-*.json")):
        records.append(json.loads(path.read_text()))
    if limit:
        records = records[:limit]
    rescored = {}
    mismatches = []
    for record in records:
        row = rows[record["ci"]]
        turn = record["last_turn"]
        for arm, result in record["arms"].items():
            if result is None:  # arm not run (e.g. control impossible)
                continue
            fields = mod._score_fields(row, turn, result["text"])
            stored = result["scores"]
            key = f"{record['ci']}:{arm}"
            rescored[key] = fields
            if fields != stored:
                mismatches.append(key)
    summary = mod.summarize_records(records) if len(records) >= 2 else {}
    arms = {
        arm: {k: v for k, v in stats.items() if not isinstance(v, (list, dict))}
        for arm, stats in summary.get("arms", {}).items()
    }
    return {
        "n_records": len(records),
        "rescore_sha": _sha(rescored),
        "rescore_mismatches_vs_saved": mismatches,
        "arm_counts": arms,
        "contrasts": summary.get("contrasts", {}),
    }


def t2_digest() -> dict:
    from stencil.t2_runner import score_work
    from stencil.t2_sessions import generate_t2, ledger_text, prompt_at
    from stencil.wave_ref import canonical_code

    out = {}
    for split, seeds in T2_SEEDS.items():
        for seed in seeds:
            sess = generate_t2(seed, split=split)
            prompts = {}
            scores = {}
            for wt in sess.work_turns:
                prompts[wt] = prompt_at(sess, wt, split=split)
                code = canonical_code(sess, wt)
                wr = score_work(code, sess, wt)
                scores[wt] = {
                    "code": code,
                    "parse": wr.parse,
                    "exec_ok": wr.exec_ok,
                    "per_opportunity": wr.per_opportunity,
                }
            out[f"{split}:{seed}"] = {
                "prompts_sha": _sha(prompts),
                "ledgers_sha": _sha(
                    {wt: ledger_text(sess.ledger_at[wt]) for wt in sess.work_turns}
                ),
                "scores_sha": _sha(scores),
                "n_work_turns": len(sess.work_turns),
            }
    return out


def compute(limit: int | None) -> dict:
    return {"multiif": multiif_digest(limit), "t2": t2_digest()}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="store the digest")
    mode.add_argument(
        "--check", action="store_true", help="compare with the stored digest"
    )
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="only the first N Multi-IF records (smoke)",
    )
    args = parser.parse_args(argv)
    digest = compute(args.limit)
    if args.write:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(digest, indent=1, sort_keys=True))
        print(f"wrote {args.out}")
        return 0
    stored = json.loads(args.out.read_text())
    diffs = []
    for section in ("multiif", "t2"):
        for key, value in digest[section].items():
            if stored[section].get(key) != value:
                diffs.append(f"{section}.{key}")
    if diffs:
        print("CLEANUP INVARIANT VIOLATION: " + ", ".join(diffs))
        return 1
    print(
        f"cleanup invariants hold: {digest['multiif']['n_records']} Multi-IF records "
        f"re-scored, {len(digest['t2'])} T2 sessions regenerated"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
