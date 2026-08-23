#!/usr/bin/env python3
"""Aggregate completed per-seed evaluations into the Phase 3 summary table."""

from __future__ import annotations

import argparse
import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any


def _load_evaluations(results_dir: Path) -> list[dict[str, Any]]:
    evaluations: list[dict[str, Any]] = []
    for path in sorted(results_dir.glob("*/eval.json")):
        if not (path.parent / "DONE").is_file():
            continue
        try:
            row = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise ValueError(f"invalid evaluation JSON: {path}") from error
        required = {"cell", "variant", "seed", "n_sequences", "n_answers", "accuracy"}
        missing = required - row.keys()
        if missing:
            raise ValueError(f"evaluation is missing fields {sorted(missing)}: {path}")
        if row["n_sequences"] < 1 or row["n_answers"] < 1:
            raise ValueError(f"evaluation counters are vacuous: {path}")
        if not 0.0 <= row["accuracy"] <= 1.0:
            raise ValueError(f"evaluation accuracy is outside [0,1]: {path}")
        evaluations.append(row)
    return evaluations


def render_summary(evaluations: list[dict[str, Any]]) -> str:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in evaluations:
        grouped[(row["cell"], row["variant"])].append(row)
    lines = [
        "# Phase 3 summary",
        "",
        "Accuracy is pooled within each seed, then summarized across available seeds.",
        "",
        "| cell | variant | seeds | mean accuracy | min-seed accuracy |",
        "|---|---|---:|---:|---:|",
    ]
    for (cell, variant), rows in sorted(grouped.items()):
        seeds = [int(row["seed"]) for row in rows]
        if len(seeds) != len(set(seeds)):
            raise ValueError(f"duplicate seed rows for {cell}/{variant}")
        accuracies = [float(row["accuracy"]) for row in rows]
        lines.append(
            f"| {cell} | {variant} | {len(rows)} | "
            f"{100 * statistics.fmean(accuracies):.3f}% | "
            f"{100 * min(accuracies):.3f}% |"
        )
    task_b = [row for row in evaluations if str(row["cell"]).startswith("task_b/")]
    if task_b:
        lines.extend(
            [
                "",
                "## Task B stale-rule analytic null",
                "",
                "The null is the exact conditional probability that a uniformly random "
                "wrong answer matches at least one prior non-active rule output.",
                "",
                "| cell | variant | seed | analytic null |",
                "|---|---|---:|---:|",
            ]
        )
        def sort_key(item: dict[str, Any]) -> tuple[str, str, int]:
            return item["cell"], item["variant"], item["seed"]

        for row in sorted(task_b, key=sort_key):
            if "stale_rule_analytic_null" not in row:
                raise ValueError("Task B evaluation lacks stale-rule analytic null")
            lines.append(
                f"| {row['cell']} | {row['variant']} | {row['seed']} | "
                f"{100 * row['stale_rule_analytic_null']:.3f}% |"
            )
    if not evaluations:
        lines.extend(["", "No completed evaluations found."])
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", type=Path, default=Path("results"))
    parser.add_argument("--output", type=Path, default=Path("results/summary.md"))
    args = parser.parse_args()
    evaluations = _load_evaluations(args.results_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_summary(evaluations), encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
