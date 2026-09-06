"""One registered admission refit; no evaluation inputs in preparation/training."""

from __future__ import annotations

import json
import random
import re
import time
from collections import Counter

import numpy as np

from scripts import focus3_gate as g
from stencil import focus3 as f

ROOT = g.ROOT
DATA = ROOT / "data/classifier"
OUT = ROOT / "results/quick-checks/focus3-gate/v7"
MODELS = DATA / "model/ft-v2"
LABELS = ["none", "rule", "fact"]
ROLES = ["user", "assistant", "tool", "system"]
REVISION = "5c38ec7c405ec4b44b94cc5a9bb96e735b38267a"
PATCH_NAMES = [
    "opus-patch",
    "scope-exemplar-patch",
    "scope-pass-opus-patch",
    "scope-pass-sol-patch",
    "scope-v2-final-patch",
    "sol-patch",
]


def read(path):
    return [json.loads(s) for s in path.read_text().splitlines() if s.strip()]


def identity(text):
    return " ".join(text.lower().split())


def patches():
    result, skipped = {}, 0
    for name in PATCH_NAMES:
        for row in read(DATA / "review" / (name + ".jsonl")):
            reason = (row.get("reason") or "").lower()
            if row.get("drop") and (
                "mirrors bench" in reason or "benchmark-taxonomy" in reason
            ):
                skipped += 1
                continue
            result[row.get("source"), row.get("text")] = row
    return result, skipped


def training_sources():
    return sorted(
        [
            *DATA.glob("kimi/*.jsonl"),
            *DATA.glob("kimi-ctx/*.jsonl"),
            *DATA.glob("kimi-scope/*.jsonl"),
            *DATA.glob("*-enrich.jsonl"),
        ]
    )


def load_original():
    patch, skipped = patches()
    fixed, seen = [], set()
    for path in training_sources():
        for original in read(path):
            o = dict(original)
            if (
                o.get("label") not in LABELS
                or o.get("role") not in ROLES
                or not isinstance(o.get("text"), str)
            ):
                continue
            pt = patch.get((o.get("source"), o["text"]))
            if pt:
                if pt.get("drop"):
                    continue
                if pt.get("new_label") in LABELS:
                    o["label"] = pt["new_label"]
                if pt.get("new_role") in ROLES:
                    o["role"] = pt["new_role"]
            if "context" in o:
                if isinstance(o["context"], list):
                    o["context"] = " ".join(str(x) for x in o["context"])
                elif not isinstance(o["context"], str):
                    o["context"] = ""
                o["text"] = re.sub(
                    r"^(?:user|assistant|tool|system)\s*:\s*",
                    "",
                    o["text"].strip(),
                    flags=re.I,
                )
                ctx = (o.get("context") or "").strip()
                core = re.sub(
                    r"^(?:user|assistant|tool|system)\s*:\s*", "", ctx, flags=re.I
                )
                if not ctx or core.strip().lower() == o["text"].strip().lower():
                    o["context"] = ""
            key = (o["text"].strip().lower(), o["label"], o["role"])
            if key not in seen:
                seen.add(key)
                fixed.append(o)
    assert len(fixed) == 20054, "Original ft corpus drift"
    return fixed, skipped


def negative_rows():
    result, selected = [], Counter()
    for name in ["opus-enrich-2", "kimi-transitions", "kimi-relations"]:
        for index, row in enumerate(read(DATA / "relations" / (name + ".jsonl"))):
            if name == "opus-enrich-2":
                use = index < 150
            else:
                use = (
                    row.get("label") == "none"
                    and row.get("hard") is True
                    and not row.get("message_new_rule")
                    and not row.get("new_rule_spans")
                    and bool(
                        re.search(
                            r"quot|report|inert|sample|citation",
                            row.get("why", ""),
                            re.I,
                        )
                    )
                )
            if not use:
                continue
            assert row["label"] == "none" and not row.get("new_rule_spans")
            selected[name] += 1
            prior = []
            for start, span in f.sentences(row["message"]):
                result.append(
                    dict(
                        text=span,
                        role=row["role"],
                        label="none",
                        context=" ".join(row["role"] + ": " + s for s in prior[-3:]),
                        source=name + ":quoted-none",
                        author=row.get("author", name.split("-")[0]),
                        source_file=name + ".jsonl",
                        source_row=index + 1,
                        message_id=name + ":" + str(index + 1),
                        start=start,
                    )
                )
                prior.append(span)
    assert selected["opus-enrich-2"] == 150
    return result, dict(selected)


def corpus():
    original, skipped = load_original()
    negatives, selected = negative_rows()
    # Exact sentence identity exclusion only; the bank never supplies examples.
    bank = json.loads(
        (ROOT / "results/quick-checks/focus3-gate/v4/bank.json").read_text()
    )
    bank_sentences = {
        identity(s)
        for split in ["setup", "gate"]
        for ep in bank[split]
        for turn in ep["turns"]
        for _, s in f.sentences(turn["text"])
    }
    seen, retained, drops = set(), [], []
    for row in original + negatives:
        key = identity(row["text"])
        if key in bank_sentences:
            drops.append(dict(reason="gate sentence identity", row=row))
            continue
        duplicate = (key, row["role"], row["label"])
        if duplicate in seen:
            drops.append(dict(reason="dedup", row=row))
            continue
        seen.add(duplicate)
        retained.append(row)
    return retained, dict(
        original_n=len(original),
        selected_messages=selected,
        negative_sentences=len(negatives),
        retained_n=len(retained),
        retained_labels=dict(Counter(r["label"] for r in retained)),
        retained_sources=dict(Counter(r["source"].split(":")[0] for r in retained)),
        taxonomy_category_drops_skipped=skipped,
        drops=drops,
    )


def split(rows, seed):
    # Sentence identity is global, regardless of role/label/context variants.
    keys = sorted({identity(r["text"]) for r in rows})
    random.Random(seed).shuffle(keys)
    dev = set(keys[: round(len(keys) * 0.1)])
    return (
        [r for r in rows if identity(r["text"]) not in dev],
        [r for r in rows if identity(r["text"]) in dev],
    )


def metrics(rows, logits):
    logits = np.asarray(logits, dtype=np.float64)
    probs = np.exp(logits - logits.max(1, keepdims=True))
    probs /= probs.sum(1, keepdims=True)
    y = np.array([LABELS.index(r["label"]) for r in rows])
    pred = probs.argmax(1)
    admitted = probs[:, 1] >= 0.95
    confusion = [
        [int(((y == a) & (pred == b)).sum()) for b in range(3)] for a in range(3)
    ]
    return dict(
        n=len(rows),
        correct=int((y == pred).sum()),
        accuracy=float((y == pred).mean()),
        confusion=confusion,
        admission_threshold=0.95,
        rule_support=int((y == 1).sum()),
        rule_admitted=int((admitted & (y == 1)).sum()),
        nonrule_support=int((y != 1).sum()),
        nonrule_admitted=int((admitted & (y != 1)).sum()),
    )


def batches(rows, tok, torch, device, shuffle=False, bs=32):
    idx = list(range(len(rows)))
    if shuffle:
        random.shuffle(idx)
    for start in range(0, len(idx), bs):
        chunk = [rows[i] for i in idx[start : start + bs]]
        tokens = tok(
            [(r.get("context") or "(no context)") for r in chunk],
            [f"[{r['role']}] {r['text']}" for r in chunk],
            padding=True,
            truncation="only_first",
            max_length=192,
            return_tensors="pt",
        )
        roles = torch.tensor(
            [[float(r["role"] == role) for role in ROLES] for r in chunk], device=device
        )
        y = torch.tensor([LABELS.index(r["label"]) for r in chunk], device=device)
        yield tokens.to(device), roles, y


def infer(rows, tok, enc, head, torch, device):
    enc.eval()
    head.eval()
    result = []
    with torch.inference_mode():
        for tokens, roles, _ in batches(rows, tok, torch, device, bs=64):
            logits = head(torch.cat([enc(**tokens).last_hidden_state[:, 0], roles], 1))
            result.extend(logits.cpu().tolist())
    return result


def fit_seed(rows, seed, deadline):
    import torch
    from transformers import AutoModel, AutoTokenizer

    torch.set_num_threads(4)
    torch.manual_seed(seed)
    random.seed(seed)
    np.random.seed(seed)
    fit, dev = split(rows, seed)
    path = MODELS / f"seed{seed}"
    assert not path.exists()
    tok = AutoTokenizer.from_pretrained(
        "BAAI/bge-small-en-v1.5", revision=REVISION, local_files_only=True
    )
    enc = AutoModel.from_pretrained(
        "BAAI/bge-small-en-v1.5", revision=REVISION, local_files_only=True
    ).to("cuda")
    head = torch.nn.Sequential(
        torch.nn.Dropout(0.1), torch.nn.Linear(enc.config.hidden_size + 4, 3)
    ).to("cuda")
    params = list(enc.parameters()) + list(head.parameters())
    opt = torch.optim.AdamW(params, lr=3e-5, weight_decay=0.01)
    steps = 3 * ((len(fit) + 31) // 32)
    sched = torch.optim.lr_scheduler.LambdaLR(
        opt,
        lambda s: min(1.0, (s + 1) / (0.06 * steps)) * max(0.0, (steps - s) / steps),
    )
    started = time.monotonic()
    for epoch in range(3):
        enc.train()
        head.train()
        total, n = 0.0, 0
        for tokens, roles, y in batches(fit, tok, torch, "cuda", shuffle=True):
            if time.monotonic() >= deadline:
                raise RuntimeError("Cooperative GPU budget exhausted")
            loss = torch.nn.functional.cross_entropy(
                head(torch.cat([enc(**tokens).last_hidden_state[:, 0], roles], 1)), y
            )
            opt.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(params, 1.0)
            opt.step()
            sched.step()
            total += loss.item() * len(y)
            n += len(y)
        print(
            json.dumps(
                dict(
                    seed=seed,
                    epoch=epoch + 1,
                    loss=total / n,
                    seconds=time.monotonic() - started,
                )
            ),
            flush=True,
        )
    logits = infer(dev, tok, enc, head, torch, "cuda")
    result = metrics(dev, logits)
    path.mkdir(parents=True)
    enc.cpu().save_pretrained(path / "encoder")
    tok.save_pretrained(path / "encoder")
    torch.save(
        dict(
            head=head.cpu().state_dict(),
            labels=LABELS,
            roles=ROLES,
            hidden=enc.config.hidden_size,
        ),
        path / "head.pt",
    )
    g.write(
        path / "dev-records.json",
        [dict(row=r, logits=values) for r, values in zip(dev, logits, strict=True)],
    )
    g.write(path / "metrics.json", result)
    manifest = dict(
        seed=seed,
        epochs=3,
        steps=steps,
        fit_n=len(fit),
        dev_n=len(dev),
        revision=REVISION,
        seconds=time.monotonic() - started,
        threshold=0.95,
        fit_ids=[identity(r["text"]) for r in fit],
        dev_ids=[identity(r["text"]) for r in dev],
        artifact_sha256={
            str(p.relative_to(path)): g.digest(p)
            for p in sorted(path.rglob("*"))
            if p.is_file()
        },
    )
    g.write(path / "manifest.json", manifest)
    print(
        json.dumps(dict(seed=seed, dev=result, seconds=manifest["seconds"])), flush=True
    )
    del enc, head, opt, params
    torch.cuda.empty_cache()
    return result
