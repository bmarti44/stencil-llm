# T1 PREREGISTRATION v2 — post checkpoint-iii reviews (2026-08-30)

v1 reviews: fable CLEARED conditional on the NULL-gate rewrite (its
arithmetic: 95% event-level implies 16-54 expected failed sessions of
160 — a gate-passing policy would predictably burn the block); sol NOT
CLEARED with 4 HIGH (s0x2 continuity pretest; trace rows lack candidate
features; objective must train candidate-vs-NULL; gate denominators +
block accounting). All folded below. Fable's h20 probe (grouped-CV AUC
0.995-0.999 active-vs-inactive on trace events) is cited as supportive
motivation only — it cannot confirm survival under lookalike
interference; that is what train-hard supplies.

## Rulings

R1. raw_max on a fresh block: SKIPPED/UNTESTED as a burden-test
decision — NOT an empirical negative (block D saved no raw scores; its
failure is established for cos_max only).

R2. Fixture amendment s0x2 (certification + train-hard/calib-hard
blocks): every work-turn task text appends "Include a one-line
docstring and type-annotate both arguments." Moment generation becomes
task-structural; obligation VALUES remain ledger-governed; the suffix
matches no CAND_PATTERN (verified) so it creates no pressable span.
Disclosures: feedback text can differ between s0x and s0x2 beyond the
suffix (nothing counted reads it); dev/val stay unextended.

R2-PRETEST (registered, before any training): score the FROZEN failed
cosine policy (threshold 0.6407741904258727) offline on the train-hard
base-arm features. Gates: (a) assertion-hit rate >= 80% of sessions
overall and >= 60% per target type (the s0x2 fix working); (b) the old
policy still false-selects in >= 20% of sessions (pressure preserved).
If (b) fails, s0x2 removed the failure rather than enabling T1 to learn
it — re-design the fixture before training.

## T1 frozen recipe

Data:
- train-hard: 13,120,000+i, i<48, s0x2, base-arm rollouts (one GPU
  collection pass; collector pinned; data digest recorded);
- calib-hard: 13,140,000+i, i<24, s0x2 (gates only);
- 13.00M trace rows: RECOMPUTED with the pinned trunk to add pooled
  candidate features + authoritative ledger spans (the stored rows lack
  both — sol HIGH; collector + digest pinned; same seeds, no new
  information).
Events: every timing-head fire. Labels are span-provenance: the live
candidate index iff the type is active AND its authoritative span is
among candidates; NULL otherwise. No-candidate rows carry no loss and
are excluded from every NULL metric (structural abstentions reported
separately).

Architecture (frozen): listwise softmax over [NULL, typed candidates];
candidate logit = cos(q(h20), k(cand)) / T with T = softplus(t), t
init 1.0; q/k are 64-d linear maps WARM-STARTED from the pinned legacy
Wq/Wk (registered choice); NULL logit = linear head on h20, zero-init.
Ties: NULL wins exact ties. Optimizer: Adam(lr=1e-3, betas 0.9/0.999,
eps 1e-8, no weight decay), 30 epochs, batch 256, shuffle generator
seed 0.

Loss: CE + decision-aligned hinge margins in LOGIT space (weight 1.0):
- active rows: logit(live) >= max(logit(NULL), strongest non-live
  candidate logit) + 0.1;
- inactive hard-negative rows: logit(NULL) >= strongest candidate
  logit + 0.1;
- no margin on no-candidate rows.
(The v1 live-vs-lookalike-only margin trained the solved boundary; this
trains the measured one — sol HIGH.)

Component gates on calib-hard (screens, NOT certification predictors —
even 0/24 clean sessions bounds only U95 = 11.7%; the sealed job is the
proof):
- conditional address >= 90% on active events (span-provenance);
- active recall >= 0.4164 (= 0.5 * trace-derived R_ceil
  0.8328173374613003; the ceiling was never sealed-certified on block C
  — that dependency is RETIRED under the burden test; 0.4164 is frozen
  as a trace-derived screening threshold, not a certified ceiling);
- ZERO NULL errors, session-stated: 0 of 24 calib-hard sessions may
  contain an above-threshold non-NULL selection at an inactive-type
  moment, where the NULL denominator is inactive events WITH >= 1
  same-type non-live candidate and NO authoritative candidate;
- the decision-margin gate: positive registered margins on >= 90% of
  active rows AND >= 90% of inactive hard-negative rows (supersedes the
  v1 lookalike-margin gate — explicit supersession, sol HIGH).
Action if any gate fails: the trained policy is NOT certified; one
registered fallback retrain (the plan's hard-negative-reweight, 4x on
inactive hard-negative rows), re-gated once; a second failure closes
the line.

Certification: ONE sealed fail-closed job on BLOCK B (13,070,000 —
registered for the first T1 policy all along; sol correction), s0x2,
N=160, provenance-by-span semantics, policy named in WORKLOG before
touching. BLOCK E is preserved for the one registered fallback
retrain's certification. 13,300,000+ extensions thereafter (one policy
per block).

PASS -> behavioral dev replay (13.10M, s0 unextended) under the
registered T1 decision table. FAIL (after the fallback path) -> the
discriminative line CLOSES; autonomous hopes ride on T2/T3.

## Unchanged
T0.3 validity rule; T0.4/T0.5 rungs; dev/val seeds; all G0 amendments
not explicitly superseded above.
