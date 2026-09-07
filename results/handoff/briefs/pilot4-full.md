# POST-REBOOT NOTE (2026-09-05, power outage at ~18:27; machine up since 18:27)
The previous codex sessions died mid-task; the scratchpad was wiped. Artifacts committed in git are the only state.
GPU: a llama-server owned by Brian (pid 2705, Qwen3.8-27B Q4, ~16 GB) now runs permanently on the GPU. It is NOT a
Stencil job: treat the GPU as available for Stencil when no OTHER compute process (a .venv python) is present; never
touch pid 2705. Memory budget: 128 GB total minus the llama-server; Qwen3-30B-A3B bf16 (~61 GB) still fits. Coordinate
with other Stencil GPU checks via results/quick-checks/<check>/RUNNING.flag files (write yours while running, delete
after; wait if another Stencil flag exists). Never signal any process. All committed prior results stand; re-read the
relevant README/records rather than redoing completed work. Commit with explicit pathspecs; no push.
# Pilot 4 for gpt-6-astra: CPU fixes from fable's pilot-3 diagnosis, DEV regression on pilot-3 outputs, then the GPU pilot (2026-09-06)

Read results/composition-pilot-3-review-fable.md fully (Sections 1-4, file:line). Register "Amendment 3" in
results/quick-checks/composition-pilot-3/README.md BEFORE code, then fix, arm-neutrally:
1. CHECKER/PROMPT CONSISTENCY: check() requires report.task == the task handle LETTER ("A"/"B") but the prompt never
   says so (123/167 executed responses echo the request text; 0/460 emit the letter) -> the prompt states `task` =
   the letter, with a verbose literal example; the checker stays as is.
2. `delivery` is undefined in the prompt -> define it as a short string scoped by the task letter (never file
   content); example in the prompt.
3. Third journaled tolerance: one trailing `}` / `]` after a complete envelope, via json.raw_decode (99/460 outputs;
   95 otherwise exact) — journal it; nothing else repaired.
4. CUMULATIVE RE-EMISSION (193/460 caps; 4-5 def step_ per capped output): replace the "Preserve earlier operations,
   repairing with whole-file replace" sentence with "append only the new function; never re-emit earlier
   functions"; render the post-edit function list in the edit tool result so the model sees the file state
   without re-dumping; sharpen the envelope error text.
5. Do NOT change: renderer layout beyond the registered value gloss; T text; cap 512; band; the register.
6. DEV REGRESSION on CPU using pilot-3's literal outputs as fixtures through Executor.run/check: report executed
   rate and cap counts under the amended parser (fable projects R executed 53 -> ~101/160), and per-kind
   violations; add tests for each fix. Repo hygiene: NEVER git add files > 10 MB — keep streamed HTTP journals out
   of git with a size+sha256 manifest; add a pre-commit size guard (tools/hooks) and a test.
Then PILOT 4 on the GPU (same qualified vLLM image/flags; RUNNING.flag; cap 2.5 GPU-h; stop/rm only your container;
DEV episodes in the frozen order; arms R/N/T; O only if time remains; the pre-run reverse-order concurrency-4
determinism replay from the vLLM review; gates as pilot 3 plus: executed-call rate >= 90% per arm, truncation
<= 2%, round-0 indent compliance >= 50% (4-space bias is a real model result: if < 50%, apply the registered
trait-swap rule afterwards on CPU and say so), R DEV final success >= 5/8, measured projection <= 12 GPU-h). Journal
as before; hidden states via HF teacher-forced prefill are deferred. Outputs under results/quick-checks/
composition-pilot-4/ (README with the readings; records <= 10 MB each, else out of git with hashes); item in
results/quick-checks/README.md; WORKLOG (<= 6 lines). Commit with explicit pathspecs; no push; never signal
any process other than your own container; never read anything under data/bench; DEV only.
