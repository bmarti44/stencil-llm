"""Diagnose the failed bitwise test: one-shot vs two-stage prefill (full arm, no eviction) on the real trunk,
in bf16 and in fp32, on a real probe context. Reports max |delta| logit, max relative delta, and top-1 agreement
over all positions of the second stage. If fp32 agrees to ~1e-4 the bf16 gap is kernel noise; else it is a bug."""
import glob, json, sys
from pathlib import Path
ROOT = Path("/home/bmarti44/stencil-llm")
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "scripts"))
import torch
from stencil.qwen3 import Qwen3, KVCache
import stencil.qwen3 as Q

rec = json.load(open(sorted(glob.glob(str(ROOT / "results/qwen/ledger-kv-probe-h1p/session-*.json")))[0]))
ids = rec["context_token_ids"]; lo, hi = rec["evict_range"]; split = hi
print("context", len(ids), "split at", split)
sd = torch.load(ROOT / "models/qwen3-1.7b.pt", map_location="cpu", weights_only=True)
for dtype in (torch.bfloat16, torch.float32):
    m = Qwen3(); m.load_state_dict(sd, strict=True); m = m.to(dtype).cuda().eval()
    x = torch.tensor([ids], device="cuda")
    with torch.no_grad():
        c1 = KVCache(); one = m(x, cache=c1)
        c2 = KVCache(); m(x[:, :split], cache=c2); two = m(x[:, split:], cache=c2)
    a = one[0, split:].float(); b = two[0].float()
    d = (a - b).abs(); rel = d / a.abs().clamp(min=1e-3)
    top = (a.argmax(-1) == b.argmax(-1)).float().mean()
    print(f"{str(dtype):16s} max|d| {d.max():.5f}  mean|d| {d.mean():.6f}  max rel {rel.max():.5f}  top-1 agreement {top:.4f}  last-pos max|d| {d[-1].max():.5f}")
    # bf16 noise floor: one-shot in two different batch shapes (pad a dummy row)
    if dtype == torch.bfloat16:
        with torch.no_grad():
            c3 = KVCache(); one_b = m(torch.cat([x, x], 0), cache=c3)[0]
        d2 = (one[0].float() - one_b.float()).abs()
        print(f"{'bf16 noise floor':16s} max|d| {d2.max():.5f} (same input, batch 1 vs batch 2)")
    del m; torch.cuda.empty_cache()
