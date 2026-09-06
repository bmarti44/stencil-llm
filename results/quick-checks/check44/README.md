# Check 44 — message-level standing-rule admission

Pre-written reading, 2026-09-06. Quick diagnostic authorized by Brian; the source
is [Astra's admission memo](../../admission-research-astra.md). No held-out input
or model outcome has been read when this reading is written. The full 800-message,
two-author protocol is a separate deeper verification, only after a promising
quick check; no such bank is authored here.

**GO bar, frozen before execution:** A (or an eligible C) must attain micro
one-to-one span-overlap recall >=85%, false admission on gold-empty one-off
payload items <=3%, false admission on gold-empty quoted/reported items <=3%,
and zero admissions on non-user roles. Missing family support cannot pass.
A semantic quick GO permits deeper verification, not integration or a production
safety claim. Otherwise **NO-GO: cut unattended admission from the first ship;
use explicit structured rule entry.** No prompt rescue, reroll, alternative bank,
threshold retuning or post-outcome label correction. Incomplete execution is
INCOMPLETE, never a semantic NO-GO or GO.

Data lineage: A/B fit-on=none; prompt/development/timing-on=24 individually
hand-written Astra messages in dev.json, with the first six fixed demonstrations.
These include payloads, quoted and adopted text, task/global rules, two-rule
messages, non-user roles, single-reply constraints and a longer log. Evaluated-on
=data/classifier/heldout/fable-admission-heldout.jsonl, 338 messages by reserved
author Fable. No fable message is opened until script/prompt/schema/recipe freeze
and the cost-only DEV projection pass. No data/bench or sealed input is read.
Author/scenario independence relies on the supplied bank provenance; an exact
DEV/evaluation message overlap assertion does not establish semantic disjointness.

Arms:

- A: local frozen Qwen3-1.7B, repository Qwen3 loader and converted checkpoint,
  bf16, hf_compatible=True on trunk/blocks/norms, thinking off, greedy constrained
  JSON, no quantization/fit. One message per call; previous_user only when supplied.
  The schema returns up to four {text,key,scope,evidence,attribution} rules, or
  an empty list. Keys are NEW because each message starts with an empty register.
  Scope is global or task:<verbatim visible artifact binding>. Raw JSON, token
  counts, prompt hash, proposed and accepted spans and rejections are recorded.
  LM Format Enforcer 0.11.3 supplies schema token filtering. A local adapter uses
  its documented TokenEnforcer API because its Transformers convenience import
  refers to a class moved in Transformers 5.16.1; no dependency monkeypatch.
- B: unchanged ft-v3 seed0 sentence head, called once per message as a batch of
  its sentence spans. Same preceding-three-sentence context builder, 192-token
  overflow abstention, P(rule)>=.95, role guard. All sentence proposals are saved;
  aggregate accepted spans into message-level predictions. No new training.
  B_register separately runs the actual v8 Runtime.update consumer over those
  cached identical head outputs, empty register, no invented current task. Its
  four-sentence and task-binding guards remain intact. Relations have no targets
  in this independent-message check. B is the requested detector baseline;
  B_register makes the limitations of the existing specialized consumer visible.
- C: eligibility checked once at arm construction/freeze; if fewer than 1,500
  Kimi rows then SKIPPED, with observed count and time in recipe-freeze.json.
  Script refuses to freeze a skipped C if >=1,500 rows have arrived; that case
  requires its own registered small fit and disjoint DEV before any evaluation.

Validation admits only user-role candidates with valid schema, NEW key, direct
or adopted attribution, exact unique text/evidence substrings and enclosing
evidence. It rejects fabricated/paraphrased text, duplicate locations (including
overlapping repeats), duplicate candidates, unsupported scope, input/output
overflow and uncertainty (via extractor abstention). Adopted evidence must include
alphanumeric content outside the quote; actual endorsement remains a semantic
model decision, not something substring checking proves. Task bindings must be
verbatim in visible message/previous_user. There is no fallback head after A
rejects. This isolated admission experiment does not modify shipping register
code, relation policy, or model packaging.

Metrics are recorded for every message, with exact character-offset and any
positive-character-overlap maximum-cardinality one-to-one matching. Report micro
span precision/recall, macro precision over predicted messages, macro recall over
positive messages, binary message detection, and the stricter character IoU>=.5
secondary metric. One long prediction cannot match two gold rules. Exact gold
boundaries are honored (including punctuation); invalid gold offsets abort as
INVALID rather than being silently repaired. Empty outputs remain in denominators.

Family definitions use the bank's existing annotations, not a keyword payload
detector: payload = gold-empty AND one_off_request; quoted = gold-empty AND
quoted_or_reported. These may overlap. Mixed positive messages contribute span
FPs/precision; they are not negative-family denominators. Report tool and assistant
roles separately and jointly. Report each family's observed rate and one-sided
95% Clopper-Pearson upper bound; the 3% quick bar concerns the observed rate,
not its upper bound. Bounds assume independent messages. Explicit scenario IDs,
if supplied, also get any-error-per-scenario bounds; otherwise scenario bounds
are unmeasured. Domain breakdowns do not create independent authors/scenarios.

Scope agreement is both global-versus-task class and literal normalized gold
scope on overlap-matched spans; semantic artifact-name aliases are not invented
after scoring. The B head has unknown scope where v8's specialized scope parser
has no binding. NEW is deliberately not a semantic key slug: report within-message
key-equivalence partition agreement on pairs of matched spans, with its support,
and mark literal semantic-key naming unmeasured. No existing-key relations or
cross-message identity test is supplied by an empty-register message bank.

Timing/resource policy: max4,096 input and256 output tokens, no truncation;
overflows abstain. One fixed prompt, zero semantic revisions. Run24 DEV/timing
messages, including the six demos (DEV accuracy is not held-out evidence), before
the single held-out pass. Count loading/grammar preparation/DEV/evaluation in
the <=5,400s GPU allocation. Launch held-out only if elapsed +1.25*338*slowest
DEV message <=5,370s. Stop cooperatively at token/message boundaries, preserving
partial raw records, never signal. Report synchronized batch1 GPU A p50/p95 and
CPU B p50/p95; these are different deployment devices. While the GPU is occupied,
also run the same24 DEV messages once on CPU, fp32/four threads, same frozen
prompt/grammar, with a1,800s cooperative CPU wall cap. Record first-call/load
separately and warm23 p50/p95 by <=1,024 versus longer total input lengths.
CPU outputs are timing only, never prompt selection. These CPU seconds consume
no GPU allocation; report them separately. The memo's complete single-repository
ship build remains UNMEASURED; component timing is not integrated ship timing.
GPU latency cannot certify the <=5s CPU ship bar. No comparative statistical
superiority claim is made: the memo's deeper paired test is not this quick GO bar.

Coordination: wait for every other Stencil RUNNING.flag and compute process to
finish naturally; Brian's llama-server is allowed and never touched. Foreground
only; acquire/check44/RUNNING.flag exclusively, remove only our flag at completion.
No background launches, signals, model fitting (unless C separately registered),
full pytest suite, push, or unrelated working-tree changes.

Reproduce using .venv/bin/python -m scripts.focus_check44 --mode selftest,
prepare, freeze, cpu_timing (CUDA_VISIBLE_DEVICES=''), run, audit in that order.
The one-shot run-start receipt blocks
re-execution. Audit replays saved records without model inference or reopening
the source held-out bank. Final outcomes belong in RESULTS.md/summary.json so
this pre-written README remains byte-identical to its recipe hash.
