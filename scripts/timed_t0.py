# ruff: noqa
"""T0 (TIMED-SELECTOR-PLAN): oracle confirmation under honest instruments.

Fresh dev seeds (12.3M), AST/execution scorer, opening-quote moment fix,
registered grid b in {2,4}, wrong-sentence and random-moment controls.
Gates: parse-gated mean compliance lift >= +15; paired parse-rate
degradation == 0 at the selected config; controls at their signatures.
"""
import ast
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from stencil import determinism  # noqa: F401  (before torch use — registered)
import torch
from tokenizers import Tokenizer

from stencil.qwen3 import Qwen3
from stencil.qwen_task import generate_codegov

SEEDS = list(range(12_300_000, 12_300_064))
LAYERS = tuple(range(20, 28))
BETAS = [2.0, 4.0]

tok = Tokenizer.from_file(str(ROOT / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
m = Qwen3()
m.load_state_dict(torch.load(ROOT / "models" / "qwen3-1.7b.pt", map_location="cpu"), strict=True)
m = m.to(torch.bfloat16).cuda().eval()


def build(seed):
    s = generate_codegov(seed)
    enc = tok.encode(s.text)
    tok_spans = {}
    for key, (a, b) in s.sentence_spans.items():
        cols = [i for i, (x, y) in enumerate(enc.offsets) if x < b and y > a]
        tok_spans[key] = (cols[0], cols[-1] + 1)
    return s, enc.ids, tok_spans


def moment(tail_text):
    """Opening-quote fix: doc moment only when an ODD number of triple-quotes
    has been emitted (we are entering, not leaving, a docstring)."""
    if re.search(r"\bdef\s*$", tail_text):
        return "prefix"
    if re.search(r'"""\s*$', tail_text) and tail_text.count('"""') % 2 == 1:
        return "doc"
    if re.search(r"def\s+\w+\s*\([^)]*:\s*$", tail_text):
        return "hint"
    return None


def gen_code(ids, tok_spans=None, beta=None, mode="timed", rng=None, max_new=90):
    toks = torch.tensor([ids], device="cuda")
    outs = []
    text = ""
    n_biased = 0
    for _ in range(max_new):
        ab = None
        if tok_spans is not None:
            key = None
            if mode == "timed":
                key = moment(text[-80:])
            elif mode == "wrong":
                k0 = moment(text[-80:])
                if k0 is not None:
                    key = {"prefix": "doc", "doc": "hint", "hint": "prefix"}[k0]
            elif mode == "random":
                if rng.random() < 0.06:  # rate-matched ~5/90 steps
                    key = ["prefix", "doc", "hint"][int(rng.random() * 3)]
            if key is not None:
                c0, c1 = tok_spans[key]
                t = toks.shape[1]
                bias = torch.zeros(t, t, device="cuda")
                bias[-1:, c0:c1] = beta
                ab = {L: bias for L in LAYERS}
                n_biased += 1
        nxt = int(m(toks, attn_bias=ab)[0, -1].argmax())
        outs.append(nxt)
        toks = torch.cat([toks, torch.tensor([[nxt]], device="cuda")], dim=1)
        text = tok.decode(outs)
        if "```" in text[-6:]:
            break
    return text.split("```")[0], n_biased


OP_TESTS = {"sum": (3, 5, 8), "max": (3, 5, 5), "mul": (3, 5, 15), "sub": (9, 4, 5)}


def score(code, s):
    rec = {"parse": False, "prefix": False, "doc": False, "hint": False,
           "exec_ok": False, "conflict": {"prefix": False, "doc": False, "hint": False}}
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return rec
    rec["parse"] = True
    fns = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    if not fns:
        return rec
    fn = fns[0]  # registered target policy: first function is the target
    rec["prefix"] = fn.name.startswith(s.prefix + "_")
    rec["conflict"]["prefix"] = fn.name.startswith(s.conflict["prefix"] + "_")
    doc = ast.get_docstring(fn)
    first = doc.split()[0] if doc and doc.split() else ""
    rec["doc"] = first == s.doc_opener
    rec["conflict"]["doc"] = first == s.conflict["doc_opener"]
    args = fn.args.args
    def annname(a):
        return getattr(a.annotation, "id", None) if a.annotation else None
    rec["hint"] = bool(args) and all(annname(a) == s.hint_type for a in args)
    rec["conflict"]["hint"] = bool(args) and all(annname(a) == s.conflict["hint_type"] for a in args)
    x, y, want = OP_TESTS[s.op]
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(code + f"\nimport sys\nsys.exit(0 if {fn.name}({x}, {y}) == {want} else 3)\n")
        path = f.name
    try:
        r = subprocess.run([sys.executable, path], timeout=5, capture_output=True)
        rec["exec_ok"] = r.returncode == 0
    except Exception:
        pass
    return rec


def run(mode=None, beta=None):
    import random
    rng = random.Random(0)
    agg = {"parse": 0, "prefix": 0, "doc": 0, "hint": 0, "exec_ok": 0}
    conf = {"prefix": 0, "doc": 0, "hint": 0}
    recs = []
    with torch.no_grad():
        for seed in SEEDS:
            s, ids, tok_spans = build(seed)
            code, nb = gen_code(ids, tok_spans if mode else None, beta, mode or "timed", rng)
            r = score(code, s)
            for k in agg:
                agg[k] += r[k]
            for k in conf:
                conf[k] += r["conflict"][k]
            recs.append({"seed": seed, **{k: r[k] for k in agg}, "conflict": r["conflict"],
                         "biased_steps": nb, "code": code})
    n = len(SEEDS)
    comp_parse_gated = sum(rec["prefix"] + rec["doc"] + rec["hint"] for rec in recs if rec["parse"])
    return {"parse": agg["parse"] / n, "exec_ok": agg["exec_ok"] / n,
            "compliance": {k: agg[k] / n for k in ("prefix", "doc", "hint")},
            "mean_parse_gated": comp_parse_gated / (3 * n),
            "conflict": {k: v / n for k, v in conf.items()}, "records": recs}


report = {}
base = run()
report["base"] = base
print(f"BASE: parse {base['parse']:.3f} exec {base['exec_ok']:.3f} "
      f"parse-gated mean {base['mean_parse_gated']:.3f} comp {base['compliance']} conflict {base['conflict']}", flush=True)
for beta in BETAS:
    r = run("timed", beta)
    report[f"timed_b{beta}"] = r
    print(f"TIMED b={beta}: parse {r['parse']:.3f} exec {r['exec_ok']:.3f} "
          f"parse-gated mean {r['mean_parse_gated']:.3f} comp {r['compliance']} conflict {r['conflict']}", flush=True)
r = run("wrong", 4.0)
report["wrong_b4"] = r
print(f"WRONG-SENTENCE b=4: parse-gated mean {r['mean_parse_gated']:.3f} conflict {r['conflict']}", flush=True)
r = run("random", 4.0)
report["random_b4"] = r
print(f"RANDOM-MOMENT b=4: parse-gated mean {r['mean_parse_gated']:.3f}", flush=True)
out = ROOT / "results" / "qwen" / "timed-t0.json"
out.write_text(json.dumps(report, indent=1))
# gate evaluation (paired parse degradation at selected config)
for beta in BETAS:
    tr = report[f"timed_b{beta}"]
    lost = sum(1 for b_, t_ in zip(report["base"]["records"], tr["records"]) if b_["parse"] and not t_["parse"])
    lift = tr["mean_parse_gated"] - base["mean_parse_gated"]
    print(f"GATE b={beta}: lift {100*lift:+.1f}pts (>= +15) | paired parse lost {lost} (== 0) -> "
          f"{'PASS' if lift >= 0.15 and lost == 0 else 'MISS'}")
print(f"evidence -> {out}")
