# Check 40j for gpt-6-astra: does the router lever add anything once the rule is RENDERED? (2026-09-06)

Context: check 40g (results/quick-checks/check40g/README.md) was INVALID at its positive control — the frozen alpha-3
JavaScript bias tensor scored JS 3/8 in the check-40e prompt harness ("Write a zero-argument function named X that
returns EXPR"), whereas the same tensor reached 32/32 in the 40c/40 harness ("For the arithmetic expression EXPR,
provide a solution. If writing a function, name it X"). Reading so far: the actuator flips a weak default prior, not a
strong one. Your composition design (results/focus-mechanism-composition-astra.md) names the decisive open question:
does routing plus masking improve executable work when the same live obligations are already rendered correctly?
Answer that question in the HARD harness now, quickly, as a quick check under Brian's quick-test-first rule.

Design (write the pre-written readings into README before any GPU work; register the recipe commit before inference):
- Model/actuator: Qwen3-30B-A3B HF, the identical router hook, the identical alpha-3 JS tensor (bias sha as in 40g's
  control), all 48 layers, prefill+decode. Mask = the 40i persistent key mask (whole assistant code bodies, positions
  preserved). Greedy decoding. Executable JS/Python scorer as in 40g (node + python), "broken" as in 40i.
- Tasks: 16 FRESH zero-argument arithmetic function tasks in the 40e prompt template (new expressions, new seed; never
  the committed 40e/40g screen items; no benchmark data). Data lineage: fit-on = nothing (no fitting anywhere);
  evaluated-on = these 16 fresh tasks only.
- Rendered rule text = exactly what the FOCUS-3 renderer would put in the current request for one live rule:
  "Live rules: (1) Write all code in JavaScript." placed in the current user turn as the renderer does (cite the
  renderer function you copy the format from; do not invent a stronger cue).
- PHASE 1, single-shot 2x2 on the 16 tasks: OFF | text-only | bias-only | text+bias. (64 generations.)
- PHASE 2, imitation pressure: build a per-task 6-turn history of Python answers produced OFF in this same harness
  (generated in-run, cache-retained, same 40e template with 6 further fresh expressions), then the 7th request carries
  the rendered rule. Arms on the 16 tasks: text-only | text+mask | text+bias | text+bias+mask. (64 generations + the
  96 history generations, shared across arms by cache prefix.)
- Report per arm: JS executable-correct count /16, Python count, broken count, fence label, first token; paired
  per-task tables; exact paired sign counts for text+bias+mask vs text-only in Phase 2 (descriptive confidence
  intervals; n=16 is a screen, say so).
- PRE-WRITTEN READINGS (all three must be written before running):
  R1 "rendering suffices": text-only >= 14/16 in BOTH phases -> the lever adds nothing measurable at this pressure;
     design consequence: actuator not in default shipping (your own reading), rendering-only becomes the primary arm.
  R2 "lever earns its place": Phase-2 text-only <= 10/16 AND text+bias+mask >= text-only + 4 with breakage <= 1/16
     -> keep the actuator in the composed arm; the larger test's C-vs-R contrast is justified.
  R3 anything else -> INCONCLUSIVE at n=16; record and stop (no enlargement in this run).
  Also report, diagnostically only: whether bias-only in Phase 1 reproduces 40g's ~3/8 rate (control sanity), and
  whether text+bias in Phase 1 beats text-only (single-shot additivity).
Cap 45 GPU-minutes total; one model load. Outputs under results/quick-checks/check40j/ (README with the readings,
records.jsonl with full token ids/cache prefix hashes/bias hash/mask trace per generation, summary.json, freeze.json
with the recipe commit and tensor hashes); item 40j in results/quick-checks/README.md (5 lines); WORKLOG entry (<= 6
lines). Commit scripts/focus_check40j.py + results (git add -f) + README/WORKLOG with explicit pathspecs; no push.
