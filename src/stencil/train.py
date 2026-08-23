# ruff: noqa: E402, I001
"""Deterministic single-run training for the scaffold and toy phases."""

from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import subprocess
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

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
from stencil.data import Example, generate
from stencil.model import StencilTransformer
from stencil.oscillator import assert_stable


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


@dataclass(frozen=True)
class Batch:
    tokens: torch.Tensor
    loss_mask: torch.Tensor
    metadata: list[dict[str, Any]]


def next_examples(stream: Iterator[Example], batch_size: int) -> Batch:
    """Collate fresh variable-length generator examples with right padding."""
    if batch_size < 1:
        raise ValueError("batch_size must be positive")
    examples = [next(stream) for _ in range(batch_size)]
    if not examples:
        raise RuntimeError("generator produced no examples")
    length = max(tokens.numel() for tokens, _, _ in examples)
    tokens = torch.zeros(batch_size, length, dtype=torch.long)
    loss_mask = torch.zeros(batch_size, length, dtype=torch.bool)
    metadata: list[dict[str, Any]] = []
    for row, (example_tokens, example_mask, example_metadata) in enumerate(examples):
        if example_tokens.ndim != 1 or example_mask.shape != example_tokens.shape:
            raise ValueError("examples must contain aligned one-dimensional tensors")
        if example_tokens.numel() < 2 or not torch.any(example_mask[:-1]):
            raise ValueError("every example must contain an answer-decision position")
        size = example_tokens.numel()
        tokens[row, :size] = example_tokens
        loss_mask[row, :size] = example_mask
        metadata.append(example_metadata)
    return Batch(tokens=tokens, loss_mask=loss_mask, metadata=metadata)


def masked_answer_loss(
    logits: torch.Tensor, tokens: torch.Tensor, loss_mask: torch.Tensor
) -> torch.Tensor:
    """Return causal cross-entropy only at registered answer decisions."""
    if logits.ndim != 3 or tokens.shape != loss_mask.shape:
        raise ValueError("logits, tokens, and loss_mask have incompatible shapes")
    if logits.shape[:2] != tokens.shape or loss_mask.dtype != torch.bool:
        raise ValueError("logits, tokens, and loss_mask have incompatible shapes")
    decisions = loss_mask[:, :-1]
    if not torch.any(decisions):
        raise ValueError("batch has no answer-decision positions")
    selected_logits = logits[:, :-1][decisions]
    targets = tokens[:, 1:][decisions]
    if selected_logits.shape[0] != targets.numel() or targets.numel() < 1:
        raise RuntimeError("answer selection was vacuous")
    return F.cross_entropy(selected_logits, targets)


def _optimizer(model: StencilTransformer, config: Config) -> torch.optim.AdamW:
    decay: list[nn.Parameter] = []
    no_decay: list[nn.Parameter] = []
    for name, parameter in model.named_parameters():
        is_bias = name.endswith("bias") or name.endswith("_bias")
        is_norm = "norm" in name
        is_oscillator = config.variant in {"m1", "m1b"} and name.startswith(
            "controller."
        )
        (no_decay if is_bias or is_norm or is_oscillator else decay).append(parameter)
    if not decay or not no_decay:
        raise RuntimeError("optimizer decay partition must be nonempty")
    if len({id(parameter) for parameter in decay + no_decay}) != sum(
        1 for _ in model.parameters()
    ):
        raise RuntimeError("optimizer parameter partition is not one-to-one")
    return torch.optim.AdamW(
        [
            {"params": decay, "weight_decay": config.weight_decay},
            {"params": no_decay, "weight_decay": 0.0},
        ],
        lr=config.lr,
        betas=(config.adam_beta1, config.adam_beta2),
        eps=config.adam_eps,
        foreach=False,
        fused=False,
    )


def _training_device(device: str | torch.device | None) -> torch.device:
    if device is not None:
        return torch.device(device)
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def train_model(
    config: Config,
    *,
    device: str | torch.device | None = None,
    on_step: Callable[[int, float, float], None] | None = None,
) -> tuple[StencilTransformer, list[float]]:
    """Train one real variant using fresh generator data at every step."""
    if config.task not in {"a", "b", "m"}:
        raise ValueError("full-variant training requires task a, b, or m")
    if config.precision != "fp32":
        raise ValueError("toy-phase training requires fp32")
    if config.steps < 1 or config.batch < 1:
        raise ValueError("steps and batch must be positive")
    execution_device = _training_device(device)
    model = StencilTransformer(config).to(device=execution_device, dtype=torch.float32)
    stream = generate(config)
    # AdamW itself has no draws; instantiation still pins the registered stream.
    named_generator(config.seed_train, "train")
    optimizer = _optimizer(model, config)
    losses: list[float] = []
    model.train()
    for step in range(config.steps):
        lr = _learning_rate(config, step)
        for group in optimizer.param_groups:
            group["lr"] = lr
        batch = next_examples(stream, config.batch)
        tokens = batch.tokens.to(execution_device)
        loss_mask = batch.loss_mask.to(execution_device)
        optimizer.zero_grad(set_to_none=True)
        loss = masked_answer_loss(model(tokens), tokens, loss_mask)
        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), config.clip)
        optimizer.step()
        value = float(loss.detach())
        losses.append(value)
        if on_step is not None:
            on_step(step, value, lr)
    return model, losses


def train_model_losses(
    config: Config, *, device: str | torch.device | None = None
) -> list[float]:
    """Convenience surface for the full-model determinism contract."""
    model, losses = train_model(config, device=device)
    del model
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
    decay_intervals = max(1, config.steps - config.warmup - 1)
    progress = min(1.0, (step - config.warmup) / decay_intervals)
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
    if config.task == "copy":
        losses, learning_rates = _train(config)
        with (run_dir / "metrics.jsonl").open("w", encoding="utf-8") as handle:
            for step, (loss, lr) in enumerate(
                zip(losses, learning_rates, strict=True)
            ):
                handle.write(
                    json.dumps({"step": step, "loss": loss, "lr": lr}) + "\n"
                )
        (run_dir / "DONE").touch()
        return run_dir

    with (run_dir / "metrics.jsonl").open("w", encoding="utf-8") as handle:
        def record(step: int, loss: float, lr: float) -> None:
            handle.write(json.dumps({"step": step, "loss": loss, "lr": lr}) + "\n")
            handle.flush()

        model, _ = train_model(config, on_step=record)
    if config.variant in {"m1", "m1b"}:
        assert_stable(model)
    checkpoint = run_dir / "final.pt"
    torch.save({"step": config.steps, "model": model.state_dict()}, checkpoint)
    from stencil.evaluate import evaluate_model  # Avoid an entrypoint cycle.

    result = evaluate_model(model, config)
    (run_dir / "eval.json").write_bytes(canonical_json(result) + b"\n")
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
