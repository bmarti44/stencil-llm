# Source reader 01 — independent result accuracy audit

Reviewer: native Astra at requested xhigh reasoning, `/root/prose_data_review`, 2026-09-07; author-disjoint from Kimi data, Sol implementation and parent's registration/results. Actual responses were inspected only after parent confirmed terminal exit and cleanup. CPU reads/reconstruction only: no inference, network, GPU action, fitting, source edits or commits.

Fit-on: none. Development-on: the exposed reviewed Kimi two-by-eight bank and this run. Evaluated-on: none. Preparatory reviews and earlier failure exposure preclude a held-out-validation claim.

**Result: FAIL. All 48 actual HTTP assistant responses are exactly `No active standing obligations.` All 48 oracle views contain active standing obligations. Therefore 0/48 views, 0/16 complete turns and 0/2 whole trajectories are correct. There are no ambiguous views affecting this result.** The run completed cleanly; accounting completion is not semantic success.

## Findings

1. **HIGH — Complete omission of active obligations in every requested view.** The empty-rule claim is contradicted by explicit language/error requirements in each episode's cold prefix and by those requirements plus subsequent active rules in later prefixes. These are actual model responses, not host defaults or parsing fallbacks. Full authenticated prefixes reached the model; no previous generated note or output entered any request. Failures already occur cold in both episodes, so generated-note propagation cannot explain their onset. This audit establishes the observed failure, not an internal model cause.

2. **MEDIUM — Required supporting evidence is absent in all 48 outputs.** There are no source IDs or exact source spans. An empty set of citations does not pass evidence completeness when active obligations were omitted. No fabricated citation was emitted; the defect is missing obligations and their evidence, rather than invented provenance.

## All 16 turns and 48 views

Indices are zero-based. Each row covers GLOBAL, then the two declared tasks: Rust `codec-core` / `ffi-shim`; JavaScript `cli-core` / `plugin-api`. Every one of the three views fails in every row. Descriptions identify the source-grounded requirements and lifecycle checks, not an alternative repaired answer.

| Turn | Calls | Correct views | Semantic check against the empty response |
| --- | --- | --- | --- |
| R0 | 0–2 | 0/3 | Global Rust 2021 and Result/PacketError/no-unwrap-or-panic rules are active. |
| R1 | 3–5 | 0/3 | Std-only/no-third-party dependency rule joins the existing rules. |
| R2 | 6–8 | 0/3 | Optional libc exception applies only to ffi-shim; baseline rules remain. |
| R3 | 9–11 | 0/3 | One-off doctest request does not remove standing obligations. |
| R4 | 12–14 | 0/3 | Unadopted anyhow quotation changes no standing obligation. |
| R5 | 15–17 | 0/3 | Rust 2024 replaces 2021; unrelated error/dependency rules persist. |
| R6 | 18–20 | 0/3 | Rust 2021 is restored while its replacement was live; other rules persist. |
| R7 | 21–23 | 0/3 | Global Pkt prefix applies to new public types, alongside existing rules. |
| J0 | 24–26 | 0/3 | Global ES2022 JavaScript, ESM-only/no-CommonJS rule is active. |
| J1 | 27–29 | 0/3 | ToolError/library-no-exit and node --test join the language rule. |
| J2 | 30–32 | 0/3 | Tool migration suggestion is non-authoritative; prior obligations remain active. |
| J3 | 33–35 | 0/3 | Runtime dependency restrictions apply while development tooling remains permitted. |
| J4 | 36–38 | 0/3 | Optional CommonJS interop wrapper applies only to plugin-api; ES2022 and other rules persist. |
| J5 | 39–41 | 0/3 | Explicit adoption activates quoted Error-suffix and lowercase/no-final-punctuation rules. |
| J6 | 42–44 | 0/3 | Cancelling the wrapper exception exposes the global ESM-only baseline again. |
| J7 | 45–47 | 0/3 | Validation adds the smoke script; all other active rules remain. |

Meaning and valid decomposition received the registered allowance. Earlier nuances about implicit development-tool permission or the ffi-shim dependency baseline cannot rescue an answer claiming no obligations: the explicit active language/error rules alone refute it. Negative-authority and one-off turns receive no persistence credit for returning an empty view.

## Integrity, accounting and cost

All 14 frozen artifact hashes match both working-tree bytes and committed bytes at `d9a5c9180c88ec12db8efed7bc9a1bcf031a7bcf`. All nine manifest transitive code hashes match the freeze, and exact driver arguments reconcile with the lifecycle record. Approved data SHA256 is `dea370797abc792677f22adb6e2c8a0284115e6b6c3672c0d4483a1f6e2b67f9`; frozen 48-request preview SHA256 is `5336b215d2422622a5f1a9b21d04286e8d1af1ed84ae29614c666534fc0a6e43`.

Independently reconstructed all 48 requests in authored episode/turn/GLOBAL/task order. Each source prefix has precisely the chronological authenticated IDs, roles and text through that turn; no future source, other episode, annotation or previous generated output is present. Rebuilt prompts equal the frozen preview, cases, rows and receipts. Every request's JSON/body/base64/hash/length agrees with the preview and registered `/model`, 1,024-token cap, temperature 0, seed 20260907 and thinking-disabled payload. The endpoint and request timeouts match the registered transport. Tool-current requests 30–32 were actually issued as historical-evidence queries; no host authority gate skipped them.

Every response's raw bytes/base64/hash/length/JSON agrees with the recorded assistant text. There are **48 HTTP 200 responses, 48 distinct response IDs, 48 `stop` finishes, 48 recorded/discarded outputs, zero errors and zero retries**. All scheduled calls have records; nothing is incomplete or omitted from the denominator. The server log independently contains 48 successful chat-completion POSTs. Every row records no output feedback. All bodies and outputs are within registered bounds; no cap or character error is concealed.

Server prompt usage matches the frozen local-tokenizer sizing for every request: **29,277 prompt + 288 completion = 29,565 total tokens**. Prompt counts span 346–894 and every completion is six tokens. All prompt-plus-cap budgets are below 32,768. Driver elapsed time is **21.786 seconds**; summed call timings are 21.702 seconds. Reservation time is **541.356/2,700 seconds**, approximately 514.132 seconds before driver start, 21.786 seconds in the driver and 5.438 seconds afterward. The pre-driver interval is below the 600-second ceiling and includes launch overhead; it is not pure model-loading time. Short empty answers do not establish a useful operating-cost advantage.

Lifecycle records driver/logs/stop/remove exit codes all zero and `cleaned=true`; the reservation flag is absent. The owned container was `stencil-maintenance-source-reader-45665a61d850`. No process was stopped by this reviewer.

Artifact bindings: `freeze.json` SHA256 `dcf9a92a7652994e90487f5de52f8678e78144198e16713f90d67355b338fba4`; `calls/rows.jsonl` `f0ed82c44cfee257fe3030993a8eb08d804809b644cb77088155fb6789281f5e`; `calls/manifest.json` `e27f471a2ae08976f7601735d2cb19284325084ba72022e208bbd64eca1bdaea`; `lifecycle.json` `439f91f518802633e0ef5854bb0160c28cb65859cd9f8344648aa3806926f93e`.

**Apply the registered stop-loss: park this fixed source-reader recipe, with no restart, prompt repair or rescue run.** The recurrent updater line remains parked after its third failure. This run neither proves general impossibility nor supports the full goal. A substantially different mechanism requires a new decision; eventual acceptance still requires fresh larger executable coding evidence, including automatic/manual-prose parity and measured costs/human interventions. These correlated DEV views support no statistical generalization.
