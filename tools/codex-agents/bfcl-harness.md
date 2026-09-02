# Brief: bfcl-harness — minimal BFCL V3 multi-turn harness for the hand-rolled trunk (Leg A of the publish gate)

## Objective
Registered text: LEDGER-PLAN.md "PUBLISH-GATE BENCHMARKS" Leg A, and results/agentic-bench-synthesis.md. Build the
SMALLEST harness that runs BFCL V3 multi-turn cases through our trunk with three arms, without an HTTP server:
1. Data: add BFCL V3 multi-turn cases as a vendored, hashed corpus under data/bench/bfcl_v3_mt/ (Apache-2.0; record
   upstream commit + sha256 of every file in data/bench/pins-manifest.json under a new key). Include the executable
   function environments the multi-turn categories need (vendor the bfcl_eval package or the minimal subset; document
   the exact upstream path/commit). Categories: base, missing_params, missing_functions, long_context.
2. scripts/bfcl_mt.py: `--split dev|sealed --arm base|ledger|control --trunk 1.7b|4b --max-new 512 --out <dir>`.
   - Cohort construction is DETERMINISTIC and hashed: a 32-case dev slice and a disjoint 64-case sealed cohort,
     stratified 8/16 per category, seed fixed, ids listed in data/bench/bfcl_v3_mt/cohorts.json (hash in manifest).
     The sealed cohort must NOT be run by this brief (dev only); a guard refuses `--split sealed` unless
     STENCIL_SEALED_RUN=1 is set by the orchestrator.
   - Chat/tool protocol: Qwen3 chat template with `<tools>` schema block and `<tool_call>` JSON, non-thinking mode
     (empty <think></think>), greedy, deadline per turn. Parse tool calls, execute against the BFCL environment,
     append tool results as tool-role turns, continue until the case's turn list ends. Reuse existing generation
     plumbing (KVCache, bias_hook, evict/keep) — no model server.
   - Arms: `base` (plain history); `ledger` (automatic finder selects instruction/schema spans from history each
     user turn; KV-pin the selected columns on eviction; echo via ledger.text_ledger_context); `control`
     (random-span echo: same token count, same template, sampled from prior USER turns, same pin budget). Eviction
     policy: identical across arms (registered K = 8192 tokens; long_context cases exceed it natively — record per
     case whether eviction fired).
   - Scoring: BFCL's own executable/state checkers (vendored), all-or-nothing per case plus per-turn results.
   - Per-record fields: case id, category, arm, per-turn responses, tool calls, validity of each call, evicted (bool),
     echo tokens added, echo-copy flag, truncated/timeout per turn, final pass. Atomic per-case records from the
     first case; never delete records; resumable.
   - Summary: paired-by-case pass, LB(ledger − control) and (ledger − base) cluster-robust one-sided (reuse
     src/stencil/stats.py), ROUND 7 safety incl. tool-call validity excess, echo-copy rate, per-category breakdown.
3. Preflight subcommand `--preflight`: on the dev slice, base competence for the selected trunk (report multi-turn
   pass; the registered floor is 15%), finder recall on the 100 labelled spans (labels: instruction sentences in the
   system/user turns and each tool schema — produce the label file deterministically and hash it), and a base-vs-base
   rerun variance check (two seeds of tie-breaking? we are greedy — verify bitwise determinism instead).
Keep it minimal: no async, no server, no vLLM. Prefer ~600 lines total.

## Allowlist
See bfcl-harness.allow.

## Tests first (TDD, rule 1)
CPU-only, no model load: cohort construction determinism + disjointness + hash; tool-call parsing table (valid JSON,
malformed, multiple calls, no call); random-span control token matching; echo-copy flag; summary from synthetic
records; sealed-split guard. RED first. Run ONLY the new test file(s) plus tests/test_ledger.py and tests/test_stats.py
(if present). DO NOT run the full suite.

## GPU policy
Check `nvidia-smi --query-compute-apps=pid --format=csv,noheader`; only if empty, run ONE dev smoke:
`uv run python scripts/bfcl_mt.py --split dev --arm base --trunk 1.7b --max-new 128 --limit 4 --out bfcl-smoke`.
Foreground only; never terminate or signal any process. `.review.lock` is held by your own wrapper: do not wait on
it; commit your allowlisted files when done.

## Acceptance
Targeted tests green; ruff clean on touched files; pins-manifest updated with every vendored file hash; sealed guard
proven by a test; no edits outside the allowlist; commit before finishing.

## Ledger handoff
Append to WORKLOG.md: upstream BFCL commit + files vendored, cohort hashes, RED->GREEN evidence, smoke result (base
pass on 4 dev cases, tool-call validity), and open questions for the orchestrator (especially any place where the
Qwen3 tool template or BFCL checker semantics were ambiguous).
