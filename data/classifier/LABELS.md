# Classifier data — label specification (2026-09-03)

Purpose: a small GENERIC classifier that decides, for one sentence of a conversation with an AI assistant, whether
the assistant must remember it for later turns. It is the write-time selector of a retention mechanism (pin the
sentence's KV columns through eviction; re-inject its text before answering). Provenance: written directly by
kimi-k3 (data/classifier/kimi, kimi-ctx), reviewed and enriched by hand by sol and Opus (review/, *-enrich.jsonl),
with author-disjoint held-out sets (heldout/). NEVER from any evaluation benchmark (IFEval, Multi-IF, BFCL,
tau-bench, S2/B3), not even by paraphrase of their instruction taxonomy.

Labels (exactly one per sentence):
- rule — a standing instruction, constraint, preference, persona, or commitment that governs the assistant's
  FUTURE replies, including sentences that change or cancel an earlier rule. Scope words matter: "from now on",
  "always", "never", "whenever", "for the rest of this project" → rule; "just for this reply" → none.
- fact — durable information likely needed in later turns that is not an instruction: identifiers, names, numbers,
  dates, decisions, states of the world, and corrections of earlier facts. Tool-output lines carrying identifiers
  the user later relies on are facts (role tool).
- none — everything else: one-off task requests (imperative is NOT automatically a rule), questions, chit-chat,
  assistant prose, most tool output, acknowledgements, meta-talk, quotes/hypotheticals/descriptions of someone
  else's rules, rules scoped to the current reply only.

Fields: text (the sentence), role (user|assistant|tool|system), label, domain, hard (bool), why (short),
source (author:domain:seed or author-enrich / author-heldout), context (optional; 1–3 preceding sentences with
speaker prefixes, present in the kimi-ctx pass and wherever the label depends on context).

Splits: train = kimi + kimi-ctx + *-enrich (after review patches applied); validation = author-disjoint heldout/*
(never trained on); evaluation of the mechanism = the dev probe (data/b3, selection set) then Multi-IF and BFCL as
post-development benchmarks, then a separately registered no-contact family.
