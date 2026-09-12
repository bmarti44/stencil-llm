---
language: en
license: apache-2.0
base_model: Qwen/Qwen3-1.7B
pipeline_tag: text-generation
library_name: transformers
tags:
  - qwen3
  - long-context
  - instruction-following
  - conversation-memory
  - coding-assistant
---

# stencil-focus-qwen3-1.7b

**Qwen3-1.7B with inference-time session memory under a fixed prompt budget.** The
learned weights are the unmodified `Qwen/Qwen3-1.7B` trunk (revision
`70d244cc86ccca08cf5af4e1e306ecf908b1ad5e`); nothing was fine-tuned. The
modification is how a long conversation is turned into a prompt when the history
no longer fits: with `stencil_focus=true` the prompt keeps the newest tokens of the
conversation and, immediately before the request, restates the user-turn sentences
that were truncated away (newest first, packed to 256 tokens including the header
`Earlier instructions still in force:`), and the window is shortened so that the
complete prompt has the same token count as the plain window. Zero parameters.
With `stencil_focus=false` the prompt is the plain newest-token window and generation
is ordinary greedy `transformers` generation. Everything else is identical.

Built by the [Stencil](https://github.com/bmarti44/stencil-llm) research project.

## Evidence

<!-- EXP4-TABLE: filled from results/memorycode-long/RESULTS.md after the registered run -->
The registered head-to-head (`results/memorycode-long/REGISTRATION.md` in the research
repo) is not yet run; this card carries no performance claim until it is. Nothing on
this card is comparable to the MemoryCode paper's native protocol.

Secondary evidence (Multi-IF, a multi-turn instruction-following check of the same
restatement machinery over an evicted region, 128 sources, Qwen3-1.7B,
`results/qwen/multiif-echo-only-128/RESULTS.md`): the parameter-free restatement of
prior user sentences (`role_echo_only`) scored 66.7 aged-adherence points versus 62.5
for the untruncated prompt and 54.7 for a trained-classifier selection of the same
kind; the registered contrast `role_echo_only − clf_echo_only` was +11.98 points,
95% interval [+6.18, +17.71], n = 128. That is not a coding-session result.

## Usage

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

repo = "bmarti44/stencil-focus-qwen3-1.7b"
tok = AutoTokenizer.from_pretrained(repo)
model = AutoModelForCausalLM.from_pretrained(
    repo, trust_remote_code=True, device_map="cuda"
)

session = model.new_session(tok)  # stencil_focus from config (default true)
session.add_message("user", "From now on, every function needs a docstring.")
session.add_message("assistant", "Understood.")
# ... many more turns ...
prompt = session.build_prompt(
    "Write a function that parses a CSV file."
)  # exact prompt
reply = session.generate("Write a function that parses a CSV file.", max_new_tokens=512)
session.reset()

off = model.new_session(tok, stencil_focus=False)  # the identical model, plain window
```

`add_message(role, text)` stores every message in order; only `user` messages feed
the restatement, other roles are stored only. `build_prompt` returns the exact string
sent to the model (Qwen3 chat template, non-thinking); `session.last` holds the token
accounting (prompt tokens, thread tokens kept, reminder tokens). Sessions are isolated
objects. The window (`focus_window`, default 3,584 tokens) and reminder budget
(`focus_budget`, 256) live in `config.json`.

## What is and is not included

- Included: the trunk weights, tokenizer, the three remote-code modules
  (`configuration_stencil_focus.py`, `modeling_stencil_focus.py`, `focus_session.py`).
- Not included: the classifier-maintained instruction register studied in the research
  repo (`bmarti44/assistant-memory-sentence-classifier` plus a relations head). On long
  coding sessions the frozen register overflowed its 16-row capacity on 138 of 144
  evaluation items and applied no lifecycle relation, so it is not the artifact's
  mechanism; its error table is published with the research results.
- No KV-cache pins, no attention steering, no hand-rolled runtime.

## Boundaries

One trunk (Qwen3-1.7B), greedy decoding, one imposed budget. Convention compliance is
the evaluated outcome in the registered experiment; functional correctness is neither
measured nor claimed. The restatement is verbatim and label-free: it can restate
sentences that are no longer in force (a superseded instruction) alongside the ones
that are; the budget keeps the newest truncated-away sentences.

## License and attribution

Package code Apache-2.0. Trunk weights: `Qwen/Qwen3-1.7B`, Apache-2.0, copied
unchanged at the revision above.
