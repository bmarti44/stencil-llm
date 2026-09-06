# Check 40f — RELEASE: router bias + prior-answer masking

Unregistered, disclosed. Fixed before generation, seed40060, Qwen3-30B-A3B bf16,
greedy, alpha3, cap64. Fit/train-on: none. Frozen directions from check40b's32
cued competence replies, alpha3 selected in exploratory40c then explicitly
requested here. Evaluated-on: 24 new synthetic episodes, same three arithmetic
families, expressions disjoint from40b/40d. No benchmarks or sealed inputs.

Schedule: SET(JS) -> NEUTRAL(OK) -> HOLD(JS) -> SWITCH(Python) ->
HOLD_AFTER_SWITCH(Python sustained) -> BACK(JS) -> CLEAR(OFF). Code prompts
are distinct and uncued except T. BACK ensures CLEAR starts after renewed JS.
R1-R4 share one actual generated SET/NEUTRAL/HOLD prefix, then branch exact
copies of its KV and text. Each continuation retains its own generated history.
Fresh OFF on the CLEAR task precedes the arms. Shared prefix rows identify their
source generation; shared generations are counted once in cost.

R1: bias changes only. R2: bias changes + mask ALL prior assistant code bodies
at SWITCH and again at CLEAR. R3: same masks, JS bias unchanged throughout.
R4: R2 plus a one-line neutral `.` body in each masked answer's original first
body position. T: bias OFF; Use JavaScript at SET/HOLD/BACK, Use Python at
SWITCH/HOLD_AFTER_SWITCH; uncued NEUTRAL/CLEAR; same mask events as R2.
Masks persist after each event; later answers remain visible until next event.
Assistant code body means generated tokens on code-request turns, excluding EOS;
keep all user/system tokens, assistant headers/empty think prefix, turn closures
and neutral pairs, even if code was broken. Nothing removed from text history.

Mask implementation: 2D key attention mask at every prefill/decode/closure,
zeros for those exact absolute positions. Full KV columns and absolute RoPE
positions remain. Old downstream KV is NOT recomputed and may carry traces of
masked answers. R4 forwards `.` at the body's original first position using its
surviving causal prefix and current bias, replaces only that KV column, masks
the rest of the body; literal history and original token provenance retained.
Previously inserted placeholders survive subsequent events; no cue in them.
No history rebuild, position renumbering, learned value, tuning or outcome retry.

Fixed reading: RELEASE WORKS iff the SAME R2 or R4 has valid unbroken Python
>=26/32 at BOTH SWITCH/CLEAR, <=2/32 broken at both, and R3 valid Python <=4/32
at BOTH events. PARTIAL iff at least one event passes in R2/R4 with its R3
control and breakage bars, but no arm passes both. Else NOT. INCOMPLETE takes
precedence if execution unfinished. For selected24, conservative equivalents:
Python>=20/24, broken<=1/24, R3<=3/24. HOLD_AFTER_SWITCH reported separately.
Also report SET/HOLD/BACK success, actual JS->Python paired transitions, fresh
OFF defaults, all parser/coarse/family/first-token/fence/arrow diagnostics.
These thresholds are descriptive, not a registered existence test. Release
requires masking in addition to routing only if combined arms meet bars while
R1 fails; R3 reports whether masking alone suffices under sustained JS bias.
If JS was not induced/reestablished, distinguish defaults from actual release.

Cost: select24 before outcomes. 32 capped projection6580.36s;
24 capped projection5058.36s. 648
generations, cap64, 15tok/s, load393.89s (40d), 1s/request prefill, 2s per
placeholder forward, 25% reserve; total5058.36s <5400s.
Cooperative deadline including load/kernel/cleanup; no signals. Foreground;
review-lock/other RUNNING.flag/GPU check, pid2705 exempt, >=68GiB MemAvailable.
Commit recipe before GPU run; pin .venv transformers5.16.1, raw slot0 contract
all48 gates, inherited grouped_mm dispatch/OFF test, CPU real mask consumer test.

Results PENDING.
