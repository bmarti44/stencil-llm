"""READ-TIME RETRIEVAL BY THE MODEL'S OWN ATTENTION, on the 20 H1' sessions, at the finder's budget.

Store everything; at the new turn, rank archived sentence spans by the attention the current query position (the
last prompt token, the one that starts generation) pays to them (trunk attn_probe, layers 20-27, mean over heads),
normalized per column. Pin the top spans up to the H1'-recorded finder budget, evict the rest, echo nothing, score
checker outcomes exactly as H1'. Controls: exact-column null at the same count; H1' recorded finder (37) / control (18).
Also reports constraint-token coverage of the ranking (vs BM25 0.37 / random 0.13 from the CPU check).
"""
import glob, json, re, sys, time
from pathlib import Path

ROOT = Path("/home/bmarti44/stencil-llm")
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "scripts"))
import torch  # noqa: E402
import g0_oracle as G  # noqa: E402
import ledger_kv_probe as P  # noqa: E402
from stencil.qwen3 import KVCache  # noqa: E402
from stencil.causal_moments import score_row_constraints  # noqa: E402

model, tok = G.load_model()
corpus = {r["key"]: r for r in (json.loads(l) for l in open(ROOT / "data/b3/mt-train-300.jsonl"))}
recs = [json.load(open(p)) for p in sorted(glob.glob(str(ROOT / "results/qwen/ledger-kv-probe-h1p/session-*.json")))]


def sentence_spans(enc, context, lo, hi):
    c0, c1 = enc.offsets[lo][0], enc.offsets[hi - 1][1]
    out = []
    for m in re.finditer(r"[^.!?\n]+[.!?]?", context[c0:c1]):
        a, b = c0 + m.start(), c0 + m.end()
        if len(re.findall(r"[A-Za-z]", m.group(0))) < 2:
            continue
        ts = P._token_span(enc, a, b)
        if ts:
            s, e = max(lo, ts[0]), min(hi, ts[1])
            if e > s:
                out.append((s, e))
    return out


def overlap(a, b):
    return max(0, min(a[1], b[1]) - max(a[0], b[0]))


tot = {"finder": 0, "finder_control": 0, "ATTN": 0, "ATTN_control": 0, "n": 0}
cov = {"attn_per_col": [], "attn_mass": []}
rows = []; t0 = time.time()
for r in recs:
    ids = r["context_token_ids"]; lo, hi = r["evict_range"]
    context = tok.decode(ids, skip_special_tokens=False); enc = tok.encode(context); assert enc.ids == ids
    spans = sentence_spans(enc, context, lo, hi)
    T = len(ids)
    mask = torch.zeros(len(spans), T, dtype=torch.bool, device="cuda")
    for i, (s, e) in enumerate(spans):
        mask[i, s:e] = True
    sink = {}
    cache = KVCache()
    with torch.no_grad():
        model(torch.tensor([ids], device="cuda"), cache=cache, attn_probe=(mask, sink))
    layers = sorted(sink)
    mass = [sum(sink[L][i] for L in layers) / len(layers) for i in range(len(spans))]
    per_col = [m / (e - s) for m, (s, e) in zip(mass, spans)]
    budget = r["arms"]["pinned"]["pinned_cols"]; keepc = [tuple(k) for k in r["keep"]]; Bk = sum(e - s for s, e in keepc)

    def top_to_budget(scores):
        keep, got = [], 0
        for i in sorted(range(len(spans)), key=lambda i: -scores[i]):
            s, e = spans[i]
            if got + (e - s) >= budget:
                keep.append((s, s + (budget - got))); got = budget; break
            keep.append((s, e)); got += e - s
        return sorted(keep)

    for name, sc in (("attn_per_col", per_col), ("attn_mass", mass)):
        k = top_to_budget(sc)
        cov[name].append(sum(sum(overlap(c, s) for s in k) for c in keepc) / Bk)
    keep = top_to_budget(per_col)
    n_pin = len({i for a, b in keep for i in range(a, b)})
    control = P.matched_control_spans(keep, (lo, hi))
    sess = corpus[r["key"]]; last = sess["turns"][-1]
    row = {"key": int(sess["key"]) * 10 + r["n_turns"], "instruction_id_list": last["instruction_id_list"], "kwargs": last["kwargs"]}
    n_aged = r["n_aged"]; out = {}
    for arm, ck in (("pinned", ()), ("pinned_control", control)):
        g = P.run_arm(model, tok, ids, arm, keep, (lo, hi), 0.0, 512, 300.0, control_keep=ck)
        sc = list(score_row_constraints(row, g["text"]))
        out[arm] = {"aged_pass": sum(sc[:n_aged]), "n": g["n"], "truncated": g.get("truncated"), "degenerate": P.is_degenerate(g), "pinned_cols": g.get("pinned_cols")}
    h = {a: r["arms"][a]["aged_pass"] for a in ("full", "evicted", "pinned", "pinned_control")}
    rows.append({"session": r["session"], "n_aged": n_aged, "budget": budget, "n_pin": n_pin, "n_spans": len(spans), "keep": keep,
                 "coverage": {k: v[-1] for k, v in cov.items()}, "h1p": h, "ATTN": out})
    tot["n"] += n_aged; tot["finder"] += h["pinned"]; tot["finder_control"] += h["pinned_control"]; tot["ATTN"] += out["pinned"]["aged_pass"]; tot["ATTN_control"] += out["pinned_control"]["aged_pass"]
    print(f"s{r['session']:02d} aged={n_aged} budget={budget} pinned={n_pin} spans={len(spans)} cov(per_col)={cov['attn_per_col'][-1]:.2f} cov(mass)={cov['attn_mass'][-1]:.2f} | finder={h['pinned']} finder_ctrl={h['pinned_control']} | ATTN={out['pinned']['aged_pass']} (trunc={out['pinned']['truncated']}, degen={out['pinned']['degenerate']}) ATTN_ctrl={out['pinned_control']['aged_pass']}", flush=True)
print(f"elapsed {time.time()-t0:.0f}s")
print("COVERAGE at finder budget: " + " ".join(f"{k}={sum(v)/len(v):.3f}" for k, v in cov.items()) + "  (BM25 0.369, random 0.133, recency 0.022)")
print("TOTALS:", json.dumps(tot))
json.dump(rows, open(Path(__file__).with_name("attn_retrieval_rows.json"), "w"), indent=1)
