# Pilot 5 for gpt-6-astra (GPU <= 1.5 h): SLAB-2 simplified harness on the qualified vLLM backend (2026-09-06)

Inputs: the SLAB-2 build (src/stencil/focus/slab2.py; its WORKLOG entry and tests) and fable's review of it
(results/slab2-review-fable.md — apply any fixes it marks as blocking BEFORE the GPU, on CPU, as a registered
amendment); the qualified vLLM image/flags (results/quick-checks/vllm-qual/); the pilot-4 diagnosis
(results/composition-pilot-4-review-fable.md) whose readings this pilot answers.
Run: RUNNING.flag under results/quick-checks/composition-pilot-5/; your own container; the pre-run reverse-order
concurrency-4 determinism replay (8 prompts) then the 8 DEV episodes at 16 rounds, arms R/N/T (O nested = R with
gold events in DEV; run O only if time remains), fixed concurrency schedule recorded, cap 1024, journal everything
(same-run; tolerances applied; per-round output hashes; timing).
PRE-WRITTEN READINGS (registered in the SLAB-2 brief): ELIGIBLE = executed (parsed trailer + file written) >= 90%
per arm; caps <= 2%; T-floor pre-check yields >= 2 rule kinds with nonzero substitution denominators in >= 2
episodes; R final success >= 5/8 on DEV; measured projection for R/N x64 + O/T x16 at 16 rounds <= 12 GPU-h (the
budget applies to the registered run itself) — if 12-15 h, apply the pre-registered 12-round fallback and report
both. INELIGIBLE with the failing item otherwise (no silent shrinking). Also report per-kind relapse with
denominators per arm, and the T-floor table (which traits enter success).
Outputs under results/quick-checks/composition-pilot-5/ (README, records <= 10 MB, summary, server log; HTTP
journals out of git with hashes); item in results/quick-checks/README.md; WORKLOG (<= 6 lines). Commit with
explicit pathspecs; no push; stop/rm only your container; never read anything under data/bench; DEV only.
