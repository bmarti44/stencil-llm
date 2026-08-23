"""Phase 3 training infrastructure tests."""

from __future__ import annotations

from dataclasses import replace

import pytest
import torch
from torch.nn import functional as F

from stencil.data import generate
from stencil.model import StencilTransformer, build_matched_configs
from stencil.train import (
    _optimizer,
    masked_answer_loss,
    next_examples,
    train_model,
    train_model_losses,
)


def test_adamw_uses_foreach() -> None:
    config = build_matched_configs()["b0_local"]
    optimizer = _optimizer(StencilTransformer(config), config)

    assert optimizer.defaults["foreach"] is True
    assert optimizer.defaults["fused"] is False


def test_static_decision_loss_and_selected_head_are_bitwise() -> None:
    config = replace(
        build_matched_configs()["b0_local"],
        batch=2,
        task_N=8,
        context_len=12,
    )
    batch = next_examples(generate(config), config.batch)
    model = StencilTransformer(config)

    full_logits = model(batch.tokens)
    rows = torch.arange(config.batch)[:, None]
    oracle_logits = full_logits[rows, batch.decision_positions]
    oracle_targets = batch.tokens[rows, batch.decision_positions + 1]
    decisions = batch.loss_mask[:, :-1]
    oracle_loss = F.cross_entropy(
        full_logits[:, :-1][decisions], batch.tokens[:, 1:][decisions]
    )

    selected_logits = model(
        batch.tokens,
        decision_positions=batch.decision_positions,
    )
    loss = masked_answer_loss(selected_logits, batch.targets)

    assert torch.equal(batch.targets, oracle_targets)
    assert torch.equal(selected_logits, oracle_logits)
    assert torch.equal(loss, oracle_loss)
    hidden = torch.randn(2, 12, config.d_model, requires_grad=True)
    model._project_logits(hidden, batch.decision_positions).sum().backward()
    hidden_grad = hidden.grad
    assert hidden_grad is not None
    selected = torch.zeros(hidden_grad.shape[:2], dtype=torch.bool)
    selected.scatter_(1, batch.decision_positions, True)
    assert torch.count_nonzero(hidden_grad[selected]) > 0
    assert torch.count_nonzero(hidden_grad[~selected]) == 0


@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA graph requires CUDA")
def test_graph_step_bitwise_equals_eager() -> None:
    config = replace(
        build_matched_configs()["b0_local"],
        batch=2,
        steps=3,
        warmup=1,
        task_N=8,
        context_len=12,
    )

    eager_model, eager_losses = train_model(config, device="cuda")
    graph_model, graph_losses = train_model(
        config, device="cuda", use_cuda_graph=True
    )

    assert eager_losses == graph_losses
    for eager, graphed in zip(
        eager_model.parameters(), graph_model.parameters(), strict=True
    ):
        assert torch.equal(eager, graphed)


@pytest.mark.determinism
def test_train_two_runs_bitwise_short() -> None:
    """Run two 50-step real M1 Task-A (2048,8) trainings in process."""
    config = replace(build_matched_configs()["m1"], steps=50)

    first = train_model_losses(config)
    second = train_model_losses(config)

    assert len(first) == len(second) == 50
    assert first == second
    assert all(loss > 0.0 for loss in first)


def test_training_rejects_non_fp32() -> None:
    config = replace(build_matched_configs()["m1"], steps=1, precision="bf16")

    with pytest.raises(ValueError, match="fp32"):
        train_model_losses(config)
