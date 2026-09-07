# POST-REBOOT NOTE (2026-09-05, power outage at ~18:27; machine up since 18:27)
The previous codex sessions died mid-task; the scratchpad was wiped. Artifacts committed in git are the only state.
GPU: a llama-server owned by Brian (pid 2705, Qwen3.8-27B Q4, ~16 GB) now runs permanently on the GPU. It is NOT a
Stencil job: treat the GPU as available for Stencil when no OTHER compute process (a .venv python) is present; never
touch pid 2705. Memory budget: 128 GB total minus the llama-server; Qwen3-30B-A3B bf16 (~61 GB) still fits. Coordinate
with other Stencil GPU checks via results/quick-checks/<check>/RUNNING.flag files (write yours while running, delete
after; wait if another Stencil flag exists). Never signal any process. All committed prior results stand; re-read the
relevant README/records rather than redoing completed work. Commit with explicit pathspecs; no push.
# Amendment 6b for gpt-6-astra (2026-09-07): fix the scoped-protocol feedback, re-pilot, then the authorized rerun

THE INDENTATION FIX WORKED. Pilot 8 (results/quick-checks/composition-pilot-8/README.md) recorded ZERO initial and
zero surviving syntax or indentation errors in every arm, zero repairs needed, across all 512 records. That was
Brian's authorized fix and it is done. Pilot 8 read STOP for a DIFFERENT, new reason, and the fresh 64-episode bank
remains model-unopened and unspent. Brian's authorization ("fix the indentation issue and rerun") still governs: get
to the rerun, but only through a clean pilot.

WHAT STOPPED IT, and it is the same lock signature as pilots 3-5 with a new surface:
 - R's slab2-dev-00 emitted an extra `identity` function in ALL 16 rounds and was rejected for scope_violation.
 - N's slab2-dev-01 used the literal opening fence `python #policy.py` in ALL 16 rounds and was rejected for
   fence_syntax before body parsing. Q had two isolated scope violations.
 - You disclosed the cause yourself after freeze: the scoped rejection path initializes state by calling the OLD
   executor with an empty output, so the feedback the model receives still says the expected shape is a "whole
   Python file" with `fences_seen=0`, even under the scoped protocol. The model is being told the wrong thing and,
   as in every previous lock, it never recovers.
PART 1 (CPU) - register "SLAB-2 Amendment 6b" BEFORE code in tests/fixtures/slab2_cpu_report.md, then:
1. Fix the scoped rejection path so it never calls the old executor for state initialization; the feedback must
   state the SCOPED expectation literally ("emit only the function <name>, nothing else"), report the actual fences
   seen, and name the offending extra definition when the cause is scope_violation.
2. Give the system prompt ONE worked example of the scoped shape, exactly as Amendment 3 did for fences, so the
   two observed failures cannot originate at round zero. Arm-neutral wording for R, N, T and Q.
3. Add consumer tests for both observed rejection causes: an extra top-level definition, and a malformed opening
   fence line; assert the returned feedback is actionable and that a corrected second attempt is accepted.
4. HARM CLAUSE COVERAGE: pilot 8 reported both harm contrasts tying at p = 1 with insufficient coverage against a
   75% episode-coverage requirement. Determine whether that requirement is ACHIEVABLE AT ALL on eight DEV episodes
   given how many episodes schedule an attempted indent change; if it is not, the gate is ill-formed in the same way
   as the old <= 1 breakage bar, and you must re-specify it so it is satisfiable on the DEV set it gates, or move
   the coverage requirement to the 64-episode run where the denominator exists. Apply your own rule: test the gate
   against its own negative control at the registered unit before freezing.
5. Tests; run tests/test_focus_slab2*.py + tests/test_no_side_effect_imports.py; commit with explicit pathspecs;
   record the new pinned green SHA.
PART 2 (GPU <= 1 h) - pilot 9 on the 8 DEV episodes, arms R/N/T/Q.
PRE-WRITTEN READING: FIX-CONFIRMED = per-lane execution 8/8 in EVERY arm, zero surviving syntax or indentation
errors, zero round-zero rejections, and the primary computable with nonzero denominators for >= 2 families.
Otherwise report the failing item and STOP; do not open the fresh bank.
PART 3 (GPU <= 12 h) - only on FIX-CONFIRMED: the full 64-episode rerun on the fresh unopened bank exactly as
specified in Amendment 6, under results/larger-test-v2/.
The frozen original (SHA 95fa7fc0) is never touched, rescored or reinterpreted. Outputs: pilot under
results/quick-checks/composition-pilot-9/; commit with explicit pathspecs (git add -f); no push; stop/rm only your
own container; never signal any process; never read anything under data/bench.
