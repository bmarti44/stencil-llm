# Implementation review: is the scoped-instruction instrument sound enough to spend GPU on?

You are reviewing the Stencil repository at /home/bmarti44/stencil-llm as an
independent adversarial reviewer. Use MAXIMUM reasoning effort.

**Do not read anything under `data/bench/`.** It holds evaluation benchmarks and
recorded responses; reading it would contaminate the work.

Write ONLY this review file. Do not edit code. Launch no GPU work: GPU use is
paused by the repository owner's standing instruction, and nothing you recommend
may assume it is lifted.

## What happened since your last review

You wrote `results/reviews/2026-09-13-a-screen-forward-astra.md`, which
recommended **scoped instruction compilation** at a 28% artifact-success forecast
— the first direction above the owner's 25% bar — and specified a first week.
Read that review first; its findings stand and you should not re-derive them.

Steps 1 and 2 of your first week are now built, on CPU, with no GPU spend:

- `results/scoped/SEMANTICS.md` — the frozen semantics the oracle implements
- `src/stencil/scoped_blocks.py` — resolver, project builder, renderer, the
  four-suite executable oracle, the shortcut and rival policies, the reminder
  renderer and the prompt builder
- `src/stencil/scoped_dev_blocks.py` — the 16 development blocks
- `scripts/scoped_gate.py` — the step-1 construction gate (writes
  `results/scoped/GATE.json`)
- `scripts/scoped_rescue.py`, `scripts/scoped_score_one.py` — the step-3 runner
  and its separate-process scorer
- `results/scoped/STEP1.md` — the step-1 result
- `results/scoped/RESCUE-REGISTRATION.md` — the step-2 registration
- `tests/test_scoped_blocks.py`, `tests/test_scoped_rescue.py` — 74 tests

Reproduce with `uv run python scripts/scoped_gate.py` and
`uv run pytest -q tests/test_scoped_blocks.py tests/test_scoped_rescue.py`.

## The standard

The bar is **25% on your artifact-success forecast**, using the definition you
have been using. The owner's goal is one published HuggingFace model artifact
that keeps focus on relevant instructions over a long-horizon agentic coding
session, proven against the same artifact with the modification off.

Your step-1 gate was: *"gold and valid alternatives pass; every shortcut fails
its designated contrasts; source metadata cannot reach the automatic arm. Failure
here means repair the fixture before freezing it, not experiment on the model."*
The gate reports PASS. **Your job is to find out whether that PASS is real.**

## The questions, in priority order

1. **Is the PASS earned or hollow?** The five trivial policies are defeated
   16/16, which the write-up itself calls cheap evidence because any scope-blind
   policy loses a block whose two cases need different values. Two scope-aware
   rivals were added for anti-vacuity (`scoped_recency` fails 4/16,
   `cancel_revives` fails 2/16). Is that enough? Name any policy — trivial or
   sophisticated — that would pass the gate while being obviously wrong, and say
   which block would have to change to defeat it.

2. **Is the executable oracle sound?** Four suites: functional, contract,
   preservation, obligation. It observes behaviour by running the code rather
   than reading it. Find a wrong implementation it would accept, or a correct one
   it would reject. Pay attention to `observe()`, to the `preservation` suite's
   use of the block's `precedent`, and to the obligation check.

3. **Does the oracle arm leak more than an instruction?** The reminder quotes the
   source message verbatim with its number. Is quoting the *winning* statement
   already a covert answer key — and if so, is that acceptable for a diagnostic
   that explicitly cannot ship, or does it make the rescue result uninterpretable?

4. **Is the registered limitation complete?** The registration records that these
   histories fit entirely in the budget, so the reminder is additive (23–68
   tokens) rather than displacing, and that the diagnostic therefore measures
   resolution rather than retrieval. What else about this design will be
   embarrassing in the write-up, and should be recorded now rather than found
   later?

5. **Are the budget and stop rules right?** Prompts are 150–303 tokens and
   `max_new_tokens` is 160. Your estimate was 0.2–0.3 GPU-hours for 64
   generations. Check that arithmetic against a 4B trunk and say what the pilot
   must measure for the launch to be honest.

6. **Does the semantics specification hold up?** `SEMANTICS.md` defines cancel as
   non-reviving, reinstatement as the only route back, obligations with
   independent support, and a `default` package baseline chosen so non-revival
   and revival land on different values. Is any of it wrong, ambiguous, or
   unrepresentative of how instructions actually change in a coding session?

7. **Does your 28% forecast move?** Up, down, or unchanged, and why. If the
   instrument is sound, does that alone change anything?

## Constraints on your answer

Adopt-only-if-it-adds-nothing rule: a recommendation that adds an arm, a model, a
benchmark, or a review stage will be declined. Prefer recommendations that delete
or repair. If you believe the whole direction should stop, say so plainly.

Grade every finding low / medium / high / critical. Acceptance blocks on open
high and critical findings.

## Output

Write the review to this file's sibling
`results/reviews/2026-09-13-scoped-instrument-astra.md`, ending with a single
line:

`VERDICT — <SOUND|REPAIR|STOP> — <n>% artifact-success forecast — <one sentence>`
