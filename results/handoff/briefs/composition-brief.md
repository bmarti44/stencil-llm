# Design + research task for gpt-6-astra: the FULL GENERALIZED FOCUS MECHANISM — composing what is proven (2026-09-06)

Brian's instruction: "keep going until you have the full generalized mechanism figured out." Repo /home/bmarti44/
stencil-llm (CPU only; GPU busy; never launch a model; never signal). Proven so far (read the READMEs + fable reviews):
skill half — a sustained router-logit bias on Qwen3-30B-A3B selects a skill family (40b/40c: JS 32/32, 0 broken), holds
it with no text (40d), and the Z schedule (enter = bias + mask of outputs under the previous skill; return to default =
bias OFF + mask) closes set/hold/switch/back/clear (40h/40i, two seeds, zero breakage); concept-level routing closed
(43b); dense-model neurons closed (41/41b); generality beyond Python/JS is being tested now (40g: Go, SQL, TS).
Instruction half — a register of live rules rendered into EVERY request controls behaviour end to end (FOCUS-3 gate:
oracle 61/64 vs ~30 baselines; check 42: every-request rendering 151/192 vs recap 131); the relation classifier
(supersedes/cancels/completes/reinstates) works at runtime (11/12); admission (is this sentence a standing rule?) is
the open piece (check 44 NO-GO for a frozen-LLM extractor; the sentence head is 98% precision / 94% message recall
on realistic messages but ~11% false admits on the gate bank's formal request template; check 44b = message-level
bge tagger running now; first-ship fallback = explicit structured rule entry). Ship form approved by Brian: one HF repo
with custom code (frozen trunk; small classifiers as extra weight files; custom cache class carrying the register +
provenance tags; router-bias hook; renderer; the loop inside generate()).
Deliver results/focus-mechanism-composition-astra.md (<= 160 lines; cite URLs for any external claim; use live web
search where it changes a design choice):
1. THE COMPOSED LOOP per user turn, precisely: admission (detector or explicit entry) -> relation classifier ->
   register precedence -> TASK-TYPE decision (what sets the router bias: the register's live task family; how a task
   type is chosen when several rules are live; when the bias is OFF) -> render live obligations into the request ->
   router bias for the live skill family -> mask outputs produced under a previous skill family (position-preserving
   eviction / attention mask; prefix-cache note) -> one generate() -> provenance tagging of the new outputs.
   State every stop/fail-safe (abstain = today's behaviour).
2. GENERALIZING THE SKILL LEVER: today's profiles are hard-coded per language. Design the PROFILE LIBRARY: how to
   extract a routing profile per skill family from a handful of cued examples automatically (statistic, positions,
   norm-matching to a reference band, validation that shuffled matched-norm control does nothing), how families are
   discovered (clustering routing signatures of cued tasks? a fixed taxonomy? user-declared?), how the task-type
   classifier maps a request/register state to a family, and what happens for unknown families (bias OFF). Cite the
   2025-2026 MoE expert-specialization/steering literature where it informs the statistic or the clustering.
3. WHAT 40g's outcomes change: if Go and SQL generalize; if only languages do; if nothing beyond JS does — the design
   branch for each.
4. THE LARGER IMPLEMENTATION TEST for the composed mechanism ("adequate proof on a larger implementation"): fresh
   multi-turn agentic coding episodes (16-32 turns, 2-3 task switches, 1-2 instruction overrides, tool outputs) with
   executable checkers, arms = composed mechanism (classifier-driven) / oracle-driven / rendering-only / nothing /
   text-restate; endpoints (final success, stale executions, wrong-skill outputs, breakage, cost); N and power; the
   pre-written reading; <= 6 GPU-h; what must be registered first; the honest claim ceiling.
5. Cuts and order. Blunt odds that the composed mechanism passes its larger test within one week.
No repo edits other than writing results/focus-mechanism-composition-astra.md; never read the sealed IFEval input file
or anything under data/bench.
