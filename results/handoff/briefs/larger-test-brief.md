# LARGER TEST for gpt-6-astra (GPU, <= 12 GPU-h): register + every-request rendering vs ordinary history on 64 fresh agentic coding episodes (2026-09-06)

Governing: results/focus-mechanism-composition-v2-astra.md section 2 + addenda (12 GPU-h; actuator OFF — router
bias line CLOSED by 40k/40l; mask a flagged contingency not enabled here), Amendment 2 in
results/quick-checks/composition-pilot-2/README.md (harness fixes; backend conditions), the vLLM qualification
(results/quick-checks/vllm-qual/) and PILOT 3 (results/quick-checks/composition-pilot-3/README.md — this brief may
only be executed if pilot 3 read ELIGIBLE; if it read INELIGIBLE, stop and report). Fable's reviews of all of the
above apply.
REGISTRATION (write results/larger-test/REGISTRATION.md and commit it BEFORE opening any evaluation episode):
- Data lineage line: fit-on none (explicit-entry register; frozen relation classifier v2 assistive only; frozen
  renderer bytes per the amended golden); development-on = DEV episodes 00-07 only; evaluated-on = the 64 frozen
  evaluation episodes (manifest hashes from the bank; never opened until now); no benchmark data anywhere.
- Arms: R (register + every-request rendering; explicit structured entries from the episode's event schedule —
  this is the SHIPPED mode; automatic admission is parked), N (ordinary complete history), and the nested subset
  O/T on the pre-registered 16 episodes (O = gold events + renderer = R here, so O is a replication of R on the
  subset; T = evaluator text restated every request). Same backend (vLLM, the qualified image digest/flags/env,
  VLLM_BATCH_INVARIANT=1, max-num-seqs 4), same EOS/cap/context semantics, fixed concurrency schedule recorded.
- Primary: exact one-sided McNemar/sign test, final success R > N, alpha .05 (single primary). Secondary
  (descriptive with CIs): stale execution, wrong skill, per-kind violations and executed-trait relapse with
  denominators, breakage (paired clause only: B_R - B_N <= 1 per v2), R vs T, cost per successful episode.
- PRE-WRITTEN PASS (all): completed accounting for all 64 pairs; R final success >= 32/64 (the pilot-calibrated
  competence floor — replace with the exact pilot-3-derived floor, state it); primary p <= .05 with observed gain
  >= 8/64; paired breakage clause; zero silent state/cache/provenance failures; GPU allocation <= 12 h.
  FAIL = completed but conjunction unmet. INCOMPLETE = budget/deadline stop with unrun pairs (never drop pairs).
  INELIGIBLE = R below the competence floor (report N/T as well, no retuning).
- Freeze: code, bank manifests, checker hashes, renderer golden, backend digest, seeds, schedule, this file — one
  commit; then run. No prompt/schema/renderer/scorer change after seeing any evaluation output.
RUN: results/larger-test/RUNNING.flag; one vLLM container (yours); order = randomised episode blocks (seeded) with
R/N interleaved; the O/T subset after R/N completes if budget remains (pre-registered order); journal every field
(v2 list + tolerances + backend identity + timing) in the same run; cooperative deadline at 11.5 GPU-h including
load and cleanup; preserve records before aggregates. Stop/rm only your container.
REPORT: results/larger-test/RESULTS.md with the pre-written reading applied mechanically, per-episode table,
paired statistics, per-kind relapse curves by round, cost audit, backend identity and HF<->backend divergence
disclosure (5/64 on DEV-00), and the exact claim ceiling from v2. Item in results/quick-checks/README.md (5 lines);
WORKLOG (<= 6 lines). Commit with explicit pathspecs (git add -f); no push; never read anything under data/bench.

ADDED from fable's vLLM review (results/vllm-qual-review-fable.md): before the run, do a ~3-GPU-minute post-restart
reverse-order concurrency-4 replay of the long frozen DEV-00 prompts (fresh prefill under concurrency, KV-recompute
invariance) and require identity; record per-round output-id hashes throughout; use the measured PILOT-3 served
projection (expected 8-11 h band; per-stream decode falls ~0.9 tok/s per 1k context, so 32-round episodes decode
slower than the 5-11k rate); the HF hidden-state recovery for check 45 is uncosted here and runs AFTER the larger
test if budget remains, else later. Correct the disclosure: 4 distinct HF divergences of 48 distinct prompts.
