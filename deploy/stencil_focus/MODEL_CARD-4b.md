---
language: en
license: apache-2.0
base_model: Qwen/Qwen3-4B
pipeline_tag: text-generation
library_name: transformers
tags:
  - qwen3
  - long-context
  - instruction-following
  - conversation-memory
  - coding-assistant
---

# stencil-focus-qwen3-4b

**Qwen3-4B with inference-time session memory under a fixed prompt budget. Efficacy NOT
PROVEN: the final registered head-to-head through this package (N = 139) read +2.0 points,
95% interval [−0.1, +4.2], p = .058 (see Evidence).** The learned weights
are the unmodified `Qwen/Qwen3-4B` trunk (revision
`1cfa9a7208912126459214e8b04321603b3df60c`); nothing was fine-tuned. The modification is
how a long conversation is turned into a prompt when the history no longer fits: with
`stencil_focus=true` the prompt keeps the newest tokens of the conversation and,
immediately before the request, restates the user-turn sentences that were truncated away
(newest first, packed to 256 tokens including the header
`Earlier instructions still in force:`), and the window is shortened so that the complete
prompt has the same token count as the plain window. Zero parameters. With
`stencil_focus=false` the prompt is the plain newest-token window and generation is
ordinary greedy `transformers` generation. Everything else is identical.

Built by the [Stencil](https://github.com/bmarti44/stencil-llm) research project.

## Evidence (no efficacy claim)

### Final confirmation through this package (Exp 4C, NOT PROVEN, FINAL)

The final pre-registered test (`results/memorycode-long/REGISTRATION-4C.md`, results in
`RESULTS-4C.md`) generated every output THROUGH THIS PACKAGE: the same bytes with
`stencil_focus=true` versus `stencil_focus=false`, on N = 139 MemoryCode-derived long coding
sessions (history truncated to a 3,584-token window, 512-token greedy generation, 300 s
deadline; outcome = the share of required conventions satisfied under the vendored
MemoryCode regex checker; functional correctness not measured). Sample size came from a
timing-only rule; the package was qualified first (16/16 flag-off outputs identical to plain
`AutoModelForCausalLM`, 8/8 replays byte-identical).

| quantity | `stencil_focus=false` | `stencil_focus=true` |
|---|---|---|
| mean required-check compliance | 0.084 | 0.105 |
| strict (all required checks) | 0/139 | 1/139 |
| output failures (invalid / capped / degenerate / timeout) | 60/139 | 61/139 |

Paired difference +2.05 points of 100, registered paired-t 95% interval [−0.07, +4.16],
two-sided p = 0.058; 25 wins / 17 losses / 97 ties; companion bootstrap [+0.14, +4.30]
(not the decision statistic). Output-failure difference +0.7 points [−5.2, +6.6]. The
registered primary interval includes zero, so the result is **NOT PROVEN, FINAL**: a small
positive average effect that this sample cannot distinguish from zero, with absolute
compliance low in both arms. This artifact is therefore published in the research
repository only, with no efficacy claim. Interim results were inspected at 75 and 100 pairs
on the owner's instruction; the run was neither stopped nor extended on that basis.

### Earlier stage (Exp 4B, qualification FAILED; descriptive only)

The earlier pre-registered proof (`results/memorycode-long/REGISTRATION-4B.md` in the research repo)
compared this artifact with `stencil_focus=true` against the identical artifact with the
flag off on MemoryCode-derived long coding sessions (history truncated to a 3,584-token
window; outcome = compliance with the conventions the mentor stated earlier, scored by the
vendored MemoryCode regex checker; functional correctness not measured). Its 16-item
qualification stage **FAILED** the registered output-failure gate (one unparsable output
on the flag-on arm among 16 items, where the gate allowed none), so the 128-item
confirmatory stage was never run. Descriptive numbers from the 16 qualification items
(`results/memorycode-long/RESULTS-4B.md`):

| arm | mean per-constraint compliance | strict (all conventions) |
|---|---|---|
| `stencil_focus=false` | .066 | 0/16 |
| `stencil_focus=true` | .109 | 0/16 |
| label-derived oracle reminder (not shippable) | .263 | 0/16 |

Paired flag-on minus flag-off: +4.3 points of 100, 95% bootstrap interval [+0.1, +9.5],
4 wins / 1 loss / 11 ties, n = 16. This is a descriptive SETUP-cohort number, not a
confirmatory result, and it is not comparable to the MemoryCode paper's native protocol.
The same mechanism on Qwen3-1.7B read −5.2 points [−10.6, −0.4] on the same 16 items; that
1.7B build is not published as a claim either.

Package parity (`results/memorycode-long/parity-4b.json`, the 16 qualification items, both
flag states): the package renders byte-identical prompts to the research runtime on 32/32
prompts, and with `stencil_focus=false` its greedy outputs equal plain
`AutoModelForCausalLM` on 16/16 items (the off switch is exact). Its greedy outputs do NOT
match the research runtime's token-for-token on any of the 32 generations (identical text
after whitespace on 7/32): the research numbers above were produced by a hand-rolled
bitwise-deterministic runtime, and `transformers` bf16 kernels take different greedy paths
on 3.6k-token prompts. Until the evaluation is reproduced through this package's own
generation path, no research number on this card is attributable to this artifact.

Secondary evidence (Multi-IF, Qwen3-1.7B, a different construction and trunk,
`results/qwen/multiif-echo-only-128/RESULTS.md`): restating truncated-away prior user
sentences scored 66.7 aged-adherence points versus 62.5 for the untruncated prompt, n = 128.
That is not a coding-session result and not a result for this trunk.

## Usage

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

repo = "bmarti44/stencil-focus-qwen3-4b"
tok = AutoTokenizer.from_pretrained(repo)
model = AutoModelForCausalLM.from_pretrained(
    repo, trust_remote_code=True, device_map="cuda"
)

session = model.new_session(tok)  # stencil_focus from config (default true)
session.add_message("user", "From now on, every function needs a docstring.")
session.add_message("assistant", "Understood.")
# ... many more turns ...
prompt = session.build_prompt("Write a function that parses a CSV file.")
reply = session.generate("Write a function that parses a CSV file.", max_new_tokens=512)
session.reset()

off = model.new_session(tok, stencil_focus=False)  # the identical model, plain window
```

`add_message(role, text)` stores every message in order; only `user` messages feed the
restatement, other roles are stored only. `build_prompt` returns the exact string sent to
the model (Qwen3 chat template, non-thinking); `session.last` holds the token accounting
(prompt tokens, thread tokens kept, reminder tokens). Sessions are isolated objects. The
window (`focus_window`, default 3,584 tokens) and reminder budget (`focus_budget`, 256)
live in `config.json`.

## What is and is not included

- Included: the trunk weights, tokenizer, the three remote-code modules
  (`configuration_stencil_focus.py`, `modeling_stencil_focus.py`, `focus_session.py`).
- Not included: the classifier-maintained instruction register studied in the research
  repo; on long coding sessions it overflowed its 16-row capacity on 138 of 144 evaluation
  items, so it is not the artifact's mechanism.
- No KV-cache pins, no attention steering, no hand-rolled runtime, no verifier loop.

## Boundaries

One trunk (Qwen3-4B), greedy decoding, one imposed budget. The restatement is verbatim and
label-free: it can restate sentences that are no longer in force alongside the ones that
are; the budget keeps the newest truncated-away sentences, which on long sessions are often
conversational filler rather than rules. The registered experiment measured convention
compliance only; nothing about functional correctness or free-running agentic sessions is
measured or claimed.

## License and attribution

Package code Apache-2.0. Trunk weights: `Qwen/Qwen3-4B`, Apache-2.0, copied unchanged at
the revision above. Evaluation items derive from MemoryCode (Cohere Labs, Apache-2.0).
