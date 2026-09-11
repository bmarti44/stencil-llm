"""CPU checks for the Exp 2a screen script: seed block, McNemar/Holm, verdict logic."""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def _module():
    spec = importlib.util.spec_from_file_location(
        "w_screen", ROOT / "scripts" / "w_screen.py"
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["w_screen"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_seed_block_is_fresh():
    mod = _module()
    seeds = [mod.SEED0 + i for i in range(64)]
    assert all(14_700_000 <= s < 14_700_100 for s in seeds)
    exposed = set(range(13_400_000, 13_400_400)) | set(range(13_500_000, 13_500_100))
    exposed |= set(range(13_600_000, 13_600_200)) | set(range(13_690_000, 13_690_200))
    assert not exposed & set(seeds)


def test_mcnemar_and_holm():
    mod = _module()
    pairs = [(True, False)] * 8 + [(True, True)] * 10 + [(False, True)] * 0
    r = mod._mcnemar(pairs)
    assert r["first_only"] == 8 and r["second_only"] == 0
    assert r["p_one_sided"] == pytest.approx(0.00390625)
    assert r["p_two_sided"] == pytest.approx(0.0078125)
    holm = mod._holm({"a": 0.001, "b": 0.02, "c": 0.06})
    assert holm["a"]["passed"] and holm["b"]["passed"] and not holm["c"]["passed"]


def _episode(seed, joint, adherent=(True, True), parse=True, exec_ok=True):
    arms = {}
    for arm in ("base", "prose", "fixed_bias", "wave", "wave_where_shuffled"):
        j = joint[arm]
        arms[arm] = {
            "joint_success": j,
            "gains": [],
            "works": {
                "5": {
                    "parse": parse,
                    "exec_ok": exec_ok if j else False,
                    "adherent": list(adherent) if j else [False, True],
                    "active_types": ["prefix", "doc"],
                }
            },
        }
    return {"seed": seed, "arms": arms}


def test_summarize_pass_and_not_demonstrated(tmp_path):
    mod = _module()
    # wave beats everything on 10 discordant episodes, no breakage -> PASS
    for i in range(12):
        j = {
            "base": False,
            "prose": i >= 10,
            "fixed_bias": i >= 10,
            "wave": True,
            "wave_where_shuffled": i >= 10,
        }
        (tmp_path / f"ep-{i}.json").write_text(json.dumps(_episode(i, j)))
    summary = mod.summarize(tmp_path)
    assert summary["verdict"].startswith("PASS")
    assert summary["joint_success"]["wave"] == 12
    assert summary["breakage_excess_over_base"]["wave"]["paired_broken"] == 0
    # wave ties the shuffled control -> NOT-DEMONSTRATED-WHERE
    for p in tmp_path.glob("ep-*.json"):
        p.unlink()
    for i in range(12):
        j = {
            "base": False,
            "prose": False,
            "fixed_bias": False,
            "wave": True,
            "wave_where_shuffled": True,
        }
        (tmp_path / f"ep-{i}.json").write_text(json.dumps(_episode(i, j)))
    summary = mod.summarize(tmp_path)
    assert summary["verdict"].startswith("NOT-DEMONSTRATED-WHERE")
    assert "competence_harm_disclosure" in summary
