# stencil-wave

Qwen3-1.7B on HuggingFace `transformers`, with an **instruction ledger**:
the instructions in earlier user turns are detected, held, and the two the
model most needs right now are amplified through an additive attention bias
while it generates. No text is added to the context. Turn it off and you
get bitwise-plain `transformers`.

```python
from stencil_wave import WaveModel
wm = WaveModel.from_pretrained("Qwen/Qwen3-1.7B")   # trunk at the pinned revision + controller + salience
out = wm.generate(messages, max_new_tokens=512)      # ledger ON: detect, hold, select, amplify
print(wm.ledger)                                     # what was held, what was selected, with scores
out = wm.generate(messages, ledger=False)            # plain HF greedy generation, bitwise identical
```

`messages` is a normal chat list (`[{"role": "user", "content": ...}, ...]`)
or a single string. Generation is greedy (`do_sample=False`), batch size 1,
non-thinking template (`enable_thinking=False`).

## Install

```
pip install transformers==4.51.0 accelerate torch safetensors numpy
pip install .            # from this directory (or: pip install git+<repo>#subdirectory=deploy/stencil_wave)
```

`transformers==4.51.0` is a hard pin: the template, token ids and the plain
path were verified bitwise against the research trunk on that version; the
bias injection hooks that version's attention dispatch. The first
`from_pretrained` downloads `Qwen/Qwen3-1.7B` (~3.4 GB) at revision
`70d244cc86ccca08cf5af4e1e306ecf908b1ad5e`. A CUDA GPU is expected (bf16);
CPU works but is slow.

## What `wm.ledger` shows

```
ledger: 2 entries, 2 held, 2 selected (turn 2, hold=aged, top_k=2, dose=3.0, layers=20-27, active=True, biased_tokens=26)
  * [0] turn 1 cols 10:19 score=+0.651  'Do not use any commas in your response.'
  * [1] turn 1 cols 19:30 score=+0.654  "Include the keyword 'harvest' at least twice."
```

`+` = held (eligible), `*` = selected (biased). `cols a:b` are the key
columns the bias targets — today the entry's token span in the context.
`wm.ledger.to_dict()` gives the same as JSON; `wm.last` holds the
`Generation` (text, new ids, prompt ids, rendered context).

Knobs (constructor or per call): `dose` (3.0), `top_k` (2), `hold`
(`"aged"` = only instructions from EARLIER turns are held — the evaluated
configuration; `"all"` also holds the current turn's), `classify` (your own
`sentence -> bool` instead of the built-in salience classifier).

## How it works (and what is exact)

1. **Salience** (`salience.py`): the research logistic classifier over
   linguistic cues, vendored verbatim with its weights; scores are bitwise
   the research module's. Under-inclusive by design (recall ~0.75); scans
   user turns only.
2. **Ledger** (`ledger.py`): each instruction sentence -> its token span in
   the rendered context -> a group of attention **key columns**. Everything
   below the ledger is expressed in columns, never prompt spans, so a future
   ledger that pins entries as KV-cache slots only has to hand out different
   column indices.
3. **Layer-20 capture** (`model.py`): a forward pre-hook on
   `model.model.layers[20]` reads the residual stream entering layer 20 in
   the same forward that generates. Entry keys = mean over the entry's
   columns; the controller (`controller.py`, 264,321 params, the research
   checkpoint converted bitwise to safetensors) scores held entries against
   the prompt's final position and selects the top-k once, at prefill.
4. **Bias injection** (`attention.py`): inside `generate(ledger=True)` the
   `"sdpa"` entry of `transformers`' attention registry is scoped to a
   wrapper. With no bias for a (layer, step) it calls the stock
   `sdpa_attention_forward` with identical arguments, so the plain path is
   untouched (the model config stays `"sdpa"`, HF's mask construction is
   unchanged). With a bias it computes fp32 scores, -inf causal mask,
   **+ bias added exactly in fp32 before softmax**, fp32 softmax and value
   matmul, cast back — the research trunk's arithmetic. A 4D float
   `attention_mask` was rejected because HF casts it to bf16 and routes it
   through the SDPA kernel; a registered custom interface name was rejected
   because HF then builds explicit masks for every layer and the no-bias
   path would no longer be the plain call.

Exactness, as measured (`tests/test_parity.py`, numbers in `parity.json`):

- **Ledger with no held entries == ledger OFF: bitwise** (ids and
  full-vocabulary logits `torch.equal`), and ledger OFF is the identical
  `model.generate` call.
- **Template and token ids**: bitwise equal to the research context on all
  7 fixtures (4 single-turn B0 prompts + 3 multi-turn conversations).
- **Ledger entries, held set, and selection**: identical on 3/3 multi-turn
  fixtures (same spans, same rank order; layer-20 state cosine >= 0.9997).
- **HF trunk vs research trunk** are different bf16 kernel paths (B0
  measured 0.39-0.77 max-abs last-logit drift between them; the package
  reproduces those B0 numbers exactly). Ledger OFF, prompt-final logits:
  max-abs diff 0.68 / 0.39 / 0.77 / 0.50 / 0.40 / 0.66 / 0.57 — all within
  the registered 1.0 bound. Along a 32-token trajectory the drift compounds:
  0.68 / 0.91 / 0.77 / 0.51 / 0.79 / 0.66 / **1.13** (6/7 within 1.0).
  Ledger ON with fixed columns and dose 3.0: prefill 0.56 / 0.57 / 0.51;
  trajectory 0.73 / 0.57 / **1.03** (2/3 within 1.0).
- **Greedy tokens**: identical wherever the research top-1/top-2 margin
  exceeds twice the drift (guaranteed); the first 32 tokens are fully equal
  on 4/7 fixtures ledger OFF and 2/3 ledger ON. Every divergence happens at
  a step whose margin is 0.025-0.099 — below the drift, where neither path
  is "right". This is the same drift class the research repo registered
  for its own cached-vs-full path; the strict 32-token criterion is kept in
  the test suite as visible `xfail`s rather than a widened tolerance.

## What it does NOT do

- Insertion-only actuator: attention toward an instruction helps when the
  fix is to *include* something; it has no mechanism for limits, removals,
  or restructuring beyond whatever extra attention happens to do.
- Qwen3-1.7B at the pinned revision only. The controller reads that model's
  layer-20 residual stream.
- The registered evaluation of this ledger (non-inferiority to text
  re-append on Multi-IF at zero context cost) is not complete; this package
  makes no benchmark claim.
- System prompts and assistant turns are not scanned for instructions.

## Tests

```
pip install pytest
python -m pytest tests                       # CPU: salience port, ledger, template, controller, bias rows
STENCIL_REPO=/path/to/stencil-llm python -m pytest tests   # + GPU parity against the research path
```

`scripts/push_to_hub.py --repo <org>/stencil-wave-qwen3-1.7b` stages the
add-on weights and the model card (`MODEL_CARD.md`); dry run unless
`--push`.
