"""Exp 0 timing and memory pilot: seconds/item, tok/s and peak memory at MAX context.

Every GPU registration in plan/BACK-ON-TRACK-PLAN.md takes its budget from this
pilot, never from an estimate. Families:
  multiif     the 4 longest echo contexts among the Exp 1 selection, one 512-token
              greedy generation each through scripts/multiif_evict.run_arm (keep=[]).
  memorycode  the 4 longest SETUP history prompts of results/memorycode-derived/
              items.json, one 512-token greedy generation each through
              scripts/memorycode_screen.generate (the history arm, no reminder).
Writes results/timing-pilot/<family>.json with per-item rows, the co-resident GPU
pids at start, and the aggregate used by the registration (max seconds/item ×1.5).
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
OUT = ROOT / "results" / "timing-pilot"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def gpu_pids() -> list[int]:
    result = subprocess.run(
        ["nvidia-smi", "--query-compute-apps=pid,used_memory", "--format=csv,noheader"],
        capture_output=True,
        text=True,
        check=False,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def family_multiif(args) -> dict:
    import torch

    echo = _load("multiif_echo_only")
    evict = echo._evict()
    records = echo.load_records()
    selected = echo.load_selection()
    longest = sorted(
        selected,
        key=lambda s: len(records[s["ci"]]["echo_context_token_ids"]),
        reverse=True,
    )[: args.items]
    tokenizer, model = echo.load_model()
    rows = []
    for item in longest:
        record = records[item["ci"]]
        ids = record["echo_context_token_ids"]
        torch.cuda.reset_peak_memory_stats()
        torch.cuda.synchronize()
        started = time.monotonic()
        generated = evict.run_arm(
            model,
            tokenizer,
            ids,
            evict_range=tuple(record["evict_range"]),
            keep=[],
            max_new=args.max_new,
            deadline=args.deadline,
        )
        torch.cuda.synchronize()
        seconds = time.monotonic() - started
        rows.append(
            {
                "ci": item["ci"],
                "context_tokens": len(ids),
                "generated_tokens": generated["n_generated"],
                "seconds": seconds,
                "tok_per_s": generated["n_generated"] / seconds if seconds else None,
                "peak_allocated_gb": torch.cuda.max_memory_allocated() / 2**30,
                "peak_reserved_gb": torch.cuda.max_memory_reserved() / 2**30,
            }
        )
        print(json.dumps(rows[-1]), flush=True)
    return {"rows": rows}


def family_memorycode(args) -> dict:
    import torch

    from stencil import memorycode as mc

    screen = _load("memorycode_screen")
    items = sorted(
        screen.load_items("setup"),
        key=lambda it: it["history_prompt_tokens"],
        reverse=True,
    )[: args.items]
    tokenizer = screen._tokenizer()
    model = screen.load_model("1.7b")
    rows = []
    for item in items:
        dialogue = mc.load_dialogue(item["dialogue"])
        prompt = mc.chat_prompt(
            mc.user_message(
                dialogue, item["session"], item["queries"][0], "history", ""
            )
        )
        torch.cuda.reset_peak_memory_stats()
        torch.cuda.synchronize()
        started = time.monotonic()
        generated = screen.generate(
            model, tokenizer, prompt, args.max_new, args.deadline
        )
        torch.cuda.synchronize()
        seconds = time.monotonic() - started
        rows.append(
            {
                "id": item["id"],
                "context_tokens": generated["prompt_tokens"],
                "generated_tokens": generated["n_generated"],
                "seconds": seconds,
                "tok_per_s": generated["n_generated"] / seconds if seconds else None,
                "peak_allocated_gb": torch.cuda.max_memory_allocated() / 2**30,
                "peak_reserved_gb": torch.cuda.max_memory_reserved() / 2**30,
            }
        )
        print(json.dumps(rows[-1]), flush=True)
    return {"rows": rows}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--family", required=True, choices=["multiif", "memorycode"])
    parser.add_argument("--items", type=int, default=4)
    parser.add_argument("--max-new", type=int, default=512)
    parser.add_argument("--deadline", type=float, default=300.0)
    args = parser.parse_args(argv)
    coresident = gpu_pids()
    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    report = {
        "family": args.family,
        "started": started,
        "coresident_gpu_apps": coresident,
    }
    families = {"multiif": family_multiif, "memorycode": family_memorycode}
    report.update(families[args.family](args))
    rows = report["rows"]
    worst = max(r["seconds"] for r in rows)
    report["aggregate"] = {
        "max_seconds_per_item": worst,
        "budget_seconds_per_item_x1.5": 1.5 * worst,
        "max_peak_allocated_gb": max(r["peak_allocated_gb"] for r in rows),
        "max_peak_reserved_gb": max(r["peak_reserved_gb"] for r in rows),
        "max_context_tokens": max(r["context_tokens"] for r in rows),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{args.family}.json").write_text(json.dumps(report, indent=1))
    print(json.dumps(report["aggregate"], indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
