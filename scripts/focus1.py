#!/usr/bin/env python3
"""FOCUS-1 v2 draft harness. All real model stages require registration/evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from stencil import focus1 as f  # noqa: E402


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest="mode", required=True)
    for mode in ("setup", "extract", "select", "run", "analyze"):
        sub = modes.add_parser(mode)
        sub.add_argument("--out", default=str(f.EXPERIMENT_ROOT))
        if mode != "analyze":
            sub.add_argument("--registered-manifest")
            sub.add_argument("--bfcl-completion")
        if mode == "setup":
            flags = sub.add_mutually_exclusive_group()
            flags.add_argument("--generate-only", action="store_true")
            flags.add_argument("--timing-smoke", action="store_true")
    return parser.parse_args(argv)


def main(argv=None, *, backend_factory=None, tokenizer_factory=None, clock=None):
    args = parse_args(argv)
    try:
        f.require(
            Path(args.out).resolve() == f.EXPERIMENT_ROOT.resolve(),
            "external experiment root",
        )
        f.require(not Path(args.out).is_symlink(), "experiment root symlink")
        store = f.Store(args.out)
        if args.mode == "analyze":
            result = f.analyze(store)
        elif args.mode == "setup" and args.generate_only:
            result = f.generate_only(
                store, tokenizer=tokenizer_factory() if tokenizer_factory else None
            )
        else:
            stage = (
                ("timing" if args.timing_smoke else "competence")
                if args.mode == "setup"
                else args.mode
            )
            result = f.execute_stage(
                store,
                stage,
                args.registered_manifest,
                args.bfcl_completion,
                backend_factory=backend_factory,
                tokenizer_factory=tokenizer_factory,
                **({"clock": clock} if clock is not None else {}),
            )
        if result["state"] == "READY":
            result = dict(
                result,
                state="INCOMPLETE",
                stage_state="READY",
                reasons=["stage complete; scientific test endpoints remain pending"],
            )
    except f.Incomplete as exc:
        result = dict(state="INCOMPLETE", reasons=[str(exc)])
    except (f.Invalid, KeyError, ValueError, OSError, TypeError) as exc:
        result = dict(state="INVALID", reasons=[str(exc)])
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return result


if __name__ == "__main__":
    main()
