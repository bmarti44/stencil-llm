# Source interpreter mechanics — independent Astra review

Canonical topic: `source-interpreter-mechanics`.
Canonical review file: `results/source-interpreter/mechanics-review-astra.md`.
Author-disjoint reviewer: user-requested `gpt-6-astra`, `xhigh` reasoning effort;
native agent session `/root/source_mechanics_review`, no wrapper or substitution.
This is a new review session. Subsequent rounds retain this file and its history;
the accepted preparation report is a separate, unchanged review topic.

## Round 1 — 2026-09-08

Score: 96/100

Decision: **ACCEPTED for the specification stage.** Zero open high/critical
findings; no findings at any severity. The draft clears the 90-point threshold.
Implementation review and the registered run remain outstanding; this decision
does not constitute a GPU launch or measured mechanics success.

Reviewed artifact: `results/source-interpreter/MECHANICS.md`, SHA-256
`a43b1d4b48cb7f0478efb43b21ac6187dcaff89bf895761a32c3681898702945`.
This decision covers that exact draft, not the separate implementation brief.

Purpose: test the credibility of the smallest local longest-FIT-row mechanics
and resource measurement: target-only causal loss, correct fresh LoRA updates,
frozen original weights, faithful standard persistence, bounded supervision and
durable evidence. Threat model: trusted-but-fallible agents, not malicious
same-uid actors. A generic training framework or a complete learning study is
outside this review's scope.

### Findings

None. There are no numbered findings to close or defer.

### Evidence and reasoning

- **Exact FIT input and causal supervision.** Independently rehashed the accepted
  manifest to `6beea4bb534e0991fc0444d634f92882ff61191880c43cf4e68da730753c4bf8`
  and recorded preview to
  `5760764f748a088d9d105b6f89b6188785941239ea28c1e60d706f9d028a0326`.
  Parsed the existing receipt without regenerating data: row 14 is the unique
  maximum at 3,891 tokens, conversation `source-fit-cal-20260908-04`, query 2,
  with 2,966 masked prefix positions, 925 supervised target/EOS positions,
  all-one attention, and one target EOS. Its labels equal exactly 2,966 copies
  of `-100` followed by the recorded target/EOS input IDs. Installed
  `transformers/models/qwen3/modeling_qwen3.py:497-499` routes labels to the
  causal loss; `transformers/loss/loss_utils.py:49-71` pads and shifts labels
  internally, with `-100` ignored. Thus unchanged full-row labels supervise
  predictions at zero-based logit positions 2,965 through 3,889, including the
  first target and EOS. No second manual label shift is needed. The draft's
  input/loss checks can be implemented directly against this consumer.

- **Adapter updates and frozen trunk.** Recomputed the count from the local
  model config: 36 layers, q output `32 * 128 = 4,096`, v output
  `8 * 128 = 1,024`, hidden size 2,560. Rank-8 q/v LoRA therefore has
  `36 * 8 * ((2560 + 4096) + (2560 + 1024)) = 2,949,120` parameters,
  with 11,796,480 raw FP32 bytes. The draft fixes the optimizer, seed,
  non-reentrant checkpointing and four real updates; includes the warm-up in
  cost; checks optimizer membership, gradients and parameter updates; permits
  legitimate first-step zero factors; and separately requires absent original
  gradients plus exact original-parameter identity and byte checks. These are
  appropriate mechanics checks without a loss-decline or semantic gate.

- **Standard save and exact reload.** Installed `peft/peft_model.py:328-391`
  obtains the PEFT adapter state and writes a canonical safetensors file.
  `peft/utils/save_and_load.py:94-145` documents canonical adapter-name-free
  keys and filters other named adapters. Critically, `peft_model.py:1477-1496`
  adds the new adapter before loading weights, and `add_adapter` at
  `peft_model.py:1178-1181` applies dtype upcasting before that load.
  `peft/tuners/tuners_utils.py:2243-2283` supplies the FP32 conversion. The
  specified `autocast_adapter_dtype=True` therefore supports direct copying of
  the saved FP32 state into FP32 destination tensors, without first rounding
  the trained state through BF16. The exact keys/shapes/dtypes/bytes check and
  actual reloaded-adapter forward remain required runtime evidence. A useful
  implementation detail is `set_adapter("roundtrip", inference_mode=True)`:
  the installed method defaults to making the selected adapter trainable
  (`peft_model.py:1591-1614`). The draft already requires evaluation mode,
  no gradients and no subsequent update; this API detail is not a finding.

- **Faithful archival packaging.** The local pre-commit hook at
  `tools/hooks/pre-commit:6-20` rejects staged blobs above 10,000,000 bytes.
  Exact parts of at most 9,000,000 bytes preserve that constraint while keeping
  the standard adapter intact locally. Ordered reconstruction into a separate
  directory, full and part hashes, unchanged configuration, and standard
  reload establish both byte preservation and consumability. No precision
  reduction, rank change or custom weight format is needed.

- **Bounded work and failure visibility.** The supervisor owns the common
  clock and child; the 585-second working deadline leaves 15 seconds within
  the 600-second total bound for termination and terminal accounting. A late
  or unconfirmed child exit cannot pass. Startup, durable step/stage evidence,
  failure accounting, ownership registration, flag coordination and explicit
  cleanup cover the credible interruption paths for this small local run.
  The bound is a first measurement reservation, not an unsupported throughput
  estimate. Failure is an allowed outcome and does not authorize retries.
  Refreshing host/swap readings and separating allocator peaks from unified
  host capacity correctly handles the reported GB10 memory accounting.

- **Scope and lineage.** The proposal consumes only the already accepted FIT
  row, evaluates no benchmark or withheld material, creates no semantic answer,
  and requires any later full training to start with a fresh adapter. Four
  repeated-row updates cannot show learned transfer or coding usefulness; the
  draft states those limitations and requires separate later registration.
  The measurement can support cost estimates at its measured length while
  leaving longer workloads unqualified. No selector-perfection or representation
  superiority prerequisite is introduced.

Review method: read the governing archived protocol and latest ledger STATE
first, inspected the frozen proposal and preparation contracts, parsed only
selected recorded preview fields, recomputed arithmetic, and read installed
primary API source. No model or weights were loaded, no GPU context or model
inference was invoked, no packages/assets were changed, no spent evaluation
material or prior adapter was inspected, and unchanged accepted tests were not
rerun. Only this canonical review file was written; no commit was made.

Residual uncertainty is empirical runtime, memory and numerical execution on
the actual machine. The proposed bounded run exists to measure those facts;
their absence before execution is not a specification defect.
