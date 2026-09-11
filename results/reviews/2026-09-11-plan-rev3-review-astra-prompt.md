You are Astra (gpt-6-astra), adversarial author-disjoint reviewer, ROUND 2 of a research-plan review. Maximum reasoning effort. READ-ONLY access to /home/bmarti44/stencil-llm; write nothing; run no model/GPU/network; do not read data/bench/ contents. Print your review as Markdown to stdout.

Round 1 (your own review, appended below) scored rev 1 at 24/100 with 34 findings. The orchestrator revised the plan to rev 3 (appended below), adopting most findings and DECLINING five with stated reasons (see the plan's last section).

Brian's instruction for this round, verbatim in spirit: "don't let astra over-engineer it - we need to make sure what we are doing here is on track, there is a decent chance of success, it's aligned with the rigorous academic research available, and it is novel."

So judge rev 3 on exactly four criteria, each scored 0-10 with a one-paragraph justification citing file:line where the repo is involved:
1. ON TRACK: does the plan pursue Brian's stated goals (results/CURRENT-GOAL.md: automated maintenance of correct reminders is the win; a mechanistically interesting proof; an honest, useful HF release) rather than drifting into evaluation machinery or process?
2. CHANCE OF SUCCESS: for each of Exp 1, 2a, 3, give your probability that it produces a clear, publishable answer (positive OR negative) within its stated budget, and the single biggest risk.
3. ALIGNMENT WITH RIGOROUS RESEARCH: are the designs (controls, estimands, tests, N, readings) at the standard of the cited literature (AutoPASTA, SpotLight, Directer, MemoryCode, LKV, exact paired tests)? Name any remaining confound that would make a reviewer reject the result.
4. NOVEL: is the method claim as now stated (a learned per-position, per-step pre-softmax bias field trained through a frozen trunk from completion loss; matched WHERE/WHEN/static controls) defensible as an incremental novelty against the literature the repo has surveyed (results/research-wave-prior-art.md, results/research-sol-web.md, results/astra-research-blockers.md)? Is the product claim honest about being non-novel?

Rules for this round:
- Verify that each round-1 finding you consider material was actually addressed in rev 3; list any material one that was NOT addressed and would still cause a reviewer to reject. Do not re-raise findings the plan declined unless you can show the decline changes a DECISION the plan will make.
- Over-engineering is a defect: if a fix adds author-hours or GPU-hours without changing what Brian will decide, say "not needed" and move on. Do not propose new arms, new benchmarks, or new process unless the plan cannot answer its own readings without them.
- Verify the plan's new factual claims against the repo: the comment-checker bug at src/stencil/t2_runner.py:91-94 and wave_ref.py:29; that seed block 14,700,000+ is unused; the memory figures; the Multi-IF 425-pair/59-singleton source structure; anything else you can check cheaply.
- End with: a total score 0-100 for "execute rev 3 as written", the list of minimum edits (if any) for acceptance at >= 90, and a two-sentence recommendation to Brian.

=== REV 3 PLAN ===
# Stencil: back-on-track research plan (rev 3, 2026-09-11)

## Context

Brian asked for an audit of the Stencil repo: what has actually been proven, whether the
"does not work" claims hold up, what is missing for an honest HuggingFace release, what the
2024-2026 literature already covers, and what experiment would prove something
mechanically interesting. Three read-only audits (positive results, negative results,
engineering/HF readiness), a web-literature pass, an adversarial Astra (gpt-6-astra, xhigh)
review of the repo, and an adversarial Astra review of rev 1 of this plan (24/100, 34
findings) were run. Rev 3 incorporates the findings that add validity and declines the ones
that add machinery without changing a decision (listed at the end). A second researcher
(session "looped-transformer") shares the GB10; the GPU protocol is in section E. Brian's
acceptance criteria for round 2: on track, decent chance of success, aligned with rigorous
published work, novel; over-engineering is a defect.

## Findings (established by the audits; file references are repo-relative)

### What is proven, and how strong it is

| Result | Trunk / data | Numbers | Strength | Gaps |
|---|---|---|---|---|
| Leg B retention under eviction | Qwen3-1.7B, Multi-IF 909 conv = 484 distinct source prompts (public) | full 65.2, evicted 16.7, clf pin-only 57.2, clf pin+echo 59.2, role pin 60.5 (pooled); C1/C3 p~3.7e-85/1.6e-65 conversation-clustered; C2 FAIL: role rule beats trained selector by 3.5 (conv-mean) / 3.3 (pooled) | Only public-benchmark result; 911/911 evidence files tracked | Echo increment given pins IS identified (+2.0); pin-only vs eviction IS identified (83.6% recovery); the pin increment GIVEN echo is not (no echo-only arm); 909 conversations are 425 pairs + 59 singletons sharing first prompts, so clustering must be by source; encoder weights gitignored; registered NOT SUPPORTED on 1 invalid output vs 0 |
| Internal wave | Qwen3-1.7B, synthetic coding sessions, n=96 | 264k-param controller, adherence 25.2->44.8; hand oracle 38.3, proxy 37.4, prose reinsertion 43.0 (+1.7 pts; reinsertion broke 30 works vs 21) | The one plausible method novelty: a learned per-step positional pre-softmax bias field trained through the frozen attention path, with WHERE/WHEN/selectivity ablations | 1 seed, no p-value; the harness re-serializes the generator's exact current ledger every request (src/stencil/t2_sessions.py:295), so it tests attention allocation GIVEN a correct external ledger; W3b readout found the field NOT decodable as "the governing rule now"; w0-ce reduced MMLU 48.05->45.83 and failed GSM8K noninferiority (WORKLOG.md:1586,1613); **the comment-type 0/120 "null" is a checker bug**: `src/stencil/t2_runner.py:91-94` requires the last line of `ast.get_source_segment(code, fn)` to be `# reviewed`, but a function's AST segment ends at its last statement and excludes a trailing comment, and `wave_ref.py:29` generates exactly that form; controller reduces to learned query-key matching plus a scalar gain (wave.py:29); w0-ce.pt untracked |
| SELECTOR | Qwen3-1.7B, synthetic named-query task, N=32, n=128 (5/128 vs 113/128) | 3.9 -> 88.3; reinsertion 84 @ 504 tok from a different block | Clean actuator test, bitwise zero-identity | Task is `current[field]` lookup with the field named (results/selector-review-sol.md:80-88); no retrieval or LoRA baseline; evidence JSON + weights untracked |
| GPT-2 focus cache | GPT-2 small, windowed attention | 100 vs 4.3 zeroed; transplant 28/32 | Clean construction | Gap guaranteed by construction; results/gpt2 0 tracked files |
| larger-test-v2 | Qwen3-30B-A3B, 64 authored episodes | register vs none: delivery 35/0/28 p=3e-11 | Rigorous stats | Prose reminder T ties/beats register on every family; R loses semantic integration 45 vs 52 (p=.0078) |
| FOCUS-3 v8 diagnostic | Qwen3-4B, 64 reused-template episodes | automatic register 57/64 vs none 29/64 vs oracle 63/64 | Encouraging for AUTOMATIC maintenance (Brian's corrected goal) | No verdict assigned; 25 false admissions in 21 episodes are policy failures, not instrument accidents; templates reused |
| W3a | Qwen3-1.7B synthetic, 96 sessions | wave 55.1 vs reinsertion 53.1 vs base 36.6, zero contamination | Qualified clean-format positive | Generalizes to ONE registered unseen rendering only |
| W3 README bullet | | "+42 pts, 73/73 never wrong" | **Misrepresents two FAILED gates** (WORKLOG.md:1326-1337, results/w3-results-sol.md) | Must be rewritten; the W3b readout failure is itself informative |

Cross-cutting, stated precisely: correct request-time restatement of the current rules is the
baseline to beat. No mechanism tried so far has beaten it by more than ~2 points (wave +1.7,
W3a +2.0) and several lost to it (FOCUS-2d 143/256 vs 176/256; larger-test-v2). C2 says nothing
about prose vs structure; it compares two pin-selection policies. Brian has superseded "must
beat manual prose": reliable AUTOMATION of correct reminders at acceptable cost is the win
(results/CURRENT-GOAL.md:3-7).

### Negative claims, re-verified

- Solid (A): static always-on bias (n=196, -4.6 monotone); deficit-gated bias on the
  **synthetic** conf-v45 bank (n=1024, +0.39, p=.389, 8-cell grid; not IFEval,
  WORKLOG.md:2302); mean-difference skill vectors (18 cells, 0 induction, cosines .89-.98);
  MoE router bias harms competence (16/32 -> 7/32, two-sided p=.022); C2; FOCUS-2d;
  cosine-threshold liveness; blind rhythm pressing; hard-threshold abstain.
- Narrow (B), idea not ruled out, no reopen planned: deficit/classifier-gated bias on cache
  columns (check 28: single dose from a single-span calibration applied to ~3.6 spans that
  cannot each hold mass 0.3; n=20; excess degenerate 5/20; 4 wins/1 loss p=.19); function-vector
  residual steering (operating point chosen on 4 examples by non-degeneracy; grid has no
  efficacy field); check43b concept routing (n=8/cell); check32/33 cache transplant (harness
  never qualified; check34 positive control 59/60).
- Process failures (C): x0.25 dosed wave (+1.5 vs +2.0 gate, one item, p=.549); check42
  (A beat C 151/192 vs 131/192; an ancillary arm's cap failures blocked closure); FOCUS-3 v1/v2
  (one sentence template x64); FOCUS-3 v3-v8 six INELIGIBLE on CPU counters; PRESS T1 (92.9%
  leakage reduction vs a bar unreachable at n=17); four source-replay bank stalls on single
  authoring defects under a no-repair protocol.

README.md:69-76 ("every amplification variant ... closed with data") overstates the per-check records.

### Engineering / publication state

- PyTorch only; hand-rolled bitwise-deterministic `src/stencil/qwen3.py` with `bias_hook`
  (line 397) and `return_hidden` (393). The wave evaluator (`scripts/w_seal.py:57`) and trainer
  recompute the full prefix per generated token; `w0_train.py:46` loads the model at import.
  The manual attention path materializes fp32 [16,T,T] scores and [T,151936] fp32 logits:
  2.25 GiB + 3.48 GiB at T=6,144 before other intermediates. Contexts must stay short and
  peaks must be measured, not assumed.
- `score_work` (`src/stencil/t2_runner.py:59`) executes generated programs with the host
  interpreter under a 5 s timeout; acceptable for the synthetic generator, not for public inputs.
- `pytest tests/` collects 2142 tests; bare `pytest`/`make gate-0` break (no `testpaths`);
  `ruff check` has 1,501 findings, so gate-0 cannot pass on testpaths alone.
- 246 review docs vs 181 experiment scripts; plan/PROTOCOL.md archived; AGENTS.md points at absent files.
- License declarations: root GPLv2, deploy/ MIT, model card apache-2.0; the classifier encoder
  is BAAI bge-small derived. An ownership/component inventory is needed before any relicensing.
- 215 unpushed commits. Untracked and NOT gitignored: models/qwen3-30b-a3b-hf (~57 GiB),
  focus-lora-4b, nested `*/seed*/encoder/*.safetensors` under admission-v2, ft-v3, relations-v3;
  results/focus-mechanism-composition-astra.md untracked but load-bearing; the source-replay
  four-file change is uncommitted.
- Untracked headline evidence: results/qwen/s1-oracle.json, s2-selector.json, s3-a0.json,
  s3-a1-oracle.json, s3-a2-selector.json, s3-final-sealed.json, s3-selector-weights.pt,
  w0-ce.pt, w0-proxy.pt; all of results/gpt2/; ft/encoder/model.safetensors (133,462,104 B).
  (b3-ce-s0.pt and w3a-audit.json are already tracked.)
- The classifier corpus reconstruction path yields 20,054 rows but per-source counts differ
  from the frozen manifest (10,576/4,080/4,543 vs 10,555/4,084/4,560); exact identity is not established.
- deploy/stencil_wave/ (last commit 2026-09-01) ships `b3-ce-s0.pt` with top-k at prefill and a
  constant +3 bias (model.py:96,123); it is not the W0 continuous field and cannot reproduce any
  synthetic result; its parity tests keep strict failures as xfails; publishing the retention
  runner is new implementation work.
- GPU: one GB10, 119 GB unified. At plan time the foreign llama-server had exited (114 GB
  available); it may return. Peer session runs Ouro-2.6B bf16 (~6-10 GB).

### Literature position (2024-2026)

- Attention steering: PASTA; **AutoPASTA (2409.10790)** selects the supporting sentence
  automatically then steers (open-book QA); **SpotLight (EACL 2026)** is dynamic
  deficit-triggered bias with multi-turn MT-IFEval evaluation; InstABoost (ICLR 2026); GUIDE;
  **Directer (2603.06745)** adds a trust-region backoff and beats tuned SpotLight/PASTA on
  rewritten IFEval; **Guiding Giants (2505.20309)** is the closest trained controller. None
  trains a per-position, per-step pre-softmax bias field through a frozen trunk from
  completion loss. That, and only that, is Stencil's plausible incremental method novelty.
- Retention/injection: SnapKV, LKV (2605.06676), Memory Inception (2605.06225), Knowledge
  Packs (2604.03270), V-Steer (2607.26228). Stencil's pin+echo is an empirical application;
  its useful finding is that a role/recency rule beat a trained selector at matched columns.
- Memory maintenance: Mem0, MemGPT/Letta, LangMem. Stencil's register is a small-model
  instance; contribution would be measured reliability, error rates and cost.
- Workloads: IFScale (2507.11538), ManyIFEval (2509.21051) show compliance collapses with
  instruction count; MemoryCode (ACL 2025, Apache-2.0, regex-checked conventions with updates
  across sessions; Llama-3.1-8B 71.7% -> 12.5%) is the closest public workload to Brian's goal.
- Steering reliability (2504.04635, 2505.22637, 2602.17881) and GUIDE/SpotLight/Directer all
  document degeneration at strength; matches check 28/30.

Astra repo verdict: NOVEL 3/10, IMPACT 4/10, ITERATION-SPEED 3/10. Recommendation: one
bounded comparison of the learned controller against prose and fixed steering; make
automatic maintenance of correct reminders the practical objective; close the echo-only
attribution cheaply; publish the useful negatives with a complete artifact release.

## Plan

### A. Re-scope: one method claim, one product claim, both narrow

**Method claim (the novelty candidate).** Given a correct external ledger, a frozen
264k-parameter controller (`src/stencil/wave.py`, checkpoint `results/qwen/w0-ce.pt`) that
allocates attention per token improves joint executable-and-adherent success on fresh short
governed-code episodes over (a) correct prose restatement and (b) fixed attention steering
on the same known governing spans; and the gain depends on WHERE the field points, not only
on WHEN/how much it presses. Scope: attention allocation given supplied rule state. No claim
about discovering, maintaining, switching or clearing obligations; no claim that the field
decodes the governing rule (W3b showed it does not under the registered readout).
Closest work: AutoPASTA, SpotLight, Directer, Guiding Giants.

**Product claim (Brian's corrected goal).** On a MemoryCode-derived evaluation with
instruction updates and cancellations, automatically maintaining the live obligation set
and rendering it as prose at request time matches or beats bounded restate-all on
convention compliance, with false-admission and stale-execution rates reported.
Contribution: small-model reliability numbers, not a new memory architecture.
Closest work: Mem0/Letta (mechanism), MemoryCode (workload).

Reuse: `wave.py`, `w_seal.py`, `t2_sessions.py`, `t2_runner.py`, `wave_ref.py`,
`multiif_evict.py` (`run_arm`, `_score_fields`, cluster stats), `ledger.py`, `qwen3.py`
(`bias_hook`, `return_hidden`, `prefill_with_eviction`), `focus3.py` lifecycle policy +
frozen `data/classifier/model/ft` and relation-v2 classifiers (CPU), `deploy/stencil_wave/`.
Parked (not "closed"): S3 dictionary task, GPT-2 focus cache, 30B FOCUS-3 GPU line,
source-replay banks, residual-stream / function-vector / MoE-router steering, cache-column
gated wave, `qwen_cache.py`. "Miller wave" is motivation, never evidence.

### B. Experiments (first pass ~4-5 GPU-h after the pilot; all Qwen3-1.7B; every estimate is replaced by Exp 0 measurements before launch)

**Exp 0 (CPU + <= 15 GPU-min): fix the instruments, measure the budget.**
1. Comment checker: in `t2_runner.py:91-94` extract the function's source span by line range
   including trailing comment lines up to the next top-level statement; add
   `tests/test_t2_runner_comment.py` with compliant and noncompliant fixtures run through
   `score_work`; add a comment branch to `_oracle_moment` (`t2_runner.py:264`). Re-score the
   saved W0 seal outputs (`results/qwen/w-seal.json` records) with the fixed checker and record
   the corrected comment rows as a qualification note; historical verdicts are not rewritten.
2. Evaluator: reuse the layer-20 feature pass via `bias_hook` instead of two prefix
   recomputations per token in `w_seal.py:57` / `w0_train.py:73`; move model load in
   `w0_train.py:46` under `main()`. Qualify on 8 fixed dev sessions: log max-abs logit drift
   and adherence agreement vs the old runner; no bitwise claim.
3. Seeds: reserve block 14,700,000+ (grep-verified unused today) for all new evaluation
   episodes; smoke fixtures use 14,690,000+.
4. Timing and memory pilot at MAXIMUM context length for each arm family (4 items each),
   recording tok/s, seconds/item and peak memory (`torch.cuda.max_memory_allocated`). Each
   experiment below launches only after its pilot writes a budget into its registration.

**Exp 1: pin increment given echo, on 128 distinct source prompts (~1-1.5 GPU-h).**
- Question: once the selected text is echoed, do the selected KV pins add anything? And does
  the arm we would ship (role-rule echo, standalone budget) hold up?
- Sources: from the exposed 909 records (425 pairs + 59 singletons), pick 128 source prompts
  deterministically (seed 0, no outcome use), one conversation per source.
- New arms, same saved histories and eviction coordinates, same 512-token limit:
  `clf_echo_only` = evicted + classifier-selected echo, zero pins (`run_arm(..., keep=[])`);
  `role_echo_only` = evicted + newest-first prior-user SENTENCES rendered by
  `render_text_ledger`, standalone budget E=256 tokens including header (not borrowed from
  the classifier). Existing full / evicted / clf_pinned / clf_pinned_echo / role_pinned outputs
  reused only after a compatibility check: replay 8 of the 128 `clf_pinned_echo` records on
  the current runtime; require identical generated text on all 8, else regenerate the
  compared arms on the 128 subset (adds ~1 GPU-h) rather than mixing runtimes.
- Scoring reuses `_score_fields` with instruction IDs/kwargs looked up from
  `data/bench/multiif_en.jsonl` by `ci`, exactly as the original run did.
- Script `scripts/multiif_echo_only.py` (~200 lines) importing `run_arm`, `_score_fields`,
  `_cluster_values`, `_contrast`, `_one_sided_cluster_p`, `invalid_output`,
  `repeated_4gram_fraction`; writes `results/qwen/multiif-echo-only-128/` (schema 2, atomic
  per-conversation, `--start/--limit`, records saved as each arm completes).
- Estimands (registered before launch): source-level paired aged-adherence difference,
  D1 = clf_pinned_echo − clf_echo_only; D2 = role_pinned − role_echo_only; D3 =
  role_echo_only − clf_echo_only. Paired mean with 95% bootstrap interval over sources plus
  exact sign test on discordant sources. Noninferiority margin 2 points. Safety: invalid /
  degenerate / truncated counts as excess over `full`, reported, no integer kill.
- Readings: D1 interval entirely above +2 → pins earn their place; retention package keeps
  pins. D1 interval entirely below +2 → pins are dispensable at this margin; ship echo-only.
  Interval straddles 2 → insufficient evidence; ship echo-only on cost grounds and say so.
  D2/D3 decide which selector the reminder package defaults to. Labelled a post-hoc ablation
  on an exposed cohort.

**Exp 2a: wave utilization screen, existing checkpoint (~1 GPU-h).**
- 64 fresh episodes from `t2_sessions.generate_t2` (`split="final"`, seeds 14,700,000-063),
  two governed code requests each, contexts <= 512 tokens, 32-token completions (raised to
  64 only if the competence pilot shows the microprograms do not fit; budget recomputed).
- Six arms, all given the identical correct live ledger:
  `base`; `prose` (oracle current-rule restatement); `spotlight` (fixed β=2 peak-normalised
  bias on the known governing spans every step = SpotLight/PASTA-style, no learning);
  `wave` (w0-ce.pt continuous field); `wave_where_shuffled` (the wave's own per-step gain
  trajectory kept, its spatial field permuted among the ledger sentence spans: removes WHERE,
  keeps WHEN and dose); `wave_static` (field computed at step 0 and frozen, gain kept:
  removes query/step dependence). These are the matched controls Astra asked for; the
  existing W0 K-perm/gain-perm/uniform ablations map onto them.
- Score per episode: joint functional-and-adherent success (all opportunities adherent AND
  reference tests pass on 3 inputs via `wave_ref.py`), with the fixed comment checker;
  execution through the existing `score_work` path (synthetic inputs only).
- Primary estimand: per-episode binary joint success; contrasts wave vs prose, wave vs
  spotlight, wave vs wave_where_shuffled; exact McNemar, Holm over 3. Secondary: mean
  adherence with paired bootstrap interval; parse rate; paired-broken works as excess over base
  (prospective rule: <= 5% of works; note the original seal's 21/408 = 5.15% would fail it).
- Exhaustive readings: PASS = all three contrasts positive at Holm-adjusted p <= .05 →
  Exp 2b. FAIL-EMPHASIS = wave vs where_shuffled not positive (two-sided interval includes 0
  or favours shuffled) → gain is timing/dose, not selection; method claim dropped. FAIL-BASELINE
  = wave not above prose or spotlight → controller is an automatic SpotLight with no shown
  advantage; method claim dropped. Any other pattern = INSUFFICIENT EVIDENCE, published as
  descriptive with intervals; no further wave spend. Two-sided p and intervals are always reported so demonstrated harm is visible.
- Competence-harm disclosure travels with every mention of w0-ce: MMLU 48.05 -> 45.83
  (175 degradations / 57 improvements), GSM8K noninferiority failed.

**Exp 2b (only on PASS): replication (~1 GPU-h).** Retrain w0-ce with seeds 1 and 2 (`SEED`
env controlling `torch.manual_seed` at `w0_train.py:109/172/189` AND the shuffle generator at
:196; compare tensors, not file hashes, against `w0-ce.pt`); same 64 episodes and arms.
PASS requires each seed to reproduce all three contrasts. No LoRA arm in this pass: a fair
LoRA protocol (matched budget, seeds, dev-selection allowance, objective) is its own
registration; until then the card states "no fine-tuning baseline" and makes no
superiority claim over adapters (check49 already shows removable adapters can carry SET).

**Exp 3: MemoryCode-derived automatic-maintenance screen (CPU contract first; ~1 GPU-h).**
- 3a (CPU, 1-2 days, no GPU): vendor github.com/Cohere-Labs-Community/MemoryCode into
  `vendor/memorycode`, pin sha in `data/bench/pins-manifest.json`. Write
  `results/memorycode-derived/CONTRACT.md` before any GPU spend, fixing: native prompt
  format vs the derived chat rendering (mentor→user, mentee→assistant; prior mentee answers
  supplied from the dataset, not generated); session/query boundaries; eviction = drop all
  sessions before the current one from the prompt (text truncation, explicitly NOT the
  Multi-IF positional-eviction runner, and named as such); candidate-sentence extraction from
  raw history independent of labels; label isolation (only `oracle` reads applicability /
  update labels); common budget accounting E=256 tokens including header and bullets with
  fixed packing/ordering/overflow rules; split by dialogue template family (not item id);
  checker qualification: for every retained regex family, compliant and violating fixtures
  incl. stale values, conflicting instructions, required text inside strings/comments,
  malformed code; convention compliance is the outcome, functional correctness is neither
  measured nor claimed (no code execution). `tests/test_memorycode.py` covers all of it.
- 3b competence qualification (16 setup items, ~15 GPU-min): `history` arm all-applicable
  compliance >= 6/16 on 1.7B; retention headroom (`oracle` − `history`) reported separately,
  not gated. If 1.7B fails, one retry on Qwen3-4B with the same four arms (no controller arm
  exists in Exp 3, so the 2048-vs-2560 hidden-size mismatch does not arise); else INELIGIBLE,
  64 never opened.
- 3c screen (64 items, ~1 GPU-h): arms `history`, `restate_all` (every instruction seen,
  newest-first, packed to E), `auto` (frozen admission + relation-v2 lifecycle policy from
  `src/stencil/focus3.py` run on CPU over the dialogue; live set rendered identically),
  `oracle` (label-derived live set, same renderer and budget). Primary: `auto` vs
  `restate_all`, exact McNemar with two-sided p and interval. Descriptive: `auto` vs `oracle`,
  false admissions, missed updates, stale-rule executions, tokens.
- Power, stated: N=64 detects only large effects (8 wins/0 losses one-sided p=.0039; 4/0
  p=.0625). This is a SCREEN: a positive triggers a registered N=256 follow-up with power
  computed by the repo's finite-enumeration method; a null is "not demonstrated at N=64".
- Readings: auto >= restate_all with interval above −2 and false-admission rate reported →
  product claim has a public-workload leg; ship `auto` with the numbers. Otherwise ship
  restate_all / role rule and publish the admission error table.

Not in this pass and why: cache-column gated wave reopen (validity, not novelty; needs a
budget-constrained actuator); BM25 / wave-as-retriever arms (different capability; would
need their own policy definitions); LoRA (own registration); any 30B run.

### C. Publication, in two releases

- **Release 1, evidence (CPU, after the hygiene step):** HF dataset repos
  `stencil-synthetic-sessions` (generators `t2_sessions.py`, `qwen_task.py`, seed manifests,
  sha256 of rendered texts) and `stencil-instruction-salience` (published as a labelled
  RECONSTRUCTION with per-row provenance and the manifest-count discrepancy stated; LLM
  authorship per file; contamination incidents; BFCL lineage from `LEDGER-PLAN.md:634`).
  A model repo `stencil-research-artifacts` holding w0-ce.pt, w0-proxy.pt, s3-selector-weights.pt,
  the classifier head + encoder (Hub-hosted), with a card whose evidence tables cite
  RESULTS.md files, carry the negative-results table, the C2 result, the Multi-IF safety-gate
  failure as recorded, the w0-ce MMLU/GSM8K harm, and an explicit "research backend numbers;
  no runtime package is qualified" statement.
- **Release 2, runtime (only after Exp 1-3 and a separate implementation budget):** the
  retention/reminder runner in `deploy/stencil_wave/` (new implementation: positional
  eviction semantics, classifier/role selectors, optional continuous controller),
  requalified end-to-end on the current transformers major version with pre-query eviction
  parity tests, and an executable example from a clean environment. No research number is
  attributed to the package until that qualification exists.
- License: first an inventory (`LICENSE-INVENTORY.md`: repo code, vendored bfcl/ifbench,
  BAAI-derived encoder, Qwen trunk, MemoryCode, contributed data) with owner and terms per
  component; then Brian decides. Apache-2.0 for Brian-owned code is the recommendation.
- Repo hygiene (explicit pathspecs only, per AGENTS.md:33): first settle the uncommitted
  source-replay four-file change (park on a branch or commit after its pending review);
  `git add -f` the untracked evidence list above and the GPT-2 JSON/txt plus
  `cache-v8-s0-ckpt.pt` and `base-v4-s0-ckpt.pt` (15.8 MB); `git add
  results/focus-mechanism-composition-astra.md scripts/focus_check32.py`; gitignore
  `models/qwen3-30b-a3b-hf/`, `data/classifier/model/focus-lora-4b/`,
  `data/classifier/model/**/encoder/*.safetensors`, `data/classifier/model/**/head.safetensors`,
  `relations-seed*/`, `relations/dev_predictions.npz`; `pyproject.toml` gains
  `testpaths = ["tests"]`; lint is scoped to changed files (`ruff check` on the diff), the
  1,501 legacy findings are budgeted separately, and `make gate-0` is rewritten to that scope.
- README rewrite: delete the W3 bullet (lines 144-148) and keep a one-line pointer to the W3a
  qualified positive and the W3b readout failure; collapse FOCUS-3 v4-v8 to one line; replace
  "every amplification variant ... closed with data" with per-recipe wording; correct the
  deficit-gated result's dataset; new order = retention headline with C2 and Exp 1 → "correct
  request-time restatement is the baseline to beat" → wave as a utilization result with its
  competence-harm line → negatives table → boundaries → repo map with one reproduce command per result.

### D. Process rules (replace the archived protocol for this program; 8 rules)

1. One registration per result, short but SUFFICIENT to implement without new scientific
   choices: data lineage, complete arm definitions, frozen selection/packing rules,
   missingness and timeout handling, intervention budget, artifact schema, stopping rule,
   unit, exact test, N, measured cost, exhaustive readings. One implementation review, one
   result audit. A changed intervention or scorer gets a focused review; nothing else does.
2. Instrument bugs (checker, harness, tooling) are fixed and re-run with a one-line
   disclosure and do not consume any development budget. Policy failures (false admissions,
   refits, threshold changes, model selection) count against a registered development budget
   of at most two revisions per program; the third is a stop.
3. Every result reports the failed-criterion / demonstrated-harm / insufficient-evidence /
   equivalence distinction explicitly, with two-sided p and an interval. "Missed by one item"
   is reported as insufficient evidence only when the interval covers the gate; a
   demonstrated adverse effect is never relabelled inconclusive.
4. Kill and safety rules are excess-over-baseline at matched n, never absolute integer
   clauses; operational eligibility, missingness, efficacy and harm are separate columns.
5. Construction defects are repaired BEFORE the evaluation freeze, with disclosure and
   preserved construct/coverage (the accepted source-replay-preparation-v2 bounded-correction
   rule is the template); sealed outcomes after the freeze are untouchable. An ancillary
   arm's failure never vetoes reporting a complete prespecified primary pair.
6. GPU launches require the Exp 0 pilot's measured budget in the registration; budget
   exhaustion is recorded INCOMPLETE, never rescued.
7. One `results/<name>/RESULTS.md` per result; reviews under `results/reviews/`; no new
   root-level review markdown; per-item records saved as they complete.
8. A claim enters README only from a RESULTS.md with a p-value and interval, or an explicit
   "descriptive" label, stating n, p and the arm it lost to. A reviewer score is never evidence of efficacy.

### E. GPU coordination (agreed with the looped-transformer session, 2026-09-11)

- Atomic reservation: a shared lock file `/home/bmarti44/.gb10-gpu.lock` taken with
  `flock -n` by a tiny wrapper (`tools/gpu_reserve.sh <name> <est-minutes> -- <cmd>`) that
  writes owner/pid/ETA into the lock file, registers the pid in `.stencil-owned-pids`, and
  releases on exit. Both sessions use it (proposed to the peer; until they adopt it, the
  first-come rule below applies). `assert_gpu_free_or_owned` gains a "cooperating foreign
  resident" allowance keyed on the lock file's owner field.
- Before any launch: `free -g`, `nvidia-smi --query-compute-apps=...`, and the pilot's
  measured peak for that arm family + 8 GB headroom must fit in available memory.
- First-come while a foreign server is resident; message "looped-transformer" before any run
  > 30 min and when it finishes; chunk runs <= 50 min; peer can pause within a minute.
- Never signal a foreign process; no `nvidia-smi --gpu-reset`; one Stencil GPU process at a
  time; no 30B runs; contexts <= 4,096 tokens.
- Enforceable stopping: per work-arm records saved as they complete; a run stops STARTING new
  items when its reservation has 5 minutes left; `--deadline` is a per-item generation cap,
  not the reservation.

### F. Verification

- Exp 0: `uv run pytest -q tests/test_t2_runner_comment.py tests/test_wave.py
  tests/test_wave_ref.py tests/test_wave_runner_qualification.py`; `python -c "import
  scripts.w0_train"` loads no model; `results/timing-pilot/summary.json` lists tok/s,
  seconds/item and peak memory per arm family at max length; re-scored comment rows written
  to `results/qwen/w-seal-comment-requalification.json`.
- Exp 1: `uv run pytest -q tests/test_multiif_evict.py tests/test_multiif_echo_only.py`
  (keep=[] arm, role budget accounting incl. header, schema 2, source selection determinism);
  compatibility replay 8/8 identical or documented regeneration; `--summarize` prints D1/D2/D3
  with bootstrap intervals, sign tests, discordant counts, safety excess, n=128 sources;
  manifest with sha256 of every record.
- Exp 2a/2b: `scripts/w_screen.py --arms base --limit 2` smoke; `results/wave-screen/RESULTS.md`
  with per-arm joint success, McNemar/Holm and two-sided p, intervals, per-type table with the
  fixed comment checker, breakage as excess, the verdict string from the exhaustive readings;
  seed-block exclusion test asserts no 13.6M or dev seeds in the episode manifest.
- Exp 3: `uv run pytest -q tests/test_memorycode.py` (rendering, label isolation, packing and
  overflow, checker fixtures per family, `auto` determinism); `CONTRACT.md` reviewed before the
  GPU registration; `results/memorycode-derived/setup/summary.json` with the eligibility line;
  `results/memorycode-derived/64/RESULTS.md` with McNemar table, intervals, admission error table.
- Publication: dataset/model cards have every number grep-checked against RESULTS.md; the
  `LICENSE-INVENTORY.md` exists before any push; `push_to_hub.py` dry-run lists every file;
  `--push` only with Brian's go.
- Hygiene: `git status --short | grep '^??'` empty under models/ and data/classifier/model/;
  `git ls-files` shows every force-added file; `git diff --check`; `ruff check` on changed
  files clean; README contains no "4×10⁻¹²" or "73/73"; `pytest` (bare) collects only tests/.

### Execution order

1. Settle the uncommitted source-replay change; hygiene; README rewrite (CPU, ~1 day).
2. Exp 0 instrument fixes + pilot (CPU + <= 15 GPU-min).
3. Exp 1 (register with measured budget → run → RESULTS.md → audit).
4. Exp 2a (register → run → RESULTS.md → audit); Exp 2b only on PASS.
5. Exp 3a contract (CPU) → 3b qualification → 3c screen → RESULTS.md → audit.
6. Release 1 (evidence) after step 1; Release 2 (runtime) only after 3 and a separate budget.

### Astra round-1 findings declined, with reasons

- Full LoRA protocol in this pass (finding 6): a fair adapter comparison is its own
  registration; adding it now doubles author-hours without changing the first decision.
- Universal Bonferroni/estimand debates beyond the stated primary (7): the primary is now a
  single binary per-episode estimand with exhaustive readings; secondary metrics are descriptive.
- Requalifying the HF runtime package before any experiment (21-22): moved to Release 2,
  after the science; Release 1 publishes evidence only.
- Native-protocol MemoryCode comparability (14): not claimed; the evaluation is labelled
  "MemoryCode-derived" and its contract is written before GPU spend.
- Repo-wide Ruff cleanup (32): lint is scoped to changed files; the 1,501 legacy findings are
  a separate budgeted chore, not a gate for science.

## Open decisions for Brian

- License: produce the inventory, then Apache-2.0 for Brian-owned code (recommended) vs keep GPLv2?
- HF org/namespace, and whether the 133 MB classifier encoder (BAAI-derived) may be published.
- Disposition of the uncommitted source-replay-preparation-v2 four-file change: park on a
  branch, or complete its pending Astra implementation review first?
- Propose the shared GPU lock wrapper to the looped-transformer session (yes/no).

=== YOUR ROUND-1 REVIEW OF REV 1 (for reference) ===
**Execute as written: 24/100 — reject.** Exp 1 is salvageable. Exp 2 cannot establish its advertised mechanism. Exp 3 is an underspecified benchmark adaptation. The process changes would recreate several failures the audits identified.

1. **CRITICAL — A/B2: the uniform control does not isolate selection from emphasis.** The wave learns both a varying gain and a spatial field over **every prompt token**. The proposed uniform arm applies fixed β=2 only to active ledger sentences. Consequently, the contrast changes timing, strength, spatial support, and concentration simultaneously. A wave win could reflect avoiding excessive emphasis, emphasizing task text, or using familiar historical wording—not choosing the governing obligation. Peak normalization does not match total bias or resulting attention mass. See [wave.py:20](/home/bmarti44/stencil-llm/src/stencil/wave.py:20), [w0_train.py:75](/home/bmarti44/stencil-llm/scripts/w0_train.py:75), and [w_seal.py:58](/home/bmarti44/stencil-llm/scripts/w_seal.py:58).

   Retain a practical uniform baseline, but add controls that preserve the checkpoint’s timing/gain while perturbing spatial selection, and controls that preserve spatial selection while removing query or step dependence. Match candidate support and register dose selection on development data. Measure where the field acts.

2. **HIGH — A/B2: the claim outruns the task and existing evidence.** The harness supplies an already resolved live ledger at every work turn. The controller does not discover updates or clears; `prompt_at` serializes their correct result for it. The task has three ordinary obligation types plus the held-out comment type, not the SELECTOR task’s 32 obligations. Furthermore, the prior readout experiment explicitly found that the field was **not decodable as “the governing rule now”** under its registered rule. An adherence gain does not overturn that finding. See [t2_sessions.py:295](/home/bmarti44/stencil-llm/src/stencil/t2_sessions.py:295) and [WORKLOG.md:1331](/home/bmarti44/stencil-llm/WORKLOG.md:1331).

   Narrow the claim to conditional attention allocation given a correct external ledger, or add direct tests of current versus stale authority, cleared obligations, and dependence on the current query.

3. **HIGH — A: the literature positioning contradicts the repository’s own research.** SpotLight is not accurately described here as a static, single-turn, uniform-bias equivalent. The local literature audit identifies dynamic deficit-triggered bias and multi-turn evaluation. The earlier search also identifies AutoPASTA’s automatic span selection. Those do not eliminate a narrower learned-controller contribution, but they invalidate the proposed novelty shortcut. See [astra-research-blockers.md:214](/home/bmarti44/stencil-llm/results/astra-research-blockers.md:214), [astra-research-blockers.md:222](/home/bmarti44/stencil-llm/results/astra-research-blockers.md:222), and [research-wave-prior-art.md:11](/home/bmarti44/stencil-llm/results/research-wave-prior-art.md:11).

4. **HIGH — B2: the proposed “fresh sealed” seed block was explicitly retired after exposure.** `13,600,000+i` appears in W3’s registration history. The subsequent amendment says that block was instantiated during review and replaces it; another amendment explicitly supersedes it. Switching to `split="final"` does not establish independence from the exposed construction. See [w3-prereg-draft.md:65](/home/bmarti44/stencil-llm/results/w3-prereg-draft.md:65) and [w3-prereg-draft.md:88](/home/bmarti44/stencil-llm/results/w3-prereg-draft.md:88).

   Reserve a genuinely unused block. Keep smoke fixtures outside it.

5. **HIGH — B2/F: the comment null is contaminated by a checker bug.** `score_work` takes `ast.get_source_segment(code, fn)` and requires its final nonempty line to equal `# reviewed`. Python’s function AST ends at the last statement and excludes a trailing comment. I reproduced this with a standard-library-only fixture:

   ```python
   def f(a, b):
       return a + b
       # reviewed
   ```

   The extracted segment ends at `return a + b`; the check returns false. The canonical builder itself generates precisely this trailing-comment form. Existing reference tests use `split="dev"`, so they miss the held-out comment case. Moreover, `_oracle_moment` has no comment branch. See [t2_runner.py:91](/home/bmarti44/stencil-llm/src/stencil/t2_runner.py:91), [wave_ref.py:29](/home/bmarti44/stencil-llm/src/stencil/wave_ref.py:29), [test_wave_ref.py:18](/home/bmarti44/stencil-llm/tests/test_wave_ref.py:18), and [t2_runner.py:264](/home/bmarti44/stencil-llm/src/stencil/t2_runner.py:264).

   “The model never produces the comment and even the hand press cannot induce it” is therefore unsupported by these scores. Fix the checker prospectively, qualify the historical aggregate, and verify compliant and noncompliant comment fixtures through the actual consumer.

6. **HIGH — B2: LoRA is neither adequately matched nor adequately specified.** The dimension arithmetic is correct: eight layers × rank four × `(4096+3072)` gives **229,376 parameters**. That is **13.22% fewer** than 264,321. More consequentially, the plan leaves scaling, adapter initialization, regularization, training scope, checkpoint selection, and development tuning unspecified. “Same recipe” is ambiguous because the wave objective includes a gain-specific L1 penalty that LoRA cannot share literally. One LoRA seed versus three wave seeds also gives an asymmetric comparison, especially when H4 compares LoRA against the best observed wave.

   LoRA also freezes the original weights, is removable, and adds no prompt tokens. Those are not residual advantages unique to the wave. See [qwen3.py:247](/home/bmarti44/stencil-llm/src/stencil/qwen3.py:247), [w0_train.py:103](/home/bmarti44/stencil-llm/scripts/w0_train.py:103), and the existing removable-adapter result in [check49/README.md:5](/home/bmarti44/stencil-llm/results/quick-checks/check49/README.md:5).

   Register an approximately equal parameter budget, comparable seed coverage, and equal development-selection allowance. If LoRA is dropped, drop the associated superiority/falsification claim too.

7. **HIGH — B2: the inference and verdicts do not match the claim.** A sign test on session adherence differences tests the balance of positive and negative differences, not mean adherence gain. Sessions with small wins can outnumber sessions with large losses. Specify whether the target is session-level win probability, mean session adherence, or pooled opportunity adherence. The secondary work-level McNemar p-value remains uncalibrated for clustered works merely because a “clustering caveat” accompanies it. See the distinction between cluster means and pooled cells in [stats.py:132](/home/bmarti44/stencil-llm/src/stencil/stats.py:132) and the exact binary test in [stats.py:122](/home/bmarti44/stencil-llm/src/stencil/stats.py:122).

   The readings also overlap or omit cases: two significance failures can coexist with disagreement in sign; exactly one nonsignificant positive seed has no clear outcome. Failure to beat uniform does not establish equivalence or make the wave “an automatic SpotLight.” A LoRA point estimate above all waves does not establish matching performance. Register exhaustive outcomes and effect intervals. Requiring all three wave tests to pass is a conjunction; its main problem is not a missing blanket Bonferroni correction.

8. **HIGH — B2/C: the plan omits directly relevant competence harm from the very checkpoint it proposes to revive.** The repository records `w0-ce` reducing MMLU from 48.05% to 45.83%, with 175 degradations versus 57 improvements, and failing the registered noninferiority gate. GSM8K also failed its noninferiority gate. These belong prominently in the research add-on’s card and interpretation, not behind a generic list of other failed wave recipes. See [WORKLOG.md:1586](/home/bmarti44/stencil-llm/WORKLOG.md:1586) and [WORKLOG.md:1613](/home/bmarti44/stencil-llm/WORKLOG.md:1613).

   The new safety rule also rejects the motivating seal: **21/408 = 5.15% paired-broken works**, above 5%. That may be a reasonable prospective standard, but it is a deliberate change requiring explanation—not an automatic correction of an old malformed rule.

9. **MEDIUM — B2/F: the reproduction instructions have avoidable traps.** The cited `manual_seed(0)` lines exist, but the shuffle generator is separately seeded at [w0_train.py:196](/home/bmarti44/stencil-llm/scripts/w0_train.py:196). Specify which random streams vary. Model loading and CUDA initialization occur at module top level, so importing this trainer for LoRA helpers is unsafe; see [w0_train.py:46](/home/bmarti44/stencil-llm/scripts/w0_train.py:46).

   Also, the checkpoint ZIP contains paths beginning `w0-ce/`. Saving identical tensors as `w0-ce-s0.pt` can change the serialized file hash through the archive name. Compare canonical tensor content, or reproduce the original serialization name in an isolated output directory. “Logs mismatch” is insufficient provenance for subsequent pooled analysis.

10. **HIGH — B1: 909 conversations are not 909 independent source prompts.** I reconstructed the saved first-user token sequences: there are **484 distinct first prompts**, comprising **425 pairs and 59 singletons**. The key prefixes give the same grouping. For example, `conv-000` and `conv-001` have keys `1000:1:en` and `1000:8:en` and identical first prompts. See [conv-000.json:4](/home/bmarti44/stencil-llm/results/qwen/multiif-evict-909-prequery-v2/conv-000.json:4) and [conv-001.json:4](/home/bmarti44/stencil-llm/results/qwen/multiif-evict-909-prequery-v2/conv-001.json:4).

   `_cluster_values` clusters only within each conversation, leaving shared-source dependence unaddressed. Use source-prompt clustering, or justify the narrower estimand and report this sensitivity. This does not erase the large historical recovery: my source-grouped sensitivity still gives extremely small C1/C3 p-values. It matters particularly for the proposed small incremental C4 effect. See [multiif_evict.py:488](/home/bmarti44/stencil-llm/scripts/multiif_evict.py:488).

11. **HIGH — B1: the readings cannot justify the shipping decision.** A nonpositive estimate, or a confidence interval crossing zero with a small estimate, does not establish that pins are dispensable. Register a practical margin and an equivalence/noninferiority decision if that is the product question. Conversely, a statistically positive but negligible pin increment does not automatically justify maintaining KV surgery.

   More seriously, the mandatory experiment tests **classifier-selected echo**, while the fallback package ships **role-selected echo**, which is optional. The existing role comparator selects recent user **token columns**, possibly partial sentences, and borrows its budget from the classifier. It is not an independently specified reminder policy. See [multiif_evict.py:271](/home/bmarti44/stencil-llm/scripts/multiif_evict.py:271) and [multiif_evict.py:823](/home/bmarti44/stencil-llm/scripts/multiif_evict.py:823). Make the proposed shipping arm mandatory and define its standalone budget.

12. **HIGH — B1/F: saved records are sufficient for replaying inputs, not for an uncontrolled historical/new-runtime comparison.** The saved echo IDs and eviction coordinates exist. However, `_score_fields` requires original benchmark instruction IDs and kwargs; those scoring specifications are not contained in the listed saved fields. The old metadata also does not pin every relevant runtime component, including the Qwen implementation. A new arm compared against historical outputs needs a verified compatible model, tokenizer, code, numerical environment, and scorer. See [multiif_evict.py:715](/home/bmarti44/stencil-llm/scripts/multiif_evict.py:715), [multiif_evict.py:742](/home/bmarti44/stencil-llm/scripts/multiif_evict.py:742), and [meta.json:27](/home/bmarti44/stencil-llm/results/qwen/multiif-evict-909-prequery-v2/meta.json:27).

   Add baseline replay checks on separate verification records before sealing the new arm. Preserve the current historical safety verdict; a new tolerance is a prospective rule or retrospective sensitivity, not a repaired original PASS.

13. **MEDIUM — B1/A: two causal statements are wrong.** `clf_pinned_echo − clf_pinned` already isolates adding echo **conditional on fixed pins**; those arms do not differ in pins. The missing arm identifies the pin increment conditional on echo and completes the factorial comparison. See [multiif_evict.py:842](/home/bmarti44/stencil-llm/scripts/multiif_evict.py:842).

   Neither outcome identifies whether a separately designed deficit-gated bias would help retained columns. Making that research conditional on C4 can be a spending preference, but it is not scientific falsification of the wave mechanism.

14. **HIGH — B3: MemoryCode’s proposed port does not yet define a reproducible experiment.** `vendor/memorycode` is absent. There is no locally inspectable adapter, pinned upstream evaluator, or mapping from its native examples to the proposed “item.” Given-text sessions can support a replay-based retention test, but converting them into user/assistant turns is a substantive prompt transformation. Specify native prompts, session/query boundaries, whether prior answers are supplied or generated, where eviction occurs, positional treatment, and the unit that contains shared history.

   The existing Multi-IF helper actually prefills history, evicts it, then prefills the current turn while preserving absolute positions. Ordinary text truncation is a different intervention. See [qwen3.py:88](/home/bmarti44/stencil-llm/src/stencil/qwen3.py:88). Call the result a **MemoryCode-derived evaluation** unless native protocol comparability is established. The earlier local audit already distinguishes its convention checks from functional coding success: [astra-research-blockers.md:43](/home/bmarti44/stencil-llm/results/astra-research-blockers.md:43).

15. **HIGH — B3: the oracle is not automatically a ceiling, and label isolation is unspecified.** A label-derived set of applicable instructions may exceed 256 tokens, may require several mutually dependent instructions, and may not map verbatim to a candidate sentence. Ordering or truncation can change performance. An oracle echo can even underperform another echo, so its observed score is not an upper bound on attainable performance.

   Freeze candidate extraction from raw history independently of gold applicability. Only the oracle arm may access applicability/update labels. Use a common budget accounting rule, including headers and source labels, and specify packing, ties, duplicates, and overflow. Otherwise the apparent selector gap can arise from privileged extraction or rendering rather than ranking. The existing renderer adds its own header and bullets without a budget limit: [ledger.py:337](/home/bmarti44/stencil-llm/src/stencil/ledger.py:337).

16. **HIGH — B3: the proposed selectors do not test the same capability.** The frozen classifier returns `P(rule)+P(fact)` and the registered Multi-IF invocation provides **empty context**. It detects salience; it does not rank applicability to the final query. The wave was trained on generation-step states and individual prompt-token keys. Turning it into a once-per-query sentence retriever requires a specified pooling and ranking rule and changes its input distribution. See [selector_v2.py:98](/home/bmarti44/stencil-llm/src/stencil/selector_v2.py:98), [multiif_evict.py:211](/home/bmarti44/stencil-llm/scripts/multiif_evict.py:211), and [wave.py:29](/home/bmarti44/stencil-llm/src/stencil/wave.py:29).

   A failed zero-shot projection transfer would not be evidence against a properly trained query-conditioned selector. Define the BM25 tokenizer, sentence boundaries, length normalization, packing, and ordering too. These are experimental policy choices, not incidental plumbing.

17. **HIGH — B3: the 4B fallback cannot run the stated wave-selector arm.** Qwen3-4B has hidden size **2560**. The W0 controller’s projections accept **2048**. This is a dimension error, not merely an uncertain transfer result. See [4B config.json:11](/home/bmarti44/stencil-llm/models/qwen3-4b-hf/config.json:11) and [wave.py:20](/home/bmarti44/stencil-llm/src/stencil/wave.py:20).

   Pre-register a reduced 4B arm set or a separately justified controller. Do not invent a projection after the 1.7B gate fails.

18. **HIGH — B3: the competence pre-gate confuses ability with retention headroom.** `full ≥4/16` is a weak observed floor; adding `full−evicted ≥3/16` requires a favorable retention contrast in a tiny sample. A competent model can fail the second condition because these particular items do not need memory. Conversely, four easy successes do not establish competence on the evaluation distribution.

   Qualify current-task coding and convention compliance with native/full and legal oracle inputs; report retention headroom separately. Split setup/evaluation by independent history or task family, not merely item ID. The local audit explicitly says no relevant 1.7B/4B MemoryCode competence floor was established: [astra-research-blockers.md:43](/home/bmarti44/stencil-llm/results/astra-research-blockers.md:43).

19. **HIGH — B3: N=64 and the headroom readings cannot support the promised decisions.** Eight net oracle wins can mean 8/0 discordance, with one-sided p=.003906, or 36/28, with p=.190866. The same headroom threshold therefore admits very different evidence. Closing half of eight net wins means four net wins; even **4 wins/0 losses gives p=.0625**, failing the unadjusted test, let alone Holm’s first .0167 threshold.

   “Oracle ≈ role → selection has no value” requires a margin and an interval, not a small observed difference. “BM25 closes 50% → retrieval suffices” likewise needs uncertainty. Register expected discordance and attainable power before calling this decisive. The repo already contains the appropriate finite-enumeration approach and shows only 46.15% power at a 10-point effect for one unadjusted N=64 test under one plausible discordance model: [focus-mechanism-composition-v2-astra.md:117](/home/bmarti44/stencil-llm/results/focus-mechanism-composition-v2-astra.md:117).

20. **HIGH — B3/F: three regex-parity fixtures cannot qualify a coding benchmark adapter.** Matching three vendor outputs can reproduce the same false-positive behavior. Cover every retained checker family with compliant examples and discriminating violations, including stale values, conflicting instructions, strings/comments containing required text, and malformed code. Report convention compliance separately from functional correctness. Either measure functionality or explicitly exclude coding competence/usefulness claims. See the existing warning in [astra-research-blockers.md:43](/home/bmarti44/stencil-llm/results/astra-research-blockers.md:43).

21. **HIGH — C/F: this is a substantial new HF implementation, not a checkpoint/config refresh.** The current package selects top-k entries **once at prefill**, ignores the gain head, and applies sustained fixed-dose bias. It does not implement the proposed retention runner or W0’s continuous per-step field. Repointing its checkpoint cannot reproduce Exp 2. Its uploader stages four files and does not publish the proposed encoder/head runtime. See [model.py:96](/home/bmarti44/stencil-llm/deploy/stencil_wave/src/stencil_wave/model.py:96), [model.py:123](/home/bmarti44/stencil-llm/deploy/stencil_wave/src/stencil_wave/model.py:123), and [push_to_hub.py:33](/home/bmarti44/stencil-llm/deploy/stencil_wave/scripts/push_to_hub.py:33).

   Budget separate work for retention semantics, position/cache bookkeeping, classifier loading, public installation/loading, and the optional continuous controller. A useful release needs an executable example from a clean environment, not merely an uploaded model card.

22. **HIGH — C/F: existing parity receipts do not transfer the research result to the proposed package.** The tests explicitly retain strict parity failures as non-strict `xfail`s; some assertions are weakened to agreement where logit margins mathematically guarantee it. They test short trajectories and fixed column groups, not pre-query eviction or the new continuous wave. See [test_parity.py:14](/home/bmarti44/stencil-llm/deploy/stencil_wave/tests/test_parity.py:14).

   Moving from transformers 4.51.0 to 5.16.1 crosses a major version while the attention adapter patches an internal attention dispatch path. Requalify actual retention and controller behavior. Until then, distinguish research-backend benchmark scores from HF-package measurements. W0’s full-prefix recomputation also differs from retaining previously intervened token states in a decoding cache; that semantic choice needs explicit verification.

23. **HIGH — C: the promised historical classifier dataset is not yet reconstructible as claimed.** I executed only the standard-library preprocessing functions from the six-patch reconstruction path. It produces 20,054 rows, but the source counts differ from the frozen manifest:

   | Source | Frozen manifest | Current reconstruction |
   |---|---:|---:|
   | kimi-k3 | 10,555 | 10,576 |
   | kimi-k3-ctx | 4,084 | 4,080 |
   | kimi-k3-scope | 4,560 | 4,543 |

   Matching the total does not establish dataset identity. See [metrics.json:42](/home/bmarti44/stencil-llm/data/classifier/model/ft/metrics.json:42), [finetune_admission_v2.py:66](/home/bmarti44/stencil-llm/scripts/finetune_admission_v2.py:66), and the prior warning in [astra-program-review.md:87](/home/bmarti44/stencil-llm/results/astra-program-review.md:87).

   Recover the actual frozen corpus or publish a clearly labeled reconstruction. Preserve per-row provenance and split identity; do not imply exact training reproducibility from the count alone.

24. **HIGH — C: Brian’s consent and a NOTICE file are not a complete relicensing plan.** The repository contains GPLv2 text, MIT package metadata, and an Apache model-card declaration. Those may represent inconsistent declarations or distinct intended scopes; the plan has not established which. Brian can authorize relicensing only for rights he controls. Imported code, model components, benchmark assets, and contributed material need their own provenance and terms. Qwen’s or MemoryCode’s license does not determine the license of unrelated repository content. See [LICENSE:1](/home/bmarti44/stencil-llm/LICENSE:1), [package pyproject.toml:6](/home/bmarti44/stencil-llm/deploy/stencil_wave/pyproject.toml:6), and [MODEL_CARD.md:4](/home/bmarti44/stencil-llm/deploy/stencil_wave/MODEL_CARD.md:4).

   Resolve ownership and component scope before offering “Apache-2.0 for the whole repo” as a ready decision. Include the classifier’s BAAI-derived encoder in that inventory; its origin is explicit in [finetune_classifier.py:64](/home/bmarti44/stencil-llm/results/quick-checks/finetune_classifier.py:64).

25. **CRITICAL — D3: “p > .3 is INCONCLUSIVE, never FAIL” suppresses strong adverse evidence.** For a one-sided benefit test, a p-value near one can accompany convincing harm. The repo’s competence-bias result has benefit p=.998291 and two-sided p=.022461, with 2 wins versus 11 losses. Your rule would relabel that adverse result inconclusive. See [quick-checks/README.md:514](/home/bmarti44/stencil-llm/results/quick-checks/README.md:514).

   Delete this rule. Distinguish failed practical criteria, demonstrated harm, insufficient evidence, and established equivalence. None is determined by “missed by one item.”

26. **HIGH — D2/D5: unlimited eligibility repair recreates the amendment spiral.** Instrument bugs and substantive eligibility failures are different. FOCUS-3’s unauthorized admissions were failures of the policy being evaluated, not CPU instrumentation accidents. The diagnostic found false admissions in 21/64 episodes and observable effects from removing them. See [diag/RESULTS.md:65](/home/bmarti44/stencil-llm/results/quick-checks/focus3-gate/diag/RESULTS.md:65).

   Permit bounded technical repair without spending a scientific trial, but count refits, policy changes, and model selection against an explicit development budget. Authoring repair must occur before scientific outcomes are exposed and must preserve the construct and coverage. The already accepted source-construction design has exactly such a bounded correction mechanism; retain its principles rather than replacing them with unrestricted repair: [PREPARATION.md:9](/home/bmarti44/stencil-llm/results/source-replay-preparation-v2/PREPARATION.md:9).

27. **HIGH — D6/F: the process diet removes essential scientific contracts.** Unit/test/N/cost/readings are insufficient without data lineage, complete arm definitions, frozen selection rules, missingness/timeouts, intervention budgets, artifact schema, and stopping behavior. These omissions are already causing the defects above. The repo’s two contamination incidents and lost per-work records directly justify retaining those requirements. See [AGENTS.md:63](/home/bmarti44/stencil-llm/AGENTS.md:63) and [AGENTS.md:92](/home/bmarti44/stencil-llm/AGENTS.md:92).

   Keep a short registration, but make it sufficient to implement the experiment without new scientific choices. Allow focused review of substantive implementation changes and repairs; “never per iteration” must not prohibit checking a changed intervention or scorer.

28. **HIGH — A/C/D: the proposed cross-cutting conclusion is false as written, and the retirement list loses useful distinctions.** C2 compares two pin-selection policies; it says nothing about prose versus structure. The internal-wave report itself gives wave 44.8 versus reinsertion 43.0. W3a subsequently reports a clean-format positive result, even though W3b’s override/readout gates failed. See [multiif_evict.py:590](/home/bmarti44/stencil-llm/scripts/multiif_evict.py:590), [internal-wave-report.md:6](/home/bmarti44/stencil-llm/results/internal-wave-report.md:6), and [WORKLOG.md:1338](/home/bmarti44/stencil-llm/WORKLOG.md:1338).

   Remove “prose beats every mechanism” as a universal conclusion. Preserve the qualified W3a result and the informative W3b readout failure. Parking S3, GPT-2, and the custom authoring pipeline is reasonable prioritization; presenting untested or narrowly tested families as scientifically extinguished is not.

29. **HIGH — E/B: fixed free-memory thresholds do not establish feasibility.** The 1.7B implementation explicitly materializes fp32 attention and full vocabulary logits. At 6,144 tokens, one `[16,T,T]` attention tensor is **2.25 GiB**, and `[T,151936]` fp32 logits are **3.48 GiB**. Those exclude simultaneously live intermediates, weights, loading/conversion peaks, cache, allocator reserve, and the peer process. The older W0 smoke used only 397 tokens. See [qwen3.py:327](/home/bmarti44/stencil-llm/src/stencil/qwen3.py:327), [qwen3.py:445](/home/bmarti44/stencil-llm/src/stencil/qwen3.py:445), and [w0_train.py:174](/home/bmarti44/stencil-llm/scripts/w0_train.py:174).

   Do not multiply inference attention memory by all layers indiscriminately, but do measure the actual peak. Register maximum-length pilots for training, long-history prefill, and package parity. Twenty-six GB free is not a demonstrated budget for every proposed path.

30. **HIGH — E: coordination and deadline guarantees are not implemented by these rules.** Two sessions can both observe free resources and launch before either sees a message. Use one shared reservation mechanism with an atomic acquire/release protocol. The reused Multi-IF entrypoint’s current guard accepts only an empty GPU or one explicitly declared owner; it does not implement “foreign resident server plus one cooperating job.” See [multiif_evict.py:934](/home/bmarti44/stencil-llm/scripts/multiif_evict.py:934) and [determinism.py:34](/home/bmarti44/stencil-llm/src/stencil/determinism.py:34).

   `--deadline 300` is checked after prefill, inside decoding; it is not a hard prefill/process deadline. W0 training and the old seal lack the proposed chunk/deadline interface. Per-session atomic output can still lose a session’s many completed arm/work generations. Save completed work-arm records and stop starting work before the reservation expires.

31. **MEDIUM — B/E: the 7.8-hour estimate is a planning guess presented as a measured program.** The old Multi-IF run spent **14.916 hours across six arms**, plus 5.934 hours generating history. Dividing arm time by six gives 2.486 hours, but does not measure echo-only latency; arm output lengths vary substantially. Three fixed 303-conversation chunks provide essentially no allowance around a 50-minute target.

   W0 training actually took **6 min 9 sec**, reasonably close to the stated 6.5-minute estimate; the 85.6-minute seal estimate is supported by recorded timestamps. Those do not price LoRA qualification, the extra causal controls, MemoryCode adaptation, a 4B retry, shared-device contention, or HF requalification. The earlier MemoryCode audit estimated 4–8 author-hours and a broad 5–15 GPU-hour range—not a measurement either. See [w0-train-status.txt:1](/home/bmarti44/stencil-llm/results/logs/w0-train-status.txt:1), [WORKLOG.md:1252](/home/bmarti44/stencil-llm/WORKLOG.md:1252), and [astra-research-blockers.md:51](/home/bmarti44/stencil-llm/results/astra-research-blockers.md:51).

   Make a measured pilot and revised budget the launch prerequisite, not an optional afterthought.

32. **HIGH — F: the verification list misses the failure modes and contains a failing repository-wide gate.** I ran Ruff without cache writes: **1,501 findings**. `make gate-0` runs Ruff after pytest, so `testpaths` alone cannot make it pass. See [Makefile:8](/home/bmarti44/stencil-llm/Makefile:8) and [pyproject.toml:28](/home/bmarti44/stencil-llm/pyproject.toml:28).

   The proposed tests also omit statistical verdict boundaries, seed-block exclusion, comment qualification, budget packing, oracle isolation, historical baseline replay, and interruption/resume consistency. A count of 911 tracked files establishes neither the right identities nor complete arm coverage. Verify manifest-bound identities and schemas. Scope lint to changed code or explicitly budget the existing debt.

33. **MEDIUM — C/F: the hygiene prescription will not meet its own final check.** The proposed ignores cover `head.safetensors` but leave nested encoder weights in `admission-v2/seed*/encoder`, `ft-v3/seed*/encoder`, and `relations-v3/seed*/encoder` unignored. Existing patterns cover only shallower encoder paths or selected subtrees; see [.gitignore:243](/home/bmarti44/stencil-llm/.gitignore:243).

   `b3-ce-s0.pt` and `w3a-audit.json` are already tracked. The source-replay four-file change remains uncommitted. Resolve its disposition before broad hygiene work, and use explicit pathspecs as [AGENTS.md:33](/home/bmarti44/stencil-llm/AGENTS.md:33) requires.

34. **MEDIUM — B2/F: generated code is executed directly on the host.** `score_work` writes the complete generated program to a temporary file and executes it with the normal Python interpreter. Parsing a function does not exclude other top-level code. The five-second timeout is not a sandbox, and the temporary files are created with `delete=False`. See [t2_runner.py:59](/home/bmarti44/stencil-llm/src/stencil/t2_runner.py:59).

   Qualify the existing sandboxed execution path before extending this approach to public coding inputs; keep scorer changes separate from historical outcome claims.

Additional factual corrections and checks:

| Claim | Verification |
|---|---|
| “Single-turn IFEval, n=1024, +0.39, p=.389” | **HIGH: wrong dataset attribution.** It is synthetic `data/b3/conf-v45.jsonl`. Both code and an explicit correction say so: [b3_deficit_conf.py:72](/home/bmarti44/stencil-llm/scripts/b3_deficit_conf.py:72), [WORKLOG.md:2302](/home/bmarti44/stencil-llm/WORKLOG.md:2302). |
| Multi-IF headline rates and N | Recomputed from all 909 saved records: 2,276 aged constraints; full 65.158%, evicted 16.652%, classifier pins 57.206%, pins+echo 59.227%, role pins 60.501%. |
| C2 “3.5 points” | Correct **conversation-mean** difference; pooled constraint difference is about 3.30 points. Keep estimands labeled. |
| C1/C3 p-values | Recomputed as approximately `3.6933e-85` and `1.5875e-65` under the historical conversation-level method. The saved summary rounds them to zero; shared-source dependence remains finding 10. |
| 911 tracked evidence files | Correct. All `results/gpt2/` files are untracked. |
| W0/classifier hashes | Both cited prefixes match actual bytes: `eab4831f…`, `22328135…`. Encoder size is 133,462,104 bytes, approximately 127.3 MiB. |
| SELECTOR 3.9→88.3 | Saved final artifact contains 5/128 versus 113/128. The 84% reinsertion comparison comes from another experiment block. |
| Deployment “four months stale” | **LOW: false.** Its last commit is September 1, 2026—ten days before this plan. |
| 215 unpushed commits | Correct against the configured upstream. |
| 30B directory “57 GB” | Approximately 56.89 GiB, or 61.08 decimal GB. Label units. |
| Two listed GPT-2 checkpoints “~23 MB” | **LOW: wrong total.** Together they are 15,763,150 bytes. |
| PID 4110069 / 26 GB free | **LOW: stale snapshot.** During this review the PID was absent and `free -g` reported 114 available. No GPU workload was launched. |
| 2,142 collected tests; 246 reviews / 85% | Not independently certified here. There are 181 Python experiment scripts; the review-document count needs a stated classification rule. Test collection is not evidence that tests pass. |

**Minimum edits required for acceptance:**

1. Replace A’s claim with one the actual intervention can identify; correct SpotLight, IFEval, and “prose beats everything” wording.
2. Repair and qualify the comment scorer, preserve the historical qualification, and reserve unused evaluation seeds.
3. Redesign Exp 2 with matched causal ablations, a fair frozen LoRA protocol, explicit estimands, intervals, and exhaustive verdicts. Preserve the known competence-harm disclosures.
4. Make the independently specified shipping reminder arm mandatory in Exp 1; account for shared source prompts and verify historical/new-runtime compatibility.
5. Write a complete MemoryCode adapter contract before authorizing its GPU budget: native-versus-derived protocol, independent split units, label isolation, legal oracle packing, checker qualification, power, and a viable 4B fallback.
6. Delete D3. Retain bounded development/repair budgets, lineage, freezes, complete records, and review of substantive changes.
7. Replace fixed resource guesses with maximum-length pilots, an atomic shared reservation, enforceable stopping, and resumable work-arm records.
8. Separate research results from HF implementation claims; qualify the new package end to end, resolve component licenses and corpus provenance, and replace the unbounded hygiene gate with a concrete scoped check.

Review used source reads, saved-result arithmetic, standard-library checks, and cache-disabled lint. No files were modified and no model, GPU workload, or network process was launched. Upstream MemoryCode contents and external bibliographic/license claims remain unverified beyond the local reports; they must not be treated as cleared by this review.
