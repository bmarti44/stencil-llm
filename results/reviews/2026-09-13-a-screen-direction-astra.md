Reading prompt from stdin...
OpenAI Codex v0.154.0
--------
workdir: /home/bmarti44/stencil-llm
model: gpt-6-astra
provider: openai
approval: never
sandbox: read-only
reasoning effort: xhigh
reasoning summaries: none
session id: 01a09c3c-7238-7c90-8ced-b0f401972973
--------
user
# Adversarial review: is this direction worth taking at all?

You are reviewing the Stencil repository at /home/bmarti44/stencil-llm as an
independent adversarial reviewer. Use MAXIMUM reasoning effort. You are
author-disjoint from everything below: you wrote none of it.

**Do not read anything under `data/bench/`.** It holds evaluation benchmarks and
recorded responses; reading it would contaminate the work. Nothing you need is
there.

Write ONLY this review file. Do not edit code.

## Your job

Brian's standing instruction, verbatim: *"we need to make sure we find a novel,
useful recombination of techniques that is not technically novel based on a
meaningless permutation, that is a significant difference, and that has a good
chance of actually working based on current research, not only in the AI
domains - but also all other academic domains. use astra to adversarially try to
disprove the goal with deep web research and anything else that I'm not thinking
of, and consider the goal satisfied when astra can not prove it."*

So: **try to disprove it.** The direction is satisfied only if you cannot.
"Good chance of working" has a numeric bar: **a direction at >= 25% on your
artifact-success forecast is NOT DISPROVED on that criterion.** State your
forecast as a number and say which side of 25% it falls.

Do deep web research. Cover 2024-2026 machine learning, and also look outside
it — cognitive psychology of belief revision and memory updating, formal belief
revision, database/version-control conflict resolution, legal interpretation of
superseded rules, anything that bears on "an agent must stop applying a rule
that was cancelled and keep applying the ones that were not."

## What you reviewed before, and what has changed

Your previous review is `results/reviews/2026-09-13-a-screen-backontrack-astra.md`
(verdict: OFF TRACK, 20%, below 25%). Read it first. Everything below postdates
it and you have not seen any of it. Re-derive your forecast; do not anchor on 20%.

Changes since, all CPU-only:

1. **The mislabelled population is corrected.** You found that
   `stale2.py` called request 1 "no supersession yet" for every session, which
   is false for the 12 reinstatement sessions. The population key is now derived
   (`alt_was_in_force`) and tested over all 624 pool sessions
   (`tests/test_a_screen_supersession.py`).
2. **A baseline results document** — `results/a-screen/RESULTS-BASELINE.md` —
   with the corrected four-cell table, Fisher p = 0.0025 on request 1 and
   p = 0.139 on request 2, family/lifecycle/transition breakdowns, and a stated
   confound list.
3. **`compare.py` refuses before it computes** (identity, completeness,
   uniqueness, replay, step-matching), with 14 mutation tests; **`preflight.py`**
   rewritten on "a check that cannot run is a FAILURE", with 52 mutation tests.
4. **The runner exception is established by recomputation**
   (`analysis/runner_equivalence.py`, `RUNNER-EXCEPTION.md`): the `off` baseline
   does not need re-running, saving ~1 GPU-hour.
5. **`names.py`'s "isolated retention" interpretation is retired**, for the two
   reasons you gave.
6. **The cf adapter finished training**: 134 optimizer steps, status complete,
   `epochs_completed` 0 (still the first pass), CE 0.0006 on never-before-seen
   examples, margin +8.8, loss already 0.0154 at step 40.
7. **A memorisation check I added** (`analysis/overlap.py`): across 192 screen
   golds the closest of 2,304 training golds scores 0.254 difflib / 0.329 token
   Jaccard at MAXIMUM, median 0.124 / 0.244, 0/192 above 0.70.
8. **An instrument defect I found in my own analysis**: run under a bare
   `python3` without pytest, `contracts.run_tests` returns False for every suite,
   so all 96 replies classified "neither" and both contrasts read p = 1.000 — a
   clean, plausible, entirely empty table. Both scripts now self-check.
9. **The design's resolution floor**: with 0 discordant pairs at n = 36 the
   registered conservative paired interval is still +/- 11.5 points. A
   wholly-positive interval needs 10 wins with 0 losses, 12 with 1, 14 with 2.

## The questions, in priority order

1. **Is candidate A a substantive recombination or a meaningless permutation?**
   It is completion-token cross-entropy on gold plus `0.1 * L_DPO` (beta 0.1,
   frozen-trunk reference) where the rejected response is the gold under the
   SUPERSEDED convention. You previously identified Context-DPO (Bi et al., ACL
   2025), Counterfactual DPO (Butcher 2024), IOPO and CRPL as prior art. Is
   anything left that is both substantive and defensible? Answer plainly,
   including "no" if that is the answer.

2. **Is "conditional revision" — the alternative you named: switch when
   applicable, preserve unaffected behaviour, restore when reinstated — actually
   better?** Is IT prior art? Is it a permutation? Does the existing four-lifecycle
   screen (stable / replacement / scope / reinstatement) already operationalise
   it, and if so what would have to change to test it as a claim rather than as
   a taxonomy? Is there published work on scoped or partial rule revision in
   LLMs that makes this dead on arrival too?

3. **Given the +/- 11.5-point resolution floor, is the remaining 1 GPU-hour
   worth spending?** Consider that it cannot resolve a modest effect, that
   cf-vs-off cannot attribute anything to the counterfactual term, and that the
   matched SFT arm is a further ~2.5 GPU-hours. Is there a cheaper experiment
   that discriminates better — including CPU-only ones, or ones on a smaller
   trunk?

4. **Attack today's new work.** Is the corrected population key right, or is
   there a third case I have still mislabelled? Does the overlap measurement
   actually license "not verbatim recall", or is difflib/Jaccard on source text
   the wrong measure for that claim? Do the guards have the "passes by doing
   nothing" property you found twice before? Is `RESULTS-BASELINE.md` honest
   about its selection effect and its confounds, or does any sentence in it
   overclaim?

5. **What am I not thinking of?** Other fields, other framings, other
   workloads, other cheap decisive tests. This is the part Brian asked for
   explicitly.

## Output

End with one line in this form:

`VERDICT — <ON TRACK|OFF TRACK> — <N>% artifact-success forecast, <above|below>
25%; <the single most important action>.`

Grade findings low/medium/high/critical. Cite files as
`/home/bmarti44/stencil-llm/<path>:<line>`. Never delete or soften a prior
finding — mark it resolved or refuted with the evidence.

codex
I’ll read the governing process and prior review first, then audit the new evidence and research the strongest prior-art challenges. I’ll stay out of `data/bench/` and make no code changes. This session has read-only filesystem access, so saving the review file may be blocked.

exec
/bin/bash -lc "pwd && sed -n '1,240p' plan/PROTOCOL.md && rg -n '"'^STATE'"' plan/LEDGER.md && sed -n '1,260p' results/reviews/2026-09-13-a-screen-backontrack-astra.md" in /home/bmarti44/stencil-llm
 succeeded in 0ms:
/home/bmarti44/stencil-llm
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

3967:STATE: running the candidate-A screen. SCREEN pool ef802ce2160ee00c, TRAIN b8f504494a281858.
**OFF TRACK at a 20% artifact-success forecast, below the 25% bar.** The baseline exposes a real problem. It does not yet establish the claimed updating-versus-retention effect, and there is no evidence that Candidate A improves anything. One `cf` evaluation is worth considering as a bounded decision purchase; the proposed four-step commitment is not.

I read no `data/bench/`, performed no GPU work, and changed no files. I reconstructed all 96 replies, verified every before/after repository hash, and reproduced the contract classifications. Contract and functional tests ran with temporary-file operations held in memory because this session is read-only; all 192 corresponding recorded pass/fail values agreed. I did not repeat the original subprocess isolation.

**1. The baseline counts are correct. The “nothing superseded yet” interpretation is wrong — high.**

I reproduced your table, J=6, function-only=15, eight stale replies passing their functional suite, and six current-rule replies passing theirs. The replay and classification logic handles this complete baseline correctly. [stale2.py:46](/home/bmarti44/stencil-llm/results/a-screen/analysis/stale2.py:46), [records:1](/home/bmarti44/stencil-llm/results/a-screen/runs/off-oldrunner.jsonl:1)

But **all four request-1 stale replies are reinstatement sessions: S12, S20, S36, S44. Those prefixes already contain a supersession.** For example, S12 first specifies verb–noun, then changes to noun–verb before request 1. That replacement survives prompt packing. The script’s assertion that request 1 has no supersession is false. [s12.py:632](/home/bmarti44/stencil-llm/src/stencil/a_screen_pool/s12.py:632), [s36.py:420](/home/bmarti44/stencil-llm/src/stencil/a_screen_pool/s36.py:420), [stale2.py:11](/home/bmarti44/stencil-llm/results/a-screen/analysis/stale2.py:11)

The corrected breakdown is:

| Population | In force | Superseded/alternative | Neither |
|---|---:|---:|---:|
| Request 1, no preceding replacement | 25/36 | **0/36 alternative** | 11/36 |
| Request 1, replacement already in prefix | 5/12 | **4/12 superseded** | 3/12 |
| Request 2, unchanged | 7/12 | **1/12 alternative, never in force** | 4/12 |
| Request 2, changed | 11/36 | **12/36 superseded** | 13/36 |

This supports a useful descriptive finding: **the model sometimes produces executable code consistent with an explicitly superseded instruction.** It does not identify whether the cause is instruction memory, copying existing code, prior-answer imitation, or difficulty implementing the requested change.

The 36-versus-12 imbalance affects precision; it is not itself a confound. Target families are balanced: each contributes 12 changed and four unchanged sessions. Nevertheless, lifecycle, project, request, transition direction, and code precedent are not held constant. “Changed” is exactly the union of replacement, scope, and reinstatement; “unchanged” is exactly stable. [a_screen.py:113](/home/bmarti44/stencil-llm/src/stencil/a_screen.py:113), [registration:32](/home/bmarti44/stencil-llm/results/a-screen/REGISTRATION-A-SCREEN.md:32)

Even treating the request-2 groups as independent samples, the descriptive stale/alternative comparison gives **two-sided Fisher p=0.139**. Wilson 95% intervals are approximately **20–50%** for 12/36 and **1–35%** for 1/12. That is uncertain evidence, not evidence of no effect; statistical significance would not remove the construction confounds.

What would make the causal interpretation solid is a matched comparison holding the project, entering repository, request and packing fixed while varying the applicable lifecycle message. Use that distinction in the existing confirmation if Candidate A earns one. **Do not add that experiment before finding out whether `cf` helps at all.**

**2. The direction is below the investment bar — high.**

My revised forecast is **20% for the full goal**, including useful improvement, a substantive contribution beyond the matched SFT control, transfer to the claimed session setting, and publication. This is a subjective forecast, not a statistical estimate.

The real stale-code failures increase confidence that there is a target worth addressing. The evidence reducing my forecast is more consequential:

- **Validation has zero current-rule successes at request 2: 0/12 changed and 0/4 unchanged.** Its stale/alternative rate is 25% in both groups. This family currently shows a broader execution problem.
- All six successful baseline sessions come from missing-record policy. The aggregate conceals substantial concentration.
- Of the six changed-session replies passing current contract plus `functional`, only **three** also pass regression and protected-function checks. The usefulness floor is lower than “six working current-rule replies” suggests. [records:34](/home/bmarti44/stencil-llm/results/a-screen/runs/off-oldrunner.jsonl:34), [a_screen.py:368](/home/bmarti44/stencil-llm/src/stencil/a_screen.py:368)
- The existing screen remains far from autonomous long-session performance.

The SFT comparison was already part of the earlier forecast; it should not be counted as newly discovered bad news. It remains the central uncertainty: **`cf − off` measures the adapter’s total benefit; `cf − sft` measures the incremental preference term.** SFT receives both counterfactual positive directions and irrelevant-history examples too. [registration:42](/home/bmarti44/stencil-llm/results/a-screen/REGISTRATION-A-SCREEN.md:42)

The training curve establishes successful optimization on templated examples. It establishes neither free-generation correctness nor transfer. CE is teacher-forced completion loss, including copied boilerplate; the logged margin is a minibatch average of a **β-scaled, reference-relative** log-probability difference. A large mean does not establish that every pair is solved. [trainer:166](/home/bmarti44/stencil-llm/scripts/a_screen_train.py:166), [trainer:353](/home/bmarti44/stencil-llm/scripts/a_screen_train.py:353), [trainer:400](/home/bmarti44/stencil-llm/scripts/a_screen_train.py:400)

Also, at inspection the saved checkpoint was **101 steps, `status="running"`, `final=false`**; the text log reached step 110. The approximately 137-step endpoint was still a projection. The real preflight correctly refused that checkpoint. [train-log.json:24](/home/bmarti44/stencil-llm/results/a-screen/adapters/cf/train-log.json:24), [train-log.json:75](/home/bmarti44/stencil-llm/results/a-screen/adapters/cf/train-log.json:75), [cf.log:32](/home/bmarti44/stencil-llm/results/a-screen/adapters/cf.log:32)

**3. The loss is an established-method permutation; the potential contribution is the behavioral result — high.**

“DPO against a stale alternative” is not a new training method:

- **Counterfactual DPO** already uses counterfactual instructions to construct preference training. [Butcher, 2024](https://arxiv.org/abs/2401.09566)
- **Context-DPO** trains faithful versus stubborn responses under conflicting context and reports improvements over an SFT baseline using faithful responses. This is direct support for plausibility, and direct prior art against a broad novelty claim. [Bi et al., ACL 2025](https://aclanthology.org/2025.findings-acl.536/)
- **IOPO** connects input changes with output preferences; **CRPL** constructs verified preferences from relationships between instruction constraints. [IOPO](https://arxiv.org/abs/2411.06208), [CRPL](https://arxiv.org/abs/2608.29352)
- **Mitigating Conversational Inertia** already uses LoRA preference training to reduce harmful dependence on prior agent behavior. [Zhang et al., 2026](https://arxiv.org/html/2602.03664v1)

The substantive recombination would be: **learn conditional revision of executable behavior—switch when applicable, preserve unaffected behavior, and restore an earlier rule when reinstated—with a useful advantage over SFT on the same positives.** Candidate A already attempts parts of this through paired histories and protected behavior. It needs evidence that those parts matter, not another named mechanism. [a_screen.py:463](/home/bmarti44/stencil-llm/src/stencil/a_screen.py:463), [a_screen.py:386](/home/bmarti44/stencil-llm/src/stencil/a_screen.py:386)

Research outside conventional alignment supports that target, but not this particular loss:

- Human experiments distinguish remembering an old association from remembering **that it changed**. Detecting and recollecting the change can turn interference into facilitation. My inference is that training should teach the temporal relationship, not globally suppress the old response. [Wahlheim and Jacoby, 2013](https://pubmed.ncbi.nlm.nih.gov/22918874/)
- LLM proactive-interference experiments find retrieval of overwritten values despite the final value remaining accessible near the query. This makes “instructions were still in context” an inadequate explanation of success or failure. [Wang and Sun, 2025](https://arxiv.org/abs/2506.08184)
- Belief-revision theory distinguishes revision from merely accumulating statements. It provides a specification for consistent change, not an empirical forecast that LoRA will learn it. [Alchourrón, Gärdenfors and Makinson, 1985](https://fitelson.org/piksi/piksi_22/agm.pdf)

Calling this catastrophic forgetting would confuse two problems: these evaluation failures occur during inference with fixed weights. The relevant hypothesis is interference or incorrect applicability selection.

**4. Skip the `off` rerun. Evaluate `cf` first if GPU use resumes — medium for the wasted rerun; high for the decision logic.**

I recovered the old runner from `309cf908^`; its hash matches the baseline’s `4acdb8f044c25a48`. Relative to the current runner, the changes add `--require-steps` and modify adapter eligibility checks. After excluding those two changes, the main-function AST is identical. The altered checks are inside `if a.adapter`, which the baseline does not enter. [runner:155](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:155), [runner:232](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:232)

**The old baseline is usable with a precise disclosure.** Preserve its recorded hash. Allow this exact reviewed old/new runner pairing in the analysis; retain the remaining identity checks. The main summary currently requires equal runner hashes, so its refusal is a tooling condition, not evidence that the baseline measurements are invalid. [summary:21](/home/bmarti44/stencil-llm/scripts/a_screen_summary.py:21)

The shortest sequence is:

1. Verify the final `cf` checkpoint and repair analysis validity on CPU.
2. Evaluate `cf` on the existing 48 sessions: approximately 62 minutes.
3. Apply the existing screen decision before spending on SFT.
4. Only if warranted, train SFT to `cf`’s actual completed step count and evaluate it.

That buys the first decision for roughly **one GPU-hour**. Completing the remaining SFT comparison would bring the total to approximately **3.6–4.1 hours**, using your timing estimates.

Two corrections to the stop-rule rationale:

- **“If `cf` does not beat `off`, `sft` will not either” is false.** The preference term could damage an otherwise useful SFT adapter. Stopping Candidate A can still be a sensible resource decision; it does not refute SFT or the entire problem. [LEDGER.md:3887](/home/bmarti44/stencil-llm/plan/LEDGER.md:3887)
- **16/36 is a screening threshold, not proof.** A five-win, zero-loss improvement has exact McNemar p=0.0625; ten wins and five losses gives p≈0.302 despite the same net gain. The ledger also explicitly reserves 14–15 for an ambiguous reading. [LEDGER.md:3891](/home/bmarti44/stencil-llm/plan/LEDGER.md:3891)

There is no CPU-only measurement of saved baseline replies that can establish an unmeasured adapter’s transfer. CPU work can decisively reject an interpretation or an invalid comparison. It cannot manufacture the missing adapter result.

**5. The highest-value CPU work is a small, trustworthy comparison path.**

In priority order:

1. Correct the supersession-history labels and retain a per-session classification table.
2. Make `compare.py` require the frozen session set and validated records; add the existing paired interval calculation and complete functional-preservation outcomes.
3. Record the exact runner-equivalence exception.
4. Report family, lifecycle and transition-direction breakdowns alongside aggregate outcomes.

Most of the baseline investigation behind those actions is completed in this review. Reuse the existing summary validator and interval implementation. **No new audit framework, benchmark, training arm or review round is needed.** [summary:37](/home/bmarti44/stencil-llm/scripts/a_screen_summary.py:37), [summary:191](/home/bmarti44/stencil-llm/scripts/a_screen_summary.py:191)

**6. The analysis scripts have several concrete defects.**

| Severity | Finding and minimum action |
|---|---|
| **High** | **`compare.py` silently changes the population.** Deleting S02 from one synthetic arm produced a 35-session comparison. Duplicates and wrong replay hashes were accepted; supplying two files labelled `off` overwrote the first dataset and printed `off vs off`. Require unique arm labels, complete frozen IDs, unique records and verified identity/replay before statistics. [compare.py:43](/home/bmarti44/stencil-llm/results/a-screen/analysis/compare.py:43), [compare.py:64](/home/bmarti44/stencil-llm/results/a-screen/analysis/compare.py:64) |
| **High** | **Its difference-of-differences interpretation is unjustified.** “A narrowing gap is supersession handling” is false. Different projects, floors, ceilings and family-specific gains can narrow it. The script prints gaps without an interaction interval or test. Label them descriptive; remove the causal sentence. [compare.py:100](/home/bmarti44/stencil-llm/results/a-screen/analysis/compare.py:100) |
| **High** | **“In force and functional” overstates usefulness.** It uses only the new request’s `functional` suite. It ignores regressions and protected behavior—the difference between six and three current-rule successes here. Retain that diagnostic, but also report `function_only` and J. [compare.py:60](/home/bmarti44/stencil-llm/results/a-screen/analysis/compare.py:60), [compare.py:80](/home/bmarti44/stencil-llm/results/a-screen/analysis/compare.py:80) |
| **Medium** | **`stale2.py` does not enforce its claimed fixed denominator or replay integrity.** It overwrites duplicates, counts whatever records exist, warns rather than refuses on hash mismatches, and never checks `repo_after`. This baseline passed my independent checks; future files are insufficiently protected. [stale2.py:82](/home/bmarti44/stencil-llm/results/a-screen/analysis/stale2.py:82), [stale2.py:105](/home/bmarti44/stencil-llm/results/a-screen/analysis/stale2.py:105) |
| **Medium** | **13/13 mutations do not establish preflight equivalence.** With synthetic metadata, `check()` accepted an SFT objective in the CF directory and a missing hub field. Standalone `--compare` accepted two unfinished logs with arbitrary differing objectives and absent recipe/hash fields because missing values compared equal. The runner checks the objective and expected hub. Have preflight take the intended arm/hub and make pair comparison invoke individual validation. [preflight.py:28](/home/bmarti44/stencil-llm/results/a-screen/analysis/preflight.py:28), [preflight.py:68](/home/bmarti44/stencil-llm/results/a-screen/analysis/preflight.py:68), [runner:173](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:173) |
| **Low** | **`look.py` is fine for a quick descriptive look at this complete baseline.** It trusts aggregate flags and excludes incomplete sessions, so it should not decide an arm comparison. [look.py:29](/home/bmarti44/stencil-llm/results/a-screen/analysis/look.py:29) |
| **Low** | Remove the temporary scratchpad import override from `compare.py`; it can shadow the reviewed `stale2.py`. [compare.py:20](/home/bmarti44/stencil-llm/results/a-screen/analysis/compare.py:20) |

The additional helpers are not scientific evidence. `names.py` uses gold request-1 state rather than the actual entering repository and can count shared function names outside the naming family; retire its “isolated retention” interpretation. `health.py` samples operational signals, including the largest GPU process rather than specifically the owned trainer; its health verdict says nothing about transfer. No need to expand either while GPU work is paused. [names.py:47](/home/bmarti44/stencil-llm/results/a-screen/analysis/names.py:47), [health.py:68](/home/bmarti44/stencil-llm/results/a-screen/analysis/health.py:68)

**7. Four things would invalidate the eventual broad claim — high.**

- **Claiming long-horizon instruction retention from this screen.** It has two live requests, authored earlier turns, and a packer told which rule turns to preserve. Relevant instructions are protected using `session.rule_turns`; this does not test learning to find or retain them through a real agent session. The registration already states this limitation correctly. [a_screen.py:244](/home/bmarti44/stencil-llm/src/stencil/a_screen.py:244), [a_screen.py:275](/home/bmarti44/stencil-llm/src/stencil/a_screen.py:275), [registration:98](/home/bmarti44/stencil-llm/results/a-screen/REGISTRATION-A-SCREEN.md:98)
- **Claiming architectural generalization from name-disjoint projects.** TRAIN has 18 project domains expanded into 576 sessions and 1,152 examples. The documented overlap says 44/48 screen projects share the dataclass-record/private-mapping idiom. That is acceptable for a screen, but limits what a positive result means. [a_train_pool.py:933](/home/bmarti44/stencil-llm/src/stencil/a_train_pool.py:933), [registration:217](/home/bmarti44/stencil-llm/results/a-screen/REGISTRATION-A-SCREEN.md:217)
- **Treating this exploratory endpoint as final proof.** The 36-session contract endpoint was selected after seeing `off`; the original registered outcome was session J. That is fine for deciding whether to spend more. Report the selection and retain the original outcomes. A successful screen earns the already envisaged confirmation of the actual artifact claim. [registration:101](/home/bmarti44/stencil-llm/results/a-screen/REGISTRATION-A-SCREEN.md:101), [LEDGER.md:3881](/home/bmarti44/stencil-llm/plan/LEDGER.md:3881)
- **Assuming common scoring defects cannot bias an arm difference.** The ledger says an under-sensitive checker “applies identically” and therefore cannot manufacture a difference. That inference is false: adapters can produce different kinds of undetected errors. Inspect actual winning replies if there is a positive result. This does not justify restarting the mutation-audit spiral now. [LEDGER.md:3870](/home/bmarti44/stencil-llm/plan/LEDGER.md:3870)

The defensible result today is a descriptive baseline failure analysis. A useful, substantive Candidate A result remains possible, but unmeasured.

**OFF TRACK — 20% artifact-success forecast, below 25%; correct labels and comparison validation, reuse `off`, evaluate `cf` once, fund matched SFT only if warranted.**

web search: 
exec
/bin/bash -lc "sed -n '1,280p' plan/BACK-ON-TRACK-PLAN.md && sed -n '3820,4090p' plan/LEDGER.md" in /home/bmarti44/stencil-llm
 succeeded in 0ms:
# Stencil: back-on-track research plan (rev 7.1, 2026-09-11)

Rev 6 = Brian's four directions after rev 5: (1) publish the classifier now, publicly, under
the `bmarti44` HF namespace with a descriptive name (section C, Release 0); (2) clean up ALL of
the code, not just changed files (section C, "Code cleanup"); (3) GPU lock wrapper accepted,
but the default becomes concurrent sharing with the looped-transformer session because both
workloads are small (section E, sized from measured memory); (4) execute autonomously, using
Astra to get unstuck (section D rules 9-10, and the open decisions are resolved with defaults).
Rev 5 = Brian's de-over-engineering pass: `wave_static` arm dropped (five arms), verification no
longer promises an impossible historical re-score, Release 2 made concrete as a text-only
`stencil-reminder` package unless Exp 1 says pins matter, and a program-level stop rule added.

Review trail: Astra repo review (NOVEL 3, IMPACT 4, ITERATION 3); Astra plan round 1 on rev 1:
24/100, 34 findings; Astra plan round 2 on rev 3: 80/100 (on-track 9, success 7, rigor 7.5,
novelty 8.5) with four minimum edits, all applied in this rev 4: full-support WHERE
permutation with gain preserved and `fixed_bias` naming; no causal inference from
nonsignificance and breakage limit inside PASS; honest comment-checker qualification instead
of impossible historical re-scoring; FOCUS-3 scope/overflow mapping and non-vacuous adapter
check in the Exp 3a contract plus frozen two-request/three-input selection in Exp 2a.
Astra's success probabilities: Exp 1 75%, Exp 2a 35%, Exp 3 55% (of a clear answer, not of a
positive result). Review files: scratchpad astra-repo-review.md, astra-plan-review.md,
astra-plan-review2.md (to be copied under results/reviews/ once execution starts).

## Rev 7 (2026-09-11, Brian's reframe): one published model artifact, proven against itself

Brian, mid-execution of rev 6: "your goal is to build and publish a model artifact to
huggingface that is able to focus on the relevant instructions for a task over a long horizon
agentic coding session. first you would clean up the repo, and then you would work towards
that. you would need to prove that your artifact outperforms the same artifact without the
modifications." This section supersedes section C's three-release endpoint (Release 0 stays
published; Releases 1 and 2 are replaced by the artifact below). Sections A-B, D-F stay in
force as evidence machinery and process; nothing already registered changes.

Rev 7.1 applies Astra's round-3 review (results/reviews/2026-09-11-plan-rev7-review-astra.md,
54/100, seven minimum edits): one frozen shipping configuration with an explicit session
interface; token-level prompt matching; applicability frozen before generation with a fixed
denominator; the sentence-window identity defect fixed (CONTRACT.md amendment 2); the
fallback frozen with its two-attempt interpretation; a measured, arithmetically correct
budget; and the existing BFCL multi-turn long-context workload registered as the agentic
check (Exp 5). The wave line and KV pins are off the artifact's critical path.

### G. The artifact: one frozen shipping configuration

- Name (descriptive, Brian may rename): `bmarti44/stencil-focus-qwen3-1.7b`. One HuggingFace
  model repo: the frozen Qwen3-1.7B trunk (weights copied; base attribution and revision on
  the card), a `stencil/` package loaded with `trust_remote_code`, and a config flag
  `stencil_focus` (default `true`). The modification is to inference-time session-memory
  handling, not to the trunk's learned weights; the card says so in its first paragraph.
- Session interface (package-owned, the thing Exp 4 evaluates and the thing users call):
  `StencilFocusModel.from_pretrained(repo, stencil_focus=True)` wraps
  `AutoModelForCausalLM`; `session = model.new_session()`; `session.add_message(role, text)`
  for every message of the conversation in order (user/mentor lines feed the register;
  other roles are stored only); `session.build_prompt(request)` returns the exact prompt
  string; `session.generate(request, **kw)` = build + greedy/`generate`; `session.reset()`
  clears state. Session state is isolated per session object.
- Frozen shipping configuration (decided now, not by later experiments; the classifier
  register is an explicitly UNPROVEN maintenance hypothesis for Exp 4: Exp 1 showed the
  role-echo policy beating the classifier-echo policy on Multi-IF, which is a different
  construction, and does not decide the long-session bundle either way):
  0. AMENDED 2026-09-11 before any LONG generation (Exp 4 registration amendment 1): the
     frozen FOCUS-3 register overflows on 138/144 LONG items in the CPU phase and applies
     no relation on SETUP-LONG, so the PRIMARY policy is the zero-parameter role rule over
     the truncated-away region (newest-first mentor sentences outside the window). The
     register below stays in the package as the OPT-IN maintainer with its error table
     and is evaluated descriptively on SETUP-LONG only. There is one primary policy and
     no fallback rerun.
     Amendment 2 (Astra implementation review, same day) fixes the execution matrix
     (48 + 256 + 16 = 320 generations, no SCREEN oracle), the timeout rule, the excess
     formula, completeness and the enforced prompt equality; see REGISTRATION.md.
  1. Register (opt-in): admission by the published sentence classifier
     (`bmarti44/assistant-memory-sentence-classifier`, frozen) and lifecycle relations by
     the frozen relations-v2 seed0 head (`data/classifier/model/relations-v2/seed0`, sha
     recorded on the card), i.e. the FOCUS-3 runtime `src/stencil/focus3.py` as mapped in
     `results/memorycode-derived/CONTRACT.md` (task scope `MAIN`, 4-sentence windows with
     their own turn index per amendment 2, overflow at 16 rows counted and reported).
  2. Rendering: live rows (status live, scope `MAIN` or global, chronological) rendered as
     `Earlier instructions still in force:` + `- <sentence>` lines, newest-first packing,
     budget E = 256 tokens including the header, inserted immediately before the current
     request. The conversation window is truncated at token boundaries so that the COMPLETE
     prompt (window + reminder + request) has the same token count as the unmodified prompt.
  3. Backend: `transformers` only. No KV pins, no attention controller, no hand-rolled
     runtime in the artifact. The research runtime is used only to run the evaluations
     bitwise-deterministically; the parity gate below ties the two together.
  4. Off switch: `stencil_focus=false` → no register is built, no reminder is rendered, the
     window is the plain recency window at the same token budget, decoding identical.
     Nothing else differs. `tests/test_stencil_focus.py` asserts that with the flag off the
     prompt equals the plain window and the outputs equal `AutoModelForCausalLM`.
- Claim shape: the ARTIFACT AS A BUNDLE beats the same artifact with `stencil_focus=false`
  (Brian's criterion). Component-wise ablations are not claimed; Exp 1 and Exp 3c are
  reported as secondary evidence about the register and the echo machinery.
- Registered fallback (frozen now, before any LONG outcome is seen; clarified after Exp 1
  read, still before any Exp 4 generation): if Exp 4 reads NOT PROVEN, the register policy
  is swapped ONCE to the zero-parameter role rule over the TRUNCATED-AWAY region: every
  mentor sentence that lies outside the recency window, newest-first packing, same renderer
  and budget (the analogue of Exp 1's winning `role_echo_only` arm, which restates the
  evicted region; restating the newest sentences of the whole session would duplicate what
  the window already shows) and Exp 4 is rerun on the same items with base outputs reused. Two fixed policies, each tested at one-sided .025, bound
  the family-wise false-positive rate at .05; both attempts are always reported and the
  selected policy's interval is not presented as a simultaneous 95% interval.
- Parity gate before publication (mirrors Release 0's export verification): on the 16
  SETUP-LONG items the published wrapper must render byte-identical prompts to the research
  runtime and produce identical greedy outputs; with `stencil_focus=false` its outputs must
  equal plain `AutoModelForCausalLM`. A clean-environment example (`pip install`, load, one
  long session) is the release gate. No research number is attributed to the artifact until
  parity holds.
- Off the critical path (parked, not cancelled): KV pins (Exp 1 decides whether a later
  Qwen-only backend is worth registering); the attention controller (Exp 2a/2b remain the
  rev 6 method-claim line, run only when the GPU is otherwise idle and never a component
  of this artifact); `deploy/stencil_wave/` is archived.

### H. Exp 4: the proof, a long-horizon coding-session head-to-head (registered before its GPU spend)

- Workload: MemoryCode-derived LONG items. Enumeration on 2026-09-11: 320 candidate
  (dialogue, session) items with history-regex checks and a prior instruction; 108 fit in
  3,584 tokens (Exp 3 uses them) and 212 do not. Verified quantiles (Astra round 3): all
  candidates min 705 / median 8,364 / P90 30,283 / max 61,046 tokens; the LONG set min 3,693
  / median 15,623 / P90 51,734 / max 61,046. W = 3,584 tokens is the IMPOSED evaluation
  budget (the local base config supports 40,960 positions); under that budget the base sees
  only the newest part of the session, which is the condition the artifact exists for.
  Split by dialogue with `random.Random(1)`: 16 SETUP-LONG (pilot + parity), 128 SCREEN-LONG
  (primary), 68 reserve, never opened in this program. One generation per item (the first
  `history_eval_query`), 512-token cap, deadline 300 s.
- Prompt construction (both arms; native single-message format, CONTRACT.md): the thread is
  the conversation text truncated at a token boundary to keep the NEWEST tokens; the
  modified arm's thread is truncated by exactly the reminder's rendered token count so the
  complete prompts have equal token counts (asserted per item and stored in the record).
  Whole-session packing is NOT used (it makes prompts unequal, Astra round 3).
- Arms:
  | arm | prompt |
  |---|---|
  | `base` | `stencil_focus=false`: recency window at W |
  | `focus` | `stencil_focus=true`: register built by the frozen runtime over ALL mentor lines of sessions 0..s−1 (including the truncated-away ones), reminder rendered, window shortened to match |
  | `oracle` | descriptive ceiling on SETUP-LONG only (and on SCREEN-LONG only if the measured budget allows): the label-derived live set through the same renderer and window |
  Label rule, stated precisely: only `oracle` may use gold labels to construct its
  intervention; selection, scoring and the error table read labels. `tests/test_memorycode.py`
  extends its isolation check through the package's own prompt-building path.
- Outcome and checker: STRICT compliance under the vendored official checker with
  applicability FROZEN from the query before generation (CONTRACT.md amendments 3/3b: a
  required parent object that is omitted scores 0.0; the required structure, class or
  function by whole-word match on the query, must be present or the item is strict-FALSE;
  the primary cohort is fixed before generation; no arm's output changes the denominator). Fractional score reported
  alongside. Convention compliance is the outcome; functional correctness is neither
  measured nor claimed.
- Primary estimand: `focus` − `base` on strict compliance, paired by item, N = 128. Exact
  McNemar on discordant items, two-sided p, and the conservative paired interval (separate
  97.5% Clopper-Pearson bounds on b/N and c/N, union bound). Power, stated: the interval is
  wholly positive first at 10 wins / 0 losses; with 10 losses it needs 29 wins; at
  win/loss probabilities .15/.05 the positive-result probability is about 26%, at .25/.05
  about 91%. N = 128 establishes a large benefit, not a modest one.
- Output-failure guard: invalid (no code fence / unparsable), truncated at the cap, and
  degenerate (4-gram repetition) generations counted per arm as EXCESS over `base`.
- Readings (exhaustive):
  - PROVEN: interval entirely above 0 AND `focus` excess output failures ≤ 5% of items →
    publish the artifact with the table.
  - POSITIVE-WITH-OUTPUT-FAILURE-EXCESS: interval above 0 but excess failures > 5% → not
    PROVEN; published as descriptive with the failure table; the fallback is NOT triggered
    (it is a policy revision, not an output-failure fix).
  - NOT PROVEN: interval covers 0 → the frozen fallback (G) runs once; the second reading is
    final.
  - HARM: interval entirely below 0 → published as demonstrated harm; program ends.
  - `oracle` − `focus` on SETUP-LONG is the reported headroom; it gates nothing.
  - The error table (false admissions, missed instruction sessions, overflow events,
    reminder tokens, empty reminders) is published with every reading and is never read as
    evidence of accurate maintenance: activity is not accuracy.
- Budget, measured: Exp 0 pilot family `memorycode-long` = the 4 longest SETUP-LONG windows
  at W = 3,584 with a 512-token generation (the ≤ 3,584 pilot measured 42-86 s/generation at
  2,446-3,002 tokens, 11.7-12 tok/s, 6.5 GB allocated / 8.0 GB reserved). Ceiling =
  1.5 × t_max × (2 × 144 + 16 [oracle on SETUP-LONG] + 128 [the permitted fallback rerun of
  `focus`]) = 1.5 × t_max × 432 generations, plus the 4-generation pilot and the 32-generation
  parity check (16 items × 2 flag states) = 468 generations; at t_max = 100 s that is 19.5
  GPU-h worst case and roughly 7 GPU-h expected (median generations are far below the cap). `oracle` on
  SCREEN-LONG (+128) is added only if t_max ≤ 60 s. The registration records the measured
  t_max, the ceiling, and the expected value from the pilot's mean; chunks ≤ 50 min; atomic
  per-item records; INCOMPLETE is never rescued.

### H2. Exp 5: the agentic check on the existing BFCL multi-turn long-context workload

Brian's goal names an agentic coding session; MemoryCode supplies conversation history with
mentee replies given, one final generation, no tool feedback. The repo already vendors BFCL
v3 multi-turn (`data/bench/bfcl_v3_mt`, 200 items per category incl. `long_context`) with a
runner (`scripts/bfcl_mt.py`, `--mode free` = the model's own tool calls and real tool
feedback drive the episode, `src/stencil/bfcl.py`). Exp 5 = the same `stencil_focus` toggle
on `multi_turn_long_context` in free-running mode: `base` vs `focus`, per-item pass under the
upstream checker, paired exact test and the same interval, N from the pilot budget (target
the full 200 if ≤ 4 GPU-h, else a `random.Random(2)` subset registered before launch).
Registered in `results/bfcl-long-context/REGISTRATION.md` after Exp 4 reads, with its own
pilot and data-lineage line (nothing in the register or classifier was fit on BFCL:
LEDGER-PLAN.md:634 records the lineage). The card says "coding-session instruction
retention" after Exp 4; it may say "agentic coding session" only if Exp 5 is also positive.

### I. Execution order, rev 7.1, and the program stop rule

1. Cleanup first (in progress): full suites on the pre-cleanup tag and on main agree →
   comment-checker fix → invariants → commit → push → archive the closed scripts with
   `archive/scripts/MAP.md`.
2. Secondary evidence already registered and partly running: Exp 1 (chunks 1-2 done/running),
   Exp 3b/3c (register vs restate-all on the ≤ 3,584 items). Their RESULTS.md files go on
   the card as secondary evidence; they do not change G's frozen configuration.
3. Exp 4: registration (`results/memorycode-long/REGISTRATION.md`, items.json with the seed-1
   split, pilot budget) → run → RESULTS.md → Astra result audit → fallback once if NOT PROVEN.
4. Packaging: `deploy/stencil_focus/` (replaces the archived `deploy/stencil_wave/`), parity
   gate on SETUP-LONG, card with the Exp 4 table, the error table and the secondary
   evidence; push under `bmarti44/`. Release 0's card gains a pointer.
5. Exp 5 registration → pilot → run → RESULTS.md → card upgraded to "agentic" only on a
   positive reading.
6. Only then, if GPU time is idle: Exp 2a (+2b) as the rev 6 method-claim line, research
   artifact only.
Stop rule: PROVEN publishes; NOT PROVEN allows exactly the one frozen fallback and then
publishes whatever the second run says (a second null is a published negative with the
artifact withheld as a claim); HARM publishes the negative. No new arms, workloads, or
components enter without a new registration.

### J. Rev 7.2 (2026-09-12): Exp 4B, the same head-to-head on the Qwen3-4B trunk

Exp 4's SETUP-LONG at 1.7B read a strict floor under a corrected oracle (0/16 on every arm;
per-constraint focus − base −5.2 points [−10.6, −0.4], descriptive, n = 16), so the 128-item
SCREEN at 1.7B was deliberately not run and is reported as "primary not run". Brian chose
the most likely direction from `results/reviews/2026-09-12-options-memo.md`: the SAME
mechanism and control on the Qwen3-4B trunk with a per-constraint primary. Registered as a
NEW registration, `results/memorycode-long/REGISTRATION-4B.md` (rule D9), consuming the
program's second and last policy revision (rule D2): artifact `bmarti44/stencil-focus-
qwen3-4b`; primary = `fraction_required` (denominator frozen from the query's required
families, structure gate), paired focus − base, 95% percentile bootstrap (seed 0, 10,000
draws) + exact sign test, N = 128 SCREEN-LONG; strict alongside; qualification gate on
SETUP-LONG 4B (oracle mean ≥ 0.20, focus-only failure excess ≤ 5%, focus − base upper
bound > 0) before any SCREEN spend; exhaustive readings PROVEN / POSITIVE-WITH-OUTPUT-
FAILURE-EXCESS / NOT PROVEN (final) / HARM / INCOMPLETE. Everything else in G-H is inherited
unchanged. Section I step 3 continues with Exp 4B; step 4's parity gate and card move to
the 4B artifact; the 1.7B SETUP-LONG result is published as a descriptive negative.

### K. Rev 7.3 (2026-09-12): Exp 4C, the Astra-authorized final confirmation, and program close

Exp 4B's qualification FAILED its output-failure gate (one focus-only unparsable output among
16). Brian delegated the D2-override decision to an open-brief Astra consult; its binding
decision (`results/reviews/2026-09-12-unblock-decision-open-astra.md`) authorized ONE final
confirmation, `results/memorycode-long/REGISTRATION-4C.md`: generation through the shipping
package (research-runtime parity had failed), the 128 SCREEN dialogues plus reserve up to
196 under a timing-only N rule, paired-t primary on `fraction_required`, +5-point failure
noninferiority, HF push only on PROVEN-SCOPED after an Astra audit and a clean-environment
reproduction. Astra's implementation review blocked ten findings; all were closed before
launch. Qualification passed (16/16 plain matches, 8/8 replays, t_max 68.7 s → N = 139).
Terminal reading (`RESULTS-4C.md`): **NOT PROVEN, FINAL**, off 0.0845 → on 0.1049, +2.05
points, 95% [−0.07, +4.16], p = .058, 25/17/97, failures 60 vs 61 (guard also not met).
Program outcome: the artifact `bmarti44/stencil-focus-qwen3-4b` stays repo-only with the
table on its card; nothing is pushed to HuggingFace; no further revision is permitted. Owner
rule from 16:50Z, binding on future registrations: interim results may be inspected; early
stop only for futility; a positive claim still needs the full registered N.

## Context

Brian asked for an audit of the Stencil repo: what has actually been proven, whether the
"does not work" claims hold up, what is missing for an honest HuggingFace release, what the
2024-2026 literature already covers, and what experiment would prove something
mechanically interesting. Three read-only audits (positive results, negative results,
engineering/HF readiness), a web-literature pass, an adversarial Astra (gpt-6-astra, xhigh)
review of the repo, and an adversarial Astra review of rev 1 of this plan (24/100, 34
findings) were run. Rev 3 incorporates the findings that add validity and declines the ones
that add machinery without changing a decision (listed at the end). A second researcher
(session "looped-transformer") shares the GB10; the GPU protocol is in section E. Brian's
acceptance criteria for round 2: on track, decent chance of success, aligned with rigorous
published work, novel; over-engineering is a defect.

## Findings (established by the audits; file references are repo-relative)

### What is proven, and how strong it is

| Result | Trunk / data | Numbers | Strength | Gaps |
|---|---|---|---|---|
| Leg B retention under eviction | Qwen3-1.7B, Multi-IF 909 conv = 484 distinct source prompts (public) | full 65.2, evicted 16.7, clf pin-only 57.2, clf pin+echo 59.2, role pin 60.5 (pooled); C1/C3 p~3.7e-85/1.6e-65 conversation-clustered; C2 FAIL: role rule beats trained selector by 3.5 (conv-mean) / 3.3 (pooled) | Only public-benchmark result; 911/911 evidence files tracked | Echo increment given pins IS identified (+2.0); pin-only vs eviction IS identified (83.6% recovery); the pin increment GIVEN echo is not (no echo-only arm); 909 conversations are 425 pairs + 59 singletons sharing first prompts, so clustering must be by source; encoder weights gitignored; registered NOT SUPPORTED on 1 invalid output vs 0 |
| Internal wave | Qwen3-1.7B, synthetic coding sessions, n=96 | 264k-param controller, adherence 25.2->44.8; hand oracle 38.3, proxy 37.4, prose reinsertion 43.0 (+1.7 pts; reinsertion broke 30 works vs 21) | The one plausible method novelty: a learned per-step positional pre-softmax bias field trained through the frozen attention path, with WHERE/WHEN/selectivity ablations | 1 seed, no p-value; the harness re-serializes the generator's exact current ledger every request (src/stencil/t2_sessions.py:295), so it tests attention allocation GIVEN a correct external ledger; W3b readout found the field NOT decodable as "the governing rule now"; w0-ce reduced MMLU 48.05->45.83 and failed GSM8K noninferiority (WORKLOG.md:1586,1613); **the comment-type 0/120 "null" is a checker bug**: `src/stencil/t2_runner.py:91-94` requires the last line of `ast.get_source_segment(code, fn)` to be `# reviewed`, but a function's AST segment ends at its last statement and excludes a trailing comment, and `wave_ref.py:29` generates exactly that form; controller reduces to learned query-key matching plus a scalar gain (wave.py:29); w0-ce.pt untracked |
| SELECTOR | Qwen3-1.7B, synthetic named-query task, N=32, n=128 (5/128 vs 113/128) | 3.9 -> 88.3; reinsertion 84 @ 504 tok from a different block | Clean actuator test, bitwise zero-identity | Task is `current[field]` lookup with the field named (results/selector-review-sol.md:80-88); no retrieval or LoRA baseline; evidence JSON + weights untracked |
| GPT-2 focus cache | GPT-2 small, windowed attention | 100 vs 4.3 zeroed; transplant 28/32 | Clean construction | Gap guaranteed by construction; results/gpt2 0 tracked files |
| larger-test-v2 | Qwen3-30B-A3B, 64 authored episodes | register vs none: delivery 35/0/28 p=3e-11 | Rigorous stats | Prose reminder T ties/beats register on every family; R loses semantic integration 45 vs 52 (p=.0078) |
| FOCUS-3 v8 diagnostic | Qwen3-4B, 64 reused-template episodes | automatic register 57/64 vs none 29/64 vs oracle 63/64 | Encouraging for AUTOMATIC maintenance (Brian's corrected goal) | No verdict assigned; 25 false admissions in 21 episodes are policy failures, not instrument accidents; templates reused |
| W3a | Qwen3-1.7B synthetic, 96 sessions | wave 55.1 vs reinsertion 53.1 vs base 36.6, zero contamination | Qualified clean-format positive | Generalizes to ONE registered unseen rendering only |
| W3 README bullet | | "+42 pts, 73/73 never wrong" | **Misrepresents two FAILED gates** (WORKLOG.md:1326-1337, results/w3-results-sol.md) | Must be rewritten; the W3b readout failure is itself informative |

Cross-cutting, stated precisely: correct request-time restatement of the current rules is the
baseline to beat. No mechanism tried so far has beaten it by more than ~2 points (wave +1.7,
W3a +2.0) and several lost to it (FOCUS-2d 143/256 vs 176/256; larger-test-v2). C2 says nothing
2026-09-12 11:00Z — Exp 4B pilot done (results/timing-pilot/memorycode-long-4b.json, GPU idle, 2.6 min): t_max 47.6 s,
mean 38.5 s, 10.7 tok/s, peak 9.14/9.66 GB. BUDGET line appended to REGISTRATION-4B.md: 71.5 s/gen, ceiling 6.0 GPU-h
(304 gens), SCREEN INCOMPLETE above 18,294 s. Astra implementation review running
(results/reviews/2026-09-12-exp4b-impl-review-astra.md); SETUP-LONG 4B launches only after its required edits.

2026-09-12 11:45Z — Astra Exp 4B implementation review: BLOCK, 9 findings
(results/reviews/2026-09-12-exp4b-impl-review-astra.md). All applied as REGISTRATION-4B.md AMENDMENT 1 + code:
fraction_required validates input and is documented as equal weight per regex check; empty/unequal bootstrap handled;
fraction reading confirmatory only for model 4b and never with lower=None; record validity (manifest model/window/
budget + terminal scored generations) → invalid_record_ids → INCOMPLETE; registered N enforced (items_scored ==
frozen); timeouts score 0.0 on the primary in run and recompute; `run --ceiling-seconds` cumulative across chunks +
BUDGET_EXHAUSTED.json + summarize reads INCOMPLETE; qualification object (PASSED/FAILED/INCOMPLETE) on setup_long;
_record_matches compares window + budget_tokens; pilot units labelled GiB; reservation 32 GB (fp32 construction
peak ≈ 24 GB on unified memory). Disclosures added (first-query restriction, oracle threshold chosen after the
descriptive 4B short numbers, 314-49 focus regeneration, precise label-use wording — this corrects the shorthand
"only oracle reads labels" in the 05:10Z entry). Tests 44 pass; the 1.7B SETUP-LONG records re-summarize
identically (16/16 valid, −5.17 [−10.56, −0.43]). Launching SETUP-LONG 4B: 48 generations, ceiling
3,430.1946394080296 s, reservation stencil-exp4b-setup-N 55 min / 32 GB, --budget-minutes 50.

2026-09-12 11:55Z — STATE: EXP 4B QUALIFICATION FAILED; PROGRAM AT ITS REGISTERED STOP (Brian decision needed).
SETUP-LONG 4B (setup_long-4b-role_evicted/, 48 gens, one slice, 1,187 s of 3,430 s ceiling, 16/16 valid, 0
timeouts, prompts equal): fraction_required base .066 / focus .109 / oracle .263; focus − base +4.3 [+0.1, +9.5]
4W/1L/11T; oracle − base +19.7 [+7.8, +33.1]; strict 0/16 all arms. Qualification: (a) oracle ≥ .20 PASS, (b)
focus-only failure excess 1/16 = .0625 > .05 FAIL (item 184-14 unparsable; base-only failure on 186-14; net 0),
(c) upper > 0 PASS → status FAILED. By REGISTRATION-4B.md item 3 the SCREEN-LONG run is NOT opened and the
program stops; this was the second and last policy revision (rule D2). RESULTS-4B.md written (descriptive).
Artifact bmarti44/stencil-focus-qwen3-4b is NOT PROVEN, withheld as a claim, not pushed. Astra result audit
launched (rule D1). GPU idle; peer informed. Open for Brian: (1) accept the stop and publish the negative (default,
nothing further runs); (2) authorize a THIRD revision as a new registration (e.g. net-excess or interval-based
failure gate at n = 16) — outside the orchestrator's authority under D2; (3) publish the package descriptively
with no claim.

2026-09-12 12:20Z — Astra result audit of Exp 4B (results/reviews/2026-09-12-exp4b-result-audit-astra.md): all 48
generations and every statistic REPRODUCE; FAILED on (b) confirmed; 8 corrections applied to RESULTS-4B.md (check
denominators 3..32 per item with equal weight per check; oracle packing 8 complete / 8 clipped; total generation
time 1,788 s vs the three-arm 3,430 s ceiling, base/focus subtotal 1,187 s; McNemar p = 1 and strict interval
±24.0 instead of "undefined"; D3 distinction stated; cross-model sentence made descriptive; D2 override wording;
manifest-4b.json and parity disclosed as not done). Code: summarize now counts the run's arms against the ceiling
(audit finding 3); the SCREEN launch guard is committed as tools/exp4b_screen_launch.sh (never invoked). Tests 44
pass. Next-path consult running (2026-09-12-next-path-consult-astra.md) per Brian's request.

2026-09-12 12:50Z — Astra next-path consult (results/reviews/2026-09-12-next-path-consult-astra.md), requested by
Brian. Recommendation: ONE final owner-authorized confirmation of the UNCHANGED 4B artifact on the frozen 128-item
SCREEN-LONG (same role_evicted / W / E / decoding / items / per-constraint estimand), with the output-failure
guard moved from a SETUP launch gate to a final-sample paired NET-excess interval with an affirmative ≤ 5-point
noninferiority requirement, and the primary decision moved to a paired-mean t interval (bootstrap + sign test
reported as companions). Judged 20-35% chance of a scoped PROVEN (coding-session retention claim only; agentic
claim still needs Exp 5); cost 3.2 GPU-h expected / 5.7 allowance. Limiting factor: the noninferiority guard has
≈34% chance of certifying at N = 128 even with zero true net harm (s_H = .365). Requires Brian's explicit override
of rule D2 and a fully disclosed outcome-informed new registration (draft disclosure paragraph in the consult).
Alternatives ranked below it: sparse authored workload 15-30%, +linter repair 10-25%, relevance ranking 10-20%,
output-contract change 5-15%, attention bias 5-15%, pass@8 (no proof value), gate reinterpretation 0%, RLVR < 5%.
Astra: publishing the negative and ending the line is an honest complete outcome and remains the default. GPU
idle; nothing launches until Brian decides.

2026-09-12 12:35Z — Publication plumbing for the 4B artifact (no HF push; nothing decided): hub build assembled
(deploy/stencil_focus/build/hub-4b, 7.6 GB, dry-run; assembler now globs shards and takes --card), MODEL_CARD-4b.md
(NOT PROVEN, descriptive tables only), manifest-4b.json (16 record sha256s). Parity run (parity_generate.py
--records setup_long-4b-role_evicted, reservation stencil-exp4b-parity, 20 min): prompts byte-identical 32/32;
off switch exact 16/16 (package flag-off == plain AutoModelForCausalLM); greedy generation parity vs the research
runtime 0/32 token-identical (7/32 text-identical). The research (hand-rolled, bitwise-deterministic) runtime and
transformers bf16 diverge in greedy paths on 3.6k-token prompts; this is the first generation-parity measurement
in the program (the 1.7B parity ran only its CPU prompt half). Consequence under G's parity gate: no research
number is attributable to the artifact; any publication must either reproduce the evaluation through the
package's transformers path (new GPU spend, a registration matter) or carry the card's explicit disclaimer. GPU
idle; peer informed. STATE unchanged: awaiting Brian's decision (accept stop / override D2 for one final SCREEN
confirmation / publish descriptively).

2026-09-12 12:50Z — REGISTRATION-4C-DRAFT.md written (NOT in force): Astra's recommended final confirmation of the
unchanged 4B artifact on the 128 frozen SCREEN-LONG items, generated THROUGH THE PACKAGE (transformers path) so
parity holds by construction; paired-mean t primary on fraction_required, net output-failure interval with an
affirmative ≤ +5-point noninferiority requirement; disclosure paragraph adopted verbatim. Becomes a registration
only on Brian's explicit D2 override (rename + quote the override in its header) and after an Astra implementation
review. STATE unchanged: blocked on Brian's decision (accept stop / override D2 → Exp 4C / publish descriptively).

2026-09-12 13:20Z — Brian: "use astra to unblock you, go with its deep web research result decision." The owner has
delegated the D2-override / publication decision to an Astra consult with deep web research
(results/reviews/2026-09-12-unblock-decision-astra-prompt.md). Its pick among {Exp 4C as drafted, a modified
confirmation with published support, descriptive HF publish, repo-only negative} is binding on the orchestrator;
the ledger will quote the decision verbatim before any launch or push.

2026-09-12 13:30Z — Brian: "why limit astra to the four decisions? let it bring forward its own decisions as well."
Prompt reopened (the four options are reference only; Astra may propose anything within the constraints) and
relaunched as results/reviews/2026-09-12-unblock-decision-open-astra.md — THIS run is the binding one. The first,
option-restricted run could not be stopped (pid guard) and finishes harmlessly as
2026-09-12-unblock-decision-astra.md; it is advisory only.

2026-09-12 14:05Z — BINDING ASTRA DECISION (results/reviews/2026-09-12-unblock-decision-open-astra.md, open brief, owner-
delegated), quoted verbatim: "DECISION: Authorize one final confirmation of the unchanged Qwen3-4B package, expanding
the frozen 128-item SCREEN with reserve dialogues up to 196 pairs under a timing-only sample-size rule, retaining
affirmative +5-point output-failure noninferiority, and publishing the HF model only if every registered gate
passes." It exercises Brian's delegated D2 override ONCE, opens the reserve prospectively (candidate order = seed-1
dialogue shuffle minus the 16 SETUP dialogues; first 128 must reproduce SCREEN), replaces research-runtime parity
with direct shipping-package evaluation + qualification (44 generations: 8 timing calls, 12 more off outputs, 16
plain-model matches, 8 package replays), N = min(196, floor(28800 / (3 t_max))) with INELIGIBLE below 128, paired-t
primary on fraction_required, failure guard U_H ≤ 0.05, exhaustive readings table (§5), budget ≤ 10 GPU-h and 3
working days, one focused Astra implementation review of the NEW runner/analysis/sample-size/publication paths,
one result audit, HF push only on PROVEN-SCOPED. Exp 4B remains FAILED / NOT PROVEN. The option-restricted
advisory run (2026-09-12-unblock-decision-astra.md) reached the same shape with a +10 guard on 128 items; the open
run governs. Executing: registration (REGISTRATION-4C.md) → CPU implementation + tests → Astra review →
qualification → freeze N → evaluation → summarize once → audit → publication gate.

2026-09-12 16:40Z — Exp 4C implementation review (results/reviews/2026-09-12-exp4c-impl-review-astra.md): BLOCK,
ten findings (nine high). All ten closed before any GPU launch (closure record appended to the review file):
effective-EOS freeze, per-call qualification receipts + sequential model release, heartbeat receipts + owned-process
watchdog with pre-call allowance checks, durable raw outputs with attempt-log accounting, qualification-only freeze
with a verified chain (runner/wrapper/summary), strict per-arm fingerprints, consistency-checked + re-scored records
with finite-statistics requirement, exactly-constant-difference Hoeffding fallback, a gated release consumer +
clean-environment verification, checker hashes + reminder source offsets (registration wording restored).
tests/test_memorycode_4c.py: 16 pass. Conservative readings recorded: a call may start only if cumulative
generation spending + deadline ≤ 3 t_max N; verification resident time is the clean-venv process (the venv build
is not GPU-resident). Next: qualification launch (44 generations, receipts), freeze, evaluation.

2026-09-12 17:00Z — Exp 4C qualification COMPLETE and ELIGIBLE (results/memorycode-long/qualification-4c.json, 44 receipts
under qualification-4c/): plain-model matches 16/16 (prompt ids + raw), package replays 8/8 (prompt bytes + ids + raw),
fingerprints equal, effective EOS [151645], resident 2,749 s of 3,600 (two processes: the first stopped cleanly at its
slice limit after 42 calls, the second resumed the last two replays). t_max = 68.689 s (351-99 focus, cap; measured with
the peer's 1.7B training co-resident, as the registration allows). Timing rule: N = floor(28800 / (3 × 68.689)) = 139.
FROZEN: items-4c.json, N = 139, frozen-ids sha eb37a6a1bdccbe3c1e752baf8ddf31a53d0f1268d59a9f633d539107cbe51546,
qualification sha ea38a9178dac8322…, ceiling 3 t_max N = 28,643 s, chain verified. WRITE-AHEAD: launching the single
evaluation via tools/exp4c_eval_launch.sh (55-min reservations, 3,000 s per-process limit, no interim efficacy look).
- 2026-09-13 12:15Z (dating: the four entries above are stamped 2026-09-14 in error; `git log` dates every one of them 2026-09-13, and this entry uses the true clock) — Astra re-review **round 8** (`results/reviews/2026-09-14-a-screen-rereview7-astra.md`) read **DO NOT LAUNCH**: "an undercharged death observation, gate readings on incomplete records, and a demonstrated false session success." Three items, all reproduced before any change, then fixed + registration **amendment 8** (§20), AUTHORING **amendment 6**. This is the first amendment that changes POOL FILES, so the SCREEN pool is re-frozen. **The false J = 1 (high) is the one that matters:** adding `self._n = 0` to `OrderBook.collect` in S35 passed every suite at BOTH checkpoints while `place → collect → place` reissued a live order id and the second order overwrote the first. The audit's class-7 write detector was a regex over each method's OWN body, and `collect` assigns nothing — it stores through `self.save(updated)` — so it read as a pure reader and was never mutated. `state_writers()` closes the writer set over calls to other methods of `self` to a fixed point (a caller of a writer is a writer): a strict superset, +6 mutants pool-wide (961 → 967), all six UNDETECTED on the pool as frozen at `e1329095` — S35@1/@2 `ready` and `collect`, S08@2 `import_results`, S10@2 `load_feed`. Four create-after-operation fixtures close them (create, run the operation, create again, assert the new id is not a live one AND the earlier record still resolves with its own values) in S08 `_C2_FUNCTIONAL`, S10 `_C2_FUNCTIONAL`, S35 `_C1_FUNCTIONAL` and `_C1_REGRESSION`; S35 needs no checkpoint-2 fixture because request 1's functional and regression suites re-run at checkpoint 2 as `protected_function`. **A second false J = 1, found here rather than by the reviewer (§20.4):** the finding is about a boundary, so the same question was asked of a receiver other than `self` — `refund(book, order_id, reason)` is S35's checkpoint-2 gold, lives in another module, stores through `book.save(...)`, and `book._n = 0` at its top passed every suite. Class 7b (`project_classes` + `handle_allocator_mutants`) mutates through any handle a function writes a counter-owning store with; the receiver's class must RESOLVE first (parameter annotation, else the unique project class whose methods cover every method called on the name) because an unresolved receiver yields a no-op that reports a FAKE escape — S31's `join_club(roll: MemberRoll, ...)` calls `roll.add`, but `MemberRoll` owns no counter. 35 class-7b mutations in eleven slot-checkpoints, 0 unresolved receivers, exactly one escape (`refund`), closed by an S35 `_C2_FUNCTIONAL` fixture. A probe that ignored the audit's own path rule reported four more; none survives — two are the `MemberRoll` no-op, and the other two sit in request 2's target file at CHECKPOINT 1, where only request 1's target carries a reply, while at checkpoint 2 class 7b generates both and the suites detect both. **Fairness checked in the other direction (§20.5):** four alternative replies that implement the registered requests faithfully but differ in construction (`collect` and `refund` building a record field by field instead of `replace`, `import_results` as an index loop, `load_feed` doing read/parse/store itself instead of delegating) score EVERY suite — 4 alternatives, 0 rejected. **The observation was backdated (F13):** the runner sampled `now` once and passed it in, so a process descheduled between the sample and the pid probe wrote an observation timestamped before its own death — Astra's scenario (read at 300 s, death at 900, probe at 1,000) permanently charged 300 s, and beside 2,400 s of work that reads `GATE PASSED` at 45 charged minutes against 55 spent. `ledger_observe` now takes a `clock` and samples it AFTER each successful probe; the same scenario writes `t = 1000.0, elapsed_s = 1000.0` and charges 1,000 s, and a read at 5,000 s still charges 1,000 s. **Incomplete records bypassed the short circuit (F12):** dropping S48@2 from the CF arm printed all twelve gate lines and `provisional: GATE PASSED`, because `missing` only rewrote the verdict after the gates were computed. Incompleteness now takes the same short circuit as ineligibility — a `## Not analysable (rounds 6-8 F12)` block naming every reason, then the verdict, then stop — verified at zero gate lines, with the complete control still printing twelve and `GATE PASSED`, and an `assert not missing and not ineligible` guarding the gate reading. Clean-tree verification: audit **1,002/0, 0 unresolved**, rename **108/0**, containment **0 violations with NO authorizations** (3 slots differing, 45 untouched; the two changed fields are the containment-exempt ones, so request text, gold, project files, contract and support suites and prefix turns are byte-identical to `e1329095`), **477 passed / 1 xfailed** (spend tests 26 → **28**), ruff and format clean, 897 files. Pools: SCREEN **re-frozen** `fa633cceefe47562` → `ef802ce2160ee00c` (zero problems, 48 slots); TRAIN unchanged `b8f504494a281858`; no arm has run, so no record carries the old hash. No arm, model, outcome unit, gate, statistic or ceiling changed. STATE: Astra **round 9** launching (`results/reviews/2026-09-14-a-screen-rereview8-astra-prompt.md`); no GPU work until it reads LAUNCH, then timing pilot (`--longest 4`, three arms per §8) → notify peer "looped-transformer" → train sft then cf (4 h each) → run 3 × 48 → summary → result audit. GB10 is free as of 11:03Z (peer's pilot stopped on a Kimi credit outage, not on GPU contention; they expect an ~8 h / 40 GB relaunch, possibly this evening).

- 2026-09-13 13:05Z — Astra re-review **round 9** (`results/reviews/2026-09-14-a-screen-rereview8-astra.md`) read **DO NOT LAUNCH** with two HIGH findings, both reproduced before any change; fixed + registration **amendment 9** (§21), AUTHORING **amendment 7**. **(1) Alias writes escaped the allocator audit.** `account = self._accounts[id]; account["tokens"] -= n` changes stored state without assigning through `self` and without calling another writer, so class 7's writer test skipped it: 13 mutations across S34 (`top_up`, `spend`, `close_account`), S36 (`log_hours`, `set_role`, `retire`) and S37 (`set_threshold`, `decommission`) passed every applicable suite — 13/13 reproduced. **The repair is a removal, not a fourth widening.** The same detector was too narrow in rounds 4, 8 and 9, and the reason it kept being too narrow is that it encoded a PLAUSIBILITY claim ("a reply would not clobber a counter inside a pure reader") inside the instrument meant to measure the thing. Measured instead of argued: with the writer test deleted from classes 7 and 7b the pool yields **340** allocator mutations instead of 255 and **85 of the extra 85 escape**, so the narrowing separated tested code from untested code, not plausible damage from implausible damage. `state_writers()` is deleted with it. What remains in class 7b is TYPING — parameter annotation, the annotation or initialiser of a `self.<attr>` receiver, else the unique project class whose methods cover every method called on the name; a parameter annotated as a counter-owning class is a handle even when only read; anything untypable is UNRESOLVED, and the pool reports none. Shipped rule: **311 allocator mutations, 0 undetected**; the 29 the throwaway measurement generated and the shipped rule does not are `_counter = 0` on a `dict` (AttributeError — a detection that detects nothing), and a coverage check confirms all 85 escapes are still generated. **Coverage comes from one generic fixture in 23 slots:** `test_no_public_call_disturbs_the_id_allocator` in each slot's checkpoint-1 `regression_tests` (re-run at checkpoint 2 as `protected_function`), which creates a record, walks EVERY module of the package with `pkgutil.walk_packages`, constructs an instance of every class they define, calls every public callable of all of them with arguments naming no existing record, then creates again. **Three drafting traps, every one found by RUNNING the fixture rather than by reading it:** (1) the junk loop can consume the reissued id ITSELF (`close_account` sorts before `open_account` in `dir()`, so the loop's own junk create minted `A1` again and the reader found *a* record under `A1` — 2 of 13 still escaped), closed by deep-copying the first record before the loop and asserting the reader returns THAT record; (2) "every public callable of the package" first meant only the store and the modules its own imports named, and the full audit found `S11@2`'s `InvoiceArchive.invoice_archive(store, number_text)` — a METHOD of a second class in a second module — still escaping at **1 undetected of 1,155**, which is what the package walk closes; (3) four slots need `tmp_path` for a path constructor while S12's creator is the naming family's own target, resolved with `getattr(_x, "book_room", None) or getattr(_x, "room_book", None)`. Cost, because the per-arm ceiling derives from it: A/B on five slots gives +7/+6/+3/−4/−4 ms against a 0.13 s pytest invocation, so §16.7's `SUITE_COST_S = 0.189`, `arm_budget_min() = 47.27` and the 50-minute ceiling are unchanged. **(2) Wall-clock accounting.** Every duration in the spend ledger was `time.time()` arithmetic: a 600 s backward step at real second 360 charged a 900 s launch **300 s** (reading `GATE PASSED: 45 charged, 55 elapsed`), and a 600 s forward step made a legitimate 45-minute run charge 55 and report INCOMPLETE. Realtime now does exactly two jobs — the calendar stamp and the launch id. `ledger_mark` writes a monotonic `m` and the kernel `boot_id`; `ledger_observe` takes a `clock` and a separate `wall` and calls the clock exactly once, after the probe; `ledger_charges` spans a live launch from the earliest `m` of the same boot and falls back to realtime only cross-boot or for legacy records; `scripts/a_screen_run.py` takes every duration from `time.monotonic()`. Verified end to end: no adjustment → 900 s; backward → 900 s; forward, 2,700 s real → 45.0 min. `test_no_duration_is_measured_on_the_wall_clock` scans the three files for a `time.time()` adjacent to a subtraction. **Fairness (§21.4), mechanical over all 23 slots at both checkpoints:** every callable the reply ADDS keeps its name, signature and behaviour while its body moves to a module-level delegate reaching the store through a handle (moved, not rewritten, so a failure means a suite reads the gold's structure rather than the request); run with a private delegate and again with a public one that the fixture's junk loop then calls — **46 alternatives, 0 rejected** each time; plus four hand-written alternatives that differ in record identity, validation order, exception message and idempotence (S34@1 `spend` replacing the stored dict, S04@1 `permit_revoke` rebuilding the record, S17@1 `record_mark` validating against a locally built set, S38@1 `admit` journalling first and idempotent) — **4 more, 0 rejected** — because the mechanical check preserves behaviour exactly and so cannot probe the behavioural axis. Clean-tree verification: audit **1,155 mutations, 0 undetected, 0 unresolved sites (844 from classes 1-6, 275 from class 7, 36 from class 7b; 131 update sites typed)**, rename **108/0**, containment **0 violations with NO authorizations** (23 slots differing, 25 untouched; the two changed fields are the containment-exempt ones), **481 passed / 1 xfailed (spend tests 28 -> 32)**, ruff and format clean, 897 files. Pools: SCREEN **re-frozen** `ef802ce2160ee00c` → `7789e34aec0e9b55` (zero problems, 48 slots); TRAIN unchanged `b8f504494a281858`; no arm has run. No arm, model, outcome unit, gate, statistic or ceiling changed. STATE: Astra **round 10** launching (`results/reviews/2026-09-13-a-screen-rereview9-astra-prompt.md`); no GPU work until it reads LAUNCH, then timing pilot (`--longest 4`, three arms per §8) → notify peer "looped-transformer" → train sft then cf (4 h each) → run 3 × 48 → summary → result audit.

- 2026-09-13 14:10Z — **The review loop is over; the experiment runs.** Brian, mid-turn: "don't do
  pre-registration, don't over-engineer - we need to quickly and accurately work on everything...
  you don't have to be academically rigorous in any of this until we actually have something that
  we think works and now we want to prove." Ten adversarial rounds on a screen that has never run a
  single generation is the amendment spiral AGENTS.md names, and the orchestrator is supposed to be
  the terminator. Acting on that:
  - **Round-10 finding 2 fixed by deletion.** Astra demonstrated the generic fixture
    `test_no_public_call_disturbs_the_id_allocator` REJECTS a correct reply: a behaviour-preserving
    `initialize_bank(bank, accounts)` constructor refactor makes the fixture call it with a junk
    string and the suite then fails (`_initialize_bank` passes) — a false J = 0 in 23 of 48 slots.
    The fixture was added in round 9 only to argue audit coverage; it is reverted out of all 23
    slots (`git checkout eecde769^ -- src/stencil/a_screen_pool/`). SCREEN pool back to
    **ef802ce2160ee00c**. The per-operation create-after-operation tests of amendment 6 stay.
  - **Round-10 findings 3 and 4 kept** (monotonic durations in `a_screen.py`, `a_screen_run.py`,
    `a_screen_train.py`; unbounded cross-boot launches refused): those make budget accounting WRONG,
    they are cheap, and they are already written and tested.
  - **Round-10 finding 1 dropped for now.** It says the mutation audit under-tests my suites for
    resets placed below a lookup. That is a sensitivity property of the instrument, not a bias: it
    applies identically to `off`, `sft` and `cf`, so it cannot manufacture a difference between
    arms. It is a thing to fix if and when there is a positive result worth proving.
  - No amendment 10, no round-11 prompt, no re-registration. The registration stands as written and
    the deltas above are recorded here instead.
STATE: running the candidate-A screen. SCREEN pool ef802ce2160ee00c, TRAIN b8f504494a281858.
Order: gold check + trainer/runner smoke -> timing pilot (`--longest 4`) -> notify peer
"looped-transformer" -> train sft then cf (4 h each) -> run 3 x 48 -> summary. Peer holds the GB10
until ~17:30Z (notasearch-luna-pool1, 40 GB of 119); Stencil peaks 8-15 GB, so we share.

- 2026-09-13 16:10Z — **PRE-COMMITTED STOP RULE for the candidate-A screen** (Brian: "if it looks
  like the numbers are not going our way, let's pause the GPU work... I'd like to run something
  else on GPU if this is not going in a good direction"). Written BEFORE the first adapter number
  exists so it cannot be rationalised afterwards.
  - **Primary measure**: replies satisfying the contract IN FORCE at request 2 of the 36 sessions
    whose convention CHANGED. Baseline `off` = **11/36 in-force, 12/36 stale, 13/36 neither**.
  - **Decision point**: when `cf` training ends (~19:15Z) it is evaluated on all 48 sessions
    (~62 min). That yields `off` vs `cf` at ~20:20Z, which is a valid FUTILITY screen even though
    it cannot isolate the objective: `cf` contains ordinary supervised training, so if `cf` does
    not beat `off`, `sft` will not either and the direction is dead.
  - **CONTINUE** to `sft` only if `cf` reaches **>= 16/36 in-force** (a lift of +5 or more).
  - **PAUSE GPU** if `cf` <= 13/36 (a lift of +2 or less, inside noise at this n): release the
    GB10 for Brian's other work, tell the peer, and carry on with Astra reviews on CPU only.
  - **14-15/36 is the ambiguous band**: report the number and the McNemar discordance to Brian
    with a recommendation, do not decide unilaterally.
  - Earlier warning, free: the training margin. `+0.6368` at step 10 says the preference term
    separates the in-force gold from the stale one. A collapse toward 0 or a negative trend is
    reported immediately as a bad sign.

- 2026-09-13 18:20Z — **GPU PAUSED after cf training, by Brian** ("you can let this run finish and
  then pause using more GPU"). The `cf` allocation is allowed to complete; nothing further
  launches. The GB10 goes to the peer session and to whatever Brian wants to run.
  - **DONE and on disk**: the `off` baseline over all 48 sessions
    (`results/a-screen/runs/off-oldrunner.jsonl`, J=6, function-only=15, 61.6 min, COMPLETE) and
    the `cf` adapter (`results/a-screen/adapters/cf/`).
  - **NOT done**: the `cf` evaluation, `sft` training, the `sft` evaluation, and the `off` re-run
    on the fixed runner. So there is NO adapter-vs-baseline number yet, and the pre-committed
    stop rule above has not been evaluated. Nothing about the direction is settled either way.
  - **Resume needs 4 GPU steps, in this order** (~4.5 h total at an uncontended rate):
    1. `off` re-run on the current runner (~62 min) so all arms share one `runner_sha256`;
       `off-oldrunner.jsonl` was produced before the eligibility-guard fix and its identity
       differs by that one hunk.
    2. `cf` eval: `a_screen_run.py --arm cf --adapter results/a-screen/adapters/cf` (~62 min).
       THIS IS THE FUTILITY SCREEN -- apply the stop rule above before spending anything more.
    3. `sft` training matched to cf's achieved step count via `--max-steps` (~1.5-2 h).
    4. `sft` eval with `--require-steps <cf steps>` (~62 min).
  - **Before each eval** run the CPU preflight
    (`scratchpad/preflight.py <adapter> [steps]`, and `--compare cf sft` once both exist). It is
    mutation-tested 13/13 and checks everything the runner checks, in a second rather than after
    the GPU hours are spent.
  - **FROZEN while paused** -- editing any of these invalidates the cf adapter or the run
    identity, and the adapter cost 4 GPU-h: `scripts/a_screen_train.py`, `scripts/a_screen_run.py`,
    `src/stencil/a_screen.py`, `src/stencil/a_train_pool.py`, and `src/stencil/a_screen_pool/`.
  - Training health at the pause: margin +0.64 -> +8.45 (monotone bar one dip), CE 0.068 ->
    0.0004, objective saturated. So a later null would read as failure to TRANSFER, not as
    undertraining -- the adapter learned the training distribution thoroughly.
  - CPU work continues: Astra reviews, analysis, and the writeup. No GPU.

exec
/bin/bash -lc "rg --files results/a-screen tests src/stencil/a_screen_pool | rg '(analysis/|BASELINE|EXCEPTION|test_a_screen|REGISTRATION|train-log|AGENTS)' && git status --short && nl -ba results/a-screen/RESULTS-BASELINE.md && nl -ba results/a-screen/analysis/stale2.py" in /home/bmarti44/stencil-llm
 succeeded in 0ms:
results/a-screen/RUNNER-EXCEPTION.md
results/a-screen/analysis/look.py
results/a-screen/analysis/stale2.py
results/a-screen/analysis/out/off-oldrunner-states.json
results/a-screen/analysis/runner_equivalence.py
results/a-screen/analysis/health.py
results/a-screen/analysis/preflight.py
results/a-screen/analysis/overlap.py
results/a-screen/analysis/names.py
results/a-screen/analysis/compare.py
results/a-screen/smoke/cf-adapter/train-log.json
results/a-screen/RESULTS-BASELINE.md
results/a-screen/REGISTRATION-A-SCREEN.md
results/a-screen/adapters/cf/train-log.json
tests/test_a_screen.py
tests/test_a_screen_supersession.py
tests/test_a_screen_compare_guard.py
tests/test_a_screen_spend.py
tests/test_a_screen_preflight_guard.py
 M plan/LEDGER.md
 M results/focal/quicklook.json
 M results/quick-checks/check45/manifest.json
 M tests/test_a_screen_spend.py
?? tests/test_a_screen_compare_guard.py
?? tests/test_a_screen_preflight_guard.py
?? tests/test_a_screen_supersession.py
     1	# Candidate-A screen: the `off` baseline, and what it does and does not show
     2	
     3	**Arm:** `off` (Qwen3-4B trunk, no adapter) · 48 sessions × 2 requests = 96 replies
     4	**Run:** `results/a-screen/runs/off-oldrunner.jsonl`, COMPLETE, 61.6 min,
     5	`runner_sha256 4acdb8f044c25a48` (see `RUNNER-EXCEPTION.md`)
     6	**Status:** descriptive baseline. **One arm.** Nothing here compares an
     7	intervention to anything, and nothing here is evidence that the candidate-A
     8	objective works.
     9	
    10	## The registered outcome
    11	
    12	**J = 6/48.** J is all six suites passing at BOTH checkpoints. All six successes
    13	are in the **`missing_record`** family; `naming` and `validation` contribute
    14	zero. `function_only` is 39/96 replies. The aggregate hides that concentration
    15	completely, which is why the breakdowns below are reported with every number.
    16	
    17	## The exploratory outcome, and how it was chosen
    18	
    19	J answers "did the whole session go right" and cannot say why a session failed.
    20	After seeing `off` — **this endpoint was selected after the baseline was read,
    21	and that is a selection effect that must travel with every use of it** — each
    22	reply was additionally re-run against the contract suite for the state IN FORCE
    23	and the suite for the OTHER state, giving five exhaustive categories: in-force /
    24	alt / both / neither / output-failure.
    25	
    26	The population key is whether the alternative state was **in force earlier in
    27	that same session**. It is derived, not assumed, and the derivation is tested
    28	over all 624 pool sessions (`tests/test_a_screen_supersession.py`):
    29	
    30	* request 1 — true only for the 12 **reinstatement** sessions, whose prefix
    31	  states a rule at turn 10 and replaces it at turn 12;
    32	* request 2 — true whenever the event changed the convention (36 sessions).
    33	
    34	An earlier version of this analysis called request 1 "no supersession yet" for
    35	every session. That was **false**, and it inverted the headline. The corrected
    36	reading is cleaner than the one it replaces.
    37	
    38	| population | n | in force | **superseded / alternative** | neither |
    39	|---|---:|---:|---:|---:|
    40	| req 1, alternative **never** in force | 36 | 25 (69%) | **0 (0%)** | 11 (31%) |
    41	| req 1, alternative **superseded in the prefix** | 12 | 5 (42%) | **4 (33%)** | 3 (25%) |
    42	| req 2, convention **unchanged** | 12 | 7 (58%) | 1 (8%) | 4 (33%) |
    43	| req 2, convention **changed** at the event | 36 | 11 (31%) | **12 (33%)** | 13 (36%) |
    44	
    45	Fisher exact, two-sided:
    46	
    47	* request 1, superseded-in-prefix vs never-in-force: **4/12 vs 0/36, p = 0.0025**
    48	* request 2, changed vs unchanged: **12/36 vs 1/12, p = 0.139**
    49	* pooled (not independent — the 12 reinstatement sessions appear in both rows):
    50	  16/48 vs 1/48, p = 0.00007
    51	
    52	**The pattern:** the model writes code obeying a convention only where a
    53	convention has actually been superseded — 0 of 36 where nothing ever was, and a
    54	consistent ~33% in both places where something was. The single "alt" reply in
    55	the unchanged cell is the one arguable exception.
    56	
    57	**The sharpest form of the failure:** in the changed-convention cell, **8 of 36
    58	replies followed the superseded convention AND passed the functional suite** —
    59	working code that implements a rule the user explicitly cancelled. A further 4
    60	followed it and did not work.
    61	
    62	## Breakdowns, where the alternative was superseded (n = 48)
    63	
    64	| family | in force | superseded | neither |
    65	|---|---:|---:|---:|
    66	| missing_record | 9/16 | 7/16 | 0/16 |
    67	| naming | 6/16 | 5/16 | 5/16 |
    68	| **validation** | **1/16** | 4/16 | 11/16 |
    69	
    70	| lifecycle | in force | superseded | neither |
    71	|---|---:|---:|---:|
    72	| reinstatement (24) | 9 | 7 | 8 |
    73	| replacement (12) | 3 | 5 | 4 |
    74	| scope (12) | 4 | 4 | 4 |
    75	
    76	| transition | n | in force | superseded | neither |
    77	|---|---:|---:|---:|---:|
    78	| raise -> none | 8 | 6 | 2 | 0 |
    79	| none -> raise | 8 | 3 | 5 | 0 |
    80	| verb_noun -> noun_verb | 10 | 4 | 2 | 4 |
    81	| noun_verb -> verb_noun | 6 | 2 | 3 | 1 |
    82	| storage -> api | 7 | 1 | 2 | 4 |
    83	| api -> storage | 9 | 0 | 2 | 7 |
    84	
    85	`validation` is a competence problem, not a focus problem: 1/16 current-rule
    86	successes and 11/16 "neither" means the trunk mostly cannot write the requested
    87	change at all, in either state. A screen whose headline mixes that family in is
    88	measuring two different things at once.
    89	
    90	## Independent cross-check
    91	
    92	`analysis/names.py` classifies the same replies syntactically — which
    93	convention's method names the reply introduced — on the 16 `naming` sessions,
    94	the only family where the two states differ by name (checked: `missing_record`
    95	and `validation` gold share identical public method names in 32/32 requests).
    96	It agrees with the executable measure on **30/32** requests. The two
    97	disagreements (S08 req1, S11 req2) are replies with the right or wrong name
    98	whose suite failed for an unrelated reason; the executable measure is the
    99	stricter of the two, as intended.
   100	
   101	## Confounds and limits, stated before any use of these numbers
   102	
   103	1. **One arm.** No intervention is compared to anything here.
   104	2. **Selection.** The contract-state endpoint was chosen after reading `off`.
   105	   The registered outcome (J) is reported above and is not replaced.
   106	3. **Supersession is confounded with prefix complexity.** Reinstatement sessions
   107	   carry a third rule turn and a longer rule history, so the request-1 contrast
   108	   compares "something was superseded" AND "one more rule statement" against
   109	   neither. The p = 0.0025 does not separate them.
   110	4. **The populations differ in more than the treatment**: project, request text
   111	   and lifecycle all vary between cells.
   112	5. **Not long-horizon retention.** The screen has two live requests over an
   113	   authored 16-turn prefix, and the packer is told which rule turns to preserve
   114	   (`session.rule_turns`). Nothing here tests finding or holding an instruction
   115	   through a real agent session.
   116	6. **Common-mode scoring defects can still bias an arm difference.** An
   117	   under-sensitive checker applying identically to both arms does NOT imply it
   118	   cannot manufacture a difference — different adapters make different kinds of
   119	   undetected error. Any positive result must be read at the reply level.
   120	
   121	## Is the screen a memorisation test? No.
   122	
   123	The cf training run reached CE 0.0006 while `epochs_completed` was still 0 —
   124	every example it learned on was unseen when it trained on it — which says the
   125	gold is close to determined by the prefix under this generator. That raises the
   126	question of whether an adapter could win the screen by reproducing text it has
   127	already been fitted to. `analysis/overlap.py` measures it directly, with no
   128	model: for each of the 192 screen golds, the most similar of the 2,304 training
   129	golds.
   130	
   131	| measure | min | p25 | median | p75 | max | >= 0.70 |
   132	|---|---:|---:|---:|---:|---:|---:|
   133	| token jaccard | 0.147 | 0.211 | 0.244 | 0.275 | 0.329 | 0/192 |
   134	| difflib ratio | 0.035 | 0.105 | 0.124 | 0.138 | 0.254 | 0/192 |
   135	
   136	Nothing in the screen resembles anything in the training pool at the text level,
   137	so a positive result cannot be verbatim recall. What this does NOT rule out is
   138	the **structural** template: 44/48 screen projects share the
   139	dataclass-record/private-mapping idiom, and the jaccard floor of ~0.24 is that
   140	shared vocabulary. A win would still need reading at the reply level.
   141	
   142	## Instrument
   143	
   144	`stencil.contracts.run_tests` shells out to `sys.executable -m pytest`. Under a
   145	bare `python3` without pytest every suite returns False and **every reply
   146	classifies as "neither"** — a complete, plausible, entirely empty table with
   147	both contrasts at p = 1.000. That happened once on 2026-09-13. `stale2.py` and
   148	`compare.py` now refuse to run unless a trivially passing suite passes, a
   149	trivially failing suite fails, and gold satisfies its own contract suite on real
   150	sessions.
   151	
   152	## Reproduce
   153	
   154	```
   155	uv run python results/a-screen/analysis/stale2.py results/a-screen/runs/off-oldrunner.jsonl
   156	uv run python results/a-screen/analysis/names.py  results/a-screen/runs/off-oldrunner.jsonl
   157	uv run pytest -q tests/test_a_screen_supersession.py tests/test_a_screen_compare_guard.py \
   158	               tests/test_a_screen_preflight_guard.py
   159	```
   160	
   161	Per-reply records: `results/a-screen/analysis/out/off-oldrunner-states.json`.
     1	"""Convention-in-force scoring.  Rebuilt twice: once after Astra's review of
     2	stale.py, once after Astra's review of THIS file found its headline label false.
     3	
     4	Correction 8 (2026-09-13, back-on-track review).  The previous version labelled
     5	request 1 "no supersession yet" for every session.  That is FALSE for the 12
     6	REINSTATEMENT sessions, whose authored prefix already contains a supersession:
     7	rule turn 10 states states[0], rule turn 12 replaces it with states[1] (=
     8	state_at[0], in force at request 1), and the event between the requests
     9	reinstates states[0].  So at request 1 of a reinstatement session the
    10	alternative state WAS in force and WAS explicitly superseded, and a reply that
    11	follows it is a genuine stale-convention error.  All four request-1 "stale"
    12	replies in the off arm (S12, S20, S36, S44) are reinstatement sessions, so the
    13	old headline -- "stale replies appear even before anything is superseded" --
    14	had no support at all.
    15	
    16	The population key is now DERIVED, never assumed: for request k, was the
    17	alternative state (`session.other(state_at[k-1])`) in force earlier in this
    18	same session?
    19	
    20	    k = 1:  true iff the prefix contains a supersession, i.e. three rule turns
    21	            (equivalent to lifecycle == "reinstatement" on all 624 pool
    22	            sessions; asserted here, tested in tests/).
    23	    k = 2:  true iff state_at[0] != state_at[1], i.e. the event changed the
    24	            convention; the alternative at request 2 IS state_at[0], which was
    25	            in force at request 1.
    26	
    27	The four cells that follow are the ones reported.  The word STALE is used only
    28	where that flag is true; where it is false the same category is the alternative
    29	state, which was never in force, and calling it stale would repeat the defect
    30	this correction fixes.
    31	
    32	Earlier corrections, kept:
    33	
    34	 3a HIGH  The conditional rate in-force/(in-force+stale) is NOT a cross-arm
    35	          comparison.  Astra's counterexample: (current, stale, neither) =
    36	          (40,40,20) -> (40,10,50) lifts it from 50% to 80% without one extra
    37	          current-rule success.  Denominators are FIXED per cell and every
    38	          category is reported against them.
    39	 3b MED   A reply can satisfy BOTH contract suites (S34: return None for an
    40	          unknown id when the account holds tokens, raise KeyError otherwise --
    41	          both suites use different setups and both pass).  BOTH is its own
    42	          unresolved bucket, never "states agree".
    43	 3c HIGH  Replay must follow the runner: apply ONLY records whose
    44	          terminal_reason is "applied", and on a failed apply RETAIN the
    45	          preceding repository rather than abandoning the session
    46	          (a_screen_run.py:575).  Every reconstruction is checked against the
    47	          repo_before hashes the runner recorded.
    48	 7  MED   Contract compliance and functional success are reported ALONGSIDE
    49	          each other, neither conditional on the other: 11 of the first 24
    50	          in-force replies failed the functional suite, so "followed the
    51	          convention" does not mean "wrote working code".
    52	
    53	Writes results/a-screen/analysis/out/<arm>-states.json: one record per
    54	(session, request) with the raw category, the population key, family,
    55	lifecycle, direction and functional score, so a cross-arm comparison never has
    56	to recompute the labels or trust this summary.
    57	"""
    58	
    59	import json
    60	import os
    61	import sys
    62	from collections import Counter, defaultdict
    63	
    64	from scipy.stats import fisher_exact
    65	
    66	sys.path.insert(0, "/home/bmarti44/stencil-llm/src")
    67	from stencil import a_screen as A  # noqa: E402
    68	from stencil.a_screen_pool import load  # noqa: E402
    69	
    70	CATS = ("in-force", "alt", "both", "neither", "output-failure")
    71	OUT = "/home/bmarti44/stencil-llm/results/a-screen/analysis/out"
    72	
    73	
    74	def repo_hash(files):
    75	    """The runner's own hash (a_screen_run.py:68-73), so replay can be checked."""
    76	    import hashlib
    77	
    78	    return hashlib.sha256(
    79	        json.dumps(files, sort_keys=True).encode()
    80	    ).hexdigest()[:16]
    81	
    82	
    83	def alt_was_in_force(session, k):
    84	    """Was the alternative state at request k in force earlier in this session?
    85	
    86	    The equivalence asserted here is checked over all 624 pool sessions by
    87	    tests/test_a_screen_supersession.py; it is the whole basis of the labels.
    88	    """
    89	    three = len(session.rule_turns) == 3
    90	    assert three == (session.lifecycle == "reinstatement"), session.id
    91	    if k == 1:
    92	        return three
    93	    return session.state_at[0] != session.state_at[1]
    94	
    95	
    96	def population(session, k):
    97	    return (k, alt_was_in_force(session, k))
    98	
    99	
   100	POP_NAME = {
   101	    (1, False): "req1  alternative NEVER in force  (stable/replacement/scope)",
   102	    (1, True): "req1  alternative SUPERSEDED in the prefix  (reinstatement)",
   103	    (2, False): "req2  convention unchanged  (stable)",
   104	    (2, True): "req2  convention CHANGED at the event  (repl/scope/reinst)",
   105	}
   106	
   107	
   108	def replay(session, recs):
   109	    """The repository entering each request, exactly as the runner built it."""
   110	    files = dict(session.files)
   111	    entering = {1: files}
   112	    for k in (1, 2):
   113	        rec = recs.get(k)
   114	        if rec is None:
   115	            break
   116	        nxt = None
   117	        if rec["terminal_reason"] == "applied":
   118	            nxt, _ = A.apply_reply(files, session.requests[k - 1], rec["output"])
   119	        files = nxt if nxt is not None else files  # runner retains on failure
   120	        entering[k + 1] = files
   121	    return entering
   122	
   123	
   124	def classify(session, rec, base):
   125	    """in-force / alt / both / neither / output-failure for one reply."""
   126	    if rec["terminal_reason"] != "applied":
   127	        return "output-failure"
   128	    k = rec["request"]
   129	    req = session.requests[k - 1]
   130	    state = session.state_at[k - 1]
   131	    files, _ = A.apply_reply(base, req, rec["output"])
   132	    if files is None:
   133	        return "output-failure"
   134	    now, _ = A.run_tests(files, req.contract_tests[state], timeout=90.0)
   135	    alt, _ = A.run_tests(files, req.contract_tests[session.other(state)], timeout=90.0)
   136	    if now and alt:
   137	        return "both"
   138	    if now:
   139	        return "in-force"
   140	    if alt:
   141	        return "alt"
   142	    return "neither"
   143	
   144	
   145	def self_check(sample=3):
   146	    """The measure must be able to FAIL and to PASS before any verdict is trusted.
   147	
   148	    Found the hard way on 2026-09-13.  `stencil.contracts.run_tests` shells out to
   149	    `sys.executable -m pytest`; under a bare `python3` that has no pytest, every
   150	    suite returns (False, "") and EVERY reply classifies as "neither" -- a clean,
   151	    plausible, entirely empty table, with the contrast at p=1.000.  A measure that
   152	    cannot pass is not evidence of failure, so this refuses to run rather than
   153	    report.  Run the analysis under `uv run python`.
   154	
   155	    Two levels: the instrument answers both ways at all, and gold satisfies its own
   156	    contract suite on real sessions (a suite nothing can pass measures nothing).
   157	    """
   158	    passing = {"test_p.py": "def test_p():\n    assert True\n"}
   159	    ok, msg = A.run_tests({"m.py": "x = 1"}, passing)
   160	    if not ok:
   161	        raise SystemExit(
   162	            f"INSTRUMENT DEAD: a trivially passing suite returned {(ok, msg)!r}.\n"
   163	            f"  interpreter: {sys.executable}\n"
   164	            f"  pytest is not importable there -- run this under `uv run python`."
   165	        )
   166	    failing = {"test_f.py": "def test_f():\n    assert False\n"}
   167	    bad, _ = A.run_tests({"m.py": "x = 1"}, failing)
   168	    if bad:
   169	        raise SystemExit("INSTRUMENT DEAD: a failing suite reported success.")
   170	    from stencil.a_screen_pool import available_slots
   171	
   172	    for sid in available_slots()[:sample]:
   173	        s = load(sid)
   174	        for k in (1, 2):
   175	            req = s.requests[k - 1]
   176	            state = s.state_at[k - 1]
   177	            base = dict(s.files) if k == 1 else A.gold_files(s, k - 1)
   178	            files = {**base, req.target: req.gold[state]}
   179	            ok, msg = A.run_tests(files, req.contract_tests[state], timeout=90.0)
   180	            if not ok:
   181	                raise SystemExit(
   182	                    f"INSTRUMENT DEAD: {sid} request {k} gold under the state in "
   183	                    f"force ({state}) fails its own contract suite: {msg}"
   184	                )
   185	    print(f"  self-check: the contract measure passes and fails correctly, and gold "
   186	          f"satisfies its own suite on {sample} sessions")
   187	
   188	
   189	def wilson(k, n, z=1.959963984540054):
   190	    if n == 0:
   191	        return (0.0, 0.0)
   192	    p = k / n
   193	    d = 1 + z * z / n
   194	    c = p + z * z / (2 * n)
   195	    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5)
   196	    return ((c - h) / d, (c + h) / d)
   197	
   198	
   199	def scan(path):
   200	    """Per-(session, request) records for one arm's run file."""
   201	    by = defaultdict(dict)
   202	    arm = None
   203	    for line in open(path):
   204	        d = json.loads(line)
   205	        arm = d["arm"]
   206	        by[d["session"]][d["request"]] = d
   207	    out, mismatch = [], 0
   208	    for sid, recs in sorted(by.items()):
   209	        s = load(sid)
   210	        entering = replay(s, recs)
   211	        for k in sorted(recs):
   212	            rec = recs[k]
   213	            base = entering.get(k)
   214	            if base is None:
   215	                continue
   216	            if rec.get("repo_before") != repo_hash(base):
   217	                mismatch += 1
   218	            state = s.state_at[k - 1]
   219	            out.append({
   220	                "arm": arm,
   221	                "session": sid,
   222	                "request": k,
   223	                "category": classify(s, rec, base),
   224	                "alt_was_in_force": alt_was_in_force(s, k),
   225	                "lifecycle": s.lifecycle,
   226	                "family": s.target_family,
   227	                "state_in_force": state,
   228	                "alternative": s.other(state),
   229	                "direction": f"{s.other(state)}->{state}"
   230	                             if alt_was_in_force(s, k) else f"(only {state})",
   231	                "functional": rec["scores"].get("functional"),
   232	                "j": all(rec["scores"].get(x) for x in A.SUITES),
   233	                "terminal_reason": rec["terminal_reason"],
   234	            })
   235	    return arm, out, mismatch, len(by)
   236	
   237	
   238	def alt_label(flag):
   239	    return "STALE (superseded)" if flag else "alt (never in force)"
   240	
   241	
   242	def report(arm, recs, mismatch, nsess, path):
   243	    print(f"\n===== {arm}   ({nsess} sessions, {path})")
   244	    if mismatch:
   245	        print(f"  !! {mismatch} reconstructed repositories disagree with the record")
   246	    else:
   247	        print("  replay verified against every recorded repo_before hash")
   248	
   249	    pops = defaultdict(Counter)
   250	    for r in recs:
   251	        pops[(r["request"], r["alt_was_in_force"])][r["category"]] += 1
   252	    for key in sorted(pops, key=lambda k: (k[0], k[1])):
   253	        tally = pops[key]
   254	        n = sum(tally.values())
   255	        print(f"  --- {POP_NAME[key]}   (fixed denominator n={n})")
   256	        for c in CATS:
   257	            if tally[c]:
   258	                name = alt_label(key[1]) if c == "alt" else c
   259	                lo, hi = wilson(tally[c], n)
   260	                print(f"        {name:20s} {tally[c]:3d}   {100 * tally[c] / n:5.1f}%"
   261	                      f"   [95% {100 * lo:.0f}-{100 * hi:.0f}]")
   262	
   263	    print("\n  --- contrasts on the alternative-state rate (Fisher exact, two-sided)")
   264	    for k, lbl in ((2, "request 2: changed vs unchanged"),
   265	                   (1, "request 1: superseded-in-prefix vs never-in-force")):
   266	        a, b = pops[(k, True)], pops[(k, False)]
   267	        na, nb = sum(a.values()), sum(b.values())
   268	        if not (na and nb):
   269	            continue
   270	        table = [[a["alt"], na - a["alt"]], [b["alt"], nb - b["alt"]]]
   271	        _, p = fisher_exact(table)
   272	        print(f"      {lbl}: {a['alt']}/{na} vs {b['alt']}/{nb}   p={p:.3f}")
   273	
   274	    print("\n  --- breakdowns where the alternative was superseded")
   275	    for dim in ("family", "lifecycle", "direction"):
   276	        cells = defaultdict(Counter)
   277	        for r in recs:
   278	            if r["alt_was_in_force"]:
   279	                cells[r[dim]][r["category"]] += 1
   280	        print(f"      by {dim}:")
   281	        for v in sorted(cells):
   282	            t = cells[v]
   283	            n = sum(t.values())
   284	            print(f"        {v:22s} n={n:3d}  " + "  ".join(
   285	                f"{c}={t[c]}" for c in CATS if t[c]))
   286	
   287	    print("\n  --- convention AND working code, neither conditional on the other")
   288	    cross = defaultdict(Counter)
   289	    for r in recs:
   290	        cross[(r["request"], r["alt_was_in_force"])][
   291	            f"{r['category']}|functional={r['functional']}"] += 1
   292	    for key in sorted(cross, key=lambda k: (k[0], k[1])):
   293	        print(f"      {POP_NAME[key]}:")
   294	        print("        " + "  ".join(f"{k}={v}" for k, v in sorted(cross[key].items())))
   295	
   296	    print("\n  --- per-session table")
   297	    print(f"      {'sess':5s} {'req':3s} {'lifecycle':14s} {'family':14s} "
   298	          f"{'direction':22s} {'category':15s} func J")
   299	    for r in recs:
   300	        print(f"      {r['session']:5s} {r['request']:<3d} {r['lifecycle']:14s} "
   301	              f"{r['family']:14s} {r['direction']:22s} {r['category']:15s} "
   302	              f"{str(r['functional']):5s} {'J' if r['j'] else '.'}")
   303	
   304	
   305	def run(path):
   306	    self_check()
   307	    arm, recs, mismatch, nsess = scan(path)
   308	    report(arm, recs, mismatch, nsess, path)
   309	    os.makedirs(OUT, exist_ok=True)
   310	    dest = f"{OUT}/{os.path.basename(path).rsplit('.jsonl', 1)[0]}-states.json"
   311	    with open(dest, "w") as fh:
   312	        json.dump({"arm": arm, "source": path, "sessions": nsess,
   313	                   "replay_mismatches": mismatch, "records": recs}, fh, indent=1)
   314	    print(f"\n  wrote {dest}")
   315	
   316	
   317	if __name__ == "__main__":
   318	    for p in sys.argv[1:]:
   319	        run(p)

web search: "Context-DPO" faithful stubborn ...
exec
/bin/bash -lc 'nl -ba results/a-screen/RESULTS-BASELINE.md && nl -ba results/a-screen/analysis/stale2.py && nl -ba tests/test_a_screen_supersession.py' in /home/bmarti44/stencil-llm
 succeeded in 0ms:
     1	# Candidate-A screen: the `off` baseline, and what it does and does not show
     2	
     3	**Arm:** `off` (Qwen3-4B trunk, no adapter) · 48 sessions × 2 requests = 96 replies
     4	**Run:** `results/a-screen/runs/off-oldrunner.jsonl`, COMPLETE, 61.6 min,
     5	`runner_sha256 4acdb8f044c25a48` (see `RUNNER-EXCEPTION.md`)
     6	**Status:** descriptive baseline. **One arm.** Nothing here compares an
     7	intervention to anything, and nothing here is evidence that the candidate-A
     8	objective works.
     9	
    10	## The registered outcome
    11	
    12	**J = 6/48.** J is all six suites passing at BOTH checkpoints. All six successes
    13	are in the **`missing_record`** family; `naming` and `validation` contribute
    14	zero. `function_only` is 39/96 replies. The aggregate hides that concentration
    15	completely, which is why the breakdowns below are reported with every number.
    16	
    17	## The exploratory outcome, and how it was chosen
    18	
    19	J answers "did the whole session go right" and cannot say why a session failed.
    20	After seeing `off` — **this endpoint was selected after the baseline was read,
    21	and that is a selection effect that must travel with every use of it** — each
    22	reply was additionally re-run against the contract suite for the state IN FORCE
    23	and the suite for the OTHER state, giving five exhaustive categories: in-force /
    24	alt / both / neither / output-failure.
    25	
    26	The population key is whether the alternative state was **in force earlier in
    27	that same session**. It is derived, not assumed, and the derivation is tested
    28	over all 624 pool sessions (`tests/test_a_screen_supersession.py`):
    29	
    30	* request 1 — true only for the 12 **reinstatement** sessions, whose prefix
    31	  states a rule at turn 10 and replaces it at turn 12;
    32	* request 2 — true whenever the event changed the convention (36 sessions).
    33	
    34	An earlier version of this analysis called request 1 "no supersession yet" for
    35	every session. That was **false**, and it inverted the headline. The corrected
    36	reading is cleaner than the one it replaces.
    37	
    38	| population | n | in force | **superseded / alternative** | neither |
    39	|---|---:|---:|---:|---:|
    40	| req 1, alternative **never** in force | 36 | 25 (69%) | **0 (0%)** | 11 (31%) |
    41	| req 1, alternative **superseded in the prefix** | 12 | 5 (42%) | **4 (33%)** | 3 (25%) |
    42	| req 2, convention **unchanged** | 12 | 7 (58%) | 1 (8%) | 4 (33%) |
    43	| req 2, convention **changed** at the event | 36 | 11 (31%) | **12 (33%)** | 13 (36%) |
    44	
    45	Fisher exact, two-sided:
    46	
    47	* request 1, superseded-in-prefix vs never-in-force: **4/12 vs 0/36, p = 0.0025**
    48	* request 2, changed vs unchanged: **12/36 vs 1/12, p = 0.139**
    49	* pooled (not independent — the 12 reinstatement sessions appear in both rows):
    50	  16/48 vs 1/48, p = 0.00007
    51	
    52	**The pattern:** the model writes code obeying a convention only where a
    53	convention has actually been superseded — 0 of 36 where nothing ever was, and a
    54	consistent ~33% in both places where something was. The single "alt" reply in
    55	the unchanged cell is the one arguable exception.
    56	
    57	**The sharpest form of the failure:** in the changed-convention cell, **8 of 36
    58	replies followed the superseded convention AND passed the functional suite** —
    59	working code that implements a rule the user explicitly cancelled. A further 4
    60	followed it and did not work.
    61	
    62	## Breakdowns, where the alternative was superseded (n = 48)
    63	
    64	| family | in force | superseded | neither |
    65	|---|---:|---:|---:|
    66	| missing_record | 9/16 | 7/16 | 0/16 |
    67	| naming | 6/16 | 5/16 | 5/16 |
    68	| **validation** | **1/16** | 4/16 | 11/16 |
    69	
    70	| lifecycle | in force | superseded | neither |
    71	|---|---:|---:|---:|
    72	| reinstatement (24) | 9 | 7 | 8 |
    73	| replacement (12) | 3 | 5 | 4 |
    74	| scope (12) | 4 | 4 | 4 |
    75	
    76	| transition | n | in force | superseded | neither |
    77	|---|---:|---:|---:|---:|
    78	| raise -> none | 8 | 6 | 2 | 0 |
    79	| none -> raise | 8 | 3 | 5 | 0 |
    80	| verb_noun -> noun_verb | 10 | 4 | 2 | 4 |
    81	| noun_verb -> verb_noun | 6 | 2 | 3 | 1 |
    82	| storage -> api | 7 | 1 | 2 | 4 |
    83	| api -> storage | 9 | 0 | 2 | 7 |
    84	
    85	`validation` is a competence problem, not a focus problem: 1/16 current-rule
    86	successes and 11/16 "neither" means the trunk mostly cannot write the requested
    87	change at all, in either state. A screen whose headline mixes that family in is
    88	measuring two different things at once.
    89	
    90	## Independent cross-check
    91	
    92	`analysis/names.py` classifies the same replies syntactically — which
    93	convention's method names the reply introduced — on the 16 `naming` sessions,
    94	the only family where the two states differ by name (checked: `missing_record`
    95	and `validation` gold share identical public method names in 32/32 requests).
    96	It agrees with the executable measure on **30/32** requests. The two
    97	disagreements (S08 req1, S11 req2) are replies with the right or wrong name
    98	whose suite failed for an unrelated reason; the executable measure is the
    99	stricter of the two, as intended.
   100	
   101	## Confounds and limits, stated before any use of these numbers
   102	
   103	1. **One arm.** No intervention is compared to anything here.
   104	2. **Selection.** The contract-state endpoint was chosen after reading `off`.
   105	   The registered outcome (J) is reported above and is not replaced.
   106	3. **Supersession is confounded with prefix complexity.** Reinstatement sessions
   107	   carry a third rule turn and a longer rule history, so the request-1 contrast
   108	   compares "something was superseded" AND "one more rule statement" against
   109	   neither. The p = 0.0025 does not separate them.
   110	4. **The populations differ in more than the treatment**: project, request text
   111	   and lifecycle all vary between cells.
   112	5. **Not long-horizon retention.** The screen has two live requests over an
   113	   authored 16-turn prefix, and the packer is told which rule turns to preserve
   114	   (`session.rule_turns`). Nothing here tests finding or holding an instruction
   115	   through a real agent session.
   116	6. **Common-mode scoring defects can still bias an arm difference.** An
   117	   under-sensitive checker applying identically to both arms does NOT imply it
   118	   cannot manufacture a difference — different adapters make different kinds of
   119	   undetected error. Any positive result must be read at the reply level.
   120	
   121	## Is the screen a memorisation test? No.
   122	
   123	The cf training run reached CE 0.0006 while `epochs_completed` was still 0 —
   124	every example it learned on was unseen when it trained on it — which says the
   125	gold is close to determined by the prefix under this generator. That raises the
   126	question of whether an adapter could win the screen by reproducing text it has
   127	already been fitted to. `analysis/overlap.py` measures it directly, with no
   128	model: for each of the 192 screen golds, the most similar of the 2,304 training
   129	golds.
   130	
   131	| measure | min | p25 | median | p75 | max | >= 0.70 |
   132	|---|---:|---:|---:|---:|---:|---:|
   133	| token jaccard | 0.147 | 0.211 | 0.244 | 0.275 | 0.329 | 0/192 |
   134	| difflib ratio | 0.035 | 0.105 | 0.124 | 0.138 | 0.254 | 0/192 |
   135	
   136	Nothing in the screen resembles anything in the training pool at the text level,
   137	so a positive result cannot be verbatim recall. What this does NOT rule out is
   138	the **structural** template: 44/48 screen projects share the
   139	dataclass-record/private-mapping idiom, and the jaccard floor of ~0.24 is that
   140	shared vocabulary. A win would still need reading at the reply level.
   141	
   142	## Instrument
   143	
   144	`stencil.contracts.run_tests` shells out to `sys.executable -m pytest`. Under a
   145	bare `python3` without pytest every suite returns False and **every reply
   146	classifies as "neither"** — a complete, plausible, entirely empty table with
   147	both contrasts at p = 1.000. That happened once on 2026-09-13. `stale2.py` and
   148	`compare.py` now refuse to run unless a trivially passing suite passes, a
   149	trivially failing suite fails, and gold satisfies its own contract suite on real
   150	sessions.
   151	
   152	## Reproduce
   153	
   154	```
   155	uv run python results/a-screen/analysis/stale2.py results/a-screen/runs/off-oldrunner.jsonl
   156	uv run python results/a-screen/analysis/names.py  results/a-screen/runs/off-oldrunner.jsonl
   157	uv run pytest -q tests/test_a_screen_supersession.py tests/test_a_screen_compare_guard.py \
   158	               tests/test_a_screen_preflight_guard.py
   159	```
   160	
   161	Per-reply records: `results/a-screen/analysis/out/off-oldrunner-states.json`.
     1	"""Convention-in-force scoring.  Rebuilt twice: once after Astra's review of
     2	stale.py, once after Astra's review of THIS file found its headline label false.
     3	
     4	Correction 8 (2026-09-13, back-on-track review).  The previous version labelled
     5	request 1 "no supersession yet" for every session.  That is FALSE for the 12
     6	REINSTATEMENT sessions, whose authored prefix already contains a supersession:
     7	rule turn 10 states states[0], rule turn 12 replaces it with states[1] (=
     8	state_at[0], in force at request 1), and the event between the requests
     9	reinstates states[0].  So at request 1 of a reinstatement session the
    10	alternative state WAS in force and WAS explicitly superseded, and a reply that
    11	follows it is a genuine stale-convention error.  All four request-1 "stale"
    12	replies in the off arm (S12, S20, S36, S44) are reinstatement sessions, so the
    13	old headline -- "stale replies appear even before anything is superseded" --
    14	had no support at all.
    15	
    16	The population key is now DERIVED, never assumed: for request k, was the
    17	alternative state (`session.other(state_at[k-1])`) in force earlier in this
    18	same session?
    19	
    20	    k = 1:  true iff the prefix contains a supersession, i.e. three rule turns
    21	            (equivalent to lifecycle == "reinstatement" on all 624 pool
    22	            sessions; asserted here, tested in tests/).
    23	    k = 2:  true iff state_at[0] != state_at[1], i.e. the event changed the
    24	            convention; the alternative at request 2 IS state_at[0], which was
    25	            in force at request 1.
    26	
    27	The four cells that follow are the ones reported.  The word STALE is used only
    28	where that flag is true; where it is false the same category is the alternative
    29	state, which was never in force, and calling it stale would repeat the defect
    30	this correction fixes.
    31	
    32	Earlier corrections, kept:
    33	
    34	 3a HIGH  The conditional rate in-force/(in-force+stale) is NOT a cross-arm
    35	          comparison.  Astra's counterexample: (current, stale, neither) =
    36	          (40,40,20) -> (40,10,50) lifts it from 50% to 80% without one extra
    37	          current-rule success.  Denominators are FIXED per cell and every
    38	          category is reported against them.
    39	 3b MED   A reply can satisfy BOTH contract suites (S34: return None for an
    40	          unknown id when the account holds tokens, raise KeyError otherwise --
    41	          both suites use different setups and both pass).  BOTH is its own
    42	          unresolved bucket, never "states agree".
    43	 3c HIGH  Replay must follow the runner: apply ONLY records whose
    44	          terminal_reason is "applied", and on a failed apply RETAIN the
    45	          preceding repository rather than abandoning the session
    46	          (a_screen_run.py:575).  Every reconstruction is checked against the
    47	          repo_before hashes the runner recorded.
    48	 7  MED   Contract compliance and functional success are reported ALONGSIDE
    49	          each other, neither conditional on the other: 11 of the first 24
    50	          in-force replies failed the functional suite, so "followed the
    51	          convention" does not mean "wrote working code".
    52	
    53	Writes results/a-screen/analysis/out/<arm>-states.json: one record per
    54	(session, request) with the raw category, the population key, family,
    55	lifecycle, direction and functional score, so a cross-arm comparison never has
    56	to recompute the labels or trust this summary.
    57	"""
    58	
    59	import json
    60	import os
    61	import sys
    62	from collections import Counter, defaultdict
    63	
    64	from scipy.stats import fisher_exact
    65	
    66	sys.path.insert(0, "/home/bmarti44/stencil-llm/src")
    67	from stencil import a_screen as A  # noqa: E402
    68	from stencil.a_screen_pool import load  # noqa: E402
    69	
    70	CATS = ("in-force", "alt", "both", "neither", "output-failure")
    71	OUT = "/home/bmarti44/stencil-llm/results/a-screen/analysis/out"
    72	
    73	
    74	def repo_hash(files):
    75	    """The runner's own hash (a_screen_run.py:68-73), so replay can be checked."""
    76	    import hashlib
    77	
    78	    return hashlib.sha256(
    79	        json.dumps(files, sort_keys=True).encode()
    80	    ).hexdigest()[:16]
    81	
    82	
    83	def alt_was_in_force(session, k):
    84	    """Was the alternative state at request k in force earlier in this session?
    85	
    86	    The equivalence asserted here is checked over all 624 pool sessions by
    87	    tests/test_a_screen_supersession.py; it is the whole basis of the labels.
    88	    """
    89	    three = len(session.rule_turns) == 3
    90	    assert three == (session.lifecycle == "reinstatement"), session.id
    91	    if k == 1:
    92	        return three
    93	    return session.state_at[0] != session.state_at[1]
    94	
    95	
    96	def population(session, k):
    97	    return (k, alt_was_in_force(session, k))
    98	
    99	
   100	POP_NAME = {
   101	    (1, False): "req1  alternative NEVER in force  (stable/replacement/scope)",
   102	    (1, True): "req1  alternative SUPERSEDED in the prefix  (reinstatement)",
   103	    (2, False): "req2  convention unchanged  (stable)",
   104	    (2, True): "req2  convention CHANGED at the event  (repl/scope/reinst)",
   105	}
   106	
   107	
   108	def replay(session, recs):
   109	    """The repository entering each request, exactly as the runner built it."""
   110	    files = dict(session.files)
   111	    entering = {1: files}
   112	    for k in (1, 2):
   113	        rec = recs.get(k)
   114	        if rec is None:
   115	            break
   116	        nxt = None
   117	        if rec["terminal_reason"] == "applied":
   118	            nxt, _ = A.apply_reply(files, session.requests[k - 1], rec["output"])
   119	        files = nxt if nxt is not None else files  # runner retains on failure
   120	        entering[k + 1] = files
   121	    return entering
   122	
   123	
   124	def classify(session, rec, base):
   125	    """in-force / alt / both / neither / output-failure for one reply."""
   126	    if rec["terminal_reason"] != "applied":
   127	        return "output-failure"
   128	    k = rec["request"]
   129	    req = session.requests[k - 1]
   130	    state = session.state_at[k - 1]
   131	    files, _ = A.apply_reply(base, req, rec["output"])
   132	    if files is None:
   133	        return "output-failure"
   134	    now, _ = A.run_tests(files, req.contract_tests[state], timeout=90.0)
   135	    alt, _ = A.run_tests(files, req.contract_tests[session.other(state)], timeout=90.0)
   136	    if now and alt:
   137	        return "both"
   138	    if now:
   139	        return "in-force"
   140	    if alt:
   141	        return "alt"
   142	    return "neither"
   143	
   144	
   145	def self_check(sample=3):
   146	    """The measure must be able to FAIL and to PASS before any verdict is trusted.
   147	
   148	    Found the hard way on 2026-09-13.  `stencil.contracts.run_tests` shells out to
   149	    `sys.executable -m pytest`; under a bare `python3` that has no pytest, every
   150	    suite returns (False, "") and EVERY reply classifies as "neither" -- a clean,
   151	    plausible, entirely empty table, with the contrast at p=1.000.  A measure that
   152	    cannot pass is not evidence of failure, so this refuses to run rather than
   153	    report.  Run the analysis under `uv run python`.
   154	
   155	    Two levels: the instrument answers both ways at all, and gold satisfies its own
   156	    contract suite on real sessions (a suite nothing can pass measures nothing).
   157	    """
   158	    passing = {"test_p.py": "def test_p():\n    assert True\n"}
   159	    ok, msg = A.run_tests({"m.py": "x = 1"}, passing)
   160	    if not ok:
   161	        raise SystemExit(
   162	            f"INSTRUMENT DEAD: a trivially passing suite returned {(ok, msg)!r}.\n"
   163	            f"  interpreter: {sys.executable}\n"
   164	            f"  pytest is not importable there -- run this under `uv run python`."
   165	        )
   166	    failing = {"test_f.py": "def test_f():\n    assert False\n"}
   167	    bad, _ = A.run_tests({"m.py": "x = 1"}, failing)
   168	    if bad:
   169	        raise SystemExit("INSTRUMENT DEAD: a failing suite reported success.")
   170	    from stencil.a_screen_pool import available_slots
   171	
   172	    for sid in available_slots()[:sample]:
   173	        s = load(sid)
   174	        for k in (1, 2):
   175	            req = s.requests[k - 1]
   176	            state = s.state_at[k - 1]
   177	            base = dict(s.files) if k == 1 else A.gold_files(s, k - 1)
   178	            files = {**base, req.target: req.gold[state]}
   179	            ok, msg = A.run_tests(files, req.contract_tests[state], timeout=90.0)
   180	            if not ok:
   181	                raise SystemExit(
   182	                    f"INSTRUMENT DEAD: {sid} request {k} gold under the state in "
   183	                    f"force ({state}) fails its own contract suite: {msg}"
   184	                )
   185	    print(f"  self-check: the contract measure passes and fails correctly, and gold "
   186	          f"satisfies its own suite on {sample} sessions")
   187	
   188	
   189	def wilson(k, n, z=1.959963984540054):
   190	    if n == 0:
   191	        return (0.0, 0.0)
   192	    p = k / n
   193	    d = 1 + z * z / n
   194	    c = p + z * z / (2 * n)
   195	    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5)
   196	    return ((c - h) / d, (c + h) / d)
   197	
   198	
   199	def scan(path):
   200	    """Per-(session, request) records for one arm's run file."""
   201	    by = defaultdict(dict)
   202	    arm = None
   203	    for line in open(path):
   204	        d = json.loads(line)
   205	        arm = d["arm"]
   206	        by[d["session"]][d["request"]] = d
   207	    out, mismatch = [], 0
   208	    for sid, recs in sorted(by.items()):
   209	        s = load(sid)
   210	        entering = replay(s, recs)
   211	        for k in sorted(recs):
   212	            rec = recs[k]
   213	            base = entering.get(k)
   214	            if base is None:
   215	                continue
   216	            if rec.get("repo_before") != repo_hash(base):
   217	                mismatch += 1
   218	            state = s.state_at[k - 1]
   219	            out.append({
   220	                "arm": arm,
   221	                "session": sid,
   222	                "request": k,
   223	                "category": classify(s, rec, base),
   224	                "alt_was_in_force": alt_was_in_force(s, k),
   225	                "lifecycle": s.lifecycle,
   226	                "family": s.target_family,
   227	                "state_in_force": state,
   228	                "alternative": s.other(state),
   229	                "direction": f"{s.other(state)}->{state}"
   230	                             if alt_was_in_force(s, k) else f"(only {state})",
   231	                "functional": rec["scores"].get("functional"),
   232	                "j": all(rec["scores"].get(x) for x in A.SUITES),
   233	                "terminal_reason": rec["terminal_reason"],
   234	            })
   235	    return arm, out, mismatch, len(by)
   236	
   237	
   238	def alt_label(flag):
   239	    return "STALE (superseded)" if flag else "alt (never in force)"
   240	
   241	
   242	def report(arm, recs, mismatch, nsess, path):
   243	    print(f"\n===== {arm}   ({nsess} sessions, {path})")
   244	    if mismatch:
   245	        print(f"  !! {mismatch} reconstructed repositories disagree with the record")
   246	    else:
   247	        print("  replay verified against every recorded repo_before hash")
   248	
   249	    pops = defaultdict(Counter)
   250	    for r in recs:
   251	        pops[(r["request"], r["alt_was_in_force"])][r["category"]] += 1
   252	    for key in sorted(pops, key=lambda k: (k[0], k[1])):
   253	        tally = pops[key]
   254	        n = sum(tally.values())
   255	        print(f"  --- {POP_NAME[key]}   (fixed denominator n={n})")
   256	        for c in CATS:
   257	            if tally[c]:
   258	                name = alt_label(key[1]) if c == "alt" else c
   259	                lo, hi = wilson(tally[c], n)
   260	                print(f"        {name:20s} {tally[c]:3d}   {100 * tally[c] / n:5.1f}%"
   261	                      f"   [95% {100 * lo:.0f}-{100 * hi:.0f}]")
   262	
   263	    print("\n  --- contrasts on the alternative-state rate (Fisher exact, two-sided)")
   264	    for k, lbl in ((2, "request 2: changed vs unchanged"),
   265	                   (1, "request 1: superseded-in-prefix vs never-in-force")):
   266	        a, b = pops[(k, True)], pops[(k, False)]
   267	        na, nb = sum(a.values()), sum(b.values())
   268	        if not (na and nb):
   269	            continue
   270	        table = [[a["alt"], na - a["alt"]], [b["alt"], nb - b["alt"]]]
   271	        _, p = fisher_exact(table)
   272	        print(f"      {lbl}: {a['alt']}/{na} vs {b['alt']}/{nb}   p={p:.3f}")
   273	
   274	    print("\n  --- breakdowns where the alternative was superseded")
   275	    for dim in ("family", "lifecycle", "direction"):
   276	        cells = defaultdict(Counter)
   277	        for r in recs:
   278	            if r["alt_was_in_force"]:
   279	                cells[r[dim]][r["category"]] += 1
   280	        print(f"      by {dim}:")
   281	        for v in sorted(cells):
   282	            t = cells[v]
   283	            n = sum(t.values())
   284	            print(f"        {v:22s} n={n:3d}  " + "  ".join(
   285	                f"{c}={t[c]}" for c in CATS if t[c]))
   286	
   287	    print("\n  --- convention AND working code, neither conditional on the other")
   288	    cross = defaultdict(Counter)
   289	    for r in recs:
   290	        cross[(r["request"], r["alt_was_in_force"])][
   291	            f"{r['category']}|functional={r['functional']}"] += 1
   292	    for key in sorted(cross, key=lambda k: (k[0], k[1])):
   293	        print(f"      {POP_NAME[key]}:")
   294	        print("        " + "  ".join(f"{k}={v}" for k, v in sorted(cross[key].items())))
   295	
   296	    print("\n  --- per-session table")
   297	    print(f"      {'sess':5s} {'req':3s} {'lifecycle':14s} {'family':14s} "
   298	          f"{'direction':22s} {'category':15s} func J")
   299	    for r in recs:
   300	        print(f"      {r['session']:5s} {r['request']:<3d} {r['lifecycle']:14s} "
   301	              f"{r['family']:14s} {r['direction']:22s} {r['category']:15s} "
   302	              f"{str(r['functional']):5s} {'J' if r['j'] else '.'}")
   303	
   304	
   305	def run(path):
   306	    self_check()
   307	    arm, recs, mismatch, nsess = scan(path)
   308	    report(arm, recs, mismatch, nsess, path)
   309	    os.makedirs(OUT, exist_ok=True)
   310	    dest = f"{OUT}/{os.path.basename(path).rsplit('.jsonl', 1)[0]}-states.json"
   311	    with open(dest, "w") as fh:
   312	        json.dump({"arm": arm, "source": path, "sessions": nsess,
   313	                   "replay_mismatches": mismatch, "records": recs}, fh, indent=1)
   314	    print(f"\n  wrote {dest}")
   315	
   316	
   317	if __name__ == "__main__":
   318	    for p in sys.argv[1:]:
   319	        run(p)
     1	"""The supersession structure the contract-state analysis labels sessions by.
     2	
     3	Astra's back-on-track review (2026-09-13) found that
     4	results/a-screen/analysis/stale2.py called request 1 "no supersession yet" for
     5	every session.  That is false for reinstatement sessions: their authored prefix
     6	supersedes the first rule before either live request.  The corrected analysis
     7	keys its populations on `alt_was_in_force(session, k)`, and that function's
     8	whole basis is the equivalence asserted here, so it is tested over the complete
     9	pools rather than assumed.
    10	"""
    11	
    12	from stencil.a_screen_pool import screen_sessions
    13	from stencil.a_train_pool import train_sessions
    14	
    15	
    16	def _all_sessions():
    17	    return list(screen_sessions()) + list(train_sessions())
    18	
    19	
    20	def test_reinstatement_is_exactly_the_three_rule_turn_sessions():
    21	    """Three rule turns <=> a supersession inside the prefix <=> reinstatement."""
    22	    sessions = _all_sessions()
    23	    assert len(sessions) == 624, len(sessions)
    24	    for s in sessions:
    25	        assert (len(s.rule_turns) == 3) == (s.lifecycle == "reinstatement"), (
    26	            f"{s.id}: lifecycle {s.lifecycle} with rule turns {s.rule_turns}"
    27	        )
    28	        assert len(s.rule_turns) in (2, 3), f"{s.id}: {s.rule_turns}"
    29	
    30	
    31	def test_reinstatement_request_1_alternative_is_the_superseded_rule():
    32	    """At request 1 of a reinstatement, the alternative state is the rule the
    33	    prefix already replaced -- so following it IS a stale-convention error."""
    34	    for s in _all_sessions():
    35	        if s.lifecycle != "reinstatement":
    36	            continue
    37	        # turn 10 states states[0]; turn 12 replaces it with states[1].
    38	        assert s.state_at[0] == s.states[1], (s.id, s.states, s.state_at)
    39	        assert s.other(s.state_at[0]) == s.states[0], (s.id, s.states, s.state_at)
    40	        # the event reinstates the original for request 2
    41	        assert s.state_at[1] == s.states[0], (s.id, s.states, s.state_at)
    42	
    43	
    44	def test_non_reinstatement_request_1_alternative_was_never_in_force():
    45	    """Everywhere else the prefix states one rule only, so at request 1 the
    46	    alternative has no history and must not be scored as stale."""
    47	    for s in _all_sessions():
    48	        if s.lifecycle == "reinstatement":
    49	            continue
    50	        assert s.state_at[0] == s.states[0], (s.id, s.states, s.state_at)
    51	        assert len(s.rule_turns) == 2, (s.id, s.rule_turns)
    52	
    53	
    54	def test_request_2_alternative_is_request_1s_state_exactly_when_changed():
    55	    """The request-2 population key: the alternative at request 2 is the state
    56	    that was in force at request 1, and it is superseded iff the event changed
    57	    the convention."""
    58	    for s in _all_sessions():
    59	        changed = s.state_at[0] != s.state_at[1]
    60	        assert changed == (s.lifecycle != "stable"), (s.id, s.lifecycle)
    61	        if changed:
    62	            assert s.other(s.state_at[1]) == s.state_at[0], (s.id, s.state_at)

web search: 
exec
/bin/bash -lc 'nl -ba results/a-screen/analysis/compare.py && nl -ba results/a-screen/analysis/preflight.py' in /home/bmarti44/stencil-llm
 succeeded in 0ms:
     1	"""Cross-arm comparison on the primary population, paired by session id.
     2	
     3	Validation comes before any statistic.  Astra's back-on-track review (2026-09-13)
     4	found three high defects in the first version, all of them "it would have
     5	computed a number anyway":
     6	
     7	  * nothing required the arms to share the frozen 48-session set, so two runs
     8	    over different sessions would have been paired on whatever they happened to
     9	    have in common and the denominator would have shrunk silently;
    10	  * nothing required distinct arm labels or unique (session, request) records,
    11	    so a file compared with itself, or a run appended twice, would have printed
    12	    a tidy zero-difference table;
    13	  * nothing checked the run identity or the replay, so arms built from
    14	    different pools, prompt budgets or scoring code would have been compared
    15	    as if they differed only in the adapter.
    16	
    17	So `validate()` refuses to report unless: each file's records are unique and
    18	complete over its own declared session set; the declared session sets are
    19	identical; and every identity field that is not the adapter is identical across
    20	arms.  `runner_sha256` is the one field that may differ, and only with
    21	--runner-exception plus the recorded reason, because the baseline `off` run was
    22	produced on the pre-fix runner whose only difference lies inside `if a.adapter`
    23	-- a branch an adapterless run never enters (see RUNNER-EXCEPTION.md).
    24	
    25	Reported outcomes (Astra 7: a correctly-named but useless implementation passes
    26	the contract measure, and J erases a contract improvement on one unrelated
    27	competence failure, so neither alone is the answer):
    28	
    29	    contract IN FORCE            the convention question on its own
    30	    IN FORCE *and* functional    the reply a user would actually accept
    31	    followed the SUPERSEDED rule the error this work exists to remove
    32	    function_only                the runner's own functional-suite flag
    33	    J (all six suites)           the screen's registered success measure
    34	
    35	Each gets the exact McNemar p on the discordant pairs and the conservative
    36	paired interval the program registered: separate 97.5% Clopper-Pearson bounds
    37	on b/N and c/N combined by the union bound.
    38	
    39	The unchanged-convention population is printed beside the changed one as a
    40	DESCRIPTIVE control.  No causal reading is attached to the gap: with 12
    41	unchanged sessions the difference of two differences has no useful precision,
    42	and the two populations differ in project, request text and lifecycle as well
    43	as in whether the convention changed.
    44	"""
    45	
    46	import argparse
    47	import json
    48	import os
    49	import sys
    50	from collections import Counter, defaultdict
    51	from itertools import combinations
    52	from math import comb
    53	
    54	from scipy.stats import beta
    55	
    56	sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    57	sys.path.insert(0, "/home/bmarti44/stencil-llm/src")
    58	from stale2 import (  # noqa: E402
    59	    CATS,
    60	    alt_was_in_force,
    61	    classify,
    62	    replay,
    63	    repo_hash,
    64	    self_check,
    65	)
    66	
    67	from stencil import a_screen as A  # noqa: E402
    68	from stencil.a_screen_pool import load  # noqa: E402
    69	
    70	# identity fields that MUST agree across arms; the adapter fields are what vary
    71	ADAPTER_FIELDS = {
    72	    "adapter", "adapter_sha256", "adapter_steps", "adapter_config_sha256",
    73	    "pilot_adapter",
    74	}
    75	RUNNER_FIELD = "runner_sha256"
    76	
    77	
    78	def mcnemar_exact(b: int, c: int) -> float:
    79	    """Two-sided exact binomial on the discordant pairs (p = 0.5)."""
    80	    n = b + c
    81	    if n == 0:
    82	        return 1.0
    83	    k = min(b, c)
    84	    tail = sum(comb(n, i) for i in range(0, k + 1)) / (2.0**n)
    85	    return min(1.0, 2.0 * tail)
    86	
    87	
    88	def clopper_pearson(k, n, conf=0.975):
    89	    """Two-sided `conf` interval on k/n (so two of these union-bound to 95%)."""
    90	    if n == 0:
    91	        return (0.0, 1.0)
    92	    a = (1 - conf) / 2
    93	    lo = 0.0 if k == 0 else beta.ppf(a, k, n - k + 1)
    94	    hi = 1.0 if k == n else beta.ppf(1 - a, k + 1, n - k)
    95	    return (float(lo), float(hi))
    96	
    97	
    98	def paired_interval(b, c, n):
    99	    """Registered conservative interval on the paired difference (b - c)/n."""
   100	    blo, bhi = clopper_pearson(b, n)
   101	    clo, chi = clopper_pearson(c, n)
   102	    return (blo - chi, bhi - clo)
   103	
   104	
   105	def load_arm(path, problems):
   106	    """Records for one arm, with every within-file check."""
   107	    recs, ident, arm = {}, None, None
   108	    for i, line in enumerate(open(path), 1):
   109	        try:
   110	            d = json.loads(line)
   111	        except json.JSONDecodeError as e:
   112	            problems.append(f"{path}:{i}: unparsable ({e})")
   113	            continue
   114	        key = (d["session"], d["request"])
   115	        if key in recs:
   116	            problems.append(f"{path}: duplicate record for {key[0]} request {key[1]}")
   117	        recs[key] = d
   118	        if arm is None:
   119	            arm = d["arm"]
   120	        elif d["arm"] != arm:
   121	            problems.append(f"{path}: mixes arms {arm!r} and {d['arm']!r}")
   122	        if ident is None:
   123	            ident = d["identity"]
   124	        elif d["identity"] != ident:
   125	            problems.append(f"{path}:{i}: identity differs from the first record")
   126	    if ident is None:
   127	        problems.append(f"{path}: no records")
   128	        return None, {}, {}
   129	    want = {(s, k) for s in ident["sessions"] for k in (1, 2)}
   130	    missing = want - set(recs)
   131	    if missing:
   132	        problems.append(
   133	            f"{path}: INCOMPLETE, {len(missing)} of {len(want)} records missing "
   134	            f"(e.g. {sorted(missing)[:3]})"
   135	        )
   136	    extra = set(recs) - want
   137	    if extra:
   138	        problems.append(
   139	            f"{path}: {len(extra)} records outside the declared session set")
   140	    return arm, recs, ident
   141	
   142	
   143	def by_session(recs):
   144	    by = defaultdict(dict)
   145	    for (sid, k), d in recs.items():
   146	        by[sid][k] = d
   147	    return by
   148	
   149	
   150	def verify_replay(recs, problems, path):
   151	    """Cheap check -- no test execution -- that each record's repo_before is the
   152	    repository the runner would have handed that request.  Runs inside validate()
   153	    so a broken chain is refused before any pytest subprocess starts."""
   154	    for sid, rr in by_session(recs).items():
   155	        try:
   156	            session = load(sid)
   157	        except Exception as e:  # a session id the frozen pool does not contain
   158	            problems.append(f"{path}: {sid} is not a pool session ({type(e).__name__})")
   159	            continue
   160	        entering = replay(session, rr)
   161	        for k, rec in rr.items():
   162	            if rec.get("repo_before") != repo_hash(entering.get(k, {})):
   163	                problems.append(
   164	                    f"{path}: {sid} request {k} replay disagrees with the record")
   165	
   166	
   167	def score_arm(recs):
   168	    """Categories, functional and J per session.  Runs the contract suites, so it
   169	    is only called once validate() has passed."""
   170	    changed, unchanged = {}, {}
   171	    for sid, rr in by_session(recs).items():
   172	        s = load(sid)
   173	        entering = replay(s, rr)
   174	        if 2 not in rr:
   175	            continue
   176	        cat = classify(s, rr[2], entering.get(2))
   177	        sc = rr[2]["scores"]
   178	        row = {
   179	            "cat": cat,
   180	            "functional": bool(sc.get("functional")),
   181	            "function_only": bool(sc.get("function_only")),
   182	            "j": all(sc.get(x) for x in A.SUITES),
   183	        }
   184	        (changed if alt_was_in_force(s, 2) else unchanged)[sid] = row
   185	    return changed, unchanged
   186	
   187	
   188	def validate(paths, runner_exception):
   189	    problems, arms, data, idents = [], [], {}, {}
   190	    for p in paths:
   191	        arm, recs, ident = load_arm(p, problems)
   192	        if arm is None:
   193	            continue
   194	        if arm in data:
   195	            problems.append(
   196	                f"arm label {arm!r} appears in two files; labels must be unique")
   197	        verify_replay(recs, problems, p)
   198	        arms.append(arm)
   199	        data[arm] = (p, recs)
   200	        idents[arm] = ident
   201	    if len(arms) < 2:
   202	        problems.append("at least two arms are required")
   203	    for x, y in combinations(arms, 2):
   204	        ix, iy = idents[x], idents[y]
   205	        if ix["sessions"] != iy["sessions"]:
   206	            problems.append(f"{x} and {y} declare different session sets")
   207	        for f in sorted(set(ix) | set(iy)):
   208	            if f in ADAPTER_FIELDS or f == "sessions":
   209	                continue
   210	            if ix.get(f) != iy.get(f):
   211	                if f == RUNNER_FIELD and runner_exception:
   212	                    print(f"  runner exception in force: {x} {ix.get(f)} vs "
   213	                          f"{y} {iy.get(f)} -- {runner_exception}")
   214	                    continue
   215	                problems.append(f"{x} and {y} differ on identity.{f}: "
   216	                                f"{ix.get(f)!r} vs {iy.get(f)!r}")
   217	    trained = [a for a in arms if idents[a].get("adapter_steps")]
   218	    if len(trained) > 1:
   219	        steps = {a: idents[a]["adapter_steps"] for a in trained}
   220	        if len(set(steps.values())) > 1:
   221	            problems.append(f"trained arms are not step-matched: {steps}")
   222	    return arms, data, idents, problems
   223	
   224	
   225	def main(argv=None):
   226	    ap = argparse.ArgumentParser(description=__doc__)
   227	    ap.add_argument("paths", nargs="+")
   228	    ap.add_argument("--runner-exception", default="",
   229	                    help="reason a runner_sha256 difference is admissible")
   230	    ap.add_argument("--allow-problems", action="store_true",
   231	                    help="print the table anyway, with every problem restated")
   232	    a = ap.parse_args(argv)
   233	
   234	    print("validating before comparing")
   235	    arms, data, idents, problems = validate(a.paths, a.runner_exception)
   236	    if problems:
   237	        print("\n  REFUSING TO COMPARE -- fix these first:")
   238	        for p in problems:
   239	            print(f"    * {p}")
   240	        if not a.allow_problems:
   241	            return 1
   242	        print("\n  --allow-problems given; every number below is suspect")
   243	    else:
   244	        print("  identity, completeness, uniqueness and replay all verified")
   245	    self_check()  # a measure that cannot pass is not evidence of failure
   246	    scored, ctrl = {}, {}
   247	    for arm in arms:
   248	        scored[arm], ctrl[arm] = score_arm(data[arm][1])
   249	
   250	    shared = sorted(set.intersection(*(set(scored[x]) for x in arms)))
   251	    print(f"\npaired on {len(shared)} sessions whose convention CHANGED "
   252	          f"(arms: {', '.join(arms)})")
   253	
   254	    print("\n  category counts, fixed denominator")
   255	    print(f"    {'arm':6} " + "  ".join(f"{c:>14}" for c in CATS))
   256	    for x in arms:
   257	        row = Counter(scored[x][s]["cat"] for s in shared)
   258	        print(f"    {x:6} " + "  ".join(f"{row[c]:>14}" for c in CATS))
   259	
   260	    outcomes = {
   261	        "contract IN FORCE": lambda r: r["cat"] == "in-force",
   262	        "IN FORCE *and* functional":
   263	            lambda r: r["cat"] == "in-force" and r["functional"],
   264	        "followed the SUPERSEDED convention": lambda r: r["cat"] == "alt",
   265	        "function_only": lambda r: r["function_only"],
   266	        "all six suites at request 2": lambda r: r["j"],
   267	    }
   268	    n = len(shared)
   269	    for label, hit in outcomes.items():
   270	        print(f"\n  '{label}'")
   271	        for x in arms:
   272	            print(f"    {x:6} {sum(hit(scored[x][s]) for s in shared):3d}/{n}")
   273	        for x, y in combinations(arms, 2):
   274	            b = sum(1 for s in shared if hit(scored[y][s]) and not hit(scored[x][s]))
   275	            c = sum(1 for s in shared if hit(scored[x][s]) and not hit(scored[y][s]))
   276	            lo, hi = paired_interval(b, c, n)
   277	            print(f"      {y} vs {x}: {y}-only {b}, {x}-only {c}   net {b - c:+d}   "
   278	                  f"exact McNemar p={mcnemar_exact(b, c):.4f}   "
   279	                  f"95% paired interval [{100 * lo:+.1f}, {100 * hi:+.1f}] pts")
   280	
   281	    cshared = sorted(set.intersection(*(set(ctrl[x]) for x in arms)))
   282	    if cshared:
   283	        print("\n  DESCRIPTIVE control: the same outcome where the convention did NOT")
   284	        print("  change.  Reported side by side only; the populations also differ in")
   285	        print("  project, lifecycle and request text, and 12 sessions cannot resolve a")
   286	        print("  difference of differences, so no causal reading is attached.")
   287	        for x in arms:
   288	            ch = sum(1 for s in shared if scored[x][s]["cat"] == "in-force")
   289	            un = sum(1 for s in cshared if ctrl[x][s]["cat"] == "in-force")
   290	            print(f"    {x:6} changed {ch}/{len(shared)}   "
   291	                  f"unchanged {un}/{len(cshared)}")
   292	
   293	    print("\n  every session whose category moved")
   294	    for x, y in combinations(arms, 2):
   295	        for s in shared:
   296	            if scored[x][s]["cat"] != scored[y][s]["cat"]:
   297	                print(f"    {s}: {x}={scored[x][s]['cat']:10} -> "
   298	                      f"{y}={scored[y][s]['cat']:10} "
   299	                      f"(functional {scored[x][s]['functional']} -> "
   300	                      f"{scored[y][s]['functional']})")
   301	    return 0
   302	
   303	
   304	if __name__ == "__main__":
   305	    sys.exit(main())
     1	"""Refuse to launch an evaluation whose adapter the runner would reject.
     2	
     3	a_screen_run.py validates the training log's recorded hashes against the CURRENT
     4	files (trainer, a_screen, a_train_pool, trunk) and against the frozen pools.
     5	Every one of those is a file I might edit between training and evaluation, and
     6	the failure arrives only after the GPU hours are spent -- which is exactly how
     7	the minimum-duration guard would have cost four hours.  This checks the same
     8	things first, in a second, on the CPU.
     9	
    10	Rewritten 2026-09-13 after Astra's back-on-track review found the guard passing
    11	on things it was built to catch.  Its 13/13 mutation run established nothing,
    12	because with synthetic metadata it accepted
    13	
    14	  * an SFT objective sitting in the CF directory -- nothing tied the log's
    15	    `objective` to the arm the caller intended, so a mislabelled or overwritten
    16	    directory would have been evaluated as the other arm;
    17	  * a log with no `hub` field at all -- the trunk check read `ident.get("hub")`
    18	    and simply did not run when it was absent;
    19	  * two logs missing the same field in `--compare`, because `None == None`, so
    20	    every absent field counted as agreement.
    21	
    22	The rule this version follows: a check that cannot run is a FAILURE, never a
    23	pass.  `need()` asserts presence before any comparison, the caller must name the
    24	arm it believes it is evaluating, and `--compare` runs the full individual
    25	validation on both adapters before it looks at them side by side.
    26	
    27	    python preflight.py check   <dir> --arm cf  [--require-steps N] [--hub PATH]
    28	    python preflight.py compare <dir> <dir> --arms sft cf [--hub PATH]
    29	"""
    30	
    31	import argparse
    32	import hashlib
    33	import json
    34	import sys
    35	from pathlib import Path
    36	
    37	ROOT = Path("/home/bmarti44/stencil-llm")
    38	sys.path.insert(0, str(ROOT / "src"))
    39	from stencil import a_screen as A  # noqa: E402
    40	
    41	REGISTERED = {
    42	    "seed": 0, "lr": 1e-4, "rank": 16, "alpha": 32,
    43	    "beta": 0.1, "dpo_weight": 0.1, "accum": 8,
    44	}
    45	REGISTERED_BUDGET_S = 4 * 3600
    46	ARMS = ("sft", "cf")
    47	HASH_FIELDS = (
    48	    ("trainer_sha256", ROOT / "scripts/a_screen_train.py"),
    49	    ("a_screen_sha256", ROOT / "src/stencil/a_screen.py"),
    50	    ("a_train_pool_sha256", ROOT / "src/stencil/a_train_pool.py"),
    51	)
    52	SHARED_IDENTITY = ("trainer_sha256", "a_screen_sha256", "a_train_pool_sha256",
    53	                   "hub", "hub_sha256", "train_pool_sha256")
    54	
    55	
    56	def sha(text: str) -> str:
    57	    return hashlib.sha256(text.encode()).hexdigest()[:16]
    58	
    59	
    60	def need(d, key, bad, where):
    61	    """Presence first.  A missing field is a refusal, never a silent agreement."""
    62	    if key not in d or d[key] is None:
    63	        bad.append(f"{where}: {key} is missing")
    64	        return None
    65	    return d[key]
    66	
    67	
    68	def check(adapter: str, arm: str, require_steps: int = 0, hub: str = "") -> list[str]:
    69	    """Problems with one adapter.  Empty list means eligible."""
    70	    bad: list[str] = []
    71	    if arm not in ARMS:
    72	        return [f"{arm!r} is not one of {ARMS}"]
    73	    path = Path(adapter) / "train-log.json"
    74	    if not path.exists():
    75	        return [f"{path} does not exist"]
    76	    try:
    77	        log = json.loads(path.read_text())
    78	    except json.JSONDecodeError as e:
    79	        return [f"{path} is not valid JSON ({e})"]
    80	    ident = log.get("identity")
    81	    if not isinstance(ident, dict):
    82	        return [f"{path} has no identity block"]
    83	
    84	    # the arm the caller believes it is evaluating, bound to the log AND the directory
    85	    objective = need(log, "objective", bad, "log")
    86	    if objective is not None and objective != arm:
    87	        bad.append(f"objective {objective!r} but the caller asked for {arm!r}")
    88	    if Path(adapter).name != arm:
    89	        bad.append(f"directory {Path(adapter).name!r} does not name the {arm!r} arm")
    90	
    91	    if not (log.get("final") and log.get("status") == "complete"):
    92	        bad.append(f"final={log.get('final')} status={log.get('status')!r}")
    93	    steps = need(log, "steps", bad, "log")
    94	    if steps is not None and (not isinstance(steps, int) or steps < 1):
    95	        bad.append(f"steps={steps!r}")
    96	    if require_steps and steps != require_steps:
    97	        bad.append(f"steps {steps} != matched {require_steps}")
    98	    if need(log, "budget_seconds", bad, "log") not in (None, REGISTERED_BUDGET_S):
    99	        bad.append(f"budget_seconds={log.get('budget_seconds')}")
   100	    if ident.get("limit"):
   101	        bad.append(f"limit={ident['limit']}")
   102	    if need(log, "examples", bad, "log") == 0:
   103	        bad.append("examples=0")
   104	
   105	    for k, want in REGISTERED.items():
   106	        if need(log, k, bad, "log") not in (None, want):
   107	            bad.append(f"{k}={log.get(k)!r} != {want!r}")
   108	
   109	    for field, file in HASH_FIELDS:
   110	        trained = need(ident, field, bad, "identity")
   111	        if trained is None:
   112	            continue
   113	        cur = sha(file.read_text())
   114	        if trained != cur:
   115	            bad.append(f"{field}: trained {trained}, current {cur} ({file.name})")
   116	
   117	    trunk = need(ident, "hub", bad, "identity")
   118	    trunk_sha = need(ident, "hub_sha256", bad, "identity")
   119	    if trunk is not None:
   120	        if hub and str(Path(hub)) != str(Path(trunk)):
   121	            bad.append(f"trained on trunk {trunk}, evaluating on {hub}")
   122	        on_disk = Path(trunk)
   123	        if not on_disk.is_dir():
   124	            bad.append(f"the trunk {trunk} is not on disk")
   125	        elif trunk_sha is not None and trunk_sha != A.dir_sha(on_disk):
   126	            bad.append("hub_sha256 differs from the trunk on disk")
   127	
   128	    pool = need(ident, "train_pool_sha256", bad, "identity")
   129	    frozen = json.loads(
   130	        (ROOT / "results/a-screen/train-pool.json").read_text()
   131	    )["pool_sha256"]
   132	    if pool is not None and pool != frozen:
   133	        bad.append(f"TRAIN pool {pool} != frozen {frozen}")
   134	
   135	    weights = Path(adapter) / "adapter_model.safetensors"
   136	    if not weights.exists():
   137	        bad.append("adapter_model.safetensors is missing")
   138	    return bad
   139	
   140	
   141	def compare(a_dir: str, b_dir: str, arms, hub: str = "") -> list[str]:
   142	    """Both adapters individually eligible does NOT make them comparable.
   143	
   144	    The peer's point, and it is right: a set of invariants only bounds the axes
   145	    it thinks to assert.  Every check above is one-sided -- "this adapter is a
   146	    valid adapter" -- and none of them looks at the OTHER arm, so two adapters
   147	    could each pass while differing in step count, data, recipe or trunk.  That
   148	    is the axis that decides whether cf-vs-sft means anything, so it is asserted
   149	    here -- and the individual validation is run first, because two adapters
   150	    that agree with each other and with nothing else are not a comparison."""
   151	    bad = []
   152	    for d, arm in zip((a_dir, b_dir), arms):
   153	        bad += [f"{arm}: {p}" for p in check(d, arm, hub=hub)]
   154	    la = json.loads((Path(a_dir) / "train-log.json").read_text())
   155	    lb = json.loads((Path(b_dir) / "train-log.json").read_text())
   156	    ia, ib = la.get("identity", {}), lb.get("identity", {})
   157	
   158	    for k in ("steps", "examples"):
   159	        va, vb = need(la, k, bad, arms[0]), need(lb, k, bad, arms[1])
   160	        if va is not None and vb is not None and va != vb:
   161	            note = " -- NOT step-matched" if k == "steps" else ""
   162	            bad.append(f"{k} {va} vs {vb}{note}")
   163	    oa, ob = need(la, "objective", bad, arms[0]), need(lb, "objective", bad, arms[1])
   164	    if oa is not None and oa == ob:
   165	        bad.append(f"both objectives are {oa!r} -- not a contrast")
   166	    for k in REGISTERED:
   167	        va, vb = need(la, k, bad, arms[0]), need(lb, k, bad, arms[1])
   168	        if va is not None and vb is not None and va != vb:
   169	            bad.append(f"{k}: {va!r} vs {vb!r}")
   170	    for k in SHARED_IDENTITY:
   171	        va, vb = need(ia, k, bad, f"{arms[0]}.identity"), need(ib, k, bad,
   172	                                                              f"{arms[1]}.identity")
   173	        if va is not None and vb is not None and va != vb:
   174	            bad.append(f"{k} differs between arms: {va!r} vs {vb!r}")
   175	    return bad
   176	
   177	
   178	def main(argv=None):
   179	    ap = argparse.ArgumentParser(description=__doc__)
   180	    sub = ap.add_subparsers(dest="cmd", required=True)
   181	    c = sub.add_parser("check")
   182	    c.add_argument("adapter")
   183	    c.add_argument("--arm", required=True, choices=ARMS)
   184	    c.add_argument("--require-steps", type=int, default=0)
   185	    c.add_argument("--hub", default="")
   186	    m = sub.add_parser("compare")
   187	    m.add_argument("adapters", nargs=2)
   188	    m.add_argument("--arms", nargs=2, required=True, choices=ARMS)
   189	    m.add_argument("--hub", default="")
   190	    a = ap.parse_args(argv)
   191	
   192	    if a.cmd == "check":
   193	        bad = check(a.adapter, a.arm, a.require_steps, a.hub)
   194	        if bad:
   195	            print(f"REFUSE {a.arm}: " + "; ".join(bad))
   196	            return 1
   197	        log = json.loads((Path(a.adapter) / "train-log.json").read_text())
   198	        print(f"OK {a.arm}: {log['steps']} optimizer steps over {log['examples']} "
   199	              f"examples, status complete, every hash current")
   200	        return 0
   201	
   202	    if a.arms[0] == a.arms[1]:
   203	        print(f"NOT COMPARABLE: both arms named {a.arms[0]!r}")
   204	        return 1
   205	    bad = compare(a.adapters[0], a.adapters[1], a.arms, a.hub)
   206	    if bad:
   207	        print("NOT COMPARABLE: " + "; ".join(bad))
   208	        return 1
   209	    la = json.loads((Path(a.adapters[0]) / "train-log.json").read_text())
   210	    print(f"COMPARABLE: both {la['steps']} steps over {la['examples']} examples, "
   211	          f"same recipe, same trunk, same pools; objectives "
   212	          f"{a.arms[0]!r} vs {a.arms[1]!r}")
   213	    return 0
   214	
   215	
   216	if __name__ == "__main__":
   217	    sys.exit(main())

web search: "instruction" "revision" "scope" "LLMs" benchmark 2025 2026 ...
codex
The corrected request-1 split matches the pool metadata, but the baseline document still overclaims: low whole-file text similarity does not establish absence of memorisation, and “neither” does not isolate a coding-competence failure. I’m also checking whether the comparison guards validate the frozen design or only agreement between the supplied files.

exec
/bin/bash -lc "nl -ba results/a-screen/analysis/preflight.py | sed -n '80,300p' && nl -ba results/a-screen/analysis/overlap.py && nl -ba results/a-screen/analysis/runner_equivalence.py && nl -ba results/a-screen/RUNNER-EXCEPTION.md" in /home/bmarti44/stencil-llm
 succeeded in 0ms:
    80	    ident = log.get("identity")
    81	    if not isinstance(ident, dict):
    82	        return [f"{path} has no identity block"]
    83	
    84	    # the arm the caller believes it is evaluating, bound to the log AND the directory
    85	    objective = need(log, "objective", bad, "log")
    86	    if objective is not None and objective != arm:
    87	        bad.append(f"objective {objective!r} but the caller asked for {arm!r}")
    88	    if Path(adapter).name != arm:
    89	        bad.append(f"directory {Path(adapter).name!r} does not name the {arm!r} arm")
    90	
    91	    if not (log.get("final") and log.get("status") == "complete"):
    92	        bad.append(f"final={log.get('final')} status={log.get('status')!r}")
    93	    steps = need(log, "steps", bad, "log")
    94	    if steps is not None and (not isinstance(steps, int) or steps < 1):
    95	        bad.append(f"steps={steps!r}")
    96	    if require_steps and steps != require_steps:
    97	        bad.append(f"steps {steps} != matched {require_steps}")
    98	    if need(log, "budget_seconds", bad, "log") not in (None, REGISTERED_BUDGET_S):
    99	        bad.append(f"budget_seconds={log.get('budget_seconds')}")
   100	    if ident.get("limit"):
   101	        bad.append(f"limit={ident['limit']}")
   102	    if need(log, "examples", bad, "log") == 0:
   103	        bad.append("examples=0")
   104	
   105	    for k, want in REGISTERED.items():
   106	        if need(log, k, bad, "log") not in (None, want):
   107	            bad.append(f"{k}={log.get(k)!r} != {want!r}")
   108	
   109	    for field, file in HASH_FIELDS:
   110	        trained = need(ident, field, bad, "identity")
   111	        if trained is None:
   112	            continue
   113	        cur = sha(file.read_text())
   114	        if trained != cur:
   115	            bad.append(f"{field}: trained {trained}, current {cur} ({file.name})")
   116	
   117	    trunk = need(ident, "hub", bad, "identity")
   118	    trunk_sha = need(ident, "hub_sha256", bad, "identity")
   119	    if trunk is not None:
   120	        if hub and str(Path(hub)) != str(Path(trunk)):
   121	            bad.append(f"trained on trunk {trunk}, evaluating on {hub}")
   122	        on_disk = Path(trunk)
   123	        if not on_disk.is_dir():
   124	            bad.append(f"the trunk {trunk} is not on disk")
   125	        elif trunk_sha is not None and trunk_sha != A.dir_sha(on_disk):
   126	            bad.append("hub_sha256 differs from the trunk on disk")
   127	
   128	    pool = need(ident, "train_pool_sha256", bad, "identity")
   129	    frozen = json.loads(
   130	        (ROOT / "results/a-screen/train-pool.json").read_text()
   131	    )["pool_sha256"]
   132	    if pool is not None and pool != frozen:
   133	        bad.append(f"TRAIN pool {pool} != frozen {frozen}")
   134	
   135	    weights = Path(adapter) / "adapter_model.safetensors"
   136	    if not weights.exists():
   137	        bad.append("adapter_model.safetensors is missing")
   138	    return bad
   139	
   140	
   141	def compare(a_dir: str, b_dir: str, arms, hub: str = "") -> list[str]:
   142	    """Both adapters individually eligible does NOT make them comparable.
   143	
   144	    The peer's point, and it is right: a set of invariants only bounds the axes
   145	    it thinks to assert.  Every check above is one-sided -- "this adapter is a
   146	    valid adapter" -- and none of them looks at the OTHER arm, so two adapters
   147	    could each pass while differing in step count, data, recipe or trunk.  That
   148	    is the axis that decides whether cf-vs-sft means anything, so it is asserted
   149	    here -- and the individual validation is run first, because two adapters
   150	    that agree with each other and with nothing else are not a comparison."""
   151	    bad = []
   152	    for d, arm in zip((a_dir, b_dir), arms):
   153	        bad += [f"{arm}: {p}" for p in check(d, arm, hub=hub)]
   154	    la = json.loads((Path(a_dir) / "train-log.json").read_text())
   155	    lb = json.loads((Path(b_dir) / "train-log.json").read_text())
   156	    ia, ib = la.get("identity", {}), lb.get("identity", {})
   157	
   158	    for k in ("steps", "examples"):
   159	        va, vb = need(la, k, bad, arms[0]), need(lb, k, bad, arms[1])
   160	        if va is not None and vb is not None and va != vb:
   161	            note = " -- NOT step-matched" if k == "steps" else ""
   162	            bad.append(f"{k} {va} vs {vb}{note}")
   163	    oa, ob = need(la, "objective", bad, arms[0]), need(lb, "objective", bad, arms[1])
   164	    if oa is not None and oa == ob:
   165	        bad.append(f"both objectives are {oa!r} -- not a contrast")
   166	    for k in REGISTERED:
   167	        va, vb = need(la, k, bad, arms[0]), need(lb, k, bad, arms[1])
   168	        if va is not None and vb is not None and va != vb:
   169	            bad.append(f"{k}: {va!r} vs {vb!r}")
   170	    for k in SHARED_IDENTITY:
   171	        va, vb = need(ia, k, bad, f"{arms[0]}.identity"), need(ib, k, bad,
   172	                                                              f"{arms[1]}.identity")
   173	        if va is not None and vb is not None and va != vb:
   174	            bad.append(f"{k} differs between arms: {va!r} vs {vb!r}")
   175	    return bad
   176	
   177	
   178	def main(argv=None):
   179	    ap = argparse.ArgumentParser(description=__doc__)
   180	    sub = ap.add_subparsers(dest="cmd", required=True)
   181	    c = sub.add_parser("check")
   182	    c.add_argument("adapter")
   183	    c.add_argument("--arm", required=True, choices=ARMS)
   184	    c.add_argument("--require-steps", type=int, default=0)
   185	    c.add_argument("--hub", default="")
   186	    m = sub.add_parser("compare")
   187	    m.add_argument("adapters", nargs=2)
   188	    m.add_argument("--arms", nargs=2, required=True, choices=ARMS)
   189	    m.add_argument("--hub", default="")
   190	    a = ap.parse_args(argv)
   191	
   192	    if a.cmd == "check":
   193	        bad = check(a.adapter, a.arm, a.require_steps, a.hub)
   194	        if bad:
   195	            print(f"REFUSE {a.arm}: " + "; ".join(bad))
   196	            return 1
   197	        log = json.loads((Path(a.adapter) / "train-log.json").read_text())
   198	        print(f"OK {a.arm}: {log['steps']} optimizer steps over {log['examples']} "
   199	              f"examples, status complete, every hash current")
   200	        return 0
   201	
   202	    if a.arms[0] == a.arms[1]:
   203	        print(f"NOT COMPARABLE: both arms named {a.arms[0]!r}")
   204	        return 1
   205	    bad = compare(a.adapters[0], a.adapters[1], a.arms, a.hub)
   206	    if bad:
   207	        print("NOT COMPARABLE: " + "; ".join(bad))
   208	        return 1
   209	    la = json.loads((Path(a.adapters[0]) / "train-log.json").read_text())
   210	    print(f"COMPARABLE: both {la['steps']} steps over {la['examples']} examples, "
   211	          f"same recipe, same trunk, same pools; objectives "
   212	          f"{a.arms[0]!r} vs {a.arms[1]!r}")
   213	    return 0
   214	
   215	
   216	if __name__ == "__main__":
   217	    sys.exit(main())
     1	"""How close is the screen's gold to the training pool's gold?
     2	
     3	Decision-relevant, CPU-only, and prompted by the cf training curve: the run
     4	reached CE 0.0006 while `epochs_completed` was still 0, so every example it
     5	learned on was UNSEEN when it trained on it.  A near-zero loss on fresh examples
     6	means the gold completion is close to determined by the prefix under this
     7	generator.  If the screen's gold is also close to the training pool's gold, then
     8	an adapter that wins the screen may be reproducing a template it has already
     9	been fitted to, and the win would not be evidence about tracking which
    10	convention is in force.
    11	
    12	This measures the thing directly, with no model: for every SCREEN gold (48
    13	sessions x 2 requests x 2 states) find the most similar TRAIN gold (576 x 2 x 2)
    14	and report the distribution of that maximum.  Two measures, because either alone
    15	is easy to fool:
    16	
    17	  jaccard   over identifier/keyword tokens -- catches "same code, renamed"
    18	  ratio     difflib on the source text, on the jaccard top-8 only -- catches
    19	            "same text, reordered"
    20	
    21	Read it as: a max similarity near 1.0 across the board means the screen is
    22	largely a memorisation test.  A spread well below 1.0 means the screen asks for
    23	code the adapter has not been shown.  Neither reading is a pass/fail gate; it is
    24	a caveat that must travel with any positive result.
    25	
    26	    uv run python results/a-screen/analysis/overlap.py
    27	"""
    28	
    29	import re
    30	import statistics
    31	import sys
    32	from difflib import SequenceMatcher
    33	
    34	sys.path.insert(0, "/home/bmarti44/stencil-llm/src")
    35	from stencil.a_screen_pool import screen_sessions  # noqa: E402
    36	from stencil.a_train_pool import train_sessions  # noqa: E402
    37	
    38	TOKEN = re.compile(r"[A-Za-z_][A-Za-z_0-9]*")
    39	TOPK = 8
    40	
    41	
    42	def tokens(src):
    43	    return frozenset(TOKEN.findall(src))
    44	
    45	
    46	def golds(sessions):
    47	    out = []
    48	    for s in sessions:
    49	        for k, req in enumerate(s.requests, 1):
    50	            for state, src in sorted(req.gold.items()):
    51	                out.append((s.id, k, state, s.target_family, src, tokens(src)))
    52	    return out
    53	
    54	
    55	def main():
    56	    screen = golds(screen_sessions())
    57	    train = golds(train_sessions())
    58	    print(f"{len(screen)} screen golds vs {len(train)} train golds")
    59	
    60	    rows = []
    61	    for sid, k, state, family, src, toks in screen:
    62	        scored = []
    63	        for tid, _, _, tfam, tsrc, ttoks in train:
    64	            inter = len(toks & ttoks)
    65	            if not inter:
    66	                continue
    67	            scored.append((inter / len(toks | ttoks), tsrc, tid, tfam))
    68	        scored.sort(reverse=True, key=lambda x: x[0])
    69	        best_j = scored[0][0] if scored else 0.0
    70	        best_r, best_id, best_fam = 0.0, "-", "-"
    71	        for _j, tsrc, tid, tfam in scored[:TOPK]:
    72	            r = SequenceMatcher(None, src, tsrc).ratio()
    73	            if r > best_r:
    74	                best_r, best_id, best_fam = r, tid, tfam
    75	        rows.append((sid, k, state, family, best_j, best_r, best_id, best_fam))
    76	
    77	    for name, idx in (("token jaccard", 4), ("difflib ratio", 5)):
    78	        vals = sorted(r[idx] for r in rows)
    79	        n = len(vals)
    80	        print(f"\n  max {name} to ANY training gold, over {n} screen golds")
    81	        print(f"    min {vals[0]:.3f}   p25 {vals[n // 4]:.3f}   "
    82	              f"median {statistics.median(vals):.3f}   p75 {vals[3 * n // 4]:.3f}   "
    83	              f"max {vals[-1]:.3f}")
    84	        for bar in (0.95, 0.90, 0.80, 0.70):
    85	            print(f"    >= {bar:.2f}: {sum(1 for v in vals if v >= bar):3d}/{n}")
    86	
    87	    print("\n  by family (median of the max difflib ratio)")
    88	    fams = sorted({r[3] for r in rows})
    89	    for f in fams:
    90	        vals = [r[5] for r in rows if r[3] == f]
    91	        print(f"    {f:16s} n={len(vals):3d}  median {statistics.median(vals):.3f}  "
    92	              f"max {max(vals):.3f}")
    93	
    94	    print("\n  the 10 closest screen golds (the memorisation risk, if any)")
    95	    for row in sorted(rows, key=lambda r: -r[5])[:10]:
    96	        sid, k, state, family, j, r, tid, tfam = row
    97	        print(f"    {sid} req{k} {state:10s} {family:14s} ratio {r:.3f} "
    98	              f"jaccard {j:.3f}  nearest {tid} ({tfam})")
    99	
   100	
   101	if __name__ == "__main__":
   102	    main()
     1	"""Why the `off` baseline does not need re-running on the current runner.
     2	
     3	The baseline (results/a-screen/runs/off-oldrunner.jsonl) records
     4	runner_sha256 4acdb8f044c25a48.  The current runner hashes differently, and
     5	compare.py refuses a runner_sha256 mismatch unless --runner-exception states the
     6	reason.  This script IS the reason, recomputed rather than asserted:
     7	
     8	  1. the two files' differences are confined to the bodies of `if a.adapter:`
     9	     and to one added `ap.add_argument("--require-steps", ..., default=0)`;
    10	  2. only one of the two adapter guards actually changed;
    11	  3. `a.require_steps` is read nowhere except inside an adapter guard, and its
    12	     default is falsy;
    13	
    14	so an adapterless run -- which never enters `if a.adapter:` -- executes the same
    15	program under both runners.  Anything the script cannot confirm is printed as a
    16	FAILURE and exits non-zero; nothing here is taken on trust.
    17	
    18	    python results/a-screen/analysis/runner_equivalence.py [OLD_REV]
    19	"""
    20	
    21	import ast
    22	import hashlib
    23	import subprocess
    24	import sys
    25	from pathlib import Path
    26	
    27	ROOT = Path(__file__).resolve().parents[3]
    28	RUNNER = ROOT / "scripts/a_screen_run.py"
    29	BASELINE_RUNNER_SHA = "4acdb8f044c25a48"
    30	DEFAULT_REV = "86282371"
    31	
    32	
    33	def sha16(text):
    34	    return hashlib.sha256(text.encode()).hexdigest()[:16]
    35	
    36	
    37	def is_adapter_guard(node):
    38	    return (
    39	        isinstance(node, ast.If)
    40	        and isinstance(node.test, ast.Attribute)
    41	        and node.test.attr == "adapter"
    42	        and isinstance(node.test.value, ast.Name)
    43	        and node.test.value.id == "a"
    44	    )
    45	
    46	
    47	def is_require_steps_option(node):
    48	    if not (isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)):
    49	        return False
    50	    call = node.value
    51	    return (
    52	        isinstance(call.func, ast.Attribute)
    53	        and call.func.attr == "add_argument"
    54	        and call.args
    55	        and isinstance(call.args[0], ast.Constant)
    56	        and call.args[0].value == "--require-steps"
    57	    )
    58	
    59	
    60	class Strip(ast.NodeTransformer):
    61	    """Empty every adapter guard and drop the --require-steps option, keeping a
    62	    record of the guard bodies so they can be compared one by one."""
    63	
    64	    def __init__(self):
    65	        self.guard_bodies = []
    66	        self.options_removed = 0
    67	
    68	    def visit_If(self, node):
    69	        self.generic_visit(node)
    70	        if is_adapter_guard(node):
    71	            self.guard_bodies.append(
    72	                "\n".join(ast.dump(x) for x in node.body)
    73	            )
    74	            return ast.If(test=node.test, body=[ast.Pass()], orelse=[])
    75	        return node
    76	
    77	    def visit_Expr(self, node):
    78	        if is_require_steps_option(node):
    79	            self.options_removed += 1
    80	            return None
    81	        return node
    82	
    83	
    84	def strip(src):
    85	    t = Strip()
    86	    tree = t.visit(ast.parse(src))
    87	    ast.fix_missing_locations(tree)
    88	    return ast.dump(tree), t
    89	
    90	
    91	def require_steps_reads_outside_guard(src):
    92	    """Every `a.require_steps` load that is NOT lexically inside an adapter guard."""
    93	    tree = ast.parse(src)
    94	    inside = set()
    95	    for node in ast.walk(tree):
    96	        if is_adapter_guard(node):
    97	            for sub in node.body:
    98	                for x in ast.walk(sub):
    99	                    inside.add(id(x))
   100	    out = []
   101	    for node in ast.walk(tree):
   102	        if (
   103	            isinstance(node, ast.Attribute)
   104	            and node.attr == "require_steps"
   105	            and isinstance(node.value, ast.Name)
   106	            and node.value.id == "a"
   107	            and id(node) not in inside
   108	        ):
   109	            out.append(node.lineno)
   110	    return out
   111	
   112	
   113	def main(rev=DEFAULT_REV):
   114	    new_src = RUNNER.read_text()
   115	    old_src = subprocess.run(
   116	        ["git", "-C", str(ROOT), "show", f"{rev}:scripts/a_screen_run.py"],
   117	        capture_output=True, text=True, check=True,
   118	    ).stdout
   119	
   120	    failures = []
   121	    print(f"old runner ({rev}) sha16 {sha16(old_src)}")
   122	    print(f"current runner        sha16 {sha16(new_src)}")
   123	    if sha16(old_src) != BASELINE_RUNNER_SHA:
   124	        failures.append(
   125	            f"{rev} hashes {sha16(old_src)}, not the {BASELINE_RUNNER_SHA} the "
   126	            f"baseline records -- this is not the runner that produced it"
   127	        )
   128	
   129	    old_dump, old_t = strip(old_src)
   130	    new_dump, new_t = strip(new_src)
   131	    print(f"adapter guards: old {len(old_t.guard_bodies)}, "
   132	          f"new {len(new_t.guard_bodies)}")
   133	    print(f"--require-steps options removed: old {old_t.options_removed}, "
   134	          f"new {new_t.options_removed}")
   135	
   136	    if old_dump != new_dump:
   137	        failures.append(
   138	            "the runners differ OUTSIDE the adapter guards and the added option"
   139	        )
   140	    else:
   141	        print("outside those sites the two runners are AST-identical: True")
   142	
   143	    if len(old_t.guard_bodies) != len(new_t.guard_bodies):
   144	        failures.append("the runners have different numbers of adapter guards")
   145	    else:
   146	        differing = [
   147	            i for i, (o, n) in enumerate(zip(old_t.guard_bodies, new_t.guard_bodies))
   148	            if o != n
   149	        ]
   150	        print(f"adapter guard bodies that differ: {differing} "
   151	              f"of {len(old_t.guard_bodies)}")
   152	
   153	    stray = require_steps_reads_outside_guard(new_src)
   154	    if stray:
   155	        failures.append(f"a.require_steps is read outside an adapter guard at {stray}")
   156	    else:
   157	        print("a.require_steps is read only inside an adapter guard: True")
   158	
   159	    print()
   160	    if failures:
   161	        print("FAILURE -- the exception is NOT established:")
   162	        for f in failures:
   163	            print(f"  * {f}")
   164	        return 1
   165	    print("ESTABLISHED: an adapterless run executes the same program under both")
   166	    print("runners, so results/a-screen/runs/off-oldrunner.jsonl needs no re-run.")
   167	    return 0
   168	
   169	
   170	if __name__ == "__main__":
   171	    sys.exit(main(*sys.argv[1:]))
     1	# Runner exception: the `off` baseline is not re-run
     2	
     3	**Recorded 2026-09-13.  Status: ESTABLISHED by recomputation, not by assertion.**
     4	
     5	`results/a-screen/runs/off-oldrunner.jsonl` records
     6	`identity.runner_sha256 = 4acdb8f044c25a48`.  The current runner hashes
     7	`f27bc5bc0690a918`, because on 2026-09-13 the adapter's minimum-elapsed-time
     8	guard was replaced with a completion/step-count guard and a `--require-steps`
     9	option was added.  `results/a-screen/analysis/compare.py` refuses a
    10	`runner_sha256` mismatch between arms; this file is the exception it requires,
    11	and the reason must be passed explicitly:
    12	
    13	```
    14	python results/a-screen/analysis/compare.py <off> <arm> \
    15	  --runner-exception "results/a-screen/RUNNER-EXCEPTION.md, verified by runner_equivalence.py"
    16	```
    17	
    18	## What was verified
    19	
    20	```
    21	python results/a-screen/analysis/runner_equivalence.py
    22	```
    23	
    24	reports, against `git show 86282371:scripts/a_screen_run.py`:
    25	
    26	```
    27	old runner (86282371) sha16 4acdb8f044c25a48      <- the hash the baseline records
    28	current runner        sha16 f27bc5bc0690a918
    29	adapter guards: old 2, new 2
    30	--require-steps options removed: old 0, new 1
    31	outside those sites the two runners are AST-identical: True
    32	adapter guard bodies that differ: [0] of 2
    33	a.require_steps is read only inside an adapter guard: True
    34	```
    35	
    36	So every difference between the two runners lies in
    37	
    38	1. the body of the **first** `if a.adapter:` guard (the second guard is
    39	   unchanged), and
    40	2. one added `ap.add_argument("--require-steps", ..., default=0)`, whose value is
    41	   read nowhere except inside an adapter guard and whose default is falsy.
    42	
    43	The baseline was produced with no `--adapter`, so it never entered either guard.
    44	Under both runners it executes the same program, and re-running it would consume
    45	about 1 GPU-hour to reproduce bytes that are already established to be identical
    46	in origin.
    47	
    48	## What this exception does NOT cover
    49	
    50	* It says nothing about a **trained** arm.  Any arm with an adapter runs the
    51	  changed guard and must be produced by the current runner; comparing two
    52	  trained arms across runner versions is not covered here.
    53	* It is not a licence to compare across any other identity field.  `compare.py`
    54	  still refuses a mismatch in pool, `a_screen`, contracts, hub, prompt budget,
    55	  `max_new`, deadline or session set, and `tests/test_a_screen_compare_guard.py`
    56	  exercises each of those refusals.
    57	* If `scripts/a_screen_run.py` changes again, this file is void until
    58	  `runner_equivalence.py` is re-run and reports ESTABLISHED against the new
    59	  file.  It exits non-zero when it cannot confirm the claim.

web search: 
web search: https://arxiv.org/abs/2609.03340
exec
/bin/bash -lc "nl -ba results/a-screen/adapters/cf/train-log.json | sed -n '1,200p' && nl -ba scripts/a_screen_train.py | sed -n '150,240p' && nl -ba scripts/a_screen_train.py | sed -n '310,450p' && nl -ba src/stencil/a_screen.py | sed -n '340,530p'" in /home/bmarti44/stencil-llm
 succeeded in 0ms:
     1	{
     2	 "objective": "cf",
     3	 "identity": {
     4	  "train_pool_sha256": "b8f504494a281858",
     5	  "a_screen_sha256": "639b59d5b4e6200d",
     6	  "a_train_pool_sha256": "57e22a7b46ff9da9",
     7	  "trainer_sha256": "688ab01a9a1faac3",
     8	  "hub": "/home/bmarti44/stencil-llm/deploy/stencil_focus/build/hub-4b",
     9	  "hub_sha256": "d42d871fc77f9847",
    10	  "limit": 0
    11	 },
    12	 "seed": 0,
    13	 "lr": 0.0001,
    14	 "rank": 16,
    15	 "alpha": 32,
    16	 "beta": 0.1,
    17	 "dpo_weight": 0.1,
    18	 "accum": 8,
    19	 "examples": 1152,
    20	 "budget_seconds": 14400.0,
    21	 "prep_seconds": 71.98683195293415,
    22	 "reference_seconds": 1855.242353559006,
    23	 "reference_tokens": 7004126,
    24	 "steps": 134,
    25	 "micro_steps": 1078,
    26	 "discarded_micro_steps": 6,
    27	 "epochs_completed": 0,
    28	 "completion_tokens_seen": 627694,
    29	 "chosen_tokens_seen": 3277473,
    30	 "rejected_tokens_seen": 3277461,
    31	 "sequence_tokens_seen": 6554934,
    32	 "final_update_loss": 0.0001408661725008642,
    33	 "loss_history": [
    34	  [
    35	   10,
    36	   0.14341629883856513
    37	  ],
    38	  [
    39	   20,
    40	   0.06984200029305612
    41	  ],
    42	  [
    43	   30,
    44	   0.030246336393156527
    45	  ],
    46	  [
    47	   40,
    48	   0.015378149607499836
    49	  ],
    50	  [
    51	   50,
    52	   0.006637048649622557
    53	  ],
    54	  [
    55	   60,
    56	   0.0036410280562051865
    57	  ],
    58	  [
    59	   70,
    60	   0.002337199512510324
    61	  ],
    62	  [
    63	   80,
    64	   0.0012076665217819027
    65	  ],
    66	  [
    67	   90,
    68	   0.0005929183022090001
    69	  ],
    70	  [
    71	   100,
    72	   0.000961018323243934
    73	  ],
    74	  [
    75	   110,
    76	   0.00097720904268499
    77	  ],
    78	  [
    79	   120,
    80	   0.0009171515560353783
    81	  ],
    82	  [
    83	   130,
    84	   0.00027022683811992463
    85	  ]
    86	 ],
    87	 "status": "complete",
    88	 "max_steps": 0,
    89	 "stopped_on": "budget",
    90	 "margin_history": [
    91	  [
    92	   10,
    93	   0.6367982377138105
    94	  ],
    95	  [
    96	   20,
    97	   2.771859698696062
    98	  ],
    99	  [
   100	   30,
   101	   4.623576681036502
   102	  ],
   103	  [
   104	   40,
   105	   6.04146198630333
   106	  ],
   107	  [
   108	   50,
   109	   7.472609466593712
   110	  ],
   111	  [
   112	   60,
   113	   6.398736055195331
   114	  ],
   115	  [
   116	   70,
   117	   7.863031029701233
   118	  ],
   119	  [
   120	   80,
   121	   8.187135550379754
   122	  ],
   123	  [
   124	   90,
   125	   8.87749108672142
   126	  ],
   127	  [
   128	   100,
   129	   8.449146369099617
   130	  ],
   131	  [
   132	   110,
   133	   8.620466327667236
   134	  ],
   135	  [
   136	   120,
   137	   9.577399176359176
   138	  ],
   139	  [
   140	   130,
   141	   8.799309322237969
   142	  ]
   143	 ],
   144	 "seconds": 14398.55446686002,
   145	 "save_seconds": 1.6648400198901072,
   146	 "final": true,
   147	 "train_seconds": 12459.141914025997
   148	}
   150	    examples = build_examples(tok, a.limit)
   151	    lens = [
   152	        len(e["prompt_ids"]) + max(len(e["chosen_ids"]), len(e["rejected_ids"]))
   153	        for e in examples
   154	    ]
   155	    print(
   156	        f"examples={len(examples)} max_len={max(lens)} mean_len={sum(lens) / len(lens):.0f}"
   157	    )
   158	    assert max(lens) <= 4096, "a training sequence exceeds the 4,096-token window"
   159	
   160	    model = AutoModelForCausalLM.from_pretrained(
   161	        a.hub, trust_remote_code=True, dtype=torch.bfloat16, device_map="cuda"
   162	    )
   163	    model.config.use_cache = False
   164	    dev = model.device
   165	
   166	    def seq_logprobs(
   167	        m, prompt_ids: list[int], comp_ids: list[int]
   168	    ) -> tuple[torch.Tensor, int]:
   169	        """(sum of completion-token log-probs, n completion tokens)."""
   170	        ids = torch.tensor([prompt_ids + comp_ids], device=dev)
   171	        logits = (
   172	            m(input_ids=ids, attention_mask=torch.ones_like(ids)).logits[0, :-1].float()
   173	        )
   174	        targets = ids[0, 1:]
   175	        lp = torch.log_softmax(logits, dim=-1).gather(1, targets[:, None])[:, 0]
   176	        n = len(comp_ids)
   177	        return lp[-n:].sum(), n
   178	
   179	    # ---- reference log-probs (cf only), adapter absent, counted in the allocation
   180	    prep_seconds = time.monotonic() - t_start
   181	    ref: dict[int, tuple[float, float]] = {}
   182	    ref_tokens = 0
   183	    t_ref = time.monotonic()
   184	    if a.objective == "cf":
   185	        model.eval()
   186	        with torch.no_grad():
   187	            for i, e in enumerate(examples):
   188	                # Astra F13: reference scoring lives inside the allocation and must not
   189	                # consume all of it; a run that cannot fit it is cost-ineligible.
   190	                if time.monotonic() - t_start >= budget_s:
   191	                    # re-review F13: §8's reading for an exhausted allocation is INCOMPLETE.
   192	                    # No adapter exists yet, so the marker is the train log the harness
   193	                    # reads: status "incomplete" and final false both refuse evaluation.
   194	                    out.mkdir(parents=True, exist_ok=True)
   195	                    (out / "train-log.json").write_text(
   196	                        json.dumps(
   197	                            {
   198	                                "objective": a.objective,
   199	                                "status": "incomplete",
   200	                                "final": False,
   201	                                "steps": 0,
   202	                                "budget_seconds": budget_s,
   203	                                "reference_examples_scored": i,
   204	                                "incomplete_reason": (
   205	                                    "reference scoring exhausted the allocation"
   206	                                ),
   207	                            },
   208	                            indent=1,
   209	                        )
   210	                        + "\n"
   211	                    )
   212	                    print(
   213	                        "INCOMPLETE: reference scoring exhausted the allocation; "
   214	                        "no adapter from this allocation may be evaluated"
   215	                    )
   216	                    sys.exit(3)
   217	                c, _ = seq_logprobs(model, e["prompt_ids"], e["chosen_ids"])
   218	                r, _ = seq_logprobs(model, e["prompt_ids"], e["rejected_ids"])
   219	                ref[i] = (c.item(), r.item())
   220	                ref_tokens += (
   221	                    2 * len(e["prompt_ids"])
   222	                    + len(e["chosen_ids"])
   223	                    + len(e["rejected_ids"])
   224	                )
   225	                if i % 100 == 0:
   226	                    print(f"ref {i}/{len(examples)} {time.monotonic() - t_start:.0f}s")
   227	        print(f"reference scoring done in {time.monotonic() - t_ref:.0f}s")
   228	    reference_seconds = time.monotonic() - t_ref
   229	
   230	    cfg = LoraConfig(
   231	        r=a.rank,
   232	        lora_alpha=a.alpha,
   233	        lora_dropout=0.0,
   234	        target_modules=TARGET_MODULES,
   235	        task_type="CAUSAL_LM",
   236	    )
   237	    model = get_peft_model(model, cfg)
   238	    for _n, p in model.named_parameters():
   239	        if p.requires_grad:
   240	            p.data = p.data.float()
   310	        elif log.get("steps", 0) < 1:
   311	            log["status"] = "incomplete"
   312	        elif log["seconds"] > budget_s:
   313	            # Round 4 F13: the final save can finish past the allocation (a save starting at
   314	            # 14,390 s of a 14,400 s budget and taking 30 s wrote seconds=14,420 and still
   315	            # claimed "complete", and the harness's runtime check is a lower bound only).
   316	            # An allocation that ends beyond its registered budget is over_budget, and the
   317	            # harness refuses it.
   318	            log["status"] = "over_budget"
   319	            log["over_budget_s"] = log["seconds"] - budget_s
   320	        else:
   321	            log["status"] = "complete"
   322	        (out / "train-log.json").write_text(json.dumps(log, indent=1) + "\n")
   323	
   324	    model.train()
   325	    rng = random.Random(a.seed)
   326	    order = list(range(len(examples)))
   327	    micro = 0
   328	    last_save = time.monotonic()
   329	    window: list[float] = []
   330	    update: list[float] = []
   331	    ce_only: list[float] = []
   332	    margins: list[float] = []
   333	    micro_times: list[float] = []
   334	    step_times: list[float] = []
   335	    stop = False
   336	    t_train = time.monotonic()
   337	    while not stop:
   338	        rng.shuffle(order)
   339	        for i in order:
   340	            # Astra F13: stop BEFORE a micro-step that would cross the allocation
   341	            elapsed = time.monotonic() - t_start
   342	            # re-review round 3 F13: the estimate covers a micro-step AND the optimizer step
   343	            # that may follow it; the reserve covers the final save.
   344	            est = max(micro_times[-20:], default=0.0) + max(
   345	                step_times[-20:], default=0.0
   346	            )
   347	            reserve = max(save_times) if save_times else 60.0
   348	            if elapsed + est + reserve >= budget_s:
   349	                stop = True
   350	                break
   351	            t_micro = time.monotonic()
   352	            e = examples[i]
   353	            with torch.autocast("cuda", dtype=torch.bfloat16):
   354	                lp_c, n_c = seq_logprobs(model, e["prompt_ids"], e["chosen_ids"])
   355	                loss = -lp_c / n_c
   356	                if a.objective == "cf":
   357	                    lp_r, _ = seq_logprobs(model, e["prompt_ids"], e["rejected_ids"])
   358	                    rc, rr = ref[i]
   359	                    margin = a.beta * ((lp_c - rc) - (lp_r - rr))
   360	                    loss = loss + a.dpo_weight * (-F.logsigmoid(margin))
   361	                    # Astra 2026-09-13: the log reported only the combined loss, so a
   362	                    # preference term that never moved would have been invisible and a
   363	                    # null uninterpretable.  Both parts are already computed here.
   364	                    ce_only.append(float(-lp_c / n_c))
   365	                    margins.append(float(margin))
   366	            (loss / a.accum).backward()
   367	            micro += 1
   368	            # Round 4 F13: loss.item() synchronises with the device, so reading it AFTER the
   369	            # timestamp left that synchronisation outside the measured micro-step and made
   370	            # the stop estimate optimistic.  Read it first, then close the measurement.
   371	            loss_value = loss.item()
   372	            micro_times.append(time.monotonic() - t_micro)
   373	            log["micro_steps"] = micro
   374	            log["completion_tokens_seen"] += n_c
   375	            log["chosen_tokens_seen"] += len(e["prompt_ids"]) + n_c
   376	            if a.objective == "cf":
   377	                log["rejected_tokens_seen"] += len(e["prompt_ids"]) + len(
   378	                    e["rejected_ids"]
   379	                )
   380	            log["sequence_tokens_seen"] = (
   381	                log["chosen_tokens_seen"] + log["rejected_tokens_seen"]
   382	            )
   383	            window.append(loss_value)
   384	            update.append(loss_value)
   385	            if micro % a.accum == 0:
   386	                t_step = time.monotonic()
   387	                torch.nn.utils.clip_grad_norm_(params, 1.0)
   388	                opt.step()
   389	                opt.zero_grad(set_to_none=True)
   390	                step_times.append(time.monotonic() - t_step)
   391	                log["steps"] += 1
   392	                if a.max_steps and log["steps"] >= a.max_steps:
   393	                    log["stopped_on"] = "max_steps"
   394	                    stop = True
   395	                # re-review F6: the mean over THIS update's micro-steps.  ``window`` is the
   396	                # ten-update print window and clears only every tenth update, so reusing it
   397	                # here reported the average of up to ten updates as the final one.
   398	                log["final_update_loss"] = sum(update) / len(update)
   399	                update = []
   400	                if log["steps"] % 10 == 0:
   401	                    avg = sum(window) / len(window)
   402	                    log["loss_history"].append([log["steps"], avg])
   403	                    extra = ""
   404	                    if ce_only:
   405	                        extra = (
   406	                            f" ce {sum(ce_only) / len(ce_only):.4f}"
   407	                            f" margin {sum(margins) / len(margins):+.4f}"
   408	                        )
   409	                        log.setdefault("margin_history", []).append(
   410	                            [log["steps"], sum(margins) / len(margins)]
   411	                        )
   412	                        ce_only, margins = [], []
   413	                    print(
   414	                        f"step {log['steps']} loss {avg:.4f}{extra} micro {micro} "
   415	                        f"{time.monotonic() - t_start:.0f}s/{budget_s:.0f}s"
   416	                    )
   417	                    window = []
   418	                # re-review round 3 F13: a periodic save must not consume the allowance
   419	                # reserved for the final one, so it only runs with room for BOTH.
   420	                room = budget_s - (time.monotonic() - t_start)
   421	                if time.monotonic() - last_save > a.save_every_min * 60 and room > 2 * (
   422	                    max(save_times) if save_times else 60.0
   423	                ):
   424	                    save(final=False)
   425	                    last_save = time.monotonic()
   426	            if stop:
   427	                break
   428	        else:
   429	            log["epochs_completed"] += 1
   430	    # discard any partial accumulation: the FINAL COMPLETED update is the adapter
   431	    log["discarded_micro_steps"] = micro % a.accum
   432	    log["train_seconds"] = time.monotonic() - t_train
   433	    opt.zero_grad(set_to_none=True)
   434	    save(final=True)
   435	    print(
   436	        f"DONE objective={a.objective} steps={log['steps']} epochs={log['epochs_completed']} "
   437	        f"discarded={log['discarded_micro_steps']} tokens={log['sequence_tokens_seen']} "
   438	        f"final_loss={log['final_update_loss']} seconds={log['seconds']:.0f}"
   439	    )
   440	
   441	
   442	if __name__ == "__main__":
   443	    main()
   340	                holder, attr = name.split(".", 1)
   341	                owner = getattr(module, holder, None)
   342	                ok = owner is not None and hasattr(owner, attr)
   343	            else:
   344	                ok = hasattr(module, name)
   345	            if not ok:
   346	                missing.append(module_path + ":" + name)
   347	    assert not missing, "public bindings gone: " + repr(missing)
   348	'''
   349	
   350	
   351	def api_test(session: Session) -> dict[str, str]:
   352	    """A generated test asserting that every public name bound before the live requests is
   353	    still RESOLVABLE on the imported module (Astra F7, re-review F17).
   354	
   355	    The first implementation compared AST definition names, which rejected legitimate
   356	    implementations (``count = _count`` inside the class, or an inherited method) while
   357	    establishing nothing about behaviour.  A runtime binding check accepts any shape that
   358	    actually exposes the name, and deletion still fails.  Behaviour preservation is the job
   359	    of the PROTECTED regression and functional suites, not of this check."""
   360	    spec: dict[str, list[str]] = {}
   361	    for path in sorted({r.target for r in session.requests}):
   362	        names = sorted(public_api(session.files.get(path, "")))
   363	        if names:
   364	            spec[path[:-3].replace("/", ".")] = names
   365	    return {"test_public_api_preserved.py": _API_TEST.format(spec=repr(spec))}
   366	
   367	
   368	def score_checkpoint(session: Session, k: int, files: dict[str, str]) -> dict:
   369	    """Run every applicable suite at checkpoint ``k`` (1 or 2) on ``files``.  At
   370	    checkpoint 2 the PROTECTED suite re-runs request 1's functional, contract (under the
   371	    state in force at checkpoint 1) and support tests."""
   372	    r = session.requests[k - 1]
   373	    state = session.state_at[k - 1]
   374	    out: dict = {"state": state}
   375	    suites = [
   376	        ("functional", r.functional_tests),
   377	        ("regression", r.regression_tests),
   378	        ("contract", r.contract_tests[state]),
   379	        ("support", r.support_tests),
   380	    ]
   381	    # Re-review F16: the protected group is scored in TWO parts so that contract
   382	    # compliance never enters the function-only measurement.  ``protected_function`` is
   383	    # request 1's functional and regression tests plus the public-binding check;
   384	    # ``protected_contract`` is its contract and support tests.  Re-review F7: request 1's
   385	    # REGRESSION tests were missing, which awarded a verified false J.
   386	    if k == 2:
   387	        r1 = session.requests[0]
   388	        s1 = session.state_at[0]
   389	        pf, pc = {}, {}
   390	        for group in (r1.functional_tests, r1.regression_tests, api_test(session)):
   391	            for name, content in group.items():
   392	                pf[f"protected_{name}"] = content
   393	        for group in (r1.contract_tests[s1], r1.support_tests):
   394	            for name, content in group.items():
   395	                pc[f"protected_{name}"] = content
   396	        suites.append(("protected_function", pf))
   397	        suites.append(("protected_contract", pc))
   398	    else:
   399	        # at checkpoint 1 only the pre-existing public bindings can already be gone
   400	        suites.append(("protected_function", api_test(session)))
   401	        out["protected_contract"] = True
   402	        out["protected_contract_msg"] = "n/a"
   403	    for name, tests in suites:
   404	        ok, msg = run_tests(files, tests, timeout=SUITE_TIMEOUT_S)
   405	        out[name] = ok
   406	        out[f"{name}_msg"] = msg
   407	    out["protected"] = bool(out["protected_function"] and out["protected_contract"])
   408	    out["all"] = all(out[n] for n in SUITES)
   409	    out["function_only"] = bool(
   410	        out["functional"] and out["regression"] and out["protected_function"]
   411	    )
   412	    return out
   413	
   414	
   415	def apply_reply(
   416	    files: dict[str, str], request: Request, reply: str
   417	) -> tuple[dict[str, str] | None, str]:
   418	    """Apply the model's reply (a fenced file) to the repository.  Returns the new
   419	    repository or ``None`` with the terminal reason."""
   420	    content = extract_file(reply)
   421	    if content is None:
   422	        return None, "parse_failure"
   423	    if not content.strip():
   424	        return None, "empty"
   425	    try:
   426	        compile(content, request.target, "exec")
   427	    except SyntaxError:
   428	        return None, "syntax_error"
   429	    return {**files, request.target: content}, "applied"
   430	
   431	
   432	def gold_files(session: Session, k: int, state: str | None = None) -> dict[str, str]:
   433	    """Repository after applying the gold answers up to checkpoint ``k`` (each under the
   434	    state in force, or ``state`` for the last one)."""
   435	    files = dict(session.files)
   436	    for i in range(k):
   437	        r = session.requests[i]
   438	        s = session.state_at[i] if (i < k - 1 or state is None) else state
   439	        files[r.target] = r.gold[s]
   440	    return files
   441	
   442	
   443	def gold_reply(session: Session, k: int, state: str | None = None) -> str:
   444	    r = session.requests[k - 1]
   445	    s = state or session.state_at[k - 1]
   446	    return f"```python\n{r.gold[s].rstrip()}\n```"
   447	
   448	
   449	# ------------------------------------------------------------------ training pairs
   450	
   451	
   452	@dataclass(frozen=True)
   453	class Pair:
   454	    session: str
   455	    variant: str  # "event" | "irrelevant"
   456	    messages: tuple[dict[str, str], ...]  # unpacked prompt (packed at training time)
   457	    chosen: str
   458	    rejected: str
   459	    chosen_state: str
   460	    rejected_state: str
   461	
   462	
   463	def pairs_from_session(session: Session) -> list[Pair]:
   464	    """Two counterfactual pairs per training session at checkpoint 2: the history with
   465	    the lifecycle event (chosen = gold under the state then in force, rejected = gold under
   466	    the stale state) and the irrelevant-history variant (chosen = gold under the unchanged
   467	    state, rejected = gold under the other state).  Both directions are executable gold."""
   468	    s1, s2 = session.state_at
   469	    files0 = dict(session.files)
   470	    files1 = gold_files(session, 1)
   471	    reply1 = gold_reply(session, 1)
   472	    r2 = session.requests[1]
   473	    out = []
   474	    ev = session_messages(session, 2, files0, reply1, files1)
   475	    stale2 = s1 if s2 != s1 else session.other(s2)
   476	    out.append(
   477	        Pair(
   478	            session.id,
   479	            "event",
   480	            tuple(ev),
   481	            gold_text(r2, s2),
   482	            gold_text(r2, stale2),
   483	            s2,
   484	            stale2,
   485	        )
   486	    )
   487	    if session.irrelevant_event:
   488	        ir = session_messages(
   489	            session, 2, files0, reply1, files1, event=session.irrelevant_event
   490	        )
   491	        out.append(
   492	            Pair(
   493	                session.id,
   494	                "irrelevant",
   495	                tuple(ir),
   496	                gold_text(r2, s1),
   497	                gold_text(r2, session.other(s1)),
   498	                s1,
   499	                session.other(s1),
   500	            )
   501	        )
   502	    return out
   503	
   504	
   505	def gold_text(request: Request, state: str) -> str:
   506	    return f"```python\n{request.gold[state].rstrip()}\n```"
   507	
   508	
   509	def make_counter(tok) -> Callable[[list[dict[str, str]]], int]:
   510	    """Token counter over the shipping chat template (thinking disabled, generation
   511	    prompt appended), the exact prompt the harness feeds the model."""
   512	
   513	    def count(msgs: list[dict[str, str]]) -> int:
   514	        text = tok.apply_chat_template(
   515	            msgs, add_generation_prompt=True, tokenize=False, enable_thinking=False
   516	        )
   517	        return len(tok(text, add_special_tokens=False)["input_ids"])
   518	
   519	    return count
   520	
   521	
   522	def render_prompt(tok, msgs: list[dict[str, str]]) -> str:
   523	    return tok.apply_chat_template(
   524	        msgs, add_generation_prompt=True, tokenize=False, enable_thinking=False
   525	    )
   526	
   527	
   528	def file_sha(path: Path) -> str:
   529	    """Streaming sha256 of a file's actual bytes (first 16 hex chars)."""
   530	    h = hashlib.sha256()

exec
/bin/bash -lc "nl -ba tests/test_a_screen_compare_guard.py | sed -n '1,260p' && nl -ba tests/test_a_screen_preflight_guard.py | sed -n '1,260p' && nl -ba src/stencil/a_train_pool.py | sed -n '830,1010p' && nl -ba results/a-screen/REGISTRATION-A-SCREEN.md | sed -n '1,145p'" in /home/bmarti44/stencil-llm
 succeeded in 0ms:
     1	"""The comparison guard must BITE, not merely pass.
     2	
     3	Astra's back-on-track review (2026-09-13): the preflight guard's 13/13 mutation
     4	run established nothing, because with synthetic metadata it accepted an SFT
     5	objective sitting in the CF directory and a missing hub field -- the same "passes
     6	by doing nothing" failure the guard existed to prevent.  So every check in
     7	compare.validate() is exercised here through a mutation of the REAL baseline run
     8	file, and each mutation must produce a problem naming that check.  The unmutated
     9	pair must produce none, so the test cannot pass by rejecting everything.
    10	
    11	Validation only; no contract suite is executed, so this test is cheap.
    12	"""
    13	
    14	import json
    15	import sys
    16	from pathlib import Path
    17	
    18	import pytest
    19	
    20	ANALYSIS = Path(__file__).resolve().parents[1] / "results/a-screen/analysis"
    21	BASE = Path(__file__).resolve().parents[1] / "results/a-screen/runs/off-oldrunner.jsonl"
    22	sys.path.insert(0, str(ANALYSIS))
    23	
    24	pytestmark = pytest.mark.skipif(
    25	    not BASE.exists() or not (ANALYSIS / "compare.py").exists(),
    26	    reason="the a-screen baseline run or its analysis is not present",
    27	)
    28	
    29	
    30	def _compare():
    31	    import compare
    32	
    33	    return compare
    34	
    35	
    36	def _rows():
    37	    return [json.loads(x) for x in BASE.read_text().splitlines() if x.strip()]
    38	
    39	
    40	def _write(tmp, name, rows):
    41	    p = tmp / name
    42	    p.write_text("".join(json.dumps(r) + "\n" for r in rows))
    43	    return str(p)
    44	
    45	
    46	def _second_arm(rows, **identity):
    47	    """A synthetic second arm: the baseline relabelled, with adapter fields set.
    48	
    49	    It is a FIXTURE for the guard, never an arm in any comparison; the outcome
    50	    columns are the baseline's own and mean nothing.
    51	    """
    52	    out = []
    53	    for r in rows:
    54	        r = json.loads(json.dumps(r))
    55	        r["arm"] = "sft"
    56	        r["identity"] = dict(
    57	            r["identity"],
    58	            adapter="/fixture/sft",
    59	            adapter_sha256="fixture",
    60	            adapter_steps=118,
    61	            adapter_config_sha256="fixture",
    62	            pilot_adapter=False,
    63	            **identity,
    64	        )
    65	        out.append(r)
    66	    return out
    67	
    68	
    69	@pytest.fixture
    70	def pair(tmp_path):
    71	    rows = _rows()
    72	    return rows, _second_arm(rows)
    73	
    74	
    75	def _validate(tmp_path, a_rows, b_rows, exception=""):
    76	    c = _compare()
    77	    pa = _write(tmp_path, "a.jsonl", a_rows)
    78	    pb = _write(tmp_path, "b.jsonl", b_rows)
    79	    return c.validate([pa, pb], exception)[3]
    80	
    81	
    82	def test_clean_pair_raises_no_problem(tmp_path, pair):
    83	    """The guard must not pass by rejecting everything."""
    84	    a, b = pair
    85	    assert _validate(tmp_path, a, b) == []
    86	
    87	
    88	def test_same_file_twice_is_refused(tmp_path, pair):
    89	    a, _ = pair
    90	    problems = _validate(tmp_path, a, a)
    91	    assert any("appears in two files" in p for p in problems), problems
    92	
    93	
    94	def test_a_single_arm_is_refused(tmp_path, pair):
    95	    a, _ = pair
    96	    c = _compare()
    97	    problems = c.validate([_write(tmp_path, "a.jsonl", a)], "")[3]
    98	    assert any("at least two arms" in p for p in problems), problems
    99	
   100	
   101	def test_a_missing_record_is_refused(tmp_path, pair):
   102	    a, b = pair
   103	    problems = _validate(tmp_path, a, b[:-1])
   104	    assert any("INCOMPLETE" in p for p in problems), problems
   105	
   106	
   107	def test_a_duplicated_record_is_refused(tmp_path, pair):
   108	    a, b = pair
   109	    problems = _validate(tmp_path, a, b + [b[0]])
   110	    assert any("duplicate record" in p for p in problems), problems
   111	
   112	
   113	def test_a_foreign_session_is_refused(tmp_path, pair):
   114	    a, b = pair
   115	    stray = json.loads(json.dumps(b[0]))
   116	    stray["session"] = "S99"
   117	    problems = _validate(tmp_path, a, b + [stray])
   118	    assert any("outside the declared session set" in p for p in problems), problems
   119	
   120	
   121	def test_different_session_sets_are_refused(tmp_path, pair):
   122	    a, b = pair
   123	    b = _second_arm(_rows(), sessions=[s["identity"]["sessions"][0] for s in b[:1]])
   124	    problems = _validate(tmp_path, a, b)
   125	    assert any("different session sets" in p for p in problems), problems
   126	
   127	
   128	@pytest.mark.parametrize(
   129	    "field", ["pool_sha256", "a_screen_sha256", "contracts_sha256", "hub_sha256",
   130	              "prompt_budget", "max_new", "deadline_s"]
   131	)
   132	def test_every_non_adapter_identity_field_is_checked(tmp_path, pair, field):
   133	    a, _ = pair
   134	    b = _second_arm(_rows(), **{field: "MUTATED"})
   135	    problems = _validate(tmp_path, a, b)
   136	    assert any(f"identity.{field}" in p for p in problems), (field, problems)
   137	
   138	
   139	def test_a_missing_identity_field_is_refused(tmp_path, pair):
   140	    """Astra's exact preflight defect: a field that is absent must not compare equal."""
   141	    a, _ = pair
   142	    b = _second_arm(_rows())
   143	    for r in b:
   144	        r["identity"].pop("hub_sha256")
   145	    problems = _validate(tmp_path, a, b)
   146	    assert any("identity.hub_sha256" in p for p in problems), problems
   147	
   148	
   149	def test_runner_difference_needs_the_recorded_exception(tmp_path, pair):
   150	    a, _ = pair
   151	    b = _second_arm(_rows(), runner_sha256="MUTATED")
   152	    assert any("identity.runner_sha256" in p for p in _validate(tmp_path, a, b))
   153	    assert _validate(tmp_path, a, b, "the recorded AST-equivalence exception") == []
   154	
   155	
   156	def test_unequal_training_steps_are_refused(tmp_path):
   157	    rows = _rows()
   158	    a = _second_arm(rows)
   159	    for r in a:
   160	        r["arm"] = "cf"
   161	        r["identity"]["adapter_steps"] = 118
   162	    b = _second_arm(rows)
   163	    for r in b:
   164	        r["identity"]["adapter_steps"] = 95
   165	    problems = _validate(tmp_path, a, b)
   166	    assert any("step-matched" in p for p in problems), problems
   167	
   168	
   169	def test_a_broken_repository_chain_is_refused(tmp_path, pair):
   170	    a, b = pair
   171	    b = json.loads(json.dumps(b))
   172	    b[1]["repo_before"] = "0" * 16
   173	    problems = _validate(tmp_path, a, b)
   174	    assert any("replay disagrees" in p for p in problems), problems
   175	
   176	
   177	def test_mixed_arm_labels_in_one_file_are_refused(tmp_path, pair):
   178	    a, b = pair
   179	    b = json.loads(json.dumps(b))
   180	    b[3]["arm"] = "cf"
   181	    problems = _validate(tmp_path, a, b)
   182	    assert any("mixes arms" in p for p in problems), problems
   183	
   184	
   185	def test_identity_drift_inside_one_file_is_refused(tmp_path, pair):
   186	    a, b = pair
   187	    b = json.loads(json.dumps(b))
   188	    b[5]["identity"]["prompt_budget"] = 9999
   189	    problems = _validate(tmp_path, a, b)
   190	    assert any("identity differs from the first record" in p for p in problems), (
   191	        problems
   192	    )
   193	
   194	
   195	def test_an_unparsable_line_is_refused(tmp_path, pair):
   196	    a, b = pair
   197	    pa = _write(tmp_path, "a.jsonl", a)
   198	    pb = tmp_path / "b.jsonl"
   199	    pb.write_text("".join(json.dumps(r) + "\n" for r in b) + "{not json\n")
   200	    problems = _compare().validate([pa, str(pb)], "")[3]
   201	    assert any("unparsable" in p for p in problems), problems
     1	"""The adapter preflight must BITE, not merely pass.
     2	
     3	Astra's back-on-track review (2026-09-13) found the first version's 13/13
     4	mutation run worthless: with synthetic metadata the guard accepted an SFT
     5	objective sitting in the CF directory, and a log with no `hub` field at all,
     6	because the trunk check simply did not run when the field was absent.  In
     7	--compare, two logs missing the same field counted as agreement, since
     8	`None == None`.
     9	
    10	Every one of those is a case here, along with one mutation per check.  The
    11	unmutated fixture must pass, so the suite cannot succeed by refusing everything.
    12	"""
    13	
    14	import json
    15	import sys
    16	from pathlib import Path
    17	
    18	import pytest
    19	
    20	ROOT = Path(__file__).resolve().parents[1]
    21	ANALYSIS = ROOT / "results/a-screen/analysis"
    22	REAL = ROOT / "results/a-screen/adapters/cf/train-log.json"
    23	sys.path.insert(0, str(ANALYSIS))
    24	
    25	pytestmark = pytest.mark.skipif(
    26	    not REAL.exists() or not (ANALYSIS / "preflight.py").exists(),
    27	    reason="no a-screen training log to build the fixture from",
    28	)
    29	
    30	
    31	def _preflight():
    32	    import preflight
    33	
    34	    return preflight
    35	
    36	
    37	def _base_log():
    38	    """The real cf log, completed.  Its hashes are the current files' hashes, so
    39	    an unmutated fixture must be accepted."""
    40	    log = json.loads(REAL.read_text())
    41	    log["final"] = True
    42	    log["status"] = "complete"
    43	    log["stopped_on"] = "budget"
    44	    return log
    45	
    46	
    47	def _adapter(tmp_path, arm, log):
    48	    d = tmp_path / arm
    49	    d.mkdir(exist_ok=True)
    50	    (d / "train-log.json").write_text(json.dumps(log))
    51	    (d / "adapter_model.safetensors").write_bytes(b"fixture")
    52	    return str(d)
    53	
    54	
    55	@pytest.fixture
    56	def clean(tmp_path):
    57	    return _adapter(tmp_path, "cf", _base_log())
    58	
    59	
    60	def test_the_unmutated_fixture_is_accepted(clean):
    61	    assert _preflight().check(clean, "cf") == []
    62	
    63	
    64	def test_the_real_in_progress_checkpoint_is_refused():
    65	    """The live guard on the live directory: a running checkpoint is not eligible."""
    66	    log = json.loads(REAL.read_text())
    67	    if log.get("final"):
    68	        pytest.skip("training has finished; the in-progress case no longer exists")
    69	    bad = _preflight().check(str(REAL.parent), "cf")
    70	    assert any("status" in p for p in bad), bad
    71	
    72	
    73	def test_an_sft_objective_in_the_cf_directory_is_refused(tmp_path):
    74	    """Astra's first exact defect."""
    75	    log = _base_log()
    76	    log["objective"] = "sft"
    77	    bad = _preflight().check(_adapter(tmp_path, "cf", log), "cf")
    78	    assert any("objective 'sft'" in p for p in bad), bad
    79	
    80	
    81	def test_a_missing_hub_field_is_refused(tmp_path):
    82	    """Astra's second exact defect: the check that cannot run must not pass."""
    83	    log = _base_log()
    84	    log["identity"].pop("hub")
    85	    bad = _preflight().check(_adapter(tmp_path, "cf", log), "cf")
    86	    assert any("hub is missing" in p for p in bad), bad
    87	
    88	
    89	@pytest.mark.parametrize("field", ["hub_sha256", "train_pool_sha256", "trainer_sha256",
    90	                                   "a_screen_sha256", "a_train_pool_sha256"])
    91	def test_a_missing_identity_field_is_refused(tmp_path, field):
    92	    log = _base_log()
    93	    log["identity"].pop(field)
    94	    bad = _preflight().check(_adapter(tmp_path, "cf", log), "cf")
    95	    assert any(f"{field} is missing" in p for p in bad), (field, bad)
    96	
    97	
    98	@pytest.mark.parametrize("field", ["hub_sha256", "train_pool_sha256", "trainer_sha256",
    99	                                   "a_screen_sha256", "a_train_pool_sha256"])
   100	def test_a_stale_identity_hash_is_refused(tmp_path, field):
   101	    log = _base_log()
   102	    log["identity"][field] = "0" * 16
   103	    bad = _preflight().check(_adapter(tmp_path, "cf", log), "cf")
   104	    assert bad, field
   105	
   106	
   107	@pytest.mark.parametrize("key", ["seed", "lr", "rank", "alpha", "beta",
   108	                                 "dpo_weight", "accum"])
   109	def test_every_registered_recipe_value_is_checked(tmp_path, key):
   110	    log = _base_log()
   111	    log[key] = 12345
   112	    bad = _preflight().check(_adapter(tmp_path, "cf", log), "cf")
   113	    assert any(key in p for p in bad), (key, bad)
   114	
   115	
   116	@pytest.mark.parametrize("key", ["seed", "lr", "rank", "alpha", "beta",
   117	                                 "dpo_weight", "accum", "steps", "examples",
   118	                                 "budget_seconds", "objective"])
   119	def test_every_registered_recipe_value_must_be_present(tmp_path, key):
   120	    log = _base_log()
   121	    log.pop(key)
   122	    bad = _preflight().check(_adapter(tmp_path, "cf", log), "cf")
   123	    assert any(f"{key} is missing" in p for p in bad), (key, bad)
   124	
   125	
   126	def test_an_unfinished_run_is_refused(tmp_path):
   127	    log = _base_log()
   128	    log["status"] = "running"
   129	    log["final"] = False
   130	    assert _preflight().check(_adapter(tmp_path, "cf", log), "cf")
   131	
   132	
   133	def test_zero_steps_is_refused(tmp_path):
   134	    log = _base_log()
   135	    log["steps"] = 0
   136	    bad = _preflight().check(_adapter(tmp_path, "cf", log), "cf")
   137	    assert any("steps" in p for p in bad), bad
   138	
   139	
   140	def test_an_unmatched_step_count_is_refused(clean):
   141	    real = json.loads(REAL.read_text())["steps"]
   142	    bad = _preflight().check(clean, "cf", require_steps=real + 1)
   143	    assert any("matched" in p for p in bad), bad
   144	
   145	
   146	def test_a_wrong_allocation_is_refused(tmp_path):
   147	    log = _base_log()
   148	    log["budget_seconds"] = 600
   149	    bad = _preflight().check(_adapter(tmp_path, "cf", log), "cf")
   150	    assert any("budget_seconds" in p for p in bad), bad
   151	
   152	
   153	def test_a_truncated_pool_is_refused(tmp_path):
   154	    log = _base_log()
   155	    log["identity"]["limit"] = 8
   156	    bad = _preflight().check(_adapter(tmp_path, "cf", log), "cf")
   157	    assert any("limit" in p for p in bad), bad
   158	
   159	
   160	def test_a_directory_that_does_not_name_the_arm_is_refused(tmp_path):
   161	    bad = _preflight().check(_adapter(tmp_path, "sft", _base_log()), "sft")
   162	    assert any("objective" in p for p in bad), bad
   163	
   164	
   165	def test_a_different_evaluation_trunk_is_refused(clean):
   166	    bad = _preflight().check(clean, "cf", hub="/some/other/trunk")
   167	    assert any("evaluating on" in p for p in bad), bad
   168	
   169	
   170	def test_missing_weights_are_refused(tmp_path):
   171	    d = _adapter(tmp_path, "cf", _base_log())
   172	    Path(d, "adapter_model.safetensors").unlink()
   173	    bad = _preflight().check(d, "cf")
   174	    assert any("safetensors" in p for p in bad), bad
   175	
   176	
   177	def test_a_missing_log_is_refused(tmp_path):
   178	    assert _preflight().check(str(tmp_path / "cf"), "cf")
   179	
   180	
   181	def test_an_unparsable_log_is_refused(tmp_path):
   182	    d = tmp_path / "cf"
   183	    d.mkdir()
   184	    (d / "train-log.json").write_text("{not json")
   185	    assert _preflight().check(str(d), "cf")
   186	
   187	
   188	# ----------------------------------------------------------------- compare
   189	
   190	
   191	def _pair(tmp_path, mutate_sft=None, mutate_cf=None):
   192	    sft, cf = _base_log(), _base_log()
   193	    sft["objective"] = "sft"
   194	    for log, mut in ((sft, mutate_sft), (cf, mutate_cf)):
   195	        if mut:
   196	            mut(log)
   197	    a = _adapter(tmp_path, "sft", sft)
   198	    b = _adapter(tmp_path, "cf", cf)
   199	    return a, b
   200	
   201	
   202	def test_a_clean_pair_is_comparable(tmp_path):
   203	    a, b = _pair(tmp_path)
   204	    assert _preflight().compare(a, b, ("sft", "cf")) == []
   205	
   206	
   207	def test_two_logs_missing_the_same_field_are_not_agreement(tmp_path):
   208	    """Astra's third exact defect: None == None counted as a match."""
   209	    drop = lambda log: log["identity"].pop("hub_sha256")  # noqa: E731
   210	    a, b = _pair(tmp_path, drop, drop)
   211	    bad = _preflight().compare(a, b, ("sft", "cf"))
   212	    assert any("hub_sha256 is missing" in p for p in bad), bad
   213	
   214	
   215	def test_identical_objectives_are_not_a_contrast(tmp_path):
   216	    a, b = _pair(tmp_path, lambda log: log.update(objective="cf"))
   217	    bad = _preflight().compare(a, b, ("sft", "cf"))
   218	    assert any("not a contrast" in p for p in bad), bad
   219	
   220	
   221	def test_unmatched_steps_are_refused(tmp_path):
   222	    a, b = _pair(tmp_path, lambda log: log.update(steps=log["steps"] - 7))
   223	    bad = _preflight().compare(a, b, ("sft", "cf"))
   224	    assert any("NOT step-matched" in p for p in bad), bad
   225	
   226	
   227	def test_unequal_example_counts_are_refused(tmp_path):
   228	    a, b = _pair(tmp_path, lambda log: log.update(examples=99))
   229	    bad = _preflight().compare(a, b, ("sft", "cf"))
   230	    assert any("examples" in p for p in bad), bad
   231	
   232	
   233	def test_a_differing_trunk_is_refused(tmp_path):
   234	    a, b = _pair(tmp_path, lambda log: log["identity"].update(hub="/other"))
   235	    bad = _preflight().compare(a, b, ("sft", "cf"))
   236	    assert any("hub" in p for p in bad), bad
   237	
   238	
   239	def test_compare_runs_the_individual_validation(tmp_path):
   240	    """A pair that agrees with each other and with nothing else is not a comparison."""
   241	    a, b = _pair(tmp_path, lambda log: log.update(status="running", final=False),
   242	                 lambda log: log.update(status="running", final=False))
   243	    bad = _preflight().compare(a, b, ("sft", "cf"))
   244	    assert any("status" in p for p in bad), bad
   245	
   246	
   247	def test_compare_refuses_one_directory_named_twice(tmp_path):
   248	    a, _ = _pair(tmp_path)
   249	    assert _preflight().main(["compare", a, a, "--arms", "sft", "sft"]) == 1
   250	
   251	
   252	def test_cli_check_returns_zero_on_the_clean_fixture(tmp_path, capsys):
   253	    d = _adapter(tmp_path, "cf", _base_log())
   254	    assert _preflight().main(["check", d, "--arm", "cf"]) == 0
   255	    assert "OK cf" in capsys.readouterr().out
   256	
   257	
   258	def test_cli_check_returns_one_on_a_mutation(tmp_path, capsys):
   259	    log = _base_log()
   260	    log["objective"] = "sft"
   830	    "Reminder to self more than to you: the backup of the old spreadsheet lives in the shared drive, folder 'archive-2025'.",
   831	]
   832	
   833	# --------------------------------------------------------------------------- chatter
   834	
   835	# Six user/assistant pairs of realistic project talk with placeholders; four are drawn
   836	# for turns 0-7 and two short ones for turns 12-15.
   837	_CHATTER: list[tuple[str, str]] = [
   838	    (
   839	        'I\'m starting {pkg}, a small in-process package for {what}. It is deliberately tiny: a frozen {Entity} dataclass, a {Store} that keeps records in a dict, and an optional Backend that writes records somewhere durable. Before we add operations, can you draft the README scope section? I want to head off the \'why not a database\' conversation, and I want the persistence story stated honestly: the Backend is a hook, not a promise.\n\nThe usage I have in mind:\n\n```python\nfrom {pkg}.model import {Entity}\nfrom {pkg}.store import {Store}\n\nbook = {Store}()\nbook.add({Entity}("x1", "alpha"))\nprint(book.find("x1"))\n```',
   840	        "Here is a scope section that says exactly that:\n\n```\n## Scope\n{pkg} keeps {Entity} records for {what} inside one process. Records live in a {Store}; an optional Backend receives each updated record so a caller can persist it, but {pkg} itself has no storage, no locking and no concurrency guarantees.\n\n## Non-goals\n- multi-process access\n- query language\n- schema migrations\n```\n\nThe non-goals list is what people actually read, and it makes the Backend hook look like what it is: a callback with an OSError contract, not a database.",
   841	    ),
   842	    (
   843	        'Question on the model. {Entity} is a frozen dataclass with name, owner, level, slot, note, site, priority, tags and status. Operations will produce updated copies with dataclasses.replace. Someone suggested making it mutable to \'save allocations\'. I don\'t buy it, but give me the argument I can paste into the review thread.\n\nFor reference this is the whole thing:\n\n```python\n@dataclass(frozen=True)\nclass {Entity}:\n    {entity}_id: str\n    name: str\n    owner: str = ""\n    level: int = 0\n    slot: int = 1\n    note: str = ""\n    site: str = "main"\n    priority: int = 0\n    tags: tuple[str, ...] = field(default_factory=tuple)\n    status: str = "active"\n```',
   844	        "The argument is about aliasing, not allocations. With a frozen record, `find` can hand the stored object to a caller and nothing the caller does can change the store; every operation goes through the store and produces a new record, so the store is the single writer. With a mutable record, any caller holding a reference can edit the store silently, and the Backend would never hear about it. The allocation cost is a few hundred bytes per operation on a package whose volume is measured in records per day. Keep it frozen; if profiling ever shows replace() as a hotspot, that is the day to revisit, and it will not come.",
   845	    ),
   846	    (
   847	        'I wrote a first test for add/find and it passes, but I am unsure about the fixture style. Here is what I have:\n\n```python\nimport pytest\n\nfrom {pkg}.model import {Entity}\nfrom {pkg}.store import {Store}\n\n\n@pytest.fixture\ndef book():\n    s = {Store}()\n    s.add({Entity}("x1", "alpha"))\n    s.add({Entity}("x2", "beta", status="archived"))\n    return s\n\n\ndef test_find_returns_stored_record(book):\n    assert book.find("x1").name == "alpha"\n\n\ndef test_find_unknown_is_none(book):\n    assert book.find("nope") is None\n```\n\nShould the archived record be in the default fixture, or is that going to confuse every future test?',
   848	        "Keep it in the fixture. Almost every operation we add will need to be exercised on an active record and an archived one, and having both present by default means each test names what it uses (`x1` active, `x2` archived) instead of building state. The only thing I would change is the fixture name: `book` is fine here, but a helper function `_store()` that returns the populated store is easier to reuse from tests that need their own Backend instance, because a fixture cannot take a constructor argument without indirection. Both are fine; pick one and keep it.",
   849	    ),
   850	    (
   851	        'I hit this while poking at the Backend from the REPL and want to make sure it is expected:\n\n```\n>>> from {pkg}.backend import Backend\n>>> b = Backend(failing=True)\n>>> b.write({{"{entity}_id": "x1"}})\nTraceback (most recent call last):\n  File "<stdin>", line 1, in <module>\n  File "{pkg}/backend.py", line 12, in write\n    raise OSError("sink unavailable")\nOSError: sink unavailable\n```\n\nSo the failing flag really does raise OSError on every write. Is that the right exception type, or should it be something package-specific from the start?',
   852	        "That is expected and OSError is the right type for the Backend itself: it stands in for a disk, a socket or a queue, and those raise OSError subclasses in the standard library. Whether the *store* converts it into a package exception is a separate decision that belongs to the store's contract, not to the backend. The Backend's job is to be honest about the failure; the store's job is to decide what callers of the store see. Keeping those two decisions apart is what lets you change the store's policy later without touching the backend or its tests.",
   853	    ),
   854	    (
   855	        'For the morning report I want a helper that prints one line per record, like `x1 alpha [active] owner=dana level=3`. I keep waffling on where it goes: a method on {Store}, a method on {Entity}, or a free function. What would you do?\n\nDraft:\n\n```python\ndef summary(record):\n    return f"{{record.{entity}_id}} {{record.name}} [{{record.status}}] owner={{record.owner}} level={{record.level}}"\n```',
   856	        'Free function, next to the model. A method on {Entity} would tie the record to one rendering; a method on {Store} would make the store know about presentation. As a free function it reads only public fields, so it works on anything the store hands back, and the report script can import it without importing the store. Your draft is fine; I would only add a `tags=` segment when the tuple is non-empty so the line stays short for untagged records:\n\n```python\ndef summary(record) -> str:\n    tags = f" tags={{\',\'.join(record.tags)}}" if record.tags else ""\n    return f"{{record.{entity}_id}} {{record.name}} [{{record.status}}] owner={{record.owner}} level={{record.level}}{{tags}}"\n```',
   857	    ),
   858	    (
   859	        "One design question before the operations land. Every operation will look the same: look the record up, compute an updated copy, store it, hand it to the backend if there is one, return something. I am tempted to write one generic `_update(id, **changes)` and have every public method be a one-liner. Is that premature?\n\nSketch:\n\n```python\ndef _update(self, {entity}_id, **changes):\n    record = self._records[{entity}_id]\n    updated = replace(record, **changes)\n    self._records[{entity}_id] = updated\n    return updated\n```",
   860	        "It is premature, for one concrete reason: the operations are going to differ in exactly the places your sketch hides. Validation, what happens on an unknown id, whether and how the backend failure is surfaced, whether anything is logged, and what is returned are all policy decisions, and we are about to state them as project conventions that may change. A generic `_update` would either grow flags for every policy or push the policy back into each caller. Write each operation out in full with a small module-level `_apply_<verb>` helper for the pure record transformation; the repetition is the point, because it keeps every policy visible where a reviewer looks.",
   861	    ),
   862	]
   863	
   864	_SHORT_CHATTER: list[tuple[str, str]] = [
   865	    (
   866	        "Do we want type hints on the private helpers too, or only on the public surface?",
   867	        "Both. The private helpers are where the record transformation happens and a wrong annotation there is the one a reader most needs to catch. It costs nothing at runtime.",
   868	    ),
   869	    (
   870	        "I will add a CHANGELOG once the first operations land. Any format preference?",
   871	        "Keep a Changelog style: an Unreleased section on top, one bullet per user-visible change, dates in ISO format. No auto-generation from commits; hand-written bullets read better.",
   872	    ),
   873	    (
   874	        "Should the store expose a way to list every record for the report script?",
   875	        "Yes, a plain `all()` returning `list(self._records.values())` in insertion order. It does not need an ordering argument yet; the report can sort.",
   876	    ),
   877	    (
   878	        "Anything to watch for when we add the first operation?",
   879	        "Only that the request text says what the operation does and the conventions we fixed say how; I will apply both and return the whole store module so you can diff it.",
   880	    ),
   881	]
   882	
   883	# --------------------------------------------------------------------------- sessions
   884	
   885	
   886	def _turns(d: dict[str, str], seed: int) -> tuple[list[Turn], list[Turn]]:
   887	    rng = random.Random(seed)
   888	    long = rng.sample(range(len(_CHATTER)), 4)
   889	    short = rng.sample(range(len(_SHORT_CHATTER)), 2)
   890	    head = []
   891	    for i in long:
   892	        u, a = _CHATTER[i]
   893	        eu, ea = _EXT[i]
   894	        head += [
   895	            Turn("user", (u + eu + _EXT2[i]).format(**d)),
   896	            Turn("assistant", (a + ea).format(**d)),
   897	        ]
   898	    tail = []
   899	    for i in short:
   900	        u, a = _SHORT_CHATTER[i]
   901	        tail += [Turn("user", u.format(**d)), Turn("assistant", a.format(**d))]
   902	    return head, tail
   903	
   904	
   905	def _states_for(
   906	    target: str, lifecycle: str, flip: bool
   907	) -> tuple[tuple[str, str], tuple[str, str]]:
   908	    a, b = STATES[target]
   909	    if flip:
   910	        a, b = b, a
   911	    if lifecycle == "stable":
   912	        return (a, b), (a, a)
   913	    if lifecycle == "reinstatement":
   914	        return (a, b), (b, a)
   915	    return (a, b), (a, b)
   916	
   917	
   918	def make_session(
   919	    target: str,
   920	    support: str,
   921	    lifecycle: str,
   922	    index: int,
   923	) -> Session:
   924	    """Deterministic session ``index`` (0..15) of one cell."""
   925	    assert (
   926	        target in TARGET_FAMILIES
   927	        and support in SUPPORT_FAMILIES
   928	        and lifecycle in LIFECYCLES
   929	    )
   930	    cell = f"{target}|{support}|{lifecycle}"
   931	    seed = int(hashlib.sha256(f"{cell}|{index}".encode()).hexdigest()[:8], 16)
   932	    rng = random.Random(seed)
   933	    d = DOMAINS[(target, support)][index % 2]
   934	    flip = bool((index // 2) % 2)  # which state is the initial one
   935	    precedent_matches_current = bool((index // 4) % 2)  # counterbalance
   936	    states, state_at = _states_for(target, lifecycle, flip)
   937	    support_state = STATES[support][(index // 8) % 2]
   938	    verbs = rng.sample([o.verb for o in OPS], 3)
   939	    existing, op1, op2 = (OP_BY_VERB[v] for v in verbs)
   940	
   941	    def kw(target_state: str) -> dict[str, str]:
   942	        k = {
   943	            "naming": "naming",
   944	            "validation": "validation",
   945	            "missing_record": "missing",
   946	        }[target]
   947	        s = {
   948	            "return_shape": "return_shape",
   949	            "error_surface": "error_surface",
   950	            "logging": "logging_policy",
   951	        }[support]
   952	        return {k: target_state, s: support_state}
   953	
   954	    # the state the existing code shows: "current" = the state in force at checkpoint 2
   955	    current2 = state_at[1]
   956	    stale2 = state_at[0] if lifecycle != "stable" else states[1]
   957	    precedent_state = current2 if precedent_matches_current else stale2
   958	    existing_code = op_code(existing, d, **kw(precedent_state))
   959	    files = {
   960	        f"{d['pkg']}/__init__.py": _init(d),
   961	        f"{d['pkg']}/model.py": _model(d),
   962	        f"{d['pkg']}/backend.py": _backend(d),
   963	        f"{d['pkg']}/errors.py": _errors(d),
   964	        f"{d['pkg']}/store.py": store_file(d, [existing_code]),
   965	    }
   966	    target_path = f"{d['pkg']}/store.py"
   967	
   968	    def request(op: Op, prior: list[tuple[str, str]]) -> Request:
   969	        gold = {st: store_file(d, prior + [op_code(op, d, **kw(st))]) for st in states}
   970	        text = (
   971	            f"Add a public method on {d['Store']} that {op.desc}: it takes the {d['entity']} id and the new "
   972	            f"{op.param} ({op.ptype}), stores the updated record, hands it to the backend when one is configured, "
   973	            f"and returns it. A {op.param} that is not valid ({op.rule}) is rejected with ValueError and nothing is stored."
   974	        )
   975	        return Request(
   976	            text=text,
   977	            target=target_path,
   978	            functional_tests=functional_tests(op, d),
   979	            regression_tests=regression_tests(existing, d),
   980	            contract_tests={st: contract_tests(target, st, op, d) for st in states},
   981	            support_tests=support_tests(support, support_state, op, d),
   982	            gold=gold,
   983	        )
   984	
   985	    req1 = request(op1, [existing_code])
   986	    req2 = request(op2, [existing_code, op_code(op1, d, **kw(state_at[0]))])
   987	
   988	    head, tail = _turns(d, seed)
   989	    sup = support_statement(support, support_state, d)
   990	    if lifecycle == "reinstatement":
   991	        first = target_statement(target, state_at[1], d)  # A, stated first
   992	        interim = replacement_text(target, state_at[0], d)  # then replaced by B
   993	        prefix = (
   994	            head
   995	            + [
   996	                Turn("user", sup),
   997	                Turn("assistant", _ack(sup)),
   998	                Turn("user", first),
   999	                Turn("assistant", _ack(first)),
  1000	                Turn("user", interim),
  1001	                Turn("assistant", _ack(interim)),
  1002	            ]
  1003	            + tail[:2]
  1004	        )
  1005	        rule_turns = (8, 10, 12)
  1006	        event = reinstatement_text(target, state_at[1], d)
  1007	    else:
  1008	        tgt = target_statement(target, state_at[0], d)
  1009	        prefix = (
  1010	            head
     1	# Registration: six-family candidate-A screen (counterfactual LoRA on current-rule execution)
     2	
     3	Registered 2026-09-13 before any project, training pair, adapter or generation exists for
     4	this program. It adopts the minimum registration Astra stated in round 8
     5	(`results/reviews/2026-09-13-direction-adversarial-rev8-astra.md`, items 1–8) without adding
     6	arms, models, benchmarks or review stages. Astra's forecast for this candidate is ~30%
     7	(range 15–45%) artifact success; the owner's bar is 25% (`plan/LEDGER.md` 07:40Z). This is a
     8	SCREEN under a development gate; passing it establishes no efficacy claim. The rev 5
     9	pre-check (`results/contracts/REGISTRATION-PRECHECK.md`) is sealed and INELIGIBLE; nothing
    10	below amends it.
    11	
    12	## 1. Domain and lineage (frozen)
    13	
    14	- Families. Targets T = {naming contract, validation entry, missing-record policy}; supports
    15	  S = {return shape, error surface, logging policy}. Dependency choice and immutability are
    16	  excluded. Exactly one target family changes (or is stable) per session; exactly one
    17	  support family is stated once and never changes.
    18	- Family selection used the pre-check's exploratory per-family summaries (J/8: return shape
    19	  6, error surface 5, logging 4, validation 3, missing-record 2, naming 2) and the dev-set
    20	  precedent probe. That use is recorded here; those 48 tasks and their prompts/responses are
    21	  excluded from every fitting set and are not reused as screen or confirmation projects.
    22	- Three project pools with disjoint NAMES (not disjoint constructions, see §13.3): TRAIN (authored for the
    23	  576 pairs), SCREEN (48 projects, one session each, this document), CONFIRM (reserved,
    24	  authored only if the gate passes, disjoint from both). Disjointness is by project name,
    25	  module path and public class/function name, VERIFIED by `scripts/a_screen_freeze.py`; a hash
    26	  list per pool is committed before the pool is used. Disjoint solution *constructions* are
    27	  NOT claimed and the measured idiom overlap is recorded -- see §13.3 (amendment 1).
    28	- Data lineage: everything is authored 2026-09-13+ for this program; fit-on = TRAIN only;
    29	  evaluated-on = SCREEN only; nothing from `data/bench/`, MemoryCode, the dev16 tasks or the
    30	  32 pre-check tasks enters any pool. No prompt, threshold or checkpoint is tuned on SCREEN.
    31	
    32	## 2. Sessions: N = 48, one per project (frozen manifest)
    33	
    34	`results/a-screen/manifest.json` (sha256 `73d1cded79c5f74f`, produced by
    35	`scripts/a_screen_manifest.py`, deterministic): 3×3 target×support grid, 6 sessions per
    36	diagonal cell and 5 per off-diagonal cell; every target family and every support family has
    37	16 sessions; lifecycle classes stable / replacement / scoped exception / reinstatement have
    38	12 sessions each, each class covering all nine cells. Contract-state variants of one
    39	repository are never separate observations. Projects are authored to the manifest slots
    40	(S01–S48) and frozen by hash before generation.
    41	
    42	## 3. Arms (three, same everything except the adapter)
    43	
    44	| arm | adapter | training data |
    45	|---|---|---|
    46	| `off` | none (adapter bypassed) | — |
    47	| `sft` | LoRA trained with completion cross-entropy only | every positive history/solution used by `cf`: both counterfactual directions and the irrelevant-history variants |
    48	| `cf` | LoRA trained with cross-entropy + 0.1·L_DPO | the same positives plus the stale-alternative preference term |
    49	
    50	Same frozen Qwen3-4B trunk (`deploy/stencil_focus/build/hub-4b` weights), same tokenizer,
    51	chat template with thinking disabled, same session memory and packing policy (§5), same
    52	rendering, generation limits and initial repositories. No teacher, scorer or private test
    53	enters inference.
    54	
    55	## 4. Training intervention (frozen before the screen)
    56	
    57	- Adapter: LoRA rank 16, alpha 32, dropout 0, on all linear projections of attention and MLP;
    58	  AdamW lr 1e-4, weight decay 0, gradient clipping 1.0, seed 0, bf16 trunk frozen.
    59	- `cf` loss: mean cross-entropy over completion tokens of the current-rule gold + 0.1·L_DPO
    60	  with β = 0.1, reference = the frozen trunk (reference log-probs precomputed once and
    61	  counted in the allocation). Chosen = gold executing the CURRENT rule; rejected = the stale
    62	  alternative, which must fail an applicable contract test and must be the executable gold of
    63	  the other rule state (so both directions have executable gold).
    64	- Pairs: 576 authored counterfactual pairs, 16 per (target×support pairing × lifecycle
    65	  class) cell = 36 cells; each history has an irrelevant-history variant (same code, the
    66	  intervening message is contract-irrelevant, gold = the unchanged rule). The convention
    67	  shown by the existing code is counterbalanced: in half of the pairs per cell the in-file
    68	  precedent matches the stale rule, in half it matches the current rule.
    69	- Allocation: a fixed 4-hour wall-clock allocation per adapter on the GB10 under the sharing
    70	  protocol, including reference scoring for `cf`; the FINAL completed optimizer step is the
    71	  adapter (no checkpoint selection, no early stopping on any evaluation). `sft` may make more
    72	  passes over the same positives inside its equal allocation. Actual token exposure, steps
    73	  and GPU-seconds are reported per adapter.
    74	- Every pair's gold and stale alternative are executed against the pair's tests before the
    75	  pool is frozen (self-check identical in kind to `tests/test_contracts.py`).
    76	
    77	## 5. Stateful session protocol (frozen)
    78	
    79	- Each session = a frozen 16-turn prefix (user/assistant turns of ordinary work on the
    80	  project, prior assistant turns authored, not generated) + two LIVE coding requests. The
    81	  arm's first patch is applied to the arm's own copy of the repository (patch = the returned
    82	  target file replacing the target; failure to parse or apply is a failure); the second
    83	  request is rendered from that resulting state.
    84	- The lifecycle event (replacement, scoped exception or reinstatement of the target contract)
    85	  is a user message placed between the two live requests; stable sessions receive a
    86	  contract-irrelevant message there instead. Reinstatement sessions carry the earlier
    87	  replacement inside the prefix.
    88	- Memory/packing policy, common to all arms: prompt = system line + the newest whole turns
    89	  that fit in P = 4,096 − 1,536 = 2,560 tokens, dropped from the oldest turn boundary first
    90	  (compaction). The prefix is authored long enough that compaction drops at least one turn
    91	  before live request 1 and at least one more before live request 2 (exercised in the prefix
    92	  and between requests). No summary, no register and no externally computed "current rule"
    93	  is inserted; whichever historical instruction messages survive the window are exactly what
    94	  reaches the model, and the record lists them per request by turn index. The contract
    95	  statement, the lifecycle message and the support-family statement must survive the window
    96	  at both live requests (checked before generation; a violation is a construction defect
    97	  fixed before the freeze, never after).
    98	- This is a limited history-replay screen; it does not test autonomous long-session
    99	  reliability, and any card will say so.
   100	
   101	## 6. Outcome (one binary per session)
   102	
   103	- J = 1 iff at BOTH live checkpoints the task's functional tests, the protected regression
   104	  tests (existing behaviour that must not break) and ALL applicable contract tests pass in
   105	  the sandbox (`stencil.contracts.run_tests`, scorer runs functional and contract suites
   106	  independently since `src/stencil/contracts.py` sha256 `de0012b279e42c1a`). Function-only
   107	  success = functional + regression at both checkpoints. No partial credit.
   108	- Decoding: one greedy generation per request, thinking disabled, ≤ 1,536 new tokens, prompt
   109	  + reserved output ≤ 4,096. Parse failure, patch-application failure, truncation at the cap,
   110	  timeout (300 s per generation) and abandonment (empty or non-code reply) count as J = 0
   111	  and function-only = 0 for that session. Private tests stay private (never rendered).
   112	
   113	## 7. Development gate (frozen; count rules decide, statistics are reported)
   114	
   115	`cf` passes iff ALL hold:
   116	1. net J wins over `off` ≥ 5 (wins − losses across the 48 paired sessions);
   117	2. net J wins over `sft` ≥ 3;
   118	3. no observed net function-only decline against either comparator (wins − losses ≥ 0);
   119	4. within the 36 changing-rule sessions, net J advantage over `off` > 0 and over `sft` > 0;
   120	5. within replacement, scoped exception and reinstatement separately (12 each), net J
   121	   difference vs each comparator ≥ 0.
   122	
   123	Reported for every contrast: paired wins/losses/ties, two-sided exact McNemar p, and the
   124	conservative 95% paired interval (separate 97.5% Clopper-Pearson bounds on b/N and c/N,
   125	union bound). Power, stated (Astra round 8): at a true 10-point effect N = 48 has roughly
   126	14–23% power under McNemar; the gate is a development screen, not a demonstration. A failed
   127	gate stops this configuration; it does not show equivalence. A passed gate authorises only
   128	the CONFIRM registration (separate document; N and horizon to be set there from the
   129	screen's measured wins, with its own compute ceiling).
   130	
   131	## 8. Compute ceiling (frozen): 16 GPU-hours for the whole screen
   132	
   133	Includes the maximum-context timing pilot (4 sessions × 3 arms at the longest prompts),
   134	both 4-hour trainings, `cf` reference scoring, model loading, and 3 × 48 × 2 = 288
   135	evaluation generations, with the protocol's 1.5 contention factor applied to the pilot's
   136	seconds/request. Pre-check average was 18.8 s/request (short prompts): 288 × 18.8 × 1.5 ≈
   137	2.3 h is an extrapolation, not a measurement. If the pilot-derived total exceeds 16 GPU-h
   138	the screen is recorded COST-INELIGIBLE; if a launched run exhausts its ceiling it is recorded
   139	INCOMPLETE. N is not reduced, failures are not dropped, and no checkpoint is selected to
   140	rescue it. Runs go through `tools/gpu_reserve.sh` with `STENCIL_GPU_SHARE=1`, chunks ≤ 50
   141	min, the peer notified before any run > 30 min.
   142	
   143	## 9. Records
   144	
   145	Per request, written as it completes (resumable jsonl): session, arm, request index, full

web search: 
web search: LLM "scope" "knowledge editing" SERAC 2024 2025 ...
web search: 
web search: LLM "instruction" "revision" benchmark site:arxiv.org/abs 2025 ...
exec
/bin/bash -lc "sed -n '3950,4080p' plan/LEDGER.md && rg -n '"'^class |def (replacement_text|scope_text|reinstatement_text)|grandfather|new methods|previously|scope'"' src/stencil/a_train_pool.py && nl -ba src/stencil/a_screen_pool/s12.py | sed -n '610,705p' && nl -ba scripts/a_screen_summary.py | sed -n '1,155p' && git status --short" in /home/bmarti44/stencil-llm
 succeeded in 0ms:
  the terminator. Acting on that:
  - **Round-10 finding 2 fixed by deletion.** Astra demonstrated the generic fixture
    `test_no_public_call_disturbs_the_id_allocator` REJECTS a correct reply: a behaviour-preserving
    `initialize_bank(bank, accounts)` constructor refactor makes the fixture call it with a junk
    string and the suite then fails (`_initialize_bank` passes) — a false J = 0 in 23 of 48 slots.
    The fixture was added in round 9 only to argue audit coverage; it is reverted out of all 23
    slots (`git checkout eecde769^ -- src/stencil/a_screen_pool/`). SCREEN pool back to
    **ef802ce2160ee00c**. The per-operation create-after-operation tests of amendment 6 stay.
  - **Round-10 findings 3 and 4 kept** (monotonic durations in `a_screen.py`, `a_screen_run.py`,
    `a_screen_train.py`; unbounded cross-boot launches refused): those make budget accounting WRONG,
    they are cheap, and they are already written and tested.
  - **Round-10 finding 1 dropped for now.** It says the mutation audit under-tests my suites for
    resets placed below a lookup. That is a sensitivity property of the instrument, not a bias: it
    applies identically to `off`, `sft` and `cf`, so it cannot manufacture a difference between
    arms. It is a thing to fix if and when there is a positive result worth proving.
  - No amendment 10, no round-11 prompt, no re-registration. The registration stands as written and
    the deltas above are recorded here instead.
STATE: running the candidate-A screen. SCREEN pool ef802ce2160ee00c, TRAIN b8f504494a281858.
Order: gold check + trainer/runner smoke -> timing pilot (`--longest 4`) -> notify peer
"looped-transformer" -> train sft then cf (4 h each) -> run 3 x 48 -> summary. Peer holds the GB10
until ~17:30Z (notasearch-luna-pool1, 40 GB of 119); Stencil peaks 8-15 GB, so we share.

- 2026-09-13 16:10Z — **PRE-COMMITTED STOP RULE for the candidate-A screen** (Brian: "if it looks
  like the numbers are not going our way, let's pause the GPU work... I'd like to run something
  else on GPU if this is not going in a good direction"). Written BEFORE the first adapter number
  exists so it cannot be rationalised afterwards.
  - **Primary measure**: replies satisfying the contract IN FORCE at request 2 of the 36 sessions
    whose convention CHANGED. Baseline `off` = **11/36 in-force, 12/36 stale, 13/36 neither**.
  - **Decision point**: when `cf` training ends (~19:15Z) it is evaluated on all 48 sessions
    (~62 min). That yields `off` vs `cf` at ~20:20Z, which is a valid FUTILITY screen even though
    it cannot isolate the objective: `cf` contains ordinary supervised training, so if `cf` does
    not beat `off`, `sft` will not either and the direction is dead.
  - **CONTINUE** to `sft` only if `cf` reaches **>= 16/36 in-force** (a lift of +5 or more).
  - **PAUSE GPU** if `cf` <= 13/36 (a lift of +2 or less, inside noise at this n): release the
    GB10 for Brian's other work, tell the peer, and carry on with Astra reviews on CPU only.
  - **14-15/36 is the ambiguous band**: report the number and the McNemar discordance to Brian
    with a recommendation, do not decide unilaterally.
  - Earlier warning, free: the training margin. `+0.6368` at step 10 says the preference term
    separates the in-force gold from the stale one. A collapse toward 0 or a negative trend is
    reported immediately as a bad sign.

- 2026-09-13 18:20Z — **GPU PAUSED after cf training, by Brian** ("you can let this run finish and
  then pause using more GPU"). The `cf` allocation is allowed to complete; nothing further
  launches. The GB10 goes to the peer session and to whatever Brian wants to run.
  - **DONE and on disk**: the `off` baseline over all 48 sessions
    (`results/a-screen/runs/off-oldrunner.jsonl`, J=6, function-only=15, 61.6 min, COMPLETE) and
    the `cf` adapter (`results/a-screen/adapters/cf/`).
  - **NOT done**: the `cf` evaluation, `sft` training, the `sft` evaluation, and the `off` re-run
    on the fixed runner. So there is NO adapter-vs-baseline number yet, and the pre-committed
    stop rule above has not been evaluated. Nothing about the direction is settled either way.
  - **Resume needs 4 GPU steps, in this order** (~4.5 h total at an uncontended rate):
    1. `off` re-run on the current runner (~62 min) so all arms share one `runner_sha256`;
       `off-oldrunner.jsonl` was produced before the eligibility-guard fix and its identity
       differs by that one hunk.
    2. `cf` eval: `a_screen_run.py --arm cf --adapter results/a-screen/adapters/cf` (~62 min).
       THIS IS THE FUTILITY SCREEN -- apply the stop rule above before spending anything more.
    3. `sft` training matched to cf's achieved step count via `--max-steps` (~1.5-2 h).
    4. `sft` eval with `--require-steps <cf steps>` (~62 min).
  - **Before each eval** run the CPU preflight
    (`scratchpad/preflight.py <adapter> [steps]`, and `--compare cf sft` once both exist). It is
    mutation-tested 13/13 and checks everything the runner checks, in a second rather than after
    the GPU hours are spent.
  - **FROZEN while paused** -- editing any of these invalidates the cf adapter or the run
    identity, and the adapter cost 4 GPU-h: `scripts/a_screen_train.py`, `scripts/a_screen_run.py`,
    `src/stencil/a_screen.py`, `src/stencil/a_train_pool.py`, and `src/stencil/a_screen_pool/`.
  - Training health at the pause: margin +0.64 -> +8.45 (monotone bar one dip), CE 0.068 ->
    0.0004, objective saturated. So a later null would read as failure to TRANSFER, not as
    undertraining -- the adapter learned the training distribution thoroughly.
  - CPU work continues: Astra reviews, analysis, and the writeup. No GPU.
47:            pkg="scopelog",
48:            Entity="Telescope",
49:            entity="telescope",
50:            Store="TelescopeLog",
52:            what="an observatory's telescope register",
205:class Op:
310:class {d["Entity"]}:
328:class Backend:
346:class {d["Err"]}(Exception):
367:class {Store}:
747:        ): f"Convention for {S}: argument validation lives in the public method itself. For every operation added from now on, the module-level _apply_* helper never validates; it applies whatever value it is given. Operations already in the file keep the arrangement they have (re-review F8: the grandfathered operation validates in its helper, so the convention must not claim that no helper validates).",
797:def replacement_text(family: str, new: str, d: dict[str, str]) -> str:
805:def scope_text(family: str, new: str, op2: Op, d: dict[str, str]) -> str:
814:def reinstatement_text(family: str, back: str, d: dict[str, str]) -> str:
839:        'I\'m starting {pkg}, a small in-process package for {what}. It is deliberately tiny: a frozen {Entity} dataclass, a {Store} that keeps records in a dict, and an optional Backend that writes records somewhere durable. Before we add operations, can you draft the README scope section? I want to head off the \'why not a database\' conversation, and I want the persistence story stated honestly: the Backend is a hook, not a promise.\n\nThe usage I have in mind:\n\n```python\nfrom {pkg}.model import {Entity}\nfrom {pkg}.store import {Store}\n\nbook = {Store}()\nbook.add({Entity}("x1", "alpha"))\nprint(book.find("x1"))\n```',
840:        "Here is a scope section that says exactly that:\n\n```\n## Scope\n{pkg} keeps {Entity} records for {what} inside one process. Records live in a {Store}; an optional Backend receives each updated record so a caller can persist it, but {pkg} itself has no storage, no locking and no concurrency guarantees.\n\n## Non-goals\n- multi-process access\n- query language\n- schema migrations\n```\n\nThe non-goals list is what people actually read, and it makes the Backend hook look like what it is: a callback with an OSError contract, not a database.",
1025:            event = scope_text(target, state_at[1], op2, d)
   610	        'its own, because names like "Mary-Jane O\'Neil" will show up:\n\n```python\n'
   611	        'def initials(who: str) -> str:\n    parts = [p for p in who.replace("-", " ")'
   612	        '.split() if p]\n    return "".join(p[0].upper() for p in parts[:2]) or "??"\n'
   613	        "```\n\nTwo characters keeps the columns aligned, and `??` for an empty name is "
   614	        "better than an exception in the morning message.",
   615	    ),
   616	    Turn(
   617	        "user",
   618	        "Two conventions before the real methods land. First, logging: when a public "
   619	        "RoomDesk method refuses a request (a slot already taken, and the same for any "
   620	        "refusal we add later), it emits exactly one `logging.warning` through the "
   621	        "module logger `roomdesk` and nothing else. Successful operations log nothing "
   622	        "at all, not even debug; the bot is chatty enough. I want to grep the log for "
   623	        "WARNING and count the fights.",
   624	    ),
   625	    Turn(
   626	        "assistant",
   627	        "Understood: every refusal in a public RoomDesk method logs exactly one warning "
   628	        "on the `roomdesk` logger (one record, not one per loop iteration), and the "
   629	        "success path emits no record at any level. KeyError on an unknown id is not a "
   630	        "refusal, it is a caller error, so it raises without logging.",
   631	    ),
   632	    Turn(
   633	        "user",
   634	        "Second, naming: public RoomDesk methods are verb_noun, like add_room and "
   635	        "list_bookings. New methods follow that pattern so the class reads as a list of "
   636	        "actions.",
   637	    ),
   638	    Turn(
   639	        "assistant",
   640	        "Noted: verb_noun for new public RoomDesk methods, matching add_room, find_room "
   641	        "and list_bookings. Private helpers can be named freely. Where the verb is "
   642	        "ambiguous I will use the verb the request itself uses.",
   643	    ),
   644	    Turn(
   645	        "user",
   646	        "Actually, wait. The bot author's own codebase names everything noun_verb "
   647	        "(message_send, channel_join) and they asked whether roomdesk could match so "
   648	        "autocomplete groups by the thing being acted on. Let's try it: from now on, "
   649	        "new public RoomDesk methods are noun_verb. Existing names such as add_room "
   650	        "stay as they are.",
   651	    ),
   652	    Turn(
   653	        "assistant",
   654	        "Switching: new public RoomDesk methods are noun_verb from now on (for example "
   655	        "room_book, booking_cancel). add_room, find_room and list_bookings keep their "
   656	        "names. If you decide against it later, say so and I will go back to verb_noun "
   657	        "for anything new.",
   658	    ),
   659	    Turn(
   660	        "user",
   661	        "The tests that exist today are only these; I will paste the current files with "
   662	        "each request so you see the real state:\n\n```python\nfrom roomdesk.store "
   663	        "import RoomDesk\n\n\ndef test_add_room_mints_sequential_ids():\n    d = "
   664	        'RoomDesk()\n    assert d.add_room("Aurora", 6).room_id == "R1"\n    assert '
   665	        'd.add_room("Birch", 12).room_id == "R2"\n\n\ndef test_find_room_missing_is_none'
   666	        '():\n    assert RoomDesk().find_room("R1") is None\n\n\ndef '
   667	        'test_list_bookings_empty():\n    d = RoomDesk()\n    d.add_room("Aurora", 6)\n'
   668	        '    assert d.list_bookings("R1") == []\n```',
   669	    ),
   670	    Turn(
   671	        "assistant",
   672	        "Good. Send the first request and I will return the complete store module, "
   673	        "keeping add_room, find_room and list_bookings exactly as they are.",
   674	    ),
   675	]
   676	
   677	_EVENT = (
   678	    "Scrap the noun_verb idea; the bot author changed their mind after seeing "
   679	    "add_room next to it and it reads badly. Back to the original rule: new public "
   680	    "RoomDesk methods are verb_noun. Whatever has already been added keeps its current "
   681	    "name; only new methods follow verb_noun again."
   682	)
   683	
   684	
   685	def build() -> Session:
   686	    return Session(
   687	        id="S12",
   688	        project="roomdesk",
   689	        target_family="naming",
   690	        support_family="logging",
   691	        lifecycle="reinstatement",
   692	        files=_FILES,
   693	        prefix=_PREFIX,
   694	        states=("verb_noun", "noun_verb"),
   695	        state_at=("noun_verb", "verb_noun"),
   696	        event=_EVENT,
   697	        requests=(_REQ1, _REQ2),
   698	        rule_turns=(8, 10, 12),
   699	    )
     1	# ruff: noqa: E501
     2	"""Gate summary for the candidate-A screen (registration §7): paired counts, exact
     3	McNemar p, conservative paired intervals, per-lifecycle and changing-rule tables, the
     4	five count gates and the verdict string.  Reads ``results/a-screen/runs/{off,sft,cf}.jsonl``.
     5	
     6	Usage: ``uv run python scripts/a_screen_summary.py --runs results/a-screen/runs --out results/a-screen/RESULTS-TABLES.md``
     7	"""
     8	
     9	from __future__ import annotations
    10	
    11	import argparse
    12	import json
    13	from math import comb
    14	from pathlib import Path
    15	
    16	from stencil import a_screen as A
    17	
    18	ARMS = ("off", "sft", "cf")
    19	
    20	
    21	# the identity fields that must agree across all three arms: everything except the adapter
    22	SHARED_IDENTITY = (
    23	    "pool_sha256",
    24	    "a_screen_sha256",
    25	    "contracts_sha256",
    26	    "runner_sha256",
    27	    "hub",
    28	    "hub_sha256",
    29	    "eos",
    30	    "max_new",
    31	    "deadline_s",
    32	    "prompt_budget",
    33	    "sessions",
    34	)
    35	
    36	
    37	def load(path: Path, arm: str, expected: set[str]) -> dict[str, dict]:
    38	    """Load one arm's records and validate them hard before any count is taken.
    39	
    40	    Astra F12 and its re-review: keep BOTH requests per session; reject duplicates, records
    41	    carrying a different arm label, records with no identity, records from more than one
    42	    identity, a request 2 with no request 1, and any session outside the frozen manifest
    43	    (an unregistered extra session supplied a fifth win and flipped the verdict).  Recompute
    44	    every session outcome from the INDIVIDUAL suite results rather than from the stored
    45	    aggregate flags (``scores.all`` was trusted even when ``scores.contract`` was false)."""
    46	    per: dict[tuple[str, int], dict] = {}
    47	    identities: set[str] = set()
    48	    for lineno, line in enumerate(path.read_text().splitlines(), 1):
    49	        if not line.strip():
    50	            continue
    51	        try:
    52	            r = json.loads(line)
    53	        except json.JSONDecodeError as exc:
    54	            raise SystemExit(f"{path.name}:{lineno}: malformed record ({exc})") from exc
    55	        if r.get("arm") != arm:
    56	            raise SystemExit(
    57	                f"{path.name}:{lineno}: arm {r.get('arm')!r}, expected {arm!r}"
    58	            )
    59	        if r["session"] not in expected:
    60	            raise SystemExit(
    61	                f"{path.name}:{lineno}: {r['session']} is not in the frozen manifest"
    62	            )
    63	        ident = r.get("identity")
    64	        if not ident:
    65	            raise SystemExit(f"{path.name}:{lineno}: record carries no identity")
    66	        if ident.get("pilot_adapter"):
    67	            raise SystemExit(
    68	                f"{path.name}:{lineno}: record was produced with --pilot-adapter "
    69	                "(an adapter that is not the registered allocation); not analysable"
    70	            )
    71	        if sorted(ident.get("sessions") or []) != sorted(expected):
    72	            got = ident.get("sessions")
    73	            raise SystemExit(
    74	                f"{path.name}:{lineno}: record was produced by a run over "
    75	                f"{len(got or [])} sessions, not the frozen manifest's {len(expected)}; "
    76	                "a subset run is a pilot, not the screen"
    77	            )
    78	        identities.add(json.dumps(ident, sort_keys=True))
    79	        key = (r["session"], r["request"])
    80	        if key in per:
    81	            raise SystemExit(f"{path.name}:{lineno}: duplicate record for {key}")
    82	        per[key] = r
    83	    if len(identities) > 1:
    84	        raise SystemExit(
    85	            f"{path.name}: records from {len(identities)} different identities"
    86	        )
    87	    out: dict[str, dict] = {}
    88	    for (session, request), r in sorted(per.items()):
    89	        if request != 2:
    90	            continue
    91	        first = per.get((session, 1))
    92	        if first is None:
    93	            raise SystemExit(f"{path.name}: {session} has request 2 but no request 1")
    94	        per_request = []
    95	        for q in (first, r):
    96	            sc = q["scores"]
    97	            missing = [n for n in A.SUITES if n not in sc]
    98	            if missing:
    99	                raise SystemExit(
   100	                    f"{path.name}: {session}@{q['request']} is missing suites {missing}"
   101	                )
   102	            ok = all(bool(sc[n]) for n in A.SUITES)
   103	            if ok != bool(sc.get("all")):
   104	                raise SystemExit(
   105	                    f"{path.name}: {session}@{q['request']} scores.all={sc.get('all')} "
   106	                    f"disagrees with its suites {[(n, sc[n]) for n in A.SUITES]}"
   107	                )
   108	            if ok and q["terminal_reason"] != "applied":
   109	                raise SystemExit(
   110	                    f"{path.name}: {session}@{q['request']} passed every suite but its "
   111	                    f"terminal reason is {q['terminal_reason']!r}"
   112	                )
   113	            per_request.append(ok)
   114	        rec = dict(r)
   115	        rec["requests"] = [first, r]
   116	        rec["J"] = bool(per_request[0] and per_request[1])
   117	        # re-review round 3 F12: recompute function-only from its THREE suites.  Trusting the
   118	        # stored flag let a record keep a failed functional suite while declaring
   119	        # function_only true, which flipped gate 3 and the verdict.
   120	        fo = []
   121	        for q in (first, r):
   122	            sc = q["scores"]
   123	            want = bool(
   124	                sc["functional"] and sc["regression"] and sc["protected_function"]
   125	            )
   126	            if want != bool(sc.get("function_only")):
   127	                raise SystemExit(
   128	                    f"{path.name}: {session}@{q['request']} function_only="
   129	                    f"{sc.get('function_only')} disagrees with functional="
   130	                    f"{sc['functional']} regression={sc['regression']} "
   131	                    f"protected_function={sc['protected_function']}"
   132	                )
   133	            fo.append(want)
   134	        rec["function_only"] = bool(fo[0] and fo[1])
   135	        if rec["J"] != r["J"] or rec["function_only"] != r["function_only"]:
   136	            raise SystemExit(
   137	                f"{path.name}: {session} stored outcome disagrees with its suites"
   138	            )
   139	        out[session] = rec
   140	    return out
   141	
   142	
   143	def mcnemar_exact(b: int, c: int) -> float:
   144	    """Two-sided exact McNemar p on discordant counts (b wins, c losses)."""
   145	    n = b + c
   146	    if n == 0:
   147	        return 1.0
   148	    k = min(b, c)
   149	    tail = sum(comb(n, i) for i in range(k + 1)) / 2**n
   150	    return min(1.0, 2 * tail)
   151	
   152	
   153	def clopper_pearson(k: int, n: int, alpha: float) -> tuple[float, float]:
   154	    """Exact binomial interval by bisection (no scipy)."""
   155	
 M plan/LEDGER.md
 M results/focal/quicklook.json
 M results/quick-checks/check45/manifest.json
 M tests/test_a_screen_spend.py
?? tests/test_a_screen_compare_guard.py
?? tests/test_a_screen_preflight_guard.py
?? tests/test_a_screen_supersession.py

exec
/bin/bash -lc "PYTHONDONTWRITEBYTECODE=1 .venv/bin/python - <<'PY'
import sys,json,copy,io,random,ast
from unittest.mock import patch
from collections import Counter
sys.path[:0]=['src','results/a-screen/analysis']
import compare as C
import runner_equivalence as R
from stencil.a_train_pool import train_sessions
from stencil.a_screen_pool import screen_sessions
from stencil import a_screen as A
rows=[json.loads(l) for l in open('results/a-screen/runs/off-oldrunner.jsonl')]
def pair():
 a=copy.deepcopy(rows);b=copy.deepcopy(rows)
 for r in b:
  r['arm']='cf';r['identity'].update(adapter='/fixture/cf',adapter_steps=134,adapter_sha256='fixture',adapter_config_sha256='fixture',pilot_adapter=False)
 return a,b
realopen=open
def valid(a,b,reason=''):
 files={'/virtual/a': '\\n'.join(map(json.dumps,a)), '/virtual/b':'\\n'.join(map(json.dumps,b))}
 def op(p,*args,**kw):return io.StringIO(files[p]) if p in files else realopen(p,*args,**kw)
 with patch('builtins.open',op):return C.validate(list(files),reason)[3]
a,b=pair();print('clean',valid(a,b))
a,b=pair();a=[r for r in a if r['session']"'!='"'S02'];b=[r for r in b if r['session']"'!='"'S02']
for r in a+b:r['identity']['sessions'].remove('S02') if 'S02' in r['identity']['sessions'] else None
print('same 47-session subset',valid(a,b))
a,b=pair()
for r in a+b:r['identity'].pop('hub_sha256')
print('both omit hub_sha256',valid(a,b))
a,b=pair()
for r in b:r['repo_after']='0000000000000000'
print('all repo_after corrupted',valid(a,b))
a,b=pair()
for r in b:r['scores']={}
print('all scores absent',valid(a,b))
a,b=pair()
for r in b:r['identity']['pilot_adapter']=True
print('pilot adapter',valid(a,b))
a,b=pair()
for r in a:r['arm']='sft';r['identity'].update(adapter='/fixture/sft',adapter_steps=120)
for r in b:r['identity'].pop('adapter_steps')
print('trained cf missing steps vs sft120',valid(a,b))
a,b=pair()
for r in b:r['identity']['runner_sha256']='arbitrary'
print('arbitrary runner exception',valid(a,b,'anything'))
print('runner recomputation');R.main()
src=R.RUNNER.read_text();tree=ast.parse(src)
guard=next(n for n in ast.walk(tree) if R.is_adapter_guard(n));guard.orelse=[ast.parse('raise RuntimeError(\"off branch changed\")').body[0]]
print('runner strips new off-branch else',R.strip(src)[0]==R.strip(ast.unparse(tree))[0])
train=list(train_sessions());pairs=[p for s in train for p in A.pairs_from_session(s)]
print('training pairs',len(pairs),'unique chosen',len(set(p.chosen for p in pairs)),'unique full unpacked input/output',len(set((json.dumps(p.messages,sort_keys=True),p.chosen,p.rejected) for p in pairs)))
order=list(range(len(pairs)));random.Random(0).shuffle(order)
seen=set();dup=0
for i in order[:1072]:
 dup+=pairs[i].chosen in seen;seen.add(pairs[i].chosen)
print('duplicate chosen in completed first1072 microsteps',dup)
print('interval floor',C.paired_interval(0,0,36))
for losses in range(3):
 wins=next(b for b in range(37-losses) if C.paired_interval(b,losses,36)[0]>0)
 print('min wins',losses,wins,C.paired_interval(wins,losses,36))
PY" in /home/bmarti44/stencil-llm
 succeeded in 1683ms:
clean []
same 47-session subset []
both omit hub_sha256 []
all repo_after corrupted []
all scores absent []
pilot adapter []
trained cf missing steps vs sft120 []
  runner exception in force: off 4acdb8f044c25a48 vs cf arbitrary -- anything
arbitrary runner exception []
runner recomputation
old runner (86282371) sha16 4acdb8f044c25a48
current runner        sha16 f27bc5bc0690a918
adapter guards: old 2, new 2
--require-steps options removed: old 0, new 1
outside those sites the two runners are AST-identical: True
adapter guard bodies that differ: [0] of 2
a.require_steps is read only inside an adapter guard: True

ESTABLISHED: an adapterless run executes the same program under both
runners, so results/a-screen/runs/off-oldrunner.jsonl needs no re-run.
runner strips new off-branch else True
training pairs 1152 unique chosen 1007 unique full unpacked input/output 1152
duplicate chosen in completed first1072 microsteps 121
interval floor (-0.11460637785869263, 0.11460637785869263)
min wins 0 10 (0.013081054468177367, 0.47553118440038444)
min wins 1 12 (0.004621043147340187, 0.5327416211854858)
min wins 2 14 (0.0060064067939239185, 0.583497306448331)

codex
The comparison guard still accepts several invalid inputs: the same reduced session set in both arms, a required hash missing from both, corrupted `repo_after` hashes, and a trained arm with no step count. I reproduced each through `validate()`. Separately, I verified that the existing runner exception is valid for the two recorded versions, so the baseline does not need rerunning.

web search: 
web search: https://arxiv.org/html/2609.03340v1
exec
/bin/bash -lc "nl -ba scripts/a_screen_train.py | sed -n '1,100p' && nl -ba src/stencil/a_train_pool.py | sed -n '790,825p' && nl -ba src/stencil/a_screen_pool/s11.py | sed -n '440,485p' && nl -ba src/stencil/contracts.py | sed -n '990,1090p' && rg -n 'def run_tests|class Session|def other|def build' src/stencil/contracts.py src/stencil/a_screen.py src/stencil/a_train_pool.py" in /home/bmarti44/stencil-llm
 succeeded in 0ms:
     1	# ruff: noqa: E501
     2	"""Train one adapter for the candidate-A screen (registration §3-§4).
     3	
     4	Arms: ``sft`` = completion-token mean cross-entropy on every positive (both
     5	counterfactual directions and the irrelevant-history variants); ``cf`` = the same
     6	cross-entropy + 0.1 * L_DPO (beta 0.1, frozen trunk as reference, reference log-probs
     7	precomputed once with the adapter disabled) against the stale-alternative gold.
     8	LoRA rank 16 / alpha 32 / dropout 0 on every attention and MLP projection, AdamW lr 1e-4,
     9	weight decay 0, clipping 1.0, seed 0, micro-batch 1 with 8-step accumulation, bf16
    10	trunk frozen.  Fixed wall-clock allocation (``--hours 4``, reference scoring included);
    11	the FINAL completed optimizer step is saved, never a selected checkpoint.
    12	
    13	Usage (through tools/gpu_reserve.sh):
    14	  uv run python scripts/a_screen_train.py --objective cf --out results/a-screen/adapters/cf
    15	Smoke: ``--limit 8 --minutes 3``.
    16	"""
    17	
    18	from __future__ import annotations
    19	
    20	import argparse
    21	import functools
    22	import json
    23	import random
    24	import sys
    25	import time
    26	from pathlib import Path
    27	
    28	ROOT = Path(__file__).resolve().parents[1]
    29	sys.path.insert(0, str(ROOT / "src"))
    30	
    31	import stencil.determinism  # noqa: E402, F401  (sets CUBLAS workspace before torch)
    32	from stencil import a_screen as A  # noqa: E402
    33	from stencil.a_train_pool import train_sessions  # noqa: E402
    34	
    35	print = functools.partial(print, flush=True)  # noqa: A001
    36	
    37	TARGET_MODULES = [
    38	    "q_proj",
    39	    "k_proj",
    40	    "v_proj",
    41	    "o_proj",
    42	    "gate_proj",
    43	    "up_proj",
    44	    "down_proj",
    45	]
    46	
    47	
    48	def verify_frozen_train(sessions) -> str:
    49	    """Astra F15: refuse to train unless the generated pool matches the frozen record."""
    50	    import hashlib
    51	    from dataclasses import asdict
    52	
    53	    frozen = json.loads((ROOT / "results/a-screen/train-pool.json").read_text())
    54	    assert not frozen["problems"], f"frozen pool records problems: {frozen['problems']}"
    55	    assert len(sessions) == frozen["n"], (
    56	        f"{len(sessions)} sessions, frozen {frozen['n']}"
    57	    )
    58	    for s in sessions:
    59	        want = frozen["hashes"][s.id]
    60	        got = hashlib.sha256(
    61	            json.dumps(asdict(s), sort_keys=True).encode()
    62	        ).hexdigest()[:16]
    63	        assert got == want, f"{s.id}: content {got}, frozen {want}"
    64	    return frozen["pool_sha256"]
    65	
    66	
    67	def build_examples(tok, limit: int = 0) -> list[dict]:
    68	    """One example per (prompt, chosen, rejected) triple, prompts packed exactly as the
    69	    harness packs them."""
    70	    count = A.make_counter(tok)
    71	    im_end = tok.convert_tokens_to_ids("<|im_end|>")
    72	    out = []
    73	    sessions = train_sessions()
    74	    if limit:
    75	        sessions = sessions[:limit]
    76	    else:
    77	        verify_frozen_train(sessions)
    78	    for s in sessions:
    79	        for p in A.pairs_from_session(s):
    80	            # re-review round 3: one packing policy path, shared with the harness, so the
    81	            # trained prompts and the evaluated prompts cannot drift apart
    82	            packed, kept = A.pack_session(s, list(p.messages), 2, count)
    83	            prompt = A.render_prompt(tok, packed)
    84	            pid = tok(prompt, add_special_tokens=False)["input_ids"]
    85	            ch = tok(p.chosen, add_special_tokens=False)["input_ids"] + [im_end]
    86	            rj = tok(p.rejected, add_special_tokens=False)["input_ids"] + [im_end]
    87	            out.append(
    88	                {
    89	                    "session": p.session,
    90	                    "variant": p.variant,
    91	                    "prompt_ids": pid,
    92	                    "chosen_ids": ch,
    93	                    "rejected_ids": rj,
    94	                    "kept": kept,
    95	                }
    96	            )
    97	    return out
    98	
    99	
   100	def main() -> None:
   790	    }[(family, state)]
   791	
   792	
   793	def _ack(text: str) -> str:
   794	    return f"Understood. {text.split(':', 1)[1].strip() if ':' in text else text} I will follow that in everything I write for this package."
   795	
   796	
   797	def replacement_text(family: str, new: str, d: dict[str, str]) -> str:
   798	    return (
   799	        "Change of convention, effective now for anything new: "
   800	        + target_statement(family, new, d).split(": ", 1)[1]
   801	        + " Existing methods stay as they are."
   802	    )
   803	
   804	
   805	def scope_text(family: str, new: str, op2: Op, d: dict[str, str]) -> str:
   806	    field = "tags" if op2.param == "tag" else op2.param
   807	    base = target_statement(family, new, d).split(": ", 1)[1]
   808	    return (
   809	        f"One exception to the {family.replace('_', ' ')} convention: for operations that change the {field} field "
   810	        f"(anything that sets a {d['entity']}'s {field}), {base[0].lower() + base[1:]} Everything else keeps the convention as stated."
   811	    )
   812	
   813	
   814	def reinstatement_text(family: str, back: str, d: dict[str, str]) -> str:
   815	    return (
   816	        "Let's go back to the earlier convention, effective now for anything new: "
   817	        + target_statement(family, back, d).split(": ", 1)[1]
   818	        + " Methods written under the interim rule stay as they are."
   819	    )
   820	
   821	
   822	IRRELEVANT = [
   823	    "Small admin note: the weekly sync moved to Thursday at 10:15, same room. Nothing changes for the code.",
   824	    "By the way, I renamed the repository on the forge; the package name and module paths stay exactly the same.",
   825	    "Heads-up that CI now runs on Python 3.12 as well as 3.11. It passed on both with the current files.",
   440	    kept = s.find("INV-2026-0001")
   441	    assert kept is not None and kept.status == "void"
   442	    assert kept.customer == "Acme" and kept.amount_cents == 100
   443	    assert s.find("INV-2026-0002").amount_cents == 4550
   444	    assert s.count() == 2
   445	"""
   446	}
   447	
   448	_C2_CONTRACT = {
   449	    "verb_noun": {
   450	        "test_archive_naming.py": """from invoiceseq.archive import InvoiceArchive
   451	
   452	
   453	def test_archive_is_verb_noun():
   454	    assert hasattr(InvoiceArchive, "archive_invoice")
   455	    assert not hasattr(InvoiceArchive, "invoice_archive")
   456	"""
   457	    },
   458	    "noun_verb": {
   459	        "test_archive_naming.py": """from invoiceseq.archive import InvoiceArchive
   460	
   461	
   462	def test_archive_is_noun_verb():
   463	    assert hasattr(InvoiceArchive, "invoice_archive")
   464	    assert not hasattr(InvoiceArchive, "archive_invoice")
   465	"""
   466	    },
   467	}
   468	
   469	_C2_SUPPORT = {
   470	    "test_archive_errors.py": _C2_HELPER
   471	    + """
   472	
   473	def test_malformed_number_propagates_raw_valueerror():
   474	    s = _store()
   475	    a = InvoiceArchive()
   476	    with pytest.raises(ValueError) as info:
   477	        _archive(a)(s, "invoice one")
   478	    assert type(info.value) is ValueError
   479	    assert not isinstance(info.value, InvoiceSeqError)
   480	"""
   481	}
   482	
   483	
   484	def _gold2(name: str) -> str:
   485	    # Request 2 targets archive.py; the store at checkpoint 2 carries the checkpoint-1
src/stencil/a_screen.py:92:class Session:
src/stencil/a_screen.py:109:    def other(self, state: str) -> str:
src/stencil/contracts.py:98:def run_tests(

web search: 
web search: "multi-turn" "instruction" "updating" benchmark language models ...
web search: 
web search: large language models evolving instructions selective update preserve constraints benchmark 2025 2026 ...
web search: 
web search: https://arxiv.org/html/2511.03508v1
exec
/bin/bash -lc "PYTHONDONTWRITEBYTECODE=1 .venv/bin/python - <<'PY'
import sys
sys.path.insert(0,'src')
from stencil.a_screen_pool import screen_sessions
for s in screen_sessions():
 if s.lifecycle in ('scope','reinstatement'):
  print(s.id,s.lifecycle,s.state_at,s.event)
PY
nl -ba src/stencil/contracts.py | sed -n '85,155p'
nl -ba src/stencil/a_screen.py | sed -n '88,120p'" in /home/bmarti44/stencil-llm
 succeeded in 0ms:
S03 scope ('verb_noun', 'noun_verb') One scoped exception to the naming rule, effective now: in the fines module (FineLedger only), new public methods are named noun_verb, for example fine_waive or fine_settle, because the treasurer's ledger spreadsheet lists operations that way and she reads the code. LoanDesk and everything else stays verb_noun. Existing method names stay as they are.
S04 reinstatement ('noun_verb', 'verb_noun') Naming again, sorry: the office manager overruled the team and we are going back to the original convention. Effective now, new public PermitLot methods are named verb_noun (revoke_permit, extend_permit style); the noun_verb change is withdrawn. Existing method names stay as they are, whatever pattern they follow.
S07 scope ('verb_noun', 'noun_verb') One scoped exception to the naming rule, effective now: in the stops module (busboard/stops.py only), new public functions are named noun_verb, for example aliases_load or stop_lookup, because that module mirrors the council data team's GTFS helper library, whose helpers are all noun_verb, and they will be reading it. Timetable, model and everything else stay verb_noun. Existing names, including normalize_stop, stay as they are.
S08 reinstatement ('noun_verb', 'verb_noun') Scrap the noun_verb experiment, it reads badly next to add_player. Back to the original rule: new public RatingBook methods are verb_noun. Whatever has already been added keeps its current name; only new methods follow verb_noun again.
S11 scope ('verb_noun', 'noun_verb') One scoped exception to the naming rule: the bookkeeping tool that will import archive.py names all of its store-like methods noun_verb (entry_post, ledger_close) and they want the archive to match. So for anything in invoiceseq/archive.py, that is methods on InvoiceArchive, new public methods are noun_verb. InvoiceStore in store.py is unaffected and stays verb_noun.
S12 reinstatement ('noun_verb', 'verb_noun') Scrap the noun_verb idea; the bot author changed their mind after seeing add_room next to it and it reads badly. Back to the original rule: new public RoomDesk methods are verb_noun. Whatever has already been added keeps its current name; only new methods follow verb_noun again.
S15 scope ('verb_noun', 'noun_verb') Scoped exception to the naming convention, effective now: read-only query methods on Workshop, meaning public methods that return data without changing any job, are named noun_verb (jobs_list style) so that all the queries sort together in the class. Mutating actions keep verb_noun, and existing names stay as they are.
S16 reinstatement ('noun_verb', 'verb_noun') Reverting the naming change: my co-owner and I talked it through and we are going back to verb_noun for new public CouponBook methods (revoke_coupon style), matching issue_coupon. The noun_verb rule is withdrawn; existing method names, including the one you just added, stay exactly as they are.
S19 scope ('api', 'storage') Scoped exception to the validation rule, effective now: for the lending features (lending a game out, returning it, extending a loan), value validation lives in the Shelf storage methods themselves, which raise ValueError, and the public loan functions pass values straight through with no check of their own. The catalogue side (add_game, rate_game and any future catalogue function) is unaffected and keeps validating in the public function; existing code stays exactly as it is.
S20 reinstatement ('storage', 'api') Scrap that last change; the import author is fine either way and I prefer the original rule. For anything new from here on, validation lives in the public functions, which raise ValueError before calling the table, and new PledgeTable methods trust their callers and do not validate. Whatever is already written stays as it is.
S23 scope ('storage', 'api') One scoped change before the next feature. For the outbound side only, meaning any operation that takes stock out of a bin, validation lives in the public function: it raises ValueError before calling the table, and the table method for that operation trusts its caller and does not validate. Inbound operations and everything else keep validating in the table as they do now.
S24 reinstatement ('api', 'storage') Scrap the flip; the importer author has gone with a different approach and I prefer the original rule. For anything new from here on, validation lives in the table: new PlotTable methods check their own inputs and raise ValueError, and new public functions pass their arguments straight through with no pre-check. Whatever is already written stays as it is.
S27 scope ('api', 'storage') One scoped exception to the validation rule, effective now: in the schedule module (festival/schedule.py) validation lives in ScreeningStore itself. New store methods there raise ValueError on bad input and the public functions in schedule.py just call through, with no pre-check of their own, because the programme importer calls the schedule store directly. book_screening keeps its check where it is, and films.py is unaffected: validation there stays in the public functions.
S28 reinstatement ('api', 'storage') Reverting last week's change, effective now: validation goes back into ReceiptFolio for new operations. New store methods raise ValueError on bad input themselves and the public functions in folio.py just call through with no pre-check of their own, the way `put` and `add_receipt` work. The accountant's import script calls the folio methods directly, so checks that live only in the public functions get bypassed. `categorize` stays as it is; only new operations follow the reinstated split.
S31 scope ('storage', 'api') One scoped exception to the validation rule, effective now: in the picks module (readcircle/picks.py) validation moves up into the public functions. New public functions there raise ValueError on bad input themselves and the new PickList methods trust their arguments and do no checking, because the voting-sheet importer calls the public functions and we want its error messages to come from one place. `nominate` and `PickList.add` stay as they are, and members.py is unaffected: validation there stays in MemberRoll.
S32 reinstatement ('storage', 'api') Reverting last week's change: the conservators are getting their own wrapper instead, so the register goes back to being a plain store. For new operations, validation lives in the public function in loans.py again (raise ValueError there) and LoanRegister methods trust their arguments. What is already in the register stays where it is.
S35 scope ('none', 'raise') One scoped exception to the unknown-id convention, effective now: for anything in refunds.py, meaning operations that hand money back against an order, an unknown order id raises KeyError. A refund against an order that does not exist must never fail quietly, because cash leaves the till. Everything in orders.py keeps returning None as before.
S36 reinstatement ('none', 'raise') Reverting the unknown-id change: the sign-in app now exports our ids exactly, and the None results were hiding a bad mapping for two weeks. From now on new Roster actions raise KeyError on an unknown volunteer id again, like `log_hours`. What is already in the roster stays as it is.
S39 scope ('raise', 'none') One scoped exception to the unknown-id rule, effective now: methods that are called from the ground-station sync path (the sync feeds us whatever flight ids the ground station reports, including ids from other laptops that this log has never seen) return None on an unknown id and change nothing, no export line and no exception. Everything outside the sync path, including `close` and `approve`, keeps raising KeyError as before.
S40 reinstatement ('none', 'raise') Reverting the unknown-id change from earlier: the import script now validates ids against the registry before calling anything, so new Registry methods that act on an application id go back to raising KeyError when the id is unknown. `shortlist` stays as written (returning None) and `withdraw` was never changed; only new methods follow the reinstated rule.
S43 scope ('none', 'raise') One scoped exception to the unknown-id rule, effective now: methods used by the on-air desk (anything the studio automation calls while broadcasting) raise KeyError on an unknown slot id, because the automation must stop rather than silently carry on with a mistyped id from the studio. Planning-desk methods, including `cancel` and `assign_host`, keep returning None as before.
S44 reinstatement ('raise', 'none') Reverting Tuesday's change: the KeyError style broke the shift script three times this week. From now on, new action methods go back to returning None on an unknown id and changing nothing, like relocate_item. Methods already written keep whatever they do now.
S47 scope ('raise', 'none') Scoped exception to the missing-id rule: holds are typed from paper slips and the slips are often stale, so for HoldBook (toolshed/holds.py) new action methods return None on an unknown hold id and change nothing. ToolStore keeps raising KeyError as before; this applies to the hold book only.
S48 reinstatement ('none', 'raise') Reverting last week's change: with the None style a mis-keyed id silently skipped two holds and both boxes went home with the wrong people. From now on, new action methods go back to raising KeyError on an unknown id, like add_item. Methods already written keep whatever they do now.
    85	                "above may still follow the OLD convention; do not copy that pattern. "
    86	                "The contracts above take precedence over anything the existing code "
    87	                "does. Before writing, check each contract against your new code.\n"
    88	            )
    89	    parts.append(f"\nTask: {task.request}\n")
    90	    parts.append(
    91	        f"\nReply with the complete new content of `{task.target}` in a single "
    92	        "```python fenced block and nothing else. Keep existing behaviour that the "
    93	        "task does not change."
    94	    )
    95	    return "".join(parts)
    96	
    97	
    98	def run_tests(
    99	    files: dict[str, str], tests: dict[str, str], timeout: float = 90.0
   100	) -> tuple[bool, str]:
   101	    """Write ``files`` and ``tests`` to a fresh directory and run pytest there.
   102	    Returns ``(all_passed, short_summary)``; a timeout or crash counts as failure."""
   103	    if not tests:
   104	        return True, "no tests"
   105	    with tempfile.TemporaryDirectory(prefix="stencil-contract-") as d:
   106	        root = Path(d)
   107	        for path, content in {**files, **tests}.items():
   108	            p = root / path
   109	            p.parent.mkdir(parents=True, exist_ok=True)
   110	            p.write_text(content)
   111	        cmd = [
   112	            sys.executable,
   113	            "-m",
   114	            "pytest",
   115	            "-q",
   116	            "-x",
   117	            "-p",
   118	            "no:cacheprovider",
   119	            *sorted(tests),
   120	        ]
   121	        try:
   122	            r = subprocess.run(
   123	                cmd,
   124	                cwd=root,
   125	                capture_output=True,
   126	                text=True,
   127	                timeout=timeout,
   128	                env={"PYTHONPATH": str(root), "PATH": "/usr/bin:/bin", "HOME": d},
   129	            )
   130	        except subprocess.TimeoutExpired:
   131	            return False, "timeout"
   132	        tail = (r.stdout.strip().split("\n") or [""])[-1]
   133	        return r.returncode == 0, tail[:200]
   134	
   135	
   136	def score(task: Task, new_target: str | None) -> dict:
   137	    """Functional-only and joint outcomes for a proposed new content of the target."""
   138	    if new_target is None:
   139	        return {"parsed": False, "functional": False, "contract": False, "J": False}
   140	    files = {**task.files, task.target: new_target}
   141	    f_ok, f_msg = run_tests(files, task.functional_tests)
   142	    # Astra round 8: contract tests always run so both outcomes are reported
   143	    # independently (J still requires both).
   144	    c_ok, c_msg = run_tests(files, task.contract_tests)
   145	    return {
   146	        "parsed": True,
   147	        "functional": f_ok,
   148	        "contract": c_ok,
   149	        "J": f_ok and c_ok,
   150	        "functional_msg": f_msg,
   151	        "contract_msg": c_msg,
   152	    }
    88	    gold: dict[str, str]  # target state -> complete content of ``target``
    89	
    90	
    91	@dataclass
    92	class Session:
    93	    id: str  # manifest slot, e.g. "S01"
    94	    project: str
    95	    target_family: str
    96	    support_family: str
    97	    lifecycle: str
    98	    files: dict[str, str]  # initial repository
    99	    prefix: list[Turn]  # exactly 16 authored turns
   100	    states: tuple[str, str]  # the target family's two states (initial, alternative)
   101	    state_at: tuple[str, str]  # state in force at checkpoint 1 and 2
   102	    event: str  # message between the live requests (contract-irrelevant if stable)
   103	    requests: tuple[Request, Request]
   104	    rule_turns: tuple[int, ...]  # prefix indices that must survive packing
   105	    irrelevant_event: str = ""  # counterfactual variant (training pools only)
   106	    notes: str = ""
   107	    tags: dict[str, str] = field(default_factory=dict)
   108	
   109	    def other(self, state: str) -> str:
   110	        a, b = self.states
   111	        return b if state == a else a
   112	
   113	    def validate(self) -> None:
   114	        assert self.lifecycle in LIFECYCLES, self.lifecycle
   115	        assert self.target_family in TARGET_FAMILIES, self.target_family
   116	        assert self.support_family in SUPPORT_FAMILIES, self.support_family
   117	        assert len(self.prefix) == 16, f"{self.id}: prefix has {len(self.prefix)} turns"
   118	        assert all(t.role in ("user", "assistant") for t in self.prefix)
   119	        assert set(self.state_at) <= set(self.states)
   120	        if self.lifecycle == "stable":

web search: 
web search: https://aclanthology.org/2025.findings-acl.536.pdf
web search: 
web search: Kung Robinson 1981 optimistic methods concurrency control validation read set paper ...
web search: 
web search: 
web search: 
web search: "ReviseQA" belief revision ...
exec
/bin/bash -lc "PYTHONDONTWRITEBYTECODE=1 .venv/bin/python - <<'PY'
import sys,random,collections,json,copy,io,contextlib
from unittest.mock import patch
sys.path[:0]=['src','results/a-screen/analysis','tests']
import test_a_screen_supersession as TS
for name in sorted(x for x in dir(TS) if x.startswith('test_')):getattr(TS,name)();print(name,'PASS')
from stencil.a_train_pool import train_sessions
from stencil.a_screen_pool import screen_sessions
from stencil import a_screen as A
import overlap as O,compare as C
from scipy.stats import fisher_exact,binomtest
pairs=[p for s in train_sessions() for p in A.pairs_from_session(s)]
ss=list(screen_sessions());tr=O.golds(train_sessions());scr=O.golds(ss)
trainstrings={x[4] for x in tr}
print('full source exact screen matches',sum(x[4] in trainstrings for x in scr),'of',len(scr))
from difflib import SequenceMatcher
rows=[]
for sid,k,state,fam,src,toks in scr:
 ranked=sorted(tr,key=lambda t:len(toks&t[5])/len(toks|t[5]),reverse=True)[:8]
 old=max(SequenceMatcher(None,src,t[4]).ratio() for t in ranked)
 new=max(SequenceMatcher(None,src,t[4],autojunk=False).ratio() for t in ranked)
 rows.append((old,new,sid,k,state))
print('autojunk true/false max same top8',max(x[0] for x in rows),max(x[1] for x in rows))
print('largest autojunk sensitivity',max(rows,key=lambda x:x[1]-x[0]))
for tb in ([[4,8],[0,36]],[[12,24],[1,11]],[[16,32],[1,47]]):print('Fisher',tb,float(fisher_exact(tb).pvalue))
base=[json.loads(l) for l in open('results/a-screen/runs/off-oldrunner.jsonl')]
print('base identity keys',sorted(base[0]['identity']))
print('score consistency',sum(bool(r['scores'].get('function_only')) "'!= bool(r['"'scores'].get('functional') and r['scores'].get('regression') and r['scores'].get('protected_function')) for r in base))
print('interval 5wins0loss',C.paired_interval(5,0,36),C.mcnemar_exact(5,0))
print('paired stable zero-discordance floor n12',C.paired_interval(0,0,12))
PY" in /home/bmarti44/stencil-llm
codex
The strongest new prior art is broader than DPO. Belief-R already measures the trade-off between revising and retaining conclusions; EvolIF adds, deletes, and modifies constraints within separate topic histories; recent agent-memory work tracks scoped revisions and invalidates stale plans. These challenge “conditional revision” as a novelty claim, while leaving open whether Stencil can deliver a useful improvement in executable coding behavior.

web search: 
web search: "Retractions: Updating from Complex Information" authors abstract ...
web search: 
web search: Reynolds separation logic shared mutable data structures 2002 pdf frame rule ...
 succeeded in 52086ms:
test_non_reinstatement_request_1_alternative_was_never_in_force PASS
test_reinstatement_is_exactly_the_three_rule_turn_sessions PASS
test_reinstatement_request_1_alternative_is_the_superseded_rule PASS
test_request_2_alternative_is_request_1s_state_exactly_when_changed PASS
full source exact screen matches 0 of 192
autojunk true/false max same top8 0.25431530494821636 0.5167708925525867
largest autojunk sensitivity (0.08354898336414047, 0.5085122131754256, 'S35', 1, 'none')
Fisher [[4, 8], [0, 36]] 0.002543940795559667
Fisher [[12, 24], [1, 11]] 0.1388437341744716
Fisher [[16, 32], [1, 47]] 7.218217669099951e-05
base identity keys ['a_screen_sha256', 'adapter', 'adapter_config_sha256', 'adapter_sha256', 'adapter_steps', 'contracts_sha256', 'deadline_s', 'eos', 'hub', 'hub_sha256', 'max_new', 'pilot_adapter', 'pool_sha256', 'prompt_budget', 'runner_sha256', 'sessions']
score consistency 0
interval 5wins0loss (-0.07553586039857574, 0.3178166768396879) 0.0625
paired stable zero-discordance floor n12 (-0.3059205794727106, 0.3059205794727106)

exec
/bin/bash -lc "PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -u - <<'PY'
import sys,math,json,copy
from pathlib import Path
from unittest.mock import patch
sys.path[:0]=['src','results/a-screen/analysis']
import compare as C,preflight as P
print('power of registered positive interval n36, multinomial iid win/loss scenario')
valid=[(b,c) for b in range(37) for c in range(37-b) if C.paired_interval(b,c,36)[0]>0]
for pw,pl in [(0.15,0.05),(0.25,0.05),(0.35,0.05)]:
 prob=sum(math.comb(36,b)*math.comb(36-b,c)*pw**b*pl**c*(1-pw-pl)**(36-b-c) for b,c in valid)
 print(pw,pl,prob)
print('zero discordance +/-5% floor required n',math.ceil(math.log(.0125)/math.log(.95)))
print('zero discordance stable floor',C.paired_interval(0,0,12))
root=Path('results/a-screen/adapters/cf').resolve();lp=root/'train-log.json'
log=json.loads(lp.read_text());raw=Path.read_text
cached={}
original=P.A.dir_sha
def hashed(p):
 key=str(p)
 if key not in cached:cached[key]=original(p)
 return cached[key]
with patch.object(P.A,'dir_sha',hashed):
 print('actual preflight',P.check(str(root),'cf',134,log['identity']['hub']))
 for name,mut in [('examples=-1',lambda x:x.update(examples=-1)),('missing limit',lambda x:x['identity'].pop('limit')),('over budget seconds',lambda x:x.update(seconds=20000)),('missing all exposure',lambda x:[x.pop(k,None) for k in ('micro_steps','discarded_micro_steps','completion_tokens_seen','chosen_tokens_seen','sequence_tokens_seen','epochs_completed')])]:
  m=copy.deepcopy(log);mut(m)
  def read(p,*a,**k):return json.dumps(m) if p==lp else raw(p,*a,**k)
  with patch.object(Path,'read_text',read):print(name,P.check(str(root),'cf',134,log['identity']['hub']))
PY" in /home/bmarti44/stencil-llm
 succeeded in 4105ms:
power of registered positive interval n36, multinomial iid win/loss scenario
0.15 0.05 0.009318949884665414
0.25 0.05 0.14508972824061803
0.35 0.05 0.4682164549161513
zero discordance +/-5% floor required n 86
zero discordance stable floor (-0.3059205794727106, 0.3059205794727106)
actual preflight []
examples=-1 []
missing limit []
over budget seconds []
missing all exposure []

web search: 
web search: https://arxiv.org/abs/2603.14517
exec
/bin/bash -lc "nl -ba results/a-screen/analysis/names.py | sed -n '1,145p' && nl -ba tests/test_a_screen_spend.py | sed -n '1,220p' && nl -ba results/a-screen/adapters/cf.log | tail -n 19 && nl -ba scripts/a_screen_run.py | sed -n '150,235p'" in /home/bmarti44/stencil-llm
 succeeded in 0ms:
     1	"""A name-level cross-check on the NAMING family.  Not a retention measure.
     2	
     3	RETIRED INTERPRETATION (2026-09-13, Astra's back-on-track review).  This file
     4	used to be headed "instruction retention, isolated from coding competence" and
     5	claimed more power than the 48 binary J values.  Both claims are withdrawn, for
     6	two demonstrated reasons:
     7	
     8	  * it read the GOLD repository entering request 2 (`A.gold_files`), not the
     9	    repository the arm's own request-1 reply produced.  The runner chains the
    10	    arm's own edit, so for any arm whose first reply differs from gold the
    11	    measure was scored against a repository that arm never saw;
    12	  * it counted public function names in every family.  Checked over the frozen
    13	    screen pool: in `missing_record` and `validation` the gold under the two
    14	    states has IDENTICAL public method names in 32/32 requests -- the states
    15	    differ in behaviour, not in naming.  So outside `naming` the classification
    16	    was reading shared names and could only report "in-force".
    17	
    18	What it does now, and all it does: on the 16 `naming` sessions, where the two
    19	states genuinely differ by method name, report which convention's names the
    20	reply introduced, against the arm's own entering repository.  That is a cheap
    21	syntactic cross-check on stale2.py's executable verdict -- it should mostly
    22	agree, and any disagreement is worth reading -- and nothing more.  The
    23	executable contract-state measure in stale2.py is the evidence; this is a
    24	second pair of eyes on one third of it.
    25	
    26	    uv run python results/a-screen/analysis/names.py <run.jsonl>
    27	"""
    28	
    29	import ast
    30	import json
    31	import os
    32	import sys
    33	from collections import Counter, defaultdict
    34	
    35	sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    36	sys.path.insert(0, "/home/bmarti44/stencil-llm/src")
    37	from stale2 import alt_was_in_force, classify, replay  # noqa: E402
    38	
    39	from stencil import a_screen as A  # noqa: E402
    40	from stencil.a_screen_pool import load  # noqa: E402
    41	
    42	FAMILY = "naming"
    43	
    44	
    45	def pubs(src: str) -> set[str]:
    46	    try:
    47	        tree = ast.parse(src)
    48	    except SyntaxError:
    49	        return set()
    50	    out = set()
    51	    for n in ast.walk(tree):
    52	        if isinstance(n, ast.ClassDef):
    53	            for f in n.body:
    54	                if isinstance(f, ast.FunctionDef) and not f.name.startswith("_"):
    55	                    out.add(f.name)
    56	        elif isinstance(n, ast.FunctionDef) and not n.name.startswith("_"):
    57	            out.add(n.name)
    58	    return out
    59	
    60	
    61	def verdict(session, rec, base):
    62	    """Which convention's NEW names the reply introduced, or neither."""
    63	    k = rec["request"]
    64	    req = session.requests[k - 1]
    65	    state = session.state_at[k - 1]
    66	    was = pubs(base.get(req.target, ""))
    67	    want = pubs(req.gold[state]) - was
    68	    stale = pubs(req.gold[session.other(state)]) - was
    69	    if not (want or stale):
    70	        return "vacuous"  # the states are not name-distinguishable here
    71	    content = A.extract_file(rec["output"])
    72	    got = (pubs(content) - was) if content else set()
    73	    if want & got:
    74	        return "in-force"
    75	    if (stale - want) & got:
    76	        return "alt"
    77	    return "neither"
    78	
    79	
    80	def run(path):
    81	    by = defaultdict(dict)
    82	    arm = None
    83	    for line in open(path):
    84	        d = json.loads(line)
    85	        arm = d["arm"]
    86	        by[d["session"]][d["request"]] = d
    87	    tally, cells, agree = Counter(), defaultdict(Counter), Counter()
    88	    rows = []
    89	    for sid, recs in sorted(by.items()):
    90	        s = load(sid)
    91	        if s.target_family != FAMILY:
    92	            continue
    93	        entering = replay(s, recs)
    94	        for k in sorted(recs):
    95	            base = entering.get(k)
    96	            if base is None:
    97	                continue
    98	            v = verdict(s, recs[k], base)
    99	            x = classify(s, recs[k], base)
   100	            tally[v] += 1
   101	            cells[(k, alt_was_in_force(s, k))][v] += 1
   102	            agree[(v, x)] += 1
   103	            rows.append((sid, k, s.lifecycle, v, x))
   104	
   105	    n = sum(tally.values())
   106	    print(f"\n===== {arm}: names introduced on the {FAMILY} family ({n} requests, "
   107	          f"{n // 2} sessions)")
   108	    print("  NOT a retention measure -- see this file's docstring.")
   109	    for v in ("in-force", "alt", "neither", "vacuous"):
   110	        if tally[v]:
   111	            print(f"    {v:9s} {tally[v]:3d}  ({100 * tally[v] / max(n, 1):.0f}%)")
   112	    print("  by population (request, alternative was in force earlier):")
   113	    for key in sorted(cells):
   114	        t = cells[key]
   115	        print(f"    req{key[0]} superseded={key[1]!s:5s} n={sum(t.values()):3d}  "
   116	              + "  ".join(f"{v}={t[v]}" for v in
   117	                          ("in-force", "alt", "neither", "vacuous") if t[v]))
   118	    print("  agreement with the executable contract measure (stale2.classify):")
   119	    same = sum(c for (v, x), c in agree.items() if v == x)
   120	    print(f"    identical verdict on {same}/{n}")
   121	    for (v, x), c in sorted(agree.items()):
   122	        if v != x:
   123	            print(f"    names={v:9s} contract={x:15s} {c}")
   124	    dis = [r for r in rows if r[3] != r[4]]
   125	    if dis:
   126	        print("  the requests where they disagree (worth reading):")
   127	        for sid, k, lc, v, x in dis:
   128	            print(f"    {sid} req{k} {lc:14s} names={v:9s} contract={x}")
   129	
   130	
   131	if __name__ == "__main__":
   132	    for p in sys.argv[1:]:
   133	        run(p)
     1	"""The candidate-A screen's launch spend ledger and budget guards (F13, F12).
     2	
     3	Every case here is one of the escapes a review demonstrated by executing the accounting:
     4	an interrupted launch charged less than it spent (round 5: a last checkpoint at 600 s
     5	and death at 1,200 s charged 900 s; round 6: death at 900 s DURING MODEL LOADING charged
     6	600 s, and the pilot's 44-suite gap lay outside the post-load bound), a torn ledger line
     7	erasing a launch entirely, a request admitted with two minutes of budget left running a
     8	full 300 s generation plus scoring and still reporting COMPLETE, and complete records
     9	from an over-budget evaluation producing the authoritative GATE PASSED verdict.
    10	"""
    11	
    12	from __future__ import annotations
    13	
    14	import json
    15	import os
    16	from pathlib import Path
    17	
    18	from stencil import a_screen as A
    19	
    20	T0 = 1_000_000.0
    21	DEAD = "1000-999999"  # a launch id whose pid cannot exist, so it can be observed dead
    22	MINE = f"1000-{os.getpid()}"  # a launch id whose pid is alive: this process
    23	
    24	
    25	BOOT = A.boot_id()
    26	
    27	
    28	def _write(path, launch, events, t0=T0, boot=None):
    29	    """Ledger lines in the production format: a realtime ``t`` for the calendar and a
    30	    MONOTONIC ``m`` under this boot's id for every duration (round 9).  ``m`` is written
    31	    on the same scale as ``t`` so a test can pass one number for both clocks.  Pass
    32	    ``boot=""`` to write a line whose monotonic reading is not comparable here -- a
    33	    legacy ledger, or one from an earlier boot -- which falls back to realtime."""
    34	    with path.open("a") as fh:
    35	        for event, elapsed in events:
    36	            rec = {
    37	                "launch": launch,
    38	                "event": event,
    39	                "t": t0 + elapsed,
    40	                "elapsed_s": elapsed,
    41	            }
    42	            if boot != "":
    43	                rec["m"] = t0 + elapsed
    44	                rec["boot"] = BOOT if boot is None else boot
    45	            fh.write(json.dumps(rec) + "\n")
    46	
    47	
    48	def _charges(path, exclude, at):
    49	    """``ledger_charges`` with both clocks reading ``at``: the tests write ``m`` on the
    50	    same scale as ``t``, so one number drives realtime and monotonic alike."""
    51	    return A.ledger_charges(path, exclude, at, at)
    52	
    53	
    54	def test_a_mark_measures_its_duration_on_the_monotonic_clock(monkeypatch, tmp_path):
    55	    """Round 9, high: ``elapsed_s`` came from ``time.time()``, which can be STEPPED by
    56	    NTP or by hand.  Astra stepped it 600 s backwards 360 s into a 900 s launch: the
    57	    ledger charged 300 s, and beside 2,400 s of other work the real summary printed GATE
    58	    PASSED at 45 charged minutes against 55 spent.  The step forwards is just as bad --
    59	    a legitimate 45-minute run charged 55 and reported INCOMPLETE."""
    60	    p = tmp_path / "spend.jsonl"
    61	    monkeypatch.setattr(A.time, "time", lambda: T0 - 600.0)  # stepped backwards
    62	    monkeypatch.setattr(A.time, "monotonic", lambda: T0 + 900.0)
    63	    A.ledger_mark(p, DEAD, "end", T0, T0)
    64	    rec = json.loads(p.read_text().splitlines()[0])
    65	    assert rec["elapsed_s"] == 900.0  # the real duration, not the stepped one
    66	    assert rec["t"] == T0 - 600.0 and rec["m"] == T0 + 900.0
    67	    assert rec["boot"] == BOOT
    68	
    69	
    70	def test_an_unfinished_launch_is_measured_on_the_monotonic_clock(tmp_path):
    71	    # the third charging case compares NOW with the launch's earliest reading, so that
    72	    # comparison is monotonic too: realtime says 5,000 s, the monotonic clock says 900
    73	    p = tmp_path / "spend.jsonl"
    74	    _write(p, DEAD, [("start", 0.0)])
    75	    assert A.ledger_charges(p, "B", T0 + 5000.0, T0 + 900.0)[0][DEAD] == 900.0
    76	
    77	
    78	def test_an_unfinished_launch_from_another_boot_is_unbounded(tmp_path):
    79	    """Round 10: the realtime fallback was ASSUMED to over-charge, and it does not.
    80	    A launch run to 900 s across a reboot, with 10 s of downtime and a 600 s
    81	    backward step, spans 310 s by realtime and charges the 600 s mark; beside
    82	    2,400 s of completed work the arm then reads 50 minutes charged against 55
    83	    spent.  Downtime establishes no direction, so the launch is UNBOUNDED."""
    84	    for name, boot in (("other.jsonl", "0000-not-this-boot"), ("legacy.jsonl", "")):
    85	        p = tmp_path / name
    86	        _write(p, DEAD, [("start", 0.0), ("tick", 600.0)], boot=boot)
    87	        charges, malformed, unbounded = A.ledger_charges(p, "B", T0 + 310.0, T0 + 900.0)
    88	        assert malformed == 0
    89	        assert unbounded == [DEAD]
    90	        assert charges[DEAD] == 600.0  # the best-effort number, not a trusted one
    91	        spent, refusals = A.ledger_spent_min(p, {DEAD}, T0 + 310.0, T0 + 900.0)
    92	        assert len(refusals) == 1 and "not bounded in either direction" in refusals[0]
    93	
    94	
    95	def test_an_unobservable_launch_is_not_sealed(tmp_path):
    96	    """The observation is the other half: sealing a realtime subtraction as
    97	    verified spend would fix the wrong number permanently, so a launch with no
    98	    monotonic origin from this boot is not observed at all."""
    99	    p = tmp_path / "other.jsonl"
   100	    _write(p, DEAD, [("start", 0.0), ("tick", 600.0)], boot="0000-not-this-boot")
   101	    assert A.ledger_observe(p, clock=lambda: T0 + 900.0, wall=lambda: T0 + 310.0) == []
   102	    assert "observed_dead" not in p.read_text()
   103	    _, _, unbounded = A.ledger_charges(p, "B", T0 + 310.0, T0 + 900.0)
   104	    assert unbounded == [DEAD]
   105	
   106	
   107	def test_a_finished_launch_from_another_boot_is_still_charged(tmp_path):
   108	    """The refusal is for launches with no BOUND, not for every cross-boot record: one
   109	    that wrote ``end`` carries its own measured elapsed and is charged it."""
   110	    p = tmp_path / "other.jsonl"
   111	    _write(p, DEAD, [("start", 0.0), ("end", 1500.0)], boot="0000-not-this-boot")
   112	    charges, malformed, unbounded = A.ledger_charges(p, "B", T0 + 310.0, T0 + 900.0)
   113	    assert (malformed, unbounded) == (0, [])
   114	    assert charges[DEAD] == 1500.0
   115	    assert A.ledger_spent_min(p, {DEAD}, T0 + 310.0, T0 + 900.0) == (25.0, [])
   116	
   117	
   118	def test_no_duration_is_measured_on_the_wall_clock():
   119	    """The mechanical form of round 9's fix: nothing in the screen subtracts wall-clock
   120	    readings.  ``time.time()`` survives only as a calendar stamp and as the documented
   121	    fallback for a launch with no comparable monotonic origin.
   122	
   123	    Round 10, high: the TRAINER was not in this list, and it was still timing its
   124	    admission guard, its saves and its final eligibility on the wall clock -- a 600 s
   125	    backward step let a 14,930-second run record 14,330 and read ``complete`` against
   126	    the registered 14,400-second allocation."""
   127	    for name in (
   128	        "src/stencil/a_screen.py",
   129	        "scripts/a_screen_run.py",
   130	        "scripts/a_screen_summary.py",
   131	        "scripts/a_screen_train.py",
   132	    ):
   133	        src = (ROOT / name).read_text()
   134	        bad = []
   135	        for ln in src.splitlines():
   136	            if "time.time()" not in ln:
   137	                continue
   138	            before, _, after = ln.partition("time.time()")
   139	            if after.lstrip().startswith("-") or before.rstrip().endswith("-"):
   140	                bad.append(ln.strip())
   141	        assert not bad, f"{name}: duration taken from the wall clock: {bad}"
   142	
   143	
   144	def test_an_interrupted_launch_is_charged_through_now(tmp_path):
   145	    # round 5: last checkpoint at 600 s, death at 1,200 s was charged 900 s
   146	    p = tmp_path / "spend.jsonl"
   147	    _write(p, DEAD, [("start", 0.0), ("model_loaded", 80.0), ("record", 600.0)])
   148	    charges, malformed, _unbounded = _charges(p, "B", T0 + 1300.0)
   149	    assert malformed == 0
   150	    assert charges[DEAD] == 1300.0
   151	
   152	
   153	def test_silence_does_not_bound_a_launch(tmp_path):
   154	    """Round 7 F13: the heartbeat rule charged a launch its last tick plus three
   155	    intervals when no gap was wider than the slack. But a ledger with ticks to 600 s
   156	    is equally consistent with death at 600 s and with a TICKER that failed at 600 s
   157	    while the process ran on -- Astra killed the ticker thread by injecting an append
   158	    failure and the main thread carried on. Absence of a mark is not evidence of
   159	    termination."""
   160	    p = tmp_path / "spend.jsonl"
   161	    ticks = [("tick", float(x)) for x in range(0, 601, 60)]
   162	    _write(p, DEAD, [("start", 0.0), *ticks])
   163	    # the old rule charged 600 + 180 = 780 whatever the read time
   164	    assert _charges(p, "B", T0 + 1500.0)[0][DEAD] == 1500.0
   165	    assert _charges(p, "B", T0 + 9000.0)[0][DEAD] == 9000.0
   166	
   167	
   168	def test_an_observation_bounds_it_and_then_never_moves(tmp_path):
   169	    # the charge is bounded by EVIDENCE: a process that is gone at a known time cannot
   170	    # have lived past it, and the observation is recorded once so later reads agree
   171	    p = tmp_path / "spend.jsonl"
   172	    _write(p, DEAD, [("start", 0.0), ("record", 600.0)])
   173	    assert A.ledger_observe(p, clock=lambda: T0 + 1500.0) == [DEAD]
   174	    assert _charges(p, "B", T0 + 1500.0)[0][DEAD] == 1500.0
   175	    assert _charges(p, "B", T0 + 99_999.0)[0][DEAD] == 1500.0
   176	    # recorded once, never re-recorded
   177	    assert A.ledger_observe(p, clock=lambda: T0 + 99_999.0) == []
   178	
   179	
   180	def test_the_observation_is_timestamped_after_the_probe(tmp_path):
   181	    """Round 8 F13: the caller sampled ``now`` once and passed it in, so a process
   182	    descheduled between that sample and the pid probe wrote a BACKDATED observation --
   183	    sampled at 300 s, probed at 1,000 s, permanently charging 300 s for a launch that
   184	    lived to 900.  Absence at the probe establishes termination by the PROBE's time.
   185	
   186	    Round 9 makes the property structural: the function takes ONE duration reading and
   187	    takes it after the probe, and the wall clock it reads for the calendar stamp --
   188	    300 s here -- cannot reach the charge at all."""
   189	    p = tmp_path / "spend.jsonl"
   190	    _write(p, DEAD, [("start", 0.0)])
   191	    seen = []
   192	
   193	    def probe_clock():
   194	        seen.append("probe")
   195	        return T0 + 1000.0
   196	
   197	    observed = A.ledger_observe(p, clock=probe_clock, wall=lambda: T0 + 300.0)
   198	    assert observed == [DEAD]
   199	    assert seen == ["probe"]  # sampled exactly once, after the pid probe succeeded
   200	    assert _charges(p, "B", T0 + 5000.0)[0][DEAD] == 1000.0
   201	
   202	
   203	def test_a_live_launch_is_not_observed_dead(tmp_path):
   204	    # a running process, or a recycled pid, must keep accruing: the conservative
   205	    # direction
   206	    p = tmp_path / "spend.jsonl"
   207	    _write(p, MINE, [("start", 0.0)])
   208	    assert A.ledger_observe(p, clock=lambda: T0 + 500.0) == []
   209	    assert _charges(p, "other", T0 + 500.0)[0][MINE] == 500.0
   210	
   211	
   212	def test_a_launch_killed_while_loading_is_charged_its_loading_time(tmp_path):
   213	    # round 6 F13: model loading had no enforced limit, so a launch killed while loading
   214	    # at 900 s and read at 1,200 s was charged the 600 s load bound
   215	    p = tmp_path / "spend.jsonl"
   216	    _write(p, DEAD, [("start", 0.0)])
   217	    assert _charges(p, "B", T0 + 1200.0)[0][DEAD] == 1200.0
   218	    A.ledger_observe(p, clock=lambda: T0 + 1200.0)
   219	    assert _charges(p, "B", T0 + 1200.0)[0][DEAD] == 1200.0
   220	
    17	reference scoring done in 1855s
    18	trainable params: 33,030,144 || all params: 4,055,498,240 || trainable%: 0.8145
    19	/home/bmarti44/stencil-llm/scripts/a_screen_train.py:364: UserWarning: Converting a tensor with requires_grad=True to a scalar may lead to unexpected behavior.
    20	Consider using tensor.detach() first. (Triggered internally at /__w/pytorch/pytorch/torch/csrc/autograd/generated/python_variable_methods.cpp:822.)
    21	  ce_only.append(float(-lp_c / n_c))
    22	step 10 loss 0.1434 ce 0.0681 margin +0.6368 micro 80 2743s/14400s
    23	step 20 loss 0.0698 ce 0.0281 margin +2.7719 micro 160 4290s/14400s
    24	step 30 loss 0.0302 ce 0.0123 margin +4.6236 micro 240 5777s/14400s
    25	step 40 loss 0.0154 ce 0.0068 margin +6.0415 micro 320 6935s/14400s
    26	step 50 loss 0.0066 ce 0.0043 margin +7.4726 micro 400 7621s/14400s
    27	step 60 loss 0.0036 ce 0.0012 margin +6.3987 micro 480 8313s/14400s
    28	step 70 loss 0.0023 ce 0.0016 margin +7.8630 micro 560 9004s/14400s
    29	step 80 loss 0.0012 ce 0.0006 margin +8.1871 micro 640 9693s/14400s
    30	step 90 loss 0.0006 ce 0.0002 margin +8.8775 micro 720 10381s/14400s
    31	step 100 loss 0.0010 ce 0.0004 margin +8.4491 micro 800 11234s/14400s
    32	step 110 loss 0.0010 ce 0.0003 margin +8.6205 micro 880 12694s/14400s
    33	step 120 loss 0.0009 ce 0.0006 margin +9.5774 micro 960 13382s/14400s
    34	step 130 loss 0.0003 ce 0.0001 margin +8.7993 micro 1040 14069s/14400s
    35	DONE objective=cf steps=134 epochs=0 discarded=6 tokens=6554934 final_loss=0.0001408661725008642 seconds=14399
   150	        ap.error(
   151	            f"--max-new {a.max_new} is not the registered {A.MAX_NEW_TOKENS}; a full "
   152	            "screen arm runs at the registered output cap"
   153	        )
   154	    adapter_steps = None
   155	    if a.adapter:
   156	        # Astra F13: the registered quantity is the adapter at the FINAL COMPLETED optimizer
   157	        # step of one uninterrupted allocation.  The trainer also writes periodic crash
   158	        # checkpoints marked status=running/final=false; refuse those.  Checked before the
   159	        # model load so a wrong adapter costs no GPU time.
   160	        tl = Path(a.adapter) / "train-log.json"
   161	        if not tl.exists():
   162	            ap.error(
   163	                f"{a.adapter}: no train-log.json; cannot verify the adapter is final"
   164	            )
   165	        tlog = json.loads(tl.read_text())
   166	        final_ok = tlog.get("final") is True and tlog.get("status") == "complete"
   167	        if not final_ok and not a.pilot_adapter:
   168	            ap.error(
   169	                f"{a.adapter}: train-log says final={tlog.get('final')} "
   170	                f"status={tlog.get('status')}; only a final adapter may be evaluated. "
   171	                "Pass --pilot-adapter to use it for timing only."
   172	            )
   173	        if tlog.get("objective") != a.arm:
   174	            ap.error(
   175	                f"{a.adapter}: trained objective {tlog.get('objective')!r} "
   176	                f"does not match arm {a.arm!r}"
   177	            )
   178	        adapter_steps = tlog.get("steps")
   179	        # re-review F13: `final=True` alone accepted a 180-second, zero-step smoke adapter
   180	        # trained on eight sessions from a stale pool.  A screen adapter must be the
   181	        # registered allocation: the full frozen TRAIN pool, no --limit, positive completed
   182	        # optimizer steps, and the registered wall clock.  --pilot-adapter opts out for the
   183	        # timing pilot, and the opt-out is recorded in every record's identity.
   184	        ident = tlog.get("identity", {})
   185	        frozen_train = json.loads(
   186	            (ROOT / "results/a-screen/train-pool.json").read_text()
   187	        )["pool_sha256"]
   188	        problems = []
   189	        if not final_ok:
   190	            problems.append(f"final={tlog.get('final')} status={tlog.get('status')}")
   191	        if ident.get("train_pool_sha256") != frozen_train:
   192	            problems.append(
   193	                f"TRAIN pool {ident.get('train_pool_sha256')} != frozen {frozen_train}"
   194	            )
   195	        if ident.get("limit"):
   196	            problems.append(f"trained on a --limit {ident['limit']} subset")
   197	        if not isinstance(adapter_steps, int) or adapter_steps < 1:
   198	            # re-review round 3: "not adapter_steps" was a truthiness test and accepted -1
   199	            problems.append(f"completed optimizer steps = {adapter_steps!r}")
   200	        if tlog.get("budget_seconds") != REGISTERED_TRAIN_SECONDS:
   201	            problems.append(
   202	                f"allocation {tlog.get('budget_seconds')}s != registered "
   203	                f"{REGISTERED_TRAIN_SECONDS}s"
   204	            )
   205	        if ident.get("hub") != str(a.hub):
   206	            problems.append(
   207	                f"trained on trunk {ident.get('hub')!r}, evaluating on {str(a.hub)!r}"
   208	            )
   209	        # Round 4 F15: the train log RECORDED these hashes and nothing checked them, so a
   210	        # stale trainer, a stale packing policy or a stale pool builder were all accepted.
   211	        # Validate each against the current file, and bind the trunk by BYTES, not pathname.
   212	        for field_name, current in (
   213	            (
   214	                "trainer_sha256",
   215	                sha(Path(__file__).parent.joinpath("a_screen_train.py").read_text()),
   216	            ),
   217	            ("a_screen_sha256", sha((ROOT / "src/stencil/a_screen.py").read_text())),
   218	            (
   219	                "a_train_pool_sha256",
   220	                sha((ROOT / "src/stencil/a_train_pool.py").read_text()),
   221	            ),
   222	            ("hub_sha256", A.dir_sha(Path(a.hub))),
   223	        ):
   224	            if ident.get(field_name) != current:
   225	                problems.append(
   226	                    f"{field_name}={ident.get(field_name)!r}, current {current!r}"
   227	                )
   228	        # re-review round 3 F13/F15: the registered recipe, not merely a finished run
   229	        for field, want in REGISTERED_TRAIN_CONFIG.items():
   230	            if tlog.get(field) != want:
   231	                problems.append(f"{field}={tlog.get(field)!r}, registered {want!r}")
   232	        # 2026-09-13 (Astra): a minimum ELAPSED time was a proxy for "a real allocation
   233	        # ran", and it rejects the very adapter this screen needs.  The two objectives are
   234	        # not comparable at equal wall clock -- cf precomputes reference log-probs and then
   235	        # runs two forward passes per micro-step where sft runs one -- so sft is trained to

exec
/bin/bash -lc "PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -u - <<'PY'
import sys,json,collections,copy,io,contextlib
from unittest.mock import patch
sys.path[:0]=['src','results/a-screen/analysis','tests']
import compare as C,stale2 as S
from stencil import a_screen as A
from stencil.a_screen_pool import screen_sessions,load
from stencil.a_train_pool import train_sessions
ss=list(screen_sessions())+list(train_sessions())
print('alt_was_in_force vs metadata over 624 x 2',sum(S.alt_was_in_force(s,k)"'!=(s.lifecycle=='"'reinstatement' if k==1 else s.lifecycle"'!='"'stable') for s in ss for k in (1,2)))
print('test file imports consumer', 'stale2' in __import__('ast').dump(__import__('ast').parse(open('tests/test_a_screen_supersession.py').read())).split('body=')[0])
n=0
for s in train_sessions():
 for p in A.pairs_from_session(s):
  history={s.state_at[0]}
  if s.lifecycle=='reinstatement':history.add(s.states[0])
  n+=p.rejected_state in history
print('rejected state was previously inforce',n,'of1152')
base=[json.loads(l) for l in open('results/a-screen/runs/off-oldrunner.jsonl')]
replayfail=[]
for sid in sorted({r['session'] for r in base}):
 s=load(sid);rr={r['request']:r for r in base if r['session']==sid};ent=S.replay(s,rr)
 for k,r in rr.items():
  for key,i in [('repo_before',k),('repo_after',k+1)]:
   if S.repo_hash(ent[i])"'!=r[key]:replayfail.append((sid,k,key))
print('"'actual before/after hashes errors',replayfail)
print('J/session',sum(r.get('J',False) for r in base if r['request']==2),'FO/session',sum(r.get('function_only',False) for r in base if r['request']==2),'FO/reply',sum(r['scores']['function_only'] for r in base))
# Exact consumer scoring path: no contract execution is needed to test score-field handling.
rr={(r['session'],r['request']):copy.deepcopy(r) for r in base}
for r in rr.values():r['scores']={}
with patch.object(C,'classify',return_value='in-force'):
 ch,un=C.score_arm(rr)
print('missing suites silently become failures',len(ch),sum(r['j'] for r in ch.values()),sum(r['function_only'] for r in ch.values()))
# Exercise self_check with a broken instrument that still handles the three sampled naming sessions.
from stencil.a_screen_pool import available_slots
print('selfcheck default sampled IDs and families',[(sid,load(sid).target_family) for sid in available_slots()[:3]])
PY" in /home/bmarti44/stencil-llm
 succeeded in 371ms:
alt_was_in_force vs metadata over 624 x 2 0
test file imports consumer False
rejected state was previously inforce 576 of1152
actual before/after hashes errors []
J/session 6 FO/session 15 FO/reply 39
missing suites silently become failures 36 0 0
selfcheck default sampled IDs and families [('S01', 'naming'), ('S02', 'naming'), ('S03', 'naming')]

codex
Two checks materially weaken the new training and overlap claims. Of 1,152 training positives, only 1,007 have distinct completion text; 121 completed first-pass examples repeated a completion already encountered. Turning off difflib’s automatic “popular character” filtering raises the maximum similarity among the same candidate pairs from 0.254 to 0.517. I also confirmed zero exact whole-file matches between screen and training golds, which supports that narrower statement.

exec
/bin/bash -lc "PYTHONDONTWRITEBYTECODE=1 .venv/bin/python - <<'PY'
import json,collections,sys
sys.path.insert(0,'src')
from stencil.a_screen_pool import load
base={(r['session'],r['request']):r for r in map(json.loads,open('results/a-screen/runs/off-oldrunner.jsonl'))}
state=json.load(open('results/a-screen/analysis/out/off-oldrunner-states.json'))
print('record keys',list(state),'records',len(state['records']))
for cat in ('in-force','alt'):
 rr=[r for r in state['records'] if r['request']==2 and r['alt_was_in_force'] and r['category']==cat]
 print(cat,'count',len(rr),'functional',sum(base[r['session'],2]['scores']['functional'] for r in rr),'function_only',sum(base[r['session'],2]['scores']['function_only'] for r in rr),'all6',sum(base[r['session'],2]['scores']['all'] for r in rr))
print('instrument empty contract suites',sum(not tests for sid in sorted({k[0] for k in base}) for rq in load(sid).requests for tests in rq.contract_tests.values()))
PY" in /home/bmarti44/stencil-llm
 succeeded in 0ms:
record keys ['arm', 'source', 'sessions', 'replay_mismatches', 'records'] records 96
in-force count 11 functional 6 function_only 3 all6 3
alt count 12 functional 8 function_only 7 all6 0
instrument empty contract suites 0

codex
I’m finishing the investment judgment and prior-finding dispositions. The screen’s weakness is not just sample size: its scoped cases test a new operation inside the exception, and every reinstatement message restates the desired rule. Success can therefore reflect following the latest explicit instruction plus preserving existing code. A cheaper matched test should require fresh behavior both inside and outside the scope, and restoration without restating the old rule.

exec
/bin/bash -lc "wc -l plan/LEDGER.md && tail -n 70 plan/LEDGER.md && nl -ba results/a-screen/REGISTRATION-A-SCREEN.md | sed -n '205,240p'" in /home/bmarti44/stencil-llm
 succeeded in 0ms:
4018 plan/LEDGER.md
  single generation is the amendment spiral AGENTS.md names, and the orchestrator is supposed to be
  the terminator. Acting on that:
  - **Round-10 finding 2 fixed by deletion.** Astra demonstrated the generic fixture
    `test_no_public_call_disturbs_the_id_allocator` REJECTS a correct reply: a behaviour-preserving
    `initialize_bank(bank, accounts)` constructor refactor makes the fixture call it with a junk
    string and the suite then fails (`_initialize_bank` passes) — a false J = 0 in 23 of 48 slots.
    The fixture was added in round 9 only to argue audit coverage; it is reverted out of all 23
    slots (`git checkout eecde769^ -- src/stencil/a_screen_pool/`). SCREEN pool back to
    **ef802ce2160ee00c**. The per-operation create-after-operation tests of amendment 6 stay.
  - **Round-10 findings 3 and 4 kept** (monotonic durations in `a_screen.py`, `a_screen_run.py`,
    `a_screen_train.py`; unbounded cross-boot launches refused): those make budget accounting WRONG,
    they are cheap, and they are already written and tested.
  - **Round-10 finding 1 dropped for now.** It says the mutation audit under-tests my suites for
    resets placed below a lookup. That is a sensitivity property of the instrument, not a bias: it
    applies identically to `off`, `sft` and `cf`, so it cannot manufacture a difference between
    arms. It is a thing to fix if and when there is a positive result worth proving.
  - No amendment 10, no round-11 prompt, no re-registration. The registration stands as written and
    the deltas above are recorded here instead.
STATE: running the candidate-A screen. SCREEN pool ef802ce2160ee00c, TRAIN b8f504494a281858.
Order: gold check + trainer/runner smoke -> timing pilot (`--longest 4`) -> notify peer
"looped-transformer" -> train sft then cf (4 h each) -> run 3 x 48 -> summary. Peer holds the GB10
until ~17:30Z (notasearch-luna-pool1, 40 GB of 119); Stencil peaks 8-15 GB, so we share.

- 2026-09-13 16:10Z — **PRE-COMMITTED STOP RULE for the candidate-A screen** (Brian: "if it looks
  like the numbers are not going our way, let's pause the GPU work... I'd like to run something
  else on GPU if this is not going in a good direction"). Written BEFORE the first adapter number
  exists so it cannot be rationalised afterwards.
  - **Primary measure**: replies satisfying the contract IN FORCE at request 2 of the 36 sessions
    whose convention CHANGED. Baseline `off` = **11/36 in-force, 12/36 stale, 13/36 neither**.
  - **Decision point**: when `cf` training ends (~19:15Z) it is evaluated on all 48 sessions
    (~62 min). That yields `off` vs `cf` at ~20:20Z, which is a valid FUTILITY screen even though
    it cannot isolate the objective: `cf` contains ordinary supervised training, so if `cf` does
    not beat `off`, `sft` will not either and the direction is dead.
  - **CONTINUE** to `sft` only if `cf` reaches **>= 16/36 in-force** (a lift of +5 or more).
  - **PAUSE GPU** if `cf` <= 13/36 (a lift of +2 or less, inside noise at this n): release the
    GB10 for Brian's other work, tell the peer, and carry on with Astra reviews on CPU only.
  - **14-15/36 is the ambiguous band**: report the number and the McNemar discordance to Brian
    with a recommendation, do not decide unilaterally.
  - Earlier warning, free: the training margin. `+0.6368` at step 10 says the preference term
    separates the in-force gold from the stale one. A collapse toward 0 or a negative trend is
    reported immediately as a bad sign.

- 2026-09-13 18:20Z — **GPU PAUSED after cf training, by Brian** ("you can let this run finish and
  then pause using more GPU"). The `cf` allocation is allowed to complete; nothing further
  launches. The GB10 goes to the peer session and to whatever Brian wants to run.
  - **DONE and on disk**: the `off` baseline over all 48 sessions
    (`results/a-screen/runs/off-oldrunner.jsonl`, J=6, function-only=15, 61.6 min, COMPLETE) and
    the `cf` adapter (`results/a-screen/adapters/cf/`).
  - **NOT done**: the `cf` evaluation, `sft` training, the `sft` evaluation, and the `off` re-run
    on the fixed runner. So there is NO adapter-vs-baseline number yet, and the pre-committed
    stop rule above has not been evaluated. Nothing about the direction is settled either way.
  - **Resume needs 4 GPU steps, in this order** (~4.5 h total at an uncontended rate):
    1. `off` re-run on the current runner (~62 min) so all arms share one `runner_sha256`;
       `off-oldrunner.jsonl` was produced before the eligibility-guard fix and its identity
       differs by that one hunk.
    2. `cf` eval: `a_screen_run.py --arm cf --adapter results/a-screen/adapters/cf` (~62 min).
       THIS IS THE FUTILITY SCREEN -- apply the stop rule above before spending anything more.
    3. `sft` training matched to cf's achieved step count via `--max-steps` (~1.5-2 h).
    4. `sft` eval with `--require-steps <cf steps>` (~62 min).
  - **Before each eval** run the CPU preflight
    (`scratchpad/preflight.py <adapter> [steps]`, and `--compare cf sft` once both exist). It is
    mutation-tested 13/13 and checks everything the runner checks, in a second rather than after
    the GPU hours are spent.
  - **FROZEN while paused** -- editing any of these invalidates the cf adapter or the run
    identity, and the adapter cost 4 GPU-h: `scripts/a_screen_train.py`, `scripts/a_screen_run.py`,
    `src/stencil/a_screen.py`, `src/stencil/a_train_pool.py`, and `src/stencil/a_screen_pool/`.
  - Training health at the pause: margin +0.64 -> +8.45 (monotone bar one dip), CE 0.068 ->
    0.0004, objective saturated. So a later null would read as failure to TRANSFER, not as
    undertraining -- the adapter learned the training distribution thoroughly.
  - CPU work continues: Astra reviews, analysis, and the writeup. No GPU.
   205	
   206	### 13.2 Pool checkers (F9, mutation-verified)
   207	
   208	Both claims were tested by mutating gold and re-running the suite. **Confirmed:** the
   209	missing-record "returns None and changes nothing" test asserted only `find("zz") is None`, so
   210	an implementation that **cleared the entire store** passed; it now snapshots the complete
   211	record mapping before and after the unknown-id call, and the `raise` state does the same.
   212	**Confirmed with a correction:** Astra located the logging defect in the `silent` state, where
   213	`assert caplog.records == []` is in fact airtight at every level; the defect is in the **`warn`**
   214	state's "active records produce no log record" test, which checked only `levelno >= WARNING`, so
   215	an implementation logging at INFO on every call passed. It now asserts zero captured records.
   216	
   217	### 13.3 What the disjointness check establishes (F10)
   218	
   219	§1 said "disjoint solution constructions … by project name, package layout, function names and
   220	test bodies". That overstated the verification. **Verified and enforced** by
   221	`scripts/a_screen_freeze.py`: SCREEN package names are unique and shared with no other pool; no
   222	module path is shared with TRAIN; no public class or function name is shared with TRAIN outside a
   223	fixed generic allowlist. **Not claimed:** disjoint constructions. The pools deliberately share a
   224	coding idiom, and the freeze record's `overlap` block now measures it: all 48 slots share at
   225	least one module basename with TRAIN (`__init__.py`, `model.py`, `store.py`, `errors.py`), 0
   226	slots reproduce TRAIN's full four-module shape, 44/48 use the same dataclass-record plus
   227	private-mapping idiom, and 0 normalised test files are identical. The screen therefore tests
   228	generalisation across projects and wording, not across program architecture, and the §6 outcome
   229	is read that way.
   230	
   231	### 13.4 Statistics (F11, F12)
   232	
   233	`paired()` uses **alpha = 0.025** per component interval, as §7 registered; the zero-discordance
   234	width recomputes to 8.72 points. The summary now loads **both** requests per session, refuses
   235	duplicate records and records from more than one `identity`, refuses a request 2 with no request
   236	1, **recomputes** each session outcome from the stored suites and fails if the stored outcome
   237	disagrees, aggregates diagnostics over both requests, and reads INCOMPLETE against the frozen
   238	48-slot manifest by name.
   239	
   240	### 13.5 Allocation chunking and resumption (F13)

codex
**OFF TRACK. Candidate A does not currently establish a substantive recombination, and renaming its target “conditional revision” does not repair that. My artifact-success forecast is 15%, below your 25% bar.** The underlying problem remains useful; the present evidence and experiment do not adequately distinguish its proposed solution from ordinary instruction tuning and simple recency or copying strategies.

This session permits filesystem reads only, so I could not save the review file. I read the prior review and governing process, read nothing under `data/bench/`, used no GPU, and changed no files. I independently checked all 96 baseline replay chains against both recorded repository hashes, executed the four population tests directly, exercised additional guard mutations in memory, checked the actual completed adapter’s preflight, and recomputed the reported statistical thresholds. I did not rerun the complete subprocess-based contract evaluation or the full pytest suites.

**1. Candidate A: no substantive methodological novelty established — high.**

The loss is ordinary completion-token cross-entropy plus a weighted DPO term. Its distinguishing choice is the construction of preference pairs. The implementation agrees with that description. [/home/bmarti44/stencil-llm/scripts/a_screen_train.py:353](/home/bmarti44/stencil-llm/scripts/a_screen_train.py:353)

The strongest challenges are:

| Prior work | What it already establishes | What remains distinguishable here |
|---|---|---|
| **Counterfactual DPO**, Butcher, 2024 | Counterfactual prompting supplies preference pairs for behavioral alignment. | Stencil’s executable, temporal coding setting. [Paper](https://arxiv.org/abs/2401.09566) |
| **Context-DPO**, Bi et al., Findings of ACL 2025 | Preferences favor context-faithful answers over stubborn alternatives, with an SFT comparison. | Superseded conversational rules, rather than principally conflicts with parametric factual knowledge. [Paper](https://aclanthology.org/2025.findings-acl.536/) |
| **IOPO**, 2024 preprint | Closely related instructions receive different preferred outputs. Particularly damaging: its **DPO\*** comparison explicitly trains both crossed preference directions, while **SFT\*** receives both matching positives. | Temporal executable constraints and preservation requirements; not the crossed-pair construction itself. [Section 6.2](https://arxiv.org/html/2411.06208v1) |
| **CRPL**, August 2026 preprint | Preference construction models relationships between permissible response spaces and verifies atomic constraints. | A demonstrated temporal, stateful coding advantage beyond those general ideas. [Paper](https://arxiv.org/abs/2608.29352) |
| **Mitigating Conversational Inertia**, February 2026 preprint | LoRA/DPO learns preferences intended to escape harmful dependence on preceding agent behavior. | Explicit rule applicability and selective preservation. Its preferences come from different context lengths, so it is adjacent rather than identical. [Section 2.1](https://arxiv.org/html/2602.03664v1) |

IOPO’s DPO\*/SFT\* construction is a stronger objection than merely observing that “DPO exists.” It anticipates an important part of Stencil’s proposed recombination: the same response can be preferred under one input and rejected under another, with both positive directions supplied to SFT.

There is also a naming correction. **Only 576 of the 1,152 constructed training pairs reject a state that was previously in force in that history.** The rest reject another convention that was not previously applicable as the new-operation rule. That is appropriate for learning when to preserve behavior, but “every rejected response follows a superseded convention” is false. The relevant construction includes stable and irrelevant-event pairs. [/home/bmarti44/stencil-llm/src/stencil/a_screen.py:463](/home/bmarti44/stencil-llm/src/stencil/a_screen.py:463)

What could remain substantive is an empirical result:

> A small adapter learns to apply revisions selectively to executable behavior, including fresh out-of-scope behavior and restoration, with a useful advantage over matched SFT and transfer beyond the training generator.

That would be a contribution through demonstrated capability, data construction and evaluation. It would not make this loss a new method. **Today, that result is absent.** Adding lifecycle names to established preference learning is insufficient.

**2. Conditional revision is a better specification, but is already prior art — high.**

My earlier suggestion needs this qualification: it identified a promising *claim to test*, not an unoccupied research area.

Several strands already cover substantial parts of it:

- **Belief-R, EMNLP 2024**, explicitly tests whether models should revise a conclusion or retain it. Its reported trade-off—models that update well can perform worse when updating is unnecessary—is directly relevant to “switch when applicable, preserve otherwise.” It evaluates inference, not stateful code editing. [Paper](https://aclanthology.org/2024.emnlp-main.586/)
- **SERAC, ICML 2022**, uses an edit-scope classifier and a counterfactual model, returning the base model’s prediction outside edit scope. Broad “scoped modification without unrelated disruption” claims were already occupied before 2024. [Paper](https://proceedings.mlr.press/v162/mitchell22a/mitchell22a.pdf)
- **EvolIF, November 2025 preprint**, maintains separate topic instruction states, adds/deletes/modifies their constraints, and returns to earlier topics. It therefore anticipates a considerable portion of the behavioral taxonomy. Its independently managed topics do not establish arbitrary overlapping coding scopes or preservation of executable artifacts. [Sections 3.2.1–3.2.3](https://arxiv.org/html/2511.03508v1)
- **TOKI, June 2026 preprint**, treats contradictory agent-memory writes through temporal versions, explicit resolution policies and preserved provenance. **PlanFence, September 2026 preprint**, validates the dependencies of a pending action and invalidates plans derived from superseded requirements. These substantially weaken a proposed novelty claim based merely on importing database ideas into agent memory. Neither establishes that this LoRA objective learns the required behavior. [TOKI](https://arxiv.org/abs/2606.06240), [PlanFence](https://arxiv.org/abs/2609.03340)
- **CodeSync, ICML 2025**, studies adaptation to evolving library APIs and evaluates preference-based updating methods. “Code knowledge changes over time” is likewise an existing workload, with documented difficulties. [Paper](https://proceedings.mlr.press/v267/wang25t.html)

These papers do **not** prove that useful progress is impossible. They do refute broad novelty claims such as “teach models to update selectively,” “preserve unaffected predictions,” or “use versioned memory to prevent stale actions.”

The present screen operationalises **parts** of conditional revision, but permits shortcuts that defeat the intended stronger interpretation:

1. **Scope is not adequately distinguished from a global change for future work.** The scoped request asks for an operation inside the exception. Preservation checks protect existing behavior, but the screen does not subsequently require a *fresh operation outside the exception*. A policy that applies the latest convention to every new operation while copying existing code can therefore pass the relevant structure of both replacement and scope cases. The training scope renderer and request construction exhibit this distinction directly. [/home/bmarti44/stencil-llm/src/stencil/a_train_pool.py:805](/home/bmarti44/stencil-llm/src/stencil/a_train_pool.py:805), [/home/bmarti44/stencil-llm/src/stencil/a_train_pool.py:985](/home/bmarti44/stencil-llm/src/stencil/a_train_pool.py:985)

2. **Reinstatement does not require recovering an earlier rule.** I inspected all 12 screen reinstatement events: each restates the desired convention. For example, S12 explicitly says that new methods are `verb_noun`. Following that latest instruction succeeds without retrieving what the original convention was. The training renderer also repeats the restored rule. [/home/bmarti44/stencil-llm/src/stencil/a_screen_pool/s12.py:677](/home/bmarti44/stencil-llm/src/stencil/a_screen_pool/s12.py:677), [/home/bmarti44/stencil-llm/src/stencil/a_train_pool.py:814](/home/bmarti44/stencil-llm/src/stencil/a_train_pool.py:814)

3. **Preserving old code is not sufficient evidence of retaining an applicable rule.** Protected execution is valuable, but existing implementations are visible in the prompt. Copying them can preserve behavior without learning the rule needed for a new operation. The current protected suites deliberately exercise request 1’s earlier convention. [/home/bmarti44/stencil-llm/src/stencil/a_screen.py:368](/home/bmarti44/stencil-llm/src/stencil/a_screen.py:368)

The necessary change is a **matched behavioral contrast**, not another taxonomy:

- Hold the project, entering repository, requested operation and packing fixed.
- Vary whether the same revision applies to that operation.
- Require fresh behavior inside and outside the scope.
- Include restoration by reference to the earlier rule, without restating its value.
- Score the requested change and preservation jointly; report their individual failures too.
- Treat variants of one underlying problem as a cluster, not independent extra observations.

Keep the existing screen intact as exploratory evidence. A different intervention or estimand belongs in a new registration.

**3. The corrected population key is right for the present target operations, but its interpretation still needs scope — medium.**

All four population tests passed over 624 sessions, and I separately checked the actual `alt_was_in_force()` outputs against the intended metadata relationships for both requests. I found no additional table cell that should be reassigned on that basis. The prior request-1 mislabelling is **resolved**. [/home/bmarti44/stencil-llm/results/a-screen/analysis/stale2.py:83](/home/bmarti44/stencil-llm/results/a-screen/analysis/stale2.py:83)

There is, however, a third **semantic** case:

> The alternative is no longer applicable to this new operation but remains applicable elsewhere, or remains the required behavior of grandfathered operations.

Scope exceptions and prospective replacements deliberately create that case. Calling the alternative “cancelled” without qualification obscures the very selectivity the proposed direction should study. The label should mean **superseded for the scored operation**, not erased from the session’s valid rules.

The tests also do less than the prose implies. They check relationships among `lifecycle`, `rule_turns`, `states` and `state_at`; they neither call `alt_was_in_force()` nor independently interpret the instruction text. A mutation to that function could leave all four tests green. This is a test-coverage limitation, not evidence that the current function returns the wrong labels. [/home/bmarti44/stencil-llm/tests/test_a_screen_supersession.py:20](/home/bmarti44/stencil-llm/tests/test_a_screen_supersession.py:20)

**4. The overlap and first-pass arguments overclaim — high.**

The completion of training is real: **134 optimizer steps, 1,078 microsteps, six discarded microsteps, zero completed epochs, `final=true`, `status=complete`**. The actual preflight accepts this checkpoint with 134 required steps. The prior unfinished-checkpoint finding is **resolved**. [/home/bmarti44/stencil-llm/results/a-screen/adapters/cf/train-log.json:24](/home/bmarti44/stencil-llm/results/a-screen/adapters/cf/train-log.json:24)

But first-pass optimization does not establish fresh-task generalization:

- There are **1,152 positive examples but 1,007 distinct chosen completion strings**.
- Reconstructing the trainer’s seed-0 ordering, **121 of the 1,072 microsteps contributing to completed updates repeat a chosen completion already encountered**.
- The full unpacked input/preference triples are distinct. Therefore, “new example” can be true as an index or prompt-triple statement while misleading as a claim about unseen solutions.
- Closely related examples additionally share operations, constructions and code already present in the input.

The trainer’s iteration and example ordering support that reconstruction. [/home/bmarti44/stencil-llm/scripts/a_screen_train.py:67](/home/bmarti44/stencil-llm/scripts/a_screen_train.py:67), [/home/bmarti44/stencil-llm/scripts/a_screen_train.py:324](/home/bmarti44/stencil-llm/scripts/a_screen_train.py:324)

The similarity analysis has three concrete limitations:

**First, the difflib value is not the maximum over all training golds.** It is the maximum over only the eight candidates selected by identifier-set Jaccard. The printed “ANY training gold” description is inaccurate. [/home/bmarti44/stencil-llm/results/a-screen/analysis/overlap.py:71](/home/bmarti44/stencil-llm/results/a-screen/analysis/overlap.py:71)

**Second, the stated interpretation of the metrics is wrong.** Identifier-set Jaccard does not robustly catch “same code, renamed”: renaming changes the tokens. Sets also discard order and multiplicity. Character-level `SequenceMatcher` uses automatic popularity filtering by default, which can suppress common characters in long source files.

I recomputed the same top-eight candidate comparisons with that filtering disabled:

| Calculation | Maximum similarity |
|---|---:|
| Existing default `SequenceMatcher` | 0.2543 |
| Same candidate sets, `autojunk=False` | **0.5168** |

For S35 request 1 under `none`, the maximum changed from **0.0835 to 0.5085**. This does not establish memorisation; it establishes that the reassuring magnitude depends heavily on the measurement choice. [/home/bmarti44/stencil-llm/results/a-screen/analysis/overlap.py:17](/home/bmarti44/stencil-llm/results/a-screen/analysis/overlap.py:17)

**Third, gold-to-gold overlap does not measure what the adapter recalls when generating.** It misses reused fragments, copied input code, renamed routines and learned construction templates.

I independently found **zero exact whole-file matches among the 192 screen golds against the enumerated training golds**. That licenses this statement:

> No screen gold is an exact duplicate of an enumerated training gold.

It does not license “nothing resembles anything” or “a positive result cannot be verbatim recall” as a general explanation of model behavior. Those sentences should be replaced. [/home/bmarti44/stencil-llm/results/a-screen/RESULTS-BASELINE.md:121](/home/bmarti44/stencil-llm/results/a-screen/RESULTS-BASELINE.md:121)

A better inexpensive audit measures the **new operation and its change from the entering repository**, alongside identifier-normalized structure and longest copied fragments. Even that remains descriptive. Holding out construction families and testing counterfactual behavior provides stronger evidence than choosing another similarity threshold.

Finally, a large reference-relative DPO margin does not isolate learning caused by DPO: increasing chosen likelihood through CE can increase it. Nor does the average margin show that every pair is solved. The log demonstrates optimization progress, not free-generation transfer or the incremental value of the preference term. [/home/bmarti44/stencil-llm/scripts/a_screen_train.py:353](/home/bmarti44/stencil-llm/scripts/a_screen_train.py:353)

**5. The guards still admit “verified” comparisons without the necessary evidence — high.**

I mutated copies of the real baseline in memory and called the actual `compare.validate()` function. The clean fixture passed. Each of these invalid cases also returned **no problems**:

| Mutation | Missing protection |
|---|---|
| Remove S02 from both arms and both declared session lists | Agreement with the frozen manifest |
| Remove `hub_sha256` from both arms | Required-field presence |
| Corrupt every `repo_after` hash | Verification of resulting repositories |
| Remove all suite scores | Required outcome schema |
| Set `pilot_adapter=true` | Exclusion of timing-only adapters |
| Compare a 120-step SFT arm against CF with `adapter_steps` absent | Mandatory step identity for trained arms |
| Use an arbitrary runner hash with any nonempty exception string | Binding to the reviewed runner pair |

The implementation checks completeness against each file’s own declaration, compares the union of supplied identity keys, verifies only `repo_before`, and selects “trained” arms through truthiness of `adapter_steps`. These are precisely the routes by which the checks do not run. [/home/bmarti44/stencil-llm/results/a-screen/analysis/compare.py:129](/home/bmarti44/stencil-llm/results/a-screen/analysis/compare.py:129), [/home/bmarti44/stencil-llm/results/a-screen/analysis/compare.py:150](/home/bmarti44/stencil-llm/results/a-screen/analysis/compare.py:150), [/home/bmarti44/stencil-llm/results/a-screen/analysis/compare.py:203](/home/bmarti44/stencil-llm/results/a-screen/analysis/compare.py:203)

Missing scores subsequently become false outcomes through `.get()` and `bool()`. I exercised that scoring path with contract classification held fixed: all 36 changed-session preservation outcomes silently became failures. Conversely, the stored `function_only` aggregate is trusted rather than recomputed from its component suites. [/home/bmarti44/stencil-llm/results/a-screen/analysis/compare.py:167](/home/bmarti44/stencil-llm/results/a-screen/analysis/compare.py:167)

Several stronger checks already exist in the registered summary consumer. Reuse them. The appropriate remedy is one trustworthy comparison path, not another independent validation framework. [/home/bmarti44/stencil-llm/scripts/a_screen_summary.py:37](/home/bmarti44/stencil-llm/scripts/a_screen_summary.py:37)

There are three additional, narrower findings:

- **Preflight’s original three defects are resolved; its universal claim is not — medium.** It now binds the intended objective, requires the previously missing hashes and validates individual adapters before comparison. But mutations setting `examples=-1`, omitting `identity.limit`, setting elapsed seconds above budget, or deleting exposure accounting all passed. It also checks weight-file existence, not loadability. These do not invalidate the real checkpoint I inspected; they limit what “eligible” and “every check ran” establish. [/home/bmarti44/stencil-llm/results/a-screen/analysis/preflight.py:91](/home/bmarti44/stencil-llm/results/a-screen/analysis/preflight.py:91)

- **The exact runner exception is established; its verifier is unsafe as a general future certificate — medium.** I reproduced the recorded hashes and AST agreement. However, `Strip.visit_If()` deletes the `else` branch as well as the adapter-only body. Adding an `else` that raises during an adapterless run still produces the same stripped AST. Preserve or reject `else` branches and bind the permitted exception to the inspected hashes. **This does not justify rerunning the existing baseline.** [/home/bmarti44/stencil-llm/results/a-screen/analysis/runner_equivalence.py:68](/home/bmarti44/stencil-llm/results/a-screen/analysis/runner_equivalence.py:68)

- **The new instrument self-check fixes the demonstrated globally dead interpreter, not every dead suite — medium.** Its default real-session sample is S01–S03, all naming sessions. It checks positive gold but does not establish cross-state rejection or functioning validation/missing-record suites. I found no empty screen contract dictionaries, which is reassuring. Nevertheless, a family-specific execution failure can still be classified as “neither.” Keep instrument failure distinguishable from model failure. [/home/bmarti44/stencil-llm/results/a-screen/analysis/stale2.py:145](/home/bmarti44/stencil-llm/results/a-screen/analysis/stale2.py:145)

The old `stale2.scan()` completeness and replay-refusal finding also remains **open, medium**: duplicates overwrite, denominators follow supplied records, and mismatches produce warnings. The real baseline’s before/after hashes passed my independent audit. [/home/bmarti44/stencil-llm/results/a-screen/analysis/stale2.py:199](/home/bmarti44/stencil-llm/results/a-screen/analysis/stale2.py:199)

**6. `RESULTS-BASELINE.md` is candid about selection, but not consistently restrained in its conclusions — high for causal claims; medium for reporting.**

The explicit endpoint-selection disclosure, project/prefix confounds and long-horizon limitation are improvements. The request-specific Fisher calculations reproduce:

- Request 1: **p = 0.00254394**.
- Request 2: **p = 0.13884373**.

Those are exploratory associations across different constructions. They do not isolate a supersession mechanism. [/home/bmarti44/stencil-llm/results/a-screen/RESULTS-BASELINE.md:101](/home/bmarti44/stencil-llm/results/a-screen/RESULTS-BASELINE.md:101)

The remaining overclaims are concrete:

- **“Only where” is contradicted by the unchanged-cell alternative reply.** Calling that an “arguable exception” does not remove it. State the observed rates without an exclusivity claim. Also, literally saying “obeying a convention” omits the essential word *alternative*. [/home/bmarti44/stencil-llm/results/a-screen/RESULTS-BASELINE.md:52](/home/bmarti44/stencil-llm/results/a-screen/RESULTS-BASELINE.md:52)

- **The pooled Fisher p-value lacks its sampling justification.** Acknowledging dependent observations does not make an independence-based p-value valid. Retain pooled counts descriptively; omit that inferential p-value or use an explicitly justified session-level analysis. [/home/bmarti44/stencil-llm/results/a-screen/RESULTS-BASELINE.md:49](/home/bmarti44/stencil-llm/results/a-screen/RESULTS-BASELINE.md:49)

- **“Validation is a competence problem, not a focus problem” is unsupported.** “Neither” means neither contract suite passed. It does not identify why. Missing components, bad routing, incomplete implementation and instruction failures can coexist. A matched current-rule-only condition is needed to isolate a competence ceiling. [/home/bmarti44/stencil-llm/results/a-screen/RESULTS-BASELINE.md:85](/home/bmarti44/stencil-llm/results/a-screen/RESULTS-BASELINE.md:85)

- **“Working code” needs the exact suite qualification.** Among the changed-request replies, the stored records show six current-rule replies passing the new functional suite, but only **three** passing `function_only`, which also requires regression and protected-function success. Eight stale replies pass the functional suite; seven pass `function_only`. Report those distinctions rather than equating the narrow suite with user acceptance. [/home/bmarti44/stencil-llm/results/a-screen/RESULTS-BASELINE.md:57](/home/bmarti44/stencil-llm/results/a-screen/RESULTS-BASELINE.md:57), [/home/bmarti44/stencil-llm/src/stencil/a_screen.py:409](/home/bmarti44/stencil-llm/src/stencil/a_screen.py:409)

- **The document presents inferential p-values without accompanying intervals.** Its reproduction script prints some intervals, but the document should carry the uncertainty wherever it carries the comparison.

The summary counts themselves check out: **J = 6/48 sessions; function-only = 15/48 sessions or 39/96 replies**. Those are different units, not inconsistent numbers.

**7. I would not spend the remaining GPU-hour as the next experiment — high.**

The registered interval calculation is correct. At \(n=36\):

| Wins | Losses | Registered interval |
|---:|---:|---:|
| 0 | 0 | −11.46 to +11.46 points |
| 5 | 0 | −7.55 to +31.78 points |
| 10 | 0 | +1.31 to +47.55 points |
| 12 | 1 | +0.46 to +53.27 points |
| 14 | 2 | +0.60 to +58.35 points |

The separate preservation population is worse: **zero discordances at \(n=12\) still gives approximately ±30.6 points**. Thus “no observed decline” cannot demonstrate preservation within a modest harm margin. [/home/bmarti44/stencil-llm/results/a-screen/analysis/compare.py:88](/home/bmarti44/stencil-llm/results/a-screen/analysis/compare.py:88)

To quantify the limitation, I enumerated an illustrative independent-session multinomial model. These are assumptions, not fitted forecasts:

| True win / loss probabilities | True net benefit | Probability the registered \(n=36\) interval is wholly positive |
|---|---:|---:|
| 0.15 / 0.05 | 10 points | **0.93%** |
| 0.25 / 0.05 | 20 points | **14.51%** |
| 0.35 / 0.05 | 30 points | **46.82%** |

This is more severe than “cannot resolve a modest effect.” It has a low probability of formally establishing even some large effects under the registered interval.

That does **not** make a one-hour run intrinsically worthless. A development screen can buy a useful decision without achieving significance. If the decision were simply whether to spend another approximately 2.5 hours on matched SFT, a large CF improvement could be actionable. But for Brian’s actual goal:

- A positive `cf − off` result does not attribute anything to the counterfactual term.
- A negative result does not show that SFT would fail.
- Neither result resolves the scope/restoration shortcuts.
- Even a large positive result cannot rescue an already occupied broad novelty claim.

The ledger’s implication that failure of CF implies failure of SFT remains false. The preference term could hurt an otherwise useful supervised adapter. [/home/bmarti44/stencil-llm/plan/LEDGER.md:3979](/home/bmarti44/stencil-llm/plan/LEDGER.md:3979)

My recommended cheaper sequence is:

1. **CPU only: establish that the proposed diagnostic defeats the trivial policies.** Construct a small matched set with a deterministic applicability oracle. Check policies that always use the newest value, always keep the old value, flip on cancellation language, and copy the existing implementation. Include a scope exception followed by a fresh out-of-scope task, and restoration without restating the old value. This tests the instrument’s distinguishing power, not the model.

2. **First model measurement: score paired alternatives with the existing CF adapter and the trunk.** For each matched history, compare the same two small executable alternatives. Require the preference to reverse when applicability reverses, while staying unchanged outside scope. This avoids repeatedly generating complete files and directly attacks the claimed context sensitivity. It remains a teacher-forced diagnostic, not a substitute for generation success or matched SFT.

3. **Only after evidence of selective behavior, buy the free-generation comparison and SFT attribution.** Keep the existing checkpoint frozen. Do not select a better-looking checkpoint or tune the diagnostic on model outcomes.

There is a concrete timing reason to investigate step 2: the existing training run scored **1,152 chosen/rejected pairs in 1,855 seconds**. A much smaller forward-scoring diagnostic could be materially cheaper than 96 autoregressive whole-file replies, although loading and workload differences require a measured budget. [/home/bmarti44/stencil-llm/results/a-screen/adapters/cf/train-log.json:22](/home/bmarti44/stencil-llm/results/a-screen/adapters/cf/train-log.json:22)

I would **not start by training a smaller trunk**. The existing 4B adapter already contains the intervention of interest. A smaller model can help test a simple rule-state representation, but its failure may be a capacity failure and its success would not establish the 4B artifact’s behavior.

**8. The most useful outside-field lessons change the experiment, not just its vocabulary.**

**Cognitive psychology: separate remembering a correction from using it.** Wahlheim and Jacoby found that detecting and recollecting change can reverse interference into facilitation. A 2025 experiment by Guo, Chen and Hu found that supplying an alternative explanation reduced continued influence more than retraction alone. These motivate separate tests of rule identification and rule execution, and separate conditions for cancellation versus explicit replacement. They do not establish that a transformer has the same mechanism. [Wahlheim and Jacoby](https://pubmed.ncbi.nlm.nih.gov/22918874/), [Guo et al.](https://www.sciencedirect.com/science/article/pii/S0278262625000302)

**Experimental economics supplies a particularly strong control.** Gonçalves, Libgober and Willis compare retracted information with both never-presented information and informationally equivalent direct information. Their experiments find weaker updating from retractions. For Stencil, compare three histories with the same final applicable rule: directly stated current rule, obsolete rule followed by cancellation/replacement, and irrelevant-history control. Hold the task and repository constant. This separates history-related difficulty from final-task competence. [Retractions: Updating from Complex Information, published online 2025; 2026 journal issue](https://discovery.ucl.ac.uk/id/eprint/10205481/)

**Formal belief revision: a flat current-value register loses essential history and dependencies.** Doyle’s truth-maintenance system records reasons for beliefs so changes can propagate through their dependents. Darwiche and Pearl show why ordinary AGM postulates are insufficient to constrain iterated revision of conditional beliefs. The relevant lesson is to track applicability and justification, not simply suppress an old string. Cancellation of a premise can invalidate several consequences; a conclusion supported independently may remain valid. [Doyle, 1979](https://www.sciencedirect.com/science/article/pii/0004370279900080), [Darwiche and Pearl, 1997](https://ftp.cs.ucla.edu/pub/stat_ser/R202.pdf)

**Database systems: fresh memory does not guarantee a valid pending action.** Optimistic concurrency control validates a transaction’s read set before committing. PlanFence applies related ideas to plans whose dependencies may have changed before execution. A useful additional workload is therefore an interrupted coding task: plan under rule A, receive revision B, then execute. Measure whether the pending implementation is revised, not merely whether B can be quoted. PlanFence’s own guarantees depend on declared dependencies and other explicit assumptions; this is a workload lesson, not an off-the-shelf proof of agent correctness. [Kung and Robinson, 1981](https://www.eecs.harvard.edu/~htk/publication/1981-tods-kung-robinson.pdf), [PlanFence limitations](https://arxiv.org/html/2609.03340v1)

**Version control: undo is a new operation, not deletion of history.** Git revert records a reversal while preserving ancestry; reverting a merge also affects what later merges will bring back. For Stencil, test an A→B→A sequence with an unrelated intervening change C that must survive. A whole-state rollback should fail. [Git documentation](https://git-scm.com/docs/git-revert)

**Legal interpretation: cancellation, reinstatement and prospective effect are distinct operations.** UK drafting guidance explicitly notes that repealing a repeal does not automatically revive the original enactment. It also distinguishes partial amendments and their continuing effects. This defeats a universal binary “cancel B, therefore A” heuristic. Define the intended semantics explicitly and test cancellation without replacement separately from express reinstatement. This is an analogy for specification, not a proposed universal rule of legal interpretation. [Office of the Parliamentary Counsel, sections 6.1.6–6.1.13](https://www.gov.uk/government/publications/drafting-bills-for-parliament/2024-03-19-drafting-guidance)

**Program verification: preservation requires a defined footprint.** Separation logic’s frame rule makes local change compatible with preservation of disjoint state under stated conditions. Stencil’s behavioral analogue should name what may change, what must remain unchanged, and which dependencies connect them. Fresh unaffected operations are essential because copying old code is an inadequate test of that property. [Reynolds, 2002](https://www.cs.cmu.edu/~jcr/seplogic.pdf)

These observations suggest useful workloads beyond convention naming: versioned API migrations with compatibility obligations, tenant-specific configuration exceptions, feature-flag rollback with unrelated fixes preserved, and interrupted plans whose requirements change before execution. Pick one with a deterministic oracle and short executable outputs. Do not expand into all of them.

**9. Prior findings retain their original severities and receive these dispositions.**

| Prior finding | Disposition |
|---|---|
| **§1, high:** request-1 supersession mislabelling | **Resolved** for the current target operations; scope qualification and consumer-test coverage are discussed above. |
| **§2, high:** insufficient evidence for the full artifact direction | **Open.** Training completion resolves the unfinished-checkpoint subfinding, not transfer or usefulness. |
| **§3, high:** established-method permutation | **Open, strengthened** by IOPO’s explicit DPO\*/SFT\* construction and broader selective-revision prior art. |
| **§4, medium:** unnecessary baseline rerun | **Resolved:** the exact old/new runner pair is equivalent on the inspected adapterless path. |
| **§4, high:** invalid stopping rationale and count threshold treated as proof | **Open.** CF failure still does not imply SFT failure; the interval calculation reinforces the distinction between screening and proof. |
| **§6, high:** comparison population, identity and replay acceptance | **Partially repaired; still open**, with reproduced shared-subset, missing-field and replay escapes. |
| **§6, high:** causal difference-of-differences interpretation | **Resolved in `compare.py`** by descriptive wording. |
| **§6, high:** narrow functional score overstated usefulness | **Partially repaired; still open.** More outcomes are printed, but the acceptance wording and registered session-level reporting remain inadequate. |
| **§6, medium:** `stale2.py` completeness and replay enforcement | **Open.** |
| **§6, medium:** original preflight objective/hub/missing-field defects | **Resolved for those demonstrated cases.** Additional limitations are separately graded above. |
| **§6, low:** scratchpad import override | **Resolved.** |
| **§6, low:** `look.py` is descriptive, not a comparison authority | **Retained.** No new authority is established by this review. |
| `names.py` isolated-retention interpretation | **Resolved by retirement.** The revised tool uses the actual entering repository and limits itself to naming. [/home/bmarti44/stencil-llm/results/a-screen/analysis/names.py:1](/home/bmarti44/stencil-llm/results/a-screen/analysis/names.py:1) |
| `health.py` signals are not transfer evidence | **Retained.** |
| **§7, high:** long-horizon, architectural-transfer, selected-endpoint and common-scoring-defect limitations | **Remain applicable.** The baseline document now acknowledges them; acknowledgment does not supply the missing evidence. The ledger still contains the refuted common-scoring-defect argument. [/home/bmarti44/stencil-llm/plan/LEDGER.md:3961](/home/bmarti44/stencil-llm/plan/LEDGER.md:3961) |

**10. Forecast and investment decision.**

I define artifact success as a published, reproducible artifact with a practically meaningful, statistically supported improvement over its disabled counterpart, evidence supporting the claimed recombination beyond matched SFT, and transfer beyond the generator’s shortcuts. I am not requiring acceptance at a particular conference.

My fresh forecast is **15%**. A transparent approximate decomposition is:

- 55% chance of useful CF improvement over the trunk;
- 45% conditional chance that the matched-SFT comparison supports a substantive incremental contribution;
- 65% conditional chance that the result survives a distinguishing scope/restoration test and broader construction transfer;
- 90% conditional chance of successful reproducible packaging.

Their product is approximately 14.5%, rounded to 15%. These are subjective conditional judgments, not measured probabilities or independent empirical estimates.

Completed training and corrected measurement improve operational readiness. Context-DPO and related results support plausibility. Against that stand direct prior art, unresolved attribution, a screen that admits simple behavioral shortcuts, and weak precision—especially for preservation.

I cannot disprove the usefulness of selective rule revision as a general research problem. **I can reject the present claim that Candidate A is already a defensible substantive recombination with at least a 25% chance of satisfying the full artifact goal.** Further guard repair alone will not change that assessment.

VERDICT — OFF TRACK — 15% artifact-success forecast, below 25%; establish a matched scope-and-restoration test that defeats recency and copying before further GPU spend.
tokens used
238,960
**OFF TRACK. Candidate A does not currently establish a substantive recombination, and renaming its target “conditional revision” does not repair that. My artifact-success forecast is 15%, below your 25% bar.** The underlying problem remains useful; the present evidence and experiment do not adequately distinguish its proposed solution from ordinary instruction tuning and simple recency or copying strategies.

This session permits filesystem reads only, so I could not save the review file. I read the prior review and governing process, read nothing under `data/bench/`, used no GPU, and changed no files. I independently checked all 96 baseline replay chains against both recorded repository hashes, executed the four population tests directly, exercised additional guard mutations in memory, checked the actual completed adapter’s preflight, and recomputed the reported statistical thresholds. I did not rerun the complete subprocess-based contract evaluation or the full pytest suites.

**1. Candidate A: no substantive methodological novelty established — high.**

The loss is ordinary completion-token cross-entropy plus a weighted DPO term. Its distinguishing choice is the construction of preference pairs. The implementation agrees with that description. [/home/bmarti44/stencil-llm/scripts/a_screen_train.py:353](/home/bmarti44/stencil-llm/scripts/a_screen_train.py:353)

The strongest challenges are:

| Prior work | What it already establishes | What remains distinguishable here |
|---|---|---|
| **Counterfactual DPO**, Butcher, 2024 | Counterfactual prompting supplies preference pairs for behavioral alignment. | Stencil’s executable, temporal coding setting. [Paper](https://arxiv.org/abs/2401.09566) |
| **Context-DPO**, Bi et al., Findings of ACL 2025 | Preferences favor context-faithful answers over stubborn alternatives, with an SFT comparison. | Superseded conversational rules, rather than principally conflicts with parametric factual knowledge. [Paper](https://aclanthology.org/2025.findings-acl.536/) |
| **IOPO**, 2024 preprint | Closely related instructions receive different preferred outputs. Particularly damaging: its **DPO\*** comparison explicitly trains both crossed preference directions, while **SFT\*** receives both matching positives. | Temporal executable constraints and preservation requirements; not the crossed-pair construction itself. [Section 6.2](https://arxiv.org/html/2411.06208v1) |
| **CRPL**, August 2026 preprint | Preference construction models relationships between permissible response spaces and verifies atomic constraints. | A demonstrated temporal, stateful coding advantage beyond those general ideas. [Paper](https://arxiv.org/abs/2608.29352) |
| **Mitigating Conversational Inertia**, February 2026 preprint | LoRA/DPO learns preferences intended to escape harmful dependence on preceding agent behavior. | Explicit rule applicability and selective preservation. Its preferences come from different context lengths, so it is adjacent rather than identical. [Section 2.1](https://arxiv.org/html/2602.03664v1) |

IOPO’s DPO\*/SFT\* construction is a stronger objection than merely observing that “DPO exists.” It anticipates an important part of Stencil’s proposed recombination: the same response can be preferred under one input and rejected under another, with both positive directions supplied to SFT.

There is also a naming correction. **Only 576 of the 1,152 constructed training pairs reject a state that was previously in force in that history.** The rest reject another convention that was not previously applicable as the new-operation rule. That is appropriate for learning when to preserve behavior, but “every rejected response follows a superseded convention” is false. The relevant construction includes stable and irrelevant-event pairs. [/home/bmarti44/stencil-llm/src/stencil/a_screen.py:463](/home/bmarti44/stencil-llm/src/stencil/a_screen.py:463)

What could remain substantive is an empirical result:

> A small adapter learns to apply revisions selectively to executable behavior, including fresh out-of-scope behavior and restoration, with a useful advantage over matched SFT and transfer beyond the training generator.

That would be a contribution through demonstrated capability, data construction and evaluation. It would not make this loss a new method. **Today, that result is absent.** Adding lifecycle names to established preference learning is insufficient.

**2. Conditional revision is a better specification, but is already prior art — high.**

My earlier suggestion needs this qualification: it identified a promising *claim to test*, not an unoccupied research area.

Several strands already cover substantial parts of it:

- **Belief-R, EMNLP 2024**, explicitly tests whether models should revise a conclusion or retain it. Its reported trade-off—models that update well can perform worse when updating is unnecessary—is directly relevant to “switch when applicable, preserve otherwise.” It evaluates inference, not stateful code editing. [Paper](https://aclanthology.org/2024.emnlp-main.586/)
- **SERAC, ICML 2022**, uses an edit-scope classifier and a counterfactual model, returning the base model’s prediction outside edit scope. Broad “scoped modification without unrelated disruption” claims were already occupied before 2024. [Paper](https://proceedings.mlr.press/v162/mitchell22a/mitchell22a.pdf)
- **EvolIF, November 2025 preprint**, maintains separate topic instruction states, adds/deletes/modifies their constraints, and returns to earlier topics. It therefore anticipates a considerable portion of the behavioral taxonomy. Its independently managed topics do not establish arbitrary overlapping coding scopes or preservation of executable artifacts. [Sections 3.2.1–3.2.3](https://arxiv.org/html/2511.03508v1)
- **TOKI, June 2026 preprint**, treats contradictory agent-memory writes through temporal versions, explicit resolution policies and preserved provenance. **PlanFence, September 2026 preprint**, validates the dependencies of a pending action and invalidates plans derived from superseded requirements. These substantially weaken a proposed novelty claim based merely on importing database ideas into agent memory. Neither establishes that this LoRA objective learns the required behavior. [TOKI](https://arxiv.org/abs/2606.06240), [PlanFence](https://arxiv.org/abs/2609.03340)
- **CodeSync, ICML 2025**, studies adaptation to evolving library APIs and evaluates preference-based updating methods. “Code knowledge changes over time” is likewise an existing workload, with documented difficulties. [Paper](https://proceedings.mlr.press/v267/wang25t.html)

These papers do **not** prove that useful progress is impossible. They do refute broad novelty claims such as “teach models to update selectively,” “preserve unaffected predictions,” or “use versioned memory to prevent stale actions.”

The present screen operationalises **parts** of conditional revision, but permits shortcuts that defeat the intended stronger interpretation:

1. **Scope is not adequately distinguished from a global change for future work.** The scoped request asks for an operation inside the exception. Preservation checks protect existing behavior, but the screen does not subsequently require a *fresh operation outside the exception*. A policy that applies the latest convention to every new operation while copying existing code can therefore pass the relevant structure of both replacement and scope cases. The training scope renderer and request construction exhibit this distinction directly. [/home/bmarti44/stencil-llm/src/stencil/a_train_pool.py:805](/home/bmarti44/stencil-llm/src/stencil/a_train_pool.py:805), [/home/bmarti44/stencil-llm/src/stencil/a_train_pool.py:985](/home/bmarti44/stencil-llm/src/stencil/a_train_pool.py:985)

2. **Reinstatement does not require recovering an earlier rule.** I inspected all 12 screen reinstatement events: each restates the desired convention. For example, S12 explicitly says that new methods are `verb_noun`. Following that latest instruction succeeds without retrieving what the original convention was. The training renderer also repeats the restored rule. [/home/bmarti44/stencil-llm/src/stencil/a_screen_pool/s12.py:677](/home/bmarti44/stencil-llm/src/stencil/a_screen_pool/s12.py:677), [/home/bmarti44/stencil-llm/src/stencil/a_train_pool.py:814](/home/bmarti44/stencil-llm/src/stencil/a_train_pool.py:814)

3. **Preserving old code is not sufficient evidence of retaining an applicable rule.** Protected execution is valuable, but existing implementations are visible in the prompt. Copying them can preserve behavior without learning the rule needed for a new operation. The current protected suites deliberately exercise request 1’s earlier convention. [/home/bmarti44/stencil-llm/src/stencil/a_screen.py:368](/home/bmarti44/stencil-llm/src/stencil/a_screen.py:368)

The necessary change is a **matched behavioral contrast**, not another taxonomy:

- Hold the project, entering repository, requested operation and packing fixed.
- Vary whether the same revision applies to that operation.
- Require fresh behavior inside and outside the scope.
- Include restoration by reference to the earlier rule, without restating its value.
- Score the requested change and preservation jointly; report their individual failures too.
- Treat variants of one underlying problem as a cluster, not independent extra observations.

Keep the existing screen intact as exploratory evidence. A different intervention or estimand belongs in a new registration.

**3. The corrected population key is right for the present target operations, but its interpretation still needs scope — medium.**

All four population tests passed over 624 sessions, and I separately checked the actual `alt_was_in_force()` outputs against the intended metadata relationships for both requests. I found no additional table cell that should be reassigned on that basis. The prior request-1 mislabelling is **resolved**. [/home/bmarti44/stencil-llm/results/a-screen/analysis/stale2.py:83](/home/bmarti44/stencil-llm/results/a-screen/analysis/stale2.py:83)

There is, however, a third **semantic** case:

> The alternative is no longer applicable to this new operation but remains applicable elsewhere, or remains the required behavior of grandfathered operations.

Scope exceptions and prospective replacements deliberately create that case. Calling the alternative “cancelled” without qualification obscures the very selectivity the proposed direction should study. The label should mean **superseded for the scored operation**, not erased from the session’s valid rules.

The tests also do less than the prose implies. They check relationships among `lifecycle`, `rule_turns`, `states` and `state_at`; they neither call `alt_was_in_force()` nor independently interpret the instruction text. A mutation to that function could leave all four tests green. This is a test-coverage limitation, not evidence that the current function returns the wrong labels. [/home/bmarti44/stencil-llm/tests/test_a_screen_supersession.py:20](/home/bmarti44/stencil-llm/tests/test_a_screen_supersession.py:20)

**4. The overlap and first-pass arguments overclaim — high.**

The completion of training is real: **134 optimizer steps, 1,078 microsteps, six discarded microsteps, zero completed epochs, `final=true`, `status=complete`**. The actual preflight accepts this checkpoint with 134 required steps. The prior unfinished-checkpoint finding is **resolved**. [/home/bmarti44/stencil-llm/results/a-screen/adapters/cf/train-log.json:24](/home/bmarti44/stencil-llm/results/a-screen/adapters/cf/train-log.json:24)

But first-pass optimization does not establish fresh-task generalization:

- There are **1,152 positive examples but 1,007 distinct chosen completion strings**.
- Reconstructing the trainer’s seed-0 ordering, **121 of the 1,072 microsteps contributing to completed updates repeat a chosen completion already encountered**.
- The full unpacked input/preference triples are distinct. Therefore, “new example” can be true as an index or prompt-triple statement while misleading as a claim about unseen solutions.
- Closely related examples additionally share operations, constructions and code already present in the input.

The trainer’s iteration and example ordering support that reconstruction. [/home/bmarti44/stencil-llm/scripts/a_screen_train.py:67](/home/bmarti44/stencil-llm/scripts/a_screen_train.py:67), [/home/bmarti44/stencil-llm/scripts/a_screen_train.py:324](/home/bmarti44/stencil-llm/scripts/a_screen_train.py:324)

The similarity analysis has three concrete limitations:

**First, the difflib value is not the maximum over all training golds.** It is the maximum over only the eight candidates selected by identifier-set Jaccard. The printed “ANY training gold” description is inaccurate. [/home/bmarti44/stencil-llm/results/a-screen/analysis/overlap.py:71](/home/bmarti44/stencil-llm/results/a-screen/analysis/overlap.py:71)

**Second, the stated interpretation of the metrics is wrong.** Identifier-set Jaccard does not robustly catch “same code, renamed”: renaming changes the tokens. Sets also discard order and multiplicity. Character-level `SequenceMatcher` uses automatic popularity filtering by default, which can suppress common characters in long source files.

I recomputed the same top-eight candidate comparisons with that filtering disabled:

| Calculation | Maximum similarity |
|---|---:|
| Existing default `SequenceMatcher` | 0.2543 |
| Same candidate sets, `autojunk=False` | **0.5168** |

For S35 request 1 under `none`, the maximum changed from **0.0835 to 0.5085**. This does not establish memorisation; it establishes that the reassuring magnitude depends heavily on the measurement choice. [/home/bmarti44/stencil-llm/results/a-screen/analysis/overlap.py:17](/home/bmarti44/stencil-llm/results/a-screen/analysis/overlap.py:17)

**Third, gold-to-gold overlap does not measure what the adapter recalls when generating.** It misses reused fragments, copied input code, renamed routines and learned construction templates.

I independently found **zero exact whole-file matches among the 192 screen golds against the enumerated training golds**. That licenses this statement:

> No screen gold is an exact duplicate of an enumerated training gold.

It does not license “nothing resembles anything” or “a positive result cannot be verbatim recall” as a general explanation of model behavior. Those sentences should be replaced. [/home/bmarti44/stencil-llm/results/a-screen/RESULTS-BASELINE.md:121](/home/bmarti44/stencil-llm/results/a-screen/RESULTS-BASELINE.md:121)

A better inexpensive audit measures the **new operation and its change from the entering repository**, alongside identifier-normalized structure and longest copied fragments. Even that remains descriptive. Holding out construction families and testing counterfactual behavior provides stronger evidence than choosing another similarity threshold.

Finally, a large reference-relative DPO margin does not isolate learning caused by DPO: increasing chosen likelihood through CE can increase it. Nor does the average margin show that every pair is solved. The log demonstrates optimization progress, not free-generation transfer or the incremental value of the preference term. [/home/bmarti44/stencil-llm/scripts/a_screen_train.py:353](/home/bmarti44/stencil-llm/scripts/a_screen_train.py:353)

**5. The guards still admit “verified” comparisons without the necessary evidence — high.**

I mutated copies of the real baseline in memory and called the actual `compare.validate()` function. The clean fixture passed. Each of these invalid cases also returned **no problems**:

| Mutation | Missing protection |
|---|---|
| Remove S02 from both arms and both declared session lists | Agreement with the frozen manifest |
| Remove `hub_sha256` from both arms | Required-field presence |
| Corrupt every `repo_after` hash | Verification of resulting repositories |
| Remove all suite scores | Required outcome schema |
| Set `pilot_adapter=true` | Exclusion of timing-only adapters |
| Compare a 120-step SFT arm against CF with `adapter_steps` absent | Mandatory step identity for trained arms |
| Use an arbitrary runner hash with any nonempty exception string | Binding to the reviewed runner pair |

The implementation checks completeness against each file’s own declaration, compares the union of supplied identity keys, verifies only `repo_before`, and selects “trained” arms through truthiness of `adapter_steps`. These are precisely the routes by which the checks do not run. [/home/bmarti44/stencil-llm/results/a-screen/analysis/compare.py:129](/home/bmarti44/stencil-llm/results/a-screen/analysis/compare.py:129), [/home/bmarti44/stencil-llm/results/a-screen/analysis/compare.py:150](/home/bmarti44/stencil-llm/results/a-screen/analysis/compare.py:150), [/home/bmarti44/stencil-llm/results/a-screen/analysis/compare.py:203](/home/bmarti44/stencil-llm/results/a-screen/analysis/compare.py:203)

Missing scores subsequently become false outcomes through `.get()` and `bool()`. I exercised that scoring path with contract classification held fixed: all 36 changed-session preservation outcomes silently became failures. Conversely, the stored `function_only` aggregate is trusted rather than recomputed from its component suites. [/home/bmarti44/stencil-llm/results/a-screen/analysis/compare.py:167](/home/bmarti44/stencil-llm/results/a-screen/analysis/compare.py:167)

Several stronger checks already exist in the registered summary consumer. Reuse them. The appropriate remedy is one trustworthy comparison path, not another independent validation framework. [/home/bmarti44/stencil-llm/scripts/a_screen_summary.py:37](/home/bmarti44/stencil-llm/scripts/a_screen_summary.py:37)

There are three additional, narrower findings:

- **Preflight’s original three defects are resolved; its universal claim is not — medium.** It now binds the intended objective, requires the previously missing hashes and validates individual adapters before comparison. But mutations setting `examples=-1`, omitting `identity.limit`, setting elapsed seconds above budget, or deleting exposure accounting all passed. It also checks weight-file existence, not loadability. These do not invalidate the real checkpoint I inspected; they limit what “eligible” and “every check ran” establish. [/home/bmarti44/stencil-llm/results/a-screen/analysis/preflight.py:91](/home/bmarti44/stencil-llm/results/a-screen/analysis/preflight.py:91)

- **The exact runner exception is established; its verifier is unsafe as a general future certificate — medium.** I reproduced the recorded hashes and AST agreement. However, `Strip.visit_If()` deletes the `else` branch as well as the adapter-only body. Adding an `else` that raises during an adapterless run still produces the same stripped AST. Preserve or reject `else` branches and bind the permitted exception to the inspected hashes. **This does not justify rerunning the existing baseline.** [/home/bmarti44/stencil-llm/results/a-screen/analysis/runner_equivalence.py:68](/home/bmarti44/stencil-llm/results/a-screen/analysis/runner_equivalence.py:68)

- **The new instrument self-check fixes the demonstrated globally dead interpreter, not every dead suite — medium.** Its default real-session sample is S01–S03, all naming sessions. It checks positive gold but does not establish cross-state rejection or functioning validation/missing-record suites. I found no empty screen contract dictionaries, which is reassuring. Nevertheless, a family-specific execution failure can still be classified as “neither.” Keep instrument failure distinguishable from model failure. [/home/bmarti44/stencil-llm/results/a-screen/analysis/stale2.py:145](/home/bmarti44/stencil-llm/results/a-screen/analysis/stale2.py:145)

The old `stale2.scan()` completeness and replay-refusal finding also remains **open, medium**: duplicates overwrite, denominators follow supplied records, and mismatches produce warnings. The real baseline’s before/after hashes passed my independent audit. [/home/bmarti44/stencil-llm/results/a-screen/analysis/stale2.py:199](/home/bmarti44/stencil-llm/results/a-screen/analysis/stale2.py:199)

**6. `RESULTS-BASELINE.md` is candid about selection, but not consistently restrained in its conclusions — high for causal claims; medium for reporting.**

The explicit endpoint-selection disclosure, project/prefix confounds and long-horizon limitation are improvements. The request-specific Fisher calculations reproduce:

- Request 1: **p = 0.00254394**.
- Request 2: **p = 0.13884373**.

Those are exploratory associations across different constructions. They do not isolate a supersession mechanism. [/home/bmarti44/stencil-llm/results/a-screen/RESULTS-BASELINE.md:101](/home/bmarti44/stencil-llm/results/a-screen/RESULTS-BASELINE.md:101)

The remaining overclaims are concrete:

- **“Only where” is contradicted by the unchanged-cell alternative reply.** Calling that an “arguable exception” does not remove it. State the observed rates without an exclusivity claim. Also, literally saying “obeying a convention” omits the essential word *alternative*. [/home/bmarti44/stencil-llm/results/a-screen/RESULTS-BASELINE.md:52](/home/bmarti44/stencil-llm/results/a-screen/RESULTS-BASELINE.md:52)

- **The pooled Fisher p-value lacks its sampling justification.** Acknowledging dependent observations does not make an independence-based p-value valid. Retain pooled counts descriptively; omit that inferential p-value or use an explicitly justified session-level analysis. [/home/bmarti44/stencil-llm/results/a-screen/RESULTS-BASELINE.md:49](/home/bmarti44/stencil-llm/results/a-screen/RESULTS-BASELINE.md:49)

- **“Validation is a competence problem, not a focus problem” is unsupported.** “Neither” means neither contract suite passed. It does not identify why. Missing components, bad routing, incomplete implementation and instruction failures can coexist. A matched current-rule-only condition is needed to isolate a competence ceiling. [/home/bmarti44/stencil-llm/results/a-screen/RESULTS-BASELINE.md:85](/home/bmarti44/stencil-llm/results/a-screen/RESULTS-BASELINE.md:85)

- **“Working code” needs the exact suite qualification.** Among the changed-request replies, the stored records show six current-rule replies passing the new functional suite, but only **three** passing `function_only`, which also requires regression and protected-function success. Eight stale replies pass the functional suite; seven pass `function_only`. Report those distinctions rather than equating the narrow suite with user acceptance. [/home/bmarti44/stencil-llm/results/a-screen/RESULTS-BASELINE.md:57](/home/bmarti44/stencil-llm/results/a-screen/RESULTS-BASELINE.md:57), [/home/bmarti44/stencil-llm/src/stencil/a_screen.py:409](/home/bmarti44/stencil-llm/src/stencil/a_screen.py:409)

- **The document presents inferential p-values without accompanying intervals.** Its reproduction script prints some intervals, but the document should carry the uncertainty wherever it carries the comparison.

The summary counts themselves check out: **J = 6/48 sessions; function-only = 15/48 sessions or 39/96 replies**. Those are different units, not inconsistent numbers.

**7. I would not spend the remaining GPU-hour as the next experiment — high.**

The registered interval calculation is correct. At \(n=36\):

| Wins | Losses | Registered interval |
|---:|---:|---:|
| 0 | 0 | −11.46 to +11.46 points |
| 5 | 0 | −7.55 to +31.78 points |
| 10 | 0 | +1.31 to +47.55 points |
| 12 | 1 | +0.46 to +53.27 points |
| 14 | 2 | +0.60 to +58.35 points |

The separate preservation population is worse: **zero discordances at \(n=12\) still gives approximately ±30.6 points**. Thus “no observed decline” cannot demonstrate preservation within a modest harm margin. [/home/bmarti44/stencil-llm/results/a-screen/analysis/compare.py:88](/home/bmarti44/stencil-llm/results/a-screen/analysis/compare.py:88)

To quantify the limitation, I enumerated an illustrative independent-session multinomial model. These are assumptions, not fitted forecasts:

| True win / loss probabilities | True net benefit | Probability the registered \(n=36\) interval is wholly positive |
|---|---:|---:|
| 0.15 / 0.05 | 10 points | **0.93%** |
| 0.25 / 0.05 | 20 points | **14.51%** |
| 0.35 / 0.05 | 30 points | **46.82%** |

This is more severe than “cannot resolve a modest effect.” It has a low probability of formally establishing even some large effects under the registered interval.

That does **not** make a one-hour run intrinsically worthless. A development screen can buy a useful decision without achieving significance. If the decision were simply whether to spend another approximately 2.5 hours on matched SFT, a large CF improvement could be actionable. But for Brian’s actual goal:

- A positive `cf − off` result does not attribute anything to the counterfactual term.
- A negative result does not show that SFT would fail.
- Neither result resolves the scope/restoration shortcuts.
- Even a large positive result cannot rescue an already occupied broad novelty claim.

The ledger’s implication that failure of CF implies failure of SFT remains false. The preference term could hurt an otherwise useful supervised adapter. [/home/bmarti44/stencil-llm/plan/LEDGER.md:3979](/home/bmarti44/stencil-llm/plan/LEDGER.md:3979)

My recommended cheaper sequence is:

1. **CPU only: establish that the proposed diagnostic defeats the trivial policies.** Construct a small matched set with a deterministic applicability oracle. Check policies that always use the newest value, always keep the old value, flip on cancellation language, and copy the existing implementation. Include a scope exception followed by a fresh out-of-scope task, and restoration without restating the old value. This tests the instrument’s distinguishing power, not the model.

2. **First model measurement: score paired alternatives with the existing CF adapter and the trunk.** For each matched history, compare the same two small executable alternatives. Require the preference to reverse when applicability reverses, while staying unchanged outside scope. This avoids repeatedly generating complete files and directly attacks the claimed context sensitivity. It remains a teacher-forced diagnostic, not a substitute for generation success or matched SFT.

3. **Only after evidence of selective behavior, buy the free-generation comparison and SFT attribution.** Keep the existing checkpoint frozen. Do not select a better-looking checkpoint or tune the diagnostic on model outcomes.

There is a concrete timing reason to investigate step 2: the existing training run scored **1,152 chosen/rejected pairs in 1,855 seconds**. A much smaller forward-scoring diagnostic could be materially cheaper than 96 autoregressive whole-file replies, although loading and workload differences require a measured budget. [/home/bmarti44/stencil-llm/results/a-screen/adapters/cf/train-log.json:22](/home/bmarti44/stencil-llm/results/a-screen/adapters/cf/train-log.json:22)

I would **not start by training a smaller trunk**. The existing 4B adapter already contains the intervention of interest. A smaller model can help test a simple rule-state representation, but its failure may be a capacity failure and its success would not establish the 4B artifact’s behavior.

**8. The most useful outside-field lessons change the experiment, not just its vocabulary.**

**Cognitive psychology: separate remembering a correction from using it.** Wahlheim and Jacoby found that detecting and recollecting change can reverse interference into facilitation. A 2025 experiment by Guo, Chen and Hu found that supplying an alternative explanation reduced continued influence more than retraction alone. These motivate separate tests of rule identification and rule execution, and separate conditions for cancellation versus explicit replacement. They do not establish that a transformer has the same mechanism. [Wahlheim and Jacoby](https://pubmed.ncbi.nlm.nih.gov/22918874/), [Guo et al.](https://www.sciencedirect.com/science/article/pii/S0278262625000302)

**Experimental economics supplies a particularly strong control.** Gonçalves, Libgober and Willis compare retracted information with both never-presented information and informationally equivalent direct information. Their experiments find weaker updating from retractions. For Stencil, compare three histories with the same final applicable rule: directly stated current rule, obsolete rule followed by cancellation/replacement, and irrelevant-history control. Hold the task and repository constant. This separates history-related difficulty from final-task competence. [Retractions: Updating from Complex Information, published online 2025; 2026 journal issue](https://discovery.ucl.ac.uk/id/eprint/10205481/)

**Formal belief revision: a flat current-value register loses essential history and dependencies.** Doyle’s truth-maintenance system records reasons for beliefs so changes can propagate through their dependents. Darwiche and Pearl show why ordinary AGM postulates are insufficient to constrain iterated revision of conditional beliefs. The relevant lesson is to track applicability and justification, not simply suppress an old string. Cancellation of a premise can invalidate several consequences; a conclusion supported independently may remain valid. [Doyle, 1979](https://www.sciencedirect.com/science/article/pii/0004370279900080), [Darwiche and Pearl, 1997](https://ftp.cs.ucla.edu/pub/stat_ser/R202.pdf)

**Database systems: fresh memory does not guarantee a valid pending action.** Optimistic concurrency control validates a transaction’s read set before committing. PlanFence applies related ideas to plans whose dependencies may have changed before execution. A useful additional workload is therefore an interrupted coding task: plan under rule A, receive revision B, then execute. Measure whether the pending implementation is revised, not merely whether B can be quoted. PlanFence’s own guarantees depend on declared dependencies and other explicit assumptions; this is a workload lesson, not an off-the-shelf proof of agent correctness. [Kung and Robinson, 1981](https://www.eecs.harvard.edu/~htk/publication/1981-tods-kung-robinson.pdf), [PlanFence limitations](https://arxiv.org/html/2609.03340v1)

**Version control: undo is a new operation, not deletion of history.** Git revert records a reversal while preserving ancestry; reverting a merge also affects what later merges will bring back. For Stencil, test an A→B→A sequence with an unrelated intervening change C that must survive. A whole-state rollback should fail. [Git documentation](https://git-scm.com/docs/git-revert)

**Legal interpretation: cancellation, reinstatement and prospective effect are distinct operations.** UK drafting guidance explicitly notes that repealing a repeal does not automatically revive the original enactment. It also distinguishes partial amendments and their continuing effects. This defeats a universal binary “cancel B, therefore A” heuristic. Define the intended semantics explicitly and test cancellation without replacement separately from express reinstatement. This is an analogy for specification, not a proposed universal rule of legal interpretation. [Office of the Parliamentary Counsel, sections 6.1.6–6.1.13](https://www.gov.uk/government/publications/drafting-bills-for-parliament/2024-03-19-drafting-guidance)

**Program verification: preservation requires a defined footprint.** Separation logic’s frame rule makes local change compatible with preservation of disjoint state under stated conditions. Stencil’s behavioral analogue should name what may change, what must remain unchanged, and which dependencies connect them. Fresh unaffected operations are essential because copying old code is an inadequate test of that property. [Reynolds, 2002](https://www.cs.cmu.edu/~jcr/seplogic.pdf)

These observations suggest useful workloads beyond convention naming: versioned API migrations with compatibility obligations, tenant-specific configuration exceptions, feature-flag rollback with unrelated fixes preserved, and interrupted plans whose requirements change before execution. Pick one with a deterministic oracle and short executable outputs. Do not expand into all of them.

**9. Prior findings retain their original severities and receive these dispositions.**

| Prior finding | Disposition |
|---|---|
| **§1, high:** request-1 supersession mislabelling | **Resolved** for the current target operations; scope qualification and consumer-test coverage are discussed above. |
| **§2, high:** insufficient evidence for the full artifact direction | **Open.** Training completion resolves the unfinished-checkpoint subfinding, not transfer or usefulness. |
| **§3, high:** established-method permutation | **Open, strengthened** by IOPO’s explicit DPO\*/SFT\* construction and broader selective-revision prior art. |
| **§4, medium:** unnecessary baseline rerun | **Resolved:** the exact old/new runner pair is equivalent on the inspected adapterless path. |
| **§4, high:** invalid stopping rationale and count threshold treated as proof | **Open.** CF failure still does not imply SFT failure; the interval calculation reinforces the distinction between screening and proof. |
| **§6, high:** comparison population, identity and replay acceptance | **Partially repaired; still open**, with reproduced shared-subset, missing-field and replay escapes. |
| **§6, high:** causal difference-of-differences interpretation | **Resolved in `compare.py`** by descriptive wording. |
| **§6, high:** narrow functional score overstated usefulness | **Partially repaired; still open.** More outcomes are printed, but the acceptance wording and registered session-level reporting remain inadequate. |
| **§6, medium:** `stale2.py` completeness and replay enforcement | **Open.** |
| **§6, medium:** original preflight objective/hub/missing-field defects | **Resolved for those demonstrated cases.** Additional limitations are separately graded above. |
| **§6, low:** scratchpad import override | **Resolved.** |
| **§6, low:** `look.py` is descriptive, not a comparison authority | **Retained.** No new authority is established by this review. |
| `names.py` isolated-retention interpretation | **Resolved by retirement.** The revised tool uses the actual entering repository and limits itself to naming. [/home/bmarti44/stencil-llm/results/a-screen/analysis/names.py:1](/home/bmarti44/stencil-llm/results/a-screen/analysis/names.py:1) |
| `health.py` signals are not transfer evidence | **Retained.** |
| **§7, high:** long-horizon, architectural-transfer, selected-endpoint and common-scoring-defect limitations | **Remain applicable.** The baseline document now acknowledges them; acknowledgment does not supply the missing evidence. The ledger still contains the refuted common-scoring-defect argument. [/home/bmarti44/stencil-llm/plan/LEDGER.md:3961](/home/bmarti44/stencil-llm/plan/LEDGER.md:3961) |

**10. Forecast and investment decision.**

I define artifact success as a published, reproducible artifact with a practically meaningful, statistically supported improvement over its disabled counterpart, evidence supporting the claimed recombination beyond matched SFT, and transfer beyond the generator’s shortcuts. I am not requiring acceptance at a particular conference.

My fresh forecast is **15%**. A transparent approximate decomposition is:

- 55% chance of useful CF improvement over the trunk;
- 45% conditional chance that the matched-SFT comparison supports a substantive incremental contribution;
- 65% conditional chance that the result survives a distinguishing scope/restoration test and broader construction transfer;
- 90% conditional chance of successful reproducible packaging.

Their product is approximately 14.5%, rounded to 15%. These are subjective conditional judgments, not measured probabilities or independent empirical estimates.

Completed training and corrected measurement improve operational readiness. Context-DPO and related results support plausibility. Against that stand direct prior art, unresolved attribution, a screen that admits simple behavioral shortcuts, and weak precision—especially for preservation.

I cannot disprove the usefulness of selective rule revision as a general research problem. **I can reject the present claim that Candidate A is already a defensible substantive recombination with at least a 25% chance of satisfying the full artifact goal.** Further guard repair alone will not change that assessment.

VERDICT — OFF TRACK — 15% artifact-success forecast, below 25%; establish a matched scope-and-restoration test that defeats recency and copying before further GPU spend.
