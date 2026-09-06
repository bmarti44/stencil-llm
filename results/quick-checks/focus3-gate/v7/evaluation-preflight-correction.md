# Unscored Fable preflight correction — 2026-09-06

The first preflight aborted at exact-sentence overlap before loading either
classifier or producing any logits. One collision: "Thanks, that fixed it."
Kimi training source kimi-k3-scope:software-engineering-pair-programming:9000
has no context; Fable's context is "assistant: Change `==` to `===` on line 42."
These are independently authored acknowledgements with different full model
inputs. No label, row, split, model or threshold is changed or selected.

Retain the first started receipt/log. Resume this unscored evaluation with a
second preflight receipt. Require full paired-input-plus-role disjointness and
source-author disjointness, and report sentence-only collisions. Preserve both
prior recipe and model-freeze receipts; update only the evaluator source hash.
There will still be exactly one inference pass per model on the same Fable set;
both saved logits and the original preflight evidence will be committed.
