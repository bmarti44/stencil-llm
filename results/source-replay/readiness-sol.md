# Source-replay implementation readiness

2026-09-08. Static inspection only. Reviewed draft SPEC SHA-256
`a6459e71ec62b38ff6699700571b2e6aec64dbd2ae60e3ab193fbb575ebd2145`
and DATA-CONTRACT SHA-256
`6ae44a7794701686cf06a0c32551d9d92b96fb582cd042dee73be95a917a7e4a`.
No code import, test, data, model, tokenizer, server, GPU or network path ran, and
no spent bank was opened.

**Disposition: the first, two-call qualification stage has no architectural
blocker once the canonical specification review is terminal. Do not implement
the scored project loader/runner until that fixed interface qualifies.** The
current eight-file first-stage allowlist is sufficient. The later paired runner
has several exact conversions and freeze details that must be stated in its
implementation brief; none requires a framework or an edit to frozen code.

## Concrete reuse and incompatibilities

1. `scripts/coding_competence_run.py::NativeToolClient` is reusable unchanged
only for worker calls. Its `perform` path compares render output to the global
`ARGUMENT_SCHEMA`, validates only `replace_function`, applies the global
1,024-token cap in `_validate_usage`, and reserves that same cap in its context
check. Overriding `payload` alone for a selector would still reject the selector
schema/tool or apply the wrong cap. Implement
`NativeSourceSelectorClient` separately, with its own exact dynamic enum schema,
`select_source_ids` response validator, 128-token cap and 32,768-token context
arithmetic. It may subclass only the unchanged transport/receipt methods
`_post`, `_parsed_response`, `_fail`, `_timeout`; its `payload` and `perform`
must be complete selector-specific methods. Do not generalize or modify the
worker client and do not use the thinking/prose `record_focus` client.

2. The worker's `HTTP_TIMEOUT_SECONDS=600` does not directly implement the new
pair ceiling. The draft's fixed resolution is clean: immediately before every
selector or worker `perform`, call
`set_deadline(min(global_driver_deadline, monotonic_now + 181))`. The existing
one-second receipt reserve then limits the shared render-plus-generation pair to
at most 180 seconds. Do not reset the deadline between the two HTTP posts, alter
the module global, or give each post a separate 180 seconds. Persist both the
global and per-pair deadlines and classify either exhaustion as technical
`INCOMPLETE`.

3. Neither existing exact data validator is reusable. The competence validator
requires zero-based rounds, distinct targets/stubs and private semantic gold;
the new contract is one-based, permits a revisited target and has intervalled
checks. Reuse low-level JSON/path/AST helpers and
`coding_competence_dev.py::consume_action`, but write the small new schema in
`src/stencil/source_replay.py`. Initial-module validation must allow only an
optional leading module docstring followed by unique top-level `FunctionDef`s,
then apply the existing one-positional-argument/no-decorator/no-nesting/no-import
checks and the contract's additional no-annotation check. Existing AST rules do
not prove semantic purity or prohibit mutation of an input object; the narrow
implementable reading of “pure” is the accepted syntactic subset plus fresh
JSON sandbox execution. If semantic nonmutation is intended, the contract must
say so before authoring because it would require a new restriction.

4. `scripts/coding_worker_dev.py::run_checks` accepts no intervals and requires
`rule_ids`. At round `r` (external indices 1..3), collect public and private
checks introduced through `r`, then retain exactly those with
`active_from_round <= r` and (`active_through_round is null` or
`r <= active_through_round`). Convert each active check to only
`check_id,symbol,input,expected_values,rule_ids=[]` for `run_checks`. Reattach
audit metadata only in private records. The work envelope receives only the
four executable fields; public tool feedback receives only action status and
genuine current results. Never serialize interval/source/behavior/rationale
metadata. Run terminal active public and private checks even after a rejected
patch, on the unchanged arm state, so “all check results” and retained-state
failures remain observable; `applied=false` still makes the round fail.

5. `coding_competence_run.py::build_issued_messages` cannot be adapted: it
injects `manual_recap` and drops the work envelope from later history. Use this
exact state transition independently for each `(project_id, arm)`:

```text
base = permanent history + this round's four original sources + original request
issued(H)   = base + work_envelope
issued(S/R) = base + ephemeral_evidence_supplement + work_envelope
after       = base + work_envelope + actual assistant tool call + actual tool result
```

Archive `base`, supplement, envelope, complete issued messages and `after`
separately with hashes. Never append the supplement to `after`; always append
the envelope. Emit the S supplement even for a valid empty selection, containing
the fixed introduction and JSON `[]`, so empty selection does not silently
change the intervention protocol. Each arm owns its module, history, tool-call
IDs, call records and workspace paths from initialization. Selector state is
fresh and never enters worker history.

6. Freeze the exact deterministic selector-input, evidence JSON and work-envelope
serialization before qualification: object keys/order, `ensure_ascii` choice,
separators and newlines. The specification pins semantic content and the evidence
introduction but not every serialization byte. This is not an architecture
blocker if the implementation constants and their tests are reviewed and hashed
before the first call; it is a blocker if those bytes are left as a runtime
choice. Reuse the frozen worker `SYSTEM_PROMPT`; do not use `CURRENT_PROMPT`.

## Lifecycle and records

Reuse `tools/run_coding_competence.py::run_lifecycle(plan, run_flag=...)`
unchanged for both the 600-second qualification and later 3,000-second screen.
It already forwards the remaining driver deadline, reserves cleanup, registers
owned child PIDs, records startup/driver/cleanup receipts, checks container
ownership, removes the run flag only after cleanup and writes a durable terminal
lifecycle record. Both new drivers should support its exact CLI:
`--input --output-dir --base-url --model --deadline-seconds`.

Do not reuse its old `make_plan`, `validate_artifacts` or
`qualify_environment`; those bind spent competence data and fixed old counts.
The new launcher needs only source-replay-specific hash/acceptance checks and a
plan. Reuse the existing `_container_command` unchanged, including endpoint and
its `stencil.owner=coding-competence:<container>` label: `run_lifecycle`'s
cleanup ownership check currently expects that literal label. A renamed
source-replay label would make cleanup evidence fail unless the frozen lifecycle
were edited, which is unnecessary. After `run_lifecycle` returns, reconcile its
terminal state with the driver manifest; a driver exit alone is not evidence of
a complete eligible qualification/screen.

Before any native request, precreate all planned call records as `UNATTEMPTED`.
Write `PENDING` plus exact request intent/bytes before transport and fsync each
partial exchange through the client callback. A first technical error stops the
schedule and leaves all remaining records unattempted. The qualification's two
calls are selector then worker; technical eligibility follows
QUALIFICATION-BRIEF (both exact native exchanges and consumer delivery complete,
timely clean shutdown), while hidden mechanical behavior is reported separately.

Before the later project stage, freeze one input container and ordering rule.
DATA-CONTRACT defines one project object, while the standard driver accepts one
`--input`; the smallest resolution is a mechanically assembled reviewed JSON
array of exactly four objects in `replay-01` through `replay-04` order, with raw
object hashes retained. Also state that arm rotation uses zero-based
`p=0..3,r=0..2` in `(p+r)%3`; using the contract's one-based round number would
rotate a different schedule. Make lineage structured/exact rather than asking a
validator to infer “fresh” from arbitrary prose.

## Minimal staged allowlists and tests

Stage 1, before any scored authoring, is exactly the current eight new files:

```text
src/stencil/source_replay.py
src/stencil/focus/native_source_selector.py
scripts/source_replay_qualification.py
tools/run_source_replay_qualification.py
tests/test_source_replay.py
tests/test_native_source_selector.py
tests/test_source_replay_qualification.py
tests/test_run_source_replay_qualification.py
```

Run only:

```text
.venv/bin/python -m pytest -q tests/test_source_replay.py tests/test_native_source_selector.py tests/test_source_replay_qualification.py tests/test_run_source_replay_qualification.py tests/test_no_side_effect_imports.py
.venv/bin/python -m ruff check <the eight paths above>
.venv/bin/python -m ruff format --check <the eight paths above>
git diff --check -- <the eight paths above>
```

Stage 2 starts only after a terminal accepted qualification. Its exact additional
allowlist should be `scripts/source_replay_preflight.py`,
`scripts/source_replay_run.py`, `tests/test_source_replay_preflight.py` and
`tests/test_source_replay_run.py`, plus modifications to
`src/stencil/source_replay.py`, `tools/run_source_replay_qualification.py` and
their existing tests. Renaming the launcher after qualification would add churn;
prefer extending it with an explicit screen plan only after qualification.
Target the six source-replay test files plus `tests/test_no_side_effect_imports.py`
and Ruff/format/diff checks on only that allowlist. No frozen existing source,
specification, scored data or result path belongs in either coder allowlist.
