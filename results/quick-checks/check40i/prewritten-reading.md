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

Results PENDING.
