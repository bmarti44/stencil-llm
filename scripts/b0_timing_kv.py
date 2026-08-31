# ruff: noqa
"""B0 timing admission, KV-cached path (supersedes b0_timing.py's
full-forward numbers): same 20 NON-IFEval smoke prompts, pinned
template, greedy, max_new 1024, EOS {151645, 151643}. Base variant =
cached stepping; wave variant = cached stepping + capture_hidden=20 +
a bias row over prompt positions applied at layers 20-27 every step
(controller MLP cost is negligible vs the trunk; the row here is a
fixed random stand-in). Projects the five-arm 541-prompt sealed job."""
import json, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from stencil import determinism  # noqa: F401
import torch
from tokenizers import Tokenizer
from stencil.qwen3 import Qwen3, KVCache

TMPL = "<|im_start|>user\n{p}<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"
EOS = {151645, 151643}
PROMPTS = [f"Write a short paragraph about topic number {i}: describe it plainly for a general reader, with an example." for i in range(20)]

tok = Tokenizer.from_file(str(ROOT / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
m = Qwen3()
m.load_state_dict(torch.load(ROOT / "models" / "qwen3-1.7b.pt", map_location="cpu"), strict=True)
m = m.to(torch.bfloat16).cuda().eval()

def run(wave_style):
    lens, t0 = [], time.time()
    g = torch.Generator().manual_seed(3)
    for p in PROMPTS:
        ids = tok.encode(TMPL.format(p=p)).ids
        P = len(ids)
        row_vals = 2.0 * torch.rand(P, generator=g).cuda()
        cache = KVCache()
        n_gen = 0
        with torch.no_grad():
            ab = None
            if wave_style:
                b = torch.zeros(P, P, device="cuda"); b[-1, :P] = row_vals
                ab = {L: b for L in range(20, 28)}
            r = m(torch.tensor([ids], device="cuda"), cache=cache, attn_bias=ab,
                  capture_hidden=(20 if wave_style else None))
            logits = r[0] if wave_style else r
            nxt = int(logits[0, -1].argmax())
            while nxt not in EOS and n_gen < 1024:
                n_gen += 1
                ab = None
                if wave_style:
                    row = torch.zeros(1, cache.length + 1, device="cuda")
                    row[0, :P] = row_vals
                    ab = {L: row for L in range(20, 28)}
                r = m(torch.tensor([[nxt]], device="cuda"), cache=cache, attn_bias=ab,
                      capture_hidden=(20 if wave_style else None))
                logits = r[0] if wave_style else r
                nxt = int(logits[0, -1].argmax())
        lens.append(n_gen)
    return time.time() - t0, lens

base_t, lens = run(False)
wave_t, _ = run(True)
# five arms: base + wave-s0 + proxy-s0 + wave-s1 + proxy-s1 = 1 base-style + 4 wave-style
proj = (541/20) * (base_t * 1 + wave_t * 4) / 3600
out = {"base_20_s": round(base_t, 1), "wave_20_s": round(wave_t, 1),
       "gen_len_mean": round(sum(lens)/len(lens), 1), "gen_len_max": max(lens),
       "five_arm_541_projection_h": round(proj, 2)}
print(json.dumps(out, indent=1))
(ROOT / "results" / "qwen" / "b0-timing-kv.json").write_text(json.dumps(out, indent=1))
