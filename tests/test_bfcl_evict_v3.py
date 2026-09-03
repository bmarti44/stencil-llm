"""CPU contracts for the BFCL LEG A registration-v3 harness."""

from __future__ import annotations

import pytest


@pytest.fixture(scope="module")
def qwen_tok():
    from tokenizers import Tokenizer

    return Tokenizer.from_file("models/qwen3-1.7b-hf/tokenizer.json")


def _columns(spans):
    return {column for start, end in spans for column in range(start, end)}


def test_message_index_split_keeps_tool_responses_in_prior_user_block(qwen_tok):
    from scripts.bfcl_mt import render_prompt
    from stencil.bfcl import context_layout

    messages = [
        {"role": "user", "content": "first request"},
        {
            "role": "assistant",
            "content": '<tool_call>{"name":"x","arguments":{}}</tool_call>',
        },
        {"role": "tool", "content": "tool result with <|im_start|>user text"},
        {"role": "user", "content": "second request"},
    ]
    prompt = render_prompt(messages, [])
    layout = context_layout(qwen_tok, prompt, messages, current_message_index=3)
    ids = qwen_tok.encode(prompt).ids
    evictable = qwen_tok.decode(ids[slice(*layout["evict_range"])])
    current = qwen_tok.decode(ids[layout["history_end"] :])
    assert "tool result" in evictable
    assert "second request" not in evictable
    assert "second request" in current


def test_protected_prefix_includes_complete_output_contract(qwen_tok):
    from scripts.bfcl_mt import render_prompt
    from stencil.bfcl import context_layout

    messages = [{"role": "user", "content": "go"}]
    prompt = render_prompt(messages, [{"name": "x", "parameters": {}}])
    layout = context_layout(qwen_tok, prompt, messages, current_message_index=0)
    protected = qwen_tok.decode(
        qwen_tok.encode(prompt).ids[slice(*layout["protected_prefix"])]
    )
    assert "For each function call" in protected
    assert "</tool_call>" in protected
    assert layout["protected_prefix"][1] == layout["history_end"]


def test_teacher_forced_context_ids_identical_across_arms_with_stub(qwen_tok):
    from scripts.bfcl_mt import teacher_forced_turn_contexts

    messages = [{"role": "user", "content": "turn zero"}]
    history = [
        {
            "role": "assistant",
            "content": '<tool_call>{"name":"lookup","arguments":{"q":"a"}}</tool_call>',
        },
        {"role": "tool", "content": "answer-a"},
    ]
    seen = []

    def trunk(ids, *, arm):
        seen.append((arm, tuple(ids)))
        return len(ids)

    contexts = teacher_forced_turn_contexts(
        qwen_tok,
        messages + history + [{"role": "user", "content": "turn one"}],
        [],
        ("base", "clf_pinned_echo", "full"),
        trunk,
    )
    assert len({tuple(row["context_ids"]) for row in contexts.values()}) == 1
    assert len({row[1] for row in seen}) == 1


def test_tool_lines_chunk_to_128_qwen_tokens_and_encoder_fit(qwen_tok):
    from transformers import AutoTokenizer

    from scripts.bfcl_mt import render_prompt
    from stencil.bfcl import select_history_spans

    text = " ".join(f"token{index}" for index in range(420))
    messages = [
        {"role": "user", "content": "old request"},
        {"role": "assistant", "content": "done"},
        {"role": "tool", "content": text},
        {"role": "user", "content": "new request"},
    ]
    prompt = render_prompt(messages, [])

    def scorer(texts, *, role, contexts):
        return [0.9] * len(texts)

    selected, candidates, dropped = select_history_spans(
        qwen_tok, prompt, messages, scorer
    )
    tool = [row for row in candidates if row["role"] == "tool"]
    assert len(tool) > 1
    assert all(len(qwen_tok.encode(row["text"]).ids) <= 128 for row in tool)
    assert "".join(row["text"] for row in tool).replace(" ", "") == text.replace(
        " ", ""
    )
    encoder = AutoTokenizer.from_pretrained("data/classifier/model/ft/encoder")
    assert max(len(encoder(f"[tool] {row['text']}").input_ids) for row in tool) <= 192
    assert selected == candidates
    assert dropped == 0


def test_control_shortfall_fills_other_role_and_echoes_own_spans():
    from stencil.bfcl import build_matched_control, render_echo

    candidates = [
        {"role": "user", "text": "u-selected", "span": [0, 3], "score": 0.9, "turn": 1},
        {"role": "user", "text": "u-free", "span": [3, 4], "score": 0.1, "turn": 1},
        {"role": "tool", "text": "tool-free", "span": [4, 7], "score": 0.1, "turn": 1},
    ]
    kept = [{**candidates[0], "pinned_columns": [0, 1, 2]}]
    control = build_matched_control(candidates, kept, (0, 12), seed=20260903)
    assert len(_columns(control["pins"])) == 3
    assert control["control_role_shortfall"] is True
    assert control["role_column_deltas"] == {"user": -3, "tool": 3}
    assert not (_columns(control["pins"]) & {0, 1, 2})
    echoed = render_echo(control["entries"])
    assert "Earlier context restated verbatim:" in echoed
    assert 'user: "u-free"' in echoed or 'tool: "tool-free"' in echoed


def test_control_echo_covers_exact_control_pins_under_same_cap(qwen_tok):
    from scripts.bfcl_mt import _turn_plan

    messages = [
        {"role": "user", "content": "Keep alpha. Ignore beta."},
        {"role": "assistant", "content": "done"},
        {"role": "tool", "content": "alpha=17\nbeta=19"},
        {"role": "user", "content": "answer now"},
    ]

    def scorer(texts, *, role, contexts):
        return [0.9 if "alpha" in text else 0.1 for text in texts]

    plan = _turn_plan(qwen_tok, messages, [], "clf_control", scorer, 20260903)
    echoed_columns = {
        column for row in plan["entries"] for column in row["pinned_columns"]
    }
    assert echoed_columns <= _columns(plan["keep"])
    assert abs(plan["selector"]["echo_token_delta"]) <= 16
    assert plan["selector"]["echo_tokens"] <= 1024


def test_pin_overflow_drops_newest_columns_first():
    from stencil.bfcl import clamp_pins_newest_first

    kept, dropped = clamp_pins_newest_first([(2, 5), (9, 12)], overflow=2)
    assert kept == [(2, 5), (9, 10)]
    assert dropped == 2


def test_recency_and_tool_swap_are_column_matched():
    from stencil.bfcl import recency_pinned_plan, tool_swap_plan

    candidates = [
        {
            "role": "user",
            "text": "old user",
            "span": [0, 4],
            "role_span": [0, 4],
            "turn": 1,
            "score": 0.9,
        },
        {
            "role": "tool",
            "text": "chosen tool",
            "span": [4, 7],
            "role_span": [4, 7],
            "turn": 1,
            "score": 0.9,
        },
        {
            "role": "tool",
            "text": "recent tool",
            "span": [7, 10],
            "role_span": [7, 10],
            "turn": 2,
            "score": 0.1,
        },
    ]
    kept = [
        {**candidates[0], "pinned_columns": [0, 1, 2, 3]},
        {**candidates[1], "pinned_columns": [4, 5, 6]},
    ]
    recency = recency_pinned_plan(candidates, classifier_columns=7, evict_range=(0, 10))
    assert _columns(recency["pins"]) == {*range(0, 4), *range(7, 10)}
    swapped = tool_swap_plan(candidates, kept, (0, 10), seed=20260903)
    assert _columns(swapped["pins"]) == set(range(0, 4))
    assert swapped["match_impossible"] is True


def _turn(
    passed=True,
    *,
    evicted=True,
    prompt=9000,
    invalid=False,
    degenerate=False,
):
    return {
        "turn": 1,
        "responses": [{"token_ids": [1], "columns_after_step": 10}],
        "tool_calls": [{"valid": not invalid}],
        "timeout": False,
        "truncated": False,
        "degenerate": degenerate,
        "pass": passed,
        "prompt_positions": prompt,
        "eviction": {
            "evicted": evicted,
            "columns_before": 9000,
            "columns_after": 1000,
            "pinned_columns": 3,
            "evictable_size": 8000,
            "budget_used": 3,
            "echo_tokens": 0,
            "pin_overflow": 0,
        },
    }


def _record(case_id, *, echo=True, base=False, full=True, full_prompt=9000):
    from stencil.bfcl import ARMS

    arms = {}
    for arm in ARMS:
        passed = echo if arm == "clf_pinned_echo" else True
        if arm in {"base", "clf_control", "recency_pinned", "tool_swap_echo"}:
            passed = base
        if arm == "full":
            passed = full
        turn = _turn(passed, prompt=full_prompt if arm == "full" else 9000)
        arms[arm] = {
            "turns": [turn],
            "evicted": arm != "full",
            "echo_tokens_added": 0,
            "echo_copy": False,
            "repeated_history_calls": 0,
            "selector": {"candidates": 1, "kept": 1, "budget": 3, "used": 3},
            "seconds": 1.0,
            "final_pass": passed,
            "final_score": {"valid": passed},
        }
    return {
        "schema": 3,
        "mode": "teacher",
        "case_id": case_id,
        "category": "long_context",
        "arms": arms,
        "seconds": 8.0,
    }


def test_per_turn_primary_a3_exclusion_and_safety_vacuity_guard():
    from stencil.bfcl import summarize_records

    records = [_record("a"), _record("b", full_prompt=50000)]
    summary = summarize_records(records)
    assert summary["primary"]["turns"] == 2
    assert summary["contrasts"]["a1_echo_minus_control"]["mean_points"] == 100.0
    assert summary["contrasts"]["a3_half_gap_recovery"]["clusters"] == 1
    assert summary["a3"]["excluded_over_40960"] == 1
    assert summary["a3"]["eligible"] is False
    assert summary["a3"]["k"] == 1
    assert summary["a3"]["status"] == "post-exclusion k<6; A3 uninformative"
    assert summary["safety"]["checks"]["base"]["timeouts_zero"] is True
    assert set(summary["safety"]["vacuity_guard"]) == {"degenerate"}
    records[0]["arms"]["base"]["turns"][0]["degenerate"] = True
    assert summarize_records(records)["safety"]["checks"]["base"]["passed"] is True


def test_registered_meta_refuses_constant_change(tmp_path, monkeypatch):
    from scripts.bfcl_mt import _check_or_write_meta

    path = tmp_path / "meta.json"
    registered = {"k": 8192, "chunk_tokens": 128, "echo_cap": 1024}
    _check_or_write_meta(path, registered)
    _check_or_write_meta(path, dict(registered))
    changed = dict(registered, k=4096)
    with pytest.raises(RuntimeError, match="registered constants"):
        _check_or_write_meta(path, changed)


def test_v3_sealed_guard(monkeypatch):
    from stencil.bfcl import ensure_split_allowed

    monkeypatch.delenv("STENCIL_SEALED_RUN", raising=False)
    with pytest.raises(PermissionError, match="STENCIL_SEALED_RUN=1"):
        ensure_split_allowed("sealed")
