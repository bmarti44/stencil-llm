codex
## Bottom line

1. **Meaningful? Yes. Useful? Not yet proven.**
2. **True to the README’s architectural spirit? Yes. Proven to stop agent drift? No.**
3. **Dynamic inside its four-key template world? Yes. Generally flexible? No.**
4. **Can the core mechanism support agents? Yes. Can `focus_cache.py` be deployed as written? No.**

The new step-1500 result is decisive for the synthetic mechanism: learned-gate evaluation reached **100% within and beyond window**, versus **3.4% beyond with the code zeroed** ([log:15](/home/bmarti44/stencil-llm/results/logs/gpt2-cachev8-s0.log:15)). The focus code is causally doing the work.

That is an excellent GPT-2 mechanistic result. It is not yet evidence that anybody needs this instead of pinned instructions, summaries, retrieval, or an external task store.

## 1. Is it useful and meaningful?

**Meaningful: yes. Useful: not yet. Confidence: 95%.**

At step 999, before long-range training, learned routing produced 8/59 beyond-window answers versus 2/59 with zero code: +10.2 points ([log:10](/home/bmarti44/stencil-llm/results/logs/gpt2-cachev8-s0.log:10)). At step 1500, after 500 long-range steps, it produced 59/59 versus 2/59.

That establishes:

- The cache captures multiple concurrent mappings.
- Learned gates and learned addressing work on held-out sequences from this generator.
- The stored state survives distances the base model cannot traverse.
- Removing the wire removes almost all performance.
- Keyed slots solved the oscillator’s superposition failure.

This is not a fake result riding on LoRA, as v7 largely was. The zero-code control makes that clear.

But “useful” remains unanswered because a much simpler system can retain four short rules:

- Keep the instructions pinned.
- Reinsert them after compaction.
- Store them as text in an external task object.
- Retrieve the relevant instruction at each query.
- Maintain a structured plan.

The baseline gauntlet deferred to Qwen is therefore not optional. Without it, the honest result is:

> A supervised, event-gated latent cache can causally preserve and apply dynamically updated templated rules through context loss in a frozen GPT-2 trunk.

It is not:

> This is a better way to keep real agents focused.

### Most embarrassing caveats, in order

1. **Training uses oracle span, commit, and slot supervision.** The writer and reader are trained with ground-truth writes at [run_gpt2_arms.py:192](/home/bmarti44/stencil-llm/scripts/run_gpt2_arms.py:192). Learned routing is used only at evaluation.

2. **The grammar and semantic keys are fixed.** “Cat,” “sun,” “red,” and “king” always mean the same four slots; initial statements occur in a fixed order. The margin loss explicitly teaches those identities.

3. **No strong usefulness baseline exists yet.** Beating zero-code proves causality, not superiority to ordinary memory engineering.

4. **The registered READ-ridge timing gate was missed.** At step 500 the four read scores were 0%, 16.7%, 33.3%, and 41.7%, despite the registered `>50% by step 500` criterion. It recovered by step 1500 to 50%, 91.7%, 83.3%, and 83.3%, but the early miss must remain in the record.

5. **This remains one seed and a small interim beyond set.** The final registered differential requires at least 128 beyond examples; step 1500 has 59.

What changes “not yet useful” to “yes”: on Qwen, beat pinned instructions, reinsertion, compaction summaries, and retrieval at matched token cost, memory, latency, and task success on natural instruction-drift tasks.

## 2. Does it solve the spirit of README.md?

**Architecturally yes; empirically at agent scale, not yet. Confidence: 90%.**

The higher-level spirit is genuinely present:

- GPT-2’s trunk is frozen.
- LoRA and the cache learn how to apply task state.
- The current mapping varies per stream, so it cannot reside in fixed weights.
- The persistent cache is separate from the rolling token context.
- Its maximum state is tiny: eight slots × `(32-key + 128-value)` floats, about 5 KB in fp32.
- Zeroing that state collapses beyond-window behavior from 100% to 3.4%.

That is a clean knowledge/current-task split. The model retains general completion machinery in weights while the cache carries which mappings apply now.

Two qualifications matter:

- “Frozen knowledge” means the pretrained trunk is frozen, not the entire computational wiring. Full-matrix LoRA, the writer, reader, and injection projections are trained.
- The cache preserves the knowledge/focus distinction, but it no longer tests the slow-wave or oscillator story in [README.md:3](/home/bmarti44/stencil-llm/README.md:3). The biological inspiration should not receive credit for a keyed associative memory.

And it does **not yet** establish the motivating product statement. The README correctly calls deployed-agent drift a hunch rather than a proved result ([README.md:8](/home/bmarti44/stencil-llm/README.md:8)).

To earn that claim, demonstrate all three:

1. Delete the relevant textual instructions during actual compaction while preserving only cache state.
2. Show that behavior remains correct and stale instructions are overwritten.
3. Show better long-task adherence than ordinary retained-text baselines.

A cache-state transplant that swaps a donor task and flips the model’s behavior would also strengthen the “current task lives here” claim beyond the zero-code ablation.

## 3. Is it dynamic and flexible?

**Narrowly dynamic; not generally flexible. Confidence: 97%.**

What v8 has honestly shown is substantial but specific:

- Answer values vary across sequences.
- Four rules coexist.
- Updates overwrite prior values.
- Gaps and update schedules vary.
- Evaluation uses learned salience, commit detection, and `_address()`, not overrides.
- At step 1500 those learned components generalized across held-out examples from the same grammar.

So this is not a static prompt embedding.

But its flexibility boundary is tight:

```text
Known four semantic keys
+ fixed templates
+ fixed initial ordering
+ supervised statement boundaries
+ teacher-addressed training
+ 16 known answer values
```

It has not shown:

- Unseen key names or variable numbers of keys.
- Rules arriving in arbitrary order.
- Paraphrased or multi-sentence instructions.
- Instructions mixed with quoted examples, code, or tool output.
- Deletes, cancellations, priority changes, or conflicting sources.
- Nested goals and subgoals.
- Capacity overflow and principled eviction.
- Semantic addressing without ground-truth slot identities.

The store currently fills to six entries because it also stores the two demo statements. That is already evidence that “instruction-shaped text” and “current job state” are not the same thing.

The adversarial test also produced one false write at steps 1000 and 1500. That is the first deployment warning. Worse, the counter returns the number of occupied slots, not the number of commits ([run_gpt2_arms.py:377](/home/bmarti44/stencil-llm/scripts/run_gpt2_arms.py:377), [run_gpt2_arms.py:410](/home/bmarti44/stencil-llm/scripts/run_gpt2_arms.py:410)), so it can undercount repeated false writes.

### What makes it genuinely dynamic

For the Qwen rung, require:

- Unseen slot names and variable slot count.
- Random initial order.
- Held-out paraphrase families.
- `set`, `update`, `delete`, `cancel`, and priority changes.
- Instructions embedded among ordinary user text, retrieved documents, tool logs, and adversarial quotations.
- Learned-address confusion matrices and active-cache exact-match after every update.
- Capacity sweeps with explicit overflow behavior.
- A phase where training executes its own learned writes, rather than always teacher-forced writes.

There are two legitimate deployment directions:

- **Structured focus API:** the agent runtime calls `focus.set(key, value)` and `focus.clear(key)`. This is safer and more useful, but the project should call it a scaffolded focus store, not autonomous salience discovery.
- **Autonomous learned writer:** the model decides what to commit. This is the more ambitious claim, but false writes and prompt injection become first-order safety problems.

Start with the structured version. It directly serves the goal and isolates memory/readout from routing.

## 4. Can this concrete mechanism support multi-hour agents?

**The core design can. The current implementation cannot yet. Confidence: 95%.**

The late-layer contextual writer, exact-hold slots, keyed overwrite, query-conditioned read, and additive injection are all plausible components for Qwen and 7B.

But `focus_cache.py` has several deployment blockers.

### Immediate implementation blocker: token-stream state is incomplete

`CacheState` stores only completed slots ([focus_cache.py:26](/home/bmarti44/stencil-llm/src/stencil/focus_cache.py:26)). Span accumulation is reconstructed locally inside each call using `prev = -1` and the current tensor’s salient positions ([focus_cache.py:118](/home/bmarti44/stencil-llm/src/stencil/focus_cache.py:118)).

If an instruction is processed token-by-token, or a chunk boundary cuts through it, the eventual commit cannot see earlier salient tokens. It will encode only the current call’s fragment.

The chunk test splits after a completed commit and before the next instruction span ([test_gpt2.py:291](/home/bmarti44/stencil-llm/tests/test_gpt2.py:291)). It does not test a boundary inside an instruction, nor full-model decoding with position/KV state.

Add to `CacheState`:

```text
pending_sum
pending_count
pending/source metadata
position offset
completed slots
```

And make the model API explicitly return state:

```python
logits, next_cache_state = model(tokens, cache_state=state)
```

Do not rely on mutable `model.cache_states` side effects at [gpt2.py:345](/home/bmarti44/stencil-llm/src/stencil/gpt2.py:345).

### Other blockers

- No delete or invalidation operation.
- No source provenance or priority hierarchy.
- When full, the cache silently overwrites the lowest slot ID ([focus_cache.py:168](/home/bmarti44/stencil-llm/src/stencil/focus_cache.py:168)).
- Learned addressing accuracy is not measured directly.
- The Python dictionaries, per-example loops, `nonzero`, and scalar conversions are not an efficient batched implementation.
- Latent state is opaque to users and difficult to repair after corruption.
- A false commit can permanently alter future behavior.

### What breaks first in a real agent

1. **False writes from tool output, code, quoted instructions, or prompt injection.**
2. **Streaming span loss at token/chunk boundaries.**
3. **Wrong-key updates, slot overflow, and stale constraints.**
4. **The model stores the right instruction but fails to consult or obey it.**
5. **Latency and batching overhead.**

## Deployment ladder

### Finish GPT-2

Let the run finish unchanged. Require:

- Final learned-minus-zero differential ≥8 points at `n>=128`.
- The result across another seed.
- Cache transplant and shuffled-cache controls.
- Learned addressing accuracy, not merely teacher-addressed ridge.
- Active-versus-stale answer metrics after updates.
- The missed early READ gate and adversarial false write recorded explicitly.

### Qwen3-1.7B

First use structured message-boundary writes:

- Persist system/developer constraints, user goal, current subtask, decisions, and tests separately.
- Carry state through forced compactions.
- Use explicit update/delete keys.
- Keep untrusted tool output read-only.
- Compare against pinned prompt, reinsertion, summary, retrieval, and ordinary long-context KV.
- Measure adherence, stale-instruction errors, false writes, missed updates, memory, latency, and task success.

Only after that succeeds should learned salience/commit detection become the primary writer.

### 7B agentic coding

Integrate the cache with the agent runtime, not solely inside the transformer:

- Serialize focus state across turns and tool calls.
- Preserve human-readable text and provenance alongside latent values.
- Separate goal, constraints, current subtask, accepted decisions, and completion criteria.
- Test multi-hour repo tasks with several compactions and mid-task reversals.
- Measure instruction violations and rework, not just final benchmark success.

## Owner-level verdict

The step-1500 result means the project has crossed an important line: **the focus cache works mechanistically on GPT-2, and the wire is causally responsible.**

It has not crossed the next line: **nobody yet knows whether this is better than retaining or retrieving the task specification in ordinary ways.**

Proceed to Qwen if the final registered differential holds. Present v8 as a successful supervised focus-memory proof, not as a solution to agent drift. The Qwen baseline gauntlet is where “interesting toy” becomes either “useful agent mechanism” or “an elaborate substitute for a pinned prompt.”
