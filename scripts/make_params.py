"""Render the registered Phase 2 trainable-parameter audit."""

from __future__ import annotations

import argparse
from pathlib import Path

from stencil.model import StencilTransformer, build_matched_configs, count_params

ROOT = Path(__file__).parents[1]
OUTPUT = ROOT / "results/params.md"


def render() -> str:
    rows = []
    for variant, config in build_matched_configs().items():
        count = count_params(StencilTransformer(config))
        rows.append(f"| {variant} | {config.d_ff} | {count:,} |")
    return "\n".join(
        [
            "# Phase 2 parameter matching",
            "",
            "Trainable parameters only; frozen buffers are excluded and embeddings "
            "are included.",
            "Widths are the first multiples of 8 within 1% of the M1b count.",
            "",
            "| variant | d_ff | trainable parameters |",
            "|---|---:|---:|",
            *rows,
            "",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rendered = render()
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != rendered:
            raise SystemExit("results/params.md is stale; run scripts/make_params.py")
        return
    OUTPUT.write_text(rendered, encoding="utf-8")


if __name__ == "__main__":
    main()
