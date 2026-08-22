from pathlib import Path

import pytest

from stencil.config import load_config
from stencil.train import train_losses

CONFIG_PATH = Path(__file__).parents[1] / "configs" / "test_tiny.json"


@pytest.mark.determinism
def test_determinism_two_runs_bitwise() -> None:
    config = load_config(CONFIG_PATH)

    first = train_losses(config)
    second = train_losses(config)

    assert len(first) == len(second) == 200
    assert first == second
