You are Astra, read-only research strategist for the Stencil program. Brian (the owner) asks:
"use astra to figure out the next best research path for this." Do NOT read anything under
data/bench/. Do not run models, use the GPU, or write files. Recompute numbers you rely on.

## The goal (Brian, 2026-09-11, unchanged)
Build and publish ONE HuggingFace model artifact that keeps focus on the relevant instructions
for a task over a long-horizon agentic coding session, and PROVE that the artifact outperforms
the same artifact with the modification turned off. Repo is already cleaned.

## Where the program stands (read these, in this order)
1. plan/LEDGER.md — the last ~8 entries (from "EXP 4B REGISTERED" to the STATE line at
   2026-09-12 11:55Z).
2. results/memorycode-long/RESULTS-4B.md and setup_long-4b-role_evicted/summary.json:
   the Qwen3-4B SETUP-LONG qualification FAILED on one focus-only unparsable output (1/16 >
   5%), while oracle per-constraint compliance .263 (≥ .20) and focus − base +4.3 points
   [+0.1, +9.5] (4W/1L/11T) passed. Strict compliance 0/16 on every arm. SCREEN never opened.
3. results/memorycode-long/REGISTRATION-4B.md (+ amendment 1), REGISTRATION.md (Exp 4,
   1.7B; amendments 1-2), results/memorycode-long/setup_long-role_evicted/summary.json
   (1.7B: focus − base −5.2 [−10.6, −0.4]).
4. results/reviews/2026-09-12-options-memo.md (the seven ranked options and the pass@k
   diagnostic), 2026-09-12-exp4-floor-consult-astra.md (your floor consult),
   2026-09-12-web-research-steering-and-compliance.md and
   2026-09-12-web-research-small-model-compliance.md (literature),
   2026-09-12-exp4b-impl-review-astra.md (your implementation review), and
   2026-09-12-exp4b-result-audit-astra.md IF it exists (your result audit, may still be
   running).
5. plan/BACK-ON-TRACK-PLAN.md sections G, H, J, D (rules D1-D10; D2 = two policy revisions
   per program, both now consumed), E (GPU sharing: one GB10, ≤ 4,096-token contexts, no
   30B runs, slices ≤ 55 min), I.
6. The package: deploy/stencil_focus/ (MODEL_CARD.md, stencil_focus/focus_session.py,
   modeling_stencil_focus.py) — what the artifact is today.
7. results/memorycode-derived/setup-4b/summary.json and CONTRACT.md (4B short cohort;
   register/restate/oracle numbers), results/memorycode-derived/auto/summary.json
   (the classifier register overflows on the long cohort).
8. Trunks available locally: Qwen3-1.7B, Qwen3-4B (bf16, hand-rolled deterministic runtime
   + HF copies). GPU: one GB10, 119 GB unified; ~10.7 tok/s at 4B for 3.6k-token prompts.
   Measured costs: 4B ≈ 40 s/generation at W = 3,584 + 512 new tokens.

## Constraints that bind any recommendation
- Proof must be "artifact vs same artifact with the modification off", paired, pre-registered,
  with exhaustive readings; no fitting, selecting or tuning on any evaluation benchmark or
  on recorded responses to its prompts (data-lineage line required). The benchmark's own
  regex checker may never be part of the intervention (label leak).
- The program's two policy revisions are consumed: anything further is a NEW registration
  that Brian must authorize, and must disclose what was seen before it was written
  (everything above is already seen).
- Contexts ≤ 4,096 tokens, no 30B models, GPU shared with a peer session, runs in ≤ 55-min
  slices. Realistic budget for the next step: ≤ 10 GPU-h and ≤ 3 working days of CPU/authoring.
- Honesty rules: descriptive vs confirmatory labelling; NOT PROVEN is final for a
  registration; the stop rule is mechanical.

## What we want from you
1. A diagnosis in one paragraph: what the Exp 4 / 4B evidence actually says about (a) the
   trunk (1.7B vs 4B), (b) the mechanism (verbatim evicted-sentence restatement, E = 256),
   (c) the workload (MemoryCode-derived LONG items, dense counter-intuitive conventions,
   strict conjunction), and (d) the gate that failed (focus-only output-failure discordance
   at n = 16). Separate "the mechanism does not help" from "the instrument cannot see it".
2. Rank the candidate next paths by probability of ending with a PROVEN artifact within the
   budget, with GPU-h and authoring cost, and what the claim would then say. Consider at
   least: (i) re-register Exp 4B with an output-failure gate that is interval- or net-based
   (what exactly must be disclosed, and is it defensible or is it fitting on the result?);
   (ii) run the 128-item 4B SCREEN as a pre-registered NEW registration with the SAME
   per-constraint primary and the failure guard moved to a reported excess-over-base at
   N = 128 instead of a launch gate (the options memo's path 1+3); (iii) the
   sparse-instruction fresh-authored long workload with a generic linter as verifier
   (options memo path 2 / path 7 admissible version); (iv) the pass@8 oracle diagnostic
   first; (v) reminder placement/format changes (the literature says null — confirm or
   refute for THIS failure mode: the focus-only failure was an unparsable output, i.e. the
   reminder may be breaking the code-fence behaviour); (vi) a relevance-ranked reminder
   instead of newest-first; (vii) attention bias on the reminder span at 4B; (viii) RLVR.
   Add any path we have not listed that the evidence supports.
3. For your top recommendation, write the registration skeleton: items/workload, arms,
   primary estimand, test and N with a power statement derived from the SETUP-LONG 4B
   spread (paired differences; recompute the SD from the 16 records), the output-failure
   guard as an excess-over-base estimand with its own interval rather than an integer gate,
   exhaustive readings, budget from the measured 40 s/generation, and the exact disclosure
   paragraph about what was seen first.
4. Say plainly whether the honest move is instead to publish the negative and the package
   descriptively and end the line. If a third registration is defensible, say why it is not
   "one more fix" in the sense of the amendment-spiral lesson in AGENTS.md.

Output: markdown with a header line (reviewer, model, date), a one-paragraph recommendation
first, then the four sections above. Cite file:line for every number you use.
