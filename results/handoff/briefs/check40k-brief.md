# Check 40k for gpt-6-astra: does router bias ON TOP OF the rendered rule make the model BETTER at the task? (2026-09-06)

Brian's question (verbatim intent): "for steering the model's internal skill — check whether doing this in conjunction
with simply writing the rule makes the model better at accomplishing the task; if it does then this needs to be
something we ship by default." Check 40j could not answer this: every arm sat at the 16/16 ceiling on trivial
arithmetic, so it measured language choice, not task competence. Build a check where text-only is NOT at ceiling.

Design (pre-written readings in README before any GPU work; recipe commit before inference):
- Model/actuator: Qwen3-30B-A3B HF; identical router hook; identical alpha-3 JS tensor (hash as 40j); all 48 layers,
  prefill+decode; greedy; token cap per reply generous enough for the tasks (e.g., 512); "broken" as in 40i.
- TASKS: author 40 FRESH small JavaScript programming tasks yourself (string/array/object processing, small parsers,
  date/number formatting, simple algorithms; each with a function name, a one-paragraph natural request in the hard
  40e-like form "Write a function named X that ...", and 4-8 HIDDEN executable node tests). No public benchmark items
  (never HumanEval/MBPP/LeetCode-style copies; invent everything). Data lineage: fit-on = nothing; calibrate-on = 8
  DEV tasks used only to set difficulty (target: text-only passes 40-75% of DEV tasks; adjust task difficulty on DEV
  only, then freeze); evaluated-on = the remaining 32 tasks, opened once.
- ARMS on the 32 tasks (paired by task): text-only (rendered live rule "Live rules: (1) Write all code in JavaScript."
  as in 40j) | text+bias (same + alpha-3 JS bias) | text+shuffled-bias (same + a fixed within-layer expert
  permutation of the tensor; the specificity control) | OFF (no rule, no bias; diagnostic — shows the model's default
  language and competence). 128 generations.
- SCORING: per task, all hidden tests pass (executable in node) = success; also record language, syntax validity,
  broken, token count. Primary endpoint: paired success text+bias vs text-only (exact McNemar / sign test on
  discordant pairs; report wins/losses/ties and a paired-difference CI). Secondary: text+shuffled vs text-only (if
  shuffled also gains, the gain is not skill-specific).
- PRE-WRITTEN READINGS:
  R1 "ship by default": text+bias beats text-only with wins - losses >= 5 of 32 AND losses <= 2 AND the exact one-sided
     sign test on discordant pairs gives p <= 0.05 (e.g. 6-0 p=.016, 7-1 p=.031, 9-2 p=.033 qualify; 6-1 p=.063, 7-2 p=.090, 8-2 p=.055 do not; compute it exactly) AND text+shuffled does
     NOT show the same gain (its wins - losses <= 2) AND breakage not higher than text-only -> the actuator earns
     default-on for the certified family; register that consequence.
  R2 "no benefit": wins - losses <= 1 (either direction) -> actuator stays behind the flag (40j decision stands).
  R3 "harm": losses - wins >= 3 -> actuator stays off; record the harm.
  R4 anything else -> INCONCLUSIVE at n=32; record; no enlargement in this run.
Cap 45 GPU-minutes; one model load. Outputs under results/quick-checks/check40k/ (README with readings, tasks.json
with hidden tests, records.jsonl with token ids/bias hash per generation, summary.json, freeze.json); item 40k in
results/quick-checks/README.md (5 lines); WORKLOG entry (<= 6 lines). Commit scripts/focus_check40k.py + results (git
add -f) + README/WORKLOG with explicit pathspecs; no push.
