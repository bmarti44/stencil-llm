# ruff: noqa
"""G1 registered re-check: TIMED oracle — spotlight the relevant obligation
sentence ONLY at its decision moments during generation (function-name
moment, docstring-opener moment, annotation moment). Per-moment governance
is the program's thesis; always-on was the wrong oracle."""
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
    lo, hi = s.obligations_span
    block = s.text[lo:hi]
    # per-obligation sentence spans (chars)
    sent_spans = {}
    for key, marker in (("prefix", "function names"), ("doc", "docstring"), ("hint", "type-hinted")):
        i = block.find(next(sn for sn in block.split(".") if marker in sn))
        sent = next(sn for sn in block.split(".") if marker in sn) + "."
        a = lo + block.find(sent)
        sent_spans[key] = (a, a + len(sent))
    tok_spans = {}
    for key, (a, b) in sent_spans.items():
        cols = [i for i, (x, y) in enumerate(enc.offsets) if x < b and y > a]
        tok_spans[key] = (cols[0], cols[-1] + 1)
    return s, enc.ids, tok_spans


def moment(tail_text):
    """Which obligation governs the NEXT token, if any."""
    if re.search(r"def\s*$", tail_text):
        return "prefix"
    if re.search(r'"""\s*$', tail_text) or re.search(r"'''\s*$", tail_text):
        return "doc"
    m_ = re.search(r"def\s+\w+\s*\([^)]*:\s*$", tail_text)
    if m_:
        return "hint"
    return None


def gen_code(ids, tok_spans=None, beta=None, max_new=90):
    toks = torch.tensor([ids], device="cuda")
    outs = []
    text = ""
    for _ in range(max_new):
        ab = None
        if tok_spans is not None:
            key = moment(text[-60:])
            if key is not None:
                c0, c1 = tok_spans[key]
                t = toks.shape[1]
                bias = torch.zeros(t, t, device="cuda")
                bias[-1:, c0:c1] = beta  # only the current prediction row
                ab = {L: bias for L in LAYERS}
        nxt = int(m(toks, attn_bias=ab)[0, -1].argmax())
        outs.append(nxt)
        toks = torch.cat([toks, torch.tensor([[nxt]], device="cuda")], dim=1)
        text = tok.decode(outs)
        if "```" in text[-6:]:
            break
    return text.split("```")[0]


def score(code, s):
    checks = {}
    mname = re.search(r"def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", code)
    checks["prefix"] = bool(mname and mname.group(1).startswith(s.prefix + "_"))
    mdoc = re.search(r'"""\s*([A-Za-z]+)', code)
    checks["doc"] = bool(mdoc and mdoc.group(1) == s.doc_opener)
    args = re.search(r"def\s+\w+\s*\(([^)]*)\)", code)
    hints = re.findall(r":\s*([A-Za-z]+)", args.group(1)) if args else []
    checks["hint"] = bool(hints) and all(h == s.hint_type for h in hints)
    conf = {
        "prefix": bool(mname and mname.group(1).startswith(s.conflict["prefix"] + "_")),
        "doc": bool(mdoc and mdoc.group(1) == s.conflict["doc_opener"]),
        "hint": bool(hints) and all(h == s.conflict["hint_type"] for h in hints),
    }
    valid = bool(mname) and "return" in code
    return checks, conf, valid


def run(timed=False, beta=None):
    comp = {"prefix": 0, "doc": 0, "hint": 0}
    conf = {"prefix": 0, "doc": 0, "hint": 0}
    valid = 0
    with torch.no_grad():
        for seed in SEEDS:
            s, ids, tok_spans = build(seed)
            code = gen_code(ids, tok_spans if timed else None, beta)
            checks, conflicts, v = score(code, s)
            for k in comp:
                comp[k] += checks[k]
                conf[k] += conflicts[k]
            valid += v
    n = len(SEEDS)
    return {"compliance": {k: round(v / n, 3) for k, v in comp.items()},
            "mean": round(sum(comp.values()) / (3 * n), 3),
            "conflict": {k: round(v / n, 3) for k, v in conf.items()},
            "valid": round(valid / n, 3)}


base = run()
print(f"BASE: {base}", flush=True)
report = {"base": base}
for beta in BETAS:
    r = run(timed=True, beta=beta)
    print(f"TIMED ORACLE b={beta}: {r}", flush=True)
    report[f"timed_b{beta}"] = r
out = ROOT / "results" / "qwen" / "agentic-g1b.json"
out.write_text(json.dumps(report, indent=1))
print(f"evidence -> {out}")
