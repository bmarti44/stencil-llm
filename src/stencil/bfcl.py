"""Small, CPU-testable helpers for the vendored BFCL V3 multi-turn harness."""

from __future__ import annotations

import hashlib
import json
import os
import random
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from stencil.stats import clustered_lower_bound

CATEGORIES = ("base", "missing_params", "missing_functions", "long_context")
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


def _rate(rows: list[dict], field: str = "final_pass") -> dict:
    passed = sum(bool(row[field]) for row in rows)
    n = len(rows)
    return {"n": n, "passed": passed, "rate": passed / n if n else None}


def _validity(rows: list[dict]) -> float | None:
    calls = [
        call for row in rows for turn in row["turns"] for call in turn["tool_calls"]
    ]
    return sum(bool(call["valid"]) for call in calls) / len(calls) if calls else None


def summarize_records(records: list[dict]) -> dict:
    """Paired pass contrasts, registered lower bounds, safety, and strata."""
    by_case: dict[str, dict[str, dict]] = {}
    for row in records:
        by_case.setdefault(row["case_id"], {})[row["arm"]] = row
    paired = {
        case_id: arms
        for case_id, arms in by_case.items()
        if all(arm in arms for arm in ("base", "ledger", "control"))
    }
    arms = ("base", "ledger", "control")
    pass_summary = {arm: _rate([case[arm] for case in paired.values()]) for arm in arms}
    contrasts = {}
    for reference in ("control", "base"):
        diffs = [
            100.0
            * (
                float(case["ledger"]["final_pass"])
                - float(case[reference]["final_pass"])
            )
            for case in paired.values()
        ]
        bound = clustered_lower_bound(diffs, alpha=0.025) if len(diffs) >= 2 else None
        contrasts[f"ledger-{reference}"] = {
            "mean_points": sum(diffs) / len(diffs) if diffs else None,
            "lower_bound": None if bound is None else bound["lower_bound"],
            "bound": bound,
        }
    rows_by_arm = {arm: [row for row in records if row["arm"] == arm] for arm in arms}
    safety = {
        "timeout_rate": {
            arm: _turn_bool_rate(rows_by_arm[arm], "timeout") for arm in arms
        },
        "truncation_rate": {
            arm: _turn_bool_rate(rows_by_arm[arm], "truncated") for arm in arms
        },
        "tool_call_validity": {arm: _validity(rows_by_arm[arm]) for arm in arms},
        "echo_copy_rate": {
            arm: sum(bool(row["echo_copy"]) for row in rows_by_arm[arm])
            / len(rows_by_arm[arm])
            if rows_by_arm[arm]
            else None
            for arm in arms
        },
    }
    safety["tool_validity_excess_vs_base"] = _difference(
        safety["tool_call_validity"]["ledger"], safety["tool_call_validity"]["base"]
    )
    safety["tool_validity_excess_vs_control"] = _difference(
        safety["tool_call_validity"]["ledger"], safety["tool_call_validity"]["control"]
    )
    safety["truncation_excess_vs_base"] = _difference(
        safety["truncation_rate"]["ledger"], safety["truncation_rate"]["base"]
    )
    safety["truncation_excess_vs_control"] = _difference(
        safety["truncation_rate"]["ledger"],
        safety["truncation_rate"]["control"],
    )
    safety["round7"] = {
        "timeout_cap": 0.02,
        "truncation_excess_cap": 0.02,
        "tool_validity_excess_floor": -0.02,
        "ledger_timeout_pass": _threshold(safety["timeout_rate"]["ledger"], "le", 0.02),
        "ledger_truncation_vs_base_pass": _threshold(
            safety["truncation_excess_vs_base"], "le", 0.02
        ),
        "ledger_truncation_vs_control_pass": _threshold(
            safety["truncation_excess_vs_control"], "le", 0.02
        ),
        "ledger_tool_validity_vs_base_pass": _threshold(
            safety["tool_validity_excess_vs_base"], "ge", -0.02
        ),
        "ledger_tool_validity_vs_control_pass": _threshold(
            safety["tool_validity_excess_vs_control"], "ge", -0.02
        ),
    }
    categories = sorted({row["category"] for row in records})
    by_category = {
        category: {
            arm: _rate([row for row in rows_by_arm[arm] if row["category"] == category])
            for arm in arms
        }
        for category in categories
    }
    return {
        "paired_cases": len(paired),
        "pass": pass_summary,
        "contrasts": contrasts,
        "safety": safety,
        "by_category": by_category,
    }


def _turn_bool_rate(rows: list[dict], field: str) -> float | None:
    turns = [turn for row in rows for turn in row["turns"]]
    return sum(bool(turn[field]) for turn in turns) / len(turns) if turns else None


def _difference(left: float | None, right: float | None) -> float | None:
    return None if left is None or right is None else left - right


def _threshold(value: float | None, direction: str, threshold: float) -> bool | None:
    if value is None:
        return None
    return value <= threshold if direction == "le" else value >= threshold


def _enable_vendor() -> None:
    vendor = str(Path(__file__).resolve().parents[2] / "vendor")
    if vendor not in sys.path:
        sys.path.insert(0, vendor)
