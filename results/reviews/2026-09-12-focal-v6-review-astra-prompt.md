# Independent review request: focal-delivery pilot v6 (bugs, validity, direction)

You are an independent reviewer. Do not assume the pilot is right or wrong; form
your own reading from the artifacts. Do NOT read anything under `data/bench/`.

## What exists

- Direction proposal under test: `results/reviews/2026-09-12-direction-proposal-rev2.md`
  (direction D, "focal delivery": session conventions delivered inside one generation
  at the syntactic unit they govern), your prior adversarial review of it
  (`results/reviews/2026-09-12-direction-adversarial-rev2-astra.md`) and your prior
  root-cause report on the earlier pilots
  (`results/reviews/2026-09-12-focal-rootcause-astra.md`).
- Runtime: `src/stencil/focal.py` (rule typing, incremental unit detector, lexer,
  span stripping, echo counting) and `src/stencil/focal_runtime.py` (greedy loop with
  rollback, cue insertion, re-feed, user-turn channel, periodic control, HF backend).
  Tests: `tests/test_focal.py`, `tests/test_focal_runtime.py`.
- Pilot script: `scripts/focal_quicklook.py`; gate summariser:
  `scripts/focal_quicklook_summary.py`.
- Pilot records (exposed SETUP-LONG pilot split, oracle rules, not results):
  `results/focal/quicklook-v3.json`, `quicklook-v4.json` (earlier runtime versions),
  `quicklook-v5.json` and `quicklook-v6.json` (current runtime; v6 differs from v5 only
  by the commit "indent-only re-feed uses the model's own tokenization"). Logs sit
  next to each JSON. Each arm record holds the full text, generated ids, inserted
  spans, events, token accounting, parse/cap/loop status, echo count and scores.
- Ledger entries for today in `plan/LEDGER.md` (search "2026-09-12") record what was
  changed and why, in order.
- Git history: `git log --oneline -15` and the diffs of the last six commits.

## Questions (answer each on its own; cite files, line numbers, item ids, arm names)

1. Bugs. Read the runtime and the v6 records against each other. List every defect
   you can find in detection, rollback, cue insertion, re-feed, the user-turn
   channel, the periodic control, span stripping, echo counting, the scorer path
   (`score` in the pilot script and the vendored checker), the frozen-history
   construction, the token accounting, and the gate summariser. For each: severity,
   which arms and items it affects, and whether it changes the v6 reading.
2. Validity. Is the v6 comparison a fair test of placement (focal vs a reminder
   before the request)? Consider prompt/token matching, what the reminder arm sees
   versus the focal arms, the oracle rule source, the scorer, the items chosen, the
   generation cap, and anything else that would make a difference between arms
   attributable to something other than where the rules are delivered.
3. Reading. State what the v6 numbers do and do not show. Apply the pilot gate as
   written in the summariser docstring and say whether you agree that gate is the
   right decision rule for continuing.
4. Direction. Given everything above and your two earlier reviews, is direction D
   still worth a registered screen, should it be modified, or should it be dropped?
   Give the decisive reason either way, and, if a screen, list the minimum changes
   to the runtime, the arms and the registration that you would require first.
5. Anything else you notice that the author of these files appears not to have
   noticed.

Write plainly. Do not soften findings. Do not propose new models, benchmarks or
review stages.
