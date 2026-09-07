# Check 44c for gpt-6-astra: token-level admission tagger + pre-registered C-then-B combination (2026-09-06)

Source: results/quick-checks/check44b/RESULTS.md (NO-GO) and results/check44b-review-fable.md. The review's decisive
finding: the sentence splitter's candidate ceiling on held-out-2 was 176/207 = 85.02% (31/56 misses are two-rule
messages whose clauses share one splitter sentence), so no threshold or head combination could reach the bar;
"Standing rule:" and "X should always" phrasings were absent/negative in the fit corpus; the "Mrs." abbreviation split
caused C's single false admission. Build 44c to fix candidate generation, not only the data:
- MODEL C2: bge-small-en-v1.5 fine-tuned as a TOKEN-LEVEL span tagger (BIO over the message tokens; whole message as
  context; span = maximal B/I run decoded to character offsets; message-level "any rule" score = max span probability).
  No sentence splitter in the candidate path. Fit-on = data/classifier/relations/kimi-admission.jsonl (with
  data/classifier/review/admission-opus-patch.jsonl applied) + data/classifier/relations/opus-admission-enrich.jsonl +
  data/classifier/relations/kimi-admission-2.jsonl (the targeted pass; apply the same span-offset validation; FIRST audit
  kimi-admission-2 yourself on CPU against data/classifier/LABELS.md — fix wrong/missing spans, drop rows that are not
  hand-writable messages, never add benchmark or gate-bank content — writing data/classifier/review/admission-2-astra-patch.jsonl
  (same patch format as admission-opus-patch.jsonl) and apply it before fitting). Scenario/domain-level split; DEV 10% covering >= 6 domains; seeds 0/1/2; GPU minutes only (verify GPU idle;
  RUNNING.flag; never signal).
- THRESHOLDS on DEV only, registered before any held-out look: span threshold t at DEV gold-empty false admissions
  <= 2% with the highest recall. PRE-REGISTERED COMBINATION rule: admit a span if C2 admits it; else if B (ft-v3
  sentence head, run message-wise as in 44b) admits the sentence AND C2's max token probability inside that sentence
  >= t_low, where t_low is chosen on C2's DEV (B run on the same DEV; report B's fit-id overlap with DEV — the review
  found 3/614). Report C2 alone and C2+B, both frozen before the look.
- EVALUATE ONCE on data/classifier/heldout/fable-admission-heldout-3.jsonl (fresh, being written by fable — poll for
  the committed file; do not fit or select on it) with 44/44b's metrics (exact/overlap span P/R micro + macro, false
  admissions by family with Clopper-Pearson bounds, latency on CPU) and ALSO report held-out-2 as a secondary
  regression number (disclosed second look). Report the candidate ceiling of the new tagger explicitly (fraction of
  gold spans representable by some token run = 100% by construction; state the tokenizer boundary caveat).
- Also run C2 and C2+B on the v8 gate SETUP bank messages (96 turns; development diagnostic only): false-admission
  turns, request-template false admissions, and the 36 admit events recovered.
- GO bar (write before running): on held-out-3, overlap recall >= 85% micro AND false admissions <= 3% payload,
  <= 3% quoted, 0 non-user; AND setup diagnostic <= 2/96 false turns with 36/36 admit events -> GO: register the
  runtime swap and authorize gate v9 with admission = explicit structured entry OR the frozen automatic candidate
  (both reported). Else NO-GO -> explicit entry stays first ship; record which bar failed.
Cap 1 GPU-h. Outputs under results/quick-checks/check44c/ (README with the pre-written reading, summary.json,
per-message records, DEV threshold derivation); model under data/classifier/model/admission-v2/ (safetensors out of
git; manifest with hashes); item 44c in results/quick-checks/README.md (5 lines); WORKLOG entry (<= 6 lines); dated
section in results/relations-classifier-report.md. Commit scripts/focus_check44c.py + results (git add -f) with
explicit pathspecs; no push. Foreground only; never terminate or signal any process; never read the sealed IFEval
input file or anything under data/bench; no fitting except the tagger's own fit.
