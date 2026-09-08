# Prose maintenance 01 — independent result accuracy audit

Reviewer: native Astra at requested xhigh reasoning, `/root/prose_data_review`, 2026-09-07. Author-disjoint from Kimi data, Sol implementation and parent's registration/results. Earlier data/code reviews were preparatory, not blind validation. Responses were first inspected after parent confirmed terminal exit and cleanup. This audit performed CPU reads/reconstruction only: no inference, network, GPU action, fitting, source edits or commits.

Fit-on: none. Development-on: two new reviewed Kimi specification-authored conversations and this exposed DEV run. Evaluated-on: none. These data and responses cannot later be described as held out.

**Result: FAIL the registered error-free maintenance criterion.** Of 48 effective GLOBAL/task views, **34 are unambiguously correct, 8 are definitely incorrect, and 6 have ambiguous dependency coverage**. Crediting all six ambiguous views gives **40/48**, which still fails. **8/16 complete turns and 1/2 complete trajectories** are correct under either treatment: every Rust turn fails its GLOBAL view; all JavaScript turns pass on meaning. The run itself completed cleanly.

## Semantic findings

1. **HIGH — Global Rust rules were narrowed to named tasks.** Every Rust note attaches `Task-specific scope: codec-core, ffi-shim` to the original global edition/error rules. The dependency ban is also task-labelled, first for both tasks and then only `codec-core`. This is explicit narrowing, not harmless paraphrase: a GLOBAL probe has no task handle. All eight Rust GLOBAL views are incorrect, even though edition replacement/restoration and error handling remain useful for the named tasks. The new public-type naming rule at turn 7 is correctly global and preserves “new”; it does not repair the older rules' scope.

2. **MEDIUM — Six Rust ffi-shim dependency views are under-specified.** From turns 2–7, the note says `For ffi-shim task only: may also depend on libc for the C bindings. Permitted.` The adjacent std-only ban is explicitly scoped to `codec-core`. A natural contrast reading carries the std-only baseline into ffi-shim and adds libc, matching the source. A stricter reading leaves the ban on other ffi-shim crates unstated. These six views are reported separately rather than presented as definite wrong restrictions or silently rescued. They do not change the failure, complete-turn count or trajectory count.

JavaScript's notes do not explicitly repeat the tooling `devDependencies` permission. They do retain the restriction specifically on runtime dependencies and shipped code, which leaves development tooling permitted. This is credited on meaning; omission of the redundant permission sentence is not counted as an invented dependency prohibition. Similarly, a global ESM baseline plus a separate task-specific permitted CommonJS wrapper is a valid decomposition of the oracle's effective language value. No exact authored key names or operation counts are required of prose notes.

## All 16 turns and 48 views

`R`: Rust probes are GLOBAL / codec-core / ffi-shim. `J`: JavaScript probes are GLOBAL / cli-core / plugin-api. `✓` correct; `✗` definite error; `?` dependency ambiguity in finding #2. Indices are zero-based; states are the actual **post-notes applied by the host**, not imagined corrected notes.

| Turn | GLOBAL | Task 1 | Task 2 | Semantic audit |
| --- | --- | --- | --- | --- |
| R0 | ✗ | ✓ | ✓ | Edition and Result/no-panic rules admitted, but labelled task-specific. |
| R1 | ✗ | ✓ | ✓ | Std-only ban added for both named tasks; global scope still lost. |
| R2 | ✗ | ✓ | ? | Correct optional libc permission; baseline ban narrowed to codec-core. |
| R3 | ✗ | ✓ | ? | One-off doctest unwrap request adds no standing rule; notes unchanged. |
| R4 | ✗ | ✓ | ? | Unadopted anyhow quotation ignored; notes unchanged. |
| R5 | ✗ | ✓ | ? | Edition changes to 2024; errors and task dependency arrangements persist. |
| R6 | ✗ | ✓ | ? | Original 2021 edition restored while replacement had been live; unrelated rules persist. |
| R7 | ✗ | ✓ | ? | New public types receive global Pkt prefix; earlier global-scope error remains. |
| J0 | ✓ | ✓ | ✓ | Global ES2022 JavaScript, ESM only/no CommonJS admitted. |
| J1 | ✓ | ✓ | ✓ | Global ToolError/library-no-exit and node --test rules admitted; language retained. |
| J2 | ✓ | ✓ | ✓ | Tool migration suggestion does not change state; candidate also matches prior notes exactly. |
| J3 | ✓ | ✓ | ✓ | Runtime-only dependency ban added, leaving development tooling permitted. |
| J4 | ✓ | ✓ | ✓ | Tiny CJS wrapper is optional only for plugin-api; global ES2022/ESM and unrelated rules retained. |
| J5 | ✓ | ✓ | ✓ | Quoted naming/message policy explicitly adopted globally; wrapper permission retained. |
| J6 | ✓ | ✓ | ✓ | Wrapper permission removed; plugin-api again inherits global ESM-only language. |
| J7 | ✓ | ✓ | ✓ | Validation gains smoke script; language, errors, naming and runtime-dependency rules preserved. |

There was one non-user candidate, at J2. The host blocked application as registered, but its raw candidate was already byte-identical to the previous note: **zero attempted semantic rule changes by this tool-turn candidate**. Do not describe the blocked-count field as evidence of a model injection failure. The 15 user candidates were applied verbatim; no per-turn manual correction or gold-state reset occurred.

## Integrity and cost

All nine freeze hashes match both current bytes and committed bytes at `3ff88b8ff7909ba3870187093587242229c569bc`. The approved input hash is `dea370797abc792677f22adb6e2c8a0284115e6b6c3672c0d4483a1f6e2b67f9`. Manifest source hashes and exact driver arguments match the freeze/launcher record.

Independently reconstructed all 16 prompts from the actual preceding applied note, authenticated source ID/role/text, full same-episode history, handles and request kind. Every reconstructed prompt, receipt prompt/hash, HTTP request JSON/body/base64/hash/length, response JSON/raw bytes/base64/hash/length, raw candidate and pre/post-note hash agrees. Both cold requests exactly match the prospective preview. Histories reset only between episodes and contain precisely the prior natural sources; no annotation oracle enters the prompts. Saved responses show **16 HTTP 200 responses, 16 `stop` finishes, 0 transport/cap errors**, 15 user applications and one correctly blocked non-user candidate. Server log contains the same 16 chat-completion POST successes. All scheduled calls have records; none is incomplete or retried.

Recomputed tokens: **10,053 prompt + 2,230 completion = 12,283 total**. Per-call prompt counts are 304–923; completions 47–256, below the 1,024 cap. No response exceeds the 8,192-character note cap (observed 180–1,112 characters). Recorded driver elapsed time is **90.128 seconds**; sum of call timings is 90.094 seconds. Reserved lifecycle time is **546.207/900 seconds**, comprising approximately 449.964 seconds before driver start, 90.128 seconds in the driver and 6.116 seconds afterward. The pre-driver interval is below the 600-second startup ceiling; it includes launch overhead and is not a pure model-loading measurement.

Lifecycle records driver/logs/stop/remove exit codes all zero, `cleaned=true`, and the run's reservation flag is absent. Container was the registered owned `stencil-maintenance-prose-11a8e8b69f69`. No external process was stopped by this reviewer. `COMPLETE` is consistent with call accounting and does not imply semantic success.

Artifact bindings: `freeze.json` SHA256 `77103a3e7e6134d72cd3110bb794d80b86dcc3aec15ba78711d48bdcaad7d064`; `calls/rows.jsonl` `83bad7727ead75f74de0c4f9f334810d5885dcbdb0517e01a7d78a7880c8392d`; `calls/manifest.json` `5ce30b3b9dff61e8ed3cc9c31afd123f1956d16622206d553d4f25dc20696dfb`; `lifecycle.json` `bd3c47392a7d261501ef8e8a3d04b58921b6a5ad04d0a72d5568042e5c47dc29`.

This is the third failed full-maintenance feasibility attempt in the registered line. **Apply the stop-loss: park this small single-updater recipe line and record a substantially different hypothesis before further inference.** The successful JavaScript trajectory and several correct lifecycle operations are useful partial evidence, not a reason for another nearly identical prompt repair. No executable coding outcome, authenticated completion, long-session generalization, statistical equivalence, human-time saving or adequate proof of the broader goal was measured.
