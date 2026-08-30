# ruff: noqa
"""PRESS-PLAN T0.3: paired single-press rollouts on the trace seeds.

For each selected press event, regenerate the work twice from the same
prompt (deterministic greedy): once unpressed (== base) and once with a
single-step press at the event's step. Conditions:
  correct  — live span of pred_type at a timing-fire step (active cell);
  wrongspan — highest-scoring NON-live candidate span at the same step;
  wrongmoment — live span pressed at fire_step+3 (a non-moment step).
Per work U := (# adherent active opportunities) - 2*BROKEN, BROKEN :=
pressed branch loses parse OR exec vs the unpressed branch (registered
T0.3). Outputs per-condition Delta-U distributions -> B, H components.
Pooling weights for H are NOT computed here (flagged: no observed false
-selection frequencies exist on trace); both wrong conditions reported
separately.
"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from stencil import determinism  # noqa: F401
import torch
from tokenizers import Tokenizer

from stencil.qwen3 import Qwen3
from stencil.t2_runner import BETA, LAYERS, feedback_text, prompt_at, score_work
from stencil.t2_sessions import generate_t2
from stencil.t2_trace import load_trace

CAP = int(os.environ.get("CAP", "220"))
SMOKE = bool(os.environ.get("SMOKE"))

tok = Tokenizer.from_file(str(ROOT / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
m = Qwen3()
m.load_state_dict(torch.load(ROOT / "models" / "qwen3-1.7b.pt", map_location="cpu"), strict=True)
m = m.to(torch.bfloat16).cuda().eval()


def gen(ptxt, press=None, max_new=120):
    """press = (step, span) applies the bias at exactly one step."""
    ids = tok.encode(ptxt).ids
    toks = torch.tensor([ids], device="cuda")
    outs, text = [], ""
    with torch.no_grad():
        for step in range(max_new):
            ab = None
            if press is not None and step == press[0]:
                t = toks.shape[1]
                bias = torch.zeros(t, t, device="cuda")
                bias[-1:, press[1][0]:press[1][1]] = BETA
                ab = {L: bias for L in LAYERS}
            nxt = int(m(toks, attn_bias=ab)[0, -1].argmax())
            outs.append(nxt)
            toks = torch.cat([toks, torch.tensor([[nxt]], device="cuda")], dim=1)
            text = tok.decode(outs)
            if "```" in text[-6:]:
                break
    return text.split("```")[0]


def U(wr, sess, wt, broken):
    adherent = sum(1 for o in sess.opportunities
                   if o.turn == wt and o.cell == "active"
                   and wr.per_opportunity.get(o.opportunity_id, {}).get("adherent"))
    return adherent - 2 * int(broken)


def prompts_for_session(sess):
    """Reproduce base-arm prompts incl. feedback threading (deterministic)."""
    prompts = {}
    feedback = {}
    for wt in sess.work_turns:
        ptxt = prompt_at(sess, wt, "dev")
        for et, ftxt in feedback.items():
            if et < wt:
                ptxt = ptxt.replace("[checker] (deterministic feedback on the previous submission is inserted here at run time)", ftxt, 1)
        prompts[wt] = ptxt
        wr = score_work(gen(ptxt), sess, wt)
        for i in range(wt + 1, len(sess.turns)):
            if sess.turns[i].kind == "env":
                feedback[i] = feedback_text(wr, sess)
                break
    return prompts


def main():
    tr = load_trace(ROOT / "results" / "qwen" / "t0-trace.pt")
    active = [e for e in tr["events"] if e["cell"] == "active"]
    active.sort(key=lambda e: (e["seed"], e["work_turn"], e["step"]))
    if SMOKE:
        active = active[:3]
    sel = active[:CAP]
    print(f"{len(sel)} active events selected (cap {CAP})", flush=True)

    prompt_cache = {}
    session_cache = {}
    results = {"correct": [], "wrongspan": [], "wrongmoment": []}
    for n, e in enumerate(sel):
        seed, wt, step = e["seed"], e["work_turn"], e["step"]
        if seed not in session_cache:
            session_cache[seed] = generate_t2(seed, 20, "dev", interference="s0")
            prompt_cache[seed] = prompts_for_session(session_cache[seed])
        sess, ptxt = session_cache[seed], prompt_cache[seed][wt]
        idx_typed = [i for i, c in enumerate(e["candidates"]) if c["type"] == e["pred_type"]]
        live = [i for i in idx_typed if e["candidates"][i]["source"] == "live"]
        if not live:
            continue
        live_span = tuple(e["candidates"][max(live, key=lambda i: e["qk_scores"][i])]["span"])
        nonlive = [i for i in range(len(e["candidates"])) if e["candidates"][i]["source"] != "live"]
        wrong_span = tuple(e["candidates"][max(nonlive, key=lambda i: e["qk_scores"][i])]["span"]) if nonlive else None

        base_code = gen(ptxt)
        base_wr = score_work(base_code, sess, wt)
        base_u = U(base_wr, sess, wt, broken=False)
        conds = {"correct": (step, live_span), "wrongmoment": (step + 3, live_span)}
        if wrong_span is not None:
            conds["wrongspan"] = (step, wrong_span)
        for cond, press in conds.items():
            code = gen(ptxt, press=press)
            wr = score_work(code, sess, wt)
            broken = (base_wr.parse and not wr.parse) or (base_wr.exec_ok and not wr.exec_ok)
            du = U(wr, sess, wt, broken) - base_u
            results[cond].append({"seed": seed, "wt": wt, "step": press[0], "dU": du,
                                  "broken": bool(broken), "changed": code != base_code})
        if n % 20 == 0:
            print(f"  {n}/{len(sel)} events", flush=True)

    summary = {}
    for cond, rows in results.items():
        n = len(rows)
        mean_du = sum(r["dU"] for r in rows) / max(1, n)
        summary[cond] = {"n": n, "mean_dU": round(mean_du, 4),
                         "broken_rate": round(sum(r["broken"] for r in rows) / max(1, n), 4),
                         "changed_rate": round(sum(r["changed"] for r in rows) / max(1, n), 4)}
        print(cond, summary[cond], flush=True)
    out = {"summary": summary, "rows": results, "note": "H pooling weights flagged: no observed false-selection frequencies on trace; conditions reported separately"}
    name = "t0-cost-smoke.json" if SMOKE else "t0-cost.json"
    (ROOT / "results" / "qwen" / name).write_text(json.dumps(out, indent=1))
    print(f"saved results/qwen/{name}", flush=True)


if __name__ == "__main__":
    main()
