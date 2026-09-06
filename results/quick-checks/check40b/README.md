# Check 40b — minimal brute-force expert routing, single-shot SET

Unregistered, disclosed; Brian's 2026-09-05 brief. Qwen3-30B-A3B, seed 40040.
Fit/train-on: none. Profile measurements reuse only the 32 cued competence
responses; alpha selection uses eight separate synthetic setup tasks. Evaluation:
32 fresh-to-this-run uncued tasks, disjoint statements and expression/tree families
from competence/setup. These are the first 16/8/32 rows of check 40's cf8c38ae
arithmetic competence/grid/screen bank, not a held-out benchmark. No sealed input
or recorded benchmark response is read. No weights fitted or trained.

## Pre-written reading (fixed before model outcomes)

Competence: 16 paired tasks per language, cue visible, >=14/16 unbroken parser-valid
target-language replies each; otherwise INELIGIBLE. Coarse task checks separate.
64-token cap for every generation. If either language has >4/16 truncations,
raise to 128 ONCE, regenerate all 32 competence replies, preserve the initial
attempt separately, and use 128 thereafter. No other cap or outcome rescue.
Profiles: teacher-force the final 32 actual cued replies, no new decoding or
success filtering. Pool raw router logits at all generated non-EOS tokens' own
positions (including the final token), exclude prompt/EOS, then take the per-layer
mean per expert per language. Longer replies weigh more. Top-k uses model k=8;
if overlap intersection/8 >90% in EVERY layer, INELIGIBLE: same experts.
Bias = alpha * (language mean logits - two-language mean logits), all 48 layers.
No normalization or learned parameters. Shuffled permutes expert indices within
each layer with seed 40042, preserving every layer's norm and the paired opposition.
Grid: four cells = Python/JavaScript direction x alpha {1,4}, eight uncued tasks
per cell, 32 generations. Select alpha from the JS-direction cells by highest
valid unbroken JS count, then fewest broken replies, then smaller alpha. Python
cells are direction controls, not eligible substitutes for the JS address. Freeze
before screen. This resolves the brief's four-cell/two-alpha ambiguity explicitly.
Screen: 32 tasks x correct(JS), swapped(Python), shuffled(JS permutation), OFF,
text-cue("Use JavaScript.") =160 generations. Every response starts a fresh
system/user request and fresh KV, with no retained history. Bias covers prefill
and decode. Parser identity ignores fence labels; task checks reuse check40's
coarse syntax/expression checker, not general execution correctness. Breakage
includes truncation, invalid/ambiguous parse, fence errors and repetition.
POSSIBLE iff correct valid unbroken JS >=20/32, correct breakage <=2/32,
and shuffled valid unbroken JS <=4/32. Otherwise MARGINAL iff correct >=12/32;
else NOT POSSIBLE. Report OFF identity distribution and all task checks.
Incomplete runs are PARTIAL. If the cost projection requires 16 screen tasks,
report descriptive counts with PARTIAL (literal 32-task thresholds unchanged).

## Pre-run cost and execution

At check40's measured conservative 16 tok/s, (32+32+160)*64=14,336 capped tokens
cost 896 seconds =14.93 decode minutes. Charge a conservative 600 seconds for
load/kernel checks and 1 second per generation/profile prefill, then a 25% reserve:
(600+896+256)*1.25=2,190 seconds =0.6083 GPU-h, below 1.5 GPU-h.
The once-raised-cap branch, including discarded 64-token competence, projects
(600+(32*64+224*128)/16+288)*1.25=3,510 seconds =0.975 GPU-h.
Reproject with elapsed allocation before each next stage; halve screen to 16 only
if projected >5,400 seconds, and stop PARTIAL if that still does not fit.
Cooperative deadline checked per token/forward; no signals or process termination.
Load and all GPU stages count; a blocking operation can overrun and is disclosed.
Reuse check40 model loader, tuple-aware router hook, grouped_mm parity/dispatch/OFF
checks, parsers, prompts, arithmetic bank and seed. No extra throughput decoding.
Foreground only. Queue for the shared review lock before polling, to preserve
priority over check42 whose running waiter predates RUNNING.flag support. The
original no-outcome waiter will exit naturally on the outcome-overwrite guard.
Poll GPU/check41 at 600-second intervals if unavailable; require
no compute process AND (check41 terminal reading OR its runner absent). Hold the
repo review lock during execution; RUNNING.flag reserves check40b through reporting.

## Results

**MARGINAL — the router bias flips language, but misses the breakage limit.**
Correct bias yielded **26/32 valid JavaScript** (25/32 coarse task-check passes),
with **6/32 broken under the fixed two-parser checker**, exceeding the <=2/32 bar.
Shuffled yielded 0/32 JS. Thus the >=20 JS and shuffled-control conditions passed,
but the pre-written POSSIBLE conjunction did not. No dose/cap/threshold rescue.
This is a positive language-induction observation for this particular sustained
router-logit bias on fresh synthetic arithmetic requests, not a reliable general
skill controller, persistent state, benchmark result, or semantic-correctness claim.

| Screen arm | Valid JS /32 | Valid Python /32 | Broken /32 | Coarse task pass /32 | JS + coarse pass /32 | Truncated /32 |
|---|---:|---:|---:|---:|---:|---:|
| correct | 26 | 0 | 6 | 25 | 25 | 0 |
| swapped | 0 | 29 | 3 | 29 | 0 | 0 |
| shuffled | 0 | 32 | 0 | 32 | 0 | 0 |
| OFF | 0 | 32 | 0 | 32 | 0 | 0 |
| text-cue | 32 | 0 | 0 | 32 | 32 | 0 |

**OFF default distribution: Python 32/32, JavaScript 0/32, invalid/ambiguous 0/32.**
All 26 correct-arm valid JS replies therefore flipped a paired OFF Python default.
Swapped retained valid Python on 29/32, with three syntax failures; it did not
improve an already-perfect OFF default. Text cue reached valid JS and coarse task
pass on all 32 with no breakage. All arms used fresh independent KV and no history.

Breakage details: the six correct-arm failures were rejected by both Python and
JavaScript parsers: four Dart-style `int name() { ... }` replies and two `->`
arrow replies. “Broken” here is the frozen two-parser category, not a claim that
Dart-style outputs are invalid in every programming language. Swapped's three
failures were missing a closing parenthesis. No truncation, repetition, empty,
ambiguous-parse or fence failures occurred anywhere in the 224 generations.
The one parser-valid JS reply that failed the coarse task checker was a bare
arrow-function assignment (`solve_screen_26 = () => { return ...; };`), which the
inherited named-function checker does not recognize. Programs were never executed;
the checker remains unchanged and its results are reported literally.

Competence: **Python 16/16, JavaScript 16/16** valid and coarse-task passing;
zero breakage/truncation. The 128-token fallback was not invoked. Profiles used
exactly those 32 replies in teacher-forced forwards, with no further decoding.
Top-8 overlap mean **80.7292%**, range **50–100%**; the all-layer >90% gate passed.
All per-language top expert IDs and overlaps are in [profile statistics](profile-statistics.json).

| Alpha | Bias direction | Valid JS /8 | Broken /8 | Coarse task pass /8 |
|---|---|---:|---:|---:|
| 1 | Python | 0 | 0 | 8 |
| 1 | JavaScript | 0 | 0 | 8 |
| 4 | Python | 0 | 0 | 8 |
| 4 | JavaScript | 7 | 1 | 4 |

**Frozen choice: alpha 4, all 48 layers, JS mean-logit profile.** JS count is the
primary grid rank, so 7 JS / 1 broken beats alpha 1's 0 JS / 0 broken. The screen
was still empty at freeze. Both Python-direction grid cells yielded 8 valid Python.

Per-layer top-8 overlap (intersection / 8):

| Layer | Overlap | Layer | Overlap | Layer | Overlap |
|---:|---:|---:|---:|---:|---:|
| 0 | 75% | 16 | 87.5% | 32 | 87.5% |
| 1 | 87.5% | 17 | 62.5% | 33 | 87.5% |
| 2 | 50% | 18 | 87.5% | 34 | 87.5% |
| 3 | 100% | 19 | 87.5% | 35 | 75% |
| 4 | 62.5% | 20 | 87.5% | 36 | 75% |
| 5 | 87.5% | 21 | 87.5% | 37 | 100% |
| 6 | 87.5% | 22 | 87.5% | 38 | 75% |
| 7 | 87.5% | 23 | 87.5% | 39 | 75% |
| 8 | 50% | 24 | 100% | 40 | 100% |
| 9 | 87.5% | 25 | 75% | 41 | 75% |
| 10 | 87.5% | 26 | 100% | 42 | 75% |
| 11 | 75% | 27 | 87.5% | 43 | 75% |
| 12 | 100% | 28 | 87.5% | 44 | 75% |
| 13 | 75% | 29 | 62.5% | 45 | 62.5% |
| 14 | 62.5% | 30 | 87.5% | 46 | 62.5% |
| 15 | 62.5% | 31 | 87.5% | 47 | 87.5% |

Execution: **744.53 seconds = 12.41 GPU-minutes**
(0.2068 GPU-h) charged including **314.04 seconds loading;
cap 5,400 seconds, no overrun. **224 generated records, 6,194 generated tokens,
32 saved teacher-forced profile records**, full 32-task screen, 64-token cap
throughout. Peak allocated GPU memory **57.65 GiB**.
No screen halving. The installed grouped_mm path was adopted; compatibility-probe
relative error 0.0, changed expert dispatch, and exact OFF next-token logits passed.
No new throughput-only decoding or eager-versus-grouped speed comparison.

Operational disclosure: check41 acquired the GPU while the initial check40b waiter
was preparing. Its predecessor waiter and check42's already-running waiter did not
coordinate via RUNNING.flag alone, so the revised foreground runner queued for
the shared lock. It acquired the lock at 20:51 UTC, still observed check41's GPU
process during teardown, and loaded only after the next 600-second poll at 21:01
showed an idle GPU and no check41 process. The original waiter exited naturally
with BlockingIOError on the busy lock at its 21:00 poll, before any model load or
generation; its source/freeze/log are preserved under `initial-waiter/`. A mixed
valid/broken JSON-key sorting defect and lint were repaired before any check40b
model outcome, with a new pre-outcome freeze. No signal, termination, background
launch, training, fitting, benchmark input, or sealed-input access.

Audit: all **224** parser scores reproduced; token IDs decode to the saved texts;
chat templates reproduce every saved input; all requests are fresh and uncued
outside competence/text-cue. Recomputed all profile means from same-run per-task
sums, every overlap, centered/shuffled biases and per-layer norm equality, grid
choice, screen counts and reading. Executed source freeze matches. CPU parser,
truncation, disjoint-bank, threshold and mixed-result serialization checks plus
ruff passed. No additional GPU generation or outcome-dependent adjustment.

Artifacts: [summary](summary.json), [records](records.jsonl), [profiles tensor](profiles.pt),
[per-task profiles](profiles/), [frozen biases](frozen-biases.pt), [grid](grid.json),
[pre-run projection](projection.json), [cost updates](cost-updates.json),
[kernel checks](kernel.json), [source freeze](freeze.json), [CPU audit](audit.json),
[audit source](audit-source.py.txt), [run log](run.log).

`profiles.pt` contains float32 means/normal/shuffled tensors of shape [2,48,128]
(language order Python, JavaScript), plus 32 per-task dictionaries with float64
logit sums [48,128], token count and source record ID. Each `profiles/*.pt` holds
one of those same dictionaries. `frozen-biases.pt` contains the three float32
[48,128] correct/swapped/shuffled tensors. JSON records retain text, input/output
token IDs, parser results, truncation, timing and applied bias hashes. File sizes
and SHA-256 values are recorded in [artifact inventory](artifact-inventory.json).

**Correction (astra full review, 2026-09-05)**: (F1, F5) For checks 40b/40c/40d/41b, the provenance description is “locally frozen before execution according to run receipts”. Their freeze files first entered Git with results; matching local hashes and timestamps do not independently establish pre-outcome Git commitment. Checks 41/40e/43 have pre-generation Git anchors. Some checks 34–38 have launch-copy/hash evidence; check39’s exact reading was committed before its recorded start. These are not all committed preregistrations; no fabricated chronology was found. All 32 contain the intended arithmetic expression;26 parse as JavaScript and6 fail the paired language checker. This is expression preservation, not32 executable correct programs.
