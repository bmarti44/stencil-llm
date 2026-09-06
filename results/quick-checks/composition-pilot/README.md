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
