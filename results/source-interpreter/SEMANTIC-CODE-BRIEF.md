# Bounded source-semantic consumer implementation

2026-09-08. Sol xhigh, native competence_launcher_impl. Implement the accepted
SEMANTIC.md, SHA d892196fc32ed1e670152dc5904a50bac854d78dda82222f4da95e4c6b2826e5.
Specification accepted by semantic-review-astra.md round2 at96/100, no open
findings, historical SHA84d75b07cce791b1028b998bbc1887c2298e35a5a05442bfa5db1c8161e90f27.
This brief authorizes CPU implementation and synthetic tests, not data/model use.

Fit-on: unchanged fixed18 FIT rows already consumed by the frozen final adapter.
Evaluated-on: six new withheld families being authored independently now, three
queries each; no DEV. Do not read any semantic/author-*/authored.json or raw
responses, actual labels, old banks, benchmarks, old adapters or model outputs.
Only prospective request metadata and accepted specs are implementation inputs.
Synthetic consumer fixtures are not ML training/evaluation material.

## Allowlist and deliverable

Write and commit only scripts/source_interpreter_semantic.py and
tests/test_source_interpreter_semantic.py. No wrappers. Your native task has no
wrapper lock; no review/coder wrapper is active. Do not edit frozen source/FIT/
mechanics/observer code, semantic spec, data, reviews, ledger or other files.
Main-guarded, import-safe, standard-library qualification/default paths; lazy ML
imports only inside the explicit model child. No new framework or dependencies.

Implement only CPU preparation and the36-call inference consumer/lifecycle.
Semantic judgments are later source-grounded Astra/Kimi reviews, not regex or
string-equivalence scoring. Do not build a general semantic judge, UI, native
tool server, trainer, retry policy or new control language.

Reuse the reviewed original source helper for validate_corpus/prepare_rows and
format/tokenizer checks. Its preview() is deliberately FIT-only: do not invoke
it on withheld or mutate constants. Reuse FIT run_generation_call and safe
mechanics byte/state helpers without invoking either experiment's main or
mutating module globals. Absolute-file invocation from /tmp with PYTHONPATH
unset must work through installed stencil.focus imports.

Provide a dry-by-default command and a distinct explicit CPU prepare path that
consumes a root-frozen accepted-input manifest after later label acceptance.
Root will supply that manifest; define its small exact schema and document it
in help/dry output or your handoff. Binding must identify exact accepted spec,
review, six file paths/hashes/withheld IDs and original asset receipt. Reuse
metadata instead of expecting a future review hash hardcoded into code: bind
historical accepted review bytes by Git blob and current review dynamically at
freeze, with no post-review source edit/hash cycle.

Preparation records all18 rows/identities/hashes/actual source-prefix lengths,
unchanged tokenizer state/templates/environment and target lengths without
truncation. Prefix+2048<=32768; whole packet ineligible on violation. Emit a
generation manifest with prefix IDs, source prefix/visible IDs, identity, fixed
order and settings but NO targets/labels/target-derived completion sequence;
emit reference/length material separately. Actual generation child reads only
the frozen generation manifest and model/adapter assets, never reference files.
Bindings can hash a reference artifact as inert bytes only if necessary, but
no gold parsing/model input is allowed in generation. No bank-dependent settings.

Verify the loaded standard final FP32 adapter against the exact tracked parts
and configuration/manifest from fit/run-01, complete144 payloads/2,949,120
parameters and SHA1f9392f3fa99cb31a010176487a6f37999f02cdbc7be9b9cdb4a9b9380e592e3.
Never initialize or train a new adapter. Load original BF16 Qwen3-4B once under
the fixed local environment, SDPA, cache enabled, eval/inference mode and
checkpointing disabled. Verify original and adapter bytes/identity before/after
the actual job; no original-weight or adapter file is loaded by your coder task.

Run fixed rows0–17 in order; even rows base then adapter, odd rows adapter then
base. Empty cache every call; same original trunk; no merge/warm-up/extra call.
Use existing single-call generation settings exactly. A per-row run directory
can prevent fixed generation-base/adapter filenames overwriting prior receipts.
The row passed to the call needs source_prefix for citation checks plus query
identity/prefix IDs; it must not contain gold labels. Preserve helper receipt
kind as a legacy label if reused, with honest outer semantic metadata.

## Owning execution and evidence

Explicit execute only after root freeze/accepted implementation. Own one model
child, register PIDs, respect current flags/review lock and never signal another
process. Whole3600sec including final supervisor publication/exit, startup660sec
from before supervisor launch through durable first generation intent, each
generation300sec including durable publication, final15sec cleanup reserve.
Whole bound wins. Handle post-Popen errors with owned cleanup and durable
partial state. Never poll your own lock. No automatic restart or retry.

Per-query directories mean current-stage observation needs explicit wiring;
existing FITsupervise_child cannot blindly observe its old single root path.
Use the smallest correct active-query/stage path contract, exercising its real
consumer with synthetic subprocesses. Existing tools/observe_source_fit.py is
configurable for initial/whole bounds and observes root current-stage.json
generation-base/adapter status; reuse its owning observe(plan) if the correct
root-stage contract can be supplied without source edits. Its historical field
name initial_training_* may represent this startup bound only with explicit
semantic receipt documentation; never claim training occurred. If reuse cannot
remain small and correct, report a concrete interface need to root rather than
copy a framework or weaken whole-process coverage. Root owns final external
observer freeze/launch; coder task must not launch it on actual assets.

All36 scheduled work records must exist in terminal accounting, distinguishing
returned outputs (including observed cap/format failures), technical errors,
unavailable in-flight output and known not-attempted work. Never zero unknown
tokens/time or call unknown a semantic loss. Stop on technical exception or
deadline; continue fixed schedule after ordinary returned malformed/capped
output. COMPLETE requires all36 returned within bounds, required receipts and
confirmed cleanup; otherwise INCOMPLETE with no inference/advancement eligible
flag. Post-look label ineligibility is applied by later assessment, never by
changing model receipts. Do not implement p-values or semantic success here.

Record exact frozen bindings, settings/state, per-call input/output IDs and
bytes, counts, whole latency, stage clocks/publication and resources, plus
whole supervisor lifecycle and exact/unknown performed work. Root outer
observation covers final publication/exit, so expose the actual contract in
the dry plan. No artifact over10MB may be committed; standard full checkpoint
stays local, no new checkpoint copy is needed merely for inference.

## Targeted verification and handoff

Write red-first meaningful consumer tests for: withheld lineage/identity/hash
and prompt-target separation; all18 prefixes/settings and deterministic36-call
order without overwrite; real single-call invocation per row/mode; ordinary
cap continuation; technical stop leaves later calls not-attempted; deadline
while a nested stage is publishing is observed by the actual supervisor; whole
tail/cleanup/unknown output accounting; complete eligibility rejects35returned
plus one unknown even if partial counts would look favorable. Use bounded fake
model/tokenizer primitives and owned tiny CPU subprocesses; no full pytest or
repeated unchanged FIT suite. Include direct absolute-file CPU qualification
from /tmp with PYTHONPATH unset and import/no-heavy-runtime check. No real
withheld preparation/tokenization until root's later accepted data invocation.

Acceptance commands: repository .venv Python -m pytest -q
tests/test_source_interpreter_semantic.py; Ruff check/format on the two allowed
files; git diff --check; direct help/dry/CPU qualification. Report initial red,
final results, exact consumer schema/commands, code/test hashes and explicit-path
commit to root. No ledger edits. Independent same-topic Astra code review follows
your stable handoff before any actual target-model job. Adequate larger coding
proof remains required and is not replaced by implementation acceptance.
