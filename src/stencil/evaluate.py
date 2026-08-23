# ruff: noqa: E402, I001
"""Frozen exact-match evaluation for Stencil toy tasks."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any

from stencil import determinism as _determinism  # noqa: F401

import torch

from stencil.config import Config
from stencil.data import OPERAND_START, generate, rule_table
from stencil.model import StencilTransformer
from stencil.train import next_examples


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
    raise ValueError("evaluation supports only tasks a, b, and m")


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


def evaluate_model(model: StencilTransformer, config: Config) -> dict[str, Any]:
    """Evaluate exactly ``eval_examples`` fresh sequences at the final model."""
    if config.eval_examples < 1:
        raise ValueError("eval_examples must be positive")
    if config.precision != "fp32":
        raise ValueError("toy-phase evaluation requires fp32")
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
            logits = model(tokens)
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
