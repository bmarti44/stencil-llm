# Check 44b for gpt-6-astra: message-level bge admission detector (arm C) — trained on the audited corpus (2026-09-06)

Source: results/quick-checks/check44/RESULTS.md (NO-GO: the frozen-1.7B extractor A recalled 2.75% of spans; the v8
sentence head B on fable's held-out scored overlap recall 80.3% micro / 85.4% macro, message recall 94%, precision
98%, false admissions 2/102 payload and 3/153 all-negative — i.e. good on realistic messages, but 11% false admits on
the gate bank's long formal request template; arm C was skipped because kimi-admission had 870 rows at freeze).
Now: data/classifier/relations/kimi-admission.jsonl (2,872) + data/classifier/review/admission-opus-patch.jsonl (53
changes) + data/classifier/relations/opus-admission-enrich.jsonl (231) exist. Build arm C properly:
- MODEL: base bge-small-en-v1.5 fine-tuned as a message-level standing-rule SPAN tagger (sentence-level: split the
  message into sentences/clauses with the frozen splitter; classify each as standing-rule / not, with the whole
  message as context in segment A and the candidate sentence in segment B — training-faithful pairing), plus
  message-level flags as auxiliary heads if cheap. Fit-on = kimi-admission (patched) + opus-admission-enrich;
  scenario-level split; DEV 10%; seeds 0/1/2 (GPU minutes; verify GPU idle; RUNNING.flag; never signal).
- THRESHOLD on DEV: choose the span threshold at DEV false-admission <= 2% on gold-empty messages with the highest
  recall; register it before any held-out look.
- EVALUATE ONCE on data/classifier/heldout/fable-admission-heldout-2.jsonl (being written now by fable; poll every
  5 min for the committed file; do NOT touch fable-admission-heldout.jsonl — it was looked at once in check 44) with
  check 44's metrics (exact/overlap span P/R micro + macro; false admissions on payload / quoted / non-user families
  with Clopper-Pearson bounds; latency on CPU). Also run B (ft-v3 head) on held-out-2 for comparison, and BOTH on the
  v8 gate SETUP bank messages (results/quick-checks/focus3-gate/v8 setup, 96 turns; development diagnostic only) to
  report false admissions on the bank's request template.
- GO bar (write before running): C overlap recall >= 85% micro with false admissions <= 3% on payload and <= 3% on
  quoted items and 0 on non-user roles on held-out-2, AND <= 2/96 false admissions on the v8 setup messages ->
  GO: C replaces the ft head in the runtime (register the swap) and a gate v9 is authorized; else NO-GO -> the
  first-ship decision stays "explicit structured rule entry" with C as an assistive suggester.
Cap 1 GPU-h. Outputs under results/quick-checks/check44b/ (README with pre-written reading, summary.json, per-message
records); model metadata under data/classifier/model/admission-v1/ (safetensors out of git); item 44b in
results/quick-checks/README.md (5 lines); WORKLOG entry (<= 6 lines); dated section in
results/relations-classifier-report.md. Commit with explicit pathspecs (git add -f for results); no push. Foreground
only; never terminate or signal any process; never read the sealed IFEval input file or anything under data/bench.
