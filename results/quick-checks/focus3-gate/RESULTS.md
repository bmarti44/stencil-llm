# FOCUS-3 gate — INELIGIBLE at setup

The frozen setup scored **8/16 final-task successes**, below the required 15/16.
The stop rule was applied: **zero gate episodes ran**. C/O/N/T gate comparisons,
register-agreement thresholds, and a FOCUS-3 PASS remain untested.

| Setup family | Episodes | Final success | Any post-change stale execution | Breakage |
|---|---:|---:|---:|---:|
| Override | 4 | 4 | 0 | 0 |
| Cancel | 4 | 0 | 4 | 0 |
| Complete-and-move-on | 4 | 0 | 4 | 0 |
| Switch-and-return | 4 | 4 | 0 | 0 |
| Total | 16 | 8 | 8 | 0 |

These are setup **oracle-rendered** generations. The classifier also processed
setup user messages for timing and saved its decisions, but those decisions did
not determine the setup renderer. The result therefore does not estimate the
classifier-driven arm's answer quality or its 64-episode register agreement.
There were 55/80 successful task replies, 80/80 correct tags, and no broken
replies among all 96 generations. Four cancellation-family hard-none requests
followed the quoted opposite ordering despite the correct oracle recap; all
four final cancellation requests failed too. Outputs and unsuccessful histories
were retained without replacements or exclusions.

After gold cancellation or completion, the renderer contains the persistent tag
and no ordering row. The unchanged-payload default remains in the system message;
it was not added as a synthetic user rule. This setup result measures that exact
cue/history combination. It does not establish general task incompetence or
classifier failure. No prompts or rendering behavior were changed after outputs.

Switch-back is reported separately: **4/4 setup final successes**. Its return
flags and previously generated column counts are in the per-turn records.
All masking/un-release-of-mask counts are zero: the implementation renders rules
and records provenance, with no masking anywhere in the ship path. This is not
evidence about lifting an attention mask.

The measured 64-episode projection was **3,320.88 s / 10,800 s**, including setup
and a 25% reserve; the 48-episode fallback was unnecessary. Competence caused the
stop. Total charged GPU-held time was **181.012 s (3.017 min)**, including the
2.570 s failed initialization. The successful run generated 2,216 tokens
including EOS. CPU classifier work during setup totaled 14.695 s; per-message
median 0.133 s and observed p95 0.250 s on this small workload.

The first freeze is commit `aa6c0e41`. A checkpoint-wrapper loading error stopped
the first launch before any classifier or trunk inference. Its freeze, log,
start and summary remain in [initialization-failure/](initialization-failure/).
The corrected loader and real-checkpoint CPU test were committed in `92ccb104`
before inference; reading, author fixture and bank stayed byte-identical.
The [pre-written reading](README.md) remains immutable. The failed launch cost
was carried forward; there was no output-based retry or threshold change.

Validation: **15 targeted tests passed; Ruff clean**. Two requested sealed-guard
hash tests were deliberately deselected because they read the sealed IFEval
bytes, forbidden by the task. The other sealed-guard checks ran. Both audits
passed on **96 raw records / 16 complete setup episodes**: token decoding,
full own-answer prompt histories, provenance positions, gold state/checkers and
independent JSON ordering/tag scores. Gate-only audit checks are explicitly
unexercised, not passed vacuously. See [audit.json](audit.json),
[independent-audit.json](independent-audit.json), and the reproducible
[audit_records.py](audit_records.py).

Artifacts: [summary.json](summary.json) includes setup endpoint counts;
[run-summary.json](run-summary.json) preserves the runner's original summary;
[selection.json](selection.json) records the pre-gate resource decision;
[setup/records/](setup/records/) contains all 96 full per-turn records;
[setup/traces/](setup/traces/) contains 16 episode register traces.
The 64 seed-30301 gate episodes remain frozen and unevaluated.

Nothing was fit or trained. The seed-0 relation model and frozen thresholds are
unchanged. New-rule admission retains the disclosed development influence in
`data/classifier/LABELS.md`; no development-independent package claim is made.
The independent episode author saw no relation examples or benchmark inputs.
The foreground process exited naturally and removed its own RUNNING.flag.
No process was signalled, no sealed input was read, and nothing was pushed.
