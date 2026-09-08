# Terminal compatibility audit — Astra

2026-09-08. Independent Astra xhigh audit of the completed bounded run, using
preserved raw receipts and the frozen implementation. Writable scope: this file
only. The accepted readiness report remains unchanged. No model/server call,
generated-code execution, semantic test, fixture generation, replay, fitting or
implementation change was performed for this audit.

**Disposition: technical compatibility/accounting/lifecycle PASS.** No material
discrepancy or open audit finding. This verifies the registered two-call
compile/apply check; it does not establish semantic worker competence or
automatic-focus parity.

Freeze commit: `4962473d9533848924dd9d662007ce29c68be9c6`. Frozen readiness SHA-256:
`521ad91202b69389037f73a91c02b15775623b98df7f4405741aca0676fbdb19`.
Root reported launcher session `87012` terminal exit 0. The saved driver exit
receipt independently records exit 0, and the complete lifecycle records owned
cleanup and complete cleanup evidence.

## Exact native reconstruction

Reconstructed both message sequences from the frozen system/request constants,
the first actual generated source, its actual resulting module, and the genuine
assistant tool invocation and ID-matched tool feedback. Re-serialized the exact
request dictionaries independently: both match the saved render and completion
HTTP bodies, base64, byte lengths and hashes. Request lengths are 1606 and 2661
bytes. Cold request SHA matches the frozen preview.

Decoded each raw HTTP response and checked its bytes, length, hash and parsed
JSON against the preserved receipt. Both renders and both generations returned
HTTP 200. Each generation followed its completed render. The server access log
contains exactly those four POSTs, in the expected order, with no extra
generation or retry.

Independently normalized native tool arguments and tool-schema field order,
applied the frozen local chat template, and tokenized it locally. Both complete
reconstructed token sequences exactly match the authoritative render IDs, which
also exactly match the generation response's prompt IDs. Neither prompt contains
a reasoning boundary. The second prompt retains only the first final tool
invocation and actual compile/apply feedback; the first raw reasoning is absent
from the messages and rendered history.

Both render responses explicitly contain temperature 0.6, top_p 0.95, top_k 20,
min_p 0.0, seed 20260908, max_tokens 2048 and thinking_token_budget 512, with the
exact registered source-only JSON schema. Native engine logs identify
`v0.19.2rc1.dev134+gfe9c3d6c5`, the qwen3 reasoning parser, reasoning grammar
masking disabled, and asynchronous scheduling enabled. The frozen container
command includes the named-tool-compatible hermes configuration and explicit
single-token reasoning boundaries. This is native configuration and observed
output evidence, not instrumentation of every internal grammar-mask operation.

## Observed tokens and boundaries

| Call | Prompt tokens | Completion tokens | Reasoning tokens | Final argument tokens | Prompt + 2048 reserve |
|---|---:|---:|---:|---:|---:|
| Cold call 0 | 336 | 533 | 512 | 18 | 2384 |
| Post-tool call 1 | 613 | 273 | 245 | 25 | 2661 |
| Total | 949 | 806 | 757 | 43 | — |

Each output begins with exactly one start token 151667 and contains exactly one
following end token 151668. End indices are 513 and 246. Counting the IDs
strictly between the boundaries gives **512** and **245**. The first reaches
the registered allowance; the second ends below it. Neither exceeds the bound.
Both outputs finish with terminal token 151645 and native finish reason `stop`.
Decoded reasoning matches the returned reasoning string exactly. Decoded final
IDs, after removing only that terminal EOS, match the raw named-tool arguments
exactly, including whitespace.

All usage fields reconcile to full ID lengths: **949 + 806 = 1755 tokens**.
The 806 completion tokens comprise 757 reasoning, 43 final-argument tokens, four
reasoning delimiters and two terminal EOS tokens. Both actual contexts fit
32768 with the full output reserve; neither overall output cap is reached.

The 512-token observation is consistent with the configured limit but does not
by itself prove forcing caused termination. Both saved receipts correctly keep
`termination_cause_proven=false`. No causal forcing claim is accepted here.

## Source and state continuity

Both returned argument objects contain exactly the source string. Static AST
inspection and independent physical-line splicing reproduce both saved modules
byte for byte, preserving the untouched `identity` helper. No generated function
was invoked during this audit. The frozen consumer path structurally validates,
compiles and splices; it does not execute the function. Its saved feedback
accurately reports compiled/spliced true and executed false.

Call 0 source SHA-256:
`fdcf509c55676defde56d8e40107d72982a64f7c35d9841592adb3aa4097d3fb`.
Its actual module SHA-256:
`4ba5057dd10ac00be3ef9a1d5ce70fc08c15229ab5307331611d282655d4ce61`.
That module is exactly call 1's pre-state and appears in its genuine tool
feedback and current-module request. No reference reset or fabricated success
is present.

Call 1 source SHA-256:
`846b02042b8e6aca2417fd9828cc90799876efc671ffc580f6e240a0f76ff06e`.
Its final module SHA-256:
`13d425ce61667e38c49dff81daf9be289b15e7ab26c371287bace5010d1b8495`.
These agree with the saved apply receipts and final manifest. The visible
functions construct the requested small objects, but no semantic execution or
general correctness qualification is inferred from this compile-only check.

## Time, ownership and frozen inputs

Total render HTTP time is 0.298526736035 seconds; total completion HTTP time is
31.859402721981 seconds. Driver-process wall time is 32.547326803207 seconds.
The complete owned reservation lasted **516.914703271992 seconds (8.62 minutes)**:
478.870145082474 seconds to driver start, 32.547326803207 seconds in the driver,
and 5.497231006622 seconds afterward. Startup is within 600 seconds, cleanup is
within its 60-second reserve, and the entire reservation is within 1200 seconds.
The forwarded driver allowance was 661 seconds; no timeout or cap rescue occurred.

The frozen container command equals the saved launch command. Launch, driver
and cleanup receipts name owned processes; launcher PID 72617, container-client
PID 73012, driver PID 74232 and cleanup PIDs 74328/74338/74415 all occur in the
owned PID registry. Cleanup logs, stop and remove each returned 0 for
`stencil-qwen-thinking-tool-6157a1263547`. Lifecycle status is `DRIVER_EXITED`,
cleaned=true and cleanup_evidence_complete=true. The run flag is absent. Root's
separate terminal check reported empty Docker/GPU compute lists; this auditor
performed no new Docker/GPU probe.

All **15 tracked input hashes** match both their bytes at the freeze commit and
their current bytes. All **four model metadata hashes** remain unchanged. The
accepted trunk manifest's **20 file size/mtime records** still match; this audit
does not claim to have rehashed the 61,078,009,236 bytes of model files. The
readiness report, code, fixture, tokenizer and prospective settings are unchanged.

## Receipt bindings and limits

| Artifact | SHA-256 |
|---|---|
| `freeze.json` | `9ae5725c1b4d41c17aaa5267abe51ea66f151a7f9b4ac337e1b1b3701324a775` |
| `calls/manifest.json` | `81e8c02410e01b7049d8d37635101ffab6727c3b1156d14f492935d7371a1369` |
| `calls/calls/call-00.json` | `9d5917ecf960ab86f5c04083a5e032bc30e8fe88b45a0b10966d9bdbe27dfa86` |
| `calls/calls/call-01.json` | `b61641722b2ab456f55d45007396a138d12426c5db0bd1658516172920d6a6b3` |
| `lifecycle.json` | `c8d64291afeee558877ebc24c1a2c3836a47a6e65739e6232aa1a51537960697` |
| `driver-exit.json` | `449f53e36ad1e29f068f6b47ba5bfee7477b87296eef80dcdfb5d9091c0b779a` |
| `cleanup-receipts.json` | `54988add9d630f34f8e801a06d9273bf79979de529466859aa9d5c342c26b07d` |

Aggregate SHA-256 of the compact, key-sorted JSON mapping of the 15 original
artifact relative paths to their individual SHA-256 values:
`65f8f6c7ccfcbf7f3e87d4db0a1cdd72d955d3254f50207a5b007e37ca186b80`.
The mapping covers freeze, container command, launch receipt/log, driver command,
driver receipt/log, server log, lifecycle, cleanup, manifest, both calls and both
workspaces; it excludes this audit and later summaries.

The measured result supports this exact two-call native reasoning/tool/history
combination and its observed bounds. It supplies no reliability estimate,
semantic coding qualification, useful automatic/manual comparison, training
result or larger automatic-focus claim. It authorizes no additional run or
reinterpretation of the separately parked competence failure.
