# ruff: noqa
"""B3 gradient-connectivity battery (v4.1; sol checkpoint-iii
FINDING-4a; the registered w0-battery pattern on the REAL B3 loss):
fresh controller, one real training row, LAM=0 CE loss ->
(1) every controller parameter receives a finite NONZERO gradient;
(2) dCE/dbias is nonzero on the biased rows."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from stencil import determinism  # noqa: F401
import torch
import torch.nn.functional as F
from tokenizers import Tokenizer
from stencil.qwen3 import Qwen3
from stencil.wave import WaveController
from stencil.bench import TMPL, WAVE_LAYERS

tok = Tokenizer.from_file(str(ROOT / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
m = Qwen3()
m.load_state_dict(torch.load(ROOT / "models" / "qwen3-1.7b.pt", map_location="cpu"), strict=True)
m = m.to(torch.bfloat16).cuda().eval()
for p in m.parameters():
    p.requires_grad_(False)
row = json.loads(open(ROOT / "data" / "b3" / "train-2000.jsonl").readline())
enc = tok.encode(TMPL.format(p=row["prompt"])); P = len(enc.ids)
full = torch.tensor([enc.ids + tok.encode(row["canonical"]).ids], device="cuda")
T = full.shape[1]
torch.manual_seed(0)
wave = WaveController().cuda()
with torch.no_grad():
    h = m(full, return_hidden=20)[0].float()
out = {}
# (1) real-loss per-param grads
field = wave.field(h[P-1:T-1].detach(), h[:P].detach())
bias = torch.zeros(T, T, device="cuda")
bias[P-1:T-1, :P] = field
logits = m(full, attn_bias={L: bias for L in WAVE_LAYERS})[0].float()
ce = F.cross_entropy(logits[P-1:T-1], full[0, P:])
ce.backward()
for n, p in wave.named_parameters():
    g = p.grad
    out[f"grad_{n}"] = bool(g is not None and torch.isfinite(g).all() and float(g.abs().sum()) > 0)
# (2) nonzero dCE/dbias
b2 = torch.zeros(T, T, device="cuda", requires_grad=True)
logits2 = m(full, attn_bias={L: b2 for L in WAVE_LAYERS})[0].float()
ce2 = F.cross_entropy(logits2[P-1:T-1], full[0, P:])
ce2.backward()
gb = b2.grad[P-1:T-1, :P]
out["dCE_dbias_nonzero"] = bool(torch.isfinite(gb).all() and float(gb.abs().sum()) > 0)
out["PASS"] = all(out.values())
print(json.dumps(out, indent=1))
(ROOT / "results" / "qwen" / "b3-battery.json").write_text(json.dumps(out, indent=1))
