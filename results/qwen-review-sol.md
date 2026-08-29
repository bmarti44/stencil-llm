codex
Verdict: the transcript cache does not invalidate the separate-focus-state experiment, but it changes the claim substantially. More urgently, the current P2 result is not validly measurable with the existing evaluator, and the live transcript run has already missed its registered step-500 gate: held-out 0%, differential 0 at step 500. The owner should stop this variant rather than let step 1500 rescue it.

P0’s actuator result remains credible. P1 establishes train-set capacity, but it was an exploratory success after the registered schedule failed—not a clean registered pass.

## High-severity findings

### 1. The P2 evaluator is teacher-forced and leaks prior answers

**Severity: HIGH**

Training constructs a query sequence containing all gold answers in [qwen_p2_drift.py](/home/bmarti44/stencil-llm/scripts/qwen_p2_drift.py:62). Evaluation then takes argmax logits at those positions in [qwen_p2_drift.py](/home/bmarti44/stencil-llm/scripts/qwen_p2_drift.py:94).

Consequences:

- “Exact” means teacher-forced per-token argmax, not exact autoregressive continuation.
- Later answer tokens see the correct earlier answer tokens.
- The second query can see the entire gold answer to the first query.
- The transcript reader’s step query can exploit gold prefixes to infer which transcript position comes next.

That is acceptable as a training diagnostic, but it cannot support the final “adherence” claim.

Required fix before another confirmatory run:

- Evaluate each query from an answer-free prompt.
- Greedily generate the complete answer.
- Compare the generated continuation to the current and stale complete values.
- Retain teacher-forced CE/token accuracy under an explicitly diagnostic name.
- Optionally add a paired log-likelihood margin between the current and stale complete continuations.

### 2. The stale-rate metric is structurally confounded

**Severity: HIGH**

Stale rate compares only the predicted first token with the stale answer’s first token in [qwen_p2_drift.py](/home/bmarti44/stencil-llm/scripts/qwen_p2_drift.py:105). Values begin with one of only eight adjectives in [qwen_task.py](/home/bmarti44/stencil-llm/src/stencil/qwen_task.py:22), so independently drawn current and stale values have roughly a 12.5% first-component collision floor before any tokenizer collisions.

A correct current answer can therefore be counted as stale whenever current and old values share their first token. The observed 21.9–25% stale rates cannot be cleanly interpreted.

Replace it with:

```python
stale_exact = (
    generated_tokens == stale_complete_tokens
    and stale_complete_tokens != current_complete_tokens
)
```

Also report current-vs-stale sequence log-probability margin. The registered `<10% stale` gate should apply only to corrected full-sequence free-running stale exact.

### 3. The current run has failed the registered early gate

**Severity: HIGH**

As read, [qwen-p2-drift.log](/home/bmarti44/stencil-llm/results/logs/qwen-p2-drift.log:1) reports at step 500:

- held-out: 0%
- zero-code: 0%
- differential: 0
- stale: 25%

That decisively misses held-out ≥50% and differential ≥15 points. Under the quick-turnaround discipline, continuing the same configuration to 1500 would be an unregistered rescue. Stop it and record the miss.

The final ≥70%/≥20-point thresholds remain reasonable, but only after repairing free-running evaluation and stale scoring.

### 4. This is no longer a compact semantic focus representation

**Severity: HIGH for an efficiency/compactness claim; MEDIUM for the underlying mechanism**

Each occupied slot now contains:

- 256 key floats
- 1,024 pooled-summary floats
- 12 × 128 transcript floats

All are stored as float32 through [qwen_cache.py](/home/bmarti44/stencil-llm/src/stencil/qwen_cache.py:80). That is 2,816 floats, approximately 11 KiB per occupied slot or 176 KiB across 16 slots, excluding overhead. The plan’s approximately 34 KiB BF16 cache description no longer applies.

The transcript also receives exact value-token boundaries from the structured event construction in [qwen_p2_drift.py](/home/bmarti44/stencil-llm/scripts/qwen_p2_drift.py:48), and silently truncates values beyond 12 tokens in [qwen_cache.py](/home/bmarti44/stencil-llm/src/stencil/qwen_cache.py:83).

This is best described as a **structured, token-aligned latent transcript memory**, not a compressed semantic summary. That is still scientifically legitimate: it tests whether a separately persisted neural memory can condition a frozen model after source deletion and updates. But it does not yet establish semantic compression or efficiency against a raw ledger.

The eventual writeup should say approximately:

> Given structured writes exposing exact value-token boundaries, the system stores up to 12 learned token projections plus a pooled summary per slot. This demonstrates a separate neural token-memory channel, not semantic compression. Efficiency remains to be tested against raw-text, prefix/KV, retrieval, and reinsertion baselines at matched state bytes, latency, and token cost.

The current task uses fixed fields and small compositional value vocabularies in [qwen_task.py](/home/bmarti44/stencil-llm/src/stencil/qwen_task.py:18); “open content” currently means held-out combinations, not arbitrary natural-language focus specifications.

### 5. P0 is recorded as passing pretests that are not implemented

**Severity: HIGH for process claims**

[QWEN-PLAN.md](/home/bmarti44/stencil-llm/QWEN-PLAN.md:31) requires non-vacuity, arbitrary chunk-boundary behavior, zero-code differential controls, adversarial no-write behavior, ridge metrics, and frozen-trunk checks. [test_qwen3.py](/home/bmarti44/stencil-llm/tests/test_qwen3.py:28) currently covers conversion parity and deterministic forward behavior, but not the cache-specific tests.

In particular, `QwenCacheState` has no pending-span accumulator in [qwen_cache.py](/home/bmarti44/stencil-llm/src/stencil/qwen_cache.py:29). Either:

- implement the registered cache tests and pending-span behavior, or
- formally amend the plan to say `focus.set` events are delivered atomically after message-boundary parsing and make no mid-value chunk-equivalence claim.

P0 parity, timing, upper-bound, and oracle evidence remain useful. “All P0 pretests passed” is not currently supported.

## Transcript-reader design

The implementation is connected, but brittle:

- Four subkeys are reduced to a slot mixture before transcript selection in [qwen_cache.py](/home/bmarti44/stencil-llm/src/stencil/qwen_cache.py:98). Several slots can therefore be blended.
- `step_q` independently predicts one of 12 fixed positions in [qwen_cache.py](/home/bmarti44/stencil-llm/src/stencil/qwen_cache.py:101). This encourages learning an output-position schedule rather than content-sensitive reading.
- Teacher forcing makes that schedule substantially easier.
- Zero-padded transcript positions have no length mask.
- Values longer than 12 tokens are silently truncated.
- The summary and transcript paths coexist without summary-only/transcript-only ablations, so successful behavior would not yet identify which representation caused it.
- There are no reported slot-attention accuracy, transcript-position accuracy, entropy, shuffled-slot, or shuffled-transcript controls.

I would simplify to content-addressed cross-attention over variable-length latent memory tokens:

1. Structured slot ID chooses the write slot.
2. Store projected value tokens plus an explicit validity mask.
3. Let generation hidden states cross-attend to all valid memory tokens at the top blocks.
4. Charge the complete memory size and attention cost in baseline comparisons.

Directly injecting transcript token `j` at generation offset `j` would probably be easier, but it is a copy-channel ceiling, not a convincing open-ended conditioning mechanism. Use it as a labeled diagnostic. It becomes oracle-like if correct output offsets or lengths are supplied.

Required ablations for either reader:

- summary only
- transcript only
- zero code
- shuffled slots
- shuffled transcript positions
- wrong-key transplant
- free-running rather than teacher-forced generation

## Registration and record repair

You cannot retroactively preregister the variants. The defensible action is to label everything seen so far as development and preserve the complete adaptive history.

Record a table containing:

- commit/config for each writer and reader
- schedule, accumulation, optimizer, state dimensions, and injection layers
- which evaluation seeds were inspected before each change
- registered gate and observed result
- reason for the subsequent modification
- artifact/log path

Do not keep overwriting the same P2 progress, checkpoint, and log paths as done in [qwen_p2_drift.py](/home/bmarti44/stencil-llm/scripts/qwen_p2_drift.py:133). Future variants need immutable tags.

Also amend the plan for:

- the 1500-step schedule versus the original 192-step P2 specification
- omission of LoRA despite the stated Qwen configuration
- the float32 transcript state and actual byte count
- corrected autoregressive evaluation
- old “held-out” seeds becoming development data
- a new untouched final evaluation seed range

P0 is not weakened by the writer iterations because its parity, actuator, and visible-task feasibility questions are separate. The one task-format change means the upper bound is a development feasibility result, not sealed benchmark performance.

P1 should be reported as:

> The registered 64-step microfit gate failed. After adaptive reader, schedule, accumulation, and optimization changes, an exploratory configuration reached 100% training exact with a 100-point zero-code differential.

That still proves train-set capacity. It does not prove registered turnaround or generalization.

## A defensible stop rule

The pooled summary and transcript designs should not be retroactively counted as the two “registered state widths/injection sites” in [QWEN-PLAN.md](/home/bmarti44/stencil-llm/QWEN-PLAN.md:112): they were adaptively selected on the same development evaluation and use essentially the same injection site.

I recommend:

1. Stop and record the current step-500 miss.
2. Repair the evaluator, stale metric, transcript mask, reproducibility, and required controls.
3. Freeze one architecture and designate all old held-out seeds as development data.
4. Register one confirmatory transcript configuration and one width fallback—nothing else.
5. Require the same early step-500 held-out/differential gate on fresh validation data.
6. Run the final gate on untouched seeds only if the early gate passes.
7. If both registered configurations miss, invoke stop condition 3 and stop the Qwen cache effort.

Do not respond to another plateau with simultaneous changes to schedule, writer, reader, width, and optimizer.

One additional reproducibility defect: the new `val_tok`, `tok_code`, and `step_q` layers are absent from the locally seeded initialization list in [qwen_cache.py](/home/bmarti44/stencil-llm/src/stencil/qwen_cache.py:48), leaving them on global PyTorch RNG initialization. Fix or explicitly seed the process before model construction.

Bottom line: the transcript direction is scientifically permissible, but its honest claim is “structured neural token memory,” not compact semantic focus. The present P2 run has failed its early gate, and the current evaluation cannot support adherence or stale-rate claims even if training later rises. Fix measurement first; allow at most two clean, preregistered attempts after that.
