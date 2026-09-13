"""The adapter preflight must BITE, not merely pass.

Astra's back-on-track review (2026-09-13) found the first version's 13/13
mutation run worthless: with synthetic metadata the guard accepted an SFT
objective sitting in the CF directory, and a log with no `hub` field at all,
because the trunk check simply did not run when the field was absent.  In
--compare, two logs missing the same field counted as agreement, since
`None == None`.

Every one of those is a case here, along with one mutation per check.  The
unmutated fixture must pass, so the suite cannot succeed by refusing everything.
"""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "results/a-screen/analysis"
REAL = ROOT / "results/a-screen/adapters/cf/train-log.json"
sys.path.insert(0, str(ANALYSIS))

pytestmark = pytest.mark.skipif(
    not REAL.exists() or not (ANALYSIS / "preflight.py").exists(),
    reason="no a-screen training log to build the fixture from",
)


def _preflight():
    import preflight

    return preflight


def _base_log():
    """The real cf log, completed.  Its hashes are the current files' hashes, so
    an unmutated fixture must be accepted."""
    log = json.loads(REAL.read_text())
    log["final"] = True
    log["status"] = "complete"
    log["stopped_on"] = "budget"
    return log


def _safetensors(n_tensors=1):
    """A minimal VALID safetensors file: existence is not loadability, so the
    fixture has to be parseable or every test refuses for the wrong reason."""
    header = json.dumps(
        {f"lora_{i}.weight": {"dtype": "F32", "shape": [1], "data_offsets": [0, 4]}
         for i in range(n_tensors)}
    ).encode()
    return len(header).to_bytes(8, "little") + header + b"\x00\x00\x00\x00"


def _adapter(tmp_path, arm, log, weights=None):
    d = tmp_path / arm
    d.mkdir(exist_ok=True)
    (d / "train-log.json").write_text(json.dumps(log))
    (d / "adapter_model.safetensors").write_bytes(
        _safetensors() if weights is None else weights
    )
    return str(d)


@pytest.fixture
def clean(tmp_path):
    return _adapter(tmp_path, "cf", _base_log())


def test_the_unmutated_fixture_is_accepted(clean):
    assert _preflight().check(clean, "cf") == []


def test_the_real_in_progress_checkpoint_is_refused():
    """The live guard on the live directory: a running checkpoint is not eligible."""
    log = json.loads(REAL.read_text())
    if log.get("final"):
        pytest.skip("training has finished; the in-progress case no longer exists")
    bad = _preflight().check(str(REAL.parent), "cf")
    assert any("status" in p for p in bad), bad


def test_an_sft_objective_in_the_cf_directory_is_refused(tmp_path):
    """Astra's first exact defect."""
    log = _base_log()
    log["objective"] = "sft"
    bad = _preflight().check(_adapter(tmp_path, "cf", log), "cf")
    assert any("objective 'sft'" in p for p in bad), bad


def test_a_missing_hub_field_is_refused(tmp_path):
    """Astra's second exact defect: the check that cannot run must not pass."""
    log = _base_log()
    log["identity"].pop("hub")
    bad = _preflight().check(_adapter(tmp_path, "cf", log), "cf")
    assert any("hub is missing" in p for p in bad), bad


@pytest.mark.parametrize("field", ["hub_sha256", "train_pool_sha256", "trainer_sha256",
                                   "a_screen_sha256", "a_train_pool_sha256"])
def test_a_missing_identity_field_is_refused(tmp_path, field):
    log = _base_log()
    log["identity"].pop(field)
    bad = _preflight().check(_adapter(tmp_path, "cf", log), "cf")
    assert any(f"{field} is missing" in p for p in bad), (field, bad)


@pytest.mark.parametrize("field", ["hub_sha256", "train_pool_sha256", "trainer_sha256",
                                   "a_screen_sha256", "a_train_pool_sha256"])
def test_a_stale_identity_hash_is_refused(tmp_path, field):
    log = _base_log()
    log["identity"][field] = "0" * 16
    bad = _preflight().check(_adapter(tmp_path, "cf", log), "cf")
    assert bad, field


@pytest.mark.parametrize("key", ["seed", "lr", "rank", "alpha", "beta",
                                 "dpo_weight", "accum"])
def test_every_registered_recipe_value_is_checked(tmp_path, key):
    log = _base_log()
    log[key] = 12345
    bad = _preflight().check(_adapter(tmp_path, "cf", log), "cf")
    assert any(key in p for p in bad), (key, bad)


@pytest.mark.parametrize("key", ["seed", "lr", "rank", "alpha", "beta",
                                 "dpo_weight", "accum", "steps", "examples",
                                 "budget_seconds", "objective"])
def test_every_registered_recipe_value_must_be_present(tmp_path, key):
    log = _base_log()
    log.pop(key)
    bad = _preflight().check(_adapter(tmp_path, "cf", log), "cf")
    assert any(f"{key} is missing" in p for p in bad), (key, bad)


def test_an_unfinished_run_is_refused(tmp_path):
    log = _base_log()
    log["status"] = "running"
    log["final"] = False
    assert _preflight().check(_adapter(tmp_path, "cf", log), "cf")


def test_zero_steps_is_refused(tmp_path):
    log = _base_log()
    log["steps"] = 0
    bad = _preflight().check(_adapter(tmp_path, "cf", log), "cf")
    assert any("steps" in p for p in bad), bad


def test_an_unmatched_step_count_is_refused(clean):
    real = json.loads(REAL.read_text())["steps"]
    bad = _preflight().check(clean, "cf", require_steps=real + 1)
    assert any("matched" in p for p in bad), bad


def test_a_wrong_allocation_is_refused(tmp_path):
    log = _base_log()
    log["budget_seconds"] = 600
    bad = _preflight().check(_adapter(tmp_path, "cf", log), "cf")
    assert any("budget_seconds" in p for p in bad), bad


def test_a_truncated_pool_is_refused(tmp_path):
    log = _base_log()
    log["identity"]["limit"] = 8
    bad = _preflight().check(_adapter(tmp_path, "cf", log), "cf")
    assert any("limit" in p for p in bad), bad


def test_a_directory_that_does_not_name_the_arm_is_refused(tmp_path):
    bad = _preflight().check(_adapter(tmp_path, "sft", _base_log()), "sft")
    assert any("objective" in p for p in bad), bad


def test_a_different_evaluation_trunk_is_refused(clean):
    bad = _preflight().check(clean, "cf", hub="/some/other/trunk")
    assert any("evaluating on" in p for p in bad), bad


def test_missing_weights_are_refused(tmp_path):
    d = _adapter(tmp_path, "cf", _base_log())
    Path(d, "adapter_model.safetensors").unlink()
    bad = _preflight().check(d, "cf")
    assert any("safetensors" in p for p in bad), bad


def test_a_missing_log_is_refused(tmp_path):
    assert _preflight().check(str(tmp_path / "cf"), "cf")


def test_an_unparsable_log_is_refused(tmp_path):
    d = tmp_path / "cf"
    d.mkdir()
    (d / "train-log.json").write_text("{not json")
    assert _preflight().check(str(d), "cf")


# ----------------------------------------------------------------- compare


def _as_sft(log):
    """The cf log reshaped into a VALID sft log.  Only the cf arm was ever
    trained, so the sft side of every pair is synthetic -- and it has to obey
    the same conventions the real trainer writes, or the clean-pair test fails
    for a fixture reason and stops testing --compare at all (it did: the sft
    side carried the cf run's rejected-side accounting)."""
    log["objective"] = "sft"
    log["rejected_tokens_seen"] = 0  # an sft run never sees a rejected side
    return log


def _pair(tmp_path, mutate_sft=None, mutate_cf=None):
    sft, cf = _as_sft(_base_log()), _base_log()
    for log, mut in ((sft, mutate_sft), (cf, mutate_cf)):
        if mut:
            mut(log)
    a = _adapter(tmp_path, "sft", sft)
    b = _adapter(tmp_path, "cf", cf)
    return a, b


def test_a_clean_pair_is_comparable(tmp_path):
    a, b = _pair(tmp_path)
    assert _preflight().compare(a, b, ("sft", "cf")) == []


def test_each_side_of_the_clean_pair_passes_its_own_arm_check(tmp_path):
    """--compare delegating to check() is only a guard if the fixture's two
    sides really are valid runs of their own arms."""
    a, b = _pair(tmp_path)
    assert _preflight().check(a, "sft") == []
    assert _preflight().check(b, "cf") == []


def test_two_logs_missing_the_same_field_are_not_agreement(tmp_path):
    """Astra's third exact defect: None == None counted as a match."""
    drop = lambda log: log["identity"].pop("hub_sha256")  # noqa: E731
    a, b = _pair(tmp_path, drop, drop)
    bad = _preflight().compare(a, b, ("sft", "cf"))
    assert any("hub_sha256 is missing" in p for p in bad), bad


def test_identical_objectives_are_not_a_contrast(tmp_path):
    a, b = _pair(tmp_path, lambda log: log.update(objective="cf"))
    bad = _preflight().compare(a, b, ("sft", "cf"))
    assert any("not a contrast" in p for p in bad), bad


def test_unmatched_steps_are_refused(tmp_path):
    a, b = _pair(tmp_path, lambda log: log.update(steps=log["steps"] - 7))
    bad = _preflight().compare(a, b, ("sft", "cf"))
    assert any("NOT step-matched" in p for p in bad), bad


def test_unequal_example_counts_are_refused(tmp_path):
    a, b = _pair(tmp_path, lambda log: log.update(examples=99))
    bad = _preflight().compare(a, b, ("sft", "cf"))
    assert any("examples" in p for p in bad), bad


def test_a_differing_trunk_is_refused(tmp_path):
    a, b = _pair(tmp_path, lambda log: log["identity"].update(hub="/other"))
    bad = _preflight().compare(a, b, ("sft", "cf"))
    assert any("hub" in p for p in bad), bad


def test_compare_runs_the_individual_validation(tmp_path):
    """A pair that agrees with each other and with nothing else is not a comparison."""
    a, b = _pair(tmp_path, lambda log: log.update(status="running", final=False),
                 lambda log: log.update(status="running", final=False))
    bad = _preflight().compare(a, b, ("sft", "cf"))
    assert any("status" in p for p in bad), bad


def test_compare_refuses_one_directory_named_twice(tmp_path):
    a, _ = _pair(tmp_path)
    assert _preflight().main(["compare", a, a, "--arms", "sft", "sft"]) == 1


def test_cli_check_returns_zero_on_the_clean_fixture(tmp_path, capsys):
    d = _adapter(tmp_path, "cf", _base_log())
    assert _preflight().main(["check", d, "--arm", "cf"]) == 0
    assert "OK cf" in capsys.readouterr().out


def test_cli_check_returns_one_on_a_mutation(tmp_path, capsys):
    log = _base_log()
    log["objective"] = "sft"
    d = _adapter(tmp_path, "cf", log)
    assert _preflight().main(["check", d, "--arm", "cf"]) == 1
    assert "REFUSE" in capsys.readouterr().out


# ------------------------------------- Astra's four narrower escapes, closed


def test_a_negative_example_count_is_refused(tmp_path):
    """`examples` was only compared against 0, so -1 passed."""
    log = _base_log()
    log["examples"] = -1
    bad = _preflight().check(_adapter(tmp_path, "cf", log), "cf")
    assert any("examples=-1" in p for p in bad), bad


def test_the_example_count_is_bound_to_the_frozen_pool(tmp_path):
    log = _base_log()
    log["examples"] = log["examples"] - 2
    bad = _preflight().check(_adapter(tmp_path, "cf", log), "cf")
    assert any("frozen TRAIN sessions" in p for p in bad), bad


def test_an_absent_limit_is_refused(tmp_path):
    """`limit` was read with .get(), so an ABSENT limit skipped the check."""
    log = _base_log()
    log["identity"].pop("limit")
    bad = _preflight().check(_adapter(tmp_path, "cf", log), "cf")
    assert any("limit is missing" in p for p in bad), bad


def test_a_run_over_its_allocation_is_refused(tmp_path):
    """Nothing bounded elapsed time from ABOVE."""
    log = _base_log()
    log["seconds"] = log["budget_seconds"] * 3
    bad = _preflight().check(_adapter(tmp_path, "cf", log), "cf")
    assert any("allocation" in p for p in bad), bad


@pytest.mark.parametrize("field", ["micro_steps", "discarded_micro_steps",
                                   "completion_tokens_seen", "chosen_tokens_seen",
                                   "rejected_tokens_seen"])
def test_deleted_exposure_accounting_is_refused(tmp_path, field):
    """The whole exposure record could be deleted and the adapter still passed."""
    log = _base_log()
    log.pop(field)
    bad = _preflight().check(_adapter(tmp_path, "cf", log), "cf")
    assert any(f"{field} is missing" in p for p in bad), (field, bad)


def test_inconsistent_microstep_accounting_is_refused(tmp_path):
    log = _base_log()
    log["micro_steps"] = log["micro_steps"] + 3
    bad = _preflight().check(_adapter(tmp_path, "cf", log), "cf")
    assert any("micro_steps" in p for p in bad), bad


def test_zero_training_tokens_are_refused(tmp_path):
    log = _base_log()
    log["completion_tokens_seen"] = 0
    bad = _preflight().check(_adapter(tmp_path, "cf", log), "cf")
    assert any("no tokens were trained on" in p for p in bad), bad


def test_a_cf_run_with_no_rejected_side_is_refused(tmp_path):
    log = _base_log()
    log["rejected_tokens_seen"] = 0
    bad = _preflight().check(_adapter(tmp_path, "cf", log), "cf")
    assert any("rejected side" in p for p in bad), bad


@pytest.mark.parametrize("blob,why", [
    (b"", "empty"),
    (b"abc", "too short for a header length"),
    ((10**9).to_bytes(8, "little") + b"{}", "impossible header length"),
    ((2).to_bytes(8, "little") + b"xx", "header is not JSON"),
    ((2).to_bytes(8, "little") + b"{}", "declares no tensors"),
])
def test_an_unloadable_weight_file_is_refused(tmp_path, blob, why):
    """Existence is not loadability: a truncated save has the right path."""
    d = _adapter(tmp_path, "cf", _base_log(), weights=blob)
    bad = _preflight().check(d, "cf")
    assert any("safetensors" in p for p in bad), (why, bad)


def test_the_real_adapter_still_passes_every_new_check():
    """The guard must not have become one that refuses everything."""
    real = REAL.parent
    log = json.loads(REAL.read_text())
    if not log.get("final"):
        pytest.skip("training has not finished")
    assert _preflight().check(str(real), "cf") == []
