"""The oracle-reminder rescue diagnostic (Astra forward review, step 3).

Sixteen development blocks x two matched applicability cases x two conditions =
64 short generations.  Condition `off` is ordinary recency context; condition
`oracle` supplies the applicable instruction VERBATIM FROM THE SOURCE MESSAGE in
the proposed reminder format, under the same context ceiling.  A block succeeds
only if both of its cases succeed.

The oracle supplies the instruction, never code, expected values or a gold patch.
It is a diagnostic condition and cannot become the shipped intervention.

Registration and prespecified readings: results/scoped/RESCUE-REGISTRATION.md.
NO GPU PROCESS MAY LAUNCH while Brian's standing pause is in force; `--stub`
exercises the whole pipeline on CPU with no model at all.

    uv run python scripts/scoped_rescue.py --stub --out /tmp/rescue.jsonl
    uv run python scripts/scoped_rescue.py --summarize --out results/scoped/rescue.jsonl
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stencil.scoped_blocks import (  # noqa: E402
    SUITES,
    entering_project,
    rescue_prompts,
    resolve,
)
from stencil.scoped_dev_blocks import BLOCKS  # noqa: E402

# registration section 4: frozen before any generation
CONDITIONS = ("off", "oracle")
MAX_NEW = 160            # a SHORT edit: one function of tens of tokens
CONTEXT_CEILING = 4096   # the shared GB10 rule, generation included
PROMPT_BUDGET = CONTEXT_CEILING - MAX_NEW
DEADLINE_S = 120.0       # short edits; the whole-file screen's 300 s does not apply
SCORE_TIMEOUT_S = 30.0
HUB = str(ROOT / "deploy/stencil_focus/build/hub-4b")

FENCE = re.compile(r"```(?:python)?\n(.*?)```", re.S)


def extract(text: str, fname: str) -> str:
    """The single new function, or "" if the reply does not contain one."""
    blocks = FENCE.findall(text)
    body = blocks[0] if blocks else text
    lines = body.splitlines()
    start = next((i for i, ln in enumerate(lines)
                  if ln.lstrip().startswith(f"def {fname}(")), None)
    if start is None:
        return ""
    indent = len(lines[start]) - len(lines[start].lstrip())
    out = [lines[start][indent:]]
    for ln in lines[start + 1:]:
        if ln.strip() and (len(ln) - len(ln.lstrip())) <= indent:
            break
        out.append(ln[indent:] if len(ln) > indent else ln.strip())
    return "\n".join(out).rstrip() + "\n"


def score(block_id: str, case_index: int, source: str) -> dict:
    if not source.strip():
        return {"scores": dict.fromkeys(SUITES, False), "ok": False,
                "error": "no function in the reply"}
    proc = subprocess.run(  # noqa: S603 - fixed argv, untrusted payload on stdin
        [sys.executable, str(ROOT / "scripts/scoped_score_one.py")],
        input=json.dumps({"block": block_id, "case": case_index, "source": source}),
        capture_output=True, text=True, timeout=SCORE_TIMEOUT_S, check=False,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        return {"scores": dict.fromkeys(SUITES, False), "ok": False,
                "error": f"scorer exit {proc.returncode}: {proc.stderr[-400:]}"}
    return json.loads(proc.stdout)


def items():
    for block in BLOCKS:
        for index, case in enumerate(block.cases):
            yield block, index, case


def stub_reply(block, case, condition: str, mode: str) -> str:
    """CPU pipeline exercise with no model.  Three modes, all needed:

    `baseline` always answers with the package default -- deliberately wrong for
    most cases, because a stub that answered correctly would hide extraction and
    scoring defects behind a green summary.
    `correct` always answers gold: a POSITIVE control, without which a systematic
    extraction bug is indistinguishable from "the model cannot do it".
    `rescue` answers gold under the reminder and takes the newest-statement
    shortcut without it, so the decision arithmetic can be seen to report
    RESCUED when it should.
    """
    from stencil.scoped_blocks import p_always_newest, render_impl
    value, obs, _ = resolve(block.history, case.path, case.fn_kind)
    if mode == "correct" or (mode == "rescue" and condition == "oracle"):
        chosen = value
    elif mode == "rescue":
        chosen = p_always_newest(block, case)
    else:
        chosen = "default"
    return "```python\n" + render_impl(case.fname, case.fn_kind, chosen, obs) + "```"


def run(a) -> int:
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if out.exists():
        for line in out.read_text().splitlines():
            if line.strip():
                rec = json.loads(line)
                done.add((rec["block"], rec["case"], rec["condition"]))

    if a.stub:
        def token_len(text: str) -> int:
            return max(1, len(text) // 4)  # a stand-in, never used for a budget claim

        generate = None
    else:
        import os
        os.environ.setdefault("STENCIL_GPU_SHARE", "1")
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        tok = AutoTokenizer.from_pretrained(a.hub, trust_remote_code=True)
        model = AutoModelForCausalLM.from_pretrained(
            a.hub, dtype=torch.bfloat16, device_map="cuda", trust_remote_code=True
        ).eval()
        eos = [tok.eos_token_id]

        def token_len(text: str) -> int:
            return len(tok(text, add_special_tokens=False).input_ids)

        def generate(prompt: str) -> dict:
            ids = tok(prompt, return_tensors="pt",
                      add_special_tokens=False).input_ids.to(model.device)
            assert ids.shape[1] <= PROMPT_BUDGET, ids.shape
            t0 = time.monotonic()
            with torch.no_grad():
                gen = model.generate(ids, attention_mask=torch.ones_like(ids),
                                     max_new_tokens=MAX_NEW, do_sample=False,
                                     eos_token_id=eos, pad_token_id=tok.pad_token_id,
                                     max_time=a.deadline)
            secs = time.monotonic() - t0
            new = gen[0, ids.shape[1]:].tolist()
            ended = bool(new) and new[-1] in eos
            return {
                "output": tok.decode([t for t in new if t not in eos],
                                     skip_special_tokens=True),
                "generated_tokens": len(new), "seconds": secs,
                "truncated": len(new) >= MAX_NEW and not ended,
                "timed_out": secs >= a.deadline,
            }

    start, spent = time.monotonic(), 0.0
    for block, index, case in items():
        prompts = rescue_prompts(block, case, token_len, PROMPT_BUDGET)
        for condition in CONDITIONS:
            key = (block.id, index, condition)
            if key in done:
                continue
            elapsed_min = (time.monotonic() - start) / 60.0
            if a.budget_min and elapsed_min >= a.budget_min:
                print(f"INCOMPLETE: {elapsed_min:.1f} min spent of "
                      f"{a.budget_min} -- stopping before {key}")
                return 2
            built = prompts[condition]
            if a.stub:
                gen = {"output": stub_reply(block, case, condition, a.stub_mode),
                       "generated_tokens": 0,
                       "seconds": 0.0, "truncated": False, "timed_out": False}
            else:
                gen = generate(built["prompt"])
            spent += gen["seconds"]
            source = extract(gen["output"], case.fname)
            result = score(block.id, index, source)
            want, obs, _ = resolve(block.history, case.path, case.fn_kind)
            rec = {
                "block": block.id, "family": block.family, "case": index,
                "case_name": case.name, "condition": condition,
                "applicable": want, "obligations": list(obs),
                "prompt_tokens": built["tokens"],
                "reminder": built.get("reminder", ""),
                "kept_messages": built["kept"],
                "n_history": len(block.history),
                "output": gen["output"], "extracted": source,
                "generated_tokens": gen["generated_tokens"],
                "seconds": gen["seconds"], "truncated": gen["truncated"],
                "timed_out": gen["timed_out"],
                "scores": result["scores"], "ok": result["ok"],
                "error": result["error"],
                "invalid": not source.strip(),
            }
            with out.open("a") as fh:
                fh.write(json.dumps(rec) + "\n")
            print(f"{block.id} case{index} {condition:6} "
                  f"want={want:8} ok={result['ok']} {gen['seconds']:.1f}s")
    print(f"complete: {spent / 60:.1f} generation-minutes")
    return 0


def summarize(path: Path) -> int:
    recs = [json.loads(x) for x in path.read_text().splitlines() if x.strip()]
    by = {(r["block"], r["case"], r["condition"]): r for r in recs}
    per_block, rows = {}, []
    for block in BLOCKS:
        got = {}
        for condition in CONDITIONS:
            cases = [by.get((block.id, i, condition)) for i in (0, 1)]
            got[condition] = all(c and c["ok"] for c in cases)
        per_block[block.id] = got
        rows.append((block.id, got["off"], got["oracle"]))
    off_n = sum(1 for _b, o, _x in rows if o)
    oracle_n = sum(1 for _b, _o, x in rows if x)
    wins = [b for b, o, x in rows if x and not o]
    losses = [b for b, o, x in rows if o and not x]

    print(f"{'block':6} {'off':6} {'oracle':6}")
    for bid, o, x in rows:
        print(f"{bid:6} {str(o):6} {str(x):6}")
    print(f"\noff succeeds on {off_n}/16 blocks; oracle on {oracle_n}/16")
    print(f"wins (oracle only): {len(wins)} {wins}")
    print(f"losses (off only):  {len(losses)} {losses}")
    for condition in CONDITIONS:
        sub = [r for r in recs if r["condition"] == condition]
        if not sub:
            continue
        median = sorted(r["generated_tokens"] for r in sub)[len(sub) // 2]
        print(f"{condition:6} invalid {sum(r['invalid'] for r in sub)}/{len(sub)} "
              f"truncated {sum(r['truncated'] for r in sub)} "
              f"timed_out {sum(r['timed_out'] for r in sub)} "
              f"median tokens {median}")
    # A ceiling is a DIFFERENT situation from "the model cannot do it", and the
    # prespecified rule cannot tell them apart, so it is flagged separately
    # rather than quietly folded into the reading.
    if off_n >= 12:
        print(f"\nCEILING WARNING: the off condition already succeeds on "
              f"{off_n}/16 blocks, so there is little headroom for the reminder "
              f"to rescue. The prespecified reading below still stands as "
              f"written, but the blocks are too easy to measure this.")

    # the prespecified reading, registration section 7 -- not renegotiable here
    if oracle_n >= 12 and len(wins) >= 6 and len(losses) <= 1:
        print("\nREADING: RESCUED -- raise direction 1 from 28% to about 40%")
    elif oracle_n <= 8 or (len(wins) - len(losses)) <= 2:
        print("\nREADING: NOT RESCUED -- reduce to about 12% and stop this "
              "coding-workload direction under the present budget")
    else:
        print("\nREADING: INTERMEDIATE -- roughly 20-25%; do not launch the "
              "confirmation")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=str(ROOT / "results/scoped/rescue.jsonl"))
    ap.add_argument("--hub", default=HUB)
    ap.add_argument("--deadline", type=float, default=DEADLINE_S)
    ap.add_argument("--budget-min", type=float, default=0.0)
    ap.add_argument("--stub", action="store_true",
                    help="no model: exercise packing, extraction and scoring on CPU")
    ap.add_argument("--stub-mode", default="baseline",
                    choices=("baseline", "correct", "rescue"))
    ap.add_argument("--summarize", action="store_true")
    a = ap.parse_args(argv)
    if a.summarize:
        return summarize(Path(a.out))
    assert entering_project(BLOCKS[0]), "fixture missing"
    return run(a)


if __name__ == "__main__":
    raise SystemExit(main())
