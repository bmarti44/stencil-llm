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

Results PENDING.
