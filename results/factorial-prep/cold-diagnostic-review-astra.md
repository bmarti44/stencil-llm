Fit-on: none. Development-on: the same two original Kimi DEV conversations, exposed maintenance attempts 01/02 and reviewed research methods. Evaluated-on: none. Synthetic local controls do not add model calls or benchmark data.

# Four-call cold diagnostic — independent Astra review

2026-09-07 · Round 1 · Reviewer: gpt-6-astra, xhigh, native session `/root/maintenance_revision_review`. Explicit user-requested Astra xhigh replaces historical Opus guidance. Author-disjoint from Sol's implementation and the parent's registration/preview. Purpose: bounded code, prompt and execution-readiness review; threat model: trusted but fallible operators. Only this review file was written. No inference, real network/GPU calls, benchmark reads, source edits or commits. Synthetic tests used temporary directories and fake HTTP/process interfaces.

**Score:** 95 / 100

**Verdict:** PASS — readiness for the separately frozen four-call diagnostic only.

## Findings

1. **High — cold-diagnostic#1 (resolved 2026-09-07: transport rejection now prevents offline application).** During preparatory review, both reviewer and coordinator independently found that a valid-looking JSON addition ending with `finish_reason=length` was replayed despite the transport failure. My synthetic reproduction recorded an accepted operation and changed post-state alongside the length error. The final driver retains raw text and the exact transport error but blocks that text from successful replay. The same independent control now records rejection, zero accepted operations and unchanged empty state; later scheduled cases continue. The added fake-HTTP test covers this path. No real diagnostic response existed when the fix landed.

Zero open high/critical findings. No additional material defect identified.

## Prompt and evidence boundaries

Reviewed all four planned requests in [the saved preview](cold-diagnostic-preview.json). Order is ETL prose, ETL transaction, TypeScript prose, TypeScript transaction. Each uses the corresponding original round-zero source verbatim, once, with the same short semantic instruction, task handles and request kind. No expected operations, gold values, author rationales or demonstrations enter the issued prompt; fixed episode IDs select the schedule rather than supply answers.

A asks for prose without register machinery. B appends the existing wire instructions, lifecycle rules, schema, caps, supported kinds and empty state/hash. I independently compared those contract fields with the unchanged updater's full prompt. The older six-item semantic guidance appears in the separately saved validation prompt, not the issued B prompt. That difference is explicitly recorded, preventing a reconstructed validation prompt from being mistaken for what the model saw.

Every case owns a distinct empty register. Cases are built before responses; no output, accepted state or conversation history flows between them. The unchanged decoder supplies temperature 0, seed 20260907, thinking disabled and the launcher-selected 1,024-token cap. B uses the unchanged compiler through a local replay decoder; A's transaction/state fields are N/A. No automatic semantic score substitutes for the later independent audit.

## Independent consumer checks

- **24 targeted tests passed:** cold diagnostic, existing maintenance driver and updater; Ruff and scoped whitespace checks pass. These include deadline incompleteness, malformed JSON, output-cap rejection, transport failure and preview without decoder construction.
- Invoked the real cold CLI with `--preview`: its complete JSON equals the parent's saved preview, and the supplied output directory remains absent. The registered model-run directory also remained absent during review.
- Exercised the real CLI through fake HTTP in two independent four-request controls. Each issued request equals the preview's exact bytes; saved request/response bodies, hashes and separate issued/validation prompts agree. One control accepts a synthetic B addition while the other B case still starts empty; the second control verifies the resolved length rejection. Prose output sentinels and accepted-rule sentinels never appear in later prompts. Exactly four requests occur per control, with no network during validation.
- Exercised the launcher's actual `main` path in default maintenance and explicit cold modes with hardware, health and subprocess boundaries replaced by local fakes. Both dry runs perform no actions or output-directory writes. Both execute paths freeze before their simulated server launch, select exactly one correct driver, preserve the 900/600/60-second total/startup/cleanup allocation, and stop/remove their own simulated container and clear its flag.
- Compared against baseline `1e83b24f2387cc978bd19c92cc87cd84ad309952`: startup-loop and complete cleanup-block ASTs are unchanged. Seven existing transport/compiler/bank/data/identity files are byte-identical. Real serving behavior, GPU availability and model weights were not revalidated by these CPU controls.

## Registration and acceptance limits

[The registration](COLD-DIAGNOSTIC.md) matches the implementation: four independent single attempts; errors and incomplete accounting retained; COMPLETE means four recorded attempts, not correct extraction. Cold mode adds its driver and registration to the committed-clean freeze while retaining the original serving limits and decoder. Actual reservation and cleanup remain measured run outcomes.

The proposed interpretation concerns combined extraction-and-transaction demand, not serialization alone. It does not establish multi-turn maintenance, model incapacity, serving correctness, autonomous recovery, coding quality or savings over manual prose. Attempts 01/02 and the three-failure maintenance stop-loss remain intact. Any full maintenance follow-up still requires its own registration and evidence; this review accepts only the stated four-call diagnostic after the reviewed files are committed and frozen.

Reviewed SHA256 identities:

- Driver: `678f12bb2a1c5c393a160e0e6eebe357dde87fb1d0fa28cc4805981c4336bc2c`
- Tests: `59cc2d782c6042a8bca562f7a8f7e22edf32c2ea5bbb8cb5ea2c607e03dcb689`
- Launcher: `eb810f29672dd1c57d481a4ff19bcc45160a1c87227e3005d172b7be3e7b7b7c`
- Registration: `46528f236ba57a118f2f8bc3b5511e9bd1818a1a7fc1684d32280270273bc4a0`
- Preview: `578734cc51746f208997c325e25506c376dad8070809ead489addc14a50ccbf6`
