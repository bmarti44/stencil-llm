# Synthesis — a selection mechanism that generalizes (2026-09-02)

Sources: results/research-generalizing-{fable,sol,kimi}.md (deep web research, ~100 fetches; claims tagged
verified/inferred in each), results/agentic-salience-review-{fable,sol,kimi}.md (the withdrawn selective-regex draft,
REWORK 2:1). Brian's directive: "we need to do something that generalizes."

## Where the three agree (verified in primary sources)
1. Attention heavy-hitters (H2O/SnapKV/TOVA/StreamingLLM/PyramidKV) fail exactly on our problem: need is delayed.
   SCBench multi-turn: full 48.7 vs SnapKV 20.9 vs StreamingLLM 15.5 (Llama-3.1-8B); SnapKV ~100% → ~3% by turn 2
   on KV retrieval; every eviction policy drops whole IFEval instruction classes; six baselines score 0% on dormant
   credential tokens. Attention is evidence of past use, not future need. Published fixes are hand-built whitelists —
   the regex we are trying to escape. => heavy-hitters are CONTROLS, never candidates.
2. Learned write-time policies transfer across domains but are unproven on tool use: TRIM-KV (math-trained) 44.8 vs
   27.7 heuristics on LongMemEval yet 0 on SCBench random-KV retrieval at 4k; Apple KVP zero-shot to 5 tasks; MemGym's
   learned critic AUROC 0.985 in-distribution vs ~0.43 out of distribution. No paper evaluates KV eviction on
   BFCL/τ-bench at all. => cross-corpus transfer must be MEASURED leave-one-corpus-out, never assumed.
3. Label-free, model-derived importance exists and transfers: KVzip (reconstruction-based, query-agnostic, 3–4× cache
   reduction with negligible loss across QA/retrieval/reasoning/code). "When Attention Closes": attention to
   instructions decays 27–48% over 50 turns while linear probes on the residual stream recover recall outcomes with
   AUC up to 0.99 — a read-time need signal exists in the hidden state. => G0/G1 are credible, not novel.
4. Self-summary ≈ observation masking at frontier scale, lengthens trajectories ~15%, unstable under repeated
   compaction; agent-memory modules' gains are embedding confounds. => self-echo is a reported arm only.
5. Protocol invariants (system prompt + tool schemas) are protected by ROLE, not learned. Our BFCL harness evicts
   them first (column 0) — a CRITICAL harness bug (fable), independent of any selector.
6. Miller (WM 2.0; Lundqvist 2016/2018; Miller & Buschman): selection is READ-time, anticipatory, item-level, with
   explicit clearing; "synapses store representations, wave dynamics determine which are active." A write-time
   importance probe is not "waves select"; a read-time per-span selection at each turn from a store that keeps
   everything is a defensible analogue. Call it Miller-inspired engineering, not evidence for the theory.

## Where they differ, and the resolution
- sol: reversible two-tier memory (lossless archive of evicted spans + query-time retrieval with the NOW-KNOWN query
  + verbatim echo), G0/G1 only as a bounded bet. kimi: G0 with a KVzip-style label + G1 probe as the main line.
  fable: G0 as an AUDIT first — measure how much oracle utility each zero-training policy already recovers; if a
  structural/retrieval proxy reaches ≥0.8 recovery, skip G1 entirely.
- Resolution (do not over-engineer): fable's ordering with sol's archive as one of the zero-training policies. Learn
  a probe only if no zero-training policy recovers enough of the oracle.

## The design: G0 audit → zero-training policies → (only if needed) G1
SUPERSEDED DEVELOPMENT PROPOSAL (2026-09-04, astra program review): the BFCL/Multi-IF fitting and policy-selection
suggestions below must not be executed. LEDGER-PLAN.md, G0 Amendment v2, governs: benchmark prompts, responses and
outcomes must not select or fit policies. This synthesis records how the proposal developed; it is not the current
training brief.
G0 oracle (label-free, deployment-matched): for a dialogue with a reference continuation (gold tool calls for BFCL;
the base model's OWN full-context responses for Multi-IF, i.e. self-distillation), utility of a candidate span s =
mean over later reference tokens of [NLL with s's KV COLUMNS evicted − NLL full], teacher-forced, columns removed via
KVCache.evict (never by deleting text). Candidates: role-tagged spans (system/schema, user, assistant, tool), 64–128
tokens or sentence-bounded, ≤12 per dialogue stratified by role. Signed utilities kept; joint-eviction replay of any
selected SET (utilities are non-additive). Position-matched null: random spans of the same role/length/age.
Zero-training policies scored by oracle recovery at a fixed K and fixed echo budget: (a) role rule (protect
system+schemas, keep all prior user turns); (b) recent+sinks; (c) query-time retrieval from a lossless archive
(BM25 over evicted spans with the current turn as query); (d) salience2 linguistic finder; (e) attention-mass
(SnapKV-style, as the predicted-failure control). Floors registered before the run.
G1 (conditional): a linear ranker over frozen hidden states (layer chosen by held-out sweep, not assumed 20) +
role + position + length, trained on pooled G0 utilities, evaluated leave-one-corpus-out (AUROC ≥0.80 on the held-out
corpus, oracle recovery ≥0.5, beats best zero-training policy under joint eviction with paired 95% CI excluding 0).
Deployment: unchanged — retention only (KV pin through eviction + verbatim echo), random-span control token-matched
from the SAME role pool as the treatment, protected prefix in every arm.

## Sanity first (sol rule 10, fable's cost estimate)
Before any 1k-dialogue oracle: a 30-dialogue-per-corpus timing and signal check on 1.7B (Multi-IF sessions from
mt-train-300 with recorded base responses; BFCL non-cohort long_context with gold calls). Report per-dialogue seconds,
the utility distribution vs the position-matched null, and the recovery of policies (a)–(e). Estimated 1–3 GPU-h.

## Do-not list (union)
Answer literals as the oracle label; random-conversation splits; attention as a causal label; deleting text to
simulate eviction; token AUROC without joint-eviction task success; unequal echo/cache budgets; schemas in the
eviction pool; LongMemEval/RULER/perplexity as agentic transfer; discarding raw history; a full oracle run before the
30-dialogue sanity check; assuming layer 20 on 4B; claiming "waves select" for a write-time probe.
