# Check 44b — pre-written reading (2026-09-06)

Fit-on = committed kimi-admission.jsonl with all 53 Opus label replacements,
plus 231 opus-admission-enrich messages. Evaluated-on = committed
fable-admission-heldout-2.jsonl, once after model/threshold freeze; disjoint.
The old Fable bank, sealed inputs and data/bench are forbidden inputs.
The v8 SETUP bank is a development diagnostic only, never fitting/calibration.

C: base BAAI/bge-small-en-v1.5 revision
5c38ec7c405ec4b44b94cc5a9bb96e735b38267a, fully fine-tuned binary span head.
Use the unchanged src/stencil/focus3.py sentences splitter. Segment A is
[role] plus the whole message; B is the exact candidate sentence. No historical
context. Identical pairing in fit, calibration and inference. A candidate is
positive iff it overlaps a gold standing-rule span. Max 512 tokens, no truncation;
overflow candidates abstain and remain in evaluation denominators. Explicit
non-user role guard. No scope/key prediction or auxiliary flags in this check;
the optional auxiliary heads are omitted to isolate the span task.

No author scenario IDs exist. Conservative grouping = whole domain across both
authors, preserving source batches and matched quote pairs. Shuffle the sorted
20 domains with Python Random(0); reserve first 2 (10% of groups) for DEV, with
actual message fraction reported. Same partition for seeds 0/1/2; seed 0 designated
before fitting, no seed/checkpoint selection. Retain every patched message as a
positive/negative example: patch drop=true means remove the invalid rule, using
new_standing_rules, consistent with the review's audited after-counts.

Recipe: three epochs per seed, batch 32, AdamW lr 3e-5, weight decay .01,
dropout .1, gradient clipping 1, 6% linear warmup then linear decay, fp32.
No class weighting, early stopping or hyperparameter search. CPU DEV probabilities
calibrate each final checkpoint. Choose the lowest probability threshold (>=)
meeting <=2% false-admission messages among gold-empty DEV messages; monotonicity
makes this maximize one-to-one overlap recall. Equally good higher thresholds
are not preferred. Include an above-1 abstain threshold. Freeze all thresholds
and weight hashes before any held-out contents are opened.

GO requires seed-0 C held-out overlap recall >=85% micro, payload false admissions
<=3%, quoted false admissions <=3%, and zero on non-user roles (each family must
have support), AND <=2/96 v8 SETUP turns with any unmatched admitted span. This
counts false admissions even on turns also containing true rules. SETUP admit
and supersedes events supply positive standing-rule spans; cancel/complete
events do not. Also report
request-template-specific false admissions. GO registers C's runtime replacement
and authorizes v9; otherwise NO-GO, first ship remains explicit structured rule
entry with C only an assistive suggester. No v9 execution is included here.
Report exact/overlap span micro P/R, positive-message macro R and predicted-message
macro P, binary message P/R, check44 negative-family point rates and one-sided95%
Clopper-Pearson upper bounds. Bounds describe independent messages, not population
certification; macro and span representability cannot replace the micro GO bar.
B is unchanged ft-v3 seed0 at .95, with check44's pairing/role/overflow behavior.
Both arms run on CPU (4 threads), once per held-out and SETUP message; latency
excludes loading, reports warm p50/p95 and all-message distributions. No replay
inference for auditing; recompute solely from saved records.

Cap: 3600 cumulative GPU allocation seconds including pilot/loading/saving;
cooperative deadline checks, foreground only, no signals. Check other Stencil
RUNNING.flag files and compute processes, tolerate Brian's llama-server. Claim
own flag atomically, remove only own flag on natural exit. The first 10 training updates of seed 0 are the training-only pilot, which estimates total cost before the seed matrix. No changes
in response to held-out scores. Wait for heldout-2 commit, polling at 5-minute
intervals. All artifacts committed with explicit paths; weights stay local; no push.
