"""Small, CPU-testable helpers for the vendored BFCL V3 multi-turn harness."""

from __future__ import annotations

import hashlib
import json
import math
import os
import random
import re
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from stencil.stats import clustered_lower_bound

CATEGORIES = ("base", "missing_params", "missing_functions", "long_context")
ARMS = (
    "base",
    "clf_pinned",
    "clf_pinned_echo",
    "clf_control",
    "recency_pinned",
    "tool_swap_echo",
    "role_pinned",
    "full",
)
ECHO_HEADER = "Earlier context restated verbatim:"
CONTROL_MARKERS = (
    "<|im_",
    "<tool_call",
    "</tool_call",
    "<tool_response",
    "</tool_response",
)
UPSTREAM_CATEGORY = {
    "base": "multi_turn_base",
    "missing_params": "multi_turn_miss_param",
    "missing_functions": "multi_turn_miss_func",
    "long_context": "multi_turn_long_context",
}
FUNCTION_DOCS = {
    "GorillaFileSystem": "gorilla_file_system.json",
    "MathAPI": "math_api.json",
    "MessageAPI": "message_api.json",
    "TwitterAPI": "posting_api.json",
    "TicketAPI": "ticket_api.json",
    "TradingBot": "trading_bot.json",
    "TravelAPI": "travel_booking.json",
    "VehicleControlAPI": "vehicle_control.json",
}
TOOL_PATTERN = re.compile(r"<tool_call>\s*(.*?)\s*</tool_call>", re.DOTALL)


def _prefix_token_count(tokenizer, context: str, char_end: int) -> int:
    return len(tokenizer.encode(context[:char_end]).ids)


def context_layout(
    tokenizer,
    context: str,
    messages: Sequence[Mapping] | None = None,
    *,
    current_message_index: int | None = None,
) -> dict:
    """Locate the protected prefix and history by semantic message index."""
    if messages is not None:
        if current_message_index is None:
            user_indices = [
                index for index, row in enumerate(messages) if row["role"] == "user"
            ]
            if not user_indices:
                raise ValueError("current user message missing")
            current_message_index = user_indices[-1]
        location = next(
            (
                row
                for row in _message_locations(context, messages)
                if row["message_index"] == current_message_index
                and row["role"] == "user"
            ),
            None,
        )
        if location is None:
            raise ValueError("current user message index not rendered")
        current_marker = int(location["pool_start"])
        current_close = context.find("<|im_end|>", int(location["end"]))
        if current_close < 0:
            raise ValueError("current user message is not closed")
    else:
        current_marker = context.rfind("<|im_start|>user\n")
        if current_marker < 0:
            raise ValueError("current user marker missing")
        current_close = context.find("<|im_end|>", current_marker)
    if not context.startswith("<|im_start|>system\n"):
        raise ValueError("BFCL context must start with a system/tools block")
    system_end = context.find("<|im_end|>")
    if system_end < 0 or system_end > current_marker:
        raise ValueError("unterminated system/tools block")
    system_end += len("<|im_end|>")
    if context[system_end : system_end + 1] == "\n":
        system_end += 1
    ids = list(tokenizer.encode(context).ids)
    protected_end = max(4, _prefix_token_count(tokenizer, context, system_end))
    eviction_end = _prefix_token_count(tokenizer, context, current_marker)
    if protected_end > eviction_end:
        raise ValueError("protected prefix consumes prior history")
    return {
        "context_token_ids": ids,
        "protected_prefix": (0, protected_end),
        "evict_range": (protected_end, eviction_end),
        "history_end": eviction_end,
        "current_user_close": current_close,
    }


def _token_span(encoding, char_start: int, char_end: int) -> tuple[int, int] | None:
    columns = [
        index
        for index, (start, end) in enumerate(encoding.offsets)
        if start < char_end and end > char_start
    ]
    return (columns[0], columns[-1] + 1) if columns else None


def _message_locations(context: str, messages: Sequence[Mapping]) -> list[dict]:
    """Map rendered user/tool message contents back to character coordinates."""
    locations = []
    cursor = 0
    user_turn = 0
    start_index = int(bool(messages and messages[0]["role"] == "system"))
    for message_index, message in enumerate(messages[start_index:], start=start_index):
        role = str(message["role"])
        content = str(message.get("content", ""))
        if role == "user":
            marker = "<|im_start|>user\n"
            marker_at = context.find(marker, cursor)
            if marker_at < 0:
                raise ValueError(f"rendered user message {message_index} not found")
            start = marker_at + len(marker)
            user_turn += 1
            pool_start = marker_at
            close_marker = "<|im_end|>"
        elif role == "assistant":
            marker = "<|im_start|>assistant\n"
            marker_at = context.find(marker, cursor)
            if marker_at < 0:
                raise ValueError(
                    f"rendered assistant message {message_index} not found"
                )
            start = marker_at + len(marker)
            pool_start = marker_at
            close_marker = "<|im_end|>"
        elif role == "tool":
            marker = "<tool_response>\n"
            marker_at = context.find(marker, cursor)
            if marker_at < 0:
                raise ValueError(f"rendered tool message {message_index} not found")
            start = marker_at + len(marker)
            pool_start = marker_at
            close_marker = "</tool_response>"
        else:
            continue
        end = start + len(content)
        if context[start:end] != content:
            raise ValueError(
                f"rendered {role} message {message_index} content mismatch"
            )
        close = context.find(close_marker, end)
        if close < 0:
            raise ValueError(f"rendered {role} message {message_index} is not closed")
        locations.append(
            {
                "role": role,
                "content": content,
                "start": start,
                "end": end,
                "message_index": message_index,
                "turn": user_turn,
                "pool_start": pool_start,
                "pool_end": close + len(close_marker),
            }
        )
        cursor = end
    return locations


def _tool_line_spans(text: str) -> list[tuple[int, int]]:
    spans = []
    for match in re.finditer(r"[^\r\n]+", text):
        if match.group().strip():
            spans.append(match.span())
    return spans


def _chunk_char_span(
    tokenizer, text: str, span: tuple[int, int], size: int
) -> list[tuple[int, int]]:
    """Split a source character span into consecutive tokenizer chunks."""
    start, end = span
    encoding = tokenizer.encode(text[start:end])
    if not encoding.ids:
        return []
    chunks = []
    for at in range(0, len(encoding.ids), size):
        offsets = encoding.offsets[at : at + size]
        visible = [(left, right) for left, right in offsets if right > left]
        if visible:
            chunks.append((start + visible[0][0], start + visible[-1][1]))
    return chunks


def select_history_spans(
    tokenizer,
    context: str,
    messages: Sequence[Mapping],
    scorer,
    *,
    threshold: float = 0.5,
    chunk_tokens: int = 128,
) -> tuple[list[dict], list[dict], int]:
    """Score prior user sentences and newline/128-token tool chunks once."""
    from stencil.selector_v2 import split_sentence_spans

    encoding = tokenizer.encode(context)
    locations = _message_locations(context, messages)
    user_locations = [row for row in locations if row["role"] == "user"]
    current_user_index = user_locations[-1]["message_index"] if user_locations else -1
    candidates = []
    for location in locations:
        role = location["role"]
        if role not in {"user", "tool"}:
            continue
        if role == "user" and location["message_index"] == current_user_index:
            continue
        pieces = (
            split_sentence_spans(location["content"])
            if role == "user"
            else _tool_line_spans(location["content"])
        )
        if chunk_tokens <= 0:
            raise ValueError("chunk_tokens must be positive")
        local_spans = [
            chunk
            for piece in pieces
            for chunk in _chunk_char_span(
                tokenizer, location["content"], piece, chunk_tokens
            )
        ]
        role_span = _token_span(encoding, location["pool_start"], location["pool_end"])
        for local_start, local_end in local_spans:
            char_start = location["start"] + local_start
            char_end = location["start"] + local_end
            span = _token_span(encoding, char_start, char_end)
            if span is None:
                continue
            candidates.append(
                {
                    "text": context[char_start:char_end],
                    "role": role,
                    "turn": int(location["turn"]),
                    "message_index": int(location["message_index"]),
                    "char_span": [char_start, char_end],
                    "span": list(span),
                    "role_span": (
                        list(role_span) if role_span is not None else list(span)
                    ),
                }
            )
    dropped = sum(
        any(marker in str(row["text"]) for marker in CONTROL_MARKERS)
        for row in candidates
    )
    candidates = [
        row
        for row in candidates
        if not any(marker in str(row["text"]) for marker in CONTROL_MARKERS)
    ]
    for role in ("user", "tool"):
        role_rows = [row for row in candidates if row["role"] == role]
        texts = [row["text"] for row in role_rows]
        if not texts:
            continue
        scores = scorer(texts, role=role, contexts=[""] * len(texts))
        if len(scores) != len(role_rows):
            raise ValueError("classifier returned the wrong number of scores")
        for row, score in zip(role_rows, scores, strict=True):
            value = float(score)
            if not 0.0 <= value <= 1.0:
                raise ValueError("classifier score outside [0, 1]")
            row["score"] = value
    selected = [row for row in candidates if row["score"] >= threshold]
    return selected, candidates, dropped


def _columns_to_spans(columns: Sequence[int]) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    for column in sorted(set(columns)):
        if spans and spans[-1][1] == column:
            spans[-1] = (spans[-1][0], column + 1)
        else:
            spans.append((column, column + 1))
    return spans


def clamp_pins_newest_first(
    spans: Sequence[tuple[int, int]], overflow: int
) -> tuple[list[tuple[int, int]], int]:
    """Drop the highest-position pin columns first until overflow is covered."""
    columns = [column for start, end in spans for column in range(int(start), int(end))]
    dropped = min(max(0, overflow), len(columns))
    kept = sorted(columns)[: len(columns) - dropped] if dropped else sorted(columns)
    return _columns_to_spans(kept), dropped


def budget_history_spans(
    candidates: Sequence[Mapping],
    evict_range: tuple[int, int],
    *,
    fraction: float = 0.25,
) -> tuple[list[dict], list[tuple[int, int]], int]:
    """Fill the column budget by probability, then by most recent span."""
    if not 0.0 <= fraction <= 1.0:
        raise ValueError("budget fraction must be in [0, 1]")
    low, high = evict_range
    budget = math.floor((high - low) * fraction)
    kept = []
    ordered = sorted(
        enumerate(candidates),
        key=lambda item: (
            -float(item[1]["score"]),
            -int(item[1]["turn"]),
            -int(item[1].get("message_index", item[0])),
            item[0],
        ),
    )
    for _, candidate in ordered:
        columns = list(
            range(
                max(low, int(candidate["span"][0])),
                min(high, int(candidate["span"][1])),
            )
        )
        if len(columns) > budget - sum(len(row["pinned_columns"]) for row in kept):
            break
        if columns:
            row = dict(candidate)
            row["pinned_columns"] = columns
            kept.append(row)
    chosen = [column for row in kept for column in row["pinned_columns"]]
    return kept, _columns_to_spans(chosen), budget


def render_echo(entries: Sequence[Mapping]) -> str:
    """Render the neutral, source-labelled LEG A echo."""
    if not entries:
        return ""
    return (
        ECHO_HEADER
        + "\n"
        + "\n".join(f"- {row['role']}: {row['text']}" for row in entries)
    )


def _candidate_columns(row: Mapping, low: int, high: int) -> list[int]:
    span = row["span"]
    return list(range(max(low, int(span[0])), min(high, int(span[1]))))


def build_matched_control(
    candidates: Sequence[Mapping],
    kept: Sequence[Mapping],
    evict_range: tuple[int, int],
    *,
    seed: int,
    tokenizer=None,
    context: str | None = None,
) -> dict:
    """Nearest-free exact-column control with cross-role shortfall fill."""
    low, high = evict_range
    selected = {column for row in kept for column in row.get("pinned_columns", [])}
    needed = {
        role: sum(
            len(row.get("pinned_columns", [])) for row in kept if row["role"] == role
        )
        for role in ("user", "tool")
    }
    pools = {
        role: sorted(
            {
                column
                for row in candidates
                if row["role"] == role
                for column in _candidate_columns(row, low, high)
                if column not in selected
            }
        )
        for role in ("user", "tool")
    }
    column_roles = {
        column: role for role, columns in pools.items() for column in columns
    }
    anchors = {
        role: [
            column
            for row in kept
            if row["role"] == role
            for column in row.get("pinned_columns", [])
        ]
        for role in ("user", "tool")
    }
    chosen: list[int] = []
    shortfall = {"user": 0, "tool": 0}
    rng = random.Random(seed)
    for role in ("user", "tool"):
        pool = pools[role]
        tie = {column: rng.random() for column in pool}
        center = sum(anchors[role]) / len(anchors[role]) if anchors[role] else low
        ordered = sorted(pool, key=lambda column: (abs(column - center), tie[column]))
        take = min(needed[role], len(ordered))
        chosen.extend(ordered[:take])
        pools[role] = ordered[take:]
        shortfall[role] = needed[role] - take
    for role in ("user", "tool"):
        other = "tool" if role == "user" else "user"
        take = shortfall[role]
        if take > len(pools[other]):
            raise RuntimeError("control pools cannot supply exact registered columns")
        chosen.extend(pools[other][:take])
        pools[other] = pools[other][take:]
    if len(set(chosen)) != sum(needed.values()):
        raise AssertionError("matched control is not exact or disjoint")
    chosen_set = set(chosen)
    if tokenizer is not None and context is not None:
        context_ids = list(tokenizer.encode(context).ids)
        entries = []
        entry_spans = [
            span
            for role in ("user", "tool")
            for span in _columns_to_spans(
                [column for column in chosen if column_roles[column] == role]
            )
        ]
        for start, end in sorted(entry_spans):
            source = next(
                row for row in candidates if start in _candidate_columns(row, low, high)
            )
            row = dict(source)
            row.update(
                {
                    "role": column_roles[start],
                    "text": tokenizer.decode(context_ids[start:end]),
                    "span": [start, end],
                    "pinned_columns": list(range(start, end)),
                }
            )
            entries.append(row)
    else:
        entries = [
            dict(row)
            for row in candidates
            if chosen_set.intersection(_candidate_columns(row, low, high))
        ]
    return {
        "pins": _columns_to_spans(chosen),
        "entries": entries,
        "role_counts": needed,
        "role_shortfall": shortfall,
    }


def same_role_control_spans(
    candidates: Sequence[Mapping],
    kept: Sequence[Mapping],
    evict_range: tuple[int, int],
    *,
    seed: int,
) -> tuple[list[tuple[int, int]], dict[str, int]]:
    """Compatibility wrapper for the v3 matched control."""
    result = build_matched_control(candidates, kept, evict_range, seed=seed)
    return result["pins"], result["role_counts"]


def recency_pinned_plan(
    candidates: Sequence[Mapping],
    classifier_columns: int,
    evict_range: tuple[int, int],
) -> dict:
    """Keep all user columns and newest tool columns up to classifier dose."""
    low, high = evict_range
    user = sorted(
        {
            column
            for row in candidates
            if row["role"] == "user"
            for column in range(
                max(low, int(row.get("role_span", row["span"])[0])),
                min(high, int(row.get("role_span", row["span"])[1])),
            )
        }
    )
    tool_rows = sorted(
        (row for row in candidates if row["role"] == "tool"),
        key=lambda row: (int(row["turn"]), int(row["span"][0])),
        reverse=True,
    )
    tool_budget = max(0, classifier_columns - len(user))
    tool: list[int] = []
    entries = [dict(row) for row in candidates if row["role"] == "user"]
    for row in tool_rows:
        columns = _candidate_columns(row, low, high)
        if len(tool) + len(columns) > tool_budget:
            continue
        tool.extend(columns)
        entries.append(dict(row))
    return {"pins": _columns_to_spans([*user, *tool]), "entries": entries}


def tool_swap_plan(
    candidates: Sequence[Mapping],
    kept: Sequence[Mapping],
    evict_range: tuple[int, int],
    *,
    seed: int,
    tokenizer=None,
    context: str | None = None,
) -> dict:
    """Retain selected users and replace selected tools by matched tools."""
    users = [dict(row) for row in kept if row["role"] == "user"]
    tools = [dict(row) for row in kept if row["role"] == "tool"]
    matched = build_matched_control(
        candidates,
        tools,
        evict_range,
        seed=seed,
        tokenizer=tokenizer,
        context=context,
    )
    user_columns = [column for row in users for column in row["pinned_columns"]]
    entries = users + [row for row in matched["entries"] if row["role"] == "tool"]
    return {
        "pins": _columns_to_spans([*user_columns, *_flatten_spans(matched["pins"])]),
        "entries": entries,
        "role_shortfall": matched["role_shortfall"],
    }


def _flatten_spans(spans: Sequence[tuple[int, int]]) -> list[int]:
    return [column for start, end in spans for column in range(start, end)]


def recent_user_spans(
    candidates: Sequence[Mapping],
    evict_range: tuple[int, int],
    budget: int,
) -> list[tuple[int, int]]:
    """Take prior-user columns only, newest first, up to classifier dose."""
    low, high = evict_range
    columns = sorted(
        {
            column
            for row in candidates
            if row["role"] == "user"
            for column in range(
                max(low, int(row.get("role_span", row["span"])[0])),
                min(high, int(row.get("role_span", row["span"])[1])),
            )
        }
    )
    return _columns_to_spans(columns[-budget:] if budget > 0 else [])


def _canonical_json(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def build_cohorts(cases: list[dict], seed: int) -> dict:
    """Take 8 dev and 16 sealed IDs per category, independent of input order."""
    grouped = {category: [] for category in CATEGORIES}
    for case in cases:
        grouped[case["category"]].append(case["id"])
    dev: list[str] = []
    sealed: list[str] = []
    for category in CATEGORIES:
        ids = sorted(grouped[category])
        if len(ids) < 24:
            raise ValueError(f"{category} has {len(ids)} cases; 24 required")
        random.Random(f"{seed}:{category}").shuffle(ids)
        dev.extend(ids[:8])
        sealed.extend(ids[8:24])
    body = {"seed": seed, "dev": dev, "sealed": sealed}
    return {**body, "sha256": hashlib.sha256(_canonical_json(body)).hexdigest()}


@dataclass(frozen=True)
class ParsedToolCall:
    raw: str
    call: dict[str, Any] | None
    valid: bool
    error: str | None = None


def parse_tool_calls(text: str) -> list[ParsedToolCall]:
    """Parse every Qwen ``<tool_call>`` block without hiding malformed calls."""
    parsed = []
    for match in TOOL_PATTERN.finditer(text):
        raw = match.group(1)
        try:
            call = json.loads(raw)
            valid = (
                isinstance(call, dict)
                and isinstance(call.get("name"), str)
                and bool(call["name"])
                and isinstance(call.get("arguments"), dict)
            )
            if not valid:
                raise ValueError("call requires string name and object arguments")
            parsed.append(ParsedToolCall(raw, call, True))
        except (json.JSONDecodeError, ValueError) as exc:
            parsed.append(ParsedToolCall(raw, None, False, str(exc)))
    return parsed


def call_to_python(call: dict[str, Any]) -> str:
    """Convert Qwen JSON calls to the call-string form consumed by BFCL."""
    name = call["name"].rsplit(".", 1)[-1]
    if not name.isidentifier():
        raise ValueError(f"invalid function name: {name!r}")
    args = call["arguments"]
    if not all(isinstance(key, str) and key.isidentifier() for key in args):
        raise ValueError("argument keys must be Python identifiers")
    return f"{name}({', '.join(f'{key}={value!r}' for key, value in args.items())})"


def control_echo(
    tokenizer, prior_user_texts: list[str], target_tokens: int, seed: int
) -> tuple[str, int]:
    """Deterministically rotate/repeat prior-user tokens to an exact token budget."""
    if target_tokens < 0:
        raise ValueError("target_tokens must be non-negative")
    pool = [token for text in prior_user_texts for token in tokenizer.encode(text).ids]
    if target_tokens and not pool:
        raise ValueError("cannot sample control without a prior user turn")
    if not target_tokens:
        return "", 0
    start = seed % len(pool)
    chosen = [pool[(start + index) % len(pool)] for index in range(target_tokens)]
    text = tokenizer.decode(chosen)
    encoded = tokenizer.encode(text).ids
    if len(encoded) != target_tokens:
        raise ValueError("tokenizer does not round-trip the sampled control span")
    return text, len(encoded)


def echo_copy_flag(response_ids: list[int], echo_ids: list[int], run: int = 8) -> bool:
    """Whether a generated response copies a contiguous token run from its echo."""
    if run <= 0:
        raise ValueError("run must be positive")
    if len(response_ids) < run or len(echo_ids) < run:
        return False
    echo_runs = {tuple(echo_ids[i : i + run]) for i in range(len(echo_ids) - run + 1)}
    return any(
        tuple(response_ids[i : i + run]) in echo_runs
        for i in range(len(response_ids) - run + 1)
    )


def ensure_split_allowed(split: str) -> None:
    if split == "sealed" and os.environ.get("STENCIL_SEALED_RUN") != "1":
        raise PermissionError(
            "sealed split requires orchestrator-set STENCIL_SEALED_RUN=1"
        )
    if split not in {"dev", "sealed"}:
        raise ValueError(f"unknown split: {split}")


def atomic_json(path: str | Path, value: object) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, default=str) + "\n"
    )
    temporary.replace(path)


def load_jsonl(path: str | Path) -> list[dict]:
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line]


def load_function_docs(case: dict, docs_dir: str | Path) -> list[dict]:
    docs = []
    for class_name in case["involved_classes"]:
        docs.extend(load_jsonl(Path(docs_dir) / FUNCTION_DOCS[class_name]))
    return docs


def prepare_case(case: dict, docs_dir: str | Path) -> dict:
    """Attach schemas and resolve BFCL missing-function holdouts."""
    prepared = json.loads(json.dumps(case))
    prepared["function"] = load_function_docs(prepared, docs_dir)
    holdouts = prepared.get("missed_function", {})
    for turn, names in list(holdouts.items()):
        found = []
        for name in names:
            index = next(
                i for i, doc in enumerate(prepared["function"]) if doc["name"] == name
            )
            found.append(prepared["function"].pop(index))
        holdouts[turn] = found
    return prepared


def execute_call_strings(
    calls: list[str], case: dict, run_name: str
) -> tuple[list[str], dict]:
    """Execute through BFCL's vendored stateful environments."""
    _enable_vendor()
    from bfcl_eval.eval_checker.multi_turn_eval.multi_turn_utils import (
        execute_multi_turn_func_call,
    )

    return execute_multi_turn_func_call(
        calls,
        case["initial_config"],
        case["involved_classes"],
        run_name,
        case["id"],
        long_context="long_context" in case["id"],
        is_evaL_run=False,
    )


def score_case(
    case: dict,
    decoded_turns: list[list[list[str]]],
    ground_truth: list[list[str]],
    run_name: str = "stencil",
) -> dict:
    """Apply BFCL's executable/state checker and irrelevance checker."""
    _enable_vendor()
    from bfcl_eval.eval_checker.multi_turn_eval.multi_turn_checker import (
        multi_turn_checker,
        multi_turn_irrelevance_checker,
    )

    result = multi_turn_checker(decoded_turns, ground_truth, case, case["id"], run_name)
    if result["valid"]:
        result = multi_turn_irrelevance_checker(decoded_turns, ground_truth)
    return result


def assert_case_record_schema(record: Mapping) -> None:
    """Fail before sealing if a per-case record cannot support every report."""
    required = {"schema", "case_id", "category", "arms", "seconds"}
    missing = required - set(record)
    if missing:
        raise ValueError(f"record fields missing: {sorted(missing)}")
    schema = int(record["schema"])
    if schema not in {2, 3}:
        raise ValueError("record schema is not BFCL LEG A v2/v3")
    if set(record["arms"]) != set(ARMS):
        raise ValueError("record arms do not equal the registered v3 arm set")
    arm_required = {
        "turns",
        "evicted",
        "echo_tokens_added",
        "echo_copy",
        "selector",
        "seconds",
        "final_pass",
        "final_score",
    }
    eviction_required = {
        "evicted",
        "columns_before",
        "columns_after",
        "pinned_columns",
        "evictable_size",
    }
    for name, arm in record["arms"].items():
        if arm_required - set(arm):
            raise ValueError(f"arm {name} schema incomplete")
        for turn in arm["turns"]:
            if eviction_required - set(turn.get("eviction", {})):
                raise ValueError(f"arm {name} turn eviction schema incomplete")
            if not {
                "responses",
                "tool_calls",
                "timeout",
                "truncated",
                "degenerate",
                "pass",
            } <= set(turn):
                raise ValueError(f"arm {name} turn schema incomplete")
            if schema == 3:
                required_v3 = {
                    "budget_used",
                    "echo_tokens",
                    "pin_overflow",
                }
                if required_v3 - set(turn["eviction"]):
                    raise ValueError(f"arm {name} turn v3 eviction schema incomplete")


def _rate(values: Sequence[bool]) -> dict:
    passed = sum(bool(value) for value in values)
    n = len(values)
    return {"n": n, "passed": passed, "rate": passed / n if n else None}


def _arm_summary(records: Sequence[Mapping], arm: str) -> dict:
    arm_rows = [record["arms"][arm] for record in records]
    turns = [turn for row in arm_rows for turn in row["turns"]]
    calls = [call for turn in turns for call in turn["tool_calls"]]
    columns = {}
    for output, field in (
        ("before", "columns_before"),
        ("after", "columns_after"),
        ("pinned", "pinned_columns"),
        ("evictable", "evictable_size"),
    ):
        values = [int(turn["eviction"][field]) for turn in turns]
        columns[output] = {
            "n": len(values),
            "mean": sum(values) / len(values) if values else None,
        }
    return {
        "final_pass": _rate([bool(row["final_pass"]) for row in arm_rows]),
        "per_turn_pass": _rate([bool(turn["pass"]) for turn in turns]),
        "tool_call_validity": (
            sum(bool(call["valid"]) for call in calls) / len(calls) if calls else None
        ),
        "tool_calls": len(calls),
        "echo_copy_rate": (
            sum(bool(row["echo_copy"]) for row in arm_rows) / len(arm_rows)
            if arm_rows
            else None
        ),
        "echo_tokens": sum(int(row.get("echo_tokens_added", 0)) for row in arm_rows),
        "repeated_history_calls": sum(
            int(row.get("repeated_history_calls", 0)) for row in arm_rows
        ),
        "pin_overflow_events": sum(
            int(turn.get("eviction", {}).get("pin_overflow", 0)) > 0 for turn in turns
        ),
        "columns": columns,
    }


def _cohort_summary(records: Sequence[Mapping]) -> dict:
    return {
        "cases": len(records),
        "arms": {arm: _arm_summary(records, arm) for arm in ARMS},
    }


def _one_sided_cluster_p(values: Sequence[float]) -> float:
    from stencil.stats import CONTINUITY_POINTS, t_cdf

    count = len(values)
    if count < 2:
        return 1.0
    raw_mean = sum(values) / count
    mean = raw_mean - CONTINUITY_POINTS / count
    variance = sum((value - raw_mean) ** 2 for value in values) / (count - 1)
    if variance == 0.0:
        return 0.0 if mean > 0 else 1.0
    statistic = mean / math.sqrt(variance / count)
    return 1.0 - t_cdf(statistic, count - 1)


def _contrast(values: Sequence[float]) -> dict:
    bound = clustered_lower_bound(values) if len(values) >= 2 else None
    return {
        "clusters": len(values),
        "mean_points": sum(values) / len(values) if values else None,
        "lower_bound": None if bound is None else bound["lower_bound"],
        "bound": bound,
        "p_one_sided": _one_sided_cluster_p(values),
    }


def _holm(contrasts: Mapping[str, Mapping], alpha: float = 0.05) -> dict:
    ordered = sorted(contrasts, key=lambda name: (contrasts[name]["p_one_sided"], name))
    passed_so_far = True
    result = {}
    for rank, name in enumerate(ordered):
        cutoff = alpha / (len(ordered) - rank)
        passed = passed_so_far and contrasts[name]["p_one_sided"] <= cutoff
        result[name] = {
            "p_one_sided": contrasts[name]["p_one_sided"],
            "cutoff": cutoff,
            "passed": passed,
        }
        passed_so_far = passed
    return result


def _primary_turns(records: Sequence[Mapping]) -> dict[str, list[int]]:
    """Case -> semantic turn indices where the base pressure trigger fired."""
    return {
        str(record["case_id"]): [
            int(turn["turn"])
            for turn in record["arms"]["base"]["turns"]
            if bool(turn["eviction"]["evicted"])
        ]
        for record in records
    }


def _turn_by_index(record: Mapping, arm: str, turn_index: int) -> Mapping:
    return next(
        turn for turn in record["arms"][arm]["turns"] if int(turn["turn"]) == turn_index
    )


def _safety(records: Sequence[Mapping], primary: Mapping[str, Sequence[int]]) -> dict:
    counts = {}
    for arm in ARMS:
        turns = [
            _turn_by_index(record, arm, turn_index)
            for record in records
            for turn_index in primary[str(record["case_id"])]
        ]
        counts[arm] = {
            "timeouts": sum(bool(turn["timeout"]) for turn in turns),
            "truncated": sum(bool(turn["truncated"]) for turn in turns),
            "degenerate": sum(bool(turn["degenerate"]) for turn in turns),
            "invalid": sum(
                any(not bool(call["valid"]) for call in turn["tool_calls"])
                for turn in turns
            ),
        }
    full = counts["full"]
    checks = {}
    for arm, row in counts.items():
        checks[arm] = {
            "timeouts_registered": (
                row["timeouts"] <= 1 if full["timeouts"] == 0 else row["timeouts"] == 0
            ),
            "truncated_le_full_plus_one": row["truncated"] <= full["truncated"] + 1,
            "degenerate_le_full": (
                row["degenerate"] <= 1
                if full["degenerate"] == 0
                else row["degenerate"] <= full["degenerate"]
            ),
            "invalid_le_full_plus_one": row["invalid"] <= full["invalid"] + 1,
        }
        checks[arm]["passed"] = all(checks[arm].values())
    return {
        "integer_clause": (
            "timeouts=0; truncated<=full+1; degenerate<=full; "
            "invalid<=full+1 (invalid is per turn)"
        ),
        "counts": counts,
        "checks": checks,
        "vacuity_guard": {
            event: "full=0; judged <=1"
            for event, field in (
                ("timeouts", "timeouts"),
                ("truncated", "truncated"),
                ("degenerate", "degenerate"),
                ("invalid", "invalid"),
            )
            if full[field] == 0
        },
        "intact": all(row["passed"] for row in checks.values()),
    }


def summarize_records(records: Sequence[Mapping]) -> dict:
    """Report v3 teacher-forced evicting-turn clustered contrasts."""
    for record in records:
        assert_case_record_schema(record)
    categories = {
        category: _cohort_summary(
            [record for record in records if record["category"] == category]
        )
        for category in CATEGORIES
    }
    primary_records = list(records)
    primary_indices = _primary_turns(primary_records)
    primary_turn_count = sum(map(len, primary_indices.values()))
    primary = {
        "unit": "teacher_forced_evicting_turn",
        "clusters": sum(bool(rows) for rows in primary_indices.values()),
        "turns": primary_turn_count,
        "arms": {
            arm: {
                "per_turn_pass": _rate(
                    [
                        bool(_turn_by_index(record, arm, turn_index)["pass"])
                        for record in primary_records
                        for turn_index in primary_indices[str(record["case_id"])]
                    ]
                )
            }
            for arm in ARMS
        },
    }

    def cluster_values(left: str, right: str, transform=None, *, a3=False):
        values = []
        excluded = 0
        for record in primary_records:
            rows = []
            for turn_index in primary_indices[str(record["case_id"])]:
                left_turn = _turn_by_index(record, left, turn_index)
                right_turn = _turn_by_index(record, right, turn_index)
                if (
                    a3
                    and int(
                        _turn_by_index(record, "full", turn_index).get(
                            "prompt_positions", 0
                        )
                    )
                    > 40960
                ):
                    excluded += 1
                    continue
                value = float(left_turn["pass"]) - float(right_turn["pass"])
                rows.append(
                    transform(record, turn_index, value) if transform else value
                )
            if rows:
                values.append(100.0 * sum(rows) / len(rows))
        return values, excluded

    a1, _ = cluster_values("clf_pinned_echo", "clf_control")
    a2, _ = cluster_values("clf_pinned_echo", "recency_pinned")
    a4, _ = cluster_values("clf_pinned_echo", "tool_swap_echo")
    ceiling, excluded = cluster_values("full", "base", a3=True)
    ceiling_positive = bool(ceiling) and sum(ceiling) / len(ceiling) > 0

    def a3_transform(record, turn_index, echo_base):
        full = float(_turn_by_index(record, "full", turn_index)["pass"])
        base = float(_turn_by_index(record, "base", turn_index)["pass"])
        return echo_base - 0.5 * (full - base)

    a3, _ = cluster_values("clf_pinned_echo", "base", a3_transform, a3=True)
    if not ceiling_positive:
        a3 = []
    values = {
        "a1_echo_minus_control": a1,
        "a2_echo_minus_recency": a2,
        "a3_half_gap_recovery": a3,
    }
    contrasts = {name: _contrast(rows) for name, rows in values.items()}
    holm = _holm(contrasts)
    safety = _safety(primary_records, primary_indices)
    a4_contrast = _contrast(a4)
    return {
        "schema": 3,
        "cases": len(records),
        "categories": categories,
        "primary": primary,
        "contrasts": contrasts,
        "holm": holm,
        "a3": {
            "eligible": ceiling_positive,
            "full_minus_base": _contrast(ceiling),
            "excluded_over_40960": excluded,
            "status": None
            if ceiling_positive
            else "full is not a ceiling; A3 uninformative",
        },
        "a4_echo_minus_tool_swap": {
            **a4_contrast,
            "alpha": 0.05,
            "passed": safety["intact"] and a4_contrast["p_one_sided"] <= 0.05,
        },
        "reported": {
            "recency_minus_role": _contrast(
                cluster_values("recency_pinned", "role_pinned")[0]
            ),
            "non_evicting_turns": sum(
                not bool(turn["eviction"]["evicted"])
                for record in records
                for turn in record["arms"]["base"]["turns"]
            ),
        },
        "safety": safety,
        "registered_contrasts_pass": safety["intact"]
        and all(row["passed"] for row in holm.values()),
        "seconds_total": sum(float(record["seconds"]) for record in records),
        "seconds_per_case": (
            sum(float(record["seconds"]) for record in records) / len(records)
            if records
            else None
        ),
    }


def _enable_vendor() -> None:
    vendor = str(Path(__file__).resolve().parents[2] / "vendor")
    if vendor not in sys.path:
        sys.path.insert(0, vendor)
