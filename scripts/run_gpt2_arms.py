# ruff: noqa: E501
"""Fine-tune the base/osc arms on the NL instruction task and evaluate.

Usage:
  uv run python scripts/run_gpt2_arms.py train <arm> <seed>   # one run
  uv run python scripts/run_gpt2_arms.py final <arm> <seed>   # sealed eval (needs results/GPT2-FLEET-FROZEN)
  uv run python scripts/run_gpt2_arms.py dial <arm> <seed>    # probe + transplant on a trained run

Both arms train the identical budget: pathway (controller+gates where present)
plus a shared lm-head bias adapter (the Step-0 contingency, arm-symmetric).
Trunk frozen; results/gpt2/<arm>-s<seed>.json + .pt written.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import torch
import torch.nn.functional as F

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from stencil import determinism  # noqa: F401,E402
from stencil.gpt2 import GatedGPT2  # noqa: E402
from stencil.nl_task import BPE, batch  # noqa: E402

OUT = ROOT / "results" / "gpt2"
STEPS = 3000
BATCH = 8
TRAIN_SPACE = 0
VAL_SPACE = 1_000_000
FINAL_SPACE = 2_000_000
DEV = "cuda" if torch.cuda.is_available() else "cpu"
LORA_RANK = 4  # symmetric adapter, both arms (post-flatline iteration)


def tag(arm: str, seed: int) -> str:
    return f"{arm}-lora-s{seed}" if LORA_RANK else f"{arm}-s{seed}"


def build(arm: str, seed: int) -> GatedGPT2:
    model = GatedGPT2(arm, window=64, seed_init=seed, lora_rank=LORA_RANK)
    sd = torch.load(ROOT / "models" / "gpt2-small.pt", map_location="cpu")
    missing, unexpected = model.load_state_dict(sd, strict=False)
    assert not unexpected
    if not hasattr(model, "logit_bias"):
        model.logit_bias = torch.nn.Parameter(torch.zeros(50257))
    return model.to(DEV)


def logits_of(model: GatedGPT2, toks: torch.Tensor) -> torch.Tensor:
    return model(toks) + model.logit_bias


def loss_fn(logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
    mask = targets >= 0
    assert int(mask.sum()) > 0, "no query targets in batch (vacuous)"
    return F.cross_entropy(logits[mask], targets[mask])


def evaluate(model: GatedGPT2, bpe: BPE, space: int, seed: int, n: int = 64) -> dict:
    model.eval()
    out: dict = {}
    with torch.no_grad():
        for family in ("train", "drought", "burst"):
            hits = {"within": [0, 0], "beyond": [0, 0]}
            base = space + seed * 100_000 + {"train": 0, "drought": 30_000, "burst": 60_000}[family]
            for start in range(0, n, BATCH):
                seeds = list(range(base + start, base + min(start + BATCH, n)))
                toks, tgts, seqs = batch(seeds, family=family, bpe=bpe)
                lg = logits_of(model, toks.to(DEV))
                for b, s in enumerate(seqs):
                    for p, slot in zip(s.query_positions, s.query_slots, strict=True):
                        d = p - s.rule_statement_pos[slot]
                        bin_ = "beyond" if d > 756 else "within"
                        pred = int(lg[b, p].argmax())
                        hits[bin_][0] += int(pred == s.targets[p])
                        hits[bin_][1] += 1
            out[family] = {
                k: {"correct": c, "total": t, "acc": (c / t if t else None)}
                for k, (c, t) in hits.items()
            }
    model.train()
    return out


def train(arm: str, seed: int) -> None:
    torch.manual_seed(seed)
    bpe = BPE()
    model = build(arm, seed)
    for p in model.trunk_parameters():
        p.requires_grad_(False)
    trainable = [p for p in model.parameters() if p.requires_grad]
    n_train = sum(p.numel() for p in trainable)
    opt = torch.optim.AdamW(trainable, lr=3e-4, weight_decay=0.01)
    history = []
    t0 = time.time()
    model.train()
    for step in range(STEPS):
        seeds = [TRAIN_SPACE + seed * 100_000 + step * BATCH + i for i in range(BATCH)]
        toks, tgts, _ = batch(seeds, bpe=bpe)
        loss = loss_fn(logits_of(model, toks.to(DEV)), tgts.to(DEV))
        loss.backward()
        opt.step()
        opt.zero_grad()
        if step % 200 == 0 or step == STEPS - 1:
            history.append({"step": step, "loss": float(loss)})
            print(f"[{arm} s{seed}] step {step} loss {float(loss):.4f}", flush=True)
            OUT.mkdir(parents=True, exist_ok=True)
            (OUT / f"{tag(arm, seed)}-progress.json").write_text(json.dumps({
                "arm": arm, "seed": seed, "step": step, "of": STEPS,
                "elapsed_sec": time.time() - t0, "history": history,
            }, indent=1))
    wall = time.time() - t0
    val = evaluate(model, bpe, VAL_SPACE, seed, n=64)
    OUT.mkdir(parents=True, exist_ok=True)
    torch.save(
        {"pathway": {n: p for n, p in model.state_dict().items() if not n.startswith(("wte", "wpe", "blocks", "ln_f"))},
         "logit_bias": model.logit_bias.detach().cpu()},
        OUT / f"{tag(arm, seed)}.pt",
    )
    (OUT / f"{tag(arm, seed)}.json").write_text(json.dumps({
        "arm": arm, "seed": seed, "steps": STEPS, "batch": BATCH,
        "trainable_params": n_train, "wall_sec": wall,
        "history": history, "validation": val,
    }, indent=1))
    print(json.dumps(val, indent=1))


def load_trained(arm: str, seed: int) -> GatedGPT2:
    model = build(arm, seed)
    saved = torch.load(OUT / f"{tag(arm, seed)}.pt", map_location=DEV)
    model.load_state_dict(saved["pathway"], strict=False)
    model.logit_bias.data = saved["logit_bias"].to(DEV)
    return model.eval()


def final(arm: str, seed: int) -> None:
    if not (ROOT / "results" / "GPT2-FLEET-FROZEN").exists():
        raise SystemExit("REFUSED: sealed final eval requires results/GPT2-FLEET-FROZEN")
    model = load_trained(arm, seed)
    res = evaluate(model, BPE(), FINAL_SPACE, seed, n=256)
    path = OUT / f"{tag(arm, seed)}-final.json"
    if path.exists():
        raise SystemExit("REFUSED: final eval already recorded (single-shot)")
    path.write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


def dial(arm: str, seed: int) -> None:
    """Probe (read) + transplant (turn) on a trained osc run."""
    model = load_trained(arm, seed)
    bpe = BPE()
    import itertools

    states, labels = [], []
    metas = []
    with torch.no_grad():
        for i in range(96):
            toks, _, seqs = batch([VAL_SPACE + 500_000 + i], bpe=bpe)
            s = seqs[0]
            ctl = model.control_states(toks.to(DEV))
            for p, slot, ans in zip(s.query_positions, s.query_slots, s.active_answer, strict=True):
                states.append(ctl[0, p].float().cpu())
                labels.append((slot, ans))
            metas.append((toks, s, ctl))
    # READ: ridge probe slot-0 answer identity at slot-0 queries
    from stencil.nl_task import ANSWER_WORDS
    xs, ys = [], []
    for st, (slot, ans) in zip(states, labels, strict=True):
        if slot == 0:
            xs.append(st)
            ys.append(ANSWER_WORDS.index(ans))
    X = torch.stack(xs)
    y = torch.tensor(ys)
    k = X.shape[0] * 3 // 4
    Y = torch.zeros(k, 16)
    Y[torch.arange(k), y[:k]] = 1
    W = torch.linalg.solve(X[:k].T @ X[:k] + 1e-3 * torch.eye(X.shape[1]), X[:k].T @ Y)
    acc = float((torch.argmax(X[k:] @ W, 1) == y[k:]).float().mean())
    print(f"READ: slot-0 answer decoded from wire at {acc:.1%} (chance 6.2%), n_test={len(y)-k}")

    # TURN: transplant donor wire trajectory; expect donor's slot-0 answer
    flips = tried = shuffle_flips = 0
    with torch.no_grad():
        for (tA, sA, _cA), (_tB, sB, cB) in itertools.pairwise(metas[:64]):
            if 0 not in sA.query_slots or 0 not in sB.query_slots:
                continue
            pa = sA.query_positions[sA.query_slots.index(0)]
            ansB = sB.active_answer[sB.query_slots.index(0)]
            ansA = sA.active_answer[sA.query_slots.index(0)]
            if ansA == ansB:
                continue
            out = model(tA.to(DEV), control_override=cB) + model.logit_bias
            pred = int(out[0, pa].argmax())
            want = bpe.encode(" " + ansB)[0]
            tried += 1
            flips += int(pred == want)
            perm = torch.randperm(cB.shape[1], generator=torch.Generator().manual_seed(tried))
            out_s = model(tA.to(DEV), control_override=cB[:, perm]) + model.logit_bias
            shuffle_flips += int(int(out_s[0, pa].argmax()) == want)
    print(f"TURN: {flips}/{tried} transplants produced the DONOR's answer; shuffle control {shuffle_flips}/{tried}")


if __name__ == "__main__":
    cmd, arm, seed = sys.argv[1], sys.argv[2], int(sys.argv[3])
    {"train": train, "final": final, "dial": dial}[cmd](arm, seed)
