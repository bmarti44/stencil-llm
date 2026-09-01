# ruff: noqa
"""Fit and certify the fixed six-feature E2 hazard gate.

Consumes only the completed synthetic harvest.  A failed count or held-out
gate writes an honest report and exits nonzero; it never opens Multi-IF.
"""

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--harvest", default="e2-corrected-harvest")
    parser.add_argument("--out", default="e2-hazard-gate.json")
    return parser.parse_args()


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def combined_sha256(paths):
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.name.encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def atomic_json(path, value):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=1))
    tmp.rename(path)


def main():
    args = parse_args()
    from stencil.ctrb import FEATURE_NAMES, HazardGate
    from stencil.e2_gate import (
        certification_reasons,
        evaluate_discrimination,
        select_threshold,
    )

    harvest = ROOT / "results" / "qwen" / args.harvest
    meta_path = harvest / "meta.json"
    summary_path = harvest / "summary.json"
    if not meta_path.exists() or not summary_path.exists():
        raise RuntimeError("completed harvest meta+summary required")
    meta = json.loads(meta_path.read_text())
    summary = json.loads(summary_path.read_text())
    session_paths = sorted(harvest.glob("session-*.json"))
    if len(session_paths) != int(meta["sessions"]):
        raise RuntimeError("partial harvest: session count mismatch")
    records = [
        moment
        for path in session_paths
        for moment in json.loads(path.read_text())["moments"]
    ]
    labels = Counter(record["label"] for record in records)
    if len(records) != int(summary["moments"]) or dict(sorted(labels.items())) != summary["labels"]:
        raise RuntimeError("harvest summary does not reproduce from per-moment records")

    provenance = {
        "harvest": str(harvest.relative_to(ROOT)),
        "harvest_meta_sha256": sha256(meta_path),
        "harvest_summary_sha256": sha256(summary_path),
        "harvest_records_sha256": combined_sha256(session_paths),
        "fit_runner_sha256": sha256(Path(__file__)),
        "gate_module_sha256": sha256(ROOT / "src" / "stencil" / "e2_gate.py"),
        "ctrb_sha256": sha256(ROOT / "src" / "stencil" / "ctrb.py"),
    }
    label_counts = {name: labels.get(name, 0) for name in ("helpful", "harmful", "neutral")}
    report = {
        "status": "PENDING",
        "provenance": provenance,
        "feature_names": list(FEATURE_NAMES),
        "label_counts": label_counts,
        "n_moments": len(records),
    }
    count_reasons = certification_reasons(label_counts, {"schemes": {}})
    if count_reasons:
        report.update({"status": "FAIL", "gate_pass": False, "failure_reasons": count_reasons})
        atomic_json(ROOT / "results" / "qwen" / args.out, report)
        print(json.dumps(report, indent=1))
        raise SystemExit(2)

    discrimination = evaluate_discrimination(records)
    reasons = certification_reasons(label_counts, discrimination)
    report["discrimination"] = discrimination
    report["failure_reasons"] = reasons
    report["gate_pass"] = not reasons
    if reasons:
        report["status"] = "FAIL"
        atomic_json(ROOT / "results" / "qwen" / args.out, report)
        print(json.dumps(report, indent=1))
        raise SystemExit(2)

    features = [record["features"] for record in records]
    binary = [int(record["label"] == "helpful") for record in records]
    utility = [int(record["utility_delta"]) for record in records]
    first = HazardGate.fit(features, binary, seed=0)
    second = HazardGate.fit(features, binary, seed=0)
    if first != second:
        raise RuntimeError("fixed-seed hazard fit is not bitwise deterministic")
    session_oof = discrimination["schemes"]["session"]["full"]["probabilities"]
    threshold = select_threshold(session_oof, binary, utility)
    report.update(
        {
            "status": "PASS",
            "gate": {
                "mean": list(first.mean),
                "scale": list(first.scale),
                "weights": list(first.weights),
                "bias": first.bias,
                "threshold": threshold,
                "dose": 3.0,
                "action": "sustained_all_live_constraint_spans",
                "draft_tokens": 0,
                "fit_seed": 0,
                "bitwise_repeat": True,
            },
        }
    )
    atomic_json(ROOT / "results" / "qwen" / args.out, report)
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
