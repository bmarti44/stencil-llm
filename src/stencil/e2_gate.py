"""Deterministic grouped hazard fitting and registered E2 discrimination."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

Z95 = 1.959963984540054


def wilson_lower(successes: int, trials: int, z: float = Z95) -> float:
    if trials <= 0:
        return 0.0
    if not 0 <= successes <= trials:
        raise ValueError("successes must be in [0,trials]")
    p = successes / trials
    z2 = z * z
    center = p + z2 / (2 * trials)
    radius = z * math.sqrt(p * (1 - p) / trials + z2 / (4 * trials * trials))
    return max(0.0, (center - radius) / (1 + z2 / trials))


@dataclass(frozen=True)
class LogisticProbe:
    mean: tuple[float, ...]
    scale: tuple[float, ...]
    weights: tuple[float, ...]
    bias: float

    @classmethod
    def fit(
        cls,
        features: Sequence[Sequence[float]],
        labels: Sequence[int],
        *,
        l2: float = 1.0,
        iters: int = 500,
        lr: float = 0.1,
    ) -> LogisticProbe:
        if not features or len(features) != len(labels):
            raise ValueError("nonempty aligned features/labels required")
        width = len(features[0])
        if width <= 0 or any(len(x) != width for x in features):
            raise ValueError("fixed positive feature width required")
        if any(y not in (0, 1) for y in labels):
            raise ValueError("binary labels required")
        n = len(features)
        mean = tuple(sum(float(x[j]) for x in features) / n for j in range(width))
        scale = tuple(
            math.sqrt(sum((float(x[j]) - mean[j]) ** 2 for x in features) / n)
            or 1.0
            for j in range(width)
        )
        standardized = [
            tuple((float(x[j]) - mean[j]) / scale[j] for j in range(width))
            for x in features
        ]
        weights = [0.0] * width
        bias = 0.0
        for _ in range(iters):
            grad_w = [l2 * w / n for w in weights]
            grad_b = 0.0
            for x, y in zip(standardized, labels, strict=True):
                z = sum(w * v for w, v in zip(weights, x, strict=True)) + bias
                probability = 1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, z))))
                error = probability - y
                for j in range(width):
                    grad_w[j] += error * x[j] / n
                grad_b += error / n
            weights = [w - lr * g for w, g in zip(weights, grad_w, strict=True)]
            bias -= lr * grad_b
        return cls(mean, scale, tuple(weights), bias)

    def probability(self, features: Sequence[float]) -> float:
        if len(features) != len(self.weights):
            raise ValueError("feature width mismatch")
        z = self.bias + sum(
            w * (float(x) - m) / s
            for w, x, m, s in zip(
                self.weights, features, self.mean, self.scale, strict=True
            )
        )
        return 1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, z))))


def _binary_labels(records: Sequence[Mapping]) -> list[int]:
    return [int(r["label"] == "helpful") for r in records]


def _utility(records: Sequence[Mapping]) -> list[int]:
    return [int(r["utility_delta"]) for r in records]


def select_threshold(
    probabilities: Sequence[float], labels: Sequence[int], utility: Sequence[int]
) -> float:
    """Choose a train-only threshold; never consult held-out observations."""
    if not probabilities or not (len(probabilities) == len(labels) == len(utility)):
        raise ValueError("aligned nonempty threshold data required")
    candidates = sorted(set(float(p) for p in probabilities), reverse=True)
    best = None
    for threshold in candidates:
        fired = [p >= threshold for p in probabilities]
        n_fired = sum(fired)
        true_positive = sum(f and y for f, y in zip(fired, labels, strict=True))
        total_positive = sum(labels)
        ppv = true_positive / n_fired if n_fired else 0.0
        recall = true_positive / total_positive if total_positive else 0.0
        net = sum(u for u, f in zip(utility, fired, strict=True) if f)
        f1 = 2 * ppv * recall / (ppv + recall) if ppv + recall else 0.0
        qualifies = ppv >= 0.70 and recall >= 0.50
        key = (int(qualifies), net if qualifies else f1, recall, ppv, threshold)
        if best is None or key > best[0]:
            best = (key, threshold)
    assert best is not None
    return best[1]


def _features(record: Mapping, kind: str) -> list[float]:
    values = [float(x) for x in record["features"]]
    if len(values) != 6:
        raise ValueError("registered hazard feature width changed")
    if kind == "full":
        return values
    indices = {
        "entropy": 1,
        "margin": 2,
        "attention": 3,
    }
    if kind in indices:
        return [values[indices[kind]]]
    if kind == "position":
        return [float(record["response_position"])]
    raise ValueError(f"unknown feature kind {kind}")


def _group(record: Mapping, scheme: str):
    if scheme == "session":
        return int(record["session"]) % 5
    if scheme == "topic":
        return str(record["topic"])
    if scheme == "family":
        return tuple(sorted(str(x) for x in record["changed_family"]))
    raise ValueError(f"unknown holdout scheme {scheme}")


def decision_metrics(records: Sequence[Mapping], decisions: Sequence[bool]) -> dict:
    if len(records) != len(decisions):
        raise ValueError("decision width mismatch")
    labels = _binary_labels(records)
    utilities = _utility(records)
    n_fired = sum(bool(x) for x in decisions)
    true_positive = sum(
        bool(f) and y for f, y in zip(decisions, labels, strict=True)
    )
    n_helpful = sum(labels)
    ppv = true_positive / n_fired if n_fired else 0.0
    recall = true_positive / n_helpful if n_helpful else 0.0
    family_utility: dict[str, int] = {}
    for rec, fired, value in zip(records, decisions, utilities, strict=True):
        if fired:
            key = "+".join(sorted(str(x) for x in rec["changed_family"]))
            family_utility[key] = family_utility.get(key, 0) + value
    return {
        "n": len(records),
        "n_helpful": n_helpful,
        "n_fired": n_fired,
        "fire_rate": n_fired / len(records) if records else 0.0,
        "true_positive": true_positive,
        "ppv": ppv,
        "ppv_lcb95": wilson_lower(true_positive, n_fired),
        "recall": recall,
        "recall_lcb95": wilson_lower(true_positive, n_helpful),
        "net_utility": sum(
            value for value, fired in zip(utilities, decisions, strict=True) if fired
        ),
        "harmful_fires": sum(
            fired and value < 0
            for value, fired in zip(utilities, decisions, strict=True)
        ),
        "family_utility": dict(sorted(family_utility.items())),
        "negative_utility_families": sorted(
            key for key, value in family_utility.items() if value < 0
        ),
    }


def cross_validate(records: Sequence[Mapping], scheme: str, feature_kind: str) -> dict:
    if not records:
        raise ValueError("records required")
    groups = [_group(record, scheme) for record in records]
    unique_groups = sorted(set(groups), key=repr)
    if len(unique_groups) < 2:
        raise ValueError(f"{scheme} needs at least two held-out groups")
    labels = _binary_labels(records)
    utility = _utility(records)
    probabilities = [0.0] * len(records)
    decisions = [False] * len(records)
    folds = []
    for heldout in unique_groups:
        train = [i for i, group in enumerate(groups) if group != heldout]
        test = [i for i, group in enumerate(groups) if group == heldout]
        probe = LogisticProbe.fit(
            [_features(records[i], feature_kind) for i in train],
            [labels[i] for i in train],
        )
        train_prob = [
            probe.probability(_features(records[i], feature_kind)) for i in train
        ]
        threshold = select_threshold(
            train_prob,
            [labels[i] for i in train],
            [utility[i] for i in train],
        )
        for i in test:
            probabilities[i] = probe.probability(_features(records[i], feature_kind))
            decisions[i] = probabilities[i] >= threshold
        train_groups = {groups[i] for i in train}
        test_groups = {groups[i] for i in test}
        folds.append(
            {
                "heldout": repr(heldout),
                "n_train": len(train),
                "n_test": len(test),
                "threshold": threshold,
                "train_groups_disjoint": train_groups.isdisjoint(test_groups),
            }
        )
    return {
        "scheme": scheme,
        "feature_kind": feature_kind,
        "probabilities": probabilities,
        "decisions": decisions,
        "metrics": decision_metrics(records, decisions),
        "folds": folds,
    }


def _matched_decisions(scores: Sequence[float], n_fired: int) -> list[bool]:
    if not 0 <= n_fired <= len(scores):
        raise ValueError("invalid matched firing count")
    order = sorted(range(len(scores)), key=lambda i: (-float(scores[i]), i))
    selected = set(order[:n_fired])
    return [i in selected for i in range(len(scores))]


def evaluate_discrimination(records: Sequence[Mapping]) -> dict:
    result = {"schemes": {}}
    for scheme in ("session", "topic", "family"):
        full = cross_validate(records, scheme, "full")
        n_fired = full["metrics"]["n_fired"]
        controls = {}
        for kind in ("entropy", "margin", "attention", "position"):
            cv = cross_validate(records, scheme, kind)
            matched = _matched_decisions(cv["probabilities"], n_fired)
            controls[kind] = {
                "metrics": decision_metrics(records, matched),
                "probabilities": cv["probabilities"],
            }
        # A fixed periodic score has peaks at quarter-response intervals and
        # uses no conflict or outcome feature.
        periodic_scores = [
            -min(abs(float(r["response_position"]) - p) for p in (0.25, 0.5, 0.75))
            for r in records
        ]
        periodic = _matched_decisions(periodic_scores, n_fired)
        controls["periodic"] = {
            "metrics": decision_metrics(records, periodic),
            "probabilities": periodic_scores,
        }
        result["schemes"][scheme] = {"full": full, "controls": controls}
    return result


def certification_reasons(
    label_counts: Mapping[str, int], discrimination: Mapping
) -> list[str]:
    """Return every registered offline-gate failure; empty means pass."""
    reasons = []
    for label in ("helpful", "harmful"):
        count = int(label_counts.get(label, 0))
        if count < 100:
            reasons.append(f"{label} count {count} < registered 100")
    if reasons and not discrimination.get("schemes"):
        return reasons
    for scheme in ("session", "topic", "family"):
        bundle = discrimination.get("schemes", {}).get(scheme)
        if bundle is None:
            reasons.append(f"{scheme}: held-out result missing")
            continue
        full = bundle["full"]["metrics"]
        attention = bundle["controls"]["attention"]["metrics"]
        position = bundle["controls"]["position"]["metrics"]
        if full["ppv_lcb95"] < 0.70:
            reasons.append(f"{scheme}: PPV LCB {full['ppv_lcb95']:.4f} < 0.70")
        if full["recall_lcb95"] < 0.50:
            reasons.append(f"{scheme}: recall LCB {full['recall_lcb95']:.4f} < 0.50")
        required_utility = 2 * max(0, int(attention["net_utility"]))
        if full["net_utility"] <= 0 or full["net_utility"] < required_utility:
            reasons.append(
                f"{scheme}: net utility {full['net_utility']} "
                f"< 2x psi {required_utility}"
            )
        if full["negative_utility_families"]:
            reasons.append(
                f"{scheme}: negative utility families "
                + ",".join(full["negative_utility_families"])
            )
        if (
            position["ppv"] >= full["ppv"]
            and position["recall"] >= full["recall"]
            and position["net_utility"] >= full["net_utility"]
        ):
            reasons.append(
                f"{scheme}: response-position control explains discrimination"
            )
    return reasons
