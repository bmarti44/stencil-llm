"""Independent saved-record count/status audit; no classifier or GPU inference."""

import json
from collections import Counter
from pathlib import Path

import numpy as np


def main():
    out = Path(__file__).resolve().parent
    bank = json.loads((out / "bank.json").read_text())
    files = sorted((out / "setup-admission/records").glob("*.json"))
    assert len(files) == 96
    counts = {
        label: Counter(gold=0, paired=0, proposed=0, applied=0)
        for label in ("supersedes", "cancels", "completes", "reinstates")
    }
    false = Counter()
    none_probabilities = []
    admission = Counter()
    details, bad_pairs = [], []
    pair_count = 0
    for ep in bank["setup"]:
        for ti, turn in enumerate(ep["turns"]):
            r = json.loads(
                (
                    out / "setup-admission/records" / f"{ep['id']}_C_{ti}.json"
                ).read_text()
            )
            assert r["turn"] == turn and not r["trace"]["overflow"]
            pairs, trace = r["trace"]["pairs"], r["trace"]
            actual = {row["id"]: row for row in trace["after"]}
            expected = {row["id"]: row for row in r["gold_trace"]["after"]}
            pair_count += len(pairs)
            for p in pairs:
                target, span = (
                    p["input"]["target_id"],
                    p["input"]["target_span"]["text"],
                )
                gold = next(
                    (
                        e["label"]
                        for e in turn["events"]
                        if e.get("target") == target and e["span"] == span
                    ),
                    "none",
                )
                assert p["gold"] == gold
                if gold == "none":
                    none_probabilities.append(p["probabilities"][0])
                    if p["applied"] != "none":
                        false[p["applied"]] += 1
                        bad_pairs.append(
                            dict(
                                episode=ep["id"],
                                turn=ti,
                                target=target,
                                label=p["applied"],
                                span=span,
                            )
                        )
            for e in turn["events"]:
                label = e["label"]
                new_id = f"{ti}:{turn['text'].index(e['span'])}"
                target = e.get("target")
                fields = ("id", "text", "scope", "kind", "version", "status")

                def same(rid, actual=actual, expected=expected, fields=fields):
                    return rid in actual and all(
                        actual[rid][k] == expected[rid][k] for k in fields
                    )

                applied_event = any(
                    a["label"] == label
                    and (
                        a.get("target") == target
                        if target
                        else a.get("span") == e["span"]
                    )
                    for a in trace["applied"]
                )
                if label == "admit":
                    group = (
                        "switched_task"
                        if ti
                        else (
                            "initial_order"
                            if e["gold_key"].startswith("order:")
                            else "initial_tag"
                        )
                    )
                    admission[group + "_total"] += 1
                    admission[group + "_applied"] += int(applied_event and same(new_id))
                    continue
                matching = [
                    p
                    for p in pairs
                    if p["input"]["target_id"] == target
                    and p["input"]["target_span"]["text"] == e["span"]
                ]
                assert len(matching) == 1
                p = matching[0]
                good = (
                    applied_event
                    and same(target)
                    and (same(new_id) if label == "supersedes" else True)
                )
                counts[label].update(
                    gold=1,
                    paired=1,
                    proposed=int(p["proposed"] == label),
                    applied=int(good),
                )
                details.append(
                    dict(
                        episode=ep["id"],
                        label=label,
                        span=e["span"],
                        target=target,
                        proposed=p["proposed"],
                        applied=bool(good),
                        p_gold=p["probabilities"][
                            (
                                "none",
                                "supersedes",
                                "cancels",
                                "completes",
                                "reinstates",
                            ).index(label)
                        ],
                    )
                )
    summary = json.loads((out / "setup-admission/summary.json").read_text())
    for label, values in counts.items():
        assert all(
            summary["diagnostics"]["per_label"][label][k] == v
            for k, v in values.items()
        )
    assert (
        sum(false.values()) == summary["diagnostics"]["gold_none"]["applied_positive"]
    )
    assert len(none_probabilities) == summary["diagnostics"]["gold_none"]["total"]
    assert (
        sum(c["applied"] for c in counts.values())
        == summary["counts"]["transitions"]["passed"]
    )
    cutoff = json.loads((out / "calibration.json").read_text())["chosen"]["threshold"]
    assert max(none_probabilities) < cutoff
    assert not (out / "started.json").exists() and not (out / "gate").exists()
    assert not (out / "RUNNING.flag").exists()
    verdict = json.loads((out / "summary.json").read_text())
    assert (
        verdict["verdict"] == "INELIGIBLE-ADMISSION"
        and verdict["gpu_held_seconds"] == 0
    )
    result = dict(
        audit="PASS",
        records=96,
        pairs=pair_count,
        transition_counts=counts,
        admission_counts=admission,
        false_applications=false,
        false_application_episodes=len({p["episode"] for p in bad_pairs}),
        false_application_details=bad_pairs,
        gold_transition_details=details,
        gold_none_max=float(np.max(none_probabilities)),
        cutoff=cutoff,
        no_gpu_or_gate=True,
    )
    (out / "independent-audit.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps({k: v for k, v in result.items() if "details" not in k}))


if __name__ == "__main__":
    main()
