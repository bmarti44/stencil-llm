# Composition DEV pilot review (fable, one round, 2026-09-06)

Scope: `results/quick-checks/composition-pilot/` (README, records.jsonl 128 rows, episodes.jsonl,
summary.json, renderer-golden.jsonl, prewritten.md, run.log, run/audit/batch-invariance JSON,
recipe.json) at commit `9691d2c2` on freeze `d1fb0660`; code `src/stencil/focus/{slab,loop,renderer,
retained_decode}.py`, `models/stencil-package/`, `scripts/composition_pilot.py` (load config only),
installed `transformers 5.2.0` / `torch 2.11.0+cu128` MoE and SDPA integrations. CPU only; tokenizer
file only (`models/qwen3-30b-a3b-hf/tokenizer.json`) to decode `rendered_token_ids`; the DEV-00
episode was regenerated with `slab.generate_episode("dev", 0)` and emitted code was executed in the
pilot's own `slab_sandbox` executor. Nothing under `data/bench` read. Only this file written.

## 0. Numbers recomputed from records.jsonl (all reproduce)

Row order is R,N,T,O per round (`oracle_checker_results[0].arm`), rows 0-63 sequential, 64-127
batch; `started_at` is non-monotone only inside batch rounds (four lanes share one decode). Rows are
unique (`request_id` x arm x mode), `failures`/`fallback_reasons` empty on all 128.

| arm (sequential) | own-body min/med/max | in 100-300 | first-10 in band | max prompt | truncated | mean s/call | executed calls |
|---|---:|---:|---:|---:|---:|---:|---:|
| R | 197/197/198 | 16/16 | 10/10 | 11,050 | 0/16 | 19.576 | 0 |
| N | 202/202/204 | 16/16 | 10/10 | 5,394 | 0/16 | 19.030 | 0 |
| T | 192/512/512 | 2/16 | 2/10 | 9,727 | 10/16 | 42.009 | 0 |
| O | 197/197/198 | 16/16 | 10/10 | 11,050 | 0/16 | 19.382 | 0 |

Batch max prompts R/N/T/O 11,050/7,144/10,224/11,050; batch T 1 deadline-interrupted at 343 tokens
(`deadline_hit=true`). Decode 16,668 tokens / 1,539.544 s = **10.827 tok/s** sequential; batch
18,887 / 3,422.151 = 5.519. Projection `spent + L + 1.25*[64(cR+cN)+16(cT+cO)]` with spent
5,385.346, L 322.758, c = 313.669/304.932/672.606/310.559 -> **20.794 h**; full-four 37.180 h;
batch lower bound with 863.951 s/lane -> 49.583 h. Truncation 10/64 = 15.625 % of sequential
calls. Round-0 prompt ids are identical between sequential and batch in all four arms; batch R and O
outputs are token-identical to sequential on 16/16 rounds, N diverges from round 0 (first differing
token index 49) and T from round 0 (index 0). Every README number I checked is right.

Two things the README's wording does not carry: (a) `executed_tool_calls` is empty on all 128 rows
but `attempted_tool_calls` is populated on 101 rows (the parser got as far as reading the call list),
and (b) all 101 parseable replies contain a correct program (section 1.3). The INELIGIBLE reading is
correct on the registered items; the sentence "this interface did not establish executable
competence" is true of the interface and false of the model, and the distinction matters for what to
fix.

## 1. What the model actually emitted (Q1)

### 1.1 Three representative literal outputs

R, round 0 (row 0; valid JSON, 197 tokens, rejected `envelope`):

```
{
  "calls": [
    {"op": "edit", "path": "policy.py", "code": "def step_0(x):\n    \"\"\"Map each integer v to v * 6 + 3, preserving order.\n\n    Args:\n        x: A list of integers.\n\n    Returns:\n        ...\n    Raises:\n        TypeError: If any element in x is not an integer.\n    \"\"\"\n    if not all(isinstance(v, int) for v in x):\n        raise TypeError(\"All elements in the input list must be integers.\")\n    return [v * 6 + 3 for v in x]"},
    {"op": "test", "path": "policy.py"}
  ],
  "status": "ok"
}
```

N, round 0 (row 1; valid JSON, 202 tokens, rejected `envelope`):

```
{"calls":[{"op":"edit","path":"policy.py","code":"def step_0(x): ..."},{"op":"test","path":"policy.py"}],
 "status":"ok","verbose":[{"task":"add step_0(x) in policy.py","delivery":"staged"}]}
```

T, round 0 (row 2; NOT JSON - Python literal `True`; 192 tokens; error fed back
`Expecting value: line 1 column 602 (char 601)`):

```
{"calls": [{"op": "edit", "path": "policy.py", "code": "def step_0(x): ..."}, {"op": "test", "path": "policy.py"}],
 "status": "ok", "verbose": True, "delivery": "staged"}
```

Shape census over all 128 (`json.loads`, then `ast.literal_eval` fallback):

| class | count | where |
|---|---:|---|
| valid JSON, top-level `{calls,status}` | 64 | R seq 16, O seq 16, R batch 16, O batch 16 |
| valid JSON, `{calls,status,verbose:[...]}` | 16 | N seq |
| valid JSON, `{calls,status,delivery:{...}}` | 15 | T batch (pretty-printed, hallucinated `delivery` object) |
| Python literal only (`"verbose": True`) | 6 | T seq rounds 0-5 |
| valid prefix + one stray trailing `]` | 16 | N batch (`Extra data: line 1 column ...`) |
| truncated at cap / deadline | 11 | T seq 10, T batch 1 |

Every one of the 101 parseable replies has exactly two calls, `edit` with `{op,path,code}` and
`test` with `{op,path}`; no `read`, no `replace`, no third call, no Markdown fence. Nothing in the
model's output space wanders: the failure is two fixed deltas from the registered envelope, (i) the
report fields sit at the top level instead of inside `report`, and (ii) `test` carries a `path`.

### 1.2 Diagnosis: prompt under-specification first, parser rigidity second, capability not at all

The frozen `SYSTEM_PROMPT` (slab.py:95-108) is the only place the envelope is described, and it never
names `report` as an object or lists its keys. The literal text is "Reply with calls/report JSON;
report status is ok, verbose includes task, compact omits task. Include delivery only for the task
named in the request." A reader who has never seen the schema reads "report status is ok" as *emit a
status of ok*, and "verbose includes task" as a field called `verbose` - which is exactly what N and T
did (`"verbose":[{"task":...}]`, `"verbose": True`). The tool schema string gives per-op field lists
(`"test":["op"]`) but no envelope example; `read`/`edit`/`replace` all take `path`, so a per-file
`test` is the natural generalization and the model made it 101/101 times. Under the T arm the
obligation line literally reads `format=verbose`, and T alone turned that into a boolean key
`"verbose": True` (Python spelling), which is why T's replies are invalid JSON while R/N/O's are valid.

The parser (`Executor.run`, slab.py:710-723) is zero-tolerance on both counts: `set(payload) !=
{"calls","report"}` and `set(call) != set(TOOL_SCHEMA["calls"][op])`. The first failing check raises
before any call executes, and the string fed back to the model is `{"error":"envelope"}` (R/N/O) or
the raw `json` module message (T, because `JSONDecodeError` is a `ValueError`). Neither tells the
model what the envelope should look like, so no arm could self-correct; R/N/O emitted the same shape
16/16 rounds.

Capability is not in question. For all 101 parseable replies I extracted the `edit` code and ran it
through `slab.evaluate_many` against the DEV-00 public case and the three hidden cases per turn:
**101/101 correct function name, correct file, correct results on public and hidden cases**, edit
followed by test in every reply, never a cumulative re-definition except in T (section 2). The model
also ignored the live `indent=3` rule in 101/101 replies (4-space bodies) and N reported `delivery`
for the unscoped task; those are the retention measurements the pilot was built to take, and they are
recoverable from these records the moment an envelope tolerance is applied on CPU.

### 1.3 How many of the 128 would have executed

| parser | executable | notes |
|---|---:|---|
| registered strict parser | 0/128 | as reported |
| strict JSON + tolerant envelope (lift top-level `status`/`task`/`delivery` into `report`, ignore `verbose`, ignore `path` on `test`) | 95/128 | loses all sequential T (Python `True`) |
| + Python-literal fallback (`True/False/None`) | 101/128 | all sequential T rounds 0-5 recovered |
| + trailing-bracket repair (json-repair style) | 117/128 | recovers the 16 batch N rows |
| any parser | never the 11 truncated rows | 10 seq T at the 512 cap, 1 batch T at deadline |

Qwen3's native chat-template tool calling (`tools=` rendered by the template; the model emits
`<tool_call>{"name":..,"arguments":..}</tool_call>` blocks) is not measurable from this run because
these replies were not generated under that template, and I did not launch the model. What the
records do show is that all 101 call lists map one-to-one onto Hermes calls (`name=op`,
`arguments={path,code}`), and that the only invalid-JSON defect (`True`) sits in the envelope, not
inside a call, so it would not have blocked call extraction. The cost of the native route is that
`report` needs its own channel (a `report` tool or the trailing assistant text) and the template
rewrites the system prompt, i.e. a renderer amendment; the benefit does not exceed what an explicit
envelope example in the existing prompt buys. I do not recommend switching interfaces for the
re-pilot.

## 2. Why T truncates (Q2): reply inflation, not request inflation

T's per-round prefill is the smallest of the four arms (159-189 new tokens/round vs R's 404-588;
T's obligations line is ~40 tokens), so the request is not the problem. The reply is: T's
`edit.code` re-emits every function of the current file cumulatively - 192 / 333 / 474 tokens on
rounds 0/1/2 (step_0; step_0+step_1; step_0..2), resets to 192 at the task switch on round 3
(core.py), climbs again 333 / 474, and from round 6 every reply hits 512 mid-code (`Unterminated
string`). Mechanism, read from the decoded T prompts: T's round-0 reply is invalid JSON, the parser
error `Expecting value: line 1 column 602` comes back as a tool result, the system prompt says
"Preserve earlier operations, repairing with whole-file replace as needed", and the model concludes
the prior edit never landed and re-sends the whole file (still as `edit`, still with `True`). R/N/O
got the opaque `envelope` string, did not read it as "your code was lost", and stayed at 197-204
tokens. So the truncation is a downstream symptom of the same interface defect plus uninformative
error feedback; with a valid envelope on round 0, T has no reason to inflate. Note the cap-side rule
"empty/capped outputs are breakage" then charged every capped T reply as breakage, which is why T
looks worse than the other arms in the outcome table for a reason unrelated to retention.

## 3. Throughput (Q3)

Per-call decode time is flat in context: 86.9 ms/step at 1.0k retained tokens, 99.5 ms/step at 11.2k
(slope ~1.2 ms per 1k tokens); prefill 371 tok/s. A flat ~90 ms step for 3.3 B active parameters is
not bandwidth-bound (bf16 active weights ~6-7 GB/token against the GB10's ~270 GB/s unified memory
puts the bandwidth ceiling near 40 tok/s); it is launch-bound. The pilot loads with
`attn_implementation="sdpa", experts_implementation="eager"` (composition_pilot.py:481-482), and
eager MoE runs each of 48 layers as a Python loop over the routed experts (8 x 3 linears + gathers per
layer, plus attention), on the order of 1.5-2k small kernel launches per decoded token. 10.8 tok/s is
the expected number for that path on this machine; it is not a regression in the decoder adapter.

Cheapest legitimate options, in order of intrusion:

1. **Same HF path, `experts_implementation="grouped_mm"`** (or `"batched_mm"`). transformers 5.2.0
   registers both for `Qwen3MoeExperts` (`integrations/moe.py:301-320`, `modeling_qwen3_moe.py:217`)
   and torch 2.11 has `torch._grouped_mm`. One flag; same weights, same bf16 arithmetic class,
   different accumulation order, so greedy argmax may flip on near-ties. Gate: replay the 16 frozen
   DEV-00 R prompts from `renderer-golden.jsonl` (and the other 48 sequential prompts in records)
   and byte-compare outputs - about 5 GPU-minutes. Expected gain 2-3x; enough to bring the nested
   recipe under 12 h if it holds (section 5).
2. **vLLM serving bf16 with prefix caching, controller outside.** The shipped R arm is a rendered
   prompt plus plain greedy decoding; nothing in R/N/T/O touches HF internals, masks or biases, and
   retained KV is only an exact-in-principle shortcut for re-prefilling the rendered history, which is
   precisely what prefix caching is. Serving all four arms through the same engine is therefore a fair
   test of the same mechanism, provided (i) the controller keeps the renderer authoritative (send the
   rendered token ids or the exact rendered text as a raw completion, never the chat endpoint),
   (ii) tokenization is checked once by re-encoding the golden prompts, (iii) greedy, `max_tokens`
   512, `<think>\n\n</think>` prefix as rendered, and (iv) the same 64-prompt byte-compare gate as
   option 1 is run and its agreement rate reported (bf16 fused-MoE kernels differ; expect most rounds
   identical, some near-tie flips - report them, do not hide them). What is lost is the residual
   capture at layers 8/16/24/32/40; recover it with one teacher-forced HF prefill over each final
   transcript (one 11k-token forward per arm-episode, seconds each), which yields the same
   activations the pilot captured up to bf16 numerics and is cheaper than the pilot's per-step hooks.
   Batching becomes free rather than harmful, which the current adapter cannot offer (section 4).
3. **llama.cpp with a bf16 GGUF** is a fair test only at bf16 (quantized variants change the
   mechanism); slot save/restore gives prefix caching. Community DGX-Spark numbers for this model are
   several-fold above 10.8 tok/s, but I have no local measurement and will not cite one.

I would not spend time on `torch.compile`/static-cache with the retained decoder: the injected
decoder's growing mask and data-dependent expert routing fight both.

## 4. Batch non-invariance (Q4): expected, and the batch path is also the wrong tool

The evidence points at padded-lane numerics, not a bookkeeping bug:

- The two unpadded lanes (R and O carry the longest prompts, so their rows have zero left padding)
  are token-identical to sequential on 16/16 rounds through 11k retained tokens; only the padded
  lanes (N, T) diverge. A position or mask off-by-one would corrupt every lane, and a padded lane
  with wrong positions would not produce a fluent, correct alternative program - batch N's round-0
  reply is a different but correct `step_0`.
- T's divergence at token 0 is a near-tie: sequential T chose `{"calls": [` and batch T chose a
  pretty-printed `{\n  "calls"` - the same formatting coin the model flipped between R (pretty) and
  N/T (compact) sequentially on identical instructions. N diverges at token 49 inside a docstring.
- Eager MoE groups tokens from all lanes per expert, so GEMM shapes and bf16 accumulation order
  change with lane count; SDPA with an explicit padding mask takes a different kernel than the
  mask-free `is_causal` path used at batch 1 (`masking_utils.py:628` returns `None` only without
  padding). Both change rounding; greedy argmax flips on near-ties.

The same mask path explains why batch is slower: batch-4 decode is 195 ms/step at 1.3k physical
tokens and 715 ms/step at 15.8k (slope ~36 ms per 1k physical tokens, 30x the sequential slope),
because the materialized-mask attention scans the padded cache every step, and finished lanes keep
being forwarded until the longest lane (T, 491-512 tokens) ends. Per-step cost is 2.2x sequential at
short context and 7x at long; aggregate 5.5 tok/s. `retained_decode.py` is correct as written; it is
simply not a batching engine. Drop batch4 from the recipe; if batching is wanted, it comes with
option 2 above. `batch-invariance.json`'s "batch only if all four match" policy did its job.

## 5. Verdicts

**INELIGIBLE reading: correct.** Fixed fallback incomplete (1/4 episodes), projection 20.794 h > 12,
truncation 15.6 % > 2 %, batch not byte-invariant - all reproduce from records. No prompt, parser or
scorer was rescued after seeing outputs; the golden freeze and hidden manifests are consistent with
recipe.json. The README should add one sentence: the model's programs were correct on every
parseable round (101/101 public and hidden cases on CPU), so the envelope failure is an interface
defect and not a capability finding.

**Root cause:** the frozen system prompt never shows or names the `report` object, and the parser
rejects the two most natural readings of it, with feedback that cannot be acted on. T's truncation is
the same defect amplified by the `Preserve earlier operations` instruction and a leaked JSON error.

**Minimal CPU fixes before a re-pilot (one registered amendment; all in `slab.py`):**

1. `SYSTEM_PROMPT`: add one literal envelope example and the three sentences it lacks -
   `report` is an object; keys `status` (always `"ok"`), `task` (verbose format only), `delivery`
   (named task only); `test` takes no `path`. Keep the schema string.
2. `Executor.run`: register two tolerances and journal when they fire - ignore an extra `path` on
   `test`; if `report` is absent, lift top-level `status`/`task`/`delivery` into it and drop other
   top-level keys. Keep JSON-strict (no Python-literal or bracket repair; those are the model's job
   once the prompt is fixed). Also make the envelope error informative and stable:
   `{"error":"envelope","expected":"{\"calls\":[...],\"report\":{\"status\":\"ok\"}}"}` instead of
   the bare string or a `json` module message.
3. Re-score DEV-00 from `records.jsonl` on CPU under the amended parser before any GPU: it turns
   95 sequential-plus-batch rows into measured retention outcomes (style 0/16 compliance, N's
   delivery misreport) for free and tells you whether the R-vs-N comparison even has signal.
4. Recipe: remove batch4; add `experts_implementation="grouped_mm"` with the 64-prompt byte-compare
   gate as the first GPU step (~5 min). Budget arithmetic: the nested recipe needs
   64(cR+cN)+16(cT+cO) = 55,321 s raw; under the registered formula with the sunk 1.5 h carried,
   the ceiling is (43,200 - 5,385 - 323)/1.25 = 29,994 s raw, a required speed-up of 1.84x
   (1.61x if the re-pilot is a fresh recipe without the sunk spend). T's cost also drops once it
   stops re-emitting files. If grouped_mm does not clear 1.84x on the gate run, go to vLLM (option 2)
   and register the equivalence-gate agreement rate as part of the recipe.
5. Do not change the renderer layout, the T obligation text, the 512 cap or the 100-300 band; none
   of them caused this.
