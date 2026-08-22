"""Orchestrator hand-execution of a Task B pinning fixture (kimi#6, Phase 1 round 1).

Derived INDEPENDENTLY of src/stencil/data.py (not read for this script) from:
- PLAN.md Section 6 Task B: R segments with a cue, delay drawn uniformly from
  32 through 256 distractors, query, operand, and answer;
  k=8 rules via the Task A Latin construction from seed_rules; consecutive segment
  cues must differ (resample on repeat); operands uniform, independent per segment.
- The coder's LEDGERED residual schedule (plan/LEDGER.md, coder handoff): per
  segment draw order = cue (immediate redraw while equal to previous segment's),
  operand, one inclusive delay randint (delays stream), then that many single
  distractor draws; scalar draws; one continuing generator per stream.
- Section 3 streams; Appendix B tokens; alignment contract for the mask.
Pins the schedule at R=2, seed_rules=0, seed_data=0, 2 sequences.
"""
import hashlib
import json

import torch

QRY = 33


def gen(seed: int, name: str) -> torch.Generator:
    g = torch.Generator(device="cpu")
    digest = hashlib.sha256(f"{seed}:{name}".encode()).digest()
    g.manual_seed(int.from_bytes(digest[:8], "big") >> 1)
    return g


def rule_table(k: int) -> list[list[int]]:
    g = gen(0, "rules")
    sigma = torch.randperm(16, generator=g).tolist()
    tau = torch.randperm(16, generator=g).tolist()
    pi = torch.randperm(16, generator=g).tolist()
    return [[pi[(sigma[i] + tau[j]) % 16] for j in range(16)] for i in range(16)][:k]


def task_b_fixture(
    R: int = 2,
    k: int = 8,
    n_seq: int = 2,
    delay_min: int = 32,
    delay_max: int = 256,
) -> dict:
    rules = rule_table(k)
    g_c = gen(0, "cues")
    g_o = gen(0, "operands")
    g_de = gen(0, "delays")
    g_di = gen(0, "distractors")
    seqs = []
    for _ in range(n_seq):
        tokens, mask_pos, meta = [], [], []
        prev = None
        for _ in range(R):
            cue = int(torch.randint(0, k, (1,), generator=g_c))
            redraws = 0
            while cue == prev:
                cue = int(torch.randint(0, k, (1,), generator=g_c))
                redraws += 1
            prev = cue
            x = int(torch.randint(0, 16, (1,), generator=g_o))
            delay = int(torch.randint(delay_min, delay_max + 1, (1,), generator=g_de))
            ds = [int(torch.randint(0, 14, (1,), generator=g_di)) for _ in range(delay)]
            seg = [1 + cue] + [50 + d for d in ds] + [QRY, 34 + x, 34 + rules[cue][x]]
            mask_pos.append(len(tokens) + len(seg) - 2)
            tokens += seg
            meta.append({"cue_index": cue, "operand_index": x, "delay": delay,
                         "cue_redraws": redraws, "answer_index": rules[cue][x]})
        mask = [False] * len(tokens)
        for p in mask_pos:
            mask[p] = True
        seqs.append({"tokens": tokens, "loss_mask": mask, "segments": meta})
    return {"task": "B", "R": R, "k": k, "delay_min": delay_min, "delay_max": delay_max,
            "seed_rules": 0, "seed_data": 0, "sequences": seqs}


if __name__ == "__main__":
    import sys
    fx = task_b_fixture()
    with open(f"{sys.argv[1]}/task_b_r2_k8_seed0.json", "w") as f:
        json.dump(fx, f, indent=1)
    for s in fx["sequences"]:
        print("B segments:", s["segments"], "len", len(s["tokens"]))
