# ruff: noqa
"""v4.3 base texts: the FROZEN trunk's own greedy responses to each
topic task (no constraints) — canonicals are then MINIMAL EDITS of
these, so CE is low except at obligation positions (sol's curation
prescription). 40 topics x 3 task phrasings = 120 texts, committed
with sha. Deterministic (greedy, pinned template)."""
import json, hashlib, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from stencil import determinism  # noqa: F401
import torch
from tokenizers import Tokenizer
from stencil.b3_gen import TOPICS
from stencil.bench import generate_cached
from stencil.qwen3 import Qwen3

TASKS = [
    "Write a short account of {t} for a neighborhood newsletter.",
    "Write a brief note about {t} for a community bulletin.",
    "Describe {t} in a few short paragraphs for local readers.",
]

tok = Tokenizer.from_file(str(ROOT / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
m = Qwen3()
m.load_state_dict(torch.load(ROOT / "models" / "qwen3-1.7b.pt", map_location="cpu"), strict=True)
m = m.to(torch.bfloat16).cuda().eval()

out = {}
for ti, topic in enumerate(TOPICS):
    for si, task in enumerate(TASKS):
        text, n, trunc, to = generate_cached(m, tok, task.format(t=topic), max_new=220)
        out[f"{ti}:{si}"] = {"topic": topic, "task": task.format(t=topic), "text": text.strip(),
                             "n_gen": n, "truncated": bool(trunc)}
        if (ti * 3 + si) % 15 == 0:
            print(f"{ti*3+si}/120", flush=True)
p = ROOT / "data" / "b3" / "base-texts.json"
p.write_text(json.dumps(out, indent=1, ensure_ascii=False))
print("sha", hashlib.sha256(p.read_bytes()).hexdigest()[:16], "truncated:",
      sum(v["truncated"] for v in out.values()))
