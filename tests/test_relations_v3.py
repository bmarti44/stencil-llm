"""Data boundary and registered reading checks; no held-out inputs."""

import copy

import numpy as np
import pytest
from scipy.stats import binom

from scripts import relations_v3 as v


@pytest.fixture(scope="module")
def corpus():
    return v.load()


def test_override_patch_and_dev_exclusion(corpus):
    rows, receipt = corpus
    assert receipt["pairs"] == 8980
    assert receipt["override_retained"] == 1231
    assert not receipt["mechanical_drops"]
    overrides = {r["override_index"]: r for r in rows if "override_index" in r}
    assert overrides[130]["label"] == "none"
    assert overrides[236]["label"] == "reinstates"
    assert overrides[214]["target_span"]["text"] in overrides[214]["message"]
    assert not ({472, 478, 584} & overrides.keys())
    for row in rows:
        span = row["target_span"]
        assert row["message"][span["start"] : span["end"]] == span["text"]
        assert all(
            isinstance(s, str) and s in row["message"] for s in row["new_rule_spans"]
        )
    for seed in range(3):
        fit, dev = v.split(rows, seed)
        assert len(dev) == 898
        assert {r["override_index"] for r in fit if r.get("fit_only")} == v.FIT_ONLY
        assert not any(r.get("fit_only") for r in dev)
        assert any(
            all(overrides[i]["id"] in {r["id"] for r in part} for i in (130, 131))
            for part in (fit, dev)
        )
        assert not ({r["scenario_id"] for r in fit} & {r["scenario_id"] for r in dev})


def test_exact_reading_and_cp():
    rows = [
        dict(row=dict(label="supersedes"), prediction="supersedes") for _ in range(90)
    ]
    rows += [dict(row=dict(label="supersedes"), prediction="none") for _ in range(10)]
    m = v.metrics(rows)
    lo, hi = m["supersedes_cp95"]
    np.testing.assert_allclose(binom.sf(89, 100, lo), 0.025)
    np.testing.assert_allclose(binom.cdf(90, 100, hi), 0.025)
    baseline = copy.deepcopy(m)
    m["accuracy"] = 0.94
    assert v.decision(m, baseline)["verdict"] == "GO"
    m["accuracy"] = 0.939999
    assert v.decision(m, baseline)["verdict"] == "NO-GO"
    m["accuracy"] = 0.94
    m["per_class"]["supersedes"]["recall"] = 0.89999
    assert v.decision(m, baseline)["verdict"] == "NO-GO"
    m["per_class"]["supersedes"]["recall"] = 0.90
    m["per_class"]["none"]["f1"] = baseline["per_class"]["none"]["f1"] - 0.031
    assert v.decision(m, baseline)["verdict"] == "NO-GO"
