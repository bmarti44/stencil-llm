# Sol xhigh verification round 6 of the ledger runner (after fix round 5), 2026-09-01 — LAUNCH slice (falsification-only) AND full 909 cohort (confirmatory)

## Executed verification

Both round-5 constructions are now invalid:

- Selected-only Simpson reversal:
  - Coverage: 90.0277%
  - All-eligible text/base mean: −0.6601; lower bound −2.9484
  - Credited neural/base mean: −0.7151; lower bound −3.0052
  - Exact reasons:
    - `text_not_clustered_better_than_base_all_eligible`
    - `neural_not_clustered_better_than_base`

- Ineffective neural arm:
  - Base 0/909; text 5/909; neural 0/909
  - Text/base lower bound: +0.0359
  - NI upper bound: +1.0642
  - Neural/base lower bound: −0.1100
  - Exact sole reason: `neural_not_clustered_better_than_base`

The implementation correctly uses credited neural in [ledger_eval.py](/home/bmarti44/stencil-llm/scripts/ledger_eval.py:412). I grade that reading correct and conservative. In a new attack, raw neural obtained a +8.567-point lower bound entirely through unselected cells; credited neural’s lower bound was −0.0316, and the credited gate alone rejected the record.

No observed conversation-mean reversal can pass mathematically: each superiority lower bound is the observed mean minus nonnegative uncertainty and continuity terms. Therefore `lower_bound > 0` implies a positive observed conversation-unit mean. Likewise, the NI upper-bound gate implies the observed text-minus-neural mean is below 2 points.

## Gate strictness

The actual full cohort has 346 eligible conversations, not 909 eligible clusters. At `k=346`:

- Constant superiority effect must exceed 0.2890 points.
- Constant text-minus-neural drop must be below 1.7110 points.
- Five +100-point improving conversations with all others tied suffice.
- Twenty +8-point improving conversations with all others tied suffice.
- For +8 points in 208/346 conversations and neural exactly one point below text:
  - Text/base lower bound: +4.1724
  - Neural/base lower bound: +3.1724
  - NI upper bound: +1.2890
  - A complete 909-record consumer-path construction passed every gate.

Coverage is tight but attainable: the full preflight found 619/671 eligible constraints linkable, a 92.25% ceiling against the 90% gate. Passing requires selecting 604/619 linkable constraints, or 97.58%. An oracle top-2 reaches the ceiling; uniform model-free choices project 87.73% overall. This could produce a conservative no-result, but cannot create false confirmation.

## CPU evidence

- Full preflight: 909 conversations, 1,805 turns, 5,768 entries, 3,605 aged entries.
- Eligible: 671; linked: 619; coverage ceiling: 92.2504%.
- 6,459 control constructions; seven disclosed incomplete controls; zero errors.
- Focused tests: 64 passed, 2 GPU-dependent skipped.
- No GPU/model load, prohibited file access, signals, background commands, or repository writes.
- Worktree clean. `HEAD` advanced externally to `d8b3a1b`; only unrelated result artifacts were added, and the reviewed runner/tests are unchanged from `ea5ed6e`.

Explicit verdicts:

- **113 slice: LAUNCH — falsification-only screen.** It may reject NI or expose weak effects; it cannot establish NI.
- **Full 909 cohort: LAUNCH — fit for confirmatory use.** A claim is valid only if the actual run clears every gate, especially the tight 90% coverage gate.
