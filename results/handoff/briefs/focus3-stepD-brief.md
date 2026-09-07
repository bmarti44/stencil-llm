# FOCUS-3 step D for gpt-6-astra: last registered iteration before escalation — v8 (2026-09-06)

Inputs: results/quick-checks/focus3-gate/v7/RESULTS.md (INELIGIBLE: admissions 36/36 and transitions 11/12 PASS; but 19
unauthorized: 14 admissions of one-shot "Sort request ... payload [...]" sentences by admission head v2 (DEV non-rule
admission only 1.2%: the bank's request+payload sentence family is absent from DEV); 4 reinstatements of "Reply exactly
even." in cancellation episodes; 1 completion retiring an extra row). STOP-LOSS: this is the last iteration on this
gate before the orchestrator escalates to Brian with a summary; do not exceed the rulings below.
RULINGS (register in results/quick-checks/focus3-gate/v8/RESULTS.md BEFORE fitting/running):
 (1) ADMISSION NEGATIVES: hand-write (yourself, in-session, no script content) >= 200 sentence-level NONE rows of
     one-shot task requests carrying data/payloads in many forms ("Sort request: payload [...]", "Here are the rows:
     ...", "Process this list: ...", "Run it on these values ...", code blocks, JSON, CSV) across >= 10 domains, plus
     >= 100 STANDING-rule positives with payload-like context nearby (so the head learns request-vs-rule, not
     payload-vs-no-payload). Never a gate-bank sentence. Save as data/classifier/ft-enrich-requests.jsonl; refit the
     admission head ONCE MORE (seeds 0/1/2; GPU minutes) -> ft-v3; evaluate once on the author-disjoint rule/fact
     held-out; record the delta and the DEV non-rule admission rate on the new family.
 (2) COMPLETES scope: a completion retires only rows whose scope is the completed task; global rows never retire on
     completes. Unit test.
 (3) REINSTATES: examine the 4 "Reply exactly even." reinstatements in the v7 traces and record the cause; rule: a
     reinstatement applies only if the span passes admission as a rule-bearing span whose admitted key equals the
     retired target's key AND the target's status is cancelled/completed; cancellation messages cannot reinstate.
     Unit test.
 (4) Everything else unchanged from v7 (relation model v2, thresholds, C', renderer, banks, readings).
Then: CPU replay (36/36, >= 11/12, 0 unauthorized; else INELIGIBLE and STOP), then gate v8 (C, C', O, N, T; cap
3 GPU-h; RUNNING.flag; never signal). Outputs under results/quick-checks/focus3-gate/v8/; README item; WORKLOG; dated
section in results/relations-classifier-report.md; commit with explicit pathspecs (git add -f); no push. Foreground
only; never terminate or signal any process; never read the sealed IFEval input file or anything under data/bench.
