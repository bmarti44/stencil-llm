# Brief: bfcl-evict-v2 — rework the BFCL V3 multi-turn harness for LEG A (protected prefix, pre-query eviction, selector v2 over user + tool spans, same-role-pool control)

## Objective
Governing text: LEDGER-PLAN.md "SELECTOR v2 — POST-DEVELOPMENT EVALUATION, LEG A" (appended after review; if it is
absent when you start, build to the draft at the same heading in this brief's companion note in WORKLOG.md and say
so). Rework scripts/bfcl_mt.py + src/stencil/bfcl.py (existing harness: BFCL v1.3 vendored corpus, cohorts.json
dev 32 / sealed 64, Qwen3 tool template, executors, checkers — keep all of that):
1. Protected prefix in EVERY arm: system prompt + <tools> schema block + 4 sink columns never evicted (the old code
   evicts from column 0 — fable's CRITICAL). Eviction at each user turn t >= 2 when the cache exceeds K = 8192:
   evictable = after the prefix and before the current user turn; keep = the arm's pins; eviction BEFORE the current
   turn is prefilled — reuse the two-stage prefill helper from src/stencil/qwen3.py (prefill_with_eviction) and the
   pre-query ordering of scripts/multiif_evict.py. Record per turn: evicted (bool), columns before/after, pinned
   columns, evictable size.
2. Selector v2 over prior USER turns AND prior TOOL-output messages: sentences (registered splitter from
   scripts/clf_probe_check.py / src/stencil/selector_v2.py) for user text; tool output split on newlines (cap 40
   lines per message, longest first if more); score WITHOUT context, role "user"/"tool", keep iff P(rule)+P(fact)
   >= 0.5; budget B = 25% of evictable columns filled by probability then recency; the registered artifact
   data/classifier/model/ft (assert sha256 against results/quick-checks/ft_final2_s0_sha256.txt). Scores computed
   once per turn on CPU in-process (transformers is in the uv env).
3. Arms (identical context ids per turn): base | clf_pinned | clf_pinned_echo | clf_control (exact-column control
   from the SAME role pool as the pins, user and tool columns in the same proportion, built after the echo clamp) |
   role_pinned (all prior user turns, nothing from tool output, recency-clipped to the classifier's column count) |
   full (no eviction). Echo: ledger.text_ledger_context of the kept spans before the current user turn; tool lines
   echoed verbatim with a "tool:" marker. Replace the old --arm flag with running all six arms per case (records
   keyed by arm) — the per-case record stays atomic and resumable.
4. Summary: per category and for the PRIMARY cohort (long_context): final pass per arm, per-turn pass, tool-call
   validity, echo-copy rate, columns; contrasts A1 (clf_pinned_echo − clf_control), A2 (clf_pinned_echo −
   role_pinned), A3 (clf_pinned_echo − base vs 0.5 x (full − base)), one-sided cluster-robust by case
   (src/stencil/stats.py), Holm over three; safety integer clause per arm vs full.
5. Preflight subcommand on the dev slice (32 cases): base competence (multi-turn pass; floor 15%), BASE-vs-BASE
   bitwise determinism on 4 cases, selector coverage (fraction of spans kept, budget used), seconds/case and the
   projected sealed-cohort cost. `--split sealed` stays guarded by STENCIL_SEALED_RUN=1 and is NOT to be run.
NEVER read data/bench/ifeval_input_data.jsonl. Never modify data/bench/*. No fitting on BFCL.

## Allowlist
See bfcl-evict-v2.allow.

## Tests first (TDD, rule 1)
CPU, no model: protected-prefix + evictable range on a templated toy with a <tools> block; two-stage ordering with a
stub trunk; selector over user + tool spans with a stub scorer; same-role-pool control proportions; budget fill order;
record schema dry-assert; summary from synthetic records; sealed guard still refuses. RED first. Run ONLY
tests/test_bfcl.py and your new test file(s). DO NOT run the full suite.

## GPU policy
The GPU is BUSY with the registered Multi-IF 909 run for ~1 day: do NOT launch any model process; mark GPU smoke
and the preflight as deferred with the exact commands in WORKLOG. Never wait on a lock; never signal any process.

## Acceptance
CPU tests green; ruff clean; commit EARLY and often; deferred commands recorded.

## Ledger handoff
Append to WORKLOG.md: what changed (file:line), the tool-output splitting rule, the same-role-pool control algorithm,
ambiguities and choices, and the deferred preflight command.
