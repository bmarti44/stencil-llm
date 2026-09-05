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

## Pre-generation compatibility repair (2026-09-05)

The first GPU attempt loaded the model but failed before any forward/generation because Transformers 5.16.1 defaults `apply_chat_template` to a BatchEncoding return. Preserve that complete attempt under `attempt1/`; request `return_dict=False` explicitly and test the actual local tokenizer on CPU. Charge its **46.37001516507007 seconds** to the same 7200-second allocation; all task banks, selectors, grid, thresholds and decoding settings remain fixed. No model response exists to select from or repair against.


## Observed results

**NOT POSSIBLE**; complete screen: True; GPU allocation 5031.58/7200 seconds.




| Arm | SET | HOLD | SWITCH | BACK | Broken episodes | CLEAR impositions |
|---|---:|---:|---:|---:|---:|---:|
| correct | 0/64 (n=64) | 0/64 (n=64) | 63/64 (n=64) | 0/64 (n=64) | 4/64 | 0/64 (64 eligible pairs) |
| swapped | 0/64 (n=64) | 0/64 (n=64) | 64/64 (n=64) | 0/64 (n=64) | 4/64 | 0/64 (64 eligible pairs) |
| shuffled | 0/64 (n=64) | 0/64 (n=64) | 64/64 (n=64) | 0/64 (n=64) | 2/64 | 0/64 (64 eligible pairs) |
| OFF | 0/64 (n=64) | 0/64 (n=64) | 64/64 (n=64) | 0/64 (n=64) | 2/64 | 0/64 (64 eligible pairs) |
| text-cue | 64/64 (n=64) | 64/64 (n=64) | 64/64 (n=64) | 64/64 (n=64) | 0/64 | 25/64 (64 eligible pairs) |

| Arm/stage | Task check | Target + task | Broken | Parse identity |
|---|---:|---:|---:|---|
| correct/SET | 60/64 | 0 | 0/64 | {"Python": 64} |
| correct/HOLD | 60/64 | 0 | 0/64 | {"Python": 64} |
| correct/SWITCH | 58/64 | 58 | 1/64 | {"Python": 63, "invalid": 1} |
| correct/BACK | 60/64 | 0 | 1/64 | {"Python": 63, "invalid": 1} |
| correct/CLEAR | 58/64 | None | 2/64 | {"Python": 62, "invalid": 2} |
| swapped/SET | 61/64 | 0 | 0/64 | {"Python": 64} |
| swapped/HOLD | 60/64 | 0 | 1/64 | {"Python": 63, "invalid": 1} |
| swapped/SWITCH | 61/64 | 61 | 0/64 | {"Python": 64} |
| swapped/BACK | 59/64 | 0 | 1/64 | {"Python": 63, "invalid": 1} |
| swapped/CLEAR | 58/64 | None | 2/64 | {"Python": 62, "invalid": 2} |
| shuffled/SET | 61/64 | 0 | 0/64 | {"Python": 64} |
| shuffled/HOLD | 60/64 | 0 | 0/64 | {"Python": 64} |
| shuffled/SWITCH | 61/64 | 61 | 0/64 | {"Python": 64} |
| shuffled/BACK | 61/64 | 0 | 0/64 | {"Python": 64} |
| shuffled/CLEAR | 58/64 | None | 2/64 | {"Python": 62, "invalid": 2} |
| OFF/SET | 61/64 | 0 | 0/64 | {"Python": 64} |
| OFF/HOLD | 60/64 | 0 | 0/64 | {"Python": 64} |
| OFF/SWITCH | 61/64 | 61 | 0/64 | {"Python": 64} |
| OFF/BACK | 60/64 | 0 | 0/64 | {"Python": 64} |
| OFF/CLEAR | 58/64 | None | 2/64 | {"Python": 62, "invalid": 2} |
| text-cue/SET | 55/64 | 55 | 0/64 | {"JavaScript": 64} |
| text-cue/HOLD | 59/64 | 59 | 0/64 | {"JavaScript": 64} |
| text-cue/SWITCH | 61/64 | 61 | 0/64 | {"Python": 64} |
| text-cue/BACK | 59/64 | 59 | 0/64 | {"JavaScript": 64} |
| text-cue/CLEAR | 59/64 | None | 0/64 | {"JavaScript": 25, "Python": 39} |

Competence/defaults: `{"Python": {"valid": 32, "task_check": 32, "n": 32}, "JavaScript": {"valid": 32, "task_check": 25, "n": 32}, "default": {"Python": 31, "broken": 1}}`.

Fresh screen defaults: `{"Python": 64}`; shuffled paired non-default counts: `{"SET": 0, "HOLD": 0, "SWITCH": 0, "BACK": 0}`.

| Layer | Python k200 | JS k200 | Python k500 | JS k500 | Python k1000 | JS k1000 |
|---|---:|---:|---:|---:|---:|---:|
| 0 | 1 | 0 | 1 | 1 | 2 | 3 |
| 1 | 0 | 0 | 1 | 3 | 2 | 5 |
| 2 | 0 | 3 | 0 | 5 | 4 | 10 |
| 3 | 3 | 5 | 10 | 16 | 22 | 31 |
| 4 | 32 | 33 | 76 | 90 | 138 | 160 |
| 5 | 6 | 9 | 10 | 18 | 26 | 27 |
| 6 | 0 | 2 | 2 | 3 | 3 | 4 |
| 7 | 0 | 0 | 0 | 2 | 2 | 2 |
| 8 | 0 | 0 | 1 | 0 | 2 | 1 |
| 9 | 2 | 3 | 5 | 4 | 10 | 7 |
| 10 | 1 | 4 | 3 | 6 | 11 | 8 |
| 11 | 0 | 1 | 0 | 2 | 1 | 4 |
| 12 | 1 | 0 | 1 | 2 | 1 | 3 |
| 13 | 0 | 0 | 1 | 0 | 1 | 0 |
| 14 | 0 | 0 | 1 | 0 | 1 | 0 |
| 15 | 0 | 0 | 0 | 0 | 0 | 0 |
| 16 | 0 | 0 | 0 | 0 | 0 | 0 |
| 17 | 0 | 0 | 0 | 0 | 0 | 0 |
| 18 | 1 | 0 | 1 | 0 | 1 | 0 |
| 19 | 2 | 0 | 2 | 0 | 2 | 0 |
| 20 | 0 | 0 | 0 | 0 | 1 | 0 |
| 21 | 2 | 0 | 2 | 0 | 2 | 0 |
| 22 | 2 | 2 | 2 | 2 | 4 | 4 |
| 23 | 1 | 1 | 1 | 1 | 1 | 2 |
| 24 | 7 | 6 | 16 | 15 | 39 | 32 |
| 25 | 11 | 13 | 22 | 29 | 46 | 53 |
| 26 | 25 | 16 | 54 | 38 | 93 | 86 |
| 27 | 34 | 30 | 72 | 60 | 120 | 99 |
| 28 | 17 | 7 | 59 | 28 | 101 | 75 |
| 29 | 17 | 14 | 48 | 42 | 88 | 86 |
| 30 | 11 | 12 | 32 | 34 | 82 | 82 |
| 31 | 8 | 7 | 32 | 31 | 67 | 60 |
| 32 | 5 | 6 | 15 | 17 | 43 | 50 |
| 33 | 5 | 7 | 12 | 11 | 41 | 33 |
| 34 | 4 | 10 | 12 | 21 | 25 | 34 |
| 35 | 2 | 9 | 6 | 19 | 18 | 39 |

Set overlaps (intersection/k): `{"1000": 0.0, "200": 0.0, "500": 0.0}`.

Frozen cell: `{"broken": 2, "gain": 1.0, "k": 200, "successes": {"JavaScript": 0, "Python": 15}, "variant": "deactivate-other"}`.

| k | g | Variant | Python /16 | JS /16 | Broken /32 |
|---:|---:|---|---:|---:|---:|
| 200 | 0.5 | both | 14 | 0 | 3 |
| 200 | 1.0 | both | 13 | 0 | 4 |
| 200 | 2.0 | both | 9 | 1 | 19 |
| 200 | 1.0 | deactivate-other | 15 | 0 | 2 |
| 500 | 0.5 | both | 14 | 0 | 3 |
| 500 | 1.0 | both | 14 | 0 | 3 |
| 500 | 2.0 | both | 11 | 1 | 16 |
| 500 | 1.0 | deactivate-other | 15 | 0 | 2 |
| 1000 | 0.5 | both | 14 | 0 | 3 |
| 1000 | 1.0 | both | 14 | 0 | 4 |
| 1000 | 2.0 | both | 5 | 1 | 23 |
| 1000 | 1.0 | deactivate-other | 15 | 0 | 2 |

This neuron-counting and scaling construction did not meet the pre-written feasibility threshold. This does not rule out other neuron selectors or interventions.

Check 40 stopped on cost before competence or expert extraction: measured 16.02 tokens/s; its prescribed reduced design projected 7.56 hours against a four-hour cap. It has no behavioral result to compare. This dense-MLP check uses a smaller model, a different intervention, and the original 531030a task bank.

records.jsonl preserves text, tokens, complete histories, parser/task/breakage flags and timing; profile task files preserve neuron counts in the original run. Generated programs are parsed, never executed.

## Interpretation and verification

Qwen3-4B could produce both languages when asked, but this neuron-counting construction did not provide language control. The frozen 200-neuron deactivate-other cell produced **0/64 JavaScript at SET, 0/64 at HOLD, 63/64 Python at SWITCH, and 0/64 JavaScript at BACK**. Every fresh screen default was Python (64/64); OFF also gave 64/64 Python at SWITCH, so the successful Python count reflects the default language. Correct had 4/64 broken episodes versus 2/64 for OFF and shuffled. Shuffled non-default outputs and correct CLEAR impositions were both 0/64. CLEAR stayed Python after an arm that never induced JavaScript.

Text cues reached **64/64 at every addressed stage**, with zero broken episodes; JavaScript persisted at CLEAR on 25/64 tasks whose fresh defaults were Python. Coarse task passes remain separate from language identity: for example, correct SET/SWITCH were 60/64 and 58/64, while text-cue SET/SWITCH were 55/64 and 61/64. These checks establish syntactic plausibility, not semantic correctness.

No setup cell induced both languages. The strongest amplification (g=2) produced only 1/16 valid JavaScript response at each k and broke 19/32, 16/32, and 23/32 responses for k=200, 500, and 1000 respectively. All correct-set overlaps were zero and all selected specificity scores were positive; the small-set winner was chosen by the frozen breakage/tie rules. This is a negative result for the specified selector and intervention, with no claim about all possible neuron selectors.

Charged GPU allocation was **5031.579599860124 seconds (83.86 minutes)**, including the preserved 46.37001516507007-second empty first attempt; no cap overrun. Check 40 ended on a throughput cost stop before behavior was measured, so it supplies no behavioral comparison (details above).

Both CPU audits passed for all 2,528 records: complete rescoring and summary reproduction; profile frequencies, entropy, neuron sets and grid choice recomputation; exact prompt-token/hash and answer-text reconstruction; every retained history pair; arm cues/scaling flags; frozen scaling tensors; launch-commit bytes; and the cumulative GPU charge. Receipts were computed outside the repository while another quick check held its lock, then copied byte-identically. See `audit.json`, `audit-extra.json`, their console logs and `audit-extra.py`; the initial lock refusal is retained in `audit-lock-wait.txt`. No CUDA context was initialized by these audits.

Binary artifacts: each `profiles-by-task/*.pt` stores int64 positive-activation counts of shape [36,9728] and its generated-position denominator. `profiles.pt` stores Python/JavaScript frequencies [2,36,9728], counts, normalized entropy [36,9728], and specificity [2,36,9728] as fp64 tensors. `frozen-scales.pt` stores correct/shuffled fp32 multipliers [2,36,9728] and the selected cell. `neuron-sets.json` records indices, per-layer sizes, overlaps and shuffled RNG; `grid.json` records all 12 cells and its pre-screen freeze. The raw `target` field names the stage address; pre-screen competence/grid directions are identified by their cue/arm fields.
