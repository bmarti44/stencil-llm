# ruff: noqa
"""W3b RECORD RUN (w3 prereg v3, frozen; seeds 13,650,000..23, s0,
feedback_mode=none, frozen w0-ce.pt, theta = 1.9 from
w3-null-theta.json).

Part 1 — FOCUS READOUT: per step, decode = the unique ledger-sentence
span containing first_argmax(field), else NULL; NULL also when
gain <= theta. Metrics: conditional WHERE accuracy at active governed
moments on exact (type, value) identity; WHEN/NULL confusion matrix
over ALL steps (active-moment vs other); a human-readable 3-session
focus-trace artifact.

Part 2 — COUNTER-AUTHORITY OVERRIDE (frozen spec): eligible moments
from the INTACT trajectory = parser moments whose type is active with
a PRECEDING visible conflicting same-type note; nearest preceding
note, first-index tie-break; imposed field = A2 hand field (+6/-6 ->
softmax/max * beta 2) on the note's full rendered-sentence token span,
layers 20-27, exactly the governed moment's row; ONE intervention per
paired rollout. Gates: paired alternate-value adoption rises >= 20
points, one-sided McNemar p < 0.05, n >= 60; non-target adherence
drop <= 2 counts total; parse/exec cost reported.
"""
import json
import sys
from math import comb
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from stencil import determinism  # noqa: F401
import torch
from tokenizers import Tokenizer

from stencil.qwen3 import Qwen3
from stencil.t2_runner import LAYERS, _oracle_moment, build_arm_prompt, ledger_sentence_spans, score_work
from stencil.t2_sessions import SENT, generate_t2
from stencil.wave import WaveController

NEUTRAL = "[checker] (no feedback available this session)"
SEEDS = [13_650_000 + i for i in range(24)]
THETA = 1.9

tok = Tokenizer.from_file(str(ROOT / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
m = Qwen3()
m.load_state_dict(torch.load(ROOT / "models" / "qwen3-1.7b.pt", map_location="cpu"), strict=True)
m = m.to(torch.bfloat16).cuda().eval()
wave = WaveController().cuda()
wave.load_state_dict(torch.load(ROOT / "results" / "qwen" / "w0-ce.pt", map_location="cpu"))
wave.eval()


def neutral(ptxt):
    return ptxt.replace("[checker] (deterministic feedback on the previous submission is inserted here at run time)", NEUTRAL)


def note_spans(ptxt, enc, sess, wt):
    """visible conflicting same-type notes: 'Note: <SENT>' occurrences whose
    value differs from the live value; returns [(type, value, span, char)]."""
    out = []
    led = sess.ledger_at[wt]
    import re
    for ty in ("prefix", "doc", "hint"):
        if ty not in led:
            continue
        pat = re.escape(SENT[ty].format(v="XXVALXX")).replace("XXVALXX", r"(\w+)")
        for mt in re.finditer(pat, ptxt):
            v = mt.group(1)
            if v == led[ty]:
                continue
            a, b = mt.span()
            cols = [i for i, (x, y) in enumerate(enc.offsets) if x < b and y > a]
            if cols:
                out.append((ty, v, (cols[0], cols[-1] + 1), a))
    return out


def rollout(sess, wt, override=None, trace=None):
    """override = (row_step, span). Returns WorkResult + focus decisions."""
    ptxt = neutral(build_arm_prompt(sess, wt, "dev", "base"))
    enc = tok.encode(ptxt)
    P = len(enc.ids)
    led_spans = ledger_sentence_spans(ptxt, sess, wt, "dev", tok)
    led = sess.ledger_at[wt]
    toks = torch.tensor([enc.ids], device="cuda")
    gen, text = [], ""
    decisions = []
    with torch.no_grad():
        K = m(toks, return_hidden=20)[0].float()[:P]
        for step in range(120):
            h_t = m(toks, return_hidden=20)[0, -1].float()
            row = wave(h_t, K)
            if override is not None and step == override[0]:
                e = torch.full((P,), -6.0)
                e[override[1][0]:override[1][1]] = 6.0
                sm = torch.softmax(e, dim=-1)
                row = (2.0 * sm / sm.max()).cuda()
            g = float(row.max())
            i_star = int(row.argmax())
            focus = None
            if g > THETA:
                for ty, (a, b) in led_spans.items():
                    if a <= i_star < b:
                        focus = (ty, led[ty])
                        break
            moment = _oracle_moment(text[-80:])
            decisions.append({"step": step, "gain": round(g, 3), "focus": focus,
                              "moment": moment if (moment in led) else None})
            if trace is not None:
                trace.append({"wt": wt, **decisions[-1]})
            t = toks.shape[1]
            bias = torch.zeros(t, t, device="cuda")
            bias[-1, :P] = row
            nxt = int(m(toks, attn_bias={L: bias for L in LAYERS})[0, -1].argmax())
            gen.append(nxt)
            toks = torch.cat([toks, torch.tensor([[nxt]], device="cuda")], dim=1)
            text = tok.decode(gen)
            if "```" in text[-6:]:
                break
    return score_work(text.split("```")[0], sess, wt), decisions, ptxt, enc


def main():
    where_ok = where_n = 0
    conf = {"tp": 0, "fn": 0, "fp": 0, "tn": 0}
    traces = []
    interventions = []  # (sess, wt, step, note_ty, note_v, note_span)
    intact_results = {}
    for si, seed in enumerate(SEEDS):
        sess = generate_t2(seed, 20, "dev", interference="s0")
        for wt in sess.work_turns:
            tr = traces if si < 3 else None
            wr, dec, ptxt, enc = rollout(sess, wt, trace=tr)
            intact_results[(seed, wt)] = wr
            led = sess.ledger_at[wt]
            notes = note_spans(ptxt, enc, sess, wt)
            chosen_for_work = False
            for d in dec:
                is_moment = d["moment"] is not None
                pressed = d["focus"] is not None
                conf["tp" if (is_moment and pressed) else "fn" if is_moment else "fp" if pressed else "tn"] += 1
                if is_moment:
                    where_n += 1
                    if d["focus"] == (d["moment"], led[d["moment"]]):
                        where_ok += 1
                    # eligible intervention: nearest PRECEDING visible conflicting same-type note
                    if not chosen_for_work:
                        cands = [n for n in notes if n[0] == d["moment"]]
                        if cands:
                            best = max(cands, key=lambda n: n[3])  # nearest preceding = max char < moment; notes all in prompt (precede generation)
                            interventions.append((seed, wt, d["step"], best[0], best[1], best[2]))
                            chosen_for_work = True
        print(f"  intact {si}/{len(SEEDS)}", flush=True)

    # Part 2: paired override rollouts (one intervention per pair)
    adopt_intact = adopt_over = 0
    discordant_01 = discordant_10 = 0
    nontarget_drop = 0
    parse_cost = 0
    used = interventions[:max(60, len(interventions))]
    for n, (seed, wt, step, ty, v, span) in enumerate(used):
        sess = generate_t2(seed, 20, "dev", interference="s0")
        wr_i = intact_results[(seed, wt)]
        wr_o, _, _, _ = rollout(sess, wt, override=(step, span))
        def adopted(wr):
            for o in sess.opportunities:
                if o.turn == wt and o.moment_class == ty:
                    return wr.per_opportunity.get(o.opportunity_id, {}).get("value_used") == v
            return False
        ai, ao = adopted(wr_i), adopted(wr_o)
        adopt_intact += ai
        adopt_over += ao
        if not ai and ao:
            discordant_01 += 1
        if ai and not ao:
            discordant_10 += 1
        for o in sess.opportunities:
            if o.turn == wt and o.cell == "active" and o.moment_class != ty:
                ii = bool(wr_i.per_opportunity.get(o.opportunity_id, {}).get("adherent"))
                oo = bool(wr_o.per_opportunity.get(o.opportunity_id, {}).get("adherent"))
                nontarget_drop += int(ii and not oo)
        parse_cost += int(wr_i.parse and not wr_o.parse)
        if n % 20 == 0:
            print(f"  override {n}/{len(used)}", flush=True)

    nI = len(used)
    # one-sided exact McNemar: P(X >= discordant_01 | n=discordant pairs, p=0.5)
    nd = discordant_01 + discordant_10
    p_val = sum(comb(nd, k) for k in range(discordant_01, nd + 1)) / (2 ** nd) if nd else 1.0
    out = {
        "readout": {
            "where_acc": round(where_ok / max(1, where_n), 4), "where_n": where_n,
            "confusion": conf, "theta": THETA,
        },
        "override": {
            "n": nI, "adopt_intact": adopt_intact, "adopt_override": adopt_over,
            "adopt_rise_points": round(100 * (adopt_over - adopt_intact) / max(1, nI), 1),
            "mcnemar_one_sided_p": round(p_val, 6),
            "discordant": [discordant_01, discordant_10],
            "nontarget_adherence_drop": nontarget_drop, "parse_cost": parse_cost,
        },
    }
    out["override"]["PASS"] = (out["override"]["adopt_rise_points"] >= 20
                               and p_val < 0.05 and nI >= 60 and nontarget_drop <= 2)
    out["readout"]["PASS_where"] = out["readout"]["where_acc"] >= 0.80
    print(json.dumps(out, indent=1), flush=True)
    (ROOT / "results" / "qwen" / "w3b.json").write_text(json.dumps(out, indent=1))
    (ROOT / "results" / "qwen" / "w3b-trace.json").write_text(json.dumps(traces))
    print("saved results/qwen/w3b.json + w3b-trace.json", flush=True)


if __name__ == "__main__":
    main()
