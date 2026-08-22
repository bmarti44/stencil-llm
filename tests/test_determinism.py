import json
import os
import subprocess
import sys
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
    assert first[0] != first[-1]


def test_determinism_forces_registered_cublas_value_in_fresh_process() -> None:
    env = os.environ.copy()
    env["CUBLAS_WORKSPACE_CONFIG"] = ":16:8"
    probe = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import json, os; "
                "import stencil.determinism as determinism; "
                "print(json.dumps([os.environ['CUBLAS_WORKSPACE_CONFIG'], "
                "determinism.torch.are_deterministic_algorithms_enabled()]))"
            ),
        ],
        check=True,
        capture_output=True,
        env=env,
        text=True,
    )

    assert json.loads(probe.stdout) == [":4096:8", True]
