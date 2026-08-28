# ruff: noqa
# Read-only analysis of osc-v7-s0 checkpoint: gate-vs-mask, probes, per-slot r-ce.
import json
import sys

import torch
import torch.nn.functional as F

sys.path.insert(0, "/home/bmarti44/stencil-llm/src")
from stencil.gpt2 import GatedGPT2  # noqa: E402
from stencil.nl_task import ANSWER_WORDS, BPE, generate  # noqa: E402

torch.set_grad_enabled(False)
DEV = "cpu"
ROOT = "/home/bmarti44/stencil-llm"

m = GatedGPT2("osc", window=64, seed_init=0, lora_rank=8, hard_salience=True)
sd = torch.load(f"{ROOT}/models/gpt2-small.pt", map_location="cpu")
m.load_state_dict(sd, strict=False)
ck = torch.load(f"{ROOT}/results/gpt2/osc-v7-s0-ckpt.pt", map_location="cpu")
m.load_state_dict(ck["pathway"], strict=False)
m.eval()
print("ckpt step", ck["step"])
aux = torch.nn.Linear(128, 4 * 16)
aux.load_state_dict(ck["aux_head"])

bpe = BPE()
# decoder for token inspection
dec = {v: k for k, v in bpe.encoder.items()}
byte_dec = {c: b for b, c in bpe.byte_enc.items()}


def detok(tid: int) -> str:
    s = dec[tid]
    return bytes(byte_dec[ch] for ch in s).decode("utf-8", errors="replace")


RULE_SPAN = 16  # cue_mask_diag's mask width

def analyze(family: str, n: int, seed0: int):
    print(f"\n===== family={family} n={n} =====")
    open_out, tot_out, closed_in, tot_in = 0, 0, 0, 0
    from collections import Counter
    leak = Counter()
    # forcing-mass ratio ahead of last statement end
    mass_rule, mass_leak = 0.0, 0.0
    # probe datasets
    Xq = {c: {s: [] for s in range(4)} for c in ("gate", "mask")}
    Yq = {c: {s: [] for s in range(4)} for c in ("gate", "mask")}
    Xe = {c: {s: [] for s in range(4)} for c in ("gate", "mask")}
    Ye = {c: {s: [] for s in range(4)} for c in ("gate", "mask")}
    # per-slot r-ce with the trained aux head (trained-gate condition)
    ce_sum = {s: 0.0 for s in range(4)}
    hit = {s: 0 for s in range(4)}
    cnt = {s: 0 for s in range(4)}
    for i in range(n):
        seq = generate(seed0 + i, family=family, bpe=bpe)
        toks = torch.tensor([seq.tokens])
        emb = m.wte(toks)
        sprob = torch.sigmoid(m.salience(emb)).squeeze(-1).squeeze(0)
        hard = (sprob > 0.5).float()
        span_mask = torch.zeros(len(seq.tokens), dtype=torch.bool)
        for lo, hi in seq.rule_spans:
            span_mask[lo:hi] = True
        open_out += int((hard.bool() & ~span_mask).sum())
        tot_out += int((~span_mask).sum())
        closed_in += int((~hard.bool() & span_mask).sum())
        tot_in += int(span_mask.sum())
        for p in torch.nonzero(hard.bool() & ~span_mask).flatten().tolist():
            leak[detok(seq.tokens[p])] += 1
        # forcing mass up to the LAST rule event position
        last_ev = max(p for p, _, _ in seq.rule_events)
        en = emb[0].norm(dim=-1)
        upto = torch.arange(len(seq.tokens)) <= last_ev
        mass_rule += float((en * hard * span_mask.float() * upto.float()).sum())
        mass_leak += float((en * hard * (~span_mask).float() * upto.float()).sum())
        # condition 1: trained hard gate (exactly the training forward)
        code_gate = m.injection_code(toks)[0]
        # condition 2: oracle cue mask (exact cue_mask_diag condition)
        keep = torch.zeros(len(seq.tokens))
        for s in range(4):
            p0 = seq.rule_statement_pos[s]
            keep[p0 : p0 + RULE_SPAN] = 1.0
        emb_m = m.wte(toks) * keep[None, :, None]
        code_mask = m._norm(m._norm(m.controller(emb_m)))[0]
        for p, s, ans in zip(seq.query_positions, seq.query_slots, seq.active_answer, strict=True):
            y = ANSWER_WORDS.index(ans)
            Xq["gate"][s].append(code_gate[p].float()); Yq["gate"][s].append(y)
            Xq["mask"][s].append(code_mask[p].float()); Yq["mask"][s].append(y)
        for p, s, ans in seq.rule_events:
            y = ANSWER_WORDS.index(ans)
            Xe["gate"][s].append(code_gate[p].float()); Ye["gate"][s].append(y)
            Xe["mask"][s].append(code_mask[p].float()); Ye["mask"][s].append(y)
            lg = aux(code_gate[p]).view(4, 16)[s]
            ce_sum[s] += float(F.cross_entropy(lg[None], torch.tensor([y])))
            hit[s] += int(lg.argmax() == y)
            cnt[s] += 1
    print(f"gate OPEN outside rule_spans: {open_out}/{tot_out} = {open_out/tot_out:.4f}")
    print(f"gate CLOSED inside rule_spans: {closed_in}/{tot_in} = {closed_in/tot_in:.4f}")
    print("top leaked tokens:", leak.most_common(15))
    print(f"forcing-mass up to last stmt end: rule {mass_rule:.0f} leak {mass_leak:.0f} ratio leak/rule {mass_leak/max(mass_rule,1e-9):.3f}")
    print(f"per-slot r-ce (aux head @ stmt ends, trained gate): "
          + " ".join(f"s{s}:{ce_sum[s]/max(cnt[s],1):.3f}(acc {hit[s]/max(cnt[s],1):.2f},n={cnt[s]})" for s in range(4)))

    def ridge(xs, ys):
        if len(ys) < 40:
            return None
        X = torch.stack(xs); y = torch.tensor(ys)
        k = len(ys) * 3 // 4
        Y = torch.zeros(k, 16); Y[torch.arange(k), y[:k]] = 1
        W = torch.linalg.solve(X[:k].T @ X[:k] + 1e-3 * torch.eye(X.shape[1]), X[:k].T @ Y)
        return round(float((torch.argmax(X[k:] @ W, 1) == y[k:]).float().mean()), 3)

    for cond in ("gate", "mask"):
        print(f"ridge probe [{cond}] @ query pos: ", [ridge(Xq[cond][s], Yq[cond][s]) for s in range(4)],
              " @ stmt end: ", [ridge(Xe[cond][s], Ye[cond][s]) for s in range(4)])


analyze("near", 400, 6_000_000)
analyze("train", 200, 6_500_000)
