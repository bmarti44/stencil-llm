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


## Results — PROCEED_PLACEHOLDER

Completed all 64 paired episodes in **16.591/30 GPU-minutes**, including
loading and pilot. Peak allocated CUDA memory: 8.648 GB.
Preregistration commit: `e24afd4`; period token ID 13.

**Placeholder passes the prospective check-39 rule and is preselected for the
larger test.** This check does not launch that test. Check 37 remains STOP under
its original rule; its observations are not pooled into this decision.

Each success cell below is strict valid/nonbroken target success out of 64.

| Variant / execution | Release 1 | Release 2 | Neutral 1 | Neutral 2 | Broken episodes |
|---|---:|---:|---:|---:|---:|---:|
| intact/surviving | 59 | 58 | 64 | 64 | 4 |
| intact/rebuilt | 59 | 58 | 63 | 64 | 4 |
| placeholder/surviving | 60 | 59 | 64 | 64 | 0 |
| placeholder/rebuilt | 58 | 57 | 64 | 64 | 0 |

All other cells, in release-1 / release-2 / neutral-1 / neutral-2 order.
Strict validity is JSON integer-array schema only; lenient accuracy can credit
a correctly valued list even when its surrounding response fails strict schema.

| Variant / execution | Strict valid | Lenient value-exact | Broken outputs | Period imitation | Empty |
|---|---|---|---|---|---|
| intact/surviving | 60 / 60 / 64 / 64 | 63 / 62 / 64 / 64 | 4 / 4 / 0 / 0 | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 |
| intact/rebuilt | 60 / 60 / 63 / 64 | 63 / 62 / 64 / 64 | 4 / 4 / 1 / 0 | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 |
| placeholder/surviving | 64 / 64 / 64 / 64 | 60 / 59 / 64 / 64 | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 |
| placeholder/rebuilt | 64 / 64 / 64 / 64 | 58 / 57 / 64 / 64 | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 |

Paired episode safety, independently in each execution. b is placeholder-only
breakage; c is intact-only breakage. p is the registered exact one-sided
McNemar upper-tail probability for increased placeholder breakage.

| Execution | b | c | Both broken | Neither broken | b-c | p | Safety |
|---|---:|---:|---:|---:|---:|---:|---|
| surviving | 0 | 4 | 0 | 60 | -4 | 1 | PASS |
| rebuilt | 0 | 4 | 0 | 60 | -4 | 1 | PASS |

surviving: zero-based placeholder-only broken episodes [];
intact-only [33, 34, 41, 43]; both [].
Placeholder gains one strict success at each surviving release; active gate PASS.
Neutral gate: PASS.

rebuilt: zero-based placeholder-only broken episodes [];
intact-only [33, 34, 41, 43]; both [].
Placeholder loses one strict success at each rebuilt release; the active-task
gate does not apply to this mode. Neutral gate: PASS.

Shared unscreened setup responses (strict valid / strict nonbroken success /
lenient value-exact / broken outputs, each out of 64):

- SET: 60 / 56 / 60 / 4.
- HOLD: 60 / 59 / 62 / 4.

Surviving/rebuilt identical generated-token sequences including EOS, in the
same four-checkpoint order (each out of 64):

- intact: 64 / 64 / 63 / 64.
- placeholder: 44 / 53 / 64 / 64.

The surviving strict release gains reflect schema repair, not better lenient
value accuracy: placeholder scores 60/59 lenient versus intact 63/62. Rebuilt
placeholder scores 58/57 lenient versus intact 63/62. Placeholder produces no
period imitations or empty responses. Intact surviving already copies 64/64
twice, so this comparison shows no surviving neutral-copy advantage for repair.

These are output comparisons on matched tokens and absolute positions, not
bitwise cache-equivalence claims. Rebuilt answers remain diagnostic shadows
of the surviving trajectory, as registered. Passing a no-significant-increase
test is not affirmative statistical proof of noninferiority or general safety.
This check measures repair under a continuing ascending cue followed by explicit
cancellation; benefit at a conflicting instruction change remains untested here.

Broken scored responses (zero-based episodes; response cells are JSON-encoded
raw strings, also saved in records):

| Episode | Variant / mode | Step | Response |
|---:|---|---|---|
| 33 | intact/surviving | RELEASE1 | `"[[-18, -17, -15, -3, 4, 5]]"` |
| 33 | intact/rebuilt | RELEASE1 | `"[[-18, -17, -15, -3, 4, 5]]"` |
| 33 | intact/surviving | RELEASE2 | `"[[-17, -9, 10, 12, 19]]"` |
| 33 | intact/rebuilt | RELEASE2 | `"[[-17, -9, 10, 12, 19]]"` |
| 33 | intact/rebuilt | NEUTRAL1 | `"[\"-11\", \"-14\", \"-1\", \"-5\", \"10\", \"3\", \"7\"]"` |
| 34 | intact/surviving | RELEASE1 | `"[[-17, -14, -13, -2, -1, 1, 5, 17]]"` |
| 34 | intact/rebuilt | RELEASE1 | `"[[-17, -14, -13, -2, -1, 1, 5, 17]]"` |
| 34 | intact/surviving | RELEASE2 | `"[[-9, -8, -6, 4, 9, 19]]"` |
| 34 | intact/rebuilt | RELEASE2 | `"[[-9, -8, -6, 4, 9, 19]]"` |
| 41 | intact/surviving | RELEASE1 | `"[[-15, -13, -3, 8, 9, 10, 11]]"` |
| 41 | intact/rebuilt | RELEASE1 | `"[[-15, -13, -3, 8, 9, 10, 11]]"` |
| 41 | intact/surviving | RELEASE2 | `"[[-16, -13, -2, 7, 13, 16]]"` |
| 41 | intact/rebuilt | RELEASE2 | `"[[-16, -13, -2, 7, 13, 16]]"` |
| 43 | intact/surviving | RELEASE1 | `"[[-15, -2, 5, 7, 19]]"` |
| 43 | intact/rebuilt | RELEASE1 | `"[[-15, -2, 5, 7, 19]]"` |
| 43 | intact/surviving | RELEASE2 | `"[[-16, -14, -12, -4, 13, 16]]"` |
| 43 | intact/rebuilt | RELEASE2 | `"[[-16, -14, -12, -4, 13, 16]]"` |

Validation: independently audited all 1,152 raw records (128 shared setup +
1,024 scored), 384 edits, 512 paired histories and 384 structurally valid edit
snapshots on CPU. Recomputed strict/lenient scores, repetition, paired gates and
output matches; reconstructed edited histories, retained closures and absolute
offsets; verified all 384 sets are unique, reproduce seed 39039 and are disjoint
from check 37. Verified source hashes and committed preregistration. Inherited
engine/self-tests, gate boundaries, lint and import safety checks passed
(3 import tests passed, 1 expected legacy-inventory xfail). No fitting, training,
sealed inputs, process signals, background launches or push.

Artifacts: [summary](4b/summary.json), [records](4b/records.jsonl),
[operations](4b/operations.jsonl), [episodes](4b/episodes.json),
[layout](4b/layout.json), [frozen reading](4b/prewritten-reading.md),
[audit](4b/audit.json), [CPU audit script](4b/audit_records.py).
Runner: `scripts/focus_check39.py`, reusing check 37's Engine and Budget.
