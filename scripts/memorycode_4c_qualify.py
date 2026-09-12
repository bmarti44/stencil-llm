"""Exp 4C technical qualification and timing (REGISTRATION-4C.md, 44 generations).

1. Eight timing calls through the package: SETUP items 359-99, 352-99, 351-99, 302-49 in
   that order, off then on for each; t_max = the maximum elapsed call time.
2. Package-off outputs for the other 12 SETUP items (16 off prompts in total).
3. Plain upstream ``AutoModelForCausalLM`` on the 16 off prompts (same EOS convention,
   raw token comparison); require 16/16 matches.
4. Reload the package and replay the eight timing calls; require 8/8 raw-token matches.
Outputs are recorded for reproducibility and are NOT scored for any launch gate.

Writes results/memorycode-long/qualification-4c.json with t_max, N by the timing-only
rule, the match counts, the package fingerprint and environment.
"""

from __future__ import annotations

import argparse
import gc
import importlib.util
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

_spec = importlib.util.spec_from_file_location(
    "memorycode_package_run", ROOT / "scripts" / "memorycode_package_run.py"
)
runner = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(runner)
screen = runner.screen

TIMING_IDS = ["359-99", "352-99", "351-99", "302-49"]
OUT = ROOT / "results" / "memorycode-long"


def _call(model, tokenizer, mc, dialogue, item, arm, research_base, args) -> dict:
    session, prompt, built, (head, sep, request) = runner.build_arm(
        model, tokenizer, mc, dialogue, item, arm, research_base, args.max_new
    )
    gen = runner.generate_package(
        session, request, head, sep, args.max_new, args.deadline
    )
    return {
        "id": item["id"],
        "arm": arm,
        "prompt": prompt,
        "prompt_tokens": built["prompt_tokens"],
        "prompt_ids": session.encode(prompt),
        "raw_ids": gen["generated_token_ids_raw"],
        "eos_token_ids": gen["eos_token_ids"],
        "seconds": gen["seconds"],
        "termination": gen["termination"],
        "text": gen["text"],
    }


def _free(model):
    import torch

    del model
    gc.collect()
    torch.cuda.empty_cache()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--hub", default=str(ROOT / "deploy/stencil_focus/build/hub-4b")
    )
    parser.add_argument("--trunk", default=str(ROOT / "models/qwen3-4b-hf"))
    parser.add_argument("--out", default=str(OUT / "qualification-4c.json"))
    parser.add_argument("--max-new", type=int, default=screen.MAX_NEW)
    parser.add_argument("--deadline", type=float, default=screen.DEADLINE)
    parser.add_argument("--model", default="4b")
    args = parser.parse_args(argv)
    if Path(args.out).exists():
        raise SystemExit(f"{args.out} exists; qualification runs once")

    import torch
    from transformers import AutoModelForCausalLM

    from stencil import memorycode as mc

    hub = Path(args.hub)
    args.cohort, args.policy, args.window = "long", "role_evicted", mc.WINDOW
    manifest = runner.package_manifest(args, OUT, hub, OUT / "items-4c-candidates.json")
    manifest["budget_tokens"] = mc.BUDGET
    setup = [
        it
        for it in json.loads((OUT / "items.json").read_text())["items"]
        if it["split"] == "setup_long"
    ]
    by_id = {it["id"]: it for it in setup}
    research_tokenizer = screen._tokenizer()
    started = time.monotonic()

    def base_tokens(item):
        dialogue = mc.load_dialogue(item["dialogue"])
        return dialogue, mc.build_long_prompt(
            dialogue, item["session"], item["queries"][0], research_tokenizer, ""
        )["prompt_tokens"]

    # 1. eight timing calls
    model, tokenizer = runner.load_package(hub)
    manifest["environment"]["attn_implementation"] = getattr(
        model.config, "_attn_implementation", None
    )
    timing = []
    for iid in TIMING_IDS:
        item = by_id[iid]
        dialogue, rb = base_tokens(item)
        for arm in ("base", "focus"):
            timing.append(_call(model, tokenizer, mc, dialogue, item, arm, rb, args))
            print(
                f"timing {iid} {arm}: {timing[-1]['seconds']:.1f}s "
                f"{timing[-1]['termination']}",
                flush=True,
            )
    t_max = max(c["seconds"] for c in timing)
    # 2. off outputs for the other 12
    off = {c["id"]: c for c in timing if c["arm"] == "base"}
    for item in setup:
        if item["id"] in off:
            continue
        dialogue, rb = base_tokens(item)
        off[item["id"]] = _call(model, tokenizer, mc, dialogue, item, "base", rb, args)
        print(f"off {item['id']}: {off[item['id']]['seconds']:.1f}s", flush=True)
    _free(model)
    # 3. plain upstream model on the 16 off prompts
    plain = AutoModelForCausalLM.from_pretrained(
        args.trunk, dtype=torch.bfloat16, device_map="cuda"
    )
    plain.eval()
    plain_matches = {}
    for iid, call in off.items():
        ids = torch.tensor([call["prompt_ids"]], device="cuda")
        with torch.no_grad():
            out = plain.generate(
                ids,
                attention_mask=torch.ones_like(ids),
                do_sample=False,
                max_new_tokens=args.max_new,
                max_time=args.deadline,
                eos_token_id=call["eos_token_ids"],
            )
        raw = out[0, ids.shape[1] :].tolist()
        plain_matches[iid] = raw == call["raw_ids"]
        print(f"plain {iid}: match={plain_matches[iid]}", flush=True)
    _free(plain)
    # 4. reload the package, replay the eight calls
    model, tokenizer = runner.load_package(hub)
    replay_matches = []
    for call in timing:
        item = by_id[call["id"]]
        dialogue, rb = base_tokens(item)
        again = _call(model, tokenizer, mc, dialogue, item, call["arm"], rb, args)
        replay_matches.append(
            {
                "id": call["id"],
                "arm": call["arm"],
                "prompt_match": again["prompt"] == call["prompt"],
                "raw_match": again["raw_ids"] == call["raw_ids"],
                "seconds": again["seconds"],
            }
        )
        print(f"replay {call['id']} {call['arm']}: {replay_matches[-1]}", flush=True)
    _free(model)
    n_plain = sum(plain_matches.values())
    n_replay = sum(r["raw_match"] and r["prompt_match"] for r in replay_matches)
    n_rule = min(196, int(28_800 // (3 * t_max)))
    passed = n_plain == 16 and n_replay == 8
    report = {
        "registration": "results/memorycode-long/REGISTRATION-4C.md",
        "manifest": manifest,
        "t_max_seconds": t_max,
        "timing_calls": [
            {k: v for k, v in c.items() if k not in ("prompt", "prompt_ids")}
            for c in timing
        ],
        "off_outputs": {
            k: {kk: vv for kk, vv in v.items() if kk not in ("prompt", "prompt_ids")}
            for k, v in off.items()
        },
        "plain_matches": plain_matches,
        "replay_matches": replay_matches,
        "n_plain_matches": n_plain,
        "n_replay_matches": n_replay,
        "passed": passed,
        "n_by_timing_rule": n_rule,
        "eligible": passed and n_rule >= 128,
        "generations": 44,
        "wall_seconds": time.monotonic() - started,
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    screen._write_atomic(Path(args.out), report)
    print(
        json.dumps(
            {
                k: report[k]
                for k in (
                    "t_max_seconds",
                    "n_plain_matches",
                    "n_replay_matches",
                    "passed",
                    "n_by_timing_rule",
                    "eligible",
                    "wall_seconds",
                )
            },
            indent=1,
        )
    )
    return 0 if report["eligible"] else 1


if __name__ == "__main__":
    sys.exit(main())
