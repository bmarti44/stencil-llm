# Composition pilot 3 — one-round diagnosis (fable, independent reviewer)

2026-09-06. CPU only; read: results/quick-checks/composition-pilot-3/{README,prewritten,report.log,audit.json,run.json,registration.json,records.jsonl,continuation/records.jsonl,hf-transcripts/slab-dev-00/R.json,run.py,continuation/continue.py,report.py}, results/quick-checks/vllm-qual/replay.py, results/quick-checks/composition-pilot{,-2}/README.md + records.jsonl, src/stencil/focus/{slab,loop,renderer}.py at 33e8273d, models/qwen3-30b-a3b-hf/tokenizer_config.json (chat template only). No data/bench, no evaluation episodes, no GPU. All counts below were recomputed from the 460 journaled records (92 in records.jsonl + 368 in continuation/records.jsonl; 460 distinct episode/arm/round keys).

## Verdict in one paragraph

Pilot 3 is not a backend regression and not a chat-template/EOS regression: the vLLM path renders byte-identical token ids to the HF path apart from the amended prompt text (Section 5). It is worse than pilot 1's CPU recovery because of four interacting CPU-side defects, three of which are instrument/prompt-spec bugs rather than model failures: (a) the format checker demands `report.task == "A"|"B"` (the task-handle letter) while the prompt only says "verbose includes task", so every verbose response fails format by construction — this defect exists in pilot 1's checker too; (b) the compact literal example and `"report"` object made the model emit a single-line envelope that ends with the merged token `"}}` followed by one extra `}` in 99/460 outputs (95 of them otherwise fully valid `{calls, report}` envelopes) — pilot 1 had the same one-token tail glitch as a trailing `]` in 16/128; (c) the prompt's "Preserve earlier operations, repairing with whole-file replace as needed" plus append-semantics `edit` induces cumulative re-emission of every prior function from round 1 onward in 13/24 lanes (12 of them at round 1), which drives 193/460 caps (174 capped outputs contain 4 or more `def step_` definitions) — pilot 1 never got past round 0 execution so this never surfaced; (d) `delivery` is undefined in the prompt, so the model emits it as a nested object of file contents (`{"core.py":"","policy.py":"<entire code again>"}`, 19 executed + 15 capped outputs) or as a string in unscoped rounds, feeding both caps and process violations. Fixing (a)-(d) on CPU is a small, mechanical amendment; pilot 4 is reachable this week under the existing envelope. Hermes tool calling is the right pilot-5 fallback, not a prerequisite (Section 4).

## 1. What changed between pilot 1 and pilot 3 outputs

Pilot 1 (old prompt, HF, DEV-00 R round 0, 197 body tokens) — pretty-printed, `status` beside `calls`, no `report`, `test` with a path:

```
{
  "calls": [
    {
      "op": "edit",
      "path": "policy.py",
      "code": "def step_0(x):\n    \"\"\"Map each integer v to v * 6 + 3, preserving order.\n ... return [v * 6 + 3 for v in x]"
    },
    {
      "op": "test",
      "path": "policy.py"
    }
  ],
  "status": "ok"
}
```

Pilot 3 (amended prompt, vLLM, same episode/arm/round, 262 body tokens) — compact, `report` present, `task` = the entire user request echoed verbatim, `delivery` = a dict re-emitting the whole file:

```
{"calls":[{"op":"edit","path":"policy.py","code":"def step_0(x):\n    \"\"\"Map each integer v ... return [v * 6 + 3 for v in x]"},{"op":"test","path":""}],"report":{"status":"ok","task":"add language -> Python. add indent -> 3. indent 3 = block bodies indented by exactly 3 spaces. add format -> verbose. add test_record -> test-after-edit. add delivery -> staged.\nExtend workshop B: add step_0(x) in policy.py; map each integer v to v * 6 + 3, preserving order. Document the function and its boundary behavior; obtain a test receipt. Only task A reports delivery. Public example: [[18,20,-18,3],[111,123,-105,21]]","delivery":{"core.py":"","policy.py":"def step_0(x):\n    \"\"\"Map each integer v to v * 6 + 3 ... return [v * 6 + 3 for v in x]"}}}
```

Pilot 3 DEV-02 R round 0 — the trailing-brace shape (the dominant new parse failure; note `"delivery":"staged"}}` + `}`):

```
... {"op":"test","path":""}],"report":{"status":"ok","task":"add language -> Python. ... Public example: [{\"event\":\"idle\",\"level\":0},-3]","delivery":"staged"}}}
```

Pilot 3 DEV-00 R round 1 (512 tokens, capped) — cumulative re-emission after a clean round-0 receipt: calls = `edit policy.py` with `def step_0` AND `def step_1` in one code string, then `test`, then `delivery` starting to re-dump `step_0` again when the cap hits. Round 2 re-emits `step_0, step_1, step_2`. In DEV-00 N the same happens after the round-0 `{"error":"envelope"}` feedback.

Shape accounting (460 pilot-3 outputs; 128 pilot-1 outputs):

| Property | Pilot 1 (HF, old prompt) | Pilot 3 (vLLM, amended prompt) |
|---|---:|---:|
| Starts with `{"calls"` compact | 48/128 | 460/460 |
| Has `"report"` key | 0/128 | 460/460 (every non-capped output; 30/193 capped reach it) |
| `status` beside `calls` (lift_report tolerance needed) | 38/128 | 0/460 |
| `test` carries a path (test_path tolerance) | 32/128 | 159/167 executed (`"path":""`) |
| Capped at 512 | 11/128 (8.6%) | 193/460 (42%) |
| Non-capped but not JSON | 22/128 | 100/460 |
| ...of which a single extra trailing token | 16 (`]`) | 99 (`}`); 95 rescuable as exact `{calls,report}` |
| ...Python literals (`True/False`) | 6 | 1 (`Expecting ',' delimiter`, DEV-00 N r0 garbled two `code` values) |
| Nested `delivery` object | 0 | 34 (19 executed + 15 capped) |
| >=2 distinct `def step_` in one output | n/a (round 0 only executed) | R 60/160, N 105/160, T 57/140 |

So the amendment did change the shape: it fixed the pilot-1 failure modes it targeted (status placement, Python literals) and introduced three new ones (task echo, delivery dict, trailing `}`), while the untested multi-round regime exposed cumulative re-emission. The "JSON prefixed to code / code inside JSON strings" hypothesis is not what happened: code always sits inside `calls[].code`; the extra code appears in `report.delivery` and in cumulative `edit` bodies.

## 2. Why `format` is violated 16/16 on every episode and arm: instrument defect

`check()` (slab.py ~966-972) builds `expected_report = {"status":"ok"}`, then `expected_report["task"] = t.task` when format is verbose, and compares `{k:v for k,v in report.items() if k!="delivery"}` for exact equality. `Turn.task` (slab.py 145-150, constructed at ~511 `Turn(i, task, request, ...)`) is the task handle, the single letter `"A"` or `"B"`. `reference()` emits `"task":"B"`. The prompt says only "verbose includes task" and "report is an object with keys status (always "ok"), task (verbose format only)". Nothing tells the model that `task` is a letter; 123/167 executed responses echo the request text, 0/460 emit the letter. Result: every verbose-round response fails `format` regardless of arm, and every compact-round response that includes `task` (the model keeps it after having emitted it once) also fails. The same `t.task` comparison exists at d1fb0660 (pilot 1's freeze), so pilot 1's recovered `format` numbers carry the same defect; it was masked there by the early exit on a missing `report`.

Because the violation is identical in R, N and T (16/16, 32/32 everywhere), it cannot carry any arm signal. This is a checker/prompt inconsistency, not a model result, and also collapses the `format` relapse measure (relapse requires `report.get("task") == t.task`, i.e. the letter — never true).

Two secondary instrument issues in the same block: (i) `except (ValueError, KeyError, TypeError, AttributeError)` sets `format=True` for every parse failure, so `format` violations are inflated by the trailing-brace and cap failures too; (ii) `process` is violated in 128/167 executed responses, 56 of them because `delivery` was emitted when not scoped (or as a dict), 53 because no receipt — the model reports `delivery` on every round because the prompt gives no value shape, and "Only task A reports delivery" is read as "task A's report includes delivery" by a model that has already echoed the request.

## 3. Why caps rose to 193/460 (R 59, N 82, T 52)

Recomputed from capped outputs: 174/193 contain 4-5 distinct `def step_` definitions in a single response; 38 begin the code with a `# core.py` / `# policy.py` file header; 15 re-dump code inside `delivery`; only 30 reach the `report` key at all. Cumulative re-emission onset: 12/13 affected lanes begin at round 1; in 8 lanes the preceding round produced an error/cap feedback, in 5 lanes the preceding round was clean (e.g. DEV-00 R: round 0 executed with a receipt, round 1 still re-emitted `step_0`+`step_1`). So error feedback amplifies it but the primary driver is the prompt: "Preserve earlier operations, repairing with whole-file replace as needed" read together with an `edit` that appends. The model treats each turn as "emit the current file", uses `edit` (append) for it, and the workspace doubles in size each round (executed `edit` bodies with `[[4,4],[4,4]]`-style duplicate widths confirm duplicate definitions were written). Three further token sinks: the verbatim `task` echo (mean 65 tokens per response, 10,933 tokens over the 167 executed responses), `Args/Returns/Raises` docstrings plus `isinstance` validation (~120 tokens per function, present in pilot 1 too), and `delivery` dicts.

Executed-clean outputs sit at 208-507 tokens (median 237), i.e. a single function already consumes ~45% of the cap; any second function or a delivery dump caps. Truncation therefore cannot pass 2% at cap 512 while re-emission occurs, independent of backend.

## 4. Is the per-round custom JSON envelope too fragile? Reconsidering Hermes tool calling

What the three pilots actually show:

- Pilot 1: 33/128 unparsable (status beside calls, Python literals, trailing `]`, 11 caps), fixed by two tolerances to 95/128 executed.
- Pilot 2: no envelope data (parity gate stop).
- Pilot 3: 100 non-capped failures, 99 of them a single trailing `}` (95 otherwise exact); 193 caps from re-emission; 0/460 format because of the letter-vs-text defect.

The envelope itself is responsible for exactly one recurring failure class: a one-token tail slip that kills the whole response (12.5% in pilot 1, 21.5% in pilot 3). Everything else is prompt-spec ambiguity (`task`, `delivery`, re-emission) that would survive a format change unchanged. So the honest reading is: the envelope is fragile at one point (single-blob all-or-nothing parse), and that point is cheaply hardened; it is not the reason final success is 0/8.

Native Qwen3 Hermes tool calling (chat template `tools` branch: `# Tools ... <tools>{json schema}</tools> ... <tool_call>{"name":..,"arguments":..}</tool_call>`, tool results as `<tool_response>` in a user turn) would isolate each call in its own delimited object, use a schema the model was trained on, and separate the report from the calls. It is the right design for pilot 5 if pilot 4 still misses the 90% executed gate. I do not recommend switching for pilot 4, for three reasons: (1) it does not address the three defects that dominate (task letter, delivery, re-emission), so it would be confounded with them; (2) it changes the renderer, journal, T-arm rule text, check45 transcript layout and the frozen HF/vLLM parity artifacts, i.e. a registration, not a fix; (3) pilot 1 already demonstrated 95/128 parse-and-execute under this envelope with a tolerant parser — on pilot 3 data a trailing-brace tolerance alone lifts R executed from 53/160 to 101/160, and removing re-emission is what recovers the rest.

Minimal Hermes amendment, if pilot 5 is needed (register before code):

- renderer.py: when `request.tools` is set, build the system message with the template's tools block (exact text from tokenizer_config.json `chat_template`, `tools` branch) instead of `Tool schema: {...}`; assistant history closure unchanged (`<|im_end|>\n`); tool results rendered as `<|im_start|>user\n<tool_response>\n{json}\n</tool_response><|im_end|>\n` (the template's own form) preceding the next request text; rule register text stays in the user turn.
- slab.py: `parse_envelope` -> `parse_tool_calls`: regex `<tool_call>\s*(\{.*?\})\s*</tool_call>` per block, `json.loads` each; calls = `[{"op": name, **arguments}]`; `report` = a final `report` tool (`{"name":"report","arguments":{"status":"ok","task":"B","delivery":"staged"}}`) or, if absent, text outside tool_call blocks is journaled and `report` is missing (breakage). Tools: edit, read, replace, test, report with JSON-schema arguments.
- journal.py/loop.py: record `attempted_tool_calls` from the parser as today; add `content_text` (non-call text) to the record; nothing else changes.
- The T arm cumulative re-emission obligation is unaffected (it is about which functions appear, not the wrapper).

## 5. vLLM adapter audit — nothing that explains the lower executed rate

- Rendered prompt: pilot-3 DEV-00 R round-0 `rendered_token_ids` (879 ids) vs pilot-1 HF record (798 ids): common prefix 124 ids, common suffix 110 ids; the differing middle decodes exactly to the amended sentences ("edit appends Python on a new line", the report-key sentence and literal example, and the indent gloss in the rule text and request). Template is `<|im_start|>system ... <|im_start|>user ... <|im_start|>assistant\n<think>\n\n</think>\n\n`, identical in both. Byte-identical up to the amendment, as required.
- Request: `/v1/completions` with `prompt` = token-id list, `max_tokens 512`, `stop_token_ids [151645,151643]`, `temperature 0`, `seed 0`, `return_token_ids`, streaming (vllm-qual/replay.py PARAMS). No chat template applied server-side; usage `prompt_tokens` asserted equal to the id count on every call; no retokenization.
- Terminal handling: run.py Decoder strips the final id only when `finish_reason == "stop"`; all 267 completed outputs ended in 151645, none in 151643; `tokenizer.decode(body) == output` verified on a sample; `decode==output True`. History closure in loop.py appends `151645 + "\n"` (= `<|im_end|>\n`), matching the template.
- Whitespace: no strip/normalization anywhere between ids and the parser (the `"}}` + `}` tail is in the token ids: last ids `['delivery','":"','st','aged','"}}','}']`).
- Determinism D=0 across cold/warm/C4 (audit.json). The per-stream 10.5 tok/s at C4 (28 tok/s aggregate) is a throughput property, not a correctness one; pilot 2 HF grouped_mm gave 16.8 tok/s single-stream.

The adapter is clean. The lower executed rate is entirely explained by the CPU-side items in Sections 1-3.

## Repository hygiene flag

`results/quick-checks/composition-pilot-3/continuation/http/records.jsonl` is committed at 33e8273d as a 75,017,475-byte blob (plus 25.4 MB `http/records.jsonl`, 17.7 MB `checkpoints/first-N/http/records.jsonl`, 17.7 MB `continuation/records.jsonl`; 11,515 tracked files under results/quick-checks). Recommend: keep streamed-chunk HTTP journals out of git (they duplicate `output_token_ids` already in records.jsonl), commit a `manifest.json` with path, byte size and sha256 for each, and keep the compact per-call records. A `.gitattributes`/pre-commit size guard (>10 MB refuses) would stop the recurrence. Rewriting history is not worth it now; stop adding.

## Minimal CPU fixes for pilot 4 (register as an amendment before code; DEV only)

1. Checker/prompt `task` consistency (slab.py `check`, `reference`, `SYSTEM_PROMPT`): state in the prompt that `task` is the workshop letter named in the request (`"task":"B"`), and give the literal verbose example `{"calls":[{"op":"test"}],"report":{"status":"ok","task":"B"}}`. Keep the checker comparing to `t.task`. Alternatively accept `task` if it contains the letter; the prompt fix is cleaner and keeps exact equality.
2. Define `delivery` in the prompt: `delivery` is the obligation value string (e.g. `"staged"`), included only when the request's workshop letter equals the delivery-scoped task, and never an object. Add the checker guard that a dict `delivery` is a format violation, not a crash path.
3. Third journaled tolerance: accept exactly one trailing `}` or `]` after a complete top-level object (`json.JSONDecoder.raw_decode`, reject if the remainder is anything else); journal it like `lift_report`. This is the pilot-1 `]` class and the pilot-3 `}` class; 95/99 pilot-3 cases would execute.
4. Stop re-emission: replace "Preserve earlier operations, repairing with whole-file replace as needed" with "edit appends only the new function; never re-emit functions that already exist in the file; use replace only when a test reports a failure in an existing function". Render the tool result for `edit` with the post-edit function-name list (`{"op":"edit","path":..,"functions":["step_0","step_1"]}`) so the model sees the file state; this is a renderer-side field, no scorer change.
5. Feedback loop: keep the envelope error message, but make it show the exact rejected tail (`unexpected trailing "}"`) rather than the generic expected skeleton, which the model currently answers by re-emitting everything.
6. Keep cap 512, stop ids, prompt-as-ids adapter, and the `test_path` tolerance unchanged. Expected effect from the pilot-3 data alone: R executed 53 -> ~101/160 from item 3, and most of the 59 caps (all re-emission-driven) from item 4; the residual ~4-space indent bias (executed widths `[4,4]` in 66/167, `[3,3]` in 14) is a real model competence result and stays a registered gate, not a fix.

Pilot 4 CPU work is a few hours (prompt sentences, three checker lines, one tolerance, one tool-result field, DEV regression tests through `Executor.run` and `check` with the pilot-3 outputs as fixtures). The GPU cost stays the measured 28 tok/s aggregate; with re-emission removed, mean output should return to the pilot-1 200-token band and the 32-round lanes stop growing 500+ tokens per round, so the 12 GPU-h projection becomes plausible again. The larger test remains reachable this week only if pilot 4 launches within one day and passes the 90%/2% gates on first try; a Hermes pilot 5 would push it past the week.
