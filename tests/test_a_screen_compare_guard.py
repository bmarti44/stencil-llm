"""The comparison guard must BITE, not merely pass.

Astra's back-on-track review (2026-09-13): the preflight guard's 13/13 mutation
run established nothing, because with synthetic metadata it accepted an SFT
objective sitting in the CF directory and a missing hub field -- the same "passes
by doing nothing" failure the guard existed to prevent.  So every check in
compare.validate() is exercised here through a mutation of the REAL baseline run
file, and each mutation must produce a problem naming that check.  The unmutated
pair must produce none, so the test cannot pass by rejecting everything.

Validation only; no contract suite is executed, so this test is cheap.
"""

import json
import sys
from pathlib import Path

import pytest

ANALYSIS = Path(__file__).resolve().parents[1] / "results/a-screen/analysis"
BASE = Path(__file__).resolve().parents[1] / "results/a-screen/runs/off-oldrunner.jsonl"
sys.path.insert(0, str(ANALYSIS))

pytestmark = pytest.mark.skipif(
    not BASE.exists() or not (ANALYSIS / "compare.py").exists(),
    reason="the a-screen baseline run or its analysis is not present",
)


def _compare():
    import compare

    return compare


def _rows():
    return [json.loads(x) for x in BASE.read_text().splitlines() if x.strip()]


def _write(tmp, name, rows):
    p = tmp / name
    p.write_text("".join(json.dumps(r) + "\n" for r in rows))
    return str(p)


def _second_arm(rows, **identity):
    """A synthetic second arm: the baseline relabelled, with adapter fields set.

    It is a FIXTURE for the guard, never an arm in any comparison; the outcome
    columns are the baseline's own and mean nothing.
    """
    out = []
    for r in rows:
        r = json.loads(json.dumps(r))
        r["arm"] = "sft"
        r["identity"] = dict(
            r["identity"],
            adapter="/fixture/sft",
            adapter_sha256="fixture",
            adapter_steps=118,
            adapter_config_sha256="fixture",
            pilot_adapter=False,
            **identity,
        )
        out.append(r)
    return out


@pytest.fixture
def pair(tmp_path):
    rows = _rows()
    return rows, _second_arm(rows)


def _validate(tmp_path, a_rows, b_rows, exception=""):
    c = _compare()
    pa = _write(tmp_path, "a.jsonl", a_rows)
    pb = _write(tmp_path, "b.jsonl", b_rows)
    return c.validate([pa, pb], exception)[3]


def test_clean_pair_raises_no_problem(tmp_path, pair):
    """The guard must not pass by rejecting everything."""
    a, b = pair
    assert _validate(tmp_path, a, b) == []


def test_same_file_twice_is_refused(tmp_path, pair):
    a, _ = pair
    problems = _validate(tmp_path, a, a)
    assert any("appears in two files" in p for p in problems), problems


def test_a_single_arm_is_refused(tmp_path, pair):
    a, _ = pair
    c = _compare()
    problems = c.validate([_write(tmp_path, "a.jsonl", a)], "")[3]
    assert any("at least two arms" in p for p in problems), problems


def test_a_missing_record_is_refused(tmp_path, pair):
    a, b = pair
    problems = _validate(tmp_path, a, b[:-1])
    assert any("INCOMPLETE" in p for p in problems), problems


def test_a_duplicated_record_is_refused(tmp_path, pair):
    a, b = pair
    problems = _validate(tmp_path, a, b + [b[0]])
    assert any("duplicate record" in p for p in problems), problems


def test_a_foreign_session_is_refused(tmp_path, pair):
    a, b = pair
    stray = json.loads(json.dumps(b[0]))
    stray["session"] = "S99"
    problems = _validate(tmp_path, a, b + [stray])
    assert any("outside the declared session set" in p for p in problems), problems


def test_different_session_sets_are_refused(tmp_path, pair):
    a, b = pair
    b = _second_arm(_rows(), sessions=[s["identity"]["sessions"][0] for s in b[:1]])
    problems = _validate(tmp_path, a, b)
    assert any("different session sets" in p for p in problems), problems


@pytest.mark.parametrize(
    "field", ["pool_sha256", "a_screen_sha256", "contracts_sha256", "hub_sha256",
              "prompt_budget", "max_new", "deadline_s"]
)
def test_every_non_adapter_identity_field_is_checked(tmp_path, pair, field):
    a, _ = pair
    b = _second_arm(_rows(), **{field: "MUTATED"})
    problems = _validate(tmp_path, a, b)
    assert any(f"identity.{field}" in p for p in problems), (field, problems)


def test_a_missing_identity_field_is_refused(tmp_path, pair):
    """Astra's exact preflight defect: a field that is absent must not compare equal."""
    a, _ = pair
    b = _second_arm(_rows())
    for r in b:
        r["identity"].pop("hub_sha256")
    problems = _validate(tmp_path, a, b)
    assert any("identity.hub_sha256" in p for p in problems), problems


def test_runner_difference_needs_the_recorded_exception(tmp_path, pair):
    a, _ = pair
    b = _second_arm(_rows(), runner_sha256="MUTATED")
    assert any("identity.runner_sha256" in p for p in _validate(tmp_path, a, b))
    assert _validate(tmp_path, a, b, "the recorded AST-equivalence exception") == []


def test_unequal_training_steps_are_refused(tmp_path):
    rows = _rows()
    a = _second_arm(rows)
    for r in a:
        r["arm"] = "cf"
        r["identity"]["adapter_steps"] = 118
    b = _second_arm(rows)
    for r in b:
        r["identity"]["adapter_steps"] = 95
    problems = _validate(tmp_path, a, b)
    assert any("step-matched" in p for p in problems), problems


def test_a_broken_repository_chain_is_refused(tmp_path, pair):
    a, b = pair
    b = json.loads(json.dumps(b))
    b[1]["repo_before"] = "0" * 16
    problems = _validate(tmp_path, a, b)
    assert any("replay disagrees" in p for p in problems), problems


def test_mixed_arm_labels_in_one_file_are_refused(tmp_path, pair):
    a, b = pair
    b = json.loads(json.dumps(b))
    b[3]["arm"] = "cf"
    problems = _validate(tmp_path, a, b)
    assert any("mixes arms" in p for p in problems), problems


def test_identity_drift_inside_one_file_is_refused(tmp_path, pair):
    a, b = pair
    b = json.loads(json.dumps(b))
    b[5]["identity"]["prompt_budget"] = 9999
    problems = _validate(tmp_path, a, b)
    assert any("identity differs from the first record" in p for p in problems), (
        problems
    )


def test_an_unparsable_line_is_refused(tmp_path, pair):
    a, b = pair
    pa = _write(tmp_path, "a.jsonl", a)
    pb = tmp_path / "b.jsonl"
    pb.write_text("".join(json.dumps(r) + "\n" for r in b) + "{not json\n")
    problems = _compare().validate([pa, str(pb)], "")[3]
    assert any("unparsable" in p for p in problems), problems
