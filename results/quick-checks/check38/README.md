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

## Results

Complete: 8.02/15 GPU-min including model load; 320 records. Pilot projected 8.94 minutes; peak CUDA allocation 7.84 GiB.
Source contains two prior exchanges, with 60/64 exact A answers and four other outputs, all retained unchanged where specified.

All counts are out of 32. Copy means exact input order; strict other also includes otherwise correct arrays wrapped in extra brackets or other non-JSON formatting.

| Arm | Step | Value A | B | Copy | Other | Strict A | B | Copy | Other | Breakage |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| T1 | SWITCH | 31 | 1 | 0 | 0 | 31 | 1 | 0 | 0 | 0 |
| T1 | BACK | 32 | 0 | 0 | 0 | 32 | 0 | 0 | 0 | 0 |
| T2 | SWITCH | 12 | 12 | 5 | 3 | 11 | 12 | 5 | 4 | 0 |
| T2 | BACK | 23 | 3 | 2 | 4 | 22 | 3 | 2 | 5 | 0 |
| T3 | SWITCH | 31 | 0 | 0 | 1 | 31 | 0 | 0 | 1 | 0 |
| T3 | BACK | 32 | 0 | 0 | 0 | 32 | 0 | 0 | 0 | 0 |
| T4 | SWITCH | 18 | 11 | 0 | 3 | 18 | 11 | 0 | 3 | 0 |
| T4 | BACK | 30 | 0 | 0 | 2 | 30 | 0 | 0 | 2 | 1 |
| R3 | SWITCH | 29 | 2 | 1 | 0 | 29 | 2 | 1 | 0 | 0 |
| R3 | BACK | 32 | 0 | 0 | 0 | 32 | 0 | 0 | 0 | 0 |

All category and breakage proportions, for both scoring methods, have 95% Wilson intervals in [summary.json](4b/summary.json). Constituent intervals below are 95% Wilson; difference intervals use the prewritten conservative Wilson-bound subtraction.

| Reading | SWITCH proportions (95% Wilson) | Difference (count; percentage points; conservative ≥95% interval) | Fixed threshold met? |
|---|---|---|---|
| ROLE | T1 B 1/32 ([0.6%, 15.7%]); R3 B 2/32 ([1.7%, 20.1%]) | -1; -3.1 pp; [-22.4, 17.0] pp | NO |
| PATTERN | T3 A 31/32 ([84.3%, 99.4%]); T2 B 12/32 ([22.9%, 54.7%]) | Both must reach 24/32 | NO |
| RECENCY | T4 B 11/32 ([20.4%, 51.7%]); T1 B 1/32 ([0.6%, 15.7%]) | +10; +31.2 pp; [0.4, 53.7] pp | NO |

Paired B gains/losses: ROLE 0/1; RECENCY 10/0.
Ascending default prior, T2 SWITCH A with no A information: **12/32 ([22.9%, 54.7%])**. B is explicitly cued here, so this measures ascending behavior despite B, not a pure cue-free prior.
R3 replicate matches **64/64** recorded check-36 SWITCH/BACK token outputs, including EOS.

## Plain-language conclusion

**Fixed reading: NONE of the three fixed thresholds met.** Moving the old instruction into a user message produced 1/32 descending answers versus 2/32 in the system slot. Moving that user cue immediately before the request produced 11/32. Removing the prior exchanges cleanly produced 12/32 descending answers and 12/32 ascending answers despite the descending instruction. With the prior exchanges and no cue, 31/32 answers were ascending. The cue-free pattern result alone cannot distinguish imitation from an ascending default. The three labels follow the fixed magnitude thresholds; failing a threshold does not establish that its factor has no effect. Role changes necessarily change chat framing/token positions, and the recency comparison applies to a separate user cue, not a cue inside the list request.

BACK recovered A in 32/32 for T1, T3 and R3, 23/32 for T2, and 30/32 for T4. T4 BACK had the only breakage: episode 24 repeated -2. The recency gain is positive in the reported conservative interval but falls two successes short of the fixed 12/32 threshold.

Validation: independent raw-record audit checked all 320 prefills, BACK continuations, value/strict scores and breakage flags; all source hashes, reading hash and Wilson intervals verified. CPU layout/decoder checks and lint passed; import-side-effect regression checks: 3 passed, 1 expected failure. [Audit](4b/audit.json), [records](4b/records.jsonl), [immutable prewritten reading](4b/prewritten-reading.md). No fitting, training, sealed-input access, signals, background run, or push.

**Correction (astra full review, 2026-09-05)**: (F2) Check38’s T1/T4 cue events and inherited filler are unanswered consecutive user turns. Role, recency, turn structure and prior demonstrations were not isolated. The 19/32 “decay” plus 10/32 “answers” comparison is not an identified additive decomposition: it compares different lists/histories across checks. The paired T2/R3 contrast does not identify the cause of the whole deficit.
