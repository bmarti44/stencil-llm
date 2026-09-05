# Check 36 review (fable, one round, CPU-only) — commit c294688

Scope: results/quick-checks/check36/README.md, 4b/ raw records, validate.py,
scripts/focus_check36.py; context results/check35-review-fable.md (plain answers
(b)/(c), which asked for this check). No model launched; no sealed inputs read.

## Verdict: ACCURATE-WITH-CORRECTIONS

Every number in the README reproduces from the raw records. The corrections are
interpretive: what the 2/32 does and does not establish about "own recent
outputs > standing instruction at an old position", and one unquantified cache
comparison.

## 1. Bookkeeping — verified from raw records, independently of validate.py

- Denominators: 10 (arm, step) cells x 32 = 320 records, no duplicates. Label
  counts, value-exact and strict counts match the README tables exactly
  (R1 3/32, R2 2/32, R3 2/32, R4 17/32 SWITCH; BACK 32/32/32/14/32; R4 BACK
  strict 5). "Copy" in the README = the scorer's OFF label (input echoed).
- R2 recompute: in all 32 episodes the single `recompute_downstream` operation
  covers positions 76..len(history)-1 as one contiguous span, replaying exactly
  history[76:] (spans == [[76, N]]); prefix 0-75 asserted bitwise unchanged.
  So every post-cue column was recomputed under the B packet at 64-75.
- R3 text: in all 32 rebuilds, tokens 64-71 are the 8 B-cue token ids, 72-75
  the 4-token suffix, 0-63 and 76.. identical to the source history; the A cue
  and the OFF cue token sequences occur nowhere in the rebuilt text (checked
  as id subsequences). The B cue is in the SYSTEM message ("...The room is
  still.\n" + 40 space tokens + "Sort the numbers from largest to smallest.
  The context is ready<|im_end|>").
- Prior A answers are present in every R2/R3 history at the recorded answer
  positions: 60/64 are value-exact A; the 4 others (ep 1, 6, 13 SET; ep 9
  HOLD) are near-ascending malformed lists. The two R2/R3 B successes (ep 7,
  12) do not coincide with those episodes.
- R2 == R3 generated tokens: 32/32 SWITCH, 32/32 BACK. R1 == S1 and R5 == S2
  generated tokens: 32/32 for both steps (recomputed here, not taken from
  validation.json). R4 SWITCH lists are identical to check35 S3/c2's, and S3's
  SET/HOLD answers are identical to S1's, so R4 vs S3/c2 is a legitimate
  paired contrast (see 2.3).
- Fixed verdict: aggregate() maps max(R2,R3) <= 8 -> PRECEDENCE_PATTERN
  mechanically; the frozen reading's sha256 matches summary.reading_sha256 and
  the README byte-prefix. The label was applied by the pre-written rule.

## 2. Substantive findings

### 2.1 (medium) The cache comparison is reported but not really quantified.

0/1152 per-layer K or V tensors are bitwise equal (36 layers x 32 episodes x
{k,v}). Median per-layer max_abs 1.16 (K) / 0.48 (V); median rms 0.031 / 0.014.
K max_abs jumps from <2 in layers 0-15 to 11-18 in layers 17-35; V max_abs
grows monotonically to 38.1 at layer 35 (mean rms there 0.12). The records
store only per-layer max_abs and rms, no reference magnitude and no
per-position breakdown, so (a) the 18/38 maxima cannot be classed as bf16
rounding on outlier channels versus a real discrepancy, and (b) one cannot tell
whether the differences concentrate at the transplanted 64-75 (R2's donor
packet was computed in a 76-token prefill; R3's in a ~450-token prefill) or are
spread over the recomputed span. Note the comparison also covers positions
0-63, which R2 never recomputed. What the check establishes is behavioral
identity (64/64 outputs), which is the right evidence for the README's
conclusion; the README should say "unquantified relative to activation scale"
rather than letting the 18/38 numbers stand alone. Cheap fix for future runs:
record max|a|, max|b| and per-span max_abs alongside.

### 2.2 (high, interpretive) R2/R3 do NOT isolate "recent own outputs beat an old standing instruction".

In R2/R3 the B cue is simultaneously (i) in the system role, (ii) the oldest
task text, and (iii) followed by two assistant answers that are (iv) consistent
demonstrations of input -> ascending list and (v) were produced under the A cue.
Nothing in the 32 histories varies any of these, so the records cannot separate
precedence-by-role, precedence-by-recency, or few-shot pattern continuation; the
fixed label "PRECEDENCE_PATTERN" bundles them by construction.

Two further facts, both in the artifacts, bear on it:
- R4 ends with NO A information anywhere in the cache (prefix 0-63 precedes the
  cue, 64-75 is the B donor, everything >= 76 recomputed from A-free survivors)
  and still produces ascending output 14/32. A fresh B cue at the same system
  position gives 31/32 B (check34 all_B SET). So an "A" output is not by itself
  evidence of A memory: under a degraded context the model defaults to
  ascending "sort" at a substantial rate. The README's reading of R2/R3's 29 A
  as retained precedence tacitly treats every A as memory.
- Check34 stickiness ((ii) B in the CURRENT user turn after three A user turns,
  60/64, equal to fresh B) and check35 TEXT (27/32) show that a current-turn
  instruction overrides the same kind of prior-answer pattern. Combined with R3,
  the established contrast is: current-user-turn cue wins, old-system cue loses.
  That is consistent with recency OR role; neither is isolated.

So the defensible sentence is: "a B cue confined to the old system position
loses to a history of A answers (2/32), while the same cue in the current user
turn wins (27/32); the records do not say whether position, role, or the
demonstrations are doing the work". The README's "retained in-context
pattern/old-position precedence dominates" is compatible with the data but
over-reads it slightly; "stale downstream K/V alone cannot explain the failure"
is correct and is the check's real result.

### 2.3 (low) R4 SWITCH: recompute contributes, paired.

R4 (evict + recompute) 17/32 vs check35 S3/c2 (evict, no recompute) 12/32 on
identical lists and identical prior answers; discordances are one-directional
(R4-only successes at ep 9, 10, 12, 16, 23; S3-only 0; sign test p = 1/32).
Recomputing the stale non-answer columns adds ~5/32 once the answers are gone.
Worth one line in the README; it is the only place recompute shows any effect.

### 2.4 (medium) R4's BACK collapse is structural, consistent with malformed turns, not directly isolated.

After the SWITCH eviction the survivors read "<|im_start|>assistant\n<think>\n\n
</think>\n\n\n<|im_start|>user ..." (assistant header, empty think, no content,
no <|im_end|>); after the BACK eviction there are three such turns. BACK labels
14 A / 11 copy / 7 other match check35 S4/c2 BACK (17/10/5, cue A intact, two
evictions, no A write) and S3 BACK (18/11/3). 9 of the 14 A outputs are
double-bracketed "[[...]]" (hence strict 5/32) — a format-degradation signature.
The BACK label is independent of the SWITCH label (B->A 7, B->copy 7, B->other
3; A->A 6, A->copy 4, A->other 4). The explanation "damage from two evictions'
malformed turns" fits all of this, but the records cannot separate it from
"A-cue-under-recompute is weak after B history" because no arm removes the
answers cleanly in text (whole turns deleted, well-formed). That control is in
2.5.

### 2.5 The cheapest separating test (text-only prefills, no cache ops, ~1 GPU-min per arm at 14 s/episode)

Reuse the 32 S1 lists and teacher-forced S1 answers; five arms, all plain
`prefill(history)` like R3:
1. ROLE: B cue moved from the system slot to a first USER message at the old
   position (system = JSON format only), prior A answers retained. Same
   recency, same demonstrations; only role changes. Compare to R3 (2/32).
2. PATTERN-OFF, CLEAN: B cue in the system slot, SET/HOLD turns deleted as
   whole turns (well-formed history, no empty assistant headers). Compare to
   R4 (17/32) to price the malformed-turn damage, and to check34 all_B SET
   (31/32) as the ceiling.
3. PATTERN-ONLY: no cue anywhere, three teacher-forced A answers, then the
   query. If A is high the demonstrations suffice without any instruction;
   check34's cue-absent single-turn default is copy 64/64.
4. RECENCY at fixed role: B cue as a USER message inserted immediately before
   the SWITCH request (after the A answers) vs arm 1. Same role, same
   demonstrations, only position changes. (Check35 TEXT is nearly this with
   the cue inside the request; 27/32.)
5. Optional: arm 2 with the A answers kept but the empty assistant turns
   removed by deleting the answers' whole turns except one — i.e. one
   demonstration vs two, to see whether pattern strength is graded.

Arms 1, 2 and 3 together give role (1 vs R3), pattern (2 vs R3, 3 vs copy
default) and, by subtraction, recency (4 vs 1). 32 x 5 text prefills is under
the 15-minute cap with margin.

## 3. Requested README edits (numbers stand)

1. Replace the bare "maximum absolute K/V differences 18.37 / 38.06" with the
   distribution (0/1152 layers bitwise equal; median max_abs 1.16/0.48; median
   rms 0.031/0.014; growth with depth) and state that reference magnitude and
   per-position location were not recorded.
2. In the plain-language conclusion, state that R2/R3 do not distinguish
   role, recency, or demonstration pattern, and that R4's 14 A with no A
   content in the cache shows "A" is also a degraded-context default.
3. Add the paired R4 vs S3/c2 line (17 vs 12, discordances 5-0).
4. Say R4 BACK's collapse matches S4/c2 BACK (cue intact) and that 9/14 A
   outputs are double-bracketed, i.e. the eviction structure, not the A write,
   is the proximate cause — with the clean-deletion control still unrun.
