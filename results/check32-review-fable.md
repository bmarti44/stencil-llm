# Review of quick check 32 (Q4, operand-free KV packet transplant) — fable, one round, CPU only

Scope: results/quick-checks/check32-kv/README.md (fixed reading + Results), 4b/ and 1.7b/
summary.json, validation.json, records.jsonl (1,920 each), episodes.json, extraction.jsonl,
packet-stats.json, packets-fp32.pt; scripts/focus_check32_kv.py (sha256 matches
rerun-provenance.json and both summaries); commit d3b0283. No model launched; no sealed
benchmark file read. Analysis scripts lived in the scratchpad only.

## Verdict: ACCURATE-WITH-CORRECTIONS

Every number in the README's two arm tables, both residual tables, and both packet-statistics
tables recomputes exactly from the raw records / tensors. The INELIGIBLE reading is correctly
applied. The corrections concern interpretation (what the near-identity of packets does and does
not show, and what the text bar's weak SWITCH means), not arithmetic.

## Recomputed from raw records (both trunks)

- Records: 1,920 per trunk = 6 arms x 64 episodes x 5 decisions; all (arm, episode, step) keys
  unique; decision denominators are 64 everywhere (no partial arms). Bank: 320 lists, all
  unordered sets unique, lengths 5-8, values in -20..20, none ascending or descending; every
  record's `values` matches episodes.json.
- Arm counts (4B): correct/swapped/off/layers_ge12 SET/HOLD/SWITCH/BACK 0/0/0/0, CLEAR 64,
  impositions 0, breakage 0; shuffled breakage 64/64, induction 0; text SET 59, HOLD 64,
  SWITCH 33, BACK 62, joint 29, strict joint 27, breakage 1. (1.7B): text SET 46, HOLD 50,
  SWITCH 14, BACK 50, joint 6; shuffled CLEAR copy 60/64, breakage 64/64. All match the README.
- Token-history integrity: recomputed history_sha256 and cache_length_after for all 384
  episode/arm sequences per trunk from prefix + filler + prompt + generated + EOS/forced-end +
  trailing ids: 0 mismatches on either trunk.
- Packet writes: every non-text, non-HOLD record carries packet_write with positions [80..83]
  and layers 0..L-1 (12..L-1 in layers_ge12); task is A/B/A/OFF (B/A/B/OFF in swapped) as
  designed; HOLD has packet_write=None and hold_packet_bitwise_retained=True in all 384 HOLD
  records per trunk; shuffled writes are kind=random. CLEAR audits: 36 (28) layers per record,
  packet_bitwise_equal and packet_max_abs=0 for K and V in every layer of every arm — the
  restore claim is verified bitwise.
- Whole-cache residuals at CLEAR: outside maxima match the README tables to the printed digits
  (e.g. 4B correct K 23.539/V 31.5625, shuffled 91.17/96.125, off 1.3125/2.605, text 1/2.25).
  Whole-cache-unequal episodes: correct/swapped/shuffled/layers_ge12 64/64, off 2/64, text 1/64
  on both trunks. This is the only direct evidence that the packet write reached the model: the
  packet-arm caches diverge from the OFF shadow at every downstream position in every episode,
  far above the batch-row nondeterminism floor seen in the off/text controls.
- Packets: packets-fp32.pt sha256 matches summary.json; all per-layer K/V norms and the joint
  cosine(A,B) in packet-stats.json recompute from the tensors (0 mismatches). Layer 0 A==B==OFF
  exactly, as it must (layer-0 K/V depends only on token and position).
- Extraction: 96 cues, 32 per task, all unique, no digit in any cue, every donor prompt is 84
  tokens with the suffix ids [576, 2266, 374, 5527] at 80..83; no extraction cue string appears
  in any packet-arm test prompt. Operand-free and disjoint as claimed. Note (not a defect): the
  text bar's BACK cue "Sort the numbers from smallest to largest." is verbatim one of the 32 A
  extraction paraphrases; harmless because nothing is fitted, but the README's "separate" should
  be read as separate from the packet-arm prompts, not from the text-bar cues.

## Correction 1: "packets near-identical (cosine >= 0.99)" is a misleading statistic

The README's cosine is over the concatenated flattened K and V of the four columns; K norms
(100-1000) dominate V norms (2-340 on 4B), so the value is essentially the cosine of post-RoPE
keys of four identical tokens at identical positions and is near 1 by construction. Minimum
joint cosines are actually 0.9877 (4B, layer 20) and 0.9803 (1.7B, layer 27), so ">= 0.99 at
every layer" is not literally true either, though the README table itself is correct.

Recomputed geometry that is informative (fp32, per layer > 0):
- V-only cosine(A,B): 0.97-0.999 (4B), 0.979-0.9996 (1.7B).
- Cue-induced displacement relative to OFF, ||A-OFF||/||OFF||: V 0.04 (layer 1) rising to
  0.45-0.60 in 4B layers 14-22 (0.50 at 1.7B layer 15). The suffix columns DO carry a large
  cue-dependent component; they are not position/token-only.
- cosine(A-OFF, B-OFF): 0.85-0.95 on both trunks at every layer >= 2, for both K and V. The two
  cues move the suffix columns in nearly the same direction ("an instruction is present").
- Task-discriminating component ||A-B||/||OFF|| in V: 0.03 (layer 1) to 0.27 (4B layer 16),
  0.22 (1.7B layer 27); typically 0.10-0.20 at mid layers.

So the packets are neither near-identical nor purely a design artefact of "the suffix attends to
the cue only weakly": the suffix attends to the cue strongly enough to shift its V by ~half its
norm, but A and B produce ~90%-aligned shifts. That is the same collinearity pattern the
extracted-vector family showed in check 31 (cosine 0.89-0.98): averaged, operand-free cue
representations encode "instruction present" much more than "which instruction".

## Correction 2: what the null result does and does not close

- Behavioural effect of the packets is exactly zero, not merely below threshold: in
  correct, swapped and layers_ge12 the generated token ids are identical to the off arm's in
  320/320 decisions on both trunks, and every one of those outputs is an exact copy of the input
  (label OFF 320/320). There is no partial ordering effect to look for; ordering statistics are
  moot. Meanwhile the write channel is demonstrably live (downstream residuals 23-96 in every
  episode; shuffled packets of matched norm break 64/64). The model reads the four columns, but
  the extracted content of those columns does not move the argmax at all.
- The check therefore cannot separate "four neutral-suffix columns cannot carry a task" (design)
  from "this trunk has no transplantable latent instruction" (trunk property), because it lacks
  the positive control that would anchor the surgery: transplanting the donor's actual cue
  columns (the ~10-14 K/V columns of the cue tokens at their own positions) into the same
  recipient. If cue-column transplant induces the task, the surgery and reading path are sound
  and only the summary-in-four-columns design failed; if it does not, the surgery/position
  layout itself is broken (or the "Process these integers" query cannot be overridden by any
  cache-side instruction) and the packet family is untested rather than closed. Cost: one arm,
  ~8 GPU-min on 4B.
- Recommended wording: the operand-free four-column packet family is closed as executed; the
  broader "instruction lives in the cache and can be transplanted" hypothesis is not yet
  disconfirmed because no cache-side positive control exists.

## Correction 3: the text bar's weak SWITCH is mostly task difficulty, not task stickiness

Label breakdown of the 64 text-arm SWITCH outputs (target B = reverse input order):
- 4B: B 33, other 23, A 7, copy 1. Of the 23 "other", 22 are permutations of the input
  multiset; nearest-order by Kendall tau: reversed 12, ascending 6, copy 4; mean tau vs
  reversed +0.41, vs ascending -0.03. Typical failures are partial reversals (pairwise swaps,
  one element misplaced), i.e. failed executions of B.
- 1.7B: B 14, other 41, A 8, copy 1. Of the 41 "other", 34 are permutations; nearest reversed
  20, ascending 14; mean tau vs reversed +0.61.
- Only 7/64 (4B) and 8/64 (1.7B) SWITCH outputs are the previous task A. That is the ceiling of
  any "stickiness" effect (11-13%), and even that is confounded: in this design the A cue sits
  in the SYSTEM prompt for the whole episode, so SWITCH pits a user-turn B instruction against a
  standing system-prompt A instruction (system/user precedence), not just against retained
  history. BACK (62/64) is high because A is the easy task AND agrees with the system prompt.
- SET 59 vs SWITCH 33 vs BACK 62 is therefore primarily an A-vs-B difficulty asymmetry.
  Corroboration: 1.7B fails A itself in 18/64 SET decisions (10 of them near-ascending
  permutations, tau 0.89), so its 14/64 B is expected from competence alone; the queue note
  already records 1.7B cannot do descending (10/32).
- The stickiness question is real but not answerable from this data; the missing cell is B
  first, fresh context, no A in the system prompt. A worthwhile quick test is tiny (2 arms x 64
  one-shot decisions: B-first fresh vs B-after-three-A-turns with the A cue in a user turn, not
  the system prompt; ~3 GPU-min on 4B). If B-first fresh is also ~33/64, stickiness is nil and
  the bar was simply set with a task the trunk cannot do at 48/64; if B-first is ~55+/64, there
  is a genuine retained-history effect worth registering. Either outcome also fixes the
  eligibility bar for any Q5 successor: as designed, a 48/64 joint bar with B = reverse-order
  cannot be met by 4B (29/64) or 1.7B (6/64) with plain text, so every future packet check
  built on this task pair will be INELIGIBLE regardless of the packet.

## Minor notes

- README "an initial audit assumption of bitwise-equal text replay was rejected by the measured
  control" is confirmed: off arm 2/64 and text 1/64 whole-cache-unequal episodes with residuals
  up to 2.6 (4B) / 27 (1.7B) V on identical token rows. This floor is disclosed correctly, but
  1.7B's floor (27.3 V) is a third of the correct-arm maximum (96.5), so the 1.7B residual table
  should not be read as a clean measure of packet propagation.
- Runtime arithmetic: 47.93 + 25.80 = 73.73 vs 73.74 stated (transition time; fine).
- GPU precheck, prior-abort archive, script hash and reading hash all match provenance.

## Ten-line summary

1. ACCURATE-WITH-CORRECTIONS: every tabulated count, residual and packet statistic recomputes exactly from raw records (1,920/trunk, denominators 64, histories hash-verified, restore bitwise exact at all layers, all writes at [80..83] with the designed task/layers).
2. Packets induced literally nothing: correct/swapped/layers_ge12 outputs are token-identical to the off arm in 320/320 decisions on both trunks (all exact copies); no partial ordering effect exists.
3. The write channel is live (downstream residuals 23-96 in 64/64 correct episodes; norm-matched random packets break 64/64), so the null is about packet content, not a failed write.
4. "Near-identical, cosine >= 0.99" is an artefact of K-dominated joint cosine (min actually 0.988/0.980); V-only cosine 0.97-0.999; cue displacement is large (||A-OFF||/||OFF|| up to 0.6 in V) but A and B displacements are 85-95% collinear; discriminating component ||A-B||/||OFF|| <= 0.27.
5. So the design is not "suffix ignores the cue"; it is "averaged operand-free cues encode instruction-present far more than which-instruction" — the check-31 collinearity pattern again.
6. Family status: the four-column operand-free packet is closed as executed; the cache-transplant hypothesis is NOT disconfirmed because no positive control (transplant the cue columns themselves, ~8 GPU-min) anchors the surgery.
7. Text-bar SWITCH weakness is mostly B-task difficulty: 4B SWITCH failures are 23 "other" (22 permutations, nearest-order reversed 12, tau +0.41) vs only 7 A; 1.7B 41 other vs 8 A; 1.7B also fails A at SET 18/64.
8. Any stickiness is <= 11-13% and confounded by the A cue living in the system prompt (system-vs-user precedence), so SET 59 / SWITCH 33 / BACK 62 is not evidence of retained-history task stickiness.
9. Stickiness is worth one tiny quick test (B-first fresh vs B-after-A with A in a user turn, ~3 GPU-min) mainly because the 48/64 joint text bar with B = reverse-order is unreachable by either trunk and will make every successor INELIGIBLE by construction.
10. 1.7B mirrors 4B on all points; its replay-control floor (V 27.3) is a third of its correct-arm residual maximum (96.5), so its residual table is less informative than 4B's.
