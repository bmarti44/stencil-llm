"""Parity gate, generation half (GPU): the published wrapper reproduces the research
runtime on the 16 SETUP-LONG items.

For every item and both flag states the assembled hub folder (``push_to_hub.py
--dry-run`` output) is loaded through ``AutoModelForCausalLM`` with
``trust_remote_code=True``; the session interface rebuilds the item's prompt, the
prompt must equal the research record's prompt token count, and the greedy output
is compared with the research runtime's saved generation (``setup_long-role_evicted``
records: ``base`` for the flag off, ``focus`` for the flag on). With the flag off the
output must also equal plain ``AutoModelForCausalLM`` (Qwen3) on the same prompt.
Writes results/memorycode-long/parity.json; exit 1 on any mismatch.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[1]
RECORDS = REPO / "results" / "memorycode-long" / "setup_long-role_evicted"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hub", default=str(HERE / "build" / "hub"))
    parser.add_argument("--trunk", default=str(REPO / "models/qwen3-1.7b-hf"))
    parser.add_argument(
        "--out", default=str(REPO / "results/memorycode-long/parity.json")
    )
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument(
        "--records",
        default=str(RECORDS),
        help="research record directory to compare against "
        "(Exp 4B: results/memorycode-long/setup_long-4b-role_evicted)",
    )
    args = parser.parse_args(argv)
    records_dir = Path(args.records)

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    sys.path.insert(0, str(REPO / "src"))
    from stencil import memorycode as mc

    tokenizer = AutoTokenizer.from_pretrained(args.hub)
    model = AutoModelForCausalLM.from_pretrained(
        args.hub, trust_remote_code=True, dtype=torch.bfloat16, device_map="cuda"
    )
    model.eval()
    plain = AutoModelForCausalLM.from_pretrained(
        args.trunk, dtype=torch.bfloat16, device_map="cuda"
    )
    plain.eval()
    items = [
        it
        for it in json.loads((REPO / "results/memorycode-long/items.json").read_text())[
            "items"
        ]
        if it["split"] == "setup_long"
    ]
    if args.limit:
        items = items[: args.limit]
    rows = []
    for item in items:
        record = json.loads((records_dir / f"item-{item['id']}.json").read_text())
        dialogue = mc.load_dialogue(item["dialogue"])
        head, sep, request = mc.long_request(dialogue, item["queries"][0])
        row = {"id": item["id"]}
        for flag, arm in ((False, "base"), (True, "focus")):
            session = model.new_session(tokenizer, stencil_focus=flag)
            for role, text, rendered in mc.focus_session_messages(
                dialogue, item["session"]
            ):
                session.add_message(role, text, rendered=rendered)
            text = session.generate(
                request, head=head, separator=sep, max_new_tokens=512
            )
            research = record["arms"][arm]["generations"][0]
            ids = session.last["generated_token_ids"]
            entry = {
                "prompt_tokens": session.last["prompt_tokens"],
                "research_prompt_tokens": research["window"]["prompt_tokens"],
                "prompt_match": session.last["prompt_tokens"]
                == research["window"]["prompt_tokens"],
                "generation_match": ids == research["generated_token_ids"],
                "text_match": text.strip() == research["text"].strip(),
            }
            if not flag:
                prompt_ids = torch.tensor(
                    [session.encode(session.last["prompt"])], device="cuda"
                )
                with torch.no_grad():
                    out = plain.generate(
                        prompt_ids,
                        attention_mask=torch.ones_like(prompt_ids),
                        do_sample=False,
                        max_new_tokens=512,
                        eos_token_id=plain.config.eos_token_id,
                    )
                entry["plain_match"] = out[0, prompt_ids.shape[1] :].tolist() == ids
            row[arm] = entry
            print(json.dumps({"id": item["id"], "arm": arm, **entry}), flush=True)
        rows.append(row)
    summary = {
        "items": len(rows),
        "prompt_match": sum(
            r[a]["prompt_match"] for r in rows for a in ("base", "focus")
        ),
        "generation_match": sum(
            r[a]["generation_match"] for r in rows for a in ("base", "focus")
        ),
        "plain_match": sum(r["base"]["plain_match"] for r in rows),
        "rows": rows,
    }
    Path(args.out).write_text(json.dumps(summary, indent=1) + "\n")
    print(json.dumps({k: v for k, v in summary.items() if k != "rows"}))
    ok = (
        summary["prompt_match"] == 2 * len(rows)
        and summary["generation_match"] == 2 * len(rows)
        and summary["plain_match"] == len(rows)
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
