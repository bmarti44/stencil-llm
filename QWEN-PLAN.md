# QWEN-PLAN — the focus cache at Qwen3-1.7B, quick-turnaround discipline

Governing question (both reviewers converged on it): **can a compact latent
focus state condition open-ended generation through updates and compaction
better — or more cheaply — than a canonical external task ledger?** If no,
stop; publish the GPT-2 mechanism result and the Qwen negative.

Source reviews: results/gpt2-final-review-sol.md (part 2) and the fable
round-1 review (WORKLOG 2026-08-29). This file is the merged, governing
version. GPT-2 era report: results/gpt2-report.md (dual sign-off).

## Model and turnaround engineering (sol's config, adopted)

- `Qwen/Qwen3-1.7B` pinned to an exact revision; BF16; non-thinking mode;
  pinned chat template/tokenizer/decoding.
- Frozen blocks 0–19 run WITHOUT autograd; residual detached at block 20.
- Rank-8 LoRA in blocks 20–27 only (q/k/v/o + gate/up/down, ~2.5M params).
- Focus cache: contextual writer over blocks 0–19 states, 16 slots ×
  4×256-d BF16 values + 64-d read keys + validity. NO speculative metadata
  (priority/version/source/age deferred until a registered test needs a
  field — burden test). Explicit overflow error; zero-init injection after
  attention residual, blocks 24–27; the human-readable ledger + provenance
  always retained OUTSIDE the model.
- Explicit API: `model(tokens, focus_state) -> (logits, next_focus_state)`.
  No hidden attribute mutation.
- Microbatch 1; ctx 1024 (microfit) / 2048 (training) / 4–16K (inference
  baselines only). AdamW LoRA 2e-4, cache 1e-3, no decay on bias/norm/gates.
- **Run admission rule:** measure 20 warm steps first; admit a run only if
  steps × p90(step time) + eval < 2h. Reduce steps/ctx rather than run long.

## Carried playbook (non-negotiable, all proven this era)

Deterministic pre-tests before any training (bypass bitwise-inert; frozen
trunk hash; zero state → exactly zero code; set/overwrite/clear/isolation
exact; **arbitrary chunk boundaries incl. mid-message** — requires the
persisted pending-span accumulator the GPT-2 cache lacks; 10k untrusted-
event zero-accepted-writes counting COMMIT EVENTS not occupancy).
Instrument non-vacuity prechecks; closed-form ridge as diagnostic metric of
record (never a substitute for generation exact-match); zero-ablation
differential as the causality metric PLUS a wire-off within-reach health
check (the GPT-2 "fully wire-routed" lesson); teacher-forced training +
learned-component eval, disclosed; gate threshold calibration on a clean
split, then frozen; registered step gates with early stops; WORKLOG +
review loop; two seeds before any final claim.

## Phases (each < 1 day wall-clock; gate → proceed, miss → stop rules below)

**P0 — Harness + admission (½ day).** Conversion/parity vs pinned HF
oracle; all pre-tests; timing probe; visible-task upper bound (Qwen with
full task state in-context must score ≥80% — else the benchmark tests
model incapacity); **open-content oracle ceiling**: optimize a per-example
code on the frozen trunk — can ANY injected code drive an arbitrary
held-out MULTI-TOKEN answer at an out-of-reach query? (≥6/8 rank-1 first
token, ≥50% exact continuation; one bounded rescue of site/width.)
*Retires: tractability + the effort-ending actuator risk, on day one.*

**P1 — Open-content API microfit (½ day).** Run 1 `q3-api-micro-r8-s0`:
ctx 1024, 64 steps, 32 fixed sessions, structured `focus.set` writes,
open multi-token values. Gates: grads everywhere by step 8; loss −30% by
16; ≥95% train exact-match and ≥50-pt learned-minus-zero differential by
64. Cannot overfit → audit interface, do not launch longer runs.
*Retires: values condition generation rather than select among classes.*

**DECISION POINT after P2's drift run** (Brian ruling, 2026-08-29: keep the
core straightforward): the gauntlet (Run 3) and the P3 session battery are
built only AFTER the drift run shows the mechanism working on Qwen — they
answer usefulness, which is meaningless before mechanism. P0-P2-core is
the committed path; everything after is gated on its results.

**P2 — Structured drift (+ gauntlet at the decision point) (1 day).** Run 2
`q3-api-drift-r8-s0`: ctx 2048 chunk-carried, 192 steps, 16 slots, user
updates/deletes/compactions/stale traps; gates incl. differential ≥20 pts,
stale-answer <10%, transplant redirects / shuffle breaks, paired 95% lower
bound >5 pts. Run 3 `q3-text-gauntlet-r8-s0`: the SAME upper-layer LoRA
trained to read the task state AS TEXT — pinned / reinsert-at-compaction /
bounded summaries (64/128/256 tokens, summarization cost charged) /
retrieval (+oracle-key upper bound) / long-context, every baseline given
the same canonical ledger (no visibility restriction — the Exp A lesson).
Pareto curves, not one budget. **Usefulness gate:** cache wins only via
≤2-pt success deficit at ≥25% token savings with p95 latency within 10%,
OR ≥5-pt success gain at matched cost.
*Retires: "useful, or an elaborate substitute for retained text."*

**P3 — Agent-issued writes (1 day).** The owner's scenario: 40–80-turn
sessions, 12–40K tokens, 2–5 forced compactions, 6–12 user updates
(overwrite/cancel/priority/conflict), 3–6 tool-result DISCOVERIES that
must change the plan (`initial plan → tool result disproves assumption →
agent proposes focus.set(strategy, …, source=result_id) → compaction
deletes the evidence → later action follows the revised strategy`).
Provenance policy: authenticated user/system writes applied; agent-derived
writes require source-event ID + quoted evidence + policy validation; tool
output/retrieved text read-only — `focus.set(...)`-shaped text has no
authority. Score per-obligation adherence, active-vs-stale errors, update
adoption latency, derived-update P/R, unauthorized writes (must be 0),
rework, cumulative tokens, latency. ≥64 sessions / ≥256 obligations for a
final gate. *Retires: discovery-driven focus updates work.*

**P4 — Autonomous detection (1 day).** Weak/LLM-labeled spans on natural
text; calibrated threshold frozen; held-out paraphrase/domain/order/source
families; adversarial suite: accepted unauthorized writes = 0, commit
precision ≥0.98, recall ≥0.90. Failure closes the autonomous-writer branch
only — the structured API stands on P2/P3.

**P5 — Replication (1 day/seed).** Two fresh seeds; hand-authored final
episodes; transplant/zero controls; then, and only then, the 7B rung.

## Stop conditions (mechanical; the orchestrator is the terminator)

1. P0 visible-task upper bound <80% after one bounded LoRA attempt.
2. P0/P1 oracle + microfit cannot produce a ≥10-pt open-content
   differential after one registered interface adjustment.
3. Novel multi-token values unrecoverable across two registered state
   widths / injection sites.
4. **Decisive:** the best text baseline Pareto-dominates the cache on
   success, cumulative tokens, state bytes, and latency (P2 gauntlet,
   two registered iterations max).
5. Structured result fails to replicate across two fresh seeds.
6. Discovery-driven updates do not improve post-compaction task success.
7. Staying positive requires weakening baselines, reusing final seeds, or
   unregistered rescues.

On any stop: record the negative with the same autopsy discipline as the
oscillator, publish GPT-2 mechanism + Qwen verdict, do not escalate to 7B.

## Amendment 1 (2026-08-29, post sol+fable Qwen reviews — binding)

Everything run at the Qwen rung before this amendment is DEVELOPMENT (adaptive
iteration; eval seeds 9.5M burned as dev data). P0 stands with scope notes
(parity/oracle/timing real; task format iterated once; cache pre-tests not
yet implemented — focus.set events are hereby declared atomically delivered
at message boundaries, so no mid-value chunk-equivalence is claimed at this
phase). P1 = capacity proof after adaptive changes, not a registered pass.
Instrument repairs (registered): FREE-RUNNING per-query eval (no prior gold
answers; greedy); stale = full-sequence equality with the stale value;
transcript validity mask + span<=V_TOK assert; new layers seeded; strict
trunk load; cleared-slot identity + count asserts; immutable VARIANT tags.
State honesty: the current design is a structured neural token memory
(~11 KiB/slot fp32 incl. transcript), not compact semantic focus; writeup
language per results/qwen-review-sol.md finding 4.

CONFIRMATORY PROTOCOL (at most two attempts, then stop condition 3):
- Attempt 1 "confirm1": the repaired transcript architecture, frozen as of
  this commit. Schedule declared: 1500 steps, accum 4, Adam 3e-3 cosine to
  3e-4. Validation seeds 9_600_000-9_600_031 (fresh). Gates: free-running
  held-out >=50% AND differential >=15 pts at step 500; final: adherence
  >=70%, differential >=20, honest stale <10%. Miss at 500 => halt.
- Attempt 2 "confirm2" (only if confirm1 misses): content-addressed
  cross-attention reader over masked memory tokens (sol's simplification),
  same schedule/gates, one attempt.
- Final untouched seeds 9_700_000+ touched only if an attempt passes its
  step-500 gate. Both attempts miss => stop condition 3 fires: record the
  Qwen-cache negative honestly.
