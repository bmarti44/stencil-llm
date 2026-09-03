"""CPU regressions for the late-arriving fable harness-v8 review."""

from __future__ import annotations

import pytest


def test_fv8_2_total_columns_not_resource_count_controls_impossibility():
    from stencil.bfcl import build_matched_control

    kept = [
        {
            "role": "user",
            "text": f"u{i}",
            "span": [i * 10, i * 10 + 10],
            "turn": i,
            "message_index": i,
            "pinned_columns": list(range(i * 10, i * 10 + 10)),
        }
        for i in range(18)
    ]
    candidates = [
        {"role": "tool", "text": f"t{i}", "span": [200 + i * 128, 328 + i * 128],
         "turn": i, "message_index": 30 + i}
        for i in range(16)
    ] + kept
    result = build_matched_control(candidates, kept, (0, 3000))
    assert result["match_impossible"] is False
    assert result["control_role_shortfall"] is True
    assert sum(result["role_counts"].values()) == 180


def test_fv8_3_nonpressure_echo_delta_allowed_but_pressure_refused():
    from stencil.bfcl import assert_case_record_schema
    from tests.test_bfcl_evict_v8 import _v8_record

    record = _v8_record()
    turn = record["arms"]["clf_control"]["turns"][0]
    turn["eviction"]["echo_token_delta"] = 17
    for arm in record["arms"].values():
        arm["turns"][0]["eviction"]["pressure_triggered"] = False
    record["turn_facts"][0]["pressure_triggered"] = False
    assert_case_record_schema(record)
    for arm in record["arms"].values():
        arm["turns"][0]["eviction"]["pressure_triggered"] = True
    record["turn_facts"][0]["pressure_triggered"] = True
    with pytest.raises(ValueError, match="echo token delta"):
        assert_case_record_schema(record)


def test_fv8_4_echo_clamp_measurement_is_local_and_exact():
    from scripts.bfcl_mt import _echo_clamp, _echo_current_user

    class Tok:
        def encode(self, text):
            if text.startswith("H" * 10000):
                raise AssertionError("full context was re-encoded")
            return type("E", (), {"ids": list(text.encode())})()

        def decode(self, ids):
            return bytes(ids).decode()

    prefix = "H" * 10000
    context = prefix + "<|im_start|>user\nnow<|im_end|>"
    close = context.index("<|im_end|>")
    row = {"role": "user", "text": "old", "span": [0, 3], "pinned_columns": [0, 1, 2]}
    chosen, tokens, residual = _echo_clamp(
        Tok(), [row], context, close, target_tokens=200,
        context_ids=list(context.encode()),
    )
    local_base = context[context.rfind("<|im_start|>user\n", 0, close + 1) :]
    local_echo = _echo_current_user(context, chosen, close=close)[
        -len(local_base) - tokens :
    ]
    assert len(local_echo.encode()) - len(local_base.encode()) == tokens
    assert residual == 200 - tokens


def test_fv8_6_manifest_includes_scripts_package_and_rejects_bench(monkeypatch):
    import sys

    from scripts import bfcl_mt

    assert "scripts/__init__.py" in bfcl_mt.harness_manifest()["files"]
    monkeypatch.setitem(sys.modules, "stencil.bench", object())
    with pytest.raises(RuntimeError, match="stencil.bench"):
        bfcl_mt.harness_manifest()


def test_fv8_7_tool_swap_user_rows_keep_echo_source_columns():
    from stencil.bfcl import tool_swap_plan

    user = {"role": "user", "text": "u", "span": [0, 2], "turn": 0,
            "pinned_columns": [0, 1]}
    result = tool_swap_plan([user], [user], (0, 2))
    assert result["entries"][0]["_echo_source_columns"] == [0, 1]
