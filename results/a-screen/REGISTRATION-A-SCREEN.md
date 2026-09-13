# Registration: six-family candidate-A screen (counterfactual LoRA on current-rule execution)

Registered 2026-09-13 before any project, training pair, adapter or generation exists for
this program. It adopts the minimum registration Astra stated in round 8
(`results/reviews/2026-09-13-direction-adversarial-rev8-astra.md`, items 1–8) without adding
arms, models, benchmarks or review stages. Astra's forecast for this candidate is ~30%
(range 15–45%) artifact success; the owner's bar is 25% (`plan/LEDGER.md` 07:40Z). This is a
SCREEN under a development gate; passing it establishes no efficacy claim. The rev 5
pre-check (`results/contracts/REGISTRATION-PRECHECK.md`) is sealed and INELIGIBLE; nothing
below amends it.

## 1. Domain and lineage (frozen)

- Families. Targets T = {naming contract, validation entry, missing-record policy}; supports
  S = {return shape, error surface, logging policy}. Dependency choice and immutability are
  excluded. Exactly one target family changes (or is stable) per session; exactly one
  support family is stated once and never changes.
- Family selection used the pre-check's exploratory per-family summaries (J/8: return shape
  6, error surface 5, logging 4, validation 3, missing-record 2, naming 2) and the dev-set
  precedent probe. That use is recorded here; those 48 tasks and their prompts/responses are
  excluded from every fitting set and are not reused as screen or confirmation projects.
- Three disjoint project pools with disjoint solution constructions: TRAIN (authored for the
  576 pairs), SCREEN (48 projects, one session each, this document), CONFIRM (reserved,
  authored only if the gate passes, disjoint from both). Disjointness is by project name,
  package layout, function names and test bodies; a hash list per pool is committed before
  the pool is used.
- Data lineage: everything is authored 2026-09-13+ for this program; fit-on = TRAIN only;
  evaluated-on = SCREEN only; nothing from `data/bench/`, MemoryCode, the dev16 tasks or the
  32 pre-check tasks enters any pool. No prompt, threshold or checkpoint is tuned on SCREEN.

## 2. Sessions: N = 48, one per project (frozen manifest)

`results/a-screen/manifest.json` (sha256 `73d1cded79c5f74f`, produced by
`scripts/a_screen_manifest.py`, deterministic): 3×3 target×support grid, 6 sessions per
diagonal cell and 5 per off-diagonal cell; every target family and every support family has
16 sessions; lifecycle classes stable / replacement / scoped exception / reinstatement have
12 sessions each, each class covering all nine cells. Contract-state variants of one
repository are never separate observations. Projects are authored to the manifest slots
(S01–S48) and frozen by hash before generation.

## 3. Arms (three, same everything except the adapter)

| arm | adapter | training data |
|---|---|---|
| `off` | none (adapter bypassed) | — |
| `sft` | LoRA trained with completion cross-entropy only | every positive history/solution used by `cf`: both counterfactual directions and the irrelevant-history variants |
| `cf` | LoRA trained with cross-entropy + 0.1·L_DPO | the same positives plus the stale-alternative preference term |

Same frozen Qwen3-4B trunk (`deploy/stencil_focus/build/hub-4b` weights), same tokenizer,
chat template with thinking disabled, same session memory and packing policy (§5), same
rendering, generation limits and initial repositories. No teacher, scorer or private test
enters inference.

## 4. Training intervention (frozen before the screen)

- Adapter: LoRA rank 16, alpha 32, dropout 0, on all linear projections of attention and MLP;
  AdamW lr 1e-4, weight decay 0, gradient clipping 1.0, seed 0, bf16 trunk frozen.
- `cf` loss: mean cross-entropy over completion tokens of the current-rule gold + 0.1·L_DPO
  with β = 0.1, reference = the frozen trunk (reference log-probs precomputed once and
  counted in the allocation). Chosen = gold executing the CURRENT rule; rejected = the stale
  alternative, which must fail an applicable contract test and must be the executable gold of
  the other rule state (so both directions have executable gold).
- Pairs: 576 authored counterfactual pairs, 16 per (target×support pairing × lifecycle
  class) cell = 36 cells; each history has an irrelevant-history variant (same code, the
  intervening message is contract-irrelevant, gold = the unchanged rule). The convention
  shown by the existing code is counterbalanced: in half of the pairs per cell the in-file
  precedent matches the stale rule, in half it matches the current rule.
- Allocation: a fixed 4-hour wall-clock allocation per adapter on the GB10 under the sharing
  protocol, including reference scoring for `cf`; the FINAL completed optimizer step is the
  adapter (no checkpoint selection, no early stopping on any evaluation). `sft` may make more
  passes over the same positives inside its equal allocation. Actual token exposure, steps
  and GPU-seconds are reported per adapter.
- Every pair's gold and stale alternative are executed against the pair's tests before the
  pool is frozen (self-check identical in kind to `tests/test_contracts.py`).

## 5. Stateful session protocol (frozen)

- Each session = a frozen 16-turn prefix (user/assistant turns of ordinary work on the
  project, prior assistant turns authored, not generated) + two LIVE coding requests. The
  arm's first patch is applied to the arm's own copy of the repository (patch = the returned
  target file replacing the target; failure to parse or apply is a failure); the second
  request is rendered from that resulting state.
- The lifecycle event (replacement, scoped exception or reinstatement of the target contract)
  is a user message placed between the two live requests; stable sessions receive a
  contract-irrelevant message there instead. Reinstatement sessions carry the earlier
  replacement inside the prefix.
- Memory/packing policy, common to all arms: prompt = system line + the newest whole turns
  that fit in P = 4,096 − 1,536 = 2,560 tokens, dropped from the oldest turn boundary first
  (compaction). The prefix is authored long enough that compaction drops at least one turn
  before live request 1 and at least one more before live request 2 (exercised in the prefix
  and between requests). No summary, no register and no externally computed "current rule"
  is inserted; whichever historical instruction messages survive the window are exactly what
  reaches the model, and the record lists them per request by turn index. The contract
  statement, the lifecycle message and the support-family statement must survive the window
  at both live requests (checked before generation; a violation is a construction defect
  fixed before the freeze, never after).
- This is a limited history-replay screen; it does not test autonomous long-session
  reliability, and any card will say so.

## 6. Outcome (one binary per session)

- J = 1 iff at BOTH live checkpoints the task's functional tests, the protected regression
  tests (existing behaviour that must not break) and ALL applicable contract tests pass in
  the sandbox (`stencil.contracts.run_tests`, scorer runs functional and contract suites
  independently since `src/stencil/contracts.py` sha256 `de0012b279e42c1a`). Function-only
  success = functional + regression at both checkpoints. No partial credit.
- Decoding: one greedy generation per request, thinking disabled, ≤ 1,536 new tokens, prompt
  + reserved output ≤ 4,096. Parse failure, patch-application failure, truncation at the cap,
  timeout (300 s per generation) and abandonment (empty or non-code reply) count as J = 0
  and function-only = 0 for that session. Private tests stay private (never rendered).

## 7. Development gate (frozen; count rules decide, statistics are reported)

`cf` passes iff ALL hold:
1. net J wins over `off` ≥ 5 (wins − losses across the 48 paired sessions);
2. net J wins over `sft` ≥ 3;
3. no observed net function-only decline against either comparator (wins − losses ≥ 0);
4. within the 36 changing-rule sessions, net J advantage over `off` > 0 and over `sft` > 0;
5. within replacement, scoped exception and reinstatement separately (12 each), net J
   difference vs each comparator ≥ 0.

Reported for every contrast: paired wins/losses/ties, two-sided exact McNemar p, and the
conservative 95% paired interval (separate 97.5% Clopper-Pearson bounds on b/N and c/N,
union bound). Power, stated (Astra round 8): at a true 10-point effect N = 48 has roughly
14–23% power under McNemar; the gate is a development screen, not a demonstration. A failed
gate stops this configuration; it does not show equivalence. A passed gate authorises only
the CONFIRM registration (separate document; N and horizon to be set there from the
screen's measured wins, with its own compute ceiling).

## 8. Compute ceiling (frozen): 16 GPU-hours for the whole screen

Includes the maximum-context timing pilot (4 sessions × 3 arms at the longest prompts),
both 4-hour trainings, `cf` reference scoring, model loading, and 3 × 48 × 2 = 288
evaluation generations, with the protocol's 1.5 contention factor applied to the pilot's
seconds/request. Pre-check average was 18.8 s/request (short prompts): 288 × 18.8 × 1.5 ≈
2.3 h is an extrapolation, not a measurement. If the pilot-derived total exceeds 16 GPU-h
the screen is recorded COST-INELIGIBLE; if a launched run exhausts its ceiling it is recorded
INCOMPLETE. N is not reduced, failures are not dropped, and no checkpoint is selected to
rescue it. Runs go through `tools/gpu_reserve.sh` with `STENCIL_GPU_SHARE=1`, chunks ≤ 50
min, the peer notified before any run > 30 min.

## 9. Records

Per request, written as it completes (resumable jsonl): session, arm, request index, full
prompt, surviving turn indices, output, repository hash before/after, rule-state
annotation, functional / regression / contract outcomes with messages, seconds, prompt and
generated tokens, terminal reason. Per adapter: steps, tokens, GPU-seconds, final loss.
Per-pool hash lists. `RESULTS.md` carries the gate table, the per-class table, the timing
and the verdict string from §7.

## 10. Known defects of the pre-check set (not carried forward)

Astra round 8 found in `contract_projects_reg.py`: the auth logging test covers rotation only
while the rule covers issuing too and accepts any matching warning rather than exactly one;
the storage-validation gold keeps validation in the existing public function. The sealed
pre-check result is preserved as reported; those projects are not reused. SCREEN and TRAIN
projects must satisfy: every contract test covers every operation the contract wording
names; count-sensitive checks assert exact counts; migration of existing operations is
either tested or explicitly grandfathered in the contract text.

## 11. Process

Implementation review (Astra, one round) on the frozen pools, training code and session
harness before the training launch; result audit (Astra, one round) after `RESULTS.md`.
Nothing else is added. Card wording for the existing 4B package follows Astra's round-8
paragraph (narrow factual negative from the pre-check) and is applied in the same commit
series as this screen's RESULTS.
