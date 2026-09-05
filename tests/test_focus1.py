"""CPU behavioral contracts for the prospective FOCUS-1 v2 harness."""

import importlib.util
import itertools
import json
import math
import re
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

import pytest
import torch

from stencil import focus1 as f


@pytest.fixture(autouse=True)
def cpu_only(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("real model/CUDA/forbidden data reached by CPU fixture")

    monkeypatch.setattr(torch.cuda, "init", forbidden)
    monkeypatch.setattr(torch.Tensor, "cuda", forbidden)
    monkeypatch.setattr(torch, "load", forbidden)
    monkeypatch.setattr(f, "load_backend", forbidden)
    real_open = Path.open

    def guarded(path, *args, **kwargs):
        value = str(path)
        if any(x in value for x in ("data/bench", "data/b3", "data/sc1")):
            forbidden()
        if "/models/" in value:
            forbidden()
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", guarded)


def test_seed_and_banks():
    assert f.seed("extraction", 0, "sort0") == int(
        "be7ecf6ccaccc2bd1a087ca8d6d86e7df23333ce19d3a8dc0da2dcb86aac107d", 16
    )
    banks = f.generate_banks()
    assert banks["extraction"][0]["lists"]["sort0"] == [-1, -3, -7, 3, -2]
    assert f.seed("test", 63, "randomB") == int(
        "4028aa50106b9fa4de3f5851966842a1b6ca835b2eb9636f849899c2f588c859", 16
    )
    assert banks == f.generate_banks()
    seen = set()
    for split, n in (("extraction", 64), ("setup", 32), ("test", 64)):
        rows = banks[split]
        assert len(rows) == n
        assert Counter(r["length"] for r in rows) == dict.fromkeys(range(5, 9), n // 4)
        if split != "extraction":
            assert Counter((r["length"], r["initial"]) for r in rows) == {
                (length, task): n // 8 for length in range(5, 9) for task in ("A", "B")
            }
        for row in rows:
            for values in row["lists"].values():
                f.validate_operands(values)
                key = tuple(sorted(values))
                assert key not in seen
                seen.add(key)
            if split == "extraction":
                triples = f.extraction_prompts(row)
                for prompt in triples.values():
                    assert json.dumps(row["lists"]["sort0"]) in prompt
    assert len(seen) == 640
    with pytest.raises(f.Invalid):
        f.validate_operands([-2, -1, 0, 1, 2])
    with pytest.raises(f.Invalid):
        f.validate_operands([2, 1, 0, -1, -2])
    bad = f.generate_banks()
    bad["test"][0]["lists"]["sort0"] = bad["setup"][0]["lists"]["sort0"]
    with pytest.raises(f.Invalid):
        f.validate_banks(bad)


@pytest.mark.parametrize("n", range(9))
def test_exact_mcnemar_exhaustive(n):
    for wins in range(n + 1):
        enumerated = sum(
            sum(bits) >= wins for bits in itertools.product((0, 1), repeat=n)
        )
        expected = enumerated / 2**n if n else 1
        assert f.mcnemar(wins, n - wins) == expected


def test_registered_arithmetic():
    assert f.ALPHA == 1 / 60
    for h, expected in enumerate(
        (0.0011790184577738583, 0.00956314971305463, 0.03890760910653732)
    ):
        assert f.binomial_lower(64, h, 0.1) == pytest.approx(expected, abs=1e-16)
    assert f.mcnemar(33, 17) <= f.ALPHA < f.mcnemar(34, 18)
    p = 29 / 32
    assert 1 - f.binomial_lower(64, 47, p**2) == pytest.approx(0.945636, abs=1e-6)
    assert 1 - f.binomial_lower(64, 47, p**4) == pytest.approx(0.122662, abs=1e-6)
    assert 0.05 ** (1 / 32) == pytest.approx(0.910632, abs=1e-6)
    # With BOTH the count and net floors, c<=16 at the largest passing tail.
    # Keep the registered tests anyway; flag the draft's redundancy wording.
    feasible = [
        f.mcnemar(b, c)
        for b in range(65)
        for c in range(65 - b)
        if b - c >= 16 and b + (64 - b - c) >= 48
    ]
    assert max(feasible) == pytest.approx(0.01465247336026465)


@pytest.mark.parametrize(
    "text,invalid,exact",
    [
        ("[-2,0,1,3,9]", False, True),
        ("[9,3,1,0,-2]", False, False),
        ("[0,0,0,0,0]", False, False),
        ("[true,0,1,3,9]", True, False),
        ("[]", True, False),
        ("[-2,0]", True, False),
        ("[NaN,0,1,3,9]", True, False),
        ("answer: [-2,0,1,3,9]", True, False),
        ("[1.5,0,1,3,9]", True, False),
        ("[-2.0,0,1,3,9]", False, True),
        ("", True, False),
    ],
)
def test_short_scoring(text, invalid, exact):
    result = f.score_reply(text, [8, f.EOS[0]], [-2, 0, 1, 3, 9])
    assert result["I"] is invalid
    assert result["exact"] is exact
    assert result["broken"] is invalid


def test_decode_does_not_hide_non_eos_special_tokens(tmp_path, fake_backend):
    row = f.generate_banks()["test"][0]
    values = row["lists"]["sort0"]
    queued = iter([151644, fake_backend.tokenizer.reply(values), f.EOS[0]])
    original = fake_backend.model

    class SpecialReply:
        def __call__(self, tokens, **kwargs):
            logits = original(tokens, **kwargs)
            if tokens.shape[1] == 1 and tokens[0, -1].item() not in f.EOS:
                logits.fill_(-100)
                logits[0, 0, next(queued)] = 100
            return logits

    fake_backend.model = SpecialReply()
    engine = engine_for(tmp_path, fake_backend)
    ids = f.layout(fake_backend.tokenizer, values)["ids"]
    record, _ = engine.answer(row, "SET", "OFF", fake_backend.empty(), ids, task="OFF")
    assert "<|im_start|>" in record["output"]["text"]
    assert record["score"]["I"] and not record["score"]["exact"]


def test_truncated_repetition_and_deadline():
    for tokens, deadline in (([8] * 64, False), ([8], True)):
        out = f.score_reply("[0,1,2,3,4]", tokens, [0, 1, 2, 3, 4], deadline=deadline)
        assert out["T"] and out["broken"]
    out = f.score_reply("[0,1,2,3,4]", [1, 2, 3, 4] * 15 + [f.EOS[0]], [0, 1, 2, 3, 4])
    assert out["R"] and out["broken"]


def test_paired_extraction_and_hook():
    off = [torch.tensor([10.0, 20.0]), torch.tensor([30.0, 40.0])]
    vectors, stats = f.normalize_pair(
        [v + torch.tensor([3.0, 0.0]) for v in off],
        [v + torch.tensor([0.0, 5.0]) for v in off],
        off,
    )
    assert torch.equal(vectors["A"], torch.tensor([4.0, 0.0]))
    assert torch.equal(vectors["B"], torch.tensor([0.0, 4.0]))
    assert stats["rho"] == 4 and stats["cosine"] == 0
    events = []
    hook = f.hook(vectors["A"], 0.5, 12, 0, events)
    hidden = torch.zeros(1, 4, 2)
    actual = hook[1](hidden)
    assert torch.equal(actual[:, :-1], hidden[:, :-1])
    assert torch.equal(actual[:, -1], torch.tensor([[2.0, 0.0]]))
    assert events[0]["generated_position"] == 0
    assert f.hook(None, 1, 12, 0, []) is None
    assert f.hook(vectors["A"], 0, 12, 0, []) is None
    for bad in (off, [torch.full((2,), float("nan"))] * 2):
        with pytest.raises(f.Invalid):
            f.normalize_pair(bad, off, off)
    _, collinear = f.normalize_pair([x + 1 for x in off], [x + 2 for x in off], off)
    assert collinear["cosine"] > 0.9


def test_fp32_difference_is_taken_before_averaging():
    off = [torch.tensor([1e8, 0.0]), torch.tensor([1e8, 0.0]), torch.tensor([1.0, 0.0])]
    a = [off[0].clone(), off[1].clone(), torch.tensor([2.0, 0.0])]
    b = [x + torch.tensor([0.0, 3.0]) for x in off]
    _, stats = f.normalize_pair(a, b, off)
    assert stats["raw_norms"]["A"] == pytest.approx(1 / 3)


def perfect_episodes():
    return [
        dict(
            episode=i,
            initial="AB"[i % 2],
            S=True,
            O=False,
            W=True,
            V=False,
            R=False,
            C=True,
            P=True,
            H=False,
            K=True,
            clear_imposition=False,
            keep_imposition=False,
            integrity=True,
            broken=dict.fromkeys(f.TEST_ARMS, False),
        )
        for i in range(64)
    ]


def test_complete_pass_harm_and_labels():
    rows = perfect_episodes()
    assert f.endpoints(rows)["state"] == "PASS"
    assert "CLEAR-UNCHALLENGED" in f.endpoints(rows)["labels"]
    rows[0]["H"] = True
    assert f.endpoints(rows)["state"] == "PASS"
    rows[1]["H"] = True
    assert f.endpoints(rows)["state"] == "FAIL"
    rows = perfect_episodes()
    for row in rows:
        row["C"] = row["P"] = row["K"] = False
    assert f.endpoints(rows)["state"] == "PASS"  # shared copy errors are not H
    rows[1]["H"] = False
    rows[1]["clear_imposition"] = True
    assert f.endpoints(rows)["state"] == "FAIL"


@pytest.mark.parametrize("key", ("S", "W", "R", "O", "V", "integrity"))
def test_independent_endpoint_failures(key):
    rows = perfect_episodes()
    for row in rows:
        row[key] = key in ("R", "O", "V")
    assert f.endpoints(rows)["state"] == ("INVALID" if key == "integrity" else "FAIL")


def test_stratum_net_partial_and_control_safety():
    rows = perfect_episodes()
    for row in rows[:18:2]:
        row["S"] = False
    assert sum(r["S"] for r in rows) >= 48
    assert f.endpoints(rows)["state"] == "FAIL"
    rows = perfect_episodes()
    for row in rows[:49]:
        row["O"] = True
    assert f.endpoints(rows)["state"] == "FAIL"
    assert any("default-coincident" in s for s in f.endpoints(rows)["labels"])
    rows = perfect_episodes()
    for row in rows:
        row["broken"]["OFF"] = row["broken"]["shuffled"] = True
    assert f.endpoints(rows)["state"] == "PASS"
    assert f.endpoints(rows[:20])["state"] == "INCOMPLETE"
    rows[0]["R"] = True
    partial = f.endpoints(rows[:20])
    assert partial["state"] == "FAIL" and partial["missing"] == 44
    assert partial["tests"] == {}


def cli_module():
    path = Path(__file__).resolve().parents[1] / "scripts/focus1.py"
    spec = importlib.util.spec_from_file_location("focus1_cli_fixture", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_cli_help_and_missing_evidence(tmp_path, monkeypatch):
    cli = cli_module()
    monkeypatch.setattr(f, "EXPERIMENT_ROOT", tmp_path)
    with pytest.raises(SystemExit) as exc:
        cli.main(["--help"])
    assert exc.value.code == 0
    for mode in ("setup", "extract", "select", "run"):
        result = cli.main([mode, "--out", str(tmp_path)])
        assert result["state"] == "INVALID"
        assert "registration" in " ".join(result["reasons"]).lower()
    assert cli.main(["analyze", "--out", str(tmp_path)])["state"] != "PASS"
    assert (
        cli.main(["setup", "--generate-only", "--out", str(tmp_path / "external")])[
            "state"
        ]
        == "INVALID"
    )


def test_script_import_does_no_experiment_work(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("experiment side effect during script import")

    monkeypatch.setattr(f, "generate_banks", forbidden)
    monkeypatch.setattr(f, "load_tokenizer", forbidden)
    monkeypatch.setattr(f, "execute_stage", forbidden)
    monkeypatch.setattr(f.Store, "__init__", forbidden)
    assert callable(cli_module().main)


def test_append_only_records(tmp_path):
    store = f.Store(tmp_path)
    store.write("fixture.json", {"value": 1})
    with pytest.raises(f.Invalid):
        store.write("fixture.json", {"value": 2})
    store.append("fixture", {"attempt_id": "one", "value": 1})
    with pytest.raises(f.Invalid):
        store.append("fixture", {"attempt_id": "one", "value": 2})
    assert store.read_log("fixture")[0]["value"] == 1
    path = tmp_path / "fixture.jsonl"
    path.write_text(path.read_text().replace('"value":1', '"value":2'))
    with pytest.raises(f.Invalid):
        store.read_log("fixture")


def test_budget_retained_maxima_and_reservations():
    budget = f.Budget(spent=0, rates=dict.fromkeys(f.COST_CLASSES, 1.0))
    budget.observe("canonical", 0.2)
    assert budget.rates["canonical"] == 1.0
    assert f.remaining_work("run")["canonical"] == 1024
    assert sum(f.remaining_work("run").values()) == 1472
    full = f.remaining_work("select")
    assert full["certification"] == 512 and full["transient"] == 64
    assert full["clear"] >= 9 * 64 * 2 + 128
    assert budget.project(full, reloads=2) == pytest.approx(
        2 + 1.25 * 3 * sum(full.values())
    )
    assert budget.deadline == 12
    budget.spent = f.CAP - 3
    with pytest.raises(f.Incomplete):
        budget.reserve({}, reloads=0)
    budget.spent = f.CAP + 1
    with pytest.raises(f.Incomplete):
        budget.reserve({}, reloads=0)


def test_pair_harm_is_query_specific():
    assert f.copy_pairs([True, False], [False, True], [True, True])["H"]
    assert not f.copy_pairs([False, False], [False, False], [False, False])["H"]
    assert not f.copy_pairs([True, True], [False, False], [False, False])["H"]
    assert f.copy_pairs([False, True], [True, True], [True, True])["H"]
    assert math.isclose(f.mcnemar(8, 0), 1 / 256)


class FakeTokenizer:
    """Characters for prompts; one synthetic token per complete JSON reply."""

    def __init__(self):
        self.outputs = {}
        self.reverse = {}
        self.special = {
            "<|im_start|>": 151644,
            "<|im_end|>": 151645,
            "<|endoftext|>": 151643,
        }

    def token_to_id(self, value):
        return self.special.get(value)

    def encode(self, text):
        result = []
        for part in re.split(
            "(<\\|im_start\\|>|<\\|im_end\\|>|<\\|endoftext\\|>)", text
        ):
            if part in self.special:
                result.append(self.special[part])
            else:
                result.extend(ord(c) + 10 for c in part)
        return SimpleNamespace(ids=result)

    def reply(self, values):
        text = json.dumps(values)
        if text not in self.reverse:
            index = 1000 + len(self.reverse)
            self.reverse[text] = index
            self.outputs[index] = text
        return self.reverse[text]

    def decode(self, ids, skip_special_tokens=True):
        special = {v: k for k, v in self.special.items()}
        return "".join(
            self.outputs[t]
            if t in self.outputs
            else ("" if skip_special_tokens else special[t])
            if t in special
            else chr(t - 10)
            if t >= 10
            else "?"
            for t in ids
        )


class FakeKV:
    def __init__(self, cfg=None):
        self.cfg = cfg or SimpleNamespace(n_layer=21, d_model=2)
        self.length = 0
        self.k = [None] * self.cfg.n_layer
        self.v = [None] * self.cfg.n_layer


class FakeTrunk:
    """Records real hook effects in KV. OFF removal preserves earlier deltas."""

    def __init__(self, tokenizer, policy=None):
        self.cfg = SimpleNamespace(n_layer=21, d_model=2)
        self.tokenizer = tokenizer
        self.policy = policy
        self.calls = []

    def __call__(self, tokens, *, cache, residual_hook=None, capture_hidden=None):
        ids = tokens[0].tolist()
        old = [] if cache.k[0] is None else cache.k[0][0, 0, :, 0].int().tolist()
        all_ids = old + ids
        text = self.tokenizer.decode(all_ids, skip_special_tokens=False)
        last_prompt = text.rsplit(f.USER, 1)[-1]
        current = torch.zeros(1, len(ids), 2)
        captured = {}
        visible = (
            "ascending"
            if "ascending order" in last_prompt
            else "descending"
            if "descending order" in last_prompt
            else None
        )
        if capture_hidden is not None and visible:
            current += torch.tensor(
                [3.0, 0.0] if visible == "ascending" else [0.0, 5.0]
            )
        active = None
        for layer in range(self.cfg.n_layer):
            if residual_hook is not None and layer == residual_hook[0]:
                current = residual_hook[1](current)
                active = (
                    "random"
                    if bool((current[0, -1] != 0).all())
                    else "A"
                    if current[0, -1, 0] > current[0, -1, 1]
                    else "B"
                )
            if capture_hidden is not None and layer in capture_hidden:
                captured[layer] = current.clone()
            base = torch.stack((tokens[0].float(), torch.zeros(len(ids))), dim=-1)[
                None, None
            ]
            new = base + current[:, None]
            cache.k[layer] = (
                new if cache.k[layer] is None else torch.cat((cache.k[layer], new), 2)
            )
            cache.v[layer] = (
                new.clone()
                if cache.v[layer] is None
                else torch.cat((cache.v[layer], new.clone()), 2)
            )
        cache.length += len(ids)
        self.calls.append(dict(ids=ids, active=active, before=old))
        logits = torch.full((1, 1, 151646), -100.0)
        if ids[-1] in self.tokenizer.outputs or ids[-1] in f.EOS:
            choice = f.EOS[0]
        else:
            match = re.search(r"Integers: (\[[^\]]+\])", last_prompt)
            values = json.loads(match.group(1)) if match else [1, -1, 0, 3, 2]
            copy = last_prompt.startswith("Copy these integers")
            residual = bool((cache.k[20] - cache.k[0]).abs().max())
            chosen = (
                active
                if active in ("A", "B")
                else "B"
                if visible == "descending"
                else "A"
            )
            answer = (
                [0] * len(values)
                if active == "random"
                else values
                if copy and not active
                else f.target(values, chosen)
            )
            if self.policy is not None:
                answer = self.policy(values, copy, active, residual, text, answer)
            choice = self.tokenizer.reply(answer)
        logits[0, 0, choice] = 100
        return (logits, captured) if capture_hidden is not None else logits


@pytest.fixture
def fake_backend():
    previous = torch.get_num_threads()
    torch.set_num_threads(1)
    tokenizer = FakeTokenizer()
    backend = f.Backend(FakeTrunk(tokenizer), tokenizer, FakeKV)
    yield backend
    torch.set_num_threads(previous)


def engine_for(tmp_path, backend, mode="run"):
    return f.Engine(backend, f.Store(tmp_path), mode, {"fixture": "only"})


def directions():
    return {"A": torch.tensor([4.0, 0.0]), "B": torch.tensor([0.0, 4.0])}


def test_fake_tokenizer_layout_consumption(fake_backend):
    row = f.generate_banks()["extraction"][0]
    layouts = f.bank_layouts(fake_backend.tokenizer, [row])["0"]["sort0"]
    assert len({layouts[k]["ids"][-1] for k in ("A", "B", "absent")}) == 1
    hold = f.layout(fake_backend.tokenizer, row["lists"]["sort0"], phase="HOLD")
    delay = fake_backend.tokenizer.encode(f.NEUTRAL * 128).ids[:128]
    assert hold["delay_ids"] == delay and len(delay) == 128
    start = len(fake_backend.tokenizer.encode(f.USER).ids)
    assert hold["ids"][start : start + 128] == delay
    broken = FakeTokenizer()
    broken.special["<|im_end|>"] = 3
    with pytest.raises(f.Invalid, match="EOS"):
        f.bank_layouts(broken, [row])
    final_bad = FakeTokenizer()
    original = final_bad.encode

    def mismatch(text):
        result = original(text)
        if "ascending order" in text:
            result.ids[-1] += 1
        return result

    final_bad.encode = mismatch
    with pytest.raises(f.Invalid, match="final wrapper"):
        f.bank_layouts(final_bad, [row])


def test_extraction_reads_layer_inputs_through_trunk(tmp_path, fake_backend):
    engine = engine_for(tmp_path, fake_backend, "extract")
    result = f.extract_vectors(engine, f.generate_banks()["extraction"])
    assert result["state"] == "READY"
    assert len(engine.store.read_log("extract")) == 192
    for layer in ("12", "16", "20"):
        assert result["vectors"][layer] == {"A": [4.0, 0.0], "B": [0.0, 4.0]}
        assert result["stats"][layer]["rho"] == 4
    assert not any(call["active"] for call in fake_backend.model.calls)


def test_main_schedule_independent_clones_and_transient(tmp_path, fake_backend):
    row = f.generate_banks()["test"][1]
    engine = engine_for(tmp_path, fake_backend)
    records, histories = engine.main_decisions(row, directions(), 1, 12)
    for j, phase in enumerate(f.PHASES):
        expected = f.schedule("B")[j]
        assert records[phase, "correct"]["source_enum"] == expected
        assert records[phase, "swapped"]["source_enum"] == f.other(expected)
        for arm in f.MAIN_ARMS:
            assert (
                records[phase, arm]["layout"]["ids"]
                == f.layout(
                    fake_backend.tokenizer, row["lists"][f"sort{j}"], phase=phase
                )["ids"]
            )
        assert records[phase, "correct"]["score"]["exact"]
        assert records[phase, "swapped"]["score"]["exact"]
    transient = engine.transient(row, histories["SET"], 12)
    assert (
        transient["output"]["history_before"]
        == records["SET", "correct"]["output"]["history_after"]
    )
    assert transient["output"]["history_before"][-1] in f.EOS
    assert not transient["output"]["hook_events"]
    assert not transient["score"][
        "exact"
    ]  # default A, initially B: descriptive failure
    assert f.impossible(engine.rows) is None
    r = f.random_directions("test", 1, 2, 4)
    assert not torch.equal(r["A"], r["B"])
    for vector in r.values():
        assert float(vector.norm()) == pytest.approx(4)
    clone = f.clone_history(histories["SET"])
    clone.cache.k[0].zero_()
    assert torch.count_nonzero(histories["SET"].cache.k[0]) > 0
    bad = f.clone_history(histories["SET"])
    bad.tokens.pop()
    with pytest.raises(f.Invalid, match="omission"):
        f.check_history(bad)
    bad = f.clone_history(histories["SET"])
    bad.cache.k[0] = bad.cache.k[0][:, :, :-1]
    with pytest.raises(f.Invalid, match="positions"):
        f.check_history(bad)


@pytest.mark.parametrize("query", (0, 1))
def test_retained_clear_residual_harm_on_either_query(tmp_path, fake_backend, query):
    row = f.generate_banks()["test"][0]
    bad_values = row["lists"][f"copy{query}"]

    def policy(values, copy, active, residual, text, answer):
        if copy and not active and residual and values == bad_values:
            return [0] * len(values)  # valid wrong copy, not old-task imposition
        return answer

    fake_backend.model.policy = policy
    engine = engine_for(tmp_path, fake_backend)
    _, histories = engine.main_decisions(row, directions(), 1, 12)
    records, _ = engine.neutral(row, histories["BACK"], directions(), 1, 12)
    c = [r for r in records if r["arm"] == "CLEAR"]
    p = [r for r in records if r["arm"] == "replay"]
    assert f.copy_pairs(
        [r["score"]["exact"] for r in c],
        [r["score"]["exact"] for r in p],
        [False, False],
    )["H"]
    assert not any(r["score"]["imposition"] for r in c)
    assert p[1]["output"]["history_before"] == c[0]["output"]["history_after"]
    for r in c:
        assert not r["output"]["hook_events"]
        assert all(d["k"] == d["v"] == 0 for d in r["comparison"]["kv_deltas"][:12])
        assert all(d["k"] > 0 and d["v"] > 0 for d in r["comparison"]["kv_deltas"][12:])
    pairs = [r for r in engine.rows if r["kind"] == "pair"]
    assert pairs[query]["copy_pair"] == [False, True]
    assert not pairs[query]["token_equal"] and pairs[query]["first_logit_delta"] > 0
    assert pairs[1 - query]["token_equal"]
    replay = fake_backend.teacher_force(histories["BACK"].tokens)
    with pytest.raises(f.Invalid, match="hook events"):
        f.compare_caches(replay, f.clone_history(replay), layer=12)
    vacuous = f.clone_history(histories["BACK"])
    vacuous.cache.k = [x.clone() for x in replay.cache.k]
    vacuous.cache.v = [x.clone() for x in replay.cache.v]
    with pytest.raises(f.Invalid, match="vacuous"):
        f.compare_caches(vacuous, replay, layer=12)


def test_competence_32_pair_floor_and_schema_separate(tmp_path, fake_backend):
    rows = f.generate_banks()["setup"]
    engine = engine_for(tmp_path, fake_backend, "competence")
    result = f.competence(engine, rows)
    assert result["state"] == "READY"
    assert result["copy_pairs"] == {"exact": 32, "n": 32}
    assert result["tasks"]["B"]["absent_exact"] == 0
    assert result["tasks"]["B"]["schema"] == 32
    bad_values = rows[0]["lists"]["copy1"]
    fake_backend.model.policy = lambda v, c, a, r, t, out: (
        [0] * len(v) if c and v == bad_values else out
    )
    failed = f.competence(
        engine_for(tmp_path / "bad", fake_backend, "competence"), rows
    )
    assert failed["state"] == "INELIGIBLE" and failed["copy_pairs"]["exact"] == 31


def test_selection_first_cell_and_all_certification(
    tmp_path, fake_backend, monkeypatch
):
    rows = f.generate_banks()["setup"]
    store = f.Store(tmp_path)
    for name in (
        "bank",
        "registration",
        "bfcl-completion",
        "timing",
        "competence",
        "extract",
    ):
        store.write(name + ".json", {"fixture": name})
    engine = f.Engine(fake_backend, store, "select", {"fixture": "only"})
    extraction = {
        "vectors": {"12": {t: v.tolist() for t, v in directions().items()}},
        "stats": {"12": {"cosine": 0.91, "rho": 4}},
    }
    calls = []
    original = engine.keep_only

    def observed_keep(*args):
        calls.append("KEEP")
        assert sum(r.get("kind") == "pair" for r in engine.rows) == 128
        return original(*args)

    monkeypatch.setattr(engine, "keep_only", observed_keep)
    result = f.selection(engine, rows, extraction)
    assert result["state"] == "READY" and result["selected"] == {
        "alpha": 0.5,
        "layer": 12,
    }
    assert result["labels"] == ["HIGH-COLLINEARITY"]
    assert result["certification"]["decisions"] == 512
    cert = [
        r for r in engine.rows if r["attempt_id"].startswith("select:certification:")
    ]
    assert len(cert) == 512 and len(calls) == 64
    assert Counter(r["arm"] for r in cert) == dict.fromkeys(
        ("correct", "swapped", "transplant", "sham"), 128
    )
    assert result["cells"][0]["tasks"]["A"]["joint_copy"] == 32


def registered_fixture(tmp_path, monkeypatch, tokenizer):
    import difflib

    draft = f.reviewed_section()
    repo = tmp_path / "repo"
    repo.mkdir()
    lines = draft.decode().splitlines(keepends=True)
    lines[0] = (
        "## FOCUS-1 — SET/HOLD/SWITCH/CLEAR SCREEN ON FROZEN QWEN "
        "(REGISTERED v2, CPU fixture)\n"
    )
    lines = [
        "STATE: registered CPU fixture, no real execution.\n"
        if line.startswith("STATE:")
        else line
        for line in lines
    ]
    registered = "".join(lines).encode()
    (repo / "LEDGER-PLAN.md").write_bytes(draft + b"\n" + registered)
    root = repo / "experiment"
    monkeypatch.setattr(f, "ROOT", repo)
    monkeypatch.setattr(f, "EXPERIMENT_ROOT", root)
    monkeypatch.setattr(f, "fingerprints", lambda: {"fake_config_and_code": "a" * 64})
    store = f.Store(root)
    result = cli_module().main(
        ["setup", "--generate-only", "--out", str(root)],
        tokenizer_factory=lambda: tokenizer,
    )
    assert result["state"] == "INCOMPLETE" and result["counts"]["test"] == 64
    reg = dict(
        status="REGISTERED",
        reviewed_section_sha256=f.REVIEWED_HASH,
        registered_section_sha256=f.digest(registered),
        section_start=len(draft) + 1,
        section_end=len(draft) + 1 + len(registered),
        textual_deltas=list(
            difflib.unified_diff(
                draft.decode().splitlines(keepends=True),
                lines,
                fromfile="reviewed-v2",
                tofile="registered-v2",
            )
        ),
        review=dict(
            registered_section_sha256=f.digest(registered),
            open_high=0,
            open_critical=0,
            science_changes_reviewed=True,
            evidence_sha256="b" * 64,
        ),
        bank_sha256=f.file_hash(store.path("bank.json")),
        preflight_id="results/qwen/bfcl-evict-v2-preflight",
    )
    store.write("registration.json", reg)
    store.write(
        "bfcl-completion.json",
        dict(
            preflight_id=reg["preflight_id"],
            terminal_status="failed",
            exit_code=1,
            recorded_at="fixture",
            terminal_record="CPU fixture, not readiness evidence",
        ),
    )
    return store


def test_all_modes_real_cli_fake_backend_and_integrity(
    tmp_path, fake_backend, monkeypatch, capsys
):
    cli = cli_module()
    store = registered_fixture(tmp_path, monkeypatch, fake_backend.tokenizer)
    common = [
        "--out",
        str(store.root),
        "--registered-manifest",
        str(store.path("registration.json")),
        "--bfcl-completion",
        str(store.path("bfcl-completion.json")),
    ]
    loads = []
    ticks = [0.0]

    def fixture_clock():
        ticks[0] += 0.001
        return ticks[0]

    def load(tokenizer):
        loads.append(True)
        assert tokenizer is fake_backend.tokenizer
        return fake_backend

    # Selection/extraction must not even open test bytes until the run stage.
    original_open = Path.open

    def test_guard(path, *args, **kwargs):
        if path == store.path("test.json"):
            raise AssertionError("test contents opened before freeze")
        return original_open(path, *args, **kwargs)

    with monkeypatch.context() as m:
        m.setattr(Path, "open", test_guard)
        for mode in (["setup", "--timing-smoke"], ["setup"], ["extract"], ["select"]):
            result = cli.main(
                mode + common,
                backend_factory=load,
                tokenizer_factory=lambda: fake_backend.tokenizer,
                clock=fixture_clock,
            )
            assert result.get("stage_state") == "READY", result
    assert len(loads) == 4
    assert store.read("select.json")["certification"]["decisions"] == 512
    result = cli.main(
        ["run", *common],
        backend_factory=load,
        tokenizer_factory=lambda: fake_backend.tokenizer,
        clock=fixture_clock,
    )
    assert result["state"] == "PASS", result
    assert result["counts"]["S"] == result["counts"]["W"] == 64
    records = store.read_log("run")
    assert sum(r["kind"] == "answer" for r in records) == 1472
    assert sum(r["kind"] == "pair" for r in records) == 128
    assert not any(r.get("arm") in ("transplant", "sham") for r in records)
    assert f.allocation_state(store)[0] > 0
    result = cli.main(["analyze", "--out", str(store.root)])
    assert result["state"] == "PASS", result
    assert len(loads) == 5
    assert cli.main(["run", *common], backend_factory=load)["state"] == "INVALID"
    assert len(loads) == 5
    # Missing/tampered persisted outcomes cannot become PASS under analysis.
    path = store.path("run.jsonl")
    saved = path.read_bytes()
    path.write_bytes(saved.rsplit(b"\n", 2)[0] + b"\n")
    assert cli.main(["analyze", "--out", str(store.root)])["state"] == "INVALID"
    path.write_bytes(saved)
    final = store.read("run.json")
    store.path("run.json").unlink()
    assert cli.main(["analyze", "--out", str(store.root)])["state"] == "INCOMPLETE"
    store.write("run.json", final)
    # Exact bank/code hashes are consumed after freeze, including test bytes.
    test_file = store.path("test.json")
    test_file.write_bytes(test_file.read_bytes() + b" ")
    assert cli.main(["analyze", "--out", str(store.root)])["state"] == "INVALID"
    capsys.readouterr()


@pytest.mark.parametrize(
    "defect", ("draft", "hash", "deltas", "bfcl", "code", "layout", "seed", "review")
)
def test_evidence_defects_refuse_before_loading(
    tmp_path, fake_backend, monkeypatch, defect
):
    cli = cli_module()
    store = registered_fixture(tmp_path, monkeypatch, fake_backend.tokenizer)
    reg = store.read("registration.json")
    if defect == "draft":
        reg["status"] = "DRAFT"
    elif defect == "hash":
        del reg["reviewed_section_sha256"]
    elif defect == "deltas":
        reg["textual_deltas"] = []
    elif defect == "review":
        reg["review"]["open_high"] = 1
    elif defect == "bfcl":
        store.path("bfcl-completion.json").write_text("{}")
    elif defect == "code":
        monkeypatch.setattr(f, "fingerprints", lambda: {"changed": "c" * 64})
    else:
        bank = store.read("setup.json")
        if defect == "layout":
            bank["layouts"]["0"]["sort0"]["main"]["ids"][-1] += 1
        else:
            bank["rows"][0]["lists"]["sort0"][0] += 1
        store.path("setup.json").write_bytes(f.canonical(bank))
    store.path("registration.json").write_bytes(f.canonical(reg))
    result = cli.main(
        [
            "setup",
            "--timing-smoke",
            "--out",
            str(store.root),
            "--registered-manifest",
            str(store.path("registration.json")),
            "--bfcl-completion",
            str(store.path("bfcl-completion.json")),
        ]
    )
    assert result["state"] == "INVALID"


def test_selection_sort_short_circuit_no_keep(tmp_path, fake_backend):
    rows = f.generate_banks()["setup"]
    bad = [row["lists"]["sort0"] for row in rows[:4]]
    fake_backend.model.policy = lambda v, c, a, r, t, out: (
        [0] * len(v) if v in bad else out
    )
    engine = engine_for(tmp_path, fake_backend, "select")
    vectors = {"12": {t: v.tolist() for t, v in directions().items()}}
    result = f.selection(
        engine, rows, {"vectors": vectors, "stats": {"12": {"cosine": 0}}}
    )
    assert result["state"] == "FAIL-ACTUATOR"
    assert len(engine.rows) == 12  # fourth wrong sort abandons each available cell
    assert all(r["arm"] == "correct" for r in engine.rows)
    assert len(result["cells"]) == 9


def test_certification_mismatch_is_invalid_without_next_cell(
    tmp_path, fake_backend, monkeypatch
):
    rows = f.generate_banks()["setup"]
    store = f.Store(tmp_path)
    for name in (
        "bank",
        "registration",
        "bfcl-completion",
        "timing",
        "competence",
        "extract",
    ):
        store.write(name + ".json", {})
    engine = f.Engine(fake_backend, store, "select", {})
    original = engine.answer

    def disagree(*args, **kwargs):
        record, logits = original(*args, **kwargs)
        if record["arm"] == "transplant":
            record["output"]["tokens"][0] += 1
        return record, logits

    monkeypatch.setattr(engine, "answer", disagree)
    with pytest.raises(f.Invalid, match="no next-cell rescue"):
        f.selection(
            engine,
            rows,
            {
                "vectors": {"12": {t: v.tolist() for t, v in directions().items()}},
                "stats": {"12": {"cosine": 0}},
            },
        )
    assert len([r for r in engine.rows if r.get("arm") == "transplant"]) == 1


def test_interruption_charge_no_resumption(tmp_path):
    store = f.Store(tmp_path)
    store.append(
        "allocation",
        dict(attempt_id="run:start", kind="start", stage="run", wall_time=100),
    )
    spent, active = f.allocation_state(store, now=700)
    assert spent == 600 and active["stage"] == "run"
    assert f.allocation_state(store, now=900)[0] == 800


def test_maximum_costs_survive_modes_and_clock(tmp_path):
    store = f.Store(tmp_path)
    store.append(
        "allocation",
        dict(attempt_id="timing:end", kind="end", stage="timing", rates={"keep": 4.0}),
    )
    store.append(
        "allocation",
        dict(
            attempt_id="competence:end",
            kind="end",
            stage="competence",
            rates={"keep": 0.1, "load": 5.0},
        ),
    )
    rates = f.cumulative_rates(store, dict.fromkeys(f.COST_CLASSES, 1.0))
    assert rates["keep"] == 4 and rates["load"] == 5
    clock = [100.0]
    budget = f.Budget(10, rates, clock=lambda: clock[0])
    assert budget.project({"keep": 2}, reloads=2) == 10 + 10 + 1.25 * 2 * (4 + 2)
    clock[0] += 100
    assert budget.elapsed == 110
    budget.spent = f.CAP - 100
    with pytest.raises(f.Incomplete):
        budget.reserve({}, reloads=1, loading=True)


def test_exception_attempt_is_persisted_before_abort(tmp_path, fake_backend):
    engine = engine_for(tmp_path, fake_backend)
    row = f.generate_banks()["test"][0]

    class BrokenTrunk:
        def __call__(self, *args, **kwargs):
            raise RuntimeError("fixture infrastructure failure")

    fake_backend.model = BrokenTrunk()
    ids = f.layout(fake_backend.tokenizer, row["lists"]["sort0"])["ids"]
    with pytest.raises(f.Incomplete, match="infrastructure"):
        engine.answer(row, "SET", "OFF", fake_backend.empty(), ids, task="OFF")
    attempts, records = engine.store.read_log("attempts"), engine.store.read_log("run")
    assert attempts[0]["attempt_id"] == records[0]["attempt_id"]
    assert "infrastructure failure" in records[0]["output"]["exception"]


def test_extraction_failure_preserves_attempt_and_exception(tmp_path, fake_backend):
    engine = engine_for(tmp_path, fake_backend, "extract")

    class BrokenCapture:
        def __call__(self, *args, **kwargs):
            raise RuntimeError("capture fixture failed")

    fake_backend.model = BrokenCapture()
    with pytest.raises(f.Incomplete, match="capture fixture failed"):
        f.extract_vectors(engine, f.generate_banks()["extraction"])
    attempt = engine.store.read_log("attempts")[0]
    record = engine.store.read_log("extract")[0]
    assert attempt["attempt_id"] == record["attempt_id"]
    assert "capture fixture failed" in record["exception"]
    assert record["layer_inputs"] is None


def test_partial_stratum_failure_stops_before_remaining_decisions():
    rows = [
        dict(
            kind="answer",
            arm="correct",
            episode=2 * i,
            initial="A",
            phase="SET",
            score=dict(broken=False, recipient=False, imposition=False),
        )
        for i in range(9)
    ]
    assert "stratum" in f.impossible(rows)


def test_competence_schema_floor_cpu(tmp_path, fake_backend):
    rows = f.generate_banks()["setup"]
    failed = [r["lists"]["sort0"] for r in rows[:2]]

    def policy(values, copy, active, residual, text, answer):
        current = text.rsplit(f.USER, 1)[-1]
        return [] if current.startswith("Process") and values in failed else answer

    fake_backend.model.policy = policy
    result = f.competence(engine_for(tmp_path, fake_backend, "competence"), rows)
    assert result["state"] == "INELIGIBLE"
    assert result["tasks"]["A"]["visible"] == result["tasks"]["B"]["visible"] == 32
    assert result["tasks"]["A"]["schema"] == result["tasks"]["B"]["schema"] == 30


def test_selection_joint_pair_floor_abandons_before_keep(tmp_path, fake_backend):
    rows = f.generate_banks()["setup"]
    failed = [r["lists"]["copy1"] for r in rows[:2]]
    fake_backend.model.policy = lambda v, c, a, r, t, out: (
        [0] * len(v) if c and v in failed else out
    )
    engine = engine_for(tmp_path, fake_backend, "select")
    result = f.selection(
        engine,
        rows,
        {
            "vectors": {"12": {t: v.tolist() for t, v in directions().items()}},
            "stats": {"12": {"cosine": 0}},
        },
    )
    assert result["state"] == "FAIL-ACTUATOR"
    assert not any(r.get("arm") == "KEEP" for r in engine.rows)
    cells = [c for c in result["cells"] if c["state"] == "REJECTED"]
    assert all(c["tasks"]["A"]["neutral_n"] == 2 for c in cells)
    assert all(
        c["tasks"]["A"]["harm"] == 0 for c in cells
    )  # shared errors still fail joint setup floor


def test_impossible_safety_only_interventions():
    for arm in f.TEST_ARMS:
        records = [
            dict(
                kind="answer",
                episode=i,
                arm=arm,
                phase="SET"
                if arm in f.MAIN_ARMS
                else "HOLD"
                if arm == "transient"
                else "copy0",
                initial="A",
                score=dict(broken=True, imposition=False),
            )
            for i in (0, 1)
        ]
        assert bool(f.impossible(records)) == (arm in f.INTERVENTIONS)


def test_hash_schema_audit_rejects_nonvacuous_fake_tampering(tmp_path, fake_backend):
    row = f.generate_banks()["test"][0]
    engine = engine_for(tmp_path, fake_backend)
    _, histories = engine.main_decisions(row, directions(), 1, 12)
    engine.transient(row, histories["SET"], 12)
    engine.neutral(row, histories["BACK"], directions(), 1, 12)
    layouts = f.bank_layouts(fake_backend.tokenizer, [row])
    selected = {"selected": {"alpha": 1, "layer": 12}}
    f.validate_run_records(engine.rows, [row], layouts, selected, {"fixture": "only"})
    import copy

    for defect in ("history", "hook", "residual", "operands", "final", "pair"):
        records = copy.deepcopy(engine.rows)
        clear = next(r for r in records if r.get("arm") == "CLEAR")
        if defect == "history":
            clear["output"]["history_before"] = []
        elif defect == "hook":
            next(r for r in records if r.get("arm") == "correct")["output"][
                "hook_events"
            ] = []
        elif defect == "residual":
            clear["comparison"]["kv_deltas"][12]["k"] = 0
        elif defect == "operands":
            clear["inputs"][0] += 1
        elif defect == "final":
            clear["output"]["history_after"].pop()
        else:
            next(r for r in records if r["kind"] == "pair")["first_logit_delta"] = None
        with pytest.raises(f.Invalid):
            f.validate_run_records(
                records, [row], layouts, selected, {"fixture": "only"}
            )
