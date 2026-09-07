# POST-REBOOT NOTE (2026-09-05, power outage at ~18:27; machine up since 18:27)
The previous codex sessions died mid-task; the scratchpad was wiped. Artifacts committed in git are the only state.
GPU: a llama-server owned by Brian (pid 2705, Qwen3.8-27B Q4, ~16 GB) now runs permanently on the GPU. It is NOT a
Stencil job: treat the GPU as available for Stencil when no OTHER compute process (a .venv python) is present; never
touch pid 2705. Memory budget: 128 GB total minus the llama-server; Qwen3-30B-A3B bf16 (~61 GB) still fits. Coordinate
with other Stencil GPU checks via results/quick-checks/<check>/RUNNING.flag files (write yours while running, delete
after; wait if another Stencil flag exists). Never signal any process. All committed prior results stand; re-read the
relevant README/records rather than redoing completed work. Commit with explicit pathspecs; no push.
# Pilot 6 for gpt-6-astra (GPU <= 2.5 h): the full SLAB-2 gates after Amendment 3 (2026-09-07)

Context: the Amendment 3 fix WORKED on the thing it targeted — results/quick-checks/pilot5-screen/README.md records
all 8 round-0 format checks passing, all 8 lanes writing files and zero caps; it read SCREEN-NOT-PASS only because
its 15-minute budget stopped 4 lanes at round 2. Do not re-run the screen. Run the full pilot from the pinned green
SHA recorded in tests/fixtures/slab2_cpu_report.md (verify `git rev-parse HEAD` before any GPU access; isolated
checkout; clean tracked tree).
Run: RUNNING.flag under results/quick-checks/composition-pilot-6/; your own container (the qualified vLLM image,
flags and env from results/quick-checks/vllm-qual/); the pre-run reverse-order concurrency-4 determinism replay
(8 prompts, D=0 required); then the 8 DEV episodes at 16 rounds, arms R / N / T / Q, fixed concurrency schedule
recorded, cap 2048, same-run journal with per-round output hashes.
PRE-WRITTEN READINGS (Amendment 3 semantics: the LANE is the execution unit; the per-round figure is descriptive;
the T floor counts only APPLICABLE post-change rounds):
ELIGIBLE = zero round-0 format failures; per-lane execution 8/8 in every arm; per-round execution >= 90% per arm;
caps <= 2%; >= 2 substitution kinds clear the corrected T floor with nonzero denominators in >= 2 episodes;
R final success >= 5/8; and the measured projection for the 64-episode larger test (R/N x64 + O/T x16 + Q) <= 12
GPU-h. A projection in (12, 15] triggers the frozen 12-round fallback with fresh DEV validation, never fewer arms;
above 15, stop. INELIGIBLE with the failing item; INCOMPLETE if the budget stops work (never a partial pass).
Also report, as pre-registered diagnostics: the matched-cell comparison the pilot-5 review surfaced (on cells where
all arms wrote a file, per-trait R vs N vs T, with the post-change indent lead R 0/9 vs N 8/9 vs T 8/9 from pilot 5
stated as the prior), and per-kind relapse with executed-trait denominators.
Outputs under results/quick-checks/composition-pilot-6/ (README with the readings, records <= 10 MB, summary,
server log; HTTP journals out of git with hashes); item in results/quick-checks/README.md; WORKLOG (<= 6 lines).
Commit with explicit pathspecs (git add -f); no push; stop/rm only your own container; never signal any process;
never read anything under data/bench; DEV episodes only.
