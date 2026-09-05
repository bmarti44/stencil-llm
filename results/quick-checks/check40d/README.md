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

**PARTIAL**. Primary failed conditions: SWITCH, CLEAR.

The primary schedule passes SET/HOLD/BACK and the shuffled specificity bar, but fails BOTH release questions: flipping to the frozen Python direction never changed the initial JS history, and turning the bias OFF never restored the fresh Python default. All 32 primary histories remain JS at every scored step. These observations do not isolate whether earlier biased KV or the retained JS answers dominate the current bias; both are retained by design.

The text-cue bar switches to Python on 32/32 SWITCH requests, showing that these retained histories can change language under an explicit request. Its uncued CLEAR also remains JS32/32, so CLEAR persistence is shared with text-cued histories. Alpha2 induces JS in only 6/32 fresh episodes and preserves those same six through every scored step; its Python26/32 at SWITCH/CLEAR reflects initial Python defaults, not successful release of the six induced JS histories. This bank is fresh and has new function names; the drop from 40c alpha2 JS25/32 is descriptive, not an isolated estimate of a history effect. Nothing was retuned.

Primary, OFF, text-cue and alpha2 have zero scored breakage and 32/32 coarse task passes at each step. Shuffled episode8 returns bare numbers at all five steps (accepted by both parsers, therefore ambiguous/broken); episode24 uses valid Python lambda assignments, which the frozen named-def coarse checker rejects. These account for shuffled broken1/32 and coarse30/32 per step. Every arm has zero => and zero literal -> replies at every scored step.

| Arm | Step | N | Valid JS | Valid Python | Broken | Coarse task pass | Truncated | => replies | -> replies |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| correct | SET | 32 | 32 | 0 | 0 | 32 | 0 | 0 | 0 |
| correct | HOLD | 32 | 32 | 0 | 0 | 32 | 0 | 0 | 0 |
| correct | SWITCH | 32 | 32 | 0 | 0 | 32 | 0 | 0 | 0 |
| correct | BACK | 32 | 32 | 0 | 0 | 32 | 0 | 0 | 0 |
| correct | CLEAR | 32 | 32 | 0 | 0 | 32 | 0 | 0 | 0 |
| shuffled | SET | 32 | 0 | 31 | 1 | 30 | 0 | 0 | 0 |
| shuffled | HOLD | 32 | 0 | 31 | 1 | 30 | 0 | 0 | 0 |
| shuffled | SWITCH | 32 | 0 | 31 | 1 | 30 | 0 | 0 | 0 |
| shuffled | BACK | 32 | 0 | 31 | 1 | 30 | 0 | 0 | 0 |
| shuffled | CLEAR | 32 | 0 | 31 | 1 | 30 | 0 | 0 | 0 |
| OFF | SET | 32 | 0 | 32 | 0 | 32 | 0 | 0 | 0 |
| OFF | HOLD | 32 | 0 | 32 | 0 | 32 | 0 | 0 | 0 |
| OFF | SWITCH | 32 | 0 | 32 | 0 | 32 | 0 | 0 | 0 |
| OFF | BACK | 32 | 0 | 32 | 0 | 32 | 0 | 0 | 0 |
| OFF | CLEAR | 32 | 0 | 32 | 0 | 32 | 0 | 0 | 0 |
| text-cue | SET | 32 | 32 | 0 | 0 | 32 | 0 | 0 | 0 |
| text-cue | HOLD | 32 | 32 | 0 | 0 | 32 | 0 | 0 | 0 |
| text-cue | SWITCH | 32 | 0 | 32 | 0 | 32 | 0 | 0 | 0 |
| text-cue | BACK | 32 | 32 | 0 | 0 | 32 | 0 | 0 | 0 |
| text-cue | CLEAR | 32 | 32 | 0 | 0 | 32 | 0 | 0 | 0 |
| alpha2 | SET | 32 | 6 | 26 | 0 | 32 | 0 | 0 | 0 |
| alpha2 | HOLD | 32 | 6 | 26 | 0 | 32 | 0 | 0 | 0 |
| alpha2 | SWITCH | 32 | 6 | 26 | 0 | 32 | 0 | 0 | 0 |
| alpha2 | BACK | 32 | 6 | 26 | 0 | 32 | 0 | 0 | 0 |
| alpha2 | CLEAR | 32 | 6 | 26 | 0 | 32 | 0 | 0 | 0 |

Breakage by family (broken / family N; unchanged two-parser category):

| Arm | Step | screen_0: ((a+b)*(c-d)) | screen_1: ((a*b)+(c*d)) | screen_2: ((a-b)-(c+d)) |
|---|---|---:|---:|---:|
| correct | SET | 0/11 | 0/11 | 0/10 |
| correct | HOLD | 0/10 | 0/11 | 0/11 |
| correct | SWITCH | 0/11 | 0/10 | 0/11 |
| correct | BACK | 0/11 | 0/11 | 0/10 |
| correct | CLEAR | 0/10 | 0/11 | 0/11 |
| shuffled | SET | 0/11 | 0/11 | 1/10 |
| shuffled | HOLD | 1/10 | 0/11 | 0/11 |
| shuffled | SWITCH | 0/11 | 1/10 | 0/11 |
| shuffled | BACK | 0/11 | 0/11 | 1/10 |
| shuffled | CLEAR | 1/10 | 0/11 | 0/11 |
| OFF | SET | 0/11 | 0/11 | 0/10 |
| OFF | HOLD | 0/10 | 0/11 | 0/11 |
| OFF | SWITCH | 0/11 | 0/10 | 0/11 |
| OFF | BACK | 0/11 | 0/11 | 0/10 |
| OFF | CLEAR | 0/10 | 0/11 | 0/11 |
| text-cue | SET | 0/11 | 0/11 | 0/10 |
| text-cue | HOLD | 0/10 | 0/11 | 0/11 |
| text-cue | SWITCH | 0/11 | 0/10 | 0/11 |
| text-cue | BACK | 0/11 | 0/11 | 0/10 |
| text-cue | CLEAR | 0/10 | 0/11 | 0/11 |
| alpha2 | SET | 0/11 | 0/11 | 0/10 |
| alpha2 | HOLD | 0/10 | 0/11 | 0/11 |
| alpha2 | SWITCH | 0/11 | 0/10 | 0/11 |
| alpha2 | BACK | 0/11 | 0/11 | 0/10 |
| alpha2 | CLEAR | 0/10 | 0/11 | 0/11 |

CLEAR release and fresh OFF baselines:

Fresh OFF: Python 32/32, JS 0/32, broken 0/32. Paired CLEAR impositions (JS where fresh OFF is Python): OFF 0/32; alpha2 6/32; correct 32/32; shuffled 0/32; text-cue 32/32.

Neutral delay: literal OK replies OFF 32/32; alpha2 32/32; correct 32/32; shuffled 30/32; text-cue 32/32. Neutral parser results are diagnostic only and code-breakage bars exclude this deliberately non-code request.

First-token, first-three-token, and fence counts (literal strings):

| Arm | Step | First token | First three tokens | Fence |
|---|---|---|---|---|
| correct | SET | {"&#96;&#96;&#96;": 32} | {"&#96;&#96;&#96;javascript\n": 32} | {"javascript": 32} |
| correct | HOLD | {"&#96;&#96;&#96;": 32} | {"&#96;&#96;&#96;javascript\n": 32} | {"javascript": 32} |
| correct | SWITCH | {"&#96;&#96;&#96;": 32} | {"&#96;&#96;&#96;javascript\n": 32} | {"javascript": 32} |
| correct | BACK | {"&#96;&#96;&#96;": 32} | {"&#96;&#96;&#96;javascript\n": 32} | {"javascript": 32} |
| correct | CLEAR | {"&#96;&#96;&#96;": 32} | {"&#96;&#96;&#96;javascript\n": 32} | {"javascript": 32} |
| shuffled | SET | {"-": 1, "&#96;&#96;": 1, "&#96;&#96;&#96;": 29, "solve": 1} | {"-27": 1, "&#96;&#96;&#96;\ndef": 1, "&#96;&#96;&#96;python\n": 29, "solve_history_": 1} | {"": 1, "(bare)": 2, "python": 29} |
| shuffled | HOLD | {"-": 1, "&#96;&#96;": 1, "&#96;&#96;&#96;": 29, "solve": 1} | {"-61": 1, "&#96;&#96;&#96;\ndef": 1, "&#96;&#96;&#96;python\n": 29, "solve_history_": 1} | {"": 1, "(bare)": 2, "python": 29} |
| shuffled | SWITCH | {"1": 1, "&#96;&#96;": 1, "&#96;&#96;&#96;": 29, "solve": 1} | {"170": 1, "&#96;&#96;&#96;\ndef": 1, "&#96;&#96;&#96;python\n": 29, "solve_history_": 1} | {"": 1, "(bare)": 2, "python": 29} |
| shuffled | BACK | {"-": 1, "&#96;&#96;": 1, "&#96;&#96;&#96;": 29, "solve": 1} | {"-65": 1, "&#96;&#96;&#96;\ndef": 1, "&#96;&#96;&#96;python\n": 29, "solve_history_": 1} | {"": 1, "(bare)": 2, "python": 29} |
| shuffled | CLEAR | {"1": 1, "&#96;&#96;": 1, "&#96;&#96;&#96;": 29, "solve": 1} | {"105": 1, "&#96;&#96;&#96;\ndef": 1, "&#96;&#96;&#96;python\n": 29, "solve_history_": 1} | {"": 1, "(bare)": 2, "python": 29} |
| OFF | SET | {"&#96;&#96;&#96;": 32} | {"&#96;&#96;&#96;python\n": 32} | {"python": 32} |
| OFF | HOLD | {"&#96;&#96;&#96;": 32} | {"&#96;&#96;&#96;python\n": 32} | {"python": 32} |
| OFF | SWITCH | {"&#96;&#96;&#96;": 32} | {"&#96;&#96;&#96;python\n": 32} | {"python": 32} |
| OFF | BACK | {"&#96;&#96;&#96;": 32} | {"&#96;&#96;&#96;python\n": 32} | {"python": 32} |
| OFF | CLEAR | {"&#96;&#96;&#96;": 32} | {"&#96;&#96;&#96;python\n": 32} | {"python": 32} |
| text-cue | SET | {"&#96;&#96;&#96;": 32} | {"&#96;&#96;&#96;javascript\n": 32} | {"javascript": 32} |
| text-cue | HOLD | {"&#96;&#96;&#96;": 32} | {"&#96;&#96;&#96;javascript\n": 32} | {"javascript": 32} |
| text-cue | SWITCH | {"&#96;&#96;&#96;": 32} | {"&#96;&#96;&#96;python\n": 32} | {"python": 32} |
| text-cue | BACK | {"&#96;&#96;&#96;": 32} | {"&#96;&#96;&#96;javascript\n": 32} | {"javascript": 32} |
| text-cue | CLEAR | {"&#96;&#96;&#96;": 32} | {"&#96;&#96;&#96;javascript\n": 32} | {"javascript": 32} |
| alpha2 | SET | {"&#96;&#96;&#96;": 32} | {"&#96;&#96;&#96;javascript\n": 6, "&#96;&#96;&#96;python\n": 26} | {"javascript": 6, "python": 26} |
| alpha2 | HOLD | {"&#96;&#96;&#96;": 32} | {"&#96;&#96;&#96;javascript\n": 6, "&#96;&#96;&#96;python\n": 26} | {"javascript": 6, "python": 26} |
| alpha2 | SWITCH | {"&#96;&#96;&#96;": 32} | {"&#96;&#96;&#96;javascript\n": 6, "&#96;&#96;&#96;python\n": 26} | {"javascript": 6, "python": 26} |
| alpha2 | BACK | {"&#96;&#96;&#96;": 32} | {"&#96;&#96;&#96;javascript\n": 6, "&#96;&#96;&#96;python\n": 26} | {"javascript": 6, "python": 26} |
| alpha2 | CLEAR | {"&#96;&#96;&#96;": 32} | {"&#96;&#96;&#96;javascript\n": 6, "&#96;&#96;&#96;python\n": 26} | {"javascript": 6, "python": 26} |

Adjacent scored-step language transitions (broken means no valid unbroken language):

| Arm | Transition | Counts |
|---|---|---|
| OFF | BACK->CLEAR | {"Python -> Python": 32} |
| OFF | HOLD->SWITCH | {"Python -> Python": 32} |
| OFF | SET->HOLD | {"Python -> Python": 32} |
| OFF | SWITCH->BACK | {"Python -> Python": 32} |
| alpha2 | BACK->CLEAR | {"JavaScript -> JavaScript": 6, "Python -> Python": 26} |
| alpha2 | HOLD->SWITCH | {"JavaScript -> JavaScript": 6, "Python -> Python": 26} |
| alpha2 | SET->HOLD | {"JavaScript -> JavaScript": 6, "Python -> Python": 26} |
| alpha2 | SWITCH->BACK | {"JavaScript -> JavaScript": 6, "Python -> Python": 26} |
| correct | BACK->CLEAR | {"JavaScript -> JavaScript": 32} |
| correct | HOLD->SWITCH | {"JavaScript -> JavaScript": 32} |
| correct | SET->HOLD | {"JavaScript -> JavaScript": 32} |
| correct | SWITCH->BACK | {"JavaScript -> JavaScript": 32} |
| shuffled | BACK->CLEAR | {"Python -> Python": 31, "broken -> broken": 1} |
| shuffled | HOLD->SWITCH | {"Python -> Python": 31, "broken -> broken": 1} |
| shuffled | SET->HOLD | {"Python -> Python": 31, "broken -> broken": 1} |
| shuffled | SWITCH->BACK | {"Python -> Python": 31, "broken -> broken": 1} |
| text-cue | BACK->CLEAR | {"JavaScript -> JavaScript": 32} |
| text-cue | HOLD->SWITCH | {"JavaScript -> Python": 32} |
| text-cue | SET->HOLD | {"JavaScript -> JavaScript": 32} |
| text-cue | SWITCH->BACK | {"Python -> JavaScript": 32} |

Broken scored replies by parser identity and fence: {"shuffled/SET: ambiguous, (bare)": 1, "shuffled/HOLD: ambiguous, (bare)": 1, "shuffled/SWITCH: ambiguous, (bare)": 1, "shuffled/BACK: ambiguous, (bare)": 1, "shuffled/CLEAR: ambiguous, (bare)": 1}. Flags (a reply can have multiple): {"ambiguous": 5}.

Execution: 992 generations, 26242 generated tokens; 2088.00 s = 34.80 GPU-min /120 cap, 0.00 s overrun; load 393.89 s, peak allocated 57.64 GiB. all scheduled generations complete.

Audit: every parser score, decoded token text, rendered message history, actual retained KV prefix, bias schedule/hash, first/fence/arrow field, aggregate and reading reconstructed on CPU. Frozen profile scaling and every shuffled permutation rederived; fresh task lineage and complete pair closures checked. Real router slot0 equality on all 48 layers, changed dispatch, exact OFF logits and grouped_mm adoption passed before generation. Import guard: 3 passed, 1 known legacy xfail; lint and CPU real-consumer checks passed.

Operational disclosure: initially Brian's server reported 93,445 MiB allocated and only ~20 GiB system memory available, so no model load was attempted. Memory changed externally to 115.7 GiB available with an empty GPU process list before launch. No process was touched by this task. Foreground only; no signals, training, fitting, sealed reads, or push. RUNNING.flag removed after GPU cleanup.

Artifacts: [summary](summary.json), [records](records.jsonl), [fixed reading](prewritten-reading.md), [tasks](tasks.json), [biases](biases.pt), [projection](projection.json), [source freeze](freeze.json), [runtime](runtime.json), [kernel](kernel.json), [CPU checks](cpu.json), [audit](audit.json), [run log](run.log), [inventory](artifact-inventory.json). biases.pt holds CPU float32 js/python [48,128] scaled from the saved 40b tensors and shuffled [32,6,48,128] within-layer permutations; no learned values. Shapes, bytes and SHA-256 in the inventory; retained records include all text and actual token/cache provenance.
