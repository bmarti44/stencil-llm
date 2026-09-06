# FOCUS-3 v8 diagnostic — one-round accuracy review (fable, 2026-09-06)

Scope: `results/quick-checks/focus3-gate/diag/` at commits 9f99c130..1e16ec95 (runtime v8: relation-v2 seed0, admission ft-v3 seed0, all v8 rules; 64 gate episodes x arms C/C'/O/N/T). Status is DIAGNOSTIC (v8 eligibility stop unmet; no PASS/FAIL label). CPU-only review; no model launched; no sealed input read. Every number below was recomputed from the 1920 raw gate records, the 220 probe records, `false-admission-effects.json`, and `v4/bank.json` with my own code (no import of the runtime); the only files I wrote are scratch files and this review.

## 1. Verification of the claimed counts

**All headline and per-family counts reproduce exactly.** Pooled (64): C exact 38, stale 7, final 57, false retirement 8, false admission 21 episodes / 25 rows, breakage 0, contradictory 5; C' 32/6/58/14/21/0/5; O 64/2/63/0/-/0/0; N stale 33 final 29 breakage 1; T stale 32 final 31. All four family tables in RESULTS.md match my recount row for row.

**Scoring is not inflated.** I re-scored all 1920 generations from raw `generation.text`, `eos` and `output_ids` with an independent parser (strict `{answer,tag}` schema, int-typed, target = payload sorted asc/desc or identity for `default`, stale = matches any listed stale direction on a post-change turn, repetition check): 0 mismatches against the stored `score` fields. Register agreement (`exact`, `false_retirement`) recomputed from `live` vs `gold_live` sets: 0 mismatches. Final success uses the last sort-kind turn (turn 5), never the prose turn 4, so the `{}` prose replies (e.g. gate_0_04 turn 4) do not count for or against any arm. C's 57/64 is real.

**No gold leak in O prompts.** O's `trace` is empty for all 384 records (O receives gold events only). Its 640 rendered rows are exactly 544 gold event spans from the bank plus 96 renderer default rows ("Ordering: return the list in the given order."), and C renders the same default row (99 times) — the default is a renderer property, not oracle knowledge. Decoding all 384 O prompts with the Qwen3 tokenizer: the rendered request is present verbatim as the final user content in every prompt; the expected answer list appears in the prompt only on the 96 `default`-direction turns, where the expected answer *is* the payload quoted in the user request itself — 0 hits on the 224 ascending/descending turns. No answer strings or gold answers are in any rendered row.

**Probe methodology spot-check.** All 220 probe records exist; for every C probe the rendered row-set differs from the original by exactly the removed row and the prior-history token prefix is the original (diff of decoded prompts = the recap line only). The probe effect totals reproduce: 110 exposed row-turns, 35 unexposed (never-rendered rows = 0), 11 semantic/text/token changes, 9 score changes, 7 rows with any semantic effect, success F->T 5 / T->F 3, stale F->T 1 / T->F 4, admission-turn 2/25 vs later 9/85. All 11 semantic changes come from payload-request rows; quote rows 0/10 (see caveat in section 3).

**Freeze ordering.** Freeze commit 6041e2d7 (06:10:12 local) precedes `started.json` (06:10:21); `freeze.json` hashes were computed before the commit. Setup-runtime parity 96/96 vs the committed v8 CPU traces is recorded.

**Small definitional point (not an error).** C' carries 7 additional spurious live rows ("Switch to task G3nXB.") created by its 7 unauthorized supersedes in switch-and-return. RESULTS counts these under unauthorized supersedes / false retirements (14/64) and not under "false admission" (21/64, identical to C). That is consistent with the action-label definition, but a reader should know C' renders 32 spurious rows in 28 episodes, not 25 in 21.

## 2. Paired contrasts (descriptive, exact two-sided McNemar on 64 paired episodes)

| Pair | Endpoint | C-only | ref-only | diff | exact p |
|---|---|---:|---:|---:|---:|
| C vs O | stale | 5 | 0 | +5 | 0.063 |
| C vs O | final success | 0 | 6 | -6 | 0.031 |
| C vs T | stale | 4 | 29 | -25 | 1.1e-05 |
| C vs T | final success | 30 | 4 | +26 | 6.2e-06 |
| C vs N | stale | 3 | 29 | -26 | 2.6e-06 |
| C vs N | final success | 31 | 3 | +28 | 7.7e-07 |
| C vs C' | any | <=1 | <=1 | 0/+-1 | 1.0 |

These are descriptive on a single synthetic seed; the registration forbids superiority labels and I make none. The C-vs-O deficit is concentrated entirely in override (4 episodes) and cancel (2 episodes); O is never worse than C on any episode.

**N/T baselines are consistent with the prior FOCUS-3 v2 gate** (seed 30301, same bank generator): N final 25 / stale 38, T final 31 / stale 32 there vs N 29/33, T 31/32 here. They are also structurally consistent with FOCUS-2d/check 42 in the sense that the no-register arm is ~0/16 on cancel and complete-and-move-on (FOCUS-2d "neither" CLEAR success 0/58 in the both-correct stratum), but the FOCUS-2d/check 42 arms are a different bank, different checkpoints, and their "text-restate" (176/256) restates the *current* rule, whereas T here restates *all* prior rules including retired ones, which is stale by construction on cancel/complete. So "roughly doubles the naive baselines" is a fair reading of this bank against N and T, not a cross-program comparison.

## 3. Where C's misses actually come from (per-episode tracing)

C's 26 non-exact episodes decompose exactly into: 21 with at least one false admission, 4 override episodes with a missed supersede, and 1 (gate_3_15) with a missed gold admission.

**Stale executions (7):**
- gate_0_02, 0_06, 0_10, 0_14 (override): the gold "Replace the sorting rule..." supersede was proposed as `none`; P(supersedes) = .253/.510/.307/.383 against C's .90 threshold. No false admission in these episodes. C' (.50) catches only gate_0_06 (.510) and the other three stay stale/failed.
- gate_1_00 (cancel): false-admitted payload row 0:151 rendered at turns 2/3/5; the probe shows that removing it repairs task, stale and success at all three turns — a probe-proven false-admission effect. (O is also stale at one turn in this episode but recovers by turn 5.)
- gate_1_04 (cancel): the cancel was applied correctly to 0:91, yet turns 2/3/5 sort ascending. Mechanism visible in the register: gold_live renders the default "return in given order" row; C does not, because two spurious sort-kind rows (payload row 0:163 scope *, and the "Inert training context..." quote row 1:0 scope G1n4A) occupy the ordering slot and suppress the default. This is the only episode where C lacks a default row that gold renders. Neither single-row probe changes the answer because removing one spurious row leaves the other, and no probe re-derives defaults (0 of 110 probes rendered a default the original lacked). So this stale/failed episode is plausibly attributable to the false admissions jointly, but it is unmeasured by design — the report's "7 of 25 rows changed an answer" and "quotes 0/10" undercount this joint/indirect channel. Flag, not a finding against the run.
- gate_2_09 (complete): C and O are both stale at turn 2 (O stale 2/64 includes this one); the probe shows removing false row 0:148 un-stales C's turn 2. Both arms succeed at turn 5.

**Final failures (7):** the 4 override supersede misses; gate_1_00 and gate_1_04 as above (false-admission linked); gate_2_03 (complete), where C is register-exact and every arm including O emits the same wrong list — model competence, not register.

So: 4/7 stale and 4/7 final failures are relation (supersedes) misses; 2/7 and 2/7 trace to false admissions (one probe-proven, one mechanistically evident but unprobed); 1 stale is shared with O and 1 final failure is shared with O.

**False retirements (8):** 4 override supersede misses (the superseded rule stays live, the replacement is never admitted); gate_1_04 (default-row suppression, false-admission linked); gate_3_05, 3_13, 3_15 (switch-and-return): the new task's gold rule ("For task G3nXB, the payload must be in ascending order until I say otherwise." / "...always sort...") was *not admitted*, P(rule) = .214/.360/.054 against .95. These are admission false *negatives* — a different failure than the 21 false positives — and are invisible in final success (16/16) because the rule sits in the same user message as the request.

**Contradictory recaps (5):** gate_1_04, 2_01, 2_09, 3_05, 3_13 — every one involves a spurious row sharing a semantic key with a legitimate row; none would exist without the false admissions. The two unauthorized "completes" (2_01, 2_09) target a spurious row 1:0 and are also consequences of false admission.

**False-admission profile:** 25 rows, all P(rule) in [.9507, .9823] (median .9647) — marginal exceedances of the .95 threshold, 20 one-shot payload requests ("Sort request for task X: payload [...]") and 5 inert quotes. Identical sets in C and C'. All 11 semantic probe changes are payload rows; net effect on success across 110 row-turns is 5 repaired vs 3 lost when the row is removed.

## 4. Plain readings

**(a) Honest end-to-end reading.** On this single synthetic cohort the classifier-driven register recovers most of the oracle's benefit (final 57 vs 63; stale 7 vs 2; register-exact 38 vs 64; O never beats C on breakage) and roughly doubles the two naive baselines (N 29, T 31) on final success while cutting stale executions by ~25 episodes. The cost is 25 spurious rows in 21 episodes that only sometimes change behaviour (7 rows with any probed effect; the probe design cannot see joint effects like gate_1_04). The register's remaining deficit is not mainly false admissions: 4 of 5 C-only stale episodes and 4 of 6 O-only successes are supersede misses in override.

**(b) Distance from a registered PASS (v3 readings).** Requirements and C's readings: register-exact >=48/64 — 38 (short by 10), and >=12/16 per family — override 6, cancel 11, complete 10, switch 11 (all four short); C/O stale distance <=4 — 5 (short by 1); C/O final-success distance <=4 — 6 (short by 2); false retirements <=2 — 8 (short by 6); breakage <=2 — 0 (met); C stale < T stale — 7 < 32 (met); zero contradictory recaps — 5 (not met); all gate records — 1920/1920 (met). Four of nine terms fail; three of the four are driven by more than one failure mode.

**(c) Are the false admissions the check-44 families, and would fixing admission alone reach PASS?** Yes on the first: all 25 spurious rows are exactly the two families check 44's GO bar names (gold-empty one-off payload items and quoted/reported items, each <=3%). On the second: no, on this evidence. A counterfactual that deletes every spurious row and changes nothing else (not causal — the histories would differ) would give register-exact <=56/64 (override <=12, cancel <=16, complete <=15, switch <=13), contradictory 0, stale distance 4 and final distance 4 (both at the boundary, assuming gate_1_00 and gate_1_04 repair), but false retirements would remain 7/64 (>2): 4 supersede misses at P(supersedes) .25–.51 under the .90 threshold plus 3 gold-rule admission misses at P(rule) .05–.36 in switch-and-return. Lowering the supersede threshold (C') buys one episode and costs 7 unauthorized supersedes. So PASS needs three things: the check-44 false-positive fix, supersede recall on "Replace the sorting rule..." phrasing, and admission recall on "for task X, ... until I say otherwise" phrasing. Check 44 currently stands INVALID/INCOMPLETE (preflight assertion, zero held-out predictions), so it provides no evidence yet on the first.

**(d) Overclaims to avoid.** Single seed (30322), single relation/admission seed (seed0), one synthetic bank from reused development templates — no population inference. McNemar p-values here are descriptive and the registration forbids superiority labels. The probe estimand is the immediate effect of one rendered row given the polluted history; it does not measure the total effect of never admitting, and it structurally cannot see joint suppression of default rows (gate_1_04). "False admission 21/64" counts admit actions only; C' has 7 further spurious rows via supersedes. The v8 eligibility stop is still unmet; nothing here upgrades the diagnostic to a gate result, and the register-exact 38 should not be read as "59% correct registers" in any shipping sense. N/T comparability to FOCUS-2d/check 42 is qualitative only (different bank, different T semantics).

## 5. Verdict on the report

RESULTS.md, summary.json, false-admissions.md and the effects file are accurate to the raw records in every count I could recompute; the leak, scoring and probe-construction checks pass. The one substantive addition a reader needs is section 3's attribution: the classifier register's remaining gap to O is mostly supersede recall, the false retirements include three admission false negatives, and the false-admission cost is understated for the joint/default-suppression case. No open high/critical finding; the diagnostic label is the correct label.
