# Stencil handoff — verified 2026-09-07

## Cold start: the first ten minutes

1. Minutes 0–2: read this section and the evening state below. Work at the repository root. Inspect changes and locks before editing; do not pull over local work.
2. Minutes 2–5: read the verdict tables and review addenda in the finalized [first result](larger-test/RESULTS.md) and [second result including its review addendum](larger-test-v2/RESULTS.md). Both runs are frozen and unrescorable. The adequate-proof gate is NOT met.
3. Minutes 5–8: read the current-state and successor sections of [NEXT-TESTS-PLAN](NEXT-TESTS-PLAN.md), the current-state paragraph of [claims corrections](CLAIMS-CORRECTIONS.md), then the [kit recovery instructions](handoff/README.md). For rationale, read the [full-program audit](full-program-review-astra.md) and [successor review](larger-test-v2-review-astra.md).
4. Minutes 8–10: inspect current ownership and resource use with the read-only commands below. A flag-free directory alone does not establish an idle GPU. A busy GPU, active experiment, held review lock, unexplained PID or container means coordinate with its owner before a launch. Do not signal or clean up somebody else's work.

```bash
cd /home/bmarti44/stencil-llm
git status --short
git log -5 --oneline
lslocks --output COMMAND,PID,PATH
find /home/bmarti44/stencil-llm/results -type f -name RUNNING.flag -print
ps -eo pid,ppid,lstart,comm
cat /home/bmarti44/stencil-llm/.stencil-owned-pids
docker ps --format '{{.ID}} {{.Names}} {{.Image}} {{.Status}}'
# Read-only GPU status, for the incoming engineer; no model load or inference:
nvidia-smi --query-gpu=index,name,memory.used,memory.total,utilization.gpu --format=csv
nvidia-smi --query-compute-apps=pid,process_name,used_memory --format=csv
```

Never (1) fit, tune or select on any evaluation benchmark or recorded responses to it;
(2) rescore either frozen larger run, even on CPU; (3) start a GPU job while any other
RUNNING.flag exists. Flags are runtime files that may be absent, not missing kit artifacts.
Check all result subdirectories, not just the historical quick-check directory.
The GPU query commands above are instructions for takeover; this docs verification did not run them.

## STATE AT 2026-09-07 EVENING

Both larger runs are complete, frozen and unrescorable. This replaces all earlier RUNNING/queued-launch and post-run-rescoring instructions.

| Run | Frozen identity | Recorded outcome |
|---|---|---|
| [Amendment 5](larger-test/REGISTRATION.md) | `95fa7fc0c006518ef84c1ea20c152c079ae1798a` | **FAIL**. Delivery 40/0/24 wins/losses/ties, raw p=9.09494702e-13, Holm p=2.72848411e-12; R breakage 20 versus N 14 violates the registered excess≤1 clause. |
| [Amendment 6b](larger-test-v2/REGISTRATION.md) | `e20c3f9bb9979ba95b9cc797115b742507a3803c` | **PASS, NARROW**. Delivery 35/0/28, Holm p=8.73114914e-11; format 25/4/34, Holm p=0.000103715807; indent 17/15/32, mean gain zero, p=0.430025033. |

Both summaries record 3,328 scheduled rows: R/N/T each 64×16=1,024; Q 16×16=256.
R is the rendered register, N retained history, T oracle prose, Q fresh context with gold prerequisites.
The primary uses scheduled first-applicable changes, common parsed writes, within-episode averaging and one-sided exact R>N sign tests with Holm across three families. Delivery powers the primary gate. Q is not a same-history counterfactual.
Sources: [first summary](larger-test/summary.json), [second summary](larger-test-v2/summary.json).

In run 1, every non-write was an indentation SyntaxError (R 48, T 51, N 2, as documented in the finalized first-result addendum). Acting on restated style rules in whole-file re-emission caused the failure family; prose paid it too. Run 2 changed to scoped-function submission and allowed one syntax-repair response. Its R broken-episode count is 1 versus N/T 0. The apparent 20→1 reduction crosses **different banks, protocols and breakage definitions**, so it is not an isolated causal estimate of a fix. All five repairs in run 2 repeated the invalid submission; the observed repair success is 0/5, clustered in one episode.

**The gate for “adequate proof on a larger implementation” is NOT met.** In run 2, T matches or beats R on every primary family and on overall format adherence. This is the reviews’ bounded comparative reading, not an equivalence test: delivery has one R win, no T wins and 62 ties; format and indent favor T. Correct prose therefore leaves no demonstrated superiority for the register representation. Final semantic integration is R 45/64, N 48/64, T 52/64, Q 16/16. R loses seven paired integrations to T with no wins: one-sided p=0.0078125 (two-sided 0.015625). Nonsignificant conditional syntax harm is not competence preservation.

The powered delivery target matches the system example's literal value; 98.63% of turn-level tasks recur from the spent bank. The supported claim is bounded request-time restatement of effective obligations, either register or prose, recovering one silent-default transition on an authored Python distribution. It does not establish general coding competence, representation superiority, removed stale influence, working self-repair, automatic admission or safe autonomous operation. Both reviews and the result addendum qualify the PASS; Astra is a self-audit, not a second author-disjoint review.

Reviews: [first Opus](larger-test-review-opus.md), [first Astra](larger-test-review-astra.md), [second Opus](larger-test-v2-review-opus.md), [second Astra](larger-test-v2-review-astra.md). Existing review calculations are cited; no scorer, driver, model or executable evaluation was run for this handoff.

## Agreed successor and open problems

The agreed successor is a **fresh 32-episode paired factorial**, 16 rounds, crossing whole-file versus scoped submission with N/R/composed-prose T: 32×16×2×3=3,072 scheduled calls, **about 5.32 GPU-h**. Primary outcomes are per-episode paired private-test integration and joint integration-plus-adherence. Hold file visibility, repair policy, feedback and effective prose/register content constant across scope cells; counterbalance delivery targets and initial switches/reinstatements. Freeze a new bank with new semantic parameterizations before any model look.

Cost is an extrapolation: half of (22,360.7679+6,341.9631) lane-group seconds = 14,351.3655 seconds; ×1.25 reserve +1,200 seconds overhead = 5.31645 hours. Proposed cooperative ceiling: 6 hours. This is a discriminating screen, not a noninferiority or safety certificate. The bank, registration, implementation and setup timing remain unfinished; this handoff authorizes no launch. Source: [successor design and cost](larger-test-v2-review-astra.md).

All six open problems have reports and costed proposed tests, indexed with dependencies in [NEXT-TESTS-PLAN](NEXT-TESTS-PLAN.md): admission, context cost, off-task detection, co-emitting self-management, compliance versus competence, and DIRECTER paper/code reproduction. These are alternatives, not an automatic queue. The existing [reserved admission bank](../data/classifier/heldout/clean-admission-bank-v1.jsonl) is for admission screens, not the coding factorial. Its existence/tracking is verified; pristine exposure history and adequacy for a selected screen are not independently certified here. Do not open its examples during preparation.

## Concurrent update observed during verification

After the evening agreement above, another session appended an **AUTOMATED MAINTENANCE PREPARATION; NO GPU LAUNCH** entry to [the shared ledger](../plan/LEDGER.md). It records a newer Brian correction: matching good manual prose through automatic register maintenance can count as benefit, and the factorial is deferred as a protocol diagnostic. It also records Kimi data preparation, Sol implementation and Astra review roles for that session. The tracked [CURRENT-GOAL](CURRENT-GOAL.md) still states the earlier representation-superiority gate at this inspection, so those two surfaces conflict. The underlying user conversation is not available to this verifier; the concurrent entry is reported, not independently authenticated or treated as this task’s launch authority. The next owner must reconcile this newer direction before choosing work. Neither entry changes the frozen FAIL/PASS or establishes adequate larger-implementation proof. The shared ledger remains outside this docs commit to preserve the other session’s work.

## Authority and unfinished implementation

Brian’s current instruction governs this CPU/docs verification and explicit-path local commit, with no push. [AGENTS](../AGENTS.md) supplies standing lessons. Its old root science/process links have moved to [archived PLAN](../archive/PLAN.md) and [archived PROTOCOL](../archive/plan/PROTOCOL.md). [LEDGER](../plan/LEDGER.md) tracks the classifier line (top STATE: check44c COMPLETE/NO-GO); it is not the overall program state. Historical fixed reviewer models and old queues do not override current instructions. Accuracy/code reviews use author-disjoint Opus at maximum reasoning effort; record any unavailability substitution in the review header. Publication, paid API work and budget changes require Brian’s separate approval.

The [claims table](CLAIMS-CORRECTIONS.md) retains the historical evidence and correction backlog. The [adoption table](astra-assessment-adoption.md) separates built infrastructure from evaluations. Specific unfinished work:

- Generic rendering still suppresses the delivery key whenever format is compact, including unrelated obligations: [renderer](../src/stencil/focus/renderer.py). A declared scope-specific policy remains to implement.
- Session/history advances before journal append; append failure has no full transaction rollback: [loop](../src/stencil/focus/loop.py), [journal](../src/stencil/focus/journal.py). Durable failure semantics remain to specify and test.
- Authority and completion evidence are externally trusted, not free-text authentication. Exact-scope register transitions need translation from classifier scope-intersection labels: [register](../src/stencil/focus/register.py), [relation labels](../data/classifier/LABELS-RELATIONS.md). Multi-target automatic updating is unproven.
- The [package README](../models/stencil-package/README.md) and [manifest](../models/stencil-package/MANIFEST.json) describe a scaffold with null asset hashes. Full-model packaging, implemented actuator and end-to-end runtime qualification remain unfinished; prior rendered history also persists.
- Check47/replay is complete; check48 is COST-INELIGIBLE with no final adapter; check49 is NO-GO with defective conflict control; check51 is a supplied-history CONTROL-PASS with exposed families. Check50 has no achieved result; check45 lacks eligible data. Do not revive these via old chains. See [47](quick-checks/check47/README.md), [48](quick-checks/check48/README.md), [49](quick-checks/check49/README.md), [51](quick-checks/check51/README.md), [45](quick-checks/check45/README.md).
- Historical pilots remain development evidence with their recorded verdicts; newer scoped pilots do not erase earlier failures or costs. All 90 evaluation-derived enrichment rows and relatives remain quarantined from clean fitting/selection: [lineage audit](full-program-review-astra.md), [enrichment file](../data/classifier/relations/astra-enrich-2.jsonl). Heldout sets 1–4 are exposed or development-informed; author separation alone does not certify independence.

## Serving and process conventions that must survive this session

Both freezes record image `vllm/vllm-openai@sha256:3dbe092ec5b2cef63b6104d33fa75d6ce53a7870962529ada69f78bbbc38e776`.
Their exact `container_command` arrays live in [first freeze](larger-test/freeze.json) and [second freeze](larger-test-v2/freeze.json); inspect those arrays as data, never execute them to recover a completed run.
The recorded flags are `VLLM_BATCH_INVARIANT=1`, `--attention-backend TRITON_ATTN`, `--dtype bfloat16`, `--kv-cache-dtype auto`, `--tensor-parallel-size 1`, `--max-model-len 32768`, `--max-num-seqs 4`, `--max-num-batched-tokens 2048`, `--gpu-memory-utilization 0.70`, `--enable-prefix-caching`, `--generation-config vllm`. The read-only model mount is the local Qwen3-30B-A3B HF directory at container mount `/model`; port mapping is localhost 18088 to 8000, device is `nvidia.com/gpu=0`, IPC is host. Temperature 0, seed 20260906 and cap 2048 are recorded decoding settings. The image is locally present (read-only Docker inspect returned image ID `sha256:ffa30d66ff5c9346c6389507cc529827fc9934a6d2ee37855934f94fe1061cdc`, size 23,274,948,300 bytes). Image presence is not a historical full-weight identity receipt.

Ollama is installed at `/usr/local/bin/ollama`; an `ollama serve` process and the local tags endpoint were observed during this verification. The endpoint returned `kimi-k3:cloud`, remote model `kimi-k3` at ollama.com. [Kimi review helper](../tools/run_kimi_review.py) defaults to `OLLAMA_HOST=http://127.0.0.1:11434` and `KIMI_MODEL=kimi-k3:cloud`; [tie-break helper](../tools/run_tiebreak.py) uses the same defaults. These make remote model requests, not local CPU inference. Availability/authentication for a new generation was **not** tested, and no remote generation was requested. After reboot, if these checks show no existing service, the daemon command is `ollama serve`; start it only as a new owned process with a durable log and immediate PID registration. Its cloud model requires the host’s Ollama account authorization; the listed tag alone does not prove that authorization works. Do not print credentials or start duplicate daemons. Read-only checks:

```bash
command -v ollama
curl --fail --max-time 3 http://127.0.0.1:11434/api/tags
ps -eo pid,ppid,lstart,comm | rg ollama
```

The ignored root `.stencil-owned-pids` registry stores one PID per line. Register every background job **you launch** immediately with `echo "$!" >> /home/bmarti44/stencil-llm/.stencil-owned-pids`. The [guard](../tools/hooks/pretool_guard.py) checks registered/environment PIDs and their process descendants; [.claude settings](../.claude/settings.json) attaches it to Claude Bash PreToolUse. Do not assume this hook runs in every tool/client. A stale PID can be reused after reboot: registry membership alone is not proof of current-session ownership. Verify launch provenance/start time; never adopt or kill another session's process. Use absolute paths for all queued work, respect `.review.lock`, preserve individual exit codes and raw logs, and never synthesize success sentinels.

## Portability, local-only assets and verification limits

Git cannot restore untracked weights or ignored raw outputs. Preserve exact bytes; retraining, generating replies again and resurrecting chains are not recovery. [Verification inventory](handoff/VERIFICATION.md) records kit additions, byte checks, source receipts and the important untracked inventory. [Kit README](handoff/README.md) explains scratchpad reconstruction without launching old jobs.

Qwen3-30B-A3B lives under the repository’s models directory: 16 untracked shards totaling 61,066,575,648 bytes plus untracked HF metadata/tokenizer files. The local smaller trunks also live under models; [conversion metadata](../models/CONVERSION.json) describes earlier conversions. Admission-v2, ft-v3, relations-v3, relation seeds and the focus LoRA assets have important untracked files under data/classifier/model; the exact paths and tracking status are in the verification inventory and byte table below. No weights are committed by this task. The original pre-run full-shard comparison remains unavailable, even when current hashes match the earlier handoff receipt.

Both run directories retain committed records, summaries, audits, costs and local hash manifests: [first local hashes](larger-test/local-hashes.json), [second local hashes](larger-test-v2/local-hashes.json). Their raw HTTP/loop bodies remain local and outside Git. Existing receipt hashes can verify copies but cannot recover lost bodies; off-host preservation has not been established. Measured GPU-held time is 24,660.9007065 seconds (6.85025h) for run 1 and 7,673.19586372 seconds (2.13144h) for run 2, from [first lifecycle](larger-test/lifecycle.json) and [second lifecycle](larger-test-v2/lifecycle.json). These exclude development cost and are not the successor budget.

Important untracked work includes the superseded [composition memo](focus-mechanism-composition-astra.md), [check32 script](../scripts/focus_check32.py), relation development predictions and learned weights. They are preserved in place, not silently swept into this docs commit. The frozen-v2 heldout3 diagnostic predictions/metrics and its diagnostic script still live only in the old scratchpad; the verification inventory records their paths, sizes and hashes. Archiving those original data/code receipts and arranging durable storage for local raw outputs/weights remain open. Do not regenerate or rescore to fill this gap.

The clean admission bank’s exposure lineage, remote Kimi generation authorization, historical serving identity and off-host backups cannot be certified by this docs task. No GPU status query, experiment, scorer execution, code change or model load was performed. Re-check current processes when taking over; a process snapshot cannot promise tomorrow’s idleness.

## Local weight byte receipts — verified current files, not historical serving identity


The earlier per-file SHA256 and byte receipts below were checked again using streaming CPU reads, without model loading. They verify current local bytes; no pre-run full-shard comparison was available, so they do not independently certify historical serving identity. Preserve these exact bytes; retraining is not recovery.

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


## 2026-09-07 continuation: automation criterion and first maintenance DEV attempt

Brian subsequently clarified that fully automated maintenance matching good manual prose can itself be a major benefit; superiority over the manual oracle is no longer required. The superseding criterion is in [CURRENT-GOAL.md](CURRENT-GOAL.md). Kimi K3 via Ollama authored two original DEV conversations, Sol xhigh implemented the isolated updater and driver, and independent Astra xhigh reviewed data, code and results. The optional factorial remains deferred.

The first frozen 16-call updater-only attempt completed in 620.47 seconds including startup/cleanup, with no retries or gold resets. It failed maintenance: 0/48 complete semantic views and 0/2 whole trajectories agreed, with 5 structurally accepted but semantically incorrect transactions and 11 rejected proposals. Exact receipts and replay were independently checked. See [result and accuracy addendum](quick-checks/maintenance-dev-01/RESULTS.md) and [independent audit](quick-checks/maintenance-dev-01/accuracy-review-astra.md). No worker or fresh validation screen ran. No old frozen outputs were rescored. The next candidate is a clearer semantic extraction prompt in a separately frozen DEV attempt; the present result does not justify scaling this recipe.


## 2026-09-07 continuation: second failure, research diagnostic next

Prompt-only attempt02 at commit `cccf963f` also failed complete maintenance on the same exposed Kimi DEV:0/48views,0/2trajectories. Independent Astra replay and semantic audit are preserved in [attempt02](quick-checks/maintenance-dev-02/RESULTS.md). Six valid transactions include two no-ops; four mutations add five entries; ten transactions are rejected. Partial semantic gains are credited, not treated as whole-state success. All16calls finished in615.55seconds including cleanup; no model server remains from this attempt.

Two deep-research agents investigated protocol and memory update architectures after Brian authorized research when stuck. [Reviewed research brief](factorial-prep/research/research-brief.md) recommends a prospective four-call cold diagnostic of plain extraction versus transaction output, not another full maintenance retry. CPU local-template reconstruction matches2039server-reported prompt tokens and expected non-thinking suffix, but does not prove server-rendered bytes. Both complete maintenance failures remain on the record and the three-failure stop-loss remains. No third run, worker or clean validation launched. Automatic parity with good manual prose remains the target.


## 2026-09-07 continuation: cold diagnostic supports testing prose maintenance

[Four-call cold diagnostic](quick-checks/maintenance-cold-01/RESULTS.md), pinned `d94ecd41`, is complete and independently audited: prose2/2 complete, register1/2 complete; register5/6 effective views. Both JSON transactions structurally pass. TypeScript output has correct task content but lacks the global rule and mislabels kind. Exact4requests equal pre-runpreview; bytes and offlinecompiler/state replays agree. No retries/caps/errors;4529tokens,26.61sdriver,467.39/900sreservation, owncontainer removed/flagclear.

This shows basic extraction on two exposed cold messages and supports a small separately registered multi-turn prose-memory check. It does not prove full maintenance, long-session focus, freshness, manual-prose equivalence, or coding quality. Preserve two earlier full-maintenance failures and the existing stop-loss. Next: Sol implementation of a simple own-notes prose updater and bounded test, KimiK3/Ollama for any new DEV data, independent Astra xhigh review before freeze/inference and after results. No next model run has launched.


## 2026-09-07 continuation: prose maintenance fails; stop-loss applied

The newly authored Kimi2x8 prose-memory trial at3ff88b8f completed16calls with no transport/cap errors. Rust notes explicitly relabeled global rules as task-specific, defeating registered error-free maintenance despite correct later edition replacement/restoration. Independent Astra audited exact source pins, wire receipts and own-note chains. [Result and semantic audit](quick-checks/prose-maintenance-01/RESULTS.md) preserve the full evidence.12,283tokens;90.13sdriver;546.21/900sreservation, owned container removed.

This is the third full-maintenance failure. Park the small single-updater recipe line and do not repeat a cosmetic prompt repair. Research may identify a substantially different hypothesis; no new inference or worker run is underway. Automatic parity with good manual prose is still valuable and remains unproven, as do coding competence and larger clean validation. KimiK3/Ollama data, Solxhigh implementations, Astraxhigh reviews remain the requested roles.
