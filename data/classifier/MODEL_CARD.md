---
language: en
license: mit
base_model: BAAI/bge-small-en-v1.5
pipeline_tag: text-classification
library_name: transformers
tags:
  - conversation-memory
  - instruction-following
  - sentence-classification
  - bge
metrics:
  - accuracy
model-index:
  - name: assistant-memory-sentence-classifier
    results:
      - task:
          type: text-classification
          name: Does the assistant need to remember this sentence? (rule / fact / none)
        dataset:
          name: Stencil held-out sentences (author-disjoint fable-validation + fable-scope-validation, opus-heldout, sol-heldout)
          type: stencil-held-out
        metrics:
          - type: accuracy
            value: 0.8911
            name: held-out accuracy (n = 1,093)
          - type: accuracy
            value: 0.8423
            name: hard-subset accuracy
---

# Assistant Memory Sentence Classifier

**Does the assistant need to remember this sentence for later turns?**
Three labels: `rule` (an instruction, constraint, preference, persona or
commitment that governs the assistant's future replies, including sentences that
change or cancel an earlier rule), `fact` (information the assistant must carry
forward), `none` (everything else, including one-off requests). A
`BAAI/bge-small-en-v1.5` fine-tune (33M parameters, CPU-friendly) produced by the
[Stencil](https://github.com/bmarti44/stencil-llm) research project, where it is
the write-time selector of a reminder/retention mechanism for long conversations.

## Usage

The model reads a sentence **pair**: the preceding context (or the literal string
`(no context)`) and the sentence itself prefixed with its speaker role in square
brackets. It ships a small `modeling_stencil.py`, so pass `trust_remote_code=True`.

```python
from transformers import pipeline

clf = pipeline(
    "text-classification",
    model="bmarti44/assistant-memory-sentence-classifier",
    trust_remote_code=True,
)
clf({"text": "(no context)", "text_pair": "[user] From now on reply in French."})
# [{'label': 'rule', 'score': ...}]
clf({"text": "assistant: Here is the helper in JavaScript.",
     "text_pair": "[user] Convert this function to TypeScript for me."})
# [{'label': 'none', 'score': ...}]
```

For batches, pass a list of such dicts. The classifier was trained and evaluated
with inputs truncated to 192 tokens (`truncation="longest_first"`); keep that
setting for numbers comparable to the ones below. Speaker roles known to the
model are `user`, `assistant`, `tool` and `system` (in that index order); the
pipeline uses `user` by default, and the forward method accepts `role_ids` to
select another.

## Evaluation

Held-out accuracy, on sentences never used for training or selection:

| Held-out source | n | accuracy |
|---|---|---|
| fable-validation (author-disjoint) | 363 | 86.8% |
| fable-scope-validation (author-disjoint, task-scoped rules) | 292 | 84.6% |
| opus-heldout | 238 | 93.7% |
| sol-heldout | 200 | 94.5% |
| **all** | **1,093** | **89.1%** |

Per class (all held-out): `none` precision 0.924 / recall 0.865; `rule` 0.911 /
0.872; `fact` 0.823 / 0.962. Hard-subset accuracy 84.2%. The export was verified
to reproduce the registered scorer's predicted label on all 1,093 held-out
sentences.

**In its intended application it did not beat a heuristic.** On the public
Multi-IF benchmark (909 conversations, frozen Qwen3-1.7B, earlier instructions
evicted from the KV cache before the final query and partly restored by pinning
selected columns and echoing their text), this classifier's selections recovered
aged-instruction compliance to 59.2% (pins + echo; 57.2% pins only) versus 16.7%
evicted and 65.2% with full context. A parameter-free rule that simply keeps the
most recent prior user sentences scored 60.5% at the same number of pinned
columns. Use this model when you need a per-sentence decision (for example to
build a compact reminder or a memory store); do not expect it to outperform
recency on benchmarks where recency already works.

## Training data and lineage

- 20,054 training sentences, written directly by kimi-k3 in fresh sessions,
  reviewed and enriched by hand by two other reviewing models (sol, Opus), with
  a three-scope label specification (conversation-scoped, task/artifact-scoped,
  and one-off) documented in the project's `data/classifier/LABELS.md`.
- Held-out sets: `fable-validation` and `fable-scope-validation` are
  author-disjoint; `opus-heldout` and `sol-heldout` share authors with the
  enrichment step.
- Disjointness policy: no benchmark item, template, marker or exact phrasing from
  any evaluation benchmark (IFEval, Multi-IF, BFCL, tau-bench) entered the data.
  Plain-language formatting rules are kept and constraint-TYPE overlap with
  IFEval is deliberate and disclosed.
- Two recorded incidents: an earlier scope-generation prompt included
  probe-specific exemplars; 38 echoing rows were dropped and the exemplars
  rewritten. This remediation does not remove development influence, so the data
  is described as item-disjoint subject to the recorded audits, not as
  development-independent.
- Training: 3 epochs, seed 0, raw `[CLS]` state plus a one-hot speaker role into
  a linear head. The Hub checkpoint folds the role part of the head into a
  per-role logit bias; numerics are unchanged.

## Intended use and limits

- Intended: deciding, per sentence of a chat transcript, whether an assistant
  should retain it (rule or fact) for later turns; building reminders; filtering
  candidates for a memory store. English only.
- Not intended: safety filtering, content moderation, or any decision about a
  person. The model reads only the sentence and a short context window; it does
  not know whether a rule was later cancelled (that is a separate lifecycle
  step in the Stencil project).
- Known weaknesses: task-scoped constraints stated as observations ("the report
  reads better without headings") are the hard subset; `fact` recall is high but
  its precision is the lowest of the three classes.

## License and attribution

Weights: MIT (same as the base model `BAAI/bge-small-en-v1.5`, revision
`5c38ec7c405ec4b44b94cc5a9bb96e735b38267a`). Training sentences were
model-written and reviewed as described above. Copyright 2026 Brian Martin.
