"""Keep-one-in oracle check on the 20 H1' sessions (deployment-matched marginal retention value).

Leave-one-out failed (AUROC 0.49): prior compliant assistant turns make each constraint sentence redundant, so
evicting it alone changes nothing. The ledger's real question is: given the evictable range IS evicted, which
spans are worth keeping? utility_keepin(s) = NLL(evict all of evict_range) - NLL(evict all except s).
Reference = the FULL arm's own greedy output (first 96 tokens). Compare keep (constraint) vs control spans.
"""
import glob, json, sys, time
from pathlib import Path

ROOT = Path("/home/bmarti44/stencil-llm")
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "scripts"))
import torch  # noqa: E402
import g0_oracle as G  # noqa: E402
from stencil.qwen3 import KVCache  # noqa: E402

model, tok = G.load_model()


def tf_tokens(base_cache, first_logits, ref, drop_range, keep=()):
    import torch.nn.functional as F
    cache = G.clone_cache(base_cache)
    cache.evict(drop_range[0], drop_range[1], keep=keep)
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
    ids = r["context_token_ids"]; ref = r["arms"]["full"]["generated_token_ids"][:96]; ev = tuple(r["evict_range"])
    if len(ref) < 8:
        continue
    cache = KVCache()
    with torch.no_grad():
        logits = model(torch.tensor([ids], device="cuda"), cache=cache)
    full_l, _ = tf_tokens(cache, logits, ref, (0, 0))  # nothing evicted
    all_l, all_top = tf_tokens(cache, logits, ref, ev)
    gap = sum(all_l) / len(all_l) - sum(full_l) / len(full_l)
    out = {"keep": [], "control": []}
    for kind, spans in (("keep", r["keep"]), ("control", r["control_keep"])):
        for a, b in spans:
            ll, top = tf_tokens(cache, logits, ref, ev, keep=[(a, b)])
            d = [x - y for x, y in zip(all_l, ll)]  # positive = keeping s lowers loss
            u = sum(d) / len(d); out[kind].append(round(u, 4))
            rows.append({"session": r["session"], "kind": kind, "span": [a, b], "n": b - a, "utility": u,
                         "frac_of_gap": (u / gap if gap > 1e-6 else 0.0), "top3": sum(sorted(d)[-3:]),
                         "flips_back": sum(int(x != y and x == z) for x, y, z in zip(top, all_top, ref))})
    print(f"s{r['session']:02d} gap(all-evicted minus full) {gap:.3f} keep {out['keep']} control {out['control']}", flush=True)
print(f"elapsed {time.time()-t0:.0f}s, {len(rows)} evictions")
for m in ("utility", "frac_of_gap", "top3", "flips_back"):
    K = [x[m] for x in rows if x["kind"] == "keep"]; C = [x[m] for x in rows if x["kind"] == "control"]
    au = sum((k > c) + 0.5 * (k == c) for k in K for c in C) / (len(K) * len(C))
    print(f"{m:12s} keep mean {sum(K)/len(K):.4f} control mean {sum(C)/len(C):.4f} AUROC(keep>control) {au:.3f}")
per = {}
for x in rows:
    per.setdefault(x["session"], {"keep": [], "control": []})[x["kind"]].append(x["utility"])
d = [sum(v["keep"]) / len(v["keep"]) - sum(v["control"]) / len(v["control"]) for v in per.values() if v["keep"] and v["control"]]
print(f"per-session paired (mean keep - mean control): mean {sum(d)/len(d):.4f}, positive in {sum(x>0 for x in d)}/{len(d)} sessions")
json.dump(rows, open(Path(__file__).with_name("oracle_check_keepin_rows.json"), "w"))
