# ruff: noqa: E402, I001
"""Shared deterministic execution and named random-number streams.

Every entrypoint must import this module before importing torch so the registered
cuBLAS workspace configuration is in force when torch initializes CUDA.
"""

import hashlib
import os

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
