# Check40h — release closure, masks at every change

Unregistered descriptive quick check; frozen before generation, seed40070,
24 episodes, Qwen3-30B-A3B bf16, greedy, alpha3, 64-token caps. Fit/train-on:
none. Profile-on: frozen check40b's32 cued competence replies; alpha3 was
selected in exploratory40c and explicitly requested here. Evaluated-on: fresh
synthetic arithmetic expressions disjoint from40b/40d/40f; nothing fit or tuned,
no evaluation benchmarks or sealed inputs read.

SET(JS) -> HOLD -> SWITCH(Python) -> HOLD_AFTER_SWITCH -> BACK(JS) ->
HOLD_AFTER_BACK -> CLEAR(OFF, Python default). No extra NEUTRAL turn. Fresh OFF
on each CLEAR task precedes arms. M/Z share exact SET/HOLD KV and replies, then
branch; each branch keeps its own subsequent generations. Tprime denotes T′.
M: JS bias at SET/HOLD/BACK/HOLD_AFTER_BACK, Python at SWITCH/HOLD_AFTER_SWITCH,
OFF at CLEAR. Z: same as M except OFF at SWITCH/HOLD_AFTER_SWITCH; this is the
mask+OFF SWITCH control. T′: bias OFF throughout, explicit Use JavaScript/Python
on every corresponding non-CLEAR request. No cue or cancellation at CLEAR.
All three arms mask all earlier assistant code-turn bodies at SWITCH, BACK,
and CLEAR (including broken replies, fences included, EOS/headers excluded).
Masks persist, so each change adds every body produced since the last change.
At T′ CLEAR also mask ALL prior cue-bearing USER TURNS, including their request,
role header and closure/newline, retaining assistant headers and closures.
This conservative cue-turn interpretation removes every direct text cue carrier.
No placeholders, text-history rebuild, position renumbering or downstream KV
recomputation. Reuse40f's exact every-forward 2D key mask and absolute RoPE IDs;
masked KV columns remain allocated. Surviving downstream KV can carry traces.

Fixed reading: CLOSED-RELEASE iff M valid Python>=20/24 at SWITCH, valid
JavaScript>=20/24 at BACK, valid Python>=20/24 at CLEAR, broken<=2/24 at EVERY
step, AND >=20 paired episodes have BACK JS, HOLD_AFTER_BACK JS and CLEAR Python.
The paired condition conservatively operationalizes 'after real reestablished
JS': an aggregate default cannot substitute for actual release. PARTIAL iff
at least one of SWITCH/BACK/CLEAR meets its target>=20 and broken<=2 but the
full rule fails; otherwise NOT. INCOMPLETE takes precedence if unfinished.
Z and T′ are reported separately and never rescue M. If Z SWITCH Python>=20/24,
masking alone restores the DEFAULT: any need for a new routing term is confined
to the non-default direction (and that direction's success must be measured).
Report all per-step parser languages/breakage/coarse checks, paired transitions,
fence loss (bare among all and valid outputs), R3-style ambiguous expression
echoes, OK imitation, family/token/arrow diagnostics. Parsers/coarse checker
unchanged from40f; code not executed. This tests arithmetic surface syntax,
not autonomous skill maintenance or general release across tasks.

Cost: 480 actual generations, 1369.80s
projection from40f measured per-request time and load plus25% reserve; estimated,
not a worst-case64-token guarantee. Cooperative cap1800s (0.5 GPU-h) includes
load, kernel checks and cleanup; no signals or outcome retries. Foreground only,
wait for other RUNNING.flags/compute, pid2705 exempt and never touched; require
>=68GiB available. Own RUNNING.flag removed on cleanup. Pinned .venv runtime,
raw slot0 contract on all48 gates, inherited grouped_mm/OFF and CPU mask tests.

**Result: PARTIAL.**

Complete: True; all scheduled generations complete.

M SWITCH Python 20/24, broken 4/24; BACK JS 19/24, broken 0/24; CLEAR Python 24/24, broken 0/24.

The prescribed M schedule does not close release: SWITCH exceeds the
breakage bar and the decisive non-default BACK misses20/24. CLEAR is
19 actual reestablished-JS releases plus5 Python-persistence cases.
Z's later masked BACK restores JS23/24 and CLEAR Python24/24, with zero
breakage throughout; this secondary schedule does not rescue the frozen M
reading. T′ meets every target24/24, zero breakage, including CLEAR after
masking all six cue-bearing user turns and all assistant code bodies.
These are language targets: T′ CLEAR passes the coarse task check23/24.
Episode5 is a valid bare Python lambda; the inherited coarse checker
requires a return statement and rejects that form. No scorer was changed.

| Arm | Step | JS | Python | Broken | Coarse task | Bare (valid) | Ambiguous / exact echoes |
|---|---|---:|---:|---:|---:|---:|---:|
| M | SET | 24 | 0 | 0 | 24 | 0 (0) | 0 / 0 |
| M | HOLD | 24 | 0 | 0 | 24 | 0 (0) | 0 / 0 |
| M | SWITCH | 0 | 20 | 4 | 20 | 0 (0) | 0 / 0 |
| M | HOLD_AFTER_SWITCH | 0 | 20 | 4 | 20 | 0 (0) | 0 / 0 |
| M | BACK | 19 | 5 | 0 | 24 | 0 (0) | 0 / 0 |
| M | HOLD_AFTER_BACK | 19 | 5 | 0 | 24 | 0 (0) | 0 / 0 |
| M | CLEAR | 0 | 24 | 0 | 24 | 0 (0) | 0 / 0 |
| Z | SET | 24 | 0 | 0 | 24 | 0 (0) | 0 / 0 |
| Z | HOLD | 24 | 0 | 0 | 24 | 0 (0) | 0 / 0 |
| Z | SWITCH | 0 | 24 | 0 | 24 | 0 (0) | 0 / 0 |
| Z | HOLD_AFTER_SWITCH | 0 | 24 | 0 | 24 | 0 (0) | 0 / 0 |
| Z | BACK | 23 | 1 | 0 | 24 | 0 (0) | 0 / 0 |
| Z | HOLD_AFTER_BACK | 23 | 1 | 0 | 24 | 0 (0) | 0 / 0 |
| Z | CLEAR | 0 | 24 | 0 | 24 | 0 (0) | 0 / 0 |
| Tprime | SET | 24 | 0 | 0 | 24 | 0 (0) | 0 / 0 |
| Tprime | HOLD | 24 | 0 | 0 | 24 | 0 (0) | 0 / 0 |
| Tprime | SWITCH | 0 | 24 | 0 | 24 | 0 (0) | 0 / 0 |
| Tprime | HOLD_AFTER_SWITCH | 0 | 24 | 0 | 24 | 0 (0) | 0 / 0 |
| Tprime | BACK | 24 | 0 | 0 | 24 | 1 (1) | 0 / 0 |
| Tprime | HOLD_AFTER_BACK | 24 | 0 | 0 | 24 | 1 (1) | 0 / 0 |
| Tprime | CLEAR | 0 | 24 | 0 | 23 | 1 (1) | 0 / 0 |

Every scheduled cell has denominator24. Coarse task means the unchanged
parser plus expression-preservation check, not execution of generated code.

Frozen M conditions: `{"BACK": false, "CLEAR": true, "SWITCH": false, "every_step_breakage": false, "reestablished_js_release": false}`.
Paired BACK JS + HOLD_AFTER_BACK JS + CLEAR Python: M 19/24, Z 23/24, T′ 24/24.

Fresh OFF CLEAR: 24/24 Python.

Z meets20/24 Python at SWITCH: masking plus removal of the old bias
restores the DEFAULT without a new Python routing term. Any need for
a new routing term is confined to the non-default direction; assess
its reliability using M BACK and its breakage above.

Fence loss and R3-style echoes are separate diagnostics, not unnamed
parser failures. The table reports all bare outputs and bare valid outputs;
ambiguous means both language parsers accept the extracted code.
No ambiguous expression echoes or OK imitation occurred in any arm.
M/Z retain fences on every reply. T′ loses fences on one valid reply at
BACK and HOLD_AFTER_BACK (episode13), and one at CLEAR (episode5).
M's broken episodes2,5,10,14 all omit a closing parenthesis at SWITCH
and repeat that defect at HOLD_AFTER_SWITCH: eight invalid replies from
four episodes, not ambiguous R3-style echoes. SWITCH onset families are
screen_1 (three of eight) and screen_0 (one of eight).

- M SWITCH: ambiguous episodes []; exact expression echoes []; OK replies [].
- M BACK: ambiguous episodes []; exact expression echoes []; OK replies [].
- M CLEAR: ambiguous episodes []; exact expression echoes []; OK replies [].
- Tprime SWITCH: ambiguous episodes []; exact expression echoes []; OK replies [].
- Tprime BACK: ambiguous episodes []; exact expression echoes []; OK replies [].
- Tprime CLEAR: ambiguous episodes []; exact expression echoes []; OK replies [].
- Z SWITCH: ambiguous episodes []; exact expression echoes []; OK replies [].
- Z BACK: ambiguous episodes []; exact expression echoes []; OK replies [].
- Z CLEAR: ambiguous episodes []; exact expression echoes []; OK replies [].

Broken reply inventory (literal text; shared prefix records identified in JSONL):

- Episode2 M SWITCH, screen_1, ['invalid']: `"```python\ndef solve_release_2_2():\n    return (32 * 15) + (11 * 39\n```"`
- Episode2 M HOLD_AFTER_SWITCH, screen_2, ['invalid']: `"```python\ndef solve_release_2_3():\n    return (15 - 24) - (31 + 14\n```"`
- Episode5 M SWITCH, screen_1, ['invalid']: `"```python\ndef solve_release_5_2():\n    return (24*16) + (35*24\n```"`
- Episode5 M HOLD_AFTER_SWITCH, screen_2, ['invalid']: `"```python\ndef solve_release_5_3():\n    return (14-9) - (20+37\n```"`
- Episode10 M SWITCH, screen_0, ['invalid']: `"```python\ndef solve_release_10_2():\n    return (15 + 31) * (19 - 2\n```"`
- Episode10 M HOLD_AFTER_SWITCH, screen_1, ['invalid']: `"```python\ndef solve_release_10_3():\n    return (28 * 31) + (19 * 19\n```"`
- Episode14 M SWITCH, screen_1, ['invalid']: `"```python\ndef solve_release_14_2():\n    return (24*31) + (15*14\n```"`
- Episode14 M HOLD_AFTER_SWITCH, screen_2, ['invalid']: `"```python\ndef solve_release_14_3():\n    return (6-4) - (22+29\n```"`

528 records / 480 actual generations / 14603 generated tokens. Truncated actual generations 0; cost-stopped 0.
GPU time including load/checks/cleanup: 1347.560/1800s (22.46/30min); overrun 0.000s.

Audit: every score/token/history/bias, shared prefix, cue span, mask event,
prefill/decode/closure mask and absolute position replayed on CPU. Summary
and fixed decision reconstructed. All48 raw router contracts and adopted
grouped_mm/OFF equality checked in runtime artifacts. Frozen recipe
`3f1a8aac` precedes inference. No fitting, sealed input, signal, background
launch or push. RUNNING.flag removed after cleanup.

Interpretation remains limited to these arithmetic surface-syntax tasks.
All body masks retain headers/closures and stale downstream KV. T′ CLEAR
also removes six complete cue-bearing user turns, including their requests;
it therefore changes more prompt content than M/Z. HOLD co-occurs with
current bias and visible new answers and does not isolate maintenance.
