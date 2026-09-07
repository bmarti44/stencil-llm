"""Amendment6b feedback through the real retained-history consumer."""

import copy
import importlib
from pathlib import Path

import pytest

from stencil.focus import slab2_endpoint as ep
from stencil.focus import slab2_v2 as s
from stencil.focus.loop import DecodeResult


@pytest.mark.parametrize("arm", list("RNT"))
@pytest.mark.parametrize("cause", ["scope_violation", "fence_syntax"])
def test_rejection_feedback_then_corrected_write(tmp_path, monkeypatch, arm, cause):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "scripts"))
    d = importlib.import_module("composition_pilot8_driver")
    e = s.generate_episode()
    seen = []

    def factory(e, a, i):
        def decode(rendered):
            seen.append(rendered.text)
            good = d.stub_factory(e, a, i)(rendered)
            if i:
                return good
            output = good.text
            if cause == "scope_violation":
                output = output.replace(
                    "\n```", "\ndef identity(x):\n  return x\n```", 1
                )
            else:
                output = output.replace("```python ", "```python #", 1)
            return DecodeResult(
                output, tuple(s.qwen_encode(output)), eos=151645, truncated=False
            )

        return decode

    rows = d.run_lane(tmp_path / arm, e, arm, factory)["records"]
    feedback = rows[0]["execution"]
    assert feedback["category"] == cause
    assert feedback["fences_seen"] == 2
    assert (
        f"emit only the function {e.turns[0].function}, nothing else"
        in feedback["expected_shape"]
    )
    assert f"```python {e.turns[0].path}" in feedback["expected_shape"]
    assert "whole Python file" not in feedback["expected_shape"]
    assert feedback["expected_shape"] in seen[1]
    if cause == "scope_violation":
        assert feedback["extra_definitions"] == ["identity"]
        assert "identity" in feedback["error"]
    assert rows[0]["repairs_used"] == 0
    assert s.file_written(rows[1])


def test_scoped_rejection_does_not_call_old_executor(tmp_path, monkeypatch):
    e = s.generate_episode()
    s.materialize(e, tmp_path)
    ex = s.Executor(tmp_path, e)

    def forbidden(*args, **kwargs):
        pytest.fail("old executor called on rejected scoped output")

    monkeypatch.setattr(s.old.Executor, "run", forbidden)
    for text, truncated in [
        ("```python #policy.py\nx\n```", False),
        ("unfinished", True),
    ]:
        result = ex.run(text, 0, truncated=truncated)
        assert ex.result is result and result["breakage"]
        assert result["fences_seen"] == text.count("```")
        assert ex.changed == "" and ex.report == {} and ex.path is None


def test_one_scoped_system_example():
    assert s.SYSTEM_PROMPT.count("```python ") == 1
    assert "```python #" not in s.SYSTEM_PROMPT
    assert "def identity" not in s.SYSTEM_PROMPT
    assert "emit only the function" in s.SYSTEM_PROMPT
    assert "nothing else" in s.SYSTEM_PROMPT


def test_real_dev_coverage_feasibility_and_negative_control():
    episodes = s.bank()
    assert all(len(ep.change_rounds(e)["indent"]) == 2 for e in episodes)
    rows = [
        dict(
            episode_id=e.episode_id,
            arm=a,
            turn=t,
            indent_attempted=True,
            outcome={"diagnostics": {"breakage": False}},
        )
        for e in episodes
        for a in "RNT"
        for t in ep.change_rounds(e)["indent"]
    ]
    result = s.harm(rows, episodes)
    assert result["calibrated"]
    assert all(
        c["n"] == 8 and c["p"] == 1 and c["coverage"]
        for c in result["contrasts"].values()
    )
    for arm in "RT":
        harmed = copy.deepcopy(rows)
        for r in harmed:
            r["outcome"]["diagnostics"]["breakage"] = r["arm"] == arm
        result = s.harm(harmed, episodes)
        assert result["contrasts"][arm]["signal"] and not result["calibrated"]
    for r in rows:
        r["indent_attempted"] = False
    assert not s.harm(rows, episodes)["calibrated"]


@pytest.mark.parametrize("cause", ["scope_violation", "fence_syntax"])
def test_same_target_second_submission_preserves_state(tmp_path, cause):
    e = s.generate_episode()
    s.materialize(e, tmp_path)
    ex = s.Executor(tmp_path, e)
    t = e.turns[0]
    original = dict(ex.last_parsable)
    good = (
        f"```python {t.path}\ndef {t.function}(x):\n  return x\n```\n"
        f"report: task={t.task} status=ok"
    )
    bad = (
        good.replace("\n```", "\ndef identity(x):\n  return x\n```", 1)
        if cause == "scope_violation"
        else good.replace("```python ", "```python #", 1)
    )
    feedback = ex.run(bad, 0)
    assert feedback["category"] == cause and ex.result is feedback
    assert ex.history == [] and ex.last_parsable == original
    assert all((tmp_path / p).read_text() == body for p, body in original.items())
    corrected = ex.run(good, 0)
    assert s.file_written(dict(execution=corrected, truncated=False))
    assert len(ex.history) == 1 and ex.prior == []
    assert (tmp_path / t.path).read_text().startswith(original[t.path])
