# ruff: noqa
"""W1 trainer (frozen: v3 W1 + v3.1 H3). OBJ=ce | OBJ=proxy (recurrent
proxy twin, H1'). Per SESSION: works in order; state carried across
works with DETACH at work-turn boundaries; full BPTT within a work; ONE
optimizer step per session. h20 rows precomputed per work (single
trunk forward); the GRU rolls over rows sequentially building the
field. Loss per v3: CE over canonical tokens through the trunk + L1
gain (ce) | timing BCE + span CE on the same rows (proxy). Adam(1e-3),
20 epochs, 40 train seeds, shuffle seed 0, final checkpoint.
"""
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
from stencil.t2_runner import LAYERS, _oracle_moment, ledger_sentence_spans, prompt_at
from stencil.t2_sessions import generate_t2
from stencil.wave import WaveRNN
from stencil.wave_ref import canonical_code

NEUTRAL = "[checker] (no feedback available this session)"
OBJ = os.environ.get("OBJ", "ce")
TRAIN = [13_400_000 + i for i in range(40)]
LAM = 0.01

tok = Tokenizer.from_file(str(ROOT / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
m = Qwen3()
m.load_state_dict(torch.load(ROOT / "models" / "qwen3-1.7b.pt", map_location="cpu"), strict=True)
m = m.to(torch.bfloat16).cuda().eval()
for p in m.parameters():
    p.requires_grad_(False)


def work_pack(sess, wt):
    ptxt = prompt_at(sess, wt, "dev").replace(
        "[checker] (deterministic feedback on the previous submission is inserted here at run time)", NEUTRAL)
    enc = tok.encode(ptxt)
    P = len(enc.ids)
    code_ids = tok.encode(canonical_code(sess, wt)).ids
    full = torch.tensor([enc.ids + code_ids], device="cuda")
    spans = ledger_sentence_spans(ptxt, sess, wt, "dev", tok)
    rows, text = [], ""
    led = sess.ledger_at[wt]
    for i, tid in enumerate(code_ids):
        key = _oracle_moment(text[-80:])
        if key is not None and key in led and key in spans:
            rows.append((i, spans[key]))  # index within generation rows
        text += tok.decode([tid])
    return full, P, rows


def session_loss(wave, sess, s0=None):
    s = wave.init_state().cuda() if s0 is None else s0
    total = torch.tensor(0.0, device="cuda")
    for wt in sess.work_turns:
        full, P, rows = work_pack(sess, wt)
        T = full.shape[1]
        with torch.no_grad():
            h = m(full, return_hidden=20)[0].float()
        K = h[:P].detach()
        H = h[P - 1:T - 1].detach()
        G = H.shape[0]
        field_rows, gains, gain_logits, e_rows = [], [], [], []
        for i in range(G):
            b, s = wave.step(H[i], s, K)
            field_rows.append(b)
            gains.append(b.max())
            if OBJ == "proxy":
                x = torch.cat([H[i], s])
                gain_logits.append(wave.w_g(x).squeeze(-1))
                q = F.normalize(wave.W_q(x), dim=-1)
                k = F.normalize(wave.W_k(K), dim=-1)
                e_rows.append(8.0 * (q @ k.T))
        field = torch.stack(field_rows)
        if OBJ == "proxy":
            pos = torch.zeros(G, device="cuda")
            span_loss = torch.tensor(0.0, device="cuda")
            n_pos = 0
            for i, span in rows:
                pos[i] = 1.0
                tgt = torch.zeros(P, device="cuda")
                tgt[span[0]:span[1]] = 1.0 / (span[1] - span[0])
                span_loss = span_loss + torch.sum(-tgt * F.log_softmax(e_rows[i], dim=-1))
                n_pos += 1
            total = total + F.binary_cross_entropy_with_logits(
                torch.stack(gain_logits), pos, reduction="mean") + span_loss / max(1, n_pos)
        else:
            bias = torch.zeros(T, T, device="cuda")
            bias[P - 1:T - 1, :P] = field
            logits = m(full, attn_bias={L: bias for L in LAYERS})[0].float()
            total = total + F.cross_entropy(logits[P - 1:T - 1], full[0, P:]) + LAM * torch.stack(gains).sum()
        s = s.detach()  # registered: detach across work turns
    return total


def main():
    torch.manual_seed(0)
    wave = WaveRNN().cuda()
    opt = torch.optim.Adam(wave.parameters(), lr=1e-3, betas=(0.9, 0.999), eps=1e-8)
    g = torch.Generator().manual_seed(0)
    for ep in range(20):
        perm = torch.randperm(len(TRAIN), generator=g)
        for j in perm.tolist():
            sess = generate_t2(TRAIN[j], 20, "dev", interference="s0")
            loss = session_loss(wave, sess)
            opt.zero_grad(); loss.backward(); opt.step()
        print(f"epoch {ep} done", flush=True)
    name = f"w1-{OBJ}.pt"
    torch.save(wave.state_dict(), ROOT / "results" / "qwen" / name)
    print(f"saved results/qwen/{name}", flush=True)


if __name__ == "__main__":
    main()
