# Check 39 — eviction repair rerun (2026-09-05)

## Reading fixed before GPU execution

Lineage: fit-on=none; evaluated-on=64 fresh synthetic episodes (384 distinct
integer sets), seed 39039; no fitting, training or benchmark inputs. Verify the
bank is disjoint from check 37 before loading the GPU; do not redraw on overlap.
Check 37's STOP verdict stands unchanged and none of its episodes are reused.
Fable's F6 was written before check 37's outcome; this authorized rerun applies
the following replacement rule prospectively to fresh episodes.

**PROCEED with placeholder iff all three conditions pass; otherwise STOP, closing
the placeholder repair. No third variant is promoted.**

1. In EACH execution mode, b = episodes broken only under placeholder and c =
   episodes broken only under intact: b - c <= 2 AND exact paired McNemar
   not-worse at .05. Precisely, the one-sided test for increased placeholder
   breakage is P[Binomial(b+c, .5) >= b]; pass iff p >= .05 (p=1 for no
   discordances). This is a failure-to-detect-increased-breakage safety gate,
   not proof of statistical noninferiority. The user's explicit NET b-c limit
   governs here; F6's original raw b<=2 wording is not substituted for it.
2. At EACH active release in surviving-cache execution, placeholder strict
   valid/nonbroken target successes >= intact - 2 (out of 64). Rebuilt release
   counts are reported but do not gate active-task success.
3. At BOTH neutral requests in BOTH executions, strict valid/nonbroken copy
   successes >=56/64. Conservatively require this for both intact and placeholder.

Design and scoring reuse `scripts/focus_check37.py`: Qwen3-4B frozen bf16,
hf_compatible, greedy, thinking disabled, max 64 new tokens. Only intact and
placeholder, each surviving-cache and rebuilt-text. System requests a JSON
integer array. Separate user cue: “Sort the numbers from smallest to largest.
Apply this rule to subsequent integer requests until I cancel it.” Fixed period
acknowledgements for cue/cancel events are retained. Generate two unscreened
SET/HOLD responses before forking variants. Six distinct unsorted lists per
episode, same integer generator and range as check 37, new seed and n=64.

Before RELEASE1, RELEASE2 and NEUTRAL1, edit newly accumulated operand answers:
intact is a no-op; placeholder replaces the entire assistant body (including
empty thinking prefill) with a CPU-verified single-token period, retaining the
assistant header, im_end and newline. Recompute period K/V from the surviving
prefix at the first original body position; retain other surviving K/V. Absolute
positions and next RoPE offsets never compact. Cue remains active at both
releases. Before NEUTRAL1 append: “Cancel the earlier sorting instruction. For
subsequent requests, copy the integers in their original input order.” Both
neutral requests explicitly ask for copying; no further edit or refresh at
NEUTRAL2. At every checkpoint, rebuild from each variant's exact edited tokens
and absolute positions, including gaps. Rebuilt responses are paired shadows;
the continuing trajectory uses unscreened surviving-cache responses.

Report every cell's strict schema validity, strict valid/nonbroken target
success, lenient value-exact accuracy, breakage, period imitation and empty output.
A broken output is schema-invalid, empty/unparseable, truncated, repetitive
(>0.2 repeated-4gram fraction or duplicate parsed integers), or missing im_end.
An episode is broken if any scored post-edit response breaks; SET/HOLD are
reported separately and do not enter the paired safety gate. Period/empty
responses count as breakage. Invalid responses never count as strict successes.

Foreground only; abort if GPU initially busy; cap 30 GPU-min including loading
and first-episode pilot. Cooperatively exit before cap or if foreign compute
appears; abort further episodes if pilot projects >=29.5 min. No process signals,
background jobs, sealed IFEval input or sealed BFCL cohort contents. Freeze the
reading and source hashes at launch and save raw responses, tokens, scores,
edit maps and position histories during the same run. Commit the reading and
script before launch. No larger experiment is launched by this check.
