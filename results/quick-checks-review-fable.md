# Quick-checks review — fable (2026-09-02)

Scope: results/quick-checks/ at d9c6b79 (README, three scripts, two logs, three rows files), WORKLOG "quick checks"
entry, LEDGER-PLAN.md G0 PILOT v1 (441-477) and AMENDMENT v2 (479-552), results/qwen/ledger-kv-probe-h1p/ (20
sessions, meta, summary), scripts/ledger_kv_probe.py, scripts/g0_oracle.py, src/stencil/qwen3.py, scripts/bfcl_mt.py,
scripts/ledger_eval.py, data/b3/mt-train-300.jsonl (first 20 sessions, prompts only). CPU only; every number below
was recomputed from the rows/logs/records with plain python (scratchpad recompute.py / recompute2b.py); no model
was loaded, no process touched. I did not read results/quick-checks-review-kimi.md (independence).

## 0. Recompute summary (all README numbers reproduce)

| claim | README | recomputed | source |
|---|---|---|---|
| LOO AUROC mean-delta / per-token / max / sum+ / top3 / flips | 0.494 / 0.48 / 0.516 / 0.509 / 0.512 / 0.496 | identical | oracle_check_rows.json (63 keep, 103 control, 20 sessions) |
| keep-in AUROC utility / frac / top3 / flips_back | 0.518 / 0.517 / 0.630 / 0.601 | identical | oracle_check_keepin_rows.json |
| role totals full/evicted/finder/finder_ctrl/role/role_ctrl over 56 | 44/14/37/18/41/26 | identical | role_rule_rows.json + h1p summary.json |
| recovery (41-14)/(44-14) | 0.90 | 0.900 (finder 0.767) | |
| safety role trunc/degen; full | 1/1; 1/2 | 1/1; 1/2 (role_ctrl 0/2) | |
| role pins mean cols, fraction of evictable | 89, 20% | 88.6 (sum 1772/9008 = 19.7% pooled, 21.6% mean); finder 46.6 (10.3%) | |
| per session role vs finder +/-/= | +4/-1/=15 | 4/1/15 | |
| per session role vs full | +3/-5/=12 | 3/5/12 | |

Additional recomputed facts used below: role pins are a strict superset of the finder's pinned columns in every
session (932/932 finder columns inside role pins); the CPU re-derivation of the role pins from the H1' context ids
with ledger_kv_probe._user_turns/_token_span gives exactly the logged column counts in 20/20 sessions, with no
chat-control-token bleed; 1470/1772 (83%) of the role exact-column control columns lie inside PRIOR ASSISTANT turns;
7/20 sessions pin more than the registered B = 25% of evictable columns (s00 35.1%, s02 31.9%, s07 29.3%, s13 25.1%,
s15 28.3%, s16 25.4%, s17 27.8%); every pinned prior user turn (40/40 turn-2 prompts) contains the sentence "Every
earlier constraint from this conversation still applies to this reply as well."

## 1. Loss-delta oracle (Q1)

**Q1-a — MEDIUM. The leave-one-out readout is floor-saturated, so "no signal" is partly an instrument failure, not
only a property of the quantity measured.** oracle_check.py:44-47 uses reference = the FULL arm's own greedy tokens;
greedy tokens have p ≈ 1 under the unevicted cache, so NLL_full ≈ 0 (log: base 0.000 in 9/20 sessions, ≤ 0.014 in
16/20) and a one-span eviction can only move the loss when it flips an argmax. Recomputed: 44/166 utilities are
exactly 0 (13/63 keep, 31/103 control) and 119/166 are below 1e-3. The per-token readouts (max_delta, flips) do not
escape this: they are 0.50-0.52. This is the self-distillation compression kimi F2.3 predicted for the G0 chat arm,
observed live. The README's stated cause ("prior compliant assistant turns make each constraint sentence redundant")
is consistent with the data (see Q1-c) but is not what these numbers isolate; the numbers isolate a saturated
instrument on a redundant context.

**Q1-b — HIGH. The keep-one-in "weak signal" (top-3 AUROC 0.63, flips-back 0.60) is a span-length artefact and
should be reported as no signal.** Constraint spans are longer than the exact-column control fragments
(matched_control_spans, ledger_kv_probe.py:343-363, matches column MASS with nearest free columns, which splinters
into short runs): keep mean 14.8 tokens vs control 9.0; AUROC(length, keep > control) = 0.757; Spearman(top3,
length) = 0.51 over the 166 rows, Spearman(flips_back, length) = 0.50. Within length strata the effect vanishes:
top3 AUROC = 0.46 for spans of 8-15 tokens (28 keep / 29 control) and 0.46 for ≥ 16 tokens (28 / 21); mean utility
AUROC 0.36 and 0.43 in the same strata. The session-argmax keep-in span is a constraint in 12/20 sessions against a
38% base rate, which is what length alone predicts. Conclusion: neither loss readout separates standing-constraint
columns from adjacent assistant-turn columns on this probe; the README's "WEAK" is generous.

**Q1-c — LOW (wording).** "The loss oracle measures need-to-reproduce-content, not adherence to standing
constraints" is the right direction but overclaims what was tested. What the data support: (i) with a 96-token
self-greedy reference the loss oracle cannot rank constraint spans above their neighbours; (ii) the neighbours are
mostly compliant assistant text (83% of control columns), i.e. content that also carries the constraint's surface
form, so redundancy is a live explanation. What was not tested: whether a checker-outcome oracle would agree
(Q2 answers it — it does not: the role/finder arms recover 77-90% of the outcome gap while the loss oracle sees
nothing). Say: "on this probe the reference-conditioned NLL oracle has no discriminative signal for constraint
columns; checker outcomes do."

**Q1-d — Would a cheap fix rescue it? No; do not build one.** Full-length reference: mean full-arm length is 244
tokens (3/20 sessions ≤ 96), so the 96-token prefix does miss late-acting outcomes (postscript 4/56, length and
placeholder counts 18/56 are global) — but the saturation in Q1-a is independent of length; a 2.5x-cost run would
still be at the floor on the chat arm. Sampled or perturbed references trade saturation for reference noise and
add a degree of freedom. An outcome-level oracle (checker pass under eviction) is exactly what role_rule_check.py
already is, at ~6 min for 20 sessions x 2 arms — it is the cheap fix and it has been run. The registered G0 TOOL
arm (gold-call reference, argument-value tokens) is a different instrument that this check does not touch: gold
JSON tokens are not self-greedy, so the floor argument does not apply there. Burden-test verdict: demote the NLL
oracle to a diagnostic on the chat corpus; keep it only where the reference is gold.

## 2. ROLE RULE (Q2)

**Q2-a — Harness semantics reproduce (verified, no finding).** role_rule_check.py:21-31 takes `context_token_ids`
and `evict_range` from each H1' record, re-encodes and asserts identity (line 26), derives pins from
ledger_kv_probe._user_turns(context)[:-1] (prior user turns only) clipped to the evict range, builds the control with
the same matched_control_spans, runs P.run_arm with arm names "pinned"/"pinned_control", max_new 512, deadline 300
(the H1' meta values), scores with score_row_constraints on the same row (key*10+n_turns, last-turn
instruction_id_list/kwargs) and the same `scores[:n_aged]` slice, and uses P.is_degenerate. This is the H1' path
(ledger_kv_probe.py:667-675) line for line. _token_span is called with contained=False (finder path used
contained=True); I checked every pinned span for chat-control tokens and marker bleed on CPU: none. Pinned-column
counts in the log equal the CPU re-derivation in 20/20 sessions and `pinned_cols` equals for role and role_ctrl in
every row.

**Q2-b — LOW. Provenance drift between the compared arms.** The full/evicted/finder/finder_ctrl numbers are H1'
records generated under qwen3.py sha 5122ec…; the role arms ran under 81a0ab… (commits 39c8740, ad558aa, 4B trunk
generalisation). By inspection the 1.7B path is unchanged (hf_compatible = n_head*head_dim != d_model is False for
16x128 = 2048) and WORKLOG records the 1.7B bitwise fixture unchanged, but the quick check ran no parity anchor in
its own process. Any registered version of this arm must regenerate `full` in the same run and assert
generated_token_ids identical to the H1' record for at least one session (or run all four arms fresh).

**Q2-c — HIGH. The tested rule is not the proposed rule.** What ran: pin every prior user turn, no budget, no echo,
no protected prefix (b3 has no system prompt), no retrieval ranking. What the simplification registers: protected
prefix + pin prior user turns + retrieval ranking within budget + echo. Under the registered B = 25% (v2 item 3)
7/20 sessions exceed budget, so the ranking component is exercised in 35% of sessions and its output is unmeasured;
the echo component is unmeasured for user-turn text (H1' measured constraint-clause echo: pinned_echo 48 vs pinned
37, quoting 0.35 — echoing whole user turns is a larger, untested intervention). "41/56" is evidence for the
unbudgeted pin-all-user-turns arm only.

**Q2-d — HIGH. The control is not fair in the direction the README implies, and the margin over control is
smaller than the finder's.** Role margin over its exact-column control is +15 (41-26); finder's is +19 (37-18).
Paired per-session (rate difference, session-bootstrap 2000 draws, seed 0, same estimator as H1'):
role - role_ctrl mean 0.283 [0.125, 0.442]; finder - finder_ctrl 0.342 [0.167, 0.508]; the difference of the two
margins is -0.058 [-0.175, 0.058]. Role vs finder head-to-head: mean +0.0625 per session [-0.017, 0.154], sign test
4 wins / 1 loss p = 0.375. The role rule is NOT distinguishable from the finder on 20 sessions. Two structural
reasons the controls are incomparable: (i) 83% of the role control columns are prior ASSISTANT turns, which are
the model's own compliant outputs and carry the constraints' surface form (caps, lowercase, bullets, keyword use);
that control scores 26 vs evicted 14 (+12), whereas the finder's control scores 18 (+4). A control that itself
recovers 40% of the gap is content-bearing, not a noise floor. (ii) At 100% of the user-role pool there is no
same-role control possible (v2 item 4 / sol G0R-6 require same-role, token-matched controls), so the role rule as
tested has no valid null.

**Q2-e — Does the higher budget alone explain the gain? Undetermined; the exact control that settles it.** The role
pins are a strict superset of the finder pins at 1.9x the columns (1772 vs 932). Register and run, on the same 20
sessions with the same harness, ONE arm: **RB = role-at-finder-budget** — within each session keep only the
finder's `pinned_cols` count of user-turn columns, chosen by a parameter-free rule fixed in advance (most recent
prior-user-turn columns first, whole tokens, no finder involvement), with its exact-column control. Readout:
paired per-session RB - finder with the session bootstrap. If RB ≈ 41 the role content wins at equal budget; if RB
≈ 37 or lower the +4 is budget. Optionally the mirror arm **FB = finder-at-role-budget** (finder spans plus the
most recent non-finder user-turn columns up to the role count) distinguishes "more user text" from "any more
columns"; RB alone answers the brief's question. Cost: 2 arms x 20 sessions ≈ 6 min GPU, same as the quick check.

**Q2-f — LOW.** Session s03: role arm truncated AND degenerate (rep4 > 0.5) yet scored 2/2 aged passes; H1' counts
passes on degenerate outputs too, so the comparison is consistent, but the registered safety table
(summarize_records, ledger_kv_probe.py:533-552) is what must be reported, not "safety within the integer clause".
Role: truncations 1 ≤ full 1 + 1, degenerate 1 ≤ full 2 — passes; role_ctrl degenerate 2 ≤ 2 — passes.

## 3. Proposed simplification (Q3) — burden test

**What is lost by cutting the G0 loss-oracle pilot.** (1) The only registered measurement on the TOOL corpus,
where the finder is known to fail (1/23 recall on BFCL labels) and the role rule's tool-dialogue behaviour (pin all
user turns; tool outputs and prior assistant calls evicted; schemas protected) is completely untested — b3 has no
tool turns. Q1's floor argument does not apply to gold-call references, so the tool arm may well be informative.
(2) The only planned OUTCOME SELECTION on data/g0. Amendment v2 item 0 (LEDGER-PLAN.md:482-489) restricts G0
outcome selection to the frozen data/g0 subsets; choosing (a) over (b)/(c) on the b3 quick check is outcome
selection on a development corpus built from the IFEval taxonomy. Cutting the pilot therefore does not merely
drop a diagnostic; it moves policy selection onto b3 and makes b3 a selection set (Q4). (3) Nothing else: the chat
NLL arm is predicted uninformative (Q1-a, kimi F2.3), and the registered signal test (v2 item 5) would say so at
higher cost.

**What survives the burden test.** Demote the chat-corpus NLL oracle to a reported diagnostic (no gate). Keep a
TOOL-corpus measurement, but make it outcome-level and joint-eviction, which is cheaper and matches Q1-d: on the
frozen data/g0 tool subset, run full / evicted / role / role-control (same-role, token-matched, v2 item 4) at
B = 25% and score gold-call argument-value exact match (the v2 item 7 primary). That is the H1' harness with a
different scorer; it needs no ranker, no null p90 machinery, no 12x12 matrix. Register RB (Q2-e) on b3 as the
budget control. Then the post-development evaluations (Multi-IF 909, BFCL after the prefix fix).

**Harness preconditions the simplification depends on, not yet true in code.** scripts/bfcl_mt.py:339 still
evicts from column 0 (`cache.evict(0, drop_end, keep=clipped)`) — the CRITICAL from
results/agentic-salience-review-fable.md F1 is unfixed; no BFCL arm may run before it is. scripts/ledger_eval.py
(the "text_ledger runner") has no eviction at all: its arms re-append ledger text to a FULL context (docstring
lines 3-10), so a role-rule run there measures echo-on-full-context (the H1' full_echo analogue, +2/56), not
retention through eviction. Registering "Multi-IF 909 via the text_ledger runner" as the role-rule evaluation
would test the wrong intervention unless an eviction arm is added or the claim is narrowed to echo.

**Miller-inspired or plain engineering?** Plain engineering, and say so. The rule is a write-time, role-tagged
retention policy: no read-time selection, no anticipation, no item-level competition, no clearing — none of the
properties the synthesis lists for Miller (results/research-generalizing-synthesis.md:25-28). The one read-time
component (retrieval ranking within budget) was not exercised in the quick check. The synthesis itself already
requires "Miller-inspired engineering, not evidence for the theory" for the full G0/G1 program; for the role rule
even "inspired" is a stretch. The claim text must not cite Miller; the deployment mechanism (KV pin through
eviction + verbatim echo) is what is being evaluated.

## 4. Leakage / lineage (Q4)

**Q4-a — HIGH. The role rule is now selected on three development sets, and the proposal would register it
without any data/g0 contact.** Timeline from git: v2 amendment 18:05 (06fd8da) forbids benchmark-derived changes
to "policy eligibility, budget, renderer, or tie-breaks" and restricts outcome selection to data/g0; the quick
checks landed 18:46 (d9c6b79) and the WORKLOG reading picks (a) on their basis. Policy (a) was on the menu before
(v1 line 464, synthesis line 45), so the menu is not newly leaked; the CHOICE among (a)/(b)/(c) is. Lineage of the
choice: (i) role protection of schemas came from the BFCL column-0 harness bug (synthesis :23-24; sol G0R-1);
(ii) "pin all prior user turns" was preferred over BM25 after the b3 coverage check (0.37 vs 0.13) and over the
finder after H1'/this check on b3; (iii) Multi-IF/BFCL error analyses shaped the segmenter and the eligible
family (v2 item 0). Consequence, stated precisely: Multi-IF and BFCL are DEVELOPMENT sets for the role rule — any
result on them is a post-development evaluation whose numbers may be reported but may not change B, the ranking
rule, the echo renderer, the protected-prefix definition, or the decision to keep the rule; b3/S2 are now
SELECTION sets (the policy was picked on their outcomes) and are evidence for nothing beyond "the rule was chosen
here". If the orchestrator proceeds without data/g0, the registration must say the selector was chosen on b3 and
v2 item 0's "restricted to the frozen data/g0 subsets" must be amended explicitly (a v3), not silently bypassed.

**Q4-b — What the no-contact family must satisfy.** (1) Never read, tokenised, summarised, or scored by any agent
or script in this repo (grep the WORKLOG/ledger/results for its name before naming it; the name is written to
LEDGER-PLAN before any file is fetched; sha256 of the fetched files recorded on first contact). (2) No shared
instruction taxonomy or checker code with IFEval/IFBench/Multi-IF/b3 (the vendored IFEval checkers must not be
its scorer), and no shared tool schemas or gold trajectories with BFCL/APIGen/ToolACE. (3) Zero 8-gram overlap
with data/b3, data/bench, data/g0 (the v2 item 1 content test extended). (4) The rule frozen BEFORE opening it:
B, ranking rule, echo renderer, protected-prefix definition, degeneracy definition, safety table, all by hash.
(5) One opening, one run, arms and floors registered; no re-run after a look. (6) Ideally a different surface
form of standing constraints (persona, policy, schema drift) so that "pin user turns" is not trivially aligned
with where the benchmark author put the instructions — on b3 and Multi-IF every constraint lives in a user turn
by construction, which is the strongest reason the rule looks good and the weakest basis for generality.

**Q4-c — New leakage in the quick-check scripts: none found.** oracle_check.py, oracle_check_keepin.py,
role_rule_check.py read only results/qwen/ledger-kv-probe-h1p/ and data/b3/mt-train-300.jsonl; no data/bench,
Multi-IF, BFCL, or b4-multiif path (grep clean). The checker labels (instruction_id_list/kwargs) are used only to
score, exactly as H1'. Two lineage notes, not leaks: the role check reuses H1' arms across a qwen3.py change
(Q2-b), and both oracle checks reuse the H1' FULL arm's tokens as reference, i.e. the "reference" was generated by
the same greedy path the arms are scored on (self-distillation, disclosed in kimi F2.3).

## 5. Findings index

| id | sev | file:line | one line |
|---|---|---|---|
| Q1-a | MEDIUM | results/quick-checks/oracle_check.py:44-47, oracle_check_loo.log | LOO readout floor-saturated (44/166 exact zeros, 119/166 < 1e-3); "no signal" is partly instrument |
| Q1-b | HIGH | oracle_check_keepin.py:44-52; ledger_kv_probe.py:343-363 | keep-in 0.63/0.60 is span-length confound (length AUROC 0.757; within-stratum 0.46) — report as no signal |
| Q1-c | LOW | results/quick-checks/README.md:16-17 | narrow the conclusion to what was measured |
| Q2-b | LOW | role_rule_check.py:14; meta.json qwen3.py sha | arms compared across a qwen3.py change without an in-run parity anchor |
| Q2-c | HIGH | role_rule_check.py:27-33; LEDGER-PLAN.md:504 | tested rule is unbudgeted pin-all-user-turns (7/20 over B), no echo, no ranking — not the proposed rule |
| Q2-d | HIGH | role_rule.log TOTALS; ledger_kv_probe.py:343 | margin over control +15 < finder +19; role vs finder CI [-0.017, 0.154], p = 0.375; control is 83% assistant text (+12 over evicted) |
| Q2-e | — | — | RB (role-at-finder-budget, recency ranking) settles the budget question |
| Q2-f | LOW | role_rule.log s03 | report the registered safety table, not a phrase |
| Q3 | HIGH | scripts/bfcl_mt.py:339; scripts/ledger_eval.py:3-10 | BFCL still evicts column 0; text_ledger runner has no eviction — the proposed evaluations test the wrong intervention as-is |
| Q4-a | HIGH | LEDGER-PLAN.md:482-489; WORKLOG.md:2443-2446 | policy choice made on b3 outcomes after v2 restricted selection to data/g0; b3 is now a selection set |

## VERDICT: ADOPT-WITH-FIXES

Adopt: demote the chat-corpus NLL oracle to a diagnostic; make the parameter-free role rule the candidate; treat
Multi-IF/BFCL as post-development evaluations; register a no-contact family for any zero-shot wording. Do not
adopt: (i) registering the rule on the strength of 41/56 (not distinguishable from the finder; unbudgeted; no
valid same-role control); (ii) cutting every data/g0 measurement (the tool corpus is the only place the rule's
tool-dialogue behaviour and the schema protection are tested, and the only place selection is not on a dev set);
(iii) "Miller-inspired" wording; (iv) the text_ledger runner or the unfixed BFCL harness as the evaluation harness.

## Registration text required (verbatim into LEDGER-PLAN.md as AMENDMENT v3; where it conflicts with v2, v3 governs)

1. Quick checks (results/quick-checks/, d9c6b79) are DEVELOPMENT evidence on data/b3. On their basis the
   reference-conditioned NLL oracle is DEMOTED to a reported diagnostic on the chat corpus (no gate, no selection
   role); its leave-one-out and keep-one-in readouts on b3 are recorded as no signal (keep-in top-3/flips-back are
   span-length confounds: length AUROC 0.757, within-stratum AUROC 0.46). The chat-corpus signal test of v2 item 5
   is withdrawn.
2. Candidate selector = ROLE RULE, defined exactly: (i) protected prefix = system turn + tool-schema block +
   columns 0-3, never evictable in any arm; (ii) the current user turn and the most recent 256 columns before it
   are never evictable (v2 item 10); (iii) budget B = 25% of the remaining evictable columns, computed identically
   in every harness; (iv) within B, pin whole prior USER turns (tool and assistant turns are never pinned), most
   recent first, whole tokens, truncating the oldest turn that does not fit; retrieval ranking is NOT part of the
   rule (it was never exercised and is withdrawn to avoid a free parameter); (v) echo = the pinned user-turn text
   rendered by the frozen render_text_ledger, appended before the final <|im_end|> exactly as echo_context
   (ledger_kv_probe.py:285-321); echo is a separately reported arm (role_echo), never merged into the role arm's
   number. The rule has no fitted parameters and no tie-breaks; its hash is the hash of the function implementing
   (i)-(v). Policies (b) recent+sinks and (c) BM25 are dropped from selection and recorded as not chosen on b3
   evidence (BM25 coverage 0.37 vs 0.13 random; recency 0.02).
3. Lineage (replaces v2 item 0's "restricted to the frozen data/g0 subsets"): the selector was CHOSEN on data/b3
   (mt-train-300, first 20 sessions: H1' records and results/quick-checks) after inspection of Multi-IF, BFCL V3,
   IFEval/IFBench and S2. data/b3 and S2 are SELECTION sets; Multi-IF 909 and BFCL V3 are DEVELOPMENT sets whose
   later results are post-development evaluations: they may be reported with clustered intervals and may not
   change any item of (2), the harness, the degeneracy definition, or the decision to retain the rule. The word
   "zero-shot" and any generality claim beyond "holds on the two development benchmark families it was designed
   around, on Qwen3-1.7B under this template, budget and cache intervention" are reserved for the no-contact
   family in (6). The rule is described as engineering; no Miller-derived claim is made for it.
4. Budget control on b3, BEFORE any gate run, same 20 H1' sessions, same harness (ledger_kv_probe.run_arm,
   max_new 512, deadline 300, score_row_constraints, scores[:n_aged]), regenerating `full` in-run and asserting its
   generated_token_ids identical to the H1' record for every session: arm RB = role-at-finder-budget (per session,
   the finder's pinned_cols count of user-turn columns, most recent first, whole tokens) with its exact-column
   control; arm ROLE_B = the rule of (2) at B = 25% with a same-role, token-matched random control drawn from the
   NON-pinned user-turn columns when any exist and otherwise reported as "no valid same-role control". Readouts:
   pooled aged passes for every arm; paired per-session rate differences RB - finder, ROLE_B - control, with the
   registered 2000-draw session bootstrap (seed 0); the registered safety table. Pre-stated reading: RB - finder
   lower bound > 0 → role content beats the finder at equal budget; otherwise the b3 advantage is attributed to
   budget and reported so. No number in this step alters (2).
5. Tool-corpus outcome check on the frozen data/g0 tool subset (MANIFEST sha re-verified), 30 dialogues, arms
   full / evicted / ROLE_B / same-role token-matched control at B, scored by gold-call argument-value exact match
   (primary) and whole-call match (secondary), joint eviction only, dialogue-clustered bootstrap; recovery =
   (ROLE_B - evicted)/(full - evicted) on pass counts. Registration floor for proceeding to (7): recovery ≥ 0.50
   with lower bound > 0 AND ROLE_B - control lower bound > 0 on the tool corpus; if not met, the rule is reported as
   chat-only and BFCL is not run for it. This replaces the v2 30/70 selection-confirmation for the NLL oracle.
6. No-contact family: named in LEDGER-PLAN before any file is fetched; sha256 recorded at first contact; never
   read, tokenised, generated on, or scored before that entry; zero 8-gram overlap with data/b3, data/bench and
   data/g0 (tests/test_g0.py content test extended); scorer not the vendored IFEval checkers; tool schemas and
   trajectories disjoint from BFCL/APIGen/ToolACE; (2) frozen by hash before opening; one run, arms and floors
   registered in the same entry. Only this run may use the word "zero-shot".
7. Harness preconditions, each a blocking test before its run: scripts/bfcl_mt.py never evicts the protected
   prefix (currently evicts from column 0 at bfcl_mt.py:339 — the agentic-salience-review-fable.md F1 CRITICAL is
   open); the Multi-IF 909 evaluation of the rule runs an EVICTION harness (full / evicted / ROLE_B / control /
   role_echo) with the ledger_kv_probe arm semantics — scripts/ledger_eval.py's text_ledger arms re-append text to a
   full context and are not an evaluation of retention; tokenizer sha and qwen3.py sha recorded in every meta.json
   and asserted equal across arms compared in one table.
8. Safety, every arm, every run: the registered safety table (timeouts = 0; truncations ≤ full + 1; degenerate
   sessions ≤ full; invalid outputs ≤ full); passes on degenerate outputs are counted as in H1' and the degenerate
   count is printed beside every pass count.
