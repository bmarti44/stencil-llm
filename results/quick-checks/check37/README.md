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


## Results — STOP

Complete in **14.715 GPU-minutes**, including load and pilot, below the 30-minute
cap. Peak allocated CUDA memory: 8.846 GB. CPU verified period token ID 13.
**Do not preselect placeholder or advance this proposed larger test.**

Each cell below is strict valid/nonbroken target successes out of 32.

| Variant / execution | Release 1 | Release 2 | Neutral 1 | Neutral 2 | Broken episodes |
|---|---:|---:|---:|---:|---:|
| intact/surviving | 30 | 30 | 32 | 32 | 1 |
| intact/rebuilt | 30 | 30 | 32 | 32 | 1 |
| body_eos/surviving | 31 | 30 | 32 | 32 | 1 |
| body_eos/rebuilt | 28 | 23 | 31 | 32 | 11 |
| whole_pair/surviving | 28 | 24 | 32 | 32 | 11 |
| whole_pair/rebuilt | 27 | 21 | 32 | 32 | 14 |
| placeholder/surviving | 30 | 30 | 32 | 32 | 1 |
| placeholder/rebuilt | 28 | 29 | 32 | 32 | 1 |

Placeholder surviving-cache releases tie intact at 30/32 and 30/32; rebuilt
placeholder scores 28/32 and 29/32 versus intact 30/32 and 30/32. The rebuilt
release-1 loss is 2/32, exceeding the allowed 1/32. Both placeholder modes copy
32/32 at both neutral requests, but BOTH fail the no-additional-breakage clause:
zero-based episode 24 becomes broken at release 2, producing
`[-11, -11, -8, -7, 6, 11, 16]` (duplicate integer). Intact is not broken there.
Intact instead has a broken episode 28, with nested arrays at both releases;
therefore equal total broken-episode counts of 1 do not satisfy the paired rule.

Strict-valid counts (JSON integer-array schema only), followed by lenient
value-exact counts, in release-1 / release-2 / neutral-1 / neutral-2 order:

| Variant / execution | Strict valid | Lenient value-exact |
|---|---|---|
| intact/surviving | 31 / 31 / 32 / 32 | 31 / 31 / 32 / 32 |
| intact/rebuilt | 31 / 31 / 32 / 32 | 31 / 31 / 32 / 32 |
| body_eos/surviving | 32 / 32 / 32 / 32 | 31 / 30 / 32 / 32 |
| body_eos/rebuilt | 28 / 25 / 31 / 32 | 32 / 30 / 32 / 32 |
| whole_pair/surviving | 28 / 25 / 32 / 32 | 32 / 31 / 32 / 32 |
| whole_pair/rebuilt | 27 / 22 / 32 / 32 | 32 / 31 / 32 / 32 |
| placeholder/surviving | 32 / 32 / 32 / 32 | 30 / 30 / 32 / 32 |
| placeholder/rebuilt | 32 / 32 / 32 / 32 | 28 / 29 / 32 / 32 |

Intact surviving/rebuilt outputs match on all 128 post-edit answers. Matching
output counts for legacy deletion are 17/11/31/32; whole-pair deletion
30/29/32/32; placeholder 26/27/32/32 (each checkpoint n=32). These compare identical
input tokens and absolute positions; they show behavioral differences after
recomputing surviving K/V, not a bitwise cache-equivalence claim. Rebuilt outputs
are shadows of the surviving trajectory, as frozen above.

Placeholder preserves schema in all 128 answers per mode but still introduces
an incorrect repeated value. Whole-pair deletion preserves turn delimiters but
has 11/14 broken episodes in surviving/rebuilt mode. Valid turn structure alone
is insufficient. Intact already copies 32/32 at both neutral requests under the
explicit cancellation and copy wording: this check shows no neutral-accuracy
advantage for eviction over that intact comparator. No alternative is promoted.

Validation: all 1,088 raw records (64 shared setup + 1,024 scored), 384 edit
records (including intact no-ops), 512 paired input histories and 288 structurally
valid intact/whole-pair/placeholder edit snapshots audited on CPU. Independently
recomputed strict scores, lenient parsing and repetition; verified deletion and
replacement maps, retained closure, absolute next positions, source/reading
hashes, completeness and gate aggregation. The 192 input sets are unique and
disjoint from check34/check35 banks. Inherited/check37 CPU checks, ruff and import
safety checks passed. No fitting, training, sealed inputs, process signals or push.

Artifacts: [summary](4b/summary.json), [raw records](4b/records.jsonl),
[edit maps](4b/operations.jsonl), [episodes](4b/episodes.json),
[layout](4b/layout.json), [frozen reading](4b/prewritten-reading.md),
[audit](4b/audit.json). Script: `scripts/focus_check37.py` (reuses check35).
