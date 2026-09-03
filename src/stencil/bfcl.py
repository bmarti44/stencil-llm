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
    "role_pinned",
    "full",
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


def context_layout(tokenizer, context: str) -> dict:
    """Locate the protected system/tools prefix and prior-history range."""
    current_marker = context.rfind("<|im_start|>user\n")
    if current_marker < 0:
        raise ValueError("current user marker missing")
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


def _tool_line_spans(text: str, cap: int = 40) -> list[tuple[int, int]]:
    lines = []
    cursor = 0
    for line_index, piece in enumerate(text.splitlines(keepends=True)):
        raw = piece.rstrip("\r\n")
        end = cursor + len(raw)
        if raw:
            lines.append((cursor, end, line_index, raw))
        cursor += len(piece)
    if text and not text.splitlines(keepends=True):
        lines.append((0, len(text), 0, text))
    if len(lines) > cap:
        lines.sort(key=lambda row: (-len(row[3]), row[2]))
        lines = lines[:cap]
    return [(start, end) for start, end, _, _ in lines]


def select_history_spans(
    tokenizer,
    context: str,
    messages: Sequence[Mapping],
    scorer,
    *,
    threshold: float = 0.5,
) -> tuple[list[dict], list[dict]]:
    """Score each prior user sentence and capped tool line exactly once."""
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
        local_spans = (
            split_sentence_spans(location["content"])
            if role == "user"
            else _tool_line_spans(location["content"])
        )
        role_span = _token_span(
            encoding, location["pool_start"], location["pool_end"]
        )
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
    return selected, candidates


def _columns_to_spans(columns: Sequence[int]) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    for column in sorted(set(columns)):
        if spans and spans[-1][1] == column:
            spans[-1] = (spans[-1][0], column + 1)
        else:
            spans.append((column, column + 1))
    return spans


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
    chosen: set[int] = set()
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
        available = [
            column
            for column in range(
                max(low, int(candidate["span"][0])),
                min(high, int(candidate["span"][1])),
            )
            if column not in chosen
        ]
        take = available[: max(0, budget - len(chosen))]
        if take:
            row = dict(candidate)
            row["pinned_columns"] = take
            kept.append(row)
            chosen.update(take)
        if len(chosen) == budget:
            break
    return kept, _columns_to_spans(chosen), budget


def same_role_control_spans(
    candidates: Sequence[Mapping],
    kept: Sequence[Mapping],
    evict_range: tuple[int, int],
    *,
    seed: int,
) -> tuple[list[tuple[int, int]], dict[str, int]]:
    """Match selected user/tool columns from each role's unselected pool."""
    low, high = evict_range
    pinned = {
        int(column) for row in kept for column in row.get("pinned_columns", [])
    }
    counts = {
        role: sum(
            len(row.get("pinned_columns", []))
            for row in kept
            if row["role"] == role
        )
        for role in ("user", "tool")
    }
    chosen = []
    for role_index, role in enumerate(("user", "tool")):
        pool = sorted(
            {
                column
                for row in candidates
                if row["role"] == role
                for column in range(
                    max(low, int(row.get("role_span", row["span"])[0])),
                    min(high, int(row.get("role_span", row["span"])[1])),
                )
                if column not in pinned
            }
        )
        needed = counts[role]
        if len(pool) < needed:
            raise RuntimeError(
                f"same-role {role} pool has {len(pool)} columns; {needed} required"
            )
        if pool:
            start = (seed + role_index * 104729) % len(pool)
            rotated = pool[start:] + pool[:start]
            chosen.extend(rotated[:needed])
    if len(set(chosen)) != sum(counts.values()):
        raise AssertionError("same-role control columns overlap")
    return _columns_to_spans(chosen), counts


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
    if int(record["schema"]) != 2:
        raise ValueError("record schema is not BFCL LEG A v2")
    if set(record["arms"]) != set(ARMS):
        raise ValueError("record arms do not equal the registered six-arm set")
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


def _safety(records: Sequence[Mapping]) -> dict:
    counts = {}
    for arm in ARMS:
        turns = [turn for record in records for turn in record["arms"][arm]["turns"]]
        counts[arm] = {
            "timeouts": sum(bool(turn["timeout"]) for turn in turns),
            "truncated": sum(bool(turn["truncated"]) for turn in turns),
            "degenerate": sum(bool(turn["degenerate"]) for turn in turns),
            "invalid_tool_calls": sum(
                not bool(call["valid"]) for turn in turns for call in turn["tool_calls"]
            ),
        }
    full = counts["full"]
    checks = {}
    for arm, row in counts.items():
        checks[arm] = {
            "timeouts_zero": row["timeouts"] == 0,
            "truncated_le_full_plus_one": row["truncated"] <= full["truncated"] + 1,
            "degenerate_le_full": row["degenerate"] <= full["degenerate"],
            "invalid_le_full_plus_one": (
                row["invalid_tool_calls"] <= full["invalid_tool_calls"] + 1
            ),
        }
        checks[arm]["passed"] = all(checks[arm].values())
    return {
        "integer_clause": (
            "timeouts=0; truncated<=full+1; degenerate<=full; "
            "invalid_tool_calls<=full+1"
        ),
        "counts": counts,
        "checks": checks,
        "intact": all(row["passed"] for row in checks.values()),
    }


def summarize_records(records: Sequence[Mapping]) -> dict:
    """Report all strata and registered long-context clustered contrasts."""
    for record in records:
        assert_case_record_schema(record)
    categories = {
        category: _cohort_summary(
            [record for record in records if record["category"] == category]
        )
        for category in CATEGORIES
    }
    primary_records = [
        record for record in records if record["category"] == "long_context"
    ]
    primary = {
        "category": "long_context",
        **_cohort_summary(primary_records),
    }
    values = {
        "a1_echo_minus_control": [
            100.0
            * (
                float(record["arms"]["clf_pinned_echo"]["final_pass"])
                - float(record["arms"]["clf_control"]["final_pass"])
            )
            for record in primary_records
        ],
        "a2_echo_minus_role": [
            100.0
            * (
                float(record["arms"]["clf_pinned_echo"]["final_pass"])
                - float(record["arms"]["role_pinned"]["final_pass"])
            )
            for record in primary_records
        ],
        "a3_half_gap_recovery": [
            100.0
            * (
                float(record["arms"]["clf_pinned_echo"]["final_pass"])
                - float(record["arms"]["base"]["final_pass"])
                - 0.5
                * (
                    float(record["arms"]["full"]["final_pass"])
                    - float(record["arms"]["base"]["final_pass"])
                )
            )
            for record in primary_records
        ],
    }
    contrasts = {name: _contrast(rows) for name, rows in values.items()}
    holm = _holm(contrasts)
    safety = _safety(primary_records)
    return {
        "schema": 2,
        "cases": len(records),
        "categories": categories,
        "primary": primary,
        "contrasts": contrasts,
        "holm": holm,
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
