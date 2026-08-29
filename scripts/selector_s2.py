# ruff: noqa
"""S2 registered run: learned contentless selector (SELECTOR-PLAN Amendment 1).

One query-key scorer on frozen cached block-20 features; direct span-address
CE; hard argmax at eval feeding the S1-selected actuator (layers 20-27,
beta 2). Report address accuracy first, then the paired behavioral eval
(base / oracle / selector on the SAME n=128 validation sessions).
Gates: address accuracy reported; behavioral net closure
(sel_gained - sel_broken) / (orc_gained - orc_broken) >= 0.5.
"""
import json
import sys
from pathlib import Path

import torch
import torch.nn.functional as F

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from tokenizers import Tokenizer

from stencil.qwen3 import Qwen3
from stencil.qwen_task import FIELDS, generate_governance

TRAIN_SEEDS = list(range(11_400_000, 11_400_512))
VAL_SEEDS = list(range(11_500_000, 11_500_128))
LAYERS = tuple(range(20, 28))
BETA = 2.0

tok = Tokenizer.from_file(str(ROOT / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
m = Qwen3()
m.load_state_dict(torch.load(ROOT / "models" / "qwen3-1.7b.pt", map_location="cpu"), strict=True)
m = m.to(torch.bfloat16).cuda().eval()


def build(seed):
    s = generate_governance(seed)
    enc = tok.encode(s.text)
    ids = enc.ids
    spans_tok = {}
    for slot, (lo_c, hi_c) in s.ledger_spans.items():
        cols = [i for i, (a, b) in enumerate(enc.offsets) if a < hi_c and b > lo_c]
        assert cols, f"empty span for slot {slot}"
        spans_tok[slot] = (cols[0], cols[-1] + 1)
    row_start_char = s.text.rfind("Q: What is the " + s.field)
    row_start = next(i for i, (a, b) in enumerate(enc.offsets) if b > row_start_char)
    return s, ids, spans_tok, row_start, FIELDS.index(s.field)


def features(item):
    s, ids, spans_tok, row_start, target = item
    with torch.no_grad():
        h = m(torch.tensor([ids], device="cuda"), return_hidden=20)[0].float()
    q_feat = h[-1]  # final prompt token ("... is")
    keys = torch.stack([h[lo:hi].mean(dim=0) for slot, (lo, hi) in sorted(spans_tok.items())])
    slot_order = sorted(spans_tok)
    return q_feat.cpu(), keys.cpu(), slot_order.index(target)


print("caching features...", flush=True)
train_items = [build(sd) for sd in TRAIN_SEEDS]
val_items = [build(sd) for sd in VAL_SEEDS]
train_feats = [features(it) for it in train_items]
val_feats = [features(it) for it in val_items]

D_SEL = 64
g = torch.Generator().manual_seed(0)
Wq = torch.nn.Linear(2048, D_SEL)
Wk = torch.nn.Linear(2048, D_SEL)
for lin in (Wq, Wk):
    torch.nn.init.normal_(lin.weight, std=0.02, generator=g)
    torch.nn.init.zeros_(lin.bias)
opt = torch.optim.Adam(list(Wq.parameters()) + list(Wk.parameters()), lr=1e-3)
for epoch in range(200):
    tot = 0.0
    for qf, ks, tgt in train_feats:
        logits = (Wq(qf) @ Wk(ks).T) / (D_SEL ** 0.5)
        loss = F.cross_entropy(logits[None], torch.tensor([tgt]))
        opt.zero_grad(); loss.backward(); opt.step()
        tot += float(loss.detach())
    if epoch % 50 == 0:
        print(f"epoch {epoch} loss {tot/len(train_feats):.4f}", flush=True)

with torch.no_grad():
    addr_hits = sum(
        int((Wq(qf) @ Wk(ks).T).argmax()) == tgt for qf, ks, tgt in val_feats
    )
print(f"ADDRESS ACCURACY (val n={len(val_feats)}): {addr_hits}/{len(val_feats)} = {addr_hits/len(val_feats):.3f}", flush=True)


def gen(ids, bias_cfg=None, max_new=20):
    toks = torch.tensor([ids], device="cuda")
    outs = []
    for _ in range(max_new):
        ab = None
        if bias_cfg is not None:
            (c0, c1), row_start = bias_cfg
            t = toks.shape[1]
            bias = torch.zeros(t, t, device="cuda")
            bias[row_start:, c0:c1] = BETA
            ab = {L: bias for L in LAYERS}
        nxt = int(m(toks, attn_bias=ab)[0, -1].argmax())
        outs.append(nxt)
        if tok.decode([nxt]).endswith("\n"):
            break
        toks = torch.cat([toks, torch.tensor([[nxt]], device="cuda")], dim=1)
    return tok.decode(outs).strip().split("\n")[0].strip().rstrip(".")


base = orc = sel = 0
recs = []
with torch.no_grad():
    for it, (qf, ks, tgt) in zip(val_items, val_feats, strict=True):
        s, ids, spans_tok, row_start, target = it
        slot_order = sorted(spans_tok)
        b_out = gen(ids) == s.value
        o_out = gen(ids, (spans_tok[target], row_start)) == s.value
        pred_slot = slot_order[int((Wq(qf) @ Wk(ks).T).argmax())]
        s_out = gen(ids, (spans_tok[pred_slot], row_start)) == s.value
        base += b_out; orc += o_out; sel += s_out
        recs.append({"seed": TRAIN_SEEDS and None, "base": b_out, "oracle": o_out, "selector": s_out,
                     "addr_correct": pred_slot == target})
n = len(val_items)
orc_net = orc - base
sel_net = sel - base
closure = sel_net / orc_net if orc_net else float("nan")
print(f"PAIRED (n={n}): base {base}/{n} oracle {orc}/{n} selector {sel}/{n}")
print(f"net closure (sel-base)/(orc-base) = {closure:.2f} (gate >= 0.5)")
out = ROOT / "results" / "qwen" / "s2-selector.json"
out.write_text(json.dumps({"train_n": len(TRAIN_SEEDS), "val_n": n,
                           "address_acc": addr_hits / n, "base": base, "oracle": orc,
                           "selector": sel, "closure": closure, "records": recs}, indent=1))
print(f"evidence -> {out}")
