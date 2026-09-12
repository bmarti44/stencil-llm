# Exp 4C result audit (Astra, read-only, maximum reasoning effort)

You are the registered result auditor for Exp 4C (`results/memorycode-long/REGISTRATION-4C.md`),
the single final confirmation of the Qwen3-4B `stencil_focus` package that your own binding
decision (`results/reviews/2026-09-12-unblock-decision-open-astra.md`) authorized. Your
implementation review (`results/reviews/2026-09-12-exp4c-impl-review-astra.md`, closure record
at its end) blocked ten findings that were then closed in commit `1ca02a31`. The evaluation has
now run to its terminal state and been summarized ONCE.

Do not read anything under `data/bench/`. Do not write files, run models or use the GPU. Do
not propose any new arm, workload, sample size, gate or test: the registration forbids every
revision on every outcome. Your job is to decide whether the terminal reading printed in
`summary-4c.json` is the reading the registration mechanically prescribes for the evidence on
disk, and whether that evidence is valid.

## Files

- Registration: `results/memorycode-long/REGISTRATION-4C.md`; ledger entries from 14:05Z on in
  `plan/LEDGER.md`.
- Frozen manifest: `results/memorycode-long/items-4c.json` (N, t_max, ids sha, qualification
  digest); candidates `items-4c-candidates.json`; original `items.json`.
- Qualification: `results/memorycode-long/qualification-4c.json` and the 44 receipts + process
  heartbeat receipts under `results/memorycode-long/qualification-4c/`.
- Evaluation records: `results/memorycode-long/screen_long_4c-4b-package-role_evicted/`
  (`item-*.json`, `raw/*.json`, `attempts.jsonl`, `process-*.json`, `summary-4c.json`,
  possibly `BUDGET_EXHAUSTED.json`).
- Code: `scripts/memorycode_package_run.py`, `scripts/memorycode_4c_qualify.py`,
  `scripts/memorycode_4c_items.py`, `scripts/memorycode_4c_summarize.py`,
  `scripts/memorycode_screen.py` (shared statistics), `src/stencil/memorycode.py` (scoring),
  `vendor/memorycode/code/evaluate_model_output.py` (official checker),
  `tests/test_memorycode_4c.py`; the package `deploy/stencil_focus/build/hub-4b/*.py`.
- Release path (not yet executed): `scripts/memorycode_4c_verify.py`,
  `scripts/memorycode_4c_verify_clean.py`, `scripts/memorycode_4c_release.py`.

## Audit tasks

1. Recompute independently from the per-item records: N valid pairs, the primary
   (mean D, s_D, paired t or the Hoeffding fallback, the 95% interval, two-sided p), the
   bootstrap and sign-test companions, strict counts with McNemar and the conservative paired
   interval, the output-failure guard (both discordance directions, category counts, mean H,
   [L_H, U_H] by paired t or the Clopper-Pearson union bound, McNemar p), and the descriptive
   subsets. State every number you recompute next to the summary's number.
2. Verify the freeze chain and identities: registered hashes, qualification digest, timing-
   derived N, exact candidate prefix, per-arm fingerprints equal to the qualification manifest,
   effective EOS, prompt-length equality and the 4,096 allocation, item identity.
3. Verify completeness and budget from the receipts, not from the summary: every frozen pair
   terminal and valid, no extra/duplicate/malformed records, generation spending (attempt log,
   interrupted attempts bounded) ≤ 3 t_max N, evaluation resident overhead ≤ 2,700 s,
   qualification resident ≤ 3,600 s, no unbounded accounting.
4. Re-score a sample of at least 20 records from their stored text with the frozen checker
   logic (read the code; do not execute models) and check the raw→scored EOS transformation,
   timeout zero-credit and failure flags.
5. Apply the readings table mechanically and state which row the evidence falls in.
6. Check the disclosures the registration requires are present or derivable (prompt accounting,
   missingness, cost, prior disclosures) and that nothing outcome-dependent entered the
   procedure (order alternation by candidate index, no regenerated terminal outputs, no
   interim efficacy summaries: `progress-4c.json` vs `summary-4c.json` timestamps).

## Output

Write, as your entire answer, a Markdown report that begins with one line
`VERDICT: ACCEPT` or `VERDICT: REJECT`, followed by `READING: <the row you determined>`, then
numbered findings graded low/medium/high/critical with file:line references and the recomputed
numbers. ACCEPT means: the summary's reading is the mechanically prescribed one, the evidence
is valid and complete, and nothing outcome-dependent entered. REJECT names the defect that
changes the reading or invalidates the evidence. If the reading is STATISTICAL GATES PASSED and
you ACCEPT, state explicitly that the release path may proceed to the clean-environment
verification and HF push under the registered card wording; if any other reading, state that
no HF release is authorized and the program ends with a repo-only report.
