# Composition pilot 4 — INELIGIBLE

Completed 479 calls; R final success **0/8 required episodes**, with **7 complete**. Round-0 R indent **2/8 required responses**; strictly executed/parsed eligible subset **2/8**; diagnostic emitted JSON-prefix code **2/8**. Prefix inspection never repairs or executes a rejected response. Determinism **D=0**, 64 calls across completed starts.

Failed/unmeasured gates: incomplete required R/N/T DEV trajectories; R round0 indentation <50% or incomplete; R executed-call rate <90%; R truncation >2%; N executed-call rate <90%; N truncation >2%; T executed-call rate <90%; T truncation >2%; R final success <5/8; registered projection >12h even setting unmeasured O cost to zero; check45 HF teacher-forced recovery cost unmeasured (prewritten full-cost condition).

| Arm | Calls executed | Caps | Final success | Stale execution | Wrong skill | Breakage | Decode tok/s | s/call |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|R|108/159|51|0/7|38|6|57|10.857|28.617|
|N|109/160|51|0/8|42|6|90|12.240|23.942|
|T|131/160|29|0/8|50|3|48|11.646|20.879|
|O (UNRUN)|0/0|0|0/0|0|0|0|—|—|

Per-episode results (violations and relapse numerator/denominator in language/style/format/process order):

| Episode/arm | Success | Integration | Stale | Wrong | Breakage | Violations L/S/F/P | Relapse L/S/F/P |
|---|---:|---:|---:|---:|---:|---|---|
|slab-dev-00/R|False|True|6|0|0|0/16/4/10|0/0, 0/0, 4/4, 6/6|
|slab-dev-01/R|False|True|6|0|0|0/14/6/7|0/0, 0/3, 6/6, 1/4|
|slab-dev-06/R|INCOMPLETE|—|0|3|31|0/0/28/3|0/0, 0/13, 0/13, 0/15|
|slab-dev-07/R|False|True|15|0|0|0/7/15/11|0/0, 7/13, 15/15, 5/11|
|slab-dev-00/N|False|False|0|1|10|0/6/10/3|0/0, 0/0, 0/4, 0/6|
|slab-dev-01/N|False|False|6|1|0|0/11/6/10|0/0, 0/3, 6/6, 4/4|
|slab-dev-06/N|False|False|19|0|19|0/13/14/23|0/0, 13/13, 14/14, 16/16|
|slab-dev-07/N|False|False|0|2|32|0/0/30/2|0/0, 0/7, 0/15, 0/11|
|slab-dev-00/T|False|True|6|0|0|0/2/4/10|0/0, 0/5, 4/4, 6/6|
|slab-dev-01/T|False|True|6|0|0|0/0/6/6|0/0, 0/5, 6/6, 0/4|
|slab-dev-06/T|False|False|0|3|32|0/0/29/3|0/0, 0/13, 0/14, 0/16|
|slab-dev-07/T|False|True|15|0|0|0/0/15/6|0/0, 0/13, 15/15, 0/11|
|slab-dev-02/R|False|False|0|3|13|0/3/13/3|0/0, 0/0, 0/4, 0/5|
|slab-dev-03/R|False|True|5|0|0|0/16/5/7|0/0, 0/3, 5/5, 0/6|
|slab-dev-04/R|False|True|6|0|0|0/16/5/6|0/0, 0/3, 5/5, 1/6|
|slab-dev-05/R|False|False|0|0|13|0/6/10/3|0/0, 0/3, 0/5, 0/6|
|slab-dev-02/N|False|False|5|1|16|0/10/4/16|0/0, 0/3, 4/4, 5/5|
|slab-dev-03/N|False|True|6|0|0|0/15/5/13|0/0, 0/3, 5/5, 6/6|
|slab-dev-04/N|False|False|0|1|13|0/5/11/3|0/0, 0/0, 0/5, 0/6|
|slab-dev-05/N|False|True|6|0|0|0/15/5/12|0/0, 3/3, 5/5, 6/6|
|slab-dev-02/T|False|False|5|0|16|0/16/4/16|0/0, 0/6, 4/4, 5/5|
|slab-dev-03/T|False|True|6|0|0|0/11/5/13|0/0, 0/4, 5/5, 6/6|
|slab-dev-04/T|False|True|6|0|0|0/12/5/11|0/0, 0/4, 5/5, 6/6|
|slab-dev-05/T|False|True|6|0|0|0/15/5/12|0/0, 3/4, 5/5, 6/6|
|slab-dev-00/O|UNRUN|—|—|—|—|—|—|
|slab-dev-01/O|UNRUN|—|—|—|—|—|—|
|slab-dev-02/O|UNRUN|—|—|—|—|—|—|
|slab-dev-03/O|UNRUN|—|—|—|—|—|—|
|slab-dev-04/O|UNRUN|—|—|—|—|—|—|
|slab-dev-05/O|UNRUN|—|—|—|—|—|—|
|slab-dev-06/O|UNRUN|—|—|—|—|—|—|
|slab-dev-07/O|UNRUN|—|—|—|—|—|—|

Per-episode timing and cost allocation (observed calls only). Allocated seconds = output tokens / measured whole-schedule aggregate rate; this partitions shared schedule cost by tokens, rather than measuring isolated episode GPU use. Startup/checks/cleanup are charged separately in the total.

| Episode/arm | Calls | Tokens | Decode tok/s | Seconds/call | Allocated schedule seconds |
|---|---:|---:|---:|---:|---:|
|slab-dev-00/R|16|2870|9.403|19.519|116.048|
|slab-dev-01/R|16|2972|9.806|20.055|120.172|
|slab-dev-06/R|31|15179|11.678|43.763|613.759|
|slab-dev-07/R|32|5590|9.722|20.330|226.030|
|slab-dev-00/N|16|7198|12.685|35.826|291.049|
|slab-dev-01/N|16|1781|10.377|11.266|72.014|
|slab-dev-06/N|32|5206|10.843|15.492|210.503|
|slab-dev-07/N|32|15952|13.081|38.711|645.015|
|slab-dev-00/T|16|2934|10.134|18.384|118.636|
|slab-dev-01/T|16|3164|10.564|19.399|127.936|
|slab-dev-06/T|32|15697|13.406|37.213|634.704|
|slab-dev-07/T|32|5174|10.805|15.624|209.209|
|slab-dev-02/R|16|7652|11.817|41.136|309.407|
|slab-dev-03/R|16|2784|9.580|19.145|112.570|
|slab-dev-04/R|16|2854|9.628|19.627|115.401|
|slab-dev-05/R|16|7088|11.600|39.452|286.602|
|slab-dev-02/N|16|2714|10.371|16.663|109.740|
|slab-dev-03/N|16|2614|10.249|16.460|105.696|
|slab-dev-04/N|16|7352|14.439|32.449|297.276|
|slab-dev-05/N|16|3046|10.752|18.347|123.164|
|slab-dev-02/T|16|2246|10.373|13.879|90.816|
|slab-dev-03/T|16|2614|10.487|16.170|105.696|
|slab-dev-04/T|16|2918|10.889|17.416|117.989|
|slab-dev-05/T|16|3062|11.155|17.865|123.811|

Main-run measurements: determinism D=0; maximum actual context 31465 <=32256; executed-trait opportunities in at least two R episodes for kinds ['style', 'format', 'process']. These do not override the failed gates.

Actual fixed C4 schedule (including C2 long tails, HTTP, tools/checker and barriers) **24.731 tok/s**. GPU-held **6831.011/9000s** (all starts), load **443.422s**. Served-only conservative projection **UNAVAILABLE GPU-h**. Formula and all per-episode timing/token costs are in [summary.json](summary.json): prior spend + this run + measured reload +1.25 × [64(max R+max N tokens)+16(max O+max T tokens)] / measured aggregate rate. Max per-arm counts include observed partial long episodes as lower bounds; a full served projection requires complete coverage of every arm. Overlapping request seconds are latency, not summed GPU cost. The known R/N/T contribution gives a registered-projection floor of **38.547h** even setting O cost to zero; this is a lower bound on that conservative projection, not a complete workload forecast. HF recovery remains unmeasured; full check45-inclusive eligibility receives no unmeasured credit.

DEV mask trigger **NOT ESTABLISHED**, kinds=[]; all four kinds and executed-prior-trait denominators are in summary. No masks enabled. T multi-function emitted responses under the amended parser (edit or replace; descriptive): 2 parseable responses (names listed in summary); capped malformed responses are counted as breakage, not silently repaired.

Rejected Python-literal boolean residues (outside quoted code strings): {'R': 0, 'N': 0, 'T': 0, 'O': 0}. These are CPU classifications of literal journaled outputs, not parser repairs.

Gold events drive R in DEV only; no fitting, evaluation episode construction or data/bench reads. **package path outcome-unvalidated**. Backend uses qualification image digest `sha256:3dbe092ec5b2cef63b6104d33fa75d6ce53a7870962529ada69f78bbbc38e776`, exact flags/env and request parameters in [registration.json](registration.json). Prior HF divergence5/64 (R1/16) stands; this pilot does not remeasure HF trajectories.

[record shards](artifact-manifest.json) contain same-run v2 records, execution/tolerances, checker and per-call timings; local http/records.jsonl (size/SHA256 in artifact-manifest.json) retains actual streamed token IDs/chunks/usage. [schedule.jsonl](schedule.jsonl) fixes episode lanes and round barriers. Hidden states are **not captured** on vLLM; check45 needs teacher-forced HF prefill. [transcript-manifest.json](transcript-manifest.json) lists the full HF final-input files under hf-transcripts/ (including system prefix), per-episode output and every prompt+body+EOS hash required, with layer/body-position convention. The separate retained-history hashes describe session state without the system prefix; those files alone are not HF prefill inputs.

[Unsubmitted calls](unsubmitted.jsonl): 1 required and 160 optional. UNRUN/None endpoints are unavailable, not observed failures or zeros. All planned episodes remain in eligibility accounting.

Stale execution counts rounds with actual executed tools and an observed retired-trait relapse. Per-kind relapse conditions on prior executed trait plus registered opportunity; style measures executed code, format/process measure emitted report traits. Current execution and attempted violations remain separate in records. Empty indentation is not compliant.

Validation: [50 targeted DEV-only tests](validation-all-amendments.log), [96-call CPU smoke](smoke.json), the original qualification adapter EOS/cap checks. The final [CPU audit](audit.json) replays each saved actual prompt, controller state, output, execution and checker result and verifies backend identity, determinism, transcript hashes and cleanup. No full pytest suite or evaluation episodes were run.

CPU literal-output regression (all460 pilot3 DEV responses through Executor.run/check; no regenerated model outputs):

| Arm | Original executed | Amended executed | Unchanged caps | Violations L/S/F/P |
|---|---:|---:|---:|---|
|R|53/160|101/160|59|7/70/160/91|
|N|49/160|77/160|82|7/49/160/57|
|T|65/140|84/140|52|0/40/140/64|

Full per-kind CPU regression and source SHA256s: [regression.json](regression.json). The old task strings are preserved, so all460 old format violations remain. This replay measures parser/executor changes, not counterfactual model trajectories.

The first start stopped on a conservative estimate before R round30. The [registered exact-context continuation](continuation/README.md) restored all92 observations on CPU and submitted only unrun admissible calls. R DEV06 round31 was actually32490>32256 and remains unavailable; no history was trimmed. Both starts and repeated qualification checks are charged. Inference sources were committed before GPU at981658a8; continuation registration atb1a18d30; the first92-call checkpoint at244c701d.

**Registered trait swap applied afterwards on CPU; swapped GPU screen UNRUN.** R indentation2/8 triggers the fixed2/3/4 -> ALPHA/BETA/GAMMA docstring-prefix mapping. All8 transformed DEV manifests are frozen and32 positive/wrong/missing/capped witnesses pass through the actual loop/executor/checker; [CPU swap artifacts](trait-swap/README.md). No candidate search or fitting; original pilot4 outcomes stand.

Executed rate means responses with at least one actually executed tool, not necessarily a valid edit or successful task. The legacy strict-JSON attempted_tool_calls field is empty on 0 executed responses accepted by the amended envelope parser; execution/tolerance records are authoritative. Raw outputs are preserved.

Every pilot4 artifact committed by this task is <=10,000,000 bytes. [Artifact manifest](artifact-manifest.json) records byte sizes/SHA256s for committed shards and local HTTP/oversized journals. The exact primary journals are reconstructed by concatenating each phase’s records/*.jsonl shards in filename order. No streamed HTTP journal is added to git.

[Prewritten registration](prewritten.md) follows unchanged.

# Composition pilot 4 — REGISTERED, not yet run

2026-09-06. Amendment 3 in ../composition-pilot-3/README.md governs the CPU
fixes and this run. Frozen order 00,01,06,07 then 02,03,04,05; R/N/T then optional
O. 9000 GPU-seconds, one qualified start, cold reverse C4 long-prompt replay
before first-eight cold/warm/mixed replay. Exact gates and cost formula are in
Amendment 3 and pilot3 prewritten registration; hidden states deferred.
Fit none; DEV only; no data/bench or evaluation episodes. Package path
outcome-unvalidated. No host signals, own container only; no push.

CPU regression: R executed 53 ->101/160 (63.125%); N49 ->77/160 (48.125%);
T65 ->84/140 (60%). Caps unchanged R59/N82/T52. All460 literal outputs traverse
Executor.run/check; format violations remain460/460 because old task strings
are preserved. Per-kind outcomes and source hashes: regression.json and
regression-records.jsonl. These do not predict amended model outputs.
Validation:30 targeted tests pass;96-call reference loop smoke passes.
HTTP streams remain local, excluded from git with size+sha256 manifest.
Any artifact above10,000,000 bytes likewise remains local; compact shards are
committed when necessary. tools/hooks/pre-commit checks staged blob sizes.
