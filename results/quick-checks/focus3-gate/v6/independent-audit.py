"""Post-outcome saved-record audit; no model inference or held-out input read."""

import json
import subprocess
from collections import Counter
from pathlib import Path


def main():
    root = Path("/home/bmarti44/stencil-llm")
    v = root / "results/quick-checks/focus3-gate/v6"
    s = json.loads((v / "summary.json").read_text())
    records = [
        json.loads(p.read_text()) for p in sorted((v / "records").glob("*.json"))
    ]
    assert len({(r["episode"], r["turn_index"]) for r in records}) == 96
    unauthorized = []
    authorized = Counter()
    actions = Counter()
    added = changed = 0
    for r in records:
        remaining = list(r["turn"]["events"])
        before = {x["id"]: x for x in r["trace"]["before"]}
        after = {x["id"]: x for x in r["trace"]["after"]}
        assert before.keys() <= after.keys()
        new = after.keys() - before.keys()
        altered = {k for k in before if before[k] != after[k]}
        added += len(new)
        changed += len(altered)
        expected_new = set()
        expected_altered = set()
        for a in r["trace"]["applied"]:
            actions[a["label"]] += 1
            match = next(
                (
                    i
                    for i, e in enumerate(remaining)
                    if all(a.get(k) == e.get(k) for k in ["label", "target", "span"])
                ),
                None,
            )
            if match is None:
                unauthorized.append(
                    dict(episode=r["episode"], turn_index=r["turn_index"], **a)
                )
            else:
                authorized[a["label"]] += 1
                remaining.pop(match)
            if a["label"] in ["admit", "supersedes", "reinstates"]:
                rid = f"{r['turn_index']}:{r['turn']['text'].index(a['span'])}"
                assert rid in new
                expected_new.add(rid)
            if a["label"] in ["cancels", "completes"]:
                rid = a["target"]
                assert after[rid]["status"] == (
                    "cancelled" if a["label"] == "cancels" else "completed"
                )
                expected_altered.add(rid)
            if a["label"] == "supersedes":
                target = a["target"]
                if after[rid]["scope"] in ["*", before[target]["scope"]]:
                    assert after[target]["status"] == "superseded"
                    expected_altered.add(target)
                else:
                    assert after[target] == before[target]
        assert new == expected_new and altered == expected_altered
        for k in altered:
            assert {x: y for x, y in before[k].items() if x != "status"} == {
                x: y for x, y in after[k].items() if x != "status"
            }
    assert unauthorized == s["unauthorized"]["details"]
    assert (
        authorized["admit"] == 35
        and sum(authorized[k] for k in ["supersedes", "cancels", "completes"]) == 11
    )
    thresholds = json.loads((v / "calibration/seed0.json").read_text())["arms"]["C"][
        "policy"
    ]["thresholds"]
    labels = ["none", "supersedes", "cancels", "completes", "reinstates"]
    gold_none = []
    for r in records:
        for p in r["trace"]["pairs"]:
            k = max(range(5), key=lambda i: p["probabilities"][i])
            proposed = (
                labels[k]
                if k
                and p["probabilities"][k] >= thresholds[labels[k]]
                and not p["overflow"]
                else "none"
            )
            assert proposed == p["proposed"]
            if p["gold"] == "none":
                gold_none.append(p)
    assert all(
        not p["overflow"]
        for r in records
        for p in r["trace"]["pairs"] + r["trace"]["admissions"]
    )
    assert not (v / "RUNNING.flag").exists() and not (v / "gate-started.json").exists()
    assert not subprocess.check_output(
        [
            "git",
            "diff",
            "5ad490ca",
            "--",
            "data/classifier/relations",
            "data/classifier/review",
            "data/classifier/model/relations",
        ],
        cwd=root,
    )
    audit = dict(
        audit="PASS",
        authorized=dict(authorized),
        actions=dict(actions),
        unauthorized=unauthorized,
        new_register_rows=added,
        status_changes=changed,
        unexplained_mutations=0,
        gold_none_pairs=len(gold_none),
        gold_none_no_positive_proposal=sum(p["proposed"] == "none" for p in gold_none),
        gold_none_proposed_positive=sum(p["proposed"] != "none" for p in gold_none),
        legacy_guard_field=(
            "summary.diagnostics.gold_none.guard_admitted counts retired "
            "P(none)>=.50, not the v6 guard; descriptive only"
        ),
        gate_not_run=True,
        historical_corpora_and_models_unchanged=True,
    )
    (v / "independent-audit.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
