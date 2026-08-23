"""Phase 3 training infrastructure tests."""

from __future__ import annotations

from dataclasses import replace

import pytest

from stencil.model import build_matched_configs
from stencil.train import train_model_losses


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
