# ruff: noqa
# ruff: noqa: E501
"""Closing checks on the cache-v8 checkpoint (sol deployment-ladder items):
1. Extended learned-vs-zero-code beyond-window differential at n=128 seqs.
2. Cache-state TRANSPLANT: run only a query tail with a DONOR sequence's
   carried cache state — predictions must follow the donor's rules.
3. Shuffled control: permute the donor's value vectors across slots — the
   transplant effect must break.
"""
import sys

import torch

sys.path.insert(0, "/home/bmarti44/stencil-llm/src")
sys.path.insert(0, "/home/bmarti44/stencil-llm/scripts")

import run_gpt2_arms as R  # noqa: E402
from stencil.nl_task import BPE, batch  # noqa: E402

DEV = R.DEV
model = R.build("cache", 0)
ck = torch.load("/home/bmarti44/stencil-llm/results/gpt2/cache-v8-s0-ckpt.pt", map_location="cpu")
model.load_state_dict(ck["pathway"], strict=False)
model.logit_bias = torch.nn.Parameter(ck["logit_bias"].to(DEV))
model = model.to(DEV).eval()
bpe = BPE()
print("ckpt step", ck["step"])

# 1. extended differential, n=128 (train family => ~236 beyond queries)
res = R.evaluate(model, bpe, R.FINAL_SPACE, 0, n=128, families=("train",))
res0 = R.evaluate(model, bpe, R.FINAL_SPACE, 0, n=128, families=("train",), zero_code=True)
b, b0 = res["train"]["beyond"], res0["train"]["beyond"]
print(f"EXTENDED DIFFERENTIAL (n=128 seqs): beyond {b['correct']}/{b['total']} = {b['acc']:.3f} "
      f"vs zero-code {b0['correct']}/{b0['total']} = {b0['acc']:.3f} "
      f"(diff {100*(b['acc']-b0['acc']):.1f} pts)")
print(f"  within: learned {res['train']['within']['acc']:.3f} zero-code {res0['train']['within']['acc']:.3f}")

# 2+3. transplant with carried state: donor B's cache, recipient A's query tail
flips = tried = shuffle_flips = 0
with torch.no_grad():
    for i in range(0, 64, 2):
        ta, _, sa = batch([R.FINAL_SPACE + 500_000 + i], bpe=bpe)
        tb, _, sb = batch([R.FINAL_SPACE + 500_000 + i + 1], bpe=bpe)
        A, B = sa[0], sb[0]
        # need a slot both query and with differing answers
        common = [s for s in A.query_slots if s in B.query_slots]
        pick = None
        for s in common:
            ansA = A.active_answer[A.query_slots.index(s)]
            ansB = B.active_answer[B.query_slots.index(s)]
            if ansA != ansB:
                pick = (s, ansB)
                break
        if pick is None:
            continue
        slot, ansB = pick
        qp = A.query_positions[A.query_slots.index(slot)]
        # donor state: full forward on B
        model(tb.to(DEV))
        donor = [st.detached() for st in model.cache_states]
        # recipient tail: last 200 tokens of A (query zone only, no statements)
        tail_start = min(A.query_positions) - 40
        tail = ta[:, tail_start:].to(DEV)
        qp_tail = qp - tail_start
        out = model(tail, cache_states=donor)
        pred = int((out + model.logit_bias)[0, qp_tail].argmax())
        want = bpe.encode(" " + ansB)[0]
        tried += 1
        flips += int(pred == want)
        # shuffled control: rotate values across the donor's slots
        sh = [st.detached() for st in donor]
        ids = sorted(sh[0].slots)
        vals = [sh[0].slots[j][1] for j in ids]
        vals = vals[1:] + vals[:1]
        sh[0].slots = {j: (sh[0].slots[j][0], v) for j, v in zip(ids, vals, strict=True)}
        out_s = model(tail, cache_states=sh)
        pred_s = int((out_s + model.logit_bias)[0, qp_tail].argmax())
        shuffle_flips += int(pred_s == want)
print(f"TRANSPLANT: {flips}/{tried} tail-only queries answered with the DONOR's rule; "
      f"shuffled-values control {shuffle_flips}/{tried}")
