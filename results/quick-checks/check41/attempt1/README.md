# Check 41 — language-specific dense MLP neuron scaling

Unregistered, disclosed quick check; Brian's 2026-09-05 brief. Seed **41041**. Dense **Qwen3-4B**, Python versus JavaScript. No weights trained or fitted.
Fit-on (selection/counting only): **32 cued synthetic tasks per language**, paired across languages. Choose dose on a separate **16-task setup slice**. Evaluated-on: **32 competence tasks** and **64 fresh uncued screen statements**. These four exact-statement sets are disjoint. Task families recur across splits; the screen is fresh to this run, not a held-out family benchmark. No benchmark data or sealed input access. Reuse exact task statements and parser/coarse checkers from **check 40 commit 531030a** through the byte-identical `check40-source.py.txt` snapshot; its task-bank RNG seed stays 40040 to preserve the requested bank, while check 41 model/RNG seed is 41041 and shuffled-set RNG is 41043. Later check 40 amendments are not silently imported.

## Pre-written reading (fixed before model outcomes)

- **INELIGIBLE** if either cued language has fewer than **28/32** valid, unbroken target-language outputs, or the selected Python/JavaScript sets overlap **>50%** (intersection/k). Conservatively apply the overlap gate to any of the three pre-specified k values before setup. Report competence task checks separately.
- **POSSIBLE** only with a complete 64-episode screen: correct **SET >=40/64**, correct **SWITCH >=40/64**, **<=4/64 broken correct episodes**, shuffled **<=8/64 non-default outputs** at every addressed stage (worst of SET/HOLD/SWITCH/BACK), and correct **CLEAR impositions <=8/64**.
- Otherwise **MARGINAL** if correct SET **>=24/64**; else **NOT POSSIBLE**. Eligibility takes precedence. An incomplete/cost-stopped run is **PARTIAL**, never extrapolated to 64. Report HOLD, BACK, parser identities, coarse task checks and per-layer counts regardless of verdict.

A target-language success requires an unambiguous valid parse and no breakage. Broken episode = any broken programming response at SET/HOLD/SWITCH/BACK/CLEAR; neutral response is recorded separately. Shuffled non-default = valid unbroken language differs from the paired fresh OFF response on the identical task, only where that default also has unambiguous valid language; report eligible pairs. CLEAR imposition = valid unbroken JS at CLEAR where the identical fresh OFF task gives valid Python; report eligible Python defaults, invalid CLEAR responses and all cue-absent default languages. Small eligible-default denominators limit the controls; counts are not rates on an assumed 64 Python defaults.

## Neuron selection and intervention

Hook the actual **SiLU(gate_proj(x)) * up_proj(x)** product immediately before **down_proj**, in all 36 MLP layers (width 9728). Count `(product > 0)` at every generated non-EOS token's own forward position, including the last non-EOS token; exclude prompt/history positions and EOS. Pool integer counts across positions/tasks, with no success filtering; longer answers weigh more. Save each task's counts and denominator in the same run as its text record.

For each neuron, let f_P/f_J be its language-specific positive-activation frequencies. Set p_l=f_l/(f_P+f_J), normalized binary entropy H=-sum(p_l log p_l)/log(2), and rank each language by **(f_l-f_other)*(1-H)**. This is a specified LAPE-style entropy-weighted frequency-difference heuristic, not a replication claim about a published LAPE algorithm. All-zero neurons get H=1. Select the top **k in {200,500,1000} across all layers**, deterministic stable flat-index ties. Report counts per layer, overlap/k, and counts of selected nonpositive scores; do not silently drop tied/nonpositive neurons.

For target l, scale its selected neurons by **1+g** and the other's by **1-g**, g in **{0.5,1,2}**. At g=2 the suppressed set is sign-reversed. If a neuron belongs to both sets, multiply both factors. The **deactivate-other** variant keeps the target unchanged and sets the other's neurons to zero; g is represented as 1 and this unique operation is run once per k. Thus **12 cells x 16 tasks x two languages**. Rank by both languages achieving >=10/16 valid unbroken inductions; then lowest total broken responses; then largest minimum directional success, largest total success, smaller k, smaller g, then deactivate-other. Freeze the best cell before any screen task, even if neither-direction setup qualification is attained. No selection or repair from screen outcomes.

Shuffled controls use their own fixed CPU RNG, drawing uniformly without replacement separately for each language/layer, with the exact correct-set size per layer and no outcome-dependent draws. The two shuffled sets may overlap independently; report overlap. Correct/swapped/shuffled use the same frozen k/g/variant.

## Screen and execution

64 retained-history episodes per arm. SET uses screen index e; HOLD e+13; SWITCH e+26; BACK e+39; CLEAR e+52, modulo 64. Every episode therefore has five different programming tasks, but each statement recurs across stages/episodes; these counts are descriptive and not 64 independent task families. Observe all 64 fresh OFF defaults before treatment. Arms: **correct**, **swapped**, **shuffled**, **OFF**, **text-cue**.

Sequence: **SET JS -> neutral “Reply only OK.” pair with JS scaling kept -> HOLD JS -> SWITCH Python -> BACK JS -> CLEAR off**. All arms retain their own complete actual user+assistant pairs. Every turn re-renders that full text history and rebuilds KV; scaling is applied at the final prompt position predicting the first token and all subsequently decoded positions, **not** earlier prompt/history replay positions. This tests sustained reapplication with retained text history, not a one-shot persistent neuronal state or cross-turn retained intervened KV. CLEAR retains earlier pairs, removes scaling, supplies a fresh uncued task and has no cancellation cue. Swapped reverses the addresses. Text-cue appends “Use JavaScript.” or “Use Python.” at addressed programming turns, with no cue at neutral/CLEAR. OFF never scales. Measure all arms against the correct address, alongside actual language counts.

Checker pinned to 531030a: ignore fence labels; accept one closed code fence or raw code; parse the entire extracted code with `ast.parse` and `node --check`. Both-parser = ambiguous; neither = invalid. Coarse task pass requires the named function, nonstub body and pre-written family-specific operation witness. This is syntactic plausibility, **not semantic program correctness**. Reject empty/invalid/ambiguous responses, unclosed/multiple fences, >=256 generated tokens without EOS, and repetition (a nonblank >=8-character line repeated >=4 times or an 8-token span repeated >=6 times). Generated programs are parsed, never executed.

Local HF Qwen3ForCausalLM, bf16, SDPA, single sequence, greedy decoding, thinking disabled, **256-token cap**. Exact OFF and active behavior tested through the real CPU Qwen3MLP and a tiny CPU Qwen3ForCausalLM before GPU execution. Hash source, banks, reading, CPU evidence and local model/tokenizer assets before launch. The first three competence requests serve as a charged throughput pilot with a 25% projection reserve; the fixed design does not shrink in response to outcomes or projection. **Two-hour GPU allocation cap includes loading and all GPU stages**; cooperative per-token/deadline checks reserve 30 seconds against new requests, keep partial records, and send no process signals. A single blocking load/forward can overrun; report measured overrun.

CPU preparation and commit precede GPU use. Foreground run waits with **600-second GPU/check40 polls**, requiring no NVIDIA compute process and no live `focus_check40.py --mode run` process (including a waiting check40 process, to give it priority). No process termination, signalling, background launch or push. Review/coder lock respected. On completion, recompute scores, summaries, profile frequencies, neuron selection and grid choice from raw artifacts on CPU.


## Observed results

**PARTIAL**; complete screen: False; GPU allocation 46.37/7200 seconds.

ERROR RuntimeError: Could not infer dtype of tokenizers.Encoding


| Arm | SET | HOLD | SWITCH | BACK | Broken episodes | CLEAR impositions |
|---|---:|---:|---:|---:|---:|---:|
| correct | 0/64 (n=0) | 0/64 (n=0) | 0/64 (n=0) | 0/64 (n=0) | 0/64 | 0/64 (0 eligible pairs) |
| swapped | 0/64 (n=0) | 0/64 (n=0) | 0/64 (n=0) | 0/64 (n=0) | 0/64 | 0/64 (0 eligible pairs) |
| shuffled | 0/64 (n=0) | 0/64 (n=0) | 0/64 (n=0) | 0/64 (n=0) | 0/64 | 0/64 (0 eligible pairs) |
| OFF | 0/64 (n=0) | 0/64 (n=0) | 0/64 (n=0) | 0/64 (n=0) | 0/64 | 0/64 (0 eligible pairs) |
| text-cue | 0/64 (n=0) | 0/64 (n=0) | 0/64 (n=0) | 0/64 (n=0) | 0/64 | 0/64 (0 eligible pairs) |

| Arm/stage | Task check | Target + task | Broken | Parse identity |
|---|---:|---:|---:|---|
| correct/SET | 0/64 | 0 | 0/64 | {} |
| correct/HOLD | 0/64 | 0 | 0/64 | {} |
| correct/SWITCH | 0/64 | 0 | 0/64 | {} |
| correct/BACK | 0/64 | 0 | 0/64 | {} |
| correct/CLEAR | 0/64 | None | 0/64 | {} |
| swapped/SET | 0/64 | 0 | 0/64 | {} |
| swapped/HOLD | 0/64 | 0 | 0/64 | {} |
| swapped/SWITCH | 0/64 | 0 | 0/64 | {} |
| swapped/BACK | 0/64 | 0 | 0/64 | {} |
| swapped/CLEAR | 0/64 | None | 0/64 | {} |
| shuffled/SET | 0/64 | 0 | 0/64 | {} |
| shuffled/HOLD | 0/64 | 0 | 0/64 | {} |
| shuffled/SWITCH | 0/64 | 0 | 0/64 | {} |
| shuffled/BACK | 0/64 | 0 | 0/64 | {} |
| shuffled/CLEAR | 0/64 | None | 0/64 | {} |
| OFF/SET | 0/64 | 0 | 0/64 | {} |
| OFF/HOLD | 0/64 | 0 | 0/64 | {} |
| OFF/SWITCH | 0/64 | 0 | 0/64 | {} |
| OFF/BACK | 0/64 | 0 | 0/64 | {} |
| OFF/CLEAR | 0/64 | None | 0/64 | {} |
| text-cue/SET | 0/64 | 0 | 0/64 | {} |
| text-cue/HOLD | 0/64 | 0 | 0/64 | {} |
| text-cue/SWITCH | 0/64 | 0 | 0/64 | {} |
| text-cue/BACK | 0/64 | 0 | 0/64 | {} |
| text-cue/CLEAR | 0/64 | None | 0/64 | {} |

Competence/defaults: `{}`.

Fresh screen defaults: `{}`; shuffled paired non-default counts: `{"SET": 0, "HOLD": 0, "SWITCH": 0, "BACK": 0}`.

The screen is incomplete; its prefix cannot decide full-screen feasibility.

Check 40 has no terminal feasibility reading yet; an empirical comparison is unavailable. Check 41 addresses dense MLP neurons, while check 40 addresses MoE routing on a different model.

records.jsonl preserves text, tokens, complete histories, parser/task/breakage flags and timing; profile task files preserve neuron counts in the original run. Generated programs are parsed, never executed.
