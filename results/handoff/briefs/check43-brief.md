# Quick check 43 for gpt-6-astra: CONCEPT-level routing bias — SUM vs PRODUCT with language fixed (2026-09-05)

Source: results/neuron-granularity-research-astra.md section 4 (your own design; implement it EXACTLY as written there,
items 1-11, including seeds 95061-95064, the last-four-neutral-token profile statistic averaged by example, the
layer 7-34 band, alpha grid {1,2,3} with paired >= 6/8 setup selection, seven conditions per prompt, the bounded
AST interpreter checker validated on hand-written functions before use, the collateral 16-task set, the PASS rule
(>= 24/32 paired, >= 12/16 per language, >= 5/8 per seed x language, <= 1 new malformed per sign, >= 8 more than each
control + one-sided exact paired McNemar, Holm .05), the 1.5 GPU-h refusal, and the INVALID/INCOMPLETE/INELIGIBLE/FAIL
readings). Brian's framing: focus at a level finer than language — an operation the model must select regardless of
language. Language and explicit-loop requirement fixed in text; only SUM/PRODUCT omitted in non-text arms; the
Python-derived direction transfers unchanged to JavaScript. Reuse the verified 40b router consumer and parsers.
Write the reading + all frozen artifacts BEFORE final generation; commit them first. RUNNING.flag protocol; never
signal. Unregistered, disclosed; outputs under results/quick-checks/check43/; item 43 in results/quick-checks/README.md
(5 lines); WORKLOG entry (<= 6 lines). Commit scripts/focus_check43.py + results (git add -f) + README/WORKLOG with
explicit pathspecs; no push. Foreground only; never terminate or signal any process; never read the sealed IFEval
input file or the sealed BFCL cohort contents; nothing fit or trained.
