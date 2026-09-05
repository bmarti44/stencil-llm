# Quick check 38 — role, recency, and few-shot pattern

Unregistered, disclosed quick check, 2026-09-05; seed 38038; Qwen3-4B,
bf16, hf_compatible, thinking disabled, greedy, 48-token cap per request.
Foreground only, cooperative 15 GPU-minute cap; abort if GPU busy; no signals.
Lineage: fit-on=none; evaluated-on=the 32 recorded check-36/check-35 S1 synthetic
histories and SWITCH/BACK lists. No fitting, training, selection, or benchmark
inputs/responses; sealed IFEval and BFCL contents are not accessed.

## Reading fixed before running

All arms use plain text prefills with fresh contiguous caches, no cache surgery.
A = ascending; B = descending. SWITCH/BACK use the recorded list requests,
with no sorting cue inside the request itself. Preserve exact recorded token IDs
for neutral context, filler, requests, and prior answers wherever retained.

- T1 (role): move the cue to a first USER message before the recorded exchanges;
  old system contains only format instruction and neutral context. Keep A answers.
- T2 (pattern off, clean): old system-slot cue; delete SET and HOLD user/assistant
  exchanges as whole turns, retain the intervening neutral filler user turn.
- T3 (pattern only): remove the old cue entirely; keep the recorded A exchanges.
- T4 (recency at fixed role): no old cue; cue in a separate USER message immediately
  before the current request; keep A answers.
- R3 replicate: replace the old system-slot cue and retain A exchanges; expected
  SWITCH B=2/32. Compare token outputs with check-36 R3, not just counts.

Source correction: despite the request/review saying three prior A exchanges,
check-36 histories contain exactly TWO (SET, HOLD). Reuse those exact histories;
no third demonstration is invented. Some recorded answers need not be correct A.
BACK uses each arm's actual SWITCH exchange and cue A in the same placement
(T4 immediately before BACK, replacing the prior cue event). T3 has no SWITCH
placement, so its BACK A cue uses the old system slot (same as R3/T2).
T2 BACK retains the generated SWITCH exchange; its no-A-information default
measurement is SWITCH only.

Fixed reading, on SWITCH value-exact counts, combinations allowed:
ROLE if T1 B - R3 B >= 12/32; PATTERN if T3 A >= 24/32 AND T2 B >= 24/32;
RECENCY if T4 B - T1 B >= 12/32. These are descriptive diagnostic thresholds,
not registered statistical existence tests or exclusive mechanistic claims.
Report each constituent proportion with a 95% Wilson interval; differences
also get a conservative >=95% Wilson-based interval (subtract marginal 97.5%
Wilson bounds, Bonferroni), plus paired gain/loss counts. Wilson intervals are
for proportions, not directly for paired differences; no independence assumed.
Report ascending default prior = T2 SWITCH A/32, where no A cue/answer exists
but B is explicitly cued; this is not an unconditional cue-free baseline.

Report A/B/copy/other and breakage per arm/step for value-exact and strict JSON
scoring; breakage overlaps outcome labels. All raw prompts, outputs, token IDs,
source hashes and the immutable prewritten reading are saved with the run.
