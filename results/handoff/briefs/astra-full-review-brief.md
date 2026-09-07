# Full-program review for gpt-6-astra (CPU only, read-only): audit ALL of the work (2026-09-07)

Brian's instruction: review all of the work. You are the AUDITOR here, not the builder — you wrote much of this
yourself, so review it adversarially and say where your own work was wrong. Do NOT touch the GPU: the registered
64-episode larger test is running (results/larger-test/RUNNING.flag). Never signal any process, never start a
container, never read anything under data/bench, and do not read the evaluation-bank episode CONTENT (manifests and
hashes only) — the larger test is mid-flight and must not be contaminated.

Scope — everything from check 31 to now:
- results/quick-checks/README.md items 31-51 and each check's README (esp. 40b-40l, 41-43b, 44-44c, 46, 47, 49, 51).
- The composition line: results/focus-mechanism-composition-astra.md, -v2-astra.md (+ addenda),
  results/quick-checks/composition-pilot-{1..7}/README.md, pilot5-screen, vllm-qual, check47-replay.
- Every review and the orchestrator addenda appended after them: results/*-review-fable.md,
  results/*-review-opus.md, results/slab2-review*.md, results/composition-pilot-*-review-*.md.
- The classifier line: results/relations-classifier-report.md, data/classifier/LABELS*.md, the audits under
  data/classifier/review/, the held-out sets 1-4 (metadata/summary lines only).
- The shipped code: src/stencil/focus/** (register, renderer, loop, journal, slab2), models/stencil-package/,
  scripts/composition_pilot5.py; AGENTS.md; results/HANDOFF-astra.md; results/astra-assessment-adoption.md.

Produce results/full-program-review-astra.md answering, with file:line evidence and no hedging:
1. CLAIM LEDGER: every claim the repo currently makes, marked SUPPORTED / OVERSTATED / UNSUPPORTED / CONTRADICTED,
   with the exact number and its source. Flag any claim that survives only because a review corrected it but the
   original file still reads wrong.
2. WHAT WOULD NOT REPLICATE: name the results most likely to fail an independent re-run and why (start from the
   ~94% cross-restart cell reproducibility the pilot-7 review measured, and say which committed conclusions sit
   inside that noise band).
3. YOUR OWN ERRORS: the specific things you got wrong across the program (harness defects that killed four pilots;
   the invalid per-round gate; the cross-workload projection in check 47; the check-49 SWITCH design; the check-46
   few-shot bank; anything else). For each: the root cause, and the one process change that would have caught it
   before the run rather than after.
4. EVIDENCE-TO-CLAIM GAP for the headline: if the larger test PASSES, exactly what may be claimed and what may not,
   given the pre-declared confounds (T's oracle prose scores 7/8 on delivery; history is never re-composed;
   the system-prompt worked example is an arm-invariant driver). Write the two or three sentences that should
   appear in the abstract, and the sentences that must NOT.
5. WHAT TO CUT: anything in the repo that is now dead weight, unreproducible, or superseded — name files.
6. THE HANDOFF: is results/HANDOFF-astra.md accurate and sufficient for you to continue this work alone? List
   every correction and addition it needs.
7. RANKED NEXT STEPS after the larger test, whatever its outcome, with a one-line justification each.
Grade findings low/medium/high/critical. Write ONLY that one report file; commit it with an explicit pathspec
(git add -f); no push. CPU only.
