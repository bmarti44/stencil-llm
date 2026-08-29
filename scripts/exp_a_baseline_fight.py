# ruff: noqa
"""Experiment A: the wire vs the trivial baseline (pin/re-insert text).

Scenario: compaction at C = first query - 40. Everything before C is deleted.
- BASELINE: base-v3 (100% near skill, no memory by proof) reads
  [pinned statements] + [tail]. The pinning policy is generous but honest:
  it may pin the most recent statement per slot, but only statements still
  within the model's receptive reach at compaction time (start >= C-756) —
  an agent cannot pin text it can no longer see — and only up to a budget of
  K carried tokens (recency-first).
- WIRE: cache-v8 processes the pre-compaction stream once, carries its
  ~5KB CacheState, reads the tail with zero carried tokens.

Reported: accuracy vs K; split by whether the queried slot's current rule
was pinnable; token/bytes cost of each channel.
"""
import sys

import torch

sys.path.insert(0, "/home/bmarti44/stencil-llm/src")
sys.path.insert(0, "/home/bmarti44/stencil-llm/scripts")

import run_gpt2_arms as R
from stencil.gpt2 import GatedGPT2
from stencil.nl_task import BPE, generate

DEV = R.DEV
bpe = BPE()

# wire model (cache-v8)
wire = R.build("cache", 0)
ck = torch.load("/home/bmarti44/stencil-llm/results/gpt2/cache-v8-s0-ckpt.pt", map_location="cpu")
wire.load_state_dict(ck["pathway"], strict=False)
wire.logit_bias = torch.nn.Parameter(ck["logit_bias"].to(DEV))
wire = wire.to(DEV).eval()

# baseline model (base-v3: trained soft salience => construct without hard gate)
base = GatedGPT2("base", window=64, seed_init=0, lora_rank=8)
sd = torch.load("/home/bmarti44/stencil-llm/models/gpt2-small.pt", map_location="cpu")
base.load_state_dict(sd, strict=False)
bs = torch.load("/home/bmarti44/stencil-llm/results/gpt2/base-v3-s0.pt", map_location="cpu")
base.load_state_dict(bs["pathway"], strict=False)
base.logit_bias = torch.nn.Parameter(bs["logit_bias"].to(DEV))
base = base.to(DEV).eval()

N = 96
BUDGETS = [0, 32, 64, 96, 128, 160]
REACH = 756

wire_hits = wire_tot = 0
base_stats = {k: {"hit": 0, "tot": 0, "hit_pinnable": 0, "tot_pinnable": 0, "hit_lost": 0, "tot_lost": 0} for k in BUDGETS}

with torch.no_grad():
    for i in range(N):
        s = generate(R.VAL_SPACE + 800_000 + i, family="train", bpe=bpe)
        toks = torch.tensor([s.tokens], device=DEV)
        C = min(s.query_positions) - 40
        tail = s.tokens[C:]
        # --- WIRE: carry state across the compaction
        wire(toks[:, :C])
        carried = [st.detached() for st in wire.cache_states]
        out = wire(torch.tensor([tail], device=DEV), cache_states=carried) + wire.logit_bias
        for p, slot, ans in zip(s.query_positions, s.query_slots, s.active_answer, strict=True):
            want = bpe.encode(" " + ans)[0]
            wire_hits += int(int(out[0, p - C].argmax()) == want)
            wire_tot += 1
        # --- BASELINE: pin policy
        # most recent statement per slot, only if start >= C-REACH
        latest: dict[int, tuple[int, int]] = {}
        span_slot: dict[tuple[int, int], int] = {}
        for pos, slot, _ans in s.rule_events:
            for lo, hi in s.rule_spans:
                if lo <= pos < hi:
                    span_slot[(lo, hi)] = slot
        for (lo, hi), slot in sorted(span_slot.items()):
            latest[slot] = (lo, min(hi, C))
        pinnable = {slot: (lo, hi) for slot, (lo, hi) in latest.items() if lo >= C - REACH and hi <= C}
        # recency-first packing per budget
        order = sorted(pinnable.items(), key=lambda kv: -kv[1][0])
        for K in BUDGETS:
            pinned: list[int] = []
            got: set[int] = set()
            for slot, (lo, hi) in order:
                seg = s.tokens[lo:hi]
                if len(pinned) + len(seg) > K:
                    continue
                pinned = s.tokens[lo:hi] + pinned  # keep textual order-ish
                got.add(slot)
            inp = pinned + tail
            out_b = base(torch.tensor([inp], device=DEV)) + base.logit_bias
            off = len(pinned) - C
            for p, slot, ans in zip(s.query_positions, s.query_slots, s.active_answer, strict=True):
                want = bpe.encode(" " + ans)[0]
                ok = int(int(out_b[0, p + off].argmax()) == want)
                st = base_stats[K]
                st["hit"] += ok
                st["tot"] += 1
                if slot in got:
                    st["hit_pinnable"] += ok
                    st["tot_pinnable"] += 1
                else:
                    st["hit_lost"] += ok
                    st["tot_lost"] += 1

print(f"WIRE (0 carried tokens, ~5KB state): {wire_hits}/{wire_tot} = {wire_hits/wire_tot:.3f}")
for K in BUDGETS:
    st = base_stats[K]
    pin = st["hit_pinnable"] / st["tot_pinnable"] if st["tot_pinnable"] else float("nan")
    lost = st["hit_lost"] / st["tot_lost"] if st["tot_lost"] else float("nan")
    print(
        f"BASELINE K={K:>3} tokens: total {st['hit']}/{st['tot']} = {st['hit']/st['tot']:.3f} "
        f"| pinned-slot acc {pin:.3f} (n={st['tot_pinnable']}) | lost-slot acc {lost:.3f} (n={st['tot_lost']})"
    )
