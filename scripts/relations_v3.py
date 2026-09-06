"""User-authorized relations v3: development fit, committed freeze, one-shot eval."""

from __future__ import annotations

import argparse
import copy
import fcntl
import hashlib
import importlib.util
import json
import os
import subprocess
import time
from collections import Counter
from pathlib import Path
from unittest.mock import patch

import numpy as np
from scipy.stats import beta

from scripts import evaluate_relations_heldout2 as h2
from scripts import focus3_gate_v6 as v2
from scripts import train_relations as tr

ROOT = tr.ROOT
OUT = ROOT / "data/classifier/model/relations-v3"
RUN = ROOT / "results/quick-checks/relations-v3"
OVERRIDE = v2.DATA / "relations/kimi-overrides.jsonl"
PATCH = v2.DATA / "review/overrides-opus-patch.jsonl"
FIT_ONLY = {178, 186, 291, 415, 417, 877, 945}
LINEAGE = (
    "fit-on = exact v2 patched Kimi relations/transitions + four enrichment sets "
    "(90 Astra2 evaluation-derived relatives disclosed) + Opus-patched Kimi overrides; "
    "calibrated-on = scenario-disjoint DEV, flagged override families excluded; "
    "evaluated-on = fresh Fable held-out-3 once after committed freeze; "
    "held-out-2 historical secondary re-look; v2 SETUP runtime diagnostic; "
    "seed0 designated, seeds1/2 DEV stability; no benchmark inputs/responses"
)
ORIGINAL_SPLIT = tr.split_development


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob(path):
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD:" + str(path.relative_to(ROOT))], cwd=ROOT, text=True
    ).strip()


def committed(path):
    blob = git_blob(path)
    raw = path.read_bytes()
    assert (
        hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
        == blob
    )
    return blob


def load():
    base, base_receipt = v2.load()
    raw, _ = tr.read_jsonl(OVERRIDE)
    patches, _ = tr.read_jsonl(PATCH)
    drops, changes = set(), []
    for p in patches:
        if "summary" in p:
            continue
        i = p["index"]
        row = raw[i]
        assert row["source"] == p["source"]
        if p.get("delete"):
            drops.add(i)
        else:
            field = p["field"]
            assert row.get(field) == p["old"], (i, field)
            if p["new"] == "<remove field>":
                del row[field]
            elif p["new"] == "<rename field to 'author'>":
                row["author"] = row.pop(field)
            else:
                row[field] = p["new"]
        changes.append(p)
    added, mechanical, counts = [], [], Counter()
    for i, row in enumerate(raw):
        if i in drops:
            continue
        row = copy.deepcopy(row)
        text = row["target_span"]["text"]
        message = tr.message_text(row)
        if text not in message:
            mechanical.append(dict(index=i, reason="nonverbatim_target"))
            continue
        start = message.find(text)
        counts["start_repaired"] += row["target_span"]["start"] != start
        counts["end_repaired"] += row["target_span"]["end"] != start + len(text)
        counts["whole_message_spans"] += text == message
        row["target_span"] = dict(start=start, end=start + len(text), text=text)
        spans = row.get("new_rule_spans", [])
        if len(spans) == 3 and isinstance(spans[0], int):
            spans = [spans]
        normalized = []
        for span in spans:
            quote = (
                span
                if isinstance(span, str)
                else span[2]
                if isinstance(span, list)
                else span.get("text", span.get("quote"))
            )
            if not quote or quote not in message:
                raise ValueError(("nonverbatim admission span", i, quote))
            offset = message.find(quote)
            normalized.append(dict(start=offset, end=offset + len(quote), text=quote))
        row["new_rule_spans"] = normalized
        row["id"] = f"overrides:{row['source']}:{i}"
        row["scenario_id"] = row["id"]
        row["source_file"] = str(OVERRIDE.relative_to(ROOT))
        row["source_row"] = i + 1
        row["override_index"] = i
        row["fit_only"] = i in FIT_ONLY
        tr.refuse_benchmark(row)
        normalized_row = tr.normalize_row(row)
        # These seven are development-history/fit only, never calibration.
        if i in FIT_ONLY:
            normalized_row["development_only"] = False
        added.append(normalized_row)
    combined, dedup = tr.deduplicate(copy.deepcopy(base) + added, full_input=True)
    assert len(base) == 7749
    base_inputs = {tr.render_pair(r): r["label"] for r in base}
    combined_inputs = {tr.render_pair(r): r["label"] for r in combined}
    assert base_inputs.items() <= combined_inputs.items()
    return combined, dict(
        lineage=LINEAGE,
        base=base_receipt,
        patch_changes=changes,
        mechanical_drops=mechanical,
        override_repairs=dict(counts),
        override_retained=len(added),
        dedup=dedup,
        pairs=len(combined),
        labels=dict(Counter(r["label"] for r in combined)),
        input_sha256={
            str(p.relative_to(ROOT)): sha(p)
            for p in [*v2.TRAIN, *v2.PATCH, *v2.ENRICH, OVERRIDE, PATCH]
        },
    )


def split(rows, seed=0, fraction=0.1):
    groups = tr.group_rows(rows)
    forced = [
        r for group in groups if any(r.get("fit_only") for r in group) for r in group
    ]
    eligible = [
        r
        for group in groups
        if not any(r.get("fit_only") for r in group)
        for r in group
    ]
    fit, dev = ORIGINAL_SPLIT(
        eligible, seed, round(len(rows) * fraction) / len(eligible)
    )
    fit += forced
    assert not any(r.get("fit_only") for r in dev)
    assert not (
        {t for r in fit for t in tr.group_tokens(r)}
        & {t for r in dev for t in tr.group_tokens(r)}
    )
    return fit, dev


def split_receipt(rows, seed):
    return {
        name: dict(
            n=len(part),
            sha256=tr.digest(part),
            ids=[r["id"] for r in part],
            labels=dict(Counter(r["label"] for r in part)),
        )
        for name, part in zip(["fit", "development"], split(rows, seed), strict=True)
    }


def source_paths():
    return [
        Path(__file__),
        ROOT / "scripts/train_relations.py",
        ROOT / "scripts/focus3_gate_v6.py",
        ROOT / "scripts/evaluate_relations_heldout2.py",
        ROOT / "src/stencil/relation_operating_point.py",
        RUN / "runtime-v2.py",
        ROOT / "scripts/focus3_gate_v5.py",
        ROOT / "scripts/focus3_gate.py",
        ROOT / "scripts/focus3_gate_v4.py",
        ROOT / "scripts/focus3_gate_v3.py",
        ROOT / "src/stencil/focus2.py",
        v2.BANK,
    ]


def prepare():
    assert not (RUN / "recipe.json").exists()
    rows, receipt = load()
    receipt["splits"] = {str(s): split_receipt(rows, s) for s in range(3)}
    write(RUN / "data-counts.json", receipt)
    RUN.mkdir(parents=True, exist_ok=True)
    # Exact runtime at v2 checkpoint freeze, without changing the active runtime.
    (RUN / "runtime-v2.py").write_bytes(
        subprocess.check_output(
            ["git", "show", "54e09f25:src/stencil/focus3.py"], cwd=ROOT
        )
    )
    old = json.loads(
        (ROOT / "results/quick-checks/focus3-gate/v6/recipe-freeze.json").read_text()
    )
    assert sha(RUN / "runtime-v2.py") == old["hashes"]["src/stencil/focus3.py"]
    baseline_records = [
        json.loads(line)
        for line in (
            ROOT / "results/quick-checks/focus3-gate/v6/second-look-records.jsonl"
        )
        .read_text()
        .splitlines()
    ]
    write(RUN / "v2-baseline.json", metrics(baseline_records))
    write(
        RUN / "recipe.json",
        dict(
            lineage=LINEAGE,
            seed=0,
            cap_seconds=1800,
            source_hashes={str(p.relative_to(ROOT)): sha(p) for p in source_paths()},
            data_counts=sha(RUN / "data-counts.json"),
            baseline_sha256=sha(RUN / "v2-baseline.json"),
            admission_hashes={
                str(p.relative_to(ROOT)): sha(p)
                for p in (v2.DATA / "model/ft").rglob("*")
                if p.is_file()
            },
            reading=(
                "GO iff heldout3 supersedes recall >= .90, accuracy >= .94, "
                "and every label F1 >= v2 heldout2 F1 - .03; otherwise v2 stays. "
                "Runtime diagnostic secondary."
            ),
            cp=(
                "two-sided 95% equal-tailed Clopper-Pearson, "
                "row-level descriptive bounds"
            ),
            recipe_reference=(
                "data/classifier/model/relations-v2/README.md; "
                "scripts/focus3_gate_v6.py fit/calibrate"
            ),
        ),
    )
    print(
        json.dumps(
            {
                k: receipt[k]
                for k in ["pairs", "labels", "override_retained", "override_repairs"]
            }
        ),
        flush=True,
    )


def verify_recipe():
    recipe = json.loads((RUN / "recipe.json").read_text())
    assert recipe["data_counts"] == sha(RUN / "data-counts.json")
    assert recipe["baseline_sha256"] == sha(RUN / "v2-baseline.json")
    for p, h in recipe["admission_hashes"].items():
        assert sha(ROOT / p) == h, p
    for p, h in recipe["source_hashes"].items():
        assert sha(ROOT / p) == h, p
    for p, h in json.loads((RUN / "data-counts.json").read_text())[
        "input_sha256"
    ].items():
        assert sha(ROOT / p) == h, p


def fit():
    verify_recipe()
    committed(RUN / "recipe.json")
    rows, receipt = load()
    expected = json.loads((RUN / "data-counts.json").read_text())
    assert all(split_receipt(rows, s) == expected["splits"][str(s)] for s in range(3))
    with (ROOT / ".review.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        flags = list((ROOT / "results/quick-checks").rglob("RUNNING.flag"))
        query = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-compute-apps=pid,process_name",
                "--format=csv,noheader",
            ],
            text=True,
        )
        others = [
            line
            for line in query.splitlines()
            if line.strip() and line.split(",")[0].strip() != "2705"
        ]
        assert not flags and not others, (flags, others)
        with (RUN / "RUNNING.flag").open("x") as fp:
            json.dump(dict(pid=os.getpid(), check="relations-v3"), fp)
    started = time.monotonic()
    try:
        write(
            RUN / "fit-started.json",
            dict(pid=os.getpid(), time=time.time(), gpu_query=query),
        )
        import torch

        def budget_hook(optimizer, args, kwargs):
            if time.monotonic() - started >= 1740:
                raise TimeoutError("cooperative GPU cap; no signal")

        with patch.object(
            tr,
            "load_training",
            lambda *a, **k: (copy.deepcopy(rows), copy.deepcopy(receipt)),
        ):
            with patch.object(tr, "split_development", split):
                original_init = torch.optim.AdamW.__init__

                def init(opt, *a, **k):
                    original_init(opt, *a, **k)
                    opt.register_step_pre_hook(budget_hook)

                with patch.object(torch.optim.AdamW, "__init__", init):
                    for seed in range(3):
                        assert time.monotonic() - started < 1500
                        path = OUT / f"seed{seed}"
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
                                *map(str, v2.TRAIN),
                                "--patch",
                                *map(str, v2.PATCH),
                                "--enrich",
                                *map(str, v2.ENRICH),
                            ]
                        )
                        tr.train(args)
                        manifest = json.loads((path / "manifest.json").read_text())
                        assert manifest["budget"]["completed_epochs"] == 3
                        arrays = dict(
                            np.load(path / "dev_predictions.npz", allow_pickle=False)
                        )
                        table = v2.calibrate(arrays)
                        write(path / "operating-point.json", table)
                        write(
                            path / "thresholds.json",
                            dict(
                                thresholds=table["arms"]["C"]["policy"]["thresholds"],
                                secondary_thresholds=table["arms"]["C'"]["policy"][
                                    "thresholds"
                                ],
                                admission_bound="positive_proposal",
                                calibration="DEV only",
                            ),
                        )
                        dev = split(rows, seed)[1]
                        assert arrays["split_sha256"].item() == tr.digest(dev)
                        with (path / "dev-records.jsonl").open("x") as fp:
                            for rec in h2.make_records(
                                dev,
                                arrays["logits"],
                                arrays["overflow"],
                                table["arms"]["C"]["policy"],
                            ):
                                fp.write(json.dumps(rec, sort_keys=True) + "\n")
                        manifest["data_lineage"] = LINEAGE
                        manifest["artifact_sha256"] = {
                            str(p.relative_to(path)): sha(p)
                            for p in path.rglob("*")
                            if p.is_file() and p.name != "manifest.json"
                        }
                        write(path / "manifest.json", manifest)
                        print(
                            json.dumps(
                                dict(
                                    seed=seed,
                                    dev=table["arms"]["C"],
                                    budget=manifest["budget"],
                                )
                            ),
                            flush=True,
                        )
        assert time.monotonic() - started < 1800
    finally:
        write(
            RUN / "gpu-time.json",
            dict(gpu_seconds=time.monotonic() - started, cap_seconds=1800),
        )
        (RUN / "RUNNING.flag").unlink()
    verify_recipe()
    write(
        RUN / "freeze.json",
        dict(
            recipe_sha256=sha(RUN / "recipe.json"),
            models={
                str(p.relative_to(ROOT)): sha(p) for p in OUT.rglob("*") if p.is_file()
            },
            seed_policy="seed0 always",
            created=time.time(),
        ),
    )


def verify_freeze():
    verify_recipe()
    committed(RUN / "freeze.json")
    freeze = json.loads((RUN / "freeze.json").read_text())
    assert freeze["recipe_sha256"] == sha(RUN / "recipe.json")
    for p, h in freeze["models"].items():
        assert sha(ROOT / p) == h, p


def metrics(records):
    report = tr.evaluate_predictions(
        [r["row"] for r in records],
        np.array([tr.LABEL_MAP[r["prediction"]] for r in records]),
    )
    for r in report["per_class"].values():
        tp = r["recall"] * r["support"] if r["support"] else 0
        r["f1"] = (
            2 * tp / (r["support"] + r["predicted"])
            if r["support"] + r["predicted"]
            else 0.0
        )
    cm = report["confusion_gold_by_prediction"]
    k, n = cm[1][1], sum(cm[1])
    assert n
    report["supersedes_cp95"] = [
        float(beta.ppf(0.025, k, n - k + 1)) if k else 0.0,
        float(beta.ppf(0.975, k + 1, n - k)) if k < n else 1.0,
    ]
    return report


def decision(current, baseline):
    failures = []
    if current["accuracy"] < 0.94:
        failures.append(f"accuracy {current['accuracy']:.6f} < .94")
    if current["per_class"]["supersedes"]["recall"] < 0.90:
        failures.append("supersedes recall < .90")
    for label in tr.LABELS:
        if (
            current["per_class"][label]["f1"]
            < baseline["per_class"][label]["f1"] - 0.03
        ):
            failures.append(f"{label} F1 below v2 heldout2 minus .03")
    return dict(verdict="NO-GO" if failures else "GO", failures=failures)


def evaluate(number):
    verify_freeze()
    assert os.environ.get("CUDA_VISIBLE_DEVICES") == ""
    path = v2.DATA / f"heldout/fable-relations-heldout-{number}.jsonl"
    # Check committed existence without reading its content until after freeze.
    blob = git_blob(path)
    with (OUT / f"heldout{number}-started.json").open("x") as fp:
        json.dump(
            dict(
                time=time.time(),
                freeze=sha(RUN / "freeze.json"),
                input_blob=blob,
                inference_passes=1,
            ),
            fp,
        )
        fp.flush()
        os.fsync(fp.fileno())
    assert committed(path) == blob
    raw = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    heldout = [tr.normalize_row(r) for r in raw if set(r) != {"summary"}]
    assert all(r is not None for r in heldout)
    for r in heldout:
        tr.refuse_benchmark(r)
    train, _ = load()
    disjoint = tr.assert_heldout_disjoint(train, heldout)
    heldout, drops = tr.deduplicate_heldout(heldout)
    assert not drops
    import torch
    from safetensors.torch import load_file
    from transformers import AutoModel, AutoTokenizer

    torch.set_num_threads(4)
    model = OUT / "seed0"
    tok = AutoTokenizer.from_pretrained(model / "encoder", local_files_only=True)
    enc = AutoModel.from_pretrained(model / "encoder", local_files_only=True).eval()
    head = torch.nn.Sequential(
        torch.nn.Dropout(0.1), torch.nn.Linear(enc.config.hidden_size + 4, 5)
    ).eval()
    head.load_state_dict(load_file(str(model / "head.safetensors")))
    policy = json.loads((model / "operating-point.json").read_text())["arms"]["C"][
        "policy"
    ]
    tokens, overflow = tr.encode_rows(heldout, tok)
    records = []
    with (
        (OUT / f"heldout{number}-records.jsonl").open("x") as fp,
        torch.inference_mode(),
    ):
        for start in range(0, len(heldout), 32):
            end = min(start + 32, len(heldout))
            ii = [i for i in range(start, end) if not overflow[i]]
            logits = np.zeros((end - start, 5), dtype=np.float64)
            if ii:
                inputs = tok.pad([tokens[i] for i in ii], return_tensors="pt")
                roles = torch.tensor(
                    [[float(heldout[i]["role"] == r) for r in tr.ROLES] for i in ii]
                )
                logits[np.array(ii) - start] = head(
                    torch.cat([enc(**inputs).last_hidden_state[:, 0], roles], dim=1)
                ).numpy()
            for rec in h2.make_records(
                heldout[start:end], logits, overflow[start:end], policy
            ):
                rec["index"] += start
                fp.write(json.dumps(rec, sort_keys=True) + "\n")
                records.append(rec)
            fp.flush()
            os.fsync(fp.fileno())
    result = metrics(records)
    result.update(
        input_sha256=sha(path),
        input_blob=blob,
        disjointness=disjoint,
        inference_passes=1,
        secondary=number == 2,
    )
    write(OUT / f"heldout{number}-metrics.json", result)
    print(json.dumps(result), flush=True)


def replay():
    verify_freeze()
    assert os.environ.get("CUDA_VISIBLE_DEVICES") == ""
    with (RUN / "runtime-started.json").open("x") as fp:
        json.dump(dict(time=time.time()), fp)
    import sys

    spec = importlib.util.spec_from_file_location(
        "stencil._relations_v3_runtime_v2", RUN / "runtime-v2.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    module.ROOT = ROOT
    policy = json.loads((OUT / "seed0/operating-point.json").read_text())["arms"]["C"][
        "policy"
    ]
    clf = module.FrozenClassifier(
        OUT / "seed0", policy["thresholds"], "positive_proposal"
    )
    records = []
    with patch.object(v2.v5, "f", module):
        for ep in json.loads(v2.BANK.read_text())["setup"]:
            runtime, oracle = module.Runtime(clf), module.Oracle()
            for ti, turn in enumerate(ep["turns"]):
                rec = v2.v5.record_turn(ep, ti, turn, runtime, oracle)
                write(RUN / "records" / f"{ep['id']}_C_{ti}.json", rec)
                records.append(rec)
    summary = v2.v5.eligibility_summary(records)
    write(RUN / "runtime-summary.json", summary)
    print(json.dumps(summary), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "mode", choices=["prepare", "fit", "heldout3", "heldout2", "replay"]
    )
    args = parser.parse_args()
    if args.mode.startswith("heldout"):
        evaluate(int(args.mode[-1]))
    else:
        globals()[args.mode]()


if __name__ == "__main__":
    main()
