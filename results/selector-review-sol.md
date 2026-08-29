codex
## Verdict

The split is cleaner and more faithful to the goal than the fused cache. Keep S0, S1, and a sharply simplified S2. Defer S3 completely.

Do not start S2 yet. Two plan-level issues must be fixed first:

1. A soft attention distribution is not mechanically “contentless”; continuous scores can encode information. Use a hard span index and fixed bias magnitude at evaluation.
2. S1/S2 lack enough specification to be deterministic: bias magnitude, query rows, layer selection, selector loss, and gap formulas are undefined.

No critical findings. Several highs are inexpensive to fix before S1/S2.

## Findings

### HIGH — The proposed softmax wire is not strictly address-only

[SELECTOR-PLAN.md:34](/home/bmarti44/stencil-llm/SELECTOR-PLAN.md:34) specifies a softmax over spans feeding the bias. Eight continuous scores can encode more than an address; their magnitudes can vary with value content. That weakens “carries an address, never a value” at [SELECTOR-PLAN.md:5](/home/bmarti44/stencil-llm/SELECTOR-PLAN.md:5).

Make the deployed/evaluated wire categorical:

```python
selector_logits = score(query_h20, span_h20)       # [B, N]
address_loss = F.cross_entropy(selector_logits, target_span)

selected = selector_logits.argmax(dim=-1).detach() # [B]
selected_mask = F.one_hot(selected, N).float()
attention_bias = FIXED_BETA * span_token_mask(selected_mask)
```

Train with direct address CE. Do not depend on answer-loss gradients through a soft spotlight. The selector may inspect content to choose an address, but the carrier exposed to Qwen is one discrete index plus a fixed-strength mask.

This is also much faster: cache frozen h20 query/span features and train the tiny scorer in seconds.

### HIGH — S1/S2 are not specified tightly enough to be registered runs

The plan does not define:

- bias magnitude
- which attention query rows receive it
- whether all heads receive identical bias
- how a character span becomes a token mask
- selector supervision
- whether selection is recomputed during generation
- “net gain” mathematically
- “closes the base→oracle gap” mathematically

See [SELECTOR-PLAN.md:30](/home/bmarti44/stencil-llm/SELECTOR-PLAN.md:30) and [SELECTOR-PLAN.md:34](/home/bmarti44/stencil-llm/SELECTOR-PLAN.md:34).

Register these before S1:

- Select an address once at the answer boundary and hold it for the whole continuation.
- Add the same fixed bias to all heads.
- Bias only the current prediction row during autoregressive generation.
- Bias every token overlapping the selected ledger-line character span.
- Keep causal `-inf` entries unchanged.
- Train the selector with direct span-address CE.
- Freeze Qwen completely.

Define paired metrics:

```text
gained = base-wrong and spotlight-correct
broken = base-correct and spotlight-wrong
rescue_rate = gained / base_wrong
break_rate = broken / base_correct
net_gain = gained - broken
net_closure = (gained - broken) / base_wrong
```

The current wording means S1 should require `rescue_rate >= 0.50` and `broken == 0`. Do not silently replace “without breaking correct cases” with positive aggregate net gain.

For S2:

```text
oracle_net  = oracle_gained  - oracle_broken
learned_net = learned_gained - learned_broken
gap_closure = learned_net / oracle_net
```

### HIGH — The present task cannot establish usefulness

The query names a fixed field, all ledger entries are structured, and the expected response is copied exactly from the ledger. A dictionary lookup can solve it without Qwen. See [qwen_task.py:147](/home/bmarti44/stencil-llm/src/stencil/qwen_task.py:147) and [qwen_task.py:177](/home/bmarti44/stencil-llm/src/stencil/qwen_task.py:177).

That does not invalidate S0–S2 as a mechanistic routing test. It does mean the strongest honest success claim is:

> On synthetic prompts with conflicting visible records, a supervised discrete span selector caused frozen Qwen to attend to the designated authority and reduced exact distractor copying.

It would not establish long-horizon focus, memory, autonomous authority detection, dynamic task changes, or agent usefulness.

Mandatory baselines before S2 is declared complete:

1. **Prompt-only:** repeat “use only the Current settings ledger” immediately before the query.
2. **Oracle reinsertion:** copy the governing ledger line next to the query.
3. **External lookup/reranker:** select the field from the ledger and return its value.
4. **No-wire trained reader:** parameter-conscious LoRA or top-layer adaptation trained on the same sessions.

The first three cost almost nothing. The trained-reader run can wait until the selector itself passes. If prompt repetition matches the selector at negligible token cost, do not proceed to S3 claiming utility.

A reranking head is a useful baseline, but not a substitute for the selector: if it copies candidate value text into the answer, it is itself a content path.

### HIGH — Required selector verification does not exist yet

There is no selector test file or attention-bias interface. Qwen currently supports residual injection only at [qwen3.py:90](/home/bmarti44/stencil-llm/src/stencil/qwen3.py:90) and [qwen3.py:110](/home/bmarti44/stencil-llm/src/stencil/qwen3.py:110).

The spotlight must be a separate path. Add it after the causal mask and before softmax around [qwen3.py:104](/home/bmarti44/stencil-llm/src/stencil/qwen3.py:104):

```python
att = (q.float() @ k.float().transpose(-2, -1)) / sqrt_d
att = att + causal_mask
if attn_bias is not None:
    att = att + attn_bias.float()
out = F.softmax(att, dim=-1) @ v.float()
```

Do not reuse `inj`; that would inject content into the residual stream.

Pre-S2 deterministic tests must include:

- `None` spotlight equals base bitwise.
- A non-`None`, exactly zero spotlight also equals base bitwise.
- The zero path is proven exercised with a hook/counter.
- Nonzero spotlight changes exactly the designated attention logits—no q/k/v, residual, MLP, or other layers.
- Future-token logits remain `-inf`.
- Only the configured query rows, source columns, heads, and layers change.
- Correct, cyclic-wrong, and shuffled addresses produce distinct logits.
- Correct-address accuracy materially exceeds wrong-address accuracy.
- Character-to-token span conversion selects precisely one ledger line and no chatter/query tokens.
- Selector probabilities/addresses reference only registered candidate spans.
- Selector parameters have finite nonzero gradients and change after a step.
- Qwen parameters are absent from the optimizer and bitwise unchanged afterward.
- Same seed/config produces identical address scores, parameter tensors, and per-example evaluation output.

For triage, record address accuracy/margin and target-span attention mass per layer alongside output accuracy. Then:

- bad address accuracy → selector problem
- correct address but unchanged attention mass → wiring problem
- moved attention but failed oracle output → actuator/trunk problem
- oracle succeeds but learned address fails → selector generalization problem

### MEDIUM — S0 is a development result, not a clean admission confirmation

The task was retuned after observing 97%, then measured on the same hard-coded 11M seed range at [selector_s0.py:25](/home/bmarti44/stencil-llm/scripts/selector_s0.py:25). The 50% result is credible evidence, especially with 29 of 32 errors matching distractors, but those examples are now development data.

Confirm the final task once on a fresh fixed seed block before S1. Do not retune again.

The script only prints aggregate output at [selector_s0.py:41](/home/bmarti44/stencil-llm/scripts/selector_s0.py:41). It should produce immutable per-example JSON containing seed, target, generation, classification, config, commit, and model/tokenizer hashes. The pre-retune 97% result is recorded in [WORKLOG.md:401](/home/bmarti44/stencil-llm/WORKLOG.md:401) but is not independently reproducible from a committed generator version; disclose that rather than reconstructing it.

Also, [selector_s0.py:7](/home/bmarti44/stencil-llm/scripts/selector_s0.py:7) imports Torch without importing the repository’s determinism setup before it. That violates [determinism.py:4](/home/bmarti44/stencil-llm/src/stencil/determinism.py:4).

### MEDIUM — These are conflicting distractors, not genuine stale values

The three “stale” values are freshly sampled at [qwen_task.py:151](/home/bmarti44/stencil-llm/src/stencil/qwen_task.py:151). They were never previously authoritative. They appear three times after the one current value at [qwen_task.py:168](/home/bmarti44/stencil-llm/src/stencil/qwen_task.py:168).

S0 therefore measures recency/frequency interference against an explicit authority instruction. That is an excellent minimal actuator-admission task, but it is not yet task-update forgetting. Call the errors “conflicting-note echoes” or “stale-like distractor echoes.”

Other limitations:

- exactly eight fixed field names
- fixed ledger and query templates
- always the same source is authoritative
- three target-field distractors versus one current record
- exact retrieval rather than application of an instruction
- no real horizon, compaction, update, or discovery

Do not expand S0/S2 to solve all of those. They belong after the mechanism gate.

## Burden-tested program

### S0: keep, then freeze

Run one fresh deterministic confirmation and save per-example evidence. No further task tuning.

### S1: keep; it is the decisive phase

The attention spotlight is the right minimal internal actuator. Applying it at eight layers is unnecessary until shown necessary.

Use a small, preregistered oracle-only sweep over configurable sites and fixed magnitudes. For example:

```text
sites: {20}, {24}, {20..27}
beta: 2, 4, 8
```

Choose by:

1. passes the paired rescue/break gate
2. fewest layers
3. lowest beta
4. highest net gain

A cheap teacher-forced likelihood screen may rank candidates, but the gate must use full free-running generation on a disjoint seed block.

Wrong-address behavior is mandatory. The behavioral requirement should be “correct-address accuracy clearly exceeds cyclic-wrong-address accuracy,” with wrong-span value echoes reported. Requiring every wrong spotlight to be worse than unmodified base is unnecessarily brittle.

### S2: simplify

Use one query-key scorer, direct address supervision, hard argmax, fixed β/site inherited from S1, and frozen cached h20 features. Report address accuracy before spending time on generation.

Do not automatically run the registered site/strength fallback:

- If address accuracy is poor, one preregistered tiny-head capacity fallback is defensible.
- If address accuracy is high but the identical hard address does not reproduce oracle behavior, debug the deterministic wiring; another training run is not justified.
- If both defined attempts miss, stop.

### S3: defer entirely

S3 is premature at [SELECTOR-PLAN.md:39](/home/bmarti44/stencil-llm/SELECTOR-PLAN.md:39). Do not write it until:

- S1 proves the actuator,
- S2 proves learned addressing,
- zero/wrong-address causality passes,
- prompt-only and no-wire baselines are known.

If reached, S3 must introduce actual authority changes: old records that genuinely were authoritative, variable update order, source-authority changes, paraphrased formats, derived/discovery-driven updates, and downstream behavior that applies the selected obligation rather than merely copying its value.

The present program can cleanly prove a contentless addressing actuator. It cannot yet prove that agents need one. The cheapest honest path is: harden the claim mechanically, run oracle S1, train the address classifier directly, and let the trivial baselines decide whether S3 deserves to exist.

**Overall confidence: high.**
