# Deep web research for gpt-6-astra: robust detection of STANDING instructions vs one-off requests (the admission problem) — 2026-09-06

Repo /home/bmarti44/stencil-llm (CPU only; a diagnostic gate run holds the GPU; never launch a model; never signal).
Context: results/quick-checks/focus3-gate/v8/ESCALATION.md and RESULTS.md (eight iterations; the relation classifier
and register work; the ADMISSION head — the older rule/fact/none sentence selector, data/classifier/LABELS.md lineage —
still admits one-shot requests carrying data (8/96) and inert quoted text (3/96) as standing rules; each refit moved
errors around; small DEV samples don't reflect the bank's phrasing families); results/focus3-design-astra.md section 4;
data/classifier/LABELS.md; data/classifier/LABELS-RELATIONS.md; results/relations-classifier-report.md.
Use LIVE WEB SEARCH (2023-2026). Deliver results/admission-research-astra.md (<= 110 lines, cite URLs):
1. How production agent-memory systems decide what to WRITE as a durable rule/preference vs a transient request
   (Mem0, Letta/MemGPT, Zep, LangMem, OpenAI/Claude memory features, Cursor rules, "user instruction extraction",
   "persistent preference detection", "memory write policy" papers) — what signals they use, measured precision.
2. Detection formulations with evidence: sentence-level classifiers vs message-level structured extraction (LLM
   emits {rule, scope, key} JSON) vs pairwise/contrastive scoring vs NLI/entailment ("this sentence states a standing
   constraint on future outputs"); robustness to quoted/reported text and to data-bearing requests; failure modes.
3. Data: does the corpus we have (rule/fact/none sentences + 7,749 relation pairs incl. quoted negatives + 300
   request/rule rows) suffice to train a message-level "new standing rule" extractor from base bge-small, or is a
   small seq2seq/LLM extractor (e.g. a 0.6-1.7B instruct model with a constrained JSON schema, frozen, few-shot) the
   right tool; latency/cost per message; how to make it fail safe.
4. RECOMMENDATION: one design for admission that (a) is not string matching, (b) handles quotes/reported speech and
   data-bearing requests, (c) is evaluable against an author-disjoint held-out we can write in a day, (d) fits the
   single-repo ship form; the quick test (<= 1 day, <= 1 GPU-h) with a pre-written reading; blunt odds; what to cut.
HARD RULES: CPU only; no repo edits other than writing results/admission-research-astra.md; never read the sealed
IFEval input file or anything under data/bench.
