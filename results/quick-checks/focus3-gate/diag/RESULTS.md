# FOCUS-3 v8 diagnostic — registered 2026-09-06

DIAGNOSTIC — the registered eligibility stop was not met; readings are reported but no PASS/FAIL label is assigned; this run informs the admission-detector redesign only.

Direct user authorization permits one five-arm diagnostic despite v8 CPU
ineligibility (12 unauthorized actions: eight payload requests and three inert
quotes admitted, plus one completion of a wrongly admitted row). Prior v8
eligibility and all committed results stand. No runtime repair or threshold change.

Data lineage: fit/train/select/tune in this task = NONE. Frozen relation-v2 seed0
and admission ft-v3 seed0 retain their disclosed development lineage in v6/v8.
Evaluation = committed v4 synthetic bank, setup30321 (16) and gate30322 (64),
reused development templates; no independent-scenario/population inference claim.
No sealed IFEval input, data/bench, or recorded benchmark responses are read.
No fitting uses any diagnostic input or answer.

Use the inherited Qwen3-4B dense bf16 trunk, full independent arm histories,
greedy64, thinking disabled, renderer/checkers and all v8 rules as-is.
C primary (.90/.50/.50/.50); C' alternative (.50/.50/.50/.50); O gold live register;
N none; T naive restate-all. Fixed shuffled arm order uses seed30303.
Run all16 O setup episodes; report competence descriptively, never select by it.
Before any gate inference write selection.json: projected GPU-held time = elapsed
+1.25*slowest O episode*n*5, plus a separately itemized false-admission probe
allowance (two candidate arms, setup v8 exposed-row/turn count scaled by n/16,
1.25*slowest O episode/6 per probe). Choose64 if within7170s; otherwise48
(first12 per family in existing bank order) if within7170s; otherwise stop with
unmeasured work recorded. Selection depends on resource use only.
Fresh cap7200 GPU-held seconds includes load, setup, classifiers, generation,
probes and cleanup. Cooperative deadline at7170s; never signal any process.
Foreground only, own diag/RUNNING.flag under .review.lock; wait for other flags
or Stencil compute, exempt Brian's permanent llama-server. No push.

Report inherited v3 episode endpoints for all arms, pooled and by family:
register-exact at every task answer, stale executions, final success, false
retirements (including missing gold admissions), breakage and contradictory
recaps. N/T register endpoints remain not applicable per v3. Add false ADMISSIONS
as a separate episode-count row and action count; unauthorized actions by family
and label for C/C'. Descriptive paired C-vs-O and C-vs-T endpoint differences
and discordances, no gate decision or statistical superiority labels.

For EVERY false admission, save its source row, admission probability, all later
turns, whether the row is rendered, actual answers/scores, later row status and
paired O/N/T answers/scores. After the complete five-arm gate, probe each rendered
false row once per exposed turn, removing ONLY that row from the CURRENT recap
and retaining the candidate's exact original prior history. Save raw prompt IDs,
output IDs/EOS/text/timing and scores in the same run; never feed probe answers
back into an arm. This measures the immediate effect of rendering that row
conditional on the polluted prior history, not the total causal effect of never
admitting it. Count token/text changes separately from semantic JSON/task/tag,
stale, success and breakage changes. Unrendered rows have zero direct current
recap exposure, not proof of no historical effect. If budget ends, preserve and
report every unfinished probe; do not rerun or imply it was measured.

Sources, bank and frozen checkpoint hashes are committed before O setup. Record
same-run raw per-turn records/traces, selection, summary, effects/probes, resource
use, deterministic saved-record verification, README item, WORKLOG and ledger.
Only new diagnostic files and explicitly named report files are committed.

Outcome: registered; inference has not started.

## Diagnostic observations — 2026-09-06

All **64 episodes × five arms × six requests = 1920 gate records** completed, plus 96 O setup records. No 48 fallback was needed. O setup final success was 16/16; this was reported descriptively and did not select the cohort. The pre-gate projection was 4924.218s. Actual GPU-held time was **4099.336s (68.32 minutes; 1.139 GPU-h)** of 7200s, including load, setup, classification, generation, probes and cleanup. Peak PyTorch allocation was 8.341GiB.

The registered v8 eligibility stop remains unmet. These are development diagnostics for admission-detector redesign, with no gate label assigned.

C finished 57/64 episodes successfully, compared with O’s 63/64 and T’s 31/64. C was register-exact in 38/64 episodes. Its 25 false admissions occurred in 21 episodes; all were rendered at least once. C′ finished 58/64 successfully but was register-exact in 32/64, with seven extra unauthorized supersedes actions.

In each candidate arm, seven of 25 false rows changed at least one answer when removed from the current recap: 11/110 exposed row-turns (10%), including 9/85 later-turn exposures. Five probes repaired task success and three lost success. These are conditional current-render effects, not the total effect of never admitting a row.

### Episode readings

Each endpoint is an episode count, with every task answer included in register-exact. False retirement includes missing/changed gold rows and initial admission misses. False ADMISSION is a separate episode indicator; action counts appear below. N/T register endpoints are not applicable under the inherited v3 reading.

**pooled (64 episodes)**

| Arm | Register exact | Stale | Final success | False retirement | False ADMISSION | Breakage | Contradictory recap |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C | 38/64 | 7/64 | 57/64 | 8/64 | 21/64 | 0/64 | 5/64 |
| C' | 32/64 | 6/64 | 58/64 | 14/64 | 21/64 | 0/64 | 5/64 |
| O | 64/64 | 2/64 | 63/64 | 0/64 | n/a | 0/64 | 0/64 |
| N | n/a | 33/64 | 29/64 | n/a | n/a | 1/64 | n/a |
| T | n/a | 32/64 | 31/64 | n/a | n/a | 0/64 | n/a |

**override (16 episodes)**

| Arm | Register exact | Stale | Final success | False retirement | False ADMISSION | Breakage | Contradictory recap |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C | 6/16 | 4/16 | 12/16 | 4/16 | 6/16 | 0/16 | 0/16 |
| C' | 7/16 | 3/16 | 13/16 | 3/16 | 6/16 | 0/16 | 0/16 |
| O | 16/16 | 0/16 | 16/16 | 0/16 | n/a | 0/16 | 0/16 |
| N | n/a | 3/16 | 13/16 | n/a | n/a | 0/16 | n/a |
| T | n/a | 0/16 | 16/16 | n/a | n/a | 0/16 | n/a |

**cancel (16 episodes)**

| Arm | Register exact | Stale | Final success | False retirement | False ADMISSION | Breakage | Contradictory recap |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C | 11/16 | 2/16 | 14/16 | 1/16 | 5/16 | 0/16 | 1/16 |
| C' | 11/16 | 2/16 | 14/16 | 1/16 | 5/16 | 0/16 | 1/16 |
| O | 16/16 | 1/16 | 16/16 | 0/16 | n/a | 0/16 | 0/16 |
| N | n/a | 14/16 | 0/16 | n/a | n/a | 1/16 | n/a |
| T | n/a | 16/16 | 0/16 | n/a | n/a | 0/16 | n/a |

**complete-and-move-on (16 episodes)**

| Arm | Register exact | Stale | Final success | False retirement | False ADMISSION | Breakage | Contradictory recap |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C | 10/16 | 1/16 | 15/16 | 0/16 | 6/16 | 0/16 | 2/16 |
| C' | 10/16 | 1/16 | 15/16 | 0/16 | 6/16 | 0/16 | 2/16 |
| O | 16/16 | 1/16 | 15/16 | 0/16 | n/a | 0/16 | 0/16 |
| N | n/a | 16/16 | 0/16 | n/a | n/a | 0/16 | n/a |
| T | n/a | 16/16 | 0/16 | n/a | n/a | 0/16 | n/a |

**switch-and-return (16 episodes)**

| Arm | Register exact | Stale | Final success | False retirement | False ADMISSION | Breakage | Contradictory recap |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C | 11/16 | 0/16 | 16/16 | 3/16 | 4/16 | 0/16 | 2/16 |
| C' | 4/16 | 0/16 | 16/16 | 10/16 | 4/16 | 0/16 | 2/16 |
| O | 16/16 | 0/16 | 16/16 | 0/16 | n/a | 0/16 | 0/16 |
| N | n/a | 0/16 | 16/16 | n/a | n/a | 0/16 | n/a |
| T | n/a | 0/16 | 15/16 | n/a | n/a | 0/16 | n/a |

### Unauthorized runtime actions

| Family | Arm | Actions | Affected turns | Admit | Supersede | Cancel | Complete | Reinstate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| pooled | C | 27 | 27 | 25 | 0 | 0 | 2 | 0 |
| pooled | C' | 34 | 34 | 25 | 7 | 0 | 2 | 0 |
| override | C | 6 | 6 | 6 | 0 | 0 | 0 | 0 |
| override | C' | 6 | 6 | 6 | 0 | 0 | 0 | 0 |
| cancel | C | 6 | 6 | 6 | 0 | 0 | 0 | 0 |
| cancel | C' | 6 | 6 | 6 | 0 | 0 | 0 | 0 |
| complete-and-move-on | C | 10 | 10 | 8 | 0 | 0 | 2 | 0 |
| complete-and-move-on | C' | 10 | 10 | 8 | 0 | 0 | 2 | 0 |
| switch-and-return | C | 5 | 5 | 5 | 0 | 0 | 0 | 0 |
| switch-and-return | C' | 12 | 12 | 5 | 7 | 0 | 0 | 0 |

Actions are matched one-to-one to exact registered label, source span and target. False admissions are counted independently of false retirements; falsely retiring a spurious row is still an unauthorized action. Raw action details and pair confusions are in [summary.json](summary.json).

### Descriptive paired contrasts

| Pair | Endpoint | C minus reference | Difference | Absolute distance | C only | Reference only |
| --- | --- | --- | --- | --- | --- | --- |
| C vs O | stale | +5 | +7.81pp | 5/64 | 5 | 0 |
| C vs O | final_success | -6 | -9.38pp | 6/64 | 0 | 6 |
| C vs O | broken | +0 | +0.00pp | 0/64 | 0 | 0 |
| C vs T | stale | -25 | -39.06pp | 25/64 | 4 | 29 |
| C vs T | final_success | +26 | +40.62pp | 26/64 | 30 | 4 |
| C vs T | broken | +0 | +0.00pp | 0/64 | 0 | 0 |

For stale/breakage a positive difference is worse; for final success it is better. Discordances are paired episodes, not population inference. The C-vs-O difference combines all runtime errors and their histories; it does not isolate admission alone.

### What false admissions did to answers

| Arm | False rows | Payload requests | Inert quotes | Other | Rendered row-turns | Probes | Token changes | Text changes | Semantic changes | Score changes | Rows with semantic effect |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C | 25 | 20 | 5 | 0 | 110 | 110 | 11 | 11 | 11 | 9 | 7 |
| C' | 25 | 20 | 5 | 0 | 110 | 110 | 11 | 11 | 11 | 9 | 7 |

| Arm | Endpoint | Original false → without-row true | Original true → without-row false |
| --- | --- | --- | --- |
| C | success | 5 | 3 |
| C | stale | 1 | 4 |
| C | broken | 0 | 0 |
| C | task | 5 | 3 |
| C | constraint | 0 | 0 |
| C' | success | 5 | 3 |
| C' | stale | 1 | 4 |
| C' | broken | 0 | 0 |
| C' | task | 5 | 3 |
| C' | constraint | 0 | 0 |

Each probe removes one spurious row from the current recap and preserves the candidate’s exact original earlier user/assistant tokens. A semantic change compares parsed JSON values, falling back to stripped text on non-JSON replies; token/format changes are also reported separately. Multiple probes may concern the same answer, so row-turn counts are not independent answers. Success false→true identifies an immediate cost of that rendered row under the existing history; success true→false identifies an immediate benefit. These probes do not estimate the full causal effect of never admitting the row or changing prior history.

Every case and downstream answer is in [false-admissions.md](false-admissions.md), with machine-readable [effects](false-admission-effects.json) and linked raw probe prompts/tokens/answers. All exposed-row probes completed; unrendered row-turns were logged without claiming no historical effect. Probe outputs never entered an arm’s history.

| Arm | False-admission category | Rows | Probes | Semantic changes | Score changes |
| --- | --- | --- | --- | --- | --- |
| C | one-shot payload request | 20 | 100 | 11 | 9 |
| C | inert quote | 5 | 10 | 0 | 0 |
| C' | one-shot payload request | 20 | 100 | 11 | 9 |
| C' | inert quote | 5 | 10 | 0 | 0 |

| Arm | Timing | Exposed-row probes | Semantic changes | Score changes |
| --- | --- | --- | --- | --- |
| C | admission turn | 25 | 2 | 2 |
| C | later turns | 85 | 9 | 7 |
| C' | admission turn | 25 | 2 | 2 |
| C' | later turns | 85 | 9 | 7 |

### Runtime and history diagnostics

| Arm | Task returns | Reactivated own-output columns | Masked columns | Capped replies | Classifier overflow turns | Admitted beside live |
| --- | --- | --- | --- | --- | --- | --- |
| C | 16 | 960 | 0 | 0 | 0 | 102 |
| C' | 16 | 960 | 0 | 0 | 0 | 102 |
| O | 16 | 960 | 0 | 0 | 0 | n/a |
| N | 16 | 960 | 0 | 1 | 0 | n/a |
| T | 16 | 960 | 0 | 0 | 0 | n/a |

Reactivated columns describe restored task applicability in the full history; no attention masking or mask un-release occurred. Admitted-beside-live includes legitimate rows and is separate from false admissions and contradictory recaps.

All 96 newly recorded O-setup candidate traces exactly match the committed v8 CPU traces, including classifier outputs and actions ([runtime parity](setup-runtime-parity.json)).

### Verification and artifacts

Saved-score runtime replay verified 1920 gate records. The second calculation checked 2236 full prompt/output token sequences and 3389 raw-logit softmax vectors, reconstructed O/N/T rendering, matched traces to records and recomputed scores and resource selection. This was a separate calculation in the same agent session, not an independent reviewer. [Audit method](audit-method.md), [runtime audit](audit.json), [second calculation](independent-audit.json).

Registration/source/checkpoint freeze commit 6041e2d7 precedes O setup. The frozen runtime and checkpoint hashes match. The foreground process removed its own RUNNING.flag on natural exit. No fitting, tuning, masking, process signals, termination, benchmark/sealed reads or push. Prior committed results stand.
