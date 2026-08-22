"""Orchestrator hand-execution of the registered Phase 1 fixture constructions.

Written BEFORE any generator exists (TDD-conform protocol, PLAN.md v1.6 /
Phase 1 test list). Implements ONLY registered spec text:
- Section 3: stream_seed(seed, name) derives a big-endian integer from the
  first eight bytes of sha256(f"{s}:{name}"), then shifts it right once.
- Section 6 Task A: cyclic square C[i][j]=(i+j)%16; three consecutive
  randperm(16) on the seed_rules 'rules' stream: sigma (rows), tau (cols),
  pi (symbols); L[i][j] = pi[C[sigma[i]][tau[j]]]; rules = first k rows.
  Per sequence, in order: one randint on 'cues' (uniform over k), one randint
  on 'operands' (uniform 16), then N single randint draws on 'distractors'.
- Section 6 Task M (v1.11 draw order): per sequence, one randperm(32) on
  'keys' taking first P; P single randint(16) on 'values'; one randperm(P)
  on 'queries' taking first n_queries.
- Appendix B tokens: cues 1..32, QRY=33, operands 34..49, distractors 50..63.
- Alignment contract: loss_mask[p] true iff tokens[p+1] is an answer token.

Conservative readings (recorded in the fixture JSON + ledger):
- cue token for rule index i is 1+i; operand index x -> token 34+x;
  distractor draw d in [0,14) -> token 50+d; key index -> token 1+idx.
- Example streams (cues/operands/distractors/keys/values/queries) seed from
  seed_data; the rule table seeds from seed_rules. One generator per stream
  for the whole fixture; the 4 sequences consume it consecutively.
- Task M miniature is the in-window placement (gap = 0).
- All randints are single scalar draws: torch.randint(0, high, (1,), generator=g).
"""
import hashlib
import json

import torch

QRY = 33
SEED_RULES = 0
SEED_DATA = 0


def stream_seed(seed: int, name: str) -> int:
    digest = hashlib.sha256(f"{seed}:{name}".encode()).digest()
    return int.from_bytes(digest[:8], "big") >> 1


def gen(seed: int, name: str) -> torch.Generator:
    g = torch.Generator(device="cpu")
    g.manual_seed(stream_seed(seed, name))
    return g


def rule_table(k: int) -> list[list[int]]:
    g = gen(SEED_RULES, "rules")
    sigma = torch.randperm(16, generator=g).tolist()
    tau = torch.randperm(16, generator=g).tolist()
    pi = torch.randperm(16, generator=g).tolist()
    L = [[pi[(sigma[i] + tau[j]) % 16] for j in range(16)] for i in range(16)]
    return L[:k]


def task_a_fixture(k: int = 2, N: int = 8, n_seq: int = 4) -> dict:
    rules = rule_table(k)
    g_cues = gen(SEED_DATA, "cues")
    g_ops = gen(SEED_DATA, "operands")
    g_dis = gen(SEED_DATA, "distractors")
    seqs = []
    for _ in range(n_seq):
        cue = int(torch.randint(0, k, (1,), generator=g_cues))
        x = int(torch.randint(0, 16, (1,), generator=g_ops))
        ds = [int(torch.randint(0, 14, (1,), generator=g_dis)) for _ in range(N)]
        tokens = [1 + cue] + [50 + d for d in ds] + [QRY, 34 + x, 34 + rules[cue][x]]
        mask = [False] * len(tokens)
        mask[len(tokens) - 2] = True  # p whose next token is the answer
        seqs.append({"tokens": tokens, "loss_mask": mask,
                     "metadata": {"cue_index": cue, "operand_index": x,
                                  "distractor_draws": ds,
                                  "answer_index": rules[cue][x]}})
    return {"task": "A", "k": k, "N": N, "seed_rules": SEED_RULES,
            "seed_data": SEED_DATA, "rule_table_first_k_rows": rules,
            "sequences": seqs}


def task_m_fixture(P: int = 4, n_queries: int = 2, n_seq: int = 4) -> dict:
    g_keys = gen(SEED_DATA, "keys")
    g_vals = gen(SEED_DATA, "values")
    g_qry = gen(SEED_DATA, "queries")
    seqs = []
    for _ in range(n_seq):
        key_perm = torch.randperm(32, generator=g_keys).tolist()
        keys = key_perm[:P]
        vals = [int(torch.randint(0, 16, (1,), generator=g_vals)) for _ in range(P)]
        q_perm = torch.randperm(P, generator=g_qry).tolist()
        queries = q_perm[:n_queries]
        tokens = []
        for ki, vi in zip(keys, vals, strict=False):
            tokens += [1 + ki, 34 + vi]
        tokens.append(QRY)  # gap = 0 (in-window miniature)
        for q in queries:
            tokens += [1 + keys[q], 34 + vals[q]]
        mask = [False] * len(tokens)
        pos = 2 * P + 1
        for _ in queries:
            mask[pos] = True  # key position predicts its answer value
            pos += 2
        seqs.append({"tokens": tokens, "loss_mask": mask,
                     "metadata": {"key_indices": keys, "value_indices": vals,
                                  "query_pair_positions": queries}})
    return {"task": "M", "P": P, "n_queries": n_queries, "gap": 0,
            "seed_rules": SEED_RULES, "seed_data": SEED_DATA, "sequences": seqs}


if __name__ == "__main__":
    import sys
    out_dir = sys.argv[1]
    a = task_a_fixture()
    m = task_m_fixture()
    with open(f"{out_dir}/task_a_k2_n8_seed0.json", "w") as f:
        json.dump(a, f, indent=1)
    with open(f"{out_dir}/task_m_p4_q2_seed0.json", "w") as f:
        json.dump(m, f, indent=1)
    print("task A rules:", a["rule_table_first_k_rows"])
    for s in a["sequences"]:
        print("A:", s["tokens"])
    for s in m["sequences"]:
        print("M:", s["tokens"])
