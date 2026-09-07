"""Amendment 3 consumer checks: reply repair, execution unit, floor, screen."""

import copy
import json

from stencil.focus import slab2 as s


def test_worked_example_and_reply_feedback(tmp_path):
    example = s.SYSTEM_PROMPT[s.SYSTEM_PROMPT.index("```") :].split("\n\n", 1)[0]
    path, code, report = s.parse_reply(example, "core.py")
    assert path == "core.py" and report["task"] == "A"
    compile(code, path, "exec")
    assert s.SYSTEM_PROMPT.count("```") == 2
    e = s.generate_episode()
    s.materialize(e, tmp_path)
    ex = s.Executor(tmp_path, e)
    result = ex.run("```python\ncore.py\n```python\npass\n```", 0)
    assert result["fences_seen"] == 3
    assert "\n" not in result["expected_shape"]
    assert len(result["expected_shape"]) <= 256
    assert e.turns[0].path in result["expected_shape"]
    assert len(json.dumps(result).encode()) < 8192
    repaired = ex.run(s.reference(e, 0), 0)
    assert s.file_written({"execution": repaired, "truncated": False})


def records():
    return [
        dict(
            episode_id=f"slab2-dev-{i:02}",
            arm=a,
            turn=j,
            truncated=False,
            execution=dict(executed=True),
            outcome=dict(
                observed=True,
                integration=True,
                report_ok=True,
                diagnostics=dict.fromkeys(
                    (*s.TRAITS, "breakage", "wrong_family"), False
                ),
            ),
        )
        for i in range(8)
        for a in "RNTQ"
        for j in range(16)
    ]


def test_lane_execution_and_primary_gate():
    rows = records()
    floor = dict(
        eligible_traits=["indent", "delivery"],
        traits={
            k: dict(
                eligible=k in ("indent", "delivery"), opportunity_episodes=["a", "b"]
            )
            for k in s.TRAITS
        },
    )
    # Eight failures in one lane count once, with per-round rate descriptive.
    for r in rows:
        if r["arm"] == "N" and r["episode_id"].endswith("00") and r["turn"] < 15:
            r["execution"] = dict(executed=False, category="fence_count_or_kind")
    v = s.pilot5_reading(rows, floor, 10)
    assert v["eligible"] and v["per_arm"]["N"]["executing_lanes"] == 8
    assert v["per_arm"]["N"]["executed_rounds"] == 113
    # Collapse one entire lane: pooled rounds still >90%, lane gate fails.
    next(
        r
        for r in rows
        if r["arm"] == "N" and r["episode_id"].endswith("00") and r["turn"] == 15
    )["execution"]["executed"] = False
    assert not s.pilot5_reading(rows, floor, 10)["eligible"]
    assert not s.pilot5_reading([r for r in records() if r["arm"] != "Q"], floor, 10)[
        "eligible"
    ]
    floor["traits"]["indent"]["eligible"] = False
    floor["traits"]["format"]["eligible"] = True
    assert s.pilot5_reading(records(), floor, 10)["kinds"] == ["process"]
    row = records()[0]
    row["execution"]["category"] = "syntax_error"
    assert not s.file_written(row)


def test_floor_uses_registered_change_boundary():
    rows = []
    for e in s.bank():
        start = next(
            t.index
            for t in e.turns
            if any(v.key == "indent" and v.action == "supersedes" for v in t.events)
        )
        for t in e.turns:
            rows.append(
                dict(
                    episode_id=e.episode_id,
                    arm="T",
                    turn=t.index,
                    outcome=dict(
                        observed=True,
                        applicable=dict.fromkeys(s.TRAITS, True),
                        satisfied={
                            k: k != "indent" or t.index >= start for k in s.TRAITS
                        },
                        trait_denominators=dict.fromkeys(s.TRAITS, 1),
                    ),
                )
            )
    floor = s.freeze_t_floor(rows)
    assert floor["traits"]["indent"]["total"] == 39
    assert floor["traits"]["indent"]["passed"] == 39
    assert floor["traits"]["language"]["total"] == 128
    missing = copy.deepcopy(rows)
    for r in missing:
        r["outcome"]["observed"] = False
    assert s.freeze_t_floor(missing)["traits"]["indent"]["total"] == 39
    assert not s.freeze_t_floor(missing)["traits"]["indent"]["eligible"]


def test_q_cost_and_screen_gate():
    costs = dict(R=159.550, N=117.601, T=110.996, O=155.095, Q=117.601)
    without = (
        494.284
        + 1.25 * (64 * (costs["R"] + costs["N"]) + 16 * (costs["T"] + costs["O"]))
    ) / 3600
    assert (
        abs(
            (s.measured_projection(costs, load_seconds=494.284) - without)
            - 2.6133555555555557
        )
        < 1e-9
    )
    rows = [r for r in records() if r["episode_id"] in ("slab2-dev-00", "slab2-dev-01")]
    assert s.screen_reading(rows)["reading"] == "SCREEN-PASS"
    rows[0]["execution"] = dict(executed=False, category="fence_count_or_kind")
    assert s.screen_reading(rows)["reading"] == "SCREEN-FAIL"
    assert s.screen_reading([])["reading"] == "SCREEN-NOT-PASS"
    rows = [r for r in records() if r["episode_id"] in ("slab2-dev-00", "slab2-dev-01")]
    for r in rows:
        if r["arm"] == "Q" and r["turn"] in (1, 2):
            r["execution"]["executed"] = False
    assert s.screen_reading(rows)["reading"] == "SCREEN-NOT-PASS"
