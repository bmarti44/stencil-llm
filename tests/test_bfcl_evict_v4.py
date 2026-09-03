"""CPU contracts for BFCL LEG A registration v7 plus Amendment 1."""

from __future__ import annotations

import pytest


def _columns(spans):
    return [column for start, end in spans for column in range(start, end)]


def _candidate(role, text, start, width, turn, score=0.1):
    return {
        "role": role,
        "text": text,
        "span": [start, start + width],
        "turn": turn,
        "message_index": turn,
        "score": score,
    }


def test_control_matches_whole_resources_by_width_and_age_without_reuse():
    from stencil.bfcl import build_matched_control

    selected = [
        {**_candidate("user", "selected-u", 0, 3, 2, 0.9), "pinned_columns": [0, 1, 2]},
        {**_candidate("tool", "selected-t", 10, 2, 1, 0.9), "pinned_columns": [10, 11]},
    ]
    candidates = [
        *selected,
        _candidate("user", "wrong-age", 20, 3, 1),
        _candidate("user", "match-u", 30, 3, 2),
        _candidate("tool", "match-t", 40, 2, 1),
    ]
    result = build_matched_control(candidates, selected, (0, 50), seed=20260903)
    assert [row["text"] for row in result["entries"]] == ["match-u", "match-t"]
    assert result["match_impossible"] is False
    assert result["control_role_shortfall"] is False
    assert len(_columns(result["pins"])) == 5
    assert len(set(_columns(result["pins"]))) == 5


def test_control_role_fallback_and_no_match_are_recorded_not_rotated():
    from stencil.bfcl import build_matched_control

    kept = [{**_candidate("user", "selected", 0, 3, 2), "pinned_columns": [0, 1, 2]}]
    fallback = _candidate("tool", "fallback", 10, 3, 2)
    result = build_matched_control([*kept, fallback], kept, (0, 20), seed=20260903)
    assert result["control_role_shortfall"] is True
    assert result["role_column_deltas"] == {"user": -3, "tool": 3}
    assert result["match_impossible"] is False
    impossible = build_matched_control(kept, kept, (0, 10), seed=20260903)
    assert impossible["match_impossible"] is True
    assert impossible["pins"] == []


def test_column_clamp_truncates_only_last_resource_to_exact_role_quota():
    from stencil.bfcl import clamp_candidate_rows

    rows = [
        _candidate("tool", "first", 0, 3, 3),
        _candidate("tool", "second", 3, 4, 2),
    ]
    result = clamp_candidate_rows(rows, {"user": 0, "tool": 5})
    assert [len(row["pinned_columns"]) for row in result["entries"]] == [3, 2]
    assert result["role_counts"] == {"user": 0, "tool": 5}
    assert _columns(result["pins"]) == [0, 1, 2, 3, 4]
    assert result["entries"][-1]["text"] != "second"


def test_recency_uses_exact_per_role_quota_and_tool_swap_has_no_fallback():
    from stencil.bfcl import recency_pinned_plan, tool_swap_plan

    rows = [
        _candidate("user", "old-u", 0, 4, 1),
        _candidate("user", "recent-u", 4, 4, 3),
        _candidate("tool", "selected-t", 10, 2, 2, 0.9),
        _candidate("tool", "match-t", 12, 2, 2),
        _candidate("user", "same-width-wrong-role", 20, 2, 2),
    ]
    recency = recency_pinned_plan(rows, {"user": 3, "tool": 2}, (0, 30))
    assert recency["role_counts"] == {"user": 3, "tool": 2}
    assert recency["match_impossible"] is False
    assert recency["entries"][0]["text"] != "old-u"
    kept = [{**rows[2], "pinned_columns": [10, 11]}]
    swap = tool_swap_plan(rows, kept, (0, 30), seed=20260903)
    assert [row["text"] for row in swap["entries"]] == ["match-t"]
    no_tool = tool_swap_plan([rows[2], rows[4]], kept, (0, 30), seed=20260903)
    assert no_tool["match_impossible"] is True
    assert no_tool["pins"] == []


def test_overflow_drops_whole_lowest_ranked_pins_with_entries_and_total_flag():
    from stencil.bfcl import resolve_pin_overflow

    rows = [
        {**_candidate("user", "high", 0, 3, 3, 0.9), "pinned_columns": [0, 1, 2]},
        {**_candidate("tool", "low", 5, 2, 1, 0.6), "pinned_columns": [5, 6]},
    ]
    partial = resolve_pin_overflow(rows, prefix_columns=4, turn_columns=3, k=10)
    assert [row["text"] for row in partial["entries"]] == ["high"]
    assert partial["pin_overflow"] is True
    assert partial["dropped_columns"] == 2
    total = resolve_pin_overflow(rows, prefix_columns=8, turn_columns=3, k=10)
    assert total["pin_overflow_total"] is True
    assert total["entries"] == [] and total["pins"] == []


@pytest.fixture(scope="module")
def qwen_tok():
    from tokenizers import Tokenizer

    return Tokenizer.from_file("models/qwen3-1.7b-hf/tokenizer.json")


def test_tool_output_is_newline_then_sentence_split_and_special_ids_drop(qwen_tok):
    from scripts.bfcl_mt import render_prompt
    from stencil.bfcl import select_history_spans

    messages = [
        {"role": "user", "content": "old request"},
        {"role": "tool", "content": "First fact. Second fact.\n\nThird fact!"},
        {"role": "user", "content": "new request"},
    ]
    prompt = render_prompt(messages, [])

    def scorer(texts, *, role, contexts):
        return [0.9] * len(texts)

    _, candidates, dropped = select_history_spans(
        qwen_tok,
        prompt,
        messages,
        scorer,
        special_token_ids={qwen_tok.encode(" fact").ids[0]},
    )
    assert [row["text"] for row in candidates if row["role"] == "tool"] == []
    assert dropped == 3


def test_scorer_truncation_is_counted_and_does_not_abort(monkeypatch):
    import torch

    from stencil.selector_v2 import ClassifierScorer

    scorer = object.__new__(ClassifierScorer)
    scorer.roles = ["user", "tool"]
    scorer.labels = ["rule", "fact"]
    scorer.encoder = lambda **batch: type(
        "Out", (), {"last_hidden_state": torch.zeros(1, 1, 1)}
    )()
    scorer.head = lambda value: torch.tensor([[2.0, 1.0]])

    class Tok:
        def __call__(self, *values, **kwargs):
            if kwargs.get("return_tensors") == "pt":
                return {"input_ids": torch.ones(1, 192, dtype=torch.long)}
            return {"input_ids": list(range(250))}

    scorer.tokenizer = Tok()
    assert len(scorer(["long candidate"], role="user", contexts=[""])) == 1
    assert scorer.scorer_truncated_candidates == 1


def test_exact_sign_flip_keeps_zeros_counts_ties_and_reports_grid():
    from stencil.bfcl import exact_sign_flip

    all_positive = exact_sign_flip([1, 1, 1, 1, 1, 1])
    assert all_positive == {
        "k": 6,
        "upper_tail": 1,
        "assignments": 64,
        "p": 1 / 64,
        "grid": "1/64",
    }
    with_zero = exact_sign_flip([1, 1, 1, 1, 1, 0])
    assert with_zero["p"] == 2 / 64
    assert with_zero["upper_tail"] == 2


def test_degenerate_ignores_truncation_and_case_safety_counts_once():
    from scripts.bfcl_mt import _degenerate
    from stencil.bfcl import summarize_records
    from tests.test_bfcl_evict_v3 import _record

    assert _degenerate([1, 2, 3], truncated=True) is False
    records = [_record(str(index)) for index in range(6)]
    for step in (
        {"token_ids": [1], "columns_after_step": 10},
        {"token_ids": [2], "columns_after_step": 10},
    ):
        records[0]["arms"]["base"]["turns"][0]["responses"].append(step)
    records[0]["arms"]["base"]["turns"][0]["timeout"] = True
    records[0]["arms"]["base"]["turns"][0]["repeated_call"] = True
    records[0]["arms"]["base"]["turns"][0]["chat_control_echo"] = True
    summary = summarize_records(records)
    assert summary["safety"]["counts"]["base"]["timeouts"] == 1
    assert summary["safety"]["counts"]["base"]["repeated_call"] == 1
    assert summary["safety"]["checks"]["base"]["timeouts_zero"] is False
    assert summary["safety"]["checks"]["base"]["chat_control_echo_zero"] is False


def test_k_floor_holm_and_comparator_uninformative_are_reported():
    from stencil.bfcl import summarize_records
    from tests.test_bfcl_evict_v3 import _record

    too_small = summarize_records([_record(str(index)) for index in range(5)])
    assert too_small["leg_status"] == "INCONCLUSIVE"
    records = [_record(str(index)) for index in range(6)]
    records[0]["arms"]["clf_control"]["turns"][0]["eviction"]["match_impossible"] = True
    summary = summarize_records(records)
    assert summary["contrasts"]["a1_echo_minus_control"]["status"] == "uninformative"
    assert summary["contrasts"]["a1_echo_minus_control"]["k"] == 6


def test_full_position_overflow_is_na_and_other_arm_overflow_truncates():
    from stencil.bfcl import position_overflow_result

    assert position_overflow_result("full", 40961) == {
        "position_overflow": True,
        "generate": False,
        "pass": None,
        "truncated": False,
    }
    assert position_overflow_result("base", 40961)["truncated"] is True


def test_registration_hash_covers_v7_and_amendment_and_meta_hash_names():
    from scripts.bfcl_mt import artifact_meta, registration_text_and_hash

    text, digest = registration_text_and_hash()
    assert "— v7" in text and "LEG A AMENDMENT 1" in text
    assert len(digest) == 64
    meta = artifact_meta(
        type(
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
    )
    assert meta["registration_sha256"] == digest
    assert {
        "harness",
        "selector_artifact",
        "trunk_weights",
        "trunk_tokenizer",
        "cohorts",
        "chat_template",
        "vendored_checker",
    } <= set(meta["frozen_hashes"])


def test_registered_cost_cut_removes_exact_arms_and_marks_a4_uninformative():
    from scripts.bfcl_mt import parse_args
    from stencil.bfcl import REDUCED_ARMS, summarize_records
    from tests.test_bfcl_evict_v3 import _record

    args = parse_args(["run", "--split", "dev", "--arm-cut"])
    assert args.arm_cut is True
    records = [_record(str(index)) for index in range(6)]
    for record in records:
        record["arms"] = {arm: record["arms"][arm] for arm in REDUCED_ARMS}
    summary = summarize_records(records)
    assert summary["a4_echo_minus_tool_swap"]["status"] == "uninformative"
