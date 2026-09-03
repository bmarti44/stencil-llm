# Brief: multiif-eviction-harness — Multi-IF 909 post-development evaluation of the spec-v2 classifier selector with a REAL eviction harness

## Objective
Registered text: LEDGER-PLAN.md "SELECTOR v2 — POST-DEVELOPMENT EVALUATION, LEG B" (read it first; it governs; it will
be appended before you are launched — if absent, stop and say so). Background: results/quick-checks/README.md items
19-22 and reviews results/check22-review-*.md. Fable's check-16 review (results/check16-review-fable.md) found that
scripts/ledger_eval.py's text_ledger runner NEVER evicts — it measures echo-on-full-context. Build the smallest
eviction harness for Multi-IF (data/bench/multiif_en.jsonl, READ-ONLY, evaluation only) that reproduces the H1'
mechanism at scale:
1. scripts/multiif_evict.py: for each of the 909 conversations, generate turns 1..T-1 with the base 1.7B trunk
   (greedy, non-thinking template, max_new 512, deadline 300 s — reuse scripts/ledger_kv_probe.py run_arm plumbing),
   then at the last turn run the registered arms on the SAME context ids:
   full | evicted (drop the evictable range: everything before the current user turn except the protected prefix =
   system prompt if any + first 4 columns) | clf_pinned (classifier-selected spans pinned via KVCache.evict keep=) |
   clf_pinned_echo (pins + echo via ledger.text_ledger_context, exactly as H1') | clf_control (exact-column control
   via matched_control_spans, computed AFTER the echo clamp) | role_pinned (all prior user turns, budget-clipped by
   recency to the classifier's column count — the parameter-free comparator).
   Selector: sentences of prior user turns (splitter = the one in results/quick-checks/clf_score_sessions.py:
   split_sentences), scored WITHOUT context by the fine-tuned classifier at data/classifier/model/ft (FINAL seed-0
   run; encoder + head.pt; record sha256 of every file in meta), threshold 0.5, role "user". Scores are computed
   ONCE per conversation on CPU before the arms (system python3 has transformers; add `transformers` to the uv env
   via `uv add transformers` so the harness runs in one process — verify `uv run python -c "import transformers"`).
2. Scoring: vendored Multi-IF/IFEval checkers as ledger_eval.py uses them (score_row_constraints or the equivalent);
   per turn-3 constraint pass, aged constraints (introduced in turns 1-2) reported separately; ROUND 7 safety table
   per arm (timeouts, truncation, degenerate, invalid) with the integer-count clause; quoting flag on echo arms.
3. Records: atomic per-conversation JSON from the first conversation (fields: key, context ids, evict range,
   selected spans + scores, pinned cols per arm, control spans, per-arm text/scores/safety, seconds); resumable;
   never delete. Summary: paired-by-conversation pass rates, cluster-robust LB for clf_pinned_echo − clf_control and
   clf_pinned_echo − full and clf_pinned − role_pinned (src/stencil/stats.py), Holm over the registered contrasts.
4. Preflight (registered): run `--limit 20` first and report seconds/conversation; the full 909 only if projected
   ≤ 12 GPU-h; commit the preflight records before continuing.
NEVER read data/bench/ifeval_input_data.jsonl. Never modify data/bench/*. No fitting of anything on Multi-IF.

## Allowlist
See multiif-eviction-harness.allow.

## Tests first (TDD, rule 1)
CPU, no model: evictable-range + protected-prefix computation on a templated toy context; selector scoring path on
3 sentences with a stub classifier; control built post-clamp equals pinned columns; record schema dry-assert;
summary from synthetic records; resume. RED first. Run ONLY tests/test_multiif_evict.py + tests/test_ledger.py.
DO NOT run the full suite.

## GPU policy
Only when `nvidia-smi --query-compute-apps=pid --format=csv,noheader` is empty; re-check later if busy; never wait
on a lock; never signal any process; foreground only. Preflight `--limit 20` only; the 909 run is the orchestrator's.

## Acceptance
Tests green; ruff clean; preflight records + timing committed (`git add -f`); commit EARLY and often.

## Ledger handoff
Append to WORKLOG.md: timing, preflight arm table, ambiguities and choices, any place the Multi-IF checker
semantics or the template were unclear.
