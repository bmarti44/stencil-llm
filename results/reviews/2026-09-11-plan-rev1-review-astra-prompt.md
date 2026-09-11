You are Astra (gpt-6-astra), acting as an adversarial, author-disjoint reviewer of a RESEARCH PLAN. Use maximum reasoning effort. You have READ-ONLY access to the repository at /home/bmarti44/stencil-llm. Do not write or modify any file; do not run any model, GPU or network process; do not read data/bench/ contents. Print your complete review as Markdown to stdout.

Your job: break this plan. It was written today by the orchestrator after three audits. Brian will decide whether to execute it. For each of the plan's parts (A re-scope, B three experiments, C HF package, D process diet, E GPU protocol, F verification), find: (1) factual errors about the repo — verify every file path, function name, line number, seed range, measured cost and number the plan cites against the actual files (e.g. scripts/multiif_evict.py, scripts/w_seal.py, scripts/w0_train.py, src/stencil/qwen3.py, src/stencil/wave.py, src/stencil/t2_runner.py, results/qwen/multiif-evict-909-prequery-v2/meta.json and a conv-*.json record, deploy/stencil_wave/, LEDGER-PLAN.md, results/internal-wave-report.md); (2) statistical or design flaws — confounds, unidentified contrasts, underpowered N, wrong unit of analysis, readings that cannot distinguish the hypotheses, kill rules that reintroduce the failure modes the audits found; (3) feasibility errors — GPU-hour estimates, memory on a shared GB10 with ~26 GB free, chunking, author-hours hidden inside "near-zero code"; (4) whether Exp 2's "uniform bias" control really separates selection from emphasis, and whether the parameter-matched LoRA is a fair control; (5) whether Exp 3's MemoryCode port is honest (eviction/echo semantics on a dataset whose sessions are given text; leakage of the oracle labels; regex checkers; competence floor for a 1.7B model); (6) whether the HF package as described would be honest and useful, and whether the license plan is sound; (7) anything the plan retires that should not be retired, or keeps that should be cut; (8) missing risks. Grade every finding low/medium/high/critical with file:line evidence. Then give a score 0-100 for "execute as written" and list the minimum edits that would make you accept it. Be blunt; no preamble.

THE PLAN FOLLOWS.

# Stencil: back-on-track research plan (draft, 2026-09-11)

## Context

Brian asked for an audit of the Stencil repo: what has actually been proven, whether the
"does not work" claims hold up, what is missing for an honest HuggingFace release, what the
2024-2026 literature already covers, and what experiment would prove something
mechanically interesting. Three read-only audits (positive results, negative results,
engineering/HF readiness) plus a web-literature pass were run. This file records the
findings and the recommended program. A second researcher (session "looped-transformer")
shares the GB10; a GPU protocol was agreed and is recorded in section E.

## Findings (established by the audits; file references are repo-relative)

### What is proven, and how strong it is

| Result | Trunk / data | Numbers | Strength | Gaps |
|---|---|---|---|---|
| Leg B retention under eviction | Qwen3-1.7B, Multi-IF 909 conv (public) | full 65.2, evicted 16.7, clf pin+echo 59.2, role pin 60.5; C1/C3 p~1e-85/1e-65; C2 FAIL: role rule beats trained selector by 3.5 pts | Only public-benchmark result; clustered t + Holm; 911/911 evidence files tracked | No echo-only arm (KV pinning vs text echo unidentified); encoder weights gitignored; registered NOT SUPPORTED on 1 invalid output vs 0 |
| Internal wave | Qwen3-1.7B, synthetic coding sessions, n=96 | 264k-param controller, adherence 25.2->44.8; beats oracle 38.3, proxy 37.4, reinsertion 43.0 (30 broken works) | Most mechanistically interesting: learned per-step pre-softmax bias field with WHERE/WHEN/selectivity ablations | 1 seed, no p-value, comment type 0/120 all arms, format-generalization retracted, w0-ce.pt untracked |
| SELECTOR | Qwen3-1.7B, synthetic named-query, N=32, n=128 | 3.9 -> 88.3; reinsertion 84 @ 504 tok | Clean actuator test, bitwise zero-identity | Task is dictionary-solvable (results/selector-review-sol.md:80-88); no retrieval or LoRA baseline; headline compares across splits; evidence JSON + weights untracked |
| GPT-2 focus cache | GPT-2 small, windowed attention | 100 vs 4.3 zeroed; transplant 28/32 | Clean construction | Gap guaranteed by construction; 16-answer space; results/gpt2 0 tracked files |
| larger-test-v2 | Qwen3-30B-A3B, 64 authored episodes | register vs none: delivery 35/0/28 p=3e-11 | Rigorous stats | Prose reminder T ties/beats register everywhere; R loses semantic integration 45 vs 52 (p=.0078) |
| W3 README bullet | | "+42 pts, 73/73 never wrong" | **Misrepresents two FAILED gates** (WORKLOG.md:1326-1337, results/w3-results-sol.md) | Must be rewritten |

Best-replicated finding in the repo: restating the correct current rule in prose at request
time beats every structured or internal mechanism tried (FOCUS-2d 143/256 vs 176/256;
larger-test-v2 T >= R; C2 role rule > classifier).

### Negative claims, re-verified

- Solid (A): static always-on bias (n=196, -4.6 monotone); deficit-gated bias on single-turn
  IFEval (n=1024, +0.39, p=.389, 8-cell grid); mean-difference skill vectors (18 cells,
  0 induction, cosines .89-.98); MoE router bias harms competence (16/32 -> 7/32, p=.022);
  C2; FOCUS-2d; cosine-threshold liveness; blind rhythm pressing; hard-threshold abstain.
- Narrow (B), idea NOT ruled out: deficit/classifier-gated bias on cache columns (one dose
  imported from a single-span single-turn calibration into a multi-span regime, n=20,
  absolute degeneracy kill rule pre-flagged as confounded in results/gated-wave-review-fable.md:83-97;
  primary arm gained +3 with 4 wins/1 loss and matched full context 44/44 before being killed
  on 8/20 512-token loops); function-vector residual steering (single operating point chosen
  on 4 examples by non-degeneracy only, results/qwen/fv-vectors/grid.json has no efficacy
  measure; type-vector cosines to .84); check43b concept routing (n=8/cell); check32/33 cache
  transplant (harness never qualified; check34 positive control worked 59/60).
- Process failures (C): x0.25 dosed wave (+1.5 vs +2.0 gate, one item, p=.549); check42
  every-request rendering (A beat C 151/192 vs 131/192, "NOT CLOSED" on a token-cap clause);
  FOCUS-3 v1/v2 (one sentence template, 64x); FOCUS-3 v3-v8 six INELIGIBLE on CPU counters,
  then the v8 diagnostic scored automatic 57/64 vs none 29/64 with no verdict; PRESS T1 (92.9%
  leakage reduction closed against a bar unreachable at n=17); four source-replay bank stalls
  on single authoring defects under a no-repair protocol.

The README sentence "every amplification variant degenerated or under-delivered and is
closed with data" (README.md:69-76) is stronger than any per-check record supports.

### Engineering / publication state

- PyTorch only; hand-rolled bitwise-deterministic `src/stencil/qwen3.py` with attention-bias hooks.
- `pytest tests/` collects 2142 tests cleanly; bare `pytest` (and `make gate-0`) breaks on
  deploy/ and results/ collection (no `testpaths` in pyproject.toml).
- 246 review docs vs 181 experiment scripts; 85% of results/*.md are reviews.
- plan/PROTOCOL.md absent (archived copy governs); AGENTS.md points at files that do not exist.
- License conflict: root LICENSE GPLv2; deploy/stencil_wave/pyproject.toml MIT; MODEL_CARD.md apache-2.0.
- 215 unpushed commits. models/qwen3-30b-a3b-hf (57 GB) and data/classifier/model/focus-lora-4b
  untracked and NOT gitignored; results/focus-mechanism-composition-astra.md untracked but load-bearing.
- Untracked evidence behind headline claims: results/qwen/s1-oracle.json, s2-selector.json,
  s3-a0.json, s3-a1-oracle.json, s3-a2-selector.json, s3-final-sealed.json, s3-selector-weights.pt,
  w0-ce.pt, w0-proxy.pt, w3a-audit.json; all of results/gpt2/; data/classifier/model/ft/encoder/model.safetensors.
- Publish-ready-ish: deploy/stencil_wave/ (real model card, push_to_hub.py dry-run default,
  parity receipts) but pinned to transformers==4.51.0 and four months stale.
- GPU: one GB10, 119 GB unified; a foreign llama-server holds ~93 GB; ~26 GB free.

### Literature position (2024-2026)

- PASTA, SpotLight (EACL 2026), InstABoost (ICLR 2026): attention steering toward a
  user-specified instruction span, single-turn. None learns WHICH of many instructions
  governs now. That selection is Stencil's genuine gap.
- V-Steer (arXiv 2607.26228): value-cache edits for instruction hierarchy. Memory Inception
  (2605.06225): KV banks at selected layers. Knowledge Packs (2604.03270): exact KV injection.
- IFScale (2507.11538), ManyIFEval (2509.21051): compliance collapses with instruction count;
  sub-2B models fail multi-constraint composition. Stencil's N=32 regime is exactly this.
- MemoryCode (ACL 2025, Apache-2.0): coding conventions with updates across sessions,
  regex-checked; Llama-3.1-8B 71.7% -> 12.5%. Closest public benchmark to Stencil's goal.
- Steering-vector reliability (2504.04635, 2505.22637, 2602.17881): high variance, degeneration
  at strength; matches Stencil's cache-column wave failure mode (loops at 512-token cap).
- Instruction (In)Stability (COLM 2024): drift within 8 turns from attention decay.

## Plan

### A. Re-scope: the one claim to pursue

In a frozen Qwen3-1.7B, a ~264k-parameter controller reading the layer-20 residual at each
generation step can SELECT which of several simultaneously stated, updated and cleared
obligations governs the current token, by emitting a pre-softmax attention bias on that
obligation's span; and it is the selection, not emphasis, that produces the adherence gain.
PASTA/SpotLight/InstABoost bias toward a user-specified span in a single turn; the learned,
per-step choice of span under many obligations and across turns is Stencil's gap. The claim
is falsified if a uniform bias over all obligation spans (SpotLight-equivalent, no selection)
or a parameter-matched LoRA trained on identical data matches the controller, or if the result
does not replicate over seeds. Its public-benchmark leg is the retention half of the same
question: under a fixed retention budget, does query-conditioned selection of which prior
instructions to keep/echo beat the parameter-free role/recency rule (Multi-IF 909, MemoryCode).

Reuse: `src/stencil/wave.py`, `scripts/w0_train.py`, `scripts/w_seal.py`,
`src/stencil/t2_sessions.py`, `scripts/multiif_evict.py`, `src/stencil/ledger.py`,
`src/stencil/qwen3.py::prefill_with_eviction`, `src/stencil/salience2.py`, the frozen
`data/classifier/model/ft` classifier (as one arm), `deploy/stencil_wave/`.
Retire as claim sources (park, do not delete): the S3 dictionary task, the GPT-2 focus cache
headline, the 30B FOCUS-3 admission line, the source-replay banks, every residual-stream /
function-vector / MoE-router steering recipe, `src/stencil/qwen_cache.py` latent-cache path.

### B. Three cheapest decisive experiments (~7.8 GPU-h total, all Qwen3-1.7B, chunks <= 50 min)

**Exp 1: Leg B echo-only arm on the existing 909 Multi-IF conversations (~2.5 GPU-h)**
- Question: does KV pinning contribute anything over echoing the same selected text?
  (clf_pinned_echo 59.2 vs clf_pinned 57.2 confounds pins and echo.)
- Near-zero code: each sealed record in `results/qwen/multiif-evict-909-prequery-v2/conv-*.json`
  stores `echo_context_token_ids`, `evict_range`, `history`, `selected_spans`, `ci`.
  `run_arm(..., keep=[])` from `scripts/multiif_evict.py` is the echo-only arm; scoring via
  `_score_fields`. New script `scripts/multiif_echo_only.py` (~150 lines) importing `run_arm`,
  `_score_fields`, `_cluster_values`, `_contrast`, `_one_sided_cluster_p`, `invalid_output`,
  `repeated_4gram_fraction`; writes to NEW dir `results/qwen/multiif-evict-909-echo-only/`
  (never touch the sealed dir; schema 2); `--start/--limit` chunking (3 x 303).
- Arms: `echo_only` (new); if budget remains, `role_echo` (role-rule text, no pins), the arm
  that would actually ship.
- N/test: 909 conversations, 2,276 constraints. Primary C4 = clf_pinned_echo − echo_only,
  one-sided cluster t (`_one_sided_cluster_p`, `clustered_lower_bound`) plus exact sign test on
  discordant conversations (`stats.mcnemar_exact_one_sided`). C5 = echo_only − evicted (sanity).
  Discordance floor < 6 → INCONCLUSIVE.
- Readings (register before launch): (a) LB(C4) > 0, p <= .05 → pins contribute; deliverable is
  a retention package (pins + echo); cache-column wave reopen becomes eligible. (b) mean(C4) <= 0
  or LB <= 0 with |mean| < 2 → pins add nothing demonstrable; deliverable is a reminder package
  (role rule + echo, no KV surgery); cache-column wave retired without rerun. Safety as excess
  over `full`; no integer kill clause.

**Exp 2: Internal wave with 3 seeds, uniform-bias and parameter-matched LoRA controls (~3.3 GPU-h)**
- Question: is the gain learned per-step selection, or emphasis of the instruction block
  (SpotLight-equivalent), and does it replicate?
- Training: `scripts/w0_train.py` hard-codes `torch.manual_seed(0)` (lines 109/172/189);
  parametrize with `SEED` → `results/qwen/w0-ce-s{0,1,2}.pt`, identical recipe. Measured cost
  6.5 min/run → 20 min. Seed 0 should reproduce sha `eab4831f…` (pinned `scripts/w_seal.py:35`);
  if not, keep both and record it.
- LoRA control: rank-4 on q_proj (2048→2048) and v_proj (2048→1024) at layers 20-27 of
  `src/stencil/qwen3.py::_Block` = 229,376 params (vs 264,321), B zero-init so disabled path is
  bitwise the trunk; same CE data/recipe via `OBJ=lora`. If plumbing exceeds 4 author-hours,
  drop it and state "no fine-tuning baseline" in the card (no peft substitution).
- Seal: `scripts/w_seal2.py` from `w_seal.py`: fresh sealed seeds 13,600,000-095,
  `split="final"`, `interference="s0"`, greedy, max_new 120, atomic per-session records,
  `--arms`, `--start/--limit`. Arms: `base`, `wave_s0/s1/s2`, `uniform` (β=2 peak-normalised
  bias equal over ALL active ledger sentence spans from `t2_runner.ledger_sentence_spans`,
  every step, no selection), `oracle` (hand spans = PASTA-style), `reinsertion`, `lora_r4`.
  Optional `misdirected` (drop first if budget binds). Prior 5-arm seal took 85.6 min →
  estimate 160 min for 8 arms.
- N/tests: 96 sessions, ~408 works, ~1,218 opportunities per arm. Primary unit = session:
  one-sided exact sign test on per-session adherence differences. Secondary: exact McNemar on
  per-work binary (408 pairs, clustering caveat). Per-type table; comment type stays disclosed null.
- Readings: H1 each `wave_s*` > `uniform`, p <= .05, all three seeds, gain over base >= 10 pts
  per seed → PASS "learned selection, not emphasis". Two or more seeds fail → FAIL: the wave is
  an automatic SpotLight; drop "selection". Seeds disagree in sign → INCONCLUSIVE. Breakage kill
  excess-over-baseline: parse rate >= base − 2 pts, paired-broken <= 5% of works per seed.
  H4: if `lora_r4` >= every `wave_s*`, card says parameter-matched fine-tuning matches; the
  controller's residual value is frozen trunk, removable, zero added tokens.

**Exp 3: MemoryCode port with oracle/role/classifier/BM25/wave-selector echo arms (~1.7 GPU-h + 20-min pre-gate)**
- Question: on a public benchmark with instruction updates and many instructions per task,
  under a fixed echo budget, does query-conditioned selection beat the role/recency rule, and
  what is the headroom (oracle − role)?
- Setup: clone github.com/Cohere-Labs-Community/MemoryCode (Apache-2.0) into
  `vendor/memorycode`, pin sha in `data/bench/pins-manifest.json`. Render dialogues as chat turns
  (mentor→user, mentee→assistant), final task = current user turn, prior sessions = evictable
  history, system prompt protected. Keep items with history <= 6,144 tokens. 16 setup + 64
  evaluation items, seed 0, disjoint; hash the eval list before any outcome is viewed.
- Arms (text echo, E=256 tokens, no pins in this pass): `full`, `evicted`, `oracle_echo`
  (dataset-labelled applicable instructions = ceiling), `role_echo`, `clf_echo` (frozen ft,
  0.5), `bm25_echo` (hand-rolled BM25 over candidate sentences, query = final task),
  `wave_sel_echo` (zero-shot: `w0-ce.pt` W_q/W_k scores of layer-20 features). ~75 s/item.
- Competence pre-gate on 16 setup items (register first): `full` all-satisfied >= 4/16 and
  `full − evicted` >= 3/16 on 1.7B; else one retry on Qwen3-4B; else INELIGIBLE, the 64 never opened.
- N/tests: 64 items, primary binary = all applicable instructions satisfied per MemoryCode's
  regex checkers. Exact McNemar. Headroom precondition `oracle_echo − role_echo` >= 8/64 net,
  else selector contrasts INCONCLUSIVE ("no headroom at this budget"); then Holm over
  `bm25_echo`, `clf_echo`, `wave_sel_echo` vs `role_echo`.
- Readings: oracle ≈ role → selection has no value at this budget (rule ships). Oracle >> role
  and BM25 closes >= 50% → retrieval suffices. Oracle >> role and nothing closes it → a learned
  query-conditioned selector is the next registered program with a measured target.

Why others wait: the cache-column deficit-gated wave reopen (n >= 64, 1024 cap,
excess-over-base rule, ~1.8 GPU-h adapting `scripts/clf_probe_check.py`) runs fourth and only
if Exp 1 reading (a) holds. The SELECTOR re-baseline is folded into Exp 2 (LoRA, uniform,
oracle-span) and Exp 3 (BM25, oracle selection); the dictionary task is retired.

### C. HuggingFace publication package

- Model repo `stencil-retention-qwen3-1.7b` built from `deploy/stencil_wave/` → 0.2.0:
  (1) evict/pin/echo runner ported to HF (`retention.py`, mirroring `qwen3.prefill_with_eviction`
  and the exact `render_text_ledger` format); (2) role-rule selector as default; (3) salience
  classifier `data/classifier/model/ft/encoder` (128 MB, Hub-hosted, sha `22328135…` pinned in
  the 909 `meta.json`) as optional selector; (4) wave controller as a separated research add-on,
  amplification OFF by default. `deploy/stencil_wave/src/stencil_wave/controller.py:5` says the
  shipped weights are `results/qwen/b3-ce-s0.pt`, whose public-benchmark siblings were null;
  the card must say so or re-point to the Exp 2 winner. Re-pin transformers to the `uv.lock`
  version; re-record `parity.json` (~5 GPU-min).
- Datasets: `stencil-synthetic-sessions` (generators `t2_sessions.py`, `qwen_task.py` + seed
  manifests + sha256 of rendered texts); `stencil-instruction-salience` (20,054-row classifier
  corpus with per-file LLM-authorship disclosure, the IFEval/Multi-IF contamination incidents
  and fixes, the BFCL lineage paragraph from `LEDGER-PLAN.md:634`).
- Model card: base + revision; mechanism; headline Multi-IF table incl. echo_only and the C2
  failure; internal wave three-seed table (synthetic only); MemoryCode; a negative-results table
  (n, p) for every Solid negative and a separate "not ruled out" list; the cross-cutting
  "prose beats structure" finding as its own section; limits.
- License: propose Apache-2.0 for the whole repo (matches Qwen3, MemoryCode, Hub norms), with
  Brian's explicit consent, a NOTICE file; vendored code keeps its own licenses. Needs Brian's
  decision (question below).
- Force-add: `results/qwen/s3-selector-weights.pt`, `s3-a0.json`, `s3-a1-oracle.json`,
  `s3-a2-selector.json`, `s1-oracle.json`, `s2-selector.json`, `s3-final-sealed.json`,
  `w0-ce.pt`, `w0-proxy.pt`, `b3-ce-s0.pt`, `w3a-audit.json`; `results/gpt2/*.json`, `*.txt` and
  the final checkpoints only (`cache-v8-s0-ckpt.pt`, `base-v4-s0-ckpt.pt`, ~23 MB);
  `data/classifier/model/ft/{head.pt,metrics.json}` + encoder config/tokenizer files (weights to
  Hub); `git add results/focus-mechanism-composition-astra.md scripts/focus_check32.py`.
- Gitignore: `models/qwen3-30b-a3b-hf/`, `data/classifier/model/focus-lora-4b/`,
  `data/classifier/model/**/head.safetensors`, `relations-seed*/`, `relations/encoder/`,
  `relations/dev_predictions.npz`.
- README rewrite: delete road-step 4 (lines 144-148, the W3 bullet); collapse FOCUS-3 v4-v8
  (lines 78-114) to one line; new order = retention headline with C2 failure and echo-only
  reading → "prose beats structure" → internal wave as synthetic N-seed result → negatives table
  → boundaries → repo map with one reproduce command per result.

### D. Process diet (8 rules)

1. One review per registered result (design before launch, results after), never per iteration.
2. CPU eligibility/instrument failures do not consume the iteration stop-loss: fix, re-run, one-line disclosure.
3. Near-miss rule: gate missed by <= 1 item or p > 0.3 is INCONCLUSIVE, never FAIL; INCONCLUSIVE cannot be cited as a negative.
4. Kill rules are excess-over-baseline at matched n, never absolute integer clauses.
5. Bank/authoring defects are repaired with disclosure (item id, before/after, who); sealed outcomes stay untouchable.
6. Every registration names: unit, exact test, discordance floor, N, GPU cost, three readings. Nothing else required.
7. One `results/<name>/RESULTS.md` per registered result; reviews under `results/reviews/`; no new root-level review markdown.
8. A claim enters README only from a RESULTS.md with a p-value or an explicit "descriptive" label, stating n, p and the arm it lost to.

### E. GPU coordination (agreed with the looped-transformer session on 2026-09-11)

- Neither session owns llama-server pid 4110069 (~93 GB). ~26 GB free while it is up.
- Before any launch: `free -g` and `nvidia-smi --query-compute-apps=...`; launch only if
  available >= 10 GB (1.7B) or >= 20 GB (4B); otherwise wait, re-check every 10 min.
- First-come while the server is up: whoever has a run live keeps it; the other waits for a
  "finished" message. Peer runs Ouro-2.6B bf16 (~6-10 GB), checkpoints every request, can pause
  within a minute on request.
- Register every launch: `echo $! >> .stencil-owned-pids`; never signal a foreign process.
- Message "looped-transformer" before any run > 30 min and when it finishes; chunk runs <= 50 min.
- `--deadline 300` and `--max-new` caps on every arm; atomic per-item records; one Stencil GPU
  process at a time; no 30B runs.

### F. Verification

- Exp 1: `set -o pipefail; uv run pytest -q tests/test_multiif_evict.py tests/test_multiif_echo_only.py`;
  smoke `--limit 2`; three chunks; `--summarize` prints C4/C5 with n=909, LB, p, discordants,
  safety excess; `git ls-files results/qwen/multiif-evict-909-echo-only | wc -l` = 911.
- Exp 2: `uv run pytest -q tests/test_wave.py tests/test_wave_ref.py tests/test_lora_linear.py`
  (disabled LoRA path bitwise-equal; 229,376 params); `SEED=0 OBJ=ce uv run python scripts/w0_train.py`
  reproduces sha `eab4831f…` or logs mismatch; `w_seal2.py --arms base --limit 2` smoke;
  `results/qwen/w-seal2.json` carries per-seed adherence, sign-test p, McNemar p, per-type table, verdict.
- Exp 3: `uv run pytest -q tests/test_memorycode.py` (rendering, candidate extraction, oracle
  labels, BM25 determinism, regex parity with vendor evaluators on 3 fixtures); pre-gate
  `results/qwen/memorycode-setup/summary.json`; sealed `results/qwen/memorycode-64/summary.json`.
- HF package: `cd deploy/stencil_wave && STENCIL_REPO=... uv run pytest -q`; `push_to_hub.py`
  dry-run lists controller, salience weights, encoder, config, card; every number in the card
  grep-checked against RESULTS.md; then `--push` only with Brian's go.
- Hygiene: `git status --short | grep '^??'` empty under models/ and data/classifier/model/;
  `git diff --check`; `uv run ruff check .`; README has no "4×10⁻¹²" or "73/73"; `pyproject.toml`
  gains `testpaths = ["tests"]` so bare `pytest` and `make gate-0` work.

### Execution order

1. Repo hygiene + README rewrite + force-adds + gitignore + testpaths (CPU, half a day).
2. Exp 1 (register readings → 3 chunks → RESULTS.md → one review).
3. Exp 2 (register → train 3 seeds + LoRA → seal → RESULTS.md → one review).
4. Exp 3 (vendor MemoryCode → pre-gate → 64 → RESULTS.md → one review).
5. HF package + card + dataset cards; push after Brian's explicit go.
6. Conditional: cache-column wave reopen only if Exp 1 reading (a).

## Open decisions for Brian

- License: adopt Apache-2.0 repo-wide (recommended) vs keep GPLv2?
- HF org/namespace for the push, and whether the 128 MB classifier encoder may be published.
- Whether the in-flight source-replay-preparation-v2 four-file change (uncommitted) is parked or completed before this program starts.
