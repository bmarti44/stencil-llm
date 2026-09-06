# Check40j — rendered-rule additivity screen

Prewritten 2026-09-06, before GPU work. Data lineage: fit-on = nothing (no fitting
anywhere in this check); evaluated-on = 16 fresh synthetic arithmetic tasks only,
with 96 further fresh expressions used only to generate OFF histories. No benchmark
data. The inherited frozen actuator was profiled previously on40b competence;
no new profiling, fitting, selection, tuning or outcome-based retries.

Seed401006; same three expression families/40e operand range40..89 and EXACT40e
zero-argument prompt/system/suffix. Names and expressions fresh; disjoint from all
40e/40g screen items. Each of16 target tasks is reused across BOTH phases/arms.
Qwen3-30B-A3B HF bf16; identical40 RouterHooks, alpha3 JS tensor loaded directly
from40g/js-control-bias.pt, all48 layers, prefill+decode, greedy, cap64 tokens.
One model load; 45 GPU-minute total cap includes load/kernel validation/cleanup.
224 generations: P1 4x16; OFF history 6x16; P2 4x16. No enlargement.

P1: OFF | text-only | bias-only | text+bias, fresh session each cell.
P2: generate six consecutive OFF answers per task using further fresh expressions;
retain actual tokens/KV, then fork identical cache prefix into text-only | text+mask |
text+bias | text+bias+mask for the seventh (target) request. Retain all OFF outcomes
without selection/replacement; report how many really are Python. If histories
are not all Python, disclose the weaker achieved pressure; do not regenerate.
Mask is40i.mask_change(...,'Z','SWITCH',...), i.e. persistent key masking of all six
assistant bodies incl fences/broken replies, excluding EOS/headers; absolute
positions preserved, no recomputation or replacement. Downstream KV can carry traces.

Literal user-authorized text: "Live rules: (1) Write all code in JavaScript."
Placed as this line + newline BEFORE the current request in the current user turn.
Placement reference: src/stencil/focus3.py:render (line258), which prepends live
rules before the current request. IMPORTANT format discrepancy: the committed
renderer actually emits an Active user rules JSON block, NOT the literal above;
no source renderer contains 'Live rules:'. This check follows Brian's exact literal
cue, copying only prepend placement; it is not byte-identical current FOCUS-3 output.
No additional cue or wrapper is added. Existing40e system and suffix remain.

Executable language/answer scorer:40g.score with js_control=True (Python AST
arithmetic evaluation; Node TypeScript-parser/VM JavaScript execution). Broken:
40i/base.score flags (empty, invalid/ambiguous, fence error, truncation, repetition),
reported independently of executable correctness. Full both scorer records retained.
JS correct requires40g executable correctness AND not40i broken; Python count uses
40i valid_language. Semantic-only failures are reported separately. Fence labels and
first tokens are diagnostic, not language evidence.

PRE-WRITTEN READINGS (fixed):
R1 "rendering suffices": text-only >=14/16 in BOTH phases -> the lever adds nothing
measurable at this pressure; actuator not in default shipping, rendering-only primary.
R2 "lever earns its place": P2 text-only <=10/16 AND text+bias+mask >=text-only+4
with breakage <=1/16 -> retain actuator in composed arm; larger C-vs-R justified.
R3 anything else -> INCONCLUSIVE at n=16; record and stop. No enlargement.
Incomplete/budget-stopped runs are INCOMPLETE, never assigned R1/R2/R3.
Diagnostic only: P1 bias-only versus40g3/8, and P1 text+bias versus text-only.
Report paired tables; P2 combined-vs-text exact win/loss/tie counts, exact binomial
sign p (descriptive), Clopper-Pearson95% intervals for each success rate and
conditional win fraction among discordants. Paired gain CI: conservative95% interval
from Bonferroni97.5% CP marginal intervals for win and loss probabilities. n=16 is a
screen, not an equivalence or population-level no-benefit proof.

Resource estimate:40i480 generations took1319.6s;224 at same per-generation cost
plus full cold-load reserve300s is916s, well below2700s; not a worst-case guarantee.
Cooperative request/token deadline with cleanup reserve; no signals, background
launch, benchmark reads, further profiling, push or modifications to prior artifacts.

Results pending.
