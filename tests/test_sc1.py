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
        {
            "id": "reject-all",
            "kind": "forbidden_substrings",
            "values": [""],
            "evidence_ids": ["governing", "fact"],
        }
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

    monkeypatch.setattr(cli, "STUDY_REGISTRY", tmp_path / "registry")
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
        {
            "manifest_id": "cpu-fixture",
            "study_id": str(tmp_path),
            "registration_hash": "test",
            "execution_root": str(tmp_path),
        },
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


# Review regressions use the actual compiler, validator and scheduling consumers.
@pytest.fixture(scope="module")
def real_tokenizer():
    from scripts.sc1 import load_tokenizer

    return load_tokenizer("4b")


def validate_source(source, tokenizer):
    ep = episodes.expand_source(source, tokenizer)
    episodes.validate_episode(ep, source, tokenizer)
    return ep


def versions():
    return {
        a: {
            "immutable_version": a + "-frozen",
            "settings": {"temperature": 0},
            "neutral_template": "Write one source under the supplied contract.",
        }
        for a in episodes.AUTHORS
    }


@pytest.mark.parametrize("pool", ["smoke", "setup", "final"])
@pytest.mark.parametrize("attempt", [0, 1, 2])
def test_astra_f4_author_envelope_is_blind(pool, attempt):
    request = episodes.commissioning_request(
        "contract",
        episodes.SCHEMA,
        versions(),
        pool,
        0,
        attempt,
        feedback="Fix the missing source field." if attempt else None,
    )
    assignment = request["input"]["assignment"]
    private = {"order", "setup_order", "clf", "rule", "full", "evicted"}

    def atoms(value):
        if isinstance(value, dict):
            return set(value) | set().union(*(atoms(v) for v in value.values()))
        if isinstance(value, list):
            return set().union(*(atoms(v) for v in value))
        return {value} if isinstance(value, str) else set()

    assert not private & atoms(request["input"])
    slot = episodes.commission_slot(pool, 0, attempt)
    assert assignment["assignments"] == slot["assignments"]
    assert assignment["seeds"]["literals"] == slot["seeds"]["literals"]
    assert request["input_hash"] == sc1.digest(request["input"])


def test_astra_f5_missing_literal_inventory_cannot_leak(source, real_tokenizer):
    source.pop("answer_literals")
    source["final_request"] += sc1.canonical(source["work"]["patch"])
    with pytest.raises(ValueError, match="literal"):
        validate_source(source, real_tokenizer)


@pytest.mark.parametrize("surface", ["system", "tools", "final_request", "recent"])
def test_astra_f5_every_answer_literal_excluded(source, real_tokenizer, surface):
    for literal in source["answer_literals"]:
        changed = copy.deepcopy(source)
        value = literal["value"] if isinstance(literal, dict) else literal
        if surface == "recent":
            changed["turns"][-1]["text"] += " Remember " + str(value)
        elif surface == "tools":
            changed["tools"] = [{"const": value}]
        else:
            changed[surface] += " Answer " + str(value)
        with pytest.raises(ValueError, match="leakage|literal|schema"):
            validate_source(changed, real_tokenizer)


@pytest.mark.parametrize("mutation", ["scope", "authority", "public_return"])
def test_astra_f6_source_boundary_through_bank(tmp_path, real_tokenizer, mutation):
    source = copy.deepcopy(episodes.load_sources(ROOT / "data/sc1/smoke")[5])
    if mutation == "scope":
        source["instruction_trajectory"][0]["scope"] = "switched"
    elif mutation == "authority":
        source["turns"][source["instruction_trajectory"][0]["turn"]]["role"] = "tool"
    else:
        source["state_trace"]["events"] = [
            {
                "turn": 5,
                "call": {"name": "get", "arguments": {"id": "${TARGET}"}},
                "return": {"v": "unfilled", "p": "fixed"},
                "public_text": '{"p":"fixed","v":"impossible state"}',
            }
        ]
        source["turns"][5]["text"] = source["state_trace"]["events"][0]["public_text"]
    sc1.atomic_json(tmp_path / "bad.source.json", source)
    with pytest.raises(ValueError, match="scope|authority|trace|return"):
        episodes.validate_bank(tmp_path, real_tokenizer)


def test_astra_f7_whitespace_negatives_are_one_attack(source, real_tokenizer):
    bad = [{"op": "replace", "path": "/p", "value": "wrong"}]
    source["attacks"] = {
        slot: {
            "output": json.dumps(bad, indent=i),
            "obligation_ids": ["target", "keep"],
        }
        for i, slot in enumerate(episodes.ATTACKS)
        if slot != "empty output"
    }
    with pytest.raises(ValueError, match="duplicate|applicab|attack"):
        validate_source(source, real_tokenizer)


def text_episode():
    return {
        "task_spec": {"kind": "text", "permitted_paths": [], "editable_lines": [0]},
        "initial_state": "Draft\nHarbor",
        "expected_artifact": "Lantern\nHarbor",
        "expected_state": None,
        "checker": [{"id": "code", "kind": "required_lines", "values": ["Lantern"]}],
        "protected_set": [
            {"id": "keep", "kind": "required_lines", "values": ["Harbor"]}
        ],
    }


def test_astra_f8_text_unauthorized_insertions_and_deletions():
    ep = text_episode()
    assert episodes.run_checker(ep, "Lantern\nHarbor")["success"]
    assert not episodes.run_checker(ep, "Wrong\nHarbor")["corruption"]
    for text in (
        "Intrusion\nLantern\nHarbor",
        "Lantern\nIntrusion\nHarbor",
        "Lantern\nHarbor\nIntrusion",
        "Lantern",
        "Lantern\nChanged",
        "Lantern\nHarbor\n" + "Intrusion\n" * 41,
    ):
        assert episodes.run_checker(ep, text)["corruption"], text
    pairs = [
        {
            "id": str(i),
            "arms": {
                arm: {
                    "success": arm == "clf" and i < 13,
                    "flags": {"F": False},
                    "corruption": False,
                    "latency": {"total": 1},
                }
                for arm in ("clf", "rule")
            },
        }
        for i in range(256)
    ]
    assert sc1.analyze_pairs(pairs)["adopt"] == "clf"
    pairs[0]["arms"]["clf"]["corruption"] = episodes.run_checker(
        ep, "Lantern\nHarbor\nIntrusion"
    )["corruption"]
    assert sc1.analyze_pairs(pairs)["adopt"] == "rule"


@pytest.mark.parametrize("kind", ["json_patch", "tool"])
def test_astra_f9_exact_json_numerics(kind):
    spec = {
        "kind": kind,
        "fields": {"v": "number", "p": "string"},
        "permitted_paths": ["/v" if kind == "json_patch" else "/target/v"],
        "operations": ["update"],
    }
    initial, expected = {"v": 0, "p": "fixed"}, {"v": 9786, "p": "fixed"}
    ep = {
        "task_spec": spec,
        "initial_state": initial if kind == "json_patch" else {"target": initial},
        "expected_artifact": expected,
        "expected_state": {"target": expected},
        "checker": [],
        "protected_set": [],
    }
    for number in ("9786", "9786.0", "9.786e3", "9786.0000000000000000000001"):
        output = (
            '[{"op":"replace","path":"/v","value":' + number + "}]"
            if kind == "json_patch"
            else '{"name":"update","arguments":{"id":"target","changes":{"v":'
            + number
            + "}}}"
        )
        assert episodes.run_checker(ep, output)["success"] == (
            number != "9786.0000000000000000000001"
        )
    assert episodes.json_equal(episodes.parse_json("-0.0"), 0)
    assert not episodes.json_equal(
        episodes.parse_json("1e30"),
        episodes.parse_json("1000000000000000000000000000001"),
    )
    for bad in ("NaN", "Infinity", '{"x":1,"x":2}'):
        with pytest.raises(ValueError):
            episodes.parse_json(bad)


def reviewed_pair(real_tokenizer):
    pair = [
        episodes.expand_source(s, real_tokenizer)
        for s in episodes.load_sources(ROOT / "data/sc1/smoke")[:2]
    ]
    pair.sort(key=lambda e: e["source_id"])
    left, right = pair
    left["pool"] = right["pool"] = "final"
    left["provenance"]["session_id"] = "author-left"
    right["provenance"]["session_id"] = "author-right"
    left["distinctness_review"]["pairs"] = {
        right["source_id"]: {
            "signed": True,
            "decision": "distinct",
            "reviewer": "reviewer",
            "session_id": "independent-session",
            "source_ids": [left["source_id"], right["source_id"]],
            "source_hashes": [
                left["validation"]["source_hash"],
                right["validation"]["source_hash"],
            ],
            "other_hash": right["validation"]["source_hash"],
        }
    }
    return pair


@pytest.mark.parametrize("side", [0, 1])
def test_astra_f10_pair_signatures_bind_both_sources(real_tokenizer, side):
    pair = reviewed_pair(real_tokenizer)
    episodes.independence_audit(pair)
    pair[side]["validation"]["source_hash"] = "changed"
    with pytest.raises(ValueError, match="review"):
        episodes.independence_audit(pair)


def test_astra_f12_unordered_fingerprint_alpha_equivalence(source):
    source["source_graph"]["relations"] = [
        {"relation": "first", "value": "left-literal"},
        {"relation": "second", "value": "right-literal"},
    ]
    changed = copy.deepcopy(source)
    changed["source_graph"]["relations"].reverse()
    assert episodes.sibling_fingerprint(source) == episodes.sibling_fingerprint(changed)
    changed["source_graph"]["relations"][0]["value"] = "renamed-literal"
    assert episodes.sibling_fingerprint(source) == episodes.sibling_fingerprint(changed)
    changed["source_graph"]["relations"][0]["value"] = "left-literal"
    assert episodes.sibling_fingerprint(source) != episodes.sibling_fingerprint(changed)


def test_astra_f13_commission_requires_both_freezes(tmp_path):
    from scripts.sc1 import main

    draft = tmp_path / "stage1.json"
    sc1.atomic_json(draft, {"status": "DRAFT", "authors": versions()})
    with pytest.raises(ValueError, match="registered|REGISTERED|Stage|freeze"):
        main(
            [
                "commission",
                "--stage1",
                str(draft),
                "--pool",
                "setup",
                "--index",
                "0",
                "--out",
                str(tmp_path / "out"),
            ]
        )


def test_astra_f14_unregistered_trunk_refused_before_loading(monkeypatch, tmp_path):
    from scripts import sc1 as cli

    called = []
    monkeypatch.setattr(cli, "load_tokenizer", lambda *a: called.append("tokenizer"))
    with pytest.raises(ValueError, match="4[Bb]|registered"):
        cli.main(["setup", "--trunk", "1.7b", "--out", str(tmp_path)])
    assert not called


def test_fable_h1_pressure_binds_on_every_smoke_episode(real_tokenizer):
    assert len(set(episodes.FILLER)) >= 256
    for source in episodes.load_sources(ROOT / "data/sc1/smoke"):
        ep = validate_source(source, real_tokenizer)
        layout = sc1.render_episode(ep, real_tokenizer)
        universe, _ = sc1.build_sc1_candidates(layout, real_tokenizer)
        assert sum(c["span"][1] - c["span"][0] for c in universe) >= 2 * layout["B"]
        rule = sc1.select_policy(layout, real_tokenizer, "rule")
        clf = sc1.select_policy(
            layout, real_tokenizer, "clf", lambda t, **kw: [1.0] * len(t)
        )
        assert any(s["reason"] == "budget" for s in rule["admission"]["skips"])
        assert rule["admission"]["pins"] != clf["admission"]["pins"]
        assert (
            max(len(sc1.token_ids(real_tokenizer, t["text"])) for t in ep["turns"])
            <= 600
        )


def test_fable_l1_eos_at_cap_is_not_truncation():
    assert not sc1.output_flags("x", [0] * 255 + [151645], False, CharTokenizer())["T"]


def test_fable_l2_repetition_taxonomy_discloses_period_limit():
    assert not sc1.output_flags("a b c " * 12, [], True, WordTokenizer())["R"]
    assert "period" in sc1.output_flags.__doc__


def test_fable_l3_smoke_never_reused(real_tokenizer):
    from scripts import sc1 as cli

    ep = episodes.expand_source(
        episodes.load_sources(ROOT / "data/sc1/smoke")[0], real_tokenizer
    )
    ep["pool"] = "final"
    with pytest.raises(ValueError, match="smoke"):
        cli._check_cohort([ep])


def test_fable_l4_real_tokenizer_segmentation_identity(real_tokenizer):
    from stencil.bfcl import select_history_spans

    for source in episodes.load_sources(ROOT / "data/sc1/smoke"):
        ep = episodes.expand_source(source, real_tokenizer)
        layout = sc1.render_episode(ep, real_tokenizer)
        actual, _ = sc1.build_sc1_candidates(layout, real_tokenizer)
        messages = [{"role": t["role"], "content": t["text"]} for t in ep["turns"]]
        messages.append({"role": "user", "content": ep["final_request"]})
        _, frozen, _ = select_history_spans(
            real_tokenizer,
            layout["text"],
            messages,
            lambda texts, **kw: [0.6] * len(texts),
        )
        fields = ("text", "role", "message_index", "char_span", "span")
        assert [{k: c[k] for k in fields} for c in actual] == [
            {k: c[k] for k in fields}
            for c in frozen
            if layout["P"] <= c["span"][0] < c["span"][1] <= layout["R"]
        ]
        assert "candidate_columns" in ep["layout_audit"]


def test_fable_l5_only_measured_interventions_are_reported():
    assert set(sc1.InterventionCounter().counts) == {
        "attention_amplification",
        "residual_steering",
    }


def test_fable_l6_output_directory_required():
    from scripts.sc1 import main

    with pytest.raises((ValueError, SystemExit), match="out"):
        main(["setup"])


@pytest.fixture
def scheduling(tmp_path, source, monkeypatch):
    from types import SimpleNamespace

    from scripts import sc1 as cli

    tok = CharTokenizer()
    seed = episodes.expand_source(source, tok)
    bank = []
    for i in range(256):
        ep = copy.deepcopy(seed)
        ep.update(id=f"cpu-{i}", pool="final", index=i)
        bank.append(ep)
    manifest = {
        "manifest_id": "cpu-manifest",
        "study_id": "cpu-study",
        "registration_hash": "cpu-registration",
        "execution_root": str(tmp_path / "run"),
    }
    args = SimpleNamespace(
        mode="final",
        out=tmp_path / "run",
        trunk="4b",
        setup_certificate=None,
        determinism_certificate=None,
        interruption_evidence=None,
    )
    monkeypatch.setattr(cli, "STUDY_REGISTRY", tmp_path / "registry", raising=False)
    monkeypatch.setattr(
        cli,
        "require_setup",
        lambda *a, **k: {
            "cost": {
                "spent": 1,
                "estimates": {"prefill": 0, "token": 0, "cpu": 0, "check": 0},
            },
            "certificate_hash": "setup",
            "study_id": "cpu-study",
        },
    )
    monkeypatch.setattr(cli, "verify_determinism", lambda *a: {"allocated_seconds": 1})
    calls, initializations = [], []

    class Backend:
        def __init__(self, *args):
            initializations.append(True)

        def generate(self, episode, arm):
            calls.append((episode["id"], arm))
            return None

    def arm_row(ep, arm, tokenizer, backend, scorer, **kw):
        failure = backend.generate(ep, arm)
        latency = dict.fromkeys(
            (
                "prefill",
                "worst_token",
                "render",
                "candidate",
                "scoring",
                "admission",
                "echo",
                "check",
            ),
            0.0,
        )
        latency.update(
            total=1 + kw.get("prior_elapsed", 0),
            prior_attempts=kw.get("prior_elapsed", 0),
        )
        row = dict.fromkeys(sc1.ARM_FIELDS)
        row.update(
            manifest_id=manifest["manifest_id"],
            episode_id=ep["id"],
            episode_hash=sc1.digest(ep),
            arm=arm,
            order=kw["order"],
            attempt_id=kw["attempt_id"],
            initialization_id=kw["initialization_id"],
            latency=latency,
            success=arm in {"clf", "full"} and not failure,
            failure=failure,
            input_tokens=sc1.MAX_INPUT,
            interventions=dict.fromkeys(sc1.INTERVENTIONS, 0),
            flags={"I": bool(failure), "T": False, "R": False, "F": bool(failure)},
            corruption=False,
            cache={},
            token_ids=[],
            allocated_seconds=1,
        )
        return row

    monkeypatch.setattr(sc1, "run_arm", arm_row)

    def run(backend=Backend):
        return cli.run_study(
            args,
            manifest,
            bank,
            tok,
            backend_factory=backend,
            scorer_factory=lambda *a: lambda t, **k: [0.0] * len(t),
        )

    return SimpleNamespace(
        args=args,
        manifest=manifest,
        bank=bank,
        tok=tok,
        run=run,
        backend=Backend,
        calls=calls,
        inits=initializations,
        arm_row=arm_row,
        cli=cli,
    )


def seed_completions(scheduling, count, spent=20000, prefill=20):
    s = scheduling
    root = s.args.out / s.args.mode
    store = sc1.RunStore(root, s.manifest["manifest_id"])
    originals = {}
    arms = ["clf", "rule"] if s.args.mode == "final" else ["full", "evicted"]
    for i in range(count):
        ep, arm = s.bank[i // 2], arms[i % 2]
        attempt = f"seed-{i}"
        store.start(ep["id"], arm, attempt)
        order = episodes.commission_slot(s.args.mode, ep["index"])[
            "order" if s.args.mode == "final" else "setup_order"
        ]
        row = s.arm_row(
            ep,
            arm,
            s.tok,
            s.backend(),
            None,
            order=order,
            attempt_id=attempt,
            initialization_id="seed",
        )
        store.complete(row)
        path = store.arm_path(ep["id"], arm)
        originals[path] = path.read_bytes()
    meter = sc1.CostMeter(
        spent=spent, estimates={"prefill": prefill, "token": 0, "cpu": 0, "check": 0}
    )
    sc1.AllocationLedger(
        s.args.out / "cost.json", s.manifest["study_id"], meter
    ).checkpoint()
    s.calls.clear()
    s.inits.clear()
    return originals


def test_astra_f1_scheduler_incremental_accounting(scheduling, monkeypatch):
    s = scheduling
    reads = []
    original = Path.read_text

    def read(path, *a, **kw):
        raw = original(path, *a, **kw)
        if path.name == "attempts.jsonl":
            reads.append(len(raw))
            assert len(reads) <= 2, "journal replay per attempt"
        return raw

    monkeypatch.setattr(Path, "read_text", read)
    original_arm = s.arm_row

    def realistic(*args, **kwargs):
        row = original_arm(*args, **kwargs)
        row["cache"] = {
            "layers": [
                {"positions": list(range(1224)), "width": 1224} for _ in range(36)
            ]
        }
        return row

    monkeypatch.setattr(sc1, "run_arm", realistic)
    assert s.run()["status"].startswith("COMPLETE")
    assert len(s.calls) == 512
    assert len(reads) <= 2, (len(reads), sum(reads))
    path = s.args.out / "final/cpu-0.clf.json"
    path.write_text(path.read_text() + " ")
    with pytest.raises(RuntimeError, match="hash"):
        sc1.RunStore(s.args.out / "final", s.manifest["manifest_id"])


@pytest.mark.parametrize("state", ["complete", "invalid", "cap", "setup-failed"])
def test_astra_f2_output_cannot_reset_execution(scheduling, state):
    s = scheduling
    if state == "setup-failed":
        s.args.mode = "setup"
        s.bank = s.bank[:32]
        for ep in s.bank:
            ep["pool"] = "setup"
    # Bind before a stop; changing the output location must always refuse.
    s.args.out.mkdir(parents=True)
    if state == "invalid":
        sc1.atomic_json(s.args.out / "invalid.json", {"cause": "defect"})
    elif state == "complete":
        seed_completions(s, 1, spent=28600, prefill=20)
    else:
        seed_completions(s, 0, spent=28600, prefill=20)
    try:
        s.run()
    except ValueError:
        pass
    s.inits.clear()
    old_cost = (
        (s.args.out / "cost.json").read_bytes()
        if (s.args.out / "cost.json").exists()
        else None
    )
    original_out = s.args.out
    s.args.out = s.args.out.parent / "new-output"

    class ForbiddenBackend:
        def __init__(self, *args):
            pytest.fail("backend initialized for duplicate study")

    with pytest.raises(ValueError, match="study|execution|output|registered"):
        s.run(ForbiddenBackend)
    assert not s.inits
    if old_cost:
        assert (original_out / "cost.json").read_bytes() == old_cost


def test_astra_f3_resume_projects_only_missing_arms(scheduling):
    s = scheduling
    originals = seed_completions(s, 510)
    store = sc1.RunStore(s.args.out / "final", s.manifest["manifest_id"])
    for arm in ("clf", "rule"):
        store.start("cpu-255", arm, "lost-" + arm)
        store.interrupt(
            "cpu-255", arm, "lost-" + arm, "host_loss", 1.5, "CPU fixture loss"
        )
    assert s.run()["status"].startswith("COMPLETE")
    assert len(s.calls) == 2
    assert all(p.read_bytes() == raw for p, raw in originals.items())
    for arm in ("clf", "rule"):
        row = episodes.parse_json(store.arm_path("cpu-255", arm).read_text())
        assert row["latency"]["prior_attempts"] == 1.5


def test_fable_m1_setup_resume_projection(scheduling):
    s = scheduling
    s.args.mode = "setup"
    del s.bank[32:]
    for ep in s.bank:
        ep["pool"] = "setup"
    originals = seed_completions(s, 60, spent=28000, prefill=10)
    result = s.run()
    assert len(s.calls) == 4, result
    assert (s.args.out / "setup-certificate.json").exists()
    assert all(p.read_bytes() == raw for p, raw in originals.items())


def test_astra_f15_projection_reserves_future_initialization(scheduling, monkeypatch):
    s = scheduling
    s.args.mode = "setup"
    del s.bank[32:]
    for ep in s.bank:
        ep["pool"] = "setup"
    original = s.backend

    class SlowInit(original):
        def __init__(self, *args):
            super().__init__(*args)
            now[0] += 100

    now = [1.0]
    monkeypatch.setattr(s.cli.time, "monotonic", lambda: now[0])
    result = s.run(SlowInit)
    cert = json.loads((s.args.out / "setup-certificate.json").read_text())
    assert cert["cost"]["remaining_initialization"] >= 100, result
    assert cert["projection_seconds"] >= cert["cost"]["spent"] + 100


def test_fable_m2_device_loss_is_resumable(scheduling):
    s = scheduling
    originals = seed_completions(s, 510, spent=100, prefill=0)

    class DeviceLoss(s.backend):
        def generate(self, *args):
            raise RuntimeError("CUDA error: device-side assert triggered")

    with pytest.raises(RuntimeError, match="CUDA"):
        s.run(DeviceLoss)
    assert not (s.args.out / "invalid.json").exists()
    store = sc1.RunStore(s.args.out / "final", s.manifest["manifest_id"])
    with pytest.raises(RuntimeError, match="interruption"):
        store.pending("cpu-255", ["clf", "rule"])

    active = next(e for e in reversed(store.events()) if e["event"] == "start")
    allocation = sc1.AllocationLedger(s.args.out / "cost.json", s.manifest["study_id"])
    evidence = {
        "allocation_id": allocation.intervals[-1]["id"],
        "reason": "device_loss",
        "elapsed": allocation.intervals[-1]["elapsed"],
        "evidence": "CPU injected device failure",
        "attempts": [
            {
                "episode_id": active["episode_id"],
                "arm": active["arm"],
                "attempt_id": active["attempt_id"],
                "elapsed": 1.25,
            }
        ],
    }
    s.args.interruption_evidence = s.args.out / "interruption.json"
    sc1.atomic_json(s.args.interruption_evidence, evidence)
    assert s.run()["status"].startswith("COMPLETE")
    assert all(p.read_bytes() == raw for p, raw in originals.items())
    completed = episodes.parse_json(
        store.arm_path(active["episode_id"], active["arm"]).read_text()
    )
    assert completed["latency"]["prior_attempts"] == 1.25


def test_astra_f16_partial_journal_tail_recovery(tmp_path):
    store = sc1.RunStore(tmp_path, "m")
    store.start("ep", "clf", "a")
    prefix = store.journal.read_bytes()
    with store.journal.open("ab") as f:
        f.write(b'{"event":"completion_prepared","row":')
    recovered = sc1.RunStore(tmp_path, "m")
    assert recovered.journal.read_bytes().startswith(prefix)
    recovered.interrupt("ep", "clf", "a", "host_loss", 2, "lost host during append")
    assert recovered.pending("ep", ["clf"]) == ["clf"]
    assert any(e["event"] == "journal_tail_recovered" for e in recovered.events())


def determinism_fixture(tmp_path, monkeypatch):
    from scripts import sc1 as cli

    tokenizer = CharTokenizer()
    bank = [
        episodes.expand_source(source, tokenizer)
        for source in episodes.load_sources(ROOT / "data/sc1/smoke")[:2]
    ]
    frozen = {
        "manifest_id": "frozen",
        "trunk": "4b",
        "deployment": {"trunk": "4b"},
        "episodes": [
            {"id": ep["id"], "pool": "smoke", "hash": sc1.digest(ep)} for ep in bank
        ],
    }
    monkeypatch.setattr(cli, "verify_manifest", lambda *a, **kw: frozen)
    monkeypatch.setattr(cli, "load_manifest_bank", lambda *a: bank)
    monkeypatch.setattr(cli, "load_tokenizer", lambda *a: tokenizer)
    rows = []
    for process in ("p1", "p2"):
        for episode in bank:
            for arm in ("clf", "rule"):
                arm_row = sc1.run_arm(
                    episode,
                    arm,
                    tokenizer,
                    DeterminismFixtureBackend(),
                    lambda texts, **kw: [0.6] * len(texts),
                    manifest_id="frozen",
                    order=["clf", "rule"],
                    attempt_id=process + episode["id"] + arm,
                    initialization_id=process,
                )
                arm_path = tmp_path / f"{process}-{episode['id']}-{arm}.arm.json"
                sc1.atomic_json(arm_path, arm_row)
                prompt = sc1.render_episode(
                    episode, tokenizer, arm_row["selection"]["echo"]["insertion"]
                )
                output = {
                    "process_id": process,
                    "initialization_id": process,
                    "episode_id": episode["id"],
                    "episode_hash": sc1.digest(episode),
                    "arm": arm,
                    "token_ids": arm_row["token_ids"],
                    "input_hash": sc1.digest(prompt["ids"]),
                    "deployment_hash": sc1.digest(frozen["deployment"]),
                    "allocated_seconds": arm_row["allocated_seconds"],
                    "executable_manifest_id": "frozen",
                    "arm_path": str(arm_path),
                    "arm_hash": sc1.file_hash(arm_path),
                }
                path = tmp_path / f"{process}-{episode['id']}-{arm}.json"
                sc1.atomic_json(path, output)
                rows.append(
                    {
                        **output,
                        "output_path": str(path),
                        "output_hash": sc1.file_hash(path),
                    }
                )
    ledger = sc1.AllocationLedger(
        tmp_path / "allocation.json", "cpu-study", sc1.CostMeter(spent=10)
    )
    ledger.intervals = [
        {"id": p, "closed": True, "elapsed": 5, "base": i * 5}
        for i, p in enumerate(("p1", "p2"))
    ]
    ledger.checkpoint()
    cert = {
        "executable_manifest_id": "frozen",
        "study_id": "cpu-study",
        "outputs": rows,
        "allocated_seconds": 10,
        "allocation_path": str(ledger.path),
        "allocation_hash": sc1.file_hash(ledger.path),
        "initializations": {p: {"allocated_seconds": 5} for p in ("p1", "p2")},
    }
    path = tmp_path / "certificate.json"
    sc1.atomic_json(path, cert)
    return cli, frozen, cert, path


def test_astra_f11_each_determinism_cell_crosses_processes(tmp_path, monkeypatch):
    cli, frozen, cert, path = determinism_fixture(tmp_path, monkeypatch)
    cli.verify_determinism(path, {"executable_freeze": "frozen"})
    for row in cert["outputs"]:
        row["process_id"] = "p1" if row["episode_id"] == "smoke-00" else "p2"
    sc1.atomic_json(path, cert)
    with pytest.raises(ValueError, match="determinism|process|cell|output"):
        cli.verify_determinism(path, {"executable_freeze": "frozen"})


def test_fable_m3_determinism_entrypoint_exists():
    from scripts import sc1 as cli

    assert callable(getattr(cli, "run_determinism", None))
    with pytest.raises((ValueError, SystemExit), match="out"):
        cli.main(["determinism"])


class DeterminismFixtureBackend:
    """CPU fixture: fixed tokens, no model construction or checkpoint access."""

    def __init__(self, *args):
        pass

    def generate(self, layout, pins, arm, interventions, deadline_at):
        return {
            "ids": [111, 107],
            "cache": {},
            "prefill": 0.001,
            "generation": 0.001,
            "worst_token": 0.00001,
            "failure": None,
            "peak_device_bytes": 0,
        }


def test_fable_m3_two_cpu_subprocesses_emit_verifiable_certificate(
    tmp_path, source, monkeypatch
):
    import os
    import subprocess
    import sys

    from scripts import sc1 as cli

    sources = episodes.load_sources(ROOT / "data/sc1/smoke")[:2]
    bank = [episodes.expand_source(s, CharTokenizer()) for s in sources]
    manifest = {
        "manifest_id": "cpu-frozen",
        "trunk": "4b",
        "study_id": "cpu-determinism",
        "registration_hash": "cpu-registration",
        "execution_root": str(tmp_path / "run"),
        "deployment": {"trunk": "4b", "greedy": True},
        "episodes": [
            {"id": e["id"], "hash": sc1.digest(e), "pool": "smoke"} for e in bank
        ],
    }
    sc1.atomic_json(tmp_path / "manifest.json", manifest)
    sc1.atomic_json(tmp_path / "bank.json", bank)
    code = """
import json, runpy, sys
from pathlib import Path
from types import SimpleNamespace
from scripts import sc1 as cli
fixtures = runpy.run_path(str(Path.cwd() / "tests/test_sc1.py"))
root = Path(sys.argv[1])
manifest = json.loads((root / "manifest.json").read_text())
bank = json.loads((root / "bank.json").read_text())
cli.STUDY_REGISTRY = root / "registry"
args = SimpleNamespace(mode="determinism", out=root / "run", trunk="4b")
print(cli.run_determinism(args, manifest, bank, fixtures["CharTokenizer"](),
    backend_factory=fixtures["DeterminismFixtureBackend"],
    scorer_factory=lambda *a: lambda texts, **kw: [0.6] * len(texts)))
"""
    for _ in range(2):
        process = subprocess.run(
            [sys.executable, "-c", code, str(tmp_path)],
            cwd=ROOT,
            env={
                **os.environ,
                "CUDA_VISIBLE_DEVICES": "",
                "PYTHONDONTWRITEBYTECODE": "1",
            },
            capture_output=True,
            text=True,
            check=False,
        )
        assert process.returncode == 0, process.stdout + process.stderr
    monkeypatch.setattr(cli, "verify_manifest", lambda *a, **k: manifest)
    monkeypatch.setattr(cli, "load_manifest_bank", lambda *a: bank)
    monkeypatch.setattr(cli, "load_tokenizer", lambda *a: CharTokenizer())
    path = tmp_path / "run/determinism-certificate.json"
    cert = cli.verify_determinism(path, {**manifest, "executable_freeze": "cpu-frozen"})
    assert len(cert["outputs"]) == 8
    cert["outputs"][0]["token_ids"][0] += 1
    sc1.atomic_json(path, cert)
    with pytest.raises(ValueError, match="determinism|output"):
        cli.verify_determinism(path, {**manifest, "executable_freeze": "cpu-frozen"})


def test_astra_f16_completed_generation_failure_is_not_interruption(source):
    ep = episodes.expand_source(source, CharTokenizer())

    class Backend(DeterminismFixtureBackend):
        def generate(self, *args):
            raise sc1.GenerationFailure("decoder stopped", ids=[111, 107])

    row = sc1.run_arm(
        ep,
        "rule",
        CharTokenizer(),
        Backend(),
        None,
        manifest_id="m",
        order=["rule", "clf"],
        attempt_id="a",
        initialization_id="i",
    )
    assert row["failure"] == "decoder stopped" and not row["success"]
    assert row["token_ids"] == [111, 107]


@pytest.mark.parametrize("issue", ["same_reviewer", "left_changed", "right_changed"])
def test_astra_f10_independent_review_sessions(real_tokenizer, issue):
    pair = reviewed_pair(real_tokenizer)
    review = pair[0]["distinctness_review"]["pairs"][pair[1]["source_id"]]
    if issue == "same_reviewer":
        review["session_id"] = pair[1]["provenance"]["session_id"]
    else:
        pair[issue == "right_changed"]["validation"]["source_hash"] = "changed"
    with pytest.raises(ValueError, match="review"):
        episodes.independence_audit(pair)


@pytest.mark.parametrize("issue", ["missing", "reversed", "wrong_role"])
def test_astra_f6_nonempty_trace_has_public_correspondence(
    tmp_path, real_tokenizer, issue
):
    source = episodes.load_sources(ROOT / "data/sc1/smoke")[5]
    validate_source(source, real_tokenizer)
    if issue == "missing":
        source["state_trace"]["events"].clear()
    elif issue == "wrong_role":
        source["turns"][5]["role"] = "assistant"
    else:
        event = copy.deepcopy(source["state_trace"]["events"][0])
        event["turn"] = 4
        source["turns"][4] = {"role": "tool", "text": event["public_text"]}
        source["filler_turns"].remove(4)
        source["state_trace"]["events"].append(event)
    sc1.atomic_json(tmp_path / "trace.source.json", source)
    with pytest.raises(ValueError, match="trace|return"):
        episodes.validate_bank(tmp_path, real_tokenizer)


def test_astra_f7_numeric_key_order_and_text_negative_identity():
    ep = {"task_spec": {"kind": "json_patch"}}
    assert episodes.mutation_key(ep, '{"a":1.0,"b":2}') == episodes.mutation_key(
        ep, '{"b":2e0,"a":1}'
    )
    ep["task_spec"]["kind"] = "text"
    assert episodes.mutation_key(ep, "x  \r\n\r\n\r\ny") == episodes.mutation_key(
        ep, "x\n\ny"
    )


def test_astra_f8_validated_text_source_rejects_unauthorized_lines(
    source, real_tokenizer
):
    source["task_spec"].update(kind="text", permitted_paths=[], editable_lines=[0])
    source["initial_state"] = "Draft\nHarbor"
    source["state_trace"] = {"start": source["initial_state"], "events": []}
    source["work"] = {"text": "${VALUE}\nHarbor"}
    instruction = (
        "Write the approved code as the first line and Harbor as the second line. "
        "Preserve Harbor and add no other lines."
    )
    source["turns"][0]["text"] = instruction
    source["instruction_trajectory"][0]["evidence_text"] = instruction
    source["obligations"] = [
        {
            "id": "target",
            "kind": "required_lines",
            "values": ["${VALUE}"],
            "evidence_ids": ["governing", "fact"],
        }
    ]
    source["protected_set"] = [
        {"id": "keep", "kind": "required_lines", "values": ["Harbor"]}
    ]
    source["answer_literals"].append(
        {
            "value": "Harbor",
            "type": "string",
            "evidence_ids": ["governing"],
            "obligation_ids": ["target"],
        }
    )
    source["attacks"] = {
        "collateral edit": {"output": "${VALUE}\nDamaged", "obligation_ids": ["keep"]}
    }
    source["inapplicable"]["wrong entity"] = (
        "The raw artifact has no alternative target entity."
    )
    ep = validate_source(source, real_tokenizer)
    assert episodes.run_checker(ep, ep["reference"] + "\nIntrusion")["corruption"]
    assert not episodes.run_checker(ep, "Wrong\nHarbor")["corruption"]


@pytest.mark.parametrize("kind,index", [("json_patch", 0), ("tool", 5)])
def test_astra_f9_validated_numeric_source(kind, index, real_tokenizer):
    source = episodes.load_sources(ROOT / "data/sc1/smoke")[index]
    source["literal_specs"]["VALUE"] = {"type": "integer"}
    source["answer_literals"][0]["type"] = "integer"
    source["task_spec"]["fields"]["v"] = "number"
    source["literal_specs"]["OLD"] = {"type": "integer"}
    if kind == "json_patch":
        source["task_spec"]["fields"]["p"] = "number"
        source["initial_state"] = {"v": 0, "p": 10}
        source["state_trace"]["start"] = copy.deepcopy(source["initial_state"])
        source["attacks"]["collateral edit"]["output"][1]["value"] = -1
    else:
        for state in (source["initial_state"], source["state_trace"]["start"]):
            state["${TARGET}"]["v"] = 0
            state["${GUARD}"]["v"] = 7
        event = source["state_trace"]["events"][0]
        event["return"]["v"] = 0
        event["public_text"] = episodes.public_return_text(
            event["call"], event["return"]
        )
        source["turns"][event["turn"]]["text"] = event["public_text"]
    ep = validate_source(source, real_tokenizer)
    value = ep["filler_manifest"]["literal_values"]["VALUE"]
    reference = episodes.parse_json(ep["reference"])
    assert episodes.run_checker(ep, ep["reference"])["success"]
    exact = ep["reference"].replace(str(value), str(value) + ".00000000000000000001")
    assert not episodes.run_checker(ep, exact)["success"]
    if kind == "tool":
        reference["arguments"]["changes"]["v"] = True
    else:
        reference[0]["value"] = True
    assert not episodes.run_checker(ep, sc1.canonical(reference))["schema_valid"]


def test_astra_f13_acceptance_checks_retained_input_and_retries(tmp_path, source):
    from scripts import sc1 as cli

    version_map = versions()
    for author in version_map.values():
        author["provider"] = "cpu-fixture-provider"
    slot = episodes.commission_slot("setup", 0)
    family = slot["assignments"]["author"]
    request = episodes.commissioning_request(
        (ROOT / cli.CONTRACT).read_text(), episodes.SCHEMA, version_map, "setup", 0
    )
    transcript = {
        "session_id": "isolated-author",
        "provider": "cpu-fixture-provider",
        "version": version_map[family]["immutable_version"],
        "settings": version_map[family]["settings"],
        "input": request["input"],
        "response": source,
        "messages": [
            {"role": "user", "content": request["input"]},
            {"role": "assistant", "content": source},
        ],
    }
    path = tmp_path / "transcript.json"
    sc1.atomic_json(path, transcript)
    entry = {
        "attempt": 0,
        "previous": None,
        "request_hash": sc1.digest(request),
        "transcript_path": str(path),
        "transcript_hash": sc1.file_hash(path),
        "source_hash": episodes.source_spec_hash(source),
        "decision": "accepted",
    }
    ep = {
        "attempt": 0,
        "pool": "setup",
        "index": 0,
        "assignments": slot["assignments"],
        "validation": {"source_hash": entry["source_hash"]},
        "provenance": {
            "session_id": "isolated-author",
            "attempt_history": [entry],
            "prompt_hash": sc1.digest(version_map[family]["neutral_template"]),
            "input_hashes": [request["input_hash"]],
            "transcript_hash": entry["transcript_hash"],
        },
    }
    stage = {"authors": version_map}
    cli.verify_author_chain(ep, stage)
    for issue in ("stale_prompt", "missing_attempts", "hidden_input"):
        bad = copy.deepcopy(ep)
        if issue == "stale_prompt":
            bad["provenance"]["prompt_hash"] = "stale"
        elif issue == "missing_attempts":
            bad["attempt"] = 2
        else:
            transcript["messages"].insert(
                0, {"role": "system", "content": "unallowed prior context"}
            )
            sc1.atomic_json(path, transcript)
            bad["provenance"]["attempt_history"][0]["transcript_hash"] = sc1.file_hash(
                path
            )
        with pytest.raises(ValueError, match="prompt|attempt|input|transcript"):
            cli.verify_author_chain(bad, stage)


def test_astra_f10_provenance_changes_preserve_content_signature(source):
    changed = copy.deepcopy(source)
    changed["provenance"]["audit_note"] = "retained external metadata"
    assert episodes.source_spec_hash(source) == episodes.source_spec_hash(changed)
    assert sc1.digest(source) != sc1.digest(changed)


def test_astra_f6_necessary_update_on_wrong_side_of_recent_boundary(
    source, real_tokenizer
):
    text = source["turns"][0]["text"]
    source["turns"][0]["text"] = "An incidental courtyard observation."
    source["turns"][10] = {"role": "user", "text": text}
    source["instruction_trajectory"][0]["turn"] = 10
    source["filler_turns"].remove(10)
    source["filler_turns"].append(0)
    with pytest.raises(ValueError, match="age"):
        validate_source(source, real_tokenizer)


def test_astra_f13_author_sessions_are_unique(real_tokenizer):
    pair = reviewed_pair(real_tokenizer)
    pair[1]["provenance"]["session_id"] = pair[0]["provenance"]["session_id"]
    with pytest.raises(ValueError, match="session"):
        episodes.independence_audit(pair)


def test_astra_f15_near_cap_setup_defers_for_next_initialization(
    scheduling, monkeypatch
):
    s = scheduling
    s.args.mode = "setup"
    del s.bank[32:]
    for ep in s.bank:
        ep["pool"] = "setup"
    seed_completions(s, 64, spent=28301, prefill=0)
    now = [1.0]
    original = sc1.AllocationLedger.__init__

    def allocation_init(self, *args, **kwargs):
        original(self, *args, **kwargs, clock=lambda: now[0])

    monkeypatch.setattr(sc1.AllocationLedger, "__init__", allocation_init)
    monkeypatch.setattr(s.cli.time, "monotonic", lambda: now[0])

    def scorer_factory(*args):
        now[0] += 300
        return lambda texts, **kwargs: [0.0] * len(texts)

    result = s.cli.run_study(
        s.args,
        s.manifest,
        s.bank,
        s.tok,
        backend_factory=s.backend,
        scorer_factory=scorer_factory,
    )
    cert = episodes.parse_json((s.args.out / "setup-certificate.json").read_text())
    assert result["status"] == "NOT RUN"
    assert cert["full_passes"] == 32 and cert["evicted_passes"] == 0
    assert cert["cost"]["spent"] < sc1.COST_CAP < cert["projection_seconds"]
    assert cert["cost"]["remaining_initialization"] == 300
    assert not s.calls and not s.inits


@pytest.mark.parametrize(
    "mutation", ["duplicate", "non_smoke", "input_hash", "token_divergence"]
)
def test_astra_f11_determinism_rejects_cell_artifact_mutations(
    tmp_path, monkeypatch, mutation
):
    cli, frozen, cert, path = determinism_fixture(tmp_path, monkeypatch)
    if mutation == "duplicate":
        cert["outputs"][1] = copy.deepcopy(cert["outputs"][0])
    elif mutation == "non_smoke":
        cert["outputs"][0]["episode_hash"] = "not-frozen"
    elif mutation == "input_hash":
        cert["outputs"][0]["input_hash"] = "not-frozen-input"
    else:
        row = cert["outputs"][0]
        row["token_ids"][0] += 1
        arm = episodes.parse_json(Path(row["arm_path"]).read_text())
        arm["token_ids"] = row["token_ids"]
        sc1.atomic_json(row["arm_path"], arm)
        row["arm_hash"] = sc1.file_hash(row["arm_path"])
        sc1.atomic_json(
            row["output_path"],
            {k: v for k, v in row.items() if k not in {"output_path", "output_hash"}},
        )
        row["output_hash"] = sc1.file_hash(row["output_path"])
    sc1.atomic_json(path, cert)
    with pytest.raises(ValueError, match="determinism|output"):
        cli.verify_determinism(path, {"executable_freeze": "frozen"})


def test_astra_f16_prepared_output_survives_loss_before_journal_append(
    tmp_path, monkeypatch
):
    store = sc1.RunStore(tmp_path, "m")
    store.start("ep", "clf", "a")
    original = store.append

    def lose_append(event):
        if event["event"] == "completion_prepared":
            raise OSError("resource loss after atomic preparation")
        return original(event)

    monkeypatch.setattr(store, "append", lose_append)
    row = {
        "manifest_id": "m",
        "episode_id": "ep",
        "arm": "clf",
        "attempt_id": "a",
        "success": False,
    }
    with pytest.raises(OSError):
        store.complete(row)
    recovered = sc1.RunStore(tmp_path, "m")
    assert recovered.pending("ep", ["clf"]) == []
    assert (
        recovered.arm_path("ep", "clf").read_bytes()
        == (sc1.canonical(row) + "\n").encode()
    )


def test_fable_m2_typed_resource_loss_without_message():
    from scripts.sc1 import infrastructure_exception

    assert infrastructure_exception(torch.cuda.OutOfMemoryError())


def test_astra_f16_recovery_proof_survives_its_own_interruption(tmp_path, monkeypatch):
    store = sc1.RunStore(tmp_path, "m")
    store.start("ep", "clf", "a")
    with store.journal.open("ab") as f:
        f.write(b'{"event":"completed"')
    append = sc1.RunStore.append

    def lost_recovery(self, event):
        if event["event"] == "journal_tail_recovered":
            raise OSError("loss while appending recovery record")
        return append(self, event)

    with monkeypatch.context() as patch:
        patch.setattr(sc1.RunStore, "append", lost_recovery)
        with pytest.raises(OSError):
            sc1.RunStore(tmp_path, "m")
    recovered = sc1.RunStore(tmp_path, "m")
    recovered.interrupt("ep", "clf", "a", "resource_loss", 2, "CPU fault injection")
    assert sc1.RunStore(tmp_path, "m").pending("ep", ["clf"]) == ["clf"]
