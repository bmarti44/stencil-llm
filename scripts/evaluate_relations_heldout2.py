"""One CPU inference pass on held-out-2 after GPU/DEV freeze; never fits/selects.

Fit-on = kimi+enrich after merged patch; calibrated-on = dev;
evaluated-on = held-out-2 once; held-out-1 = development history.
Per-row records are written during that same pass. Replays score saved records.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from datetime import UTC, datetime

import numpy as np

from scripts import train_relations as tr
from stencil import relation_operating_point as op

MODEL = tr.ROOT / "data/classifier/model/relations"
HELDOUT = tr.ROOT / "data/classifier/heldout/fable-relations-heldout-2.jsonl"
HELDOUT_BLOB = "0008dbe51853c4a2075076c4f30cdd433ebd5e76"
LINEAGE = (
    "fit-on = kimi+enrich after merged patch; calibrated-on = dev "
    "(original seed-specific scenario-disjoint split, fit-author-shared); "
    "evaluated-on = held-out-2 once; held-out-1 = development; "
    "no benchmark inputs/responses; admission not trained"
)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def claim_once(model_dir, manifest):
    if (
        manifest["state"] != "development_complete_frozen"
        or manifest["recipe"]["seed"] != 0
        or manifest["heldout_evaluation_count"] != 0
        or manifest["budget"]["completed_epochs"] != 3
    ):
        raise ValueError("requires unevaluated, frozen, three-epoch seed 0")
    # Exclusive durable claim before any held-out input opens. No resume mode.
    with (model_dir / "heldout2-started.json").open("x") as f:
        json.dump({"started_utc": datetime.now(UTC).isoformat()}, f)
        f.flush()
        os.fsync(f.fileno())


def score_rows(rows, logits, overflow, policy):
    labels = np.array([tr.LABEL_MAP[r["label"]] for r in rows])
    probs, labels, overflow = op.inputs(logits, labels, overflow)
    predictions = op.predict(probs, policy, overflow)
    argmax = np.where(overflow, 0, probs.argmax(axis=1))
    report = tr.evaluation_report(rows, predictions, overflow)
    report["operating_point_metrics"] = op.metrics(labels, predictions)
    return report, tr.evaluation_report(rows, argmax, overflow), predictions, probs


def make_records(rows, logits, overflow, policy):
    _, _, predictions, probs = score_rows(rows, logits, overflow, policy)
    records = []
    for i, row in enumerate(rows):
        records.append(
            {
                "index": i,
                "row": row,
                "model_input_sha256": tr.digest(tr.render_pair(row)),
                "logits": logits[i].tolist(),
                "probabilities": probs[i].tolist(),
                "gold": row["label"],
                "prediction": op.LABELS[int(predictions[i])],
                "argmax": op.LABELS[0 if overflow[i] else int(probs[i].argmax())],
                "overflow": bool(overflow[i]),
            }
        )
    return records


def main():
    if os.environ.get("CUDA_VISIBLE_DEVICES") != "":
        raise ValueError("CPU evaluation requires CUDA_VISIBLE_DEVICES=''")
    manifest = json.loads((MODEL / "manifest.json").read_text())
    policy_record = json.loads((MODEL / "operating-point.json").read_text())
    assert policy_record["rule"] == op.RULE
    for name, expected in manifest["artifact_sha256"].items():
        assert sha(MODEL / name) == expected, name
    for name, expected in {
        **manifest["source_sha256"],
        **manifest["data_audit"]["input_sha256"],
    }.items():
        assert sha(tr.ROOT / name) == expected, name
    threshold_record = json.loads((MODEL / "thresholds.json").read_text())
    assert threshold_record["policy"] == policy_record["policy"]
    data = tr.ROOT / "data/classifier"
    training, receipt = tr.load_training(
        [data / "relations/kimi-relations.jsonl"],
        [data / "review/relations-merged-patch.jsonl"],
        [data / f"relations/{a}-enrich.jsonl" for a in ("astra", "opus")],
    )
    assert receipt["input_sha256"] == manifest["data_audit"]["input_sha256"]
    fit, dev = tr.split_development(training, 0)
    assert tr.digest(fit) == manifest["split"]["fit"]["sha256"]
    assert tr.digest(dev) == manifest["split"]["development"]["sha256"]

    import torch
    from safetensors.torch import load_file
    from transformers import AutoModel, AutoTokenizer

    torch.set_num_threads(4)
    torch.use_deterministic_algorithms(True)
    tokenizer = AutoTokenizer.from_pretrained(MODEL / "encoder", local_files_only=True)
    encoder = AutoModel.from_pretrained(MODEL / "encoder", local_files_only=True).eval()
    head = torch.nn.Sequential(
        torch.nn.Dropout(0.1), torch.nn.Linear(encoder.config.hidden_size + 4, 5)
    ).eval()
    head.load_state_dict(load_file(str(MODEL / "head.safetensors")))
    claim_once(MODEL, manifest)
    manifest.update(state="heldout2_evaluation_started", heldout_evaluation_count=1)
    tr.write_json(MODEL / "manifest.json", manifest)
    started = time.monotonic()
    raw_bytes = HELDOUT.read_bytes()
    blob = hashlib.sha1(
        b"blob " + str(len(raw_bytes)).encode() + b"\0" + raw_bytes
    ).hexdigest()
    assert blob == HELDOUT_BLOB, "held-out-2 differs from committed 8ae68078 input"
    raw = [json.loads(line) for line in raw_bytes.decode().splitlines() if line.strip()]
    headers = [r for r in raw if set(r) == {"summary"}]
    normalized = []
    for row in raw:
        if set(row) == {"summary"}:
            continue
        tr.refuse_benchmark(row)
        pair = tr.normalize_row(row)
        if pair is not None:
            normalized.append(pair)
    disjointness = tr.assert_heldout_disjoint(training, normalized)
    heldout, decisions = tr.deduplicate_heldout(normalized)
    assert len(heldout) == 357 and not decisions
    tokens, overflow = tr.encode_rows(heldout, tokenizer)
    logits = np.zeros((len(heldout), 5), dtype=np.float64)
    indices = np.flatnonzero(~overflow)
    manifest["heldout_inference_count"] = 1
    tr.write_json(MODEL / "manifest.json", manifest)
    records_path = MODEL / "heldout2-records.jsonl"
    with records_path.open("x") as output, torch.inference_mode():
        # Write every record in the inference run, including overflow abstentions.
        for start in range(0, len(heldout), 32):
            ii = indices[(indices >= start) & (indices < start + 32)]
            if len(ii):
                inputs = tokenizer.pad([tokens[i] for i in ii], return_tensors="pt")
                roles = torch.tensor(
                    [[float(heldout[i]["role"] == r) for r in tr.ROLES] for i in ii]
                )
                cls = encoder(**inputs).last_hidden_state[:, 0]
                logits[ii] = head(torch.cat([cls, roles], dim=1)).numpy()
            end = min(start + 32, len(heldout))
            records = make_records(
                heldout[start:end],
                logits[start:end],
                overflow[start:end],
                policy_record["policy"],
            )
            for record in records:
                record["index"] += start
                output.write(json.dumps(record, sort_keys=True) + "\n")
            output.flush()
            os.fsync(output.fileno())
    operational, argmax, _, _ = score_rows(
        heldout, logits, overflow, policy_record["policy"]
    )
    metrics = json.loads((MODEL / "metrics.json").read_text())
    metrics.update(heldout=operational, heldout_argmax=argmax)
    metrics["heldout_dataset"] = "heldout-2"
    metrics["data_lineage"] = LINEAGE
    metrics["new_rule_admission"] = {
        "implemented": False,
        "evaluated": False,
        "reason": "Pairwise relation head only; admission/runtime/gate untested.",
    }
    tr.write_json(MODEL / "metrics.json", metrics)
    manifest.update(
        state="complete",
        data_lineage=LINEAGE,
        heldout={
            "path": str(HELDOUT.relative_to(tr.ROOT)),
            "sha256": hashlib.sha256(raw_bytes).hexdigest(),
            "git_blob": blob,
            "raw_jsonl_records": len(raw),
            "summary_records_excluded": len(headers),
            "admission_rows_excluded": len(raw) - len(headers) - len(normalized),
            "pairs": len(heldout),
            "dedup_decisions": decisions,
            "disjointness_audit": disjointness,
            "summary_headers": headers,
        },
        evaluation_wall_seconds=time.monotonic() - started,
        evaluation_device="cpu",
        evaluation_completed_utc=datetime.now(UTC).isoformat(),
    )
    for name in ("metrics.json", "heldout2-records.jsonl", "heldout2-started.json"):
        manifest["artifact_sha256"][name] = sha(MODEL / name)
    tr.write_json(MODEL / "manifest.json", manifest)
    print(json.dumps({"heldout": operational, "argmax": argmax["accuracy"]}))


if __name__ == "__main__":
    main()
