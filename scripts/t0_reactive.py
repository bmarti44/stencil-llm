# ruff: noqa
"""PRESS-PLAN T0.5: event-triggered (reactive) pressing baseline.

Dev replay seeds (13.10M, s0 unextended), arms: base, reactive, oracle,
structured (== oracle alias, reported for the record), reinsertion.
Reactive rule (registered): when this arm's OWN checker feedback flags
moment class c after work turn w, press type-c parser moments
(_oracle_moment) at subsequent work turns while c stays active with the
same value (update/clear resets the trigger); refractory: the trigger
drops after the first later work where c scores adherent.

Metric (v3.2): eligible set frozen from the BASE arm — per violation
episode, the DOWNSTREAM SET = all active opportunities of that type at
later work turns; all arms scored on the union;
recovery_closure = (A_reactive - A_base) / (A_oracle - A_base);
precondition (A_oracle - A_base)/|set| >= 0.10.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from stencil import determinism  # noqa: F401
import torch
from tokenizers import Tokenizer

from stencil.qwen3 import Qwen3
from stencil.t2_runner import (BETA, LAYERS, _oracle_moment, feedback_text,
                               ledger_sentence_spans, prompt_at, run_session, score_work)
from stencil.t2_sessions import generate_t2

SEEDS = [13_100_000 + i for i in range(24)]

tok = Tokenizer.from_file(str(ROOT / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
m = Qwen3()
m.load_state_dict(torch.load(ROOT / "models" / "qwen3-1.7b.pt", map_location="cpu"), strict=True)
m = m.to(torch.bfloat16).cuda().eval()


def run_reactive(sess):
    results = []
    feedback = {}
    triggered = {}  # type -> ledger value at trigger time
    for wt in sess.work_turns:
        led = sess.ledger_at[wt]
        # update/clear resets the trigger
        for ty in list(triggered):
            if led.get(ty) != triggered[ty]:
                del triggered[ty]
        ptxt = prompt_at(sess, wt, "dev")
        for et, ftxt in feedback.items():
            if et < wt:
                ptxt = ptxt.replace("[checker] (deterministic feedback on the previous submission is inserted here at run time)", ftxt, 1)
        spans = ledger_sentence_spans(ptxt, sess, wt, "dev", tok)
        toks = torch.tensor([tok.encode(ptxt).ids], device="cuda")
        outs, text = [], ""
        with torch.no_grad():
            for _ in range(120):
                ab = None
                key = _oracle_moment(text[-80:])
                if key is not None and key in triggered and key in spans:
                    t = toks.shape[1]
                    bias = torch.zeros(t, t, device="cuda")
                    bias[-1:, spans[key][0]:spans[key][1]] = BETA
                    ab = {L: bias for L in LAYERS}
                nxt = int(m(toks, attn_bias=ab)[0, -1].argmax())
                outs.append(nxt)
                toks = torch.cat([toks, torch.tensor([[nxt]], device="cuda")], dim=1)
                text = tok.decode(outs)
                if "```" in text[-6:]:
                    break
        wr = score_work(text.split("```")[0], sess, wt)
        results.append(wr)
        # refractory: adherent triggered types drop; new violations trigger
        for o in sess.opportunities:
            if o.turn != wt or o.cell != "active":
                continue
            e = wr.per_opportunity.get(o.opportunity_id, {})
            ty = o.moment_class
            if e.get("adherent") is False and ty in sess.ledger_at[wt]:
                triggered[ty] = sess.ledger_at[wt][ty]
            elif e.get("adherent") and ty in triggered:
                del triggered[ty]
        for i in range(wt + 1, len(sess.turns)):
            if sess.turns[i].kind == "env":
                feedback[i] = feedback_text(wr, sess)
                break
    return results


def main():
    per_arm = {a: {} for a in ("base", "reactive", "oracle", "reinsertion")}
    downstream = {}  # (seed) -> set of opportunity_ids
    for k, seed in enumerate(SEEDS):
        sess = generate_t2(seed, 20, "dev", interference="s0")
        for arm in per_arm:
            rs = run_reactive(sess) if arm == "reactive" else run_session(m, tok, sess, "dev", arm)
            for r in rs:
                for o in sess.opportunities:
                    if o.turn == r.turn:
                        per_arm[arm][o.opportunity_id] = r.per_opportunity.get(o.opportunity_id, {})
        # downstream sets from the BASE arm
        ids = set()
        for wt in sess.work_turns:
            for o in sess.opportunities:
                if o.turn != wt or o.cell != "active":
                    continue
                if per_arm["base"][o.opportunity_id].get("adherent") is False:
                    later_env = next((i for i in range(wt + 1, len(sess.turns)) if sess.turns[i].kind == "env"), None)
                    if later_env is None:
                        continue
                    for o2 in sess.opportunities:
                        if o2.cell == "active" and o2.moment_class == o.moment_class and o2.turn > later_env:
                            ids.add(o2.opportunity_id)
        downstream[seed] = ids
        print(f"  {k}/{len(SEEDS)} sessions, eligible so far {sum(len(v) for v in downstream.values())}", flush=True)

    elig = set().union(*downstream.values()) if downstream else set()
    A = {arm: sum(1 for oid in elig if per_arm[arm].get(oid, {}).get("adherent")) for arm in per_arm}
    n = len(elig)
    headroom = (A["oracle"] - A["base"]) / max(1, n)
    rc = (A["reactive"] - A["base"]) / max(1, (A["oracle"] - A["base"])) if A["oracle"] != A["base"] else 0.0
    # whole-session adherence per arm (all active opportunities), for the record
    allact = {arm: 0 for arm in per_arm}
    tot = 0
    for seed in SEEDS:
        sess = generate_t2(seed, 20, "dev", interference="s0")
        for o in sess.opportunities:
            if o.cell == "active":
                tot += 1
                for arm in per_arm:
                    allact[arm] += bool(per_arm[arm].get(o.opportunity_id, {}).get("adherent"))
    out = {"n_eligible": n, "A": A, "headroom_on_eligible": round(headroom, 4),
           "recovery_closure": round(rc, 4),
           "precondition_binds": headroom >= 0.10,
           "session_adherence": {a: round(allact[a] / max(1, tot), 4) for a in per_arm},
           "n_active_total": tot}
    print(json.dumps(out, indent=1), flush=True)
    (ROOT / "results" / "qwen" / "t0-reactive.json").write_text(json.dumps(out, indent=1))
    print("saved results/qwen/t0-reactive.json", flush=True)


if __name__ == "__main__":
    main()
