#!/usr/bin/env python3
"""FOCUS-3 v5 step A: CPU-only frozen-v4 replay; no fitting or GPU entry point."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from collections import Counter

import numpy as np

from scripts import focus3_gate as g
from scripts import focus3_gate_v4 as v4
from stencil import focus3 as f

OUT = g.ROOT / "results/quick-checks/focus3-gate/v5"
V4 = OUT.parent / "v4"
ARMS = {
    "C": dict(supersedes=0.94, cancels=0.5, completes=0.5, reinstates=0.5),
    "C'": dict(supersedes=0.80, cancels=0.5, completes=0.5, reinstates=0.5),
}


def dev_tables(logits, labels, overflow):
    logits, labels = np.asarray(logits), np.asarray(labels)
    assert logits.shape == (len(labels), 5) and np.isfinite(logits).all()
    assert not np.asarray(overflow).any()
    ex = np.exp(logits - logits.max(axis=1, keepdims=True))
    p = ex / ex.sum(axis=1, keepdims=True)
    none, positive = labels == 0, labels != 0
    assert none.any() and positive.any()
    guard = [
        dict(
            threshold=t,
            none_pass=int((p[none, 0] >= t).sum()),
            none_total=int(none.sum()),
            positive_pass=int((p[positive, 0] >= t).sum()),
            positive_total=int(positive.sum()),
        )
        for t in [0.5, 0.2046, 0.9711621345086118]
    ]
    winners = p.argmax(axis=1)
    sweep = []
    policies = [
        (f"supersedes={t:.2f}", t, None) for t in [0.94, 0.50, 0.90, 0.80, 0.72, 0.70]
    ]
    policies += [
        ("argmax", None, None),
        ("margin=.2", None, 0.2),
        ("margin=.5", None, 0.5),
    ]
    for name, threshold, margin in policies:
        pred = winners.copy()
        if threshold is not None:
            cutoffs = np.array([0.0, threshold, 0.5, 0.5, 0.5])
            pred[p[np.arange(len(p)), winners] < cutoffs[winners]] = 0
        if margin is not None:
            ordered = np.sort(p, axis=1)
            pred[ordered[:, -1] - ordered[:, -2] < margin] = 0
        table = {}
        for i, label in enumerate(f.LABELS[1:], 1):
            total = int((labels == i).sum())
            correct = int(((labels == i) & (pred == i)).sum())
            table[label] = dict(
                correct=correct,
                total=total,
                recall=correct / total if total else None,
                none_fp=int((none & (pred == i)).sum()),
            )
        correct = int((positive & (pred == labels)).sum())
        fp = int((none & (pred != 0)).sum())
        sweep.append(
            dict(
                policy=name,
                correct_positive=correct,
                positive_total=int(positive.sum()),
                recall=correct / int(positive.sum()),
                none_fp=fp,
                none_total=int(none.sum()),
                none_fp_rate=fp / int(none.sum()),
                per_label=table,
            )
        )
    return dict(guard=guard, sweep=sweep, arms=ARMS)


def unauthorized(records):
    details = []
    for r in records:
        remaining = list(r["turn"]["events"])
        for action in r["trace"]["applied"]:
            match = next(
                (
                    i
                    for i, e in enumerate(remaining)
                    if action["label"] == e["label"]
                    and action.get("target") == e.get("target")
                    and action.get("span") == e.get("span")
                ),
                None,
            )
            if match is None:
                details.append(
                    dict(episode=r["episode"], turn_index=r["turn_index"], **action)
                )
            else:
                remaining.pop(match)
    return dict(
        applications=len(details),
        records=len({(r["episode"], r["turn_index"]) for r in details}),
        total_records=len(records),
        per_label=dict(Counter(r["label"] for r in details)),
        details=details,
    )


def eligibility_summary(records):
    result = v4.eligibility_summary(records)
    ids = [(r["episode"], r["turn_index"]) for r in records]
    episodes = {r["episode"] for r in records}
    complete = (
        len(records) == 96
        and len(episodes) == 16
        and len(set(ids)) == 96
        and all(
            {ti for ep, ti in ids if ep == episode} == set(range(6))
            for episode in episodes
        )
    )
    per_label = result["diagnostics"]["per_label"]
    per_label_pass = all(
        per_label[label]["gold"] == 4 and per_label[label]["applied"] >= 3
        for label in ["supersedes", "cancels", "completes"]
    )
    bad = unauthorized(records)
    result.update(
        complete=complete,
        unauthorized=bad,
        per_label_pass=per_label_pass,
        eligible=result["eligible"]
        and complete
        and per_label_pass
        and bad["applications"] == 0,
    )
    return result


def committed_bytes(path):
    return subprocess.check_output(
        ["git", "show", "HEAD:" + str(path.relative_to(g.ROOT))], cwd=g.ROOT
    )


def frozen_models():
    assert committed_bytes(V4 / "freeze.json") == (V4 / "freeze.json").read_bytes()
    freeze = json.loads((V4 / "freeze.json").read_text())
    hashes = {
        p: h
        for p, h in freeze["hashes"].items()
        if p.startswith("data/classifier/model/")
    }
    assert hashes
    for p, digest in hashes.items():
        assert g.digest(g.ROOT / p) == digest, f"frozen v4 model drift: {p}"
    return hashes


def source_hashes():
    paths = [
        "src/stencil/focus3.py",
        "src/stencil/focus2.py",
        "scripts/focus3_gate_v5.py",
        "scripts/focus3_gate_v4.py",
        "scripts/focus3_gate_v3.py",
        "scripts/focus3_gate.py",
        "scripts/train_relations.py",
        "tests/test_focus3_gate_v5.py",
        "tests/test_focus3_gate.py",
        "tests/test_focus3_gate_v4.py",
        "data/classifier/relations/astra-enrich-2.jsonl",
    ]
    paths += [
        str((OUT / name).relative_to(g.ROOT))
        for name in ["registration.md", "dev-tables.json", "deleted-bank-rows.json"]
    ]
    paths += [
        str((V4 / name).relative_to(g.ROOT)) for name in ["bank.json", "freeze.json"]
    ]
    return {p: g.digest(g.ROOT / p) for p in paths}


def prepare():
    assert not (OUT / "freeze.json").exists()
    assert f.THRESHOLDS == ARMS["C"] and f.NONE_PAIR_THRESHOLD == 0.5
    models = frozen_models()
    assert committed_bytes(V4 / "bank.json") == (V4 / "bank.json").read_bytes()
    assert (
        (OUT / "RESULTS.md")
        .read_text()
        .startswith((OUT / "registration.md").read_text())
    )
    z = np.load(v4.DEV, allow_pickle=False)
    table = dev_tables(z["logits"], z["labels"], z["overflow"])
    assert table["guard"][0] == dict(
        threshold=0.5,
        none_pass=217,
        none_total=259,
        positive_pass=5,
        positive_total=317,
    )
    table.update(
        source=str(v4.DEV.relative_to(g.ROOT)),
        source_sha256=g.digest(v4.DEV),
        split_sha256=str(z["split_sha256"]),
    )
    g.write(OUT / "dev-tables.json", table)
    g.write(
        OUT / "freeze.json",
        dict(
            models=models,
            sources=source_hashes(),
            reading=(OUT / "registration.md").read_text(),
            created=time.time(),
            arms=ARMS,
            replay_arm="C",
        ),
    )
    print("V5 STEP A CPU READY; frozen v4 model hashes match", flush=True)


def verify_freeze():
    freeze = json.loads((OUT / "freeze.json").read_text())
    assert freeze["models"] == frozen_models()
    assert freeze["sources"] == source_hashes(), "v5 frozen source drift"
    assert f.THRESHOLDS == ARMS["C"] and f.NONE_PAIR_THRESHOLD == 0.5
    return freeze


def record_turn(ep, ti, turn, runtime, oracle):
    trace = runtime.update(turn["text"], ti)
    gold = oracle.update(turn["text"], ti, turn["events"])
    for p in trace["pairs"]:
        p["gold"] = g.gold_pair_label(p["input"], turn)
    live = runtime.register.live(runtime.task, turn["kind"])
    gold_live = oracle.register.live(oracle.task, turn["kind"])
    return dict(
        episode=ep["id"],
        family=ep["family"],
        arm="C",
        turn_index=ti,
        turn=turn,
        trace=trace,
        gold_trace=gold,
        live=[f.wire(r) for r in live],
        gold_live=[f.wire(r) for r in gold_live],
        agreement=f.agreement(live, gold_live, ep["gold_keys"]),
        event_checks=v4.event_checks(turn, ti, trace, gold),
    )


def replay():
    verify_freeze()
    assert os.environ.get("CUDA_VISIBLE_DEVICES") == "", (
        "explicit CPU environment required"
    )
    assert not (OUT / "started.json").exists(), "setup already replayed"
    g.write(
        OUT / "started.json",
        dict(
            time=time.time(),
            pid=os.getpid(),
            freeze_sha256=g.digest(OUT / "freeze.json"),
        ),
    )
    started, cpu_started = time.monotonic(), time.process_time()
    classifier = f.FrozenClassifier()
    for _, enc, head, _ in classifier.branches.values():
        assert all(p.device.type == "cpu" for m in (enc, head) for p in m.parameters())
    bank = json.loads((V4 / "bank.json").read_text())
    records = []
    for ep in bank["setup"]:
        runtime, oracle = f.Runtime(classifier), f.Oracle()
        episode_records = []
        for ti, turn in enumerate(ep["turns"]):
            r = record_turn(ep, ti, turn, runtime, oracle)
            assert all(
                "model_input" in a and "logits" in a
                for a in r["trace"]["pairs"] + r["trace"]["admissions"]
            )
            g.write(OUT / "records" / f"{ep['id']}_C_{ti}.json", r)
            records.append(r)
            episode_records.append(r)
            g.write(OUT / "traces" / f"{ep['id']}_C.json", episode_records)
        print(json.dumps(dict(episode=ep["id"], records=len(records))), flush=True)
    result = eligibility_summary(records)
    result.update(
        wall_seconds=time.monotonic() - started,
        cpu_seconds=time.process_time() - cpu_started,
        gpu_held_seconds=0,
        generation_records=0,
        gate_records=0,
        pair_count=sum(len(r["trace"]["pairs"]) for r in records),
        admission_span_count=sum(len(r["trace"]["admissions"]) for r in records),
        verdict="ELIGIBLE-STEP-A" if result["eligible"] else "INELIGIBLE-STEP-A",
        freeze_sha256=g.digest(OUT / "freeze.json"),
    )
    g.write(OUT / "summary.json", result)
    verify_freeze()
    print(
        json.dumps(
            {k: result[k] for k in ["verdict", "counts", "unauthorized", "pair_count"]}
        ),
        flush=True,
    )


def audit():
    from scripts import train_relations as trainer

    verify_freeze()
    bank = json.loads((V4 / "bank.json").read_text())
    records = []

    class Replay:
        record = None

        def relations(self, pairs):
            saved = self.record["trace"]["pairs"]
            assert pairs == [p["input"] for p in saved]
            return [
                {
                    k: v
                    for k, v in p.items()
                    if k not in ["input", "gold", "applied", "proposed"]
                }
                for p in saved
            ]

        def admission(self, spans, previous):
            saved = self.record["trace"]["admissions"]
            assert spans == [p["span"] for p in saved]
            assert [list(p) for p in f.admission_inputs(spans, previous)] == [
                p["model_input"] for p in saved
            ]
            return [
                {k: v for k, v in p.items() if k not in ["span", "start", "accepted"]}
                for p in saved
            ]

    for ep in bank["setup"]:
        classifier = Replay()
        runtime, oracle = f.Runtime(classifier), f.Oracle()
        episode_records = []
        for ti, turn in enumerate(ep["turns"]):
            r = json.loads((OUT / "records" / f"{ep['id']}_C_{ti}.json").read_text())
            for p in r["trace"]["pairs"]:
                value = p["input"]
                normalized = trainer.normalize_row(
                    dict(value, label=p["gold"], author="astra")
                )
                assert not normalized["span_offsets_repaired"]
                assert f.pair_input(value) == trainer.render_pair(normalized)
                assert list(f.pair_input(value)) == p["model_input"]
                assert value["old_rule"]["scope"] in [
                    "global",
                    "task:"
                    + f.scope_of(
                        value["target_span"]["text"],
                        f.selected_task(turn["text"], runtime.task),
                    ),
                ]
            for p in r["trace"]["pairs"] + r["trace"]["admissions"]:
                logits = np.asarray(p["logits"], dtype=np.float64)
                ex = np.exp(logits - logits.max())
                np.testing.assert_allclose(
                    ex / ex.sum(), p["probabilities"], atol=1e-12, rtol=1e-12
                )
                assert not p["overflow"]
            classifier.record = r
            assert record_turn(ep, ti, turn, runtime, oracle) == r, (ep["id"], ti)
            records.append(r)
            episode_records.append(r)
        assert episode_records == json.loads(
            (OUT / "traces" / f"{ep['id']}_C.json").read_text()
        )
    summary = json.loads((OUT / "summary.json").read_text())
    assert all(summary[k] == v for k, v in eligibility_summary(records).items())
    assert summary["pair_count"] == sum(len(r["trace"]["pairs"]) for r in records)
    assert summary["admission_span_count"] == sum(
        len(r["trace"]["admissions"]) for r in records
    )
    assert len(list((OUT / "records").glob("*.json"))) == len(records) == 96
    z = np.load(v4.DEV, allow_pickle=False)
    table = json.loads((OUT / "dev-tables.json").read_text())
    assert all(
        table[k] == v
        for k, v in dev_tables(z["logits"], z["labels"], z["overflow"]).items()
    )
    result = dict(
        audit="PASS",
        records=96,
        traces=16,
        runtime_replay=True,
        trainer_rendering_parity=True,
        softmax_recomputed=True,
        dev_tables_recomputed=True,
        frozen_v4_models_match=True,
        record_sha256={
            p.name: g.digest(p) for p in sorted((OUT / "records").glob("*.json"))
        },
    )
    g.write(OUT / "audit.json", result)
    print(
        "V5 CPU audit PASS: 96 records, 16 traces, runtime/trainer/softmax/DEV parity",
        flush=True,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", required=True, choices=["prepare", "replay", "audit"])
    args = parser.parse_args()
    globals()[args.mode]()


if __name__ == "__main__":
    main()
