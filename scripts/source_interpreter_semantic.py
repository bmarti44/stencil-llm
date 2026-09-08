#!/usr/bin/env python3
"""Prepare and run the fixed fresh source-interpreter semantic comparison."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
for import_root in (ROOT, ROOT / "src"):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from scripts import source_interpreter_fit as fit  # noqa: E402
from scripts import source_interpreter_mechanics as mechanics  # noqa: E402
from stencil.focus import source_interpreter as source_module  # noqa: E402

SEMANTIC_ROOT = ROOT / "results/source-interpreter/semantic"
RESULTS_DIR = SEMANTIC_ROOT
ACCEPTED_INPUTS_PATH = SEMANTIC_ROOT / "accepted-inputs.json"
PREPARED_DIR = SEMANTIC_ROOT / "prepared"
GENERATION_MANIFEST_PATH = PREPARED_DIR / "generation-manifest.json"
REFERENCE_MANIFEST_PATH = PREPARED_DIR / "reference-manifest.json"
RUN_FLAG = SEMANTIC_ROOT / "RUNNING.flag"
REVIEW_LOCK = ROOT / ".review.lock"
OWNED_PIDS = ROOT / ".stencil-owned-pids"
MODEL_PATH = ROOT / "models/qwen3-4b-hf"
SEMANTIC_PATH = ROOT / "results/source-interpreter/SEMANTIC.md"
SEMANTIC_REVIEW_PATH = ROOT / "results/source-interpreter/semantic-review-astra.md"
BASE_ASSETS_PATH = ROOT / "results/coding-auto-reasoning/research-next/base-assets.json"
ADAPTER_ROOT = ROOT / "results/source-interpreter/fit/run-01"
ADAPTER_DIR = ADAPTER_ROOT / "reconstructed-adapter"
ADAPTER_MANIFEST_PATH = ADAPTER_ROOT / "archive-manifest.json"
ADAPTER_CONFIG_PATH = ADAPTER_ROOT / "adapter/adapter_config.json"

SEMANTIC_SHA256 = "d892196fc32ed1e670152dc5904a50bac854d78dda82222f4da95e4c6b2826e5"
ACCEPTED_SEMANTIC_COMMIT = "96a99d8cf2fb8c55e173cf4e56e998eb47d05f88"
ACCEPTED_REVIEW_SHA256 = (
    "84d75b07cce791b1028b998bbc1887c2298e35a5a05442bfa5db1c8161e90f27"
)
EOS_TOKEN_ID = fit.EOS_TOKEN_ID
PAD_TOKEN_ID = fit.PAD_TOKEN_ID
CONTEXT_TOKENS = 32768
SCHEDULED_CALLS = 36
STARTUP_SECONDS = 660.0
GENERATION_SECONDS = 300.0
RESERVATION_SECONDS = 3600.0
TERMINATION_RESERVE_SECONDS = 15.0
WORKING_SECONDS = RESERVATION_SECONDS - TERMINATION_RESERVE_SECONDS

CONVERSATION_IDS = tuple(f"source-semantic-20260908-{index:02d}" for index in range(6))
FAMILY_IDS = tuple(f"source-semantic-family-20260908-{index:02d}" for index in range(6))
DOCUMENT_PATHS = tuple(
    f"results/source-interpreter/semantic/author-{index:02d}/reviewed.json"
    for index in range(6)
)

STATIC_SHA256 = {
    "results/source-interpreter/SEMANTIC.md": SEMANTIC_SHA256,
    "results/source-interpreter/SEMANTIC-CODE-BRIEF.md": (
        "2d80b13932434c053eaeb17169e0fdac4f126f47ed0525b6787c6e5a7a738222"
    ),
    "src/stencil/focus/source_interpreter.py": (
        "ce8126cab730d5b3b652acccc2930db5bb6df1797dfa8181ef038fff2b7b927d"
    ),
    "scripts/source_interpreter_fit.py": (
        "fe526cc2fe61c183f2a2c4d5db801f8ac684c2f7ad8db7f01980994212c5ee36"
    ),
    "scripts/source_interpreter_mechanics.py": (
        "4eb7cb46f0191e7481e162e03ee12db2d771e9a043792ddd3d6c825e50321927"
    ),
    "tools/observe_source_fit.py": (
        "e04b4cc839d3d906f9ff85513b495c6e0cebcdd63c45cd9413819675679790ee"
    ),
    "results/coding-auto-reasoning/research-next/base-assets.json": (
        "4987d6eec20a7628d45d64799cb8b7fc7250870be2e868755880e70b7e2b5227"
    ),
    "results/source-interpreter/fit/run-01/archive-manifest.json": (
        "836c2966ce253ad1b783a262faa4b0f2ef4f2379924f614999013ec6feaa0807"
    ),
    "results/source-interpreter/fit/run-01/adapter/adapter_config.json": (
        "45f10d86fd18dc5d5f4c748b1b9c59f292f7fc92f6f6334e21dff9255f9a70b2"
    ),
    "results/source-interpreter/fit/run-01/reconstructed-adapter/adapter_config.json": (
        "45f10d86fd18dc5d5f4c748b1b9c59f292f7fc92f6f6334e21dff9255f9a70b2"
    ),
}
ADAPTER_PAYLOADS = (
    {
        "path": (
            "results/source-interpreter/fit/run-01/archive/"
            "adapter_model.safetensors.part-000"
        ),
        "bytes": 9_000_000,
        "sha256": "9e1beaca13ce4fbbede13bfc55b5453701aaa21b078da9ea1cfb2637dcbdeb22",
    },
    {
        "path": (
            "results/source-interpreter/fit/run-01/archive/"
            "adapter_model.safetensors.part-001"
        ),
        "bytes": 2_815_504,
        "sha256": "0aed2f5132275601c5fcde5196d69010cbed07a43f73a194e0b2d41617fd9aae",
    },
)
ADAPTER_SHA256 = "1f9392f3fa99cb31a010176487a6f37999f02cdbc7be9b9cdb4a9b9380e592e3"
ADAPTER_BYTES = 11_815_504
ADAPTER_TENSORS = 144
ADAPTER_PARAMETERS = 2_949_120


class SemanticError(RuntimeError):
    """The fixed semantic preparation or execution contract was not met."""


def _sha_file(path: Path) -> str:
    return mechanics._sha_file(Path(path))


def _json_bytes(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _read_json(path: Path, label: str) -> Any:
    try:
        return json.loads(Path(path).read_bytes())
    except Exception as exc:
        raise SemanticError(f"{label} is not readable JSON: {exc}") from exc


def _write_json(path: Path, value: Any) -> None:
    mechanics._write_json(Path(path), value)


def _receipt(path: Path) -> dict[str, Any]:
    return {
        "path": str(path),
        "bytes": path.stat().st_size,
        "sha256": _sha_file(path),
    }


def _binding(path: Path) -> dict[str, Any]:
    return {"bytes": path.stat().st_size, "sha256": _sha_file(path)}


def _accepted_review_bytes(root: Path) -> bytes:
    try:
        return subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "show",
                f"{ACCEPTED_SEMANTIC_COMMIT}:"
                "results/source-interpreter/semantic-review-astra.md",
            ],
            check=True,
            capture_output=True,
        ).stdout
    except subprocess.CalledProcessError as exc:
        raise SemanticError("accepted semantic review blob is unavailable") from exc


def qualify_static(*, root: Path = ROOT) -> dict[str, Any]:
    """Qualify immutable code/metadata without reading semantic data or weights."""
    root = Path(root).resolve()
    bindings = {}
    for relative, expected in STATIC_SHA256.items():
        path = root / relative
        if _sha_file(path) != expected:
            raise SemanticError(f"static binding differs: {relative}")
        bindings[relative] = _binding(path)
    accepted_review = _accepted_review_bytes(root)
    if hashlib.sha256(accepted_review).hexdigest() != ACCEPTED_REVIEW_SHA256:
        raise SemanticError("historical accepted semantic review differs")
    current_review = root / "results/source-interpreter/semantic-review-astra.md"
    bindings[str(current_review.relative_to(root))] = _binding(current_review)
    for relative in (
        "scripts/source_interpreter_semantic.py",
        "tests/test_source_interpreter_semantic.py",
    ):
        path = root / relative
        if path.is_file():
            bindings[relative] = _binding(path)
    for expected in ADAPTER_PAYLOADS:
        path = root / expected["path"]
        if not path.is_file() or path.stat().st_size != expected["bytes"]:
            raise SemanticError(f"adapter payload size differs: {expected['path']}")
    full_adapter = root / ADAPTER_DIR.relative_to(ROOT) / "adapter_model.safetensors"
    if not full_adapter.is_file() or full_adapter.stat().st_size != ADAPTER_BYTES:
        raise SemanticError("standard full FIT adapter is unavailable")
    head = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return {
        "kind": "source-interpreter-semantic-static-qualification",
        "status": "PASS",
        "bindings": bindings,
        "accepted_review": {
            "git_commit": ACCEPTED_SEMANTIC_COMMIT,
            "sha256": ACCEPTED_REVIEW_SHA256,
        },
        "git_head": head,
        "adapter": {
            "source_sha256": ADAPTER_SHA256,
            "source_bytes": ADAPTER_BYTES,
            "tensors": ADAPTER_TENSORS,
            "parameters": ADAPTER_PARAMETERS,
            "payloads": list(ADAPTER_PAYLOADS),
            "payload_bytes_verified": False,
        },
        "model_loaded": False,
        "tokenizer_loaded": False,
        "accepted_documents_read": False,
        "gpu_used": False,
    }


def _validate_binding(root: Path, relative: str, binding: Any) -> None:
    if type(binding) is not dict or set(binding) != {"bytes", "sha256"}:
        raise SemanticError(f"binding shape differs: {relative}")
    path = root / relative
    if (
        not path.is_file()
        or path.stat().st_size != binding["bytes"]
        or _sha_file(path) != binding["sha256"]
    ):
        raise SemanticError(f"file binding differs: {relative}")


def validate_accepted_manifest(value: Any, *, root: Path = ROOT) -> list[Path]:
    """Validate the root-frozen six-document accepted-input manifest."""
    root = Path(root).resolve()
    required_keys = {
        "schema_version",
        "kind",
        "status",
        "accepted_review_git_commit",
        "bindings",
        "documents",
    }
    if type(value) is not dict or set(value) != required_keys:
        raise SemanticError("accepted-input manifest keys differ")
    if (
        value["schema_version"] != 1
        or value["kind"] != "source-interpreter-semantic-accepted-inputs"
        or value["status"] != "ACCEPTED"
        or value["accepted_review_git_commit"] != ACCEPTED_SEMANTIC_COMMIT
    ):
        raise SemanticError("accepted-input manifest status or authority differs")
    required_bindings = {
        "results/source-interpreter/SEMANTIC.md": SEMANTIC_SHA256,
        "results/source-interpreter/semantic-review-astra.md": None,
        "results/coding-auto-reasoning/research-next/base-assets.json": (
            STATIC_SHA256[
                "results/coding-auto-reasoning/research-next/base-assets.json"
            ]
        ),
    }
    if type(value["bindings"]) is not dict or set(value["bindings"]) != set(
        required_bindings
    ):
        raise SemanticError("accepted-input authority bindings differ")
    for relative, expected_hash in required_bindings.items():
        binding = value["bindings"][relative]
        _validate_binding(root, relative, binding)
        if expected_hash is not None and binding["sha256"] != expected_hash:
            raise SemanticError(f"accepted authority hash differs: {relative}")
    review = _accepted_review_bytes(root)
    if hashlib.sha256(review).hexdigest() != ACCEPTED_REVIEW_SHA256:
        raise SemanticError("accepted review Git blob differs")
    documents = value["documents"]
    if type(documents) is not list or len(documents) != 6:
        raise SemanticError("accepted inputs must contain exactly six documents")
    paths = []
    for index, item in enumerate(documents):
        expected = {
            "index": index,
            "path": DOCUMENT_PATHS[index],
            "conversation_id": CONVERSATION_IDS[index],
            "family_id": FAMILY_IDS[index],
            "split": "withheld",
        }
        if type(item) is not dict or set(item) != {
            *expected,
            "bytes",
            "sha256",
        }:
            raise SemanticError(f"accepted document binding shape differs: {index}")
        if any(item.get(key) != field for key, field in expected.items()):
            raise SemanticError(f"accepted withheld identity differs: {index}")
        _validate_binding(
            root,
            item["path"],
            {"bytes": item["bytes"], "sha256": item["sha256"]},
        )
        paths.append(root / item["path"])
    return paths


def _row_receipt(row: Any) -> dict[str, Any]:
    value = row.receipt() if callable(getattr(row, "receipt", None)) else row
    if type(value) is not dict:
        raise SemanticError("prepared row receipt is not an object")
    return value


def _preparation_bindings(
    root: Path, accepted_path: Path, qualification: dict[str, Any]
) -> dict[str, Any]:
    bindings = dict(qualification["bindings"])
    bindings[str(accepted_path.relative_to(root))] = _binding(accepted_path)
    for relative in (
        "scripts/source_interpreter_semantic.py",
        "tests/test_source_interpreter_semantic.py",
    ):
        bindings[relative] = _binding(root / relative)
    return bindings


def prepare_packet(
    accepted_path: Path,
    output_dir: Path,
    *,
    root: Path = ROOT,
    source: Any = source_module,
    tokenizer: Any = None,
) -> dict[str, Any]:
    """Prepare target-free generation rows and a separate reference manifest."""
    root = Path(root).resolve()
    accepted_path = Path(accepted_path).resolve()
    output_dir = Path(output_dir).resolve()
    expected_accepted = root / ACCEPTED_INPUTS_PATH.relative_to(ROOT)
    expected_output = root / PREPARED_DIR.relative_to(ROOT)
    if accepted_path != expected_accepted or output_dir != expected_output:
        raise SemanticError("preparation paths differ from the canonical packet")
    if output_dir.exists():
        raise SemanticError("preparation output directory already exists")
    accepted = _read_json(accepted_path, "accepted-input manifest")
    paths = validate_accepted_manifest(accepted, root=root)
    qualification = qualify_static(root=root)
    documents, input_receipts = source.load_documents(paths)
    if [document.get("conversation_id") for document in documents] != list(
        CONVERSATION_IDS
    ) or any(document.get("split") != "withheld" for document in documents):
        raise SemanticError("loaded withheld document identity differs")
    tokenizer = tokenizer if tokenizer is not None else source.load_tokenizer()
    prepared = [_row_receipt(row) for row in source.prepare_rows(documents, tokenizer)]
    if len(prepared) != 18:
        raise SemanticError("preparation did not produce exactly eighteen rows")
    generation_rows = []
    reference_rows = []
    for row_index, row in enumerate(prepared):
        conversation_index, query_index = divmod(row_index, 3)
        identity = {
            "row_index": row_index,
            "conversation_index": conversation_index,
            "conversation_id": CONVERSATION_IDS[conversation_index],
            "family_id": FAMILY_IDS[conversation_index],
            "split": "withheld",
            "query_index": query_index,
        }
        if any(
            row.get(key) != expected
            for key, expected in identity.items()
            if key not in {"row_index", "conversation_index"}
        ):
            raise SemanticError(f"prepared row identity differs: {row_index}")
        prefix_ids = row.get("prefix_ids")
        source_prefix = row.get("source_prefix")
        if (
            type(prefix_ids) is not list
            or any(type(token) is not int or token < 0 for token in prefix_ids)
            or row.get("prefix_length") != len(prefix_ids)
            or type(source_prefix) is not list
            or not source_prefix
        ):
            raise SemanticError(f"prepared prefix differs: {row_index}")
        target_ids = row.get("target_ids")
        target_with_eos = row.get("target_with_eos_ids")
        if (
            type(target_ids) is not list
            or not target_ids
            or type(target_with_eos) is not list
            or target_with_eos != target_ids + [EOS_TOKEN_ID]
            or row.get("target_length") != len(target_with_eos)
            or row.get("full_length") != len(prefix_ids) + len(target_with_eos)
            or row.get("eos_token_id") != EOS_TOKEN_ID
            or row.get("target_text_sha256")
            != hashlib.sha256(row.get("target_text", "").encode("utf-8")).hexdigest()
        ):
            raise SemanticError(f"prepared reference target differs: {row_index}")
        context = len(prefix_ids) + fit.GENERATION_SETTINGS["max_new_tokens"]
        if context > CONTEXT_TOKENS:
            raise SemanticError(f"prepared prefix exceeds context: {row_index}")
        visible_ids = [message.get("message_id") for message in source_prefix]
        generation_rows.append(
            {
                **identity,
                "query_message_id": row["query_message_id"],
                "task_handle": row["task_handle"],
                "source_prefix": source_prefix,
                "source_prefix_sha256": row["source_prefix_sha256"],
                "visible_source_ids": visible_ids,
                "prefix_ids": prefix_ids,
                "prefix_sha256": hashlib.sha256(_json_bytes(prefix_ids)).hexdigest(),
                "prefix_length": len(prefix_ids),
                "context_with_output_tokens": context,
            }
        )
        reference_rows.append(
            {
                **identity,
                "query_message_id": row["query_message_id"],
                "target_text": row["target_text"],
                "target_text_sha256": row["target_text_sha256"],
                "target_ids": target_ids,
                "target_with_eos_ids": target_with_eos,
                "target_length": row["target_length"],
                "full_length": row["full_length"],
                "eos_token_id": row["eos_token_id"],
            }
        )
    bindings = _preparation_bindings(root, accepted_path, qualification)
    tokenizer_state, tokenizer_assets, control_tokens = (
        source._verify_original_tokenizer(tokenizer)
    )
    common = {
        "schema_version": 1,
        "documents": 6,
        "rows_count": 18,
        "input_receipts": input_receipts,
        "tokenizer_state": tokenizer_state,
        "tokenizer_asset_sha256": tokenizer_assets,
        "control_tokens": control_tokens,
        "environment": {
            "sys_executable": str(Path(sys.executable)),
            "resolved_executable": str(Path(sys.executable).resolve()),
            "sys_prefix": str(Path(sys.prefix)),
            "packages": mechanics._package_versions(),
        },
        "bindings": bindings,
        "adapter": qualification["adapter"],
        "preparation_git_head": qualification["git_head"],
    }
    generation = {
        **common,
        "kind": "source-interpreter-semantic-generation-manifest",
        "status": "FROZEN_TARGET_FREE",
        "settings": dict(fit.GENERATION_SETTINGS),
        "scheduled_calls": SCHEDULED_CALLS,
        "order": [
            {"ordinal": ordinal, "row_index": row, "mode": mode}
            for ordinal, (row, mode) in enumerate(fixed_call_order())
        ],
        "rows": generation_rows,
        "reference_manifest_read_by_generation": False,
        "contains_targets_or_labels": False,
    }
    reference = {
        **common,
        "kind": "source-interpreter-semantic-reference-manifest",
        "status": "SEALED_REFERENCE",
        "rows": reference_rows,
    }
    output_dir.mkdir(parents=True, exist_ok=False)
    _write_json(output_dir / "generation-manifest.json", generation)
    _write_json(output_dir / "reference-manifest.json", reference)
    return {
        "kind": "source-interpreter-semantic-preparation",
        "status": "PASS",
        "documents": 6,
        "rows": 18,
        "scheduled_calls": SCHEDULED_CALLS,
        "generation_manifest": _receipt(output_dir / "generation-manifest.json"),
        "reference_manifest": _receipt(output_dir / "reference-manifest.json"),
        "model_loaded": False,
        "gpu_used": False,
    }


def fixed_call_order() -> list[tuple[int, str]]:
    return [
        (row, mode)
        for row in range(18)
        for mode in (("base", "adapter") if row % 2 == 0 else ("adapter", "base"))
    ]


def validate_generation_manifest(
    value: Any, *, root: Path = ROOT
) -> list[dict[str, Any]]:
    expected_keys = {
        "schema_version",
        "kind",
        "status",
        "documents",
        "rows_count",
        "input_receipts",
        "tokenizer_state",
        "tokenizer_asset_sha256",
        "control_tokens",
        "environment",
        "bindings",
        "adapter",
        "preparation_git_head",
        "settings",
        "scheduled_calls",
        "order",
        "rows",
        "reference_manifest_read_by_generation",
        "contains_targets_or_labels",
    }
    if (
        type(value) is not dict
        or set(value) != expected_keys
        or value.get("schema_version") != 1
        or value.get("kind") != "source-interpreter-semantic-generation-manifest"
        or value.get("status") != "FROZEN_TARGET_FREE"
        or value.get("documents") != 6
        or value.get("rows_count") != 18
        or value.get("scheduled_calls") != SCHEDULED_CALLS
        or value.get("settings") != fit.GENERATION_SETTINGS
        or value.get("contains_targets_or_labels") is not False
        or value.get("reference_manifest_read_by_generation") is not False
    ):
        raise SemanticError("generation manifest header differs")
    if value.get("order") != [
        {"ordinal": ordinal, "row_index": row, "mode": mode}
        for ordinal, (row, mode) in enumerate(fixed_call_order())
    ]:
        raise SemanticError("generation call order differs")
    expected_adapter = {
        "source_sha256": ADAPTER_SHA256,
        "source_bytes": ADAPTER_BYTES,
        "tensors": ADAPTER_TENSORS,
        "parameters": ADAPTER_PARAMETERS,
        "payloads": list(ADAPTER_PAYLOADS),
        "payload_bytes_verified": False,
    }
    if value.get("adapter") != expected_adapter:
        raise SemanticError("generation adapter binding differs")
    if (
        not isinstance(value.get("preparation_git_head"), str)
        or len(value["preparation_git_head"]) != 40
    ):
        raise SemanticError("generation preparation Git head differs")
    rows = value.get("rows")
    if type(rows) is not list or len(rows) != 18:
        raise SemanticError("generation manifest lacks eighteen rows")
    forbidden = {"target", "targets", "target_ids", "target_text", "labels"}

    def reject_gold(item: Any) -> None:
        if isinstance(item, dict):
            if set(item) & forbidden:
                raise SemanticError("generation manifest contains target material")
            for child in item.values():
                reject_gold(child)
        elif isinstance(item, list):
            for child in item:
                reject_gold(child)

    reject_gold(value)
    inputs = value.get("input_receipts")
    input_keys = {
        "path",
        "bytes",
        "sha256",
        "conversation_id",
        "family_id",
        "split",
        "read_error",
        "parse_error",
    }
    if (
        type(inputs) is not list
        or len(inputs) != 6
        or any(type(item) is not dict or set(item) != input_keys for item in inputs)
        or any(
            item.get("conversation_id") != CONVERSATION_IDS[index]
            or item.get("family_id") != FAMILY_IDS[index]
            or item.get("split") != "withheld"
            or item.get("read_error") is not None
            or item.get("parse_error") is not None
            for index, item in enumerate(inputs)
        )
    ):
        raise SemanticError("generation input receipts differ")
    row_keys = {
        "row_index",
        "conversation_index",
        "conversation_id",
        "family_id",
        "split",
        "query_index",
        "query_message_id",
        "task_handle",
        "source_prefix",
        "source_prefix_sha256",
        "visible_source_ids",
        "prefix_ids",
        "prefix_sha256",
        "prefix_length",
        "context_with_output_tokens",
    }
    for index, row in enumerate(rows):
        if (
            type(row) is not dict
            or set(row) != row_keys
            or row.get("row_index") != index
            or row.get("conversation_index") != index // 3
            or row.get("conversation_id") != CONVERSATION_IDS[index // 3]
            or row.get("family_id") != FAMILY_IDS[index // 3]
            or row.get("split") != "withheld"
            or row.get("query_index") != index % 3
            or row.get("prefix_length") != len(row.get("prefix_ids", []))
            or row.get("context_with_output_tokens")
            != row.get("prefix_length", 0) + fit.GENERATION_SETTINGS["max_new_tokens"]
            or row.get("context_with_output_tokens") > CONTEXT_TOKENS
            or row.get("visible_source_ids")
            != [message.get("message_id") for message in row.get("source_prefix", [])]
            or row.get("query_message_id") != row.get("visible_source_ids", [None])[-1]
            or row.get("source_prefix_sha256")
            != hashlib.sha256(_json_bytes(row.get("source_prefix"))).hexdigest()
            or row.get("prefix_sha256")
            != hashlib.sha256(_json_bytes(row.get("prefix_ids"))).hexdigest()
            or any(
                type(token) is not int or token < 0
                for token in row.get("prefix_ids", [])
            )
        ):
            raise SemanticError(f"generation row differs: {index}")
    bindings = value.get("bindings")
    if type(bindings) is not dict:
        raise SemanticError("generation manifest bindings are absent")
    root = Path(root).resolve()
    for relative, binding in bindings.items():
        _validate_binding(root, relative, binding)
    expected_environment = {
        "sys_executable": str(Path(sys.executable)),
        "resolved_executable": str(Path(sys.executable).resolve()),
        "sys_prefix": str(Path(sys.prefix)),
        "packages": mechanics._package_versions(),
    }
    if value.get("environment") != expected_environment:
        raise SemanticError("generation environment differs from preparation")
    return rows


def initialize_call_records(run: Path, rows: list[dict[str, Any]]) -> None:
    if len(rows) != 18:
        raise SemanticError("call initialization requires eighteen rows")
    for ordinal, (row_index, mode) in enumerate(fixed_call_order()):
        row = rows[row_index]
        _write_json(
            Path(run) / f"call-{ordinal:02d}.json",
            {
                "ordinal": ordinal,
                "row_index": row_index,
                "conversation_id": row["conversation_id"],
                "query_index": row["query_index"],
                "query_message_id": row["query_message_id"],
                "mode": mode,
                "prefix_sha256": row["prefix_sha256"],
                "status": "NOT_ATTEMPTED",
                "reason": "fixed call has not started",
                "receipt_path": None,
                "receipt_sha256": None,
                "generated_ids_available": False,
                "whole_call_seconds": None,
            },
        )


def partial_call_records(run: Path) -> list[dict[str, Any]]:
    calls = []
    for ordinal, (row_index, mode) in enumerate(fixed_call_order()):
        path = Path(run) / f"call-{ordinal:02d}.json"
        if not path.is_file():
            calls.append(
                {
                    "ordinal": ordinal,
                    "row_index": row_index,
                    "mode": mode,
                    "status": "NOT_ATTEMPTED",
                    "receipt_path": None,
                    "generated_ids_available": False,
                    "whole_call_seconds": None,
                }
            )
            continue
        try:
            call = _read_json(path, "partial semantic call")
        except SemanticError:
            calls.append(
                {
                    "ordinal": ordinal,
                    "row_index": row_index,
                    "mode": mode,
                    "status": "UNKNOWN",
                    "receipt_path": path.name,
                    "generated_ids_available": None,
                    "whole_call_seconds": None,
                }
            )
            continue
        if call.get("status") in {"INTENT", "COMPLETION_PENDING"}:
            call["status"] = "UNAVAILABLE"
            raw_path = Path(run) / f"row-{row_index:02d}" / f"generation-{mode}.json"
            try:
                raw = _read_json(raw_path, "recoverable nested generation receipt")
            except SemanticError:
                raw = None
            if type(raw) is dict:
                generated = raw.get("generated_ids")
                call.update(
                    {
                        "receipt_path": str(raw_path.relative_to(run)),
                        "receipt_sha256": _sha_file(raw_path),
                        "generated_ids_available": isinstance(generated, list),
                        "generated_tokens": len(generated)
                        if isinstance(generated, list)
                        else None,
                        "decoded_bytes": raw.get("decoded_bytes"),
                        "whole_call_seconds": raw.get("whole_call_seconds"),
                        "raw_receipt_status": raw.get("status"),
                        "within_deadline_confirmed": False,
                        "availability_interpretation": (
                            "raw output bytes are available; final call-completion "
                            "and within-deadline confirmation are unavailable"
                        ),
                    }
                )
            else:
                call["generated_ids_available"] = None
                call["whole_call_seconds"] = None
        calls.append(call)
    return calls


def validate_complete_calls(run: Path) -> list[dict[str, Any]]:
    calls = partial_call_records(run)
    if len(calls) != SCHEDULED_CALLS or any(
        call.get("status") != "RETURNED" for call in calls
    ):
        raise SemanticError("complete execution requires all 36 returned calls")
    for ordinal, call in enumerate(calls):
        if (
            call.get("ordinal") != ordinal
            or (call.get("row_index"), call.get("mode")) != fixed_call_order()[ordinal]
        ):
            raise SemanticError("complete call identity or order differs")
        receipt_path = call.get("receipt_path")
        if not isinstance(receipt_path, str):
            raise SemanticError("complete call receipt is absent")
        path = Path(run) / receipt_path
        if not path.is_file() or _sha_file(path) != call.get("receipt_sha256"):
            raise SemanticError("complete call receipt binding differs")
        receipt = _read_json(path, "complete nested generation receipt")
        if (
            receipt.get("status") != "RETURNED"
            or receipt.get("mode") != call["mode"]
            or receipt.get("row_index") != call["row_index"]
            or type(receipt.get("generated_ids")) is not list
            or type(receipt.get("complete_output_ids")) is not list
            or receipt.get("whole_call_seconds") is None
            or (receipt.get("stop_facts") or {}).get("deadline_reached") is not False
            or hashlib.sha256(_json_bytes(receipt.get("prefix_ids"))).hexdigest()
            != call.get("prefix_sha256")
            or receipt.get("original_trunk_object_id")
            != call.get("original_trunk_object_id")
        ):
            raise SemanticError("complete nested generation receipt differs")
    trunk_ids = {call.get("original_trunk_object_id") for call in calls}
    if len(trunk_ids) != 1 or None in trunk_ids:
        raise SemanticError("complete calls did not use one original trunk")
    return calls


def _call_record(
    ordinal: int,
    row: dict[str, Any],
    mode: str,
    status: str,
    **details: Any,
) -> dict[str, Any]:
    return {
        "ordinal": ordinal,
        "row_index": row["row_index"],
        "conversation_id": row["conversation_id"],
        "query_index": row["query_index"],
        "query_message_id": row["query_message_id"],
        "mode": mode,
        "prefix_sha256": row["prefix_sha256"],
        "status": status,
        **details,
    }


def run_inference_schedule(
    run: Path,
    *,
    rows: list[dict[str, Any]],
    model: Any,
    tokenizer: Any,
    torch: Any,
    adapter_name: str,
    stopping_list: Any,
    single_call: Any = None,
    deadline_seconds: float = GENERATION_SECONDS,
    overall_deadline: float = math.inf,
    clock: Any = time.monotonic,
) -> dict[str, Any]:
    """Consume the fixed 36 calls, stopping only for technical incompleteness."""
    run = Path(run)
    single_call = fit.run_generation_call if single_call is None else single_call
    initialize_call_records(run, rows)
    stopped = None
    for ordinal, (row_index, mode) in enumerate(fixed_call_order()):
        row = rows[row_index]
        row_dir = run / f"row-{row_index:02d}"
        if ordinal % 2 == 0:
            row_dir.mkdir(exist_ok=False)
        elif not row_dir.is_dir():
            raise SemanticError("paired row directory is absent")
        expected_receipt = row_dir / f"generation-{mode}.json"
        if expected_receipt.exists():
            raise SemanticError("generation receipt path is occupied")
        started = clock()
        hard_deadline = min(started + deadline_seconds, overall_deadline)
        intent = _call_record(
            ordinal,
            row,
            mode,
            "INTENT",
            started_monotonic=started,
            hard_deadline_monotonic=hard_deadline,
            receipt_path=None,
            receipt_sha256=None,
            generated_ids_available=None,
            whole_call_seconds=None,
        )
        _write_json(run / f"call-{ordinal:02d}.json", intent)
        stage_intent = fit._publish_stage(
            run,
            f"generation-{mode}",
            "INTENT",
            hard_deadline=hard_deadline,
            clock=clock,
            ordinal=ordinal,
            row_index=row_index,
        )
        if stage_intent["publication_observed_monotonic"] > hard_deadline:
            call = _call_record(
                ordinal,
                row,
                mode,
                "TECHNICAL_DEADLINE",
                receipt_path=None,
                receipt_sha256=None,
                generated_ids_available=False,
                whole_call_seconds=None,
            )
            _write_json(run / f"call-{ordinal:02d}.json", call)
            stopped = "INCOMPLETE_DEADLINE"
            break
        remaining = max(0.0, hard_deadline - clock())
        output = single_call(
            row_dir,
            model=model,
            tokenizer=tokenizer,
            torch=torch,
            row={**row, "preview_row_index": row_index},
            mode=mode,
            adapter_name=adapter_name,
            stopping_list=stopping_list,
            deadline_seconds=remaining,
            clock=clock,
        )
        receipt_path = row_dir / f"generation-{mode}.json"
        deadline_reached = bool(
            (output.get("stop_facts") or {}).get("deadline_reached")
            or output.get("deadline_reached")
        )
        terminal = (
            "DEADLINE"
            if deadline_reached
            else "COMPLETE"
            if output.get("status") == "RETURNED"
            else "FAILED"
        )
        stage = fit._publish_stage(
            run,
            f"generation-{mode}",
            terminal,
            hard_deadline=hard_deadline,
            clock=clock,
            ordinal=ordinal,
            row_index=row_index,
            receipt_path=str(receipt_path.relative_to(run)),
        )
        if (
            stage.get("status") == "DEADLINE"
            or stage.get("publication_observed_monotonic", math.inf) > hard_deadline
        ):
            deadline_reached = True
        status = (
            "TECHNICAL_DEADLINE"
            if deadline_reached
            else output.get("status", "TECHNICAL_ERROR")
        )
        call = _call_record(
            ordinal,
            row,
            mode,
            status,
            receipt_path=str(receipt_path.relative_to(run))
            if receipt_path.is_file()
            else None,
            receipt_sha256=_sha_file(receipt_path) if receipt_path.is_file() else None,
            generated_ids_available=(output.get("generated_ids") is not None),
            generated_tokens=len(output["generated_ids"])
            if output.get("generated_ids") is not None
            else None,
            decoded_bytes=output.get("decoded_bytes"),
            whole_call_seconds=output.get("whole_call_seconds"),
            strict_output_valid=(output.get("strict_output") or {}).get("valid"),
            cap_reached=(output.get("stop_facts") or {}).get("cap_reached"),
            deadline_reached=deadline_reached,
            stage_completion=stage,
            original_trunk_object_id=output.get("original_trunk_object_id"),
        )
        _write_json(run / f"call-{ordinal:02d}.json", call)
        if status != "RETURNED":
            stopped = (
                "INCOMPLETE_DEADLINE" if deadline_reached else "INCOMPLETE_TECHNICAL"
            )
            break
    calls = partial_call_records(run)
    returned = sum(call.get("status") == "RETURNED" for call in calls)
    return {
        "status": stopped
        or ("COMPLETE" if returned == SCHEDULED_CALLS else "INCOMPLETE"),
        "scheduled_calls": SCHEDULED_CALLS,
        "returned_calls": returned,
        "calls": calls,
    }


def _current_stage(run: Path) -> dict[str, Any] | None:
    path = Path(run) / "current-stage.json"
    if not path.is_file():
        return None
    try:
        value = _read_json(path, "current semantic stage")
    except SemanticError:
        return None
    return value if type(value) is dict else None


def supervise_child(
    run: Path,
    command: list[str],
    *,
    run_flag: Path = RUN_FLAG,
    pid_registry: Path = OWNED_PIDS,
    reservation_seconds: float = RESERVATION_SECONDS,
    termination_reserve_seconds: float = TERMINATION_RESERVE_SECONDS,
    started_monotonic: float | None = None,
    poll_seconds: float = 0.25,
    clock: Any = time.monotonic,
    wall_clock: Any = time.time,
    popen: Any = subprocess.Popen,
    register: Any = mechanics.register_pid,
) -> tuple[int, dict[str, Any]]:
    """Own one model child and bound nested semantic stages and publication."""
    run = Path(run)
    started = clock() if started_monotonic is None else started_monotonic
    work_deadline = started + reservation_seconds - termination_reserve_seconds
    total_deadline = started + reservation_seconds
    child = None
    child_exit_confirmed = False
    timed_out_stage = None
    error = None
    termination_requested = False
    try:
        _write_json(run / "child-command.json", list(command))
        with (
            (run / "child.stdout.log").open("xb") as stdout,
            (run / "child.stderr.log").open("xb") as stderr,
        ):
            try:
                child = popen(
                    list(command),
                    cwd=str(ROOT),
                    stdin=subprocess.DEVNULL,
                    stdout=stdout,
                    stderr=stderr,
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
                while child.poll() is None:
                    now = clock()
                    stage = _current_stage(run)
                    deadline = work_deadline
                    if stage and stage.get("status") in {
                        "INTENT",
                        "COMPLETION_PENDING",
                    }:
                        candidate = stage.get("hard_deadline_monotonic")
                        if type(candidate) in (int, float) and math.isfinite(candidate):
                            deadline = min(deadline, float(candidate))
                    if now >= deadline:
                        stage_active = bool(
                            stage
                            and stage.get("status") in {"INTENT", "COMPLETION_PENDING"}
                            and deadline < work_deadline
                        )
                        timed_out_stage = (
                            stage.get("stage") if stage_active else "whole-job"
                        )
                        termination_requested = True
                        child_exit_confirmed = mechanics._stop_owned_child(
                            child, total_deadline=total_deadline, clock=clock
                        )
                        break
                    try:
                        child.wait(timeout=max(0.0, min(poll_seconds, deadline - now)))
                    except subprocess.TimeoutExpired:
                        continue
                if child.poll() is not None:
                    child_exit_confirmed = True
            except Exception as exc:
                error = f"{type(exc).__name__}: {exc}"
                if child is not None and child.poll() is None:
                    termination_requested = True
                    child_exit_confirmed = mechanics._stop_owned_child(
                        child, total_deadline=total_deadline, clock=clock
                    )
                elif child is not None:
                    child_exit_confirmed = True
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        if child is not None and child.poll() is None:
            termination_requested = True
            child_exit_confirmed = mechanics._stop_owned_child(
                child, total_deadline=total_deadline, clock=clock
            )
        elif child is not None:
            child_exit_confirmed = True
    finally:
        child_exit = clock()
        child_code = child.returncode if child_exit_confirmed else None
        status = "INCOMPLETE_CHILD"
        exit_code = 2
        model_cleanup_confirmed = False
        if timed_out_stage is not None:
            status = "INCOMPLETE_STAGE_TIMEOUT"
        elif error is not None:
            status = "INCOMPLETE_SUPERVISOR"
        elif child_exit_confirmed and child_code == 0:
            try:
                result = _read_json(run / "result.json", "semantic result")
                validate_complete_calls(run)
                if (
                    result.get("status") != "COMPLETE"
                    or result.get("complete_execution_eligible_for_later_assessment")
                    is not True
                    or result.get("cleanup_confirmed") is not True
                ):
                    raise SemanticError("semantic result completion fields differ")
                model_cleanup_confirmed = True
                status = (
                    "COMPLETE" if child_exit <= work_deadline else "INCOMPLETE_DEADLINE"
                )
                exit_code = 0 if status == "COMPLETE" else 2
            except Exception as exc:
                status = "INCOMPLETE_CHILD_RESULT"
                error = f"{type(exc).__name__}: {exc}"
        calls = partial_call_records(run)
        lifecycle = {
            "schema_version": 1,
            "kind": "source-interpreter-semantic-lifecycle",
            "status": "FINALIZING",
            "candidate_status": status,
            "started_monotonic": started,
            "child_exit_monotonic": child_exit,
            "ended_monotonic": None,
            "elapsed_seconds": None,
            "reservation_seconds": reservation_seconds,
            "termination_reserve_seconds": termination_reserve_seconds,
            "work_deadline_monotonic": work_deadline,
            "total_deadline_monotonic": total_deadline,
            "child_pid": child.pid if child is not None else None,
            "child_exit_code": child_code,
            "child_exit_confirmed": child_exit_confirmed,
            "termination_requested": termination_requested,
            "timed_out_stage": timed_out_stage,
            "error": error,
            "calls": calls,
            "returned_calls": sum(call.get("status") == "RETURNED" for call in calls),
            "unavailable_calls": sum(
                call.get("status") == "UNAVAILABLE" for call in calls
            ),
            "not_attempted_calls": sum(
                call.get("status") == "NOT_ATTEMPTED" for call in calls
            ),
            "complete_execution_eligible_for_later_assessment": False,
            "practical_advancement_execution_eligible": False,
            "owned_child_cleanup_confirmed": child is None or child_exit_confirmed,
            "model_cleanup_confirmed": model_cleanup_confirmed,
            "run_flag_cleared": False,
            "receipt_publication_tail": None,
        }
        _write_json(run / "lifecycle.json", lifecycle)
        if child is None or child_exit_confirmed:
            Path(run_flag).unlink(missing_ok=True)
            lifecycle["run_flag_cleared"] = True
        finalized = clock()
        if status == "COMPLETE" and finalized > total_deadline:
            status = "INCOMPLETE_FINALIZATION_DEADLINE"
            exit_code = 2
        complete = status == "COMPLETE"
        lifecycle.update(
            {
                "status": status,
                "ended_monotonic": finalized,
                "elapsed_seconds": finalized - started,
                "ended_unix": wall_clock(),
                "complete_execution_eligible_for_later_assessment": complete,
                "practical_advancement_execution_eligible": complete,
                "receipt_publication_tail": {
                    "starts_monotonic": finalized,
                    "included_in_elapsed": False,
                    "bounded_by_outer_observer": True,
                    "description": (
                        "Final lifecycle fsync and supervisor exit follow the last "
                        "self-observed monotonic sample."
                    ),
                },
            }
        )
        _write_json(run / "lifecycle.json", lifecycle)
    return exit_code, lifecycle


def _verify_adapter_files(*, root: Path = ROOT, payload_bytes: bool) -> dict[str, Any]:
    root = Path(root).resolve()
    qualification = qualify_static(root=root)
    verified = []
    for expected in ADAPTER_PAYLOADS:
        path = root / expected["path"]
        if payload_bytes and _sha_file(path) != expected["sha256"]:
            raise SemanticError(f"adapter payload bytes differ: {expected['path']}")
        verified.append({**expected, "bytes_verified": payload_bytes})
    full = root / ADAPTER_DIR.relative_to(ROOT) / "adapter_model.safetensors"
    if payload_bytes and _sha_file(full) != ADAPTER_SHA256:
        raise SemanticError("standard adapter bytes differ")
    return {
        "qualification": qualification,
        "payloads": verified,
        "full_adapter": {
            "path": str(full.relative_to(root)),
            "bytes": full.stat().st_size,
            "sha256": ADAPTER_SHA256,
            "bytes_verified": payload_bytes,
        },
    }


def _guard(deadline: float, label: str) -> None:
    if time.monotonic() >= deadline:
        raise SemanticError(f"deadline reached before {label}")


def run_child(
    run: Path,
    *,
    generation_manifest: Path,
    startup_deadline: float,
    overall_deadline: float,
) -> int:
    """Load one frozen base/adapter and execute only target-free manifest calls."""
    run = Path(run)
    model = torch = None
    startup = fit._publish_stage(
        run,
        "startup",
        "INTENT",
        hard_deadline=startup_deadline,
        model_calls=0,
    )
    try:
        if startup["publication_observed_monotonic"] > startup_deadline:
            raise SemanticError("startup intent publication exceeded deadline")
        manifest = _read_json(generation_manifest, "generation manifest")
        rows = validate_generation_manifest(manifest)
        initialize_call_records(run, rows)
        before_files = _verify_adapter_files(payload_bytes=True)
        _guard(startup_deadline, "ML imports")
        import gc

        import peft
        import torch as torch_module
        import transformers
        from peft import PeftModel, get_peft_model_state_dict
        from transformers import (
            AutoModelForCausalLM,
            AutoTokenizer,
            StoppingCriteriaList,
        )

        torch = torch_module
        if not torch.cuda.is_available():
            raise SemanticError("CUDA is unavailable")
        tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, local_files_only=True)
        if source_module._tokenizer_state(tokenizer) != manifest["tokenizer_state"]:
            raise SemanticError("loaded tokenizer state differs from preparation")
        _guard(startup_deadline, "base model load")
        base = AutoModelForCausalLM.from_pretrained(
            MODEL_PATH,
            local_files_only=True,
            dtype=torch.bfloat16,
            attn_implementation="sdpa",
            device_map={"": "cuda"},
            low_cpu_mem_usage=True,
        )
        model = PeftModel.from_pretrained(
            base,
            ADAPTER_DIR,
            adapter_name="semantic",
            is_trainable=False,
            autocast_adapter_dtype=True,
            local_files_only=True,
        )
        model.set_adapter("semantic", inference_mode=True)
        model.eval()
        model.gradient_checkpointing_disable()
        model.config.use_cache = True
        state = {
            name: value.detach().cpu().clone()
            for name, value in get_peft_model_state_dict(
                model, adapter_name="semantic"
            ).items()
        }
        if (
            len(state) != ADAPTER_TENSORS
            or sum(value.numel() for value in state.values()) != ADAPTER_PARAMETERS
            or any(value.dtype != torch.float32 for value in state.values())
        ):
            raise SemanticError("loaded final FP32 adapter state differs")
        original_state = mechanics.capture_parameter_state(model)
        startup_complete = fit._publish_stage(
            run,
            "startup",
            "COMPLETE",
            hard_deadline=startup_deadline,
            adapter_tensors=len(state),
            adapter_parameters=ADAPTER_PARAMETERS,
        )
        if not fit._stage_completed_within_deadline(startup_complete):
            raise SemanticError("startup completion exceeded deadline")
        inference = run_inference_schedule(
            run,
            rows=rows,
            model=model,
            tokenizer=tokenizer,
            torch=torch,
            adapter_name="semantic",
            stopping_list=StoppingCriteriaList,
            overall_deadline=overall_deadline,
        )
        if inference["status"] != "COMPLETE":
            raise SemanticError(
                f"semantic inference is incomplete: {inference['status']}"
            )
        calls = validate_complete_calls(run)
        frozen = mechanics.validate_frozen_originals(model, original_state["originals"])
        after_state = {
            name: value.detach().cpu().clone()
            for name, value in get_peft_model_state_dict(
                model, adapter_name="semantic"
            ).items()
        }
        mechanics.compare_adapter_states(state, after_state)
        after_files = _verify_adapter_files(payload_bytes=True)
        resource = mechanics._resource_receipt("semantic-before-cleanup", torch)
        cleanup = fit._publish_stage(
            run, "cleanup", "INTENT", hard_deadline=overall_deadline
        )
        if cleanup["publication_observed_monotonic"] > overall_deadline:
            raise SemanticError("cleanup intent exceeded deadline")
        del model
        del base
        gc.collect()
        torch.cuda.empty_cache()
        cleanup_complete = fit._publish_stage(
            run, "cleanup", "COMPLETE", hard_deadline=overall_deadline
        )
        if not fit._stage_completed_within_deadline(cleanup_complete):
            raise SemanticError("cleanup completion exceeded deadline")
        result = {
            "schema_version": 1,
            "kind": "source-interpreter-semantic-result",
            "status": "COMPLETE",
            "fit_on": "frozen final FIT adapter only",
            "evaluated_on": "six fresh withheld families",
            "semantic_judgments_performed": False,
            "settings": dict(fit.GENERATION_SETTINGS),
            "scheduled_calls": SCHEDULED_CALLS,
            "returned_calls": len(calls),
            "calls": calls,
            "original_parameters": {**frozen, "unchanged": True},
            "adapter_parameters": {
                "tensors": len(state),
                "parameters": sum(value.numel() for value in state.values()),
                "exact_before_after": True,
            },
            "adapter_files_before": before_files,
            "adapter_files_after": after_files,
            "resource_before_cleanup": resource,
            "cleanup_confirmed": True,
            "complete_execution_eligible_for_later_assessment": True,
            "practical_advancement_execution_eligible": True,
            "runtime": {
                "python": sys.version,
                "torch": torch.__version__,
                "transformers": transformers.__version__,
                "peft": peft.__version__,
            },
        }
        _write_json(run / "result.json", result)
        return 0
    except BaseException as exc:
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise
        _write_json(
            run / "failure.json",
            {
                "schema_version": 1,
                "kind": "source-interpreter-semantic-failure",
                "status": "INCOMPLETE",
                "error": f"{type(exc).__name__}: {exc}",
                "calls": partial_call_records(run),
                "complete_execution_eligible_for_later_assessment": False,
                "practical_advancement_execution_eligible": False,
                "ended_unix": time.time(),
            },
        )
        return 2


def _input_schema() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "kind": "source-interpreter-semantic-accepted-inputs",
        "status": "ACCEPTED",
        "accepted_review_git_commit": ACCEPTED_SEMANTIC_COMMIT,
        "bindings": {
            "results/source-interpreter/SEMANTIC.md": {"bytes": "int", "sha256": "hex"},
            "results/source-interpreter/semantic-review-astra.md": {
                "bytes": "int",
                "sha256": "hex",
            },
            "results/coding-auto-reasoning/research-next/base-assets.json": {
                "bytes": "int",
                "sha256": "hex",
            },
        },
        "documents": [
            {
                "index": index,
                "path": DOCUMENT_PATHS[index],
                "bytes": "int",
                "sha256": "hex",
                "conversation_id": CONVERSATION_IDS[index],
                "family_id": FAMILY_IDS[index],
                "split": "withheld",
            }
            for index in range(6)
        ],
    }


def make_plan(
    run: Path, generation_manifest: Path = GENERATION_MANIFEST_PATH
) -> dict[str, Any]:
    run = Path(run).resolve()
    command = [
        str(ROOT / ".venv/bin/python"),
        str(Path(__file__).resolve()),
        "--run-dir",
        str(run),
        "--generation-manifest",
        str(Path(generation_manifest).resolve()),
        "--execute",
    ]
    return {
        "schema_version": 1,
        "kind": "source-interpreter-semantic-launch-plan",
        "status": "DRAFT_UNACCEPTED",
        "accepted_code_review": False,
        "execute": False,
        "cwd": str(ROOT),
        "run_dir": str(run),
        "generation_manifest": str(Path(generation_manifest).resolve()),
        "scheduled_calls": SCHEDULED_CALLS,
        "settings": dict(fit.GENERATION_SETTINGS),
        "fixed_order": [
            {"ordinal": ordinal, "row_index": row, "mode": mode}
            for ordinal, (row, mode) in enumerate(fixed_call_order())
        ],
        "accepted_input_schema": _input_schema(),
        "cpu_prepare_command": [
            str(ROOT / ".venv/bin/python"),
            str(Path(__file__).resolve()),
            "--prepare",
            "--accepted-inputs",
            str(ACCEPTED_INPUTS_PATH),
            "--output-dir",
            str(PREPARED_DIR),
        ],
        "outer_observer_required": True,
        "outer_observer": {
            "initial_training_seconds": int(STARTUP_SECONDS),
            "initial_bound_semantics": (
                "semantic startup through durable first generation intent; no training"
            ),
            "whole_process_seconds": int(RESERVATION_SECONDS),
            "poll_seconds": 0.25,
            "receipt": str(run.parent / f"observer-{run.name}.json"),
        },
        "outer_observer_contract": (
            "Root launches tools/observe_source_fit.py before this supervisor. Its "
            "historical initial_training fields mean only the 660-second semantic "
            "startup bound through durable first generation intent; no training "
            "occurs. The same observer bounds all 3,600 seconds through final "
            "lifecycle publication, supervisor exit, and owned-group absence."
        ),
        "command": command,
        "bindings": {},
        "dry_run_reads_semantic_documents": False,
        "dry_run_loads_tokenizer": False,
        "dry_run_loads_model": False,
        "dry_run_starts_child": False,
    }


def _ensure_no_active_flags() -> None:
    flags = sorted(ROOT.joinpath("results").rglob("RUNNING.flag"))
    if flags:
        raise SemanticError(f"active run flags exist: {[str(path) for path in flags]}")


def _qualify_execution(generation_manifest: Path) -> dict[str, Any]:
    """Refuse an unfrozen or resource-occupied explicit launch."""
    _ensure_no_active_flags()
    gpu = subprocess.run(
        ["nvidia-smi", "--query-compute-apps=pid", "--format=csv,noheader"],
        check=True,
        capture_output=True,
    )
    if gpu.stdout.strip():
        raise SemanticError("a GPU compute process is active")
    manifest = _read_json(generation_manifest, "generation manifest")
    relative_manifest = str(Path(generation_manifest).resolve().relative_to(ROOT))
    bound = set(manifest.get("bindings", {})) | {
        relative_manifest,
        "scripts/source_interpreter_semantic.py",
        "tests/test_source_interpreter_semantic.py",
    }
    for relative in sorted(bound):
        tracked = subprocess.run(
            ["git", "-C", str(ROOT), "ls-files", "--error-unmatch", "--", relative],
            check=False,
            capture_output=True,
        )
        dirty = subprocess.run(
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
            capture_output=True,
        )
        if tracked.returncode != 0 or dirty.stdout.strip():
            raise SemanticError(f"bound file is dirty or untracked: {relative}")
    head = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return {"git_head": head, "gpu_compute_processes": [], "active_flags": []}


def _acquire_review_lock() -> Any:
    handle = REVIEW_LOCK.open("a+")
    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as exc:
        handle.close()
        raise SemanticError("review lock is held") from exc
    return handle


def _reserve_flag(run: Path) -> None:
    RUN_FLAG.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(RUN_FLAG, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(descriptor, "w") as stream:
        json.dump({"pid": os.getpid(), "run_dir": str(run)}, stream, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument(
        "--generation-manifest", type=Path, default=GENERATION_MANIFEST_PATH
    )
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--accepted-inputs", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--_qualify-only", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--_child", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--startup-deadline", type=float, help=argparse.SUPPRESS)
    parser.add_argument("--overall-deadline", type=float, help=argparse.SUPPRESS)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args._qualify_only:
        if any(
            (
                args.run_dir,
                args.execute,
                args.prepare,
                args.accepted_inputs,
                args.output_dir,
                args._child,
                args.startup_deadline,
                args.overall_deadline,
            )
        ):
            raise ValueError("qualification-only mode cannot be combined")
        print(json.dumps(qualify_static(), sort_keys=True))
        return 0
    if args.prepare:
        if (
            args.run_dir is not None
            or args.execute
            or args._child
            or args.accepted_inputs is None
            or args.output_dir is None
            or args.startup_deadline is not None
            or args.overall_deadline is not None
        ):
            raise ValueError("prepare requires only accepted-inputs and output-dir")
        receipt = prepare_packet(args.accepted_inputs, args.output_dir)
        print(json.dumps(receipt, sort_keys=True))
        return 0
    if args.run_dir is None:
        raise ValueError("run-dir is required")
    run = args.run_dir.resolve()
    if run.parent != RESULTS_DIR or not run.name.startswith("run-"):
        raise ValueError("run-dir must be a run-* direct child of semantic results")
    if args._child:
        if (
            args.execute
            or args.startup_deadline is None
            or args.overall_deadline is None
            or not run.is_dir()
        ):
            raise ValueError("internal child requires an existing run and deadlines")
        return run_child(
            run,
            generation_manifest=args.generation_manifest.resolve(),
            startup_deadline=args.startup_deadline,
            overall_deadline=args.overall_deadline,
        )
    if args.startup_deadline is not None or args.overall_deadline is not None:
        raise ValueError("deadline arguments are internal only")
    _ensure_no_active_flags()
    plan = make_plan(run, args.generation_manifest)
    if not args.execute:
        print(json.dumps(plan, ensure_ascii=True, indent=2, sort_keys=True))
        return 0
    if run.exists():
        raise SemanticError("run directory is occupied")
    started = time.monotonic()
    startup_deadline = started + STARTUP_SECONDS
    overall_deadline = started + WORKING_SECONDS
    mechanics.register_pid(os.getpid())
    review_handle = _acquire_review_lock()
    flag_reserved = run_created = child_started = False
    try:
        qualification = qualify_static()
        qualification["execution"] = _qualify_execution(args.generation_manifest)
        manifest = _read_json(args.generation_manifest, "generation manifest")
        validate_generation_manifest(manifest)
        if time.monotonic() >= startup_deadline:
            raise SemanticError("startup deadline reached before child launch")
        _reserve_flag(run)
        flag_reserved = True
        run.mkdir(parents=True, exist_ok=False)
        run_created = True
        child_command = [
            str(ROOT / ".venv/bin/python"),
            str(Path(__file__).resolve()),
            "--_child",
            "--run-dir",
            str(run),
            "--generation-manifest",
            str(args.generation_manifest.resolve()),
            "--startup-deadline",
            repr(startup_deadline),
            "--overall-deadline",
            repr(overall_deadline),
        ]
        _write_json(
            run / "start.json",
            {
                "schema_version": 1,
                "kind": "source-interpreter-semantic-start",
                "status": "INCOMPLETE",
                "supervisor_pid": os.getpid(),
                "started_unix": time.time(),
                "started_monotonic": started,
                "startup_deadline_monotonic": startup_deadline,
                "work_deadline_monotonic": overall_deadline,
                "total_deadline_monotonic": started + RESERVATION_SECONDS,
                "generation_manifest": _receipt(args.generation_manifest),
                "qualification": qualification,
                "plan": plan,
            },
        )
        child_started = True
        code, _lifecycle = supervise_child(
            run,
            child_command,
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
                    "kind": "source-interpreter-semantic-lifecycle",
                    "status": "INCOMPLETE_BEFORE_CHILD",
                    "error": f"{type(exc).__name__}: {exc}",
                    "calls": partial_call_records(run),
                    "complete_execution_eligible_for_later_assessment": False,
                    "practical_advancement_execution_eligible": False,
                },
            )
        if flag_reserved:
            RUN_FLAG.unlink(missing_ok=True)
        raise
    finally:
        review_handle.close()


if __name__ == "__main__":
    raise SystemExit(main())
