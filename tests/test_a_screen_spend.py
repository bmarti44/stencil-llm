"""The candidate-A screen's launch spend ledger and budget guards (F13, F12).

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
import os
from pathlib import Path

from stencil import a_screen as A

T0 = 1_000_000.0
DEAD = "1000-999999"  # a launch id whose pid cannot exist, so it can be observed dead
MINE = f"1000-{os.getpid()}"  # a launch id whose pid is alive: this process


BOOT = A.boot_id()


def _write(path, launch, events, t0=T0, boot=None):
    """Ledger lines in the production format: a realtime ``t`` for the calendar and a
    MONOTONIC ``m`` under this boot's id for every duration (round 9).  ``m`` is written
    on the same scale as ``t`` so a test can pass one number for both clocks.  Pass
    ``boot=""`` to write a line whose monotonic reading is not comparable here -- a
    legacy ledger, or one from an earlier boot -- which falls back to realtime."""
    with path.open("a") as fh:
        for event, elapsed in events:
            rec = {
                "launch": launch,
                "event": event,
                "t": t0 + elapsed,
                "elapsed_s": elapsed,
            }
            if boot != "":
                rec["m"] = t0 + elapsed
                rec["boot"] = BOOT if boot is None else boot
            fh.write(json.dumps(rec) + "\n")


def _charges(path, exclude, at):
    """``ledger_charges`` with both clocks reading ``at``: the tests write ``m`` on the
    same scale as ``t``, so one number drives realtime and monotonic alike."""
    return A.ledger_charges(path, exclude, at, at)


def test_a_mark_measures_its_duration_on_the_monotonic_clock(monkeypatch, tmp_path):
    """Round 9, high: ``elapsed_s`` came from ``time.time()``, which can be STEPPED by
    NTP or by hand.  Astra stepped it 600 s backwards 360 s into a 900 s launch: the
    ledger charged 300 s, and beside 2,400 s of other work the real summary printed GATE
    PASSED at 45 charged minutes against 55 spent.  The step forwards is just as bad --
    a legitimate 45-minute run charged 55 and reported INCOMPLETE."""
    p = tmp_path / "spend.jsonl"
    monkeypatch.setattr(A.time, "time", lambda: T0 - 600.0)  # stepped backwards
    monkeypatch.setattr(A.time, "monotonic", lambda: T0 + 900.0)
    A.ledger_mark(p, DEAD, "end", T0, T0)
    rec = json.loads(p.read_text().splitlines()[0])
    assert rec["elapsed_s"] == 900.0  # the real duration, not the stepped one
    assert rec["t"] == T0 - 600.0 and rec["m"] == T0 + 900.0
    assert rec["boot"] == BOOT


def test_an_unfinished_launch_is_measured_on_the_monotonic_clock(tmp_path):
    # the third charging case compares NOW with the launch's earliest reading, so that
    # comparison is monotonic too: realtime says 5,000 s, the monotonic clock says 900
    p = tmp_path / "spend.jsonl"
    _write(p, DEAD, [("start", 0.0)])
    assert A.ledger_charges(p, "B", T0 + 5000.0, T0 + 900.0)[0][DEAD] == 900.0


def test_an_unfinished_launch_from_another_boot_is_unbounded(tmp_path):
    """Round 10: the realtime fallback was ASSUMED to over-charge, and it does not.
    A launch run to 900 s across a reboot, with 10 s of downtime and a 600 s
    backward step, spans 310 s by realtime and charges the 600 s mark; beside
    2,400 s of completed work the arm then reads 50 minutes charged against 55
    spent.  Downtime establishes no direction, so the launch is UNBOUNDED."""
    for name, boot in (("other.jsonl", "0000-not-this-boot"), ("legacy.jsonl", "")):
        p = tmp_path / name
        _write(p, DEAD, [("start", 0.0), ("tick", 600.0)], boot=boot)
        charges, malformed, unbounded = A.ledger_charges(p, "B", T0 + 310.0, T0 + 900.0)
        assert malformed == 0
        assert unbounded == [DEAD]
        assert charges[DEAD] == 600.0  # the best-effort number, not a trusted one
        spent, refusals = A.ledger_spent_min(p, {DEAD}, T0 + 310.0, T0 + 900.0)
        assert len(refusals) == 1 and "not bounded in either direction" in refusals[0]


def test_an_unobservable_launch_is_not_sealed(tmp_path):
    """The observation is the other half: sealing a realtime subtraction as
    verified spend would fix the wrong number permanently, so a launch with no
    monotonic origin from this boot is not observed at all."""
    p = tmp_path / "other.jsonl"
    _write(p, DEAD, [("start", 0.0), ("tick", 600.0)], boot="0000-not-this-boot")
    assert A.ledger_observe(p, clock=lambda: T0 + 900.0, wall=lambda: T0 + 310.0) == []
    assert "observed_dead" not in p.read_text()
    _, _, unbounded = A.ledger_charges(p, "B", T0 + 310.0, T0 + 900.0)
    assert unbounded == [DEAD]


def test_a_finished_launch_from_another_boot_is_still_charged(tmp_path):
    """The refusal is for launches with no BOUND, not for every cross-boot record: one
    that wrote ``end`` carries its own measured elapsed and is charged it."""
    p = tmp_path / "other.jsonl"
    _write(p, DEAD, [("start", 0.0), ("end", 1500.0)], boot="0000-not-this-boot")
    charges, malformed, unbounded = A.ledger_charges(p, "B", T0 + 310.0, T0 + 900.0)
    assert (malformed, unbounded) == (0, [])
    assert charges[DEAD] == 1500.0
    assert A.ledger_spent_min(p, {DEAD}, T0 + 310.0, T0 + 900.0) == (25.0, [])


def test_no_duration_is_measured_on_the_wall_clock():
    """The mechanical form of round 9's fix: nothing in the screen subtracts wall-clock
    readings.  ``time.time()`` survives only as a calendar stamp and as the documented
    fallback for a launch with no comparable monotonic origin.

    Round 10, high: the TRAINER was not in this list, and it was still timing its
    admission guard, its saves and its final eligibility on the wall clock -- a 600 s
    backward step let a 14,930-second run record 14,330 and read ``complete`` against
    the registered 14,400-second allocation."""
    for name in (
        "src/stencil/a_screen.py",
        "scripts/a_screen_run.py",
        "scripts/a_screen_summary.py",
        "scripts/a_screen_train.py",
    ):
        src = (ROOT / name).read_text()
        bad = []
        for ln in src.splitlines():
            if "time.time()" not in ln:
                continue
            before, _, after = ln.partition("time.time()")
            if after.lstrip().startswith("-") or before.rstrip().endswith("-"):
                bad.append(ln.strip())
        assert not bad, f"{name}: duration taken from the wall clock: {bad}"


def test_an_interrupted_launch_is_charged_through_now(tmp_path):
    # round 5: last checkpoint at 600 s, death at 1,200 s was charged 900 s
    p = tmp_path / "spend.jsonl"
    _write(p, DEAD, [("start", 0.0), ("model_loaded", 80.0), ("record", 600.0)])
    charges, malformed, _unbounded = _charges(p, "B", T0 + 1300.0)
    assert malformed == 0
    assert charges[DEAD] == 1300.0


def test_silence_does_not_bound_a_launch(tmp_path):
    """Round 7 F13: the heartbeat rule charged a launch its last tick plus three
    intervals when no gap was wider than the slack. But a ledger with ticks to 600 s
    is equally consistent with death at 600 s and with a TICKER that failed at 600 s
    while the process ran on -- Astra killed the ticker thread by injecting an append
    failure and the main thread carried on. Absence of a mark is not evidence of
    termination."""
    p = tmp_path / "spend.jsonl"
    ticks = [("tick", float(x)) for x in range(0, 601, 60)]
    _write(p, DEAD, [("start", 0.0), *ticks])
    # the old rule charged 600 + 180 = 780 whatever the read time
    assert _charges(p, "B", T0 + 1500.0)[0][DEAD] == 1500.0
    assert _charges(p, "B", T0 + 9000.0)[0][DEAD] == 9000.0


def test_an_observation_bounds_it_and_then_never_moves(tmp_path):
    # the charge is bounded by EVIDENCE: a process that is gone at a known time cannot
    # have lived past it, and the observation is recorded once so later reads agree
    p = tmp_path / "spend.jsonl"
    _write(p, DEAD, [("start", 0.0), ("record", 600.0)])
    assert A.ledger_observe(p, clock=lambda: T0 + 1500.0) == [DEAD]
    assert _charges(p, "B", T0 + 1500.0)[0][DEAD] == 1500.0
    assert _charges(p, "B", T0 + 99_999.0)[0][DEAD] == 1500.0
    # recorded once, never re-recorded
    assert A.ledger_observe(p, clock=lambda: T0 + 99_999.0) == []


def test_the_observation_is_timestamped_after_the_probe(tmp_path):
    """Round 8 F13: the caller sampled ``now`` once and passed it in, so a process
    descheduled between that sample and the pid probe wrote a BACKDATED observation --
    sampled at 300 s, probed at 1,000 s, permanently charging 300 s for a launch that
    lived to 900.  Absence at the probe establishes termination by the PROBE's time.

    Round 9 makes the property structural: the function takes ONE duration reading and
    takes it after the probe, and the wall clock it reads for the calendar stamp --
    300 s here -- cannot reach the charge at all."""
    p = tmp_path / "spend.jsonl"
    _write(p, DEAD, [("start", 0.0)])
    seen = []

    def probe_clock():
        seen.append("probe")
        return T0 + 1000.0

    observed = A.ledger_observe(p, clock=probe_clock, wall=lambda: T0 + 300.0)
    assert observed == [DEAD]
    assert seen == ["probe"]  # sampled exactly once, after the pid probe succeeded
    assert _charges(p, "B", T0 + 5000.0)[0][DEAD] == 1000.0


def test_a_live_launch_is_not_observed_dead(tmp_path):
    # a running process, or a recycled pid, must keep accruing: the conservative
    # direction
    p = tmp_path / "spend.jsonl"
    _write(p, MINE, [("start", 0.0)])
    assert A.ledger_observe(p, clock=lambda: T0 + 500.0) == []
    assert _charges(p, "other", T0 + 500.0)[0][MINE] == 500.0


def test_a_launch_killed_while_loading_is_charged_its_loading_time(tmp_path):
    # round 6 F13: model loading had no enforced limit, so a launch killed while loading
    # at 900 s and read at 1,200 s was charged the 600 s load bound
    p = tmp_path / "spend.jsonl"
    _write(p, DEAD, [("start", 0.0)])
    assert _charges(p, "B", T0 + 1200.0)[0][DEAD] == 1200.0
    A.ledger_observe(p, clock=lambda: T0 + 1200.0)
    assert _charges(p, "B", T0 + 1200.0)[0][DEAD] == 1200.0


def test_the_pilots_suite_cost_gap_is_inside_the_charge(tmp_path):
    # round 6 F13: the post-load bound assumed six suites between marks, and the pilot
    # runs 44 (4 sessions x 11) between model_loaded and suite_cost_measured
    p = tmp_path / "spend.jsonl"
    _write(
        p,
        DEAD,
        [("start", 0.0), ("model_loaded", 200.0), ("suite_cost_measured", 900.0)],
    )
    assert _charges(p, "B", T0 + 1500.0)[0][DEAD] == 1500.0


def test_a_finished_launch_is_charged_its_elapsed_time(tmp_path):
    p = tmp_path / "spend.jsonl"
    _write(p, "A", [("start", 0.0), ("record", 600.0), ("end", 900.0)])
    charges, _, _u = _charges(p, "B", T0 + 5000.0)
    assert charges["A"] == 900.0


def test_a_torn_tail_is_repaired_so_the_next_launch_is_visible(tmp_path):
    p = tmp_path / "spend.jsonl"
    _write(p, "A", [("start", 0.0), ("model_loaded", 80.0), ("record", 600.0)])
    with p.open("a") as fh:
        fh.write('{"launch": "A", "event": "rec')  # killed mid-write, no newline
    torn = A.ledger_repair(p)
    assert torn is not None and torn.startswith('{"launch": "A"')
    # launch B's own marks, in the same synthetic epoch as A's
    _write(p, "B", [("start", 0.0), ("record", 60.0)], t0=T0 + 1200.0)
    charges, malformed, _unbounded = _charges(p, "C", T0 + 1300.0)
    assert malformed == 0
    assert "B" in charges and charges["B"] > 0.0  # B was erased before the repair
    assert A.ledger_repair(p) is None  # a clean tail is left alone


def test_a_malformed_line_is_reported_not_skipped(tmp_path):
    p = tmp_path / "spend.jsonl"
    _write(p, "A", [("start", 0.0)])
    with p.open("a") as fh:
        fh.write("not json at all\n")
    _, malformed, _u = _charges(p, "B", T0 + 10.0)
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


def test_absent_spend_evidence_is_a_refusal_not_a_zero(tmp_path):
    """Round 7 F12: a missing or emptied ledger read as zero spend, so deleting an
    ordinary sidecar turned an over-budget arm into GATE PASSED.  Absence of evidence is
    not evidence of nothing."""
    missing = tmp_path / "gone.jsonl"
    spent, refusals = A.ledger_spent_min(missing, {"L1"})
    assert spent == 0.0 and len(refusals) == 1 and "missing" in refusals[0]
    empty = tmp_path / "empty.jsonl"
    empty.write_text("")
    _, refusals = A.ledger_spent_min(empty, {"L1"})
    assert len(refusals) == 1 and "empty" in refusals[0]


def test_the_ledger_must_account_for_every_launch_the_records_name(tmp_path):
    # a ledger covering only some of the launches that produced records accounts for
    # none of the rest, which is a refusal rather than a smaller number
    p = tmp_path / "spend.jsonl"
    _write(p, "L1", [("start", 0.0), ("end", 60.0)])
    spent, refusals = A.ledger_spent_min(
        p, {"L1", "L2"}, now=T0 + 60.0, now_m=T0 + 60.0
    )
    assert len(refusals) == 1 and "L2" in refusals[0]
    assert A.ledger_spent_min(p, {"L1"}, now=T0 + 60.0, now_m=T0 + 60.0)[1] == []


def test_the_registered_ceiling_admits_the_last_request(tmp_path):
    """Round 7, medium: §18.2 sized the ceiling against total work and forgot the
    five-minute admission margin, so under the registered estimates a 45-minute ceiling
    refused request 96 at 2,416 s.  Simulate the real guard over all 48 sessions."""
    work = (
        A.GEN_ESTIMATE_S + 5 * A.SUITE_COST_S,
        A.GEN_ESTIMATE_S + 6 * A.SUITE_COST_S,
    )
    for ceiling, ok in ((45.0, False), (A.ARM_BUDGET_MIN, True)):
        spent_s = A.LOAD_ALLOWANCE_S
        admitted = 0
        for _ in range(48):
            for w in work:
                if not A.may_start(ceiling, spent_s / 60, A.START_MARGIN_MIN):
                    break
                admitted += 1
                spent_s += w
        assert (admitted == 96) is ok, (ceiling, admitted, spent_s)
    assert A.ARM_BUDGET_MIN >= A.arm_budget_min()


# 2026-09-13: these fixtures are DERIVED from the budget, never hard-coded.
# ARM_BUDGET_MIN was raised from 50 to 100 minutes once the generation time was
# measured, and the 3001 s literal that used to mean "over budget" silently became
# comfortably UNDER it.  Two tests failed loudly, which was lucky; a third kept
# passing for an unrelated reason (its ledger was deleted) while no longer
# exercising the case it names.  A fixture that encodes a threshold has to be
# computed from that threshold, and the relation is asserted here so the next
# change to the constant cannot quietly hollow these tests out.
UNDER_BUDGET_S = A.ARM_BUDGET_MIN * 0.8 * 60.0
OVER_BUDGET_S = (A.ARM_BUDGET_MIN + 1.0) * 60.0 + 1.0
assert UNDER_BUDGET_S / 60.0 < A.ARM_BUDGET_MIN < OVER_BUDGET_S / 60.0


def test_the_ledger_is_read_independently_of_the_status(tmp_path):
    # the status is the runner's claim; the ledger is the evidence.  A status claiming
    # COMPLETE and well inside budget over a ledger holding more must not be believed.
    p = tmp_path / "cf.jsonl.spend.jsonl"
    _write(p, "L1", [("start", 0.0), ("end", OVER_BUDGET_S)])
    spent, refusals = A.ledger_spent_min(
        p, {"L1"}, now=T0 + OVER_BUDGET_S, now_m=T0 + OVER_BUDGET_S
    )
    assert refusals == []
    assert spent > A.ARM_BUDGET_MIN


ROOT = Path(__file__).resolve().parents[1]


def _screen_records(runs, spend_s, budget_min, max_new=A.MAX_NEW_TOKENS, ledger=True):
    """Complete 48-session records for all three arms, with the spend ledger and status
    artifact a run of that length would have left.  Nested winners (20/25/32 of 48) so
    every count gate clears and only eligibility can change the verdict."""
    manifest = json.loads((ROOT / "results/a-screen/manifest.json").read_text())
    pool = json.loads((ROOT / "results/a-screen/screen-pool.json").read_text())
    ids = sorted(r["session"] for r in manifest["sessions"])
    ident = {
        "pool_sha256": pool["pool_sha256"],
        "a_screen_sha256": "x",
        "contracts_sha256": "x",
        "runner_sha256": "x",
        "hub": "hub",
        "hub_sha256": "x",
        "eos": [1],
        "max_new": max_new,
        "deadline_s": 300.0,
        "prompt_budget": A.PROMPT_BUDGET,
        "sessions": ids,
        "pilot_adapter": False,
    }
    winners = {"off": set(ids[:20]), "sft": set(ids[:25]), "cf": set(ids[:32])}
    runs.mkdir(parents=True, exist_ok=True)
    for arm, adapter in (("off", "none"), ("sft", "s"), ("cf", "c")):
        with (runs / f"{arm}.jsonl").open("w") as fh:
            for m in manifest["sessions"]:
                ok = m["session"] in winners[arm]
                sc = dict.fromkeys(A.SUITES, ok)
                sc["all"] = sc["function_only"] = ok
                for k in (1, 2):
                    fh.write(
                        json.dumps(
                            {
                                "arm": arm,
                                "session": m["session"],
                                "request": k,
                                "target_family": m["target"],
                                "lifecycle": m["lifecycle"],
                                "terminal_reason": "applied" if ok else "truncated",
                                "identity": dict(ident, adapter=adapter),
                                "truncated": False,
                                "timed_out": False,
                                "seconds": 40.0,
                                "generated_tokens": 50,
                                "scores": sc,
                                "J": ok,
                                "function_only": ok,
                                "launch": "L1",
                            }
                        )
                        + "\n"
                    )
        if ledger:
            _write(
                runs / f"{arm}.jsonl.spend.jsonl",
                "L1",
                [("start", 0.0), ("end", spend_s)],
            )
        A.write_status(
            runs / f"{arm}.jsonl.status.json",
            arm=arm,
            launch="L1",
            status=A.run_status([], [], budget_min, spend_s / 60),
            spent_min=spend_s / 60,
            budget_min=budget_min,
            registered_budget_min=A.ARM_BUDGET_MIN,
            sessions=ids,
            not_started=[],
            request2_not_started=[],
            over_budget=spend_s / 60 > budget_min,
            pilot=False,
        )
    return runs


def _summary(runs):
    """``(verdict line, gate PASS/FAIL lines printed)`` from the real summary."""
    import subprocess
    import sys

    cmd = [sys.executable, str(ROOT / "scripts/a_screen_summary.py")]
    cmd += ["--runs", str(runs)]
    out = subprocess.run(
        cmd, capture_output=True, text=True, cwd=ROOT, check=True
    ).stdout
    verdict = next(ln for ln in out.splitlines() if ln.startswith("**Verdict"))
    gates = sum(
        1
        for ln in out.splitlines()
        if ln.startswith("- ") and (": PASS" in ln or ": FAIL" in ln)
    )
    return verdict, gates


def test_the_summary_reads_the_gates_for_an_eligible_evaluation(tmp_path):
    # the control: the same records inside budget must still produce the gate reading,
    # or
    # the three refusals below would prove nothing
    runs = _screen_records(tmp_path / "runs", UNDER_BUDGET_S, A.ARM_BUDGET_MIN)
    verdict, gates = _summary(runs)
    assert verdict.startswith("**Verdict: GATE PASSED**")
    assert gates == 12


def test_the_summary_refuses_an_over_budget_evaluation(tmp_path):
    """The consumer's semantics (AGENTS.md): round 6 F12 was a check that existed in the
    runner's console output and nowhere the summary reads, so complete 48-session
    records from an over-budget evaluation produced ``Verdict: GATE PASSED``.  Round 7:
    suppressing the verdict alone still printed twelve PASS lines above it, so the gates
    must not be computed at all."""
    runs = _screen_records(tmp_path / "runs", OVER_BUDGET_S, A.ARM_BUDGET_MIN)
    verdict, gates = _summary(runs)
    assert "INCOMPLETE (budget eligibility:" in verdict
    assert "GATE PASSED**" not in verdict
    assert gates == 0


def test_the_summary_refuses_a_deleted_spend_ledger(tmp_path):
    # round 7 F12: removing the sidecar made the independent evidence check read zero
    runs = _screen_records(
        tmp_path / "runs", OVER_BUDGET_S, A.ARM_BUDGET_MIN, ledger=False
    )
    verdict, gates = _summary(runs)
    assert "INCOMPLETE (budget eligibility:" in verdict and gates == 0


def test_the_summary_refuses_an_incomplete_evaluation(tmp_path):
    """Round 8 F12: missing records took the other path -- dropping a single checkpoint
    still printed all twelve gates and read "provisional: GATE PASSED", because
    `missing` only rewrote the verdict after the gates had been computed."""
    runs = _screen_records(tmp_path / "runs", UNDER_BUDGET_S, A.ARM_BUDGET_MIN)
    cf = runs / "cf.jsonl"
    kept = [
        ln
        for ln in cf.read_text().splitlines()
        if not (json.loads(ln)["session"] == "S48" and json.loads(ln)["request"] == 2)
    ]
    cf.write_text("\n".join(kept) + "\n")
    verdict, gates = _summary(runs)
    assert "INCOMPLETE (47/48 sessions complete" in verdict
    assert "GATE PASSED" not in verdict and gates == 0


def test_the_summary_refuses_an_unregistered_output_cap(tmp_path):
    # round 7, medium: the three arms AGREEING on --max-new 2048 passed every identity
    # check, so the registered cap is checked against its own value
    runs = _screen_records(
        tmp_path / "runs", UNDER_BUDGET_S, A.ARM_BUDGET_MIN, max_new=2048
    )
    verdict, gates = _summary(runs)
    assert "INCOMPLETE (budget eligibility:" in verdict and gates == 0


def test_a_backwards_clock_cannot_zero_a_charge(tmp_path):
    # the observation's elapsed is a wall-clock difference, so a clock that moved
    # backwards between the launch and the observation must not charge less than the
    # launch's own marks
    p = tmp_path / "spend.jsonl"
    _write(p, DEAD, [("start", 0.0), ("record", 900.0)])
    A.ledger_observe(p, clock=lambda: T0 - 500.0)  # "now" is BEFORE the launch started
    charges, _, _u = _charges(p, "B", T0 + 1000.0)
    assert charges[DEAD] == 900.0
