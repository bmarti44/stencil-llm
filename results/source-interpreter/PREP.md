# Source interpreter — FIT-only label and length preparation

2026-09-08. Fit-on none so far; this packet is prospectively FIT-only calibration
material, not evaluation. All six conversations and their scenario families are
assigned FIT before authoring or prefix expansion. Future DEV/withheld data will
be wholly new conversations and families; their labels, lengths and outputs will
not determine this packet's formatting or future training hyperparameters.
All exposed earlier coding/focus examples and benchmark-derived rows remain
excluded. Kimi K3 via existing local Ollama authors the semantic content; Sol
xhigh implements; Astra xhigh independently reviews. No new API, download,
external compute, target-model inference or training is authorized by this CPU step.

Decision basis: results/coding-auto-reasoning/research-next/research-astra.md,
SHA879f1ece8e7a8b5cd5fef63cb3808073e870d7255c0cfec8c1038ae451c71bdc.
Root verified its seven local bindings, consequential VerIH methods/results,
extractive-compression distinction, documented Qwen nonthinking switch and LoRA
parameter arithmetic. This selects a small preparation unit, not a successful
mechanism. Original untrained recipes and their thresholds remain frozen.

The candidate is one fresh Qwen3-4B LoRA interpreter emitting a complete current
focus JSON object. Any later semantic test compares it with the unchanged same
base under identical local HF nonthinking generation settings; no worker/server
framework is needed to falsify the isolated learning hypothesis. Training
mechanics, training recipe/budget, fresh transfer and downstream code utility are
separate later decisions. A perfect selector/manual comparator is not a universal
prerequisite for future paired utility evidence. The full goal still requires
adequate fresh larger executable proof, beyond this packet or selector scores.

## Packet and source semantics

Author six independent original coding-session conversations, each with three
work-request checkpoints: two short(8–12messages),two medium(16–24),two longer
(32–48). These bands calibrate lengths, not a compression or simplification cap.
Messages should contain meaningful project discussion and changing directions,
not repeated filler. Source tasks are natural requests; this packet does not
need executable reference modules, public/private code tests or manual answers
to the requested programming algorithm.
The final query must be the conversation's final source message, so every
conversation supplies a checkpoint over its complete history. Report actual
prefix token lengths separately from these whole-conversation message bands.

Use varied original scenario families and natural wording. Across the packet,
cover global and task-scoped standing rules, conditional permissions, exceptions,
explicit adoption versus unadopted assistant suggestions/quoted directions,
retirement/replacement and irrelevant future-task rules. Include one genuinely
empty-current-focus checkpoint in a short conversation after all prior standing
rules cease to apply; the programming request still supplies its own algorithm.
No gold source wording or scenarios from spent examples are supplied to Kimi.

At each checkpoint, target all currently applicable standing constraints and
conventions, with correct scope, modality and exceptions, citing visible original
message IDs. The current programming algorithm need not be repeated. Preserve
self-contained unchanged source wording when suitable; use accurate scoped prose
when interpretation across messages is required. A citation is not proof of
coverage or entailment. Kimi authors source and targets; Astra checks targets
against the exact source rather than accepting author confidence as evidence.
No root-authored semantic correction, oracle fallback or gold simplification.

## Exact document schema

Each author emits one JSON object with exactly:

- schema_version:1
- conversation_id: nonempty string, fixed by the authoring request
- family_id: nonempty string, fixed by the authoring request
- split:"fit" for every document in this packet
- messages: ordered list of objects with message_id,role,text and optional
  task_handle; roles are user,assistant,tool; IDs and text are nonempty strings.
  task_handle, when present, is nonempty and occurs only on a user work request.
- queries: exactly three objects with message_id and target. Each message_id
  identifies a distinct user work-request message with a task_handle; query order
  follows source order. The target is exactly {"obligations":[{"text":..., 
  "source_ids":[...]}]}; text is nonempty and citations are visible nonempty IDs.
  An empty obligations list is valid when there are no current standing rules.

Every source prefix ends inclusively at its query message. Preserve original
roles,text,IDs,order and task_handle; no future message, target, annotation or
previous generated focus enters input. All source messages with task_handle must
have their query; no hidden extra work checkpoints. IDs are unique within their
conversation. Family and conversation identity are checked before prefix
expansion; shared family IDs cannot cross splits. Structural checks do not prove
semantic independence of differently named families; independent review does.
A reusable validator may accept fit/dev/withheld splits, but this calibration
invocation accepts only the six preassigned FIT documents. No withheld data is
created or consulted to select lengths, caps or hyperparameters at this stage.

## Local format and CPU evidence

Use the verified original models/qwen3-4b-hf tokenizer and explicit repository
.venv/bin/python environment recorded in research-next/base-assets.json. Do not
load model weights. Build a fixed system instruction asking for complete current
standing focus and exactly the JSON shape above, plus one user message carrying
current task handle and the authentic source-event prefix. Fix the literal system
prompt in the implementation before real packet tokenization. It must not contain
worked examples or conditions copied from spent model outputs.

Use apply_chat_template with enable_thinking=False and add_generation_prompt=True.
Record the exact nonthinking generation prefix. Canonical target JSON uses UTF-8,
unescaped Unicode, sorted keys and compact separators, followed by exactly one
EOS token. Inputs are prefix token IDs followed by target token IDs and EOS;
labels mask every prefix position with-100 and supervise every target/EOS position.
Padding has attention0 and label-100. Verify token-boundary behavior and decoded
bytes through the actual tokenizer/consumer; do not assume whole-text and separate
segment tokenization coincide. Choose and document one exact causal prefix/target
construction that both training and later local generation will share.

Reject silent truncation, reserved role/control-token injection in source/target
text, empty target supervision, future citations, ambiguous checkpoint identity,
misplaced loss positions or invalid schema. Do not mutate source text to pass.
The reserved-token restriction defines this natural-text calibration domain;
it is not a claim about arbitrary adversarial special-token strings.

One CPU preview after data acceptance records each of18actual prefixes, target
and full-sequence token counts, losses/masks/EOS counts, hashes of exact source,
target,template/tokenizer/code/environment, and distributions/maxima by length
band. No output or sequence cap is selected here; report actual lengths without
truncation. A later measured mechanics registration must cost those real lengths.
A long or malformed document remains an explicit preparation failure until its
source/label issue is reviewed; tasks are not made easier to fit a desired number.

Reuse the record_focus shape validator where safe, but do not invoke the native
reasoning client: its positive-reasoning contract does not define this local
final-only protocol. No new training framework or serving integration is needed.
The smallest implementation is one pure data/serialization module and targeted
consumer tests; root may call its preview function through a short CPU invocation.
No top-level experiment script import, old data/adapter load or new trainer yet.

Preparation passes only with reviewed complete labels, exact source boundaries,
correct actual-token loss construction and full18-row receipts. This qualifies
labels and format only; it cannot establish learned transfer, speed, code utility
or the broader goal. Next possible action is a separately reviewed FIT-only
longest-sequence training-mechanics measurement with a hard bound, not full SFT
or a test on withheld data. Original raw authoring and any guarded correction
remain preserved and tracked with explicit paths.
