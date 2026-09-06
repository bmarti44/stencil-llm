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

PENDING.
