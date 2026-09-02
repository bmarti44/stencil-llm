"""RB control (kimi F2.4): ROLE RULE AT THE FINDER'S BUDGET on the 20 H1' sessions.
Per session: pin prior user turns oldest-first, whole turns, until the union of pinned columns >= the H1'-recorded
finder pin count; clip the final span from the right to exact equality; evict the rest; plus an exact-column null at
that count. Same run_arm/scoring path as H1'. Decision (registered by kimi's review before running): RB >= 38 total ->
structure does the work at equal budget; RB <= 37 -> the +4 over the finder is budget.
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
tot = {"finder": 0, "finder_control": 0, "RB": 0, "RB_control": 0, "n": 0}
rows = []; t0 = time.time()
for r in recs:
    ids = r["context_token_ids"]; lo, hi = r["evict_range"]
    context = tok.decode(ids, skip_special_tokens=False); enc = tok.encode(context)
    assert enc.ids == ids
    budget = r["arms"]["pinned"]["pinned_cols"]
    keep = []; got = 0
    for a, b in P._user_turns(context)[:-1]:  # oldest first
        ts = P._token_span(enc, a, b)
        if not ts:
            continue
        s, e = max(lo, ts[0]), min(hi, ts[1])
        if e <= s:
            continue
        if got + (e - s) >= budget:
            keep.append((s, s + (budget - got))); got = budget; break
        keep.append((s, e)); got += e - s
    n_pin = len({i for a, b in keep for i in range(a, b)})
    control = P.matched_control_spans(keep, (lo, hi))
    sess = corpus[r["key"]]; last = sess["turns"][-1]
    row = {"key": int(sess["key"]) * 10 + r["n_turns"], "instruction_id_list": last["instruction_id_list"], "kwargs": last["kwargs"]}
    n_aged = r["n_aged"]; out = {}
    for arm, ck in (("pinned", ()), ("pinned_control", control)):
        g = P.run_arm(model, tok, ids, arm, keep, (lo, hi), 0.0, 512, 300.0, control_keep=ck)
        sc = list(score_row_constraints(row, g["text"]))
        out[arm] = {"aged_pass": sum(sc[:n_aged]), "n": g["n"], "truncated": g.get("truncated"), "degenerate": P.is_degenerate(g), "pinned_cols": g.get("pinned_cols")}
    assert out["pinned"]["pinned_cols"] == out["pinned_control"]["pinned_cols"] == n_pin == budget, (out, n_pin, budget)
    h = {a: r["arms"][a]["aged_pass"] for a in ("full", "evicted", "pinned", "pinned_control")}
    rows.append({"session": r["session"], "n_aged": n_aged, "budget": budget, "keep": keep, "h1p": h, "RB": out})
    tot["n"] += n_aged; tot["finder"] += h["pinned"]; tot["finder_control"] += h["pinned_control"]; tot["RB"] += out["pinned"]["aged_pass"]; tot["RB_control"] += out["pinned_control"]["aged_pass"]
    print(f"s{r['session']:02d} aged={n_aged} budget={budget} finder={h['pinned']} finder_ctrl={h['pinned_control']} | RB={out['pinned']['aged_pass']} (trunc={out['pinned']['truncated']}, degen={out['pinned']['degenerate']}) RB_ctrl={out['pinned_control']['aged_pass']}", flush=True)
print(f"elapsed {time.time()-t0:.0f}s")
print("TOTALS:", json.dumps(tot))
json.dump(rows, open(Path(__file__).with_name("role_budget_rows.json"), "w"), indent=1)
