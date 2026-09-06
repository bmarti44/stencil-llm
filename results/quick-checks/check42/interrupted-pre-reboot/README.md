# Check 42 — live-rule placement in every request

Unregistered, disclosed quick check, authorized 2026-09-05. Fit/train-on: **none**.
Evaluated-on: **reused** frozen FOCUS-2d final bank, seed **9053723**, whose outcomes
have already been seen for other arms. A/B/C are **new generations**. Reuse the
same Qwen3-4B competence certificate (ascending 61/64, descending 57/64, default
64/64), model/tokenizer assets, greedy bf16 non-thinking backend and scoring in
`src/stencil/focus2.py`, the library consumed by `scripts/focus2.py`. No sealed
IFEval input or sealed BFCL cohort contents are read. No weights are fitted.

## Pre-written reading — fixed before new model output

**MASKING CLOSED on this family** if A or B has all-five success count >= C,
the exact one-sided McNemar test for that candidate being **worse** than C has
**p > .05**, and candidate constraint-failure episodes **<= C + 2**. Define
b = candidate succeeds/C fails, c = candidate fails/C succeeds; p(worse) is
P[Binomial(b+c,.5) >= c], or 1 with no discordances. Also report p(better) and
the full b/c counts. This implements the requested operational not-worse reading;
a nonsignificant test is not a statistical proof of equivalence. No adjustment
or new threshold after outcomes. Otherwise report the measured gap. Secondary:
**B versus A** isolates adding the schema/tag carrier. No complete-pair closure
claim if any planned episode is excluded or the run is incomplete.

All-five is the conjunction of task success, unchanged schema/tag constraint,
and no structural breakage across SWITCH/HOLD/BACK/CLEAR/NEUTRAL2. Constraint
failures count episodes with any failing checkpoint. Preserve FOCUS-2d's exact
collateral scoring (user_fact/tool_fact; assistant_fact only memo episodes),
schema_invalid separate from F6 structural broken, and every F6 flag. Tables
use the same episode subset for all arms and recorded references.

## Frozen arms and history semantics

- **A — placement-every-request:** plain current task/default rule plus that
  task request's obligations, in every task request (SET/PREHOLD and all five
  scored checkpoints), and the live task/default rule in each delay user turn.
  No recap or anti-imitation wording. Original system schema/tag remain.
- **B — A plus local schema/tag:** same block order: task/default, schema, tag,
  request obligations. Schema/tag are repeated in delay user turns too; those
  neutral turns have no task-specific additional-key obligation.
- **C — text-restate exactly as FOCUS-2d:** original system SET cue and uncued
  SET/PREHOLD; original recap at all five checkpoints, no local schema/tag;
  original uncued delay user text. All generations are fresh.
- **Recorded BOTH and neither:** original FOCUS-2d raw records, no regeneration;
  subset-matched reference rows, not additional experimental arms.

Every arm keeps all its own generated assistant answers, terminals and fact/tool
scaffolding. A/B retire the initial system task cue before SET; old task cue
segments retire at change events exactly through FOCUS-2d's placement machinery.
Inserted delay blocks are owned cue segments and retire with their rule event too.
No assistant body is removed or replaced. Every request uses empty KV and
contiguous positions as before; this is prompt management, no custom cache mask.
The fixed bootstrap fact/tool turns stay identical and are not task requests.

Preserve FOCUS-2d's isolated generation then replay of each delay pair: 512-token
neutral base user text plus A/B's rule block, their separately generated answer,
then replay that exact complete pair into that arm's history. Thus A/B neutral
user bodies exceed 512 tokens by the disclosed block length. DELAY0 carries SET,
DELAY1 SWITCH, DELAY2 CLEAR/default. C's delay bodies remain exactly 512 tokens.
All arms generate their own SET/PREHOLD and three delay answers; no recorded
prior or another arm's answer is borrowed. Original 128 task / 160 then 320
delay token caps and complete-nonempty-delay validation apply. A twice-capped
delay excludes its episode from every paired arm; all attempts stay recorded.
Delay records retain the inherited base-delay token metadata; input_ids and
input_layout provide the exact full user/prompt token lengths including blocks.

## Resource decision — before generation

The 72.9-second worst FOCUS-2d pilot cell covered five arms with shared priors
and delays. Project three arms as **72.9 × 3/5 × 1.4 × N + 300 seconds**:
40% allowance for unsharing priors/delays and larger local blocks, plus five
minutes loading. N=256 projects **15,976.416 s (4.438 h)**, above 3.5 h.
Use the user-authorized **192 episodes**, projecting **12,057.312 s (3.349 h)**.
Selection is frozen original index <48 in each direction/delay cell: 48 each
ascending/0, ascending/512, descending/0, descending/512, including 12 memo
episodes per cell (48 memo episodes total). No score-based sampling or tuning.
The full 256-episode bank is unchanged. This is a disclosed scaled quick check.

GPU cap **12,600 seconds including loading**, cooperative checks between tokens
and requests, no signals or process termination. Blocking operations may overrun;
measure and disclose any excess. Foreground only. Check 40 then check 41 retain
priority: poll NVIDIA compute processes and both terminal readings/processes
every 600 seconds. Start only when no NVIDIA compute process remains and each
priority check has a terminal reading or no live run process. Respect .review.lock.
CPU replay verifies exact saved input trajectories, retained assistant content,
output token/text identity and recomputed scores before the final local commit.

Preparation v1 was superseded before any generation to mark delay blocks as
retireable cue segments. Final CPU smoke: 204 records over eight episodes; exact
C replay: 1,632 records over all 192 selected episodes. Perturbed input rejected;
McNemar direction checked; 11 targeted FOCUS-2d tests pass.

PENDING — pre-written reading; no check-42 model outputs exist.
