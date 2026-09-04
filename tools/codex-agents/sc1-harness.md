# Brief: sc1-harness — build the SC1 executable artifacts (harness + expander/checker toolchain) to LEDGER-PLAN "SC1 ... DRAFT v2"

## Objective
Governing text: LEDGER-PLAN.md section "SC1 — LEARNED vs RULE SELECTOR ... (DRAFT v2, 2026-09-04)" and
data/sc1/AUTHOR-CONTRACT.md (v2). Reviews that shaped them: results/sc1-review-{astra,fable,kimi}.md (their
"missing pieces" lists M1-M12 / items 1-14 are the checklist). Design source: results/astra-research-blockers.md §3/§5.
Build, CPU-tested, everything the v2 text names as an executable artifact, so the artifact freeze (stage 2) can be
hashed. Reuse the eviction core (pre-query eviction, pin persistence, protected prefix) from src/stencil/bfcl.py /
src/stencil/qwen3.py; do NOT reuse the scoring-dependent helpers the reviews flagged (bfcl.py budget_history_spans
break-at-first-oversize, recency quotas, role_pinned_spans in scripts/multiif_evict.py). Deliverables:
1. src/stencil/sc1.py — common UNSCORED candidate builder (frozen segmentation identical to the classifier's, user
   sentences + 128-token tool chunks, straddle rule per v2), recent-window geometry per v2, clf ranking
   (P(rule)+P(fact), threshold 0.5, tie rule per v2) and rule ranking (prior-user newest-first then prior-tool
   newest-first, ties by source offset), the NEW skip-and-continue admission (named as in v2), the echo builder
   (selection order and presentation order exactly as v2 registers; header + role/turn labels count toward E),
   intervention counter (must be 0), invalid/truncated/repetitive flags with the v2 definitions (repetitive =
   normalized 4-token block repeated >= 8 CONSECUTIVE times), latency split, per-arm record writer with every
   field v2 lists under "Reported".
2. src/stencil/sc1_episodes.py — episode JSON schema (v2 record format), the deterministic expander from the
   structured source specification, the code-generated checker runner (editing: schema/content rules + protected
   set; tool-work: single call into an isolated in-memory record store, complete resulting state checked incl.
   protected records), mutation generator (six distinct applicable negatives with obligation-linked substitutes),
   positive-reference execution through the SAME runner, reference-fits-256-tokens check, commissioning sampler
   (SHA-256 stream convention from the contract, master seed 20260904), realized-count report, sibling fingerprint.
3. scripts/sc1.py — modes: `validate` (episode bank: schema, expander determinism, reference passes, all mutations
   fail, age measured by the frozen renderer, fingerprints), `smoke` (8 harness-authored synthetic episodes under
   data/sc1/smoke/, never reused), `setup` (32 episodes, arms full/evicted/clf/rule, applies the setup gate and
   writes the gate certificate BEFORE any final outcome can be read), `final` (256 episodes, clf+rule only, arm order
   per v2, fresh state per run, resumable by paired episode index, halts if projected cost exceeds the cap),
   `analyze` (exact one-sided McNemar, b/c/N, D_hat, Clopper-Pearson union interval, adoption rule i-iv, flags U/K).
   Manifest + hashes for code, classifier files (sha256 must equal the LEG B record), episodes, contract; refuse to
   run `final` unless the setup certificate exists and hashes match. Trunk flag `--trunk 4b` (default) / `1.7b`.
4. tests/test_sc1.py — CPU only, tiny fake trunk/tokenizer fixtures as in tests/test_bfcl*.py: candidate builder
   identity across arms; admission skip-and-continue; echo cap and drop order; window geometry; flags (incl. a
   scattered 4-gram NOT flagged, a consecutive one flagged); McNemar exact values (b=13,c=0 -> p=2^-13; b+c=0 -> 1;
   fable's power cell reproduces 0.5086 at N=256,q=0.20,delta=0.05); expander determinism; checker: reference
   passes, each of six mutations fails, reject-all checker detected; sampler digest example from the contract;
   final refuses without setup certificate; intervention counter nonzero aborts.
Write the 8 smoke episodes yourself (fictional, NOT from any benchmark, NOT reused later). Record in WORKLOG the
manifest hash and any v2 clause you found ambiguous (take the most conservative reading; do not edit LEDGER-PLAN).

## Allowlist
See sc1-harness.allow.

## Tests first (TDD, rule 1)
RED first: write tests/test_sc1.py before the implementation. Run ONLY tests/test_sc1.py, tests/test_eval_data_separation.py,
tests/test_sealed_guard.py, tests/test_no_side_effect_imports.py. DO NOT run the full suite.

## GPU policy
No GPU: the GPU is running the registered BFCL preflight. Never launch a model process; CPU fixtures only. Never wait
on a lock; never signal any process. Never read the sealed IFEval input file. Never modify data/bench/*.

## Acceptance
CPU tests green; ruff clean; `uv run python scripts/sc1.py validate data/sc1/smoke` passes on your smoke bank
(CPU, no trunk); commit EARLY and often with explicit pathspecs.

## Ledger handoff
Append to WORKLOG.md: "## <date> — sc1-harness handoff": files, manifest hash, test command + result, the smoke
validate output summary, open ambiguities. Do not edit LEDGER-PLAN.md.
