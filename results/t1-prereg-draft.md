# T1 PREREGISTRATION — draft for checkpoint-iii review (2026-08-30)

Context: block-D certification FAILED (k=149/160; results/qwen/
g0-certify-D.json). All 88 false-selection events were value-wrong at
inactive-type moments — absolute-score liveness detection fails when the
live sentence is absent (ranking-only discrimination). 79 sessions
failed non-vacuity (doc 53/hint 22/prefix 4): with the target obligation
cleared, the model often does not generate that moment class.

## Rulings requested

R1. SKIP the runner-up certification (raw_max on block E). Its
discrimination is also ranking-only (counterfeit hard-AUPRC 0.9977 was
measured with the same flawed counterfeit instrument; its threshold was
likewise selected without real hard negatives). Predictable failure;
burden test says do not spend the last reserve block on it. Block E is
preserved for the trained T1 policy.

R2. Fixture generator amendment "s0x2" (certification blocks only):
every work-turn task text appends "Include a one-line docstring and
type-annotate both arguments." — moment generation becomes
task-structural (the model produces doc/hint moments regardless of
ledger state), fixing the doc/hint assertion-miss mode; obligation
VALUES remain governed solely by the ledger. Non-vacuity assertion
unchanged. TDD as a pure function of seed. Dev/val stay unextended
(unchanged from G0 amendments).

## T1 frozen recipe (the registered training rung, now with real
hard negatives — the G0 amendment's requirement)

Data (new registered blocks; recorded before touching):
- train-hard: 13,120,000+i, i<48, s0x2, base-arm rollouts;
- calib-hard: 13,140,000+i, i<24, s0x2 (component gates only);
- plus the existing 13.00M s0 trace events (active-rich, already
  collected) as additional training rows.
Events: every timing-head fire. Per event: h20 state, typed candidate
set (pred_type restriction retained), pooled candidate features.
Labels: the live-of-type candidate index when the type is active and
its authoritative span is among candidates (span-provenance labels, NOT
value labels); NULL otherwise (inactive type, no candidates, or
live-span absent).

Architecture: listwise softmax over [NULL, cand_1..cand_n(typed)];
candidate logits = cos(q(h20), k(cand)) / learned temperature; NULL
logit = linear null head on h20. Init seed 0.

Loss: CE + margin term (live beats best same-type non-live by >= 0.1
cosine, hinge, weight 1.0). Adam 1e-3, 30 epochs, batch 256. Frozen.

Component gates on calib-hard (before any sealed or behavioral run):
- conditional address (active events, span-provenance) >= 90%;
- active recall >= 0.5 * R_ceil (R_ceil = 0.833 from G0);
- NULL accuracy at inactive-type fire moments >= 95%.

Then ONE sealed certification on block E (s0x2, N=160, fail-closed job,
same provenance-by-span semantics; policy named in WORKLOG before
touching). PASS (U95 <= 5%) -> behavioral dev replay (13.10M, s0
unextended) under the registered T1 decision table. FAIL -> the
discriminative line CLOSES (honest negative; no further certification
attempts) and the program's autonomous hopes ride on T2/T3.

Certification accounting: E is the last reserve; extension block
13,300,000+i, i<160 registered now (one policy per block, sealed jobs
only).

## Unchanged
T0.3 validity rule and constants; T0.4/T0.5 rungs (queued); dev/val
seeds; all G0 amendments not superseded above.
