"""Registered E2 audit ranges, paired tests, and cluster inference."""

from __future__ import annotations

import hashlib
import math
import random
from collections import Counter
from collections.abc import Mapping, Sequence


def mcnemar_one_sided(improvements: int, regressions: int) -> float:
    """Exact P[X >= improvements], X~Binomial(discordants, 0.5)."""
    if improvements < 0 or regressions < 0:
        raise ValueError("discordant counts must be nonnegative")
    total = improvements + regressions
    if total == 0:
        return 1.0
    return min(
        1.0,
        sum(math.comb(total, k) for k in range(improvements, total + 1))
        / (2**total),
    )


def periodic_assignment(key: str, turn: int, *, rate: float, onset: int) -> int | None:
    """Stable conflict-free periodic-arm admission at a frozen expected rate."""
    if not 0.0 <= rate <= 1.0 or onset < 0:
        raise ValueError("invalid periodic schedule")
    digest = hashlib.sha256(f"e2-periodic:{key}:{turn}".encode()).digest()
    uniform = int.from_bytes(digest[:8], "big") / 2**64
    return int(onset) if uniform < rate else None


def summarize_policy_audit(records: Sequence[Mapping]) -> dict:
    if not records:
        raise ValueError("nonempty audit records required")
    by_turn = {}
    origin_counts = Counter()
    aged = 0
    fired_total = 0
    onset_violations = 0
    silent_mismatches = 0
    for turn in sorted({int(r["turn"]) for r in records}):
        rows = [r for r in records if int(r["turn"]) == turn]
        fired = sum(bool(r["fired"]) for r in rows)
        by_turn[str(turn)] = {
            "n": len(rows),
            "fired": fired,
            "fire_rate": fired / len(rows),
        }
        for row in rows:
            is_fired = bool(row["fired"])
            onset_count = int(row["onset_count"])
            if onset_count != int(is_fired):
                onset_violations += 1
            if not is_fired and not bool(row["silent_identical"]):
                silent_mismatches += 1
            if is_fired:
                origin = int(row["selected_origin"])
                origin_counts[origin] += 1
                aged += int(origin < turn)
                fired_total += 1
    max_origin_share = (
        max(origin_counts.values(), default=0) / fired_total if fired_total else 0.0
    )
    return {
        "n": len(records),
        "by_turn": by_turn,
        "fired": fired_total,
        "onset_violations": onset_violations,
        "silent_mismatches": silent_mismatches,
        "selected_origin_counts": {
            str(key): value for key, value in sorted(origin_counts.items())
        },
        "aged_selected_fraction": aged / fired_total if fired_total else 0.0,
        "max_origin_share": max_origin_share,
    }


def audit_reasons(summary: Mapping) -> list[str]:
    reasons = []
    for turn in (2, 3):
        row = summary.get("by_turn", {}).get(str(turn))
        if row is None:
            reasons.append(f"turn {turn}: audit rows missing")
            continue
        rate = float(row["fire_rate"])
        if not 0.10 <= rate <= 0.60:
            reasons.append(f"turn {turn}: firing rate {rate:.4f} outside [0.10,0.60]")
    if int(summary.get("onset_violations", 0)):
        reasons.append(f"onset count violations: {summary['onset_violations']}")
    if int(summary.get("silent_mismatches", 0)):
        reasons.append(f"silent identity mismatches: {summary['silent_mismatches']}")
    aged = float(summary.get("aged_selected_fraction", 0.0))
    if not 0.20 <= aged <= 0.80:
        reasons.append(f"aged selected fraction {aged:.4f} outside [0.20,0.80]")
    share = float(summary.get("max_origin_share", 0.0))
    if share > 0.80:
        reasons.append(f"single origin share {share:.4f} > 0.80")
    return reasons


def safe_dose_reasons(summary: Mapping[str, Mapping]) -> list[str]:
    reasons = []
    required = ("2.25", "3.0", "3.75")
    decision_hashes = set()
    for dose in required:
        row = summary.get(dose)
        if row is None:
            reasons.append(f"dose {dose}: result missing")
            continue
        decision_hashes.add(str(row["decision_hash"]))
        if int(row["net_utility"]) <= 0:
            reasons.append(f"dose {dose}: net utility is not positive")
        if float(row["harm_p_one_sided"]) <= 0.05:
            reasons.append(f"dose {dose}: significant regression excess")
        if int(row["arm_truncations"]) > int(row["native_truncations"]):
            reasons.append(f"dose {dose}: excess truncations")
        if int(row["arm_timeouts"]) > int(row["native_timeouts"]):
            reasons.append(f"dose {dose}: excess timeouts")
    if len(decision_hashes) > 1:
        reasons.append("safe-dose firing decisions are not identical")
    return reasons


def _quantile(sorted_values: Sequence[float], probability: float) -> float:
    if not sorted_values:
        raise ValueError("values required")
    position = probability * (len(sorted_values) - 1)
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return float(sorted_values[lower])
    weight = position - lower
    return float(sorted_values[lower] * (1 - weight) + sorted_values[upper] * weight)


def cluster_bootstrap_delta(
    rows: Sequence[Mapping], *, draws: int = 10_000, seed: int = 0
) -> dict:
    """Resample whole conversations and compute arm-minus-base cell rate."""
    if not rows or draws <= 0:
        raise ValueError("nonempty rows and positive draws required")
    clusters = sorted({int(row["conversation"]) for row in rows})
    grouped = {
        cluster: [row for row in rows if int(row["conversation"]) == cluster]
        for cluster in clusters
    }

    def delta(sampled):
        numerator = 0
        denominator = 0
        for cluster in sampled:
            for row in grouped[cluster]:
                base = [int(bool(x)) for x in row["base"]]
                arm = [int(bool(x)) for x in row["arm"]]
                if len(base) != len(arm):
                    raise ValueError("paired cell width changed")
                numerator += sum(arm) - sum(base)
                denominator += len(base)
        if denominator == 0:
            raise ValueError("cluster sample has no cells")
        return numerator / denominator

    point = delta(clusters)
    rng = random.Random(seed)
    samples = sorted(
        delta([rng.choice(clusters) for _ in clusters]) for _ in range(draws)
    )
    return {
        "clusters": len(clusters),
        "draws": draws,
        "seed": seed,
        "point_delta": point,
        "ci95": [_quantile(samples, 0.025), _quantile(samples, 0.975)],
    }
