"""Quick GPU test of the parameter-free ROLE RULE on the 20 H1' sessions: pin ALL prior user turns (no finder),
evict the rest of the history, score the checker outcomes exactly as H1' did. Compare with H1' recorded arms
(full / evicted / pinned[finder] / pinned_control) and a matched exact-column control for the role pins.
"""
import glob, json, sys, time
from pathlib import Path

ROOT = Path("/home/bmarti44/stencil-llm")
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "scripts"))
import torch  # noqa: E402
import g0_oracle as G  # noqa: E402
import ledger_kv_probe as P  # noqa: E402
from stencil.causal_moments import score_row_constraints  # noqa: E402

model, tok = G.load_model()
corpus = {r["key"]: r for r in (json.loads(l) for l in open(ROOT / "data/b3/mt-train-300.jsonl"))}
recs = [json.load(open(p)) for p in sorted(glob.glob(str(ROOT / "results/qwen/ledger-kv-probe-h1p/session-*.json")))]
tot = {"full": 0, "evicted": 0, "pinned_finder": 0, "pinned_finder_control": 0, "pinned_role": 0, "pinned_role_control": 0, "n": 0}
rows = []; t0 = time.time()
for r in recs:
    ids = r["context_token_ids"]; lo, hi = r["evict_range"]
    context = tok.decode(ids, skip_special_tokens=False)
    enc = tok.encode(context)
    if enc.ids != ids:
        print(f"s{r['session']:02d} SKIP: re-encoded context differs ({len(enc.ids)} vs {len(ids)} tokens)"); continue
    turns = P._user_turns(context)[:-1]  # prior user turns only
    keep = []
    for a, b in turns:
        ts = P._token_span(enc, a, b)
        if ts:
            keep.append((max(lo, ts[0]), min(hi, ts[1])))
    keep = [k for k in keep if k[1] > k[0]]
    n_pin = len({i for a, b in keep for i in range(a, b)}); n_ev = hi - lo
    try:
        control = P.matched_control_spans(keep, (lo, hi))
    except RuntimeError as e:
        print(f"s{r['session']:02d} role pins {n_pin}/{n_ev} columns: control impossible ({e})"); control = None
    sess = corpus[r["key"]]; last = sess["turns"][-1]
    row = {"key": int(sess["key"]) * 10 + r["n_turns"], "instruction_id_list": last["instruction_id_list"], "kwargs": last["kwargs"]}
    n_aged = r["n_aged"]
    out = {}
    for arm, kp, ck in (("pinned", keep, ()), ("pinned_control", keep, control)):
        if arm == "pinned_control" and control is None:
            out[arm] = None; continue
        g = P.run_arm(model, tok, ids, arm, kp, (lo, hi), 0.0, 512, 300.0, control_keep=ck)
        sc = list(score_row_constraints(row, g["text"]))
        out[arm] = {"aged_pass": sum(sc[:n_aged]), "n": g["n"], "truncated": g.get("truncated"), "degenerate": P.is_degenerate(g), "pinned_cols": g.get("pinned_cols")}
    h = {a: r["arms"][a]["aged_pass"] for a in ("full", "evicted", "pinned", "pinned_control")}
    rows.append({"session": r["session"], "n_aged": n_aged, "role_pin_cols": n_pin, "evictable": n_ev, "finder_pin_cols": r["arms"]["pinned"]["pinned_cols"], "h1p": h, "role": out})
    tot["n"] += n_aged; tot["full"] += h["full"]; tot["evicted"] += h["evicted"]; tot["pinned_finder"] += h["pinned"]; tot["pinned_finder_control"] += h["pinned_control"]
    tot["pinned_role"] += out["pinned"]["aged_pass"]; tot["pinned_role_control"] += (out["pinned_control"] or {"aged_pass": 0})["aged_pass"]
    print(f"s{r['session']:02d} aged={n_aged} full={h['full']} evicted={h['evicted']} finder={h['pinned']}(cols {r['arms']['pinned']['pinned_cols']}) finder_ctrl={h['pinned_control']} | ROLE={out['pinned']['aged_pass']} (cols {n_pin}/{n_ev}, trunc={out['pinned']['truncated']}, degen={out['pinned']['degenerate']}) role_ctrl={(out['pinned_control'] or {}).get('aged_pass')}", flush=True)
print(f"elapsed {time.time()-t0:.0f}s")
print("TOTALS over aged constraints:", json.dumps(tot))
json.dump(rows, open(Path(__file__).with_name("role_rule_rows.json"), "w"), indent=1)
