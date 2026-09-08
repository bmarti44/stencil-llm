# Proposed fixed FIT run and generation cost measurement

Draft, 2026-09-08. Requires independent specification and implementation review
before execution. This is one training recipe and two FIT-only generation calls;
it neither evaluates transfer nor authorizes a fresh semantic comparison.

Fit-on: all eighteen accepted query rows from the six preassigned Kimi FIT
families in accepted-inputs.json. Development-on/evaluated-on: none. Generation
timing uses the existing longest FIT prefix only. No benchmark, spent DEV bank,
old response, old adapter or withheld conversation enters training. Never
initialize from the four-step mechanics adapter. New conversations for a later
semantic comparison are authored and assigned separately before model access.

## Fixed training proposal

Use the same original local Qwen3-4B, verified repository environment, accepted
source-only nonthinking prefixes and target-only JSON/EOS loss construction.
Consume the exact eighteen recorded rows in preview.json, with their accepted
source/target bindings. Batch size one, no padding/truncation/packing or omitted
row. Maximum full sequence remains the measured 3,891 tokens.

Initialize a fresh rank-8 q_proj/v_proj LoRA adapter, alpha16, dropout0, no bias,
FP32 adapter and BF16 frozen original trunk. Preserve the measured SDPA,
non-reentrant gradient checkpointing, cache-disabled training and AdamW settings:
learning rate0.0001, betas(0.9,0.999), epsilon1e-8, weight decay0; no scheduler,
clipping or accumulation. Seed20260908. No hyperparameter search or checkpoint
selection. Save only the final fixed-step checkpoint.

Train exactly three epochs: 18 rows per epoch, **54 optimizer updates**. Each
epoch contains every row once, in an explicitly frozen seeded shuffle order.
The complete schedule is written before execution. Three passes are a modest
fixed first recipe, not a claim of optimality or a setting selected by the four
mechanics losses. Total presented sequence tokens:89,343; supervised target/EOS
tokens:21,702. Repetition does not create additional independent examples.

Keep the accepted numerical checks and durable step intent/pending/completion/
validation records. Require finite positive loss and finite/nonzero aggregate
adapter gradients and updates, correct optimizer membership, and absent original
gradients. Do not require every tensor's gradient to be nonzero, falling loss,
or any semantic score. Verify all original parameter identities and exact bytes
before/after the job. Save standard FP32 PEFT state and exact archive parts,
reconstruct and reload it, and verify complete adapter state equality.

## Two FIT-only generation calls

After fixed training and reload, use the exact accepted row14 prefix IDs only
(2,966 tokens). Its target/EOS IDs and labels must never enter generation input.
The template already fixes nonthinking mode; do not re-render it through a new
tool client or insert generated focus. Generate once from the unchanged base
and once with the final trained adapter, under identical settings and the same
source prefix. Use the same original trunk without merging weights.

Proposed settings: evaluation mode, no gradients, greedy generation
(`do_sample=False`), batch1, native KV cache, actual EOS151645/pad151643,
`max_new_tokens=2048`. This cap is prospectively fixed: it exceeds every accepted
FIT target (maximum925 including EOS) by1,123 tokens. It is not derived from a
generated answer or a retry of the frozen failed coding pilot. Preserve every
returned ID and decoded byte, prompt IDs, settings, active adapter/base identity,
output length, EOS/cap/parse status, whole-call elapsed time and resource usage.
Exact installed generation and adapter-disable APIs are under read-only Sol
qualification; settle those details before specification freeze.

These calls measure generation behavior and cost on FIT material. They do not
test generalization or select a recipe. Strict full-response parsing may report
invalid JSON, invalid citations or a capped response; preserve that failure,
with no repair, extraction, retry or settings change. A capped or malformed
request does not become a semantic success because its timing is available.
There is no perfect-selector or perfect-FIT-format prerequisite for a future
prospectively registered utility experiment. The later fresh comparison must
count the same request failures and remain separately justified.

## Cost, bound and interpretation

The accepted mechanics result gives a maximum timed forward/backward/optimizer
interval of3.3202526710520033 seconds on the longest row. Conservatively retaining
the entire125.124811046-second mechanics job as setup allowance gives:
`125.124811046 + 54 * 3.3202526710520033 = 304.418455283 seconds`.
This intentionally double-counts the pilot's four updates as allowance. It is
an estimate for training/persistence, not a generation latency measurement;
per-step diagnostic overhead is excluded from the core interval. Four times
that estimate is1,217.673821131 seconds. Reserve1,220 seconds for the complete
training/persistence stage, with no restart after technical failure.

Autoregressive decoding latency is unmeasured. Allocate an initial fixed maximum
of300 seconds to each of the two generation calls as a measurement reservation,
not a throughput prediction. Proposed outer whole-process ceiling:2,400 seconds
(40 minutes), including all startup, training, generation, hashing, receipts and
cleanup. A common owning supervisor and outer observation must enforce the
stage/whole deadlines and account for final publication/exit. No concurrent model
job, new service, model download, package change or external spending.

On failure or timeout, preserve all performed work and unresolved attempts and
stop this fixed job. Unused time grants no retry. Training/persistence completion,
each generation request's outcome, and complete cost measurement are separate
reported fields. Any incomplete call or missing required measurement is disclosed;
no hidden warm-up, silent shrinking, generated-output repair or aggregate-only
records. Archive explicit receipts/config/byte parts under the existing10MB
commit limit; retain standard full checkpoints locally.

If the job completes and independent review accepts its evidence, use the actual
generation lengths/times and training cost to cost the next wholly fresh
same-base-versus-adapter comparison. Do not extrapolate a training step into a
decoding rate. Neither this proposal nor its eventual FIT losses/outputs prove
useful current-focus selection. Fresh semantic evidence and adequate larger
coding utility remain required for the broader goal. Automatic usefulness
comparable to good manual prose remains a meaningful benefit.
