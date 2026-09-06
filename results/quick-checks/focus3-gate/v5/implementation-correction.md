# Pre-written implementation correction before saved-probability replay

The one CPU classifier inference run at registration commit 1780f5b9 produced
33/36 admissions, 8/12 transitions and 13 unauthorized actions. Full records,
model probabilities, audit, source snapshots and original freeze are preserved
under implementation-diagnostic/. This is implementation evidence, not a second
arm or changed operating point.

The task-switch guard incorrectly inspected the full admission span including
harness payload text. Bare `Work on task X;` prose therefore failed the anchored
switch match, and a high P(rule) on the concatenated payload/request was borrowed
for four reinstatements and seven task-switch admissions. This violates ruling
3's task-switch semantics. Fix task_switch_only to inspect the same prose prefix
that relation pairing uses; preserve admission model inputs and every score.

Recompute runtime state with the SAME saved per-turn probabilities, asserting
identical pair inputs and admission inputs on every turn; if the corrected
trajectory needs an unseen input, fail loudly, never infer or synthesize a score.
No new classifier inference, fitting, threshold changes, bank edits or GPU work.
Task switches occur at the final turn for these 11 changes, so earlier scoring
inputs are expected to remain identical. Keep the global overlap none guard and
quoted-text behavior unchanged; report remaining errors and stop after step A.
