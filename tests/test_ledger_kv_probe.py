import importlib.util
import sys
from pathlib import Path

import pytest

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
        "pinned_wave_d0.5", "pinned_wave_d1.0", "pinned_wave_d3.0",
    )


def test_record_schema_has_history_and_generated_token_ids(kv):
    arm_names = kv.arm_names([0.5])
    arms = {name: {"generated_token_ids": [7, 8], "scores": [True], "aged_pass": 1,
                   "aged_n": 1, "truncated": False, "timed_out": False, "rep4": 0.0,
                   "pinned_cols": 3, "cache_cols": 9, "text": "ok", "n": 2,
                   "degenerate": False} for name in arm_names}
    rec = kv.session_record(
        session=2, key=17, topic="topic", n_turns=3, evict_range=(1, 9),
        keep=[(2, 5)], control_keep=[(5, 8)], n_aged=1,
        history_token_ids=[1, 2, 3], context_token_ids=[1, 2, 3, 4], arms=arms,
    )
    assert rec["history_token_ids"] == [1, 2, 3]
    assert rec["context_token_ids"] == [1, 2, 3, 4]
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
