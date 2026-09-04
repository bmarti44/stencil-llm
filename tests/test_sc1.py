"""SC1 consumer checks: invented fixtures only, no model loading or benchmark IO."""

import copy
import hashlib
import json
from pathlib import Path

import pytest
import torch

from stencil import sc1
from stencil import sc1_episodes as episodes
from stencil.qwen3 import KVCache, Qwen3Config

ROOT = Path(__file__).resolve().parents[1]


class CharTokenizer:
    def encode(self, text, add_special_tokens=False):
        return type(
            "Encoding",
            (),
            {
                "ids": [ord(c) for c in text],
                "offsets": [(i, i + 1) for i in range(len(text))],
            },
        )()

    def decode(self, ids, **kwargs):
        return "".join(chr(i) for i in ids)

    def get_added_tokens_decoder(self):
        return {}


class WordTokenizer(CharTokenizer):
    def encode(self, text, add_special_tokens=False):
        return type("Encoding", (), {"ids": text.split()})()


def public_history():
    return {
        "system": "Return the requested artifact.",
        "tools": None,
        "turns": [
            {"role": "user", "text": "Keep amber. Keep copper."},
            {"role": "tool", "text": "Ledger violet.\nParcel silver."},
            {"role": "assistant", "text": "Ordinary chatter. " * 100},
        ],
        "final_request": "Finish the artifact.",
    }


def candidate(a, b, text="small", role="user", index=0, char=0):
    return {
        "id": f"{role}:{index}:{char}:{a}:{b}",
        "span": [a, b],
        "char_span": [char, char + len(text)],
        "text": text,
        "message_index": index,
        "role": role,
    }


def test_geometry_and_renderer_private_isolation():
    tok = CharTokenizer()
    source = public_history()
    layout = sc1.render_episode(source, tok)
    assert layout["R"] == layout["H"] - 1024
    assert layout["C"] == layout["R"] - layout["P"]
    assert layout["B"] == min(256, layout["C"] // 4)
    changed = copy.deepcopy(source)
    changed.update(reference="PRIVATE", assignments={"scope": "SECRET"})
    assert sc1.render_episode(changed, tok) == layout
    assert sc1.window_geometry(10, 4106) == {
        "P": 10,
        "H": 4106,
        "R": 3082,
        "C": 3072,
        "B": 256,
        "evict_range": [10, 3082],
    }


def test_common_candidates_threshold_ties_and_rule_independence():
    tok = CharTokenizer()
    layout = sc1.render_episode(public_history(), tok)
    universe, exclusions = sc1.build_sc1_candidates(layout, tok)
    assert {c["role"] for c in universe} == {"user", "tool"}
    assert not any("score" in c for c in universe)
    assert exclusions
    baseline = sc1.select_policy(layout, tok, "rule", scorer=None)
    for value in (0, 1):

        def scorer(texts, *, role, contexts, value=value):
            assert all(c == "" for c in contexts)
            return [value] * len(texts)

        clf = sc1.select_policy(layout, tok, "clf", scorer=scorer)
        rule = sc1.select_policy(layout, tok, "rule", scorer=scorer)
        assert rule["candidates"] == clf["candidates"] == universe
        assert rule["candidate_hash"] == clf["candidate_hash"]
        assert rule["admission"] == baseline["admission"]
    items = [candidate(10, 12, index=0), candidate(12, 14, index=1)]
    ranked = sc1.rank_clf(items, lambda texts, **kw: [0.5] * len(texts))[0]
    assert ranked[0]["candidate"]["message_index"] == 1
    assert len(sc1.admit_whole_spans(ranked, (10, 20), 4)["admitted"]) == 2
    with pytest.raises(ValueError, match="score"):
        sc1.rank_clf(items, lambda texts, **kw: [float("nan")] * len(texts))


def test_boundary_piece_is_dropped_without_clipping():
    tok = CharTokenizer()
    layout = sc1.render_episode(public_history(), tok)
    loc = layout["locations"][0]
    layout.update(sc1.window_geometry(layout["P"], loc["start"] + 15 + 1024))
    rows, dropped = sc1.build_sc1_candidates(layout, tok)
    assert [r["text"] for r in rows] == ["Keep amber."]
    assert any(d["reason"] == "straddle" for d in dropped)


def test_skip_and_continue_union_and_ineligible():
    rows = [candidate(0, 8), candidate(8, 11), candidate(9, 12)]
    ranked = [{"candidate": c, "key": [i]} for i, c in enumerate(rows)]
    result = sc1.admit_whole_spans(ranked, (0, 20), 4)
    assert result["pins"] == [[8, 12]]
    assert len(result["admitted"]) == 2
    assert result["skips"][0]["reason"] == "budget"
    ranked[1]["key"] = [float("inf")]
    assert len(sc1.admit_whole_spans(ranked, (0, 20), 4)["admitted"]) == 1


def test_echo_chronological_selection_cap_skip_and_empty():
    tok = CharTokenizer()
    layout = sc1.render_episode(public_history(), tok)
    rows = [
        candidate(40, 42, "late", index=2),
        candidate(10, 12, "old"),
        candidate(20, 22, "x" * 240, index=1),
    ]
    echo = sc1.build_sc1_echo(rows, layout, tok)
    assert echo["entries"] == [rows[1], rows[0]]
    assert echo["tokens"] <= 256 and echo["increase"] <= 256
    assert echo["text"].startswith(
        'Earlier context restated verbatim:\n- user turn 0: "old"'
    )
    assert echo["insertion"].endswith("\n\n")
    empty = sc1.build_sc1_echo([rows[2]], layout, tok)
    assert empty["text"] == empty["insertion"] == ""
    assert empty["tokens"] == 0


def test_flags_consecutive_scattered_normalized_and_exact_cap():
    tok = WordTokenizer()
    assert not sc1.output_flags(
        " ".join("a b c d " + str(i) for i in range(8)), [0] * 256, False, tok
    )["R"]
    flags = sc1.output_flags("prefix " + "Ａ B c D\n" * 8, [0] * 256, False, tok)
    assert flags == {"I": True, "T": True, "R": True, "F": True}
    assert not sc1.output_flags("valid", [0] * 256, True, tok)["T"]


def test_exact_statistics_power_and_union_gates():
    assert sc1.mcnemar(13, 0) == 2**-13
    assert sc1.mcnemar(0, 0) == 1
    assert sc1.mcnemar(4, 0) == 0.0625
    assert sc1.mcnemar(5, 0) == 0.03125
    assert sc1.exact_power(256, 0.2, 0.05)["test"] == pytest.approx(0.5086, abs=0.00005)
    assert sc1.clopper_pearson(0, 256)[0] == 0
    assert sc1.clopper_pearson(256, 256)[1] == 1
    pairs = []
    for i in range(256):
        row = {
            a: {
                "success": a == "clf" and i < 13,
                "flags": {"F": False},
                "corruption": False,
                "latency": {"total": 1},
            }
            for a in ("clf", "rule")
        }
        pairs.append({"id": str(i), "arms": row})
    summary = sc1.analyze_pairs(pairs)
    assert summary["adopt"] == "clf" and summary["b"] == 13
    for pair in pairs[:3]:
        pair["arms"]["clf"]["flags"]["F"] = True
    assert sc1.analyze_pairs(pairs)["adopt"] == "rule"
    assert sc1.analyze_pairs(pairs)["U"] == 3
    with pytest.raises(ValueError, match="256"):
        sc1.analyze_pairs(pairs[:-1])


def test_sampler_digest_and_assignment_attempt_invariance():
    for bad_index in (True, 1.5):
        with pytest.raises(ValueError):
            episodes.stream_digest("setup", bad_index, "author")
    expected = hashlib.sha256(b"SC1-v2|20260904|setup|0|author|0").hexdigest()
    assert expected == (
        "5a1059b0553e7578e9e3577f90d5d1f43ecb96e118a371d912d9211d82eac83d"
    )
    assert episodes.stream_digest("setup", 0, "author") == expected
    a = episodes.commission_slot("setup", 0, attempt=0)
    b = episodes.commission_slot("setup", 0, attempt=2)
    assert a["assignments"] == b["assignments"]
    assert a["seeds"]["author"] == expected
    assert a["seeds"]["literals"] != b["seeds"]["literals"]
    assert a["assignments"]["author"] == episodes.AUTHORS[int(expected[:2], 16) >> 6]


@pytest.fixture
def source():
    return episodes.load_sources(ROOT / "data/sc1/smoke")[0]


def test_expander_determinism_reference_six_negatives_and_reject_all(source):
    tok = CharTokenizer()
    first = episodes.expand_source(source, tok)
    assert first == episodes.expand_source(source, tok)
    report = episodes.validate_episode(first, source, tok)
    assert report["reference"]["success"]
    assert len(first["mutations"]) == 6
    assert len({m["output"] for m in first["mutations"]}) == 6
    assert all(not row["success"] for row in report["mutations"])
    assert all(m["obligation_ids"] for m in first["mutations"])
    first["checker"].append(
        {"kind": "forbidden_substrings", "values": [""], "id": "reject-all"}
    )
    with pytest.raises(ValueError):
        episodes.validate_episode(first, source, tok)
    impossible_source = copy.deepcopy(source)
    impossible_source["obligations"].append(
        {"id": "reject-all", "kind": "forbidden_substrings", "values": [""]}
    )
    impossible = episodes.expand_source(impossible_source, tok)
    with pytest.raises(ValueError, match="reference failed"):
        episodes.validate_episode(impossible, impossible_source, tok)


def test_checker_strict_json_complete_protected_and_fresh_state(source):
    ep = episodes.expand_source(source, CharTokenizer())
    initial = copy.deepcopy(ep["initial_state"])
    good = episodes.run_checker(ep, ep["reference"])
    assert good["success"]
    assert not episodes.run_checker(ep, "```json\n" + ep["reference"] + "\n```")[
        "schema_valid"
    ]
    for bad in ('{"a":1,"a":2}', '{"a":NaN}', "true false"):
        assert not episodes.run_checker(ep, bad)["schema_valid"]
    assert ep["initial_state"] == initial
    collateral = next(m for m in ep["mutations"] if m["slot"] == "collateral edit")
    assert episodes.run_checker(ep, collateral["output"])["corruption"]
    assert not episodes.json_equal(True, 1)
    assert episodes.json_equal(1, 1.0)


def test_fingerprint_ignores_names_preserves_causality(source):
    renamed = copy.deepcopy(source)
    renamed["entities"][0]["name"] = "Different Fictional Name"
    assert episodes.sibling_fingerprint(source) == episodes.sibling_fingerprint(renamed)
    renamed["source_graph"]["events"].append({"kind": "additional_causal_event"})
    assert episodes.sibling_fingerprint(source) != episodes.sibling_fingerprint(renamed)


class FakeTrunk:
    cfg = Qwen3Config(
        n_layer=2,
        d_model=8,
        n_head=2,
        n_kv_head=1,
        head_dim=4,
        d_ff=16,
        vocab=256,
        rope_theta=10000,
        rms_eps=1e-6,
        n_ctx=40960,
        tie_word_embeddings=True,
    )

    def __init__(self):
        self.calls = []

    def __call__(self, tokens, *, cache, **kwargs):
        n = tokens.shape[1]
        self.calls.append((cache.length, tokens.tolist(), kwargs))
        data = torch.arange(cache.length, cache.length + n).reshape(1, 1, n, 1).float()
        for i in range(self.cfg.n_layer):
            cache.k[i] = (
                data.clone() if cache.k[i] is None else torch.cat((cache.k[i], data), 2)
            )
            cache.v[i] = cache.k[i].clone()
        cache.length += n
        return torch.zeros(1, n, 256)


def test_two_stage_cache_positions_and_intervention_abort():
    model = FakeTrunk()
    cache = KVCache(model.cfg)
    audit = sc1.InterventionCounter()
    _, record = sc1.prefill_sc1(
        model,
        cache,
        torch.arange(20).reshape(1, 20),
        history_end=15,
        evict_range=(3, 12),
        pins=[(6, 8)],
        interventions=audit,
    )
    assert [c[0] for c in model.calls] == [0, 15]
    assert record["retained_positions"] == [0, 1, 2, 6, 7, 12, 13, 14]
    assert cache.length == 20
    assert cache.k[1].flatten().tolist() == [
        0,
        1,
        2,
        6,
        7,
        12,
        13,
        14,
        15,
        16,
        17,
        18,
        19,
    ]
    with pytest.raises(RuntimeError, match="intervention"):
        audit.invoke("residual_steering", lambda: None)
    with pytest.raises(RuntimeError, match="intervention"):
        audit.assert_zero()


def test_final_refuses_missing_setup_before_backend_loading(tmp_path):
    from scripts.sc1 import main

    with pytest.raises((ValueError, SystemExit), match="setup"):
        main(["final", str(tmp_path), "--out", str(tmp_path / "out")])


def test_completed_arm_immutable_and_interrupted_second_resume(tmp_path):
    store = sc1.RunStore(tmp_path, "manifest")
    store.start("ep", "clf", "attempt-1")
    row = {
        "manifest_id": "manifest",
        "episode_id": "ep",
        "arm": "clf",
        "attempt_id": "attempt-1",
    }
    store.complete(row)
    original = store.arm_path("ep", "clf").read_bytes()
    store.start("ep", "rule", "attempt-2")
    with pytest.raises(RuntimeError, match="interruption"):
        store.pending("ep", ["clf", "rule"])
    store.interrupt("ep", "rule", "attempt-2", "host_loss", 1.5)
    assert store.pending("ep", ["clf", "rule"]) == ["rule"]
    assert store.arm_path("ep", "clf").read_bytes() == original
    with pytest.raises(RuntimeError, match="completed"):
        store.complete({**row, "success": False})
    store.arm_path("ep", "clf").write_text(json.dumps({**row, "changed": True}))
    with pytest.raises(RuntimeError, match="hash"):
        store.pending("ep", ["clf", "rule"])


def test_cost_projection_reserves_attempt_and_never_decreases():
    meter = sc1.CostMeter(
        spent=28701, estimates={"prefill": 0, "token": 0, "cpu": 0, "check": 0}
    )
    assert not meter.can_start(1)
    meter = sc1.CostMeter(
        estimates={"prefill": 2, "token": 0.01, "cpu": 1, "check": 0.1}
    )
    assert meter.project(512) == pytest.approx(512 * 1.25 * (2 + 2.56 + 1 + 0.1))
    meter.observe(
        {"prefill": 1, "token": 0.001, "cpu": 0.1, "check": 0.01}, 9000, 10000
    )
    assert meter.estimates["prefill"] == 2


def test_allocation_checkpoint_recovery_includes_crash_and_idle_time(tmp_path):
    now = [10.0]
    clock = lambda: now[0]  # noqa: E731
    path = tmp_path / "cost.json"
    allocation = sc1.AllocationLedger(path, "m", sc1.CostMeter(spent=20), clock=clock)
    allocation.begin("process-one")
    now[0] = 15
    allocation.checkpoint()
    assert allocation.meter.spent == 25
    restored = sc1.AllocationLedger(path, "m", clock=clock)
    with pytest.raises(ValueError, match="interruption"):
        restored.begin("process-two")
    restored.recover(
        {
            "allocation_id": "process-one",
            "reason": "host_loss",
            "elapsed": 12,
            "evidence": "host event 123",
        }
    )
    assert restored.meter.spent == 32
    restored.begin("process-two")
    now[0] = 18
    restored.checkpoint(close=True)
    assert restored.meter.spent == 35


def test_fake_generation_consumer_records_all_fields_and_rechecks_interventions(source):
    ep = episodes.expand_source(source, CharTokenizer())

    class Backend:
        def generate(self, layout, pins, arm, interventions, deadline_at):
            return {
                "ids": token_list,
                "cache": {},
                "prefill": 0.2,
                "generation": 0.1,
                "worst_token": 0.01,
                "failure": None,
                "peak_device_bytes": 0,
            }

    token_list = [ord(c) for c in ep["reference"]]
    row = sc1.run_arm(
        ep,
        "rule",
        CharTokenizer(),
        Backend(),
        None,
        manifest_id="m",
        order=["clf", "rule"],
        attempt_id="a",
        initialization_id="i",
    )
    assert set(row) == sc1.ARM_FIELDS
    assert row["success"] and row["checker"]["success"]
    assert row["selection"]["candidate_hash"]
    assert row["latency"]["total"] > 0


def test_smoke_all_styles_and_six_mutations_use_real_local_tokenizer():
    from scripts.sc1 import load_tokenizer

    bank, report = episodes.validate_bank(ROOT / "data/sc1/smoke", load_tokenizer("4b"))
    assert len(bank) == 8 and report["mutations_fail"] == 48
    assert {ep["task_spec"]["kind"] for ep in bank} == {"json_patch", "tool"}
    tool = next(ep for ep in bank if ep["task_spec"]["kind"] == "tool")
    reference = episodes.parse_json(tool["reference"])
    before = copy.deepcopy(tool["initial_state"])
    reference["arguments"]["changes"]["v"] = False
    verdict = episodes.run_checker(tool, json.dumps(reference))
    assert not verdict["schema_valid"] and not verdict["corruption"]
    assert verdict["result"] is None and tool["initial_state"] == before
    corrupted = copy.deepcopy(tool["expected_state"])
    corrupted["unpermitted"] = {"v": "extra", "p": "extra"}
    assert episodes.check_result(tool, corrupted)["corruption"]


def test_text_checker_normalization_and_protected_extras():
    ep = {
        "task_spec": {"kind": "text", "permitted_paths": [""]},
        "initial_state": "Draft",
        "expected_artifact": "Lantern\n\nHarbor",
        "expected_state": None,
        "checker": [
            {"id": "lines", "kind": "required_lines", "values": ["Lantern", "Harbor"]}
        ],
        "protected_set": [
            {"id": "no_extra", "kind": "forbidden_substrings", "values": ["Extra"]}
        ],
    }
    assert episodes.run_checker(ep, "Lantern  \r\n\r\n\r\nHarbor\t")["success"]
    bad = episodes.run_checker(ep, "Lantern\n\nHarbor\nExtra")
    assert not bad["success"] and bad["corruption"]


def test_setup_certificate_recomputes_counts_not_claims(tmp_path):
    from scripts.sc1 import require_setup

    payload = {
        "manifest_id": "m",
        "full_passes": 24,
        "evicted_passes": 16,
        "passed": True,
        "projection_seconds": 100,
        "cost": {"samples": [1]},
        "output_hashes": {},
        "episode_hashes": {},
    }
    payload["certificate_hash"] = sc1.digest(payload)
    path = tmp_path / "cert.json"
    sc1.atomic_json(path, payload)
    with pytest.raises(ValueError, match="32|setup"):
        require_setup(path, "m", committed=False)


def test_setup_workflow_cpu_diagnostics_and_gate_certificate(
    tmp_path, source, monkeypatch
):
    from types import SimpleNamespace

    from scripts import sc1 as cli

    tokenizer = CharTokenizer()
    seed_episode = episodes.expand_source(source, tokenizer)
    bank = []
    for i in range(32):
        ep = copy.deepcopy(seed_episode)
        ep.update(id=f"cpu-setup-{i}", pool="setup", index=i)
        bank.append(ep)

    class Backend:
        def __init__(self, *args):
            self.evicted = 0

        def generate(self, layout, pins, arm, interventions, deadline_at):
            assert arm in {"full", "evicted"}
            if arm == "evicted":
                self.evicted += 1
            text = (
                seed_episode["reference"]
                if arm == "full" or self.evicted > 16
                else "[]"
            )
            return {
                "ids": [ord(c) for c in text],
                "cache": {},
                "prefill": 0.001,
                "generation": 0.001,
                "worst_token": 0.0001,
                "failure": None,
                "peak_device_bytes": 0,
            }

    monkeypatch.setattr(
        cli, "verify_determinism", lambda *a: {"allocated_seconds": 1.0}
    )
    args = SimpleNamespace(
        mode="setup",
        out=tmp_path,
        trunk="4b",
        setup_certificate=None,
        determinism_certificate=None,
        interruption_evidence=None,
    )
    result = cli.run_study(
        args,
        {"manifest_id": "cpu-fixture"},
        bank,
        tokenizer,
        backend_factory=Backend,
        scorer_factory=lambda *a: lambda texts, **kw: [0.0] * len(texts),
    )
    assert result["status"] == "SETUP PASSED"
    cert = cli.require_setup(
        tmp_path / "setup-certificate.json", "cpu-fixture", committed=False
    )
    assert cert["full_passes"] == 32 and cert["evicted_passes"] == 16
    assert len(list((tmp_path / "setup").glob("*.cpu.json"))) == 32
    assert not list((tmp_path / "setup").glob("*.clf.json"))
    cert["evicted_passes"] = 0
    cert["certificate_hash"] = sc1.digest(
        {k: v for k, v in cert.items() if k != "certificate_hash"}
    )
    sc1.atomic_json(tmp_path / "setup-certificate.json", cert)
    with pytest.raises(ValueError, match="pass counts"):
        cli.require_setup(
            tmp_path / "setup-certificate.json", "cpu-fixture", committed=False
        )


def test_candidate_segmentation_matches_frozen_leg_a_helper():
    from stencil.bfcl import select_history_spans

    tok = CharTokenizer()
    ep = public_history()
    ep["turns"][0]["text"] = "amber " * 70 + ". Further copper."
    layout = sc1.render_episode(ep, tok)
    rows, _ = sc1.build_sc1_candidates(layout, tok)
    messages = [{"role": t["role"], "content": t["text"]} for t in ep["turns"]]
    messages.append({"role": "user", "content": ep["final_request"]})
    _, frozen, _ = select_history_spans(
        tok, layout["text"], messages, lambda texts, **kw: [0.6] * len(texts)
    )
    expected = [
        {k: c[k] for k in ("text", "role", "message_index", "char_span", "span")}
        for c in frozen
        if layout["P"] <= c["span"][0] < c["span"][1] <= layout["R"]
    ]
    actual = [{k: c[k] for k in expected[0]} for c in rows]
    assert actual == expected
    assert all(c["span"][1] - c["span"][0] <= 128 for c in rows)
