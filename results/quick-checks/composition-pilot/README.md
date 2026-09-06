# Composition DEV pilot — prewritten 2026-09-06

Status: frozen recipe, GPU outcomes pending. Fit/train-on none; development-on
SLAB DEV only, authored templates/seeds disjoint from the evaluation bank.
No evaluation episode or data/bench content opened. R uses explicitly adopted GOLD
DEV events; O uses the identical event/renderer path and is not an independent
perception measurement. N retains ordinary complete history; T restates evaluator
text each request. All actuator settings OFF (40k R3 HARM; 40l R4 diagnostic).
This is a local package-dispatch pilot, not a completed single-snapshot shipment.

CPU prerequisite: Fable round 2 resolves H1–H4/M1–M3; the 35c546f4 WORKLOG records
the bank repair/freeze. N1 repaired before inference: attempted and executed
replacement scoring uses the last parsable snapshot when the prior file is broken.
Regression fails on original code and passes after repair, including true-new-stale
positive control. All original eight DEV episodes were actually 16 rounds; to meet
this brief's long-context requirement DEV-06/07 are now 32, with DEV-only turn-26
reinstatement (eval long uses 27/28/29). DEV fixtures re-frozen before GPU; evaluation
hashes/accounting preserved from the committed fixture, never regenerated from content.
The updated CPU accounting is 13.637h including the larger DEV pilot, not GPU evidence.

Frozen order: DEV-00,01,06,07,02,03,04,05. The first four are the fallback (all four
domains, two short/two long). Run sequential RNTO on DEV-00, then batch4 RNTO on the
same full episode. Batch may serve later episodes only if every lane's output bytes
and EOS match sequential at all 16 rounds. Otherwise fall back to sequential.
The diagnostic replay is separately labeled and charged, never pooled as new cases.
Attempt all eight in fixed order if the 5400s allocation allows. Before each later
episode reserve 1.25 times the worst measured wall seconds/round in that mode times
its scheduled rounds, plus 60s. No replacement, shortened history or outcome selection.
If even the fixed four cannot finish, read INELIGIBLE/INCOMPLETE.

One local Qwen3-30B-A3B bf16 load, SDPA, eager MoE, greedy argmax, 512 generated-token
cap including EOS. Frozen SYSTEM_PROMPT and real sandbox Executor/checker. Actual
model.generate(custom_generate=models/stencil-package, decoder=RetainedDecoder)
dispatch invokes the package register/renderer/journal; the injected backend retains
KV per episode. Batch lanes retain independent logical positions/attention masks;
physical padding stays invisible. No prefix sharing, attention masking of own bodies,
actuator, retries, output selection or second generation for an invalid tool envelope.

paired_context_gate runs BEFORE any arm renders, on conservative pre-render bounds
(system + full retained history + encoded transport/T text + 2048 tokens for the
live block/tombstones/chat delimiters); actual length <= bound is asserted at decode.
A rejected round rejects all four arms and is reported; no arm silently shrinks.
The exact existing renderer layout is unchanged. The post-pilot DEV-00 R golden
commits exact UTF-8 rendered text losslessly in JSONL, with per-round hashes.
After that freeze, layout changes require a registered amendment.

Journal before aggregates: all v2 Journal.FIELDS, plus same-writer oracle results,
current attempted/executed calls, results/hashes, gate receipt, timings and hidden
file hashes. Tools see only public cases; hidden outcomes never enter next requests.
Hidden arrays: layers 8/16/24/32/40, one-based post-block residuals (hidden_states[L]),
shape (5,2048), original bf16 cast to float16. Last prompt-token vector and mean over
actually forwarded generated body tokens (float32 accumulation). EOS excluded.
No extra forward for capture: at cap the final sampled token has no activation yet;
record hidden_complete=false and the exact contributing count, never fabricate it.
No-output mean is NaN, undefined, not a zero vector. The .npy files stay local;
hidden-manifest.json records shapes, keys and SHA256. README/summary/records and
small audit/freeze receipts are committed; hidden binaries and workspaces are not.

Readings frozen before inference: ELIGIBLE requires complete fixed fallback,
projection <=12 GPU-h, full context plus 512 reserve <=32768, truncations <=2%,
R >=75% own bodies in 100–300 AND >=75% completed R episodes with their first ten
bodies all in band, and nonzero style/format/process relapse opportunities in at
least one arm. Language relapse has denominator zero BY DESIGN (live Python rule
never retired); report this zero row, not a fictitious language pressure pass.
Any failed item gives INELIGIBLE with the item. No shipping PASS from a DEV pilot.

Cost: spent + measured reload allocation + 1.25*[64(cR+cN)+16(cT+cO)], using the
largest completed DEV episode cost per arm, including GPU-held journal/tool waits.
Also report full-four-by-64 cost. Batch amortizes four occupied lanes, and only a
byte-invariant batch implementation can qualify. Report sequential and batch
separately. If only short episodes were measured in a mode, show the observed-cost
projection AND a 32-round normalization using measured seconds/round; explicitly
mark missing long-context validation. No invented prefill/decode rate. Pilot spend
and the diagnostic replay are included in both projections; no optional arm cost.

DEV-only mask trigger: R >=15% relapse on one kind, >=20 opportunities and >=2
episodes, with the trait previously emitted, and O also relapsing in >=2 episodes.
Report the trigger only; no optional GPU mask screen is part of this task.
No signals, process termination, external messages or push. RUNNING.flag is held
only while allocated; any other Stencil flag/GPU Python prevents load.
