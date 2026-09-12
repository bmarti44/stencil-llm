"""Exp 4C (REGISTRATION-4C.md; Astra implementation review applied): sample-size rule,
freeze chain, effective-EOS handling, strict fingerprints, attempt/receipt accounting,
record validity (consistency, extras, NaN, malformed), the paired-t primary with its
Hoeffding fallback on exactly constant differences, the output-failure guard, every
terminal reading, budget exhaustion, qualification receipts and the release gates."""

from __future__ import annotations

import gc
import hashlib
import importlib.util
import json
import math
import weakref
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


summ = _load("memorycode_4c_summarize")
qualify = _load("memorycode_4c_qualify")
release = _load("memorycode_4c_release")
runner = summ.runner
items4c = summ.items4c

ENV = {
    "python": "3.12.13",
    "torch": "2.13.0+cu130",
    "transformers": "5.16.1",
    "tokenizers": "0.23.1",
    "cuda": "13.0",
    "gpu_name": "NVIDIA GB10",
    "dtype": "torch.bfloat16",
    "device": "cuda:0",
    "attn_implementation": "sdpa",
    "deterministic_algorithms": False,
    "cublas_workspace_config": None,
    "allow_tf32_matmul": False,
    "float32_matmul_precision": "highest",
    "sdpa_kernels": {"flash": True, "mem_efficient": True, "math": True, "cudnn": True},
}
MANIFEST = {
    "model": "4b",
    "policy": "role_evicted",
    "decoding": runner.generation_settings(512, 300.0, [151645]),
    "window": 3584,
    "budget_tokens": 256,
    "items_sha256": "items-sha",
    "package_sha256": "pkg-sha",
    "checker_sha256": {"a": "1"},
    "generation_path": "transformers",
    "eos_token_ids": [151645],
    "environment": ENV,
}


def _gen(score: float, fail: bool, timed_out: bool) -> dict:
    raw = [1, 2] if timed_out else [1, 2, 151645]
    ids = [1, 2]
    prompt = "p"
    score = 0.0 if timed_out else score
    return {
        "termination": "timeout" if timed_out else "eos",
        "timed_out": timed_out,
        "timeout_reason": "max_time_stop" if timed_out else None,
        "truncated": False,
        "ended_by_eos": not timed_out,
        "seconds": 10.0,
        "generated_token_ids": ids,
        "generated_token_ids_raw": raw,
        "eos_token_ids": [151645],
        "n_generated": 2,
        "n_generated_raw": len(raw),
        "prompt": prompt,
        "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
        "prompt_ids_count": 3584,
        "text": "code",
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
            "strict": score == 1.0 and not timed_out,
            "fraction": score,
            "fraction_required": score,
        },
    }


def _item(i: int) -> dict:
    return {
        "id": f"d{i}-1",
        "session": 1,
        "queries": ["q"],
        "history_regex": [],
        "candidate_index": i,
        "required": {"q": []},
        "structure": {"q": []},
    }


def _rec(i, on, off, fail_on=False, fail_off=False, timed_out_on=False, manifest=None):
    m = manifest if manifest is not None else MANIFEST
    it = _item(i)
    gon, goff = _gen(on, fail_on, timed_out_on), _gen(off, fail_off, False)
    return {
        **{k: it[k] for k in summ.ITEM_KEYS},
        "arms": {
            "focus": {
                "generations": [gon],
                "strict": gon["scores"]["strict"],
                "manifest": m,
                "reminder": "Earlier instructions still in force:\n- Use tabs.",
                "kept_sentences": 1,
                "reminder_sources": {
                    "eviction_boundary_char": 100,
                    "kept_spans": [
                        {
                            "start": 10,
                            "end": 19,
                            "message_index": 0,
                            "sentence": "Use tabs.",
                        }
                    ],
                },
            },
            "base": {
                "generations": [goff],
                "strict": goff["scores"]["strict"],
                "manifest": m,
            },
        },
    }


def _items(n):
    return [_item(i) for i in range(n)]


def _acct(gen=0.0, overhead=0.0, qual=0.0, unbounded=False):
    return {
        "generation_seconds": gen,
        "overhead_seconds": overhead,
        "qualification_seconds": qual,
        "unbounded": unbounded,
    }


def _run(records, n=None, ceiling=1e9, acct=None, marker=False, **kw):
    return summ.analyze(
        records,
        _items(n or len(records)),
        MANIFEST,
        ceiling,
        acct or _acct(),
        marker,
        **kw,
    )


# ------------------------------------------------------------------ sample size / chain
def test_sample_size_rule_is_timing_only():
    assert items4c.sample_size(47.641592214) == 196
    assert items4c.sample_size(50.0) == 192
    assert items4c.sample_size(60.0) == 160
    assert items4c.sample_size(75.0) == 128
    assert items4c.sample_size(76.0) == 126  # INELIGIBLE below 128 (checked by caller)


def _fake_qual(t_max=50.0, n_calls=8):
    calls = [
        {"id": i, "arm": a, "seconds": t_max - k * 0.5}
        for k, (i, a) in enumerate(items4c.TIMING_CALLS[:n_calls])
    ]
    return {
        "eligible": True,
        "passed": True,
        "t_max_seconds": max(c["seconds"] for c in calls),
        "timing_calls": calls,
        "manifest": {"package_sha256": "pkg-sha"},
    }


def _fake_frozen(qual, n=None):
    cand = json.loads(
        (ROOT / "results/memorycode-long/items-4c-candidates.json").read_text()
    )
    t_max = qual["t_max_seconds"]
    n = n or items4c.sample_size(t_max)
    chosen = cand["items"][:n]
    return {
        "items_json_sha256": items4c.ITEMS_JSON_SHA256,
        "candidate_ids_sha256": items4c.CANDIDATE_IDS_SHA256,
        "qualification_sha256": "qsha",
        "package_sha256": "pkg-sha",
        "n": n,
        "t_max_seconds": t_max,
        "frozen_ids_sha256": items4c.ids_sha256([it["id"] for it in chosen]),
        "items": chosen,
    }


def test_freeze_chain_verifies_and_rejects_frozen_n_mismatch():
    qual = _fake_qual(50.0)
    frozen = _fake_frozen(qual)
    assert frozen["n"] == 192
    assert items4c.verify_frozen(frozen, qual, "qsha") == []
    wrong = _fake_frozen(qual, n=196)  # not the timing rule
    assert any("rule" in p for p in items4c.verify_frozen(wrong, qual, "qsha"))
    assert any("digest" in p for p in items4c.verify_frozen(frozen, qual, "other"))
    short = _fake_qual(50.0, n_calls=7)
    assert any("prescribed" in p for p in items4c.verify_frozen(frozen, short, "qsha"))
    swapped = dict(frozen, items=list(reversed(frozen["items"])))
    swapped["frozen_ids_sha256"] = items4c.ids_sha256(
        [it["id"] for it in swapped["items"]]
    )
    assert any("prefix" in p for p in items4c.verify_frozen(swapped, qual, "qsha"))
    other_pkg = dict(qual, manifest={"package_sha256": "changed"})
    assert any("package" in p for p in items4c.verify_frozen(frozen, other_pkg, "qsha"))
    ineligible = dict(qual, eligible=False)
    assert any(
        "eligible" in p for p in items4c.verify_frozen(frozen, ineligible, "qsha")
    )


def test_candidate_manifest_reproduces_registration_hashes():
    cand = json.loads(
        (ROOT / "results/memorycode-long/items-4c-candidates.json").read_text()
    )
    assert cand["n_candidates"] == 196
    assert cand["candidate_ids_sha256"] == items4c.CANDIDATE_IDS_SHA256
    assert cand["items_json_sha256"] == items4c.ITEMS_JSON_SHA256
    assert (
        items4c.ids_sha256([it["id"] for it in cand["items"]])
        == cand["candidate_ids_sha256"]
    )
    assert [it["candidate_index"] for it in cand["items"]] == list(range(196))
    assert sum(it["source"] == "reserve" for it in cand["items"]) == 68
    original = json.loads((ROOT / "results/memorycode-long/items.json").read_text())
    screen_ids = [it["id"] for it in original["items"] if it["split"] == "screen_long"]
    assert [it["id"] for it in cand["items"][:128]] == screen_ids


# ------------------------------------------------------------------ EOS
class _FakeSession:
    def __init__(self, model, raw):
        self.model = model
        self._raw = raw
        self.last = {}
        self.tokenizer = SimpleNamespace(
            decode=lambda ids, skip_special_tokens=True: str(ids)
        )

    def generate(self, request, **kw):
        assert kw["max_time"] == 300.0 and kw["max_new_tokens"] == 512
        self.last = {"generated_token_ids": list(self._raw), "prompt_tokens": 10}


def _fake_model():
    return SimpleNamespace(
        config=SimpleNamespace(eos_token_id=151645),
        generation_config=SimpleNamespace(eos_token_id=[151645, 151643]),
    )


def test_effective_eos_is_the_config_value_not_the_generation_config_union():
    model = _fake_model()
    assert runner.eos_ids(model) == [151645]
    # 151643 inside the package output is NOT a stop: it stays in the scored ids and,
    # with fewer than max_new tokens, the call is a max_time timeout, not an EOS end
    g = runner.generate_package(
        _FakeSession(model, [1, 151643, 2]), "r", "", "", 512, 300.0
    )
    assert g["generated_token_ids"] == [1, 151643, 2] and g["termination"] == "timeout"
    assert g["timeout_reason"] == "max_time_stop" and g["timed_out"]
    g = runner.generate_package(
        _FakeSession(model, [1, 2, 151645]), "r", "", "", 512, 300.0
    )
    assert g["generated_token_ids"] == [1, 2] and g["termination"] == "eos"
    assert g["eos_token_ids"] == [151645] and g["ended_by_eos"]
    # a terminal effective EOS in raw position 512 is an EOS completion with 511 ids
    raw = list(range(511)) + [151645]
    g = runner.generate_package(_FakeSession(model, raw), "r", "", "", 512, 300.0)
    assert g["termination"] == "eos" and g["n_generated"] == 511
    g = runner.generate_package(
        _FakeSession(model, list(range(512))), "r", "", "", 512, 300.0
    )
    assert g["termination"] == "cap" and g["truncated"] and not g["timed_out"]


# ------------------------------------------------------------------ fingerprints
def test_fingerprint_is_strict_after_load_and_only_provisionally_lenient():
    assert runner.fingerprint_matches(MANIFEST, MANIFEST)
    changed = dict(MANIFEST, environment=dict(ENV, attn_implementation="eager"))
    assert not runner.fingerprint_matches(changed, MANIFEST)
    assert not runner.fingerprint_matches(changed, MANIFEST, provisional=True)
    unresolved = dict(
        MANIFEST,
        environment=dict(ENV, attn_implementation=None, dtype=None, device=None),
        eos_token_ids=None,
        decoding=runner.generation_settings(512, 300.0, None),
    )
    assert not runner.fingerprint_matches(unresolved, MANIFEST)
    assert runner.fingerprint_matches(unresolved, MANIFEST, provisional=True)
    # a missing required field (an empty environment) never matches, even provisionally
    empty = dict(MANIFEST, environment={})
    assert not runner.fingerprint_matches(empty, MANIFEST)
    assert not runner.fingerprint_matches(empty, MANIFEST, provisional=True)
    missing_tok = dict(
        MANIFEST, environment={k: v for k, v in ENV.items() if k != "tokenizers"}
    )
    assert not runner.fingerprint_matches(missing_tok, MANIFEST, provisional=True)
    assert not runner.fingerprint_matches(
        dict(MANIFEST, checker_sha256={"a": "2"}), MANIFEST
    )


# ------------------------------------------------------------------ accounting
def _receipt(tmp_path, name, elapsed, ended, gen=0.0, overhead=None):
    payload = {
        "kind": "evaluation",
        "elapsed": elapsed,
        "ended": ended,
        "beat_interval": 5.0,
        "generation_seconds": gen,
        "overhead_seconds": elapsed - gen if overhead is None else overhead,
    }
    (tmp_path / name).write_text(json.dumps(payload))


def test_completed_attempt_without_record_is_charged_and_open_attempts_are_bounded(
    tmp_path,
):
    _receipt(tmp_path, "process-a.json", 400.0, "clean", gen=40.0)
    _receipt(tmp_path, "process-b.json", 130.0, None, gen=0.0)  # killed mid-call
    rows = [
        {
            "attempt_id": "x:base:1",
            "id": "x",
            "arm": "base",
            "event": "start",
            "process": "process-a.json",
            "process_elapsed": 10.0,
        },
        {
            "attempt_id": "x:base:1",
            "id": "x",
            "arm": "base",
            "event": "end",
            "seconds": 40.0,
            "process": "process-a.json",
            "process_elapsed": 50.0,
        },
        {
            "attempt_id": "y:focus:1",
            "id": "y",
            "arm": "focus",
            "event": "start",
            "process": "process-b.json",
            "process_elapsed": 100.0,
        },
    ]
    (tmp_path / "attempts.jsonl").write_text(
        "\n".join(json.dumps(r) for r in rows) + "\n"
    )
    acct = runner.attempt_accounting(tmp_path, 300.0)
    # the completed 40 s attempt counts although no terminal record exists (finding 4)
    assert acct["completed_seconds"] == 40.0 and acct["n_completed"] == 1
    # the open attempt is bounded by its process's last beat + one interval
    assert acct["open_seconds"] == pytest.approx(130.0 + 5.0 - 100.0)
    assert not acct["unbounded"] and acct["generation_seconds"] == pytest.approx(75.0)
    res = runner.resident_seconds(tmp_path)
    assert res["resident_seconds"] == pytest.approx(400.0 + 135.0)
    assert res["interrupted_processes"] == 1 and not res["unbounded"]
    # an open attempt whose process receipt is missing cannot be bounded
    rows.append(
        {
            "attempt_id": "z:base:1",
            "id": "z",
            "arm": "base",
            "event": "start",
            "process": "process-missing.json",
            "process_elapsed": 1.0,
        }
    )
    (tmp_path / "attempts.jsonl").write_text(
        "\n".join(json.dumps(r) for r in rows) + "\n"
    )
    assert runner.attempt_accounting(tmp_path, 300.0)["unbounded"]
    assert (
        runner.attempt_accounting(tmp_path / "none", 300.0)["generation_seconds"] == 0.0
    )


def test_process_receipt_watchdog_detects_limit_violations(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "BEAT_INTERVAL", 1000.0)  # the beat thread stays idle
    r = runner.ProcessReceipt(tmp_path, "test", resident_limit=1e9, overhead_limit=1e9)
    try:
        assert r._violation() is None
        r.resident_limit = 0.0
        assert r._violation() == "watchdog:resident"
        r.resident_limit = 1e9
        r.overhead_limit = 0.0
        assert r._violation() == "watchdog:overhead"
        r.overhead_limit = 1e9
        r.call_limit = 0.0
        r.begin_call()
        assert r._violation() == "watchdog:call"
        r.end_call(1.0)
        assert r._violation() is None
        assert json.loads(r.path.read_text())["generation_seconds"] == 1.0
    finally:
        r.finish()
    assert json.loads(r.path.read_text())["ended"] == "clean"


def test_release_model_drops_references():
    class Obj:
        pass

    o = Obj()
    ref = weakref.ref(o)
    runner.release_model(o)
    del o
    gc.collect()
    assert ref() is None


# ------------------------------------------------------------------ statistics
def test_paired_t_and_hoeffding_fallback_on_exactly_constant_differences():
    t = summ.paired_t([0.1, 0.2, 0.0, 0.3, 0.1, 0.2, 0.1, 0.0])
    assert t["method"] == "paired t" and t["lower"] < t["mean"] < t["upper"]
    assert 0 < t["p"] < 0.05
    h = summ.paired_t([0.05] * 40)
    assert h["method"].startswith("hoeffding")
    assert h["lower"] == pytest.approx(0.05 - math.sqrt(2 * math.log(40) / 40))
    assert h["p"] == pytest.approx(min(1.0, 2 * math.exp(-40 * 0.05**2 / 2)))
    # floating-point rounding must not bypass the fallback (review finding 8)
    h = summ.paired_t([0.12] * 134)
    assert h["method"].startswith("hoeffding")
    assert h["lower"] == pytest.approx(-0.114644204) and h["upper"] == pytest.approx(
        0.354644204
    )
    assert h["p"] == pytest.approx(0.762118808)
    assert summ.paired_t([float("nan"), 0.1])["method"] == "undefined"


def test_readings_cover_every_row():
    n = 40
    recs = [_rec(i, on=0.5 + 0.01 * (i % 3), off=0.3) for i in range(n)]
    out = _run(recs)
    assert out["status"]["technical_ok"] and out["status"]["finite_statistics"]
    assert out["stats"]["primary"]["lower"] > 0
    assert out["stats"]["failure_guard"]["method"].startswith("clopper")
    # at n = 40 the zero-discordance Clopper-Pearson upper bound exceeds +5 points
    assert out["stats"]["failure_guard"]["upper"] > 0.05
    assert out["reading"]["statistical_gates_passed"] is False
    assert "NONINFERIORITY UNRESOLVED" in out["reading"]["verdict"]
    # N = 128 with zero discordance: upper bound 1 - 0.0125^(1/128) ≈ 3.37 points → pass
    big = [_rec(i, on=0.5 + 0.01 * (i % 3), off=0.3) for i in range(128)]
    out = _run(big)
    assert out["stats"]["failure_guard"]["upper"] == pytest.approx(
        0.03365521009, abs=1e-6
    )
    assert out["reading"]["statistical_gates_passed"]
    assert out["reading"]["verdict"].startswith("STATISTICAL GATES PASSED")
    # N = 196 with one focus-only failure: paired t, U_H ≈ +1.52 points → pass
    big = [
        _rec(i, on=0.5 + 0.01 * (i % 3), off=0.3, fail_on=(i == 0)) for i in range(196)
    ]
    g = _run(big)["stats"]["failure_guard"]
    assert g["method"] == "paired t" and g["upper"] == pytest.approx(
        0.01516430638, abs=1e-6
    )
    assert g["p"] == pytest.approx(0.318549791, abs=1e-6)
    recs = [_rec(i, on=0.3 + (0.1 if i % 2 else -0.1), off=0.3) for i in range(n)]
    assert _run(recs)["reading"]["verdict"] == "NOT PROVEN, FINAL"
    recs = [_rec(i, on=0.2, off=0.3 + 0.01 * (i % 3)) for i in range(n)]
    assert _run(recs)["reading"]["verdict"] == "HARM"
    recs = [
        _rec(i, on=0.5 + 0.01 * (i % 3), off=0.3, fail_on=(i % 4 != 0))
        for i in range(n)
    ]
    out = _run(recs)
    assert out["stats"]["failure_guard"]["lower"] > 0.05
    assert "DEMONSTRATED EXCESS OUTPUT HARM" in out["reading"]["verdict"]
    recs = [
        _rec(i, on=0.5 + 0.01 * (i % 3), off=0.3, fail_on=(i % 10 == 0))
        for i in range(n)
    ]
    out = _run(recs)
    assert "NONINFERIORITY UNRESOLVED" in out["reading"]["verdict"]
    assert summ.reading_4c(out["status"], out["stats"], eligible=False)[
        "verdict"
    ].startswith("INELIGIBLE")


def test_nan_scores_never_pass(monkeypatch):
    recs = [_rec(i, on=0.5 + 0.01 * (i % 3), off=0.3) for i in range(128)]
    out = _run(recs)
    assert out["reading"]["statistical_gates_passed"]
    # a non-finite statistic, however it arises, blocks the positive decision
    stats = json.loads(json.dumps(out["stats"]))
    stats["primary"]["lower"] = float("nan")
    status = dict(out["status"], finite_statistics=False, technical_ok=False)
    assert summ.reading_4c(status, stats)["verdict"] == "INCOMPLETE"
    nan_rec = _rec(0, on=float("nan"), off=0.3)
    out = _run([nan_rec] + recs[1:])
    assert out["status"]["invalid_records"]["d0-1"].startswith(
        "focus: fraction_required"
    )
    assert out["reading"]["verdict"] == "INCOMPLETE"


# ------------------------------------------------------------------ validity
def test_incomplete_on_missing_invalid_duplicate_extra_malformed_or_budget():
    recs = [_rec(i, on=0.5, off=0.3) for i in range(10)]
    out = summ.analyze(recs[:9], _items(10), MANIFEST, 1e9, _acct())
    assert (
        out["status"]["missing_ids"] == ["d9-1"]
        and out["reading"]["verdict"] == "INCOMPLETE"
    )
    bad = dict(MANIFEST, package_sha256="other")
    out = _run(recs[:9] + [_rec(9, on=0.5, off=0.3, manifest=bad)])
    assert out["status"]["invalid_records"]["d9-1"] == "base: fingerprint mismatch"
    # one arm generated under another attention backend is invalid (per-arm identity)
    mixed = _rec(9, on=0.5, off=0.3)
    mixed["arms"]["focus"]["manifest"] = dict(
        MANIFEST, environment=dict(ENV, attn_implementation="eager")
    )
    assert (
        _run(recs[:9] + [mixed])["status"]["invalid_records"]["d9-1"]
        == "focus: fingerprint mismatch"
    )
    out = _run(recs + [recs[0]], n=10)
    assert (
        out["status"]["duplicate_ids"] == ["d0-1"]
        and out["reading"]["verdict"] == "INCOMPLETE"
    )
    # an extra valid record beyond the frozen manifest blocks confirmation
    out = summ.analyze(
        recs + [_rec(10, on=0.5, off=0.3)], _items(10), MANIFEST, 1e9, _acct()
    )
    assert out["status"]["invalid_records"]["d10-1"] == "not in the frozen manifest"
    assert not out["status"]["complete"]
    # malformed file / mismatched filename / unknown arm
    out = summ.analyze(
        [("item-d0-1.json", None)] + recs[1:], _items(10), MANIFEST, 1e9, _acct()
    )
    assert out["status"]["invalid_records"]["item-d0-1.json"] == "malformed record"
    out = summ.analyze(
        [("item-d5-1.json", recs[0])] + recs[1:], _items(10), MANIFEST, 1e9, _acct()
    )
    assert "filename" in out["status"]["invalid_records"]["d0-1"]
    odd = _rec(0, on=0.5, off=0.3)
    odd["arms"]["oracle"] = odd["arms"]["base"]
    assert (
        _run([odd] + recs[1:])["status"]["invalid_records"]["d0-1"]
        == "unknown or missing arm"
    )
    half = _rec(3, on=0.5, off=0.3)
    del half["arms"]["base"]
    assert (
        _run(recs[:3] + [half] + recs[4:])["status"]["invalid_records"]["d3-1"]
        == "unknown or missing arm"
    )
    # budget: generation over the ceiling, overhead over 2,700 s, qualification over
    # 3,600 s, unbounded accounting, or the marker file → INCOMPLETE even when complete
    for acct in (
        _acct(gen=101.0),
        _acct(overhead=2701.0),
        _acct(qual=3601.0),
        _acct(unbounded=True),
    ):
        out = _run(recs, ceiling=100.0, acct=acct)
        assert (
            out["status"]["budget"]["exhausted"]
            and out["reading"]["verdict"] == "INCOMPLETE"
        )
    assert _run(recs, marker=True)["reading"]["verdict"] == "INCOMPLETE"
    assert _run(recs, ceiling=100.0, acct=_acct(gen=99.0))["status"]["technical_ok"]


def test_record_consistency_is_checked_not_just_presence():
    def broken(mutate):
        rec = _rec(0, on=0.5, off=0.3)
        mutate(rec["arms"]["focus"]["generations"][0], rec)
        return _run([rec])["status"]["invalid_records"].get("d0-1")

    assert broken(lambda g, r: g.__setitem__("generated_token_ids", [9, 9])).startswith(
        "focus: scored ids"
    )
    assert "[0, 1]" in broken(
        lambda g, r: g["scores"].__setitem__("fraction_required", 3.0)
    )
    assert "seconds" in broken(lambda g, r: g.__setitem__("seconds", -1.0))
    assert "failure categories" in broken(lambda g, r: g["failures"].pop("degenerate"))
    assert "eos set" in broken(
        lambda g, r: g.__setitem__("eos_token_ids", [151645, 151643])
    )
    assert "prompt hash" in broken(lambda g, r: g.__setitem__("prompt", "other"))
    assert "differs from window" in broken(
        lambda g, r: g.__setitem__("prompt_ids_count", 3583)
    )
    assert "timeout classification" in broken(
        lambda g, r: g.__setitem__("timed_out", True)
    )
    assert "arm strict" in broken(
        lambda g, r: r["arms"]["focus"].__setitem__("strict", True)
    )
    assert "identity" in broken(lambda g, r: r.__setitem__("session", 2))
    assert "provenance" in broken(
        lambda g, r: r["arms"]["focus"].pop("reminder_sources")
    )
    assert broken(lambda g, r: None) is None
    # timeout zero-credit and the failure column
    recs = [_rec(i, on=0.5, off=0.3) for i in range(6)]
    recs[0] = _rec(0, on=1.0, off=0.3, timed_out_on=True)
    out = _run(recs)
    assert out["stats"]["primary"]["mean_on"] == pytest.approx((0.0 + 0.5 * 5) / 6)
    assert out["stats"]["failure_guard"]["on_only"] == 1
    assert out["stats"]["failure_guard"]["categories"]["focus"]["timed_out"] == 1


def test_records_are_rescored_with_the_frozen_checker_and_decoded_text_checked():
    recs = [_rec(i, on=0.5, off=0.3) for i in range(4)]

    def agree(item, g):
        return g["scores"], g["failures"]

    def disagree(item, g):
        return dict(g["scores"], fraction_required=0.9), g["failures"]

    assert _run(recs, rescore=agree)["status"]["complete"]
    out = _run(recs, rescore=disagree)
    assert all(
        v.endswith("frozen checker") for v in out["status"]["invalid_records"].values()
    )
    out = _run(recs, decode=lambda ids: "not the text")
    assert all("decoded" in v for v in out["status"]["invalid_records"].values())


# ------------------------------------------------------------------ qualification
def test_qualification_prescribes_44_calls_and_reports_from_receipts(
    tmp_path, monkeypatch
):
    setup = items4c.TIMING_IDS + [f"s{i}" for i in range(12)]
    calls = qualify.prescribed_calls(setup)
    assert len(calls) == 44
    assert [c["stage"] for c in calls].count("timing") == 8
    assert [c["stage"] for c in calls].count("off") == 12
    assert [c["stage"] for c in calls].count("plain") == 16
    assert [c["stage"] for c in calls].count("replay") == 8
    assert [(c["id"], c["arm"]) for c in calls[:8]] == items4c.TIMING_CALLS
    monkeypatch.setattr(qualify, "QDIR", tmp_path)
    (tmp_path / "calls").mkdir()
    ids = {c["key"]: [1, 2, 151645] for c in calls}

    def receipt(c, seconds):
        base = {
            **c,
            "prompt": "p" + c["id"],
            "prompt_ids": [1],
            "raw_ids": ids[c["key"]],
            "scored_ids": [1, 2],
            "text": "t",
            "eos_token_ids": [151645],
            "termination": "eos",
            "timeout_reason": None,
            "seconds": seconds,
            "prompt_tokens": 3584,
            "prompt_sha256": "x",
            "prompt_ids_sha256": "y",
            "manifest": MANIFEST,
        }
        if c["stage"] == "plain":
            base.update(prompt_ids_match=True, raw_match=True)
        return base

    # persist all but one call: the report is incomplete and no t_max-based eligibility
    for k, c in enumerate(calls[:-1]):
        (tmp_path / "calls" / f"{c['key']}.json").write_text(
            json.dumps(receipt(c, 30.0 + k))
        )
    (tmp_path / "process-a.json").write_text(
        json.dumps({"elapsed": 100.0, "ended": "clean"})
    )
    rep = qualify.report(calls, MANIFEST, {"id": 1})
    assert not rep["complete"] and rep["missing_calls"] == [calls[-1]["key"]]
    assert not rep["passed"] and not rep["eligible"]
    assert (
        qualify.load_call(calls[-1]) is None and qualify.load_call(calls[0]) is not None
    )
    (tmp_path / "calls" / f"{calls[-1]['key']}.json").write_text(
        json.dumps(receipt(calls[-1], 20.0))
    )
    rep = qualify.report(calls, MANIFEST, {"id": 1})
    assert rep["complete"] and rep["passed"] and rep["eligible"]
    assert rep["t_max_seconds"] == 37.0 and rep["n_by_timing_rule"] == 196
    assert rep["n_plain_matches"] == 16 and rep["n_replay_matches"] == 8
    assert [(t["id"], t["arm"]) for t in rep["timing_calls"]] == items4c.TIMING_CALLS
    # a replay whose raw output differs fails the 8/8 requirement
    c = calls[-1]
    bad = receipt(c, 20.0)
    bad["raw_ids"] = [1, 2, 3, 151645]
    (tmp_path / "calls" / f"{c['key']}.json").write_text(json.dumps(bad))
    rep = qualify.report(calls, MANIFEST, {"id": 1})
    assert rep["n_replay_matches"] == 7 and not rep["passed"]
    # resident time over the allowance fails qualification
    (tmp_path / "calls" / f"{c['key']}.json").write_text(json.dumps(receipt(c, 20.0)))
    (tmp_path / "process-b.json").write_text(
        json.dumps({"elapsed": 3600.0, "ended": None})
    )
    assert not qualify.report(calls, MANIFEST, {"id": 1})["passed"]


# ------------------------------------------------------------------ release
def test_release_refuses_unverified_or_changed_bytes(tmp_path):
    q = tmp_path / "qualification-4c.json"
    q.write_text(json.dumps({"manifest": {"package_sha256": "pkg"}}))
    qsha = release._sha(q)
    s = tmp_path / "summary-4c.json"
    s.write_text(
        json.dumps(
            {
                "reading": {"statistical_gates_passed": True},
                "status": {"technical_ok": True},
                "qualification_sha256": qsha,
            }
        )
    )
    a = tmp_path / "audit-4c.json"
    a.write_text(
        json.dumps(
            {
                "verdict": "ACCEPT",
                "summary_sha256": release._sha(s),
                "package_sha256": "pkg",
            }
        )
    )
    v = tmp_path / "verification-4c.json"
    v.write_text(
        json.dumps(
            {
                "passed": True,
                "fingerprint_bound": True,
                "package_sha256": "pkg",
                "qualification_sha256": qsha,
            }
        )
    )
    assert release.gates(s, a, v, q)[0] == []
    v.write_text(
        json.dumps(
            {
                "passed": False,
                "fingerprint_bound": True,
                "package_sha256": "pkg",
                "qualification_sha256": qsha,
            }
        )
    )
    assert any(p.startswith("verification") for p in release.gates(s, a, v, q)[0])
    a.write_text(
        json.dumps(
            {"verdict": "ACCEPT", "summary_sha256": "stale", "package_sha256": "pkg"}
        )
    )
    assert any("another summary" in p for p in release.gates(s, a, v, q)[0])
    s.write_text(
        json.dumps(
            {
                "reading": {"statistical_gates_passed": False},
                "status": {"technical_ok": True},
                "qualification_sha256": qsha,
            }
        )
    )
    assert any("statistical" in p for p in release.gates(s, a, v, q)[0])
    assert any(
        "missing" in p for p in release.gates(s, a, v, tmp_path / "none.json")[0]
    )
    # staging refuses bytes whose fingerprint differs from the evaluated package
    hub = tmp_path / "hub"
    hub.mkdir()
    (hub / "config.json").write_text("{}")
    (hub / "README.md").write_text("old card")
    card = tmp_path / "card.md"
    card.write_text("card")
    files = runner.package_files(hub)
    assert list(files) == [
        "config.json"
    ]  # README excluded from the inference fingerprint
    fp = runner.package_fingerprint(files)
    with pytest.raises(SystemExit):
        release.stage(hub, tmp_path / "staged-bad", card, "not-the-fingerprint")
    assert not (tmp_path / "staged-bad").exists()
    staged_files = release.stage(hub, tmp_path / "staged", card, fp)
    assert runner.package_fingerprint(staged_files) == fp
    assert (tmp_path / "staged" / "README.md").read_text() == "card"
    with pytest.raises(SystemExit):
        release.stage(hub, tmp_path / "staged", card, fp)  # immutable


def test_prompt_fields_come_from_the_linked_raw_file_when_absent_from_the_record():
    rec = _rec(0, on=0.5, off=0.3)
    raws = {}
    for arm in ("base", "focus"):
        g = rec["arms"][arm]["generations"][0]
        rec["arms"][arm]["attempt_id"] = f"d0-1:{arm}:abc"
        rec["arms"][arm]["raw_file"] = f"d0-1_{arm}_abc.json"
        raws[rec["arms"][arm]["raw_file"]] = {
            "attempt_id": f"d0-1:{arm}:abc",
            "arm": arm,
            "id": "d0-1",
            "prompt": g["prompt"],
            "prompt_sha256": g["prompt_sha256"],
            "prompt_ids_count": g["prompt_ids_count"],
            "window": g["window"],
            "generation": {"generated_token_ids_raw": g["generated_token_ids_raw"]},
            "manifest": MANIFEST,
        }
        for k in ("prompt", "prompt_sha256", "prompt_ids_count", "window"):
            del g[k]
    assert "prompt text missing" in _run([rec])["status"]["invalid_records"]["d0-1"]
    out = _run([rec], raw_loader=raws.get)
    assert out["status"]["complete"], out["status"]
    wrong = dict(raws)
    wrong[rec["arms"]["base"]["raw_file"]] = dict(
        raws[rec["arms"]["base"]["raw_file"]], attempt_id="other"
    )
    assert (
        "attempt"
        in _run([rec], raw_loader=wrong.get)["status"]["invalid_records"]["d0-1"]
    )
    wrong[rec["arms"]["base"]["raw_file"]] = dict(
        raws[rec["arms"]["base"]["raw_file"]],
        generation={"generated_token_ids_raw": [9]},
    )
    assert (
        "raw ids differ"
        in _run([rec], raw_loader=wrong.get)["status"]["invalid_records"]["d0-1"]
    )


def test_reminder_provenance_must_reproduce_the_reminder():
    def broken(mutate):
        rec = _rec(0, on=0.5, off=0.3)
        mutate(rec["arms"]["focus"])
        return _run([rec])["status"]["invalid_records"].get("d0-1")

    assert broken(lambda a: None) is None
    assert "reproduce" in broken(
        lambda a: a["reminder_sources"]["kept_spans"][0].__setitem__(
            "sentence", "Other."
        )
    )
    assert "count" in broken(lambda a: a.__setitem__("kept_sentences", 2))
    assert "evicted region" in broken(
        lambda a: a["reminder_sources"].__setitem__("eviction_boundary_char", 5)
    )
    assert "missing" in broken(lambda a: a.pop("reminder_sources"))
