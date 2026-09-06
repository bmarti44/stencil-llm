# Check 44c — one-round accuracy review (fable, 2026-09-06)

Scope: results/quick-checks/check44c/{RESULTS.md, *.json, *-records.jsonl},
scripts/focus_check44c.py (+ frozen copy), data/classifier/model/admission-v2
metadata, data/classifier/review/admission-2-astra-patch.jsonl, and my own
bank data/classifier/heldout/fable-admission-heldout-3.jsonl. CPU only; no
model launched; nothing under data/bench read. All counts below are recomputed
from the journaled records with my own code (IoU, adjacency, cue tests) and the
runner's `match_spans` where the registered metric is involved.

## 1. Verification of the claims

| Claim | My check | Status |
|---|---|---|
| Heldout-3 records == my gold | 357/357 inputs identical (message, role, standing_rules) to the committed bank; 0 offset/text mismatches | verified |
| Overlap micro 247 TP / 71 unmatched preds / 138 misses; P 77.67 % R 64.16 % | 247/318, 247/385 from records; identical with `match_spans` and my own greedy check | verified |
| Exact micro 31.76 / 26.23 % | 101/318, 101/385 | verified |
| C2 and C2+B identical | accepted lists byte-identical on all 357 heldout-3 rows (and heldout-2, SETUP); B added 0 spans | verified |
| Family denominators payload 57 / quoted 36 / non-user 34, all gold-empty 111 | recomputed as gold-empty AND flag (payload = one_off_request, quoted = quoted_or_reported); non-user 34 = all tool/assistant rows, which carry no gold by construction | verified |
| Quoted false admissions 2/36 | fa3-adm-110 ("think of as wisdom", "than a rule I want you to enforce"), fa3-adm-281 ("I mention as background", "than as a rule for you"); both are correctly gold-empty reported sayings; the admitted text is the hedge, not the quoted rule | verified |
| SETUP 36/36 admit, 3/4 supersedes, 10/96 false turns, 14 unmatched preds, 4 template turns | reproduced; see Section 4 for what the 10 turns actually contain | verified |
| Heldout-2 second look 88.89 / 81.16 % | 168/189, 168/207 | verified |
| Freeze before look | heldout-3 blob 05e46d98 committed 08:54 (f06ccdd9); thresholds committed 09:27:38 (fd43ff8f); model-freeze.json utc 13:27:10Z; evaluation-start.json utc 13:27:40Z (30 s after freeze, 2 s after the commit); `evaluate()` refuses to run twice and hashes the freeze before opening the bank | verified from receipts. The bank was readable in the tree for 33 min before freeze; no artifact shows contact and `corpus()` never touches it, but "first opened only in evaluate()" is a statement about the code path, not an independently verifiable fact |
| Audit patch: 122 rows changed, 5 dropped, spans 1289 -> 1396, gold-empty 769 -> 668 | 122 patch rows: 110 add spans (+109 net), 7 remove one span each, 5 drop (4 had 0 spans, 1 had 2). 1289 + 109 - 2 = 1396; corpus.json kimi2 = 1572 rows, 1396 spans, 668 empty | verified |
| Patch quality (spot) | the 7 removals are all correct under LABELS.md (single-reply "For this task, ...", meta "This applies to the whole presentation", "I'll keep them brief going forward" is a user commitment about the user); the 5 drops are unfilled `[paste]`/`[500 words of text]` placeholders | reasonable |
| DEV threshold t = 0.7273 at 5/250 | dev-threshold-derivation.json: next-lower candidate 0.7262 admits 6/250; seeds 1/2 give 0.605/0.700 with 5/250 each | verified; RESULTS correctly notes the one-message sensitivity |
| Ceiling 385/385 | token runs are disjoint and nonempty for every gold span; no overflow (max 512 tokens never reached; median positive message 39 tokens) | verified, and irrelevant to the outcome (Section 2) |

No arithmetic error. The numbers are what the records contain.

## 2. Why recall fell to 64 % and exact match to 26 % on this bank

### 2a. The 138 misses, segmented

| Segment | Spans | Note |
|---|---:|---|
| (b1) whole-message miss: message has gold, zero decoded runs at all | 44 | 30 messages; any_rule_score = 0 |
| (b2) span miss: no decoded run touches this gold, but other runs exist in the message | 46 | almost all in two/three-rule lists |
| (c) threshold band: a decoded run overlaps the gold but its confidence < t | 43 | best confidence 0.51-0.72 (t = 0.727) |
| (a) merge: an accepted run overlaps this gold but was consumed by another gold | 5 | one run spanning two adjacent rules |
| total | 138 | |

So 90/138 (65 %) are "never decoded" and are untouchable by any threshold or
decoder change; RESULTS' 291/385 = 75.6 % unthresholded figure (my count: 247 +
43 threshold + 1 of the merges re-matched = 291) is the true ceiling of this
trained tagger, 9.4 points below the 85 % bar. The post-hoc sweep confirms it:
t = 0 gives 291/385 = 75.6 % recall at 63.7 % precision and 4/111 gold-empty
admissions; t = 0.60 gives 72.7 %; t = 0.80 gives 57.7 %. No threshold passes.

Per category (my bank's field): two_rules 136/244 = 55.7 %, buried_rule
38/54 = 70.4 %, rule_plus_payload 73/87 = 83.9 %. By rules per message:
1 rule 79 %, 2 rules 70 %, 3 rules 37 %. Whole-message misses: 47 messages
(19 two_rules, 15 buried, 13 rule+payload), 25 of them flagged hard.

### 2b. Boundary errors (the exact-match collapse), with IoU bands

Of the 247 overlap matches, 101 are exact and 146 are boundary-imperfect:

| IoU band | Matches |
|---|---:|
| [0.9, 1) | 26 |
| [0.75, 0.9) | 39 |
| [0.5, 0.75) | 45 |
| [0.25, 0.5) | 13 |
| (0, 0.25) | 23 |

Direction: 83 over-extensions, 60 truncations, 3 shifted. Of the 62
over-extensions where the prediction starts before the gold and ends at or
after it, 54 (87 %) prepend exactly a framing cue ("From now on, ", "Going
forward, ", "For all future X: ", "For forecast text, "). This is a **label
convention conflict, not a model error**: the fit corpus puts the framing cue
INSIDE the gold span (529 spans start with one; only 182 have it immediately
before the span), whereas my bank excludes it (4 spans start with one; 98 have
it immediately before). The 44b review already flagged this as a
"labeling-convention/coverage gap". Exact-match 26 % is therefore mostly a
measurement of the convention mismatch; it should not be read as boundary
incompetence, and RESULTS should say so (Section 5).

Truncations (60) are real: they come from O-gaps inside a rule (the head emits
O on a mid-rule token, e.g. "record depths as metres below the" / "dat" /
"below ground surface"). Across all gold spans decoded into >= 2 runs (69
spans), the break is an O-gap 235 times and a B-restart 7 times, so the
"adjacent B starts a new span" decode rule is NOT the cause; the token head
simply has no sequence constraint and its per-token decisions are noisy inside
rules it half-recognizes. A gap-merging decoder (join runs across <= k O
tokens) makes things worse at the frozen threshold, because merged runs
average in the low-confidence gap tokens and long merged runs swallow two
rules: k = 1 gives 56.4 % recall, k = 2 48.1 %, k = 3 46.0 % (precision 96-98 %).
Decoder change is not a live hypothesis.

### 2c. The 71 unmatched predictions

| Kind | Count | Note |
|---|---:|---|
| fragment: overlaps a gold already matched by another prediction | 42 | same O-gap fragmentation as above |
| framing-cue fragment adjacent (<= 3 chars) to a gold span | 14 | "for", "For", "going forward,", "for all future patterns", "For food records,", "For all future antenna notes:" — rule text under the FIT convention, non-rule under mine |
| other non-rule text on positive messages | 11 | "the logs", "word", "the", "thing", "mar", "Nobody looked at the", "instructions in any pattern you write", "settling on a mat for five minutes, recall from play", "no jumping on guests" |
| false admissions on gold-empty messages | 4 | the 2 quoted messages x 2 spans each; 0 on payload, 0 on non-user |

So over-extension/fragmentation/convention accounts for 56 of 71 and genuine
false admissions for 15 (11 on positive messages, 4 spans on 2 negative
messages). Precision would be respectable if the tagger emitted one run per
rule; it does not.

### 2d. The underlying cause: rule phrasing the fit data barely contains

Recall by whether the gold span opens with a strong cue word
(always/never/whenever/from now on/for/going forward/keep/until/every/when/don't/...):

| Bank | cue-initial | cue-less |
|---|---|---|
| DEV (in-distribution) | 230/234 = 98 % | 38/52 = 73 % |
| heldout-2 | 137/137 = 100 % | 31/70 = 44 % |
| heldout-3 | 114/131 = 87 % | 133/254 = 52 % |

and by length: <= 5 words 40 %, 6-9 words 57 %, 10+ words 77 % on heldout-3.

Fit corpus composition: 80 % of its 2,889 gold spans are cue-initial (kimi
85 %, kimi2 78 %), 7 % are <= 5 words, and only 43 of 2,179 positive messages
carry three rules. Heldout-3: 34 % cue-initial, 12 % <= 5 words, 34 of 246
positive messages carry three rules, and its typical miss is a terse list rule
("Timestamps in UTC only.", "Weather at the start of the hunt in one line.",
"Flights counted whether or not they connected."). DEV recall of 93.7 % did not
predict 64 % because DEV shares kimi's phrasing distribution; it is not a proxy
for author-disjoint text. The same pattern was visible in heldout-2 (two_rules
59.7 %, cue-less 44 %) and was the stated target of the kimi2 pass; the pass
added multi-rule messages (410 two-rule, 41 three-rule) but kept the cue-heavy
style, so the coverage gap did not close.

Position is not the driver: recall is 75 % for mid-sentence starts vs 51 % for
after-punctuation starts on heldout-3 — the after-punctuation spans are the
terse list items. Buried rules after data blocks account for only 10 of the 44
whole-message-miss spans.

### 2e. The 44b sentence head on the same bank (journaled, no new inference)

The B arm (44b frozen sentence head) was scored on heldout-3 in the same run:
overlap recall 232/385 = 60.3 %, precision 232/234 = 99.1 %, 0/111 gold-empty
admissions; per category two_rules 105/244 (43 %), rule_plus_payload 79/87
(91 %), buried_rule 48/54 (89 %). Its recall loss is entirely candidate
boundaries in list-style multi-rule messages (the 44b splitter ceiling here is
289/385 = 75.1 %; B recovers 232/289 = 80 % of representable spans). The
post-hoc union of both arms' accepted spans reaches 323/385 = 83.9 % at 58.5 %
precision — still below the bar. Measured with the repo's existing frozen
`split_clauses` (not designed against this bank), a clause-level candidate
ceiling on heldout-3 is 340/385 = 88.3 % overlap but only 279/385 = 72.5 % at
IoU >= 0.5 (fit corpus: 96.9 % overlap). At B's 80-95 % recovery of
representable spans, the reachable recall is 71-84 %, below 85 %.

## 3. Plain answers

**(1) NO-GO correctly applied.** All six bars were registered before the look
(README.md in ab977033; thresholds in fd43ff8f; the bank's contents were not
needed for any decision), the arithmetic is right, the matching is the
registered one-to-one maximum-cardinality matching, the family denominators
follow the 44/44b definition (gold-empty AND flag), and no threshold, seed, or
arm was chosen after the look. The NO-GO would stand under every threshold
(ceiling 75.6 %) and under either labeling convention (the convention conflict
moves exact-match, not overlap recall).

**(2) Park.** This line has now failed the same recall bar three times (44:
sentence head; 44b: refit + heldout-2 61 % on two_rules; 44c: token tagger,
55.7 % on two_rules), each time with a prewritten fix that targeted the previous
failure and each time discovering a further phrasing/boundary gap on the next
author-disjoint bank. The candidate hypotheses do not clear Brian's
adequate-proof rule:

- Span-decoding change: refuted above (gap-merge reduces recall; 90/138 misses
  have no run at all).
- Separate boundary model: that IS 44c's token tagger, and it lost to the
  sentence head on precision (77.7 % vs 99.1 %) while gaining only 4 points of
  recall.
- Clause-level candidates + pairwise/sentence head: the strongest option, and
  the sentence head's precision (0/111, 1/154 gold-empty admissions across
  two fresh banks) is genuinely proven. But its measured ceiling with the
  existing clause splitter is 88.3 % overlap / 72.5 % IoU-0.5 on heldout-3,
  which leaves no margin over the 85 % bar once the head's own losses are
  applied, and a splitter tuned to close that margin would have to be designed
  against text it will then be evaluated on. Reaching the bar would also need
  a fourth author-disjoint bank (heldout-3 is now open and heldout-2 already
  motivated a design choice).
- More fit data in the missing style (terse cue-less list rules, three-rule
  messages): plausible but unproven, and it is the third data pass; the
  evidence says each pass covers the previous bank's style, not the next one.

Recommendation: explicit structured entry ships; automatic admission becomes a
later research item with a recorded reopening condition: a fit set whose
measured phrasing profile (cue-initial fraction <= 50 %, >= 10 % three-rule
messages, >= 15 % spans of <= 5 words) is fixed BEFORE fitting, a clause
candidate generator whose one-to-one ceiling is >= 95 % overlap on fit+DEV
multi-rule messages, and a fresh author-disjoint bank. Until then, the
registered use of heldout-3 is regression only.

**(3) Corrections to RESULTS.md** (none change the reading):

- Exact-match numbers need a convention caveat: 54 of 62 leading over-extensions
  and 14 of the 25 positive-message unmatched predictions are framing cues that
  the fit corpus labels as rule text and heldout-3 labels as non-rule. State
  that exact P/R and roughly 14 of the 71 unmatched predictions measure a
  boundary-convention mismatch between fit gold and bank gold; overlap metrics
  and the family rates are convention-independent.
- SETUP "10/96 false-admission turns" should be described: 6 turns contain
  only fragments of correctly recovered rules ("for task S0n0A keep the
  payload sorted in descending order", "from now on", "always sort the payload
  in ascending order"), 3 turns admit template text only ("task rule",
  "conversation tag"), and 1 turn has both. The registered bar counts any
  unmatched span, so FAIL stands, but the sentence "false admissions" overstates
  what happened: payload text was never admitted; 4 turns admitted template
  tokens.
- "B starts a new run even next to B/I" is listed among the decoder caveats,
  but the fragmentation is O-gaps (235 breaks) not B-restarts (7); the caveat
  should not suggest that the adjacent-B rule is what fragments spans.
- Add the journaled B-arm numbers on heldout-3 (60.3 % / 99.1 %, 0/111) — they
  are already in the records and are the most useful fact for anyone deciding
  whether to reopen this line.
- Cosmetic: several numbers lost their leading space ("has357 messages",
  "246 positive messages and111", "268/286").
- Scenario-family sidecar denominators (payload 56, all-negative 92) count
  distinct scenarios, not messages; the text says "scenario upper bounds" but
  should say so explicitly beside the 57/111 message counts to avoid a reader
  taking 56 vs 57 as a discrepancy.

## 4. SETUP false turns, itemised

| Turn | Unmatched spans | Kind |
|---|---|---|
| setup:0:0 | "for task S0n0A keep the payload sorted in descending order" | fragment of recovered gold |
| setup:3:0 | "task rule", "conversation tag" | template |
| setup:3:2 | "A, keep all payloads in ascending order from now on instead" | fragment |
| setup:7:0 | "from now on" | fragment |
| setup:8:0 | "for task S2n0A keep the payload sorted in descending order" | fragment |
| setup:11:0 | "task rule", "conversation tag" | template |
| setup:12:0 | "always sort the payload in ascending order" | fragment |
| setup:13:2 | "conversation tag" | template |
| setup:15:0 | "from now on" | fragment |
| setup:15:2 | fragment + "the" + "conversation tag" | mixed |

Exact SETUP 0/40 is the same O-gap fragmentation (39 truncations, 28 of them at
IoU >= 0.9).

## 5. Limits of this review

Post-hoc segmentation and the cue/length/position tests are diagnostics on an
already-open bank; they are not selections and no threshold or model was
changed. The clause ceiling used the repo's existing splitter unmodified. The
"first opened only in evaluate()" claim is supported by the code path and the
30-second gap between freeze and evaluation-start receipts, not by an external
witness. I authored heldout-3; the framing-cue exclusion and the terse
list-rule style are my authoring choices, made per the bank's field note ("each
span is one rule clause") and without reference to the fit data's convention.
That makes the exact-match numbers partly a measurement of me, which is why
Section 3(3) asks RESULTS to say so; it does not affect overlap recall, the
family bars, or the reading.
