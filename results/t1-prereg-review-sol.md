codex
NOT CLEARED. The two rulings are defensible, but four HIGH registration gaps would materially change execution.

## R1 — runner-up skip is allowed

[PRESS-PLAN](/home/bmarti44/stencil-llm/PRESS-PLAN.md:154) says the runner-up “may” certify, not must. Do not spend a block merely to satisfy ceremony.

Narrow the rationale, though: raw-max is plausibly low-value, not proven to fail. Block D did not save raw scores or vector norms, so cosine failure does not establish that raw-max would also cross its `85,141` threshold. Record:

> `raw_max` SKIPPED/UNTESTED as a burden-test decision; it is not an empirical negative.

## HIGH — s0x2 needs a continuity/non-vacuity pretest

The uniform suffix does not leak obligation values and does not change dev/validation adherence scoring; those remain on ordinary S0. Requiring docstrings and annotations changes only whether the relevant syntactic moments occur. That is a reasonable fix.

But it also changes query states and candidate representations. A T1 pass on s0x2 would not directly demonstrate repair of the failure observed on s0x unless s0x2 demonstrably preserves that pressure.

During the train-hard collection, before training, score the frozen failed cosine policy offline on the same base-arm features and preregister:

- assertion-hit rate overall and per type;
- false-selection sessions under the frozen old policy;
- a minimum pressure gate showing the old policy still fails materially.

No extra generation is necessary. If s0x2 makes the old policy safe, it has removed the failure rather than enabled T1 to learn it. The uniform suffix is preferable to type-specific prompting or teacher-forced syntax, provided this control passes.

## HIGH — the existing trace lacks required training features

The draft calls 13.00M events “already collected,” but [t0_trace.py](/home/bmarti44/stencil-llm/scripts/t0_trace.py:82) stored query `h20`, old q/k scores and candidate metadata—not pooled 2048-dimensional candidate features or authoritative ledger spans.

A newly trained `k(cand)` cannot use those rows as written. Register one of:

- Recompute 13.00M prompt/candidate features with the pinned trunk and provenance spans; recommended.
- Drop the trace rows and train only on 13.12M, disclosed.
- Freeze the old candidate projection and train a materially different architecture.

Do not let implementation silently choose among these. If recomputed, pin the collector and data digest.

## HIGH — the objective does not train the measured boundary

The proposed margin only makes live candidates beat non-live candidates. Block D already established that ranking works. The open problem is candidate versus NULL.

Replace it with a decision-aligned margin in logit space:

```text
active:
  live >= max(NULL, strongest non-live candidate) + 0.1

inactive hard negative:
  NULL >= strongest candidate + 0.1
```

Skip the margin on no-candidate rows. Those rows produce a one-class softmax with zero loss and must not inflate NULL metrics.

Also freeze before implementation:

- q/k dimension and whether they warm-start from the pinned legacy heads;
- positive temperature parameterization and initialization;
- NULL-head initialization;
- argmax/tie behavior—NULL should win exact ties;
- Adam betas, epsilon, weight decay, shuffle seed and masking;
- action if any component gate fails.

Warm-starting q/k from the proven ranking heads and training q/k + NULL jointly is the mechanistically natural choice, but it must be registered.

## HIGH — gate denominators and block accounting need correction

“NULL accuracy ≥95%” is not coherent with the 5% session gate unless narrowly defined:

- Denominator must be inactive events with at least one same-type non-live candidate and no authoritative candidate.
- Report no-candidate structural abstentions separately.
- Add a calibration screen reporting sessions with any false selection. Event accuracy is not a safety bound: even 0/24 false sessions has one-sided U95 `11.73%`; sealed certification remains the proof.
- Retain the original positive-lookalike-margin gate from [PRESS-PLAN](/home/bmarti44/stencil-llm/PRESS-PLAN.md:278), or explicitly supersede it with the new decision-margin gate.

The exact trace-derived ceiling is `0.8328173374613003`, so the active-recall floor is:

```text
0.41640866873065013
```

It was never sealed-certified on block C. Either certify it as registered or, preferably under the burden test, explicitly retire that dependency and freeze `0.41640866873065013` as a trace-derived screening threshold—not a certified ceiling.

Finally, block B is untouched and was registered specifically for the first T1 policy at [PRESS-PLAN](/home/bmarti44/stencil-llm/PRESS-PLAN.md:112). Use:

- Block B: first trained T1 certification.
- Block E: preserve for the one registered retrained fallback.
- `13.30M+`: later fresh-policy extensions.

The proposed 13.12M training and 13.14M calibration ranges are otherwise disjoint from existing train/dev/validation/certification ranges.
