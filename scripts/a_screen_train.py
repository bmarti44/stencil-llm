# ruff: noqa: E501
"""Train one adapter for the candidate-A screen (registration §3-§4).

Arms: ``sft`` = completion-token mean cross-entropy on every positive (both
counterfactual directions and the irrelevant-history variants); ``cf`` = the same
cross-entropy + 0.1 * L_DPO (beta 0.1, frozen trunk as reference, reference log-probs
precomputed once with the adapter disabled) against the stale-alternative gold.
LoRA rank 16 / alpha 32 / dropout 0 on every attention and MLP projection, AdamW lr 1e-4,
weight decay 0, clipping 1.0, seed 0, micro-batch 1 with 8-step accumulation, bf16
trunk frozen.  Fixed wall-clock allocation (``--hours 4``, reference scoring included);
the FINAL completed optimizer step is saved, never a selected checkpoint.

Usage (through tools/gpu_reserve.sh):
  uv run python scripts/a_screen_train.py --objective cf --out results/a-screen/adapters/cf
Smoke: ``--limit 8 --minutes 3``.
"""

from __future__ import annotations

import argparse
import functools
import json
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from stencil import a_screen as A  # noqa: E402
from stencil.a_train_pool import train_sessions  # noqa: E402

print = functools.partial(print, flush=True)  # noqa: A001

TARGET_MODULES = [
    "q_proj",
    "k_proj",
    "v_proj",
    "o_proj",
    "gate_proj",
    "up_proj",
    "down_proj",
]


def build_examples(tok, limit: int = 0) -> list[dict]:
    """One example per (prompt, chosen, rejected) triple, prompts packed exactly as the
    harness packs them."""
    count = A.make_counter(tok)
    im_end = tok.convert_tokens_to_ids("<|im_end|>")
    out = []
    sessions = train_sessions()
    if limit:
        sessions = sessions[:limit]
    for s in sessions:
        for p in A.pairs_from_session(s):
            packed, kept = A.pack(list(p.messages), count)
            prompt = A.render_prompt(tok, packed)
            pid = tok(prompt, add_special_tokens=False)["input_ids"]
            ch = tok(p.chosen, add_special_tokens=False)["input_ids"] + [im_end]
            rj = tok(p.rejected, add_special_tokens=False)["input_ids"] + [im_end]
            out.append(
                {
                    "session": p.session,
                    "variant": p.variant,
                    "prompt_ids": pid,
                    "chosen_ids": ch,
                    "rejected_ids": rj,
                    "kept": kept,
                }
            )
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--objective", choices=["sft", "cf"], required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--hub", default=str(ROOT / "deploy/stencil_focus/build/hub-4b"))
    ap.add_argument("--hours", type=float, default=4.0)
    ap.add_argument(
        "--minutes", type=float, default=0.0, help="smoke override of --hours"
    )
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--rank", type=int, default=16)
    ap.add_argument("--alpha", type=int, default=32)
    ap.add_argument("--beta", type=float, default=0.1)
    ap.add_argument("--dpo-weight", type=float, default=0.1)
    ap.add_argument("--accum", type=int, default=8)
    ap.add_argument("--limit", type=int, default=0, help="smoke: first N sessions")
    ap.add_argument("--save-every-min", type=float, default=30.0)
    a = ap.parse_args()
    budget_s = a.minutes * 60 if a.minutes else a.hours * 3600
    t_start = time.time()

    import torch
    import torch.nn.functional as F
    from peft import LoraConfig, get_peft_model
    from transformers import AutoModelForCausalLM, AutoTokenizer

    torch.manual_seed(a.seed)
    random.seed(a.seed)
    tok = AutoTokenizer.from_pretrained(a.hub, trust_remote_code=True)
    examples = build_examples(tok, a.limit)
    lens = [
        len(e["prompt_ids"]) + max(len(e["chosen_ids"]), len(e["rejected_ids"]))
        for e in examples
    ]
    print(
        f"examples={len(examples)} max_len={max(lens)} mean_len={sum(lens) / len(lens):.0f}"
    )
    assert max(lens) <= 4096, "a training sequence exceeds the 4,096-token window"

    model = AutoModelForCausalLM.from_pretrained(
        a.hub, trust_remote_code=True, dtype=torch.bfloat16, device_map="cuda"
    )
    model.config.use_cache = False
    dev = model.device

    def seq_logprobs(
        m, prompt_ids: list[int], comp_ids: list[int]
    ) -> tuple[torch.Tensor, int]:
        """(sum of completion-token log-probs, n completion tokens)."""
        ids = torch.tensor([prompt_ids + comp_ids], device=dev)
        logits = (
            m(input_ids=ids, attention_mask=torch.ones_like(ids)).logits[0, :-1].float()
        )
        targets = ids[0, 1:]
        lp = torch.log_softmax(logits, dim=-1).gather(1, targets[:, None])[:, 0]
        n = len(comp_ids)
        return lp[-n:].sum(), n

    # ---- reference log-probs (cf only), adapter absent, counted in the allocation
    ref: dict[int, tuple[float, float]] = {}
    if a.objective == "cf":
        model.eval()
        with torch.no_grad():
            for i, e in enumerate(examples):
                c, _ = seq_logprobs(model, e["prompt_ids"], e["chosen_ids"])
                r, _ = seq_logprobs(model, e["prompt_ids"], e["rejected_ids"])
                ref[i] = (c.item(), r.item())
                if i % 100 == 0:
                    print(f"ref {i}/{len(examples)} {time.time() - t_start:.0f}s")
        print(f"reference scoring done in {time.time() - t_start:.0f}s")

    cfg = LoraConfig(
        r=a.rank,
        lora_alpha=a.alpha,
        lora_dropout=0.0,
        target_modules=TARGET_MODULES,
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, cfg)
    for _n, p in model.named_parameters():
        if p.requires_grad:
            p.data = p.data.float()
    model.print_trainable_parameters()
    model.gradient_checkpointing_enable()
    model.enable_input_require_grads()
    params = [p for p in model.parameters() if p.requires_grad]
    opt = torch.optim.AdamW(params, lr=a.lr, weight_decay=0.0)

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    log: dict = {
        "objective": a.objective,
        "seed": a.seed,
        "lr": a.lr,
        "rank": a.rank,
        "alpha": a.alpha,
        "beta": a.beta,
        "dpo_weight": a.dpo_weight,
        "accum": a.accum,
        "examples": len(examples),
        "budget_seconds": budget_s,
        "reference_seconds": time.time() - t_start,
        "steps": 0,
        "micro_steps": 0,
        "epochs_completed": 0,
        "completion_tokens_seen": 0,
        "sequence_tokens_seen": 0,
        "loss_history": [],
    }

    def save(final: bool) -> None:
        model.save_pretrained(str(out))
        log["seconds"] = time.time() - t_start
        log["final"] = final
        (out / "train-log.json").write_text(json.dumps(log, indent=1) + "\n")

    model.train()
    rng = random.Random(a.seed)
    order = list(range(len(examples)))
    micro = 0
    last_save = time.time()
    window: list[float] = []
    stop = False
    while not stop:
        rng.shuffle(order)
        for i in order:
            if time.time() - t_start >= budget_s:
                stop = True
                break
            e = examples[i]
            with torch.autocast("cuda", dtype=torch.bfloat16):
                lp_c, n_c = seq_logprobs(model, e["prompt_ids"], e["chosen_ids"])
                loss = -lp_c / n_c
                if a.objective == "cf":
                    lp_r, _ = seq_logprobs(model, e["prompt_ids"], e["rejected_ids"])
                    rc, rr = ref[i]
                    margin = a.beta * ((lp_c - rc) - (lp_r - rr))
                    loss = loss + a.dpo_weight * (-F.logsigmoid(margin))
            (loss / a.accum).backward()
            micro += 1
            log["micro_steps"] = micro
            log["completion_tokens_seen"] += n_c
            log["sequence_tokens_seen"] += len(e["prompt_ids"]) + n_c
            window.append(loss.item())
            if micro % a.accum == 0:
                torch.nn.utils.clip_grad_norm_(params, 1.0)
                opt.step()
                opt.zero_grad(set_to_none=True)
                log["steps"] += 1
                if log["steps"] % 10 == 0:
                    avg = sum(window) / len(window)
                    log["loss_history"].append([log["steps"], avg])
                    print(
                        f"step {log['steps']} loss {avg:.4f} micro {micro} "
                        f"{time.time() - t_start:.0f}s/{budget_s:.0f}s"
                    )
                    window = []
                if time.time() - last_save > a.save_every_min * 60:
                    save(final=False)
                    last_save = time.time()
        else:
            log["epochs_completed"] += 1
    # discard any partial accumulation: the FINAL COMPLETED update is the adapter
    opt.zero_grad(set_to_none=True)
    save(final=True)
    print(
        f"DONE objective={a.objective} steps={log['steps']} epochs={log['epochs_completed']} "
        f"tokens={log['sequence_tokens_seen']} seconds={log['seconds']:.0f}"
    )


if __name__ == "__main__":
    main()
