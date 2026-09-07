"""SLAB-2 consumer tests; authored synthetic episodes, no benchmark data."""

import copy
import json
from pathlib import Path

import pytest

from stencil.focus import slab2 as s

FIXTURES = Path(__file__).parent / "fixtures"


def setup(tmp_path, episode):
    s.materialize(episode, tmp_path, episode.manifest()["episode_sha256"])
    return s.Executor(tmp_path, episode)


@pytest.mark.parametrize(
    "family,index", [("dev", i) for i in range(8)] + [("eval", i) for i in range(64)]
)
def test_reference_real_path(tmp_path, family, index):
    e = s.generate_episode(family, index)
    ex = setup(tmp_path, e)
    assert len(e.turns) == 16
    assert {x.action for t in e.turns for x in t.events} >= {
        "supersedes",
        "cancels",
        "completes",
        "reinstates",
    }
    for i, _t in enumerate(e.turns):
        result = ex.run(s.reference(e, i), i)
        assert result["passed"] == i + 1 and not result["failed"]
        assert len(s.qwen_encode(s.reference(e, i))) <= s.REPLY_CAP
        assert s.check(e, i, ex, eligible_traits=tuple(s.TRAITS))["success"]
        assert "result =" not in json.dumps(result)


@pytest.mark.parametrize("index", range(8))
def test_mutants_and_should_pass(tmp_path, index):
    e = s.generate_episode("dev", index)
    ex = setup(tmp_path, e)
    seen = set()
    for i in range(16):
        before = {p: (tmp_path / p).read_text() for p, _ in e.initial}
        snapshots = copy.deepcopy(ex.last_parsable)
        history = copy.deepcopy(ex.history)

        def restore(before=before, snapshots=snapshots, history=history):
            for p, c in before.items():
                (tmp_path / p).write_text(c)
            ex.last_parsable = copy.deepcopy(snapshots)
            ex.history = copy.deepcopy(history)

        for label, output in s.mutants(e, i).items():
            restore()
            ex.run(output, i)
            outcome = s.check(e, i, ex, eligible_traits=tuple(s.TRAITS))
            witness = "semantic" if label == "hidden_only" else label
            assert outcome["diagnostics"][witness], (index, i, label, outcome)
            if label == "hidden_only":
                assert ex.result["passed"] == i + 1 and ex.result["failed"] == 0
            trait = "indent" if label == "indent" else label
            if (
                trait in s.TRAITS
                and outcome["trait_denominators"][trait]
                and outcome["prior_trait_present"][trait]
            ):
                assert outcome["raw_relapse"][trait]
            assert not outcome["success"]
            seen.add(label)
        for output in s.should_pass(e, i).values():
            restore()
            ex.run(output, i)
            assert s.check(e, i, ex, eligible_traits=tuple(s.TRAITS))["success"]
        restore()
        ex.run(s.reference(e, i), i)
    assert {
        "indent",
        "delivery",
        "format",
        "breakage",
        "wrong_family",
        "semantic",
    } <= seen


def test_free_reemission_and_parsable_repair(tmp_path):
    e = s.generate_episode()
    ex = setup(tmp_path, e)
    for i in range(14):
        output = s.reference(e, i)
        ex.run(output, i)
    ex.run(output, 13)
    assert ex.changed == ""
    assert s.check(e, 13, ex, eligible_traits=tuple(s.TRAITS))["success"]
    ex.run("```python\ndef broken(:\n```\nreport: task=A status=ok", 14)
    ex.run(s.reference(e, 14), 14)
    assert "step_14" in ex.changed and "step_13" not in ex.changed
    assert s.check(e, 14, ex, eligible_traits=tuple(s.TRAITS))["success"]
    ex.run(s.reference(e, 15), 15, truncated=True)
    assert not ex.result["executed"] and ex.result["breakage"]


def test_fixtures(tmp_path):
    fixtures = json.loads((FIXTURES / "slab2_replies.json").read_text())
    assert len(fixtures) >= 18
    e = s.generate_episode()
    for row in fixtures:
        ex = setup(tmp_path, e)
        result = ex.run(row["reply"], 0)
        assert result["executed"] == row["executed"]
        assert result["breakage"] == row["breakage"]
        if "tolerances" in row:
            assert result["tolerances"] == row["tolerances"]


def test_manifest_disjointness_and_text_updater():
    receipt = json.loads((FIXTURES / "slab2_manifest.json").read_text())
    assert (
        receipt["source_sha256"]
        == s.hashlib.sha256(Path(s.__file__).read_bytes()).hexdigest()
    )
    dev, ev = s.bank(), s.bank("eval")
    assert {e.seed for e in dev}.isdisjoint(e.seed for e in ev)
    assert {e.template_id for e in dev}.isdisjoint(e.template_id for e in ev)
    for family, episodes in (("dev", dev), ("eval", ev)):
        assert [e.manifest() for e in episodes] == receipt["banks"][family]
        for e in episodes:
            for t in e.turns:
                for row in t.events:
                    assert s.literal(row.key, row.value) in row.text
                if family == "eval":

                    def fields(rows):
                        return [
                            (r.action, r.key, r.value, r.target_version, r.scope)
                            for r in rows
                        ]

                    assert fields(s.text_events(e, t.index)) == fields(t.events)


def floor_records():
    records = []
    for i in range(8):
        for j in range(16):
            records.append(
                dict(
                    episode_id=f"slab2-dev-{i:02}",
                    arm="T",
                    turn=j,
                    outcome=dict(
                        observed=True,
                        applicable={k: True for k in s.TRAITS},
                        satisfied={
                            k: k not in {"format", "delivery_scope"} for k in s.TRAITS
                        },
                        trait_denominators={k: int(j >= 10) for k in s.TRAITS},
                    ),
                )
            )
    return records


def test_floor_missingness_threshold_and_gate():
    records = floor_records()
    floor = s.freeze_t_floor(records)
    assert "format" not in floor["eligible_traits"]
    assert "delivery" in floor["eligible_traits"]
    for r in records[:64]:
        r["outcome"]["observed"] = False
    assert s.freeze_t_floor(records)["traits"]["indent"]["eligible"]
    records[64]["outcome"]["observed"] = False
    assert not s.freeze_t_floor(records)["traits"]["indent"]["eligible"]
    with pytest.raises(ValueError):
        s.freeze_t_floor(records[:-1])
    records[0]["episode_id"] = "slab2-eval-00"
    with pytest.raises(ValueError):
        s.freeze_t_floor(records)
    assert s.paired_context_gate(dict.fromkeys("RNTO", 32768 - s.REPLY_CAP))
    assert not s.paired_context_gate(dict(R=31745, N=1, T=1, O=1))
    with pytest.raises(ValueError):
        s.paired_context_gate(dict(R=1))
    assert s.measured_projection(dict.fromkeys("RNTO", 180), reserve=1) == 8
    assert s.pilot5_reading([], floor, 13)["cost_action"] == "12-round-refreeze"
    assert not s.pilot5_reading([], floor, None)["eligible"]


def test_excluded_trait_diagnostic_only(tmp_path):
    e = s.generate_episode()
    ex = setup(tmp_path, e)
    for i in range(16):
        ex.run(s.reference(e, i), i)
    output = s.reference(e, 15) + " delivery=stale"
    ex.run(output, 15)
    outcome = s.check(e, 15, ex, eligible_traits=("indent",))
    assert outcome["diagnostics"]["format"] and outcome["success"]
    assert "format" not in outcome["relapse"]


def test_frozen_full_audit():
    result = json.loads((FIXTURES / "slab2_cpu_audit.json").read_text())
    assert result["calls"] == 4608 and len(result["lanes"]) == 288
    assert s.paired_context_gate(result["max_context_per_arm"])
    for lane in result["lanes"]:
        assert len(lane["accounting"]) == 16
        assert lane["input_tokens"] == sum(r["prompt"] for r in lane["accounting"])
        assert lane["output_tokens"] == sum(r["generated"] for r in lane["accounting"])
    assert result["model_cost_projection"] is None


def test_pilot5_reading_uses_floor_for_final_success():
    floor = s.freeze_t_floor(floor_records())
    records = []
    for i in range(8):
        for arm in "RNT":
            for j in range(16):
                records.append(
                    dict(
                        episode_id=f"slab2-dev-{i:02}",
                        arm=arm,
                        turn=j,
                        truncated=False,
                        outcome=dict(
                            observed=True,
                            integration=True,
                            report_ok=True,
                            success=False,
                            diagnostics={
                                k: k == "format"
                                for k in (*s.TRAITS, "breakage", "wrong_family")
                            },
                        ),
                    )
                )
    assert s.pilot5_reading(records, floor, 12)["eligible"]
    assert not s.pilot5_reading(records, floor, 12.01)["eligible"]
    for row in records:
        if row["arm"] == "R" and row["turn"] == 15 and row["episode_id"][-2:] < "04":
            row["outcome"]["report_ok"] = False
    assert s.pilot5_reading(records, floor, 10)["r_final_success"] == 4
    assert not s.pilot5_reading(records, floor, 10)["eligible"]


def test_compact_floor_cannot_borrow_verbose_success(tmp_path):
    e = s.generate_episode()
    ex = setup(tmp_path, e)
    for i, t in enumerate(e.turns):
        output = s.reference(e, i)
        if dict(t.live)["format"] == "compact":
            output += " delivery=stale"
        ex.run(output, i)
        outcome = s.check(e, i, ex)
        assert outcome["floor_pending"] and outcome["success"] is None
        assert outcome["applicable"]["format"] == (dict(t.live)["format"] == "compact")
        if outcome["applicable"]["format"]:
            assert not outcome["satisfied"]["format"]


def test_paired_scoring_preserves_missingness():
    clean = dict(
        observed=True,
        integration=True,
        report_ok=True,
        diagnostics={k: False for k in (*s.TRAITS, "breakage", "wrong_family")},
        trait_denominators={k: int(k == "indent") for k in s.TRAITS},
        raw_relapse={k: False for k in s.TRAITS},
    )
    r = [[copy.deepcopy(clean) for _ in range(16)] for _ in range(64)]
    n = copy.deepcopy(r)
    for lane in n[:8]:
        lane[-1]["integration"] = False
    assert s.paired_clauses(r, n, ("indent",))["clauses_pass"]
    r[0][10]["observed"] = False
    result = s.paired_clauses(r, n, ("indent",))
    assert not result["clauses_pass"]
    assert result["common_opportunities"]["style"]["missing"] == 1


def test_cross_file_syntax_recovery(tmp_path):
    e = s.generate_episode()
    ex = setup(tmp_path, e)
    for i in range(2):
        ex.run(s.reference(e, i), i)
    path = e.turns[2].path
    before = (tmp_path / path).read_bytes()
    broken = s.reference(e, 2).replace("def step_2(x):", "def step_2(:")
    result = ex.run(broken, 2)
    assert result["executed"] and result["breakage"]
    assert path in result["error"] and "line " in result["error"]
    assert (tmp_path / path).read_bytes() == before
    assert (tmp_path / path).read_text() == ex.last_parsable[path]
    assert e.turns[3].path != path
    ex.run(s.reference(e, 3), 3)
    outcome = s.check(e, 3, ex)
    assert not outcome["diagnostics"]["breakage"]
    assert not outcome["diagnostics"]["wrong_family"]
    repaired = False
    for i in range(4, 16):
        ex.run(s.reference(e, i), i)
        outcome = s.check(e, i, ex, eligible_traits=tuple(s.TRAITS))
        assert not outcome["diagnostics"]["wrong_family"]
        repaired |= e.turns[i].path == path
        if repaired:
            assert outcome["success"]
    assert repaired


@pytest.mark.parametrize("n_rounds", [12, 16])
def test_delivery_power_and_fallback(tmp_path, n_rounds):
    counts = {}
    for family in ("dev", "eval"):
        opportunities = []
        for e in s.bank(family, n_rounds=n_rounds):
            opportunities.append(
                sum(
                    "delivery" in dict(t.retired)
                    and dict(t.live)["format"] == "verbose"
                    and "delivery" in dict(t.live)
                    for t in e.turns
                )
            )
        counts[family] = sum(bool(n) for n in opportunities)
    assert counts["dev"] >= 7 and counts["eval"] >= 56
    lane = s.dry_run(
        tmp_path, s.generate_episode(n_rounds=n_rounds), "R", n_rounds=n_rounds
    )
    assert len(lane["records"]) == n_rounds
    assert all(row["outcome"]["success"] for row in lane["records"])
    outcomes = [[row["outcome"] for row in lane["records"]] for _ in range(64)]
    assert s.paired_clauses(
        outcomes, outcomes, ("indent", "delivery"), n_rounds=n_rounds
    )["complete"]
    with pytest.raises(ValueError):
        s.generate_episode(n_rounds=14)


def test_cost_concurrency_and_schedule_rule():
    assert s.measured_projection(dict.fromkeys("RNTO", 180), reserve=1) == 8
    with pytest.raises(ValueError):
        s.measured_projection(dict.fromkeys("RNTO", 180), max_workers=1)
    floor = s.freeze_t_floor(floor_records())
    assert s.pilot5_reading([], floor, 12)["cost_action"] == "16-round"
    assert s.pilot5_reading([], floor, 15)["cost_action"] == "12-round-refreeze"
    assert s.pilot5_reading([], floor, 15.01)["cost_action"] == "stop"
    assert s.pilot5_reading([], floor, 13, n_rounds=12)["cost_action"] == "stop"


@pytest.mark.parametrize(
    "reply,category",
    [
        (
            "```python\ndef f(): pass\n```\nreport: task=A status=ok extra=x",
            "trailer_key_or_value",
        ),
        (
            "```python\ndef f(): pass\n```\nreport: task=A task=A status=ok",
            "duplicate_key",
        ),
        ("```python\nreport: task=A status=ok\n```", "misplaced_trailer"),
        (
            "```python\ndef f(): pass\n```\nreport: task=A status=ok\n"
            "```python\nx=1\n```",
            "fence_count_or_kind",
        ),
        ("~~~~python\nx=1\n~~~~\nreport: task=A status=ok", "fence_count_or_kind"),
        ("```js\nx=1\n```\nreport: task=A status=ok", "fence_syntax"),
        ('```python\nx=1\n```\n{"task":"A","status":"ok"}', "trailer_count"),
    ],
)
def test_parser_breakage_categories(tmp_path, reply, category):
    e = s.generate_episode()
    ex = setup(tmp_path, e)
    result = ex.run(reply, 0)
    assert result["breakage"] and not result["executed"]
    assert result["category"] == category


def test_prompt_cap_registration():
    assert s.REPLY_CAP == 2048
    assert "2048" in s.SYSTEM_PROMPT
    for e in s.bank():
        assert all("short one-line docstring" in t.request for t in e.turns)


def test_sensitivity_table_arithmetic():
    table = s.cost_table(594408)
    assert [row["reserved_hours"] for row in table] == pytest.approx(
        [9.067049032838508, 19.473989898989903, 11.991627305443096]
    )
