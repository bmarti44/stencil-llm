# Quick check 40d for gpt-6-astra: SET / HOLD / SWITCH / BACK / CLEAR with the router bias on Qwen3-30B-A3B (2026-09-05)

Source: results/quick-checks/check40c/README.md (POSSIBLE; dose-response: alpha 3 sustained = 32/32 valid JavaScript,
0 broken, 32/32 task pass; alpha 2 = 25/32, 0 broken; alpha 4 breaks 6/32), results/quick-checks/check40b/README.md and
results/check40b-review-fable.md. Orchestrator ruling: the screen uses alpha 3 sustained (the dose-response's clean
maximum; disclose that alpha 2 was the script's first-eligible pick and run alpha 2 as a secondary arm). Same model /
router hook / frozen JS-Python profiles and direction as 40b/40c (reuse scripts/focus_check40b.py / focus_check40c.py;
pin the .venv transformers 5.16.1 import and assert router slot 0 = raw logits). 64-token caps.
DESIGN (write the reading into the README BEFORE running): 32 retained-history episodes, each step a fresh uncued
programming task, complete user+assistant pairs, a neutral non-code pair as the delay: SET (bias JS on; task 1) ->
HOLD (bias kept; neutral pair; task 2) -> SWITCH (bias flipped to the Python direction; task 3) -> BACK (bias JS; task 4)
-> CLEAR (bias OFF; task 5; imposition = JavaScript where the OFF default is Python). Arms: correct (as described),
shuffled (random matched-norm bias at every step), OFF (no bias anywhere), text-cue bar ("Use JavaScript." / "Use
Python." written into the corresponding requests, no bias), alpha-2 secondary (correct schedule at alpha 2). Score per
step: valid language by both parsers, coarse task check, breakage, first/fence token.
READING (fixed): CONTROLLABLE if correct reaches JS >= 26/32 at SET, JS >= 26/32 at HOLD (bias sustained, no cue),
Python >= 26/32 at SWITCH, JS >= 26/32 at BACK, Python >= 26/32 at CLEAR (no imposition), breakage <= 2/32 at every
step, shuffled JS <= 4/32 everywhere; PARTIAL if SET/HOLD/BACK pass but SWITCH or CLEAR fail (say which: the
"release" question); else NOT CONTROLLABLE. Report per-step tables, per-family breakage, arrow counts.
Cost: project from ~15 tok/s (32 episodes x 5 arms x ~6 generations x 64 tokens + neutral pairs + load); cap 2 GPU-h;
if the projection exceeds it, use 24 episodes and record before running. Unregistered, disclosed; outputs under
results/quick-checks/check40d/ (README with pre-written reading, summary.json, records); item 40d in
results/quick-checks/README.md (5 lines); WORKLOG entry (<= 6 lines). Commit scripts + results (git add -f) +
README/WORKLOG with explicit pathspecs; no push. Foreground only; never terminate or signal any process; never read
the sealed IFEval input file or the sealed BFCL cohort contents; nothing fit or trained.
