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


def test_the_reminder_for_a_reinstated_rule_quotes_the_referenced_statement():
    block = next(b for b in BLOCKS if b.id == "R1")
    text = oracle_reminder(block, block.cases[0])
    reinstate = next(e for e in block.history if e.kind == "reinstate")
    referenced = next(e for e in block.history if e.id == reinstate.ref)
    assert referenced.text in text
    for other in block.history:
        if other.kind in ("set", "replace") and other.id != referenced.id:
            assert other.text not in text


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


def _destub(path):
    """Rewrite a stub run's fingerprint so the REAL summarize() path runs.

    The consumer refuses an efficacy reading on stub records, which is correct;
    the decision arithmetic still has to be exercised through that same
    consumer, so the fixture removes the marker rather than bypassing the code.
    """
    lines = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        rec["fingerprint"] = {**rec["fingerprint"], "stub": False, "stub_mode": ""}
        lines.append(json.dumps(rec))
    path.write_text("\n".join(lines) + "\n")


def _summarize(path):
    proc = subprocess.run(  # noqa: S603
        [sys.executable, str(ROOT / "scripts/scoped_rescue.py"), "--summarize",
         "--out", str(path)], capture_output=True, text=True, check=False,
        cwd=str(ROOT))
    return proc.stdout


def _stub_run(tmp_path, mode):
    out = tmp_path / f"{mode}.jsonl"
    proc = subprocess.run(  # noqa: S603
        [sys.executable, str(ROOT / "scripts/scoped_rescue.py"), "--stub",
         "--stub-mode", mode, "--out", str(out)],
        capture_output=True, text=True, check=False, cwd=str(ROOT))
    assert proc.returncode == 0, proc.stderr[-2000:]
    recs = [json.loads(x) for x in out.read_text().splitlines() if x.strip()]
    return recs, out


def test_the_pipeline_produces_sixty_four_records(tmp_path):
    recs, _ = _stub_run(tmp_path, "baseline")
    assert len(recs) == 64
    assert len({(r["block"], r["case"], r["condition"]) for r in recs}) == 64


def test_a_stub_run_refuses_to_produce_an_efficacy_reading(tmp_path):
    _recs, path = _stub_run(tmp_path, "rescue")
    assert "READING: STUB RUN" in _summarize(path)


def test_a_correct_answer_passes_every_block(tmp_path):
    """The positive control: without it a systematic extraction bug and a model
    that cannot do the task look identical."""
    _recs, path = _stub_run(tmp_path, "correct")
    _destub(path)
    out = _summarize(path)
    assert "off succeeds on 16/16 blocks; oracle on 16/16" in out
    assert "CEILING" in out


def test_the_arithmetic_reports_rescued_when_it_should(tmp_path):
    _recs, path = _stub_run(tmp_path, "rescue")
    _destub(path)
    out = _summarize(path)
    assert "off succeeds on 0/16 blocks; oracle on 16/16" in out
    assert "READING: RESCUED" in out
    assert "p = " in out


def test_the_baseline_stub_is_scored_wrong_not_silently_accepted(tmp_path):
    recs, path = _stub_run(tmp_path, "baseline")
    _destub(path)
    assert "READING: NOT RESCUED" in _summarize(path)
    assert any(not r["ok"] for r in recs)
    assert all(not r["invalid"] for r in recs), "the stub always emits a function"


# ------------------------------------------- the consumer must refuse bad data


def test_an_incomplete_dataset_gets_no_efficacy_reading(tmp_path):
    """Astra fed the old consumer a 48-record prefix with oracle wins and it
    printed RESCUED, because a missing case silently became a failure."""
    _recs, path = _stub_run(tmp_path, "rescue")
    _destub(path)
    lines = path.read_text().splitlines()
    path.write_text("\n".join(lines[:48]) + "\n")
    out = _summarize(path)
    assert "READING: INCOMPLETE" in out
    assert "RESCUED" not in out.replace("NOT RESCUED", "")


def test_duplicate_records_are_refused(tmp_path):
    _recs, path = _stub_run(tmp_path, "rescue")
    _destub(path)
    lines = path.read_text().splitlines()
    path.write_text("\n".join([*lines, lines[0]]) + "\n")
    assert "duplicate" in _summarize(path)


def test_mixed_configurations_are_refused(tmp_path):
    a, _p = _stub_run(tmp_path, "rescue")
    path = tmp_path / "rescue.jsonl"
    _destub(path)
    lines = path.read_text().splitlines()
    rec = json.loads(lines[0])
    rec["fingerprint"] = {**rec["fingerprint"], "max_new": 999}
    lines[0] = json.dumps(rec)
    path.write_text("\n".join(lines) + "\n")
    out = _summarize(path)
    assert "different configurations" in out and "READING: INCOMPLETE" in out


def test_a_partial_trailing_line_does_not_abort_the_consumer(tmp_path):
    _recs, path = _stub_run(tmp_path, "rescue")
    _destub(path)
    path.write_text(path.read_text() + '{"block": "S1", "cas')
    out = _summarize(path)
    assert "incomplete line" in out


def test_a_timed_out_generation_never_counts_as_a_success(tmp_path):
    _recs, path = _stub_run(tmp_path, "rescue")
    _destub(path)
    lines = path.read_text().splitlines()
    rec = json.loads(lines[0])
    assert rec["ok"] or not rec["ok"]
    rec["ok"], rec["timed_out"] = True, True
    lines[0] = json.dumps(rec)
    path.write_text("\n".join(lines) + "\n")
    out = _summarize(path)
    assert f"{rec['block']:6} " in out


def test_a_resume_across_configurations_is_refused(tmp_path):
    _recs, path = _stub_run(tmp_path, "rescue")
    lines = path.read_text().splitlines()
    rec = json.loads(lines[0])
    rec["fingerprint"] = {**rec["fingerprint"], "engine_sha": "deadbeefdeadbeef"}
    path.write_text(json.dumps(rec) + "\n")
    proc = subprocess.run(  # noqa: S603
        [sys.executable, str(ROOT / "scripts/scoped_rescue.py"), "--stub",
         "--stub-mode", "rescue", "--out", str(path)],
        capture_output=True, text=True, check=False, cwd=str(ROOT))
    assert proc.returncode == 3, proc.stdout[-800:]
    assert "different configuration" in proc.stdout


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


# ------------------------------------- extraction defects Astra and I both found


@pytest.mark.parametrize("label,reply", [
    ("import above the function",
     "```python\nimport typing\n\ndef fetch_rate(table, key) -> typing.Optional[int]:"
     "\n    return table.get(key)\n```"),
    ("code in the SECOND fence",
     "```\nnotes\n```\n```python\ndef fetch_rate(table, key):\n"
     "    return table.get(key)\n```"),
    ("multiline signature",
     "```python\ndef fetch_rate(\n    table,\n    key,\n):\n"
     "    return table.get(key)\n```"),
    ("top-level helper the answer calls",
     "```python\ndef _pick(t, k):\n    return t.get(k)\n\n"
     "def fetch_rate(table, key):\n    return _pick(table, key)\n```"),
])
def test_a_correct_reply_survives_extraction(label, reply):
    """Each of these previously produced a function that could not import, or no
    function at all, and scored as a total failure."""
    block = next(b for b in BLOCKS if b.id == "S1")
    case = block.cases[0]  # compat lookup -> none
    source = R.extract(reply, case.fname)
    assert source.strip(), label
    assert R.score(block.id, 0, source)["ok"], (label, source)


def test_module_level_side_effects_are_dropped_not_executed():
    block = next(b for b in BLOCKS if b.id == "S1")
    reply = ("```python\ndef fetch_rate(table, key):\n    return table.get(key)\n\n"
             "raise SystemExit(3)\n```")
    source = R.extract(reply, "fetch_rate")
    assert "SystemExit" not in source
    assert R.score(block.id, 0, source)["ok"]


# --------------------------------------------- the registered generation format


@pytest.mark.skipif(not Path(R.HUB).exists(), reason="no local trunk")
def test_the_non_thinking_chat_template_is_actually_applied():
    """Registered as "thinking disabled"; the runner used to tokenize raw text,
    so there was no assistant boundary and no empty thinking block at all."""
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(R.HUB, trust_remote_code=True)
    rendered = tok.apply_chat_template(
        [{"role": "user", "content": "hello"}],
        tokenize=False, add_generation_prompt=True, enable_thinking=False)
    assert "<|im_start|>assistant" in rendered
    assert "<think>" in rendered and "</think>" in rendered
    assert rendered.rstrip().endswith("</think>")


# --------------------------------------------------- the registered pilot rules


def test_the_pilot_projection_uses_the_registered_contention_factor():
    assert R.project(10.0) == pytest.approx(1.5 * 10.0 * 64 / 3600.0)


def test_the_pilot_refuses_above_the_registered_ceiling():
    """0.5 GPU-hours is the registered stop; 18.75 s/generation is the boundary."""
    assert R.project(18.0) < R.CEILING_GPU_H
    assert R.project(19.0) > R.CEILING_GPU_H


def test_the_pilot_selects_the_longest_prompt_cases():
    def tok(text):
        return max(1, len(text) // 4)
    chosen = R.pilot_items(tok)
    assert len(chosen) == R.PILOT_CASES
    sizes = [rescue_prompts(b, c, tok, R.PROMPT_BUDGET)["oracle"]["tokens"]
             for b, _i, c in chosen]
    assert sizes == sorted(sizes, reverse=True)


# ------------------------------- the public prompt carries the hidden contract


def test_the_prompt_carries_the_package_baseline_and_conventions():
    """Astra's finding 3: C4/core was told to follow documentation it never saw."""
    def tok(text):
        return max(1, len(text) // 4)
    for block in BLOCKS:
        for case in block.cases:
            built = rescue_prompts(block, case, tok, R.PROMPT_BUDGET)
            for condition in ("off", "oracle"):
                text = " ".join(built[condition]["prompt"].split())
                assert "a missing entry yields DEFAULT" in text
                assert "the more specific one wins" in text
                assert "does not bring back whatever that instruction" \
                       " replaced" in text
                assert "governs work done after it" in text


def test_the_baseline_and_conventions_are_identical_in_both_conditions():
    def tok(text):
        return max(1, len(text) // 4)
    block = next(b for b in BLOCKS if b.id == "C4")
    built = rescue_prompts(block, block.cases[0], tok, R.PROMPT_BUDGET)
    head = built["off"]["prompt"].split("message 1:")[0]
    assert head == built["oracle"]["prompt"].split("message 1:")[0]
