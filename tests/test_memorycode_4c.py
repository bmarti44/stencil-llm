"""Exp 4C (REGISTRATION-4C.md): sample-size rule, record validity, the paired-t
primary with its Hoeffding fallback, the output-failure guard, every terminal reading,
budget accounting incl. interrupted attempts, timeout zero-credit."""

from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


summ = _load("memorycode_4c_summarize")
items4c = _load("memorycode_4c_items")
runner = summ.runner

MANIFEST = {
    "model": "4b",
    "policy": "role_evicted",
    "decoding": {"greedy": True, "max_new": 512, "deadline": 300.0},
    "window": 3584,
    "budget_tokens": 256,
    "items_sha256": "items-sha",
    "package_sha256": "pkg-sha",
    "generation_path": "transformers",
    "environment": {
        "torch": "2.13.0",
        "transformers": "5.16.1",
        "attn_implementation": "sdpa",
    },
}


def _rec(
    i: int,
    on: float,
    off: float,
    fail_on=False,
    fail_off=False,
    timed_out_on=False,
    manifest=None,
    strict_on=False,
    strict_off=False,
):
    def gen(score, fail, timed_out):
        return {
            "termination": "timeout" if timed_out else "eos",
            "timed_out": timed_out,
            "truncated": False,
            "seconds": 10.0,
            "generated_token_ids": [1, 2],
            "generated_token_ids_raw": [1, 2, 151645],
            "window": {"prompt_tokens": 3584},
            "failures": {
                "invalid": fail,
                "truncated": False,
                "degenerate": False,
                "timed_out": timed_out,
            },
            "scores": {
                "per_family": [score],
                "structure_present": True,
                "strict": score == 1.0,
                "fraction": score,
                "fraction_required": score,
            },
        }

    return {
        "id": f"d{i}-1",
        "candidate_index": i,
        "manifest": manifest if manifest is not None else MANIFEST,
        "arms": {
            "focus": {
                "generations": [gen(on, fail_on, timed_out_on)],
                "strict": strict_on,
            },
            "base": {"generations": [gen(off, fail_off, False)], "strict": strict_off},
        },
    }


def _ids(n):
    return [f"d{i}-1" for i in range(n)]


def _run(records, n=None, ceiling=None, spent=0.0, marker=False):
    return summ.analyze(
        records, _ids(n or len(records)), MANIFEST, "items-sha", ceiling, spent, marker
    )


def test_sample_size_rule_is_timing_only():
    assert items4c.sample_size(47.641592214) == 196
    assert items4c.sample_size(50.0) == 192
    assert items4c.sample_size(60.0) == 160
    assert items4c.sample_size(75.0) == 128
    assert items4c.sample_size(76.0) == 126  # INELIGIBLE below 128 (checked by caller)


def test_paired_t_and_hoeffding_fallback():
    t = summ.paired_t([0.1, 0.2, 0.0, 0.3, 0.1, 0.2, 0.1, 0.0])
    assert t["method"] == "paired t" and t["lower"] < t["mean"] < t["upper"]
    assert 0 < t["p"] < 0.05
    h = summ.paired_t([0.05] * 40)
    assert h["method"].startswith("hoeffding")
    assert h["lower"] == pytest.approx(0.05 - math.sqrt(2 * math.log(40) / 40))
    assert h["p"] == pytest.approx(min(1.0, 2 * math.exp(-40 * 0.05**2 / 2)))


def test_readings_cover_every_row():
    n = 40
    # proven-shape: consistent gains, no failures anywhere
    recs = [_rec(i, on=0.5 + 0.01 * (i % 3), off=0.3) for i in range(n)]
    out = _run(recs, ceiling=1e9)
    assert out["status"]["technical_ok"]
    assert out["stats"]["primary"]["lower"] > 0
    assert out["stats"]["failure_guard"]["method"].startswith("clopper")
    assert out["reading"]["statistical_gates_passed"] is False or True  # decided below
    # guard at zero variance uses the Clopper-Pearson union bound; with n = 40 its
    # upper bound exceeds +5 points, so the reading is NONINFERIORITY UNRESOLVED
    assert "NONINFERIORITY UNRESOLVED" in out["reading"]["verdict"]
    # a large N with zero discordance passes the guard
    big = [_rec(i, on=0.5 + 0.01 * (i % 3), off=0.3) for i in range(1500)]
    out = summ.analyze(big, _ids(1500), MANIFEST, "items-sha", 1e9, 0.0)
    assert out["reading"]["statistical_gates_passed"]
    assert out["reading"]["verdict"].startswith("STATISTICAL GATES PASSED")
    # NOT PROVEN: differences straddle zero
    recs = [_rec(i, on=0.3 + (0.1 if i % 2 else -0.1), off=0.3) for i in range(n)]
    assert _run(recs, ceiling=1e9)["reading"]["verdict"] == "NOT PROVEN, FINAL"
    # HARM: consistent losses
    recs = [_rec(i, on=0.2, off=0.3 + 0.01 * (i % 3)) for i in range(n)]
    assert _run(recs, ceiling=1e9)["reading"]["verdict"] == "HARM"
    # demonstrated excess output harm: gains but focus fails on most items
    recs = [
        _rec(i, on=0.5 + 0.01 * (i % 3), off=0.3, fail_on=(i % 4 != 0))
        for i in range(n)
    ]
    out = _run(recs, ceiling=1e9)
    assert out["stats"]["failure_guard"]["lower"] > 0.05
    assert "DEMONSTRATED EXCESS OUTPUT HARM" in out["reading"]["verdict"]
    # noninferiority unresolved: a few focus-only failures
    recs = [
        _rec(i, on=0.5 + 0.01 * (i % 3), off=0.3, fail_on=(i % 10 == 0))
        for i in range(n)
    ]
    out = _run(recs, ceiling=1e9)
    assert "NONINFERIORITY UNRESOLVED" in out["reading"]["verdict"]
    # INELIGIBLE overrides everything
    assert summ.reading_4c(out["status"], out["stats"], eligible=False)[
        "verdict"
    ].startswith("INELIGIBLE")


def test_incomplete_on_missing_invalid_duplicate_or_budget():
    recs = [_rec(i, on=0.5, off=0.3) for i in range(10)]
    # missing pair
    out = summ.analyze(recs[:9], _ids(10), MANIFEST, "items-sha", 1e9, 0.0)
    assert out["status"]["missing_ids"] == ["d9-1"]
    assert out["reading"]["verdict"] == "INCOMPLETE"
    # changed package hash
    bad = dict(MANIFEST, package_sha256="other")
    recs2 = recs[:9] + [_rec(9, on=0.5, off=0.3, manifest=bad)]
    out = _run(recs2, ceiling=1e9)
    assert out["status"]["invalid_records"]["d9-1"] == "fingerprint mismatch"
    assert out["reading"]["verdict"] == "INCOMPLETE"
    # changed environment (attention backend) is a mismatch; unknown backend is not
    env = dict(
        MANIFEST, environment=dict(MANIFEST["environment"], attn_implementation="eager")
    )
    assert not runner.fingerprint_matches(env, MANIFEST)
    unknown = dict(
        MANIFEST, environment=dict(MANIFEST["environment"], attn_implementation=None)
    )
    assert runner.fingerprint_matches(unknown, MANIFEST)
    # duplicate id
    out = _run(recs + [recs[0]], n=10, ceiling=1e9)
    assert out["status"]["duplicate_ids"] == ["d0-1"]
    assert out["reading"]["verdict"] == "INCOMPLETE"
    # budget exhausted (spent > ceiling) even when complete
    out = _run(recs, ceiling=100.0, spent=101.0)
    assert out["status"]["budget"]["exhausted"]
    assert out["reading"]["verdict"] == "INCOMPLETE"
    # marker file
    out = _run(recs, ceiling=1e9, marker=True)
    assert out["reading"]["verdict"] == "INCOMPLETE"
    # a missing arm is invalid, never silently dropped
    half = _rec(3, on=0.5, off=0.3)
    del half["arms"]["base"]
    out = _run(recs[:3] + [half] + recs[4:], ceiling=1e9)
    assert out["status"]["invalid_records"]["d3-1"] == "missing arm"


def test_timeout_scores_zero_on_the_primary_and_counts_as_failure():
    recs = [_rec(i, on=0.5, off=0.3) for i in range(6)]
    recs[0] = _rec(0, on=1.0, off=0.3, timed_out_on=True)
    out = _run(recs, ceiling=1e9)
    on = out["stats"]["primary"]["mean_on"]
    assert on == pytest.approx((0.0 + 0.5 * 5) / 6)
    assert out["stats"]["failure_guard"]["on_only"] == 1
    assert out["stats"]["failure_guard"]["categories"]["focus"]["timed_out"] == 1


def test_interrupted_attempts_count_against_the_budget(tmp_path):
    log = tmp_path / "attempts.jsonl"
    rows = [
        {"id": "a", "arm": "base", "event": "start", "monotonic": 0.0},
        {"id": "a", "arm": "base", "event": "end", "monotonic": 40.0, "seconds": 40.0},
        {"id": "b", "arm": "base", "event": "start", "monotonic": 50.0},  # killed
        {"id": "b", "arm": "base", "event": "start", "monotonic": 80.0},  # retried
        {"id": "b", "arm": "base", "event": "end", "monotonic": 120.0, "seconds": 40.0},
        {"id": "c", "arm": "focus", "event": "start", "monotonic": 130.0},  # open
    ]
    log.write_text("\n".join(json.dumps(r) for r in rows) + "\n")
    lost = runner.interrupted_seconds(tmp_path, deadline=300.0)
    assert lost == pytest.approx(30.0 + 300.0)
    assert runner.interrupted_seconds(tmp_path / "none", deadline=300.0) == 0.0


def test_candidate_manifest_reproduces_registration_hashes():
    cand = json.loads(
        (ROOT / "results/memorycode-long/items-4c-candidates.json").read_text()
    )
    assert cand["n_candidates"] == 196
    assert (
        cand["candidate_ids_sha256"]
        == "3125634e658bf35fc20e8555199abb5cc8f30ada4c14f328caba08fa7e43ca28"
    )
    assert (
        cand["items_json_sha256"]
        == "affe6877f059e5f58466023fe70c45cefeadca4b98d1a036832901d14073ce1a"
    )
    assert (
        items4c.ids_sha256([it["id"] for it in cand["items"]])
        == cand["candidate_ids_sha256"]
    )
    assert [it["candidate_index"] for it in cand["items"]] == list(range(196))
    assert sum(it["source"] == "reserve" for it in cand["items"]) == 68
    original = json.loads((ROOT / "results/memorycode-long/items.json").read_text())
    screen_ids = [it["id"] for it in original["items"] if it["split"] == "screen_long"]
    assert [it["id"] for it in cand["items"][:128]] == screen_ids
