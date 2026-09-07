# Check 47 — STAY on Qwen3-30B-A3B

**The local dense FP8 checkpoint loads, but fails the prespecified switch screen.** It executes 0/32 DEV calls versus the MoE’s 32/32 on the same episodes. Neither trunk finishes either episode successfully. Every dense DEV response begins with a JSON fence (19 unclosed, 13 closed); the unchanged pilot4 parser rejects all 32. No prompt/parser rescue or candidate selection.

The disclosed JavaScript second look passes **22/32** hidden-test tasks versus the MoE’s **16/32**. This is descriptive across trunks/precisions/backends, not an isolated architecture effect. No fit or tuning; only DEV00/01 gold events and the check40k authored bank. No benchmark access.

| Matched R episodes | Dense FP8 | MoE bf16, committed pilot4 |
|---|---:|---:|
| Executed responses | 0/32 (0%) | 32/32 (100%) |
| Caps | 0/32 | 0/32 |
| Final success | 0/2 | 0/2 |
| Round-0 indent compliance (executed) | 0/2 | 0/2 |
| Violations language/style/format/process | 0/0/32/0 | 0/30/10/17 |
| Breakage | 32 | 0 |

Dense zero style/process counts do not establish compliance: no code ran and the rejected envelopes provide no valid reports. Empty executed-trait denominators are unavailable evidence. Same original pilot4 indentation tasks, 512-token cap, retained history, gold R events, renderer and checker; no later lexical swap or SLAB-2 changes.

| Dense measurement | DEV R (2 streams) | JavaScript (4 streams) |
|---|---:|---:|
| Decode tok/s per stream (pooled) | 7.328 | 7.469 |
| Schedule aggregate output tok/s | 12.693 | 24.020 |
| Seconds/call (latency) | 21.951 | 29.486 |
| Schedule seconds | 378.469 | 290.796 |
| Caps | 0 | 2 |

Aggregate rates include HTTP, barriers, tools/checking and long tails; output totals include EOS. Decode rates exclude first-chunk tokens and prefill. Concurrent call latencies are not summed as GPU cost. DEV has only two independent episodes; JS uses four workers. MoE matched-episode decode rates were 9.403/9.806 tok/s and latencies 19.519/20.055s, within pilot4’s different C4 schedule (24.731 aggregate tok/s across all arms); this is not a matched scheduling speed experiment.

**Larger-test cost sensitivity (R/N ×64 + O/T ×16 = 160 episodes).** All-arm costs are unmeasured. These extrapolations assign every arm the larger observed R episode token total, scale linearly to 16 or 32 rounds, add 25% serving margin plus one measured startup. Longer contexts and O recovery can cost more. The registered conservative long-episode comparison is the 32-round row; 16 rounds are an optimistic sensitivity, not a complete forecast.

| R-like rounds/episode | Rate basis | FP8 GPU-h | bf16 estimate GPU-h |
|---:|---|---:|---:|
| 16 | observed DEV C2 | 11.47 | 22.85 |
| 16 | observed JS C4 rate applied to DEV tokens; cross-workload proxy | 6.11 | 12.12 |
| 32 | observed DEV C2 | 22.85 | 45.61 |
| 32 | observed JS C4 rate applied to DEV tokens; cross-workload proxy | 12.12 | 24.15 |

bf16 estimate uses **2× FP8 serving time** as a weight-bandwidth proxy, not a measurement or guaranteed bound. Startup is held fixed; native bf16 kernels and actual cache costs remain unqualified. The JS C4 rate is a cross-workload sensitivity, not measured C4 DEV performance. These are incremental future-run estimates; they exclude sunk prior pilots and unmeasured HF recovery. No complete ≤12 GPU-h claim is established. The failed execution criterion independently decides STAY.

**Feasibility and resources.** Qualified image digest `sha256:3dbe092ec5b2cef63b6104d33fa75d6ce53a7870962529ada69f78bbbc38e776`, vLLM 0.19.2rc1.dev134+gfe9c3d6c5, Transformers 5.6.0. CPU registry supported `Qwen3_5ForConditionalGeneration` and both configs; native FP8 loaded on GB10. Text-only fallback unneeded. The example `python` entrypoint was absent; rerun with `python3` passed. Both CPU probes used no GPU device and network disabled. Original errors and registry output are retained.

Startup **342.298s**; total container-held **1015.477/2400s** including startup, inference, idle and cleanup. Own container removed and RUNNING.flag deleted; Brian’s pid 2705 was not signaled. No checkpoint downloaded, no disk approval needed, no push. STAY is a screen result under this renderer/backend, not evidence the dense trunk is generally inferior.

Exact commands and container exit/removal receipts: [attempts.json](attempts.json). EOS mapping uses local generation config `[248046,248044]` (the text config names 248044); both follow the qualification client’s EOS accounting. JavaScript preserves check40k prompts, thinking-disabled template, cap 768 and all four hidden Node tests per task. Prompt/response/token journals retained; no hidden tests supplied in prompts.

A first audit rejected live source drift from a concurrent session. The successful audit extracts `src/` and `scripts/` from `184cb321` into a temporary directory, checks the frozen hashes, and exactly reproduces all 32 saved prompts, controller states, executions and outcomes. No live files were restored and no inference repeated. Recipe frozen at `184cb321` before inference. [registration.json](registration.json) pins committed source hashes; unrelated dirty SLAB-2 files were unused. [audit.json](audit.json) verifies 64 HTTP token/EOS/cap records, 32 exact DEV consumer replays and 32 hidden-test rescoring/prompt replays. [cpu-smoke.log](cpu-smoke.log): 32 reference calls through the new-tokenizer consumer. [summary.json](summary.json) contains per-episode violations, indent evidence and all timing/projection arithmetic. [artifact-manifest.json](artifact-manifest.json) pins compact records (each ≤10 MB); generated workspace/journal duplicates stay local.
