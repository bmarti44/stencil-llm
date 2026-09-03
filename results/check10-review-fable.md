# Check 10 review — fable (independent, CPU-only), 2026-09-02

Scope: results/quick-checks/README.md item 10 (self_extract_turn2_check.py / _rows.json / .log) against
results/qwen/ledger-kv-probe-h1p/session-*.json, data/b3/mt-train-300.jsonl and scripts/ledger_kv_probe.py.
Method: every number below was recomputed from the rows + H1' records with a CPU script (tokenizer only; the matcher,
the sentence splitter and the echo-clamp loop were re-executed from the check's code path via ledger_kv_probe helpers).
Script: scratchpad an.py (not committed). No model was loaded; nothing under data/bench/ was read.

## 1. Totals recomputed from the rows — all reproduce

| arm | README | recomputed |
|---|---|---|
| full / evicted | 44 / 14 | 44 / 14 |
| finder pinned / pinned_echo / echo_only / finder control | 37 / 48 / 37 / 18 | 37 / 48 / 37 / 18 |
| SELF pinned / pinned_echo / exact-column control | 36 / 43 / 22 | 36 / 43 / 22 |
| n aged | 56 | 56 (= sum of n_aged; each equals len(instruction_id_list) - len(new_combo) of the last turn) |

The h1p block of every row equals the aged_pass of the corresponding H1' session record; n_aged agrees with the
corpus. Coverage 0.869 (16/20 >= 0.8) and extras 41 reproduce exactly — but see finding F2 for what they measure.

Paired per session: SELF pinned vs finder pinned +4/-5/=11; SELF echo vs finder echo +1/-6/=13; SELF echo vs full
+5/-4/=11. Echo gain: SELF +7/-1/=12, finder +9/-1/=10.

## 2. Does the extraction prompt see only the single user turn? — YES (code-confirmed)

`ask_ctx = "<|im_start|>user\n" + ASK.format(turn=context[a:b]) + "<|im_end|>\n" + OPENER` for each (a,b) in
`P._user_turns(context)[:-1]`. `context` is decoded from the H1' `context_token_ids`, whose meta.json records
"mark_isolation: all arm contexts ... have literal Constraint: markers removed"; I verified 0 occurrences of
"Constraint" in all 20 decoded contexts. No assistant turn, no marks, no kwargs, no oracle span, no system prompt
reaches the extractor. The last user turn is excluded (correct: its constraints are not aged). The ASK string is
byte-identical to check 9's (checks 9 and 10 differ only in the matcher); it is NOT the same prompt as checks 7/8
(read-time whole-history wording), so "prompt fixed before the run" is true for 9 -> 10 only.

Residual cue (LOW): mark-stripping leaves a fingerprint in the user text — each constraint sentence starts lowercase
after a double space ("newsletter.  use the word 'tallow' ..."). A generic extractor may exploit this segmentation
cue on b3; it will not exist on Multi-IF/BFCL. Not a leak of labels, but a reason not to read the 0.93 recall as
transferable.

## 3. What the extractor actually produced (105 quotes over 20 sessions)

By type (a quote is typed by the sentence its matched span covers >= 50%):

| type | quotes | fate |
|---|---|---|
| true aged constraint | 50 | matched; 50 spans pinned + echoed |
| task sentence of a prior turn ("Write a short account of X for a neighborhood newsletter", "Now add a brief closing section ...") | 30 | matched; pinned + echoed |
| reminder sentence "Every earlier constraint from this conversation still applies to this reply as well." | 14 | matched by the substring matcher, then ALL 14 dropped by the echo-clamp loop (see 4) |
| constraint fragment "begin with the exact title" (title split from its <<...>> by the 4B; s15, s19) | 2 | matched as a partial span (< 50% of the oracle clause) |
| the extraction prompt's own instruction sentence ("Quote verbatim, one per line ...") echoed back by the 4B | 9 (s03,04,05,07,08,09,14,16,19) | never matched (Jaccard 0.09-0.13) — harmless here, but the 4B confuses wrapper and message in 9/20 sessions |

Oracle-clause recall (the registered H1' auto_coverage definition, >= 0.5 of the clause covered): SELF 52/56
clauses = per-session mean 0.933, 17/20 sessions at 1.0, vs finder auto_coverage 0.967 (18/20). The four misses are
all EXTRACTOR misses (the quote never appeared), not matcher misses: s10 and s12 "keep the reply under 90 words in
total." (turn 2; the 4B quoted the title but not the length limit), s15 "respond using only capital letters
throughout." and "keep the reply under 110 words in total." (the 4B returned nothing usable for turn 1). This
contradicts check 9's caveat "the extractor quoted every true constraint"; that was true of the sessions inspected
then, not of the set. The pattern (per-reply length/casing limits treated as non-standing) matches the LABELS.md rule
"just for this reply -> none" — the teacher and the benchmark disagree on exactly this class (F6).

## 4. The echo clamp — verified on CPU

Re-running `P.echo_context` on the pre-clamp keep reproduces the drop loop exactly: the 14 dropped spans are the 14
reminder-sentence spans and nothing else (the token span begins with the leading-space token, so the window is
" Every earlier ...", `find(..., 1)` hits at 1, the bounded span is empty -> ValueError -> dropped). The loop mutates
`keep` as well as `aged`, so the reminder was removed from BOTH the pinned and the echo arm. Consequently quoting the
reminder is not a cheat in the reported numbers: it contributed zero columns and zero echo text.

Two side effects of the loop order (both LOW, both conservative for the claim):
- `n_pin` (logged "cols=...") and `coverage`/`extras` were computed BEFORE the drop; the SELF pinned arm actually
  pinned 1303 columns in total (rows SELF.pinned.pinned_cols), not the logged 1485. The 41 "extras" therefore
  include the 14 reminder spans that never reached any arm; the extras that actually entered the arms are 32
  (30 task sentences + 2 title fragments), and 5 of the task sentences coincide with the finder's own 7 extras
  ("Now add a brief closing section ..." x7 in r["keep"]).
- `matched_control_spans` was built from the PRE-drop keep, so the exact-column control pinned 1485 columns vs the
  SELF arm's 1303 (control >= SELF in 14/20 sessions). The control is over-budgeted by 14%; its 22 (vs finder
  control 18 at 932 columns) is consistent with the RB finding that budget alone buys a few passes.

## 5. Safety counts (recomputed; registered def: truncated or rep4 > 0.5)

| arm | truncated | degenerate |
|---|---|---|
| full | 1 | 2 |
| finder pinned / pinned_echo | 0 / 0 | 0 / 1 |
| SELF pinned / pinned_echo | 0 / 1 | 0 / 1 |
| SELF control | 1 | 4 |
| evicted / echo_only / finder control | 0 / 0 / 1 | 1 / 1 / 2 |

SELF echo's single degenerate session is s16 (truncated at 512; it scored 1/3 vs pinned 2/3). Within the H1' integer
clause (<= 2/20); no safety concern beyond the full arm's own.

## 6. Is the comparison to the finder fair? — NOT budget-matched

Columns pinned per session (SELF actual vs finder): total 1303 vs 932 (SELF/finder 1.40); SELF pins more columns in
17/20 sessions; SELF = 14.5% of the 9008 evictable columns, finder 10.3%. The extra mass is the 30 task sentences
(SELF's constraint-typed columns alone total 902, i.e. the finder's budget). Check 5 (RB) established on this very
probe that +40% budget for a role-type selection is worth about +4..+12 passes at the pin level. "SELF pinned 36
matches finder 37" is therefore a claim at unequal cost; the honest reading is "SELF at 1.4x the finder's budget
matches the finder", and the budget-matched SELF number is unknown. Two cheap registered controls would settle it:
(a) SELF restricted to its constraint-typed spans / a length-matched trim (same mechanism, ~932 columns), and
(b) the finder given SELF's budget (finder + oldest task sentences). Note the echo comparison is on firmer ground:
the echo text is what carries the effect (finder 37 -> 48, SELF 36 -> 43), and there the SELF deficit (-5, 1/-6/=13
paired) is precisely the task-sentence dilution the README names.

## 7. Would the extras be harmful or helpful in deployment?

- Task sentences (30/32 of the real extras): on b3 they are near-harmless (every task is "continue the same
  newsletter piece", so restating it is redundant) and cost only KV columns. On Multi-IF a restated earlier task
  ("write a poem about X") in the echo invites re-answering an old request; on BFCL a restated earlier tool request
  ("book a flight to ...") invites re-executing a completed action — the echo of a task sentence is an actual
  hazard there, not dilution. Pinning them without echo is the safer form of the same error.
- Reminder sentence: benchmark-specific meta-text; quoting it is not a cheat (dropped, see 4) but its presence in
  14/20 extractions shows the 4B classifies "instruction-shaped" sentences rather than standing rules. On a real
  benchmark it does not exist; nothing transfers either way.
- Title fragments: harmless duplicates of a covered clause.

## 8. Leakage audit

- Prompt wording: generic; no taxonomy words, no benchmark phrases. OK.
- Matcher: substring search over the normalized PRIOR history only (c0..c1 bounds enforced), fallback Jaccard >= 0.5
  over regex sentences. No oracle or finder input. The s08 coverage of 1.15 shows the coverage metric double counts
  nested matched spans (two quotes covering the same region); a clipped column-set coverage gives 0.860 mean
  instead of 0.869 (16/20 unchanged). Cosmetic.
- Reminder quoting: not a cheat (Section 4).
- b3 status: b3 is a selection set. Checks 7 -> 8 -> 9 -> 10 changed the extractor size, the prompt form (read-time
  whole-history -> write-time per-turn) and the matcher after looking at b3 outcomes; the README states this. Fine as
  a development probe; the 36/43 numbers are selection-set numbers and must not be quoted as an estimate of
  Multi-IF/BFCL performance.
- Raw extractor output is not recorded (only the filtered `extracted_lines`); s15's empty turn-1 extraction cannot be
  audited (NONE vs filtered-out). Record the raw text next time (AGENTS.md: registered output field list).

## Findings (graded)

- F1 (MEDIUM) Budget mismatch: SELF pinned uses 1.40x the finder's columns (1303 vs 932; 17/20 sessions higher).
  "Matches the taxonomy finder on pins" is unsupported at equal cost; needs the budget-matched control (Section 6).
- F2 (MEDIUM) Mislabeled metric: "coverage 0.87" is token-mass coverage of the FINDER's kept spans (r["keep"],
  focus=auto), not of the oracle constraints as check 7's wording implies; it is computed pre-clamp and double counts
  nested spans (1.15 in s08). The registered oracle-clause recall is 0.933 (17/20), finder 0.967 (18/20).
- F3 (MEDIUM) Extractor recall is not 1.0: 4/56 aged clauses were never quoted (s10, s12, s15), all per-reply
  length/casing limits — the class LABELS.md labels "none". Check 9's "the extractor quoted every true constraint"
  was over-general.
- F4 (LOW) The logged cols/extras/control were built from the pre-clamp keep: reported SELF columns overstated by
  182 (1485 vs 1303), extras overstated by 14 (reminders never reached an arm; real extras entering the arms = 32),
  control over-budgeted by 14% (conservative).
- F5 (LOW) The 4B echoes the extraction prompt's own sentence in 9/20 sessions; never matched here, but a wrapper/
  message confusion that a system-role framing or a stop-list should fix before deployment.
- F6 (LOW, registration item) Teacher/spec disagreement: the 4B teacher labels prior task sentences as standing
  instructions (30/40 task sentences quoted) and skips per-reply limits, while LABELS.md says the opposite for both.
  A classifier distilled from this teacher inherits the teacher's precision error unless the label spec wins.
- F7 (LOW) Mark-stripping leaves a lowercase-after-double-space segmentation cue in every b3 constraint sentence;
  recall on b3 may not transfer.

## VERDICT: CONFIRMED-WITH-QUALIFICATIONS

The arithmetic is right (all totals, coverage, extras, safety reproduce from the rows and H1' records), the
extractor sees only the single unmarked user turn, the matcher and clamp are clean, and the reminder sentence did not
contribute. What is NOT established: parity with the finder at equal cost (F1), and the "coverage" figure as stated
(F2). The echo result (43 vs full 44, finder_echo 48) stands as a selection-set observation with the dilution
mechanism concretely identified as 30 restated task sentences.

Register before this selector touches Multi-IF/BFCL:
1. A budget-matched SELF arm (constraint-typed or length-trimmed to the finder's per-session column count) and/or
   finder-at-SELF-budget, on the same 20 H1' sessions, with the pre-registered rule "SELF at budget >= finder - 2"
   or equivalent.
2. The exact extractor contract: prompt text (byte hash), 4B checkpoint hash, greedy decode, max_new 256, the
   post-filters (bullet strip, >= 3 words, NONE), a stop-list for the prompt's own sentence, and raw output recorded
   per turn (registered output field list, dry-asserted).
3. The matcher contract (normalized substring in prior USER turns only; fallback Jaccard >= 0.5) and the coverage
   metric definition (oracle-clause recall, clipped column sets), computed post-clamp.
4. An extras policy for deployment: whether task sentences may be pinned, and that they are NOT echoed (or a
   pre-registered echo cap), given re-execution hazard on BFCL; the reminder clamp is b3-only and must be replaced by
   a general "no meta-sentence" rule or removed.
5. Which turns the write-time extractor runs on (user only vs assistant/tool) and its per-turn latency budget
   (a 4B forward + up to 256 greedy tokens per message).
6. The b3 -> Multi-IF/BFCL wall: no prompt, filter, matcher or budget change after the first held-out number; the 36/43
   figures reported as selection-set results only.
