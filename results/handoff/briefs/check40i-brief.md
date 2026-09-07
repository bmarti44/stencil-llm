# Quick check 40i for gpt-6-astra: release CLOSURE with the Z schedule as PRIMARY, fresh seed (~10-15 GPU-min) — 2026-09-06

Source: results/check40h-review-fable.md items 8-10 (Z = return to default by mask + bias OFF; enter non-default by bias
+ mask; opposite-direction bias unnecessary). Reuse scripts/focus_check40h.py (frozen JS direction alpha 3, masking =
position-preserving eviction of assistant code-turn bodies at each change, 64-token caps), NEW seed 40080, 24 fresh
episodes. Arms: (Z) PRIMARY: SET(JS bias) -> HOLD -> SWITCH(bias OFF + mask) -> HOLD_AFTER_SWITCH -> BACK(JS bias + mask)
-> HOLD_AFTER_BACK -> CLEAR(bias OFF + mask); (Zc) control at BACK: bias OFF + mask (must NOT re-enter JS: JS <= 4/24);
(S) shuffled-direction bias + mask at BACK (control); (OFF) no bias, no mask. READING (fixed before running):
CLOSED-RELEASE if Z gives Python >= 20/24 at SWITCH, JS >= 20/24 at BACK, Python >= 20/24 at CLEAR (paired real
releases), breakage <= 2/24 at every step, Zc JS <= 4/24 and S JS <= 4/24 at BACK; PARTIAL/NOT otherwise. Report fence
counts, the missing-paren defect count, and cost. Cap 0.5 GPU-h. GPU: verify idle (no compute process; no other
RUNNING.flag); write your flag; never signal. Unregistered, disclosed; outputs under results/quick-checks/check40i/
(README with pre-written reading, summary.json, records); item 40i in results/quick-checks/README.md (5 lines);
WORKLOG entry (<= 6 lines). Commit with explicit pathspecs (git add -f for results); no push. Foreground only; never
terminate or signal any process; never read the sealed IFEval input file or the sealed BFCL cohort contents; nothing
fit or trained.
