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
- Three project pools with disjoint NAMES (not disjoint constructions, see §13.3): TRAIN (authored for the
  576 pairs), SCREEN (48 projects, one session each, this document), CONFIRM (reserved,
  authored only if the gate passes, disjoint from both). Disjointness is by project name,
  module path and public class/function name, VERIFIED by `scripts/a_screen_freeze.py`; a hash
  list per pool is committed before the pool is used. Disjoint solution *constructions* are
  NOT claimed and the measured idiom overlap is recorded -- see §13.3 (amendment 1).
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

## 12. Frozen pools (2026-09-13, before any pilot, training or evaluation generation)

| pool | record | sha256 (first 16) | content |
|---|---|---|---|
| SCREEN | `results/a-screen/screen-pool.json` | `c0e623f4942e47af` | 48 hand-authored sessions (`src/stencil/a_screen_pool/s01.py`–`s48.py`), manifest agreement checked, 12 per lifecycle class, 6/5 per cell, no package/module/class/function name shared with TRAIN, the pre-check projects or the development projects |
| TRAIN | `results/a-screen/train-pool.json` | `6a39f66e0510a509` | 576 generated sessions (`src/stencil/a_train_pool.py`), 36 cells × 16, precedent counterbalanced 8/8 per cell, 1,152 (prompt, chosen, rejected) triples, every executable and packing check passes |

Both pools were RE-FROZEN by amendment 1 (§13.7); the hashes in the table above are
superseded by SCREEN `e0867688b60e1071` and TRAIN `f6b3d63e941e1d70`, and the name-disjointness
wording is narrowed by §13.3.

Self-checks: `tests/test_a_screen.py`, 241 passed at the time of this section, 301 after
amendment 1 (48 screen slots and 12 sampled train sessions × 5 checks, plus a packing unit test). Measured smoke: trainer ~6.5 s per `cf`
micro-step and ~1.2 s per reference example; harness ~15 s per request. Astra
implementation review (`results/reviews/2026-09-13-a-screen-implementation-review-astra.md`)
precedes the timing pilot; findings are verified and resolved first (owner, 2026-09-13).

## 13. Amendment 1 (2026-09-13, after the Astra implementation review, before any pilot, training or evaluation generation)

The review read **REJECT for launch** on 15 findings
(`results/reviews/2026-09-13-a-screen-implementation-review-astra.md`): "The scorer can award
false session successes, and permitted first replies can remove every governing rule from
request 2." Every finding was reproduced before it was changed, and the two that did not
reproduce as written are recorded as such. **No arm, model, benchmark, outcome, gate or
ceiling changes.** The screened quantity is unchanged; what changes is that the apparatus now
measures it.

### 13.1 Scoring and protocol (what a session success now requires)

| # | Defect, as verified | Resolution |
|---|---|---|
| F7 | A checkpoint-2 reply could delete request 1's work, or rename a pre-existing public method, and still score J. | Checkpoint 2 adds a **PROTECTED** suite: request 1's functional, contract-under-state-1 and support tests re-run on the checkpoint-2 repository (test names prefixed `protected_`), ANDed with an AST check that every pre-existing public top-level def/class and public method name still exists (`public_api`, `api_preserved`). A session's J now requires all five suites at both checkpoints. |
| F1 | A permitted first reply at the 1,536-token cap could evict every governing rule from request 2's window. | Request 2 always renders the CURRENT content of each changed file, so it is self-contained; the superseded request/reply pair is evicted **before** any prefix turn (`drop_first_order`); `required_indices` (rule turns, lifecycle event, live request) is asserted at run time; the self-check qualifies every session against a synthetic reply at the permitted maximum. |
| F2 | Request 1's history message was re-rendered from the post-reply files, retrospectively rewriting what the model had been shown. | Request 1 renders from the ORIGINAL repository (`files0`). |
| F8 | The return-shape wording in three slots collided with protected behaviour. | S01/S02/S33 wording exempts counts and `None` lookups. |

### 13.2 Pool checkers (F9, mutation-verified)

Both claims were tested by mutating gold and re-running the suite. **Confirmed:** the
missing-record "returns None and changes nothing" test asserted only `find("zz") is None`, so
an implementation that **cleared the entire store** passed; it now snapshots the complete
record mapping before and after the unknown-id call, and the `raise` state does the same.
**Confirmed with a correction:** Astra located the logging defect in the `silent` state, where
`assert caplog.records == []` is in fact airtight at every level; the defect is in the **`warn`**
state's "active records produce no log record" test, which checked only `levelno >= WARNING`, so
an implementation logging at INFO on every call passed. It now asserts zero captured records.

### 13.3 What the disjointness check establishes (F10)

§1 said "disjoint solution constructions … by project name, package layout, function names and
test bodies". That overstated the verification. **Verified and enforced** by
`scripts/a_screen_freeze.py`: SCREEN package names are unique and shared with no other pool; no
module path is shared with TRAIN; no public class or function name is shared with TRAIN outside a
fixed generic allowlist. **Not claimed:** disjoint constructions. The pools deliberately share a
coding idiom, and the freeze record's `overlap` block now measures it: all 48 slots share at
least one module basename with TRAIN (`__init__.py`, `model.py`, `store.py`, `errors.py`), 0
slots reproduce TRAIN's full four-module shape, 44/48 use the same dataclass-record plus
private-mapping idiom, and 0 normalised test files are identical. The screen therefore tests
generalisation across projects and wording, not across program architecture, and the §6 outcome
is read that way.

### 13.4 Statistics (F11, F12)

`paired()` uses **alpha = 0.025** per component interval, as §7 registered; the zero-discordance
width recomputes to 8.72 points. The summary now loads **both** requests per session, refuses
duplicate records and records from more than one `identity`, refuses a request 2 with no request
1, **recomputes** each session outcome from the stored suites and fails if the stored outcome
disagrees, aggregates diagnostics over both requests, and reads INCOMPLETE against the frozen
48-slot manifest by name.

### 13.5 Allocation chunking and resumption (F13)

The GPU protocol's 50-minute chunk rule exists so an exclusive lock is never held long. This
screen runs under `STENCIL_GPU_SHARE=1`, where a long run slows the peer but never blocks it, so
the rule does not apply and **each 4-hour training allocation runs as one uninterrupted
process**, with the peer session notified at start and end. **There is no resumption.** The
registered quantity is the adapter at the final completed optimizer step of one allocation;
resuming would change the optimizer-state and data-order trajectory and would not be that
quantity. The trainer's periodic saves are crash diagnostics only, marked `final: false`,
`status: "running"`, and the harness now **refuses** any adapter whose `train-log.json` is
missing, non-final, or trained under a different objective than the arm (checked before the
model loads). If an allocation dies before its final save it is recorded INCOMPLETE and its
intermediate checkpoints are never evaluated; **at most one** allocation may be re-run from
scratch (9.9 + 4 = 13.9 h against the 16 GPU-h ceiling), and a second failure ends the screen
INCOMPLETE.

### 13.6 Apparatus hardening (F3, F4, F5, F6, F14, F15)

Per-request persistence with flush and identity-filtered resume (F3); the EOS set is the union
of `GenerationConfig`, `model.config` and `<|im_end|>`, and a late EOS past the deadline still
fails (F4); the determinism import precedes torch in both entrypoints (F5); split training
telemetry and the final update loss are logged (F6); `--longest N` runs the pilot on the longest
packed prompts (F14); both pools are verified against their freeze records before any training or
evaluation, every record carries an `identity` block, and the builders exit non-zero without
writing when any session has a problem (F15). Aligning the TRAIN builder's packing check with
the new eviction order was itself caught by that non-zero exit.

### 13.7 Re-frozen pools and self-checks

| pool | record | sha256 (first 16) | was |
|---|---|---|---|
| SCREEN | `results/a-screen/screen-pool.json` | `e0867688b60e1071` | `c0e623f4942e47af` |
| TRAIN | `results/a-screen/train-pool.json` | `f6b3d63e941e1d70` | `6a39f66e0510a509` |

Session content changed (request rendering, the PROTECTED suite, the tightened checkers), so both
hashes move; the manifest, the 48 slots, the 36 cells and the counterbalance are unchanged.
`tests/test_a_screen.py`: **301 passed** (48 screen slots and 12 sampled TRAIN sessions × 5
checks, plus a packing unit test). Known record gap, not a gate: 37 SCREEN slots omit
`support_state` from `tags`, so the freeze record's support-state balance is partly `?`; the
support suite is scored from the session's own `support_tests` and never looks that tag up.

## 14. Amendment 2 (2026-09-13, after the Astra re-review, before any pilot, training or evaluation generation)

The re-review of amendment 1 read **DO NOT LAUNCH**
(`results/reviews/2026-09-13-a-screen-rereview-astra.md`): "It can award false session
successes, reject correct implementations, and evaluate request 2 without showing the file
being edited." Six findings were PARTIAL and two were new. Every counterexample was reproduced
before it was changed. **No arm, model, outcome unit, gate or ceiling changes.** The screened
quantity is unchanged.

### 14.1 The two critical partials

**F1, request 2 could hide the file it asks the model to rewrite.** The self-contained
rendering showed only the files *changed* since request 1. In the seven slots whose two
requests edit different files (S03, S07, S11, S27, S31, S35, S47, all scoped-exception, so one
whole gate stratum) a maximum-length first reply evicted the request-1 message and left the
request-2 target invisible; the model was asked to replace a file whose content was nowhere in
the window. Request 2 now always renders the current content of its own target as well as every
changed file. A second, independent defect surfaced while fixing it: the packer evicted in
plain index order and dropped an early rule turn while keeping later droppable chatter, even
though S47's required messages fit the budget with 443 tokens to spare. `pack` now takes a
`protect` set, and every call goes through one `pack_session` helper so no call site can omit
it. All 48 slots and the sampled TRAIN sessions pass the maximum-length-reply qualification.

**F7, the PROTECTED group omitted request 1's REGRESSION tests.** Verified false J: in S01,
changing `find` from `self._recipes.get(id)` to `self._recipes[id]` makes a missing record
raise instead of returning `None`, and every checkpoint-2 suite still passed. Request 1's
regression tests are now protected too, and the mutation fails.

### 14.2 Two new findings from the fixes themselves

**F16, contract compliance had leaked into the function-only measurement.** The single
`protected` flag mixed request 1's functional and regression tests with its contract and
support tests, and `function_only` read that flag, so a contract miss depressed the
function-only count that gate 3 compares. The protected group is now scored in two parts:
`protected_function` (request 1's functional and regression tests plus the binding check) and
`protected_contract` (its contract and support tests). `function_only` reads only the former.
Verified: cross-state gold now reports `contract` false with `function_only` true.

**F17, the AST check rejected legitimate implementations.** `api_preserved` compared AST
definition names, so a behaviour-preserving public alias (`count = _count` in the class) failed
while a silent behaviour change passed. It is replaced by a generated test that imports the
module and asserts every pre-existing public name still RESOLVES. Measured before replacing it:
all 156 possible renames of a pre-existing public method across all 48 slots are already caught
by the executable suites once request 1's regression tests are protected, so the shape check
added no detection. The binding check still fails deletion, and now passes an alias.

### 14.3 Records, resume and adapter provenance

The summary refuses, with the line number: a record labelled with another arm, a record with no
`identity`, a second identity inside one arm, a session outside the frozen manifest, a duplicate
record, a request 2 with no request 1, a `scores.all` that disagrees with the individual suites,
a record that passed every suite while its terminal reason was not `applied`, and any record
produced with `--pilot-adapter`. It requires the three arms to share every identity field except
the adapter, and it reads INCOMPLETE instead of dividing by zero when no session is complete.
Each refusal was verified against a synthetic dataset; the unregistered extra session that had
supplied a fifth win and flipped the verdict to GATE PASSED is now rejected.

Resume matches the COMPLETE identity rather than the adapter hash alone (an `off` record matched
on `"none"` even when the pool or the runner had changed), refuses duplicate keys, and repairs a
truncated final line before appending so no record is welded onto invalid JSON. The harness also
binds the model by CONTENT (`hub_sha256`: configs, tokenizer and weight index in full, the
multi-GB shards by name and exact size) because the hub is a mutable directory.

The adapter guard now requires the registered allocation, not merely a final log: the frozen
TRAIN pool hash, no `--limit` subset, a positive number of completed optimizer steps, and the
registered 14,400-second wall clock. `--pilot-adapter` is the one documented opt-out, it prints
what is wrong, it stamps `pilot_adapter: true` into every record's identity, and the summary
refuses any record carrying that stamp. Verified against the existing smoke adapter, which the
guard rejects on all three counts.

### 14.4 Compute and the training allocation

`--budget-min` is now CUMULATIVE across launches (the prior records' seconds are added, so a
relaunch cannot reset the clock) and guards every session start including one whose request 1 is
already saved. A session that has started finishes both requests; the guard exists to stop
STARTING work near the reservation's end. The trainer reserves the longest measured save time so
the final save fits inside the allocation, reports `final_update_loss` from the final update's
own micro-steps (it had averaged the rolling ten-update print window, so two updates at 1 and 9
reported 5), and writes §8's reading of an exhausted reference pass as `status: "incomplete"`,
`final: false`, which the harness then refuses. Astra's accounting stands: 8.0 h training
(reference scoring inside CF's four hours, not added again) + 1.8 h evaluation + 0.1 h pilot =
9.9 h, 13.9 h with the one permitted re-run, against the 16 GPU-h ceiling. The 2.1 h remainder
covers model loads, the 1,296 suite subprocess invocations that run while the model is resident,
and checkpoint writes; §8's INCOMPLETE rule is never rescued.

### 14.5 TRAIN wording (F8)

The initial validation statement said "the module-level `_apply_*` helpers never validate" while
the grandfathered operation validates in its helper (`_apply_schedule` raises `ValueError`). Both
validation statements now say "for every operation added from now on" and "operations already in
the file keep the arrangement they have". The 16 SCREEN validation slots were audited and already
grandfather explicitly, naming the pre-existing operation as the consistent example.

### 14.6 The claim this screen can support

Adopted verbatim from the re-review, and it supersedes any broader reading:

> On these 48 authored two-request sessions, the final CF adapter met the registered
> development thresholds against both the frozen trunk and equal-time SFT, under the registered
> rendering and decoding policy.

It does not establish transfer across program architectures, autonomous long-session
reliability, any particular internal rule-tracking mechanism, or a generally superior training
objective across seeds. One binary outcome per session remains the registered unit; treating
requests or individual tests as independent observations would inflate N. A pass authorises only
the CONFIRM registration. §1's "disjoint solution constructions" phrase is deleted; §13.3's
measured overlap governs.

### 14.7 Re-frozen pools and self-checks

| pool | record | sha256 (first 16) | was |
|---|---|---|---|
| SCREEN | `results/a-screen/screen-pool.json` | `e0867688b60e1071` | unchanged by amendment 2 |
| TRAIN | `results/a-screen/train-pool.json` | `b8f504494a281858` | `f6b3d63e941e1d70` |

Only the TRAIN statement wording changed session content. `tests/test_a_screen.py`: **301
passed**. Statistics re-verified independently: `mcnemar_exact` agrees with
`2·Binom(b+c, ½)` lower tail on all 256 discordant-count cells up to 15/15, and both
Clopper-Pearson bounds solve their defining binomial tail equations at 0.0125 per side for
k ∈ {0, 1, 5, 12, 48} at N = 48.
