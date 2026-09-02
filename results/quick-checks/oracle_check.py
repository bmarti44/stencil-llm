"""Quick GPU validity check of the counterfactual oracle on the 20 H1' sessions (known needed spans).

Per session: prefill the context; reference = the FULL arm's own generated tokens (first 96); for each constraint
span (keep) and each exact-column control span (control_keep): evict only that span, teacher-force the reference.
utility = NLL_evicted - NLL_full. Readout: AUROC(keep > control) and per-session paired difference.
Uses the pilot's own helpers (scripts/g0_oracle.py) so the measurement is the same code path.
"""
import glob, json, sys, time
from pathlib import Path

ROOT = Path("/home/bmarti44/stencil-llm")
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "scripts"))
import torch  # noqa: E402
import g0_oracle as G  # noqa: E402
from stencil.qwen3 import KVCache  # noqa: E402

model, tok = G.load_model()

def tf_tokens(base_cache, first_logits, ref, drop=()):
    import torch.nn.functional as F
    cache = G.clone_cache(base_cache)
    for lo, hi in sorted(drop, reverse=True):
        cache.evict(lo, hi)
    losses, top = [], []
    logits = first_logits
    with torch.no_grad():
        for i, tgt in enumerate(ref):
            row = logits[0, -1].float()
            losses.append(float(F.cross_entropy(row[None], torch.tensor([tgt], device=row.device))))
            top.append(int(row.argmax()))
            if i + 1 < len(ref):
                logits = model(torch.tensor([[tgt]], device="cuda"), cache=cache)
    return losses, top

recs = [json.load(open(p)) for p in sorted(glob.glob(str(ROOT / "results/qwen/ledger-kv-probe-h1p/session-*.json")))]
rows = []; t0 = time.time()
for r in recs:
    ids = r["context_token_ids"]; ref = r["arms"]["full"]["generated_token_ids"][:96]
    if len(ref) < 8:
        continue
    cache = KVCache()
    with torch.no_grad():
        logits = model(torch.tensor([ids], device="cuda"), cache=cache)
    bl, btop = tf_tokens(cache, logits, ref); base = sum(bl)/len(bl)
    out = {"keep": [], "control": []}
    for kind, spans in (("keep", r["keep"]), ("control", r["control_keep"])):
        for a, b in spans:
            ll, top = tf_tokens(cache, logits, ref, [(a, b)])
            d = [x - y for x, y in zip(ll, bl)]
            u = sum(d) / len(d); out[kind].append(round(u, 4))
            rows.append({"session": r["session"], "kind": kind, "span": [a, b], "n": b - a, "utility": u,
                         "max_delta": max(d), "sum_pos": sum(x for x in d if x > 0), "top3": sum(sorted(d)[-3:]),
                         "flips": sum(int(x != y) for x, y in zip(top, btop)), "flip_from_correct": sum(int(x != y and y == z) for x, y, z in zip(top, btop, ref))})
    print(f"s{r['session']:02d} base {base:.3f} keep {out['keep']} control {out['control']}", flush=True)
print(f"elapsed {time.time()-t0:.0f}s, {len(rows)} evictions")
keep = [x["utility"] for x in rows if x["kind"] == "keep"]; ctrl = [x["utility"] for x in rows if x["kind"] == "control"]
auroc = sum((k > c) + 0.5 * (k == c) for k in keep for c in ctrl) / (len(keep) * len(ctrl))
print(f"keep n={len(keep)} mean {sum(keep)/len(keep):.4f} median {sorted(keep)[len(keep)//2]:.4f} | control n={len(ctrl)} mean {sum(ctrl)/len(ctrl):.4f} median {sorted(ctrl)[len(ctrl)//2]:.4f} | AUROC(keep>control) {auroc:.3f}")
per = {}
for x in rows:
    per.setdefault(x["session"], {"keep": [], "control": []})[x["kind"]].append(x["utility"])
d = [sum(v["keep"]) / len(v["keep"]) - sum(v["control"]) / len(v["control"]) for v in per.values() if v["keep"] and v["control"]]
print(f"per-session paired (mean keep - mean control): mean {sum(d)/len(d):.4f}, positive in {sum(x>0 for x in d)}/{len(d)} sessions")
# per-token-of-span utility (controls are length-matched in aggregate but not per span)
kt = [x["utility"] / x["n"] for x in rows if x["kind"] == "keep"]; ct = [x["utility"] / x["n"] for x in rows if x["kind"] == "control"]
auroc_t = sum((k > c) + 0.5 * (k == c) for k in kt for c in ct) / (len(kt) * len(ct))
print(f"per-token utility AUROC(keep>control) {auroc_t:.3f}")
for m in ("max_delta", "sum_pos", "top3", "flips", "flip_from_correct"):
    K = [x[m] for x in rows if x["kind"] == "keep"]; C = [x[m] for x in rows if x["kind"] == "control"]
    au = sum((k > c) + 0.5 * (k == c) for k in K for c in C) / (len(K) * len(C))
    print(f"{m:18s} keep mean {sum(K)/len(K):.4f} control mean {sum(C)/len(C):.4f} AUROC {au:.3f}")
json.dump(rows, open(Path(__file__).with_name("oracle_check_rows.json"), "w"))
