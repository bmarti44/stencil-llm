# Check43b — calibrated SUM/PRODUCT routing

**CLOSE concept-level routing on this trunk under the tested recipe.** The frozen
reading applies: executable PRODUCT **0/8 at both doses**, below MARGINAL's 3/8.
No safe setup cell exists. Final two-seed Python/JavaScript and collateral runs
were mechanically skipped; those capabilities remain unmeasured. This is an
operational stop, not proof that no other concept actuator could exist.

Unregistered, disclosed; gpt-6-astra, 2026-09-06 UTC. Fit/train: none. Profile-on:
all 32 committed check43 cued Python donor responses, without filtering. Select-on:
the same eight check43 setup prompts (development reuse). Fresh seeds96063/96064
and separate collateral96065 were authored and frozen but **not evaluated**.
The first eight previously successful check40c tasks were deliberately reused as
positive controls. No evaluation benchmark, sealed IFEval input or sealed BFCL
cohort was read. Frozen weights, fresh KV, greedy decoding, complete-program
bounded interpreter inherited unchanged from check43.

| Setup arm | Band norm | SUM /8 | PRODUCT /8 | Checker-malformed /8 |
|---|---:|---:|---:|---:|
| Neutral OFF, measured first | 0 | 8 | 0 | 0 |
| +b | 6.805823 | 8 | 0 | 0 |
| −b | 6.805823 | 7 | 0 | 0 |
| Shuffled +b | 6.805823 | 8 | 0 | 0 |
| Shuffled −b | 6.805823 | 7 | 0 | 0 |
| +b | 10.208735 | 7 | 0 | 1 |
| −b | 10.208735 | 7 | 0 | 0 |
| Shuffled +b | 10.208735 | 4 | 0 | 4 |
| Shuffled −b | 10.208735 | 7 | 0 | 0 |

**Same-runtime JS sanity: 8/8 valid unbroken JavaScript**, exceeding the required
6/8. This used the frozen 40c alpha3 actuator across all 48 layers, exactly as its
successful runtime recipe. Paired +SUM/−PRODUCT success is 0/8 at both doses.
The negative sign is the informative intervention against the measured SUM default.
No −b response contains `*=` or initializes its accumulator to `1`.
All 80 generations ended with EOS; there were no truncations or budget stops.

“Checker-malformed” follows the frozen contract, not just Python syntax: all five
such outputs are syntactically valid list-building functions (`[]`, `.append`,
list return), violating the required scalar reduction and interpreter allowlist.
The four remaining incorrect programs are executable SUM-like reductions with
wrong slice endpoints. All complete outputs and per-input executions are retained;
no checker relaxation or repaired-output score was applied.

## Profiles and magnitude

Teacher-forced raw router logits are saved at **every generated non-EOS token**
(48–62 tokens per donor). Identity literal index is **21 in all 32 donors**;
the primary window is **19,20,21** (` =`, space, `0`/`1`). Index22 (newline) and
operator indices37,40,41,44,47,50,51 are separately reported in the maps. Absolute
window-plus-newline positions vary with prompt length:159–162,162–165,167–170,
172–175. The review's exceptional first divergence at index18 is `a` versus `acc`,
not an earlier identity literal; assignment-based alignment fixes that distinction.

The primary statistic averages each donor's three positions, then averages the
16 donors equally per operation, takes (SUM−PRODUCT)/2, expert-centers and keeps
layers7–34. Identity-token router logits condition on that literal and predict its
successor; the preceding two positions predict the space and literal. This is a
profile around the decision, not an isolated causal intervention at one token.
Bias is sustained through prefill and decode, as frozen before outcomes.

Window unit band norm **5.094164**; identity-only diagnostic9.170836;
all-generated diagnostic1.379595. Only the window direction was screened.
Multipliers1.336004/2.004006 match frozen JS alpha2/3 band norms6.805823/10.208735.
The old check43 unit norm0.722413 would require multipliers9.421/14.131,
respectively: the roughly9x remark describes alpha2, not alpha3.
Actual bfloat16 band norms were6.805833/10.208892; maximum absolute float32 shifts
were0.694746/1.042120. Per-layer norms and maxima are in the magnitude audit.
The JS sanity uses full norm15.659565; its restriction to this band is10.208735.
Equal band norm is a magnitude reference and does not imply equal sensitivity.

| Decode observations, layers7–34 | Changed top-8 set fraction | Mean mixture-weight L1 |
|---|---:|---:|
| −b, norm6.81 | 63.01% | 0.2023 |
| −b, norm10.21 | 77.82% | 0.2951 |
| JS sanity, band subset | 77.30% | 0.3627 |

These are comparisons against original routing at the same current hidden inputs,
not independent samples or cross-trajectory causal mediation. Prefill changes,
both signs and both stable shuffled controls are recorded in the detailed audit.
All concept changes stay within layers7–34; actual expert-consumer indices and
weights match the returned router tuple, with zero mismatches. Plus/minus token
sequences match6/8 and5/8; minus/OFF match7/8 and6/8. Thus the calibrated actuator
changes dispatch substantially and sometimes changes output, without selecting
PRODUCT. This weakens the old under-dosing explanation at the tested magnitudes;
it does not identify why PRODUCT selection fails.

## Provenance, cost and validation

Recipe, banks, source and CPU fixtures were committed in **da131791 before any new
model outcome**. The grid, signs, stable seed96062 expert permutations and stop rule
were unchanged after launch. CPU preparation corrected identity alignment before
that commit; it produced no model outcomes. The prior check43 null stands.

**672.881907 seconds = 11.214698 GPU-min = 0.186912 GPU-h**, including load
383.428842 seconds, kernel checks, profiling and cleanup; setup cap1440 seconds.
Peak allocation57.648853 GiB. **80 generations /3963 generated tokens**, plus
32 teacher-forced donor forwards. Same-engine raw-slot contracts passed all48
layers; grouped_mm consumer/nonzero/OFF parity checks passed. Full greedy
OFF/unhooked replay was not repeated here; kernel OFF next-logit parity was tested.
RUNNING.flag was removed after natural completion. No signals, process termination,
background launch or push.

CPU audit recomputed 72 bounded concept scores and eight inherited JS parser/coarse
scores, all80 input/bias hashes, all32 saved
profiles, all three diagnostic directions, permutations, norm matching, dispatch
boundaries and the frozen reading. Native handwritten Python/JS checker parity:
32 variants ×43 lists =1376 comparisons; rejection and small-HF consumer fixtures
passed. Targeted selection/alignment/import tests:6 passed,1 existing legacy xfail.

Artifacts: [reading](prewritten-reading.md), [recipe hashes](recipe-freeze.json),
[banks](banks.json), [positions](profile-positions.json), [magnitude](magnitude.json),
[records](records.jsonl), [grid](grid.json), [summary](summary.json),
[score audit](audit.json), [tensor/dispatch audit](audit-details.json),
[CPU audit source](audit_artifacts.py), [console](console.log).
`profiles/*.pt` stores per-donor bfloat16 raw logits[48,generated_tokens,128],
IDs and position maps. `profiles.pt` stores float64 operation means[2,48,128],
float32 directions[48,128], the shuffle and int64 permutations[48,128]. These are
measurements, not trained checkpoints; CPU-only torch loading reproduces them.
