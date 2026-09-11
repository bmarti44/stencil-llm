"""Audit saved held-out-2 records, without model loading or held-out input access.

V3 cells are descriptive slices of frozen author rationales/gold metadata,
identified after the single evaluation; they never feed calibration or selection.
"""

import json
from collections import Counter

import numpy as np

from scripts import evaluate_relations_heldout2 as ev
from scripts import train_relations as tr


def v3_memberships(row):
    why = row["why"].lower()
    return {
        "scoped_bare_suspension": "bare suspension" in why,
        "scoped_explicit_replacement": (
            row["old_rule"]["scope"] == "global" and row["label"] == "supersedes"
        ),
        "whole_global_withdrawal": (
            row["old_rule"]["scope"] == "global" and row["label"] == "cancels"
        ),
        "single_reply_exception": "single-reply exception" in why,
        "uncommitted_hedge": "hedged" in why or "tentative question" in why,
        "whole_task_closure_plus_global_admission": (
            row["label"] == "completes" and row["message_new_rule"] is True
        ),
        "whole_task_closure_without_admission": (
            row["label"] == "completes" and row["message_new_rule"] is False
        ),
        "subunit_closure": "sub-unit" in why or "subunit" in why,
        "inactive_or_modified_restoration": (
            "inactive target" in why or "modified restoration" in why
        ),
    }


def main():
    root = ev.MODEL
    manifest = json.loads((root / "manifest.json").read_text())
    metrics = json.loads((root / "metrics.json").read_text())
    policy = json.loads((root / "operating-point.json").read_text())["policy"]
    assert manifest["state"] == "complete"
    assert manifest["heldout_evaluation_count"] == 1
    assert manifest["heldout_inference_count"] == 1
    for name, expected in manifest["artifact_sha256"].items():
        assert ev.sha(root / name) == expected, name
    for name, expected in {
        **manifest["source_sha256"],
        **manifest["data_audit"]["input_sha256"],
    }.items():
        assert ev.sha(tr.ROOT / name) == expected, name
    records = [
        json.loads(line)
        for line in (root / "heldout2-records.jsonl").read_text().splitlines()
    ]
    assert len(records) == 357
    assert [r["index"] for r in records] == list(range(357))
    assert len({r["row"]["id"] for r in records}) == 357
    for record in records:
        assert record["model_input_sha256"] == tr.digest(tr.render_pair(record["row"]))
        assert record["gold"] == record["row"]["label"]
    rows = [r["row"] for r in records]
    logits = np.array([r["logits"] for r in records])
    overflow = np.array([r["overflow"] for r in records])
    operational, argmax, predictions, probs = ev.score_rows(
        rows, logits, overflow, policy
    )
    assert operational == metrics["heldout"]
    assert argmax == metrics["heldout_argmax"]
    assert np.array_equal(probs, np.array([r["probabilities"] for r in records]))
    assert [ev.op.LABELS[p] for p in predictions] == [r["prediction"] for r in records]
    assert [
        ev.op.LABELS[0 if r["overflow"] else int(np.argmax(r["logits"]))]
        for r in records
    ] == [r["argmax"] for r in records]
    # Independently count raw labels, without the scoring helper.
    counts = Counter((r["gold"], r["prediction"]) for r in records)
    confusion = [[counts[a, b] for b in ev.op.LABELS] for a in ev.op.LABELS]
    assert confusion == operational["confusion_gold_by_prediction"]
    assert sum(confusion[i][i] for i in range(5)) == 337
    assert sum(counts["none", k] for k in ev.op.LABELS[1:]) == 10
    cells = {}
    for name in v3_memberships(rows[0]):
        ii = np.array(
            [i for i, r in enumerate(rows) if v3_memberships(r)[name]], dtype=int
        )
        part = [rows[i] for i in ii]
        cells[name] = {
            "row_ids": [r["id"] for r in part],
            "gold_counts": dict(Counter(r["label"] for r in part)),
            "operating": tr.evaluate_predictions(part, predictions[ii]),
            "argmax": tr.evaluate_predictions(
                part,
                np.array(
                    [ev.op.LABELS.index(records[i]["argmax"]) for i in ii], dtype=int
                ),
            ),
            "error_ids": [
                rows[i]["id"]
                for i in ii
                if records[i]["gold"] != records[i]["prediction"]
            ],
        }
    result = {
        "interpretation": __doc__,
        "records_sha256": ev.sha(root / "heldout2-records.jsonl"),
        "slice_definition_source_sha256": ev.sha(
            tr.ROOT / "scripts/audit_relations_heldout2.py"
        ),
        "cells": cells,
        "admission_evaluated": False,
        "total_records": 357,
        "inference_passes": 1,
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
