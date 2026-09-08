# Sol xhigh brief: staged Kimi preparation only

2026-09-08. DRAFT pending prospective-spec acceptance. Native Sol xhigh as Brian
requested; no wrapper. Root owns documents, generated request configuration,
ledger and commits. Write no scientific data or authoring outputs during coding.

Implement PREPARATION.md and its exact two prompt templates with the smallest
preparation-only code. Preserve the old stopped bank and all qualified helpers.
The scientific selector/worker/driver/launcher are not this work unit. The new
launch-binding update is deferred until fresh data passes preparation; it must
not be forgotten or bypassed when the screen is later considered.

Fit-on none. Implementation tests use isolated hand-written mechanical fixtures,
not old bank content, benchmark examples or prospective evaluation artifacts.
Do not read any author-*/authored.json or response.json, call a model/API/server,
start a container, load weights, use a real tokenizer or acquire data. Root will
run accepted actual authoring/CPU validation later, once, on wholly fresh data.

## Allowlist

- src/stencil/source_replay_authoring.py (new pure assembly/validation)
- tools/prepare_source_replay.py (new main-guarded transport/driver)
- tests/test_source_replay_authoring.py (new)
- tests/test_prepare_source_replay.py (new)
- src/stencil/source_replay_screen.py and tests/test_source_replay_screen.py
  only if a small extraction is necessary to reuse partial validation; preserve
  full-project behavior. Prefer reusing its existing helpers without edits.

No other files, review files, ledger edits or commits. Record any proposed scope
change to root before making it. Do not wait for .review.lock; no wrapper is used.

## Required behavior

Pure functions strictly parse author content, validate scaffold/packets, render
fixed prompts once, assemble the existing project schema, and maintain cumulative
reference state. Reuse actual contract checks and consume_action/run_checks;
never fabricate later rounds to pass a full-project validator or use a separate
toy execution path. Each accepted stage's original parsed fields are immutable.
Source text, code, rationales and expected values come only from Kimi. Local
assembly supplies administrative metadata and the registered request template.
Keep lineage separately until final assembly, without dropping or rewriting it.

Driver CLI: --run-dir with an absolute new directory, --freeze for an exact
root-authored preparation manifest, --execute opt-in. Without --execute, print
the sixteen-slot plan and required subject paths/hashes; no network calls or
output-directory mutation. A compact JSON freeze binds exact PREPARATION.md,
both prompts, inherited DATA-CONTRACT/SPEC, executed preparation code and reused
validation/action/sandbox dependencies, and independent current code-review
evidence. Freeze schema/path/hash validation is required; root checks actual
latest review disposition before launch. Do not create a second review parser
or a general workflow/approval framework for this data-preparation command.
Report the exact freeze shape and subject list to root before it freezes a run.

On execution, reject nonempty/existing run directories and changed/missing freeze
subjects before requests. Register owned PID before calls. Create an initial
durable job record listing all16planned slots and fixed options/deadline, then
perform the four stage barriers. Independent projects may run concurrently,
dependent stages never do. Check whole-job time before HTTP, validation and
positive final publication. Per-request time uses the remaining whole deadline,
at most450seconds; no stage resets. No retry, fallback or repair, including
transport errors. If one stage fails, finish preserving already-launched calls
and leave all later slots unattempted. Never treat an observed tool timeout as
permission to restart a still-running job.

Use urllib or existing installed standard-library facilities; no packages. Save
exact request bytes before POST, response bytes before interpretation, hashes,
HTTP/done status, reported token counts, final/thinking sizes, timestamps and
terminal stage/whole-job states. Model thinking remains separate evidence, never
input to later authoring. Reject unsuccessful/incomplete envelopes and strict
content violations. Do not reinterpret normal done_reason as content validity.
No automatic removal of Markdown fences, duplicate-key acceptance or brace repair.

Execute only accepted pure-function code through the existing isolated action and
sandbox consumers. Record all actual active check results, reference state hashes,
and stage3 mutant validity/designated failure. Future instruction visibility for
expiry must not expand source-ID visibility; semantic prefix grounding remains
for independent source review. Use actual consumer output, no copied PASS flags.

Assemble four final authored.json files with the unchanged public/private schema
only after all stages pass. Whole-job terminal status is PREPARED_UNREVIEWED,
INELIGIBLE or INCOMPLETE with a concrete reason; never ACCEPTED or a scientific
PASS. A separate final screen preflight is later required to validate assembled
bytes, token headroom and affordability; do not claim it ran here. All files must
fit the repo10MB-per-file artifact policy; do not silently truncate raw evidence.

## Meaningful targeted verification

Write failing tests through actual consuming paths before implementation:
strict duplicate/NaN/partial/fenced JSON rejection; shape and source-ID prefix
validation; immutability and exact round assembly; one-pass template substitution
when inserted text contains dollar markers; retained/retirement interval conflicts;
references applied sequentially with real consume_action/run_checks on synthetic
fixtures; accepted references but wrong retired-rule mutant behavior; all16slots,
barrier failure leaving later work unattempted; no retry; exact raw-body receipts;
changed freeze rejection; shared deadline and late-publication failure through an
injected clock/transport; import and default dry-plan have no network/filesystem
side effects. Test intervention paths, not producer-only metadata or tautologies.

Use injected transport/clock and real lightweight sandbox where useful. Do not
run the full pytest suite. Required targeted command:
PYTHONPATH=src .venv/bin/python -m pytest -q tests/test_source_replay_authoring.py
tests/test_prepare_source_replay.py tests/test_source_replay_screen.py
(one shell command with those paths, not three separate invocations).
Also relevant Ruff check/format, git diff --check, and direct --help/default dry
plan from a non-repository working directory using absolute script paths.

Finish at a stable boundary: report exact files/hashes, actual red/green test
results, CLI/freeze shape, limitations and any deferred launch-binding work.
No authoring, real preflight, model execution or code acceptance claim. Root
archives candidate code and requests the same new canonical Astra reviewer to
audit stable implementation before actual preparation.
