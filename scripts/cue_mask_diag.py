# ruff: noqa: E501
"""Sol cue-masking diagnostic: is the oscillator drowned by filler, or unable
to encode at all? Feed the trained controller full vs rule-only embeddings and
ridge-probe answer identity per slot at query positions. Near family (no
updates, short distances) so encoding, not memory span, is what's tested."""
import sys

import torch

sys.path.insert(0, "/home/bmarti44/stencil-llm/src")
from stencil.gpt2 import GatedGPT2  # noqa: E402
from stencil.nl_task import ANSWER_WORDS, BPE, generate  # noqa: E402

DEV = "cuda"
RULE_SPAN = 16  # rule statements are ~14 tokens; mask a fixed window

m = GatedGPT2("osc", window=64, seed_init=0, lora_rank=8)
sd = torch.load("/home/bmarti44/stencil-llm/models/gpt2-small.pt", map_location="cpu")
m.load_state_dict(sd, strict=False)
ck = torch.load("/home/bmarti44/stencil-llm/results/gpt2/osc-v3-s0-ckpt.pt", map_location="cpu")
m.load_state_dict(ck["pathway"], strict=False)
m = m.to(DEV).eval()
print("controller from osc-v3 ckpt step", ck["step"])

bpe = BPE()
N = 640


def collect(masked: bool) -> tuple[dict, dict]:
    xs: dict[int, list] = {s: [] for s in range(4)}
    ys: dict[int, list] = {s: [] for s in range(4)}
    with torch.no_grad():
        for i in range(N):
            seq = generate(6_000_000 + i, family="near", bpe=bpe)
            toks = torch.tensor([seq.tokens], device=DEV)
            emb = m.wte(toks)
            if masked:
                keep = torch.zeros(len(seq.tokens), device=DEV)
                for s in range(4):
                    p0 = seq.rule_statement_pos[s]
                    keep[p0 : p0 + RULE_SPAN] = 1.0
                emb = emb * keep[None, :, None]
            code = m._norm(m.controller(emb))
            for p, s, ans in zip(seq.query_positions, seq.query_slots, seq.active_answer, strict=True):
                xs[s].append(code[0, p].float().cpu())
                ys[s].append(ANSWER_WORDS.index(ans))
    return xs, ys


def ridge_acc(xs: list, ys: list) -> float:
    X = torch.stack(xs)
    y = torch.tensor(ys)
    k = len(ys) * 3 // 4
    Y = torch.zeros(k, 16)
    Y[torch.arange(k), y[:k]] = 1
    W = torch.linalg.solve(X[:k].T @ X[:k] + 1e-3 * torch.eye(X.shape[1]), X[:k].T @ Y)
    return float((torch.argmax(X[k:] @ W, 1) == y[k:]).float().mean())


for masked in (False, True):
    xs, ys = collect(masked)
    accs = [round(ridge_acc(xs[s], ys[s]), 3) for s in range(4) if len(ys[s]) >= 40]
    label = "RULE-ONLY (filler zeroed)" if masked else "FULL input (as trained)"
    print(f"{label}: per-slot probe acc {accs} (chance 0.0625)", flush=True)
