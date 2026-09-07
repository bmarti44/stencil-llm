# Day 5b for gpt-6-astra: CPU amendment + RE-PILOT with grouped_mm (2026-09-06)

Fable's pilot review results/composition-pilot-review-fable.md (read fully) found: the envelope failure is an
INTERFACE defect (system prompt never names `report` as an object/keys; parser zero-tolerance; 101/101 replies use
the same two deltas; under a tolerant mapping 95-117/128 would execute; all 101 parseable replies contain the right
function and pass DEV-00's public+hidden cases); T truncation is reply inflation after a leaked JSON error text;
10.8 tok/s is expected for experts_implementation="eager" (launch-bound), grouped_mm is the cheapest fix (needed
speed-up 1.84x); batch non-invariance is expected bf16 padded numerics — drop batch4.
PART 1 (CPU; one registered amendment in the pilot README, written BEFORE any code change):
 a. slab.py system prompt: add a literal envelope example and name the `report` object keys.
 b. Parser: register exactly two tolerances (extra `path` on `test`; lift top-level status/task/delivery into
    `report`), journal every tolerance applied; Python-literal fallback (True/False) and single stray-bracket repair
    only if you register them too; make the envelope error informative and never leak json-module text to the model.
 c. Re-score DEV-00 from the existing records on CPU under the amended parser: report executed calls, final success,
    per-kind violations (fable: all 101 ignore indent=3; N misreports delivery) — as the pilot's recovered outcomes.
 d. Do NOT change renderer layout (frozen golden), T obligation text, the 512 cap, or the 100-300 band.
 e. Config: experts_implementation="grouped_mm" for the trunk; keep eager as the fallback flag.
 Tests: parser tolerances (positive + negative), prompt example presence, re-score reproduction. Commit with explicit
 pathspecs (src/stencil/focus/**, tests/test_focus_*.py, fixtures, results/quick-checks/composition-pilot/ amendment).
PART 2 (GPU; RUNNING.flag; one load; cap 2.0 GPU-h; never signal):
 1. grouped_mm parity gate: replay the 64 frozen sequential R/N/T/O prompts of DEV-00 greedy under grouped_mm and
    byte-compare token ids to the frozen records (report divergence count; a divergence-free gate or a disclosed
    <= 1/64 first-divergence position analysis is required to proceed; else STOP and report).
 2. Re-pilot: DEV episodes in the frozen order 00,01,06,07,02,03,04,05 (both lengths), arms R/N/T (O = R under gold
    events; run O only if time remains), sequential, amended parser; journal everything as before including the
    hidden states for check 45 (layers 8,16,24,32,40; last-prompt-token and generated-mean).
 3. Report: tok/s, seconds/call, truncation, executed calls, competence (final success), relapse per kind with
    executed-trait denominators, max context, the DEV mask trigger check, and the COST PROJECTION for R/N x64 +
    O/T x16 against 12 GPU-h with the measured grouped_mm numbers (no batching credit).
 Pre-written readings: ELIGIBLE (projection <= 12 h; truncation <= 2%; executed-call rate >= 90%; nonzero
 executed-trait relapse denominators in >= 2 episodes) / INELIGIBLE with the failing item / INCOMPLETE.
Outputs: results/quick-checks/composition-pilot-2/ (README, records, renderer check against the frozen golden,
hidden/ out of git with manifest hashes); item in results/quick-checks/README.md; WORKLOG (<= 6 lines). Commit with
explicit pathspecs; no push; never read anything under data/bench; DEV episodes only.
