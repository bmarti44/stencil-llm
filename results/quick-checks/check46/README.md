# Check 46 — NO-GO

Data lineage: **fit none**. One unchanged prompt, six fresh Astra-authored examples, 20 DEV rows only from `kimi-admission-2.jsonl` and `kimi-overrides.jsonl`. Admission/relations heldout-3 received one frozen model look; both banks had prior exposure to other models. v8 SETUP is a development diagnostic. Taxonomy sources: [LABELS.md](../../../data/classifier/LABELS.md) and [LABELS-RELATIONS.md](../../../data/classifier/LABELS-RELATIONS.md). No fitting, benchmark reads or push.

Admission overlap **304/385 = 78.96% recall**, **89.94% precision**; relations **399/448 = 89.06% accuracy**, supersedes **150/172 = 87.21% recall**. SETUP **36/36 admits**, **58/96 false-admission turns**.

The registered bars remain: admission overlap recall >=85%, precision >=95%, payload/quoted false admission <=3% each and non-user zero; relations accuracy >=94% and supersedes recall >=85%; SETUP <=2/96 false turns and 36/36 admits. Exactly one passing admission/relations half yields PARTIAL. GO also requires SETUP. No threshold or prompt changed after the held-out look.

## Admission

| Match | Micro precision | Micro recall | Macro predicted-message precision | Macro positive-message recall | TP / FP / FN |
|---|---:|---:|---:|---:|---:|
|overlap|89.94%|78.96%|89.99%|72.49%|304 / 34 / 81|
|exact|17.46%|15.32%|13.23%|10.57%|59 / 279 / 326|

Maximum-cardinality one-to-one character-span matching and macro denominators are inherited unchanged from check44b/c. Broad spans cannot recover two gold rules. No semantic key/kind/value accuracy is claimed. Legacy scope counters in summary.json use check44’s scope vocabulary and are not a typed-register validation result.

| Negative family | False admissions | Rate | One-sided 95% Clopper–Pearson upper |
|---|---:|---:|---:|
|payload|6/57|10.53%|19.72%|
|quoted|4/36|11.11%|23.65%|
|non_user|4/34|11.76%|24.93%|

Payload means gold-negative `one_off_request`; quoted means gold-negative `quoted_or_reported`; non-user includes all non-user roles. These subsets can overlap. Bounds are message-level descriptive binomial bounds, not a deployment guarantee.

## Decoder and admission limit

Qualified image `vllm/vllm-openai@sha256:3dbe092ec5b2cef63b6104d33fa75d6ce53a7870962529ada69f78bbbc38e776`; exact qualified flags in server.json, including batch invariance, Triton attention, bf16, concurrency 4. Greedy, seed 0, thinking off, cap 512. Deterministic configuration inherited from qualification; no new cross-start determinism claim.

**XGrammar structured decoding was used for every call**: fixed strict-schema object fields plus a shared-suffix grammar accepting every nonempty contiguous character substring of the message in `span`. No fallback. Seven actual XGrammar-consumer witnesses pass (including quotes, backslash and newline). The actual auto selector with the model tokenizer and first submitted grammar selects xgrammar (backend-validation.json); the inspected engine uses a single backend. Post-parse strict schema and normalized substring validation remain active. Raw-verbatim **807/807**; normalized-inclusive **807/807**; normalized-only repairs **0**. Counts cover parsed operations in all 901 evaluation calls; full-response failures are separate: `{'truncated': 1}`; post-parse rejection categories: `{'add_has_target': 1, 'invalid_target': 1}`.

Normalization folds whitespace, curly quotes and case, then maps matched characters to original offsets. It does not repair paraphrases; ambiguous repeated spans are rejected. Thus this run separates semantic omissions/false admissions from check44’s non-verbatim decoder corruption. Its measured recall is the operating point of this frozen prompt, **not an architecture-wide admission ceiling**; no sentence-splitter ceiling is imposed. Comparison with check44’s 2.75% does not isolate model size because the model, backend and decoder changed together.

## Miss families

Descriptive definitions and exact member/miss IDs are in families.json. Admission author categories are reported directly. Cue-less is an explicit lexical proxy on gold spans; it is not a manually validated linguistic annotation. Multi-rule single-sentence subsets use documented punctuation boundaries. Relation subsets use author rationale idioms on gold supersedes rows, never as model inputs.

| Admission family | Recovered / gold spans | Overlap recall |
|---|---:|---:|
|two_rules|218/244|89.34%|
|rule_plus_payload|52/87|59.77%|
|buried_rule|34/54|62.96%|
|2_rules_single_sentence|116/140|82.86%|
|3_rules_single_sentence|37/39|94.87%|
|cue_less|180/212|84.91%|

| Relation miss family | Correct / gold supersedes | Recall |
|---|---:|---:|
|withdraw_replace|12/12|100.00%|
|bare_value_temporal|17/18|94.44%|
|task_override_global|0/21|0.00%|
|actually_B|7/7|100.00%|

All 21 task-over-global misses emitted add rather than supersedes. The frozen prompt explicitly defined overlapping-scope replacement, so this is an operation-choice failure, not corrupted span text. Rule-plus-payload and buried-rule admission recall also remain low despite valid substrings.

## Relations

| Label | Precision | Recall | F1 | Correct / gold |
|---|---:|---:|---:|---:|
|none|79.01%|96.24%|86.78%|128/133|
|supersedes|92.59%|87.21%|89.82%|150/172|
|cancels|100.00%|72.55%|84.09%|37/51|
|completes|97.50%|95.12%|96.30%|39/41|
|reinstates|97.83%|88.24%|92.78%|45/51|

Positive-target identification: **281/315** gold transition rows had an overlapping emitted relation targeting r1 (independent of correct operation). Raw emitted relation target IDs: **285/285** equal r1 before validation. A one-rule register tests reference recovery only, not multi-target discrimination. Gold candidate text/label is not supplied. The bank lacks kind/value fields, so these are empty strings; version defaults to 1, with the original rule text, key, scope and status preserved. Multiple overlapping operations or invalid output count as errors; no operation maps to none. Gold-offset repairs on held-out relations: **0**.

SETUP is the inherited independent-turn admission diagnostic: empty register, up to two preceding user sentences; recovered admits **36/36**, replacement spans **4/4**. It is not a predicted-register lifecycle rollout.

## Cost and validation

All 921 calls recorded: 20 DEV +357 admission +448 relations +96 SETUP. GPU held **40.887/60 minutes**, including startup, profiling, CPU work while held and cleanup. Evaluation schedule **1807.867s**, amortized **2.007 GPU-s/message** at concurrency 4; all-in **2.723s/evaluation message**. These amortized costs are not isolated request latency.

User-role requests: mean latency **6.009s**, median **5.951s**, p95 **15.359s**; mean input/output **1444.9/67.7 tokens**. All-role latency median/p95 **5.815/15.114s**. One extra updater call per user message; no monetary tariff assumed.

Freeze: examples/prompt 52cdb6d6; first harness b3b8a38b; final freeze 519c7338. DEV had five malformed gold end offsets with unique literal quotes; the frozen scorer repairs only those uniquely locatable quotes and journals the count. Initial held-out loading stopped before inference on summary headers; recovery took a second physical source read into committed snapshots and skipped headers (8742da2d). One model look only; prompt, parser and scoring remained frozen. Records contain same-call raw outputs, visible inputs, usage and timing. Audit replays request hashes and parser outputs from saved records; six targeted CPU tests and seven XGrammar witnesses pass. All artifacts <=10MB. Owned container removed and RUNNING.flag deleted; no host/other-process signals.

## Disposition

Neither half passes. Explicit entry stays the automatic-path boundary; no runtime swap or new fitted model is shipped. Next hypothesis: a small dense generative updater fine-tuned on the provenance-reconciled, audited authored corpus. **Prospective lineage:** fit only on clean authored register/message/operation examples and audited authored-input labels; scenario-disjoint DEV; evaluate once on a fresh author-disjoint bank. Exclude heldout-3 prompts, labels, outputs, error-derived paraphrases and every benchmark item/response from fitting. Existing heldout-3 becomes a disclosed secondary diagnostic. No training was performed or launched here.

## Orchestrator addendum after the fable accuracy review (2026-09-06; results/check46-review-fable.md)
Numbers and freeze order verified; NO-GO correct; PARTIAL correctly withheld. Corrections/diagnosis: only 12 of 81
admission misses are broad-span-over-list; 69 are messages where the trunk emitted `[]`, with the gold rule sitting
after a payload or chatter in 59 of them (a one-span-per-clause fix caps at 82.1% recall; the real lever is a
rule-after-payload positive exemplar in the few-shot bank). False spans: 22 are the one-off request admitted as an
invented task rule; role + template gates give quoted 0/36, non-user 0/34, payload 0/57 but precision only 93.3%.
SETUP 58 false turns are all user-role (52 template, 12 inert-quote, 6 empty-register cancels/completes emitted as
add): template + quote gates plus a populated typed register leave <= 2/96. Task-over-global 0/21 is a prompt/
exemplar gap (all emitted `add`), and scope is mostly wrong overall (226/266 global golds emitted as invented task
scopes). Trunk remains the best admission recall (78.96 vs 64.16/60.3) and best supersedes recall (87.21 vs 73.26)
with a complementary error shape. Latency is output-token bound (empty calls 0.63 s; ~12.9 tok/s per request).
Consequences: check 48 must beat R 78.96 / P 89.94; any prompt change requires a FRESH author-disjoint bank (both
held-outs are now exposed); the cheaper alternative is trunk-proposer + small fitted verifier.
