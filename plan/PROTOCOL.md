# Stencil process protocol (2026-09-11)

This file is the live process protocol for the back-on-track program. It is a copy of
sections D and E of `plan/BACK-ON-TRACK-PLAN.md`; the plan file is authoritative and this
copy is regenerated when the plan changes. The pre-2026-09 protocol is archived under
`archive/`.

## Rules (from plan/BACK-ON-TRACK-PLAN.md section D, rev 6)

1. One registration per result, short but SUFFICIENT to implement without new scientific
   choices: data lineage, complete arm definitions, frozen selection/packing rules,
   missingness and timeout handling, intervention budget, artifact schema, stopping rule,
   unit, exact test, N, measured cost, exhaustive readings. One implementation review, one
   result audit. A changed intervention or scorer gets a focused review; nothing else does.
2. Instrument bugs (checker, harness, tooling) are fixed and re-run with a one-line
   disclosure and do not consume any development budget. Policy failures (false admissions,
   refits, threshold changes, model selection) count against a registered development budget
   of at most two revisions per program; the third is a stop.
3. Every result reports the failed-criterion / demonstrated-harm / insufficient-evidence /
   equivalence distinction explicitly, with two-sided p and an interval. "Missed by one item"
   is reported as insufficient evidence only when the interval covers the gate; a
   demonstrated adverse effect is never relabelled inconclusive.
4. Kill and safety rules are excess-over-baseline at matched n, never absolute integer
   clauses; operational eligibility, missingness, efficacy and harm are separate columns.
5. Construction defects are repaired BEFORE the evaluation freeze, with disclosure and
   preserved construct/coverage (the accepted source-replay-preparation-v2 bounded-correction
   rule is the template); sealed outcomes after the freeze are untouchable. An ancillary
   arm's failure never vetoes reporting a complete prespecified primary pair.
6. GPU launches require the Exp 0 pilot's measured budget in the registration; budget
   exhaustion is recorded INCOMPLETE, never rescued.
7. One `results/<name>/RESULTS.md` per result; reviews under `results/reviews/`; no new
   root-level review markdown; per-item records saved as they complete.
8. A claim enters README only from a RESULTS.md with a p-value and interval, or an explicit
   "descriptive" label, stating n, p and the arm it lost to. A reviewer score is never evidence of efficacy.
9. Autonomous execution (Brian, rev 6). The orchestrator runs the execution order end to end
   without blocking questions. The only interrupts are: an HF login that is missing, a push to
   the GitHub remote (never done without Brian), stopping a process this session did not
   launch, and a change to the registered arms or estimands (which is a new registration, not
   a question). Every other choice is made by the most conservative reading, recorded in
   `plan/LEDGER.md`, and flagged in the next result audit. Progress is written ahead to the
   ledger before every long step so a context reset resumes from its STATE line.
10. Getting unstuck with Astra. "Stuck" is defined mechanically: two failed attempts at the
    same test/bug, a registration choice the plan does not cover, a result whose reading is
    not in the exhaustive list, or a review finding the orchestrator cannot refute in one
    pass. Then, and only then, invoke Astra read-only:
    `codex exec --skip-git-repo-check -C /home/bmarti44/stencil-llm -s read-only -m gpt-6-astra
    -c 'model_reasoning_effort="xhigh"' < prompt.md > results/reviews/<date>-<topic>-astra.md`,
    launched detached (`setsid nohup`, `.done` sentinel, Monitor until-loop) so the 10-minute
    Bash timeout cannot kill it. The prompt states the stuck condition, the two attempts made,
    the files involved, and forbids reading `data/bench/`. Astra's answer is adopted only if it
    adds no arm, model, benchmark or review stage; otherwise it is recorded as declined with
    one line of reason. Astra also performs the one implementation review and one result
    audit per registration (rule 1); Opus at maximum effort is the substitute when codex is
    unavailable, recorded in the review header per AGENTS.md.

## GPU coordination (plan section E)

- Sizing, which decides everything: the GB10 has 119 GB unified memory. Every Stencil run in
  this plan is Qwen3-1.7B (bf16 weights 3.4 GB) at contexts <= 4,096 tokens; the manual
  attention path's transient fp32 tensors at T=4,096 are 1.0 GiB per layer for scores and
  2.3 GiB for logits, so the expected process peak is 8-15 GB (Exp 0 measures it). The peer's
  Ouro-2.6B bf16 work is ~6-10 GB. Both fit together with tens of GB to spare, so the default
  is CONCURRENT use. Bitwise determinism is per-process (`torch.use_deterministic_algorithms`
  + fixed cuBLAS workspace, `determinism.py:13-18`); a co-resident process changes throughput,
  not results. Exp 0 checks this once: the 8-dev-session qualification run is repeated with
  the peer resident (if it is) and must be bitwise identical to the solo run.
- Reservation file, not an exclusive lock: `tools/gpu_reserve.sh <name> <est-minutes>
  <peak-gb> -- <cmd>` (~15 lines) appends `{name, pid, started, eta, peak_gb}` to
  `/home/bmarti44/.gb10-gpu.reservations` under `flock`, appends the pid to
  `.stencil-owned-pids`, removes its line on exit, and refuses to launch when
  `free memory < own peak_gb + sum(other reservations' peak_gb) + 8 GB headroom`. It takes the
  exclusive `flock -n` on `/home/bmarti44/.gb10-gpu.lock` only when called with `--exclusive`,
  which this plan never needs (no 30B, nothing > 40 GB). Offered to the peer as-is; if they do
  not adopt it, their processes are read from `nvidia-smi` with an assumed 12 GB peak.
- Guard change (`src/stencil/determinism.py:34`, `assert_gpu_free_or_owned`): keep the
  exclusive semantics as the default; add shared mode when `STENCIL_GPU_SHARE=1`: foreign pids
  are allowed if they are all listed in the reservations file or in
  `STENCIL_GPU_FOREIGN_PIDS`, and the memory rule above holds. Nothing else changes.
- Etiquette with "looped-transformer": message before any run > 30 min with its peak_gb and
  ETA, and when it ends; message immediately on any OOM either side (the OOM side retries
  after the other finishes; no first-come dispute); chunk runs <= 50 min; never signal a
  foreign process; no `nvidia-smi --gpu-reset`; one Stencil GPU process at a time; contexts
  <= 4,096 tokens.
- Timing budgets are measured under whatever load is present; the pilot summary records the
  co-resident processes, and every registration carries a 1.5x factor on the pilot's
  seconds/item so contention never turns a run into INCOMPLETE.
- Enforceable stopping: per work-arm records saved as they complete; a run stops STARTING new
  items when its reservation has 5 minutes left; `--deadline` is a per-item generation cap,
  not the reservation.

