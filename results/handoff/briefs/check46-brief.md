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
(RUNNING.flag under results/quick-checks/check46/; stop/rm only your container); cap 60 GPU-minutes (astra cost note: 901 calls ~38 min aggregate decode at concurrency 4; profile 20 DEV calls first and stop INCOMPLETE if completion cannot fit; reuse a running qualified server if present); ~900 short
generations. Report latency per message. Data lineage line first. Outputs under results/quick-checks/check46/
(README with readings, few-shot file, prompt, records <= 10 MB, summary); item 46 in results/quick-checks/README.md
(5 lines); WORKLOG (<= 6 lines); dated section in results/relations-classifier-report.md. Commit with explicit
pathspecs (git add -f, no files > 10 MB); no push; never signal any process but your container; never read
anything under data/bench.

ADDED (fable's updater research, results/updater-research-fable.md): check 44's 2.75% was mostly DECODER
CORRUPTION (289/314 non-verbatim span rejections). Therefore: (1) match spans with a NORMALISED verbatim matcher
(whitespace/quote/case-normalised exact substring; report raw-verbatim and normalised rates separately) and, if the
vLLM image supports it, constrain the span field by guided decoding to substrings of the message (LogitMatch-style)
— journal which was used; (2) report results PER MISS FAMILY: cue-less rules, two/three-rule single sentences,
rule+payload, withdraw+replace, bare new value + temporal, task-scoped override of global, "actually, B"; (3) the
expected outcome is PARTIAL (relations likely >= 90%, admission likely short) — state the admission ceiling honestly.
