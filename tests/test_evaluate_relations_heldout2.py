"""Synthetic-only checks: never open either real held-out dataset."""

import json

import numpy as np
import pytest

from scripts import evaluate_relations_heldout2 as ev
from scripts import train_relations as tr


def fixture_rows():
    rows = []
    for label in ("none", "supersedes", "cancels", "completes", "reinstates"):
        text = f"Synthetic {label} fixture."
        rows.append(
            tr.normalize_row(
                {
                    "old_rule": "Use triangles",
                    "scope": "global",
                    "status": "live",
                    "message": text,
                    "target_span": {"text": text, "start": 0, "end": len(text)},
                    "source": "fable:unit-fixture",
                    "role": "user",
                    "label": label,
                    "hard": label == "none",
                }
            )
        )
    return rows


def test_real_record_writer_and_policy_metrics():
    rows = fixture_rows()
    probs = np.array(
        [
            [0.1, 0.7, 0.1, 0.05, 0.05],
            [0.1, 0.7, 0.1, 0.05, 0.05],
            [0.02, 0.02, 0.92, 0.02, 0.02],
            [0.05, 0.05, 0.05, 0.8, 0.05],
            [0.02, 0.02, 0.02, 0.02, 0.92],
        ]
    )
    policy = {"kind": "per_class", "thresholds": dict.fromkeys(ev.op.LABELS[1:], 0.6)}
    overflow = np.array([False, False, False, True, False])
    logits = np.log(probs)
    report, argmax, pred, _ = ev.score_rows(rows, logits, overflow, policy)
    assert pred.tolist() == [1, 1, 2, 0, 4]  # .7 accepted, unlike historical .98
    assert report["accuracy"] == 0.6
    assert report["none_fp"]["numerator"] == 1
    assert report["hard_negatives"]["none_fp"]["denominator"] == 1
    assert report["overflow_abstentions"] == 1
    assert report["operating_point_metrics"]["correct_positive_recall"] == 0.75
    records = ev.make_records(rows, logits, overflow, policy)
    assert len(records) == 5
    for r in records:
        assert set(r) == {
            "index",
            "row",
            "model_input_sha256",
            "logits",
            "probabilities",
            "gold",
            "prediction",
            "argmax",
            "overflow",
        }
    replay = [json.loads(json.dumps(r)) for r in records]
    replay_report = ev.score_rows(
        [r["row"] for r in replay],
        np.array([r["logits"] for r in replay]),
        np.array([r["overflow"] for r in replay]),
        policy,
    )
    assert replay_report[0] == report and replay_report[1] == argmax
    margin = {"kind": "margin", "margin": 0.7}
    assert ev.score_rows(rows, logits, overflow, margin)[2].tolist() == [0, 0, 2, 0, 4]


def test_durable_one_shot_guard(tmp_path):
    manifest = {
        "state": "development_complete_frozen",
        "recipe": {"seed": 0},
        "heldout_evaluation_count": 0,
        "budget": {"completed_epochs": 3},
    }
    for key, value in [
        ("recipe", {"seed": 1}),
        ("heldout_evaluation_count", 1),
        ("budget", {"completed_epochs": 2}),
        ("state", "complete"),
    ]:
        with pytest.raises(ValueError):
            ev.claim_once(tmp_path, dict(manifest, **{key: value}))
    assert not list(tmp_path.iterdir())
    ev.claim_once(tmp_path, manifest)
    assert json.loads((tmp_path / "heldout2-started.json").read_text())["started_utc"]
    with pytest.raises(FileExistsError):
        ev.claim_once(tmp_path, manifest)
