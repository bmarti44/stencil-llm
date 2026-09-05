# Check43 — CONCEPT-level SUM/PRODUCT router SET

Unregistered, disclosed. Fit/train: none. Profile: seed95061 Python; dose: disjoint seed95062 Python; evaluate: fresh seeds95063/95064 Python/JS.

Implementation choices frozen before outcomes: source section 4 items 1–11 below govern.
Prompts name the language, function, list argument and an explicit loop; the only
text-arm addition is the SUM/PRODUCT sentence before the common neutral suffix.
The four profile tokens are the final four user-content tokens, excluding chat
termination and assistant header; their token IDs must match for all 32 donors.
Profiles include all donors, without success filtering, averaged equally per example.
Grid runs all three doses. Select the smallest qualifying dose, freeze it, then
run its OFF/shuffled/text setup controls (40 more generations). No selection on controls.
The first slice-family setup text-SUM generation is the pilot and is reused in
its setup-control cell: no extra scored generation or outcome-dependent replacement.
Conservative cost uses its seconds/token including prefill and dispatch audit,
96 tokens for every remaining request, plus measured profiling costs, 25% reserve.
The historical budget arithmetic is (37632/15+314+600)*1.25/3600 = 1.1885 h.
OFF paired success means its ONE program passes both distinct operation checks;
swapped pairs score minus as SUM and plus as PRODUCT. Shuffled pairs score the
corresponding signs. Each prompt is one unit; one-sided binomial discordance tails
and Holm correction across three comparisons; Wilson 95% intervals are descriptive.
Collateral uses seed95064 after 10000 discarded PRNG draws, with distinct names/prompts.
Collateral tasks are disjoint explicit SUM/PRODUCT reductions balanced by operation,
language and list family; no newly failed task under either sign versus OFF.
JS shadowing/redeclarations and assignments to const are rejected.
Bounded interpreter: entire function body statically allowlisted, including dead
branches; integer arithmetic, variables, slices/indexing, len/range/min/max,
assignments, if, for/while and returns. No imports, arbitrary calls, mutation,
I/O, recursion, comprehensions, nested functions or unsupported constructs. Require
an executed loop on at least one test. 2000 instructions per input, integers within
2**53-1, arrays/ranges <=64, source <=12000 chars. Python AST and existing Node
syntax parser retained; Node's bundled Acorn supplies JS AST without executing output.
Test cases cover every length 0–8 and negative/zero/repeated operands; all execution
results saved. Unsupported, runtime errors, missing return, no executed loop and
truncation are malformed failures; valid wrong arithmetic is a semantic failure.
Fresh KV is empty (hash recorded); non-text arms must have identical input hashes.
Dispatch pre-hooks verify the actual expert consumer indices/weights against the
router tuple and record per-layer changed top-8 sets and mixture weights, separately
for prefill/decode. OFF full greedy output is compared with hooks removed on the
pilot input; this extra instrumentation generation is explicitly budgeted separately
(up to 96 tokens), excluded from the 392 scored matrix and saved in its own record.
All model parameters require_grad=False, inference only. Unhooked OFF replay is
instrumentation, not a replacement. Per-token reserve uses the unchanged consumer's
deadline shifted 30 seconds earlier, giving at least 30 seconds to save/return.
Freeze in two commits: CPU recipe/banks/checker first; profiles, selected dose,
setup records, actual biases and final binding committed before ANY final generation.
Invalid instrumentation -> INVALID; cost/missing required work -> INCOMPLETE;
donor/final text competence or damaged controls -> INELIGIBLE; no safe setup ->
FAIL/NO SAFE SET. Otherwise every PASS gate is conjunctive; missed gate -> FAIL.
No fitting/training, benchmark data, check40/41 banks, sealed inputs, signals or push.

## Governing source, verbatim

**4. One proposed SET-only screen: additive versus multiplicative aggregation**

Why this pair: both are broadly pretrained, short, compositional operations with unambiguous executable outputs. An external SUM/PRODUCT/OFF state selects the intended operation while visible inputs retain all operands. The experiment asks whether routing can select semantic computation while language remains fixed. It does not claim that an addition SAE found in Claude corresponds to a particular Qwen expert or that reductions share one universal neuron.

1. **Lineage/freeze:** no weight fitting; profile only newly authored Python cued tasks (seed 95061), select one dose on disjoint Python setup prompts (95062), evaluate fresh banks (95063/95064), balanced over Python/JS. No benchmark prompts, responses, published expert IDs or check40/41 banks. Freeze prompts, checkers, seeds, gains, hook, hashes and reading before final generation; never replace failed examples.
2. **Task:** request one function returning a scalar reduction of a supplied integer list, with language and explicit-loop requirement fixed in text; omit only SUM/PRODUCT in non-text arms. Use whole-list/prefix/suffix/slice variants, distinct names/paraphrases and bounded integer operands. Controller sees only SUM/PRODUCT/OFF, no answer. Require competence in both modes; unsupported/truncated replies count as failures.
3. **Discovery:** 16 Python task pairs, explicit SUM and PRODUCT cues, both executable; require ≥15/16 competent per direction. Record raw router logits over the same last four neutral prompt tokens before code generation, not over operation-specific generated syntax. Average by example, not token count. Define `b_l = (mean_SUM - mean_PRODUCT)/2`, subtract its expert-wise mean; freeze zero-indexed layers 7–34 and zero elsewhere. This middle band is an informed prior, not proven code localization.
4. **Actuator/setup:** use the verified 40b router consumer, adding `±alpha*b_l` before softmax/top-8/renormalization, during current prefill and every decode step. Keep k=8 and all weights frozen. Grid only alpha={1,2,3}, eight Python setup prompts, both signs. Select the smallest alpha achieving ≥6/8 **paired** SUM-and-PRODUCT executable successes and zero malformed/nonterminating replies; if none, stop FAIL/NO SAFE SET. No JS-informed dose selection or second actuator.
5. **Controls:** same-prompt `+b`, `-b`, matched-norm per-layer expert-index shuffled `+b/-b`, OFF, text-SUM and text-PRODUCT: seven generations/prompt. Reuse opposite-sign outputs as swapped controls. Shuffle once using seed 95062, preserving exact within-layer values; no damaged null accepted. Setup totals 8×(six grid outputs + OFF + two shuffled + two textual)=88 generations; freeze then audit selected-dose controls.
6. **Executable checker:** parse the **entire extracted code body**, require only the declared callable, then evaluate supported ASTs with an instruction budget; reject unsupported constructs. Python AST and a JS parser feed a small bounded interpreter for assignments, arithmetic, indexing/slices and loops. Validate its results against hand-written functions on both sides before model use. Test lengths 0–8, negatives, zeros, repeats and multiple novel inputs per function; exact integer outputs and no input mutation/I/O required. Empty SUM=0, PRODUCT=1; include inputs whose answers differ. A fence label, `+`/`*` count, or parser success earns nothing alone.
7. **Final:** 32 fresh prompt instances, 16/language and eight per seed×language, balanced over the four list-selection families; each evaluated in all seven conditions =224 generations. Both addresses start from identical prompt/KV hashes within each instance. The Python-derived direction and dose transfer unchanged to JS. These are two synthetic banks under greedy decoding, not independent model-training seeds or a general code benchmark.
8. **Eligibility/collateral:** text controls ≥15/16 correct for each operation×language; otherwise INELIGIBLE/COMPETENCE. OFF and each shuffled sign must give valid, terminating code on ≥30/32 instances. Add 16 disjoint explicit-operation neutral tasks under OFF/+b/-b (48 generations); require no new task failures versus OFF. Changed routes/weights at dispatch must be recorded, and OFF must reproduce the unhooked consumer's outputs on identical inputs.
9. **PASS:** correct signs produce both intended executable programs on ≥24/32 paired instances, with ≥12/16 per language and ≥5/8 in each seed×language cell; introduce at most one newly malformed/nonterminating reply per sign versus OFF. Require ≥8 more paired successes than shuffled, swapped and OFF, plus one-sided exact paired McNemar tests against those three controls, Holm familywise .05. Use prompt instances as statistical units, not individual runtime inputs. Report discordances, counts and intervals; practical thresholds alone are not evidence of existence.
10. **Budget:** 32 donor +88 setup +224 final +48 collateral =392 generations, each ≤96 new tokens, ≤37,632 decode tokens. At the audit's measured ~15 tok/s, plus 314 s load and an estimated 600 s profiling/prefill allowance, ×1.25 reserve gives **1.188 GPU-h**; this is a projection, not a measurement for these longer tasks. Pilot the slowest setup family and project all remaining costs; refuse an over-1.5-hour matrix, never shrink after outcomes. Cooperative per-token deadline; foreground only, no signals, leave ≥30 s to save/return.
11. **Records/reading:** save prompts, full outputs/token IDs, EOS, seeds, bias/hook hashes, per-layer route changes, all execution results and elapsed allocation time in the same run. Invalid instrumentation→INVALID; cost/missing work→INCOMPLETE; eligibility failure→INELIGIBLE; otherwise missing a gate→FAIL. Language-only movement, both signs producing the same operation, and correct arithmetic with broken programs are failures for this claim. SET PASS warrants later hold/switch/clear; it proves none of those now.

