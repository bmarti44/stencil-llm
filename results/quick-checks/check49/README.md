# Check49 — NO-GO: two LoRAs select the initial language but do not SWITCH or CLEAR

2026-09-07 · gpt-6-astra · frozen bf16 Qwen3-4B dense proxy · recipe freeze `166598bb`.

**Completed registered experiment, NO-GO.** All272 generations and both one-epoch fits completed in850.757 GPU-held seconds. M, T and X each achieved **0/12 all-active episodes** because every M/T SWITCH failed the language requirement. M cold-HOLD passed10/12, but M introduced10 executable losses versus T and CLEAR passed only4/12 with five stale JavaScript impositions. This is neither INELIGIBLE nor a budget-truncated experiment. The supplemental cache-matched parity audit is pending GPU availability; the original full-prefix checks and limitation are preserved below.

The [user amendment](../../handoff/briefs/check49-brief.md) adopts [Astra's two-LoRA contract](../../dense-focus-research-astra.md), replacing [Fable's single-adapter teacher-distillation/40k proposal](../../dense-focus-research-fable.md). This run is supervised adaptation on CPU-authored solutions, **not a reproduction of Prompt Baking KL distillation**, and uses no40k second look. Both recipes ask whether a separate weight carrier can hold a rule without text; the amendment additionally demands reversible lifecycle control, paired competence, causal labels and shipping relevance. The complete five conditions are copied verbatim in [registration.md](registration.md).

## Registered readings

| Condition | Observed | Reading |
|---|---|---|
| Full records, eligibility, <=3600 GPU-held seconds |272/272 calls; setup Python8/8, JS8/8, default Python8/8;32/32 fitting steps; main850.757s | Pass; supplemental audit time will be added |
| M all-active>=10/12; cold>=10/12; M-X>=3 with paired exact p<=.05 | M0/12, T0/12, X0/12; cold10/12;0 favorable/0 unfavorable discordances, p=1 | Fail |
| Zero newly broken/truncated M where paired T succeeds; M all-active>=T |10 executable losses,5 wins across60 decisions; losses occur in all five decisions of episodes2 and9 | Fail; wins cannot offset losses |
| CLEAR>=11/12, zero stale impositions, OFF replay parity |4/12 CLEAR;5 stale impositions;12/12 same-history replay matches | Fail independently of the parity diagnostic |
| More all-active than T, or equal with>=50% fewer rule-carrier positions and<=10% more inference time |0 versus0; positions0 versus576; M188.853s versus T191.436s (-1.35%) | Cost clause passes, but a tie at zero complete episodes is not useful control |

The exact paired test operates on independent episodes, not the48 correlated active decisions. There were no favorable episode discordances, so p=1. No late rank, learning-rate, checkpoint, task, cap, cue-placement or threshold changes were made.

## Language, execution and breakage

M selects the current adapter without text; T uses the current rendered rule without adapters; X swaps the adapter labels without text. At CLEAR every arm disables adapters and T removes the current rule. Every request rebuilds fresh cache/state from the full literal history. No masks, answer deletion or cache reuse occur in trajectories. The cold probe is separately registered and retains the initial adapter with a neutral exchange but no old code demonstrations.

| Active decisions,48 per arm | M | T | X |
|---|---:|---:|---:|
| Required language |34|34|10|
| Executable semantics, irrespective of language |33|37|29|
| Required language AND semantics AND no truncation |25|28|7|
| Syntax/recognition failures |3|3|11|
| Truncations at96 tokens |3|3|7|
| Presentation failures |3|6|7|

Language successes for M by SET/HOLD/SWITCH/BACK are **12/11/0/11 of12**; T is also12/11/0/11, while X is0/0/10/0. Joint executable successes for M are9/8/0/8, versus T10/9/0/9. Selection affects the first answer and cold behavior, but neither this miniature adapter nor this particular text-rendering baseline overrides retained answer language at SWITCH. This does not compare against a masking or alternative rendering design.

Across all60 lifecycle decisions, including CLEAR, M/T/X execute41/46/36 correctly; syntax/recognition failures4/4/14 and truncations4/4/9. Counts overlap and must not be added. M's ten paired executable losses are the `unique` and `flatten` episodes, five decisions each; there are no additional sentinel losses. All per-task failures and literal completions remain in [records.jsonl](records.jsonl); [audit.json](audit.json) contains per-episode and per-stage tables.

Fresh OFF writes Python12/12 and executes10/12. M's CLEAR matches that fresh language with correct execution on4/12; it retains JavaScript in episodes1,3,5,7,9, five of six JavaScript-initial episodes. All12 same-history OFF references reproduce the corresponding M CLEAR token-for-token. **Identical OFF computation does not erase earlier emitted examples from the transcript.**

The unrelated sentinel bank is eight tasks paired with a preassigned adapter, i.e.16 calls, following the amended272-call arithmetic. Exact requested JSON-format/content success is1/8 for both ON and OFF. The other seven pairs give the right factual value inside an object instead of the requested scalar, so the strict check fails. This is weak evidence about unrelated competence: only one pair passes the full baseline contract. Sentinel `syntax`/`presentation` fields are fixed placeholders; only the strict JSON equality field is scored. The code-task presentation/syntax metrics above are separately measured and do not include these placeholders.

## Fitting, lineage and assets

Fit-on=128 newly authored examples per mode from16 training families, with CPU-authored Python and JavaScript references. Setup-on=eight other authored task families. Evaluate-on=12 new families, one episode per family with five decisions plus a cold variant, and eight unrelated sentinels. Family names/semantics and prompt IDs are disjoint across fit/setup/evaluation; variants within a family are related, and the statistical unit is the episode. No benchmark items, benchmark responses, check40k bank, or reads under `data/bench` were used. There is no trunk-generated teacher corpus or evaluation-driven selection.

[Data](data.json) freezes the authored prompts, references and independent expected outputs. CPU validation executed416 references in Python/Node,832 wrong/stale mutants, and five targeted consumer/gate tests; longest reference57 real-tokenizer tokens. All fit sequences fit cap256 without truncation. Training: seed0, rank8 q/v on all36 layers, alpha8/dropout0, bf16 trunk and adapters, output-only loss, AdamW1e-4/weight_decay.01, batch8, one epoch,16 steps per mode. Every step has finite nonzero adapter gradients; no trunk parameter ever receives a gradient. Both fits took14.139s, or14.196s including save, under the600s ceiling. [fit.jsonl](fit.jsonl) records each step.

The final, unmerged adapters are retained outside git for Check50:

| Adapter | Local directory | Parameters | Weight bytes | SHA256 of adapter_model.safetensors |
|---|---|---:|---:|---|
| Python | `data/classifier/model/focus-lora-4b/python/` |2,949,120|5,917,336|`56f352c50c0473035df9603dc981f72f2aa856ece26de14f1a42cc892ce8e4f7`|
| JavaScript | `data/classifier/model/focus-lora-4b/js/` |2,949,120|5,917,336|`229858707ab48a55589786f55773be961f3b53146cb8c3949ed89109da23fc12`|

Combined files including config/README are11,847,352 bytes (11.30MiB). [adapter-manifest.json](adapter-manifest.json) binds all six files. These are completed recipe weights, not a successful lifecycle certificate or authorization to launch Check50/27B follow-ups.

## OFF parity and numerical-path limitation

All trunk tensors were hashed in memory before and after fitting/evaluation: **zero changes**. All base-model local file hashes likewise match, and all non-LoRA gradients remain None. ON changes the logits for all16 parity prompts.

For16 baseline prompts, the pre-fit pristine, post-fit OFF and direct-pristine-layer full-prefix logit hashes match exactly16/16. The frozen diagnostic additionally compared full-prefix teacher-forced argmax tokens to an earlier incremental cached greedy sequence. That cross-path comparison differs on one prompt (`baseline/python/2`), yielding the original `parity.token_diffs=1`; this is not an observed OFF-versus-pristine logit difference. The original [parity.json](parity.json) and [summary.json](summary.json) are immutable evidence, including that overly strict cross-path comparison.

A bounded [cache-matched teacher-forced audit](audit_parity.py), committed as `7447a43f` before its launch, replays exactly the same16 saved token streams under both OFF and direct-pristine paths with fresh incremental caches. It does not sample new outputs, fit, change labels or rerun evaluation. Its first preflight yielded to another Stencil flag before model loading. Result and cumulative cost: **PENDING GPU availability**. The NO-GO does not depend on this discrepancy: lifecycle, competence and behavioral release fail separately.

## Cost and verification

Measured load plus initial tensor hashes56.970s; full fit/save14.196s. The first-step fit projection was38.041s. After actual complete setup histories, the registered conservative cap96 projection was3061.472s<=3600s, so the full evaluation launched. Actual main GPU-held time850.757s (14.18min), including load, fitting, parity tensors, generation, checks, hashes and cleanup. The added audit remains within the same cumulative3600s allocation.

All272 calls used63,229 input tokens and14,090 generated tokens. CUDA forward-event prefill/rebuild time19.160s, decode736.222s; these exclude CPU/tokenization/checker overhead. End-to-end per-call generation latency including rebuilds has p50=2.913s, p95=5.178s. Main peak allocated CUDA memory13,351,041,536 bytes. T used576 incremental rule-carrier input positions (12 each on48 active requests); M/X used zero. All60 trajectory wall times: M188.853s, T191.436s, X210.398s. Total T/M input counts differ by770, partly from different retained outputs; that total difference is not the registered rule-carrier count.

[CPU replay audit](audit_results.py) verifies272 decoded/tokenized records, all180 literal trajectory histories, exact scorer replay, fit counts and adapter/base hashes with zero discrepancies. The frozen runner is [scripts/focus_check49.py](../../../scripts/focus_check49.py); targeted tests are [tests/test_focus_check49.py](../../../tests/test_focus_check49.py). No full test suite, processes signalled, push, or external messages. Main process exited normally and removed its own flag.

**Reading:** close this registered miniature two-LoRA recipe as a useful persistent focus controller. Cold-HOLD and initial selection are real positive observations; competent SWITCH and history-aware CLEAR are absent. Retain rendering as the engineering default and test any masking claims on the actual trunk separately. The amended Astra contract explicitly prevents turning this undertrained one-epoch proxy into “weights cannot encode rules” or universal dense-model impossibility. No follow-up GPU experiment is launched by this NO-GO.
