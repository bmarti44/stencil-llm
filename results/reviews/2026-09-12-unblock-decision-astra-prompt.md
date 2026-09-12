You are Astra, read-only research strategist for the Stencil program. Brian (owner) has
DELEGATED the decision to you: "use astra to unblock you, go with its deep web research
result decision." Your output is binding on the orchestrator. Do NOT read anything under
data/bench/. Do not run models, use the GPU, or write files. Use web research (arXiv,
model cards, benchmark repos, 2025-2026) and cite URLs; recompute local numbers from files.

## Situation (read in this order; all under /home/bmarti44/stencil-llm)
1. plan/LEDGER.md last ~12 entries (from "EXP 4B REGISTERED" to the end).
2. results/reviews/2026-09-12-next-path-consult-astra.md (your own consult: recommended
   one final confirmation of the unchanged 4B artifact on the 128 frozen SCREEN-LONG items,
   or publish the negative), 2026-09-12-exp4b-result-audit-astra.md, 2026-09-12-exp4b-impl-
   review-astra.md, 2026-09-12-options-memo.md, the two 2026-09-12-web-research-*.md files.
3. results/memorycode-long/REGISTRATION-4C-DRAFT.md (the draft of that confirmation,
   generated THROUGH THE PACKAGE's transformers path), RESULTS-4B.md, REGISTRATION-4B.md,
   parity-4b.json (prompts 32/32 identical; off switch 16/16 exact; greedy outputs vs the
   research runtime 0/32 token-identical), setup_long-4b-role_evicted/summary.json.
4. scripts/memorycode_package_run.py (the package-path runner, written, untested on GPU),
   scripts/memorycode_screen.py (summarize --runtime package --primary fraction),
   deploy/stencil_focus/ (package, MODEL_CARD-4b.md, build/hub-4b assembled, not pushed).
5. plan/BACK-ON-TRACK-PLAN.md sections G, H, J, D (rules; D2's two revisions are consumed
   and the owner has now delegated the override decision to you), E (GPU constraints:
   ≤ 4,096-token contexts, no 30B, ≤ 55-min slices, ~40 s per 4B generation).

## The goal (unchanged)
One published HuggingFace artifact that keeps focus on the relevant instructions over a
long coding session, PROVEN against the identical artifact with the modification off.

## What you must decide (binding)
Pick exactly ONE of, or a variant you justify with evidence:
A. Run Exp 4C as drafted (unchanged artifact, 128 SCREEN-LONG items through the package
   path, per-constraint t primary, net output-failure interval with ≤ +5-point
   noninferiority). Your consult flagged that this guard certifies only ~34% of the time
   under zero true harm at N = 128. Decide whether to keep it, or replace it with a
   pre-specified guard that is defensible AND decidable at N = 128 (e.g. failure-rate
   difference upper bound ≤ +10 points, or "no demonstrated increase" = interval lower
   bound ≤ 0 with the point estimate reported, or a category-specific guard on
   invalid-only outputs), stating exactly why and what it costs the claim.
B. A modified confirmation using web-research evidence that a specific, label-free,
   zero- or near-zero-parameter change to the reminder (placement, header wording, a
   "respond in Python in one fenced block" output contract, relevance ranking by a frozen
   public encoder, deduplication of superseded sentences) has reproducible published
   support for models in the 1.5-8B range. Only if the evidence is strong enough that it
   is not "one more fix"; the change must be frozen before generation and disclosed.
C. Publish the package descriptively on HuggingFace now with the NOT PROVEN card (no
   efficacy claim), and end the proof line.
D. Publish the negative in the repo only and end the line (no HF push).

For your pick, give: (1) the decision in one sentence; (2) the deep-web-research findings
that drove it, with URLs and the specific numbers you rely on (models, N, effect sizes,
whether the setting matches ours: long history evicted, dense counter-intuitive coding
conventions, greedy decoding, ≤ 4B); (3) the exact registration text to freeze
(items, arms, primary, guard, readings, budget, disclosure) if A or B, or the exact card
wording if C; (4) the exact operational sequence for the orchestrator (pilot, review,
launch, summarize, publish gate), including whether the Astra implementation review (rule
D1) can be waived given the runner reuses reviewed code; (5) what gets published on EACH
possible reading, so nothing is decided after seeing outcomes.

Constraints you must respect: no fitting/selecting/tuning on the benchmark or on recorded
responses; the benchmark checker never enters the intervention; the claim is artifact-on vs
artifact-off, paired, pre-registered, exhaustive readings; NOT PROVEN is final; everything
seen so far is disclosed. Budget: ≤ 10 GPU-h, ≤ 3 working days.

Output: markdown; header line (reviewer, model, date); the DECISION in bold on the first
line after the header; then sections 1-5. Be concrete enough that the orchestrator can
execute without making a scientific choice.
