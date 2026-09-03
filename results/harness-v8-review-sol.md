# BFCL harness v8 review — LEG A v7 + Amendments 1–4

Reviewer: sol, 2026-09-03. Target commits: `2621509` and `a145340`.
Governing text: `LEDGER-PLAN.md:623-771`, including LEG A Amendments 1–4.
Prior findings rechecked: `results/harness-v4-review-{sol,fable}.md` and
`results/harness-v6-review-{sol,fable}.md`.

All review execution was foreground and CPU-only with CUDA hidden. No model or
GPU process was launched, waited on, signalled, or terminated. The sealed IFEval
input and the sealed BFCL case/answer rows were not opened. BFCL data access was
limited to the registered dev offsets and non-content index/manifest metadata.
No repository file was written by this review other than this report.

The concurrently running `function-vector-focus` wrapper advanced `HEAD` after
the review began and changed manifest-covered `src/stencil/qwen3.py`. That work
is outside this pinned review. The BFCL runner, BFCL helper, and BFCL v8 tests are
unchanged from `a145340`; code findings below cite those target bytes. A launch
from the later tree would independently require a new registered harness
identity because the registration says any later harness change re-registers
the leg.

## Bottom line

**No: the REGISTERED dev preflight may not be launched under this harness.**

The requested dev census is green, as are the nearest matcher, bidirectional
echo clamp, initial-overflow safety semantics, call normalization, local runtime
module closure, and primary-claim decision table. Three launch blockers remain:

1. A passing dev certificate cannot validate a sealed invocation because the
   certificate embeds dev-only verified-byte maps while sealed metadata embeds
   different sealed-only maps. Worse, the sealed loader reads and decodes the
   cohort before certificate validation.
2. Amendment 4's exact per-role equality is still fail-open for a
   `clf_control` role-shortfall: exact total columns with unequal roles are
   accepted as informative on both the generation and sealed record paths.
3. Full initial-prompt overflows are excluded correctly from A3, per-turn
   reporting, and truncation safety, but still enter the preflight's full
   case-level competence baseline as failures.

The first issue makes the certificate unusable even after a successful GPU
preflight; the second can change A1's registered estimand on unseen cases; the
third can choose the wrong trunk or stop the leg for a condition Amendment 4
made NA. These are harness/authorization failures, not model outcomes.

## Blocking findings

### BFCL-V8-1 — CRITICAL — sealed authorization is both too late and impossible to satisfy

There are two coupled defects.

First, `main()` calls `_load_cases_verified(args.split, args.limit)` at
`scripts/bfcl_mt.py:2251`, before it calls
`validate_preflight_certificate(...)` at lines 2263–2266. For `--split sealed`,
the loader first hashes all mixed source files and then bounded-reads, hashes,
ID-checks, JSON-decodes, and returns every sealed case and answer row. Therefore
an existing but invalid, stale, mismatched, or forged certificate is rejected
only **after** the sealed cohort has been accessed. This reopens the critical
authorization ordering part of BFCL-V4-2.

Second, a genuine dev preflight certificate cannot match sealed metadata:

- `certificate_payload()` includes the complete `meta["frozen_hashes"]`
  (`scripts/bfcl_mt.py:251-278`).
- A dev `_load_cases_verified()` result contains hashes for the 64 case/answer
  records actually loaded and an empty `source_files` map
  (`scripts/bfcl_mt.py:338-364`). A sealed result contains a different record
  map and the complete mixed-source map.
- `artifact_meta()` embeds that split-specific object under
  `frozen_hashes.verified_bytes`; it also adds mixed source hashes to
  `frozen_hashes.bfcl_files` only for sealed execution
  (`scripts/bfcl_mt.py:1589-1620`).
- `validate_preflight_certificate()` requires exact equality of the entire
  certificate contract and sealed contract (`scripts/bfcl_mt.py:292-310`).

A CPU synthetic consumer-path probe made a valid dev-shaped certificate and
validated it against otherwise identical sealed-shaped metadata. The actual
result was `preflight certificate does not match sealed run contract`. This is
not a hypothetical mutation case; it follows deterministically from the two
normal split-specific metadata shapes.

The v8 certificate does correctly recompute the **dev bytes actually loaded**:
bounded case/answer bytes are hashed before decoding, the offset bytes are
hashed from their read buffer, function-document bytes are verified before
being decoded and are the objects passed into `prepare_case`, and the current
checker/template/module bytes are hashed. The defect is how that evidence is
mixed into the cross-split authorization contract and when authorization is
consumed.

Required code fix:

1. Split certificate metadata into:
   - a split-independent frozen contract: registration, constants, selected
     trunk/arms/settings, code/module hashes, selector/model/tokenizer hashes,
     pinned offsets/cohort/function-doc/checker/template hashes, and the
     offset index's expected per-record hash map; and
   - a preflight evidence inventory: the hashes of the 32 dev cases and answers
     actually loaded plus the other bytes actually used by preflight.
   Do not compare a dev actual-record inventory to a sealed actual-record
   inventory as if they were the same object.
2. Reorder `main()` for sealed execution: clean-tree/environment guard; build
   and verify only the split-independent contract without reading a sealed
   case/answer row; validate the passing certificate; only then verify the
   complete mixed source hashes and bounded-load/decode the registered sealed
   rows. Model loading must remain after certificate validation.
3. After authorization, store the actual sealed-row digests in sealed run meta
   and bind them into `run_identity_sha256`; each bounded row must still be
   checked against the expected digest from the already-authorized offset
   index before decoding.
4. Add consumer-path tests, not payload-only tests:
   - an invalid/mismatched existing certificate must refuse before a mocked
     sealed loader is called;
   - a certificate emitted from a dev-shaped preflight must validate against a
     sealed split-independent contract;
   - after that validation, a same-ID sealed-row mutation must be rejected by
     the bounded loader; and
   - changing any common harness/model/data-manifest byte must reject the
     certificate before sealed row access.

### BFCL-V8-2 — CRITICAL — Amendment 4 per-role equality remains fail-open on `clf_control` shortfalls

Amendment 4 and the v8 brief require exact per-role treatment/comparator column
equality on **every** evicting turn on both dev and sealed paths. A violation is
fail-closed and makes the affected contrast uninformative. The implementation
still preserves the superseded exact-total exception for
`control_role_shortfall`:

- `build_matched_control()` redistributes the quota by the roles of fallback
  resources and considers a clamp usable when only its total equals the
  treatment total (`src/stencil/bfcl.py:608-641`).
- `_turn_plan()` explicitly accepts exact total instead of exact roles when
  `clf_control.control_role_shortfall` is true
  (`scripts/bfcl_mt.py:1014-1025`).
- `assert_case_record_schema()`, which is the sealed result boundary, repeats
  the same exception (`src/stencil/bfcl.py:1264-1286`).
- `assert_dev_invariants()` also checks only the total on those turns
  (`scripts/bfcl_mt.py:1898-1917`).

A sealed-shaped CPU record with treatment `{user: 2, tool: 1}`, control
`{user: 0, tool: 3}`, `control_role_shortfall=true`, and
`match_impossible=false` was accepted by `assert_case_record_schema()`. Such a
record would enter A1 as informative despite violating the latest registered
per-role invariant. This is the exact class Amendment 4 required to fail
closed.

The real dev census did not encounter this branch, so its green result does not
close the consumer defect.

Required code fix:

1. In `build_matched_control()`, preserve `control_role_shortfall` and the role
   deltas for reporting, but set `match_impossible=true` whenever the final
   `role_counts != treatment_role_counts`. Exact aggregate equality is not
   sufficient under Amendment 4.
2. In `_turn_plan()`, require `arm_role_counts == treatment_roles` for every
   usable comparator, including `clf_control`; remove the shortfall exact-total
   exception. Prefer propagating the builder's `match_impossible` so the event
   is recorded and A1 becomes uninformative as registered; any contradictory
   usable plan must raise before generation.
3. Apply the identical rule in `assert_dev_invariants()` and
   `assert_case_record_schema()`. A sealed-shaped unequal-role record must be
   rejected or already carry `match_impossible=true`; it must never be
   summarized as informative.
4. Replace the existing fallback regression that expects
   `match_impossible=false` for unequal roles. Add cases for a USER shortage
   filled by TOOL columns and the converse, and assert the recorded shortfall,
   deltas, and contrast-wide uninformative disposition.

### BFCL-V8-3 — HIGH — full initial-prompt NA cases still contaminate the preflight competence baseline

The turn-level and summary behavior is mostly correct:

- `position_overflow_result("full", ..., phase="initial_prompt")` produces
  `na=true` and `truncated=false` (`src/stencil/bfcl.py:856-876`).
- A3 excludes the turn (`src/stencil/bfcl.py:1638-1702`).
- `_arm_summary()` excludes affected full cases from final-pass reporting and
  excludes NA turns from per-turn reporting (`src/stencil/bfcl.py:1323-1339`).
- Because the event is not truncated, it does not inflate full's truncation
  safety count.

But `run_case_arm()` computes teacher-forced `final_score` with
`all(turn["pass"] for turn in turns if turn["pass"] is not None)`
(`scripts/bfcl_mt.py:1417-1420`). Initial-prompt NA turns carry boolean
`pass=false`, not `None`, so the raw arm `final_pass` is false. `preflight()`
then calculates `full_passed` and `full_long_passed` by summing those raw arm
fields over all 32/all 8 cases (`scripts/bfcl_mt.py:2038-2065`) and reports
literal denominators 32 and 8 (`scripts/bfcl_mt.py:2098-2112`). It does filter
NA turns for `full_long_turn_passed`, but it does not filter NA cases for either
case-level full competence floor.

The CPU dev census reconfirmed six initial-prompt overflows on the 11 evicting
turns, in two of the eight long-context cases. They contribute zero to full's
truncation safety baseline, but both affected cases still enter these
case-competence numerators as failures. That conflicts with Amendment 4's NA /
excluded-from-full-baseline reading and with the summary's own final-pass
population.

Required code fix:

1. Define one shared `full_case_final_reporting_eligible` predicate: a case is
   excluded when any full turn has
   `overflow_phase == "initial_prompt"` / `na == true`.
2. Use that predicate in both `_arm_summary()` and preflight competence. Compute
   `full_passed` and `full_long_passed` only over eligible rows; report the
   eligible `n` and the count excluded for initial-prompt overflow. Keep the
   registered absolute floors (at least 5 overall and at least 2 long-context)
   unless the registration is amended to change them.
3. Keep `full_long_turn_passed` filtered by `na`, as it is now, and keep later
   within-generation/tool-step overflow as a counted false/truncated event.
4. Add a CPU preflight-aggregation test with one initial-prompt overflow case
   and one within-turn overflow case. The former must be absent from full's
   case and turn denominators and safety baseline; the latter must remain a
   failed case/turn and a truncation safety event.

## Requested dev census

The registered CPU/no-model census was rerun through the harness's own
`load_cases("dev")`, `build_teacher_history()`, `context_layout()`, and
`_turn_plan()` with the v8 stub that keeps the first USER sentence on every
evicting turn and rejects TOOL candidates.

- Dev cases: 32; late teacher-forced histories: 115.
- Evicting turns: 11, all long-context.
- USER selected after budget/overflow: 11/11 turns.
- Comparator turn-arms checked: 33 (11 × `clf_control`, `recency_pinned`, and
  `tool_swap_echo`).
- `match_impossible`: 0/33.
- `control_role_shortfall`: 0/33.
- Per-role equality failures: 0/33. The retained dose was USER-only in this
  registered stub, with USER widths 11–23 columns and TOOL width 0.
- Every `abs(echo_token_delta) <= 16` assertion passed.

An additional tool-heavy deterministic stub was run to exercise nonzero TOOL
matching. Its post-overflow treatment retained TOOL-only spans on all 11 turns,
so it is complementary evidence, not a mixed-role census. It also had 0/33
`match_impossible`, 0/33 shortfalls, and 0/33 per-role equality failures. Echo
delta ranges were:

| comparator | echo-token delta range |
|---|---:|
| `clf_control` | -5 to 0 |
| `recency_pinned` | -1 to 0 |
| `tool_swap_echo` | -5 to 0 |

The overflow-only census independently reproduced the registered counts:
six of 11 evicting turns had a full initial prompt over 40,960 positions
(41,102–43,804). All six mapped to `na=true, truncated=false`, contributing
zero initial-overflow truncation events to full's safety baseline.

These censuses demonstrate that the current dev slice happens not to trigger
the open shortfall exception. They do not make a fail-open sealed consumer
sound.

## Verified closures

Targeted CPU tests produced **22 passed, 1 deselected in 8.45 s**, covering the
non-census v8 regressions, verified-byte inventory, echo overflow rejection,
execution-normalized repetition, runtime module closure, both full overflow
phases, certificate mismatch handling, the complete primary decision table,
and A2/A3/A4 separation. The registered v8 census separately passed in 92.63 s.

- **Nearest matching core:** every selected target is visited before
  supplementation; width, age, and stable-source ordering are implemented;
  failed clamps propagate; tool-swap target grouping is preserved. Mixed-role
  adversarial unit tests pass. The Amendment-4 shortfall exception is the open
  part described in V8-2.
- **Bidirectional echo clamp:** over-target entries truncate at Qwen token
  boundaries; under-target echoes extend the last entry only within its saved
  source columns; the pinned dose is unchanged. `_turn_plan()` asserts the
  clamp on generation paths and schema validation rejects delta >16 records.
- **Actual dev bytes:** registration SHA-256
  `d3e4e84c01a329c53e03950a83a7e9ca0699a89f7f67c8b63d40114d9721a745`
  includes Amendment 4. The dev loader recomputed 64 case/answer row hashes,
  eight function-document hashes, and 15 checker/environment hashes. The
  certificate construction records them. V8-1 is a consumer/order mismatch,
  not an expected-vs-actual dev hashing regression.
- **Runtime module manifest:** the dry import closure contains 25 entries,
  including package initializers, runner, BFCL/statistics/selector/Qwen/cache
  modules, checker utilities, and all dynamic BFCL environment modules.
  `stencil.bench` and the unrelated IFEval chain are no longer imported.
- **Normalization:** `canonical_call()` and `call_to_python()` both call the
  single `normalize_call()` implementation, including qualified-name stripping
  and argument-object/key validation. Ground truth, echoed calls, current-turn
  exclusions, generated calls, and executable checker input use this path.
- **Primary claim table:** the ordering is complete: global k<6 and A1
  uninformative are INCONCLUSIVE; treatment safety is UNSUPPORTED; A3
  uninformative branches to SUPPORTED_A1_ONLY only when A1 passes; eligible A3
  requires both Holm-passing A1 and A3. A2 does not gate the primary, and A4 is
  a separate family with local safety.
- **Other v4 closures:** dev seek-only loading, truncated-degenerate exclusion,
  malformed/unmatched tool-call invalidity, tool-swap rank order, scorer
  truncation accounting, measured invariant counters, candidate-source checks,
  all-prior-USER reporting arm, non-evicting stratum, exact ordered resume
  records, and run-identity binding remain present.

## Prior-finding disposition

| prior finding | v8 disposition |
|---|---|
| sol BFCL-V4-1 | **CLOSED for the dev boundary and actual row-byte verification.** Dev bounded reads do not touch sealed row ranges. |
| sol BFCL-V4-2 | **REOPENED / BLOCKER (V8-1).** Gates/certificate exist, but sealed certificate validation occurs after sealed access and the normal dev certificate cannot equal sealed metadata. |
| sol BFCL-V4-3 | **CLOSED.** Complete primary outcome table, A2 separation, A3 post-exclusion status, and A4-local decision are implemented. |
| sol BFCL-V4-4 | **CLOSED.** Truncated repetition, malformed tags, echoed-call history, and qualified execution normalization are fixed. |
| sol BFCL-V4-5 | **PARTIAL / BLOCKER (V8-1).** Module/run/record identity and stale-record refusal are closed; the certificate cannot bind a normal dev preflight to a sealed run. |
| sol BFCL-V4-6 | **CLOSED.** Named measured invariant numerators/denominators and candidate-source assertions are present. |
| sol BFCL-V4-7 | **PARTIAL (V8-2/V8-3).** Reporting and shared pressure facts are present; shortfall equality and full case-level NA competence remain wrong. |
| fable F1 | **CLOSED for nearest matching; Amendment-4 residual open (V8-2).** No dev `match_impossible`; per-target supplementation works. |
| fable F2 | **CLOSED.** Bidirectional source-bound echo clamp and generation/schema assertions are present and green. |
| fable F3 | **PARTIAL (V8-3).** Initial vs within-turn scoring no longer crashes and A3/safety are correct; preflight case competence still treats initial NA as failure. |
| fable F4 | **CLOSED.** Truncated generations cannot be degenerate. |
| fable F5 | **CLOSED.** Runtime local import closure is manifested. |
| fable F6 | **CLOSED.** Tool replacements retain treatment target order. |
| fable F7 | **CLOSED.** Scorer truncation counts the actual untruncated pair. |
| fable F8 | **CLOSED except V8-2's latest-amendment equality rule.** Shared pressure/overflow facts, zero non-evict pins, scoped events, and measured counters are implemented. |
| fable F9 | **CLOSED.** Registered outcomes, strata, and dose/event aggregates are reported. |
| fable F10 | **CLOSED.** Dev case/answer loading is seek-only. |
| sol BFCL-V6-1 / fable FV6-1 | **CLOSED at matcher/clamp level; BLOCKED by V8-2 at the final shortfall consumer.** |
| sol BFCL-V6-2 | **CLOSED for actual dev-byte hashing; BLOCKED by V8-1 for cross-split certificate consumption and authorization order.** |
| sol BFCL-V6-3 / fable FV6-3 | **CLOSED.** Clamp is bidirectional and >16 is rejected, not converted into a method result. |
| sol BFCL-V6-4 | **CLOSED.** Safety and execution share `normalize_call()`. |
| sol BFCL-V6-5 / fable FV6-5 | **CLOSED for the pinned target commit.** Full repo-local runtime import chain and provenance fields are present. |
| sol BFCL-V6-6 / fable FV6-2 | **PARTIAL (V8-3).** Turn facts, A3, final report, and safety phases are correct; preflight full case competence is not. |
| fable FV6-4 | **PARTIAL / BLOCKER (V8-2).** Counts and sealed checks exist, but the shortfall exact-total exception violates Amendment 4's exact per-role rule. |
| fable FV6-6 | **CLOSED.** Dead matcher seed was removed and stable-source tie-break metadata is explicit. |

## Launch instruction

Do not launch the registered 1.7B dev preflight and do not reuse any shakedown
output as its certificate. Implement V8-1 through V8-3, add the consumer-path
regressions above, re-register the changed harness/module/data contract, and
rerun the CPU census from the frozen commit. Only after a reviewer confirms
that a dev-produced certificate authorizes the sealed contract **before any
sealed row access**, and that every usable comparator has exact per-role
equality, may the registered preflight start in a fresh output directory.

**VERDICT: UNSOUND**
