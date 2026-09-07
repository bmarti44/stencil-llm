# POST-REBOOT NOTE (2026-09-05, power outage at ~18:27; machine up since 18:27)
The previous codex sessions died mid-task; the scratchpad was wiped. Artifacts committed in git are the only state.
GPU: a llama-server owned by Brian (pid 2705, Qwen3.8-27B Q4, ~16 GB) now runs permanently on the GPU. It is NOT a
Stencil job: treat the GPU as available for Stencil when no OTHER compute process (a .venv python) is present; never
touch pid 2705. Memory budget: 128 GB total minus the llama-server; Qwen3-30B-A3B bf16 (~61 GB) still fits. Coordinate
with other Stencil GPU checks via results/quick-checks/<check>/RUNNING.flag files (write yours while running, delete
after; wait if another Stencil flag exists). Never signal any process. All committed prior results stand; re-read the
relevant README/records rather than redoing completed work. Commit with explicit pathspecs; no push.
# Pilot-5 registered fix + 8-lane screen for gpt-6-astra (2026-09-07)

Source: results/composition-pilot-5-review-opus.md and the addendum appended to
results/quick-checks/composition-pilot-5/README.md. The register arm's execution deficit is an INSTRUMENT
ARTIFACT: all 65 R non-executions are "too many fences" (the model emits both core.py and policy.py, or re-opens a
fence after a bare path line), failures are per-EPISODE (0 of 96 locked rounds ever recover because the model
copies its own round-0 layout out of history and the feedback is an opaque category token), and the root cause is
the SYSTEM PROMPT at slab2.py:63, not the rendered register block.
PART 1 (CPU; register "SLAB-2 Amendment 3" in tests/fixtures/slab2_cpu_report.md BEFORE code):
1. Rewrite slab2.py:62-64 so the format instruction carries ONE worked example showing a single fence opener that
   carries the path (the knife-edge is one token: "# core.py" parses, a bare "core.py" line does not), and so it
   cannot be read as licensing two files in one reply. Keep it arm-neutral: identical text for R, N, T, O, Q.
2. Add a shape restatement to the ReplyError feedback: instead of the opaque {"category":"fence_count_or_kind"}
   token, return the one-line expected shape plus the count of fences seen. Registered, bounded, journaled.
3. Register the LANE (episode) as the execution unit alongside the per-round number: report both, and make the
   ELIGIBLE gate read on lanes (all-16-rounds-failed lanes counted once) with the per-round figure descriptive.
4. Fix the T-floor denominator: the indent trait is unsatisfiable before the supersede turn (no arm satisfies it
   before turn 11), so the floor must count only APPLICABLE post-change rounds; recompute the floor table from the
   saved pilot-5 T records under the corrected denominator and report which kinds now qualify.
5. Add the mandatory Q arm to the cost projection (~+2.6 h; the pinned module calls it mandatory but pilot 5
   omitted it) and restate the projection range (6.6-7.8 h measured, ~10.4 h with Q).
6. Tests for each; run tests/test_focus_slab2*.py + tests/test_no_side_effect_imports.py; commit with explicit
   pathspecs; record the new pinned green SHA in tests/fixtures/slab2_cpu_report.md.
PART 2 (GPU, <= 15 GPU-minutes, only after Part 1 is committed and green; RUNNING.flag under
results/quick-checks/pilot5-screen/; wait for any other flag; your own container; stop/rm it after):
Run 8 lanes only — 2 DEV episodes x arms R/N/T/Q at 16 rounds from the new pinned SHA — and report: round-0 fence
failures per arm (predicted 0/8 lanes), execution per lane and per round, caps, and the measured x-factor.
PRE-WRITTEN READING: SCREEN-PASS = zero round-0 fence failures in all 8 lanes AND per-lane execution 8/8 AND
per-round execution >= 90% in every arm -> the pilot-5 gates are re-run in full as pilot 6 (8 DEV episodes,
R/N/T + Q, 16 rounds) and, if pilot 6 reads ELIGIBLE, the 64-episode larger test is authorized. SCREEN-FAIL =
any round-0 fence failure remains -> stop and report the literal outputs; do not enlarge.
Outputs under results/quick-checks/pilot5-screen/ (README with the reading, records <= 10 MB); item in
results/quick-checks/README.md; WORKLOG (<= 4 lines). No push; never signal any process; never read anything under
data/bench.
