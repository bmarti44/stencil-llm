"""Flat experiment configuration and canonical identity helpers."""

from __future__ import annotations

import dataclasses
import hashlib
import json
import os
import stat
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Config:
    seed_data: int
    seed_init: int
    seed_train: int
    variant: str
    d_model: int
    n_layers: int
    n_heads: int
    d_ff: int
    window: int
    vocab: int
    context_len: int
    rope_theta: float
    osc_pairs: int | None
    osc_cells: int | None
    period_min: float | None
    period_max: float | None
    damping_learnable: bool | None
    task: str
    seed_rules: int
    task_N: int | None
    task_k: int | None
    task_R: int | None
    task_delay_min: int | None
    task_delay_max: int | None
    task_P: int | None
    task_queries: int | None
    task_placement: str | None
    lr: float
    lr_min: float
    warmup: int
    steps: int
    batch: int
    clip: float
    adam_beta1: float
    adam_beta2: float
    adam_eps: float
    weight_decay: float
    eval_examples: int = 10_000
    eval_seed_offset: int = 1_000_000
    precision: str = "fp32"
    task_d_slots: int | None = None
    task_d_core_len: int | None = None
    task_d_updates: int | None = None
    task_d_queries: int | None = None
    task_d_family: str | None = None
    task_d_reinsert: str | None = None
    task_d_gap_min: int | None = None
    task_d_gap_max: int | None = None
    task_d_burst_start_min: int | None = None
    task_d_burst_start_max: int | None = None
    task_d_burst_intra_min: int | None = None
    task_d_burst_intra_max: int | None = None
    task_d_burst_inter_min: int | None = None
    task_d_burst_inter_max: int | None = None
    task_d_curriculum_start: int | None = None
    task_d_curriculum_end: int | None = None
    task_d_curriculum_gap_min: int | None = None
    task_d_curriculum_gap_max: int | None = None
    task_d_schedule_offset: int | None = None
    task_d_sequence_index: int | None = None

    def as_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)

    @property
    def task_d_validation_offset(self) -> int:
        return self.eval_seed_offset

    @property
    def task_d_final_offset(self) -> int:
        return self.eval_seed_offset * 2 + 1


def canonical_json(value: Any) -> bytes:
    """Encode JSON with sorted keys, compact separators, and Python float repr."""
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def config_hash(config: Config | dict[str, Any]) -> str:
    value = config.as_dict() if isinstance(config, Config) else config
    return hashlib.sha256(canonical_json(value)).hexdigest()


def load_config(path: str | Path) -> Config:
    with Path(path).open(encoding="utf-8") as handle:
        raw = json.load(handle)
    if not isinstance(raw, dict):
        raise ValueError("config must be a JSON object")

    fields = {field.name for field in dataclasses.fields(Config)}
    unknown = set(raw) - fields
    if unknown:
        raise ValueError(f"unknown config fields: {sorted(unknown)}")
    try:
        config = Config(**raw)
    except TypeError as error:
        raise ValueError(f"invalid config fields: {error}") from error
    _validate(config)
    return config


def _validate(config: Config) -> None:
    variants = {
        "b0_full", "b0_local", "b1", "b2", "m1", "m1b", "b3", "b3k", "b4"
    }
    tasks = {"a", "b", "d", "m", "copy"}
    if config.variant not in variants:
        raise ValueError(f"invalid variant: {config.variant}")
    if config.task not in tasks:
        raise ValueError(f"invalid task: {config.task}")
    if config.precision not in {"fp32", "bf16"}:
        raise ValueError(f"invalid precision: {config.precision}")

    oscillatory = config.variant in {"m1", "m1b"}
    osc_fields = (
        config.osc_pairs,
        config.osc_cells,
        config.period_min,
        config.period_max,
        config.damping_learnable,
    )
    if oscillatory:
        if any(value is None for value in osc_fields):
            raise ValueError(
                "all oscillator fields are required for oscillatory variants"
            )
        if config.damping_learnable != (config.variant == "m1b"):
            raise ValueError("damping_learnable is inconsistent with variant")
        longest_delay = _longest_delay(config)
        if config.period_max is None or config.period_max < 2 * longest_delay:
            raise ValueError("period_max must be at least twice the longest task delay")
    elif any(value is not None for value in osc_fields):
        raise ValueError("oscillator fields must be null for non-oscillatory variants")

    required_by_task = {
        "a": {"task_N", "task_k"},
        "b": {"task_k", "task_R", "task_delay_min", "task_delay_max"},
        "d": {
            "task_k",
            "task_d_slots",
            "task_d_core_len",
            "task_d_updates",
            "task_d_queries",
            "task_d_family",
            "task_d_reinsert",
            "task_d_gap_min",
            "task_d_gap_max",
            "task_d_burst_start_min",
            "task_d_burst_start_max",
            "task_d_burst_intra_min",
            "task_d_burst_intra_max",
            "task_d_burst_inter_min",
            "task_d_burst_inter_max",
            "task_d_curriculum_start",
            "task_d_curriculum_end",
            "task_d_curriculum_gap_min",
            "task_d_curriculum_gap_max",
            "task_d_schedule_offset",
            "task_d_sequence_index",
        },
        "m": {"task_P", "task_queries", "task_placement"},
        "copy": set(),
    }
    task_fields = {
        "task_N",
        "task_k",
        "task_R",
        "task_delay_min",
        "task_delay_max",
        "task_P",
        "task_queries",
        "task_placement",
        "task_d_slots",
        "task_d_core_len",
        "task_d_updates",
        "task_d_queries",
        "task_d_family",
        "task_d_reinsert",
        "task_d_gap_min",
        "task_d_gap_max",
        "task_d_burst_start_min",
        "task_d_burst_start_max",
        "task_d_burst_intra_min",
        "task_d_burst_intra_max",
        "task_d_burst_inter_min",
        "task_d_burst_inter_max",
        "task_d_curriculum_start",
        "task_d_curriculum_end",
        "task_d_curriculum_gap_min",
        "task_d_curriculum_gap_max",
        "task_d_schedule_offset",
        "task_d_sequence_index",
    }
    required = required_by_task[config.task]
    missing = sorted(name for name in required if getattr(config, name) is None)
    inactive = sorted(
        name
        for name in task_fields - required
        if getattr(config, name) is not None
    )
    if missing:
        raise ValueError(f"required task fields are null: {missing}")
    if inactive:
        raise ValueError(f"inactive task fields must be null: {inactive}")
    if config.task_placement not in {None, "in_window", "beyond_window"}:
        raise ValueError(f"invalid task_placement: {config.task_placement}")
    if config.task == "d":
        _validate_task_d(config)


def _validate_task_d(config: Config) -> None:
    if config.task_d_slots != 4:
        raise ValueError("Task D slots must equal 4")
    if config.task_k != 8:
        raise ValueError("Task D requires k=8")
    if config.task_d_core_len != 3848 or config.context_len != 4096:
        raise ValueError("Task D core/context lengths must be 3848/4096")
    if config.task_d_queries != 16:
        raise ValueError("Task D queries must equal 16")
    expected_updates = {"train": 12, "id-control": 12, "drought": 3, "burst": 8}
    if config.task_d_family not in expected_updates:
        raise ValueError("invalid Task D family")
    if config.task_d_updates != expected_updates[config.task_d_family]:
        raise ValueError("invalid Task D updates for family")
    if config.task_d_reinsert not in {"none", "every-128", "prequery"}:
        raise ValueError("invalid Task D reinsert policy")
    bounds = (
        (config.task_d_gap_min, config.task_d_gap_max),
        (config.task_d_burst_start_min, config.task_d_burst_start_max),
        (config.task_d_burst_intra_min, config.task_d_burst_intra_max),
        (config.task_d_burst_inter_min, config.task_d_burst_inter_max),
    )
    if any(lo is None or hi is None or lo < 0 or lo > hi for lo, hi in bounds):
        raise ValueError("invalid Task D gap bounds")
    if config.task_d_family in {"train", "id-control"} and (
        config.task_d_gap_min != 64 or config.task_d_gap_max != 320
    ):
        raise ValueError("Task D train gap bounds must be 64..320")
    if config.task_d_family == "drought" and (
        config.task_d_gap_min != 768 or config.task_d_gap_max != 1280
    ):
        raise ValueError("Task D drought gap bounds must be 768..1280")
    if (
        config.task_d_burst_start_min != 64
        or config.task_d_burst_start_max != 512
        or config.task_d_burst_intra_min != 8
        or config.task_d_burst_intra_max != 32
        or config.task_d_burst_inter_min != 640
        or config.task_d_burst_inter_max != 1200
    ):
        raise ValueError("invalid Task D burst gap bounds")
    if (
        config.task_d_curriculum_start != 8000
        or config.task_d_curriculum_end != 12000
        or config.task_d_curriculum_gap_min != 32
        or config.task_d_curriculum_gap_max != 128
    ):
        raise ValueError("invalid Task D curriculum bounds")
    if config.task_d_schedule_offset is None or config.task_d_schedule_offset < 0:
        raise ValueError("Task D schedule offset must be non-negative")
    if config.task_d_sequence_index is None or config.task_d_sequence_index < 0:
        raise ValueError("Task D sequence index must be non-negative")
    if config.eval_seed_offset < 1:
        raise ValueError("Task D eval seed offset must be positive")


def _longest_delay(config: Config) -> int:
    if config.task == "a":
        assert config.task_N is not None
        return config.task_N
    if config.task == "b":
        assert config.task_delay_max is not None
        return config.task_delay_max
    return config.context_len


@dataclass(frozen=True)
class GitIdentity:
    git_sha: str
    git_diff_sha256: str
    untracked_sha256: str
    dirty: bool


def git_identity(repo: str | Path = ".") -> GitIdentity:
    root = Path(repo)
    git_sha = _git(root, "rev-parse", "HEAD").decode().strip()
    diff = _git(
        root,
        "diff",
        "--binary",
        "--full-index",
        "--no-textconv",
        "--no-ext-diff",
        "HEAD",
    )
    untracked_paths = _git(
        root, "ls-files", "--others", "--exclude-standard", "-z"
    ).split(b"\0")
    records = bytearray()
    for encoded_path in sorted(path for path in untracked_paths if path):
        path = encoded_path.decode("utf-8")
        file_path = root / path
        mode = file_path.lstat().st_mode
        if stat.S_ISLNK(mode):
            target = os.readlink(file_path).encode("utf-8", "surrogateescape")
            content = (
                b"L\0"
                + str(len(target)).encode("ascii")
                + b"\0"
                + target
            )
        else:
            content = file_path.read_bytes()
        records.extend(encoded_path)
        records.extend(b"\0")
        records.extend(str(len(content)).encode("ascii"))
        records.extend(b"\0")
        records.extend(content)
    diff_hash = hashlib.sha256(diff).hexdigest()
    untracked_hash = hashlib.sha256(records).hexdigest()
    return GitIdentity(
        git_sha=git_sha,
        git_diff_sha256=diff_hash,
        untracked_sha256=untracked_hash,
        dirty=bool(diff) or bool(records),
    )


def run_id(config: Config | dict[str, Any], identity: GitIdentity) -> str:
    value = config.as_dict() if isinstance(config, Config) else config
    # Registered four-term formula, in order and with no separators.
    preimage = (
        canonical_json(value)
        + identity.git_sha.encode("ascii")
        + identity.git_diff_sha256.encode("ascii")
        + identity.untracked_sha256.encode("ascii")
    )
    return hashlib.sha256(preimage).hexdigest()[:12]


def _git(root: Path, *args: str) -> bytes:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        stdout=subprocess.PIPE,
    ).stdout
