# BFCL harness v6 review — LEG A v7 + Amendments 1–3

Reviewer: sol, 2026-09-03. Reviewed commits `9fe7c3f` and `c547811`
against `LEDGER-PLAN.md:623-758`, and rechecked every finding in
`results/harness-v4-review-sol.md` (BFCL-V4-1..7) and
`results/harness-v4-review-fable.md` (F1..F10). `HEAD` is `7b8de79`; there is
no code/test/data diff from `9fe7c3f` to `HEAD`.

Execution by this review was CPU-only with `CUDA_VISIBLE_DEVICES=''`; it loaded
or launched no model, did not touch the pre-existing GPU shakedown, signalled or
terminated no process, opened no sealed split or sealed IFEval file, left
unrelated files untouched, and wrote only this file. One hard-rule violation
occurred and is disclosed rather
than waived: running the whole v5 test file included
`test_v4_1_index_preserves_all_frozen_bfcl_files_and_is_manifest_pinned`, which
SHA-256-read the eight mixed BFCL case/answer files. It did not parse, print, or
execute any sealed row, but the hash process necessarily read bytes spanning
sealed rows. The seek-only loader test and the census themselves used only the
registered dev offsets. No later mixed-file hash check was run.

## Bottom line

The dev-only evidence requested by the brief is green: the seek-only loader,
the complete `primary_claim_status` table, certificate mismatch/refusal, the
registered safety arithmetic, and the no-model census all execute. Under the
registered deterministic stub scorer the census reconstructs the 32 dev cases
and 115 teacher-forced histories, finds exactly 11 evicting turns, observes no
`match_impossible` in `clf_control`, `recency_pinned`, or `tool_swap_echo`, and
keeps every absolute `echo_token_delta` at or below 16.

That does not make the harness safe for the registered preflight. Six
code-level gaps remain. Most importantly, the matcher can silently report a
resource-mismatched comparator as usable; a passing certificate does not prove
the actual BFCL source/function-document bytes equal its recorded hashes; and
Amendment 3's echo-delta assertion is still a sealed-only fail-open path.

## Blocking findings

### BFCL-V6-1 — CRITICAL — nearest matching can stop before matching every selected span and can suppress a failed clamp

`src/stencil/bfcl.py:490-542` first checks only the combined available-column
total, then cycles through selected targets only until the *matched column
sum* reaches the treatment total. A wide first match can therefore end the
loop before later selected spans are visited. This is not the registered
"for each selected span" one-to-one nearest match.

There is a second fail-open consequence in `build_matched_control`.
`clamp_candidate_rows()` reports whether the requested per-role quota was
actually filled, but `src/stencil/bfcl.py:585-605` discards
`clamped["match_impossible"]` and returns `match_impossible: False`
unconditionally. For example, with selected USER=2 columns and TOOL=2 columns,
a first same-role USER candidate four columns wide can satisfy the loop's
global total before the TOOL target is considered. The clamp then emits only
the two requested USER columns, leaves the TOOL quota unfilled, and the caller
still labels the comparator usable. Dev invariants happen not to encounter
this construction; sealed data can, and sealed execution does not run
`assert_dev_invariants()`.

`tool_swap_plan()` has the same target-cardinality defect: one wide disjoint
TOOL candidate can satisfy the aggregate quota for two selected TOOL chunks,
so the second selected chunk receives no one-to-one replacement while A4 is
reported usable (`src/stencil/bfcl.py:685-742`).

This reopens fable F1 and the comparator portion of BFCL-V4-7. It can change
A1/A4's estimand without setting the registered uninformative state.

Required code fix:

1. Rewrite `_resource_match()` so every target in `kept` is visited in
   registered order and receives an unused nearest candidate, with the exact
   key `(abs(width delta), abs(turn delta), stable source order)`. Do not let an
   aggregate width terminate the first target pass.
2. Preserve target-to-match groups explicitly. If additional resources are
   needed to make a narrower set reach the quota, define and test a
   deterministic supplementation pass; never silently let one wide match stand
   for an unvisited target. The current text's simultaneous "one-to-one" and
   "impossible only when total eligible columns are short" requirements need
   an explicit supplementation rule if both are intended.
3. In `build_matched_control()` and `tool_swap_plan()`, propagate
   `clamped["match_impossible"]`; assert exact total columns, and exact per-role
   columns whenever `control_role_shortfall` is false, before returning a
   usable plan.
4. Add adversarial tests for (a) a wide first USER match plus an unvisited TOOL
   target, (b) one wide TOOL replacement for two selected TOOL chunks, and
   (c) a clamp that leaves a nonzero role quota. Each must either produce the
   registered exact comparator or set `match_impossible`.

### BFCL-V6-2 — CRITICAL — the certificate records expected BFCL hashes without verifying the bytes used

The seek-only boundary itself is fixed: `load_cases("dev")` performs bounded
reads only at dev offsets and validates the raw ID before JSON decoding
(`scripts/bfcl_mt.py:229-266`). The offset-index hash is also verified.

But `artifact_meta()` assigns `frozen_hashes["bfcl_files"]` directly from
`pins-manifest.json` (`scripts/bfcl_mt.py:1313-1329`). It never hashes or
otherwise verifies the current case, answer, cohort, or function-document
bytes against that map. `load_cases()` verifies only `offsets.json`; an indexed
row changed in place while retaining its ID is accepted. Function documents
used in model prompts and tool execution are likewise not checked. Thus a
passing preflight certificate and later sealed meta can contain the expected
hash strings while executing changed data.

This leaves BFCL-V4-1 requirement 2 and BFCL-V4-5's code/data identity binding
open. The repository's current static test proves that today's files match the
pin, but the production certificate path does not enforce that fact.

Required code fix:

1. Extend the authorized offset index with a SHA-256 for every indexed case and
   answer record. In `read_row()`, hash the bounded raw bytes and compare before
   the ID check/JSON decode. This preserves the dev/sealed read boundary while
   detecting mutation of every row actually used.
2. At `artifact_meta()`/certificate construction, recompute and refuse
   mismatches for every non-cohort-content file that executes or enters a
   prompt: `cohorts.json`, all function documents, and the vendored checker /
   environment files. Do not merely copy their expected digests.
3. On an authorized sealed invocation, before model loading and before decoding
   any cohort row, validate the mixed case/answer source files against the
   registered source hashes (or use physically separated/Merkle-addressed
   sealed records). Bind the verified map, not the manifest's unverified map,
   into the certificate comparison and run identity.
4. Add mutation tests using temporary copies: a same-ID row-byte change and a
   function-document change must both be refused. Rebuild/re-pin the offset
   index only through an authorized sealing step and recompute the registration
   artifacts.

### BFCL-V6-3 — HIGH — Amendment 3 echo overflow is still treated as a method failure in sealed summaries

The new `_echo_clamp()` uses Qwen source-token boundaries, preserves whole-row
source characters, and passes the requested dev census. However, Amendment 3
says any `abs(echo_token_delta) > 16` is a **harness assertion failure, not a
method failure**. Only preflight explicitly raises. A sealed run does not call
`assert_dev_invariants()`, and `summarize_records()` still converts a delta over
16 into an uninformative A1/A2/A4 contrast
(`src/stencil/bfcl.py:1545-1564,1573-1593`). That is the superseded
pre-Amendment-3 behavior.

This leaves fable F2 only partially closed despite the green dev values.

Required code fix: in `_turn_plan()`, after comparator construction, assert
`abs(echo_token_delta) <= 16` for every comparator not already
`match_impossible`, before any generation. At schema/summary boundaries, raise
on such a record rather than changing a contrast status. Add a sealed-shaped
synthetic record with delta 17 and prove it is rejected, never summarized as
uninformative.

### BFCL-V6-4 — HIGH — repeated-call normalization is not the execution normalization

The v5 code correctly includes ground-truth and echoed calls and now catches
unmatched tool-call tags. But `_canonical_call()` only sorts JSON keys
(`scripts/bfcl_mt.py:497-526`), while executable calls normalize a qualified
name with `name.rsplit(".", 1)[-1]` (`src/stencil/bfcl.py:932-940`). Therefore
an earlier/echoed `lookup(...)` and a generated valid
`{"name":"API.lookup",...}` execute as the same call but have different safety
keys. The repeated-call event is missed even though the registered definition
uses a normalized call.

This leaves the repeated-call part of BFCL-V4-4 open.

Required code fix: make one canonicalizer validate the argument object,
normalize the function name exactly as `call_to_python()` does, and serialize
sorted arguments. Use it for prior ground truth, echoed JSON/tool-call blocks,
current-turn exclusion, and generated calls. Add a consumer-path test showing
that qualified and unqualified spellings of the same executable call set
`repeated_call=True` unless present in the current ground truth.

### BFCL-V6-5 — HIGH — the "every executing module" manifest has an unmanifested runtime import chain

`harness_manifest()` is a useful improvement and hashes the main Stencil files
plus the BFCL checker tree (`scripts/bfcl_mt.py:141-164`). It is not complete.
Every generation calls `from stencil.bench import EOS`
(`scripts/bfcl_mt.py:326-342`). Importing `stencil.bench` executes
`vendor/ifeval` and `langdetect` imports (`src/stencil/bench.py:16-27`), but the
repo-local IFEval modules are absent from `harness_manifest`. Package
`__init__.py` files on the Stencil/BFCL import path are also omitted. The claim
that every executing local module is hash-bound is therefore false.

This leaves BFCL-V4-5 and fable F5 open under Amendment 3's explicit
confirmation.

Required code fix: remove the unrelated `stencil.bench` dependency by defining
the two registered BFCL EOS IDs in the BFCL runner or a BFCL-specific hashed
module. Add all executing repo-local package initializers and dynamic BFCL
environment modules to the manifest. Add a CPU import-closure test that
exercises teacher-history/checker imports plus the generation module imports,
then rejects any loaded repo-local `module.__file__` absent from the canonical
manifest. Hashing a known subset is not a proof of closure.

### BFCL-V6-6 — MEDIUM — overflow events are scored correctly but still misreported at three boundaries

The central Amendment 3 crash is fixed: `position_overflow_result()` and
`run_case_arm()` produce `pass=False, truncated=True`, schema v5 rejects
non-boolean passes, and safety counts full overflow as truncated. Two residuals
remain:

* `pin_overflow_total` is computed before the base/full early return
  (`scripts/bfcl_mt.py:659-682`) but `_arm_event_fields()` records it only on
  `clf_pinned_echo` (`scripts/bfcl_mt.py:623-648`). The original BFCL-V4-7
  requirement specifically required the shared total-overflow fact to be
  recorded for base/all non-full arms. No record-level `turn_facts` replacement
  exists.
* `_arm_summary()` excludes an entire full case from final-pass reporting after
  *any* position overflow (`src/stencil/bfcl.py:1182-1189`). That is correct for
  the original registered initial-full-prompt exclusion, but it also excludes
  a within-generation or later tool-step overflow, which Amendment 3 says is a
  counted truncated failure.
* If the pre-generation position check fires for a non-full pressure-exposed
  turn, the synthetic result sets `evicted=False`
  (`scripts/bfcl_mt.py:1008-1033`). The primary population is defined from
  `base.eviction.evicted`, so that registered pressure turn is silently removed
  from primary and safety rather than retained as a truncated failure.

Required code fix: create one record-level per-turn fact containing the shared
pressure trigger and `pin_overflow_total`; validate it against every arm and
use it to define the primary population. Record an overflow phase
(`initial_prompt`, `within_generation`, `tool_step`). Keep the registered A3 /
full-final exclusion only for the initial full-prompt condition; count later
full overflows as false final passes. Add synthetic summary tests for all three
phases and for a non-full pre-generation overflow whose pressure trigger stays
primary.

## Prior-finding disposition

| Prior finding | Disposition in v6 |
|---|---|
| BFCL-V4-1 | **PARTIAL / BLOCKER.** Dev seek-only loading is closed; actual source/function-document integrity is not enforced (V6-2). |
| BFCL-V4-2 | **CLOSED.** All five gates feed a passing-only digest-bound certificate; fallback/refusal, exact reduced-arm timing, arm-cut rules, sealed settings, no-limit rule, and pre-model validation are implemented and tested. |
| BFCL-V4-3 | **CLOSED.** Complete primary table, A2 separation, A3 fields/post-exclusion k, and A4-local gating are implemented and CPU-tested. |
| BFCL-V4-4 | **PARTIAL / BLOCKER.** Truncated-degenerate and malformed/unmatched calls are fixed; qualified-name repetition escapes normalization (V6-4). |
| BFCL-V4-5 | **PARTIAL / BLOCKER.** Record/run identity, exact arms/order, stale/extra record refusal, and individual expected hashes are present; verified BFCL bytes and full module closure are not (V6-2/V6-5). |
| BFCL-V4-6 | **CLOSED.** Candidate source is asserted twice; all six invariant families have derived `{passed,n}` counts and a nonconstant aggregate. |
| BFCL-V4-7 | **PARTIAL / BLOCKER.** Tool order, prior-user source, non-evicting outcomes, and dose aggregates are fixed; matcher and overflow facts retain the V6-1/V6-6 defects. |
| F1 | **PARTIAL / BLOCKER.** Dev feasibility is green and the nearest key is present, but matching is not reliably per-target/one-to-one and failed clamps are suppressed (V6-1). |
| F2 | **PARTIAL / BLOCKER.** Source-boundary echo clamp is green on dev; sealed delta overflow still becomes uninformative instead of asserting (V6-3). |
| F3 | **PARTIAL / BLOCKER.** `None`/crash and safety counting are closed; within-turn full final-pass reporting remains wrong (V6-6). |
| F4 | **CLOSED.** Truncated generations cannot be degenerate. |
| F5 | **OPEN / BLOCKER.** Static manifest is still not the executing repo-local module closure (V6-5). |
| F6 | **CLOSED.** Tool replacements are reinserted at treatment-order target positions. |
| F7 | **CLOSED.** Truncation counting uses the exact untruncated encoder pair. |
| F8 | **PARTIAL / BLOCKER.** Measured invariant counts, zero non-evict pins, and scoped shortfall/overflow-drop counts are fixed; the shared total-overflow/pressure facts are not faithfully represented (V6-6). |
| F9 | **CLOSED.** Outcome label, non-evicting treatment-echo stratum, and registered dose/event aggregates are present. |
| F10 | **CLOSED.** Dev case/answer loading is seek-only and never scans a sealed row. |

## Requested CPU verification

The targeted command was run with CUDA hidden, bytecode and pytest cache writes
disabled:

```text
CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 .venv/bin/pytest -q \
  -p no:cacheprovider tests/test_bfcl_evict_v5.py tests/test_bfcl_evict_v6.py
```

The lightweight cases covering seek-only reads, registration hash/certificate
refusal, the primary decision table, safety definitions, report fields, and
manifest membership passed before the long census. The census itself used no
model and confirmed exactly 11 evicting dev turns, zero comparator
`match_impossible` events for all three registered comparators, and
`abs(echo_token_delta) <= 16` throughout. `test_sealed_guard.py` was
intentionally not run because its IFEval hash test opens the sealed IFEval file,
which this brief forbids. The command selection nevertheless violated the BFCL
half of that same rule because the v5 manifest-pin test hash-read the complete
mixed BFCL files, as disclosed at the top of this review; its digest-only output
did not expose item contents or outcomes.

Static checks also confirmed registration SHA-256
`7f4078ece9263daed0d0fd28799318de098bd78e5d08c7da7249ca53d281674a`
covers LEG A v7 plus A1/A2/A3 while excluding intervening LEG B Amendment 3.

## VERDICT

The existing shakedown output must not become a registered preflight
certificate, and no sealed run is authorized. Fix V6-1 through V6-6, add the
consumer-path regressions above, re-register the harness/data-index/module
manifest, and rerun the complete dev preflight from a new output directory.

**VERDICT: UNSOUND**
