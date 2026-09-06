# Check43 — concept-level SUM/PRODUCT router SET

**FAIL / NO SAFE SET.** The three permitted doses each achieved **0/8 paired
SUM-and-PRODUCT setup successes**, below the required 6/8. Donor competence was
16/16 for each operation. The frozen stop rule ended the experiment after setup;
no dose was selected and no final or collateral responses were generated.

Unregistered, disclosed; gpt-6-astra, 2026-09-05. No weight fitting/training.
Profile-on: newly authored Python tasks, seed 95061. Dose selection: separate
Python tasks, seed 95062. Evaluation banks 95063/95064 were authored and frozen
but **not evaluated**. No benchmark, prior check40/41 task bank, sealed IFEval
input or sealed BFCL cohort was read. Consumer/parsers reuse verified check40b;
40c's pinned-runtime/raw-slot checks are reused, without its banks or directions.

| Alpha | +b SUM | −b PRODUCT | Paired success | Malformed, both signs |
|---|---:|---:|---:|---:|
| 1 | 7/8 | 0/8 | 0/8 | 0/16 |
| 2 | 7/8 | 0/8 | 0/8 | 0/16 |
| 3 | 7/8 | 0/8 | 0/8 | 0/16 |

Both signs at every dose produced seven exact SUM reductions and one terminating
SUM-like function with an incorrect exclusive slice endpoint. None passed PRODUCT.
Plus/minus token sequences were identical on 8/8, 8/8 and 7/8 prompts at doses
1, 2 and 3. All 81 scored generations ended with EOS; no truncation or malformed
reply occurred. These are setup measurements; final paired comparisons,
McNemar/Holm tests, language/seed-cell thresholds, collateral and JS transfer are
**untested**, not passes. Setup 0/8 has descriptive Wilson 95% interval [0, 0.3244]
at each dose; it is not a final-screen confidence claim.

The actuator did change routing. Per-sign changed top-8-set layer/token counts
were +/− 3414/3444 at alpha1, 6619/6583 at alpha2 and 9430/9472 at alpha3.
These compare biased versus original routing for the same current hidden inputs;
they are dispatch observations, not independent statistical units. Mixture-weight
changes and consumer equality are recorded separately in every generation.
All changes were inside layers 7–34. The shared four profile IDs
[279, 4583, 729, 13] decode to ` the complete function.`. All 32 per-example
four-token logit means, operation means, centered bias and seed95062 shuffle
recomputed exactly. Bias Frobenius norm is 0.7224128246; no norm amplification.

The source's narrow conclusion holds: **this Python-derived neutral-suffix router
difference, band and dose grid did not select PRODUCT**. This closes this bounded
SET screen. It does not rule out concept representations, stronger/different
actuators, or concept control generally; it supplies no JS-transfer or persistence
result. No higher dose, second actuator or failed-example replacement was attempted.

The reading, all 72 task prompts/input banks, checker, seeds and hook bindings
were committed in `a993adbc` before any model generation. The script would commit
profiles, selected dose, setup records and final hashes before final generation;
that branch was not reached because no dose qualified. Profiles and the complete
failed grid are preserved with this report. The script and original recipe hashes
remain unchanged after model outcomes.

Cost: **700.2435 seconds = 11.6707 GPU-min = 0.19451 GPU-h**, including model load
392.2796 seconds and a 3.3230-second unhooked replay; no 5400-second overrun.
Pilot 14.4241 tok/s projected 4406.4084 seconds (73.4401 min), so the matrix was
admitted within the cap. Actual peak allocated memory: 57.6381 GiB.
There are 81 scored records (32 donors + 48 grid + one reused setup text-SUM pilot),
4271 scored tokens, plus one separately saved 58-token OFF instrumentation replay:
**82 total generations / 4329 total tokens**. Remaining selected-dose controls,
224 final and 48 collateral generations were skipped by the setup stop rule.
Foreground only; RUNNING.flag removed after natural completion; no signals,
background launches, process termination, push or changes to Brian's server.

Validation: 32 hand-written function variants matched native Python/JavaScript
execution on 43 input lists each (1376 comparisons); unsupported/dead-branch,
nontermination, mutation, truncation and JS scope/const rejection fixtures passed.
Small-model actual-consumer/OFF tests passed. Real GPU grouped_mm/eager parity,
48 raw-logit router contracts and full greedy OFF/unhooked parity passed.
All 81 output scores were recomputed; input/KV/hook/bias hashes, dispatch-band
boundaries, source commit and early-stop reading independently checked.
Ruff passed; import guard: 3 passed, 1 existing xfail.

Artifacts: [frozen reading](prewritten-reading.md), [recipe bindings](recipe-freeze.json),
[banks](banks.json), [CPU fixtures](cpu.json), [records](records.jsonl),
[profiles](profiles.pt), [grid](grid.json), [summary](summary.json),
[record audit](audit.json), [detailed audit](audit-details.json),
[unhooked replay](unhooked-replay.json), [console](console.log).
Per-donor `.pt` files in `profiles/` contain task/operation, all prompt IDs, four
positions/IDs, float64 logit sums and their means (48×128), count=4. `profiles.pt`
contains float64 operation means (2×48×128), float32 bias/shuffle (48×128), int64
permutations (48×128) and shared token IDs. Both are measurements, not checkpoints.
