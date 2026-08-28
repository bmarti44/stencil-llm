codex
## Decision

Choose **D: close the undamped-oscillator branch as a negative, then continue with a hard event-gated, keyed focus cache**.

This is A’s exact-hold idea, but not a literal drop-in of the toy latch. If forced to choose only A/B/C, choose **A**, with the redesign below.

Do not make B the mainline. Damping trades filler suppression directly against long-term instruction retention—the exact capability the README requires. Preserve B as a cheap comparator, not another rescue campaign.

**Recommendation confidence: high, about 85%.**

The governing goal is a separate state that preserves the current job while ordinary context churns ([README.md:8](/home/bmarti44/stencil-llm/README.md:8), [README.md:14](/home/bmarti44/stencil-llm/README.md:14)). Stable, updateable state fits that goal better than continuous resonance.

## Why literal A is insufficient

The existing toy latches do not solve the real problem as written:

- `CueLatch` stores the projection of the **latest single cue token** ([oscillator.py:448](/home/bmarti44/stencil-llm/src/stencil/oscillator.py:448)). With salience high across a natural-language statement, it repeatedly overwrites itself and ends up holding the final salient token—often punctuation or syntax—not the statement.
- `KeyedCueLatch` has four fixed registers and recognizes updates through hard-coded token IDs ([oscillator.py:483](/home/bmarti44/stencil-llm/src/stencil/oscillator.py:483)). That is perfect for the toy generator and unusable for arbitrary task specifications.

The actual mechanism needs three things the toy latch lacks:

1. A contextual encoder that compresses a complete instruction or update.
2. Multiple keyed entries, so one update does not erase unrelated constraints.
3. Exact no-write semantics, so 1,000 filler tokens produce exactly zero state change.

Soft recurrence is the pathology. Even a filler write strength of 0.001 gives \((1-0.001)^{1000}\approx0.37\) retention in a conventional soft latch. The forward write event must therefore be hard or exactly sparse.

## Recommended focus-cache design

### State

For the GPT-2 pilot:

```text
4–8 slots
key:   32 or 64 dimensions per slot
value: 128 dimensions per slot
valid/version/source metadata
```

For Qwen/agent work, scale explicitly rather than pretending a 128-vector can hold an arbitrary job:

```text
16–32 slots
2–4 value vectors × 256 dimensions per slot
key + validity + source priority + version/age
```

A real task description has nontrivial information content. Memory must grow with task complexity; no fixed tiny vector can preserve an arbitrarily large specification after compaction.

### Contextual writer

Do not encode directly from static token embeddings again.

For GPT-2, run blocks 0–7 normally, then use their contextual hidden states to encode candidate instructions. This is convenient because the existing residual injection already targets blocks 8–11.

```text
blocks 0–7
    ↓ contextual hidden states
salience/span accumulator + commit detector
    ↓
key/value writer
    ↓
persistent focus slots
    ↓ query-conditioned read
blocks 8–11 additive injection
```

During a salient span:

```python
candidate_sum += salience_t * writer_proj(hidden_t)
candidate_mass += salience_t
```

At a learned or structured statement-end commit:

```python
value = value_mlp(candidate_sum / candidate_mass)
key = key_mlp(candidate_sum / candidate_mass)
```

Then reset the temporary candidate accumulator. The existing `rule_events` at [nl_task.py:100](/home/bmarti44/stencil-llm/src/stencil/nl_task.py:100) can supervise the commit detector during this synthetic phase.

### Hard write and hold

Forward behavior should be discrete:

```python
if commit:
    slot = match_existing_key_or_allocate(key)
    keys[slot] = key
    values[slot] = value
    valid[slot] = True
else:
    # Bitwise unchanged.
    keys, values, valid = previous_state
```

For differentiable training, use a straight-through hard commit or an exactly sparse thresholded gate. Do not use `state = (1-s)*old + s*new` with small nonzero filler values.

Updates with the same key overwrite that slot. Deletes/cancellations invalidate it. Other slots must remain bitwise unchanged.

For the real agent, prefer available structure over pretending the v5 lexical classifier transfers:

- System/developer/user message roles.
- Explicit plan or task-update events.
- A `focus.set(key, text)` / `focus.clear(key)` action.
- Learned natural-language routing only after the memory mechanism works.

Using deployment-visible message roles is not oracle leakage. Allowing arbitrary tool output or retrieved text to write persistent focus state would also create a prompt-injection vulnerability.

### Read and injection

At each token, read only the relevant focus entries:

```python
q = query_proj(current_hidden)
scores = q @ keys.T
weights = softmax(scores.masked_fill(~valid, -inf))
read = weights @ values
code = rms_norm(read_proj(read))
```

Feed `code` through the existing zero-initialized additive projections into blocks 8–11. That actuator has already been validated.

For continuous global constraints, optionally include a small pooled “always active” focus vector alongside the query-selected slot.

### Compaction behavior

The focus state must become an explicit input/output of streaming inference:

```python
logits, next_focus_state = model(tokens, focus_state=previous_focus_state)
```

Serialize it independently of the rolling token context. Required verification:

- Process a stream continuously.
- Process the same stream in chunks while deleting old token context but carrying the focus state.
- Relevant outputs and final focus state must agree.

Without that test, this remains a full-sequence training trick rather than a deployable compaction-resistant memory.

## First 500-step decision gates

Before training, deterministic tests must prove:

- Ten thousand filler tokens cause bitwise-zero state change.
- Updating slot 2 changes only slot 2.
- Repeating an update replaces the stale value.
- Chunked execution across simulated compaction matches continuous execution.
- Bypassing the cache restores the stateless model exactly.

Then require:

### By step 100

- Rule-end capture CE well below \(\ln 16\), preferably `< 1.5`.
- Rule-end capture accuracy above 50%, trending rapidly upward.
- If capture is still at chance, stop: the contextual writer is broken.

### By step 250

- Rule-end accuracy above 80%.
- Near query auxiliary accuracy above 50%.
- Current-answer decoding beats stale-answer decoding after updates.
- If capture works but near-query retention is at chance, stop and audit addressing/readout.

### By step 500

On a sufficiently large fixed held-out set:

- Near query accuracy above 90%.
- Query auxiliary CE clearly below 2.0.
- Beyond-window standard accuracy at least 15–20%, versus 6.25% chance.
- Active-answer accuracy materially exceeds stale-answer accuracy after updates.
- A probe decodes all four slots—not merely slot 0.
- Transplanting the focus state changes answers while the frozen trunk remains untouched.

Near accuracy alone remains meaningless because the trunk can solve near examples without the wire.

If beyond-window behavior remains at chance despite clean capture and exact hold, close the GPT-2 experiment. No v8 routing or optimizer patch.

## Why B is the wrong mainline

A leaky oscillator faces a structural tradeoff. Approximately:

\[
\text{instruction signal after }D\text{ tokens}\propto\lambda^D
\]

while continually injected filler noise approaches a steady magnitude proportional to:

\[
\frac{\epsilon}{\sqrt{1-\lambda^2}}
\]

Stronger damping reduces accumulated noise but destroys instructions across long gaps. Weaker damping preserves instructions but accumulates leakage. Compaction makes refresh impossible because the original instruction has disappeared.

Input-dependent resets, exact forcing gates, and keyed overwrites could fix this—but by then the oscillator has become a gated state-space memory whose crucial behavior is latch-like.

B is worth one cheap controller-only comparison on cached hidden-state streams. It must beat a matched nonoscillatory latch on retention length, updates, and interference. Do not spend another full GPT-2 run merely to preserve the word “oscillator.”

## Honesty audit

| Option | Honest success claim | Knowledge/focus split? | Limitation |
|---|---|---|---|
| A, literal toy latch | A supervised cue-triggered register lets frozen GPT-2 retain a templated task beyond its context. | Yes, narrowly. | Single-token/fixed-slot shortcut; no natural-language or scale result. |
| B, damped oscillator | A supervised, damped oscillatory controller retains templated rules beyond context. | Yes. | Oscillation gets credit only if it beats matched real-pole/latch baselines and uses genuinely oscillatory modes. |
| C | The current undamped, continuously forced two-cell oscillator fails at GPT-2 scale despite validated routing, actuation, and direct capture supervision. | Tests—and rejects—this implementation, not the broader split. | Does not falsify all oscillatory or external-memory mechanisms. |
| D, focus cache | A separately persisted, event-gated task state lets frozen model knowledge remain usable through task updates and context compaction. | Yes—this is the most literal implementation of the README split. | Architecturally, it is a supervised memory module until it wins natural drift benchmarks against strong baselines. |

“Anyone can build a memory module” is fair. A GPT-2 success would prove mechanism existence and causality, not novelty or deployed usefulness.

At Qwen and 7B, the project only earns the stronger claim if the focus cache beats:

- Pinned or periodically reinserted instructions.
- Compaction summaries.
- Retrieval from an external task specification.
- A simple GRU/SSM or latent recurrent state.
- Standard long-context/KV retention.

The existing adversarial review already identified the absence of literal latches and pinned/global instruction retention as a serious weakness ([devils-advocate.md:75](/home/bmarti44/stencil-llm/results/devils-advocate.md:75), [devils-advocate.md:87](/home/bmarti44/stencil-llm/results/devils-advocate.md:87)).

## Can the oscillator remain relevant?

Yes, but not as content storage.

A nonceremonial hybrid would:

- Store instruction content exactly in keyed latch/cache entries.
- Use an oscillator only to control recency, urgency, periodic rehearsal, or time-dependent retrieval priority.
- Never let oscillation mutate the stored content.

That requires a benchmark where timing matters: expiring subgoals, periodic checks, alternating task phases, or scheduled revisits. The present mapping task has no such requirement. Adding an oscillator to it now would be decorative.

## Is C already the more valuable result?

For the oscillator hypothesis, **yes**. The accumulated autopsy is more valuable than another damping tweak:

- Adapter capacity isolated.
- Actuator ceiling directly tested.
- Routing gradient failure measured and then repaired.
- Salience made sharply selective.
- Capture supervision moved directly to statement ends.
- The controller still remained at chance ([WORKLOG.md:110](/home/bmarti44/stencil-llm/WORKLOG.md:110)).

Freeze and write that negative now. Do not describe it as “oscillators cannot work”; describe the exact architecture and forcing regime.

For the broader README goal, stopping completely would be premature. One bounded focus-cache experiment answers a different and more important question: does separating persistent task state from frozen model knowledge help at all on a real model?

So the blunt recommendation is:

> End the oscillator rescue program. Preserve its negative. Run one hard-stop GPT-2 focus-cache pilot, then move to Qwen only if it produces unmistakable beyond-window behavior by step 500.
