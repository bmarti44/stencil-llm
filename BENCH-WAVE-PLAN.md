# BENCH-WAVE-PLAN v2 — the wave on real benchmarks

Brian's directive (2026-08-30): prove the wave mechanism generally with
real benchmarks, starting with IFEval, then the most relevant further
evaluations — improvement AND cross-benchmark generalization. Same
fast-iteration reviewer loop.

Grounding: results/internal-wave-report.md (sealed in-harness win;
clean-format win), results/research-benchmarks.md (landscape:
Qwen3-1.7B non-thinking IFEval 68.2 strict-prompt SAMPLED — anchors
only; no IFEval train split — training uses synthetic constraints;
notable steering deltas on 2-8B models: +3-7 points; 1 prompt ~ 0.18
strict-prompt points -> paired tests, not thresholds).

## B0 — infrastructure + identity (gates everything)

- B0.1 CHECKPOINT IDENTITY: verify which HF checkpoint our
  parity-proven qwen3-1.7b.pt matches (Qwen/Qwen3-1.7B instruct vs
  -Base) by config + a fresh logit-parity spot check; record. All
  baseline comparisons are scoped to that checkpoint.
- B0.2 IFEval RUNNER: vendor Google's rule-based verifiers (or
  lm-eval's ifeval task via a custom LM object exposing
  generate_until); OUR loop = Qwen3 chat template (non-thinking),
  greedy, max_new registered; deterministic end-to-end. TDD: verifier
  vendoring against 5 hand-built response/constraint fixtures;
  template round-trip test.
- B0.3 OWN BASELINE: base model on the 541 IFEval prompts, greedy;
  report all four metrics. This number (not the published sampled
  68.2) is the comparison root. One run, committed with per-prompt
  records FROM THE START (playbook lesson).

## B1 — zero-shot probe (Brian's instinct; exploratory, cheap)

Attach frozen w0-ce unchanged (K = prompt h20; automatic pressing) and
rerun B0.3's prompts. Report the delta with a paired McNemar
(prompt-level strict) — EXPLORATORY, no pass/fail gate; any signal is
information about transfer distance. Also record gain histograms (is
the gain head quiet off-distribution?).

## B2 — do-no-harm (the removability claim, tested externally)

With w0-ce attached: MMLU (loglikelihood, registered 2k-question
subset seeded), GSM8K (registered 200-item subset, greedy 4-shot).
Gate: paired degradation bounds — MMLU accuracy drop <= 0.5 points,
GSM8K drop <= 1.0 point (both directions reported). A gate FAIL is a
real finding about off-distribution gain firing, reported not hidden.

## B3 — the benchmark wave (the recipe on constraint-following)

Training data (fresh, synthetic; NO IFEval eval items): a registered
generator of verifiable-constraint prompts in the IFEval taxonomy
STYLE but with disjoint parameters/phrasings (AutoIF/IFTRAIN pattern):
N_train = 2,000 prompts x canonical adherent responses BUILT
programmatically (constraint types where a canonical response is
deterministically constructible AND verifiable: case, length ranges,
bullets/sections, keyword inclusion/exclusion, start/end phrases,
JSON). Every canonical response passes its own verifier (W0.0-style
zero-failure freeze). Training: the identical W0 recipe — CE through
the frozen trunk, A2 field over the INSTRUCTION span(s), same
optimizer/init/seeds, wave + matched proxy twin (same actuator, proxy
labels = instruction-span pointing + press-at-response-start) for the
causal comparison.
Gates before eval: G-W0a-style connectivity battery on the new data;
held-out synthetic constraint accuracy improvement; ablation battery
(K-perm / gain-perm / uniform at matched gain, binding <90% each).

## B4 — sealed benchmark evaluation

ONE sealed run each (fail-closed, pinned hashes, per-prompt records in
the artifact from the start):
- IFEval 541 (untouched by anything upstream): arms base / wave /
  proxy. PRIMARY: prompt-level strict accuracy, paired McNemar
  one-sided p < 0.05 AND delta >= +2.0 points (>= ~11 prompts; below
  the +3-7 published steering band but above noise). Causal: wave >
  proxy.
- Multi-IF (English subset, registered size): the long-horizon claim;
  same metrics; EXPLORATORY gate (report, no pass/fail — first
  multi-turn external exposure).
- Do-no-harm rerun WITH the B3 wave (same B2 bounds — now a real gate).
Decision table: IFEval PASS + do-no-harm PASS -> the wave mechanism is
externally validated on its first real benchmark; either FAIL -> honest
negative with autopsy; Multi-IF informs the NEXT benchmark's
registration (cross-benchmark generalization = a fresh checkpoint-iii
registration naming benchmark #3 by what B4 reveals, e.g. FollowBench/
ComplexBench/IFBench for taxonomy hold-out, or RULER-style long-context
if Multi-IF shows length sensitivity).

## Frozen rules

Seeds: synthetic-train generator seed 0; subsets drawn with registered
seed 1; one sealed attempt per B4 item, no redraws. TDD for verifiers,
template, generator, canonical builders. Reviews: (i) this plan,
(ii) B0 results + B3 preregistration details, (iii) pre-B4, (iv) close.
Playbook governs (pipefail, consumer-path tests, per-work records in
sealed artifacts, no top-level work in imported scripts). Every claim
scoped to the verified checkpoint identity and greedy decoding.

## v1.1 (fable checkpoint-i edits; sol round pending)

- B0.1 SETTLED by fable's file-level audit: the local shards are
  BITWISE Qwen/Qwen3-1.7B (instruct) — shard sha256 169ad53e... /
  912becff... match the HF LFS hashes; Base excluded (different repo
  shape/hash). Remaining B0.1 work: fresh logit-parity spot check of
  qwen3-1.7b.pt vs shards; record both shard hashes in the artifact.
- B0.2 additions: ONE-TIME pinned downloads (exact revision + sha256
  recorded, files committed): IFEval input_data.jsonl (541), MMLU
  subset source, GSM8K subset, Multi-IF English subset; NO `datasets`
  dependency. Verifier vendoring: the 4 lm-eval ifeval files +
  langdetect/immutabledict/nltk pinned in pyproject + punkt_tab
  COMMITTED to the repo with instructions_util's TOP-LEVEL
  download_nltk_resources() call patched to a local-path assert (the
  no-top-level-work rule applies to vendored code); confirm `random`
  unused on the checking path. Fixtures must include one
  sentence-count (nltk) and one langdetect constraint. Chat template:
  pinned deterministic f-string for non-thinking single-turn,
  verified against HF apply_chat_template in an ISOLATED oracle env
  (convert-script pattern); stop on token 151645; greedy.
- Checkpoint-ii registration list (frozen before B0.3): max_new;
  stop rule; Multi-IF English subset size; MMLU subset source split +
  shuffling procedure.
- B3 additions: an explicit CONSTRAINT-COMPATIBILITY MATRIX (JSON
  cannot co-occur with bullets/paragraphs/start-end; end-with is
  exact-suffix; word counts use the VERIFIER'S tokenizer); the
  keyword-forbidden generator excludes stopwords and the entire
  filler-template lexicon; every canonical response verified by the
  VENDORED checker before freeze.
- B4: exact one-sided BINOMIAL McNemar; the full discordant table
  (b, c) goes in the artifact.
- FIREWALL: B3 generator parameters/phrasings may not be derived from
  inspection of per-prompt B1 IFEval failures (taxonomy-level use
  only) — closes the B1->B4 adaptive-leak path.

## v2 (sol checkpoint-i: 1 CRITICAL + 6 HIGH; all folded — SUPERSEDES
conflicting v1/v1.1 text)

C1. SEALED ORDERING FIXED: the 541 IFEval prompts are touched EXACTLY
ONCE, by the sealed B4 job (base/wave/proxy in one run). B0 uses
hand-built fixtures and NON-IFEval smoke prompts only; B3 (generator,
proxy, recipe, eval code) freezes fully at checkpoint ii BEFORE any
541 exposure; the zero-shot probe (old B1) MOVES AFTER B4 (run on the
same sealed artifacts' base outputs is impossible — it becomes its own
post-B4 exploratory run, disclosed as post-seal).

H1. RUNNER: ONE implementation — a direct deterministic runner with a
commit-pinned copy of Google's official data + verifiers for IFEval;
lm-eval (pinned) ONLY as an adapter for MMLU-Redux/GSM8K. Verifier
goldens: positive AND targeted-negative fixtures for EVERY instruction
class present in the 541, plus four-metric aggregate parity against
the pinned upstream evaluator on a fixed response set. RUNTIME
ADMISSION: a 20-prompt generation timing test BEFORE B0.3; registered
max_new, EOS ids (151645 + 151643), truncation accounting; if the
full-forward runtime exceeds the registered bound, implement KV cache
with token-by-token parity vs full forward INCLUDING the wave bias.

H2. B0.1 provenance: record repo+revision (local metadata:
70d244cc86ccca08cf5af4e1e306ecf908b1ad5e), sha256 of config/tokenizer/
index/shards/converted .pt; fresh parity = identical chat-template
token ids (enable_thinking=False) AND last-token logits/top-1 vs
transformers 4.51.0 loading that exact revision in the isolated oracle
env. ALL claims scoped: "Qwen/Qwen3-1.7B@70d244cc, post-trained,
non-thinking, greedy". 68.2 remains anchor-only (Qwen recommends
sampled non-thinking).

H3. B2 fixed: dataset = MMLU-Redux (pinned revision, registered prompt
format + shot policy) and GSM8K FULL test set (1,319 items, 4-shot
with the four demonstrations and answer extractor frozen at
checkpoint ii; the 200-item bound was statistically impossible).
Bounds become registered paired non-inferiority tests; subsets, where
used, are committed item-ID manifests, not seed descriptions.

H4. B3 separation upgraded: constraint-FAMILY holdout (train families
vs held families evaluated separately: per-family seen-vs-unseen
reporting); disjoint semantic tasks/templates/parameters/canonical
responses with normalized leak checks and committed manifests; the
compatibility matrix (v1.1) plus, for EVERY accepted combination, a
passing canonical response AND a targeted mutation that fails the
intended verifier.

H5. PROXY MATCHED: identical response-row support — proxy gain
supervised on every teacher-forced response row (or a preregistered
per-constraint relevance mask), span CE over all active constraint
spans at those same rows; architecture/actuator/init/optimizer/steps
identical. Otherwise the claim is scoped to "CE beats a start-only
heuristic".

H6. B4 causal gate: wave-vs-proxy requires its OWN one-sided
prompt-level exact binomial McNemar p < 0.05 (raw inequality
insufficient). Benchmark #3 PREREGISTERED NOW: IFBench (58 OOD
verifier families) as the cross-taxonomy test; Multi-IF described as
exploratory three-turn transfer, not long-horizon. External-validation
claims require a SECOND frozen training seed (registered now: init
seeds 0 and 1, both trained, both evaluated in B4; the claim needs
both to pass the primary gate).

H7. Seeds/manifests: exact train/dev/calibration streams, dataset
revisions, and committed item manifests replace the two generic seeds.

## v2.1 (sol round 2, four HIGHs)

- SINGLE-USE INVARIANT (precise): "No model generation, scoring,
  per-prompt inspection, or error analysis of the 541 before the
  sealed B4 job; vendoring the data and deriving the class inventory
  are permitted non-generative exposure; post-seal reuse (incl. the
  zero-shot probe) is exploratory and permitted, disclosed as
  post-seal." H1's timing admission rebinds to "before B4".
- B0.1 PARITY CRITERIA (frozen): chat-template token ids bitwise
  equal; top-1 equal on every fixture; all logits finite;
  max_abs_error <= 1e-3 (registered tolerance; identity comes from
  file hashes, behavior from these criteria).
- B2 is BLOCKED until checkpoint ii freezes mechanically: MMLU-Redux
  exact revision + item count + manifests; margins with inherited
  status stated; null hypotheses; alpha = 0.05 one-sided; test
  construction (paired exact binomial on discordant items per suite);
  aggregation rule across MMLU subjects (pooled, registered).
- B4 ARMS (one sealed job): base, wave-s0, proxy-s0, wave-s1,
  proxy-s1. Gate mapping: EXTERNAL CLAIM requires BOTH seeds to pass
  the primary gate AND do-no-harm; CAUSAL ATTRIBUTION requires both
  seed-specific causal McNemars to pass; a single-seed pass is
  reported as artifact-specific, not external validation.
- IFBench FULLY PREREGISTERED at checkpoint iii (pre-B4, before any
  B4 result exists): revision, split, metric, the same five arms,
  greedy decoding, effect floor +2.0 points, one-sided exact binomial
  McNemar p < 0.05 per seed, NO retraining between B4 and IFBench
  (the same frozen checkpoints run both).

## v2.2 (sol round 3, two HIGHs)

- B0.1 parity bound corrected to the recorded conversion scale: exact
  token-id equality; all logits finite; top-1 equality on EVERY
  fixture; max_abs_error <= 0.5 (frozen; the recorded HF-parity worst
  error is 0.365 — identity is established by file hashes, behavior by
  top-1 + this bound).
- B2/B4 non-inferiority procedure REGISTERED PROPERLY: a one-sided 95%
  Tango score confidence bound for the paired accuracy difference
  (exact-conditional fallback if the score iteration fails to
  converge); PASS iff the upper degradation bound < the registered
  margin. Exact-binomial McNemar remains ONLY for the superiority
  gates (IFEval primary, causal), where the zero-margin null is the
  correct test.

## v2.3 (sol round 4)

- The undefined "exact-conditional fallback" is REMOVED: the
  non-inferiority procedure FAILS CLOSED — if the Tango score
  iteration does not converge, the gate result is FAIL (reported as
  numerical-failure, not as a policy verdict), no fallback method.

## v3 — checkpoint-ii submission (B0 results + freeze list + B3 prereg; 2026-08-30)

### B0 results (evidence for this review)

- IDENTITY: revision 70d244cc + 7 file sha256s recorded
  (results/qwen/b0-identity.json). Template/ids/top-1 all PASS on all
  fixtures; worst_err 0.6955 EXCEEDS the frozen 0.5 magnitude bound.
  RULING REQUESTED (R1): accept 0.6955 as the recorded bf16 drift
  characterization (top-1 identity everywhere; a magnitude threshold
  grades size, it cannot decide existence — playbook), or demand rework.
- KV CACHE: the registered "token-by-token parity vs full forward" is
  UNPASSABLE in bf16 — cached (GEMV) vs full (GEMM) kernels drift up to
  0.459 (no-bias) / 1.107 (wave-bias) logits while greedy margins go as
  low as 0.103; a flip was observed at step 19/24. RULING REQUESTED
  (R2), amended acceptance already implemented (tests/test_qwen3_kv.py,
  5/5): (a) the cached path IS the deployment semantics for ALL arms,
  bitwise self-deterministic; (b) cross-path drift bounded (<=1.0 /
  <=2.0) with top-1 agreement mandatory at margins above the bound;
  (c) capture_hidden within 5% of activation scale, cosine >= 0.999.
- SCORING: four-metric aggregate parity vs isolated lm_eval==0.4.8 is
  EXACT on all 541 per-prompt dicts (results/qwen/b0-score-parity.json)
  after re-vendoring bitwise from the pip pin (our copy had drifted to
  lm-eval main: greedy-vs-lazy highlight regex). AMENDMENT (R3): the
  v1.1 claim "`random` unused on the checking path" is FALSE — upstream
  draws a random letter on invalid kwargs; exactly 2/541 rows (keys
  1122, 1129) are random-state-sensitive. Registered pin:
  random.seed(row key) before scoring each row, both sides; disclosed
  wherever IFEval numbers are reported.
- TIMING: KV-cached five-arm projection 7.95h (b0-timing-kv.json;
  was 11.35h full-forward). Caveat: smoke gen len ~100; cost is linear
  in generated length with the cache.
- GENERATOR: ONE code path for all arms (stencil.bench.generate_cached);
  wave bias enters via a mid-forward hook at layer 20 reading the SAME
  position's h20 (train-time teacher forcing = test-time semantics);
  hook==direct-bias proven bitwise; hook tensor == return_hidden proven
  bitwise; wave path demonstrably reaches logits (tests 6/6).

### Freeze list (frozen at this checkpoint, before any 541 exposure)

- Decoding: greedy; max_new 1024; EOS {151645, 151643}; truncation
  recorded per prompt; pinned non-thinking template f-string (bitwise
  vs HF apply_chat_template, enable_thinking=False).
- Data pins (data/bench/pins-manifest.json; converted JSONL committed):
  GSM8K test 1319 @ 740312ad; MMLU-Redux-2.0 5700 @ 372ea425; Multi-IF
  4501 @ 0ab97ce0, English subset 909 rows (language=='English',
  sorted by (key, turn_index)).
- MMLU-Redux protocol: items with error_type=="ok" ONLY (5330);
  zero-shot; prompt "Question: {q}\nA. {c0}\nB. {c1}\nC. {c2}\nD. {c3}\n
  Answer:" through the pinned chat template; score = argmax over the
  summed logprob of " A"/" B"/" C"/" D" continuations (loglikelihood,
  no generation); pooled across subjects (registered v2 H3).
- GSM8K protocol: FULL test 1319; 4-shot with the four demos =
  train rows 0-3 of the pinned revision (data/bench/gsm8k_demos.jsonl;
  train raw sha256 ea82612e...); demos joined as Q/A pairs in one user
  message; answer extractor = LAST number in the response (commas and
  $ stripped; regex -?[0-9][0-9,]*\.?[0-9]*), exact match vs the #### 
  gold value.
- Do-no-harm construction (Tango, fail-closed): margins MMLU-Redux
  0.5pt / GSM8K 1.0pt, alpha 0.05 one-sided. Registered rule: with
  discordant counts n10 (base right, wave wrong) and n01 (converse),
  p_up = BetaInv(0.95, n10+1, n01) (exact Clopper-Pearson upper bound),
  drop_up = (2*p_up - 1)*(n10+n01)/N; NON-INFERIOR iff drop_up <=
  margin. Non-convergence or any scoring error = FAIL (fail-closed).
- Multi-IF: English 909, EXPLORATORY (report only), turn-wise IFEval
  metrics via the same vendored verifiers, multi-turn template =
  concatenated pinned single-turn blocks with prior model turns.
- Single-use invariant restated: no model generation, scoring of model
  outputs, or per-prompt inspection of the 541 before sealed B4.

### B3 preregistration details

- Families (IFEval taxonomy groups): change_case, keywords, length,
  detectable_format, detectable_content, combination, punctuation,
  startend, language. TRAIN families: change_case, keywords, length,
  detectable_format, detectable_content, combination. HELD-OUT
  families (zero training exposure): punctuation, startend, language.
  Per-family seen-vs-unseen reporting registered (v2 H4).
- Generator: seed 0; N_train 2000 prompts; 1-3 constraints per prompt
  drawn under the committed compatibility matrix
  (data/b3/compat-matrix.json, to be committed with the generator);
  parameters/phrasings DISJOINT from the 541's by construction
  (registered leak check: normalized instruction text + kwargs of
  every generated prompt vs all 541, zero overlap).
- Canonical responses: builder per constraint combination; EVERY
  canonical response must pass the VENDORED checker for all its
  constraints, and every registered mutation must fail its targeted
  checker, before the training set freezes (committed digests).
- Wave training: the SELECTOR recipe unchanged (CE-through-frozen-trunk
  on canonical adherent completions; A2 peak-normalized field; w_g
  zero/-2 init); TWO seeds (s0, s1). Proxy twins: identical module/
  actuator/optimizer/data ROWS (row-matched, v2 H5), labels from the
  proxy scheme; two seeds.
- B4 arms (one sealed job, per-work records from the first row):
  base, wave-s0, proxy-s0, wave-s1, proxy-s1 on the 541; gates as
  registered in v2 (both seeds must pass for the external claim; exact
  one-sided binomial McNemar, +2.0pt primary on strict-prompt).

## v3.1 — checkpoint-ii round-1 corrections (sol FINDINGS 1-6 + fable
FINDINGS 1-4; 2026-08-30)

### Statistics (FINDING-1, critical — both reviewers)

The v3 Clopper-Pearson plug-in rule is DEAD (type-I 0.45-0.50 at the
margin; NaN at n01=0; mislabeled Tango). Restored registered rule:
one-sided 95% TANGO SCORE upper confidence limit on delta = p10 - p01
(constrained trinomial MLE by bounded maximization; bisection
inversion; ANY non-convergence raises = FAIL). NON-INFERIOR iff
upper limit < margin (STRICT, as in v2.2). Implementation
src/stencil/stats.py; tests/test_noninferiority.py pins the boundary
tables (0,0)/(k,0)/(0,k), monotonicity, and simulated type-I <= 0.08
at both reviewers' counterexample scenarios.

### Identity scoping (FINDING-4 sol / FINDING-2 fable)

b0_identity v2 measures drift over the FULL vocabulary:
worst_err_full_vocab 0.7679. Claim rescoped: source identity by
hashes; template/ids bitwise; top-1 full-vocab equal on all fixtures;
the registered 0.5 magnitude gate FAILED and is recorded as failed.
R1 asks acceptance of the behavioral result WITH the failed magnitude
gate on the record, not a pass.

### KV evidence (FINDING-5 sol)

Per-step drift/margins/agreement committed:
results/qwen/b0-kv-drift.json. Wording rescoped: bounds are
fixture-local characterization; argmax stability is mathematically
guaranteed only where margin > 2*bound; the per-step agreement is an
empirical observation. Consumer-path test added: cached generation
through the ACTUAL sealed trained WaveController (w0-ce.pt),
deterministic — TO BE RE-RUN with the trained benchmark wave at
checkpoint iii before B4. return_hidden with a cache now raises
(fable FINDING-4 foot-gun closed).

### Protocol freezes (FINDING-3 sol)

- MMLU-Redux (loglikelihood, no generation): one KV-cached prefill
  per item per arm (fresh cache; the registered deployment path);
  score = log-softmax at the final position of the four single tokens
  {" A":362, " B":425, " C":356, " D":422} (single-token property
  asserted in-test); argmax vs gold; ties (exact float equality)
  score as WRONG (fail-closed). Wave arms: bias_hook fires at the
  prefill's FINAL ROW ONLY — the row whose logits are scored — with
  the bias row over all prompt positions computed from that row's h20
  (the generation-step semantics applied to the scored position);
  base arm identical with no hook.
- GSM8K serialization (literal): one user message =
  "Question: {q_demo1}\nAnswer: {a_demo1}\n\n" x4 demos (answer text
  verbatim from the pinned train rows INCLUDING their "#### n" line)
  + "Question: {q_test}\nAnswer:"; through the pinned chat template;
  greedy, max_new 1024, EOS {151645,151643}, no other stop strings.
  Extractor: last match of -?[0-9][0-9,]*\.?[0-9]* after removing
  "$"; commas stripped; trailing "." stripped; compared as
  python Decimal equality vs the gold "#### " value.
- Multi-IF: ALL 2727 turns (909 conversations x 3 embedded turns),
  sequential; each arm consumes ITS OWN prior responses. History
  serialization: prior turns as
  "<|im_start|>user\n{p}<|im_end|>\n<|im_start|>assistant\n{r}<|im_end|>\n"
  (no think blocks in history), final turn opens with the pinned
  assistant opener incl. empty think block. Turn t scored with turn
  t's instruction_id_list/kwargs only (per the dataset columns).
  Reporting: per-turn-index (n=909 each) + pooled (n=2727) four
  metrics; EXPLORATORY (unchanged).
- Runtime envelope (FINDING-6): long-output admission COMPLETE
  (results/qwen/b0-timing-long.json): 19.74 tokens/s wave-style at
  full max_new depth (all 8 stress prompts hit the 1024 cap);
  absolute worst-case ceiling 39.0h if EVERY prompt of EVERY arm hits
  max_new (the smoke-mix projection remains 7.95h). Sealed jobs write
  per-prompt records via atomic JSONL append (key, arm, response,
  n_gen, truncated flag) as they complete; on crash, resume SKIPS
  completed (key, arm) pairs exactly (no regeneration, no redraws —
  the one-shot rule is preserved because no completed item is ever
  re-decided). Registered per-prompt hard timeout: 3x the admission's
  slowest per-prompt wall time, recorded as truncated-timeout if hit.

### B3 proxy registration (FINDING-2 sol)

Proxy twin = EXACT w0-proxy objective transplanted: identical module,
actuator, optimizer, steps, seeds, and data ROWS as the wave arm;
loss = BCE(gain logits, timing positives) + mean uniform-within-span
CE(e-logits, span targets), weight 1:1 (as in scripts/w0_train.py).
For B3: timing positives = ALL response rows (the same rows the wave
CE trains through); span targets = each prompt's constraint-
instruction token spans (uniform within each span, averaged over the
prompt's constraints). No gain-conditioning on results.

### B3 materialization (FINDING-2 sol): the generator, compatibility
matrix, canonical/mutation builders, manifests, and template
fingerprints are committed WITH this amendment (src/stencil/b3_gen.py,
data/b3/) and are part of the round-2 review scope. Leak firewall
upgraded from "normalized exact overlap" to: (a) per-instruction-id
generated kwargs tuples DISJOINT from the 541's kwargs tuples,
mechanically asserted; (b) our instruction phrasings are fingerprinted
templates, and no generated instruction sentence appears as a
substring (word-normalized) of any 541 prompt nor vice versa,
mechanically asserted; (c) semantic base tasks from a committed
40-topic lexicon disjoint from 541 topics by the same substring check.

## v3.2 — checkpoint-ii round-2 closures (sol FINDINGS 2/5/6; 2026-08-30)

- MATRIX BUG FIXED (round-2 FINDING-2): compat pairs are now stored in
  canonical sorted order (13 declared pairs had been silently
  unreachable under combo_ok's sorted lookup); a test asserts every
  declared pair is reachable. Structural conflicts surfaced by the fix
  and registered as incompatible: n_sent x n_words_max; the bullets
  builder now lengthens bullets to honor n_words_min. TRAIN RE-FROZEN:
  train-2000.jsonl sha 54cd99f6..., sizes 664/672/664.
- DEV STREAM FROZEN: dev-200.jsonl (seed 2, prompt-disjoint from train
  by registered exclusion, sha 489d1a70...). Checkpoint selection =
  lowest dev-200 CE. No other synthetic streams; held-family
  evaluation happens ONLY on the 541 at B4 (per-family reporting).
- TRAINING SCHEDULE FROZEN: Adam lr 1e-3 betas (0.9, 0.999) eps 1e-8;
  5 epochs over train-2000, gradient accumulation 8, shuffle
  generator seed 0, wave seeds s0=0 / s1=1 (torch.manual_seed);
  checkpoint saved per epoch, selected by dev-200 CE; proxy twins:
  identical schedule/rows, w0-proxy objective with span targets from
  the registered constraint_spans() (committed + tested).
- CONSUMER PATH FIXED (FINDING-5): the registered adapter
  (make_wave_bias_fn) biases the PREFILL'S SCORED ROW from its own
  h20 (the first response token is wave-influenced, matching the MMLU
  registration) and each generation row thereafter; the test now
  asserts a finite NONZERO field, a nonzero wave-vs-zero-field logit
  differential on the same prefix, and deterministic repeat. A direct
  regression test pins the return_hidden+cache guard.
- RUNTIME CONTRACT (FINDING-6): b0_timing_long v2 records per-prompt
  wall times; REGISTERED per-prompt timeout = 300 seconds (literal;
  ~5x the ~52s max_new-saturated admission prompt); a timed-out item
  is recorded truncated-timeout and its partial response is SCORED
  AS-IS (deterministic, disclosed per item). Sealed record protocol:
  each completed (key, arm) record is written to a temp file and
  atomically renamed into the job's records/ directory (crash-safe;
  no partial JSONL tails); resume scans records/, verifies the pinned
  sha256s of model, wave/proxy checkpoints, tokenizer, dataset, and
  runner code BEFORE skipping completed pairs; any hash mismatch
  aborts the resume (fail-closed).
- GSM8K (round-2 ruling): no regex match or invalid Decimal = item
  scored WRONG (registered explicitly; never a job failure).
- STATS WORDING: the Tango bound is disclosed as a NOMINAL asymptotic
  score bound (recomputed exact type-I 0.048/0.050 at the registered
  boundary scenarios), not an exact finite-sample interval; the pure-
  degradation MMLU simulation added to the test suite.

## v3.3 — B3 training amendment: L1 gain penalty removed (2026-08-31)

FLEET STOPPED after epoch 1 of run 1: dev task CE frozen at 5.776607
across epochs; diagnosis (WORKLOG) — trained gains collapsed to
EXACTLY 0 (w_g weights learned to kill the gain through the features;
bias stayed -2.006). Cause: the w0-transplanted L1 gain penalty
(LAM=0.01/row) is 10x larger than this task's per-row CE gradient
(~0.0008), so the penalty wins the race and the wave dies before
learning. Signal EXISTS: a random untrained field at forced gain 2.0
improves dev CE (6.479 -> 6.062; 4.048 -> 3.930).

AMENDMENT: LAM = 0 for B3 wave training (the L1's purpose in W was
timing SELECTIVITY for pressing; B3 constraints are active for the
whole response, and the row-matched proxy's timing target is likewise
all-rows-positive — matched). Everything else in the frozen schedule
is unchanged. Pilot evidence (300 rows, 1 epoch, LAM=0): mean gain
0.238 -> 2.0 within 100 rows; dev CE 5.636 -> 4.598. Collapsed ep0/ep1
checkpoints deleted; fleet relaunches from scratch after review
sign-off of this amendment.

### v3.3 addendum (sol condition, recorded BEFORE relaunch)

- The gain-permutation ablation gate is RETIRED for B3 (inert when gain
  saturates); the gain head is preregistered as potentially decorative.
  RETAINED: K-permutation ablation and the matched-uniform-field
  ablation (random field at matched gain — the pilot's counterfactual,
  now a registered control).
- B4 causal scoping (registered wording): a wave-vs-proxy margin
  supports the TASK-CE TRAINING OBJECTIVE PACKAGE for learning the
  attention field; it does NOT test autonomous timing / when-to-act,
  and is not attributed specifically to addressing unless gain
  distributions are matched. Response-row gain histograms are reported
  for BOTH arms in the B4 artifact.

## v4 — checkpoint-iii submission (pre-B4; 2026-08-31)

### IFBench preregistration (benchmark #3, run POST-B4)

- Source: allenai/IFBench_test (arXiv:2507.02833, NeurIPS 2025 D&B);
  pinned HF revision 2e8a48de45ff3bf41242f927254ca81b59ca3ae2; 300
  rows (recomputed on the pinned file; the paper's "294" is a claim we
  do not inherit); data/bench/ifbench_test.jsonl committed + hashed.
- Taxonomy: ALL 300 rows use only the NEW constraint namespaces
  (count/words/format/repeat/sentence/ratio/custom) — fully DISJOINT
  from IFEval's 25 classes and from every B3 training family: this is
  the registered taxonomy-holdout benchmark. The classic-checker
  landmines (langdetect, random draws in checking) do not apply to
  these rows; the new checkers' random use is in build_description
  only (verification deterministic; will be re-verified by goldens).
- Protocol (registered now, executed post-B4): vendor the ifbench
  verifier package (Apache-2.0) pinned to the GitHub revision matching
  the paper; goldens = positive + targeted-negative fixture per
  instruction class present in the 300 (same discipline as B0.2);
  same five arms, decoding, timeout, atomic records as B4; same
  primary metric (strict-prompt) + McNemar machinery; EXPLORATORY
  until its own pre-run review confirms the vendored goldens.

### B4 execution registration

- IFEval sealed job: scripts/b4_ifeval.py (committed; single-use seal,
  atomic records, hash-verified resume, gain telemetry). Launch order:
  base, wave-s0, proxy-s0, wave-s1, proxy-s1 (sequential, uncontended
  GPU). Controllers: results/qwen/b3-{ce,proxy}-s{0,1}.pt (selected
  checkpoints; sha256s in their .json records).
- Do-no-harm rerun (the BINDING gate): b2_mmlu.py + b2_gsm8k.py with
  CTRL=b3-ce-s0 and b3-ce-s1 (wave arms; margins/Tango as frozen).
  The w0-ce B2 MMLU FAIL (drop upper bound 2.69pt) stands recorded as
  the internal wave's off-distribution answer.
- Multi-IF (exploratory): scripts/b4_multiif.py (committed; smoked on
  1 conversation); PROPOSED arms = base, wave-s0, proxy-s0 (three, not
  five — 2727 turns x 5 arms exceeds the runtime envelope; reviewers
  rule).
- Evidence bundle for this checkpoint: b3-ce/proxy-s0/s1.json (training
  records), b3-ablations.json (K-perm + uniform controls; gain
  saturation), b3-consumer-path.json (all four controllers nonzero
  field + logit movement + deterministic through the cache),
  b2-mmlu-gate.json (FAIL recorded), b2-gsm8k gate (pending, appended
  when the legs finish).

## v4.1 — checkpoint-iii round-2 corrections (2026-08-31)

- SEAL REBUILT (sol FINDING-1, critical): scripts/b4_ifeval.py is now
  ONE entry point with a CLOSED hard-coded arm table (base, wave-s0,
  proxy-s0, wave-s1, proxy-s1 in fixed order), each controller bound
  to its registered selected-checkpoint sha256; one GLOBAL seal
  (results/qwen/b4/.started + manifest.json); resume requires
  byte-exact manifest equality over the FULL pin set: trunk, tokenizer,
  bench/qwen3/wave modules, vendored ifeval verifier tree digest, all
  four controllers, the 541, and the runner itself
  (stencil.bench.provenance_pins). The four selected controllers are
  now GIT-TRACKED (force-added).
- REAL DEADLINE (sol FINDING-2 / fable FINDING-2): generate_cached now
  enforces the 300s per-prompt deadline in the generation loop; a
  timed-out PARTIAL response is scored as-is with the timeout flag in
  the record and all reporting. Registered wording narrowed: the
  truncation point of a timed-out item is load-dependent (the flag is
  a runaway backstop ~5.6x the admission's worst case, not an expected
  path). Gain telemetry includes the prefill's scored row (fable
  FINDING-3).
- B2 BINDING ADJUDICATOR (sol FINDING-3): scripts/b2_adjudicate.py —
  frozen construction; per-item discordances only; registered
  controller hashes enforced; BOTH seeds must pass BOTH suites
  (MMLU < 0.5pt, GSM8K < 1.0pt Tango-strict); fail-closed on any
  missing record/provenance/non-convergence.
- B3 GATES (sol FINDING-4): (a) gradient battery on the REAL loss —
  results/qwen/b3-battery.json PASS (all params finite nonzero;
  dCE/dbias nonzero). (b) REGISTERED BEFORE RUNNING — dev-200
  GENERATION adherence gate: all five arms generate on the dev-200
  prompts (same decoding/deadline as B4); metric = strict-prompt
  adherence (ALL of a row's constraints pass the vendored checkers);
  GATE: each wave seed must exceed base by >= +2.0 points strict-prompt
  (mirrors the B4 primary margin); proxies reported, not gated.
  Artifact: results/qwen/b3-dev-gate.json.
- IFBench wording corrected (sol FINDING-5): "instruction-class /
  checker holdout WITH semantic overlap" (identifiers and checker code
  are disjoint; word-count/format/keyword SEMANTICS overlap B3
  families). Transfer claims are scoped to unseen verifier classes and
  compositions, not wholly unseen constraint semantics. Full verifier
  freeze (vendored ifbench package at a pinned GitHub sha + per-class
  goldens + per-row seed pin where needed + the same aggregate and
  paired-McNemar adjudicator as IFEval) is being committed with this
  amendment; IFBench remains post-B4 in execution and gets its own
  pre-run goldens review.
- Multi-IF (sol FINDING-6): runner hardened to the same closed
  three-arm table (base, wave-s0, proxy-s0), full pin set, real
  deadline, timeout field; exploratory scope unchanged (no two-seed or
  external-validation claims from it).

## v4.4 — B3 recipe amendment (PENDING REVIEW; pilot evidence attached
when ready; 2026-08-31)

Registered dev-gate FAIL for the v3-recipe waves (base 0.865, wave-s0
0.755, wave-s1 0.790, proxy-s0 0.845) triggered the dual failure
analysis + dual data curation (WORKLOG). Amended recipe, per the
converged reviewer prescription:
- DATA: v4.3 curated streams FROZEN (train-v43 1932 rows sha 8a5b083c,
  dev-v43 196 rows sha 4ca86881; sol hand-curation + independent
  re-verification; dev topics DISJOINT from train).
- TRAINER: obligation-span weighted CE (x8 on obligation tokens),
  EOS supervision (id 151645, x8), beta_max 1.0, LAM 0, otherwise the
  frozen v3.2 schedule (Adam 1e-3, 5 epochs, accum 8, shuffle seed 0,
  seeds 0/1, unrounded dev task CE selection).
- GATE: same registered dev generation gate on dev-v43 (196):
  each wave seed >= base + 2.0pts strict adherence; base re-measured
  on dev-v43.
- FIREWALL disclosure: postscript_marker 'P.P.S' exempt from kwargs
  disjointness (upstream regex-escape landmine forces the special-
  cased marker; the postscript VALUE varies per row from the prompt).

## v4.5 — deficit-triggered wave (THE FINAL single-turn rescue;
registered per sol's results review, 2026-08-31)

Motivating evidence (exploratory, scoped): dose sweep on v4.4 wave-s0
(x1.0 0.7959 / x0.5 0.8214 / x0.25 0.8571 vs base 0.8418 on dev-v43;
x0.25 beats base by +1.5pts but n=196 cannot distinguish +1.5 from
+2.0 — best-case paired p=0.125; sweep numbers pending fable's
independent reproduction). Research prior: SpotLight (2505.12025)
deficit-triggered steering with positive IFEval deltas at 3-8B.

MECHANISM (implemented, battery 4/4 green): frozen v4.4 Wq/Wk select
the governing Constraint: span per generated row (first-index
tie-break; no span -> no intervention); per biased layer/head, measure
natural post-softmax mass psi on the span; psi >= tau -> ZERO bias
(bitwise base attention); else uniform span bias
min(b_max, logit(tau) - logit(psi)) (exact odds correction). Every
intervention logged (span, score, per-item records).

CALIBRATION (one shot): frozen tau grid {0.10, 0.20, 0.30, 0.45} x
b_max {3.0, 6.0} on cal-v45 (200 rows, seed 5, prompt-disjoint);
select by adherence, ties -> LOWER intervention rate; base cal run as
reference. No recalibration after confirmation begins.

CONFIRMATION (one shot): conf-v45 (512 rows, seed 7, dev-topic,
prompt-disjoint from everything). GATE: deficit-wave(seed-0 Wq/Wk)
>= base + 2.0pts strict adherence AND one-sided exact McNemar p<0.05
AND no excess timeouts/truncations; per-row records + raw discordants
saved. If seed 0 passes, REPLICATE with seed-1 Wq/Wk (same tau/b_max,
no re-selection); BOTH must pass before sealed IFEval.

STOP-LOSS (registered): this is recipe iteration 3 and the LAST
single-turn rescue. One calibration grid, one confirmation block, no
recalibration/retraining/fallbacks after seeing confirmation. Failure
CLOSES the single-turn synthetic/IFEval wave line (honest negative
with the full autopsy chain already recorded); token-aware contrast or
GRPO training would be a separately authorized program. The x0.25
static dose is carried as a descriptive comparator only.
