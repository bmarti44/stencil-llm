Data lineage — fit-on: newly seeded, operand-balanced synthetic extraction examples only; separate synthetic setup examples may select the actuator/dose. Evaluated-on: 64 fresh seeded episodes, disjoint by operand-set checks as well as seeds. Trunk: frozen Qwen3-1.7B. No `data/bench`, sealed IFEval/BFCL contents, b3 data/probe/response, SC1 setup/final episodes, or existing fitted vector may enter this work. This coder task is CPU implementation only: no fitting/training or model/GPU process.

# Brief: focus1-harness — frozen-skill SET/HOLD/SWITCH/CLEAR screen

## Objective

Implement the FOCUS-1 DRAFT v1 section appended to LEDGER-PLAN.md, without running the experiment or representing the draft as registered. Build one small experiment driver, `scripts/focus1.py`, with modes `setup / extract / select / run / analyze`, pure helpers in `src/stencil/focus1.py`, and CPU tests using fake trunks. Preserve the exact registered science when the draft becomes registered; flag ambiguities in the handoff instead of silently choosing a favorable interpretation.

CPU only; foreground only; never launch a model or GPU process, fit/train anything, terminate/signal any process, inspect sealed IFEval input or sealed BFCL cohort contents, or launch another coder/reviewer/model. The BFCL preflight is already running. Implement future GPU stages, but do not execute them. Do not queue a watcher or use external timeout commands. A wrapper's existing lock belongs to that wrapper: do not wait on it. Execute this brief in a direct foreground coder session: the current `tools/run_codex_agent.sh` unconditionally writes WORKLOG.md, so it cannot launch this brief under the current exclusion.

Reuse existing code without inheriting its data or old decision rules:

- Read `scripts/function_vectors.py` for final-position layer-input extraction and grid organization. Use `stencil.function_vectors.mean_difference` and `make_residual_hook`; never call its `extract`, `grid`, `probe_constraint_types`, b3 loaders, or existing vector artifacts. The new synthetic generator is the only source of example text.
- Use `src/stencil/qwen3.py`'s KVCache, `residual_hook`, `capture_hidden` and `prefill_with_eviction` pre-query semantics. Extraction captures layer INPUTS at L=12/16/20. Injection affects only the last current position. No change to trunk hooks is expected or allowlisted.
- Read `scripts/clf_probe_check.py --vectors/--fv-grid` consumption logic for hash-bound frozen artifacts; do not run/import its experiment or copy its inherited calibration verdicts.
- Read `archive/PLAN.md` Phase 4's donor/sham/shuffle construction; transplant ONLY an operand-blind enum, never donor KV or a full donor trajectory. Own-state sham must be exact; different task answers must be identifiable on fresh recipient operands.
- Import only `stencil.sc1_episodes.parse_json` and `json_equal` for short-output scoring. Do not invoke its compiler, cohort loader, authoring, evaluator, runner, numeric power law, or SC1 allocation framework. Use local fixed-shape list validation and the existing function-vector repetition helper; SC1's 256-token truncation rule is inappropriate for this 64-token screen.
- `src/stencil/wave.py` contains WaveController/WaveRNN; `INTERNAL-WAVE-PLAN.md` and `scripts/w0_train.py`/`w1_train.py` document the later gradient recipe. They are reference material only. The training scripts perform GPU work at module top level: never import them. FOCUS-2 remains a ten-line unregistered sketch, with no controller implementation here.

Implement the phase/state contract literally. Sorting phases are SET/HOLD/SWITCH/BACK, correct addresses `(a,a,other(a),a)` and swapped/transplant their complement. Canonical sorting prefixes exclude earlier generated replies; only an enum persists across the two D=128 neutral-token delays. All five sorting arms start each decision with equal independent KV clones and identical prompt tokens/positions, before hooks are applied. Donor state is captured before operands are read; donor and recipient lists differ. A/B random directions are independently seeded and norm matched, fixed across the episode. Sorting arm order may be seeded once, never chosen from outputs.

CLEAR forks the actual correct BACK cache, including the final generated token, into CLEAR and KEEP before appending the same neutral query. Keep that genuinely steered cache throughout BOTH neutral turns. The clean OFF replay is a separately labeled residual audit at each query, conditioning on the CLEAR fork's exact prior token history; it is not a substitute CLEAR score or a matched-KV treatment. Record per-layer cache and first-decision logit differences. Never use `generate_injected(clear_after=...)`: it rebuilds KV and would change this experiment. The fake trunk must demonstrate that turning a hook off can leave harmful residual KV.

Implement the registered endpoint definitions and exact tests, including conjunctions, stratum/count floors, zero old-task impositions, KEEP interference non-vacuity, shuffled equivalence bound and per-arm episode breakage. Return one unambiguous PASS/FAIL/INELIGIBLE/FAIL-ACTUATOR/INCOMPLETE/INVALID state with reasons, retaining all intermediate scores. Never treat nonsignificance as clearance or control success. Enum transplant is equivalent to oracle swapping, not independent evidence; do not multiply their sample size.

Use the registered SHA-256/MT19937 streams and big-endian seed mapping, with golden CPU fixtures. Pair identical operands across extraction A/B/OFF, balance lengths/tasks, and reject unordered-set collisions across every generated list. The CPU generator can write all banks once, but GPU setup/extract/select may read only extraction/setup inputs and the test hash/count, never test episode contents. Selection uses sort0 for each task and both retained-KV CLEAR/replay and KEEP queries, including the >=4/32 per-task KEEP-imposition floor. Freeze prompts, bank hashes, code/config/tokenizer hashes, layer/dose/vectors and every setup outcome before `run` opens test. Restrict user-supplied paths to the experiment root and the pinned model/config inputs; do not accept arbitrary external corpora. Do not read model weights in CPU tests.

CLI contract (paths below are examples for the later operator; all GPU commands remain unexecuted in this brief):

- `setup --generate-only --out /home/bmarti44/stencil-llm/results/qwen/focus1-v1`: CPU bank/manifests only, no model initialization. Avoid a real benchmark reader anywhere in imports.
- `setup --timing-smoke --out <root> --registered-manifest <registration> --bfcl-completion <terminal-evidence>`: first future GPU operation; use setup examples and measure every registered cost class. No formal competence selection from smoke output.
- `setup --out <root> --registered-manifest <registration> --bfcl-completion <terminal-evidence>`: record the separate 32-episode visible-cue and neutral-OFF competence gates. Use the smoke's retained rate maxima and charge its cost; no replacement bank on failure.
- `extract --out <root> --registered-manifest <registration> --bfcl-completion <terminal-evidence>`: only after competence succeeds; extract fp32 paired differences and normalize to common rho per layer. No gradients or optimizer.
- `select --out <root> --registered-manifest <registration> --bfcl-completion <terminal-evidence>`: inspect setup only, in `(alpha,L)` order, stop at the first eligible cell, write an immutable selection manifest. No existing b3 grid or test outcomes.
- `run --out <root> --registered-manifest <registration> --bfcl-completion <terminal-evidence>`: require successful preceding modes and exact manifest hashes before opening the 64 test episodes; no dose/trunk/seed/length/threshold overrides, retries, resumption or overwrite.
- `analyze --out <root>`: CPU only, reads persisted attempt records and manifests, never generates or loads a model; incomplete records cannot yield PASS.

The registration manifest must bind a section actually marked registered, not this draft. BFCL evidence must be a recorded terminal status for the existing preflight, obtained by the operator without reading cohort contents; BFCL scientific success is not required. GPU entry points refuse missing evidence before model import/loading. Do not create evidence or assume a vanished process means completed preflight. The coder supplies these interfaces but cannot certify or exercise real GPU readiness.

Charge initialization, extraction, selection, test generation, neutral replay, persistence and interruptions against ONE cumulative 21,600-second allocation budget. Keep a simple append-only allocation/attempt log, not another general framework. Timing smoke measures longest prompt/delay, decode, CLEAR/KEEP and replay plus load/check/persistence. Use retained maxima, 1.25 forecast multiplier, remaining reload reserves, and a complete next-attempt deadline reservation. Cooperative checks return normally; no signals, external timeout utility, budget reset, or background chain. A process that cannot return by a cooperative deadline is not certified by CPU fixtures.

Persist every per-decision record in the same run, before aggregates. Include all fields enumerated in the registration, actual hook events, cache non-vacuity, source/recipient/donor mapping, raw output/token/EOS and exception status, comparison inputs and cost. Refuse duplicate attempt IDs/overwrites. For partial or safety-stopped runs retain missing counts and fail closed on PASS; never restart v1 to replace bad outputs. Hash and schema assertions should stay local and small.

## Allowlist

Only the exact four paths in `tools/codex-agents/focus1-harness.allow`: `scripts/focus1.py`, `src/stencil/focus1.py`, `tests/test_focus1.py`, `LEDGER-PLAN.md`. The ledger permission is APPEND-ONLY for the coder handoff; it does not permit editing the draft's thresholds or any SC1 section. Keep test fixtures inline or in temporary pytest directories. Use tmp paths for all fake artifacts.

Do not edit WORKLOG.md, README, any SC1 file/data, trunk/function-vector/controller code, existing scripts/tests, brief/allowlist, benchmarks or model artifacts. No broad `tests/*`/`results/*` exception. If a real shared-hook defect is found, provide its minimal CPU reproduction and an explicit unimplemented dependency in the handoff; do not widen scope or substitute a different actuator.

## Tests first

Write meaningful RED CPU tests in `tests/test_focus1.py` before implementation, then record GREEN. Fake trunk/tokenizer/KV fixtures only; monkeypatch real model loaders, CUDA entry points and forbidden-data reads to fail loudly. Cover the actual CLI consumer as well as helpers:

1. Golden seed derivation and reproducible generation; all partition sizes, per-length/task counts, paired extraction operands and global unordered-set disjointness; rejection of sorted/colliding inputs. Selection never reads test contents. Changing a seed/manifest after freeze, an external data path, or b3/benchmark/SC1 source must fail before model loading.
2. Extraction arithmetic on known fake hidden states; pair normalization and equal norms; zero/nonfinite vectors fail; exact layer-input/last-position hook placement including token 1, OFF/alpha-zero identity. No per-operand vector or donor-content channel.
3. Independent cache clones and equal prompt/KV/position/logit checks before branching; mutation/aliasing and post-query eviction defects fail. Address-only donor copying on different operands and own-state sham identity; fixed norm-matched seeded random controls; full delayed switching and switch-back sequences.
4. Non-vacuous retained-KV CLEAR failure with a fake trunk whose previous hook changed later outputs; removing the hook must fail clearance there. A behaviorally clearing fixture passes only if both neutral queries succeed; replay/residual differences survive reporting. Secret cache rebuild, empty caches, missing hook calls, stale operands and answer-token omission fail.
5. Short-output parsing: wrong order vs invalid schema, no booleans, no extra prose, wrong/missing operands, empty/degenerate/truncated/deadline outputs; exact old-task sorted answers vs neutral copies. A valid but wrong sort is not breakage. Episode aggregation must not count four decisions or swap/transplant as extra trials.
6. Exhaustive small-n exact McNemar tails vs independent integer enumeration, b=c=0 => p=1, and exact binomial boundary enumeration. Recompute 63/64 CLEAR p=0.00956314971305463, 0/64 shuffled p=0.0011790184577738583, alpha=1/60, 29/32 competence. Fixtures fail each floor, stratum, paired comparison, safety gate, KEEP non-vacuity and family conjunction independently; a fully satisfying fixture reaches PASS. An impossible outcome/safety floor yields partial FAIL without fabricated final-N p-values; other missing/budget records yield INCOMPLETE.
7. Fake-clock projection includes reloads, all candidate cells until selection, both neutral audits and persisted overhead; refusal at the cap, retained maxima never decrease, interrupted time remains charged. Missing BFCL/registration/timing/competence/selection evidence refuses GPU modes before loading; draft never counts as registered. CPU `--help`, generation-only and analyze cannot initialize a model.
8. Every mode emits/consumes required records through the real CLI path using injected fake backends; attempt persistence precedes summary, duplicate attempts/overwrites fail, missing/tampered/malformed records cannot PASS. A second broken episode stops scheduling, retains partial evidence and never silently reduces N=64. No script import side effects.

Run only the targeted file, not the full pytest suite. Do not write implementation-mirroring tests for prose or low-impact changes. Exercise test fixtures where invalid baseline artifacts would otherwise pass vacuously.

## Acceptance

All commands are foreground and CPU. From `/home/bmarti44/stencil-llm`, run:

```bash
CUDA_VISIBLE_DEVICES='' .venv/bin/python -m pytest -q -p no:cacheprovider tests/test_focus1.py
CUDA_VISIBLE_DEVICES='' .venv/bin/python -m ruff check --no-cache scripts/focus1.py src/stencil/focus1.py tests/test_focus1.py
CUDA_VISIBLE_DEVICES='' .venv/bin/python scripts/focus1.py --help
git diff --check -- scripts/focus1.py src/stencil/focus1.py tests/test_focus1.py LEDGER-PLAN.md
```

No real extraction, calibration, model load, GPU smoke, competence run, or test evaluation is an acceptance command. Passing CPU fixtures establishes harness behavior only. Commit the allowlisted implementation and append-only handoff with explicit pathspecs, preserving unrelated work, and do not push. An unimplemented scientific dependency is not acceptance; report it honestly. The draft remains unregistered pending review with zero open high/critical findings.

## Ledger handoff

Append a concise FOCUS-1 CPU handoff at the end of LEDGER-PLAN.md, outside the under-120-line registration: actual model, effort, wrapper log path (or `not wrapper-launched`), actual session ID (or explicitly unavailable), commit/files, targeted RED/GREEN results, code/fixture hashes, implemented CLI, deferred GPU commands in order, and unresolved ambiguities with conservative choices. Do not fabricate launch provenance or edit WORKLOG.md.

State explicitly: no fitting/training, no model/GPU process launched; BFCL terminal evidence and actual registration remain prerequisites; 1.7B skill competence, real determinism, CLEAR residual behavior, measured costs and all scientific endpoints remain unmeasured. Leave the draft's registered constants untouched; any proposed science correction belongs in the handoff for review, not a silent edit.
