"""Real scoped consumer regressions; original bank never model evaluated here."""

import copy
import importlib
from pathlib import Path

import pytest

from stencil.focus import slab2_endpoint as ep
from stencil.focus import slab2_v2 as s


@pytest.fixture
def driver(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "scripts"))
    return importlib.import_module("composition_pilot8_driver")


def envelope(body, t):
    return f"```python {t.path}\n{body}```\nreport: task={t.task} status=ok"


def test_literal_hybrid_and_top_level_anchor(tmp_path):
    e = s.generate_episode()
    s.materialize(e, tmp_path)
    ex = s.Executor(tmp_path, e)
    t = e.turns[0]
    original = ex.last_parsable[t.path]
    body = f'def {t.function}(x):\n    """doc"""\n  result = x\n  return result\n'
    result = ex.run(envelope(body, t), 0)
    assert result["syntax_type"] == "IndentationError"
    assert result["offending_line"] == "  result = x\n"
    assert (tmp_path / t.path).read_text() == original
    body = f'  def {t.function}(x):\n    """doc"""\n    return x\n'
    result = ex.run(envelope(body, t), 0)
    assert s.file_written(dict(execution=result, truncated=False))
    assert (tmp_path / t.path).read_text().startswith(original)
    assert "\ndef " + t.function in (tmp_path / t.path).read_text()


def test_scope_and_semantic_exclusion(tmp_path):
    e = s.generate_episode()
    s.materialize(e, tmp_path)
    ex = s.Executor(tmp_path, e)
    t = e.turns[0]
    old = ex.last_parsable.copy()
    result = ex.run(
        envelope(f"def {t.function}(x):\n  return x\ndef other(x):\n  return x\n", t), 0
    )
    assert result["breakage"] and not result["executed"]
    assert old == ex.last_parsable
    result = ex.run(envelope(f"def {t.function}(x):\n  return 1 / 0\n", t), 0)
    out = s.check(e, 0, ex)
    assert not result["breakage"] and not out["diagnostics"]["breakage"]
    assert not out["integration"] and out["diagnostics"]["semantic"]


@pytest.mark.parametrize("arm", list("RNTQ"))
@pytest.mark.parametrize("repair_ok", [True, False])
def test_one_repair_real_consumer(tmp_path, driver, arm, repair_ok):
    e = s.generate_episode()
    calls = {}
    prompts = []

    def factory(e, a, i):
        def decode(rendered):
            calls[i] = calls.get(i, 0) + 1
            prompts.append(rendered.text)
            if i == 0 and (calls[i] == 1 or not repair_ok):
                from stencil.focus.loop import DecodeResult

                t = e.turns[i]
                out = envelope(f'def {t.function}(x):\n    """doc"""\n  return x\n', t)
                return DecodeResult(
                    out, tuple(s.qwen_encode(out)), eos=151645, truncated=False
                )
            return driver.stub_factory(e, a, i)(rendered)

        return decode

    result = (driver.run_q if arm == "Q" else driver.run_lane)(
        tmp_path / arm, e, arm, factory
    )
    rows = result["records"]
    assert len(rows) == 16 and calls[0] == 2
    assert rows[0]["repairs_used"] == 1 and len(rows[0]["attempts"]) == 2
    assert rows[0]["execution"].get("category") == (
        None if repair_ok else "syntax_error"
    )
    assert rows[0]["outcome"]["diagnostics"]["breakage"] != repair_ok
    assert any("IndentationError:" in p and "  return x" in p for p in prompts)
    assert all(calls[i] == 1 for i in range(1, 16))


def test_fresh_bank_disjoint():
    fresh = s.bank("eval")
    receipt = s.lineage_receipt(fresh)
    assert len(fresh) == 64 and all(not v["overlap"] for v in receipt.values())
    assert all(len(e.turns) == 16 for e in fresh)
    with pytest.raises(AssertionError):
        s.lineage_receipt(s.old.bank("eval"))


def test_harm_primary_and_noncompliance():
    from test_focus_slab2_amendment4 import synthetic

    episodes, rows = synthetic()
    rows = copy.deepcopy(rows)
    for r in rows:
        r.update(indent_attempted=True, repairs_used=0)
        r["outcome"]["diagnostics"]["breakage"] = False
    assert s.harm(rows, episodes)["calibrated"]
    before = ep.primary(rows, episodes)
    for r in rows:
        if r["arm"] == "T":
            r["outcome"]["diagnostics"]["breakage"] = True
    h = s.harm(rows, episodes)
    assert h["contrasts"]["T"]["signal"] and not h["calibrated"]
    assert ep.primary(rows, episodes) == before
    for r in rows:
        r["indent_attempted"] = False
    h = s.harm(rows, episodes)
    assert not h["calibrated"] and h["contrasts"]["R"]["n"] == 0


def test_pilot_512_real_stub(tmp_path, driver):
    episodes = s.bank()
    rows = [
        r
        for e in episodes
        for a in "RNTQ"
        for r in (driver.run_q if a == "Q" else driver.run_lane)(
            tmp_path / e.episode_id / a, e, a, driver.stub_factory
        )["records"]
    ]
    out = s.pilot_reading(rows, episodes, deterministic=True)
    assert out["reading"] == "FIX-CONFIRMED", out["failures"]
    assert out["harm_calibration"]["calibrated"]
    rows[0]["execution"].update(syntax_type="IndentationError", category="syntax_error")
    assert s.pilot_reading(rows, episodes, deterministic=True)["reading"] == "STOP"


def test_successor_reading_and_negative_control():
    from test_focus_slab2_amendment5 import larger

    episodes, rows, q = larger()
    for r in rows:
        r.update(indent_attempted=True, repairs_used=0)
        r["outcome"]["diagnostics"]["breakage"] = False
    result = s.larger_reading(rows, episodes, q, cpu_control=True, calibrated=True)
    assert result["reading"] == "PASS"
    assert result["primary"] == ep.primary(rows, episodes)
    assert (
        s.larger_reading(rows[:-1], episodes, q, cpu_control=True, calibrated=True)[
            "reading"
        ]
        == "INCOMPLETE"
    )
    for r in rows:
        if r["arm"] == "T":
            r["outcome"]["diagnostics"]["breakage"] = True
    assert (
        s.larger_reading(rows, episodes, q, cpu_control=True, calibrated=True)[
            "reading"
        ]
        == "FAIL"
    )


def test_repair_transport_receipts_not_overwritten(tmp_path, driver, monkeypatch):
    runner = importlib.import_module("larger_test_v2")
    monkeypatch.setattr(runner.p, "LOCAL", tmp_path)
    phases = []

    def factory(e, a, i, phase):
        phases.append(phase)
        path = tmp_path / "http" / phase / e.episode_id / a / f"{i}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}")
        return lambda rendered: None

    monkeypatch.setattr(runner.p, "factory", factory)
    e = s.generate_episode()
    runner.factory(e, "R", 0)(None)
    runner.factory(e, "R", 0)(None)
    assert phases == ["main-attempt1", "main-attempt2"]


def test_splice_replacement_preserves_other_bytes():
    old = "# header\ndef left(x):\n    return x\n\ndef right(x):\n  return x\n"
    new = "def left(x):\n   return x + 1\n"
    assert (
        s.splice(old, new, "left")
        == "# header\n" + new + "\ndef right(x):\n  return x\n"
    )
