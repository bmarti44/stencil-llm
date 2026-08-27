"""Orchestrator hand-execution of the Task D miniature fixture.

Derived DIRECTLY from the frozen generation law in plan/taskd/PLAN-TASKD.md,
BEFORE any generator exists. Binding conservative readings (flagged for review):

- Token map: USLOT_d = 28+d (full scale: slots 1..4 -> 29..32
miniature slots
  1..2 -> 29,30). QSLOT_d = 59+d (full: 60..63
  miniature 60,61). CUE_r = r
  (1..8). QRY=33. Operands 34..49. PAD=0. Task-D distractor alphabet is 50..59
  (10 symbols) because 60..63 are reserved as QSLOT markers.
- Gap semantics: update event i starts at (end of previous event) + gap_i,
  where events are the 2-token [USLOT][CUE] pairs
  the initial block (slots in
  order, 2 tokens each) starts at position 0 and counts as the zeroth event
  span. Gaps are distractor-span lengths.
- Query blocks are 4 tokens [QRY][QSLOT][x][PAD]
the PAD is in the INPUT
the
  true answer lives ONLY in the separate targets array at the x position
  (targets[p] = answer token id where p is the x position
  -1 elsewhere).
- Valid-start recompute per the law: a candidate start s is valid iff the
  4-token block [s, s+3] does not overlap any update event or placed query
  block and is not within 2 tokens of either
  draw = index into the sorted
  current valid-start list, from the operands stream (randint over its size).
- Miniature parameters (fixture-only, registered here): slots=2, k=8,
  L_core=256, updates=3, Q=4, gap bounds U{16..48}
  reinsertion case:
  refresh blocks (2 active-slot [USLOT][CUE] pairs = 4 tokens) inserted before
  every final-coordinate multiple of 64
  reserve = 4 tokens per multiple.
- seed_rules=0. seed_data = smallest integer >= 0 whose draw sequence yields
  at least one legal NO-OP update (rule draw equal to the slot's current
  rule)
  the chosen seed and the no-op position are recorded in the fixture.
- Streams (Section 3 scheme): rules from seed_rules
cues/delays/operands/
  distractors from seed_data
  one continuing generator per stream.
"""
import hashlib
import json

import torch

QRY = 33
PAD = 0


def gen(seed: int, name: str) -> torch.Generator:
    g = torch.Generator(device="cpu")
    digest = hashlib.sha256(f"{seed}:{name}".encode()).digest()
    g.manual_seed(int.from_bytes(digest[:8], "big") >> 1)
    return g


def rule_table(k: int = 8) -> list[list[int]]:
    g = gen(0, "rules")
    sigma = torch.randperm(16, generator=g).tolist()
    tau = torch.randperm(16, generator=g).tolist()
    pi = torch.randperm(16, generator=g).tolist()
    return [[pi[(sigma[i] + tau[j]) % 16] for j in range(16)] for i in range(16)][:k]


SLOTS, K, L_CORE, N_UP, Q, GAP_LO, GAP_HI = 2, 8, 256, 3, 4, 16, 48


def build_core(seed_data: int):
    g_c, g_de, g_op, g_di = (gen(seed_data, n) for n in ("cues", "delays",
        "operands", "distractors"))
    events = []  # (start, 'U', slot, rule) 2-token update events
    active = {}
    # (1) initial block: SLOTS rules from cues, slots 1.. in order, from pos 0
    pos = 0
    for d in range(1, SLOTS + 1):
        r = int(torch.randint(1, K + 1, (1,), generator=g_c))
        events.append((pos, d, r))
        active[d] = r
        pos += 2
    init_end = pos
    # (2) gap vector  (3) slots  (4) rules — draw order per the law
    gaps = [int(torch.randint(GAP_LO, GAP_HI + 1, (1,),
        generator=g_de)) for _ in range(N_UP)]
    slots = [int(torch.randint(1, SLOTS + 1, (1,), generator=g_c)) for _ in range(N_UP)]
    rls = [int(torch.randint(1, K + 1, (1,), generator=g_c)) for _ in range(N_UP)]
    upd, prev_end, noop_at = [], init_end, []
    hist = dict(active)
    for i in range(N_UP):
        s = prev_end + gaps[i]
        if rls[i] == hist[slots[i]]:
            noop_at.append(i)
        hist[slots[i]] = rls[i]
        upd.append((s, slots[i], rls[i]))
        prev_end = s + 2
    if prev_end + Q * 4 > L_CORE - 8:
        return None  # law's rejection branch; miniature scans seeds instead
    all_updates = events + upd
    # (5) query starts: sequential draws, recomputed valid set
    blocked = set()
    for s, _, _ in all_updates:
        blocked.update(range(s - 2,
            s + 4))  # event 2 tokens + 2-token clearance both sides
    qstarts = []
    for _ in range(Q):
        valid = [s for s in range(init_end, L_CORE - 4)
                 if all((s + j) not in blocked for j in range(4))]
        idx = int(torch.randint(0, len(valid), (1,), generator=g_op))
        s = valid[idx]
        qstarts.append(s)
        blocked.update(range(s - 2, s + 6))  # 4-token block + 2 clearance
    # (6) query slots  (7) operands
    qslots = [int(torch.randint(1, SLOTS + 1, (1,), generator=g_c)) for _ in range(Q)]
    xs = [int(torch.randint(0, 16, (1,), generator=g_op)) for _ in range(Q)]
    # assemble core
    toks = [None] * L_CORE
    for s, d, r in all_updates:
        toks[s], toks[s + 1] = 28 + d, r
    targets = [-1] * L_CORE
    # active-rule resolution per query (most recent update to slot strictly before QRY
    # pos)
    q_meta = []
    for (s, d, x) in zip(qstarts, qslots, xs, strict=True):
        rule = None
        for (us, ud, ur) in sorted(all_updates):
            if us < s and ud == d:
                rule = ur
        ans = 34 + rule_table(K)[rule - 1][x]
        toks[s], toks[s + 1], toks[s + 2], toks[s + 3] = QRY, 59 + d, 34 + x, PAD
        targets[s + 2] = ans
        q_meta.append({"start": s, "slot": d, "x": x, "active_rule": rule,
            "answer": ans})
    for i in range(L_CORE):
        if toks[i] is None:
            toks[i] = 50 + int(torch.randint(0, 10, (1,), generator=g_di))
    return {"tokens": toks, "targets": targets,
        "updates": [list(u) for u in all_updates],
            "queries": q_meta, "noop_update_indices": noop_at, "gaps": gaps}


def reinsert64(core):
    """Miniature reinsert case: refresh (all active slots) before each final-coord multi
    ple of 64."""
    toks, out, final_i, core_i = core["tokens"], [], 0, 0
    upds = sorted(core["updates"])
    def active_at(cp):
        st = {}
        for us, ud, ur in upds:
            if us < cp:
                st[ud] = ur
        return st
    while core_i < len(toks):
        if final_i and final_i % 64 == 0:
            for d, r in sorted(active_at(core_i).items()):
                out += [28 + d, r]
                final_i += 2
        out.append(toks[core_i])
        core_i += 1
        final_i += 1
    return out


if __name__ == "__main__":
    import sys
    seed = 0
    while True:
        c = build_core(seed)
        if c and c["noop_update_indices"]:
            break
        seed += 1
    c["seed_data"] = seed
    c["reinsert64_tokens"] = reinsert64(c)
    with open(sys.argv[1], "w") as f:
        json.dump(c, f, indent=1)
    print("seed_data:", seed, "| no-op at update idx:", c["noop_update_indices"],
          "| updates:", c["updates"], "| queries:", [(q['start'], q['slot'],
              q['active_rule']) for q in c["queries"]],
          "| reinsert len:", len(c["reinsert64_tokens"]))
