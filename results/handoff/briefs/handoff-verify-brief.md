# Handoff readiness verification for gpt-6-astra (CPU only, docs only) — 2026-09-07

Brian is handing this project over. Your job is to make the handoff ACTUALLY ready, not to describe it as ready.
You wrote the previous audit that found the handoff "stale and unsafe to follow literally", so apply that same
standard now. No experiments. No GPU. No code changes. Docs and verification only.
VERIFY, and FIX in place what is wrong:
1. results/HANDOFF-astra.md — read it end to end as if you were starting cold tomorrow with no memory of this work.
   Check EVERY factual statement against the repository as it stands right now, including the new
   "STATE AT 2026-09-07 EVENING" section covering both larger runs. Check that every file path it names exists and
   that every number it quotes matches its source file. Fix anything stale, wrong, or missing. In particular
   confirm it correctly states: both larger runs are frozen and unrescorable; the first FAILED and why; the second
   PASSED its gates but is NARROW because the prose comparator matches or beats the register on every family and
   beats it on semantic integration; the gate for "adequate proof on a larger implementation" is NOT met; the
   agreed successor is the 32-episode factorial at about 5.32 GPU-h; and the open problems each have a report and a
   costed test.
2. results/handoff/ — verify the kit is complete and usable: every brief referenced anywhere is present, every
   chain script is present, and README.md explains how to rebuild a chain after the scratchpad is wiped. Add any
   brief or script that is missing (copy from the session scratchpad at
   /tmp/claude-1000/-home-bmarti44-stencil-llm/a88136df-3902-46b9-a661-86e0dc1bb53f/scratchpad). List what you added.
3. RESOLVE-ALL-LINKS CHECK: mechanically test that every relative path referenced in HANDOFF-astra.md,
   results/NEXT-TESTS-PLAN.md, results/CLAIMS-CORRECTIONS.md and results/handoff/README.md resolves to a file that
   exists. Report and fix every broken one.
4. A COLD-START SECTION at the top of HANDOFF-astra.md: the first ten minutes for a new engineer — what to read in
   what order, how to check whether the GPU is free and whether anything is running, the exact commands, and the
   three things they must never do (fit or select on any evaluation benchmark; rescore either frozen run; start a
   GPU job while another RUNNING.flag exists).
5. STATE THE UNFINISHED WORK precisely: anything left half-done, any file that is untracked but important, any
   process convention that only exists in this session's memory. Include the ollama/kimi setup, the vLLM image and
   flags, the guard registry, and where model weights live and which are untracked.
Commit HANDOFF-astra.md, results/handoff/** and any corrected doc with explicit pathspecs (git add -f); no push.
Report back a 10-line summary listing exactly what you fixed and anything you could not verify.
