# Brief: evict-before-query — apply KV eviction BEFORE the current turn is prefilled (harness + probe)

## Objective
Sol's harness review (results/harness-review-sol.md, EVICT-1 CRITICAL) and fable's (results/harness-review-fable.md,
E1): scripts/multiif_evict.py and scripts/ledger_kv_probe.py prefill the WHOLE context and only then call
KVCache.evict, so the current user turn's K/V (and the first generated token's logits) were computed with
full-history attention — the "evicted" arm is not cleanly evicted. Fix the ordering in both, minimally:
1. Split the prefill: (a) prefill history ids = everything up to and including the last assistant <|im_end|>\n
   before the current user turn (for the echo arms this is the same history; the echo text lives inside the current
   user turn, so it is prefilled in step (c)); (b) apply the arm's eviction: KVCache.evict(lo, hi, keep=pins) on the
   history cache — the evictable range and protected prefix as registered; (c) prefill the current user turn +
   opener (the same ids as before, positions continuing — `length` is not reduced by evict, verify); (d) generate.
   The full arm skips (b). Column counts, keep spans, control spans, and echo construction stay as they are.
2. Assert in code that the current-turn ids are NOT in the cache before step (c) (a test with a stub trunk), and
   that for the full arm the two-stage prefill produces logits bitwise-equal to the one-shot prefill (GPU test,
   runs only when the GPU is idle; otherwise mark skipped with a reason).
3. Meta: record "eviction_timing": "pre-query" in meta.json and refuse to resume into a directory whose meta says
   otherwise. Do not touch results/qwen/multiif-evict-909 or the preflight directory (invalid-ordering records are
   kept). New default out dir: multiif-evict-909-prequery.
4. Probe re-validation: add `--eviction-timing pre-query|post-prefill` to scripts/ledger_kv_probe.py (default
   pre-query) and to the quick-check probe path used by results/quick-checks/clf_probe_check.py (copy it into
   scripts/clf_probe_check.py so it is under test, reading scores from a --scores file); then, ONLY if the GPU is
   idle, run the 20-session probe with the FINAL selector scores (results/quick-checks/clf_scores_final_s0.json
   if present, else regenerate with results/quick-checks/clf_score_sessions_ft.py on CPU) under pre-query eviction
   and report full / evicted / clf_pinned / clf_pinned_echo / clf_control totals next to the post-prefill numbers
   (33 / 46 / 17; full 44; evicted 14). If the GPU is busy, do everything else and say the probe was not run.
NEVER read data/bench/ifeval_input_data.jsonl. Never modify data/bench/*. No fitting on any benchmark.

## Allowlist
See evict-before-query.allow.

## Tests first (TDD, rule 1)
CPU: two-stage prefill ordering with a stub trunk (current-turn ids absent before eviction; positions continue);
meta refuses resume across timings; the probe flag round-trips. RED first. Run ONLY tests/test_multiif_evict.py
tests/test_ledger_kv_probe*.py (if present) and your new tests. DO NOT run the full suite.

## GPU policy
Only when `nvidia-smi --query-compute-apps=pid --format=csv,noheader` is empty; re-check later if busy; never wait
on a lock; never signal any process; foreground only.

## Acceptance
Tests green; ruff clean; bitwise-equality test for the full arm (or skipped-with-reason); commit EARLY.

## Ledger handoff
Append to WORKLOG.md: what changed (file:line), the bitwise test result, the probe re-validation table if run,
and any ambiguity in where the history/current-turn boundary falls.
