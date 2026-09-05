# Quick check 41b — causal decision-position neurons (2026-09-05)

Prewritten reading, frozen before model execution; seed 41042; dense Qwen3-4B.
Data lineage: no fitting, training, parameter updates or benchmark input reads.
Gradient readout on 32 uncued synthetic fit tasks; cued JS/Python and uncued
activations from those same tasks only. Cell selection on 8 separate setup tasks;
evaluation on 32 fresh uncued tasks, disjoint IDs and full prompts. The check41
operation bank/parser/checkers are reused; operation families overlap. New check41b
function names prevent exact prompt overlap with previous checks. No sealed input.

Decision position is the final prompt position predicting generated token 1.
c = logsumexp(logits of literal JS tokens function,const,let,//,async) minus
logsumexp(logits of literal Python tokens def,import,class,#,from). Each literal
must encode as one token, with no leading whitespace variants. Preserve token IDs,
per-task top-1 defaults, actual first tokens and first eight tokens. A code fence
can be the actual first token: do not silently move the readout to a later token.
For all 36 layers, use the actual SiLU(gate)*up input to down_proj. Average
x * dc/dx at that position over 32 uncued tasks; save per-task gradients, x and
attributions, plus cued-minus-uncued differences and language-cued means. Rank by
absolute signed mean attribution, stable flat-index ties; k in {50,200,800}.
Report sign/layer distributions and intersections with all check41 frequency sets.

Grid: 8 setup tasks x [k={50,200,800}, T={1,4,16}, multiplicative g={1,3,8}
or cued-mean clamp (no g)] = 36 cells, 288 generations. Positive attribution
neurons multiply by 1+g and negative by 1-g toward JS; swapped reverses sign.
Clamp sets selected neurons to their fit-task cued-JS mean; swapped uses the
cued-Python mean. Shuffled selects random other neurons matched per-layer sign
counts, with their own cued means for clamp. Exactly the first T token-predicting
positions are modified: final prompt position then T-1 decode positions; release
from prediction T+1 onward. Earlier cached changes persist naturally after release.
Pick most valid JS, then least breakage; residual ties lower k, lower T,
multiplicative before clamp, lower gain. Freeze before any screen output.

Screen: all 32 fresh SET tasks, each in correct/swapped/shuffled/OFF/text-cue arms.
If correct SET >=12/32, extend first 16 SET trajectories with their own retained
histories through HOLD/SWITCH/BACK/CLEAR on rotated screen tasks. Reapply first-T
intervention on each active request; SWITCH targets Python, BACK JavaScript,
CLEAR has no intervention or new cue. OFF never has a cue; text-cue explicitly
names the target each active request. No neutral step required in this check.
Parse language, reuse coarse task check and breakage; generated programs never run.
Log c and paired OFF shift for fresh SET, plus same-history unmodified c/shift on
every request (text-cue shift compared with identical history minus current cue).

FIXED READING: POSSIBLE if correct valid JavaScript >=20/32, correct breakage <=2/32,
and shuffled valid JavaScript <=4/32 at SET. Otherwise MARGINAL if correct valid
JavaScript >=12/32; else NOT POSSIBLE. An incomplete screen is PARTIAL, never a
negative finding. On NOT POSSIBLE state plainly: the language decision is not
carried by identifiable MLP neurons at the decision position on this trunk under
this registered selector and intervention. This bounded result cannot exclude
other contrast definitions, sites or distributed representations.

Foreground only; no process signals. Wait behind check41 and check40b, check40b
RUNNING.flag included; poll resources every 600 seconds. Queue on .review.lock
to serialize with the existing check42 waiter. Write our RUNNING.flag only when
holding the GPU slot, remove on exit. 5400-second allocation cap including model
load, pilot, attribution and generation. Cooperative per-forward/per-token stop,
30-second cleanup reserve. No outcome-based redesign or rerun of the screen.
CPU tests verify autograd and first-T hooks through real tiny Qwen3 consumers.
The first setup generation is the charged pilot; record timing and full-design
projection before the remaining matrix. If the projection exceeds the cap, stop
with PARTIAL instead of shrinking the design after seeing outcomes.
