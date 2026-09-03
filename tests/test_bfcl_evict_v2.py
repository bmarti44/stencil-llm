"""CPU-only contracts for the BFCL LEG A selector-v2 eviction harness."""

from __future__ import annotations

import copy

import pytest

from stencil.bfcl import ensure_split_allowed


@pytest.fixture(scope="module")
def tok():
    from tokenizers import Tokenizer

    return Tokenizer.from_file("models/qwen3-1.7b-hf/tokenizer.json")


def _columns(spans):
    return {column for start, end in spans for column in range(start, end)}


def test_layout_protects_system_tools_and_sinks_before_current_user(tok):
    from scripts.bfcl_mt import render_prompt
    from stencil.bfcl import context_layout

    messages = [
        {"role": "system", "content": "Never reveal the secret."},
        {"role": "user", "content": "Remember alpha."},
        {"role": "assistant", "content": "I will."},
        {"role": "tool", "content": "alpha=17"},
        {"role": "user", "content": "What is alpha?"},
    ]
    tools = [{"name": "lookup", "description": "Find a value", "parameters": {}}]
    prompt = render_prompt(messages, tools)
    layout = context_layout(tok, prompt)
    ids = tok.encode(prompt).ids

    protected = tok.decode(ids[slice(*layout["protected_prefix"])])
    evictable = tok.decode(ids[slice(*layout["evict_range"])])
    assert layout["protected_prefix"][0] == 0
    assert layout["protected_prefix"][1] >= 4
    assert "Never reveal the secret." in protected
    assert "<tools>" in protected and "lookup" in protected and "</tools>" in protected
    assert layout["evict_range"][0] == layout["protected_prefix"][1]
    assert "Remember alpha." in evictable and "alpha=17" in evictable
    assert "What is alpha?" not in evictable


def test_two_stage_prefill_evicts_before_current_turn():
    import torch

    from stencil.qwen3 import prefill_with_eviction

    events = []

    class Cache:
        def __init__(self):
            self.length = 0
            self.k = [None]

        def evict(self, lo, hi, keep=()):
            events.append(("evict", self.length, lo, hi, tuple(keep)))
            assert self.length == 5
            assert 90 not in trunk.seen
            self.k[0] = self.k[0][:, :, :3]
            return {0: 0, 3: 1, 4: 2}

    class Trunk:
        def __init__(self):
            self.seen = []

        def __call__(self, tokens, *, cache):
            values = tokens[0].tolist()
            events.append(("prefill", values, cache.length))
            self.seen.extend(values)
            cache.length += len(values)
            cache.k[0] = torch.zeros(1, 1, len(self.seen), 1)
            return torch.tensor([[[float(value)] for value in values]])

    trunk = Trunk()
    cache = Cache()
    _, _, before, after = prefill_with_eviction(
        trunk,
        cache,
        torch.tensor([[1, 2, 3, 4, 5, 90, 91]]),
        history_end=5,
        evict_range=(1, 3),
        keep=(),
    )
    assert events == [
        ("prefill", [1, 2, 3, 4, 5], 0),
        ("evict", 5, 1, 3, ()),
        ("prefill", [90, 91], 5),
    ]
    assert (before, after) == (5, 3)


def test_selector_scores_prior_user_and_all_tool_lines_without_context(tok):
    from scripts.bfcl_mt import render_prompt
    from stencil.bfcl import select_history_spans

    tool_lines = [f"line-{index} " + ("x" * index) for index in range(42)]
    messages = [
        {"role": "user", "content": "Keep alpha. Ignore drizzle."},
        {"role": "assistant", "content": "Calling."},
        {"role": "tool", "content": "\n".join(tool_lines)},
        {"role": "user", "content": "Use the earlier result."},
    ]
    prompt = render_prompt(messages, [])
    calls = []

    def scorer(texts, *, role, contexts):
        calls.append((list(texts), role, list(contexts)))
        return [0.9 if text.startswith(("Keep", "line-41")) else 0.1 for text in texts]

    selected, candidates, dropped = select_history_spans(tok, prompt, messages, scorer)
    assert [call[1] for call in calls] == ["user", "tool"]
    assert all(context == "" for texts, _, contexts in calls for context in contexts)
    assert calls[0][0] == ["Keep alpha.", "Ignore drizzle."]
    assert len(calls[1][0]) == 42
    assert calls[1][0][:2] == tool_lines[:2]
    assert {row["role"] for row in candidates} == {"user", "tool"}
    assert [(row["role"], row["text"]) for row in selected] == [
        ("user", "Keep alpha."),
        ("tool", tool_lines[41]),
    ]
    assert dropped == 0


def test_budget_stops_when_next_whole_span_does_not_fit():
    from stencil.bfcl import budget_history_spans

    candidates = [
        {"role": "user", "turn": 1, "score": 0.9, "span": [2, 8]},
        {"role": "tool", "turn": 3, "score": 0.8, "span": [20, 26]},
        {"role": "user", "turn": 2, "score": 0.8, "span": [10, 16]},
    ]
    kept, pins, budget = budget_history_spans(candidates, (0, 40), fraction=0.25)
    assert budget == 10
    assert _columns(pins) == set(range(2, 8))
    assert [row["turn"] for row in kept] == [1]
    assert kept[-1]["pinned_columns"] == list(range(2, 8))


def test_same_role_control_matches_exact_user_tool_proportions():
    from stencil.bfcl import same_role_control_spans

    candidates = [
        {"role": "user", "span": [0, 20]},
        {"role": "tool", "span": [20, 40]},
    ]
    kept = [
        {"role": "user", "pinned_columns": [0, 1, 2]},
        {"role": "tool", "pinned_columns": [20, 21]},
    ]
    control, counts = same_role_control_spans(candidates, kept, (0, 40), seed=7)
    assert counts == {"user": 3, "tool": 2}
    assert len(_columns(control)) == 5
    assert not (_columns(control) & {0, 1, 2, 20, 21})
    assert sum(column < 20 for column in _columns(control)) == 3
    assert sum(column >= 20 for column in _columns(control)) == 2


def _turn(passed=True, *, invalid=False):
    return {
        "turn": 1,
        "responses": [{"token_ids": [1, 2, 3]}],
        "tool_calls": [{"valid": not invalid}],
        "timeout": False,
        "truncated": False,
        "degenerate": False,
        "pass": passed,
        "eviction": {
            "evicted": True,
            "columns_before": 9000,
            "columns_after": 1000,
            "pinned_columns": 10,
            "evictable_size": 8000,
        },
    }


def _arm(passed=True, *, invalid=False):
    return {
        "turns": [_turn(passed, invalid=invalid)],
        "evicted": True,
        "echo_tokens_added": 0,
        "echo_copy": False,
        "selector": {"candidates": 4, "kept": 2, "budget": 10, "used": 10},
        "seconds": 1.0,
        "final_pass": passed,
        "final_score": {"valid": passed},
    }


def _record(case_id="case-0", category="long_context"):
    from stencil.bfcl import ARMS

    return {
        "schema": 2,
        "case_id": case_id,
        "category": category,
        "arms": {arm: _arm() for arm in ARMS},
        "seconds": 6.0,
    }


def test_record_schema_dry_assert_requires_all_six_arms_and_eviction_fields():
    from stencil.bfcl import assert_case_record_schema

    record = _record()
    assert_case_record_schema(record)
    broken = copy.deepcopy(record)
    broken["arms"].pop("full")
    with pytest.raises(ValueError, match="arms"):
        assert_case_record_schema(broken)
    broken = copy.deepcopy(record)
    broken["arms"]["base"]["turns"][0]["eviction"].pop("evictable_size")
    with pytest.raises(ValueError, match="eviction"):
        assert_case_record_schema(broken)


def test_summary_reports_categories_primary_contrasts_holm_and_safety():
    from stencil.bfcl import summarize_records

    records = [_record(f"long-{index}") for index in range(4)]
    records.append(_record("base-0", category="base"))
    for record in records[:4]:
        record["arms"]["base"] = _arm(False)
        record["arms"]["clf_control"] = _arm(False)
        record["arms"]["role_pinned"] = _arm(False)
        record["arms"]["full"] = _arm(True)
        record["arms"]["clf_pinned_echo"] = _arm(True)
    summary = summarize_records(records)
    assert summary["cases"] == 5
    assert summary["primary"]["unit"] == "teacher_forced_evicting_turn"
    assert summary["primary"]["arms"]["clf_pinned_echo"]["per_turn_pass"]["rate"] == 1.0
    assert summary["categories"]["base"]["arms"]["base"]["final_pass"]["n"] == 1
    assert summary["contrasts"]["a1_echo_minus_control"]["mean_points"] == 80.0
    assert summary["contrasts"]["a2_echo_minus_recency"]["mean_points"] == 0
    assert summary["contrasts"]["a3_half_gap_recovery"]["mean_points"] == 40.0
    assert set(summary["holm"]) == {
        "a1_echo_minus_control",
        "a2_echo_minus_recency",
        "a3_half_gap_recovery",
    }
    assert summary["safety"]["intact"] is True


def test_sealed_guard_still_refuses_without_environment(monkeypatch):
    monkeypatch.delenv("STENCIL_SEALED_RUN", raising=False)
    with pytest.raises(PermissionError, match="STENCIL_SEALED_RUN=1"):
        ensure_split_allowed("sealed")
