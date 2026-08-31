# ruff: noqa
"""Checkpoint-ii FINDING-6: long-output admission. 8 NON-IFEval prompts
that elicit long generations, cached wave-style stepping, max_new 1024.
Records tokens/sec at depth and the absolute worst-case ceiling
(541 prompts x 5 arms x max_new at the measured long-context rate)."""
import json, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from stencil import determinism  # noqa: F401
import torch
from tokenizers import Tokenizer
from stencil.qwen3 import Qwen3, KVCache
from stencil.bench import TMPL, EOS

PROMPTS = [f"Write a detailed essay of at least 700 words about aspect {i} of daily life in a small river town: routines, seasons, work, and change over a decade. Do not stop early." for i in range(8)]

tok = Tokenizer.from_file(str(ROOT / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
m = Qwen3()
m.load_state_dict(torch.load(ROOT / "models" / "qwen3-1.7b.pt", map_location="cpu"), strict=True)
m = m.to(torch.bfloat16).cuda().eval()

lens, per_prompt_s, t0 = [], [], time.time()
g = torch.Generator().manual_seed(5)
for p in PROMPTS:
    ids = tok.encode(TMPL.format(p=p)).ids
    P = len(ids)
    row_vals = 2.0 * torch.rand(P, generator=g).cuda()
    cache = KVCache(); n = 0
    with torch.no_grad():
        b = torch.zeros(P, P, device="cuda"); b[-1, :P] = row_vals
        logits = m(torch.tensor([ids], device="cuda"), cache=cache,
                   attn_bias={L: b for L in range(20, 28)}, capture_hidden=20)[0]
        nxt = int(logits[0, -1].argmax())
        while nxt not in EOS and n < 1024:
            n += 1
            row = torch.zeros(1, cache.length + 1, device="cuda"); row[0, :P] = row_vals
            logits = m(torch.tensor([[nxt]], device="cuda"), cache=cache,
                       attn_bias={L: row for L in range(20, 28)}, capture_hidden=20)[0]
            nxt = int(logits[0, -1].argmax())
    lens.append(n)
    per_prompt_s.append(round(time.time() - t0 - sum(per_prompt_s), 1))
wall = time.time() - t0
tot = sum(lens)
tps = tot / wall
ceiling_h = 541 * 5 * 1024 / tps / 3600
out = {"gen_lens": lens, "per_prompt_s": per_prompt_s,
       "slowest_prompt_s": max(per_prompt_s),
       "total_tokens": tot, "wall_s": round(wall, 1),
       "tokens_per_s_wave_style": round(tps, 2),
       "worst_case_ceiling_h_5x541xMAXNEW": round(ceiling_h, 1),
       "note": "ceiling assumes EVERY prompt hits max_new in EVERY arm; the sealed job registers crash-safe per-prompt persistence with resume-by-skip (no redraws)"}
print(json.dumps(out, indent=1))
(ROOT / "results" / "qwen" / "b0-timing-long.json").write_text(json.dumps(out, indent=1))
