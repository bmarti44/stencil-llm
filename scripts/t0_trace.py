# ruff: noqa
"""PRESS-PLAN T0.1: trace pass over the frozen trace seeds (13.00M block).

Replays the base arm step-by-step, recording one event at every legacy
timing-head fire: h20 state, timing logits, full candidate set with
source labels (live/superseded/distractor), qk + cosine score vectors,
ledger snapshot, counterfactual cell. Also replays the legacy selector
arm (registered theta) with H2 press logging. TRACE SEEDS ONLY — fixture
blocks are certification-sealed (plan v3.2).
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from stencil import determinism  # noqa: F401
import torch
import torch.nn.functional as F
from tokenizers import Tokenizer

from stencil.qwen3 import Qwen3
from stencil.t2_runner import ledger_sentence_spans, prompt_at, run_session, score_work
from stencil.t2_select import candidate_spans
from stencil.t2_sessions import generate_t2
from stencil.t2_trace import TraceWriter

import os
TRACE = [13_000_000 + i for i in range(int(os.environ.get("TRACE_N", "48")))]
OUT = "t0-trace-smoke.pt" if os.environ.get("TRACE_N") else "t0-trace.pt"
CLASSES = ["none", "prefix", "doc", "hint"]
MAX_NEW = 120

tok = Tokenizer.from_file(str(ROOT / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
m = Qwen3()
m.load_state_dict(torch.load(ROOT / "models" / "qwen3-1.7b.pt", map_location="cpu"), strict=True)
m = m.to(torch.bfloat16).cuda().eval()
sel = torch.load(ROOT / "results" / "qwen" / "t2b-selector.pt", map_location="cpu")
head = torch.nn.Linear(2048, 4); head.load_state_dict(sel["head"]); head = head.cuda()
Wq = torch.nn.Linear(2048, 64); Wq.load_state_dict(sel["Wq"]); Wq = Wq.cuda()
Wk = torch.nn.Linear(2048, 64); Wk.load_state_dict(sel["Wk"]); Wk = Wk.cuda()
TAU, THETA = sel["tau"], sel["theta"]


def source_of(ty, value, sess, wt):
    led = sess.ledger_at[wt]
    if led.get(ty) == value:
        return "live"
    if value in sess.superseded_at[wt].get(ty, ()):
        return "superseded"
    return "distractor"


def cell_of(ty, sess, wt):
    for o in sess.opportunities:
        if o.turn == wt and o.moment_class == ty:
            return o.cell
    return "none"


def trace_base(sess, writer, seed):
    n_events = 0
    for wt in sess.work_turns:
        ptxt = prompt_at(sess, wt, "dev")
        enc = tok.encode(ptxt)
        cands = candidate_spans(ptxt, enc)
        toks = torch.tensor([enc.ids], device="cuda")
        with torch.no_grad():
            cand_feats = None
            if cands:
                h_prompt = m(toks, return_hidden=20)[0].float()
                cand_feats = torch.stack([h_prompt[c[2][0]:c[2][1]].mean(dim=0) for c in cands])
            outs, text = [], ""
            for step in range(MAX_NEW):
                h20 = m(toks, return_hidden=20)[0, -1].float()
                probs = torch.softmax(head(h20), dim=-1)
                c = int(probs[1:].argmax()) + 1
                if float(probs[c]) > TAU and cands:
                    q = Wq(h20)
                    k = Wk(cand_feats.cuda())
                    qk = (q @ k.T / 8.0).cpu().tolist()
                    cos = (F.normalize(q, dim=0) @ F.normalize(k, dim=1).T).cpu().tolist()
                    writer.add_event({
                        "seed": seed, "work_turn": wt, "step": step,
                        "pred_type": CLASSES[c],
                        "h20": h20.cpu().to(torch.float16),
                        "timing_logits": head(h20).cpu(),
                        "candidates": [
                            {"type": ty, "value": v, "source": source_of(ty, v, sess, wt), "span": sp}
                            for ty, v, sp, _ in cands
                        ],
                        "qk_scores": qk, "cos_scores": cos,
                        "ledger": dict(sess.ledger_at[wt]),
                        "cell": cell_of(CLASSES[c], sess, wt),
                    })
                    n_events += 1
                nxt = int(m(toks)[0, -1].argmax())
                outs.append(nxt)
                toks = torch.cat([toks, torch.tensor([[nxt]], device="cuda")], dim=1)
                text = tok.decode(outs)
                if "```" in text[-6:]:
                    break
        wr = score_work(text.split("```")[0], sess, wt)
        writer.add_work({"seed": seed, "work_turn": wt, "arm": "base", "parse": wr.parse,
                        "exec_ok": wr.exec_ok, "per_opportunity": wr.per_opportunity})
    return n_events


def sel_timing(model, toks, text):
    with torch.no_grad():
        h = model(toks, return_hidden=20)[0, -1].float()
        probs = torch.softmax(head(h), dim=-1)
        c = int(probs[1:].argmax()) + 1
        return CLASSES[c] if float(probs[c]) > TAU else None


def sel_address(model, toks, ptxt, spans, key):
    enc = tok.encode(ptxt)
    cands = candidate_spans(ptxt, enc)
    if not cands:
        return None
    with torch.no_grad():
        h_prompt = model(torch.tensor([enc.ids], device="cuda"), return_hidden=20)[0].float()
        cf = torch.stack([h_prompt[c[2][0]:c[2][1]].mean(dim=0) for c in cands])
        s = model(toks, return_hidden=20)[0, -1].float()
        scores = (Wq(s) @ Wk(cf.cuda()).T) / 8.0
        j = int(scores.argmax())
        if float(scores[j]) <= THETA:
            return None
    ty = cands[j][0]
    return ty if ty in spans else None


def main():
    writer = TraceWriter(ROOT / "results" / "qwen" / OUT)
    total = 0
    press_log = []
    for k, seed in enumerate(TRACE):
        sess = generate_t2(seed, 20, "dev", interference="s0")
        total += trace_base(sess, writer, seed)
        rs = run_session(m, tok, sess, "dev", "selector", timing=sel_timing,
                         address=sel_address, press_log=press_log)
        for r in rs:
            writer.add_work({"seed": seed, "work_turn": r.turn, "arm": "selector",
                            "parse": r.parse, "exec_ok": r.exec_ok,
                            "per_opportunity": r.per_opportunity})
        if k % 8 == 0:
            print(f"  {k}/{len(TRACE)} sessions, {total} events, {len(press_log)} legacy presses", flush=True)
    writer.add_work({"seed": None, "work_turn": None, "arm": "selector-press-log",
                    "parse": None, "exec_ok": None, "per_opportunity": press_log})
    writer.close()
    print(f"TRACE COMPLETE: {total} events, {len(press_log)} legacy selector presses", flush=True)
    print(f"saved results/qwen/{OUT}", flush=True)


if __name__ == "__main__":
    main()
