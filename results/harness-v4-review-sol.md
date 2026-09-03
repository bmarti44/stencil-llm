# BFCL harness v4 review — registration v7 + Amendments 1–2

Reviewer: sol, 2026-09-03.  Scope: commits `a496212` and `cdad4ea`, with the
current governing Amendment 2 at `9fd70bd`.  The implementation files are
unchanged between `a496212` and `HEAD`; the later commits change only
`WORKLOG.md` and `LEDGER-PLAN.md`.

Execution constraints were honored: all checks were foreground and CPU-only
with `CUDA_VISIBLE_DEVICES=''`; no model or GPU process was launched, no process
was signalled or terminated, and neither the sealed IFEval input nor any BFCL
case/answer contents were opened.  This file is the only review output.

## Bottom line

The core turn construction, eviction primitive, selector mechanics, comparator
resource matching, and exact sign-flip calculation are substantially present.
The harness is nevertheless not safe to launch on the sealed cohort.  Its dev
loader parses all mixed case and answer files, including sealed-cohort rows; its
preflight records failures but does not enforce most gates; a sealed run is not
bound to a passing preflight; and Amendment 2's outcome rules are not implemented
in the summary.  Two registered safety definitions are also computed incorrectly.

## Findings, ordered by severity

### BFCL-V4-1 — CRITICAL — the dev path reads sealed-cohort contents it does not evaluate

`scripts/bfcl_mt.py:121-134` reads every row of all four `cases_*.jsonl` files
and all four `answers_*.jsonl` files into dictionaries and only then selects the
IDs in `cohorts.json[split]`.  The repository has mixed category JSONLs, not
physically separated dev/sealed files.  Therefore `load_cases("dev")` parses the
64 sealed cases and their ground truths during the dev preflight even though it
returns only the 32 dev rows.  `preflight()` calls that path at least twice
(`scripts/bfcl_mt.py:1251,1265`).

This is an actual non-evaluation read, not a hypothetical fitting path.  I found
no selector fitting or result-adaptive threshold path, and the scorer remains
CPU/eval/no-grad, but the sealed-data boundary itself is broken.

Required fix:

1. Replace the scan-and-filter loader with a frozen, hash-registered per-ID byte
   offset index, or physically separate registered dev and sealed case/answer
   files.  `load_cases("dev")` must seek/read only the 32 dev records; it must not
   scan or JSON-parse a non-dev line.  Build the index during an authorized
   sealing step, not by a dev/preflight process after sealing.
2. Bind the index/file hashes into the BFCL manifest hash and meta, and assert
   that every returned ID is exactly in the requested cohort before any item is
   decoded.
3. Add a test that wraps file reads/seeks and proves the dev loader never touches
   any registered sealed offset.  A test that merely checks returned IDs is
   insufficient.

### BFCL-V4-2 — CRITICAL — preflight failures do not stop execution, and sealed authorization is not tied to preflight

`preflight()` computes `deterministic`, `competence_ok`, feasibility, the
30-GPU-hour decision, and the reduced-cost stop flag, but—with the exception of
the echo-delta error and Python assertions—only writes those values to
`preflight.json` and returns successfully (`scripts/bfcl_mt.py:1250-1454`).  In
particular:

- a failed BASE-vs-BASE determinism check does not raise;
- failed 1.7B competence does not prevent treating that invocation as successful,
  and failed 4B competence does not stop it;
- failed pressure/tool feasibility does not raise;
- projected full and reduced cost above 30 GPU-h does not raise; and
- nothing in `run --split sealed` reads or validates a preflight report.

The sealed guard at `src/stencil/bfcl.py:873-879` checks only
`STENCIL_SEALED_RUN=1`.  A caller with that flag may choose either trunk, either
arm set, changed generation settings, a new output directory, and even
`--limit 1`, without a passing registered preflight.  This can consume the
one-shot cohort under an invalid design.

Required fix:

1. Have preflight write its report first and then exit nonzero on every failed
   registered gate.  A 1.7B competence failure should produce an explicit
   `FALLBACK_REQUIRED_4B` state; a 4B failure, determinism failure, feasibility
   failure, invariant failure, or reduced projection above 30 hours must produce
   `INCONCLUSIVE` and no sealed certificate.
2. Compute the reduced projection from the measured seconds of exactly
   `REDUCED_ARMS`, not `full_projection * 5/8` (`scripts/bfcl_mt.py:1339-1342`).
3. Emit a machine-validated preflight certificate containing the selected trunk,
   exact arm set/cut decision, all gate booleans and counts, generation settings,
   registration hash, complete code/data/model hashes, and a digest of the
   certificate payload.
4. Require that certificate on every sealed invocation and validate it before
   model loading or BFCL item access.  The sealed CLI must reject `--limit`, a
   trunk/arm/settings/hash mismatch, a non-passing certificate, or a requested
   full arm set when the certificate requires the cut.  Keep the environment
   guard as an additional authorization check.
5. Reject `preflight --arm-cut`; it currently produces reduced records and then
   indexes the absent `clf_pinned` arm at `scripts/bfcl_mt.py:1294`.

### BFCL-V4-3 — HIGH — Amendment 2's outcome table is absent and the available aggregate is wrong

`summarize_records()` sets `leg_status` only from the global six-cluster floor
(`src/stencil/bfcl.py:1405-1407`).  It never emits the registered primary claim
state.  A CPU synthetic record set with six primary clusters and a
`clf_control.match_impossible` event produced:

```text
a1 status = uninformative; leg_status = evaluated
```

Amendment 2 requires that result to be `INCONCLUSIVE`.  Likewise, an A3
population reduced to five clusters is correctly marked uninformative in the
contrast row, but `a3.eligible` remains `true` and `a3.status` remains `null`
(`src/stencil/bfcl.py:1412-1418`).

The only aggregate decision, `registered_contrasts_pass`, requires *every* Holm
row to pass and globally requires every arm's safety
(`src/stencil/bfcl.py:1443-1445`).  A CPU example in which A1 and A3 both reject
but A2 does not gave
Holm `{A1: true, A3: true, A2: false}` and
`registered_contrasts_pass=false`.  That contradicts the registered rule: A2
non-rejection only removes the learned-ranking claim and does not block the
primary benefit claim.  A4's `passed` field has the same unrelated-global-safety
problem at lines 1420-1425.

Required fix:

1. Add an explicit `primary_claim_status` decision function, tested as a complete
   table.  Apply, in order: global `k<6 -> INCONCLUSIVE`; any A1-uninformative
   reason `-> INCONCLUSIVE`; treatment safety breach `-> UNSUPPORTED`; A3
   uninformative plus Holm-passing A1 `-> SUPPORTED_A1_ONLY` with the registered
   “no measurable full-context headroom” label; A3 uninformative plus failing A1
   `-> UNSUPPORTED`; eligible A3 `-> SUPPORTED` only when both Holm-adjusted A1
   and A3 pass, otherwise `UNSUPPORTED`.
2. Do not gate that state on A2.  Keep A2's Holm result and the exact registered
   non-rejection wording as a separate claim field.
3. Split `a3.headroom_gate_passed`, `a3.k`, `a3.status`, and `a3.eligible`; set A3
   uninformative when its post-exclusion `k<6` even if the headroom mean is
   positive.
4. Gate A4 only on A4's method status plus treatment and `tool_swap_echo` safety,
   never on reporting-only arms.

### BFCL-V4-4 — HIGH — the registered safety events are under/over-counted

First, `_degenerate(ids, truncated)` ignores `truncated` entirely
(`scripts/bfcl_mt.py:638-642`).  The registration says the repetition test is
evaluated only on non-truncated generations.  The CPU counterexample
`_degenerate([1,2,3,4] * 20, truncated=True)` returned `True`; it must not create
a degenerate event.

Second, repeated-call detection seeds `history_call_raw` only from earlier
ground-truth calls in teacher mode (`scripts/bfcl_mt.py:693-702`) and later
generated calls in free mode.  It never extracts normalized calls present in the
actual echoed entries, despite the registered definition “earlier ground-truth
or echoed call.”  Those events can therefore be missed.

There is a smaller invalid-call hole: `parse_tool_calls()` only returns regex
matches with both tags (`src/stencil/bfcl.py:808-826`), so an emitted unmatched
`<tool_call>` marker produces no invalid call record instead of a parse failure.

Required fix:

1. Begin `_degenerate` with `if truncated: return False`, then apply the frozen
   4-gram calculation only to non-truncated response IDs.  Test a long repetitive
   truncated response, not only the existing three-token example.
2. Before generation, build a canonical repeated-call set from prior ground
   truth *and from `plan["entries"]`*.  Normalize valid echoed tool calls with the
   same function-name and sorted-argument canonicalizer used for generated and
   ground-truth calls.  Compare each generated valid call against that union and
   the current-turn ground-truth exclusion.
3. Make unmatched/open/close tool-call markers yield an invalid parsed record,
   and add paired tests for malformed JSON and unmatched tags.
4. Keep per-case `any(step event)` aggregation; that portion at
   `src/stencil/bfcl.py:1179-1249`, the +1 rules, and the degenerate-only vacuity
   guard otherwise match the registration.

### BFCL-V4-5 — HIGH — freeze and resume identity do not cover the executing harness, and stale records can enter summaries

The meta's `harness` hash covers only `scripts/bfcl_mt.py`
(`scripts/bfcl_mt.py:1030-1042`).  The eviction, matching, statistics, safety,
schema, and selector behavior lives in `src/stencil/bfcl.py`,
`src/stencil/selector_v2.py`, `src/stencil/stats.py`, and
`src/stencil/qwen3.py`; none is bound by that hash.  Editing one of those files
after preflight would leave an existing meta acceptable.  A fresh sealed output
directory also records whatever hashes happen to exist then rather than comparing
them with preflight.

On resume, records do not carry a meta/certificate digest.  Schema validation
accepts either full or reduced arms regardless of the output meta
(`src/stencil/bfcl.py:958-1024`).  After processing, `run()` summarizes every
`records/*.json` glob entry rather than exactly the current cohort ID list
(`scripts/bfcl_mt.py:1142-1147`).  An extra/stale case or a record produced under
a different allowed arm set can silently enter the result.  `--limit` is also
absent from meta.

Required fix:

1. Replace the single-file harness hash with a canonical tree/manifest hash over
   every executing local source listed above (plus any other imported
   experiment-specific module).  Store individual hashes for auditability.
2. Compare sealed meta to the passing preflight certificate; do not merely create
   a new self-consistent meta.
3. Store `run_identity_sha256` in every case record and require it to equal the
   active meta/certificate digest on resume.  Require record arms to equal
   `meta["arms"]` exactly.
4. Build `all_records` by iterating the registered cohort IDs in registered
   order.  Reject missing, duplicate, unexpected, or extra record files instead
   of globbing them into the summary.  Include `limit` in nonsealed run identity
   and forbid it for sealed runs.

### BFCL-V4-6 — MEDIUM — the preflight invariant report overstates what was checked

The important cache equation, protected-prefix check, and comparator quota checks
are real assertions.  However, `passed_fraction` is hard-coded to `1.0`
(`scripts/bfcl_mt.py:1241-1247`), and the registered candidate-source assertion
(`candidate.message_index < current user message index`) is not made or counted
by `assert_dev_invariants()`.  The report also does not expose a per-invariant
numerator/denominator, so “100%” is not independently auditable.

Required fix: assert candidate message indices in `select_history_spans()` and
again through the actual preflight consumer; return named `{passed, n}` counters
for each of the six registered invariant families and derive the aggregate from
those counters.  Never print a constant pass fraction.

### BFCL-V4-7 — MEDIUM — some registered overflow/comparator/report fields are not faithful

- `base` and `full` return early from `_turn_plan()` at
  `scripts/bfcl_mt.py:420-429`.  Consequently a shared
  `pin_overflow_total` turn is recorded as false for `base`, even though the
  registration makes total overflow a property under which all non-full arms
  proceed with zero pins/echo.  Compute and record the shared total-overflow fact
  before the arm early return.
- `tool_swap_plan()` groups every selected USER entry before every replacement
  TOOL entry (`src/stencil/bfcl.py:650-681`).  This does not preserve the
  treatment's registered probability/rank order and can change which whole echo
  entries survive the E cap.  Return the tool match paired to each selected tool
  and rebuild entries by walking `kept` in its original order.
- `role_pinned` is derived from messages that produced at least one selector
  candidate (`src/stencil/bfcl.py:757-775`).  A prior user message with no
  splitter-eligible two-letter sentence contributes no columns, contrary to “all
  prior user columns.”  Derive this reporting arm directly from prior USER
  message locations.
- The top-level `reported.non_evicting_turns` is only a count
  (`src/stencil/bfcl.py:1427-1442`), not the registered echo-only stratum outcome.
  Add per-arm pass/effect summaries for that fixed stratum.  Also aggregate
  scorer truncations, dropped-control candidates, overflow-dropped columns,
  per-role shortfall deltas, budget use, echo deltas, and position exceedances;
  the raw records contain many but not all of these fields.

These do not rescue the critical launch blockers, but they must be fixed before
the registered report is produced.

## Item-by-item disposition

1. **Teacher forcing and identity: verified.**  `build_teacher_history()` executes
   and renders prior ground-truth calls/responses; every semantic turn is an
   independent branch, and scoring uses ground truth through `t-1` plus the arm's
   current turn.  `run_case()` asserts equality of the unaugmented rendered
   context IDs across all arms at every turn.  Environment keys include run,
   case, arm, and turn, so the vendored global instances are isolated on the
   normal one-process path.
2. **Eviction: verified with BFCL-V4-7 reporting defects.**  The message-index
   range and protected system/contract prefix are correct; prefill evicts before
   the current-turn suffix; current/prefix IDs survive; the cache persists across
   tool steps; lowest-ranked whole treatment pins and echo entries are dropped;
   comparators are constructed afterward.
3. **Selector/echo: core mechanics verified.**  Prior USER sentence splitting,
   TOOL newline-first splitting, 128-Qwen-token chunks, empty context, true role,
   `longest_first,max_length=192`, truncation counting, threshold/ranking/whole
   budget fill, literal plus added/special-ID rejection, JSON quoting, exact
   header, pinned-only entries, and E=1024 are implemented.  Tool-swap order and
   the reporting-only all-user arm need BFCL-V4-7.
4. **Comparators: mostly verified.**  Control matching is seeded, disjoint,
   one-to-one on width/source-turn age, without reuse; other-role shortfall is
   recorded without making it automatically impossible.  Recency uses the same
   universe and permits treatment overlap; tool swap is same-role/disjoint;
   clamp truncation uses Qwen boundaries; comparator echo deltas are checked at
   16 and sealed summary disposition is contrast-wide.  Preserve selected-rank
   order for tool swap as above.
5. **Statistics: arithmetic verified; decision reporting fails.**  Independent
   rational enumeration agreed with the helper on grids `1/64`, `2/64`, `2/64`,
   and `14/64`, including zeros and upper-tail ties.  Three `1/64` p-values pass
   Holm at `1/60`, `1/40`, and `1/20`.  Eligible A1–A3 and separate A4 handling,
   post-40,960 A3 values, the positive-headroom gate, and the descriptive
   continuity-corrected LB are implemented.  BFCL-V4-3 breaks the registered
   final disposition and A3 status reporting.
6. **Safety: case aggregation and numeric inequalities verified; event
   definitions fail.**  See BFCL-V4-4.  The degenerate-only vacuity guard is
   correctly limited to degenerate.
7. **Preflight/freeze/invariants: not satisfied.**  Meta is written before model
   loading, current constants are correct, and the current registration hash
   `8be398906a8ef159cd5a349add612c7f1fd629a8462a87707351c215ec88eb82`
   includes both amendments.  Current harness/artifact/trunk/tokenizer/cohort/
   template/checker hashes recompute to the values recorded by the handoff except
   for the expected Amendment-2 registration-hash change.  BFCL-V4-2, V4-5, and
   V4-6 prevent those values from acting as a sealed gate.
8. **Reported fields: partial.**  Teacher-forced case pass, primary per-turn pass,
   free-run final pass/first divergence, validity, echo-copy, raw per-turn cache
   columns, and several event counts exist.  The registered outcome state and
   echo-only stratum do not; several event/dose aggregates are incomplete.
9. **Sealed guard: present but insufficient.**  The environment check refuses an
   unflagged sealed split, as its tests show.  It does not prevent partial cohort
   execution or bind authorization to a passing preflight, and the dev loader has
   already crossed the sealed-data boundary.

## CPU verification

- `pytest -q tests/test_bfcl_evict_v2.py tests/test_bfcl_evict_v3.py
  tests/test_bfcl_evict_v4.py`: **32 passed**.
- Independent exact-enumeration checks matched `exact_sign_flip()` on four
  vectors, including a retained zero and unequal rational case means.
- Synthetic summary checks reproduced every BFCL-V4-3 counterexample and the
  BFCL-V4-4 truncated-degenerate counterexample above.
- `git diff --check` was clean.  A targeted Ruff invocation found one unrelated
  existing unused local, `f_lo`, at `src/stencil/stats.py:79`; it does not affect
  the registered calculation.

## State and leakage conclusion

No normal-path in-memory state leak across arms or cases was found: cases are
deep-copied, caches are per arm/turn, the selector is inference-only, and BFCL's
module-global environments receive distinct names.  The persistent resume path
can mix stale/foreign case records as described in BFCL-V4-5.  The only direct
non-evaluation BFCL read found in the runnable harness is the critical eager
population load in BFCL-V4-1; manifest hashing is expected and no training write
path was found.

## VERDICT

Do not launch the BFCL sealed run.  BFCL-V4-1 and BFCL-V4-2 are
registration/sealing blockers; BFCL-V4-3 through V4-5 can change the reported
scientific disposition even if a run completes.  Implement the instructions
above, add adversarial CPU tests for each counterexample and gate transition,
re-register the changed harness and complete source manifest, and rerun the dev
preflight before any sealed authorization.

**VERDICT: UNSOUND**
