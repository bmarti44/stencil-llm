# Check 45 for gpt-6-astra: OFF-TASK PROBE — predict rule violation from the hidden state before generation (2026-09-06)

Brian's idea: "train a probe that measures how off task the model is, in a generalized way — given the task, context
and focus, how far the model is from the focus text, as a percentage — and use it to get the model back on task."
Literature anchor: ReBIND's pre-generation relapse probe (AUROC .897; see results/reuse-research-fable.md P2/TOP-3).
Data: the Day 5 composition pilot (results/quick-checks/composition-pilot/: journal records with per-round hidden
checker results by rule kind, and hidden/ .npy last-prompt-token hidden states for layers {8,16,24,32,40} plus mean
generated-token states, keyed by episode/round/arm). Read its README first; if the pilot was INELIGIBLE or produced
< 150 labelled rounds with >= 25 violations, report INSUFFICIENT DATA and stop (no GPU).
Design (CPU only; no model; the hidden states are already saved):
- Label per round: any live-rule violation (binary) and per kind (style/format/process); also "stale execution".
- Features: last-prompt-token state per layer (separately) and the concatenation; standardise.
- Fit: logistic-regression probes with L2, fit on DEV episodes split by EPISODE (leave-episodes-out CV over the 8
  DEV episodes; never mix rounds of one episode across folds; never touch evaluation episodes — they are not in the
  pilot anyway). Report AUROC per layer and per kind with 95% bootstrap CIs over episodes, calibration (reliability
  table, Brier), and the probe's precision/recall at the operating point that would trigger an intervention on
  <= 20% of rounds. Baselines: a text-similarity baseline (bge-small cosine between the rendered live rules and the
  reply) — to show whether hidden states beat surface similarity; a majority/prior baseline.
- PRE-WRITTEN READINGS: R1 "usable trigger": best layer AUROC >= .85 (CI lower bound >= .75) on leave-episodes-out
  AND beats the similarity baseline by >= .10 AUROC -> register the probe as the off-task METER for the larger test's
  R arm (diagnostic logging only in the registered run; an intervention policy is a separate registered step).
  R2 "signal but weak": AUROC .70-.85 -> keep as a diagnostic; propose the one change most likely to raise it (more
  DEV episodes; generated-token mean states; per-kind probes) as a follow-up, not a rerun. R3 AUROC < .70 -> no
  pre-generation signal at this data size; record. R4 insufficient data -> stop.
Cap: CPU; no GPU. Outputs under results/quick-checks/check45/ (README with readings, per-fold records, probe
weights .npz out of git with hashes in a manifest); item 45 in results/quick-checks/README.md (5 lines); WORKLOG
(<= 6 lines). Data lineage: fit-on = DEV pilot rounds only; evaluated-on = held-out DEV episodes by fold; no
benchmark data; no evaluation-bank episodes. Commit scripts/focus_check45.py + results (git add -f) with explicit
pathspecs; no push; never terminate or signal any process; never read anything under data/bench.
