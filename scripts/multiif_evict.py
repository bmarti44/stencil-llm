"""Registered Multi-IF post-development evaluation with pre-query KV eviction.

The benchmark is evaluation-only: this module never fits, selects a threshold,
or reads the sealed single-turn IFEval data. Conversation records are written
atomically from the first completed conversation and are safe to resume.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
import time
from collections.abc import Mapping, Sequence
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from stencil import determinism  # noqa: E402
from stencil.qwen3 import prefill_with_eviction as prefill_for_generation  # noqa: E402

ARMS = (
    "full",
    "evicted",
    "clf_pinned",
    "clf_pinned_echo",
    "clf_control",
    "role_pinned",
)
OPENER = "<|im_start|>assistant\n<think>\n\n</think>\n\n"
CHAT_CONTROL_TOKENS = ("<|im_start|>", "<|im_end|>", "<|endoftext|>")
DEGENERATE_REP4 = 0.5
QUOTING_RUN = 8
REGISTERED_COHORT = 909


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--max-new", type=int, default=512)
    parser.add_argument("--deadline", type=float, default=300.0)
    parser.add_argument("--out", default="multiif-evict-909-prequery-v2")
    args = parser.parse_args(argv)
    if args.limit is not None and args.limit <= 0:
        parser.error("--limit must be positive")
    if args.start < 0:
        parser.error("--start must be non-negative")
    return args


def sha256(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def atomic_json(path: str | Path, value: object) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=1) + "\n")
    temporary.replace(path)


def split_sentences(text: str) -> list[tuple[int, int]]:
    """The exact registered splitter from ``clf_score_sessions.py``."""
    out = []
    start = 0
    i = 0
    n = len(text)
    single_quote = double_quote = False
    while i < n:
        char = text[i]
        if char == '"':
            double_quote = not double_quote
        elif char == "'":
            if not single_quote and (i == 0 or not text[i - 1].isalnum()):
                single_quote = True
            elif single_quote and (i + 1 >= n or not text[i + 1].isalnum()):
                single_quote = False
        if char in ".!?":
            abbreviation = (
                i >= 1
                and text[i - 1].isalpha()
                and text[i - 1].isupper()
                and (i < 2 or not text[i - 2].isalpha())
            )
            j = i + 1
            while j < n and text[j] in ".!?":
                j += 1
            k = j
            next_single, next_double = single_quote, double_quote
            while k < n and text[k] in "\"')":
                if text[k] == '"':
                    next_double = not next_double
                elif text[k] == "'" and next_single:
                    next_single = False
                k += 1
            if (
                not abbreviation
                and not next_single
                and not next_double
                and (k >= n or text[k].isspace())
            ):
                out.append((start, k))
                single_quote, double_quote = next_single, next_double
                start = k
                while start < n and text[start].isspace():
                    start += 1
                i = start
                continue
        i += 1
    if start < n:
        out.append((start, n))
    return [
        (begin, end)
        for begin, end in out
        if end > begin and len(re.findall(r"[A-Za-z]", text[begin:end])) >= 2
    ]


def user_turns(context: str) -> list[tuple[int, int]]:
    marker = "<|im_start|>user\n"
    turns = []
    cursor = 0
    while True:
        marker_start = context.find(marker, cursor)
        if marker_start < 0:
            return turns
        start = marker_start + len(marker)
        end = context.find("<|im_end|>", start)
        if end < 0:
            raise ValueError("unterminated user turn")
        turns.append((start, end))
        cursor = end + len("<|im_end|>")


def _prefix_token_count(tokenizer, context: str, char_end: int) -> int:
    return len(tokenizer.encode(context[:char_end]).ids)


def context_layout(tokenizer, context: str) -> dict:
    """Return protected prefix and real prior-history eviction range."""
    turns = user_turns(context)
    if len(turns) < 2:
        raise ValueError("context must contain prior and current user turns")
    current_marker = context.rfind("<|im_start|>user\n", 0, turns[-1][0])
    if current_marker < 0:
        raise ValueError("current user marker missing")
    system_end = 0
    if context.startswith("<|im_start|>system\n"):
        close = context.find("<|im_end|>")
        if close < 0 or close > context.find("<|im_start|>user\n"):
            raise ValueError("unterminated system prompt")
        system_end = close + len("<|im_end|>")
        if context[system_end : system_end + 1] == "\n":
            system_end += 1
    ids = list(tokenizer.encode(context).ids)
    protected_end = max(4, _prefix_token_count(tokenizer, context, system_end))
    eviction_end = _prefix_token_count(tokenizer, context, current_marker)
    if protected_end > eviction_end:
        raise ValueError("protected prefix consumes the evictable history")
    return {
        "context_token_ids": ids,
        "protected_prefix": (0, protected_end),
        "evict_range": (protected_end, eviction_end),
    }


def _token_span(encoding, char_start: int, char_end: int) -> tuple[int, int] | None:
    columns = [
        index
        for index, (start, end) in enumerate(encoding.offsets)
        if start < char_end and end > char_start and end <= char_end
    ]
    return (columns[0], columns[-1] + 1) if columns else None


def select_prior_user_sentences(
    tokenizer,
    context: str,
    scorer,
    *,
    threshold: float = 0.5,
) -> tuple[list[dict], list[dict]]:
    """Score all prior-user sentences once, without context, on CPU."""
    encoding = tokenizer.encode(context)
    candidates = []
    for turn, (user_start, user_end) in enumerate(user_turns(context)[:-1], start=1):
        content = context[user_start:user_end]
        for local_start, local_end in split_sentences(content):
            char_start, char_end = user_start + local_start, user_start + local_end
            while char_start < char_end and context[char_start].isspace():
                char_start += 1
            while char_end > char_start and context[char_end - 1].isspace():
                char_end -= 1
            span = _token_span(encoding, char_start, char_end)
            if span is not None:
                candidates.append(
                    {
                        "text": context[char_start:char_end],
                        "turn": turn,
                        "char_span": [char_start, char_end],
                        "span": list(span),
                    }
                )
    texts = [row["text"] for row in candidates]
    scores = scorer(texts, role="user", contexts=[""] * len(texts)) if texts else []
    if len(scores) != len(candidates):
        raise ValueError("classifier returned the wrong number of scores")
    for row, score in zip(candidates, scores, strict=True):
        row["score"] = float(score)
        if not 0.0 <= row["score"] <= 1.0:
            raise ValueError("classifier score outside [0, 1]")
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


def matched_control_spans(
    keep: Sequence[tuple[int, int]], evict_range: tuple[int, int]
) -> list[tuple[int, int]] | None:
    """Position-match exactly the deduplicated surviving-column mass."""
    low, high = evict_range
    pinned = {
        column
        for start, end in keep
        for column in range(max(low, start), min(high, end))
    }
    available = set(range(low, high)) - pinned
    if len(available) < len(pinned):
        return None
    chosen = []
    for target in sorted(pinned):
        candidate = min(
            available,
            key=lambda column: (abs(column - target), column < target, column),
        )
        chosen.append(candidate)
        available.remove(candidate)
    return _columns_to_spans(chosen)


def clamp_and_match_control(
    spans: Sequence[tuple[int, int]], evict_range: tuple[int, int]
) -> tuple[list[tuple[int, int]], list[tuple[int, int]] | None]:
    """Clamp selected spans first, then construct the exact-column control."""
    low, high = evict_range
    pinned = _columns_to_spans(
        [
            column
            for start, end in spans
            for column in range(max(low, start), min(high, end))
        ]
    )
    return pinned, matched_control_spans(pinned, evict_range) if pinned else []


def role_pinned_spans(
    tokenizer, context: str, evict_range: tuple[int, int], budget: int
) -> list[tuple[int, int]]:
    """Pin prior USER columns, clipped to the classifier budget by recency."""
    if budget <= 0:
        return []
    encoding = tokenizer.encode(context)
    low, high = evict_range
    columns = []
    for start, end in user_turns(context)[:-1]:
        span = _token_span(encoding, start, end)
        if span is not None:
            columns.extend(range(max(low, span[0]), min(high, span[1])))
    chosen = sorted(set(columns))[-budget:]
    if len(chosen) != budget:
        raise RuntimeError("prior USER columns cannot fill classifier pin budget")
    return _columns_to_spans(chosen)


def repeated_4gram_fraction(ids: Sequence[int]) -> float:
    if len(ids) < 8:
        return 0.0
    grams = [tuple(ids[index : index + 4]) for index in range(len(ids) - 3)]
    return 1.0 - len(set(grams)) / len(grams)


def invalid_output(text: str) -> bool:
    return bool(
        not text
        or not any(char.isalnum() for char in text)
        or any(token in text for token in CHAT_CONTROL_TOKENS)
    )


def detect_quoting(
    response_ids: Sequence[int], echo_ids: Sequence[int], *, echo_arm: bool
) -> bool:
    if not echo_arm or len(response_ids) < QUOTING_RUN or len(echo_ids) < QUOTING_RUN:
        return False
    windows = {
        tuple(echo_ids[index : index + QUOTING_RUN])
        for index in range(len(echo_ids) - QUOTING_RUN + 1)
    }
    return any(
        tuple(response_ids[index : index + QUOTING_RUN]) in windows
        for index in range(len(response_ids) - QUOTING_RUN + 1)
    )


def run_arm(
    model,
    tokenizer,
    ids: Sequence[int],
    *,
    evict_range: tuple[int, int] | None,
    keep: Sequence[tuple[int, int]],
    max_new: int,
    deadline: float,
) -> dict:
    """Greedy generation after a single real pre-query cache eviction."""
    import torch

    from stencil.bench import EOS
    from stencil.qwen3 import KVCache

    cache = KVCache(model.cfg)
    generated = []
    started = time.monotonic()
    timed_out = False
    device = next(model.parameters()).device
    with torch.no_grad():
        tokens = torch.tensor([list(ids)], device=device)
        # All callers provide chat contexts; derive the exact registered split
        # from the final user marker rather than from any echo text length.
        context = tokenizer.decode(ids, skip_special_tokens=False)
        marker = context.rfind("<|im_start|>user\n")
        if marker < 0:
            raise ValueError("current user marker missing")
        history_end = len(tokenizer.encode(context[:marker]).ids)
        pinned_columns = []
        logits, index_map, _history_columns_before, history_columns_after = (
            prefill_for_generation(
                model,
                cache,
                tokens,
                history_end=history_end,
                evict_range=evict_range,
                keep=keep,
            )
        )
        if evict_range is not None:
            pinned_columns = sorted(
                {
                    index_map[column]
                    for start, end in keep
                    for column in range(start, end)
                    if column in index_map
                }
            )
        cache_columns_before = len(ids)
        cache_columns_after = history_columns_after + len(ids) - history_end
        next_token = int(logits[0, -1].argmax())
        while next_token not in EOS and len(generated) < max_new:
            if time.monotonic() - started > deadline:
                timed_out = True
                break
            generated.append(next_token)
            logits = model(
                torch.tensor([[next_token]], device=device), cache=cache
            )
            next_token = int(logits[0, -1].argmax())
    text = tokenizer.decode(generated, skip_special_tokens=False)
    truncated = len(generated) >= max_new
    repetition = repeated_4gram_fraction(generated)
    return {
        "text": text,
        "generated_token_ids": generated,
        "n_generated": len(generated),
        "timed_out": timed_out,
        "truncated": truncated,
        "repetition_4gram": repetition,
        "degenerate": truncated or repetition > DEGENERATE_REP4,
        "invalid": invalid_output(text),
        "pinned_cols": len(pinned_columns),
        "cache_cols_before": cache_columns_before,
        "cache_cols_after_eviction": cache_columns_after,
        "evicted_cols": cache_columns_before - cache_columns_after,
    }


def assert_record_schema(record: Mapping) -> None:
    required = {
        "schema",
        "ci",
        "key",
        "last_turn",
        "context_token_ids",
        "echo_context_token_ids",
        "protected_prefix",
        "evict_range",
        "selected_spans",
        "control_impossible",
        "control_pinned_cols",
        "control_available_cols",
        "pinned_cols",
        "control_spans",
        "arms",
        "seconds",
    }
    missing = required - set(record)
    if missing:
        raise ValueError(f"record fields missing: {sorted(missing)}")
    if set(record["arms"]) != set(ARMS):
        raise ValueError("record arms do not equal the registered arm set")
    if set(record["pinned_cols"]) != set(ARMS):
        raise ValueError("pinned_cols do not cover the registered arm set")
    if not isinstance(record["control_impossible"], bool):
        raise ValueError("control_impossible must be boolean")
    control_impossible = record["control_impossible"]
    control_fields = (
        record["control_spans"],
        record["pinned_cols"]["clf_control"],
        record["arms"]["clf_control"],
    )
    null_control_fields = [value is None for value in control_fields]
    if any(null_control_fields) != all(null_control_fields):
        raise ValueError("control fields must be all null or all populated")
    if control_impossible != all(null_control_fields):
        raise ValueError("control fields do not match control_impossible")
    pinned_columns = int(record["control_pinned_cols"])
    available_columns = int(record["control_available_cols"])
    low, high = (int(value) for value in record["evict_range"])
    if available_columns != high - low - pinned_columns:
        raise ValueError("control shortfall arithmetic is inconsistent")
    if pinned_columns < 0 or available_columns < 0:
        raise ValueError("control shortfall counts must be non-negative")
    if control_impossible != (available_columns < pinned_columns):
        raise ValueError("control_impossible does not match the recorded arithmetic")
    if int(record["pinned_cols"]["clf_pinned"]) != pinned_columns:
        raise ValueError("recorded classifier pin count is inconsistent")
    for name, arm in record["arms"].items():
        if arm is None:
            if name != "clf_control":
                raise ValueError(f"arm {name} may not be null")
            continue
        arm_required = {
            "text",
            "generated_token_ids",
            "n_generated",
            "scores",
            "safety",
            "quoting",
        }
        if arm_required - set(arm):
            raise ValueError(f"arm {name} schema incomplete")
        if set(arm["safety"]) != {"timed_out", "truncated", "degenerate", "invalid"}:
            raise ValueError(f"arm {name} safety schema incomplete")
        if set(arm["scores"]) < {"all", "aged"}:
            raise ValueError(f"arm {name} score schema incomplete")


def resume_indices(outdir: str | Path, cohort: Sequence[tuple[int, str]]) -> list[int]:
    """Validate existing records and return only missing conversation indices."""
    outdir = Path(outdir)
    missing = []
    for ci, key in cohort:
        path = outdir / f"conv-{ci:03d}.json"
        if not path.exists():
            missing.append(ci)
            continue
        record = json.loads(path.read_text())
        assert_record_schema(record)
        if int(record["ci"]) != ci or str(record["key"]) != str(key):
            raise RuntimeError(f"resume identity mismatch at conversation {ci}")
    return missing


def _cluster_values(records: Sequence[Mapping], arm: str) -> list[float]:
    values = []
    for record in records:
        bits = [bool(value) for value in record["arms"][arm]["scores"]["aged"]]
        if not bits:
            raise ValueError("vacuous aged-constraint cluster")
        values.append(100.0 * sum(bits) / len(bits))
    return values


def _one_sided_cluster_p(values: Sequence[float]) -> float:
    """One-sided t p-value with stats.py's one-cluster continuity penalty."""
    from stencil.stats import CONTINUITY_POINTS, t_cdf

    count = len(values)
    if count < 2:
        return 1.0
    mean = sum(values) / count - CONTINUITY_POINTS / count
    variance = sum((value - sum(values) / count) ** 2 for value in values) / (count - 1)
    if variance == 0.0:
        return 0.0 if mean > 0 else 1.0
    statistic = mean / math.sqrt(variance / count)
    return 1.0 - t_cdf(statistic, count - 1)


def _contrast(values: Sequence[float]) -> dict:
    from stencil.stats import clustered_lower_bound

    bound = clustered_lower_bound(values)
    return {
        "n": len(values),
        "mean_points": sum(values) / len(values) if values else None,
        "lower_bound": bound["lower_bound"],
        "bound": bound,
        "p_one_sided": _one_sided_cluster_p(values),
    }


def _holm(contrasts: Mapping[str, Mapping], alpha: float = 0.05) -> dict:
    ordered = sorted(contrasts, key=lambda name: (contrasts[name]["p_one_sided"], name))
    passed_so_far = True
    result = {}
    count = len(ordered)
    for rank, name in enumerate(ordered):
        cutoff = alpha / (count - rank)
        passed = passed_so_far and contrasts[name]["p_one_sided"] <= cutoff
        result[name] = {
            "p_one_sided": contrasts[name]["p_one_sided"],
            "cutoff": cutoff,
            "passed": passed,
        }
        passed_so_far = passed
    return result


def summarize_records(records: Sequence[Mapping]) -> dict:
    """Paired conversation summary, registered contrasts, Holm, and safety."""
    if len(records) < 2:
        raise ValueError("summary needs at least two conversations")
    for record in records:
        assert_record_schema(record)
    control_records = [record for record in records if not record["control_impossible"]]
    arm_summary = {}
    clusters = {
        arm: _cluster_values(control_records if arm == "clf_control" else records, arm)
        for arm in ARMS
    }
    for arm in ARMS:
        arm_records = control_records if arm == "clf_control" else records
        aged = [
            bool(value)
            for record in arm_records
            for value in record["arms"][arm]["scores"]["aged"]
        ]
        all_constraints = [
            bool(value)
            for record in arm_records
            for value in record["arms"][arm]["scores"]["all"]
        ]
        arm_summary[arm] = {
            "aged_pass": sum(aged),
            "aged_n": len(aged),
            "aged_rate": sum(aged) / len(aged) if aged else None,
            "all_pass": sum(all_constraints),
            "all_n": len(all_constraints),
            "all_rate": sum(all_constraints) / len(all_constraints)
            if all_constraints
            else None,
            "conversation_mean_aged_rate": (
                sum(clusters[arm]) / (100 * len(arm_records)) if arm_records else None
            ),
        }
    values = {
        "c1_echo_minus_control": [
            echo - control
            for echo, control in zip(
                _cluster_values(control_records, "clf_pinned_echo"),
                clusters["clf_control"],
                strict=True,
            )
        ],
        "c2_classifier_minus_role": [
            classifier - role
            for classifier, role in zip(
                clusters["clf_pinned"], clusters["role_pinned"], strict=True
            )
        ],
        "c3_half_gap_recovery": [
            echo - evicted - 0.5 * (full - evicted)
            for echo, evicted, full in zip(
                clusters["clf_pinned_echo"],
                clusters["evicted"],
                clusters["full"],
                strict=True,
            )
        ],
        "descriptive_echo_minus_full": [
            echo - full
            for echo, full in zip(
                clusters["clf_pinned_echo"], clusters["full"], strict=True
            )
        ],
    }
    contrasts = {name: _contrast(rows) for name, rows in values.items()}
    registered = {
        name: contrasts[name]
        for name in values
        if not name.startswith("descriptive")
    }
    holm = _holm(registered)
    safety_arms = {}
    for arm in ARMS:
        arm_records = control_records if arm == "clf_control" else records
        safety_arms[arm] = {
            field: sum(
                bool(record["arms"][arm]["safety"][field]) for record in arm_records
            )
            for field in ("timed_out", "truncated", "degenerate", "invalid")
        }
        safety_arms[arm]["quoting"] = sum(
            bool(record["arms"][arm]["quoting"]) for record in arm_records
        )
    full = safety_arms["full"]
    safety_pass = {}
    for arm, counts in safety_arms.items():
        safety_pass[arm] = {
            "timeouts_zero": counts["timed_out"] == 0,
            "truncation_integer_clause": counts["truncated"] <= full["truncated"] + 1,
            "degenerate_not_above_full": counts["degenerate"] <= full["degenerate"],
            "invalid_not_above_full": counts["invalid"] <= full["invalid"],
        }
        safety_pass[arm]["passed"] = all(safety_pass[arm].values())
    safety_intact = all(row["passed"] for row in safety_pass.values())
    return {
        "schema": 1,
        "conversations": len(records),
        "n_control_impossible": len(records) - len(control_records),
        "c1_population": len(control_records),
        "arms": arm_summary,
        "contrasts": contrasts,
        "holm": holm,
        "safety": {
            "integer_clause": (
                "timeouts=0; truncations<=full+1; degenerate<=full; invalid<=full"
            ),
            "counts": safety_arms,
            "checks": safety_pass,
            "intact": safety_intact,
        },
        "registered_contrasts_pass": safety_intact
        and all(row["passed"] for row in holm.values()),
        "seconds_total": sum(float(record["seconds"]["total"]) for record in records),
        "seconds_per_conversation": sum(
            float(record["seconds"]["total"]) for record in records
        )
        / len(records),
    }


def _tree_hashes(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): sha256(path)
        for path in sorted(root.rglob("*"))
        if path.is_file() and "__pycache__" not in path.parts
    }


def build_meta(args: argparse.Namespace, data_path: Path, model_path: Path) -> dict:
    classifier_dir = ROOT / "data/classifier/model/ft"
    return {
        "schema": 1,
        "registered_cohort": REGISTERED_COHORT,
        "slice": {"start": args.start, "limit": args.limit},
        "arms": list(ARMS),
        "threshold": 0.5,
        "selector_role": "user",
        "selector_context": "empty",
        "classifier_files_sha256": _tree_hashes(classifier_dir),
        "data": str(data_path.relative_to(ROOT)),
        "data_sha256": sha256(data_path),
        "model_sha256": sha256(model_path),
        "tokenizer_sha256": sha256(ROOT / "models/qwen3-1.7b-hf/tokenizer.json"),
        "harness_sha256": sha256(__file__),
        "ledger_sha256": sha256(ROOT / "src/stencil/ledger.py"),
        "selector_sha256": sha256(ROOT / "src/stencil/selector_v2.py"),
        "stats_sha256": sha256(ROOT / "src/stencil/stats.py"),
        "generation": {
            "greedy": True,
            "thinking": False,
            "opener": OPENER,
            "max_new": args.max_new,
            "deadline_seconds": args.deadline,
        },
        "position_policy": "no_reindex_positions_continue",
        "eviction_timing": "pre-query",
        "scoring": "vendored Multi-IF/IFEval process_results; truncations scored as-is",
    }


def _check_or_write_meta(path: Path, meta: Mapping) -> None:
    if path.exists():
        if json.loads(path.read_text()) != meta:
            raise RuntimeError("resume provenance mismatch")
    else:
        atomic_json(path, meta)


def _turn_doc(row: Mapping, turn: int) -> tuple[str, list[str], list[dict]]:
    prompt = json.loads(row[f"turn_{turn}_prompt"])["content"]
    ids = json.loads(row[f"turn_{turn}_instruction_id_list"])
    kwargs = [json.loads(value) for value in json.loads(row[f"turn_{turn}_kwargs"])]
    return prompt, ids, kwargs


def _score(row: Mapping, turn: int, text: str) -> dict:
    sys.path.insert(0, str(ROOT / "vendor"))
    import random

    import langdetect
    from ifeval import utils as ifeval_utils

    langdetect.DetectorFactory.seed = 0
    prompt, ids, kwargs = _turn_doc(row, turn)
    seed = int(hashlib.sha256(f"{row['key']}:{turn}".encode()).hexdigest()[:8], 16)
    random.seed(seed)
    document = {
        "key": 0,
        "prompt": prompt,
        "instruction_id_list": ids,
        "kwargs": kwargs,
    }
    return ifeval_utils.process_results(document, [text])


def _score_fields(row: Mapping, turn: int, text: str) -> dict:
    result = _score(row, turn, text)
    all_scores = [bool(value) for value in result["inst_level_strict_acc"]]
    previous_ids = (
        json.loads(row[f"turn_{turn - 1}_instruction_id_list"]) if turn > 1 else []
    )
    aged_count = len(previous_ids)
    return {
        "all": all_scores,
        "aged": all_scores[:aged_count],
        "prompt_strict": bool(result["prompt_level_strict_acc"]),
        "prompt_loose": bool(result["prompt_level_loose_acc"]),
        "instruction_loose": [bool(value) for value in result["inst_level_loose_acc"]],
        "aged_count": aged_count,
    }


def _entries(selected: Sequence[Mapping]):
    from stencil.ledger import Entry

    return [
        Entry(
            str(row["text"]),
            tuple(row["span"]),
            None,
            int(row["turn"]),
        )
        for row in selected
    ]


def _generate_history(
    model, tokenizer, prompts: Sequence[str], args
) -> tuple[str, dict]:
    history = ""
    generations = []
    started = time.monotonic()
    for prompt in prompts:
        context = history + f"<|im_start|>user\n{prompt}<|im_end|>\n" + OPENER
        result = run_arm(
            model,
            tokenizer,
            tokenizer.encode(context).ids,
            evict_range=None,
            keep=[],
            max_new=args.max_new,
            deadline=args.deadline,
        )
        generations.append(
            {
                "text": result["text"],
                "generated_token_ids": result["generated_token_ids"],
                "n_generated": result["n_generated"],
                "timed_out": result["timed_out"],
                "truncated": result["truncated"],
            }
        )
        history += (
            f"<|im_start|>user\n{prompt}<|im_end|>\n"
            f"<|im_start|>assistant\n{result['text']}<|im_end|>\n"
        )
    return history, {"generations": generations, "seconds": time.monotonic() - started}


def evaluate_conversation(
    model, tokenizer, scorer, row: Mapping, ci: int, args
) -> dict:
    from stencil.ledger import render_text_ledger, text_ledger_context

    started = time.monotonic()
    turns = [turn for turn in (1, 2, 3) if row[f"turn_{turn}_prompt"]]
    if len(turns) < 2:
        raise ValueError(f"conversation {ci} has no aged constraints")
    prompts = [_turn_doc(row, turn)[0] for turn in turns]
    history, history_meta = _generate_history(model, tokenizer, prompts[:-1], args)
    context = history + f"<|im_start|>user\n{prompts[-1]}<|im_end|>\n" + OPENER
    layout = context_layout(tokenizer, context)

    selector_started = time.monotonic()
    selected, candidates = select_prior_user_sentences(tokenizer, context, scorer)
    selected_spans = [tuple(record["span"]) for record in selected]
    pinned, control = clamp_and_match_control(selected_spans, layout["evict_range"])
    pinned_columns = sum(end - start for start, end in pinned)
    available_columns = (
        layout["evict_range"][1] - layout["evict_range"][0] - pinned_columns
    )
    control_impossible = control is None
    role_pins = role_pinned_spans(
        tokenizer, context, layout["evict_range"], pinned_columns
    )
    entries = _entries(selected)
    echo_context = text_ledger_context(context, entries)
    echo_layout = context_layout(tokenizer, echo_context)
    if echo_layout["evict_range"] != layout["evict_range"]:
        raise AssertionError("echo changed prior-history eviction coordinates")
    echo_ids = echo_layout["context_token_ids"]
    rendered_echo = render_text_ledger(entries)
    rendered_echo_ids = tokenizer.encode(rendered_echo).ids if rendered_echo else []
    selector_seconds = time.monotonic() - selector_started

    arm_inputs = {
        "full": (layout["context_token_ids"], None, []),
        "evicted": (layout["context_token_ids"], layout["evict_range"], []),
        "clf_pinned": (layout["context_token_ids"], layout["evict_range"], pinned),
        "clf_pinned_echo": (echo_ids, echo_layout["evict_range"], pinned),
        "clf_control": (
            layout["context_token_ids"],
            layout["evict_range"],
            control,
        ),
        "role_pinned": (layout["context_token_ids"], layout["evict_range"], role_pins),
    }
    arms = {}
    arm_started = time.monotonic()
    for name in ARMS:
        if name == "clf_control" and control_impossible:
            arms[name] = None
            continue
        ids, eviction, keep = arm_inputs[name]
        generated = run_arm(
            model,
            tokenizer,
            ids,
            evict_range=eviction,
            keep=keep,
            max_new=args.max_new,
            deadline=args.deadline,
        )
        scores = _score_fields(row, turns[-1], generated["text"])
        arms[name] = {
            **generated,
            "scores": scores,
            "safety": {
                "timed_out": generated.pop("timed_out"),
                "truncated": generated.pop("truncated"),
                "degenerate": generated.pop("degenerate"),
                "invalid": generated.pop("invalid"),
            },
            "quoting": detect_quoting(
                generated["generated_token_ids"],
                rendered_echo_ids,
                echo_arm=name == "clf_pinned_echo",
            ),
        }
    arm_seconds = time.monotonic() - arm_started
    if not control_impossible and (
        arms["clf_pinned"]["pinned_cols"] != arms["clf_control"]["pinned_cols"]
    ):
        raise AssertionError("classifier and control pinned-column counts differ")
    if arms["clf_pinned"]["pinned_cols"] != arms["role_pinned"]["pinned_cols"]:
        raise AssertionError("classifier and role pinned-column counts differ")
    seconds = {
        "history": history_meta["seconds"],
        "selector": selector_seconds,
        "arms": arm_seconds,
        "total": time.monotonic() - started,
    }
    record = {
        "schema": 1,
        "ci": ci,
        "key": row["key"],
        "last_turn": turns[-1],
        "context_token_ids": layout["context_token_ids"],
        "echo_context_token_ids": echo_ids,
        "protected_prefix": list(layout["protected_prefix"]),
        "evict_range": list(layout["evict_range"]),
        "history": history_meta,
        "selector_candidates": candidates,
        "selected_spans": selected,
        "control_impossible": control_impossible,
        "control_pinned_cols": pinned_columns,
        "control_available_cols": available_columns,
        "pinned_cols": {
            name: int(arms[name]["pinned_cols"]) if arms[name] is not None else None
            for name in ARMS
        },
        "classifier_spans": [list(span) for span in pinned],
        "role_spans": [list(span) for span in role_pins],
        "control_spans": (
            [list(span) for span in control] if control is not None else None
        ),
        "echo_text": rendered_echo,
        "echo_tokens_added": len(echo_ids) - len(layout["context_token_ids"]),
        "arms": arms,
        "seconds": seconds,
    }
    assert_record_schema(record)
    return record


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    determinism.assert_gpu_free_or_owned()
    import torch
    from tokenizers import Tokenizer

    from stencil.qwen3 import Qwen3
    from stencil.selector_v2 import ClassifierScorer

    data_path = ROOT / "data/bench/multiif_en.jsonl"
    model_path = ROOT / "models/qwen3-1.7b.pt"
    rows = [json.loads(line) for line in data_path.read_text().splitlines()]
    if len(rows) != REGISTERED_COHORT:
        raise RuntimeError(
            f"Multi-IF cohort is {len(rows)}, expected {REGISTERED_COHORT}"
        )
    stop = len(rows) if args.limit is None else min(len(rows), args.start + args.limit)
    selected_rows = list(enumerate(rows[args.start:stop], start=args.start))
    outdir = ROOT / "results/qwen" / args.out
    outdir.mkdir(parents=True, exist_ok=True)
    _check_or_write_meta(outdir / "meta.json", build_meta(args, data_path, model_path))
    missing = set(
        resume_indices(outdir, [(ci, str(row["key"])) for ci, row in selected_rows])
    )
    tokenizer = Tokenizer.from_file(str(ROOT / "models/qwen3-1.7b-hf/tokenizer.json"))
    scorer = ClassifierScorer(ROOT / "data/classifier/model/ft")
    model = Qwen3()
    model.load_state_dict(torch.load(model_path, map_location="cpu", weights_only=True))
    model = model.to(torch.bfloat16).cuda().eval()
    for ci, row in selected_rows:
        if ci not in missing:
            continue
        record = evaluate_conversation(model, tokenizer, scorer, row, ci, args)
        atomic_json(outdir / f"conv-{ci:03d}.json", record)
        aged = len(record["arms"]["full"]["scores"]["aged"])
        report = " ".join(
            (
                f"{arm}={sum(record['arms'][arm]['scores']['aged'])}/{aged}"
                if record["arms"][arm] is not None
                else f"{arm}=NA"
            )
            for arm in ARMS
        )
        elapsed = record["seconds"]["total"]
        print(f"conversation {ci}: {report} seconds={elapsed:.1f}", flush=True)
    records = [
        json.loads((outdir / f"conv-{ci:03d}.json").read_text())
        for ci, _ in selected_rows
    ]
    summary = summarize_records(records)
    summary["projected_full_gpu_hours"] = (
        summary["seconds_per_conversation"] * REGISTERED_COHORT / 3600
    )
    summary["full_run_allowed_by_preflight"] = (
        summary["projected_full_gpu_hours"] <= 12.0
    )
    atomic_json(outdir / "summary.json", summary)
    print(json.dumps(summary, indent=1), flush=True)


if __name__ == "__main__":
    main()
