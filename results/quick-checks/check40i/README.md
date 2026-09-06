# Check40i — Z primary release closure

Unregistered, disclosed descriptive quick check; seed40080,24 fresh episodes,
Qwen3-30B-A3B bf16,greedy,alpha3,64-token caps. Fit/train-on:none.
Profile-on:frozen40b competence replies; alpha3 from exploratory40c, requested
here without tuning. Evaluated-on:fresh synthetic arithmetic expressions,
disjoint from40b/40d/40f/40h. No benchmarks or sealed inputs read.

Fixed BEFORE inference: Z PRIMARY SET(JS bias) -> HOLD -> SWITCH(bias OFF +
mask) -> HOLD_AFTER_SWITCH -> BACK(JS bias + mask) -> HOLD_AFTER_BACK ->
CLEAR(bias OFF + mask). Zc and S share Z's exact first4 replies and KV, then
branch: Zc BACK/HOLD_AFTER_BACK bias OFF; S BACK/HOLD_AFTER_BACK frozen40b
shuffled JS direction scaled to alpha3. Both mask at BACK and CLEAR; both
bias OFF at CLEAR. OFF:no bias or mask, full7-step retained-history arm.
No text cues, NEUTRAL turn, or extra fresh-OFF generation. 672 logical records,
480 actual generations. Each branch retains its own subsequent answers.

Masks reuse40h/40f position-preserving key eviction of ALL previous assistant
code-turn bodies at SWITCH/BACK/CLEAR, including fences and broken replies,
excluding EOS/headers. Persistent masks apply at every forward; no placeholders,
KV recomputation or position renumbering. Surviving downstream KV may carry traces.

Fixed reading:CLOSED-RELEASE iff Z Python>=20/24 at SWITCH, JS>=20/24 at BACK,
Python>=20/24 at CLEAR; Z broken<=2/24 at EVERY step; Zc JS<=4/24 and S JS<=4/24
at BACK. Paired real releases additionally require>=20 episodes with SET JS +
HOLD JS + SWITCH Python and>=20 with BACK JS + HOLD_AFTER_BACK JS + CLEAR Python.
This conservatively fixes the user's paired-real-releases requirement.
PARTIAL iff any primary SWITCH/BACK/CLEAR target>=20 and broken<=2 but the full
conjunction fails; NOT otherwise. INCOMPLETE takes precedence if unfinished.
Controls are reported in full; primary breakage bar applies to Z.
Report fences/bare valid replies, missing-closing-parenthesis defects (broken
code with positive '(' minus ')' balance), other parser breaks, coarse checks,
paired counts and cost. No scorer change; coarse checks do not execute code.

Projected cost:1684.45s from40h; cooperative cap1800s
(0.5 GPU-h) includes load/kernel checks/cleanup, with request/token reserves.
Foreground only; wait for any other Stencil flag/compute process; Brian pid2705
exempt and never touched. No signals, retries, fitting, background launch or push.
Claim limited to arithmetic language surface syntax under this schedule;
HOLD with current bias and visible own answers does not isolate maintenance.
Prior negated-JS bias is not used; no claim about independently profiled Python.

**Result: CLOSED-RELEASE.**

Complete: True; all scheduled generations complete.

Z SWITCH Python 24/24; BACK JS 23/24; CLEAR Python 24/24.
Paired real SWITCH releases 24/24; paired real CLEAR releases 23/24; both paired releases in the same episode 23/24 (diagnostic).
Zc BACK JS 0/24; S BACK JS 0/24.
Z CLEAR paired-release cases 23/24; outside the paired criterion 1/24.
Z BACK miss episodes: [2].

| Arm | Step | JS | Python | Broken | Coarse task | Fenced | Bare (valid) | Missing paren |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Z | SET | 24 | 0 | 0 | 24 | 24 | 0 (0) | 0 |
| Z | HOLD | 24 | 0 | 0 | 24 | 24 | 0 (0) | 0 |
| Z | SWITCH | 0 | 24 | 0 | 24 | 24 | 0 (0) | 0 |
| Z | HOLD_AFTER_SWITCH | 0 | 24 | 0 | 24 | 24 | 0 (0) | 0 |
| Z | BACK | 23 | 1 | 0 | 24 | 24 | 0 (0) | 0 |
| Z | HOLD_AFTER_BACK | 23 | 1 | 0 | 24 | 24 | 0 (0) | 0 |
| Z | CLEAR | 0 | 24 | 0 | 24 | 24 | 0 (0) | 0 |
| Zc | SET | 24 | 0 | 0 | 24 | 24 | 0 (0) | 0 |
| Zc | HOLD | 24 | 0 | 0 | 24 | 24 | 0 (0) | 0 |
| Zc | SWITCH | 0 | 24 | 0 | 24 | 24 | 0 (0) | 0 |
| Zc | HOLD_AFTER_SWITCH | 0 | 24 | 0 | 24 | 24 | 0 (0) | 0 |
| Zc | BACK | 0 | 24 | 0 | 24 | 24 | 0 (0) | 0 |
| Zc | HOLD_AFTER_BACK | 0 | 24 | 0 | 24 | 24 | 0 (0) | 0 |
| Zc | CLEAR | 0 | 24 | 0 | 24 | 24 | 0 (0) | 0 |
| S | SET | 24 | 0 | 0 | 24 | 24 | 0 (0) | 0 |
| S | HOLD | 24 | 0 | 0 | 24 | 24 | 0 (0) | 0 |
| S | SWITCH | 0 | 24 | 0 | 24 | 24 | 0 (0) | 0 |
| S | HOLD_AFTER_SWITCH | 0 | 24 | 0 | 24 | 24 | 0 (0) | 0 |
| S | BACK | 0 | 24 | 0 | 24 | 24 | 0 (0) | 0 |
| S | HOLD_AFTER_BACK | 0 | 24 | 0 | 24 | 24 | 0 (0) | 0 |
| S | CLEAR | 0 | 24 | 0 | 24 | 24 | 0 (0) | 0 |
| OFF | SET | 0 | 24 | 0 | 24 | 24 | 0 (0) | 0 |
| OFF | HOLD | 0 | 24 | 0 | 24 | 24 | 0 (0) | 0 |
| OFF | SWITCH | 0 | 24 | 0 | 24 | 24 | 0 (0) | 0 |
| OFF | HOLD_AFTER_SWITCH | 0 | 24 | 0 | 24 | 24 | 0 (0) | 0 |
| OFF | BACK | 0 | 24 | 0 | 24 | 24 | 0 (0) | 0 |
| OFF | HOLD_AFTER_BACK | 0 | 24 | 0 | 24 | 24 | 0 (0) | 0 |
| OFF | CLEAR | 0 | 24 | 0 | 24 | 24 | 0 (0) | 0 |

Every completed cell has denominator24; shared prefixes are logical arm records.
Coarse task checks preserve the expression and parse syntax; code is not executed.

Frozen conditions: `{"BACK": true, "CLEAR": true, "SWITCH": true, "S_back_control": true, "Zc_back_control": true, "every_step_breakage": true, "paired_clear_release": true, "paired_switch_release": true}`.

Missing-parenthesis defects: 0 logical replies, 0 actual generations, 0 distinct episodes.
Actual generations: fenced 480, bare 0, ambiguous 0, expression echoes 0, OK replies 0.

672 records / 480 actual generations / 14152 tokens; truncated 0, cost-stopped 0.
GPU allocation wall cost including load/kernel/cleanup: 1319.301/1800s (21.99/30min; 0.3665 GPU-h). Overrun 0.000s.

CPU audit replays every score/token/history, bias digest, shared prefix, body mask,
every forward and absolute position. Independent counts, paired verdict and Python
parses agree. Recipe commit bb42c4e6 precedes inference; freeze hashes verified.
No fitting, sealed input, signals, background launch, outcome retries or push.
Own RUNNING.flag removed on natural completion.

This reading concerns this fresh synthetic arithmetic language-syntax check.
It does not establish general skill closure or autonomous maintenance. The Zc/S
comparison isolates the BACK bias after identical masked prefixes; masks retain
headers/closures and downstream KV. Prior40h PARTIAL remains unchanged.
