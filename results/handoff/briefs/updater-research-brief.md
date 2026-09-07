# Deep web research for gpt-6-astra: the best options for an AUTOMATIC register updater — including a LoRA adapter on the trunk itself (2026-09-06)

Brian's question: "can we use a classifier to finish off the automatic bit — input the chat context, current rules
and current instruction, output the new instructions? Could we use a LoRA adapter on the model itself to do this?"
Context (read: results/focus-mechanism-composition-v2-astra.md sections 1-2; results/quick-checks/check44b/RESULTS.md,
check44c/RESULTS.md and their fable reviews; results/relations-classifier-report.md latest sections; results/
reuse-research-{astra,fable}.md P1/P2; the queued check 46 brief at the end of this prompt). State of play: the
register + every-request renderer is built and reviewed; rule ENTRY is explicit; two small discriminative
classifiers exist (relations bge-small ~96% on ordinary phrasing, 73% supersedes recall on override idioms;
admission span taggers NO-GO at 64-73% recall); a frozen 1.7B extractor recalled 2.75%; check 46 (queued) will try
the frozen 30B trunk zero/few-shot as a structured updater (register JSON + message -> ops list). Audited hand-written
data available for fitting: ~5.4k relation pairs + 1.5k transitions + 1.2k override idioms + 2.9k + 1.6k admission
messages (all kimi-written, Opus/astra audited; author-disjoint fable held-outs exist for both tasks; NO benchmark
data may ever be used for fitting or selection).
Research, with real citations (arXiv/ACL/ICLR/NeurIPS, GitHub, HF Hub, vLLM/PEFT docs), the best options to try,
ranked by (expected accuracy on our banks) x (cheapness to test on one GB10 with ~8-12k examples) x (fits the
ship form: one HF repo, frozen trunk, custom generate):
A. LoRA / adapter on the TRUNK (Qwen3-30B-A3B MoE) as a register updater: feasibility of LoRA on an MoE trunk
   (which modules: attention only vs expert MLPs; PEFT support for Qwen3MoE; memory/time to fine-tune on GB10 with
   ~10k short examples; QLoRA needed?); serving a LoRA in vLLM (multi-LoRA, `--enable-lora`, MoE LoRA support
   status as of today) so the SAME server does both the updater call and generation; "activated LoRA" / aLoRA
   (IBM) that switches the adapter on only for the updater tokens without recomputing the KV cache — is it
   supported anywhere we can use; risks: does an adapter for extraction change the trunk's generation when off
   (it must not; it is a separate weight file). Include known results of small-data structured-extraction LoRAs
   on 30B-class models.
B. LoRA on a SMALL model (Qwen3-1.7B/4B/8B dense) as a dedicated updater, served alongside: expected accuracy vs
   the trunk; cost per message; evidence from instruction/constraint extraction and dialogue-state-tracking
   fine-tunes (e.g., DST with LLMs, schema-guided generation, span extraction with generative decoders).
C. Discriminative alternatives we have NOT tried that address our specific failure (multi-rule sentences, cue-less
   rules, "withdraw + replace" idioms): token-classification with a larger encoder (deberta-v3-large / ModernBERT
   / bge-large), pairwise+span joint models, GLiNER-style fine-tuning on OUR data, contrastive span models;
   with evidence on small-data span extraction recall.
D. Prompted frozen trunk with constrained decoding (what check 46 does): state-of-the-art few-shot structured
   extraction results for 30B-class models; prompt patterns that help (schema-first, evidence spans, chain of
   verification); expected accuracy ceiling without fitting.
E. Anything else: e.g., "instruction hierarchy"/"system prompt update" research, memory-write policies with
   learned gates, RLHF-style preference data for rule extraction, synthetic data generation at scale from our
   label specs (is more data the real lever? our banks say cue-less and multi-rule coverage is the gap).
For EACH option: what it is, evidence with links, install/fit/serve effort in hours on our machine, GPU cost,
expected accuracy vs our bars (admission overlap recall >= 85% at precision >= 95%; relations >= 94% with supersedes
recall >= 85%), ship-form fit, risks (eval contamination — NEVER fit on any benchmark; contamination of the trunk's
generation; latency). End with: a RANKED TOP-3 to try in order, each as a quick check with a pre-written GO bar
and a <= 1 GPU-h budget, and a plain-language paragraph for Brian on whether a LoRA on the trunk is the right
bet. Write results/updater-research-astra.md. CPU only; web search; no installs; no model launches; never read
anything under data/bench.

=== queued check 46 brief (for reference) ===
# Check 46 for gpt-6-astra (GPU via the qualified vLLM server): the frozen TRUNK as the register UPDATER (2026-09-06)

Brian's proposal: "use a classifier of sorts to finish off the automatic bit: input the chat context, current rules
and current instruction; output the new instructions." We tried a frozen 1.7B JSON extractor (check 44 arm A:
2.75% recall). Not tried: the 30B trunk itself (Qwen3-30B-A3B, served deterministically by vLLM) as a structured
register updater. Test it in ONE look on the existing author-disjoint banks; no fitting anywhere.
Task definition: input = current register (JSON table: id, key, scope, kind, value, text, version, status) + the
new message with its role + up to 2 preceding user sentences when the bank row has prev_user; output = JSON list of
operations {op: add|supersedes|cancels|completes|reinstates|none, span: verbatim text, key, scope, kind, value,
target_id?} — constrained by a strict schema (use vLLM guided/structured decoding if available in the qualified
image; else strict post-parse with a journaled failure category). Greedy; thinking off; a short system prompt that
defines standing rule vs one-off/quoted/tool/assistant text using data/classifier/LABELS.md and
LABELS-RELATIONS.md wording (cite; do not lift any held-out example); 4-6 few-shot examples YOU author (never from
any held-out or gate bank; write them fresh; commit them before evaluation).
Evaluation banks (never fit on; opened once for this check — both were looked at once before by other models,
disclosed): (a) ADMISSION: data/classifier/heldout/fable-admission-heldout-3.jsonl (357 messages, 385 spans):
score add-ops as spans with check 44b/44c's metrics (overlap/exact micro+macro P/R; false admissions on payload /
quoted / non-user families with Clopper-Pearson); (b) RELATIONS: data/classifier/heldout/fable-relations-heldout-3
.jsonl (448 rows: old rule + status + message + target span + label): present the old rule as the register and
score the predicted op for the gold target span (accuracy, per-label P/R/F1, supersedes recall), plus target
identification when the register has the one rule. Also (c) the v8 gate SETUP bank (96 turns; development
diagnostic only): false-admission turns and admit events recovered (36 needed).
DEV for prompt iteration: only data/classifier/relations/kimi-admission-2.jsonl and kimi-overrides.jsonl rows (fit
corpora; never held-outs); at most 3 prompt iterations on <= 200 DEV rows; freeze the prompt in a commit before the
held-out look.
PRE-WRITTEN READINGS: GO = admission overlap recall >= 85% with precision >= 95%, payload/quoted FA <= 3% each,
non-user FA = 0, AND relations accuracy >= 94% with supersedes recall >= 85%, AND setup FA turns <= 2/96 with
36/36 admits -> register the trunk-updater as the automatic proposal path (typed register validates; explicit
entry overrides); cost per user message reported. PARTIAL = admission GO but relations not (or vice versa) ->
use the passing half automatically, the other stays explicit. NO-GO otherwise -> next hypothesis is a fine-tuned
small generative updater on the audited corpus (state the data lineage for it).
GPU: use the running/qualified vLLM server if pilot 4 left one, else start your own with the qualified image/flags
(RUNNING.flag under results/quick-checks/check46/; stop/rm only your container); cap 45 GPU-minutes; ~900 short
generations. Report latency per message. Data lineage line first. Outputs under results/quick-checks/check46/
(README with readings, few-shot file, prompt, records <= 10 MB, summary); item 46 in results/quick-checks/README.md
(5 lines); WORKLOG (<= 6 lines); dated section in results/relations-classifier-report.md. Commit with explicit
pathspecs (git add -f, no files > 10 MB); no push; never signal any process but your container; never read
anything under data/bench.
