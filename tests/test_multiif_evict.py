"""CPU contract tests for the registered Multi-IF real-eviction harness."""

from __future__ import annotations

import json
import subprocess
from types import SimpleNamespace

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
        "evict_range": [1, 3],
        "selected_spans": [{"text": "rule", "score": 0.9, "span": [1, 2]}],
        "control_impossible": False,
        "control_pinned_cols": 1,
        "control_available_cols": 1,
        "pinned_cols": {
            arm: (1 if "pinned" in arm or arm == "clf_control" else 0)
            for arm in ARMS
        },
        "control_spans": [[2, 3]],
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
    assert summary["contrasts"]["c1_echo_minus_control"]["n"] == 4
    assert summary["contrasts"]["c2_classifier_minus_role"]["lower_bound"] > 0
    assert summary["contrasts"]["c3_half_gap_recovery"]["mean_points"] == 50.0
    assert set(summary["holm"]) == {
        "c1_echo_minus_control",
        "c2_classifier_minus_role",
        "c3_half_gap_recovery",
    }
    assert summary["safety"]["intact"] is True


def test_control_shortfall_skips_only_control_and_c1(monkeypatch):
    import scripts.multiif_evict as harness
    import stencil.ledger

    class Encoding:
        ids = [10, 11, 12]

    class Tokenizer:
        def encode(self, _text):
            return Encoding()

    monkeypatch.setattr(
        harness,
        "_turn_doc",
        lambda _row, turn: (f"prompt {turn}", ["instruction"], [{}]),
    )
    monkeypatch.setattr(
        harness,
        "_generate_history",
        lambda *_args: ("history", {"generations": [], "seconds": 0.0}),
    )
    monkeypatch.setattr(
        harness,
        "context_layout",
        lambda *_args: {
            "context_token_ids": [10, 11, 12],
            "protected_prefix": (0, 0),
            "evict_range": (0, 3),
        },
    )
    monkeypatch.setattr(
        harness,
        "select_prior_user_sentences",
        lambda *_args: (
            [{"text": "keep", "turn": 1, "score": 0.9, "span": [0, 2]}],
            [],
        ),
    )
    monkeypatch.setattr(harness, "role_pinned_spans", lambda *_args: [(0, 2)])
    monkeypatch.setattr(
        stencil.ledger, "text_ledger_context", lambda context, _: context
    )
    monkeypatch.setattr(stencil.ledger, "render_text_ledger", lambda _entries: "")
    called = []

    def fake_run_arm(_model, _tokenizer, _ids, *, keep, **_kwargs):
        called.append(tuple(keep))
        return {
            "text": "answer",
            "generated_token_ids": [1],
            "n_generated": 1,
            "timed_out": False,
            "truncated": False,
            "degenerate": False,
            "invalid": False,
            "pinned_cols": sum(end - start for start, end in keep),
        }

    monkeypatch.setattr(harness, "run_arm", fake_run_arm)
    monkeypatch.setattr(
        harness,
        "_score_fields",
        lambda *_args: {"all": [True], "aged": [True]},
    )

    row = {"key": "short", **{f"turn_{turn}_prompt": "x" for turn in (1, 2, 3)}}
    record = harness.evaluate_conversation(
        object(),
        Tokenizer(),
        object(),
        row,
        145,
        SimpleNamespace(max_new=1, deadline=1),
    )

    assert len(called) == len(harness.ARMS) - 1
    assert record["control_impossible"] is True
    assert record["control_pinned_cols"] == 2
    assert record["control_available_cols"] == 1
    assert record["control_spans"] is None
    assert record["pinned_cols"]["clf_control"] is None
    assert record["arms"]["clf_control"] is None
    assert all(
        record["arms"][arm] is not None
        for arm in harness.ARMS
        if arm != "clf_control"
    )

    records = [_record(i) for i in range(4)] + [record]
    summary = harness.summarize_records(records)
    assert summary["n_control_impossible"] == 1
    assert summary["c1_population"] == 4
    assert summary["contrasts"]["c1_echo_minus_control"]["n"] == 4
    assert summary["contrasts"]["c2_classifier_minus_role"]["n"] == 5
    assert summary["contrasts"]["c3_half_gap_recovery"]["n"] == 5
    assert summary["arms"]["full"]["aged_n"] == 9


def test_resume_preserves_existing_record_and_returns_only_missing(tmp_path):
    from scripts.multiif_evict import atomic_json, resume_indices

    path = tmp_path / "conv-000.json"
    original = _record()
    atomic_json(path, original)
    before = path.read_bytes()
    assert resume_indices(tmp_path, [(0, "key-0"), (1, "key-1")]) == [1]
    assert path.read_bytes() == before
    assert json.loads(path.read_text()) == original


def test_two_stage_prefill_evicts_before_current_turn_and_keeps_positions():
    import torch

    from scripts.multiif_evict import prefill_for_generation

    events = []

    class Cache:
        def __init__(self):
            self.length = 0
            self.k = [None]

        def evict(self, lo, hi, keep=()):
            events.append(("evict", self.length, lo, hi, tuple(keep)))
            assert self.length == 4
            assert 50 not in trunk.seen and 51 not in trunk.seen
            self.k[0] = self.k[0][:, :, :2]
            return {0: 0, 3: 1}

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
    logits, _, before, after = prefill_for_generation(
        trunk,
        cache,
        torch.tensor([[10, 11, 12, 13, 50, 51]]),
        history_end=4,
        evict_range=(1, 3),
        keep=(),
    )
    assert events == [
        ("prefill", [10, 11, 12, 13], 0),
        ("evict", 4, 1, 3, ()),
        ("prefill", [50, 51], 4),
    ]
    assert cache.length == 6
    assert (before, after) == (4, 2)
    assert logits[0, -1, 0].item() == 51


def _gpu_idle() -> tuple[bool, str]:
    try:
        import torch

        if not torch.cuda.is_available():
            return False, "CUDA unavailable"
        result = subprocess.run(
            ["nvidia-smi", "--query-compute-apps=pid", "--format=csv,noheader"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (ImportError, FileNotFoundError, subprocess.CalledProcessError) as exc:
        return False, f"GPU idle check unavailable: {exc}"
    if result.stdout.strip():
        return False, f"GPU busy (compute PIDs: {result.stdout.strip()})"
    return True, ""


def test_full_two_stage_prefill_logits_bitwise_equal_one_shot(tok):
    idle, reason = _gpu_idle()
    if not idle:
        pytest.skip(reason)

    import torch

    from scripts.multiif_evict import context_layout, prefill_for_generation
    from stencil.qwen3 import KVCache, Qwen3

    model = Qwen3()
    model.load_state_dict(
        torch.load("models/qwen3-1.7b.pt", map_location="cpu", weights_only=True)
    )
    model = model.to(torch.bfloat16).cuda().eval()
    layout = context_layout(tok, _context())
    tokens = torch.tensor([layout["context_token_ids"]], device="cuda")
    with torch.no_grad():
        one_shot = model(tokens, cache=KVCache(model.cfg))[:, -1]
        two_stage, _, _, _ = prefill_for_generation(
            model,
            KVCache(model.cfg),
            tokens,
            history_end=layout["evict_range"][1],
            evict_range=None,
            keep=(),
        )
    assert torch.equal(two_stage[:, -1], one_shot)


def test_meta_records_prequery_and_rejects_other_timing(tmp_path):
    from scripts.multiif_evict import _check_or_write_meta

    path = tmp_path / "meta.json"
    _check_or_write_meta(path, {"eviction_timing": "pre-query"})
    with pytest.raises(RuntimeError, match="resume provenance mismatch"):
        _check_or_write_meta(path, {"eviction_timing": "post-prefill"})


def test_default_output_directory_is_registered_prequery_name():
    from scripts.multiif_evict import parse_args

    assert parse_args([]).out == "multiif-evict-909-prequery-v2"
