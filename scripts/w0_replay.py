# ruff: noqa
"""W0 dev replay (INTERNAL-WAVE-PLAN v3.1): seeds 13,450,000..23,
feedback_mode=none for EVERY arm. Arms: base, wave (w0-ce.pt), proxy
(w0-proxy.pt — the matched causal control, identical actuator), oracle
(once; parser+ledger, hand A2 field), reinsertion. Closure from raw
paired numerators; T0.3 validity rule; per-press gain histograms.
Inference (wave/proxy): at each step, h20 via return_hidden=20 on the
current sequence; field row over prompt columns; second forward with
the bias. Deterministic greedy.
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
from stencil.t2_runner import LAYERS, _oracle_moment, ledger_sentence_spans, prompt_at, score_work
from stencil.t2_sessions import generate_t2, ledger_text
from stencil.wave import WaveController

NEUTRAL = "[checker] (no feedback available this session)"
SEEDS = [13_450_000 + i for i in range(24)]

tok = Tokenizer.from_file(str(ROOT / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
m = Qwen3()
m.load_state_dict(torch.load(ROOT / "models" / "qwen3-1.7b.pt", map_location="cpu"), strict=True)
m = m.to(torch.bfloat16).cuda().eval()


def load_ctrl(name):
    w = WaveController().cuda()
    w.load_state_dict(torch.load(ROOT / "results" / "qwen" / name, map_location="cpu"))
    return w.eval()


def hand_row(P, span, beta=2.0):
    e = torch.full((P,), -6.0)
    e[span[0]:span[1]] = 6.0
    sm = torch.softmax(e, dim=-1)
    return beta * sm / sm.max()


def run_arm(sess, arm, ctrl=None):
    results, gains = [], []
    for wt in sess.work_turns:
        ptxt = prompt_at(sess, wt, "dev").replace(
            "[checker] (deterministic feedback on the previous submission is inserted here at run time)", NEUTRAL)
        if arm == "reinsertion":
            led = ledger_text(sess.ledger_at[wt])
            marker = sess.turns[wt].text
            ptxt = ptxt.replace(marker, "(Reminder) " + led + "\n" + marker, 1)
        enc = tok.encode(ptxt)
        P = len(enc.ids)
        spans = ledger_sentence_spans(ptxt, sess, wt, "dev", tok) if arm == "oracle" else {}
        toks = torch.tensor([enc.ids], device="cuda")
        K = None
        gen, text = [], ""
        with torch.no_grad():
            if arm in ("wave", "proxy"):
                K = m(toks, return_hidden=20)[0].float()[:P]
            for _ in range(120):
                ab = None
                if arm == "oracle" and spans:
                    key = _oracle_moment(text[-80:])
                    if key is not None and key in spans:
                        t = toks.shape[1]
                        bias = torch.zeros(t, t)
                        bias[-1, :P] = hand_row(P, spans[key])
                        ab = {L: bias.cuda() for L in LAYERS}
                elif arm in ("wave", "proxy"):
                    h_t = m(toks, return_hidden=20)[0, -1].float()
                    row = ctrl(h_t, K)
                    gains.append(float(row.max()))
                    t = toks.shape[1]
                    bias = torch.zeros(t, t, device="cuda")
                    bias[-1, :P] = row
                    ab = {L: bias for L in LAYERS}
                nxt = int(m(toks, attn_bias=ab)[0, -1].argmax())
                gen.append(nxt)
                toks = torch.cat([toks, torch.tensor([[nxt]], device="cuda")], dim=1)
                text = tok.decode(gen)
                if "```" in text[-6:]:
                    break
        results.append(score_work(text.split("```")[0], sess, wt))
    return results, gains


def main():
    ctrls = {"wave": load_ctrl("w0-ce.pt"), "proxy": load_ctrl("w0-proxy.pt")}
    arms = ["base", "wave", "proxy", "oracle", "reinsertion"]
    agg = {a: {"adh": 0, "n": 0, "parse": 0, "works": 0, "paired": {}} for a in arms}
    hists = {"wave": [], "proxy": []}
    for k, seed in enumerate(SEEDS):
        sess = generate_t2(seed, 20, "dev", interference="s0")
        for arm in arms:
            rs, gains = run_arm(sess, arm, ctrls.get(arm))
            if arm in hists:
                hists[arm] += gains
            for r in rs:
                a = agg[arm]
                a["works"] += 1
                a["parse"] += r.parse
                a["paired"][(seed, r.turn)] = {"parse": r.parse, "exec": r.exec_ok,
                                               "adh": {o.opportunity_id: bool(r.per_opportunity.get(o.opportunity_id, {}).get("adherent"))
                                                       for o in sess.opportunities if o.turn == r.turn and o.cell == "active"}}
                for o in sess.opportunities:
                    if o.turn == r.turn and o.cell == "active":
                        a["n"] += 1
                        a["adh"] += bool(r.per_opportunity.get(o.opportunity_id, {}).get("adherent"))
        print(f"  {k}/{len(SEEDS)} sessions", flush=True)

    out = {}
    base = agg["base"]
    for arm in arms:
        a = agg[arm]
        out[arm] = {"adherence": round(a["adh"] / max(1, a["n"]), 4), "n_active": a["n"],
                    "parse_rate": round(a["parse"] / max(1, a["works"]), 4)}
        if arm != "base":
            broken = sum(1 for kk in a["paired"] if
                         (base["paired"][kk]["parse"] and not a["paired"][kk]["parse"]) or
                         (base["paired"][kk]["exec"] and not a["paired"][kk]["exec"]))
            gain = a["adh"] - base["adh"]
            du = gain - 2 * broken
            out[arm]["paired_broken"] = broken
            out[arm]["adh_gain_raw"] = gain
            out[arm]["dU_total"] = du
            out[arm]["valid"] = bool(du > 0 and du >= 0.8 * gain)
    headroom = (agg["oracle"]["adh"] - base["adh"]) / max(1, base["n"])
    out["headroom"] = round(headroom, 4)
    out["precondition_binds"] = headroom >= 0.10
    for arm in ("wave", "proxy"):
        denom = agg["oracle"]["adh"] - base["adh"]
        out[arm]["closure"] = round((agg[arm]["adh"] - base["adh"]) / denom, 4) if denom else None
        h = torch.histc(torch.tensor(hists[arm] or [0.0]), bins=10, min=0.0, max=2.0).tolist()
        out[arm]["gain_hist_0_2"] = h
    print(json.dumps({k: v for k, v in out.items() if k != "records"}, indent=1), flush=True)
    (ROOT / "results" / "qwen" / "w0-replay.json").write_text(json.dumps(out, indent=1))
    print("saved results/qwen/w0-replay.json", flush=True)


if __name__ == "__main__":
    main()
