# POST-REBOOT NOTE (2026-09-05, power outage at ~18:27; machine up since 18:27)
The previous codex sessions died mid-task; the scratchpad was wiped. Artifacts committed in git are the only state.
GPU: a llama-server owned by Brian (pid 2705, Qwen3.8-27B Q4, ~16 GB) now runs permanently on the GPU. It is NOT a
Stencil job: treat the GPU as available for Stencil when no OTHER compute process (a .venv python) is present; never
touch pid 2705. Memory budget: 128 GB total minus the llama-server; Qwen3-30B-A3B bf16 (~61 GB) still fits. Coordinate
with other Stencil GPU checks via results/quick-checks/<check>/RUNNING.flag files (write yours while running, delete
after; wait if another Stencil flag exists). Never signal any process. All committed prior results stand; re-read the
relevant README/records rather than redoing completed work. Commit with explicit pathspecs; no push.
# Check 51 for gpt-6-astra (GPU <= 10 min): the missing POSITIVE CONTROL for mode switching (2026-09-07)

Source: results/check49-review-opus.md (HIGH finding 1) and the addendum on results/quick-checks/check49/README.md.
Check 49's SWITCH endpoint is inadmissible: in every arm, including the every-request-text comparator T and the
swapped-label control X, the TRANSCRIPT WINS 36/36 — each SWITCH generation copies the previous answer with one
constant incremented, so no carrier (adapter OR text) was ever shown capable of flipping the mode against a
retained transcript. Supply that positive control before anything else in this line.
Design (quick test first; write the reading into README before any GPU work):
- Same frozen bf16 Qwen3-4B, same episode construction and scorers as check 49 (reuse its committed harness; do not
  refit or reload adapters — this is a TEXT-only control).
- Use the SETUP families only. Do NOT open or re-use the 12 evaluation episodes' prompts (no second look).
- 8 generations: build the check-49 SWITCH situation (two prior assistant answers in mode A, then a same-family
  request whose only change is a constant), and render the mode-B rule as a RECENCY instruction at the switch turn
  — i.e. in the current user turn immediately before the request, in the production renderer's live-rules form,
  not in the system message.
- Report per generation: emitted language, executable correctness, whether it copied the prior answer's structure,
  and the first divergent token versus the retained-transcript continuation.
- PRE-WRITTEN READING: CONTROL-PASS = >= 6/8 switch to mode B with executable correctness preserved -> a carrier
  CAN beat a retained transcript when placed at recency, so check 49's SWITCH cell is a placement artifact and the
  corrected re-run is authorized (fourth text-at-recency arm, output cap 96 -> 160, spend the registered fitting
  ceiling). CONTROL-FAIL = <= 3/8 -> no carrier tested so far can flip a mode against a retained transcript; record
  that as the finding, and the switch question moves to the register's MASKING contingency (checks 40h/40i) rather
  than to any carrier. 4-5/8 = INCONCLUSIVE at n=8; record and stop.
Cap 10 GPU-minutes; RUNNING.flag under results/quick-checks/check51/; wait for any other flag (pilot 6 owns the GPU
now); your own container if one is needed; never signal any process. Outputs under results/quick-checks/check51/
(README with the reading, records <= 10 MB); item 51 in results/quick-checks/README.md; WORKLOG (<= 4 lines).
Commit with explicit pathspecs (git add -f); no push; never read anything under data/bench.
