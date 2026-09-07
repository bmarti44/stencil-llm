# Check 47 accuracy review — Opus (maximum reasoning), independent reviewer under Brian's 2026-09-06 ruling (`ae5a2dd0`)

CPU only. No GPU touched, no process signalled, nothing under `data/bench` read, no repo file edited except this
one. Every number below was recomputed from records; where I ran code I re-ran it against the frozen source tree
(`git archive 184cb321 src scripts`) as well as the live worktree, because six `src/stencil/focus/*.py` files have
drifted from the registered hashes since the freeze.

**Verdict: STAY is the correct trunk decision, but the recorded reason is wrong.** The registered switch rule is
conjunctive and the *cost* clause fails on every projected row; that is what actually decides it. The clause the
report says decides it — "The failed execution criterion independently decides STAY"
(`results/quick-checks/check47/README.md:37`, `summary.json` `reason`) — is an INSTRUMENT artifact of exactly the
kind that killed pilots 1–4. The harness comparison should be recorded **INELIGIBLE**, with the JavaScript result
standing separately and un-tested for significance.

---

## 1. Provenance and freeze — CLEAN

Verified, not taken on trust:

- The reading was frozen before inference. `registration.json` (with the `reading` field carrying the full
  conjunctive switch rule) is byte-identical to `git show 184cb321:results/quick-checks/check47/registration.json`;
  so are `run.py` and `serve.py`. Freeze commit `184cb321` = epoch 1788744942 = **21:35:42**. First inference call
  (`http/records.jsonl` min `started`) = 1788745142.13 = **21:39:02**. Gap 200 s. The container was launched at
  21:33:19, 143 s *before* the freeze commit, but the server was not ready until 21:39:01 (startup 342.298 s), so no
  token was generated before the rule was committed. Good.
- 25 of the 28 registered `source_hashes` match commit `184cb321` byte-for-byte; the other three
  (`composition-pilot-4/run.py`, `composition-pilot-4/report.py`, `vllm-qual/replay.py`) are `results/` files and
  match the live worktree at the registered digests. No drift in anything the run consumed.
- MoE comparison numbers are from committed records, not re-run. I recomputed them independently from the four
  files named in `moe-baseline.json` (all tracked; `git ls-files` confirms): 32 unique (episode, round) R rows for
  `slab-dev-00/01`, **executed 32/32, caps 0, violations language 0 / style 30 / format 10 / process 17 /
  breakage 0 / semantic 0, final success False on both**. Exact match to `moe-baseline.json` and to README:13.
  Round-0 indent compliance 0/2 confirmed from the raw MoE outputs (both emitted 4-space bodies against an
  `indent 3` rule).
- Arithmetic in the timing/projection block reproduces to the last digit (Section 4).
- **LOW-1 — precision/backend label is dropped from the one-line summaries.** README:7 labels the DEV table
  "Dense FP8 | MoE bf16, committed pilot4" and README:5 says the JS look is "descriptive across
  trunks/precisions/backends"; that is adequate. But `WORKLOG.md` and `plan/LEDGER.md` both record
  "JS disclosed second look 22/32 vs 16/32" with no precision, backend or significance qualifier. Those lines are
  what gets read in six weeks. Add "FP8/vLLM vs bf16/HF, paired p=0.11" to both.

## 2. The 0/32 execution result — INSTRUMENT ARTIFACT, not a trunk difference

**HIGH-1 (`README.md:3`, `README.md:9`, `summary.json` `reason`, `scripts/composition_pilot.py:379-386`,
`src/stencil/focus/slab.py:697-703`, `:1040-1042`).** The entire 0/32 is one leading markdown fence.

Three dense responses, verbatim from `results/quick-checks/check47/records.jsonl` (lines 1, 8, 32; the third is
round 15 of `slab-dev-01`, i.e. after fifteen consecutive rounds of envelope-error feedback):

````text
=== record line 1  — slab-dev-00 round 0, 135 output tokens, EOS 248046, not truncated, fence UNCLOSED
```json
{"calls":[{"op":"edit","path":"policy.py","code":"def step_0(x):\n   \"\"\"Map each integer v in x to v * 6 + 3, preserving order.\n\n   Input: x, a list of integers.\n   Output: a new list of integers where each element is v * 6 + 3.\n   Boundary: empty list returns empty list; order is preserved.\n   \"\"\"\n   result = [v * 6 + 3 for v in x]\n   return result"},{"op":"test"}],"report":{"status":"ok","task":"B"}}

=== record line 8  — slab-dev-01 round 3, 163 output tokens, EOS 248046, not truncated, fence closed
```json
{"calls":[{"op":"edit","path":"core.py","code":"def step_3(x):\n   \"\"\"Accept when count >= 4 and enabled is true.\n\n   Input: x (dict) with keys 'count' (int) and 'enabled' (bool).\n   Output: bool; True if count >= 4 and enabled is True, else False.\n   Boundary: count == 4 with enabled True returns True; count == 3 or enabled False returns False.\n   \"\"\"\n   result = x.get('count', 0) >= 4 and x.get('enabled', False) is True\n   return result"},{"op":"test"}],"report":{"status":"ok","task":"A","delivery":"queued"}}
```

=== record line 32 — slab-dev-01 round 15, 164 output tokens, EOS 248046, not truncated, fence closed;
                 this is after fifteen consecutive rounds of envelope-error tool feedback
```json
{"calls":[{"op":"edit","path":"core.py","code":"def step_15(x):\n   \"\"\"Accept when count >= 6 and enabled is true.\n\n   Input: x (dict) with keys 'count' (int) and 'enabled' (bool).\n   Output: bool; True if count >= 6 and enabled is True, else False.\n   Boundary: count == 6 with enabled True returns True; count == 5 or enabled False returns False.\n   \"\"\"\n   result = x.get('count', 0) >= 6 and x.get('enabled', False) is True\n   return result"},{"op":"test"}],"report":{"status":"ok","task":"A","delivery":"ready"}}
```

````

The failure path is `slab.parse_envelope` → `output.lstrip(" \t\r\n")` then `json.JSONDecoder().raw_decode` →
`ValueError` on the backtick → `EnvelopeError` → caught at `slab.py:1040` → `violations["breakage"]=True;
violations["format"]=True`, everything else left at its `False` initial value. That is precisely the
`0/0/32/0` + `breakage 32` row at README:13-14, and it is why `Executor.run` records zero executed calls.

**The counterfactual, run on CPU against the frozen tree, costs nothing and was not reported.** Strip the fence and
re-parse the same 32 saved outputs with the same frozen `slab.parse_envelope`:

| Frozen-tree re-parse of the 32 dense DEV outputs | Dense (fence stripped) | MoE actual |
|---|---:|---:|
| Envelope parses | **32/32** | 32/32 |
| `language` violations | **0/32** | 0/32 |
| `style` (indent) violations | **0/32** | **30/32** |
| `wrong_family` violations | **0/32** | 0/32 |
| `format` violations (report shape) | 6/32 | 10/32 |
| `delivery` mismatches (report half of `process`) | 4/32 | (process total 17/32) |
| Fence shape | 13 closed / 19 unclosed | n/a |

The 19/13 split in README:3 is exactly reproduced. Every one of the 32 responses is a well-formed
`{"calls":[edit, test],"report":{...}}` envelope; every one ends on EOS 248046; none is truncated; all 32 sit in
the 100–300 token "substantial body" band (`dev-summary.json` `in_100_300: 32`). The dense model tracked the
register perfectly, including the mid-episode `indent 3 → 2 → 3` switch at rounds 11-13, emitting `[3],[3],…,[2],
[2],[3],[3],[3],[3]`. It also obeyed "test takes no path" — which the MoE never did (below).

**HIGH-2 — the parser carries a registered repair for the MoE's characteristic deviation and none for the
dense model's (`src/stencil/focus/slab.py:723-728`).** `parse_envelope` has exactly three registered tolerances:
`trailing_closer`, `lift_report`, `test_path`. I counted tolerance usage in the committed MoE baseline: the
`test_path` tolerance fires on **32/32** MoE R rounds — every MoE response emitted `{"op":"test","path":"policy.py"}`
against a system prompt that says "test takes no path", and the harness silently strips it. The dense model got the
call shape right and was rejected for a fence. A parser that repairs 32/32 of one model's deviations and 0/32 of
the other's is not a neutral instrument. This is the review prompt's concern, quantified.

**HIGH-3 — "Matched R episodes" (README:7) is true for 2 of 32 pairs, not 32.** I compared
`rendered_messages` between the committed MoE R rows and the check-47 dense rows: **identical on 2/32** — the two
round-0 prompts. From round 1 the dense arm's retained history carries
`{"error":"envelope","expected":"{\"calls\":[...],\"report\":{\"status\":\"ok\"}}","reason":"invalid JSON: Expecting
value: line 1 column 1 (char 0)"}` while the MoE arm carries real edit/test receipts with file hashes. Thirty of
the thirty-two "matched" comparisons are between a model answering a working conversation and a model answering a
conversation poisoned by its own rejection. Worse, the error message names the expected object shape — which the
dense model *is* producing — so its repeated fence is not evidence of stubbornness either.

The one genuinely matched, un-diverged pair inverts the screen: at round 0, dense is style-, format- and
delivery-compliant on 2/2 episodes; the MoE violates style on 2/2 (4-space bodies under `indent 3`) and violates
`process` on 2/2 (it volunteers `"delivery":"staged"`/`"queued"` on task B, where delivery is scoped to task A).

**MEDIUM-1 — the harness's own see-through diagnostic is fence-blind too
(`results/quick-checks/composition-pilot-4/report.py:33`).** `round0_indent.raw_prefix_eligible_edits` exists
precisely to inspect emitted fields when the executor rejects a reply ("Inspect emitted fields diagnostically;
never feed a prefix to the executor"), but it uses `raw_decode(r['output'].lstrip())` — the same call that fails
on a backtick. So `dev-summary.json` reports `raw_prefix_eligible_edits: 0`, and the run had **no instrument
capable of observing dense behaviour at all**. That is why the artifact set contains no hint of the table above.

**Plain answer to the question asked.** "STAY" is not supportable on this evidence *as an execution result*. The
honest reading of the harness comparison is **INELIGIBLE — the dense trunk was not measured**; 32/32 responses
were well-formed work rejected on a presentation convention the parser was never asked to accept. The JavaScript
result stands separately (Section 3), and the cost projection stands separately (Section 4), and those two are
what should carry the decision.

To the report's credit, it does not hide the mechanism: README:3 names the parser, README:16 says the zero
style/process counts "do not establish compliance", and README:41 says "STAY is a screen result under this
renderer/backend, not evidence the dense trunk is generally inferior." Those caveats are correct and were written
without prompting. The defect is that a five-minute CPU diagnostic would have converted "we don't know" into
"we know, and it points the other way", and the headline and `summary.json` `reason` were left asserting the
contaminated criterion as decisive.

## 3. JavaScript 22/32 vs 16/32 — real, properly paired, and not statistically distinguishable

**Re-scored independently.** I re-ran the check-40k Node harness myself (`node v22.22.2`) over all 64 responses —
32 dense from `js-records.jsonl`, 32 MoE from `check40k/records.jsonl` (`phase=eval`, `arm=text-only`) — using a
standalone copy of `NODE` and `extract_code`, against `check40k/tasks.json`. Result: **dense 22, MoE 16, zero
mismatches with the recorded scores.** The numbers are sound.

**Pairing is genuine.** The 32 `task_id`s are identical sets. Decoding the MoE `input_token_ids` with the
Qwen3-30B tokenizer, the dense run's stored `messages` system and user content appear verbatim in the MoE prompt
on **32/32** tasks. Both renders use `<|im_start|>…<think>\n\n</think>\n\n` — thinking disabled on both sides, same
cap 768, same four hidden tests, same `no_mutation` rule. The template and prompt confounds are controlled.

**Exact paired test (the repo's own `focus_check40k.sign`).** Discordant pairs: dense-win 8, MoE-win 2 (both
success 14, both fail 8). One-sided p = 56/1024 = **0.0547**; two-sided p = 112/1024 = **0.1094**. Not significant
at α = 0.05. (Unpaired Fisher on 22/32 vs 16/32 gives p = 0.203, for reference.) A registered paired statistic
exists in `focus_check40k.pair()` and was not applied.
**MEDIUM-2 (`README.md:5`, `WORKLOG.md`, `plan/LEDGER.md`):** "passes 22/32 versus the MoE's 16/32" reads as a
competence gap and is at present indistinguishable from noise on 32 paired tasks. Per AGENTS.md ("existence
questions get a registered statistical test"), the p-value belongs next to the number.

**Confounds, all entangled and none separable from this design** (README:5 acknowledges the class, not the list):
architecture (hybrid dense vs MoE), size (27B dense vs 30B-A3B), precision (FP8 e4m3 block-scaled vs bf16),
inference stack (vLLM 0.19.2rc1 vs HF Transformers `Qwen3MoeForCausalLM`), attention kernel (`TRITON_ATTN` vs
`sdpa`), expert path (`experts_implementation="eager"` on the MoE), batching (4-way continuous batching with
prefix caching vs sequential single-stream with router hooks), and tokenizer/vocabulary. Sampling is controlled
(both greedy). Notably the MoE side is the *no-intervention* arm of a bias experiment (`active=None` for
`text-only`, with `assert all(not x["masked"] …)`), so it is a clean baseline — good.

Two details in the dense model's disfavour, which make 22/32 a floor: both dense failures on `roundTag` and
`batchCredits` are cap-768 truncations that left an unclosed fence, and `extract_code` returns `""` on a fence
count ≠ 2. The MoE truncated zero times. So the dense model paid for verbosity twice and still won 8 discordant
pairs to 2.

**And the sharpest fact in the whole check:** `focus_check40.extract_code:432-438` *strips markdown fences*. The
JavaScript scorer is fence-tolerant; the agentic envelope parser is not. Identical model behaviour scores 22/32 in
one instrument and 0/32 in the other.

## 4. The 24.2 GPU-hour projection — arithmetic exact, extrapolation optimistic, and pointed at the wrong harness

**Re-derived exactly.** `max_tokens = max(2204, 2600) = 2600`; `tokens = 160·2600·rounds/16`;
`serving = tokens/agg`; `fp8_h = (startup + 1.25·serving)/3600`; `bf16_h = (startup + 2.5·serving)/3600`;
`startup = ready_at − lifecycle.start = 342.298 s`. Rates: DEV C2 = 4804/378.469 = 12.693255 tok/s;
JS C4 = 6985/290.796 = 24.020238 tok/s. All four README rows reproduce to two decimals: 11.47/22.85, 6.11/12.12,
22.85/45.61, **12.12/24.15**. `gpu_held = 1015.477 s ≤ 2400`. `audit.json` counts (28 hashes, 64 HTTP, 32+32
replays) all verified.

**MEDIUM-3 — "~24.2 h" is the optimistic row, not the registered conservative one.** README:28 states plainly
that "the registered conservative long-episode comparison is the 32-round row"; the 32-round *DEV C2* row is
**45.61 h**. 24.15 h is the 32-round row on a **cross-workload proxy** — a short-context, 4-stream JavaScript rate
applied to long-context agentic token totals. Quoting 24.2 as "the" 32-round projection silently picks the
cheaper basis. The README is right; the summary of it is not.

**MEDIUM-4 — the token basis comes from the broken run.** 2600 tokens/episode is what the dense model emitted
while receiving nothing but error feedback. The MoE's matched R episodes emitted **2870 / 2972** tokens over the
same 16 rounds. Re-basing on 2972 raises every row by 14.3%: 16-round JS-C4 goes 12.12 → **13.84 h**, i.e. the one
row anywhere near the ≤12 h gate **flips to a fail**. 32-round DEV-C2 goes to 52.13 h. The projection is
optimistic in the direction that matters.

Two further structural notes: linear scaling in rounds ignores that decode throughput degrades as retained context
grows (observed max context already 11,259 at 16 rounds), and the 2× bf16 multiplier is applied to *total serving
time* including HTTP, barriers and tool time, not just decode — which errs conservative, so it partly offsets.
README:37 discloses both.

**Under the SLAB-2 harness the number is different — and I computed it with SLAB-2's own registered method**
(`tests/fixtures/slab2_cpu_report.md:30-36`: 594,702 reference output tokens, 2,560 calls, 0.8 s/call TTFT,
reserve 1.25). My implementation reproduces the committed MoE rows exactly (9.071182 h and 11.997207 h), so the
method is right:

| SLAB-2, 16 rounds, fenced whole-file, cap 2048 | reference basis | ×1.35 model-style | ×2 bf16-equivalent |
|---|---:|---:|---:|
| MoE assumption, 24.7 tok/s (committed) | 9.07 h | 12.00 h | — |
| **Dense FP8 at its measured JS-C4 24.020 tok/s** | **9.31 h** | **12.32 h** | **24.63 h** |
| Dense FP8 at its measured DEV-C2 12.693 tok/s | 16.98 h | 22.67 h | 45.35 h |

At FP8 and equal concurrency the dense trunk costs essentially the same as the MoE (9.31 vs 9.07 h) — its
aggregate throughput, 24.020 tok/s, is within 3% of pilot-4's MoE 24.731 tok/s. **The whole cost case against the
dense trunk rests on the unmeasured 2× bf16 heuristic**, which the registration requires because the science needs
bf16 weights. That is a defensible requirement and a defensible first-order proxy for a bandwidth-bound 27B dense
model (27 GB → 54 GB of weights), but it is a heuristic deciding a gate, and README:37 says so.

Also note SLAB-2's arm structure is **R/N/Q ×64 + T/O ×16 = 224 lane-episodes**
(`src/stencil/focus/slab2.py:806-808`), not the 160 in README:28. Any forward-looking cost row should use 224.

## 5. Architecture — confirmed from the local config, and it is the strongest STAY argument, unstated

Confirmed from `/home/bmarti44/models/qwen3.8-27b-fp8/config.json` and the safetensors weight map:
`num_hidden_layers 64`, `layer_types` = **48 `linear_attention` + 16 `full_attention`**,
`full_attention_interval 4`, full attention at indices 3, 7, 11, …, 63. The linear layers carry
`linear_attn.A_log`, `.conv1d.weight`, `.dt_bias`, `.in_proj_{a,b,qkv,z}` and `.norm` — the Gated DeltaNet
signature. `quantization_config`: fp8 e4m3, dynamic activations, block-scaled (`weight_scale_inv` on every large
projection); the server log confirms `quantization=fp8` with `CutlassFp8BlockScaledMMKernel`, `dtype=torch.bfloat16`
as compute dtype. So "native FP8 loaded" (README:39) is accurate, and the previously "[unverified against the local
config]" claim in `results/dense-focus-research-fable.md:163` is now **verified**.

**Consequence for the certified attention-mask release.** Brian's register design releases a rule by attention
masking and never deletes history. On this trunk that mechanism can only touch **16 of 64 layers**: the 48 GDN
layers carry a recurrent state with no per-token key to evict, so a masked token's contribution cannot be removed
without recomputing the state from the start of the sequence. Note also that the 40h/40i "mask" was already only
position-preserving KV eviction in a research harness and "has not been shown equivalent" to a serving-time
attention mask (`results/check40i-review-fable.md:127-129`) — so on the dense trunk the contingency degrades twice
over.

**LOW-2 (`README.md`, all lines).** This fact is recorded in `model-metadata.json` but appears nowhere in the
README and no consequence is drawn. It is a *structural, precision-independent, parser-independent* reason the
dense trunk is a poor host for the registered release mechanism — a far more durable STAY argument than 0/32, and
it is buried in a config dump.

**MEDIUM-5 — an experimental serving path is undisclosed.** `server-0.log:13-14`: "Mamba cache mode is set to
'align' … Prefix caching in Mamba cache 'align' mode is currently enabled. Its support for Mamba layers is
experimental. Please report any issues you may observe." The run enabled `--enable-prefix-caching` with
`VLLM_BATCH_INVARIANT=1` on a hybrid model over 16-round retained-history prompts, on an experimental code path
touching exactly the 48 GDN layers. It is not the cause of the fence, and no determinism gate was run for check 47
(pilot-4 had one: cold-reverse + b1_cold/b1_warm/b4_mixed). Disclose it; do not build on the dense timings without
it.

## 6. Bottom line for Brian

**Is the trunk decision correct as recorded?** The decision yes; the record no. STAY is over-determined — the
registered rule at `registration.json` `reading` is conjunctive, and the bf16-equivalent ≤12 h clause fails on
every row the check produced (best row 12.12 h, and 13.84 h once re-based on the MoE's own token counts). But
`README.md:37` and `summary.json` `reason` rest the decision on the execution criterion, which is the one clause
that measured the parser rather than the model. If 0/32 is carried forward it becomes a false record of dense
competence — the same failure mode as the "never pressed"/"bitwise identical" claims that died on re-verification
(AGENTS.md, 2026-08-30). **Recommended edit, no re-run needed:** mark the harness row INELIGIBLE, add the
fence-stripped counterfactual table from Section 2 as a CPU diagnostic, move the deciding reason to the cost
clause, and add the paired p = 0.11 to the JS line in README, WORKLOG and LEDGER.

**The single experiment that would settle it fairly.** Zero GPU hours: re-run the *frozen* pilot-4 consumer over
the 32 already-saved dense outputs with one added, explicitly-registered parser tolerance —
`strip_leading_fence` — replaying each round's executor and checker in sequence exactly as `audit.py` already
does. This is not a rescue and not a re-fit: the model text is fixed and the tolerance is a fourth sibling of the
three the MoE already enjoys. It will yield a real executed rate, real receipts, real `process` and `semantic`
counts, and a real final-success number, on the same two episodes. The only thing it cannot recover is the
divergence from round 1 onward, since the dense arm's history is poisoned; so run it forward as a fresh
CPU-replayed episode and label round ≥ 1 as counterfactual-history. If Brian wants one GPU measurement instead,
the honest one is 2 episodes × 16 rounds under **SLAB-2** (≈ 12 min at the measured rate), because SLAB-2 is the
harness that will actually run.

**Does anything change the queued plan?** No — and one thing sharpens it.

- **Pilot 5 on the MoE: proceed unchanged.** Nothing here bears on it. The `slab2-review-fable-r2.md` GO and the
  two driver items stand.
- **The larger test (64 episodes) on the MoE: proceed unchanged.** The committed SLAB-2 cost table puts the MoE at
  9.07 h reference / 12.00 h model-style against a ≤12 h gate; my independent recomputation reproduces both
  figures exactly. That gate is *tight* — a 0.03 h margin at ×1.35 — and is the thing to watch, not the trunk.
- **The one sharpening.** SLAB-2's system prompt is `"Each response is exactly ONE fenced code block containing
  the WHOLE requested file: ```python core.py …"` (`src/stencil/focus/slab2.py:59-72`), and `parse_reply`
  *requires* exactly two fence markers, tolerates a leading `<think>` block and tolerates leading prose
  (`slab2.py:417-433`). **The behaviour that scored the dense trunk 0/32 is the behaviour SLAB-2 mandates.** So
  check 47's execution finding does not transfer to the successor harness at all, and it must not be cited as a
  reason not to revisit the dense trunk later. (Its 19/32 unclosed fences would fail SLAB-2's exact-two-fence
  rule; but in the JS bank, where a fenced block was the natural output, it closed 30/32 and the two misses were
  cap truncations — so the unclosed rate looks like an artifact of wrapping JSON in a fence, not a stable trait.)
- **What should be recorded as the durable reason to stay on the MoE:** (a) the bf16-equivalent cost gate, and
  (b) the 48-of-64 GDN architecture, which caps the certified attention-mask release at a quarter of the stack.
  Both are parser-independent. Neither is currently in the README.

---

### Findings index

| # | Sev | Where | Finding |
|---|---|---|---|
| HIGH-1 | high | `check47/README.md:3,9`; `summary.json` `reason`; `scripts/composition_pilot.py:379-386`; `src/stencil/focus/slab.py:697-703,1040-1042` | 0/32 is a leading markdown fence; all 32 parse and are 0/32 style-violating once stripped (frozen-tree verified). Harness row should read INELIGIBLE. |
| HIGH-2 | high | `src/stencil/focus/slab.py:723-728` | Parser's `test_path` tolerance repairs 32/32 MoE rounds; no tolerance offered for the dense deviation. Asymmetric instrument. |
| HIGH-3 | high | `check47/README.md:7` | "Matched R episodes": only 2 of 32 prompt pairs are identical; 30 dense rounds answer an error-poisoned history. |
| MED-1 | medium | `composition-pilot-4/report.py:33` | The see-through `raw_prefix` diagnostic is itself fence-blind; the run had no instrument able to observe dense behaviour. |
| MED-2 | medium | `check47/README.md:5`; `WORKLOG.md`; `plan/LEDGER.md` | 22/32 vs 16/32 given without the registered paired test; exact McNemar two-sided p = 0.109 (8 vs 2 discordant), one-sided 0.055. |
| MED-3 | medium | `check47/README.md:28,35` | 24.15 h is the optimistic cross-workload row; the registered conservative 32-round row is 45.61 h. |
| MED-4 | medium | `check47/report.py:16` | Projection token basis (2600) taken from the broken run; MoE matched basis is 2972, which pushes the only near-gate row 12.12 → 13.84 h. |
| MED-5 | medium | `check47/server-0.log:13-14` | Experimental Mamba-`align` prefix caching enabled on a hybrid model over retained-history prompts; undisclosed, and no determinism gate was run. |
| LOW-1 | low | `WORKLOG.md`; `plan/LEDGER.md` | JS number recorded without precision/backend/significance qualifiers in the lines that will be read later. |
| LOW-2 | low | `check47/README.md` (absent); `model-metadata.json` | 48 GDN + 16 full-attention (interval 4) verified from the local config but never surfaced, and its consequence for the mask-release contingency never drawn. |

Nothing rises to CRITICAL: the artifact set is complete, the audit is real (28 hashes, 64 HTTP token/EOS/cap
checks, 32 exact consumer replays against an isolated frozen tree, 32 Node re-scorings — all of which I spot-
verified), the resource discipline is clean (single container, exit 0, removed, 1015.5/2400 s,
`gpu-before.json` shows no compute apps at launch), and the final trunk decision is right. The defect is
diagnostic, not evidentiary: a perfectly faithful replay of an instrument artifact reproduces the artifact.
