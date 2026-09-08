# Source interpreter — proposed FIT-only training mechanics measurement

Draft, 2026-09-08. This is a proposal for the next independently reviewed step;
no GPU launch is authorized by this draft. Final preparation receipt acceptance,
this resource/measurement specification, and its small implementation must be
accepted before execution. The full goal still requires fresh transfer evidence
and adequate larger executable proof. Automatic usefulness comparable to manual
prose remains a meaningful benefit; no perfect-selector prerequisite is added.

## Purpose and fixed input

Measure whether the local original Qwen3-4B can perform correct, affordable LoRA
updates at the actual longest approved calibration sequence. This measures
mechanics and resources, never semantic transfer or code usefulness. Fit-on only
the already preassigned FIT calibration material; evaluated-on none. No DEV,
withheld, benchmark, spent response or old adapter enters the job. Any later
full training starts with a fresh adapter, not this mechanics adapter.

Use the exact accepted input manifest
`results/source-interpreter/accepted-inputs.json`, SHA
`6beea4bb534e0991fc0444d634f92882ff61191880c43cf4e68da730753c4bf8`, and actual CPU
preview SHA `5760764f748a088d9d105b6f89b6188785941239ea28c1e60d706f9d028a0326`.
The longest row is conversation `source-fit-cal-20260908-04`, query index 2,
preview row index 14: 2,966 prefix tokens plus 925 target/EOS tokens = 3,891.
Consume those exact recorded input IDs, attention and labels, independently
checking their source/target bindings and target-only mask. Batch size one,
no padding beyond that row, no truncation, no new sequence or generation cap.
No semantic generation or worker task is part of this measurement.

## Proposed fixed mechanics

Use the qualified original local `models/qwen3-4b-hf` in the recorded repository
Python environment, local-only loading, BF16 trunk and SDPA attention. Disable
KV caching. Enable gradient checkpointing with non-reentrant recomputation.
No quantization, model download, package changes, new serving process or trainer
framework. Bind exact code, original assets, installed packages and settings.

Create one fresh q_proj/v_proj LoRA adapter: rank 8, alpha 16, dropout 0,
no trained bias, causal-LM task. Use FP32 trainable adapter parameters and keep
all original model parameters frozen. Expected adapter count is 2,949,120;
verify this against the actual named parameters before any update. Seed 20260908
for initialization. These are fixed mechanics choices, not hyperparameters
selected on evaluation outcomes or a claim that this is the final learning recipe.

AdamW: learning rate 0.0001, betas (0.9, 0.999), epsilon 1e-8, weight decay 0.
No scheduler, gradient accumulation or clipping. Exactly four optimizer steps
on the same longest FIT row: one warm-up step followed by three timed steps.
Synchronize CUDA around each timed interval and retain the individual timings;
report mean and maximum, not only an aggregate. The warm-up is an actual update
and belongs in all cost and update counts. Stop on technical failure; do not
retry, choose a shorter row, change settings or tune against its loss.

Check positive finite supervised loss, nonempty supervised positions and finite
adapter gradients. Require nonzero aggregate gradient and adapter update; do not
require every individual tensor's first gradient/update to be nonzero, since
zero-initialized LoRA factors can legitimately remain zero on the first step.
Check the optimizer contains only the intended adapter parameters and that all
original parameter gradients remain absent. Verify every original model
parameter's identity and exact bytes before and after the job; do not call
runtime-cache identity a frozen-weight measurement. Record actual dtype, shape,
parameter count, gradient/update counts and norms, and before/after hashes.
Loss decline is not a quality or transfer gate for this resource measurement.

Save once using standard PEFT `save_pretrained(safe_serialization=True)`.
Capture the complete default adapter state on CPU before saving. Reload the
reconstructed archive through `load_adapter` under the temporary name
`roundtrip` on the same trunk, with `is_trainable=False` and
`autocast_adapter_dtype=True`; no second base model is needed. Compare canonical
adapter-state keys, shapes, dtypes and exact tensor bytes, and reject missing or
unexpected adapter keys. Explicitly activate the reloaded adapter and perform
one evaluation-mode, no-gradient loss computation on the same FIT row, confirming
that it can be consumed. No optimizer update follows reload. Include that call,
save/reload and all hash work in total cost. No withheld example or generated
answer is involved.

The handoff limits committed files to 10 MB; it does not forbid larger local
files. Preserve the standard local adapter for save/reload. Archive its exact
bytes in parts of at most 9,000,000 bytes plus full/part hashes, sizes and
reconstruction order. Concatenate into a separate local directory with the
unchanged adapter configuration, verify full byte identity, then perform the
standard reload above. This is artifact packaging, not a new model format or
permission to lower rank or saved precision to fit the repository. All registered
receipts and archival parts use explicit paths and forced Git tracking.

Sol xhigh checked the installed PEFT 0.20.0 source without loading weights;
root independently checked the parameter arithmetic and save/upcast/load paths.
Config dimensions (36 layers, hidden size 2,560, q output 4,096, v output 1,024)
give `36 * 8 * ((2560 + 4096) + (2560 + 1024)) = 2,949,120` parameters.
Default adapter upcasting makes their raw FP32 payload 11,796,480 bytes before
safetensors metadata. Installed ordinary-LoRA saving writes one canonical
file; `max_shard_size` does not implement sharding here. Primary local evidence:
`models/qwen3-4b-hf/config.json`, and under
`.venv/lib/python3.12/site-packages/peft/`, `mapping_func.py:30-54`,
`tuners/tuners_utils.py:2243-2283`, `tuners/lora/layer.py:258-260`,
`peft_model.py:328-391`, and `utils/save_and_load.py:980-1023`.

## Proposed resource bound and receipts

One owned model child and a small owning supervisor, no concurrent model job.
Proposed hard whole-process
reservation: 600 seconds, including load, hashes, four steps, save, reload,
post-reload forward, receipt writing and cleanup. This is a single initial
measurement bound, not an extrapolated GPU timing or permission for a matrix.
A timeout or failure leaves an explicit incomplete result with completed work
and actual cost; unused time does not authorize a retry. Register the exact PID
before any long work and monitor its exact session through terminal status.
The supervisor starts the common monotonic clock before launching the child,
reserves the last 15 seconds for termination and terminal accounting, requests
termination at 585 seconds if still active, and kills only its owned child if
needed before the 600-second ceiling. Register supervisor and child ownership;
preserve the child's last durable stage/step evidence on forced termination.
The supervisor writes terminal status even when the child cannot. No pass is
possible after the working deadline or without confirmed child exit. Coordinate
with the existing RUNNING.flag convention before launch and clear only this
job's flag after the owned child exits.

Hardware is NVIDIA GB10 on aarch64, driver 580.159.03. Read-only nvidia-smi reports
N/A for a separate total/used GPU memory pool, so N/A must not become a zero or
unlimited-memory assumption. Record actual torch allocated/reserved peaks and
available device information, plus host available memory and swap at startup,
after load, each step, save/reload and exit. Preserve the distinction between
unified system capacity, allocator accounting and a process's measured usage.
The earlier host snapshot is contextual only; refresh it at the actual run.

Write a start receipt before model load, and a durable per-step receipt during
the same run with step ordinal, warm-up/timed designation, loss, supervised-token
count, forward/backward/update timing, gradient/update evidence and memory.
Write terminal status and complete cost even after failure. Record input/code/
environment/base/tokenizer/adapter bindings, all stage timings and terminal
cleanup. No hidden warm-up, discarded attempt or aggregate-only receipt.

Mechanics passes only if the full registered work completes within the bound,
all exact input/loss/update/frozen-weight/save-reload checks pass, and resource
measurements are complete. This would permit costing a separately registered
full FIT run and fresh same-base versus adapter semantic comparison. It does
not itself authorize either, nor establish that learning or downstream utility
will succeed. If a future FIT corpus exceeds the measured length, this receipt
cannot certify the unmeasured longer workload.
