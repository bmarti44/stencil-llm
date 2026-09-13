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

import stencil.determinism  # noqa: E402, F401  (sets CUBLAS workspace before torch)
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


def verify_frozen_train(sessions) -> str:
    """Astra F15: refuse to train unless the generated pool matches the frozen record."""
    import hashlib
    from dataclasses import asdict

    frozen = json.loads((ROOT / "results/a-screen/train-pool.json").read_text())
    assert not frozen["problems"], f"frozen pool records problems: {frozen['problems']}"
    assert len(sessions) == frozen["n"], (
        f"{len(sessions)} sessions, frozen {frozen['n']}"
    )
    for s in sessions:
        want = frozen["hashes"][s.id]
        got = hashlib.sha256(
            json.dumps(asdict(s), sort_keys=True).encode()
        ).hexdigest()[:16]
        assert got == want, f"{s.id}: content {got}, frozen {want}"
    return frozen["pool_sha256"]


def build_examples(tok, limit: int = 0) -> list[dict]:
    """One example per (prompt, chosen, rejected) triple, prompts packed exactly as the
    harness packs them."""
    count = A.make_counter(tok)
    im_end = tok.convert_tokens_to_ids("<|im_end|>")
    out = []
    sessions = train_sessions()
    if limit:
        sessions = sessions[:limit]
    else:
        verify_frozen_train(sessions)
    for s in sessions:
        for p in A.pairs_from_session(s):
            # re-review round 3: one packing policy path, shared with the harness, so the
            # trained prompts and the evaluated prompts cannot drift apart
            packed, kept = A.pack_session(s, list(p.messages), 2, count)
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
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
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
    prep_seconds = time.time() - t_start
    ref: dict[int, tuple[float, float]] = {}
    ref_tokens = 0
    t_ref = time.time()
    if a.objective == "cf":
        model.eval()
        with torch.no_grad():
            for i, e in enumerate(examples):
                # Astra F13: reference scoring lives inside the allocation and must not
                # consume all of it; a run that cannot fit it is cost-ineligible.
                if time.time() - t_start >= budget_s:
                    # re-review F13: §8's reading for an exhausted allocation is INCOMPLETE.
                    # No adapter exists yet, so the marker is the train log the harness
                    # reads: status "incomplete" and final false both refuse evaluation.
                    out.mkdir(parents=True, exist_ok=True)
                    (out / "train-log.json").write_text(
                        json.dumps(
                            {
                                "objective": a.objective,
                                "status": "incomplete",
                                "final": False,
                                "steps": 0,
                                "budget_seconds": budget_s,
                                "reference_examples_scored": i,
                                "incomplete_reason": (
                                    "reference scoring exhausted the allocation"
                                ),
                            },
                            indent=1,
                        )
                        + "\n"
                    )
                    print(
                        "INCOMPLETE: reference scoring exhausted the allocation; "
                        "no adapter from this allocation may be evaluated"
                    )
                    sys.exit(3)
                c, _ = seq_logprobs(model, e["prompt_ids"], e["chosen_ids"])
                r, _ = seq_logprobs(model, e["prompt_ids"], e["rejected_ids"])
                ref[i] = (c.item(), r.item())
                ref_tokens += (
                    2 * len(e["prompt_ids"])
                    + len(e["chosen_ids"])
                    + len(e["rejected_ids"])
                )
                if i % 100 == 0:
                    print(f"ref {i}/{len(examples)} {time.time() - t_start:.0f}s")
        print(f"reference scoring done in {time.time() - t_ref:.0f}s")
    reference_seconds = time.time() - t_ref

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

    import hashlib

    def _sha(text: str) -> str:
        return hashlib.sha256(text.encode()).hexdigest()[:16]

    log: dict = {
        "objective": a.objective,
        "identity": {
            "train_pool_sha256": json.loads(
                (ROOT / "results/a-screen/train-pool.json").read_text()
            )["pool_sha256"],
            "a_screen_sha256": _sha((ROOT / "src/stencil/a_screen.py").read_text()),
            "a_train_pool_sha256": _sha(
                (ROOT / "src/stencil/a_train_pool.py").read_text()
            ),
            "trainer_sha256": _sha(Path(__file__).read_text()),
            "hub": str(a.hub),
            "limit": a.limit,
        },
        "seed": a.seed,
        "lr": a.lr,
        "rank": a.rank,
        "alpha": a.alpha,
        "beta": a.beta,
        "dpo_weight": a.dpo_weight,
        "accum": a.accum,
        "examples": len(examples),
        "budget_seconds": budget_s,
        "prep_seconds": prep_seconds,
        "reference_seconds": reference_seconds,
        "reference_tokens": ref_tokens,
        "steps": 0,
        "micro_steps": 0,
        "discarded_micro_steps": 0,
        "epochs_completed": 0,
        "completion_tokens_seen": 0,
        "chosen_tokens_seen": 0,
        "rejected_tokens_seen": 0,
        "sequence_tokens_seen": 0,
        "final_update_loss": None,
        "loss_history": [],
        "status": "running",
    }

    save_times: list[float] = []

    def save(final: bool) -> None:
        t_save = time.time()
        model.save_pretrained(str(out))
        save_times.append(time.time() - t_save)
        log["seconds"] = time.time() - t_start
        log["save_seconds"] = log.get("save_seconds", 0.0) + save_times[-1]
        log["final"] = final
        # re-review round 3 F13: an allocation that produced no completed optimizer step is
        # INCOMPLETE, not complete; the harness refuses either way.
        if not final:
            log["status"] = "running"
        else:
            log["status"] = "complete" if log.get("steps", 0) >= 1 else "incomplete"
        (out / "train-log.json").write_text(json.dumps(log, indent=1) + "\n")

    model.train()
    rng = random.Random(a.seed)
    order = list(range(len(examples)))
    micro = 0
    last_save = time.time()
    window: list[float] = []
    update: list[float] = []
    micro_times: list[float] = []
    step_times: list[float] = []
    stop = False
    t_train = time.time()
    while not stop:
        rng.shuffle(order)
        for i in order:
            # Astra F13: stop BEFORE a micro-step that would cross the allocation
            elapsed = time.time() - t_start
            # re-review round 3 F13: the estimate covers a micro-step AND the optimizer step
            # that may follow it; the reserve covers the final save.
            est = max(micro_times[-20:], default=0.0) + max(
                step_times[-20:], default=0.0
            )
            reserve = max(save_times) if save_times else 60.0
            if elapsed + est + reserve >= budget_s:
                stop = True
                break
            t_micro = time.time()
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
            micro_times.append(time.time() - t_micro)
            log["micro_steps"] = micro
            log["completion_tokens_seen"] += n_c
            log["chosen_tokens_seen"] += len(e["prompt_ids"]) + n_c
            if a.objective == "cf":
                log["rejected_tokens_seen"] += len(e["prompt_ids"]) + len(
                    e["rejected_ids"]
                )
            log["sequence_tokens_seen"] = (
                log["chosen_tokens_seen"] + log["rejected_tokens_seen"]
            )
            window.append(loss.item())
            update.append(loss.item())
            if micro % a.accum == 0:
                t_step = time.time()
                torch.nn.utils.clip_grad_norm_(params, 1.0)
                opt.step()
                opt.zero_grad(set_to_none=True)
                step_times.append(time.time() - t_step)
                log["steps"] += 1
                # re-review F6: the mean over THIS update's micro-steps.  ``window`` is the
                # ten-update print window and clears only every tenth update, so reusing it
                # here reported the average of up to ten updates as the final one.
                log["final_update_loss"] = sum(update) / len(update)
                update = []
                if log["steps"] % 10 == 0:
                    avg = sum(window) / len(window)
                    log["loss_history"].append([log["steps"], avg])
                    print(
                        f"step {log['steps']} loss {avg:.4f} micro {micro} "
                        f"{time.time() - t_start:.0f}s/{budget_s:.0f}s"
                    )
                    window = []
                # re-review round 3 F13: a periodic save must not consume the allowance
                # reserved for the final one, so it only runs with room for BOTH.
                room = budget_s - (time.time() - t_start)
                if time.time() - last_save > a.save_every_min * 60 and room > 2 * (
                    max(save_times) if save_times else 60.0
                ):
                    save(final=False)
                    last_save = time.time()
        else:
            log["epochs_completed"] += 1
    # discard any partial accumulation: the FINAL COMPLETED update is the adapter
    log["discarded_micro_steps"] = micro % a.accum
    log["train_seconds"] = time.time() - t_train
    opt.zero_grad(set_to_none=True)
    save(final=True)
    print(
        f"DONE objective={a.objective} steps={log['steps']} epochs={log['epochs_completed']} "
        f"discarded={log['discarded_micro_steps']} tokens={log['sequence_tokens_seen']} "
        f"final_loss={log['final_update_loss']} seconds={log['seconds']:.0f}"
    )


if __name__ == "__main__":
    main()
