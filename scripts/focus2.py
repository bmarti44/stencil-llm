#!/usr/bin/env python3
"""FOCUS-2 v2 CLI. Import/help/prepare/analyze never construct a trunk."""

import argparse
import json
import time
from pathlib import Path

from stencil import focus2


def main(
    argv=None, *, backend_factory=None, tokenizer_factory=None, clock=time.monotonic
):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("competence", "pilot", "run", "analyze"))
    parser.add_argument(
        "--prepare-freeze",
        type=Path,
        metavar="DIRECTORY",
        help="CPU-only candidate content; cannot register a draft",
    )
    parser.add_argument("--freeze", type=Path)
    parser.add_argument("--launch-receipt", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--development-manifest", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.prepare_freeze:
            focus2.require(not args.mode, "prepare and execution modes are exclusive")
            development = (
                focus2.parse_json(args.development_manifest.read_text())
                if args.development_manifest
                else None
            )
            result = focus2.prepare_freeze(args.prepare_freeze, development=development)
        else:
            focus2.require(
                args.mode and args.freeze and args.output,
                "mode, freeze and output are required",
            )
            if args.mode == "analyze":
                result = focus2.analyze(
                    args.freeze,
                    args.launch_receipt,
                    args.output,
                    tokenizer_factory=tokenizer_factory,
                )
            else:
                result = focus2.execute_stage(
                    args.freeze,
                    args.launch_receipt,
                    args.output,
                    args.mode,
                    backend_factory=backend_factory,
                    tokenizer_factory=tokenizer_factory,
                    clock=clock,
                )
        print(json.dumps(result, ensure_ascii=False, allow_nan=False, sort_keys=True))
        return (
            0
            if result["status"]
            in (
                "DRAFT",
                "COMPLETE",
                "PASS",
                "FAIL",
                "FAIL-SAFETY",
                "PASS with MARGINAL ADDED CONTROL",
            )
            else 1
        )
    except (
        focus2.Invalid,
        focus2.Incomplete,
        OSError,
        KeyError,
        TypeError,
        ValueError,
    ) as exc:
        print(
            json.dumps(
                {"status": getattr(exc, "status", "INVALID"), "reason": str(exc)}
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
