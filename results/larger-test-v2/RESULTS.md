Fit-on: none; development-on: eight DEV episodes and prior failure audits; evaluated-on: the fresh64 successor bank, one model pass. No benchmark inputs or responses.

# Amendment 6b — PASS

Pinned code: `e20c3f9bb9979ba95b9cc797115b742507a3803c`. 3328 records and 3333 HTTP responses audited. Every saved prompt, feedback, executor result, score, text/token/EOS/cap record and local hash reproduced. GPU held **2.1314 hours**; own container/flag cleanup recorded.

Failed full-run items: none.

**Residual failure:** R episode56 had five surviving `IndentationError`s at rounds10–14. All five syntax-repair responses repeated their initial submission verbatim: a two-space docstring followed by four-space statements raised `unexpected indent`. The harness preserved these bodies and recorded the failures. Round15 wrote successfully, but final semantic integration for this episode failed. The registered harm test counts this as one harmful episode; PASS does not establish a universal indentation fix or effective model self-repair. See [residual errors](residual-errors.json).

| Arm | Records | Executing lanes | Initial round-zero rejections | Initial / surviving syntax | Repairs | Broken episodes | Final semantic integration |
|---|---:|---:|---:|---:|---:|---:|---:|
| R | 1024 | 64 | 0 | 5 / 5 | 5 | 1 | 45 |
| N | 1024 | 64 | 0 | 0 / 0 | 0 | 0 | 48 |
| T | 1024 | 64 | 0 | 0 / 0 | 0 | 0 | 52 |
| Q | 256 | 16 | 0 | 0 / 0 | 0 | 0 | 16 |

Breakage is syntax/protocol failure; semantic wrong values and runtime test exceptions are integration failures, reported separately. Repair counts distinguish initial failures from final breakage; a zero repair count supplies no GPU evidence of repair efficacy.

| Primary family | Paired episodes | R wins / N wins / ties | Mean gain | One-sided p | Holm p | Missing-write-as-failure gain |
|---|---:|---:|---:|---:|---:|---:|
| delivery | 63 | 35/0/28 | 0.555556 | 2.91038305e-11 | 8.73114914e-11 | 0.53125 |
| format | 63 | 25/4/34 | 0.333333 | 5.18579036e-05 | 0.000103715807 | 0.3125 |
| indent | 64 | 17/15/32 | 0 | 0.430025033 | 0.430025033 | 0 |

Unchanged primary: scheduled first-applicable change rounds, common parsed writes, within-episode averaging, exact one-sided R>N sign test, Holm across three families. Delivery alone powers the full-run primary verdict. DEV significance never gates FIX-CONFIRMED. Negative directions and missingness remain part of the result. Episode56 supplies the one missing paired episode for delivery and format; their missing-write-as-failure gains remain positive. Indent mean gain is exactly zero, so this run supplies no indentation-adherence improvement evidence.

| Harm contrast | Common-attempt episodes | Greater / lower / ties | Holm p | Coverage | Harm signal |
|---|---:|---:|---:|---|---|
| R:N | 61 | 1/0/60 | 1 | True | False |
| T:N | 61 | 0/0/61 | 1 | True | False |

Coverage remains75% in both contrasts (6/8 DEV,48/64 full run). All8 DEV schedules have two indent-change opportunities; the CPU scoped negative control reaches8/8. Thus the gate is achievable and was retained. Conditional risk excludes non-attempts; this selected-population comparison is neither a causal adjustment nor noninferiority evidence. T:N is the block-free reminder negative control.

The original95fa7fc0 FAIL remains frozen, untouched and unrescored. Its registered one-adversarial-flip format fragility caveat remains. Successor significance fragility (episode R-win to N-win, recompute Holm-3): indent: 0, format: 5, delivery: 12; zero means already nonsignificant. See flip-sensitivity.json.

Fixed cross-container replay: 0/40 payloads divergent; 0/8 DEV episodes with any divergence. Descriptive clustered control, not universal reproducibility.

Claim ceiling: bounded request-time rule restatement on one frozen trunk and authored distribution. No superiority-to-prose, removed-stale-influence, generalized coding competence, free-text admission or actuator claim. The scoped system example and accumulated old history remain possible influences.

Artifacts: [registration](REGISTRATION.md), [summary](summary.json), [audit](audit.json), [episode tables](episode-tables.json), [cost](cost-audit.json), records-R/N/T/Q.jsonl, receipts.json, local-hashes.json. Raw HTTP and loop journals remain local and hash-indexed. Explicit-path local commits; no push, host signals, or edits to original larger-test results.

Cost accounting covers3,389 HTTP responses:3,333 main attempts,16 determinism calls and40 fixed replay calls; [HTTP costs](http-costs.json). The3,349 main/determinism per-output receipts and40 replay receipts are hash-bound separately. [Independent statistical audit](statistical-audit.json) reconstructs common-event episode averages with exact fractions and reproduces all three sign/Holm results.

No main attempt hit the2048-token cap; maximum audited main/determinism prompt+cap was17350/32768. All8,293 local-file hashes were verified; each committed arm record file is below2.54MB (limit10MB). The independent statistical audit also reproduces both harm contrasts at the episode unit.
