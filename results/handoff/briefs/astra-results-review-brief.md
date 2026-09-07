# Independent results review for gpt-6-astra (fresh session): quick checks 31-43 and FOCUS-2d — 2026-09-05

Brian's instruction: "spin up an astra sub agent to review all of the results as well." Repo /home/bmarti44/stencil-llm
(read-only; CPU only; the GPU is running check 42 — never launch a model process; never signal anything). You are a
fresh reviewer with no memory of authoring any of this; treat every number as a claim to recompute from raw records.
Scope (read in this order): results/quick-checks/README.md items 31-43 + QUEUE sections; the per-check READMEs and
raw records under results/quick-checks/{focus1-probe,check32-kv,check33,check34,check35,check36,check37,check38,check39,
check40,check40b,check40c,check40d,check40e,check41,check41b,check43}/; fable's accuracy reviews results/check3{1,2,4,5,
6,8}-review-fable.md, results/check40b-review-fable.md, results/check40e-review-fable.md, results/check43-review-fable.md;
FOCUS-2/2b/2c/2d in LEDGER-PLAN.md (sections "FOCUS-2 ...", their OUTCOMEs) + results/focus2d-review-fable.md +
results/focus2c-safety-diagnosis-fable.md; results/focus-synthesis-astra.md; results/neuron-granularity-research-astra.md;
results/relations-classifier-report.md.
Deliver results/astra-results-review.md (<= 200 lines), graded findings (low/medium/high/critical) with file:line or
record-level evidence, covering:
1. ACCURACY: for each check, does the README's reading follow mechanically from its pre-written rule and the raw
   records? Recompute the headline counts yourself (parsers/records, not the summary files) for at least 40b, 40c, 40d,
   43, 41, 41b, 38 and FOCUS-2d. Flag any place fable's review and the README disagree and who is right.
2. INTEGRITY: pre-registration discipline (readings written before outcomes — verify hashes/commit order where
   recorded), seed/bank disjointness, leakage of cues into "uncued" prompts, fairness of shuffled/swapped controls,
   dose/cell selection on setup vs test, any post-hoc reinterpretation that changed a verdict.
3. CLAIMS vs EVIDENCE: what the program can honestly claim today about (a) instruction control on a frozen trunk
   (placement cadence, masking), (b) skill selection via router bias (set/hold yes; switch/clear no; generality
   unknown; concept-level open), (c) neuron-level control (closed on dense; untested inside experts), (d) the
   register/classifier. Identify overclaims in READMEs, WORKLOG, memory-like summaries, or the synthesis, and give
   exact replacement wording.
4. STATISTICS: n=32 single-seed greedy screens — what confidence do they support; which results need replication
   before they carry weight; recompute at least two of the McNemar/Wilson numbers.
5. THE MILLER QUESTION: given all of it, is "sustained router bias = slow control selecting which stored experts
   express" a fair Miller analogue, and what would falsify it; what is the single most valuable next experiment and
   what should be cut from the current queue (42 running; retrain, 43b, 40f, 40g queued).
End with VERDICT on the program's current claims (SOUND / SOUND-WITH-FIXES / UNSOUND).
HARD RULES: CPU only; never launch any GPU/model process; foreground only; never terminate or signal any process; no
repo edits other than writing results/astra-results-review.md; never read the sealed IFEval input file or the sealed
BFCL cohort contents.
