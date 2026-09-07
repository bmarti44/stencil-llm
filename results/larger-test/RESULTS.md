Fit-on: none; development-on: eight DEV episodes only; evaluated-on: the 64 frozen authored evaluation episodes, one model pass, no tuning.

# SLAB-2 Amendment 5 — FAIL

3328/3328 scheduled records; 64/64 complete R/N/T episodes. Frozen SHA `95fa7fc0c006518ef84c1ea20c152c079ae1798a`. Failed clauses: R episode breakage exceeds N by more than one.

| Family | Paired episodes | R wins / N wins / ties | Mean paired gain | One-sided p | Holm p | Evidence | Missing-write sensitivity gain |
|---|---:|---:|---:|---:|---:|---|---:|
| delivery | 64 | 40/0/24 | 0.625 | 9.09494702e-13 | 2.72848411e-12 | True | 0.625 |
| format | 58 | 24/9/25 | 0.25862068965517243 | 0.00676549342 | 0.0135309868 | True | 0.234375 |
| indent | 54 | 9/5/40 | 0.037037037037037035 | 0.211975098 | 0.211975098 | False | -0.0703125 |

Delivery is the predeclared primary; all signs are episode-paired after within-episode averaging. No independent-round inference. Joint final success below uses pilot7’s applicable-trait diagnostic rubric and is descriptive only. The frozen summary’s all-four-raw-satisfied field is retained unchanged; its stricter definition was noticed during loading before evaluation outputs and is not used in this table or any verdict.

| Arm | Episodes | Any breakage | Any nonwrite | Any cap | Any compact ready | Any compact format violation | Joint final |
|---|---:|---:|---:|---:|---:|---:|---:|
| R | 64 | 20 | 13 | 0 | 25 | 29 | 12 |
| N | 64 | 14 | 2 | 0 | 7 | 41 | 5 |
| T | 64 | 29 | 19 | 0 | 27 | 29 | 14 |
| Q | 16 | 7 | 0 | 0 | 16 | 16 | 0 |

Per-family arm adherence: mean of within-episode written-change adherence; measured-episode denominator. These descriptive arm means use each arm’s own writes; the primary above uses common R/N writes.

| Family | R mean / episodes | N mean / episodes | T mean / episodes | Q mean / episodes |
|---|---:|---:|---:|---:|
| delivery | 1.0000 / 64 | 0.3750 / 64 | 0.9032 / 62 | 1.0000 / 16 |
| format | 0.6897 / 58 | 0.3906 / 64 | 0.7288 / 59 | 0.0000 / 16 |
| indent | 0.6759 / 54 | 0.6406 / 64 | 0.7685 / 54 | 0.3750 / 16 |

Paired breakage: R-only 8, N-only 2, both 12, neither 42. The registered practical tolerance fails; this is not a separately registered test of harm.

Missingness matters for indent: the conditional paired gain is positive, but the all-attempt sensitivity is negative (see table). Missing paired changes are listed by episode in summary.json; no later successful round replaces them. “None” in the episode table means no common parsed-write measurement, not zero adherence.

Paired breakage excess R−N=6 episodes (allowed<=1). CPU composition: 276 scheduled compact registers across 64 episodes, all clean and bit-exact between forward/reconstructed state; 35 historical hashes exact.

Cross-container reproducibility: **0/40 divergent (0.0%)**, from the fixed pilot7 payloads reissued midway in this container. 0/8 DEV episodes had any divergence; episode-mean divergence 0.0%. This preselected R-only set does not establish universal reproducibility or negate the prior 10/166 divergence observation. Descriptive; no cell-independence confidence claim.

GPU held **6.8503h** (24660.901s), including loading, replay and cleanup, against 11.5h cooperative/12h hard limits. Projection 7.4462h; queue wait 0.04s. Main generated tokens 844,905; max prompt+cap 12047+2048<=32768. Full cost decomposition in cost-audit.json.

CPU audit: all 3328 records agree with raw same-run records, saved HTTP completions/token accounting and SHA256 receipts; 4960 local files verified; independent episode sign/Holm reimplementation agrees. Initial isolated validation failed because its tokenizer link was absent; corrected asset link gave 37 passed / 1 xfail and CPU smoke before GPU. No source or threshold changed after freeze.

Claim ceiling: any positive evidence credits the current effective value restated at request time in this bounded explicit-rule package on one frozen trunk and authored distribution. T is oracle prose (DEV 7/8); this is not evidence that a register data structure beats prose. Accumulated history retains old blocks, the system worked example attracts delivery=ready, and T remains uncomposed on compact format. No free-text admission, universal task selection, autonomous long-horizon engineering, actuator efficacy or absence-of-stale-influence claim. See [registration](REGISTRATION.md) and [v2 ceiling](../focus-mechanism-composition-v2-astra.md).

Q is a 16-episode fresh-context reference using gold prerequisite files; O was dropped as byte-identical to R. No later retries, seeds, outcome-selected subsets or tuning. HTTP/full journals are local and hash-indexed; own container cleanup is recorded. No host process signals or push.

| Episode | Delivery gain | Format gain | Indent gain | Broken R/N/T/Q | Compact ready R/N/T/Q | Final R/N/T/Q |
|---|---:|---:|---:|---|---|---|
| slab2-eval-00 | 1.0 | 1.0 | 0.0 | 0/0/1/0 | 0/0/1/1 | 0/0/0/0 |
| slab2-eval-01 | 1.0 | 0.0 | 0.0 | 0/0/1/1 | 1/0/1/1 | 0/0/0/0 |
| slab2-eval-02 | 1.0 | None | None | 1/1/1/1 | 1/0/1/1 | 0/0/0/0 |
| slab2-eval-03 | 1.0 | 0.0 | 0.0 | 0/0/1/0 | 1/0/1/1 | 0/0/0/0 |
| slab2-eval-04 | 1.0 | 1.0 | 0.0 | 0/0/1/0 | 0/0/1/1 | 1/0/0/0 |
| slab2-eval-05 | 1.0 | 1.0 | 0.0 | 0/0/0/1 | 0/0/1/1 | 0/0/0/0 |
| slab2-eval-06 | 1.0 | 1.0 | 0.0 | 1/1/1/1 | 0/0/0/1 | 0/0/0/0 |
| slab2-eval-07 | 1.0 | None | None | 1/0/0/0 | 1/0/1/1 | 0/0/0/0 |
| slab2-eval-08 | 1.0 | 0.0 | 0.0 | 0/0/0/0 | 0/0/0/1 | 1/0/1/0 |
| slab2-eval-09 | 0.0 | 1.0 | 0.5 | 0/0/0/1 | 0/1/0/1 | 1/0/1/0 |
| slab2-eval-10 | 1.0 | -1.0 | 0.0 | 1/1/1/1 | 1/0/0/1 | 0/0/0/0 |
| slab2-eval-11 | 1.0 | 0.0 | 0.5 | 0/0/0/0 | 1/0/0/1 | 0/0/0/0 |
| slab2-eval-12 | 0.0 | None | None | 1/0/1/0 | 1/1/1/1 | 0/0/0/0 |
| slab2-eval-13 | 1.0 | 1.0 | 0.0 | 0/0/1/0 | 0/0/1/1 | 1/0/0/0 |
| slab2-eval-14 | 1.0 | 0.0 | 0.0 | 1/1/1/1 | 1/0/1/1 | 0/0/0/0 |
| slab2-eval-15 | 1.0 | 1.0 | 0.0 | 0/0/1/0 | 0/0/1/1 | 0/0/0/0 |
| slab2-eval-16 | 0.0 | 0.0 | -0.5 | 0/0/0/— | 0/0/0/— | 1/1/1/— |
| slab2-eval-17 | 1.0 | 0.0 | 0.5 | 0/0/0/— | 1/0/0/— | 0/0/1/— |
| slab2-eval-18 | 1.0 | None | None | 1/1/1/— | 1/0/1/— | 0/0/0/— |
| slab2-eval-19 | 1.0 | 0.0 | None | 1/0/1/— | 1/0/1/— | 0/0/0/— |
| slab2-eval-20 | 1.0 | 0.0 | 0.0 | 0/0/1/— | 1/0/1/— | 0/0/0/— |
| slab2-eval-21 | 1.0 | 1.0 | 0.0 | 1/0/1/— | 0/0/1/— | 0/0/0/— |
| slab2-eval-22 | 0.0 | 0.0 | None | 1/1/1/— | 0/0/0/— | 0/0/0/— |
| slab2-eval-23 | 1.0 | 0.0 | 0.0 | 0/0/0/— | 1/0/0/— | 0/0/1/— |
| slab2-eval-24 | 0.0 | -1.0 | 0.5 | 0/0/0/— | 1/0/0/— | 0/0/0/— |
| slab2-eval-25 | 1.0 | 1.0 | 0.0 | 0/0/0/— | 0/0/0/— | 0/0/0/— |
| slab2-eval-26 | 1.0 | 1.0 | None | 1/1/1/— | 0/0/0/— | 0/0/0/— |
| slab2-eval-27 | 0.0 | -1.0 | 0.5 | 0/0/1/— | 1/0/1/— | 0/0/0/— |
| slab2-eval-28 | 1.0 | 0.0 | 0.0 | 0/0/1/— | 0/0/1/— | 0/0/0/— |
| slab2-eval-29 | 1.0 | 0.0 | 0.0 | 0/0/0/— | 0/0/0/— | 0/0/0/— |
| slab2-eval-30 | 0.0 | -1.0 | 0.0 | 1/1/1/— | 1/0/1/— | 0/0/0/— |
| slab2-eval-31 | 1.0 | -1.0 | 0.5 | 0/0/0/— | 1/0/0/— | 0/0/1/— |
| slab2-eval-32 | 0.0 | 1.0 | 0.0 | 0/0/0/— | 0/1/0/— | 0/0/0/— |
| slab2-eval-33 | 1.0 | 1.0 | 0.0 | 0/0/0/— | 0/0/0/— | 0/0/1/— |
| slab2-eval-34 | 1.0 | 1.0 | 0.0 | 1/1/1/— | 0/0/1/— | 0/0/0/— |
| slab2-eval-35 | 0.0 | -1.0 | 1.0 | 0/1/0/— | 1/0/1/— | 0/0/0/— |
| slab2-eval-36 | 0.0 | 0.0 | 0.0 | 0/0/1/— | 0/0/0/— | 0/0/0/— |
| slab2-eval-37 | 1.0 | 0.0 | 0.0 | 0/0/0/— | 0/0/0/— | 0/0/1/— |
| slab2-eval-38 | 1.0 | None | None | 1/1/1/— | 1/0/1/— | 0/0/0/— |
| slab2-eval-39 | 0.0 | 0.0 | 0.5 | 0/0/0/— | 0/0/0/— | 1/0/0/— |
| slab2-eval-40 | 0.0 | 0.0 | 0.0 | 0/0/0/— | 0/1/0/— | 1/0/1/— |
| slab2-eval-41 | 1.0 | 1.0 | None | 1/0/0/— | 0/0/0/— | 0/0/0/— |
| slab2-eval-42 | 1.0 | 1.0 | 0.0 | 1/1/1/— | 0/0/0/— | 0/0/0/— |
| slab2-eval-43 | 0.0 | 0.0 | 0.0 | 0/0/0/— | 0/0/0/— | 1/1/1/— |
| slab2-eval-44 | 0.0 | 0.0 | 0.0 | 0/0/1/— | 0/0/1/— | 1/1/0/— |
| slab2-eval-45 | 0.0 | -1.0 | -1.0 | 1/0/1/— | 1/0/1/— | 0/1/0/— |
| slab2-eval-46 | 0.0 | 0.0 | -1.0 | 1/1/1/— | 0/0/0/— | 0/0/0/— |
| slab2-eval-47 | 1.0 | None | 0.0 | 1/0/1/— | 1/0/1/— | 0/0/0/— |
| slab2-eval-48 | 0.0 | 0.0 | -0.5 | 0/0/0/— | 0/0/0/— | 0/0/0/— |
| slab2-eval-49 | 1.0 | 1.0 | -0.5 | 0/0/0/— | 0/0/0/— | 0/0/1/— |
| slab2-eval-50 | 0.0 | -1.0 | 0.0 | 0/0/0/— | 1/0/0/— | 0/1/0/— |
| slab2-eval-51 | 0.0 | 0.0 | 0.0 | 0/0/0/— | 0/0/0/— | 0/0/1/— |
| slab2-eval-52 | 0.0 | 0.0 | 0.0 | 0/0/0/— | 0/0/0/— | 0/0/0/— |
| slab2-eval-53 | 1.0 | -1.0 | 1.0 | 0/1/0/— | 1/0/0/— | 0/0/1/— |
| slab2-eval-54 | 1.0 | 1.0 | 0.0 | 0/0/1/— | 0/0/1/— | 0/0/0/— |
| slab2-eval-55 | 1.0 | 1.0 | 0.0 | 0/0/0/— | 0/0/0/— | 1/0/0/— |
| slab2-eval-56 | 1.0 | 1.0 | None | 1/0/0/— | 1/0/0/— | 0/0/0/— |
| slab2-eval-57 | 1.0 | 1.0 | 0.0 | 0/0/0/— | 0/0/1/— | 1/0/0/— |
| slab2-eval-58 | 0.0 | 1.0 | 0.0 | 0/0/0/— | 0/1/0/— | 0/0/0/— |
| slab2-eval-59 | 1.0 | 1.0 | 0.0 | 0/0/0/— | 0/0/1/— | 1/0/0/— |
| slab2-eval-60 | 0.0 | 0.0 | 0.0 | 0/0/0/— | 1/1/0/— | 0/0/0/— |
| slab2-eval-61 | 0.0 | 1.0 | 0.0 | 0/0/0/— | 0/1/0/— | 0/0/0/— |
| slab2-eval-62 | 1.0 | 1.0 | 0.0 | 0/0/0/— | 0/0/0/— | 0/0/0/— |
| slab2-eval-63 | 0.0 | 0.0 | 0.0 | 0/0/0/— | 0/0/0/— | 0/0/1/— |

Artifacts: [registration](REGISTRATION.md), [freeze](freeze.json), [summary and missingness](summary.json), [R records](records-R.jsonl), [N records](records-N.jsonl), [T records](records-T.jsonl), [Q records](records-Q.jsonl), [CPU control](composition-control.json), [reproducibility](reproducibility.json), [cost audit](cost-audit.json), [audit](audit.json), [HTTP/journal hashes](local-hashes.json), [same-run receipt hashes](receipts-hashes.json), [server log](server.log).

## Orchestrator addendum after the two independent reviews (2026-09-07)
Reviews: results/larger-test-review-opus.md (maximum-reasoning) and results/larger-test-review-astra.md
(adversarial self-audit). They agree on the accounting, the primary and the cause of breakage, and the Opus read
corrects the harm story in a way that makes the FAIL stronger, not weaker.
VERIFIED: 3328/3328 unique records; 64/64 complete episodes; zero caps; all 11 frozen source hashes identical; the
CPU-rebuilt bank matches freeze.json exactly; freeze -> bank open -> first record strictly ordered; no prior model
artifact on any evaluation id. Re-executing the frozen larger_reading() on the committed records reproduces
summary.json BYTE-IDENTICALLY (FAIL, one failing clause, breakage_excess 6).
PRIMARY REPRODUCED from an independent re-implementation: delivery 40/0/24, mean 0.625, p = 9.094947e-13 (= 2^-40),
Holm 2.728e-12, with exactly one change round per episode and ZERO missing paired writes; format 24/9/25, Holm
0.01353; indent 9/5/40, Holm 0.212, sensitivity -0.0703. No outcome-dependent selection anywhere in the path.
THE MECHANISM OF THE GAIN: N is NOT information-starved. In all 64 episodes every arm is told the new value in the
current user message, and ALL 40 of N's failures re-emit its OWN RETIRED TRAILER VALUE while R is 64/64. The gain
comes from stopping the model repeating its own superseded output, not from supplying missing information.
THE COST IS REAL AND THE CLAUSE WAS ILL-FORMED IN BOTH DIRECTIONS. Every non-write in the run (R 48, T 51, N 2) is
an indentation SyntaxError, and 9 of the 10 differential-breakage episodes first fail exactly on their indent-change
round: one coherent family, not the pilot lock/format family. As stated, the failing clause is NOT significant
(exact McNemar b=8/c=2, two-sided p = 0.109, paired diff 6/64, 95% CI [-0.0003, +0.188]). But the clause's source
definition excludes semantic test failures while the implemented metric includes them; on the definition-matched
metric the excess is 13 vs 2, p = 0.0037. Fixing the instrument makes the FAIL WORSE. Separately the <= 1 bar came
from a design memo that disclaims it, not from the authorizing review, and was never DEV-calibrated.
ATTRIBUTION IS SETTLED BY T: the correct, non-accumulating oracle prose arm breaks MORE than R (29 vs 20 episodes,
two-sided p = 0.035; 19 vs 13 non-writes). Breakage therefore cannot be attributed to rendering a register; it is
the cost of ACTING on a restated style obligation inside a whole-file re-emission protocol.
CONFOUNDS QUANTIFIED: T delivery 0.903 and 310/313 on non-defaults (blocks "beats prose"); R's turn-11 prompt
carries 11 stale copies of the superseded rule against 1 current (blocks "removes stale influence"); Q has a
composed block, no history, 16/16 delivery=ready emissions and 0/16 format adherence (blocks attributing the format
gain to composition).
REPRODUCIBILITY: 40 fixed payloads reissued mid-run, 0/40 divergent (95% upper bound 8.8%). Delivery tolerates 12
adversarial episode flips before losing Holm significance; FORMAT TOLERATES ONE, so the format result is not robust
to the historical 6.02% cross-restart divergence rate and must be reported with that caveat.
WHAT THIS ESTABLISHED: rendering the current effective obligations into the request raised delivery-obligation
adherence from 37.5% to 100% across 64 paired episodes at p = 9.09e-13, by stopping the model repeating its own
retired value; and the same restatement raised syntactically-invalid-file episodes from 2 to 13 in 64, a real and
significant competence cost that oracle prose pays even more heavily.
WHAT IT DID NOT ESTABLISH: that the register beats correct prose; that composition fixed the compact format; that
stale influence is removed; that final executable success improved; or that the mechanism passed. THE REGISTERED
VERDICT IS FAIL AND STANDS. No rescoring.
NEXT STEP (both reviewers, converging): re-run the register arm alone on a SCOPED-EDIT protocol that cannot
re-indent untouched code, about 2.5 GPU-h, with a new freeze and honest bank lineage. Orchestrator addition, from
the literal outputs: a rule change has TWO consequences, future compliance and reconciliation of the existing
artifact, and the renderer only ever rendered the first — a reconciliation obligation is the design change to test.
