# Round 6: generate-then-disprove, widened search space

Rounds 1–5 (`results/reviews/2026-09-12-direction-adversarial-rev2-astra.md`,
`…-rev3-…`, `…-rev4-…`, `…-rev5-…`) rejected every proposed direction (runtime enforcement,
focal delivery D, dependency-aware delivery E1, revalidated examples E2, compiled
demonstrations E3) on the same criterion, "good chance of actually working". All five
were reminder-style, inference-time wrappers built from the repository's present assets,
and your round-5 judgment that "no presently specified direction supported by these assets
earns a defensible good chance" was scoped to that family. The owner's goal is not scoped
that way. This round widens the space and inverts the roles: you generate, then you
attack your own candidates with the same rigor you applied to the author's.

## The owner's goal (verbatim)

"we need to make sure we find a novel, useful recombination of techniques that is not
technically novel based on a meaningless permutation, that is a significant difference,
and that has a good chance of actually working based on current research, not only in
the AI domains - but also all other academic domains."

The objective the direction must serve (owner, 2026-09-11): build and publish ONE
HuggingFace model artifact that keeps focus on the relevant instructions for a task over
a long-horizon agentic coding session, and PROVE that it outperforms the same artifact
with the modification off.

## Hard constraints (repository policy; do not propose around them)

- Compute: one NVIDIA GB10 (119 GB unified, shared with another job of ~30 GB); no 30B
  models; evaluation contexts ≤ 4,096 tokens; fine-tuning of models up to ~4B (full or
  adapter) is feasible; training runs of tens of GPU-hours are feasible; hundreds are not.
- Never fit, select or tune on evaluation benchmarks (`data/bench/` is off limits to you
  and to training). Training data must be authored or drawn from sources disjoint from
  the evaluation.
- The proof is a registered, paired comparison of the artifact against itself with the
  modification off, with functional correctness AND instruction compliance measured
  together (round-5 lesson).
- No new review stages; one registration, one implementation review, one result audit.

## What you may draw on

Anything: training-time methods (instruction-retention fine-tuning, contrastive or
consistency objectives over long sessions, synthetic long-session curricula, distillation
from a larger teacher on authored sessions, preference optimisation for rule adherence),
decoding-time methods (constrained decoding, monitors, anchoring, contrastive decoding
against a rule-blind branch), representation-level methods (steering, adapters gated by
rule state), tool/harness designs (linters compiled from rules, test-first scaffolds,
diff-based rule checks feeding back into generation), memory architectures, and
non-AI domains (human factors, prospective memory, checklists in aviation/medicine,
instructional design, organisational routines, legal drafting, quality engineering).
The repository's existing negatives (`README.md`, `results/memorycode-long/RESULTS-4C.md`,
`plan/LEDGER.md`) are prior evidence, not constraints.

## Task

1. Generate 5–7 candidate directions spanning at least three different mechanism
   classes (not five wrappers). For each: the specific recombination, the prior art it
   recombines (identifiers), the gap, why the cross-domain evidence predicts it works,
   the first cheap disconfirming test (N, arms, outcome, kill rule) within the compute
   constraints, and the path to the published artifact.
2. Attack each candidate as you attacked D/E1/E2/E3: novelty (deep web search through
   today), meaningless-permutation, significance, and chance of working, with
   probability ranges for the first test and for the artifact. Use the same calibration
   as rounds 3–5 so the numbers are comparable (D 20%, E1 ~20%, E2 15–35%, E3 5–15%).
3. Rank the survivors. State plainly whether any candidate reaches a level you would
   call a good chance (say what number you would need), and if none does, state the
   highest-probability candidate and what the owner would have to change (compute,
   model size, objective, or proof standard) for a candidate to reach that level.
4. Anything the owner is not thinking of, including whether the objective itself
   (long-horizon instruction focus proven by self-comparison on a ≤4B model) is the
   binding constraint.

Cite sources with identifiers. Write plainly. Do not soften. Do not read `data/bench/`.
