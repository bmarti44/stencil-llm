# ruff: noqa: E501
"""P0 decisive test: open-content oracle ceiling (QWEN-PLAN stop condition 2).

The obligation text is DELETED (query-only prompt). Optimize per-example
additive residual injections at blocks 24-27; can ANY code make frozen Qwen
generate the held-out multi-token value? Gate: >=6/8 rank-1 first token and
>=50% exact teacher-forced continuation.
"""
import sys
from pathlib import Path

import torch
import torch.nn.functional as F

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from tokenizers import Tokenizer  # noqa: E402

from stencil.qwen3 import Qwen3  # noqa: E402
from stencil.qwen_task import generate  # noqa: E402

INJ_LAYERS = (24, 25, 26, 27)

tok = Tokenizer.from_file(str(ROOT / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
m = Qwen3()
m.load_state_dict(torch.load(ROOT / "models" / "qwen3-1.7b.pt", map_location="cpu"), strict=False)
m = m.to(torch.bfloat16).cuda().eval()
for p in m.parameters():
    p.requires_grad_(False)

first_hits = cont_hits = tried = 0
for i in range(8):
    s = generate(9_100_000 + i)
    ids_q = tok.encode(s.query_text).ids
    ids_full = tok.encode(s.query_text + " " + s.value + ".").ids
    assert ids_full[: len(ids_q)] == ids_q, "tokenization prefix mismatch"
    want = ids_full[len(ids_q):]
    toks = torch.tensor([ids_full], device="cuda")
    T = toks.shape[1]
    inj = {L: torch.zeros(1, T, 2048, device="cuda", requires_grad=True) for L in INJ_LAYERS}
    opt = torch.optim.Adam(list(inj.values()), lr=0.05)
    tgt = torch.tensor(want, device="cuda")
    span = slice(len(ids_q) - 1, len(ids_full) - 1)
    for _ in range(200):
        logits = m(toks, inj={L: v.to(torch.bfloat16) for L, v in inj.items()})
        loss = F.cross_entropy(logits[0, span], tgt)
        opt.zero_grad()
        loss.backward()
        opt.step()
    with torch.no_grad():
        logits = m(toks, inj={L: v.to(torch.bfloat16) for L, v in inj.items()})
        preds = logits[0, span].argmax(-1)
        first_ok = int(preds[0]) == want[0]
        cont_ok = bool((preds == tgt).all())
    tried += 1
    first_hits += first_ok
    cont_hits += cont_ok
    print(f"ex {i}: first {'OK' if first_ok else 'X'} cont {'OK' if cont_ok else 'X'} "
          f"final ce {float(loss):.3f} value {s.value!r}", flush=True)
print(f"OPEN-CONTENT ORACLE: first-token {first_hits}/{tried} (gate >=6/8), "
      f"exact continuation {cont_hits}/{tried} (gate >=4/8)")
