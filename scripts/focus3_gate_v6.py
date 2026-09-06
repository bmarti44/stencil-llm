"""Registered v6 refit, second look, and one-shot eligibility/gate consumers."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
import time
from collections import Counter

import numpy as np

from scripts import evaluate_relations_heldout2 as h2
from scripts import focus3_gate as g
from scripts import focus3_gate_v5 as v5
from scripts import train_relations as tr
from stencil import focus3 as f
from stencil import relation_operating_point as op

OUT = tr.ROOT / "results/quick-checks/focus3-gate/v6"
MODELS = tr.ROOT / "data/classifier/model/relations-v2"
DATA = tr.ROOT / "data/classifier"
TRAIN = [
    DATA / "relations/kimi-relations.jsonl",
    DATA / "relations/kimi-transitions.jsonl",
]
PATCH = [
    DATA / "review/relations-merged-patch.jsonl",
    DATA / "review/transitions-opus-patch.jsonl",
]
ENRICH = [
    DATA / f"relations/{name}.jsonl"
    for name in ["astra-enrich", "opus-enrich", "astra-enrich-2", "opus-enrich-2"]
]
BANK = tr.ROOT / "results/quick-checks/focus3-gate/v4/bank.json"
LINEAGE = (
    "fit: patched Kimi/original enrich + reviewed transitions + Opus2 +90 Astra2 "
    "evaluation-derived relatives; calibration: scenario-disjoint DEV; "
    "heldout2: disclosed SECOND LOOK diagnostic; setup/gate: development "
    "runtime agreement, shared idioms; admission frozen; no bench/sealed inputs"
)


def load():
    return tr.load_training(TRAIN, PATCH, ENRICH, clean_v2=True)


def split_receipt(rows, seed):
    fit, dev = tr.split_development(rows, seed)
    assert not ({r["scenario_id"] for r in fit} & {r["scenario_id"] for r in dev})
    assert not (
        {t for r in fit for t in tr.group_tokens(r)}
        & {t for r in dev for t in tr.group_tokens(r)}
    )
    return {
        name: dict(
            n=len(part),
            sha256=tr.digest(part),
            labels=dict(Counter(r["label"] for r in part)),
            sources=dict(Counter(r["source_file"] for r in part)),
            ids=[r["id"] for r in part],
        )
        for name, part in [("fit", fit), ("development", dev)]
    }


def sources():
    paths = [
        tr.ROOT / p
        for p in [
            "scripts/focus3_gate_v6.py",
            "scripts/train_relations.py",
            "scripts/evaluate_relations_heldout2.py",
            "scripts/focus3_gate_v5.py",
            "scripts/focus3_gate_v4.py",
            "scripts/focus3_gate.py",
            "src/stencil/focus3.py",
            "src/stencil/focus2.py",
            "src/stencil/relation_operating_point.py",
            "tests/test_focus3_gate_v6.py",
        ]
    ]
    paths += (
        TRAIN
        + PATCH
        + ENRICH
        + [BANK, OUT / "registration.md", OUT / "data-counts.json"]
    )
    paths += [p for p in (DATA / "model/ft").rglob("*") if p.is_file()]
    return {str(p.relative_to(tr.ROOT)): g.digest(p) for p in sorted(paths)}


def prepare():
    assert not (OUT / "recipe-freeze.json").exists()
    rows, receipt = load()
    receipt.update(
        splits={str(s): split_receipt(rows, s) for s in range(3)}, lineage=LINEAGE
    )
    g.write(OUT / "data-counts.json", receipt)
    g.write(
        OUT / "recipe-freeze.json",
        dict(hashes=sources(), created=time.time(), lineage=LINEAGE),
    )
    print(
        json.dumps({k: receipt[k] for k in ["pairs", "final_labels", "final_sources"]}),
        flush=True,
    )


def verify_recipe():
    receipt = json.loads((OUT / "recipe-freeze.json").read_text())
    assert receipt["hashes"] == sources(), "v6 recipe drift"
    return receipt


def calibrate(arrays):
    probs, labels, overflow = op.inputs(
        arrays["logits"], arrays["labels"], arrays["overflow"]
    )
    none = labels == 0
    assert none.any() and (labels != 0).any()
    winners = probs.argmax(axis=1)
    records, policies = [], {}
    for arm in ["C", "C'"]:
        thresholds = {}
        for k, label in enumerate(op.LABELS[1:], 1):
            cap = 0.10 if arm == "C'" and label == "supersedes" else 0.05
            allowance = math.floor(cap * int(none.sum()))
            thresholds[label] = 1.01
            for threshold in op.RULE["threshold_grid"]:
                emitted = (winners == k) & (probs[:, k] >= threshold) & ~overflow
                fp = int((emitted & none).sum())
                tp = int((emitted & (labels == k)).sum())
                records.append(
                    dict(
                        arm=arm,
                        label=label,
                        threshold=threshold,
                        none_fp=fp,
                        none_support=int(none.sum()),
                        true_positive=tp,
                        support=int((labels == k).sum()),
                        cap=cap,
                        allowance=allowance,
                    )
                )
                if (
                    thresholds[label] == 1.01
                    and fp <= allowance
                    and ((labels == k) & ~overflow).any()
                ):
                    thresholds[label] = threshold
        policy = dict(kind="per_class", thresholds=thresholds)
        policies[arm] = dict(
            policy=policy, dev=op.metrics(labels, op.predict(probs, policy, overflow))
        )
    return dict(
        arms=policies,
        curve=records,
        argmax=op.metrics(labels, np.where(overflow, 0, winners)),
    )


def fit():
    verify_recipe()
    assert not (OUT / "fit-started.json").exists()
    g.OUT = OUT
    with g.claim_gpu():
        started = time.monotonic()
        g.write(OUT / "fit-started.json", dict(pid=os.getpid(), time=time.time()))
        for seed in range(3):
            path = MODELS / f"seed{seed}"
            args = tr.parse_args(
                [
                    "--dev-only",
                    "--clean-v2",
                    "--seed",
                    str(seed),
                    "--epochs",
                    "3",
                    "--device",
                    "cuda",
                    "--local-files-only",
                    "--output",
                    str(path),
                    "--train",
                    *map(str, TRAIN),
                    "--patch",
                    *map(str, PATCH),
                    "--enrich",
                    *map(str, ENRICH),
                ]
            )
            tr.train(args)
            manifest = json.loads((path / "manifest.json").read_text())
            assert manifest["budget"]["completed_epochs"] == 3
            assert (
                manifest["budget"]["completed_steps"]
                == manifest["budget"]["planned_steps"]
            )
            arrays = dict(np.load(path / "dev_predictions.npz", allow_pickle=False))
            assert (
                arrays["split_sha256"].item()
                == manifest["split"]["development"]["sha256"]
            )
            table = calibrate(arrays)
            table.update(
                seed=seed, lineage=LINEAGE, split_sha256=arrays["split_sha256"].item()
            )
            g.write(OUT / "calibration" / f"seed{seed}.json", table)
            g.write(path / "operating-point.json", table)
            g.write(
                path / "thresholds.json",
                dict(
                    thresholds=table["arms"]["C"]["policy"]["thresholds"],
                    secondary_thresholds=table["arms"]["C'"]["policy"]["thresholds"],
                    admission_bound="positive_proposal",
                    calibration="DEV only",
                ),
            )
            metrics = json.loads((path / "metrics.json").read_text())
            metrics["v2_dev"] = table["arms"]
            g.write(path / "metrics.json", metrics)
            manifest["data_lineage"] = LINEAGE
            manifest["artifact_sha256"] = {
                str(p.relative_to(path)): g.digest(p)
                for p in sorted(path.rglob("*"))
                if p.is_file() and p.name != "manifest.json"
            }
            g.write(path / "manifest.json", manifest)
            print(
                json.dumps(
                    dict(seed=seed, arms=table["arms"], budget=manifest["budget"])
                ),
                flush=True,
            )
        g.write(
            OUT / "fit-summary.json",
            dict(gpu_held_seconds=time.monotonic() - started, seeds=3),
        )
    verify_recipe()
    g.write(
        OUT / "freeze.json",
        dict(
            recipe=g.digest(OUT / "recipe-freeze.json"),
            models={
                str(p.relative_to(tr.ROOT)): g.digest(p)
                for p in sorted(MODELS.rglob("*"))
                if p.is_file()
            },
            created=time.time(),
            seed_policy="always seed0",
        ),
    )


def verify_freeze():
    verify_recipe()
    freeze = json.loads((OUT / "freeze.json").read_text())
    assert freeze["recipe"] == g.digest(OUT / "recipe-freeze.json")
    assert all(g.digest(tr.ROOT / p) == h for p, h in freeze["models"].items())
    return freeze


def policies():
    return json.loads((MODELS / "seed0/operating-point.json").read_text())["arms"]


def classifier(arm="C"):
    return f.FrozenClassifier(
        MODELS / "seed0", policies()[arm]["policy"]["thresholds"], "positive_proposal"
    )


def second_look():
    verify_freeze()
    assert os.environ.get("CUDA_VISIBLE_DEVICES") == ""
    rows, receipt = load()
    assert (
        receipt["input_sha256"]
        == json.loads((OUT / "data-counts.json").read_text())["input_sha256"]
    )
    import torch
    from safetensors.torch import load_file
    from transformers import AutoModel, AutoTokenizer

    torch.set_num_threads(4)
    path = MODELS / "seed0"
    tok = AutoTokenizer.from_pretrained(path / "encoder", local_files_only=True)
    enc = AutoModel.from_pretrained(path / "encoder", local_files_only=True).eval()
    head = torch.nn.Sequential(
        torch.nn.Dropout(0.1), torch.nn.Linear(enc.config.hidden_size + 4, 5)
    ).eval()
    head.load_state_dict(load_file(str(path / "head.safetensors")))
    with (OUT / "second-look-started.json").open("x") as fp:
        json.dump(
            dict(
                time=time.time(),
                look=2,
                diagnostic_only=True,
                freeze_sha256=g.digest(OUT / "freeze.json"),
            ),
            fp,
        )
        fp.flush()
        os.fsync(fp.fileno())
    started = time.monotonic()
    raw = h2.HELDOUT.read_bytes()
    assert (
        hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        == h2.HELDOUT_BLOB
    )
    heldout = [
        tr.normalize_row(r)
        for r in map(json.loads, raw.decode().splitlines())
        if set(r) != {"summary"}
    ]
    assert len(heldout) == 357 and all(r is not None for r in heldout)
    disjoint = tr.assert_heldout_disjoint(rows, heldout)
    heldout, drops = tr.deduplicate_heldout(heldout)
    assert not drops
    tokens, overflow = tr.encode_rows(heldout, tok)
    logits = np.zeros((len(heldout), 5), dtype=np.float64)
    arms = policies()
    with (OUT / "second-look-records.jsonl").open("x") as fp, torch.inference_mode():
        for start in range(0, len(heldout), 32):
            end = min(start + 32, len(heldout))
            ii = [i for i in range(start, end) if not overflow[i]]
            if ii:
                inputs = tok.pad([tokens[i] for i in ii], return_tensors="pt")
                roles = torch.tensor(
                    [[float(heldout[i]["role"] == r) for r in tr.ROLES] for i in ii]
                )
                logits[ii] = head(
                    torch.cat([enc(**inputs).last_hidden_state[:, 0], roles], dim=1)
                ).numpy()
            records = h2.make_records(
                heldout[start:end],
                logits[start:end],
                overflow[start:end],
                arms["C"]["policy"],
            )
            secondary = h2.make_records(
                heldout[start:end],
                logits[start:end],
                overflow[start:end],
                arms["C'"]["policy"],
            )
            for rec, alt in zip(records, secondary, strict=True):
                rec.update(
                    index=rec["index"] + start,
                    secondary_prediction=alt["prediction"],
                    look=2,
                )
                fp.write(json.dumps(rec, sort_keys=True) + "\n")
            fp.flush()
            os.fsync(fp.fileno())
    measured = {
        arm: h2.score_rows(heldout, logits, overflow, value["policy"])[0]
        for arm, value in arms.items()
    }
    old = [
        json.loads(s)
        for s in (DATA / "model/relations/heldout2-records.jsonl")
        .read_text()
        .splitlines()
    ]
    assert [r["model_input_sha256"] for r in old] == [
        tr.digest(tr.render_pair(r)) for r in heldout
    ]
    prior = op.metrics(
        np.array([tr.LABEL_MAP[r["gold"]] for r in old]),
        np.array([tr.LABEL_MAP[r["prediction"]] for r in old]),
    )
    current = measured["C"]["operating_point_metrics"]
    delta = {
        k: current[k] - prior[k]
        for k in [
            "accuracy",
            "correct_positive_recall",
            "none_fp",
            "none_fp_count",
            "correct_positive",
        ]
    }
    g.write(
        OUT / "second-look.json",
        dict(
            look=2,
            diagnostic_only=True,
            arms=measured,
            prior=prior,
            delta=delta,
            disjointness=disjoint,
            wall_seconds=time.monotonic() - started,
            input_sha256=hashlib.sha256(raw).hexdigest(),
            records=357,
            argmax=h2.score_rows(heldout, logits, overflow, arms["C"]["policy"])[1],
        ),
    )
    verify_freeze()
    print(json.dumps(dict(second_look=current, delta=delta)), flush=True)


def replay():
    verify_freeze()
    assert (OUT / "second-look.json").exists()
    assert os.environ.get("CUDA_VISIBLE_DEVICES") == ""
    with (OUT / "preflight-started.json").open("x") as fp:
        json.dump(dict(time=time.time(), freeze=g.digest(OUT / "freeze.json")), fp)
    started = time.monotonic()
    clf = classifier()
    records = []
    # The setup list is accessed; no gate episode is scored or inspected.
    for ep in json.loads(BANK.read_text())["setup"]:
        runtime, oracle = f.Runtime(clf), f.Oracle()
        trace = []
        for ti, turn in enumerate(ep["turns"]):
            rec = v5.record_turn(ep, ti, turn, runtime, oracle)
            g.write(OUT / "records" / f"{ep['id']}_C_{ti}.json", rec)
            records.append(rec)
            trace.append(rec)
            g.write(OUT / "traces" / f"{ep['id']}_C.json", trace)
        print(json.dumps(dict(episode=ep["id"], records=len(records))), flush=True)
    summary = v5.eligibility_summary(records)
    summary.update(
        verdict="ELIGIBLE" if summary["eligible"] else "INELIGIBLE",
        cpu_replay_wall_seconds=time.monotonic() - started,
        gate_records=0,
        generation_records=0,
        cpu_inference_passes=1,
        gpu_held_seconds=json.loads((OUT / "fit-summary.json").read_text())[
            "gpu_held_seconds"
        ],
        pair_count=sum(len(r["trace"]["pairs"]) for r in records),
        admission_span_count=sum(len(r["trace"]["admissions"]) for r in records),
    )
    g.write(OUT / "summary.json", summary)
    verify_freeze()
    print(
        json.dumps({k: summary[k] for k in ["verdict", "counts", "unauthorized"]}),
        flush=True,
    )


def audit():
    verify_freeze()
    rows, receipt = load()
    counts = json.loads((OUT / "data-counts.json").read_text())
    assert all(receipt[k] == counts[k] for k in receipt)
    for seed in range(3):
        assert split_receipt(rows, seed) == counts["splits"][str(seed)]
        arrays = dict(
            np.load(MODELS / f"seed{seed}/dev_predictions.npz", allow_pickle=False)
        )
        table = json.loads((OUT / "calibration" / f"seed{seed}.json").read_text())
        assert all(table[k] == v for k, v in calibrate(arrays).items())
    records = []
    for ep in json.loads(BANK.read_text())["setup"]:
        clf = v5.SavedClassifier()
        clf.thresholds = policies()["C"]["policy"]["thresholds"]
        clf.admission_bound = "positive_proposal"
        runtime, oracle = f.Runtime(clf), f.Oracle()
        trace = []
        for ti, turn in enumerate(ep["turns"]):
            rec = json.loads((OUT / "records" / f"{ep['id']}_C_{ti}.json").read_text())
            for pair in rec["trace"]["pairs"]:
                normalized = tr.normalize_row(
                    dict(pair["input"], author="astra", label=pair["gold"])
                )
                assert list(tr.render_pair(normalized)) == pair["model_input"]
            for p in rec["trace"]["pairs"] + rec["trace"]["admissions"]:
                if not p["overflow"]:
                    np.testing.assert_allclose(
                        (
                            np.exp(np.array(p["logits"]) - max(p["logits"]))
                            / np.exp(np.array(p["logits"]) - max(p["logits"])).sum()
                        ),
                        p["probabilities"],
                        atol=1e-12,
                        rtol=1e-12,
                    )
            clf.record = rec
            assert v5.record_turn(ep, ti, turn, runtime, oracle) == rec
            records.append(rec)
            trace.append(rec)
        assert trace == json.loads((OUT / "traces" / f"{ep['id']}_C.json").read_text())
    summary = json.loads((OUT / "summary.json").read_text())
    assert all(summary[k] == v for k, v in v5.eligibility_summary(records).items())
    assert len(records) == len(list((OUT / "records").glob("*.json"))) == 96
    saved = [
        json.loads(s)
        for s in (OUT / "second-look-records.jsonl").read_text().splitlines()
    ]
    assert len(saved) == 357
    report = json.loads((OUT / "second-look.json").read_text())
    for arm, key in [("C", "prediction"), ("C'", "secondary_prediction")]:
        scored, _, predictions, probs = h2.score_rows(
            [r["row"] for r in saved],
            np.array([r["logits"] for r in saved]),
            np.array([r["overflow"] for r in saved]),
            policies()[arm]["policy"],
        )
        assert scored == report["arms"][arm]
        assert [op.LABELS[i] for i in predictions] == [r[key] for r in saved]
        np.testing.assert_allclose(
            probs, [r["probabilities"] for r in saved], atol=1e-12
        )
    g.write(
        OUT / "audit.json",
        dict(
            audit="PASS",
            records=96,
            traces=16,
            second_look_records=357,
            runtime_replay=True,
            calibration_recomputed=True,
            splits_disjoint=True,
            trainer_rendering_parity=True,
            frozen_hashes=True,
            record_sha256={
                p.name: g.digest(p) for p in sorted((OUT / "records").glob("*.json"))
            },
        ),
    )
    print(
        "V6 audit PASS: splits/calibration, second-look scores, 96 runtime records",
        flush=True,
    )


def run():
    verify_freeze()
    admission = json.loads((OUT / "summary.json").read_text())
    assert admission["eligible"], "INELIGIBLE: gate prohibited"
    assert not (OUT / "gate-started.json").exists()
    g.OUT = OUT
    with g.claim_gpu():
        started = time.monotonic()
        spent = admission["gpu_held_seconds"]
        g.write(OUT / "gate-started.json", dict(time=time.time(), pid=os.getpid()))
        trunk = None
        result = dict(verdict="INCOMPLETE")
        try:
            trunk = g.Trunk(started + g.BUDGET - spent - 30)
            clf = classifier()
            bank = json.loads(BANK.read_text())
            setup, durations = [], []
            for ep in bank["setup"]:
                t = time.monotonic()
                setup.extend(g.run_episode(ep, "O", trunk, clf, "setup"))
                durations.append(time.monotonic() - t)
            competence = sum(
                f.episode_metrics([r for r in setup if r["episode"] == e["id"]])[
                    "final_success"
                ]
                for e in bank["setup"]
            )
            selection = dict(
                competence=competence,
                n=64,
                arms=["C", "C'", "O", "N", "T"],
                projection=spent
                + time.monotonic()
                - started
                + 1.25 * max(durations) * 64 * 5,
            )
            g.write(OUT / "selection.json", selection)
            if competence < 15:
                result = dict(verdict="INELIGIBLE", selection=selection)
            elif selection["projection"] > g.BUDGET - 30:
                result = dict(verdict="INCOMPLETE", selection=selection)
            else:
                records = []
                rng = random.Random(30303)
                for ep in bank["gate"]:
                    arms = list(selection["arms"])
                    rng.shuffle(arms)
                    for arm in arms:
                        clf.thresholds = policies()[arm if arm == "C'" else "C"][
                            "policy"
                        ]["thresholds"]
                        records.extend(g.run_episode(ep, arm, trunk, clf, "gate"))
                        print(
                            json.dumps(
                                dict(
                                    episode=ep["id"],
                                    arm=arm,
                                    elapsed=time.monotonic() - started,
                                )
                            ),
                            flush=True,
                        )
                primary = f.summarize(
                    bank["gate"], [r for r in records if r["arm"] != "C'"], 64
                )
                alt = [
                    dict(r, arm="C" if r["arm"] == "C'" else r["arm"])
                    for r in records
                    if r["arm"] != "C"
                ]
                result = dict(
                    verdict=primary["verdict"],
                    primary=primary,
                    secondary=f.summarize(bank["gate"], alt, 64),
                    selection=selection,
                    records=len(records),
                )
        finally:
            if trunk is not None:
                trunk.backend.close()
            result["gpu_held_seconds"] = spent + time.monotonic() - started
            g.write(OUT / "gate-summary.json", result)
    verify_freeze()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        required=True,
        choices=["prepare", "fit", "second-look", "replay", "audit", "run"],
    )
    args = parser.parse_args()
    globals()[args.mode.replace("-", "_")]()


if __name__ == "__main__":
    main()
