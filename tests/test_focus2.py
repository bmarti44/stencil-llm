"""CPU-only adversarial fixtures. No historical bank or model is a test input."""

import copy
import hashlib
import importlib.util
import json
import math
import os
import random
import subprocess
from collections import Counter
from pathlib import Path

import pytest
from tokenizers import Tokenizer

from stencil import focus2 as f

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def tok():
    return Tokenizer.from_file(str(ROOT / "models/qwen3-4b-hf/tokenizer.json"))


@pytest.fixture(autouse=True)
def forbid_real_backend(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("real backend construction attempted")

    monkeypatch.setattr(f, "load_backend", forbidden)


@pytest.fixture(scope="session")
def banks():
    return f.generate_banks()


def fabricated_development(extra=None):
    sources = {}
    for label in (*range(31, 40), "repair"):
        fps = [extra or f.sha("fabricated input " + str(label))]
        sources[str(label)] = dict(
            path="fabricated-source.py",
            sha256=f.sha("fabricated source"),
            input_count=len(fps),
            fingerprints=fps,
            fingerprints_sha256=f.digest(fps),
        )
    return dict(
        coverage=list(range(31, 40)) + ["repair"],
        sources=sources,
        fingerprints=sorted({fp for s in sources.values() for fp in s["fingerprints"]}),
    )


def test_literal_template():
    literal = (
        "Cancel the superseded task rule: {superseded_rule}.\n"
        "Your earlier answers under that rule followed a rule that no longer "
        "applies; do not imitate your earlier answers; the rules that apply now are:\n"
        "{live_rules_or_default}\n"
        "Use earlier facts when requested, while following the current rules "
        "for this answer."
    )
    assert f.RECAP == literal
    assert hashlib.sha256(literal.encode()).hexdigest() == (
        "2658b026d6bd22d4ed460b34c543abc159e4e80ff56f367be4eaf5c035f8e8d7"
    )


def test_independent_stream_and_generator(banks):
    namespace = "focus2-v1:9053714:final:sort:ascending:0:0:SET:payload"
    rng = random.Random(
        int.from_bytes(hashlib.sha256(namespace.encode()).digest(), "big")
    )
    while True:
        values = rng.sample(range(-20, 21), rng.randint(5, 8))
        if values != sorted(values) and values != sorted(values, reverse=True):
            break
    first = banks["final"][0]
    assert first["requests"]["SET"] == values
    assert first["requests"]["SET"] != first["requests"]["SWITCH"]
    assert len(banks["final"]) == 256
    assert len(banks["pilot"]) == 4
    assert len(banks["competence"]) == 192
    for name, count in (("final", 64), ("pilot", 1)):
        cells = Counter((e["family"], e["direction"], e["delay"]) for e in banks[name])
        assert len(cells) == 4 and set(cells.values()) == {count}
    assert Counter(e["family"] for e in banks["final"] if e["memo"]) == {
        k: 64 for k in f.SELECTED_FAMILIES
    }
    cells = Counter((e["family"], e["direction"]) for e in banks["competence"])
    assert len(cells) == 3 and set(cells.values()) == {64}
    f.validate_banks(banks, fabricated_development())
    assert f.generate_banks() == banks


def test_fingerprints_ignore_tags_ids_and_sort_permutations(banks):
    ep = copy.deepcopy(banks["final"][0])
    original = f.fingerprint(ep["family"], ep["requests"]["SET"])
    ep["id"], ep["tag"] = "attack", -500
    ep["requests"]["SET"].reverse()
    assert f.fingerprint(ep["family"], ep["requests"]["SET"]) == original
    assert f.fingerprint("case", ["AbC", "dEf", "GhI"]) == f.fingerprint(
        "case", ["ghi", "DEF", "abc"]
    )
    dev = fabricated_development(original)
    with pytest.raises(f.Invalid, match="collision"):
        f.validate_banks(banks, dev)
    with pytest.raises(f.Invalid, match="development"):
        f.validate_banks(banks, None)
    bad = copy.deepcopy(banks)
    bad["pilot"][0]["requests"]["SET"] = ep["requests"]["SET"]
    with pytest.raises(f.Invalid):
        f.validate_banks(bad, dev)


def test_focus2b_operand_law_seeds_and_memo_denominators(banks):
    assert f.SELECTED_FAMILIES == ("sort",)
    assert f.CONFIG["families"] == ["sort"]
    for name, seed in (("competence", 9053712), ("pilot", 9053713), ("final", 9053714)):
        assert {ep["seed"] for ep in banks[name]} == {seed}
        assert f.CONFIG["seeds"][name] == seed
        assert {ep["family"] for ep in banks[name]} == {"sort"}
        for ep in banks[name]:
            for values in ep["requests"].values():
                assert 5 <= len(values) <= 8 and len(set(values)) == len(values)
                assert all(type(v) is int and -20 <= v <= 20 for v in values)
                assert values != sorted(values)
                assert values != sorted(values, reverse=True)
    memos = Counter(
        (ep["direction"], ep["delay"]) for ep in banks["final"] if ep["memo"]
    )
    assert len(memos) == 4 and set(memos.values()) == {16}


def test_focus2b_actual_requests_state_shape_and_obligations_once(tok, banks):
    schema = (
        'Output compact JSON of the form {"answer": <JSON array of integers>, '
        '"tag": <integer>}; no prose or unrequested keys.'
    )
    assert f.TEMPLATES["schema"] == schema
    assert f.TEMPLATES["default"] == "Return the payload list unchanged."
    for direction in (*f.FAMILIES["sort"], "default"):
        ep = next(e for e in banks["competence"] if e["direction"] == direction)
        h = f.competence_history(tok, ep)
        h.request(ep, "SET", cue=f.live_rules(ep, "SET") + "\n")
        text = tok.decode(h.render(current=True)["ids"], skip_special_tokens=False)
        assert schema in text and f.rule(ep, "SET") in text
        assert text.count("Additional requested keys:") == 1
    ep = banks["final"][0]
    for arm in f.ARMS:
        h = f.initial_history(tok, ep)
        for step in f.REQUESTS:
            if step in ("SWITCH", "BACK", "CLEAR"):
                f.intervene(h, ep, arm, step)
            cue = f.current_cue(ep, arm, step) if step in f.CHECKPOINTS else None
            h.request(ep, step, cue=cue)
            user = h.messages[-2]
            text = tok.decode(
                [t for part in user["parts"] for t in part["ids"]],
                skip_special_tokens=False,
            )
            assert text.count("Additional requested keys:") == 1
            assert f.obligations(ep, step) in text
            if cue:
                assert schema in text
            if step == "SET":
                full = tok.decode(
                    h.render(current=True)["ids"], skip_special_tokens=False
                )
                assert full.count("Additional requested keys:") == 1
            h.answer(f.encode(tok, f.gold(ep, step)), f.EOS)


def test_all_gold_caps_defaults_and_real_delay(tok, banks):
    delay = f.delay_text(tok)
    assert len(f.encode(tok, delay)) == 512
    for bank in banks.values():
        for ep in bank:
            for step, payload in ep["requests"].items():
                assert f.target(ep["family"], payload, "default") != f.target(
                    ep["family"], payload, f.FAMILIES[ep["family"]][0]
                )
                assert f.target(ep["family"], payload, "default") != f.target(
                    ep["family"], payload, f.FAMILIES[ep["family"]][1]
                )
                text = f.gold(ep, step, memo="abcdef")
                assert len(f.encode(tok, text)) < 64
                assert f.score(
                    ep, step, text, f.encode(tok, text), f.EOS, source_memo="abcdef"
                )["success"]
    history = f.History(tok)
    history.pair("neutral", "delay", delay, f.encode(tok, "Recorded."), f.EOS)
    layout = history.render()
    assert len(layout["ids"]) > 512
    assert tok.decode(layout["ids"], skip_special_tokens=False).endswith("<|im_end|>\n")
    assert layout["positions"] == list(range(len(layout["ids"])))


@pytest.mark.parametrize(
    "text",
    [
        "",
        ".",
        "  .\n",
        "{} extra",
        "NaN",
        '{"answer":NaN,"tag":3}',
        '{"answer":[],"tag":3,"tag":3}',
        '{"answer":[],"tag":true}',
    ],
)
def test_malformed_breaks(tok, banks, text):
    ep = banks["final"][0]
    assert f.score(ep, "SWITCH", text, f.encode(tok, text), f.EOS)["broken"]


def test_checker_mutations_and_collateral_separation(tok, banks):
    ep = banks["final"][0]
    value = json.loads(f.gold(ep, "SWITCH"))
    for key, replacement in (("answer", [7, 9]), ("tag", ep["tag"] + 1)):
        changed = {**value, key: replacement}
        text = json.dumps(changed)
        score = f.score(ep, "SWITCH", text, f.encode(tok, text), f.EOS)
        assert not score["success"] and not score["broken"]
    text = json.dumps({**value, "unasked": 1})
    assert f.score(ep, "SWITCH", text, f.encode(tok, text), f.EOS)["broken"]
    text = f.gold(ep, "NEUTRAL2", memo="abcdef")
    parsed = json.loads(text)
    for key in ("user_fact", "tool_fact", "assistant_fact"):
        missing = {k: v for k, v in parsed.items() if k != key}
        text = json.dumps(missing)
        s = f.score(
            ep, "NEUTRAL2", text, f.encode(tok, text), f.EOS, source_memo="abcdef"
        )
        assert s["success"] and not s["collateral"][key]
    for step in ("CLEAR", "NEUTRAL2"):
        for direction in f.FAMILIES["sort"]:
            changed = {
                "answer": f.target("sort", ep["requests"][step], direction),
                "tag": ep["tag"],
            }
            text = json.dumps(changed)
            s = f.score(ep, step, text, f.encode(tok, text), f.EOS)
            assert not s["success"] and s["imposition"][direction]


@pytest.mark.parametrize("period", [1, 2, 3, 4])
def test_repetition_and_cap(tok, banks, period):
    ep = banks["final"][0]
    text = f.gold(ep, "SWITCH")
    loop = list(range(20, 20 + period)) * 8
    assert f.score(ep, "SWITCH", text, loop, f.EOS)["repetitive"]
    ids = list(range(100, 163))
    assert not f.score(ep, "SWITCH", text, ids, f.EOS)["truncated"]
    assert f.score(ep, "SWITCH", text, ids + [200], None)["truncated"]


def test_renderer_scope_and_nonvacuity(tok, banks):
    ep = banks["final"][0]
    history = f.initial_history(tok, ep)
    history.request(ep, "SET", cue=None)
    with pytest.raises(f.Invalid, match="unanswered"):
        history.request(ep, "PREHOLD", cue=None)
    history.answer(f.encode(tok, '{"answer":[9],"tag":0,"memo":"secret"}'), f.EOS)
    history.request(ep, "PREHOLD", cue=None)
    history.answer(f.encode(tok, "wrong"), f.EOS)
    before = history.render()
    for arm in f.ARMS:
        branch = history.fork()
        edit = f.intervene(branch, ep, arm, "SWITCH")
        branch.request(ep, "SWITCH", cue=f.current_cue(ep, arm, "SWITCH"))
        after = branch.render(current=True)
        decoded = tok.decode(after["ids"], skip_special_tokens=False)
        assert (
            "wrong" in decoded if arm not in f.EVICTION_ARMS else "wrong" not in decoded
        )
        assert (
            "secret" in decoded
            if arm not in f.EVICTION_ARMS
            else "secret" not in decoded
        )
        if arm in f.EVICTION_ARMS:
            assert len(edit["removed_bodies"]) == 2
            assert all(x["replacement_tokens"] == [13] for x in edit["removed_bodies"])
            assert all(x["ids"] for x in edit["removed_bodies"])
        rule = f.rule(ep, "SWITCH")
        last_user = decoded.rsplit("<|im_start|>user\n", 1)[1]
        assert (rule in last_user) == (
            arm in ("both", "placement-only", "text-restate")
        )
        assert str(ep["user_fact"]) in decoded
        assert "<|im_start|>user\n<tool_response>\n" in decoded
        assert after["positions"] == list(range(len(after["ids"])))
        branch.answer(f.encode(tok, "fresh branch body"), f.EOS)
        f.intervene(branch, ep, arm, "BACK")
        branch.request(ep, "BACK", cue=f.current_cue(ep, arm, "BACK"))
        branch.answer(f.encode(tok, "second branch body"), f.EOS)
        f.intervene(branch, ep, arm, "CLEAR")
        assert history.render() == before
    with pytest.raises(f.Invalid, match="vacuous"):
        f.intervene(f.initial_history(tok, ep), ep, "both", "SWITCH")


def test_stats_independent_edges():
    assert f.paired([True] * 8, [True] * 8)["p"] == 1
    assert f.paired([True] * 8, [False] * 8)["p"] == 1 / 256
    assert f.holm([0.01, 0.025, 0.04]) == pytest.approx([0.03, 0.05, 0.05])
    assert f.holm([0.04, 0.01, 0.025]) == pytest.approx([0.05, 0.03, 0.05])
    with pytest.raises(f.Invalid):
        f.holm([0.01, 0.02])
    for b, c, n in ((0, 0, 256), (13, 0, 256), (2, 7, 32), (0, 32, 32), (32, 0, 32)):
        lo, hi = f.paired_interval(b, c, n)
        rlo, rhi = f.paired_interval(c, b, n)
        assert lo == pytest.approx(-rhi) and hi == pytest.approx(-rlo)
        assert lo <= (b - c) / n <= hi
    z2 = 1.959963984540054**2
    assert f.paired_interval(0, 0, 256)[1] == pytest.approx(z2 / (256 + z2), abs=1e-7)
    for k, expected in ((0, 0.011633876), (2, 0.024387414567)):
        u = f.exact_upper(k, 256)
        assert u == pytest.approx(expected, abs=1e-7)
        assert sum(
            math.comb(256, j) * u**j * (1 - u) ** (256 - j) for j in range(k + 1)
        ) == pytest.approx(0.05)


def hand_episodes():
    rows = []
    for i in range(256):
        arms = {
            a: {
                "Y": True,
                "broken": False,
                "constraint": False,
                "user_fact": False,
                "tool_fact": False,
                "assistant_fact": False,
            }
            for a in f.ARMS
        }
        rows.append(
            {
                "id": str(i),
                "family": "sort",
                "direction": "ascending",
                "delay": 0,
                "memo": i < 64,
                "source_valid": i < 60,
                "both_correct": i < 128,
                "arms": arms,
            }
        )
    return rows


def test_primary_secondary_and_safety_hand_tables():
    rows = hand_episodes()
    for i in range(13):
        for a in ("placement-only", "eviction-only", "text-restate"):
            rows[i]["arms"][a]["Y"] = False
    report = f.decisions(rows)
    assert report["status"] == "PASS"
    assert report["primary"]["text-restate"]["b"] == 13
    rows[12]["arms"]["text-restate"]["Y"] = True
    assert f.decisions(rows)["status"] == "FAIL"
    rows[12]["arms"]["text-restate"]["Y"] = False
    rows[12]["arms"]["placement-only"]["Y"] = True
    assert f.decisions(rows)["status"] == "PASS with MARGINAL ADDED CONTROL"
    for i in range(5):
        rows[i]["arms"]["both"]["broken"] = True
    rows[20]["arms"]["text-restate"]["broken"] = True
    assert f.decisions(rows)["safety"]["passes"]
    rows[5]["arms"]["both"]["broken"] = True
    assert not f.decisions(rows)["safety"]["passes"]
    rows = hand_episodes()
    rows[0]["arms"]["both"]["assistant_fact"] = True
    report = f.decisions(rows)
    assert report["safety"]["passes"]
    assert report["collateral"]["assistant_fact"]["n"] == 64
    assert report["source_missing"] == 4
    assert set(report["secondary"]) == {
        "placement-only >= text-restate",
        "eviction-only vs neither",
    }
    assert all("adjusted_p" not in c for c in report["secondary"].values())
    assert "not demonstrated noninferiority/equivalence" in report["secondary_limit"]


class FakeBackend:
    """Greedy token stream with isolated sentinel caches; never touches torch."""

    def __init__(self, tok, policy=None, clock=None):
        self.tok, self.policy, self.clock = tok, policy, clock
        self.calls, self.caches = [], []
        self.peak_memory = 0

    def empty(self):
        cache = {"ids": [], "serial": len(self.caches)}
        self.caches.append(cache)
        return cache

    def prefill(self, ids, cache, layout, context):
        assert cache["ids"] == []
        assert layout["positions"] == list(range(len(ids)))
        assert len(layout["tokens"]) == len(ids)
        cache["ids"] += ids
        self.calls.append(copy.deepcopy(context))
        ep, step = context["episode"], context["checkpoint"]
        text = "Noted." if step.startswith("DELAY") else f.gold(ep, step, memo="abcdef")
        if self.policy:
            text = self.policy(context, ids, text)
        cache["queue"] = f.encode(self.tok, text) + [f.EOS]
        if self.clock:
            self.clock.advance("prefill")
        return cache["queue"].pop(0)

    def decode(self, token, cache):
        cache["ids"].append(token)
        if self.clock:
            self.clock.advance("decode")
        return cache["queue"].pop(0)


class Clock:
    def __init__(self):
        self.now, self.jump, self.at = 0.0, 0.0, None

    def __call__(self):
        self.now += 0.00001
        return self.now

    def advance(self, kind):
        if self.at == kind:
            self.now += self.jump


def test_fake_episode_unscreened_memo_and_maps(tok, banks, tmp_path):
    ep = banks["final"][0]

    def policy(ctx, ids, text):
        if ctx["checkpoint"] == "PREHOLD":
            return '{"answer":[999],"tag":' + str(ep["tag"]) + "}"
        if ctx["checkpoint"] == "NEUTRAL2" and ctx["arm"] in f.EVICTION_ARMS:
            value = json.loads(text)
            value.pop("assistant_fact")
            return json.dumps(value)
        return text

    backend = FakeBackend(tok, policy)
    store = f.RecordStore(tmp_path / "records")
    engine = f.Engine(tok, backend, store, f.Budget(Clock()), {"test": "binding"})
    f.episode(engine, ep)
    records = store.rows()
    scored = [r for r in records if r["arm"] in f.ARMS]
    assert len(scored) == 25
    assert all(not r["both_correct"] for r in scored)
    assert len({r["shared_prior_hash"] for r in scored}) == 1
    assert all(f.REQUIRED_RECORD <= r.keys() for r in records)
    assert len({id(c) for c in backend.caches}) == len(backend.caches)
    episodes = f.validate_records(
        records, [ep], tok, {"test": "binding"}, complete=True
    )
    assert episodes[0]["arms"]["both"]["Y"]
    assert episodes[0]["arms"]["both"]["assistant_fact"]
    assert not episodes[0]["arms"]["text-restate"]["assistant_fact"]
    bad = copy.deepcopy(records)
    bad[-1]["output_text"] = "."
    with pytest.raises(f.Invalid):
        f.validate_records(bad, [ep], tok, {"test": "binding"}, complete=True)
    with pytest.raises(f.Invalid):
        store.write(records[0])


def cli():
    spec = importlib.util.spec_from_file_location(
        "focus2_cli", ROOT / "scripts/focus2.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_import_help_and_draft_refuse_before_backend(tmp_path, capsys):
    module = cli()
    with pytest.raises(SystemExit) as exc:
        module.main(["--help"])
    assert exc.value.code == 0
    assert set(tmp_path.iterdir()) == set()
    assert (
        module.main(
            [
                "--mode",
                "run",
                "--freeze",
                str(tmp_path),
                "--output",
                str(tmp_path / "out"),
            ]
        )
        != 0
    )
    assert not (tmp_path / "out").exists()
    assert "INVALID" in capsys.readouterr().out


def test_check39_gate_is_distinct():
    receipt = repair_receipt()
    assert f.repair_gate(receipt)
    # Net +2 with raw b=6 passes check39, but cannot pass the main F6 cap.
    for mode in ("surviving", "rebuilt"):
        receipt["arms"][f"placeholder/{mode}"]["broken_episodes"] = list(range(6))
        receipt["arms"][f"intact/{mode}"]["broken_episodes"] = list(range(6, 10))
    assert f.repair_gate(receipt)
    receipt["arms"]["placeholder/rebuilt"]["steps"]["RELEASE1"]["success"] = 0
    assert f.repair_gate(receipt)  # diagnostic rebuilt release never gates
    receipt["arms"]["placeholder/surviving"]["steps"]["RELEASE1"]["success"] = 55
    assert not f.repair_gate(receipt)
    receipt = repair_receipt()
    receipt["preselected_larger_test_variant"] = "whole_pair"
    with pytest.raises(f.StopRepair):
        f.repair_gate(receipt)
    receipt = repair_receipt()
    receipt["verdict"] = "STOP"
    with pytest.raises(f.StopRepair):
        f.repair_gate(receipt)


def repair_receipt():
    return {
        "status": "complete",
        "complete": True,
        "n": 64,
        "verdict": "PROCEED_PLACEHOLDER",
        "preselected_larger_test_variant": "placeholder",
        "placeholder_token_ids": [13],
        "placeholder_cpu_verified": True,
        "started_utc": "2026-09-05T08:43:10Z",
        "source_hashes": {},
        "arms": {
            f"{a}/{m}": {
                "broken_episodes": [],
                "steps": {
                    s: {"n": 64, "valid": 64, "success": 60, "broken": 0}
                    for s in ("RELEASE1", "RELEASE2", "NEUTRAL1", "NEUTRAL2")
                },
            }
            for a in ("intact", "placeholder")
            for m in ("surviving", "rebuilt")
        },
    }


def git(root, *args):
    return subprocess.check_output(
        ["git", "-C", str(root), *args],
        text=True,
        env={**os.environ, "GIT_COMMITTER_DATE": "2026-09-05T08:40:00Z"},
    ).strip()


def commit(root):
    git(root, "add", ".")
    git(
        root,
        "-c",
        "core.hooksPath=/dev/null",
        "commit",
        "--date=2026-09-05T08:40:00Z",
        "-qm",
        "fabricated CPU fixture",
    )
    return git(root, "rev-parse", "HEAD")


@pytest.fixture
def frozen(tmp_path, tok, monkeypatch):
    root = tmp_path / "repo"
    root.mkdir()
    git(root, "init", "-q")
    git(root, "config", "user.email", "fixture@example.invalid")
    git(root, "config", "user.name", "CPU fixture")
    # All dependency contents are fabricated, including historical receipts.
    # Patch only immutable trust roots to the corresponding committed fixtures;
    # the real CLI preflight/consumer is otherwise used without a bypass.
    (root / "LEDGER-PLAN.md").write_text(
        "DRAFT v1\n" + f.RECAP + "\nPrewritten readings: original.\n"
    )
    v1 = commit(root)
    section = (
        "DRAFT v2; NOT YET REGISTERED\n"
        + f.RECAP
        + "\n"
        + f.READINGS
        + "\n"
        + f.EXPECTATION
        + "\nClaim ceiling: "
        + f.CLAIM_CEILING
    )
    (root / "LEDGER-PLAN.md").write_text(section)
    v2 = commit(root)
    evidence = root / "evidence"
    evidence.mkdir()
    (evidence / "review36.md").write_text("ACCURATE-WITH-CORRECTIONS; reviewed source")
    (evidence / "review38.md").write_text(
        "ACCURATE; corrections: inside-request; cross-check confounds"
    )
    (evidence / "check37.md").write_text("STOP under its own rule; not pooled")
    code_paths = [
        "check39.py",
        "repair.py",
        "check36.py",
        "check35.py",
        "check34.py",
        "check32.py",
    ]
    for p in code_paths:
        (evidence / p).write_text("# fabricated guarded source\n")
    (evidence / "reading.md").write_text(
        "PROCEED with placeholder iff preselected gates pass"
    )
    prereg = commit(root)
    receipt = repair_receipt()
    receipt["source_commit"] = prereg
    receipt["source_hashes"] = {
        "evidence/" + p: f.sha((evidence / p).read_bytes())
        for p in ("check39.py", "repair.py", "check35.py", "check34.py", "check32.py")
    }
    receipt["source_hashes"]["evidence/reading.md"] = f.sha(
        (evidence / "reading.md").read_bytes()
    )
    (evidence / "summary.json").write_text(f.canonical(receipt))
    (evidence / "readme.md").write_text(
        (evidence / "reading.md").read_text() + "\nPROCEED_PLACEHOLDER"
    )
    receipt_commit = commit(root)
    pins = dict(
        v1_commit=v1,
        v2_commit=v2,
        v3_commit=v2,
        focus2b_commit=v2,
        focus2b_section_sha256=f.sha(section),
        ledger="LEDGER-PLAN.md",
        v2_section_sha256=f.sha(section),
        v3_section_sha256=f.sha(section),
        check36_source=prereg,
        check36_paths=["evidence/" + p for p in code_paths[2:]],
        check36_review="evidence/review36.md",
        check36_review_sha256=f.sha((evidence / "review36.md").read_bytes()),
        check38_review="evidence/review38.md",
        check38_review_sha256=f.sha((evidence / "review38.md").read_bytes()),
        check37_readme="evidence/check37.md",
        prereg_commit=prereg,
        receipt_commit=receipt_commit,
        summary="evidence/summary.json",
        summary_sha256=f.sha((evidence / "summary.json").read_bytes()),
        repair_reading="evidence/reading.md",
        prereg_reading="evidence/reading.md",
        repair_readme="evidence/readme.md",
        check39_code="evidence/check39.py",
        repair_code="evidence/repair.py",
        launch="2026-09-05T08:43:10Z",
    )
    monkeypatch.setattr(f, "PINS", pins)
    monkeypatch.setattr(f, "ROOT", root)
    # CPU tokenizer injection still uses real Qwen token IDs. Fixture token file
    # is a small marker hashed/committed through the same dependency checks.
    folder = root / "freeze"
    f.prepare_freeze(folder, tok=tok, section_text=section)
    for name in (
        "model",
        "model_config",
        "qwen_default_config",
        "tokenizer",
        "tokenizer_config",
        "qwen",
        "stats",
        "generator",
        "cli",
        "checker_tests",
    ):
        (folder / f"{name}.fixture").write_text("fabricated " + name)
    (folder / "development.json").write_text(f.canonical(fabricated_development()))
    (folder / "review.json").write_text(
        f.canonical(
            {
                "status": "APPROVED",
                "open_high_critical": 0,
                "section_sha256": f.sha(section),
            }
        )
    )
    manifest = json.loads((folder / "manifest.json").read_text())
    manifest["status"] = "REGISTERED"
    manifest["candidate_only"] = False
    manifest["output_path"] = "outputs"
    paths = {
        k: "freeze/" + k + ".json"
        for k in ("banks", "templates", "config", "development", "review")
    }
    paths.update(
        section="freeze/section.md",
        inherited_section="freeze/inherited_section.md",
        readings="freeze/readings.txt",
    )
    paths.update(
        {
            k: "freeze/" + k + ".fixture"
            for k in (
                "model",
                "model_config",
                "qwen_default_config",
                "tokenizer",
                "tokenizer_config",
                "qwen",
                "stats",
                "generator",
                "cli",
                "checker_tests",
            )
        }
    )
    paths.update(
        check36_review=pins["check36_review"],
        check38_review=pins["check38_review"],
        check39_summary=pins["summary"],
        check39_reading=pins["repair_reading"],
        check39_readme=pins["repair_readme"],
        check39_code=pins["check39_code"],
        repair_code=pins["repair_code"],
        check37_readme=pins["check37_readme"],
    )
    for i, p in enumerate(pins["check36_paths"]):
        paths[f"check36_source_{i}"] = p
    manifest["files"] = {
        k: {"path": p, "sha256": f.sha((root / p).read_bytes())}
        for k, p in paths.items()
    }
    review = json.loads((folder / "review.json").read_text())
    review["dependencies"] = {
        k: v["sha256"] for k, v in manifest["files"].items() if k != "review"
    }
    (folder / "review.json").write_text(f.canonical(review))
    manifest["files"]["review"]["sha256"] = f.sha((folder / "review.json").read_bytes())
    monkeypatch.setattr(
        f, "RUNTIME_SOURCES", {k: root / paths[k] for k in f.RUNTIME_SOURCES}
    )
    manifest["anchors"] = {
        k: pins[k]
        for k in (
            "v1_commit",
            "v2_commit",
            "v3_commit",
            "focus2b_commit",
            "check36_source",
            "prereg_commit",
            "receipt_commit",
        )
    }
    (folder / "manifest.json").write_text(f.canonical(manifest))
    freeze_commit = commit(root)
    launch = root / "launch.json"
    launch.write_text(
        f.canonical(
            {
                "freeze_commit": freeze_commit,
                "manifest_sha256": f.sha((folder / "manifest.json").read_bytes()),
                "manifest_path": "freeze/manifest.json",
                "output_path": "outputs",
            }
        )
    )
    commit(root)
    return root, folder, launch


def args_for(frozen, mode):
    root, folder, launch = frozen
    return [
        "--mode",
        mode,
        "--freeze",
        str(folder),
        "--launch-receipt",
        str(launch),
        "--output",
        str(root / "outputs"),
    ]


def test_positive_preflight_with_historical_stop_and_ledger_append(frozen, tok):
    root, folder, launch = frozen
    result = f.preflight(folder, launch, "competence", root / "outputs", tok=tok)
    assert result["historical_check37"] == "STOP (not pooled; not a v2 veto)"
    with (root / "LEDGER-PLAN.md").open("a") as handle:
        handle.write("\nUnrelated later appendix\n")
    assert (
        f.preflight(folder, launch, "competence", root / "outputs", tok=tok)["binding"]
        == result["binding"]
    )


@pytest.mark.parametrize(
    "attack",
    [
        "draft",
        "dirty",
        "missing",
        "untracked",
        "wrong_commit",
        "bad_anchor",
        "review36",
        "receipt",
        "template",
        "bank",
        "no_manifest",
        "no_launch",
    ],
)
def test_refusal_through_main_before_backend(frozen, tok, attack, capsys):
    root, folder, launch = frozen
    manifest = json.loads((folder / "manifest.json").read_text())
    if attack == "draft":
        manifest["status"] = "DRAFT"
        (folder / "manifest.json").write_text(f.canonical(manifest))
    elif attack == "dirty":
        (folder / "readings.txt").write_text("tampered")
    elif attack == "missing":
        (folder / "section.md").unlink()
    elif attack == "untracked":
        git(root, "rm", "--cached", "freeze/readings.txt")
    elif attack == "wrong_commit":
        data = json.loads(launch.read_text())
        data["freeze_commit"] = f.PINS["v1_commit"]
        launch.write_text(f.canonical(data))
        commit(root)
    elif attack == "bad_anchor":
        f.PINS["v1_commit"] = "0" * 40
    elif attack == "review36":
        f.PINS["check36_review_sha256"] = "0" * 64
    elif attack == "receipt":
        (root / f.PINS["summary"]).write_text(f.canonical({"verdict": "STOP"}))
    elif attack == "template":
        (folder / "templates.json").write_text("{}")
    elif attack == "bank":
        (folder / "banks.json").write_text("{}")
    elif attack == "no_manifest":
        (folder / "manifest.json").unlink()
    else:
        launch.unlink()
    calls = []
    code = cli().main(
        args_for(frozen, "competence"),
        tokenizer_factory=lambda _: tok,
        backend_factory=lambda *a: calls.append(a),
    )
    assert code != 0 and not calls
    assert not (root / "outputs").exists()
    assert "INVALID" in capsys.readouterr().out


def test_competence_boundaries():
    rows = [
        {
            "family": family,
            "direction": direction,
            "success": i < (56 if direction == "default" else 52),
        }
        for family in f.SELECTED_FAMILIES
        for directions in (f.FAMILIES[family],)
        for direction in (*directions, "default")
        for i in range(64)
    ]
    assert f.competence_gate(rows)["status"] == "PASS"
    rows[0]["success"] = False
    assert f.competence_gate(rows)["status"] == "INELIGIBLE"
    with pytest.raises(f.Invalid):
        f.competence_gate(rows[:-1])


def test_full_fake_pipeline_and_analyzer(frozen, tok, capsys):
    root, folder, launch = frozen
    clock = Clock()

    def factory(*_):
        return FakeBackend(tok, clock=clock)

    module = cli()
    for mode in ("competence", "pilot", "run", "analyze"):
        code = module.main(
            args_for(frozen, mode),
            tokenizer_factory=lambda _: tok,
            backend_factory=factory,
            clock=clock,
        )
        assert code == 0, capsys.readouterr().out
    report = f.analyze(folder, launch, root / "outputs", tok=tok)
    assert report["n"] == 256 and report["status"] == "FAIL"
    assert report["prewritten_readings"] == f.READINGS
    assert report["checkpoint_counts"]["both"]["SWITCH"]["n"] == 256
    ends = [
        json.loads((root / "outputs" / mode / "end.json").read_text())
        for mode in ("competence", "pilot", "run")
    ]
    assert ends[0]["spent_after"] < ends[1]["spent_after"] < ends[2]["spent_after"]
    assert module.main(args_for(frozen, "run"), tokenizer_factory=lambda _: tok) != 0
    # A forged aggregate certificate is not sufficient; raw rows govern.
    cert_path = root / "outputs/competence/certificate.json"
    cert = json.loads(cert_path.read_text())
    cert["cells"]["sort/ascending"]["success"] = 55
    cert_path.write_text(f.canonical(cert))
    with pytest.raises(f.Invalid):
        f.preflight(folder, launch, "run", root / "outputs", tok=tok)


@pytest.mark.parametrize("at", ["prefill", "decode"])
def test_budget_crossing_partial_is_durable(frozen, tok, at, capsys):
    root, folder, launch = frozen
    clock = Clock()
    clock.at, clock.jump = at, f.GPU_CAP + 1
    code = cli().main(
        args_for(frozen, "competence"),
        tokenizer_factory=lambda _: tok,
        backend_factory=lambda *_: FakeBackend(tok, clock=clock),
        clock=clock,
    )
    assert code != 0 and "INCOMPLETE" in capsys.readouterr().out
    end = json.loads((root / "outputs/competence/end.json").read_text())
    assert end["status"] == "INCOMPLETE" and end["spent_after"] > f.GPU_CAP
    rows = f.RecordStore(root / "outputs/competence/records").rows()
    assert len(rows) == 1 and not rows[0]["complete"]
    assert rows[0]["cost"][at + "_seconds"] > f.GPU_CAP


def test_fable_A2_sixth_h_stops_scheduling_without_rescue(tok, banks, tmp_path):
    def policy(ctx, ids, text):
        return "." if ctx["arm"] == "both" and ctx["checkpoint"] == "SWITCH" else text

    backend = FakeBackend(tok, policy)
    engine = f.Engine(
        tok, backend, f.RecordStore(tmp_path / "records"), f.Budget(Clock()), {}
    )
    status = f.run_episodes(engine, banks["final"])
    assert status == "FAIL-SAFETY"
    rows = engine.store.rows()
    assert len({r["episode"] for r in rows}) == 6
    assert sum(r["arm"] == "both" and r["checkpoint"] == "NEUTRAL2" for r in rows) == 6
    assert not any("signal" in x for x in vars(backend))


def test_competence_prompt_is_immediate(tok, banks):
    for family in f.SELECTED_FAMILIES:
        ep = next(e for e in banks["competence"] if e["family"] == family)
        h = f.competence_history(tok, ep)
        h.request(ep, "SET", cue=f.live_rules(ep, "SET") + "\n")
        text = tok.decode(h.render(current=True)["ids"], skip_special_tokens=False)
        assert text.count("<|im_start|>user\n") == 1
        user = text.split("<|im_start|>user\n")[1]
        assert f.rule(ep, "SET") in user and f.canonical(ep["requests"]["SET"]) in user


def test_backend_failure_cost_counters_and_delay_flags(tok, banks, tmp_path):
    ep = next(e for e in banks["final"] if e["delay"] == 512)
    backend = FakeBackend(
        tok, lambda ctx, ids, text: "." if ctx["checkpoint"] == "DELAY0" else text
    )
    engine = f.Engine(
        tok, backend, f.RecordStore(tmp_path / "rows"), f.Budget(Clock()), {}
    )
    f.episode(engine, ep)
    rows = engine.store.rows()
    delay = next(r for r in rows if r["checkpoint"] == "DELAY0")
    assert not delay["flags"]["empty"]
    assert delay["delay_user_tokens"] == 512
    assert delay["complete_delay_tokens"] > 512
    f.validate_records(rows, [ep], tok, {}, complete=True)
    bad = copy.deepcopy(rows)
    bad[0]["cost"]["emitted_tokens"] += 1
    with pytest.raises(f.Invalid, match="counter"):
        f.validate_records(bad, [ep], tok, {}, complete=True)


def test_output_directory_and_review_hash_binding(frozen, tok):
    root, folder, launch = frozen
    with pytest.raises(f.Invalid, match="output"):
        f.preflight(folder, launch, "competence", root / "another-run", tok=tok)
    data = json.loads((folder / "review.json").read_text())
    assert data["dependencies"]["banks"] == f.sha((folder / "banks.json").read_bytes())


def test_score_old_field_and_representation_are_task_errors(tok, banks):
    for family in ("fields", "representation"):
        ep = copy.deepcopy(banks["final"][0])
        ep["family"] = family
        ep["direction"] = f.FAMILIES[family][0]
        ep["requests"]["CLEAR"] = f.payload(random.Random(42), family)
        for old in f.FAMILIES[family]:
            value = {
                "answer": f.target(family, ep["requests"]["CLEAR"], old),
                "tag": ep["tag"],
            }
            text = f.canonical(value)
            flags = f.score(ep, "CLEAR", text, f.encode(tok, text), f.EOS)
            assert not flags["success"] and not flags["broken"]


def test_independent_all_skill_targets():
    assert f.target("sort", [4, -3, 2, 0], "descending") == [4, 2, 0, -3]
    assert f.target("case", ["xYz", "ABc", "dEf"], "upper") == ["XYZ", "ABC", "DEF"]
    assert f.target("case", ["xYz", "ABc", "dEf"], "lower") == ["xyz", "abc", "def"]
    records = [{"left": 4, "right": 9}, {"left": -1, "right": 3}]
    assert f.target("fields", records, "right") == [9, 3]
    assert f.target("representation", {"items": [3, -5, 6, 0]}, "string") == "3,-5,6,0"
    assert f.target("representation", {"items": [3, -5, 6, 0]}, "default") == {
        "items": [3, -5, 6, 0]
    }


def test_malformed_tool_and_separate_cue_rejected(tok):
    h = f.History(tok)
    h.message(
        "user", "event", "bad", [("cue", f.encode(tok, "Sort ascending."), "bad")]
    )
    h.message("assistant", "event", "bad", [("body", [13], "bad")])
    with pytest.raises(f.Invalid, match="separate moved-cue"):
        h.render()
    h = f.History(tok)
    h.message("user", "fact", "fact", [("input", [13], "fact")])
    h.message("assistant", "tool_call", "fact", [("body", [13], "fact")])
    h.message("tool", "tool_return", "fact", [("return", [13], "fact")])
    h.message("assistant", "fact", "fact", [("body", [13], "fact")])
    with pytest.raises(f.Invalid, match="tool"):
        h.render()


@pytest.mark.parametrize("mode", ["pilot", "run"])
def test_missing_certificates_refuse_before_construction(frozen, tok, mode):
    calls = []
    assert (
        cli().main(
            args_for(frozen, mode),
            tokenizer_factory=lambda _: tok,
            backend_factory=lambda *a: calls.append(a),
        )
        != 0
    )
    assert not calls


def test_incomplete_decisions_never_upgrade_and_projection():
    rows = hand_episodes()
    assert f.decisions(rows, "INCOMPLETE")["status"] == "INCOMPLETE"
    assert not f.decisions(rows, "INCOMPLETE")["complete"]
    with pytest.raises(f.Incomplete):
        f.Budget(Clock(), spent=f.GPU_CAP).check()
    summaries = [{"id": str(i)} for i in range(4)]
    records = [
        {
            "episode": str(i),
            "arm": "both",
            "checkpoint": "SWITCH",
            "cost": {
                "allocation_seconds": i + 1,
                "cumulative_seconds": 3 + (i + 1) * (i + 2) / 2,
            },
        }
        for i in range(4)
    ]
    cert = f.certificate(
        "pilot",
        records,
        summaries,
        {"load_seconds": 3, "spent_before": 0, "spent_after": 13},
        {},
    )
    assert cert["projection_seconds"] == 1.25 * (256 * 4 + 3)


def test_numerical_inversion_error_is_explicit(monkeypatch):
    f.paired_interval.cache_clear()

    def fail(*args, **kwargs):
        raise RuntimeError("deliberate numerical failure")

    monkeypatch.setattr(f, "tango_upper_bound", fail)
    with pytest.raises(f.Invalid, match="numerical inversion failure"):
        f.paired_interval(4, 1, 29)


def test_pilot_projection_includes_allocation_between_requests():
    summaries = [{"id": str(i)} for i in range(4)]
    records = [
        {
            "episode": str(i),
            "arm": "both",
            "checkpoint": "SWITCH",
            "cost": {"allocation_seconds": 10, "cumulative_seconds": 3 + 20 * (i + 1)},
        }
        for i in range(4)
    ]
    end = {"load_seconds": 3, "spent_before": 0, "spent_after": 83}
    cert = f.certificate("pilot", records, summaries, end, {})
    assert cert["projection_seconds"] == 1.25 * (256 * 20 + 3)


@pytest.mark.parametrize("checkpoint", f.CHECKPOINTS)
def test_every_checkpoint_is_necessary_no_later_recovery(
    tok, banks, tmp_path, checkpoint
):
    ep = banks["final"][0]

    def policy(ctx, ids, text):
        if ctx["arm"] == "both" and ctx["checkpoint"] == checkpoint:
            obj = json.loads(text)
            obj["answer"] = [999]
            return f.canonical(obj)
        return text

    engine = f.Engine(
        tok,
        FakeBackend(tok, policy),
        f.RecordStore(tmp_path / "records"),
        f.Budget(Clock()),
        {},
    )
    f.episode(engine, ep)
    summaries = f.validate_records(engine.store.rows(), [ep], tok, {}, complete=True)
    assert not summaries[0]["arms"]["both"]["Y"]
    assert not summaries[0]["arms"]["both"]["broken"]
    assert summaries[0]["arms"]["both"]["constraint"] is False


def test_mechanism_strata_and_v3_binding_cost():
    rows = hand_episodes()
    for i in range(128, 141):
        for arm in ("placement-only", "eviction-only", "text-restate"):
            rows[i]["arms"][arm]["Y"] = False
    report = f.decisions(rows)
    assert report["strata"]["both_correct"]["True"]["placement-only"]["b"] == 0
    assert report["strata"]["both_correct"]["False"]["placement-only"]["b"] == 13
    assert "error-demonstration cleanup" in report["mechanism_reading"]
    for key in ("user_fact", "tool_fact", "constraint"):
        changed = copy.deepcopy(rows)
        for i in range(3):
            changed[i]["arms"]["both"][key] = True
        report = f.decisions(changed)
        assert report["primary_pass"] and report["status"] == "FAIL-SAFETY"


def test_cpu_prepare_through_main_cannot_register(tmp_path, monkeypatch):
    monkeypatch.setattr(
        f, "git_bytes", lambda *_: ("DRAFT v2\n" + f.RECAP + "\n" + f.READINGS).encode()
    )
    path = tmp_path / "candidate"
    assert cli().main(["--prepare-freeze", str(path)]) == 0
    manifest = json.loads((path / "manifest.json").read_text())
    assert manifest["status"] == "DRAFT" and manifest["candidate_only"]
    assert "development" not in manifest["files"]


def test_interrupted_prefill_retains_partial_cost(frozen, tok, capsys):
    root, _, _ = frozen
    clock = Clock()
    clock.at, clock.jump = "prefill", 3

    class Interrupted(FakeBackend):
        def prefill(self, *args):
            super().prefill(*args)
            raise KeyboardInterrupt("fabricated foreground interruption")

    assert (
        cli().main(
            args_for(frozen, "competence"),
            tokenizer_factory=lambda _: tok,
            backend_factory=lambda *_: Interrupted(tok, clock=clock),
            clock=clock,
        )
        == 1
    )
    assert "INCOMPLETE" in capsys.readouterr().out
    rows = f.RecordStore(root / "outputs/competence/records").rows()
    assert len(rows) == 1 and not rows[0]["complete"]
    assert rows[0]["cost"]["prefill_seconds"] >= 3
    assert rows[0]["cost"]["allocation_seconds"] >= 3


def test_fable_A1_disclosed_cost_and_binding_net_harm():
    rows = hand_episodes()
    for i, row in enumerate(rows):
        for arm in ("placement-only", "eviction-only", "text-restate"):
            row["arms"][arm]["Y"] = i >= 20
        row["arms"]["both"]["assistant_fact"] = i < 64
        row["arms"]["text-restate"]["assistant_fact"] = i < 10
    report = f.decisions(rows)
    assert report["status"] == "PASS"
    assert report["collateral"]["assistant_fact"]["passes"] is None
    assert report["disclosed_cost"]["assistant_fact"]["candidate"] == 64
    assert report["disclosed_cost"]["assistant_fact"]["comparator"] == 10
    assert (
        "eviction forfeits assistant-authored content it removes (64/64 vs 10/64)"
        in report["headline"]
    )
    assert (
        report["benefit_cost_table"]["assistant_fact"]
        == report["disclosed_cost"]["assistant_fact"]
    )
    for key in ("user_fact", "tool_fact", "constraint"):
        changed = copy.deepcopy(rows)
        for i in range(5):
            changed[i]["arms"]["both"][key] = True
        changed[10]["arms"]["text-restate"][key] = True
        assert f.decisions(changed)["status"] == "FAIL-SAFETY"  # h-r=4
        changed[4]["arms"]["both"][key] = False
        changed[11]["arms"]["text-restate"][key] = True
        assert f.decisions(changed)["collateral"][key]["passes"]  # h-r=2


def test_fable_A2_breakage_five_six_boundaries():
    rows = hand_episodes()
    for i in range(5):
        rows[i]["arms"]["both"]["broken"] = True
    # h=5,r=0 fails the retained exact p>.05 clause (p=1/32).
    assert not f.decisions(rows)["safety"]["passes"]
    rows[20]["arms"]["text-restate"]["broken"] = True
    assert f.decisions(rows)["safety"]["passes"]
    rows[5]["arms"]["both"]["broken"] = True
    assert not f.decisions(rows)["safety"]["passes"]
    assert f.exact_upper(5, 256) == pytest.approx(0.0406256185)


@pytest.mark.parametrize("direction,threshold", [("ascending", 52), ("default", 56)])
def test_fable_A3_competence_boundaries(banks, direction, threshold):
    rows = [
        dict(id=e["id"], family=e["family"], direction=e["direction"], success=True)
        for e in banks["competence"]
    ]
    cell = [r for r in rows if r["family"] == "sort" and r["direction"] == direction]
    for i, r in enumerate(cell):
        r["success"] = i < threshold
    assert f.competence_gate(rows)["status"] == "PASS"
    cell[threshold - 1]["success"] = False
    assert f.competence_gate(rows)["status"] == "INELIGIBLE"


def test_tool_group_matches_pinned_qwen_template(tok, banks):
    """Fable B2 / FOCUS2-1: compare independent template and actual consumer."""
    from jinja2 import Environment

    ep = banks["final"][0]
    template = json.loads(
        (ROOT / "models/qwen3-4b-hf/tokenizer_config.json").read_text()
    )["chat_template"]
    messages = [
        {"role": "user", "content": f.TEMPLATES["tool_request"]},
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [{"function": {"name": "fact", "arguments": {}}}],
        },
        {"role": "tool", "content": f.canonical({"tool_fact": ep["tool_fact"]})},
        {"role": "assistant", "content": "."},
        {"role": "user", "content": "Next request."},
    ]
    native = (
        Environment()
        .from_string(template)
        .render(messages=messages, add_generation_prompt=False)
    )
    expected = native.split("<|im_start|>user\nNext request.")[0]
    h = f.initial_history(tok, ep)
    actual = h.render()
    first = next(s["start"] for s in actual["segments"] if s["scope"] == "tool-fact")
    assert actual["ids"][first:] == f.encode(tok, expected)
    assert "<tools>" in tok.decode(actual["ids"])
    old = h.fork()
    returned = next(m for m in old.messages if m["kind"] == "tool_return")
    returned["role"] = "tool"
    returned["parts"][0]["ids"] = f.encode(tok, "<|im_start|>tool\n")
    with pytest.raises(f.Invalid, match="tool|role"):
        old.render()
    for step in ("SET", "PREHOLD"):
        h.request(ep, step)
        h.answer(f.encode(tok, f.gold(ep, step)), f.EOS)
    for arm in f.ARMS:
        branch = h.fork()
        for step in ("SWITCH", "BACK", "CLEAR"):
            f.intervene(branch, ep, arm, step)
            assert expected in tok.decode(
                branch.render()["ids"], skip_special_tokens=False
            )
            branch.request(ep, step, cue=f.current_cue(ep, arm, step))
            branch.answer(f.encode(tok, f.gold(ep, step)), f.EOS)


@pytest.mark.parametrize("answer", ["", "Echo " * 100])
def test_invalid_delay_blocks_replay_and_complete_analysis(
    tok, banks, tmp_path, answer
):
    """FOCUS2-2: execution and offline consumer must reject the same raw delay."""
    ep = next(e for e in banks["pilot"] if e["delay"])
    backend = FakeBackend(
        tok,
        lambda ctx, ids, text: (
            answer if ctx["checkpoint"].startswith("DELAY") else text
        ),
    )
    engine = f.Engine(
        tok, backend, f.RecordStore(tmp_path / "rows"), f.Budget(Clock()), {}
    )
    with pytest.raises(f.Invalid, match="delay"):
        f.episode(engine, ep)
    rows = engine.store.rows()
    assert len(rows) == 1 and rows[0]["checkpoint"] == "DELAY0"
    assert rows[0]["complete"] and rows[0]["flags"]["broken"]
    assert [c["checkpoint"] for c in backend.calls] == ["DELAY0"]
    for complete in (False, True):
        with pytest.raises(f.Invalid, match="delay"):
            f.validate_records(rows, [ep], tok, {}, complete=complete)
    assert f.decisions([], "INVALID")["fixed_n"] == 256


@pytest.mark.parametrize("answer", [".", "Noted.", "x " * 62 + "x"])
def test_FOCUS2_2_valid_delay_controls(tok, banks, tmp_path, answer):
    ep = next(e for e in banks["pilot"] if e["delay"])
    assert len(f.encode(tok, answer)) <= 63
    engine = f.Engine(
        tok,
        FakeBackend(
            tok,
            lambda ctx, ids, text: (
                answer if ctx["checkpoint"].startswith("DELAY") else text
            ),
        ),
        f.RecordStore(tmp_path / "rows"),
        f.Budget(Clock()),
        {},
    )
    f.episode(engine, ep)
    assert f.validate_records(engine.store.rows(), [ep], tok, {}, complete=True)[0][
        "arms"
    ]["both"]["Y"]


@pytest.mark.parametrize("terminal", [f.EOS, f.END, None])
def test_astra_terminal_token_repair_edge(tok, banks, terminal):
    ep = banks["final"][0]
    h = f.initial_history(tok, ep)
    for step in ("SET", "PREHOLD"):
        h.request(ep, step)
        h.answer(f.encode(tok, "retired"), terminal)
    before = h.render()
    edit = f.intervene(h, ep, "both", "SWITCH")
    decoded = tok.decode(h.render()["ids"], skip_special_tokens=False)
    assert "<|endoftext|>" not in decoded
    assert decoded.count("<|im_start|>assistant\n.<|im_end|>\n") >= 2
    if terminal == f.END:
        positions = [i for i, t in enumerate(before["ids"]) if t == f.END]
        assert len(positions) == 2
        assert all(edit["original_to_edited"][i] is None for i in positions)


def test_fable_B3_pilot_breakage_does_not_stop(tok, banks, tmp_path):
    backend = FakeBackend(
        tok,
        lambda ctx, ids, text: (
            "." if ctx["arm"] == "both" and ctx["checkpoint"] == "SWITCH" else text
        ),
    )
    engine = f.Engine(
        tok, backend, f.RecordStore(tmp_path / "rows"), f.Budget(Clock()), {}
    )
    assert f.run_episodes(engine, banks["pilot"]) == "COMPLETE"
    rows = engine.store.rows()
    summaries = f.validate_records(rows, banks["pilot"], tok, {}, complete=True)
    assert len(summaries) == 4 and all(r["arms"]["both"]["broken"] for r in summaries)
    end = dict(spent_before=0, load_seconds=0, spent_after=engine.budget.elapsed())
    assert f.certificate("pilot", rows, summaries, end, {})["status"] == "PASS"


def test_astra_development_coverage_cannot_be_empty(banks):
    with pytest.raises(f.Invalid, match="development"):
        f.validate_banks(
            banks, {"coverage": list(range(31, 40)) + ["repair"], "fingerprints": []}
        )


def rebind_fixture(frozen):
    root, folder, launch = frozen
    manifest = json.loads((folder / "manifest.json").read_text())
    for desc in manifest["files"].values():
        desc["sha256"] = f.sha((root / desc["path"]).read_bytes())
    review = json.loads((folder / "review.json").read_text())
    review["dependencies"] = {
        k: d["sha256"] for k, d in manifest["files"].items() if k != "review"
    }
    (folder / "review.json").write_text(f.canonical(review))
    manifest["files"]["review"]["sha256"] = f.sha((folder / "review.json").read_bytes())
    (folder / "manifest.json").write_text(f.canonical(manifest))
    freeze_commit = commit(root)
    receipt = json.loads(launch.read_text())
    receipt.update(
        freeze_commit=freeze_commit,
        manifest_sha256=f.sha((folder / "manifest.json").read_bytes()),
    )
    launch.write_text(f.canonical(receipt))
    commit(root)


def test_fable_B1_ignored_model_preflight_and_tamper(frozen, tok, capsys):
    root, folder, launch = frozen
    model = folder / "model.fixture"
    git(root, "rm", "--cached", "freeze/model.fixture")
    (root / ".gitignore").write_text("freeze/model.fixture\n")
    manifest = json.loads((folder / "manifest.json").read_text())
    manifest["files"]["model"].update(
        tracked=False,
        bytes=model.stat().st_size,
        source_revision="fabricated CPU fixture",
    )
    (folder / "manifest.json").write_text(f.canonical(manifest))
    rebind_fixture(frozen)
    assert f.preflight(folder, launch, "competence", root / "outputs", tok=tok)
    model.write_text("tampered model fixture")
    calls = []
    assert (
        cli().main(
            args_for(frozen, "competence"),
            tokenizer_factory=lambda _: tok,
            backend_factory=lambda *a: calls.append(a),
        )
        == 1
    )
    assert not calls and "asset" in capsys.readouterr().out


def test_FOCUS2_1_frozen_renderer_mismatch_refuses_before_backend(frozen, tok, capsys):
    _, folder, _ = frozen
    path = folder / "templates.json"
    templates = json.loads(path.read_text())
    templates["renderer_fixture_sha256"] = "0" * 64
    path.write_text(f.canonical(templates))
    rebind_fixture(frozen)
    calls = []
    assert (
        cli().main(
            args_for(frozen, "competence"),
            tokenizer_factory=lambda _: tok,
            backend_factory=lambda *a: calls.append(a),
        )
        == 1
    )
    assert not calls and "template/rendered" in capsys.readouterr().out
