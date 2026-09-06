"""Reproduce Check 45's R4 stop from the pilot README; stdlib/CPU only."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    source = ROOT / "results/quick-checks/composition-pilot/README.md"
    raw = source.read_bytes()
    heading = raw.decode("utf-8").splitlines()[0]
    if heading != "# Composition DEV pilot — INELIGIBLE / INCOMPLETE":
        raise SystemExit(
            "Pilot status changed: reassess eligibility; script only reproduces R4."
        )
    output = ROOT / "results/quick-checks/check45"
    output.mkdir(parents=True, exist_ok=True)
    # Stop before loading records, hidden states, embedding models, or labels.
    (output / "per-fold.jsonl").write_text("", encoding="utf-8")
    manifest = {
        "check": 45,
        "reading": "R4",
        "status": "INSUFFICIENT DATA",
        "reason": "Pilot README declares INELIGIBLE / INCOMPLETE; mandatory stop.",
        "source": str(source.relative_to(ROOT)),
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "source_heading": heading,
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "required_labelled_rounds": 150,
        "required_violations": 25,
        "labelled_rounds": None,
        "violations": None,
        "counts_note": "Not audited: ineligibility alone triggers stop.",
        "planned_lineage": {
            "fit_on": "DEV pilot rounds only",
            "evaluated_on": "held-out DEV episodes by fold",
            "benchmark_data": False,
            "evaluation_bank_episodes": False,
        },
        "actual_lineage": "Pilot README only; no fitting or evaluation.",
        "folds_run": 0,
        "per_fold_records": "per-fold.jsonl",
        "per_fold_sha256": hashlib.sha256(b"").hexdigest(),
        "probe_weights": [],
        "metrics": None,
        "models_loaded": 0,
        "gpu_used": False,
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print("Check 45: R4 — INSUFFICIENT DATA (pilot INELIGIBLE); no fitting.")


if __name__ == "__main__":
    main()
