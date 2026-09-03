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
    assert args.focus == "oracle"
    assert args.dose == [0.5, 1.0, 3.0]
    assert args.max_new == 512
    assert args.eviction_timing == "pre-query"
    assert kv.arm_names(args.dose) == (
        "full", "evicted", "pinned", "pinned_control",
        "echo_only", "pinned_echo",
        "pinned_wave_d0.5", "pinned_wave_d1.0", "pinned_wave_d3.0",
    )

    auto = kv.parse_args(["--focus", "auto"])
    assert auto.dose == []
    assert kv.arm_names(auto.dose, focus=auto.focus) == (
        "full", "evicted", "pinned", "pinned_control",
        "echo_only", "pinned_echo", "full_echo",
    )
    with pytest.raises(SystemExit):
        kv.parse_args(["--focus", "auto", "--dose", "1.0"])
    assert kv.parse_args(["--eviction-timing", "post-prefill"]).eviction_timing == "post-prefill"


def test_auto_focus_uses_salience2_on_unmarked_turns_and_not_oracle_reader(kv, tok):
    marked = (
        "<|im_start|>user\nWrite about rain. Constraint: include cedar.<|im_end|>\n"
        "<|im_start|>assistant\nRain falls.<|im_end|>\n"
        "<|im_start|>user\nContinue. Constraint: end with done.<|im_end|>\n"
        "<|im_start|>assistant\n"
    )
    seen = []

    def finder(text, *, backend):
        assert "Constraint:" not in text
        seen.append((text, backend))
        start = text.index("include cedar") if "cedar" in text else text.index("end with done")
        return [type("Found", (), {"start": start, "end": len(text) - 1})()]

    def forbidden_reader(*args, **kwargs):
        raise AssertionError("auto focus read oracle marks")

    unmarked = kv.strip_constraint_marks(marked)
    records = kv.focus_span_records(
        tok, unmarked, last_turn=2, focus="auto", finder=finder,
        marked_span_reader=forbidden_reader,
    )
    assert len(seen) == 2
    assert all(backend == kv.salience_backend() for _, backend in seen)
    assert len(records) == 1 and records[0]["origin_turn"] == 1
    selected = tok.decode(tok.encode(unmarked).ids[slice(*records[0]["span"])])
    assert "include cedar" in selected


def test_auto_coverage_and_extra_on_synthetic_marked_history(kv, tok):
    marked = (
        "<|im_start|>user\nTask. Constraint: alpha beta gamma delta. "
        "Constraint: epsilon zeta eta theta.<|im_end|>\n"
        "<|im_start|>assistant\nold<|im_end|>\n"
        "<|im_start|>user\nContinue.<|im_end|>\n<|im_start|>assistant\n"
    )
    unmarked = kv.strip_constraint_marks(marked)
    enc = tok.encode(unmarked)

    def token_span(needle):
        a = unmarked.index(needle)
        b = a + len(needle)
        ids = [i for i, (x, y) in enumerate(enc.offsets) if x < b and y > a]
        return (ids[0], ids[-1] + 1)

    selected = [
        {"span": token_span("alpha beta gamma"), "origin_turn": 1},
        {"span": token_span("Task"), "origin_turn": 1},
    ]
    metrics = kv.auto_selection_metrics(tok, marked, unmarked, selected, last_turn=2)
    assert metrics == {"auto_coverage": 0.5, "auto_extra": 1}


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


def test_oracle_record_schema_roundtrips_committed_h1_session(kv):
    path = ROOT / "results" / "qwen" / "ledger-kv-probe-h1" / "session-000.json"
    old = __import__("json").loads(path.read_text())
    rebuilt = kv.session_record(
        session=old["session"], key=old["key"], topic=old["topic"],
        n_turns=old["n_turns"], evict_range=old["evict_range"], keep=old["keep"],
        control_keep=old["control_keep"], n_aged=old["n_aged"],
        history_token_ids=old["history_token_ids"], context_token_ids=old["context_token_ids"],
        arms=old["arms"], echo_context_token_ids=old["echo_context_token_ids"],
        echo_tokens_added=old["echo_tokens_added"], echo_text_sha256=old["echo_text_sha256"],
    )
    rebuilt["context_tokens"] = old["context_tokens"]
    assert rebuilt == old


def test_provenance_and_registered_kill_rule(kv):
    prov = kv.provenance_manifest()
    for key in ("determinism.py", "tokenizer.json", "bench.py", "ctrb.py", "ledger_kv_probe.py",
                "salience2_weights.json", "salience2_probe.npz", "salience2_hybrid.json",
                "vendor/ifeval"):
        assert key in prov and len(prov[key]) == 64, key
    meta = kv.build_meta(
        doses=[0.5, 1.0, 3.0], max_new=512, deadline=300.0,
        eviction_timing="pre-query",
    )
    assert meta["wave_kill_rule"] == "degenerate sessions > 2/20 at best dose"
    assert meta["eviction_timing"] == "pre-query"
    assert meta["provenance"] == prov


def test_quick_check_probe_flag_and_scores_path_round_trip():
    from scripts.clf_probe_check import parse_args

    args = parse_args([
        "--scores", "scores.json", "--eviction-timing", "post-prefill"
    ])
    assert args.scores == "scores.json"
    assert args.eviction_timing == "post-prefill"


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


def test_current_turn_start_supports_single_turn_generation(kv, tok):
    context = (
        "<|im_start|>user\nFirst prompt.<|im_end|>\n"
        "<|im_start|>assistant\n<think>\n\n</think>\n\n"
    )
    ids = tok.encode(context).ids
    split = kv.current_turn_start(tok, ids)
    assert split == 0
    assert tok.decode(ids[split:], skip_special_tokens=False).startswith(
        "<|im_start|>user\n"
    )


def test_echo_span_stops_before_next_constraint_and_reminder(kv, tok):
    from stencil.e2 import constraint_span_records

    context = (
        "<|im_start|>user\nTask. Constraint: include cedar. Constraint: include ash. "
        "Every earlier constraint from this conversation still applies to this reply as well.<|im_end|>\n"
        "<|im_start|>assistant\nold<|im_end|>\n"
        "<|im_start|>user\nContinue.<|im_end|>\n<|im_start|>assistant\n"
    )
    marked = [r for r in constraint_span_records(tok, context) if r["origin_turn"] < 2]
    _, entries, rendered = kv.echo_context(tok, context, marked)
    assert len(entries) == 2
    assert all(not entry.text.rstrip().endswith(" Constraint") for entry in entries)
    assert "Every earlier constraint" not in rendered


def test_quoting_requires_eight_consecutive_echo_tokens(kv):
    echo_ids = list(range(20, 32))
    assert kv.detect_quoting([99, *echo_ids[2:10], 98], echo_ids, echo_arm=True)
    assert not kv.detect_quoting([99, *echo_ids[2:9], 98], echo_ids, echo_arm=True)
    assert not kv.detect_quoting([99, *echo_ids[2:10], 98], echo_ids, echo_arm=False)


@pytest.mark.parametrize(
    "text, expected",
    [
        ("", True),
        (" \n\t", True),
        ("...!? —", True),
        ("<|im_start|>assistant\nhello", True),
        ("hello<|im_end|>", True),
        ("ordinary words", False),
        ("42", False),
    ],
)
def test_invalid_output_detection_table(kv, text, expected):
    assert kv.invalid_output(text) is expected


def test_summary_contrasts_and_recovered_fractions(kv):
    passes = {
        "full": (2, 2, 2),
        "evicted": (1, 1, 0),
        "pinned": (2, 1, 1),
        "pinned_control": (1, 1, 1),
        "echo_only": (1, 2, 0),
        "pinned_echo": (2, 2, 1),
        "full_echo": (2, 2, 2),
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
                "invalid_output": arm == "echo_only" and session == 2,
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
        "full_echo_minus_full": {"pass_count_difference": 0, "recovered_fraction_of_gap": 0.0},
    }
    assert summary["echo_only"]["invalid_output"] == 1
    assert summary["safety_table"]["echo_only"] == {
        "timeouts": {"events": 0, "vs_full": 0, "safe": True},
        "truncations": {"events": 0, "vs_full": 0, "safe": True},
        "degenerate_sessions": {"events": 0, "vs_full": 0, "safe": True},
        "invalid_output": {"events": 1, "vs_full": 1, "safe": False},
        "safe": False,
    }
