# ruff: noqa
"""S3-A0 scale admission (Amendment 2): base vs FULL-LEDGER re-insertion at
N in {8,16,32}, paired, with token costs. Gate: exists N* with reinsertion
acc < 0.80 (selection fails despite re-supplied text) OR cost > 300 tok/query
while base < 0.60."""
import json
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from tokenizers import Tokenizer

from stencil.qwen3 import Qwen3
from stencil.qwen_task import generate_governance

tok = Tokenizer.from_file(str(ROOT / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
m = Qwen3()
m.load_state_dict(torch.load(ROOT / "models" / "qwen3-1.7b.pt", map_location="cpu"), strict=True)
m = m.to(torch.bfloat16).cuda().eval()

SEED = 11_800_000
N_SESS = 64


def gen_from(text, max_new=20):
    toks = torch.tensor([tok.encode(text).ids], device="cuda")
    outs = []
    for _ in range(max_new):
        nxt = int(m(toks)[0, -1].argmax())
        outs.append(nxt)
        if tok.decode([nxt]).endswith("\n"):
            break
        toks = torch.cat([toks, torch.tensor([[nxt]], device="cuda")], dim=1)
    return tok.decode(outs).strip().split("\n")[0].strip().rstrip(".")


report = {}
with torch.no_grad():
    for N in (8, 16, 32):
        base_h = re_h = 0
        cost = 0
        for i in range(N_SESS):
            s = generate_governance(SEED + N * 10_000 + i, n_obligations=N)
            base_h += gen_from(s.text) == s.value
            lines = "".join(s.text[lo:hi] for lo, hi in sorted(s.ledger_spans.values()))
            qpos = s.text.rfind("Q: What is the " + s.field)
            rem = "(Reminder — authoritative ledger:" + lines + ")\n"
            cost += len(tok.encode(rem).ids)
            re_h += gen_from(s.text[:qpos] + rem + s.text[qpos:]) == s.value
        report[N] = {"base": base_h / N_SESS, "reinsertion": re_h / N_SESS,
                     "reinsertion_tokens_per_query": round(cost / N_SESS)}
        print(f"N={N}: base {base_h}/{N_SESS} = {base_h/N_SESS:.2f} | "
              f"reinsertion {re_h}/{N_SESS} = {re_h/N_SESS:.2f} @ ~{cost//N_SESS} tok/query", flush=True)
out = ROOT / "results" / "qwen" / "s3-a0.json"
out.write_text(json.dumps({"seed": SEED, "n_sess": N_SESS, "report": report}, indent=1))
gate = any(
    (r["reinsertion"] < 0.80) or (r["reinsertion_tokens_per_query"] > 300 and r["base"] < 0.60)
    for r in report.values()
)
print(f"S3-A0 GATE: {'PASS' if gate else 'MISS'} -> {out}")
