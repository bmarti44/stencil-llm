# Freeze v7 controller; train a FRESH per-slot head on statement-end codes.
# If it learns what ridge finds, the r-ce-at-chance is an optimization artifact.
import sys

import torch
import torch.nn.functional as F

sys.path.insert(0, "/home/bmarti44/stencil-llm/src")
from stencil.gpt2 import GatedGPT2  # noqa: E402
from stencil.nl_task import ANSWER_WORDS, BPE, generate  # noqa: E402

torch.set_grad_enabled(False)
ROOT = "/home/bmarti44/stencil-llm"
m = GatedGPT2("osc", window=64, seed_init=0, lora_rank=8, hard_salience=True)
m.load_state_dict(torch.load(f"{ROOT}/models/gpt2-small.pt", map_location="cpu"), strict=False)
ck = torch.load(f"{ROOT}/results/gpt2/osc-v7-s0-ckpt.pt", map_location="cpu")
m.load_state_dict(ck["pathway"], strict=False)
m.eval()
bpe = BPE()

X, Y, S = [], [], []
for i in range(400):
    seq = generate(6_000_000 + i, family="near", bpe=bpe)
    toks = torch.tensor([seq.tokens])
    code = m.injection_code(toks)[0]
    for p, s, ans in seq.rule_events:
        X.append(code[p].float()); Y.append(ANSWER_WORDS.index(ans)); S.append(s)
X = torch.stack(X); Y = torch.tensor(Y); S = torch.tensor(S)
k = len(Y) * 3 // 4

# signal scale: per-slot between-class spread of the unit-RMS code
for s in range(4):
    sel = S == s
    Xs, Ys = X[sel], Y[sel]
    mu = torch.stack([Xs[Ys == c].mean(0) for c in range(16) if (Ys == c).any()])
    between = float((mu - mu.mean(0)).pow(2).mean().sqrt())
    within = float(torch.cat([Xs[Ys == c] - Xs[Ys == c].mean(0) for c in range(16) if (Ys == c).sum() > 1]).pow(2).mean().sqrt())
    print(f"slot {s}: between-class RMS {between:.5f} within-class RMS {within:.5f} code RMS {float(Xs.pow(2).mean().sqrt()):.3f}")

torch.set_grad_enabled(True)
for tag, wd, lr, steps in (("as-trained wd=0.01 lr=3e-4", 0.01, 3e-4, 500),
                            ("no-wd lr=1e-2", 0.0, 1e-2, 3000)):
    torch.manual_seed(0)
    head = torch.nn.Linear(128, 64)
    opt = torch.optim.AdamW(head.parameters(), lr=lr, weight_decay=wd)
    for t in range(steps):
        idx = torch.randperm(k)[:96]
        lg = head(X[idx]).view(-1, 4, 16)[torch.arange(96), S[idx]]
        loss = F.cross_entropy(lg, Y[idx])
        opt.zero_grad(); loss.backward(); opt.step()
    with torch.no_grad():
        lg = head(X[k:]).view(-1, 4, 16)[torch.arange(len(Y) - k), S[k:]]
        ce = float(F.cross_entropy(lg, Y[k:]))
        acc = float((lg.argmax(-1) == Y[k:]).float().mean())
        per = [float((lg[S[k:] == s].argmax(-1) == Y[k:][S[k:] == s]).float().mean()) for s in range(4)]
        wn = float(head.weight.norm())
    print(f"[{tag}] held-out r-ce {ce:.3f} acc {acc:.3f} per-slot acc {[round(p,2) for p in per]} |W| {wn:.1f}")
