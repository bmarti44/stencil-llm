# Quick check 33 (Q3): task-coordinate replacement

Unregistered, disclosed quick check; 2026-09-05; seed 33033. Source: hypotheses-astra.md #3 and check31-review-fable.md item 8. User authorization supersedes the old Q3 queue contingency. GPU initially idle: nvidia-smi reported no compute apps and 0% utilization. Foreground only, no process signals, 90 cumulative GPU-minutes including loading, 4B first.

## Fixed reading — written before execution

For EACH variant, PASS requires correct >=40/64 joint value-exact SET+HOLD+SWITCH+BACK; text-cue bar >=48/64 joint (otherwise INELIGIBLE); swapped >=40/64 following B/B/A/B; shuffled induction <=8/64 AND shuffled breakage <=8/64; correct breakage <=2/64; correct CLEAR task impositions <=2/64. MARGINAL requires correct SET >=32/64 and shuffled induction <=8/64, with an eligible text bar. FAIL otherwise. Incomplete required matrices are PARTIAL, never scientific negatives. The overall trunk reading is the best eligible variant, with both variants explicitly reported. One-shot HOLD without reapplication is the mechanism measurement. If retained text joint <48/64, run a fresh-history text bar (each decision independently cued); this diagnostic cannot rescue the fixed eligibility rule. Thresholds never change after observing results.

Induction means output equals A OR B on ANY of the first four decisions, counted per episode (the conservative interpretation of the shuffled limit). Breakage means ANY of five outputs cannot be parsed as one integer list, truncates at 64 output tokens, repeats a 4-gram with fraction >0.2, or duplicates an integer. Value-exact accepts one bracketed list embedded in prose, fences, or quoted integer entries; never changes values/signs/order. Strict JSON integer-list exactness is also recorded. Exactness and breakage are reported separately, as in check 32. CLEAR requests copy with all hooks removed; an A/B output is an imposition.

## Frozen design, implementation choices, and lineage

Extraction-on = 128 fresh operand-paired A/B/OFF triples per trunk; selection-on = 32 separate lists per trunk; evaluation-on = 64 fresh episodes per trunk, FIVE new lists per episode. All unordered operand sets are disjoint across splits and trunks, drawn from independent SHA-256-derived streams rooted at seed 33033. Lists have 5–8 distinct integers from -20..20. Reject ascending and descending inputs, conservatively implementing the already-in-task-form exclusion and keeping A/B/copy targets distinct. No benchmark inputs/responses or old check examples are used; no sealed IFEval/BFCL contents are accessed. Mean extraction changes no model parameters.

Reuse focus1_probe's non-thinking chat template, GPU precheck, atomic JSON writer, Qwen residual-hook/cache plumbing, and strict scorer; use check32_kv's format-lenient scorer. Cue A is “Sort these integers in ascending order.”; B is “Reverse these integers in their input order.”; OFF is “Process these integers.” Each asks for only a JSON array. Fit captures fp32 final-prompt layer-input residuals at zero-based L=8,12,16,20. Save states, means, unit contrasts, projections, paired minimum margin, and (c_OFF-c_B)/(c_A-c_B).

Actuator: h' = h + clip(target - u·h, -d, d)u, d=abs(c_A-c_B), target=c_task + overshoot*(c_task-c_OFF), overshoot in {0,0.5}. Arithmetic fp32 then cast to bf16; only the selected direction changes before unavoidable cast rounding. Log projected coordinates, signed displacement, clipping, and orthogonal residual caused by casting. Sustained applies at each query's final prompt token and all decoding tokens including EOS; across HOLD filler it also applies to all 128 neutral filler tokens. Other prompt/wrapper/closure tokens are untouched. One-shot applies only at final prompt positions of SET, SWITCH, BACK; HOLD receives zero hooks including filler and decoding. Setup tests immediate A and B in fresh contexts for each layer/dose/variant, with one-shot at the final prompt token only. Select independently per variant by (paired lists where BOTH tasks induced, then fewer broken outputs, then higher weaker-task count, then higher total exact); ties prefer lower layer then lower overshoot. Report all 16 cells.

Test arms: sustained and one-shot each have correct, swapped, shuffled; shared OFF and retained text-cue bar. Shuffled uses a fixed independent random unit vector per episode/variant (own RNG stream), the same target scalars and clip bound as correct, with its OWN projected coordinate in the replacement formula. This matches the clip magnitude, not necessarily the realized displacement; both are logged. Text bar explicitly cues SET/SWITCH/BACK and relies on retained instruction history for HOLD, matching check 32's no-new-cue HOLD. Fresh text bar explicitly cues every checkpoint. All arms retain full generated tokens including EOS, add a 128-token neutral filler turn before HOLD, and stop applying at CLEAR. No task cue text in actuator arms. All test arms use paired operands. Deterministic greedy bf16 HF-compatible Qwen; equal-length requests may be batched without padding; after EOS each row's cache is trimmed to its actual history, discarding any unused batched computation. Batch partition and absolute hook positions are recorded.

## Results

Both trunks completed in **52.07 cumulative GPU-minutes**, 4B first. The fixed reading above is unchanged; before-run.md preserves the exact hashed pre-run file. No process was signalled and no benchmark data was accessed.

Counts below are out of 64 episodes; swapped is scored against B/B/A/B. “Any induction” means A or B output at any of the first four checkpoints. Broken means any of five outputs. Fresh text is diagnostic only.

### 4b: sustained **INELIGIBLE**, one-shot **INELIGIBLE**

| Arm | SET | HOLD | SWITCH | BACK | Joint | Strict joint | CLEAR copy | Impositions | Broken | Any induction |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| sustained_correct | 0 | 0 | 0 | 0 | 0 | 0 | 64 | 0 | 0 | 0 |
| sustained_swapped | 0 | 0 | 1 | 0 | 0 | 0 | 64 | 0 | 0 | 1 |
| sustained_shuffled | 0 | 0 | 0 | 0 | 0 | 0 | 64 | 0 | 0 | 0 |
| one_shot_correct | 0 | 0 | 0 | 0 | 0 | 0 | 64 | 0 | 0 | 0 |
| one_shot_swapped | 0 | 0 | 0 | 0 | 0 | 0 | 64 | 0 | 0 | 0 |
| one_shot_shuffled | 0 | 0 | 0 | 0 | 0 | 0 | 64 | 0 | 0 | 0 |
| off | 0 | 0 | 0 | 0 | 0 | 0 | 64 | 0 | 0 | 0 |
| text | 45 | 48 | 52 | 62 | 34 | 34 | 64 | 0 | 3 | 64 |
| fresh_text | 45 | 41 | 15 | 51 | 7 | 4 | 63 | 0 | 3 | 62 |

Strict exactness by checkpoint:

| Arm | SET | HOLD | SWITCH | BACK | CLEAR |
|---|---:|---:|---:|---:|---:|
| sustained_correct | 0 | 0 | 0 | 0 | 64 |
| sustained_swapped | 0 | 0 | 1 | 0 | 64 |
| sustained_shuffled | 0 | 0 | 0 | 0 | 64 |
| one_shot_correct | 0 | 0 | 0 | 0 | 64 |
| one_shot_swapped | 0 | 0 | 0 | 0 | 64 |
| one_shot_shuffled | 0 | 0 | 0 | 0 | 64 |
| off | 0 | 0 | 0 | 0 | 62 |
| text | 45 | 47 | 52 | 62 | 64 |
| fresh_text | 45 | 41 | 9 | 51 | 63 |

The retained text bar achieved 34/64 joint, while fresh-history text achieved 7/64. With these frozen prompts, the fresh bar also misses 48/64, so retained-history stickiness alone does not explain the missed competence bar. Sustained replacement achieved 0/64 joint and 0/64 SET; one-shot achieved 0/64 joint and **0/64 HOLD with zero reapplication**. Neither actuator established either task on any test checkpoint, so this tested coordinate is readable but did not provide usable task control. Both variants remain INELIGIBLE under the frozen rule. Correct CLEAR impositions were 0/64 sustained and 0/64 one-shot; with no task established, clean copying does not demonstrate successful erasure. Runtime: 33.77 GPU-minutes.

Fit statistics (128 paired triples; fp32; zero-based layer inputs):

| Layer | c_A | c_B | c_OFF | d | Min paired margin | Positive pairs | Global gap | OFF fraction B→A |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 8 | -1.08553 | -2.8323 | -1.65576 | 1.74678 | 1.62275 | 128/128 | 1.29888 | 0.673554 |
| 12 | 4.94291 | 1.46355 | 3.55366 | 3.47936 | 3.28465 | 128/128 | 3.00142 | 0.600715 |
| 16 | -2.74931 | -7.61333 | -3.50415 | 4.86402 | 4.66663 | 128/128 | 3.99691 | 0.844812 |
| 20 | 9.17047 | 1.05948 | 7.74753 | 8.11099 | 7.48981 | 128/128 | 6.71591 | 0.824566 |

All setup cells (each task n=32; both means paired exact success; breakage counts out of 64 outputs):

| Variant | Layer | Overshoot | A | B | A strict | B strict | Both | Broken | Selected |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| sustained | 8 | 0.0 | 0 | 0 | 0 | 0 | 0 | 0 | yes |
| sustained | 8 | 0.5 | 0 | 0 | 0 | 0 | 0 | 0 |  |
| sustained | 12 | 0.0 | 0 | 0 | 0 | 0 | 0 | 0 |  |
| sustained | 12 | 0.5 | 0 | 0 | 0 | 0 | 0 | 0 |  |
| sustained | 16 | 0.0 | 0 | 0 | 0 | 0 | 0 | 0 |  |
| sustained | 16 | 0.5 | 0 | 0 | 0 | 0 | 0 | 0 |  |
| sustained | 20 | 0.0 | 0 | 0 | 0 | 0 | 0 | 3 |  |
| sustained | 20 | 0.5 | 0 | 0 | 0 | 0 | 0 | 2 |  |
| one_shot | 8 | 0.0 | 0 | 0 | 0 | 0 | 0 | 0 | yes |
| one_shot | 8 | 0.5 | 0 | 0 | 0 | 0 | 0 | 0 |  |
| one_shot | 12 | 0.0 | 0 | 0 | 0 | 0 | 0 | 0 |  |
| one_shot | 12 | 0.5 | 0 | 0 | 0 | 0 | 0 | 0 |  |
| one_shot | 16 | 0.0 | 0 | 0 | 0 | 0 | 0 | 0 |  |
| one_shot | 16 | 0.5 | 0 | 0 | 0 | 0 | 0 | 0 |  |
| one_shot | 20 | 0.0 | 0 | 0 | 0 | 0 | 0 | 1 |  |
| one_shot | 20 | 0.5 | 0 | 0 | 0 | 0 | 0 | 1 |  |

CPU reconstruction passed for all 3,904 records: raw scoring, source/reading hashes, fit means/projections, all-cell selection, retained token histories including EOS, exact hook schedules, clipping, random RNG streams and aggregate verdicts. 57,877/57,877 hook events changed at least one bf16 element; maximum orthogonal cast residual norm was 0.150798. Replacement is direction-only before casting; bf16 rounding means the realized displacement is not mathematically confined to that direction.

Matched empty-history SET prompts produced identical output token sequences in 64/64 retained/fresh pairs and identical scores in 64/64. Any disagreement here is a batch/numerical difference, not a history effect.

### 1.7b: sustained **INELIGIBLE**, one-shot **INELIGIBLE**

| Arm | SET | HOLD | SWITCH | BACK | Joint | Strict joint | CLEAR copy | Impositions | Broken | Any induction |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| sustained_correct | 1 | 0 | 0 | 2 | 0 | 0 | 62 | 0 | 2 | 2 |
| sustained_swapped | 0 | 0 | 1 | 0 | 0 | 0 | 63 | 0 | 1 | 2 |
| sustained_shuffled | 1 | 0 | 0 | 2 | 0 | 0 | 60 | 0 | 4 | 2 |
| one_shot_correct | 1 | 0 | 0 | 3 | 0 | 0 | 61 | 0 | 3 | 3 |
| one_shot_swapped | 0 | 0 | 1 | 0 | 0 | 0 | 62 | 0 | 2 | 3 |
| one_shot_shuffled | 0 | 0 | 0 | 3 | 0 | 0 | 61 | 0 | 3 | 3 |
| off | 1 | 0 | 0 | 2 | 0 | 0 | 61 | 0 | 3 | 2 |
| text | 48 | 45 | 14 | 54 | 7 | 0 | 64 | 0 | 3 | 64 |
| fresh_text | 48 | 48 | 11 | 54 | 6 | 0 | 64 | 0 | 12 | 64 |

Strict exactness by checkpoint:

| Arm | SET | HOLD | SWITCH | BACK | CLEAR |
|---|---:|---:|---:|---:|---:|
| sustained_correct | 1 | 0 | 0 | 2 | 62 |
| sustained_swapped | 0 | 0 | 1 | 0 | 63 |
| sustained_shuffled | 1 | 0 | 0 | 2 | 60 |
| one_shot_correct | 1 | 0 | 0 | 3 | 61 |
| one_shot_swapped | 0 | 0 | 1 | 0 | 62 |
| one_shot_shuffled | 0 | 0 | 0 | 3 | 61 |
| off | 1 | 0 | 0 | 2 | 61 |
| text | 1 | 43 | 12 | 52 | 62 |
| fresh_text | 1 | 1 | 0 | 1 | 64 |

The retained text bar achieved 7/64 joint, while fresh-history text achieved 6/64. With these frozen prompts, the fresh bar also misses 48/64, so retained-history stickiness alone does not explain the missed competence bar. Sustained replacement achieved 0/64 joint and 1/64 SET; one-shot achieved 0/64 joint and **0/64 HOLD with zero reapplication**. OFF itself produced A/B-form output in 2/64 episodes, versus 2/64 sustained and 3/64 one-shot. Both variants remain INELIGIBLE under the frozen rule. Correct CLEAR impositions were 0/64 sustained and 0/64 one-shot. Runtime: 18.27 GPU-minutes.

Fit statistics (128 paired triples; fp32; zero-based layer inputs):

| Layer | c_A | c_B | c_OFF | d | Min paired margin | Positive pairs | Global gap | OFF fraction B→A |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 8 | -2.02079 | -6.11507 | -2.83703 | 4.09428 | 3.75352 | 128/128 | 3.06466 | 0.800638 |
| 12 | -11.6716 | -26.4545 | -10.1175 | 14.7829 | 13.631 | 128/128 | 11.5339 | 1.10513 |
| 16 | 21.0364 | -22.2943 | 16.1468 | 43.3307 | 40.7846 | 128/128 | 35.4548 | 0.887156 |
| 20 | 123.404 | -155.411 | 104.554 | 278.815 | 256.688 | 128/128 | 225.18 | 0.932391 |

All setup cells (each task n=32; both means paired exact success; breakage counts out of 64 outputs):

| Variant | Layer | Overshoot | A | B | A strict | B strict | Both | Broken | Selected |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| sustained | 8 | 0.0 | 0 | 0 | 0 | 0 | 0 | 0 | yes |
| sustained | 8 | 0.5 | 0 | 0 | 0 | 0 | 0 | 0 |  |
| sustained | 12 | 0.0 | 0 | 0 | 0 | 0 | 0 | 7 |  |
| sustained | 12 | 0.5 | 0 | 0 | 0 | 0 | 0 | 6 |  |
| sustained | 16 | 0.0 | 0 | 0 | 0 | 0 | 0 | 0 |  |
| sustained | 16 | 0.5 | 0 | 0 | 0 | 0 | 0 | 0 |  |
| sustained | 20 | 0.0 | 0 | 0 | 0 | 0 | 0 | 3 |  |
| sustained | 20 | 0.5 | 0 | 0 | 0 | 0 | 0 | 17 |  |
| one_shot | 8 | 0.0 | 0 | 0 | 0 | 0 | 0 | 0 | yes |
| one_shot | 8 | 0.5 | 0 | 0 | 0 | 0 | 0 | 0 |  |
| one_shot | 12 | 0.0 | 0 | 0 | 0 | 0 | 0 | 0 |  |
| one_shot | 12 | 0.5 | 0 | 0 | 0 | 0 | 0 | 0 |  |
| one_shot | 16 | 0.0 | 0 | 0 | 0 | 0 | 0 | 0 |  |
| one_shot | 16 | 0.5 | 0 | 0 | 0 | 0 | 0 | 0 |  |
| one_shot | 20 | 0.0 | 0 | 0 | 0 | 0 | 0 | 0 |  |
| one_shot | 20 | 0.5 | 0 | 0 | 0 | 0 | 0 | 0 |  |

CPU reconstruction passed for all 3,904 records: raw scoring, source/reading hashes, fit means/projections, all-cell selection, retained token histories including EOS, exact hook schedules, clipping, random RNG streams and aggregate verdicts. 59,443/59,443 hook events changed at least one bf16 element; maximum orthogonal cast residual norm was 1.53114. Replacement is direction-only before casting; bf16 rounding means the realized displacement is not mathematically confined to that direction.

Matched empty-history SET prompts produced identical output token sequences in 62/64 retained/fresh pairs and identical scores in 62/64. Any disagreement here is a batch/numerical difference, not a history effect.

### Artifacts and limits

Per trunk: summary.json, records.jsonl (all setup/test outputs and hook positions), examples.json, extraction.json, fit-stats.json, fit-fp32.pt (states/means/unit vectors), cells.json, selected.json, random-directions.pt, pilot.json, and validation.json. audit.py independently reconstructs measurements on CPU; report.py renders these tables. Source script and imported plumbing hashes are in provenance.json. No model weights changed.

Shuffled matches the clip bound, not the realized displacement or intervention energy. One-shot HOLD retains prior generated answers as well as edited KV; a positive result would not isolate these sources without an identical-token replay control. The text bar uses no new HOLD cue, while fresh text is explicitly cued at each independent decision. These are descriptive single-seed screens, not registered hypothesis tests or broad impossibility claims.
