# LEG B OUTCOME review (sol, 2026-09-04)

Scope: `LEDGER-PLAN.md` “SELECTOR v2 — POST-DEVELOPMENT
EVALUATION, LEG B,” Leg B Amendments 1–3, “LEG B OUTCOME,”
`results/qwen/multiif-evict-909-prequery-v2/{meta,summary,conv-*}.json`, and
the executing `scripts/multiif_evict.py` at the hash in `meta.json`. This was a
CPU-only, foreground, read-only audit. I launched no model/GPU process, did not
signal any process, and did not read the sealed IFEval input.

## Executive result and graded findings

The arithmetic, record exceptions, and decisive registered reading reproduce.
The three statistical components are C1 PASS, C3 PASS, C2 FAIL; the safety
clause independently invalidates every registered contrast because every
contrast contains at least one arm with `invalid=1` against `full=0`. Therefore
Leg B is **NOT SUPPORTED as registered**. The outcome correctly refuses a
retroactive `full+1` rescue.

I find no high or critical error in that bottom-line reading. I find three
medium qualifications and one low artifact defect:

1. **MEDIUM — C1 does not isolate retention or learned selection.**
   `clf_pinned_echo` receives both selected KV pins and a text echo, while
   `clf_control` receives matched pinned columns but no echo
   (`scripts/multiif_evict.py:842-852`). Thus C1 is a contrast of the combined
   selected-pin-plus-echo treatment against a non-echo deterministic complement
   control. It is not a clean “retention” contrast, and the control is not
   random despite the gloss at `LEDGER-PLAN.md:587`. The large result is not
   numerically explained by echo alone—the unregistered no-echo
   `clf_pinned - clf_control` mean is still +24.558 points—but that sensitivity
   is post hoc and outside Holm. A model card may disclose the C1 statistic; it
   must not turn it into confirmatory evidence that KV retention, echo, or the
   classifier separately caused the gain.

2. **MEDIUM — “C2 fails alone” has a genuine two-way reading here.** The
   registered tree says an arm's safety breach fails its contrasts, says C1 or
   C3 failure means unsupported, and separately says “C2 fails alone” selects
   the role rule (`LEDGER-PLAN.md:591-598`). On the strict gate-level reading,
   C2 did not fail alone: safety fails C1, C2, and C3. On the
   statistical-component reading, C1 and C3 pass and C2 alone fails. The
   outcome's choice to apply the role result only **descriptively** is the
   conservative resolution and is acceptable. It should say the role rule is
   *preferred by the registered simplicity policy / observed result*, not that
   failure of the one-sided classifier-superiority test by itself proves the
   reverse. For context only, an unregistered reverse-direction calculation
   gives role-minus-classifier mean +3.493 points, corrected LB +2.200, and
   one-sided p = 1.43e-6; the substantive preference is not resting on a near
   tie. The failed Leg B must not be described as authorizing an “ADVANCE to Leg
   A”; any already-registered Leg A work has its own provenance and status.

3. **MEDIUM — the known 12-hour provenance field remains stale.** Amendment 1
   raised the cap to 24 GPU-hours (`LEDGER-PLAN.md:605-613`), and the observed
   20.868 GPU-hours is within it. But `summary.json:237` still says
   `"full_run_allowed_by_preflight": false` because the harness continues to
   compare with 12 hours. `meta.json` also lacks the amended cap/registration
   identity. This is a reporting/provenance contradiction, not an outcome
   error; the outcome's “under the amended 24 GPU-h cap” statement is correct.

4. **LOW — two stored p-values are numeric zero, not mathematical zero.** The
   harness calculates `1 - CDF`, which cancels to `0.0` for C1 and C3. Direct
   Student-t survival-function calculation gives finite p-values below. The
   outcome says `p ~ 0`, which is fair, and Holm decisions do not change.

## Independent record recomputation

There are exactly 909 `conv-000.json` through `conv-908.json` records, with
`ci=0..908` in order and 909 unique keys. I aggregated their recorded Boolean
score cells directly, without calling `summarize_records` or trusting
`summary.json`.

| arm | aged pass / n | aged rate | all-final pass / n | all-final rate | conversation-mean aged rate |
|---|---:|---:|---:|---:|---:|
| full | 1483 / 2276 | 0.651582 | 2082 / 3185 | 0.653689 | 0.656032 |
| evicted | 379 / 2276 | 0.166520 | 1139 / 3185 | 0.357614 | 0.163550 |
| clf_pinned | 1302 / 2276 | 0.572056 | 2016 / 3185 | 0.632967 | 0.572516 |
| clf_pinned_echo | 1348 / 2276 | 0.592267 | 2019 / 3185 | 0.633909 | 0.594518 |
| clf_control | 747 / 2263 | 0.330093 | 1514 / 3167 | 0.478055 | 0.327341 |
| role_pinned | 1377 / 2276 | 0.605009 | 2085 / 3185 | 0.654631 | 0.607444 |

The control denominator correctly loses 13 aged and 18 all-final constraint
cells from the five structurally impossible conversations. The other arms keep
all 909 conversations, as Amendment 3 requires.

For inference I formed each conversation's mean aged-pass percentage, then the
registered within-conversation differences. The lower bound is the one-sided
95% Student-t bound minus the registered one-cluster continuity term `100/k`.
The p-value uses the same continuity penalty. Independent SciPy t-survival
probabilities avoid the harness's `1-CDF` cancellation.

| contrast | k | mean points | corrected 95% LB | raw one-sided p | Holm cutoff | Holm-adjusted p | statistical component |
|---|---:|---:|---:|---:|---:|---:|---|
| C1 `clf_pinned_echo - clf_control` | 904 | +26.843658 | +24.712021 | 3.6933e-85 | 0.016667 | 1.1080e-84 | PASS |
| C3 `echo - evicted - 0.5(full-evicted)` | 909 | +18.472681 | +16.730401 | 1.5875e-65 | 0.025000 | 3.1750e-65 | PASS |
| C2 `clf_pinned - role_pinned` | 909 | -3.492849 | -4.785469 | 0.999999683 | 0.050000 | 0.999999683 | FAIL |

The Holm order is C1, C3, C2. This exactly reproduces the outcome after normal
rounding. The pooled recovered fraction printed in the outcome is

`(1348/2276 - 379/2276) / (1483/2276 - 379/2276) = 0.877717`.

Using conversation-mean rates instead gives 0.875093. Both round to 0.88, so
the unlabelled estimator choice does not affect the reading. C3 itself uses the
registered conversation-clustered estimator, not the pooled fraction.

The equal-column claim also checks out. Across all 909 records,
`clf_pinned`, `clf_pinned_echo`, and `role_pinned` each retain 34,642 columns
(mean 38.110; range 0–303), with zero per-record mismatches. On the 904 feasible
controls, `clf_control` equals the classifier's pin count in every record
(34,055 columns total; mean 37.671; range 0–151).

## Safety and the invalid outputs

Direct event counts are:

| arm | timeout | truncated | degenerate | invalid | quoting |
|---|---:|---:|---:|---:|---:|
| full | 0 | 208 | 241 | 0 | 0 |
| evicted | 0 | 54 | 54 | 0 | 0 |
| clf_pinned | 0 | 162 | 192 | **1** | 0 |
| clf_pinned_echo | 0 | 187 | 222 | **1** | 153 |
| clf_control (n=904) | 0 | 76 | 87 | 0 | 0 |
| role_pinned | 0 | 164 | 194 | **1** | 0 |

Thus every arm meets timeout, truncation (`<=209`), and degenerate (`<=241`)
requirements. `clf_pinned`, `clf_pinned_echo`, and `role_pinned` each fail
`invalid <= full` because 1 is not <= 0. The phrase “one invalid output per
pinned arm” is correct as an arm-event count, but there are two unique affected
conversations and three arm events:

- **ci 278, key `1886:11:en`, `clf_pinned_echo`.** The exact 512-token output
  has SHA-256 `2be8e178dd367d9abd5ded0a2f539bf8c19b3a8f2bf64a5f5794bc59c0289130`.
  It is 1,109 characters containing only 256 double quotes, 512 spaces, and
  341 newlines, beginning `"  \n"  \n"  \n"  \n\n...`. Its token stream is
  prefix `[1,2303]`, followed by the cycle
  `[1,2303,1,2303,1,18611]` through token 512. It is truncated, has repeated
  4-gram fraction 0.9882, and passes 0/2 aged constraints.

- **ci 534, key `2653:18:en`, both `clf_pinned` and `role_pinned`.** The two
  outputs and token streams are byte-identical. The exact text has SHA-256
  `863f343f5f49c1defb67b7e5b40869f86156f88df0cd1e78c9bf063cd52a48b7`,
  is 1,276 characters, and contains only 3 double quotes, 508 asterisks, 510
  spaces, and 255 newlines, beginning `"  \n"  \n**"  \n**  \n**  \n...`.
  Its 512-token stream has prefix `[1,2303,1,2303,334,1]` followed by the
  cycle `[2303,334]`. Both arms are truncated, have repeated 4-gram fraction
  0.9843, and pass 0/3 aged constraints.

The operative function, frozen in the registered harness before this run,
defines invalid as empty, containing no alphanumeric character, or containing
a Qwen chat-control token (`scripts/multiif_evict.py:297-302`). All three arm
events satisfy the no-alphanumeric branch; none relies on a subjective reading
or a chat-token false positive. They are also truncation/degeneracy events, but
the registered categories overlap and invalid has its own zero-baseline clause.
Reclassifying them after outcome would be impermissible.

## The five `control_impossible` conversations

Every record obeys Amendment 3's arithmetic: `available = evictable - pinned`,
`available < pinned`, all three control fields are null, and every non-control
arm ran and scored.

| ci | key | topic / selected material | evictable | pinned | available | aged passes: full / evicted / clf / echo / role |
|---:|---|---|---:|---:|---:|---:|
| 145 | `1476:16:en` | Azure rename, sentence cap, required ending | 147 | 79 | 68 | 1/3 / 2/3 / 1/3 / 1/3 / 1/3 |
| 358 | `2192:11:en` | repeat font line, no lead-in, “consider” twice | 119 | 60 | 59 | 1/2 / 0/2 / 1/2 / 1/2 / 1/2 |
| 613 | `2859:10:en` | long quantum-entanglement source plus title rule | 515 | 303 | 212 | 1/2 / 1/2 / 2/2 / 2/2 / 2/2 |
| 769 | `334:1:en` | Color Paper slogan and bullet/capital rules | 131 | 72 | 59 | 1/3 / 0/3 / 1/3 / 0/3 / 1/3 |
| 770 | `334:5:en` | same family, 16-capital variant | 132 | 73 | 59 | 2/3 / 0/3 / 1/3 / 0/3 / 1/3 |

This gives `n_control_impossible=5`, C1 `k=904`, and 2,263 control aged cells,
exactly as reported. The criterion is structural and was registered before the
fresh v2 run; it does not select on a v2 arm's pass/fail outcome. It does narrow
C1 to conversations where a disjoint equal-column control exists, but only
5/909 (0.55%) are excluded and the exclusion is fully disclosed.

## Echo-copy rate and interpretation

The reported 153/909 is exact: **16.8317%** of `clf_pinned_echo` responses
contain at least one eight-token window from the rendered echo. One quoted
conversation is control-impossible, so C1 contains 152 quoted cases. The flag
means token overlap, not necessarily pathological wholesale copying; Multi-IF
can itself require exact repetition.

Descriptive stratification is:

| echo response stratum | conversations | echo-arm aged pass | C1 mean | C3 mean | echo minus same selected pins |
|---|---:|---:|---:|---:|---:|
| quoting | 153 | 196/373 = 0.5255 | +28.235 | +14.216 | -2.996 |
| non-quoting | 756 | 1152/1903 = 0.6054 | +26.563 | +19.334 | +3.252 |
| all | 909 | 1348/2276 = 0.5923 | +26.844 | +18.473 | +2.200 |

The quoting cases do not account for the C1 signal, and the echo arm actually
has a lower raw pass rate in that post-treatment stratum. But quoting status is
an outcome of the treatment, not a randomized baseline covariate, so these
rows cannot identify the echo effect and must not be used for a post hoc
exclusion. The rate leaves the registered pass/fail unchanged. It **does**
matter for language: with a non-echo C1 control and direct echo-token reuse in
16.8% of outputs, C1/C3 support at most the combined pin-plus-reinjection
system's statistical component, not a pure availability/retention mechanism.

## Registered decision and allowable claims

The safety application is correct arm by arm:

- C1 contains failing `clf_pinned_echo`, so C1 fails as registered even though
  its statistical component passes.
- C3 contains failing `clf_pinned_echo`, so C3 fails as registered even though
  its statistical component passes.
- C2 contains both failing `clf_pinned` and failing `role_pinned`, so C2 fails
  on safety as well as failing its registered superiority direction.

Accordingly, “REGISTERED VERDICT: NOT SUPPORTED” is correct and complete for
Leg B. It is permissible to report the exact arm rates, C1/C3 statistical
components, the one-event safety sensitivity, and the observed role advantage,
provided they are labelled disclosed/descriptive and kept subordinate to the
failed registered verdict. It is not permissible to say Leg B passed, that the
registered mechanism benefit was established, that the classifier beat the
role rule, that KV retention was isolated, or that this is zero-shot/general
transfer. The last point is especially clear because the registration itself
calls Multi-IF a development family that shaped the design
(`LEDGER-PLAN.md:567-569`).

## Lineage and leakage

I found no run-time fitting, arm leakage, or undisclosed artifact substitution.

- Every hash in `meta.json` matches the current executing artifact: Multi-IF
  data `3a3d2af3...816d`, trunk `13bfabb5...2829`, tokenizer
  `aeb13307...dae4`, harness `e1c08f31...ba65`, ledger renderer
  `506335ab...15ba`, selector code `75ca13a8...95f3`, stats
  `2484b07d...347b2f`, and all six classifier files. The three headline
  classifier hashes exactly match the registration.
- The harness hash is the Amendment-3 implementation committed after the
  amendment and before the fresh run. All 909 records plus meta/summary are
  tracked, and the working copies are identical to `HEAD`.
- The selector runs frozen/no-grad on prior-user sentences, without current
  turn text, checker outcomes, or arm responses. All arms in a conversation
  share the same generated history; only the registered echo arm gets added
  current-query text.
- A conservative exact scan of all 23,903 `text` rows in every classifier
  JSONL (a superset of the actual training rows) against all 2,714 Multi-IF
  prompts found zero normalized full-prompt matches and zero classifier texts
  of at least 30 characters appearing as a benchmark-prompt substring. This
  supports item-level disjointness but is not an independent semantic-paraphrase
  proof.

The important limitation is disclosed rather than hidden: classifier/spec work
used synthetic-probe feedback, and Multi-IF's family/constraint types informed
the design. The result is a post-development evaluation. It cannot support a
no-contact or zero-shot claim. Amendment 3 was driven by a structural failure
encountered in the superseded run; the fresh-directory restart and objective
eligibility rule make the resulting 904-case C1 auditable, though the claim that
no superseded arm outcome was viewed is procedural and cannot be proven from
files alone.

## Model card and next registration

The model card should preserve the already-registered lineage sentence at
`LEDGER-PLAN.md:599-602`, then add a concise outcome paragraph along these
lines:

> On the corrected 909-conversation Multi-IF post-development evaluation, Leg
> B was not supported under its preregistered safety rule: `clf_pinned`,
> `clf_pinned_echo`, and `role_pinned` each produced one invalid event versus
> zero for full context, violating `invalid <= full`. Before that safety gate,
> C1 and C3 had positive statistical components (+26.84 points, LB +24.71; and
> +18.47, LB +16.73), while the equal-column C2 point estimate favored the
> parameter-free role rule over the learned classifier by 3.49 points. C1
> excluded five structurally impossible controls. The echo treatment copied an
> eight-token run from echoed text in 153/909 conversations and was compared
> with a non-echo control, so C1/C3 do not isolate KV retention from text
> reinjection or classifier selection.

For the selector program, the actionable C2 result is to stop treating this
classifier as the preferred selector for Multi-IF-style user-only dialogue.
Use the parameter-free role/recency rule as the prospectively registered
default there. Keep the frozen classifier for the separately registered BFCL
question, where tool-role selection is materially different. Any classifier
iteration must return only to classifier/probe data and then be assessed on a
new no-contact family; it must not train, threshold, or choose examples from
these 909 outcomes.

A new run under Leg A's `invalid <= full+1` clause is defensible only as an
explicitly outcome-informed **robustness replication**, not as a repair of this
Leg B and not as independent confirmation. Leg A's one-event rule predates this
outcome, which is useful rationale, but choosing it for Leg B after seeing
exactly one event is still post-outcome. Moreover, the same frozen greedy model,
harness, and 909 known prompts will be highly dependent and may simply reproduce
the same outputs; spending another approximately 21 GPU-hours on that alone has
low scientific value. Applying `full+1` as a sensitivity to the existing data
would make safety intact but would still leave C2 failed; it must be labelled
post hoc.

The stronger next registration is a new/no-contact cohort with:

1. the invalid definition and `<= full+1` allowance written operationally in
   advance, while retaining this original Leg B failure permanently;
2. an explicit decision table for the combination “C1/C3 statistical pass,
   C2 fail, safety pass/fail,” removing the present “fails alone” ambiguity;
3. the role/recency selector as the Multi-IF-style primary, with the learned
   classifier retained only where tool-source discrimination is in scope;
4. a factorial echo design (`pinned`, `echo-only`, `pinned+echo`) and an
   equal-column **and equal-echo** selector control, so availability,
   reinjection, and selection have identifiable contrasts;
5. an a priori rule for quoting (prefer reporting with no exclusion), full
   cohort/denominators, multiplicity, and whether any historical run may be
   combined. The known 909 must remain development/replication data, never be
   relabelled no-contact.

## VERDICT

**CONFIRMED-WITH-QUALIFICATIONS.** The orchestrator's decisive registered
reading—C1/C3 statistical components pass widely, C2 does not, three relevant
arms breach `invalid <= full`, and Leg B is therefore **NOT SUPPORTED** without
retroactive rescue—is correct. Qualifications: “C2 fails alone” is ambiguous
once safety invalidates all contrasts; role preference should remain a
descriptive/next-registration decision; C1/C3 do not isolate retention because
only their treatment has echo; and the artifact still carries the known stale
12-hour authorization field.
