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
REDUCED_ARMS = (
    "base",
    "clf_pinned_echo",
    "clf_control",
    "recency_pinned",
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
    special_token_ids: set[int] | None = None,
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
        pieces = split_sentence_spans(location["content"])
        if role == "tool":
            pieces = [
                sentence
                for line in _tool_line_spans(location["content"])
                for sentence in split_sentence_spans(
                    location["content"][line[0] : line[1]]
                )
                for sentence in [(line[0] + sentence[0], line[0] + sentence[1])]
            ]
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
    if any(int(row["message_index"]) >= current_user_index for row in candidates):
        raise AssertionError(
            "candidate source is not earlier than current user message"
        )
    if special_token_ids is None:
        decoder = (
            tokenizer.get_added_tokens_decoder()
            if hasattr(tokenizer, "get_added_tokens_decoder")
            else {}
        )
        special_token_ids = {int(token_id) for token_id in decoder}

    def unsafe(row: Mapping) -> bool:
        return any(marker in str(row["text"]) for marker in CONTROL_MARKERS) or bool(
            set(tokenizer.encode(str(row["text"])).ids) & special_token_ids
        )

    dropped = sum(unsafe(row) for row in candidates)
    candidates = [row for row in candidates if not unsafe(row)]
    scorer_before = int(getattr(scorer, "scorer_truncated_candidates", 0))
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
    truncated = int(getattr(scorer, "scorer_truncated_candidates", scorer_before))
    for row in candidates:
        row["scorer_truncated_candidates"] = max(0, truncated - scorer_before)
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
        + "\n".join(
            f"- {row['role']}: {json.dumps(str(row['text']), ensure_ascii=False)}"
            for row in entries
        )
    )


def _candidate_columns(row: Mapping, low: int, high: int) -> list[int]:
    span = row["span"]
    return list(range(max(low, int(span[0])), min(high, int(span[1]))))


def _row_columns(row: Mapping, low: int, high: int) -> list[int]:
    return _candidate_columns(row, low, high)


def _decode_row(
    row: Mapping, columns: Sequence[int], tokenizer=None, context=None
) -> dict:
    out = dict(row)
    out["span"] = [min(columns), max(columns) + 1]
    out["pinned_columns"] = list(columns)
    if tokenizer is not None and context is not None:
        out["text"] = tokenizer.decode(
            list(tokenizer.encode(context).ids)[out["span"][0] : out["span"][1]]
        )
    elif len(columns) < int(row["span"][1]) - int(row["span"][0]):
        width = max(1, int(row["span"][1]) - int(row["span"][0]))
        out["text"] = str(row["text"])[
            : max(1, len(str(row["text"])) * len(columns) // width)
        ]
    return out


def clamp_candidate_rows(
    rows: Sequence[Mapping],
    quotas: Mapping[str, int],
    *,
    evict_range: tuple[int, int] | None = None,
    tokenizer=None,
    context: str | None = None,
) -> dict:
    """Admit resources in order, truncating only the final row per role."""
    low, high = evict_range or (-sys.maxsize, sys.maxsize)
    remaining = {role: int(quotas.get(role, 0)) for role in ("user", "tool")}
    entries: list[dict] = []
    closed: set[str] = set()
    for row in rows:
        role = str(row["role"])
        if role in closed or remaining[role] <= 0:
            continue
        columns = _row_columns(row, low, high)
        if not columns:
            continue
        take = min(len(columns), remaining[role])
        entries.append(_decode_row(row, columns[:take], tokenizer, context))
        remaining[role] -= take
        if take < len(columns):
            closed.add(role)
    chosen = [column for row in entries for column in row["pinned_columns"]]
    counts = {
        role: sum(len(row["pinned_columns"]) for row in entries if row["role"] == role)
        for role in ("user", "tool")
    }
    return {
        "pins": _columns_to_spans(chosen),
        "entries": entries,
        "role_counts": counts,
        "match_impossible": any(remaining.values()),
    }


def _resource_match(
    candidates: Sequence[Mapping],
    kept: Sequence[Mapping],
    evict_range: tuple[int, int],
    *,
    seed: int,
    allow_role_fallback: bool,
) -> tuple[list[Mapping], bool, bool]:
    """One-to-one width/age resource matching without reuse or rotation."""
    low, high = evict_range
    selected_ids = {id(row) for row in kept}
    selected_spans = {tuple(row["span"]) for row in kept}
    available = [
        row
        for row in candidates
        if id(row) not in selected_ids and tuple(row["span"]) not in selected_spans
    ]
    rng = random.Random(seed)
    tie = {id(row): rng.random() for row in available}
    matches: list[Mapping] = []
    shortfall = False
    for target in kept:
        width = len(target.get("pinned_columns", _row_columns(target, low, high)))
        same = [
            row
            for row in available
            if row["role"] == target["role"]
            and int(row["turn"]) == int(target["turn"])
            and len(_row_columns(row, low, high)) == width
        ]
        pool = same
        if not pool and allow_role_fallback:
            pool = [
                row
                for row in available
                if row["role"] != target["role"]
                and int(row["turn"]) == int(target["turn"])
                and len(_row_columns(row, low, high)) == width
            ]
            shortfall |= bool(pool)
        if not pool:
            return [], True, shortfall
        choice = min(pool, key=lambda row: (tie[id(row)], int(row["span"][0])))
        matches.append(choice)
        available.remove(choice)
    return matches, False, shortfall


def build_matched_control(
    candidates: Sequence[Mapping],
    kept: Sequence[Mapping],
    evict_range: tuple[int, int],
    *,
    seed: int,
    tokenizer=None,
    context: str | None = None,
) -> dict:
    """Width/age resource-identified control with registered role fallback."""
    low, high = evict_range
    needed = {
        role: sum(
            len(row.get("pinned_columns", [])) for row in kept if row["role"] == role
        )
        for role in ("user", "tool")
    }
    matched, impossible, shortfall = _resource_match(
        candidates, kept, evict_range, seed=seed, allow_role_fallback=True
    )
    if impossible:
        return {
            "pins": [],
            "entries": [],
            "role_counts": {"user": 0, "tool": 0},
            "role_shortfall": needed,
            "control_role_shortfall": shortfall,
            "role_column_deltas": {role: -needed[role] for role in needed},
            "match_impossible": True,
        }
    quotas = {
        role: sum(
            len(_row_columns(row, low, high)) for row in matched if row["role"] == role
        )
        for role in ("user", "tool")
    }
    clamped = clamp_candidate_rows(
        matched,
        quotas,
        evict_range=evict_range,
        tokenizer=tokenizer,
        context=context,
    )
    actual = clamped["role_counts"]
    deltas = {role: actual[role] - needed[role] for role in needed}
    return {
        "pins": clamped["pins"],
        "entries": clamped["entries"],
        "role_counts": needed,
        "role_shortfall": {
            role: max(0, needed[role] - actual[role]) for role in needed
        },
        "control_role_shortfall": shortfall,
        "role_column_deltas": deltas,
        "match_impossible": False,
    }


def same_role_control_spans(
    candidates: Sequence[Mapping],
    kept: Sequence[Mapping],
    evict_range: tuple[int, int],
    *,
    seed: int,
) -> tuple[list[tuple[int, int]], dict[str, int]]:
    """Compatibility wrapper retaining the v2 column-dose API."""
    low, high = evict_range
    selected = {column for row in kept for column in row.get("pinned_columns", [])}
    counts = {
        role: sum(
            len(row.get("pinned_columns", [])) for row in kept if row["role"] == role
        )
        for role in ("user", "tool")
    }
    chosen = []
    rng = random.Random(seed)
    for role in ("user", "tool"):
        pool = sorted(
            {
                column
                for row in candidates
                if row["role"] == role
                for column in _candidate_columns(row, low, high)
                if column not in selected
            },
            key=lambda column: (rng.random(), column),
        )
        if len(pool) < counts[role]:
            raise RuntimeError("same-role control pool cannot supply exact columns")
        chosen.extend(pool[: counts[role]])
    return _columns_to_spans(chosen), counts


def recency_pinned_plan(
    candidates: Sequence[Mapping],
    classifier_columns: int | Mapping[str, int],
    evict_range: tuple[int, int],
    *,
    tokenizer=None,
    context: str | None = None,
) -> dict:
    """Most-recent candidates under exact treatment per-role quotas."""
    if isinstance(classifier_columns, Mapping):
        quotas = {
            role: int(classifier_columns.get(role, 0)) for role in ("user", "tool")
        }
    else:  # compatibility for v3 callers: allocate dose user-first, then tool
        low, high = evict_range
        user_available = sum(
            len(_candidate_columns(row, low, high))
            for row in candidates
            if row["role"] == "user"
        )
        quotas = {
            "user": min(int(classifier_columns), user_available),
            "tool": max(0, int(classifier_columns) - user_available),
        }
    ordered = sorted(
        candidates,
        key=lambda row: (
            -int(row["turn"]),
            -int(row.get("message_index", row["span"][0])),
            -int(row["span"][0]),
        ),
    )
    return clamp_candidate_rows(
        ordered,
        quotas,
        evict_range=evict_range,
        tokenizer=tokenizer,
        context=context,
    )


def tool_swap_plan(
    candidates: Sequence[Mapping],
    kept: Sequence[Mapping],
    evict_range: tuple[int, int],
    *,
    seed: int,
    tokenizer=None,
    context: str | None = None,
) -> dict:
    """Retain users and replace tools by disjoint same-role width/age matches."""
    tools = [dict(row) for row in kept if row["role"] == "tool"]
    matches, impossible, _ = _resource_match(
        candidates, tools, evict_range, seed=seed, allow_role_fallback=False
    )
    if impossible:
        return {
            "pins": _columns_to_spans(
                [
                    column
                    for row in kept
                    if row["role"] == "user"
                    for column in row["pinned_columns"]
                ]
            ),
            "entries": [dict(row) for row in kept if row["role"] == "user"],
            "role_shortfall": {
                "user": 0,
                "tool": sum(len(row["pinned_columns"]) for row in tools),
            },
            "match_impossible": True,
        }
    tool_quota = sum(len(row["pinned_columns"]) for row in tools)
    matched = clamp_candidate_rows(
        matches,
        {"user": 0, "tool": tool_quota},
        evict_range=evict_range,
        tokenizer=tokenizer,
        context=context,
    )
    replacement_iter = iter(matched["entries"])
    entries = [
        dict(row) if row["role"] == "user" else next(replacement_iter) for row in kept
    ]
    columns = [column for row in entries for column in row["pinned_columns"]]
    return {
        "pins": _columns_to_spans(columns),
        "entries": entries,
        "role_shortfall": {"user": 0, "tool": 0},
        "match_impossible": False,
    }


def resolve_pin_overflow(
    entries: Sequence[Mapping],
    *,
    prefix_columns: int,
    turn_columns: int,
    k: int,
    no_echo_turn_columns: int | None = None,
) -> dict:
    """Drop whole lowest-ranked pins, preserving prefix/current-turn columns."""
    total = (
        prefix_columns
        + (turn_columns if no_echo_turn_columns is None else no_echo_turn_columns)
        > k
    )
    kept = [] if total else [dict(row) for row in entries]
    capacity = max(0, k - prefix_columns - turn_columns)
    dropped_columns = 0
    while sum(len(row.get("pinned_columns", [])) for row in kept) > capacity:
        dropped_columns += len(kept[-1].get("pinned_columns", []))
        kept.pop()
    pins = _columns_to_spans(
        [column for row in kept for column in row.get("pinned_columns", [])]
    )
    return {
        "pins": pins,
        "entries": kept,
        "pin_overflow": bool(dropped_columns) and not total,
        "pin_overflow_total": total,
        "dropped_columns": (
            sum(len(row.get("pinned_columns", [])) for row in entries)
            if total
            else dropped_columns
        ),
    }


def exact_sign_flip(values: Sequence[float]) -> dict:
    """Exact one-sided paired sign-flip test, with zeros and upper-tail ties."""
    rows = [float(value) for value in values]
    observed = sum(rows)
    assignments = 1 << len(rows)
    upper = 0
    for mask in range(assignments):
        statistic = sum(
            value if mask & (1 << index) else -value for index, value in enumerate(rows)
        )
        if statistic >= observed - 1e-12:
            upper += 1
    return {
        "k": len(rows),
        "upper_tail": upper,
        "assignments": assignments,
        "p": upper / assignments,
        "grid": f"{upper}/{assignments}",
    }


def position_overflow_result(arm: str, positions: int, limit: int = 40960) -> dict:
    """Registered action when initial or within-turn positions exceed the limit."""
    overflow = positions > limit
    return {
        "position_overflow": overflow,
        "generate": not overflow,
        "pass": None if arm == "full" and overflow else (False if overflow else None),
        "truncated": arm != "full" and overflow,
    }


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


def prior_user_spans(
    tokenizer,
    context: str,
    messages: Sequence[Mapping],
    current_message_index: int,
    evict_range: tuple[int, int],
) -> list[tuple[int, int]]:
    """Return every prior USER message column, independent of candidates."""
    encoding = tokenizer.encode(context)
    low, high = evict_range
    columns = []
    for location in _message_locations(context, messages):
        if (
            location["role"] != "user"
            or location["message_index"] >= current_message_index
        ):
            continue
        span = _token_span(encoding, location["pool_start"], location["pool_end"])
        if span is not None:
            columns.extend(range(max(low, span[0]), min(high, span[1])))
    return _columns_to_spans(columns)


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
    cursor = 0
    while True:
        opened = text.find("<tool_call>", cursor)
        closed = text.find("</tool_call>", cursor)
        if opened < 0 and closed < 0:
            break
        if closed >= 0 and (opened < 0 or closed < opened):
            parsed.append(
                ParsedToolCall("</tool_call>", None, False, "unmatched closing tag")
            )
            cursor = closed + len("</tool_call>")
            continue
        end = text.find("</tool_call>", opened + len("<tool_call>"))
        if end < 0:
            parsed.append(
                ParsedToolCall(
                    text[opened + len("<tool_call>") :],
                    None,
                    False,
                    "unmatched opening tag",
                )
            )
            break
        raw = text[opened + len("<tool_call>") : end].strip()
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
        cursor = end + len("</tool_call>")
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


def assert_case_record_schema(
    record: Mapping,
    *,
    expected_arms: Sequence[str] | None = None,
    run_identity_sha256: str | None = None,
) -> None:
    """Fail before sealing if a per-case record cannot support every report."""
    required = {"schema", "case_id", "category", "arms", "seconds"}
    missing = required - set(record)
    if missing:
        raise ValueError(f"record fields missing: {sorted(missing)}")
    schema = int(record["schema"])
    if schema not in {2, 3, 4, 5}:
        raise ValueError("record schema is not BFCL LEG A v2/v3/v4/v5")
    if schema >= 5 and (
        not isinstance(record.get("run_identity_sha256"), str)
        or len(record["run_identity_sha256"]) != 64
    ):
        raise ValueError("record schema v5 requires the meta run identity digest")
    record_arms = set(record["arms"])
    if record_arms != set(ARMS) and record_arms != set(REDUCED_ARMS):
        raise ValueError("record arms do not equal a registered v7 arm set")
    if expected_arms is not None and list(record["arms"]) != list(expected_arms):
        raise ValueError("record arms do not equal active meta arms")
    if (
        run_identity_sha256 is not None
        and record.get("run_identity_sha256") != run_identity_sha256
    ):
        raise ValueError("record run identity does not equal active meta digest")
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
            if schema >= 4:
                required_v4 = {
                    "budget_used",
                    "echo_tokens",
                    "pin_overflow",
                    "pin_overflow_total",
                    "match_impossible",
                    "echo_token_delta",
                }
                if required_v4 - set(turn["eviction"]):
                    raise ValueError(f"arm {name} turn v4 eviction schema incomplete")
                if {"position_overflow", "repeated_call", "chat_control_echo"} - set(
                    turn
                ):
                    raise ValueError(f"arm {name} turn v4 safety schema incomplete")


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
    selectors = [row.get("selector", {}) for row in arm_rows]
    selector_turns = [
        turn for selector in selectors for turn in selector.get("turns", [])
    ]
    role_deltas = {
        role: sum(
            int(turn.get("eviction", {}).get("role_column_deltas", {}).get(role, 0))
            for turn in turns
        )
        for role in ("user", "tool")
    }
    return {
        "final_pass": _rate(
            [
                bool(row["final_pass"])
                for row in arm_rows
                if arm != "full" or not bool(row.get("position_overflow"))
            ]
        ),
        "per_turn_pass": _rate(
            [bool(turn["pass"]) for turn in turns if turn["pass"] is not None]
        ),
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
        "pin_overflow_total": sum(
            bool(turn.get("eviction", {}).get("pin_overflow_total")) for turn in turns
        ),
        "position_overflow": sum(bool(turn.get("position_overflow")) for turn in turns),
        "control_role_shortfall": sum(
            bool(turn.get("eviction", {}).get("control_role_shortfall"))
            for turn in turns
        ),
        "match_impossible": sum(
            bool(turn.get("eviction", {}).get("match_impossible")) for turn in turns
        ),
        "echo_token_deltas": [
            int(turn.get("eviction", {}).get("echo_token_delta", 0)) for turn in turns
        ],
        "scorer_truncated_candidates": sum(
            int(turn.get("scorer_truncated_candidates", 0)) for turn in selector_turns
        ),
        "echo_dropped_control_tokens": sum(
            int(turn.get("echo_dropped_control_tokens", 0)) for turn in selector_turns
        ),
        "pin_overflow_dropped_columns": sum(
            int(turn.get("eviction", {}).get("pin_overflow_dropped_columns", 0))
            for turn in turns
        ),
        "role_column_deltas": role_deltas,
        "budget_used": sum(
            int(turn.get("eviction", {}).get("budget_used", 0)) for turn in turns
        ),
        "columns": columns,
    }


def _cohort_summary(records: Sequence[Mapping]) -> dict:
    arms = [arm for arm in ARMS if all(arm in record["arms"] for record in records)]
    return {
        "cases": len(records),
        "arms": {arm: _arm_summary(records, arm) for arm in arms},
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
    exact = exact_sign_flip(values)
    return {
        "clusters": len(values),
        "k": len(values),
        "mean_points": sum(values) / len(values) if values else None,
        "lower_bound": None if bound is None else bound["lower_bound"],
        "bound": bound,
        "p_one_sided": exact["p"],
        "p_grid": exact["grid"],
        "sign_flip": exact,
        "descriptive_clustered_p": _one_sided_cluster_p(values),
        "status": "eligible" if len(values) >= 6 else "uninformative",
    }


def _holm(contrasts: Mapping[str, Mapping], alpha: float = 0.05) -> dict:
    eligible = {
        name: row for name, row in contrasts.items() if row.get("status") == "eligible"
    }
    ordered = sorted(eligible, key=lambda name: (eligible[name]["p_one_sided"], name))
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
    for name in contrasts:
        if name not in result:
            result[name] = {
                "p_one_sided": contrasts[name]["p_one_sided"],
                "cutoff": None,
                "passed": False,
                "status": "uninformative",
            }
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
    available_arms = [
        arm for arm in ARMS if all(arm in record["arms"] for record in records)
    ]
    for arm in available_arms:
        cases = [
            [
                _turn_by_index(record, arm, turn_index)
                for turn_index in primary[str(record["case_id"])]
            ]
            for record in records
            if primary[str(record["case_id"])]
        ]
        counts[arm] = {
            "timeouts": sum(
                any(bool(turn["timeout"]) for turn in turns) for turns in cases
            ),
            "truncated": sum(
                any(bool(turn["truncated"]) for turn in turns) for turns in cases
            ),
            "degenerate": sum(
                any(bool(turn["degenerate"]) for turn in turns) for turns in cases
            ),
            "invalid": sum(
                any(
                    any(not bool(call["valid"]) for call in turn["tool_calls"])
                    for turn in turns
                )
                for turns in cases
            ),
            "repeated_call": sum(
                any(bool(turn.get("repeated_call")) for turn in turns)
                for turns in cases
            ),
            "chat_control_echo": sum(
                any(bool(turn.get("chat_control_echo")) for turn in turns)
                for turns in cases
            ),
        }
    full = counts["full"]
    checks = {}
    for arm, row in counts.items():
        checks[arm] = {
            "timeouts_zero": row["timeouts"] == 0,
            "truncated_le_full_plus_one": row["truncated"] <= full["truncated"] + 1,
            "degenerate_le_full": (
                row["degenerate"] <= 1
                if full["degenerate"] == 0
                else row["degenerate"] <= full["degenerate"]
            ),
            "invalid_le_full_plus_one": row["invalid"] <= full["invalid"] + 1,
            "repeated_call_le_full_plus_one": row["repeated_call"]
            <= full["repeated_call"] + 1,
            "chat_control_echo_zero": row["chat_control_echo"] == 0,
        }
        checks[arm]["passed"] = all(checks[arm].values())
    return {
        "integer_clause": (
            "timeouts=0; truncated<=full+1; degenerate<=full; "
            "invalid<=full+1; repeated-call<=full+1; chat-control-echo=0 (case-level)"
        ),
        "counts": counts,
        "checks": checks,
        "vacuity_guard": {
            event: "full=0; judged <=1"
            for event, field in (("degenerate", "degenerate"),)
            if full[field] == 0
        },
        "intact": all(row["passed"] for row in checks.values()),
    }


def primary_claim_status(
    *,
    global_k: int,
    a1_informative: bool,
    treatment_safety: bool,
    a1_passed: bool,
    a3_eligible: bool,
    a3_passed: bool,
) -> dict[str, str]:
    """Apply the registered Amendment-2 primary-claim ordering exactly."""
    if global_k < 6:
        return {"status": "INCONCLUSIVE", "reason": "global exposed-cluster k<6"}
    if not a1_informative:
        return {"status": "INCONCLUSIVE", "reason": "A1 is uninformative"}
    if not treatment_safety:
        return {"status": "UNSUPPORTED", "reason": "treatment safety breach"}
    if not a3_eligible:
        if a1_passed:
            return {
                "status": "SUPPORTED_A1_ONLY",
                "reason": "no measurable full-context headroom on this cohort",
            }
        return {"status": "UNSUPPORTED", "reason": "A3 uninformative and A1 failed"}
    if a1_passed and a3_passed:
        return {"status": "SUPPORTED", "reason": "A1 and A3 passed"}
    return {"status": "UNSUPPORTED", "reason": "eligible A1/A3 did not both pass"}


def summarize_records(
    records: Sequence[Mapping],
    *,
    expected_case_ids: Sequence[str] | None = None,
    run_identity_sha256: str | None = None,
    expected_arms: Sequence[str] | None = None,
) -> dict:
    """Report v3 teacher-forced evicting-turn clustered contrasts."""
    if expected_case_ids is not None:
        actual = [str(record.get("case_id")) for record in records]
        if actual != list(expected_case_ids) or len(actual) != len(set(actual)):
            raise ValueError("records do not equal the exact ordered cohort id list")
    for record in records:
        assert_case_record_schema(
            record,
            expected_arms=expected_arms,
            run_identity_sha256=run_identity_sha256,
        )
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
            if all(arm in record["arms"] for record in primary_records)
        },
    }

    def cluster_values(
        left: str, right: str, transform=None, *, a3=False, no_shortfall=False
    ):
        if any(
            left not in record["arms"] or right not in record["arms"]
            for record in primary_records
        ):
            return [], 0
        values = []
        excluded = 0
        for record in primary_records:
            rows = []
            for turn_index in primary_indices[str(record["case_id"])]:
                left_turn = _turn_by_index(record, left, turn_index)
                right_turn = _turn_by_index(record, right, turn_index)
                if no_shortfall and bool(
                    _turn_by_index(record, "clf_control", turn_index)["eviction"].get(
                        "control_role_shortfall"
                    )
                ):
                    continue
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
    a1_no_shortfall, _ = cluster_values(
        "clf_pinned_echo", "clf_control", no_shortfall=True
    )
    a2, _ = cluster_values("clf_pinned_echo", "recency_pinned")
    a4, _ = cluster_values("clf_pinned_echo", "tool_swap_echo")
    ceiling, excluded = cluster_values("full", "base", a3=True)
    ceiling_positive = bool(ceiling) and sum(ceiling) / len(ceiling) > 0

    def a3_transform(record, turn_index, echo_base):
        full = float(_turn_by_index(record, "full", turn_index)["pass"])
        base = float(_turn_by_index(record, "base", turn_index)["pass"])
        return echo_base - 0.5 * (full - base)

    a3, _ = cluster_values("clf_pinned_echo", "base", a3_transform, a3=True)
    values = {
        "a1_echo_minus_control": a1,
        "a2_echo_minus_recency": a2,
        "a3_half_gap_recovery": a3,
    }
    contrasts = {name: _contrast(rows) for name, rows in values.items()}
    a3_eligible = ceiling_positive and len(a3) >= 6
    if not a3_eligible:
        contrasts["a3_half_gap_recovery"]["status"] = "uninformative"
    safety = _safety(primary_records, primary_indices)
    comparator_for = {
        "a1_echo_minus_control": "clf_control",
        "a2_echo_minus_recency": "recency_pinned",
        "a3_half_gap_recovery": "base",
    }
    for name, arm in comparator_for.items():
        unusable = any(
            bool(
                _turn_by_index(record, arm, turn_index)["eviction"].get(
                    "match_impossible"
                )
            )
            or abs(
                int(
                    _turn_by_index(record, arm, turn_index)["eviction"].get(
                        "echo_token_delta", 0
                    )
                )
            )
            > 16
            for record in primary_records
            for turn_index in primary_indices[str(record["case_id"])]
        )
        if unusable or not safety["checks"][arm]["passed"]:
            contrasts[name]["status"] = "uninformative"
    if not safety["checks"]["full"]["passed"]:
        contrasts["a3_half_gap_recovery"]["status"] = "uninformative"
    if not safety["checks"]["clf_pinned_echo"]["passed"]:
        for row in contrasts.values():
            row["status"] = "failed_safety"
    holm = _holm(contrasts)
    a4_contrast = _contrast(a4)
    a4_available = all("tool_swap_echo" in record["arms"] for record in primary_records)
    a4_unusable = not a4_available or any(
        bool(
            _turn_by_index(record, "tool_swap_echo", turn_index)["eviction"].get(
                "match_impossible"
            )
        )
        or abs(
            int(
                _turn_by_index(record, "tool_swap_echo", turn_index)["eviction"].get(
                    "echo_token_delta", 0
                )
            )
        )
        > 16
        for record in primary_records
        for turn_index in primary_indices[str(record["case_id"])]
    )
    if a4_unusable or (
        a4_available and not safety["checks"]["tool_swap_echo"]["passed"]
    ):
        a4_contrast["status"] = "uninformative"
    if not safety["checks"]["clf_pinned_echo"]["passed"]:
        a4_contrast["status"] = "failed_safety"
    a1_passed = bool(holm["a1_echo_minus_control"]["passed"])
    a3_passed = bool(holm["a3_half_gap_recovery"]["passed"])
    a3_claim_eligible = (
        a3_eligible and contrasts["a3_half_gap_recovery"]["status"] == "eligible"
    )
    primary_claim = primary_claim_status(
        global_k=primary["clusters"],
        a1_informative=contrasts["a1_echo_minus_control"]["status"] != "uninformative",
        treatment_safety=safety["checks"]["clf_pinned_echo"]["passed"],
        a1_passed=a1_passed,
        a3_eligible=a3_claim_eligible,
        a3_passed=a3_passed,
    )
    a2_passed = bool(holm["a2_echo_minus_recency"]["passed"])
    a4_safety = safety["checks"]["clf_pinned_echo"]["passed"] and (
        not a4_available or safety["checks"]["tool_swap_echo"]["passed"]
    )
    non_evicting = {
        str(record["case_id"]): [
            int(turn["turn"])
            for turn in record["arms"]["base"]["turns"]
            if not bool(turn["eviction"]["evicted"])
        ]
        for record in records
    }
    non_evicting_count = sum(map(len, non_evicting.values()))

    def non_evicting_arm(arm: str) -> dict:
        arm_passes = []
        differences = []
        for record in records:
            for turn_index in non_evicting[str(record["case_id"])]:
                arm_value = _turn_by_index(record, arm, turn_index)["pass"]
                base_value = _turn_by_index(record, "base", turn_index)["pass"]
                if arm_value is not None:
                    arm_passes.append(bool(arm_value))
                if arm_value is not None and base_value is not None:
                    differences.append(float(arm_value) - float(base_value))
        return {
            "per_turn_pass": _rate(arm_passes),
            "effect_vs_base_points": {
                "n": len(differences),
                "mean": (
                    100.0 * sum(differences) / len(differences) if differences else None
                ),
            },
        }

    return {
        "schema": 5,
        "leg_status": primary_claim["status"],
        "primary_claim": primary_claim,
        "cases": len(records),
        "categories": categories,
        "primary": primary,
        "contrasts": contrasts,
        "holm": holm,
        "a2_claim": {
            **holm["a2_echo_minus_recency"],
            "passed": a2_passed,
            "non_rejection_wording": "no learned-ranking advantage detected",
        },
        "a3": {
            "headroom_gate_passed": ceiling_positive,
            "k": len(a3),
            "eligible": a3_claim_eligible,
            "full_minus_base": _contrast(ceiling),
            "excluded_over_40960": excluded,
            "status": (
                "eligible"
                if a3_claim_eligible
                else "post-exclusion k<6; A3 uninformative"
                if len(a3) < 6
                else "A3 comparator/method safety uninformative"
                if contrasts["a3_half_gap_recovery"]["status"] != "eligible"
                else "full is not a ceiling; A3 uninformative"
            ),
        },
        "a4_echo_minus_tool_swap": {
            **a4_contrast,
            "alpha": 0.05,
            "passed": a4_safety
            and a4_contrast["status"] == "eligible"
            and a4_contrast["p_one_sided"] <= 0.05,
        },
        "reported": {
            "teacher_forced_case_pass": {
                arm: _arm_summary(records, arm)["final_pass"]
                for arm in ARMS
                if all(arm in record["arms"] for record in records)
            },
            "a1_no_shortfall_sensitivity": _contrast(a1_no_shortfall),
            "recency_minus_role": _contrast(
                cluster_values("recency_pinned", "role_pinned")[0]
            ),
            "non_evicting_turns": {
                "turns": non_evicting_count,
                "arms": {
                    arm: non_evicting_arm(arm)
                    for arm in ARMS
                    if all(arm in record["arms"] for record in records)
                },
            },
        },
        "safety": safety,
        "registered_contrasts_pass": primary_claim["status"]
        in {"SUPPORTED", "SUPPORTED_A1_ONLY"},
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
