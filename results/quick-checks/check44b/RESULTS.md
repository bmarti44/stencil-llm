# Check 44b — awaiting the committed new Fable bank

No held-out or SETUP inference has run. First-ship structured rule entry remains
in force pending the registered GO/NO-GO evaluation. The original Fable bank
has not been opened in this check.

The pre-written recipe was committed in f03c4398; all three final checkpoints,
DEV thresholds and weight hashes were frozen in bab43b0d before any held-out look.
Fit-on = 2794 audited Kimi/Opus messages; DEV = 309 messages (marketing/travel,
2/20 whole-domain groups). Gold span counts: fit1346, DEV147. All matched quote
variants and source batches stay together; explicit scenario IDs were absent.

| Seed | DEV threshold | Overlap micro P / R | Gold-empty false admissions |
|---|---:|---:|---:|
| 0, designated | 0.9883976740722434 | 97.83% / 91.84% (135/147 recall) | 3/183 (1.64%) |
| 1 | 0.9768228882950498 | 97.87% / 93.88% (138/147 recall) | 3/183 (1.64%) |
| 2 | 0.956549283252651 | 97.87% / 93.88% (138/147 recall) | 3/183 (1.64%) |

DEV outcomes cannot establish GO. Frozen splitter maximum overlap recall is
141/147=95.92% on DEV; no splitter rescue or seed selection occurred. All seeds
completed 468 updates over three epochs. GPU allocation, conservatively including
CPU calibration and saving, was 212.346/3600 seconds (3.539 minutes); peak torch
allocation4.342GiB. The first-ten-update pilot projected498.247 seconds.
The owned flag was removed on natural exit; no process was signalled.

Six focused tests and scoped lint pass. Real CPU smoke checked full-message
pairing, >512-token abstention and the non-user guard. Saved DEV scores and
thresholds reproduce, all frozen file hashes verify, and B's nine checkpoint
files match check44. Safetensors remain local and untracked.

Evaluation will consume the newly committed Fable-2 bank once, plus the96 SETUP
turns, with both arms on CPU/four threads. Five-minute commit polls are preserved
in heldout-polls.jsonl. See README.md for the unchanged decision rule.
