# ruff: noqa: E501
"""P2 drift run: q3-api-drift (QWEN-PLAN Run 2).

Fresh multi-chunk sessions every step: obligations set (chunk 0), updated and
cleared (chunk 1), both evidence chunks DELETED, two queries answered through
the carried state (>=1 on an updated field — the stale trap). Registered
gates: held-out exact >=50% and differential >=15 pts by step ~500; final
adherence >=70%, differential >=20, stale-first-token rate <10%; cleared slot
absent (mechanism); transplant redirects / shuffled sub-values break.
"""
import json
import sys
import time
from pathlib import Path

import torch
import torch.nn.functional as F

ROOT = Path(globals().get("__file__", "scripts/x.py")).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from tokenizers import Tokenizer  # noqa: E402

from stencil.qwen3 import Qwen3  # noqa: E402
from stencil.qwen_cache import QwenFocusCache, QwenWithCache  # noqa: E402
from stencil.qwen_task import generate_drift  # noqa: E402

tok = Tokenizer.from_file(str(ROOT / "models" / "qwen3-1.7b-hf" / "tokenizer.json"))
trunk = Qwen3()
trunk.load_state_dict(torch.load(ROOT / "models" / "qwen3-1.7b.pt", map_location="cpu"), strict=False)
trunk = trunk.to(torch.bfloat16).cuda().eval()
for p in trunk.parameters():
    p.requires_grad_(False)
cache = QwenFocusCache(seed=0).cuda()
model = QwenWithCache(trunk, cache)
OUT = ROOT / "results" / "qwen"
OUT.mkdir(parents=True, exist_ok=True)


def build(seed: int):
    s = generate_drift(seed)
    chunk_toks, chunk_events = [], []
    for ci, chunk in enumerate(s.chunks):
        ids: list[int] = []
        events = []
        for li, (line, slot, kind) in enumerate(chunk):
            lead = " " if ids else ""
            piece = tok.encode(lead + line).ids
            if slot is not None:
                vlo = vhi = None
                value = (s.values_by_line or {}).get((ci, li))
                if value is not None:
                    idx = line.index(" " + value)
                    pre = tok.encode(lead + line[:idx]).ids
                    prev = tok.encode(lead + line[:idx] + " " + value).ids
                    assert piece[: len(prev)] == prev and prev[: len(pre)] == pre, "value span tokenization mismatch"
                    vlo = len(ids) + len(pre)
                    vhi = len(ids) + len(prev)
                events.append((len(ids), len(ids) + len(piece), slot, kind, vlo, vhi))
            ids += piece
        chunk_toks.append(torch.tensor([ids]))
        chunk_events.append(events)
    # query chunk with teacher-forced answers; record answer spans
    text = s.query_parts[0]
    spans = []  # (lo, hi, current_ids, stale_first_or_None)
    for part, (_field, value, stale) in zip(s.query_parts[1:], s.queries, strict=True):
        pre = tok.encode(text + part).ids
        text = text + part + " " + value + ".\n"
        post = tok.encode(text.rstrip("\n")).ids
        cur_ids = post[len(pre):]
        sf = tok.encode(" " + stale).ids[0] if stale is not None else None
        spans.append((len(pre), len(post), cur_ids, sf))
    q_toks = torch.tensor([tok.encode(text.rstrip("\n")).ids])
    return s, chunk_toks, chunk_events, q_toks, spans


def forward_session(item, zero_code=False):
    s, chunk_toks, chunk_events, q_toks, spans = item
    st = None
    for ct, ev in zip(chunk_toks, chunk_events, strict=True):
        st = model.write_chunk(ct.cuda(), ev, st)
    logits = model.read_logits(q_toks.cuda(), st, zero_code=zero_code)
    return logits, st, spans


def session_loss(item):
    logits, _, spans = forward_session(item)
    losses = []
    for lo, hi, cur_ids, _ in spans:
        tgt = torch.tensor(cur_ids, device="cuda")
        losses.append(F.cross_entropy(logits[0, lo - 1 : hi - 1], tgt))
    return torch.stack(losses).mean()


def evaluate(seeds, zero_code=False):
    hits = tot = stale_hits = stale_tot = 0
    with torch.no_grad():
        for sd in seeds:
            item = build(sd)
            logits, st, spans = forward_session(item, zero_code=zero_code)
            assert len(st.slots) == 3, "cleared slot still present"  # 4 set - 1 clear
            for lo, hi, cur_ids, stale_first in spans:
                preds = logits[0, lo - 1 : hi - 1].argmax(-1).cpu()
                hits += bool((preds == torch.tensor(cur_ids)).all())
                tot += 1
                if stale_first is not None:
                    stale_tot += 1
                    stale_hits += int(preds[0]) == stale_first
    return hits / tot, (stale_hits / stale_tot if stale_tot else 0.0)


STEPS = 1500
opt = torch.optim.Adam(cache.parameters(), lr=3e-3)
sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=STEPS, eta_min=3e-4)
HELD = list(range(9_500_000, 9_500_032))
t0 = time.time()
history = []
for step in range(STEPS):
    opt.zero_grad()
    tot = 0.0
    for k in range(4):
        loss = session_loss(build(10_000_000 + step * 4 + k)) / 4
        loss.backward()
        tot += float(loss.detach()) * 4
    opt.step()
    sched.step()
    if step % 100 == 0 or step == STEPS - 1:
        print(f"step {step} loss {tot/4:.4f} ({(time.time()-t0)/60:.0f} min)", flush=True)
    if step > 0 and step % 250 == 0 or step == STEPS - 1:
        acc, stale = evaluate(HELD)
        acc0, _ = evaluate(HELD, zero_code=True)
        history.append({"step": step, "held_acc": acc, "zero_code": acc0, "stale_rate": stale})
        print(f"step {step} EVAL held {acc:.2f} zero-code {acc0:.2f} diff {100*(acc-acc0):.0f}pts stale {stale:.2f}", flush=True)
        torch.save(cache.state_dict(), OUT / "cache-p2-s0-ckpt.pt")
        (OUT / "p2-progress.json").write_text(json.dumps(history, indent=1))
print("done")
