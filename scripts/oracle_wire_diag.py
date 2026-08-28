# ruff: noqa: E501
"""Sol diagnostic 5: can ANY wire state make the trained osc model emit the
right beyond-window answer? Freezes everything; optimizes control_override."""
import sys

import torch
import torch.nn.functional as F

sys.path.insert(0, "/home/bmarti44/stencil-llm/src")
from stencil.gpt2 import GatedGPT2  # noqa: E402
from stencil.nl_task import BPE, batch  # noqa: E402

DEV = "cuda"
m = GatedGPT2("osc", window=64, seed_init=0, lora_rank=8)
sd = torch.load("/home/bmarti44/stencil-llm/models/gpt2-small.pt", map_location="cpu")
m.load_state_dict(sd, strict=False)
ck = torch.load("/home/bmarti44/stencil-llm/results/gpt2/osc-lora8-s0-ckpt.pt", map_location="cpu")
print("ckpt step", ck["step"])
m.load_state_dict(ck["pathway"], strict=False)
m.logit_bias = torch.nn.Parameter(ck["logit_bias"])
m = m.to(DEV).eval()
for p in m.parameters():
    p.requires_grad_(False)

bpe = BPE()
hits = tried = 0
i = 0
while tried < 8 and i < 40:
    seed = 5_000_000 + i
    i += 1
    toks, _, seqs = batch([seed], bpe=bpe)
    s = seqs[0]
    sel = None
    for p, slot in zip(s.query_positions, s.query_slots, strict=True):
        if p - s.rule_statement_pos[slot] > 756:
            sel = (p, slot)
            break
    if sel is None:
        continue
    qp, slot = sel
    tgt = torch.tensor([s.targets[qp]], device=DEV)
    tk = toks.to(DEV)
    ctl = m.control_states(tk).detach().clone()
    ctl.requires_grad_(True)
    opt = torch.optim.Adam([ctl], lr=0.05)
    for _ in range(150):
        out = m(tk, control_override=ctl) + m.logit_bias
        loss = F.cross_entropy(out[0, qp][None], tgt)
        opt.zero_grad()
        loss.backward()
        opt.step()
    with torch.no_grad():
        out = m(tk, control_override=ctl) + m.logit_bias
        ok = int(out[0, qp].argmax()) == int(tgt)
        rank = int((out[0, qp] > out[0, qp, tgt[0]]).sum()) + 1
    tried += 1
    hits += ok
    print(f"ex {tried}: {'HIT' if ok else 'miss'} final ce {float(loss):.3f} target rank {rank}", flush=True)
print(f"ORACLE-WIRE: {hits}/{tried} beyond-window answers reachable by SOME wire state")
