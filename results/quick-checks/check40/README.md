# Check 40 — brute-force MoE skill routing

Unregistered, disclosed quick check; Brian's 2026-09-05 resume. Seed 40040. This pre-outcome amendment adopts [the research memo](../../moe-routing-research-astra.md). The initial reading remains in commit 531030a; its numerical thresholds remain unchanged.
Fit/train-on: **none**. Profiles average cued synthetic measurements; dose selection uses only the separate setup split. Evaluated-on: fresh authored arithmetic tasks. Four splits have disjoint exact prompts and expression-tree/operator families (32 competence, 32 profile, 16 grid, 64 screen). No benchmark data, recorded benchmark responses, imported expert IDs, or sealed IFEval/BFCL inputs.

## Pre-written reading (frozen before model output)

Pair ranking: (1) Python source versus controlled English description of the same arithmetic tree (memo P1); (2) Python versus JavaScript source for the same tree, retaining Brian's programming-language requirement. Evaluate competence and, if competent, profiles for BOTH pairs; select the first eligible pair, then exactly one grid. No pair substitution after actuator outcomes. The broader P2/P3 alternatives are omitted to retain programming languages within this small budget. Paired inputs and cues are visible only in competence/profile/text controls; screen requests never name a language. Stable system default asks for a function unless another format is requested.

Competence: each mode >=28/32 parser-valid, unbroken responses. Record task correctness separately and uncued default distribution on the same 32. Python uses ast.parse; JavaScript uses node --check. English is parsed through a frozen recursive grammar: integer leaves; “the sum/difference/product of (X) and (Y)”. Code task checks require a named nonstub function and the exact requested return-expression AST; English task checks require the exact tree. No program execution. This is narrow serialization/operand preservation, not general programming competence; failure of this restrictive grammar makes the pair INELIGIBLE.

Primary profile: per-example mean top-8 expert selection frequencies over the final eight IDENTICAL prompt-suffix token IDs, averaged equally over 32 paired examples. The suffix and ordinary assistant header follow the differing user cues; verify suffix equality before accepting profiles. Canonical checker-defined answers are teacher-forced only for measurement, with no outcome filtering. Record answer-position frequencies, mean logits, router mass, and eighth-minus-ninth margins separately as diagnostics. Sigma per layer is the pooled mean within-token logit SD on primary suffix positions. P[s,l,e]=sigma[l]*f[s,l,e]; bias=alpha*(P[s]-mean(P)). No difference-norm amplification, changed top-k, or training. Save per-task statistics and token IDs in the same run.

Report per-layer primary raw-logit RMS distance, frequency L1, and top-8 intersection/8. Preserve the initial eligibility threshold: >=7/8 overlap at EVERY layer means INELIGIBLE “same experts” under this operational statistic. This is not mathematical identity; the memo's additional permutation/reliability gates and new outcome thresholds are not substituted for the user-preserved reading.

Grid: alpha {0.5,1,2,4} x {all,upper half}, both directions on the separate 16-task slice. Rank by both directions >=10/16 valid/unbroken; then lowest total breakage; largest minimum directional successes; largest total successes; smaller alpha; upper half. If no cell reaches both bars, freeze the best and disclose that fact. Never select on screen outcomes.

Episodes: 64 screen statements, five different tasks per episode at offsets {0,13,26,39,52} modulo 64. SET -> neutral “Reply only OK.” pair -> HOLD -> SWITCH -> BACK -> CLEAR. Keep actual complete user/assistant history and incremental KV, including generated terminal tokens. Bias affects NEW request prefill and decode; consume each answer's last sampled token under its original bias, then switch. Never recompute old KV under a new bias. A truncated answer stays in history, with a disclosed structural end marker to close its chat turn. No history eviction or answer replacement. CLEAR supplies a fresh uncued task with bias OFF; compare to its separately generated fresh OFF default.

Arms: correct maps B/A/B at SET/SWITCH/BACK, maintaining B through neutral/HOLD; swapped reverses addresses. Shuffled uses one fixed expert-index permutation per layer applied to both centered profiles (seed 40042), preserving values, norms, and opposition. OFF has no bias. Text-cue adds the current mode cue at SET/HOLD/SWITCH/BACK, none at neutral/CLEAR. Score every arm against the correct address and report actual mode counts.

Breakage: empty/invalid/ambiguous parse, unclosed/multiple fences, 256-token cap without EOS, a nonblank >=8-character line repeated >=4 times, or an 8-token span repeated >=6 times. Valid wrong-tree outputs are task failures, reported separately. English parsing admits the frozen grammar only. Fence labels never establish language identity.

POSSIBLE: complete 64-episode screen, correct SET >=40/64 and SWITCH >=40/64 valid/unbroken addressed outputs, <=4/64 broken correct episodes, shuffled B <=8/64 at its worst SET/HOLD/SWITCH/BACK stage, and correct CLEAR impositions <=8/64. Imposition = valid B after CLEAR where paired fresh default is valid Python. MARGINAL if correct SET >=24/64; otherwise NOT POSSIBLE. Eligibility takes precedence. HOLD/BACK/task checks are separate. These descriptive thresholds do not establish statistical existence or benchmark generalization.

Throughput FIRST: load bf16 Qwen3MoeForCausalLM, SDPA, single GPU, non-thinking, then verify the already-installed grouped_mm expert path against eager and the tuple-aware hook. Require changed expert dispatch under nonzero bias and exact OFF next-token logits; adopt grouped_mm only on compatibility/parity success. No new kernel development or serving engine. Generate THREE 128-token pilot continuations (EOS suppressed only to measure exactly 128; this exception never applies to scored generation). Record each wall-clock tokens/s and use the slowest; time a 2048-token prefill as a conservative retained-context envelope.

Before competence/extraction, project load/pilot + both candidate competence/profile screens + complete dose grid + 64 episodes x five arms x six replies + fresh defaults, at 256 capped tokens/reply, with 25% reserve. Teacher-forced passes and prefill are charged separately. If >4 GPU-h, SCALE to 32 episodes, alpha {1,4}, layers {all}; record measured projection and scaling in this README before proceeding. If still >4 h, STOP with measured throughput and no extraction. Preserve literal initial 64-count thresholds: a scaled run is a disclosed PARTIAL descriptive screen, never promoted to a full-screen POSSIBLE verdict. Recheck a conservative remaining-cost projection before grid and screen; never launch beyond cap.

Four-hour wall allocation starts before load. Cooperative deadline checks between requests/tokens; blocking kernels/load may overrun and any excess is reported. Foreground idle-GPU/download wait only, nvidia-smi polls every 600 seconds; never signal any process. All safetensors index shards must have matching membership, exact complete byte lengths and available HF SHA256 metadata verification; wait until model-specific downloader exits. A retained prompt exceeding the measured 2048-token envelope stops rather than silently extrapolating cost.

**Primary alternative explanation:** profiles may describe tokens produced AFTER a task has already been selected, while task choice lives in shared attention/residual computation. A bias could change syntax or damage processing without selecting a skill. Shared-suffix primary measurements and separate answer-token diagnostics address this risk; even a positive result is only externally maintained oracle control on these synthetic output modes.


## Results — PARTIAL / COST STOP

**The capped screen does not fit the four-hour budget, even after the prescribed reduction.** The runner stopped after the throughput pilot, before competence, profile extraction, pair selection, dose selection, or behavioral screening. This is a cost result; it does not decide whether expert-routing bias can select a skill.

The installed `grouped_mm` expert implementation was available and adopted. The GPU checks verified changed dispatch under nonzero router bias and exact OFF next-token logits. The expert-output comparison passed (recorded relative error 0.0 on the compatibility probe). No eager-versus-optimized speedup was measured.

| Pilot | Generated tokens | Wall seconds | Tokens/s |
|---|---:|---:|---:|
| 1 | 128 | 7.9907 | 16.0187 |
| 2 | 128 | 7.4127 | 17.2677 |
| 3 | 128 | 7.3670 | 17.3747 |

Projection uses the slowest trial, **16.0187 tokens/s**, plus the measured 2,048-token prefill cost (0.7469 seconds), already charged load/pilot time, and a 25% reserve. Every generated reply is charged at its 256-token cap, including neutral turns and fresh defaults; these are conservative capped projections, not measured screen runtimes.

| Design | Episodes | Alpha / layers | Capped decode tokens | Projected total GPU hours | Fits 4 h? |
|---|---:|---|---:|---:|---|
| Full | 64 | 0.5, 1, 2, 4 / all, upper half | 622,592 | 14.4341 | No |
| Required reduction | 32 | 1, 4 / all | 319,488 | 7.5569 | No |

The full projection includes 192 competence generations across the two candidate pairs, 256 teacher-forced profile forwards, 256 grid generations, and 1,984 final/default generations. The reduced projection retains competence/profile work and uses 64 grid plus 992 final/default generations. The reduced design and refusal were recorded before any extraction; no additional recipe or token-cap reduction was tried.

Actual charged GPU allocation: **869.90 seconds (14.50 minutes)** of 14,400 seconds; no cap overrun. This includes 422 seconds for the preserved first attempt: loading succeeded, but an absent `hf_device_map` metadata attribute stopped it before generation. The repair reads actual parameter placement; the first attempt has zero generated records and its script, freeze, log, weights receipt, and summary are retained under `attempt1/`. Current-attempt peak allocated memory was 57.64 GiB.

Eleven CPU check groups and lint passed. The final audit reproduced the raw-record summary, verified all 384 pilot token records and prompt hashes, recomputed timing/projection arithmetic, and verified the executed source freeze. The initial `selected_pair` placeholder was removed during reporting because no pair was selected. There are no behavioral success counts, overlap measurements, profiles, or bias/grid tensors to interpret.

Artifacts: [summary](summary.json), [throughput and projections](throughput.json), [pilot records](records.jsonl), [kernel checks](kernel.json), [audit](audit.json), [runtime](runtime.json), and [prior attempt charge](prior-attempts.json).
