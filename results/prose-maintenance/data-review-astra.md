# Prose maintenance DEV data — independent accuracy review

Reviewer: native Astra, maximum requested reasoning effort (xhigh), session `/root/prose_data_review`, 2026-09-07. Brian's current Astra-review instruction supersedes the historical Opus reviewer note. Author-disjoint from Kimi and parent; reviewer edits only assigned review files. No inference, network, fitting, benchmark reads, or data/source edits in this review.

Fit-on: none. Authoring-on: new specification-only Kimi DEV scenarios. Evaluated-on: none. Every authored source and annotation is exposed DEV; this review cannot establish absence of pretraining overlap or held-out status. The current goal values automatic maintenance matching good manual reminders; these seeds cannot prove full maintenance generalization or executable coding benefit.

## Round 1 — 2026-09-07

Score: 86/100

Disposition: HOLD for a narrow Kimi-authored annotation patch; one open high finding, no critical findings. Scope: source-to-operation/state agreement, authority, modality, preservation, lifecycle coverage and authorship/consumer receipts. Threat model: accidental ambiguous or incorrect annotations, not malicious authors.

Reviewed `kimi-dev-authored.json` SHA256 `2f83f83dfb4c5689df9f5bdf97f93ff2e5c42e73720800ad357071095fb2555f`, author prompt, request/response, receipt, CPU receipt and `maintenance_bank.py`/register semantics. The response's content is byte-identical to the authored JSON. Request model is `kimi-k3:cloud`; response reports `kimi-k3`. Receipt records HTTP 200 and `done=true`. The prompt supplies mechanism requirements and new Rust/JavaScript settings, without benchmark examples or prior mechanism responses.

### Findings

1. **HIGH — JS task override loses the unchanged ES2022 JavaScript requirement.** Round 4 permits only a CommonJS interop wrapper for `plugin-api`, while global `lang` includes ES2022 JavaScript and ESM/no-CommonJS. The new task value `ESM with a CommonJS interop wrapper permitted` shadows the entire global key, so the oracle drops ES2022 JavaScript from `plugin-api` views in rounds 4–5. Structural replay passes because it checks the same incomplete annotation. Kimi must retain the original language/version plus ESM baseline and narrowly permitted wrapper in the local value, its round-6 cancellation echo, and the two affected expected views. Do not weaken the natural source to match the incomplete oracle.

2. **MEDIUM — Rust naming value omits the explicit “new” restriction.** Round 7 mandates the `Pkt` prefix for “every new public type name”; its operation and all three expected views instead say `public type names prefixed with Pkt`. This shorthand can be read as a broader obligation to rename existing public types, which the source does not require. Preserve “new” in Kimi's annotation and rationale before using it as the semantic oracle. This is annotation precision, not a reason to invent an existing-name migration request.

### Every-turn semantic audit

`R` is the Rust episode (`GLOBAL`, `codec-core`, `ffi-shim`); `J` is the JavaScript episode (`GLOBAL`, `cli-core`, `plugin-api`). Every row covers all three effective probes; “preserve” means every previously live unrelated rule, including task-local permissions. Indices are zero-based.

| Turn | Authorized change / preserved state | Assessment |
| --- | --- | --- |
| R0 | Admit Rust 2021 and Result/PacketError plus no unwrap/panics in library code, globally. | All 3 views agree. |
| R1 | Add global std-only/no third-party rule; preserve language/errors. | All 3 agree. |
| R2 | Add optional libc C-binding exception only for ffi-shim; retain global restriction for GLOBAL/codec-core and preserve language/errors. | All 3 agree; permission is not required libc use. |
| R3 | One-snippet doctest unwrap request, explicitly no standing change. | Zero operations; all 3 persistent views agree. |
| R4 | Quoted anyhow suggestion expressly rejected. | Zero operations; all 3 preserve both dependency scopes and prior errors/language. |
| R5 | Replace global edition 2021 with 2024; preserve errors and both dependency scopes. | All 3 agree; exact original target. |
| R6 | Cancel still-live 2024, then restore retired original 2021 in the same transaction. | All 3 agree; cancellation precedes reinstatement, unrelated rules persist. |
| R7 | Add global Pkt naming rule only for new public types. | Correct operation/scope; all 3 need finding #2's qualifier. |
| J0 | Admit ES2022 JavaScript, ESM only/no CommonJS globally. | All 3 agree. |
| J1 | Add ToolError-subclass/library-no-process.exit policy and node --test before done; preserve language. | All 3 agree; library restriction does not prohibit entrypoint exit. |
| J2 | Tool proposes TypeScript migration. | Zero operations; all 3 unchanged; tool has no rule authority. |
| J3 | Reject migration, add global runtime-dependency ban/Node built-in imports with optional tooling devDependencies. | All 3 agree; permission is not required tooling dependencies. |
| J4 | Permit tiny CommonJS interop wrapper for plugin-api only; preserve ES2022 JavaScript and all other rules. | GLOBAL/cli-core agree; plugin-api fails finding #1. |
| J5 | Explicitly adopt quoted error-name suffix and lowercase/unpunctuated message policy, globally. | Adoption and unrelated keys correct; plugin-api retains finding #1. |
| J6 | Cancel plugin-api wrapper permission; reveal still-live global language. | All 3 agree; target value must change with finding #1's patch. |
| J7 | Replace validation with unit suite plus smoke script before done; preserve language/errors/dependencies/naming. | All 3 agree; no completion event is fabricated. |

### Independent CPU and coverage checks

`load_authored_bank(..., expected_episodes=2, expected_rounds=8)` passed. A separate in-memory dictionary trace checked all 16 transactions and 48 declared views, exact target key/kind/scope/value, unique creation IDs, changed replacement values, cancellation before restoration, and single use of reinstatement targets. It agrees structurally with the adapter; neither replay resolves findings #1–2's natural-language mismatch.

Exactly 2 distinct episodes × 8 rounds, 2 task handles per episode, empty initial rules, and 48 complete GLOBAL/task probes. Every natural message is under 100 whitespace-separated words (range 35–62). There are 15 user turns and 1 tool turn; 13 changing turns and 3 no-op turns; 11 adds, 2 replacements, 2 cancellations and 1 reinstatement. Both episodes have changing and no-op turns. Requested multi-admission, one-off request, unadopted quote, tool-negative, explicit quote adoption, global/local shadowing, replacement, cancellation, restoration during a live replacement, and override cancellation revealing global are present. Rust errors remain live for all 8 rounds; JS global language remains live for all 8, including while shadowed. No rationale invents an earlier rule or a completion receipt.

Remaining coverage limits are intentional: no authenticated completion, executable task outcomes, large or untouched validation, or measured time saving. Gold operations/rationales are annotation oracles only and must remain absent from updater prompts. Any Kimi patch must be saved separately; this round and its finding identities remain on record for re-review.
