#!/usr/bin/env python3
"""Run the one fixed full-FIT source-interpreter job under bounded supervision."""

from __future__ import annotations

import argparse
import base64
import contextlib
import fcntl
import hashlib
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
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import source_interpreter_mechanics as mechanics  # noqa: E402

RESULTS_DIR = ROOT / "results/source-interpreter/fit"
RUN_FLAG = ROOT / "results/source-interpreter/RUNNING.flag"
REVIEW_LOCK = ROOT / ".review.lock"
OWNED_PIDS = ROOT / ".stencil-owned-pids"
MODEL_PATH = ROOT / "models/qwen3-4b-hf"
PREVIEW_PATH = ROOT / "results/source-interpreter/preview.json"
INPUTS_PATH = ROOT / "results/source-interpreter/accepted-inputs.json"
FIT_PATH = ROOT / "results/source-interpreter/FIT.md"
BRIEF_PATH = ROOT / "results/source-interpreter/FIT-CODE-BRIEF.md"
FIT_REVIEW_PATH = ROOT / "results/source-interpreter/fit-review-astra.md"
BASE_ASSETS_PATH = ROOT / "results/coding-auto-reasoning/research-next/base-assets.json"

EOS_TOKEN_ID = 151645
PAD_TOKEN_ID = 151643
GENERATION_ROW_INDEX = 14
ROW_SCHEDULE = (
    (12, 15, 16, 1, 9, 8, 13, 14, 0, 4, 5, 17, 10, 3, 2, 11, 6, 7),
    (9, 12, 5, 16, 3, 2, 8, 10, 14, 0, 1, 15, 4, 17, 11, 13, 7, 6),
    (8, 0, 7, 9, 6, 10, 16, 17, 12, 11, 4, 5, 15, 13, 14, 3, 2, 1),
)
TRAINING_STAGE_SECONDS = 1220.0
GENERATION_STAGE_SECONDS = 300.0
RESERVATION_SECONDS = 2400.0
TERMINATION_RESERVE_SECONDS = 15.0
WORKING_SECONDS = RESERVATION_SECONDS - TERMINATION_RESERVE_SECONDS
ARCHIVE_PART_BYTES = 9_000_000

TRAINING_SETTINGS = {
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
    "epochs": 3,
    "updates": 54,
    "batch_size": 1,
    "sequence_tokens_presented": 89_343,
    "supervised_tokens_presented": 21_702,
}
GENERATION_SETTINGS = {
    "max_new_tokens": 2048,
    "do_sample": False,
    "num_beams": 1,
    "num_return_sequences": 1,
    "eos_token_id": EOS_TOKEN_ID,
    "pad_token_id": PAD_TOKEN_ID,
    "use_cache": True,
    "return_dict_in_generate": True,
    "output_scores": False,
    "output_logits": False,
    "output_attentions": False,
    "output_hidden_states": False,
    "logits_to_keep": 1,
    "synced_gpus": False,
    "temperature": 1.0,
    "top_k": 0,
    "top_p": 1.0,
}

EXPECTED_SHA256 = {
    "results/source-interpreter/FIT.md": (
        "f1f306e9ccac968013568dd6f0ed46a42d6df7297105c7a2531a83b7caa541a7"
    ),
    "results/source-interpreter/FIT-CODE-BRIEF.md": (
        "9a3836c0e08944052d98c86c21e7b09c952778f396af0ac8133c813293328e6f"
    ),
    "results/source-interpreter/preview.json": (
        "5760764f748a088d9d105b6f89b6188785941239ea28c1e60d706f9d028a0326"
    ),
    "results/source-interpreter/accepted-inputs.json": (
        "6beea4bb534e0991fc0444d634f92882ff61191880c43cf4e68da730753c4bf8"
    ),
    "results/coding-auto-reasoning/research-next/base-assets.json": (
        "4987d6eec20a7628d45d64799cb8b7fc7250870be2e868755880e70b7e2b5227"
    ),
    "src/stencil/focus/source_interpreter.py": (
        "ce8126cab730d5b3b652acccc2930db5bb6df1797dfa8181ef038fff2b7b927d"
    ),
    "scripts/source_interpreter_mechanics.py": (
        "4eb7cb46f0191e7481e162e03ee12db2d771e9a043792ddd3d6c825e50321927"
    ),
    "tests/test_source_interpreter_mechanics.py": (
        "d6aa5b3b888d2d11a6d573e996dd5de0c48927073f1b432cb957547c8d735bf4"
    ),
    "results/source-interpreter/PREP.md": (
        "5a8536453e52a9427aae02e8a32d6671b9968bc667e483d80f09b2a3be01898e"
    ),
    "results/source-interpreter/RESULTS.md": (
        "12209772c5b1b7449d3a056581f4e60dcdf75e84e9cc236e7e694c96ce850436"
    ),
    "results/source-interpreter/review-astra.md": (
        "c6538d94d711494c69a0a201105daa51c34aa7c73e3591dcc2b94ac75f4a3e05"
    ),
    "results/source-interpreter/mechanics/RESULTS.md": (
        "51387edc9255cdfe04e06900d7d2410010eed321d32433471c3c90f5b46033bd"
    ),
    "results/source-interpreter/mechanics/observer-01.json": (
        "dfb876be456264f83fceaee5127c8beebb95e9419e077e0496b447059511abcf"
    ),
    "results/source-interpreter/mechanics-review-astra.md": (
        "36412129ba95db784c5849e1675459f6cf3d1dd609745001fa28a3efb1d2cde5"
    ),
}
ACCEPTED_FIT_COMMIT = "d5f5b9ac183ffe988b834f29b13a7cdea86dfd38"
ACCEPTED_FIT_REVIEW_SHA256 = (
    "a7b9309c7bb22b0ffb0002f6761251212e3f55275c19432e9983fb548bb3bb10"
)
ACCEPTED_INPUT_PATHS = tuple(
    f"results/source-interpreter/author-{index:02d}/reviewed.json" for index in range(6)
)
BOUND_FILES = (
    tuple(EXPECTED_SHA256)
    + ACCEPTED_INPUT_PATHS
    + (
        "results/source-interpreter/fit-review-astra.md",
        "scripts/source_interpreter_fit.py",
        "tests/test_source_interpreter_fit.py",
    )
)


class FitError(RuntimeError):
    """The accepted fixed-FIT execution contract was not met."""


def _sha_file(path: Path) -> str:
    return mechanics._sha_file(Path(path))


def _read_json(path: Path, label: str) -> Any:
    try:
        return json.loads(Path(path).read_bytes())
    except Exception as exc:
        raise FitError(f"{label} is not readable JSON: {exc}") from exc


def _write_json(path: Path, value: Any) -> None:
    mechanics._write_json(Path(path), value)


def _append_json(path: Path, value: Any) -> None:
    mechanics._append_json(Path(path), value)


def validate_all_rows(
    row_receipts: Any,
    documents: Any,
    input_receipts: Any,
    manifest: Any,
    *,
    root: Path = ROOT,
    validate_row: Any = mechanics.validate_training_row,
) -> list[dict[str, Any]]:
    """Consume every preview row through its exact source and causal validator."""
    if (
        type(row_receipts) is not list
        or len(row_receipts) != 18
        or type(documents) is not list
        or len(documents) != 6
        or type(input_receipts) is not list
        or len(input_receipts) != 6
        or type(manifest) is not dict
        or type(manifest.get("documents")) is not list
        or len(manifest["documents"]) != 6
    ):
        raise ValueError("FIT artifacts must contain six documents and eighteen rows")
    validated = []
    for index, row in enumerate(row_receipts):
        document_index, query_index = divmod(index, 3)
        document = documents[document_index]
        entry = manifest["documents"][document_index]
        try:
            expected = {
                "conversation_id": document["conversation_id"],
                "family_id": document["family_id"],
                "query_index": query_index,
                "query_message_id": document["queries"][query_index]["message_id"],
            }
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError("document query identity is malformed") from exc
        if any(row.get(key) != value for key, value in expected.items()):
            raise ValueError(f"preview row order or source identity differs at {index}")
        if (
            entry.get("conversation_id") != document["conversation_id"]
            or entry.get("family_id") != document["family_id"]
        ):
            raise ValueError("accepted manifest source identity differs")
        causal = validate_row(
            row,
            document=document,
            input_receipt=input_receipts[document_index],
            manifest_entry=entry,
            root=root,
        )
        if causal.get("label_positions") != row.get("loss_positions"):
            raise ValueError(f"preview row causal labels differ at {index}")
        validated.append({**row, "preview_row_index": index, "causal": causal})
    return validated


def build_schedule(rows: Any) -> list[dict[str, Any]]:
    """Bind the fixed three-epoch order to exact validated row identities."""
    if type(rows) is not list or len(rows) != 18:
        raise ValueError("schedule requires exactly eighteen validated rows")
    if [row.get("preview_row_index") for row in rows] != list(range(18)):
        raise ValueError("validated preview row order differs")
    schedule = []
    for epoch_index, order in enumerate(ROW_SCHEDULE):
        if sorted(order) != list(range(18)):
            raise FitError("fixed epoch schedule is not a permutation")
        for epoch_position, row_index in enumerate(order):
            row = rows[row_index]
            if row.get("preview_row_index") != row_index:
                raise ValueError("scheduled preview row identity differs")
            schedule.append(
                {
                    "ordinal": len(schedule),
                    "epoch": epoch_index + 1,
                    "epoch_position": epoch_position,
                    "row_index": row_index,
                    "conversation_id": row["conversation_id"],
                    "family_id": row["family_id"],
                    "query_index": row["query_index"],
                    "query_message_id": row["query_message_id"],
                    "prefix_length": row["prefix_length"],
                    "full_length": row["full_length"],
                    "supervised_tokens": len(row["loss_positions"]),
                    "label_positions": list(row["loss_positions"]),
                    "causal_logit_positions": list(
                        row["causal"]["causal_logit_positions"]
                    ),
                }
            )
    if len(schedule) != TRAINING_SETTINGS["updates"]:
        raise FitError("fixed schedule does not contain 54 updates")
    return schedule


def _archived_fit_review(root: Path) -> bytes:
    try:
        return subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "show",
                f"{ACCEPTED_FIT_COMMIT}:results/source-interpreter/fit-review-astra.md",
            ],
            check=True,
            capture_output=True,
        ).stdout
    except subprocess.CalledProcessError as exc:
        raise FitError("accepted FIT review blob is unavailable") from exc


def validate_artifacts(
    *, root: Path = ROOT, verify_base_files: bool = False
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Qualify exact FIT inputs, all causal rows, code, environment and base."""
    root = Path(root).resolve()
    hashes = {}
    for relative, expected in EXPECTED_SHA256.items():
        actual = _sha_file(root / relative)
        if actual != expected:
            raise FitError(f"frozen artifact differs: {relative}")
        hashes[relative] = actual
    archived_review = _archived_fit_review(root)
    if hashlib.sha256(archived_review).hexdigest() != ACCEPTED_FIT_REVIEW_SHA256:
        raise FitError("accepted FIT review blob differs")
    hashes[f"{ACCEPTED_FIT_COMMIT}:fit-review-astra.md"] = ACCEPTED_FIT_REVIEW_SHA256
    hashes["results/source-interpreter/fit-review-astra.md"] = _sha_file(
        root / FIT_REVIEW_PATH.relative_to(ROOT)
    )
    preview = _read_json(root / PREVIEW_PATH.relative_to(ROOT), "FIT preview")
    manifest = _read_json(root / INPUTS_PATH.relative_to(ROOT), "accepted inputs")
    required = {
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
    for key, expected in required.items():
        if preview.get(key) != expected:
            raise FitError(f"preview field is not qualified: {key}")
    if (
        manifest.get("status") != "LABELS_ACCEPTED_CPU_PREVIEW_PENDING"
        or manifest.get("query_rows") != 18
        or type(manifest.get("documents")) is not list
        or len(manifest["documents"]) != 6
    ):
        raise FitError("accepted input manifest is not qualified")
    if (
        tuple(entry.get("path") for entry in manifest["documents"])
        != ACCEPTED_INPUT_PATHS
    ):
        raise FitError("accepted input paths differ")
    source = mechanics._source_module()
    paths = [root / entry["path"] for entry in manifest["documents"]]
    documents, input_receipts = source.load_documents(paths)
    if input_receipts != preview.get("inputs"):
        raise FitError("preview input receipts differ from accepted sources")
    rows = validate_all_rows(
        preview.get("row_receipts"),
        documents,
        input_receipts,
        manifest,
        root=root,
    )
    schedule = build_schedule(rows)
    if (
        sum(item["full_length"] for item in schedule) != 89_343
        or sum(item["supervised_tokens"] for item in schedule) != 21_702
    ):
        raise FitError("fixed schedule token totals differ")
    generation_row = rows[GENERATION_ROW_INDEX]
    if (
        generation_row["prefix_length"] != 2966
        or generation_row["target_length"] != 925
        or generation_row["full_length"] != 3891
        or generation_row["eos_token_id"] != EOS_TOKEN_ID
        or generation_row["full_length"] != max(row["full_length"] for row in rows)
    ):
        raise FitError("registered generation row differs")
    if (
        preview.get("environment", {}).get("distributions")
        != mechanics._package_versions()
    ):
        raise FitError("installed package versions differ from preview")
    environment = preview.get("environment", {})
    if (
        Path(sys.executable) != Path(environment.get("sys_executable", ""))
        or Path(sys.executable).resolve()
        != Path(environment.get("resolved_executable", ""))
        or Path(sys.prefix) != Path(environment.get("sys_prefix", ""))
    ):
        raise FitError("Python interpreter differs from preview")
    tokenizer = preview.get("tokenizer", {})
    if (
        tokenizer.get("verified_original_state") is not True
        or tokenizer.get("eos_token_id") != EOS_TOKEN_ID
        or tokenizer.get("pad_token_id") != PAD_TOKEN_ID
        or tokenizer.get("base_assets_receipt_sha256")
        != EXPECTED_SHA256[
            "results/coding-auto-reasoning/research-next/base-assets.json"
        ]
    ):
        raise FitError("preview tokenizer binding differs")
    base_assets = _read_json(
        root / BASE_ASSETS_PATH.relative_to(ROOT), "original base asset receipt"
    )
    base_files = base_assets.get("files")
    if (
        base_assets.get("status") != "LOCAL_BASE_BYTES_VERIFIED"
        or type(base_files) is not dict
        or not base_files
    ):
        raise FitError("base asset receipt is not qualified")
    checked_files = {}
    for relative, receipt in base_files.items():
        path = root / relative
        if not path.is_file() or path.stat().st_size != receipt.get("bytes"):
            raise FitError(f"base asset size differs: {relative}")
        if receipt.get("matches_historical_original") is not True:
            raise FitError(f"base asset lacks original binding: {relative}")
        if verify_base_files and _sha_file(path) != receipt.get("sha256"):
            raise FitError(f"base asset bytes differ: {relative}")
        checked_files[relative] = receipt["sha256"]
    if preview.get("code_sha256") != {
        "src/stencil/focus/source_interpreter.py": EXPECTED_SHA256[
            "src/stencil/focus/source_interpreter.py"
        ]
    }:
        raise FitError("preview code binding differs")
    bindings = {
        "artifact_sha256": hashes,
        "input_receipts": input_receipts,
        "preview_tokenizer": tokenizer,
        "base_assets": {
            "receipt_sha256": hashes[
                "results/coding-auto-reasoning/research-next/base-assets.json"
            ],
            "file_sha256": checked_files,
            "all_file_bytes_verified": verify_base_files,
        },
        "packages": mechanics._package_versions(),
        "runner_sha256": _sha_file(root / "scripts/source_interpreter_fit.py"),
        "test_sha256": _sha_file(root / "tests/test_source_interpreter_fit.py"),
        "schedule": [list(epoch) for epoch in ROW_SCHEDULE],
        "scheduled_updates": len(schedule),
        "generation_row_index": GENERATION_ROW_INDEX,
        "validated_row_receipts": [
            {
                "row_index": row["preview_row_index"],
                "conversation_id": row["conversation_id"],
                "family_id": row["family_id"],
                "query_index": row["query_index"],
                "query_message_id": row["query_message_id"],
                "prefix_length": row["prefix_length"],
                "target_length": row["target_length"],
                "full_length": row["full_length"],
                "supervised_tokens": len(row["loss_positions"]),
                "row_sha256": hashlib.sha256(
                    mechanics._json_bytes(
                        preview["row_receipts"][row["preview_row_index"]]
                    )
                ).hexdigest(),
            }
            for row in rows
        ],
    }
    return bindings, rows


def _publish_stage(
    run: Path,
    stage: str,
    status: str,
    *,
    hard_deadline: float,
    clock: Any = time.monotonic,
    **details: Any,
) -> dict[str, Any]:
    receipt = {
        "stage": stage,
        "status": status,
        "monotonic": clock(),
        "hard_deadline_monotonic": hard_deadline,
        **details,
    }
    safe = stage.replace("-", "_")
    _write_json(Path(run) / f"stage-{safe}.json", receipt)
    _write_json(Path(run) / "current-stage.json", receipt)
    _append_json(Path(run) / "stages.jsonl", receipt)
    return receipt


class _GenerationDeadline:
    def __init__(self, deadline: float, clock: Any):
        self.deadline = deadline
        self.clock = clock
        self.reached = False

    def __call__(self, _input_ids: Any, _scores: Any, **_kwargs: Any) -> bool:
        self.reached = self.clock() >= self.deadline
        return self.reached


def _adapter_layer_state(
    model: Any, *, mode: str, adapter_name: str
) -> list[dict[str, Any]]:
    states = []
    for module in model.modules():
        disabled = getattr(module, "disable_adapters", None)
        active = getattr(module, "active_adapters", None)
        if type(disabled) is bool and active is not None:
            active_names = list(active) if not isinstance(active, str) else [active]
            states.append(
                {
                    "class": type(module).__name__,
                    "disabled": disabled,
                    "active_adapters": active_names,
                }
            )
    if not states:
        raise FitError("no adapter layers were available for state verification")
    if mode == "base":
        if any(item["disabled"] is not True for item in states):
            raise FitError("base generation did not disable every adapter layer")
    elif any(
        item["disabled"] is not False or adapter_name not in item["active_adapters"]
        for item in states
    ):
        raise FitError("adapter generation did not activate the reloaded adapter")
    return states


def _strict_output(payload: bytes, row: dict[str, Any]) -> dict[str, Any]:
    source = mechanics._source_module()
    try:
        parsed = source._parse_json(payload)
        positions = {
            message["message_id"]: index
            for index, message in enumerate(row["source_prefix"])
        }
        source._validate_target(
            parsed,
            message_positions=positions,
            query_position=len(row["source_prefix"]) - 1,
            label="generated",
        )
    except Exception as exc:
        return {"valid": False, "error": f"{type(exc).__name__}: {exc}"}
    return {"valid": True, "error": None}


def _generation_kwargs(
    input_ids: Any, attention_mask: Any, stopping: Any
) -> dict[str, Any]:
    return {
        "input_ids": input_ids,
        "attention_mask": attention_mask,
        **GENERATION_SETTINGS,
        "stopping_criteria": stopping,
    }


def run_generation_call(
    run: Path,
    *,
    model: Any,
    tokenizer: Any,
    torch: Any,
    row: dict[str, Any],
    mode: str,
    adapter_name: str,
    stopping_list: Any,
    deadline_seconds: float,
    clock: Any = time.monotonic,
) -> dict[str, Any]:
    """Make one exact prefix-only call and durably retain any returned bytes."""
    stage = f"generation-{mode}"
    input_ids = torch.tensor([row["prefix_ids"]], dtype=torch.long, device="cuda")
    attention_mask = torch.ones_like(input_ids)
    inherited = model.generation_config.to_dict()
    resolved = {
        key: GENERATION_SETTINGS.get(key, inherited.get(key))
        for key in sorted(set(inherited) | set(GENERATION_SETTINGS))
    }
    stage_started = clock()
    hard_deadline = stage_started + deadline_seconds
    deadline = _GenerationDeadline(hard_deadline, clock)
    kwargs = _generation_kwargs(input_ids, attention_mask, stopping_list([deadline]))
    _publish_stage(
        run,
        stage,
        "INTENT",
        hard_deadline=hard_deadline,
        clock=clock,
        mode=mode,
        row_index=row["preview_row_index"],
    )
    receipt: dict[str, Any] = {
        "schema_version": 1,
        "kind": "source-interpreter-fit-generation",
        "mode": mode,
        "status": "INTENT",
        "row_index": row["preview_row_index"],
        "conversation_id": row["conversation_id"],
        "query_index": row["query_index"],
        "query_message_id": row["query_message_id"],
        "prefix_ids": list(row["prefix_ids"]),
        "prefix_length": len(row["prefix_ids"]),
        "target_or_labels_supplied": False,
        "past_key_values_supplied": False,
        "fresh_cache": True,
        "original_trunk_object_id": id(
            model.get_base_model()
            if callable(getattr(model, "get_base_model", None))
            else model
        ),
        "explicit_generation_arguments": dict(GENERATION_SETTINGS),
        "inherited_generation_config": inherited,
        "resolved_generation_config": resolved,
        "stage_started_monotonic": stage_started,
        "hard_deadline_monotonic": hard_deadline,
        "generated_ids": None,
        "complete_output_ids": None,
        "decoded_text": None,
        "decoded_utf8_base64": None,
        "decoded_bytes": None,
        "decoded_sha256": None,
        "strict_output": None,
        "stop_facts": None,
        "whole_call_seconds": None,
        "resource_before": mechanics._resource_receipt(f"{stage}-before", torch),
        "resource_after": None,
    }
    try:
        if mode == "base":
            selection = model.disable_adapter()
        elif mode == "adapter":
            model.set_adapter(adapter_name, inference_mode=True)
            selection = contextlib.nullcontext()
        else:
            raise ValueError(f"unknown generation mode: {mode}")
        with selection:
            receipt["adapter_layers"] = _adapter_layer_state(
                model, mode=mode, adapter_name=adapter_name
            )
            torch.cuda.synchronize()
            began = clock()
            with torch.inference_mode():
                output = model.generate(**kwargs)
            torch.cuda.synchronize()
            receipt["whole_call_seconds"] = clock() - began
            receipt["resource_after"] = mechanics._resource_receipt(
                f"{stage}-after", torch
            )
        complete_ids = output.sequences[0].tolist()
        receipt["complete_output_ids"] = complete_ids
        prefix_ids = list(row["prefix_ids"])
        if complete_ids[: len(prefix_ids)] != prefix_ids:
            raise FitError("generate output does not preserve the exact prefix IDs")
        generated_ids = complete_ids[len(prefix_ids) :]
        receipt["generated_ids"] = generated_ids
        receipt["generated_tokens"] = len(generated_ids)
        terminal_eos = bool(generated_ids and generated_ids[-1] == EOS_TOKEN_ID)
        eos_present = EOS_TOKEN_ID in generated_ids
        payload_ids = generated_ids[:-1] if terminal_eos else generated_ids
        decoded = tokenizer.decode(
            payload_ids,
            skip_special_tokens=False,
            clean_up_tokenization_spaces=False,
        )
        payload = decoded.encode("utf-8")
        strict = _strict_output(payload, row)
        receipt.update(
            {
                "status": "RETURNED",
                "payload_ids": payload_ids,
                "decoded_text": decoded,
                "decoded_utf8_base64": base64.b64encode(payload).decode("ascii"),
                "decoded_bytes": len(payload),
                "decoded_sha256": hashlib.sha256(payload).hexdigest(),
                "strict_output": strict,
                "stop_facts": {
                    "eos_present": eos_present,
                    "terminal_eos": terminal_eos,
                    "cap_reached": len(generated_ids)
                    >= GENERATION_SETTINGS["max_new_tokens"],
                    "deadline_reached": deadline.reached,
                },
                "response_complete": terminal_eos and strict["valid"],
            }
        )
    except Exception as exc:
        receipt.update(
            {
                "status": "TECHNICAL_ERROR",
                "error": f"{type(exc).__name__}: {exc}",
                "deadline_reached": deadline.reached,
            }
        )
    _write_json(Path(run) / f"generation-{mode}.json", receipt)
    stop_facts = receipt.get("stop_facts") or {}
    final_stage_status = (
        "DEADLINE"
        if stop_facts.get("deadline_reached") or receipt.get("deadline_reached")
        else "COMPLETE"
        if receipt["status"] == "RETURNED"
        else "FAILED"
    )
    stage_receipt = _publish_stage(
        run,
        stage,
        final_stage_status,
        hard_deadline=hard_deadline,
        clock=clock,
        mode=mode,
        receipt_path=f"generation-{mode}.json",
        elapsed_seconds=clock() - stage_started,
    )
    if (
        receipt["status"] == "RETURNED"
        and stage_receipt["monotonic"] > hard_deadline
        and not (receipt.get("stop_facts") or {}).get("deadline_reached")
    ):
        receipt["stop_facts"]["deadline_reached"] = True
        receipt["publication_deadline_reached"] = True
        _write_json(Path(run) / f"generation-{mode}.json", receipt)
        _publish_stage(
            run,
            stage,
            "DEADLINE",
            hard_deadline=hard_deadline,
            clock=clock,
            mode=mode,
            receipt_path=f"generation-{mode}.json",
            elapsed_seconds=clock() - stage_started,
        )
    return receipt


def _not_attempted(mode: str, reason: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "kind": "source-interpreter-fit-generation",
        "mode": mode,
        "status": "NOT_ATTEMPTED",
        "reason": reason,
        "generated_ids": None,
        "complete_output_ids": None,
        "decoded_text": None,
        "whole_call_seconds": None,
    }


def run_generation_pair(
    run: Path,
    *,
    model: Any,
    tokenizer: Any,
    torch: Any,
    row: dict[str, Any],
    adapter_name: str,
    stopping_list: Any,
    deadline_seconds: float = GENERATION_STAGE_SECONDS,
    clock: Any = time.monotonic,
) -> dict[str, Any]:
    """Run fixed base-first and adapter-second calls unless a technical stop occurs."""
    run = Path(run)
    run.mkdir(parents=True, exist_ok=True)
    model.eval()
    model.gradient_checkpointing_disable()
    model.config.use_cache = True
    first = run_generation_call(
        run,
        model=model,
        tokenizer=tokenizer,
        torch=torch,
        row=row,
        mode="base",
        adapter_name=adapter_name,
        stopping_list=stopping_list,
        deadline_seconds=deadline_seconds,
        clock=clock,
    )
    if first["status"] != "RETURNED" or first["stop_facts"]["deadline_reached"]:
        status = (
            "INCOMPLETE_DEADLINE"
            if (first.get("stop_facts") or {}).get("deadline_reached")
            or first.get("deadline_reached")
            else "INCOMPLETE_EXCEPTION"
        )
        second = _not_attempted("adapter", f"base call ended with {status}")
        _write_json(run / "generation-adapter.json", second)
        return {"status": status, "calls": [first, second]}
    second = run_generation_call(
        run,
        model=model,
        tokenizer=tokenizer,
        torch=torch,
        row=row,
        mode="adapter",
        adapter_name=adapter_name,
        stopping_list=stopping_list,
        deadline_seconds=deadline_seconds,
        clock=clock,
    )
    if second["status"] != "RETURNED" or second["stop_facts"]["deadline_reached"]:
        status = (
            "INCOMPLETE_DEADLINE"
            if (second.get("stop_facts") or {}).get("deadline_reached")
            or second.get("deadline_reached")
            else "INCOMPLETE_EXCEPTION"
        )
    else:
        status = "COMPLETE"
    same_trunk = first["original_trunk_object_id"] == second["original_trunk_object_id"]
    if not same_trunk:
        return {"status": "INCOMPLETE_EXCEPTION", "calls": [first, second]}
    return {"status": status, "same_original_trunk": True, "calls": [first, second]}


def _publish_fit_step(
    run: Path,
    receipt: dict[str, Any],
) -> None:
    mechanics._publish_step(Path(run), receipt)


def perform_fit_step(
    run: Path,
    *,
    schedule_item: dict[str, Any],
    model: Any,
    optimizer: Any,
    loss_call: Any,
    sync: Any,
    resource: Any,
) -> dict[str, Any]:
    """Perform one update with its exact FIT row bound before optimizer entry."""
    ordinal = schedule_item["ordinal"]
    receipt = {
        **copy_schedule_item(schedule_item),
        "classification": "warm-up" if ordinal == 0 else "timed",
        "status": "INTENT",
        "update_completed": False,
        "update_completion_known": True,
        "validation_completed": False,
        "resource_completed": False,
        "labels_passed_unchanged": True,
        "original_bytes_checked": False,
        "intent_unix": time.time(),
    }
    _publish_fit_step(run, receipt)
    optimizer.zero_grad(set_to_none=True)
    before = mechanics.capture_parameter_state(model, hash_originals=False)
    sync()
    began = time.monotonic()
    loss = loss_call()
    sync()
    receipt["forward_seconds"] = time.monotonic() - began
    loss_value = float(loss.detach().float().item())
    if not math.isfinite(loss_value) or loss_value <= 0:
        raise FitError(f"update {ordinal} loss is not positive finite")
    receipt["loss"] = loss_value
    sync()
    began = time.monotonic()
    loss.backward()
    sync()
    receipt["backward_seconds"] = time.monotonic() - began
    receipt["status"] = "UPDATE_PENDING"
    receipt["update_completed"] = None
    receipt["update_completion_known"] = False
    _publish_fit_step(run, receipt)
    sync()
    began = time.monotonic()
    optimizer.step()
    sync()
    receipt["update_seconds"] = time.monotonic() - began
    receipt["status"] = "UPDATE_CONFIRMED"
    receipt["update_completed"] = True
    receipt["update_completion_known"] = True
    receipt["update_confirmed_unix"] = time.time()
    _publish_fit_step(run, receipt)
    evidence = mechanics.validate_optimizer_step(model, optimizer, before)
    receipt["gradient_and_update"] = evidence
    receipt["validation_completed"] = True
    receipt["status"] = "VALIDATION_CONFIRMED"
    _publish_fit_step(run, receipt)
    receipt["memory"] = resource(f"step-{ordinal}")
    receipt["resource_completed"] = True
    receipt["status"] = "VALIDATED"
    _publish_fit_step(run, receipt)
    return receipt


def copy_schedule_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        key: list(value) if isinstance(value, list) else value
        for key, value in item.items()
    }


def _step_references(run: Path) -> list[dict[str, Any]]:
    references = []
    for ordinal in range(54):
        path = Path(run) / f"step-{ordinal:02d}.json"
        references.append(
            {
                "ordinal": ordinal,
                "path": path.name,
                "bytes": path.stat().st_size,
                "sha256": _sha_file(path),
            }
        )
    return references


def _generation_references(run: Path) -> list[dict[str, Any]]:
    return [
        {
            "mode": mode,
            "path": f"generation-{mode}.json",
            "sha256": _sha_file(Path(run) / f"generation-{mode}.json"),
        }
        for mode in ("base", "adapter")
    ]


def validate_completion(result: dict[str, Any], *, run: Path) -> dict[str, int]:
    if result.get("status") != "COMPLETE" or result.get("mechanical_pass") is not True:
        raise FitError("child result is not COMPLETE")
    if result.get("settings", {}).get("training") != TRAINING_SETTINGS:
        raise FitError("complete result training settings differ")
    references = result.get("step_receipts")
    if type(references) is not list or len(references) != 54:
        raise FitError("complete result lacks 54 step receipts")
    _bindings, rows = validate_artifacts(verify_base_files=False)
    receipts = []
    for ordinal, reference in enumerate(references):
        path = Path(run) / reference.get("path", "")
        if (
            reference.get("ordinal") != ordinal
            or not path.is_file()
            or _sha_file(path) != reference.get("sha256")
        ):
            raise FitError("complete step receipt binding differs")
        receipts.append(_read_json(path, "complete step receipt"))
    schedule = build_schedule(rows)
    for expected, actual in zip(schedule, receipts, strict=True):
        for key in (
            "ordinal",
            "epoch",
            "epoch_position",
            "row_index",
            "conversation_id",
            "family_id",
            "query_index",
            "query_message_id",
            "label_positions",
            "causal_logit_positions",
        ):
            if actual.get(key) != expected[key]:
                raise FitError(f"complete step receipt differs: {key}")
        if (
            actual.get("status") != "VALIDATED"
            or actual.get("update_completed") is not True
        ):
            raise FitError("complete result contains an unvalidated update")
    generation = result.get("generation")
    references = result.get("generation_receipts")
    if (
        generation is None
        or generation.get("status") != "COMPLETE"
        or generation.get("same_original_trunk") is not True
        or type(references) is not list
        or len(references) != 2
    ):
        raise FitError("complete result lacks both returned generation calls")
    generation_calls = []
    for mode, reference in zip(("base", "adapter"), references, strict=True):
        path = Path(run) / reference.get("path", "")
        if (
            reference.get("mode") != mode
            or not path.is_file()
            or _sha_file(path) != reference.get("sha256")
        ):
            raise FitError("complete generation receipt binding differs")
        call = _read_json(path, "complete generation receipt")
        generation_calls.append(call)
        if (
            call.get("mode") != mode
            or call.get("status") != "RETURNED"
            or call.get("whole_call_seconds") is None
            or call.get("complete_output_ids") is None
            or call.get("generated_ids") is None
        ):
            raise FitError("complete result has an incomplete generation call")
        stage = _read_json(
            Path(run) / f"stage-generation_{mode}.json", "generation stage"
        )
        if stage.get("status") != "COMPLETE" or stage.get(
            "monotonic", math.inf
        ) > stage.get("hard_deadline_monotonic", -math.inf):
            raise FitError("complete generation stage exceeded its deadline")
    summaries = generation.get("calls")
    if type(summaries) is not list or len(summaries) != 2:
        raise FitError("complete result lacks generation summaries")
    for summary, call in zip(summaries, generation_calls, strict=True):
        if any(
            summary.get(key) != call.get(key)
            for key in ("mode", "status", "response_complete", "stop_facts")
        ):
            raise FitError("generation summary differs from its durable receipt")
    training_stage = _read_json(Path(run) / "stage-training.json", "training stage")
    if training_stage.get("status") != "COMPLETE" or training_stage.get(
        "monotonic", math.inf
    ) > training_stage.get("hard_deadline_monotonic", -math.inf):
        raise FitError("complete training stage exceeded its deadline")
    if result.get("original_parameters", {}).get("unchanged") is not True:
        raise FitError("complete result lacks frozen-original proof")
    if result.get("adapter_roundtrip", {}).get("exact") is not True:
        raise FitError("complete result lacks exact adapter roundtrip")
    return {"updates": 54, "validated_updates": 54, "generation_calls": 2}


def _partial_update_counts(run: Path) -> dict[str, Any]:
    return mechanics._partial_update_counts(Path(run))


def _current_stage(run: Path) -> dict[str, Any] | None:
    path = Path(run) / "current-stage.json"
    if not path.is_file():
        return None
    try:
        value = _read_json(path, "current stage")
    except FitError:
        return None
    return value if type(value) is dict else None


def _partial_generation_calls(run: Path) -> list[dict[str, Any]]:
    calls = []
    for mode in ("base", "adapter"):
        path = Path(run) / f"generation-{mode}.json"
        if not path.is_file():
            calls.append(
                {
                    "mode": mode,
                    "status": "UNAVAILABLE",
                    "receipt_path": None,
                    "generated_ids_available": False,
                }
            )
            continue
        try:
            value = _read_json(path, "partial generation receipt")
        except FitError:
            calls.append(
                {
                    "mode": mode,
                    "status": "UNAVAILABLE",
                    "receipt_path": path.name,
                    "generated_ids_available": None,
                }
            )
            continue
        calls.append(
            {
                "mode": mode,
                "status": value.get("status", "UNKNOWN"),
                "receipt_path": path.name,
                "receipt_sha256": _sha_file(path),
                "generated_ids_available": value.get("generated_ids") is not None,
            }
        )
    return calls


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
    """Own one child and enforce its durable stage and whole-job deadlines."""
    run = Path(run)
    started = clock() if started_monotonic is None else started_monotonic
    work_deadline = started + reservation_seconds - termination_reserve_seconds
    total_deadline = started + reservation_seconds
    child = None
    child_exit_confirmed = False
    timed_out_stage = None
    termination_requested = False
    termination_reason = None
    launch_error = None
    try:
        _write_json(run / "child-command.json", list(command))
        with (
            (run / "child.stdout.log").open("xb") as stdout,
            (run / "child.stderr.log").open("xb") as stderr,
        ):
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
                while child.poll() is None:
                    now = clock()
                    stage = _current_stage(run)
                    deadline = work_deadline
                    if stage and stage.get("status") == "INTENT":
                        candidate = stage.get("hard_deadline_monotonic")
                        if type(candidate) in (int, float) and math.isfinite(candidate):
                            deadline = min(deadline, float(candidate))
                    if now >= deadline:
                        stage_deadline_active = bool(
                            stage
                            and stage.get("status") == "INTENT"
                            and deadline < work_deadline
                        )
                        timed_out_stage = (
                            stage.get("stage") if stage_deadline_active else "whole-job"
                        )
                        termination_requested = True
                        termination_reason = "stage-deadline"
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
                launch_error = f"{type(exc).__name__}: {exc}"
                if child is not None and child.poll() is None:
                    termination_requested = True
                    termination_reason = "supervisor-error"
                    child_exit_confirmed = mechanics._stop_owned_child(
                        child, total_deadline=total_deadline, clock=clock
                    )
                elif child is not None:
                    child_exit_confirmed = True
    except Exception as exc:
        launch_error = f"{type(exc).__name__}: {exc}"
        if child is not None and child.poll() is None:
            termination_requested = True
            termination_reason = "supervisor-error"
            child_exit_confirmed = mechanics._stop_owned_child(
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
        if timed_out_stage is not None:
            status = "INCOMPLETE_STAGE_TIMEOUT"
        elif launch_error is not None:
            status = "INCOMPLETE_LAUNCH"
        elif child_exit_confirmed and child_exit_code == 0:
            try:
                completion = validate_completion(
                    _read_json(run / "result.json", "child result"), run=run
                )
                status = (
                    "COMPLETE"
                    if child_exit_monotonic <= work_deadline
                    else "INCOMPLETE_DEADLINE"
                )
                exit_code = 0 if status == "COMPLETE" else 2
            except Exception as exc:
                status = "INCOMPLETE_CHILD_RESULT"
                launch_error = f"{type(exc).__name__}: {exc}"
        partial = _partial_update_counts(run)
        exact = completion is not None or partial["update_count_is_exact"]
        confirmed = (
            completion["updates"] if completion else partial["confirmed_updates"]
        )
        lifecycle = {
            "schema_version": 1,
            "kind": "source-interpreter-fit-lifecycle",
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
            "timed_out_stage": timed_out_stage,
            "error": launch_error,
            "partial_files": mechanics._partial_files(run),
            "updates": confirmed if exact else None,
            "confirmed_updates": confirmed,
            "validated_updates": completion["validated_updates"]
            if completion
            else partial["validated_updates"],
            "pending_or_unknown_steps": partial["pending_or_unknown_steps"],
            "update_count_is_exact": exact,
            "generation_calls": _partial_generation_calls(run),
            "run_flag_cleared": False,
            "finalization_within_total_deadline": None,
            "receipt_publication_tail": None,
        }
        _write_json(run / "lifecycle.json", lifecycle)
        if child is None or child_exit_confirmed:
            Path(run_flag).unlink(missing_ok=True)
            lifecycle["run_flag_cleared"] = True
        finalized = clock()
        within_total = finalized <= total_deadline
        if status == "COMPLETE" and not within_total:
            status = "INCOMPLETE_FINALIZATION_DEADLINE"
            exit_code = 2
        lifecycle.update(
            {
                "status": status,
                "ended_monotonic": finalized,
                "elapsed_seconds": finalized - started,
                "ended_unix": wall_clock(),
                "finalization_within_total_deadline": within_total,
                "receipt_publication_tail": {
                    "starts_monotonic": finalized,
                    "included_in_elapsed": False,
                    "bounded_by_outer_process_observation": True,
                    "description": (
                        "Final lifecycle fsync and supervisor exit follow the last "
                        "self-observed monotonic sample."
                    ),
                },
            }
        )
        _write_json(run / "lifecycle.json", lifecycle)
    return exit_code, lifecycle


def _guard_deadline(deadline: float, stage: str) -> None:
    if time.monotonic() >= deadline:
        raise FitError(f"deadline reached before {stage}")


def run_fit(
    run: Path, *, overall_deadline_monotonic: float, training_deadline_monotonic: float
) -> int:
    """Child body; this is the only path that imports ML runtimes or loads a model."""
    run = Path(run)
    child_started = time.monotonic()
    model = optimizer = torch = None
    bindings: dict[str, Any] = {}
    _write_json(
        run / "child-start.json",
        {
            "schema_version": 1,
            "kind": "source-interpreter-fit-child-start",
            "status": "INCOMPLETE",
            "pid": os.getpid(),
            "started_unix": time.time(),
            "started_monotonic": child_started,
            "training_deadline_monotonic": training_deadline_monotonic,
            "overall_deadline_monotonic": overall_deadline_monotonic,
        },
    )
    _publish_stage(
        run,
        "training",
        "INTENT",
        hard_deadline=training_deadline_monotonic,
        updates=54,
    )
    try:
        bindings, rows = validate_artifacts(verify_base_files=True)
        schedule = build_schedule(rows)
        _guard_deadline(training_deadline_monotonic, "ML runtime import")
        import gc

        import peft
        import torch as torch_module
        import transformers
        from peft import LoraConfig, get_peft_model, get_peft_model_state_dict
        from transformers import AutoModelForCausalLM, StoppingCriteriaList

        torch = torch_module
        if not torch.cuda.is_available():
            raise FitError("CUDA is unavailable")
        torch.manual_seed(TRAINING_SETTINGS["seed"])
        torch.cuda.manual_seed_all(TRAINING_SETTINGS["seed"])
        source = mechanics._source_module()
        tokenizer = source.load_tokenizer()
        tokenizer_state = source._tokenizer_state(tokenizer)
        if (
            tokenizer_state != bindings["preview_tokenizer"]["state"]
            or hashlib.sha256(mechanics._json_bytes(tokenizer_state)).hexdigest()
            != bindings["preview_tokenizer"]["state_sha256"]
        ):
            raise FitError("loaded tokenizer state differs from preview")
        _guard_deadline(training_deadline_monotonic, "model load")
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
        config = LoraConfig(
            r=TRAINING_SETTINGS["rank"],
            lora_alpha=TRAINING_SETTINGS["alpha"],
            lora_dropout=TRAINING_SETTINGS["dropout"],
            bias=TRAINING_SETTINGS["bias"],
            task_type="CAUSAL_LM",
            target_modules=["q_proj", "v_proj"],
            inference_mode=False,
        )
        model = get_peft_model(model, config, adapter_name="default")
        trainable = {
            name: parameter
            for name, parameter in model.named_parameters()
            if parameter.requires_grad
        }
        if (
            sum(parameter.numel() for parameter in trainable.values())
            != TRAINING_SETTINGS["trainable_parameters"]
            or not trainable
            or any(
                "lora_" not in name or value.dtype != torch.float32
                for name, value in trainable.items()
            )
        ):
            raise FitError("fresh adapter trainable parameters differ")
        initial_state = mechanics.capture_parameter_state(model)
        optimizer = torch.optim.AdamW(
            list(trainable.values()),
            lr=TRAINING_SETTINGS["learning_rate"],
            betas=tuple(TRAINING_SETTINGS["betas"]),
            eps=TRAINING_SETTINGS["epsilon"],
            weight_decay=TRAINING_SETTINGS["weight_decay"],
        )
        model.train()
        for item in schedule:
            _guard_deadline(training_deadline_monotonic, f"update {item['ordinal']}")
            row = rows[item["row_index"]]
            input_ids = torch.tensor(
                [row["input_ids"]], dtype=torch.long, device="cuda"
            )
            attention_mask = torch.tensor(
                [row["attention_mask"]], dtype=torch.long, device="cuda"
            )
            labels = torch.tensor([row["labels"]], dtype=torch.long, device="cuda")

            def loss_call(
                model=model,
                input_ids=input_ids,
                attention_mask=attention_mask,
                labels=labels,
            ):
                return model(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    labels=labels,
                    use_cache=False,
                ).loss

            receipt = perform_fit_step(
                run,
                schedule_item=item,
                model=model,
                optimizer=optimizer,
                loss_call=loss_call,
                sync=torch.cuda.synchronize,
                resource=lambda stage: mechanics._resource_receipt(stage, torch),
            )
            if receipt["label_positions"] != row["loss_positions"]:
                raise FitError("step label positions differ from the complete row")
            input_ids = attention_mask = labels = None
        _guard_deadline(training_deadline_monotonic, "adapter save")
        saved_state = {
            name: value.detach().cpu().clone()
            for name, value in get_peft_model_state_dict(
                model, adapter_name="default"
            ).items()
        }
        if not saved_state or any(
            value.dtype != torch.float32 for value in saved_state.values()
        ):
            raise FitError("saved adapter state is not complete FP32 state")
        adapter_dir = run / "adapter"
        model.save_pretrained(
            adapter_dir,
            safe_serialization=True,
            selected_adapters=["default"],
        )
        weights_path = adapter_dir / "adapter_model.safetensors"
        config_path = adapter_dir / "adapter_config.json"
        if not weights_path.is_file() or not config_path.is_file():
            raise FitError("standard PEFT save is incomplete")
        archive = mechanics.archive_file(
            weights_path, run / "archive", max_part_bytes=ARCHIVE_PART_BYTES
        )
        _write_json(run / "archive-manifest.json", archive)
        reconstructed = run / "reconstructed-adapter"
        reconstructed.mkdir(parents=False, exist_ok=False)
        shutil.copyfile(config_path, reconstructed / "adapter_config.json")
        reconstruction = mechanics.reconstruct_archive(
            archive, run / "archive", reconstructed / "adapter_model.safetensors"
        )
        load_result = model.load_adapter(
            reconstructed,
            adapter_name="roundtrip",
            is_trainable=False,
            autocast_adapter_dtype=True,
            local_files_only=True,
        )
        load_receipt = mechanics._adapter_load_receipt(load_result)
        roundtrip_state = {
            name: value.detach().cpu().clone()
            for name, value in get_peft_model_state_dict(
                model, adapter_name="roundtrip"
            ).items()
        }
        mechanics.compare_adapter_states(saved_state, roundtrip_state)
        adapter_receipt = {
            "saved_state_keys": sorted(saved_state),
            "saved_state": {
                name: {
                    "shape": list(value.shape),
                    "dtype": str(value.dtype),
                    "numel": value.numel(),
                    "sha256": mechanics._parameter_digest(value),
                }
                for name, value in saved_state.items()
            },
            "weights_bytes": weights_path.stat().st_size,
            "weights_sha256": _sha_file(weights_path),
            "config_sha256": _sha_file(config_path),
            "reconstructed_config_sha256": _sha_file(
                reconstructed / "adapter_config.json"
            ),
            "archive": archive,
            "reconstruction": reconstruction,
            "load": load_receipt,
            "exact": True,
        }
        training_completion = _publish_stage(
            run,
            "training",
            "COMPLETE",
            hard_deadline=training_deadline_monotonic,
            updates=54,
            adapter_roundtrip_exact=True,
        )
        if training_completion["monotonic"] > training_deadline_monotonic:
            raise FitError("training stage publication exceeded its deadline")
        pair = run_generation_pair(
            run,
            model=model,
            tokenizer=tokenizer,
            torch=torch,
            row=rows[GENERATION_ROW_INDEX],
            adapter_name="roundtrip",
            stopping_list=StoppingCriteriaList,
        )
        if pair["status"] != "COMPLETE":
            raise FitError(
                f"generation pair is technically incomplete: {pair['status']}"
            )
        _guard_deadline(overall_deadline_monotonic, "final original-parameter check")
        frozen = mechanics.validate_frozen_originals(model, initial_state["originals"])
        final_resource = mechanics._resource_receipt("before-cleanup", torch)
        cleanup_intent = _publish_stage(
            run,
            "cleanup",
            "INTENT",
            hard_deadline=overall_deadline_monotonic,
        )
        if cleanup_intent["monotonic"] > overall_deadline_monotonic:
            raise FitError("cleanup stage publication exceeded the working deadline")
        del optimizer
        del model
        gc.collect()
        torch.cuda.empty_cache()
        cleanup_completion = _publish_stage(
            run,
            "cleanup",
            "COMPLETE",
            hard_deadline=overall_deadline_monotonic,
        )
        if cleanup_completion["monotonic"] > overall_deadline_monotonic:
            raise FitError("cleanup completion exceeded the working deadline")
        _publish_stage(
            run,
            "finalization",
            "INTENT",
            hard_deadline=overall_deadline_monotonic,
        )
        generation_references = _generation_references(run)
        generation_summary = {
            "status": pair["status"],
            "same_original_trunk": pair["same_original_trunk"],
            "calls": [
                {
                    "mode": call["mode"],
                    "status": call["status"],
                    "response_complete": call["response_complete"],
                    "stop_facts": call["stop_facts"],
                }
                for call in pair["calls"]
            ],
        }
        result = {
            "schema_version": 1,
            "kind": "source-interpreter-fit-result",
            "status": "COMPLETE",
            "mechanical_pass": True,
            "semantic_evidence": False,
            "fit_on": "all eighteen accepted FIT rows",
            "evaluated_on": "none",
            "bindings": bindings,
            "settings": {
                "training": TRAINING_SETTINGS,
                "generation": GENERATION_SETTINGS,
            },
            "runtime": {
                "python": sys.version,
                "packages": {
                    "torch": torch.__version__,
                    "transformers": transformers.__version__,
                    "peft": peft.__version__,
                },
            },
            "step_receipts": _step_references(run),
            "generation_receipts": generation_references,
            "generation": generation_summary,
            "responses_complete": all(
                call.get("response_complete") is True for call in pair["calls"]
            ),
            "original_parameters": {**frozen, "unchanged": True},
            "adapter_roundtrip": adapter_receipt,
            "final_resource": final_resource,
            "timings": {"total_child_seconds": time.monotonic() - child_started},
        }
        validate_completion(result, run=run)
        _write_json(run / "result.json", result)
        finalization = _publish_stage(
            run,
            "finalization",
            "COMPLETE",
            hard_deadline=overall_deadline_monotonic,
        )
        if finalization["monotonic"] > overall_deadline_monotonic:
            raise FitError("result publication exceeded the working deadline")
        return 0
    except BaseException as exc:
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise
        _write_json(
            run / "failure.json",
            {
                "schema_version": 1,
                "kind": "source-interpreter-fit-failure",
                "status": "INCOMPLETE",
                "error": f"{type(exc).__name__}: {exc}",
                "current_stage": _current_stage(run),
                "partial_updates": _partial_update_counts(run),
                "ended_unix": time.time(),
            },
        )
        return 2


def _active_flags(root: Path = ROOT) -> list[Path]:
    return sorted(Path(root).joinpath("results").rglob("RUNNING.flag"))


def _ensure_no_active_flags(root: Path = ROOT) -> None:
    flags = _active_flags(root)
    if flags:
        raise FitError(f"an active run flag exists: {flags[0]}")


def _command(command: list[str], *, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(command, check=check, capture_output=True)


def _qualify_environment() -> dict[str, Any]:
    _ensure_no_active_flags()
    gpu = _command(["nvidia-smi", "--query-compute-apps=pid", "--format=csv,noheader"])
    if gpu.stdout.strip():
        raise FitError("a GPU compute process is active")
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
            raise FitError(f"bound file is dirty or untracked: {relative}")
    head = (
        _command(["git", "-C", str(ROOT), "rev-parse", "HEAD"]).stdout.decode().strip()
    )
    if len(head) != 40:
        raise FitError("current git HEAD could not be resolved")
    return {"git_head": head, "gpu_compute_processes": [], "active_flags": []}


def _acquire_review_lock():
    handle = REVIEW_LOCK.open("a+", encoding="utf-8")
    try:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as exc:
        handle.close()
        raise FitError("review lock is active") from exc
    return handle


def _reserve_flag(run: Path) -> None:
    payload = (
        json.dumps(
            {"pid": os.getpid(), "run_dir": str(run), "kind": "source-interpreter-fit"},
            sort_keys=True,
        ).encode("utf-8")
        + b"\n"
    )
    descriptor = os.open(RUN_FLAG, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())


def make_plan(run: Path) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "kind": "source-interpreter-fit-launch-plan",
        "execute": False,
        "run_dir": str(Path(run)),
        "model": str(MODEL_PATH),
        "input_manifest": str(INPUTS_PATH),
        "preview": str(PREVIEW_PATH),
        "settings": {
            "training": TRAINING_SETTINGS,
            "generation": GENERATION_SETTINGS,
        },
        "schedule": [list(epoch) for epoch in ROW_SCHEDULE],
        "generation_row_index": GENERATION_ROW_INDEX,
        "reservation_seconds": int(RESERVATION_SECONDS),
        "working_seconds": int(WORKING_SECONDS),
        "training_stage_seconds": int(TRAINING_STAGE_SECONDS),
        "generation_stage_seconds": int(GENERATION_STAGE_SECONDS),
        "termination_reserve_seconds": int(TERMINATION_RESERVE_SECONDS),
        "outer_observer_required": True,
        "outer_observer_contract": (
            "Root must time and bound the complete supervisor process through final "
            "lifecycle publication and exit."
        ),
        "child_command": [
            str(ROOT / ".venv/bin/python"),
            str(Path(__file__).resolve()),
            "--_child",
            "--run-dir",
            str(Path(run)),
            "--overall-deadline-monotonic",
            "<set-by-supervisor>",
            "--training-deadline-monotonic",
            "<set-by-supervisor>",
        ],
        "dry_run_loads_model": False,
        "dry_run_uses_cuda": False,
        "dry_run_starts_child": False,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-dir", type=Path)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--_qualify-only", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--_child", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument(
        "--overall-deadline-monotonic", type=float, help=argparse.SUPPRESS
    )
    parser.add_argument(
        "--training-deadline-monotonic", type=float, help=argparse.SUPPRESS
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    internal_values = (
        args.run_dir,
        args.execute,
        args._child,
        args.overall_deadline_monotonic,
        args.training_deadline_monotonic,
    )
    if args._qualify_only:
        if internal_values != (None, False, False, None, None):
            raise ValueError("qualification-only mode cannot be combined")
        _ensure_no_active_flags()
        bindings, rows = validate_artifacts(verify_base_files=False)
        print(
            json.dumps(
                {
                    "kind": "source-interpreter-fit-qualification",
                    "status": "PASS",
                    "model_loaded": False,
                    "gpu_used": False,
                    "rows": len(rows),
                    "updates": TRAINING_SETTINGS["updates"],
                    "generation_calls": 2,
                    "bindings": {
                        "runner_sha256": bindings["runner_sha256"],
                        "test_sha256": bindings["test_sha256"],
                    },
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
            "run-dir must be a run-* direct child of results/source-interpreter/fit"
        )
    if args._child:
        if (
            args.execute
            or args.overall_deadline_monotonic is None
            or args.training_deadline_monotonic is None
            or not run.is_dir()
        ):
            raise ValueError("internal child requires an existing run and deadlines")
        return run_fit(
            run,
            overall_deadline_monotonic=args.overall_deadline_monotonic,
            training_deadline_monotonic=args.training_deadline_monotonic,
        )
    if (
        args.overall_deadline_monotonic is not None
        or args.training_deadline_monotonic is not None
    ):
        raise ValueError("deadline arguments are internal only")
    _ensure_no_active_flags()
    plan = make_plan(run)
    if not args.execute:
        print(json.dumps(plan, ensure_ascii=True, indent=2, sort_keys=True))
        return 0
    if run.exists():
        raise FitError("run directory is occupied")
    started = time.monotonic()
    overall_deadline = started + WORKING_SECONDS
    training_deadline = started + TRAINING_STAGE_SECONDS
    mechanics.register_pid(os.getpid())
    review_handle = _acquire_review_lock()
    flag_reserved = run_created = child_started = False
    try:
        environment = _qualify_environment()
        bindings, _rows = validate_artifacts(verify_base_files=False)
        _guard_deadline(training_deadline, "child launch")
        _reserve_flag(run)
        flag_reserved = True
        run.mkdir(parents=True, exist_ok=False)
        run_created = True
        plan["execute"] = True
        plan["child_command"][-3] = repr(overall_deadline)
        plan["child_command"][-1] = repr(training_deadline)
        _write_json(
            run / "start.json",
            {
                "schema_version": 1,
                "kind": "source-interpreter-fit-start",
                "status": "INCOMPLETE",
                "supervisor_pid": os.getpid(),
                "started_unix": time.time(),
                "started_monotonic": started,
                "work_deadline_monotonic": overall_deadline,
                "total_deadline_monotonic": started + RESERVATION_SECONDS,
                "training_deadline_monotonic": training_deadline,
                "environment": environment,
                "bindings": bindings,
                "plan": plan,
            },
        )
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
                    "kind": "source-interpreter-fit-lifecycle",
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
