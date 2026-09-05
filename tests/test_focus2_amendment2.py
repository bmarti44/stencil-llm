"""Operational adapter boundaries; scientific consumers remain frozen."""

import pytest

from scripts import focus2_amendment2 as a
from stencil import focus2 as f


def test_amended_budget_reaches_eight_hours_and_restores_frozen_runtime():
    original = (
        f.preflight,
        f.GPU_CAP,
        f.Budget,
        f.run_episodes,
        f.analyze,
        f.CONFIG.copy(),
    )
    now = [0.0]
    with a.cost_runtime({}):
        budget = f.Budget(lambda: now[0], spent=571.4905308557209)
        now[0] = 21601
        budget.check()
        now[0] = 28800 - budget.spent
        with pytest.raises(f.Incomplete, match="budget exhausted"):
            budget.check()
        assert (f.run_episodes, f.analyze, f.CONFIG) == original[3:]
    assert (f.preflight, f.GPU_CAP, f.Budget) == original[:3]


def test_adapter_prohibits_pilot_and_preserves_completed_stage(tmp_path, monkeypatch):
    monkeypatch.setattr(f, "ROOT", tmp_path)
    pre = {"spent": 571.49, "projection": 24082.1}
    inputs = (
        f.ROOT / a.BASE / "freeze",
        f.ROOT / a.BASE / "launch-receipt.json",
        f.ROOT / a.BASE / "outputs",
    )
    with a.cost_runtime(pre):
        with pytest.raises(f.Invalid, match="only the registered unstarted final"):
            f.preflight(*inputs[:2], "pilot", inputs[2])
        with pytest.raises(f.Invalid, match="only the registered unstarted final"):
            f.preflight(*inputs[:2], "run", tmp_path)
        assert f.preflight(*inputs[:2], "run", inputs[2]) is pre
        prior = inputs[2] / "run"
        prior.mkdir(parents=True)
        record = prior / "existing-record"
        record.write_text("completed output")
        with pytest.raises(f.Invalid, match="refusing output overwrite/retry"):
            f.execute_stage(*inputs, "run")
        assert record.read_text() == "completed output"


def test_frozen_scheduler_applies_projection_and_sixth_breakage(monkeypatch):
    class Engine:
        def __init__(self):
            self.budget = f.Budget(lambda: 0.0, spent=571.49)

    episodes = [{"bank": "final"}] * 256
    calls = []

    def broken_episode(engine, ep):
        calls.append(ep)
        return [dict(arm="both", flags={"broken": True})]

    monkeypatch.setattr(f, "episode", broken_episode)
    with a.cost_runtime({}):
        assert (
            f.run_episodes(Engine(), episodes, worst_cell_seconds=75.15)
            == "FAIL-SAFETY"
        )
        assert len(calls) == 6
        calls.clear()
        with pytest.raises(f.Incomplete, match="budget exhausted"):
            f.run_episodes(Engine(), episodes, worst_cell_seconds=100)
        assert calls == []
