---
base_model: Qwen/Qwen3-1.7B
library_name: transformers
license: apache-2.0
tags:
  - qwen3
  - instruction-following
  - attention-steering
  - stencil
---

# stencil-wave add-on for Qwen/Qwen3-1.7B

An **add-on** (not a fine-tune) for `Qwen/Qwen3-1.7B` at revision
`70d244cc86ccca08cf5af4e1e306ecf908b1ad5e`. It contains:

- `controller.safetensors` — 264,321 parameters: a selector (`W_q`, `W_k`:
  2048->64) that reads the residual stream entering layer 20 and scores
  ledger entries against the current position; a gain head (`w_g`) that the
  ledger path does not use.
- `salience_weights.json` — a 19-feature logistic regression over
  linguistic cues that decides whether a user-turn sentence states a
  persistent output requirement.
- `config.json` — pins and the actuation constants.

Used through the `stencil-wave` Python package (`WaveModel`), which loads
the unmodified trunk from `Qwen/Qwen3-1.7B` with `transformers==4.51.0`.

## What it does

At generation time, for the user turns of the conversation:

1. **Detect**: split each user turn into sentences and keep those the
   salience classifier calls instructions (precision ~0.92-0.96, recall
   ~0.75 on hand-labeled Multi-IF sentences: it is under-inclusive and
   misses constraints buried inside task sentences).
2. **Hold**: entries stated in an earlier turn are held (the configuration
   that was evaluated); each entry's key is the mean layer-20 residual over
   its tokens.
3. **Select**: the controller scores held entries against the prompt's
   final layer-20 state; the top-2 are selected once, at prefill.
4. **Amplify**: an additive pre-softmax attention bias of +3.0 is added to
   the selected entries' key columns at layers 20-27 for every generated
   token. No text is added to the context (zero added tokens).

With no held entries, or with the ledger turned off, generation is bitwise
what `transformers` produces.

## What it does NOT do

- It is an **insertion-only actuator**: it can make the model attend to an
  instruction, which helps when the fix is to *include* something. It has
  no mechanism for limits, removals, or restructuring ("under 90 words",
  "no commas", "as JSON") beyond whatever extra attention happens to do.
  Those families are reported separately in the research program and are
  excluded from its primary endpoint.
- It only works with **Qwen3-1.7B at the pinned revision**: the controller
  reads that model's layer-20 residual stream and its weights are specific
  to it.
- The registered evaluation (non-inferiority of this neural ledger to
  re-appending the same instructions as text, on Multi-IF, at zero context
  cost) is **not complete**; nothing here claims a benchmark result.
- The salience classifier scans **user** turns only; system prompts and
  assistant turns are not read.
- Greedy decoding only; batch size 1.

## Provenance

Controller: research checkpoint `results/qwen/b3-ce-s0.pt` (INTERNAL-WAVE
v3.1 selection A2, trained with a cross-entropy objective on synthetic
constraint-following data), converted bitwise. Salience: refit-deterministic
logistic regression, `src/stencil/salience_weights.json`. Parity of the
packaged path against the research path is recorded in the package's
`parity.json`.
