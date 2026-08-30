# ruff: noqa
"""PRESS-PLAN sealed certification job — FAIL-CLOSED (impl review r2).

One policy, one block, one run. Block and N are HARD-CODED (no env
knobs); artifact hashes are pinned and checked; a .started marker makes
reruns refuse; the result is written atomically. Block A was
administratively VOIDED (reviewer instantiated its sessions during
audit); the named policy certifies on block D per WORKLOG naming.

Named policy: supervised timing head (fires at prob > tau) +
type-restricted cos_max address + threshold 0.6407741904258727 + runner
guards. Failure/press semantics are provenance-by-span via
press_certify.certify_decision (STRICTER than trace-time value-level
selection — disclosed). The s0x non-vacuity assertion binds to the
session's targeted work turn (press_certify.s0x_assertion_hit).
"""
import hashlib
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

from stencil.press_certify import certify_decision, s0x_assertion_hit
from stencil.press_stats import clopper_pearson_upper
from stencil.qwen3 import Qwen3
from stencil.t2_runner import BETA, LAYERS, feedback_text, ledger_sentence_spans, prompt_at, score_work
from stencil.t2_select import candidate_spans
from stencil.t2_sessions import generate_t2

BLOCK = "D"                      # hard-coded; block A voided, see WORKLOG
SEED0, N = 13_090_000, 160
THR = 0.6407741904258727
CLASSES = ["none", "prefix", "doc", "hint"]
PINNED = {
    "results/qwen/t2b-selector.pt": "e9922d703cbcf1a4f2cc127dab134ce44f679871df72949c9c8833047f08104f",
    "models/qwen3-1.7b.pt": "13bfabb5592c7b35383a56471fba1c74c771f57587322e60faaabb96268b2829",
    "models/qwen3-1.7b-hf/tokenizer.json": "aeb13307a71acd8fe81861d94ad54ab689df773318809eed3cbe794b4492dae4",
}


def certify_session(m, tok, head, Wq, Wk, tau, sess):
    reasons = []
    target = sess.held_out["s0x"]
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
                if float(probs[ci]) > tau and cands:
                    ty = CLASSES[ci]
                    typed = [i for i, c in enumerate(cands) if c[0] == ty]
                    if s0x_assertion_hit(wt, ty, target, typed, cands, spans):
                        assertion_met = True
                    if typed:
                        q = F.normalize(Wq(h20), dim=0)
                        k = F.normalize(Wk(cand_feats.cuda()), dim=1)
                        cos = q @ k.T
                        j = max(typed, key=lambda i: float(cos[i]))
                        verdict = certify_decision(float(cos[j]), THR, cands[j][2], spans)
                        if verdict == "false-selection":
                            reasons.append(f"false-selection wt{wt} step{step} type {ty} value {cands[j][1]} span {cands[j][2]}")
                        elif verdict == "press":
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
        reasons.append(f"s0x-assertion-missing target {target['type']} wt {target['work_turn']}")
    return bool(reasons), reasons


def main():
    out_path = ROOT / "results" / "qwen" / f"g0-certify-{BLOCK}.json"
    marker = ROOT / "results" / "qwen" / f"g0-certify-{BLOCK}.started"
    if out_path.exists() or marker.exists():
        sys.exit(f"REFUSED: {out_path.name} or {marker.name} exists — sealed job already started/finished")
    for rel, want in PINNED.items():
        got = hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
        if got != want:
            sys.exit(f"REFUSED: hash mismatch for {rel}: {got[:12]} != pinned {want[:12]}")
    marker.write_text("started")

    tok = Tokenizer.from_file(str(ROOT / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
    m = Qwen3()
    m.load_state_dict(torch.load(ROOT / "models" / "qwen3-1.7b.pt", map_location="cpu"), strict=True)
    m = m.to(torch.bfloat16).cuda().eval()
    sel = torch.load(ROOT / "results" / "qwen" / "t2b-selector.pt", map_location="cpu")
    head = torch.nn.Linear(2048, 4); head.load_state_dict(sel["head"]); head = head.cuda()
    Wq = torch.nn.Linear(2048, 64); Wq.load_state_dict(sel["Wq"]); Wq = Wq.cuda()
    Wk = torch.nn.Linear(2048, 64); Wk.load_state_dict(sel["Wk"]); Wk = Wk.cuda()

    failures = []
    for n in range(N):
        seed = SEED0 + n
        sess = generate_t2(seed, 20, "dev", interference="s0x")
        failed, reasons = certify_session(m, tok, head, Wq, Wk, sel["tau"], sess)
        if failed:
            failures.append({"seed": seed, "reasons": reasons})
            print(f"  FAIL {seed}: {reasons[:2]}", flush=True)
        if n % 20 == 0:
            print(f"  {n}/{N} sessions, {len(failures)} failures", flush=True)
    k = len(failures)
    u95 = clopper_pearson_upper(k, N)
    verdict = "PASS" if u95 <= 0.05 else "FAIL"
    out = {"block": BLOCK, "seed0": SEED0, "n": N, "k": k, "u95": round(u95, 5), "verdict": verdict,
           "policy": "timing-head+type-restricted-cos_max@0.6407741904258727+runner-guards",
           "semantics": "provenance-by-span (stricter than trace-time value-level selection; disclosed)",
           "pinned": PINNED, "failures": failures}
    tmp = str(out_path) + ".partial"
    Path(tmp).write_text(json.dumps(out, indent=1))
    os.replace(tmp, out_path)
    print(f"CERTIFICATION {verdict}: k={k}/{N}, U95={u95:.4f} (<= 0.05 required)", flush=True)
    print(f"saved {out_path.relative_to(ROOT)}", flush=True)


if __name__ == "__main__":
    main()
