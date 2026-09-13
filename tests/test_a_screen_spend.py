"""The candidate-A screen's launch spend ledger and budget guards (round 5, F13).

Every case here is one of the escapes the round-5 review demonstrated by executing the
accounting: an interrupted launch charged less than it spent, a torn ledger line erasing
a launch entirely, and a request admitted with two minutes of budget left running a full
300 s generation plus scoring and still reporting COMPLETE.
"""

from __future__ import annotations

import json

from stencil import a_screen as A

DEADLINE_S = 300.0
BOUND_S = A.work_bound_s(DEADLINE_S)


def _write(path, launch, events, t0=1_000_000.0):
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


def test_work_bound_covers_one_generation_and_every_suite():
    # a checkpoint follows generation AND scoring, so the bound has to cover both
    assert BOUND_S == DEADLINE_S + len(A.SUITES) * A.SUITE_TIMEOUT_S == 840.0


def test_an_interrupted_launch_is_charged_its_lifetime(tmp_path):
    # round 5: last checkpoint at 600 s, death at 1200 s was charged 900 s
    p = tmp_path / "spend.jsonl"
    _write(p, "A", [("start", 0.0), ("model_loaded", 80.0), ("record", 600.0)])
    charges, malformed = A.ledger_charges(p, "B", 1_000_000.0 + 1300.0, BOUND_S)
    assert malformed == 0
    assert charges["A"] >= 1200.0


def test_an_interrupted_launch_charge_stays_bounded(tmp_path):
    # read a day later, the lifetime term must not charge the whole day
    p = tmp_path / "spend.jsonl"
    _write(p, "A", [("start", 0.0), ("model_loaded", 80.0), ("record", 600.0)])
    charges, _ = A.ledger_charges(p, "B", 1_000_000.0 + 86_400.0, BOUND_S)
    assert charges["A"] == 600.0 + BOUND_S


def test_a_finished_launch_is_charged_its_elapsed_time(tmp_path):
    p = tmp_path / "spend.jsonl"
    _write(p, "A", [("start", 0.0), ("record", 600.0), ("end", 900.0)])
    charges, _ = A.ledger_charges(p, "B", 1_000_000.0 + 5000.0, BOUND_S)
    assert charges["A"] == 900.0


def test_a_launch_that_died_while_loading_is_charged(tmp_path):
    # no checkpoint yet, so only the lifetime and the load bound can charge it
    p = tmp_path / "spend.jsonl"
    _write(p, "A", [("start", 0.0)])
    charges, _ = A.ledger_charges(p, "B", 1_000_000.0 + 400.0, BOUND_S)
    assert charges["A"] == 400.0
    charges, _ = A.ledger_charges(p, "B", 1_000_000.0 + 99_999.0, BOUND_S)
    assert charges["A"] == A.LOAD_BOUND_S


def test_a_torn_tail_is_repaired_so_the_next_launch_is_visible(tmp_path):
    p = tmp_path / "spend.jsonl"
    _write(p, "A", [("start", 0.0), ("model_loaded", 80.0), ("record", 600.0)])
    with p.open("a") as fh:
        fh.write('{"launch": "A", "event": "rec')  # killed mid-write, no newline
    torn = A.ledger_repair(p)
    assert torn is not None and torn.startswith('{"launch": "A"')
    A.ledger_mark(p, "B", "start", __import__("time").time())
    charges, malformed = A.ledger_charges(p, "C", 1_000_000.0 + 1300.0, BOUND_S)
    assert malformed == 0
    assert "B" in charges and charges["B"] > 0.0  # B was erased before the repair
    assert A.ledger_repair(p) is None  # a clean tail is left alone


def test_a_malformed_line_is_reported_not_skipped(tmp_path):
    p = tmp_path / "spend.jsonl"
    _write(p, "A", [("start", 0.0)])
    with p.open("a") as fh:
        fh.write("not json at all\n")
    _, malformed = A.ledger_charges(p, "B", 1_000_000.0 + 10.0, BOUND_S)
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
