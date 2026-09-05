# FOCUS-1 DRAFT v2 + harness v1 — astra review, 2026-09-05

Reviewed target: `e3cd09e`; checkout: `98824112131dc061ed2d81ad53ce126a2005e8c3`. The intervening commit only appends ledger/worklog documentation; the reviewed v2 section, harness and tests are unchanged. Governing section: `LEDGER-PLAN.md:1710–1780`, SHA-256 `746b354436a2007984f394fa995c68c6a455312c80bc4493dca9f9bc5f0e67fb`. Implementation hashes match the handoff at lines 1791–1793.

**A: SOUND-WITH-FIXES. B: SOUND-WITH-FIXES. Do not begin the real timing smoke/setup until H1–H3 below are fixed and verified.** No critical finding; three open high harness findings, one low text correction. The experiment remains a useful, narrowly scoped oracle controllability screen. The implementation's normal path is substantially faithful; its deadline and cost paths are not ready for the one-shot run.

Scope: v2 and both prior reviews/dispositions; all of `src/stencil/focus1.py`, its driver/tests and handoff; relevant Qwen hooks/KV/prefill and function-vector code; the eval/sealed guards and parsing import dependencies. Threat model: mistakes in the supplied implementation and ordinary execution, not malicious rewriting of code, manifests and hash chains by the same user. No subagents, real model initialization, GPU work, training, background launch or process signal was used. This review is the only repository file intentionally written.

At final verification, an unrelated untracked `scripts/focus1_probe.py` had appeared since the initial clean status. I did not create, read, execute or modify it. The reviewed implementation/driver/test hashes remained unchanged.

## Validation and a review-execution exception

The requested command completed: **72 passed, one unrelated existing SyntaxWarning, in 122.11 seconds**:

```text
PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' CUDA_VISIBLE_DEVICES='' uv run pytest -q tests/test_focus1.py tests/test_eval_data_separation.py tests/test_sealed_guard.py
```

The environment additions suppress bytecode and pytest cache writes. `uv run` reported refreshing one environment package. Additional reproductions used foreground Python, CPU tensors, the existing fake tokenizer/trunk and an in-memory store; no additional test files or experiment artifacts were written.

**The requested test command conflicts with the sealed-input hard rule.** `tests/test_sealed_guard.py:33–45` reads the sealed IFEval file twice to compute SHA-256. I launched the supplied command before discovering this dependency, so those reads occurred. I disclosed the conflict when found and did not signal the running process. No sealed contents were printed, parsed as examples, or used in the review; no sealed BFCL cohort contents were read. Nevertheless, this run cannot honestly be described as satisfying “never read the sealed IFEval input file.” Future reviews under that rule must omit the two hash-reading tests or use an independently supplied integrity receipt. This is a review-execution exception, not evidence of a FOCUS-1 benchmark-data dependency.

## Part A — text

### Prior-finding disposition

The following are this reviewer's concurrence on the **text** fixes; the original review files remain preserved. Text closure does not certify the corresponding implementation failure paths.

| Prior finding | Disposition after inspecting v2 |
|---|---|
| fable F1 | Resolved: explicit sustained signal, independent main decisions given enum, no within-trunk HOLD claim (`1734–1738`, `1754`). |
| fable F2 | Resolved: descriptive retained-SET HOLD, OFF throughout, no selection or safety endpoint (`1738`). |
| fable F3 | Retained appropriately: paired synthetic extraction and disjoint operands; address carries no operand/answer (`1711`, `1719–1727`). This supports the restricted content-free runtime-channel claim, not a proof that an averaged activation contains no statistical operand information. |
| fable F4 | Resolved: exact canonical layouts exclude every previous main prompt/reply and include the 128-token neutral prefix only at HOLD/BACK (`1735–1736`). |
| fable F5 | Resolved: shuffled is explicitly a weak complete-schedule control; swapped establishes address specificity (`1734`, `1737`, `1748`). |
| fable F6 | Resolved: KEEP copy/imposition floors removed from both selection and test; KEEP safety retained; CLEAR-UNCHALLENGED is descriptive (`1728–1729`, `1750`). |
| fable F7 | Resolved: C/P separated; query-matched replay defines H without becoming a conjunct of C (`1741`, `1749`). |
| **fable F8 HIGH** | **Resolved in text:** absolute C>=63 and the four-copy test conjunction are removed. The exact endpoint tests residual harm, with independent zero-imposition and safety requirements (`1749–1752`). The stricter joint setup-copy screen is deliberately retained as selection, not misrepresented as the test endpoint. |
| **fable F9 HIGH** | **Resolved in text:** OFF schema competence added; safety floor/stop limited to five named intervention arms; broken controls produce zero applicable indicators (`1716`, `1757`). Harness H1 below prevents full implementation closure. |
| fable F10 | Resolved: per-stratum OFF counts and default-coincident interpretation (`1746`). |
| fable F11 | **Partly resolved; T1 remains:** standalone c=17/18 boundary corrected, obsolete CLEAR contrast removed, but “paired tests can still bind” is false after imposing the count/net floors. |
| fable F12 | Resolved: correct two-/four-decision conditional power replaces the single-decision extrapolation (`1717`). |
| fable F13 | Resolved: asc/desc first; asc/reverse requires a new registration/bank, without automatic fallback (`1732`). |
| fable F14 | Resolved: transplant/sham moved to setup certification, cell short-circuit specified, full shuffled control deliberately retained (`1729–1730`). |
| kimi F1–F4 | Resolved/retained with the stated changes: honest ceiling, residual-harm CLEAR, transplant as determinism witness, individual shuffled checkpoints. No double counting. |
| **kimi H1 HIGH** | **Resolved in text:** selection sort floor 29/32, copy competence 32/32, explicit eligibility-versus-reliability caveat, and replacement of the old absolute CLEAR endpoint (`1716–1717`, `1728`, `1749`). These changes do not certify high reliability; v2 now says that correctly. |
| kimi M1 | Resolved with a justified alternative to R5: neutral tokens enter the new canonical prompt; old main history does not. Only enum state crosses decisions (`1735`). |
| kimi M2 | Resolved with a justified change: replay is separate from C but is necessarily a baseline for H, rather than audit-only (`1741`, `1749`). |
| kimi M3 | Resolved: exact reviewed-section hash, listed registration deltas and review of science changes (`1731`). Section is 71 physical lines. |
| kimi L1–L4 | Resolved: explicit p threshold, enumerated setup arms, removed obsolete KEEP boundary, restricted claims. |
| kimi S1; A1–A3 | Retained/resolved: initial skill pair, fixed extraction/grid, collinearity flag and disjoint lineage. Hook implementation was independently inspected here. |
| kimi C1–C3 | Appropriate stated dispositions: speculative budget headroom rejected, two useful cuts adopted, other cuts declined. The small-framework aspiration does not itself certify timing code; see H2–H3. |
| kimi C4 | Current tail/power numbers checked; obsolete CLEAR arithmetic superseded. The paired-test interpretation still needs T1. |

### T1 — LOW, open: the paired tests cannot bind after these count/net floors

Evidence: `LEDGER-PLAN.md:1752`; the coder already correctly flagged this at `1807`, and `tests/test_focus1.py:90–112` checks it.

Let a be joint successes, b treatment-only and c control-only. With N=64 and treatment successes a+b>=48, c<=16. Adding b-c>=16 gives the largest feasible one-sided McNemar p at `(a,b,c,d)=(16,32,16,0)`: **0.01465247336026465 < 1/60**. Thus none of S–O, W–V or W–R can fail its p requirement while satisfying its treatment count and net floors. The quoted `(33,17)` and `(34,18)` tails are correct standalone but cannot attain 48 treatment successes in 64 episodes. W–R is even more redundant when R=0.

Exact text fix: replace “Floors grade magnitude; paired tests can still bind.” with “Floors grade magnitude. With N=64, treatment success >=48 and net gain >=16, the registered McNemar tests are redundant: their maximum feasible p is 0.01465247336026465. Retain and report the tests without counting them as additional evidence.” Update F11/C4's disposition accordingly. The existing exhaustive feasible-table test verifies the correction. Updating the reviewed section requires updating its hash and the explicitly bound registration delta; do not silently substitute text under the old hash.

### Recomputed reachability, CLEAR and safety

Independent CPU arithmetic confirmed:

| Quantity | Recomputed |
|---|---:|
| Family alpha | 1/60 = 0.016666666666666666 |
| Binomial(64,.10), lower tail h=0 | 0.0011790184577738603 |
| Same, h=1 | 0.009563149713054645 |
| Same, h=2 | 0.03890760910653739 |
| McNemar b=8,c=0 | 0.00390625 |
| Net 16, c=17 / c=18 | 0.016419568782134242 / 0.018241700004179906 |
| SET/SWITCH expected 75% episode success | p>=0.8660254038 / p>=0.9306048591 |
| P(count>=48), p=29/32, SET / SWITCH | 0.9456359780 / 0.1226621171 |
| One-sided 95% lower bound after 32/32 | 0.9106318 approximately |
| Test decodes | 64*(16+2+2+2+1) = 1,472 |

H<=1 is exactly the passing lower-tail boundary. R=0 is stricter than its lower-tail test, which also accepts R=1. The old absolute CLEAR-count/KEEP gates are gone. Joint setup CLEAR/replay success >=31/32 already implies setup H<=1; recording both is consistent but redundant.

No remaining **mathematically unreachable** gate was found. A full witness has all setup competence/selection answers correct and well formed; test S=W=64, O=V=R=H=0, C=P=K=64, zero breakage/impositions, valid certification and nonzero affected-layer residuals. KEEP may respect the explicit copy instruction and receive CLEAR-UNCHALLENGED while the experiment passes.

Reachability is not a power guarantee. Under an illustrative homogeneous independent per-reply schema/nonbreakage probability q, the chance of satisfying <=1 broken episode out of 64 is `P(Bin(64,1-q^m)<=1)` for m replies per arm. At q=.99 this is **0.2766649** for correct/swapped (m=4), and **0.6352294** for a two-query arm. Expected broken-episode count <=1 requires q>=**0.9960707** and **0.9921567**, respectively. At q=31/32 the corresponding probabilities are **0.0028540** and **0.0892766**. These are deliberate severe safety screens, not statistical tests of actuator benefit. Schema validity and sort correctness are different quantities; do not substitute the 29/32 sort floor for q.

The retained joint setup-copy floor is also stringent: with four independent copy decisions at q=.99, P(joint episodes>=31/32)=**0.6388738** per task; at q=31/32 it is **0.0916397**. Perfectly correlated CLEAR/replay errors change those probabilities. These are conditional illustrations, not estimates for the real trunk. They explain possible FAIL-ACTUATOR/FAIL without requiring threshold relaxation.

### Question and claim ceiling

No remaining two-readable main HOLD/delay clause was found. PASS answers the **registered sustained-signal, externally scheduled** question: one fixed A/B pair supports fresh-operand sorting schedules and limited behavioral release relative to replay. It does not show a transient signal holding a skill inside the trunk. The descriptive retained-SET arm is the only observation of HOLD without reapplication, and cannot independently establish a focus mechanism.

There is an intentional limit to CLEAR: shared valid-but-wrong copy replies can yield C=P=0 and H=0, and PASS remains possible if the other gates hold. The tests explicitly exhibit this. Consequently report C/P and the per-query pairs next to H; claim only the registered bound on replay-relative harm plus zero observed old-task impositions. Do not turn PASS into “copy reliability restored,” “zero residual harm,” “erased skill,” or a guarantee about other histories. Within that explicitly narrow ceiling, the v2 dispositions are honest. They would not support the stronger colloquial interpretation of SET/HOLD/SWITCH/CLEAR as autonomous persistent focus.

## Part B — harness findings

### H1 — HIGH, open: permitted deadline breakage is rejected as an integrity defect; CLEAR can dereference a missing audit cache

Locations: `src/stencil/focus1.py:930–1016`, `1117–1202`, `1327–1377`, `2515–2539`.

`Backend.decode` deliberately returns a partial history when its deadline expires before the final prompt token is processed. `validate_run_records` nevertheless requires the entire prompt to have reached KV, a first-logit hash, and the complete hook schedule for every answer. A normal OFF timeout therefore becomes `Invalid: omitted final token/secret rebuild`, even though OFF deadline breakage has no stop/floor. Transient deadlines can hit the same unconditional first-logit requirement. The current tests exercise scoring deadlines and counter-based stop helpers, but miss this actual producer-to-validator path.

Independent in-memory CPU reproduction through the real methods:

```text
baseline one-episode record validation: PASS
OFF deadline score: I=True, T=True, broken=True, exact=False
registered stop result: None
actual validator: Invalid omitted final token/secret rebuild
first CLEAR deadline: AttributeError 'NoneType' object has no attribute 'cache'
```

For the OFF case I generated a valid fake episode, replaced its SET/OFF record with `Engine.answer` using the same canonical prefix and a `1e-12`-second deadline, and passed all records through `validate_run_records`. For CLEAR, `Engine.neutral` with that deadline persisted CLEAR/replay answers and then passed `None` first histories to `compare_caches`. `execute_stage` converts the resulting AttributeError into generic INCOMPLETE. This is not a scientific impossibility or a corrupt cache.

**Exact fix:** represent the actual consumed prompt span/partial-decode status explicitly. Validate timeout prefixes against the frozen full prompt, with no fictitious final token, hook event or logit. Preserve complete-record strictness for completed answers. Allowed OFF/shuffled/transient deadline records must remain valid broken-control/descriptive records with zero applicable success indicators. For intervention deadlines, apply the registered breakage count; if a required retained source or residual comparison was never produced, return an explicit incomplete-audit/budget result rather than dereferencing `None` or inventing evidence. Missing evidence on a purportedly completed audit must still be INVALID.

**Required tests:** through `Engine.answer`/`Backend.decode` and the actual persisted-record analyzer, expire an OFF and a transient answer before first logits; multiple such control/descriptive failures must not themselves stop or invalidate a run. Exercise intervention timeouts before first logits and after generation begins, including CLEAR query two. Verify T, actual consumed IDs and observed/missing counts; second broken intervention episode stops; unavailable audits are explicitly reported and cannot PASS. Keep existing tampered-history/final-token tests failing.

### H2 — HIGH, open: the cooperative deadline and complete load reservation are not enforced at all execution boundaries

Locations: `src/stencil/focus1.py:1955–2016`, `2988–3016`; supporting preparation paths `891–929`, `1226–1241`.

Extraction reserves before each call but never checks the frozen attempt deadline after capture or records a deadline failure. A fake clock that advances two seconds inside each actual fake capture, with a frozen one-second deadline, produced:

```text
deadline_seconds 1
elapsed 384.0
state READY
attempts_over_deadline 192 of 192
```

This used the real `extract_vectors`, all 64 extraction triples, the real remaining-work counter and a CPU fake backend. No model was initialized. An exceeded deadline does not authorize continuing the remaining captures.

Separately, the reservation before loading is made **before** tokenizer/layout/model-file verification. After `check_bank`, the code checks only `elapsed>=CAP`, then loads. Using the real `execute_stage` with in-memory evidence/storage, a fake verification cost left 0.5 seconds, while the frozen deadline plus retained load reserve required 2.0 seconds. The fake loader was still invoked. It raised a sentinel immediately; no model was loaded. The eventual overrun/INCOMPLETE guard does not repair a forbidden launch.

**Exact fix:** re-run the complete projection/deadline/load reservation immediately before calling the loader, after all preload checks. Add cooperative budget/deadline checks at extraction and multi-forward preparation boundaries, including after each returned capture/forward and before launching another. An over-deadline extraction must persist the attempt and explicit timeout, terminate the stage normally as INCOMPLETE, and not contribute successful extraction evidence or continue the bank. Preserve the immutable deadline and cumulative charged time; do not raise the deadline to accommodate the failed attempt.

**Required tests:** (1) one capture advances the fake clock past its deadline: one persisted failed attempt, zero later captures, INCOMPLETE, no usable extraction manifest; (2) preload verification consumes the remaining full reservation: loader call count stays zero; (3) a canonical-prefix/probe forward consumes the budget: no additional probe/decode forward starts. Exercise these through `execute_stage` as well as helpers, with no real backend.

### H3 — HIGH, open: retained timing maxima omit mandatory post-query audits

Locations: `src/stencil/focus1.py:1190–1195`, `1292–1305`, `1352–1381`, `2815–2953`; projection at `712–719`.

The first-decision all-layer K/V comparison, first-logit comparison, construction and persistence of the paired audit occur **after** both `Engine.answer` measurements. Their time is never observed as a cost-class/check/persistence maximum. Initial source checks/fork cloning before `prepare_started` are also outside that measurement. Total allocation elapsed eventually includes these operations, but the rate-based forecast for all remaining work does not. The synthetic 64-token worst-case timing loops do not run these residual-audit consumers either, so they do not close the omission.

Independent in-memory fake-clock reproduction: add ten seconds only to each post-query `compare_caches(..., layer=L)` return, leaving the before-query comparisons unchanged, then run the actual two-query `Engine.neutral`:

```text
post-query audit seconds charged: 20.0
maximum retained cost rate: 0.001
neutral attempt costs: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
```

Thus arbitrary mandatory audit cost can be absent from every retained maximum while the projection claims to price the remaining 128 test audits. The 1.25 multiplier is not a measurement of omitted work. Actual cap-overrun detection correctly forbids PASS, but a misleading admission forecast can waste the one-shot budget.

**Exact fix:** include the entire registered query/fork/audit/persistence lifecycle in measured costs with a matching remaining-work count. This can be done by extending an existing query cost or a small explicitly counted audit unit; it does not require a new framework. Measure the same consumer on longest permitted retained histories during timing smoke, including both K/V comparison points, logits, clones/hashes and pair-record persistence. Retain maxima across stages and reserve before starting those operations. Keep closing persistence accounted for.

**Required tests:** advance a fake clock only during post-query K/V/logit comparisons, initial forks and pair persistence. Each must increase the applicable retained rate and the forecast by at least its counted future work (with the registered multiplier). A cap-near smoke must refuse admission when these costs make the forecast exceed 21,600 seconds. Verify the 128 test-query audits are neither omitted nor double counted, and verify the longest-history timing path actually calls the audit consumer.

## Implementation coverage outside H1–H3

| Requirement | Evidence and assessment |
|---|---|
| Seeded, separate synthetic banks | `126–222`: SHA-256 big-endian seeds, dedicated MT19937 streams, global unordered-set rejection, 64/32/64 rows, correct length/task/donor balance. 640 distinct operand sets. No externally supplied example path. |
| Competence including cue-absent OFF schema | `1891–1952`: visible >=29/32 per task, paired OFF copy 32/32, absent OFF schema >=31/32 separately per task. OFF correctness is recorded, not gated. |
| Extraction math/hook | `332–375`, `1955–2031`; `qwen3.py:418–426`: layer INPUT capture at final prompt token, each difference formed in fp32 before averaging, common rho normalization, zero/nonfinite layers excluded, grid exactly alpha={.5,1,2}, L={12,16,20}. Shared hook is last-position-only and inert at alpha zero/OFF. |
| Selection | `2034–2169`: setup-only lexicographic first eligible cell, 29/32 sorts per task, joint CLEAR/replay >=31/32, harm/imposition/safety checks, short-circuit, KEEP only after provisional eligibility. No best-test or best-cell rescue. |
| Certification and freeze | `2170–2228`, `1729–1866`: all 512 setup decisions, transplant=swapped and sham=correct token identity, mismatch INVALID without next-cell rescue; frozen inputs, vectors, outcomes and manifest chain before test. Certification is a determinism witness, not another independent endpoint. |
| Four main arms and shuffled directions | `1205–1272`, `378–388`: four test arms, separate Gaussian randomA/randomB streams and armorder stream; matched norm, fixed episode directions, correct schedules. |
| Enum-only main carry and neutral delay | `286–329`, `891–929`, `1205–1272`: independent canonical caches and equal unhooked logits/positions, fixed 128 token IDs, hook-free prefix, no prior main history supplied to later main decisions. Retained caches are used only for the separately registered probes. |
| Retained CLEAR/replay | `1292–1398`: actual BACK history fork including final token, each fork retains its own first reply, per-query OFF replay teacher-forces CLEAR's history, per-layer residuals and paired audit. Primary CLEAR never calls the old rebuilding path. The shared `generate_injected(clear_after=...)` is not used. |
| Non-vacuity convention | Requires both K and V nonzero at every affected layer for each query, as disclosed in the handoff. Conservative and potentially more restrictive than numerical reality; it is fail-closed, not evidence of guaranteed real non-vacuity. Lower-layer deltas are reported without a zero requirement. |
| Transient HOLD | `1274–1290`: correct SET cache, final token retained, appended delay/HOLD prompt, OFF through prompt/decode; descriptive only, no retuning. H1 qualifies deadline handling. |
| Statistics | `426–563`, `2236–2295`: inclusive exact tails, b+c=0 => p=1, paired per-episode indicators, strata/count/net floors, query-specific H, R whole-schedule OR, no duplicate trials. Analysis rechecks scores and records. |
| Stops/partial output | `2327–2402`: five named intervention safety stops, early irreversible count/stratum/harm/imposition failure; no optional success stopping. Partial verdicts suppress final-N p-values. Normal completed-control breakage is handled correctly; H1 covers partial deadline records. |
| Resume | `1671–1739`: no resumption is the v2 requirement, and it is correctly refused. An interrupted allocation remains charged; duplicate stages and overwrites are refused. |
| Cost cap | Cumulative elapsed, retained maxima, remaining cells, reloads and final overrun marker exist. Actual cap overrun prevents PASS. H2–H3 block certification of the admission/deadline contract. |
| Model/data guards | Driver permits only the pinned experiment root/evidence files; registration and BFCL terminal evidence and prior stages precede loader invocation. Help/generation/analyze do not load a model. The BFCL evidence interface checks a recorded terminal status, not scientific success. It is an operator attestation, not an independently authenticated process-history service. |

**No test-outcome leak into selection was found.** `preflight` checks extraction/setup and the stored test count/hash; `check_bank(test=True)` first opens test after frozen selection/certification validation (`1786–1789`). The all-mode CPU test instruments that actual file-open boundary. No benchmark reader is called by FOCUS-1; extraction and setup examples come from its generated banks, not b3/SC1/evaluation responses. Importing the two permitted parsing helpers transitively imports other helper modules, but inspection found no benchmark read or model initialization on that import path. The generic eval scanner is name/path based and is not itself a proof of all transitive data separation; the consumer trace is the relevant evidence here.

## What can be cut

3,121 helper lines are more than this question intrinsically needs, but the required freeze, provenance, retained-KV comparisons and partial-run semantics explain much of the code. Do not discard controls or weaken the registered guards merely to meet a line count. The best cuts concern repeated work and duplicated representations:

1. `Backend.forward` scans every full growing K/V tensor for finiteness on **every generated token** through `check_history`. Retain cheap length/layer-shape checks per forward; move complete-cache scans/hashes to canonical branching, retained forks and query audits, with the same fail-closed boundary checks. This removes thousands of device synchronizations without removing a scientific observation.
2. `canonical` performs four redundant unhooked probe forwards after proving independent equal clones. One canonical unhooked probe plus the existing clone-equality checks and setup determinism certification may replace repeated probes if the exact equality-witness contract is updated prospectively. Keep the four actual intervention answers.
3. Centralize record derivation/validation and store immutable layout/history references where possible. Whole prompt histories, source histories, events and comparisons are repeated across answer, replay and pair records; store the raw source once and reference it by hash/ID. Preserve same-run raw outputs and each query's exact reconstructed prior history.
4. Measure complete operation costs once at the operation boundary. This simplifies the scattered `preparation_seconds`, answer/check/persistence and out-of-band audit bookkeeping, and directly fixes H2–H3.

The transplant test-arm cut and cell short-circuit are already implemented. Keep the descriptive transient HOLD, two-query retained CLEAR/replay, all-layer audit and swapped contrast: each answers something the other arms cannot. Keep the mathematically redundant tests in this registration unless a separately reviewed simplification changes them.

Real tokenizer facts, Qwen competence, greedy determinism, residual behavior, peak memory and wall-clock costs remain unmeasured by this review. The CPU fixtures establish substantial normal-path coverage and the concrete failure-path defects above; they do not certify readiness by themselves.

**VERDICT (A), text registration readiness: SOUND-WITH-FIXES — correct T1 and bind the resulting reviewed text; prior text HIGH findings concurred resolved.**

**VERDICT (B), harness readiness for timing smoke + setup on the real trunk: SOUND-WITH-FIXES — H1, H2 and H3 are open HIGH blockers; fix and test each before the first real smoke.**
