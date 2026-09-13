"""The candidate-A screen's launch spend ledger, heartbeat and budget guards (F13, F12).

Every case here is one of the escapes a review demonstrated by executing the accounting:
an interrupted launch charged less than it spent (round 5: a last checkpoint at 600 s
and death at 1,200 s charged 900 s; round 6: death at 900 s DURING MODEL LOADING charged
600 s, and the pilot's 44-suite gap lay outside the post-load bound), a torn ledger line
erasing a launch entirely, a request admitted with two minutes of budget left running a
full 300 s generation plus scoring and still reporting COMPLETE, and complete records
from an over-budget evaluation producing the authoritative GATE PASSED verdict.
"""

from __future__ import annotations

import json
from pathlib import Path

from stencil import a_screen as A

T0 = 1_000_000.0
SLACK = A.TICK_SLACK_S


def _write(path, launch, events, t0=T0):
    with path.open("a") as fh:
        for event, elapsed in events:
            fh.write(
                json.dumps(
                    {
                        "launch": launch,
                        "event": event,
                        "t": t0 + elapsed,
                        "elapsed_s": elapsed,
                    }
                )
                + "\n"
            )


def _beat(until, every=A.TICK_S):
    """The heartbeat marks a launch alive until ``until`` seconds of life."""
    out, t = [], 0.0
    while t <= until:
        out.append(("tick", t))
        t += every
    return out


def test_the_heartbeat_slack_is_three_intervals():
    assert A.TICK_S == 60.0 and SLACK == 180.0


def test_an_interrupted_launch_is_charged_its_lifetime(tmp_path):
    # round 5: last checkpoint at 600 s, death at 1,200 s was charged 900 s
    p = tmp_path / "spend.jsonl"
    _write(p, "A", [("start", 0.0), ("model_loaded", 80.0)] + _beat(1200.0))
    charges, malformed = A.ledger_charges(p, "B", T0 + 1300.0)
    assert malformed == 0
    assert charges["A"] >= 1200.0


def test_a_launch_killed_while_loading_is_charged_its_loading_time(tmp_path):
    # round 6 F13: model loading had no enforced limit, so a launch killed while loading
    # at 900 s and read at 1,200 s was charged the 600 s load bound.  The heartbeat runs
    # from before the load, so its last tick bounds the charge from below.
    p = tmp_path / "spend.jsonl"
    _write(p, "A", [("start", 0.0)] + _beat(900.0))
    charges, _ = A.ledger_charges(p, "B", T0 + 1200.0)
    assert charges["A"] >= 900.0
    assert charges["A"] == 900.0 + SLACK


def test_the_pilots_suite_cost_gap_is_inside_the_charge(tmp_path):
    # round 6 F13: the post-load bound assumed six suites between marks, and the pilot
    # runs 44 (4 sessions x 11) between model_loaded and suite_cost_measured.
    p = tmp_path / "spend.jsonl"
    _write(
        p,
        "A",
        [("start", 0.0), ("model_loaded", 200.0)]
        + _beat(1500.0)
        + [("suite_cost_measured", 900.0)],
    )
    charges, _ = A.ledger_charges(p, "B", T0 + 9_000.0)
    assert charges["A"] >= 1500.0


def test_an_intact_heartbeat_bounds_the_charge(tmp_path):
    # read a day later, the charge must not grow to the whole day
    p = tmp_path / "spend.jsonl"
    _write(p, "A", [("start", 0.0), ("record", 600.0)] + _beat(600.0))
    charges, _ = A.ledger_charges(p, "B", T0 + 86_400.0)
    assert charges["A"] == 600.0 + SLACK


def test_a_broken_heartbeat_is_charged_the_whole_lifetime(tmp_path):
    # nothing bounds what a launch did across an interval no mark closes, so the cap is
    # gone: a ten-minute hole (a stopped process, a full disk, a starved writer) is
    # charged the lifetime, which is an upper bound whatever happened in the dark
    p = tmp_path / "spend.jsonl"
    _write(p, "A", [("start", 0.0), ("tick", 0.0), ("record", 600.0)])
    charges, _ = A.ledger_charges(p, "B", T0 + 9_000.0)
    assert charges["A"] == 9_000.0


def test_a_launch_killed_in_its_first_minute_is_bounded(tmp_path):
    # the ticker writes its first tick before its first wait, so a launch with no
    # checkpoint yet still has a verified alive-timestamp
    p = tmp_path / "spend.jsonl"
    _write(p, "A", [("start", 0.0), ("tick", 0.0)])
    charges, _ = A.ledger_charges(p, "B", T0 + 86_400.0)
    assert charges["A"] == SLACK


def test_a_finished_launch_is_charged_its_elapsed_time(tmp_path):
    p = tmp_path / "spend.jsonl"
    _write(p, "A", [("start", 0.0), ("record", 600.0), ("end", 900.0)])
    charges, _ = A.ledger_charges(p, "B", T0 + 5000.0)
    assert charges["A"] == 900.0


def test_a_torn_tail_is_repaired_so_the_next_launch_is_visible(tmp_path):
    p = tmp_path / "spend.jsonl"
    _write(p, "A", [("start", 0.0), ("model_loaded", 80.0), ("record", 600.0)])
    with p.open("a") as fh:
        fh.write('{"launch": "A", "event": "rec')  # killed mid-write, no newline
    torn = A.ledger_repair(p)
    assert torn is not None and torn.startswith('{"launch": "A"')
    A.ledger_mark(p, "B", "start", __import__("time").time())
    charges, malformed = A.ledger_charges(p, "C", T0 + 1300.0)
    assert malformed == 0
    assert "B" in charges and charges["B"] > 0.0  # B was erased before the repair
    assert A.ledger_repair(p) is None  # a clean tail is left alone


def test_a_malformed_line_is_reported_not_skipped(tmp_path):
    p = tmp_path / "spend.jsonl"
    _write(p, "A", [("start", 0.0)])
    with p.open("a") as fh:
        fh.write("not json at all\n")
    _, malformed = A.ledger_charges(p, "B", T0 + 10.0)
    assert malformed == 1


def test_every_request_start_is_guarded():
    # the round-5 scenario: budget 45 min, request 1 admitted at 39.98 min
    budget, margin = 45.0, 5
    assert A.may_start(budget, 2399.0 / 60, margin)
    # request 2 would start at 44.97 min with two seconds of budget left
    assert not A.may_start(budget, 2698.0 / 60, margin)
    assert A.may_start(None, 10_000.0, margin)  # no budget given: never refused


def test_an_over_budget_run_is_incomplete():
    assert A.run_status([], [], 45.0, 2997.0 / 60) == "INCOMPLETE"
    assert A.run_status([], [], 45.0, 44.0) == "COMPLETE"
    assert A.run_status(["S01"], [], 45.0, 10.0) == "INCOMPLETE"
    assert A.run_status([], ["S01"], 45.0, 10.0) == "INCOMPLETE"
    assert A.run_status([], [], None, 10_000.0) == "COMPLETE"


# ------------------------------------------------- round 6 F12: durable eligibility


def _status(tmp_path, **kw):
    p = tmp_path / "cf.jsonl.status.json"
    fields = dict(
        arm="cf",
        launch="L1",
        status="COMPLETE",
        spent_min=40.0,
        budget_min=A.ARM_BUDGET_MIN,
        registered_budget_min=A.ARM_BUDGET_MIN,
        sessions=["S01"],
        not_started=[],
        request2_not_started=[],
        over_budget=False,
        pilot=False,
    )
    fields.update(kw)
    A.write_status(p, **fields)
    return p


def test_a_missing_status_is_refused(tmp_path):
    st, refusal = A.read_status(tmp_path / "cf.jsonl.status.json")
    assert st is None and "missing" in refusal


def test_a_complete_in_budget_status_is_accepted(tmp_path):
    st, refusal = A.read_status(_status(tmp_path))
    assert refusal is None and st["status"] == "COMPLETE"


def test_an_incomplete_status_is_refused(tmp_path):
    _, refusal = A.read_status(_status(tmp_path, status="INCOMPLETE"))
    assert "INCOMPLETE" in refusal


def test_an_unbudgeted_or_over_ceiling_run_is_refused(tmp_path):
    for budget in (0.0, A.ARM_BUDGET_MIN + 1):
        _, refusal = A.read_status(_status(tmp_path, budget_min=budget))
        assert "registered per-arm ceiling" in refusal


def test_a_status_that_spent_more_than_its_budget_is_refused(tmp_path):
    _, refusal = A.read_status(_status(tmp_path, spent_min=A.ARM_BUDGET_MIN + 0.1))
    assert "budget" in refusal


def test_a_pilot_status_is_refused(tmp_path):
    _, refusal = A.read_status(_status(tmp_path, pilot=True))
    assert "PILOT" in refusal


def test_the_ledger_is_read_independently_of_the_status(tmp_path):
    # the status is the runner's claim; the ledger is the evidence.  A status claiming
    # COMPLETE and 40 minutes over a ledger holding 45.02 must not be believed.
    p = tmp_path / "cf.jsonl.spend.jsonl"
    _write(p, "L1", [("start", 0.0), ("end", 2701.0)])
    spent, malformed = A.ledger_spent_min(p, now=T0 + 2701.0)
    assert malformed == 0
    assert spent > A.ARM_BUDGET_MIN


def test_the_summary_refuses_an_over_budget_evaluation(tmp_path):
    """The consumer's semantics (AGENTS.md): round 6 F12 was a check that existed in
    the runner's console output and nowhere the summary reads, so complete 48-session
    records from an over-budget evaluation produced ``Verdict: GATE PASSED``.  This
    builds exactly those records and runs the real summary."""
    import subprocess
    import sys

    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root / "results/a-screen/manifest.json").read_text())
    pool = json.loads((root / "results/a-screen/screen-pool.json").read_text())
    ids = sorted(r["session"] for r in manifest["sessions"])
    ident = {
        "pool_sha256": pool["pool_sha256"],
        "a_screen_sha256": "x",
        "contracts_sha256": "x",
        "runner_sha256": "x",
        "hub": "hub",
        "hub_sha256": "x",
        "eos": [1],
        "max_new": A.MAX_NEW_TOKENS,
        "deadline_s": 300.0,
        "prompt_budget": A.PROMPT_BUDGET,
        "sessions": ids,
        "pilot_adapter": False,
    }
    # nested winners so every count gate clears: off 20, sft 25, cf 32 of 48
    winners = {"off": set(ids[:20]), "sft": set(ids[:25]), "cf": set(ids[:32])}
    runs = tmp_path / "runs"
    runs.mkdir()
    for arm, adapter in (("off", "none"), ("sft", "s"), ("cf", "c")):
        with (runs / f"{arm}.jsonl").open("w") as fh:
            for s in manifest["sessions"]:
                ok = s["session"] in winners[arm]
                sc = dict.fromkeys(A.SUITES, ok)
                sc["all"] = sc["function_only"] = ok
                for k in (1, 2):
                    fh.write(
                        json.dumps(
                            {
                                "arm": arm,
                                "session": s["session"],
                                "request": k,
                                "target_family": s["target"],
                                "lifecycle": s["lifecycle"],
                                "terminal_reason": "applied" if ok else "truncated",
                                "identity": dict(ident, adapter=adapter),
                                "truncated": False,
                                "timed_out": False,
                                "seconds": 40.0,
                                "generated_tokens": 50,
                                "scores": sc,
                                "J": ok,
                                "function_only": ok,
                            }
                        )
                        + "\n"
                    )
        # 2,701 s resident against the registered 45-minute (2,700 s) ceiling
        _write(
            runs / f"{arm}.jsonl.spend.jsonl", "L1", [("start", 0.0), ("end", 2701.0)]
        )
        A.write_status(
            runs / f"{arm}.jsonl.status.json",
            arm=arm,
            launch="L1",
            status=A.run_status([], [], A.ARM_BUDGET_MIN, 2701.0 / 60),
            spent_min=2701.0 / 60,
            budget_min=A.ARM_BUDGET_MIN,
            registered_budget_min=A.ARM_BUDGET_MIN,
            sessions=ids,
            not_started=[],
            request2_not_started=[],
            over_budget=True,
            pilot=False,
        )
    cmd = [sys.executable, str(root / "scripts/a_screen_summary.py")]
    cmd += ["--runs", str(runs)]
    done = subprocess.run(cmd, capture_output=True, text=True, cwd=root, check=True)
    got = done.stdout
    assert "**Verdict: INCOMPLETE (budget eligibility:" in got
    assert "GATE PASSED**" not in got
