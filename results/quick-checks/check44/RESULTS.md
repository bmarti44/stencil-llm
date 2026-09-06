# Check 44 — operational NO-GO; semantic comparison limited by decoder integration

**Cut unattended admission from the first ship; use explicit structured rule
entry.** The frozen A stack failed the registered quick bar. This is not a clean
negative result about the underlying LLM's semantic ability: valid JSON frequently
contained corrupted evidence strings, and the frozen token filter excludes some
legal merged string-ending tokens. No held-out output was normalized, rescued,
rerun, or used for fitting/prompt/threshold selection. No800-message bank was built.

The [pre-written reading](README.md) and recipe were committed in242140fb before
A inference. Same338 Fable messages,185 positive messages,218 gold rule spans;
one held-out prediction per message per arm. A/B fit-on in this check=none;
prompt/DEV=24 original Astra messages, first six demos. C was skipped at the
original arm-construction check:870 Kimi rows<1500. That decision was frozen
before CPU/GPU DEV and before any held-out prediction.

| Arm | Exact span P / R | Overlap span P / R | IoU>=.5 P / R | Binary message P / R |
|---|---:|---:|---:|---:|
| A, validated frozen1.7B extractor | 18.75% / 1.38% (3/16;3/218) | 37.50% / 2.75% (6/16;6/218) | 31.25% / 2.29% | 46.67% / 3.78% |
| B, unchanged ft-v3 seed0 head | 71.35% / 58.26% (127/178;127/218) | 98.31% / 80.28% (175/178;175/218) | 89.33% / 72.94% | 98.31% / 94.05% |
| B_register, unchanged v8 consumer | undefined / 0% | undefined / 0% | undefined / 0% | undefined / 0% |

Primary recall is **micro, one-to-one span overlap**, fixed before evaluation.
Macro recall over positive messages is A2.97%, B85.41%; it does not replace that
primary metric. Macro precision over predicted messages is A36.67%, B98.31%.
B detects174/185 positive messages, but matches only34/66 spans on the33 two-rule
messages: its sentence-level proposals often combine two annotated clauses.
Single-rule and rule+payload overlap recalls are111/119 and30/33. This explains
much of the difference between B's message and span recall.

| Negative family | A false admissions; one-sided95% upper bound | B false admissions; one-sided95% upper bound |
|---|---:|---:|
| Registered one-off/payload flag | 8/102 =7.84%;13.71% | 2/102 =1.96%;6.04% |
| Quoted/reported | 0/52 =0%;5.60% | 1/52 =1.92%;8.80% |
| Non-user roles | 0/12;22.09% | 0/12;22.09% |
| Tool | 0/7;34.82% | 0/7;34.82% |
| Assistant | 0/5;45.07% | 0/5;45.07% |
| All gold-empty messages | 8/153 =5.23%;9.24% | 3/153 =1.96%;4.99% |

The registered payload family uses gold-empty AND one_off_request. It includes
one quoted item, hence102 rather than the author's101 payload_request-category
items. On that narrower category, A is8/101=7.92%, B2/101=1.98%; the reading is
unchanged. Family overlap is one message. Bounds are Clopper-Pearson, conditional
on independent messages; this one-author bank supplies no scenario IDs, so
scenario-level bounds are unmeasured. Zero quoted admissions cannot certify a
<=3% population FPR here. Non-user zero is protected by the explicit role guard;
A proposed three raw non-user candidates, all rejected. Before validation, A
returned nonempty rule lists on91/102 payload negatives and35/52 quoted negatives;
these are unvalidated proposals, not admitted-write metrics or salvaged scores.

A fails both required recall>=85% and payload FPR<=3%. Its0 quoted admissions
do not compensate for these failures. B is descriptive, not an eligible A/C
replacement under the registered rule, and its span recall also falls below85%.
B_register writes nothing: its specialized scope parser finds no usable binding
with current_task=None in this independent-message bank. Its zero false-admission
rate is complete abstention, not evidence of a working admission pipeline.

**Why A failed operationally.** All338 raw outputs parse as JSON. They contain
314 candidates, of which16 survive validation. Rejections are289
nonverbatim-or-nonunique, six ungrounded scopes, and three non-user candidates.
178/185 positive messages have at least one provenance rejection.275/314 raw text
fields and277/314 evidence fields end with an added apostrophe/comma/space suffix;
274 raw outputs contain tabs. These are valid JSON strings with unsupported
source bytes, so rejecting them was the registered behavior.

The [model-free decoder diagnostic](decoder-diagnostic.json) accepts a complete
synthetic JSON string at the character-parser level, while the token filter
rejects the legal merged token47891 (`.","`) after `Hello`. This reproduces the
tokenization restriction already noted in the [CPU smoke record](cpu-smoke.json).
I treated successful character-token JSON paths as sufficient integration smoke
coverage; that was inadequate for evidence-preserving greedy decoding. The audit
establishes token exclusion and widespread string corruption, but does not measure
counterfactual LLM performance with a corrected decoder. Do not interpret A's2.75%
recall as an isolated measure of its discourse understanding. No punctuation
cleanup, permissive source matcher, new decoder, or second prediction pass was
used to improve the registered result.

Scope class and literal scope agree on4/6 A overlap matches. B has unknown scope
on all175 matches because its head supplies no scope prediction and the frozen
specialized parser has no binding. A has zero matched within-message key-pair
support; B has one pair, correctly distinct. Literal semantic-key slug agreement
is unmeasured: A's memo-defined schema emits NEW, followed by opaque allocations.
There are no existing-key relations or cross-message identity tests in this bank.

Held-out latency: A GPU batch1 p50/p95=2.785/4.432s, max7.021s; B CPU
p50/p95=.0568/.0646s. These are different deployment devices. Total GPU charge is
1084.249s=18.071min/90min, including the failed83.269s preflight and model reload;
overall peak torch-allocated GPU memory3.729GiB. GPU24DEV completed; the initial
conservative projection was3264.883s. The separate fp32/four-thread CPU timing
stopped naturally at its1800s token-boundary cap (actual1801.005s):20 complete
messages and one partial.19 warm complete calls have p50/p95=94.267/188.218s.
All exceed1024 input tokens; the<=1024 stratum and integrated single-repository
shipping latency remain unmeasured. CPU outputs did not select the prompt.

**Preflight repair and audit.** The author bank has one summary header plus338
messages. The original loader counted339 objects and stopped before any held-out
prediction. [REPAIR.md](REPAIR.md), preflight-v1/, and the39731964 repair commit
preserve the failure and narrow header/resume fix. Saved24DEV results were reused;
the original prompt/schema/GO/README stayed frozen. Source bytes were reopened
for metadata diagnosis; “one pass” denotes predictions, not a single file-open.

[audit.json](audit.json) replays all338 records, validators and all arm scores.
[validation.json](validation.json) verifies all338 prompt hashes and token counts,
redecodes all output token lists, confirms all raw JSON parses, checks package and
source hashes, and matches the100/200-record recovery checkpoints to final records.
Synthetic header consumer tests, provenance/matching/bound selftests and scoped
lint pass. No held-out predictions were repeated. Own GPU flag removed naturally;
no process was signalled, no benchmark/sealed input was read, and nothing pushed.

Complete metrics are in [summary.json](summary.json), every input/raw JSON/accepted
span/rejection/head probability/consumer trace in [records.jsonl](records.jsonl),
and the exact source snapshot in [evaluation-bank.jsonl](evaluation-bank.jsonl).
