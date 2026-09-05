"""Recompute/score DEV only; no held-out input option or evaluation path."""

import argparse
import csv
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from scripts import train_relations as tr
from stencil import relation_operating_point as op


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def infer_dev(model_dir):
    import torch
    from safetensors.torch import load_file
    from transformers import AutoModel, AutoTokenizer

    manifest = json.loads((model_dir / "manifest.json").read_text())
    data = tr.ROOT / "data/classifier"
    rows, receipt = tr.load_training(
        [data / "relations/kimi-relations.jsonl"],
        [data / "review/relations-merged-patch.jsonl"],
        [data / f"relations/{author}-enrich.jsonl" for author in ("astra", "opus")],
    )
    fit, dev = tr.split_development(rows, manifest["recipe"]["seed"])
    assert receipt["input_sha256"] == manifest["data_audit"]["input_sha256"]
    for name, part in (("fit", fit), ("development", dev)):
        assert tr.digest(part) == manifest["split"][name]["sha256"]
    torch.set_num_threads(4)
    tokenizer = AutoTokenizer.from_pretrained(
        model_dir / "encoder", local_files_only=True
    )
    encoder = AutoModel.from_pretrained(
        model_dir / "encoder", local_files_only=True
    ).eval()
    head = torch.nn.Sequential(
        torch.nn.Dropout(0.1), torch.nn.Linear(encoder.config.hidden_size + 4, 5)
    )
    head.load_state_dict(load_file(str(model_dir / "head.safetensors")))
    head.eval()
    tokens, overflow = tr.encode_rows(dev, tokenizer)
    logits = np.zeros((len(dev), 5), dtype=np.float64)
    indices = np.flatnonzero(~overflow)
    with torch.inference_mode():
        for start in range(0, len(indices), 32):
            ii = indices[start : start + 32]
            inputs = tokenizer.pad([tokens[i] for i in ii], return_tensors="pt")
            roles = torch.tensor(
                [[float(dev[i]["role"] == r) for r in tr.ROLES] for i in ii]
            )
            cls = encoder(**inputs).last_hidden_state[:, 0]
            logits[ii] = head(torch.cat([cls, roles], dim=1)).numpy()
    return dict(
        logits=logits,
        labels=np.array([tr.LABEL_MAP[r["label"]] for r in dev]),
        overflow=overflow,
        split_sha256=np.array(tr.digest(dev)),
    )


def curves(arrays, output, prefix):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    probs, labels, overflow = op.inputs(
        arrays["logits"], arrays["labels"], arrays["overflow"]
    )
    records = []
    for kind, grid in (
        ("per_class", op.RULE["threshold_grid"]),
        ("margin", op.RULE["margin_grid"]),
    ):
        for value in grid:
            policy = (
                {"kind": kind, "thresholds": dict.fromkeys(op.LABELS[1:], value)}
                if kind == "per_class"
                else {"kind": kind, "margin": value}
            )
            result = op.metrics(labels, op.predict(probs, policy, overflow))
            for label, m in result["per_class"].items():
                records.append(
                    {
                        "kind": kind,
                        "cutoff": value,
                        "class": label,
                        **m,
                        "total_coverage_all": result["coverage_all"],
                        "total_correct_positive_recall": result[
                            "correct_positive_recall"
                        ],
                        "total_none_fp": result["none_fp"],
                    }
                )
    with (output / f"{prefix}-curve.csv").open("w") as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    fig, axes = plt.subplots(2, 4, figsize=(16, 7), constrained_layout=True)
    for i, kind in enumerate(("per_class", "margin")):
        for label in op.LABELS[1:]:
            part = [r for r in records if r["kind"] == kind and r["class"] == label]
            for j, key in enumerate(("precision", "coverage_all", "recall", "none_fp")):
                axes[i, j].plot(
                    [r["cutoff"] for r in part],
                    [np.nan if r[key] is None else r[key] for r in part],
                    label=label,
                )
                axes[i, j].set(
                    xlabel="Probability cutoff"
                    if i == 0
                    else "Top-two probability margin",
                    ylabel=key.replace("_", " "),
                    ylim=(-0.02, 1.02 if j < 3 else 0.22),
                )
                axes[i, j].grid(alpha=0.2)
        axes[i, 3].axhline(0.05, color="black", linestyle="--", linewidth=1)
    axes[0, 0].legend(fontsize=8)
    fig.suptitle(
        f"{prefix}: DEV only; recall = correct class / gold class; "
        "undefined precision omitted"
    )
    fig.savefig(output / f"{prefix}-curve.png", dpi=160)
    plt.close(fig)
    lines = [
        f"# {prefix} DEV operating curves",
        "",
        "Full grid and counts: "
        f"[{prefix}-curve.csv]({prefix}-curve.csv). "
        "Per-class coverage_all = emitted class / all DEV; "
        "recall = correct class / gold class. None-FP denominator is all gold none. "
        "Undefined precision is —. "
        "Curves use the actual positive-argmax acceptance path.",
        "",
        "| Variant | Cutoff | Class | Precision | Recall | Coverage/all | None-FP |",
        "|---|---:|---|---:|---:|---:|---:|",
    ]
    for r in records:
        if r["cutoff"] in (0, 0.2, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.98):
            values = [
                "—" if r[k] is None else f"{100 * r[k]:.2f}%"
                for k in ("precision", "recall", "coverage_all", "none_fp")
            ]
            lines.append(
                f"| {r['kind']} | {r['cutoff']:.2f} | {r['class']} | "
                + " | ".join(values)
                + " |"
            )
    (output / f"{prefix}-curve.md").write_text("\n".join(lines) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--prefix", required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    cache = args.model_dir / "dev_predictions.npz"
    arrays = (
        dict(np.load(cache, allow_pickle=False))
        if cache.exists()
        else infer_dev(args.model_dir)
    )
    manifest = json.loads((args.model_dir / "manifest.json").read_text())
    assert arrays["split_sha256"].item() == manifest["split"]["development"]["sha256"]
    np.savez_compressed(args.output / f"{args.prefix}-dev.npz", **arrays)
    curves(arrays, args.output, args.prefix)
    record = op.select(arrays["logits"], arrays["labels"], arrays["overflow"])
    probs, labels, overflow = op.inputs(
        arrays["logits"], arrays["labels"], arrays["overflow"]
    )
    record.update(
        created_utc=datetime.now(UTC).isoformat(),
        model_dir=str(args.model_dir),
        seed=manifest["recipe"]["seed"],
        split_sha256=arrays["split_sha256"].item(),
        checkpoint_sha256={
            str(p.relative_to(args.model_dir)): sha(p)
            for p in (
                args.model_dir / "encoder/model.safetensors",
                args.model_dir / "head.safetensors",
            )
        },
        dev_logits_sha256=sha(args.output / f"{args.prefix}-dev.npz"),
        argmax=op.metrics(labels, np.where(overflow, 0, probs.argmax(axis=1))),
        heldout_evaluations_this_task=0,
        lineage=(
            "fit: unchanged patched Kimi+Astra/Opus; "
            "calibration/evaluation: original DEV only; "
            "heldout-1 historical development; heldout-2 reserved"
        ),
    )
    tr.write_json(args.output / f"{args.prefix}-operating-point.json", record)
    print(
        json.dumps({k: record[k] for k in ("policy", "qualified_on_dev", "dev")}),
        flush=True,
    )


if __name__ == "__main__":
    main()
