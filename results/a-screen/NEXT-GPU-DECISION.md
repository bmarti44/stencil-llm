# The one decision left, and the exact commands either way

> **BLOCKED. 2026-09-13, Brian: "pause all GPU work until further notice."**
> Nothing in this file may be executed until Brian lifts that in his own words.
> It is written out in full so that acting on a future "yes" costs no thinking
> time — it is a runbook, not a plan of record, and it is not authorization.

## The decision

Evaluate the finished `cf` adapter on the frozen 48 sessions: **~1 GPU-hour**,
one command. That converts candidate A from unmeasured to measured. The `off`
baseline is reused (see `RUNNER-EXCEPTION.md`), which is why it is one hour and
not 4.5.

**What a "yes" buys.** The screen has never been run with an adapter. Today the
honest statement is "a descriptive baseline failure analysis and no evidence
either way about the intervention." After the hour it is either a measured
positive worth funding a matched SFT arm to attribute, or a measured null that
closes candidate A cleanly instead of leaving it ambiguous.

**What a "yes" does not buy.** `cf` vs `off` cannot isolate the counterfactual
objective — `cf` contains ordinary supervised training too. Attribution needs
the matched SFT arm, which is a second decision, taken only if the first result
warrants it.

**Honest prior.** Astra puts the direction at 20%, below the 25% bar. The
strongest reason to spend the hour anyway is that the baseline's failure mode is
real and specific — 12/36 changed-convention replies followed the superseded
rule, 8 of them with working code — so there is a large, clearly-defined error
for an intervention to remove. The strongest reason not to is that the loss is
largely prior art (Context-DPO, Bi et al., ACL 2025) and a positive result would
be a replication in a new workload, not a new method.

## If yes: evaluate cf (~1 GPU-h)

```bash
cd /home/bmarti44/stencil-llm
export STENCIL_GPU_SHARE=1

# 1. the adapter is eligible (CPU, one second)
uv run python results/a-screen/analysis/preflight.py check \
  results/a-screen/adapters/cf --arm cf \
  --hub /home/bmarti44/stencil-llm/deploy/stencil_focus/build/hub-4b

# 2. message the peer BEFORE launching (run > 30 min), then launch detached
(
  setsid nohup bash -c 'cd /home/bmarti44/stencil-llm && \
    tools/gpu_reserve.sh a-screen-eval-cf 75 26 -- \
      uv run python scripts/a_screen_run.py \
        --arm cf \
        --adapter /home/bmarti44/stencil-llm/results/a-screen/adapters/cf \
        --hub /home/bmarti44/stencil-llm/deploy/stencil_focus/build/hub-4b \
        --out /home/bmarti44/stencil-llm/results/a-screen/runs/cf.jsonl \
        --budget-min 100' \
    >/dev/null 2>&1 & echo $! >> /home/bmarti44/stencil-llm/.stencil-owned-pids
)
```

`--budget-min 100` is `ARM_BUDGET_MIN`, set from the MEASURED 35.75 s mean
generation time with the registered 1.5x contention factor.

**The 26 GiB declaration, derived not guessed.** Evaluation is inference only:
no reference scoring, no optimiser or gradient state. Qwen3-4B bf16 weights are
~8 GiB; the KV cache at the 4,096-position ceiling is 36 layers x 8 KV heads x
128 dim x 2 (K and V) x 4,096 x 2 bytes = ~0.6 GiB; fp32 logits are 151,936
floats = 0.6 MB per step. That is ~10-12 GiB of real usage, and 26 GiB is
roughly twice it. The margin is deliberate: the training run was declared at
24 GB and peaked at 56,516 MiB (2.35x), because a figure measured on a
different workload was reused and because PyTorch's caching allocator holds the
high-water mark. **This number is an upper bound to be corrected by
measurement, not a measurement** — sample `nvidia-smi` during the run and
rewrite the reservation the moment it exceeds the declaration, then tell the
peer.

Then, CPU only:

```bash
uv run python results/a-screen/analysis/stale2.py results/a-screen/runs/cf.jsonl
uv run python results/a-screen/analysis/compare.py \
  results/a-screen/runs/off-oldrunner.jsonl results/a-screen/runs/cf.jsonl \
  --runner-exception "RUNNER-EXCEPTION.md, verified by runner_equivalence.py"
```

`compare.py` refuses to print a table unless identity, completeness, uniqueness
and replay all verify, and `stale2.self_check()` refuses unless the contract
measure can both pass and fail. **Run under `uv run python`, never bare
`python3`** — bare python3 has no pytest and silently scores every reply
"neither".

## If the first result warrants attribution: matched SFT (~1.5 GPU-h + 1 GPU-h)

`cf` achieved **134** optimizer steps, so the matched SFT arm trains to exactly
that count and the runner is told to refuse anything else:

```bash
# 1. train, step-matched.  Every other value is the trainer's default and is the
#    registered recipe: seed 0, lr 1e-4, rank 16, alpha 32, beta 0.1,
#    dpo_weight 0.1, accum 8, --hours 4.0 as the safety cap.
(
  setsid nohup bash -c 'cd /home/bmarti44/stencil-llm && \
    tools/gpu_reserve.sh a-screen-train-sft 150 70 -- \
      uv run python scripts/a_screen_train.py \
        --objective sft --max-steps 134 \
        --out /home/bmarti44/stencil-llm/results/a-screen/adapters/sft \
        --hub /home/bmarti44/stencil-llm/deploy/stencil_focus/build/hub-4b' \
    >/dev/null 2>&1 & echo $! >> /home/bmarti44/stencil-llm/.stencil-owned-pids
)

# 2. BOTH eligibility and comparability must pass before any evaluation (CPU)
uv run python results/a-screen/analysis/preflight.py compare \
  results/a-screen/adapters/sft results/a-screen/adapters/cf --arms sft cf \
  --hub /home/bmarti44/stencil-llm/deploy/stencil_focus/build/hub-4b

# 3. evaluate with the count pinned, so the runner refuses a mismatched adapter
uv run python scripts/a_screen_run.py --arm sft --require-steps 134 \
  --adapter /home/bmarti44/stencil-llm/results/a-screen/adapters/sft \
  --hub /home/bmarti44/stencil-llm/deploy/stencil_focus/build/hub-4b \
  --out /home/bmarti44/stencil-llm/results/a-screen/runs/sft.jsonl \
  --budget-min 100

# 4. three-arm comparison (CPU)
uv run python results/a-screen/analysis/compare.py \
  results/a-screen/runs/off-oldrunner.jsonl \
  results/a-screen/runs/sft.jsonl \
  results/a-screen/runs/cf.jsonl \
  --runner-exception "RUNNER-EXCEPTION.md, verified by runner_equivalence.py"
```

The 70 GiB for SFT training repeats cf's reservation rather than assuming SFT is
cheaper. It probably is — no reference-scoring phase, one forward pass per
micro-step instead of two — but that is a prediction, and the last time a peak
was predicted rather than measured it was 2.35x low and collided with the peer.
Measure it, then correct the reservation downward and say so.

SFT has no reference-scoring phase and one forward pass per micro-step where cf
has two, so 134 steps will take well under cf's 4-hour allocation. That is
expected and is exactly why the old minimum-elapsed-time guard was replaced.

## If no

Everything above stays on disk. `results/a-screen/RESULTS-BASELINE.md` is a
complete, honest, publishable negative-space result on its own: it documents a
real and specific failure mode of a 4B model in multi-turn coding sessions, with
the confounds stated. Nothing about candidate A is claimed.
