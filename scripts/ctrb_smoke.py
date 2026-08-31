#!/usr/bin/env python3
# ruff: noqa: E402, E501
"""CTRB end-to-end plumbing smoke on 12 non-evaluation calibration rows.

This is deliberately **not an evidence gate**: moments are labeled and the
hazard is fit on those same labels.  It proves only that frozen-feature
extraction, deterministic causal branching, checker labels, and the automatic
gate connect end to end.  It must not be quoted as held-out performance.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--rows", type=int, default=12)
    p.add_argument("--moments", type=int, default=30)
    p.add_argument("--trace-max-new", type=int, default=160)
    p.add_argument("--branch-max-new", type=int, default=220)
    p.add_argument("--deadline", type=float, default=300.0)
    p.add_argument("--failing-only", action="store_true")
    p.add_argument("--conflict-top", action="store_true",
                   help="pick the highest conflict-score eligible moments per row (importance sampling for label collection; labels remain causal)")
    return p.parse_args(argv)


def _evenly_pick(records, n):
    """Deterministic spread across a row's eligible trajectory."""
    if n <= 0 or not records:
        return []
    if len(records) <= n:
        return records
    return (
        [records[round(i * (len(records) - 1) / (n - 1))] for i in range(n)]
        if n > 1
        else [records[len(records) // 2]]
    )


def main(argv=None):
    args = parse_args(argv)
    if args.rows < 1 or args.moments < 1:
        raise SystemExit("--rows and --moments must be positive")

    import torch
    from tokenizers import Tokenizer

    from stencil import determinism  # noqa: F401
    from stencil.causal_moments import label_causal_moment, score_row_constraints
    from stencil.ctrb import HazardGate, constraint_spans_of, generate_ctrb
    from stencil.qwen3 import Qwen3
    from stencil.wave import WaveController

    if not torch.cuda.is_available():
        raise SystemExit(
            "CUDA unavailable: CTRB smoke requires the frozen Qwen trunk on GPU"
        )
    rows = [json.loads(line) for line in open(ROOT / "data" / "b3" / "cal-v45.jsonl")]
    if args.failing_only:
        # sample moments where labels can be informative: rows whose BASE
        # calibration generation was non-adherent (recorded, read-only)
        rec = ROOT / "results" / "qwen" / "b3-deficit-cal"
        fail_idx = [i for i in range(len(rows))
                    if not json.loads((rec / f"base-{i:03d}.json").read_text())["adherent"]]
        rows = [rows[i] for i in fail_idx]
    rows = rows[: args.rows]
    if len(rows) != args.rows:
        raise SystemExit(f"requested {args.rows} rows, found {len(rows)}")

    tok = Tokenizer.from_file(str(ROOT / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
    model = Qwen3()
    model.load_state_dict(
        torch.load(ROOT / "models" / "qwen3-1.7b.pt", map_location="cpu"), strict=True
    )
    model = model.to(torch.bfloat16).cuda().eval()
    ctrl = WaveController(beta_max=1.0).cuda()
    ctrl.load_state_dict(
        torch.load(ROOT / "results" / "qwen" / "b3-ce-s0.pt", map_location="cpu")
    )
    ctrl = ctrl.eval()

    # First make native cached trajectories.  The zero gate is a contractual
    # base-equivalent path; only records with a complete delta-5 vector enter.
    by_row = []
    for row_i, row in enumerate(rows):
        spans = constraint_spans_of(tok, row["prompt"])
        result = generate_ctrb(
            model,
            tok,
            row["prompt"],
            ctrl,
            spans,
            HazardGate.constant(0.0),
            max_new=args.trace_max_new,
            deadline_s=args.deadline,
            draft_tokens=0,
            collect_prefixes=True,
        )
        eligible = [r for r in result.trace if r["features"] is not None]
        by_row.append((row_i, row, spans, eligible))
        print(
            f"TRACE row={row_i} tokens={result.n_generated} eligible={len(eligible)}",
            flush=True,
        )

    # Allocate approximately evenly, then fill any remainder in stable order.
    base_n, remainder = divmod(args.moments, len(by_row))
    chosen = []

    def conflict_score(rec):
        # deterministic conflict ranking: entropy rise + margin collapse
        f = rec["features"]
        return f[1] + f[2]

    for position, (row_i, row, spans, eligible) in enumerate(by_row):
        allocation = base_n + int(position < remainder)
        if args.conflict_top:
            picked = sorted(eligible, key=lambda r: (-conflict_score(r), r["step"]))[:allocation]
            picked = sorted(picked, key=lambda r: r["step"])
        else:
            picked = _evenly_pick(eligible, allocation)
        for rec in picked:
            chosen.append((row_i, row, spans, rec))
    if len(chosen) < args.moments:
        seen = {(ri, rec["step"]) for ri, _, _, rec in chosen}
        for row_i, row, spans, eligible in by_row:
            for rec in eligible:
                if (row_i, rec["step"]) not in seen:
                    chosen.append((row_i, row, spans, rec))
                    seen.add((row_i, rec["step"]))
                    if len(chosen) == args.moments:
                        break
            if len(chosen) == args.moments:
                break
    if not chosen:
        raise SystemExit("no eligible causal moments: feature plumbing failed")

    feats, binary_labels, records = [], [], []
    for moment_i, (row_i, row, spans, rec) in enumerate(chosen):
        best = rec["selected_span"]

        def score_fn(text, r=row):
            return score_row_constraints(r, text)

        labeled = label_causal_moment(
            model=model,
            tokenizer=tok,
            prompt=row["prompt"],
            prefix_ids=rec["prefix_ids"],
            selected_span=spans[best],
            score_fn=score_fn,
            dose=1.0,
            burst_tokens=4,
            max_new=args.branch_max_new,
            deadline_s=args.deadline,
        )
        f = tuple(float(x) for x in rec["features"])
        if not all(math.isfinite(x) for x in f):
            raise RuntimeError(f"nonfinite feature at moment {moment_i}: {f}")
        feats.append(f)
        binary_labels.append(int(labeled.label == "helpful"))
        item = {
            "moment": moment_i,
            "row": row_i,
            "key": row["key"],
            "step": rec["step"],
            "span": best,
            "features": f,
            "label": labeled.label,
            "utility_delta": labeled.utility_delta,
            "native_scores": labeled.native_scores,
            "burst_scores": labeled.burst_scores,
            "branches_differ": labeled.native.continuation_ids
            != labeled.burst.continuation_ids,
        }
        records.append(item)
        print("MOMENT " + json.dumps(item, separators=(",", ":")), flush=True)

    counts = Counter(r["label"] for r in records)
    branch_diffs = sum(r["branches_differ"] for r in records)
    if branch_diffs == 0:
        raise SystemExit(
            "all one-burst branches are token-identical: CTRB actuator smoke failed"
        )
    if counts["helpful"] == 0:
        raise SystemExit(
            "no helpful causal moments: the hazard cannot be fit; invoke the registered fallback"
        )

    gate_a = HazardGate.fit(feats, binary_labels, seed=0)
    gate_b = HazardGate.fit(feats, binary_labels, seed=0)
    if gate_a != gate_b:
        raise RuntimeError("deterministic hazard fit did not reproduce")
    probs = [gate_a.probability(x) for x in feats]
    pred = [p >= 0.5 for p in probs]
    fit_acc = sum(
        int(a == bool(y)) for a, y in zip(pred, binary_labels, strict=True)
    ) / len(pred)
    summary = {
        "purpose": "plumbing-smoke-not-evidence",
        "rows": len(rows),
        "moments": len(records),
        "labels": {k: counts[k] for k in ("helpful", "harmful", "neutral")},
        "branch_differences": branch_diffs,
        "fit_accuracy_same_data": fit_acc,
        "helpful_probability_range": [min(probs), max(probs)],
        "fit_deterministic": True,
    }
    print("SUMMARY " + json.dumps(summary, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
