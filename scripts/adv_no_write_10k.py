# ruff: noqa
"""The 10k-token adversarial no-write measurement the goal-review registered
(H1): quoted slot words + instruction-adjacent phrasing, LEARNED gates,
trained cache-v8 checkpoint. Reports writes per 10k tokens (honest number,
not an assertion)."""
import sys
import torch
sys.path.insert(0, "/home/bmarti44/stencil-llm/src")
sys.path.insert(0, "/home/bmarti44/stencil-llm/scripts")
import run_gpt2_arms as R
from stencil.nl_task import BPE

DEV = R.DEV
m = R.build("cache", 0)
ck = torch.load("results/gpt2/cache-v8-s0-ckpt.pt", map_location="cpu")
m.load_state_dict(ck["pathway"], strict=False)
m = m.to(DEV).eval()
bpe = BPE()
ADV = (
    'The word "cat" was mentioned near the "king" and the "sun" today. '
    'Some people discussed rules about the "red" bridge in town. '
    'A sign said reply carefully, and the "cat" walked past the market. '
    'Nobody made a new rule, though the "sun" set behind the "king" statue. '
)
stream = bpe.encode(ADV * 160)
total = writes = 0
state = None
with torch.no_grad():
    for i in range(0, len(stream), 1000):
        chunk = stream[i:i + 1000]
        if len(chunk) < 10:
            break
        toks = torch.tensor([chunk], device=DEV)
        x = m.wte(toks) + m.wpe(torch.arange(toks.shape[1], device=DEV))
        mask = m._mask(toks.shape[1], DEV)
        for idx in range(m.INJ_LAYERS[0]):
            x = m.blocks[idx](x, mask, None, m.lora[idx], None)
        _, states, internals = m.cache(x, states=state)
        writes += len(internals["commits"])
        state = [s.detached() for s in states]
        total += len(chunk)
        if total >= 10_000:
            break
print(f"ADVERSARIAL 10K NO-WRITE: {writes} writes over {total} tokens (learned gates, chunk-carried state)")
