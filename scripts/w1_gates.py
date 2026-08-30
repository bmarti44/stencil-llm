# ruff: noqa
"""W1 gates (v3 W1 + v3.1 H2'): held CE (>= 10% improve) + the frozen
CE-procedure temporal probes — teacher-forced canonical prefixes, h20
FIXED; (a) predecessor-state PERMUTATION: swap the s-input sequences
across matched sessions; (b) matched RESET: s_prev = init at every
step. Each must degrade held CE >= 10% RELATIVE to the wave's gain...
registered: ">= 10% relative" CE degradation (vs the intact wave's CE).
CKPT env (w1-ce.pt default).
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

import w1_train as W  # safe: model at top level, work under main()
from stencil.t2_sessions import generate_t2
from stencil.wave import WaveRNN

CKPT = os.environ.get("CKPT", "w1-ce.pt")
HELD = [13_400_040 + i for i in range(8)]
m, tok = W.m, W.tok


def session_ces(wave, sess, mode="intact", donor_states=None):
    """teacher-forced canonical CE per work; state handling per mode.
    Returns (ces, s_trace) where s_trace records the s_prev input at
    each step (for donor permutation)."""
    s = wave.init_state().cuda()
    ces, s_trace = [], []
    di = 0
    for wt in sess.work_turns:
        full, P, _ = W.work_pack(sess, wt)
        T = full.shape[1]
        with torch.no_grad():
            h = m(full, return_hidden=20)[0].float()
            K = h[:P]
            H = h[P - 1:T - 1]
            rows = []
            for i in range(H.shape[0]):
                s_in = s
                if mode == "reset":
                    s_in = wave.init_state().cuda()
                elif mode == "permute":
                    s_in = donor_states[di % len(donor_states)]
                    di += 1
                s_trace.append(s_in)
                b, s = wave.step(H[i], s_in, K)
                rows.append(b)
            bias = torch.zeros(T, T, device="cuda")
            bias[P - 1:T - 1, :P] = torch.stack(rows)
            logits = m(full, attn_bias={L: bias for L in W.LAYERS})[0].float()
            ces.append(float(F.cross_entropy(logits[P - 1:T - 1], full[0, P:])))
        s = s.detach()
    return ces, s_trace


def battery():
    """G-W1a: real-CE connectivity incl. GRU params (registered)."""
    torch.manual_seed(0)
    wave = WaveRNN().cuda()
    sess = generate_t2(13_400_000, 20, "dev", interference="s0")
    wt = sess.work_turns[1]
    full, P, _ = W.work_pack(sess, wt)
    T = full.shape[1]
    with torch.no_grad():
        h = m(full, return_hidden=20)[0].float()
    K = h[:P].detach(); H = h[P - 1:T - 1].detach()
    s_st = wave.init_state().cuda()
    rows = []
    for i in range(H.shape[0]):
        b, s_st = wave.step(H[i], s_st, K)
        rows.append(b)
    bias = torch.zeros(T, T, device="cuda")
    bias[P - 1:T - 1, :P] = torch.stack(rows)
    logits = m(full, attn_bias={L: bias for L in W.LAYERS})[0].float()
    ce = F.cross_entropy(logits[P - 1:T - 1], full[0, P:])
    ce.backward()
    out = {}
    for n, prm in wave.named_parameters():
        g = prm.grad
        out[f"grad_{n}"] = bool(g is not None and torch.isfinite(g).all() and float(g.abs().sum()) > 0)
    out["PASS"] = all(out.values())
    print(json.dumps(out, indent=1), flush=True)
    (ROOT / "results" / "qwen" / "w1-battery.json").write_text(json.dumps(out, indent=1))


def main():
    if os.environ.get("BATTERY"):
        return battery()
    wave = WaveRNN().cuda()
    wave.load_state_dict(torch.load(ROOT / "results" / "qwen" / CKPT, map_location="cpu"))
    wave.eval()
    zero_ces, intact, reset, perm = [], [], [], []
    traces = {}
    sessions = [generate_t2(seed, 20, "dev", interference="s0") for seed in HELD]
    for sess in sessions:
        # zero-field baseline
        for wt in sess.work_turns:
            full, P, _ = W.work_pack(sess, wt)
            with torch.no_grad():
                lz = m(full)[0].float()
            zero_ces.append(float(F.cross_entropy(lz[P - 1:full.shape[1] - 1], full[0, P:])))
        ces, tr = session_ces(wave, sess, "intact")
        intact += ces
        traces[sess.seed] = tr
    # matched-session donor permutation: donor = the NEXT held session's trace
    for i, sess in enumerate(sessions):
        donor = traces[sessions[(i + 1) % len(sessions)].seed]
        ces, _ = session_ces(wave, sess, "permute", donor_states=donor)
        perm += ces
        ces_r, _ = session_ces(wave, sess, "reset")
        reset += ces_r
    z = sum(zero_ces) / len(zero_ces)
    it = sum(intact) / len(intact)
    pe = sum(perm) / len(perm)
    re = sum(reset) / len(reset)
    rep = {"ckpt": CKPT, "zero_ce": round(z, 4), "intact_ce": round(it, 4),
           "permute_ce": round(pe, 4), "reset_ce": round(re, 4),
           "held_improve": round((z - it) / z, 4),
           "permute_degrade_rel": round((pe - it) / it, 4),
           "reset_degrade_rel": round((re - it) / it, 4)}
    rep["G_W1c_ce"] = rep["held_improve"] >= 0.10
    rep["temporal_ce_permute"] = rep["permute_degrade_rel"] >= 0.10
    rep["temporal_ce_reset"] = rep["reset_degrade_rel"] >= 0.10
    print(json.dumps(rep, indent=1), flush=True)
    (ROOT / "results" / "qwen" / f"w1-gates-{CKPT.replace('.pt','')}.json").write_text(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()
