"""Write small decoded examples from every Phase 1 task and placement."""

from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path

from stencil.config import Config, load_config
from stencil.data import generate

ROOT = Path(__file__).parents[1]
SECTION_TITLES = (
    "Task A — cued rule application (N=8 miniature)",
    "Task B — switching (R=3 miniature)",
    "Task M — in-window (P=4, queries=2 miniature)",
    "Task M — beyond-window (P=4, queries=2 miniature)",
)


def task_config(task: str, **overrides: object) -> Config:
    base = load_config(ROOT / "configs" / "test_tiny.json")
    task_fields: dict[str, object] = {
        "task_N": None,
        "task_k": None,
        "task_R": None,
        "task_delay_min": None,
        "task_delay_max": None,
        "task_P": None,
        "task_queries": None,
        "task_placement": None,
    }
    task_fields.update(overrides)
    return replace(base, task=task, **task_fields)


def decode(token: int, task: str) -> str:
    if token == 0:
        return "PAD"
    if 1 <= token <= 32:
        prefix = "key" if task == "m" else "cue"
        return f"{prefix}[{token - 1}]"
    if token == 33:
        return "QRY"
    if 34 <= token <= 49:
        return f"symbol[{token - 34}]"
    return f"distractor[{token - 50}]"


def render_section(title: str, config: Config) -> list[str]:
    lines = [f"## {title}", ""]
    stream = generate(config)
    for sample_index in range(1, 4):
        tokens, loss_mask, metadata = next(stream)
        marked = []
        for position, token in enumerate(tokens.tolist()):
            label = decode(token, config.task)
            if loss_mask[position]:
                label += " -> ANSWER"
            marked.append(label)
        lines.extend(
            [
                f"### Sample {sample_index}",
                "",
                "`" + " | ".join(marked) + "`",
                "",
                f"Metadata: `{metadata}`",
                "",
            ]
        )
    return lines


def render_document() -> str:
    """Render the complete deterministic G1 sample artifact."""
    sections = [
        (
            "Task A — cued rule application (N=8 miniature)",
            task_config("a", task_N=8, task_k=2),
        ),
        (
            "Task B — switching (R=3 miniature)",
            task_config(
                "b",
                task_k=8,
                task_R=3,
                task_delay_min=4,
                task_delay_max=8,
            ),
        ),
        (
            "Task M — in-window (P=4, queries=2 miniature)",
            task_config(
                "m", task_P=4, task_queries=2, task_placement="in_window"
            ),
        ),
        (
            "Task M — beyond-window (P=4, queries=2 miniature)",
            task_config(
                "m", task_P=4, task_queries=2, task_placement="beyond_window"
            ),
        ),
    ]
    lines = [
        "# Phase 1 decoded data samples",
        "",
        "`-> ANSWER` marks an input position whose logits predict the next token.",
        "",
    ]
    for title, config in sections:
        lines.extend(render_section(title, config))
    return "\n".join(lines)


def validate_document(content: str) -> None:
    """Require exactly three samples in each registered artifact section."""
    headings = [
        line.removeprefix("## ")
        for line in content.splitlines()
        if line.startswith("## ")
    ]
    if headings != list(SECTION_TITLES):
        raise ValueError(f"expected sections {list(SECTION_TITLES)}, found {headings}")
    for index, title in enumerate(SECTION_TITLES):
        start = content.index(f"## {title}")
        stop = (
            content.index(f"## {SECTION_TITLES[index + 1]}")
            if index + 1 < len(SECTION_TITLES)
            else len(content)
        )
        sample_headings = [
            line
            for line in content[start:stop].splitlines()
            if line.startswith("### Sample ")
        ]
        if sample_headings != ["### Sample 1", "### Sample 2", "### Sample 3"]:
            raise ValueError(f"section {title!r} does not contain exactly 3 samples")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    output_path = ROOT / "results/data_samples.md"
    rendered = render_document()
    validate_document(rendered)
    if args.check:
        current = (
            output_path.read_text(encoding="utf-8")
            if output_path.exists()
            else None
        )
        if current != rendered:
            raise SystemExit(f"{output_path.relative_to(ROOT)} is stale; regenerate it")
        return
    output_path.write_text(rendered, encoding="utf-8")


if __name__ == "__main__":
    main()
