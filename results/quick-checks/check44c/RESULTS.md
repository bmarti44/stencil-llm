# Check44c — NO-GO (2026-09-06)

**Explicit structured entry remains first ship. No runtime swap or gate v9
is authorized.** The designated seed0 C2+B fails three registered bars; C2 alone
has identical predictions and fails the same bars. No threshold, seed or model
was changed after the look.

| Heldout-3 / SETUP bar | Both frozen arms | Required | Result |
|---|---:|---:|---|
| Heldout-3 overlap micro recall | 247/385 = 64.16% | ≥85% | FAIL |
| Payload negative-message admissions | 0/57 | ≤3% | pass |
| Quoted negative-message admissions | 2/36 = 5.56% | ≤3% | FAIL |
| Non-user admissions | 0/34 | 0 | pass |
| SETUP false-admission turns | 10/96 | ≤2/96 | FAIL |
| SETUP admit events recovered | 36/36 | 36/36 | pass |

All six model thresholds were frozen in commit `fd43ff8f` before evaluation.
Recipe/split commit `08e5fb3d`; audit/pre-registration `ab977033`.
The fresh bank was already committed before model freeze, but its contents were
first opened only in evaluate(), after the freeze commit. Evaluation-start.json
records the bank blob and freeze digest. Heldout-3 has357 messages/385 gold spans,
18 author-disjoint domains,246 positive messages and111 gold-empty messages.
Its71 two-rule and34 three-rule messages contribute244/385 gold spans; the
remaining141 positive messages contain one rule each. Family denominators follow
44/44b: gold-empty AND family flag; categories and families are not interchangeable.

## Span metrics

Both C2 and C2+B have exactly the same accepted spans on every evaluation and
SETUP message. B adds zero spans at its DEV-selected threshold. Values below
therefore apply independently to both arms.

| Bank | Exact micro P / R | Overlap micro P / R | Exact macro P / R | Overlap macro P / R |
|---|---|---|---|---|
| Heldout-3 (primary) | 31.76% / 26.23% | 77.67% / 64.16% | 38.93% / 27.71% | 86.98% / 70.26% |
| Heldout-2 (SECOND LOOK) | 56.61% / 51.69% | 88.89% / 81.16% | 64.35% / 56.25% | 93.35% / 84.94% |
| SETUP (development) | 0.00% / 0.00% | 73.58% / 97.50% | 0.00% / 0.00% | 80.80% / 95.83% |

Macro P averages predicted messages; macro R averages positive messages.
Heldout-3:318 predictions,247 true matches,71 unmatched predictions,138 misses.
Heldout-2:189 predictions,168 true matches,21 unmatched predictions,39 misses;
recall81.16% versus check44b C72.95%, a secondary regression comparison only.
SETUP:53 predictions,39/40 overlap matches,14 unmatched predictions on10 turns;
36/36 admit and3/4 supersedes events recovered, with4/96 request-template
false admissions. Exact SETUP matches are0/40: overlap recovery does not certify
complete, executable rule extraction. Gold-empty SETUP admissions are0/72;
that narrower number excludes false extra spans on positive turns.

## False admissions and uncertainty

One-sided95% Clopper-Pearson upper bounds; point rates govern the registered bar.
These message-level intervals do not certify population rates or independence.
Both arms have the following counts and bounds.

| Bank | Family | Admissions / messages | Rate | CP upper95 |
|---|---|---:|---:|---:|
| heldout3 | payload | 0/57 | 0.00% | 5.12% |
| heldout3 | quoted | 2/36 | 5.56% | 16.47% |
| heldout3 | non_user | 0/34 | 0.00% | 8.43% |
| heldout3 | all_negative | 2/111 | 1.80% | 5.56% |
| heldout2 | payload | 1/97 | 1.03% | 4.80% |
| heldout2 | quoted | 2/57 | 3.51% | 10.64% |
| heldout2 | non_user | 0/30 | 0.00% | 9.50% |
| heldout2 | all_negative | 3/154 | 1.95% | 4.96% |

Supplementary scenario-family-bounds.json groups by the author's actual `scenario`
field (the inherited aggregator recognizes only `scenario_id` and leaves its
inline scenario_groups null). Heldout-3 scenario upper bounds: payload0/56→5.21%,
quoted2/36→16.47%, non-user0/34→8.43%, all-negative2/92→6.69%. The sidecar also
contains heldout-2 bounds. This is a saved-record reporting supplement, not a new look.

## Candidate generation and interpretation

The ideal BIO token-run ceiling is **385/385=100% on heldout-3**,207/207 on
heldout-2, and40/40 on SETUP; exact tokenizer-edge representability also happens
to be100% on these banks. No overflows. In general an edge inside a token cannot
be returned exactly, and two gold spans sharing one token are not independently
representable; >512-token messages abstain. B starts a new run even next to B/I.
C2 has no sentence splitter; the B fallback retains B's registered sentence path.

A perfect representational ceiling did not produce a good learned decoder.
Post-hoc saved-record accounting (no selection): the actual unthresholded BIO
runs match291/385=75.58% on heldout-3, before confidence filtering. Thresholding
reduces that to247/385. Thus94 misses remain even with all decoded runs admitted;
44 further matches are lost to the frozen confidence threshold. Additional
fragment predictions reduce precision. These are decoder/matching and confidence
measurements, not causal attribution to individual training examples.
The prospective combination contributes nothing on DEV or either held-out bank
or SETUP; it doubles CPU cost here without improving accuracy.

## Data audit, split and training

Fit-on:2,872 original kimi messages after53 inherited Opus label replacements,
231 Opus enrichment messages,1,572 retained messages from the1,577-row kimi2
pass after Astra review. All1,577 messages and spans were read on CPU against
LABELS.md. The122-row patch includes five dropped unfilled authoring placeholders,
missed task-writing/adopted-quote constraints, typos in future markers, erroneous
non-user admissions and one-off operations. No new messages were authored.
Kimi2 gold spans1289→1396; gold-empty769→668 after drops and corrections.
The raw pass still has **zero literal “Standing rule:” messages**, and only
3 positive/10 negative “should always” messages after the patch; the requested
source did not fully close those phrasing gaps. No heldout/gate text was added.
Manual label review remains fallible; inaccessible benchmark corpora were not
opened for deduplication and perfect semantic disjointness is not claimed.

4,675 messages total; fit4,209 (2603 gold spans), DEV466 (286 gold spans), DEV9.97%
across13 domains. No author scenario IDs existed: whole(domain,source-generation
batch) groups are the registered scenario-family proxy. No within-batch split;
this is not domain-disjoint and cross-batch paraphrase relatives cannot be ruled
out. Full split IDs and grouping receipt are in the model directory.

Three fixed seeds,3 epochs each,396 updates/seed, no seed/checkpoint selection.
GPU allocation88.546/3600 seconds (1.476 minutes), peak1.494GiB; first10-update
pilot projected269.619 seconds. CPU calibration occurred after GPU release.
No other fitting, no signals, no background jobs, no push. The cooperative flag
was removed on natural completion.

## DEV threshold derivation

Same250 empty DEV messages, budgetfloor(.02×250)=5, for C2 and total C2+B.
Lowest feasible >= threshold maximizes recall of nested admitted sets; above1
abstention is included. Combination form was motivated by44b's second-bank
review and registered before this fresh look. B overlap with DEV: **1/871
sentences** appear in ft-v3 seed0 fit_ids. C2+B and C2 DEV spans are identical.

| Seed | t | t_low | Empty false admissions | DEV overlap recall |
|---|---:|---:|---:|---:|
| 0 | 0.7273366828 | 0.9039153621 | 5/250 | 268/286 = 93.71% |
| 1 | 0.6049145322 | 0.8081128010 | 5/250 | 269/286 = 94.06% |
| 2 | 0.7001239357 | 0.9026749514 | 5/250 | 270/286 = 94.41% |

All tested candidate thresholds and counts are in dev-threshold-derivation.json.
Seed0's immediately lower span candidate0.7262046912 admits6/250 negatives;
selected0.7273366828 admits5. The threshold remains sensitive to one message.

## CPU latency and verification

CPU4 threads, milliseconds; exclude model loading and first message per bank.
Combination cost includes both heads and merge; no conditional-cost discount.
All-message latency distributions are also in summary.json.

| Bank | C2 p50 / p95 ms | C2+B p50 / p95 ms |
|---|---:|---:|
| heldout3 | 87.90 / 96.01 | 181.39 / 200.73 |
| heldout2 | 85.72 / 94.74 | 173.68 / 190.29 |
| setup | 93.14 / 101.38 | 207.85 / 255.44 |

All783 evaluation/SETUP records journal token offsets, BIO distributions, spans,
confidence, B proposals, accepted spans, scores and timing in the same run.
Audit re-decodes them and reproduces all counts. Independent audit_records.py
uses SciPy assignment matching and beta quantiles, verifies exact/overlap micro
and macro metrics, family bounds, SETUP events, and all1398 DEV records/thresholds.
The initial built-in audit compared tuple match pairs with their JSON list forms;
this serialization-only assertion was repaired after evaluation. The original
runner is preserved as frozen-focus_check44c.py; audit-repair.json binds old/new
hashes and verification enforces AST identity of every function except audit and
verify_recipe. All2349 arm scores match after JSON normalization. No inference,
training, thresholds, predictions, matching algorithm or outcomes changed.

Focused BIO/adjacent-span/orphan-I/role-guard tests, strict threshold-boundary
check, import-safety check and runner Ruff checks pass. Weights remain local as
safetensors, with committed hashes and metadata in admission-v2/manifest.json.
The freeze, raw records and independent verifier are the reproducible evidence.
