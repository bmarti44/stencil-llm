# Quick check 31 — UNREGISTERED FOCUS-1 steering feasibility probe

Brian approved, 2026-09-05. Probe seed **31031**. This probe has no bearing on
registered FOCUS-1 fitting, training, or selection. Fit-on: 32 new synthetic
operand-paired triples; evaluated-on: separate 32 competence and 16 steering
lists. Splits are disjoint by unordered operand set; no benchmark inputs or
recorded benchmark responses are used. Both trunks share these probe-only lists.

Write-ahead: run `scripts/focus1_probe.py --trunk 1.7b`, then `--trunk 4b`,
foreground, at most 30 minutes of GPU wall time each, including loading.
GPU checked idle; no running review/coder wrapper. Historical process/ledger
files are under `archive/plan/`; user scope takes precedence over historical
ledger edits. Outputs and progress are confined here. Full responses are saved
incrementally, including prompt IDs, generated IDs, hook positions and scores.

Layers mean zero-based layer inputs. Prompts use the local Qwen chat envelope
with thinking disabled. Greedy decoding, 48-token cap, bf16 trunk with
`hf_compatible` enabled everywhere; fp32 vectors and addition before bf16 cast.
Lists contain 5–8 distinct integers sampled from −20…20 and exclude already
ascending/descending permutations. Exact match means an integer-only JSON array
with precisely the expected sequence (JSON whitespace is immaterial).
Breakage is syntactically invalid JSON, hitting the token cap, repeated integer
entries, or repeated-token-4gram fraction >0.2; flags may overlap.

Correct and swapped are views of the same actual injection on identical inputs;
OFF is likewise computed once per held list and reused. Reports expose both
requested-target and actual-injected-target rates. The descriptive best shared
cell maximizes the weaker task, then total hits, then fewer strict output failures (including schema), prioritizing
cells meeting the FEASIBLE rule. FEASIBLE means both correct tasks ≥12/16 and
breakage ≤1/16 each at the same layer/alpha; OFF-relative flips are reported
separately, and an already-default task need not improve. Otherwise MARGINAL means
weaker-task success ≥8/16 or incomplete data; INFEASIBLE means below that.
The delay diagnostic tests both directions at one best shared cell, with only
the final prompt-token addition; decoding hooks are off and prompt KV retained.
This is prompt-only persistence, with no neutral delay interval inserted.

The first 1.7B scoring pass grouped integer-schema failures under invalid JSON.
After generation, this was corrected from saved responses: JSON syntax and
integer schema are separate fields, and breakage uses syntax/truncation/repetition.
Exact-match labels, the original strict-output-failure tie-break, chosen delay
cell and verdict are unchanged. Original row scores, summary and execution source
are retained under `1.7b/`; 4B uses the corrected scorer from the outset.

| Trunk | Cue asc /32 | Cue desc /32 | No-cue competence A/D/C/O /32 | Held OFF A/D/C/O /16 | Best shared L, α | Delay asc/desc /16 | GPU min | Reading |
|---|---:|---:|---|---|---|---|---:|---|
| 1.7b | 0 | 0 | 0/0/26/6 | 0/0/12/4 | 12, 0.5 | 0/0 | 5.33 | **INFEASIBLE** |
| 4b | 27 | 30 | 0/0/30/2 | 0/0/16/0 | 16, 2 | 0/0 | 9.73 | **INFEASIBLE** |

**1.7B — INFEASIBLE on this probe.** Visible cues scored 0/32 for both tasks under
strict integer-array exact match. The diagnostic allowing quoted integer strings
recovers 28/32 ascending but only 10/32 descending sequences: formatting explains
much of ascending failure, while descending also has substantial value/order errors.
Cue-absent behavior mostly copies (26/32 competence; 12/16 held). All 18 sustained
injection directions scored zero exact task successes, as did both prompt-only
directions. Asc/desc vectors are highly aligned (cosine 0.894–0.965). The descriptive
tie-break selects L12, α=0.5, but this cell induces neither task; it is not promising.

**4B — INFEASIBLE on this probe.** Visible cues scored 27/32 ascending and 30/32
descending with no breakage; cue-absent held inputs copied 16/16. Nevertheless,
all 18 sustained injection directions and both prompt-only directions scored
zero exact task successes. The task vectors are even more aligned (0.971–0.980).
4B is the better competence baseline, but no tested cell looks useful for task
steering. L16, α=2 wins only the descriptive tie-break. Since sustained steering
never induced either skill, the delay result does not establish a retention limit.

These are completed, unregistered feasibility measurements for these particular
prompts, operands, layers and strengths. They do not determine the registered
FOCUS-1 outcome, justify choosing its configuration, or rule out other steering methods.

All table entries below are counts out of 16. A/D/C/O = exact ascending / exact
descending / copy / other. B = breakage; S = valid JSON with the wrong integer-array
schema. B and S may overlap. For target asc, v_asc is correct and v_desc swapped;
for target desc those roles reverse. OFF is given above and reused in every cell.
The JSON summaries additionally contain every arm’s rates and paired wins/losses
versus OFF, including rates relative to the actual injected direction.

| Trunk | Layer | α | v_asc: A/D/C/O | B | S | v_desc: A/D/C/O | B | S |
|---|---:|---:|---|---:|---:|---|---:|---:|
| 1.7b | 12 | 0.5 | 0/0/11/5 | 1 | 3 | 0/0/11/5 | 0 | 4 |
| 1.7b | 12 | 1 | 0/0/9/7 | 0 | 7 | 0/0/7/9 | 2 | 7 |
| 1.7b | 12 | 2 | 0/0/12/4 | 3 | 0 | 0/0/2/14 | 13 | 0 |
| 1.7b | 16 | 0.5 | 0/0/7/9 | 1 | 7 | 0/0/4/12 | 1 | 10 |
| 1.7b | 16 | 1 | 0/0/1/15 | 0 | 15 | 0/0/0/16 | 0 | 16 |
| 1.7b | 16 | 2 | 0/0/0/16 | 0 | 16 | 0/0/0/16 | 2 | 14 |
| 1.7b | 20 | 0.5 | 0/0/4/12 | 1 | 11 | 0/0/3/13 | 0 | 13 |
| 1.7b | 20 | 1 | 0/0/0/16 | 1 | 15 | 0/0/0/16 | 4 | 12 |
| 1.7b | 20 | 2 | 0/0/0/16 | 12 | 4 | 0/0/0/16 | 16 | 0 |
| 4b | 12 | 0.5 | 0/0/12/4 | 0 | 4 | 0/0/12/4 | 0 | 4 |
| 4b | 12 | 1 | 0/0/8/8 | 0 | 8 | 0/0/8/8 | 0 | 8 |
| 4b | 12 | 2 | 0/0/8/8 | 0 | 8 | 0/0/8/8 | 0 | 8 |
| 4b | 16 | 0.5 | 0/0/11/5 | 0 | 5 | 0/0/10/6 | 0 | 6 |
| 4b | 16 | 1 | 0/0/14/2 | 0 | 2 | 0/0/10/6 | 0 | 6 |
| 4b | 16 | 2 | 0/0/16/0 | 0 | 0 | 0/0/16/0 | 0 | 0 |
| 4b | 20 | 0.5 | 0/0/15/1 | 0 | 1 | 0/0/16/0 | 0 | 0 |
| 4b | 20 | 1 | 0/0/16/0 | 0 | 0 | 0/0/16/0 | 0 | 0 |
| 4b | 20 | 2 | 0/0/16/0 | 0 | 0 | 0/0/16/0 | 0 | 0 |

| Trunk | Layer | ‖v_asc‖ | ‖v_desc‖ | Cosine |
|---|---:|---:|---:|---:|
| 1.7b | 12 | 13.2026 | 14.7264 | 0.965020 |
| 1.7b | 16 | 31.9283 | 34.0522 | 0.949750 |
| 1.7b | 20 | 103.7918 | 115.5136 | 0.893702 |
| 4b | 12 | 3.5262 | 3.4461 | 0.971285 |
| 4b | 16 | 6.1170 | 5.7859 | 0.980094 |
| 4b | 20 | 9.5005 | 9.3444 | 0.973361 |

Artifacts: each trunk has `summary.json`, complete `records.jsonl`, `examples.json`,
`extraction.json`, `extraction-states.pt`, `vectors.pt`, and format diagnostics.
The residual archive stores three tasks × three layers × 32 fp32 vectors; vector
width is 2048 for 1.7B and 2560 for 4B. `vectors.pt` stores six fp32 mean differences
keyed `task:layer`. All are probe-only, with no registered consumer.

Validation: 864 generation records and 192 extraction prompts audited; all prompts
and decoded text match stored token IDs, all caps/hooks match the requested schedule,
all scores and summary cells recompute, and all 12 saved vectors exactly match
independently recomputed means of the saved paired residuals. Both runs completed
within their 30-minute caps; final `nvidia-smi` showed no compute processes.
CPU smoke checks cover import safety, split separation, exact scoring, syntax/schema
distinction, breakage, arm semantics and shared-cell selection; script lint passes.
See `validation.json` for audited counts and artifact SHA-256 hashes.
