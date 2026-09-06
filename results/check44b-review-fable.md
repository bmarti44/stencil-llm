# Check 44b accuracy review (fable, one round, 2026-09-06)

Scope: results/quick-checks/check44b (RESULTS.md, 426 records, DEV records, freeze,
scripts) against my own gold, data/classifier/heldout/fable-admission-heldout-2.jsonl.
CPU only; no inference; nothing read under data/bench or the gate banks' gold answers
beyond the 16 setup episodes of results/quick-checks/focus3-gate/v4/bank.json.
Recompute scripts: scratchpad recheck.py / recheck2.py (independent matcher, CP bound,
family definitions written from the gold header, not imported from the check).

## 1. Claims verified span by span

Gold identity: all 330 record inputs equal my committed rows field-for-field (id,
message, standing_rules with offsets, category, scenario, flags); source sha256
9709606e... matches evaluation-start.json and the committed blob. 0 mismatches.

| Claim | Recomputed | Status |
|---|---|---|
| Matching is one-to-one | match_spans is an augmenting-path maximum-cardinality matching (exact / overlap / iou50); my independent implementation gives identical pairs | verified |
| C overlap micro P/R 99.34 / 72.95 (151/207), 152 predictions | 151/152, 151/207 | verified |
| C exact 82.24 / 60.39; macro 99.67 / 78.69; message 100 / 85.80 | identical | verified |
| B overlap 95.43 / 80.68 (167/207), exact 78.86 / 66.67, macro 97.32 / 87.22, message 99.40 / 94.89 | identical | verified |
| False-admission families C 0/97, 0/57, 0/30, 0/154; B 0/97, 1/57, 0/30, 1/154 | identical; family definitions (gold-empty & one_off_request; gold-empty & quoted_or_reported; role != user) reproduce 97/57/30 | verified |
| One-sided 95% CP uppers 3.04 / 5.12 / 9.50 / 1.93 %; B quoted 8.05 %, all-negative 3.04 %; scenario-level 3.68 / 6.18 / 10.15 / 3.38 % | own bisection on the binomial CDF (k=0 closed form 1-0.05^(1/n)) reproduces every figure to 4 places | verified |
| Category recall C 101/114, 25/62, 25/31; B 109/114, 27/62, 31/31 | identical | verified |
| Splitter representability 176/207 = 85.02 %, all 31 two-rule messages put both clauses in one candidate | identical; every unrepresentable span is in a two_rules message | verified |
| SETUP C 2/96 false turns (5:0, 13:0 "Work on task ..."), 0/96 request-template, 34/40 gold; B 22/96, 15/96, 39/40; gold-empty admits 0/72 vs 14/72 | identical | verified |
| DEV threshold 0.9883976740722434 = lowest feasible at <= 2 % gold-empty false admissions (3/183) | recomputed from seed0/dev-records.json; identical; DEV recall 135/147 = 91.84 % | verified |
| No held-out look before freeze | model-freeze.json 08:12:37, freeze commit bab43b0d 08:13:18, my bank committed 2b3cfc74 08:15:26, polls at 08:08/08:14 "not committed", 08:19 "committed", evaluation-start 08:19:37. HELDOUT is referenced only inside evaluate() (lines 496-501); prepare/fit never touch it. DEV (marketing, travel; 309 msgs) shares 0 normalized messages with held-out-2 | verified (git-level; the file's on-disk existence before commit cannot be proven from git, but the code path cannot read it before evaluate) |
| v8 SETUP bank identity | v8/recipe-freeze.json hash of v4/bank.json 00cf7659... equals check44b recipe hash | verified |
| audit.json / independent-audit.json | replay all scores from records; consistent with my recount; neither re-ran inference | verified |

No arithmetic error found. The reported numbers are exactly what the records contain.

## 2. Where C's 56 misses come from (records only)

For every unmatched gold span: is it reachable by any splitter candidate under the
one-to-one overlap matching; if reachable, the maximum P over overlapping candidates.

| Class | Spans | Notes |
|---|---:|---|
| (a) boundary: splitter never produced a one-to-one candidate | 31 | all in two_rules; colon/semicolon lists ("Two rules for X: a; b.") and "A, and B" in one sentence; the frozen regex splits only on `.!?` + whitespace |
| (b) threshold: representable, P in [0.95, 0.9884) | 11 | e.g. adm-020 0.9877, adm-286 0.9873, adm-284 0.9877, adm-316 0.9857, adm-330 0.979 |
| (b') representable, P in [0.90, 0.95) | 1 | adm-216 0.9235 |
| representable, P in [0.5, 0.9) | 4 | adm-036 0.900, adm-196 0.646, adm-244 0.699, adm-271 0.8995 |
| (c) genuine, P < 0.5 | 9 | adm-090 0.096, adm-092 0.008, adm-165 0.40, adm-270 0.003, adm-315 0.002, and four two-rule sentences scored 0.01-0.29 (adm-110, 157, 186, 261) that lose BOTH spans (one counted as boundary, one here) |

Diagnostic recall at lower thresholds (held-out-2; NOT a selection, the arm stays
frozen): 0.95 -> 162/207 = 78.3 % with 1/154 false admission (quoted); 0.90 ->
163/207 = 78.7 % with 3/154; 0.50 -> 167/207 = 80.7 % with 5/154. Splitter
ceiling 176/207 = 85.02 %. On representable spans only: C 151/176 = 85.8 %,
B 167/176 = 94.9 %. Excluding the two_rules category: C 126/145 = 86.9 %,
B 140/145 = 96.6 %.

Consequence: no threshold, and no head-level combination of C and B, can reach
85 % on this bank; the 85 % bar sits at the candidate-generation ceiling
(176/207 = 85.02 %), i.e. C would have needed every representable span. The
authors registered 85 % believing the ceiling was ~95 % (fit 95.17 %, DEV 95.92 %);
held-out-2's two-rule messages are uniformly single-sentence lists (31/31), versus
70/434 multi-rule spans (16 %) unrepresentable in the corpus. That is an authoring
style difference in my bank (a legitimate real-world form, but over-represented
relative to the corpus) and should be stated next to the recall number.

Phrasing-level causes for the 25 representable misses, checked against the fit+DEV
corpus sentences:
- "Standing rule: ..." appears 0 times in the corpus; both such held-out rules
  (adm-270, adm-315) score 0.002-0.003 (B: 0.995/0.984). Pure data gap.
- "<Noun> should always ..." is 2 positive / 23 negative in the corpus (the negatives
  are reported speech: "My boss says you should always ..."); six bare-user
  "should always" rules in held-out-2 score 0.65-0.988 and five are missed. A
  labeling-convention/coverage gap, not a model limit.
- "For this <session/agreement/sprint/set/lager>, ..." task-scoped rules: five of the
  13 one-rule misses (P 0.008-0.96). Corpus has 131 pos / 42 neg "For this" sentences,
  so this is the head learning "For this X" as one-off-leaning; by scope, C recall is
  task 19/27 = 70 % vs global 132/180 = 73 %, so it is not a scope-level effect.
- Abbreviation "Mrs." splits: C's only held-out false admission (adm-317, fragment
  "H' in anything you write ...", P 0.995) and one miss (adm-330) are both this
  splitter artifact. B shows the same fragments (its fp list includes 317 and 330).

## 3. DEV calibration: correct but fragile

Budget is floor(0.02 * 183) = 3 false admissions. DEV negative-message admits by
threshold: 0.988 -> 3, 0.98 -> 4, 0.95 -> 4, 0.90 -> 5, 0.5 -> 7. The frozen
0.9884 is set by a single fourth DEV negative message; at 0.95 DEV recall would be
138/147 = 93.9 % (2.19 % false admissions). Seeds 1/2 landed at 0.977 / 0.957 with
the same 3/183. DEV is two domains (marketing 153, travel 156) chosen by
Random(0) over 20 domains; all three DEV false admissions are travel. This is not a
protocol violation, but the operating point is decided by one message and should
be reported as such; the next check should use a DEV with >= 5 domains or a
scenario-grouped split so that the 2 % budget is at least 5-6 messages.

## 4. SETUP (gate) quantification

The gate's "36/36 admissions" (v8 RESULTS/registration; LEDGER 620, 690, 747) are
the 36 `admit` events in the 16 setup episodes (32 on turn 0 = tag rule + order
rule, each its own sentence; 4 further admits), plus 4 `supersedes` events = the
40 gold spans scored here. Turn-0 messages are two-rule messages, not one-rule,
but the rules are sentence-separated, so the splitter is not the limit there.

| Setup arm (role guard, no scope/lifecycle guards) | admit | supersedes | false turns | request-template |
|---|---:|---:|---:|---:|
| C frozen 0.9884 | 32/36 | 2/4 | 2/96 | 0/96 |
| C diag 0.985 | 34/36 | 2/4 | 5/96 | 2/96 |
| C diag 0.98 | 36/36 | 2/4 | 8/96 | 2/96 |
| C diag 0.95 | 36/36 | 3/4 | 8/96 | 2/96 |
| B frozen 0.95 | 36/36 | 3/4 | 22/96 | 15/96 |
| combo t_low 0.95-0.98 (C admits, else B admits and C.P >= t_low) | 36/36 | 2/4 | 2/96 | 0/96 |
| combo t_low 0.5 | 36/36 | 2/4 | 4/96 | 2/96 |

C's four missed admits are "Always sort payloads in descending order for task SxnyA."
/ "For task SxnyA, the payload must be in descending order until I say otherwise"
at P 0.9847-0.9862, i.e. 0.002-0.004 under the frozen threshold. The missed
supersedes "Replace the sorting rule for task S0n1A: always use ascending order."
scores 0.011 (genuine miss; B 0.99+). C.P on B's 22 setup false spans: 20 are
< 0.33, two are 0.89 and 0.94, so a combo t_low >= 0.95 inherits none of B's
request-template admissions on this bank.

## 5. Answers

(1) NO-GO is correctly applied. The registered decision is mechanical
(overlap recall >= 0.85 AND family rates AND <= 2/96 SETUP), recall 72.95 % < 85 %
is exact, everything else passed, and nothing was revised after the look. Two
qualifications belong in the record: the bar was at the splitter ceiling on this
bank (85.02 %), so the metric mostly measured candidate generation, not the head;
and on representable spans C (85.8 %) is still clearly below B (94.9 %), so C is not
the better tagger at its operating point, only the more precise one (held-out 0 vs
1 false admission; SETUP 0 vs 15 request-template admissions).

(2) The combination rule "admit if C admits; else if B admits and C.P >= t_low"
is post hoc in form: it is motivated by what held-out-2 revealed (11 of C's 25
representable misses sit in [0.95, 0.988) and B catches most of them; B's false
admissions have low C.P). It can still be fairly pre-registered for the NEXT check
provided: (i) t_low is fixed on DEV before the new bank exists, which requires
running B on C's 309-message DEV (feasible: only 3/614 C-DEV sentences are in
ft-v3's fit_ids, 0/… of held-out-2 sentences); (ii) held-out-2 is never used to pick
t_low and the review states that the rule was generated after seeing it; (iii) the
registered bar is not recycled unchanged — see below, no head-level rule can pass
85 % on a bank with this two-rule form, so the rule must be paired with a candidate
fix or the bar restated on representable spans plus a separate representability
requirement. Also register the trade: on SETUP the combo fixes the four 0.985
admits without B's request-template admissions, but does not recover supersedes
sentences C scores near 0 ("Replace the sorting rule ..." 0.011).

(3) The running data pass (kimi-admission-2.jsonl, 246 rows so far: 119 empty,
57 one-rule, 64 two-rule, 6 three-rule; 23 of 70 multi-rule messages put two
rules in one splitter sentence) targets the right phrasing gaps ("Standing rule:",
bare "should always", "For this X", colon lists) and can plausibly recover most of
the 25 representable misses. It cannot touch the 31 boundary misses: with the
frozen regex splitter a sentence yields one candidate, so a refit on any amount of
two-rule data still emits at most one span per sentence. Fixing recall on this
bank requires a candidate change (clause splitting on `;`, `:`-introduced lists,
", and"/" and " between imperative clauses; or a token-level BIO tagger whose
spans are not pre-segmented), with abbreviation handling ("Mrs.", "Dr.", "e.g.")
in the same pass since it produced C's only false admission. Re-register the
splitter ceiling as a reported quantity with its own requirement (e.g. >= 95 %
on the new bank) so the head bar means what it says. Next look: NOT held-out-2
(seen once; its miss list is now public in this review and in RESULTS) and not
the original Fable bank (B/ft-v3 has been read against it repeatedly). Use a fresh
author-disjoint held-out-3 whose two-rule messages mix sentence-separated and
single-sentence forms in a stated ratio; held-out-2 may be re-run only as a
secondary regression number, never as the decision bank.

(4) For the gate: no. C at the frozen threshold admits 32/36 setup admit events;
the gate requires 36/36. The four misses are the gate's own per-task order rules
at P 0.985-0.986, so "89 % one-rule recall" is exactly the wrong number here — the
gate's rules are formulaic and C scores them just under a threshold that was set
by one DEV message. At any threshold <= 0.98 C reaches 36/36 admits but with
8/96 false-admission turns (task-selection sentences plus 2 request-template) versus
the <= 2/96 condition; the combo at t_low 0.95-0.98 gives 36/36, 2/96, 0
request-template on the setup traces, at 2/4 supersedes (the gate's ">= 11/12
transitions" criterion is separate and downstream guards were not applied here).
Note these are development-bank numbers computed after the fact; they size the
gap, they do not certify a v9 configuration.

## 6. Findings by severity

- MEDIUM (reporting): RESULTS states the recall failure without stating that the
  registered 85 % bar equals the splitter ceiling on this bank (85.02 %) and that
  the ceiling shift (95.9 % DEV -> 85.0 % held-out) is a held-out authoring-form
  difference. Add both sentences; keep NO-GO.
- MEDIUM (design, for the next check): DEV false-admission budget of 3 messages
  pins the threshold on one message; 0.988 vs 0.95 differ by one DEV negative.
- LOW: "C misses concentrated in two-rule and rule+payload" is right in count but
  the mechanism differs: two-rule = candidate boundaries (31) plus four whole
  sentences scored < 0.3; rule+payload = phrasing gaps ("Standing rule:" 0.002,
  "From now on, convert ..." 0.40-0.988), not payload interference.
- LOW: the "Mrs." split accounts for C's single held-out false admission and one
  miss; RESULTS calls the false admission count 0/154 correctly (adm-317 is a
  positive message) but the fragment admission is worth naming as a splitter bug.
- No high or critical findings. NO-GO stands; the numbers are reproducible from the
  saved records against my gold with no discrepancies.
