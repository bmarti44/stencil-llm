# Check 37 — eviction repair (2026-09-05)

## Reading fixed before GPU execution

Proceed-rule: placeholder repair has no additional broken episodes versus intact,
loses <=1/32 active-task successes versus intact at EACH release, and copies
>=26/32 at BOTH neutral requests. Preselect placeholder for the larger test if
it passes; otherwise **STOP**, with no promotion of another variant.
Apply this rule separately to surviving-cache and matched text-rebuild results;
both must pass. This conservative interpretation is fixed before outcomes.

Lineage: fit-on=none; evaluated-on=32 fresh synthetic episodes, seed 9053701,
six distinct unsorted integer lists each, no fitting, training or benchmark inputs.
Qwen3-4B, frozen bf16/hf_compatible, greedy, thinking disabled, 64 new tokens.
Foreground only, <=30 GPU-min including load and pilot; abort on initially busy GPU;
cooperatively exit if foreign compute appears or pilot projects beyond the cap.
No background jobs, process signals, sealed IFEval input or sealed BFCL contents.

Standing instruction is a separate user event: “Sort the numbers from smallest
to largest. Apply this rule to subsequent integer requests until I cancel it.”
Event acknowledgements are fixed periods, excluded from deletion. System requests
only a JSON integer array. Generate two unscreened SET/HOLD answers to separate
“Process these integers” user requests before forking the four paired variants.
Before RELEASE1 and RELEASE2, remove all newly accumulated answer material per
variant, with the original cue still active; generate one new ascending answer
after each release. Before NEUTRAL1, apply the same edit again, then append a
separate explicit cancellation user event: “Cancel the earlier sorting instruction.
For subsequent requests, copy the integers in their original input order.”
Both neutral user requests explicitly ask to copy in original input order.
NEUTRAL2 has no further intervention, cancellation or cue refresh.

Variants: intact; legacy generated body+EOS deletion (check 35, leaving the
prefilled empty thinking body and assistant header); deletion of each complete
operand user+assistant pair including trailing newline; replacement of the ENTIRE
assistant body (including the empty thinking prefill) by “.”, CPU-verified as one
token, retaining the assistant header, im_end and newline. Standing-event pairs
remain in every variant. Whole-pair removal is diagnostic and deletes user data.

Absolute positions and the next RoPE offset never compact. The period occupies
the first original assistant-body position; compute its K/V from the surviving
prefix at that position, delete remaining body columns, preserve survivor K/V.
At every scored checkpoint, fork a rebuild from the EXACT edited tokens and
absolute positions of that variant's surviving-cache history. Refill contiguous
spans with original offsets, preserving gaps and the final next offset. Compare
both answers. Continue each variant using its unscreened surviving-cache answer;
rebuilt answers are paired diagnostic shadows, not independent trajectories.
Intact gets the same rebuild diagnostic. Outputs need not be bitwise equal.

Report strict JSON integer-array validity, strict valid/nonbroken target success,
and lenient value-exact accuracy separately at each checkpoint. A broken output
is strict-invalid, empty/unparseable, truncated, repetitive (>0.2 repeated-4gram
fraction or duplicate parsed integers), or not terminated by im_end. A broken
episode has any broken scored post-edit output. “Additional” means an episode
broken in placeholder but not intact in that mode, not a net count difference.
Gate successes require strict exact output and no breakage; no invalid output
counts as release. Save raw replies, tokens, score fields, edits and position maps
in the same run. Freeze a copy/hash of this reading at launch; report results below.
