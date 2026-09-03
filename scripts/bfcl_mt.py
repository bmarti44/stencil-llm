#!/usr/bin/env python3
"""Minimal no-server BFCL V3 multi-turn runner for the hand-rolled Qwen trunk."""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib
import inspect
import json
import re
import subprocess
import sys
import time
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "vendor"))

from stencil import determinism  # noqa: F401, E402
from stencil.bfcl import (  # noqa: E402
    ARMS,
    CATEGORIES,
    ECHO_HEADER,
    FUNCTION_DOCS,
    REDUCED_ARMS,
    assert_case_record_schema,
    atomic_json,
    budget_history_spans,
    build_matched_control,
    call_to_python,
    canonical_call,
    context_layout,
    echo_copy_flag,
    ensure_split_allowed,
    execute_call_strings,
    parse_tool_calls,
    position_overflow_result,
    prepare_case,
    prior_user_spans,
    recency_pinned_plan,
    render_echo,
    resolve_pin_overflow,
    score_case,
    select_history_spans,
    summarize_records,
    tool_swap_plan,
)

K = 8192
MAX_STEPS = 20
COHORT_SEED = 20260902
CONTROL_TIE_BREAK = "nearest-width, nearest-turn, stable-source"
CHUNK_TOKENS = 128
ECHO_CAP = 1024
BUDGET_FRACTION = 0.25
SELECTOR_THRESHOLD = 0.5
ADDED_FUNCTION_PROMPT = (
    "I have updated some more functions you can choose from. What about now?"
)
DATA = ROOT / "data/bench/bfcl_v3_mt"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command", choices=("run", "preflight"), default="run", nargs="?"
    )
    parser.add_argument("--split", choices=("dev", "sealed"), default="dev")
    parser.add_argument("--trunk", choices=("1.7b", "4b"), default="1.7b")
    parser.add_argument("--mode", choices=("teacher", "free"), default="teacher")
    parser.add_argument("--max-new", type=int, default=512)
    parser.add_argument("--deadline", type=float, default=300.0)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--out", default="bfcl-evict-v3")
    parser.add_argument("--preflight-certificate", type=Path)
    parser.add_argument(
        "--arm-cut",
        action="store_true",
        help="apply the registered >30 GPU-h reduced arm set",
    )
    args = parser.parse_args(argv)
    ensure_split_allowed(args.split)
    if args.max_new <= 0 or args.deadline <= 0:
        parser.error("--max-new and --deadline must be positive")
    if args.command == "preflight" and args.split != "dev":
        parser.error("--preflight is dev-only")
    if args.command == "preflight" and args.mode != "teacher":
        parser.error("preflight requires --mode teacher")
    if args.command == "preflight" and args.limit is not None:
        parser.error("preflight always runs the complete 32-case dev slice")
    if args.command == "preflight" and args.arm_cut:
        parser.error("preflight measures the full arm set; --arm-cut is invalid")
    if args.split == "sealed":
        if args.limit is not None:
            parser.error("sealed runs forbid --limit")
        if args.command != "run" or args.mode != "teacher":
            parser.error("sealed execution requires run --mode teacher")
        if (
            args.preflight_certificate is None
            or not args.preflight_certificate.is_file()
        ):
            parser.error("sealed run requires an existing --preflight-certificate")
    return args


def sha256(path: str | Path) -> str:
    with Path(path).open("rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def _read_verified_bytes(path: Path, expected_sha256: str) -> bytes:
    """Read and verify immutable input bytes from one file handle."""
    with path.open("rb") as handle:
        raw = handle.read()
    actual = hashlib.sha256(raw).hexdigest()
    if actual != expected_sha256:
        raise RuntimeError(f"frozen input hash mismatch: {path}")
    return raw


def _load_verified_json(path: Path, expected_sha256: str) -> object:
    """Hash and decode the exact bytes read from one file handle."""
    return json.loads(_read_verified_bytes(path, expected_sha256))


def _read_indexed_row(
    root: Path, entry: dict, case_id: str
) -> tuple[dict, str, str]:
    """Bounded-read, hash, identify, and decode one authorized BFCL record."""
    path = root / entry["file"]
    with path.open("rb") as handle:
        handle.seek(int(entry["offset"]))
        raw = handle.read(int(entry["length"]))
    actual = hashlib.sha256(raw).hexdigest()
    if actual != entry.get("sha256"):
        raise RuntimeError(f"indexed BFCL record hash mismatch: {case_id}")
    match = re.search(rb'"id"\s*:\s*"([^"\\]+)"', raw)
    if match is None or match.group(1).decode() != case_id:
        raise RuntimeError(f"indexed BFCL id mismatch before decode: {case_id}")
    row = json.loads(raw)
    if str(row["id"]) != case_id:
        raise RuntimeError(f"decoded BFCL id mismatch: {case_id}")
    return row, str(entry["category"]), actual


def registration_text_and_hash() -> tuple[str, str]:
    """Return exactly LEG A v7 plus its LEG A amendments and SHA-256."""
    ledger = (ROOT / "LEDGER-PLAN.md").read_text()
    header = (
        "## SELECTOR v2 — POST-DEVELOPMENT EVALUATION, LEG A (BFCL V3 multi-turn) — v7"
    )
    start = ledger.index(header)
    leg_b_a3 = ledger.index("\n### LEG B AMENDMENT 3", start)
    leg_a_a3 = ledger.index("\n### LEG A AMENDMENT 3", leg_b_a3)
    next_section = ledger.find("\n## ", leg_a_a3 + 1)
    a3_end = len(ledger) if next_section < 0 else next_section
    text = ledger[start:leg_b_a3] + ledger[leg_a_a3:a3_end]
    return text, hashlib.sha256(text.encode()).hexdigest()


def _tree_sha256(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(str(path.relative_to(ROOT)).encode() + b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def git_provenance() -> dict:
    """Return the exact repository revision and porcelain dirty state."""
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.rstrip("\n")
    return {"commit": commit, "dirty": bool(status), "status": status}


def assert_clean_git_for_sealed() -> dict:
    """Sealed execution is valid only from a committed, clean harness tree."""
    provenance = git_provenance()
    if provenance["dirty"]:
        raise RuntimeError("sealed run requires a clean git worktree")
    return provenance


def harness_manifest() -> dict:
    """Canonical hashes for every local module that can execute in this harness."""
    runtime_imports = [
        "stencil.ledger",
        "stencil.qwen3",
        "stencil.qwen_cache",
        "stencil.selector_v2",
        "bfcl_eval.eval_checker.multi_turn_eval.multi_turn_checker",
        "bfcl_eval.eval_checker.multi_turn_eval.multi_turn_utils",
        *(
            "bfcl_eval.eval_checker.multi_turn_eval.func_source_code." + name
            for name in (
                "gorilla_file_system",
                "long_context",
                "math_api",
                "message_api",
                "posting_api",
                "ticket_api",
                "trading_bot",
                "travel_booking",
                "vehicle_control",
            )
        ),
    ]
    for name in runtime_imports:
        importlib.import_module(name)
    paths = {ROOT / "scripts/bfcl_mt.py"}
    for name, module in tuple(sys.modules.items()):
        if not (name.startswith("stencil") or name.startswith("bfcl_eval")):
            continue
        if name in {"stencil.bench"} or name.startswith("vendor.ifeval"):
            continue
        raw_path = getattr(module, "__file__", None)
        if not raw_path:
            continue
        path = Path(raw_path).resolve()
        if path.suffix == ".py" and path.is_relative_to(ROOT):
            paths.add(path)
    files = {str(path.relative_to(ROOT)): sha256(path) for path in sorted(paths)}
    files["chat_template:render_prompt"] = hashlib.sha256(
        inspect.getsource(render_prompt).encode()
    ).hexdigest()
    return {"files": files, "sha256": _canonical_sha256(files)}


def certificate_payload(meta: dict, gates: dict) -> dict:
    """Signed preflight contract, excluding dev-only report presentation."""
    return {
        "schema": 1,
        "trunk": meta["trunk"],
        "arms": list(meta["arms"]),
        "generation": {
            "max_new": meta.get("max_new"),
            "deadline": meta.get("deadline"),
            "greedy": meta.get("greedy", True),
            "thinking": meta.get("thinking", False),
        },
        "constants": {
            key: meta.get(key)
            for key in (
                "k",
                "budget_fraction",
                "chunk_tokens",
                "echo_cap",
                "selector_threshold",
                "echo_header",
                "control_tie_break",
            )
        },
        "registration_sha256": meta.get("registration_sha256"),
        "frozen_hashes": meta.get("frozen_hashes", {}),
        "classifier_sha256": meta.get("classifier_sha256", {}),
        "gates": gates,
    }


def _gate_passed(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, dict):
        for key in ("passed", "passed_all"):
            if key in value:
                return bool(value[key])
    return False


def validate_preflight_certificate(path: Path, meta: dict) -> str:
    report = json.loads(path.read_text())
    if report.get("status") != "PASSED" or "certificate" not in report:
        raise RuntimeError("sealed run requires a passing preflight certificate")
    payload = report["certificate"]
    digest = _canonical_sha256(payload)
    if report.get("certificate_sha256") != digest:
        raise RuntimeError("preflight certificate digest mismatch")
    required = {"competence", "determinism", "feasibility", "invariants", "cost"}
    if set(payload.get("gates", {})) != required or not all(
        _gate_passed(payload["gates"][gate]) for gate in required
    ):
        raise RuntimeError("preflight certificate contains a failed gate")
    expected = certificate_payload(meta, {})
    actual_contract = dict(payload)
    actual_contract["gates"] = {}
    if actual_contract != expected:
        raise RuntimeError("preflight certificate does not match sealed run contract")
    return digest


def _load_cases_verified(
    split: str, limit: int | None = None
) -> tuple[list[tuple[str, dict, list]], dict]:
    index_path = DATA / "offsets.json"
    pins_path = ROOT / "data/bench/pins-manifest.json"
    with pins_path.open("rb") as handle:
        pins_raw = handle.read()
    pins = json.loads(pins_raw)["pins"][
        "ShishirPatil/gorilla BFCL V3 multi-turn"
    ]
    with index_path.open("rb") as handle:
        index_raw = handle.read()
    index_digest = hashlib.sha256(index_raw).hexdigest()
    if index_digest != pins["offsets_sha256"]:
        raise RuntimeError("BFCL offsets index hash mismatch")
    index = json.loads(index_raw)
    if int(index.get("schema", 0)) < 2:
        raise RuntimeError("BFCL offsets index lacks per-record hashes")
    if split == "sealed":
        # Authorized sealed invocations bind the complete mixed sources before
        # any cohort row is decoded.  Dev never scans these mixed files.
        for relative, expected in index["source_files_sha256"].items():
            actual = sha256(ROOT / relative)
            if actual != expected or actual != pins["files_sha256"].get(relative):
                raise RuntimeError(f"frozen BFCL source hash mismatch: {relative}")
    cohort = list(index["cohorts"][split])
    ids = cohort[:limit] if limit is not None else cohort
    requested = set(ids)
    rows = []
    record_hashes = {}
    for case_id in ids:
        if case_id not in requested:
            raise AssertionError("indexed row is outside requested cohort")
        case, category, case_digest = _read_indexed_row(
            ROOT, index["records"][case_id]["case"], case_id
        )
        answer, answer_category, answer_digest = _read_indexed_row(
            ROOT, index["records"][case_id]["answer"], case_id
        )
        if category != answer_category:
            raise RuntimeError(f"indexed BFCL category mismatch: {case_id}")
        rows.append((category, case, answer["ground_truth"]))
        record_hashes[f"{case_id}:case"] = case_digest
        record_hashes[f"{case_id}:answer"] = answer_digest
    verified = {
        "offsets": index_digest,
        "pins_manifest": hashlib.sha256(pins_raw).hexdigest(),
        "records": record_hashes,
        "source_files": (
            dict(index["source_files_sha256"]) if split == "sealed" else {}
        ),
    }
    return rows, verified


def load_cases(split: str, limit: int | None = None) -> list[tuple[str, dict, list]]:
    rows, _ = _load_cases_verified(split, limit)
    return rows


def _load_verified_runtime_inputs(pins: dict) -> tuple[dict, dict]:
    """Load function docs once and hash every prompt/checker byte source."""
    function_docs = {}
    docs_by_class = {}
    for class_name, filename in FUNCTION_DOCS.items():
        path = DATA / "function_docs" / filename
        relative = str(path.relative_to(ROOT))
        expected = pins["files_sha256"].get(relative, "")
        raw = _read_verified_bytes(path, expected)
        actual = hashlib.sha256(raw).hexdigest()
        function_docs[relative] = actual
        docs_by_class[class_name] = [
            json.loads(line) for line in raw.splitlines() if line
        ]
    checker_files = {}
    for relative, expected in pins["files_sha256"].items():
        if not (
            relative.startswith("vendor/bfcl_eval/") and relative.endswith(".py")
        ):
            continue
        actual = sha256(ROOT / relative)
        if actual != expected:
            raise RuntimeError(f"frozen input hash mismatch: {relative}")
        checker_files[relative] = actual
    return docs_by_class, {
        "function_docs": function_docs,
        "checker": checker_files,
    }


def load_model(trunk: str):
    import torch
    from tokenizers import Tokenizer

    from stencil.qwen3 import Qwen3, Qwen3Config

    model_dir = ROOT / f"models/qwen3-{trunk}-hf"
    tokenizer = Tokenizer.from_file(str(model_dir / "tokenizer.json"))
    config = Qwen3Config.from_hf(model_dir / "config.json")
    model = Qwen3(config)
    state = torch.load(
        ROOT / f"models/qwen3-{trunk}.pt", map_location="cpu", weights_only=True
    )
    model.load_state_dict(state, strict=True)
    return model.to(torch.bfloat16).cuda().eval(), tokenizer


def render_prompt(messages: list[dict], tools: list[dict]) -> str:
    """Qwen3 tool template, fixed to non-thinking generation."""
    prompt = "<|im_start|>system\n"
    if messages and messages[0]["role"] == "system":
        prompt += messages[0]["content"] + "\n\n"
    prompt += (
        "# Tools\n\nYou may call one or more functions to assist with the user "
        "query.\n\n"
        "You are provided with function signatures within <tools></tools> XML tags:\n"
        "<tools>"
    )
    for tool in tools:
        prompt += "\n" + json.dumps(tool)
    prompt += (
        "\n</tools>\n\nFor each function call, return a json object with function "
        "name and arguments within <tool_call></tool_call> XML tags:\n"
        '<tool_call>\n{"name": <function-name>, "arguments": <args-json-object>}\n'
        "</tool_call><|im_end|>\n"
    )
    start = 1 if messages and messages[0]["role"] == "system" else 0
    for index, message in enumerate(messages[start:], start=start):
        role = message["role"]
        content = message.get("content", "")
        if role in {"user", "system"}:
            prompt += f"<|im_start|>{role}\n{content}<|im_end|>\n"
        elif role == "assistant":
            prompt += f"<|im_start|>assistant\n{content}<|im_end|>\n"
        elif role == "tool":
            previous = messages[index - 1]["role"] if index else None
            following = (
                messages[index + 1]["role"] if index + 1 < len(messages) else None
            )
            if previous != "tool":
                prompt += "<|im_start|>user"
            prompt += f"\n<tool_response>\n{content}\n</tool_response>"
            if following != "tool":
                prompt += "<|im_end|>\n"
    return prompt + "<|im_start|>assistant\n<think>\n\n</think>\n\n"


def generate(
    model,
    tokenizer,
    prompt: str,
    *,
    evict_range,
    keep,
    allow_eviction: bool,
    max_new: int,
    deadline: float,
    cache=None,
    continuation_ids: list[int] | None = None,
):
    import torch

    from stencil.qwen3 import KVCache, prefill_with_eviction

    eos = {151645, 151643}

    ids = tokenizer.encode(prompt).ids
    if not ids:
        raise ValueError("empty prompt")
    device = next(model.parameters()).device
    cache = cache or KVCache(model.cfg)
    generated = []
    started = time.monotonic()
    timed_out = False
    position_overflow = False
    evicted = False
    pin_overflow = 0
    with torch.no_grad():
        if continuation_ids is not None:
            columns_before = int(cache.k[0].shape[2])
            logits = model(torch.tensor([continuation_ids], device=device), cache=cache)
            columns_after = int(cache.k[0].shape[2])
            index_map = {}
            active_keep = list(keep)
        else:
            if evict_range is None:
                raise ValueError("initial turn generation requires an eviction range")
            history_end = int(evict_range[1])
            protected_end = int(evict_range[0])
            active_keep = list(keep)
            actual_range = (
                tuple(evict_range)
                if allow_eviction and evict_range is not None and history_end > K
                else None
            )
            logits, index_map, columns_before, columns_after = prefill_with_eviction(
                model,
                cache,
                torch.tensor([ids], device=device),
                history_end=history_end,
                evict_range=actual_range,
                keep=active_keep,
            )
            evicted = actual_range is not None
        pinned_columns = (
            sum(
                column in index_map
                for start, end in active_keep
                for column in range(start, end)
            )
            if evicted
            else 0
        )
        protected_prefix_survived = (
            all(column in index_map for column in range(protected_end))
            if evicted
            else True
        )
        if not protected_prefix_survived:
            raise AssertionError("protected prefix did not survive eviction")
        next_token = int(logits[0, -1].argmax())
        while next_token not in eos and len(generated) < max_new:
            if time.monotonic() - started > deadline:
                timed_out = True
                break
            generated.append(next_token)
            if int(cache.k[0].shape[2]) + 1 > 40960:
                position_overflow = True
                break
            logits = model(torch.tensor([[next_token]], device=device), cache=cache)
            next_token = int(logits[0, -1].argmax())
    return {
        "text": tokenizer.decode(generated, skip_special_tokens=False),
        "token_ids": generated,
        "truncated": len(generated) >= max_new or position_overflow,
        "timeout": timed_out,
        "evicted": evicted,
        "prompt_tokens": len(ids),
        "columns_before": columns_before,
        "columns_after": columns_after,
        "pinned_columns": pinned_columns,
        "evictable_size": (
            int(evict_range[1]) - int(evict_range[0]) if evict_range is not None else 0
        ),
        "pin_overflow": pin_overflow,
        "protected_prefix_survived": protected_prefix_survived,
        "position_overflow": position_overflow,
        "overflow_phase": "within_generation" if position_overflow else None,
        "current_turn_prefilled_before_eviction": (
            columns_before != int(evict_range[1])
            if continuation_ids is None and evict_range is not None
            else False
        ),
        "columns_after_step": int(cache.k[0].shape[2]),
        "_cache": cache,
    }


def _tool_step_suffix(tokenizer, outputs: list[str]) -> list[int]:
    body = "<|im_end|>\n<|im_start|>user"
    for output in outputs:
        body += f"\n<tool_response>\n{output}\n</tool_response>"
    body += "<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"
    return list(tokenizer.encode(body).ids)


def _echo_current_user(
    context: str, entries: list[dict], *, close: int | None = None
) -> str:
    if not entries:
        return context
    if close is None:
        marker = context.rfind("<|im_start|>user\n")
        close = context.find("<|im_end|>", marker)
        if marker < 0 or close < 0:
            raise ValueError("current user turn is not closed")
    rendered = render_echo(entries)
    return context[:close] + "\n\n" + rendered + context[close:]


def teacher_forced_turn_contexts(
    tokenizer, messages: list[dict], tools: list[dict], arms, trunk=None
) -> dict[str, dict]:
    """Build and assert the arm-independent pre-intervention context IDs."""
    context = render_prompt(messages, tools)
    ids = list(tokenizer.encode(context).ids)
    contexts = {arm: {"context": context, "context_ids": list(ids)} for arm in arms}
    if trunk is not None:
        for arm, row in contexts.items():
            row["stub_output"] = trunk(row["context_ids"], arm=arm)
    if len({tuple(row["context_ids"]) for row in contexts.values()}) != 1:
        raise AssertionError("teacher-forced contexts differ across arms")
    return contexts


def _call_string_to_json(call: str, tools: list[dict] | None = None) -> dict:
    tree = ast.parse(call.strip(), mode="eval").body
    if not isinstance(tree, ast.Call):
        raise ValueError(f"ground-truth call is not a call: {call}")
    name = tree.func.attr if isinstance(tree.func, ast.Attribute) else tree.func.id
    parameter_names: list[str] = []
    if tools:
        schema = next((row for row in tools if row.get("name") == name), None)
        parameter_names = list(
            (schema or {}).get("parameters", {}).get("properties", {})
        )
    if tree.args and len(parameter_names) < len(tree.args):
        raise ValueError(
            f"cannot name positional arguments for ground-truth call: {call}"
        )
    arguments = {
        parameter_names[index]: ast.literal_eval(value)
        for index, value in enumerate(tree.args)
    }
    arguments.update(
        {keyword.arg: ast.literal_eval(keyword.value) for keyword in tree.keywords}
    )
    return {"name": name, "arguments": arguments}


def canonical_repeated_call_set(
    prior_ground_truth: list[list[str]], tools: list[dict], entries: list[dict]
) -> set[str]:
    """Canonical calls that repetition safety treats as prior/echoed."""
    calls = {
        canonical_call(_call_string_to_json(call, tools))
        for turn in prior_ground_truth
        for call in turn
    }
    for entry in entries:
        text = str(entry.get("text", "")).strip()
        parsed_rows = parse_tool_calls(text)
        for parsed in parsed_rows:
            if parsed.valid and parsed.call is not None:
                try:
                    calls.add(canonical_call(parsed.call))
                except ValueError:
                    pass
        if not parsed_rows:
            try:
                value = json.loads(text)
            except json.JSONDecodeError:
                value = None
            if (
                isinstance(value, dict)
                and isinstance(value.get("name"), str)
                and isinstance(value.get("arguments"), dict)
            ):
                try:
                    calls.add(canonical_call(value))
                except ValueError:
                    pass
    return calls


def repeated_call_event(
    call: dict, prior_calls: set[str], current_ground_truth: set[str]
) -> bool:
    """Apply the execution canonicalizer at the repetition decision point."""
    normalized = canonical_call(call)
    return normalized in prior_calls and normalized not in current_ground_truth


def build_teacher_history(
    case: dict, ground_truth: list, turn_index: int, run_name: str
) -> list[dict]:
    """Execute and render every ground-truth turn before ``turn_index``."""
    messages: list[dict] = []
    tools = case["function"]
    holdouts = case.get("missed_function", {})
    for prior in range(turn_index):
        if str(prior) in holdouts:
            tools.extend(holdouts[str(prior)])
            messages.append({"role": "user", "content": ADDED_FUNCTION_PROMPT})
        else:
            messages.extend(case["question"][prior])
        calls = list(ground_truth[prior])
        rendered_calls = "\n".join(
            "<tool_call>"
            + json.dumps(_call_string_to_json(call, tools), separators=(",", ":"))
            + "</tool_call>"
            for call in calls
        )
        messages.append({"role": "assistant", "content": rendered_calls})
        outputs, _ = execute_call_strings(calls, case, run_name)
        messages.extend({"role": "tool", "content": output} for output in outputs)
    return messages


def _echo_cap(
    tokenizer, entries: list[dict], context: str, close: int, *, cap: int = ECHO_CAP
) -> tuple[list[dict], int]:
    chosen: list[dict] = []
    for row in entries:
        proposed = [*chosen, row]
        echoed = _echo_current_user(context, proposed, close=close)
        tokens = len(tokenizer.encode(echoed).ids) - len(tokenizer.encode(context).ids)
        if tokens > cap:
            break
        chosen = proposed
    echoed = _echo_current_user(context, chosen, close=close)
    tokens = len(tokenizer.encode(echoed).ids) - len(tokenizer.encode(context).ids)
    return chosen, tokens


def _echo_clamp(
    tokenizer,
    entries: list[dict],
    context: str,
    close: int,
    *,
    target_tokens: int,
) -> tuple[list[dict], int, int]:
    """Clamp comparator echo at a source Qwen-token boundary."""
    if target_tokens <= 0 or not entries:
        return [], 0, max(0, target_tokens)
    context_ids = list(tokenizer.encode(context).ids)
    chosen: list[dict] = []

    def measure(rows: list[dict]) -> int:
        echoed = _echo_current_user(context, rows, close=close)
        return len(tokenizer.encode(echoed).ids) - len(context_ids)

    for row in entries:
        whole = [*chosen, dict(row)]
        whole_tokens = measure(whole)
        if whole_tokens <= target_tokens:
            chosen = whole
            continue
        columns = list(row.get("pinned_columns", []))
        best_row = None
        best_tokens = measure(chosen)
        # BPE rendering can merge across the JSON framing boundary, so token
        # count is not guaranteed monotone in source-prefix length.  Exhausting
        # one candidate is bounded by the registered 128-token chunk size and
        # guarantees the token-exact boundary when one exists.
        for count in range(1, len(columns) + 1):
            partial = dict(row)
            partial_columns = columns[:count]
            partial["pinned_columns"] = partial_columns
            partial["span"] = [partial_columns[0], partial_columns[-1] + 1]
            partial["text"] = tokenizer.decode(
                context_ids[partial_columns[0] : partial_columns[-1] + 1]
            )
            tokens = measure([*chosen, partial])
            if tokens <= target_tokens and tokens >= best_tokens:
                best_row, best_tokens = partial, tokens
            if tokens == target_tokens:
                break
        if best_row is not None:
            chosen.append(best_row)
        return chosen, best_tokens, target_tokens - best_tokens
    tokens = measure(chosen)
    if tokens < target_tokens and chosen:
        last = dict(chosen[-1])
        pinned = list(last.get("pinned_columns", []))
        source = list(last.get("_echo_source_columns", pinned))
        context_ids = list(tokenizer.encode(context).ids)
        best_row = last
        best_tokens = tokens
        # Extend only the echoed text. The comparator's pinned-column dose is
        # unchanged, and the extension never passes the source resource end.
        for count in range(len(pinned) + 1, len(source) + 1):
            extended = dict(last)
            extended["text"] = tokenizer.decode(
                context_ids[source[0] : source[count - 1] + 1]
            )
            measured = measure([*chosen[:-1], extended])
            if measured <= target_tokens and measured >= best_tokens:
                best_row, best_tokens = extended, measured
            if measured == target_tokens:
                break
        chosen[-1] = best_row
        tokens = best_tokens
    return chosen, tokens, target_tokens - tokens


def _arm_event_fields(
    arm: str,
    *,
    evicted: bool,
    pinned_columns: int,
    pin_overflow: bool = False,
    pin_overflow_total: bool = False,
    dropped_columns: int = 0,
    control_role_shortfall: bool = False,
    role_column_deltas: dict[str, int] | None = None,
    pressure_triggered: bool | None = None,
) -> dict:
    """Record shared turn facts on every arm and arm-specific plan events."""
    treatment = arm == "clf_pinned_echo"
    control = arm == "clf_control"
    return {
        "pinned_columns": int(pinned_columns) if evicted else 0,
        "pin_overflow": bool(pin_overflow) if treatment else False,
        "pin_overflow_total": bool(pin_overflow_total),
        "pressure_triggered": (
            bool(evicted) if pressure_triggered is None else bool(pressure_triggered)
        ),
        "pin_overflow_dropped_columns": int(dropped_columns) if treatment else 0,
        "control_role_shortfall": bool(control_role_shortfall) if control else False,
        "role_column_deltas": (
            dict(role_column_deltas or {"user": 0, "tool": 0})
            if control
            else {"user": 0, "tool": 0}
        ),
    }


def _turn_plan(tokenizer, messages, tools, arm: str, scorer, seed: int) -> dict:
    context = render_prompt(messages, tools)
    current_index = max(
        index for index, row in enumerate(messages) if row["role"] == "user"
    )
    layout = context_layout(
        tokenizer, context, messages, current_message_index=current_index
    )
    empty = {
        "candidates": 0,
        "eligible": 0,
        "kept": 0,
        "budget": 0,
        "used": 0,
        "role_counts": {"user": 0, "tool": 0},
        "control_role_shortfall": {"user": 0, "tool": 0},
        "echo_dropped_control_tokens": 0,
    }
    suffix_columns = len(layout["context_token_ids"]) - layout["history_end"]
    empty["pin_overflow_total"] = layout["protected_prefix"][1] + suffix_columns > K
    empty["candidate_message_indices"] = []
    empty["current_user_message_index"] = current_index
    if arm in {"base", "full"}:
        return {
            "context": context,
            "echo_close": layout["current_user_close"],
            "evict_range": layout["evict_range"],
            "keep": [],
            "entries": [],
            "echo_ids": [],
            "selector": empty,
        }
    eligible, candidates, dropped = select_history_spans(
        tokenizer,
        context,
        messages,
        scorer,
        threshold=SELECTOR_THRESHOLD,
        chunk_tokens=CHUNK_TOKENS,
    )
    kept, classifier_pins, budget = budget_history_spans(
        eligible, layout["evict_range"], fraction=BUDGET_FRACTION
    )
    original_pin_columns = sum(len(row["pinned_columns"]) for row in kept)
    while True:
        classifier_entries, classifier_echo_tokens = _echo_cap(
            tokenizer, kept, context, layout["current_user_close"]
        )
        overflow = resolve_pin_overflow(
            kept,
            prefix_columns=layout["protected_prefix"][1],
            turn_columns=suffix_columns + classifier_echo_tokens,
            no_echo_turn_columns=suffix_columns,
            k=K,
        )
        if len(overflow["entries"]) == len(kept):
            break
        kept = overflow["entries"]
    overflow["dropped_columns"] = original_pin_columns - sum(
        len(row["pinned_columns"]) for row in kept
    )
    overflow["pin_overflow"] = (
        bool(overflow["dropped_columns"]) and not overflow["pin_overflow_total"]
    )
    classifier_pins = overflow["pins"]
    echo_context = _echo_current_user(
        context, classifier_entries, close=layout["current_user_close"]
    )
    echo_layout = context_layout(
        tokenizer,
        echo_context,
        messages,
        current_message_index=current_index,
    )
    if echo_layout["evict_range"] != layout["evict_range"]:
        raise AssertionError("echo changed prior-history eviction coordinates")
    control = build_matched_control(
        candidates,
        kept,
        echo_layout["evict_range"],
        tokenizer=tokenizer,
        context=context,
    )
    control_entries, control_echo_tokens, control_echo_residual = _echo_clamp(
        tokenizer,
        control["entries"],
        context,
        layout["current_user_close"],
        target_tokens=classifier_echo_tokens,
    )
    classifier_columns = sum(end - start for start, end in classifier_pins)
    treatment_roles = {
        role: sum(len(row["pinned_columns"]) for row in kept if row["role"] == role)
        for role in ("user", "tool")
    }
    role_pins = prior_user_spans(
        tokenizer,
        context,
        messages,
        current_index,
        layout["evict_range"],
    )
    if overflow["pin_overflow_total"]:
        role_pins = []
    recency = recency_pinned_plan(
        candidates,
        treatment_roles,
        layout["evict_range"],
        tokenizer=tokenizer,
        context=context,
    )
    recency_entries, recency_echo_tokens, recency_echo_residual = _echo_clamp(
        tokenizer,
        recency["entries"],
        context,
        layout["current_user_close"],
        target_tokens=classifier_echo_tokens,
    )
    tool_swap = tool_swap_plan(
        candidates,
        kept,
        layout["evict_range"],
        tokenizer=tokenizer,
        context=context,
    )
    swap_entries, swap_echo_tokens, swap_echo_residual = _echo_clamp(
        tokenizer,
        tool_swap["entries"],
        context,
        layout["current_user_close"],
        target_tokens=classifier_echo_tokens,
    )
    keep = {
        "clf_pinned": classifier_pins,
        "clf_pinned_echo": classifier_pins,
        "clf_control": control["pins"],
        "recency_pinned": recency["pins"],
        "tool_swap_echo": tool_swap["pins"],
        "role_pinned": role_pins,
    }[arm]
    entries = {
        "clf_pinned": [],
        "clf_pinned_echo": classifier_entries,
        "clf_control": control_entries,
        "recency_pinned": recency_entries,
        "tool_swap_echo": swap_entries,
        "role_pinned": [],
    }[arm]
    echo_tokens = {
        "clf_pinned": 0,
        "clf_pinned_echo": classifier_echo_tokens,
        "clf_control": control_echo_tokens,
        "recency_pinned": recency_echo_tokens,
        "tool_swap_echo": swap_echo_tokens,
        "role_pinned": 0,
    }[arm]
    arm_role_counts = {
        "clf_pinned": treatment_roles,
        "clf_pinned_echo": treatment_roles,
        "clf_control": {
            role: treatment_roles[role]
            + control.get("role_column_deltas", {}).get(role, 0)
            for role in ("user", "tool")
        },
        "recency_pinned": recency.get("role_counts", {"user": 0, "tool": 0}),
        "tool_swap_echo": {
            role: sum(
                len(row.get("pinned_columns", []))
                for row in tool_swap["entries"]
                if row["role"] == role
            )
            for role in ("user", "tool")
        },
        "role_pinned": {
            "user": sum(end - start for start, end in role_pins),
            "tool": 0,
        },
    }[arm]
    rendered = render_echo(entries)
    match_impossible = {
        "clf_control": control.get("match_impossible", False),
        "recency_pinned": recency.get("match_impossible", False),
        "tool_swap_echo": tool_swap.get("match_impossible", False),
    }.get(arm, False)
    echo_delta = (
        echo_tokens - classifier_echo_tokens
        if arm in {"clf_control", "recency_pinned", "tool_swap_echo"}
        else 0
    )
    pressure_triggered = layout["history_end"] > K
    if pressure_triggered and not match_impossible and abs(echo_delta) > 16:
        raise AssertionError(f"{arm} echo token delta exceeds 16: {echo_delta}")
    if (
        pressure_triggered
        and arm in {"clf_control", "recency_pinned", "tool_swap_echo"}
        and not match_impossible
    ):
        exact_roles = arm_role_counts == treatment_roles
        exact_total = sum(arm_role_counts.values()) == sum(treatment_roles.values())
        usable_columns = exact_total if arm == "clf_control" and control.get(
            "control_role_shortfall", False
        ) else exact_roles
        if not usable_columns:
            raise AssertionError(f"{arm} comparator column mismatch")
    return {
        "context": context,
        "echo_close": layout["current_user_close"],
        "evict_range": layout["evict_range"],
        "keep": keep,
        "entries": entries,
        "echo_ids": tokenizer.encode(rendered).ids if rendered else [],
        "selector": {
            "candidates": len(candidates),
            "eligible": len(eligible),
            "kept": len(kept),
            "budget": budget,
            "used": classifier_columns,
            "nominal_b": budget,
            "actual_b": classifier_columns,
            "candidate_spans_by_role": {
                role: [row["span"] for row in candidates if row["role"] == role]
                for role in ("user", "tool")
            },
            "eligible_spans_by_role": {
                role: [row["span"] for row in eligible if row["role"] == role]
                for role in ("user", "tool")
            },
            "selected_spans_by_role": {
                role: [row["span"] for row in kept if row["role"] == role]
                for role in ("user", "tool")
            },
            "capacity_rejections": max(0, len(eligible) - len(kept)),
            "fallback_count": int(control.get("control_role_shortfall", False)),
            "treatment_role_counts": treatment_roles,
            "control_role_counts": control["role_counts"],
            "pinned_columns_by_role": arm_role_counts,
            "control_role_shortfall": control["role_shortfall"],
            "control_role_shortfall_event": control.get(
                "control_role_shortfall", False
            ),
            "role_column_deltas": control.get(
                "role_column_deltas", {"user": 0, "tool": 0}
            ),
            "match_impossible": match_impossible,
            "echo_dropped_control_tokens": dropped,
            "scorer_truncated_candidates": max(
                (int(row.get("scorer_truncated_candidates", 0)) for row in candidates),
                default=0,
            ),
            "echo_tokens": echo_tokens,
            "echo_token_delta": echo_delta,
            "echo_clamp_residual": {
                "clf_control": control_echo_residual,
                "recency_pinned": recency_echo_residual,
                "tool_swap_echo": swap_echo_residual,
            }.get(arm, 0),
            "echo_entry_count_delta": (
                len(entries) - len(classifier_entries)
                if arm in {"clf_control", "recency_pinned", "tool_swap_echo"}
                else 0
            ),
            "match_deltas": {
                "clf_control": control.get("matches", []),
                "tool_swap_echo": tool_swap.get("matches", []),
            }.get(arm, []),
            "pin_overflow": overflow["pin_overflow"],
            "pin_overflow_total": overflow["pin_overflow_total"],
            "pin_overflow_dropped_columns": overflow["dropped_columns"],
            "spans": kept,
            "candidate_message_indices": [
                int(row["message_index"]) for row in candidates
            ],
            "current_user_message_index": current_index,
        },
    }


def _degenerate(ids: list[int], truncated: bool) -> bool:
    if truncated:
        return False
    if len(ids) < 8:
        return False
    grams = [tuple(ids[index : index + 4]) for index in range(len(ids) - 3)]
    return 1.0 - len(set(grams)) / len(grams) > 0.5


def run_case_arm(
    model,
    tokenizer,
    scorer,
    category: str,
    raw_case: dict,
    ground_truth: list,
    args,
    run_tag: str,
    arm: str,
    verified_docs: dict | None = None,
):
    case = prepare_case(raw_case, DATA / "function_docs", verified_docs)
    tools = case["function"]
    holdouts = case.get("missed_function", {})
    messages = []
    decoded_turns = []
    turns = []
    any_eviction = False
    copied_echo = False
    total_echo_added = 0
    selector_turns = []
    context_ids_by_turn = []
    history_call_raw: set[str] = set()
    repeated_history_calls = 0
    arm_started = time.monotonic()
    for turn_index, original_messages in enumerate(case["question"]):
        if args.mode == "teacher":
            turn_case = prepare_case(raw_case, DATA / "function_docs", verified_docs)
            teacher_run = f"teacher_{run_tag}_{arm}_{turn_index}"
            messages = build_teacher_history(
                turn_case, ground_truth, turn_index, teacher_run
            )
            tools = turn_case["function"]
            turn_holdouts = turn_case.get("missed_function", {})
            if str(turn_index) in turn_holdouts:
                tools.extend(turn_holdouts[str(turn_index)])
                current_messages = [{"role": "user", "content": ADDED_FUNCTION_PROMPT}]
            else:
                current_messages = turn_case["question"][turn_index]
            active_case = turn_case
        elif str(turn_index) in holdouts:
            tools.extend(holdouts[str(turn_index)])
            current_messages = [{"role": "user", "content": ADDED_FUNCTION_PROMPT}]
            active_case = case
        else:
            current_messages = original_messages
            active_case = case
        messages.extend(current_messages)
        responses = []
        turn_calls = []
        decoded_steps = []
        turn_started = time.monotonic()
        turn_timeout = False
        turn_truncated = False
        turn_degenerate = False
        turn_position_overflow = False
        turn_overflow_phase = None
        turn_na = False
        turn_repeated_call = False
        plan = _turn_plan(
            tokenizer,
            messages,
            tools,
            arm,
            scorer,
            seed=COHORT_SEED + turn_index * 101,
        )
        canonical_history = canonical_repeated_call_set(
            ground_truth[:turn_index], tools, plan["entries"]
        )
        if args.mode == "teacher":
            history_call_raw = canonical_history
        else:
            history_call_raw.update(canonical_history)
        context_ids_by_turn.append(
            list(tokenizer.encode(render_prompt(messages, tools)).ids)
        )
        selector_turns.append(plan["selector"])
        first_eviction = None
        cache = None
        continuation_ids = None
        for _step in range(MAX_STEPS):
            remaining = max(1e-6, args.deadline - (time.monotonic() - turn_started))
            base_context = plan["context"]
            context = _echo_current_user(
                base_context, plan["entries"], close=plan["echo_close"]
            )
            echo_added = len(tokenizer.encode(context).ids) - len(
                tokenizer.encode(base_context).ids
            )
            context_ids = tokenizer.encode(context).ids
            if cache is None:
                if turn_index >= 1 and arm != "full" and plan["evict_range"][1] > K:
                    positions = (
                        plan["evict_range"][0]
                        + sum(end - start for start, end in plan["keep"])
                        + len(context_ids)
                        - plan["evict_range"][1]
                    )
                else:
                    positions = len(context_ids)
            else:
                positions = int(cache.k[0].shape[2]) + len(continuation_ids or [])
            pre_generation_phase = "initial_prompt" if cache is None else "tool_step"
            position_action = position_overflow_result(
                arm, positions, phase=pre_generation_phase
            )
            if position_action["position_overflow"]:
                overflow_phase = position_action["overflow_phase"]
                result = {
                    "text": "",
                    "token_ids": [],
                    "truncated": position_action["truncated"],
                    "timeout": False,
                    "evicted": False,
                    "prompt_tokens": positions,
                    "columns_before": positions,
                    "columns_after": positions,
                    "pinned_columns": 0,
                    "evictable_size": plan["evict_range"][1] - plan["evict_range"][0],
                    "pin_overflow": 0,
                    "columns_after_step": positions,
                    "position_overflow": True,
                    "overflow_phase": overflow_phase,
                    "na": position_action["na"],
                }
                turn_position_overflow = True
                turn_overflow_phase = overflow_phase
                turn_na = bool(position_action["na"])
            else:
                result = generate(
                    model,
                    tokenizer,
                    context,
                    evict_range=plan["evict_range"],
                    keep=plan["keep"],
                    allow_eviction=turn_index >= 1 and arm != "full",
                    max_new=args.max_new,
                    deadline=remaining,
                    cache=cache,
                    continuation_ids=continuation_ids,
                )
                cache = result.pop("_cache")
                turn_position_overflow |= result["position_overflow"]
                if result["position_overflow"]:
                    turn_overflow_phase = result.get(
                        "overflow_phase", "within_generation"
                    )
            if first_eviction is None:
                event_fields = _arm_event_fields(
                    arm,
                    evicted=bool(result["evicted"]),
                    pinned_columns=int(result["pinned_columns"]),
                    pin_overflow=bool(plan["selector"].get("pin_overflow", False)),
                    pin_overflow_total=bool(
                        plan["selector"].get("pin_overflow_total", False)
                    ),
                    dropped_columns=int(
                        plan["selector"].get("pin_overflow_dropped_columns", 0)
                    ),
                    control_role_shortfall=bool(
                        plan["selector"].get("control_role_shortfall_event", False)
                    ),
                    role_column_deltas=plan["selector"].get(
                        "role_column_deltas", {"user": 0, "tool": 0}
                    ),
                    pressure_triggered=(
                        turn_index >= 1 and plan["evict_range"][1] > K
                    ),
                )
                first_eviction = {
                    "evicted": result["evicted"],
                    "columns_before": result["columns_before"],
                    "columns_after": result["columns_after"],
                    **event_fields,
                    "evictable_size": result["evictable_size"],
                    "budget_used": plan["selector"]["used"],
                    "echo_tokens": plan["selector"].get("echo_tokens", 0),
                    "match_impossible": plan["selector"].get("match_impossible", False),
                    "echo_token_delta": plan["selector"].get("echo_token_delta", 0),
                    "echo_clamp_residual": plan["selector"].get(
                        "echo_clamp_residual", 0
                    ),
                    "echo_entry_count_delta": plan["selector"].get(
                        "echo_entry_count_delta", 0
                    ),
                    "match_deltas": plan["selector"].get("match_deltas", []),
                    "pinned_columns_by_role": plan["selector"].get(
                        "pinned_columns_by_role", {"user": 0, "tool": 0}
                    ),
                    "protected_prefix_columns": plan["evict_range"][0],
                    "current_turn_prefilled_before_eviction": result.get(
                        "current_turn_prefilled_before_eviction", False
                    ),
                    "protected_prefix_survived": result.get(
                        "protected_prefix_survived", True
                    ),
                }
            any_eviction |= result["evicted"]
            if _step == 0:
                total_echo_added += echo_added
            copied_echo |= echo_copy_flag(result["token_ids"], plan["echo_ids"])
            responses.append(result)
            turn_timeout |= result["timeout"]
            turn_truncated |= result["truncated"]
            turn_degenerate |= _degenerate(result["token_ids"], result["truncated"])
            if turn_position_overflow:
                break
            messages.append({"role": "assistant", "content": result["text"]})
            parsed = parse_tool_calls(result["text"])
            executable = []
            call_records = []
            for item in parsed:
                record = asdict(item)
                try:
                    if item.valid:
                        canonical_call(item.call)
                except ValueError as exc:
                    record["valid"] = False
                    record["error"] = str(exc)
                current_ground_truth = {
                    canonical_call(_call_string_to_json(call, tools))
                    for call in ground_truth[turn_index]
                }
                if record["valid"] and repeated_call_event(
                    item.call, history_call_raw, current_ground_truth
                ):
                    repeated_history_calls += 1
                    turn_repeated_call = True
                if record["valid"]:
                    try:
                        record["python"] = call_to_python(item.call)
                        executable.append(record["python"])
                    except ValueError as exc:
                        record["valid"] = False
                        record["error"] = str(exc)
                call_records.append(record)
            turn_calls.extend(call_records)
            decoded_steps.append(executable)
            if not executable or result["timeout"] or result["truncated"]:
                break
            execution, _ = execute_call_strings(
                executable,
                active_case,
                teacher_run if args.mode == "teacher" else f"stencil_{run_tag}_{arm}",
            )
            for record, output in zip(
                [record for record in call_records if record["valid"]],
                execution,
                strict=True,
            ):
                record["execution"] = output
                messages.append({"role": "tool", "content": output})
            continuation_ids = _tool_step_suffix(tokenizer, execution)
        history_call_raw.update(
            canonical_call(call["call"])
            for call in turn_calls
            if call.get("valid") and call.get("call")
        )
        if args.mode == "teacher":
            decoded_for_score = [
                [list(calls)] for calls in ground_truth[:turn_index]
            ] + [decoded_steps]
        else:
            decoded_turns.append(decoded_steps)
            decoded_for_score = decoded_turns
        turn_score = (
            {"valid": False, "error_type": "stencil:position_overflow"}
            if turn_position_overflow
            else score_case(
                active_case,
                decoded_for_score,
                ground_truth[: turn_index + 1],
                run_name=f"score_{run_tag}_{arm}_turn_{turn_index}",
            )
        )
        turns.append(
            {
                "turn": turn_index,
                "responses": responses,
                "tool_calls": turn_calls,
                "timeout": turn_timeout,
                "truncated": turn_truncated,
                "degenerate": turn_degenerate,
                "pass": (
                    None if turn_score["valid"] is None else bool(turn_score["valid"])
                ),
                "score": turn_score,
                "eviction": first_eviction,
                "prompt_positions": responses[0]["prompt_tokens"] if responses else 0,
                "position_overflow": turn_position_overflow,
                "overflow_phase": turn_overflow_phase,
                "na": turn_na,
                "repeated_call": turn_repeated_call,
                "chat_control_echo": any(
                    marker in render_echo(plan["entries"])
                    for marker in (
                        "<|im_",
                        "<tool_call",
                        "</tool_call",
                        "<tool_response",
                        "</tool_response",
                    )
                ),
            }
        )
        if turn_timeout and args.mode == "free":
            break
    if args.mode == "teacher":
        final_score = {
            "valid": all(turn["pass"] for turn in turns if turn["pass"] is not None)
        }
    elif len(decoded_turns) == len(ground_truth):
        final_score = score_case(
            case,
            decoded_turns,
            ground_truth,
            run_name=f"score_{run_tag}_{arm}_final",
        )
    else:
        final_score = {"valid": False, "error_type": "stencil:incomplete_timeout"}
    return {
        "case_id": case["id"],
        "category": category,
        "turns": turns,
        "evicted": any_eviction,
        "echo_tokens_added": total_echo_added,
        "echo_copy": copied_echo,
        "selector": {
            "candidates": sum(row["candidates"] for row in selector_turns),
            "eligible": sum(row.get("eligible", 0) for row in selector_turns),
            "kept": sum(row["kept"] for row in selector_turns),
            "budget": sum(row["budget"] for row in selector_turns),
            "used": sum(row["used"] for row in selector_turns),
            "turns": selector_turns,
        },
        "seconds": time.monotonic() - arm_started,
        "final_pass": bool(final_score["valid"]),
        "final_score": final_score,
        "repeated_history_calls": repeated_history_calls,
        "position_overflow": any(turn["position_overflow"] for turn in turns),
        "_context_ids": context_ids_by_turn,
    }


def run_case(
    model,
    tokenizer,
    scorer,
    category,
    raw_case,
    ground_truth,
    args,
    run_tag,
    run_identity_sha256: str | None = None,
    verified_docs: dict | None = None,
):
    started = time.monotonic()
    selected_arms = (
        REDUCED_ARMS
        if args.mode == "teacher" and args.arm_cut
        else ARMS
        if args.mode == "teacher"
        else ("base", "clf_pinned_echo")
    )
    arms = {
        arm: run_case_arm(
            model,
            tokenizer,
            scorer,
            category,
            raw_case,
            ground_truth,
            args,
            run_tag,
            arm,
            verified_docs,
        )
        for arm in selected_arms
    }
    context_ids = {arm: arms[arm].pop("_context_ids") for arm in selected_arms}
    if args.mode == "teacher":
        for turn_index in range(len(ground_truth)):
            rows = [context_ids[arm][turn_index] for arm in selected_arms]
            if any(row != rows[0] for row in rows[1:]):
                raise AssertionError(
                    f"teacher-forced context ids differ at turn {turn_index}"
                )
    turn_facts = []
    if args.mode == "teacher":
        for turn_index in range(len(ground_truth)):
            arm_facts = [
                next(
                    turn
                    for turn in arms[arm]["turns"]
                    if int(turn["turn"]) == turn_index
                )["eviction"]
                for arm in selected_arms
            ]
            pressure = {bool(row.get("pressure_triggered")) for row in arm_facts}
            overflow_total = {bool(row.get("pin_overflow_total")) for row in arm_facts}
            if len(pressure) != 1 or len(overflow_total) != 1:
                raise AssertionError(
                    f"arm-independent turn facts differ at turn {turn_index}"
                )
            turn_facts.append(
                {
                    "turn": turn_index,
                    "pressure_triggered": pressure.pop(),
                    "pin_overflow_total": overflow_total.pop(),
                }
            )
    first_divergence = None
    if args.mode == "free":
        left = response_ids(arms["base"])
        right = response_ids(arms["clf_pinned_echo"])
        first_divergence = next(
            (
                index
                for index, pair in enumerate(zip(left, right, strict=False))
                if pair[0] != pair[1]
            ),
            None,
        )
        if first_divergence is None and len(left) != len(right):
            first_divergence = min(len(left), len(right))
    record = {
        "schema": 6,
        "mode": args.mode,
        "case_id": raw_case["id"],
        "category": category,
        "arms": arms,
        "seconds": time.monotonic() - started,
        "first_divergence_turn": first_divergence,
        "run_identity_sha256": run_identity_sha256,
        "turn_facts": turn_facts,
    }
    if args.mode == "teacher":
        assert_case_record_schema(record)
    return record


def artifact_meta(
    args,
    *,
    verified_inputs: dict | None = None,
    verified_runtime: dict | None = None,
) -> dict:
    provenance = (
        assert_clean_git_for_sealed() if args.split == "sealed" else git_provenance()
    )
    _, registration_hash = registration_text_and_hash()
    classifier = assert_registered_classifier()
    model_dir = ROOT / f"models/qwen3-{args.trunk}-hf"
    code_manifest = harness_manifest()
    pins_manifest = ROOT / "data/bench/pins-manifest.json"
    with pins_manifest.open("rb") as handle:
        pins_raw = handle.read()
    pins = json.loads(pins_raw)["pins"][
        "ShishirPatil/gorilla BFCL V3 multi-turn"
    ]
    if verified_inputs is None:
        _, loaded = _load_cases_verified(args.split, getattr(args, "limit", None))
    else:
        loaded = verified_inputs

    if verified_runtime is None:
        _, runtime = _load_verified_runtime_inputs(pins)
    else:
        runtime = verified_runtime
    function_docs = runtime["function_docs"]
    checker_files = runtime["checker"]
    cohorts_path = DATA / "cohorts.json"
    cohorts_digest = sha256(cohorts_path)
    cohorts_relative = str(cohorts_path.relative_to(ROOT))
    if cohorts_digest != pins["files_sha256"].get(cohorts_relative):
        raise RuntimeError("frozen input hash mismatch: cohorts.json")
    template_digest = hashlib.sha256(
        inspect.getsource(render_prompt).encode()
    ).hexdigest()
    verified_bytes = {
        **loaded,
        "cohorts": cohorts_digest,
        "function_docs": function_docs,
        "checker": checker_files,
        "template": template_digest,
    }
    actual_bfcl_files = {
        cohorts_relative: cohorts_digest,
        **function_docs,
        **checker_files,
    }
    if args.split == "sealed":
        actual_bfcl_files.update(loaded["source_files"])
    frozen_hashes = {
        "harness": code_manifest["sha256"],
        "harness_manifest": code_manifest["sha256"],
        "harness_files": code_manifest["files"],
        "selector_artifact": hashlib.sha256(
            json.dumps(classifier, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        "trunk_weights": sha256(ROOT / f"models/qwen3-{args.trunk}.pt"),
        "trunk_tokenizer": sha256(model_dir / "tokenizer.json"),
        "trunk_config": sha256(model_dir / "config.json"),
        "cohorts": cohorts_digest,
        "offsets": loaded["offsets"],
        "pins_manifest": hashlib.sha256(pins_raw).hexdigest(),
        "bfcl_files": actual_bfcl_files,
        "chat_template": template_digest,
        "vendored_checker": _canonical_sha256(checker_files),
        "verified_bytes": verified_bytes,
    }
    return {
        "schema": 5,
        "split": args.split,
        "mode": args.mode,
        "arms": list(
            REDUCED_ARMS
            if args.mode == "teacher" and getattr(args, "arm_cut", False)
            else ARMS
            if args.mode == "teacher"
            else ("base", "clf_pinned_echo")
        ),
        "cost_arm_cut": bool(getattr(args, "arm_cut", False)),
        "limit": getattr(args, "limit", None),
        "trunk": args.trunk,
        "max_new": args.max_new,
        "deadline": args.deadline,
        "k": K,
        "budget_fraction": BUDGET_FRACTION,
        "chunk_tokens": CHUNK_TOKENS,
        "echo_cap": ECHO_CAP,
        "selector_threshold": SELECTOR_THRESHOLD,
        "echo_header": ECHO_HEADER,
        "control_tie_break": CONTROL_TIE_BREAK,
        "git": provenance,
        "registration_sha256": registration_hash,
        "selector_roles": ["user", "tool"],
        "selector_context": "empty",
        "eviction_timing": "pre-query",
        "protected_prefix": "system_plus_tools_and_at_least_four_sink_columns",
        "greedy": True,
        "thinking": False,
        "frozen_hashes": frozen_hashes,
        "classifier_sha256": classifier,
    }


def bind_run_identity(meta: dict, certificate_sha256: str | None = None) -> dict:
    bound = dict(meta)
    bound["preflight_certificate_sha256"] = certificate_sha256
    bound["run_identity_sha256"] = _canonical_sha256(bound)
    return bound


def assert_registered_classifier() -> dict[str, str]:
    manifest = ROOT / "results/quick-checks/ft_final2_s0_sha256.txt"
    expected = {}
    for line in manifest.read_text().splitlines():
        if not line.strip():
            continue
        digest, relative = line.split(maxsplit=1)
        path = ROOT / relative
        if not path.is_file() or sha256(path) != digest:
            raise RuntimeError(f"registered classifier sha256 mismatch: {relative}")
        expected[relative] = digest
    if not expected or not all(
        relative.startswith("data/classifier/model/ft/") for relative in expected
    ):
        raise RuntimeError("registered classifier manifest is empty or out of scope")
    return expected


def _check_or_write_meta(path: Path, meta: dict) -> None:
    if path.exists():
        if json.loads(path.read_text()) != meta:
            raise RuntimeError("registered constants or provenance differ from meta")
    else:
        atomic_json(path, meta)


def run(
    args,
    model,
    tokenizer,
    scorer,
    *,
    resume: bool = True,
    run_tag: str = "main",
    meta: dict | None = None,
    cases: list[tuple[str, dict, list]] | None = None,
    verified_docs: dict | None = None,
) -> list[dict]:
    output = Path(args.out)
    if not output.is_absolute():
        output = ROOT / "results/qwen" / output
    records_dir = output / "records"
    records_dir.mkdir(parents=True, exist_ok=True)
    if cases is None:
        cases, verified_inputs = _load_cases_verified(args.split, args.limit)
    else:
        verified_inputs = None
    if meta is None:
        meta = bind_run_identity(
            artifact_meta(args, verified_inputs=verified_inputs)
        )
    _check_or_write_meta(output / "meta.json", meta)
    run_identity = str(meta["run_identity_sha256"])
    records = []
    cohort_ids = [str(case["id"]) for _, case, _ in cases]
    expected_files = {f"{case_id}.json" for case_id in cohort_ids}
    extra_files = {path.name for path in records_dir.glob("*.json")} - expected_files
    if extra_files:
        raise RuntimeError(
            f"unexpected record files outside active cohort: {sorted(extra_files)}"
        )
    for index, (category, case, answer) in enumerate(cases):
        path = records_dir / f"{case['id']}.json"
        if resume and path.exists():
            record = json.loads(path.read_text())
            if args.mode == "teacher":
                assert_case_record_schema(
                    record,
                    expected_arms=meta["arms"],
                    run_identity_sha256=run_identity,
                )
            elif record.get("run_identity_sha256") != run_identity or list(
                record.get("arms", {})
            ) != list(meta["arms"]):
                raise RuntimeError("resume run identity or arms mismatch")
            if record["case_id"] != case["id"] or record["category"] != category:
                raise RuntimeError(f"resume identity mismatch: {case['id']}")
        else:
            record = run_case(
                model,
                tokenizer,
                scorer,
                category,
                case,
                answer,
                args,
                f"{run_tag}_{index}",
                run_identity,
                verified_docs,
            )
            atomic_json(path, record)
        records.append(record)
        passes = " ".join(
            f"{arm}={int(row['final_pass'])}" for arm, row in record["arms"].items()
        )
        print(
            f"{index + 1}: {case['id']} {passes} seconds={record['seconds']:.1f}",
            flush=True,
        )
    all_records = [
        json.loads((records_dir / f"{case_id}.json").read_text())
        for case_id in cohort_ids
    ]
    if args.mode != "teacher" and any(
        record.get("run_identity_sha256") != run_identity
        or list(record.get("arms", {})) != list(meta["arms"])
        for record in all_records
    ):
        raise RuntimeError("summary record run identity or arms mismatch")
    summary = (
        summarize_records(
            all_records,
            expected_case_ids=cohort_ids,
            run_identity_sha256=run_identity,
            expected_arms=meta["arms"],
        )
        if args.mode == "teacher"
        else {
            "schema": 3,
            "mode": "free",
            "cases": len(all_records),
            "arms": {
                arm: _free_arm_summary(all_records, arm)
                for arm in ("base", "clf_pinned_echo")
            },
            "first_divergence_turns": {
                row["case_id"]: row.get("first_divergence_turn") for row in all_records
            },
        }
    )
    atomic_json(output / "summary.json", summary)
    return records


def _free_arm_summary(records: list[dict], arm: str) -> dict:
    passed = sum(bool(row["arms"][arm]["final_pass"]) for row in records)
    return {
        "passed": passed,
        "n": len(records),
        "rate": passed / len(records) if records else None,
    }


def response_ids(arm_record: dict) -> list[list[list[int]]]:
    return [
        [response["token_ids"] for response in turn["responses"]]
        for turn in arm_record["turns"]
    ]


def determinism_trace(arm_record: dict) -> list[dict]:
    """Registered generated-id, call, output, and checker trace."""
    return [
        {
            "response_ids": [row["token_ids"] for row in turn["responses"]],
            "calls": [row.get("python") for row in turn["tool_calls"]],
            "outputs": [row.get("execution") for row in turn["tool_calls"]],
            "score": turn["score"],
        }
        for turn in arm_record["turns"]
    ]


def assert_dev_invariants(records: list[dict]) -> dict:
    """Assert registration-v7 invariants for every generated dev arm/turn."""
    families = {
        name: {"passed": 0, "n": 0}
        for name in (
            "protected_prefix",
            "current_turn_absent",
            "cache_equation",
            "candidate_source",
            "comparator_columns",
            "comparator_echo",
        )
    }

    def check(name: str, condition: bool) -> None:
        families[name]["n"] += 1
        families[name]["passed"] += bool(condition)
        if not condition:
            raise AssertionError(f"dev invariant failed: {name}")

    shortfalls = overflows = drops = 0
    match_deltas = {"clf_control": [], "tool_swap_echo": []}
    comparator_arms = ("clf_control", "recency_pinned", "tool_swap_echo")
    match_impossible = {arm: 0 for arm in comparator_arms}
    shortfall_counts = {arm: 0 for arm in comparator_arms}
    delta_counts = {arm: 0 for arm in comparator_arms}
    echo_clamp_residual_counts = {arm: 0 for arm in comparator_arms}
    echo_entry_count_deltas = {arm: [] for arm in comparator_arms}
    for record in records:
        treatment_turns = record["arms"]["clf_pinned_echo"]["turns"]
        for turn_offset, treatment_turn in enumerate(treatment_turns):
            treatment = treatment_turn["eviction"]
            for arm, arm_row in record["arms"].items():
                turn = arm_row["turns"][turn_offset]
                eviction = turn["eviction"]
                if eviction["evicted"]:
                    check(
                        "current_turn_absent",
                        eviction["current_turn_prefilled_before_eviction"] is False,
                    )
                    check(
                        "protected_prefix",
                        eviction["protected_prefix_survived"] is True,
                    )
                    check(
                        "cache_equation",
                        eviction["columns_before"]
                        - eviction["evictable_size"]
                        + eviction["pinned_columns"]
                        == eviction["columns_after"],
                    )
                selector = arm_row.get("selector", {}).get("turns", [])[turn_offset]
                current_user = int(selector["current_user_message_index"])
                for message_index in selector["candidate_message_indices"]:
                    check("candidate_source", int(message_index) < current_user)
                pressure_triggered = bool(treatment.get("pressure_triggered"))
                if pressure_triggered and arm in {
                    "recency_pinned",
                    "tool_swap_echo",
                }:
                    check(
                        "comparator_columns",
                        eviction["pinned_columns_by_role"]
                        == treatment["pinned_columns_by_role"]
                        or eviction["match_impossible"],
                    )
                    check(
                        "comparator_echo",
                        abs(eviction["echo_token_delta"]) <= 16
                        or eviction["match_impossible"],
                    )
                if pressure_triggered and arm == "clf_control":
                    if eviction["control_role_shortfall"]:
                        check(
                            "comparator_columns",
                            sum(eviction["pinned_columns_by_role"].values())
                            == sum(treatment["pinned_columns_by_role"].values())
                            or eviction["match_impossible"],
                        )
                    else:
                        check(
                            "comparator_columns",
                            eviction["pinned_columns_by_role"]
                            == treatment["pinned_columns_by_role"]
                            or eviction["match_impossible"],
                        )
                    check(
                        "comparator_echo",
                        abs(eviction["echo_token_delta"]) <= 16
                        or eviction["match_impossible"],
                    )
                shortfalls += bool(eviction.get("control_role_shortfall"))
                overflows += bool(eviction.get("pin_overflow"))
                drops += int(eviction.get("pin_overflow_dropped_columns", 0))
                if arm in match_deltas:
                    match_deltas[arm].extend(eviction.get("match_deltas", []))
                if arm in comparator_arms and bool(eviction.get("pressure_triggered")):
                    match_impossible[arm] += bool(eviction.get("match_impossible"))
                    shortfall_counts[arm] += bool(
                        eviction.get("control_role_shortfall")
                    )
                    delta_counts[arm] += int(eviction.get("echo_token_delta", 0)) != 0
                    echo_clamp_residual_counts[arm] += int(
                        eviction.get("echo_clamp_residual", 0)
                    ) != 0
                    echo_entry_count_deltas[arm].append(
                        int(eviction.get("echo_entry_count_delta", 0))
                    )
    passed = sum(row["passed"] for row in families.values())
    checked = sum(row["n"] for row in families.values())
    return {
        "checked": checked,
        "passed_fraction": passed / checked if checked else None,
        "families": families,
        "control_role_shortfall": shortfalls,
        "pin_overflow": overflows,
        "dropped_columns": drops,
        "match_deltas": match_deltas,
        "match_impossible": match_impossible,
        "shortfall_counts": shortfall_counts,
        "delta_counts": delta_counts,
        "echo_clamp_residual_counts": echo_clamp_residual_counts,
        "echo_entry_count_deltas": echo_entry_count_deltas,
    }


def preflight(
    args, model, tokenizer, scorer, *, cases=None, verified_docs=None
) -> None:
    output = Path(args.out)
    if not output.is_absolute():
        output = ROOT / "results/qwen" / output
    first = run(
        args,
        model,
        tokenizer,
        scorer,
        resume=True,
        run_tag="preflight_a",
        cases=cases,
        verified_docs=verified_docs,
    )
    try:
        invariants = assert_dev_invariants(first)
    except AssertionError as exc:
        failure = {
            "schema": 5,
            "status": "INCONCLUSIVE",
            "failure_state": "INVARIANT_FAILURE",
            "error": str(exc),
        }
        atomic_json(output / "preflight.json", failure)
        raise RuntimeError("registered preflight invariant failed") from exc
    invariants["passed"] = all(
        row["passed"] == row["n"] for row in invariants["families"].values()
    )
    if invariants["match_impossible"]["clf_control"]:
        failure = {
            "schema": 5,
            "status": "INCONCLUSIVE",
            "failure_state": "INVARIANT_FAILURE",
            "error": "dev clf_control matching is impossible",
            "invariants": invariants,
        }
        atomic_json(output / "preflight.json", failure)
        raise RuntimeError(failure["error"])
    excessive_echo = [
        (record["case_id"], arm, turn["turn"], turn["eviction"]["echo_token_delta"])
        for record in first
        for arm in ("clf_control", "recency_pinned", "tool_swap_echo")
        for turn in record["arms"][arm]["turns"]
        if abs(int(turn["eviction"].get("echo_token_delta", 0))) > 16
        and not turn["eviction"].get("match_impossible")
    ]
    if excessive_echo:
        failure = {
            "schema": 5,
            "status": "INCONCLUSIVE",
            "failure_state": "INVARIANT_FAILURE",
            "error": f"dev comparator echo token delta exceeds 16: {excessive_echo}",
        }
        atomic_json(output / "preflight.json", failure)
        raise RuntimeError(failure["error"])
    dev_cases = cases if cases is not None else load_cases("dev")
    determinism_cases = [
        next(row for row in dev_cases if row[0] == category) for category in CATEGORIES
    ]
    second = [
        run_case_arm(
            model,
            tokenizer,
            scorer,
            category,
            case,
            answer,
            args,
            f"preflight_b_{index}",
            "base",
            verified_docs,
        )
        for index, (category, case, answer) in enumerate(determinism_cases)
    ]
    deterministic = all(
        determinism_trace(
            next(row for row in first if row["case_id"] == right["case_id"])["arms"][
                "base"
            ]
        )
        == determinism_trace(right)
        for right in second
    )
    base_rows = [record["arms"]["base"] for record in first]
    full_rows = [record["arms"]["full"] for record in first]
    selectors = [record["arms"]["clf_pinned"]["selector"] for record in first]
    candidates = sum(row["candidates"] for row in selectors)
    kept = sum(row["kept"] for row in selectors)
    budget = sum(row["budget"] for row in selectors)
    used = sum(row["used"] for row in selectors)
    seconds = sum(
        float(record["arms"][arm]["seconds"]) for record in first for arm in ARMS
    )
    reduced_seconds = sum(
        float(record["arms"][arm]["seconds"])
        for record in first
        for arm in REDUCED_ARMS
    )
    base_passed = sum(row["final_pass"] for row in base_rows)
    full_passed = sum(row["final_pass"] for row in full_rows)
    long_turns = [
        turn
        for record in first
        if record["category"] == "long_context"
        for turn in record["arms"]["base"]["turns"]
    ]
    long_turn_rate = sum(bool(turn["pass"]) for turn in long_turns) / len(long_turns)
    long_records = [record for record in first if record["category"] == "long_context"]
    full_long_passed = sum(
        record["arms"]["full"]["final_pass"] for record in long_records
    )
    full_long_turns = [
        turn
        for record in long_records
        for turn in record["arms"]["full"]["turns"]
        if not bool(turn.get("na"))
    ]
    full_long_turn_passed = sum(bool(turn["pass"]) for turn in full_long_turns)
    exposed_records = [
        record
        for record in first
        if record["category"] == "long_context" and record["arms"]["base"]["evicted"]
    ]
    exposed_tool_turns = sum(
        any(span.get("role") == "tool" for span in selector_turn.get("spans", []))
        and bool(base_turn["eviction"]["evicted"])
        for record in exposed_records
        for selector_turn, base_turn in zip(
            record["arms"]["clf_pinned_echo"]["selector"]["turns"],
            record["arms"]["base"]["turns"],
            strict=True,
        )
    )
    competence_ok = (
        full_passed >= 5
        and full_long_passed >= 2
        and full_long_turn_passed >= 6
        and base_passed >= 5
        and sum(bool(turn["pass"]) for turn in long_turns) >= 6
    )
    projected_hours = seconds / len(first) * 64 / 3600
    reduced_projected_hours = reduced_seconds / len(first) * 64 / 3600
    report = {
        "competence": {
            "full_overall": {"passed": full_passed, "n": 32, "floor": "5/32"},
            "full_long_cases": {"passed": full_long_passed, "n": 8, "floor": "2/8"},
            "full_long_turns": {
                "passed": full_long_turn_passed,
                "n": len(full_long_turns),
                "floor": "at least 6 passing eligible turns",
            },
            "base_overall": {"passed": base_passed, "n": 32, "floor": "5/32"},
            "base_long_turns": {
                "passed": sum(bool(turn["pass"]) for turn in long_turns),
                "n": 40,
                "floor": "6/40",
            },
            "passed_all": competence_ok,
            "trunk": args.trunk,
            "use_4b_fallback": not competence_ok and args.trunk == "1.7b",
            "if_failed": "rerun every floor once with --trunk 4b"
            if not competence_ok and args.trunk == "1.7b"
            else "INCONCLUSIVE"
            if not competence_ok
            else None,
        },
        "base_competence": {
            "passed": base_passed,
            "n": len(base_rows),
            "rate": base_passed / len(base_rows),
            "floor": "5/32",
            "overall_floor_pass": base_passed >= 5,
            "long_context_turns_passed": sum(bool(turn["pass"]) for turn in long_turns),
            "long_context_turns_n": len(long_turns),
            "long_context_turns_rate": long_turn_rate,
            "long_context_floor_pass": sum(bool(turn["pass"]) for turn in long_turns)
            >= 6,
            "passed_both": competence_ok,
            "trunk": args.trunk,
            "use_4b_fallback": not competence_ok and args.trunk == "1.7b",
            "if_failed": (
                "rerun preflight with --trunk 4b"
                if not competence_ok and args.trunk == "1.7b"
                else "leg void"
                if not competence_ok
                else None
            ),
        },
        "bitwise_base_rerun": {"cases": 4, "passed": deterministic},
        "invariants": invariants,
        "selector_coverage": {
            "candidates": candidates,
            "kept": kept,
            "fraction_spans_kept": kept / candidates if candidates else None,
            "budget_columns": budget,
            "used_columns": used,
            "fraction_budget_used": used / budget if budget else None,
            "by_role": {
                role: {
                    "eligible_spans": sum(
                        len(turn.get("eligible_spans_by_role", {}).get(role, []))
                        for row in selectors
                        for turn in row.get("turns", [])
                    ),
                    "selected_spans": sum(
                        len(turn.get("selected_spans_by_role", {}).get(role, []))
                        for row in selectors
                        for turn in row.get("turns", [])
                    ),
                }
                for role in ("user", "tool")
            },
            "nominal_b": budget,
            "actual_b": used,
            "capacity_rejections": sum(
                int(turn.get("capacity_rejections", 0))
                for row in selectors
                for turn in row.get("turns", [])
            ),
            "fallback_count": sum(
                int(turn.get("fallback_count", 0))
                for row in selectors
                for turn in row.get("turns", [])
            ),
        },
        "feasibility": {
            "pressure_exposed_cases": len(exposed_records),
            "no_pressure_cases": len(long_records) - len(exposed_records),
            "pressure_exposed_floor": 4,
            "tool_chunk_exposed_case_turns": exposed_tool_turns,
            "tool_chunk_floor": 4,
            "passed": len(exposed_records) >= 4 and exposed_tool_turns >= 4,
            "a4_informative": exposed_tool_turns > 0,
        },
        "timing": {
            "seconds": seconds,
            "cases": len(first),
            "seconds_per_case": seconds / len(first),
            "projected_sealed_cases": 64,
            "projected_sealed_hours": projected_hours,
            "cap_gpu_hours": 30,
            "arm_cut_required": projected_hours > 30,
            "projected_reduced_hours": reduced_projected_hours,
            "measured_reduced_arm_seconds": reduced_seconds,
            "stop_inconclusive": projected_hours > 30 and reduced_projected_hours > 30,
            "sealed_arms": (
                ["base", "clf_pinned_echo", "clf_control", "recency_pinned", "full"]
                if projected_hours > 30
                else list(ARMS)
            ),
        },
    }
    cost_ok = projected_hours <= 30 or reduced_projected_hours <= 30
    gates = {
        "competence": report["competence"],
        "determinism": report["bitwise_base_rerun"],
        "feasibility": report["feasibility"],
        "invariants": report["invariants"],
        "cost": {
            "passed": cost_ok,
            "full_projected_hours": projected_hours,
            "reduced_projected_hours": reduced_projected_hours,
            "cap_gpu_hours": 30,
        },
    }
    all_passed = all(_gate_passed(value) for value in gates.values())
    report["schema"] = 5
    report["status"] = "PASSED" if all_passed else "INCONCLUSIVE"
    if all_passed:
        contract_meta = artifact_meta(args)
        cut = projected_hours > 30
        contract_meta["arms"] = list(REDUCED_ARMS if cut else ARMS)
        contract_meta["cost_arm_cut"] = cut
        payload = certificate_payload(contract_meta, gates)
        report["certificate"] = payload
        report["certificate_sha256"] = _canonical_sha256(payload)
    else:
        report["failure_state"] = (
            "FALLBACK_REQUIRED_4B"
            if not competence_ok and args.trunk == "1.7b"
            else "INCONCLUSIVE"
        )
    atomic_json(output / "preflight.json", report)
    print(json.dumps(report, indent=2))
    if not all_passed:
        raise RuntimeError(f"registered preflight failed: {report['failure_state']}")


def main() -> None:
    args = parse_args()
    if args.split == "sealed":
        assert_clean_git_for_sealed()
    determinism.assert_gpu_free_or_owned()
    output = Path(args.out)
    if not output.is_absolute():
        output = ROOT / "results/qwen" / output
    cases, verified_inputs = _load_cases_verified(args.split, args.limit)
    with (ROOT / "data/bench/pins-manifest.json").open("rb") as handle:
        pins = json.loads(handle.read())["pins"][
            "ShishirPatil/gorilla BFCL V3 multi-turn"
        ]
    verified_docs, verified_runtime = _load_verified_runtime_inputs(pins)
    base_meta = artifact_meta(
        args,
        verified_inputs=verified_inputs,
        verified_runtime=verified_runtime,
    )
    certificate_sha256 = None
    if args.split == "sealed":
        certificate_sha256 = validate_preflight_certificate(
            args.preflight_certificate, base_meta
        )
    meta = bind_run_identity(base_meta, certificate_sha256)
    _check_or_write_meta(output / "meta.json", meta)
    from stencil.selector_v2 import ClassifierScorer

    model, tokenizer = load_model(args.trunk)
    scorer = ClassifierScorer(ROOT / "data/classifier/model/ft")
    if args.command == "preflight":
        preflight(
            args,
            model,
            tokenizer,
            scorer,
            cases=cases,
            verified_docs=verified_docs,
        )
    else:
        run(
            args,
            model,
            tokenizer,
            scorer,
            meta=meta,
            cases=cases,
            verified_docs=verified_docs,
        )


if __name__ == "__main__":
    main()
