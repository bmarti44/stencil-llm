# ruff: noqa: E402, I001
"""Minimal deterministic Phase 0 copy-task trainer."""

from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import subprocess
from pathlib import Path

from stencil import determinism as _determinism  # noqa: F401

import torch
from torch import nn
from torch.nn import functional as F

from stencil.config import (
    Config,
    GitIdentity,
    canonical_json,
    git_identity,
    load_config,
)
from stencil.config import run_id as make_run_id
from stencil.determinism import named_generator


class CopyModel(nn.Module):
    def __init__(self, config: Config) -> None:
        super().__init__()
        self.embedding_weight = nn.Parameter(
            torch.empty(config.vocab, config.d_model)
        )
        self.head_weight = nn.Parameter(torch.empty(config.vocab, config.d_model))
        self.head_bias = nn.Parameter(torch.empty(config.vocab))

    def forward(self, tokens: torch.Tensor) -> torch.Tensor:
        hidden = F.embedding(tokens, self.embedding_weight)
        return F.linear(hidden, self.head_weight, self.head_bias)


def initialize_model(config: Config) -> CopyModel:
    generator = named_generator(config.seed_init, "init")
    model = CopyModel(config)
    nn.init.normal_(model.embedding_weight, mean=0.0, std=0.02, generator=generator)
    nn.init.normal_(model.head_weight, mean=0.0, std=0.02, generator=generator)
    nn.init.zeros_(model.head_bias)
    return model


def first_batch(config: Config) -> torch.Tensor:
    return _next_batch(config, named_generator(config.seed_data, "operands"))


def _next_batch(config: Config, generator: torch.Generator) -> torch.Tensor:
    return torch.randint(
        34,
        50,
        (config.batch, config.context_len),
        generator=generator,
        dtype=torch.long,
    )


def train_losses(config: Config) -> list[float]:
    losses, _ = _train(config)
    return losses


def _train(config: Config) -> tuple[list[float], list[float]]:
    if config.task != "copy":
        raise ValueError("the Phase 0 trainer supports only task='copy'")
    if config.precision != "fp32":
        raise ValueError("the Phase 0 trainer requires fp32")

    model = initialize_model(config).to(dtype=torch.float32)
    operands = named_generator(config.seed_data, "operands")
    # Instantiate the registered optimizer stream even though AdamW has no random draws.
    named_generator(config.seed_train, "train")
    decay = [model.embedding_weight, model.head_weight]
    no_decay = [model.head_bias]
    optimizer = torch.optim.AdamW(
        [
            {"params": decay, "weight_decay": config.weight_decay},
            {"params": no_decay, "weight_decay": 0.0},
        ],
        lr=config.lr,
        betas=(config.adam_beta1, config.adam_beta2),
        eps=config.adam_eps,
    )

    losses: list[float] = []
    learning_rates: list[float] = []
    for step in range(config.steps):
        lr = _learning_rate(config, step)
        for group in optimizer.param_groups:
            group["lr"] = lr
        tokens = _next_batch(config, operands)
        logits = model(tokens)
        loss = F.cross_entropy(
            logits[:, 1:, :].reshape(-1, config.vocab),
            tokens[:, :-1].reshape(-1),
        )
        optimizer.zero_grad(set_to_none=True)
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), config.clip)
        optimizer.step()
        losses.append(loss.detach().item())
        learning_rates.append(lr)
    return losses, learning_rates


def _learning_rate(config: Config, step: int) -> float:
    if step < config.warmup:
        return config.lr * (step + 1) / config.warmup
    decay_steps = max(1, config.steps - config.warmup)
    progress = min(1.0, (step - config.warmup) / decay_steps)
    cosine = 0.5 * (1.0 + math.cos(math.pi * progress))
    return config.lr_min + (config.lr - config.lr_min) * cosine


def run(
    config: Config,
    *,
    repo: str | Path = ".",
    force: bool = False,
    allow_dirty: bool = False,
) -> Path:
    root = Path(repo).resolve()
    identity = git_identity(root)
    if identity.dirty and not allow_dirty:
        raise RuntimeError("dirty worktree requires --allow-dirty")
    identifier = make_run_id(config, identity)
    run_dir = root / "results" / identifier
    _prepare_run_dir(run_dir, identity, force)

    (run_dir / "config.json").write_bytes(canonical_json(config.as_dict()) + b"\n")
    env = _environment(identity)
    (run_dir / "env.json").write_bytes(canonical_json(env) + b"\n")
    losses, learning_rates = _train(config)
    with (run_dir / "metrics.jsonl").open("w", encoding="utf-8") as handle:
        for step, (loss, lr) in enumerate(zip(losses, learning_rates, strict=True)):
            handle.write(json.dumps({"step": step, "loss": loss, "lr": lr}) + "\n")
    (run_dir / "DONE").touch()
    return run_dir


def _prepare_run_dir(
    run_dir: Path, identity: GitIdentity, force: bool
) -> None:
    if run_dir.exists():
        if not force:
            raise FileExistsError(f"run directory already exists: {run_dir}")
        env_path = run_dir / "env.json"
        try:
            prior = json.loads(env_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError) as error:
            raise RuntimeError("cannot force a run without a valid env.json") from error
        keys = ("git_sha", "git_diff_sha256", "untracked_sha256")
        current = _environment(identity)
        if any(prior.get(key) != current[key] for key in keys):
            raise RuntimeError(
                "--force refuses a run directory from different git state"
            )
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True)


def _environment(identity: GitIdentity) -> dict[str, object]:
    gpu_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else None
    driver = None
    if torch.cuda.is_available():
        try:
            driver = subprocess.run(
                ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.splitlines()[0]
        except (FileNotFoundError, subprocess.CalledProcessError, IndexError):
            driver = None
    return {
        "git_sha": identity.git_sha,
        "git_diff_sha256": identity.git_diff_sha256,
        "untracked_sha256": identity.untracked_sha256,
        "dirty": identity.dirty,
        "CUBLAS_WORKSPACE_CONFIG": os.environ["CUBLAS_WORKSPACE_CONFIG"],
        "torch_version": torch.__version__,
        "gpu_name": gpu_name,
        "driver": driver,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=Path)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--allow-dirty", action="store_true")
    args = parser.parse_args()
    config = load_config(args.config)
    print(run(config, force=args.force, allow_dirty=args.allow_dirty))


if __name__ == "__main__":
    main()
