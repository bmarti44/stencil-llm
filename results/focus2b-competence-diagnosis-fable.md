# FOCUS-2b competence diagnosis (fable, independent review, 2026-09-05, CPU only)

Scope: the 192 durable competence records under `results/qwen/focus2b/outputs/competence/records/`
(Amendment 1, freeze f1d32f1, registration 2c18cda; certificate INELIGIBLE: descending 48/64 vs bar 52,
ascending 56/64, default 64/64), re-read against `results/qwen/focus2b/freeze/section.md`,
`src/stencil/focus2.py` (TEMPLATES, `canonical`), the check-31 records
(`results/quick-checks/focus1-probe/4b/records.jsonl`) and the check-34 records
(`results/quick-checks/check34/4b/records.jsonl`), plus the FOCUS-2 competence records for the same trunk.
Token strings were decoded with `models/qwen3-4b-hf/tokenizer.json` (frozen hash aeb13307). No model
launched; no sealed benchmark file opened; no repo edit except this file. Fit-on = none (diagnosis only).

## 1. The 16 descending failures, verbatim

Prompt for every descending fixture (only tag and payload vary):

```
<|im_start|>system
Follow the live task rule. Keep earlier facts for later requests.<|im_end|>
<|im_start|>user
Sort the integers from largest to smallest.
Output compact JSON of the form {"answer": <JSON array of integers>, "tag": <integer>}; no prose or unrequested keys.
Keep tag equal to NN.
Additional requested keys: none.
Process this payload: [11,-5,-19,-18,3,20]<|im_end|>
<|im_start|>assistant
<think>

</think>

```

| # | payload (as rendered) | expected answer | model `answer` | class | first wrong index / len |
|---|---|---|---|---|---|
| 0:0 | `[-5,3,16,-12,-6]` | `[16,3,-5,-6,-12]` | `[16,3,-5,-12,-6]` | one adjacent inversion (negatives) | 3/5 |
| 0:9 | `[3,-11,-10,-6,-19,9]` | `[9,3,-6,-10,-11,-19]` | `[9,3,-1,-10,-6,-19]` | wrong values: `-11` -> `-1`, `-6` displaced | 2/6 |
| 0:14 | `[15,-5,5,1,0,-17,-3]` | `[15,5,1,0,-3,-5,-17]` | `[15,5,1,0,-1, -17]` | wrong values: `-3,-5` -> `-1` (item dropped) | 4/7 |
| 0:18 | `[2,-12,17,-17,-4,11,-20]` | `[17,11,2,-4,-12,-17,-20]` | `[17, 11, 2, -1, -4, -17, -20]` | wrong values: `-12` -> `-1`, misplaced | 3/7 |
| 0:20 | `[-3,-12,-16,9,2,-2,17,-8]` | `[17,9,2,-2,-3,-8,-12,-16]` | `[17,9,2,-2,-8,-12,-16,-3]` | one element displaced (`-3` to end; 3 inv) | 4/8 |
| 0:22 | `[-8,17,-9,-7,20,-18]` | `[20,17,-7,-8,-9,-18]` | `[20,17,-7,-9,-18,-8]` | one element displaced (`-8` to end; 2 inv) | 3/6 |
| 0:27 | `[16,-12,-7,17,14,-15]` | `[17,16,14,-7,-12,-15]` | `[17,16,14,14,-12,-15]` | wrong values: `-7` -> duplicate `14` | 3/6 |
| 0:29 | `[0,-20,3,-3,-11,-1,9,-13]` | `[9,3,0,-1,-3,-11,-13,-20]` | `[9,3,0,-1,-3,-11,-20,-13]` | one adjacent inversion (`-20,-13`) | 6/8 |
| 0:33 | `[-2,7,8,-8,-10,1,-19]` | `[8,7,1,-2,-8,-10,-19]` | `[8,7,1,-2,-10,-19,-8]` | one element displaced (`-8` to end; 2 inv) | 4/7 |
| 0:37 | `[15,8,-11,6,-3,1]` | `[15,8,6,1,-3,-11]` | `[15,8,6,-3,-11,1]` | one element displaced (`1` to end; 2 inv) | 3/6 |
| 0:38 | `[-4,-16,-5,18,-7,16,-17,5]` | `[18,16,5,-4,-5,-7,-16,-17]` | `[18,16,5,-4,-7,-5,-16,-17]` | one adjacent inversion (`-5,-7`) | 4/8 |
| 0:45 | `[8,-11,11,-14,4,5,9,-13]` | `[11,9,8,5,4,-11,-13,-14]` | `[11,9,5,4,8,-11,-13,-14]` | one element displaced (`8`; 2 inv) | 2/8 |
| 0:46 | `[-15,3,1,11,-14]` | `[11,3,1,-14,-15]` | `[11, 3, 1, -15, -14]` | one adjacent inversion (`-14,-15`) | 3/5 |
| 0:57 | `[-3,-8,-12,-11,18,17]` | `[18,17,-3,-8,-11,-12]` | `[18,17,12,11,8,3]` | wrong values: all four minus signs dropped | 2/6 |
| 0:60 | `[-5,-20,-13,-4,-12]` | `[-4,-5,-12,-13,-20]` | `[-5, -4, -12, -13, -20]` | one adjacent inversion (`-4,-5`) | 0/5 |
| 0:61 | `[7,-7,-15,-1,13,-10]` | `[13,7,-1,-7,-10,-15]` | `[13,7,-7,-10,-15,-1]` | one element displaced (`-1` to end; 3 inv) | 2/6 |

Tag correct in 16/16; JSON parseable in 16/16; `truncated`/`repetitive`/`empty`/`placeholder`
false in 16/16 (24-36 emitted tokens, EOS 151645 every time). There is no format, copy, or
schema failure among the 16. Note: 0:27 is a *fresh* draw (the retired f86ae560 collision was a
different list); the Amendment-1 rejection machinery is not implicated in any failure.

Classification (16): one adjacent inversion 5; one element displaced to the end of the list 6;
wrong values 5 (three of them `-11`/`-12`/`-3,-5` -> `-1`; one `-7` -> duplicate `14`; one sign
drop on all four negatives); copy 0; format 0; other 0.

Where the error sits: the first divergence from the reference is at a negative element in
14/16 failures, and at index >= len/2 (the second half of the output) in 13/16. Payloads with a
negative majority fail 12/36 vs 4/28 for positive-majority payloads. The eight ascending failures
show the mirror image: 5/8 first diverge at a positive element in the ascending tail
(`..., 20, 9]`, `..., 20, 6, 17]`, `..., 20, 7, 12]`), two are verbatim copies, one hallucinates
`-15`. So the model's errors are late-list errors in both directions; the descending penalty is
larger because the descending tail is the negative block.

## 2. FOCUS-2b frame vs check 34 vs check 31, token by token

| | check 31 (30/32 desc) | check 34 text_B / all_B (60/64 desc each) | FOCUS-2b competence (48/64 desc) |
|---|---|---|---|
| system turn | none | `Respond with only a JSON array of integers.\nThe room is quiet. The room is still.\n` + 42 space tokens + cue (`Sort the numbers from largest to smallest.` as text in text_B; as a transplanted KV packet in all_B) + ` The context is ready` | `Follow the live task rule. Keep earlier facts for later requests.` |
| user cue | `Sort these integers in descending order.` | `Process these integers.` (cue lives in the system turn) | `Sort the integers from largest to smallest.` |
| output demand | `Output only a JSON array.` | `Output only a JSON array.` | `Output compact JSON of the form {"answer": <JSON array of integers>, "tag": <integer>}; no prose or unrequested keys.` + `Keep tag equal to NN.` + `Additional requested keys: none.` |
| payload line | `Integers: [-1, 4, 15, 16, 7, -17]` (Python `json.dumps` default, `", "`) | `Integers: [-9, 16, -1, 1, 9, 19, 12]` (same) | `Process this payload: [19,-17,13,-18,-16,1,20]` (`canonical`, separators `","`) |
| payload tokens | `' [-' '1' ',' ' ' '4' ',' ' ' '1' '5' ... ',' ' -' '1' '7' ']'` | identical scheme | `' [' '1' '9' ',-' '1' '7' ',' '1' '3' ',-' '1' '8' ',-' '1' '6' ',' '1' ',' '2' '0' ']'` |
| assistant prefix | `<think>\n\n</think>\n\n` | same | same |
| decode | greedy, 48 max | greedy, 64 max | greedy, 64 max |
| prompt length | ~40 tokens | 127 tokens | 104 tokens |
| tool_response / memo / facts framing | none | none | none at competence (all 192 records are single SET requests; `tool` does not occur in any `input_text`) |
| model output format | spaced array 32/32 | spaced array 63/64 | spaced array 24/64 desc, 60/64 asc, 0/64 default (compact copy) |

Three things differ between the ~0.94 frames and the FOCUS-2b frame: (i) the payload is rendered
compact, so every negative number is tokenized as the merged token `,-` followed by digits instead
of `,` `␠-` digits; (ii) the answer is wrapped in `{"answer": [...], "tag": N}` with the tag and
obligations lines; (iii) the system prompt is a generic "live task rule" sentence rather than
"Respond with only a JSON array of integers." Cue wording is not a candidate: check 34 text_B used
the same "largest to smallest" wording at 60/64, and check 31 used "descending order" at 30/32.
Delay, truncation and the tag constraint are ruled out by the records (section 1).

## 3. Does the frame plausibly cost the 12-point gap?

Yes, and the evidence is now stronger than magnitude. FOCUS-2 (range -99..99, 4-6 items) scored
44/64 and FOCUS-2b (range -20..20, 5-8 items, i.e. the check-31/34 operand law) scored 48/64 under the
same frame; that +4 is not distinguishable from noise (Fisher one-sided p = 0.28). My FOCUS-2 diagnosis
(section 6 there) picked magnitude as "the one systematic difference"; that was the wrong pick, because
it treated the rendering of the payload as identical when it was not. Pooling all descending banks on
this trunk:

- plain-array, spaced-payload frames: check 31 30/32, check 34 all_B 60/64, text_B 60/64, shuffled_B 60/64,
  B_fresh 60/64 = 270/288 = 0.938 (exact 95% lower bound 0.91);
- wrapper, compact-payload frames: FOCUS-2 44/64, FOCUS-2b 48/64 = 92/128 = 0.719 (exact 95% lower bound 0.65);
- Fisher one-sided p = 5e-9; check 34 text_B alone vs FOCUS-2b alone p = 0.003.

The frame difference accounts for the whole ~20-point deficit between FOCUS-2b and the check-34
condition, with the 12-point gap to check 34 sitting well inside it. Which component? The records
cannot separate (i)-(iii) causally, but they favour (i), the compact `,-` tokenization:

- The degradation is direction-specific (descending 48 vs ascending 56 in FOCUS-2b; 44 vs 56 in FOCUS-2),
  while the bare frame shows no direction asymmetry (check 34: 60 vs 59; check 31: 30 vs 27 the other way).
  The wrapper and system prompt are identical across directions, so they cannot by themselves produce an
  asymmetry; the descending tail is the block of negatives that must be emitted as `,-` tokens.
- Three of the five wrong-value failures are two-digit negatives collapsing to `-1` (`-11`, `-12`,
  `-3,-5` -> `-1`), and one drops every minus sign; these are token-boundary errors on negatives, not
  arithmetic errors. Nothing like them occurs in the 32+320 bare-frame descending outputs (their 6 failures
  are dropped items and ordering slips).
- Within FOCUS-2b descending, outputs the model chose to space (`[17, 11, 2, ...]`) succeed 20/24 vs 28/40 when
  it echoed the compact form; suggestive only (post-hoc, conditioned on the output).
- Ascending is also below its bare-frame rate (0.875 vs 0.92-0.94), so (ii)/(iii) probably cost a few points
  on their own; they are not free.

## 4. The single change most likely to clear 52/64

Render the payload with `json.dumps` default separators (`[19, -17, 13, -18, -16, 1, 20]`), i.e. the
exact check-31/34 payload line, and leave everything else frozen (wrapper, tag, obligations, system
prompt, checker). This is a rendering change only: the checker parses with whitespace-tolerant
`json.loads`, gold values are unchanged, the semantic fingerprints (unordered sets) are unchanged, and
the "compact JSON" instruction refers to the model's output, not the payload. It is the smallest
change that restores the one difference shared by all five ~0.94 banks and both ~0.72 banks.

Probability estimate (from the records, not a measurement):
- If the spaced rendering restores the bare-frame rate (0.938), P(>= 52/64) > 0.999; at the pooled
  lower bound 0.91 it is 0.99; at a pessimistic 0.85 it is 0.85.
- If the wrapper/system prompt are the real cause and spacing does nothing, the rate stays ~0.72 and
  P(>= 52/64) = 0.06 (0.16 at the observed 0.75).
- Weighting the tokenization explanation at ~0.65 on the asymmetry and `-1` evidence: P(clear 52/64)
  ~ 0.65 x 0.97 + 0.35 x 0.10 ~ 0.66 for the spacing-only change.

The alternative single change the task names, plain-array output as in check 34 (drop the
`{"answer":..,"tag":N}` wrapper and the tag for sort-only), restores conditions (ii) but keeps the
compact payload; on the same weighting its P(clear 52/64) is ~ 0.35 x 0.97 + 0.65 x 0.15 ~ 0.44, and
it also removes the unchanged-constraint (tag) collateral endpoint and the JSON-object breakage check,
so it is both less likely to work and more costly to the design. Doing both (spaced payload + the
check-31 request line `Sort the integers from largest to smallest. Output only a JSON array. Integers:
[...]`, tag dropped) reproduces the check-31/34 frame up to the system prompt and gives P ~ 0.9, but
at the same collateral cost. Recommendation: spaced payload alone first; it is a one-line change in
`canonical`/`TEMPLATES["request"]`, requires re-freezing (rendered token maps change) and a fresh
competence run under a new registration, and it can be pre-registered as a prompt-frame correction
with this diagnosis as its development evidence. No outcome from the 48/64 run may be reused.

## 5. Would 75% competence make the primary endpoint uninterpretable? Could the bar be 44/64?

Not uninterpretable, but weaker, and the registered margin becomes harder to reach. Y requires all
five post-change answers correct. Under independence the ceiling on Y in the perfect-mechanism arm is
roughly p_desc^2 p_asc for asc-start episodes and p_asc^2 p_desc for desc-start, averaged: 0.75 at
desc 0.94, 0.60 at 0.81 (the current bar), 0.53 at 0.75, 0.47 at 0.69 (44/64). There is no floor
effect at any of these: Y stays far from zero in every arm. Two things do degrade:

1. The mechanism effect is scaled by the competence ceiling, and the >= 5-point (13/256) margin over
   text-restate is absolute. A true 15% mechanism effect nets ~28 episodes at competence 0.94, ~23 at
   0.81, ~21 at 0.75, ~19 at 0.69 (simulation, section 6 note); it still clears 13 on average, but the
   probability of clearing 13 AND the Holm-adjusted exact McNemar drops from ~0.9 to ~0.8, ~0.7, ~0.6.
   A 10% effect drops from ~0.7 to ~0.5, ~0.35, ~0.27.
2. Competence noise adds discordant pairs in both directions. Pairing helps: the same payload and greedy
   decoding are shared across arms, so a list the model cannot sort tends to fail in every arm and lands
   on the concordant diagonal. Section 1 shows the failures are list-specific late-tail slips, which is
   the favourable case for pairing; the simulation assumed only half of the competence noise is shared.

A 44/64 bar (68.75%, exact lower bound 0.58) would have passed this run and would very probably pass a
re-run of the same frame (P = 0.90 at p = 0.75). The trade-off is that it sacrifices roughly a fifth to a
quarter of the primary contrast's power at the pre-registered expectation ("both minus placement-only
bounded by ~10/32", i.e. an effect in the 10-15% band where power is already marginal), it lowers the
Y ceiling to ~0.5 so that "all five correct" reads increasingly as a competence lottery, and it makes
the F11 both-correct / prior-error strata thinner. It would be a legitimate registration if the frame
were kept as is, but it treats a rendering artefact as the model's competence. Fixing the payload
rendering (section 4) is the better trade: it keeps the 52/64 bar (81%, LB 0.71), which the same trunk
has met five times out of five under the spaced frame, and it does not weaken the endpoint.

Two cautions on lowering the bar: (a) the bar was set with a stated rationale (exact 95% LB 0.71 at
52/64); 44/64 gives LB 0.58 and should be registered with that number, not with "75%"; (b) if the bar is
lowered AND the frame is left compact, the descending-tail `-1` collapses and sign drops become part of
the final-run noise in every arm, including CLEAR/NEUTRAL2 defaults that copy the payload (default is
64/64 here because copying compact input to compact output is trivial; that does not transfer to sorted
output).

## 6. Bottom line

The 16 descending failures are all genuine late-list errors (11 single inversions/displacements, 5
corrupted negative values), none format or copy. The registered frame differs from the 30/32 and
60/64 frames in payload rendering (compact `,-` tokens), output wrapper, and system prompt; the frame
as a whole is responsible for the gap (p = 5e-9 pooled), the operand-magnitude hypothesis from my
FOCUS-2 diagnosis is refuted (+4 points, p = 0.28), and the direction asymmetry plus the `-11`/`-12`
-> `-1` collapses point at the compact rendering of negatives. Spaced payload rendering is the single
change most likely to clear 52/64 (~0.66 overall; ~0.99 if the tokenization reading is right). A
44/64 bar would not make Y uninterpretable (no floor effect) but costs 20-25% of primary-contrast
power at the expected effect size and registers a rendering artefact as trunk competence.

Method note: classification and counts are reproducible from the records with ~80 lines of Python
(scratchpad only); the power figures come from a 400-rep simulation with N = 256, arms paired on the
episode, asc competence 0.875, default 1.0, half-shared competence noise, exact one-sided McNemar at
0.05/3 plus the 13-net margin; they are order-of-magnitude guides, not registered numbers.
