# ruff: noqa
"""B3 trainer — benchmark wave (CE-through-frozen-trunk) and row-matched
proxy twin, per the v3.2 FROZEN schedule: Adam(1e-3, (0.9,0.999), 1e-8),
5 epochs over data/b3/train-2000.jsonl, accumulation 8, shuffle seed 0,
controller seeds s0=0 / s1=1, checkpoint per epoch, SELECTED by lowest
UNROUNDED dev-200 TASK CE — objective-independent: each controller's
field through the frozen trunk, CE only (no gain penalty, no proxy
losses) — tie-break: lowest epoch index (round-3 FINDING-2 closure).

OBJ=ce|proxy SEED=0|1. Wave semantics identical to w0_train.py: h20 =
layer-20 input; K = prompt rows detached; H = generating rows detached;
gradient reaches the controller THROUGH THE BIAS; teacher-forced rows
P-1..T-2 biased over prompt columns (deployment = same-position
bias_hook, registered v3.1). Proxy (registered v3.1/3.2): BCE(gain
logits, all-response-rows positive) + mean uniform-within-span CE of
e-logits toward constraint_spans(), weight 1:1, identical rows/data/
schedule. SMOKE=1: 4 rows, 1 epoch, no artifacts sealed.
"""
import json
import hashlib
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

from stencil.b3_gen import constraint_spans
from stencil.bench import TMPL, WAVE_LAYERS
from stencil.qwen3 import Qwen3
from stencil.wave import WaveController

OBJ = os.environ.get("OBJ", "ce")
SEED = int(os.environ.get("SEED", "0"))
SMOKE = bool(os.environ.get("SMOKE"))
LAM = 0.0  # v3.3: L1 gain penalty REMOVED for B3 (collapse evidence, WORKLOG 2026-08-31)
EPOCHS = 1 if SMOKE else 5
ACCUM = 8

assert OBJ in ("ce", "proxy")

tok = Tokenizer.from_file(str(ROOT / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
m = Qwen3()
m.load_state_dict(torch.load(ROOT / "models" / "qwen3-1.7b.pt", map_location="cpu"), strict=True)
m = m.to(torch.bfloat16).cuda().eval()
for p in m.parameters():
    p.requires_grad_(False)


def load_rows(name):
    return [json.loads(line) for line in open(ROOT / "data" / "b3" / name)]


def encode_row(row):
    """(full ids tensor, P, span list) for one training row."""
    ptxt = TMPL.format(p=row["prompt"])
    enc = tok.encode(ptxt)
    P = len(enc.ids)
    code_ids = tok.encode(row["canonical"]).ids
    full = torch.tensor([enc.ids + code_ids], device="cuda")
    # constraint spans are indexed on the BARE prompt encoding; shift by
    # the template prefix length before the {p} slot
    prefix = TMPL.split("{p}")[0]
    off = len(tok.encode(prefix).ids)
    spans = [(a + off, b + off) for (a, b) in constraint_spans(row, tok).values()]
    return full, P, spans


def forward_loss(wave, full, P, spans):
    T = full.shape[1]
    with torch.no_grad():
        h = m(full, return_hidden=20)[0].float()
    K = h[:P].detach()
    H = h[P - 1:T - 1].detach()
    if OBJ == "proxy":
        q = F.normalize(wave.W_q(H), dim=-1)
        k = F.normalize(wave.W_k(K), dim=-1)
        e = 8.0 * (q @ k.T)
        gain_logit = wave.w_g(H).squeeze(-1)
        pos = torch.ones(H.shape[0], device="cuda")  # all response rows positive
        bce = F.binary_cross_entropy_with_logits(gain_logit, pos, reduction="mean")
        span_loss = torch.tensor(0.0, device="cuda")
        for a, b in spans:
            b = min(b, P)
            tgt = torch.zeros(P, device="cuda")
            tgt[a:b] = 1.0 / (b - a)
            span_loss = span_loss + torch.mean(torch.sum(-tgt * F.log_softmax(e, dim=-1), dim=-1))
        return bce + span_loss / max(1, len(spans))
    field = wave.field(H, K)
    bias = torch.zeros(T, T, device="cuda")
    bias[P - 1:T - 1, :P] = field
    logits = m(full, attn_bias={L: bias for L in WAVE_LAYERS})[0].float()
    targets = full[0, P:]
    ce = F.cross_entropy(logits[P - 1:T - 1], targets)
    return ce if LAM == 0 else ce + LAM * wave.gain(H).sum()


def task_ce(wave, full, P):
    """objective-INDEPENDENT selection metric: this controller's field
    through the frozen trunk, plain CE on the canonical tokens."""
    T = full.shape[1]
    h = m(full, return_hidden=20)[0].float()
    field = wave.field(h[P - 1:T - 1], h[:P])
    bias = torch.zeros(T, T, device="cuda")
    bias[P - 1:T - 1, :P] = field
    logits = m(full, attn_bias={L: bias for L in WAVE_LAYERS})[0].float()
    return float(F.cross_entropy(logits[P - 1:T - 1], full[0, P:]))


def dev_task_ce(wave, dev_rows):
    tot = 0.0
    for row in dev_rows:
        full, P, _ = encode_row(row)
        with torch.no_grad():
            tot += task_ce(wave, full, P)
    return tot / len(dev_rows)


def main():
    train = load_rows("train-2000.jsonl")
    dev = load_rows("dev-200.jsonl")
    if SMOKE:
        train, dev = train[:4], dev[:2]
    torch.manual_seed(SEED)
    wave = WaveController().cuda()
    opt = torch.optim.Adam(wave.parameters(), lr=1e-3, betas=(0.9, 0.999), eps=1e-8)
    g = torch.Generator().manual_seed(0)  # frozen shuffle seed
    rec = {"obj": OBJ, "seed": SEED, "epochs": [],
           "data_sha256": {n: hashlib.sha256((ROOT / "data" / "b3" / n).read_bytes()).hexdigest()
                           for n in ("train-2000.jsonl", "dev-200.jsonl")},
           "trainer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    t0 = time.time()
    for ep in range(EPOCHS):
        perm = torch.randperm(len(train), generator=g).tolist()
        run, nstep = 0.0, 0
        opt.zero_grad()
        for j, idx in enumerate(perm):
            full, P, spans = encode_row(train[idx])
            loss = forward_loss(wave, full, P, spans) / ACCUM
            loss.backward()
            run += float(loss) * ACCUM
            nstep += 1
            if (j + 1) % ACCUM == 0:
                opt.step()
                opt.zero_grad()
            if j % 200 == 0:
                print(f"ep{ep} {j}/{len(perm)} loss {run / max(1, nstep):.4f} "
                      f"({time.time() - t0:.0f}s)", flush=True)
        opt.step()
        opt.zero_grad()
        d = dev_task_ce(wave, dev)
        ck = ROOT / "results" / "qwen" / f"b3-{OBJ}-s{SEED}-ep{ep}.pt"
        if not SMOKE:
            torch.save(wave.state_dict(), ck)
        rec["epochs"].append({"epoch": ep, "train_loss": round(run / nstep, 4),
                              "dev_task_ce": d})  # UNROUNDED (selection metric)
        print(f"epoch {ep}: train {run / nstep:.4f} dev_task_ce {d:.6f}", flush=True)
    # frozen selection: lowest unrounded dev task CE; tie-break lowest epoch
    best = min(rec["epochs"], key=lambda e: (e["dev_task_ce"], e["epoch"]))["epoch"]
    rec["selected_epoch"] = best
    if not SMOKE:
        sel = ROOT / "results" / "qwen" / f"b3-{OBJ}-s{SEED}.pt"
        sel.write_bytes((ROOT / "results" / "qwen" / f"b3-{OBJ}-s{SEED}-ep{best}.pt").read_bytes())
        rec["selected_sha256"] = hashlib.sha256(sel.read_bytes()).hexdigest()
        (ROOT / "results" / "qwen" / f"b3-{OBJ}-s{SEED}.json").write_text(json.dumps(rec, indent=1))
    print(json.dumps(rec["epochs"], indent=1))
    print("selected epoch", best)


if __name__ == "__main__":
    main()
