# Classifier data — label specification (2026-09-03)

Purpose: a small GENERIC classifier that decides, for one sentence of a conversation with an AI assistant, whether
the assistant must remember it for later turns. It is the write-time selector of a retention mechanism (pin the
sentence's KV columns through eviction; re-inject its text before answering). Provenance: written directly by
kimi-k3 (data/classifier/kimi, kimi-ctx), reviewed and enriched by hand by sol and Opus (review/, *-enrich.jsonl),
with held-out sets (heldout/; fable-validation is author-disjoint, opus/sol held-out share authors with the
enrichment). Disjointness policy (item-level, agreed by kimi/sol/Opus/fable reviews of 2026-09-03): no benchmark
item, template, marker, or exact phrasing from any evaluation benchmark (IFEval, Multi-IF, BFCL, tau-bench, S2/B3)
enters the data; plain-language formatting rules are kept and constraint-TYPE overlap with IFEval is deliberate and
disclosed. The three-scope spec and enrichment were developed with feedback from the b3 probe. An earlier
scope-generation prompt included probe-specific exemplars; 38 echoing rows were dropped and the exemplars rewritten.
This remediation does not remove development influence. The final artifact is described as item-disjoint subject to
the recorded audits, not as development-independent (astra program review, 2026-09-04).
Review status: kimi/ and kimi-ctx/ reviewed by sol and Opus (review/*-patch.jsonl); kimi-scope/ reviewed via
review/scope-v2-*-patch.jsonl when present; *-enrich.jsonl are reviewer-authored.

Labels (exactly one per sentence):
- rule — an instruction, constraint, preference, persona, or commitment that governs the assistant's FUTURE
  replies, including sentences that change or cancel an earlier rule. THREE SCOPES (v2, 2026-09-03, after quick
  check 19): (1) conversation-scoped ("from now on", "always", "never", "whenever") → rule; (2) TASK/ARTIFACT-scoped —
  a constraint on the piece of work in progress (a document, a piece of code, a plan, a story: "keep the whole
  thing short", "no bullet points", "open with a one-line heading", "use tabs in this file", "sign off with my
  initials"; exemplars deliberately NOT drawn from the dev probe — see fable's check-22 review F3) → rule,
  because it persists while the same work continues in later turns ("now extend it", "revise the piece", "add a
  closing section") and is echoed back precisely then; (3) explicitly single-reply scoped ("just for this one
  answer", "this time only", "for this message") → none. v2.1 (Opus scope-pass review S7/S8): "for now",
  "temporarily", "until I say otherwise" → rule (conversation-scoped with an open expiry); "for this section", "in
  this paragraph", "for the next two chapters" → rule while that sub-unit is the work in progress (task-scoped), none
  only when the sub-unit is already finished in the same turn. When a sentence mixes a work request with a
  constraint on how it must be done ("Summarize this in under 100 words."), the constraint clause wins → rule. When scope is unstated, a constraint on how the work must
  be written is TASK-scoped (rule); a request to do a piece of work is a one-off task (none).
- fact — durable information likely needed in later turns that is not an instruction: identifiers, names, numbers,
  dates, decisions, states of the world, and corrections of earlier facts. Tool-output lines carrying identifiers
  the user later relies on are facts (role tool).
- none — everything else: one-off task requests (imperative is NOT automatically a rule), questions, chit-chat,
  assistant prose, most tool output, acknowledgements, meta-talk, quotes/hypotheticals/descriptions of someone
  else's rules, rules scoped to the current reply only.

Fields: text (the sentence), role (user|assistant|tool|system), label, domain, hard (bool), why (short),
source (author:domain:seed or author-enrich / author-heldout), context (optional; 1–3 preceding sentences with
speaker prefixes, present in the kimi-ctx pass and wherever the label depends on context).

Splits: the frozen model's manifest records its training sources and patches. Fable validation is author-disjoint;
Opus/sol validation shares authors with enrichment. These are development validation sets, not untouched mechanism
tests. Multi-IF/BFCL are post-development evaluation families. The exact frozen training-input recipe must be
reconciled before a new fit (astra program review, 2026-09-04: the committed recipe/current patches do not yet
reproduce the recorded source composition). A separately registered no-contact family follows.
Deployment limit (astra G2): the classifier scores a sentence and role without the current task or conversational
context, so a completed, switched, or reversed instruction keeps its score; the three-scope taxonomy is an admission
heuristic, not a scope-resolution mechanism.
