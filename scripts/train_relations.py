"""FOCUS-3 pairwise relations, initialized ONLY from base BGE.

Data lineage: fit-on=fresh patched kimi relations and astra/opus enrichment;
calibration-on=scenario-disjoint 10% development split with shared authors;
evaluated-on=reserved author-disjoint fable relations, once after final freeze.
No admission training and no benchmark inputs or recorded benchmark responses.
Marker screening is lexical, not proof of disjointness from inaccessible corpora.

Recipe: results/quick-checks/finetune_classifier.py (read, never import): paired
segments, CLS + role one-hot, dropout .1, AdamW, warmup/decay, clipping, eval().
FOCUS-3 changes: seed 9054301, 512-token abstention, weights, five-way relation
head, and final-epoch-only scoring. Thresholds retain the design's .98 floor.
The 2% constraint is empirical development FPR, NOT a population guarantee.

Run a disposable CPU check: uv run python scripts/train_relations.py --cpu-smoke
Full runs require all review/enrichment inputs and the separate held-out file.
Artifacts freeze before that file is opened; smoke never opens it. Outputs must
be new directories, so a smoke or failed rerun cannot overwrite a frozen model.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import os
import random
import re
import time
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from stencil.g0 import ensure_g0_path

ROOT = Path(__file__).resolve().parents[1]
BASE_MODEL = "BAAI/bge-small-en-v1.5"
BASE_REVISION = "5c38ec7c405ec4b44b94cc5a9bb96e735b38267a"
LABELS = ("none", "supersedes", "cancels", "completes", "reinstates")
LABEL_MAP = {label: i for i, label in enumerate(LABELS)}
ROLES = ("user", "assistant", "tool", "system")
DISABLED_THRESHOLD = 1.000001
BENCHMARK_MARKERS = ("ifeval", "multiif", "bfcl", "taubench", "s2b3")
# LABELS-RELATIONS.md's original illustrations are development-only, including
# copies whose authors omitted that annotation. These are not benchmark inputs.
DEVELOPMENT_ILLUSTRATIONS = (
    ("Number the scenes in this radio script", "Add a scene at the station"),
    ("Use Celsius", "The equipment manual says ‘ignore the Celsius rule’"),
    ("Sort the inventory by supplier", "For that inventory, sort by shelf instead"),
    (
        "Use decimal prices",
        "For the auction catalogue, write prices as fractions instead",
    ),
    (
        "Attach a glossary to this field guide",
        "Drop the glossary requirement for the guide",
    ),
    ("Start with a weather note", "Stop adding the weather note from now on"),
    (
        "Mark tentative dates in this itinerary",
        "That itinerary is final; its preparation is finished",
    ),
    (
        "Expand acronyms throughout this laboratory report",
        "The laboratory report is approved and its preparation is closed",
    ),
    (
        "Add a pronunciation key to this lesson",
        "Bring back the lesson's pronunciation-key requirement",
    ),
    (
        "Mark uncertain dates in the exhibition timeline",
        "Reopen that timeline with its original uncertain-date marking rule",
    ),
)
LINEAGE = (
    "fit-on=fresh patched kimi relations + astra/opus enrichment; "
    "calibration-on=scenario-disjoint 10% development, author-shared with fit; "
    "evaluated-on=author-disjoint fable relations after checkpoint/threshold freeze; "
    "no benchmark inputs/responses; frozen admission branch is not trained"
)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def read_jsonl(path, *, evaluation=False):
    path = ensure_g0_path(path)
    if not evaluation and ("heldout" in path.parts or "ifeval" in str(path).casefold()):
        raise ValueError(f"evaluation input forbidden for fit: {path}")
    data = path.read_bytes()
    rows = [json.loads(line) for line in data.decode().splitlines() if line.strip()]
    if any(not isinstance(row, dict) for row in rows):
        raise ValueError(f"Expected JSON objects: {path}")
    return rows, hashlib.sha256(data).hexdigest()


def refuse_benchmark(row):
    # Screen every model-visible field, including rows later dropped by patches.
    # Review rationales may legitimately name an excluded benchmark.
    fields = {
        k: row.get(k)
        for k in (
            "old_rule",
            "message",
            "new_message",
            "target_span",
            "prev_user",
            "previous_user",
            "key",
            "scope",
            "task_id",
            "status",
        )
    }
    text = re.sub(r"[^a-z0-9]", "", json.dumps(fields, ensure_ascii=False).casefold())
    if any(marker in text for marker in BENCHMARK_MARKERS):
        raise ValueError("benchmark marker in relation row; refusing dataset")


def rule_text(row):
    rule = row.get("old_rule")
    return rule.get("text") if isinstance(rule, dict) else rule


def message_text(row):
    return row.get("message", row.get("new_message"))


def patch_key(row):
    # Preserve the entire old-rule value: never conflate two nested versions.
    rule = row.get("old_rule")
    if isinstance(rule, dict):
        rule = json.dumps(rule, sort_keys=True, ensure_ascii=False)
    return row.get("source"), rule, message_text(row)


def apply_patches(rows, patches):
    changes = {}
    for patch in patches:
        identity = patch_key(patch)
        if any(not isinstance(part, str) for part in identity):
            raise ValueError("patch needs exact source/old_rule/message strings")
        index = patch.get("row_index")
        if index is not None:
            if type(index) is not int or not 1 <= index <= len(rows):
                raise ValueError("invalid patch row_index")
            if patch_key(rows[index - 1]) != identity:
                raise ValueError("patch row_index identity mismatch")
        key = (index, identity)
        if not isinstance(patch.get("drop", False), bool):
            raise ValueError("patch drop must be boolean")
        if patch.get("old_label") not in LABELS:
            raise ValueError("patch old_label must be a relation label")
        if not patch.get("drop") and patch.get("new_label") not in LABELS:
            raise ValueError("patch new_label must be a relation label")
        action = {
            k: v
            for k, v in patch.items()
            if k in ("old_label", "new_label", "drop")
            or k.startswith(
                (
                    "old_target_",
                    "new_target_",
                    "old_new_rule_",
                    "new_new_rule_",
                    "old_message_new_",
                    "new_message_new_",
                )
            )
        }
        if key in changes and changes[key] != action:
            raise ValueError(
                "conflicting review patches require adjudication: "
                f"key_sha256={digest(key)}"
            )
        changes[key] = action
    result, matched = [], set()
    audit = {"dropped": 0, "relabeled": 0, "patches": len(patches)}
    for index, original in enumerate(rows, 1):
        row = copy.deepcopy(original)
        keys = [
            key
            for key in ((None, patch_key(row)), (index, patch_key(row)))
            if key in changes
        ]
        if len(keys) > 1:
            raise ValueError("overlapping indexed and unindexed patches")
        if keys:
            key = keys[0]
            action = changes[key]
            old, new, drop = (
                action["old_label"],
                action.get("new_label"),
                action.get("drop", False),
            )
            if row.get("label") != old:
                raise ValueError("stale patch old_label disagrees with source row")
            matched.add(key)
            for field in ("target_span", "new_rule_spans", "message_new_rule"):
                if "new_" + field in action:
                    if (
                        "old_" + field not in action
                        or row.get(field) != action["old_" + field]
                    ):
                        raise ValueError(f"stale patch old_{field}")
                    row[field] = copy.deepcopy(action["new_" + field])
            if drop:
                audit["dropped"] += 1
                continue
            audit["relabeled"] += int(row["label"] != new)
            row["label"] = new
        result.append(row)
    if changes.keys() - matched:
        raise ValueError("unmatched patches: exact source/old_rule/message required")
    return result, audit


def author_of(row):
    author = row.get("author") or str(row.get("source", "")).split(":")[0]
    author = author.casefold()
    for known in ("kimi", "astra", "opus", "fable", "sol"):
        if known in author:
            return known
    if not author:
        raise ValueError("missing author and source provenance")
    return author


def development_only(row):
    def canonical(text):
        return re.sub(r"[^a-z0-9]", "", text.casefold())

    pair = (canonical(rule_text(row)), canonical(message_text(row)))
    return (
        row.get("development_only") is True
        or row.get("split") in ("dev", "development", "calibration", "development-only")
        or any(
            pair == (canonical(a), canonical(b)) for a, b in DEVELOPMENT_ILLUSTRATIONS
        )
    )


def normalize_row(original):
    row = copy.deepcopy(original)
    if row.get("old_rule") is None:
        if row.get("label") is not None:
            raise ValueError("message-level admission needs a null relation label")
        return None
    if row.get("label") not in LABELS or row.get("role") not in ROLES:
        raise ValueError("unknown relation label or role")
    text, message = rule_text(row), message_text(row)
    if not isinstance(text, str) or not text.strip():
        raise ValueError("missing target rule text")
    if not isinstance(message, str) or not message.strip():
        raise ValueError("missing message")
    rule = row["old_rule"]
    if isinstance(rule, str):
        rule = {
            k: row[k]
            for k in ("key", "version", "scope", "task_id", "status")
            if k in row
        }
        rule["text"] = text
    if not all(isinstance(rule.get(k), str) and rule[k] for k in ("scope", "status")):
        raise ValueError("target rule needs scope and status")
    span = row.get("target_span")
    if not isinstance(span, dict):
        raise ValueError("candidate span needs offsets and verbatim text")
    quote = span.get("text", span.get("quote"))
    if not isinstance(quote, str) or not quote or quote not in message:
        raise ValueError("candidate span is not verbatim in message")
    start, end = span.get("start"), span.get("end")
    valid = (
        isinstance(start, int)
        and isinstance(end, int)
        and 0 <= start < end <= len(message)
        and message[start:end] == quote
    )
    if not valid:
        start = message.find(quote)
        if message.find(quote, start + 1) != -1:
            raise ValueError("ambiguous candidate span with invalid offsets")
        end = start + len(quote)
    previous = row.get("prev_user", row.get("previous_user"))
    if previous is not None and not isinstance(previous, str):
        raise ValueError("previous user context must be text or null")
    row.update(
        old_rule=rule,
        message=message,
        author=author_of(row),
        prev_user=previous,
        target_span={"start": start, "end": end, "text": quote},
        span_offsets_repaired=not valid,
        development_only=development_only(row),
        new_rule_spans=[
            s if isinstance(s, str) else s.get("text", s.get("quote"))
            for s in row.get("new_rule_spans", [])
        ],
    )
    return row


def fingerprint(row):
    return rule_text(row).strip().casefold(), message_text(row).strip().casefold()


def group_tokens(row):
    """Visible message and declared scenario/paraphrase relatives stay together."""
    tokens = [("message", message_text(row).strip().casefold())]
    for key in (
        "id",
        "scenario_id",
        "parent_id",
        "parent_scenario_id",
        "family_id",
        "declared_family_id",
        "paraphrase_group",
        "paraphrase_id",
    ):
        if row.get(key) is not None:
            tokens.append(("relative", str(row[key])))
    for key in ("sibling_ids", "parent_ids", "paraphrase_ids"):
        values = row.get(key) or []
        if not isinstance(values, list):
            raise ValueError(f"{key} must be a list")
        tokens.extend(("relative", str(value)) for value in values)
    return tokens


def group_rows(rows):
    parents = list(range(len(rows)))

    def find(i):
        while parents[i] != i:
            parents[i] = parents[parents[i]]
            i = parents[i]
        return i

    seen = {}
    for i, row in enumerate(rows):
        for token in group_tokens(row):
            if token in seen:
                parents[find(i)] = find(seen[token])
            seen[token] = i
    groups = defaultdict(list)
    for i, row in enumerate(rows):
        groups[find(i)].append(row)
    return list(groups.values())


def deduplicate(rows, *, reject_conflicts=False):
    # Assign connected components BEFORE dedup, retaining dropped relatives' links.
    for group in group_rows(rows):
        group_id = digest(
            sorted({token for row in group for token in group_tokens(row)})
        )
        for row in group:
            if "family_id" in row and "declared_family_id" not in row:
                row["declared_family_id"] = row["family_id"]
            row["family_id"] = group_id
        if any(row.get("development_only") for row in group):
            for row in group:
                row["development_only"] = True
    labels = defaultdict(set)
    for row in rows:
        labels[fingerprint(row)].add(row["label"])
    seen, result, decisions = {}, [], []
    for row in rows:
        key = fingerprint(row)
        if len(labels[key]) > 1:
            if reject_conflicts:
                raise ValueError(
                    "conflicting held-out labels require an independent audit"
                )
            decisions.append(
                {
                    "fingerprint_sha256": digest(key),
                    "dropped_source": row.get("source"),
                    "reason": "conflicting labels; exclude entire fingerprint",
                }
            )
            continue
        if key in seen:
            decisions.append(
                {
                    "fingerprint_sha256": digest(key),
                    "kept_source": seen[key].get("source"),
                    "dropped_source": row.get("source"),
                }
            )
        else:
            seen[key] = row
            result.append(row)
    return result, decisions


def load_training(paths, patch_paths, enrich_paths):
    raw, patches, hashes, summaries = [], [], {}, []
    for path in [*paths, *enrich_paths, *patch_paths]:
        rows, sha = read_jsonl(path)
        hashes[str(Path(path).resolve())] = sha
        if path in patch_paths:
            summaries.extend(row["summary"] for row in rows if set(row) == {"summary"})
            rows = [row for row in rows if set(row) != {"summary"}]
        for row in rows:
            refuse_benchmark(row)
        (patches if path in patch_paths else raw).extend(rows)
    # Reserved-author data cannot be laundered away by a patch or deduplication.
    if any(author_of(row) == "fable" for row in raw):
        raise ValueError("reserved held-out author cannot enter fit/development")
    fixed, audit = apply_patches(raw, patches)
    normalized = [normalize_row(row) for row in fixed]
    pairs = [row for row in normalized if row is not None]
    audit.update(
        admission_rows_excluded=len(normalized) - len(pairs),
        span_offsets_repaired=sum(r["span_offsets_repaired"] for r in pairs),
    )
    pairs, decisions = deduplicate(pairs)
    audit.update(
        input_sha256=hashes,
        dedup_decisions=decisions,
        pairs=len(pairs),
        review_summaries=summaries,
    )
    return pairs, audit


def split_development(rows, seed=9054301, fraction=0.1):
    groups = group_rows(rows)
    random.Random(seed).shuffle(groups)
    target = max(1, round(len(rows) * fraction))
    remaining = Counter(r["author"] for r in rows)
    target_labels = Counter(r["label"] for r in rows)
    dev = [r for g in groups if any(r.get("development_only") for r in g) for r in g]
    groups = [g for g in groups if not any(r.get("development_only") for r in g)]
    remaining.subtract(r["author"] for r in dev)
    dev_labels = Counter(r["label"] for r in dev)
    fit = []
    # Greedy label balancing, with seeded tie ordering and intact scenario groups.
    while groups:
        groups.sort(
            key=lambda g: (
                sum(
                    max(
                        0, fraction * target_labels[r["label"]] - dev_labels[r["label"]]
                    )
                    for r in g
                )
                / len(g)
            ),
            reverse=True,
        )
        group = groups.pop(0)
        authors = Counter(r["author"] for r in group)
        can_share = all(remaining[a] > n for a, n in authors.items())
        if (
            len(dev) < target
            and can_share
            and (
                not dev or abs(len(dev) + len(group) - target) <= abs(len(dev) - target)
            )
        ):
            dev.extend(group)
            remaining.subtract(authors)
            dev_labels.update(r["label"] for r in group)
        else:
            fit.extend(group)
    if not fit or not dev:
        raise ValueError("need multiple independent groups for fit/development")
    if not {r["author"] for r in dev} <= {r["author"] for r in fit}:
        raise ValueError("development authors need independent fit groups")
    return fit, dev


def render_pair(row):
    rule = row["old_rule"]
    a = f"[target] {rule['status']} {rule['scope']} {rule['text']}"
    # Only visible target-version metadata, never a hidden new-task label.
    metadata = {
        k: rule[k] for k in ("key", "version", "task_id") if rule.get(k) is not None
    }
    if metadata:
        a += " [metadata] " + json.dumps(metadata, sort_keys=True, ensure_ascii=False)
    b = f"[message] {row['role']}: {row['message']} [span] {row['target_span']['text']}"
    if row.get("prev_user"):
        b += f" [prev_user] {row['prev_user']}"
    return a, b


def encode_rows(rows, tokenizer, max_length=512):
    encoded, overflow = [], []
    for row in rows:
        a, b = render_pair(row)
        tokens = tokenizer(a, b, truncation=False, padding=False)
        too_long = len(tokens["input_ids"]) > max_length
        encoded.append(None if too_long else tokens)
        overflow.append(too_long)
    return encoded, np.asarray(overflow, dtype=bool)


def probabilities(logits):
    logits = np.asarray(logits, dtype=np.float64)
    if logits.ndim != 2 or logits.shape[1] != len(LABELS):
        raise ValueError("expected N x 5 logits")
    valid = np.isfinite(logits).all(axis=1)
    safe = np.where(valid[:, None], logits, 0)
    exps = np.exp(safe - safe.max(axis=1, keepdims=True))
    probs = exps / exps.sum(axis=1, keepdims=True)
    probs[~valid] = [1, 0, 0, 0, 0]
    return probs


def predict(logits, thresholds, overflow=None):
    probs = probabilities(logits)
    winners = probs.argmax(axis=1)
    result = np.zeros(len(probs), dtype=int)
    for k, label in enumerate(LABELS[1:], 1):
        threshold = thresholds.get(label, DISABLED_THRESHOLD)
        if not math.isfinite(threshold) or threshold < 0.98:
            raise ValueError("threshold must be finite and at least .98")
        result[(winners == k) & (probs[:, k] >= threshold)] = k
    if overflow is not None:
        result[np.asarray(overflow, dtype=bool)] = 0
    return result


def calibrate_thresholds(logits, labels, max_none_fp=0.02, floor=0.98, overflow=None):
    """Lowest supported threshold meeting the empirical per-class none-FP cap.

    Tied scores are excluded together using nextafter; >1 disables a class even
    for numerically saturated p=1. Missing none or positive support disables it.
    """
    if not 0.98 <= floor <= 1 or not 0 <= max_none_fp <= 0.02:
        raise ValueError("calibration may only tighten the registered constraints")
    if not np.isfinite(logits).all():
        raise ValueError("non-finite development logits")
    probs = probabilities(logits)
    labels = np.asarray(labels)
    if labels.shape != (len(probs),) or not np.isin(labels, range(5)).all():
        raise ValueError("invalid development labels")
    usable = np.ones(len(labels), dtype=bool) if overflow is None else ~overflow
    none = labels == 0
    allowance = math.floor(max_none_fp * int(none.sum()))
    result = {}
    for k, label in enumerate(LABELS[1:], 1):
        if not none.any() or not ((labels == k) & usable).any():
            result[label] = DISABLED_THRESHOLD
            continue
        scores = np.sort(probs[none & usable, k])[::-1]
        threshold = floor
        if len(scores) > allowance and scores[allowance] >= floor:
            threshold = float(np.nextafter(scores[allowance], np.inf))
        result[label] = threshold
    return result


def evaluate_predictions(rows, predictions):
    gold = np.array([LABEL_MAP[r["label"]] for r in rows], dtype=int)
    predictions = np.asarray(predictions)
    confusion = np.zeros((5, 5), dtype=int)
    np.add.at(confusion, (gold, predictions), 1)
    none = gold == 0

    def rate(numerator, denominator):
        return {
            "numerator": int(numerator),
            "denominator": int(denominator),
            "rate": float(numerator / denominator) if denominator else None,
        }

    per_class = {}
    for k, label in enumerate(LABELS):
        tp = int(confusion[k, k])
        predicted, support = int(confusion[:, k].sum()), int(confusion[k].sum())
        per_class[label] = {
            "precision": tp / predicted if predicted else None,
            "recall": tp / support if support else None,
            "support": support,
            "predicted": predicted,
            "none_fp": rate(((predictions == k) & none).sum(), none.sum())
            if k
            else None,
        }
    report = {
        "n": len(rows),
        "accuracy": float((gold == predictions).mean()) if len(rows) else None,
        "labels": list(LABELS),
        "confusion_gold_by_prediction": confusion.tolist(),
        "per_class": per_class,
        "none_fp": rate(((predictions != 0) & none).sum(), none.sum()),
        "coverage": rate((predictions != 0).sum(), len(rows)),
        "abstentions": int((predictions == 0).sum()),
    }
    return report


def evaluation_report(rows, predictions, overflow):
    report = evaluate_predictions(rows, predictions)
    hard = np.array([r.get("hard") is True and r["label"] == "none" for r in rows])
    report["hard_negatives"] = evaluate_predictions(
        [r for r, keep in zip(rows, hard, strict=True) if keep], predictions[hard]
    )
    report["overflow_abstentions"] = int(overflow.sum())
    report["per_scope"] = {}
    for scope in sorted({r["old_rule"]["scope"] for r in rows}):
        mask = np.array([r["old_rule"]["scope"] == scope for r in rows])
        report["per_scope"][scope] = evaluate_predictions(
            [r for r, keep in zip(rows, mask, strict=True) if keep], predictions[mask]
        )
    return report


def assert_heldout_disjoint(training, heldout):
    if not heldout or any(r["author"] != "fable" for r in heldout):
        raise ValueError("held-out pairs must use reserved author fable")
    if {r["author"] for r in training} & {r["author"] for r in heldout}:
        raise ValueError("held-out author overlap")
    fit_tokens = {t for r in training for t in group_tokens(r)}
    if fit_tokens & {t for r in heldout for t in group_tokens(r)}:
        raise ValueError("held-out message/scenario/relative overlap")
    if {fingerprint(r) for r in training} & {fingerprint(r) for r in heldout}:
        raise ValueError("held-out semantic fingerprint overlap")


def class_weights(rows):
    counts = np.bincount([LABEL_MAP[r["label"]] for r in rows], minlength=5)
    if (counts == 0).any():
        raise ValueError("training needs examples of every relation class")
    return (len(rows) / (len(LABELS) * counts)).tolist()


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    data = ROOT / "data" / "classifier"
    parser.add_argument(
        "--train",
        type=Path,
        nargs="+",
        default=[data / "relations" / "kimi-relations.jsonl"],
    )
    parser.add_argument(
        "--patch",
        type=Path,
        nargs="+",
        default=[
            data / "review" / f"relations-{author}-patch.jsonl"
            for author in ("astra", "opus")
        ],
    )
    parser.add_argument(
        "--enrich",
        type=Path,
        nargs="+",
        default=[
            data / "relations" / f"{author}-enrich.jsonl"
            for author in ("astra", "opus")
        ],
    )
    parser.add_argument(
        "--heldout",
        type=Path,
        default=data / "heldout" / "fable-relations-heldout.jsonl",
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--base-revision", default=BASE_REVISION)
    parser.add_argument("--device", choices=["cpu", "cuda"], default="cpu")
    parser.add_argument("--seed", type=int, default=9054301)
    parser.add_argument("--epochs", type=int, default=None)
    parser.add_argument("--lr", type=float, default=3e-5)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--cpu-threads", type=int, default=4)
    parser.add_argument("--cpu-smoke", action="store_true")
    parser.add_argument("--local-files-only", action="store_true")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dev-only", action="store_true")
    mode.add_argument("--evaluate-only", action="store_true")
    parser.add_argument("--max-cpu-minutes", type=float, default=90)
    args = parser.parse_args(argv)
    args.epochs = (
        args.epochs if args.epochs is not None else (1 if args.cpu_smoke else 3)
    )
    if args.cpu_smoke and (args.device != "cpu" or args.epochs != 1):
        parser.error("--cpu-smoke requires CPU and one epoch")
    if min(args.epochs, args.batch_size, args.cpu_threads) < 1 or args.lr <= 0:
        parser.error("epochs, batch size, threads and lr must be positive")
    if not 0 < args.max_cpu_minutes <= 90:
        parser.error("CPU budget must be in (0, 90] minutes")
    if not re.fullmatch(r"[0-9a-f]{40}", args.base_revision):
        parser.error("--base-revision must be an immutable base-BGE commit SHA")
    args.output = args.output or data / "model" / (
        "relations-cpu-smoke" if args.cpu_smoke else "relations"
    )
    return args


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def train(args):
    cpu_start, wall_start = time.process_time(), time.monotonic()
    # Import heavyweight libraries only when explicitly invoked, never on import.
    if args.device == "cuda":
        os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    import torch
    import transformers
    from safetensors.torch import save_file
    from transformers import AutoModel, AutoTokenizer

    if args.output.exists():
        raise ValueError(
            "output already exists; use a new directory to preserve freezes"
        )
    missing = [str(p) for p in [*args.patch, *args.enrich] if not p.is_file()]
    if missing and not args.cpu_smoke:
        raise ValueError(f"review/enrichment inputs missing: {missing}")
    if not args.cpu_smoke and not args.dev_only and not args.heldout.is_file():
        raise ValueError("held-out file missing; no fitting started")
    rows, receipt = load_training(
        args.train,
        [p for p in args.patch if p.is_file()],
        [p for p in args.enrich if p.is_file()],
    )
    all_training = rows
    if args.cpu_smoke:
        groups = group_rows(rows)
        random.Random(args.seed).shuffle(groups)
        rows = []
        for group in groups:
            if len(rows) + len(group) <= 200:
                rows.extend(group)
        if len(rows) != 200:
            raise ValueError("cannot form exactly 200 smoke rows with intact groups")
    fit, dev = split_development(rows, args.seed)
    random.seed(args.seed)
    np.random.seed(args.seed)
    torch.manual_seed(args.seed)
    torch.set_num_threads(args.cpu_threads)
    torch.use_deterministic_algorithms(True)
    tokenizer = AutoTokenizer.from_pretrained(
        BASE_MODEL, revision=args.base_revision, local_files_only=args.local_files_only
    )
    encoder = AutoModel.from_pretrained(
        BASE_MODEL, revision=args.base_revision, local_files_only=args.local_files_only
    )

    class RelationClassifier(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.encoder = encoder
            self.head = torch.nn.Sequential(
                torch.nn.Dropout(0.1),
                torch.nn.Linear(encoder.config.hidden_size + 4, 5),
            )

        def forward(self, tokens, roles):
            cls = self.encoder(**tokens).last_hidden_state[:, 0]
            return self.head(torch.cat([cls, roles], dim=1))

    model = RelationClassifier().to(args.device)
    fit_tokens, fit_overflow = encode_rows(fit, tokenizer)
    dev_tokens, dev_overflow = encode_rows(dev, tokenizer)
    eligible = [i for i, tokens in enumerate(fit_tokens) if tokens is not None]
    weights = class_weights([fit[i] for i in eligible])
    print(
        f"fit={len(fit)} dev={len(dev)} overflow_fit={int(fit_overflow.sum())} "
        f"device={args.device}",
        flush=True,
    )

    def batch(rows, tokens, indices):
        inputs = tokenizer.pad(
            [tokens[i] for i in indices], padding=True, return_tensors="pt"
        )
        inputs = {key: value.to(args.device) for key, value in inputs.items()}
        roles = torch.tensor(
            [[float(rows[i]["role"] == r) for r in ROLES] for i in indices],
            device=args.device,
        )
        return inputs, roles

    def infer(rows, tokens):
        model.eval()
        logits = np.zeros((len(rows), 5), dtype=np.float64)
        indices = [i for i, t in enumerate(tokens) if t is not None]
        with torch.inference_mode():
            for start in range(0, len(indices), args.batch_size):
                ii = indices[start : start + args.batch_size]
                logits[ii] = model(*batch(rows, tokens, ii)).cpu().numpy()
        return logits

    args.output.mkdir(parents=True)
    manifest = {
        "state": "fitting",
        "data_lineage": LINEAGE,
        "cpu_smoke": args.cpu_smoke,
        "missing_smoke_inputs": missing,
        "base_model": BASE_MODEL,
        "base_revision": args.base_revision,
        "recipe": {
            "seed": args.seed,
            "epochs": args.epochs,
            "lr": args.lr,
            "batch_size": args.batch_size,
            "optimizer": "AdamW",
            "weight_decay": 0.01,
            "warmup_fraction": 0.06,
            "gradient_clip": 1.0,
            "max_tokens": 512,
            "pooling": "CLS",
            "dropout": 0.1,
            "class_weights": weights,
            "device": args.device,
            "cpu_threads": args.cpu_threads,
        },
        "versions": {
            "torch": torch.__version__,
            "transformers": transformers.__version__,
        },
        "labels": LABEL_MAP,
        "roles": list(ROLES),
        "data_audit": receipt,
        "split": {
            name: {
                "n": len(part),
                "sha256": digest(part),
                "labels": dict(Counter(r["label"] for r in part)),
                "authors": sorted({r["author"] for r in part}),
                "families": sorted({r["family_id"] for r in part}),
            }
            for name, part in (("fit", fit), ("development", dev))
        },
        "overflow_fit": int(fit_overflow.sum()),
        "source_sha256": {
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (Path(__file__), ROOT / "data/classifier/LABELS-RELATIONS.md")
        },
        "heldout_evaluation_count": 0,
        "exclusion_coverage": "lexical markers only; no sealed corpus access",
    }
    if args.cpu_smoke:
        manifest["data_lineage"] = LINEAGE.split("evaluated-on=")[0] + (
            "evaluated-on=development only in CPU smoke; held-out never opened"
        )
    elif args.dev_only:
        manifest["data_lineage"] = LINEAGE.split("evaluated-on=")[0] + (
            "evaluated-on=development only; reserved held-out unopened"
        )
    write_json(args.output / "manifest.json", manifest)
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    steps = args.epochs * math.ceil(len(eligible) / args.batch_size)
    sched = torch.optim.lr_scheduler.LambdaLR(
        opt,
        lambda s: min(1.0, (s + 1) / (0.06 * steps)) * max(0.0, (steps - s) / steps),
    )
    weight_tensor = torch.tensor(weights, device=args.device, dtype=torch.float32)
    completed_steps, completed_epochs, stopped_for_budget = 0, 0, False
    fitting_limit = args.max_cpu_minutes * 60 * 0.80
    for epoch in range(args.epochs):
        model.train()
        random.shuffle(eligible)
        total = 0.0
        for start in range(0, len(eligible), args.batch_size):
            if time.process_time() - cpu_start >= fitting_limit:
                stopped_for_budget = True
                break
            ii = eligible[start : start + args.batch_size]
            targets = torch.tensor(
                [LABEL_MAP[fit[i]["label"]] for i in ii], device=args.device
            )
            loss = torch.nn.functional.cross_entropy(
                model(*batch(fit, fit_tokens, ii)), targets, weight=weight_tensor
            )
            if not torch.isfinite(loss):
                raise ValueError("non-finite training loss")
            opt.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(
                model.parameters(), 1.0, error_if_nonfinite=True
            )
            opt.step()
            sched.step()
            total += float(loss.detach()) * len(ii)
            completed_steps += 1
            if completed_steps % 25 == 0:
                print(
                    f"step={completed_steps}/{steps} cpu_minutes="
                    f"{(time.process_time() - cpu_start) / 60:.2f} "
                    f"wall_minutes={(time.monotonic() - wall_start) / 60:.2f}",
                    flush=True,
                )
        print(f"epoch={epoch + 1} loss={total / len(eligible):.6f}", flush=True)
        if stopped_for_budget:
            break
        completed_epochs += 1
    manifest["budget"] = {
        "max_cpu_minutes": args.max_cpu_minutes,
        "fitting_fraction": 0.80,
        "completed_steps": completed_steps,
        "planned_steps": steps,
        "completed_epochs": completed_epochs,
        "reduced_for_budget": stopped_for_budget,
        "policy": "Batch-boundary stop; 20% for calibration/save; no signals",
    }
    dev_logits = infer(dev, dev_tokens)
    thresholds = calibrate_thresholds(
        dev_logits,
        np.array([LABEL_MAP[r["label"]] for r in dev]),
        overflow=dev_overflow,
    )
    model.eval()
    model.cpu()
    model.encoder.save_pretrained(args.output / "encoder")
    tokenizer.save_pretrained(args.output / "encoder")
    save_file(model.head.state_dict(), str(args.output / "head.safetensors"))
    threshold_record = {
        "thresholds": thresholds,
        "default": "none",
        "floor": 0.98,
        "max_empirical_none_fp_per_class": 0.02,
        "calibration_split": "development",
        "disabled_above": 1.0,
        "interpretation": "empirical constraint, not a population bound",
    }
    write_json(args.output / "thresholds.json", threshold_record)
    metrics = {
        "development": evaluation_report(
            dev, predict(dev_logits, thresholds, dev_overflow), dev_overflow
        )
    }
    metrics["development_argmax"] = evaluation_report(
        dev,
        np.where(dev_overflow, 0, probabilities(dev_logits).argmax(axis=1)),
        dev_overflow,
    )
    manifest["artifact_sha256"] = {
        str(path.relative_to(args.output)): hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
        for path in sorted(args.output.rglob("*"))
        if path.is_file() and path.name != "manifest.json"
    }
    manifest["state"] = "checkpoint_and_thresholds_frozen"
    write_json(args.output / "manifest.json", manifest)
    # First held-out read happens only AFTER checkpoint and thresholds freeze.
    if not args.cpu_smoke and not args.dev_only:
        raw, sha = read_jsonl(args.heldout, evaluation=True)
        normalized = []
        for row in raw:
            refuse_benchmark(row)
            pair = normalize_row(row)
            if pair is not None:
                normalized.append(pair)
        assert_heldout_disjoint(all_training, normalized)
        heldout, decisions = deduplicate(normalized, reject_conflicts=True)
        manifest["heldout"] = {
            "path": str(args.heldout),
            "sha256": sha,
            "dedup_decisions": decisions,
            "admission_rows_excluded": len(raw) - len(normalized),
        }
        model.to(args.device)
        tokens, overflow = encode_rows(heldout, tokenizer)
        logits = infer(heldout, tokens)
        metrics["heldout"] = evaluation_report(
            heldout, predict(logits, thresholds, overflow), overflow
        )
    write_json(args.output / "metrics.json", metrics)
    manifest["artifact_sha256"]["metrics.json"] = hashlib.sha256(
        (args.output / "metrics.json").read_bytes()
    ).hexdigest()
    manifest["state"] = "cpu_smoke_complete" if args.cpu_smoke else "complete"
    if args.dev_only:
        manifest["state"] = "development_complete_frozen"
    manifest["budget"]["cpu_minutes"] = (time.process_time() - cpu_start) / 60
    manifest["budget"]["wall_minutes"] = (time.monotonic() - wall_start) / 60
    write_json(args.output / "manifest.json", manifest)
    print(
        json.dumps({"output": str(args.output), "state": manifest["state"]}), flush=True
    )


def evaluate_frozen(args):
    """One final CPU evaluation of a previously frozen development-only run."""
    if args.device != "cpu" or os.environ.get("CUDA_VISIBLE_DEVICES") != "":
        raise ValueError("final evaluation requires CPU and CUDA_VISIBLE_DEVICES=''")
    import torch
    from safetensors.torch import load_file
    from transformers import AutoModel, AutoTokenizer

    started = time.process_time()
    manifest = json.loads((args.output / "manifest.json").read_text())
    if (
        manifest["state"] != "development_complete_frozen"
        or manifest["heldout_evaluation_count"]
    ):
        raise ValueError("checkpoint is not eligible for its one final evaluation")
    if manifest["recipe"]["seed"] != 0:
        raise ValueError("only predesignated seed 0 may evaluate held-out")
    for name, expected in manifest["artifact_sha256"].items():
        if hashlib.sha256((args.output / name).read_bytes()).hexdigest() != expected:
            raise ValueError(f"frozen artifact changed: {name}")
    for name, expected in manifest["data_audit"]["input_sha256"].items():
        if hashlib.sha256(Path(name).read_bytes()).hexdigest() != expected:
            raise ValueError("frozen development input changed")
    for name, expected in manifest["source_sha256"].items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
            raise ValueError("frozen trainer/spec changed")
    training, _ = load_training(args.train, args.patch, args.enrich)
    torch.set_num_threads(args.cpu_threads)
    torch.use_deterministic_algorithms(True)
    tokenizer = AutoTokenizer.from_pretrained(
        args.output / "encoder", local_files_only=True
    )
    encoder = (
        AutoModel.from_pretrained(args.output / "encoder", local_files_only=True)
        .cpu()
        .eval()
    )
    head = torch.nn.Sequential(
        torch.nn.Dropout(0.1), torch.nn.Linear(encoder.config.hidden_size + 4, 5)
    )
    head.load_state_dict(load_file(str(args.output / "head.safetensors")))
    head.cpu().eval()
    thresholds = json.loads((args.output / "thresholds.json").read_text())["thresholds"]
    manifest["state"] = "heldout_evaluation_started"
    manifest["heldout_evaluation_count"] = 1
    write_json(args.output / "manifest.json", manifest)
    raw, sha = read_jsonl(args.heldout, evaluation=True)
    normalized = []
    for row in raw:
        refuse_benchmark(row)
        pair = normalize_row(row)
        if pair is not None:
            normalized.append(pair)
    assert_heldout_disjoint(training, normalized)
    heldout, decisions = deduplicate(normalized, reject_conflicts=True)
    tokens, overflow = encode_rows(heldout, tokenizer)
    logits = np.zeros((len(heldout), 5), dtype=np.float64)
    indices = [i for i, t in enumerate(tokens) if t is not None]
    with torch.inference_mode():
        for start in range(0, len(indices), args.batch_size):
            ii = indices[start : start + args.batch_size]
            inputs = tokenizer.pad(
                [tokens[i] for i in ii], padding=True, return_tensors="pt"
            )
            roles = torch.tensor(
                [[float(heldout[i]["role"] == r) for r in ROLES] for i in ii]
            )
            cls = encoder(**inputs).last_hidden_state[:, 0]
            logits[ii] = head(torch.cat([cls, roles], dim=1)).numpy()
    metrics = json.loads((args.output / "metrics.json").read_text())
    metrics["heldout"] = evaluation_report(
        heldout, predict(logits, thresholds, overflow), overflow
    )
    metrics["heldout_at_098"] = evaluation_report(
        heldout, predict(logits, dict.fromkeys(LABELS[1:], 0.98), overflow), overflow
    )
    metrics["heldout_argmax"] = evaluation_report(
        heldout, np.where(overflow, 0, probabilities(logits).argmax(axis=1)), overflow
    )
    metrics["new_rule_admission"] = {
        "implemented": False,
        "evaluated": False,
        "reason": "Pairwise head only; no admission head loaded, trained or evaluated.",
    }
    np.savez_compressed(
        args.output / "heldout_predictions.npz",
        logits=logits,
        gold=np.array([LABEL_MAP[r["label"]] for r in heldout]),
        overflow=overflow,
    )
    write_json(args.output / "metrics.json", metrics)
    manifest["heldout"] = {
        "path": str(args.heldout),
        "sha256": sha,
        "raw_rows": len(raw),
        "pairs": len(heldout),
        "dedup_decisions": decisions,
        "admission_rows_excluded": len(raw) - len(normalized),
        "authors": ["fable"],
    }
    manifest["data_lineage"] = (
        "fit-on = kimi+enrich after merged patch; calibrated-on = dev split "
        "(scenario-disjoint 10%, fit-author-shared); evaluated-on = fable held-out, "
        "author-disjoint, seed 0 once; no benchmark inputs/responses; "
        "admission not trained"
    )
    manifest["evaluation_cpu_minutes"] = (time.process_time() - started) / 60
    for name in ("metrics.json", "heldout_predictions.npz"):
        manifest["artifact_sha256"][name] = hashlib.sha256(
            (args.output / name).read_bytes()
        ).hexdigest()
    manifest["state"] = "complete"
    write_json(args.output / "manifest.json", manifest)
    print(
        json.dumps(
            {
                "heldout_accuracy": metrics["heldout"]["accuracy"],
                "none_fp": metrics["heldout"]["none_fp"],
                "state": "complete",
            }
        ),
        flush=True,
    )


def main():
    args = parse_args()
    if args.evaluate_only:
        evaluate_frozen(args)
    else:
        train(args)


if __name__ == "__main__":
    main()
