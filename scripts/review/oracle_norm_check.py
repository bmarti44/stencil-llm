# ruff: noqa
# Gate-1 caveat check: oracle_inject_diag optimizes code_override AFTER _norm,
# so its norm is unconstrained. Measure final RMS, and rerun with a unit-RMS
# projection each step. 4 examples, osc-v6 ckpt, same protocol otherwise.
import sys

import torch
import torch.nn.functional as F

sys.path.insert(0, "/home/bmarti44/stencil-llm/src")
from stencil.gpt2 import GatedGPT2  # noqa: E402
from stencil.nl_task import BPE, batch  # noqa: E402

DEV = "cuda" if torch.cuda.is_available() else "cpu"
print("device", DEV)
m = GatedGPT2("osc", window=64, seed_init=0, lora_rank=8)
m.load_state_dict(torch.load("/home/bmarti44/stencil-llm/models/gpt2-small.pt", map_location="cpu"), strict=False)
ck = torch.load("/home/bmarti44/stencil-llm/results/gpt2/osc-v6-s0-ckpt.pt", map_location="cpu")
m.load_state_dict(ck["pathway"], strict=False)
m.logit_bias = torch.nn.Parameter(ck["logit_bias"])
m = m.to(DEV).eval()
for p in m.parameters():
    p.requires_grad_(False)

bpe = BPE()


def run(project: bool):
    hits = tried = 0
    i = 0
    while tried < 4 and i < 40:
        seed = 8_000_000 + i
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
        qp, _ = sel
        tgt = torch.tensor([s.targets[qp]], device=DEV)
        tk = toks.to(DEV)
        code = m.injection_code(tk).detach().clone()
        code.requires_grad_(True)
        opt = torch.optim.Adam([code], lr=0.05)
        for _ in range(150):
            out = m(tk, code_override=code) + m.logit_bias
            loss = F.cross_entropy(out[0, qp][None], tgt)
            opt.zero_grad(); loss.backward(); opt.step()
            if project:
                with torch.no_grad():
                    code.data = code.data * torch.rsqrt(code.data.pow(2).mean(-1, keepdim=True) + 1e-8)
        with torch.no_grad():
            out = m(tk, code_override=code) + m.logit_bias
            ok = int(out[0, qp].argmax()) == int(tgt)
            rank = int((out[0, qp] > out[0, qp, tgt[0]]).sum()) + 1
            rms_q = float(code[0, qp].pow(2).mean().sqrt())
            rms_all = float(code.pow(2).mean().sqrt())
        tried += 1; hits += ok
        print(f"  ex {tried}: {'HIT' if ok else 'miss'} ce {float(loss):.3f} rank {rank} codeRMS@q {rms_q:.2f} codeRMS(all) {rms_all:.2f}", flush=True)
    print(f"{'UNIT-RMS' if project else 'UNCONSTRAINED'}: {hits}/{tried}")


print("unconstrained (as gate 1 ran):")
run(False)
print("unit-RMS projected (what a real writer through _norm can emit):")
run(True)
