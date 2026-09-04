# SC1 harness v1 — adversarial review, astra, 2026-09-04

Reviewed target: `eca514e`. The checkout was `08b8a3d58a99e43c23222dd1991139f92c134837`; `git diff eca514e HEAD --` over the reviewed implementation, tests, SC1 data and governing LEDGER text was empty. Governing requirements are SC1 DRAFT v2 in `LEDGER-PLAN.md:912–1262` and `data/sc1/AUTHOR-CONTRACT.md` v2. This is a new implementation review, not a rewrite or closure of the three v1 text reviews.

**Disposition: do not freeze this executable or commission production through it yet.** The selection/eviction/statistical core is substantially correct. The surrounding validation and execution controls are not: there are reproducible source leaks, inadequate negative coverage, incorrect checker outcomes, a broken determinism gate, and execution/accounting defects. Findings below assume trusted but fallible operators and authors, not a malicious same-UID attacker.

## Execution and evidence

- Read the archived protocol and topmost STATE: the requested active `plan/PROTOCOL.md` and `plan/LEDGER.md` do not exist; their archived counterparts do. The brief's narrower write restriction governs this review.
- Ran `CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 uv run pytest -q -p no:cacheprovider tests/test_sc1.py`: **22 passed in 19.20 s**. Bytecode and pytest cache writes were disabled. No full suite or benchmark tests ran.
- Ran additional foreground CPU probes using the real local Qwen tokenizer, pure checker/compiler functions, fake generation results and in-memory/mocked persistence. Modified source variants stayed in memory. No classifier/trunk model was instantiated; no CUDA workload, provider call, process signal, or sealed benchmark read occurred.
- `verify_manifest('data/sc1/smoke/manifest.json')` passed for **44 files**, ID `8f4668b6ffeb1f49f6074f220a0f9c8acadab57d8d31c323f902c20bf2c43753`. The five runtime classifier hashes match the frozen record and `WORKLOG.md:3164–3168`.
- Only this review file was written as a repository artifact. There are no implementation fixes in this review.

## High findings

### F1 — HIGH — Scheduling repeatedly parses and hashes the entire output journal; its projected overhead alone exceeds the study budget

**Locations:** `scripts/sc1.py:485–493`; `src/stencil/sc1.py:704–720,806–808`; record expansion at `src/stencil/sc1.py:496–505,758–768`.

Before every arm, the runner calls `store.pending` for every episode to count remaining attempts. Every call reparses and rehashes the entire journal, including the full output row embedded in each `completion_prepared` event. Thus the final scheduling loop alone requests **512 × 256 = 131,072 complete journal scans**. Per-layer repeated position lists make real records much larger than the fake-backend rows in the tests. Completed file hashes are also repeatedly read.

CPU reproduction used the smoke-00 rule selection and the real 4B configuration's 36 layers, constructing exactly the cache-audit structure produced by `prefill_sc1` without a model. Each layer had 1,224 position entries; the arm row was 227,997 bytes. A 64-arm, valid hash-chained journal was 14,635,172 bytes. One call to the actual `RunStore.events()` took **0.40628 s**, with the journal already in memory. Linear scaling across the growing 512-arm journal gives approximately **59.17 hours for the remaining-count scans alone**. This is a CPU extrapolation, not a measured GPU run, and excludes disk costs and other journal calls. Even the cache-empty 7,139-byte fake row projected 2.31 hours.

This overhead is charged while allocation is held but absent from the setup generation/selector projection. The study can pass projection and then exhaust its cap due to its own scheduler.

**Exact fix:** Verify/recover the journal once on opening a run, build an indexed state of attempts/completions and a remaining counter, and update that state after each durable append. Scheduling must use the index, not replay the journal per episode. Preserve immutable row hashes and full audit records; store/reference position information without forcing repeated full-record decoding. Charge actual persistence costs and include measured overhead in planning where required.

**Regression test:** Drive the real scheduling consumer through 256 synthetic episodes with realistic cache-audit rows and a fake backend; count journal reads and parsed bytes. Require bounded initial verification plus incremental processing, not 131,072 full replays. Verify changed completed bytes are still detected on reopen/analysis. No wall-clock-sensitive assertion is needed.

### F2 — HIGH — Changing `--out` resets the study's one-shot execution and cumulative cost

**Locations:** `scripts/sc1.py:387–428,598–606,663`; `src/stencil/sc1.py:1096–1109`.

Attempts, the allocation ledger, `invalid.json`, setup certificates and completion markers are all scoped to the caller-selected output directory. There is no durable manifest-to-study/run-directory binding. Reissuing `setup` with the same manifest and a new `--out` starts again from only the determinism certificate's cost. Reissuing `final` in another directory starts again from the setup certificate's cost, with no knowledge of earlier final attempts. The per-directory invalid marker likewise does not prevent rerunning an invalidated bank elsewhere.

This is an ordinary supported CLI path, not file tampering. It allows failed-setup retries, rerunning completed final arms and exceeding the global eight-hour budget while each individual directory appears compliant. V2 explicitly forbids all three.

**Exact fix:** Bind each registration/manifest to one durable study execution identity and cumulative allocation/attempt journal before model loading. A new output path must either relocate that same verified state or refuse; it must not create a second execution. Carry failure, invalidation and cap-exhaustion status across invocations and require that status in `analyze` as well. A genuinely new study requires a new registration and new sources.

**Regression test:** With a fake backend, complete or fail setup in directory A, then invoke the same manifest in directory B. Assert refusal before backend initialization and no cost reset. Repeat after a completed final first arm, after `invalid.json`, and after a cap halt; verify relocation preserves every completed byte and charged second.

### F3 — HIGH — Resume uses 512/64 attempts in the initial cost projection even when most are already complete

**Location:** `scripts/sc1.py:429–455`, especially line 441.

The initial resume gate calls `meter.can_start(512 if final else 64)` before reconciling the actual number of missing arms. Later the loop computes remaining work correctly, but an affordable resume never reaches it if this earlier projection refuses.

CPU reproduction through `run_study`, with persistence and setup-certificate IO mocked, returned `INCOMPLETE: cost cap` for spent=20,000 s and a 20 s prefill estimate. The code projected **32,800 s** for 512 arms. With two arms genuinely remaining, the same meter projects **20,050 s**, and its 300-second reservation passes. No backend was loaded. The existing tests test `CostMeter` arithmetic, not this erroneous consumer argument.

**Exact fix:** Reconcile durable/prepared completions and interruption status first, calculate actual missing attempts, then perform the initial forecast and reservation using that count. Apply the same correction to setup. Do not rerun completed arms to make the count match the old forecast.

**Regression test:** Run the real resume consumer with 510 completed final arms, two missing interrupted arms and the numbers above. Require completion of only the two missing attempts, byte-identical preservation of the 510 outputs, and inclusion of prior attempt costs. Also test a truly unaffordable remainder.

### F4 — HIGH — The supposedly blinded author input exposes policy identities and execution order

**Locations:** `src/stencil/sc1_episodes.py:246–257,1295–1312`, especially `input.assignment = slot` at line 1303.

`commission_slot` contains `order: ['clf','rule']` and `setup_order: ['full','evicted']`. `commissioning_request` copies the whole slot into the actual author input. The CPU probe for setup slot 0 returned both arrays there. The author contract forbids policy identity/ranking information; the execution-order stream is private and serves no authoring purpose. This disclosure is present even with an otherwise perfectly isolated external transport.

**Exact fix:** Construct the author assignment from an explicit allowlist of authoring factors, pool/index, attempt, and permitted content/literal/filler seeds. Keep arm names, arm order and the order stream in private commissioning metadata, outside every model-visible message. Hash the exact sanitized input sent to the provider.

**Regression test:** Exercise the actual request-envelope consumer for all pools and attempts. Recursively assert its model-visible input contains no `order`, `setup_order`, order digest or `clf`/`rule`/`full`/`evicted` arm labels, while assignments remain correct and content-attempt seeds change as registered.

### F5 — HIGH — Literal leakage checks are optional and can certify an OLD episode whose final request contains the complete answer

**Locations:** `src/stencil/sc1_episodes.py:92–119,975–980,1089–1095`.

The indispensable-literal inventory is not a required source field. `material.get('answer_literals', [])` silently disables all literal checks when an author omits it. The compiler does not check completeness against evidence/obligations. Even the shipped tool smoke inventory lists only `${VALUE}`, not its required target identifier.

CPU reproduction: take smoke-00, remove `answer_literals`, and append its exact source `work.patch` to `final_request`. The real expander and `validate_episode` accept it, with `reference.success=True`, assigned/verified age still OLD, and `literal_leakage=[]`. The rendered request includes the complete correct patch with value `eef05cba2a`. Production's additional checks require semantic-review metadata but do not repair this mechanical omission; the same validation path remains vulnerable to a missed/stale review.

**Exact fix:** Require a nonempty, typed inventory of indispensable answer literals linked to the actual decisive evidence and obligations, including required target identifiers. Validate its completeness against the compiled dependency specification; do not default to an empty list. Apply checks to prefix, tools, final request and the OLD recent suffix. Keep generic schema keys distinct from tested literals, and bind the independent semantic leakage review to the exact reviewed public rendering.

**Regression test:** The demonstrated omission must fail validation. With a complete inventory, put each tested value/identifier in each forbidden surface and require rejection before freeze. Include an assistant restatement in the retained suffix and a tool-schema constant. Preserve valid generic field names.

### F6 — HIGH — Source validation does not enforce assigned scope, actual user authority, or agreement between public tool returns and the state trace

**Locations:** `src/stencil/sc1_episodes.py:943–974,1033–1039,1150–1159`.

Three separate CPU mutations passed `expand_source` plus the actual `validate_episode`:

1. Change smoke-00's trajectory scope to `switched`; it still validates under the sampler's `continuing` assignment.
2. Change its governing instruction's actual public turn to role `tool`; leave private `authority='user'`. It still validates because line 1038 checks the annotation, not the source role.
3. Add a `get` event to smoke-05 whose correct private return is `{'v':'unfilled','p':'fixed'}`, but whose public tool text is `{'v':'impossible state','p':'fixed'}`. Validation passes: it compares execution to `event.return`, then merely checks that the unrelated `event.public_text` occurs in the turn. It never compares that public text with the return. It also does not enforce public event order/role correspondence.

These are violations of the registered population and information/state model, not just metadata reporting defects. A model may be scored against a hidden world different from the public one. The current 8 smoke traces all have no events, so they do not exercise the replay-to-public-return linkage.

**Exact fix:** Validate the trajectory's registered scope and required scope-event structure, actual user source roles for governing instructions, and complete necessary evidence/dependency links before measuring age. Use a frozen public-return serialization/mapping that is checked against the executed trace return; require correct tool turn, chronological event ordering and correspondence for public state-bearing tool returns. Private truthy annotations must not substitute for these mechanical checks.

**Regression test:** Reject all three mutations above through `validate_bank`. Add a positive, nonempty trace using the same frozen serializer, plus missing/out-of-order events, a governing tool instruction falsely annotated as user, and a necessary update placed on the wrong side of R.

### F7 — HIGH — Five whitespace variants of one semantic negative plus empty output satisfy “six distinct applicable negatives”

**Locations:** `src/stencil/sc1_episodes.py:796–837,1101–1117`.

Distinctness is raw string equality, and applicable named slots are accepted from arbitrary witness labels. The validator only requires at least two schema-valid failures; it does not require distinct semantic attacks. In a CPU reproduction, all five nonempty attack slots were the exact same patch replacing `/p` with `wrong`, serialized with different indentation. Each linked `target` and `keep`; empty output occupied the sixth slot. The actual validator accepted all six. There were **five schema-valid failures but only one distinct parsed nonempty output**. All obligation/invariant coverage checks passed.

This defeats the registered checker-sensitivity audit while retaining a green validation report. The current test checks raw output distinctness too (`tests/test_sc1.py:222`).

**Exact fix:** Deduplicate valid JSON/call negatives by parsed canonical structure and text negatives by the production normalization, before counting slots. Require each named slot to match an applicable source event/entity/scope, or use the declared first applicable unused substitute. Validate the obligation link for the actual failure class; explicitly distinguish permitted parser/schema negatives from semantic coverage instead of treating a count of two valid failures as a general certificate.

**Regression test:** Reject the five-indentation reproduction through the real validator. Include JSON key-order/number-spelling duplicates and normalized text duplicates. Test inapplicable cancellation/scope labels, substitute priority, and a valid bank containing six genuinely distinct applicable outputs plus supplementary unreachable-state probes.

### F8 — HIGH — Raw-text corruption ignores unauthorized additions, so the K=0 adoption gate can pass incorrectly

**Locations:** `src/stencil/sc1_episodes.py:518–539`, especially lines 525–527; text grammar at `src/stencil/sc1_episodes.py:144–161`.

For every string result, `check_result` unconditionally discards all `outside` changes. The grammar provides no enforced line/region permission mechanism to replace that check. A nonempty protected set such as “retain Harbor” is accepted, but it does not detect arbitrary added lines.

CPU reproduction constructed an editing smoke variant with the public instruction “Write the approved code as the first line and Harbor as the second line. Preserve Harbor and add no other lines.” The complete expected artifact was `${VALUE}\nHarbor`; the protected predicate required Harbor. It passed the complete source/reference/six-negative validator. Appending `\nIntrusion` to its reference produced **schema_valid=True, success=False, corruption=False**. The output violates the explicitly forbidden addition but never enters K. On an otherwise qualifying 256-pair table, that missing clf-only corruption can change adoption.

**Exact fix:** Add/enforce explicit text line/content edit permissions and protection against unauthorized insertions/deletions, or compile an exhaustive equivalent invariant for the frozen text language. Do not erase string differences unconditionally. Preserve the distinction between a wrong value in an authorized edit and a change outside permitted edits. Continue evaluating protection for parsed text that fails other schema/task checks.

**Regression test:** Validate the source described above, then require K=true for extra lines at the beginning, middle and end and for protected-line deletion/change, including an over-40-line output. Require K=false for a wrong value confined to an authorized editable region. Feed one clf-only corruption into the real analysis consumer and require adoption to fail.

### F9 — HIGH — JSON floating-point parsing accepts mathematically wrong exact values

**Locations:** `src/stencil/sc1_episodes.py:289–301,317–320,378–385`.

`json.loads` converts decimal numbers to binary floats before checking equality. Different JSON numbers can become identical Python values. This is not the contract's numeric-by-value comparison.

CPU reproduction changed smoke-00 to a seeded numeric task (`fields.v='number'`, VALUE an integer, initial v=0). The complete validator passed; the generated target was **9786**. The model-style output `[{"op":"replace","path":"/v","value":9786.0000000000000000000001}]` then returned **schema_valid=True and success=True**, with resulting v=9786.0. The output is not numerically equal to 9786. Boolean separation and nonfinite rejection are implemented, but they do not prevent precision loss.

**Exact fix:** Parse and retain finite JSON decimals exactly through sources, output parsing, equality and canonical serialization, for example with Decimal/exact rational numeric semantics. Never round to binary float before equality. Preserve equivalence of 1, 1.0 and 1e0 and separation of booleans; define integer schema membership by the frozen numeric law.

**Regression test:** Use the validated numeric source above: accept 9786, 9786.0 and 9.786e3; reject 9786.0000000000000000000001 and large distinct values that collide as floats. Test the production call and patch paths, signed zero, booleans, nonfinite numbers and duplicate keys.

### F10 — HIGH — Pairwise semantic review signatures bind only the right-hand source

**Locations:** `src/stencil/sc1_episodes.py:723–730,1219–1229`; handoff claim `WORKLOG.md:4009–4012`.

The pair review, stored on the lexically earlier source, checks `other_hash` against the later source. Nothing binds the signature to the earlier source's own content hash. An author can make an ordinary pre-freeze revision to the left source while leaving the prior review entry in place; the compiler updates its source hash, but the independence audit still accepts the stale sign-off. Final artifact hashing only freezes this already-invalid review record.

CPU reproduction: two production-pool-tagged smoke records with one properly populated pair sign-off passed `independence_audit`. Changing the left `scenario_gist` and left `validation.source_hash` without updating the sign-off also passed. This is narrower than the handoff's claim that signatures bind semantic source content.

**Exact fix:** Every pair decision must bind both source IDs and both `source_spec_hash` values, plus reviewer/session identity and decision. Invalidate review on either content change. Bind each narrative/leakage/coverage review to its own source/rendering as well. Enforce that independent reviewers are not either author session.

**Regression test:** Obtain a valid pair sign-off, change either source separately, and require rejection until re-review. Include same-session reviewer rejection and a positive case where only excluded provenance metadata changes without altering the separately frozen full provenance bytes.

### F11 — HIGH — Determinism certificate validation does not require cross-process replication of each cell

**Locations:** `scripts/sc1.py:323–348`.

The verifier checks two process IDs globally and two rows per episode/arm, but never requires those two rows to come from different processes. CPU reproduction supplied source A twice per arm from process P1 and source B twice per arm from process P2. That is eight rows and two processes, but no cell was replicated across processes. `verify_determinism` accepted it. It also does not require episode IDs/hashes to belong to the frozen smoke sources or bind each record to a distinct retained output artifact.

The certificate gates all production model execution, so a malformed aggregation can bypass the separately registered determinism prerequisite.

**Exact fix:** Require exactly the full Cartesian product of two distinct initialization/process identities, two frozen smoke source identities/hashes, and the two arms, one retained output per cell. Verify matching frozen inputs/deployment and token IDs across the two processes for each episode/arm. Bind retained output hashes and all charged initialization/execution time.

**Regression test:** Reject the A/P1-only, B/P2-only reproduction; reject duplicate process/cell records and non-smoke/unmatched input hashes. Accept a valid eight-record Cartesian product; reject one-token divergence in any replicated cell.

## Medium findings and remaining enforcement gaps

### F12 — MEDIUM — Fingerprints change when an explicitly unordered relation collection is reordered

**Location:** `src/stencil/sc1_episodes.py:667–699`.

Literal placeholder IDs are assigned during traversal, before unordered collections are sorted. With two relations `{relation:'first', value:'left-literal'}` and `{relation:'second', value:'right-literal'}`, reversing the relation list changed the fingerprint from `570c66d7dfde3ca75e61b7213ea6221f687229b153d1bcf3c689350b8639ddec` to `15f037824378366f2afae36e5641386f7952737c4fe9cc86801dd2a327322166` in the CPU probe. Contract v2 says ordering/renaming alone must not create a source. Distinct hashes still require human review, so this is not by itself proof of invalid inference.

Fix canonical ordering and equality-class assignment together, before assigning placeholder numbers. Test relation permutation, entity renaming, dictionary order, and repeated-versus-distinct literal equality patterns.

### F13 — MEDIUM — The commissioning path does not enforce its prospective freezes or complete provenance/retry law

**Locations:** `scripts/sc1.py:680–694`; `src/stencil/sc1_episodes.py:1045–1082,1277–1314`; production verification at `scripts/sc1.py:196–250`.

`commission` only extracts `authors` from `--stage1`. It does not require REGISTERED status, verify the scientific/executable freeze, or require an executable freeze at all. Source validation does not require prior rejected attempts/transcripts when `attempt>0`; commissioning CLI has no repair-attempt input. Author session uniqueness across the bank is not checked. `prompt_hash`/`input_hashes` are present-checked but not reconciled with the exact sanitized commissioning request and retained transcript. A transcript file hash alone does not establish what input the author received. Pair-reviewer independence is also not validated against author sessions (F10).

The handoff accurately says the provider transport is external and these are envelopes, not actual authoring calls; missing external artifacts are not fabricated here. Nevertheless, the envelope/acceptance contract must require and bind these fields before the external transport is usable. Add a frozen-stage verification helper shared by commissioning and production acceptance, an audited three-attempt request/rejection chain, session uniqueness, and exact request/transcript input checks. Test a DRAFT stage, missing Stage 2, stale prompt hash, reused session and attempt 2 without attempts 0/1.

### F14 — MEDIUM — Production can select the unregistered 1.7B trunk

**Locations:** `scripts/sc1.py:117,227–235,662,743–745`; `src/stencil/sc1.py:872–883`; `data/sc1/smoke/README.md:66` (the documented alternate trunk).

V2 specifies Qwen3-4B. The CLI explicitly supports 1.7B; production only compares the chosen trunk to a manifest that can itself be built for 1.7B. Agreement between two manifests does not establish agreement with the scientific registration. Enforce 4B for SC1-v2 production and bind all scientific deployment constants to the registered Stage 1 deployment. An exploratory alternate deployment needs its own registration. Test refusal before tokenizer/backend loading even when two supplied manifests agree on 1.7B.

### F15 — MEDIUM — Remaining initialization cost is always zero in the setup projection

**Locations:** `src/stencil/sc1.py:646–656`; `scripts/sc1.py:466–475,570–589`.

`remaining_initialization` defaults to zero and is never assigned by the runner. Yet deployment is one resident model per invocation with no warmup, and `final` is a new invocation. Its required model/scorer loading cost is omitted from the setup certificate's projection, contrary to `LEDGER-PLAN.md:1196–1208`. Actual allocation metering later catches spending but cannot make the earlier launch decision correct. Use the measured/frozen future initialization estimate, retaining it conservatively on interruption/resume; test a near-cap setup whose final initialization makes it unaffordable.

### F16 — MEDIUM — Interruption handling is only complete for cleanly journaled process loss, not the production error paths

**Locations:** `scripts/sc1.py:406–418,466–468,519–530`; `src/stencil/sc1.py:704–719,781–803`.

Every exception during `run_arm` is marked as an unresolved harness defect, including a backend device/resource-loss exception; there is no typed backend distinction for the registered infrastructure class or completed generation failure. Loading errors occur outside that handler. Additionally, an external loss during an append can leave a partial final JSONL line; `events()` then fails parsing before recovery can journal the interruption. These paths fail closed, rather than selecting a wrong package, but do not supply the advertised resume/failure taxonomy.

Introduce explicit backend outcomes for completed generation failure, documented infrastructure interruption and actual harness defect. Recover a demonstrably incomplete journal tail through a durable append-only recovery record while preserving valid prior events/arms; do not accept altered complete records. Test with a fake backend raising a device/resource-loss exception, an ordinary completed failure, and an in-memory truncated final journal event. No process needs to be killed or signalled.

## Required checklist: what was verified and what remains blocked

**Candidates, policies, budgets and echo — substantially implemented correctly.** `build_sc1_candidates` is pure/unscored and used separately by both timed arms. The consumer test compares common candidate records/hashes and proves rule independence with absent, constant-zero and constant-one scorers. It shares `split_sentence_spans`, `_tool_line_spans`, `_chunk_char_span` and `_token_span` with the frozen LEG A path; all resulting user/tool pieces are chunked at 128 local tokenizer tokens. Filtering/control-token exclusions match that implementation. Complete-piece straddles are dropped, a straddling message can contribute fully old pieces, and exclusions are retained. C is all removable columns, R=max(P,H−1024), B=min(256,C//4). Ranking uses >=0.5, the registered tie keys, nonfinite rejection and the ineligible infinity sentinel. Admission uses whole-span union accounting and continues after oversize/ineligible candidates. Echo selects chronologically, skips nonfits, serializes exactly the required header/role/index/JSON-quoted text, and checks both insertion tokens and final-message increase including two LF. Empty echo has no header; omitted echoes do not remove pins. The pinned result never draws from private fields or the final request.

**Eviction — correct two-stage structure in the inspected core and CPU cache tests.** A fresh `KVCache` is created per arm. `prefill_with_eviction` receives history first, retains prefix/pins/suffix, preserves post-RoPE K/V and absolute `cache.length`, and only then receives the query/echo. There is no BFCL pressure trigger or full-context fallback in final arms. `run_arm` asserts original history IDs/H are unchanged by echo insertion; per-layer cache widths and retained positions are recorded. Actual Qwen RoPE uses `cache.length` (`qwen3.py:402–404`); eviction does not reduce it. The 40,960-position guard is present. This does not prove absence of indirect information in surviving history KV, which v2 explicitly does not claim. The fake-cache test is not a GPU numerical determinism test.

**Interventions and fresh state — inspected paths are off.** Model forwards are routed through `InterventionCounter.forward`, which detects provided steering/amplification hooks and refuses; fresh executor copies prevent cross-arm state mutation. No scope resolver or digest is called in SC1. The scope/digest counters have no active call sites here, so their zero values are evidence of the absent path, not a measured run of those functions. Arm order uses the independent sampler stream, and all setup model generations are only full/evicted; clf/rule setup work is CPU selection/echo diagnostics. F4 concerns accidentally exposing that private order to authors.

**Checker — shared runner and complete state are present, but acceptance is blocked by F5–F9.** References and negatives call the same `run_checker` as model outputs, including fresh finite create/update/delete/get/list execution and patch application. Duplicate JSON keys, nonfinite values, extra text/framing, extra tool arguments, zero/multiple calls and boolean-number confusion are rejected. Full expected state/artifact and protected predicates are checked, including non-target creates/deletes. Parsed editing schema failures still reach protection checks when an artifact can be constructed; rejected tool operations do not mutate/invent state. Reference length, 40-line limits, assigned age, positive witness, generic negative, OLD recency-only negative and supplementary coverage probes are checked; the reject-all fixture fails validation. The normal smoke bank validates eight references and 48 raw-distinct negatives, but that count is not enough to establish the promised semantic coverage (F7). No-op checks are present, including a separate unchanged-state check during source validation. Direct-checker counterexamples that cannot survive source validation are not counted as additional production-success findings.

**Setup/final analysis — correct main gate order, incomplete lifecycle enforcement.** `final`/`analyze` require an existing, hash-verified setup certificate before tokenizer/backend/final outcome access. The certificate must equal its committed bytes; its 32 pair hashes and full/evicted pass counts are recomputed. Full>=24 and full−evicted>=8 are required; setup uses 64 generations. The analysis path requires a completion seal, all 256 registered final IDs, both immutable arms, correct episode/manifest/order identities and zero recorded interventions. There is no pair exclusion or partial-cohort statistical result. Persistence writes each arm before proceeding, and prepared completion records can recover publication crashes. Cost metering charges the allocation interval, and local attempt scheduling reserves 300 seconds. These good local controls do not fix F1–F3, F11 or F15–F16, nor make separate output directories a single study.

**Flags/analysis definitions — correct given correct checker rows.** I is parser/schema failure; T is reaching 256 tokens without schema-valid completion; complete valid output at the cap is not truncated. Repetition uses NFKC, casefold, collapsed whitespace, frozen tokenizer IDs and eight consecutive nonoverlapping four-token blocks from any token offset. All flags are evaluated, including on truncated output. U is the paired clf-only episode union, not marginal subtraction or three allowances. K is the paired clf-only corruption flag for both styles; the mathematical aggregation is right but F8 makes some input K flags wrong. Mean standalone latency includes rendering/candidate/scoring/admission/echo/prefill/generation/checking and prior interrupted attempt times; initialization is separate. The i–iv adoption conjunction is implemented, with the registered no-advantage wording when it fails.

**Lineage — runtime identity verified; author boundary enforcement remains incomplete.** No benchmark loader, benchmark cohort read or training/fitting call was found on the SC1 execution paths inspected. Importing pure BFCL segmentation helpers does not execute its benchmark loaders. The smoke manifest's file set contains no benchmark input; runtime classifier files match the five LEG B records. `data/sc1/smoke/README.md` explicitly marks all eight fixtures as informed-session development material, never reusable for setup/final; production rejects smoke-pool episodes. No evidence of fitting or tuning on SC1 was found. This is not a new audit of historical classifier training. Actual production author isolation/transcripts and independent review are still prerequisites, accurately disclosed in the handoff; F4/F5/F6/F10/F13 show why the current code is not yet an adequate acceptance boundary for them.

## Independent arithmetic

Recomputed McNemar using integer binomial sums and `Fraction`, and the CP bounds independently using 50-digit Decimal binomial-tail/CDF inversion with 100 bisection iterations. The harness's values agreed within 1.3e−16. Each component CP interval is two-sided 97.5% (tail 0.0125), and the reported paired interval is `[L_b−U_c,U_b−L_c]`, giving the required union-bound coverage. These are descriptive intervals, not extra adoption gates.

| b | c | Exact one-sided p | Paired union-CP interval |
|---:|---:|---:|---:|
| 13 | 0 | 1/8192 = 0.0001220703125 | [0.007852479769003665, 0.09060192861528388] |
| 20 | 7 | 160703/16777216 = 0.0095786452293396 | [−0.01503836145993203, 0.11454890808299877] |
| 0 | 0 | 1 | [−0.016971623041129008, 0.016971623041129008] |

Thus b=c=0 is handled correctly. At 13 net wins, D_hat=13/256=0.05078125. The unit-tested power cell N=256, q=.20, D=.05 agrees with the retained exact enumeration: rejection 0.5085745547974364, joint statistical/size gate approximately 0.4972492024243923. Rejection and the size/engineering gates remain distinct.

Sampler hand-check: SHA-256 of the exact UTF-8 bytes `SC1-v2|20260904|setup|0|author|0` is `5a1059b0553e7578e9e3577f90d5d1f43ecb96e118a371d912d9211d82eac83d`. First byte 0x5a is binary 01011010; the leading pair is 01, index 1 in `(kimi-k3,fable,gpt-6-astra,Opus)`, so the author is **fable**. The implementation agrees. Its setup-0 factor assignment is tool-work/user/recent/continuing. Assignment/order streams stay at attempt 0; only content streams change on repair. The digest convention and first-bit mappings are correct.

Eleven high findings remain open. Resolve F1–F11 and explicitly dispose of F12–F16 before executable freeze/production commissioning. The passing CPU suite and correct statistical formulas do not certify the study lifecycle, source validity, checker coverage or cost feasibility. Each high finding above supplies the required fix and a consumer-level regression test.

**VERDICT: UNSOUND**
