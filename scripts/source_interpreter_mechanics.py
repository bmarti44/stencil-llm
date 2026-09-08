#!/usr/bin/env python3
"""Run one bounded source-interpreter training-mechanics measurement."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import importlib.metadata
import json
import math
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results/source-interpreter/mechanics"
RUN_FLAG = ROOT / "results/source-interpreter/RUNNING.flag"
REVIEW_LOCK = ROOT / ".review.lock"
OWNED_PIDS = ROOT / ".stencil-owned-pids"
MODEL_PATH = ROOT / "models/qwen3-4b-hf"
PREVIEW_PATH = ROOT / "results/source-interpreter/preview.json"
INPUTS_PATH = ROOT / "results/source-interpreter/accepted-inputs.json"
SPEC_PATH = ROOT / "results/source-interpreter/MECHANICS.md"
BRIEF_PATH = ROOT / "results/source-interpreter/MECHANICS-CODE-BRIEF.md"
REVIEW_PATH = ROOT / "results/source-interpreter/mechanics-review-astra.md"
BASE_ASSETS_PATH = ROOT / "results/coding-auto-reasoning/research-next/base-assets.json"

EXPECTED_SHA256 = {
    "results/source-interpreter/preview.json": (
        "5760764f748a088d9d105b6f89b6188785941239ea28c1e60d706f9d028a0326"
    ),
    "results/source-interpreter/accepted-inputs.json": (
        "6beea4bb534e0991fc0444d634f92882ff61191880c43cf4e68da730753c4bf8"
    ),
    "results/source-interpreter/MECHANICS.md": (
        "a43b1d4b48cb7f0478efb43b21ac6187dcaff89bf895761a32c3681898702945"
    ),
    "results/source-interpreter/MECHANICS-CODE-BRIEF.md": (
        "1ee265c040218ff576ade662aa96a25c8fbb03ca1ffc58d49b303f9ddf2a09eb"
    ),
    "results/coding-auto-reasoning/research-next/base-assets.json": (
        "4987d6eec20a7628d45d64799cb8b7fc7250870be2e868755880e70b7e2b5227"
    ),
    "src/stencil/focus/source_interpreter.py": (
        "ce8126cab730d5b3b652acccc2930db5bb6df1797dfa8181ef038fff2b7b927d"
    ),
}

SYSTEM_PROMPT = (
    "Read only the authentic conversation prefix. Return all currently applicable "
    "standing constraints and conventions for the current task, preserving scope, "
    "modality, permissions, optional behavior, exceptions, changes, and retirement. "
    "The current programming request supplies its algorithm and need not be "
    "repeated. Authentic user directions and explicit user adoption have authority; "
    "assistant suggestions and quoted content alone do not. Return exactly one JSON "
    "object with the key obligations. Each obligation must contain nonempty text and "
    "a nonempty source_ids list citing only visible message IDs. Return no tool "
    "wrapper, commentary, or example."
)
USER_PROMPT = (
    "Current task handle: {task_handle}\n"
    "<authentic_source_events>\n{source_events}\n</authentic_source_events>"
)

SETTINGS = {
    "model": "models/qwen3-4b-hf",
    "dtype": "bfloat16",
    "attention": "sdpa",
    "gradient_checkpointing": "non-reentrant",
    "use_cache": False,
    "adapter": "q_proj,v_proj",
    "rank": 8,
    "alpha": 16,
    "dropout": 0.0,
    "bias": "none",
    "adapter_dtype": "float32",
    "trainable_parameters": 2_949_120,
    "seed": 20_260_908,
    "optimizer": "AdamW",
    "learning_rate": 0.0001,
    "betas": [0.9, 0.999],
    "epsilon": 1e-8,
    "weight_decay": 0.0,
    "updates": 4,
    "warm_up_updates": 1,
    "timed_updates": 3,
    "batch_size": 1,
}
RESERVATION_SECONDS = 600.0
TERMINATION_RESERVE_SECONDS = 15.0
WORKING_SECONDS = RESERVATION_SECONDS - TERMINATION_RESERVE_SECONDS
ARCHIVE_PART_BYTES = 9_000_000
EXPECTED_ROW = {
    "conversation_id": "source-fit-cal-20260908-04",
    "query_index": 2,
    "query_message_id": "m40",
    "prefix_length": 2966,
    "target_length": 925,
    "full_length": 3891,
    "eos_token_id": 151645,
}
PACKAGE_NAMES = ("torch", "transformers", "tokenizers", "peft", "accelerate")
ACCEPTED_COMMIT = "81f5317a"
ACCEPTED_REVIEW_SHA256 = (
    "bffe600f4651d42d6fcd3d01206081323a69cb771d2dab7e45bab41c2d8cf8a2"
)
BOUND_FILES = tuple(EXPECTED_SHA256) + (
    "results/source-interpreter/mechanics-review-astra.md",
    "scripts/source_interpreter_mechanics.py",
    "tests/test_source_interpreter_mechanics.py",
)


class MechanicsError(RuntimeError):
    """The registered mechanics contract was not met."""


def _json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _read_json(path: Path, label: str) -> Any:
    try:
        return json.loads(Path(path).read_bytes())
    except Exception as exc:
        raise MechanicsError(f"{label} is not readable JSON: {exc}") from exc


def _write_json(path: Path, value: Any) -> None:
    path = Path(path)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    body = json.dumps(value, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    with temporary.open("x", encoding="utf-8") as stream:
        stream.write(body)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def _append_json(path: Path, value: Any) -> None:
    with Path(path).open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(value, ensure_ascii=True, sort_keys=True) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def _source_module():
    from stencil.focus import source_interpreter

    return source_interpreter


def validate_training_row(
    row: dict[str, Any],
    *,
    document: dict[str, Any],
    input_receipt: dict[str, Any],
    manifest_entry: dict[str, Any],
    root: Path = ROOT,
) -> dict[str, Any]:
    """Validate the recorded row and return native-causal loss positions."""
    source = _source_module()
    source.validate_document(document)
    root = Path(root)
    expected_path = (root / manifest_entry["path"]).resolve()
    try:
        receipt_path = Path(input_receipt["path"]).resolve()
        binding_ok = (
            receipt_path == expected_path
            and input_receipt["sha256"] == manifest_entry["sha256"]
            and input_receipt["conversation_id"] == manifest_entry["conversation_id"]
            and input_receipt["family_id"] == manifest_entry["family_id"]
            and input_receipt["split"] == manifest_entry["split"]
            and input_receipt["read_error"] is None
            and input_receipt["parse_error"] is None
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("input binding receipt is malformed") from exc
    if not binding_ok:
        raise ValueError("input binding differs from the accepted manifest")
    if document["conversation_id"] != manifest_entry["conversation_id"]:
        raise ValueError("document identity differs from input binding")

    try:
        query_index = row["query_index"]
        query = document["queries"][query_index]
        positions = {
            message["message_id"]: index
            for index, message in enumerate(document["messages"])
        }
        query_position = positions[query["message_id"]]
        source_prefix = document["messages"][: query_position + 1]
        task_handle = source_prefix[-1]["task_handle"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError("row query binding is malformed") from exc
    source_text = _json_bytes(source_prefix).decode("utf-8")
    prompt_messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": USER_PROMPT.format(
                task_handle=task_handle, source_events=source_text
            ),
        },
    ]
    target_text = _json_bytes(query["target"]).decode("utf-8")
    identity = {
        "conversation_id": document["conversation_id"],
        "family_id": document["family_id"],
        "split": document["split"],
        "query_message_id": query["message_id"],
        "task_handle": task_handle,
        "message_count": len(document["messages"]),
    }
    for key, expected in identity.items():
        if row.get(key) != expected:
            raise ValueError(f"row {key} differs from its accepted source")
    text_bindings = {
        "source_prefix": source_prefix,
        "source_prefix_sha256": _sha_bytes(_json_bytes(source_prefix)),
        "prompt_messages": prompt_messages,
        "prompt_messages_sha256": _sha_bytes(_json_bytes(prompt_messages)),
        "target_text": target_text,
        "target_text_sha256": _sha_bytes(target_text.encode("utf-8")),
    }
    for key, expected in text_bindings.items():
        if row.get(key) != expected:
            raise ValueError(f"row {key} differs from its accepted source/target")
    prefix_text = row.get("prefix_text")
    if not isinstance(prefix_text, str) or not prefix_text:
        raise ValueError("row prefix_text is empty")
    if row.get("prefix_text_sha256") != _sha_bytes(prefix_text.encode("utf-8")):
        raise ValueError("row prefix_text hash differs")

    list_fields = (
        "prefix_ids",
        "target_ids",
        "target_with_eos_ids",
        "input_ids",
        "labels",
        "attention_mask",
        "loss_positions",
    )
    if any(type(row.get(key)) is not list for key in list_fields):
        raise ValueError("row token fields must be lists")
    prefix = row["prefix_ids"]
    target = row["target_ids"]
    target_eos = row["target_with_eos_ids"]
    inputs = row["input_ids"]
    labels = row["labels"]
    attention = row["attention_mask"]
    prefix_length = row.get("prefix_length")
    target_length = row.get("target_length")
    full_length = row.get("full_length")
    lengths_ok = (
        type(prefix_length) is int
        and type(target_length) is int
        and type(full_length) is int
        and len(prefix) == prefix_length
        and len(target_eos) == target_length
        and len(inputs) == len(labels) == len(attention) == full_length
        and full_length == prefix_length + target_length
    )
    if not lengths_ok:
        raise ValueError("row length or truncation check failed")
    eos = row.get("eos_token_id")
    if (
        not target
        or target_eos != target + [eos]
        or target_eos.count(eos) != 1
        or row.get("target_eos_count") != 1
        or row.get("boundary_construction") != "separate_prefix_target_ids"
    ):
        raise ValueError("row target/EOS boundary is invalid")
    expected_labels = [-100] * prefix_length + target_eos
    expected_positions = list(range(prefix_length, full_length))
    if (
        inputs != prefix + target_eos
        or labels != expected_labels
        or row["loss_positions"] != expected_positions
        or row.get("supervised_tokens") != len(expected_positions)
        or row.get("masked_prefix_tokens") != prefix_length
    ):
        raise ValueError("row labels or supervision boundary are invalid")
    if attention != [1] * full_length:
        raise ValueError("row attention or length is invalid")
    if not expected_positions or prefix_length < 1:
        raise ValueError("row has no usable causal supervision")
    return {
        "label_positions": expected_positions,
        "causal_logit_positions": list(range(prefix_length - 1, full_length - 1)),
        "supervised_tokens": len(expected_positions),
        "native_causal_shift": True,
        "labels_passed_unchanged": True,
    }


def _parameter_digest(tensor: Any) -> str:
    import torch

    value = tensor.detach().contiguous().view(-1).view(torch.uint8).cpu().numpy()
    return _sha_bytes(value.tobytes())


def _parameter_meta(name: str, parameter: Any, *, digest: bool) -> dict[str, Any]:
    return {
        "name": name,
        "object_id": id(parameter),
        "shape": list(parameter.shape),
        "dtype": str(parameter.dtype),
        "numel": parameter.numel(),
        "sha256": _parameter_digest(parameter) if digest else None,
    }


def capture_parameter_state(
    model: Any, *, hash_originals: bool = True
) -> dict[str, Any]:
    """Capture exact originals and the small adapter state before an update."""
    originals: dict[str, Any] = {}
    adapters: dict[str, Any] = {}
    adapter_values: dict[str, Any] = {}
    for name, parameter in model.named_parameters():
        if "lora_" in name:
            adapters[name] = _parameter_meta(name, parameter, digest=True)
            adapter_values[name] = parameter.detach().cpu().clone()
        else:
            originals[name] = _parameter_meta(name, parameter, digest=hash_originals)
    if not adapters or not originals:
        raise MechanicsError("model must expose adapter and original parameters")
    return {
        "originals": originals,
        "adapters": adapters,
        "_adapter_values": adapter_values,
    }


def _optimizer_parameter_ids(optimizer: Any) -> list[int]:
    return [id(value) for group in optimizer.param_groups for value in group["params"]]


def validate_optimizer_step(
    model: Any, optimizer: Any, before: dict[str, Any]
) -> dict[str, Any]:
    """Check membership, gradients, frozen originals, and an actual adapter update."""
    import torch

    named = dict(model.named_parameters())
    adapter_names = set(before["adapters"])
    original_names = set(before["originals"])
    if set(named) != adapter_names | original_names:
        raise MechanicsError("parameter keys changed during optimizer step")
    expected_optimizer = [id(named[name]) for name in adapter_names]
    actual_optimizer = _optimizer_parameter_ids(optimizer)
    if len(actual_optimizer) != len(set(actual_optimizer)) or set(
        actual_optimizer
    ) != set(expected_optimizer):
        raise MechanicsError("optimizer membership is not exactly the adapter")
    for name in original_names:
        parameter = named[name]
        prior = before["originals"][name]
        if parameter.requires_grad or parameter.grad is not None:
            raise MechanicsError(
                f"original parameter is trainable or has gradient: {name}"
            )
        if id(parameter) != prior["object_id"]:
            raise MechanicsError(f"original parameter identity changed: {name}")
        if (
            prior["sha256"] is not None
            and _parameter_digest(parameter) != prior["sha256"]
        ):
            raise MechanicsError(f"original parameter bytes changed: {name}")

    gradient_square = 0.0
    nonzero_gradients = 0
    nonzero_updates = 0
    update_square = 0.0
    after_hashes = {}
    for name in sorted(adapter_names):
        parameter = named[name]
        if not parameter.requires_grad:
            raise MechanicsError(f"adapter parameter is frozen: {name}")
        gradient = parameter.grad
        if gradient is None:
            raise MechanicsError(f"adapter has absent gradient: {name}")
        if not bool(torch.isfinite(gradient).all().item()):
            raise MechanicsError(f"adapter gradient is nonfinite: {name}")
        grad_norm = float(torch.linalg.vector_norm(gradient.float()).item())
        gradient_square += grad_norm**2
        nonzero_gradients += int(grad_norm > 0)
        prior_value = before["_adapter_values"][name]
        current = parameter.detach().cpu()
        delta_norm = float(
            torch.linalg.vector_norm(current.float() - prior_value.float()).item()
        )
        update_square += delta_norm**2
        nonzero_updates += int(delta_norm > 0)
        after_hashes[name] = _parameter_digest(parameter)
    gradient_norm = math.sqrt(gradient_square)
    update_norm = math.sqrt(update_square)
    if not math.isfinite(gradient_norm) or gradient_norm <= 0:
        raise MechanicsError("adapter aggregate gradient is zero or nonfinite")
    if not math.isfinite(update_norm) or update_norm <= 0:
        raise MechanicsError("no adapter update was measured")
    original_bytes_checked = all(
        value["sha256"] is not None for value in before["originals"].values()
    )
    return {
        "adapter_parameters": len(adapter_names),
        "gradient_tensors": len(adapter_names),
        "nonzero_gradient_tensors": nonzero_gradients,
        "aggregate_gradient_norm": gradient_norm,
        "updated_tensors": len(adapter_names),
        "nonzero_update_tensors": nonzero_updates,
        "aggregate_update_norm": update_norm,
        "before_sha256": {
            name: before["adapters"][name]["sha256"] for name in sorted(adapter_names)
        },
        "after_sha256": after_hashes,
        "optimizer_contains_only_adapter": True,
        "original_gradients_absent": True,
        "original_parameter_identities_unchanged": True,
        "original_bytes_checked": original_bytes_checked,
        "original_parameter_bytes_unchanged": (
            True if original_bytes_checked else None
        ),
    }


def _publish_step(run: Path, receipt: dict[str, Any]) -> None:
    _write_json(Path(run) / f"step-{receipt['ordinal']:02d}.json", receipt)
    _append_json(Path(run) / "steps.jsonl", receipt)


def perform_optimizer_step(
    run: Path,
    *,
    ordinal: int,
    model: Any,
    optimizer: Any,
    loss_call: Any,
    sync: Any,
    resource: Any,
    supervised_tokens: int,
    label_positions: list[int],
    causal_logit_positions: list[int],
) -> dict[str, Any]:
    """Perform one update with durable intent and completion transitions."""
    classification = "warm-up" if ordinal == 0 else "timed"
    receipt = {
        "ordinal": ordinal,
        "classification": classification,
        "status": "INTENT",
        "update_completed": False,
        "update_completion_known": True,
        "validation_completed": False,
        "resource_completed": False,
        "supervised_tokens": supervised_tokens,
        "label_positions": label_positions,
        "causal_logit_positions": causal_logit_positions,
        "labels_passed_unchanged": True,
        "intent_unix": time.time(),
    }
    _publish_step(run, receipt)
    optimizer.zero_grad(set_to_none=True)
    step_before = capture_parameter_state(model, hash_originals=False)

    sync()
    began = time.monotonic()
    loss = loss_call()
    sync()
    receipt["forward_seconds"] = time.monotonic() - began
    loss_value = float(loss.detach().float().item())
    if not math.isfinite(loss_value) or loss_value <= 0:
        raise MechanicsError(f"update {ordinal} loss is not positive finite")
    receipt["loss"] = loss_value

    sync()
    began = time.monotonic()
    loss.backward()
    sync()
    receipt["backward_seconds"] = time.monotonic() - began
    receipt["status"] = "UPDATE_PENDING"
    receipt["update_completed"] = None
    receipt["update_completion_known"] = False
    _publish_step(run, receipt)

    sync()
    began = time.monotonic()
    optimizer.step()
    sync()
    receipt["update_seconds"] = time.monotonic() - began
    receipt["status"] = "UPDATE_CONFIRMED"
    receipt["update_completed"] = True
    receipt["update_completion_known"] = True
    receipt["update_confirmed_unix"] = time.time()
    _publish_step(run, receipt)

    evidence = validate_optimizer_step(model, optimizer, step_before)
    receipt["gradient_and_update"] = evidence
    receipt["validation_completed"] = True
    receipt["status"] = "VALIDATION_CONFIRMED"
    _publish_step(run, receipt)

    memory = resource(f"step-{ordinal}")
    receipt["memory"] = memory
    receipt["resource_completed"] = True
    receipt["status"] = "VALIDATED"
    _publish_step(run, receipt)
    return receipt


def validate_frozen_originals(model: Any, originals: dict[str, Any]) -> dict[str, Any]:
    named = dict(model.named_parameters())
    current_originals = {name for name in named if "lora_" not in name}
    if current_originals != set(originals):
        raise MechanicsError("original parameter keys changed")
    total = 0
    after_hashes = {}
    for name, prior in originals.items():
        parameter = named[name]
        if (
            id(parameter) != prior["object_id"]
            or str(parameter.dtype) != prior["dtype"]
            or list(parameter.shape) != prior["shape"]
        ):
            raise MechanicsError(f"original parameter identity changed: {name}")
        if parameter.requires_grad or parameter.grad is not None:
            raise MechanicsError(f"original parameter gained a gradient: {name}")
        digest = _parameter_digest(parameter)
        if digest != prior["sha256"]:
            raise MechanicsError(f"original parameter bytes changed: {name}")
        after_hashes[name] = digest
        total += parameter.numel()
    return {
        "count": len(originals),
        "numel": total,
        "identities_unchanged": True,
        "bytes_unchanged": True,
        "gradients_absent": True,
        "before_sha256": {name: value["sha256"] for name, value in originals.items()},
        "after_sha256": after_hashes,
    }


def compare_adapter_states(expected: dict[str, Any], actual: dict[str, Any]) -> None:
    if set(expected) != set(actual):
        raise MechanicsError("adapter state keys differ")
    for name in sorted(expected):
        left = expected[name].detach().cpu().contiguous()
        right = actual[name].detach().cpu().contiguous()
        if left.shape != right.shape:
            raise MechanicsError(f"adapter state shape differs: {name}")
        if left.dtype != right.dtype:
            raise MechanicsError(f"adapter state dtype differs: {name}")
        if _parameter_digest(left) != _parameter_digest(right):
            raise MechanicsError(f"adapter state bytes differ: {name}")


def archive_file(
    source: Path,
    archive_dir: Path,
    *,
    max_part_bytes: int = ARCHIVE_PART_BYTES,
) -> dict[str, Any]:
    source = Path(source)
    archive_dir = Path(archive_dir)
    if max_part_bytes <= 0:
        raise ValueError("max_part_bytes must be positive")
    archive_dir.mkdir(parents=False, exist_ok=False)
    parts = []
    total = 0
    full_digest = hashlib.sha256()
    with source.open("rb") as stream:
        for index, body in enumerate(iter(lambda: stream.read(max_part_bytes), b"")):
            name = f"adapter_model.safetensors.part-{index:03d}"
            path = archive_dir / name
            with path.open("xb") as output:
                output.write(body)
                output.flush()
                os.fsync(output.fileno())
            digest = _sha_bytes(body)
            full_digest.update(body)
            total += len(body)
            parts.append(
                {"index": index, "name": name, "bytes": len(body), "sha256": digest}
            )
    if not parts:
        raise MechanicsError("adapter archive source is empty")
    return {
        "schema_version": 1,
        "source_name": source.name,
        "source_bytes": total,
        "source_sha256": full_digest.hexdigest(),
        "maximum_part_bytes": max_part_bytes,
        "parts": parts,
        "reconstruction": "ordered byte concatenation",
    }


def reconstruct_archive(
    manifest: dict[str, Any], archive_dir: Path, destination: Path
) -> dict[str, Any]:
    archive_dir = Path(archive_dir)
    destination = Path(destination)
    temporary = destination.with_name(f".{destination.name}.{os.getpid()}.tmp")
    digest = hashlib.sha256()
    total = 0
    try:
        with temporary.open("xb") as output:
            for expected_index, part in enumerate(manifest.get("parts", [])):
                if part.get("index") != expected_index:
                    raise MechanicsError("archive part order differs")
                body = (archive_dir / part["name"]).read_bytes()
                if len(body) != part["bytes"] or _sha_bytes(body) != part["sha256"]:
                    raise MechanicsError(f"archive part differs: {part['name']}")
                if len(body) > manifest["maximum_part_bytes"]:
                    raise MechanicsError(f"archive part exceeds bound: {part['name']}")
                output.write(body)
                digest.update(body)
                total += len(body)
            output.flush()
            os.fsync(output.fileno())
        if total != manifest.get("source_bytes"):
            raise MechanicsError("archive reconstructed size differs")
        if digest.hexdigest() != manifest.get("source_sha256"):
            raise MechanicsError("archive reconstructed hash differs")
        os.replace(temporary, destination)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return {"bytes": total, "sha256": digest.hexdigest(), "exact": True}


def _package_versions() -> dict[str, str]:
    return {name: importlib.metadata.version(name) for name in PACKAGE_NAMES}


def _root_path(root: Path, canonical: Path) -> Path:
    return Path(root) / canonical.relative_to(ROOT)


def validate_artifacts(
    *, root: Path = ROOT, verify_base_files: bool = False
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Bind accepted data, exact recorded row, tokenizer files, code and base."""
    root = Path(root).resolve()
    hashes = {}
    for relative, expected in EXPECTED_SHA256.items():
        path = root / relative
        actual = _sha_file(path)
        if actual != expected:
            raise MechanicsError(f"frozen artifact differs: {relative}")
        hashes[relative] = actual
    try:
        accepted_review = subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "show",
                f"{ACCEPTED_COMMIT}:results/source-interpreter/mechanics-review-astra.md",
            ],
            check=True,
            capture_output=True,
        ).stdout
    except subprocess.CalledProcessError as exc:
        raise MechanicsError("accepted mechanics review blob is unavailable") from exc
    if _sha_bytes(accepted_review) != ACCEPTED_REVIEW_SHA256:
        raise MechanicsError("accepted mechanics review blob differs")
    hashes[f"{ACCEPTED_COMMIT}:mechanics-review-astra.md"] = ACCEPTED_REVIEW_SHA256
    review_relative = "results/source-interpreter/mechanics-review-astra.md"
    hashes[review_relative] = _sha_file(root / review_relative)
    preview_path = root / PREVIEW_PATH.relative_to(ROOT)
    inputs_path = root / INPUTS_PATH.relative_to(ROOT)
    base_assets_path = root / BASE_ASSETS_PATH.relative_to(ROOT)
    preview = _read_json(preview_path, "source-interpreter preview")
    manifest = _read_json(inputs_path, "accepted input manifest")
    base_assets = _read_json(base_assets_path, "base asset receipt")
    required_preview = {
        "schema_version": 1,
        "kind": "source-interpreter-cpu-preview",
        "status": "PASS",
        "fit_on": "none",
        "model_calls": 0,
        "model_loaded": False,
        "gpu_used": False,
        "documents": 6,
        "rows": 18,
        "splits": {"fit": 6, "dev": 0, "withheld": 0},
    }
    for key, expected in required_preview.items():
        if preview.get(key) != expected:
            raise MechanicsError(f"preview field is not qualified: {key}")
    if (
        manifest.get("status") != "LABELS_ACCEPTED_CPU_PREVIEW_PENDING"
        or manifest.get("documents") is None
        or len(manifest["documents"]) != 6
        or manifest.get("query_rows") != 18
    ):
        raise MechanicsError("accepted input manifest is not qualified")
    source = _source_module()
    if source.SYSTEM_PROMPT != SYSTEM_PROMPT or source.USER_PROMPT != USER_PROMPT:
        raise MechanicsError("source-interpreter prompt code differs")
    paths = [root / entry["path"] for entry in manifest["documents"]]
    documents, input_receipts = source.load_documents(paths)
    if preview.get("inputs") != input_receipts:
        raise MechanicsError("preview input receipts differ from current inputs")
    for document, receipt, entry in zip(
        documents, input_receipts, manifest["documents"], strict=True
    ):
        validate_training_row(
            preview["row_receipts"][
                next(
                    index
                    for index, candidate in enumerate(preview["row_receipts"])
                    if candidate["conversation_id"] == document["conversation_id"]
                    and candidate["query_index"] == 0
                )
            ],
            document=document,
            input_receipt=receipt,
            manifest_entry=entry,
            root=root,
        )
    row = preview["row_receipts"][14]
    for key, expected in EXPECTED_ROW.items():
        if row.get(key) != expected:
            raise MechanicsError(f"registered longest-row field differs: {key}")
    if row["full_length"] != max(
        candidate["full_length"] for candidate in preview["row_receipts"]
    ):
        raise MechanicsError("registered row is no longer the longest preview row")
    document_index = next(
        index
        for index, value in enumerate(documents)
        if value["conversation_id"] == EXPECTED_ROW["conversation_id"]
    )
    causal = validate_training_row(
        row,
        document=documents[document_index],
        input_receipt=input_receipts[document_index],
        manifest_entry=manifest["documents"][document_index],
        root=root,
    )
    if preview.get("code_sha256") != {
        "src/stencil/focus/source_interpreter.py": EXPECTED_SHA256[
            "src/stencil/focus/source_interpreter.py"
        ]
    }:
        raise MechanicsError("preview code binding differs")
    if preview.get("environment", {}).get("distributions") != _package_versions():
        raise MechanicsError("installed package versions differ from the preview")
    environment = preview["environment"]
    if (
        Path(sys.executable) != Path(environment.get("sys_executable", ""))
        or Path(sys.executable).resolve()
        != Path(environment.get("resolved_executable", ""))
        or Path(sys.prefix) != Path(environment.get("sys_prefix", ""))
    ):
        raise MechanicsError("Python interpreter differs from the preview")
    tokenizer = preview.get("tokenizer", {})
    if (
        tokenizer.get("verified_original_state") is not True
        or tokenizer.get("base_assets_receipt_sha256")
        != EXPECTED_SHA256[
            "results/coding-auto-reasoning/research-next/base-assets.json"
        ]
        or tokenizer.get("eos_token_id") != EXPECTED_ROW["eos_token_id"]
    ):
        raise MechanicsError("preview tokenizer binding differs")
    base_files = base_assets.get("files")
    if (
        base_assets.get("status") != "LOCAL_BASE_BYTES_VERIFIED"
        or type(base_files) is not dict
        or not base_files
    ):
        raise MechanicsError("base asset receipt is not qualified")
    checked_files = {}
    for relative, receipt in base_files.items():
        path = root / relative
        if not path.is_file() or path.stat().st_size != receipt.get("bytes"):
            raise MechanicsError(f"base asset size differs: {relative}")
        if receipt.get("matches_historical_original") is not True:
            raise MechanicsError(f"base asset lacks original binding: {relative}")
        if verify_base_files and _sha_file(path) != receipt.get("sha256"):
            raise MechanicsError(f"base asset bytes differ: {relative}")
        checked_files[relative] = receipt["sha256"]
    asset_hashes = tokenizer.get("asset_sha256")
    for name, digest in asset_hashes.items():
        relative = f"models/qwen3-4b-hf/{name}"
        if checked_files.get(relative) != digest:
            raise MechanicsError(f"tokenizer/base receipt differs: {name}")
    bindings = {
        "artifact_sha256": hashes,
        "input_receipts": input_receipts,
        "selected_row_index": 14,
        "selected_row": {**EXPECTED_ROW, **causal},
        "preview_tokenizer": tokenizer,
        "base_assets": {
            "receipt_sha256": hashes[
                "results/coding-auto-reasoning/research-next/base-assets.json"
            ],
            "file_sha256": checked_files,
            "all_file_bytes_verified": verify_base_files,
        },
        "packages": _package_versions(),
        "runner_sha256": _sha_file(root / "scripts/source_interpreter_mechanics.py"),
        "test_sha256": _sha_file(root / "tests/test_source_interpreter_mechanics.py"),
    }
    return bindings, row


def _host_memory() -> dict[str, int | None]:
    values = {}
    try:
        for line in Path("/proc/meminfo").read_text(encoding="ascii").splitlines():
            key, rest = line.split(":", 1)
            if key in {"MemAvailable", "SwapTotal", "SwapFree"}:
                values[key] = int(rest.split()[0]) * 1024
    except (OSError, ValueError, IndexError):
        pass
    return {
        "host_available_bytes": values.get("MemAvailable"),
        "swap_total_bytes": values.get("SwapTotal"),
        "swap_free_bytes": values.get("SwapFree"),
    }


def _resource_receipt(stage: str, torch: Any = None) -> dict[str, Any]:
    receipt: dict[str, Any] = {"stage": stage, "unix": time.time(), **_host_memory()}
    if torch is None or not torch.cuda.is_available():
        receipt["cuda"] = None
        return receipt
    free, total = torch.cuda.mem_get_info()
    properties = torch.cuda.get_device_properties(0)
    receipt["cuda"] = {
        "device": torch.cuda.current_device(),
        "name": properties.name,
        "capability": list(torch.cuda.get_device_capability(0)),
        "device_total_bytes": properties.total_memory,
        "torch_mem_get_info_free_bytes": free,
        "torch_mem_get_info_total_bytes": total,
        "allocated_bytes": torch.cuda.memory_allocated(),
        "reserved_bytes": torch.cuda.memory_reserved(),
        "maximum_allocated_bytes": torch.cuda.max_memory_allocated(),
        "maximum_reserved_bytes": torch.cuda.max_memory_reserved(),
        "accounting_note": (
            "Torch device and allocator accounting on unified memory; not a "
            "separate nvidia-smi memory pool."
        ),
    }
    return receipt


def _record_stage(
    run: Path,
    stage_receipts: list[dict[str, Any]],
    stage: str,
    *,
    torch: Any = None,
    **details: Any,
) -> dict[str, Any]:
    receipt = {
        "ordinal": len(stage_receipts),
        "stage": stage,
        "monotonic": time.monotonic(),
        "resource": _resource_receipt(stage, torch),
        **details,
    }
    stage_receipts.append(receipt)
    _append_json(run / "stages.jsonl", receipt)
    _write_json(run / "current-stage.json", receipt)
    return receipt


def _guard_deadline(deadline: float, stage: str) -> None:
    if time.monotonic() >= deadline:
        raise MechanicsError(f"working deadline reached before {stage}")


def _adapter_load_receipt(load_result: Any) -> dict[str, Any]:
    missing = list(getattr(load_result, "missing_keys", []))
    unexpected = list(getattr(load_result, "unexpected_keys", []))
    missing_adapter = [key for key in missing if "lora_" in key]
    unexpected_adapter = [key for key in unexpected if "lora_" in key]
    if missing_adapter or unexpected_adapter:
        raise MechanicsError(
            "reloaded adapter reports missing or unexpected adapter keys"
        )
    return {
        "reported_missing_keys": missing,
        "reported_unexpected_keys": unexpected,
        "missing_adapter_keys": missing_adapter,
        "unexpected_adapter_keys": unexpected_adapter,
    }


def _state_receipt(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "originals": state["originals"],
        "adapters": state["adapters"],
    }


def run_measurement(run: Path, *, deadline_monotonic: float) -> int:
    """Child body. This is the only path that imports or loads ML runtimes."""
    run = Path(run)
    stage_receipts: list[dict[str, Any]] = []
    step_receipts: list[dict[str, Any]] = []
    resource_receipts: list[dict[str, Any]] = []
    child_started = time.monotonic()
    bindings: dict[str, Any] = {}
    model = None
    optimizer = None
    torch = None
    _write_json(
        run / "child-start.json",
        {
            "schema_version": 1,
            "kind": "source-interpreter-mechanics-child-start",
            "pid": os.getpid(),
            "started_unix": time.time(),
            "started_monotonic": child_started,
            "working_deadline_monotonic": deadline_monotonic,
            "status": "INCOMPLETE",
        },
    )
    try:
        _guard_deadline(deadline_monotonic, "artifact qualification")
        stage_started = time.monotonic()
        bindings, row = validate_artifacts(verify_base_files=True)
        resource_receipts.append(_resource_receipt("startup"))
        _record_stage(
            run,
            stage_receipts,
            "artifacts-qualified",
            elapsed_seconds=time.monotonic() - stage_started,
            bindings=bindings,
        )

        _guard_deadline(deadline_monotonic, "runtime import")
        stage_started = time.monotonic()
        import gc

        import peft
        import torch as torch_module
        import transformers
        from peft import LoraConfig, get_peft_model, get_peft_model_state_dict
        from transformers import AutoModelForCausalLM

        torch = torch_module
        if not torch.cuda.is_available():
            raise MechanicsError("CUDA is unavailable")
        torch.manual_seed(SETTINGS["seed"])
        torch.cuda.manual_seed_all(SETTINGS["seed"])
        source = _source_module()
        tokenizer = source.load_tokenizer()
        tokenizer_state = source._tokenizer_state(tokenizer)
        if tokenizer_state != bindings["preview_tokenizer"]["state"]:
            raise MechanicsError("loaded tokenizer state differs from preview")
        if (
            _sha_bytes(_json_bytes(tokenizer_state))
            != bindings["preview_tokenizer"]["state_sha256"]
        ):
            raise MechanicsError("loaded tokenizer state hash differs from preview")
        _record_stage(
            run,
            stage_receipts,
            "tokenizer-qualified",
            torch=torch,
            elapsed_seconds=time.monotonic() - stage_started,
        )

        _guard_deadline(deadline_monotonic, "model load")
        stage_started = time.monotonic()
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_PATH,
            local_files_only=True,
            dtype=torch.bfloat16,
            attn_implementation="sdpa",
            device_map={"": "cuda"},
            low_cpu_mem_usage=True,
        )
        model.config.use_cache = False
        model.gradient_checkpointing_enable(
            gradient_checkpointing_kwargs={"use_reentrant": False}
        )
        lora = LoraConfig(
            r=SETTINGS["rank"],
            lora_alpha=SETTINGS["alpha"],
            lora_dropout=SETTINGS["dropout"],
            bias=SETTINGS["bias"],
            task_type="CAUSAL_LM",
            target_modules=["q_proj", "v_proj"],
            inference_mode=False,
        )
        model = get_peft_model(model, lora, adapter_name="default")
        trainable = {
            name: parameter
            for name, parameter in model.named_parameters()
            if parameter.requires_grad
        }
        trainable_count = sum(value.numel() for value in trainable.values())
        if trainable_count != SETTINGS["trainable_parameters"]:
            raise MechanicsError(f"unexpected trainable count: {trainable_count}")
        if not trainable or any(
            "lora_" not in name or value.dtype != torch.float32
            for name, value in trainable.items()
        ):
            raise MechanicsError("trainable adapter names or dtypes differ")
        initial_state = capture_parameter_state(model)
        optimizer = torch.optim.AdamW(
            list(trainable.values()),
            lr=SETTINGS["learning_rate"],
            betas=tuple(SETTINGS["betas"]),
            eps=SETTINGS["epsilon"],
            weight_decay=SETTINGS["weight_decay"],
        )
        input_ids = torch.tensor([row["input_ids"]], dtype=torch.long, device="cuda")
        attention_mask = torch.tensor(
            [row["attention_mask"]], dtype=torch.long, device="cuda"
        )
        labels = torch.tensor([row["labels"]], dtype=torch.long, device="cuda")
        resource_receipts.append(_resource_receipt("after-load", torch))
        _record_stage(
            run,
            stage_receipts,
            "model-loaded",
            torch=torch,
            trainable_parameters=trainable_count,
            trainable_names=sorted(trainable),
            original_state=_state_receipt(initial_state),
            elapsed_seconds=time.monotonic() - stage_started,
        )

        model.train()
        for ordinal in range(SETTINGS["updates"]):
            _guard_deadline(deadline_monotonic, f"update {ordinal}")
            receipt = perform_optimizer_step(
                run,
                ordinal=ordinal,
                model=model,
                optimizer=optimizer,
                loss_call=lambda: (
                    model(
                        input_ids=input_ids,
                        attention_mask=attention_mask,
                        labels=labels,
                        use_cache=False,
                    ).loss
                ),
                sync=torch.cuda.synchronize,
                resource=lambda stage: _resource_receipt(stage, torch),
                supervised_tokens=len(row["loss_positions"]),
                label_positions=row["loss_positions"],
                causal_logit_positions=list(
                    range(row["prefix_length"] - 1, row["full_length"] - 1)
                ),
            )
            step_receipts.append(receipt)
            resource_receipts.append(receipt["memory"])

        _guard_deadline(deadline_monotonic, "adapter save")
        stage_started = time.monotonic()
        saved_state = {
            name: value.detach().cpu().clone()
            for name, value in get_peft_model_state_dict(
                model, adapter_name="default"
            ).items()
        }
        if not saved_state or any(
            value.dtype != torch.float32 for value in saved_state.values()
        ):
            raise MechanicsError("saved adapter state is not complete FP32 state")
        adapter_dir = run / "adapter"
        model.save_pretrained(
            adapter_dir,
            safe_serialization=True,
            selected_adapters=["default"],
        )
        weights_path = adapter_dir / "adapter_model.safetensors"
        config_path = adapter_dir / "adapter_config.json"
        if not weights_path.is_file() or not config_path.is_file():
            raise MechanicsError("standard PEFT save is incomplete")
        archive_manifest = archive_file(weights_path, run / "archive")
        _write_json(run / "archive-manifest.json", archive_manifest)
        reconstructed_dir = run / "reconstructed-adapter"
        reconstructed_dir.mkdir(parents=False, exist_ok=False)
        config_copy = reconstructed_dir / "adapter_config.json"
        shutil.copyfile(config_path, config_copy)
        if _sha_file(config_copy) != _sha_file(config_path):
            raise MechanicsError("adapter configuration copy differs")
        reconstruction = reconstruct_archive(
            archive_manifest,
            run / "archive",
            reconstructed_dir / "adapter_model.safetensors",
        )
        resource_receipts.append(_resource_receipt("save", torch))
        _record_stage(
            run,
            stage_receipts,
            "adapter-saved",
            torch=torch,
            elapsed_seconds=time.monotonic() - stage_started,
        )

        _guard_deadline(deadline_monotonic, "adapter reload")
        stage_started = time.monotonic()
        load_result = model.load_adapter(
            reconstructed_dir,
            adapter_name="roundtrip",
            is_trainable=False,
            autocast_adapter_dtype=True,
            local_files_only=True,
        )
        load_receipt = _adapter_load_receipt(load_result)
        roundtrip_state = {
            name: value.detach().cpu().clone()
            for name, value in get_peft_model_state_dict(
                model, adapter_name="roundtrip"
            ).items()
        }
        compare_adapter_states(saved_state, roundtrip_state)
        model.set_adapter("roundtrip", inference_mode=True)
        model.eval()
        with torch.no_grad():
            post_loss = model(
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=labels,
                use_cache=False,
            ).loss
        torch.cuda.synchronize()
        post_loss_value = float(post_loss.detach().float().item())
        if not math.isfinite(post_loss_value) or post_loss_value <= 0:
            raise MechanicsError("post-reload loss is not positive finite")
        frozen = validate_frozen_originals(model, initial_state["originals"])
        resource_receipts.append(_resource_receipt("reload", torch))
        adapter_receipt = {
            "saved_state_keys": sorted(saved_state),
            "saved_state": {
                name: {
                    "shape": list(value.shape),
                    "dtype": str(value.dtype),
                    "numel": value.numel(),
                    "sha256": _parameter_digest(value),
                }
                for name, value in saved_state.items()
            },
            "weights_bytes": weights_path.stat().st_size,
            "weights_sha256": _sha_file(weights_path),
            "config_sha256": _sha_file(config_path),
            "reconstructed_config_sha256": _sha_file(config_copy),
            "archive": archive_manifest,
            "reconstruction": reconstruction,
            "load": load_receipt,
            "exact": True,
        }
        _record_stage(
            run,
            stage_receipts,
            "adapter-reloaded",
            torch=torch,
            elapsed_seconds=time.monotonic() - stage_started,
        )

        _guard_deadline(deadline_monotonic, "cleanup")
        stage_started = time.monotonic()
        post_loss = input_ids = attention_mask = labels = None
        del optimizer
        optimizer = None
        del model
        model = None
        gc.collect()
        torch.cuda.empty_cache()
        resource_receipts.append(_resource_receipt("exit", torch))
        _record_stage(
            run,
            stage_receipts,
            "cleanup-complete",
            torch=torch,
            elapsed_seconds=time.monotonic() - stage_started,
        )
        _guard_deadline(deadline_monotonic, "terminal receipt")
        timed = step_receipts[1:]
        timed_totals = [
            item["forward_seconds"] + item["backward_seconds"] + item["update_seconds"]
            for item in timed
        ]
        result = {
            "schema_version": 1,
            "kind": "source-interpreter-mechanics-result",
            "status": "COMPLETE",
            "mechanical_pass": True,
            "bindings": bindings,
            "settings": SETTINGS,
            "runtime": {
                "python": sys.version,
                "packages": {
                    "torch": torch.__version__,
                    "transformers": transformers.__version__,
                    "peft": peft.__version__,
                },
            },
            "stage_receipts": stage_receipts,
            "step_receipts": step_receipts,
            "original_parameters": {**frozen, "unchanged": True},
            "adapter_roundtrip": adapter_receipt,
            "resource_receipts": resource_receipts,
            "timings": {
                "timed_update_seconds": timed_totals,
                "timed_update_mean_seconds": sum(timed_totals) / len(timed_totals),
                "timed_update_max_seconds": max(timed_totals),
                "total_seconds": time.monotonic() - child_started,
            },
            "post_reload": {
                "loss": post_loss_value,
                "optimizer_update": False,
                "adapter": "roundtrip",
                "inference_mode": True,
                "evaluation_mode": True,
                "no_grad": True,
            },
        }
        validate_completion(result)
        _write_json(run / "result.json", result)
        return 0
    except BaseException as exc:
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise
        try:
            if model is not None:
                del model
            if optimizer is not None:
                del optimizer
            if torch is not None and torch.cuda.is_available():
                torch.cuda.empty_cache()
            resource_receipts.append(_resource_receipt("incomplete-exit", torch))
        except Exception:
            pass
        durable_steps = _current_step_receipts(run)
        result = {
            "schema_version": 1,
            "kind": "source-interpreter-mechanics-result",
            "status": "INCOMPLETE",
            "mechanical_pass": False,
            "error": f"{type(exc).__name__}: {exc}",
            "bindings": bindings,
            "settings": SETTINGS,
            "stage_receipts": stage_receipts,
            "step_receipts": durable_steps,
            "update_accounting": _partial_update_counts(run),
            "resource_receipts": resource_receipts,
            "timings": {"total_seconds": time.monotonic() - child_started},
        }
        _write_json(run / "result.json", result)
        return 2


def validate_completion(result: dict[str, Any]) -> dict[str, int]:
    if result.get("status") != "COMPLETE" or result.get("mechanical_pass") is not True:
        raise MechanicsError("child result is not COMPLETE")
    for key in (
        "bindings",
        "settings",
        "stage_receipts",
        "step_receipts",
        "original_parameters",
        "adapter_roundtrip",
        "resource_receipts",
        "timings",
        "post_reload",
    ):
        if not result.get(key):
            raise MechanicsError(f"complete result lacks {key}")
    steps = result["step_receipts"]
    if (
        type(steps) is not list
        or len(steps) != 4
        or [item.get("ordinal") for item in steps] != list(range(4))
        or [item.get("classification") for item in steps]
        != ["warm-up", "timed", "timed", "timed"]
        or any(item.get("update_completed") is not True for item in steps)
    ):
        raise MechanicsError(
            "complete result must contain four updates and one warm-up"
        )
    if result["original_parameters"].get("unchanged") is not True:
        raise MechanicsError("complete result lacks frozen-original proof")
    if result["adapter_roundtrip"].get("exact") is not True:
        raise MechanicsError("complete result lacks exact adapter roundtrip")
    if result["post_reload"].get("optimizer_update") is not False:
        raise MechanicsError("post-reload evaluation performed an update")
    return {"updates": 4, "warm_up_updates": 1, "timed_updates": 3}


def register_pid(pid: int, *, registry: Path = OWNED_PIDS) -> None:
    with Path(registry).open("a", encoding="ascii") as stream:
        stream.write(f"{pid}\n")
        stream.flush()
        os.fsync(stream.fileno())


def _partial_files(run: Path) -> list[str]:
    return sorted(
        str(path.relative_to(run))
        for path in Path(run).rglob("*")
        if path.is_file() and path.name != "lifecycle.json"
    )


def _current_step_receipts(run: Path) -> list[dict[str, Any]]:
    receipts = []
    for path in sorted(Path(run).glob("step-*.json")):
        try:
            receipts.append(_read_json(path, "partial step receipt"))
        except MechanicsError:
            continue
    return receipts


def _partial_update_counts(run: Path) -> dict[str, Any]:
    confirmed = []
    validated = []
    pending_or_unknown = []
    for path in sorted(Path(run).glob("step-*.json")):
        try:
            value = _read_json(path, "partial step receipt")
        except MechanicsError:
            pending_or_unknown.append(path.name)
            continue
        if (
            value.get("update_completed") is True
            and value.get("update_completion_known", True) is True
        ):
            confirmed.append(value)
            if value.get("validation_completed") is True:
                validated.append(value)
        elif value.get("update_completion_known") is False:
            pending_or_unknown.append(value.get("ordinal", path.name))
    exact = not pending_or_unknown
    return {
        "confirmed_updates": len(confirmed),
        "warm_up_updates_confirmed": sum(
            value.get("classification") == "warm-up" for value in confirmed
        ),
        "timed_updates_confirmed": sum(
            value.get("classification") == "timed" for value in confirmed
        ),
        "validated_updates": len(validated),
        "pending_or_unknown_steps": pending_or_unknown,
        "update_count_is_exact": exact,
    }


def _stop_owned_child(child: Any, *, total_deadline: float, clock: Any) -> bool:
    if child.poll() is not None:
        return True
    child.terminate()
    try:
        child.wait(timeout=max(0.0, min(5.0, total_deadline - clock())))
    except subprocess.TimeoutExpired:
        child.kill()
        try:
            child.wait(timeout=max(0.0, total_deadline - clock()))
        except subprocess.TimeoutExpired:
            pass
    return child.poll() is not None


def supervise_child(
    run: Path,
    command: list[str],
    *,
    run_flag: Path = RUN_FLAG,
    pid_registry: Path = OWNED_PIDS,
    reservation_seconds: float = RESERVATION_SECONDS,
    termination_reserve_seconds: float = TERMINATION_RESERVE_SECONDS,
    started_monotonic: float | None = None,
    clock=time.monotonic,
    wall_clock=time.time,
    popen=subprocess.Popen,
    register=register_pid,
) -> tuple[int, dict[str, Any]]:
    """Own one exact child until exit, enforcing work and cleanup deadlines."""
    run = Path(run)
    started = clock() if started_monotonic is None else started_monotonic
    work_deadline = started + reservation_seconds - termination_reserve_seconds
    total_deadline = started + reservation_seconds
    child = None
    child_exit_confirmed = False
    timed_out = False
    termination_requested = False
    termination_reason = None
    launch_error = None
    stdout_path = run / "child.stdout.log"
    stderr_path = run / "child.stderr.log"
    try:
        _write_json(run / "child-command.json", list(command))
        with stdout_path.open("xb") as stdout, stderr_path.open("xb") as stderr:
            try:
                child = popen(
                    list(command),
                    stdin=subprocess.DEVNULL,
                    stdout=stdout,
                    stderr=stderr,
                    cwd=str(ROOT),
                    start_new_session=False,
                )
                register(child.pid, registry=pid_registry)
                _write_json(
                    run / "child-launch.json",
                    {
                        "pid": child.pid,
                        "command": list(command),
                        "launched_unix": wall_clock(),
                        "work_deadline_monotonic": work_deadline,
                        "total_deadline_monotonic": total_deadline,
                    },
                )
                try:
                    child.wait(timeout=max(0.0, work_deadline - clock()))
                except subprocess.TimeoutExpired:
                    timed_out = True
                    termination_requested = True
                    termination_reason = "working-deadline"
                    child_exit_confirmed = _stop_owned_child(
                        child, total_deadline=total_deadline, clock=clock
                    )
                if child.poll() is not None:
                    child_exit_confirmed = True
            except Exception as exc:
                launch_error = f"{type(exc).__name__}: {exc}"
                if child is not None and child.poll() is None:
                    termination_requested = True
                    termination_reason = "supervisor-error"
                    child_exit_confirmed = _stop_owned_child(
                        child, total_deadline=total_deadline, clock=clock
                    )
                elif child is not None:
                    child_exit_confirmed = True
    except Exception as exc:
        launch_error = f"{type(exc).__name__}: {exc}"
        if child is not None and child.poll() is None:
            termination_requested = True
            termination_reason = "supervisor-error"
            child_exit_confirmed = _stop_owned_child(
                child, total_deadline=total_deadline, clock=clock
            )
        elif child is not None:
            child_exit_confirmed = True
    finally:
        child_exit_monotonic = clock()
        child_exit_code = child.returncode if child_exit_confirmed else None
        status = "INCOMPLETE_CHILD"
        exit_code = 2
        completion = None
        if timed_out:
            status = "INCOMPLETE_TIMEOUT"
        elif launch_error is not None:
            status = "INCOMPLETE_LAUNCH"
        elif child_exit_confirmed and child_exit_code == 0:
            try:
                completion = validate_completion(
                    _read_json(run / "result.json", "child result")
                )
                if child_exit_monotonic <= work_deadline:
                    status = "COMPLETE"
                    exit_code = 0
                else:
                    status = "INCOMPLETE_DEADLINE"
            except Exception as exc:
                launch_error = f"{type(exc).__name__}: {exc}"
        partial_counts = _partial_update_counts(run)
        confirmed_updates = (
            completion["updates"] if completion else partial_counts["confirmed_updates"]
        )
        warm_up_confirmed = (
            completion["warm_up_updates"]
            if completion
            else partial_counts["warm_up_updates_confirmed"]
        )
        timed_confirmed = (
            completion["timed_updates"]
            if completion
            else partial_counts["timed_updates_confirmed"]
        )
        count_is_exact = (
            completion is not None or partial_counts["update_count_is_exact"]
        )
        lifecycle = {
            "schema_version": 1,
            "kind": "source-interpreter-mechanics-lifecycle",
            "status": "FINALIZING",
            "candidate_status": status,
            "started_monotonic": started,
            "child_exit_monotonic": child_exit_monotonic,
            "ended_monotonic": None,
            "elapsed_seconds": None,
            "ended_unix": None,
            "reservation_seconds": reservation_seconds,
            "working_seconds": reservation_seconds - termination_reserve_seconds,
            "termination_reserve_seconds": termination_reserve_seconds,
            "work_deadline_monotonic": work_deadline,
            "total_deadline_monotonic": total_deadline,
            "child_pid": child.pid if child is not None else None,
            "child_exit_code": child_exit_code,
            "child_exit_confirmed": child_exit_confirmed,
            "termination_requested": termination_requested,
            "termination_reason": termination_reason,
            "error": launch_error,
            "partial_files": _partial_files(run),
            "updates": confirmed_updates if count_is_exact else None,
            "warm_up_updates": warm_up_confirmed if count_is_exact else None,
            "timed_updates": timed_confirmed if count_is_exact else None,
            "confirmed_updates": confirmed_updates,
            "warm_up_updates_confirmed": warm_up_confirmed,
            "timed_updates_confirmed": timed_confirmed,
            "validated_updates": (
                completion["updates"]
                if completion
                else partial_counts["validated_updates"]
            ),
            "pending_or_unknown_steps": partial_counts["pending_or_unknown_steps"],
            "update_count_is_exact": count_is_exact,
            "run_flag_cleared": False,
            "finalization_within_total_deadline": None,
            "receipt_publication_tail": None,
        }
        _write_json(run / "lifecycle.json", lifecycle)
        if child_exit_confirmed or child is None:
            Path(run_flag).unlink(missing_ok=True)
            lifecycle["run_flag_cleared"] = True
        finalized_monotonic = clock()
        within_total = finalized_monotonic <= total_deadline
        if status == "COMPLETE" and not within_total:
            status = "INCOMPLETE_FINALIZATION_DEADLINE"
            exit_code = 2
        lifecycle["status"] = status
        lifecycle["ended_monotonic"] = finalized_monotonic
        lifecycle["elapsed_seconds"] = finalized_monotonic - started
        lifecycle["ended_unix"] = wall_clock()
        lifecycle["finalization_within_total_deadline"] = within_total
        lifecycle["receipt_publication_tail"] = {
            "starts_monotonic": finalized_monotonic,
            "included_in_elapsed": False,
            "bounded_by_outer_process_observation": True,
            "description": (
                "The final lifecycle JSON fsync occurs after its last self-observed "
                "monotonic sample."
            ),
        }
        _write_json(run / "lifecycle.json", lifecycle)
    return exit_code, lifecycle


def make_plan(run: Path) -> dict[str, Any]:
    run = Path(run)
    return {
        "schema_version": 1,
        "kind": "source-interpreter-mechanics-launch-plan",
        "execute": False,
        "run_dir": str(run),
        "input_manifest": str(INPUTS_PATH),
        "preview": str(PREVIEW_PATH),
        "model": str(MODEL_PATH),
        "selected_row_index": 14,
        "settings": SETTINGS,
        "reservation_seconds": int(RESERVATION_SECONDS),
        "working_seconds": int(WORKING_SECONDS),
        "termination_reserve_seconds": int(TERMINATION_RESERVE_SECONDS),
        "child_command": [
            str(ROOT / ".venv/bin/python"),
            str(Path(__file__).resolve()),
            "--_child",
            "--run-dir",
            str(run),
            "--deadline-monotonic",
            "<set-by-supervisor>",
        ],
        "dry_run_loads_model": False,
        "dry_run_uses_cuda": False,
        "dry_run_starts_child": False,
    }


def _active_flags(root: Path = ROOT) -> list[Path]:
    return sorted(Path(root).joinpath("results").rglob("RUNNING.flag"))


def _command(command: list[str], *, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(command, check=check, capture_output=True)


def _qualify_environment() -> dict[str, Any]:
    flags = _active_flags()
    if flags:
        raise MechanicsError(f"an active run flag exists: {flags[0]}")
    gpu = _command(["nvidia-smi", "--query-compute-apps=pid", "--format=csv,noheader"])
    if gpu.stdout.strip():
        raise MechanicsError("a GPU compute process is active")
    for relative in BOUND_FILES:
        tracked = _command(
            ["git", "-C", str(ROOT), "ls-files", "--error-unmatch", "--", relative],
            check=False,
        )
        dirty = _command(
            [
                "git",
                "-C",
                str(ROOT),
                "status",
                "--porcelain=v1",
                "--untracked-files=all",
                "--",
                relative,
            ],
            check=False,
        )
        if tracked.returncode != 0 or dirty.stdout.strip():
            raise MechanicsError(f"bound file is dirty or untracked: {relative}")
    head = (
        _command(["git", "-C", str(ROOT), "rev-parse", "HEAD"]).stdout.decode().strip()
    )
    if len(head) != 40:
        raise MechanicsError("current git HEAD could not be resolved")
    return {"git_head": head, "gpu_compute_processes": [], "active_flags": []}


def _acquire_review_lock():
    handle = REVIEW_LOCK.open("a+", encoding="utf-8")
    try:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as exc:
        handle.close()
        raise MechanicsError("review lock is active") from exc
    return handle


def _reserve_flag(run: Path) -> None:
    payload = (
        _json_bytes(
            {
                "pid": os.getpid(),
                "run_dir": str(run),
                "kind": "source-interpreter-mechanics",
            }
        )
        + b"\n"
    )
    descriptor = os.open(RUN_FLAG, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--_qualify-only", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--_child", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--deadline-monotonic", type=float, help=argparse.SUPPRESS)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args._qualify_only:
        if (
            args.run_dir is not None
            or args.execute
            or args._child
            or args.deadline_monotonic is not None
        ):
            raise ValueError("qualification-only mode cannot be combined")
        validate_artifacts(verify_base_files=False)
        print(
            json.dumps(
                {
                    "kind": "source-interpreter-mechanics-qualification",
                    "model_loaded": False,
                    "selected_row_index": 14,
                    "status": "PASS",
                },
                sort_keys=True,
            )
        )
        return 0
    if args.run_dir is None:
        raise ValueError("run-dir is required")
    run = args.run_dir.resolve()
    if run.parent != RESULTS_DIR or not run.name.startswith("run-"):
        raise ValueError(
            "run-dir must be a run-* direct child of "
            "results/source-interpreter/mechanics"
        )
    if args._child:
        if args.execute or args.deadline_monotonic is None or not run.is_dir():
            raise ValueError("internal child requires an existing run and deadline")
        return run_measurement(run, deadline_monotonic=args.deadline_monotonic)
    if args.deadline_monotonic is not None:
        raise ValueError("deadline-monotonic is internal only")
    plan = make_plan(run)
    if not args.execute:
        print(json.dumps(plan, ensure_ascii=True, indent=2, sort_keys=True))
        return 0
    if run.exists():
        raise MechanicsError("run directory is occupied")
    register_pid(os.getpid())
    review_handle = _acquire_review_lock()
    flag_reserved = False
    run_created = False
    child_started = False
    try:
        environment = _qualify_environment()
        bindings, _row = validate_artifacts(verify_base_files=False)
        _reserve_flag(run)
        flag_reserved = True
        run.mkdir(parents=True, exist_ok=False)
        run_created = True
        started = time.monotonic()
        deadline = started + WORKING_SECONDS
        plan["execute"] = True
        plan["child_command"][-1] = repr(deadline)
        start_receipt = {
            "schema_version": 1,
            "kind": "source-interpreter-mechanics-start",
            "status": "INCOMPLETE",
            "supervisor_pid": os.getpid(),
            "started_unix": time.time(),
            "started_monotonic": started,
            "work_deadline_monotonic": deadline,
            "total_deadline_monotonic": started + RESERVATION_SECONDS,
            "environment": environment,
            "bindings": bindings,
            "settings": SETTINGS,
            "plan": plan,
            "resource": _resource_receipt("supervisor-start"),
        }
        _write_json(run / "start.json", start_receipt)
        child_started = True
        code, _lifecycle = supervise_child(
            run,
            plan["child_command"],
            run_flag=RUN_FLAG,
            started_monotonic=started,
        )
        return code
    except Exception as exc:
        if run_created and not child_started:
            _write_json(
                run / "lifecycle.json",
                {
                    "schema_version": 1,
                    "kind": "source-interpreter-mechanics-lifecycle",
                    "status": "INCOMPLETE_BEFORE_CHILD",
                    "error": f"{type(exc).__name__}: {exc}",
                    "ended_unix": time.time(),
                    "child_exit_confirmed": None,
                },
            )
        if flag_reserved and not child_started:
            RUN_FLAG.unlink(missing_ok=True)
        raise
    finally:
        fcntl.flock(review_handle, fcntl.LOCK_UN)
        review_handle.close()


if __name__ == "__main__":
    sys.exit(main())
