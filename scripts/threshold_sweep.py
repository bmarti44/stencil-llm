# ruff: noqa
"""Commit-threshold calibration sweep on the noisy-teacher checkpoint (Exp B).
Artifact for the report's precision-recovery claim."""
import sys
import torch
sys.path.insert(0, "/home/bmarti44/stencil-llm/src")
sys.path.insert(0, "/home/bmarti44/stencil-llm/scripts")
import run_gpt2_arms as R
from stencil.nl_task import BPE, batch

DEV = R.DEV
m = R.build("cache", 0)
ck = torch.load("results/gpt2/cache-v8noise-s0-ckpt.pt", map_location="cpu")
m.load_state_dict(ck["pathway"], strict=False)
m = m.to(DEV).eval()
bpe = BPE()
stats = {th: [0, 0, 0] for th in (0.5, 0.6, 0.7, 0.8, 0.9, 0.95)}
with torch.no_grad():
    for i in range(48):
        toks, _, seqs = batch([R.VAL_SPACE + 850_000 + i], bpe=bpe)
        sal_m, com_m, labels, _ = R.cache_masks(seqs, toks.shape[1], DEV)
        x = m.wte(toks.to(DEV)) + m.wpe(torch.arange(toks.shape[1], device=DEV))
        mask = m._mask(toks.shape[1], DEV)
        for idx in range(m.INJ_LAYERS[0]):
            x = m.blocks[idx](x, mask, None, m.lora[idx], None)
        cl = torch.sigmoid(m.cache.commit(x).squeeze(-1))
        for th, st in stats.items():
            pred = cl > th
            st[0] += int((pred & com_m).sum())
            st[1] += int((pred & ~com_m).sum())
            st[2] += int((~pred & com_m).sum())
print("ckpt step", ck["step"])
for th, (tp, fp, fn) in stats.items():
    p = tp / (tp + fp) if tp + fp else 0
    r = tp / (tp + fn) if tp + fn else 0
    print(f"threshold {th}: precision {p:.3f} recall {r:.3f}")
