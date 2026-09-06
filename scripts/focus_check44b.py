"""Check44b: separate preparation, fitting, sealed evaluation and saved-record audit."""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import math
import os
import random
import subprocess
import time
from pathlib import Path

from scripts import focus_check44 as metrics
from stencil.admission import BASE, LIMIT, REVISION, Detector, accepts, candidates

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/quick-checks/check44b"
MODELS = ROOT / "data/classifier/model/admission-v1"
DATA = ROOT / "data/classifier"
SOURCES = [
    DATA / "relations/kimi-admission.jsonl",
    DATA / "review/admission-opus-patch.jsonl",
    DATA / "relations/opus-admission-enrich.jsonl",
]
HELDOUT = DATA / "heldout/fable-admission-heldout-2.jsonl"
BANK = ROOT / "results/quick-checks/focus3-gate/v4/bank.json"
CAP = 3600


def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def lines(path):
    return [json.loads(s) for s in path.read_text().splitlines() if s.strip()]


def sha(path):
    return metrics.sha(path)


def committed(path):
    rel = str(path.relative_to(ROOT))
    digest = subprocess.check_output(
        ["git", "rev-parse", f"HEAD:{rel}"], cwd=ROOT, text=True
    ).strip()
    actual = subprocess.check_output(
        ["git", "hash-object", rel], cwd=ROOT, text=True
    ).strip()
    assert digest == actual, f"Uncommitted bytes: {rel}"
    return digest


def corpus():
    original = lines(SOURCES[0])
    patches = lines(SOURCES[1])
    header = patches.pop(0)["summary"]
    lookup = {(r["source"], r["message"]): r for r in original}
    assert len(lookup) == len(original) == 2872
    assert len(patches) == 53
    for p in patches:
        row = lookup[p["source"], p["message"]]
        assert row["standing_rules"] == p["old_standing_rules"]
        row["standing_rules"] = p["new_standing_rules"]
    rules = [s for r in original for s in r["standing_rules"]]
    assert len(rules) == header["after"]["rule_spans_total"] == 1448
    assert sum(not r["standing_rules"] for r in original) == 1642
    added = [r for r in lines(SOURCES[2]) if "message" in r]
    assert len(added) == 231
    rows = [dict(r, check44b_id=f"kimi:{i + 1}") for i, r in enumerate(original)]
    rows += [dict(r, check44b_id=r["id"]) for r in added]
    assert len({identity(r["message"]) for r in rows}) == len(rows)
    for r in rows:
        metrics.gold_spans(r)
        assert r["role"] == "user" or not r["standing_rules"]
    return rows


def identity(s):
    return " ".join(s.casefold().split())


def partition(rows):
    groups = sorted({r["domain"] for r in rows})
    random.Random(0).shuffle(groups)
    dev = set(groups[: round(0.1 * len(groups))])
    return [r for r in rows if r["domain"] not in dev], [
        r for r in rows if r["domain"] in dev
    ]


def label(span, row):
    return int(
        any(
            min(span["end"], g["end"]) > max(span["start"], g["start"])
            for g in metrics.gold_spans(row)
        )
    )


def calibrate(records):
    empty = [r for r in records if not r["input"]["standing_rules"]]
    assert empty
    thresholds = {0.0, math.nextafter(1.0, math.inf)}
    thresholds.update(
        p for r in records for p in r["C"]["probabilities"] if p is not None
    )
    budget = math.floor(0.02 * len(empty))
    # Admitted sets shrink with threshold; first feasible maximizes recall.
    for t in sorted(thresholds):
        errors = sum(
            bool(accepts(r["input"], r["C"]["spans"], r["C"]["probabilities"], t))
            for r in empty
        )
        if errors <= budget:
            return dict(
                threshold=t,
                false_admissions=errors,
                negative_messages=len(empty),
                rate=errors / len(empty),
                maximum_allowed=budget,
                selection="lowest feasible threshold; maximum overlap recall",
            )
    raise AssertionError("Abstain candidate must be feasible")


def scored(records, arm, threshold=None):
    for r in records:
        a = r[arm]
        if threshold is not None:
            a["accepted"] = accepts(
                r["input"], a["spans"], a["probabilities"], threshold
            )
        a["score"] = metrics.score(a["accepted"], r["input"])
    result = metrics.aggregate(records, arm)
    # No semantic key/scope heads: do not report guessed scores.
    result.pop("metadata")
    result["warm_cpu_latency_seconds"] = metrics.percentiles(
        [r[arm]["seconds"] for r in records[1:]]
    )
    return result


def prepare():
    assert not (OUT / "recipe.json").exists()
    for p in SOURCES:
        committed(p)
    rows = corpus()
    fit, dev = partition(rows)
    write(OUT / "corpus.json", rows)
    write(
        MODELS / "split.json",
        dict(
            fit_ids=[r["check44b_id"] for r in fit],
            dev_ids=[r["check44b_id"] for r in dev],
            dev_domains=sorted({r["domain"] for r in dev}),
        ),
    )
    ceiling = {}
    for name, subset in (("fit", fit), ("dev", dev)):
        gold = sum(len(r["standing_rules"]) for r in subset)
        tp = sum(
            len(metrics.match_spans(candidates(r), metrics.gold_spans(r), "overlap"))
            for r in subset
        )
        ceiling[name] = dict(
            messages=len(subset),
            gold_spans=gold,
            splitter_overlap_ceiling=tp / gold,
            reachable_spans=tp,
            gold_empty=sum(not r["standing_rules"] for r in subset),
            candidates=sum(len(candidates(r)) for r in subset),
        )
    paths = SOURCES + [
        Path(__file__),
        ROOT / "src/stencil/admission.py",
        ROOT / "src/stencil/focus3.py",
        ROOT / "scripts/focus_check44.py",
        OUT / "README.md",
        OUT / "corpus.json",
        MODELS / "split.json",
        BANK,
    ]
    for folder in (DATA / "model/ft-v3/seed0", DATA / "model/relations-v2/seed0"):
        paths.extend(
            p for p in folder.rglob("*") if p.is_file() and ".cache" not in p.parts
        )
    write(
        OUT / "recipe.json",
        dict(
            utc=time.time(),
            base=BASE,
            revision=REVISION,
            seeds=[0, 1, 2],
            designated=0,
            limit=LIMIT,
            epochs=3,
            batch_size=32,
            gpu_cap_seconds=CAP,
            corpus_counts=ceiling,
            hashes={str(p.relative_to(ROOT)): sha(p) for p in paths},
        ),
    )
    print(json.dumps(ceiling), flush=True)


def verify_recipe():
    recipe = json.loads((OUT / "recipe.json").read_text())
    for p, digest in recipe["hashes"].items():
        assert sha(ROOT / p) == digest, p
    return recipe


@contextlib.contextmanager
def gpu_claim():
    flag = OUT / "RUNNING.flag"
    assert not list((ROOT / "results/quick-checks").rglob("RUNNING.flag")), (
        "Other Stencil flag; wait"
    )
    query = subprocess.check_output(
        [
            "nvidia-smi",
            "--query-compute-apps=pid,process_name",
            "--format=csv,noheader",
        ],
        text=True,
    )
    for line in query.splitlines():
        pid, name = line.split(",", 1)
        assert pid.strip() == "2705" or "llama-server" in name, query
    with flag.open("x") as f:
        f.write(json.dumps(dict(pid=os.getpid(), start=time.time(), check="44b")))
    try:
        assert not [
            p
            for p in (ROOT / "results/quick-checks").rglob("RUNNING.flag")
            if p != flag
        ], "Concurrent claimant"
        yield query
    finally:
        flag.unlink()


def fit():
    import torch
    from safetensors.torch import save_file

    verify_recipe()
    assert not (OUT / "fit-start.json").exists(), "No reruns"
    torch.set_num_threads(4)
    fit_rows, dev = partition(json.loads((OUT / "corpus.json").read_text()))
    with gpu_claim() as query:
        started = time.monotonic()
        write(
            OUT / "fit-start.json",
            dict(
                utc=time.time(),
                pid=os.getpid(),
                gpu_query=query,
                recipe_sha256=sha(OUT / "recipe.json"),
            ),
        )
        deadline = started + CAP - 30
        results = []
        try:
            for seed in (0, 1, 2):
                torch.manual_seed(seed)
                random.seed(seed)
                model = Detector(device="cuda")
                examples = []
                overflows = 0
                for r in fit_rows:
                    spans, tokens = model.encode(r)
                    for s, t in zip(spans, tokens, strict=True):
                        if len(t["input_ids"]) <= LIMIT:
                            examples.append((t, label(s, r)))
                        else:
                            overflows += 1
                params = list(model.enc.parameters()) + list(model.head.parameters())
                opt = torch.optim.AdamW(params, lr=3e-5, weight_decay=0.01)
                steps = 3 * math.ceil(len(examples) / 32)
                sched = torch.optim.lr_scheduler.LambdaLR(
                    opt,
                    lambda s, steps=steps: (
                        min(1.0, (s + 1) / (0.06 * steps))
                        * max(0.0, (steps - s) / steps)
                    ),
                )
                seed_start = time.monotonic()
                losses = []
                updates = 0
                # First ten actual training updates are the training-only timing pilot.
                for epoch in range(3):
                    model.enc.train()
                    model.head.train()
                    random.shuffle(examples)
                    total = 0.0
                    for offset in range(0, len(examples), 32):
                        assert time.monotonic() < deadline, "Cooperative GPU cap"
                        chunk = examples[offset : offset + 32]
                        batch = model.tok.pad(
                            [t for t, _ in chunk], return_tensors="pt"
                        ).to("cuda")
                        y = torch.tensor([y for _, y in chunk], device="cuda")
                        opt.zero_grad(set_to_none=True)
                        logits = model.head(model.enc(**batch).last_hidden_state[:, 0])
                        loss = torch.nn.functional.cross_entropy(logits, y)
                        loss.backward()
                        torch.nn.utils.clip_grad_norm_(params, 1.0)
                        opt.step()
                        sched.step()
                        total += loss.item() * len(chunk)
                        updates += 1
                        if seed == 0 and updates == 10:
                            elapsed = time.monotonic() - seed_start
                            projection = 3 * steps * elapsed / 10 + 300
                            pilot = dict(
                                updates=10,
                                seconds=elapsed,
                                updates_per_second=10 / elapsed,
                                peak_allocated_GiB=torch.cuda.max_memory_allocated()
                                / 2**30,
                                projected_total_seconds=projection,
                                cap_seconds=CAP,
                            )
                            write(OUT / "pilot.json", pilot)
                            with (ROOT / "plan/LEDGER.md").open("a") as ledger:
                                ledger.write(
                                    "\n2026-09-06 — CHECK44B GPU PILOT: "
                                    f"{json.dumps(pilot)}.\n"
                                    "Continue matrix only if within cap.\n"
                                )
                            print("PILOT", json.dumps(pilot), flush=True)
                            assert projection < CAP - 30, (
                                "Cost-only stop before full matrix"
                            )
                    losses.append(total / len(examples))
                    print(
                        json.dumps(
                            dict(
                                seed=seed,
                                epoch=epoch + 1,
                                loss=losses[-1],
                                seconds=time.monotonic() - started,
                            )
                        ),
                        flush=True,
                    )
                path = MODELS / f"seed{seed}"
                path.mkdir()
                model.enc.to("cpu").save_pretrained(path / "encoder")
                model.tok.save_pretrained(path / "encoder")
                save_file(
                    model.head.to("cpu").state_dict(), str(path / "head.safetensors")
                )
                model.device = "cpu"
                del opt, sched, params, batch, y, logits, loss
                torch.cuda.empty_cache()
                records = [dict(input=r, C=model.infer(r)) for r in dev]
                threshold = calibrate(records)
                write(path / "threshold.json", threshold)
                summary = scored(records, "C", threshold["threshold"])
                write(path / "dev-records.json", records)
                result = dict(
                    seed=seed,
                    fit_candidates=len(examples),
                    fit_overflows=overflows,
                    steps=updates,
                    epoch_losses=losses,
                    seed_wall_seconds=time.monotonic() - seed_start,
                    threshold=threshold,
                    dev=summary,
                )
                write(path / "metadata.json", result)
                results.append(result)
                print(
                    "SEED",
                    seed,
                    json.dumps(
                        dict(
                            threshold=threshold,
                            overlap=summary["overlap"],
                            negatives=summary["all_negative"],
                        )
                    ),
                    flush=True,
                )
                del model
                assert time.monotonic() < deadline, "Cooperative allocation cap"
            files = [p for p in MODELS.rglob("*") if p.is_file()]
            write(
                OUT / "model-freeze.json",
                dict(
                    utc=time.time(),
                    recipe_sha256=sha(OUT / "recipe.json"),
                    designated_seed=0,
                    hashes={str(p.relative_to(ROOT)): sha(p) for p in files},
                ),
            )
        finally:
            write(
                OUT / "fit-summary.json",
                dict(
                    completed_seeds=len(results),
                    gpu_allocation_seconds=time.monotonic() - started,
                    peak_allocated_GiB=torch.cuda.max_memory_allocated() / 2**30,
                    seeds=results,
                ),
            )


def verify_models():
    verify_recipe()
    freeze = json.loads((OUT / "model-freeze.json").read_text())
    assert freeze["recipe_sha256"] == sha(OUT / "recipe.json")
    for p, digest in freeze["hashes"].items():
        assert sha(ROOT / p) == digest, p


def read_bank(raw):
    rows = [json.loads(s) for s in raw.decode().splitlines() if s.strip()]
    header = rows.pop(0)["summary"] if rows and set(rows[0]) == {"summary"} else None
    assert rows and all("message" in r and "standing_rules" in r for r in rows)
    if header and "rows" in header:
        assert len(rows) == header["rows"]
    for r in rows:
        metrics.gold_spans(r)
    return rows, header


def setup_rows():
    bank = json.loads(BANK.read_text())
    rows = []
    for ei, ep in enumerate(bank["setup"]):
        previous = ""
        for ti, turn in enumerate(ep["turns"]):
            rules = []
            for event in turn["events"]:
                if event["label"] in ("admit", "supersedes"):
                    s, e = metrics.unique_span(turn["text"], event["span"])
                    rules.append(
                        dict(
                            text=event["span"],
                            start=s,
                            end=e,
                            scope=event["scope"],
                            key=event.get("gold_key", f"order:{event['scope']}"),
                        )
                    )
            rows.append(
                dict(
                    id=f"setup:{ei}:{ti}",
                    role="user",
                    message=turn["text"],
                    previous_user=previous,
                    standing_rules=rules,
                    domain="v8-setup",
                    one_off_request=True,
                    quoted_or_reported=False,
                )
            )
            previous = turn["text"]
    assert len(rows) == 96
    return rows


def setup_summary(records, arm):
    result = scored(records, arm)
    false = [r for r in records if r[arm]["score"]["overlap"]["fp"]]
    request_false = []
    for r in records:
        start = r["input"]["message"].find("Sort request for task ")
        if start >= 0 and any(s["end"] > start for s in r[arm]["accepted"]):
            request_false.append(r["input"]["id"])
    result.update(
        false_admission_turns=metrics.rate(len(false), len(records)),
        false_turn_ids=[r["input"]["id"] for r in false],
        request_template_false_admissions=metrics.rate(
            len(request_false), len(records)
        ),
        request_false_turn_ids=request_false,
    )
    return result


def evaluate():
    import torch

    assert os.environ.get("CUDA_VISIBLE_DEVICES") == "", "CPU isolation required"
    verify_models()
    committed(OUT / "model-freeze.json")
    committed(HELDOUT)
    assert not (OUT / "evaluation-start.json").exists(), "One-shot guard"
    torch.set_num_threads(4)
    c, b = Detector(MODELS / "seed0"), metrics.Baseline()
    # No source content is opened until models and thresholds are frozen and committed.
    raw = HELDOUT.read_bytes()
    rows, header = read_bank(raw)
    fit_ids = {
        identity(r["message"]) for r in json.loads((OUT / "corpus.json").read_text())
    }
    assert not fit_ids & {identity(r["message"]) for r in rows}, (
        "Data-lineage collision; no salvage"
    )
    (OUT / "evaluation-bank.jsonl").write_bytes(raw)
    write(
        OUT / "evaluation-start.json",
        dict(
            utc=time.time(),
            n=len(rows),
            source_sha256=hashlib.sha256(raw).hexdigest(),
            header=header,
            model_freeze_sha256=sha(OUT / "model-freeze.json"),
            device="cpu",
            threads=4,
        ),
    )
    combined = {}
    for name, bank in (("heldout", rows), ("setup", setup_rows())):
        records = []
        with (OUT / f"{name}-records.jsonl").open("x") as journal:
            for i, row in enumerate(bank):
                ca = c.infer(row)
                ba, _ = b.infer(row)
                record = dict(index=i, input=row, C=ca, B=ba)
                for arm in ("C", "B"):
                    record[arm]["score"] = metrics.score(record[arm]["accepted"], row)
                assert {
                    "accepted",
                    "probabilities",
                    "spans",
                    "seconds",
                    "score",
                    "token_counts",
                } <= ca.keys()
                journal.write(json.dumps(record, ensure_ascii=False) + "\n")
                journal.flush()
                records.append(record)
                if i % 50 == 0:
                    print(name, i + 1, "/", len(bank), flush=True)
        combined[name] = {
            arm: (
                setup_summary(records, arm) if name == "setup" else scored(records, arm)
            )
            for arm in ("C", "B")
        }
    go = (
        combined["heldout"]["C"]["go"]
        and combined["setup"]["C"]["false_admission_turns"]["errors"] <= 2
    )
    write(
        OUT / "summary.json",
        dict(
            reading="GO" if go else "NO-GO",
            decision="Register C runtime swap; gate v9 authorized"
            if go
            else "Explicit structured rule entry; C assistive suggester only",
            **combined,
            fit=json.loads((OUT / "fit-summary.json").read_text()),
        ),
    )
    print("READING", "GO" if go else "NO-GO", flush=True)


def audit():
    verify_models()
    summary = json.loads((OUT / "summary.json").read_text())
    n = 0
    for name in ("heldout", "setup"):
        records = lines(OUT / f"{name}-records.jsonl")
        for i, r in enumerate(records):
            assert r["index"] == i
            ca = r["C"]
            threshold = json.loads((MODELS / "seed0/threshold.json").read_text())[
                "threshold"
            ]
            assert (
                accepts(r["input"], ca["spans"], ca["probabilities"], threshold)
                == ca["accepted"]
            )
            assert ca["spans"] == candidates(r["input"])
            assert all(
                (p is None) == (count > LIMIT)
                for p, count in zip(
                    ca["probabilities"], ca["token_counts"], strict=True
                )
            )
            for arm in ("C", "B"):
                assert json.dumps(
                    metrics.score(r[arm]["accepted"], r["input"]), sort_keys=True
                ) == json.dumps(r[arm]["score"], sort_keys=True)
        for arm in ("C", "B"):
            expected = (
                setup_summary(records, arm) if name == "setup" else scored(records, arm)
            )
            assert expected == summary[name][arm]
        n += len(records)
    for seed in (0, 1, 2):
        path = MODELS / f"seed{seed}"
        assert calibrate(
            json.loads((path / "dev-records.json").read_text())
        ) == json.loads((path / "threshold.json").read_text())
    assert summary["fit"]["completed_seeds"] == 3
    assert summary["fit"]["gpu_allocation_seconds"] <= CAP
    write(
        OUT / "audit.json",
        dict(
            status="PASS",
            records=n,
            all_scores_recomputed=True,
            thresholds_recomputed=True,
            frozen_hashes_verified=True,
            inference_repeated=False,
        ),
    )
    print("AUDIT PASS", n)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "fit", "evaluate", "audit"))
    args = parser.parse_args()
    globals()[args.mode]()


if __name__ == "__main__":
    main()
