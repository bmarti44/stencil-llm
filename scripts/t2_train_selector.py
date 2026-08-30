# ruff: noqa
"""T2 stage 3: train timing + address heads per CONTRACT v3 frozen recipe.

- rollout policy (frozen): base + oracle rollouts on the train split;
- timing: linear 4-way {none,prefix,doc,hint} over h20, AST-grounded labels,
  Adam 1e-3, 30 epochs, class weights [1,20,20,20], batch 512;
- address: 64-d query-key over the MUST-2 candidate set (ALL obligation-like
  sentences in the prompt: live ledger + distractor/superseded quotes),
  trained with CE at moments whose type is live; theta (null threshold)
  calibrated ONCE on calib as a score quantile so that inactive-type moments
  abstain (false-press gates), then frozen with tau.
Saves heads + thresholds + calibration report to results/qwen/t2-selector.pt.
"""
import ast
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from stencil import determinism  # noqa: F401
import torch
import torch.nn.functional as F
from tokenizers import Tokenizer

from stencil.qwen3 import Qwen3
from stencil.t2_runner import _oracle_moment, run_session, ledger_sentence_spans
from stencil.t2_sessions import SENT, SENT_UNSEEN_FMT, generate_t2, prompt_at

TRAIN = [12_650_000 + i for i in range(48)]
CALIB = [12_700_000 + i for i in range(24)]
CLASSES = ["none", "prefix", "doc", "hint"]
LAYERS = tuple(range(20, 28))
BETA = 2.0

tok = Tokenizer.from_file(str(ROOT / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
m = Qwen3()
m.load_state_dict(torch.load(ROOT / "models" / "qwen3-1.7b.pt", map_location="cpu"), strict=True)
m = m.to(torch.bfloat16).cuda().eval()

CAND_PATTERNS = {
    "prefix": [r"All function names must start with '(\w+)_'\.", r"Use the naming scheme (\w+)_\* for every function you define\."],
    "doc": [r"Every docstring must begin with the word '(\w+)'\."],
    "hint": [r"All function arguments must be type-hinted as (\w+)\."],
}


def candidate_spans(prompt_text, enc):
    """MUST-2: every obligation-like sentence, live or quoted."""
    cands = []  # (type, value, tok_span, char_start)
    for ty, pats in CAND_PATTERNS.items():
        for pat in pats:
            for match in re.finditer(pat, prompt_text):
                a, b = match.span()
                cols = [i for i, (x, y) in enumerate(enc.offsets) if x < b and y > a]
                if cols:
                    cands.append((ty, match.group(1), (cols[0], cols[-1] + 1), a))
    return cands


def gen_and_collect(sess, split, arm):
    """Run one arm over a session collecting (state, timing_label) and
    (state, candidates, address_label_or_None) at AST-grounded moments."""
    tim_X, tim_Y = [], []
    addr = []  # (state, cand_feats, label or None-for-abstain, live_type_active)
    for wt in sess.work_turns:
        ptxt = prompt_at(sess, wt, split)
        enc = tok.encode(ptxt)
        ids = enc.ids
        spans = ledger_sentence_spans(ptxt, sess, wt, split, tok)
        toks = torch.tensor([ids], device="cuda")
        outs, text = [], ""
        with torch.no_grad():
            for _ in range(120):
                ab = None
                if arm == "oracle" and spans:
                    key = _oracle_moment(text[-80:])
                    if key is not None and key in spans:
                        t = toks.shape[1]
                        bias = torch.zeros(t, t, device="cuda")
                        bias[-1:, spans[key][0]:spans[key][1]] = BETA
                        ab = {L: bias for L in LAYERS}
                nxt = int(m(toks, attn_bias=ab)[0, -1].argmax())
                outs.append(nxt)
                toks = torch.cat([toks, torch.tensor([[nxt]], device="cuda")], dim=1)
                text = tok.decode(outs)
                if "```" in text[-6:]:
                    break
        code = text.split("```")[0]
        # AST moments in generated code -> generation step indices
        labels = ast_moments(code, outs)
        full = ids + outs
        with torch.no_grad():
            h = m(torch.tensor([full], device="cuda"), return_hidden=20)[0].float().cpu()
        cands = candidate_spans(ptxt, enc)
        cand_feats = torch.stack([h[c[2][0]:c[2][1]].mean(dim=0) for c in cands]) if cands else None
        led = sess.ledger_at[wt]
        for i in range(len(outs)):
            state = h[len(ids) + i - 1]
            cls = labels.get(i, "none")
            tim_X.append(state)
            tim_Y.append(CLASSES.index(cls))
            if cls != "none" and cand_feats is not None:
                if cls in led:
                    tgt = next((j for j, c in enumerate(cands) if c[0] == cls and c[1] == led[cls]), None)
                    if tgt is not None:
                        addr.append((state, cand_feats, tgt, True))
                else:
                    addr.append((state, cand_feats, None, False))  # abstain case
    return tim_X, tim_Y, addr


def ast_moments(code, gen_ids):
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return {}
    fns = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    if not fns:
        return {}
    fn = fns[0]
    lines = code.split("\n")
    def char_of(lineno, col):
        return sum(len(ln) + 1 for ln in lines[: lineno - 1]) + col
    targets = []
    nc = code.find("def " + fn.name)
    if nc >= 0:
        targets.append((nc + 4, "prefix"))
    doc = ast.get_docstring(fn)
    if doc and doc.split() and isinstance(fn.body[0], ast.Expr):
        w = code.find(doc.split()[0], char_of(fn.body[0].lineno, fn.body[0].col_offset))
        if w >= 0:
            targets.append((w, "doc"))
    for a in fn.args.args:
        if a.annotation is not None:
            targets.append((char_of(a.annotation.lineno, a.annotation.col_offset), "hint"))
    offs, pos = [], 0
    for tid in gen_ids:
        piece = tok.decode([tid])
        offs.append((pos, pos + len(piece)))
        pos += len(piece)
    out = {}
    for c, cls in targets:
        for i, (a, b) in enumerate(offs):
            if a <= c < b:
                out[i] = cls
                break
    return out


print("collecting train rollouts (base + oracle)...", flush=True)
TX, TY, ADDR = [], [], []
for k, seed in enumerate(TRAIN):
    sess = generate_t2(seed, 20, "dev")
    for arm in ("base", "oracle"):
        tx, ty, ad = gen_and_collect(sess, "dev", arm)
        TX += tx; TY += ty; ADDR += ad
    if k % 12 == 0:
        print(f"  {k}/{len(TRAIN)} sessions", flush=True)
TX = torch.stack(TX); TY = torch.tensor(TY)
print(f"timing examples {len(TY)} (moments {(TY>0).sum().item()}), address examples {len(ADDR)} (abstain cases {sum(1 for a in ADDR if a[2] is None)})", flush=True)

g = torch.Generator().manual_seed(0)
head = torch.nn.Linear(2048, 4)
torch.nn.init.normal_(head.weight, std=0.02, generator=g); torch.nn.init.zeros_(head.bias)
w = torch.tensor([1.0, 20.0, 20.0, 20.0])
opt = torch.optim.Adam(head.parameters(), lr=1e-3)
for ep in range(30):
    perm = torch.randperm(len(TY), generator=g)
    for i in range(0, len(TY), 512):
        idx = perm[i:i+512]
        loss = F.cross_entropy(head(TX[idx]), TY[idx], weight=w)
        opt.zero_grad(); loss.backward(); opt.step()

Wq = torch.nn.Linear(2048, 64); Wk = torch.nn.Linear(2048, 64)
for lin in (Wq, Wk):
    torch.nn.init.normal_(lin.weight, std=0.02, generator=g); torch.nn.init.zeros_(lin.bias)
aopt = torch.optim.Adam(list(Wq.parameters()) + list(Wk.parameters()), lr=1e-3)
pos = [(s, cf, t) for s, cf, t, live in ADDR if t is not None]
for ep in range(60):
    tot = 0.0
    for s, cf, t in pos:
        logits = (Wq(s) @ Wk(cf).T) / 8.0
        loss = F.cross_entropy(logits[None], torch.tensor([t]))
        aopt.zero_grad(); loss.backward(); aopt.step()
        tot += float(loss.detach())
print(f"address train loss {tot/len(pos):.4f}", flush=True)

print("calibrating on calib split...", flush=True)
CX, CY, CADDR = [], [], []
for seed in CALIB:
    sess = generate_t2(seed, 20, "dev")
    tx, ty, ad = gen_and_collect(sess, "dev", "base")
    CX += tx; CY += ty; CADDR += ad
CX = torch.stack(CX); CY = torch.tensor(CY)
with torch.no_grad():
    probs = torch.softmax(head(CX), dim=-1)
    best = None
    for tau in [0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.98]:
        cls = probs[:, 1:].argmax(dim=-1) + 1
        conf = probs.gather(1, cls[:, None]).squeeze(1)
        pred = torch.where(conf > tau, cls, torch.zeros_like(cls))
        tp = ((pred > 0) & (pred == CY)).sum().item()
        fp = ((pred > 0) & (pred != CY)).sum().item()
        fn = ((pred == 0) & (CY > 0)).sum().item()
        prec = tp / (tp + fp) if tp + fp else 0
        rec = tp / (tp + fn) if tp + fn else 0
        if prec >= 0.95 and (best is None or rec > best[2]):
            best = (tau, prec, rec)
    assert best, "no tau reaches precision 0.95"
    TAU = best[0]
    # theta: max address score quantile separating live from abstain cases
    live_scores, abstain_scores = [], []
    for s, cf, t, live in CADDR:
        sc = float(((Wq(s) @ Wk(cf).T) / 8.0).max())
        (live_scores if live else abstain_scores).append(sc)
    theta_best = None
    import numpy as _np
    for q in [0.5, 0.6, 0.7, 0.8, 0.9, 0.95]:
        theta = float(_np.quantile(abstain_scores, q)) if abstain_scores else -1e9
        fpress = sum(1 for sc in abstain_scores if sc > theta)
        kept = sum(1 for sc in live_scores if sc > theta)
        prec_ok = fpress == 0
        if theta_best is None or (prec_ok and kept > theta_best[2]):
            if prec_ok or theta_best is None:
                theta_best = (theta, fpress, kept, q)
    THETA = theta_best[0]
    addr_acc = 0
    naddr = 0
    for s, cf, t, live in CADDR:
        if t is None:
            continue
        naddr += 1
        addr_acc += int(int(((Wq(s) @ Wk(cf).T) / 8.0).argmax()) == t)
print(f"FROZEN tau={TAU} (prec {best[1]:.3f} rec {best[2]:.3f}) theta={THETA:.3f} "
      f"(calib abstain false-press {theta_best[1]}/{len(abstain_scores)}, live kept {theta_best[2]}/{len(live_scores)}) "
      f"addr acc {addr_acc}/{naddr}", flush=True)
torch.save({"head": head.state_dict(), "Wq": Wq.state_dict(), "Wk": Wk.state_dict(),
            "tau": TAU, "theta": THETA,
            "calib": {"precision": best[1], "recall": best[2],
                      "abstain_false_press": theta_best[1], "n_abstain": len(abstain_scores),
                      "addr_acc": addr_acc / max(1, naddr)}},
           ROOT / "results" / "qwen" / "t2-selector.pt")
print("saved results/qwen/t2-selector.pt")
