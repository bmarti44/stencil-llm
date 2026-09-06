"""Replay saved v3 scores and runtime state; never run model inference."""

from __future__ import annotations

import importlib.util
import json
import sys
from unittest.mock import patch

import numpy as np
from scipy.stats import binom

from scripts import relations_v3 as v


def records(path):
    return [json.loads(line) for line in path.read_text().splitlines()]


def audit_scores(saved, policy):
    for r in saved:
        assert r["model_input_sha256"] == v.tr.digest(v.tr.render_pair(r["row"]))
        z = np.array(r["logits"])
        probs = np.exp(z - z.max()) / np.exp(z - z.max()).sum()
        np.testing.assert_allclose(probs, r["probabilities"], atol=1e-12)
        winner = int(np.argmax(probs))
        if r["overflow"] or (
            winner and probs[winner] < policy["thresholds"][v.tr.LABELS[winner]]
        ):
            winner = 0
        assert r["prediction"] == v.tr.LABELS[winner]
        assert r["gold"] == r["row"]["label"]


def main():
    v.verify_freeze()
    counts = json.loads((v.RUN / "data-counts.json").read_text())
    dev_counts = []
    for seed in range(3):
        model = v.OUT / f"seed{seed}"
        arrays = dict(np.load(model / "dev_predictions.npz", allow_pickle=False))
        table = json.loads((model / "operating-point.json").read_text())
        assert table == v.v2.calibrate(arrays)
        saved = records(model / "dev-records.jsonl")
        assert [r["row"]["id"] for r in saved] == counts["splits"][str(seed)][
            "development"
        ]["ids"]
        assert v.tr.digest([r["row"] for r in saved]) == arrays["split_sha256"].item()
        np.testing.assert_array_equal([r["logits"] for r in saved], arrays["logits"])
        np.testing.assert_array_equal(
            [r["overflow"] for r in saved], arrays["overflow"]
        )
        assert not any(r["row"].get("fit_only") for r in saved)
        audit_scores(saved, table["arms"]["C"]["policy"])
        dev_counts.append(len(saved))
    policy = json.loads((v.OUT / "seed0/operating-point.json").read_text())["arms"][
        "C"
    ]["policy"]
    evaluation_counts = {}
    for number in [3, 2]:
        saved = records(v.OUT / f"heldout{number}-records.jsonl")
        audit_scores(saved, policy)
        summary = json.loads((v.OUT / f"heldout{number}-metrics.json").read_text())
        measured = v.metrics(saved)
        assert all(summary[k] == value for k, value in measured.items())
        k = summary["confusion_gold_by_prediction"][1][1]
        n = summary["per_class"]["supersedes"]["support"]
        lo, hi = summary["supersedes_cp95"]
        if k:
            np.testing.assert_allclose(binom.sf(k - 1, n, lo), 0.025)
        if k < n:
            np.testing.assert_allclose(binom.cdf(k, n, hi), 0.025)
        evaluation_counts[str(number)] = len(saved)
    spec = importlib.util.spec_from_file_location(
        "stencil._v3_audit_runtime", v.RUN / "runtime-v2.py"
    )
    f = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = f
    spec.loader.exec_module(f)
    f.ROOT = v.ROOT
    replayed, regressions, improvements = [], [], []
    with patch.object(v.v2.v5, "f", f):
        for ep in json.loads(v.v2.BANK.read_text())["setup"]:
            clf = v.v2.v5.SavedClassifier()
            clf.thresholds = policy["thresholds"]
            clf.admission_bound = "positive_proposal"
            runtime, oracle = f.Runtime(clf), f.Oracle()
            for ti, turn in enumerate(ep["turns"]):
                name = f"{ep['id']}_C_{ti}.json"
                rec = json.loads((v.RUN / "records" / name).read_text())
                clf.record = rec
                # SavedClassifier's consumption contract is checked below.
                current = v.v2.v5.record_turn(ep, ti, turn, runtime, oracle)
                assert current == rec, name
                replayed.append(rec)
                old = json.loads(
                    (
                        v.ROOT / "results/quick-checks/focus3-gate/v6/records" / name
                    ).read_text()
                )
                for a, b in zip(old["event_checks"], rec["event_checks"], strict=True):
                    if a["label"] not in v.tr.LABELS[1:]:
                        continue
                    if a["passed"] and not b["passed"]:
                        regressions.append(dict(episode=ep["id"], turn=ti, event=b))
                    if b["passed"] and not a["passed"]:
                        improvements.append(dict(episode=ep["id"], turn=ti, event=b))
    assert v.v2.v5.eligibility_summary(replayed) == json.loads(
        (v.RUN / "runtime-summary.json").read_text()
    )
    result = dict(
        dev_records=dev_counts,
        heldout_records=evaluation_counts,
        runtime_records=len(replayed),
        regressions=regressions,
        improvements=improvements,
        audit="PASS; saved-score and state replay only",
    )
    v.write(v.RUN / "audit.json", result)
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
