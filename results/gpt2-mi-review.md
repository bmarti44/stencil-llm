## Verdict

Run 3 has already moved the needle—but it has not yet shown that the graft is learning.

The base rank-8 arm fell from 14.50 loss to 1.68 at step 200 and **0.090 at step 400** on fresh near-curriculum batches: [progress JSON](/home/bmarti44/stencil-llm/results/gpt2/base-lora8-s0-progress.json). Each sequence has four randomized queries and two fixed demos. Even assuming zero demo loss, the query loss at step 400 is at most:

\[
L_\text{query} \le \frac{6}{4} \times 0.090 = 0.136
\]

So full qkv/attention/MLP LoRA has solved the reachable-rule prerequisite. The earlier “GPT-2 cannot apply the rule” blocker is gone.

But this is the stateless base arm. The experiment still has not demonstrated:

- reliable storage of four active rules in the oscillator;
- rule-selective actuation through the scalar head gates;
- above-chance performance when rules are beyond the trunk’s receptive field.

My blunt expectation: run 3 should produce strong near/in-reach results. Its chance of producing a substantial long-range oscillator advantage is much less certain because the remaining bottleneck is the wire-to-residual actuator, not adapter capacity.

## What the remote computation actually does

For an unreachable rule token at position \(r\), the only path to a query logit at \(q\) is:

```text
frozen rule-token embedding
  → continuously driven oscillator cells
  → 128-d control state at q
  → RMS normalization
  → 144 scalar gate values
  → rescale already-computed attention-head outputs
  → output projection / residual / MLP
  → frozen tied vocabulary head + logit bias
```

Relevant implementation:

- The controller consumes every token embedding: [gpt2.py:233](/home/bmarti44/stencil-llm/src/stencil/gpt2.py:233).
- The state is RMS-normalized once: [gpt2.py:260](/home/bmarti44/stencil-llm/src/stencil/gpt2.py:260).
- Gates are `2*sigmoid`, hence positive and bounded by 2: [gpt2.py:147](/home/bmarti44/stencil-llm/src/stencil/gpt2.py:147).
- A gate multiplies a head’s value output **after attention selection/softmax**: [gpt2.py:111](/home/bmarti44/stencil-llm/src/stencil/gpt2.py:111).
- LoRA changes qkv, output projections and MLPs, but it is not directly conditioned on the wire: [gpt2.py:104](/home/bmarti44/stencil-llm/src/stencil/gpt2.py:104).

Consequently, the wire cannot tell a head what token to attend to. At a remote query there is no rule content in the local attention values anyway. The wire has to encode the answer using a pattern of 144 scalar volume controls over whatever head-output vectors happen to exist. Later residual/MLP computation must decode that amplitude pattern into one of 16 frozen output embeddings.

That path is connected, but “nonzero Jacobian” is a very low bar. The reachability test only checks `g_osc > 0`: [test_gpt2_reach.py:61](/home/bmarti44/stencil-llm/tests/test_gpt2_reach.py:61). It does not establish usable magnitude, class rank, or actuator capacity.

## Ranked findings

### 1. High — The main remaining blocker is actuator capacity, not a dead gradient

The gates provide a conditional channel, but an awkward one: one positive scalar per head, applied after attention has already chosen and aggregated its values. The gate cannot inject an arbitrary rule vector, alter attention weights, or directly select a LoRA transformation.

Repo evidence:

- Gate-only and output-projection-LoRA runs stayed near chance: [WORKLOG.md:17](/home/bmarti44/stencil-llm/WORKLOG.md:17), [base rank-4 result](/home/bmarti44/stencil-llm/results/gpt2/base-lora-s0.json).
- My first-step diagnostic found nonzero gradients in the gate source, controller, and every LoRA up-projection. Only the zero-initialized LoRA down matrices had exactly zero gradient on step zero, as expected.
- In the failed oscillator checkpoint, gates had standard deviation 0.33 and only 0.4% of preactivations had `|pre| > 4`. Sigmoid saturation was therefore not the main failure.
- A normalized-state ridge probe on 1,024 new sequences decoded one slot’s 16-way answer at 11.3% from the untrained wire and 14.5% from the failed trained wire. Weak, but above 6.25% chance while output remained at chance. Information exists that the actuator is not using effectively.

Fast falsifier: replace the controller output with freely optimized per-example gate logits for 16–32 fixed examples. If even oracle gates cannot push the correct candidate to top-1, the gate site is decisively inadequate. Also compute the Jacobian/SVD of the 16 candidate logits with respect to the 144 gate preactivations.

### 2. High — The oscillator is being used as an all-token resonator, not a clean job register

Every filler sentence, demo and query token forces the oscillator: [oscillator.py:218](/home/bmarti44/stencil-llm/src/stencil/oscillator.py:218). There is no instruction mask, update boundary, reset, or keyed slot operation.

Both undamped cells use the same 8–2048 period grid. Raw query-time state RMS was roughly \(3.8\times10^5\) at initialization and \(6.6\times10^5\) in the failed checkpoint. RMS normalization keeps gates numerically usable, but:

- it removes all radial/amplitude information;
- its Jacobian contains a roughly \(1/\mathrm{RMS}\) factor;
- the retained direction can be dominated by resonant filler/position components;
- terminal query losses must train the controller to suppress hundreds of irrelevant inputs.

This is much harder than the toy setting, where embeddings, trunk and output circuits trained together and cues were explicit atomic tokens.

Fast falsifier: run the same wire probe on paired sequences differing only in one rule answer. Measure separation immediately after the rule and at the query. Repeat with oscillator forcing masked to rule/update spans. A large masked-state improvement identifies filler interference directly.

### 3. High, now resolved locally — Earlier LoRA placement could not learn retrieval/application

Rank-4 LoRA on attention output projections could only remix an already-computed attention result. It could not change attention selection, values, or MLP features. Its flatline was therefore not strong evidence that frozen GPT-2 fundamentally cannot learn the task.

Run 3’s full qkv/MLP LoRA has falsified that pessimistic hypothesis by step 400. This is the best news in the review.

What remains to falsify: evaluate the step-400/1000 model on a fixed held-out near set. The current result is a fresh training-stream batch, not a fixed validation set, although it cannot be explained by memorizing that exact batch.

### 4. Critical for “see results quickly” — The runner hides the answer until the run is over

The current runner:

- combines demo and real-query loss;
- logs one noisy batch every 200 steps;
- performs no near validation during the curriculum;
- reports no candidate-restricted accuracy or top-5;
- saves no intermediate checkpoint;
- evaluates only after all 4,000 steps: [run_gpt2_arms.py:103](/home/bmarti44/stencil-llm/scripts/run_gpt2_arms.py:103).

With two fixed demos and four uniformly random query targets:

- input-independent optimal aggregate CE is about **2.716**, not `ln(16)`;
- perfect demos plus chance query selection gives aggregate CE **1.848**.

Therefore an aggregate decline can initially be demo learning. Step 400’s 0.090 is strong enough to rule that out, but most intermediate values are ambiguous.

Fast falsifier/fix: every 50–100 steps report separately:

- real-query CE and exact accuracy;
- demo CE and accuracy;
- candidate-restricted 16-way CE/top-1/top-5;
- fixed near-set results split by actual answer-token distance;
- for osc, fixed standard within/beyond accuracy;
- gate quantiles and saturation;
- a checkpoint.

This would have answered the local question at step 200–400 instead of after an hour.

### 5. Medium — “Near” was not actually a direct-attention curriculum

I measured 1,024 near-family queries:

- answer-token distance: 59–120;
- median: 91;
- directly attendable within the 64-token layer window: only 33/1,024, or 3.2%.

So almost every “near” example requires a two-layer relay through intervening text. The old evaluation’s “within” bin is looser still: anything up to 756 tokens.

This matters because theoretical graph reachability is not the same thing as a pretrained GPT-2 capability. Fortunately, run 3 has now learned this relay.

Fast falsifier: build distance rungs at 32, 64, 96, 128 and 256 tokens and evaluate the same checkpoint. That reveals exactly where retrieval fails, in minutes.

### 6. Medium — The task contains avoidable token-translation difficulty

Inside a quoted rule, `dog` is token 9703. The output target `" dog"` is token 3290. Similar mismatches occur for every answer. The model must learn a semantic/bare-to-leading-space transformation rather than copy or retrieve the exact answer token.

Combined with four slots, 16 answers, updates, and 1,024-token streams, that made the first experiment unnecessarily difficult.

Fast falsifier: use a rule template where the answer appears with exactly the same token ID as the target, one slot and \(k=4\), within 32 tokens. Then increase one dimension at a time.

### 7. Medium-low — Optimizer details are secondary, not the root cause

The runner applies one `3e-4`, weight-decayed AdamW group to controller frequencies, gate biases, logit bias and all LoRA matrices: [run_gpt2_arms.py:97](/home/bmarti44/stencil-llm/scripts/run_gpt2_arms.py:97). The toy optimizer exempted oscillator and bias/norm parameters from decay.

Other observations:

- All LoRA down matrices have exactly zero gradient on step zero because their up matrices are zero. They begin learning after the up matrices move.
- Gate/controller gradients are live.
- Run 3 learning rapidly at `3e-4` shows the LR is not preventing local adoption.

Quick test: a 50-step fixed-batch overfit with adapter LRs `{3e-4, 1e-3, 3e-3}`, controller LR lower, and zero decay on bias/controller. Do this only after the representation/actuation tests; hyperparameter sweeps will not repair a bad communication site.

### 8. Low — Several declared invariants do not match the implementation

These are not causing the flatline, but they weaken comparisons:

- The arms do not have identical trainable budgets. Gate-only base has 160,993 trainables versus osc’s 130,401; with full LoRA the totals are approximately 1,340,641 versus 1,310,049.
- Gates do not initialize as an exact no-op unless bypassed; the test explicitly asserts ordinary initialized gates change logits: [test_gpt2.py:55](/home/bmarti44/stencil-llm/tests/test_gpt2.py:55).
- Distance bins use the start of the statement rather than the answer token, misclassifying boundary cases by about nine tokens.
- The dial probe uses 72 training examples for a 128-dimensional raw-state regression and only 24 test examples; it probes raw state even though gates consume normalized state: [run_gpt2_arms.py:172](/home/bmarti44/stencil-llm/scripts/run_gpt2_arms.py:172).
- The transplant supplies the donor’s entire trajectory without aligning the recipient’s slot-query position to the donor’s corresponding query position.

## Fast diagnostic sequence

I would run these before another full fleet:

1. **Instrument run 3.** Add query/demo split, fixed near and standard evals, candidate metrics, and checkpoints. This is the highest-return change.

2. **Distance ladder.** Evaluate rules at answer-token distances 32, 64, 96, 128, 256. Run 3 should now pass the first four strongly.

3. **Upper bounds.**
   - Current LoRA on one-rule, 32-token, \(k=4\) fresh examples.
   - Same task with the top two blocks or trunk unfrozen.
   - Fixed-batch overfit versus fresh-example generalization.

4. **Wire representation.** Probe normalized control state immediately after each rule and at each query, using at least 1,024 examples and a permutation/majority baseline. Use counterfactual paired rule swaps.

5. **Wire actuation.** Optimize oracle gates/control vectors while freezing everything else. If oracle gates fail, change the actuator immediately.

6. **Attention/logit lens.** On direct examples, record relevant-rule attention mass per head and the correct answer’s candidate rank after every block. Gate changes cannot alter attention weights directly; qkv LoRA must do that job.

7. **Temporal gradient trace.** Retain control-state gradients and report their norm at the relevant rule, filler, demo and query positions. This tells whether terminal credit reaches rule encoding or only tunes query-time gates.

## Ranked minimal interventions

1. **Let the current osc pilot reach the standard phase, but only with early evaluation.** Run 3 has earned this test. Do not launch more seeds yet.

2. **If long-range adoption stays flat, add a zero-initialized additive wire projection into the residual stream.** For example, after attention projection in the last few blocks:

   ```python
   x = x + attention_output + wire_up[layer](control_normalized)
   ```

   This gives the wire a content-bearing direction instead of forcing it to encode answers as head volumes. A late fusion module combining `x_query` and `control_query` is even more direct and lets local GPT-2 knowledge interpret the job state.

3. **Make the controller instruction-driven.** Mask oscillator forcing to rule/update spans, or use a four-slot event-driven latch updated at authenticated rule boundaries. The existing repo already contains latch designs. This is mechanically closer to “a wire carrying the current job” than continuously integrating every filler token.

4. **Add temporary auxiliary wire supervision.** Predict each slot’s active answer from the wire at queries and updates; discard the auxiliary head at evaluation. This honestly answers whether the memory can be trained, instead of asking sparse output loss to discover memory and actuation simultaneously.

5. **Use a visible-result curriculum:** one slot, \(k=4\), exact token match, distance <48; then four slots; then \(k=8/16\); then 96/128 distance; then beyond 756. More fixed demos are not the answer—they reward format while consuming a third of the loss. More randomized main queries per rule are better.

6. **Only then try controller-conditioned LoRA/FiLM.** A simple version is `B(diag(s(control)) A x)` or layerwise scale-and-shift. This is more expressive than scalar head gates but more invasive than additive residual injection.

7. **Optimizer tuning last.** Raise LoRA/gate-readout LR, lower controller LR, remove decay from controller/bias, and add clipping/warmup if gradient traces justify it.

## What to watch in run 3

The base arm has already passed its near prerequisite at step 400. The current loss is an honest visible result for the adapter, not yet for the graft.

During the first 1,000 steps:

- Osc near loss should collapse similarly to base. If it does not, controller-driven gates are interfering with otherwise-learnable LoRA computation.
- Record fixed held-out near query accuracy; do not rely on the one training batch.
- Gate values should spread without mostly pinning at 0 or 2.
- Normalized wire probe accuracy should rise substantially above the weak 11–15% observed so far.

At the step-1,000 transition:

- Expect loss to jump; the task distribution becomes genuinely long-range.
- Base beyond-window accuracy should stay at chance.
- Osc beyond-window candidate CE and exact accuracy must begin improving within the next few hundred steps.
- If osc within accuracy remains high but beyond accuracy and wire probes remain flat after roughly 500 standard steps, stop. More of the same training is unlikely to discover a usable actuator.
- If the wire probe rises but output does not, move directly to additive residual injection.
- If neither rises, mask/cue the controller or add auxiliary wire supervision.

The shortest honest path is now very clear: preserve run 3’s successful full LoRA, expose real-query metrics immediately, and treat additive late fusion plus instruction-only controller updates as the next move if the oscillator arm fails beyond the window.
tokens used
