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
