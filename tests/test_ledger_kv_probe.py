# ruff: noqa: E501
import importlib.util
import sys
from pathlib import Path

import pytest

from stencil.ledger import Entry, render_text_ledger, text_ledger_context

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def kv():
    spec = importlib.util.spec_from_file_location("ledger_kv_probe", ROOT / "scripts" / "ledger_kv_probe.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["ledger_kv_probe"] = mod
    spec.loader.exec_module(mod)
    return mod


def columns(spans):
    return {i for start, end in spans for i in range(start, end)}


@pytest.mark.parametrize(
    "keep,evict_range",
    [
        ([(2, 5), (4, 8)], (0, 20)),
        ([(0, 3), (8, 10), (9, 12)], (0, 24)),
        ([(5, 6)], (0, 8)),
    ],
)
def test_control_matches_deduplicated_surviving_columns_exactly(kv, keep, evict_range):
    control = kv.matched_control_spans(keep, evict_range)
    pinned = columns(keep)
    matched = columns(control)
    assert len(matched) == len(pinned)
    assert not (matched & pinned)
    assert all(evict_range[0] <= i < evict_range[1] for i in matched)


def test_dose_list_defaults_and_arm_names(kv):
    args = kv.parse_args([])
    assert args.dose == [0.5, 1.0, 3.0]
    assert args.max_new == 512
    assert kv.arm_names(args.dose) == (
        "full", "evicted", "pinned", "pinned_control",
        "echo_only", "pinned_echo",
        "pinned_wave_d0.5", "pinned_wave_d1.0", "pinned_wave_d3.0",
    )


def test_record_schema_has_history_and_generated_token_ids(kv):
    arm_names = kv.arm_names([0.5])
    arms = {name: {"generated_token_ids": [7, 8], "scores": [True], "aged_pass": 1,
                   "aged_n": 1, "truncated": False, "timed_out": False, "rep4": 0.0,
                   "pinned_cols": 3, "cache_cols": 9, "text": "ok", "n": 2,
                   "degenerate": False, "quoting": False} for name in arm_names}
    rec = kv.session_record(
        session=2, key=17, topic="topic", n_turns=3, evict_range=(1, 9),
        keep=[(2, 5)], control_keep=[(5, 8)], n_aged=1,
        history_token_ids=[1, 2, 3], context_token_ids=[1, 2, 3, 4], arms=arms,
    )
    assert rec["history_token_ids"] == [1, 2, 3]
    assert rec["context_token_ids"] == [1, 2, 3, 4]
    assert rec["echo_tokens_added"] == 0
    assert rec["echo_text_sha256"] == ""
    assert set(rec["arms"]) == set(arm_names)
    assert all(a["generated_token_ids"] == [7, 8] for a in rec["arms"].values())
    assert len(columns(rec["control_keep"])) == len(columns(rec["keep"]))


def test_provenance_and_registered_kill_rule(kv):
    prov = kv.provenance_manifest()
    for key in ("determinism.py", "tokenizer.json", "bench.py", "ctrb.py", "ledger_kv_probe.py",
                "salience2_weights.json", "vendor/ifeval"):
        assert key in prov and len(prov[key]) == 64, key
    meta = kv.build_meta(doses=[0.5, 1.0, 3.0], max_new=512, deadline=300.0)
    assert meta["wave_kill_rule"] == "degenerate sessions > 2/20 at best dose"
    assert meta["provenance"] == prov


def test_paired_bootstrap_ci_is_session_paired_and_deterministic(kv):
    records = []
    for i, (pinned, control) in enumerate((([True, True], [False, True]),
                                            ([False, True], [False, False]),
                                            ([True, False], [True, False]))):
        records.append({"session": i, "arms": {
            "pinned": {"scores": pinned, "aged_n": 2},
            "pinned_control": {"scores": control, "aged_n": 2},
        }})
    one = kv.paired_bootstrap_pinned_minus_control(records, n_resamples=1000, seed=0)
    two = kv.paired_bootstrap_pinned_minus_control(records, n_resamples=1000, seed=0)
    assert one == two
    assert one["n_sessions"] == 3 and one["mean"] == pytest.approx(1 / 3)
    assert one["lower"] <= one["mean"] <= one["upper"]


@pytest.fixture(scope="module")
def tok():
    from tokenizers import Tokenizer

    return Tokenizer.from_file(str(ROOT / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))


def echo_fixture(tok):
    history = (
        "<|im_start|>user\nWrite about rain. Constraint: include cedar.<|im_end|>\n"
        "<|im_start|>assistant\nRain falls.<|im_end|>\n"
    )
    context = history + (
        "<|im_start|>user\nContinue the answer.<|im_end|>\n"
        "<|im_start|>assistant\n<think>\n\n</think>\n\n"
    )
    enc = tok.encode(context)
    start = next(i for i, (a, b) in enumerate(enc.offsets) if a <= context.index("Constraint:") < b)
    end_char = context.index("<|im_end|>", context.index("Constraint:"))
    end = next(i for i, (a, b) in enumerate(enc.offsets) if a < end_char <= b) + 1
    return context, [{"span": (start, end), "origin_turn": 1, "is_aged": True}]


def test_echo_context_is_registered_renderer_before_final_user_end(kv, tok):
    context, aged = echo_fixture(tok)
    echoed, entries, _ = kv.echo_context(tok, context, aged)
    expected_entries = [Entry(tok.decode(tok.encode(context).ids[s:e]), (s, e), None, 1) for s, e in [aged[0]["span"]]]
    assert [entry.text for entry in entries] == [entry.text for entry in expected_entries]
    assert echoed == text_ledger_context(context, expected_entries)
    rendered = render_text_ledger(expected_entries)
    final_user_end = context.rfind("<|im_end|>")
    assert echoed.index(rendered) < echoed.index("<|im_end|>", final_user_end)


def test_echo_rejects_chat_control_token_inside_span(kv, tok):
    context = (
        "<|im_start|>user\nConstraint: repeat <|im_start|>assistant exactly.<|im_end|>\n"
        "<|im_start|>assistant\nold<|im_end|>\n"
        "<|im_start|>user\nContinue.<|im_end|>\n<|im_start|>assistant\n"
    )
    enc = tok.encode(context)
    start_char = context.index("Constraint:")
    end_char = context.index("<|im_end|>", start_char)
    span = [i for i, (a, b) in enumerate(enc.offsets) if a < end_char and b > start_char]
    with pytest.raises(ValueError, match="chat-control token"):
        kv.echo_context(tok, context, [{"span": (span[0], span[-1] + 1), "origin_turn": 1}])


def test_echo_eviction_range_recomputed_on_echoed_ids_covers_same_history(kv, tok):
    context, aged = echo_fixture(tok)
    echoed, _, _ = kv.echo_context(tok, context, aged)
    base_ids, base_range = kv.tokenized_eviction_range(tok, context)
    echo_ids, echo_range = kv.tokenized_eviction_range(tok, echoed)
    assert tok.decode(base_ids[slice(*base_range)]) == tok.decode(echo_ids[slice(*echo_range)])


def test_quoting_requires_eight_consecutive_echo_tokens(kv):
    echo_ids = list(range(20, 32))
    assert kv.detect_quoting([99, *echo_ids[2:10], 98], echo_ids, echo_arm=True)
    assert not kv.detect_quoting([99, *echo_ids[2:9], 98], echo_ids, echo_arm=True)
    assert not kv.detect_quoting([99, *echo_ids[2:10], 98], echo_ids, echo_arm=False)


def test_summary_contrasts_and_recovered_fractions(kv):
    passes = {
        "full": (2, 2, 2),
        "evicted": (1, 1, 0),
        "pinned": (2, 1, 1),
        "pinned_control": (1, 1, 1),
        "echo_only": (1, 2, 0),
        "pinned_echo": (2, 2, 1),
    }
    quoting = {"echo_only": {1}, "pinned_echo": {0}}
    records = []
    for session in range(3):
        arms = {}
        for arm, values in passes.items():
            arms[arm] = {
                "aged_pass": values[session], "aged_n": 2,
                "quoting": session in quoting.get(arm, set()),
                "truncated": False, "timed_out": False, "rep4": 0.0,
            }
        records.append({"session": session, "n_aged": 2, "arms": arms})
    summary = kv.summarize_records(records, tuple(passes))
    assert summary["gap_full_minus_evicted_passes"] == 4
    assert summary["echo_only"]["quoting_rate"] == pytest.approx(1 / 3)
    assert summary["echo_only"]["pass_rate_quoting_excluded"] == pytest.approx(1 / 4)
    assert summary["contrasts"] == {
        "pinned_minus_evicted": {"pass_count_difference": 2, "recovered_fraction_of_gap": 0.5},
        "echo_only_minus_evicted": {"pass_count_difference": 1, "recovered_fraction_of_gap": 0.25},
        "pinned_echo_minus_echo_only": {"pass_count_difference": 2, "recovered_fraction_of_gap": 0.5},
        "pinned_minus_pinned_control": {"pass_count_difference": 1, "recovered_fraction_of_gap": 0.25},
    }
