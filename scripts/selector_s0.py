# ruff: noqa
"""S0 admission: base Qwen on the governance/interference task.
Gate: accuracy in 40-80% with selection-shaped errors (stale echoes)."""
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from tokenizers import Tokenizer

from stencil.qwen3 import Qwen3
from stencil.qwen_task import generate_governance

tok = Tokenizer.from_file(str(ROOT / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
m = Qwen3()
m.load_state_dict(torch.load(ROOT / "models" / "qwen3-1.7b.pt", map_location="cpu"), strict=True)
m = m.to(torch.bfloat16).cuda().eval()

n = 64
hits = stale_echo = other = 0
with torch.no_grad():
    for i in range(n):
        s = generate_governance(11_000_000 + i)
        toks = torch.tensor([tok.encode(s.text).ids], device="cuda")
        outs = []
        for _ in range(20):
            nxt = int(m(toks)[0, -1].argmax())
            outs.append(nxt)
            toks = torch.cat([toks, torch.tensor([[nxt]], device="cuda")], dim=1)
        gen = tok.decode(outs).strip().split("\n")[0].strip().rstrip(".")
        if gen == s.value:
            hits += 1
        elif gen in s.stale_values:
            stale_echo += 1
        else:
            other += 1
            if other <= 3:
                print(f"  other-error ex{i}: want {s.value!r} got {gen!r}")
print(f"S0 BASE: correct {hits}/{n} = {hits/n:.2f} | stale-echo {stale_echo} | other {other}")
print(f"gate: 0.40 <= acc <= 0.80 -> {'PASS' if 0.40 <= hits/n <= 0.80 else 'MISS'}")
