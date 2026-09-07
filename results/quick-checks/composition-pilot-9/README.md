Fit-on: none; development-on: eight DEV episodes and prior failure audits; evaluated-on: none; fresh64 remains model-unopened until the separate frozen launch.

# Amendment 6b — FIX-CONFIRMED

Pinned code: `1e093a46b426f30cf8a615bab431d4890d0ce66e`. 512 records and 512 HTTP responses audited. Every saved prompt, feedback, executor result, score, text/token/EOS/cap record and local hash reproduced. GPU held **0.3893 hours**; own container/flag cleanup recorded.

Failed pilot items: none.

| Arm | Records | Executing lanes | Initial round-zero rejections | Initial / surviving syntax | Repairs | Broken episodes | Final semantic integration |
|---|---:|---:|---:|---:|---:|---:|---:|
| R | 128 | 8 | 0 | 0 / 0 | 0 | 0 | 3 |
| N | 128 | 8 | 0 | 0 / 0 | 0 | 0 | 4 |
| T | 128 | 8 | 0 | 0 / 0 | 0 | 0 | 4 |
| Q | 128 | 8 | 0 | 0 / 0 | 0 | 0 | 8 |

Breakage is syntax/protocol failure; semantic wrong values and runtime test exceptions are integration failures, reported separately. Repair counts distinguish initial failures from final breakage; a zero repair count supplies no GPU evidence of repair efficacy.

| Primary family | Paired episodes | R wins / N wins / ties | Mean gain | One-sided p | Holm p | Missing-write-as-failure gain |
|---|---:|---:|---:|---:|---:|---:|
| delivery | 8 | 6/0/2 | 0.75 | 0.015625 | 0.046875 | 0.75 |
| format | 8 | 4/0/4 | 0.5 | 0.0625 | 0.125 | 0.5 |
| indent | 8 | 1/2/5 | -0.125 | 0.875 | 0.875 | -0.125 |

Unchanged primary: scheduled first-applicable change rounds, common parsed writes, within-episode averaging, exact one-sided R>N sign test, Holm across three families. Delivery alone powers the full-run primary verdict. DEV significance never gates FIX-CONFIRMED. Negative directions and missingness remain part of the result.

| Harm contrast | Common-attempt episodes | Greater / lower / ties | Holm p | Coverage | Harm signal |
|---|---:|---:|---:|---|---|
| R:N | 6 | 0/0/6 | 1 | True | False |
| T:N | 6 | 0/0/6 | 1 | True | False |

Coverage remains75% in both contrasts (6/8 DEV,48/64 full run). All8 DEV schedules have two indent-change opportunities; the CPU scoped negative control reaches8/8. Thus the gate is achievable and was retained. Conditional risk excludes non-attempts; this selected-population comparison is neither a causal adjustment nor noninferiority evidence. T:N is the block-free reminder negative control.

The original95fa7fc0 FAIL remains frozen, untouched and unrescored. Its registered one-adversarial-flip format fragility caveat remains. Successor significance fragility (episode R-win to N-win, recompute Holm-3): indent: 0, format: 0, delivery: 1; zero means already nonsignificant. See flip-sensitivity.json.

Measured full-run projection: **2.6137 GPU-hours**, including25% main reserve and1200s controls/cleanup. Harm calibration eligible: **True**. Frozen64 launch additionally requires this receipt and its source/hash binding committed first.

Determinism8/8 exact, C4 forward/reverse. The40 fixed pilot7-payload cross-container replay belongs to the full run and was not performed in this pilot. CPU166passed/1expected xfail; new protocol rejection tests failed on old feedback then passed after the repair.

Claim ceiling: bounded request-time rule restatement on one frozen trunk and authored distribution. No superiority-to-prose, removed-stale-influence, generalized coding competence, free-text admission or actuator claim. The scoped system example and accumulated old history remain possible influences.

Artifacts: [registration](REGISTRATION.md), [summary](summary.json), [audit](audit.json), [episode tables](episode-tables.json), [cost](cost-audit.json), records-R/N/T/Q.jsonl, receipts.json, local-hashes.json. Raw HTTP and loop journals remain local and hash-indexed. Explicit-path local commits; no push, host signals, or edits to original larger-test results.
