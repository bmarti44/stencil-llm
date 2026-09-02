# ruff: noqa: E402, I001
"""Shared deterministic execution and named random-number streams.

Every entrypoint must import this module before importing torch so the registered
cuBLAS workspace configuration is in force when torch initializes CUDA.
"""

import hashlib
import os
import re
import subprocess

os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"

import torch


torch.use_deterministic_algorithms(True)


def stream_seed(seed: int, name: str) -> int:
    """Derive a registered 63-bit stream seed from an experiment seed."""
    digest = hashlib.sha256(f"{seed}:{name}".encode()).digest()
    return int.from_bytes(digest[:8], "big") >> 1


def named_generator(seed: int, name: str, device: str = "cpu") -> torch.Generator:
    """Return a fresh generator at the start of a registered named stream."""
    generator = torch.Generator(device=device)
    generator.manual_seed(stream_seed(seed, name))
    return generator


def assert_gpu_free_or_owned() -> None:
    """Fail closed unless the GPU is free or its sole app is the declared owner.

    ``STENCIL_GPU_OWNER`` is deliberately explicit: Unix user ownership is not
    enough because concurrent agents run under the same account.
    """
    result = subprocess.run(
        ["nvidia-smi", "--query-compute-apps=pid", "--format=csv,noheader"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        raise RuntimeError(
            f"nvidia-smi compute-app query failed ({result.returncode}): "
            f"{result.stderr.strip()}"
        )
    active = {int(value) for value in re.findall(r"\d+", result.stdout)}
    if not active:
        return
    owner_text = os.environ.get("STENCIL_GPU_OWNER", "")
    owner = int(owner_text) if owner_text.isdigit() else None
    if owner is not None and active == {owner}:
        return
    raise RuntimeError(
        "GPU busy: active compute pid(s) " + ",".join(map(str, sorted(active)))
        + f"; STENCIL_GPU_OWNER={owner_text or '<unset>'} does not exclusively match"
    )
