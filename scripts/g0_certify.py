# ruff: noqa
"""PRESS-PLAN sealed certification job (one policy, one block, one run).

Named policy (WORKLOG, before this block was touched): legacy supervised
timing head (fires at prob > tau) + type-restricted cos_max address over
MUST-2 candidates + threshold 0.6407741904258727 + runner guards.

Per session (interference=s0x): replay the policy arm (presses applied
as deployed). FAILURE EVENTS (any -> session fails):
  (a) a press decision (cos score > THR) whose chosen candidate is not
      the live entry of the predicted type at an active moment
      (pre-structural-guard, per plan v3.1);
  (b) the s0x assertion missing: no timing fire of the session's target
      type with a same-type non-live candidate and no live same-type
      candidate (counted as failure, never dropped).
Output: k/160, exact one-sided 95% CP bound, PASS iff U95 <= 5%.
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

from stencil.press_stats import clopper_pearson_upper
from stencil.qwen3 import Qwen3
from stencil.t2_runner import BETA, LAYERS, feedback_text, ledger_sentence_spans, prompt_at, score_work
from stencil.t2_select import candidate_spans
from stencil.t2_sessions import generate_t2

BLOCK = os.environ.get("BLOCK", "A")
STARTS = {"A": 13_060_000, "B": 13_070_000, "C": 13_080_000, "D": 13_090_000, "E": 13_095_000}
N = int(os.environ.get("N", "160"))
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


def certify_session(sess):
    """Returns (failed: bool, reasons: list)."""
    reasons = []
    target = sess.held_out["s0x"]["type"]
    assertion_met = False
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
        cand_feats = None
        with torch.no_grad():
            if cands:
                h_prompt = m(toks, return_hidden=20)[0].float()
                cand_feats = torch.stack([h_prompt[c[2][0]:c[2][1]].mean(dim=0) for c in cands])
            outs, text = [], ""
            for step in range(120):
                ab = None
                h20 = m(toks, return_hidden=20)[0, -1].float()
                probs = torch.softmax(head(h20), dim=-1)
                ci = int(probs[1:].argmax()) + 1
                if float(probs[ci]) > TAU and cands:
                    ty = CLASSES[ci]
                    typed = [i for i, c in enumerate(cands) if c[0] == ty]
                    live_val = sess.ledger_at[wt].get(ty)
                    has_live = any(cands[i][1] == live_val for i in typed) if live_val else False
                    if ty == target and typed and not has_live:
                        assertion_met = True
                    if typed:
                        q = F.normalize(Wq(h20), dim=0)
                        k = F.normalize(Wk(cand_feats.cuda()), dim=1)
                        cos = (q @ k.T)
                        j = max(typed, key=lambda i: float(cos[i]))
                        if float(cos[j]) > THR:
                            chosen_live = cands[j][1] == live_val and live_val is not None
                            if not chosen_live:
                                reasons.append(f"false-selection wt{wt} step{step} type {ty} value {cands[j][1]}")
                            # deployed behavior: apply the press if in-ledger
                            if ty in spans:
                                t = toks.shape[1]
                                bias = torch.zeros(t, t, device="cuda")
                                bias[-1:, cands[j][2][0]:cands[j][2][1]] = BETA
                                ab = {L: bias for L in LAYERS}
                nxt = int(m(toks, attn_bias=ab)[0, -1].argmax())
                outs.append(nxt)
                toks = torch.cat([toks, torch.tensor([[nxt]], device="cuda")], dim=1)
                text = tok.decode(outs)
                if "```" in text[-6:]:
                    break
        wr = score_work(text.split("```")[0], sess, wt)
        for i in range(wt + 1, len(sess.turns)):
            if sess.turns[i].kind == "env":
                feedback[i] = feedback_text(wr, sess)
                break
    if not assertion_met:
        reasons.append(f"s0x-assertion-missing target {target}")
    return bool(reasons), reasons


def main():
    seeds = [STARTS[BLOCK] + i for i in range(N)]
    failures = []
    for n, seed in enumerate(seeds):
        sess = generate_t2(seed, 20, "dev", interference="s0x")
        failed, reasons = certify_session(sess)
        if failed:
            failures.append({"seed": seed, "reasons": reasons})
            print(f"  FAIL {seed}: {reasons[:2]}", flush=True)
        if n % 20 == 0:
            print(f"  {n}/{N} sessions, {len(failures)} failures", flush=True)
    k = len(failures)
    u95 = clopper_pearson_upper(k, N)
    verdict = "PASS" if u95 <= 0.05 else "FAIL"
    out = {"block": BLOCK, "n": N, "k": k, "u95": round(u95, 5), "verdict": verdict,
           "policy": "timing-head+type-restricted-cos_max@0.6407741904258727+runner-guards",
           "failures": failures}
    (ROOT / "results" / "qwen" / f"g0-certify-{BLOCK}.json").write_text(json.dumps(out, indent=1))
    print(f"CERTIFICATION {verdict}: k={k}/{N}, U95={u95:.4f} (<= 0.05 required)", flush=True)
    print(f"saved results/qwen/g0-certify-{BLOCK}.json", flush=True)


if __name__ == "__main__":
    main()
