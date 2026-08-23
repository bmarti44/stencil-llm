"""Frozen Section 6 evaluation protocol tests."""

from __future__ import annotations

from dataclasses import replace

import pytest
import torch

from stencil.data import generate, rule_table
from stencil.evaluate import eval_config, exact_match_from_logits
from stencil.model import build_matched_configs


def test_eval_exact_match_correctness() -> None:
    """Score 3 nonempty decisions with exactly 2 correct predictions."""
    tokens = torch.tensor([[1, 4, 2, 3], [2, 1, 5, 0]])
    loss_mask = torch.tensor(
        [[True, False, True, False], [False, True, False, False]]
    )
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
    train_config = replace(
        build_matched_configs()["m1"], task_N=128, context_len=132
    )
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
