#!/usr/bin/env python3
"""Minimal no-server BFCL V3 multi-turn runner for the hand-rolled Qwen trunk."""

from __future__ import annotations

import argparse
import ast
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
    ARMS,
    CATEGORIES,
    assert_case_record_schema,
    atomic_json,
    budget_history_spans,
    build_matched_control,
    call_to_python,
    context_layout,
    echo_copy_flag,
    ensure_split_allowed,
    execute_call_strings,
    load_jsonl,
    parse_tool_calls,
    prepare_case,
    recency_pinned_plan,
    recent_user_spans,
    render_echo,
    score_case,
    select_history_spans,
    summarize_records,
    tool_swap_plan,
)

K = 8192
MAX_STEPS = 20
COHORT_SEED = 20260902
CONTROL_SEED = 20260903
CHUNK_TOKENS = 128
ECHO_CAP = 1024
SELECTOR_THRESHOLD = 0.5
ECHO_HEADER = "Earlier context restated verbatim:"
ADDED_FUNCTION_PROMPT = (
    "I have updated some more functions you can choose from. What about now?"
)
DATA = ROOT / "data/bench/bfcl_v3_mt"
CASE_FILES = {category: DATA / f"cases_{category}.jsonl" for category in CATEGORIES}
ANSWER_FILES = {category: DATA / f"answers_{category}.jsonl" for category in CATEGORIES}


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
    args = parser.parse_args(argv)
    ensure_split_allowed(args.split)
    if args.max_new <= 0 or args.deadline <= 0:
        parser.error("--max-new and --deadline must be positive")
    if args.command == "preflight" and args.split != "dev":
        parser.error("--preflight is dev-only")
    if args.command == "preflight" and args.limit is not None:
        parser.error("preflight always runs the complete 32-case dev slice")
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

    from stencil.bench import EOS
    from stencil.qwen3 import KVCache, prefill_with_eviction

    ids = tokenizer.encode(prompt).ids
    if not ids:
        raise ValueError("empty prompt")
    device = next(model.parameters()).device
    cache = cache or KVCache(model.cfg)
    generated = []
    started = time.monotonic()
    timed_out = False
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
            active_columns = sorted(
                column for start, end in keep for column in range(start, end)
            )
            suffix = len(ids) - history_end
            overflow = max(
                0,
                protected_end + len(active_columns) + suffix - K,
            )
            if overflow:
                pin_overflow = min(overflow, len(active_columns))
                active_columns = active_columns[: len(active_columns) - pin_overflow]
            active_keep = []
            for column in active_columns:
                if active_keep and active_keep[-1][1] == column:
                    active_keep[-1] = (active_keep[-1][0], column + 1)
                else:
                    active_keep.append((column, column + 1))
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
            else sum(end - start for start, end in active_keep)
        )
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
        "columns_before": columns_before,
        "columns_after": columns_after,
        "pinned_columns": pinned_columns,
        "evictable_size": (
            int(evict_range[1]) - int(evict_range[0]) if evict_range is not None else 0
        ),
        "pin_overflow": pin_overflow,
        "columns_after_step": int(cache.k[0].shape[2]),
        "_cache": cache,
    }


def _tool_step_suffix(tokenizer, outputs: list[str]) -> list[int]:
    body = "<|im_end|>\n<|im_start|>user"
    for output in outputs:
        body += f"\n<tool_response>\n{output}\n</tool_response>"
    body += "<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"
    return list(tokenizer.encode(body).ids)


def _echo_current_user(context: str, entries: list[dict]) -> str:
    if not entries:
        return context
    marker = context.rfind("<|im_start|>user\n")
    close = context.find("<|im_end|>", marker)
    if marker < 0 or close < 0:
        raise ValueError("current user turn is not closed")
    rendered = render_echo(entries)
    return context[:close] + "\n\n" + rendered + context[close:]


def teacher_forced_turn_contexts(
    tokenizer, messages: list[dict], tools: list[dict], arms
) -> dict[str, dict]:
    """Build and assert the arm-independent pre-intervention context IDs."""
    context = render_prompt(messages, tools)
    ids = list(tokenizer.encode(context).ids)
    contexts = {arm: {"context": context, "context_ids": list(ids)} for arm in arms}
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


def _echo_cap(tokenizer, entries: list[dict]) -> tuple[list[dict], int]:
    chosen: list[dict] = []
    for row in entries:
        proposed = [*chosen, row]
        tokens = len(tokenizer.encode(render_echo(proposed)).ids)
        if tokens > ECHO_CAP:
            continue
        chosen = proposed
    return chosen, len(tokenizer.encode(render_echo(chosen)).ids) if chosen else 0


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
    if arm in {"base", "full"}:
        return {
            "evict_range": layout["evict_range"],
            "keep": [],
            "entries": [],
            "echo_ids": [],
            "selector": empty,
        }
    eligible, candidates, dropped = select_history_spans(
        tokenizer, context, messages, scorer, threshold=SELECTOR_THRESHOLD
    )
    kept, classifier_pins, budget = budget_history_spans(
        eligible, layout["evict_range"]
    )
    classifier_entries, classifier_echo_tokens = _echo_cap(tokenizer, kept)
    echo_context = _echo_current_user(context, classifier_entries)
    echo_layout = context_layout(tokenizer, echo_context)
    if echo_layout["evict_range"] != layout["evict_range"]:
        raise AssertionError("echo changed prior-history eviction coordinates")
    control = build_matched_control(
        candidates, kept, echo_layout["evict_range"], seed=CONTROL_SEED
    )
    control_entries, control_echo_tokens = _echo_cap(tokenizer, control["entries"])
    classifier_columns = sum(end - start for start, end in classifier_pins)
    role_pins = recent_user_spans(candidates, layout["evict_range"], classifier_columns)
    recency = recency_pinned_plan(candidates, classifier_columns, layout["evict_range"])
    recency_entries, recency_echo_tokens = _echo_cap(tokenizer, recency["entries"])
    tool_swap = tool_swap_plan(
        candidates, kept, layout["evict_range"], seed=CONTROL_SEED
    )
    swap_entries, swap_echo_tokens = _echo_cap(tokenizer, tool_swap["entries"])
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
    rendered = render_echo(entries)
    return {
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
            "role_counts": control["role_counts"],
            "control_role_shortfall": control["role_shortfall"],
            "echo_dropped_control_tokens": dropped,
            "echo_tokens": echo_tokens,
            "spans": kept,
        },
    }


def _degenerate(ids: list[int], truncated: bool) -> bool:
    if truncated:
        return True
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
    selector_turns = []
    context_ids_by_turn = []
    arm_started = time.monotonic()
    for turn_index, original_messages in enumerate(case["question"]):
        if args.mode == "teacher":
            turn_case = prepare_case(raw_case, DATA / "function_docs")
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
        plan = _turn_plan(
            tokenizer,
            messages,
            tools,
            arm,
            scorer,
            seed=COHORT_SEED + turn_index * 101,
        )
        context_ids_by_turn.append(
            list(tokenizer.encode(render_prompt(messages, tools)).ids)
        )
        selector_turns.append(plan["selector"])
        first_eviction = None
        cache = None
        continuation_ids = None
        for _step in range(MAX_STEPS):
            remaining = max(1e-6, args.deadline - (time.monotonic() - turn_started))
            base_context = render_prompt(messages, tools)
            context = _echo_current_user(base_context, plan["entries"])
            echo_added = len(tokenizer.encode(context).ids) - len(
                tokenizer.encode(base_context).ids
            )
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
            if first_eviction is None:
                first_eviction = {
                    "evicted": result["evicted"],
                    "columns_before": result["columns_before"],
                    "columns_after": result["columns_after"],
                    "pinned_columns": result["pinned_columns"],
                    "evictable_size": result["evictable_size"],
                    "budget_used": plan["selector"]["used"],
                    "echo_tokens": plan["selector"].get("echo_tokens", 0),
                    "pin_overflow": result["pin_overflow"],
                }
            any_eviction |= result["evicted"]
            if _step == 0:
                total_echo_added += echo_added
            copied_echo |= echo_copy_flag(result["token_ids"], plan["echo_ids"])
            responses.append(result)
            turn_timeout |= result["timeout"]
            turn_truncated |= result["truncated"]
            turn_degenerate |= _degenerate(result["token_ids"], result["truncated"])
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
        if args.mode == "teacher":
            decoded_for_score = [
                [list(calls)] for calls in ground_truth[:turn_index]
            ] + [decoded_steps]
        else:
            decoded_turns.append(decoded_steps)
            decoded_for_score = decoded_turns
        turn_score = score_case(
            active_case,
            decoded_for_score,
            ground_truth[: turn_index + 1],
            run_name=f"score_{run_tag}_{arm}_turn_{turn_index}",
        )
        turns.append(
            {
                "turn": turn_index,
                "responses": responses,
                "tool_calls": turn_calls,
                "timeout": turn_timeout,
                "truncated": turn_truncated,
                "degenerate": turn_degenerate,
                "pass": bool(turn_score["valid"]),
                "score": turn_score,
                "eviction": first_eviction,
                "prompt_positions": responses[0]["prompt_tokens"] if responses else 0,
            }
        )
        if turn_timeout:
            break
    if args.mode == "teacher":
        final_score = {"valid": all(turn["pass"] for turn in turns)}
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
        "repeated_history_calls": 0,
        "_context_ids": context_ids_by_turn,
    }


def run_case(model, tokenizer, scorer, category, raw_case, ground_truth, args, run_tag):
    started = time.monotonic()
    selected_arms = ARMS if args.mode == "teacher" else ("base", "clf_pinned_echo")
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
    record = {
        "schema": 3,
        "mode": args.mode,
        "case_id": raw_case["id"],
        "category": category,
        "arms": arms,
        "seconds": time.monotonic() - started,
        "first_divergence_turn": first_divergence,
    }
    if args.mode == "teacher":
        assert_case_record_schema(record)
    return record


def artifact_meta(args) -> dict:
    files = [*CASE_FILES.values(), *ANSWER_FILES.values(), DATA / "cohorts.json"]
    return {
        "schema": 3,
        "split": args.split,
        "mode": args.mode,
        "arms": list(ARMS if args.mode == "teacher" else ("base", "clf_pinned_echo")),
        "trunk": args.trunk,
        "max_new": args.max_new,
        "deadline": args.deadline,
        "k": K,
        "budget_fraction": 0.25,
        "chunk_tokens": CHUNK_TOKENS,
        "echo_cap": ECHO_CAP,
        "selector_threshold": SELECTOR_THRESHOLD,
        "echo_header": ECHO_HEADER,
        "control_seed": CONTROL_SEED,
        "selector_roles": ["user", "tool"],
        "selector_context": "empty",
        "eviction_timing": "pre-query",
        "protected_prefix": "system_plus_tools_and_at_least_four_sink_columns",
        "greedy": True,
        "thinking": False,
        "script_sha256": sha256(__file__),
        "classifier_sha256": assert_registered_classifier(),
        "data_sha256": {str(path.relative_to(ROOT)): sha256(path) for path in files},
    }


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
    args, model, tokenizer, scorer, *, resume: bool = True, run_tag: str = "main"
) -> list[dict]:
    output = Path(args.out)
    if not output.is_absolute():
        output = ROOT / "results/qwen" / output
    records_dir = output / "records"
    records_dir.mkdir(parents=True, exist_ok=True)
    _check_or_write_meta(output / "meta.json", artifact_meta(args))
    records = []
    cases = load_cases(args.split, args.limit)
    for index, (category, case, answer) in enumerate(cases):
        path = records_dir / f"{case['id']}.json"
        if resume and path.exists():
            record = json.loads(path.read_text())
            if args.mode == "teacher":
                assert_case_record_schema(record)
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
        json.loads(path.read_text()) for path in sorted(records_dir.glob("*.json"))
    ]
    summary = (
        summarize_records(all_records)
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


def preflight(args, model, tokenizer, scorer) -> None:
    first = run(args, model, tokenizer, scorer, resume=True, run_tag="preflight_a")
    dev_cases = load_cases("dev")
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
    selectors = [record["arms"]["clf_pinned"]["selector"] for record in first]
    candidates = sum(row["candidates"] for row in selectors)
    kept = sum(row["kept"] for row in selectors)
    budget = sum(row["budget"] for row in selectors)
    used = sum(row["used"] for row in selectors)
    seconds = sum(float(record["seconds"]) for record in first)
    competence_rate = sum(row["final_pass"] for row in base_rows) / len(base_rows)
    long_turns = [
        turn
        for record in first
        if record["category"] == "long_context"
        for turn in record["arms"]["base"]["turns"]
    ]
    long_turn_rate = sum(bool(turn["pass"]) for turn in long_turns) / len(long_turns)
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
    competence_ok = competence_rate >= 0.15 and long_turn_rate >= 0.15
    projected_hours = seconds / len(first) * 64 / 3600
    report = {
        "base_competence": {
            "passed": sum(row["final_pass"] for row in base_rows),
            "n": len(base_rows),
            "rate": competence_rate,
            "floor": 0.15,
            "overall_floor_pass": competence_rate >= 0.15,
            "long_context_turns_passed": sum(bool(turn["pass"]) for turn in long_turns),
            "long_context_turns_n": len(long_turns),
            "long_context_turns_rate": long_turn_rate,
            "long_context_floor_pass": long_turn_rate >= 0.15,
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
        "selector_coverage": {
            "candidates": candidates,
            "kept": kept,
            "fraction_spans_kept": kept / candidates if candidates else None,
            "budget_columns": budget,
            "used_columns": used,
            "fraction_budget_used": used / budget if budget else None,
        },
        "feasibility": {
            "pressure_exposed_cases": len(exposed_records),
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
            "sealed_arms": (
                ["base", "clf_pinned_echo", "clf_control", "recency_pinned", "full"]
                if projected_hours > 30
                else list(ARMS)
            ),
        },
    }
    output = Path(args.out)
    if not output.is_absolute():
        output = ROOT / "results/qwen" / output
    atomic_json(output / "preflight.json", report)
    print(json.dumps(report, indent=2))


def main() -> None:
    args = parse_args()
    determinism.assert_gpu_free_or_owned()
    output = Path(args.out)
    if not output.is_absolute():
        output = ROOT / "results/qwen" / output
    _check_or_write_meta(output / "meta.json", artifact_meta(args))
    from stencil.selector_v2 import ClassifierScorer

    model, tokenizer = load_model(args.trunk)
    scorer = ClassifierScorer(ROOT / "data/classifier/model/ft")
    if args.command == "preflight":
        preflight(args, model, tokenizer, scorer)
    else:
        run(args, model, tokenizer, scorer)


if __name__ == "__main__":
    main()
