# Composition DEV pilot — INELIGIBLE / INCOMPLETE

**Do not launch the larger test under this recipe.** The measured sequential
projection is **20.794 GPU-h >12** even using only the completed short episode;
truncation is **10/64 =15.625% >2%**. Batch4 fails byte invariance and its interrupted
observed-prefix cost already gives a **49.583 GPU-h** proxy lower bound assuming four occupied lanes. Only DEV-00 completed in sequential R/N/T/O. DEV-01–07 and GPU validation
of the 32-round shape are **unrun**, not passing or replaced cases.

Fit/train-on none; development-on authored SLAB DEV only, with gold structured
events used for explicit R **only in DEV**. O has the same gold event/renderer path:
R/O outputs match on all 16 rounds, not an independent perception measurement.
No evaluation episode or data/bench content was opened. No signals, termination,
second model load or push. Actuator OFF throughout (40k R3 HARM;40l diagnostic).
The local custom-generation package remains a scaffold, not a complete HF snapshot.

Preflight freeze **d1fb0660**: [Fable r2](../../slab-bank-review-fable-r2.md) closes
H1–H4; the bank-fix WORKLOG and re-frozen manifests were checked. N1 was repaired
against the last parsable snapshot in both attempted/executed replacement scoring,
with a red→green DEV regression and a true-new-stale positive control. All original
DEV episodes were 16 rounds: DEV06/07 were made 32 rounds, with DEV-only reinstatement at 26,
before outcomes. Evaluation manifest hashes/accounting were preserved without
regenerating evaluation content. CPU reference accounting becomes 13.637h including
the enlarged DEV bank; it is not a measured GPU cost. CPU actual-HF-dispatch stub
preflight: 448 calls, including both lengths and threaded batch4, all checked.

The [prewritten recipe](prewritten.md) froze order 00,01,06,07,02,03,04,05, with
00/01/06/07 as the four-domain/two-length fallback. The runner completed the frozen
full-episode batch replay after its first-round mismatch; all that diagnostic cost
is charged. It then selected sequential fallback, but no further episode fit the
cooperative deadline. No N history, body cap or episode was silently shortened.
All 64 batch calls have records, but the last T reply was deadline-interrupted at343
body tokens; that comparison is not treated as a completed full-cost measurement.
The raw episode receipt counts all scheduled rows as `complete`; this report also
checks `deadline_hit` and therefore marks the batch execution/cost incomplete.

One Qwen3-30B-A3B HF bf16 load, SDPA/eager MoE, greedy, cap 512 including EOS, frozen
system prompt, real sandbox Executor, and actual retained KV through
`model.generate(custom_generate=models/stencil-package, decoder=RetainedDecoder)`.
`paired_context_gate` preceded every arm render, using conservative bounds with
actual<=bound assertions. Every live view matches DEV gold. No context rejection
or loop failure. Batch padding uses independent key masks/logical positions.
This measures this particular batch adapter; it does not rule out other backends.

| Sequential arm, DEV-00 | Own-body tokens min/median/max | In100–300 | First10 in band | Max prompt | Truncated | Mean seconds per generate call |
|---|---:|---:|---:|---:|---:|---:|
| R |197/197/198|16/16|10/10|11,050|0/16|19.576|
| N |202/202/204|16/16|10/10|5,394|0/16|19.030|
| T |192/512/512|2/16|2/10|9,727|10/16|42.009|
| O |197/197/198|16/16|10/10|11,050|0/16|19.382|

Across **all 128 calls**, max prompt R/N/T/O =11,050/7,144/10,224/11,050.
Global max plus 512 reserve =11,562 <=32,768 (21,206-token margin). Max padded
physical cache =15,807 positions. These are short-episode observations, **not a
GPU 32-round fit certificate**. R meets the observed token-band condition, but the
fixed four-episode pressure assessment is incomplete and no edits executed.

| Episode/arm | Final success | Any stale execution | Wrong-skill checker flag | Any breakage | Executed batches |
|---|---:|---:|---:|---:|---:|
| DEV-00 R |0/1|0/1|0/1|1/1|0/16|
| DEV-00 N |0/1|0/1|0/1|1/1|0/16|
| DEV-00 T |0/1|0/1|0/1|1/1|0/16|
| DEV-00 O |0/1|0/1|0/1|1/1|0/16|

All 128 envelopes were rejected before a tool call executed. A typical reply puts
`status` beside `calls` instead of inside required `report`, and adds an unsupported
`path` to `test`. The model emits current function code, but this interface did not
establish executable competence. The frozen checker exits early on a missing report:
zero style/process/wrong-skill flags there **do not establish compliance**. The
batch diagnostic also has breakage in every arm, no executed batches and no stale
execution; its final T output is incomplete. Exact per-round outcomes remain saved.
A CPU interface/checker redesign would need a new pre-evaluation freeze/amendment;
no prompt, schema, renderer or scorer was rescued after seeing these outputs.

| Kind: scored relapse / scheduled opportunities | R | N | T | O | Opportunities with a previously executed trait, each arm |
|---|---:|---:|---:|---:|---:|
| Language |0/0|0/0|0/0|0/0|0|
| Style |0/5|0/5|0/5|0/5|0|
| Format |0/4|0/4|0/4|0/4|0|
| Process |0/6|0/6|0/6|0/6|0|

Language is zero-by-design: Python stays live and is never retired. Scheduled
style/format/process denominators are nonzero, but **measurable executed-relapse
pressure was not established**; these zeros are not clean-retention evidence.
DEV mask trigger **NOT MET**: 0 relapse, at most 6 opportunities/kind (<20), only 1
episode (<2), and no previously executed trait. No mask screen or actuator enabled.

| Measured mode | Episode wall seconds | Prefill tokens / seconds / tok-s | Decode-forward tokens / seconds / tok-s |
|---|---:|---:|---:|
| Sequential, complete |1,601.766|21,664 /58.295 /371.629|16,668 /1,539.544 /10.827|
| Batch4, interrupted |3,455.803|21,623 /31.803 /679.901|18,887 /3,422.151 /5.519|

Batch N and T differ from sequential on **all 16 rounds**, starting on identical
round-0 inputs; R and O match16/16. These are subsequently divergent workloads,
not an identical-output speed comparison. Batch timings are counted once per
aligned round. Per-call time excludes the subsequent journal/checker callback;
episode cost includes those waits and preparation overhead, allocated evenly to
sequential arms. All literal tokens, per-call timing and execution timing are in
[records.jsonl](records.jsonl). GPU-held wall **5,385.346/5,400 s =1.49593h**, including
load **322.758s**, callbacks and cleanup; peak CUDA allocation 68,460,523,520 bytes.
RUNNING.flag was removed and the process exited normally. No additional work fit.

| Projection, including actual pilot + measured-load reload allowance +25% reserve | R/N64 + O/T16 | Four arms x64 |
|---|---:|---:|
| Sequential: largest completed DEV costs, short only |**20.794h**|37.180h|
| Batch4: lower bound from partial replay, assuming four occupied lanes; unusable |**>=49.583h**|>=78.381h|

Formula: `spent + L +1.25*[64(cR+cN)+16(cT+cO)]`; full-four uses `64*sum(c)`.
Sequential cR/N/T/O =313.669/304.932/672.606/310.559 seconds. Batch observed-prefix
cost /4 =863.951s/lane. A completed batch c is unavailable. The batch proxy assumes
four occupied lanes; scheduling the nested two-arm remainder was not validated.
No unmeasured batching gain is credited. Linear 32-round normalizations in
[summary.json](summary.json) are explicitly unvalidated diagnostics; no long GPU
trajectory exists. The current recipe already fails 12h without relying on them.

**Renderer freeze:** [renderer-golden.jsonl](renderer-golden.jsonl) contains all16
exact R rendered UTF-8 blocks, per-block hashes, complete prompt IDs and literal
output IDs/EOS from this run. A CPU consumer replay matches every byte/token.
No layout change after this freeze without a registered amendment. The inferencing
bank/controller/renderer/decoder/custom-entry hashes still match[recipe.json](recipe.json).
Post-run code changes only add the audit, interrupted-cost reporting and golden test.

**Hidden-state artifacts:**256 local `.npy` files, two per call, shape (5,2048),
layers 8/16/24/32/40 as one-based post-block residuals. Prompt vectors are bf16→float16;
generated-body means accumulate forwarded bf16 vectors in float32 then cast float16.
All 128 prompt vectors and 117 complete body means are present. The 10 sequential cap
hits and 1 deadline-interrupted T reply lack the final sampled token's activation;
their partial means and exact counts are labeled, not fabricated or regenerated.
[hidden-manifest.json](hidden-manifest.json) records every path, shape, dtype and hash;
**no .npy is committed**. This limits downstream check 45 use of those 11 means.

Validation: [audit.json](audit.json) verifies 128 unique records, all literal token
IDs, repeated CPU checker/executor results, workspace hashes, live views and 256
hidden hashes/shapes. Targeted tests 47 passed, 1 expected legacy xfail; scoped Ruff
and diff checks pass. Reproduce on CPU with `scripts/composition_pilot_audit.py` and
`scripts/composition_pilot_report.py`; no trunk load. Numerical gates unchanged.

## Registered Day 5b amendment — 2026-09-06 (before code changes)

Fit/train-on none; recovery-on frozen DEV-00 records; re-pilot-on authored DEV
00,01,06,07,02,03,04,05 only. No evaluation/benchmark content or responses.
Fable's CPU review establishes correct programs in all 101 parseable replies;
the original zero-execution result is an interface defect, not a capability finding.

Register exactly two JSON-strict tolerances: (1) remove only an extra `path` key
from a `test` call; (2) only when `report` is absent and `calls` is present, lift
present top-level status/task/delivery into `report`, dropping other top-level
keys (including verbose, with dropped keys/values preserved in the tolerance
journal). Do not interpret nested verbose as task/delivery. Every application
is journaled, including on subsequently rejected outputs. No Python-literal
fallback or stray-bracket repair. Execution and checker share normalization.
Other envelope/schema defects remain errors. JSON/envelope errors return stable,
informative expected-envelope feedback, never json-module exception text.
Add a literal envelope example and explicit report keys to the system prompt.
Renderer layout, T obligation text, cap512 and band100–300 stay frozen.
Recovery replays each frozen lane cumulatively on CPU: report tool and call
execution, final integration and all-obligation success, violations and prior-trait
relapse denominators; no claim these are newly generated amended trajectories.

Trunk default grouped_mm, explicit eager fallback flag (no automatic retry/load).
One GPU load, 7200s inclusive wall cap, sequential only, no signals. First replay
all64 frozen sequential prompts using retained prefixes while they match; reset
a lane's cache if a prior divergence prevents reuse. Compare complete body+EOS
int64 bytes, journal exact IDs and first difference. Proceed only after all64
complete with <=1 divergent prompt, disclosing its first-divergence analysis;
otherwise STOP (no fallback run). Re-pilot R/N/T in frozen episode order; O only
after all R/N/T episodes if time remains. Collect the existing layer8/16/24/32/40
prompt/mean hidden records and hashes. Frozen renderer check replays original
system and original tool feedback so amendment-induced inputs aren't layout drift.

Projection uses prior pilot spent + this run spent + measured reload allowance
+1.25*[64(cR+cN)+16(cT+cO)], largest completed per-arm episode costs; O=R proxy
under DEV gold if O unrun (disclose). No batching credit. ELIGIBLE requires <=12h,
truncation<=2%, executed-call rate>=90%, nonzero executed-trait denominators in
>=2 episodes and completed fixed fallback00/01/06/07 including both lengths.
Observed threshold failure is INELIGIBLE; unavailable evidence/gate failure is
INCOMPLETE. DEV mask trigger retains >=20 opportunities, >=15% relapse and >=2
relapsing episodes in R and O; unrun O cannot establish that trigger.

### Day5b recovered outcomes (CPU, amended parser; frozen outputs)

95/128 responses execute190 tool operations: sequential R/N/O16 each, T0;
batch R/O16 each, T15, N0. All eight lanes finish with final all-obligation
success=false and integration=false. These are cumulative replays of original
outputs, not counterfactual model continuations with successful tool feedback.
All95 recovered responses violate indentation. Sequential R/N/O each have
style16, format12, process15 and breakage15 violations; batch R/O identical;
batch T style15, format13, process15, breakage15. Unparsed sequential T and
batch N have format16/breakage16; their zero style counts are unmeasured.
Language/wrong-family flags are0 on parsed rows. All executed-trait relapse
opportunities are0: no recovered obsolete trait establishes retention pressure.

The frozen snippets omit separating newlines: the second append to a module
joins `return ...]def step_1...`, invalidating cumulative integration. Individual
function correctness in Fable's review does not establish cumulative success.
No edit-append semantics were changed. N places delivery inside discarded
`verbose` entries; four sequential N turns make that claim when delivery is
unscoped. The exact claims and `dropped_unscoped_delivery` diagnostic are saved;
they are not silently lifted by a third tolerance. The normalized process
checker separately measures actual receipts and top-level lifted report fields.
Reproduce with `python -m stencil.focus.pilot_recovery`; deterministic results
and all128 per-row execution/tolerance/outcome records are in
[recovered-summary.json](recovered-summary.json) and
[recovered-records.jsonl](recovered-records.jsonl).

Test-selection deviation: the broad CPU `tests/test_focus_slab.py` invocation
included synthetic evaluation-bank generator/witness cases before this was
noticed. No data/bench content was read and no evaluation prompt went to the
trunk; no evaluation result informed code, registration, tuning or selection.
The run was allowed to finish without signals. Dedicated new tests and GPU
work are DEV-only. The recovery/interface result does not erase this deviation.
