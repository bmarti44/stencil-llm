# Conditional lexical style screen — COMPETENCE FAIL

Fit/train-on: none. Evaluated-on: the eight authored DEV episodes only. Gold events drive R in DEV only; actuator OFF. No evaluation or data/bench reads.

The original required round-zero indentation screen failed2/8 (eligible parsed/executed subset2/4). The [conditional registration](conditional-registration.md) fixed one replacement, with no candidate search: indent2/3/4 maps to docstring_prefix ALPHA/BETA/GAMMA. Each emitted function must start with a docstring beginning with its exact label and colon; indentation is free. [Activation](activation.json) preserves original response hashes. Frozen transformed episodes and shared system prompt are in [frozen.json](frozen.json).

**2/8 required responses compliant; 2/2 eligible executed edits compliant.** The registered gate requires both >=4/8 required responses and >=50% eligible executed edits. Five responses were rejected as malformed envelopes; DEV00 executed an edit containing a bare BETA prefix before the function and failed its test. These six responses cannot disappear from the required denominator. All eight were uncapped. The result measures the execution-qualified round-zero screen, not label compliance inside rejected envelopes.

This is ONLY the failed round-zero competence-gate re-pilot, not eight complete episodes. No retirement/relapse, R/N effect, final-episode competence, or larger-test eligibility is established. The original pilot's outcomes stand; no second replacement is selected.

The same qualified image digest, exact flags/env, max-num-seqs4 and raw-ID request semantics are frozen in [registration.json](registration.json). The fresh server first passed the same eight frozen prompts cold/warm/mixed C4: D=0 across24 calls. The two style waves submitted DEV00,01,06,07 then02,03,04,05, four R round-zero calls each, with a barrier; [schedule.jsonl](schedule.jsonl) records submission order, while records retain actual completion order. Max output512 and both qualified EOS IDs are unchanged.

| Episode | Label | Compliant response | Executed tools | Breakage | Tokens | Seconds/call |
|---|---|---:|---:|---:|---:|---:|
|slab-dev-00|BETA|False|2|True|394|29.851|
|slab-dev-01|BETA|True|2|False|233|20.750|
|slab-dev-06|GAMMA|False|0|True|327|27.217|
|slab-dev-07|GAMMA|False|0|True|269|23.929|
|slab-dev-02|BETA|False|0|True|435|27.903|
|slab-dev-03|ALPHA|True|2|False|195|17.167|
|slab-dev-04|ALPHA|False|0|True|217|19.206|
|slab-dev-05|BETA|False|0|True|223|19.569|

Measured style-wave aggregate **39.489 tok/s**, 58.068s for8 calls. Style server startup/checks/calls/cleanup **764.957s**; all pilot3 starts **8796.278/9000s**. This short-prompt rate is not substituted for the main full-trajectory rate. The owned container was stopped/removed and the shared RUNNING.flag removed; [run.json](run.json), [server.log](server.log), and [container-inspect.json](container-inspect.json) retain identity and lifecycle. No host process was signaled.

[CPU witnesses](cpu-witnesses.json):32 passed before this GPU start, through the actual loop/executor/checker (positive, wrong label, missing label and cap for every DEV episode). [Final audit](audit.json):8 exact CPU prompt/output/execution/checker replays,32 HTTP calls,8 full HF-input hashes, fixed-backend determinism, cleanup and total budget verified. [records.jsonl](records.jsonl) journals the v2 fields, applied tolerances and timing; [HTTP records](http/records.jsonl) retain streamed raw IDs. No parser repair or extra runtime tolerance was introduced.

Hidden states are NOT captured by vLLM. Check45 would require teacher-forced HF prefill of the exact full prompt+body+EOS inputs listed and hashed in [transcripts.jsonl](transcripts.jsonl); files are c4/<episode>/R/hf-final-input.json. HF recovery timing is unmeasured. These eight round-zero inputs remain separate from the original main-pilot transcripts and labels.
