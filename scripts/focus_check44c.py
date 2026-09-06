"""Check44c: CPU data audit receipt, BIO fitting, DEV freeze, one-shot evaluation.

All executable work is under main. No benchmark or sealed IFEval inputs are used.
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import json
import math
import os
import random
import subprocess
import time
from collections import Counter, defaultdict
from pathlib import Path

from scripts import focus_check44 as metrics
from scripts import focus_check44b as prior
from stencil.admission import BASE, LIMIT, REVISION, accepts

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/quick-checks/check44c"
MODELS = ROOT / "data/classifier/model/admission-v2"
DATA = ROOT / "data/classifier"
SOURCES = prior.SOURCES + [
    DATA / "relations/kimi-admission-2.jsonl",
    DATA / "review/admission-2-astra-patch.jsonl",
]
HELDOUT = DATA / "heldout/fable-admission-heldout-3.jsonl"
SECONDARY = DATA / "heldout/fable-admission-heldout-2.jsonl"
write, lines, sha, committed, identity = (
    prior.write,
    prior.lines,
    prior.sha,
    prior.committed,
    prior.identity,
)
CAP = 3600


def corpus():
    rows = prior.corpus()
    extra = lines(SOURCES[3])
    patches = lines(SOURCES[4])
    assert patches[0]["summary"]["source_sha256"] == sha(SOURCES[3])
    lookup = {(r["source"], r["message"]): r for r in extra}
    assert len(lookup) == len(extra)
    dropped = set()
    for p in patches[1:]:
        key = p["source"], p["message"]
        row = lookup[key]
        assert row["standing_rules"] == p["old_standing_rules"]
        row["standing_rules"] = p["new_standing_rules"]
        if p["drop"]:
            dropped.add(key)
    rows += [
        dict(r, check44b_id=f"kimi2:{i + 1}")
        for i, r in enumerate(extra)
        if (r["source"], r["message"]) not in dropped
    ]
    seen = {}
    for r in rows:
        key = identity(r["message"])
        assert key not in seen, ("duplicate", r["check44b_id"], seen.get(key))
        seen[key] = r["check44b_id"]
        gold = sorted(metrics.gold_spans(r), key=lambda s: s["start"])
        assert all(
            a["end"] <= b["start"] for a, b in zip(gold, gold[1:], strict=False)
        ), r
        assert r["role"] == "user" or not gold, r
    return rows


def partition(rows):
    # Source-generation batches contain whole scenario/quote-pair families; never split a batch.
    groups = defaultdict(list)
    for r in rows:
        groups[(r["domain"], r["source"])].append(r)
    keys = sorted(groups)
    random.Random(0).shuffle(keys)
    target = round(0.1 * len(rows))
    chosen = []
    domains = set()
    for key in keys:
        if len(domains) < 6 and key[0] not in domains:
            chosen.append(key)
            domains.add(key[0])
    n = sum(len(groups[k]) for k in chosen)
    for key in keys:
        if key not in chosen and abs(n + len(groups[key]) - target) < abs(n - target):
            chosen.append(key)
            n += len(groups[key])
    chosen = set(chosen)
    fit = [r for r in rows if (r["domain"], r["source"]) not in chosen]
    dev = [r for r in rows if (r["domain"], r["source"]) in chosen]
    assert len({r["domain"] for r in dev}) >= 6
    assert not {(r["domain"], r["source"]) for r in fit} & chosen
    return fit, dev


def bio_labels(offsets, row):
    labels = [0 if e > s else -100 for s, e in offsets]
    occupied = set()
    for g in metrics.gold_spans(row):
        idx = [
            i
            for i, (s, e) in enumerate(offsets)
            if e > s and min(e, g["end"]) > max(s, g["start"])
        ]
        assert idx and not occupied.intersection(idx), (
            "unrepresentable gold token labels",
            row["check44b_id"],
        )
        occupied.update(idx)
        for j, i in enumerate(idx):
            labels[i] = 1 if j == 0 else 2
    return labels


def decode(message, offsets, probs):
    """BIO argmax; B begins a new run, orphan I begins a run, O closes it.

    Span confidence = arithmetic mean of P(B)+P(I) over the run.
    This produces separate adjacent B-started runs without a sentence splitter.
    """
    spans, scores, active, values = [], [], None, []

    def finish():
        if active is not None:
            s, e = active
            spans.append(dict(start=s, end=e, text=message[s:e]))
            scores.append(sum(values) / len(values))

    for (s, e), p in zip(offsets, probs, strict=True):
        if e <= s:
            finish()
            active, values = None, []
            continue
        tag = max(range(3), key=lambda k: p[k])
        if tag == 0:
            finish()
            active, values = None, []
        else:
            if tag == 1 or active is None:
                finish()
                active, values = [s, e], []
            else:
                active[1] = e
            values.append(p[1] + p[2])
    finish()
    return spans, scores


class Tagger:
    def __init__(self, path=None, device="cpu"):
        import torch
        from safetensors.torch import load_file
        from transformers import AutoModel, AutoTokenizer

        self.torch, self.device = torch, device
        source = Path(path) / "encoder" if path else BASE
        kw = dict(local_files_only=True)
        if not path:
            kw["revision"] = REVISION
        self.tok = AutoTokenizer.from_pretrained(source, **kw)
        assert self.tok.is_fast
        self.enc = AutoModel.from_pretrained(source, **kw).to(device)
        self.head = torch.nn.Sequential(
            torch.nn.Dropout(0.1), torch.nn.Linear(self.enc.config.hidden_size, 3)
        ).to(device)
        if path:
            self.head.load_state_dict(load_file(str(Path(path) / "head.safetensors")))

    def encode(self, row):
        # Role is an explicit guard; all text tokens receive whole-message context.
        t = self.tok(row["message"], return_offsets_mapping=True, truncation=False)
        offsets = t.pop("offset_mapping")
        return t, offsets

    def infer(self, row):
        started = time.monotonic()
        t, offsets = self.encode(row)
        overflow = len(t["input_ids"]) > LIMIT
        self.enc.eval()
        self.head.eval()
        if overflow:
            probs = [[1.0, 0.0, 0.0] for _ in offsets]
        else:
            with self.torch.inference_mode():
                batch = self.tok.pad([t], return_tensors="pt").to(self.device)
                logits = self.head(self.enc(**batch).last_hidden_state)[0]
                probs = logits.double().softmax(-1).cpu().tolist()
        spans, ps = decode(row["message"], offsets, probs)
        return dict(
            spans=spans,
            probabilities=ps,
            token_offsets=offsets,
            token_probabilities=probs,
            any_rule_score=max(ps, default=0.0),
            token_counts=[len(t["input_ids"])],
            overflow=int(overflow),
            accepted=[],
            role_guard=row["role"] != "user",
            seconds=time.monotonic() - started,
        )


def combine(row, c, b, t, tlow):
    spans = accepts(row, c["spans"], c["probabilities"], t)
    if row["role"] != "user" or c["overflow"]:
        return spans
    for s in b["accepted"]:
        # C2 is first; B only adds a sentence having no overlap with admitted C2 spans.
        if any(min(s["end"], a["end"]) > max(s["start"], a["start"]) for a in spans):
            continue
        p = max(
            (
                v[1] + v[2]
                for (x, y), v in zip(
                    c["token_offsets"], c["token_probabilities"], strict=True
                )
                if y > x and min(y, s["end"]) > max(x, s["start"])
            ),
            default=0.0,
        )
        if p >= tlow:
            spans.append(dict(s, fallback=True, c2_max_token_probability=p))
    return spans


def low_scores(r):
    c = r["C2"]
    return [
        max(
            (
                p[1] + p[2]
                for (x, y), p in zip(
                    c["token_offsets"], c["token_probabilities"], strict=True
                )
                if y > x and min(y, s["end"]) > max(x, s["start"])
            ),
            default=0.0,
        )
        for s in r["B"]["accepted"]
    ]


def calibrate(records):
    budget = math.floor(0.02 * sum(not r["input"]["standing_rules"] for r in records))
    empty = [r for r in records if not r["input"]["standing_rules"]]
    candidates = {0.0, math.nextafter(1.0, math.inf)}
    candidates.update(p for r in records for p in r["C2"]["probabilities"])
    derivation = []
    for t in sorted(candidates):
        fp = sum(
            bool(accepts(r["input"], r["C2"]["spans"], r["C2"]["probabilities"], t))
            for r in empty
        )
        derivation.append(dict(threshold=t, false_admissions=fp))
        if fp <= budget:
            break
    # For fixed C2 threshold, union is nested as low threshold decreases.
    lows = {0.0, math.nextafter(1.0, math.inf)}
    lows.update(p for r in records for p in low_scores(r))
    low_derivation = []
    for low in sorted(lows):
        fp = sum(bool(combine(r["input"], r["C2"], r["B"], t, low)) for r in empty)
        low_derivation.append(dict(threshold=low, false_admissions=fp))
        if fp <= budget:
            break
    return dict(
        t=t,
        t_low=low,
        negative_messages=len(empty),
        maximum_allowed=budget,
        c2_candidates=derivation,
        combination_candidates=low_derivation,
        selection="Lowest feasible >= threshold maximizes nested-set one-to-one overlap recall; same <=2% empty-message budget for C2 and combination.",
    )


def apply_thresholds(records, thresholds):
    for r in records:
        c = r["C2"]
        c["accepted"] = accepts(
            r["input"], c["spans"], c["probabilities"], thresholds["t"]
        )
        start = time.monotonic()
        accepted = combine(r["input"], c, r["B"], thresholds["t"], thresholds["t_low"])
        r["C2+B"] = dict(
            accepted=accepted,
            seconds=c["seconds"] + r["B"]["seconds"] + time.monotonic() - start,
        )
        for arm in ("C2", "C2+B", "B"):
            r[arm]["score"] = metrics.score(r[arm]["accepted"], r["input"])


def aggregate(records, arm):
    return prior.scored(records, arm)


def ceiling(rows, tok):
    gold = exact = overlap = total = overflow = 0
    for r in rows:
        enc = tok(r["message"], return_offsets_mapping=True, truncation=False)
        offsets = enc["offset_mapping"]
        overflow += len(enc["input_ids"]) > LIMIT
        ideal = []
        occupied = set()
        for g in metrics.gold_spans(r):
            gold += 1
            ix = [
                i
                for i, (s, e) in enumerate(offsets)
                if e > s and min(e, g["end"]) > max(s, g["start"])
            ]
            if not ix:
                continue
            shared = bool(occupied.intersection(ix))
            occupied.update(ix)
            if not shared:
                total += 1
                s, e = offsets[ix[0]][0], offsets[ix[-1]][1]
                exact += int(s == g["start"] and e == g["end"])
                ideal.append(dict(start=s, end=e))
        overlap += len(metrics.match_spans(ideal, metrics.gold_spans(r), "overlap"))
    return dict(
        gold_spans=gold,
        representable_token_runs=total,
        overlap_fraction=overlap / gold if gold else None,
        exact_boundary_fraction=exact / gold if gold else None,
        overflows=overflow,
        caveat="Token-run candidate ceiling is 100% when distinct gold spans map to nonempty disjoint token runs. Exact character edges inside a token cannot be represented; whole-message >512-token inputs abstain. B starts a new span even adjacent to B/I. Measured here, not assumed.",
    )


def prepare():
    assert os.environ.get("CUDA_VISIBLE_DEVICES") == ""
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
            dev_groups=sorted({(r["domain"], r["source"]) for r in dev}),
            dev_fraction=len(dev) / len(rows),
            grouping="whole domain/source-generation batch; no author scenario IDs available; not a claim of domain-disjointness or cross-batch semantic disjointness",
        ),
    )
    from transformers import AutoTokenizer

    tok = AutoTokenizer.from_pretrained(BASE, revision=REVISION, local_files_only=True)
    for r in rows:
        bio_labels(tok(r["message"], return_offsets_mapping=True)["offset_mapping"], r)
    receipts = {k: ceiling(sub, tok) for k, sub in [("fit", fit), ("dev", dev)]}
    paths = SOURCES + [
        Path(__file__),
        OUT / "README.md",
        OUT / "corpus.json",
        MODELS / "split.json",
        ROOT / "scripts/focus_check44.py",
        ROOT / "scripts/focus_check44b.py",
        ROOT / "src/stencil/admission.py",
        ROOT / "src/stencil/focus3.py",
        ROOT / "scripts/focus3_gate_v8.py",
    ]
    paths += [
        p
        for folder in ("ft-v3/seed0", "relations-v2/seed0")
        for p in (DATA / "model" / folder).rglob("*")
        if p.is_file() and ".cache" not in p.parts
    ]
    write(
        OUT / "recipe.json",
        dict(
            utc=time.time(),
            base=BASE,
            revision=REVISION,
            seeds=[0, 1, 2],
            designated_seed=0,
            primary_arm="C2+B",
            epochs=3,
            batch=32,
            lr=3e-5,
            cap_seconds=CAP,
            fit_messages=len(fit),
            dev_messages=len(dev),
            ceiling=receipts,
            hashes={str(p.relative_to(ROOT)): sha(p) for p in paths},
        ),
    )
    print(json.dumps(dict(fit=len(fit), dev=len(dev), ceiling=receipts)), flush=True)


def verify_recipe():
    recipe = json.loads((OUT / "recipe.json").read_text())
    for p, h in recipe["hashes"].items():
        assert sha(ROOT / p) == h, p
    return recipe


@contextlib.contextmanager
def gpu_claim():
    flag = OUT / "RUNNING.flag"
    assert not list((ROOT / "results/quick-checks").rglob("RUNNING.flag")), (
        "Other flag: wait"
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
        f.write(json.dumps(dict(pid=os.getpid(), utc=time.time(), check="44c")))
    try:
        assert not [
            p
            for p in (ROOT / "results/quick-checks").rglob("RUNNING.flag")
            if p != flag
        ]
        yield query
    finally:
        flag.unlink()


def fit_models():
    import torch
    from safetensors.torch import save_file

    verify_recipe()
    assert not (OUT / "fit-start.json").exists(), "No refitting"
    torch.set_num_threads(4)
    fit, dev = partition(json.loads((OUT / "corpus.json").read_text()))
    info = []
    with gpu_claim() as query:
        started = time.monotonic()
        deadline = started + CAP - 60
        write(
            OUT / "fit-start.json",
            dict(utc=time.time(), gpu_query=query, pid=os.getpid()),
        )
        try:
            for seed in (0, 1, 2):
                torch.manual_seed(seed)
                random.seed(seed)
                m = Tagger(device="cuda")
                examples = []
                for r in fit:
                    t, off = m.encode(r)
                    assert len(t["input_ids"]) <= LIMIT, "No fit truncation"
                    examples.append((t, bio_labels(off, r)))
                params = list(m.enc.parameters()) + list(m.head.parameters())
                opt = torch.optim.AdamW(params, lr=3e-5, weight_decay=0.01)
                steps = 3 * math.ceil(len(examples) / 32)
                sched = torch.optim.lr_scheduler.LambdaLR(
                    opt,
                    lambda s: (
                        min(1.0, (s + 1) / (0.06 * steps))
                        * max(0.0, (steps - s) / steps)
                    ),
                )
                losses = []
                updates = 0
                seed_start = time.monotonic()
                run_deadline = deadline
                for epoch in range(3):
                    m.enc.train()
                    m.head.train()
                    random.shuffle(examples)
                    loss_sum = 0
                    for start in range(0, len(examples), 32):
                        assert time.monotonic() < min(deadline, run_deadline), (
                            "Cooperative time budget reached"
                        )
                        chunk = examples[start : start + 32]
                        batch = m.tok.pad(
                            [x for x, y in chunk], return_tensors="pt"
                        ).to("cuda")
                        y = torch.full(
                            batch["input_ids"].shape,
                            -100,
                            device="cuda",
                            dtype=torch.long,
                        )
                        for i, (_, label) in enumerate(chunk):
                            y[i, : len(label)] = torch.tensor(label, device="cuda")
                        opt.zero_grad(set_to_none=True)
                        logits = m.head(m.enc(**batch).last_hidden_state)
                        loss = torch.nn.functional.cross_entropy(
                            logits.flatten(0, 1), y.flatten()
                        )
                        loss.backward()
                        torch.nn.utils.clip_grad_norm_(params, 1.0)
                        opt.step()
                        sched.step()
                        loss_sum += loss.item() * len(chunk)
                        updates += 1
                        if seed == 0 and updates == 10:
                            elapsed = time.monotonic() - seed_start
                            pilot = dict(
                                updates=10,
                                seconds=elapsed,
                                updates_per_second=10 / elapsed,
                                projected_gpu_seconds=3 * steps * elapsed / 10 + 120,
                                peak_GiB=torch.cuda.max_memory_allocated() / 2**30,
                                per_seed_timeout_seconds=4 * steps * elapsed / 10,
                            )
                            write(OUT / "pilot.json", pilot)
                            with (ROOT / "plan/LEDGER.md").open("a") as f:
                                f.write(
                                    "\n2026-09-06 — CHECK44C pilot: "
                                    + json.dumps(pilot)
                                    + ".\n"
                                )
                            print("PILOT", json.dumps(pilot), flush=True)
                            assert pilot["projected_gpu_seconds"] < CAP - 60, (
                                "Cost-only stop"
                            )
                        if updates == 10:
                            p = json.loads((OUT / "pilot.json").read_text())
                            run_deadline = seed_start + p["per_seed_timeout_seconds"]
                    losses.append(loss_sum / len(examples))
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
                m.enc.to("cpu").save_pretrained(path / "encoder")
                m.tok.save_pretrained(path / "encoder")
                save_file(m.head.to("cpu").state_dict(), str(path / "head.safetensors"))
                item = dict(
                    seed=seed,
                    updates=updates,
                    losses=losses,
                    seconds=time.monotonic() - seed_start,
                )
                write(path / "training.json", item)
                info.append(item)
                del opt, sched, params, batch, y, logits, loss, m
                torch.cuda.empty_cache()
                assert time.monotonic() < deadline
        finally:
            write(
                OUT / "fit-summary.json",
                dict(
                    gpu_allocation_seconds=time.monotonic() - started,
                    seeds=info,
                    peak_GiB=torch.cuda.max_memory_allocated() / 2**30,
                ),
            )


def freeze():
    import torch

    assert os.environ.get("CUDA_VISIBLE_DEVICES") == ""
    verify_recipe()
    assert not (OUT / "model-freeze.json").exists()
    torch.set_num_threads(4)
    _, dev = partition(json.loads((OUT / "corpus.json").read_text()))
    b = metrics.Baseline()
    brecords = [b.infer(r)[0] for r in dev]
    manifest = json.loads((DATA / "model/ft-v3/seed0/manifest.json").read_text())
    from stencil.focus3 import sentences

    fit_ids = set(manifest["fit_ids"])
    overlap = [
        dict(id=r["check44b_id"], text=s)
        for r in dev
        for _, s in sentences(r["message"])
        if identity(s) in fit_ids
    ]
    write(
        OUT / "b-dev-overlap.json",
        dict(
            overlap=overlap,
            n_overlap=len(overlap),
            dev_sentences=sum(len(sentences(r["message"])) for r in dev),
            definition="normalized DEV sentence in B manifest fit_ids; prior heldout2-informed combination form disclosed in README",
        ),
    )
    summaries = {}
    for seed in (0, 1, 2):
        m = Tagger(MODELS / f"seed{seed}")
        records = [
            dict(input=r, C2=m.infer(r), B=copy.deepcopy(br))
            for r, br in zip(dev, brecords, strict=True)
        ]
        threshold = calibrate(records)
        apply_thresholds(records, threshold)
        path = MODELS / f"seed{seed}"
        write(path / "threshold.json", threshold)
        write(OUT / f"seed{seed}-dev-records.json", records)
        summaries[str(seed)] = dict(
            threshold=threshold,
            metrics={a: aggregate(records, a) for a in ("C2", "C2+B", "B")},
        )
        print(
            "FROZEN SEED",
            seed,
            "t",
            threshold["t"],
            "low",
            threshold["t_low"],
            flush=True,
        )
        del m
    write(OUT / "dev-threshold-derivation.json", summaries)
    hashes = {
        str(p.relative_to(ROOT)): sha(p) for p in MODELS.rglob("*") if p.is_file()
    }
    write(
        MODELS / "manifest.json",
        dict(
            utc=time.time(),
            architecture="BGE fully finetuned BIO head O/B/I, whole message",
            base=BASE,
            revision=REVISION,
            designated_seed=0,
            primary_arm="C2+B",
            hashes=hashes,
            recipe_sha256=sha(OUT / "recipe.json"),
        ),
    )
    hashes[str((MODELS / "manifest.json").relative_to(ROOT))] = sha(
        MODELS / "manifest.json"
    )
    write(
        OUT / "model-freeze.json",
        dict(utc=time.time(), recipe_sha256=sha(OUT / "recipe.json"), hashes=hashes),
    )


def verify_models():
    verify_recipe()
    f = json.loads((OUT / "model-freeze.json").read_text())
    assert f["recipe_sha256"] == sha(OUT / "recipe.json")
    for p, h in f["hashes"].items():
        assert sha(ROOT / p) == h, p


def setup_summary(records, arm):
    summary = prior.setup_summary(records, arm)
    # Match admit separately from supersedes without double-crediting a prediction.
    counts = Counter()
    recovered = Counter()
    for r in records:
        g = r["input"]["standing_rules"]
        pairs = metrics.match_spans(r[arm]["accepted"], g, "overlap")
        counts.update(s["event"] for s in g)
        recovered.update(g[j]["event"] for _, j in pairs)
    assert counts["admit"] == 36 and counts["supersedes"] == 4
    summary["events"] = {k: dict(recovered=recovered[k], n=counts[k]) for k in counts}
    return summary


def setup_rows():
    rows = prior.setup_rows()
    bank = json.loads(prior.BANK.read_text())
    turns = [t for ep in bank["setup"] for t in ep["turns"]]
    for r, t in zip(rows, turns, strict=True):
        events = [e for e in t["events"] if e["label"] in ("admit", "supersedes")]
        for g, e in zip(r["standing_rules"], events, strict=True):
            g["event"] = e["label"]
    return rows


def evaluate():
    import torch

    assert os.environ.get("CUDA_VISIBLE_DEVICES") == ""
    verify_models()
    committed(OUT / "model-freeze.json")
    committed(HELDOUT)
    assert not (OUT / "evaluation-start.json").exists(), "ONE LOOK only"
    torch.set_num_threads(4)
    c = Tagger(MODELS / "seed0")
    b = metrics.Baseline()
    threshold = json.loads((MODELS / "seed0/threshold.json").read_text())
    # Durable receipt before opening the fresh bank. No selection after this point.
    write(
        OUT / "evaluation-start.json",
        dict(
            utc=time.time(),
            heldout_commit=committed(HELDOUT),
            freeze_sha256=sha(OUT / "model-freeze.json"),
            device="cpu",
            threads=4,
        ),
    )
    rows, header = prior.read_bank(HELDOUT.read_bytes())
    corpus_ids = {
        identity(r["message"]) for r in json.loads((OUT / "corpus.json").read_text())
    }
    assert not corpus_ids & {identity(r["message"]) for r in rows}, (
        "Data collision; no salvage"
    )
    (OUT / "evaluation-bank.jsonl").write_bytes(HELDOUT.read_bytes())
    combined = {}
    banks = [
        ("heldout3", rows),
        ("heldout2", prior.read_bank(SECONDARY.read_bytes())[0]),
        ("setup", setup_rows()),
    ]
    for name, bank in banks:
        records = []
        with (OUT / f"{name}-records.jsonl").open("x") as journal:
            for i, row in enumerate(bank):
                record = dict(index=i, input=row, C2=c.infer(row), B=b.infer(row)[0])
                apply_thresholds([record], threshold)
                assert {
                    "token_offsets",
                    "token_probabilities",
                    "accepted",
                    "spans",
                    "probabilities",
                    "seconds",
                    "score",
                } <= record["C2"].keys()
                journal.write(json.dumps(record, ensure_ascii=False) + "\n")
                journal.flush()
                records.append(record)
                if i % 50 == 0:
                    print(name, i + 1, "/", len(bank), flush=True)
        combined[name] = {
            a: setup_summary(records, a) if name == "setup" else aggregate(records, a)
            for a in ("C2", "C2+B")
        }
        combined[name]["candidate_ceiling"] = ceiling(bank, c.tok)
    arm_go = {
        a: combined["heldout3"][a]["go"]
        and combined["setup"][a]["false_admission_turns"]["errors"] <= 2
        and combined["setup"][a]["events"]["admit"]["recovered"] == 36
        for a in ("C2", "C2+B")
    }
    go = arm_go["C2+B"]
    write(
        OUT / "summary.json",
        dict(
            reading="GO" if go else "NO-GO",
            arm_go=arm_go,
            designated_seed=0,
            primary_arm="C2+B",
            decision="Register frozen C2+B runtime swap and authorize gate v9: explicit structured entry OR frozen automatic candidate, both reported."
            if go
            else "Explicit structured entry remains first ship; no runtime swap or gate v9 authorization.",
            heldout3_header=header,
            heldout3_sha256=sha(HELDOUT),
            heldout2_sha256=sha(SECONDARY),
            setup_sha256=sha(prior.BANK),
            fit=json.loads((OUT / "fit-summary.json").read_text()),
            **combined,
        ),
    )
    print("READING", "GO" if go else "NO-GO", flush=True)


def audit():
    verify_models()
    summary = json.loads((OUT / "summary.json").read_text())
    threshold = json.loads((MODELS / "seed0/threshold.json").read_text())
    n = 0
    for name in ("heldout3", "heldout2", "setup"):
        records = lines(OUT / f"{name}-records.jsonl")
        for i, r in enumerate(records):
            assert r["index"] == i
            c = r["C2"]
            sp, ps = decode(
                r["input"]["message"], c["token_offsets"], c["token_probabilities"]
            )
            assert sp == c["spans"] and ps == c["probabilities"]
            assert accepts(r["input"], sp, ps, threshold["t"]) == c["accepted"]
            assert (
                combine(r["input"], c, r["B"], threshold["t"], threshold["t_low"])
                == r["C2+B"]["accepted"]
            )
            for a in ("C2", "C2+B", "B"):
                assert metrics.score(r[a]["accepted"], r["input"]) == r[a]["score"]
            n += 1
        for a in ("C2", "C2+B"):
            actual = (
                setup_summary(records, a) if name == "setup" else aggregate(records, a)
            )
            assert actual == summary[name][a], (name, a)
    write(
        OUT / "audit.json",
        dict(
            records=n,
            passed=True,
            method="Re-decode saved token distributions; reproduce threshold acceptance, C-then-B union, matching, all summary metrics. No repeated inference.",
        ),
    )
    print("AUDIT", n, flush=True)


def selftest():
    row = dict(
        message="A; B.",
        role="user",
        check44b_id="test",
        standing_rules=[dict(start=0, end=1, text="A"), dict(start=3, end=4, text="B")],
    )
    off = [(0, 0), (0, 1), (1, 2), (3, 4), (4, 5), (0, 0)]
    y = bio_labels(off, row)
    assert y == [-100, 1, 0, 1, 0, -100]
    probs = [
        [1.0, 0.0, 0.0],
        [0.01, 0.98, 0.01],
        [0.99, 0.005, 0.005],
        [0.02, 0.97, 0.01],
        [0.99, 0.005, 0.005],
        [1.0, 0.0, 0.0],
    ]
    sp, ps = decode(row["message"], off, probs)
    assert [(s["start"], s["end"]) for s in sp] == [(0, 1), (3, 4)]
    # Adjacent B labels can separate rules with no O between them; orphan I repaired.
    sp, _ = decode("AB", [(0, 1), (1, 2)], [[0.0, 1.0, 0.0], [0.0, 1.0, 0.0]])
    assert len(sp) == 2
    sp, _ = decode("AB", [(0, 1), (1, 2)], [[0.0, 0.0, 1.0], [0.0, 0.0, 1.0]])
    assert len(sp) == 1 and sp[0]["text"] == "AB"
    c = dict(
        spans=[],
        probabilities=[],
        token_offsets=off,
        token_probabilities=probs,
        overflow=0,
    )
    b = dict(accepted=[dict(start=0, end=5, text="A; B.")])
    assert len(combine(row, c, b, 0.9, 0.98)) == 1
    assert not combine(dict(row, role="tool"), c, b, 0.9, 0.0)
    print("SELFTEST passed")


def main():
    p = argparse.ArgumentParser()
    p.add_argument(
        "mode",
        choices=["prepare", "fit", "freeze", "evaluate", "audit", "selftest", "poll"],
    )
    a = p.parse_args()
    if a.mode == "poll":
        try:
            print("COMMITTED", committed(HELDOUT))
        except subprocess.CalledProcessError:
            print("NOT COMMITTED")
    else:
        dict(
            prepare=prepare,
            fit=fit_models,
            freeze=freeze,
            evaluate=evaluate,
            audit=audit,
            selftest=selftest,
        )[a.mode]()


if __name__ == "__main__":
    main()
