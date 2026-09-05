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

PENDING.
