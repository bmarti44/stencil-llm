"""FOCUS-3 v8: final admission refit and strict lifecycle, one-shot stop."""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import subprocess
import time
from contextlib import contextmanager

from scripts import finetune_admission_v3 as a
from scripts import focus3_gate as g
from scripts import focus3_gate_v5 as v5
from scripts import focus3_gate_v6 as v6
from stencil import focus3 as f

OUT = a.OUT
BANK = v6.BANK


@contextmanager
def claim_gpu():
    flag = OUT / "RUNNING.flag"
    while True:
        with (g.ROOT / ".review.lock").open("a") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                ready = False
                detail = "review lock busy"
            else:
                flags = list((g.ROOT / "results/quick-checks").rglob("RUNNING.flag"))
                query = subprocess.run(
                    [
                        "nvidia-smi",
                        "--query-compute-apps=pid,process_name",
                        "--format=csv,noheader",
                    ],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                other = [
                    s
                    for s in query.stdout.splitlines()
                    if s.split(",")[0].strip() != "2705"
                ]
                ready = not flags and not other
                detail = dict(flags=list(map(str, flags)), compute=other)
                if ready:
                    with flag.open("x") as fp:
                        json.dump(dict(pid=os.getpid(), check="FOCUS-3 v8"), fp)
                        fp.flush()
                        os.fsync(fp.fileno())
        if ready:
            break
        print("Waiting for GPU: " + json.dumps(detail), flush=True)
        time.sleep(30)
    try:
        yield
    finally:
        if flag.exists() and json.loads(flag.read_text())["pid"] == os.getpid():
            flag.unlink()


def sources():
    paths = [
        g.ROOT / p
        for p in [
            "src/stencil/focus3.py",
            "scripts/finetune_admission_v2.py",
            "scripts/finetune_admission_v3.py",
            "scripts/focus3_gate_v8.py",
            "scripts/focus3_gate_v6.py",
            "scripts/focus3_gate_v5.py",
            "scripts/focus3_gate.py",
            "src/stencil/focus2.py",
            "tests/test_focus3_gate_v8.py",
        ]
    ]
    paths += [a.BASE, a.ENRICHMENT] + [
        a.DATA / "review" / (n + ".jsonl") for n in a.prior.PATCH_NAMES
    ]
    paths += [a.BASE.parent / "heldout.json", a.BASE.parent / "heldout-records.jsonl"]
    paths += [
        OUT / "registration.md",
        OUT / "training-rows.json",
        OUT / "data-counts.json",
        BANK,
    ]
    for directory in [v6.MODELS / "seed0"]:
        paths += [p for p in directory.rglob("*") if p.is_file()]
    return {str(p.relative_to(g.ROOT)): g.digest(p) for p in sorted(paths)}


def prepare():
    assert not (OUT / "recipe-freeze.json").exists()
    rows, counts = a.corpus()
    # Catch tokenizer/target-length errors without running any model.
    from transformers import AutoTokenizer

    tok = AutoTokenizer.from_pretrained(
        "BAAI/bge-small-en-v1.5", revision=a.REVISION, local_files_only=True
    )
    for row in rows:
        tok(
            row.get("context") or "(no context)",
            f"[{row['role']}] {row['text']}",
            truncation="only_first",
            max_length=192,
        )
    counts["splits"] = {
        str(seed): dict(
            fit=len(a.split(rows, seed)[0]), dev=len(a.split(rows, seed)[1])
        )
        for seed in range(3)
    }
    g.write(OUT / "training-rows.json", rows)
    g.write(OUT / "data-counts.json", counts)
    g.write(OUT / "recipe-freeze.json", dict(hashes=sources(), created=time.time()))
    print(json.dumps({k: v for k, v in counts.items() if k != "drops"}), flush=True)


def verify_recipe():
    assert (
        json.loads((OUT / "recipe-freeze.json").read_text())["hashes"] == sources()
    ), "v8 recipe drift"


def fit():
    verify_recipe()
    with (OUT / "fit-started.json").open("x") as fp:
        json.dump(
            dict(time=time.time(), recipe=g.digest(OUT / "recipe-freeze.json")), fp
        )
    rows = json.loads((OUT / "training-rows.json").read_text())
    with claim_gpu():
        started = time.monotonic()
        try:
            for seed in range(3):
                a.fit_seed(rows, seed, started + 10770)
        finally:
            g.write(
                OUT / "fit-summary.json",
                dict(gpu_held_seconds=time.monotonic() - started),
            )
    verify_recipe()
    g.write(
        OUT / "freeze.json",
        dict(
            recipe=g.digest(OUT / "recipe-freeze.json"),
            created=time.time(),
            models={
                str(p.relative_to(g.ROOT)): g.digest(p)
                for p in sorted(a.MODELS.rglob("*"))
                if p.is_file()
            },
        ),
    )


def verify_freeze():
    verify_recipe()
    frozen = json.loads((OUT / "freeze.json").read_text())
    assert frozen["recipe"] == g.digest(OUT / "recipe-freeze.json")
    assert all(g.digest(g.ROOT / p) == h for p, h in frozen["models"].items())


def classifier(arm="C"):
    return f.FrozenClassifier(
        v6.MODELS / "seed0",
        v6.policies()[arm]["policy"]["thresholds"],
        "positive_proposal",
        a.MODELS / "seed0",
        True,
        True,
    )


def evaluation_identity(row):
    return (
        a.identity(row.get("context") or "(no context)"),
        row["role"],
        a.identity(row["text"]),
    )


def evaluate():
    verify_freeze()
    assert os.environ.get("CUDA_VISIBLE_DEVICES") == ""
    import torch
    from transformers import AutoModel, AutoTokenizer

    torch.set_num_threads(4)
    assert not (OUT / "heldout-inference-started.json").exists()
    receipt = OUT / "heldout-started.json"
    if receipt.exists():
        assert (OUT / "evaluation-preflight-correction.md").exists()
        receipt = OUT / "heldout-preflight-resumed.json"
    with receipt.open("x") as fp:
        json.dump(
            dict(
                time=time.time(),
                freeze=g.digest(OUT / "freeze.json"),
                diagnostic_repeat=True,
            ),
            fp,
        )
        fp.flush()
        os.fsync(fp.fileno())
    paths = sorted((a.DATA / "heldout").glob("fable-validation*.jsonl"))
    assert paths
    rows = [
        r
        for path in paths
        for r in a.read(path)
        if r.get("label") in a.LABELS
        and r.get("role") in a.ROLES
        and isinstance(r.get("text"), str)
    ]
    patches, _ = a.patches()
    for row in rows:
        patch = patches.get((row.get("source"), row["text"]), {})
        if patch.get("new_label") in a.LABELS:
            row["label"] = patch["new_label"]
    train = json.loads((OUT / "training-rows.json").read_text())
    overlap = {a.identity(r["text"]) for r in train} & {
        a.identity(r["text"]) for r in rows
    }
    full_overlap = {evaluation_identity(r) for r in train} & {
        evaluation_identity(r) for r in rows
    }
    assert not full_overlap, "Held-out full model-input overlap"
    assert all("fable" in r.get("source", "").lower() for r in rows)
    assert not any("fable" in r.get("source", "").lower() for r in train)
    with (OUT / "heldout-inference-started.json").open("x") as fp:
        json.dump(
            dict(
                time=time.time(),
                full_input_overlap=0,
                sentence_only_collisions=sorted(overlap),
            ),
            fp,
        )
        fp.flush()
        os.fsync(fp.fileno())
    previous = a.read(a.BASE.parent / "heldout-records.jsonl")
    assert [r["row"] for r in previous] == rows, "Diagnostic comparator input drift"
    old_summary = json.loads((a.BASE.parent / "heldout.json").read_text())
    assert old_summary["inputs"] == {
        str(p.relative_to(g.ROOT)): g.digest(p) for p in paths
    }
    predictions = {"ft-v2": [r["logits"]["ft-v2"] for r in previous]}
    for name, path in [("ft-v3", a.MODELS / "seed0")]:
        tok = AutoTokenizer.from_pretrained(path / "encoder", local_files_only=True)
        enc = AutoModel.from_pretrained(path / "encoder", local_files_only=True).eval()
        head = torch.nn.Sequential(
            torch.nn.Dropout(0.1), torch.nn.Linear(enc.config.hidden_size + 4, 3)
        ).eval()
        state = torch.load(path / "head.pt", map_location="cpu", weights_only=True)
        assert state["labels"] == a.LABELS and state["roles"] == a.ROLES
        head.load_state_dict(state["head"])
        predictions[name] = a.infer(rows, tok, enc, head, torch, "cpu")
    with (OUT / "heldout-records.jsonl").open("x") as fp:
        for i, row in enumerate(rows):
            fp.write(
                json.dumps(
                    dict(
                        index=i,
                        row=row,
                        logits={k: v[i] for k, v in predictions.items()},
                    )
                )
                + "\n"
            )
        fp.flush()
        os.fsync(fp.fileno())
    metrics = {k: a.metrics(rows, v) for k, v in predictions.items()}
    g.write(
        OUT / "heldout.json",
        dict(
            metrics=metrics,
            delta_accuracy=metrics["ft-v3"]["accuracy"] - metrics["ft-v2"]["accuracy"],
            comparator="committed v7 ft-v2 logits on identical rows and file hashes",
            diagnostic_repeat=True,
            exact_sentence_overlap=len(overlap),
            sentence_only_collisions=sorted(overlap),
            full_model_input_overlap=0,
            author_disjoint=True,
            inputs={str(p.relative_to(g.ROOT)): g.digest(p) for p in paths},
        ),
    )
    verify_freeze()
    print(json.dumps(metrics), flush=True)


def replay():
    verify_freeze()
    assert (OUT / "heldout.json").exists()
    assert os.environ.get("CUDA_VISIBLE_DEVICES") == ""
    with (OUT / "preflight-started.json").open("x") as fp:
        json.dump(dict(time=time.time(), freeze=g.digest(OUT / "freeze.json")), fp)
    started = time.monotonic()
    clf = classifier()
    records = []
    for ep in json.loads(BANK.read_text())["setup"]:
        rt, oracle, trace = f.Runtime(clf), f.Oracle(), []
        for ti, turn in enumerate(ep["turns"]):
            rec = v5.record_turn(ep, ti, turn, rt, oracle)
            g.write(OUT / "records" / f"{ep['id']}_C_{ti}.json", rec)
            records.append(rec)
            trace.append(rec)
            g.write(OUT / "traces" / f"{ep['id']}_C.json", trace)
        print(json.dumps(dict(episode=ep["id"], records=len(records))), flush=True)
    summary = v5.eligibility_summary(records)
    summary.update(
        verdict="ELIGIBLE" if summary["eligible"] else "INELIGIBLE",
        cpu_replay_wall_seconds=time.monotonic() - started,
        gpu_held_seconds=json.loads((OUT / "fit-summary.json").read_text())[
            "gpu_held_seconds"
        ],
        cross_key_proposals=sum(r["trace"]["cross_key_proposals"] for r in records),
        gate_records=0,
        cpu_inference_passes=1,
    )
    g.write(OUT / "summary.json", summary)
    verify_freeze()
    print(json.dumps(summary), flush=True)


def audit():
    verify_freeze()
    rows = json.loads((OUT / "training-rows.json").read_text())
    for seed in range(3):
        fit, dev = a.split(rows, seed)
        manifest = json.loads((a.MODELS / f"seed{seed}/manifest.json").read_text())
        assert not (
            {a.identity(r["text"]) for r in fit} & {a.identity(r["text"]) for r in dev}
        )
        assert manifest["fit_ids"] == [a.identity(r["text"]) for r in fit]
        assert manifest["dev_ids"] == [a.identity(r["text"]) for r in dev]
        saved = json.loads((a.MODELS / f"seed{seed}/dev-records.json").read_text())
        assert a.metrics(
            [r["row"] for r in saved], [r["logits"] for r in saved]
        ) == json.loads((a.MODELS / f"seed{seed}/metrics.json").read_text())
        assert a.family_metrics(
            [r["row"] for r in saved], [r["logits"] for r in saved]
        ) == json.loads(
            (a.MODELS / f"seed{seed}/request-family-metrics.json").read_text()
        )
    records = []
    for ep in json.loads(BANK.read_text())["setup"]:
        clf = v5.SavedClassifier()
        clf.key_identity = True
        clf.strict_lifecycle = True
        clf.admission_bound = "positive_proposal"
        clf.thresholds = v6.policies()["C"]["policy"]["thresholds"]
        rt, oracle = f.Runtime(clf), f.Oracle()
        for ti, turn in enumerate(ep["turns"]):
            rec = json.loads((OUT / "records" / f"{ep['id']}_C_{ti}.json").read_text())
            clf.record = rec
            assert v5.record_turn(ep, ti, turn, rt, oracle) == rec
            for pair in rec["trace"]["pairs"]:
                if pair["applied"] != "none":
                    assert not pair["cross_key"]
                    target = next(
                        r
                        for r in rec["trace"]["before"]
                        if r["id"] == pair["input"]["target_id"]
                    )
                    assert pair["proposal_key"] == rt.key_slugs.get(
                        target["id"], f.relation_key(target["text"])
                    )
            records.append(rec)
    summary = json.loads((OUT / "summary.json").read_text())
    assert all(summary[k] == v for k, v in v5.eligibility_summary(records).items())
    assert len(records) == 96
    saved = a.read(OUT / "heldout-records.jsonl")
    for name, metric in json.loads((OUT / "heldout.json").read_text())[
        "metrics"
    ].items():
        assert (
            a.metrics([r["row"] for r in saved], [r["logits"][name] for r in saved])
            == metric
        )
    g.write(
        OUT / "audit.json",
        dict(
            audit="PASS",
            records=96,
            split_disjoint=True,
            dev_metrics_recomputed=True,
            heldout_metrics_recomputed=True,
            runtime_replay=True,
            key_identity=True,
            strict_lifecycle=True,
            cross_key_proposals=summary["cross_key_proposals"],
        ),
    )
    print("V8 saved-record audit PASS", flush=True)


def run():
    verify_freeze()
    # Reuse v6's exact O-setup/projection/arm order/readings consumer.
    v6.OUT = OUT
    v6.verify_freeze = verify_freeze
    v6.classifier = classifier
    g.claim_gpu = claim_gpu
    v6.run()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        required=True,
        choices=["prepare", "fit", "evaluate", "replay", "audit", "run"],
    )
    globals()[parser.parse_args().mode]()


if __name__ == "__main__":
    main()
