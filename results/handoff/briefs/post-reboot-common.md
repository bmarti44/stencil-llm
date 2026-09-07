# POST-REBOOT NOTE (2026-09-05, power outage at ~18:27; machine up since 18:27)
The previous codex sessions died mid-task; the scratchpad was wiped. Artifacts committed in git are the only state.
GPU: a llama-server owned by Brian (pid 2705, Qwen3.8-27B Q4, ~16 GB) now runs permanently on the GPU. It is NOT a
Stencil job: treat the GPU as available for Stencil when no OTHER compute process (a .venv python) is present; never
touch pid 2705. Memory budget: 128 GB total minus the llama-server; Qwen3-30B-A3B bf16 (~61 GB) still fits. Coordinate
with other Stencil GPU checks via results/quick-checks/<check>/RUNNING.flag files (write yours while running, delete
after; wait if another Stencil flag exists). Never signal any process. All committed prior results stand; re-read the
relevant README/records rather than redoing completed work. Commit with explicit pathspecs; no push.
