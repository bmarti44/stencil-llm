# Fixed FIT training and generation cost review — Astra

Reviewer: **gpt-6-astra, xhigh reasoning**, independent native session
`/root/source_fit_review`; no wrapper. User-directed Astra/xhigh substitution
for the historical Opus maximum-effort reviewer rule. The reviewer did not
author the proposal, implementation or semantic data.

Purpose: review the prospective single-machine fixed FIT recipe and two
FIT-only generation cost calls. Threat model: trusted-but-fallible
experimenters. This review tests scientific scope, lineage, executable recipe,
installed API compatibility, cost/deadline accounting and unnecessary gates;
it does not demand hostile-agent defenses or accept the broader goal.

## Round 1 — specification review, 2026-09-08

**Score: 96/100. ACCEPTED — proposal only.**

**Zero findings; zero open high or critical findings.** Acceptance requires
90/100 and no open high/critical findings. No corrective specification change
is required. Finding numbering starts at #1 if a later round identifies an
in-scope implementation defect or regression; there are no findings to close
or renumber in this round.

Exact reviewed specification:
`results/source-interpreter/FIT.md`, SHA-256
`f1f306e9ccac968013568dd6f0ed46a42d6df7297105c7a2531a83b7caa541a7`.
The parent reports prospective freeze commit `975bdc1a`; the current file hash
was independently checked before and during review.

### Input and evidence bindings

Independently hashed these supporting artifacts under
`results/source-interpreter/`:

| Artifact | SHA-256 |
| --- | --- |
| `PREP.md` | `5a8536453e52a9427aae02e8a32d6671b9968bc667e483d80f09b2a3be01898e` |
| `MECHANICS.md` | `a43b1d4b48cb7f0478efb43b21ac6187dcaff89bf895761a32c3681898702945` |
| `accepted-inputs.json` | `6beea4bb534e0991fc0444d634f92882ff61191880c43cf4e68da730753c4bf8` |
| `preview.json` | `5760764f748a088d9d105b6f89b6188785941239ea28c1e60d706f9d028a0326` |
| Accepted preparation `review-astra.md` | `c6538d94d711494c69a0a201105daa51c34aa7c73e3591dcc2b94ac75f4a3e05` |
| Accepted `mechanics-review-astra.md` | `36412129ba95db784c5849e1675459f6cf3d1dd609745001fa28a3efb1d2cde5` |

Read the accepted preparation and mechanics conclusions without reopening their
resolved findings. Their frozen results provide the lineage and measured
training/persistence evidence; this round does not repeat their semantic,
tokenizer or live-weight audits.

### Assessment

**Lineage and usefulness.** Training consumes only the eighteen accepted query
rows from six families assigned FIT before Kimi authoring. Independently checked
all six canonical document hashes, FIT/family identities and the complete set
of three query indices per conversation against the saved preview. Stored
prefix/target concatenation, target/EOS labels and unpadded attention masks
agree for every row. No new source, spent DEV bank, benchmark or old adapter is
needed. Repeated prefixes remain correlated FIT examples. A fresh final adapter
followed by two FIT cost calls is a useful bounded next step toward a later
fresh comparison; neither a perfect selector nor perfect FIT formatting is a
necessary gate for that later prospectively justified work.

**Recipe exactness.** The original frozen BF16 Qwen3-4B trunk, fresh FP32 rank-8
q/v adapter, alpha 16, zero dropout/bias, SDPA, non-reentrant checkpointing and
AdamW settings are specified consistently with accepted mechanics. Initialization
must start fresh, never from the four-update mechanics adapter. Independently
reproduced all three shuffle lists using the stated single seeded Python RNG;
each contains all eighteen indices once. The lists therefore prescribe exactly
54 updates, with no extra warm-up, dropped row or checkpoint selection.
Recomputed presented sequence tokens **89,343** and supervised target/EOS tokens
**21,702** from the saved rows. Numerical and frozen-weight checks preserve
nonvacuous aggregate gradients/updates without requiring each LoRA factor to
change or loss to decline. Final standard FP32 state/archive/reload equality is
feasible using the accepted primitives. The draft implementation brief clarifies
that no extra post-reload target-loss call is intended; the registered follow-on
model calls are the two prefix-only generations.

**Same-base versus adapter semantics.** Row 14 is independently confirmed as
the maximum prefix, target and full-sequence row: **2,966 + 925 = 3,891** tokens.
Its recorded source-only prefix is the common input. Inspecting
`src/stencil/focus/source_interpreter.py:675` confirms that this prefix precedes
separately constructed target/EOS supervision and fixes nonthinking mode.
Generation receives neither target IDs nor labels. The unchanged original trunk
is used first with all adapters disabled and then with the reconstructed final
adapter explicitly active; no merge or second original model is required.

Read-only inspection of installed PEFT **0.20.0** confirms that
`peft_model.py:1046` disables LoRA layers within its context and restores their
enabled state on exit. `peft_model.py:1591` forwards `inference_mode=True` through
adapter activation; the tuner freezes active and inactive adapter parameters
appropriately. The causal-LM `generate` path forwards ordinary LoRA generation
to the underlying model. Actual runtime adapter-state verification remains part
of the proposed contract and must be exercised in implementation review.

Installed Transformers **5.16.1** Qwen3 accepts `logits_to_keep` in its forward
method (`models/qwen3/modeling_qwen3.py:448`). Generation keyword overrides have
highest precedence (`generation/utils.py:1771`). The original local generation
config really enables sampling and EOS IDs 151645/151643; the proposal's greedy
settings and single EOS override therefore make a substantive, valid correction
for this protocol. The native default cache path creates a new `DynamicCache`
when no past state is supplied (`generation/utils.py:1929`); that path does not
meet the automatic compilation condition (`generation/utils.py:2120`). Fresh
per-call caches, evaluation/inference mode and disabled checkpointing are
compatible with the planned two calls.

**Output and timing interpretation.** The 2,048-token cap exceeds the maximum
accepted target including EOS by **1,123** tokens and is fixed before generation.
Retaining full sequence IDs, separate suffix IDs and exact decoded payload bytes
allows strict full-document parsing without extraction or repair. Completion
requires EOS and valid structure/citations, not agreement with the FIT gold or
correct instruction selection. EOS/cap/deadline are separate observable facts;
the native generator supplies no finish-reason field to justify a stronger
claim. An invalid or capped ordinary return still permits the second fixed call.
Synchronized whole-call latency is adequate for this resource measurement.
Two fixed-order calls with potentially different lengths cannot establish an
adapter latency benchmark or isolated prefill/decode rates; FIT.md says so.

**Budget and partial work.** Recomputed the estimate as approximately
**304.418455283 seconds**, fourfold **1,217.673821131 seconds**, consistent with
the 1,220-second training/persistence reservation. The retained complete pilot
cost supplies allowance beyond the timed core; this remains an estimate because
per-step diagnostic overhead is outside that core. It is not a decoding-rate
measurement. The two unmeasured 300-second generation reservations plus training
leave **580 seconds** within the 2,400-second outer ceiling for remaining work,
including the final 15-second cleanup reserve.

The stage definitions include qualification/model initialization and final
training receipt, then each call's synchronization and durable publication.
Child monotonic stopping plus an owning supervisor monitoring durable stage
deadlines is implementable. A stopping criterion alone cannot interrupt a hung
CUDA operation; the proposal explicitly requires external enforcement and
outer observation through supervisor exit. Deadline recovery does not guarantee
partial IDs: hard termination can make them unavailable, which must remain
distinct from zero generated tokens. Separately reporting training completion,
each request outcome, unresolved work and completeness of cost measurement
prevents a technical failure or missing receipt becoming a success. No retry or
use of spare time to change the recipe is permitted. These requirements need
consumer-level implementation verification, not another prerequisite experiment.

### Review boundary and next step

This accepts **only the prospective specification**. The actual runner is not
reviewed or authorized for execution by this report. Next is the bounded Sol
implementation, targeted consumer checks, independent code review and one
prospectively bound run. Stage monitoring being unwritten at this specification
stage is not a defect. No full-suite testing, additional model pilot, perfect-FIT
gate, new framework or external compute is necessary to proceed to implementation.

Any eventual FIT training loss, parse outcome or timing still cannot establish
generalization or coding utility. A wholly fresh same-base/adapter comparison
and adequate larger executable coding proof remain required for the broader
goal; automatic usefulness comparable to good manual prose remains valuable.

Review method: local text/primary-source inspection and narrow standard-library
JSON/hash/arithmetic checks only. No model loads, weight-payload reads, GPU
operations, generation, data authoring, network, script imports, tests, rescoring
of old outputs or access to excluded evaluation banks occurred. Only this
canonical review file was written; no code, specification, ledger edit or commit
was made.

## Round 2 — implementation review, 2026-09-08

**Score: 84/100. NOT ACCEPTED — implementation corrections required.**

Same independent native **gpt-6-astra, xhigh** session and user-directed reviewer
substitution as round 1. **Three open findings: #1 high; #2–#3 medium. Zero
critical findings.** The accepted specification remains unchanged; this round
does not reopen its scientific choices or the accepted preparation/mechanics
findings. Round 1 and its input hash/history are preserved verbatim.

Reviewed stable Sol commit
`16d4d976ab3ebb8f7d650e5a9ce0ded134475344`, with independently checked current
bindings:

| Artifact | SHA-256 |
| --- | --- |
| `scripts/source_interpreter_fit.py` | `a405a9d045eecf90de4974b0c5415025e2418a512eed3f24536a897a36ad67d0` |
| `tests/test_source_interpreter_fit.py` | `7b38c1bf4a9e4b901b5daa91de8b6806af7dd7d77ceff786da7fbe86b8fb8a8e` |
| `results/source-interpreter/FIT.md` | `f1f306e9ccac968013568dd6f0ed46a42d6df7297105c7a2531a83b7caa541a7` |
| `results/source-interpreter/FIT-CODE-BRIEF.md` | `9a3836c0e08944052d98c86c21e7b09c952778f396af0ac8133c813293328e6f` |

### Findings

**Finding 1 — high, OPEN. Stage deadlines can be bypassed by late completion
publication.** `scripts/source_interpreter_fit.py:459` samples `monotonic`
before writing the stage receipt, current-stage receipt and append-only history.
Generation (`:697`) and training (`:1473`) then treat that pre-write timestamp
as the completion/publication time. `validate_completion` (`:917`) accepts the
same timestamp. Meanwhile, `supervise_child` (`:1126`) applies a stage's hard
deadline only while current-stage status is `INTENT`; seeing `COMPLETE` drops
the stage reservation even if its publication was late or later required
publication is still blocked. The whole-process ceiling does not establish the
separate 1,220/300-second stage bounds.

Independently reproduced this through the actual `run_generation_pair`
consumer with the existing CPU model/tokenizer fakes. A mutable monotonic clock
starts at zero. Only the write of `stage-generation_base.json` with status
`COMPLETE` advances it to 301 seconds before publishing the file. With the
registered 300-second reservation, the actual consumer nevertheless returns
`COMPLETE`, makes **both** generator calls, and records base
`deadline_reached=false`. The durable base stage says `status=COMPLETE`,
`monotonic=0`, `elapsed_seconds=0`, `hard_deadline_monotonic=300`. This is a
missed-deadline success, not merely an imprecise latency field. No model, GPU or
real sleep was involved. The exact executable reproduction was supplied to the
parent, which independently reports the same result.

**Required correction:** keep each stage reservation externally enforceable
until its required durable completion is observed; distinguish timestamps
sampled before writes from observations after those writes. Late or blocked
publication must leave the stage incomplete and prevent a subsequent generation
call. Add a consuming regression that delays completion publication itself,
covering the shared training/generation completion mechanism rather than only
an `INTENT`-stage hang. The initial training reservation must also be enforced
from supervisor launch during pre-child qualification: `main` (`:1793`) charges
qualification to an internal clock, but no child-stage watchdog exists until
the child publishes training intent. A root outer observer can supply that
initial enforcement; its launch contract must cover it explicitly, alongside
the existing whole-process bound. This is the already accepted stage contract,
not a new deadline or prerequisite experiment.

**Finding 2 — medium, OPEN. The recorded “resolved generation configuration”
is not the configuration Hugging Face resolves.** In
`scripts/source_interpreter_fit.py:575`, `resolved_generation_config` is a
manual overlay of the checkpoint object's `to_dict()` and all explicit kwargs.
It omits library default resolution and input-dependent preparation and mixes
generation configuration with forward/control arguments such as
`logits_to_keep` and `synced_gpus`.

Installed Transformers 5.16.1 primary code supplies a concrete mismatch:
`generation/configuration_utils.py:390` initializes omitted `max_length`,
`min_length` and `repetition_penalty` to `None`;
`generation/utils.py:1771` fills library defaults, including 20, 0 and 1.0,
respectively. `_prepare_generated_length` then derives **max_length=5,014**
from the 2,966-token prefix plus the 2,048-token allowance. The runner's overlay
retains unresolved values instead. The existing fake config contains only a
small checkpoint dictionary and never exercises native resolution, so its
green generation tests do not qualify this receipt field.

**Required correction:** preserve the native resolved configuration actually
used by the call, including applicable derived lengths, while recording explicit
forward/control arguments separately. Add a consumer check with unset checkpoint
fields that would acquire native defaults. Retain the same registered decoding
settings. This finding concerns accurate required evidence; the explicit
greedy/single-EOS kwargs themselves are compatible and do not require a recipe
change or a model warm-up.

**Finding 3 — medium, OPEN. Failure summaries label known unstarted calls as
unavailable.** `scripts/source_interpreter_fit.py:1029`
(`_partial_generation_calls`) assigns `UNAVAILABLE` to every missing generation
file, without consulting the durable stage history or fixed call order. It is
the actual lifecycle consumer used by `supervise_child` (`:1220`). Thus a
training failure/hard timeout reports both generation calls as unavailable,
and a hard timeout during base generation also reports the never-started
adapter call as unavailable. The explicit pair exception path writes
`NOT_ATTEMPTED` correctly; the externally terminated path cannot reach it.
The existing hung-training test exercises precisely the missing-file case but
does not check its generation classifications.

**Required correction:** use durable generation intent and the fixed order to
distinguish calls known not to have started from an in-flight or unresolved
call whose output is unavailable. Keep unknown output unknown. Add failure-path
consumer assertions for a training stop and a hard stop during base generation.
FIT.md explicitly requires unstarted calls to be marked `NOT_ATTEMPTED`; this
distinction makes the partial-work accounting usable without inventing a zero
response or treating all absent files as attempted requests.

### Verified implementation behavior

The core recipe follows the accepted proposal. Qualification verifies accepted
hashes and all eighteen rows through the existing source-binding/causal-label
consumer, checks source order and all 54 scheduled token totals, and binds the
runtime interpreter/package environment. The historical accepted specification
review is verified through its fixed Git blob; current review/code hashes are
recorded dynamically. This avoids a current-review hash cycle. Root's later
launch manifest still needs to pin the final accepted code review.

Inspection of the actual training loop confirms that each schedule item selects
`rows[item['row_index']]`, constructs that row's full input/attention/label
tensors and performs one optimizer update. Each step's durable intent includes
ordinal, epoch, row/query identity and causal loss positions. The first update
is part of 54. The reused numerical/optimizer and partial-update checks retain
confirmed versus unknown optimizer completion. Frozen original initialization,
fresh FP32 q/v LoRA, standard final save/byte archive/reconstruction and complete
adapter-state comparison follow accepted mechanics; no mechanics adapter is
loaded and no extra post-reload target-loss forward is added.

The two actual generation invocations receive only prefix IDs and all-ones
attention, with no labels or supplied past cache. The first call uses
`disable_adapter`; the second explicitly activates `roundtrip` in inference
mode. Runtime layer-state checks and original-trunk identity receipts accompany
the calls. The final original-parameter check spans training and generation.
Installed PEFT/HF source inspection supports these interfaces, including the
plain Boolean monotonic stopping criterion consumed by `StoppingCriteriaList`.
No live HF generation was performed in this review.

Returned full and suffix IDs, terminal EOS handling, strict full-document
structure/citation parsing, unmodified decoded UTF-8 bytes/hash and separate
stop facts follow the specification. Invalid JSON or an ordinary returned cap
still permits the second preplanned call; an ordinary technical exception or
observed generation deadline stops it. Whole-call synchronization/timing is
appropriate and makes no isolated decode-rate claim. Findings #1–#3 identify the
remaining deadline and receipt gaps; they do not justify per-token hooks,
semantic repair, another pilot or broader infrastructure.

### Independent validation and boundary

Ran `.venv/bin/python -m pytest -q tests/test_source_interpreter_fit.py`:
**8 passed in 0.83 seconds**. This includes import checks excluding torch,
transformers and PEFT; a dry invocation that creates no run; and actual absolute
direct-file artifact qualification from a temporary working directory with
`PYTHONPATH` removed, returning 18 rows/54 updates without a model load. Ruff
check, Ruff format check and `git diff --check` passed. The additional bounded
CPU publication reproduction above exposes a case absent from those eight
tests. No frozen mechanics suite or full pytest suite was rerun.

No actual FIT job, weights read, ML runtime import, GPU/model operation,
generation, network access, semantic authoring, preview regeneration or excluded
evaluation-bank access occurred. Only this canonical review was changed; no
implementation, specification, ledger edit or commit was made. Correct the
three findings, then request a focused delta review before the prospective
single-run freeze. Fresh semantic comparison and larger executable coding
utility remain unestablished; this is code review, not execution or utility
evidence.

## Round 3 — findings 1–3 correction review, 2026-09-08

**Score: 96/100. ACCEPTED — runner implementation. Zero open findings,
including zero high or critical findings.**

Same independent native **gpt-6-astra, xhigh** session and user-directed reviewer
substitution. This round checks the three corrections and their consequences;
the accepted recipe and earlier scientific scope remain unchanged. Rounds 1–2
and finding identities are preserved. This is code acceptance, not an actual FIT
run result, transfer evidence or coding-utility result.

Reviewed stable Sol correction commit
`6949d66a8f2544a14f2a5c6d7c4286ed717fe084` and independently checked:

| Artifact | SHA-256 |
| --- | --- |
| `scripts/source_interpreter_fit.py` | `fe526cc2fe61c183f2a2c4d5db801f8ac684c2f7ad8db7f01980994212c5ee36` |
| `tests/test_source_interpreter_fit.py` | `b875ab92e37a50630ab99ddbf3c26afef4f57335d467af3b4fd6b3fe7ca8027e` |
| `results/source-interpreter/FIT-FIX-BRIEF.md` | `3743f7f9950d9e2bfe3ab731d40aba8ce56de1272a1e9ff0c6bac039d348c959` |
| Unchanged `results/source-interpreter/FIT.md` | `f1f306e9ccac968013568dd6f0ed46a42d6df7297105c7a2531a83b7caa541a7` |

**Finding 1 — high, resolved 2026-09-08.** The shared `_publish_stage` path now
keeps `current-stage.json` at `COMPLETION_PENDING` while writing terminal
evidence. It samples after the required completion-record writes, checks again
after publishing the observation records, and converts late completion into
`DEADLINE`. The current stage remains pending until the next stage's durable
intent or child exit; a prematurely visible per-stage `COMPLETE` file therefore
does not disarm inner supervision. The supervisor enforces both `INTENT` and
`COMPLETION_PENDING`. Training, generation, cleanup and finalization consumers
use the corrected completion checks, and late generation publication sets the
deadline fact and stops the fixed pair before its second call.

The consuming regression for the original 301-second publication defect now
returns `INCOMPLETE_DEADLINE`, invokes the generator only once and preserves
the base stage as `DEADLINE`, with a post-write observation of 301. Independently
exercised the actual supervisor with an owned dummy child that leaves its
per-stage file `COMPLETE` but current stage `COMPLETION_PENDING`, then hangs.
The supervisor reports `INCOMPLETE_STAGE_TIMEOUT` for `generation-base`,
confirms/reaps the child and clears its flag; measured observer lifecycle was
0.201464086 seconds under this small synthetic reservation. This directly
qualifies pending-publication supervision rather than relying on an unchanged
intent-only test.

The corrected dry plan explicitly requires the root observer to start before
supervisor launch and enforce the initial **1,220 seconds through pre-child
qualification and durable training completion**, as well as the entire
2,400-second process bound. The parent supplied its concrete observation rule:
check the initial deadline before accepting a durable transition to either
registered generation stage, which the fixed child can reach only after the
training completion check; retain the initial bound until that transition or
earlier supervisor exit. This conservatively avoids trusting a prematurely
visible per-training completion file. That division of responsibility satisfies
the initial-bound correction. The actual outer observer and its launch bindings
still must be frozen and verified before execution; this report does not claim
they have already run.

**Finding 2 — medium, resolved 2026-09-08.**
`_native_resolved_generation_config` now invokes the installed native
`_prepare_generation_config` and `_prepare_generated_length` with the same
checkpoint configuration, configuration kwargs and actual prefix length used
by the subsequent ordinary generate path. Forward and control kwargs are
recorded separately. Read the installed `GenerationMixin.generate` preparation
sequence and PEFT delegation to check this agreement: for the registered
decoder-only input-ID call, absent user config, fixed single return/beam and
unchanged settings, the resolver receives the same effective configuration
inputs and derives the same length. It does not change the generation recipe.

The consumer test now uses the installed `GenerationConfig` and actual native
resolver methods, rather than a fake manual overlay. It confirms inherited
`None` fields resolve to `min_length=0`, `repetition_penalty=1.0` and
`max_length=5014`, while `logits_to_keep` and `synced_gpus` remain explicit
forward/control arguments. Both calls retain the prescribed prefix-only
inputs, greedy/single-EOS settings and adapter modes. These are CPU
configuration/API checks, not a live native model-generation measurement.

**Finding 3 — medium, resolved 2026-09-08.** The actual partial-generation
lifecycle consumer now consults the durable per-generation stage receipt when
an output file is absent. No stage intent means `NOT_ATTEMPTED`; an existing
stage with unavailable output means `UNAVAILABLE`, with availability unknown.
This matches the fixed call order and the producer's rule that durable intent
precedes invocation. The training-stop consumer test confirms both calls are
`NOT_ATTEMPTED`; the new base hard-stop consumer test confirms base
`UNAVAILABLE` and adapter `NOT_ATTEMPTED`. The independent pending-publication
dummy check also produces that latter classification. No missing response is
converted into zero generated tokens.

Independent validation: `.venv/bin/python -m pytest -q
tests/test_source_interpreter_fit.py` **10 passed in 2.69 seconds**. Ruff check,
Ruff format check and `git diff --check` passed. The targeted suite includes
the actual absolute direct-file artifact qualification from a temporary working
directory with `PYTHONPATH` unset, plus import/dry checks that keep ML imports
and run creation out of those non-executing paths. The native configuration
tests import the installed HF/Torch Python dependencies on CPU; they instantiate
no model and invoke no CUDA work. The additional pending-publication supervisor
check imports no ML runtime. No frozen mechanics or full pytest suite was run.

Read the complete runner/test delta: the 54-row schedule, actual loss/update
loop, fresh adapter, standard FP32 archive/reload equality, original-parameter
checks, two prefix-only calls and strict unchanged-output handling retain their
round-2 behavior. No new finding or regression was identified. Only this
canonical review was changed; no code, specification, ledger edit or commit
was made. No weights, model/GPU operation, semantic generation, network, new
data, preview regeneration or excluded evaluation bank was accessed.

The next step is the prospectively bound single run with the required root
observer, followed by independent review of its actual evidence. Acceptance
here establishes readiness of the reviewed runner under that launch contract;
fresh semantic comparison and adequate larger executable coding proof remain
separate, unestablished requirements.

## Round 4 — concrete outer-observer review, 2026-09-08

**Score: 96/100. ACCEPTED — prelaunch outer monitor. Zero new or open
findings, including zero high or critical findings.** Findings #1–#3 retain
their round-3 resolutions; all prior rounds are preserved. Same independent
native **gpt-6-astra, xhigh** session and user-directed reviewer substitution.
This narrow round verifies the actual orchestration tool and its existing
dummy-process receipts under the division of responsibility accepted in round
3. It does not reopen the frozen ML runner or accept an actual FIT result.

Reviewed root process-tooling commit `2c65507d` and independently checked:

| Artifact | SHA-256 |
| --- | --- |
| `tools/observe_source_fit.py` | `e04b4cc839d3d906f9ff85513b495c6e0cebcdd63c45cd9413819675679790ee` |
| `results/source-interpreter/fit/observer-qualification.json` | `fb8f8297fb9b2ff9d6c153bfe2314777ed47248243a2d547cc5dbcb63527bbc6` |
| Unchanged `scripts/source_interpreter_fit.py` | `fe526cc2fe61c183f2a2c4d5db801f8ac684c2f7ad8db7f01980994212c5ee36` |

**Initial and whole-process bounds.** The observer takes its initial monotonic
sample before launching the supervisor, so pre-child qualification is included.
It retains the initial deadline until it observes `generation-base` or
`generation-adapter` at `INTENT`/`COMPLETION_PENDING`, checking time again after
reading the durable stage file and before accepting that transition. The
accepted fixed child can reach either stage only after its training completion
check. A per-training `COMPLETE` file alone does not release the outer bound.
Confirmed whole supervisor exit within the initial interval also establishes
that bound. The loop otherwise retains the whole deadline, with successful
termination requiring actual elapsed time within 2,400 seconds. The interval
ends after confirmed supervisor exit and any required owned-group cleanup,
therefore includes the supervisor's final publication and exit tail.

**Ownership, failure and launch behavior.** `Popen(start_new_session=True)`
creates the observer's own private process group; the accepted supervisor's
model child inherits it. The observer registers itself and its launched
supervisor and signals only that known group. Timeout/error handling terminates
the owned group and waits for its supervisor; receipt fields retain actual
elapsed time and incomplete status. Success additionally requires zero
supervisor exit, inner lifecycle `COMPLETE`, confirmed model-child exit and an
absent owned group. Cleanup latency following timeout is measured and cannot
turn an exceeded reservation into success. No retry path exists.

The tool has a main guard and only standard-library imports. Its default mode
checks the supplied artifact sizes/hashes and launches no process. Actual
execution requires explicit `--execute`, `FROZEN_READY` and an accepted-review
entry. The reviewed launch manifest is still a draft; root must bind the final
canonical review hash, exact command, tool and inputs in the final frozen
manifest before invoking execution. This review does not treat draft metadata
as launch authority or claim that the tool independently grades review prose.

**Qualification reconciliation.** Read the three recorded dummy commands and
their actual consumer receipts, recomputing elapsed and reservation arithmetic:

| Case | Initial / whole reservation | Actual elapsed | Recorded outcome |
| --- | --- | --- | --- |
| Initial timeout | 0.12 / 1.0 seconds | 0.121301820 seconds | `INCOMPLETE_INITIAL_TIMEOUT` |
| Whole timeout after generation-stage observation | 0.5 / 0.8 seconds | 0.803450375 seconds | `INCOMPLETE_WHOLE_TIMEOUT` |
| Ordinary completion | 0.5 / 1.0 seconds | 0.073729666 seconds | `COMPLETE_UNREVIEWED` |

Both recorded transitions precede their initial deadlines; the first timeout
has no transition. Timeout exit codes are -15; successful exit is zero with
the required inner lifecycle. All receipts report confirmed exits and absent
groups. Observer/supervisor IDs are present in the ownership registry, and the
three exact supervisor PIDs are currently absent. This audit reconciles the
existing recorded process qualification; it does not claim a second live group
measurement during those historical runs.

Independently invoked the actual observer CLI without `--execute` against the
current draft manifest: **PASS, launch bindings checked; no process launched**.
Parsed the stable tool as Python and inspected its full execution path. The
recorded three consumer runs and direct dry qualification cover this small
monitor's relevant behavior; no redundant dummy runs, ML tests or full suite
were needed.

Only this canonical review was changed. No code/specification/ledger edit,
commit, process launch, model/weights/GPU operation, ML runtime import, network,
new data or evaluation occurred in this round. The root may now complete the
prospective manifest freeze and perform the one registered FIT job under the
accepted monitor. Actual run evidence still requires independent audit, and
neither prelaunch acceptance nor FIT-only cost evidence establishes fresh
semantic transfer or adequate larger executable coding utility.

## Round 5 — actual fixed-FIT result audit, 2026-09-08

**Score: 96/100. ACCEPTED — recorded training/persistence and two-call cost
measurement, with the trained FIT response explicitly FAILED. Zero new or
open findings, including zero high or critical findings.**

Same independent native **gpt-6-astra, xhigh** session and user-directed
reviewer substitution. All earlier rounds and finding identities remain intact;
findings #1–#3 retain their prior closures. This round audits actual evidence
from the one frozen job. It accepts neither semantic generalization nor coding
utility, and does not authorize retry, repair, cap changes or a new evaluation.

Reviewed launch freeze `fe1d0112` and result archive `7721e52e`. Exact principal
artifact bindings, under `results/source-interpreter/fit/`:

| Artifact | SHA-256 |
| --- | --- |
| `launch-plan.json` | `396632617e32ea11c250b5d291dcf2030e88c1d75dae623a73d89ae3aff4b097` |
| `observer-01.json` | `e1d8de7af3b8466646f9bbabf595ef578d62bf7f83ae574bafea0bb1fe2679ed` |
| `run-01/result.json` | `ce2b1e435ce064f4e185011c7096fba6cb53c0efab41e4986b153aa0132ffd11` |
| `run-01/lifecycle.json` | `d7d655363b891dbd1ee467f9f0c2079d31b5817e60e59bc1101a066af992f558` |
| `run-01/steps.jsonl` | `d68c1346aa9e8b1c1b190946790be34ab1abcf97ec9d6ff3a828f1591454f36b` |
| `run-01/generation-base.json` | `964e3373befcf9766fcecfb2d0e32b51a2dfe1b92f16e30306fa43f0ba602a19` |
| `run-01/generation-adapter.json` | `08ffd4816857eb4a6feea10eccc49544883ce814afde9fb29e3327c6dc22ca53` |
| `run-01/archive-manifest.json` | `836c2966ce253ad1b783a262faa4b0f2ef4f2379924f614999013ec6feaa0807` |
| `root-reconciliation.json` | `49e46e3335481c7136d7b23ab4f7a321862f295b36d509796c6e3d6623e04587` |
| `RESULTS.md` | `139d2be96bf9d4cdb95c7949630a4d7afea758054712d9b586a558a38accbe03` |
| `adapter-description.md` | `57e07003b64e388c60bbd6a2a95f406e24d450e32789f50464e213528cb68c3d` |

### Launch, lineage and fixed updates

Independently matched all thirteen launch-bound artifacts to both current bytes
and the frozen Git blobs. The manifest itself matches its freeze, is
`FROZEN_READY`, specifies one attempt with no automatic retry, and binds the
round-4 prelaunch review hash
`7997820c7bb5aee2b4b6940a21041be51d1ac64e091517f8cf7799fd5b8e867e`.
The runner and observer remain the accepted hashes from rounds 3–4.

All seventeen runtime artifact bindings reconcile, including the historical
round-1 review blob and the current-at-launch round-4 review. Start/result
bindings agree, with the expected change from base-file verification pending
to completed. The recorded original asset hash map matches the qualified base
receipt. All six canonical FIT source files match their frozen bytes, manifest
hashes, identities and runtime input receipts. The saved preview is unchanged.
No DEV, withheld or benchmark material appears in this registered input chain.

The saved schedule exactly matches the frozen runner's three eighteen-row
orders. Independently reconciled every step's ordinal, epoch, position,
conversation/query identity, full/prefix length and causal loss positions with
its selected preview row. Totals are **54 updates, 89,343 sequence tokens and
21,702 supervised target/EOS tokens**. Each of the 270 history records belongs
to the correct step, with ordered `INTENT`, `UPDATE_PENDING`,
`UPDATE_CONFIRMED`, `VALIDATION_CONFIRMED`, `VALIDATED` transitions; each final
record equals its final step file and the result's hashed reference.

All recorded losses and aggregate adapter gradient/update norms are finite and
positive. Optimizer membership, absent original gradients and original identity
checks pass; update completion is known and validation/resource records are
complete. Each adapter after-hash map equals the next step's before-hash map.
There is no unresolved update attempt, extra warm-up update or checkpoint
selection in the accepted execution path or its recorded history.

### Original trunk and final adapter bytes

The complete recorded original before/after hash maps agree for **398 tensors,
4,022,468,096 parameters**, with successful runtime identity and absent-gradient
checks. This reconciles the accepted runner's recorded endpoint verification;
it is not an independent second live-weight measurement or a per-step original
byte check. No original weight shard was opened or rehashed during this audit.

Independently concatenated the two tracked archive parts in memory and checked
their individual sizes/hashes, reconstruction order and full identity with both
local standard checkpoint files. The final adapter is **11,815,504 bytes**, SHA
`1f9392f3fa99cb31a010176487a6f37999f02cdbc7be9b9cdb4a9b9380e592e3`.
The 9,000,000- and 2,815,504-byte parts reproduce it exactly.

Parsed the safetensors header and independently hashed every tensor's payload.
All **144 FP32 payload hashes** match both the saved-state receipt and the
canonicalized final optimizer-step hashes. Offsets are contiguous and cover
the complete payload. Shapes are 72 A tensors `[8,2560]`, 36 q-projection B
tensors `[4096,8]` and 36 v-projection B tensors `[1024,8]`, totaling
**2,949,120 parameters**. Both adapter configurations are byte-identical, with
hash `45f10d86fd18dc5d5f4c748b1b9c59f292f7fc92f6f6334e21dff9255f9a70b2`.
The runtime standard reload records exact complete state equality and no
missing/unexpected keys. The fresh full-FIT adapter is distinct from the earlier
mechanics checkpoint; that old adapter was not read during this audit.

### Raw generation evidence and failure interpretation

Both saved calls use exactly the accepted **2,966-ID row-14 prefix**, followed
only by the returned generated suffix. Complete/suffix/payload ID relationships
reconcile, with no target/labels or supplied past cache. The original-trunk
object identity matches between calls. All 72 recorded adapter layers are
disabled for base generation; adapter generation explicitly records only
`roundtrip` active on each enabled layer. Explicit settings and native resolved
configurations agree across the calls, including the registered greedy/single
EOS settings and resolved `max_length=5014`.

Using only the hash-verified original tokenizer JSON and standard-library byte
operations, independently inverted its recorded ByteLevel vocabulary and
decoded each payload's token IDs. Both reconstructions exactly match the saved
text, base64 UTF-8 bytes, lengths and hashes. No tokenizer/model object or
scoring script was loaded. Independently checked complete JSON structure,
duplicate-key/constants rejection and visible source citations; no target
semantic comparison or obligation-correctness score was computed.

| Fixed call order | Generated IDs | Recorded whole-call time | Independently checked outcome |
| --- | ---: | ---: | --- |
| Base, adapters disabled | 703 | 40.517819119 seconds | Terminal EOS; complete valid document and visible citations |
| Reloaded trained adapter | 2,048 | 123.050696406 seconds | No EOS; token cap; incomplete JSON |

The base payload is 2,867 UTF-8 bytes, SHA
`efacbadb8fe1af1ed71a624cc4d29f6b61d0529af84e21451722c14470aadd0a`.
The trained payload is 9,115 bytes, SHA
`4723de47fbed7d877858adcdea23d9f15dca77d2431aff93559ed7046116a820`.
Its strict parse fails on an unterminated string beginning at character 279,
consistent with the retained error. All EOS/cap/deadline facts and result
summaries agree with the raw receipts. **The trained response failed.**
Technical completion and measured cost do not change that outcome. Base
structural completion also does not establish correct instruction selection.
No semantic repair, extraction, cap retry or new-conversation evaluation is
part of this evidence.

### Deadlines, resources, exit and archive

Recomputed whole outer elapsed time as **351.821924262 seconds**. Its durable
initial-training transition was observed by **161.890731962 seconds**, within
1,220; the whole process is within 2,400. The inner lifecycle is
351.619755533 seconds. Outer observation extends **0.065214376 seconds** beyond
inner finalization, covering the final supervisor publication/exit tail. The
350.190441937-second child field has the narrower scope correctly stated in
RESULTS.md.

All twenty stage-history entries reconcile with the five final stage receipts;
ordered completion observations satisfy their registered deadlines. Both
generation stages complete within 300 seconds. The adapter's failure is a token
cap/format failure, not a time-reservation failure. The raw log retains the
model-loading progress and inactive-`top_k` warning; it contains no recorded
retry or corrective settings change. The observer's terminal log agrees with
its receipt and the parent's report that exact session 67209 exited zero.

Pre-cleanup Torch peaks are **16,003,383,808 allocated bytes**
(14.904312611 GiB) and **27,353,153,536 reserved bytes** (25.474609375 GiB).
These are recorded allocator peaks on GB10 unified memory, not total process
memory or a separate NVML pool. Runtime records Python 3.12.13, Torch
2.13.0+cu130, Transformers 5.16.1 and PEFT 0.20.0. Observer/supervisor/model-child
PIDs 165749/165750/166299 are registered and currently absent; the run flag is
absent. The receipts confirm both process exits and an absent owned group.
The root's post-run GPU-empty observation is reported as its observation;
this audit made no GPU query or context.

All **85 tracked FIT artifacts** match result-archive Git blobs and are at most
10,000,000 bytes. The two 11.8 MB standard checkpoint copies remain local and
untracked; their exact archive parts/configurations are tracked. The prose
reports and root reconciliation accurately characterize the checked evidence.
Their review-pending wording is the preserved pre-audit state; this round
supplies acceptance without revising those historical bytes.

Only this canonical review was changed. No code/specification/ledger edit,
commit, model rerun, original-weight read, GPU operation, ML runtime import,
test-suite rerun, network, data authoring or excluded evaluation-bank access
occurred. The useful result of this unit is a fixed trained adapter, measured
costs and an unrepaired capped FIT failure. Fresh semantic comparison and
adequate larger executable coding proof remain separate requirements; no
perfect-FIT prerequisite or broader success claim is introduced.
