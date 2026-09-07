"""Amendment 5 tests use DEV-derived synthetic schedules; no eval bank access."""

import copy
import importlib
from dataclasses import replace
from pathlib import Path

import pytest
from test_focus_slab2_amendment4 import synthetic

from stencil.focus import slab2_endpoint as ep


def larger():
    dev, rows = synthetic()
    episodes, records = [], []
    ids = [f"synthetic-{i:02}" for i in range(64)]
    for i, eid in enumerate(ids):
        base = dev[i % 8]
        episodes.append(replace(base, episode_id=eid))
        for row in rows:
            if row["episode_id"] == base.episode_id and (row["arm"] != "Q" or i < 16):
                records.append({**copy.deepcopy(row), "episode_id": eid})
    return episodes, records, ids[:16]


def test_larger_exact_conjunction_and_episode_counts():
    episodes, rows, q = larger()

    def reading():
        return ep.larger_reading(rows, episodes, q, cpu_control=True)

    out = reading()
    assert out["reading"] == "PASS" and out["actual_records"] == 3328
    assert out["primary"]["families"]["delivery"]["holm_p"] == 3 / 2**64
    assert out["per_arm"]["R"]["broken"] == 64
    assert out["per_arm"]["R"]["joint_final"] == 0  # descriptive, never a gate
    assert ep.larger_reading(rows, episodes, q, cpu_control=False)["reading"] == "FAIL"
    assert (
        ep.larger_reading(rows[:-1], episodes, q, cpu_control=True)["reading"]
        == "INCOMPLETE"
    )
    # More than two compact emissions within one episode do not gate.
    for r in rows:
        if r["episode_id"] == episodes[0].episode_id and r["arm"] == "R":
            r["output"] += " delivery=ready"
    assert reading()["reading"] == "PASS"
    assert reading()["per_arm"]["R"]["compact_ready"] == 1
    for r in rows:
        if r["arm"] == "N" and r["episode_id"] == episodes[0].episode_id:
            r["outcome"]["diagnostics"]["breakage"] = False
    assert reading()["reading"] == "PASS"  # +1 accepted
    for r in rows:
        if r["arm"] == "N" and r["episode_id"] == episodes[1].episode_id:
            r["outcome"]["diagnostics"]["breakage"] = False
    assert reading()["reading"] == "FAIL"  # +2 rejected


def test_delivery_required_not_any_significant_family():
    episodes, rows, q = larger()
    for row in rows:
        row["outcome"]["satisfied"]["delivery"] = True
    out = ep.larger_reading(rows, episodes, q, cpu_control=True)
    assert out["primary"]["families"]["format"]["pass"]
    assert out["reading"] == "FAIL"
    with pytest.raises(ValueError):
        ep.larger_reading(rows + [rows[0]], episodes, q, cpu_control=True)
    with pytest.raises(ValueError):
        ep.larger_reading(rows, episodes, q[:-1], cpu_control=True)


def test_control_saved_hashes_and_scheduled_dev(monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "scripts"))
    runner = importlib.import_module("larger_test")
    result = runner.composition_control(runner.s.bank())
    assert result["passed"] and result["historical_hashes_exact"] == 35
    assert result["scheduled_compact"] == 35 and result["episode_count"] == 8


def test_actual_runner_records_before_summary(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[1] / "scripts"))
    runner = importlib.import_module("larger_test")
    monkeypatch.setattr(runner, "OUT", tmp_path)
    monkeypatch.setattr(runner.p, "LOCAL", tmp_path / "local")
    monkeypatch.setattr(runner.p, "factory", runner.d.stub_factory)
    episodes, _, q = larger()
    # Synthetic IDs renamed only for collector glob, DEV source still explicit.
    episodes = [
        replace(e, episode_id=f"slab2-eval-{i:02}") for i, e in enumerate(episodes)
    ]
    registration = dict(
        q_ids=[e.episode_id for e in episodes[:16]],
        episode_hashes={e.episode_id: e.manifest()["episode_sha256"] for e in episodes},
        schedule=[dict(id=0, arm="R", ids=[e.episode_id for e in episodes[:4]])],
        replay_after_group=99,
    )
    groups = runner.run_bank(episodes, registration)
    assert not groups[0]["errors"]
    out = runner.collect(episodes, registration, True)
    assert out["reading"] == "INCOMPLETE" and out["actual_records"] == 64
    import json

    rows = [
        json.loads(x) for x in (tmp_path / "records-R.jsonl").read_text().splitlines()
    ]
    assert all(
        {"output_sha256", "text_sha256", "output_ids", "execution", "outcome", "timing"}
        <= r.keys()
        for r in rows
    )
