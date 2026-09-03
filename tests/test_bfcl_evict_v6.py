"""CPU regressions for LEG A Amendment 3 and fable F1--F10."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def qwen_tok():
    from tokenizers import Tokenizer

    return Tokenizer.from_file("models/qwen3-1.7b-hf/tokenizer.json")


def _candidate(role, text, start, width, turn, *, message_index=None, score=0.1):
    return {
        "role": role,
        "text": text,
        "span": [start, start + width],
        "turn": turn,
        "message_index": turn if message_index is None else message_index,
        "score": score,
    }


def test_f1_nearest_match_ranks_width_then_age_then_stable_source():
    from stencil.bfcl import build_matched_control

    selected = {
        **_candidate("user", "selected", 0, 10, 8, score=0.9),
        "pinned_columns": list(range(10)),
    }
    rows = [
        selected,
        _candidate("user", "far-width", 20, 7, 8),
        _candidate("user", "far-age", 30, 9, 2),
        _candidate("user", "stable-second", 40, 9, 7, message_index=5),
        _candidate("user", "stable-first", 50, 9, 7, message_index=4),
        _candidate("user", "supplement", 60, 3, 1),
    ]
    result = build_matched_control(rows, [selected], (0, 70))
    assert result["match_impossible"] is False
    assert result["entries"][0]["text"] == "stable-first"
    assert result["matches"][0] == {
        "target_role": "user",
        "matched_role": "user",
        "width_delta": -1,
        "turn_delta": -1,
    }
    assert sum(len(row["pinned_columns"]) for row in result["entries"]) == 10


def test_f1_impossible_depends_on_total_available_columns_not_exact_rows():
    from stencil.bfcl import build_matched_control

    selected = {
        **_candidate("user", "selected", 0, 6, 4),
        "pinned_columns": list(range(6)),
    }
    available = _candidate("user", "different width and age", 10, 8, 1)
    possible = build_matched_control(
        [selected, available], [selected], (0, 20)
    )
    assert possible["match_impossible"] is False
    assert sum(len(row["pinned_columns"]) for row in possible["entries"]) == 6
    impossible = build_matched_control(
        [selected, _candidate("user", "too-short", 10, 5, 1)],
        [selected],
        (0, 20),
    )
    assert impossible["match_impossible"] is True


def test_f2_decode_preserves_char_text_until_a_column_truncation(qwen_tok):
    from scripts.bfcl_mt import render_prompt
    from stencil.bfcl import clamp_candidate_rows, context_layout

    messages = [
        {"role": "user", "content": "  Alpha spacing is exact.  "},
        {"role": "assistant", "content": "ok"},
        {"role": "user", "content": "now"},
    ]
    context = render_prompt(messages, [])
    layout = context_layout(qwen_tok, context, messages, current_message_index=2)
    start = layout["evict_range"][0]
    row = _candidate("user", "  Alpha spacing is exact.  ", start, 4, 0)
    full = clamp_candidate_rows(
        [row],
        {"user": 4, "tool": 0},
        evict_range=layout["evict_range"],
        tokenizer=qwen_tok,
        context=context,
    )
    assert full["entries"][0]["text"] == row["text"]
    truncated = clamp_candidate_rows(
        [row],
        {"user": 2, "tool": 0},
        evict_range=layout["evict_range"],
        tokenizer=qwen_tok,
        context=context,
    )
    assert truncated["entries"][0]["text"] != row["text"]


def test_f2_echo_clamp_truncates_last_entry_at_source_token_boundary(qwen_tok):
    from scripts.bfcl_mt import _echo_clamp, render_prompt
    from stencil.bfcl import context_layout

    messages = [
        {"role": "user", "content": "alpha beta gamma delta epsilon"},
        {"role": "assistant", "content": "ok"},
        {"role": "tool", "content": "one two three four five six seven eight"},
        {"role": "user", "content": "now"},
    ]
    context = render_prompt(messages, [])
    layout = context_layout(qwen_tok, context, messages, current_message_index=3)
    ids = qwen_tok.encode(context).ids
    low, high = layout["evict_range"]
    midpoint = low + (high - low) // 2
    entries = [
        {
            **_candidate(
                "user", qwen_tok.decode(ids[low:midpoint]), low, midpoint - low, 0
            ),
            "pinned_columns": list(range(low, midpoint)),
        },
        {
            **_candidate(
                "tool",
                qwen_tok.decode(ids[midpoint:high]),
                midpoint,
                high - midpoint,
                1,
            ),
            "pinned_columns": list(range(midpoint, high)),
        },
    ]
    # Pick a target known to be attainable by a source-token prefix.
    attainable = []
    for count in range(1, len(entries[1]["pinned_columns"]) + 1):
        partial = dict(entries[1])
        partial["pinned_columns"] = entries[1]["pinned_columns"][:count]
        partial["text"] = qwen_tok.decode(ids[midpoint : midpoint + count])
        _, tokens, _ = _echo_clamp(
            qwen_tok,
            [entries[0], partial],
            context,
            layout["current_user_close"],
            target_tokens=10_000,
        )
        attainable.append(tokens)
    target = attainable[len(attainable) // 2]
    chosen, tokens, residual = _echo_clamp(
        qwen_tok,
        entries,
        context,
        layout["current_user_close"],
        target_tokens=target,
    )
    assert tokens == target and residual == 0
    assert chosen[0]["text"] == entries[0]["text"]
    assert 0 < len(chosen[-1]["pinned_columns"]) < len(entries[-1]["pinned_columns"])


def test_f3_full_overflow_is_always_a_truncated_failure():
    from stencil.bfcl import position_overflow_result, summarize_records
    from tests.test_bfcl_evict_v3 import _record

    assert position_overflow_result("full", 40961) == {
        "position_overflow": True,
        "generate": False,
        "pass": False,
        "truncated": True,
    }
    records = [_record(str(index)) for index in range(6)]
    full = records[0]["arms"]["full"]["turns"][0]
    full.update({"pass": False, "truncated": True, "position_overflow": True})
    summary = summarize_records(records)
    assert summary["safety"]["counts"]["full"]["truncated"] == 1


def test_f4_f5_f10_v5_closures_remain_live(monkeypatch):
    from scripts import bfcl_mt

    assert bfcl_mt._degenerate([1, 2, 3, 4] * 20, truncated=True) is False
    manifest = bfcl_mt.harness_manifest()
    assert "src/stencil/bfcl.py" in manifest["files"]
    assert "src/stencil/selector_v2.py" in manifest["files"]
    monkeypatch.delenv("STENCIL_SEALED_RUN", raising=False)
    assert len(bfcl_mt.load_cases("dev", limit=1)) == 1


def test_f6_tool_swap_echo_order_and_match_deltas_follow_treatment_order():
    from stencil.bfcl import tool_swap_plan

    tool = {**_candidate("tool", "selected tool", 0, 3, 4), "pinned_columns": [0, 1, 2]}
    user = {**_candidate("user", "selected user", 10, 2, 3), "pinned_columns": [10, 11]}
    replacement = _candidate("tool", "replacement", 20, 4, 2)
    result = tool_swap_plan(
        [tool, user, replacement], [tool, user], (0, 30)
    )
    assert result["entries"][0]["text"].startswith("replace")
    assert result["entries"][1]["text"] == "selected user"
    assert result["matches"] == [
        {
            "target_role": "tool",
            "matched_role": "tool",
            "width_delta": 1,
            "turn_delta": -2,
        }
    ]


def test_f7_truncation_count_uses_the_actual_pair_length():
    from stencil.selector_v2 import scoring_pair_token_count

    class PairTokenizer:
        def __call__(self, *values, **kwargs):
            assert kwargs.get("truncation") is False
            return {"input_ids": list(range(190 if len(values) == 1 else 205))}

    tokenizer = PairTokenizer()
    assert scoring_pair_token_count(tokenizer, "", "candidate", "user") == 205


def test_f8_non_evicting_pins_zero_and_shared_events_are_arm_scoped():
    from scripts.bfcl_mt import _arm_event_fields

    assert (
        _arm_event_fields("base", evicted=False, pinned_columns=123)["pinned_columns"]
        == 0
    )
    treatment = _arm_event_fields(
        "clf_pinned_echo",
        evicted=True,
        pinned_columns=10,
        pin_overflow=True,
        pin_overflow_total=True,
        dropped_columns=7,
        control_role_shortfall=True,
        role_column_deltas={"user": -2, "tool": 2},
    )
    control = _arm_event_fields(
        "clf_control",
        evicted=True,
        pinned_columns=10,
        pin_overflow=True,
        pin_overflow_total=True,
        dropped_columns=7,
        control_role_shortfall=True,
        role_column_deltas={"user": -2, "tool": 2},
    )
    assert treatment["pin_overflow"] is True
    assert treatment["control_role_shortfall"] is False
    assert control["pin_overflow"] is False
    assert control["control_role_shortfall"] is True


def test_f9_echo_only_stratum_outcome_label_and_dose_aggregates():
    from stencil.bfcl import summarize_records
    from tests.test_bfcl_evict_v3 import _record, _turn

    records = [_record(str(index)) for index in range(6)]
    for record in records:
        for arm, arm_row in record["arms"].items():
            echo_only = _turn(arm != "base", evicted=False)
            echo_only["turn"] = 2
            echo_only["eviction"].update(
                echo_tokens=4 if arm not in {"base", "full"} else 0,
                nominal_b=12,
                actual_b=0,
                scorer_truncated_candidates=0,
                echo_dropped_control_tokens=0,
                pin_overflow_dropped_columns=0,
                role_column_deltas={"user": 0, "tool": 0},
            )
            arm_row["turns"].append(echo_only)
    summary = summarize_records(records)
    assert summary["outcome"]["label"] == summary["leg_status"]
    assert summary["reported"]["non_evicting_stratum"]["turns"] == 6
    assert (
        summary["reported"]["non_evicting_stratum"]["arms"]["clf_pinned_echo"][
            "per_turn_pass"
        ]["n"]
        == 6
    )
    assert {"nominal_b", "actual_b"} <= set(
        summary["categories"]["long_context"]["arms"]["clf_pinned_echo"]
    )


def test_registration_hash_includes_a3_and_stale_certificate_is_refused(tmp_path):
    from scripts.bfcl_mt import (
        artifact_meta,
        certificate_payload,
        registration_text_and_hash,
        validate_preflight_certificate,
    )

    text, digest = registration_text_and_hash()
    assert "LEG A AMENDMENT 1" in text
    assert "LEG A AMENDMENT 2" in text
    assert "LEG A AMENDMENT 3" in text
    args = type(
        "Args",
        (),
        {
            "split": "dev",
            "mode": "teacher",
            "trunk": "1.7b",
            "max_new": 1,
            "deadline": 1.0,
        },
    )()
    meta = artifact_meta(args)
    assert meta["registration_sha256"] == digest
    stale = json.loads(json.dumps(meta))
    stale["registration_sha256"] = "0" * 64
    gates = {
        name: True
        for name in ("competence", "determinism", "feasibility", "invariants", "cost")
    }
    payload = certificate_payload(stale, gates)
    certificate = {
        "status": "PASSED",
        "certificate": payload,
        "certificate_sha256": hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
    }
    path = tmp_path / "stale.json"
    path.write_text(json.dumps(certificate))
    with pytest.raises(RuntimeError, match="certificate"):
        validate_preflight_certificate(path, meta)


def test_real_dev_dry_census_nearest_matching_and_echo_clamp(qwen_tok):
    """Re-run fable's 32-case/11-evicting-turn census without a model."""
    from scripts.bfcl_mt import (
        K,
        _turn_plan,
        build_teacher_history,
        load_cases,
        render_prompt,
    )
    from stencil.bfcl import context_layout, prepare_case

    evicting = 0
    for category, raw_case, ground_truth in load_cases("dev"):
        case = prepare_case(raw_case, ROOT / "data/bench/bfcl_v3_mt/function_docs")
        for turn_index in range(1, len(ground_truth)):
            messages = build_teacher_history(
                case, ground_truth, turn_index, f"v6_census_{category}_{turn_index}"
            )
            messages.extend(case["question"][turn_index])
            current_index = max(
                i for i, row in enumerate(messages) if row["role"] == "user"
            )
            context = render_prompt(messages, case["function"])
            layout = context_layout(
                qwen_tok, context, messages, current_message_index=current_index
            )
            if layout["history_end"] <= K:
                continue
            evicting += 1

            def scorer(texts, *, role, contexts):
                del role, contexts
                return [
                    0.9
                    if int(hashlib.sha256(text.encode()).hexdigest(), 16) % 10 < 3
                    else 0.1
                    for text in texts
                ]

            for arm in ("clf_control", "recency_pinned", "tool_swap_echo"):
                plan = _turn_plan(
                    qwen_tok, messages, case["function"], arm, scorer, 20260903
                )
                assert plan["selector"]["match_impossible"] is False
                assert abs(plan["selector"]["echo_token_delta"]) <= 16
    assert evicting == 11
