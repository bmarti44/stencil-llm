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
        required = {"cell", "variant", "seed", "n_sequences", "n_answers"}
        missing = required - row.keys()
        if missing:
            raise ValueError(f"evaluation is missing fields {sorted(missing)}: {path}")
        if row["n_sequences"] < 1 or row["n_answers"] < 1:
            raise ValueError(f"evaluation counters are vacuous: {path}")
        if row["cell"] != "task_d" and "accuracy" not in row:
            raise ValueError(f"evaluation is missing accuracy: {path}")
        if "accuracy" in row and not 0.0 <= row["accuracy"] <= 1.0:
            raise ValueError(f"evaluation accuracy is outside [0,1]: {path}")
        if row["cell"] == "task_d" and "splits" in row:
            if not isinstance(row["splits"], dict) or not row["splits"]:
                raise ValueError(f"Task D evaluation has no split rows: {path}")
            evaluations.extend(row["splits"].values())
        else:
            evaluations.append(row)
    return evaluations


def render_summary(evaluations: list[dict[str, Any]]) -> str:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    legacy = [row for row in evaluations if row["cell"] != "task_d"]
    for row in legacy:
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
    task_b = [row for row in legacy if str(row["cell"]).startswith("task_b/")]
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
    task_d = [row for row in evaluations if row["cell"] == "task_d"]
    if task_d:
        lines.extend(_render_task_d(task_d))
    if not evaluations:
        lines.extend(["", "No completed evaluations found."])
    return "\n".join(lines) + "\n"


def _render_task_d(rows: list[dict[str, Any]]) -> list[str]:
    lines = [
        "",
        "## Task D",
        "",
        "The tables below expose the registered decision-procedure inputs; the "
        "orchestrator applies the frozen procedure separately.",
        "",
        "### Adoption reliability",
        "",
        "| contender | seed | id-control validation | adoption |",
        "|---|---:|---:|---|",
    ]
    for row in sorted(rows, key=lambda item: (item["contender"], item["seed"])):
        if row.get("split") != "validation":
            continue
        accuracy = row["families"]["id-control"]["sequence_weighted_exact_match"][
            "accuracy"
        ]
        status = "PASS" if accuracy >= 0.95 else "FAIL"
        lines.append(
            f"| {row['contender']} | {row['seed']} | {100 * accuracy:.3f}% | {status} |"
        )

    lines.extend(
        [
            "",
            "### Cost axis",
            "",
            "| contender | seed | split | injected tokens / sequence | "
            "train wall (s) | eval wall (s) |",
            "|---|---:|---|---:|---:|---:|",
        ]
    )
    for row in sorted(
        rows, key=lambda item: (item["contender"], item["seed"], item["split"])
    ):
        overhead = row["families"]["id-control"]["injected_token_overhead"][
            "per_sequence"
        ]
        cost = row.get("cost", {})
        train_wall = cost.get("train_wall_seconds")
        eval_wall = cost.get("eval_wall_seconds")
        lines.append(
            f"| {row['contender']} | {row['seed']} | {row['split']} | {overhead} | "
            f"{_format_optional(train_wall)} | {_format_optional(eval_wall)} |"
        )

    for split in ("validation", "final"):
        for family in ("id-control", "drought", "burst"):
            selected = [row for row in rows if row.get("split") == split]
            if not selected:
                continue
            lines.extend(
                [
                    "",
                    f"### {family} {split} curves",
                    "",
                    "| contender | seed | distance bin | correct / total | accuracy |",
                    "|---|---:|---|---:|---:|",
                ]
            )
            for row in sorted(
                selected, key=lambda item: (item["contender"], item["seed"])
            ):
                for bucket in row["families"][family]["decision_axis_bins"]:
                    accuracy = bucket.get(
                        "comparison_accuracy",
                        bucket["accuracy"] if bucket["denominator"] >= 200 else None,
                    )
                    lines.append(
                        f"| {row['contender']} | {row['seed']} | {bucket['label']} | "
                        f"{bucket['numerator']} / {bucket['denominator']} | "
                        f"{_format_percent(accuracy)} |"
                    )
            lines.extend(
                [
                    "",
                    "| contender | seed | global updates | correct / total | "
                    "accuracy |",
                    "|---|---:|---:|---:|---:|",
                ]
            )
            for row in sorted(
                selected, key=lambda item: (item["contender"], item["seed"])
            ):
                for bucket in row["families"][family][
                    "accuracy_by_global_update_count"
                ]:
                    lines.append(
                        f"| {row['contender']} | {row['seed']} | {bucket['updates']} | "
                        f"{bucket['numerator']} / {bucket['denominator']} | "
                        f"{_format_percent(bucket['accuracy'])} |"
                    )

    lines.extend(
        [
            "",
            "### Decision-table inputs",
            "",
            "| contender | seed | split | family | overall | tail >512 | "
            "survival D | stale excess |",
            "|---|---:|---|---|---:|---:|---:|---:|",
        ]
    )
    for row in sorted(
        rows, key=lambda item: (item["contender"], item["seed"], item["split"])
    ):
        for family in ("drought", "burst"):
            metrics = row["families"][family]
            overall = _format_percent(
                metrics["sequence_weighted_exact_match"]["accuracy"]
            )
            survival = metrics["first_crossing_survival"]
            lines.append(
                f"| {row['contender']} | {row['seed']} | {row['split']} | {family} | "
                f"{overall} | "
                f"{_format_percent(metrics['tail_over_512']['accuracy'])} | "
                f"{survival if survival is not None else 'NA'} | "
                f"{_format_optional(metrics['stale_slot_preference']['excess'])} |"
            )
    return lines


def _format_percent(value: float | None) -> str:
    return "NA" if value is None else f"{100 * value:.3f}%"


def _format_optional(value: float | None) -> str:
    return "NA" if value is None else f"{value:.3f}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results-dir", type=Path, default=Path("results"))
    parser.add_argument("--output", type=Path, default=Path("results/summary.md"))
    parser.add_argument(
        "--taskd-output", type=Path, default=Path("results/taskd-report.md")
    )
    args = parser.parse_args()
    evaluations = _load_evaluations(args.results_dir)
    rendered = render_summary(evaluations)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")
    print(args.output)
    if any(row["cell"] == "task_d" for row in evaluations):
        args.taskd_output.parent.mkdir(parents=True, exist_ok=True)
        args.taskd_output.write_text(rendered, encoding="utf-8")
        print(args.taskd_output)


if __name__ == "__main__":
    main()
