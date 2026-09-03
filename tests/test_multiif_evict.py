"""CPU contract tests for the registered Multi-IF real-eviction harness."""

from __future__ import annotations

import json

import pytest


@pytest.fixture(scope="module")
def tok():
    from tokenizers import Tokenizer

    return Tokenizer.from_file("models/qwen3-1.7b-hf/tokenizer.json")


def _context():
    return (
        "<|im_start|>system\nKeep system policy.<|im_end|>\n"
        "<|im_start|>user\nKeep alpha. Ignore the weather.<|im_end|>\n"
        "<|im_start|>assistant\nEarlier answer.<|im_end|>\n"
        "<|im_start|>user\nKeep beta! Mere narrative.<|im_end|>\n"
        "<|im_start|>assistant\nAnother answer.<|im_end|>\n"
        "<|im_start|>user\nGive the final answer.<|im_end|>\n"
        "<|im_start|>assistant\n<think>\n\n</think>\n\n"
    )


def _columns(spans):
    return {column for start, end in spans for column in range(start, end)}


def test_eviction_layout_protects_system_and_first_four_columns(tok):
    from scripts.multiif_evict import context_layout

    context = _context()
    layout = context_layout(tok, context)
    ids = tok.encode(context).ids
    assert layout["context_token_ids"] == ids
    assert layout["protected_prefix"][0] == 0
    assert layout["protected_prefix"][1] >= 4
    protected = tok.decode(ids[slice(*layout["protected_prefix"])])
    assert "Keep system policy." in protected
    evicted = tok.decode(ids[slice(*layout["evict_range"])])
    assert "Keep alpha." in evicted and "Keep beta!" in evicted
    assert "Give the final answer." not in evicted
    assert layout["evict_range"][0] == layout["protected_prefix"][1]


def test_selector_scores_three_sentences_once_without_context(tok):
    from scripts.multiif_evict import select_prior_user_sentences

    calls = []

    def stub(texts, *, role, contexts):
        calls.append((list(texts), role, list(contexts)))
        return [0.9 if text.startswith("Keep") else 0.1 for text in texts]

    selected, candidates = select_prior_user_sentences(
        tok, _context(), stub, threshold=0.5
    )
    assert len(calls) == 1
    assert calls[0][1] == "user"
    assert calls[0][2] == [""] * 4
    assert [row["text"] for row in candidates] == [
        "Keep alpha.",
        "Ignore the weather.",
        "Keep beta!",
        "Mere narrative.",
    ]
    assert [row["text"] for row in selected] == ["Keep alpha.", "Keep beta!"]
    assert all(row["turn"] < 3 and 0 <= row["score"] <= 1 for row in candidates)
    ids = tok.encode(_context()).ids
    assert [tok.decode(ids[slice(*row["span"])]).strip() for row in selected] == [
        "Keep alpha.",
        "Keep beta!",
    ]


def test_control_is_built_after_clamp_and_matches_pinned_columns():
    from scripts.multiif_evict import clamp_and_match_control

    # Both spans cross an eviction boundary; only their post-clamp columns count.
    pinned, control = clamp_and_match_control([(1, 7), (18, 25)], (4, 20))
    assert pinned == [(4, 7), (18, 20)]
    assert len(_columns(control)) == len(_columns(pinned)) == 5
    assert not (_columns(control) & _columns(pinned))
    assert _columns(control) <= set(range(4, 20))


def _arm(bits, *, timeout=False, truncated=False, degenerate=False, invalid=False):
    return {
        "text": "answer",
        "generated_token_ids": [1],
        "n_generated": 1,
        "scores": {"all": bits, "aged": bits[:-1]},
        "safety": {
            "timed_out": timeout,
            "truncated": truncated,
            "degenerate": degenerate,
            "invalid": invalid,
        },
        "quoting": False,
    }


def _record(ci=0, bits=None):
    from scripts.multiif_evict import ARMS

    bits = bits or [True, True, True]
    return {
        "schema": 1,
        "ci": ci,
        "key": f"key-{ci}",
        "last_turn": 3,
        "context_token_ids": [1, 2, 3],
        "echo_context_token_ids": [1, 2, 3, 4],
        "protected_prefix": [0, 1],
        "evict_range": [1, 2],
        "selected_spans": [{"text": "rule", "score": 0.9, "span": [1, 2]}],
        "pinned_cols": {
            arm: (1 if "pinned" in arm or arm == "clf_control" else 0)
            for arm in ARMS
        },
        "control_spans": [[1, 2]],
        "arms": {arm: _arm(list(bits)) for arm in ARMS},
        "seconds": {"history": 0.1, "selector": 0.01, "arms": 0.2, "total": 0.31},
    }


def test_record_schema_dry_assert_rejects_missing_arm():
    from scripts.multiif_evict import assert_record_schema

    record = _record()
    assert_record_schema(record)
    record["arms"].pop("full")
    with pytest.raises(ValueError, match="arms"):
        assert_record_schema(record)


def test_summary_from_synthetic_records_reports_registered_contrasts():
    from scripts.multiif_evict import summarize_records

    records = [_record(i) for i in range(4)]
    for record in records:
        record["arms"]["full"] = _arm([True, True, True])
        record["arms"]["evicted"] = _arm([False, False, True])
        record["arms"]["clf_pinned"] = _arm([True, True, True])
        record["arms"]["clf_pinned_echo"] = _arm([True, True, True])
        record["arms"]["clf_control"] = _arm([False, False, True])
        record["arms"]["role_pinned"] = _arm([False, False, True])
    summary = summarize_records(records)
    assert summary["conversations"] == 4
    assert summary["arms"]["full"]["aged_pass"] == 8
    assert summary["arms"]["evicted"]["aged_pass"] == 0
    assert summary["contrasts"]["c1_echo_minus_control"]["mean_points"] == 100.0
    assert summary["contrasts"]["c2_classifier_minus_role"]["lower_bound"] > 0
    assert summary["contrasts"]["c3_half_gap_recovery"]["mean_points"] == 50.0
    assert set(summary["holm"]) == {
        "c1_echo_minus_control",
        "c2_classifier_minus_role",
        "c3_half_gap_recovery",
    }
    assert summary["safety"]["intact"] is True


def test_resume_preserves_existing_record_and_returns_only_missing(tmp_path):
    from scripts.multiif_evict import atomic_json, resume_indices

    path = tmp_path / "conv-000.json"
    original = _record()
    atomic_json(path, original)
    before = path.read_bytes()
    assert resume_indices(tmp_path, [(0, "key-0"), (1, "key-1")]) == [1]
    assert path.read_bytes() == before
    assert json.loads(path.read_text()) == original
