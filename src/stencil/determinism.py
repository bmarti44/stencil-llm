# ruff: noqa: E402, I001
"""Shared deterministic execution and named random-number streams.

Every entrypoint must import this module before importing torch so the registered
cuBLAS workspace configuration is in force when torch initializes CUDA.
"""

import hashlib
import os
import re
import subprocess
from pathlib import Path

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


RESERVATIONS = Path.home() / ".gb10-gpu.reservations"


def _reserved_pids(path: Path | None = None) -> set[int]:
    """PIDs in the shared reservations file (one JSON object per line, ``"pid": N``)."""
    try:
        text = (RESERVATIONS if path is None else path).read_text()
    except OSError:
        return set()
    return {int(value) for value in re.findall(r'"pid"\s*:\s*(\d+)', text)}


def _ancestors(pid: int, limit: int = 64) -> set[int]:
    """Ancestor pids of ``pid`` from /proc (empty when unavailable)."""
    seen: set[int] = set()
    current = pid
    for _ in range(limit):
        try:
            stat = Path(f"/proc/{current}/stat").read_text()
        except OSError:
            break
        parent = int(stat.rsplit(")", 1)[1].split()[1])
        if parent <= 1 or parent in seen:
            break
        seen.add(parent)
        current = parent
    return seen


def _session_of(pid: int) -> int | None:
    """Session id of ``pid`` from /proc (None when unavailable); survives the
    reservation wrapper exiting before its GPU child."""
    try:
        stat = Path(f"/proc/{pid}/stat").read_text()
        return int(stat.rsplit(")", 1)[1].split()[3])
    except (OSError, IndexError, ValueError):
        return None


def assert_gpu_free_or_owned() -> None:
    """Fail closed unless the GPU is free, owned, or shared by reservation.

    ``STENCIL_GPU_OWNER`` is deliberately explicit: Unix user ownership is not
    enough because concurrent agents run under the same account. Shared mode
    (``STENCIL_GPU_SHARE=1``, plan section E, 2026-09-11) additionally tolerates
    foreign pids that are listed in the reservations file or in
    ``STENCIL_GPU_FOREIGN_PIDS``; unlisted pids still raise.
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
    if os.environ.get("STENCIL_GPU_SHARE") == "1":
        allowed = _reserved_pids() | {
            int(v)
            for v in re.findall(r"\d+", os.environ.get("STENCIL_GPU_FOREIGN_PIDS", ""))
        }
        if owner is not None:
            allowed.add(owner)
        unlisted = sorted(
            pid
            for pid in active
            if pid not in allowed
            and not (_ancestors(pid) & allowed)
            and _session_of(pid) not in allowed
        )
        if not unlisted:
            return
        raise RuntimeError(
            "GPU busy (shared mode): unreserved compute pid(s) "
            + ",".join(map(str, unlisted))
        )
    raise RuntimeError(
        "GPU busy: active compute pid(s) "
        + ",".join(map(str, sorted(active)))
        + f"; STENCIL_GPU_OWNER={owner_text or '<unset>'} does not exclusively match"
    )
