# Check40k — task competence beyond a rendered JavaScript rule

**Completed: R3 — harm. Text-only16/32 versus text+bias7/32; wins2/losses11/ties19. Actuator stays off by default.**

Prewritten 2026-09-06 before GPU work; recipe committed before inference.
Data lineage: fit-on = nothing in this check; calibrate-on = eight authored DEV
programming tasks only; evaluated-on = 32 remaining authored tasks, opened once.
All 40 are freshly invented here; no public benchmark or recorded benchmark
responses used. Inherited actuator lineage: check40b competence profiles, unchanged
check40g alpha-3 JS tensor, same tensor hash as check40j. No new bias fitting/tuning.
Hidden means tests are committed for audit but never supplied to the model.

Qwen3-30B-A3B HF bf16, inherited check40 RouterHooks, all 48 layers,
prefill+decode, greedy, thinking disabled, independent fresh sessions, cap 768.
Exact check40j literal user-line "Live rules: (1) Write all code in JavaScript."
prepended to the current request; check40e system and suffix unchanged. As recorded
in 40j, this literal differs from the repository renderer's Active user rules JSON.
Arms: text-only | text+bias | text+shuffled-bias | OFF. Each evaluation task gets
all four arms, order rotated by task index to balance timing. 128 final generations.
Shuffled control: torch CPU generator seed 401107, independent randperm(128) per
layer, fixed for the whole run. Exactly preserves each layer's multiset and norm.

DEV target: 4..6 of 8 task successes (integer realization of 40..75%). DEV uses
text-only. If outside range, adjust DEV task difficulty only while retaining this
single model load and total resource cap; preserve all earlier DEV versions and
records. No evaluation outcomes may inform any adjustment. Freeze the calibrated
recipe in a local commit before opening the 32 evaluation tasks. If calibration
cannot qualify within budget, stop as INCOMPLETE; do not evaluate at ceiling.
The 32 evaluation tasks are fixed before GPU work and never changed from DEV.
A non-ceiling DEV result does not guarantee non-ceiling held-out performance;
if text-only is at 32/32 report the ceiling limitation without a replacement run.

Primary success = all four hidden Node tests pass. Language, syntax, inherited
40i broken flags (empty/invalid/ambiguous/fences/truncation/repetition), and token
counts are separate outcomes: broken is NOT silently added to the success endpoint.
Node executes extracted code in a fresh vm context per case, 200ms VM timeout;
JSON-normalized values compared by deepStrictEqual. Undefined/non-JSON outputs fail.
Input mutation checked for tasks explicitly requesting nonmutation. Python syntax
is recognized but is not executed: OFF success is JavaScript-task success, not a
language-neutral competence estimate. Semantic errors alone do not count as broken.

PRE-WRITTEN READINGS, fixed:
R1 "ship by default": bias wins-losses >=5/32, losses <=2, exact one-sided sign
p<=.05, shuffled wins-losses <=2, and bias broken <= text-only broken. Register
default-on consequence only for this certified authored JS task family.
R2 "no benefit": wins-losses <=1 -> behind flag, 40j decision stands.
R3 "harm": losses-wins >=3 -> stays off; record harm.
R4 otherwise -> INCONCLUSIVE at n=32, no enlargement.
Ambiguity resolved before outcomes: test R3 BEFORE R2 because literal R2 includes
large harms; retain literal R2 elsewhere (including net loss of two). R1 first,
then R3, then R2, then R4. Incomplete runs never receive a substantive reading.
Exact one-sided p = sum(comb(w+l,k), k=w..w+l)/2**(w+l), or 1 with no discordants.
Examples computed by prepare: 6-0=.015625,7-1=.03515625,9-2=.03271484375 qualify;
6-1=.0625,7-2=.08984375,8-2=.0546875 do not. The supplied 7-1=.031 was approximate
and incorrect; use the exact .03515625, which still qualifies.
Report wins/losses/ties for both paired contrasts, exact one/two-sided p and paired
95% difference CI: Bonferroni union of two 97.5% Clopper-Pearson marginal intervals
for win/loss probabilities, [win.lower-loss.upper,win.upper-loss.lower]. This is
conservative, not an equivalence test; rates also get exact 95% CP intervals.

Resource: one load, 45 GPU-minutes including load, DEV, idle/calibration and cleanup.
Cooperative token deadline with reserve, no signals. DEV measured throughput gives
an evaluation projection before opening; stop if projected total exceeds cap.
Coordinate with all quick-check RUNNING.flag files and review lock; pid2705 exempt.
No prior artifact rewrites, benchmark reads, background launches, signals or push.

## Completed result — R3: harm

**Do not ship this alpha-3 actuator by default.** With the rule rendered, text-only
passed 16/32 tasks; adding the frozen JS bias passed 7/32. The net change was
-9 tasks (-28.125 percentage points), meeting R3 (losses minus wins = 9 >= 3).
The actuator stays off by default / behind its existing opt-in flag. No runtime
shipping change is made or justified by this check. The claim is limited to this
model, tensor, dose, schedule and authored JavaScript task family.

DEV was 5/8 (62.5%) on the first and only pass: no task difficulty adjustment,
no retries and no evaluation-informed changes. Evaluation text-only was 16/32
(50%), so the requested non-ceiling competence comparison was achieved.

| Arm | All tests pass | Valid JS / Python / invalid | Broken | Truncated | Tokens total |
|---|---:|---:|---:|---:|---:|
| text-only | 16/32 (50.00%) | 32 / 0 / 0 | 0 | 0 | 4630 |
| text+bias | 7/32 (21.88%) | 30 / 0 / 2 | 2 | 1 | 4669 |
| text+shuffled-bias | 11/32 (34.38%) | 32 / 0 / 0 | 1 | 0 | 4738 |
| OFF | 7/32 (21.88%) | 17 / 14 / 1 | 3 | 0 | 4262 |

| Contrast vs text-only | Wins / losses / ties | Difference | Conservative 95% paired CI | One-sided p (benefit) | Exact two-sided p |
|---|---:|---:|---:|---:|---:|
| text+bias | 2 / 11 / 19 | -28.125 pp | [-55.123, +6.226] pp | 0.998291015625 | 0.0224609375 |
| text+shuffled-bias | 1 / 6 / 25 | -15.625 pp | [-38.900, +12.169] pp | 0.9921875 | 0.125 |

The primary ties comprise five both-success and fourteen both-failure tasks;
shuffled ties comprise ten both-success and fifteen both-failure tasks.
The preregistered paired CI is deliberately conservative: subtracting Bonferroni
Clopper-Pearson marginal bounds gives [-55.123,+6.226] pp. It contains zero even
though the conditional exact two-sided sign test gives .0224609375: these are
non-dual procedures with different conservatism. Do not describe this interval
as excluding no effect. The one-sided test for a benefit is .998291015625.
R3 is the prewritten magnitude reading, not a claim of population-wide harm.
Shuffled bias also loses net five tasks; there is no positive specificity result.

All eleven primary losses produced syntactically valid, unbroken JavaScript in
both arms. Thus the measured regression is task correctness, not merely language
choice or invalid output. For example, `quietSpans` with text-only correctly kept
the lower range bound after a negative minute mark, while bias used `prev=mark+1`
and emitted an interval starting below zero. The two primary wins were
`cancelMarks` and `runInventory`; per-task arm outcomes are in paired.json.
The two bias-broken tasks (`windowVotes`, `bracketTotals`) also failed text-only,
so they contributed ties, not any of the eleven semantic losses.

Only the biased `bracketTotals` reply hit cap768; text-only replies ranged62..279
tokens. The other bias-broken reply had invalid syntax. Shuffled broken1 and
OFF broken2 of3 were the inherited repetition heuristic, which can flag legitimate
repeated statements in longer code; the remaining OFF broken reply was invalid.
OFF returned JavaScript17, Python14, invalid1: its7/32 score is executable JS task
success only. Python program competence was not measured or counted as failure
on a language-neutral task; this diagnostic is explicitly language-dependent.

All136 records (8DEV +128 evaluation),160 hidden tests/reference solutions,
exact prompts/token IDs, per-forward fresh-session trace,48-layer hook contract,
bias hashes/permutations, summary and paired arithmetic passed CPU audit.
An additional strict-return sensitivity audit replaces JSON normalization by
structuredClone + deepStrictEqual to distinguish NaN/undefined/holes from null;
it changes ZERO individual test results across all136 records, and preserves R3.
No model reruns or primary-score changes were needed. Syntax-valid code with
wrong return values was tested through the actual Node consumer in preparation.

Recipe commit `288697191e6d47741efdcf527b6b87951e5c7990`; DEV/evaluation freeze commit
`4942594d5d25b69d1d1da43d2917e736f17e489f`. One cold load took
382.329s; total GPU reservation
1520.526/2700s (25.342 minutes), including calibration
and cleanup. Exactly one evaluation opening, no enlargement. RUNNING.flag removed;
no signals, process termination, benchmark reads, fitting, or push.

Reproduce CPU checks without inference:
`./.venv/bin/python scripts/focus_check40k.py audit` and
`./.venv/bin/python results/quick-checks/check40k/strict-audit.py`.
The run command refuses a second inference run when records already exist.
