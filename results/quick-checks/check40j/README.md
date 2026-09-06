# Check40j — R1: rendering suffices

**Text-only scored16/16 executable-correct JavaScript in BOTH phases.** Adding the
router, mask, or both yielded no additional executable success under six retained
Python answers. Apply the prewritten consequence: **leave the actuator out of
default shipping; rendering-only becomes the primary arm.** No larger run follows.

This is an n=16 descriptive screen on one arithmetic harness, not an equivalence
proof or a claim that routing never helps. The requested literal cue is used;
current FOCUS-3 actually emits a JSON wrapper. That pre-inference discrepancy is
documented below; this does not establish byte-identical production-renderer behavior.

| Phase | Arm | JS executable-correct /16 | Python | Broken | Fence labels | First token |
|---|---|---:|---:|---:|---|---|
| P1 | OFF | 0 | 16 | 0 | python: 16 | fence opener: 16 |
| P1 | text-only | 16 | 0 | 0 | javascript: 16 | fence opener: 16 |
| P1 | bias-only | 0 | 16 | 0 | python: 16 | fence opener: 16 |
| P1 | text+bias | 16 | 0 | 0 | js: 16 | fence opener: 16 |
| P2 | text-only | 16 | 0 | 0 | javascript: 16 | fence opener: 16 |
| P2 | text+mask | 16 | 0 | 0 | javascript: 16 | fence opener: 16 |
| P2 | text+bias | 16 | 0 | 0 | javascript: 16 | fence opener: 16 |
| P2 | text+bias+mask | 16 | 0 | 0 | (bare): 10, js: 6 | fence opener: 6, function: 10 |

All96/96 history answers were valid, executable-correct Python, zero broken.
They were generated OFF in-run and cached once per task; all four P2 arms share
each exact six-turn token/KV prefix. No history answer was replaced or selected.
All224 replies were semantically correct in their emitted language, zero truncated
or otherwise broken. Python counts agree with executable Python counts here.

**Paired P2 text+bias+mask vs text-only:** wins0, losses0, ties16 (both succeed16,
both fail0); observed gain0/16 =0 percentage points. Exact two-sided sign p=1
(no discordants; uninformative). Descriptive95% CP success interval for every16/16
arm:79.41–100%; bias-only and OFF0/16 JS:0–20.59%. Conservative paired-gain95%
interval:−23.96 to+23.96 points, using Bonferroni97.5% CP intervals for win/loss
probabilities. Conditional win interval among discordants is vacuous[0,1].
The finite screen cannot exclude a population benefit; R1 is the registered
engineering decision at this pressure, not proof of zero population effect.

**Diagnostics:** P1 bias-only0/16 does NOT reproduce40g3/8. The exact tensor/hash
is unchanged; task/name/seed sensitivity remains visible in this hard harness.
P1 text+bias16 vs text-only16: wins0/losses0/ties16, no single-shot additivity.
P1 bias changes the fence label from javascript to js on16/16. P2 combined emits
10 bare functions and6 js fences, while text-only emits16 javascript fences.
Presentation changed; executable correctness did not. No control-triggered tuning.

**Paired task tables.** Each cell is executable language / fence label / first-token
code. J=correct JavaScript; P=correct Python; F=literal three-backtick fence opener;
U=literal `function` token. No cell is broken. Exact token IDs and all fields are
in records.jsonl; expressions and six fresh history tasks per row are in tasks.json.

**P1**

| Task | OFF | text-only | bias-only | text+bias |
|---|---|---|---|---|
| solve_j_000 | P / python / F | J / javascript / F | P / python / F | J / js / F |
| solve_j_007 | P / python / F | J / javascript / F | P / python / F | J / js / F |
| solve_j_014 | P / python / F | J / javascript / F | P / python / F | J / js / F |
| solve_j_021 | P / python / F | J / javascript / F | P / python / F | J / js / F |
| solve_j_028 | P / python / F | J / javascript / F | P / python / F | J / js / F |
| solve_j_035 | P / python / F | J / javascript / F | P / python / F | J / js / F |
| solve_j_042 | P / python / F | J / javascript / F | P / python / F | J / js / F |
| solve_j_049 | P / python / F | J / javascript / F | P / python / F | J / js / F |
| solve_j_056 | P / python / F | J / javascript / F | P / python / F | J / js / F |
| solve_j_063 | P / python / F | J / javascript / F | P / python / F | J / js / F |
| solve_j_070 | P / python / F | J / javascript / F | P / python / F | J / js / F |
| solve_j_077 | P / python / F | J / javascript / F | P / python / F | J / js / F |
| solve_j_084 | P / python / F | J / javascript / F | P / python / F | J / js / F |
| solve_j_091 | P / python / F | J / javascript / F | P / python / F | J / js / F |
| solve_j_098 | P / python / F | J / javascript / F | P / python / F | J / js / F |
| solve_j_105 | P / python / F | J / javascript / F | P / python / F | J / js / F |

**P2**

| Task | text-only | text+mask | text+bias | text+bias+mask |
|---|---|---|---|---|
| solve_j_000 | J / javascript / F | J / javascript / F | J / javascript / F | J / js / F |
| solve_j_007 | J / javascript / F | J / javascript / F | J / javascript / F | J / js / F |
| solve_j_014 | J / javascript / F | J / javascript / F | J / javascript / F | J / (bare) / U |
| solve_j_021 | J / javascript / F | J / javascript / F | J / javascript / F | J / js / F |
| solve_j_028 | J / javascript / F | J / javascript / F | J / javascript / F | J / js / F |
| solve_j_035 | J / javascript / F | J / javascript / F | J / javascript / F | J / (bare) / U |
| solve_j_042 | J / javascript / F | J / javascript / F | J / javascript / F | J / (bare) / U |
| solve_j_049 | J / javascript / F | J / javascript / F | J / javascript / F | J / (bare) / U |
| solve_j_056 | J / javascript / F | J / javascript / F | J / javascript / F | J / (bare) / U |
| solve_j_063 | J / javascript / F | J / javascript / F | J / javascript / F | J / (bare) / U |
| solve_j_070 | J / javascript / F | J / javascript / F | J / javascript / F | J / js / F |
| solve_j_077 | J / javascript / F | J / javascript / F | J / javascript / F | J / (bare) / U |
| solve_j_084 | J / javascript / F | J / javascript / F | J / javascript / F | J / (bare) / U |
| solve_j_091 | J / javascript / F | J / javascript / F | J / javascript / F | J / js / F |
| solve_j_098 | J / javascript / F | J / javascript / F | J / javascript / F | J / (bare) / U |
| solve_j_105 | J / javascript / F | J / javascript / F | J / javascript / F | J / (bare) / U |

**Execution/provenance.**

Recipe committed BEFORE inference: `3dddc28e5dc0b232e27276ff2738aee8523124f6`.
Tensor float32-bytes SHA256: `bda3d63e34d203df983d03e71e5850079b1496a2ecaad15f8bfbb25bd2f83cb2`.
Tensor file SHA256: `5776dfab18bf2286c0932ad0d86a4670eb1541ae5cb55806d3bba0e616f8fab7`.
One model load;224 generations;827.221/2700 GPU-seconds (13.787 minutes),
peak Torch allocation57.642 GiB. Natural exit0; own RUNNING.flag removed.
No signals, pushes, fitting, re-generation or benchmark data. SciPy1.18.1 was
missing in a synthetic reporting smoke during loading; installed before the first
generation, and all decision-boundary/paired-sign fixtures passed. No script,
prompt, tensor or reading changed after recipe commit. Frozen dependencies match
all17 corresponding recipe-commit git blobs. CPU mask/consumer tests and scorer
controls passed before inference; saved-record audit rechecks scores, tokens,
current messages, all cache prefixes, every-forward masks, bias schedule and summary.

Artifacts: [records.jsonl](records.jsonl), [summary.json](summary.json),
[freeze.json](freeze.json), [tasks.json](tasks.json), [audit.json](audit.json),
[run.log](run.log), [prewritten-reading.md](prewritten-reading.md).

---

**Pre-inference recipe and readings (verbatim):**

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
