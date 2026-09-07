# Text-only task for gpt-6-astra: apply the wording fixes from results/astra-results-review.md (F1-F8) — 2026-09-05

Repo /home/bmarti44/stencil-llm. CPU only; another codex task (classifier retrain) is running and edits only
data/classifier/model/relations/* and results/relations-classifier-report.md — do not touch those or WORKLOG.md.
Apply every fix in results/astra-results-review.md sections F1-F8 (and the F7 literal corrections) as follows:
- For quick-check READMEs (results/quick-checks/check36/README.md "precedence dominates", check40c prewritten
  reading's "sustained bias causes breakage" implication, check40b/40c/40d/41b wording flagged) and
  results/quick-checks/README.md items: append a dated "Correction (astra full review, 2026-09-05)" paragraph with
  the exact replacement wording; do NOT rewrite the original sentences (they are the record).
- For reviewer files (results/check3*-review-fable.md, results/check40b-review-fable.md, results/check43-review-fable.md,
  results/focus2c-safety-diagnosis-fable.md): append a "Correction" line only (reviewers' prior text is never deleted).
- results/focus-synthesis-astra.md: prepend a dated banner "HISTORICAL (pre-FOCUS-2d) — not the current program
  verdict; see results/astra-results-review.md" (F8).
- README.md (repo root): if it states any of the flagged slogans, replace with astra's exact replacement sentence:
  "An externally maintained routing bias selects a narrow output mode using frozen co-trained experts. Whether it
  selects language-independent computation or supplies reversible task control remains unproved." and narrow any
  "semantically correct" claim to "expression preserved; executable validity as parsed".
- LEDGER-PLAN.md: append "## PROGRAM-REVIEW CLARIFICATIONS 2 (2026-09-05, astra full results review)" listing each
  F-id with its disposition and the replacement text; no registered text changed.
Commit with explicit pathspecs; no push. Never launch any GPU/model process; never terminate or signal any process;
never read the sealed IFEval input file or anything under data/bench.
