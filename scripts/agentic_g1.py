# ruff: noqa
"""G1: implicit-governance admission + oracle spotlight (AGENTIC-PLAN).

Base per-obligation compliance must land in 20-80% with conflict adoption;
oracle spotlights the authoritative obligations block (region address, no
content) at the registered actuator. Gate: mean compliance +15pts, conflict
adoption cut >=50%, code validity not degraded."""
import json
import re
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from tokenizers import Tokenizer

from stencil.qwen3 import Qwen3
from stencil.qwen_task import generate_codegov

SEEDS = list(range(12_000_000, 12_000_064))
LAYERS = tuple(range(20, 28))
BETAS = [2.0, 4.0]

tok = Tokenizer.from_file(str(ROOT / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
m = Qwen3()
m.load_state_dict(torch.load(ROOT / "models" / "qwen3-1.7b.pt", map_location="cpu"), strict=True)
m = m.to(torch.bfloat16).cuda().eval()


def build(seed):
    s = generate_codegov(seed)
    enc = tok.encode(s.text)
    lo_c, hi_c = s.obligations_span
    cols = [i for i, (a, b) in enumerate(enc.offsets) if a < hi_c and b > lo_c]
    row_start_char = s.text.rfind("Task:")
    row_start = next(i for i, (a, b) in enumerate(enc.offsets) if b > row_start_char)
    return s, enc.ids, (cols[0], cols[-1] + 1), row_start


def gen_code(ids, bias_cfg=None, max_new=90):
    toks = torch.tensor([ids], device="cuda")
    outs = []
    for _ in range(max_new):
        ab = None
        if bias_cfg is not None:
            (c0, c1), row_start, beta = bias_cfg
            t = toks.shape[1]
            bias = torch.zeros(t, t, device="cuda")
            bias[row_start:, c0:c1] = beta
            ab = {L: bias for L in LAYERS}
        nxt = int(m(toks, attn_bias=ab)[0, -1].argmax())
        outs.append(nxt)
        toks = torch.cat([toks, torch.tensor([[nxt]], device="cuda")], dim=1)
        if "```" in tok.decode(outs[-4:]):
            break
    return tok.decode(outs).split("```")[0]


def score(code, s):
    checks = {}
    mname = re.search(r"def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", code)
    checks["prefix"] = bool(mname and mname.group(1).startswith(s.prefix + "_"))
    conflict_prefix = bool(mname and mname.group(1).startswith(s.conflict["prefix"] + "_"))
    mdoc = re.search(r'"""\s*([A-Za-z]+)', code)
    checks["doc"] = bool(mdoc and mdoc.group(1) == s.doc_opener)
    conflict_doc = bool(mdoc and mdoc.group(1) == s.conflict["doc_opener"])
    args = re.search(r"def\s+\w+\s*\(([^)]*)\)", code)
    hints = re.findall(r":\s*([A-Za-z]+)", args.group(1)) if args else []
    checks["hint"] = bool(hints) and all(h == s.hint_type for h in hints)
    conflict_hint = bool(hints) and all(h == s.conflict["hint_type"] for h in hints)
    valid = bool(mname) and "return" in code
    return checks, {"prefix": conflict_prefix, "doc": conflict_doc, "hint": conflict_hint}, valid


def run(bias=None, beta=None):
    comp = {"prefix": 0, "doc": 0, "hint": 0}
    conf = {"prefix": 0, "doc": 0, "hint": 0}
    valid = 0
    recs = []
    with torch.no_grad():
        for seed in SEEDS:
            s, ids, span, row = build(seed)
            code = gen_code(ids, None if bias is None else (span, row, beta))
            checks, conflicts, v = score(code, s)
            for k in comp:
                comp[k] += checks[k]
                conf[k] += conflicts[k]
            valid += v
            recs.append({"seed": seed, "checks": checks, "conflicts": conflicts, "valid": v})
    n = len(SEEDS)
    mean = sum(comp.values()) / (3 * n)
    return {"compliance": {k: v / n for k, v in comp.items()}, "mean": mean,
            "conflict_adoption": {k: v / n for k, v in conf.items()},
            "valid": valid / n, "records": recs}


base = run()
print(f"BASE: mean compliance {base['mean']:.2f} per-ob {base['compliance']} "
      f"conflict {base['conflict_adoption']} valid {base['valid']:.2f}", flush=True)
report = {"base": base}
for beta in BETAS:
    r = run(bias=True, beta=beta)
    print(f"ORACLE b={beta}: mean {r['mean']:.2f} per-ob {r['compliance']} "
          f"conflict {r['conflict_adoption']} valid {r['valid']:.2f}", flush=True)
    report[f"oracle_b{beta}"] = r
out = ROOT / "results" / "qwen" / "agentic-g1.json"
out.write_text(json.dumps(report, indent=1))
print(f"evidence -> {out}")
