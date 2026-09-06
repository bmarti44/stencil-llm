"""V8 data addition, using the unchanged v7 admission fitting recipe."""

from __future__ import annotations

import json
from collections import Counter

from scripts import finetune_admission_v2 as prior
from scripts import focus3_gate as g
from stencil import focus3 as f

ROOT, DATA = prior.ROOT, prior.DATA
OUT = ROOT / "results/quick-checks/focus3-gate/v8"
MODELS = DATA / "model/ft-v3"
ENRICHMENT = DATA / "ft-enrich-requests.jsonl"
BASE = ROOT / "results/quick-checks/focus3-gate/v7/training-rows.json"
LABELS, ROLES, REVISION = prior.LABELS, prior.ROLES, prior.REVISION
read, identity, split = prior.read, prior.identity, prior.split
metrics, infer, patches = prior.metrics, prior.infer, prior.patches
SOURCE = "astra-v8-requests"


def enrichment():
    rows = read(ENRICHMENT)
    counts = Counter(r["label"] for r in rows)
    assert counts["none"] >= 200 and counts["rule"] >= 100
    assert set(counts) == {"none", "rule"}
    assert len({r["domain"] for r in rows if r["label"] == "none"}) >= 10
    assert len({identity(r["text"]) for r in rows}) == len(rows)
    assert all(r.get("context") for r in rows if r["label"] == "rule")
    # Each hand-written target is one verbatim runtime sentence span.
    assert all(f.sentences(r["text"]) == [(0, r["text"])] for r in rows)
    return [
        dict(
            r,
            role="user",
            source=SOURCE,
            author="astra",
            source_row=i + 1,
            context=r.get("context", ""),
        )
        for i, r in enumerate(rows)
    ]


def corpus():
    frozen = json.loads((BASE.parent / "recipe-freeze.json").read_text())["hashes"]
    assert g.digest(BASE) == frozen[str(BASE.relative_to(ROOT))]
    original = json.loads(BASE.read_text())
    assert len(original) == 20634
    added = enrichment()
    bank = json.loads(
        (ROOT / "results/quick-checks/focus3-gate/v4/bank.json").read_text()
    )
    bank_sentences = {
        identity(s)
        for name in ("setup", "gate")
        for ep in bank[name]
        for turn in ep["turns"]
        for _, s in f.sentences(turn["text"])
    }
    retained, seen, drops = [], set(), []
    for row in original + added:
        key = identity(row["text"])
        duplicate = (key, row["role"], row["label"])
        if key in bank_sentences or duplicate in seen:
            drops.append(
                dict(
                    reason="gate sentence identity"
                    if key in bank_sentences
                    else "dedup",
                    row=row,
                )
            )
            continue
        seen.add(duplicate)
        retained.append(row)
    # Minimum enrichment is binding after exclusion, too.
    kept = [r for r in retained if r["source"] == SOURCE]
    assert sum(r["label"] == "none" for r in kept) >= 200
    assert sum(r["label"] == "rule" for r in kept) >= 100
    return retained, dict(
        original_n=len(original),
        original_sha256=g.digest(BASE),
        enrichment_n=len(added),
        enrichment_sha256=g.digest(ENRICHMENT),
        enrichment_labels=dict(Counter(r["label"] for r in added)),
        enrichment_domains=dict(Counter(r["domain"] for r in added)),
        retained_n=len(retained),
        retained_labels=dict(Counter(r["label"] for r in retained)),
        drops=drops,
    )


def family_metrics(rows, logits):
    indices = [i for i, r in enumerate(rows) if r["source"] == SOURCE]
    assert indices
    return metrics([rows[i] for i in indices], [logits[i] for i in indices])


def fit_seed(rows, seed, deadline):
    # The original function owns every optimizer/tokenization/update choice.
    old_path = prior.MODELS
    try:
        prior.MODELS = MODELS
        result = prior.fit_seed(rows, seed, deadline)
    finally:
        prior.MODELS = old_path
    saved = json.loads((MODELS / f"seed{seed}/dev-records.json").read_text())
    family = family_metrics([r["row"] for r in saved], [r["logits"] for r in saved])
    g.write(MODELS / f"seed{seed}/request-family-metrics.json", family)
    print(json.dumps(dict(seed=seed, request_family_dev=family)), flush=True)
    return result
