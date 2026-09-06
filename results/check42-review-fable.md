# Check 42 accuracy review (fable, 2026-09-05) — ONE ROUND

Scope: commit b5be4318; results/quick-checks/check42/{README.md, summary.json,
input-accounting.json, freeze.json, final-audit.*, coverage-diagnostic.*,
prefix-*.json, records/ (4,471)}; scripts/focus_check42.py; src/stencil/focus2.py
helpers; the recorded FOCUS-2d records under results/qwen/focus2d/outputs/run/records/
for the BOTH/neither references; my own source design in results/focus2d-review-fable.md
section 4 (3)-(5). CPU only. Every number below was recomputed from the raw records with
an independent script (exact binomial McNemar per src/stencil/stats.py's definition,
P[Bin(b+c, 1/2) >= b]). No sealed benchmark file was opened; no model was launched.

## 1. Recomputation — all registered numbers reproduce exactly

- Records: 4,471 = 192 episodes x (A,C: 5 checkpoints + SET/PREHOLD) + B's 124
  complete episodes x 7 + 915 delay generations (A 288, C 288, B 339 incl. 51 retries).
  Every record is sha256-wrapped; all 192 planned IDs have A and C checkpoint
  trajectories; B has checkpoint records for exactly 124.
- Common 124-episode subset, all-five (success at all five checkpoints; `success` =
  task AND constraint AND NOT broken in `score()`): A 99, B 99, C 88. Per-checkpoint
  success A 116/119/121/121/115, B 117/121/120/118/116, C 108/120/115/107/124
  (SWITCH/HOLD/BACK/CLEAR/NEUTRAL2). Match.
- Paired all-five: A vs C b/c 23/12, p(worse) 0.97952, p(better) 0.044766;
  B vs C 20/9, 0.98794 / 0.030714; B vs A 4/4, 0.63672 both ways. Match.
- Constraint failures (any checkpoint with constraint = False): A 0, B 0, C 0.
  All seven F6 flags (broken, json_invalid, schema_invalid, empty, placeholder,
  truncated, repetitive) are 0 for A, B, C on the 124 and for A, C on all 192. Match.
- Collateral on 124: user_fact A 1 / B 0 / C 0; tool_fact 1/0/0; assistant_fact
  (41 memo episodes) A 23, B 3, C 27. A's single fact loss is
  final:sort:descending:0:21 at NEUTRAL2 (answer+tag only, both requested keys
  omitted; task still correct so it is collateral, not constraint, per FOCUS-2d
  scoring). Match.
- Recorded references, recomputed from the original 7,296 FOCUS-2d records on the
  same 124 IDs: BOTH all-five 78, constraint failures 15 (all 15 are the CLEAR
  bare-array schema_invalid cases from my FOCUS-2d review), broken 0, per-checkpoint
  101/114/115/109/124; neither 0, 0 failures, 57/73/88/0/9. Match.
- Full A/C coverage diagnostic (all 192 planned pairs, no exclusion in either arm):
  A 151, C 131, b/c 39/19, p(better) 0.0059641, p(worse) 0.99732; constraint 0/192
  each; assistant_fact 39/64 vs 42/64. Match.
- Input accounting: `bank()` selects original index < 48 per cell; memo episodes are
  indices 0-15 in every cell of the full bank (16/64), so the subset carries all 64
  memo episodes (16/cell, 33% vs 25% in the full bank). The freeze's descriptive
  string "12 memo episodes per cell" was wrong; the correction in
  input-accounting.json is accurate and no ID, byte or score changed
  (`frozen_ids_match: true`). Selection is outcome-independent.
- Pre-registration chain: README at pre-run commit 9803c032 hashes to
  7eb58cca..., equal to freeze.json `prewritten_reading`; scripts/focus_check42.py
  at HEAD hashes to 0282f2cd..., equal to freeze `check42_source`; `run()` refuses
  to start if either differs. The reading was fixed before any output.
- C's 1,632 fresh records are token-identical to the original text-restate
  trajectories (greedy determinism), as final-audit.json states. This means the
  comparator's outcomes were known before the check was designed (disclosed as
  "other-arm outcomes seen").

## 2. The delay-cap exclusion mechanism (B's 68 lost episodes)

It is a prompt-design artifact of arm B, not a harness bug and not an arm-specific
code path. The harness treats every arm identically: isolated generation of each
delay pair (160-token first attempt, 320-token retry, `delay_capped` = eos None and
length == cap), then replay of the exact pair into history. Only the user text differs:

- C: the 512-token neutral text ("The room is quiet. ... Quiet. Answer in one
  sentence."). Model answers "The room is quiet." (5 tokens) in 288/288.
- A: live rule line + neutral text. At DELAY0/DELAY1 (rule = sort ascending/
  descending) the model answers with a sorted integer list -20..20 (87 tokens,
  96/96 each); at DELAY2 (default rule "Return the payload list unchanged.") it
  answers "The room is quiet." (96/96). All terminate; none flagged.
- B: live rule + "Output compact JSON of the form {"answer": <JSON array of
  integers>, "tag": <integer>}; no prose or unrequested keys." + "Keep tag equal to
  N." + neutral text. The block orders a JSON integer array for a turn that has no
  payload. All 152 capped outputs begin `{"answer": [` and are a degenerate run
  (typically the tag value repeated) until the cap. First-attempt caps DELAY0 17/96,
  DELAY1 21/86, DELAY2 46/73; retries recover 7, 8, 1; twice-capped 10+13+45 = 68.
  DELAY2 is worst because "Return the payload list unchanged" + the schema line with
  no payload gives the model nothing to return. When B does terminate it answers
  with a well-formed JSON object (e.g. {"answer": [1,...,10], "tag": 75}), which is
  itself a format-conforming answer to a prose question.

So the cause is the schema/format line rendered into a non-task turn — precisely the
"request type distinction" the README tells future designs to preserve. It was frozen
into B's design ("Schema/tag are repeated in delay user turns too") and the exclusion
rule ("A twice-capped delay excludes its episode from every paired arm") was frozen with
it. Note also that A's delay answers are no longer neutral prose either (sorted lists at
DELAY0/1); this does not affect scoring validity but means A's histories carry two
extra sorted-list exemplars in delay-512 cells. A's NEUTRAL2 failures (14/192) split
7/7 between delay-0 and delay-512 cells, so no evidence this hurt A.

Selection check on the exclusion: on the 68 excluded episodes A 52 vs C 43 (b/c 16/7),
i.e. the dropped episodes favour A slightly more than the retained ones. The 124 subset
is therefore, if anything, conservative for the A-vs-C claim; there is no bias in A's
favour from conditioning on B's completion.

## 3. Was the closure rule applied mechanically?

Yes. `closes_masking = not excluded and not unfinished and cand >= comp and
p_worse > .05 and constraint delta <= 2` is evaluated per contrast with `excluded`
global (any episode lacking all three arms). The prewritten text says both "MASKING
CLOSED if A or B ..." and "No complete-pair closure claim if any planned episode is
excluded" and "A twice-capped delay excludes its episode from every paired arm". The
global reading is the most conservative and is the one coded before generation; it was
applied unchanged, the ledger recorded the consequence at the first excluded cell
(ascending/512 index 0) before any score aggregation, and the A/C coverage diagnostic
was declared at that point as descriptive. No gate, threshold, prompt or cap changed.
A per-candidate reading ("A on its complete pairs") is also admissible from the same
text and would close on 192/192 pairs; the team chose not to take it. That is correct
conduct under AGENTS.md (conservative reading, disclosed), and the label should stand
as recorded.

## 4. Plain answers

(a) Does the substantive finding hold? Yes. Plain every-request placement of the live
rule (A) beats the anti-imitation recap (C) on the frozen numeric gate with zero
constraint and zero structural harm, on the 124 common episodes (99 vs 88, p(better)
.045) and more strongly on all 192 complete A/C pairs (151 vs 131, b/c 39/19,
p(better) .006, constraint 0/192 each). Per checkpoint on 192, A beats C at SWITCH
(179 vs 169, 13/3), BACK (186 vs 171, 16/1) and CLEAR (188 vs 169, 20/1), ties at HOLD
(181 vs 184, 3/6) and loses only at NEUTRAL2 (178 vs 192, 0/14), where A still
sometimes imitates the retained sort answers. This confirms my FOCUS-2d reading:
cadence, not supersession wording, is what made text-restate work, and the bare rule
is at least as good as the recap where both are rendered. Masking is dominated:
recorded BOTH on the same 124 is 78 all-five with 15 constraint failures (bare-array
CLEAR answers) and 41/41 assistant-fact losses; A vs BOTH paired 31/10, descriptive
p .0007 (on 192: 151 vs 109, 57/15, p 3e-7, BOTH 41 constraint failures). Nothing
masking bought at HOLD/NEUTRAL2 is missing from A, and A has none of masking's costs.
"Zero constraint harm" is exact for A/B/C; "zero collateral harm" is not — A loses the
user and tool fact once (1/192 each) and assistant-fact recall stays poor (39/64,
comparable to C's 42/64). B's local schema/tag repetition does not change all-five
(99 vs 99, 4/4) but does fix assistant-fact recall (3/41 vs 23/41, p 5e-6) — a real,
useful signal for the register design, achieved only in the 124 episodes where B did
not runaway.

(b) Is "not closed" a technicality? Yes, an infrastructure/design technicality of the
frozen three-arm coupling, not a scientific failure of placement. A itself excluded
nothing; the excluded episodes were lost because B's frozen delay block put a JSON
format order into a prose turn. The numeric gates for A pass on both the common subset
and the complete 192, with the excluded 68 favouring A. The correct reading for the
ship design: register the live task/default rule and render it in every task request
(A); render format/persistent constraints (schema, tag, memo obligation) only in
requests of the type they govern, never into turns of a different type (B's lesson);
keep the cache/mask machinery as an experimental arm, not the default. The formal
label "MASKING NOT CLOSED under the frozen reading" should stay in the README as
written; the ledger and any successor plan can state "masking dominated on this
family; placement-every-request is the ship candidate; closure label withheld on the
frozen no-exclusion guard only".

(c) Overclaims to avoid. (i) The 124-episode tables are conditional on B completing
its delays; cite the 192-pair A/C numbers for A and say the 124 numbers are the frozen
common-sample view. (ii) The bank is reused and C's outcomes were known
(token-identical to FOCUS-2d text-restate) before the design; this is a confirmatory
quick check of a hypothesis formed on the same bank, not an independent replication.
(iii) One seed (9053723), one family (sort), one model (Qwen3-4B greedy bf16),
synthetic payloads, three change events; no claim about other families, models,
benchmarks or autonomous change detection. (iv) The subset has a 33% memo fraction
vs 25% in the bank; direction/delay balanced. (v) Do not call B "validated": its
all-turn carrier fails 68/96 delay episodes by construction, and its assistant-fact
gain is measured on the surviving 124. (vi) "p(better) .045 on 124" is a single
uncorrected one-sided test on a subset; the 192-pair p .006 is the robust statement.
(vii) A's delay answers are sorted integer lists, not neutral prose; do not describe
A's histories as containing untouched neutral delays.

(d) Is a further run needed? Not for the decision at hand. The evidence that
every-request placement of the live rule beats the recap and dominates masking on this
family is complete on 192 pairs with no exclusion and passes the frozen numeric gate
with margin; rerunning A vs C would only re-confirm a deterministic greedy result on
the same bank. The only open, cheap and optional cell is a corrected B — schema/tag
rendered in task requests only, plain rule (or nothing) in neutral turns — to see
whether the assistant-fact recall gain (3/41 vs 23/41) survives without the runaway.
That is a register-design refinement, not a prerequisite for shipping A or for
retiring masking from the default path. If Brian wants the formal "MASKING CLOSED"
label on a fresh registration, a two-arm A vs C run on a new seed (different bank) is
the honest way to get it; the present check should not be relabelled.

## 5. Minor notes (none above low)

- README claim "Thus zero checkpoint truncations does not mean no capped
  generations" is accurate: capped delay attempts carry `complete: true` and are
  identified only by `delay_capped()`; my first pass filtering on `complete` found
  none, which is the trap the README warns about.
- The README's PENDING/pre-run section and the interrupted-pre-reboot/ directory are
  preserved history; the 4 pre-outage records were not reused (recovery.json).
- Charged GPU time 11,631 s of 12,600 s, including a 299 s pre-outage allowance;
  cap respected.
- freeze.json still says "12 memo episodes per cell"; leave it (hash-bound), the
  correction lives in input-accounting.json and summary.json.
