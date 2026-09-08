# Coding self-cue — independent result integrity audit

Reviewer: explicitly configured `gpt-6-astra`, xhigh reasoning, `/root/astra_research_reset`, 2026-09-08; requested native Astra substitution for the historical Opus default. Author-disjoint from worker implementation and Kimi data. Only this review file is writable. Read-only receipt audit: no model calls, worker/check reruns, code/data/prompt/parameter changes, run-record changes or feedback to the live worker. The earlier readiness review is preserved.

## Batch 1 — project 0, calls 0–17

**PARTIAL. No receipt-integrity discrepancy found in this completed batch.** No final screen, full-accounting, resource-ceiling or terminal-cleanup verdict is issued while the registered run remains live. This is an integrity reading of recorded outcomes, not a semantic recap review or a claim that finite checks establish all natural-language requirements. Those semantics are being reviewed independently.

Audited `results/quick-checks/coding-self-cue-01`, project `kimi-coding-dev-exhibit-labels`, six chronological rounds in fixed H/C/M order. All 18 call receipts, turn records, workspace snapshots and matching JSONL rows were complete when read. Later-project records and mutable aggregate status are outside this batch conclusion.

### Frozen inputs and native exchange

- `freeze.json` binds commit `cf33e861b5651bee87e0671055407e4a93110c69`. All ten listed files match both their recorded SHA-256 and their bytes in that commit. The current worktree bytes also match. This includes launcher, runner, CPU consumer, renderer, `slab.py`, sandbox, trunk receipt, protocol, final bank and corrected preview.
- Freeze SHA-256: `8bdd58c5a98e326d98b32f7fed2cd455638af4dfc122c467c372251807e894d1`. The accepted driver remains `0be26f7a...`, bank `925d58b6...` and preview `ca4fdf09...`.
- Independently reconstructed every issued message list from the frozen natural source messages/request, actual prior module and code-only canonical assistant history. Source roles, source IDs, request identity, task and target all agree. Only the current C recap instruction or current M manual reminder is added to that arm's issued view. Exact reconstruction shows no added oracle/check/reference/future-message content and no external-prefix or ephemeral-reminder persistence. Comments within accepted submitted code remain part of the actual artifact, as registered.
- The three first-round requests match the frozen preview's message lists, message hashes, request-body hashes and token counts exactly: H **570**, C **609**, M **666**.
- Every recorded request is native `POST /v1/chat/completions` to the frozen local endpoint with `/model`, cap 768, temperature 0, seed 20260907 and thinking disabled. Request intent, parsed payload and exact serialized request bytes agree. Both request and response base64 decode to the recorded text/JSON, byte lengths and SHA-256. Each response is HTTP 200 with exactly one assistant choice, `finish_reason=stop`, and matching raw output across the HTTP, call and turn records.

### Actual state and parser decisions

Reparsed saved response text through the accepted exact parser and recomputed the nonexecuting splice/compile decision. This does not rerun inference or executable checks. All 18 parser outcomes, extracted prefixes/fences, patch flags, pre/post modules and module/history hashes agree with the saved records. Workspace bytes agree with their corresponding post-state, and every JSONL row is the exact intended projection of its turn record.

Two submission-format failures are accurately represented:

1. Call **0**, H round 0: the response submitted a whole module; the parser records `response patch must contain exactly one top-level definition`.
2. Call **1**, C round 0: the response omitted the required path from its code-fence opening; the parser records `response fence must be ```python <path> with code`.

Both preserve the initial module and append no fabricated assistant code. Their raw responses remain available for the separate semantic audit. All other batch submissions are retained after valid parsing, including submissions with failed checks. Reconstructed per-arm histories show that subsequent requests use the arm's actual accumulated state. They neither reset to reference code nor import another arm's code. External prose is absent from canonical assistant additions; natural source assistant messages retain their authentic role and content.

### Recorded checks and accounting

All **213** recorded checks are present: **71 per arm**. Independently assembled the active check list from initial helper checks, cumulative functional checks through each round and only that round's obligation checks. Ordered IDs, symbols, rule IDs and expected alternatives agree with the receipts. Recomputed each pass/fail flag using recorded actual values and independent recursive type-sensitive JSON equality, with errors preventing a pass. All 213 verdicts agree. Turn conjunctions, completion flags, empty unfinished-check lists and row contents are consistent.

This verifies saved execution-result consistency against the frozen checks. It does not independently repeat sandbox execution or infer per-check process identity from absent PID fields. The accepted frozen consumer supplies the previously tested fresh-process/seccomp execution path.

| Arm | Valid submissions | Rounds passing the saved submission/check conjunction | Recorded checks passing | Prompt tokens | Completion tokens | Summed call seconds |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| H | 5/6 | 3, 5 | 61/71 | 11,842 | 1,833 | 79.453 |
| C | 5/6 | 3, 5 | 60/71 | 12,345 | 2,319 | 100.091 |
| M | 6/6 | 0, 2, 3, 5 | 69/71 | 13,593 | 1,829 | 80.853 |

These are descriptive batch receipts, not a final gate or independent-episode statistical result. The two invalid submissions are technically accounted responses with semantic/submission failure; they are not mislabeled as successful work.

All 18 usage objects contain non-boolean nonnegative integer counts with consistent totals and completion counts within 768. Independently rendered each actual native message list with the installed local tokenizer, then applied the existing raw Qwen tokenizer: all prompt counts agree with both local receipts and server usage. The maximum actual prompt plus reserved output cap is **4,787/32,768**. Recorded call times are nonnegative and sequential. No transport, capacity, token-accounting or local-prompt failure appears in this batch. Full-run reservation, startup and cleanup are deliberately deferred until terminal lifecycle records exist.

### Batch preservation and next boundary

The read-only reconstruction completed with 2,447 equality assertions plus type, range and time checks. To detect later drift, the ordered completed-batch evidence digest is **`cb62b878de402c79a1c66614f898d767fbc3de5cfca9d39d5744952ea0494df5`**.

Digest recipe: for each call index 0–17, in order, append four `[name, sha256]` pairs: run-relative call file, run-relative turn file, run-relative workspace file, and `rows.jsonl:<index>`. The first three hashes cover exact file bytes. The row hash covers its parsed JSON serialized with `ensure_ascii=False`, sorted keys and separators `(',', ':')`, encoded UTF-8. Serialize the resulting ordered 72-pair list with that same JSON recipe and SHA-256 it. No live-run file is created or changed by this audit.

Await the next explicitly assigned completed-project batch. After all 72 calls and terminal cleanup, reconcile the preserved batch digests, full aggregate accounting and lifecycle before a final result-integrity verdict. No change to inference order, inputs, prompts, parameters or gates follows from this preliminary review.

## Batch 2 — project 1, calls 18–35

**PARTIAL. No receipt-integrity discrepancy found. One recorded capacity failure makes this batch technically incomplete.** This is not a semantic null, and complete slot/check accounting must not erase the missing capacity-eligible response. No final full-run gate or cleanup verdict is issued here.

Applied the same read-only reconstruction to completed project `kimi-coding-dev-lighting-cues` only, without rerunning worker code or sandbox checks. All ten frozen files still match the recorded commit and worktree; the freeze-file digest is unchanged. Every call/turn/row/workspace identity and exact serialized exchange agrees. Native source roles, independent arm histories, ephemeral instruction/reminder placement, actual module state and code-only assistant additions match the frozen recipe. The three cold requests match the preview exactly, with token counts H **561**, C **600**, M **734**. Every later actual local token count agrees with the server's reported prompt usage; maximum prompt plus output allowance is **4,745/32,768**.

Call **34**, C round 5, received HTTP 200 but finished with **`length` at 768 completion tokens**. Its raw HTTP bytes and decoded response are retained. The receipt accurately labels `capacity`, records `NativeDecodeError: finish_reason=length: output cap reached`, leaves the previous module unchanged and appends no assistant code. `technical_complete=false` coexists correctly with a complete check set and complete slot accounting. There is no repair or shortened retry. The other 17 exchanges have `finish_reason=stop`; all 18 usage objects have valid types, sums and cap counts. No transport or token-accounting failure occurs in this batch.

C calls **19, 22, 25, 28 and 31** each fail the required-path fence format. Reapplying the nonexecuting accepted parser reproduces every error. Together with call 34's capacity failure, these leave C's initial module unchanged throughout this project; its shorter subsequent histories are actual failed-submission history, not artificial truncation. All H/M submissions are shape-valid and retained, including code that later produces recorded runtime errors. The saved H/M error outcomes remain failures under the independent receipt-verdict calculation.

All **309** expected check records are present, **103 per arm**, with cumulative functionality/current-only obligations and exact expected alternatives. Independent type-sensitive comparisons agree with every stored verdict, error disposition and turn conjunction. No unfinished check IDs remain for this batch. There are **18 accounted slots/check sets and 17 technically complete calls**.

| Arm | Valid submissions | Rounds passing the saved submission/check conjunction | Recorded checks passing | Prompt tokens | Completion tokens | Summed call seconds |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| H | 6/6 | 1 | 73/103 | 12,306 | 1,524 | 65.913 |
| C | 0/6 | none | 18/103 | 7,412 | 2,565 | 104.419 |
| M | 6/6 | 1 | 81/103 | 14,115 | 1,768 | 77.800 |

The batch completed **3,005 equality assertions**, plus type/range/time checks. Its 72-pair digest under the Batch 1 recipe, using actual call indices 18–35 for row labels, is **`faa04fdf2f318d4a139564a1c98704edb6dc0cc8c391d4abe0bb549150c8cd2a`**. These are partial descriptive receipts; source/recap semantic conclusions remain with the separate reviewer. Await the next completed-project assignment and eventual terminal lifecycle audit.

## Batch 3 — project 2, calls 36–53

**PARTIAL. No receipt-integrity discrepancy found in this completed batch.** All 18 exchanges and check sets are technically complete; the earlier call 34 capacity failure remains preserved and unresolved as missing capacity-eligible evidence. This batch does not supply a final full-run or cleanup verdict.

Audited project `kimi-coding-dev-puzzle-scores` with the same nonexecuting reconstruction. All ten frozen files match the commit and current worktree, and the freeze digest is unchanged. Exact native wire bytes, metadata, raw response propagation, source IDs/roles, task/target identity, independent arm histories, ephemeral prompt additions, parser/splice outcomes, pre/post-state hashes, workspace snapshots and JSONL rows all agree. The current manual reminder appears only in M's issued view; no discarded external prefix enters later canonical assistant history. The first three calls match the frozen cold prompts exactly: H **514**, C **553**, M **616**.

All 18 responses are HTTP 200, one assistant choice, `finish_reason=stop`, valid usage and no decoder error. Local rendering/tokenization agrees with recorded local and server prompt counts for every call. Completion counts span **130–607**; maximum actual prompt plus 768-token allowance is **4,047/32,768**. No capacity, transport, local-prompt or token-accounting failure occurs in this batch.

C calls **37** and **43** reproduce the parser error `response must contain exactly one triple-backtick fence`; call **40** reproduces the required-path fence-format error. These three invalid submissions leave their previous modules unchanged and append no assistant code. The later three C submissions and all H/M submissions are accepted into actual lane state even when their checks fail. Every saved prefix/fence and state transition agrees with the accepted parser/splicer; no worker code or checks were rerun.

All **285** recorded checks, **95 per arm**, exactly match the active cumulative functional/current-only obligation lists. Independent recursive type-sensitive comparisons agree with each verdict, and there are no recorded sandbox exceptions in this batch. All 18 slot-accounting/check-completion flags, turn conjunctions and empty unfinished-check lists are consistent.

| Arm | Valid submissions | Rounds passing the saved submission/check conjunction | Recorded checks passing | Prompt tokens | Completion tokens | Summed call seconds |
| --- | ---: | --- | ---: | ---: | ---: | ---: |
| H | 6/6 | 0, 1 | 86/95 | 11,735 | 1,580 | 67.616 |
| C | 3/6 | none | 51/95 | 7,115 | 1,898 | 77.430 |
| M | 6/6 | 0, 1 | 86/95 | 11,822 | 1,390 | 59.729 |

Completed **2,861 equality assertions**, plus type/range/time checks. The 72-pair batch digest under the same recipe, with row indices 36–53, is **`1eb3df157634858a9e2709e1a9d604e6f46a85886a5b8e689a10ec368b96e78b`**. Audit coverage is now completed calls 0–53; final-project records and terminal lifecycle remain pending. Semantic recap/direct-source judgments remain separate.

## Batch 4 — project 3, calls 54–71

No receipt-integrity discrepancy found in completed project `kimi-coding-dev-tray-placement`. The same reconstruction verifies all 18 native exchanges, exact source/code histories, accepted parser/splice decisions, workspace bytes and row projections. All ten frozen files remain unchanged. Cold requests H/C/M exactly match the preview, with counts **890, 929, 1017**. Every actual local prompt count equals the server's count; maximum prompt plus output allowance is **7,779/32,768**. Completion counts span **293–768**.

C calls **55, 58, 61, 64 and 67** reproduce the required-path fence-format rejection. Calls **69, 70 and 71**—all three arms' final-round requests—finish with `length` at exactly **768 completion tokens**. Each retains its raw response and prior module, appends no assistant code, completes the registered checks of actual retained state, and correctly records `technical_complete=false`. C therefore retains its initial module throughout this project. H/M retain the actual valid state from round 4 after the final-round capacity failures. No reset, repair, retry or discarded-prefix persistence appears.

All **396** expected check records, **132 per arm**, are present with consistent type-sensitive verdicts and no sandbox exceptions. The batch has **18 accounted slots/check sets and 15 technically complete calls**. H and M each have five valid submissions and passing conjunctions at rounds 0–4; each records 124/132 passing checks. C has zero valid submissions or passing round conjunctions and 18/132 passing checks. These are actual retained-state outcomes, including checks after failed submissions; they do not convert the capacity-limited requests into completed semantic evidence.

The batch passed **3,527 equality assertions**, plus type/range/time checks. Its 72-pair digest is **`4c4fa261fc0dfd9cac1e134f49bd830fd8559a51667d3da78625743ad06babd9`**. Final reconciliation follows rather than replacing any earlier partial reading.

## Final receipt-integrity verdict — 2026-09-08

**Integrity review score: 96/100. ACCEPTED as an accurate, auditable record of this run; zero open high/critical integrity findings. Experiment status: INCOMPLETE / CAPACITY-INELIGIBLE.** All 72 slots are accounted, while only 68 calls provide technically complete evidence. These are different predicates. This review does not recast the run as a fully completed semantic null or a successful feasibility screen.

### Complete reconciliation

Verified exactly 72 sequential call files, 72 turn files, 72 workspace files and 72 ordered JSONL rows, with no missing or additional call/turn files. Recomputed all four ordered batch digests against their earlier preserved values: all agree. Final driver log JSON exactly equals the terminal manifest; recorded driver arguments agree with `driver-command.json`. Manifest input and code bindings agree with the unchanged freeze. The saved server log independently records exactly **72 `POST /v1/chat/completions` responses with HTTP 200**; response receipts have **72 distinct server response IDs**. Recorded call intervals are sequential and lie within the run's recorded timing window. No extra call, retry, test feedback or human code correction appears in the audited run.

Across the four batches, the audit covered all twelve cold request identities, all 72 exact native wire exchanges and actual local/server prompt token comparisons, all independent arm-state transitions, and every one of **1,203** saved check outcomes. Current-only manual reminders and external-prefix disposal are verified by exact reconstruction, not a keyword-only contamination search. Expected alternatives and error dispositions agree with the saved pass/fail flags. This remains a receipt audit: it does not rerun worker/check execution or replace the independent natural-source/recap semantic review.

Recomputed terminal counters match the manifest exactly:

| Counter | Verified value |
| --- | ---: |
| Scheduled / recorded / network-attempted calls | 72 / 72 / 72 |
| Completed check sets / accounted slots | 72 / 72 |
| Technically complete calls | 68 |
| Total call errors | 19 |
| Parser/submission-format failures | 15 |
| Capacity failures | 4 |
| Transport / token-accounting / local-prompt failures | 0 / 0 / 0 |

The four capacity failures are calls **34, 69, 70 and 71**. The other fifteen call errors are accurately recorded parser failures at **0, 1, 19, 22, 25, 28, 31, 37, 40, 43, 55, 58, 61, 64 and 67**. All capacity responses have valid token accounting but fail the fixed capacity eligibility. The final manifest correctly sets `accounting_complete=true`, `status=INCOMPLETE`, and reason `one or more capacity-ineligible calls`.

### Descriptive outcomes and measured costs

| Arm | Valid submissions | Passing submission/check conjunctions | Recorded checks passing | Parse failures | Capacity failures | Prompt tokens | Completion tokens | Call seconds |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| H | 22/24 | 10/24 | 344/401 | 1 | 1 | 57,986 | 8,297 | 372.330 |
| C | 8/24 | 2/24 | 147/401 | 14 | 2 | 37,433 | 10,293 | 428.570 |
| M | 23/24 | 12/24 | 360/401 | 0 | 1 | 62,500 | 8,332 | 377.875 |

No arm passes all six registered turn conjunctions in any complete project. These counts include consequences of retaining failed-submission state and do not identify a unique cause of coding or obligation failure. They also do not establish that the manual arm was a competent passing control. The separate semantic audit supplies the recap and direct-source requirement readings.

Verified total usage is **157,919 prompt tokens and 26,922 completion tokens**. Summed recorded HTTP-call elapsed time is **1,178.775 seconds**, recorded check time **21.508 seconds**, and driver elapsed time **1,212.160 seconds**. These measure different components and are not interchangeable with GPU reservation time. All 72 actual prompt lengths plus the 768-token allowance fit the registered 32,768-token context; the largest is **7,779**. Passing the prospective reference headroom gate did not guarantee actual worker completion within the fixed output cap, as the four recorded length finishes demonstrate.

### Terminal lifecycle and cleanup

Lifecycle reports `DRIVER_EXITED`, driver exit **2**, `cleaned=true`, and exit **0** for log capture, stop and removal. The manifest status and exit 2 agree with the capacity-ineligible result. The independently recomputed lifecycle wall interval agrees with recorded GPU-held duration **1,714.459 seconds**, below **3,600**. Launcher start to driver manifest start is **496.033 seconds**, an upper bound on successful startup below **600**. Driver manifest finish to lifecycle end is **6.267 seconds**, an upper bound on post-driver cleanup below **60**. There is no deadline or budget-exceeded status.

Read-only `docker ps -a` filtered for the owned container `stencil-maintenance-coding-6f9d04c8ed87` returns no container. The run's `RUNNING.flag` and `/proc/13554` are absent; PID 13554 remains correctly listed in the owned-process registry. These observations corroborate successful cleanup without stopping or altering any process.

Terminal artifact SHA-256 bindings:

| Artifact, relative to run directory | SHA-256 |
| --- | --- |
| `freeze.json` | `8bdd58c5a98e326d98b32f7fed2cd455638af4dfc122c467c372251807e894d1` |
| `lifecycle.json` | `2e5b82fcb01ab5c50adffe73e33e726038a9858b825c3050f5285c1158b37fc7` |
| `driver-command.json` | `06725ee9f0e55a4974f9fa0f9f9d0912d5f45f3c0c01c9515e4a11abb619c59e` |
| `driver.log` | `238e3c0754edab6995f04cd8a8a7688dfde5a38f82ab0fd4f6f143626387a9c9` |
| `server.log` | `65d45c08b7dc89515ea9b0a7b2540dfb894b895698e42428bcc5873c35590403` |
| `calls/manifest.json` | `739846e50239a9f442ce50f08896dc3748f93c2787853eb6d5e90da06f9557ad` |
| `calls/rows.jsonl` | `06e97608f82080ebbb90f8c0a6ebf7060f8b5b78d232227917150621f5a51613` |

**SCREEN-GO is not met.** Preserve the specific completed submission/executable misses separately from the four technically incomplete responses. The fixed recipe receives no prompt, format-repair or output-cap retry under its registered stop rule. This run supports neither scaling this recipe nor a generalized benefit claim; accepting its receipt integrity is not accepting its scientific success.
