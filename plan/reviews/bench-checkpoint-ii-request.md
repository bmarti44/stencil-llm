# BENCH-WAVE checkpoint-ii review request (2026-08-30)

Scope: BENCH-WAVE-PLAN.md v3 section (B0 evidence + freeze list + B3 prereg).
Evidence: results/qwen/b0-identity.json, b0-timing-kv.json, b0-score-parity.json;
tests/test_qwen3_kv.py (5/5), tests/test_bench_runner.py (6/6),
tests/test_ifeval_vendor.py (3/3); src/stencil/bench.py, src/stencil/qwen3.py
(KVCache/bias_hook); data/bench/pins-manifest.json + committed JSONLs;
vendor/ifeval re-vendored bitwise from lm_eval==0.4.8 + 2 patches.

Rulings requested:
- R1: accept worst_err 0.6955 vs frozen 0.5 HF-parity bound (top-1/template/ids
  all PASS; magnitude-vs-existence playbook rule)?
- R2: accept the amended KV acceptance (cached path = deployment semantics for
  ALL arms, bitwise self-determinism; cross-path drift bounds 1.0/2.0 with
  top-1 agreement above bound; capture_hidden 5%/cos 0.999) replacing the
  unpassable registered token-parity criterion?
- R3: accept the per-row random.seed(key) scoring pin (upstream nondeterminism
  on keys 1122/1129), correcting v1.1's false "`random` unused" claim?
- R4: freeze list as written (decoding, MMLU-Redux ok-only 5330 loglikelihood
  protocol, GSM8K full 1319 4-shot demos=train[0:4] + last-number extractor,
  Clopper-Pearson non-inferiority construction, Multi-IF EN 909 exploratory)?
- R5: B3 prereg (family split 6 train / 3 held, generator seed 0, N=2000,
  canonical-response verification discipline, row-matched proxies, B4 arms)?

Grade findings low/medium/high/critical. Open high/critical block progress.
