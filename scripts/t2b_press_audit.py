# ruff: noqa
"""Press audit for the T2b val selector claim (sol re-verification HIGH):
run base and selector arms over the val seeds, counting (a) timing-head
fires and (b) actually applied presses, and hashing each work's generated
token ids. Proves or refutes "the registered selector never pressed on val
and its outputs are token-identical to base"."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from stencil import determinism  # noqa: F401
import torch
from tokenizers import Tokenizer

from stencil.qwen3 import Qwen3
from stencil.t2_runner import run_session
from stencil.t2_select import candidate_spans
from stencil.t2_sessions import generate_t2

SEEDS = [12_960_000 + i for i in range(96)]
CLASSES = ["none", "prefix", "doc", "hint"]

tok = Tokenizer.from_file(str(ROOT / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
m = Qwen3()
m.load_state_dict(torch.load(ROOT / "models" / "qwen3-1.7b.pt", map_location="cpu"), strict=True)
m = m.to(torch.bfloat16).cuda().eval()
sel = torch.load(ROOT / "results" / "qwen" / "t2b-selector.pt", map_location="cpu")
head = torch.nn.Linear(2048, 4); head.load_state_dict(sel["head"]); head = head.cuda()
Wq = torch.nn.Linear(2048, 64); Wq.load_state_dict(sel["Wq"]); Wq = Wq.cuda()
Wk = torch.nn.Linear(2048, 64); Wk.load_state_dict(sel["Wk"]); Wk = Wk.cuda()
TAU, THETA = sel["tau"], sel["theta"]

counts = {"timing_fires": 0, "applied_presses": 0, "steps": 0}


def timing(model, toks, text):
    counts["steps"] += 1
    with torch.no_grad():
        h = model(toks, return_hidden=20)[0, -1].float()
        probs = torch.softmax(head(h), dim=-1)
        c = int(probs[1:].argmax()) + 1
        if float(probs[c]) > TAU:
            counts["timing_fires"] += 1
            return CLASSES[c]
        return None


def address(model, toks, ptxt, spans, key):
    enc = tok.encode(ptxt)
    cands = candidate_spans(ptxt, enc)
    if not cands:
        return None
    with torch.no_grad():
        h_prompt = model(torch.tensor([enc.ids], device="cuda"), return_hidden=20)[0].float()
        cf = torch.stack([h_prompt[c[2][0]:c[2][1]].mean(dim=0) for c in cands])
        s = model(toks, return_hidden=20)[0, -1].float()
        scores = (Wq(s) @ Wk(cf.cuda()).T) / 8.0
        j = int(scores.argmax())
        if float(scores[j]) <= THETA:
            return None
    ty = cands[j][0]
    if ty in spans:
        counts["applied_presses"] += 1
        return ty
    return None


def work_hashes(arm):
    hs = {}
    with torch.no_grad():
        for seed in SEEDS:
            sess = generate_t2(seed, 20, "val", interference="s0")
            rs = run_session(m, tok, sess, "val", arm,
                             timing=timing if arm == "selector" else None,
                             address=address if arm == "selector" else None)
            for r in rs:
                hs[f"{seed}:{r.turn}"] = hashlib.sha256(r.code.encode()).hexdigest()
    return hs


base_h = work_hashes("base")
sel_h = work_hashes("selector")
same = sum(1 for k in base_h if base_h[k] == sel_h.get(k))
out = {"n_works": len(base_h), "token_identical_works": same,
       "timing_fires": counts["timing_fires"],
       "applied_presses": counts["applied_presses"],
       "selector_steps": counts["steps"], "theta": THETA, "tau": TAU}
print(json.dumps(out, indent=1), flush=True)
(ROOT / "results" / "qwen" / "t2b-press-audit.json").write_text(json.dumps(out, indent=1))
print("saved results/qwen/t2b-press-audit.json")
