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

## Round 2 — 2026-09-08 — implementation

Score: 84/100

Decision: **NOT ACCEPTED for execution.** Two open high findings and one open
medium finding below. The accepted specification is unchanged; these are
implementation defects within its existing launch and measurement contract.
Round 1 is preserved verbatim. Same author-disjoint Astra xhigh native reviewer,
same purpose and trusted-but-fallible threat model; no reviewer substitution.

Reviewed commit: `e4f45c2c57e416483dcbc6684cb8117ff287cff4`.

- `scripts/source_interpreter_mechanics.py`, SHA-256
  `20ab4f538a312e99f0bc95e2cee970092474256869d60c6c95436dcc3c3dd82a`.
- `tests/test_source_interpreter_mechanics.py`, SHA-256
  `28ad1f99cd480273a8d9afd281830a6b9d573fafb248dbbea826ec053191fe6c`.
- Governing `MECHANICS.md`, unchanged SHA-256
  `a43b1d4b48cb7f0478efb43b21ac6187dcaff89bf895761a32c3681898702945`.
- Implementation brief, SHA-256
  `1ee265c040218ff576ade662aa96a25c8fbb03ca1ffc58d49b303f9ddf2a09eb`.

### Findings

#### 1. [high] The registered direct-file launch cannot import its data consumer

`source-interpreter-mechanics#1` — open.

Evidence: `_source_module()` imports `src.stencil.focus` at runner line 167.
The registered supervisor/child commands execute the runner by absolute file
path, which places `ROOT/scripts` at `sys.path[0]`. The installed editable
package supplies `ROOT/src`, not `ROOT`, so the package available in that
environment is `stencil`, not `src.stencil`. Independently reproduced using
the actual `.venv/bin/python`, replacing only `sys.path[0]` with the registered
script directory: `ModuleNotFoundError: No module named 'src'`. This is an
import-only CPU check; no model/runtime was loaded. Root independently reproduced
the failure through `runpy.run_path` and the actual `validate_artifacts(False)`
consumer and preserved `results/source-interpreter/mechanics-direct-import-error.log`.

The nine passing tests do not exercise this path: pytest adds both `src` and
`.` through `pyproject.toml:26`, the fresh import test imports from the repository
root, and dry-run returns before `_source_module`. Root's separate module-style
artifact qualification passed and is valid for that invocation, but cannot
qualify the registered direct-file launch. The supervisor currently fails before
reserving the GPU job; launching with `python -m` alone would leave the generated
direct-file child command broken as well.

Narrow correction: import the installed `stencil.focus.source_interpreter`
package, or otherwise make the actual direct-file path explicitly valid without
depending on pytest's path configuration. Add a fresh subprocess regression for
the direct-file import/qualification consumer with no repository-root path
injection; no model load is needed. Keep the accepted helper unchanged.

#### 2. [high] A completed optimizer update can disappear from failure accounting

`source-interpreter-mechanics#2` — open.

Evidence: the actual training loop performs and synchronizes `optimizer.step()`
at runner lines 999–1000, then calls gradient/update validation and resource
collection at 1002–1003, and only afterward appends or writes any step receipt
at 1022–1024. Both validation and resource collection can raise. For example,
an absent/nonfinite adapter gradient is deliberately rejected by
`validate_optimizer_step` after the optimizer invocation. A forced termination
during the per-tensor CPU copies/hashes has the same accounting problem.
In these cases the model has already undergone the update, but neither the
in-memory completed-step list nor `step-*.json` records it. The exception result
omits it, and `_partial_update_counts` at 1273–1290 reports only previously written
full receipts. On the first update, the lifecycle can therefore report zero
updates and zero warm-up updates after an actual warm-up update occurred.

This matters to the stated purpose: technical failure must preserve completed
work and actual update counts, and this one-shot run has no automatic retry to
reconstruct lost evidence. It does not falsely turn this particular failure into
a mechanics pass, but it loses required evidence from a failed measurement.
The existing failing-child test writes complete step files itself before exiting,
so it verifies recovery of those files without exercising this gap in the real
step-writing order.

Narrow correction: write a small durable current-step record before the work and
durably record a synchronized optimizer completion before potentially failing
validation/hash/resource work. Keep update completion distinct from validation
success. Failure/timeout accounting should preserve confirmed completed updates
and explicitly mark an interrupted, unresolved update as unknown or a lower
bound, rather than claim an exact smaller count. This needs no transactional GPU
framework: a few stage/status fields in the existing receipt path suffice.
Exercise the actual step consumer with CPU doubles that fail immediately after
the update, and verify the warm-up count plus incomplete status; also cover a
pending-step receipt in the timeout consumer.

#### 3. [medium] Terminal elapsed cost stops before supervisor finalization

`source-interpreter-mechanics#3` — open.

Evidence: `supervise_child` samples `ended = clock()` at runner line 1390,
before reading/validating the child result, reading partial step records,
enumerating partial files, writing the lifecycle receipt twice with fsync, or
clearing the flag at 1446–1450. The saved `ended_monotonic` and COMPLETE decision
both use that earlier timestamp; there is no later clock/bound check. Thus the
recorded total interval excludes terminal accounting and flag cleanup, and a
delay in that work can finish beyond the registered total bound while the
supervisor still returns COMPLETE. This is a boundary/accounting defect, not a
claim that normal small-file finalization has already overrun the budget.

Narrow correction: retain child-exit time separately, measure finalization through
cleanup/accounting, and make the final status/bound check use a suitably late
monotonic sample. Record the full measured interval and distinguish any final
receipt-emission tail that cannot describe itself. Add an injected-clock or
delayed-finalization CPU test showing that accounting time is included and late
finalization cannot retain COMPLETE. No new supervision service is needed.

### Verified strengths and prior handoff fixes

The native loss call passes the exact full labels unchanged; target/EOS masking
and causal positions match the accepted row. Input hashes bind the frozen
preview, accepted source documents and helper; the child additionally hashes
base files and compares actual loaded tokenizer state with the accepted receipt.
The selected interpreter/package versions are checked. Root reports the actual
module-style artifact consumer passed in 0.06713999199564569 seconds with no heavy
imports, recorded at `mechanics-artifact-check.json`, SHA-256
`11d361550e4fcc7e514115a1ea601db390577b470c82814eadea45db0d68ce6c`;
this corroborates the schema path while leaving finding 1 intact.

The update checks reject absent gradients, nonfinite gradients, zero aggregate
updates and incorrect optimizer membership while accepting a legitimate zero
individual factor. Original parameters are frozen, their identities checked
per step, and their full before/after bytes checked at the end. Per-step receipts
now correctly disclose when original bytes were not rehashed. The corrected
`Tensor.view(torch.uint8)` byte path is exercised by the targeted CPU tests.

Standard FP32 PEFT save, exact byte parts, ordered reconstruction, canonical
adapter-state equality, explicit `roundtrip` inference activation and the single
no-gradient post-reload loss call match the accepted design. The original trunk
is reused and checked afterward. No semantic generation or evaluation is added.

The post-Popen registration/launch-receipt exception path now terminates and reaps
the owned child, and the targeted injected registration-failure test passes.
Happy exit, failing exit, timeout, preservation of a separate foreign flag/process,
and recovery of already-written partial steps also pass. The immutable historical
round-1 review binding plus current-review launch hash avoids the prior mutable
review-hash cycle. These fixes are real; finding 2 concerns the remaining interval
before a completed update gets its first durable receipt.

### Validation and scope

Independently ran `.venv/bin/pytest -q tests/test_source_interpreter_mechanics.py`:
**9 passed in 1.99 seconds**. This includes fresh import and dry-run checks.
Read both complete implementation files, the accepted spec/brief, relevant
installed package/path evidence, and the latest ledger STATE. Rehashed both
reviewed implementation files before writing this round; neither changed.

No real training, target-model inference, model/weight loading, CUDA context,
real adapter save, new semantic data, network download or full-suite run occurred.
Only this canonical report was written; no implementation/spec/ledger edits or
commit were made. The required corrections are confined to launch imports and
measurement receipts; the registered model settings, data, four updates and
scientific scope do not need to change.

## Round 3 — 2026-09-08 — findings 1–3 correction

Score: 96/100

Decision: **ACCEPTED for the registered mechanics implementation.** Findings
1–3 are resolved below. Zero open findings at any severity; no new findings.
The 90-point threshold and zero-open-high/critical condition are met. Prior
rounds are preserved verbatim; the closure decisions in this round supersede
their earlier open statuses. Same Astra xhigh author-disjoint native reviewer,
same canonical topic, purpose and trusted-but-fallible threat model.

Reviewed correction commit: `c108534c78f405c5605eca2f1f0b3e8bbf135f71`.

- Runner SHA-256:
  `4eb7cb46f0191e7481e162e03ee12db2d771e9a043792ddd3d6c825e50321927`.
- Targeted tests SHA-256:
  `d6aa5b3b888d2d11a6d573e996dd5de0c48927073f1b432cb957547c8d735bf4`.
- Accepted specification remains unchanged, SHA-256:
  `a43b1d4b48cb7f0478efb43b21ac6187dcaff89bf895761a32c3681898702945`.
- Supplemental correction brief SHA-256:
  `5c3ed039dc07b14d1a1d2f35a5ea742df634c4227b62505fee457f86751e8d94`.

### Finding closures

#### 1. [high] (resolved in round 3, 2026-09-08) Direct-file import

`source-interpreter-mechanics#1` is resolved. `_source_module` now imports
the installed `stencil.focus` package. The new `--_qualify-only` branch invokes
the actual artifact consumer without running model work, and rejects combinations
with execution/child/run arguments. The targeted regression executes the absolute
runner file from a temporary working directory with `PYTHONPATH` removed. It
passes through the previously failing consumer and returns qualified row 14.
This regression passed in the reviewer's targeted run. Root separately reports
the same direct-file qualification from `/tmp` passed and preserved its log at
`results/source-interpreter/mechanics-direct-qualification.log`, SHA-256
`ad3f40f61b88058e565af91c508d3e61e89bedafda354eb2b1d2564f3e3cd4bc`.
Both the supervisor and child share the corrected import; changing only the
supervisor's invocation style is no longer needed.

#### 2. [high] (resolved in round 3, 2026-09-08) Update evidence before validation

`source-interpreter-mechanics#2` is resolved. The actual training loop now calls
`perform_optimizer_step` (runner lines 454–529), which publishes durable INTENT
before work, UPDATE_PENDING before `optimizer.step`, and UPDATE_CONFIRMED after
synchronization and before gradient/update validation or resource collection.
Later validation and resource completion have separate transitions. The atomic
current-step JSON is written before the append-only history at each transition,
so a later history-write or validation failure cannot erase a published confirmed
update. If interruption occurs before confirmation is published, the prior
pending record explicitly leaves completion unknown.

The incomplete child result recovers current durable step records and update
accounting; the supervisor separately records confirmed totals, warm-up/timed
counts, validated totals and pending/unknown steps. Exact totals become null
when an update is unresolved. This conservatively handles the GPU/filesystem
boundary without claiming atomic completion across both systems.

The new regression exercises this actual step consumer with a tiny CPU adapter:
the optimizer changes its parameter, subsequent absent-gradient validation fails,
and the durable receipt still confirms one performed warm-up with validation
incomplete. The existing timeout consumer now also receives an UPDATE_PENDING
record and verifies `updates=null`, confirmed lower bound zero, and unknown step
0. Both tests pass. The unchanged full-row loss call, optimizer settings and four
update ordinals remain intact through the extraction into this helper.

#### 3. [medium] (resolved in round 3, 2026-09-08) Finalization timing

`source-interpreter-mechanics#3` is resolved with the implementation correction
and the explicit outer-observation handoff. The supervisor retains a separate
child-exit timestamp, writes a FINALIZING receipt, completes result/partial-work
accounting and flag cleanup, then takes the finalization timestamp at runner
line 1554. Recorded elapsed time now covers that work. Finalization after the
total deadline changes an otherwise COMPLETE candidate to
INCOMPLETE_FINALIZATION_DEADLINE and returns failure. The injected-clock test
passes: child exit at 0.2 seconds followed by finalization at 2.1 seconds under a
2-second total reservation cannot remain COMPLETE.

The final lifecycle publication is explicitly identified as a tail outside the
last self-observed timestamp. Root has recorded in the latest ledger STATE that
the actual launch will observe the entire outer process and make the wall-time/
bound verdict including this publication and process-exit tail. That exact outer
receipt remains necessary before claiming a complete measurement within 600
seconds; the runner's self-reported COMPLETE field alone is insufficient. This
is the narrow accounting handoff contemplated by finding 3 and its correction
brief, with no additional supervision framework or increased budget.

### Verification and remaining empirical work

Independently read the complete two-file delta and its affected consumers,
checked the latest ledger STATE and correction brief, and rehashed both code
files plus the unchanged accepted specification. Ran only
`.venv/bin/pytest -q tests/test_source_interpreter_mechanics.py`:
**12 passed in 2.05 seconds**, including the import/dry-run, direct-file consumer,
post-update failure, pending timeout and finalization regressions. The fixes
introduce no observed in-scope regression. Existing loss masking, frozen-trunk,
standard FP32 save/archive/reload and scientific scope remain as reviewed in
round 2.

This acceptance qualifies the code for the frozen, supervised four-update
measurement. It establishes no empirical runtime, memory feasibility, numerical
mechanics pass, learned transfer or coding usefulness. The eventual measurement
must still produce its registered complete receipts, actual outer process cost
and terminal exit evidence. No automatic retry or changed settings are added.

Only this canonical review file was written. No code/spec/ledger edit, commit,
model/weight load, CUDA context, real training/inference/save, semantic authoring,
network request, preview regeneration or full-suite run occurred in this review.
