# W3 PREREGISTRATION — clean-format validation + focus observability
(draft for review; from Brian's rulings on the sealed result's
asterisks, 2026-08-30)

## W3a — clean-format validation (fixes the asterisk-1 confound)

New generator mode interference="s0c" (val-clean): for the held-out
type (prefix), EVERY sentence occurrence — user_set, user_update,
distractor, s0 notes, ledger serialization — renders in the UNSEEN
format (SENT_UNSEEN_FMT); the trained format appears NOWHERE in the
prompt. TDD as a pure function of seed; a registered assertion sweeps
each session's prompts for the trained-format string (zero occurrences
required, counted per session, failures reported not dropped).
Seeds: 13,600,000+i, i<96 (fresh; never referenced anywhere). Arms:
base, wave (w0-ce.pt UNCHANGED — no retraining, the point is
generalization of the frozen artifact), proxy, oracle, reinsertion;
feedback_mode=none; same PASS bars as the seal (headroom >= 0.10 else
inconclusive; closure >= 0.50; T0.3 validity; causal wave > proxy raw
gain with both valid); one attempt, fail-closed, pinned hashes, full
per-work records + full-length sha256 from the start (the seal's
evidence lesson). CLAIM if passed: true format generalization on the
prefix type. If failed: the rendering-robustness result stands as the
honest boundary.

## W3b — focus observability and override (the reframed W2, per Brian:
it is FOCUS, not memory, that must transplant and audit)

The wave's focus at any instant IS its field: where it points, how
hard. Two registered demonstrations on dev seeds (13,650,000+i, i<24;
no sealed block):
1. FOCUS READOUT (auditability): at every generation step, decode the
   wave's current focus as argmax-span of its field mapped to the
   ledger entry containing it (NULL if gain < 0.2). Registered metric:
   at parser-identified governed moments, readout-vs-governing-
   obligation accuracy >= 0.80; plus a full per-step focus trace
   artifact for 3 sessions (the "quick and easy audit" deliverable —
   a human-readable timeline of what the wave attends to).
2. FOCUS OVERRIDE (transplant-of-focus): externally impose a focus —
   replace the wave's field with a hand field pointing at a DIFFERENT
   live ledger entry at governed moments — and measure governance
   following the imposed focus: adherence to the imposed entry's rule
   at its moments rises >= 20 points over the wave's un-overridden
   rate on those moments, while un-overridden moments are unaffected
   (paired). This is the focus.set primitive demonstrated through the
   wave's own actuator: focus is inspectable, steerable, and carried
   by the field — no memory claim required.
Both use the frozen w0-ce.pt; no training anywhere in W3.

## Rules
TDD for the generator mode and readout; reviews before running (this
draft), at results, and at close; every number from committed
artifacts; the W3a attempt is one-shot, W3b is dev-only (repeatable
diagnostics, disclosed as such).

## v2 (sol round 1: 2 CRITICAL + 2 HIGH; all folded)

- s0c IMPLEMENTED for real (sol: the v1 name fell through — 255/255
  contaminated): ONE shared renderer used by every emitter (user_set,
  user_update, distractor, s0_note), the ledger serialization, and the
  visible_stale classifier; s0c = s0 scheduling + clean rendering.
  SCOPE: prefix only (SENT_UNSEEN_FMT has no doc/hint variants) —
  the claim is prefix-format generalization. Zero-occurrence assertion
  sweeps the trained prefix template across EVERY CODE_PREFIXES value.
  TDD: set/update/distractor/s0-note/compaction/stale-classification.
- W3a REBOUND to fresh seeds 13,700,000+i, i<96 (the 13.6M block was
  instantiated during review — exposure recorded in WORKLOG).
- W3b override REDESIGNED as COUNTER-AUTHORITY override (sol's
  design): at type-compatible governed moments, override the wave's
  field toward a visible conflicting s0 note carrying another value of
  the SAME type; measure adoption of that value vs the intact-wave
  paired rollout (identical seeds). Frozen: one intervention per
  paired rollout; eligible opportunity IDs from the intact trajectory;
  n >= 60 interventions; paired exact test (McNemar) at p < 0.05;
  parse/exec cost reported; non-target moments non-inferiority bound:
  adherence drop <= 2 counts total.
- Readout spec (frozen): i = first_argmax(field); decode = the unique
  ledger span containing i, else NULL; conditional WHERE accuracy at
  active governed moments scored on exact (type, value) identity; a
  separate WHEN/NULL confusion matrix over ALL steps incl.
  absent/cleared; NULL threshold selected ONCE on held W0 data
  (13,400,040..47) and frozen before the record run.
- W3b is ONE hash-pinned record run on 13,650,000..23 (exact reruns
  may verify reproducibility; any change requires fresh seeds); PASS
  gates apply to that record run only.
