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
| SCREEN | `results/a-screen/screen-pool.json` | `eb9c5c97e2d42d61` | `e0867688b60e1071` |
| TRAIN | `results/a-screen/train-pool.json` | `b8f504494a281858` | `f6b3d63e941e1d70` |

The TRAIN statement wording and the twelve regression assertions of §14.8 changed session
content. `tests/test_a_screen.py`: **301
passed**. Statistics re-verified independently: `mcnemar_exact` agrees with
`2·Binom(b+c, ½)` lower tail on all 256 discordant-count cells up to 15/15, and both
Clopper-Pearson bounds solve their defining binomial tail equations at 0.0125 per side for
k ∈ {0, 1, 5, 12, 48} at N = 48.

### 14.8 Answering the re-review's own question 3, by mutation audit

The re-review framed the whole issue as "is there any remaining path by which a session can
score J = 1 while the repository is actually wrong". Rather than reason about it, the scorer was
mutation-audited: every dictionary `.get` lookup and every store write-back in BOTH target files
of all 48 slots was broken one at a time in the checkpoint-2 gold, and each mutation had to be
caught by some suite. **149 mutations, 12 undetected.** All 12 were the same class as F7 and all
12 were in PRE-EXISTING operations whose behaviour no regression test pinned:

- S17 `get_student` and S18 `get_station`: declared `-> X | None`, but no test called them with
  an unknown id, so changing `.get(id)` to `[id]` made them raise and still scored J.
- S38 `void`, S39 `close`, S40 `withdraw`, S41 `close`, S42 `requeen`, S43 `cancel`,
  S44 `relocate_item`, S45 `move_singer`, S46 `cancel_ride`, S47 `retire_tool`: each regression
  test asserted the RETURNED record's new state but never re-read the store, so deleting the
  write-back left the operation returning a correct object that was never persisted, and the
  session still scored J.

Each of the twelve now has one added assertion that re-reads through the store's own public
reader (or calls the lookup with an unknown id). The audit re-runs at **149 mutations, 0
undetected**. This is why the SCREEN pool hash moves in amendment 2. The audit script is the
standing check for this question: a new slot or a changed regression test must keep it at zero.

## 15. Amendment 3 (2026-09-13, after the Astra re-review round 3, before any pilot, training or evaluation generation)

Round 3 read **DO NOT LAUNCH**: "It can award J = 1 after an edit deletes unrelated records,
and the summary can still turn a failed gate into a pass." F6, F8, F16 and F17 were confirmed
RESOLVED; six findings were PARTIAL. Every counterexample was reproduced before it was changed.
**No arm, model, outcome unit, gate or ceiling changes.**

### 15.1 Request 2 renders the whole repository (F1, third and final form)

Amendment 2 added request 2's own target to the rendering. That was still not enough: in S03 the
target's record type `Fine` and its `frozen=True` declaration live in `model.py`, so a reply that
assigns in place raises `FrozenInstanceError` while the constraint appears nowhere in the window.
Request 2 now renders the CURRENT content of EVERY file, exactly as request 1 does. This ends the
defect class instead of patching instances of it, and it fits: over all 48 slots the required
messages plus every file need at most **2,383 of the 2,560-token budget** (S08; 177 tokens
spare). The self-check asserts that every file appears in request 2, with an applied reply and
with an unapplied one.

Compaction is unchanged by it, measured over all 48 slots with the shipping tokenizer:

| | min | median | max |
|---|---:|---:|---:|
| prefix turns surviving at request 1 (of 16) | 13 | 14 | 15 |
| prefix turns surviving at request 2, gold first reply | 12 | 13 | 15 |
| prefix turns surviving at request 2, maximum-length first reply | 4 | 8 | 9 |
| packed request-2 tokens, gold first reply | 2,350 | 2,451 | 2,556 |

The superseded request and its reply are evicted at request 2 in **48/48** slots. Round 3's
observation is recorded as a scope limit, not a defect: the rule turns are protected, so the
screen does not test recovery of an evicted rule. §14.6's claim is written accordingly.

### 15.2 The summary can no longer turn a failed gate into a pass (F12)

Two executed counterexamples each flipped **GATE FAILED → GATE PASSED**:

- relabelling CF's S03 `lifecycle` from `scope` to `replacement` moved a session between strata,
  because the strata were read from CF's own records. Strata now come from the **frozen
  manifest**, and any record whose label disagrees with the manifest is refused by name.
- leaving a failed functional suite in place while setting the stored `function_only` flags true
  bypassed gate 3. `function_only` is now **recomputed** from its three suites
  (`functional`, `regression`, `protected_function`) and a disagreement is refused.

Also closed: an identity that is non-empty but incomplete now fails (every field in
`SHARED_IDENTITY` is required), the one shared identity must match the **current** SCREEN freeze
rather than merely being self-consistent, and an empty stratum is reported instead of dividing by
zero (one completed stable session used to raise `ZeroDivisionError` on the changing-rule
subset; gate 4 also cannot pass on an empty subset).

### 15.3 Provenance now establishes the registered comparison (F13, F15)

The model fingerprint hashed JSON below 2 MB in full and everything else by size, so the
11,422,654-byte `tokenizer.json`, the 2,776,833-byte `vocab.json` and all three weight shards
were size-only: different content of the same length fingerprinted identically. `dir_sha` now
hashes every file's **actual bytes** (8.06 GB in 5.9 s, stable across calls; verified that a
one-byte change in the tokenizer, the vocabulary or a weight shard changes the fingerprint and
that restoring the bytes restores it). The adapter's `adapter_config.json` is hashed into the
identity too, and the per-request **deadline** is recorded and must equal the registered 300 s.

The adapter guard no longer accepts a log that merely looks finished. It requires the frozen
TRAIN pool hash, no `--limit` subset, the evaluation trunk, at least one completed optimizer step
**as an integer** (`not steps` had accepted `-1`), at least half the allocation in elapsed
seconds, and every value of the registered recipe: `seed 0`, `lr 1e-4`, `rank 16`, `alpha 32`,
`beta 0.1`, `dpo_weight 0.1`, `accum 8`. Verified against Astra's fabricated log: all eight
deviations plus the 1-second runtime are named in the refusal.

### 15.4 Resume, budget and the trainer (F3, F13)

A complete final record missing only its newline is now **completed** rather than deleted; only
malformed trailing bytes are discarded; all four file shapes were checked. An output file holding
records from another arm or identity is refused **before** any generation rather than producing a
file the summary rejects after the GPU time is spent.

`--budget-min` counts **resident** wall time, not `model.generate` seconds: every record carries
a `resident_s` stamp and a resumed run continues from the largest stamp in the file. The
protocol's five-minute starting margin is applied. In the trainer: one packing path shared with
the harness (`pack_session`), the stop estimate includes the optimizer step as well as the
micro-step, a periodic save cannot consume the allowance reserved for the final save, and
`status` is `"complete"` only when at least one optimizer step completed.

### 15.5 Corrected compute accounting

Round 3's count is adopted. The amended scorer runs **five suites at checkpoint 1 and six at
checkpoint 2**, so the evaluation entails **48 × 3 × 11 = 1,584** suite subprocesses, plus 132
for the pilot's 12 arm-sessions. §14.4's 1,296 is superseded.

| component | hours |
|---|---:|
| two training allocations, CF reference scoring included | 8.0 |
| evaluation generations, 288 × 15 s × 1.5 | 1.8 |
| pilot generations, 24 × 15 s | 0.1 |
| subtotal | **9.9** |
| one permitted training re-run | 4.0 |
| subtotal with the re-run | **13.9** |
| remaining allowance against the 16 GPU-h ceiling | **2.1** |

The 2.1 h remainder must cover model loads, checkpoint writes and all 1,716 suite invocations,
which is **at most 4.41 s per invocation** before any other resident overhead. That is not
asserted here: the registered timing pilot now measures `resident_s`, which includes suite
execution, and §8's ceiling is applied to the pilot's measurement. If the pilot shows the
evaluation cannot fit with the re-run reserve, the re-run reserve is given up first and the
screen runs without it; §8's INCOMPLETE rule is never rescued.

### 15.6 The audit's own question, asked of the fixtures instead of the scorer (F7 class, final)

§14.8 audited the scorer against two mutation classes and closed twelve holes. Round 3's
criticism was that the audit itself was too narrow: "it can award J = 1 after an edit deletes
unrelated records." Three classes were added, all of them things a reply to the registered
request can plausibly write, and all of them leaving the repository wrong:

| # | mutation | what it would mean in a reply |
|---|---|---|
| 1 | `store.get(k)` → `store[k]` | a declared `-> X \| None` lookup starts raising |
| 2 | the write-back line is deleted | the operation returns a correct record that is never persisted |
| 3 | `self._m[k] = v` → `self._m = {k: v}` | the edit **deletes every other record** |
| 4 | `replace(rec, …)` gains `field=<default>` | the update **resets an unrelated attribute** |
| 5 | `rec.with_X(…)` wrapped in `replace(…, field=<default>)` | the same reset where the slot updates through a record helper |

Class 5 exists because round 3's second S01 example updates through `recipe.with_servings(…)`,
which has no `replace(` call site at all, so class 4 generated nothing for it.

At five classes the audit found **82 undetected mutations across 38 of the 48 slots** (61
whole-mapping replacements, 21 attribute resets). Every one was a construction defect rather than
a scorer defect: a fixture that stores exactly ONE record, with every defaulted attribute left at
its default, asserting only the record the operation returned. Such a fixture cannot distinguish
"updated this record" from "replaced the store with this record", and cannot distinguish "kept the
other fields" from "reset them".

All 38 were repaired under a written standard, now AUTHORING.md amendment 2 so a future slot
cannot be added without it. For every `functional_tests` and `regression_tests` suite of both
requests:

1. the fixture stores **at least two records** and the tests operate on one of them;
2. at least one record carries a **non-default** value in each defaulted attribute the operation
   does not itself set;
3. after the operation the suite **reads the other record back through the store's own public
   reader** and asserts the count is unchanged — by the public counter where one exists, else by
   reading every record back **and** asserting `get(<a key never stored>) is None`;
4. every "the other record survived" assertion is preceded by an explicit non-`None` guard, so it
   cannot pass vacuously (AGENTS.md's exact-zero rule applied to record survival).

Class 5 was added while that repair was in flight, so the slots repaired before it existed had
never been audited against it. The **pool-wide** re-run found exactly that residue: **2 undetected
mutations**, `S02 close_ticket` silently clearing `assignee` and `S41 close` silently clearing
`crew` — in both cases a pre-existing close operation that erases a field only the *other*
operation sets, which no single-operation fixture can observe. One regression test each now
assigns two records, closes one, and reads both back. This is recorded rather than smoothed over
because it is the reason the audit is run pool-wide and not per repair.

Final state: **292 mutations, 0 undetected**, and `tests/test_a_screen.py`
**301 passed**, including that both states' gold reaches every suite at both
checkpoints for all 48 slots.

Nothing outside the two fixture fields changed, and that is checked mechanically rather than
asserted. `scripts/a_screen_containment.py` rebuilds each changed slot's `Session` from git and
compares every session and request field except `functional_tests` and `regression_tests`: **39
slots changed, 9 untouched, 0 violations**. It also reports a slot whose file changed without any
fixture body changing, so an edit cannot hide in a helper. Its own non-vacuity was verified by
injecting six edits one at a time: a project file, a request text, a contract suite, a support
suite, and a behaviour-neutral edit inside a gold builder are each reported; an added functional
test and an added regression test are each correctly not.

Three limits are recorded rather than engineered away:

- Requirement 2 is **vacuous** where a slot has nothing unrelated to preserve: S18 stores plain
  dicts with no defaults at all, S27's `Screening` has no defaulted field, and in several slots the
  operation's own field is the only defaulted one. There the NEIGHBOUR record carries the
  non-default value, so classes 3 and 5 are still caught.
- Four seeds are not reachable through the public API at the checkpoint that needs them (S05's
  `renewals` before a freeze, S47's `borrower` before a retire, S01's `tags` and S43's `host` at
  checkpoint 1). Those are seeded through the store's own mapping with `dataclasses.replace` — the
  idiom the pool already used — or pinned in the other request's suite where the operation is
  pre-existing. A fixture that reaches into private state is weaker evidence than one that does
  not, so it is stated.
- S29 has no public price setter until request 2, so its checkpoint-1 fixture writes the
  non-default value into private store state; a second pin using only the public API was added to
  request 2's regression suite, so the mutation is caught without relying on private access.

No existing assertion was weakened or deleted. Where a test's exact assertion pins a single record
(`count() == 1`, an exact audit-log body), the test was left verbatim and a two-record sibling was
added beside it.

One consequence is stated plainly because it cuts against the arm under test as much as for it: a
two-record fixture at checkpoint 2 can fail a session for a defect introduced by the **request-1**
reply that request 1's own suites could not observe. In S02, a request-1 reply that rebuilds the
record (`Ticket(ticket_id=…, title=…, status="closed")`) instead of updating it drops `assignee` —
invisible at checkpoint 1, where no ticket has an assignee, and caught at checkpoint 2 once one
does. That is the intended reading: J requires both checkpoints to pass every suite, the repository
at checkpoint 2 really is wrong in that case, and the protected suites already re-run request 1's
tests there. It applies identically to all three arms.

A sixth class — persisting the record under a different key — was considered and **declined**: a
wrong-key write either destroys the neighbours, which is class 3, or is observationally identical
to the deleted write-back, which is class 2, and no form of it is something a reply plausibly
writes. The audit stays at five classes.

### 15.7 Re-frozen pool and self-checks

| pool | record | sha256 (first 16) | was |
|---|---|---|---|
| SCREEN | `results/a-screen/screen-pool.json` | `4f5d59eb87bb99f8` | `eb9c5c97e2d42d61` |
| TRAIN | `results/a-screen/train-pool.json` | `b8f504494a281858` | unchanged; no TRAIN file was touched |

`uv run pytest -q tests/test_a_screen.py` → **301 passed**.
`uv run python scripts/a_screen_mutate.py` → **292 mutations, 0 undetected**.
`uv run python scripts/a_screen_containment.py` → **0 violations**.
