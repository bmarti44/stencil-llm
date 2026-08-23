"""Generate pinned LinOSS/D-LinOSS numerical-oracle fixtures once.

This script requires network access.  It checks out the registered upstream
commits into a temporary directory, builds the registered tensors from Stencil's
named torch streams, and executes the pinned upstream IMEX recurrences with JAX
0.4.35 in an isolated uv environment.  No upstream source is copied into ``src``.
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
from pathlib import Path
from types import SimpleNamespace

import jax
jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp
import numpy as np

source = np.load(sys.argv[1], allow_pickle=False)
linoss_checkout = Path(sys.argv[3])
damped_checkout = Path(sys.argv[4])

# Execute code from the verified pinned checkouts, not a local transcription.
sys.path.insert(0, str(linoss_checkout))
from models.LinOSS import apply_linoss_imex

sys.path.insert(0, str(damped_checkout / "src"))
from damped_linoss.models.LinOSS import DampedIMEX1Layer

result = {}

REGISTERED_EQUATIONS = '''Stencil PLAN Section 5.2 (state order z,y):
z[k+1] = (z[k] + dt*(-A*y[k] + B@u[k])) / (1 + dt*G)
y[k+1] = y[k] + dt*z[k+1]'''
UPSTREAM_UNDAMPED_EQUATIONS = '''tk-rusch/linoss apply_linoss_imex (state order z,y):
z[k+1] = z[k] - dt*A*y[k] + dt*B@u[k]
y[k+1] = y[k] + dt*z[k+1]'''
UPSTREAM_DAMPED_EQUATIONS = (
    "jaredbmit/damped-linoss DampedIMEX1Layer (state order z,y):\n"
    "z[k+1] = (z[k] - dt*A*y[k] + dt*B@u[k]) / (1 + dt*G)\n"
    "y[k+1] = y[k] + dt*z[k+1]"
)


def registered_zero_initial(inputs, B, a, damping, dt=1.0):
    def step(state, u):
        y, z = state
        z = (z + dt * (-a * y + B @ u)) / (1 + dt * damping)
        y = y + dt * z
        return (y, z), (y, z)

    initial = (jnp.zeros_like(a), jnp.zeros_like(a))
    (_, _), (ys, zs) = jax.lax.scan(step, initial, inputs)
    return ys, zs


def upstream_undamped_zero_initial(inputs, B, a, dt=1.0):
    steps = jnp.full_like(a, dt)
    identity_readout = jnp.eye(a.shape[0], dtype=jnp.complex128)
    ys = apply_linoss_imex(
        a,
        B.astype(jnp.complex128),
        identity_readout,
        inputs,
        steps,
    )
    # Exact update identity, not a finite-difference approximation:
    # y[k+1] = y[k] + dt*z[k+1], with the upstream zero y[0].
    previous = jnp.concatenate((jnp.zeros_like(ys[:1]), ys[:-1]), axis=0)
    return ys, (ys - previous) / steps


def upstream_damped_zero_initial(inputs, B, a, damping, dt=1.0):
    steps = jnp.full_like(a, dt)
    projected = jax.vmap(lambda u: B @ u)(inputs).astype(jnp.complex128)
    layer = SimpleNamespace(state_dim=a.shape[0])
    ys = DampedIMEX1Layer._recurrence(layer, a, damping, steps, projected).real
    # Exact update identity, not a finite-difference approximation:
    # y[k+1] = y[k] + dt*z[k+1], with the upstream zero y[0].
    previous = jnp.concatenate((jnp.zeros_like(ys[:1]), ys[:-1]), axis=0)
    return ys, (ys - previous) / steps


def fail_discrepancy(upstream_equations, upstream, registered):
    errors = [
        float(jnp.max(jnp.abs(left - right)))
        for left, right in zip(upstream, registered)
    ]
    print("MATERIAL UPSTREAM/REGISTERED EQUATION DISCREPANCY", file=sys.stderr)
    print(upstream_equations, file=sys.stderr)
    print("--- versus ---", file=sys.stderr)
    print(REGISTERED_EQUATIONS, file=sys.stderr)
    print(f"max_abs_error(y,z)={errors}", file=sys.stderr)
    raise SystemExit(2)


def verify_upstream_equations():
    inputs = jnp.array([[0.3, -0.2], [0.7, 0.5], [-0.4, 0.9]], dtype=jnp.float64)
    B = jnp.array([[0.2, -0.6], [0.8, 0.1]], dtype=jnp.float64)
    a = jnp.array([0.17, 0.43], dtype=jnp.float64)
    for damping, upstream_equations, upstream in (
        (
            jnp.zeros_like(a),
            UPSTREAM_UNDAMPED_EQUATIONS,
            upstream_undamped_zero_initial(inputs, B, a),
        ),
        (
            jnp.array([0.01, 0.03], dtype=jnp.float64),
            UPSTREAM_DAMPED_EQUATIONS,
            upstream_damped_zero_initial(
                inputs,
                B,
                a,
                jnp.array([0.01, 0.03], dtype=jnp.float64),
            ),
        ),
    ):
        registered = registered_zero_initial(inputs, B, a, damping)
        if not all(
            bool(jnp.allclose(left, right, rtol=1e-12, atol=1e-12))
            for left, right in zip(upstream, registered)
        ):
            fail_discrepancy(upstream_equations, upstream, registered)


verify_upstream_equations()

for seed in (0, 1):
    inputs = jnp.asarray(source[f"seed{seed}_inputs"])
    B1 = jnp.asarray(source[f"seed{seed}_B1"])
    B2 = jnp.asarray(source[f"seed{seed}_B2"])
    Wa = jnp.asarray(source[f"seed{seed}_Wa"])
    Wb = jnp.asarray(source[f"seed{seed}_Wb"])
    a = jnp.asarray(source[f"seed{seed}_A"])
    result[f"seed{seed}_inputs"] = np.asarray(inputs)
    for name in ("A", "B1", "B2", "Wa", "Wb", "initial"):
        result[f"seed{seed}_{name}"] = source[f"seed{seed}_{name}"]
    for label, damping in (("undamped", 0.0), ("damped", 1e-2)):
        damping_vector = jnp.full_like(a, damping)
        if damping == 0:
            y1, z1 = upstream_undamped_zero_initial(inputs, B1, a)
        else:
            y1, z1 = upstream_damped_zero_initial(
                inputs, B1, a, damping_vector
            )
        glu = (y1 @ Wa.T) * jax.nn.sigmoid(y1 @ Wb.T)
        if damping == 0:
            y2, z2 = upstream_undamped_zero_initial(glu, B2, a)
        else:
            y2, z2 = upstream_damped_zero_initial(glu, B2, a, damping_vector)
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
        initial = torch.zeros((4, 64), dtype=torch.float64)
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
                    "fixtures:input",
                    "fixtures:a",
                    "fixtures:b",
                    "fixtures:glu",
                ],
                "initial_state": "zeros",
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
                "equinox==0.11.10",
                "--with",
                "sympy",
                "--with",
                "numpy",
                "python",
                str(worker),
                str(source),
                str(OUTPUT),
                str(temp / "linoss"),
                str(temp / "damped-linoss"),
            ],
            check=True,
        )
    print(f"wrote {OUTPUT}")


if __name__ == "__main__":
    main()
