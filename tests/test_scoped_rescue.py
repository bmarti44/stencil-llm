"""The rescue diagnostic's CPU-testable half: packing, extraction, arithmetic.

No GPU, no model.  Everything here runs before Brian lifts the pause, so that
step 3 is one command and not a debugging session on GPU time.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import scoped_rescue as R  # noqa: E402

from stencil.scoped_blocks import (  # noqa: E402
    oracle_reminder,
    rescue_prompts,
    resolve,
    resolve_events,
)
from stencil.scoped_dev_blocks import BLOCKS  # noqa: E402


def _tok(text):
    return max(1, len(text) // 4)


# ------------------------------------------------------------- extraction


def test_a_fenced_function_is_extracted():
    reply = ("Sure.\n```python\ndef fetch_rate(table, key):\n"
             "    return table.get(key)\n```\n")
    assert R.extract(reply, "fetch_rate") == (
        "def fetch_rate(table, key):\n    return table.get(key)\n")


def test_an_unfenced_function_is_extracted():
    reply = "def fetch_rate(table, key):\n    return table.get(key)\n\nThat's it."
    assert "return table.get(key)" in R.extract(reply, "fetch_rate")


def test_prose_without_a_function_extracts_nothing():
    assert R.extract("I would return None here.", "fetch_rate") == ""


def test_the_wrong_function_name_extracts_nothing():
    reply = "```python\ndef other(table, key):\n    return 1\n```"
    assert R.extract(reply, "fetch_rate") == ""


def test_trailing_prose_after_the_function_is_dropped():
    reply = ("```python\ndef fetch_rate(table, key):\n    return table.get(key)\n"
             "\nprint('hi')\n```")
    assert "print" not in R.extract(reply, "fetch_rate")


# ------------------------------------------------------- the reminder text


def test_the_reminder_quotes_source_text_and_never_the_answer():
    """It supplies the instruction, not a gold patch or an expected value."""
    for block in BLOCKS:
        for case in block.cases:
            text = oracle_reminder(block, case)
            winner, _obs = resolve_events(block.history, case.path, case.fn_kind)
            assert winner is None or winner.text in text
            for banned in ("def ", "return ", "MissingEntry(key)", "table.get"):
                assert banned not in text, (block.id, case.name, banned)


def test_the_reminder_for_a_reinstated_rule_quotes_the_original_statement():
    block = next(b for b in BLOCKS if b.id == "R1")
    text = oracle_reminder(block, block.cases[0])
    assert block.history[0].text in text          # the reinstated original
    assert block.history[1].text not in text      # not the superseded replacement


def test_the_reminder_carries_live_obligations():
    block = next(b for b in BLOCKS if b.id == "R2")
    text = oracle_reminder(block, block.cases[0])
    assert "note()" in text


def test_a_released_obligation_is_not_in_the_reminder():
    block = next(b for b in BLOCKS if b.id == "C3")
    assert "note()" not in oracle_reminder(block, block.cases[0])


# ------------------------------------------------------------- the prompts


@pytest.mark.parametrize("bid", [b.id for b in BLOCKS])
def test_both_conditions_stay_inside_the_shared_ceiling(bid):
    block = next(b for b in BLOCKS if b.id == bid)
    for case in block.cases:
        built = rescue_prompts(block, case, _tok, R.PROMPT_BUDGET)
        for condition in ("off", "oracle"):
            assert built[condition]["tokens"] <= R.PROMPT_BUDGET


def test_the_only_difference_between_the_conditions_is_the_reminder():
    block, case = BLOCKS[0], BLOCKS[0].cases[0]
    built = rescue_prompts(block, case, _tok, R.PROMPT_BUDGET)
    stripped = built["oracle"]["prompt"].replace(
        "\n" + built["oracle"]["reminder"] + "\n", "")
    assert stripped == built["off"]["prompt"]


def test_the_off_prompt_never_contains_the_reminder_header():
    for block in BLOCKS:
        for case in block.cases:
            built = rescue_prompts(block, case, _tok, R.PROMPT_BUDGET)
            assert "Instruction in force" not in built["off"]["prompt"]


def test_the_prompt_carries_the_entering_file_and_the_request():
    block, case = BLOCKS[0], BLOCKS[0].cases[0]
    built = rescue_prompts(block, case, _tok, R.PROMPT_BUDGET)
    assert case.fname in built["off"]["prompt"]
    assert "lookup_price" in built["off"]["prompt"]


def test_no_prompt_leaks_the_block_id_or_the_answer_label():
    for block in BLOCKS:
        for case in block.cases:
            built = rescue_prompts(block, case, _tok, R.PROMPT_BUDGET)
            for condition in ("off", "oracle"):
                text = built[condition]["prompt"]
                assert block.id not in text
                assert "applicable" not in text.lower()
                assert "defeats" not in text.lower()


# ------------------------------------------------------- the whole pipeline


def _stub_run(tmp_path, mode):
    out = tmp_path / f"{mode}.jsonl"
    proc = subprocess.run(  # noqa: S603
        [sys.executable, str(ROOT / "scripts/scoped_rescue.py"), "--stub",
         "--stub-mode", mode, "--out", str(out)],
        capture_output=True, text=True, check=False, cwd=str(ROOT))
    assert proc.returncode == 0, proc.stderr[-2000:]
    recs = [json.loads(x) for x in out.read_text().splitlines() if x.strip()]
    summary = subprocess.run(  # noqa: S603
        [sys.executable, str(ROOT / "scripts/scoped_rescue.py"), "--summarize",
         "--out", str(out)], capture_output=True, text=True, check=False,
        cwd=str(ROOT))
    return recs, summary.stdout


def test_the_pipeline_produces_sixty_four_records(tmp_path):
    recs, _ = _stub_run(tmp_path, "baseline")
    assert len(recs) == 64
    assert len({(r["block"], r["case"], r["condition"]) for r in recs}) == 64


def test_a_correct_answer_passes_every_block(tmp_path):
    """The positive control: without it a systematic extraction bug and a model
    that cannot do the task look identical."""
    _recs, out = _stub_run(tmp_path, "correct")
    assert "off succeeds on 16/16 blocks; oracle on 16/16" in out
    assert "CEILING WARNING" in out


def test_the_arithmetic_reports_rescued_when_it_should(tmp_path):
    _recs, out = _stub_run(tmp_path, "rescue")
    assert "off succeeds on 0/16 blocks; oracle on 16/16" in out
    assert "READING: RESCUED" in out


def test_the_baseline_stub_is_scored_wrong_not_silently_accepted(tmp_path):
    recs, out = _stub_run(tmp_path, "baseline")
    assert "READING: NOT RESCUED" in out
    assert any(not r["ok"] for r in recs)
    assert all(not r["invalid"] for r in recs), "the stub always emits a function"


def test_a_reply_with_no_function_scores_false_without_running_the_scorer():
    result = R.score("S1", 0, "   ")
    assert result["ok"] is False
    assert "no function" in result["error"]


def test_the_scorer_runs_model_output_in_a_separate_process():
    """Untrusted output must not be exec'd in the runner's own process."""
    block = BLOCKS[0]
    value = resolve(block.history, block.cases[0].path, block.cases[0].fn_kind)[0]
    assert value  # sanity
    result = R.score("S1", 0, "def fetch_rate(table, key):\n    raise SystemExit(3)\n")
    assert result["ok"] is False
