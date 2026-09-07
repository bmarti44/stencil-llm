# Check 48 — COST-INELIGIBLE

Data lineage: **fit-on = audited Kimi/Opus/Astra authored corpora; evaluated-on = fresh Fable held-out-4 once after frozen adapter**, with v8 SETUP as a development diagnostic. No benchmark inputs/responses or `data/bench` reads. Entire Astra-enrich-2 (90 evaluation-derived rows), linked visible relatives, and unresolved audit cases are excluded. Historic taxonomy/probe-development influence remains disclosed by LABELS.md; audited item-level provenance is not proof of perfect disjointness from inaccessible corpora. Check46 was NO-GO, so this is the main fitted-updater hypothesis.

**Stopped at the registered throughput gate.** Full fit/save projects **22.32 minutes** (<=25); full evaluation projects **38.01 minutes** (>22). GPU occupied **86.90 seconds**. No fixed fit, adapter, held-out look or SETUP run. This measures feasibility of the frozen HF/schema configuration; fitted quality remains unknown.

## Frozen contract and selection

Exactly **2,048 FIT transitions** (683 add / 683 none / 682 updates) plus **128 scenario-held DEV transitions** (43/43/42). Each is complete for its visible empty or single-target register. This does not test multi-target selection or a full predicted-register lifecycle. Kimi admission1/2/3, relations/transitions/overrides/transitions3 and clean Opus/Astra enrichments all contribute; source hashes/counts, exclusions and field repairs are in conversion-manifest.json. The completed Opus pass3 patches at bafd6548 were applied immediately; no wait or duplicate pass3 audit. Patch identity and old values are checked. Derived-value audit corrections are separately recorded in conversion-patch.jsonl.

Selection is outcome-independent: connected components union shared domains, Kimi source batches, explicit scenario/parent/family identities, repeated messages and old-rule texts. Approximately 10% of hash-ordered groups plus authored DEV groups are reserved for DEV; fixed category counts are filled round-robin across source/family strata in SHA256 order. Enrichment sessions span domains and are grouped by domain/explicit relatives rather than globally by session. This conservative scenario proxy is disclosed, not a proof of semantic independence. No author-disjointness is claimed for DEV; Fable is reserved for screening. Overflow above 768 total training tokens is excluded and journaled before selection, never truncated. The final selected sample has no overflow.

Minimal admission spans exclude leading temporal/task framing cues and terminal `. ! ? , ;`, retaining conditional when/if/whenever triggers. All offsets are recomputed against exact text, including pass3 target_span ends. Whole-message relation spans remain evidence only; independently derived grounded values omit retirement, old-value comparisons and justification. Three selected-value corrections were made after a full read of selected supersedes values. This fallible conversion audit is not an independent review. Unresolvable replacement or admission metadata is excluded before fixed selection. Fields: `op,span,key,scope,kind,value,target_id`; kind is `instruction`; scope global or normalized task slug; relation keys/IDs refer to the visible target. Add uses null target; cancels/completes use empty value; reinstates copies the original instruction; supersedes carries the replacement. None is the empty list. No gold label, rationale, source ID or candidate span is an input.

## Fixed runtime and budgets

Qwen3-4B from models/qwen3-4b-hf, BF16, seed0, PEFT0.20.0 rank16/alpha32 on q/k/v/o/gate/up/down projections, dropout0, bias none. One epoch; AdamW LR1e-4, betas .9/.999, epsilon1e-8, weight decay0, grad norm1, batch4, no accumulation, fixed seeded order, output-only loss, SDPA. No seed/epoch/checkpoint search. Six pilot optimizer updates are discarded by restoring every initial adapter tensor, optimizer and RNG; the fixed fit starts fresh. Only a complete 2,048-row epoch may be saved as the screened adapter.

HF generate, greedy, thinking off, cap512, batch8, strict JSON schema prefix enforcement with LM Format Enforcer and exact post-parse schema validation. A local prefix adapter uses the public TokenEnforcer API because the installed HF integration imports an obsolete tokenizer alias. Normalized verbatim matching is inherited from check46 (whitespace, curly quotes, case; ambiguous or paraphrased spans rejected). Authenticated non-user-role guard rejects all operations, while preserving raw output. No other rule/template gates. Batch completion time is recorded as response latency for each concurrently processed message; amortized GPU seconds/message is separately reported and never substituted for p95 latency.

Hard phase caps: **300s load/smoke +300s pilot +1500s fit/save +1320s evaluation (including all DEV and SETUP) +180s cleanup =3600s**. Occupied GPU time includes intervening CPU/commit work. Pilot projects fit from five warmed training steps with 25% margin plus30s save, and evaluation from eight longest-output DEV rows with25% margin and the full header-inclusive bank-size upper bound. Both phase projections must fit before the fixed run; no reduced sample, cap or cut checkpoint. Cooperative deadline checks stop the owned job without signals. The own RUNNING.flag is deleted on normal/error cleanup; other flags/processes and Brian's llama-server are untouched. All adapters remain out of git with hashes committed.

## Prewritten readings and scoring

SCREEN-GO requires complete banks, admission overlap recall >=85% and precision >=95%, gold-negative payload/quoted false admission <=3% each, non-user false admission0; relations accuracy >=94% and supersedes recall >=85%; SETUP <=2/96 false-admission turns and36/36 admits; GPU p95 response latency <=1s. It licenses a registered full-data fit plus larger fresh validation, not shipping. PARTIAL means exactly one quality half passes; no automatic refit. NO-GO means complete quality bars missed. Deadline/infeasible projection gives INCOMPLETE/COST-INELIGIBLE and no quality verdict for unfinished banks. Both halves passing quality but failing latency is cost-ineligible for SCREEN-GO.

Admission uses check46's one-to-one exact/overlap micro/macro metrics and message-level false-admission denominators/Clopper–Pearson bounds. Relations uses operation on the overlapping target span with invalid/multiple operations counted as errors, target accuracy separately. Value and complete-operation correctness are scored where converted DEV supplies complete gold; the screening pair labels lack full value gold, so no fabricated semantic-value score. All seven requested family rows are reported for both tasks using frozen descriptive predicates in convert.py, with denominators and N/A for empty/unmeasured cells. Cue-less is a lexical proxy, and relation family membership can use author rationale for reporting only.

PEFT API reference: [Hugging Face LoRA documentation](https://huggingface.co/docs/peft/package_reference/lora). Installed versions and exact local code govern this run.

## Outcome

**COST-INELIGIBLE**. GPU occupied 1.448/60 minutes. Stage: pilot.
The fixed fit/screen did not complete. Held-out quality, SETUP and per-family accuracy are **unmeasured**, not zero. No quality conclusion about Qwen3-4B is licensed.

- load_smoke_seconds: 56.692
- pilot_seconds: 29.651
- train_tokens_per_second: 889.072
- projected_fit_save_seconds: 1339.263
- projected_evaluation_seconds: 2280.819

### Admission families

| Family | Correct / denominator | Rate |
|---|---:|---:|
| cue-less | Not evaluated | N/A |
| multi-rule-list | Not evaluated | N/A |
| rule+payload | Not evaluated | N/A |
| withdraw+replace | Not evaluated | N/A |
| bare-value+temporal | Not evaluated | N/A |
| task-scoped-override | Not evaluated | N/A |
| actually-B | Not evaluated | N/A |

### Relations families

| Family | Correct / denominator | Rate |
|---|---:|---:|
| cue-less | Not evaluated | N/A |
| multi-rule-list | Not evaluated | N/A |
| rule+payload | Not evaluated | N/A |
| withdraw+replace | Not evaluated | N/A |
| bare-value+temporal | Not evaluated | N/A |
| task-scoped-override | Not evaluated | N/A |
| actually-B | Not evaluated | N/A |

### Pilot interpretation and disposition

The eight longest-gold-output DEV rows form one conservative batch, all from Kimi admission3. After discarding the timing updates, the base adapter state generated 378 total output tokens (maximum 121) in 16.826 seconds of GPU generation, 16.856 seconds including per-batch preparation/records. Four rows emitted an empty list; two proposed invalid supersedes targets. These are pre-fit DEV observations, not held-out or fitted-updater quality scores. Eight parser replays match; zero JSON/schema failures, two typed target rejections.

Projection is **1.25 × (16.855939/8) ×866 =2280.819 seconds**. The 866 is a conservative header-inclusive physical-line upper bound for both heldout4 files plus 96 SETUP and 128 DEV. Without the 25% margin the full evaluation still projects 30.41 minutes; excluding all 128 DEV it projects 32.40 minutes with margin. The longest-output batch is deliberately conservative and not a representative latency sample, so this does not prove an optimally batched implementation cannot fit. No recipe/batch/cap change or refit was made to rescue the screen. Batch-visible response latency 16.826 seconds is not isolated single-message latency.

Peak allocated GPU memory 29.96 GiB. The fixed fit never started; no adapter directory or weights were created, and adapter-manifest.json explicitly records that absence plus unchanged base hashes. DEV inference records are pilot-dev-records.jsonl (eight pre-fit calls); no full-DEV or held-out inference records exist. All requested family results above are unmeasured. The source banks remain available for a future independently registered run. No deployment change or automatic next fit is licensed. Five CPU tests, three grammar-consumer witnesses, all 2,176 gold-parser checks and eight saved-parser replays pass. Own flag absent and process exited normally; no signals or push.
