# Quick check 40g for gpt-6-astra: generality rerun with a positive control (fable's follow-up, ~20-30 GPU-min) — 2026-09-05

Source: results/check40e-review-fable.md items 5-10. Do exactly its cheapest follow-up, one model load:
 (1) POSITIVE CONTROL: the frozen 40b/40c JavaScript direction at alpha 3 on 8 uncued tasks IN THE 40e HARNESS (must
     reproduce >= 6/8 JS; else the harness differs from 40c — stop and report INVALID);
 (2) TypeScript: alpha 4.5 and 6 with the 40e TS direction, plus a TS direction extracted at the FENCE-LABEL position
     (generated tokens 1-3) scaled to band norm 15.7, on 16 uncued tasks; arms correct/shuffled/OFF/text-cue; record
     dispatch counts per record (route-change fractions per layer);
 (3) P2 rerun with the one-line prompt fix "SQL table name: items (columns id INTEGER, value INTEGER). Rows:" —
     competence 16/16 both sides (>= 14/16), then the 32-task SET screen JSON -> SQL with correct/swapped/shuffled/
     OFF/text-cue; use strict-between thresholds so the JSON default does not break on boundaries; breakage gate PAIRED
     vs OFF (correct-only breaks <= 2/32), not absolute;
 (4) Go: install the Go toolchain WITHOUT root under $HOME (official tarball; verify gofmt/go vet work on CPU); if it
     installs, run Python -> Go competence (16/16) and, if competent, the 32-task SET screen with a Go direction at
     norm-matched alpha 3 (same arms).
READINGS (fixed before running): per pair GENERALIZES if correct >= 20/32 addressed-skill success with paired breakage
<= 2/32 and shuffled <= 4/32; MARGINAL >= 12/32; else NOT; INVALID if the positive control fails. State plainly, per
pair, and overall whether the router lever generalizes beyond Python/JavaScript. Cap 1 GPU-h. RUNNING.flag protocol;
never signal. Unregistered, disclosed; outputs under results/quick-checks/check40g/; item 40g in
results/quick-checks/README.md (5 lines); WORKLOG entry (<= 6 lines). Commit with explicit pathspecs (git add -f for
results); no push. Foreground only; never terminate or signal any process; never read the sealed IFEval input file
or the sealed BFCL cohort contents; nothing fit or trained.

ADDITIONS (2026-09-06, Brian: "we're a go on 40g"; fable's check-40i review item 10): run the Go pair with a FRESH
40b-style competence/profile step as the positive control (Python 16/16 and Go >= 14/16 cued), alpha 3 norm-matched to
the JS band; SET screen on 32 uncued tasks; if SET Go >= 20/32 with <= 2 broken, ALSO run the Z release schedule on
24 retained-history episodes (bias OFF + mask to return; bias + mask to re-enter) with the Zc control, using the same
decision function as check 40i. Go install without root under $HOME (official tarball); verify gofmt/go vet on CPU.
GPU: check 44b may hold it (results/quick-checks/check44b/RUNNING.flag) — wait; write your own flag.
