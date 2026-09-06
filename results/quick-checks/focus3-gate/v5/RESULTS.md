# FOCUS-3 v5 step A — pre-written registration (2026-09-06)

CPU-only replay of FROZEN v4 seed-0 relations and ft admission classifiers.
Fit-on: unchanged v4 patched Kimi + Astra/Opus pool; historical admission lineage
caveats remain. No fitting, selection or new calibration. Descriptive DEV tables
use committed original scenario-disjoint 576-row seed-0 logits. Evaluated-on:
exact committed v4 16-episode/96-turn development setup bank, seed 30321.
No sealed/bench reads, held-out re-evaluation, GPU/trunk processes, signals,
background launches or push. STOP after CPU replay/report. Step B (refit + gate)
awaits enrichment review and is not executed here.

## Orchestrator rulings, fixed before tests or replay

1. Confident none iff P(none) >= .50, the fixed positive-side admission bound.
   Retire gold-none 90th/95th percentile rule. Review DEV table:

   | cutoff | gold-none passing / 259 | gold-positive passing / 317 |
   |---|---:|---:|
   | .50 (registered) | 217 | 5 |
   | .2046 (rounded positive 95th percentile; descriptive) | 227 | 16 |
   | .9711621345086118 (retired none 90th percentile) | 26 | 0 |

   Passing positives are unsafe none classifications (5/317 = 1.58% at .50).
2. Pair prose spans only with overlapping scopes: global or same task, using
   scope_of(span, current task). Never score wrong-task pairs. Filter any
   non-overlapping positive before selection; it must not skip span admission.
   Global rows still overlap task rules; no extra same-key pairing restriction.
   All remaining pairs must meet the none bound for a new admission.
3. Reinstates require a retired target and a rule-bearing span: that span must
   pass non-overflow admission P(rule) >= .95 OR contain retired rule text
   verbatim. Bare Continue/Work on/Return to/Switch to task X spans only select
   task; never reinstate. Relation threshold still applies. No extra quoted
   cancellation filter is registered: report residual unauthorized actions.
4. C stays .94/.50/.50/.50 (supersedes/cancels/completes/reinstates).
   Separate future gate arm C' = .80/.50/.50/.50; never swap into this replay.
   Other C' runtime/gate rules match C; report arms separately. Later enriched
   fitting would show runtime/classifier agreement on a development bank whose
   idioms entered fitting, not generalisation to unseen phrasings.
   Descriptive review DEV sweep (none-FP denominator 259):

   | policy | correct-positive recall / 317 | total none-FP | supersedes recall / FP | cancels recall / FP | completes recall / FP | reinstates recall / FP |
   |---|---:|---:|---|---|---|---|
   | C: .94/.50/.50/.50 | .921 | 26 (10.0%) | .79 / 11 | .99 / 6 | .99 / 7 | .99 / 2 |
   | per-class cap 10%: .50 each | .972 | 40 (15.4%) | .94 / 25 | .99 / 6 | .99 / 7 | .99 / 2 |
   | supersedes .90 | .934 | 29 (11.2%) | .83 / 14 | same | same | same |
   | C': supersedes .80 | .946 | 33 (12.7%) | .87 / 18 | same | same | same |
   | supersedes .72 | .953 | 37 (14.3%) | .89 / 22 | same | same | same |
   | supersedes .70 | .956 | 37 (14.3%) | .90 / 22 | same | same | same |
   | plain argmax | .972 | 41 (15.8%) | .94 / 26 | .99 / 6 | .99 / 7 | .99 / 2 |
   | argmax margin >= .2 | .962 | 38 (14.7%) | .92 / 24 | .99 / 6 | .99 / 7 | .99 / 1 |
   | argmax margin >= .5 | .943 | 34 (13.1%) | .89 / 21 | .97 / 5 | .97 / 7 | .97 / 1 |

5. Require all 96 distinct records, 36/36 admissions, existing >=11/12
   correct-source transitions, AND >=3/4 for each represented transition label
   (supersedes/cancels/completes), no overflow, unauthorized applications ==0
   across 96 records. Reinstates has no gold support; recall N/A, never a vacuous
   pass. Count every applied action without a matching gold label, target and
   span on that turn, including admits and duplicates; count actions and affected
   records separately. Expected by request: 36/36 admissions, 8–9/12 transitions,
   zero unauthorized. Expectations do not override the stop. Keep known misses:
   "Replace the sorting rule for task S0n1A: always use ascending order."
   "The sorting rule for task S1n2A no longer applies."
   "That concludes task S2n3A."
6. Delete exactly astra-enrich-2-{cancels,completes,supersedes}-00, the three
   verbatim bank rows; retain exact sentences in a deletion receipt. Keep 90
   relatives quarantined as evaluation-derived; deletion does not make them
   clean. Leave kimi-transitions.jsonl untouched for later enrichment review.
   No enrichment is consumed in this replay.
7. CPU parity extends real runtime consumers for guard side/boundary, scope
   pairing/admission reachability, reinstates rule and unauthorized counter.
   Preserve trained rendering, offsets and status vocabulary. Bind model/input/
   source hashes before replay; write raw records in the run and replay saved
   predictions through Runtime for the CPU audit.

Source: results/focus3-gate-v4-review-fable.md; user rulings take precedence.

## Replay outcome

**INELIGIBLE-STEP-A.** Step A is complete; no refit or 64-episode gate ran.
The requested expected 36/36 admissions and zero unauthorized applications did
not materialize under the registered rules. Do not proceed to step B on a claim
that this replay passed.

| setup criterion | measured | required | result |
|---|---:|---:|---|
| distinct records / episodes | 96 / 16 | 96 / 16 | pass |
| initial ordering admissions | 16/16 | 16/16 | pass |
| initial tag admissions | 16/16 | 16/16 | pass |
| switched-task admissions | 1/4 | 4/4 | fail |
| all authorized admissions | 33/36 | 36/36 | fail |
| correct-source transitions | 8/12 | >=11/12 | fail |
| supersedes | 2/4 | >=3/4 | fail |
| cancels | 3/4 | >=3/4 | pass |
| completes | 3/4 | >=3/4 | pass |
| unauthorized applications | 2 across 96 records | 0 across 96 | fail |
| applied reinstates | 0; no gold support | rule-bearing only | no false restore |
| overflow | 0 | 0 | pass |

The three switched-task failures have no wrong-task pair or positive proposal.
Their remaining global-tag pair fails the registered .50 none bound:

| episode | P(rule) on new rule (v4 review, rounded) | P(none) against global tag | outcome |
|---|---:|---:|---|
| setup_3_00 | .9773 | .115694 | blocked |
| setup_3_01 | .9607 | .510802 | admitted |
| setup_3_02 | .9582 | .056845 | blocked |
| setup_3_03 | .9772 | .049374 | blocked |

Scope exclusion removes sibling-task interference, but global tag rules still
legitimately overlap. Dropping those pairs by key or relaxing the .50 bound would
change this registration; neither change was made. The review's predicted four
recovered admissions overlooked these overlapping global pairs.

All three known phrasing misses remain, with unchanged correct-target behavior:

| episode | gold label / span | P(gold label) |
|---|---|---:|
| setup_0_01 | supersedes: Replace the sorting rule for task S0n1A: always use ascending order. | .702283 |
| setup_1_02 | cancels: The sorting rule for task S1n2A no longer applies. | .015570 |
| setup_2_03 | completes: That concludes task S2n3A. | .033564 |

The fourth miss is setup_0_02, “For task S0n2A, switch the standing order from
descending to ascending.” P(supersedes)=.726819 < .94. Separate C' (.80) was
registered but not executed; its DEV supersedes recall is 92/106=.867925 and
combined none-FP 33/259=12.7413%, independently recomputed in dev-tables.json.

Two residual unauthorized applications affect two records:

- setup_0_01 turn 1: admitted `Inert setup context: the sample "Cancel the sorting
  rule for task S0n1A." is not an instruction.` P(rule)=.960425, with P(none)
  .961404/.959730 on the two overlapping rules. This false admission becomes
  possible under the .50 bound. It must count even though no relation applies.
- setup_3_00 turn 1: cancelled ordering row 0:90 from `Inert setup log context:
  the line "Cancel the sorting rule for task S3n0A." is not an instruction.`
  P(cancels)=.599703; P(rule)=.760051 does not veto cancellation under these rules.

No quoted-text veto or further policy repair was introduced after seeing these
outcomes. Total applications: admit34 (33 authorized +1 unauthorized),
supersedes2, cancels4 (3 authorized +1 unauthorized), completes3, reinstates0.
All 45 observed additions/status changes match logged actions independently.

## Execution and evidence

Registration/runtime/tests committed at 1780f5b9 before one frozen-classifier
CPU inference pass. That run exposed an implementation mistake: the bare-task
switch guard inspected admission spans containing the harness's payload suffix,
allowing four final-turn reinstatements and seven final-turn admissions. The
original 96 records, source snapshots, freeze, audit and log are retained in
implementation-diagnostic/ (13 unauthorized actions in that implementation).

The correction was prewritten in implementation-correction.md and committed at
037c7efb before recomputing state. It recognizes task switches on the relation
prose prefix. The final replay consumed the SAME saved probabilities, asserted
exact pair/admission input equality throughout, and performed zero additional
model inference. Only 11 final-turn records changed; every score is preserved.
This is an implementation correction to ruling 3, with no new threshold, arm,
bank wording or fitting. The first-run model-inference count is one for step A;
summary.json's inference_passes=0 describes the final saved-probability replay.

96 final records and 16 traces were written during replay. There are 156 scored
relation pairs (12 gold-positive, 144 gold-none) and 184 admission spans, versus
v4's 201 pairs; scope filtering and changed trajectories alter the count.
Gold-none pairs: 18 positive proposals, 1 applied relation, 117/144 meeting the
none guard. Unauthorized counts additionally include the false admission.
Frozen-model hashes, trained input/status/scope/offset parity, softmax values,
DEV tables, complete runtime state and identical saved predictions audit PASS.
Independent multiset action matching/state-mutation audit also PASS.

Validation: 53 targeted tests passed, one existing legacy import-inventory
xfail; corrected audit consumer additionally passed; Ruff and diff checks pass.
Initial CPU inference including load: 14.962216 wall seconds / 109.207944 process
CPU seconds. Final saved-probability replay: 1.114159 wall / .090228 process CPU
seconds. GPU time 0, generated replies 0, gate records 0. No GPU claim was needed
for CPU-only work. No GPU/model server process, signal, benchmark/sealed read,
new fitting, Kimi-transition access or push occurred.

Exactly three verbatim rows were removed: astra-enrich-2-cancels-00,
astra-enrich-2-completes-00, astra-enrich-2-supersedes-00. Their exact sentences
are in deleted-bank-rows.json and the known-miss table above. The other 90 rows
retain their evaluation-derived quarantine and historical parent IDs; they do
not become clean fitting data by deletion of the originals. Clean multi-domain
Kimi transitions remain untouched pending the later enrichment review.

Artifacts: registration.md, freeze.json, dev-tables.json, summary.json,
audit.json, independent-audit.json, records/, traces/, replay.log, and preserved
implementation-diagnostic/. Runtime/setup evidence only; no novel-phrasing,
held-out, refit, readiness or GPU-gate success claim. Stop here at step A.
