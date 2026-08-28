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
from stencil.nl_task import ANSWER_WORDS, BPE, batch  # noqa: E402

OUT = ROOT / "results" / "gpt2"
STEPS = 4000
CURRICULUM_STEPS = 1000  # phase 1: "near" family (all rules in reach)
BATCH = 8
TRAIN_SPACE = 0
VAL_SPACE = 1_000_000
FINAL_SPACE = 2_000_000
DEV = "cuda" if torch.cuda.is_available() else "cpu"
LORA_RANK = 8  # full-matrix symmetric adapter, both arms (iteration 2)
HARD_SALIENCE = True  # v7: straight-through binary gate (fable gate 2)
SALIENCE_WEIGHT = 1.0  # v5: balanced BCE on salience logits (sol prescription)
AUX_WEIGHT = 0.3  # iteration 3: auxiliary wire-readout supervision (train only)
REPLAY_EVERY = 4  # iteration 3: 1 in 4 phase-2 items replays the near family


def tag(arm: str, seed: int) -> str:
    return f"{arm}-v8-s{seed}"


def build(arm: str, seed: int) -> GatedGPT2:
    model = GatedGPT2(arm, window=64, seed_init=seed, lora_rank=LORA_RANK, hard_salience=HARD_SALIENCE)
    sd = torch.load(ROOT / "models" / "gpt2-small.pt", map_location="cpu")
    missing, unexpected = model.load_state_dict(sd, strict=False)
    assert not unexpected
    if not hasattr(model, "logit_bias"):
        model.logit_bias = torch.nn.Parameter(torch.zeros(50257))
    return model.to(DEV)


def logits_of(model: GatedGPT2, toks: torch.Tensor, **kw) -> torch.Tensor:
    return model(toks, **kw) + model.logit_bias


def loss_fn(logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
    mask = targets >= 0
    assert int(mask.sum()) > 0, "no query targets in batch (vacuous)"
    return F.cross_entropy(logits[mask], targets[mask])


def evaluate(
    model: GatedGPT2, bpe: BPE, space: int, seed: int, n: int = 64,
    families: tuple[str, ...] = ("train", "drought", "burst"),
    zero_code: bool = False,
) -> dict:
    model.eval()
    out: dict = {}
    offs = {"train": 0, "drought": 30_000, "burst": 60_000, "near": 90_000}
    with torch.no_grad():
        for family in families:
            hits = {"within": [0, 0], "beyond": [0, 0]}
            base = space + seed * 100_000 + offs[family]
            for start in range(0, n, BATCH):
                seeds = list(range(base + start, base + min(start + BATCH, n)))
                toks, tgts, seqs = batch(seeds, family=family, bpe=bpe)
                kw = {}
                if zero_code:
                    kw["code_override"] = torch.zeros(toks.shape[0], toks.shape[1], 128, device=DEV)
                lg = logits_of(model, toks.to(DEV), **kw)
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


def ridge_acc(X: torch.Tensor, y: torch.Tensor, classes: int = 16) -> float:
    """Closed-form ridge probe — the capture metric of record (fable fix:
    CE-trained heads cannot amplify small-scale signals; ridge can)."""
    n = X.shape[0]
    k = n * 3 // 4
    Y = torch.zeros(k, classes)
    Y[torch.arange(k), y[:k]] = 1
    W = torch.linalg.solve(
        X[:k].T @ X[:k] + 1e-3 * torch.eye(X.shape[1]), X[:k].T @ Y
    )
    return float((torch.argmax(X[k:] @ W, 1) == y[k:]).float().mean())


def instrument_precheck() -> None:
    """The instrument must pass on codes KNOWN separable (non-vacuity)."""
    g = torch.Generator().manual_seed(0)
    means = torch.randn(16, 128, generator=g)
    y = torch.arange(320) % 16
    X = means[y] + 0.1 * torch.randn(320, 128, generator=g)
    acc = ridge_acc(X, y)
    assert acc > 0.9, f"ridge instrument vacuous: {acc}"
    print(f"instrument precheck: ridge {acc:.2%} on separable synthetic codes")


def cache_masks(seqs: list, t_len: int, dev: str) -> tuple[torch.Tensor, torch.Tensor, list, torch.Tensor]:
    """Teacher masks from ground truth: salience over statement spans, commit
    at statement ends, teacher slot ids (rules 0-3, demo statements 4+);
    labels (batch, pos, slot, answer) per rule commit."""
    b = len(seqs)
    sal = torch.zeros(b, t_len, dtype=torch.bool, device=dev)
    com = torch.zeros(b, t_len, dtype=torch.bool, device=dev)
    slot_ov = torch.full((b, t_len), -1, dtype=torch.long, device=dev)
    labels = []
    for i, s in enumerate(seqs):
        event_pos = {pos: slot for pos, slot, _ in s.rule_events}
        demo_id = 4
        for lo, hi in s.rule_spans:
            if hi - 1 >= t_len:
                continue
            sal[i, lo:hi] = True
            com[i, hi - 1] = True
            if hi - 1 in event_pos:
                slot_ov[i, hi - 1] = event_pos[hi - 1]
            else:
                slot_ov[i, hi - 1] = demo_id
                demo_id += 1
        for pos, slot, ans in s.rule_events:
            labels.append((i, pos, slot, ANSWER_WORDS.index(ans)))
    return sal, com, labels, slot_ov


def train_cache(arm: str, seed: int) -> None:
    """v8 focus-cache pilot. Teacher-forced writes during training (gates
    trained by BCE in parallel); evaluation uses the LEARNED gates only."""
    assert arm == "cache"
    instrument_precheck()
    torch.manual_seed(seed)
    bpe = BPE()
    model = build(arm, seed)
    for p in model.trunk_parameters():
        p.requires_grad_(False)
    trainable = [p for p in model.parameters() if p.requires_grad]
    gate_params = list(model.cache.salience.parameters()) + list(model.cache.commit.parameters())
    gate_ids = {id(p) for p in gate_params}
    other = [p for p in trainable if id(p) not in gate_ids]
    aux_q = torch.nn.Linear(128, 4 * len(ANSWER_WORDS)).to(DEV)
    aux_v = torch.nn.Linear(128, 4 * len(ANSWER_WORDS)).to(DEV)
    opt = torch.optim.AdamW(
        [
            {"params": other, "lr": 3e-4},
            {"params": list(aux_q.parameters()) + list(aux_v.parameters()), "lr": 3e-4, "weight_decay": 0.0},
            {"params": gate_params, "lr": 3e-3, "weight_decay": 0.0},
        ],
        weight_decay=0.01,
    )
    n_train = sum(p.numel() for p in trainable)
    history: list[dict] = []
    split_history: list[dict] = []
    evals: list[dict] = []
    t0 = time.time()
    model.train()
    for step in range(STEPS):
        seeds = [TRAIN_SPACE + seed * 100_000 + step * BATCH + i for i in range(BATCH)]
        if step < CURRICULUM_STEPS:
            fam: str | list[str] = "near"
        else:
            fam = ["near" if i % REPLAY_EVERY == 0 else "train" for i in range(BATCH)]
        toks, tgts, seqs = batch(seeds, family=fam, bpe=bpe)
        toks_d, tgts_d = toks.to(DEV), tgts.to(DEV)
        sal_m, com_m, labels, slot_ov = cache_masks(seqs, toks.shape[1], DEV)
        # teacher-forced forward (training only)
        pos_emb = torch.arange(toks.shape[1], device=DEV)
        x = model.wte(toks_d) + model.wpe(pos_emb)
        mask = model._mask(toks.shape[1], toks_d.device)
        for index in range(model.INJ_LAYERS[0]):
            x = model.blocks[index](x, mask, None, model.lora[index], None)
        code, states, internals = model.cache(
            x, sal_override=sal_m, commit_override=com_m, slot_override=slot_ov
        )
        for index in range(model.INJ_LAYERS[0], 12):
            inj = model.inject[model.INJ_LAYERS.index(index)](code)
            x = model.blocks[index](x, mask, None, model.lora[index], inj)
        logits = model.ln_f(x) @ model.wte.weight.T + model.logit_bias
        loss = loss_fn(logits, tgts_d)
        # gate teachers (balanced BCE, targets from ground truth)
        sl, cl = internals["sal_logits"], internals["commit_logits"]
        sal_loss = 0.5 * (F.softplus(-sl[sal_m]).mean() + F.softplus(sl[~sal_m]).mean())
        com_loss = 0.5 * (F.softplus(-cl[com_m]).mean() + F.softplus(cl[~com_m]).mean())
        # key-binding margin loss (R1): same-slot keys cohere, cross-slot
        # keys separate, so LEARNED addressing matches the taught slots.
        ckeys = [(slot, key) for _i, _p, _v, key, slot in internals["commits"]]
        key_loss = torch.zeros((), device=DEV)
        n_pairs = 0
        for a in range(len(ckeys)):
            for bb in range(a + 1, len(ckeys)):
                cs = F.cosine_similarity(ckeys[a][1], ckeys[bb][1], dim=0)
                if ckeys[a][0] == ckeys[bb][0]:
                    key_loss = key_loss + F.relu(0.8 - cs)
                else:
                    key_loss = key_loss + F.relu(cs - 0.5)
                n_pairs += 1
        if n_pairs:
            key_loss = key_loss / n_pairs
        # capture aux: per-slot heads on committed VALUES (wd-free)
        by_pos = {(i, p): v for i, p, v, _k, _s in internals["commits"]}
        v_states, v_slots, v_tgts = [], [], []
        for i, pos, slot, ans in labels:
            v = by_pos.get((i, pos))
            if v is not None:
                v_states.append(v)
                v_slots.append(slot)
                v_tgts.append(ans)
        v_logits = aux_v(torch.stack(v_states)).view(-1, 4, len(ANSWER_WORDS))
        v_sel = v_logits[torch.arange(len(v_slots), device=DEV), torch.tensor(v_slots, device=DEV)]
        v_tgt_t = torch.tensor(v_tgts, device=DEV)
        aux_v_ce = F.cross_entropy(v_sel, v_tgt_t)
        # retention aux: per-slot heads on the READ code at query positions
        q_states, q_slots, q_tgts = [], [], []
        for i, s in enumerate(seqs):
            for pq, slot, ans in zip(s.query_positions, s.query_slots, s.active_answer, strict=True):
                q_states.append(code[i, pq])
                q_slots.append(slot)
                q_tgts.append(ANSWER_WORDS.index(ans))
        q_logits = aux_q(torch.stack(q_states)).view(-1, 4, len(ANSWER_WORDS))
        q_sel = q_logits[torch.arange(len(q_slots), device=DEV), torch.tensor(q_slots, device=DEV)]
        q_tgt_t = torch.tensor(q_tgts, device=DEV)
        aux_q_ce = F.cross_entropy(q_sel, q_tgt_t)
        loss = loss + sal_loss + com_loss + key_loss + AUX_WEIGHT * (aux_v_ce + aux_q_ce)
        if step % 100 == 0 or step == STEPS - 1:
            with torch.no_grad():
                qmask = torch.zeros_like(tgts_d, dtype=torch.bool)
                for bqi, s in enumerate(seqs):
                    for pq in s.query_positions:
                        qmask[bqi, pq] = True
                det = logits.detach()
                split_history.append({
                    "step": step,
                    "query_ce": float(F.cross_entropy(det[qmask], tgts_d[qmask])),
                    "query_acc": float((det[qmask].argmax(-1) == tgts_d[qmask]).float().mean()),
                    "capture_ce": float(aux_v_ce.detach()),
                    "capture_acc": float((v_sel.detach().argmax(-1) == v_tgt_t).float().mean()),
                    "read_ce": float(aux_q_ce.detach()),
                    "read_acc": float((q_sel.detach().argmax(-1) == q_tgt_t).float().mean()),
                    "sal_loss": float(sal_loss.detach()),
                    "com_loss": float(com_loss.detach()),
                    "key_loss": float(key_loss.detach()),
                })
        loss.backward()
        opt.step()
        opt.zero_grad()
        if step % 200 == 0 or step == STEPS - 1:
            history.append({"step": step, "loss": float(loss.detach())})
            m = split_history[-1]
            print(
                f"[{arm} s{seed}] step {step} loss {float(loss.detach()):.4f} "
                f"query ce {m['query_ce']:.3f} acc {m['query_acc']:.2f} "
                f"CAPTURE ce {m['capture_ce']:.3f} acc {m['capture_acc']:.2f} "
                f"READ ce {m['read_ce']:.3f} acc {m['read_acc']:.2f} "
                f"sal {m['sal_loss']:.3f} com {m['com_loss']:.3f} key {m['key_loss']:.3f}",
                flush=True,
            )
        if step > 0 and (step % 500 == 0 or step == CURRICULUM_STEPS - 1):
            mid = evaluate(model, bpe, VAL_SPACE, seed, n=32, families=("near", "train"))
            mid_zero = evaluate(model, bpe, VAL_SPACE, seed, n=32, families=("train",), zero_code=True)
            ridge = ridge_capture(model, bpe, seed)
            evals.append({
                "step": step, "eval": mid, "zero_code_train": mid_zero["train"],
                "ridge": ridge,
            })
            torch.save(
                {"pathway": {n_: p_ for n_, p_ in model.state_dict().items() if not n_.startswith(("wte", "wpe", "blocks", "ln_f"))},
                 "logit_bias": model.logit_bias.detach().cpu(), "step": step,
                 "aux_q": aux_q.state_dict(), "aux_v": aux_v.state_dict()},
                OUT / f"{tag(arm, seed)}-ckpt.pt",
            )
            bz = mid_zero["train"]["beyond"]["acc"]
            print(
                f"[{arm} s{seed}] step {step} EVAL near-within {mid['near']['within']['acc']} "
                f"train within {mid['train']['within']['acc']} beyond {mid['train']['beyond']['acc']} "
                f"beyond-ZEROCODE {bz} RIDGE cap {ridge['capture']} read {ridge['read']} "
                f"salPR {ridge['sal_pr']} comPR {ridge['com_pr']} occ {ridge['mean_occupancy']} "
                f"advWrites {ridge['adversarial_writes']}",
                flush=True,
            )
        if step % 200 == 0 or step == STEPS - 1:
            OUT.mkdir(parents=True, exist_ok=True)
            (OUT / f"{tag(arm, seed)}-progress.json").write_text(json.dumps({
                "arm": arm, "seed": seed, "step": step, "of": STEPS,
                "elapsed_sec": time.time() - t0, "history": history,
                "split_history": split_history, "evals": evals,
            }, indent=1))
    wall = time.time() - t0
    val = evaluate(model, bpe, VAL_SPACE, seed, n=64)
    OUT.mkdir(parents=True, exist_ok=True)
    torch.save(
        {"pathway": {n_: p_ for n_, p_ in model.state_dict().items() if not n_.startswith(("wte", "wpe", "blocks", "ln_f"))},
         "logit_bias": model.logit_bias.detach().cpu(),
         "aux_q": aux_q.state_dict(), "aux_v": aux_v.state_dict()},
        OUT / f"{tag(arm, seed)}.pt",
    )
    (OUT / f"{tag(arm, seed)}.json").write_text(json.dumps({
        "arm": arm, "seed": seed, "steps": STEPS, "batch": BATCH,
        "trainable_params": n_train, "wall_sec": wall,
        "history": history, "split_history": split_history, "evals": evals,
        "validation": val,
    }, indent=1))
    print(json.dumps(val, indent=1))


def ridge_capture(model: GatedGPT2, bpe: BPE, seed: int, n: int = 48) -> dict:
    """Metrics of record (closed-form ridge, teacher-forced gates):
    - capture: per-slot on committed values (writer quality);
    - read: per-slot on the READ code at query positions (store+addressing —
      overwritten/collided slots FAIL here; R2 fix);
    plus learned-gate precision/recall vs teacher masks (R5) and an
    adversarial no-write count on slot-word-bearing filler (R6)."""
    model.eval()
    cap: dict[int, tuple[list, list]] = {s: ([], []) for s in range(4)}
    red: dict[int, tuple[list, list]] = {s: ([], []) for s in range(4)}
    pr = {"sal_tp": 0, "sal_fp": 0, "sal_fn": 0, "com_tp": 0, "com_fp": 0, "com_fn": 0}
    occupancy: list[int] = []
    with torch.no_grad():
        for i in range(n):
            toks, _, seqs = batch([VAL_SPACE + 700_000 + seed * 10_000 + i], bpe=bpe)
            s = seqs[0]
            toks_d = toks.to(DEV)
            sal_m, com_m, labels, slot_ov = cache_masks(seqs, toks.shape[1], DEV)
            pos_emb = torch.arange(toks.shape[1], device=DEV)
            x = model.wte(toks_d) + model.wpe(pos_emb)
            mask = model._mask(toks.shape[1], toks_d.device)
            for index in range(model.INJ_LAYERS[0]):
                x = model.blocks[index](x, mask, None, model.lora[index], None)
            code, states, internals = model.cache(
                x, sal_override=sal_m, commit_override=com_m, slot_override=slot_ov
            )
            occupancy.append(len(states[0].slots))
            by_pos = {(bi, p): v for bi, p, v, _k, _s in internals["commits"]}
            for bi, pos, slot, ans in labels:
                v = by_pos.get((bi, pos))
                if v is not None:
                    cap[slot][0].append(v.float().cpu())
                    cap[slot][1].append(ans)
            for pq, slot, ans in zip(s.query_positions, s.query_slots, s.active_answer, strict=True):
                red[slot][0].append(code[0, pq].float().cpu())
                red[slot][1].append(ANSWER_WORDS.index(ans))
            # learned-gate PR on the same hidden states
            sal_l = (torch.sigmoid(internals["sal_logits"]) > 0.5)
            com_l = (torch.sigmoid(internals["commit_logits"]) > 0.5)
            pr["sal_tp"] += int((sal_l & sal_m).sum())
            pr["sal_fp"] += int((sal_l & ~sal_m).sum())
            pr["sal_fn"] += int((~sal_l & sal_m).sum())
            pr["com_tp"] += int((com_l & com_m).sum())
            pr["com_fp"] += int((com_l & ~com_m).sum())
            pr["com_fn"] += int((~com_l & com_m).sum())
    # R6: adversarial filler with quoted slot words, LEARNED gates: count writes
    adv = 'The word "cat" was mentioned near the "king" and the "sun" today. '
    adv_toks = torch.tensor([ (bpe.encode(adv * 12))[:512] ], device=DEV)
    with torch.no_grad():
        pos_emb = torch.arange(adv_toks.shape[1], device=DEV)
        x = model.wte(adv_toks) + model.wpe(pos_emb)
        mask = model._mask(adv_toks.shape[1], DEV)
        for index in range(model.INJ_LAYERS[0]):
            x = model.blocks[index](x, mask, None, model.lora[index], None)
        _, adv_states, _ = model.cache(x)
    model.train()

    def probe(d: dict) -> list:
        out = []
        for s2 in range(4):
            xs, ys = d[s2]
            if len(ys) < 24:
                out.append(None)
                continue
            out.append(round(ridge_acc(torch.stack(xs), torch.tensor(ys)), 3))
        return out

    def prf(tp: int, fp: int, fn: int) -> list:
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        return [round(prec, 3), round(rec, 3)]

    return {
        "capture": probe(cap),
        "read": probe(red),
        "sal_pr": prf(pr["sal_tp"], pr["sal_fp"], pr["sal_fn"]),
        "com_pr": prf(pr["com_tp"], pr["com_fp"], pr["com_fn"]),
        "mean_occupancy": round(sum(occupancy) / len(occupancy), 2),
        "adversarial_writes": len(adv_states[0].slots),
    }


def gate_stats(model: GatedGPT2, bpe: BPE) -> dict:
    """Quantiles of the gates and the salience gate over one sequence."""
    qs = torch.tensor([0.01, 0.25, 0.5, 0.75, 0.99])
    with torch.no_grad():
        toks, _, _ = batch([VAL_SPACE + 999_000], bpe=bpe)
        control = model.control_states(toks.to(DEV))
        control = control * torch.rsqrt(control.pow(2).mean(-1, keepdim=True) + 1e-8)
        g = model.gate_source(control).flatten().float().cpu()
        sal = torch.sigmoid(model.salience(model.wte(toks.to(DEV)))).flatten().float().cpu()
    return {
        "gates": [round(float(v), 4) for v in torch.quantile(g, qs)],
        "salience": [round(float(v), 4) for v in torch.quantile(sal, qs)],
    }


def train(arm: str, seed: int) -> None:
    torch.manual_seed(seed)
    bpe = BPE()
    model = build(arm, seed)
    for p in model.trunk_parameters():
        p.requires_grad_(False)
    trainable = [p for p in model.parameters() if p.requires_grad]
    n_train = sum(p.numel() for p in trainable)
    # Aux head reads the active answer straight off the injection code at
    # query positions (train-time only; lives OUTSIDE the model so the eval
    # path cannot see it).
    aux_head = torch.nn.Linear(128, 4 * len(ANSWER_WORDS)).to(DEV)  # per-slot heads (sol audit finding 6)
    salience_params = list(model.salience.parameters())
    salience_ids = {id(p) for p in salience_params}
    other_params = [p for p in trainable if id(p) not in salience_ids]
    opt = torch.optim.AdamW(
        [
            {"params": other_params + list(aux_head.parameters()), "lr": 3e-4},
            {"params": salience_params, "lr": 3e-3, "weight_decay": 0.0},
        ],
        weight_decay=0.01,
    )
    history = []
    split_history: list[dict] = []
    evals: list[dict] = []
    t0 = time.time()
    model.train()
    for step in range(STEPS):
        seeds = [TRAIN_SPACE + seed * 100_000 + step * BATCH + i for i in range(BATCH)]
        if step < CURRICULUM_STEPS:
            fam: str | list[str] = "near"
        else:
            fam = ["near" if i % REPLAY_EVERY == 0 else "train" for i in range(BATCH)]
        toks, tgts, seqs = batch(seeds, family=fam, bpe=bpe)
        toks_d, tgts_d = toks.to(DEV), tgts.to(DEV)
        logits = logits_of(model, toks_d)
        loss = loss_fn(logits, tgts_d)
        code = model.injection_code(toks_d)
        aux_states, aux_targets, aux_slots = [], [], []
        n_query_aux = 0
        for b, s in enumerate(seqs):
            for p, slot, ans in zip(s.query_positions, s.query_slots, s.active_answer, strict=True):
                aux_states.append(code[b, p])
                aux_targets.append(ANSWER_WORDS.index(ans))
                aux_slots.append(slot)
                n_query_aux += 1
        # v6: capture supervision — read the just-stated answer off the wire
        # at every statement end (retention supervision above stays).
        for b, s in enumerate(seqs):
            for p, slot, ans in s.rule_events:
                aux_states.append(code[b, p])
                aux_targets.append(ANSWER_WORDS.index(ans))
                aux_slots.append(slot)
        aux_logits = aux_head(torch.stack(aux_states)).view(-1, 4, len(ANSWER_WORDS))
        aux_sel = aux_logits[torch.arange(len(aux_slots), device=DEV), torch.tensor(aux_slots, device=DEV)]
        aux_tgt = torch.tensor(aux_targets, device=DEV)
        aux_ce = F.cross_entropy(aux_sel, aux_tgt)
        # v5: direct balanced supervision on the salience logits — rule/update
        # statement spans open, everything else closed. Train-time only; eval
        # computes salience from embeddings with no span information.
        sal_logits = model.salience(model.wte(toks_d)).squeeze(-1)
        rule_mask = torch.zeros_like(toks_d, dtype=torch.bool)
        for b, s in enumerate(seqs):
            for lo, hi in s.rule_spans:
                rule_mask[b, lo:hi] = True
        sal_loss = 0.5 * (
            F.softplus(-sal_logits[rule_mask]).mean()
            + F.softplus(sal_logits[~rule_mask]).mean()
        )
        loss = loss + AUX_WEIGHT * aux_ce + SALIENCE_WEIGHT * sal_loss
        if step % 100 == 0 or step == STEPS - 1:
            # sol MI-review finding 4: split real-query vs demo metrics live.
            with torch.no_grad():
                qmask = torch.zeros_like(tgts_d, dtype=torch.bool)
                for b, s in enumerate(seqs):
                    for p in s.query_positions:
                        qmask[b, p] = True
                dmask = (tgts_d >= 0) & ~qmask
                det = logits.detach()
                m = {
                    "step": step, "family": fam,
                    "query_ce": float(F.cross_entropy(det[qmask], tgts_d[qmask])),
                    "query_acc": float((det[qmask].argmax(-1) == tgts_d[qmask]).float().mean()),
                    "demo_ce": float(F.cross_entropy(det[dmask], tgts_d[dmask])),
                    "demo_acc": float((det[dmask].argmax(-1) == tgts_d[dmask]).float().mean()),
                    "aux_ce": float(aux_ce.detach()),
                    "aux_q_ce": float(F.cross_entropy(aux_sel.detach()[:n_query_aux], aux_tgt[:n_query_aux])),
                    "aux_r_ce": float(F.cross_entropy(aux_sel.detach()[n_query_aux:], aux_tgt[n_query_aux:])),
                    "aux_acc": float((aux_sel.detach().argmax(-1) == aux_tgt).float().mean()),
                    "sal_loss": float(sal_loss.detach()),
                    "sal_rule_med": float(torch.sigmoid(sal_logits.detach()[rule_mask]).median()),
                    "sal_filler_p90": float(torch.quantile(torch.sigmoid(sal_logits.detach()[~rule_mask]), 0.9)),
                }
            split_history.append(m)
        loss.backward()
        opt.step()
        opt.zero_grad()
        if step % 200 == 0 or step == STEPS - 1:
            history.append({"step": step, "loss": float(loss.detach())})
            m = split_history[-1]
            print(
                f"[{arm} s{seed}] step {step} loss {float(loss.detach()):.4f} "
                f"query ce {m['query_ce']:.3f} acc {m['query_acc']:.2f} "
                f"demo ce {m['demo_ce']:.3f} acc {m['demo_acc']:.2f} "
                f"aux q-ce {m['aux_q_ce']:.3f} r-ce {m['aux_r_ce']:.3f} acc {m['aux_acc']:.2f} "
                f"sal loss {m['sal_loss']:.3f} rule-med {m['sal_rule_med']:.2f} filler-p90 {m['sal_filler_p90']:.3f}",
                flush=True,
            )
        if step > 0 and (step % 500 == 0 or step == CURRICULUM_STEPS - 1):
            mid = evaluate(model, bpe, VAL_SPACE, seed, n=32, families=("near", "train"))
            gq = gate_stats(model, bpe)
            evals.append({"step": step, "eval": mid, "gate_quantiles": gq})
            torch.save(
                {"pathway": {n_: p_ for n_, p_ in model.state_dict().items() if not n_.startswith(("wte", "wpe", "blocks", "ln_f"))},
                 "logit_bias": model.logit_bias.detach().cpu(), "step": step,
                 "aux_head": aux_head.state_dict()},
                OUT / f"{tag(arm, seed)}-ckpt.pt",
            )
            near_w = mid["near"]["within"]["acc"]
            tr = mid["train"]
            print(
                f"[{arm} s{seed}] step {step} EVAL near-within {near_w} "
                f"train within {tr['within']['acc']} beyond {tr['beyond']['acc']} "
                f"gates {gq['gates']} salience {gq['salience']}",
                flush=True,
            )
        if step % 200 == 0 or step == STEPS - 1:
            OUT.mkdir(parents=True, exist_ok=True)
            (OUT / f"{tag(arm, seed)}-progress.json").write_text(json.dumps({
                "arm": arm, "seed": seed, "step": step, "of": STEPS,
                "elapsed_sec": time.time() - t0, "history": history,
                "split_history": split_history, "evals": evals,
            }, indent=1))
    wall = time.time() - t0
    val = evaluate(model, bpe, VAL_SPACE, seed, n=64)
    OUT.mkdir(parents=True, exist_ok=True)
    torch.save(
        {"pathway": {n: p for n, p in model.state_dict().items() if not n.startswith(("wte", "wpe", "blocks", "ln_f"))},
         "logit_bias": model.logit_bias.detach().cpu(),
         "aux_head": aux_head.state_dict()},
        OUT / f"{tag(arm, seed)}.pt",
    )
    (OUT / f"{tag(arm, seed)}.json").write_text(json.dumps({
        "arm": arm, "seed": seed, "steps": STEPS, "batch": BATCH,
        "trainable_params": n_train, "wall_sec": wall,
        "history": history, "split_history": split_history, "evals": evals,
        "validation": val,
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
    if cmd == "train" and arm == "cache":
        train_cache(arm, seed)
    else:
        {"train": train, "final": final, "dial": dial}[cmd](arm, seed)
