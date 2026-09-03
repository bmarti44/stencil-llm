# Brief: bfcl-evict-v4 — bring the BFCL harness from registration v3 (commits 955aeef, 31e7cb9) to the REGISTERED v7 + AMENDMENT 1

## Objective
Governing text: LEDGER-PLAN.md "SELECTOR v2 — POST-DEVELOPMENT EVALUATION, LEG A (BFCL V3 multi-turn) — v7" plus
"LEG A AMENDMENT 1" (the last sections). Build to it VERBATIM; where v7 and the v3 code differ, v7 wins. Your handoff
(WORKLOG.md "bfcl-evict-v3 coder handoff") describes the v3 baseline: scripts/bfcl_mt.py, src/stencil/bfcl.py,
src/stencil/selector_v2.py, tests/test_bfcl_evict_v3.py (29 tests). Implement the deltas, each with a CPU test:
1. Decisions (i)-(vii) and the comparator resource identity: clf_control matched one-to-one on token width and
   source-turn age (seed 20260903; disjoint; no repetition/rotation); on no-shortfall turns also role-matched with
   exact per-role columns; shortfall filled from the other role, recorded control_role_shortfall + per-role deltas,
   stays in A1, excluded from the no-shortfall sensitivity; A1 uninformative only if no width/age match exists in
   either role. recency_pinned: most recent candidates from the user+tool universe under the treatment's exact
   per-role quota and echo budget; impossible exact match -> A2 uninformative (match_impossible recorded).
   tool_swap_echo: selected user spans kept; each selected tool chunk replaced by a disjoint tool chunk matched on
   width and age; no other-role fallback; impossible -> A4 uninformative. Column clamp for every comparator: spans
   admitted whole in match order until the next would exceed the quota; the last admitted span truncated at a Qwen3
   token boundary so the count is exact; its echo entry is the truncated text. Every comparator receives the echo of
   its own spans under the common framing, clamped to the treatment's echo token count by whole spans;
   abs(echo_token_delta) <= 16 required (dev: larger stops preflight; sealed: that comparator's contrast becomes
   uninformative; no turn dropped).
2. Pin overflow exactly as v7: treatment drops whole pins in reverse (P, recency, stable-source) rank with their echo
   entries until it fits; comparators built after; pin_overflow_total when prefix + no-echo turn-t message alone
   exceed K (all pins/echo dropped, all non-full arms proceed, turn stays primary); never drop current-turn or prefix
   ids. Echo entries = the arm's pinned spans after any drop, never an unpinned candidate.
3. Candidate hygiene: tool output split newline-first (empty dropped), then the registered splitter, then 128-token
   chunking; ranking (P desc, recency, stable source order); drop any candidate containing the five literal markers OR
   any special/added token id of the trunk tokenizer (echo_dropped_control_tokens); an emitted chat-control echo event
   is a safety failure; scorer truncation counted (scorer_truncated_candidates), never aborts.
4. Statistics: exact one-sided paired sign-flip over case means (enumerate 2^k; zeros retained; ties counted in the
   upper tail; no mid-p); Holm alpha 0.05 over eligible A1-A3; A4 separate; k < 6 -> INCONCLUSIVE (leg) / uninformative
   (per contrast, A3 after 40,960 exclusions); p-grid and k reported; the LEG B continuity-corrected clustered LB
   reported descriptively; A3 gate = cluster-mean point estimate of full − base > 0 on the A3 population.
5. Safety, case-level: a case counted once per type if any sub-step has the event; timeouts = 0; truncated <= full+1;
   degenerate (4-gram test on NON-truncated generations only — remove the `if truncated: return True` branch, unit
   test it) <= full (+ the degenerate-only vacuity guard); invalid <= full+1; repeated-call (normalized call identical
   to an earlier ground-truth or echoed call and absent from the turn's ground truth) <= full+1; chat-control echo
   events = 0; treatment breach fails every contrast; comparator breach makes its contrasts uninformative.
6. Position overflow: turns whose full prompt exceeds 40,960 positions: full does not generate (NA; position_overflow
   in full's reporting); any arm whose within-turn cache exceeds 40,960 at any step stops generating (truncated event,
   scores fail).
7. Preflights as v7 (1)-(6): floors on full AND base (teacher-forced; the exact fractions in v7); determinism traces;
   feasibility gate; cost projection with the 30 GPU-h arm-cut rule (cut removes tool_swap_echo, clf_pinned,
   role_pinned and free-running; A4 uninformative); frozen constants + the full hash list (K, B, T, E, threshold,
   header, seed, registration hash = sha256 of the v7+A1 section text, harness, selector artifact, trunk weights,
   trunk tokenizer, cohorts.json, chat template, vendored checker) written before anything runs and refused on
   mismatch; invariants (6) asserted on every dev generation with the AMENDMENT 1 lead-in (clf_control's per-role
   equality only on no-shortfall turns).
8. Reported fields exactly as v7's "Reported, not gated" paragraph (teacher-forced case pass for every arm;
   free-running for base and clf_pinned_echo only; echo-copy rate with NO exclusion).
`--split sealed` stays guarded by STENCIL_SEALED_RUN=1 and is NOT to be run. NEVER read
data/bench/ifeval_input_data.jsonl. Never modify data/bench/*. No fitting on BFCL.

## Allowlist
See bfcl-evict-v4.allow.

## Tests first (TDD, rule 1)
RED first for every delta above. Run ONLY tests/test_bfcl.py tests/test_bfcl_evict_v2.py tests/test_bfcl_evict_v3.py
and your new tests/test_bfcl_evict_v4.py. DO NOT run the full suite.

## GPU policy
The GPU is BUSY (registered Multi-IF 909 run, then queued probes): do NOT launch any model process; record the exact
deferred smoke/preflight commands in WORKLOG. Never wait on a lock; never signal any process.

## Acceptance
CPU tests green; ruff clean; commit EARLY and often; deferred commands recorded.

## Ledger handoff
Append to WORKLOG.md: what changed (file:line) per delta, the exact sign-flip implementation and a worked k=6 example,
the hash list as written to meta, ambiguities and choices, deferred commands.
