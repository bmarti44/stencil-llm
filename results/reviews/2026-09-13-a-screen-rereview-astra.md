**The screen still cannot launch. It can award false session successes, reject correct implementations, and evaluate request 2 without showing the file being edited.**

I reviewed the implementation at `aa2706c7`; the subsequent commit only adds the ledger entry. Both frozen pool hashes reproduce. I used the shipping tokenizer and template, executed targeted authored tests through an in-memory module loader, and checked the statistical calculations against SciPy. The read-only sandbox prevented rerunning the subprocess-based 301-test suite. I did not read `data/bench/` or run GPU work.

The disposition of the original findings is:

| Finding | Status | Assessment |
|---|---|---|
| **F1 — critical** | **PARTIAL** | The cap-length rule-eviction example is fixed. Request 2 now loses unchanged source files, including its own target in seven slots. **Fix:** retain the current target and required repository context before evicting their only source. [a_screen.py:143](/home/bmarti44/stencil-llm/src/stencil/a_screen.py:143) |
| **F2 — high** | **RESOLVED** | Historical request 1 now renders from `files0`. [a_screen.py:175](/home/bmarti44/stencil-llm/src/stencil/a_screen.py:175) |
| **F3 — high** | **PARTIAL** | Request 1 is persisted immediately. Resume checks only arm and adapter-weight hash, silently overwrites duplicate keys, and leaves malformed trailing bytes in place. **Fix:** validate complete identity and unique keys; repair an interrupted final line before appending. [a_screen_run.py:194](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:194), [write:260](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:260) |
| **F4 — high** | **RESOLVED** | Both shipping EOS tokens survive the union, and elapsed-deadline violations fail even with EOS. [a_screen_run.py:146](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:146), [classification:235](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:235) |
| **F5 — high** | **RESOLVED** | Both entrypoints import the determinism module before their other Torch-dependent imports. [runner:40](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:40), [trainer:31](/home/bmarti44/stencil-llm/scripts/a_screen_train.py:31) |
| **F6 — low residual** | **PARTIAL** | Token counters and timing categories improved. `final_update_loss` averages the accumulating ten-update window, because `window` clears only every tenth update. Two updates averaging 1 and 9 report final loss **5**, not 9. **Fix:** calculate final-update loss from that update’s microsteps. [a_screen_train.py:299](/home/bmarti44/stencil-llm/scripts/a_screen_train.py:299) |
| **F7 — critical** | **PARTIAL** | PROTECTED rejects the earlier operation-renaming/deletion examples. It omits request 1’s regression suite, leaving another verified false J. **Fix:** preserve those regression checks too. [a_screen.py:302](/home/bmarti44/stencil-llm/src/stencil/a_screen.py:302) |
| **F8 — high** | **PARTIAL** | The three SCREEN return-shape statements changed. TRAIN’s initial validation statement still says helpers never validate, while `T-val-ret-sta-00` preserves a validating `_apply_schedule`. **Fix:** explicitly grandfather the original operations in the initial TRAIN statements. [statement:747](/home/bmarti44/stencil-llm/src/stencil/a_train_pool.py:747), [gold construction:958](/home/bmarti44/stencil-llm/src/stencil/a_train_pool.py:958) |
| **F9 — high** | **RESOLVED** | Reproduced: clearing the store now fails the missing-record test; INFO logging on an active record now fails the warn-state test. The alleged silent-state hole is **WITHDRAWN**. [snapshot:491](/home/bmarti44/stencil-llm/src/stencil/a_train_pool.py:491), [checks:618](/home/bmarti44/stencil-llm/src/stencil/a_train_pool.py:618), [logging:701](/home/bmarti44/stencil-llm/src/stencil/a_train_pool.py:701) |
| **F10 — medium** | **RESOLVED by narrowing** | §13.3 explicitly withdraws construction disjointness and reports overlap. This supports the narrower interpretation below. The contradictory opening phrase at §1 line 22 should be deleted when editing the registration. [registration:219](/home/bmarti44/stencil-llm/results/a-screen/REGISTRATION-A-SCREEN.md:219) |
| **F11 — high** | **RESOLVED** | Both component intervals now use alpha 0.025. [a_screen_summary.py:93](/home/bmarti44/stencil-llm/scripts/a_screen_summary.py:93) |
| **F12 — high** | **PARTIAL** | Both requests and duplicate identities are handled, but outcomes still trust aggregate score flags; extra sessions, wrong arm labels and missing identities are accepted. **Fix:** validate individual suites, terminal status, arm, identity, metadata and exact manifest membership. [loader:19](/home/bmarti44/stencil-llm/scripts/a_screen_summary.py:19), [manifest handling:123](/home/bmarti44/stencil-llm/scripts/a_screen_summary.py:123) |
| **F13 — high** | **PARTIAL** | Amendment 1 resolves the training-chunk/resumption choice. Cumulative budget enforcement and adapter qualification remain incomplete. **Fix:** account across launches, guard each request and final saves, and verify the registered training allocation/configuration before evaluation. [runner budget:272](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:272), [trainer stop:270](/home/bmarti44/stencil-llm/scripts/a_screen_train.py:270), [adapter guard:104](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:104) |
| **F14 — medium** | **RESOLVED** | `--longest` selects by maximum packed prompt length across both gold-path checkpoints. Current top four: S42, S14, S28, S03. Recompute after fixing F1. [a_screen_run.py:178](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:178) |
| **F15 — medium** | **PARTIAL** | Pool-content verification and failed-builder exits are fixed. Model/tokenizer identity remains a mutable directory path; resume and summary do not enforce the recorded implementation identity. **Fix:** bind frozen model/tokenizer content and require compatible identities throughout. [runner identity:160](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:160), [trainer identity:212](/home/bmarti44/stencil-llm/scripts/a_screen_train.py:212) |

**F1’s worst permitted first reply now preserves rules while hiding necessary code.** I constructed checkpoint-1 gold plus harmless comments totaling **1,535 text tokens**, leaving one token for EOS. Required-message survival passed in all 48 slots.

For S03 specifically, this reply passes every checkpoint-1 suite. Request 2 packs to **2,556 tokens**, retaining indices `[0,8,9,10,11,12,13,14,15,16,19,20]`. It contains neither `class FineLedger`, `self._fines`, `record_fine`, `owed`, nor the `Fine` definition—yet asks the model to replace `loandesk/fines.py`. The renderer includes only changed `desk.py` and says everything else is unchanged from an evicted request. [renderer:143](/home/bmarti44/stencil-llm/src/stencil/a_screen.py:143), [eviction:211](/home/bmarti44/stencil-llm/src/stencil/a_screen.py:211), [S03 target:337](/home/bmarti44/stencil-llm/src/stencil/a_screen_pool/s03.py:337)

Its checkpoint-1 score is **success**. Supplying the oracle gold second reply produces **J=1**; the model must reconstruct unseen source to do that. A first reply alone cannot determine final J.

The same target-file omission affects **S03, S07, S11, S27, S31, S35 and S47**. All are scoped-exception sessions, so this damages a specific gate stratum. Other slots lose supporting module definitions. The runtime assertion checks rule indices, not repository completeness.

**F7 still awards a false J with a 283-token second reply.** Starting from S01 checkpoint-2 gold, replace:

```python
return self._recipes.get(recipe_id)
```

with:

```python
return self._recipes[recipe_id]
```

Now `find(missing)` raises instead of returning `None`. Every checkpoint-2 suite, `api_preserved`, `all`, and `function_only` remains **True**. With successful checkpoint 1, the session receives **J=1**.

The omitted checkpoint-1 regression test immediately rejects this mutation. PROTECTED includes first-request functional, contract and support tests, but omits that regression test. [omission:306](/home/bmarti44/stencil-llm/src/stencil/a_screen.py:306), [missing regression assertion:106](/home/bmarti44/stencil-llm/src/stencil/a_screen_pool/s01.py:106), [weaker checkpoint-2 regression:226](/home/bmarti44/stencil-llm/src/stencil/a_screen_pool/s01.py:226)

The fixes also introduce two distinct scoring defects:

- **F16 — high: function-only now includes contract compliance.** PROTECTED combines functional and contract tests, then feeds `function_only`. I verified an S01 path with functionally correct `recipe_scale` under the wrong naming convention: functional and regression suites pass at both checkpoints, but reported session function-only is **False** because protected naming fails. This can hide a real functional decline by depressing a comparator’s function-only baseline. **Fix:** calculate protected functional/regression preservation separately from protected contract compliance. [a_screen.py:306](/home/bmarti44/stencil-llm/src/stencil/a_screen.py:306), [function-only calculation:326](/home/bmarti44/stencil-llm/src/stencil/a_screen.py:326)

- **F17 — medium: AST definition names reject legitimate public bindings.** In S01, rename the implementation of `count` to `_count` and bind `count = _count` inside the class. Callers retain exactly the same public method and behavior. All executable checkpoint-2 tests pass; `api_preserved` fails because the AST contains no `def count`. Aliases and inherited methods are legitimate implementations. Conversely, a retained AST name establishes no behavioral preservation, as the `find` mutation demonstrates. **Fix:** check actual public bindings and registered behavior instead of requiring a particular definition shape. [public_api:259](/home/bmarti44/stencil-llm/src/stencil/a_screen.py:259), [comparison:281](/home/bmarti44/stencil-llm/src/stencil/a_screen.py:281)

The PROTECTED merge has no test-filename collisions in the current SCREEN or TRAIN pools. TRAIN’s snapshot helper assumes instance dictionaries containing repr-visible records; that matches its fixed authored dataclasses. The original mutations now fail, and neither arm generates TRAIN checker inputs. A general object-state comparison framework would add no useful decision here.

**The new record loader and adapter guard also remain permissive in decision-changing ways.**

I executed these counterexamples:

- The summary accepts `scores.contract=False` alongside `scores.all=True` and reports **J=True**. It recomputes from aggregate flags, not individual suites. [a_screen_summary.py:44](/home/bmarti44/stencil-llm/scripts/a_screen_summary.py:44)
- A synthetic valid 48-session dataset fails gate 1 with four net wins. Adding unregistered **S49** to all three files supplies a fifth win and changes the verdict to **GATE PASSED**. Completeness checks missing IDs but leaves extras in the analysis. [a_screen_summary.py:124](/home/bmarti44/stencil-llm/scripts/a_screen_summary.py:124)
- The loader accepts `arm="cf"` records in `off.jsonl`, and accepts missing identities. With no completed sessions, summary crashes with `ZeroDivisionError` instead of reporting INCOMPLETE. [loader:27](/home/bmarti44/stencil-llm/scripts/a_screen_summary.py:27), [diagnostics:143](/home/bmarti44/stencil-llm/scripts/a_screen_summary.py:143)
- The runner’s exact resume block accepts an `off` record from a different pool and runner version because its adapter hash is still `"none"`. Skipping an unterminated malformed tail and appending leaves the next record attached to invalid JSON. [a_screen_run.py:196](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:196)
- The exact adapter guard accepts a log declaring **180 seconds, eight TRAIN sessions, zero optimizer steps, and an old TRAIN pool**, provided `final=True`, `status="complete"` and the objective matches. It therefore does not establish that the adapter represents the registered allocation. **Fix within F13:** qualify full-screen adapters against registered provenance/configuration and positive completed steps; distinguish the existing timing pilot’s smoke-adapter eligibility. [a_screen_run.py:109](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:109)

These paths are shared across arms, but their effects need not cancel. Output structure changes prompt contents and API-check outcomes; contract failures contaminate function-only counts; incomplete or stale records can affect one arm.

**The narrowed scientific claim is defensible after these apparatus defects are fixed.** If `cf` passes all five gates, the supported statement is:

> On these 48 authored two-request sessions, the final CF adapter met the registered development thresholds against both the frozen trunk and equal-time SFT, under the registered rendering and decoding policy.

The 44/48 construction overlap permits a reading of transfer across projects and wording within a largely shared coding idiom. It does not establish transfer across program architectures, autonomous long-session reliability, a particular internal rule-tracking mechanism, or a generally superior training objective across seeds. Passing authorizes CONFIRM registration; it establishes no efficacy claim. [overlap interpretation:223](/home/bmarti44/stencil-llm/results/a-screen/REGISTRATION-A-SCREEN.md:223), [gate interpretation:126](/home/bmarti44/stencil-llm/results/a-screen/REGISTRATION-A-SCREEN.md:126)

**One binary outcome per session remains the right unit.** It measures successful completion and preservation across the two dependent edits. Treating requests or individual tests as independent observations would inflate N. Shared constructions limit generalization; they do not justify changing the registered unit.

**The statistical arithmetic is correct; gate 3 currently consumes the wrong measurement.**

`mcnemar_exact` computes

\[
\min\left(1,\;2\sum_{i=0}^{\min(b,c)}
{b+c\choose i}2^{-(b+c)}\right),
\]

with \(p=1\) for zero discordance. This is exact and two-sided. Every discordant-count combination with \(b+c\le48\) matched SciPy to floating-point precision. The Clopper–Pearson bounds matched for N=12, 36 and 48. [a_screen_summary.py:57](/home/bmarti44/stencil-llm/scripts/a_screen_summary.py:57)

Alpha 0.025 gives two 97.5% component intervals. Subtracting opposite endpoints gives the registered conservative 95% union-bound interval **for each contrast**. It is not simultaneous coverage across every reported contrast. [a_screen_summary.py:93](/home/bmarti44/stencil-llm/scripts/a_screen_summary.py:93)

Two hand-checkable boundaries:

- With \(b=c=0,N=48\), the component upper bound is \(1-0.0125^{1/48}=0.0872491\). The difference interval is **[−8.7249, +8.7249] percentage points**. That is the half-width; total width is 17.4498 points.
- With five wins and zero losses, gate 1 passes, while two-sided McNemar gives \(2/2^5=0.0625\). Three wins and zero losses give \(p=0.25\). Passing these count gates therefore need not imply statistical significance.

For valid, correctly classified manifest records, gates 1, 2, 4 and 5 implement §7’s inequalities. Gate 3’s inequality is correct, but F16 changes its input from registered function-only success. [gate implementation:161](/home/bmarti44/stencil-llm/scripts/a_screen_summary.py:161), [registered outcomes:103](/home/bmarti44/stencil-llm/results/a-screen/REGISTRATION-A-SCREEN.md:103)

**The compute estimate fits conditionally, including one rerun.**

| Component | Hours |
|---|---:|
| Two training allocations, including CF reference scoring | 8.0 |
| Evaluation: 288 × 15 s × 1.5 | 1.8 |
| Pilot: 24 × 15 s | 0.1 |
| Estimated total | **9.9** |
| One additional full training allocation | **4.0** |
| Total with one rerun | **13.9** |
| Remaining allowance | **2.1** |

The reference pass is already inside CF’s four hours. Adding it again double-counts it. The remaining allowance must cover pilot/evaluation loading, scoring while the model remains resident, checkpoint writes, existing screen smoke work, interrupted evaluation and reloads. There are **1,296 suite subprocess invocations** across the evaluation: 144 arm-sessions × nine suites. Their resident time is absent from a generation-only seconds/request estimate. [suite execution:313](/home/bmarti44/stencil-llm/src/stencil/a_screen.py:313), [compute scope:133](/home/bmarti44/stencil-llm/results/a-screen/REGISTRATION-A-SCREEN.md:133)

F13 remains operationally real: `--budget-min` defaults to unlimited, resets per process, checks only session starts, exempts saved-first-request sessions, and does not guard the second request. Training’s estimate excludes optimizer/save overhead. The reservation wrapper records an ETA without enforcing it. [runner:92](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:92), [budget check:272](/home/bmarti44/stencil-llm/scripts/a_screen_run.py:272), [trainer:270](/home/bmarti44/stencil-llm/scripts/a_screen_train.py:270), [wrapper:55](/home/bmarti44/stencil-llm/tools/gpu_reserve.sh:55)

A second training failure must end INCOMPLETE. A launched allocation exhausting its reference-scoring budget must also follow §8’s INCOMPLETE rule; the trainer currently prints COST-INELIGIBLE. [a_screen_train.py:170](/home/bmarti44/stencil-llm/scripts/a_screen_train.py:170)

The shortest changes that would change my answer are:

1. Preserve request 2’s target and required source context while maintaining the registered caps and rule survival.
2. Preserve all earlier regression checks, separate function-only from contracts, and replace AST-shape API preservation.
3. Explicitly grandfather TRAIN’s original operations and re-freeze affected content.
4. Repair resume and summary validation; enforce registered adapter provenance and compatible immutable run identities.
5. Enforce cumulative compute accounting and per-request stopping, reserve save overhead, and correct final-update loss reporting.

**DO NOT LAUNCH**
