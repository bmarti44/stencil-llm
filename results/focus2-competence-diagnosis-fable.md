# FOCUS-2 competence diagnosis (fable, independent review, 2026-09-05, CPU only)

Scope: the 768 durable competence records under `results/qwen/focus2/outputs/competence/records/`
(freeze 8b86095, registration 7203294), re-read against the frozen banks/templates in
`results/qwen/focus2/freeze/` and the scorer in `src/stencil/focus2.py` (`score`, `answer_shape`,
`target`, `json_equal`). No model launched; no sealed benchmark file opened; no repo edit except
this file. Fit-on = none (diagnosis only).

Method. For every non-success record I re-parsed `output_text` with plain `json.loads`, extracted
`answer`, and applied a value-exact / format-lenient normaliser: strings split on `[,\s]+`; lists of
one-key dicts unwrapped to their values; for the representation default, a bare items list or a
one-element list holding the payload counted as "the payload". Each failure was then binned as
value-exact-lenient, semantically-related-but-wrong (copy / opposite field / tag-as-answer /
first-item-only / letter error / order error), or unparseable. Script kept in the session scratchpad;
all counts below are reproducible from the records with ~60 lines of Python.

## 1. Cell-by-cell table

| Cell | Strict | Need | Format-lenient value-exact (answer only) | ...with top-level tag also right | Dominant failure shape | Diagnosis |
|---|---:|---:|---:|---:|---|---|
| case/default | 7 | 56 | 41 (7+34) | 41 | 34 comma-joined string, 23 single-word string (22 = first item only), 1 concatenation | (b) cue/format: answer shape never stated; "without the canceled transformation" refers to nothing; (a) 22 first-item truncations |
| case/lower | 2 | 52 | 59 (2+57) | 59 (+2 unparseable that are correct lists inside a stray quote) | 60/64 outputs are a space-joined string | (b)/(c) format only; 3 genuine letter errors |
| case/upper | 0 | 52 | 44 (0+44) | 44 | 54 space-joined strings, 10 run-together strings; 17 letter transposition/drop errors, 3 partial uppercasing | (b) format AND (a) genuine: 20/64 wrong letters even after normalising |
| fields/default | 59 | 56 | 59 | 59 | 3 flattened pairs, 2 tag-as-answer | PASS |
| fields/left | 0 | 52 | 48 (0+48) | 10 | 38 `[{"left":x,"tag":t},...]` with no top-level tag, 10 `[{"left":x},...]` + tag, 16 verbatim copies of the payload | (b) cue: "select ... from each record" read as "keep the record, drop the other field"; copy prior in 16 |
| fields/right | 0 | 52 | 10 (0+10) | 0 | 35 `{"answer":TAG}`, 15 `[{"tag":T},{"tag":T},{"tag":T}]`, 4 `{"answer":T,"tag":T}`, 10 whole records + tag | (b) cue: "the right integer" read as "the correct integer" = the tag. 54/64 tag-as-answer |
| representation/array | 55 | 52 | 55 | 55 | 4 `[1,2,3,4]` index arrays, 4 dropped items, 1 permutation | PASS; residual (a) |
| representation/default | 0 | 56 | 0 (22 unwrapped items list; 9 payload-in-list) | 0 | 22 `{"answer":[items]}`, 20 `{"answer":<first item>}`, 12 `{"answer":TAG}`, 9 `{"answer":[{"items":[..]}]}` | (b)+(d): gold demands a nested object `{"items":[..]}` under "answer"; the model never nests a dict in "answer". Only representation has a dict payload; the two list-payload defaults pass 59 and 64 |
| representation/string | 64 | 52 | 64 | 64 | - | PASS |
| sort/ascending | 56 | 52 | 56 | 56 | 5 near-sorted permutations, 3 drop/dup/hallucinate | PASS; residual (a) |
| sort/default | 64 | 56 | 64 | 64 | - | PASS |
| sort/descending | 44 | 52 | 44 | 44 | 18 near-sorted permutations (typically ONE adjacent inversion; 12/18 on the negative side, e.g. -52 before -74), 2 verbatim copies | (a) genuine ordering errors under the registered operand law; not a format problem |

Tag constraint: in every failing cell except fields, the tag was correct in all fails
(case/lower's two exceptions are the unparseable-but-correct lines). The `truncated`,
`repetitive`, `empty`, `placeholder` flags are false on every failing record; the 64-token cap
never bit. No record was unparseable except the two case/lower stray-quote lines.

Aggregate over the 7 failing cells: 395 failures. 193 are value-exact once format is normalised
(answer content right, shape wrong); 145 of those also carry the correct top-level tag. Adding the
31 representation/default outputs that are the payload in an unrequested shape gives 224
"semantically the requested thing, wrongly shaped". The remaining ~170 are wrong content
(copies, tag-as-answer, first-item truncations, letter errors, order errors).

## 2. Verbatim samples (model output next to registered gold)

case/default (gold shape is a JSON list; cue: "Copy the current payload exactly as a JSON value without the canceled transformation.")
- #56 payload `["Agf","Cefugc","Xkvlve"]` gold `{"answer":["Agf","Cefugc","Xkvlve"],"tag":89}` out `{"answer": "Agf,Cefugc,Xkvlve", "tag": 89}`
- #3 payload `["Rkkuyh","Uuho","Xrz"]` gold `{"answer":["Rkkuyh","Uuho","Xrz"],"tag":69}` out `{"answer": "Rkkuyh","tag": 69}`
- #49 payload `["Iocj","Ghrlde","Ixjea"]` gold `{"answer":["Iocj","Ghrlde","Ixjea"],"tag":84}` out `{"answer": "IocjGhrldeIxjea", "tag": 84}`

case/lower (cue: "Convert every word to lowercase, retaining word order.")
- #16 payload `["Kfv","Vrjf","Kinnu"]` gold `{"answer":["kfv","vrjf","kinnu"],"tag":74}` out `{"answer": "kfv vrjf kinnu", "tag": 74}`
- #22 payload `["Mrmpb","Fnnfx","Ohko"]` gold `{"answer":["mrmpb","fnnfx","ohko"],"tag":92}` out `{"answer": "["mrmpb","fnnfx","ohko"],"tag":92}` (stray quote; content correct)
- #6 payload `["Nil","Pjlix","Ocg"]` gold `{"answer":["nil","pjlix","ocg"],"tag":13}` out `{"answer": "nil pjlix ogc", "tag": 13}` (genuine: ocg -> ogc)

case/upper (cue: "Convert every word to uppercase, retaining word order.")
- #56 payload `["Xagi","Vqqrj","Vim"]` gold `{"answer":["XAGI","VQQRJ","VIM"],"tag":92}` out `{"answer": "XAGI VQQRJ VIM", "tag": 92}` (format only)
- #31 payload `["Arir","Bks","Wez"]` gold `{"answer":["ARIR","BKS","WEZ"],"tag":87}` out `{"answer": "ARIR BKs WEZ", "tag": 87}` (partial case)
- #52 payload `["Bzeqxq","Ozwrm","Xuif"]` gold `{"answer":["BZEQXQ","OZWRM","XUIF"],"tag":45}` out `{"answer": "BZEXQOZWRMXUIF", "tag": 45}` (dropped Q, no separators)

fields/left (cue: "Select the left integer from each record, retaining record order.")
- #0 payload `[{"left":30,"right":-85},{"left":40,"right":-88},{"left":64,"right":-36}]` gold `{"answer":[30,40,64],"tag":81}` out `{"answer":[{"left":30,"tag":81},{"left":40,"tag":81},{"left":64,"tag":81}]}`
- #5 payload `[{"left":-2,"right":-73},{"left":-14,"right":-81},{"left":0,"right":-98}]` gold `{"answer":[-2,-14,0],"tag":60}` out `{"answer":[{"left":-2},{"left":-14},{"left":0}],"tag":60}`
- #50 payload `[{"left":-55,"right":-37},{"left":-1,"right":4},{"left":0,"right":43}]` gold `{"answer":[-55,-1,0],"tag":99}` out `{"answer": [{"left":-55,"right":-37},{"left":-1,"right":4},{"left":0,"right":43}],"tag":99}` (copy)

fields/right (cue: "Select the right integer from each record, retaining record order.")
- #47 payload `[{"left":69,"right":-50},{"left":9,"right":-68},{"left":76,"right":-28}]` gold `{"answer":[-50,-68,-28],"tag":52}` out `{"answer":52}`
- #63 payload `[{"left":-55,"right":88},{"left":-73,"right":-32},{"left":3,"right":-16}]` gold `{"answer":[88,-32,-16],"tag":63}` out `{"answer": [{"tag": 63}, {"tag": 63}, {"tag": 63}]}`
- #0 payload `[{"left":13,"right":-47},{"left":71,"right":16},{"left":-73,"right":32}]` gold `{"answer":[-47,16,32],"tag":19}` out `{"answer": [{"left":13,"right":-47,"tag":19},{"left":71,"right":16,"tag":19},{"left":-73,"right":32,"tag":19}]}`

representation/default (cue: "Copy the current payload exactly as a JSON value without the canceled transformation."; payload is a dict)
- #19 payload `{"items":[-7,40,12,-79,10]}` gold `{"answer":{"items":[-7,40,12,-79,10]},"tag":41}` out `{"answer":[-7,40,12,-79,10],"tag":41}`
- #1 payload `{"items":[77,-29,-73,-71,20]}` gold `{"answer":{"items":[77,-29,-73,-71,20]},"tag":21}` out `{"answer":77,"tag":21}`
- #52 payload `{"items":[-10,-67,-91,-4]}` gold `{"answer":{"items":[-10,-67,-91,-4]},"tag":77}` out `{"answer": [{"items":[-10,-67,-91,-4]}],"tag":77}`

sort/descending (cue: "Sort the integers from largest to smallest.")
- #4 payload `[-74,22,49,28,-58,-52]` gold `{"answer":[49,28,22,-52,-58,-74],"tag":72}` out `{"answer": [49,28,22,-52,-74,-58], "tag": 72}`
- #26 payload `[-95,39,-83,-36,-10]` gold `{"answer":[39,-10,-36,-83,-95],"tag":76}` out `{"answer": [39, -36, -83, -95, -10], "tag": 76}`
- #7 payload `[8,-66,-17,67,-55,-68]` gold `{"answer":[67,8,-17,-55,-66,-68],"tag":34}` out `{"answer": [8, -66, -17, 67, -55, -68], "tag": 34}` (copy)

## 3. What the prompt actually says, and where it is defective

The rendered request is (verbatim from a record's `input_text`):

```
<|im_start|>system
Follow the live task rule. Keep earlier facts for later requests.<|im_end|>
<|im_start|>user
<family cue line>
Output compact JSON with "answer" and integer "tag", without prose or unrequested keys.
Keep tag equal to NN.
Additional requested keys: none.
Process this payload: <payload>
Additional requested keys: none.<|im_end|>
```

Defects visible in the records:
1. The schema line never states the shape of `answer`. The model defaulted to a string for
   every word-list task (case: 178/192 outputs are strings) and to record-shaped objects for fields.
   The scorer (`answer_shape` + `json_equal`) is strict on shape, so the cue and checker disagree
   on 193 answers whose content is right. This is a template/checker mismatch (b)+(c), not
   incompetence.
2. "the right integer" is ambiguous ("correct"); 54/64 fields/right answers are the tag. (b).
3. "Copy the current payload exactly as a JSON value without the canceled transformation" is
   rendered in competence where nothing was canceled; for a dict payload the model unwraps the
   list, returns the first item, or returns the tag. For list payloads the same cue works (sort 64,
   fields 59) but for the case list it degrades to comma-strings and single words. (b), and for
   representation also (d): the dict payload is the odd one out and its default gold requires a
   nesting the model never produces.
4. `Additional requested keys: none.` is rendered twice (once inside `live_rules`, once in the
   request obligations). Harmless but sloppy; dedupe.
5. Checker: `json.loads` is whitespace-tolerant, so `{"answer": [-2, -24, 3, 57], "tag": 62}`
   parses fine; the checker is not at fault for spacing or key order. The only checker-side
   strictness that bites is the shape law (list of str / list of int / nested dict), which is a
   design choice, not a bug. The two stray-quote case/lower lines are model output errors.

Genuine model incompetence (a), after normalising format: case/upper letter errors 20/64;
case/lower 3/64; sort/descending 18-20/64 ordering errors; sort/ascending 8/64;
representation/array 9/64; the 22 case/default first-item truncations and the 16 fields/left copies
are prior-driven behaviour under an underspecified cue and are best read as (b).

## 4. Salvageability with a prompt/checker fix only (no model change), from the records alone

- case/lower: YES. A format-lenient checker (accept a whitespace/comma-separated string of words,
  or state "as a JSON array of strings" in the cue) gives 59/64 on the existing records (61 with
  stray-quote repair); threshold 52. Only cell where the records already prove the fix.
- case/upper: NO. Even fully lenient, 44/64 < 52; 20 answers have wrong letters (transpositions,
  drops, partial case) in 3-6-letter nonsense words. This is tokenisation-level incompetence on
  random strings, independent of format.
- case/default: NO from records (41/64 < 56); the 22 first-item truncations need a cue change
  whose effect the records cannot show.
- fields/left: NO from records (48/64 < 52 even unwrapping dict-wrapped values); 16 copies.
  fields/right: NO (10/64). Both need a cue rewrite (avoid "left/right" wording; e.g. keys "a"/"b"
  with cue 'Return the list of the values stored under key "a", one per record') and a fresh run.
- representation/default: NO. At most 31/64 even accepting any faithful rendering of the payload;
  the family's default is structurally defective while the payload is a dict.
- sort/descending: NO by checker; the 18 order errors are real. See section 6 for the operand
  hypothesis.

Consequently no family clears all its cells (A, B, default) from the records alone; the four-family
leg as registered cannot be rescued by rescoring. Rescoring under a changed checker law would also
be a post-outcome change and cannot count as competence for FOCUS-2 itself.

## 5. Minimal FOCUS-2b design with a high-probability competence pass

Use only sort. Every other family has at least one cell that fails even under lenient scoring.

- Family: sort, directions ascending/descending, default = copy. (Optionally add case/lower vs a
  second lowercase-family direction only if a design exists whose other direction is not
  uppercase; the records give no such evidence, so do not.)
- Operand law: `rng.sample(range(-20, 21), rng.randint(5, 8))`, rejecting already-sorted lists and
  deduplicating by unordered set, i.e. the check-31/34 law. Evidence: with that law and Qwen3-4B
  greedy, descending scored 30/32 (check 31, user cue) and 60/64 (check 34 all_B, system cue);
  ascending 27/32 and 59/64. Under the registered law (`range(-99,100)`, 4-6 items) descending is
  44/64 and 18/20 failures are single adjacent inversions, 12 of them among two-digit negatives.
  Length is not the driver (checks used 5-8 items); magnitude is the only law difference left.
- Cue wording (state the shape, keep the tag):
  - ascending: "Sort the integers from smallest to largest."
  - descending: "Sort the integers from largest to smallest."
  - default (CLEAR): "Return the payload list unchanged." (drop "without the canceled
    transformation"; the sort default already scored 64/64 under the current wording, so this is
    a clarity change, not a rescue)
  - schema: 'Output compact JSON of the form {"answer":<JSON array of integers>,"tag":<integer>};
    no prose, no other keys.' Render obligations once.
- Checker law: unchanged exact-value law (`json_equal` on the integer list, tag exact), which the
  records show the model can meet for lists (sort/ascending 56, sort/default 64, representation
  array 55). Keep the whitespace-tolerant parser; no value-lenient rescue.
- Counts: with one family the registered N=256 final bank becomes 128 per direction (or keep 256
  = 64/direction x 2 delays x 2); thresholds 52/64 per direction cell and 56/64 default remain.
- Expected pass probability: if descending returns to the check-34 rate (60/64 = 0.94), P(>=52/64)
  ~ 0.99; at check-31's 30/32 = 0.94 likewise; at a pessimistic 0.85 it is ~0.85. Ascending
  already passes under the harder law (56/64). This is a projection from prior records, not a
  measurement; FOCUS-2b still needs its own competence run, since the registered law forbids
  reuse of these outcomes.

## 6. sort/descending 44/64 vs check 31 (30/32) vs check 34 (60/64): what differs

| | check 31 | check 34 all_B single-shot | FOCUS-2 competence |
|---|---|---|---|
| Operand law | range(-20,21), 5-8 items, not pre-sorted, seed 31031 | range(-20,21), 5-8 items, seed 34034 | range(-99,100), 4-6 items, not pre-sorted, seed 9053702 |
| Cue text | "Sort these integers in descending order." (user) | "Sort the numbers from largest to smallest." (system context, after a filler sentence) | "Sort the integers from largest to smallest." (user, first line of the rules block) |
| Output demanded | "Output only a JSON array." bare array | system "Respond with only a JSON array of integers." + user "Process these integers. Output only a JSON array." bare array | object `{"answer":[...],"tag":NN}` plus "Keep tag equal" and obligations lines |
| Delay | none | none (single-shot) | none (competence delay = 0) |
| Decode | greedy, 48 new tokens | greedy, 64 | greedy, 64 |
| Result | 30/32 desc, 27/32 asc | 60/64 desc, 59/64 asc | 44/64 desc, 56/64 asc |

Delay is not a factor in any of the three. The object wrapper and tag line are tolerated
(ascending 56/64 and default 64/64 under the same wrapper), and the cue wording is near-identical
to check 34's. The one systematic difference that lines up with the failure mode (near-sorted
lists with one inversion, mostly among two-digit negatives, 12/18) is the operand magnitude range.
The records cannot prove causation without a run; they do rule out format, delay, truncation and
the tag constraint.

## 7. Bottom line

The competence miss is roughly half specification (cue never states the answer shape; "right" is
ambiguous; the representation default demands a nested object) and half real incompetence
(uppercasing random strings, descending sort of two-digit negatives). Only case/lower would pass on
rescoring. A one-family sort-only FOCUS-2b with the check-31/34 operand law and an explicit
answer-shape line is the minimal design the existing records support; it must be re-registered and
re-run, not rescued from these outcomes.
