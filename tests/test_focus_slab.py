"""SLAB CPU contracts; evaluation content is never printed or snapshotted."""

import json
from dataclasses import asdict
from pathlib import Path

import pytest

from stencil.focus.register import Register
from stencil.focus.slab import (
    DOMAINS,
    Executor,
    InvalidProgram,
    bank,
    check,
    digest,
    dry_run,
    evaluate,
    generate_episode,
    materialize,
    mutants,
    reference,
    write_manifests,
)

FIXTURES = Path(__file__).parent / "fixtures"


def test_determinism_disjointness_and_pressure_structure():
    dev, evaluation = bank(), bank("eval")
    assert [e.manifest() for e in dev] == [e.manifest() for e in bank()]
    assert len(dev) >= 8 and len(evaluation) == 64
    assert [len(e.turns) for e in evaluation].count(16) == 48
    assert [len(e.turns) for e in evaluation].count(32) == 16
    assert {e.seed for e in dev}.isdisjoint(e.seed for e in evaluation)
    assert {e.template_id for e in dev}.isdisjoint(e.template_id for e in evaluation)
    assert {e.domain for e in dev} == set(DOMAINS)
    assert digest(asdict(dev[0])) != digest(asdict(generate_episode(seed=17)))
    for e in (*dev, *evaluation):
        state = Register(defaults=e.defaults, task_handles={"A", "B"})
        events = []
        switches = sum(
            a.task != b.task for a, b in zip(e.turns, e.turns[1:], strict=False)
        )
        assert 2 <= switches <= 3
        assert any(t.task == "A" for t in e.turns[5:])
        for t in e.turns:
            state = state.apply(t.events)
            assert {
                v.entry.key: v.entry.value for v in state.live(t.task, "tool_call")
            } == dict(t.live)
            assert 3 <= len(t.live) <= 5
            assert dict(t.live)["indent"] in {"2", "4"}
            assert all(f"{k}={v}" in t.t_text for k, v in t.live)
            if t.index < 10:
                assert not t.retired
            assert not any(x == t.public_case for x, _ in e.private[t.index]["cases"])
            events.extend(t.events)
        assert {"supersedes", "cancels", "completes", "reinstates"} <= {
            x.action for x in events
        }
        assert any(dict(t.denominators)["style"] for t in e.turns)
        assert any(dict(t.denominators)["format"] for t in e.turns)
        assert any(dict(t.denominators)["process"] for t in e.turns)
        assert "private" not in e.public_view()
        assert all("expression" not in t for t in e.public_view()["turns"])


@pytest.mark.parametrize(
    "family,index", [("dev", i) for i in range(8)] + [("eval", i) for i in range(64)]
)
def test_every_reference_and_mutant_witness(tmp_path, family, index):
    e = generate_episode(family, index)
    # CPU checker audit is authorized; no evaluation content is sent to a decoder.
    materialize(e, tmp_path, e.manifest()["episode_sha256"])
    executor = Executor(
        tmp_path, json.loads((tmp_path / "public_tests.json").read_text())
    )
    seen = set()
    for i, _t in enumerate(e.turns):
        before = {p: (tmp_path / p).read_text() for p in ("core.py", "policy.py")}
        for label, output in mutants(e, i).items():
            for p, content in before.items():
                (tmp_path / p).write_text(content)
            executor.run(output)
            result = check(e, i, output, executor)
            group, kind = (
                ("relapse", label.split(":")[1])
                if ":" in label
                else ("violations", label)
            )
            if label == "hidden_only":
                kind = "semantic"
                assert executor.results[-1]["failed"] == 0
                assert executor.results[-1]["passed"] == i + 1
            assert result[group][kind], (e.episode_id, i, label)
            assert not result["success"]
            seen.add(label)
        for p, content in before.items():
            (tmp_path / p).write_text(content)
        output = reference(e, i)
        feedback = executor.run(output)
        result = check(e, i, output, executor)
        assert result["success"], (e.episode_id, i, result)
        assert len(feedback["executed"]) == 3
        assert feedback["results"][-1]["passed"] == i + 1
        assert not any(result["relapse"].values())
    assert {"relapse:style", "relapse:format", "relapse:process"} <= seen
    assert result["integration"]


def test_manifest_hashes(tmp_path):
    receipt = write_manifests(tmp_path)
    frozen = json.loads((FIXTURES / "slab_manifest.json").read_text())
    assert receipt == frozen
    assert receipt == json.loads((tmp_path / "slab_manifest.json").read_text())
    assert len(receipt["oracle_text_subset"]) == 16
    # Stratify by domain as well as episode length, not index modulo four.
    subset = receipt["oracle_text_subset"]
    assert len(set(subset)) == 16
    chosen = [e for e in bank("eval") if e.episode_id in subset]
    assert {e.domain for e in chosen} == set(DOMAINS)
    assert {len(e.turns) for e in chosen} == {16, 32}
    for family in ("dev", "eval"):
        for e, manifest in zip(bank(family), receipt["banks"][family], strict=False):
            assert manifest["episode_sha256"] == digest(asdict(e))
            assert manifest["public_sha256"] == digest(e.public_view())
            assert manifest["hidden_sha256"] == digest(e.private)


def test_dev_loop_dry_run(tmp_path):
    result = dry_run(tmp_path)
    frozen = json.loads((FIXTURES / "slab_dev_golden.json").read_text())
    for key in ("accounting", "rendered_sha256", "events_sha256", "final_hashes"):
        assert result[key] == frozen[key]
    rows = [json.loads(x) for x in (tmp_path / "loop.jsonl").read_text().splitlines()]
    checks = [
        json.loads(x) for x in (tmp_path / "checker.jsonl").read_text().splitlines()
    ]
    assert len(rows) == len(checks) == 16
    for i, (row, checker) in enumerate(zip(rows, checks, strict=False)):
        assert row["request_id"] == i
        assert checker["outcome"]["success"]
        assert row["attempted_tool_calls"] == checker["executed"]["executed"]
        assert row["executed_tool_calls"] == (
            checks[i - 1]["executed"]["executed"] if i else []
        )
        assert row["tool_results"] == (
            checks[i - 1]["executed"]["results"] if i else []
        )
        assert row["gpu_held_seconds"] == 0
    assert result["model_cost_projection"] is None
    assert result["tokenizer"] == "utf8-byte-stub"
    assert result["accounting"][-1]["prompt"] > result["accounting"][0]["prompt"]
    with pytest.raises(ValueError, match="DEV only"):
        dry_run(tmp_path / "eval", generate_episode("eval"))


def test_fail_closed_bounds_scope_receipts_and_missingness(tmp_path):
    e = generate_episode()
    with pytest.raises(ValueError, match="freeze"):
        materialize(generate_episode("eval"), tmp_path)
    materialize(e, tmp_path)
    ex = Executor(tmp_path, json.loads((tmp_path / "public_tests.json").read_text()))
    malformed = json.loads(reference(e, 0))
    malformed["calls"][1]["path"] = "../escape.py"
    ex.run(json.dumps(malformed))
    assert check(e, 0, json.dumps(malformed), ex)["violations"]["breakage"]
    assert not (tmp_path.parent / "escape.py").exists()
    ex.run(reference(e, 0))
    # A receipt from a different workspace state cannot authorize delivery.
    (tmp_path / "policy.py").write_text("# tampered\n")
    assert check(e, 0, reference(e, 0), ex)["violations"]["process"]
    missing = check(e, 12, "", ex, executed=False)
    assert missing["relapse"] is None and not missing["observed"]
    assert missing["denominators"]["process"] == 1
    for code in (
        "import os",
        'def f(x):\n    return __import__("os")',
        "def f(x):\n    while True: pass",
        "def f(x):\n    return x.__class__",
        "def f(x):\n    return 2 ** 999999999",
        "def f(x):\n    return [v for v in x]",
    ):
        with pytest.raises(InvalidProgram):
            evaluate(code, "f", list(range(65)))


def test_paired_clauses_have_no_absolute_floor_and_do_not_reward_missingness():
    import copy

    from stencil.focus.slab import paired_clauses

    # R40/N12 is informative despite both missing the old absolute product floor.
    clean = dict(
        observed=True,
        denominators=dict(language=0, style=1, format=0, process=0),
        relapse=dict(language=False, style=False, format=False, process=False),
        violations=dict(breakage=False),
        success=True,
    )
    r = [[copy.deepcopy(clean) for _ in range(16 if i < 48 else 32)] for i in range(64)]
    n = copy.deepcopy(r)
    for i in range(64):
        r[i][-1]["success"] = i < 40
        n[i][-1]["success"] = i < 12
    result = paired_clauses(r, n)
    assert result["clauses_pass"] and result["gain"] == 28
    n[0][11].update(observed=False, relapse=None, violations=None)
    result = paired_clauses(r, n)
    assert not result["complete"] and not result["clauses_pass"]
    assert result["common_opportunities"]["style"]["missing"] == 1
    n[0][11] = copy.deepcopy(clean)
    r[0][11]["relapse"]["style"] = True
    assert not paired_clauses(r, n)["relapse_clause"]
    r[0][11]["relapse"]["style"] = False
    r[0][1]["violations"]["breakage"] = True
    assert paired_clauses(r, n)["breakage_clause"]
    r[1][1]["violations"]["breakage"] = True
    assert not paired_clauses(r, n)["breakage_clause"]
