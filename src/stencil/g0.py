"""Shared, side-effect-free helpers for the G0 counterfactual salience pilot."""

from __future__ import annotations

import hashlib
import math
import random
import re
from collections import Counter, defaultdict
from collections.abc import Sequence
from pathlib import Path
from typing import Any

SEED = 20260903
ROLES = ("system", "user", "assistant", "tool")
SPAN_FIELDS = ("role", "start", "end", "n_tok", "text_sha", "utility", "top1_agree")
RECORD_FIELDS = (
    "corpus",
    "id",
    "turn",
    "n_context_tokens",
    "spans",
    "nulls",
    "joint",
    "policies",
    "seconds",
)


def ensure_g0_path(path: str | Path) -> Path:
    """Reject every path whose normalized components enter evaluation data."""
    result = Path(path).resolve(strict=False)
    parts = result.parts
    if any(parts[i : i + 2] == ("data", "bench") for i in range(len(parts) - 1)):
        raise ValueError("evaluation-only benchmark paths are forbidden in G0")
    return result


def text_sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def length_bucket(n_tokens: int) -> int:
    if n_tokens <= 64:
        return 0
    if n_tokens <= 96:
        return 1
    return 2


def age_bucket(age: int) -> int:
    if age <= 1:
        return 0
    if age <= 3:
        return 1
    if age <= 7:
        return 2
    return 3


def _sentence_token_ranges(text: str, tokenizer) -> list[tuple[int, int]]:
    encoding = tokenizer.encode(text)
    offsets = encoding.offsets
    ranges = []
    for match in re.finditer(r"[^.!?\n]+(?:[.!?]+|\n+|$)", text):
        cols = [
            i
            for i, (a, b) in enumerate(offsets)
            if a < match.end() and b > match.start()
        ]
        if cols:
            ranges.append((cols[0], cols[-1] + 1))
    if not ranges and encoding.ids:
        ranges.append((0, len(encoding.ids)))
    return ranges


def _message_chunks(
    text: str, tokenizer, min_tokens: int, max_tokens: int
) -> list[tuple[int, int]]:
    sentences = _sentence_token_ranges(text, tokenizer)
    chunks: list[tuple[int, int]] = []
    pending: tuple[int, int] | None = None
    for sent_start, sent_end in sentences:
        cursor = sent_start
        while sent_end - cursor > max_tokens:
            if pending is not None:
                chunks.append(pending)
                pending = None
            chunks.append((cursor, cursor + max_tokens))
            cursor += max_tokens
        if cursor >= sent_end:
            continue
        if pending is None:
            pending = (cursor, sent_end)
        elif sent_end - pending[0] <= max_tokens:
            pending = (pending[0], sent_end)
        else:
            chunks.append(pending)
            pending = (cursor, sent_end)
        if pending[1] - pending[0] >= min_tokens:
            chunks.append(pending)
            pending = None
    if pending is not None:
        if chunks and pending[1] - chunks[-1][0] <= max_tokens:
            chunks[-1] = (chunks[-1][0], pending[1])
        else:
            chunks.append(pending)
    return chunks


def build_candidate_spans(
    messages: Sequence[dict[str, Any]],
    tokenizer,
    *,
    seed: int = SEED,
    max_spans: int = 12,
    min_tokens: int = 64,
    max_tokens: int = 128,
) -> list[dict[str, Any]]:
    """Construct message-bounded spans and select them round-robin by role."""
    if not 0 < min_tokens <= max_tokens:
        raise ValueError("token bounds must satisfy 0 < min <= max")
    current_turn = max(
        (int(m.get("turn", i)) for i, m in enumerate(messages)), default=0
    )
    by_role: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for message_idx, message in enumerate(messages):
        role = str(message["role"])
        if role not in ROLES:
            continue
        content = str(message.get("content", ""))
        encoding = tokenizer.encode(content)
        base = int(message["token_start"])
        turn = int(message.get("turn", message_idx))
        for lo, hi in _message_chunks(content, tokenizer, min_tokens, max_tokens):
            if hi - lo < 2:
                continue
            char_lo = encoding.offsets[lo][0]
            char_hi = encoding.offsets[hi - 1][1]
            n_tok = hi - lo
            by_role[role].append(
                {
                    "role": role,
                    "start": base + lo,
                    "end": base + hi,
                    "n_tok": n_tok,
                    "text_sha": text_sha(content[char_lo:char_hi]),
                    "message_idx": message_idx,
                    "turn": turn,
                    "age": current_turn - turn,
                    "length_bucket": length_bucket(n_tok),
                    "age_bucket": age_bucket(current_turn - turn),
                }
            )
    rng = random.Random(seed)
    for role in ROLES:
        rng.shuffle(by_role[role])
    selected = []
    while len(selected) < max_spans:
        progressed = False
        for role in ROLES:
            if by_role[role]:
                selected.append(by_role[role].pop())
                progressed = True
                if len(selected) == max_spans:
                    break
        if not progressed:
            break
    return selected


def match_null_spans(
    candidates: Sequence[dict[str, Any]],
    messages: Sequence[dict[str, Any]],
    tokenizer,
    *,
    seed: int = SEED,
) -> list[dict[str, Any]]:
    """Draw deterministic role/length/age-matched token spans."""
    rng = random.Random(seed ^ 0xA11CE)
    current_turn = max(
        (int(m.get("turn", i)) for i, m in enumerate(messages)), default=0
    )
    nulls = []
    for candidate in candidates:
        eligible = []
        for message_idx, message in enumerate(messages):
            turn = int(message.get("turn", message_idx))
            encoding = tokenizer.encode(str(message.get("content", "")))
            if (
                message["role"] != candidate["role"]
                or age_bucket(current_turn - turn) != candidate["age_bucket"]
            ):
                continue
            base = int(message["token_start"])
            lengths = [
                n_tok
                for n_tok in range(1, min(128, len(encoding.ids)) + 1)
                if length_bucket(n_tok) == candidate["length_bucket"]
            ]
            if lengths:
                eligible.append((message_idx, turn, encoding, base, lengths))
        choice = None
        for _ in range(100):
            message_idx, turn, encoding, base, lengths = rng.choice(eligible)
            n_tok = rng.choice(lengths)
            lo = rng.randrange(len(encoding.ids) - n_tok + 1)
            bounds = (base + lo, base + lo + n_tok)
            if bounds != (candidate["start"], candidate["end"]):
                choice = (message_idx, turn, encoding, lo, bounds)
                break
        if choice is None:
            raise ValueError(
                "cannot draw a distinct null with matching role, length, and age "
                "buckets"
            )
        message_idx, turn, encoding, lo, (start, end) = choice
        n_tok = end - start
        content = str(messages[message_idx].get("content", ""))
        char_lo = encoding.offsets[lo][0]
        char_hi = encoding.offsets[lo + n_tok - 1][1]
        nulls.append(
            {
                "role": candidate["role"],
                "start": start,
                "end": end,
                "n_tok": n_tok,
                "text_sha": text_sha(content[char_lo:char_hi]),
                "message_idx": message_idx,
                "turn": turn,
                "age": current_turn - turn,
                "length_bucket": candidate["length_bucket"],
                "age_bucket": candidate["age_bucket"],
            }
        )
    return nulls


def policy_recovery(
    utilities: Sequence[float],
    kept_span_idx: Sequence[int],
    null_utilities: Sequence[float],
) -> dict[str, float]:
    if len(utilities) != len(null_utilities):
        raise ValueError("candidate and null utility arrays must have equal length")
    kept = set(kept_span_idx)
    positive = [max(0.0, float(value)) for value in utilities]
    adjusted = [
        max(0.0, float(value) - max(0.0, float(null)))
        for value, null in zip(utilities, null_utilities, strict=True)
    ]

    def ratio(values: Sequence[float]) -> float:
        denominator = sum(values)
        return (
            sum(value for i, value in enumerate(values) if i in kept) / denominator
            if denominator
            else 0.0
        )

    return {"recovery": ratio(positive), "recovery_null_adj": ratio(adjusted)}


def _terms(text: str) -> list[str]:
    return re.findall(r"[\w]+", text.lower())


def bm25_rank(
    documents: Sequence[str], query: str, *, k1: float = 1.5, b: float = 0.75
) -> list[int]:
    """Small deterministic Okapi BM25 implementation (no optional dependency)."""
    docs = [_terms(document) for document in documents]
    if not docs:
        return []
    avg_len = sum(map(len, docs)) / len(docs) or 1.0
    dfs = Counter(term for doc in docs for term in set(doc))
    query_terms = _terms(query)
    scores = []
    for index, doc in enumerate(docs):
        counts = Counter(doc)
        score = 0.0
        for term in query_terms:
            freq = counts[term]
            if not freq:
                continue
            idf = math.log(1.0 + (len(docs) - dfs[term] + 0.5) / (dfs[term] + 0.5))
            denom = freq + k1 * (1.0 - b + b * len(doc) / avg_len)
            score += idf * freq * (k1 + 1.0) / denom
        scores.append((score, index))
    return [index for _, index in sorted(scores, key=lambda item: (-item[0], item[1]))]


def assert_g0_record(record: dict[str, Any]) -> None:
    def require(mapping: dict[str, Any], fields: Sequence[str], where: str) -> None:
        missing = [field for field in fields if field not in mapping]
        if missing:
            raise ValueError(
                f"{where} missing registered field(s): {', '.join(missing)}"
            )

    require(record, RECORD_FIELDS, "record")
    for group in ("spans", "nulls"):
        if not isinstance(record[group], list):
            raise ValueError(f"{group} must be a list")
        for index, span in enumerate(record[group]):
            require(span, SPAN_FIELDS, f"{group}[{index}]")
    require(record["joint"], ("span_idx", "utility", "sum_utility"), "joint")
    if not isinstance(record["policies"], dict):
        raise ValueError("policies must be an object")
    for name, policy in record["policies"].items():
        require(
            policy, ("kept_span_idx", "recovery", "recovery_null_adj"), f"policy {name}"
        )
