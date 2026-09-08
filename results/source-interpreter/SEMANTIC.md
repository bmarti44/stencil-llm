# Fresh source-interpreter comparison

Draft for independent review, 2026-09-08. No data authoring or model launch
until the specification is accepted. Actual FIT-result audit is concurrently
pending. This is a small falsification screen, not the larger coding proof.

Fit-on: only the eighteen accepted FIT rows already used for the fixed final
adapter. Development-on: none in this comparison. Evaluated-on: six wholly new
conversation families, assigned withheld before Kimi authoring. No benchmark,
spent bank, prior response or old adapter is a source for these conversations.
No fitting, prompt changes, checkpoint selection, cap changes or recipe tuning
on this bank, its labels, lengths or model responses. After the one look it is
spent; later executable coding evidence must use separately authored families.

## Question and fixed candidates

Does the already trained helper recover complete current standing instructions
on new conversations, and how does its unchanged original model compare?
Use the final adapter from fit/run-01, SHA256
1f9392f3fa99cb31a010176487a6f37999f02cdbc7be9b9cdb4a9b9380e592e3,
and the same original local Qwen3-4B assets, tokenizer and environment as FIT.
No new training. The trained adapter is the prospectively selected candidate;
the base is a control, not a replacement selected from evaluation outcomes.

Both receive only the authentic source prefix through the current query, using
the unchanged source_interpreter.py system/user templates and nonthinking
tokenization. No gold target, prior generated focus or future source enters
generation. Preserve the same greedy native HF settings, output cap2048,
EOS151645 and pad151643 as FIT.md. No grammar, extraction, repair or retry.
Load the original trunk once with the saved adapter, switching enabled state
without merging or sharing generation caches. Freeze code, bytes and complete
request order before the first call.

## Fresh packet

Kimi K3 via the existing local Ollama endpoint authors six original documents,
each with exactly three work-request checkpoints. Retain the existing document
schema, with split withheld. Use two short conversations (8–12 messages), two
medium (16–24), and two longer (32–48). Final query is the final source message.
All eighteen checkpoints are retained; prefixes of one conversation are not
independent cases. These are fictional coding discussions, not executed projects.

Preassigned family slots, whose concrete names/requirements Kimi must invent:

| Index | Conversation / family suffix | Band | New domain |
| --- | --- | --- | --- |
| 00 | source-semantic-20260908-00 / source-semantic-family-20260908-00 | short | ferry maintenance scheduling software |
| 01 | source-semantic-20260908-01 / source-semantic-family-20260908-01 | short | seed-library inventory software |
| 02 | source-semantic-20260908-02 / source-semantic-family-20260908-02 | medium | community radio playlist auditing |
| 03 | source-semantic-20260908-03 / source-semantic-family-20260908-03 | medium | bicycle route surface inspection |
| 04 | source-semantic-20260908-04 / source-semantic-family-20260908-04 | longer | theater costume alteration tracking |
| 05 | source-semantic-20260908-05 / source-semantic-family-20260908-05 | longer | rainwater tank sensor reporting |

Across the packet require global and scoped rules, conditional permissions,
exceptions, adopted versus unadopted suggestions, inert quoted/tool text,
replacement, retirement and reinstatement. Each conversation includes a
meaningful instruction change between checkpoints, with consequences visible
in its targets. One checkpoint in00 has genuinely empty standing focus after
retirement; the other seventeen retain meaningful standing instructions.
No example source text or gold wording is supplied. Do not shorten or simplify
requirements to fit a token allowance.

Kimi authors sources and complete prose targets with visible source citations.
Astra independently checks all labels against the sources before target-model
access, including semantic family independence and ambiguity. Preserve raw
author requests/responses and all corrections. Only Kimi may correct semantic
content; no model-response-informed correction is allowed. A single bounded
label-correction batch may address enumerated label defects with source and
metadata frozen. Unresolved source ambiguity or labels stop preparation rather
than deleting/replacing difficult cases or repeatedly correcting them.

CPU preparation uses the existing generic validate_corpus/prepare_rows path;
the FIT-only preview entry point must not be relabeled or its checks bypassed.
Record all source/target/prefix hashes and actual lengths without truncation.
Freeze a generation manifest containing prefix IDs and visible source IDs but
no targets. Record a separate sealed reference-label manifest. Prefix plus2048
must fit the conservative native32768-token context; incompatibility stops the
whole preparation, with no selective removal or shortening. Target lengths
are descriptive and cannot change the output cap or label semantics.

## Execution and cost

Run all eighteen paired queries: thirty-six total generation calls. Visit
conversation indices00–05 in order, each query in source order. For flattened
row index r, base goes first when r is even and adapter first when r is odd.
This balances first-call order nine times each, while keeping paired inputs
identical. Each request starts with an empty cache. No warm-up or extra call.

Retain complete input/output IDs, decoded UTF-8 bytes, native resolved settings,
actual adapter identity/state, EOS/cap/deadline facts, whole-call latency and
resources. Reuse the reviewed FIT single-call consumer where safe, adding a
per-query path so receipts cannot overwrite one another. No training or new
serving stack is needed. Sol implements only the bounded new consumer/tests;
do not alter frozen FIT/mechanics code or build a general experiment framework.

The actual FIT pair cost40.517819119+123.050696406=163.568515525 seconds.
Eighteen such pairs estimate2944.233279450 seconds. Retain the entire observed
161.890731962-second initial training/persistence interval as a conservative
setup allowance (it includes work this test does not repeat), plus60 seconds
for final verification/publication: total3166.124011412 seconds, about52.77
minutes. This is an extrapolation from one FIT prefix and unequal outputs,
not a throughput guarantee for unseen longer prefixes. Authoring and remote
review time are additional and reported separately; no paid API/new compute.

Four times the estimate is12664.496045648 seconds. Impose a STRICTER whole
process bound of3600 seconds to retain the quick-check one-GPU-hour ceiling;
do not authorize the larger allowance. Each call retains300 seconds, startup
has660 seconds, and the final15 seconds are reserved for cleanup. The whole
ceiling always wins. The outer owner measures from before supervisor launch
through process exit/final publication and kills/reaps only its owned group.
Stop on a technical exception/deadline, preserve completed/partial/unavailable/
not-attempted distinctions, and classify the test INCOMPLETE. No resume or retry.
Ordinary returned cap/invalid answers count as failures and the remaining fixed
calls continue. Longer actual inputs may make the estimate optimistic; the
response is an honest incomplete result, never dropping queries or raising limits.

## Semantic assessment and prospective decision

Before opening responses, fix a blinded response-ID mapping and evaluator
instructions. Astra xhigh and Kimi K3 independently judge the complete returned
answers against the same source prefixes and accepted reference targets,
without model names, arm labels, latency or token counts. Natural prose may
have more than one valid wording or grouping; exact target-string matching is
not a semantic test. A supported equivalent interpretation may pass even when
it differs from the reference. The source is authoritative.

For each of36 scheduled responses, record structural completion and these
separate semantic defects with source evidence: omitted applicable instruction;
unsupported added instruction; wrong authority; wrong scope/condition/exception;
wrong permission/obligation modality; stale or prematurely reinstated rule;
and missing/incorrect supporting citation. Record each defect as present/absent
per response, allowing overlap. Complete-current-focus success requires a
complete structurally valid response and no material semantic defect. Capped,
malformed or unavailable responses fail; do not salvage a good-looking prefix.
Report structural failures separately, without inventing detailed semantic
judgments for unrecoverable output. No claims that absent defect coding means
an invalid answer is semantically correct.

Preserve both independent judgments. Root verifies disagreements against source
and sends specific evidence for Astra adjudication, recording the original
votes and final rationale. Any unresolved material ambiguity is scored failure
for the affected response and disclosed; never exclude a pair. Evidence of a
reference-label defect after unblinding makes that checkpoint ineligible for
an unqualified semantic claim and the overall screen INELIGIBLE, not a repaired
or smaller scored bank. Raw structural outcomes and costs remain reportable.

Primary descriptive measure: complete-current-focus counts per conversation
(0–3), and aggregate/18 for each arm. Also report fully correct conversations
(0–6), every defect frequency and all measured costs. Primary inferential test:
one-sided exact paired sign test of trained>base on the SIX conversation-level
counts, dropping only statistical ties in the binomial denominator. All six
scheduled conversations remain in reports. Zero discordances yields p=1.
Six wins and zero losses yield p=1/64; five and zero yield p=1/32. No test of
eighteen correlated rows as independent, no multiplicity of primary tests, no
evidence-of-equivalence claim from a nonsignificant result.

Separately, the prospective practical screen is trained success at least12/18
checkpoints, including at least one in every conversation. This deliberately
allows errors: it is a pragmatic bar for spending on a later worker test, not
a statistical proof, production standard or perfect-selector prerequisite.
If below the bar, park this fixed recipe after the one look; do not immediately
tune on its failures. If the bar passes, propose a separately registered fresh
coding-utility comparison whether or not superiority over base is significant.
Claim learning improvement only if the registered sign test gives p<=0.05;
otherwise report the difference as descriptive. A control that performs well
cannot be promoted as a newly selected candidate using this withheld bank.

No outcome here proves better code, useful manual-prose parity, robust long
sessions or the whole goal. Those still require adequate fresh executable
projects, comparing automatic focus with ordinary history and useful manual
reminders, measuring correctness, adherence and cost. Automatic usefulness
comparable to good manual prose remains a meaningful benefit; register
representation superiority is not required.
