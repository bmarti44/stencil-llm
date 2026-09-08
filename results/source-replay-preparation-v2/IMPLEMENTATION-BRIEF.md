# Bounded construction correction implementation brief

2026-09-08. DRAFT. Activate only after independent acceptance of the exact
PREPARATION.md, DATA-CONTRACT.md and correction-prompt.txt in this registration.
Root owns this brief, ledger and commits. Sol xhigh implements; Astra xhigh
reviews only its canonical review file. No actual authorship is authorized here.

## Objective and allowlist

Implement the accepted prospective construction policy by reusing the existing
preparation tool. Do not add another runner, provider, framework or review parser.
Only these files may change:
- src/stencil/source_replay_authoring.py
- tools/prepare_source_replay.py
- tests/test_source_replay_authoring.py
- tests/test_prepare_source_replay.py

Read the current accepted design and review before writing code. Existing screen,
action, worker, sandbox and renderer helpers may be read but stay unchanged.
The current scientific runner, scoring, prompts, gate and qualified helpers are
out of scope. All stopped data, historical documents, reviews, snapshots and
freezes stay untouched. Root will archive versioned shared-code changes; old
launches retain their original commit/hash provenance.

Fit-on: none. Test only with existing synthetic fixtures and small synthetic
faults necessary for this implementation. No source/check/reference content or
responses from any stopped bank, benchmark, scientific worker or adapter may
be opened or used. No recursive results searches; read only explicitly named
specification/review/research documents. No actual API/model/tokenizer/container,
scientific preflight, data generation, external network or download.

## Required behavior

Use new registration defaults, exact construct IDs/domains and new contract.
Reuse the two immutable ordinary prompt files. The CLI remains
--run-dir --freeze --execute, dry by default. Bind the actual new preparation
specification/contract/correction prompt, reused prompts/SPEC, current code/tests,
existing consumers and NEW immutable acceptance snapshot: the exact18subjects
specified in PREPARATION.md. Root populates a review snapshot and actual freeze
only after code acceptance; do not manufacture either. Return the exact updated
freeze schema and required subject paths in the handoff.

Reserve16ordinary slots plus4correction slots before any call. Correction slots
16–19 have fixed project identities and no triggering stage initially. Bind their
triggering stage, original slot/raw/parsed hashes and diagnostics hash before
POST. Unused reserved slots remain explicitly UNATTEMPTED. At most one global
correction barrier, consumed once even if fewer than four projects need it.

Collect per-project validation outcomes instead of overwriting one failure
variable. Mixed eligible/noneligible failure always stops. Only the four
registered StageValidationError categories permit a correction. Successful
siblings' packet/reference states are accepted once; never reapply their actions
or rerun their checks during the correction barrier. A failed project's correction
starts from its unchanged pre-round reference and immutable accepted prior packets.

Implement one small pure correction validator/renderer as needed. Preserve exact
public/private check-ID sets, partitions and immutable check metadata listed in
the accepted design. Reference/input/expected/rationale/mutant-source changes are
allowed only in this new construction protocol, never in a stopped bank. Retain
original failing records and separately recorded corrected raw/parsed/validation
artifacts. Do not relabel the failed original execution as passing. Link the
correction explicitly. Only the accepted corrected packet enters subsequent
prior_packets and final assembled projects.

Follow the design's exact diagnostics projection, including permitted actual/error
values from construction execution. Sol's earlier codes-only recommendation is
not the draft policy: the independent accepted design determines these fields.
Do not dump a whole execution record or include modules, internal paths, timing,
sibling data, worker answers or a human-written repair. Ordinary author requests
receive no correction diagnostics. No stage0/transport/envelope/strict-JSON/
structural/deadline or unexpected-local-error repair, no second correction,
replacement, discarded checks or relaxed final source review.

Preserve existing supervised transport, absolute450/2400second deadlines, owned
cleanup, exact raw evidence and terminal dispositions. A fifth HTTP wave is
permitted within the same whole budget; the clock does not restart. Record
construction costs separately. PREPARED_UNREVIEWED still requires every project
and every round to validate, plus final assembly; it is not source-bank approval.

## Targeted regressions, red first

Write consuming tests first and report the initial red failures. Cover:
- No correction needed:16calls,4reserved unused slots,20slots total.
- One and four failed siblings:17/20calls, one correction barrier only.
- Mixed ineligible/eligible stage failures: no correction call.
- A failed correction or later failure: terminal stop, no second correction.
- Preserved check partition and every immutable metadata field.
- Successful siblings applied only once; failed originals and corrected evidence
  coexist; only accepted corrected packets appear in later requests/assembly.
- Exact correction projection and one-pass renderer, with no sibling/module/
  timing/worker data; actual construction values/errors preserved as registered.
- Request/global deadlines and exhausted fifth-wave budget remain incomplete,
  with all original/correction attempted or unattempted slots honestly recorded.
- Real new defaults/freeze subject consumer, not only test-only overrides.

Required validation:
PYTHONPATH=src .venv/bin/python -m pytest -q tests/test_source_replay_authoring.py tests/test_prepare_source_replay.py tests/test_source_replay_screen.py

Run targeted Ruff/format/whitespace checks and absolute-path --help/default
dry-plan from /tmp. No full pytest or repeated unchanged checks after passing.
CPU-only synthetic local HTTP tests already present may run; no real provider.

Return exact changed files/hashes, red-to-green evidence, static/smoke results,
updated freeze/interface shape and any remaining concrete limitation. Do not
commit. Root independently verifies and archives, then the same new Astra reviewer
reviews stable implementation before any actual preparation call.
