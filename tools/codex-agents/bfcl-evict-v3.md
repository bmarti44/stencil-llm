# Brief: bfcl-evict-v3 — bring the BFCL harness to LEG A registration v3 (teacher-forced primary, message-index eviction, 128-token tool chunks, echoing control, recency + tool-swap arms, per-turn primary endpoint)

## Objective
Governing text: WORKLOG.md section "LEG A registration v3" (appended just before this brief; it will be copied into
LEDGER-PLAN.md after the reviewers confirm it — build to it verbatim). Reviews that drove it: results/leg-a-review-
{sol,fable}.md (sol: per-arm rollouts vs identical ids, eviction underspecified, controls confounded, tool
segmentation; fable: scorer crash on long tool output, final-pass primary is a null, teacher-forced primary,
message-index split, echo cap, recency_pinned column-matched, safety vacuity, preflight floors/cap). Current code:
scripts/bfcl_mt.py + src/stencil/bfcl.py + src/stencil/selector_v2.py after commit c09549f (bfcl-evict-v2), 18 tests.
Implement, minimally and in this order, each with CPU tests:
1. TEACHER-FORCED primary: before turn t, every arm's context = the ground-truth trajectory (ground-truth calls of
   turns < t executed through the vendored environments, rendered as <tool_call> JSON + <tool_response>); identical
   context ids across arms per turn (assert); each arm generates turn t with its own steps (MAX_STEPS 20, deadline
   300 s); score turn t with multi_turn_checker on ground_truth[:t] + [arm turn t]. FREE-RUNNING secondary for base
   and clf_pinned_echo only (final pass; first-divergence turn recorded). `--mode teacher|free`.
2. Eviction exactly as registered: one decision per user turn t >= 2 at step 0, before the turn-t user message is
   prefilled; trigger prefix+history > K=8192; evictable range located by MESSAGE INDEX (tool responses live inside
   user blocks); protected prefix [0, max(4, system_turn_end)) incl. the output-format contract; cache persists
   across steps; pin overflow rule (drop newest-first, record); two-stage schedule for every arm incl. full;
   per-turn/per-step column records.
3. Selector: user sentences + tool messages split on newlines then chunked into consecutive T=128-token pieces (Qwen3
   tokenizer); scored with truncation="longest_first", max_length 192, assert no candidate > 192 encoder tokens;
   keep iff P >= 0.5; pins filled by (P desc, recency) whole-span until B = 25% of evictable; drop candidates
   containing chat/tool control markers (count them); echo header "Earlier context restated verbatim:", prefixes
   "user:"/"tool:", most probable first, cap E = 1,024 tokens whole spans, inside the turn-t user message, fixed
   across steps.
4. Arms: base | clf_pinned | clf_pinned_echo | clf_control (same-role-pool exact columns, nearest free, post-clamp,
   seed 20260903, disjoint, shortfall filled from the other role and recorded, AND echo of its own spans under the
   same template/cap) | recency_pinned (all prior user columns + most recent tool columns up to the classifier's
   count, echoed identically) | tool_swap_echo (selected user spans kept; selected tool chunks replaced by matched
   tool chunks; pinned + echoed identically) | role_pinned (user columns only, no echo; reported) | full.
5. Summary: primary unit = per-turn pass at evicting turns (teacher-forced), cluster = case, continuity 100/k,
   one-sided cluster-robust, Holm over A1-A3, A4 separate; A3 only if full − base > 0 and excluding turns whose full
   prompt exceeds 40,960 positions (count them); safety integer clause with the vacuity guard and invalid = failed
   parse_tool_calls/call_to_python per turn (replace the rate-based ROUND 7 fields in summarize_records); reported
   fields as registered (echo-copy rate with NO exclusion; verbatim-repeated calls; columns; echo tokens; overflow).
6. Preflight subcommand: (1) 1.7B base competence: overall final pass >= 15% AND per-turn pass on the 40 dev
   long_context turns >= 15%, with the 4B fallback flag; (2) base-vs-base determinism on the first dev id per
   category; (3) feasibility gate: >= 4/8 dev long_context cases pressure-exposed and >= 4 exposed case-turns keep a
   tool chunk; (4) seconds/case + projected sealed cost (cap 30 GPU-h; arm-cut rule); (5) constants + harness sha
   written to meta before anything runs; refuse to run if meta constants differ from the registered ones.
`--split sealed` stays guarded by STENCIL_SEALED_RUN=1 and is NOT to be run. NEVER read
data/bench/ifeval_input_data.jsonl. Never modify data/bench/*. No fitting on BFCL.

## Allowlist
See bfcl-evict-v3.allow.

## Tests first (TDD, rule 1)
CPU, no model: message-index evictable range with tool responses inside user blocks; protected prefix end incl.
the format contract; teacher-forced context identity across arms with a stub trunk; 128-token chunking + the 192
assertion with the real bge tokenizer (CPU); control role quotas/shortfall/echo parity; recency_pinned column
matching; tool_swap replacement; per-turn primary summary from synthetic records incl. the A3 exclusions and the
vacuity guard; constants/meta refusal; sealed guard. RED first. Run ONLY tests/test_bfcl.py tests/test_bfcl_evict_v2.py
and your new test file(s). DO NOT run the full suite.

## GPU policy
The GPU is BUSY (registered Multi-IF 909 run, then queued probes): do NOT launch any model process; record the exact
deferred smoke/preflight commands in WORKLOG. Never wait on a lock; never signal any process.

## Acceptance
CPU tests green; ruff clean; commit EARLY and often; deferred commands recorded.

## Ledger handoff
Append to WORKLOG.md: what changed (file:line), how the teacher-forced context is rendered (exact template), the
message-index split, the control/recency/tool_swap algorithms, ambiguities and choices, deferred commands.
