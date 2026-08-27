# ruff: noqa: E402, I001
"""Frozen exact-match evaluation for Stencil toy tasks."""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from stencil import determinism as _determinism  # noqa: F401

import torch

from stencil.config import Config, canonical_json, load_config
from stencil.data import OPERAND_START, generate, rule_table
from stencil.model import StencilTransformer
from stencil.train import next_examples

TASK_D_BINS: tuple[tuple[str, int, int | None], ...] = (
    ("[0,64]", 0, 64),
    ("(64,128]", 64, 128),
    ("(128,252]", 128, 252),
    ("(252,512]", 252, 512),
    ("(512,1024]", 512, 1024),
    ("(1024,2048]", 1024, 2048),
    ("(2048,inf)", 2048, None),
)
TASK_D_MIN_BIN_SAMPLES = 200


@dataclass(frozen=True)
class ExactMatch:
    n_answers: int
    n_correct: int
    accuracy: float
    first_answer_correct: list[bool]


def eval_config(config: Config) -> Config:
    """Move only example streams to the registered frozen eval seed."""
    return replace(config, seed_data=config.seed_data + config.eval_seed_offset)


def _validate_score_inputs(
    logits: torch.Tensor, tokens: torch.Tensor, loss_mask: torch.Tensor
) -> None:
    if logits.ndim != 3 or logits.shape[:2] != tokens.shape:
        raise ValueError("logits and tokens have incompatible shapes")
    if tokens.shape != loss_mask.shape or loss_mask.dtype != torch.bool:
        raise ValueError("tokens and loss_mask have incompatible shapes")
    if torch.any(loss_mask[:, -1]):
        raise ValueError("last token cannot be an answer-decision position")
    per_sequence = loss_mask[:, :-1].sum(dim=1)
    if torch.any(per_sequence < 1):
        raise ValueError("every sequence must contain an answer-decision position")


def exact_match_from_logits(
    logits: torch.Tensor, tokens: torch.Tensor, loss_mask: torch.Tensor
) -> ExactMatch:
    """Pool exact token matches over causal answer-decision positions."""
    _validate_score_inputs(logits, tokens, loss_mask)
    decisions = loss_mask[:, :-1]
    predictions = logits[:, :-1].argmax(dim=-1)
    correctness = predictions.eq(tokens[:, 1:])
    selected = correctness[decisions]
    n_answers = selected.numel()
    if n_answers < 1:
        raise RuntimeError("exact-match selection was vacuous")
    first: list[bool] = []
    for row in range(tokens.shape[0]):
        positions = torch.nonzero(decisions[row], as_tuple=False).flatten()
        if positions.numel() < 1:
            raise RuntimeError("first-answer selection was vacuous")
        first.append(bool(correctness[row, positions[0]].item()))
    n_correct = int(selected.sum().item())
    return ExactMatch(
        n_answers=n_answers,
        n_correct=n_correct,
        accuracy=n_correct / n_answers,
        first_answer_correct=first,
    )


def cell_name(config: Config) -> str:
    if config.task == "a":
        return f"task_a/N={config.task_N}/k={config.task_k}"
    if config.task == "b":
        return f"task_b/R={config.task_R}/k={config.task_k}"
    if config.task == "m":
        return f"task_m/{config.task_placement}"
    if config.task == "d":
        return "task_d"
    raise ValueError("evaluation supports only tasks a, b, d, and m")


def task_d_eval_configs(
    config: Config,
    *,
    split: str,
    repo: str | Path = ".",
) -> dict[str, Config]:
    """Build the three paired Task D family configs at one frozen offset."""
    if config.task != "d":
        raise ValueError("Task D family evaluation requires task='d'")
    if split not in {"validation", "final"}:
        raise ValueError("Task D split must be validation or final")
    root = Path(repo).resolve()
    if split == "final" and not (root / "results" / "TASKD-FLEET-FROZEN").is_file():
        raise RuntimeError(
            "final Task D evaluation requires results/TASKD-FLEET-FROZEN"
        )
    offset = (
        config.task_d_validation_offset
        if split == "validation"
        else config.task_d_final_offset
    )
    # Evaluation schedules are keyed only by (family, offset, sequence index),
    # never by the training seed carried in the run config.
    common = dict(
        seed_data=0,
        task_d_schedule_offset=offset,
        task_d_sequence_index=0,
    )
    return {
        "id-control": replace(
            config,
            task_d_family="id-control",
            task_d_updates=12,
            task_d_gap_min=64,
            task_d_gap_max=320,
            **common,
        ),
        "drought": replace(
            config,
            task_d_family="drought",
            task_d_updates=3,
            task_d_gap_min=768,
            task_d_gap_max=1280,
            **common,
        ),
        "burst": replace(
            config,
            task_d_family="burst",
            task_d_updates=8,
            **common,
        ),
    }


def first_crossing_survival(
    bins: list[dict[str, Any]], *, min_samples: int = TASK_D_MIN_BIN_SAMPLES
) -> int | str | None:
    """Return the last consecutive >=90% bin, stopping at an NA or crossing."""
    survived: int | str | None = None
    for row in bins:
        denominator = int(row["denominator"])
        accuracy = row["accuracy"]
        if denominator < min_samples or accuracy is None or float(accuracy) < 0.9:
            break
        upper = row["upper"]
        survived = ">2048" if upper is None else int(upper)
    return survived


def _in_task_d_bin(distance: int, lower: int, upper: int | None) -> bool:
    if lower == 0:
        return 0 <= distance <= 64
    return distance > lower and (upper is None or distance <= upper)


def task_d_metrics(
    decisions: list[dict[str, Any]],
    *,
    n_sequences: int,
    injected_tokens: int,
    min_bin_samples: int = TASK_D_MIN_BIN_SAMPLES,
) -> dict[str, Any]:
    """Reduce frozen per-query Task D records into registered family metrics."""
    if n_sequences < 1 or not decisions:
        raise ValueError("Task D metrics require non-vacuous sequences and decisions")
    per_sequence: dict[int, list[bool]] = {}
    for decision in decisions:
        sequence = int(decision["sequence"])
        per_sequence.setdefault(sequence, []).append(bool(decision["correct"]))
    if set(per_sequence) != set(range(n_sequences)):
        raise ValueError("Task D decisions do not cover every sequence exactly")
    sequence_accuracies = [
        sum(values) / len(values) for _, values in sorted(per_sequence.items())
    ]

    bin_rows: list[dict[str, Any]] = []
    for label, lower, upper in TASK_D_BINS:
        selected = [
            row
            for row in decisions
            if _in_task_d_bin(int(row["distance"]), lower, upper)
        ]
        numerator = sum(bool(row["correct"]) for row in selected)
        denominator = len(selected)
        accuracy = numerator / denominator if denominator else None
        eligible = denominator >= min_bin_samples
        bin_rows.append(
            {
                "label": label,
                "lower": lower,
                "upper": upper,
                "numerator": numerator,
                "denominator": denominator,
                "accuracy": accuracy,
                "comparison_eligible": eligible,
                "comparison_accuracy": accuracy if eligible else None,
            }
        )

    global_rows = []
    for count in sorted({int(row["global_updates"]) for row in decisions}):
        selected = [row for row in decisions if int(row["global_updates"]) == count]
        numerator = sum(bool(row["correct"]) for row in selected)
        global_rows.append(
            {
                "updates": count,
                "numerator": numerator,
                "denominator": len(selected),
                "accuracy": numerator / len(selected),
            }
        )

    wrong = [row for row in decisions if not bool(row["correct"])]
    stale_matches = 0
    null_total = 0.0
    for row in wrong:
        active = int(row["active_answer"])
        stale = {int(value) for value in row["superseded_answers"]}
        stale.discard(active)
        stale_matches += int(int(row["prediction"]) in stale)
        null_total += len(stale) / 15
    if wrong:
        observed = stale_matches / len(wrong)
        null = null_total / len(wrong)
        excess = observed - null
    else:
        observed = null = excess = None

    tail_bins = [
        row for row in bin_rows if row["lower"] >= 512 and row["comparison_eligible"]
    ]
    tail_correct = sum(int(row["numerator"]) for row in tail_bins)
    tail_count = sum(int(row["denominator"]) for row in tail_bins)
    return {
        "sequence_weighted_exact_match": {
            "numerator": sum(sequence_accuracies),
            "denominator": n_sequences,
            "accuracy": sum(sequence_accuracies) / n_sequences,
        },
        "decision_axis_bins": bin_rows,
        "accuracy_by_global_update_count": global_rows,
        "first_crossing_survival": first_crossing_survival(
            bin_rows, min_samples=min_bin_samples
        ),
        "stale_slot_preference": {
            "n_wrong_answers": len(wrong),
            "n_stale_matches": stale_matches,
            "observed": observed,
            "null": null,
            "excess": excess,
        },
        "tail_over_512": {
            "numerator": tail_correct,
            "denominator": tail_count,
            "accuracy": tail_correct / tail_count if tail_count else None,
        },
        "injected_token_overhead": {
            "per_sequence": injected_tokens,
            "total": injected_tokens * n_sequences,
        },
    }


def _task_d_decisions(
    config: Config,
    metadata: list[dict[str, Any]],
    predictions: torch.Tensor,
    targets: torch.Tensor,
    *,
    sequence_start: int,
) -> list[dict[str, Any]]:
    rules = rule_table(config)
    records: list[dict[str, Any]] = []
    for row, details in enumerate(metadata):
        queries = sorted(
            details["queries"], key=lambda query: query["final_decision_position"]
        )
        if len(queries) != predictions.shape[1]:
            raise RuntimeError("Task D query metadata is not aligned with decisions")
        updates = details["updates"]
        for column, query in enumerate(queries):
            prior = [
                update
                for update in updates
                if update[0] < query["start"] and update[1] == query["slot"]
            ]
            if not prior:
                raise RuntimeError("Task D query has no prior slot update")
            active_update = prior[-1]
            superseded_rules = {update[2] for update in prior[:-1]}
            superseded_answers = [
                OPERAND_START + rules[rule - 1][query["x"]] for rule in superseded_rules
            ]
            prediction = int(predictions[row, column])
            target = int(targets[row, column])
            records.append(
                {
                    "sequence": sequence_start + row,
                    "schedule_id": list(details["schedule_id"]),
                    "correct": prediction == target,
                    "distance": query["start"] - active_update[0],
                    "global_updates": sum(
                        update[0] < query["start"] for update in updates
                    ),
                    "prediction": prediction,
                    "active_answer": target,
                    "superseded_answers": superseded_answers,
                }
            )
    return records


def _task_b_diagnostics(
    config: Config,
    metadata: list[dict[str, Any]],
    predictions: torch.Tensor,
    targets: torch.Tensor,
    decisions: torch.Tensor,
) -> tuple[int, int, list[float]]:
    rules = rule_table(config)
    stale_errors = 0
    wrong_answers = 0
    nulls: list[float] = []
    for row, details in enumerate(metadata):
        cues = details["cue_indices"]
        operands = details["operand_indices"]
        positions = torch.nonzero(decisions[row], as_tuple=False).flatten().tolist()
        if len(positions) != len(cues) or len(cues) != len(operands):
            raise RuntimeError("Task B metadata is not aligned with answer decisions")
        sequence_null = 0.0
        for segment, position in enumerate(positions):
            prediction = int(predictions[row, position])
            target = int(targets[row, position])
            operand = operands[segment]
            active_answer = rules[cues[segment]][operand]
            stale = {
                rules[prior][operand]
                for prior in cues[:segment]
                if prior != cues[segment]
            }
            stale.discard(active_answer)
            sequence_null += len(stale) / 15
            if prediction != target:
                wrong_answers += 1
                if prediction - OPERAND_START in stale:
                    stale_errors += 1
        nulls.append(sequence_null / len(positions))
    return stale_errors, wrong_answers, nulls


def _task_d_contender(config: Config) -> str:
    if config.task_d_reinsert == "every-128":
        return "reinsert128"
    if config.task_d_reinsert == "prequery":
        return "prequery"
    return config.variant


def _evaluate_task_d_family(
    model: StencilTransformer, config: Config
) -> dict[str, Any]:
    stream = generate(config)
    try:
        device = next(model.parameters()).device
    except StopIteration as error:
        raise ValueError("evaluation model has no parameters") from error
    decisions: list[dict[str, Any]] = []
    gap_redraws = 0
    gap_fallbacks = 0
    seen = 0
    model.eval()
    with torch.inference_mode():
        while seen < config.eval_examples:
            count = min(config.batch, config.eval_examples - seen)
            batch = next_examples(stream, count)
            tokens = batch.tokens.to(device)
            positions = batch.decision_positions.to(device)
            logits = model(
                tokens,
                decision_positions=positions,
                cue_positions=batch.cue_positions.to(device),
                cue_valid=batch.cue_valid.to(device),
                use_truncation=False,
            )
            predictions = logits.argmax(dim=-1).cpu()
            decisions.extend(
                _task_d_decisions(
                    config,
                    batch.metadata,
                    predictions,
                    batch.targets,
                    sequence_start=seen,
                )
            )
            gap_redraws += sum(int(row["gap_redraws"]) for row in batch.metadata)
            gap_fallbacks += sum(int(row["gap_fallbacks"]) for row in batch.metadata)
            seen += count
    if seen != config.eval_examples or len(decisions) != 16 * seen:
        raise RuntimeError("Task D evaluation sequence or decision count is not exact")
    overhead = {"none": 0, "every-128": 248, "prequery": 128}[
        str(config.task_d_reinsert)
    ]
    result = task_d_metrics(decisions, n_sequences=seen, injected_tokens=overhead)
    result.update(
        {
            "family": config.task_d_family,
            "schedule_offset": config.task_d_schedule_offset,
            "n_sequences": seen,
            "n_answers": len(decisions),
            "gap_redraws": gap_redraws,
            "gap_fallbacks": gap_fallbacks,
        }
    )
    return result


def merge_task_d_evaluations(
    existing: dict[str, Any] | None, result: dict[str, Any]
) -> dict[str, Any]:
    """Merge one sealed split into the single per-run eval.json document."""
    if result.get("cell") != "task_d" or result.get("split") not in {
        "validation",
        "final",
    }:
        raise ValueError("invalid Task D split result")
    split = str(result["split"])
    if existing is None:
        base = {
            key: result[key]
            for key in (
                "cell",
                "variant",
                "contender",
                "seed",
                "n_sequences",
                "n_answers",
            )
        }
        base["splits"] = {split: result}
        return base
    if existing.get("cell") != "task_d" or not isinstance(existing.get("splits"), dict):
        raise ValueError("existing eval.json is not a Task D split document")
    for key in ("variant", "contender", "seed"):
        if existing.get(key) != result.get(key):
            raise ValueError(f"Task D split identity differs at {key}")
    if split in existing["splits"]:
        raise RuntimeError(f"Task D {split} evaluation already exists")
    merged = dict(existing)
    merged["splits"] = dict(existing["splits"])
    merged["splits"][split] = result
    return merged


def evaluate_model(
    model: StencilTransformer,
    config: Config,
    *,
    task_d_split: str = "validation",
    repo: str | Path = ".",
) -> dict[str, Any]:
    """Evaluate exactly ``eval_examples`` fresh sequences at the final model."""
    if config.eval_examples < 1:
        raise ValueError("eval_examples must be positive")
    if config.precision != "fp32":
        raise ValueError("toy-phase evaluation requires fp32")
    if config.task == "d":
        family_configs = task_d_eval_configs(config, split=task_d_split, repo=repo)
        return {
            "cell": cell_name(config),
            "variant": config.variant,
            "contender": _task_d_contender(config),
            "seed": config.seed_train,
            "split": task_d_split,
            "eval_offset": (
                config.task_d_validation_offset
                if task_d_split == "validation"
                else config.task_d_final_offset
            ),
            "n_sequences": config.eval_examples,
            "n_answers": config.eval_examples * 16,
            "families": {
                family: _evaluate_task_d_family(model, family_config)
                for family, family_config in family_configs.items()
            },
        }
    frozen = eval_config(config)
    stream = generate(frozen)
    try:
        device = next(model.parameters()).device
    except StopIteration as error:
        raise ValueError("evaluation model has no parameters") from error
    n_answers = 0
    n_correct = 0
    first_answer_correct: list[bool] = []
    stale_errors = 0
    wrong_answers = 0
    stale_nulls: list[float] = []
    seen = 0
    model.eval()
    with torch.inference_mode():
        while seen < config.eval_examples:
            count = min(config.batch, config.eval_examples - seen)
            batch = next_examples(stream, count)
            tokens = batch.tokens.to(device)
            loss_mask = batch.loss_mask.to(device)
            logits = model(tokens, use_truncation=False)
            scored = exact_match_from_logits(logits, tokens, loss_mask)
            n_answers += scored.n_answers
            n_correct += scored.n_correct
            first_answer_correct.extend(scored.first_answer_correct)
            if config.task == "b":
                decisions = loss_mask[:, :-1]
                predictions = logits[:, :-1].argmax(dim=-1)
                diagnostics = _task_b_diagnostics(
                    frozen,
                    batch.metadata,
                    predictions,
                    tokens[:, 1:],
                    decisions,
                )
                stale_errors += diagnostics[0]
                wrong_answers += diagnostics[1]
                stale_nulls.extend(diagnostics[2])
            seen += count
    if seen != config.eval_examples or len(first_answer_correct) != seen:
        raise RuntimeError("evaluation sequence count is not exact")
    result: dict[str, Any] = {
        "cell": cell_name(config),
        "variant": config.variant,
        "seed": config.seed_data,
        "n_sequences": seen,
        "n_answers": n_answers,
        "accuracy": n_correct / n_answers,
        "n_correct": n_correct,
        "n_first_answers": seen,
        "n_first_correct": sum(first_answer_correct),
        "first_answer_correct": first_answer_correct,
    }
    if config.task == "b":
        result.update(
            {
                "n_wrong_answers": wrong_answers,
                "n_stale_rule_errors": stale_errors,
                "stale_rule_error_rate": (
                    stale_errors / wrong_answers if wrong_answers else None
                ),
                "stale_rule_analytic_null": sum(stale_nulls) / len(stale_nulls),
                "stale_rule_analytic_null_per_sequence": stale_nulls,
            }
        )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Evaluate a completed Task D run at a frozen split"
    )
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--split", choices=("validation", "final"), required=True)
    parser.add_argument("--repo", type=Path)
    args = parser.parse_args()
    run_dir = args.run_dir.resolve()
    root = args.repo.resolve() if args.repo else run_dir.parent.parent
    config = load_config(run_dir / "config.json")
    if config.task != "d":
        raise ValueError("the split evaluator supports Task D runs only")
    # Refuse an unsealed or duplicate final before loading the model.
    task_d_eval_configs(config, split=args.split, repo=root)
    eval_path = run_dir / "eval.json"
    existing = json.loads(eval_path.read_text(encoding="utf-8"))
    if args.split in existing.get("splits", {}):
        raise RuntimeError(f"Task D {args.split} evaluation already exists")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    checkpoint = torch.load(
        run_dir / "final.pt", map_location=device, weights_only=True
    )
    model = StencilTransformer(config).to(device)
    model.load_state_dict(checkpoint["model"])
    started = time.perf_counter()
    result = evaluate_model(model, config, task_d_split=args.split, repo=root)
    result["cost"] = {
        "train_wall_seconds": existing["splits"]["validation"]
        .get("cost", {})
        .get("train_wall_seconds"),
        "eval_wall_seconds": time.perf_counter() - started,
    }
    merged = merge_task_d_evaluations(existing, result)
    eval_path.write_bytes(canonical_json(merged) + b"\n")
    print(eval_path)


if __name__ == "__main__":
    main()
