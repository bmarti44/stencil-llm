# Check 31 (FOCUS-1 steering feasibility probe) — one-round accuracy review (fable, 2026-09-05)

Scope: results/quick-checks/focus1-probe/{README.md,validation.json,1.7b/*,4b/*}, scripts/focus1_probe.py.
CPU only; no model launched; no sealed input read. Recomputation scripts lived in the scratchpad
(recheck.py, texts.py, more.py); nothing in the repo was edited except this file.

## Verdict: ACCURATE-WITH-CORRECTIONS (corrections are clarifications; no number in the tables is wrong)

## What was recomputed from the raw records (both trunks)

1. Denominators. 432 records per trunk: competence 3x32, steering_off 16, steering 3 layers x 3 alphas x
   2 directions x 16 = 288, delay 2x16. Ids contiguous, no duplicates, 16 distinct examples per arm.
2. Strict scorer. Re-ran `score()` from scripts/focus1_probe.py on every record's saved text/values with
   truncation recomputed as n_generated==48 and the saved rep4: 0/864 mismatches. Every cell's A/D/C/O, B
   and S counts, competence counts, steering_off counts, delay cell and reading recompute exactly.
   The 1.7B initial-summary.json label counts equal the corrected summary.json (scoring correction changed
   only the invalid_json/schema split, as claimed).
3. Correct/swapped/OFF. For every cell, `swapped` for target t equals `correct` for the other direction
   on the same 16 records (same injection, two views), and OFF is the single steering_off set. Confirmed.
4. Leakage. `banks()` re-derived from seed 31031 equals examples.json for both trunks (identical files,
   same sha); extraction.json (96 prompts) is exactly the `vectors` bank; unordered operand sets are
   disjoint across competence/vectors/steering (32+32+16 distinct keys). Operand range is [-20,20].
5. Vectors and cosines. All 12 vectors.pt entries are bitwise equal to mean(with)-mean(off) recomputed
   from extraction-states.pt (n=32 each). Cosines recompute to the README values (0.965020/0.949750/
   0.893702; 0.971285/0.980093/0.973361). Vectors are not massive-activation artifacts: top-5 dims carry
   2-6% of ||v||^2. ||v||/||mean h_off|| is 0.10-0.19, so alpha=2 injects 20-37% of the residual norm.
6. Hook positions. Every steering record has hook_positions == [0..n_generated] (or [0..n-1] when
   truncated), every delay record [0], every OFF/competence record []. Injection is at the final prompt
   token plus every decode position, at the stated zero-based layer input (qwen3.py applies the hook
   when i == layer). This matches the README and the DRAFT v2 actuator definition.
7. Copy default. 1.7B competence cue-absent: 26/32 copy (others: 3 `[{"value":..}]` objects, 1 quoted
   strings, 1 dropped elements, 1 misordered); 1.7B held OFF 12/16; 4B competence cue-absent 30/32
   (2 nested `[[...]]`), 4B held OFF 16/16. Confirmed.

## Lenient re-score: no steering cell leaves 0

A permissive scorer (first `[...]` anywhere in the text, code fences stripped, quoted integer strings and
integral floats coerced) was applied to all 288+32 steering/delay records per trunk: 0 exact ascending and
0 exact descending sequences in every cell on both trunks. The zeros are not a formatting artifact.

Correction 1 (competence wording). README: the string-tolerant diagnostic "recovers 28/32 ascending but
only 10/32 descending" on 1.7B. That is correct for competence-diagnostics.json's definition (valid JSON
with quoted integers). With code fences also stripped the counts are 29/32 asc and 15/32 desc (five desc
answers are exact but wrapped in ```json fences). Either way 1.7B is below the DRAFT v2 gate (>=29/32
EXACT integer arrays per skill; v2's score_reply rejects strings and fenced text), and desc has genuine
value/order errors (e.g. `["18","14","12","6","7","1","-1","-14"]`, `["9","15","3","10","7","5","3"]`).

## Hidden partial effect? None toward the task; the effect is purely on surface format

- Ordering statistics of the parsed output (fraction of ascending adjacent pairs; Kendall tau vs the
  ascending target) do not move from OFF: 1.7B OFF 0.55 / +0.09 vs cells 0.51-0.55 / +0.04-0.10;
  4B OFF 0.51 / +0.04 vs cells 0.42-0.51 / -0.29-+0.04 (the drops come from examples that became
  unparseable, not from reordering). First element equals min/max at the same 4/2 counts as OFF.
- What the injection does change is format: 1.7B -> quoted-string arrays, ```json fences, multi-line
  arrays (the S column); 4B L12 -> nested `[[...]]` (S=8/16 at alpha>=1), L16/L20 -> spaced `[ ... ]`.
  Text changed vs OFF in 4-16/16 (1.7B) and 2-8/16 (4B) records per cell, so the injection demonstrably
  reached the stream; it just does not touch order.
- The effect is direction-invariant: on 4B, asc- and desc-injected outputs are byte-identical 16/16 at
  L12 alpha=1, L12 alpha=2 and L16 alpha=2 (and across alpha 1 vs 2 at L12); on 1.7B they differ in only
  2-5/16 records per cell (11/16 at L12 alpha=2), all differences being format. Consistent with the
  shared "sort-instruction" component (cos 0.89-0.98) dominating both vectors.
- Not hidden but worth stating: the task IS linearly present at the extraction position. Projecting the
  32 asc and 32 desc extraction states onto (v_asc - v_desc) separates them 32/32 pairs at every layer
  with large margin (e.g. 1.7B L16 means 12.6 vs 2.0, sd 0.86; 4B L20 12.6 vs 10.5, sd 0.2). So the
  negative result is about the mean-difference-vs-OFF actuator at alpha<=2, not about the absence of a
  task signal. The contrast direction is untested here and explicitly forbidden by DRAFT v2 ("no
  orthogonalization or replacement contrast"), so it cannot rescue FOCUS-1 as written.

## Does it generalize to the FOCUS-1 DRAFT v2 actuator? Yes; the hold is justified on two grounds

Same trunk (1.7B), same prompts (visible/absent wording identical), same layers {12,16,20} and alphas
{0.5,1,2}, same `mean_difference` at the final prompt token, same injection schedule (final prompt
position + every decode position, never earlier prompt tokens). Deviations: v2 rescales both vectors to
rho=(||v_A||+||v_B||)/2 (norms here differ by <=11%, i.e. an alpha change of <=1.11x, inside the grid);
operands [-9,9] vs [-20,20]; 64 vs 32 extraction lists; max_new 64 vs 48. None plausibly turns 0/16 into
the >=29/32 v2 selection floor.
(a) 1.7B would be INELIGIBLE at v2's competence gate before extraction (0/32 exact per skill; v2 rejects
strings/fences), and v2 forbids a 4B fallback. (b) Even on 4B, which passes the competence gate
(27/32, 30/32), the identical actuator/grid produced 0/16 in all 18 cells with no partial ordering shift.
Caveat: the operand range differs; 1.7B's quoted-string habit was not shown to be range-independent, but
its desc value/order errors are, and (b) does not depend on it.

## Minor notes (no action required)
- scripts/focus1_probe.py (sha 2f98b72a...) differs from 1.7b/execution_script.py (80b3e8e2..., the hash in
  both summaries) exactly by the documented syntax/schema scoring split and tie-break rename; label
  counts, best cell and readings are unchanged under both versions (verified).
- README "Cosine 0.89-0.98" and all table rows verified; validation.json hashes match the files on disk.
