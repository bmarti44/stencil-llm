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
measure and disclose any excess. Foreground only. The reboot note supersedes the old check40/check41 priority
wait: allow Brian's permanent server (pid2705), wait for any other NVIDIA compute
process or Stencil RUNNING.flag, and publish our flag under .review.lock.
CPU replay verifies exact saved input trajectories, retained assistant content,
output token/text identity and recomputed scores before the final local commit.

Preparation v1 was superseded before any generation to mark delay blocks as
retireable cue segments. Final CPU smoke: 204 records over eight episodes; exact
C replay: 1,632 records over all 192 selected episodes. Perturbed input rejected;
McNemar direction checked; 11 targeted FOCUS-2d tests pass.

PENDING — resumed from verified committed CPU preparation. Four uncommitted
pre-outage records are preserved under interrupted-pre-reboot/ and excluded from
this fresh run, as directed by the committed-state recovery rule. No outcomes
were used to change the design. Charge 299 seconds (old launch through kernel
boot, including downtime) to the same cap: combined projection 12,356.312 s
(3.432 h) remains within 12,600 s. Original freeze, reading and source preserved;
only resource coordination/accounting changed before the new launch.

## Results

**Final status: COMPLETE schedule; MASKING NOT CLOSED under the frozen reading.**
The pre-run PENDING text above is preserved history. All 192 scheduled episodes
were attempted; 124 have all three arms. Both candidates meet the numeric
all-five/McNemar/constraint conditions on those 124, but B's 68 twice-capped delay
episodes violate the additional no-exclusion condition fixed before generation.

**Input-accounting correction, with no sample change:** the frozen first 48
indices in each cell retain **16 memo episodes/cell, 64 total**, not the
12/cell and 48 total stated in the preparation prose and freeze's descriptive
selection string. All selected IDs, bank bytes, seeds and scores are unchanged.
The subset retains all 64 original memo episodes and 128 of 192 non-memo episodes;
it is balanced by direction/delay but has a higher memo fraction than the full
bank. Counts and indices are in `input-accounting.json`; every table uses actual
denominators. The historical freeze and prewritten text remain intact for audit.

| Arm | Scheduled | Complete checkpoint trajectories | Twice-capped delay episodes | Capped delay attempts |
|---|---:|---:|---:|---:|
| A | 192 | 192 | 0 | 0 |
| B | 192 | 124 | 68 | 152 |
| C | 192 | 192 | 0 | 0 |

B's exclusions are 68/96 delay episodes (36 ascending, 32 descending). Each
excluded episode failed to emit an ending at both the 160-token first attempt
and the 320-token retry. All attempts are preserved. These are the harness's
**isolated neutral-delay generations**, which are later replayed into retained
history. They are not included in the scored-checkpoint F6 rows below. Thus zero
checkpoint truncations does not mean no capped generations.

The following primary and recorded-reference tables use the **same 124 eligible
episodes** (41 memo episodes). They are conditional on B completing its delays.

Completed paired episodes: 124/192; new records: 4471. CPU replay verified every prompt, retained answer, cue retirement and score.

| Arm | All-five | SWITCH | HOLD | BACK | CLEAR | NEUTRAL2 | Constraint failures | Broken |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| A | 99 | 116 | 119 | 121 | 121 | 115 | 0 | 0 |
| B | 99 | 117 | 121 | 120 | 118 | 116 | 0 | 0 |
| C | 88 | 108 | 120 | 115 | 107 | 124 | 0 | 0 |
| both (recorded reference) | 78 | 101 | 114 | 115 | 109 | 124 | 15 | 0 |
| neither (recorded reference) | 0 | 57 | 73 | 88 | 0 | 9 | 0 | 0 |

| Contrast | All-five b/c | p(worse) | p(better) | Constraint excess | Closure |
|---|---:|---:|---:|---:|---|
| A_vs_C | 23/12 | 0.97952 | 0.0447655 | 0 | False |
| B_vs_C | 20/9 | 0.98794 | 0.0307142 | 0 | False |
| B_vs_A | 4/4 | 0.636719 | 0.636719 | 0 | secondary |

| Arm | user_fact failures | tool_fact failures | assistant_fact failures |
|---|---:|---:|---:|
| A | 1/124 | 1/124 | 23/41 |
| B | 0/124 | 0/124 | 3/41 |
| C | 0/124 | 0/124 | 27/41 |
| both | 0/124 | 0/124 | 41/41 |
| neither | 0/124 | 0/124 | 25/41 |

| Arm | broken | json_invalid | schema_invalid | empty | placeholder | truncated | repetitive |
|---|---:|---:|---:|---:|---:|---:|---:|
| A | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| B | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| C | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| both | 0 | 0 | 15 | 0 | 0 | 0 | 0 |
| neither | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

Per-checkpoint constraint and F6 counts, paired collateral contrasts, and exact denominators are in summary.json. F6 counts above are episodes with any flagged checkpoint; schema_invalid alone is not structural breakage.

**MASKING NOT CLOSED by the frozen reading:** the no-exclusion condition fails. Both A and B score 99/124 versus C 88/124, with zero constraint failures; their numeric conditions pass on this common subset. Missing B trajectories prevent the complete-sample closure claim. This result supplies no evidence that masking fixes B's delay failures.

Repeating schema/tag changes all-five by +0 episodes (B versus A; discordances 4/4). This is the schema-carrier contrast.

These are reused synthetic bank outcomes with fresh generations, a scaled 192-episode quick check, and an operational closure decision. A nonsignificant McNemar test does not prove equivalence, general safety, benchmark transfer, or autonomous detection of rule changes.

GPU allocation: 3.2309 h / 3.5 h, including loading.

## Full A/C coverage diagnostic and FOCUS-3 conclusion

This additional coverage view was declared after B's delay exclusions appeared,
before aggregate task scores were inspected. It uses all 192 planned A/C pairs
and is descriptive; it does not replace the frozen common-sample decision.

| Arm | All-five | Constraint failures | Broken | User-fact failures | Tool-fact failures | Assistant-fact failures |
|---|---:|---:|---:|---:|---:|---:|
| A | 151/192 | 0/192 | 0/192 | 1/192 | 1/192 | 39/64 |
| C | 131/192 | 0/192 | 0/192 | 0/192 | 0/192 | 42/64 |

A versus C: **+20 all-five episodes (+10.4167 percentage points)**;
paired discordances **39/19**, exact p(worse) **0.9973225702**,
p(better) **0.005964069858**. A meets the requested numeric efficacy and
constraint screen on its complete A/C pairs. The extra frozen all-arm
no-exclusion guard still blocks the check's formal MASKING CLOSED label.

**FOCUS-3:** A, the plain live task rule in every request with own answers kept,
is the useful text-only ship candidate on this family. Its complete A/C comparison
improves all-five success with zero observed schema/tag failures; this check
demonstrates no need for a custom cache/mask to reach that result. It does **not**
establish zero collateral harm: A loses both the user and tool fact in one
NEUTRAL2 episode, and assistant-fact failures remain 39/64 (C: 42/64).

Adding schema/tag locally (B) gives **no net all-five improvement over A** on
124 common episodes (99 each; discordances 4/4). It improves assistant-fact recall
there (3 failures versus A's 23, denominator 41), but its 68 delay exclusions make
the exact all-turn B carrier unsuitable as a validated ship recipe. Preserve the
request type distinction in any future design; do not infer that these isolated
neutral-delay failures will be repaired by masking. No follow-up design or experiment
was performed.

The retained-answer claim is verified through exact trajectory replay, not
inferred from a mask setting. All **4,471 records** passed replay and score audit;
independent arithmetic reproduced every primary/reference count and McNemar p.
All **1,632 fresh C records** have exactly the original prompt IDs, output IDs,
terminals and flags. The 2,560 recorded BOTH/neither files match their git blobs.
`summary.json` includes the completion/input corrections and full A/C diagnostic;
`analyzer-summary.json` preserves the frozen analyzer's output unchanged.

Total charged allocation **11631.287 s / 12,600 s
(3.230913 h)**: new run 11332.287 s plus
299 s conservative pre-outage allowance. RUNNING.flag removed after natural
completion; no signals, sealed reads, fitting/training, background launch or push.
