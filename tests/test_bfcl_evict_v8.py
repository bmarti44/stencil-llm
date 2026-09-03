"""CPU regressions closing fable FV6-1 through FV6-6."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def qwen_tok():
    from tokenizers import Tokenizer

    return Tokenizer.from_file("models/qwen3-1.7b-hf/tokenizer.json")


def _candidate(role, text, start, width, turn, *, message_index=None):
    return {
        "role": role,
        "text": text,
        "span": [start, start + width],
        "turn": turn,
        "message_index": turn if message_index is None else message_index,
        "score": 0.1,
    }


def _selected(role, text, start, width, turn):
    return {
        **_candidate(role, text, start, width, turn),
        "score": 0.9,
        "pinned_columns": list(range(start, start + width)),
    }


def _v8_record():
    from tests.test_bfcl_evict_v3 import _record

    record = _record("v8")
    record.update(schema=6, run_identity_sha256="0" * 64)
    record["turn_facts"] = [
        {"turn": 1, "pressure_triggered": True, "pin_overflow_total": False}
    ]
    for arm_row in record["arms"].values():
        turn = arm_row["turns"][0]
        turn.update(
            position_overflow=False,
            repeated_call=False,
            chat_control_echo=False,
            overflow_phase=None,
            na=False,
        )
        turn["eviction"].update(
            columns_after=1003,
            pin_overflow_total=False,
            match_impossible=False,
            echo_token_delta=0,
            pressure_triggered=True,
            pinned_columns_by_role={"user": 2, "tool": 1},
            control_role_shortfall=False,
            role_column_deltas={"user": 0, "tool": 0},
            current_turn_prefilled_before_eviction=False,
            protected_prefix_survived=True,
        )
        arm_row["selector"]["turns"] = [
            {
                "current_user_message_index": 3,
                "candidate_message_indices": [0, 1],
            }
        ]
    return record


def test_fv6_1_supplements_the_short_role_not_the_aggregate():
    from stencil.bfcl import build_matched_control

    user = _selected("user", "selected user", 0, 10, 4)
    tool = _selected("tool", "selected tool", 10, 128, 4)
    rows = [
        user,
        tool,
        _candidate("user", "wide user", 200, 100, 3),
        _candidate("tool", "tool one", 300, 50, 3),
        _candidate("tool", "tool two", 350, 50, 2),
        _candidate("tool", "tool three", 400, 50, 1),
    ]
    result = build_matched_control(rows, [user, tool], (0, 500))
    assert result["match_impossible"] is False
    assert result["role_counts"] == {"user": 10, "tool": 128}


def test_fv6_1_dev_and_sealed_paths_reject_usable_role_mismatch():
    from scripts.bfcl_mt import assert_dev_invariants
    from stencil.bfcl import assert_case_record_schema

    record = _v8_record()
    record["arms"]["recency_pinned"]["turns"][0]["eviction"][
        "pinned_columns_by_role"
    ] = {"user": 1, "tool": 1}
    with pytest.raises(AssertionError, match="comparator_columns"):
        assert_dev_invariants([record])
    with pytest.raises(ValueError, match="comparator column"):
        assert_case_record_schema(record)


def test_fv6_2_full_initial_overflow_is_na_but_within_turn_is_failure():
    from stencil.bfcl import position_overflow_result

    initial = position_overflow_result("full", 40961, phase="initial_prompt")
    within = position_overflow_result("full", 40961, phase="within_generation")
    assert initial["na"] is True
    assert initial["truncated"] is False
    assert initial["pass"] is False
    assert within["na"] is False
    assert within["truncated"] is True
    assert within["pass"] is False


def test_fv6_3_echo_clamp_pads_last_entry_from_source(qwen_tok):
    from scripts.bfcl_mt import _echo_clamp, _echo_current_user, render_prompt
    from stencil.bfcl import context_layout

    source = "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda"
    messages = [
        {"role": "user", "content": source},
        {"role": "assistant", "content": "ok"},
        {"role": "user", "content": "now"},
    ]
    context = render_prompt(messages, [])
    layout = context_layout(qwen_tok, context, messages, current_message_index=2)
    low, high = layout["evict_range"]
    columns = list(range(low, high))
    short = max(1, len(columns) // 3)
    row = {
        **_candidate(
            "user",
            qwen_tok.decode(qwen_tok.encode(context).ids[low : low + short]),
            low,
            high - low,
            0,
        ),
        "pinned_columns": columns[:short],
        "_echo_source_columns": columns,
    }
    baseline = len(
        qwen_tok.encode(
            _echo_current_user(context, [row], close=layout["current_user_close"])
        ).ids
    ) - len(qwen_tok.encode(context).ids)
    full_row = dict(row, text=qwen_tok.decode(qwen_tok.encode(context).ids[low:high]))
    target = len(
        qwen_tok.encode(
            _echo_current_user(context, [full_row], close=layout["current_user_close"])
        ).ids
    ) - len(qwen_tok.encode(context).ids)
    chosen, tokens, residual = _echo_clamp(
        qwen_tok,
        [row],
        context,
        layout["current_user_close"],
        target_tokens=target,
    )
    assert tokens > baseline
    assert abs(target - tokens) <= 16
    assert residual == target - tokens
    assert chosen[-1]["pinned_columns"] == columns[:short]


def test_fv6_4_preflight_invariants_report_comparator_event_counts():
    from scripts.bfcl_mt import assert_dev_invariants

    record = _v8_record()
    control = record["arms"]["clf_control"]["turns"][0]["eviction"]
    control.update(match_impossible=True, control_role_shortfall=True)
    record["arms"]["recency_pinned"]["turns"][0]["eviction"][
        "echo_token_delta"
    ] = -2
    events = assert_dev_invariants([record])
    assert events["match_impossible"] == {
        "clf_control": 1,
        "recency_pinned": 0,
        "tool_swap_echo": 0,
    }
    assert events["shortfall_counts"]["clf_control"] == 1
    assert events["delta_counts"] == {
        "clf_control": 0,
        "recency_pinned": 1,
        "tool_swap_echo": 0,
    }


def test_fv6_5_git_provenance_and_fv6_6_stable_tie_break(monkeypatch):
    from scripts import bfcl_mt

    provenance = bfcl_mt.git_provenance()
    expected_head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert provenance["commit"] == expected_head
    assert isinstance(provenance["dirty"], bool)
    assert "control_seed" not in bfcl_mt.certificate_payload(
        {
            "trunk": "1.7b",
            "arms": [],
            "control_tie_break": "nearest-width, nearest-turn, stable-source",
        },
        {},
    )["constants"]
    assert bfcl_mt.CONTROL_TIE_BREAK == "nearest-width, nearest-turn, stable-source"

    monkeypatch.setattr(
        bfcl_mt,
        "git_provenance",
        lambda: {"commit": "f" * 40, "dirty": True, "status": " M tracked.py"},
    )
    with pytest.raises(RuntimeError, match="clean git worktree"):
        bfcl_mt.assert_clean_git_for_sealed()
    monkeypatch.setattr(
        bfcl_mt,
        "_load_cases_verified",
        lambda *args, **kwargs: pytest.fail("sealed loader ran before git refusal"),
    )
    with pytest.raises(RuntimeError, match="clean git worktree"):
        bfcl_mt.artifact_meta(type("Args", (), {"split": "sealed"})())


def test_fv6_1_real_dev_census_selects_users_on_every_evicting_turn(qwen_tok):
    """Every one of the registered 11 dev evictions exercises USER matching."""
    from scripts.bfcl_mt import (
        K,
        _turn_plan,
        build_teacher_history,
        load_cases,
        render_prompt,
    )
    from stencil.bfcl import context_layout, prepare_case

    evicting = user_selected = 0
    census = []
    for category, raw_case, ground_truth in load_cases("dev"):
        case = prepare_case(raw_case, ROOT / "data/bench/bfcl_v3_mt/function_docs")
        for turn_index in range(1, len(ground_truth)):
            messages = build_teacher_history(
                case, ground_truth, turn_index, f"v8_census_{category}_{turn_index}"
            )
            messages.extend(case["question"][turn_index])
            current_index = max(
                index for index, row in enumerate(messages) if row["role"] == "user"
            )
            layout = context_layout(
                qwen_tok,
                render_prompt(messages, case["function"]),
                messages,
                current_message_index=current_index,
            )
            if layout["history_end"] <= K:
                continue
            evicting += 1

            def scorer(texts, *, role, contexts):
                del contexts
                return [0.9 if role == "user" else 0.1 for _ in texts]

            treatment = _turn_plan(
                qwen_tok, messages, case["function"], "clf_pinned_echo", scorer, 0
            )["selector"]
            assert treatment["pinned_columns_by_role"]["user"] > 0
            user_selected += 1
            for arm in ("clf_control", "recency_pinned", "tool_swap_echo"):
                comparator = _turn_plan(
                    qwen_tok, messages, case["function"], arm, scorer, 0
                )["selector"]
                if not comparator["match_impossible"]:
                    if arm == "clf_control" and comparator[
                        "control_role_shortfall_event"
                    ]:
                        comparator_total = sum(
                            comparator["pinned_columns_by_role"].values()
                        )
                        treatment_total = sum(
                            treatment["pinned_columns_by_role"].values()
                        )
                        assert comparator_total == treatment_total
                    else:
                        assert comparator["pinned_columns_by_role"] == treatment[
                            "pinned_columns_by_role"
                        ]
                    assert abs(comparator["echo_token_delta"]) <= 16
                census.append(
                    {
                        "case": str(raw_case["id"]),
                        "turn": turn_index,
                        "arm": arm,
                        "treatment": treatment["pinned_columns_by_role"],
                        "comparator": comparator["pinned_columns_by_role"],
                        "shortfall": comparator["control_role_shortfall_event"],
                        "impossible": comparator["match_impossible"],
                    }
                )
    assert (evicting, user_selected) == (11, 11)
    assert len(census) == 33
    print("FV6 census per-turn per-role:", census)
