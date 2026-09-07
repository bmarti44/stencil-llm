# POST-REBOOT NOTE (2026-09-05, power outage at ~18:27; machine up since 18:27)
The previous codex sessions died mid-task; the scratchpad was wiped. Artifacts committed in git are the only state.
GPU: a llama-server owned by Brian (pid 2705, Qwen3.8-27B Q4, ~16 GB) now runs permanently on the GPU. It is NOT a
Stencil job: treat the GPU as available for Stencil when no OTHER compute process (a .venv python) is present; never
touch pid 2705. Memory budget: 128 GB total minus the llama-server; Qwen3-30B-A3B bf16 (~61 GB) still fits. Coordinate
with other Stencil GPU checks via results/quick-checks/<check>/RUNNING.flag files (write yours while running, delete
after; wait if another Stencil flag exists). Never signal any process. All committed prior results stand; re-read the
relevant README/records rather than redoing completed work. Commit with explicit pathspecs; no push.
# Quick check 40h for gpt-6-astra: release CLOSURE — masks at EVERY change + mask+OFF control (~15 GPU-min) — 2026-09-06

Source: results/check40f-review-fable.md items 6-9. Reuse scripts/focus_check40f.py (frozen JS/Python directions,
alpha 3, masking = position-preserving eviction of every assistant code-turn body, 64-token caps, 24 episodes, seed
40070). Arms: (M) bias change + mask at SWITCH, BACK AND CLEAR (mask all bodies produced under the previous skill at
each change); (Z) mask + bias OFF at SWITCH (isolates the routing term: does masking alone restore the default?); (T')
text cue + mask INCLUDING the cue turn at CLEAR (cue-turn masking), as the bar. Drop R4 placeholders. Steps: SET(JS)
-> HOLD -> SWITCH(Python) -> HOLD_AFTER_SWITCH -> BACK(JS) -> HOLD_AFTER_BACK -> CLEAR(bias OFF; Python default).
READING (fixed before running): CLOSED-RELEASE if M gives Python >= 20/24 at SWITCH, JS >= 20/24 at BACK (the
non-default direction with a mask — the decisive new cell), and Python >= 20/24 at CLEAR after real reestablished JS,
with breakage <= 2/24 at every step; report Z separately (if Z >= 20/24 Python at SWITCH, masking alone restores the
DEFAULT and the routing term is only needed for the non-default direction — state that). PARTIAL / NOT otherwise.
Report fence loss after masking (fable item 4) and R3-style ambiguous echoes explicitly. Cap 0.5 GPU-h. GPU: the
FOCUS-3 gate may hold it (results/quick-checks/focus3-gate/RUNNING.flag) — wait; write your own flag; never signal.
Outputs under results/quick-checks/check40h/ (README with pre-written reading, summary.json, records); item 40h in
results/quick-checks/README.md (5 lines); WORKLOG entry (<= 6 lines). Commit with explicit pathspecs (git add -f for
results); no push. Foreground only; never terminate or signal any process; never read the sealed IFEval input file
or the sealed BFCL cohort contents; nothing fit or trained.
