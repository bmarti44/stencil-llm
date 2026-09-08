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
The complete zero-based preview-row schedule is fixed here, generated with one
Python `random.Random(20260908)` instance and a new `list(range(18))` shuffled
at each epoch; execution consumes these lists directly:

```
epoch 1: 12 15 16 1 9 8 13 14 0 4 5 17 10 3 2 11 6 7
epoch 2: 9 12 5 16 3 2 8 10 14 0 1 15 4 17 11 13 7 6
epoch 3: 8 0 7 9 6 10 16 17 12 11 4 5 15 13 14 3 2 1
```

Three passes are a modest
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

Use `model.eval()` and `torch.inference_mode()`, with checkpointing disabled
for generation. Order is fixed: base first inside `model.disable_adapter()`,
then reloaded final adapter via `set_adapter(name, inference_mode=True)`.
Verify actual adapter-enabled state for each call. No merge, unload, extra
warm-up, prompt re-rendering or target-derived stopping rule. Each call starts
with an empty cache; no cache is shared between calls.

Explicit `generate` arguments are `input_ids=[prefix_ids]`, an all-ones
`attention_mask`, `use_cache=True`, `max_new_tokens=2048`, `do_sample=False`,
`num_beams=1`, `num_return_sequences=1`, `eos_token_id=151645`,
`pad_token_id=151643`, `return_dict_in_generate=True`, `output_scores=False`,
`output_logits=False`, `output_attentions=False`, `output_hidden_states=False`,
`logits_to_keep=1` and `synced_gpus=False`. Override inherited sampling settings
with `temperature=1.0`, `top_k=0`, `top_p=1.0`; they are inactive under greedy
decoding. Use the installed native dynamic cache path, without compilation,
custom logits processors, forced JSON grammar or beam search. Preserve the
resolved generation configuration as well as explicit arguments.

The cap is prospectively fixed: it exceeds every accepted
FIT target (maximum925 including EOS) by1,123 tokens. It is not derived from a
generated answer or a retry of the frozen failed coding pilot. Preserve every
returned ID and decoded byte, prompt IDs, settings, active adapter/base identity,
output length, EOS/cap/parse status, whole-call elapsed time and resource usage.
Preserve the complete returned sequence and separately its generated suffix.
Retain terminal EOS in IDs; remove exactly one terminal151645 before decoding
the payload with `skip_special_tokens=False` and
`clean_up_tokenization_spaces=False`. Record exact decoded UTF-8 bytes and hash.
Derive stop facts from output and deadline records: EOS present, cap reached,
deadline reached; preserve simultaneous facts, rather than inventing an HF
finish-reason field. EOS plus one strict valid complete source-interpreter JSON
document qualifies response completion only, not correct instruction selection.

Time each complete `generate` invocation using CUDA synchronization immediately
before and after a monotonic interval. Record generated-token count and whole
call latency; no per-token CUDA hooks or claim about isolated prefill/decode
speed is required. These two calls are a minimal resource measurement, not a
latency benchmark, and their fixed order can affect observed timing.

Installed primary-code qualification: source_interpreter.py already records
nonthinking prefix IDs; PEFT0.20.0 supports disable_adapter and same-trunk
set_adapter; Transformers5.16.1 Qwen3 supports logits_to_keep. The original
generation_config.json defaults to sampling and two EOS IDs, so the explicit
overrides above are necessary. Sol xhigh qualified these APIs read-only; no
model or generation call was made during qualification.

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
stage/whole deadlines and account for final publication/exit. The training stage
starts with supervisor launch, includes artifact validation, model initialization,
all54 updates, save/reconstruction/reload and equality verification, and ends
with a durable training-complete receipt within1,220 seconds. Each generation
reservation starts immediately before its pre-call synchronization, includes
post-call synchronization and durable output publication, and is300 seconds.
The child uses a stateful monotonic stopping criterion to return partial IDs
on an observed deadline. The supervisor also monitors durable stage deadlines
so a hung CUDA call cannot outlive its reservation. A hard timeout may prevent
recovery of in-flight output; report it as unavailable, never as zero generation.
Receipt preparation, final original-weight checks and cleanup share the remaining
whole-process allowance; reserve the final15 seconds for owned-process cleanup.
The independent outer observer enforces2,400 seconds through supervisor exit.
No concurrent model
job, new service, model download, package change or external spending.

On failure or timeout, preserve all performed work and unresolved attempts and
stop this fixed job. Unused time grants no retry. Training/persistence completion,
each generation request's outcome, and complete cost measurement are separate
reported fields. An ordinary returned cap/invalid JSON result is recorded and
the second preplanned call still runs; a technical exception or deadline stops
the job, with any unstarted call marked not attempted. Any incomplete call or
missing required measurement is disclosed;
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
