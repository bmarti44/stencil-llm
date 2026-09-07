# Stencil handoff — 2026-09-07, CPU documentation correction

The registered 64-episode larger test is RUNNING according to Brian's current instruction. Its outcome is unassessed here. This replaces the old handoff end to end, applying all 15 corrections in [the full-program audit, Section 6](full-program-review-astra.md). Work from `/home/bmarti44/stencil-llm`. Do not replay the old queue.

## Authority, authorization and protection (corrections 3, 8–10, 13)

| Authority | Current role |
|---|---|
| Brian's current 2026-09-07 handoff-rewrite instruction | CPU only; edit and commit exactly HANDOFF-astra.md, CLAIMS-CORRECTIONS.md and astra-assessment-adoption.md; no push. Overrides historical ledger-writing and launch instructions for this task. |
| Frozen [Amendment 5 registration](larger-test/REGISTRATION.md), commit `95fa7fc0c006518ef84c1ea20c152c079ae1798a` | Governs the running experiment, endpoints, allocation, budgets and acceptance. This rewrite uses committed Git objects, not live run files. |
| [AGENTS.md](../AGENTS.md) | Standing operational lessons, including review ownership and explicit-path commits. Its root PLAN.md and plan/PROTOCOL.md pointers are stale. |
| [Archived PLAN](../archive/PLAN.md), [archived PROTOCOL](../archive/plan/PROTOCOL.md) | Historical science/process context; obsolete fixed models, roles and repeated review loops do not supersede current instructions. |
| [plan/LEDGER.md](../plan/LEDGER.md) | Classifier-line state (latest STATE: check44c complete/NO-GO), not full-program or larger-test status. |
| [Audit](full-program-review-astra.md), this handoff and [corrections table](CLAIMS-CORRECTIONS.md) | Evidence limits and continuation guidance; do not amend frozen science. Old v1/v2 proposals, briefs and scratchpad chains are history, not launch authority. |

During this task: no GPU queries or inference, process signals, container operations, flag access/change, live `results/larger-test/` access/change, check README edits, `src/` or `scripts/` edits, or `data/bench` access/change. No cleanup. The actual coordination flag is `/home/bmarti44/stencil-llm/results/quick-checks/larger-test/RUNNING.flag`; the misleading alternative is `/home/bmarti44/stencil-llm/results/larger-test/RUNNING.flag`. A missing flag is **not evidence of an idle GPU or completed experiment**. Do not run `git pull` before inspecting active work, tracked changes and pinned state; no pull is needed here.

The standing accuracy/code review rule is **Opus at maximum reasoning effort**, author-disjoint, writing only its review file. If effort is not a tool parameter, explicitly request maximum effort in the prompt. Fable is the documented overflow/unavailability fallback; record the substitution and reason in the review header. Brian explicitly selected Astra to audit its own program on 2026-09-07: that is a **self-auditor role override**, not independent review. This rewrite is likewise not the independent post-run acceptance review.

Work autonomously within authorization. Stop at missing authorization, contamination boundaries, failed eligibility and registered stop-loss. Three failures of the same bar park the line; a fix requires a new discriminating hypothesis and a prospective amendment, never an automatic re-pilot. Amendment 5 expressly authorizes no further DEV re-pilot. Preserve all seven pilots as development cost; neither a new title nor another repair resets failure history.

Capability is not permission: a PARTIAL classifier result does not authorize a runtime swap; a larger-test PASS does not satisfy the publish gate. Brian's explicit approval remains required for API spend, publication to `bmarti44/stencil`, and changes beyond the registered budget. Historical 54 GB dense-bf16 download and ~96% disk occupancy were 2026-09-06 planning facts, not current capacity measurements or download permission. Do not print credentials. No new download or spending is authorized by this handoff.

## State and next decisions (corrections 1, 6, 9, 10)

| Work | Recorded state; continuation |
|---|---|
| Check47 and CPU replay | Complete, STAY under the frozen conjunction. Original dense 0/32 execution was fence rejection; repaired dense/MoE both32/32. Saved-output replay is not corrected live trajectories; 30 later histories remain unmatched. Cost proxies24.15h/45.61h are not measured dense-bf16 SLAB-2 cost. |
| Check48 updater | COST-INELIGIBLE; no final adapter or heldout4 model evaluation. Fit/save projection22.32min, evaluation38.01min>22; no quality result or automatic refit. |
| Check49 | Registered NO-GO with defective conflict control: M/T SWITCH0/12 with cold cue qualification. Narrow causal JS SET survives (M12/12 vs swapped0/12); weight control remains open. Ten decision losses represent two episodes; M9/12 vsT10/12, paired1 win/2 losses,p=.5. |
| Check51 | CONTROL-PASS,8/8 on supplied histories across four families/two directions; not proof that placement solely caused49. Four evaluation-generator branches were exposed by a source read; exclude those families from a fresh successor confirmation lineage. |
| Check50 / check45 | No achieved check50 result. Check45 insufficient eligible data:128 calls from DEV00<150 required rounds; no fit, AUROC or intervention-benefit result. |
| Pilots1–4 | 1: INELIGIBLE/INCOMPLETE, envelope/parser defects. 2: parity STOP; saved-output recovery, not new trajectories. 3: INELIGIBLE,460/480, task/prompt and append defects. 4: INELIGIBLE,479/480, caps/overflow. Do not collapse these into one generic failure. |
| Pilots5–7 | All historically INELIGIBLE:5 malformed-lane repetition and old T floor;6 final/qualification failures and scorer/composition defects;7 invalid compact behavioral gate (block-free N also fails). CPU composition repair does not change their historical verdicts. |
| Larger test | Authorized frozen Amendment5 running; no outcome or progress inferred from this document. It is the next deliverable, not a queued launch. |
| Adoption pass | Built components and DEV evaluations are separated in [adoption status](astra-assessment-adoption.md). X is mock-only; intervention rerun is infrastructure. |

After the run, close evidence accounting and independent review first. Then repair synopsis/check headlines and the two controller bugs in a successor commit, preserving frozen bytes and historical scores. A fresh matched prose-vs-structured rendering comparison needs a prospective contract and clean lineage. The already authorized corrected49 successor remains behind composition work and needs real retained-history text-at-recency qualification, fresh families disjoint from51, and episode-level harms. Check50, dense switching, broad router/SAE searches, probe fitting and paid baselines remain parked unless separately justified and authorized.

## Frozen larger-test contract (correction 2)

Gold structured events; no fitted admission/updater, router bias or attention mask. Qwen3-30B-A3B bf16, one frozen backend. R=register rendering, N=ordinary retained history, T=oracle prose; R/N/T each64 episodes×16 rounds=1,024 rows per arm. Q=fresh-context gold-prerequisite reference on IDs00–15,16×16=256. **3,328 records total; O absent; no 12-round fallback.** Q is not a capability ceiling or same-history counterfactual.

Primary is `slab2_endpoint.primary`: schedule-only effective changes select the first applicable round before the next change, with no substitution of a later write. Measure common paired parsed writes; average common events within each episode using exact fractions; apply a one-sided exact sign test R>N. Holm correction spans delivery, format and indent at alpha .05. A family passes only with Holm p≤.05 and positive mean paired gain. Delivery alone supplies the overall evidence gate.

`slab2_endpoint.larger_reading()` returns PASS iff delivery passes, R any-breakage episodes minus N any-breakage episodes≤1, the CPU composition control passes, and every expected record is present exactly once. A complete run failing the conjunction is FAIL; unrun rounds/episodes, deadline/resource/error stops or pre-run determinism failure yield INCOMPLETE. Duplicate/unregistered keys hard-fail accounting. No partial PASS, dropped/replaced episodes or retries. Joint-final, Q-qualified subset, T floor, absolute breakage and compact-behavior are **not gates**. A missing registered cross-container receipt prevents an unqualified protocol-completion claim even though it is not an argument to `larger_reading`.

CPU control: reproduce all35 saved DEV compact-register hashes/versions; on all64 frozen schedules verify forward-state/event-log reconstruction hash identity and absence of both the delivery row and `trailer delivery=` from compact rendering. Preserve every hash and coverage. This verifies current-block SLAB composition only.

Frozen groups: increasing four-ID chunks00–03,…,60–63; within each chunk R,N,T, then Q only through chunk12–15. There are52 groups, IDs0–51, concurrency4 within each same-arm group, each lane sequential for16 rounds. After group27 (T28–31), replay exactly40 saved pilot7 R payloads: eight DEV IDs×rounds0,4,8,12,15. Compare full request hashes, response text, token IDs and finish reason; report divergent/40, eight per-episode rates and any-divergence episodes. No threshold or independent-cell inference. Before main inference, eight DEV R round0 prompts replay forward/reverse with exact token-body/EOS/cap equality; this is not a DEV trajectory re-pilot.

Projection `(497.4678113460541 + 1.25*(64*(106.95503854006529+96.3614319190383+89.96212818473577)+16*82.3344509229064))/3600` =7.112901h; adding1,200s replay/determinism/cleanup gives **7.446235h**. Cooperative GPU-held deadline41,400s=11.5h including startup/cleanup; hard ceiling43,200s=12h. Stop new groups with1,500s reserve, requests180s before deadline; each request bounded by1,200s and remaining time minus60s. Waiting is separate. These are the running owner's frozen controls, not instructions for this docs worker to intervene.

Pinned worktree: `/tmp/stencil-larger5-pinned`, freeze SHA `95fa7fc0c006518ef84c1ea20c152c079ae1798a`. Model-facing bytes match `24ed80a49edcea3359d0c45d361daf7fdf761745`. [freeze.json](larger-test/freeze.json) at the freeze SHA binds all source hashes,64 IDs/per-episode hashes, schedule and40 prior file/request hashes. ID SHA256=`245e6d1b5f2031ed2fa10b872f958519d299a72d1c58ca312031ae2ea4c9a691`; bank ID/hash map=`2e54d534f3f0a253084756e17ba85ff8b65091ff5cb1cf348c2a30971b11ef71`; existing bank manifest=`e8c365ede1398c0a8c458f2041d2fa195a82163a17e6732cd35821218da614ca`.

Image: `vllm/vllm-openai@sha256:3dbe092ec5b2cef63b6104d33fa75d6ce53a7870962529ada69f78bbbc38e776`. Frozen serving: BATCH_INVARIANT=1, TRITON_ATTN, prefix cache, bf16/auto KV, tensor parallel1, context32768, max sequences4, batched tokens2048, memory utilization.70, vllm generation config; cap2048, seed20260906, temperature0. The exact container command is frozen metadata, not a takeover launch instruction.

Only after the owner confirms completion and final receipts are finalized, read the final result on CPU (do not execute this during the protected run):

```bash
cat /home/bmarti44/stencil-llm/results/larger-test/RESULTS.md
python3 -m json.tool /home/bmarti44/stencil-llm/results/larger-test/summary.json
python3 -m json.tool /home/bmarti44/stencil-llm/results/larger-test/reproducibility.json
```

Missing files mean missing receipts, not permission to rerun the driver.

## WHAT IS PROVEN, at the measured scope (corrections 4–6)

The typed register and real rendering consumer support bounded explicit-state experiments. **Check42 is a reused-bank diagnostic, NOT CLOSED under its frozen no-exclusion rule**: A/C151/192 vs131/192, paired39/19; B excluded68/96 delayed episodes. This is not clean confirmatory cadence evidence. FOCUS-3 repaired v2 gate O61/64 versus C27,N25,T31/64 replaces the unversioned historical63/64 oracle shorthand; automatic lifecycle remains ineligible.

Check40i Z gives SWITCH24/24 Python, BACK23/24 JS and CLEAR24/24 Python on short arithmetic bodies, one Python/JS pair and one MoE trunk. Coarse checks are not program execution. It is not generic certified release. Check40j text-only and combined both16/16,0 wins/0 losses, descriptive gain CI[-23.96,+23.96]pp: no measured incremental gain, not equivalence or universal actuator redundancy. Check40k's tested alpha3 harms semantic success16/32→7/32,2 wins/11 losses,p=.022461;40l does not recover it. Steering families are parked by local evidence and budget, not mathematically closed. Extracted residual, KV, coordinate, neuron and concept-routing recipes31–33,41/41b,43/43b do not close whole dense-model or SAE intervention families; check34 establishes a live cue-column route. No default actuator/profile-library search is queued.

Backend qualification measured64/64 identical scheduled B1/B1-repeat/C4 outputs within a container. HF differs5/64 scheduled rows, equivalently **4/48 distinct prompts**. Pilot6/7 matched requests have **156/166 cross-container identity** (N differs4/95,T6/71); R/Q have no matched sample in that166. This is not R-trajectory reproducibility. Same-container replay measures local byte stability; CPU score replay measures scoring of saved responses; new-generation replication needs new inference and can differ. The registered40-payload control measures cross-container response identity without rerunning trajectories. Preserve raw evidence; a seed/image hash does not regenerate historical answers.

The HF package is a scaffold. Tiny CPU custom_generate dispatch and159+ historical test counts are integration evidence, not full-model validation, packaged assets or measured HF/vLLM equivalence. Explicit authenticated structured entry remains the usable boundary; classifiers are assistive.

Automatic admission44/44b/44c is NO-GO. Check46 is **six-shot in-context**, not zero-shot: overlap recall78.96%,precision89.94%,relations89.06%; task-over-global0/21,SETUP58/96 false turns. **69 missed gold spans occur in62 empty-list messages** (59/69 late); **22 false spans comprise19 request admissions and3 duplicate fragments**. Post-hoc93.3% precision is diagnostic surgery, not prospective rescue. Single-rule target IDs285/285 do not measure multi-target updating. Relations v3 is NO-GO; “harder bank” is supported by a reported frozen-v2 bank3 diagnostic, while an unqualified “no regression” needs its scratchpad-only paired receipts preserved.

## Exposure table and successor lineage (correction 7)

No evaluation episode content was opened for this rewrite. Entries below report documented historical exposure, not a new content audit. “Not documented” is not proof of no exposure. Bank names expand to `data/classifier/heldout/fable-{admission,relations}-heldout{,-2,-3,-4}.jsonl`. Admission counts are messages/spans; relations counts are rows. Fable author separation is not semantic independence.

| Bank | Authors | Metadata reads | Content / audit reads | Model looks | Error-driven development use | Allowed future role |
|---|---|---|---|---|---|---|
| Admission1:338/218 | Fable | Historical summaries; Astra audit summary-only | Evaluation/review exposure | Historical admission/B/check44 evaluation | Subsequent admission development; precise feedback inventory incomplete | Exposed diagnostic; no fresh confirmation |
| Admission2:330/207 | Fable | Historical summaries; Astra audit summary-only | Evaluation/review exposure | 44b;44c secondary second look | Error-informed token admission development | Exposed diagnostic; no fresh confirmation |
| Admission3:357/385 | Fable | Historical summaries; Astra audit summary-only | 44c/46 error audits; pass3 annotation comparison | 44c,46 | Error-family diagnosis and pass3 training-span conventions | Development/diagnostic only |
| Admission4:320/349 | Fable | Historical summaries; Astra audit summary-only | Pass3 audit used heldout3/4 annotation conventions | **No check48 model evaluation** | Pass3 framing/punctuation/scope repairs fed48 preparation | Retire as pristine confirmation for that recipe; disclosed diagnostic only |
| Relations1:594 | Fable | Historical summaries; Astra audit summary-only | Evaluation/review exposure | Original CPU checkpoint (0 positive coverage) | Subsequent operating-policy/development feedback | Exposed diagnostic; no fresh confirmation |
| Relations2:357 | Fable | Historical summaries; Astra audit summary-only | Evaluations/error analysis | GPU seed0,v2;v3 second look |90 Astra2 evaluation-derived relatives;v2 seed0 DEV includes all90,seeds1/2 fit30 each | Exposed diagnostic; relatives quarantined from future clean fits |
| Relations3:448 | Fable | Historical summaries; Astra audit summary-only | v3/46 audits;pass3 conventions | v3,46;reported frozen-v2 replay | Subsequent error analysis and training-preparation feedback | Exposed diagnostic; preserve existing v2 receipts before comparison claims |
| Relations4:320 | Fable | Historical summaries; Astra audit summary-only | Heldout3/4 pass3 comparison; fine-grained per-bank access census incomplete | **No check48 model evaluation** | Training preparation received pass3 feedback; cannot assert no contact | Retire as pristine confirmation for prepared recipe |
| SLAB DEV:8 episodes | Astra/program-generated authored schedules | Many development reads | Pilots1–7 and reviews | Repeated model looks | Repeated harness, scorer and renderer repairs | Development and frozen replay only; never independent confirmation |
| SLAB eval:64 episodes | Frozen program-generated authored schedules | Pre-freeze IDs/hashes/manifest only per registration | Running owner's one-shot instantiation; no content read in this rewrite | Registered running R/N/T64,Q16; outcome unassessed | No outcome feedback licensed | Finish frozen evaluation once; retire after exposure; tags do not establish withheld families |
| Check49/51 generator families | Astra-authored code;51 histories CPU-authored | Setup/source reads |51 source-range overrun exposed four evaluation branches |49 lifecycle;51 eight supplied-history controls | Control diagnosis and exposed branch knowledge | Exclude all four51-exposed families from fresh successor confirmation |

Quarantine **all90** rows in `data/classifier/relations/astra-enrich-2.jsonl` and their evaluation-derived relatives from future clean fit, calibration, prompt/example selection and recipe development. Check48 already excluded the90, but that does not undo heldout4 annotation feedback. Preserve contaminated lineage as disclosed history; do not delete/relabel it. Pass3 removed94 framing cues,changed13 scope labels and prescribed punctuation cleanup. Missing scenario IDs (1,234 override rows;1,097 inconsistent transition rows) limit sibling separation; grouping proxies, exact deduplication, new domains and different authors do not prove paraphrase separation. Write fit-on/development-on/evaluated-on lineage before any new freeze. No benchmark data or recorded responses may guide fitting, selection or tuning.

## Current implementation limitations (correction 11)

Source line references are those verified in [audit H1/H2/M1/M2](full-program-review-astra.md), not promises that this rewrite fixes code.

| Limitation | Source and consequence |
|---|---|
| Generic delivery omission | `src/stencil/focus/renderer.py:76–89`: any format=compact suppresses delivery even for unrelated email obligations. SLAB-specific composition is hardcoded into a generic key interface. Requires a successor declared policy. |
| Journal commit boundary | `loop.py:395–408,438`; `journal.py:67–78`: session/history advance before append/checker; append failure can leave generation1 and journal cursor0. No fsync/hash chain; propagation is not rollback or crash durability. Hook restoration can also fail after commit. |
| Transport-trusted authority/evidence | `register.py:307,364,412`; `loop.py:107,125,232`; `scripts/composition_pilot5.py:131`: trusted role/origin/adopted/receipt membership supplied externally; scheduled gold completion is not independently verified model task completion. |
| Exact-scope relation translation | `register.py:338`; `data/classifier/LABELS-RELATIONS.md:23`: global→task intersection supersedes labels do not directly map to legal exact-scope transitions; narrower override needs a separate add. No demonstrated complete-operation translator. |
| Stale rendered history | `loop.py:349,363`: prior rendered blocks and model answers persist. Current composition does not remove old imperatives. |
| No implemented actuator or packaged assets | `models/stencil-package/README.md:3,57,86`; `custom_generate/generate.py:5`; `MANIFEST.json:3`: scaffold imports installed stencil.focus, hashes null, no bundled trunk/classifiers/controller/working actuator. |
| No multi-target updater measurement | Check46 single target r1,285/285; audit Section1/check46 and `results/quick-checks/check46/README.md:66,72`. Span/relation accuracy does not certify runtime state mutation. |
| Endpoint limits | `slab2_endpoint.py:79–103,279–307`; `slab2.py:637,710–714`: primary requires parsed writes, not semantic success; registered final diagnostic omits wrong_family/breakage terms used by older checker. Report a separate strict sensitivity; do not change frozen scores. |
| Proposal string recognition | `loop.py:367–370` recognizes four literal done strings as proposals only. “No string matching anywhere” overstates the rule; proposals never authorize completion. |

## Portability and recovery (correction 14)

Git alone cannot reproduce this program's historical artifacts. The pinned source is reconstructible from its commit; exact historical generated replies and learned weights are only verifiable against preserved bytes. Retraining/regenerating creates a new artifact, not recovery. Do not resurrect scratchpad chains, GO files or completed jobs. A missing scratchpad is a preservation problem, never a reason to relaunch pilots or the sealed run.

Required local serving assets are `models/qwen3-30b-a3b-hf/` (trunk shards, tokenizer, config/index), the pinned image, and frozen source. Original pilot7 HTTP payload files named in freeze.json are also indispensable for the40-control historical comparison. Metadata hashes alone are not full weight hashes. The inventory below combines existing manifests with CPU-only byte hashes of local weights and historical receipts; **live larger-test journal sizes/hashes remain unassessed until completion**. No current-run preservation or cleanup is performed here.

| Artifact | Tracking / size / SHA256 receipt | Recovery meaning |
|---|---|---|
| Frozen source and bank manifest | Git commit95fa7fc0; source hashes below and freeze.json; bank hash above | Source bytes reconstructible from Git. Do not instantiate evaluation schedules during takeover. |
| Pinned vLLM image | Digest above; local image size not queried under container prohibition | Can request the digest from registry if retained and separately authorized; tag alone is insufficient. |
| Qwen3-30B-A3B shards | Untracked;16 shards,61,066,575,648 bytes (filesystem size metadata,2026-09-07). Full current shard SHA256s measured on CPU at idle I/O priority are listed below; no pre-run full-shard comparison receipt was available | Preserve these local bytes. Download matching bytes only with authorization. Current hashes verify copies; absence of a historical full-shard comparison remains a serving-provenance gap. |
| Model metadata | `quick-checks/vllm-qual/model-metadata-hashes.json`: config `2850ddb3bf7aecad20b611e2d44f3077fc8193f4827c93beddd4c02ad63c2297`; tokenizer `aeb13307a71acd8fe81861d94ad54ab689df773318809eed3cbe794b4492dae4`; shard index `df0d481ec595c55a0ba58426d517390c6214a566ec4ff1c8fc4bbce9f57b3c24` | Verify these files against receipt; index hash is not a shard-content hash. |
| Pilot6 local journals/workspaces/HTTP | Local untracked/ignored bodies; `quick-checks/composition-pilot-6/local-hashes.json`,1,200 manifest entries,101,902,655 bytes | Per-file bytes/SHA256 in linked manifest; preserve raw responses for exact score replay. Workspaces can be reconstructed from saved writes, replies cannot be reconstructed from hashes. |
| Pilot7 local journals/workspaces/HTTP | Local untracked/ignored bodies; `quick-checks/composition-pilot-7/local-hashes.json`,1,040 entries,64,770,493 bytes | Same distinction;40 original replay file/request hashes additionally bound by frozen larger-test manifest. |
| Check49 JS adapter | Untracked `data/classifier/model/focus-lora-4b/js/adapter_model.safetensors`,5,917,336 bytes,SHA256 `229858707ab48a55589786f55773be961f3b53146cb8c3949ed89109da23fc12` | Verify saved bytes; refit is new work, not recovery. Config/tokenizer/base dependencies also required. |
| Check49 Python adapter | Untracked corresponding `python/adapter_model.safetensors`,5,917,336 bytes,SHA256 `56f352c50c0473035df9603dc981f72f2aa856ece26de14f1a42cc892ce8e4f7` | Full side-file sizes/hashes in `quick-checks/check49/adapter-manifest.json`. Both adapters≈11.30MiB; not packaged. |
| Relations encoder | Untracked `data/classifier/model/relations/encoder/model.safetensors`,133,462,128 bytes,SHA256 `eab36a23614aab3945ab7b24bee9f918158ece4ac49a3041c2a5e74395c0c214` from `data/classifier/model/relations/manifest.json` | Preserve with head, operating point and tokenizer. Manifest permits checking copies; no guarantee retraining restores bytes. |
| Other classifier weights | Untracked admission-v2 seeds0–2 encoder/head;ft-v3 seeds0–2 encoders;relations-seed1/2;relations-v3 seeds0–2 encoder/head (per-file byte/hash inventory below) | Local assets, not evidence of a one-download release; existing manifests where available must accompany copies. |
| Frozen-v2 bank3 diagnostic | Scratchpad-only exact prediction receipts; existing files located and byte-hashed in this rewrite (inventory below); review reports87.95% and126/172 | Preserve these existing files after the run. Byte hashing is not a new paired score audit; retain attribution and narrow “no regression” until independent verification. Never regenerate and call it the old receipt. |
| V1 composition memo | Untracked `results/focus-mechanism-composition-astra.md`; size/hash below | Historical superseded design; snapshot can be preserved later, not authority for new launches. |
| Live larger-test raw/loop/HTTP journals and restart control | Outside Git by registration; current size/hash intentionally unassessed. Final `local-hashes.json` receipt required after completion | Preserve originals and accessible storage location. Hashes alone only verify; they cannot recover missing outputs. |
| Package MANIFEST | Null asset hashes; scaffold | Build and test a complete distributable separately; Git clone is not the intended product yet. |

Frozen source SHA256s (from committed freeze metadata):

| Source | SHA256 |
|---|---|
| `src/stencil/focus/slab2.py` | `b5c930e7c109520d4bc9d8c11b9255727bc99f2b86ee8e95c215283984524068` |
| `src/stencil/focus/renderer.py` | `e1ec3da2f3cd1565746e2b11c24308330b1f8c4d76dfe15f70bf5fa2dc2996be` |
| `src/stencil/focus/loop.py` | `892791a22e90174e7d22c5a82a172e7ecafb900e23f4fd83ff3de439782079ab` |
| `src/stencil/focus/register.py` | `7e7da909ec59327408b180a854b4a8e222846b9b7935b681402ca6b092cb3732` |
| `src/stencil/focus/slab.py` | `3f3a9f04ee9bae3395c3fdf5d3011e2b8cca4b930332a72dd2edafce7de04b59` |
| `src/stencil/focus/slab_sandbox.py` | `3dad55e31b23fd859a9fcf805b3694acc99c8efdb48c35ed82ca78b16f9d7de8` |
| `src/stencil/focus/journal.py` | `217d6ce770b8e9f3c374bb6bea8157823e1e335db8d169be54b4bde043a24b4f` |
| `src/stencil/focus/slab2_endpoint.py` | `95dfa314f21afaea09bb449b3720d37f8a4fc8b018c322779cbc82a22a92d2ec` |
| `scripts/composition_pilot5.py` | `25fee357597b4240c731a120d5b7dfcc6a568c62aadeafca91322c37738aee9c` |
| `scripts/composition_pilot7.py` | `f58ed6e0521fb513515979fe1c140081b02ea9dafba4611ee01b9141a32d8440` |
| `scripts/larger_test.py` | `bedb16d619aaf1194734c1e81b82f758b662b8393396236ef75573d883c567e1` |

Historical design byte receipt:

| File | Bytes | SHA256 |
|---|---|---|
| `results/focus-mechanism-composition-astra.md` | 35,719 | `79b22b84af5fc03721afd12f30e21576783c3a82e4c2083e3e9593da498891af` |

Frozen `freeze.json` Git-object bytes: SHA256 `0b4fda055c40b617d463e3d73b8dd6839649f8def7a5246620d85c2167ec8a88`. No live run artifact was read to obtain this.

## Post-run acceptance, in order (correction 15)

1. Obtain the running owner's completion/cleanup evidence; preserve pinned SHA, source/image/model identity and original local receipts. Absence of a flag or an aggregate file is insufficient. Do not pull, relaunch, signal or remove anything as a recovery shortcut.
2. Read finalized RESULTS.md/summary.json using the CPU commands above. Audit exactly64 unique registered episode IDs and3,328 unique `(episode_id,arm,turn)` keys: R/N/T each1,024,Q256 only IDs00–15, turns0–15. Check frozen episode hashes; reject duplicate, unexpected and missing keys. Reconcile all52 groups and incomplete-stop reasons. Preserve per-round records before trusting aggregates.
3. CPU-replay saved raw/HTTP responses through the frozen scorer and real consumer semantics; compare output/token/text hashes and per-record scores without new generation. Verify35 DEV composition hashes and all64 forward/reconstruction coverage. Recompute `larger_reading` from frozen source in an isolated audit context; never invoke the experiment driver's main entrypoint as a reader.
4. For each of delivery/format/indent report scheduled change opportunities, first applicable round, common parsed-write events, eligible episodes, within-episode denominators, exact mean gains and win/loss/tie counts. Recompute one-sided sign p-values and Holm across all three. Report all family directions, including negative ones; never treat rounds as independent trials.
5. Recompute missing-write-as-failure sensitivity on the scheduled opportunities, with no later-write substitution. Publish conditional missingness and any direction/evidence change prominently. Apply the registered gate unchanged; sensitivity is additional disclosure, not a retroactive replacement gate.
6. Report absolute any-breakage counts for R and N and their difference≤1; report all arms' semantic/integration, report/path/task and final diagnostics. Preserve the registered joint-final diagnostic; add a clearly separate strict sensitivity including wrong_family and breakage. PASS may coexist with poor executable success or high shared breakage.
7. Account for40/40 cross-container comparisons at the frozen payload keys and insertion point, with request hashes, text/token/finish comparisons, divergence fraction and eight episode rates/any-divergence count. Separately verify the pre-run forward/reverse determinism receipt. Missing40-control records are an execution-protocol failure even if mechanical PASS exists; no retrospective second attempt.
8. Reconcile measured startup, inference, replay, cleanup, GPU-held time and separate wait time against projection7.446235h,deadline11.5h and ceiling12h. Keep costs for pilots1–7 visible as development cost. Review the owner's cleanup receipt without claiming this docs worker performed it.
9. Preserve per-arm≤10MB records, episode tables, summary, CPU/control/replay audits, cost/server receipts and RESULTS.md; archive oversized journals outside Git with per-file bytes/SHA256 and retrievable location. Verify the committed copies with `git ls-files`; use `git add -f` and explicit commit pathspecs after authorization permits these run artifacts. Resolve portability gaps without inventing historical bytes.
10. Obtain an independent Opus maximum-effort accuracy review (documented fable fallback only), reconcile findings and report PASS/FAIL/INCOMPLETE plus any protocol incompleteness. Then correct deferred public headlines at their point of use. A PASS supports bounded request-time effective-state restatement on one authored Python distribution, conditional on parsed writes and relative breakage. It does not identify register superiority over prose, final executable improvement, safety, clean history, automatic updating, neuroscience, universal skill selection or deterministic regeneration. Publication requires its separate gate and Brian's approval.

No step authorizes changing the frozen result or launching a successor automatically.

## Local weight byte receipts — 2026-09-07

CPU SHA256 of local files, read at idle I/O priority without model loading, GPU or container access. These verify current local bytes; no pre-run full-shard hash comparison was available, so they do not independently certify historical serving identity. Preserve these exact bytes for recovery; retraining is not recovery.

| File | Bytes | SHA256 |
|---|---|---|
| `models/qwen3-30b-a3b-hf/model-00001-of-00016.safetensors` | 3,999,417,504 | `454e77b346a61bfb201d54df60e15158838cf930617ee135113556204f2802b5` |
| `models/qwen3-30b-a3b-hf/model-00002-of-00016.safetensors` | 3,999,974,192 | `47f015d6e5bb1782a834d75c06113c5e8c77ddca1cb7daf89686a4ec0deda19e` |
| `models/qwen3-30b-a3b-hf/model-00003-of-00016.safetensors` | 3,997,360,832 | `ac0bf5990f2da995c1e8b77a3149dee71900b4fe1b8a614231dea9647193d96b` |
| `models/qwen3-30b-a3b-hf/model-00004-of-00016.safetensors` | 3,999,975,056 | `89b01fd34a683c70fdb7f22c2e7090538d65063335ba0db46f3654642b17d1e5` |
| `models/qwen3-30b-a3b-hf/model-00005-of-00016.safetensors` | 3,999,975,400 | `9849eb3584d928e35bf5956ccfd91b64207467e1fad8304aae68dc4d92d6d6d9` |
| `models/qwen3-30b-a3b-hf/model-00006-of-00016.safetensors` | 3,999,975,400 | `f7a0f1525557d740158fb692986ad43506e1b5901e7406ae65808c6457bc53ad` |
| `models/qwen3-30b-a3b-hf/model-00007-of-00016.safetensors` | 3,999,975,472 | `920702a50f27a009e5f676da3b02978dbd794f6ad7854f301d709136154c1a84` |
| `models/qwen3-30b-a3b-hf/model-00008-of-00016.safetensors` | 3,997,362,064 | `a85bf0cc8a8047c116172d4c08cf4792eb59d4375032708ba3e1a7ffca0f708a` |
| `models/qwen3-30b-a3b-hf/model-00009-of-00016.safetensors` | 3,999,975,408 | `25cd8aaed86b8e17685efb152912f92448ea3fffb1bdc247f257f04d05907604` |
| `models/qwen3-30b-a3b-hf/model-00010-of-00016.safetensors` | 3,999,975,400 | `7c3307ee214797c4bc61c0994f81d690e768150df5f14d18edf84e53ba4810dc` |
| `models/qwen3-30b-a3b-hf/model-00011-of-00016.safetensors` | 3,999,975,408 | `c658cad2842d36fa4c7c7f726f8515dc5670a3d80c94e13257d4e322ffe61988` |
| `models/qwen3-30b-a3b-hf/model-00012-of-00016.safetensors` | 3,987,400,496 | `8cb898bc5e78492600053d1105c9ff61d7a719f5cc2802df63e41535a652cc26` |
| `models/qwen3-30b-a3b-hf/model-00013-of-00016.safetensors` | 3,997,353,632 | `599594421f314cb8e8ab4474db0eb490cc6310585067e82d73821254b93319ce` |
| `models/qwen3-30b-a3b-hf/model-00014-of-00016.safetensors` | 3,999,975,400 | `66d3294e9976b5f01d117a0a0bed768f128a8898eb6937e224d051de2961d363` |
| `models/qwen3-30b-a3b-hf/model-00015-of-00016.safetensors` | 3,999,975,400 | `2fe000da4fc7399ff6303bb0daec8c415a5d850f5ea53863392758c77fc37664` |
| `models/qwen3-30b-a3b-hf/model-00016-of-00016.safetensors` | 1,087,928,584 | `0c979e314faf06e94a5e1841abd285d4e26e763c79c1abe7710d543192d9da48` |
| `data/classifier/model/admission-v2/seed0/encoder/model.safetensors` | 133,462,128 | `3690e2123c7fe3796fb851c25df695d3b81d06dd9564274161e74588fd06144f` |
| `data/classifier/model/admission-v2/seed0/head.safetensors` | 4,756 | `a5a34ce501da7c70e378a65942e5d4b37f647ef18fe05ffc24af2d2417bf935d` |
| `data/classifier/model/admission-v2/seed1/encoder/model.safetensors` | 133,462,128 | `6d553669e2c7b772761724abe7f5883f58f5d8afd5ae587512494496e08c3e43` |
| `data/classifier/model/admission-v2/seed1/head.safetensors` | 4,756 | `97e87542a9f6913690d16b14e622474433ebaa2ddaaeb31b048a9ae1aab3f910` |
| `data/classifier/model/admission-v2/seed2/encoder/model.safetensors` | 133,462,128 | `e72858e22ba3a2a95eb233a51d9b3b3a183b0f33ac0021f85935dc532a191fa9` |
| `data/classifier/model/admission-v2/seed2/head.safetensors` | 4,756 | `e85ca47d3f38cbf67e858f918b74bba861d907e27e7401b0e589ddd08dd75805` |
| `data/classifier/model/focus-lora-4b/js/adapter_model.safetensors` | 5,917,336 | `229858707ab48a55589786f55773be961f3b53146cb8c3949ed89109da23fc12` |
| `data/classifier/model/focus-lora-4b/python/adapter_model.safetensors` | 5,917,336 | `56f352c50c0473035df9603dc981f72f2aa856ece26de14f1a42cc892ce8e4f7` |
| `data/classifier/model/ft-v3/seed0/encoder/model.safetensors` | 133,462,128 | `980080c5286dc826897f72164afc35a509c4b68635ca051b348c39bf4522bf0e` |
| `data/classifier/model/ft-v3/seed1/encoder/model.safetensors` | 133,462,128 | `9e13281dff9445fec3fd430d2a20d08c9158fa327847f47b73a722be457768fb` |
| `data/classifier/model/ft-v3/seed2/encoder/model.safetensors` | 133,462,128 | `3a1aebd0fcd2383d6ab5396e614c2f916e48c3e5013cad0c87cec9cd6b250871` |
| `data/classifier/model/relations-seed1/head.safetensors` | 7,916 | `e37aa70155e9c17091802d626bae6d607c6d53eeabfa3dcc9e669c24f6571fb4` |
| `data/classifier/model/relations-seed2/head.safetensors` | 7,916 | `665944699b923e01588d539bf2711950f9f459ae6090781d0be779eb5a80c646` |
| `data/classifier/model/relations-v3/seed0/encoder/model.safetensors` | 133,462,128 | `f6200e807b422443b4740e4f93de6520b3043418fb968797403a95ca848c59a0` |
| `data/classifier/model/relations-v3/seed0/head.safetensors` | 7,916 | `8b1020090d2b6147244ccc38a3fd7d0d5d28cf68298df060bd88e077a0e46958` |
| `data/classifier/model/relations-v3/seed1/encoder/model.safetensors` | 133,462,128 | `f9c039432abbf2400cb8956007cc8dbc0bf50bb50760e918e30db34f5cdd4067` |
| `data/classifier/model/relations-v3/seed1/head.safetensors` | 7,916 | `b210b72df22788284456ee06c34d9b4bdb0c604efa0fae5333b23e7996aa4c00` |
| `data/classifier/model/relations-v3/seed2/encoder/model.safetensors` | 133,462,128 | `fbd2d74641e1be1bfd4de3d6cfbfbd69b84fa8a3a5685f47980b12e386823a00` |
| `data/classifier/model/relations-v3/seed2/head.safetensors` | 7,916 | `f59c4e9f1dacdef08e55d41aac3396b4c2f4db459d42214c4155768a119d849c` |

Existing scratchpad diagnostic byte receipts, located without parsing examples or executing the diagnostic. Parent directory is `/tmp/claude-1000/-home-bmarti44-stencil-llm/a88136df-3902-46b9-a661-86e0dc1bb53f/scratchpad/`. These files remain uncommitted; this docs task records their identity, not a completed portability repair.

| File under that scratchpad | Bytes | SHA256 |
|---|---|---|
| `v2-heldout3-records.jsonl` | 568,275 | `d587b4d40f5d0886acfaa1bde5208351cfb0b056c28b28b79f81c01f3223fd0b` |
| `v2-heldout3-metrics.json` | 1,943 | `46586e44a402a65c7ab1e1459b05d4ca523e08c040530ec0356a527ca8ab5297` |
| `v2_diag.py` | 3,070 | `5f3054862928df55d9ba226481dc151ae628b36d407a981d7ea3d9d8863f12a6` |
