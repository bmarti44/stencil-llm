# ruff: noqa
"""W3b NULL-threshold calibration (frozen, w3 prereg v3): grid theta in
{0.05..0.95 step 0.05} * beta_max over the wave's gain; maximize
ACTIVE-vs-NULL balanced accuracy on held W0 seeds (13,400,040..47);
ties -> HIGHER threshold. Positive steps = generation steps at
parser-identified governed moments whose type is active; negatives =
all other steps. Computed ONCE; recorded in WORKLOG before the record
run. Data: the wave's own generation rollouts on held seeds.
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
from stencil.t2_runner import LAYERS, _oracle_moment, build_arm_prompt, ledger_sentence_spans
from stencil.t2_sessions import generate_t2
from stencil.wave import WaveController

NEUTRAL = "[checker] (no feedback available this session)"
HELD = [13_400_040 + i for i in range(8)]

tok = Tokenizer.from_file(str(ROOT / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
m = Qwen3()
m.load_state_dict(torch.load(ROOT / "models" / "qwen3-1.7b.pt", map_location="cpu"), strict=True)
m = m.to(torch.bfloat16).cuda().eval()
wave = WaveController().cuda()
wave.load_state_dict(torch.load(ROOT / "results" / "qwen" / "w0-ce.pt", map_location="cpu"))
wave.eval()


def main():
    rows = []  # (gain, is_positive)
    for seed in HELD:
        sess = generate_t2(seed, 20, "dev", interference="s0")
        for wt in sess.work_turns:
            ptxt = build_arm_prompt(sess, wt, "dev", "base").replace(
                "[checker] (deterministic feedback on the previous submission is inserted here at run time)", NEUTRAL)
            enc = tok.encode(ptxt)
            P = len(enc.ids)
            led = sess.ledger_at[wt]
            toks = torch.tensor([enc.ids], device="cuda")
            gen, text = [], ""
            with torch.no_grad():
                K = m(toks, return_hidden=20)[0].float()[:P]
                for _ in range(120):
                    h_t = m(toks, return_hidden=20)[0, -1].float()
                    row = wave(h_t, K)
                    g = float(row.max())
                    key = _oracle_moment(text[-80:])
                    pos = key is not None and key in led
                    rows.append((g, pos))
                    t = toks.shape[1]
                    bias = torch.zeros(t, t, device="cuda")
                    bias[-1, :P] = row
                    nxt = int(m(toks, attn_bias={L: bias for L in LAYERS})[0, -1].argmax())
                    gen.append(nxt)
                    toks = torch.cat([toks, torch.tensor([[nxt]], device="cuda")], dim=1)
                    text = tok.decode(gen)
                    if "```" in text[-6:]:
                        break
    n_pos = sum(1 for _, p in rows if p)
    n_neg = len(rows) - n_pos
    best = None
    for i in range(1, 20):
        theta = round(0.05 * i, 2) * 2.0  # * beta_max
        tp = sum(1 for g, p in rows if p and g > theta)
        tn = sum(1 for g, p in rows if not p and g <= theta)
        ba = 0.5 * (tp / max(1, n_pos) + tn / max(1, n_neg))
        if best is None or ba > best["ba"] or (ba == best["ba"] and theta > best["theta"]):
            best = {"theta": theta, "ba": round(ba, 4), "tp": tp, "tn": tn}
    out = {"n_steps": len(rows), "n_pos": n_pos, "n_neg": n_neg, **best}
    print(json.dumps(out, indent=1), flush=True)
    (ROOT / "results" / "qwen" / "w3-null-theta.json").write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
