# ruff: noqa
"""Checkpoint-ii FINDING-5: committed per-step KV-vs-full drift
diagnostics (fixture-local characterization, not a global bound).
Reuses the acceptance tests' own full_path_drift on the registered
fixture prompt, no-bias and wave-bias paths."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT))
from stencil import determinism  # noqa: F401
import torch
from tokenizers import Tokenizer
from stencil.qwen3 import Qwen3
from tests.test_qwen3_kv import PROMPT, STEPS, full_path_drift, make_rows

tok = Tokenizer.from_file(str(ROOT / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
m = Qwen3()
m.load_state_dict(torch.load(ROOT / "models" / "qwen3-1.7b.pt", map_location="cpu"), strict=True)
m = m.to(torch.bfloat16).cuda().eval()
ids = tok.encode(PROMPT).ids
out = {"prompt": PROMPT, "steps": STEPS,
       "note": ("fixture-local characterization of cached-vs-full bf16 kernel drift; "
                "argmax stability is guaranteed mathematically only where margin > 2*drift — "
                "the per-step agreement recorded here is an empirical observation")}
for name, rows in (("no_bias", None), ("wave_bias", make_rows(len(ids), STEPS))):
    diffs, margins, agree = full_path_drift(m, ids, rows)
    out[name] = {"max_abs_logit_diff_per_step": [round(d, 4) for d in diffs],
                 "full_path_top1_top2_margin_per_step": [round(g, 4) for g in margins],
                 "top1_agree_per_step": agree,
                 "max_diff": round(max(diffs), 4), "min_margin": round(min(margins), 4)}
print(json.dumps({k: v for k, v in out.items() if k in ("no_bias", "wave_bias")}, default=str)[:400])
(ROOT / "results" / "qwen" / "b0-kv-drift.json").write_text(json.dumps(out, indent=1))
