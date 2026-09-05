# Review of results/focus-synthesis-astra.md (fable, one round, 2026-09-05)

Scope: gpt-6-astra's synthesis of quick checks 31-36 and its proposed larger test, judged
against results/quick-checks/README.md items 31-36 + QUEUE, check3{2-kv,3,4,5,6}/README.md
and summary.json, my own check31/32/34/35 reviews, and results/astra-drift-assessment.md.
CPU only; no model launched; sealed IFEval input and BFCL cohorts not opened. For the
Multi-IF feasibility finding (F7) I read ONLY the per-turn `instruction_id_list` metadata
fields of data/bench/multiif_en.jsonl (no prompts, no responses, no scores), to count
eligible conversations under the synthesis's own eligibility rule.

Note on "check 37, now running": at review time no check37 directory, script, prewritten
reading or WORKLOG entry exists in the tree (`find` for *check37*, `ls scripts`, WORKLOG
tail), and `nvidia-smi --query-compute-apps` returned no compute process visible to me.
I therefore review the repair pre-check as specified in the synthesis (lines 47-55), not an
executed artifact. See F8.

## VERDICT: SOUND-WITH-FIXES

The one-paragraph finding is accurate: every number I traced is correct against the raw
summaries (check35 summary.json, check36 summary.json arms R1-R5), and the three pairwise
orderings are each backed by a paired contrast on the same histories. The novelty paragraph
is honest. The proposed test is sound in structure (2x2 factorial + strong text bar, paired
McNemar with Holm, prewritten gates, correct lineage) but has one stage that cannot run as
specified (Multi-IF, F7), one arm whose wording can rig the primary contrast (text-restate,
F4), one safety gate that fails on chance (F6), and a competence bar that the sorting family
already misses (F5). Fixes are exact-text replacements below; none changes the hypothesis.

## 1. Accuracy of the one-paragraph finding (lines 3-16)

Verified, number by number:

- "old-position SWITCH scored 2/32 after both downstream recomputation and full text
  rebuild, with identical generated outputs (not bitwise-identical caches)" — check36 R2
  SWITCH exact 2, R3 exact 2, both 29 A / 2 B / 1 copy; README states 32/32 identical token
  sequences at SWITCH and BACK, max |dK|/|dV| 18.37/38.06. Correct.
- "current-user text cue scored 27/32" — check35 TEXT SWITCH 27 (BACK 29). Correct.
- "release+recompute reached 17/32, but BACK fell to 14/32, only 5/32 strict" — R4 SWITCH
  17, BACK exact 14, strict 5 (11 copy, 7 other). Correct.
- "CLEAR and its follow-up copied in 25-28/32" — c2 forks only: S2/c2 25/25, S3/c2 27/28,
  S4/c2 27/26, S5/c2 27/26. Correct for the release (c2) arms; c1/c3 are 0-11.
- "zero copying and 32/32 impositions for its neutral-text CLEAR baseline" — TEXT/text CLEAR
  0 copy / 32 A, NEUTRAL 0 / 32. Correct.
- "even the intact-A control fell from 27/32 to 17/32 after the second deletion" — S4
  SWITCH 27 A, BACK 17 A. Correct.
- "K and V jointly worked, either alone did not, and layers >=12 sufficed" — check34
  k_only/v_only 0/64 (copy), layers_ge12 58/57. Correct.
- "Checks 32/33 also missed their text-competence eligibility bars" — 32: 29/64 vs 48/64;
  33: 34/64 and 7/64 vs 48/64. Correct.
- "averaged four-column suffix K/V packets" (line 8) — check32-kv README line 13: fp32 mean
  of the four suffix columns' post-RoPE K/V. Correct.

Is the ordering established?

(a) current-position instruction > own recent outputs: check34 Part 2, B cue in the current
user turn after three completed A turns, 60/64 (and A after B 60/64); check35 TEXT SWITCH
27/32 with two A answers retained. Established, paired.

(b) current-position instruction > standing instruction at an old position: check35 TEXT
SWITCH keeps the transplanted A cue at columns 64-75 (only the user turn says B) and
scores 27/32 B. Established, but note (a) and (b) are confounded in TEXT: the current cue
beat A-cue AND A-answers together; no arm had a current B cue against an old A cue with
answers removed. That is fine for the ordering claim (the current cue beats the
conjunction), but the synthesis should not imply each pair was isolated. See F1.

(c) own recent outputs > standing instruction at an old position: this is the claim the
task asked me to verify. Check36 R3 rebuilds the whole context from text with the B cue
tokens at 64-71 (the four-token suffix at 72-75), teacher-forces the recorded A answers at
their original boundaries, and freshly prefills the SWITCH query: 29/32 continue A. The
standing instruction (B) is genuinely present as text and genuinely recomputed, and the
only A-carrying content is the two retained own answers plus their downstream columns.
So "own outputs > old standing instruction" IS shown with the instruction present and
recomputed. Two caveats belong in the sentence: (i) the "standing instruction" in R2/R3
is a contradicting REPLACEMENT — the history never shows the model obeying B, so what was
measured is "two own demonstrations beat a rewritten system instruction they contradict",
not "a standing instruction loses to its own outputs" in general; (ii) the standing
instruction sits inside a 76-token neutral system prefix at absolute positions 64-75,
and R4 (14/32 A with NO A cue and NO A answers anywhere in the recomputed history) shows
ascending is also a default attractor under the malformed empty-turn structure, so part of
the 29/32 may be prior, not imitation. Neither caveat overturns the ordering; both bound it.

### F1 (low, accuracy of wording) — line 4-5
Replace:
"with a recency-weighted ordering: a current-position instruction > the model's own recent
outputs acting as demonstrations > a standing instruction at an old position."
With:
"with a recency-weighted ordering: a current-position instruction > the model's own recent
outputs acting as demonstrations > a standing instruction at an old position. The three
pairs rest on: check 34 Part 2 (current cue vs three own answers, 60/64) and check 35 TEXT
(current cue vs old cue plus two own answers together, 27/32); check 36 R3 (two own answers
vs a contradicting rewritten old-position instruction, text-rebuilt, 29/32 still A). The
current cue was never tested against the old cue alone, and the old-vs-own contrast used
an instruction the history had never been seen obeying."

### F2 (low, accuracy) — line 25-26
"Repeated body/EOS deletion also leaves malformed empty assistant turns" is correct
(check35 F4: assistant header + empty think block + newline, no content, no im_end), but
R4 adds a second fact worth one clause: with the B cue recomputed and no A anywhere,
14/32 still sorted ascending. Append after "17/32 after the second deletion.":
"Check 36 R4 (B cue recomputed, all answers removed, malformed turns kept) still produced
ascending in 14/32 with no ascending cue or answer in the history, so the malformed
structure also exposes a default-direction prior; the larger test must report results
per change direction, not pooled."

## 2. Novelty honesty (lines 28-37)

Honest and correctly scoped. "Recency, restatement and few-shot imitation are prompting
folklore" is the right concession; Multi-IF's own paper documents turn-wise adherence
decay, and lost-in-the-middle / demonstration-anchoring are known. The three "new in this
record" items are correctly labeled as record-local, not literature priority. One
overstatement:

### F3 (low) — line 30-31
"matched cue K AND V are needed together. That is a measured mechanism worth checking"
K-only and V-only 0/64 is an attention-arithmetic consequence (V-only is bitwise OFF
because filler keys draw no attention; K-only attends to cue-shaped keys holding filler
values). It is a clean reduction, not a mechanism to check. Replace "matched cue K AND V
are needed together." with "matched cue K AND V are needed together (an expected
consequence of attention arithmetic, recorded here, not a hypothesis to test further)."

Also, line 32-33 correctly narrows "eviction beats text at CLEAR" to the tested neutral
reminder; that sentence is the most important honesty line in the document and should
survive any edit.

## 3. The proposed larger test (lines 39-91)

### Repair pre-check (lines 47-55) — sound with two additions

The design (intact vs body/EOS deletion vs whole-pair deletion vs one-token placeholder
body with valid closure; cache-deletion vs text-rebuild at matched absolute positions;
two releases under an active cue, then cancel + two neutral requests) is the right
experiment, and preselecting the placeholder is the right pre-commitment. Gates are
prewritten. Issues:

F8 (medium, process) — no check37 artifact exists in the tree at review time. The house
rule (README QUEUE: "pass/fail reading written before running") requires the reading and
script hash to be committed before or at launch. If check 37 is running, its prewritten
reading is not in git; commit `results/quick-checks/check37/README.md` (prewritten section)
and the script before results land, and record in WORKLOG the launch time and GPU query.
Otherwise the pre-check cannot be distinguished from a post-hoc variant selection, which
line 55 explicitly forbids.

F9 (medium, design) — the placeholder body "." is itself a demonstration. Under the
synthesis's own account (own outputs are few-shot demonstrations), two assistant turns
containing only "." teach "answer with a period". The >=26/32 copy gate would catch a
failure but would not distinguish "placeholder imitated" from "residual sorting". Add to
line 52 after "Score strict validity, active-task and neutral accuracy.":
"Also count outputs equal to the placeholder token or empty at every scored request
(placeholder imitation), reported as its own column; any such output is a breakage."

F10 (low, design) — the pre-check tests deletion under the SAME cue (A active), then
cancel. The larger test deletes at a change (new cue live). A placeholder that is harmless
under A-active may still be read differently when the new cue conflicts; this is covered by
the synthetic stage, so no change to check 37, but line 55 should say so: append
"The pre-check certifies structural safety under an active cue only; its effect at an
instruction change is measured in the synthetic stage, not assumed."

### Five arms and primary endpoint (lines 62-71) — sound; three fixes

The 2x2 (placement x eviction) plus a text-restate bar is the correct factorial, and
"neither" = old-slot text update reproduces check36 R3 on four new families, which is a
useful replication. Two of the three decision contrasts are, however, not informative:
"both > eviction-only" is guaranteed by R2/R3-vs-TEXT (old-slot update fails at 2/32
regardless), and "both > placement-only" is weaker than "both > text-restate" because
text-restate contains placement plus restatement at every request. The only contrast that
answers the question is both vs text-restate. That is fine as a decision rule (all three
must hold) but the write-up should say which contrast carries the claim.

F4 (high, fairness) — line 64-65, text-restate wording. The hypothesis is that own outputs
act as demonstrations. The strongest text competitor therefore must explicitly tell the
model to disregard its own earlier answers, not just cancel superseded rules. If the
frozen restate template omits that clause, "both > text-restate by 5 points" can be
manufactured by under-specifying the text arm. Replace:
"text-restate = keep answers, explicitly cancel superseded rules and restate all live
rules/default at EVERY scored request."
With:
"text-restate = keep answers; at EVERY scored request, in the current user turn,
explicitly cancel the superseded rule, state that the assistant's earlier answers in this
conversation followed a rule that no longer applies and must not be imitated, and restate
all live rules or the default. The template is frozen and hashed before the repair
pre-check; its exact text is published with the freeze."

F11 (medium, confound) — line 57 retains two unscreened earlier answers in every arm. In
the "both" and eviction-only arms those answers are removed, so any SET/HOLD errors
(29/32 and 31/32 in check 35: 3 and 1 wrong) are removed too, while text arms keep them.
Part of a "both" advantage could be removal of BAD demonstrations, not STALE ones. Add
after "retained unscreened.":
"Record whether both earlier answers were correct; report every primary contrast
stratified by that flag, and state the effect within the both-correct stratum as the
mechanism estimate."

F12 (medium, safety design) — line 59 keeps "later-needed user/tool facts" but eviction
removes only assistant bodies, so no fixture can detect loss of assistant-authored content
(the real collateral cost of deleting own outputs). Add after "cannot count as success.":
"In a fixed 25% of episodes per family the second neutral request also asks for one value
the assistant itself produced in a pre-change answer (e.g. 'What was the third element of
your first answer?'); score it as a collateral fact, reported separately, not in the
primary endpoint. Eviction arms are expected to fail it; the report must show the size of
that cost next to the benefit."

F13 (medium, structure) — line 57 "0/512-token delays": check 34/35's 128-token HOLD
filler was a user turn with no assistant reply, and consecutive user turns were a
confound in every SWITCH/BACK result so far (check34 F4, check35 F6). Replace
"0/512-token delays" with "0/512-token delays, where the delay is one or more VALID
user+assistant pairs (a neutral question and the model's actual answer, retained
unscreened), never an unanswered user turn".

### Decision rule (lines 71-73) — correct test, one clarification

Exact McNemar on paired binary joint success, Holm over three contrasts at .05, plus a
>=5 pp practical margin over text-restate (13/256 episodes) is appropriate. Add the
sentence: "The claim rests on both-vs-text-restate; both-vs-eviction-only is a
manipulation check and both-vs-placement-only a dose check; both are required but neither
alone supports the claim."

### Safety gates (lines 73-76)

F6 (medium, statistics) — "zero newly broken episodes versus text-restate" with n=256 and
a ~1% structural breakage base rate (check35 TEXT 1/128 answers; check34 1-2/64) expects
2-3 broken episodes per arm by chance, so a discordant break under "both" alone has
roughly even odds. As written the gate fails a true benefit by coin flip and, worse, a
1-count difference could be argued either way after the fact. Replace:
"Safety requires zero newly broken episodes versus text-restate, strict schema checks,"
With:
"Safety requires: structural breakage (empty, truncated, repetitive, schema-invalid) under
both not significantly higher than under text-restate (paired exact McNemar, one-sided
.05) AND at most 2/256 episodes broken under both but valid under text-restate; strict
schema checks;"
Keep the 1.16% one-sided bound sentence; recompute it for the chosen count (2/256 gives a
one-sided 95% upper bound of about 2.5%).

### Competence bar (line 60)

F5 (medium, will stop the study on noise) — ">=29/32 per cued skill" is above the sorting
family's own measured competence: check31 4B ascending 27/32, check35 SET 29/32 (all arms
share one measurement), check34 text_A 59/64 = 29.5/32 equivalent. The gate as written
fails ascending sort with p roughly 0.4 by binomial noise at a true 90% rate. Replace
">=29/32 per cued skill" with ">=56/64 per cued skill (the check-34 single-shot bar
rescaled), with the two directions of each family reported separately".

### Multi-IF stage (lines 77-83)

F7 (high, feasibility) — the stage cannot run as specified. Multi-IF's English split
(909 conversations, pins-manifest revision 0ab97ce0) has cumulative, non-conflicting
instruction lists by construction: from the `turn_{1,2,3}_instruction_id_list` metadata
alone (no prompts read), 896/909 rows have turn-3 lists that extend turn-2 lists, 890/909
add exactly one new instruction id at turn 3 (19 add none), and ZERO rows add a turn-3
instruction in the same family (change_case, language, length_constraints, startend,
detectable_format) as an earlier live one. There is no "explicit change/override" at turn
3 to identify; the eligible slice under line 77's rule is empty, and any wider rule
("any new constraint") would make eviction delete demonstrations that satisfied
constraints which are STILL LIVE — the opposite of the release hypothesis. Under that
wider rule "both" would be expected to LOSE, and a loss there says nothing about
release. Two acceptable fixes; pick one and say which:
(1) Cut the Multi-IF stage; move its 5.5 GPU-h to reserve (HARD TOTAL stays <=12) and,
if a second evaluation family is wanted, use fresh override/cancel episodes built with
SC1's scope/checker primitives (line 83) as a second SYNTHETIC family, disjoint seed,
frozen before the repair pre-check.
(2) Keep Multi-IF only as a DO-NO-HARM check, not a transfer test: treat every turn-3
conversation as "no change" (oracle says: nothing superseded), so "both" == placement
with no eviction and the only measurable quantity is whether the current-recap placement
harms or helps native turn-3 adherence. That is a placement-only safety check and must
be labeled as such; it cannot support "safe benefit beyond current text".
Replace line 77-82 accordingly, and replace line 81's "safe benefit beyond current text
on Multi-IF supports transfer" with "Multi-IF contains no supersession events; transfer
of release cannot be measured there".

Fitting: the synthetic stage lineage (line 43-45) is correct and complete. For the
Multi-IF stage, even under option (2), the eligibility/scope rule must be written and
hashed before the file is opened by the script; my metadata count above was done for
this review and must not be used to choose thresholds (it is a feasibility count, not a
development signal). The "replay identical unscreened turn-1/2 answers across arms"
choice is correct.

### What could make it pass without answering the question

1. Rigged text arm (F4) — fixed by the "do not imitate your earlier answers" clause.
2. Removal of erroneous demonstrations rather than stale ones (F11) — fixed by
   stratification.
3. Shorter context. "both" always has the shortest history; adherence generally rises as
   context shrinks. The 0/512 delay stratum partly controls this; add to line 72's
   reporting: "report the both-vs-text-restate discordance separately for the 0-delay and
   512-delay strata; if the gain is confined to the 512-delay stratum, report it as a
   context-length effect, not release".
4. CLEAR trivially equals a fresh single-turn prompt under "both" (old slot retired,
   answers removed, current default request). That is the hypothesis, not a leak, but
   line 82's "synthetic success alone is scoped" should name it: "a both-arm CLEAR is a
   near-fresh prompt; the claim is only that text cancellation cannot match it".
5. Oracle scope map — correctly disclosed (line 41) as control, not detection. No fix.
6. Direction prior (F2/R4) — fixed by per-direction reporting.

### Cost realism (line 88-91)

Synthetic: 256 episodes x 5 arms x ~7 requests = ~9,000 decisions at <=64 tokens.
Check35 measured 43.4 s per 48-decision episode (0.9 s/decision, 6 arms batched) with
recomputation adding prefill only; 9,000 x ~1 s = ~2.5 h, so 4 GPU-h holds if arms are
batched as in check 35. If the text-rebuild histories are prefilled one episode at a time
with 512-token delays, expect 1.5-2x; still under 4 h. Repair 0.5 GPU-h: 32 episodes x 4
variants x 2 renderings x ~6 requests = ~1,500 decisions, ~25 min; holds. Multi-IF
5.5 GPU-h: 128 x 5 x 256-token answers plus shared turn-1/2 generation is ~3-4 h at
15-20 tok/s single-stream; holds but is the only stage without batching headroom — moot
under F7 option (1). The 12 GPU-h HARD TOTAL with foreground timing pilots is realistic.

## 4. Cuts

Agree with all cuts at line 85-87 (Q5, Q6, Q2, vector/packet/dose grids, 1.7B, fleets,
SC1 governance revival). Additional cuts:
- Multi-IF transfer stage as specified (F7) — cut or demote to a placement do-no-harm
  check; this is the largest single cost item and cannot answer its question.
- "neither" and "eviction-only" stay (cheap, and they are the manipulation checks), but
  drop them from any headline sentence; only both-vs-text-restate carries the claim.
- The four families could be three: "output representation" and "field selection" both
  test format-type changes; if the competence fixtures fail one, do not replace it —
  report three families rather than adding a family after seeing competence results.

## 5. Findings summary

| # | Severity | Line | Issue |
|---|---|---|---|
| F7 | high | 77-82 | Multi-IF has zero turn-3 override events by metadata; stage infeasible as specified |
| F4 | high | 64-65 | text-restate template must tell the model not to imitate its earlier answers |
| F5 | medium | 60 | >=29/32 competence bar already missed by sorting; use >=56/64 |
| F6 | medium | 73 | zero-new-breakage gate fails on chance at n=256 |
| F8 | medium | 47-55 | check 37 running with no committed prewritten reading in the tree |
| F9 | medium | 52 | placeholder "." is itself a demonstration; count imitation |
| F11 | medium | 57 | stratify by pre-change answer correctness |
| F12 | medium | 59 | no fixture can detect loss of assistant-authored content |
| F13 | medium | 57 | delays must be valid user+assistant pairs |
| F1 | low | 4-5 | state which contrast supports each pair of the ordering |
| F2 | low | 25-26 | R4 shows an ascending default prior; report per direction |
| F3 | low | 30-31 | K+V-jointly is attention arithmetic, not a mechanism to check |
| F10 | low | 55 | pre-check certifies structure under an active cue only |

No number in the synthesis is wrong. VERDICT: SOUND-WITH-FIXES — apply F4, F5, F6, F7
before freezing; F8 before check 37 results are read; the rest before the synthetic freeze.
