"""THE TRAINED GENERIC CLASSIFIER AS THE SELECTOR, on the 20 H1' sessions.
Sentences of each prior user turn are scored by the classifier (rule/fact/none); spans with P(rule)+P(fact) above a
threshold are the focus set, ranked by that probability; arms: pinned (all selected), pinned_echo, and BUDGET-MATCHED
pinned/pinned_echo (top spans by probability clipped to the finder's per-session pin count) + exact-column controls
computed AFTER the echo clamp (sol QC10#2). Same run_arm/scoring path as H1'.
"""
import glob, json, os, re, sys, time
from pathlib import Path

ROOT = Path("/home/bmarti44/stencil-llm")
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "scripts"))
import torch  # noqa: E402
import g0_oracle as G  # noqa: E402
import ledger_kv_probe as P  # noqa: E402
from stencil.causal_moments import score_row_constraints  # noqa: E402

THR = float(os.environ.get("CLF_THR", "0.5"))
model, tok = G.load_model()
SCORES = json.load(open(Path(__file__).with_name("clf_scores.json")))  # precomputed on CPU (system python has transformers)

corpus = {r["key"]: r for r in (json.loads(l) for l in open(ROOT / "data/b3/mt-train-300.jsonl"))}
recs = [json.load(open(p)) for p in sorted(glob.glob(str(ROOT / "results/qwen/ledger-kv-probe-h1p/session-*.json")))]


def overlap(a, b):
    return max(0, min(a[1], b[1]) - max(a[0], b[0]))


def clamp(context, aged, keep):
    while aged:
        try:
            P.echo_context(tok, context, aged); return aged, keep
        except ValueError:
            bad = None
            for a in aged:
                try:
                    P.echo_context(tok, context, [a])
                except ValueError:
                    bad = a; break
            if bad is None:
                raise
            aged = [a for a in aged if a is not bad]; keep = [k for k in keep if k != tuple(bad["span"])]
    return aged, keep


ARMS = ("CLF_pinned", "CLF_pinned_echo", "CLF_control", "CLFB_pinned", "CLFB_pinned_echo", "CLFB_control")
tot = {"full": 0, "evicted": 0, "finder": 0, "finder_echo": 0, "n": 0, **{a: 0 for a in ARMS}}
cov = []; rows = []; t0 = time.time()
for r in recs:
    ids = r["context_token_ids"]; lo, hi = r["evict_range"]
    context = tok.decode(ids, skip_special_tokens=False); enc = tok.encode(context); assert enc.ids == ids
    uturns = P._user_turns(context)
    cands = []  # (span, prob, origin_turn)
    for ca, cb, pr, t in SCORES[str(r["session"])]:
        ts = P._token_span(enc, ca, cb)
        if ts:
            s, e = max(lo, ts[0]), min(hi, ts[1])
            if e > s:
                cands.append(((s, e), pr, t))
    sel = sorted([c for c in cands if c[1] >= THR], key=lambda c: -c[1])
    keepc = [tuple(k) for k in r["keep"]]; Bk = sum(e - s for s, e in keepc)
    budget = r["arms"]["pinned"]["pinned_cols"]
    sets = {}
    keep_all = sorted(c[0] for c in sel); aged_all = [{"span": c[0], "origin_turn": c[2]} for c in sel]
    kept, got = [], 0
    for (s, e), pr, t in sel:
        if got >= budget:
            break
        take = min(e - s, budget - got); kept.append(((s, s + take), t)); got += take
    keep_b = sorted(k for k, _ in kept); aged_b = [{"span": k, "origin_turn": t} for k, t in kept]
    cov.append(sum(sum(overlap(c, s) for s in keep_all) for c in keepc) / Bk)
    sess = corpus[r["key"]]; last = sess["turns"][-1]
    row = {"key": int(sess["key"]) * 10 + r["n_turns"], "instruction_id_list": last["instruction_id_list"], "kwargs": last["kwargs"]}
    n_aged = r["n_aged"]; out = {}
    for tag, keep, aged in (("CLF", keep_all, aged_all), ("CLFB", keep_b, aged_b)):
        aged, keep = clamp(context, aged, keep)
        control = P.matched_control_spans(keep, (lo, hi)) if keep else []
        if aged:
            echoed, _, _ = P.echo_context(tok, context, aged); echo_ids, echo_ev = P.tokenized_eviction_range(tok, echoed)
        else:
            echo_ids, echo_ev = ids, (lo, hi)
        for arm, arm_ids, ev, ck, name in (("pinned", ids, (lo, hi), (), f"{tag}_pinned"), ("pinned_echo", echo_ids, echo_ev, (), f"{tag}_pinned_echo"), ("pinned_control", ids, (lo, hi), control, f"{tag}_control")):
            gg = P.run_arm(model, tok, arm_ids, arm, keep, ev, 0.0, 512, 300.0, control_keep=ck)
            sc = list(score_row_constraints(row, gg["text"]))
            out[name] = {"aged_pass": sum(sc[:n_aged]), "truncated": gg.get("truncated"), "degenerate": P.is_degenerate(gg), "pinned_cols": gg.get("pinned_cols")}
        out[f"{tag}_cols"] = len({i for a, b in keep for i in range(a, b)})
    h = {a: r["arms"][a]["aged_pass"] for a in ("full", "evicted", "pinned", "pinned_echo")}
    rows.append({"session": r["session"], "n_aged": n_aged, "budget": budget, "n_cands": len(cands), "n_sel": len(sel), "coverage": cov[-1], "h1p": h, "out": out,
                 "selected": [(c[0], round(c[1], 3)) for c in sel]})
    tot["n"] += n_aged; tot["full"] += h["full"]; tot["evicted"] += h["evicted"]; tot["finder"] += h["pinned"]; tot["finder_echo"] += h["pinned_echo"]
    for a in ARMS:
        tot[a] += out[a]["aged_pass"]
    print(f"s{r['session']:02d} aged={n_aged} cands={len(cands)} sel={len(sel)} cols={out['CLF_cols']}/{out['CLFB_cols']}(finder {budget}) cov={cov[-1]:.2f} | finder={h['pinned']}/{h['pinned_echo']} | CLF {out['CLF_pinned']['aged_pass']}/{out['CLF_pinned_echo']['aged_pass']} ctrl {out['CLF_control']['aged_pass']} | CLFB {out['CLFB_pinned']['aged_pass']}/{out['CLFB_pinned_echo']['aged_pass']} ctrl {out['CLFB_control']['aged_pass']}", flush=True)
print(f"elapsed {time.time()-t0:.0f}s thr={THR}")
print(f"COVERAGE mean {sum(cov)/len(cov):.3f} sessions>=0.8: {sum(c>=0.8 for c in cov)}/20")
print("TOTALS:", json.dumps(tot))
json.dump(rows, open(Path(__file__).with_name("clf_probe_rows.json"), "w"), indent=1)
