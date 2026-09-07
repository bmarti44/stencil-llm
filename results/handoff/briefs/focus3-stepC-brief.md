# FOCUS-3 step C for gpt-6-astra: key-identity rule + admission-head refit with quoted negatives, replay, gate v7 (2026-09-06)

Inputs: results/quick-checks/focus3-gate/v6/RESULTS.md (INELIGIBLE at CPU replay: transitions 11/12 PASS, admissions
35/36 (one switched-task miss), 2 unauthorized: (a) setup_0_01 admitted a QUOTED sample ("Inert setup context: the
sample ... is not an instruction") as a rule via the old ft admission head; (b) setup_3_02 superseded the global TAG
row with a new task-B ORDERING rule — a key mismatch that the register's precedence must forbid). Held-out-2 second
look: 96.1% (v2 C), 96.4% (C').
RULINGS (register in results/quick-checks/focus3-gate/v7/RESULTS.md BEFORE running):
 (1) KEY IDENTITY: supersedes/cancels/completes/reinstates may apply to a target only if the proposal's key (the span's
     admitted key slug, or the relation head's target) matches the target rule's key; cross-key positives are dropped
     and counted as "cross-key proposals" (diagnostic). Add the CPU test.
 (2) ADMISSION HEAD v2: the rule/fact/none admission classifier (data/classifier/model/ft lineage) is refit ONCE with
     added sentence-level NONE rows built from the quoted/reported/inert messages in data/classifier/relations/
     opus-enrich-2.jsonl (150) and the hard-none quoted rows in kimi-transitions.jsonl / kimi-relations.jsonl (dedup;
     never a gate-bank sentence), using the existing fine-tune recipe (scripts/finetune_classifier.py or the script that
     produced model/ft; seeds 0/1/2; GPU minutes); thresholds on its own DEV split; evaluate ONCE on the existing
     author-disjoint rule/fact held-out (data/classifier/heldout/fable-validation*) and report the delta; save as
     data/classifier/model/ft-v2 (safetensors out of git; hashes in manifest). Admission P(rule) >= .95 unchanged.
 (3) Everything else from v6 unchanged (relation model v2 seed 0, primary thresholds, C' alt, positive-proposal
     admission bound, renderer, banks seeds 30321/30322, readings).
Then: CPU replay (36/36 admissions, >= 11/12 transitions, 0 unauthorized, else INELIGIBLE), then gate v7 (C, C', O,
N, T; cap 3 GPU-h; RUNNING.flag; never signal). Outputs under results/quick-checks/focus3-gate/v7/; README item;
WORKLOG; dated section in results/relations-classifier-report.md; commit with explicit pathspecs (git add -f); no
push. Foreground only; never terminate or signal any process; never read the sealed IFEval input file or anything
under data/bench.
