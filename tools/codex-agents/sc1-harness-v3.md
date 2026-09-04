# Brief: sc1-harness-v3 — close the two v2 re-reviews (astra R1-R8 UNSOUND; fable N1-N10) on commit 5f7bcbf

## Objective
Governing text unchanged: LEDGER-PLAN.md "SC1 ... (DRAFT v2)" + data/sc1/AUTHOR-CONTRACT.md (v2). Close every finding
in results/sc1-harness-v2-review-astra.md (R1 short numeric output escapes the checker and invalidates the study;
R2 no exclusive execution owner -> duplicate work / overwritten allocation state; R3 multiline public JSON bypasses
trace correspondence, F6 partial; R4 text edit permissions checked against the oracle instead of the original protected
artifact, F8 partial; R5 eight empty timeouts certify determinism, F11 partial; R6 caught partial journal appends made
unrecoverable, F16/M2 partial; R7 applicable raw-text obsolete/scope attacks cannot pass the validator, F7 partial;
R8 600-token per-turn safeguard enforced only during filler append; plus every PARTIAL row in its table) and in
results/sc1-harness-v2-review-fable.md (N2 grammar filler-turn guidance vs the 600-token cap -> text + error message,
re-run smoke; N3 manifest/science_hash bind the LIVE LEDGER-PLAN.md -> hash a registration SNAPSHOT file
(data/sc1/registration-snapshot.md, byte copy of the governing SC1 v2 section + contract at freeze time) instead;
N4 vacuous F1 test (read_bytes) and M1 boundary test; N5-N10 lows incl. the registry location and the private order
stream written into the author-input file; N1 add a `real_candidate_columns` audit field and pressure report per
episode). Read each review for the exact fix + test it prescribes. For each Stage-1 ambiguity both reviewers list
(JSON schema for Stage 1, transcript/attempt-history schema, canonical tool envelopes, text edit law, abandoned
determinism cost carry-over, filler-dominance disclosure), do NOT edit LEDGER-PLAN.md: write the proposed clause text
into data/sc1/STAGE1-CLAUSES.md (proposals only) so the orchestrator can append them as a dated amendment.

## Allowlist
See sc1-harness-v3.allow.

## Tests first (TDD, rule 1)
RED first: one failing test per finding (test_astra_r1 ... test_fable_n2 ...), and fix the two vacuous tests (N4).
Run ONLY tests/test_sc1.py tests/test_eval_data_separation.py tests/test_sealed_guard.py tests/test_no_side_effect_imports.py.
DO NOT run the full suite.

## GPU policy
No GPU: the registered BFCL preflight owns it. CPU fixtures + real tokenizer only; never launch a model process; never
wait on a lock; never signal any process. Never read the sealed IFEval input file. Never modify data/bench/*.

## Acceptance
All finding-named tests green; existing tests green; ruff clean; smoke bank regenerated + `validate` PASS with the
pressure report; manifest regenerated against the registration snapshot and verified; commit EARLY and often with
explicit pathspecs.

## Ledger handoff
Append to WORKLOG.md "## <date> — sc1-harness-v3 handoff": per finding id -> commit + test; new manifest hash;
snapshot hash; test counts; pointer to data/sc1/STAGE1-CLAUSES.md. Do not edit LEDGER-PLAN.md.
