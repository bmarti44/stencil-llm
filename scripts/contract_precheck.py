"""Competence pre-check for the contract domain (proposal rev 5 §3).

Runs the UNMODIFIED shipping package (``stencil_focus=false``, plain greedy
``generate``)
on the authored contract tasks with the contracts stated immediately in the request,
scores joint success J (functional AND contract tests) in a sandbox, and writes one
record per task as it completes (atomic, resumable).  Eligibility rule, frozen in the
proposal: J >= 50% and function-only >= 60% on the registered task set.

Usage: ``uv run python scripts/contract_precheck.py --out
results/contracts/precheck.jsonl``
(``--no-contracts`` runs the same tasks without the contract lines, the descriptive
baseline; ``--limit`` for a smoke run).  No benchmark data is involved.
"""

from __future__ import annotations

import argparse
import functools
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stencil.contract_projects import all_tasks  # noqa: E402
from stencil.contracts import extract_file, render_request, score  # noqa: E402

print = functools.partial(print, flush=True)  # noqa: A001


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hub", default=str(ROOT / "deploy/stencil_focus/build/hub-4b"))
    ap.add_argument("--out", default=str(ROOT / "results/contracts/precheck.jsonl"))
    ap.add_argument("--max-new", type=int, default=1536)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--no-contracts", action="store_true")
    args = ap.parse_args()

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    torch.manual_seed(0)
    tok = AutoTokenizer.from_pretrained(args.hub)
    model = AutoModelForCausalLM.from_pretrained(
        args.hub, trust_remote_code=True, dtype=torch.bfloat16, device_map="cuda"
    )
    model.eval()
    eos_cfg = model.config.eos_token_id
    eos = list(eos_cfg if isinstance(eos_cfg, list) else [eos_cfg])

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if out.exists():
        for line in out.read_text().splitlines():
            if line.strip():
                done.add(json.loads(line)["id"])

    tasks = all_tasks()
    if args.limit:
        tasks = tasks[: args.limit]
    n_j = n_f = n = 0
    for task in tasks:
        if task.id in done:
            continue
        user = render_request(task, contracts_in_request=not args.no_contracts)
        msgs = [{"role": "user", "content": user}]
        prompt = tok.apply_chat_template(
            msgs, tokenize=False, add_generation_prompt=True, enable_thinking=False
        )
        ids = tok(prompt, return_tensors="pt").input_ids.to(model.device)
        t0 = time.time()
        with torch.no_grad():
            gen = model.generate(
                ids,
                attention_mask=torch.ones_like(ids),
                max_new_tokens=args.max_new,
                do_sample=False,
                eos_token_id=eos,
            )
        new = gen[0, ids.shape[1] :].tolist()
        truncated = len(new) >= args.max_new and new[-1] not in eos
        text = tok.decode([t for t in new if t not in eos], skip_special_tokens=True)
        new_target = extract_file(text)
        sc = score(task, new_target)
        rec = {
            "id": task.id,
            "project": task.project,
            "families": list(task.families),
            "states": [c.state for c in task.contracts],
            "contracts_in_request": not args.no_contracts,
            "prompt_tokens": int(ids.shape[1]),
            "generated_tokens": len(new),
            "truncated": truncated,
            "seconds": time.time() - t0,
            "response": text,
            **sc,
        }
        with out.open("a") as fh:
            fh.write(json.dumps(rec) + "\n")
        n += 1
        n_j += int(sc["J"])
        n_f += int(sc["functional"])
        print(
            f"[{task.id}] J={sc['J']} functional={sc['functional']} "
            f"contract={sc['contract']} parsed={sc['parsed']} gen={len(new)} "
            f"trunc={truncated} s={rec['seconds']:.0f}"
            f" | running J {n_j}/{n} F {n_f}/{n}"
        )
    print(f"DONE new={n} J={n_j} functional={n_f}")


if __name__ == "__main__":
    main()
