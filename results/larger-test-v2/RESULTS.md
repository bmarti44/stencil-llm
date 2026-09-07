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

## Orchestrator addendum after the two independent reviews (2026-09-07)
Reviews: results/larger-test-v2-review-opus.md (maximum reasoning) and results/larger-test-v2-review-astra.md
(adversarial self-audit). THE PASS STANDS on its registered gates, and both reviews agree it establishes something
NARROWER than "the mechanism works at scale".
VERIFIED: 3,328 unique records; 16 turns in every lane; 52/52 groups; all 23 pinned source files hash-identical at
e20c3f9b; registration, freeze and DEV calibration committed before the one-shot bank open; the verdict came from
the frozen reading function; a 250-record independent receipt-to-record replay gave 0 mismatches; the endpoint code
is byte-identical to the frozen FAIL. The primary re-derives exactly: delivery 35/0/28, p = 1/2^35 = 2.910383e-11,
Holm 8.731e-11; format 25/4/34, Holm 1.0372e-04; indent 17/15/32, p = 0.430. Reproducibility: 40/40 cross-container
payloads byte-identical, determinism 8/8; flip tolerance delivery 12, format 5, indent 0, so format is robust this
time (it tolerated one in the frozen run). Clustering the repeated-task episodes still leaves delivery 1.9e-09 and
format 2.2e-03.
THE HARM CLAUSE IS LEGITIMATE, NOT UNFALSIFIABLE: DEV-calibrated pre-freeze, applied identically to its own control,
minimum detectable effect enumerated before the run, and the one real harm event DID enter the test (episode 56 has
indent_attempted true on both arms). The superseded <= 1 margin would also have passed, so the PASS does not depend
on the clause swap.
FIVE FINDINGS THAT QUALIFY THE RESULT, and they are the honest content of this run:
1. (HIGH) T EQUALS OR BEATS R ON EVERY PRIMARY FAMILY (delivery 1/0/62; format 1 win vs 6 losses; indent 10/13/41)
   and on adherence (format 62/64 vs 56/64). RESULTS never shows R vs T, although the full-program audit
   pre-committed to reporting exactly this. There is therefore NO evidence that the register REPRESENTATION
   contributes anything over correct prose.
2. (HIGH) THE COMPETENCE COST SURVIVES INTO THE PASS, against the prose control: semantic integration R 45 vs T 52
   is 7 discordant episodes all one way, one-sided p = 0.0078 (Holm 0.0234). R vs N (45 vs 48) is noise, p = 0.375.
3. (HIGH) The powered delivery endpoint requires the literal value `ready` at 64/64 rounds, identical to the
   arm-invariant system example, so copying the example scores 64/64. R is exonerated only by an UNREPORTED
   off-endpoint diagnostic (R 395/395 across all four values; N 346/395, failing only on `ready`, 37/86).
4. (HIGH) The bank-disjointness receipts are true by construction but 98.63% of turn-level tasks are reused from
   the spent bank and 16 of 64 episodes reproduce a spent episode's task sequence.
5. The scoped protocol EASED the coding work and the delivery gain DECREASED relative to the frozen run, so the
   pass is partly an easier task, not only a working mechanism (astra). Episode 56's exclusion is outcome-dependent
   and favours R; under missing-write-as-failure both families still survive (delivery Holm 1.615e-09, format
   3.249e-04). Repair efficacy is ZERO: all five repair replies are token-identical to their initial submission
   although the repair prompt genuinely differed, so feedback reached the model and was ignored; exact 95% upper
   bound on repair success 45.1%. Pooled indent zero masks 12 reinstatement losses.
WHAT THIS RUN ESTABLISHES: request-time restatement of the currently effective obligations, whether from the
register OR as plain prose, recovers one specific silent-default rule transition that ordinary retained history
does not, on largely the same task pool as the frozen FAIL, with adherence gains that survive clustering and
adversarial flips.
WHAT IT DOES NOT ESTABLISH: that the register representation contributes anything over correct prose; that the
mechanism preserves competence (it is significantly worse than prose on semantically correct work); that repair
works; that indent or reinstatement behaviour improved; or that this is competent long-horizon software work.
AGREED SUCCESSOR (astra): one fresh 32-episode paired FACTORIAL, 16 rounds, crossing whole-file versus scoped
submission with N / R / composed-prose T, 3,072 calls, about 5.32 GPU-h, primary = per-episode paired private-test
integration and joint integration-plus-adherence, on a separately frozen bank with new semantic parameterizations.
That design separates the protocol effect from the mechanism effect, which this run confounds.
