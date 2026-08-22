"""Write small decoded examples from every Phase 1 task and placement."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from stencil.config import Config, load_config
from stencil.data import generate

ROOT = Path(__file__).parents[1]


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


def main() -> None:
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
    (ROOT / "results/data_samples.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
