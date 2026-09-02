from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from stencil.g0 import (
    assert_g0_record,
    bm25_rank,
    build_candidate_spans,
    ensure_g0_path,
    match_null_spans,
    policy_recovery,
)


class ToyTokenizer:
    def encode(self, text: str):
        words = text.split()
        offsets = []
        cursor = 0
        for word in words:
            start = text.index(word, cursor)
            offsets.append((start, start + len(word)))
            cursor = start + len(word)
        return type(
            "Encoding", (), {"ids": list(range(len(words))), "offsets": offsets}
        )()


def _messages():
    roles = ("system", "user", "assistant", "tool")
    return [
        {
            "role": roles[i % len(roles)],
            "content": " ".join(f"m{i}w{j}." for j in range(18)),
            "token_start": i * 25,
            "turn": i,
        }
        for i in range(12)
    ]


def test_candidate_and_null_spans_are_deterministic_stratified_and_bounded():
    messages = _messages()
    first = build_candidate_spans(
        messages,
        ToyTokenizer(),
        seed=20260903,
        max_spans=12,
        min_tokens=4,
        max_tokens=8,
    )
    second = build_candidate_spans(
        messages,
        ToyTokenizer(),
        seed=20260903,
        max_spans=12,
        min_tokens=4,
        max_tokens=8,
    )
    assert first == second
    assert len(first) == 12
    assert {span["role"] for span in first} == {"system", "user", "assistant", "tool"}
    for span in first:
        message = messages[span["message_idx"]]
        assert message["token_start"] <= span["start"] < span["end"]
        assert span["end"] <= message["token_start"] + 18

    nulls = match_null_spans(first, messages, ToyTokenizer(), seed=20260903)
    assert len(nulls) == len(first)
    for candidate, null in zip(first, nulls, strict=True):
        assert null["role"] == candidate["role"]
        assert null["length_bucket"] == candidate["length_bucket"]
        assert null["age_bucket"] == candidate["age_bucket"]
        assert (null["start"], null["end"]) != (candidate["start"], candidate["end"])


def test_policy_recovery_arithmetic_and_null_adjustment():
    utilities = [2.0, -3.0, 1.0, 0.0]
    null_utilities = [0.5, 7.0, 0.25, -1.0]
    result = policy_recovery(utilities, [0, 2], null_utilities)
    assert result["recovery"] == pytest.approx(1.0)
    assert result["recovery_null_adj"] == pytest.approx(2.25 / 2.25)
    partial = policy_recovery(utilities, [0], null_utilities)
    assert partial["recovery"] == pytest.approx(2 / 3)
    assert partial["recovery_null_adj"] == pytest.approx(1.5 / 2.25)


def test_bm25_toy_ranking():
    docs = ["red apple orchard", "torque wrench garage", "green apple pie"]
    assert bm25_rank(docs, "apple pie") == [2, 0, 1]


def test_eval_data_guard_source_scan_and_runtime(tmp_path):
    root = Path(__file__).resolve().parents[1]
    for path in (root / "scripts/g0_oracle.py", root / "src/stencil/g0.py"):
        if path.exists():
            forbidden = "data" + "/" + "bench"
            assert forbidden not in path.read_text()
    ensure_g0_path(tmp_path / "data/g0/subset.jsonl")
    with pytest.raises(ValueError, match="evaluation-only"):
        ensure_g0_path(tmp_path / "data" / "bench" / "forbidden.jsonl")


def test_record_schema_dry_assert():
    span = {
        "role": "user",
        "start": 4,
        "end": 8,
        "n_tok": 4,
        "text_sha": "a" * 64,
        "utility": 0.2,
        "top1_agree": 0.75,
    }
    record = {
        "corpus": "chat",
        "id": "stub",
        "turn": 3,
        "n_context_tokens": 12,
        "spans": [span],
        "nulls": [dict(span)],
        "joint": {"span_idx": [0], "utility": 0.2, "sum_utility": 0.2},
        "policies": {
            "role_rule": {
                "kept_span_idx": [0],
                "recovery": 1.0,
                "recovery_null_adj": 1.0,
            }
        },
        "seconds": 1.2,
    }
    assert_g0_record(record)
    broken = json.loads(json.dumps(record))
    del broken["spans"][0]["top1_agree"]
    with pytest.raises(ValueError, match="top1_agree"):
        assert_g0_record(broken)


def test_script_import_has_no_side_effects():
    root = Path(__file__).resolve().parents[1]
    path = root / "scripts/g0_oracle.py"
    if not path.exists():
        pytest.skip("RED phase: script not implemented yet")
    spec = importlib.util.spec_from_file_location("g0_oracle", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
