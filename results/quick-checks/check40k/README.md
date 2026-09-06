# Check40k — task competence beyond a rendered JavaScript rule

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

Results pending.
