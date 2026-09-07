"""Amendment 4 controls use saved DEV registers, not regenerated replacements."""

import copy
import json
from dataclasses import asdict, replace
from pathlib import Path

import pytest

from stencil.focus import slab2 as s
from stencil.focus import slab2_endpoint as ep
from stencil.focus.register import Entry, Evidence, Register, Scope, Source
from stencil.focus.renderer import Request, render

FIXTURE = Path(__file__).parent / "fixtures/slab2_pilot6_registers.json"


def entry(d):
    return Entry(
        **{
            **d,
            "scope": Scope(**d["scope"]),
            "source": Source(**d["source"]),
            "evidence": Evidence(**d["evidence"]) if d["evidence"] else None,
        }
    )


def saved_register(row):
    j = row["saved"]
    return Register.replay(
        tuple(entry(e) for e in j["register_events"]),
        defaults=tuple(entry(e) for e in j["defaults"]),
        task_handles={"A", "B"},
        event_generations=j["event_generations"],
        generation=row["turn"],
    )


def test_saved_34_compact_control_and_all35():
    rows = json.loads(FIXTURE.read_text())["rows"]
    assert len(rows) == 35 and sum(r["matched"] for r in rows) == 34
    for row in rows:
        assert "trailer delivery=ready" in json.dumps(row["old_rendered"])
        reg = saved_register(row)
        request = Request("", **row["saved"]["request_bindings"])
        before = asdict(reg)
        # Reconstructed state must equal the saved state, not just the new block.
        assert (
            json.loads(json.dumps([asdict(v) for v in reg.versions]))
            == row["saved"]["after_versions"]
        )
        assert (
            json.loads(
                json.dumps(
                    [asdict(v) for v in reg.live(request.task_handle, request.kind)]
                )
            )
            == row["saved"]["applicability"]
        )
        result = render(reg, request)
        live_rows = json.loads(result.text.splitlines()[1])
        assert all(v["key"] != "delivery" for v in live_rows)
        assert "trailer delivery=" not in result.text
        assert all("scope" not in v and "provenance" not in v for v in live_rows)
        assert (
            next(v for v in live_rows if v["key"] == "indent")["text"].count(
                "block bodies indented"
            )
            == 1
        )
        assert "replaced by" not in result.text and "reinstated as" not in result.text
        assert asdict(reg) == before
        assert render(reg, replace(request, rule_mode="O")).envelope == result.envelope


def test_composition_preserves_literal_and_scope():
    e = s.generate_episode()
    reg = Register(defaults=e.defaults, task_handles={"A", "B"}).apply(
        e.turns[0].events
    )
    task = next(x.scope.task_handle for x in e.defaults if x.key == "delivery")
    for fmt in ("compact", "verbose", "COMPACT"):
        # Test value literalness without mutating or parsing rule prose.
        defaults = tuple(
            replace(x, value=fmt)
            if x.key == "format"
            else replace(
                x, value="arbitrary-literal", text="trailer delivery=arbitrary-literal"
            )
            for x in e.defaults
        )
        r = Register(defaults=defaults, task_handles={"A", "B"})
        out = render(r, Request("", "tool_call", task))
        assert ("trailer delivery=arbitrary-literal" in out.text) == (fmt != "compact")
        other = "B" if task == "A" else "A"
        assert (
            "trailer delivery=" not in render(r, Request("", "tool_call", other)).text
        )
    assert "delivery" in {v.entry.key for v in reg.live(task, "tool_call")}


def test_breakage_independent_and_empty_widths(tmp_path):
    e = s.generate_episode()
    s.materialize(e, tmp_path)
    ex = s.Executor(tmp_path, e)
    output = s.reference(e, 0).replace(e.private[0]["expression"], "unknown(x)")
    ex.run(output, 0)
    out = s.check(e, 0, ex)
    assert ex.result["breakage"]
    assert out["satisfied"]["language"] and out["satisfied"]["indent"]
    assert out["diagnostics"]["breakage"]
    assert (
        set(out["satisfied"])
        == set(s.TRAITS)
        == {"language", "indent", "format", "delivery"}
    )
    ex.run(output, 0)
    assert ex.changed == "" and not s.check(e, 0, ex)["satisfied"]["indent"]
    ex.run("```python\ndef invalid(:\n```\nreport: task=A status=ok", 0)
    assert not s.check(e, 0, ex)["satisfied"]["language"]


def synthetic():
    episodes = s.bank()
    records = []
    for e in episodes:
        for a in ep.ARMS:
            for t in e.turns:
                live = dict(t.live)
                records.append(
                    dict(
                        episode_id=e.episode_id,
                        arm=a,
                        turn=t.index,
                        output="report: task=A status=ok",
                        truncated=False,
                        prompt_tokens=100,
                        execution=dict(executed=True),
                        outcome=dict(
                            observed=True,
                            applicable=dict(
                                language=True,
                                indent=True,
                                format=live["format"] == "compact",
                                delivery=live["format"] == "verbose"
                                and "delivery" in live,
                            ),
                            satisfied={k: a != "N" for k in s.TRAITS},
                            trait_denominators={
                                k: int(k in dict(t.retired)) for k in s.TRAITS
                            },
                            integration=False,
                            report_ok=True,
                            diagnostics=dict(breakage=True),
                        ),
                    )
                )
    return episodes, records


def test_episode_pairing_holm_missingness_and_zero():
    episodes, rows = synthetic()
    result = ep.primary(rows, episodes)
    for k, f in result["families"].items():
        assert f["n"] == f["wins"] == 8 and f["losses"] == 0
        assert f["p"] == 1 / 256 and f["holm_p"] == 3 / 256 and f["pass"]
        assert all(
            len(e["change_rounds"]) == (2 if k == "indent" else 1)
            for e in f["episodes"]
        )
    changed = copy.deepcopy(rows)
    # Removing one change write affects that event, not the next round.
    turn = ep.change_rounds(episodes[0])["indent"][0]
    next(
        r
        for r in changed
        if r["arm"] == "R"
        and r["episode_id"] == episodes[0].episode_id
        and r["turn"] == turn
    )["execution"]["executed"] = False
    f = ep.primary(changed, episodes)["families"]["indent"]
    assert f["episodes"][0]["paired_denominator"] == 1
    assert f["episodes"][0]["missing_paired_rounds"] == [turn]
    assert f["strict_failed_attempts"]["mean_gain"] < f["mean_gain"]
    for r in changed:
        r["outcome"]["satisfied"] = dict.fromkeys(s.TRAITS, True)
    assert all(
        f["p"] == 1 and not f["pass"]
        for f in ep.primary(changed, episodes)["families"].values()
    )
    assert ep.primary([], episodes)["computable_families"] == 0
    with pytest.raises(ValueError):
        ep.primary(rows + [rows[0]], episodes)


def test_pilot_gates_ignore_joint_final_and_charge_q_without_o():
    episodes, rows = synthetic()
    cells = {
        (r["episode_id"], r["turn"])
        for r in json.loads(FIXTURE.read_text())["rows"]
        if r["matched"]
    }
    floor = ep.strict_floor(rows)
    result = ep.pilot_reading(rows, episodes, floor, 7, cells, deterministic=True)
    assert result["reading"] == "ELIGIBLE"  # all integration/breakage checks fail
    assert (
        ep.projection(dict.fromkeys(ep.ARMS, 100), 500) == (500 + 1.25 * 20800) / 3600
    )
    with pytest.raises(ValueError):
        ep.projection(dict.fromkeys("RNTO", 100), 500)
    selected = [
        r for r in rows if r["arm"] == "R" and (r["episode_id"], r["turn"]) in cells
    ]
    for r in selected[:3]:
        r["output"] += " delivery=ready"
    assert (
        ep.pilot_reading(rows, episodes, floor, 7, cells, deterministic=True)["reading"]
        == "INELIGIBLE"
    )
    for r in selected[:9]:
        r["outcome"]["satisfied"]["format"] = False
    assert (
        "compact format<26/34"
        in ep.pilot_reading(rows, episodes, floor, 7, cells, deterministic=True)[
            "failures"
        ]
    )
    assert (
        ep.pilot_reading(rows[:-1], episodes, floor, 7, cells, deterministic=True)[
            "reading"
        ]
        == "INCOMPLETE"
    )


def test_pilot7_actual_driver_and_artifact_consumer(tmp_path, monkeypatch):
    import importlib
    import time

    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "scripts"))
    driver = importlib.import_module("composition_pilot7")
    monkeypatch.setattr(driver, "OUT", tmp_path)
    monkeypatch.setattr(driver, "LOCAL", tmp_path / "local")
    monkeypatch.setattr(driver, "START", time.time())
    monkeypatch.setattr(
        driver, "factory", lambda e, a, i, phase="main": driver.d.stub_factory(e, a, i)
    )
    driver.gate()
    result = driver.run_phase("main", 16, 1)
    rows = [
        json.loads(x)
        for x in (tmp_path / "main-records.jsonl").read_text().splitlines()
    ]
    assert len(rows) == 512 and {r["arm"] for r in rows} == set(ep.ARMS)
    assert (tmp_path / "main-records.jsonl").stat().st_size < 10_000_000
    assert result["reading"] == "ELIGIBLE"
    assert result["primary"]["computable_families"] == 3
    assert all("delivery_scope" not in r["outcome"]["satisfied"] for r in rows)
    assert all(
        {
            "output",
            "output_ids",
            "eos",
            "truncated",
            "execution",
            "outcome",
            "prompt_tokens",
            "output_sha256",
            "timing",
        }
        <= r.keys()
        for r in rows
    )
    # This is a driver-only synthetic clock/cost receipt, not GPU eligibility.


@pytest.mark.parametrize(
    "failure",
    [
        "round0",
        "execution",
        "cap",
        "floor",
        "context",
        "cost",
        "determinism",
        "denominators",
    ],
)
def test_each_registered_execution_gate(failure):
    episodes, rows = synthetic()
    cells = {
        (r["episode_id"], r["turn"])
        for r in json.loads(FIXTURE.read_text())["rows"]
        if r["matched"]
    }
    floor = ep.strict_floor(rows)
    hours, deterministic = 7, True
    if failure == "round0":
        rows[0]["execution"]["executed"] = False
    if failure == "execution":
        for r in rows:
            if r["arm"] == "Q" and r["turn"] in (1, 2):
                r["execution"]["executed"] = False
    if failure == "cap":
        for r in rows:
            if r["arm"] == "Q" and r["turn"] == 1:
                r["truncated"] = True
    if failure == "floor":
        floor["traits"]["indent"]["eligible"] = False
    if failure == "context":
        rows[0]["prompt_tokens"] = 32768
    if failure == "cost":
        hours = 12.00001
    if failure == "determinism":
        deterministic = False
    if failure == "denominators":
        for r in rows:
            if r["arm"] == "N" and r["turn"] >= 10:
                r["execution"]["executed"] = False
    result = ep.pilot_reading(
        rows, episodes, floor, hours, cells, deterministic=deterministic
    )
    assert result["reading"] == "INELIGIBLE" and result["failures"]
