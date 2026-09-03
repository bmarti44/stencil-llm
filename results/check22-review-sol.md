# Verification of quick checks 19–22 — spec-v2 generic classifier selector

Date: 2026-09-03

Reviewer: sol

Scope: the evidence named in the brief, plus read-only provenance/hash checks. I did not read any evaluation-benchmark file or directory. The only model execution was the expressly permitted offline, CPU-only bge-small nearest-neighbour audit.

## Bottom line

The reported b3 development-probe arithmetic is correct: the three logged seeds give `33/33/33` for pin-only and `46/45/44` for pin+echo, hence means `33.0` and `45.0`; the unbudgeted classifier control is `17` on every seed; full/finder/finder+echo/evicted are `44/37/48/14`; and selected pinned columns are `803/20 = 40.15` versus `932/20 = 46.60`, or `0.861588x`. Held-out accuracy rounds to `0.90` for every seed and fable's author-disjoint slice is `0.851/0.879/0.857`.

Those are development results, not transfer results. Check 19 caused both the definition and the v2 data to change. b3 is therefore simultaneously (i) the selector/mechanism selection set and (ii) the specification-development set. The stronger lineage statement that no training row derives from b3 is not sustainable: there are no exact copies, but the post-check-19 scope batch contains clear masked-template paraphrases of the observed b3 cases. The v2 concept itself is defensibly generic; this particular supporting data set and result are probe-informed.

## 1. Independent numerical recomputation

The totals below are sums of the 20 session rows where a retained row file exists. Seed 1 has no retained row file, so its outcome and column totals can only be re-summed from the 20 human-readable log lines and checked against the log's `TOTALS` object.

| seed | data status asserted in README | pin-only | pin+echo | exact-column control | coverage | held-out | fable held-out | evidence |
|---|---|---:|---:|---:|---:|---:|---:|---|
| 0 | 59-row final patch included | 33 | 46 | 17 | 0.8591 | 0.9001 | 0.8512 | row JSON recomputed |
| 1 | final patch excluded | 33 | 45 | 17 | 0.859 (logged) | 0.8976 | 0.8788 | log lines only |
| 2 | final patch excluded | 33 | 44 | 17 | 0.8591 | 0.9001 | 0.8567 | row JSON recomputed |
| mean | mixed data | **33.0** | **45.0** | **17.0** | **≈0.859** | **0.8993** | **0.8622** | arithmetic |

References re-summed from the H1′ records are `n=56`, full `44`, evicted `14`, taxonomy finder pin-only `37`, and taxonomy finder pin+echo `48`. Thus “trails finder by 4 on pins and 3 on echo” is correct. `45` matches/exceeds the full-context **baseline point estimate** of `44`; “full-context ceiling” is inaccurate because the finder+echo arm itself scores `48`.

Columns are also exact. Every seed log sums to 803 selected pinned columns, mean 40.15; the H1′ finder budgets sum to 932, mean 46.60. `803/932 = 0.86158798`. The echo arm pins the same selected columns, but the `0.86x` claim counts pinned columns only, not the extra echoed text/context length. That cost definition must accompany the claim.

The budget-clipped `CLFB` arms are not the headline arms and should not be conflated with them. Their columns and outcomes vary: seed 0 `793 cols, 33/45/control 17`; seed 1 `677 cols, 27/35/control 17`; seed 2 `775 cols, 33/40/control 18`.

### Safety, separated by arm

The retained rows record only `truncated` and `degenerate`; they do not retain timeout, repetition score, or invalid-output fields. Counts are sessions out of 20:

| evidence | pin-only trunc / degenerate | pin+echo trunc / degenerate | control trunc / degenerate |
|---|---:|---:|---:|
| classifier seed 0 | 0 / 0 | 0 / 1 | 2 / 2 |
| classifier seed 1 | **not recoverable** | **not recoverable** | **not recoverable** |
| classifier seed 2 | 0 / 0 | 0 / 2 | 2 / 2 |
| H1′ full reference | 1 / 2 | — | — |
| H1′ finder | 0 / 0 | 0 / 1 | 1 / 2 (finder control) |

On the surviving classifier rows, pin-only is safer than full and pin+echo is no worse than full. A three-seed safety claim is not auditable because `clf_probe8_s1_rows.json` is absent and the log omits safety fields.

## 2. What the v1→v2 timing makes b3

`LABELS.md` says v2 was created “after quick check 19,” and README item 19 gives the causal diagnosis: b3 misses on exact postscript, exact title, bullet-count, and letter-case constraints motivated a third, task/artifact scope. Git history also orders the v2 spec before the 4,954-row scope pass and both before checks 21–22.

Therefore b3 is not merely a clean dev probe on which a previously specified selector was tried. It selected the mechanism/threshold family in checks 13–18, exposed the context-scoring failure in check 19, changed the target label ontology, and shaped the new data. Call it the **selection and specification-development set**. Check 22 is an in-development fit-to-requirements result.

There are two legitimate readings of v2:

- Generic notion: a constraint on an ongoing artifact really does survive revisions, unlike an explicitly single-reply instruction. The three-scope distinction is coherent outside b3. The scope pass spans 40 domains and 4,954 rows (`2,060 rule / 893 fact / 2,001 none`) and includes broad non-benchmark-looking cases such as project-wide shell-script headers (`shell-and-file-operations-agent-scope.jsonl:9`), chapter-local story constraints (`creative-writing-collaboration-scope.jsonl`), report vocabulary bans, cancellations, durable facts, and explicit single-reply counterexamples. Opus's strict HOW/WHAT, scope-survival, and bounded-override tests rejected 366 of 461 proposed relabels, evidence that the abstraction is not simply “label every imperative rule.”
- Probe-shaped realization: the v2 text itself names “begin with the title,” “end with a P.S.,” and artifact continuation, precisely the check-19 failures. The subsequent Kimi scope rows repeatedly instantiate b3 shapes: `Keep it under 90 words` (`teaching-assistant-grading-scope.jsonl:15`, `financial-planning-chat-scope.jsonl:32`), `Now add a closing section ...` across many domains, angle-bracket titles (`event-planning-scope.jsonl:31`), lowercase-only constraints (`personal-assistant-scheduling-scope.jsonl:14`), and exactly five bullets (`sales-crm-agent-with-tools-scope.jsonl:235`). This is useful targeted development data, but it prevents treating b3 performance as generic transfer.

Conclusion: the ontology is plausibly generic; its empirical validation on b3 is probe-shaped. Only frozen post-development evaluation can establish generic transfer.

## 3. Lineage and nearest-neighbour audit

### Scope-pass comparison with the 38 H1′ constraint sentences

I decoded the 38 unique spans only from the permitted H1′ records and compared them with all 4,954 `kimi-scope` rows using offline CPU `BAAI/bge-small-en-v1.5` normalized CLS cosine, plus normalized-exact and character checks.

- Normalized exact matches: **0**.
- Per-query nearest cosine: min `0.6617`, median `0.7487`, mean `0.7675`, max `0.9208`; 11/38 are at least `0.80`, 7/38 at least `0.85`, and 1/38 at least `0.90`.
- Clear paraphrases/templates to flag:
  - `keep the reply under 90 words in total` → `Keep it under 90 words` twice (`cos=0.9208`), plus several artifact-specific 90-word caps;
  - `Now add a brief closing section for the same newsletter piece` → `Now add a closing section to the letter/report/agenda` (`cos=0.8742/0.8535/0.8510`);
  - `format the reply as exactly 5 bullet points` → `Keep the executive summary to exactly 5 bullet points` (direct masked-template analogue found by lexical inspection);
  - `in lowercase letters only` → `From now on, respond only in lowercase letters` (`cos=0.8684`) and `Use lowercase only in the calendar notes` (`0.8644`);
  - all six `begin with the exact title <<...>>` items → repeated “begin ... with a title in angle brackets” rows across event planning, scheduling, poetry, documentation, and other domains;
  - the reply word bans have many “never use the word/phrase ...” family analogues, though not item-level copies.
- No comparably close item paraphrase was found for the P.P.S. strings, four-placeholder lists, or “use word X no fewer than N times” items. Those nearest neighbours are mostly generic/weak (`~0.66–0.76`).

Because the scope pass was written after and in response to check 19, the clear template matches are not safely dismissible as coincidental taxonomy overlap. “No copy” is supported; “no row derives from b3” and “no paraphrase” are refuted.

### Relabel pipeline

The set arithmetic is correct:

- Kimi/unreviewed proposals: 461 label changes (plus 8 note records);
- Opus approvals: 95;
- sol approvals: 131, including 26 additions not in Kimi's proposal set;
- Opus∩sol over `(source,text,new_label)`: 59;
- final patch: 59, exactly equal to that intersection, with no final row outside the Kimi proposal set.

This is good evidence of conservative agreement on the old-data relabels. It does **not** remove probe knowledge. Kimi proposed under the b3-informed v2 spec; Opus and sol reviewed after that change; no blind-review prompt, accessible-file manifest, or no-contact record is present. Probe knowledge could enter through the spec, the generation brief, direct repository access, or reviewer context.

It also does not establish that the whole v2 training addition was reviewed. Every one of the 4,954 new rows has a `kimi-k3-scope:*` source. The 59-row final intersection contains 39 `kimi-k3-ctx`, 19 `kimi-k3`, and one `sol-enrich` row—zero `kimi-k3-scope` rows. Opus's review says it reviewed the 461 proposed **relabels**, not the 4,954 new scope rows. Describe the latter as Kimi-authored synthetic rows, not human-hand-written or independently row-reviewed data.

I did not inspect evaluation benchmarks, so item-level benchmark disjointness cannot be independently verified here. The evidence asserts it but does not supply source prompts or an auditable no-contact generation record. Moreover, `LABELS.md` still claims no overlap “not even by paraphrase of their instruction taxonomy,” while the README correction explicitly withdraws that policy for item-level disjointness, and the trainer logs say 282 taxonomy-category drops were not applied. The honest policy is deliberate type/taxonomy overlap with claimed item-level disjointness—not taxonomy-disjoint data.

## 4. Seed stability and the required identical-data rerun

Assuming the README's data split is accurate, the result gives useful but provisional stability evidence: seeds 1–2 are the identical-data replicate (`33/33` pin, `45/44` echo), while seed 0 is a robustness check to a small 59-label patch (`59/20,385 = 0.29%` of logged training rows) and lands at `33/46`. Pin-only is exact across all; echo ranges by two around mean 45. The selected span sets for retained seeds 0 and 2 are identical; their probability ranking differs, and echo order explains the differing echo outputs. This is much more stable than the frozen-embedding result, but it is not a formal three-seed identical-treatment replicate.

The asserted seed data split itself is not reproducibly recorded. Every training log says only `train 20385`; none records a data-manifest hash or applied patch list. The trainer unconditionally loads every `review/*-patch.jsonl` present. The final patch was committed before the check-21 result commit, and the current untracked seed artifacts do not provide immutable run manifests. Excluding the patch for seeds 1–2 therefore requires an unrecorded temporary filesystem state. Treat the mismatch as asserted, not verified.

The FINAL run must, before any post-development benchmark access:

1. freeze one identical train/held-out manifest and record its ordered file hashes, effective post-patch row hash, exact patch names/hashes, deduplication result, `train_n`, code hash, base-model revision/hash, and seeds;
2. train seeds 0/1/2 from that manifest, retain all per-seed score and session-row files, and hash each encoder/head/tokenizer artifact;
3. apply the already frozen no-context sentence scoring and inclusive `P(rule)+P(fact) >= 0.5` rule with no seed picking on b3;
4. report every seed and the predeclared aggregate. To retain the current stability wording, predeclare a criterion such as pin-total range ≤1 and echo-total range ≤2, and require no material regression from the current `33` pin / approximately `45` echo result. If it differs, replace the quick-check number with the identical-data result rather than choosing seeds;
5. retain full safety fields per arm and show pin-only and pin+echo separately against the full baseline.

## 5. Findings and grades

### HIGH 1 — b3 lineage/transfer overclaim

b3 changed the spec and generated training targets; clear post hoc scope-row paraphrases exist. Check 22 is not transfer, and “no training row derives from b3” is false under any ordinary causal meaning of “derives.” The README's narrower “development result on the selection set” wording is correct.

### HIGH 2 — “hand-written, reviewed, taxonomy-disjoint” is not supported

The 4,954-row scope pass is Kimi-authored synthetic data and was not covered by the two-reviewer relabel intersection. The live LABELS taxonomy-disjoint sentence contradicts the README's accepted item-level policy and trainer behavior. Claim only reviewed relabels, claimed item-level benchmark disjointness, and disclosed taxonomy overlap.

### MEDIUM 3 — three-seed identical-data stability is not yet established

Two seeds form the identical-data replicate; seed 0 is claimed to differ. Worse, no run manifest proves that split. The agreement supports provisional robustness, but the FINAL manifest-locked rerun is required before “stable across seeds” is used externally.

### MEDIUM 4 — three-seed safety is not auditable

Seed 1's rows were not retained, and seeds 0/2 retain only truncation and a Boolean degeneracy result. The surviving evidence is reassuring, but complete arm-specific timeout/truncation/degeneracy/invalid-output safety must be retained in the final run.

### MEDIUM 5 — cost and “ceiling” wording need narrowing

`0.86x` is correct only for pinned KV columns, excluding echo-context overhead. Full context `44` is a baseline, not a ceiling, because echo arms reach `45–48`. Say “matched the full-context baseline point estimate at 0.86x its finder comparator's pinned-column count,” not “reached the ceiling.”

## 6. Registration required before Multi-IF 909 or BFCL

The following must be frozen in a timestamped, immutable registration with every `[FILL]` resolved **before any benchmark prompts, responses, per-item scores, or diagnostics are viewed**:

```text
COHORT AND CLAIM
Multi-IF cohort: all 909 registered conversations; any subset is falsification-only.
BFCL cohort/version/split/hash: [FILL].
Primary claim: "A selector frozen after b3 development transfers item-level to [benchmark]
under real KV-cache eviction." We do not claim b3-independent spec development,
taxonomy no-contact, or benchmark-family no-contact. We claim item-level no-contact only,
subject to the lineage manifest below.
Primary unit, metric, aggregation over the three seeds, confidence interval/test,
multiplicity rule, success margin, and missing/invalid handling: [FILL EXACTLY].

SELECTOR
Sentence candidates are sentences from completed prior USER turns only.
Score each sentence without preceding-sentence or conversation context.
Keep iff P(rule)+P(fact) >= 0.5 (inclusive).
Sentence splitter implementation/hash and tie ordering: [FILL].
Evaluate seeds 0,1,2 and report the predeclared aggregate; do not choose a seed from
benchmark outcomes. Artifact selection/ensemble rule: [FILL].

ARMS
1 FULL: protected prefix + complete history, no eviction.
2 EVICTED: the registered real eviction policy, no retained candidate columns and no echo.
3 CLF_PIN: real eviction plus selector columns pinned.
4 CLF_PIN_ECHO: the identical selected columns pinned and their source text re-injected
   by the frozen echo template/order.
5 ROLE_CONTROL_PIN: exact-column matched control selected from the same prior-user role
   pool, with the same eligibility/age window and post-clamp column count.
6 ROLE_CONTROL_PIN_ECHO: the same control columns pinned and the same control text echoed
   with the identical template/order.
7 FINDER_PIN and FINDER_PIN_ECHO, if retained, are frozen descriptive comparators and may
   not be fitted or altered on benchmark outcomes.
Control sampling seed, exclusion/overlap rules, fallback tiers, and impossible-control
handling: [FILL]. Controls are constructed after every clamp.

REAL EVICTION AND BUDGET
Cache capacity, evictable range, eviction time, position-index policy, protected-prefix
length/rule, current-turn treatment, maximum pinned columns, clipping/ranking behavior,
echo token cap, generation max tokens, and deadline: [FILL NUMERIC VALUES/FORMULAS].
Instrument and assert actual removed/retained KV column identities and counts per layer.
Count and report separately: pinned columns, protected columns, evicted columns, echo-added
context tokens, final prefill length, and generation compute. Any cost-ratio claim names its
exact numerator and denominator.
For BFCL, the system prompt and complete tool/function-schema prefix are protected in every
arm, excluded from selector/control pools and budget comparisons; the current user turn is
also protected. The matched control comes from the same eligible prior-user role pool.
scripts/ledger_eval.py's text_ledger arm is not an eviction harness: it re-appends text to an
otherwise normal context. It cannot be used to establish an eviction claim.

ARTIFACTS
Record SHA-256 for each seed's encoder model.safetensors, head.pt, tokenizer/config, base
bge-small revision/weights, scoring code, sentence splitter, echo code, real-eviction code,
checker/scorer, LABELS.md, effective ordered training-row manifest, every patch, held-out
manifest, benchmark input/version, and environment lockfile. Store artifacts immutably.

SAFETY
Register per arm and per seed: timeout, truncation, invalid/empty output, repetition-based
degeneracy (exact formula/threshold), prompt/echo overflow, cache-integrity failure, and
checker failure. BFCL also registers malformed tool calls, invalid function/argument calls,
protected-prefix corruption, and execution errors. Register denominators, paired comparison
to FULL, allowed excess, stop rule, and whether any failed session remains in efficacy.

LINEAGE
Freeze a row-level author/source/hash manifest and the prompts/access manifests used by all
data writers and reviewers. State that b3 was used for mechanism selection, threshold history,
context/no-context choice, v2 spec development, data generation, and relabel review. Certify
that no Multi-IF/BFCL item, response, checker output, nearest neighbour, score, or diagnostic
was used for training, thresholding, model/seed selection, prompt/spec changes, or stopping.
Disclose known benchmark-family/taxonomy knowledge and claim only item-level disjointness.
Publish exact/normalized/fuzzy/embedding dedupe results under a predeclared flag threshold;
quarantine every flagged item before unblinding or mark the claim contaminated.

CLAIM WORDING ON SUCCESS
"On the frozen [benchmark/version] cohort under instrumented real KV-cache eviction, the
pre-registered three-seed spec-v2 selector [state exact arm and metric] versus [controls],
at [exact pinned-column and total-context costs], with [CI/test] and [safety counts]. The
selector and label ontology were developed on b3; this is post-development item-level
transfer, not b3-independent development and not proof of universal instruction retention."
```

The current classifier artifact directories are untracked and the quick-check logs do not register their hashes. They must not be used for an external evaluation until the identical-data rerun creates immutable manifests and hashes.

## VERDICT

**CONFIRMED-WITH-QUALIFICATIONS.** The check-22 outcome, means, reference totals, held-out numbers, threshold, no-context scoring, and pinned-column ratio are confirmed. The generic-transfer, b3-independent lineage, fully reviewed-data, taxonomy-disjointness, three-seed identical-treatment stability, and complete safety readings are not confirmed and must be narrowed or repaired as above.
