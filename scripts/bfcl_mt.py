#!/usr/bin/env python3
"""Minimal no-server BFCL V3 multi-turn runner for the hand-rolled Qwen trunk."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "vendor"))

from stencil import determinism  # noqa: F401, E402
from stencil.bfcl import (  # noqa: E402
    CATEGORIES,
    atomic_json,
    call_to_python,
    control_echo,
    echo_copy_flag,
    ensure_split_allowed,
    execute_call_strings,
    load_jsonl,
    parse_tool_calls,
    prepare_case,
    score_case,
    summarize_records,
)
from stencil.ledger import (  # noqa: E402
    Entry,
    context_tokens_added,
    text_ledger_context,
)

K = 8192
MAX_STEPS = 20
COHORT_SEED = 20260902
ADDED_FUNCTION_PROMPT = (
    "I have updated some more functions you can choose from. What about now?"
)
DATA = ROOT / "data/bench/bfcl_v3_mt"
CASE_FILES = {category: DATA / f"cases_{category}.jsonl" for category in CATEGORIES}
ANSWER_FILES = {category: DATA / f"answers_{category}.jsonl" for category in CATEGORIES}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split", choices=("dev", "sealed"), default="dev")
    parser.add_argument("--arm", choices=("base", "ledger", "control"), default="base")
    parser.add_argument("--trunk", choices=("1.7b", "4b"), default="1.7b")
    parser.add_argument("--max-new", type=int, default=512)
    parser.add_argument("--deadline", type=float, default=300.0)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--out", default="bfcl-mt")
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args(argv)
    ensure_split_allowed(args.split)
    if args.max_new <= 0 or args.deadline <= 0:
        parser.error("--max-new and --deadline must be positive")
    if args.preflight and args.split != "dev":
        parser.error("--preflight is dev-only")
    return args


def sha256(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_cases(split: str, limit: int | None = None) -> list[tuple[str, dict, list]]:
    cohort = json.loads((DATA / "cohorts.json").read_text())[split]
    cases = {
        row["id"]: (category, row)
        for category, path in CASE_FILES.items()
        for row in load_jsonl(path)
    }
    answers = {
        row["id"]: row["ground_truth"]
        for path in ANSWER_FILES.values()
        for row in load_jsonl(path)
    }
    ids = cohort[:limit] if limit is not None else cohort
    return [(cases[case_id][0], cases[case_id][1], answers[case_id]) for case_id in ids]


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


def _token_span(encoding, start: int, end: int) -> tuple[int, int] | None:
    columns = [
        index
        for index, (left, right) in enumerate(encoding.offsets)
        if left < end and right > start
    ]
    return (columns[0], columns[-1] + 1) if columns else None


def _message_locations(
    prompt: str, messages: list[dict]
) -> list[tuple[dict, int, int]]:
    locations = []
    cursor = 0
    for message in messages:
        if message["role"] not in {"system", "user"}:
            continue
        marker = f"<|im_start|>{message['role']}\n"
        marker_at = prompt.find(marker, cursor)
        if marker_at < 0:
            continue
        start = marker_at + len(marker)
        end = start + len(message.get("content", ""))
        locations.append((message, start, end))
        cursor = end
    return locations


def _focus_entries(tokenizer, prompt: str, messages: list[dict], tools: list[dict]):
    from stencil.salience2 import DEFAULT_BACKEND, extract_instructions

    encoding = tokenizer.encode(prompt)
    user_entries = []
    prior_user_columns = []
    user_locations = [
        item
        for item in _message_locations(prompt, messages)
        if item[0]["role"] == "user"
    ]
    for turn, (message, start, end) in enumerate(user_locations[:-1], start=1):
        span = _token_span(encoding, start, end)
        if span:
            prior_user_columns.extend(range(*span))
        for found in extract_instructions(message["content"], backend=DEFAULT_BACKEND):
            token_span = _token_span(encoding, start + found.start, start + found.end)
            if token_span:
                user_entries.append(
                    Entry(
                        found.text(message["content"]),
                        token_span,
                        None,
                        turn,
                        provenance=f"salience2:{DEFAULT_BACKEND}",
                    )
                )
    schema_entries = []
    cursor = 0
    for tool in tools:
        text = json.dumps(tool)
        start = prompt.find(text, cursor)
        if start < 0:
            raise ValueError(f"schema not found in rendered prompt: {tool['name']}")
        span = _token_span(encoding, start, start + len(text))
        if span:
            schema_entries.append(Entry(text, span, None, 0, provenance="tool_schema"))
        cursor = start + len(text)
    return user_entries, schema_entries, sorted(set(prior_user_columns))


def _columns_to_spans(columns: list[int]) -> list[tuple[int, int]]:
    spans = []
    for column in sorted(set(columns)):
        if spans and spans[-1][1] == column:
            spans[-1] = (spans[-1][0], column + 1)
        else:
            spans.append((column, column + 1))
    return spans


def _entry_columns(entries: list[Entry], budget: int) -> list[int]:
    columns = []
    seen = set()
    for entry in entries:
        for column in range(*entry.span):
            if column not in seen:
                columns.append(column)
                seen.add(column)
                if len(columns) == budget:
                    return columns
    return columns


def _control_context(
    tokenizer, base: str, prior: list[str], target_added: int, seed: int
):
    if target_added == 0:
        return base, [], 0
    overhead = context_tokens_added(
        tokenizer, base, text_ledger_context(base, [Entry("", (0, 0), None, 0)])
    )
    estimate = max(1, target_added - overhead)
    for target in range(max(1, estimate - 8), estimate + 9):
        text, _ = control_echo(tokenizer, prior, target, seed)
        entry = Entry(text, (0, 0), None, 0, provenance="random_user_span")
        context = text_ledger_context(base, [entry])
        added = context_tokens_added(tokenizer, base, context)
        if added == target_added:
            return context, tokenizer.encode(text).ids, added
    raise ValueError("could not token-match random-span control echo")


def arm_context(
    tokenizer, messages: list[dict], tools: list[dict], arm: str, seed: int
):
    base = render_prompt(messages, tools)
    if arm == "base":
        return base, [], [], 0
    user_entries, schema_entries, prior_columns = _focus_entries(
        tokenizer, base, messages, tools
    )
    budget = min(
        len(prior_columns),
        len(
            {
                column
                for entry in [*user_entries, *schema_entries]
                for column in range(*entry.span)
            }
        ),
    )
    ledger_columns = _entry_columns([*user_entries, *schema_entries], budget)
    ledger_context = text_ledger_context(base, user_entries)
    target_added = context_tokens_added(tokenizer, base, ledger_context)
    if arm == "ledger":
        echo_ids = tokenizer.encode("\n".join(entry.text for entry in user_entries)).ids
        return ledger_context, _columns_to_spans(ledger_columns), echo_ids, target_added
    prior_texts = [
        message["content"] for message in messages[:-1] if message["role"] == "user"
    ]
    control_context, echo_ids, added = _control_context(
        tokenizer, base, prior_texts, target_added, seed
    )
    if budget:
        start = seed % len(prior_columns)
        control_columns = [
            prior_columns[(start + i) % len(prior_columns)] for i in range(budget)
        ]
        if len(set(control_columns)) != budget:
            raise AssertionError("control pin budget contains duplicate columns")
    else:
        control_columns = []
    return control_context, _columns_to_spans(control_columns), echo_ids, added


def _eviction_end(cache_columns: int, keep: list[tuple[int, int]], target: int) -> int:
    need = cache_columns - target
    if need <= 0:
        return 0
    kept = {column for start, end in keep for column in range(start, end)}
    removed = 0
    for end in range(1, cache_columns + 1):
        if end - 1 not in kept:
            removed += 1
        if removed == need:
            return end
    raise ValueError("pin budget leaves too few evictable columns")


def generate(model, tokenizer, prompt: str, keep, max_new: int, deadline: float):
    import torch

    from stencil.bench import EOS
    from stencil.qwen3 import KVCache

    ids = tokenizer.encode(prompt).ids
    if not ids:
        raise ValueError("empty prompt")
    device = next(model.parameters()).device
    cache = KVCache(model.cfg)
    generated = []
    started = time.monotonic()
    timed_out = False
    evicted = False
    with torch.no_grad():
        if len(ids) > 1:
            model(torch.tensor([ids[:-1]], device=device), cache=cache)
        if len(ids) > K:
            clipped = [
                (start, min(end, len(ids) - 1))
                for start, end in keep
                if start < len(ids) - 1
            ]
            drop_end = _eviction_end(len(ids) - 1, clipped, K - 1)
            cache.evict(0, drop_end, keep=clipped)
            evicted = True
        logits = model(torch.tensor([[ids[-1]]], device=device), cache=cache)
        next_token = int(logits[0, -1].argmax())
        while next_token not in EOS and len(generated) < max_new:
            if time.monotonic() - started > deadline:
                timed_out = True
                break
            generated.append(next_token)
            logits = model(torch.tensor([[next_token]], device=device), cache=cache)
            next_token = int(logits[0, -1].argmax())
    return {
        "text": tokenizer.decode(generated, skip_special_tokens=False),
        "token_ids": generated,
        "truncated": len(generated) >= max_new,
        "timeout": timed_out,
        "evicted": evicted,
        "prompt_tokens": len(ids),
    }


def run_case(
    model,
    tokenizer,
    category: str,
    raw_case: dict,
    ground_truth: list,
    args,
    run_tag: str,
):
    case = prepare_case(raw_case, DATA / "function_docs")
    tools = case["function"]
    holdouts = case.get("missed_function", {})
    messages = []
    decoded_turns = []
    turns = []
    any_eviction = False
    copied_echo = False
    total_echo_added = 0
    for turn_index, original_messages in enumerate(case["question"]):
        if str(turn_index) in holdouts:
            tools.extend(holdouts[str(turn_index)])
            current_messages = [{"role": "user", "content": ADDED_FUNCTION_PROMPT}]
        else:
            current_messages = original_messages
        messages.extend(current_messages)
        responses = []
        turn_calls = []
        decoded_steps = []
        turn_started = time.monotonic()
        turn_timeout = False
        turn_truncated = False
        for step in range(MAX_STEPS + 1):
            remaining = max(1e-6, args.deadline - (time.monotonic() - turn_started))
            context, keep, echo_ids, echo_added = arm_context(
                tokenizer,
                messages,
                tools,
                args.arm,
                seed=COHORT_SEED + turn_index * 101 + step,
            )
            result = generate(model, tokenizer, context, keep, args.max_new, remaining)
            any_eviction |= result["evicted"]
            total_echo_added += echo_added
            copied_echo |= echo_copy_flag(result["token_ids"], echo_ids)
            responses.append(result)
            turn_timeout |= result["timeout"]
            turn_truncated |= result["truncated"]
            messages.append({"role": "assistant", "content": result["text"]})
            parsed = parse_tool_calls(result["text"])
            executable = []
            call_records = []
            for item in parsed:
                record = asdict(item)
                if item.valid:
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
                executable, case, f"stencil_{run_tag}_{args.arm}"
            )
            for record, output in zip(
                [record for record in call_records if record["valid"]],
                execution,
                strict=True,
            ):
                record["execution"] = output
                messages.append({"role": "tool", "content": output})
        decoded_turns.append(decoded_steps)
        turn_score = score_case(
            case,
            decoded_turns,
            ground_truth[: turn_index + 1],
            run_name=f"score_{run_tag}_turn_{turn_index}",
        )
        turns.append(
            {
                "turn": turn_index,
                "responses": responses,
                "tool_calls": turn_calls,
                "timeout": turn_timeout,
                "truncated": turn_truncated,
                "pass": bool(turn_score["valid"]),
                "score": turn_score,
            }
        )
        if turn_timeout:
            break
    if len(decoded_turns) == len(ground_truth):
        final_score = score_case(
            case, decoded_turns, ground_truth, run_name=f"score_{run_tag}_final"
        )
    else:
        final_score = {"valid": False, "error_type": "stencil:incomplete_timeout"}
    return {
        "case_id": case["id"],
        "category": category,
        "arm": args.arm,
        "turns": turns,
        "evicted": any_eviction,
        "echo_tokens_added": total_echo_added,
        "echo_copy": copied_echo,
        "final_pass": bool(final_score["valid"]),
        "final_score": final_score,
    }


def artifact_meta(args) -> dict:
    files = [*CASE_FILES.values(), *ANSWER_FILES.values(), DATA / "cohorts.json"]
    return {
        "schema": 1,
        "split": args.split,
        "arm": args.arm,
        "trunk": args.trunk,
        "max_new": args.max_new,
        "deadline": args.deadline,
        "k": K,
        "greedy": True,
        "thinking": False,
        "script_sha256": sha256(__file__),
        "data_sha256": {str(path.relative_to(ROOT)): sha256(path) for path in files},
    }


def run(
    args, model, tokenizer, *, resume: bool = True, run_tag: str = "main"
) -> list[dict]:
    output = Path(args.out)
    if not output.is_absolute():
        output = ROOT / "results/qwen" / output
    records_dir = output / "records"
    records_dir.mkdir(parents=True, exist_ok=True)
    atomic_json(output / "meta.json", artifact_meta(args))
    records = []
    cases = load_cases(args.split, args.limit)
    for index, (category, case, answer) in enumerate(cases):
        path = records_dir / f"{case['id']}--{args.arm}.json"
        if resume and path.exists():
            record = json.loads(path.read_text())
        else:
            record = run_case(
                model, tokenizer, category, case, answer, args, f"{run_tag}_{index}"
            )
            atomic_json(path, record)
        records.append(record)
        valid_calls = sum(
            call["valid"] for turn in record["turns"] for call in turn["tool_calls"]
        )
        total_calls = sum(len(turn["tool_calls"]) for turn in record["turns"])
        print(
            f"{index + 1}: {case['id']} {args.arm} pass={record['final_pass']} "
            f"valid={valid_calls}/{total_calls}",
            flush=True,
        )
    all_records = [
        json.loads(path.read_text()) for path in sorted(records_dir.glob("*.json"))
    ]
    atomic_json(output / "summary.json", summarize_records(all_records))
    return records


def finder_recall() -> dict:
    from stencil.salience2 import DEFAULT_BACKEND, extract_instructions

    labels = json.loads((DATA / "finder_labels.json").read_text())["labels"]
    results = []
    for label in labels:
        if label["kind"] == "tool_schema":
            hit = True  # schemas are explicitly admitted as automatic schema spans
        else:
            hit = bool(extract_instructions(label["text"], backend=DEFAULT_BACKEND))
        results.append({"case_id": label["case_id"], "kind": label["kind"], "hit": hit})
    return {
        "backend": DEFAULT_BACKEND,
        "labels": len(results),
        "hits": sum(row["hit"] for row in results),
        "recall": sum(row["hit"] for row in results) / len(results),
        "by_kind": {
            kind: {
                "n": sum(row["kind"] == kind for row in results),
                "hits": sum(row["kind"] == kind and row["hit"] for row in results),
            }
            for kind in sorted({row["kind"] for row in results})
        },
    }


def response_ids(record: dict) -> list[list[list[int]]]:
    return [
        [response["token_ids"] for response in turn["responses"]]
        for turn in record["turns"]
    ]


def preflight(args, model, tokenizer) -> None:
    args.arm = "base"
    args.limit = None
    first = run(args, model, tokenizer, resume=True, run_tag="preflight_a")
    second = [
        run_case(model, tokenizer, category, case, answer, args, f"preflight_b_{index}")
        for index, (category, case, answer) in enumerate(load_cases("dev"))
    ]
    deterministic = all(
        response_ids(left) == response_ids(right)
        for left, right in zip(first, second, strict=True)
    )
    report = {
        "base_competence": {
            "passed": sum(row["final_pass"] for row in first),
            "n": len(first),
            "rate": sum(row["final_pass"] for row in first) / len(first),
            "floor": 0.15,
            "floor_pass": sum(row["final_pass"] for row in first) / len(first) >= 0.15,
        },
        "finder": finder_recall(),
        "bitwise_base_rerun": deterministic,
    }
    report["finder"]["floor"] = 0.80
    report["finder"]["floor_pass"] = report["finder"]["recall"] >= 0.80
    output = Path(args.out)
    if not output.is_absolute():
        output = ROOT / "results/qwen" / output
    atomic_json(output / "preflight.json", report)
    print(json.dumps(report, indent=2))


def main() -> None:
    args = parse_args()
    model, tokenizer = load_model(args.trunk)
    if args.preflight:
        preflight(args, model, tokenizer)
    else:
        run(args, model, tokenizer)


if __name__ == "__main__":
    main()
