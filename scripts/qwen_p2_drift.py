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
import os
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
trunk.load_state_dict(torch.load(ROOT / "models" / "qwen3-1.7b.pt", map_location="cpu"), strict=True)
trunk = trunk.to(torch.bfloat16).cuda().eval()
for p in trunk.parameters():
    p.requires_grad_(False)
cache = QwenFocusCache(seed=0).cuda()
model = QwenWithCache(trunk, cache)
OUT = ROOT / "results" / "qwen"
OUT.mkdir(parents=True, exist_ok=True)
VARIANT = os.environ.get("VARIANT", "dev")  # immutable artifact tag per variant


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
    # TRAINING stream: teacher-forced answers (diagnostic only); targets are
    # taken from the FINAL tokenization (fable fix: '.\n' merge wart).
    text = s.query_parts[0]
    bounds = []
    for part, (_field, value, _stale) in zip(s.query_parts[1:], s.queries, strict=True):
        pre = tok.encode(text + part).ids
        text = text + part + " " + value + ".\n"
        post = tok.encode(text.rstrip("\n")).ids
        bounds.append((len(pre), len(post)))
    q_ids = tok.encode(text.rstrip("\n")).ids
    q_toks = torch.tensor([q_ids])
    spans = [(lo, hi, q_ids[lo:hi], None) for lo, hi in bounds]
    # FREE-RUNNING eval prompts: one per query, NO prior gold answers.
    fr = []
    for part, (field, value, stale) in zip(s.query_parts[1:], s.queries, strict=True):
        prompt_ids = tok.encode(s.query_parts[0] + part).ids
        fr.append((torch.tensor([prompt_ids]), field, value, stale))
    clear_slot = next(
        line[1] for chunk in s.chunks for line in chunk if line[2] == "clear"
    )
    return s, chunk_toks, chunk_events, q_toks, spans, fr, clear_slot


def forward_session(item, zero_code=False):
    s, chunk_toks, chunk_events, q_toks, spans, fr, clear_slot = item
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


def generate_answer(prompt_toks, st, zero_code=False, max_new=16):
    toks = prompt_toks.cuda()
    outs = []
    for _ in range(max_new):
        logits = model.read_logits(toks, st, zero_code=zero_code)
        nxt = int(logits[0, -1].argmax())
        outs.append(nxt)
        toks = torch.cat([toks, torch.tensor([[nxt]], device="cuda")], dim=1)
    return tok.decode(outs).strip().split("\n")[0].strip().rstrip(".")


def evaluate(seeds, zero_code=False):
    """FREE-RUNNING per-query eval: no prior gold answers in context; greedy
    generation; stale = generated text equals the full stale value (which
    always differs from current as a string)."""
    hits = tot = stale_hits = stale_tot = 0
    with torch.no_grad():
        for sd in seeds:
            item = build(sd)
            s, chunk_toks, chunk_events, _q, _spans, fr, clear_slot = item
            st = None
            for ct, ev in zip(chunk_toks, chunk_events, strict=True):
                st = model.write_chunk(ct.cuda(), ev, st)
            assert clear_slot not in st.slots, "cleared slot identity still present"
            assert len(st.slots) == 3
            for prompt_toks, _field, value, stale in fr:
                gen = generate_answer(prompt_toks, st, zero_code=zero_code)
                hits += gen == value
                tot += 1
                if stale is not None:
                    stale_tot += 1
                    stale_hits += gen == stale
    return hits / tot, (stale_hits / stale_tot if stale_tot else 0.0)


STEPS = 1500
opt = torch.optim.Adam(cache.parameters(), lr=3e-3)
sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=STEPS, eta_min=3e-4)
HELD = list(range(9_600_000, 9_600_032))  # confirmatory validation (Amendment 1)
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
        torch.save(cache.state_dict(), OUT / f"cache-p2-{VARIANT}-ckpt.pt")
        (OUT / f"p2-{VARIANT}-progress.json").write_text(json.dumps(history, indent=1))
print("done")
