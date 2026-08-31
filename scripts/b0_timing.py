# ruff: noqa
"""B0 timing admission (pre-B4 requirement): 20 NON-IFEval smoke
prompts through the pinned template, greedy, max_new candidate 1024,
EOS {151645, 151643}; measures wall time for base and wave-style
(2-forward) stepping; projects the five-arm 541-prompt sealed job."""
import json, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from stencil import determinism  # noqa: F401
import torch
from tokenizers import Tokenizer
from stencil.qwen3 import Qwen3

TMPL = "<|im_start|>user\n{p}<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"
EOS = {151645, 151643}
PROMPTS = [f"Write a short paragraph about topic number {i}: describe it plainly for a general reader, with an example." for i in range(20)]

tok = Tokenizer.from_file(str(ROOT / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
m = Qwen3()
m.load_state_dict(torch.load(ROOT / "models" / "qwen3-1.7b.pt", map_location="cpu"), strict=True)
m = m.to(torch.bfloat16).cuda().eval()

def run(two_forward):
    lens, t0 = [], time.time()
    for p in PROMPTS:
        ids = tok.encode(TMPL.format(p=p)).ids
        toks = torch.tensor([ids], device="cuda")
        with torch.no_grad():
            for _ in range(1024):
                if two_forward:
                    _ = m(toks, return_hidden=20)
                nxt = int(m(toks)[0, -1].argmax())
                if nxt in EOS:
                    break
                toks = torch.cat([toks, torch.tensor([[nxt]], device="cuda")], dim=1)
        lens.append(toks.shape[1] - len(ids))
    return time.time() - t0, lens

base_t, lens = run(False)
wave_t, _ = run(True)
proj = (541/20) * (base_t * 3 + wave_t * 2) / 3600  # base+proxy... arms: base + 2 waves + 2 proxies = 1x base-style + 4x two-forward
proj = (541/20) * (base_t * 1 + wave_t * 4) / 3600
out = {"base_20_s": round(base_t, 1), "wave_20_s": round(wave_t, 1),
       "gen_len_mean": round(sum(lens)/len(lens), 1), "gen_len_max": max(lens),
       "five_arm_541_projection_h": round(proj, 2)}
print(json.dumps(out, indent=1))
(ROOT / "results" / "qwen" / "b0-timing.json").write_text(json.dumps(out, indent=1))
