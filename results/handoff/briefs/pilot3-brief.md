# Pilot 3 for gpt-6-astra (GPU): DEV pilot on the QUALIFIED vLLM backend with the corrected harness (2026-09-06)

Inputs: results/quick-checks/vllm-qual/README.md (QUALIFIED at concurrency 4: deterministic across three passes,
HF differs 5/64, C4 aggregate 39.9 tok/s, projection 7.85 GPU-h; the exact server image digest/flags/env are in its
records — reuse them verbatim; max-num-seqs 4), results/quick-checks/composition-pilot-2/README.md Amendment 2 (newline
append; indent gloss; backend conditions; round-0 indent-compliance gate; trait-swap rule), fable's reviews
results/composition-pilot-review-fable.md and composition-pilot-2-review-fable.md.
Run (write results/quick-checks/composition-pilot-3/RUNNING.flag; the GPU must be idle; start the vLLM container
yourself as in the qualification; stop/rm only your own container at the end; cap 2.5 GPU-h):
1. Backend: vLLM bf16, VLLM_BATCH_INVARIANT=1, prefix caching, plain token-id prompts from the package renderer
   (controller/register/renderer/checker/executor outside the server, in-process via loop.generate_once with a
   vLLM decoder adapter that keeps the same EOS/cap/context semantics for every arm). Determinism check first:
   replay 8 frozen DEV-00 prompts single-stream and at concurrency 4 mixed across arms -> must be identical (D=0).
2. DEV episodes in the frozen order 00,01,06,07,02,03,04,05 (both lengths), arms R, N, T sequentially per episode
   but with the four arms (or four episodes) submitted concurrently at max-num-seqs 4 — the concurrency schedule
   must be fixed and recorded; O only if time remains. Corrected harness (newline append; indent gloss; amended
   parser; new prompt example). Gold events drive R in DEV only (state it).
3. Gates (pre-written in README before GPU): round-0 indent compliance in R >= 50% of eligible edits across DEV
   (else apply the registered trait-swap rule on CPU afterwards and re-pilot the swapped trait only); executed-call
   rate >= 90%; truncation <= 2% (T's cumulative re-emission counts symmetrically as breakage — report it);
   R final success on DEV >= 5/8 (competence floor for the larger test's power); nonzero executed-trait relapse
   denominators in >= 2 episodes for >= 2 kinds; max context <= 32,768 - 512; measured cost projection for
   R/N x64 + O/T x16 <= 12 GPU-h at the measured concurrency-4 rate (no unmeasured credit).
   ELIGIBLE = all gates pass -> the larger test may be registered; INELIGIBLE with the failing item otherwise.
4. Journal everything (v2 field list + tolerances applied + backend identity/digest + per-call timing); hidden
   states are NOT captured on vLLM — record that check 45 requires a teacher-forced HF prefill over the final
   transcripts (list the transcript hashes it will need).
5. Report per arm/episode: final success, stale execution, wrong skill, breakage, per-kind violations and
   executed-trait relapse with denominators, DEV mask-trigger check (v2 section 3), tok/s, seconds/call, cost.
Outputs under results/quick-checks/composition-pilot-3/ (README, records, summary, server log); item in
results/quick-checks/README.md (5 lines); WORKLOG (<= 6 lines). Commit with explicit pathspecs (git add -f); no
push; never signal any process other than stopping your own container; never read anything under data/bench;
DEV episodes only.
