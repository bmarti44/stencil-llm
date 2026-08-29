codex
# Verdict

Do not sign off [gpt2-report.md](/home/bmarti44/stencil-llm/results/gpt2-report.md:1) as written.

The central result is real: a separately persisted cache causally carries four changing templated rules through a provably unreachable gap in frozen GPT-2. Zeroing or transplanting the cache changes behavior exactly as the mechanism predicts.

But the report has four high-severity problems. Most importantly, it has not shown that the cache is useful for agents or superior to an ordinary external task ledger. The honest status remains:

> Mechanism proven on a synthetic GPT-2 construction; usefulness for long-horizon agents pending.

No critical findings. Review confidence: 97%.

# Part 1 — Report audit

## High findings

### H1 — Experiment A does not test a real pin/reinsertion baseline

The report calls 22.1% a pinning “ceiling at any budget” and says nothing can rescue the “unpinnable” 40% ([report:31](/home/bmarti44/stencil-llm/results/gpt2-report.md:31)).

That is false outside the script’s artificial policy. The baseline is forbidden to preserve a statement once it has left the model’s receptive field:

- It may pin only statements with `lo >= C - 756`.
- Earlier instructions are discarded even though an agent runtime could have stored them when they arrived.
- It uses a separately trained `base-v3` model that was not trained on the repacked/pinned layout.

See [exp_a_baseline_fight.py:4](/home/bmarti44/stencil-llm/scripts/exp_a_baseline_fight.py:4), [line 69](/home/bmarti44/stencil-llm/scripts/exp_a_baseline_fight.py:69), and [line 78](/home/bmarti44/stencil-llm/scripts/exp_a_baseline_fight.py:78).

An external current-task ledger can retain every update as it arrives and reinsert the latest value after compaction—the same temporal privilege given to the cache. Therefore:

- 80.2% and 22.1% are results under the registered restricted policy.
- “Ceiling at any budget,” “structurally unpinnable,” and “nothing rescues” are not supported.
- Experiment A does not establish usefulness.

Required correction:

> Under a restricted baseline allowed to reinsert only statements still visible at compaction, the cache scored 80.2% versus 22.1%. This is not a deployment-grade pin/reinsertion comparison: an external instruction ledger could preserve earlier updates, and the baseline was not trained on repacked layouts.

### H2 — The “10k adversarial tokens” test was never run

The headline table claims bitwise-zero writes on “10k adversarial tokens” ([report:25](/home/bmarti44/stencil-llm/results/gpt2-report.md:25)).

The registered test actually generates 128 uniformly random token IDs and forwards them once: [test_gpt2.py:255](/home/bmarti44/stencil-llm/tests/test_gpt2.py:255). They are not constructed from quoted slot words, despite the test’s docstring.

The learned-gate adversarial diagnostic is separate: approximately 512 tokens made by repeating one sentence, and it produced one occupied slot at the mature checkpoint ([run_gpt2_arms.py:405](/home/bmarti44/stencil-llm/scripts/run_gpt2_arms.py:405), [log](/home/bmarti44/stencil-llm/results/logs/gpt2-cachev8-s0.log:10)). Its counter measures final occupancy, not total false commit events, so repeated false writes can be undercounted.

Either run the actual registered 10,000-token test and count commits, or replace the row with:

> At initialization, closed gates produced zero writes on 128 random token IDs.

### H3 — Chunk equivalence is much narrower than the report implies

The test compares only final cache keys and values after splitting a synthetic hidden-state tensor at a safe boundary—after one complete write and before the next instruction begins: [test_gpt2.py:291](/home/bmarti44/stencil-llm/tests/test_gpt2.py:291).

It does not test:

- A boundary inside an instruction.
- Token-by-token streaming.
- Full-model logits.
- KV-cache or positional continuity.
- Actual context compaction.

This matters because `CacheState` contains only completed slots ([focus_cache.py:27](/home/bmarti44/stencil-llm/src/stencil/focus_cache.py:27)). Span accumulation is local to each call and restarts with `prev = -1` ([focus_cache.py:120](/home/bmarti44/stencil-llm/src/stencil/focus_cache.py:120)). If a chunk boundary bisects an instruction, earlier salient tokens are lost from the eventual value.

Required correction:

> Cache slot state is bitwise equal across a safe boundary between complete events. Arbitrary-boundary streaming and full-model compaction equivalence are not established; the current state lacks a persisted pending-span accumulator.

This is a deployment blocker, not a failure of the synthetic causal result.

### H4 — Experiment C does not isolate inference by frozen knowledge

The 100% versus 5.1% result proves that the trained pathway can turn a fixed clue phrase into a class-specific cache value and use it later. It does not prove that “the frozen trunk infers” the answer ([report:43](/home/bmarti44/stencil-llm/results/gpt2-report.md:43)).

The clue for each answer is fixed in `DERIVED_CLUES` ([nl_task.py:78](/home/bmarti44/stencil-llm/src/stencil/nl_task.py:78)). Full-matrix LoRA, writer, reader, injection projections, and the output adapter all receive answer supervision. They can learn those sixteen phrase-to-answer associations even if pretrained knowledge contributes nothing.

The forced-write paraphrase score, 5/8, is useful evidence of limited semantic transfer. But:

- It is only eight cases.
- The test code/output is not committed; only a prose WORKLOG entry exists.
- It does not isolate the frozen trunk from learned LoRA.

Required wording:

> The trained frozen-trunk-plus-adapter pathway derived and stored answer values from fixed clue phrases. A 5/8 forced-write paraphrase probe suggests limited semantic transfer, but the experiment does not isolate how much came from pretrained trunk knowledge versus the trained adapters.

## Medium findings

### M1 — “Weak-label acquisition is viable” is too broad

The run establishes robustness to synthetic independent teacher corruption on the same templates:

- 30% of ground-truth spans are dropped.
- About 10% of sequences receive one synthetic spurious event.
- Evaluation returns to the clean, familiar grammar.

That is not weak acquisition from real language. The threshold result—0.97 precision at 0.87 recall—is stated only in [WORKLOG.md:269](/home/bmarti44/stencil-llm/WORKLOG.md:269); no sweep script, calibration split, or output artifact is committed.

Use:

> The fixed-template detector tolerated registered synthetic label corruption. Generalization to weak labels on natural text remains untested.

### M2 — Single-seed optimization is omitted

The main cache, noisy-label, and derived results are all seed 0. The final sample has 253 beyond-window queries, but only one trained initialization.

This does not undo the causal demonstration, but the report should say “one training seed.” A second seed was explicitly identified as unfinished in [WORKLOG.md:231](/home/bmarti44/stencil-llm/WORKLOG.md:231).

### M3 — “Sealed offset” conceals a recorded protocol deviation

The 253-query check used `FINAL_SPACE`, but outside the original fleet-freeze/single-shot marker procedure. This is honestly recorded in [WORKLOG.md:234](/home/bmarti44/stencil-llm/WORKLOG.md:234), but “sealed offset” implies full compliance.

Use:

> Final-space offset, evaluated after the checkpoint was frozen, outside the superseded single-shot marker ritual.

### M4 — A registered intermediate gate was missed and omitted

The registered per-slot READ-ridge criterion was `>50% by step 500`. Actual scores were 0%, 16.7%, 33.3%, and 41.7%; training continued and recovered by step 1500. That is not fatal, but omitting it makes the stopping discipline look cleaner than it was.

### M5 — The reproducibility footer is too strong

“All numbers reproduce” is inaccurate ([report:94](/home/bmarti44/stencil-llm/results/gpt2-report.md:94)):

- The threshold sweep has no committed script/output.
- The 5/8 and 0/8 paraphrase probe has no committed script/output.
- Experiment A has a deterministic script, but no saved result artifact.
- The 10k claim does not correspond to its test.

Use “main training and causal-control results,” not “all numbers.”

## Low finding

The actuator evidence should be written as “8/8 unconstrained oracle; 4/4 under unit-RMS projection.” The report’s “8/8, including unit-RMS” compresses two different checks. See [oracle_inject_diag.py:28](/home/bmarti44/stencil-llm/scripts/oracle_inject_diag.py:28) and [oracle_norm_check.py:28](/home/bmarti44/stencil-llm/scripts/review/oracle_norm_check.py:28).

## What is solid and should remain prominent

These claims check out:

- Receptive field: \(12 \times 63 = 756 < 1024\), with exact-zero reachability verification.
- Exact cache configuration.
- 1,963,347 trainable parameters, reasonably described as ~1.9M.
- Maximum eight-slot fp32 state: 5,120 bytes, reasonably described as ~5KB.
- 253/253 beyond-window versus 11/253 zero-code, a +95.7-point causal differential.
- Transplant 28/32 versus shuffled-values 1/32.
- Four simultaneous slots and updates work on held-out sequences from the same grammar.
- Oscillator probe numbers and the narrow scope of that negative.
- The closed 16-answer wall, supervised acquisition, detection brittleness, and lack of module novelty are stated unusually clearly.

The sentence at the top—“Usefulness beyond this construction remains to be earned”—is admirably direct. It is not buried. Experiment A currently contradicts it by implying that the cache already beat ordinary retention; fixing H1 restores the report’s honesty.

# Part 2 — Qwen3-1.7B plan

## Owner-level decision

Proceed, but make Qwen answer one question before autonomous salience:

> Can a compact latent focus state condition open-ended generation through updates and compaction better—or more cheaply—than a canonical external task ledger?

If the answer is no, stop. A better detector cannot make an unnecessary memory useful.

Use the structured API first. Autonomous salience comes later because it otherwise entangles three risks:

1. What should be stored?
2. Can the cache retain open content?
3. Can Qwen use that content correctly?

The API isolates risks 2 and 3 and is already a legitimate deployment architecture. Learned detection is only valuable after the memory channel earns its keep.

## Pinned model and interface

Pin `Qwen/Qwen3-1.7B` to an exact revision. It has 1.7B parameters, 28 layers, hidden size 2,048, 16 query heads, 8 KV heads, and a 32,768-token advertised context. Qwen requires `transformers>=4.51.0`; use BF16 and no YaRN for this rung. [Official model card](https://huggingface.co/Qwen/Qwen3-1.7B), [configuration](https://huggingface.co/Qwen/Qwen3-1.7B/blob/b9352fbb8ce704292730cf54b3b1dceb2a808738/config.json), [Transformers guidance](https://github.com/QwenLM/Qwen3/blob/main/docs/source/inference/transformers.md).

Use non-thinking mode for deterministic short-output evaluations. Pin the chat template, generation prompt, model revision, tokenizer revision, decoding settings, and maximum output length.

### Fast training configuration

- Frozen Qwen blocks 0–19, run without autograd.
- Detach the residual entering block 20.
- Rank-8 LoRA only in blocks 20–27 on `q/k/v/o` and `gate/up/down` projections: approximately 2.49M LoRA parameters.
- Train cache writer/read/injection plus that upper-stack LoRA.
- Inject after the attention residual in blocks 24–27.
- BF16 trunk and activations; fp32 optimizer state.
- Microbatch 1, no gradient accumulation.
- Context 1,024 for microfit; 2,048 for training; 4K–16K only for inference baselines.
- AdamW: LoRA `2e-4`; cache/injection `1e-3`; 5% warmup; clip 1.0; no decay on bias/norm/gates.
- Evaluation every 32–64 steps.
- Hard process kill at two hours.

Running only the upper eight blocks under autograd is what makes the turnaround plausible. Full 28-layer LoRA backpropagation is unnecessary until this configuration fails an oracle-qualified test.

Do not promise a runtime from model size. Qwen’s published numbers are inference measurements on different hardware, not GB10 training measurements ([official benchmark](https://github.com/QwenLM/Qwen3/blob/main/docs/source/getting_started/speed_benchmark.md)). First measure 20 warm steps at 1,024 and 2,048 tokens. Admit a planned run only when:

\[
N_{\text{steps}}\times p90(\text{step time}) + T_{\text{eval}} < 7{,}200\text{s}.
\]

Target 95 minutes training plus 20 minutes evaluation. If 192 steps do not fit, reduce to 128 or 1,536-token chunks—do not silently run overnight.

## Focus-state design

Use an explicit runtime API:

```text
focus.set(key, value, source_id, priority, version)
focus.clear(key, source_id)
```

State:

- 16 slots.
- Exact structured key used for overwrite/clear.
- Learned 64-dimensional read key.
- Four 256-dimensional BF16 value vectors per slot.
- Validity, version, source role, priority, age.
- Explicit overflow error or registered eviction policy—never silently replace slot zero.
- Approximately 34 KiB latent state plus metadata.
- Human-readable canonical value and provenance retained outside the model.

The raw ledger is intentional. It makes corruption auditable and lets the latent representation be regenerated. It also means the cache must justify itself through better conditioning efficiency, not claim to be the only surviving copy.

Writer/read path:

```text
frozen blocks 0–19
    → contextual focus-message states
    → four-query pooling → four value vectors
    → exact API-keyed store

current generation state at block 20
    → four-head query-conditioned read over active values
    → 512–1024-dimensional code
    → zero-init residual projections in blocks 24–27
```

Updates overwrite exactly; clears invalidate exactly. Structured API writes occur at message boundaries, so Phase 1 needs no learned commit gate. The explicit model call should return `next_focus_state`, never mutate hidden model attributes.

## The evaluation that matches the owner’s scenario

Each held-out session should contain:

- 40–80 user/assistant/tool turns.
- 12K–40K cumulative stream tokens.
- Two to five forced compactions.
- Six initial task-state entries.
- Six to twelve user updates, including overwrite, cancellation, priority change, and conflicting stale text.
- Three to six discoveries from tool results that require changing the plan or current subtask.
- Distractor documents, code, quoted instructions, and prompt-injection attempts.
- Open values: unseen paths, identifiers, commands, schemas, numeric constraints, prose requirements, and multi-token decisions.

State categories should include goal, deliverable, constraints, current subtask, accepted decisions, discoveries, and completion criteria.

A discovery-driven example must have this causal shape:

```text
initial plan
→ tool result disproves an assumption
→ agent proposes focus.set("strategy", revised_strategy, source=result_id)
→ compaction deletes the tool result and old discussion
→ later tool/action follows revised strategy
```

Score:

- End-task success.
- Per-obligation adherence.
- Active-versus-stale instruction errors.
- Update adoption latency.
- Derived-update precision and recall.
- Unauthorized accepted writes.
- Rework and wasted tool calls.
- Cumulative prompt tokens.
- Latent/raw state bytes.
- Cache-update and p50/p95 turn latency.

Use at least 64 sessions and 256 independently scored obligations for a final gate.

## Baseline gauntlet

Give every baseline the same canonical update ledger. Do not repeat Experiment A’s visibility restriction.

1. **Pinned current state:** prepend the complete latest ledger every turn.
2. **Reinsert at compaction:** insert the complete latest ledger immediately after each compaction.
3. **Compaction summary:** same Qwen generates a bounded 64/128/256-token current-state summary; include summarization cost.
4. **Retrieval:** retain every update externally and retrieve latest-per-key or top-k relevant entries. Include an oracle-key retrieval upper bound.
5. **Long context:** no compaction at 8K and 16K where feasible.

Train a matched upper-eight-layer rank-8 LoRA text arm on visible current-state layouts. Otherwise the cache arm receives specialized training while the baseline is asked to generalize zero-shot.

Report Pareto curves rather than one cherry-picked budget. The cache earns usefulness only if, against the best baseline, it achieves either:

- No more than two points lower task success while reducing cumulative input tokens by at least 25%, with p95 latency within 10%; or
- At least a five-point task-success gain at matched cumulative tokens and latency.

Count cache bytes and update compute. “Zero carried tokens” is not zero cost.

## Phased execution

| Phase | Wall time | Work and hard gate | Riskiest assumption retired |
|---|---:|---|---|
| 0. Harness and admission | <½ day | Pin environment; visible-task upper bound ≥80%; inert bypass bitwise; frozen hashes; arbitrary-boundary state tests; 20-step timing; unit-RMS oracle residual improves 7/8 examples. | Qwen can perform the task and the chosen actuator can affect generation. |
| 1. Open-content API microfit | <½ day | Run 1 then Run 2 below. Require held-out multi-token generation and a large zero-code differential. | A latent value can condition generation rather than select one of 16 classes. |
| 2. Structured drift plus gauntlet | <1 day | Run matched text arm; evaluate all baseline policies and cost curves. Require a Pareto win. | The cache is useful rather than an elaborate substitute for retained text. |
| 3. Agent-issued API writes | <1 day | Teacher-force focus calls during training; learned calls at evaluation. Trusted user updates plus evidence-linked agent-derived updates. | Qwen can dynamically update focus from discoveries. |
| 4. Autonomous detection | <1 day | Train span/commit detector; threshold on calibration split; final on held-out surface families and sources. | Detection generalizes beyond templates without unsafe writes. |
| 5. Long-session replication | <1 day per seed | Two fresh training seeds; 40–80-turn sessions, multiple compactions, transplant/zero controls, hand-authored final episodes. | Gains survive optimization seed and realistic task composition. |

Only after Phase 5 passes should the project move to 7B coding tasks.

## First three concrete runs

### Run 1 — `q3-api-micro-r8-s0`

- Context 1,024.
- Batch 1.
- 64 optimizer steps.
- Fixed 32-session microset with open multi-token values.
- Structured writes, four slots initially.
- Maximum 30 minutes.

Gates:

- By step 8: nonzero gradients in every LoRA/cache/injection group.
- By step 16: response loss down at least 30%.
- By step 64: ≥95% training exact match and ≥50-point learned-minus-zero differential.
- If it cannot overfit, stop and audit the interface; do not launch a longer run.

### Run 2 — `q3-api-drift-r8-s0`

- Context 2,048, streamed across chunks.
- Batch 1.
- 192 steps, reduced only by the timing admission rule.
- 16 slots, four value vectors per slot.
- Four to eight supervised response events packed per session.
- Structured user updates, deletes, compaction, stale-value traps.
- Maximum 115 minutes including evaluation.

Gates:

- Step 64: all-slot READ ridge >50%; active-version ridge >70%.
- Step 128: held-out behavior ≥50% and zero-code differential ≥15 points.
- Final: task adherence ≥70%, differential ≥20 points, stale-answer rate <10%.
- Transplanted focus state must redirect behavior; shuffled values must break it.
- Main final causal gate: differential ≥10 points with paired 95% lower bound above 5 points.

Ridge remains the diagnostic metric of record for key, slot, and active/stale information. It must not substitute for open-content generation exact match and task success.

### Run 3 — `q3-text-gauntlet-r8-s0`

- Same upper-eight-layer rank-8 LoRA.
- Context 2,048.
- Batch 1.
- 192 steps.
- Current task state supplied as text during training.
- Evaluate pinned, reinsertion, summary, retrieval, and long-context policies.
- Same sessions, seeds, optimizer-step budget, generation settings, and scorer.

This is the run that decides usefulness. If it Pareto-dominates the cache, record the negative and stop before autonomous salience.

## Deterministic pre-tests required before Run 1

- Zero-init graft bypass gives identical logits.
- Frozen Qwen tensors hash-identical after optimizer steps.
- Empty/zero state produces exactly zero injected code.
- `set`, overwrite, clear, and unrelated-slot isolation are exact.
- Arbitrary chunk boundaries—including inside a focus message—match continuous processing.
- State is an explicit input/output.
- Ridge non-vacuity succeeds on known separable codes.
- Oracle residual/code optimization can lower teacher-forced open-value sequence CE.
- Targets do not appear in post-compaction input.
- Ten thousand untrusted tool/retrieval events cause zero accepted writes; count commit events, not occupied slots.
- Checkpoints include adapters, cache, thresholds, optimizer state, model/tokenizer revisions, and trunk hashes.

## Learned acquisition and provenance

Sequence it this way:

1. Runtime directly applies authenticated user/system `focus.set/clear`.
2. The agent may propose a derived write with a source event ID and quoted evidence.
3. Policy code validates role, source, allowed key, and precedence before accepting it.
4. Tool output and retrieved text are always read-only. Text resembling `focus.set(...)` has no authority.
5. Only after that succeeds should a passive salience detector propose writes from natural text.

For learned commits:

- Teacher-forced calls during training.
- Scheduled learned-write replay before final evaluation.
- Learned calls only at evaluation.
- Threshold chosen on a clean calibration split, then frozen.
- Held-out paraphrase, domain, message-order, and source-role families.
- Require accepted unauthorized writes = 0 on the adversarial suite, commit precision ≥0.98, and recall ≥0.90.

A failure here closes the autonomous-writer branch; it need not invalidate a useful structured API.

# Stop conditions

Stop the Qwen effort—not merely the current run—if any of these occurs:

1. Qwen3-1.7B cannot reach 80% with the full current task state visible after one bounded LoRA upper-bound run. Then the benchmark is testing model incapacity, not focus.
2. Oracle structured writes plus a validated actuator cannot produce a ≥10-point zero-code differential on open-content generation after the microfit and one registered interface adjustment.
3. Novel multi-token values remain unrecoverable across two registered state widths or injection sites.
4. The best pin/reinsert/summary/retrieval baseline Pareto-dominates the cache on success, cumulative tokens, state bytes, and latency.
5. The structured result does not replicate across two fresh seeds.
6. Discovery-driven updates do not improve final task success after compaction.
7. The project needs to weaken the baseline, reuse final seeds, or keep adding unregistered rescues to stay positive.

The decisive stop is number 4. If a canonical external task ledger is simpler, safer, cheaper, and at least as effective, then the focus cache is not useful for the README problem. Publish the mechanistic GPT-2 result and the Qwen negative; do not escalate it to 7B.

Plan confidence: 80%. The main uncertainty is not memory capacity. It is whether latent conditioning can beat simply feeding Qwen a compact, human-readable current-task ledger.
