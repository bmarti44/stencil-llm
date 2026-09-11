You are Astra (gpt-6-astra), acting as an adversarial, author-disjoint reviewer. Use maximum reasoning effort. You have READ-ONLY access to the repository at /home/bmarti44/stencil-llm. Do not write, create, or modify any file; do not run any model, GPU, or network process; do not read files under data/bench/ (sealed benchmark contents). Print your complete review as Markdown to stdout. Nothing else is captured.

# The question Brian is asking

Brian (the project owner) wants a blunt, adversarial answer to three questions about this repo as it stands today (2026-09-11):

1. NOVEL: Is there anything here that is genuinely novel relative to the 2024-2026 literature? Name the closest prior work for each candidate and say what, if anything, Stencil adds.
2. MEANINGFUL / IMPACTFUL: Would any of it matter to an outside ML researcher or practitioner if it were published on HuggingFace or arXiv tomorrow? Which result, in what form, and to whom?
3. EASY TO QUICKLY TEST AND ITERATE ON: Given one shared NVIDIA GB10 (119 GB unified memory, ~26 GB currently free because another researcher's llama-server holds 93 GB), Qwen3-1.7B/4B trunks on disk, PyTorch-only code, and a hand-rolled bitwise-deterministic qwen3.py with attention-bias hooks, can the promising directions be tested in runs of <= 1 GPU-hour each with a fast iteration loop? What in the codebase or process makes iteration slow, and what would you cut?

# Context you may rely on but MUST spot-check (do not re-audit everything)

Three independent audits were completed today. Their conclusions:

Positive results:
- Leg B (Qwen3-1.7B, Multi-IF 909 conversations, public benchmark): pin selected historical KV columns + echo their text after pre-query eviction. full 65.2%, evicted 16.7%, clf pin+echo 59.2%, role-rule pin 60.5%. C1/C3 pass with clustered t + Holm; C2 FAILS: a parameter-free role/recency rule beats the trained 133M bge selector by 3.5 pts. No echo-only arm exists, so KV pinning vs text echo is unidentified. Records: LEDGER-PLAN.md lines ~793-842, results/astra-program-review.md, scripts/multiif_evict.py, results/qwen/multiif-evict-909-prequery-v2/.
- Internal wave (Qwen3-1.7B, synthetic coding sessions, n=96): 264k-param controller reads block-20 hidden states, emits a per-step positional pre-softmax attention-bias field trained by CE through the frozen trunk. Adherence 25.2 -> 44.8; beats oracle 38.3, proxy 37.4, text reinsertion 43.0 (which broke 30 works). One seed, no p-value, comment rule-type 0/120 in all arms. results/internal-wave-report.md, src/stencil/wave.py, scripts/w0_train.py, scripts/w_seal.py, deploy/stencil_wave/.
- SELECTOR (Qwen3-1.7B, synthetic named-query task, N=32 obligations): learned 5-bit span address + attention spotlight layers 20-27: 3.9 -> 88.3. Its own reviewer (results/selector-review-sol.md:80-88) says the task is solvable by dictionary lookup; retrieval and LoRA baselines were mandated and never run. results/selector-report.md, src/stencil/qwen_task.py, scripts/selector_s3_final.py.
- GPT-2 focus cache: 100% vs 4.3% with wire zeroed; gap guaranteed by construction (windowed attention, 16-answer space). results/gpt2-report.md.
- larger-test-v2 (Qwen3-30B-A3B, 64 authored 16-round coding episodes): register vs no-register delivery 35/0/28 p=3e-11, but a plain prose reminder ties or beats the register on every family and the register loses semantic integration 45 vs 52 (p=.0078). FOCUS-2d (256 episodes): placement+eviction 143/256 vs prose restatement 176/256.
- The README's W3 bullet ("+42 points p~4e-12, 73/73 never wrong") describes two FAILED registered gates (WORKLOG.md ~1326-1337, results/w3-results-sol.md).

Negative results, re-verified: solid negatives include static always-on attention bias (n=196), deficit-gated bias on single-turn IFEval (n=1024, +0.39, p=.389), mean-difference skill vectors (18 cells, 0 induction), MoE router bias harming competence, C2, FOCUS-2d. NARROW negatives whose idea is NOT ruled out: deficit/classifier-gated bias on cache columns (single dose imported from a single-span calibration into a multi-span regime, n=20, absolute degeneracy kill rule; the primary arm gained +3 with 4 wins/1 loss and matched full context 44/44 before being killed on 8/20 512-token loops; results/gated-wave-review-fable.md:77-97, results/quick-checks/README.md:244-253); function-vector residual steering (operating point chosen on 4 examples by non-degeneracy only; results/qwen/fv-vectors/grid.json has no efficacy field). Process failures: check42 (A beat C 151/192 vs 131/192 but labelled NOT CLOSED on a token-cap clause); FOCUS-3 v3-v8 six INELIGIBLE on CPU counters followed by an unlabelled v8 diagnostic scoring automatic 57/64 vs none 29/64; four source-replay bank stalls on single authoring defects under a no-repair protocol.

Cross-cutting: the best-replicated finding is that restating the correct current rule in prose at request time beats every structured or internal mechanism tried.

Engineering: 246 review documents vs 181 experiment scripts; plan/PROTOCOL.md is missing (archived copy governs); license conflict (root GPLv2, deploy/ MIT, model card apache-2.0); headline evidence files (results/qwen/s3-*.json, s3-selector-weights.pt, w0-ce.pt, w0-proxy.pt, all of results/gpt2/) are gitignored and untracked; 215 unpushed commits; 57 GB of untracked MoE weights not gitignored.

Literature the audits found (verify or extend from your own knowledge; no network): PASTA (Zhang et al.), SpotLight (EACL 2026), InstABoost (ICLR 2026) — attention steering toward a USER-SPECIFIED instruction span, single-turn; none learns which of many instructions governs now. V-Steer (arXiv 2607.26228) value-cache edits for instruction hierarchy. Memory Inception (2605.06225) KV banks at selected layers. Knowledge Packs (2604.03270) exact KV injection. IFScale (2507.11538), ManyIFEval (2509.21051): compliance collapses as instruction count grows. MemoryCode (ACL 2025, Apache-2.0): coding conventions with updates across sessions, regex-checked, Llama-3.1-8B 71.7% -> 12.5%. Steering-vector reliability papers (2504.04635, 2505.22637, 2602.17881). Instruction (In)Stability (COLM 2024). LKV learned KV eviction (2605.06676).

# What to do

- Spot-check at least: README.md, results/selector-report.md, results/internal-wave-report.md, results/gated-wave-review-fable.md, results/quick-checks/README.md (the check 28 and check 30 sections), results/astra-drift-assessment.md, results/CURRENT-GOAL.md, src/stencil/wave.py, src/stencil/qwen3.py (the attention-bias hook), scripts/multiif_evict.py (arm definitions), and deploy/stencil_wave/MODEL_CARD.md. Cite file:line for every claim you make about the repo.
- Be adversarial toward BOTH the repo's claims AND the audits' conclusions above. If you think an audit conclusion is wrong, say so with evidence.
- Do not soften. If the honest answer to "is this novel" is "no", say so and say what the nearest prior work already did. If the honest answer to "is this impactful" is "only as a negative result", say so and say which negative and for whom.
- Give a single ranked shortlist (at most 3) of the directions that best satisfy all three criteria simultaneously, each with: the claim, the closest prior work, the cheapest decisive test (arms, N, statistic, GPU-hours on Qwen3-1.7B), and the biggest risk.
- End with a scored verdict: NOVEL 0-10, IMPACT 0-10, ITERATION-SPEED 0-10, with one sentence each, and a one-paragraph recommendation to Brian.

Length: as long as needed for evidence, but every paragraph must carry a finding. No preamble.
