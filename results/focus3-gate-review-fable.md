# FOCUS-3 feasibility gate v2 — independent review (fable, 2026-09-06)

Scope: commit 43d076a3, results/quick-checks/focus3-gate/ (RESULTS.md, README.md, summary.json,
gate/ and setup/ records+traces, v1/), src/stencil/focus3.py, scripts/focus3_gate.py,
data/classifier/model/{relations,ft}, data/classifier/LABELS*.md. CPU only; no model launched;
no sealed benchmark file opened. All numbers below were recomputed from the raw per-turn records.

## Recount (raw records, 1,536 gate records, 64 episodes x 4 arms x 6 turns)

| Arm | final success | stale episodes | false-retirement episodes | register-exact |
|---|---:|---:|---:|---:|
| C | 27 | 27 | 64 | 0 |
| O | 61 | 2 | 0 | 64 |
| N | 25 | 38 | n/a | n/a |
| T | 31 | 32 | n/a | n/a |

Matches RESULTS.md exactly. Per family (C/O/N/T final success): override 11/15/9/15,
cancel 7/14/0/0, complete 3/16/0/0, switch-and-return 6/16/16/16.

## (1) Admission path — what was scored, by what, with what result

- Runtime (`focus3.Runtime.update`): each user message is split by the simple regex splitter
  `focus3.sentences` (NOT `selector_v2.split_sentence_spans`); every span is scored by the
  **ft head** (`data/classifier/model/ft`, 3-way none/rule/fact, role one-hot user) with encoder
  pair `("(no context)" | previous USER MESSAGE, "[user] <span>")`; admission requires
  P(rule) >= 0.95 AND every relation pair on that span P(none) >= 0.98 AND scope != single-reply.
- Turn 0 of every gate episode has exactly four spans: "Work on task X." / "For every sorting
  request in this conversation, keep tag equal to N." / "For task X, sort the payload in
  {ascending|descending} order." / "Sort request for task X: payload [...] ...". At turn 0 the
  register is empty, so there are zero relation pairs and the pair guard is vacuous; the
  decision is the ft head alone.
- The ordering instruction WAS presented, correctly segmented, correct role, correct scope key
  (task X). It scored P(none) 0.953-0.989, **P(rule) 0.0095-0.0454, 64/64 below 0.95** (RESULTS
  range confirmed). The tag rule scored P(rule) 0.997 in 64/64 and was admitted 64/64. So this
  is neither a segmentation nor a role/scope bug: it is the head's verdict on one sentence.
- It is ONE sentence, not 64: the bank uses a single template for the initial ordering rule
  (two directions). All 64 "failures" are one template repeated. Same template at the override
  change turn (turn 2, with previous-user context) scored P(rule) 0.05-0.558, also never admitted.
- Why the head says none: the ft training set (kimi/kimi-ctx/kimi-scope/enrich) contains only 2
  ascending/descending rows, both labelled none ("Sort the dataframe by value in descending
  order." / "Just for this search, sort by price ascending."), and 10 none vs 6 rule among
  "sort ..." sentences; rule-labelled sort items all carry "whenever/every time/going forward".
  LABELS.md itself says "a request to do a piece of work is a one-off task (none)". "For task X,
  sort the payload in ascending order." reads as exactly that. The classifier applied its label
  spec; the bank's author wrote the standing ordering rule in one-off imperative phrasing.
- Two genuine (minor) encoding mismatches exist but cannot explain a 0.02 -> 0.95 gap on their
  own: (i) training contexts are 1-3 PRECEDING SENTENCES with a "user:" prefix (kimi-ctx), while
  runtime passes the raw previous user message without prefix, and at turn 0 passes "(no
  context)" even though two preceding sentences exist in the same message; (ii) the splitter is
  not the frozen selector-v2 splitter (semicolon-joined "Continue task X; Sort request ..." is one
  span). Note these; do not sell them as the cause.
- **A threshold cannot fix this**: the "Sort request for task X: payload [...]" span scores
  P(rule) 0.27-0.77 at turn 0 and up to 0.88 on later turns, and "Reply exactly <word>." scores
  up to 0.953. Any cutoff that admits the ordering rule (<= 0.045) admits stale payload requests
  and one-off prose as live rules in most episodes. There is no separating threshold.
- The near-miss guard was load-bearing at least once: gate_1_02 turn 4 "Reply exactly plain."
  reached P(rule) 0.953 >= 0.95 and was blocked only because its pair P(none) was 0.837 < 0.98.
  "Cancel the sorting rule for task X." reached 0.93-0.961 (the ft spec labels cancellations as
  rules) and was likewise blocked only by the pair guard (P(none) 0.57-0.71).
- The failure was visible BEFORE the gate: v1 AND v2 setup C diagnostic traces (setup ran C for
  timing/diagnostics, 16 episodes each) show 0/16 ordering admissions with the same probabilities.
  Neither v1/RESULTS.md nor the pre-gate LEDGER entries surfaced it ("runtime/admission untested"
  at LEDGER line ~298). The 46-minute v2 gate confirmed a deterministic CPU result already on
  disk.

## (2) "False retirements 64/64"

Pre-registered definition (README): any gold-live row missing/changed/shadowed in C's rendered
set at any task answer, **including initial admission misses**. `agreement.false_retirement`
is true at turn 0 of every C episode because the gold ordering row is absent. Actual retire
events in C: zero (applied labels = 64 "admit" of tag rules, nothing else). The count is honest
under its definition but the word "retirement" overstates: 64 missing-admission episodes,
0 wrongful retirements. Consequence chain: no ordering row -> default row
"Ordering: return the list in the given order." rendered on every C sort request -> C actively
tells the model to ignore the ordering instruction. This is why C (6/16) is WORSE than N (16/16)
and T (16/16) on switch-and-return and why C's override successes (11) are mostly episodes where
the raw conversation alone suffices. Design finding: a default row is fail-open when admission
is a false negative.

## (3) Relation head runtime evidence

- 480 pairs, all against the single live global tag row (the only admitted row); gold none 480.
  Proposed: 477 none, **3 "reinstates"** (P 0.517/0.520/0.560, just over the 0.50 threshold) on
  "Cancel the sorting rule for task X." vs the live tag rule in gate_1_06/1_12/1_14. Wrong label
  and wrong target; applied=none only because `reinstates` requires an inactive target. The
  RESULTS statement "all 480 ... applied-none" is true; "proposed" was not all none.
- Zero gold-positive pairs occurred (48 gold supersedes/cancels/completes events had no target
  because the target row was never admitted). There is NO runtime evidence about transition
  recall. Only evidence: none-pair false-positive 3/480 (0.6%) at the proposed level, 0/480 at
  the applied level, consistent with dev none_fp for reinstates 0.8% but on an easier target.
- Hard-none prose (turn 1, quoted/bracketed/inert cancellations): 0/64 admitted, 0/64 pairs
  positive (max positive prob 0.22). Good, but a weak test since the target row was the tag rule.

## (4) N and T

N (no register, raw history): 25/64 final, 38/64 stale; cancel 0/16, complete 0/16, override
9/16, switch 16/16. T (every ever-stated rule re-rendered, no live-state decisions): 31/64 final,
32/64 stale; cancel 0/16, complete 0/16, override 15/16, switch 16/16. T shows restating rules
helps override (15 vs 9) but cannot cancel/complete (0/32 in both N and T). The C-vs-T "beats
naive" term (27 < 32 stale) passed only because C's default row happens to say the right thing
after cancel/complete; it is not evidence of classifier competence.

## (5) O is clean

Checked every O record: `rendered_request` = fixed header + JSON of gold-live rows + the user's
own message. Rows are the user's verbatim sentences (ids like "0:91") or the fixed default row.
No direction key, expected answer, `gold_keys` map, or checker output appears in any O prompt;
`gold_keys` are consumed only by `agreement`/audit. Provenance is logged, never rendered. O's
extra information versus N is exactly and only the admission/retirement decisions — which is
the quantity O is defined to isolate. Three O failures (gate_0_14 wrong value 768 in override;
gate_1_06, gate_1_10 sorted despite the default row after cancel) are retained. One caveat for
claims: the default row text literally states the post-cancel target behaviour, so O measures
"correct register rendered every request", not "model infers cancellation".

## Verdicts

(a) The C failure is a **genuine admission-head limit on this bank's phrasing**, not a
threshold, segmentation, or role/scope defect. The head is spec-consistent (one-off imperative
sort = none); the bank wrote its standing ordering rule as a one-off imperative. Lowering the
threshold is refuted by the raw scores (sort-request spans 0.27-0.88 vs ordering rule <= 0.045).
The "relation head's message-level new-rule signal" does not exist at runtime: the relation head
is 5-class pairwise, and LABELS-RELATIONS.md defines new-rule as "reuse the existing classifier's
rule probability". A calibrated admission rule cannot be built from these scores without fitting
on the gate bank, which the protocol forbids.

(b) Minimal next step, CPU, minutes, no GPU: score the two ordering template sentences with the
ft head under (i) the training-faithful context encoding (preceding sentences, "user:" prefix)
and (ii) spec-conformant paraphrases ("For task X, always sort payloads in ascending order";
"Whenever you sort for task X, use ascending order"). If (i) crosses 0.95, fix the context
encoding in `Runtime.update`/`admission` and register a NEW gate (fresh seed, new freeze). If
only (ii) does, the bank phrasing is outside the frozen label spec and the fix is a re-authored
bank whose ordering rules satisfy LABELS.md scope (2) wording, OR admission-head enrichment with
task-scoped ordering-constraint items (synthetic, non-benchmark). Either way it is a new
registration, not a rerun. **A rerun of this 64-episode gate as-is is not justified**: greedy
decoding plus a deterministic CPU classifier reproduces 0/64 admissions exactly; ~55 GPU-min
would buy nothing. Also add a pre-gate stop: setup C diagnostics must show initial admission of
every gold rule kind before the gate is allowed to consume GPU (both v1 and v2 setups already
had the 0/16 on disk).

(c) O licenses: on this frozen synthetic cohort (64 episodes, one template per family), an
oracle-maintained register rendered inside every task request steers Qwen3-4B to 61/64 final
success and 2/64 stale versus 25/64 and 38/64 with no register and 31/64 and 32/64 with all
rules restated; the O-T contrast (30 more successes, 30 fewer stale) isolates live-state
decisions (supersede/cancel/complete/default) as the driver, not restatement. It does NOT
license: any classifier claim; any statistical/general claim (fixed cohort, one template);
any weight-side or masking claim (prompt rendering only); or "model understands cancellation"
(the default row states the target behaviour). Strongest honest sentence: "given correct
register state, per-request rendering is sufficient to control ordering/tag behaviour on this
cohort end-to-end; obtaining that state from the current admission head is the open problem."
