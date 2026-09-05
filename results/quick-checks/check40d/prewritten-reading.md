# Check 40d — SET / HOLD / SWITCH / BACK / CLEAR

Unregistered, disclosed, 2026-09-05. Qwen3-30B-A3B bf16, greedy, 64-token
caps, unchanged 40b/40c router hook and frozen JS/Python profiles. Fit/train-on:
none. Profile-on: committed 40b's 32 cued competence replies; original dose
selection on eight setup tasks, 40c exploratory dose comparison on its reused
32 screen tasks. Evaluated-on: 32 new synthetic retained-history episodes,
five distinct expressions per episode, disjoint from those prior expressions.
Same three screen expression families; no benchmark or sealed inputs.

## Fixed pre-run design and reading

Primary alpha 3 sustained is the orchestrator's explicit override: 40c's clean
maximum was JS32/32, broken0; alpha 2 was the script's first-eligible pick
(JS25/32, broken0) and is a separate secondary arm here. No dose selection here.
SET JS bias/task1 -> neutral non-code user+generated-assistant pair under JS
bias -> HOLD JS bias/task2 -> SWITCH Python bias/task3 -> BACK JS bias/task4 ->
CLEAR bias OFF/task5. Every task request is new and uncued except text-cue.
Each arm retains its own complete user+assistant pairs AND actual KV cache;
new tokens receive the current bias, old KV is never recomputed. All 48 layers,
prefill and decode including turn-ending tokens. Bias stays JS across the delay.
An ended or capped response is retained literally; capped answers get the
inherited im_end closure. No replacement, replay, truncation or history reset.

Arms in fixed order: correct alpha3 schedule; shuffled independent within-layer
permutations of alpha3 JS bias at EVERY step including NEUTRAL and CLEAR
(matched per-layer norm, fixed seed 40043, frozen before outcomes); OFF throughout;
text-cue without bias ("Use JavaScript." at SET/HOLD/BACK, "Use Python." at
SWITCH, no cue at NEUTRAL/CLEAR); correct schedule alpha2 secondary. No instruction
persists in a hidden prompt. Fresh OFF CLEAR baseline once per episode precedes
all arms, for paired imposition = valid JS at CLEAR where fresh OFF is Python.
The retained OFF arm separately measures uncued-history defaults.

CONTROLLABLE iff correct valid unbroken JS >=26/32 at SET, HOLD, BACK,
valid unbroken Python >=26/32 at SWITCH and CLEAR, correct broken <=2/32 at
EVERY scored step, and shuffled valid JS <=4/32 everywhere (including the delay).
PARTIAL iff SET/HOLD/BACK meet target and breakage bars, shuffled passes, but
SWITCH or CLEAR target/breakage fails; name each failed release step.
Otherwise NOT CONTROLLABLE. Incomplete execution is INCOMPLETE, without a
behavioral verdict. If pre-run cost selects 24 episodes, use conservative
integer equivalents: >=ceil(26*24/32)=20, <=floor(2*24/32)=1 broken,
<=floor(4*24/32)=3 shuffled, disclosing changed denominators before any run.
Secondary and text arms never rescue the primary reading.

Score unchanged Python ast and Node --check parsers, coarse task check,
breakage/truncation flags, first token/first three/fence; report per-step tables,
per-family breakage, => replies and literal -> substrings (may be annotations),
and paired adjacent-language transition counts. Coarse checker can miss valid
arrow assignments; no generated programs executed. Neutral pair gets parser
and token diagnostics plus literal OK adherence, excluded from code breakage
bars because it explicitly requests non-code. This is a history/release check
on arithmetic surface syntax, not autonomous state maintenance or transfer.

## Frozen cost and execution

32-episode capped projection = 7002.68 s;
24-episode fallback = 5370.01 s. Select 32 before running.
992 generations = 32*(5 arms*6 including neutral +1 fresh CLEAR),
63488 capped tokens /15 tok/s +377.61 s prior measured load
+1 s/request prefill allowance, all times multiplied by 1.25 reserve =
7002.68 s (1.9452 GPU-h), cap 7200 s including load,
kernel checks and cleanup. Cooperative per-forward/token stop, no signals;
blocking operations may overrun and must be disclosed. No outcome retries.
Pinned PYTHONNOUSERSITE=1 .venv/bin/python -s -B; require transformers5.16.1
from .venv and verify every router slot0 equals raw F.linear before generation.
Reuse grouped_mm dispatch/OFF equality check. Foreground only; acquire shared
review lock, require no other Stencil RUNNING.flag or GPU compute process except
Brian's pid2705, and >=68 GiB system MemAvailable. Publish own RUNNING.flag while
running, remove on normal/exception cleanup. Never touch or signal any process.

## Results

PENDING; no outcome observed.
