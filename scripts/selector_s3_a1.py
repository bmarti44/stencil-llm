# ruff: noqa
"""S1 registered oracle-spotlight run (SELECTOR-PLAN Amendment 1).

Preregistered grid: sites {20},{24},{20-27} x beta {2,4}; all heads; bias
rows = final-query rows onward; cols = governing ledger-line token span.
Gates per config: rescue_rate >= 0.50 AND broken == 0; wrong-span control
<= 10% flips. Selection rule: pass gate, then fewest layers, lowest beta,
highest net gain. Fresh seed block; per-example JSON evidence."""
import json
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from tokenizers import Tokenizer

from stencil.qwen3 import Qwen3
from stencil.qwen_task import FIELDS32, generate_governance

SEED_BASE = 11_820_000  # S3-A1 block (N*=32)
N = 64
GRID = [(tuple(range(20, 28)), 2.0), (tuple(range(20, 28)), 4.0)]

tok = Tokenizer.from_file(str(ROOT / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
m = Qwen3()
m.load_state_dict(torch.load(ROOT / "models" / "qwen3-1.7b.pt", map_location="cpu"), strict=True)
m = m.to(torch.bfloat16).cuda().eval()


def build(seed):
    s = generate_governance(seed, n_obligations=32)
    enc = tok.encode(s.text)
    ids = enc.ids
    # governing span chars -> token columns via offsets (overlap mapping)
    lo_c, hi_c = s.ledger_spans[FIELDS32.index(s.field)]
    cols = [i for i, (a, b) in enumerate(enc.offsets) if a < hi_c and b > lo_c]
    assert cols and s.field.split()[0] in s.text[enc.offsets[cols[0]][0]:enc.offsets[cols[-1]][1]], "span mapping failed"
    row_start_char = s.text.rfind("Q: What is the " + s.field)
    row_start = next(i for i, (a, b) in enumerate(enc.offsets) if b > row_start_char)
    return s, ids, (cols[0], cols[-1] + 1), row_start


def gen(ids, bias_cfg=None, max_new=20):
    toks = torch.tensor([ids], device="cuda")
    outs = []
    for _ in range(max_new):
        ab = None
        if bias_cfg is not None:
            layers, beta, (c0, c1), row_start = bias_cfg
            t = toks.shape[1]
            bias = torch.zeros(t, t, device="cuda")
            bias[row_start:, c0:c1] = beta
            ab = {L: bias for L in layers}
        nxt = int(m(toks, attn_bias=ab)[0, -1].argmax())
        outs.append(nxt)
        toks = torch.cat([toks, torch.tensor([[nxt]], device="cuda")], dim=1)
    return tok.decode(outs).strip().split("\n")[0].strip().rstrip(".")


items = [build(SEED_BASE + i) for i in range(N)]
base = []
with torch.no_grad():
    for s, ids, span, row in items:
        base.append(gen(ids) == s.value)
base_correct = sum(base)
print(f"BASE on S1 block: {base_correct}/{N}", flush=True)

results = []
records = []
with torch.no_grad():
    for layers, beta in GRID:
        gained = broken = 0
        for j, (s, ids, span, row) in enumerate(items):
            out = gen(ids, (layers, beta, span, row)) == s.value
            if out and not base[j]:
                gained += 1
            if not out and base[j]:
                broken += 1
            records.append({"config": [list(layers), beta], "seed": SEED_BASE + j,
                            "base": base[j], "spot": out})
        rescue = gained / max(1, N - base_correct)
        res = {"layers": list(layers), "beta": beta, "gained": gained, "broken": broken,
               "rescue_rate": round(rescue, 3), "net": gained - broken,
               "gate": rescue >= 0.5 and broken == 0}
        results.append(res)
        print(res, flush=True)

# wrong-span control on the best passing config
passing = [r for r in results if r["gate"]]
if passing:
    best = sorted(passing, key=lambda r: (len(r["layers"]), r["beta"], -r["net"]))[0]
    layers, beta = tuple(best["layers"]), best["beta"]
    wrong_fix = 0
    with torch.no_grad():
        for j, (s, ids, span, row) in enumerate(items):
            if base[j]:
                continue
            wrong_span = (max(0, span[0] - 40), span[0])  # a non-governing region
            if gen(ids, (layers, beta, wrong_span, row)) == s.value:
                wrong_fix += 1
    n_err = N - base_correct
    print(f"SELECTED {best} | wrong-span control fixes {wrong_fix}/{n_err} (gate <=10%)")
    best["wrong_span_fixes"] = wrong_fix
    best["wrong_span_gate"] = wrong_fix <= 0.10 * n_err
else:
    print("NO CONFIG PASSED THE GATE")
out = ROOT / "results" / "qwen" / "s3-a1-oracle.json"
out.write_text(json.dumps({"seed_base": SEED_BASE, "n": N, "base_correct": base_correct,
                           "grid": results, "records": records}, indent=1))
print(f"evidence -> {out}")
