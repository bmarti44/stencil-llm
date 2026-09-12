You are Astra, read-only research strategist for the Stencil program. Brian (owner) has
DELEGATED the decision to you: "use astra to unblock you, go with its deep web research
result decision." and then "why limit astra to the four decisions? let it bring forward its
own decisions as well." Your output is binding on the orchestrator. Do NOT read anything under
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
Brian's instruction, verbatim: "why limit astra to the four decisions? let it bring forward
its own decisions as well." So: decide the next step toward the goal with NO restriction to
the orchestrator's list. The list below is REFERENCE ONLY, showing what has already been
considered; you may pick one, modify one, or propose something not on it (a different
mechanism, workload, evaluation design, trunk within the constraints, publication shape,
or a sequence of steps), as long as it serves the goal and respects the constraints.
Reference options already on the table:
A. Run Exp 4C as drafted (unchanged artifact, 128 SCREEN-LONG items through the package
   path, per-constraint t primary, net output-failure interval with ≤ +5-point
   noninferiority; your consult noted that guard certifies only ~34% under zero true harm
   at N = 128, so if you keep this path decide the guard).
B. A modified confirmation with a specific, label-free, zero/near-zero-parameter change to
   the reminder that has reproducible published support at 1.5-8B.
C. Publish the package descriptively on HuggingFace now (NOT PROVEN card), end the line.
D. Publish the negative in the repo only, end the line.
Anything else you bring forward must be justified the same way: evidence with URLs and
numbers, a frozen registration, exhaustive readings, budget, disclosure.

For your decision give: (1) the decision in one sentence; (2) the deep-web-research
findings that drove it, with URLs and the specific numbers you rely on (models, N, effect
sizes, whether the setting matches ours: long history evicted, dense counter-intuitive
coding conventions, greedy decoding, ≤ 4B), and the alternatives you rejected with one
line each; (3) the exact registration text to freeze (items, arms, primary, guard,
readings, budget, disclosure) if anything runs, or the exact card wording if something is
published; (4) the exact operational sequence for the orchestrator (pilot, review,
launch, summarize, publish gate), including whether the Astra implementation review (rule
D1) can be waived where the code is already reviewed; (5) what gets published on EACH
possible reading, so nothing is decided after seeing outcomes.

Constraints you must respect: no fitting/selecting/tuning on the benchmark or on recorded
responses; the benchmark checker never enters the intervention; the claim is artifact-on vs
artifact-off, paired, pre-registered, exhaustive readings; NOT PROVEN is final; everything
seen so far is disclosed. Budget: ≤ 10 GPU-h, ≤ 3 working days.

Output: markdown; header line (reviewer, model, date); the DECISION in bold on the first
line after the header; then sections 1-5. Be concrete enough that the orchestrator can
execute without making a scientific choice.
