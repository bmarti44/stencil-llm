# FOCUS-1 DRAFT v1 review — fable, 2026-09-04

Scope: LEDGER-PLAN.md "## FOCUS-1 ... (DRAFT v1)" (lines 1564-1636), tools/codex-agents/focus1-harness.md,
results/astra-drift-assessment.md, results/astra-path-assessment.md, archive/PLAN.md Phase 4 (lines 410-421),
results/quick-checks/README.md item 30, scripts/function_vectors.py, src/stencil/function_vectors.py,
src/stencil/qwen3.py (KVCache / prefill_with_eviction / residual_hook path, lines 60-150, 387-440),
INTERNAL-WAVE-PLAN.md (head). CPU only; no model, GPU, or torch import; no sealed benchmark file read.
Closed forms recomputed from a scratchpad pytest module (pure Python `comb`); numbers in Section 6.

## VERDICT: SOUND-WITH-FIXES

The design is a fair and honest oracle screen for Brian's question, with the right controls in the right places
(operand-balanced content-free vectors, fresh operands at every decision, matched-KV arms, opposite-address within-
episode contrast, retained-KV CLEAR with a clean-replay audit). It does not smuggle content. It has one HIGH
statistical defect (the CLEAR floor is likely unreachable under its own competence gate), one HIGH stop-rule
defect (control-arm breakage can kill the run without measuring anything, and the OFF cue-absent arm is never
exercised before test), and several medium clarity/fidelity issues, chief among them that the four sorting
decisions are independent forward passes given the enum, so "HOLD" and "BACK" add no mechanism beyond "SET":
the screen tests sustained-signal selection plus release, not any within-trunk persistence. That is acceptable
for an oracle controllability screen, but the claim ceiling must say it plainly. No critical findings.

Findings are numbered F1..F14 with severity; replacement text is in Section 7.

---

## 1. FIDELITY

**F1 (medium) — HOLD/BACK are re-SETs; nothing is held inside the trunk.** LEDGER-PLAN.md:1590-1591: only the
enum persists between decisions; every sorting decision starts from a canonical cue-free neutral-prefix KV that
excludes earlier replies; hooks are off during delays; injection (line 1584) is applied at the final prompt
position and every decoding position of every decision. Consequently the SET, HOLD, SWITCH, BACK decisions are
four independent forward passes that differ only in operands, the enum, and (for HOLD/BACK) a neutral prefix in
front. The "delay" tests whether the actuator still works after 128 neutral tokens in the KV; it does not test
that the trunk holds a selection. The draft admits "externally maintained latch screen, not autonomous
persistence" (line 1595) and "externally latched delay" (line 1612), which is honest, but the words SET/HOLD/
SWITCH/BACK invite a stronger reading. Miller's signal is *transient* and the selection persists; here the signal
is *sustained* throughout each answer and absent between answers. Fix: state in the claim ceiling that all four
decisions are independent given the enum and that no within-trunk persistence is tested or claimed; optionally
add the cheap descriptive arm in F2.

**F2 (low, recommended) — a 64-generation descriptive "transient-hold" arm would answer the one Miller-relevant
question the design currently cannot.** Fork the correct arm's SET cache (steered reply retained, as CLEAR does)
through the delay and issue the HOLD cue-absent prompt with the hook OFF. If the trunk carries the selection in
its own steered KV, HOLD succeeds without the signal; if not, the FOCUS-2 controller must re-emit continuously.
This is the mirror of CLEAR on an ambiguous query instead of an explicit copy query, costs ~64 generations
(~3 min), and is exactly the number FOCUS-2's recurrence-vs-latch decision needs. Descriptive only; no gate.

**F3 (low) — content-freeness is sound.** Extraction (line 1582) captures the final prompt token, which is the
same chat-wrapper token in the A/B/no-cue contexts, on identical operand lists; the vector therefore encodes
"the cue was present" and nothing about operands or answers. Test operands are fresh and disjoint (unordered-set
rejection, line 1575). Transplant carries only the enum (line 1593). No answers, exemplars, echo, or pin. Good.

**F4 (medium) — ambiguity: what exactly is in each decision's KV.** "Canonical cue-free neutral-prefix KV ...
earlier generated answers are excluded" (line 1591) does not say whether earlier *prompts* (with operands) are
included, or whether SET's context lacks the delay text while HOLD's has it. Unanswered user turns in the chat
template would be an odd context. Conservative reading, which the harness should freeze: SET/SWITCH context =
[chat wrapper][cue-absent prompt]; HOLD/BACK context = [chat wrapper][128 neutral tokens as a user or system
turn][cue-absent prompt]; no earlier prompts or replies anywhere. Record the exact token layout and hash it.

**F5 (medium) — shuffled control is nearly vacuous; the real control is the within-episode A/B contrast.** A
Gaussian direction in d_model=2048 rescaled to rho is almost orthogonal to everything and will behave like OFF.
R_i requires the shuffled arm to complete a four-answer schedule containing *both* directions (line 1607), which
no fixed default can do, so sum(R)=0 is essentially guaranteed. That is acceptable as a dose-matched safety
check, but it does not "reject trivial explanations" — the swapped arm does that, because W_i requires the
opposite-address schedule (both directions) on the same operands. Do not describe shuffled as the control that
rules out "any perturbation sorts". Optional, more informative substitute at equal cost: inject the shared
component (u_A+u_B)/2, which reveals how much of the effect is "sort-ness" versus the A/B differential.
Either way, no PASS/FAIL consequence.

**F6 (medium) — CLEAR is sound and non-vacuous in state, but weak in challenge; KEEP's floor gates on the wrong
quantity.** Mechanism check: the hook adds at layer-L input, so K/V at layers >= L for the hooked positions (final
prompt token + every generated token of BACK) are contaminated and stay in the forked cache (qwen3.py:421-422;
KVCache appends post-RoPE K/V). Layers < L will show exactly zero delta, layers >= L nonzero: the every-layer
audit (line 1601) is therefore guaranteed non-vacuous and should be read that way. But the contamination is ~30
positions of one reply in a ~300-token context; behavioural imposition from that residue is implausible, so
CLEAR will almost surely pass whenever copy competence holds. The KEEP arm (line 1597: old address and dose
remain, i.e. hook ON during the copy query) measures *active override of an explicit instruction*, a different
mechanism from residual-KV carry-over. Requiring KEEP impositions >= 8/64 (line 1608) and >= 4/32 per task in
selection (line 1585) makes PASS depend on the dose being strong enough to defeat "Copy these integers in exactly
the given order", which is unrelated to whether the actuator sets/switches/releases. A working selector can
FAIL-ACTUATOR or FAIL solely because the copy instruction is robust. Fix: keep KEEP as the reported
active-interference reference and the residual audit as the non-vacuity certificate; remove the KEEP floors from
the PASS gate and from cell eligibility; if KEEP imposes on < 8/64, label the CLEAR family "CLEAR-UNCHALLENGED"
in the report rather than FAIL. Replacement text in Section 7.

**F7 (medium) — clean replay inside C_i lets text history, not the actuator, fail CLEAR.** C_i (line 1608)
requires the clean replay to copy exactly too. The replay conditions on the same token history with OFF from
an empty cache, so a replay failure means the *text* (a sorted answer sitting in context) induced sorting on a
copy query — an in-context effect that has nothing to do with residual KV or the actuator. The draft itself says
the replay "may not replace the retained-KV result" (line 1600) yet makes it a conjunct. Combine with F10 below.

## 2. VALIDITY

**F8 (HIGH) — the CLEAR floor 63/64 is likely unreachable under the registered competence gate.** The copy
competence gate is >= 31/32 complete two-query pairs (line 1570), i.e. per-pair success >= 0.969. C_i is a
conjunction of four exact copies (CLEAR pair AND replay pair). Recomputed: if CLEAR and replay are perfectly
correlated (no residual effect), P(sum(C) >= 63 | q=31/32) = 0.402; if independent, 0.089; even at q=0.99 the
correlated case is 0.865. A perfectly clearing actuator therefore fails the CLEAR floor with probability 0.13-0.91
depending on the copy rate the gate permits. This is a way to FAIL without the actuator being at fault and
mostly measures copy competence. Fix (Section 7): make the endpoint the *residual-KV harm count* — CLEAR fails a
query while its clean replay succeeds on that query — which the design already measures per query, require
harm <= 1/64 with the exact lower-tail Binomial(64,0.10) test (P(X<=1)=0.00956 <= 1/60, recomputed), keep zero
old-task impositions as a hard safety floor, and report sum(C) descriptively. This removes copy competence from
the endpoint and makes the replay the matched baseline it was built to be.

**F9 (HIGH) — control-arm breakage can kill the run, and OFF cue-absent output is never exercised before test.**
Line 1615: "Require <= 1/64 in EVERY arm ... stop as soon as an arm's second broken episode makes PASS
impossible". The OFF and shuffled arms answer "Process these integers. Output only a JSON array." with no task;
prose, an empty array, or a non-integer array is I-breakage; a runaway is T-breakage. Two such OFF episodes end
the experiment as FAIL/INCOMPLETE having measured nothing about the actuator. Setup never runs the OFF cue-absent
prompt (line 1585 lists cue-absent sorts per task, CLEAR/replay, KEEP; line 1570 runs cue-visible sorts and
neutral copies), so this is a genuine unknown at test time. Note also that OFF breakage counts O_i=0, inflating
S-O. Fix: (a) add to the competence gate a schema-compliance check for the OFF cue-absent prompt on the 32 setup
episodes (>= 31/32 valid integer arrays of the right length; correctness not required), 64 extra generations;
(b) restrict the breakage *stop rule* to intervention arms (correct, swapped, transplant, CLEAR, KEEP, replay);
for OFF and shuffled report breakage and treat a broken reply as failure (O_i=V_i=R_i=0). Section 7 text.

**F10 (medium) — OFF's default direction can coincide with one address; report and label per stratum.** If the
trunk's default on the cue-absent prompt is ascending sort (plausible), then O_i=1 on the 32 initial-A episodes
and the SET family's net gain >= 16 must come entirely from initial-B episodes, while the >= 24/32 initial-A
stratum floor is satisfied by the default, not the actuator. The design's answer is the swapped arm and W_i (both
directions required), which is correct. Add to the SET reading: report OFF cue-absent success per stratum; if a
stratum's OFF success is >= 24/32, that stratum's SET evidence is "default-coincident" and the SET claim rests on
the other stratum and on W. No threshold change needed.

**F11 (low) — vacuous paired tests, floor-vs-test dominance; harmless but say so.** V_i (OFF completing a
four-answer schedule with both directions) is ~0 by construction, so "McNemar win over V, net >= 16" is
subsumed by sum(W) >= 48. For R: the exact test admits sum(R)=1 (P(X<=1)=0.00956 <= 1/60) but the floor
requires 0; the floor binds. For CLEAR: P(Bin(64,.9)>=62)=0.0389 > 1/60, so the floor 63 and the test coincide.
McNemar on net >= 16 only bites when c >= 17 (p at c=16: 0.01465; c=17: 0.01642; c=20: 0.02202). Record these
in the section so nobody reads them as independent evidence.

**F12 (low) — regression to the selection threshold.** A cell selected exactly at 24/32 cue-absent sorts (75%)
passes the 48/64 test floor with probability 0.567 (P(Bin(64,.75)>=48)); at a true 85% rate, 0.988. Expected
and acceptable for select-then-confirm; state it so a near-threshold FAIL is read as "underpowered at the
selected dose", not "no effect".

**Claim ceiling (line 1612):** correct in substance; needs the F1 sentence. "Controllability, not autonomous
focus" is the right ceiling. No clause lets a run PASS without the within-episode opposite-address contrast on
fresh operands, which is the question; good.

## 3. SKILLS / COMPETENCE

**F13 (medium) — asc/desc is an acceptable but minimal pair; competence gate is right; one addition.** Both are
demonstrably in a 1.7B instruct trunk, operand-sensitive, same output schema, and the design already forbids
sorted/reverse-sorted inputs so copy != A != B (line 1575). Weaknesses: (i) they are two settings of one
"sort" competency and their vectors will be highly collinear (report cos(u_A,u_B); expect > 0.8), so the A/B
differential is a small orthogonal component and a dose that carries "sort" may not carry "which way"; (ii) F10's
default coincidence. A pair with the same schema but genuinely different circuits — ascending sort vs. reverse
(copy in reverse order), or ascending sort vs. "the list with each element negated" — would give a cleaner
"select among distinct stored competencies" test and lower collinearity, at identical cost. I would keep asc/desc
for v1 only because astra's design source named it and it is the harder, more Miller-like case (same circuit,
different parameter); if the grid finds no eligible cell, the F13 pair is the natural v2 registration.
The 29/32 gate (0.90625 >= 0.9, recomputed) is right; add the F9(a) OFF schema check to it.

## 4. ACTUATOR / SELECTION

Sound. Mean-difference at the final prompt token on operand-paired triples is the standard function-vector
recipe and the reuse of `mean_difference` (fp32) and `make_residual_hook` (last-position add, returns None when
inert) is correct for this purpose (function_vectors.py:87-139). Common-norm rescaling rho_L is declared and
reported. First-eligible in (alpha, L) lexicographic order picks the *weakest* working dose, which is the right
bias given check 30's truncation failure at alpha 2.0/L12 on 512-token outputs; here max_new=64 and the vector
is normalised, so that failure mode is bounded and the <= 1/32 breakage eligibility catches it. Selection on
setup does not leak into test: test episodes are disjoint by seed and by operand set, and GPU stages never read
test inputs (lines 1576-1577). Selecting on the same criteria the test uses is ordinary select-then-confirm
(F12). Brittleness: one actuator/one dose is a deliberate screen; the honest outcome of a miss is FAIL-ACTUATOR
for this actuator, which the draft states. Two notes: (a) the eligibility order should be sort-rate -> breakage
-> CLEAR -> (KEEP, descriptive) with the cell abandoned at the first failed criterion, which cuts selection cost
by more than half in the typical case (F14); (b) sustained per-token injection is the one variant tested; a
prompt-position-only injection is more "transient" and less prone to runaway, but adding it doubles the grid —
leave it for a v2 registration if FAIL-ACTUATOR occurs, as the draft's "no expanded grid" rule requires.

## 5. COST / SIMPLICITY

**F14 (medium) — budget is feasible but the transplant arm is dead weight and selection ordering matters.**
Generation counts (recomputed): test = 64 x (5 arms x 4 decisions) + 64 x (2 CLEAR + 2 KEEP + 2 replay) = 1664;
competence = 128; extraction = 192 prefills; selection = 448 generations per cell (32 x 2 tasks x (1 sort + 2 CLEAR
+ 2 KEEP + 2 replay)), worst case 9 cells = 4032; worst-case total ~5,800 generations (+ ~200 with F9(a)).
At 2-4 s per generation (prefill ~200-350 tokens + ~25-35 decoded tokens, batch 1, custom Qwen3 forward) that is
3.2-6.5 h — inside the 21,600 s cap (6 x 3600, recomputed) only with the projection rule doing real work.
Cuts that lose nothing: (1) the transplant arm on test is the swapped arm's enum re-applied to the same cloned
KV with greedy decoding; under the determinism the design itself asserts via the own-state sham (line 1593), its
tokens are identical to swapped's, so W_i = swapped. Replace it with a determinism assertion (swapped and
transplant tokens equal on the 32 setup episodes; any mismatch is INVALID) and drop it from test: -256
generations. (2) Short-circuit cell eligibility (Section 4a): typically -1,500 to -3,000 generations.
(3) Shuffled could be reduced to a 16-episode descriptive arm (F5), -192 generations; optional.
Everything else in the harness brief is proportionate; the budget/projection/deadline machinery is the
minimum the protocol requires. The FOCUS-2 sketch is correctly quarantined.

## 6. Recomputed closed forms (scratchpad pytest, pure Python)

| quantity | draft | recomputed |
|---|---|---|
| alpha_f = 0.05/3 | 1/60 | 0.016667 |
| P(Bin(64,.90) >= 63) | 0.00956314971305463 | 0.009563149713054641 (match) |
| P(Bin(64,.90) >= 62) | — | 0.038908 (> 1/60; floor 63 and test coincide) |
| P(Bin(64,.10) = 0) | 0.0011790184577738583 | 0.0011790184577738603 (match) |
| P(Bin(64,.10) <= 1) | — | 0.009563 (<= 1/60; test admits R=1, floor binds) |
| McNemar b=8,c=0 | 1/256 | 0.00390625 (match); b=6,c=0: 0.015625 (smallest passing b at c=0) |
| 29/32 | 90.625% | 0.90625 (match); 28/32 = 0.875 fails |
| 6 GPU-h | 21,600 s | 21,600 (match) |
| P(sum(C)>=63) under q=31/32, correlated / independent | — | 0.402 / 0.089 (F8) |
| P(Bin(64,.75)>=48) / P(Bin(64,.85)>=48) | — | 0.567 / 0.988 (F12) |
| McNemar at net 16, c = 0/8/16/17/20 | — | 1.5e-5 / 0.0035 / 0.01465 / 0.01642 / 0.02202 |
| generations: test / competence / per-cell / 9 cells / worst total | — | 1664 / 128 / 448 / 4032 / 5824 |

## 7. Replacement text

R-F8/F7 (replace the C_i sentence and the CLEAR requirement at line 1608):
> C_i = retained-KV CLEAR copies both neutral lists exactly; P_i = its clean replay copies both exactly;
> H_i = CLEAR fails on at least one query on which its clean replay succeeds (residual-KV harm); K_i = KEEP copies
> both exactly. CLEAR requires sum(H) <= 1 with exact lower-tail Binomial(64,0.10) p <= alpha_f (P(X<=1) =
> 0.009563), ZERO old-task impositions after CLEAR, and nonzero hook-event counters and nonzero layer >= L K/V
> deltas in every episode. Report sum(C), sum(P), sum(K), KEEP impositions and the paired C-vs-K table
> descriptively. If KEEP imposes the old task on fewer than 8/64 episodes, the CLEAR family is reported as
> CLEAR-UNCHALLENGED (release established against residual KV only, not against active interference); this is
> not a FAIL.

R-F6 (line 1585, cell eligibility): delete ">=4/32 KEEP old-task impositions per task;" and append: "Evaluate
criteria in the order cue-absent sort rate, breakage, CLEAR/replay; abandon a cell at its first failed criterion;
KEEP is run only on eligible cells and reported."

R-F9 (line 1570, competence): append "and >=31/32 schema-valid replies (integer array of the query length) to
the cue-absent prompt with OFF on the same setup episodes; correctness is not required and is reported per task."
(line 1615, breakage): replace "Require <=1/64 in EVERY arm" with "Require <=1/64 in every intervention arm
(correct, swapped, transplant, CLEAR, KEEP, replay); report OFF/shuffled breakage and score a broken control reply
as failure (O_i=V_i=R_i=0) without stopping."

R-F1 (line 1612, claim ceiling): append "All four sorting decisions are independent forward passes given the
enum; the signal is sustained during each answer and absent between answers. No within-trunk persistence of the
selection is tested or claimed; HOLD and BACK certify actuator robustness to a neutral 128-token prefix only."

R-F14 (line 1592/1606): "Four arms at every sorting decision: correct, swapped, shuffled, OFF. Transplant is
certified on setup only: the opposite-task donor's enum applied at the matched phase must reproduce the swapped
arm's tokens bitwise on all 32 setup episodes, and the own-state sham must reproduce the correct arm's; any
mismatch is INVALID." and "W_i = swapped arm completes all four DONOR-target answers".

R-F10 (line 1605, SET reading): append "Report OFF cue-absent success per stratum; a stratum whose OFF success
is >=24/32 is labelled default-coincident and contributes no SET evidence beyond W."

R-F4 (line 1591): append "Context layout is frozen and hashed: SET/SWITCH = [chat wrapper][cue-absent prompt];
HOLD/BACK = [chat wrapper][128 neutral tokens][cue-absent prompt]; no earlier prompt or reply in any decision's
context."

Optional R-F2 (new sentence after line 1597): "Descriptive transient-hold arm: fork the correct arm's SET cache
(steered reply retained) through the delay and issue the HOLD prompt with the hook OFF; report exact-sort rate;
no gate."

## 8. Open items for the ledger

- F8, F9 must close before registration (HIGH). F1/F4/F6/F7/F10/F13/F14 are wording/cost fixes (medium).
- Unverified here (needs the tokenizer, not a model): that 128 tokens of the repeated neutral sentence fall on a
  clean truncation and that the chat wrapper's final token is identical across the A/B/no-cue extraction
  contexts (it is by construction of the fixed template, but hash it in the manifest).
- No repo file other than this review was written; no process launched beyond the CPU pytest recomputation.
