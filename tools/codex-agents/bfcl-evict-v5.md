# Brief: bfcl-evict-v5 — close the harness review findings (sol BFCL-V4-1..7; fable's harness-v4 review if present) before any BFCL GPU step

## Objective
Governing text: LEDGER-PLAN.md "LEG A ... v7" + "AMENDMENT 1" + "AMENDMENT 2". Reviews to close, item by item, with
the reviewer's "Required fix" lists as the spec: results/harness-v4-review-sol.md (BFCL-V4-1 CRITICAL sealed-cohort
contents parsed by the dev loader; V4-2 CRITICAL preflight failures do not stop execution and sealed authorization is
not tied to a passed preflight; V4-3 HIGH the Amendment-2 primary_claim_status decision table is absent and
registered_contrasts_pass wrongly gates on A2/global safety; V4-4 HIGH safety event counting — degenerate must
return False when truncated, canonical repeated-call set built before generation, unmatched tool-call markers must
yield an invalid record; V4-5 HIGH freeze/resume identity must cover a canonical manifest of every executing module
and records must carry the meta digest, summaries must use exactly the cohort id list; V4-6/7 MEDIUM invariant report
faithfulness and field fidelity) and results/harness-v4-review-fable.md (read it if it exists when you start; apply its
fixes too; note any conflict with sol's and resolve toward the registered text).
Hard requirements:
1. Sealed boundary (V4-1): `load_cases("dev")` must never parse a sealed row. Build, in a one-time authorized
   step (scripts/bfcl_seal_index.py, run by you now on CPU — it reads the category files ONCE to write a per-id byte
   offset index data/bench/bfcl_v3_mt/offsets.json and its sha256 into data/bench/pins-manifest.json — this is the
   only permitted full read and is recorded in WORKLOG), then make the dev loader seek/read only the 32 dev offsets;
   assert every returned id is in the requested cohort before decoding; a test wraps file reads/seeks and proves the
   dev loader never touches a sealed offset. NOTE: data/bench/* is otherwise frozen — the ONLY additions allowed are
   offsets.json and the manifest entry; no existing file changes (assert their hashes unchanged in the test).
2. Preflight gating (V4-2): every registered preflight failure raises and writes status INCONCLUSIVE; `run --split
   sealed` requires STENCIL_SEALED_RUN=1 AND a preflight certificate (preflight.json with all gates passed, the frozen
   constants, the trunk choice, the arm set, and the manifest hash) whose digest is bound into the sealed run's meta;
   any mismatch (trunk, arms, constants, harness manifest) refuses to start.
3. Decision table (V4-3 + Amendment 2): `primary_claim_status` function with the complete registered ordering,
   tested as a table; A2 and A4 as separate claim fields; A3 fields split (headroom_gate_passed, k, status, eligible).
4. Safety (V4-4) exactly as registered definitions.
5. Identity (V4-5): canonical manifest hash over every executing module (scripts/bfcl_mt.py, src/stencil/{bfcl,
   selector_v2, ledger, stats, qwen3, qwen_cache}.py, vendored checker/executor files, chat template), individual
   hashes stored; records carry the meta digest; summarize_records validates records against the exact cohort id list
   and the digest and refuses stale or foreign records.
6. Faithful invariant reporting and fields (V4-6/7) as sol lists them.
`--split sealed` is NOT to be run. NEVER read data/bench/ifeval_input_data.jsonl. No fitting on BFCL. GPU: BUSY —
do not launch any model process; record deferred commands.

## Allowlist
See bfcl-evict-v5.allow.

## Tests first (TDD, rule 1)
RED first for each numbered item (the seek-only loader test is mandatory and must fail on the current loader). Run
ONLY tests/test_bfcl.py tests/test_bfcl_evict_v{2,3,4}.py tests/test_sealed_guard.py and your new
tests/test_bfcl_evict_v5.py. DO NOT run the full suite.

## GPU policy
No GPU. Never wait on a lock; never signal any process.

## Acceptance
CPU tests green; ruff clean; offsets index + manifest entry committed with the WORKLOG record of the one-time read;
commit EARLY and often.

## Ledger handoff
Append to WORKLOG.md: each finding -> fix (file:line), the one-time index build (what was read, hashes), the
decision-table test, the certificate format, deferred commands.
