# ruff: noqa: E402, I001
"""Deterministic single-run training for the scaffold and toy phases."""

from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import subprocess
import time
from collections.abc import Callable, Iterator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any

os.environ["TORCHINDUCTOR_DETERMINISTIC"] = "1"

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
from stencil.data import Example, generate, task_d_training_stream
from stencil.model import StencilTransformer
from stencil.oscillator import assert_stable


class CopyModel(nn.Module):
    def __init__(self, config: Config) -> None:
        super().__init__()
        self.embedding_weight = nn.Parameter(torch.empty(config.vocab, config.d_model))
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
    decision_positions: torch.Tensor
    targets: torch.Tensor
    cue_positions: torch.Tensor
    cue_valid: torch.Tensor
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
    decision_rows: list[torch.Tensor] = []
    cue_rows: list[torch.Tensor] = []
    cue_valid_rows: list[torch.Tensor] = []
    separate_target_rows: list[torch.Tensor | None] = []
    metadata: list[dict[str, Any]] = []
    for row, (example_tokens, example_mask, example_metadata) in enumerate(examples):
        if example_tokens.ndim != 1 or example_mask.shape != example_tokens.shape:
            raise ValueError("examples must contain aligned one-dimensional tensors")
        if example_tokens.numel() < 2 or not torch.any(example_mask[:-1]):
            raise ValueError("every example must contain an answer-decision position")
        size = example_tokens.numel()
        tokens[row, :size] = example_tokens
        loss_mask[row, :size] = example_mask
        decision_rows.append(torch.nonzero(example_mask[:-1], as_tuple=False).flatten())
        if "cue_positions" in example_metadata or "cue_valid" in example_metadata:
            positions = example_metadata.get("cue_positions")
            valid = example_metadata.get("cue_valid")
            if (
                not isinstance(positions, torch.Tensor)
                or not isinstance(valid, torch.Tensor)
                or positions.shape != valid.shape
                or positions.ndim != 1
                or positions.dtype != torch.long
                or valid.dtype != torch.bool
            ):
                raise ValueError("metadata cue tensors are incompatible")
            cue_rows.append(positions)
            cue_valid_rows.append(valid)
        else:
            positions = torch.nonzero(
                (example_tokens >= 1) & (example_tokens <= 32), as_tuple=False
            ).flatten()
            cue_rows.append(positions)
            cue_valid_rows.append(torch.ones_like(positions, dtype=torch.bool))
        separate_targets = example_metadata.get("targets")
        if separate_targets is not None and (
            not isinstance(separate_targets, torch.Tensor)
            or separate_targets.shape != example_tokens.shape
            or separate_targets.dtype != torch.long
        ):
            raise ValueError("metadata targets must align with example tokens")
        separate_target_rows.append(separate_targets)
        metadata.append(example_metadata)
    decision_count = decision_rows[0].numel()
    if decision_count < 1 or any(
        row.numel() != decision_count for row in decision_rows
    ):
        raise ValueError("batch examples must have a fixed decision count")
    decision_positions = torch.stack(decision_rows)
    row_indices = torch.arange(batch_size)[:, None]
    if all(row is not None for row in separate_target_rows):
        targets = torch.stack(
            [
                row[positions]
                for row, positions in zip(
                    separate_target_rows, decision_rows, strict=True
                )
                if row is not None
            ]
        )
        if torch.any(targets < 0):
            raise ValueError("separate targets are missing at decision positions")
    elif any(row is not None for row in separate_target_rows):
        raise ValueError("a batch cannot mix separate and shifted targets")
    else:
        targets = tokens[row_indices, decision_positions + 1]
    cue_count = max(row.numel() for row in cue_rows)
    cue_positions = torch.zeros(batch_size, cue_count, dtype=torch.long)
    cue_valid = torch.zeros(batch_size, cue_count, dtype=torch.bool)
    for row, (positions, valid) in enumerate(
        zip(cue_rows, cue_valid_rows, strict=True)
    ):
        cue_positions[row, : positions.numel()] = positions
        cue_valid[row, : positions.numel()] = valid
    return Batch(
        tokens=tokens,
        loss_mask=loss_mask,
        decision_positions=decision_positions,
        targets=targets,
        cue_positions=cue_positions,
        cue_valid=cue_valid,
        metadata=metadata,
    )


def _training_batches(
    stream: Iterator[Example],
    batch_size: int,
    steps: int,
    *,
    prefetch: bool,
) -> Iterator[Batch]:
    """Yield batches synchronously or one batch ahead on a single worker."""
    if not prefetch:
        for _ in range(steps):
            yield next_examples(stream, batch_size)
        return

    with ThreadPoolExecutor(max_workers=1, thread_name_prefix="stencil-data") as worker:
        pending = worker.submit(next_examples, stream, batch_size)
        for step in range(steps):
            batch = pending.result()
            if step + 1 < steps:
                pending = worker.submit(next_examples, stream, batch_size)
            yield batch


def masked_answer_loss(logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
    """Return causal cross-entropy for statically gathered decision rows."""
    if logits.ndim != 3 or targets.ndim != 2 or logits.shape[:2] != targets.shape:
        raise ValueError("decision logits and targets have incompatible shapes")
    if targets.dtype != torch.long or targets.numel() < 1:
        raise ValueError("targets must be a nonempty integer tensor")
    return F.cross_entropy(logits.flatten(0, 1), targets.flatten())


def task_d_answer_loss(
    logits: torch.Tensor,
    targets: torch.Tensor,
    input_tokens: torch.Tensor,
    *,
    batch_size: int,
) -> torch.Tensor:
    """Score Task D's separate targets with binding non-vacuity assertions."""
    _assert_task_d_targets(targets, input_tokens, batch_size=batch_size)
    return masked_answer_loss(logits, targets)


def _assert_task_d_targets(
    targets: torch.Tensor, input_tokens: torch.Tensor, *, batch_size: int
) -> None:
    """Reject vacuous Task D masks before eager execution or graph replay."""
    expected = 16 * batch_size
    if targets.numel() != expected:
        raise AssertionError(f"Task D loss requires exactly {expected} targets")
    if input_tokens.shape != targets.shape:
        raise AssertionError("Task D inputs and targets must align")
    # Latin-square rules have legitimate fixed points (rule(x) == x, ~1/16 of
    # queries), so per-position inequality is NOT required. Vacuity is the
    # degenerate case: targets outside the answer alphabet, or the whole batch
    # collapsing to target==input (loss would reward copying the operand).
    if not torch.all((targets >= 34) & (targets <= 49)):
        raise AssertionError("Task D targets must lie in the answer alphabet")
    differing = (targets != input_tokens).float().mean().item()
    if differing < 0.5:
        raise AssertionError(
            f"Task D targets equal inputs at {1 - differing:.0%} of masked "
            "positions — fixed-point rate should be ~6%; mask wiring is broken"
        )


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
        foreach=True,
        fused=False,
    )


def _training_device(device: str | torch.device | None) -> torch.device:
    if device is not None:
        return torch.device(device)
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


class _CudaGraphStep:
    """Capture deterministic forward+backward while leaving updates eager."""

    def __init__(
        self,
        model: StencilTransformer,
        optimizer: torch.optim.AdamW,
        batch: Batch,
        device: torch.device,
    ) -> None:
        if device.type != "cuda":
            raise ValueError("CUDA graph execution requires a CUDA device")
        self.model = model
        self.optimizer = optimizer
        self.tokens = torch.empty_like(batch.tokens, device=device)
        self.decision_positions = torch.empty_like(
            batch.decision_positions, device=device
        )
        self.targets = torch.empty_like(batch.targets, device=device)
        self.cue_positions = torch.empty_like(batch.cue_positions, device=device)
        self.cue_valid = torch.empty_like(batch.cue_valid, device=device)
        self.truncation_start = _truncation_start(model, batch)
        self._copy_batch(batch)

        capture_stream = torch.cuda.Stream(device=device)
        capture_stream.wait_stream(torch.cuda.current_stream(device))
        with torch.cuda.stream(capture_stream):
            for _ in range(3):
                optimizer.zero_grad(set_to_none=True)
                warmup_loss = self._loss()
                warmup_loss.backward()
        torch.cuda.current_stream(device).wait_stream(capture_stream)
        del warmup_loss

        optimizer.zero_grad(set_to_none=False)
        self.graph = torch.cuda.CUDAGraph()
        torch.autograd.graph.set_override_stale_capture_stream(True)
        try:
            with torch.cuda.graph(self.graph, stream=capture_stream):
                self.loss = self._loss()
                self.loss.backward()
        finally:
            torch.autograd.graph.set_override_stale_capture_stream(False)

    def _copy_batch(self, batch: Batch) -> None:
        if self.model.config.task == "d":
            rows = torch.arange(batch.tokens.shape[0])[:, None]
            _assert_task_d_targets(
                batch.targets,
                batch.tokens[rows, batch.decision_positions],
                batch_size=batch.tokens.shape[0],
            )
        tensors = (
            (self.tokens, batch.tokens),
            (self.decision_positions, batch.decision_positions),
            (self.targets, batch.targets),
            (self.cue_positions, batch.cue_positions),
            (self.cue_valid, batch.cue_valid),
        )
        for destination, source in tensors:
            if destination.shape != source.shape:
                raise ValueError("CUDA graph batches must have fixed tensor shapes")
            destination.copy_(source, non_blocking=True)

    def _loss(self) -> torch.Tensor:
        logits = self.model(
            self.tokens,
            decision_positions=self.decision_positions,
            cue_positions=self.cue_positions,
            cue_valid=self.cue_valid,
            truncation_start=self.truncation_start,
        )
        return masked_answer_loss(logits, self.targets)

    def forward_backward(self, batch: Batch) -> torch.Tensor:
        self._copy_batch(batch)
        self.optimizer.zero_grad(set_to_none=False)
        self.graph.replay()
        return self.loss.detach().clone()


def train_model(
    config: Config,
    *,
    device: str | torch.device | None = None,
    on_step: Callable[[int, float, float], None] | None = None,
    use_cuda_graph: bool = False,
    use_prefetch: bool = True,
    use_compiled_scan: bool = False,
) -> tuple[StencilTransformer, list[float]]:
    """Train one real variant using fresh generator data at every step."""
    if config.task not in {"a", "b", "d", "m"}:
        raise ValueError("full-variant training requires task a, b, d, or m")
    if config.precision != "fp32":
        raise ValueError("toy-phase training requires fp32")
    if config.steps < 1 or config.batch < 1:
        raise ValueError("steps and batch must be positive")
    execution_device = _training_device(device)
    model = StencilTransformer(config, use_compiled_scan=use_compiled_scan).to(
        device=execution_device, dtype=torch.float32
    )
    stream = task_d_training_stream(config) if config.task == "d" else generate(config)
    # AdamW itself has no draws; instantiation still pins the registered stream.
    named_generator(config.seed_train, "train")
    optimizer = _optimizer(model, config)
    graph_step: _CudaGraphStep | None = None
    losses: list[float] = []
    pending_losses: list[torch.Tensor] = []
    pending_steps: list[tuple[int, float]] = []

    def flush_losses() -> None:
        if not pending_losses:
            return
        values = torch.stack(pending_losses).cpu().tolist()
        losses.extend(values)
        if on_step is not None:
            for (recorded_step, recorded_lr), value in zip(
                pending_steps, values, strict=True
            ):
                on_step(recorded_step, value, recorded_lr)
        pending_losses.clear()
        pending_steps.clear()

    model.train()
    batches = _training_batches(
        stream, config.batch, config.steps, prefetch=use_prefetch
    )
    for step, batch in enumerate(batches):
        lr = _learning_rate(config, step)
        for group in optimizer.param_groups:
            group["lr"] = lr
        if use_cuda_graph:
            if graph_step is None:
                graph_step = _CudaGraphStep(model, optimizer, batch, execution_device)
            loss = graph_step.forward_backward(batch)
        else:
            if config.task == "d":
                rows = torch.arange(batch.tokens.shape[0])[:, None]
                _assert_task_d_targets(
                    batch.targets,
                    batch.tokens[rows, batch.decision_positions],
                    batch_size=config.batch,
                )
            tokens = batch.tokens.to(execution_device)
            decision_positions = batch.decision_positions.to(execution_device)
            targets = batch.targets.to(execution_device)
            cue_positions = batch.cue_positions.to(execution_device)
            cue_valid = batch.cue_valid.to(execution_device)
            optimizer.zero_grad(set_to_none=True)
            logits = model(
                tokens,
                decision_positions=decision_positions,
                cue_positions=cue_positions,
                cue_valid=cue_valid,
                truncation_start=_truncation_start(model, batch),
            )
            loss = masked_answer_loss(logits, targets)
            loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), config.clip)
        optimizer.step()
        pending_losses.append(loss.detach())
        pending_steps.append((step, lr))
        if len(pending_losses) == 50:
            flush_losses()
    flush_losses()
    return model, losses


def _truncation_start(model: StencilTransformer, batch: Batch) -> int:
    """Keep Task D's variable query positions graph-static without dropping queries."""
    if model.config.task == "d":
        return 0
    return max(
        0,
        int(batch.decision_positions.min()) - model.receptive_field(),
    )


def train_model_losses(
    config: Config,
    *,
    device: str | torch.device | None = None,
    use_prefetch: bool = True,
    use_compiled_scan: bool = False,
) -> list[float]:
    """Convenience surface for the full-model determinism contract."""
    model, losses = train_model(
        config,
        device=device,
        use_prefetch=use_prefetch,
        use_compiled_scan=use_compiled_scan,
    )
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
    use_cuda_graph: bool = False,
    use_prefetch: bool = True,
    use_compiled_scan: bool = False,
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
            for step, (loss, lr) in enumerate(zip(losses, learning_rates, strict=True)):
                handle.write(json.dumps({"step": step, "loss": loss, "lr": lr}) + "\n")
        (run_dir / "DONE").touch()
        return run_dir

    with (run_dir / "metrics.jsonl").open("w", encoding="utf-8") as handle:

        def record(step: int, loss: float, lr: float) -> None:
            handle.write(json.dumps({"step": step, "loss": loss, "lr": lr}) + "\n")

        train_started = time.perf_counter()
        model, _ = train_model(
            config,
            on_step=record,
            use_cuda_graph=use_cuda_graph,
            use_prefetch=use_prefetch,
            use_compiled_scan=use_compiled_scan,
        )
        train_wall_seconds = time.perf_counter() - train_started
    if config.variant in {"m1", "m1b"}:
        assert_stable(model)
    checkpoint = run_dir / "final.pt"
    torch.save({"step": config.steps, "model": model.state_dict()}, checkpoint)
    from stencil.evaluate import evaluate_model  # Avoid an entrypoint cycle.

    eval_started = time.perf_counter()
    result = evaluate_model(model, config, repo=root)
    eval_wall_seconds = time.perf_counter() - eval_started
    result["cost"] = {
        "train_wall_seconds": train_wall_seconds,
        "eval_wall_seconds": eval_wall_seconds,
    }
    if config.task == "d":
        from stencil.evaluate import merge_task_d_evaluations

        result = merge_task_d_evaluations(None, result)
    (run_dir / "eval.json").write_bytes(canonical_json(result) + b"\n")
    (run_dir / "DONE").touch()
    return run_dir


def _prepare_run_dir(run_dir: Path, identity: GitIdentity, force: bool) -> None:
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
    parser.add_argument("--cuda-graph", action="store_true")
    parser.add_argument("--compiled-scan", action="store_true")
    parser.add_argument(
        "--no-prefetch", action="store_false", dest="use_prefetch", default=True
    )
    args = parser.parse_args()
    config = load_config(args.config)
    print(
        run(
            config,
            force=args.force,
            allow_dirty=args.allow_dirty,
            use_cuda_graph=args.cuda_graph,
            use_prefetch=args.use_prefetch,
            use_compiled_scan=args.compiled_scan,
        )
    )


if __name__ == "__main__":
    main()
