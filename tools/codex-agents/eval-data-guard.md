# Brief: eval-data-guard — mechanically forbid fitting/selecting on any evaluation benchmark

## Objective
Brian's rule (2026-09-02): never fit, train, select, or tune any finder/selector/policy on data from an evaluation
benchmark — all of data/bench (IFEval sealed file, multiif_en.jsonl, bfcl_v3_mt/*, S2 sets), not even case-disjoint
slices or the model's recorded responses to their prompts. Today the salience2 finder was found trained on Multi-IF
prompts (src/stencil/salience2.py load_multiif23_docs + load_conv_prose reading results/qwen/b4-multiif-base) and
src/stencil/salience.py (v1) does the same. Make this impossible to repeat silently:
1. tests/test_eval_data_separation.py: an AST/string scan of src/stencil/*.py and scripts/*.py that FAILS if any
   module whose name or functions indicate fitting (`fit`, `train`, `refit`, `select_policy`, `training_docs`,
   `load_*_docs`, `oracle`) references a path under data/bench/ or results/qwen/b4-multiif-base, unless the file is
   in an explicit EVAL_ONLY allowlist of evaluation runners (scripts/ledger_eval.py, scripts/bfcl_mt.py,
   scripts/ledger_kv_probe.py, scripts/t*_*.py that only evaluate) — the allowlist is a literal in the test, like
   tests/test_sealed_guard.py ALLOWED. The test must go RED on the current salience2.py/salience.py before your fix.
2. Fix salience2.py and salience.py: remove Multi-IF prompts and b4-multiif-base prose from the training corpora
   (`training_docs` real = an empty list or a disjoint public prose source already in the repo — data/b3 prose is
   fine); keep the loaders only if renamed `eval_*` and unused by any fit. Refit the shipped linguistic weights
   (`python -m stencil.salience2`, CPU, seconds) and record the new sha256 in WORKLOG; the old weights file is
   overwritten (its sha is in git history). Do NOT run the probe/hybrid GPU refits.
3. tools/hooks/pretool_guard.py: extend the sealed rule so that a Bash command that (a) mentions any data/bench path
   or results/qwen/b4-multiif-base AND (b) contains a fit-indicating token (`fit`, `train`, `refit`, `-m stencil.salience`)
   is denied with "eval data used for fitting". Keep the existing sealed-name rule untouched. Add cases to
   tests/test_pretool_guard.py (allow: evaluation runners, `git`, `ls`, `sha256sum`; deny: a fit script fed a bench path).
4. Add to AGENTS.md (one entry, imperative): the rule, the two incidents, and "write the data-lineage line
   (fit-on vs evaluated-on, disjoint) before any registration or brief".

## Allowlist
See eval-data-guard.allow.

## Tests first (TDD, rule 1)
RED first for (1) and (3). Run ONLY: `set -o pipefail; uv run pytest -q tests/test_eval_data_separation.py tests/test_pretool_guard.py tests/test_salience2.py tests/test_sealed_guard.py`. DO NOT run the full suite.

## GPU policy
No GPU needed. Never launch model processes. `.review.lock` is held by your own wrapper: never wait on it; commit
your allowlisted files when done.

## Acceptance
Targeted tests green; ruff clean; the scan test provably RED before the fix (paste the failing output in WORKLOG);
new weights sha recorded; commit before finishing.

## Ledger handoff
Append to WORKLOG.md: files scanned, the allowlist, RED->GREEN evidence, new salience2 weights sha256 and the
top-12 features before/after, anything in the repo that still reads eval data for a non-eval purpose.
