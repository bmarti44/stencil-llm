# ruff: noqa
"""T1 prereg v3: train-hard/calib-hard collection + R2-PRETEST.

One collection pass per block (BLOCK env: "train" = 13.12M x48,
"calib" = 13.14M x24; SMOKE=1 uses 2 scratch seeds 13,050,100+).
Base-arm rollouts on s0x2; per timing-fire event stores h20, pooled
candidate features, span-provenance labels (authoritative = candidate
span inside a ledger sentence span), cell, s0x target info. After
collection, runs the registered pretest offline on the stored features:
frozen cos policy (legacy Wq/Wk, threshold 0.6407741904258727) —
assertion-hit coverage (must be total) and pressure (old policy
false-selects >= 10/48 train sessions). Digest recorded by TraceWriter.
"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from stencil import determinism  # noqa: F401
import torch
import torch.nn.functional as F
from tokenizers import Tokenizer

from stencil.qwen3 import Qwen3
from stencil.t2_runner import feedback_text, ledger_sentence_spans, prompt_at, score_work, span_in_ledger
from stencil.t2_select import candidate_spans
from stencil.t2_sessions import generate_t2
from stencil.t2_trace import TraceWriter, load_trace

BLOCK = os.environ.get("BLOCK", "train")
SMOKE = bool(os.environ.get("SMOKE"))
if SMOKE:
    SEEDS = [13_050_100 + i for i in range(2)]
elif BLOCK == "train":
    SEEDS = [13_120_000 + i for i in range(48)]
else:
    SEEDS = [13_140_000 + i for i in range(24)]
OUT = f"t1-{'smoke' if SMOKE else BLOCK}-features.pt"
THR = 0.6407741904258727
CLASSES = ["none", "prefix", "doc", "hint"]

tok = Tokenizer.from_file(str(ROOT / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
m = Qwen3()
m.load_state_dict(torch.load(ROOT / "models" / "qwen3-1.7b.pt", map_location="cpu"), strict=True)
m = m.to(torch.bfloat16).cuda().eval()
sel = torch.load(ROOT / "results" / "qwen" / "t2b-selector.pt", map_location="cpu")
head = torch.nn.Linear(2048, 4); head.load_state_dict(sel["head"]); head = head.cuda()
Wq = torch.nn.Linear(2048, 64); Wq.load_state_dict(sel["Wq"]); Wq = Wq.cuda()
Wk = torch.nn.Linear(2048, 64); Wk.load_state_dict(sel["Wk"]); Wk = Wk.cuda()
TAU = sel["tau"]


def collect_session(sess, writer, seed):
    n = 0
    feedback = {}
    for wt in sess.work_turns:
        ptxt = prompt_at(sess, wt, "dev")
        for et, ftxt in feedback.items():
            if et < wt:
                ptxt = ptxt.replace("[checker] (deterministic feedback on the previous submission is inserted here at run time)", ftxt, 1)
        enc = tok.encode(ptxt)
        cands = candidate_spans(ptxt, enc)
        spans = ledger_sentence_spans(ptxt, sess, wt, "dev", tok)
        toks = torch.tensor([enc.ids], device="cuda")
        with torch.no_grad():
            cand_feats = None
            if cands:
                h_prompt = m(toks, return_hidden=20)[0].float()
                cand_feats = torch.stack([h_prompt[c[2][0]:c[2][1]].mean(dim=0) for c in cands])
            outs, text = [], ""
            for step in range(120):
                h20 = m(toks, return_hidden=20)[0, -1].float()
                probs = torch.softmax(head(h20), dim=-1)
                ci = int(probs[1:].argmax()) + 1
                if float(probs[ci]) > TAU and cands:
                    ty = CLASSES[ci]
                    writer.add_event({
                        "seed": seed, "work_turn": wt, "step": step, "pred_type": ty,
                        "h20": h20.cpu().to(torch.float16),
                        "cand_feats": cand_feats.cpu().to(torch.float16),
                        "candidates": [
                            {"type": c[0], "value": c[1], "span": c[2],
                             "authoritative": span_in_ledger(c[2], spans)}
                            for c in cands
                        ],
                        "type_active": ty in sess.ledger_at[wt],
                        "s0x_target": dict(sess.held_out["s0x"]),
                        "ledger": dict(sess.ledger_at[wt]),
                    })
                    n += 1
                nxt = int(m(toks)[0, -1].argmax())
                outs.append(nxt)
                toks = torch.cat([toks, torch.tensor([[nxt]], device="cuda")], dim=1)
                text = tok.decode(outs)
                if "```" in text[-6:]:
                    break
        wr = score_work(text.split("```")[0], sess, wt)
        writer.add_work({"seed": seed, "work_turn": wt, "arm": "base", "parse": wr.parse,
                        "exec_ok": wr.exec_ok, "per_opportunity": wr.per_opportunity})
        for i in range(wt + 1, len(sess.turns)):
            if sess.turns[i].kind == "env":
                feedback[i] = feedback_text(wr, sess)
                break
    return n


def pretest(path):
    tr = load_trace(path)
    sessions = {}
    for e in tr["events"]:
        s = sessions.setdefault(e["seed"], {"assertion": False, "false_sel": False})
        typed = [i for i, c in enumerate(e["candidates"]) if c["type"] == e["pred_type"]]
        if not typed:
            continue
        has_auth = any(e["candidates"][i]["authoritative"] for i in typed)
        tgt = e["s0x_target"]
        if (e["work_turn"] == tgt["work_turn"] and e["pred_type"] == tgt["type"] and not has_auth):
            s["assertion"] = True
        with torch.no_grad():
            q = F.normalize(Wq(e["h20"].float().cuda()), dim=0)
            k = F.normalize(Wk(e["cand_feats"].float().cuda()), dim=1)
            cos = q @ k.T
            j = max(typed, key=lambda i: float(cos[i]))
            if float(cos[j]) > THR and not e["candidates"][j]["authoritative"]:
                s["false_sel"] = True
    hit = sum(1 for s in sessions.values() if s["assertion"])
    pressure = sum(1 for s in sessions.values() if s["false_sel"])
    return {"n_sessions_with_events": len(sessions), "assertion_hit": hit,
            "pressure_sessions": pressure}


def main():
    writer = TraceWriter(ROOT / "results" / "qwen" / OUT)
    total = 0
    for k, seed in enumerate(SEEDS):
        sess = generate_t2(seed, 20, "dev", interference="s0x2")
        total += collect_session(sess, writer, seed)
        if k % 8 == 0:
            print(f"  {k}/{len(SEEDS)} sessions, {total} events", flush=True)
    writer.close()
    print(f"COLLECTED {total} events -> results/qwen/{OUT}", flush=True)
    p = pretest(ROOT / "results" / "qwen" / OUT)
    p["n_seeds"] = len(SEEDS)
    print("PRETEST:", json.dumps(p), flush=True)
    (ROOT / "results" / "qwen" / OUT.replace("-features.pt", "-pretest.json")).write_text(json.dumps(p, indent=1))


if __name__ == "__main__":
    main()
