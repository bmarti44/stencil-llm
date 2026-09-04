# Brief: sc1-harness-v2 — close BOTH harness reviews (astra F1-F11 UNSOUND; fable H1, M1-M3, lows) on commit 0fe7fe7

## Objective
Governing text unchanged: LEDGER-PLAN.md "SC1 ... (DRAFT v2)" + data/sc1/AUTHOR-CONTRACT.md (v2). Reviews to close,
every finding, no negotiation of severities: results/sc1-harness-review-astra.md (F1-F11 HIGH + mediums/lows) and
results/sc1-harness-review-fable.md (H1 HIGH: single-turn filler makes U << B so the budget never binds and clf can
only be a subset of rule -> multi-turn role-mixed filler from a large pool + validation rule "U columns >= 2B and the
rule arm records at least one budget skip" tested with the real tokenizer; M1 resume cost projection; M2 infrastructure
exceptions must be resumable, never exclusive invalid.json; M3 add a `determinism` mode producing the certificate
`setup` requires; lows: T flag at 255+EOS, repetition periods, smoke never-reuse enforced mechanically, real-tokenizer
segmentation identity test, --out default). Astra's F1-F11 in one sentence each: scheduling must not re-parse/re-hash
the journal per attempt (O(1) incremental accounting); --out must not reset one-shot execution or cumulative cost
(bind the study to a registered study id); resume projection uses remaining attempts only; the author-facing input
must not expose policy identities or execution order; literal-leakage checks mandatory (an OLD episode whose final
request contains the answer must FAIL validation); source validation must enforce assigned scope, user authority,
and public-tool-return/state-trace agreement; six negatives must be semantically distinct and applicable (whitespace
variants rejected); raw-text corruption must catch unauthorized additions; exact JSON numerics (Decimal, no float
equality); pairwise semantic review signatures bind both sources; determinism certificate requires cross-process
replication of each cell. Read each review for the exact fix + test it prescribes and implement that. Where a fix
needs a text clause the v2 registration lacks, take the most conservative reading and record it in the WORKLOG
handoff as "ambiguity for Stage 1" — do not edit LEDGER-PLAN.md or the contract.

## Allowlist
See sc1-harness-v2.allow.

## Tests first (TDD, rule 1)
RED first: one failing test per finding (name tests by finding id: test_astra_f1 ... test_fable_h1 ...). Run ONLY
tests/test_sc1.py tests/test_eval_data_separation.py tests/test_sealed_guard.py tests/test_no_side_effect_imports.py.
DO NOT run the full suite.

## GPU policy
No GPU: the registered BFCL preflight owns it. CPU fixtures + real tokenizer only; never launch a model process; never
wait on a lock; never signal any process. Never read the sealed IFEval input file. Never modify data/bench/*.

## Acceptance
All finding-named tests green; existing tests green; ruff clean; `scripts/sc1.py validate data/sc1/smoke` PASS with
the regenerated smoke bank (multi-turn filler; U >= 2B on every smoke episode); manifest regenerated and verified;
commit EARLY and often with explicit pathspecs.

## Ledger handoff
Append to WORKLOG.md "## <date> — sc1-harness-v2 handoff": per finding id -> commit + test name; new manifest hash;
test command + counts; Stage-1 ambiguities list. Do not edit LEDGER-PLAN.md.
