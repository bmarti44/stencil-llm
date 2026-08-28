codex
## Verdict

The iteration-3 graph is connected correctly. I found no detach, missing optimizer parameter, wrong layer index, dead injection branch, incorrect label alignment, or aux-head omission from the optimizer.

The auxiliary chance result is real: the controller is receiving gradients, but its normalized state contains almost no answer-discriminating signal. The continuously driven resonator has become enormous and nearly direction-constant.

No critical wiring defect. There is one high functional blocker and several medium audit/design defects.

## 1. Aux gradient path — connected

The path is:

```text
aux_ce
 → aux_head
 → stacked injection_code[b, query_position]
 → RMS normalization
 → ExternalOscillatorController
 → cell-2 B/a_raw
 → W_a/W_b
 → cell-1 B/a_raw
```

Code:

- Aux states are taken without `detach()` or `no_grad()`: [run_gpt2_arms.py:136](/home/bmarti44/stencil-llm/scripts/run_gpt2_arms.py:136).
- Aux CE is added to the main loss before backward: [run_gpt2_arms.py:142](/home/bmarti44/stencil-llm/scripts/run_gpt2_arms.py:142).
- `loss.backward()` follows normally: [run_gpt2_arms.py:169](/home/bmarti44/stencil-llm/scripts/run_gpt2_arms.py:169).
- `control_states()` invokes the controller without disabling gradients: [gpt2.py:256](/home/bmarti44/stencil-llm/src/stencil/gpt2.py:256).
- Both oscillator implementations use ordinary differentiable operations: [oscillator.py:218](/home/bmarti44/stencil-llm/src/stencil/oscillator.py:218), [oscillator.py:256](/home/bmarti44/stencil-llm/src/stencil/oscillator.py:256).

The only oscillator buffer is `g_zero`, because damping is intentionally non-learnable: [oscillator.py:169](/home/bmarti44/stencil-llm/src/stencil/oscillator.py:169). These remain trainable parameters:

- `controller.W_a`
- `controller.W_b`
- `controller.cells.0.a_raw`
- `controller.cells.0.B`
- `controller.cells.1.a_raw`
- `controller.cells.1.B`

On the exact 8×1024 step-0 near batch, auxiliary CE alone produced dense, nonzero gradients in all six controller tensors:

- 61,568/61,568 controller parameter elements had nonzero gradient.
- Controller gradient L2 was 16.78.
- Aux-head gradient L2 was 2.08.
- Trunk, gates, LoRA, injection matrices and logit bias correctly received no gradient from the auxiliary-only loss.

So the gradient does not die.

## 2. Optimizer inventory — complete, with no duplicates

For the osc arm, `trainable` contains:

| Group | Tensors | Parameters |
|---|---:|---:|
| controller | 6 | 61,568 |
| gate source | 2 | 18,576 |
| additive injection | 4 | 393,216 |
| full rank-8 LoRA | 96 | 1,179,648 |
| logit bias | 1 | 50,257 |
| **Model total** | **109** | **1,703,265** |
| aux head | 2 | 2,064 |
| **Optimizer total** | **111** | **1,705,329** |

All 111 optimizer parameter identities are unique.

For base, the model trainables are the reported 1,832,289:

- 110,736 gate-source parameters;
- 98,432 in `control_proj`;
- 393,216 injection;
- 1,179,648 LoRA;
- 50,257 logit bias.

The aux head is appended explicitly at [run_gpt2_arms.py:120](/home/bmarti44/stencil-llm/scripts/run_gpt2_arms.py:120). Weight decay at 0.01 is much too weak to pin it at chance.

I also reproduced a fixed-batch aux-only optimization using the same initialization, AdamW, LR and 0.3 weight:

- step 0: CE 2.908, accuracy 9.4%
- step 50: CE 2.189, accuracy 21.9%
- step 100: CE 1.648, accuracy 34.4%

The optimizer and backward path demonstrably work.

## 3. High — The normalized oscillator code is effectively answer-blind

This is the smoking gun, but it is a representation failure rather than a wiring mistake.

At the current step-1500 osc checkpoint:

- raw query-state RMS: approximately **5.5–6.1 million**;
- the answer token changes raw state by only **0.30–0.35%**;
- the answer token changes normalized code by about **0.0008 RMS**;
- query-to-query one-token code change is similarly only about **0.00086 RMS**.

Held-out ridge results from 1,024 near sequences:

- one shared decoder over all slots: 6.25–7.3%;
- separate slot-0 decoder: approximately 6.6–8.2%;
- other separate slot decoders: also chance;
- adding explicit one-hot slot identity: still chance.

Even more decisively, on a separate held-out set the normalized code was at chance **at the rule’s answer token itself**, not only after the delay:

- answer-token probe: 6.4–7.8%;
- statement-end probe: 6.4–7.8%;
- query probe: 6.8–8.0%.

The auxiliary head has no stable class structure to exploit. It is being shown sixteen heavily overlapping clouds.

The causal mechanism is exactly the earlier filler-drowning concern:

- every one of 1,024 embeddings forces cell 1;
- its output continuously forces cell 2;
- both undamped cells use the same period grid;
- raw state grows into the millions;
- RMS normalization discards magnitude and retains a direction barely changed by the rule token.

Severity: **High**, because it blocks both auxiliary decoding and additive injection.

## 4. Normalization consistency — correct

`injection_code()` does:

```python
control = control_states(tokens)
control = norm(control)
control = control_proj(control)  # base only
return norm(control)
```

Forward does the same:

```python
control = norm(control_states(tokens))
code = control if osc else control_proj(control)
code = norm(code)
```

See [gpt2.py:267](/home/bmarti44/stencil-llm/src/stencil/gpt2.py:267) and [gpt2.py:295](/home/bmarti44/stencil-llm/src/stencil/gpt2.py:295).

For osc, the second normalization is mathematically redundant because `control_proj` is absent. It is not a mismatch and is not what pins aux at chance. Both the aux head and injection receive the same normalization pathology.

The helper recomputes the controller instead of reusing the exact forward tensor. There is no dropout or state mutation, and deterministic execution is enabled, so this is not a correctness bug. Refactoring forward to optionally return `code` would nevertheless remove duplicate controller computation and make identity structurally guaranteed.

Severity: **Low**.

## 5. Injection path — correctly live in both arms

For every non-vanilla arm:

- `inject` contains four `128→768`, bias-free matrices: [gpt2.py:231](/home/bmarti44/stencil-llm/src/stencil/gpt2.py:231).
- Base additionally gets `768→128 control_proj`: [gpt2.py:225](/home/bmarti44/stencil-llm/src/stencil/gpt2.py:225).
- Training/evaluation use `gate_bypass=False` by default, so `code` is non-`None`: [gpt2.py:295](/home/bmarti44/stencil-llm/src/stencil/gpt2.py:295).
- Zero-based block indices 8, 9, 10 and 11 map one-to-one to `inject[0:4]`: [gpt2.py:307](/home/bmarti44/stencil-llm/src/stencil/gpt2.py:307).
- Injection enters after the attention residual and before LN2/MLP: [gpt2.py:123](/home/bmarti44/stencil-llm/src/stencil/gpt2.py:123).
- Evaluation calls ordinary `model(toks)`, so injection remains active: [run_gpt2_arms.py:81](/home/bmarti44/stencil-llm/scripts/run_gpt2_arms.py:81).
- `gate_bypass=True` disables both gates and injection, as intended.

All four osc checkpoint injection matrices moved from zero. Their L2 norms are approximately 1.45, 1.55, 1.60 and 1.48. That movement comes from the main forward loss; aux does not touch injection parameters. This independently confirms every injection matrix is in the optimizer and loss graph.

## 6. Aux head and labels — correct, but the objective is weaker than intended

The tensor shapes are correct:

- 32 query states per batch: four queries × eight sequences;
- each state is 128-dimensional;
- aux head produces 16 logits;
- targets are integer indices into `ANSWER_WORDS`.

`active_answer` is constructed in exactly the same order as `query_positions`: [nl_task.py:191](/home/bmarti44/stencil-llm/src/stencil/nl_task.py:191). The zip at [run_gpt2_arms.py:139](/home/bmarti44/stencil-llm/scripts/run_gpt2_arms.py:139) is therefore correct.

A reproduced first batch had clearly nonconstant labels covering all 16 classes. Across fresh batches they are uniform.

There is, however, a design mismatch:

- The earlier ridge probe was slot-specific.
- The new aux head is one shared linear classifier over all four slots.
- Supervision occurs only at query positions—not at rule/update positions—so this is still terminal supervision through the entire resonator, not true intermediate capture supervision.

A more faithful auxiliary readout would use four slot-specific heads:

```python
aux_head = nn.Linear(128, 4 * len(ANSWER_WORDS))
aux_logits = aux_head(states).view(-1, 4, 16)
selected = aux_logits[torch.arange(len(aux_slots)), aux_slots]
aux_ce = F.cross_entropy(selected, aux_targets)
```

This change belongs around [run_gpt2_arms.py:119](/home/bmarti44/stencil-llm/scripts/run_gpt2_arms.py:119) and [run_gpt2_arms.py:137](/home/bmarti44/stencil-llm/scripts/run_gpt2_arms.py:137).

But it is not sufficient by itself: the current checkpoint’s separate per-slot probes are also at chance. The controller input dynamics must be fixed first.

Severity: **Medium**.

## 7. Medium — The checkpoint omits the aux head

The checkpoint contains:

- controller;
- gate source;
- injection;
- LoRA;
- logit bias;
- step number.

It does **not** contain `aux_head.state_dict()`.

That does not affect uninterrupted training or final model evaluation, because the aux head is deliberately train-only. But it means:

- the run cannot be resumed exactly;
- the trained aux head cannot be audited afterward;
- a checkpoint-based connectivity test cannot distinguish a moving head from a frozen one.

Precise fix at [run_gpt2_arms.py:186](/home/bmarti44/stencil-llm/scripts/run_gpt2_arms.py:186):

```python
"aux_head": aux_head.state_dict(),
```

Do the same in the final save if diagnostic reproducibility matters.

Also, `trainable_params` excludes the aux head’s 2,064 parameters. That is only a reporting issue.

## 8. Medium — The injection test can pass without exercising injection

In [test_gpt2.py:156](/home/bmarti44/stencil-llm/tests/test_gpt2.py:156), the test perturbs injection weights and then asserts non-bypass output differs from vanilla. But ordinary initialized gates already make the model differ from vanilla. Therefore the final assertion can pass even if `_Block.forward` silently ignores `inj`.

Replace that portion with:

```python
before = m(toks)
for _, p in inj:
    p.add_(0.01)
after = m(toks)
assert not torch.equal(after, before)
```

Add a second test that constructs aux CE and asserts every controller parameter has a non-`None`, nonzero gradient. The current green suite verifies inertness and classification, not actual loss connectivity.

## 9. Replay/eval/base path — correct

- Replay is exactly deterministic rows 0 and 4 of every eight-item phase-2 batch: [run_gpt2_arms.py:131](/home/bmarti44/stencil-llm/scripts/run_gpt2_arms.py:131).
- Mixed-family batching preserves seed/family alignment: [nl_task.py:223](/home/bmarti44/stencil-llm/src/stencil/nl_task.py:223).
- Base’s query-time aux code is expected to be constant because the scored token is always `->`; its stateless source sees only that token. Chance aux is the correct control behavior.
- The aux head is absent from evaluation, while the learned injection remains present.
- Near construction and replay are empirically working: both held-out near evaluations reach 100%.

Severity: **No finding**.
