"""Phase 3 training infrastructure tests."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest
import torch
from torch.nn import functional as F

from stencil.data import generate
from stencil.model import StencilTransformer, build_matched_configs
from stencil.train import (
    _optimizer,
    masked_answer_loss,
    next_examples,
    task_d_answer_loss,
    task_d_training_stream,
    train_model,
    train_model_losses,
)


def _tiny_task_d_config():
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
        d_model=16,
        n_layers=1,
        n_heads=1,
        d_ff=32,
        window=4,
        batch=1,
        steps=2,
        warmup=1,
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


def test_task_d_loss_is_separate_target_and_nonvacuous() -> None:
    logits = torch.randn(2, 16, 64, generator=torch.Generator().manual_seed(3))
    targets = torch.full((2, 16), 41, dtype=torch.long)
    inputs = torch.zeros(2, 16, dtype=torch.long)

    actual = task_d_answer_loss(logits, targets, inputs, batch_size=2)
    expected = F.cross_entropy(logits.flatten(0, 1), targets.flatten())

    assert torch.equal(actual, expected)
    # Latin-square fixed points make target==input legitimate at ~1/16 of
    # positions; the guard fires only on degenerate wiring (>=50% equal) or
    # out-of-alphabet targets.
    with pytest.raises(AssertionError, match="mask wiring"):
        task_d_answer_loss(logits, targets, targets.clone(), batch_size=2)
    with pytest.raises(AssertionError, match="answer alphabet"):
        task_d_answer_loss(logits, torch.zeros_like(targets), inputs, batch_size=2)
    fixed_point_inputs = inputs.clone()
    fixed_point_inputs[0, 0] = 41  # one legitimate fixed point must NOT raise
    task_d_answer_loss(logits, targets, fixed_point_inputs, batch_size=2)
    with pytest.raises(AssertionError, match="32"):
        task_d_answer_loss(
            logits[:, :-1], targets[:, :-1], inputs[:, :-1], batch_size=2
        )


def test_task_d_training_stream_applies_curriculum_per_step_only() -> None:
    config = _tiny_task_d_config()
    stream = task_d_training_stream(config)
    first = [next(stream)[2] for _ in range(config.batch)]
    second = [next(stream)[2] for _ in range(config.batch)]

    assert {row["curriculum_step"] for row in first} == {0}
    assert {tuple(row["curriculum_bounds"]) for row in first} == {(32, 128)}
    assert {row["curriculum_step"] for row in second} == {1}
    assert {tuple(row["curriculum_bounds"]) for row in second} == {(32, 128)}
    assert all(len(row["updates"]) == 16 for row in first + second)


@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA graph requires CUDA")
@pytest.mark.parametrize("task", ["a", "d"])
def test_graph_step_bitwise_equals_eager(task: str) -> None:
    config = (
        replace(
            build_matched_configs()["b0_local"],
            batch=2,
            steps=3,
            warmup=1,
            task_N=8,
            context_len=12,
        )
        if task == "a"
        else _tiny_task_d_config()
    )

    eager_model, eager_losses = train_model(config, device="cuda")
    graph_model, graph_losses = train_model(config, device="cuda", use_cuda_graph=True)

    assert eager_losses == graph_losses
    for eager, graphed in zip(
        eager_model.parameters(), graph_model.parameters(), strict=True
    ):
        assert torch.equal(eager, graphed)


@pytest.mark.parametrize(
    ("device", "use_cuda_graph"),
    [
        ("cpu", False),
        pytest.param(
            "cuda",
            True,
            marks=pytest.mark.skipif(
                not torch.cuda.is_available(), reason="CUDA graph requires CUDA"
            ),
        ),
    ],
)
def test_prefetch_bitwise_equals_sync(
    tmp_path: Path, device: str, use_cuda_graph: bool
) -> None:
    config = replace(
        build_matched_configs()["b0_local"],
        batch=2,
        steps=4,
        warmup=1,
        task_N=8,
        context_len=12,
    )

    def train(prefetch: bool) -> tuple[StencilTransformer, list[float], bytes]:
        metrics_path = tmp_path / str(prefetch) / "metrics.jsonl"
        metrics_path.parent.mkdir()
        with metrics_path.open("w", encoding="utf-8") as handle:
            model, losses = train_model(
                config,
                device=device,
                use_cuda_graph=use_cuda_graph,
                use_prefetch=prefetch,
                on_step=lambda step, loss, lr: handle.write(
                    json.dumps({"step": step, "loss": loss, "lr": lr}) + "\n"
                ),
            )
        return model, losses, metrics_path.read_bytes()

    sync_model, sync_losses, sync_metrics = train(False)
    prefetch_model, prefetch_losses, prefetch_metrics = train(True)

    assert sync_losses == prefetch_losses
    for sync, prefetched in zip(
        sync_model.parameters(), prefetch_model.parameters(), strict=True
    ):
        assert torch.equal(sync, prefetched)
    assert sync_metrics == prefetch_metrics


@pytest.mark.determinism
@pytest.mark.parametrize(
    "config",
    [
        replace(build_matched_configs()["m1"], steps=50),
        _tiny_task_d_config(),
    ],
    ids=["task-a", "task-d"],
)
def test_train_two_runs_bitwise_short(config) -> None:
    """Run two short real trainings in process, including separate-target Task D."""

    first = train_model_losses(config, use_compiled_scan=True)
    second = train_model_losses(config, use_compiled_scan=True)

    assert len(first) == len(second) == config.steps
    assert first == second
    assert all(loss > 0.0 for loss in first)


def test_training_rejects_non_fp32() -> None:
    config = replace(build_matched_configs()["m1"], steps=1, precision="bf16")

    with pytest.raises(ValueError, match="fp32"):
        train_model_losses(config)
