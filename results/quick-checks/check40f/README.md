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

## Results

**RELEASE WORKS** (24 episodes; pre-run resource fallback from32).

**Masking was required in addition to the routing change for successful SWITCH in this comparison.** R2 produced valid Python23/24 at SWITCH and HOLD_AFTER_SWITCH (broken1 each); R1 bias-only produced Python0/24. R3 mask-only under unchanged JS bias produced Python0/24, JS18/24 and broken6/24 at SWITCH/CLEAR; this control does not establish clean JS maintenance. R4's neutral-period replacement failed: all24 replies at SWITCH/CLEAR were invalid period copies.

**CLEAR meets the frozen output target but is not an independent JS-release success.** R2 CLEAR is valid Python24/24, broken0; its BACK restored JS0/24 (Python23, broken1). Consequently BACK->CLEAR is23 Python->Python plus1 broken->Python, with zero reestablished-JS cases. R2 shows the tested SWITCH benefit and satisfies the specified reading, but a fresh release-from-JS claim at CLEAR remains untested. Text+mask T switches/holds Python24/24 and restores JS24/24 at BACK, yet CLEAR is JS23/24 and broken1, Python0.

R2 episode23 omitted a closing parenthesis at SWITCH, HOLD_AFTER_SWITCH and BACK, then returned valid Python at CLEAR. T episode19 CLEAR omitted the function keyword. Neither was token-capped. Breakage remains counted without repair. These are surface-syntax results on fresh arithmetic expressions, not general reversible computation control.

| Arm | Step | N | Valid JS | Valid Python | Broken | Coarse task pass | Truncated | => | -> |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| R1 | SET | 24 | 24 | 0 | 0 | 24 | 0 | 0 | 0 |
| R1 | HOLD | 24 | 24 | 0 | 0 | 24 | 0 | 0 | 0 |
| R1 | SWITCH | 24 | 24 | 0 | 0 | 24 | 0 | 0 | 0 |
| R1 | HOLD_AFTER_SWITCH | 24 | 24 | 0 | 0 | 24 | 0 | 0 | 0 |
| R1 | BACK | 24 | 24 | 0 | 0 | 24 | 0 | 0 | 0 |
| R1 | CLEAR | 24 | 24 | 0 | 0 | 24 | 0 | 0 | 0 |
| R2 | SET | 24 | 24 | 0 | 0 | 24 | 0 | 0 | 0 |
| R2 | HOLD | 24 | 24 | 0 | 0 | 24 | 0 | 0 | 0 |
| R2 | SWITCH | 24 | 0 | 23 | 1 | 23 | 0 | 0 | 0 |
| R2 | HOLD_AFTER_SWITCH | 24 | 0 | 23 | 1 | 23 | 0 | 0 | 0 |
| R2 | BACK | 24 | 0 | 23 | 1 | 23 | 0 | 0 | 0 |
| R2 | CLEAR | 24 | 0 | 24 | 0 | 24 | 0 | 0 | 0 |
| R3 | SET | 24 | 24 | 0 | 0 | 24 | 0 | 0 | 0 |
| R3 | HOLD | 24 | 24 | 0 | 0 | 24 | 0 | 0 | 0 |
| R3 | SWITCH | 24 | 18 | 0 | 6 | 12 | 0 | 5 | 0 |
| R3 | HOLD_AFTER_SWITCH | 24 | 18 | 0 | 6 | 12 | 0 | 5 | 0 |
| R3 | BACK | 24 | 18 | 0 | 6 | 12 | 0 | 5 | 0 |
| R3 | CLEAR | 24 | 18 | 0 | 6 | 14 | 0 | 4 | 0 |
| R4 | SET | 24 | 24 | 0 | 0 | 24 | 0 | 0 | 0 |
| R4 | HOLD | 24 | 24 | 0 | 0 | 24 | 0 | 0 | 0 |
| R4 | SWITCH | 24 | 0 | 0 | 24 | 0 | 0 | 0 | 0 |
| R4 | HOLD_AFTER_SWITCH | 24 | 0 | 0 | 24 | 0 | 0 | 0 | 0 |
| R4 | BACK | 24 | 0 | 0 | 24 | 0 | 0 | 0 | 0 |
| R4 | CLEAR | 24 | 0 | 0 | 24 | 0 | 0 | 0 | 0 |
| T | SET | 24 | 24 | 0 | 0 | 24 | 0 | 0 | 0 |
| T | HOLD | 24 | 24 | 0 | 0 | 24 | 0 | 0 | 0 |
| T | SWITCH | 24 | 0 | 24 | 0 | 24 | 0 | 0 | 0 |
| T | HOLD_AFTER_SWITCH | 24 | 0 | 24 | 0 | 24 | 0 | 0 | 0 |
| T | BACK | 24 | 24 | 0 | 0 | 24 | 0 | 0 | 0 |
| T | CLEAR | 24 | 23 | 0 | 1 | 20 | 0 | 3 | 0 |

Fixed combined-arm pass flags: {"R2": {"CLEAR": true, "SWITCH": true}, "R4": {"CLEAR": false, "SWITCH": false}}.

R1: SWITCH Python0/24, HOLD_AFTER_SWITCH Python0/24, CLEAR Python0/24.
R2: SWITCH Python23/24, HOLD_AFTER_SWITCH Python23/24, CLEAR Python24/24.
R3: SWITCH Python0/24, HOLD_AFTER_SWITCH Python0/24, CLEAR Python0/24.
R4: SWITCH Python0/24, HOLD_AFTER_SWITCH Python0/24, CLEAR Python0/24.
T: SWITCH Python24/24, HOLD_AFTER_SWITCH Python24/24, CLEAR Python0/24.

Interpretation: apply the fixed reading above without replacing it with a post-outcome criterion. Compare R2/R4 with the identical-prefix R1 to assess the added context intervention at SWITCH. R3 measures masking under sustained JS bias; its broken replies are failures, not evidence of successfully maintained JavaScript.
The BACK->CLEAR transitions below determine whether CLEAR is an actual new release or already-Python persistence. A Python CLEAR following a failed JS BACK meets the frozen output-language target but does not independently demonstrate release from reestablished JS. Likewise, a high HOLD_AFTER_SWITCH rate co-occurs with retained Python answers and sustained bias.

Fresh OFF CLEAR default: Python24/24, JS0/24, broken0/24.

### Paired language transitions

| Arm | Transition | Counts |
|---|---|---|
| R1 | BACK->CLEAR | {"JavaScript -> JavaScript": 24} |
| R1 | HOLD->SWITCH | {"JavaScript -> JavaScript": 24} |
| R1 | HOLD_AFTER_SWITCH->BACK | {"JavaScript -> JavaScript": 24} |
| R1 | SET->HOLD | {"JavaScript -> JavaScript": 24} |
| R1 | SWITCH->HOLD_AFTER_SWITCH | {"JavaScript -> JavaScript": 24} |
| R2 | BACK->CLEAR | {"Python -> Python": 23, "broken -> Python": 1} |
| R2 | HOLD->SWITCH | {"JavaScript -> Python": 23, "JavaScript -> broken": 1} |
| R2 | HOLD_AFTER_SWITCH->BACK | {"Python -> Python": 23, "broken -> broken": 1} |
| R2 | SET->HOLD | {"JavaScript -> JavaScript": 24} |
| R2 | SWITCH->HOLD_AFTER_SWITCH | {"Python -> Python": 23, "broken -> broken": 1} |
| R3 | BACK->CLEAR | {"JavaScript -> JavaScript": 18, "broken -> broken": 6} |
| R3 | HOLD->SWITCH | {"JavaScript -> JavaScript": 18, "JavaScript -> broken": 6} |
| R3 | HOLD_AFTER_SWITCH->BACK | {"JavaScript -> JavaScript": 18, "broken -> broken": 6} |
| R3 | SET->HOLD | {"JavaScript -> JavaScript": 24} |
| R3 | SWITCH->HOLD_AFTER_SWITCH | {"JavaScript -> JavaScript": 18, "broken -> broken": 6} |
| R4 | BACK->CLEAR | {"broken -> broken": 24} |
| R4 | HOLD->SWITCH | {"JavaScript -> broken": 24} |
| R4 | HOLD_AFTER_SWITCH->BACK | {"broken -> broken": 24} |
| R4 | SET->HOLD | {"JavaScript -> JavaScript": 24} |
| R4 | SWITCH->HOLD_AFTER_SWITCH | {"broken -> broken": 24} |
| T | BACK->CLEAR | {"JavaScript -> JavaScript": 23, "JavaScript -> broken": 1} |
| T | HOLD->SWITCH | {"JavaScript -> Python": 24} |
| T | HOLD_AFTER_SWITCH->BACK | {"Python -> JavaScript": 24} |
| T | SET->HOLD | {"JavaScript -> JavaScript": 24} |
| T | SWITCH->HOLD_AFTER_SWITCH | {"Python -> Python": 24} |

### Family and output diagnostics

| Arm | Step | Family | Broken / N |
|---|---|---|---:|
| R1 | BACK | screen_0 | 0/8 |
| R1 | BACK | screen_1 | 0/8 |
| R1 | BACK | screen_2 | 0/8 |
| R1 | CLEAR | screen_0 | 0/8 |
| R1 | CLEAR | screen_1 | 0/8 |
| R1 | CLEAR | screen_2 | 0/8 |
| R1 | HOLD | screen_0 | 0/8 |
| R1 | HOLD | screen_1 | 0/8 |
| R1 | HOLD | screen_2 | 0/8 |
| R1 | HOLD_AFTER_SWITCH | screen_0 | 0/8 |
| R1 | HOLD_AFTER_SWITCH | screen_1 | 0/8 |
| R1 | HOLD_AFTER_SWITCH | screen_2 | 0/8 |
| R1 | SET | screen_0 | 0/8 |
| R1 | SET | screen_1 | 0/8 |
| R1 | SET | screen_2 | 0/8 |
| R1 | SWITCH | screen_0 | 0/8 |
| R1 | SWITCH | screen_1 | 0/8 |
| R1 | SWITCH | screen_2 | 0/8 |
| R2 | BACK | screen_0 | 1/8 |
| R2 | BACK | screen_1 | 0/8 |
| R2 | BACK | screen_2 | 0/8 |
| R2 | CLEAR | screen_0 | 0/8 |
| R2 | CLEAR | screen_1 | 0/8 |
| R2 | CLEAR | screen_2 | 0/8 |
| R2 | HOLD | screen_0 | 0/8 |
| R2 | HOLD | screen_1 | 0/8 |
| R2 | HOLD | screen_2 | 0/8 |
| R2 | HOLD_AFTER_SWITCH | screen_0 | 0/8 |
| R2 | HOLD_AFTER_SWITCH | screen_1 | 0/8 |
| R2 | HOLD_AFTER_SWITCH | screen_2 | 1/8 |
| R2 | SET | screen_0 | 0/8 |
| R2 | SET | screen_1 | 0/8 |
| R2 | SET | screen_2 | 0/8 |
| R2 | SWITCH | screen_0 | 0/8 |
| R2 | SWITCH | screen_1 | 1/8 |
| R2 | SWITCH | screen_2 | 0/8 |
| R3 | BACK | screen_0 | 0/8 |
| R3 | BACK | screen_1 | 6/8 |
| R3 | BACK | screen_2 | 0/8 |
| R3 | CLEAR | screen_0 | 0/8 |
| R3 | CLEAR | screen_1 | 0/8 |
| R3 | CLEAR | screen_2 | 6/8 |
| R3 | HOLD | screen_0 | 0/8 |
| R3 | HOLD | screen_1 | 0/8 |
| R3 | HOLD | screen_2 | 0/8 |
| R3 | HOLD_AFTER_SWITCH | screen_0 | 6/8 |
| R3 | HOLD_AFTER_SWITCH | screen_1 | 0/8 |
| R3 | HOLD_AFTER_SWITCH | screen_2 | 0/8 |
| R3 | SET | screen_0 | 0/8 |
| R3 | SET | screen_1 | 0/8 |
| R3 | SET | screen_2 | 0/8 |
| R3 | SWITCH | screen_0 | 0/8 |
| R3 | SWITCH | screen_1 | 0/8 |
| R3 | SWITCH | screen_2 | 6/8 |
| R4 | BACK | screen_0 | 8/8 |
| R4 | BACK | screen_1 | 8/8 |
| R4 | BACK | screen_2 | 8/8 |
| R4 | CLEAR | screen_0 | 8/8 |
| R4 | CLEAR | screen_1 | 8/8 |
| R4 | CLEAR | screen_2 | 8/8 |
| R4 | HOLD | screen_0 | 0/8 |
| R4 | HOLD | screen_1 | 0/8 |
| R4 | HOLD | screen_2 | 0/8 |
| R4 | HOLD_AFTER_SWITCH | screen_0 | 8/8 |
| R4 | HOLD_AFTER_SWITCH | screen_1 | 8/8 |
| R4 | HOLD_AFTER_SWITCH | screen_2 | 8/8 |
| R4 | SET | screen_0 | 0/8 |
| R4 | SET | screen_1 | 0/8 |
| R4 | SET | screen_2 | 0/8 |
| R4 | SWITCH | screen_0 | 8/8 |
| R4 | SWITCH | screen_1 | 8/8 |
| R4 | SWITCH | screen_2 | 8/8 |
| T | BACK | screen_0 | 0/8 |
| T | BACK | screen_1 | 0/8 |
| T | BACK | screen_2 | 0/8 |
| T | CLEAR | screen_0 | 1/8 |
| T | CLEAR | screen_1 | 0/8 |
| T | CLEAR | screen_2 | 0/8 |
| T | HOLD | screen_0 | 0/8 |
| T | HOLD | screen_1 | 0/8 |
| T | HOLD | screen_2 | 0/8 |
| T | HOLD_AFTER_SWITCH | screen_0 | 0/8 |
| T | HOLD_AFTER_SWITCH | screen_1 | 0/8 |
| T | HOLD_AFTER_SWITCH | screen_2 | 0/8 |
| T | SET | screen_0 | 0/8 |
| T | SET | screen_1 | 0/8 |
| T | SET | screen_2 | 0/8 |
| T | SWITCH | screen_0 | 0/8 |
| T | SWITCH | screen_1 | 0/8 |
| T | SWITCH | screen_2 | 0/8 |

| Arm | Step | First token | First three tokens | Fence labels |
|---|---|---|---|---|
| R1 | BACK | {"&#96;&#96;&#96;": 24} | {"&#96;&#96;&#96;javascript\n": 24} | {"javascript": 24} |
| R1 | CLEAR | {"&#96;&#96;&#96;": 24} | {"&#96;&#96;&#96;javascript\n": 24} | {"javascript": 24} |
| R1 | HOLD | {"&#96;&#96;&#96;": 24} | {"&#96;&#96;&#96;javascript\n": 24} | {"javascript": 24} |
| R1 | HOLD_AFTER_SWITCH | {"&#96;&#96;&#96;": 24} | {"&#96;&#96;&#96;javascript\n": 24} | {"javascript": 24} |
| R1 | NEUTRAL | {"OK": 24} | {"OK<&#124;im_end&#124;>": 24} | {"(bare)": 24} |
| R1 | SET | {"&#96;&#96;&#96;": 24} | {"&#96;&#96;&#96;javascript\n": 24} | {"javascript": 24} |
| R1 | SWITCH | {"&#96;&#96;&#96;": 24} | {"&#96;&#96;&#96;javascript\n": 24} | {"javascript": 24} |
| R2 | BACK | {"&#96;&#96;&#96;": 24} | {"&#96;&#96;&#96;python\n": 24} | {"python": 24} |
| R2 | CLEAR | {"&#96;&#96;&#96;": 24} | {"&#96;&#96;&#96;python\n": 24} | {"python": 24} |
| R2 | HOLD | {"&#96;&#96;&#96;": 24} | {"&#96;&#96;&#96;javascript\n": 24} | {"javascript": 24} |
| R2 | HOLD_AFTER_SWITCH | {"&#96;&#96;&#96;": 24} | {"&#96;&#96;&#96;python\n": 24} | {"python": 24} |
| R2 | NEUTRAL | {"OK": 24} | {"OK<&#124;im_end&#124;>": 24} | {"(bare)": 24} |
| R2 | SET | {"&#96;&#96;&#96;": 24} | {"&#96;&#96;&#96;javascript\n": 24} | {"javascript": 24} |
| R2 | SWITCH | {"&#96;&#96;&#96;": 24} | {"&#96;&#96;&#96;python\n": 24} | {"python": 24} |
| R3 | BACK | {"((": 6, "(()": 4, "&#96;&#96;&#96;": 11, "function": 2, "solve": 1} | {"(() => {": 4, "((10": 1, "((19": 2, "((34": 1, "((36": 1, "((4*": 1, "&#96;&#96;&#96;javascript\n": 11, "function solve_release": 2, "solve_release_": 1} | {"(bare)": 13, "javascript": 11} |
| R3 | CLEAR | {"((": 2, "(()": 2, "OK": 4, "&#96;&#96;&#96;": 4, "function": 10, "solve": 2} | {"(() => {": 2, "((38": 1, "((8-": 1, "OK<&#124;im_end&#124;>": 4, "&#96;&#96;&#96;javascript\n": 4, "function solve_release": 10, "solve_release_": 2} | {"(bare)": 20, "javascript": 4} |
| R3 | HOLD | {"&#96;&#96;&#96;": 24} | {"&#96;&#96;&#96;javascript\n": 24} | {"javascript": 24} |
| R3 | HOLD_AFTER_SWITCH | {"((": 6, "(()": 4, "&#96;&#96;&#96;": 11, "function": 2, "solve": 1} | {"(() => {": 4, "((12": 1, "((20": 1, "((35": 1, "((39": 1, "((5+": 1, "((6+": 1, "&#96;&#96;&#96;javascript\n": 11, "function solve_release": 2, "solve_release_": 1} | {"(bare)": 13, "javascript": 11} |
| R3 | NEUTRAL | {"OK": 24} | {"OK<&#124;im_end&#124;>": 24} | {"(bare)": 24} |
| R3 | SET | {"&#96;&#96;&#96;": 24} | {"&#96;&#96;&#96;javascript\n": 24} | {"javascript": 24} |
| R3 | SWITCH | {"((": 6, "(()": 4, "&#96;&#96;&#96;": 11, "function": 2, "solve": 1} | {"(() => {": 4, "((22": 1, "((23": 1, "((29": 1, "((30": 1, "((34": 1, "((37": 1, "&#96;&#96;&#96;javascript\n": 11, "function solve_release": 2, "solve_release_": 1} | {"(bare)": 13, "javascript": 11} |
| R4 | BACK | {".": 24} | {".<&#124;im_end&#124;>": 24} | {"(bare)": 24} |
| R4 | CLEAR | {".": 24} | {".<&#124;im_end&#124;>": 24} | {"(bare)": 24} |
| R4 | HOLD | {"&#96;&#96;&#96;": 24} | {"&#96;&#96;&#96;javascript\n": 24} | {"javascript": 24} |
| R4 | HOLD_AFTER_SWITCH | {".": 24} | {".<&#124;im_end&#124;>": 24} | {"(bare)": 24} |
| R4 | NEUTRAL | {"OK": 24} | {"OK<&#124;im_end&#124;>": 24} | {"(bare)": 24} |
| R4 | SET | {"&#96;&#96;&#96;": 24} | {"&#96;&#96;&#96;javascript\n": 24} | {"javascript": 24} |
| R4 | SWITCH | {".": 24} | {".<&#124;im_end&#124;>": 24} | {"(bare)": 24} |
| T | BACK | {"&#96;&#96;&#96;": 11, "function": 13} | {"&#96;&#96;&#96;javascript\n": 11, "function solve_release": 13} | {"(bare)": 13, "javascript": 11} |
| T | CLEAR | {"function": 20, "solve": 4} | {"function solve_release": 20, "solve_release_": 4} | {"(bare)": 24} |
| T | HOLD | {"&#96;&#96;&#96;": 24} | {"&#96;&#96;&#96;javascript\n": 24} | {"javascript": 24} |
| T | HOLD_AFTER_SWITCH | {"&#96;&#96;&#96;": 11, "def": 13} | {"&#96;&#96;&#96;python\n": 11, "def solve_release": 13} | {"(bare)": 13, "python": 11} |
| T | NEUTRAL | {"OK": 24} | {"OK<&#124;im_end&#124;>": 24} | {"(bare)": 24} |
| T | SET | {"&#96;&#96;&#96;": 24} | {"&#96;&#96;&#96;javascript\n": 24} | {"javascript": 24} |
| T | SWITCH | {"&#96;&#96;&#96;": 11, "def": 13} | {"&#96;&#96;&#96;python\n": 11, "def solve_release": 13} | {"(bare)": 13, "python": 11} |

Neutral literal OK counts (non-code; excluded from code breakage): {"R1": 24, "R2": 24, "R3": 24, "R4": 24, "T": 24}.
Scored breakage flags (includes shared prefix rows): {"ambiguous": 24, "invalid": 100}.

### Execution and audit

648 actual generations, 864 arm records (shared prefixes identified), 14406 generated tokens. GPU allocation 1376.87s = 22.95/90min including loading, kernel checks and cleanup; overrun0.00s. Peak allocated57.64GiB. all scheduled generations complete.

Recipe committed at e570e74c before runtime launch; this is an unregistered disclosed quick check with a pre-generation Git anchor, not a registered benchmark. Nothing fit/trained or tuned. No sealed inputs, signals, background launches or push.

Audit reconstructs every score, decoded output, actual retained token prefix, mask event, placeholder position/context, per-forward mask and absolute position, shared prefix, bias schedule, aggregate and fixed reading on CPU. Tiny real-model SDPA tests establish masked-K/V poisoning invariance and physical-eviction equivalence; retained-position and placeholder-column isolation pass. Runtime verifies raw linear router slot0 on all48 layers, changed expert dispatch, exact OFF logits and grouped_mm adoption. Import guard3 passed/1 known legacy xfail.

The literal text history remains intact. R2/R3/T mask generated code-answer bodies; R4 substitutes neutral period K/V only in each original first body position, with the other body positions masked. Downstream K/V, user turns, empty think/header tokens, turn closures and neutral pairs remain. T also retains earlier explicit user language cues. Thus masking here is not a complete erasure of all historical language information. HOLD uses sustained bias and retained new answers; it does not isolate bias-only maintenance.

Artifacts: [records](records.jsonl), [summary](summary.json), [audit](audit.json), [tasks](tasks.json), [frozen reading](prewritten-reading.md), [projection](projection.json), [freeze](freeze.json), [runtime](runtime.json), [kernel](kernel.json), [CPU checks](cpu.json), [resources](resources.json), [run log](run.log), [ledger](ledger.md), [inventory](artifact-inventory.json). `biases.pt`: CPU float32 js/python tensors [48,128], exactly40d alpha3 directions scaled from40b; no learned values.
