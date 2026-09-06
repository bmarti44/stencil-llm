# SLAB-1 repaired bank: CPU audit, 2026-09-06

The repaired bank meets the context and reference-pressure requirements. **GPU launch remains INFEASIBLE at reference lengths: 13.342 GPU-hours projected against 12.** No model weights, GPU, benchmark content, process signals, or network service were used. The existing check40k Python job was observed holding the review lock; no review/coder wrapper was active. The direct CPU build brief governs this scoped repair, rather than the archived phase-gate procedure. No scientific PASS is claimed.

Data lineage: fit-on = none; development-on = authored DEV grammar; evaluated-on = authored evaluation grammar, template/seed-disjoint. No public benchmark content, demonstrations, or recorded benchmark responses enter either family.

## Review findings and changes

- H1 ([review](../../results/slab-bank-review-fable.md), lines 186–202): `loop.py` transports identical text/results once; the SLAB current request also appears once. Reads expose a fixed final 240-byte UTF-8 excerpt with SHA256 and complete byte length, identically in every arm. Shared recurring instructions moved into the frozen system prompt. All four arms retain every own body and complete conversational history. A common four-arm admission function rejects the entire round if any prompt plus the 512-token reserve exceeds 32,768; a future live runner must call this before any arm decodes. The CPU audit exercises that contract for every aligned round; no clipping, seed replacement or asymmetric overflow occurred.
- H2 (review lines 72–83): requests require documented functions with named intermediate results; references contain operation-specific docstrings, compute the result and return it. Accounting uses only the real local Qwen tokenizer; byte/injected accounting is rejected. Literal tool envelopes remain the own-body definition and remain unmaskable.
- H3 (review lines 94–111): public and hidden cases use the same real CPython subprocess implementation. The worker enforces 256 MiB address space, 2 CPU seconds, a 2-second self-exit watchdog, kernel network/file-open/process-creation denials synchronized across all threads, bounded JSON output and no import/IO builtins. Parent processes send no signals. A test escapes the convenience builtin restriction and still receives EPERM for socket and host-file creation/opening. Ordinary annotations, docstrings, helpers, multiline statements, comprehensions and computational builtins pass (including ord, pow, divmod and iter). A watchdog-thread escape probe also receives EPERM for socket creation. Whole-file replace permits repair; unchanged definitions preserve their earlier style, while changed definitions are checked. Syntax/runtime/resource failures are invalid programs; wrong returned values are semantic failures; malformed calls and empty/capped outputs are breakage.
- H4 (review lines 134–149): seeded sampling covers six event-order shapes, varying event times, indent values, delivery values, scoped task, receipt keys, switch points and quoted payloads. Format retirement independently samples cancellation, completion or supersession; both supersession and completion therefore vary their target key. Format retirement independently samples cancellation, completion or supersession; both supersession and completion therefore vary their target key. DEV uses a distinct reinstatement-time production and distinct prose/rule-text productions. Strict tests compare actual normalized request scaffolds, full lifecycle tuples and rule text, with no collision exemptions. There are 61 distinct eval schedules (largest cell 3) and 8 distinct DEV schedules; all six ordering shapes occur in eval. This improves schedule diversity, but is not a claim of independently measured iid model outcomes.
- M1/M2 (review lines 41–54): every arm sees the frozen system defaults `format compact; delivery ready`, tool schema and execution policy. Manifests hash system, schema, generator, transport, renderer, sandbox and tokenizer. Each episode has at least three delayed process opportunities after completion (DEV 3–5; eval 3–21).
- M3 (review lines 112–125): ten should-pass variants per turn accompany the mutants: renamed local, parentheses, blank lines, annotation, helper, alternate docstring, reordered expression, whole-file rewrite, no read, and read after the receipt. Records expose attempted relapse, `prior_trait_present` and `prior_compliance`; scored relapse requires a prior executed own-body trait. Prior compliance is descriptive, so a first relapse immediately after a change is not silently excluded. Reinstated-style controls distinguish stale execution from an unobserved PEP-8 prior.
- LOW (review lines 126–130, 154–158, 230–233): references vary read/edit/test versus test/edit/test; the process witness requires a current workspace-bound receipt rather than a fixed call sequence. Public list cases are nonempty and discriminating. T's retired reminders expire after the same three generations as R. Python indentation tokens exclude continuation alignment and string contents. Lineage is present here, in manifests and in WORKLOG. Language is never retired; its zero relapse denominator is explicit and supports no language-relapse claim.

## Complete tokenizer dry run

All 64 eval + 8 DEV episodes were replayed in each of R/N/T/O: 288 sessions, 5,632 decoder calls. The decoder is a deterministic reference stub; all token IDs come from `models/qwen3-30b-a3b-hf/tokenizer.json`, SHA256 `aeb13307a71acd8fe81861d94ad54ab689df773318809eed3cbe794b4492dae4`. No weights are opened. R and O use the same explicit authenticated events and renderer in this CPU replay; this does not establish learned-classifier quality. `slab_cpu_audit.json` stores every round's accounting, opportunity denominator and freeze hashes. Full same-run journals/checkers remain under `/tmp/slab-bank-audit-committed-20260906/`.

| Arm | Maximum prompt tokens | Remaining context | After 512-token reserve |
|---|---:|---:|---:|
| R | 29,611 | 3,157 | 2,645 |
| N | 18,785 | 13,983 | 13,471 |
| T | 19,694 | 13,074 | 12,562 |
| O | 29,611 | 3,157 | 2,645 |

Reference own bodies: n=1,408 unique scheduled turns, min **107**, median **121**, mean **121.646**, max **137** Qwen tokens. All 1,408 are in the 100–300 band; all 72 episodes retain ten qualifying bodies before first retirement. Across four identical stub decoders this is 5,632 qualifying outputs. Actual model pressure must still be measured; reference pressure is not a GPU result.

| Family | Style | Format | Process | Language |
|---|---:|---:|---:|---:|
| Eval, 64 episodes | 486 | 503 | 512 | 0 |
| DEV, 8 episodes | 39 | 39 | 42 | 0 |
| Total, per arm | 525 | 542 | 554 | 0 |

These are schedule-fixed opportunities, counted once per turn/kind, including announcement turns. Actual relapse additionally requires the prior-own-body trait; missing executions remain missing. The minimum delayed process count is separately checked for every episode.

## Cost against 12 GPU-hours

Assume 15.4 decoded tokens/s, **1,000 newly-prefilled tokens/s**, KV retained within each episode, no cross-session sharing, all 4 arms x 64 eval episodes plus all 4 arms x 8 DEV episodes. Charge system once and newly appended prompt tokens each turn. This prefill throughput is an explicit assumption, not a measurement; model loading, GPU-idle tool time and other overhead are excluded.

- 685,108 decoded reference tokens / 15.4 = **12.358 decode-hours**.
- 3,542,789 newly-prefilled tokens / 1,000 = **0.984 prefill-hours**.
- Total **13.342 hours**, exceeding budget by **1.342 hours**. Even infinite prefill throughput cannot fit these reference decodes in 12 hours.
- At 512 decoded tokens for every call, with the same reference prefill, the scenario is **52.997 hours**; it is not a measured worst-case runtime guarantee.

The measured DEV cost/pressure gate remains required before a GPU launch. No sample count, arm, generation pressure, or eligibility requirement was reduced to make this projection pass.

## Validation

Validation coverage: **168 passing tests, 1 expected legacy xfail**. The requested command `CUDA_VISIBLE_DEVICES='' .venv/bin/python -m pytest tests/test_focus_*.py tests/test_no_side_effect_imports.py -q` completed all 72 exhaustive reference/mutant/should-pass tests successfully; four snapshot mismatches were resolved by the requested transport/manifest re-freeze. The final non-exhaustive rerun covers all four failures and the added regressions (96 passed, 1 expected xfail). All 1,408 literal reference outputs remain identical after the last sampler change; the full 72 x 4 tokenizer/state/execution audit was regenerated after that change and the final sandbox hardening. Frozen manifest/golden bindings, strict disjointness, mixed-style rewrite, sandbox escape, prior-trait and overflow regressions pass. Ruff and whitespace checks pass.
