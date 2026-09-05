"""DEV-only operating-point policy, frozen before GPU retraining or new tests."""

import math

import numpy as np

LABELS = ("none", "supersedes", "cancels", "completes", "reinstates")
RULE = {
    "version": "2026-09-05-dev-v1",
    "threshold_grid": [i / 100 for i in range(50, 99)],
    "margin_grid": [i / 100 for i in range(99)],
    "max_none_fp_per_positive_class": 0.05,
    "minimum_correct_positive_recall": 0.60,
    "selection": (
        "lowest feasible per-class thresholds; else lowest feasible single margin"
    ),
    "failure": (
        "retain per-class policy, mark usefulness gate failed; no further tuning"
    ),
    "prediction": "positive argmax passes >= cutoff; otherwise none; overflow abstains",
    "ties": "argmax first label in fixed label order; equal cutoff accepted",
    "seed_policy": (
        "recalibrate same rule on each original DEV split; always ship seed 0"
    ),
}


def inputs(logits, labels, overflow):
    logits = np.asarray(logits, dtype=np.float64)
    labels = np.asarray(labels)
    overflow = np.asarray(overflow, dtype=bool)
    if (
        logits.shape != (len(labels), 5)
        or overflow.shape != labels.shape
        or not np.isfinite(logits).all()
        or not np.isin(labels, range(5)).all()
    ):
        raise ValueError("invalid calibration arrays")
    exp = np.exp(logits - logits.max(axis=1, keepdims=True))
    return exp / exp.sum(axis=1, keepdims=True), labels, overflow


def predict(probs, policy, overflow):
    winners = probs.argmax(axis=1)
    if policy["kind"] == "per_class":
        cutoffs = np.array([1.01] + [policy["thresholds"][k] for k in LABELS[1:]])
        accepted = probs.max(axis=1) >= cutoffs[winners]
    elif policy["kind"] == "margin":
        ordered = np.sort(probs, axis=1)
        accepted = ordered[:, -1] - ordered[:, -2] >= policy["margin"]
    else:
        raise ValueError("unknown policy")
    return np.where(accepted & ~overflow, winners, 0)


def metrics(labels, predictions):
    none, positive = labels == 0, labels != 0
    emitted = predictions != 0
    correct_positive = positive & (predictions == labels)

    def rate(n, d):
        return float(n / d) if d else None

    per_class = {}
    for k, label in enumerate(LABELS[1:], 1):
        pred, gold = predictions == k, labels == k
        tp, count, support = int((pred & gold).sum()), int(pred.sum()), int(gold.sum())
        fp = int((pred & none).sum())
        per_class[label] = {
            "support": support,
            "predicted": count,
            "true_positive": tp,
            "precision": rate(tp, count),
            "recall": rate(tp, support),
            "coverage_all": rate(count, len(labels)),
            "none_fp_count": fp,
            "none_fp": rate(fp, int(none.sum())),
        }
    return {
        "n": len(labels),
        "none_support": int(none.sum()),
        "positive_support": int(positive.sum()),
        "predicted_positive": int(emitted.sum()),
        "correct_positive": int(correct_positive.sum()),
        "positive_precision": rate(int(correct_positive.sum()), int(emitted.sum())),
        "coverage_all": rate(int(emitted.sum()), len(labels)),
        "gold_positive_coverage": rate(
            int((emitted & positive).sum()), int(positive.sum())
        ),
        "correct_positive_recall": rate(
            int(correct_positive.sum()), int(positive.sum())
        ),
        "none_fp_count": int((emitted & none).sum()),
        "none_fp": rate(int((emitted & none).sum()), int(none.sum())),
        "accuracy": rate(int((predictions == labels).sum()), len(labels)),
        "per_class": per_class,
    }


def select(logits, labels, overflow):
    probs, labels, overflow = inputs(logits, labels, overflow)
    none_n = int((labels == 0).sum())
    if not none_n or not (labels != 0).any():
        raise ValueError("DEV needs both none and positive support")
    allowance = math.floor(RULE["max_none_fp_per_positive_class"] * none_n)
    thresholds = {}
    for k, label in enumerate(LABELS[1:], 1):
        thresholds[label] = 1.01  # explicit disable when no feasible point/support
        if not ((labels == k) & ~overflow).any():
            continue
        for t in RULE["threshold_grid"]:
            pred = predict(
                probs,
                {"kind": "per_class", "thresholds": dict.fromkeys(LABELS[1:], t)},
                overflow,
            )
            if int(((pred == k) & (labels == 0)).sum()) <= allowance:
                thresholds[label] = t
                break
    per_class = {"kind": "per_class", "thresholds": thresholds}
    chosen = per_class
    primary_metrics = metrics(labels, predict(probs, per_class, overflow))
    qualified = (
        primary_metrics["correct_positive_recall"]
        >= RULE["minimum_correct_positive_recall"]
    )
    if not qualified:
        for margin in RULE["margin_grid"]:
            candidate = {"kind": "margin", "margin": margin}
            result = metrics(labels, predict(probs, candidate, overflow))
            if (
                all(
                    c["none_fp_count"] <= allowance
                    for c in result["per_class"].values()
                )
                and result["correct_positive_recall"]
                >= RULE["minimum_correct_positive_recall"]
            ):
                chosen, qualified = candidate, True
                break
    return {
        "rule": RULE,
        "policy": chosen,
        "qualified_on_dev": qualified,
        "none_fp_allowance_per_class": allowance,
        "primary_policy": per_class,
        "primary_dev": primary_metrics,
        "dev": metrics(labels, predict(probs, chosen, overflow)),
    }
