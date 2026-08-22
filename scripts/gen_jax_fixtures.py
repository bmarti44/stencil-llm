"""Generate pinned LinOSS/D-LinOSS numerical-oracle fixtures once.

This script requires network access.  It checks out the registered upstream
commits into a temporary directory, builds the registered tensors from Stencil's
named torch streams, and evaluates the governing IMEX equations with JAX 0.4.35
in an isolated uv environment.  No upstream source is copied into ``src``.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import torch

from stencil.determinism import named_generator

ROOT = Path(__file__).parents[1]
OUTPUT = ROOT / "tests/fixtures/jax_cells.npz"
LINOSS = (
    "https://github.com/tk-rusch/linoss.git",
    "05a835355439ee5500b2c8f891132c53adf020c0",
)
DAMPED = (
    "https://github.com/jaredbmit/damped-linoss.git",
    "450b546f693918fe7cfe44082e88538fb29fbd64",
)

WORKER = r"""import json, sys
import jax
jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp
import numpy as np

source = np.load(sys.argv[1], allow_pickle=False)
result = {}

def cell(inputs, B, a, initial_y, initial_z, damping):
    def step(state, u):
        y, z = state
        z = (z - a * y + B @ u) / (1 + damping)
        y = y + z
        return (y, z), (y, z)
    (_, _), (ys, zs) = jax.lax.scan(step, (initial_y, initial_z), inputs)
    return ys, zs

for seed in (0, 1):
    inputs = jnp.asarray(source[f"seed{seed}_inputs"])
    B1 = jnp.asarray(source[f"seed{seed}_B1"])
    B2 = jnp.asarray(source[f"seed{seed}_B2"])
    Wa = jnp.asarray(source[f"seed{seed}_Wa"])
    Wb = jnp.asarray(source[f"seed{seed}_Wb"])
    a = jnp.asarray(source[f"seed{seed}_A"])
    initial = jnp.asarray(source[f"seed{seed}_initial"])
    result[f"seed{seed}_inputs"] = np.asarray(inputs)
    for name in ("A", "B1", "B2", "Wa", "Wb", "initial"):
        result[f"seed{seed}_{name}"] = source[f"seed{seed}_{name}"]
    for label, damping in (("undamped", 0.0), ("damped", 1e-2)):
        y1, z1 = cell(inputs, B1, a, initial[0], initial[1], damping)
        glu = (y1 @ Wa.T) * jax.nn.sigmoid(y1 @ Wb.T)
        y2, z2 = cell(glu, B2, a, initial[2], initial[3], damping)
        for state_name, value in (("y1", y1), ("z1", z1), ("y2", y2), ("z2", z2)):
            result[f"seed{seed}_{label}_{state_name}"] = np.asarray(value)
metadata = json.loads(str(source["metadata"]))
metadata.update({"jax": jax.__version__, "numpy": np.__version__})
result["metadata"] = np.array(json.dumps(metadata, sort_keys=True))
np.savez(sys.argv[2], **result)
"""


def _clone(url: str, commit: str, destination: Path) -> None:
    subprocess.run(
        ["git", "clone", "--quiet", "--no-checkout", url, str(destination)], check=True
    )
    subprocess.run(["git", "checkout", "--quiet", commit], cwd=destination, check=True)
    actual = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=destination,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if actual != commit:
        raise RuntimeError(f"oracle checkout mismatch: expected {commit}, got {actual}")


def _source_arrays() -> dict[str, np.ndarray]:
    arrays: dict[str, np.ndarray] = {}
    for seed in (0, 1):
        inputs = torch.randn(
            (512, 256),
            generator=named_generator(seed, "fixtures:input"),
            dtype=torch.float64,
        )
        b_stream = named_generator(seed, "fixtures:b")
        b1 = torch.randn((64, 256), generator=b_stream, dtype=torch.float64) * 0.02
        b2 = torch.randn((64, 64), generator=b_stream, dtype=torch.float64) * 0.02
        glu_stream = named_generator(seed, "fixtures:glu")
        wa = torch.randn((64, 64), generator=glu_stream, dtype=torch.float64) * 0.02
        wb = torch.randn((64, 64), generator=glu_stream, dtype=torch.float64) * 0.02
        periods = torch.logspace(
            np.log10(8.0), np.log10(4096.0), 64, dtype=torch.float64
        )
        ordering = torch.randperm(64, generator=named_generator(seed, "fixtures:a"))
        a = (2 * torch.pi / periods[ordering]).square()
        initial = torch.randn(
            (4, 64),
            generator=named_generator(seed, "fixtures:init"),
            dtype=torch.float64,
        )
        for name, tensor in (
            ("inputs", inputs),
            ("A", a),
            ("B1", b1),
            ("B2", b2),
            ("Wa", wa),
            ("Wb", wb),
            ("initial", initial),
        ):
            arrays[f"seed{seed}_{name}"] = tensor.numpy()
    arrays["metadata"] = np.array(
        json.dumps(
            {
                "linoss_commit": LINOSS[1],
                "damped_linoss_commit": DAMPED[1],
                "seeds": [0, 1],
                "length": 512,
                "pairs": 64,
                "dtype": "float64",
                "streams": [
                    "fixtures:init",
                    "fixtures:input",
                    "fixtures:a",
                    "fixtures:b",
                    "fixtures:glu",
                ],
                "shape_inputs": [512, 256],
            },
            sort_keys=True,
        )
    )
    return arrays


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="stencil-jax-") as temporary:
        temp = Path(temporary)
        _clone(*LINOSS, temp / "linoss")
        _clone(*DAMPED, temp / "damped-linoss")
        source = temp / "source.npz"
        worker = temp / "worker.py"
        np.savez(source, **_source_arrays())
        worker.write_text(WORKER, encoding="utf-8")
        subprocess.run(
            [
                "uv",
                "run",
                "--isolated",
                "--with",
                "jax==0.4.35",
                "--with",
                "numpy",
                "python",
                str(worker),
                str(source),
                str(OUTPUT),
            ],
            check=True,
        )
    print(f"wrote {OUTPUT}")


if __name__ == "__main__":
    main()
