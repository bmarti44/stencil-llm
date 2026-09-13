"""The comparison guard must BITE, and it must bite where Astra broke it.

Round 1 (2026-09-13): 14 mutations, all caught.  Astra then mutated the same
real baseline and got `validate()` to return CLEAN on seven more, every one of
them a route by which a check simply did not run.  Those seven are the core of
this suite; a mutation suite only bounds the axes it thinks to assert, so each
is written from Astra's reproduction rather than from my own idea of what could
go wrong.

The unmutated pair must still pass, so the suite cannot succeed by refusing
everything.  Validation only; no contract suite is executed.
"""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "results/a-screen/analysis"
BASE = ROOT / "results/a-screen/runs/off-oldrunner.jsonl"
sys.path.insert(0, str(ANALYSIS))
sys.path.insert(0, str(ROOT / "scripts"))

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


def _second_arm(rows, identity=None, steps=134):
    """The baseline relabelled, with adapter fields set.  A FIXTURE for the
    guard, never an arm in any comparison."""
    out = []
    for r in rows:
        r = json.loads(json.dumps(r))
        r["arm"] = "sft"
        ident = dict(
            r["identity"],
            adapter="/fixture/sft",
            adapter_sha256="fixture",
            adapter_steps=steps,
            adapter_config_sha256="fixture",
            pilot_adapter=False,
        )
        ident.update(identity or {})
        r["identity"] = ident
        out.append(r)
    return out


@pytest.fixture
def pair():
    rows = _rows()
    return rows, _second_arm(rows)


def _validate(tmp_path, a_rows, b_rows, exception=""):
    c = _compare()
    pa = _write(tmp_path, "a.jsonl", a_rows)
    pb = _write(tmp_path, "b.jsonl", b_rows)
    return c.validate([pa, pb], exception)[3]


def test_the_unmutated_pair_raises_no_problem(tmp_path, pair):
    """The guard must not pass by rejecting everything."""
    a, b = pair
    assert _validate(tmp_path, a, b) == []


# ---------------------------------------------------- Astra's seven escapes


def test_a_session_dropped_from_both_arms_and_both_declarations(tmp_path, pair):
    """Escape 1: completeness was checked against each file's OWN declaration, so
    removing a session everywhere shrank the denominator silently."""
    a, b = pair
    keep = [r for r in a if r["session"] != "S02"]
    for r in keep:
        r["identity"] = dict(r["identity"],
                             sessions=[s for s in r["identity"]["sessions"]
                                       if s != "S02"])
    other = _second_arm(keep)
    problems = _validate(tmp_path, keep, other)
    assert any("frozen manifest" in p for p in problems), problems


def test_a_field_missing_from_both_arms_is_not_agreement(tmp_path, pair):
    """Escape 2: the identity loop compared the UNION of SUPPLIED keys, so a
    field absent on both sides was never compared at all."""
    a, b = pair
    a = json.loads(json.dumps(a))
    for r in a:
        r["identity"].pop("hub_sha256")
    b = _second_arm(_rows())
    for r in b:
        r["identity"].pop("hub_sha256")
    problems = _validate(tmp_path, a, b)
    assert any("missing" in p and "hub_sha256" in p for p in problems), problems


def test_a_corrupted_repo_after_is_refused(tmp_path, pair):
    """Escape 3: only repo_before was verified."""
    a, b = pair
    b = json.loads(json.dumps(b))
    for r in b:
        r["repo_after"] = "0" * 16
    problems = _validate(tmp_path, a, b)
    assert any("repo_after" in p for p in problems), problems


def test_deleted_suite_scores_are_refused(tmp_path, pair):
    """Escape 4: .get() then bool() turned every missing score into a silent
    False, and all 36 preservation outcomes became failures."""
    a, b = pair
    b = json.loads(json.dumps(b))
    for r in b:
        r["scores"] = {}
    problems = _validate(tmp_path, a, b)
    assert any("missing suites" in p for p in problems), problems


def test_a_pilot_adapter_is_refused(tmp_path, pair):
    """Escape 5: a timing-only adapter is not the registered allocation."""
    a, _ = pair
    b = _second_arm(_rows(), identity={"pilot_adapter": True})
    problems = _validate(tmp_path, a, b)
    assert any("pilot-adapter" in p or "pilot_adapter" in p for p in problems), problems


def test_an_adapter_without_a_step_count_is_refused(tmp_path, pair):
    """Escape 6: 'trained' was selected by truthiness, so an absent
    adapter_steps excused an arm from step matching entirely."""
    a, _ = pair
    b = _second_arm(_rows(), steps=None)
    problems = _validate(tmp_path, a, b)
    assert any("adapter_steps" in p for p in problems), problems


def test_an_arbitrary_runner_hash_is_refused_even_with_an_exception(tmp_path, pair):
    """Escape 7: ANY non-empty exception string admitted ANY runner hash.  The
    exception is a statement about one inspected pair."""
    a, _ = pair
    b = _second_arm(_rows(), identity={"runner_sha256": "deadbeefdeadbeef"})
    problems = _validate(tmp_path, a, b, "I inspected it, honest")
    assert any("NOT the inspected pair" in p for p in problems), problems


def test_the_inspected_runner_pair_is_admitted_with_the_exception(tmp_path, pair):
    """...and the real, established pair still works, or the exception is useless."""
    c = _compare()
    real = sorted(c.RUNNER_EXCEPTION_PAIR)
    a = json.loads(json.dumps(_rows()))
    for r in a:
        r["identity"]["runner_sha256"] = real[0]
    b = _second_arm(_rows(), identity={"runner_sha256": real[1]})
    assert _validate(tmp_path, a, b) != []          # refused without the flag
    assert _validate(tmp_path, a, b, "RUNNER-EXCEPTION.md") == []


# ------------------------------------------------------------ round-1 cases


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
    assert problems


def test_a_duplicated_record_is_refused(tmp_path, pair):
    a, b = pair
    problems = _validate(tmp_path, a, b + [b[0]])
    assert any("duplicate record" in p for p in problems), problems


def test_a_foreign_session_is_refused(tmp_path, pair):
    a, b = pair
    stray = json.loads(json.dumps(b[0]))
    stray["session"] = "S99"
    problems = _validate(tmp_path, a, b + [stray])
    assert any("frozen manifest" in p for p in problems), problems


@pytest.mark.parametrize(
    "field", ["pool_sha256", "a_screen_sha256", "contracts_sha256", "hub_sha256",
              "prompt_budget", "max_new", "deadline_s", "hub"]
)
def test_every_shared_identity_field_is_checked(tmp_path, pair, field):
    a, _ = pair
    b = _second_arm(_rows(), identity={field: "MUTATED"})
    problems = _validate(tmp_path, a, b)
    assert any(field in p for p in problems), (field, problems)


def test_unequal_training_steps_are_refused(tmp_path):
    rows = _rows()
    a = _second_arm(rows, steps=134)
    for r in a:
        r["arm"] = "cf"
    b = _second_arm(rows, steps=95)
    problems = _validate(tmp_path, a, b)
    assert any("step-matched" in p for p in problems), problems


def test_a_broken_repository_chain_is_refused(tmp_path, pair):
    a, b = pair
    b = json.loads(json.dumps(b))
    b[1]["repo_before"] = "0" * 16
    problems = _validate(tmp_path, a, b)
    assert any("repo_before" in p for p in problems), problems


def test_mixed_arm_labels_in_one_file_are_refused(tmp_path, pair):
    a, b = pair
    b = json.loads(json.dumps(b))
    b[3]["arm"] = "cf"
    problems = _validate(tmp_path, a, b)
    assert problems


def test_identity_drift_inside_one_file_is_refused(tmp_path, pair):
    a, b = pair
    b = json.loads(json.dumps(b))
    b[5]["identity"]["prompt_budget"] = 9999
    problems = _validate(tmp_path, a, b)
    assert any("identit" in p for p in problems), problems


def test_an_unparsable_line_is_refused(tmp_path, pair):
    a, b = pair
    pa = _write(tmp_path, "a.jsonl", a)
    pb = tmp_path / "b.jsonl"
    pb.write_text("".join(json.dumps(r) + "\n" for r in b) + "{not json\n")
    problems = _compare().validate([pa, str(pb)], "")[3]
    assert any("malformed" in p or "unparsable" in p for p in problems), problems


def test_a_stored_aggregate_that_disagrees_with_its_suites_is_refused(tmp_path, pair):
    """The registered consumer recomputes J and function_only from the individual
    suites and refuses when the stored flag disagrees."""
    a, b = pair
    b = json.loads(json.dumps(b))
    for r in b:
        if r["request"] == 2:
            r["J"] = True
            break
    problems = _validate(tmp_path, a, b)
    assert problems
