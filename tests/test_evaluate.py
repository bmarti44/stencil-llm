"""Frozen Section 6 evaluation protocol tests."""

from __future__ import annotations

from dataclasses import replace

import pytest
import torch

from stencil.data import generate, rule_table, task_d
from stencil.evaluate import (
    _task_d_decisions,
    eval_config,
    exact_match_from_logits,
    first_crossing_survival,
    merge_task_d_evaluations,
    task_d_eval_configs,
    task_d_metrics,
)
from stencil.model import build_matched_configs
from stencil.train import next_examples


def test_eval_exact_match_correctness() -> None:
    """Score 3 nonempty decisions with exactly 2 correct predictions."""
    tokens = torch.tensor([[1, 4, 2, 3], [2, 1, 5, 0]])
    loss_mask = torch.tensor([[True, False, True, False], [False, True, False, False]])
    logits = torch.full((2, 4, 6), -10.0)
    logits[0, 0, 4] = 10.0  # correct: predicts tokens[0, 1]
    logits[0, 2, 0] = 10.0  # wrong: target tokens[0, 3] == 3
    logits[1, 1, 5] = 10.0  # correct: predicts tokens[1, 2]

    scored = exact_match_from_logits(logits, tokens, loss_mask)

    assert scored.n_answers == 3
    assert scored.n_correct == 2
    assert scored.accuracy == pytest.approx(2 / 3)
    assert scored.first_answer_correct == [True, True]


def test_eval_uses_eval_stream() -> None:
    """Eval examples differ from train while seed_rules keeps tables equal."""
    train_config = replace(build_matched_configs()["m1"], task_N=128, context_len=132)
    frozen_eval_config = eval_config(train_config)
    train_tokens = next(generate(train_config))[0]
    eval_tokens = next(generate(frozen_eval_config))[0]

    assert frozen_eval_config.seed_data == (
        train_config.seed_data + train_config.eval_seed_offset
    )
    assert not torch.equal(train_tokens, eval_tokens)
    assert rule_table(train_config) == rule_table(frozen_eval_config)
    assert train_config.seed_rules == frozen_eval_config.seed_rules == 0


def test_eval_rejects_vacuous_answer_mask() -> None:
    tokens = torch.tensor([[1, 2]])
    logits = torch.zeros(1, 2, 3)
    loss_mask = torch.zeros(1, 2, dtype=torch.bool)

    with pytest.raises(ValueError, match="answer"):
        exact_match_from_logits(logits, tokens, loss_mask)


def _task_d_config():
    return replace(
        build_matched_configs()["b0_local"],
        task="d",
        task_N=None,
        task_k=8,
        context_len=4096,
        task_d_slots=4,
        task_d_core_len=3848,
        task_d_updates=12,
        task_d_queries=16,
        task_d_family="train",
        task_d_reinsert="none",
        task_d_gap_min=64,
        task_d_gap_max=320,
        task_d_burst_start_min=64,
        task_d_burst_start_max=512,
        task_d_burst_intra_min=8,
        task_d_burst_intra_max=32,
        task_d_burst_inter_min=640,
        task_d_burst_inter_max=1200,
        task_d_curriculum_start=8000,
        task_d_curriculum_end=12000,
        task_d_curriculum_gap_min=32,
        task_d_curriculum_gap_max=128,
        task_d_schedule_offset=0,
        task_d_sequence_index=0,
    )


def test_task_d_metric_miniature_stale_null_and_tail() -> None:
    decisions = [
        dict(
            sequence=0,
            correct=True,
            distance=32,
            global_updates=4,
            prediction=40,
            active_answer=40,
            superseded_answers=[],
        ),
        dict(
            sequence=0,
            correct=False,
            distance=100,
            global_updates=5,
            prediction=41,
            active_answer=42,
            superseded_answers=[41, 41, 42],
        ),
        dict(
            sequence=1,
            correct=False,
            distance=300,
            global_updates=7,
            prediction=50,
            active_answer=44,
            superseded_answers=[45, 46],
        ),
        dict(
            sequence=1,
            correct=True,
            distance=600,
            global_updates=9,
            prediction=47,
            active_answer=47,
            superseded_answers=[48],
        ),
    ]

    metrics = task_d_metrics(
        decisions, n_sequences=2, injected_tokens=248, min_bin_samples=1
    )

    assert metrics["sequence_weighted_exact_match"] == {
        "numerator": 1.0,
        "denominator": 2,
        "accuracy": 0.5,
    }
    assert [
        (row["numerator"], row["denominator"]) for row in metrics["decision_axis_bins"]
    ] == [(1, 1), (0, 1), (0, 0), (0, 1), (1, 1), (0, 0), (0, 0)]
    assert [
        (row["updates"], row["numerator"], row["denominator"])
        for row in metrics["accuracy_by_global_update_count"]
    ] == [(4, 1, 1), (5, 0, 1), (7, 0, 1), (9, 1, 1)]
    assert metrics["first_crossing_survival"] == 64
    assert metrics["stale_slot_preference"] == {
        "n_wrong_answers": 2,
        "n_stale_matches": 1,
        "observed": 0.5,
        "null": pytest.approx(0.1),
        "excess": pytest.approx(0.4),
    }
    assert metrics["tail_over_512"] == {
        "numerator": 1,
        "denominator": 1,
        "accuracy": 1.0,
    }
    assert metrics["injected_token_overhead"] == {
        "per_sequence": 248,
        "total": 496,
    }


def test_task_d_stale_metric_is_na_without_wrong_answers() -> None:
    metrics = task_d_metrics(
        [
            dict(
                sequence=0,
                correct=True,
                distance=20,
                global_updates=4,
                prediction=40,
                active_answer=40,
                superseded_answers=[],
            )
        ],
        n_sequences=1,
        injected_tokens=0,
    )
    assert metrics["stale_slot_preference"] == {
        "n_wrong_answers": 0,
        "n_stale_matches": 0,
        "observed": None,
        "null": None,
        "excess": None,
    }


def test_task_d_survival_na_caps_at_prior_bin() -> None:
    rows = [
        {"upper": 64, "denominator": 250, "accuracy": 0.95},
        {"upper": 128, "denominator": 199, "accuracy": 1.0},
        {"upper": 252, "denominator": 500, "accuracy": 1.0},
    ]
    assert first_crossing_survival(rows) == 64
    rows[1] = {"upper": 128, "denominator": 250, "accuracy": 0.89}
    assert first_crossing_survival(rows) == 64
    rows[0] = {"upper": 64, "denominator": 0, "accuracy": None}
    assert first_crossing_survival(rows) is None


def test_task_d_final_eval_refuses_without_fleet_freeze(tmp_path) -> None:
    with pytest.raises(RuntimeError, match="TASKD-FLEET-FROZEN"):
        task_d_eval_configs(_task_d_config(), split="final", repo=tmp_path)

    marker = tmp_path / "results" / "TASKD-FLEET-FROZEN"
    marker.parent.mkdir()
    marker.touch()
    configs = task_d_eval_configs(
        replace(_task_d_config(), seed_data=2), split="final", repo=tmp_path
    )
    assert set(configs) == {"id-control", "drought", "burst"}
    assert all(
        config.task_d_schedule_offset == config.task_d_final_offset
        for config in configs.values()
    )
    assert {config.seed_data for config in configs.values()} == {0}


def test_task_d_decisions_use_separate_targets_and_core_coordinates() -> None:
    config = _task_d_config()
    batch = next_examples(task_d(config), 1)
    records = _task_d_decisions(
        config,
        batch.metadata,
        batch.targets.clone(),
        batch.targets,
        sequence_start=0,
    )

    assert len(records) == 16
    assert all(record["correct"] for record in records)
    assert all(record["distance"] >= 0 for record in records)
    assert all(record["global_updates"] >= 4 for record in records)


def test_task_d_eval_document_merges_each_split_once() -> None:
    base = {
        "cell": "task_d",
        "variant": "m1",
        "contender": "m1",
        "seed": 0,
        "n_sequences": 10_000,
        "n_answers": 160_000,
        "split": "validation",
        "families": {},
    }
    document = merge_task_d_evaluations(None, base)
    final = {**base, "split": "final"}
    document = merge_task_d_evaluations(document, final)

    assert set(document["splits"]) == {"validation", "final"}
    with pytest.raises(RuntimeError, match="already exists"):
        merge_task_d_evaluations(document, final)
