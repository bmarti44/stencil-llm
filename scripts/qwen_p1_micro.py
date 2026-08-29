# ruff: noqa: E501
"""P1 microfit: q3-api-micro (QWEN-PLAN Run 1).

32 fixed sessions. Chunk 1 (obligations + filler) is written to the cache via
structured events, then DELETED; chunk 2 (query only) is answered through the
carried state. Gates: loss falling by step 16; >=95% train exact-match and
>=50-pt learned-minus-zero differential by step 64. Held-out generalization
logged (not gated at P1).
"""
import sys
from pathlib import Path

import torch
import torch.nn.functional as F

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from tokenizers import Tokenizer  # noqa: E402

from stencil.qwen3 import Qwen3  # noqa: E402
from stencil.qwen_cache import QwenFocusCache, QwenWithCache  # noqa: E402
from stencil.qwen_task import FIELDS, generate  # noqa: E402

tok = Tokenizer.from_file(str(ROOT / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
trunk = Qwen3()
trunk.load_state_dict(torch.load(ROOT / "models" / "qwen3-1.7b.pt", map_location="cpu"), strict=False)
trunk = trunk.to(torch.bfloat16).cuda().eval()
for p in trunk.parameters():
    p.requires_grad_(False)
cache = QwenFocusCache(seed=0).cuda()
model = QwenWithCache(trunk, cache)


def build(seed: int):
    """Line-wise tokenization so obligation spans are exact."""
    s = generate(seed)
    ids: list[int] = []
    events = []
    lines = [f"Note: the {f} is {v}." for f, v in s.obligations]
    for j, line in enumerate(lines):
        piece = tok.encode((" " if ids else "") + line).ids
        events.append((len(ids), len(ids) + len(piece), FIELDS.index(s.obligations[j][0])))
        ids += piece
    from stencil.qwen_task import FILLER
    g = torch.Generator().manual_seed(seed + 777)
    for _ in range(6):
        ids += tok.encode(" " + FILLER[int(torch.randint(0, len(FILLER), (1,), generator=g))]).ids
    q_ids = tok.encode(s.query_text).ids
    full = tok.encode(s.query_text + " " + s.value + ".").ids
    assert full[: len(q_ids)] == q_ids
    want = full[len(q_ids):]
    return s, torch.tensor([ids]), torch.tensor([full]), len(q_ids), want


TRAIN = [build(9_200_000 + i) for i in range(32)]
HELD = [build(9_300_000 + i) for i in range(16)]

opt = torch.optim.Adam(cache.parameters(), lr=3e-3)


def evaluate(items, zero_code=False):
    hits = 0
    with torch.no_grad():
        for s, ev_toks, q_toks, qlen, want in items:
            st = model.write_chunk(ev_toks.cuda(), events_of(s))
            logits = model.read_logits(q_toks.cuda(), st, zero_code=zero_code)
            preds = logits[0, qlen - 1 : q_toks.shape[1] - 1].argmax(-1)
            hits += bool((preds.cpu() == torch.tensor(want)).all())
    return hits / len(items)


def events_of(s):
    # recompute events (must match build's line-wise layout)
    ids_len = 0
    events = []
    for _j, (f, v) in enumerate(s.obligations):
        piece = tok.encode((" " if ids_len else "") + f"Note: the {f} is {v}.").ids
        events.append((ids_len, ids_len + len(piece), FIELDS.index(f)))
        ids_len += len(piece)
    return events


STEPS = 1500
sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=STEPS, eta_min=3e-4)
for step in range(STEPS):
    opt.zero_grad()
    tot = 0.0
    for k in range(4):
        s, ev_toks, q_toks, qlen, want = TRAIN[(step * 4 + k) % 32]
        st = model.write_chunk(ev_toks.cuda(), events_of(s))
        logits = model.read_logits(q_toks.cuda(), st)
        loss = F.cross_entropy(logits[0, qlen - 1 : q_toks.shape[1] - 1], torch.tensor(want, device="cuda")) / 4
        loss.backward()
        tot += float(loss.detach()) * 4
    opt.step()
    sched.step()
    if step % 150 == 0 or step == STEPS - 1:
        print(f"step {step} loss {tot/4:.4f}", flush=True)

train_acc = evaluate(TRAIN)
train_zero = evaluate(TRAIN, zero_code=True)
held_acc = evaluate(HELD)
held_zero = evaluate(HELD, zero_code=True)
print(f"TRAIN exact {train_acc:.2f} vs zero-code {train_zero:.2f} (gates: >=0.95, diff >=0.50)")
print(f"HELD-OUT exact {held_acc:.2f} vs zero-code {held_zero:.2f} (logged, ungated at P1)")
