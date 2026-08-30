# ruff: noqa
"""W0 trainer — wave (CE-through-trunk) and matched proxy control.

OBJ=ce (wave) | OBJ=proxy (matched control: identical module/actuator,
timing BCE + span CE on the SAME rows — v3.1 C1'). BATTERY=1 runs the
G-W0a connectivity battery; SMOKE=1 the max-length memory/time smoke.

Semantics (registered): h20 = return_hidden=20 = layer-20 INPUT
(upstream of all biased layers; no circularity — verified in WORKLOG).
Single forward per work: layers 0-19 no-grad implicitly via detached
inputs is NOT possible with the current API, so the full forward runs
grad-enabled with trunk requires_grad=False (bias enters at 20-27; the
0-19 activations carry no grad because no parameter upstream requires
it and the bias does not touch them). K = h20[0:P] detached; H rows =
h20[P-1 : T-1] detached (controller inputs are features, not grad
paths — the gradient reaches the controller THROUGH THE BIAS, v3).
Loss: CE over canonical tokens + lambda*L1(gain), lambda 0.01 (sum).
Adam(1e-3), 20 epochs, 40 seeds, accum 8, shuffle seed 0, final ckpt.
"""
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from stencil import determinism  # noqa: F401
import torch
import torch.nn.functional as F
from tokenizers import Tokenizer

from stencil.qwen3 import Qwen3
from stencil.t2_runner import LAYERS, _oracle_moment, ledger_sentence_spans, prompt_at
from stencil.t2_sessions import generate_t2
from stencil.wave import WaveController
from stencil.wave_ref import canonical_code

NEUTRAL = "[checker] (no feedback available this session)"
OBJ = os.environ.get("OBJ", "ce")
BATTERY = bool(os.environ.get("BATTERY"))
SMOKE = bool(os.environ.get("SMOKE"))
TRAIN = [13_400_000 + i for i in range(40)]
LAM = 0.01

tok = Tokenizer.from_file(str(ROOT / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
m = Qwen3()
m.load_state_dict(torch.load(ROOT / "models" / "qwen3-1.7b.pt", map_location="cpu"), strict=True)
m = m.to(torch.bfloat16).cuda().eval()
for p in m.parameters():
    p.requires_grad_(False)


def work_batch(sess, wt):
    ptxt = prompt_at(sess, wt, "dev").replace(
        "[checker] (deterministic feedback on the previous submission is inserted here at run time)", NEUTRAL)
    enc = tok.encode(ptxt)
    P = len(enc.ids)
    code_ids = tok.encode(canonical_code(sess, wt)).ids
    full = torch.tensor([enc.ids + code_ids], device="cuda")
    spans = ledger_sentence_spans(ptxt, sess, wt, "dev", tok)
    # proxy labels: rows at governed moments + their authoritative span
    rows, text = [], ""
    led = sess.ledger_at[wt]
    for i, tid in enumerate(code_ids):
        key = _oracle_moment(text[-80:])
        if key is not None and key in led and key in spans:
            rows.append((P - 1 + i, spans[key]))
        text += tok.decode([tid])
    return full, P, rows


def forward_loss(wave, full, P, rows):
    T = full.shape[1]
    with torch.no_grad():
        h = m(full, return_hidden=20)[0].float()
    K = h[:P].detach()
    H = h[P - 1:T - 1].detach()          # rows generating tokens P..T-1
    field = wave.field(H, K)             # [G, P]
    if OBJ == "proxy":
        # matched control: timing BCE on gain logits + span CE on e-logits
        q = F.normalize(wave.W_q(H), dim=-1)
        k = F.normalize(wave.W_k(K), dim=-1)
        e = 8.0 * (q @ k.T)
        gain_logit = wave.w_g(H).squeeze(-1)
        pos = torch.zeros(H.shape[0], device="cuda")
        span_loss = torch.tensor(0.0, device="cuda")
        n_pos = 0
        for r, span in rows:
            g_row = r - (P - 1)
            pos[g_row] = 1.0
            tgt = torch.zeros(P, device="cuda")
            tgt[span[0]:span[1]] = 1.0 / (span[1] - span[0])
            span_loss = span_loss + torch.sum(-tgt * F.log_softmax(e[g_row], dim=-1))
            n_pos += 1
        bce = F.binary_cross_entropy_with_logits(gain_logit, pos, reduction="mean")
        return bce + (span_loss / max(1, n_pos))
    # wave: CE through the trunk
    bias = torch.zeros(T, T, device="cuda")
    bias[P - 1:T - 1, :P] = field
    logits = m(full, attn_bias={L: bias for L in LAYERS})[0].float()
    targets = full[0, P:]
    ce = F.cross_entropy(logits[P - 1:T - 1], targets)
    l1 = LAM * wave.gain(H).sum()
    return ce + l1


def battery():
    torch.manual_seed(0)
    wave = WaveController().cuda()
    sess = generate_t2(13_400_000, 20, "dev", interference="s0")
    full, P, rows = work_batch(sess, sess.work_turns[1])
    global OBJ
    OBJ = "ce"
    out = {}
    # (1) per-param finite nonzero grads with the REAL CE loss (no L1)
    lam_save, globals_l = None, None
    loss = forward_loss(wave, full, P, rows) - LAM * wave.gain(
        m(full, return_hidden=20)[0].float()[P - 1:full.shape[1] - 1].detach()).sum()
    loss.backward()
    for n, p in wave.named_parameters():
        g = p.grad
        out[f"grad_{n}"] = bool(g is not None and torch.isfinite(g).all() and float(g.abs().sum()) > 0)
    wave.zero_grad()
    # (2) nonzero dCE/dbias
    T = full.shape[1]
    with torch.no_grad():
        h = m(full, return_hidden=20)[0].float()
    bias = torch.zeros(T, T, device="cuda", requires_grad=True)
    logits = m(full, attn_bias={L: bias for L in LAYERS})[0].float()
    ce = F.cross_entropy(logits[P - 1:T - 1], full[0, P:])
    ce.backward()
    out["dCE_dbias_nonzero"] = bool(float(bias.grad.abs().sum()) > 0)
    # (3) detached bias FAILS (self-test)
    wave.zero_grad()
    K = h[:P].detach(); H = h[P - 1:T - 1].detach()
    field = wave.field(H, K).detach()          # deliberately severed
    bias2 = torch.zeros(T, T, device="cuda")
    bias2[P - 1:T - 1, :P] = field
    logits2 = m(full, attn_bias={L: bias2 for L in LAYERS})[0].float()
    ce2 = F.cross_entropy(logits2[P - 1:T - 1], full[0, P:])
    try:
        ce2.backward()
    except RuntimeError:
        pass
    out["detached_bias_fails"] = all(
        p.grad is None or float(p.grad.abs().sum()) == 0 for p in wave.parameters())
    # (4) zero field bitwise base-equivalent
    with torch.no_grad():
        zb = torch.zeros(T, T, device="cuda")
        lz = m(full, attn_bias={L: zb for L in LAYERS})
        lb = m(full)
    out["zero_field_bitwise_base"] = bool(torch.equal(lz, lb))
    # (5) wrong vs correct hand fields distinguishable
    with torch.no_grad():
        r0, span0 = rows[0]
        e = torch.full((P,), -6.0); e[span0[0]:span0[1]] = 6.0
        sm = torch.softmax(e, dim=-1); row_c = 2.0 * sm / sm.max()
        c_bias = torch.zeros(T, T, device="cuda"); c_bias[r0, :P] = row_c.cuda()
        e2 = torch.full((P,), -6.0); e2[span0[0] - 30:span0[0] - 30 + (span0[1] - span0[0])] = 6.0
        sm2 = torch.softmax(e2, dim=-1); row_w = 2.0 * sm2 / sm2.max()
        w_bias = torch.zeros(T, T, device="cuda"); w_bias[r0, :P] = row_w.cuda()
        lc = m(full, attn_bias={L: c_bias for L in LAYERS})[0, r0]
        lw = m(full, attn_bias={L: w_bias for L in LAYERS})[0, r0]
    out["positions_distinguishable"] = bool(float((lc - lw).abs().max()) > 1e-3)
    out["PASS"] = all(v for k, v in out.items() if k != "PASS")
    print(json.dumps(out, indent=1), flush=True)
    (ROOT / "results" / "qwen" / "w0-battery.json").write_text(json.dumps(out, indent=1))


def smoke():
    torch.manual_seed(0)
    wave = WaveController().cuda()
    # max-length synthetic work (registered max total 397 -> use 397)
    full = torch.randint(1000, 2000, (1, 397), device="cuda")
    t0 = time.time()
    loss = forward_loss(wave, full, 300, [(310, (10, 20))])
    loss.backward()
    torch.cuda.synchronize()
    peak = torch.cuda.max_memory_allocated() / 2**20
    print(json.dumps({"wall_s": round(time.time() - t0, 2), "peak_MiB": round(peak, 1)}), flush=True)


def main():
    if BATTERY:
        return battery()
    if SMOKE:
        return smoke()
    torch.manual_seed(0)
    wave = WaveController().cuda()
    opt = torch.optim.Adam(wave.parameters(), lr=1e-3, betas=(0.9, 0.999), eps=1e-8)
    works = []
    for seed in TRAIN:
        sess = generate_t2(seed, 20, "dev", interference="s0")
        works += [(sess, wt) for wt in sess.work_turns]
    g = torch.Generator().manual_seed(0)
    for ep in range(20):
        perm = torch.randperm(len(works), generator=g)
        opt.zero_grad()
        for step, j in enumerate(perm.tolist()):
            sess, wt = works[j]
            full, P, rows = work_batch(sess, wt)
            loss = forward_loss(wave, full, P, rows) / 8.0
            loss.backward()
            if (step + 1) % 8 == 0:
                opt.step(); opt.zero_grad()
        opt.step(); opt.zero_grad()
        print(f"epoch {ep} done", flush=True)
    name = f"w0-{OBJ}.pt"
    torch.save(wave.state_dict(), ROOT / "results" / "qwen" / name)
    print(f"saved results/qwen/{name}", flush=True)


if __name__ == "__main__":
    main()
