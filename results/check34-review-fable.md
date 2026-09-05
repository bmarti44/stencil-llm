# Check 34 review (fable, one round, CPU-only) — commit b6adfc8

Scope: results/quick-checks/check34/README.md, 4b/{summary.json, records.jsonl,
donors.jsonl, layout.json, episodes.json, validation.json, run.log}, audit.py,
scripts/focus_check34.py, and the reused src/stencil/qwen3.py cache/RoPE/eviction
code. No model was launched; every number below was recomputed from records.jsonl.

## 1. Bookkeeping — verified, no discrepancies

- Denominators: 13 single arms x 64 = 832; stickiness 3 finals x 64 + 2 arms x 3
  priors x 64 = 576; retained 2 directions x 5 steps x 32 = 320; total 1728. All
  per-arm counts in summary.json and both README tables recomputed identically from
  records (exact, strict, A/B/copy/other, breakage). Joint 3/32 (eps 3, 7, 16) and
  5/32 (eps 2, 6, 12, 16, 23) confirmed. Wilson 95% for 60/64 = [0.8500, 0.9754];
  Bonferroni difference interval +/-0.1453 confirmed. Discordances 3/3 confirmed
  (fresh-only eps 8, 26, 38; history-only eps 44, 58, 59; all are near-miss sorts,
  not task flips).
- Recipient contexts are cue-free: every non-text recipient prefix has the OFF
  sentence ids at columns 64-71 and the 4-token suffix at 72-75; the content tokens
  "Sort"/" numbers"/" smallest"/" largest" (ids 10231/5109/24632/7772) appear in no
  recipient prefix, no single/retained prompt, and no filler. Text arms carry the
  real cue at 64-71. Donors: 192 records, cue ids at 64-71, 76 tokens, digit-free,
  192 distinct packet hashes.
- Writes: every packet_write has positions 64..75, kinds both/k/v as the arm name
  says, layers 0..35 (12..35 for layers_ge12), and a strictly positive max-abs change
  in every written layer of every written kind (so K-only and V-only writes really
  differed from the filler columns). The `positions`/`copied_bitwise` fields are
  constants written after a runtime torch.equal assert, not measurements; acceptable.
- Position validity: KVCache stores post-RoPE K (qwen3.py:60), donor and recipient
  prefixes are both 76 tokens prefilled from length 0, so column 64-75 positions
  match. Transplants elsewhere would require re-rotation.
- Token identity all-layer vs text bar: 64/64 A, 64/64 B (recomputed). Also
  shuffled vs text 63/64 A, 64/64 B; layers>=12 vs text 52/59; v_only vs off
  64/64; k_only vs off 37/29 (K-only changed whitespace only, e.g. "[ -9, ..." vs
  "[-9, ...", never the values).
- OFF copy default: 64/64 parsed output equals the input list.
- HOLD/CLEAR flags: 64/64 each. HOLD filler is 133 tokens = user header + 128
  filler + im_end (audit asserts this). CLEAR compares against the pre-SET capture.
- Budget/provenance: initial GPU app list empty, 21.44 min < 45, script and
  reading hashes verified by audit, prewritten section preserved. No attention or
  probe fields exist in any record.

## 2. Substantive findings

### F1 (high, interpretive): the all-layer same-episode transplant is the text bar by construction.
Recipient columns 0-63 are identical tokens to the text arm and, by causality, have
identical K/V. Columns 64-75 are copied from a donor whose prefill was exactly the
text arm's 76 tokens. After the write the recipient cache at 0-75 is therefore the
text-arm cache up to batch-composition bf16 noise; everything downstream is then the
same computation. The 64/64 identical token sequences are a consequence of this
identity, not an independent confirmation of "transfer". The same holds for the
retained SET step. The README (line 85, 87) says the result "uses cached
representations of the actual instruction tokens" but does not state that the
headline arm is mathematically equivalent to putting the cue text in the prompt.
It should.

### F2 (medium): "shuffled donor transfers across contexts" is a 1-2-token perturbation.
Contexts are "The {a} is quiet. The {b} is still." with a,b from an 8-word list;
episode e and its donor e+1 differ in 1 token (56 episodes) or 2 tokens (8). The
donor cue columns differ from the same-episode donor only via attention to one or
two swapped nouns, and 63/64 and 64/64 shuffled outputs are token-identical to the
text bar. This is the expected near-invariance to a tiny prefix edit, not evidence
that "cue KV transfers across contexts". The README wording ("after another
episode's neutral context") is literally true but overstates the diagnostic.

### F3 (what is genuinely new): the partial-write arms.
- K-only and V-only both 0/64 (copy). V-only outputs are bitwise identical to OFF
  (filler keys draw no attention, so cue values are invisible); K-only draws
  attention to cue-shaped keys but filler values carry no instruction, changing
  only formatting whitespace. Both K and V of the cue columns are required; this is
  the one clean mechanistic fact in Part 1.
- layers>=12 only: 58/57 exact but only 52/59 token-identical to text. Layers 0-11
  of the cue columns can stay filler and the task still lands, with detectable
  downstream drift. This is a real, non-tautological reduction result.
- CLEAR restoring filler columns still sorts 30/27 of 32 (in-context pattern), and
  SWITCH by overwriting the old position fails 3/32 A->B, 17/32 B->A.

### F4 (medium): SWITCH failure is not explained by "prior answers dominate any cue".
Part 2 gives the controlling contrast: three completed A turns in history plus a B
cue at the current user position -> 60/64 B (and A after three B turns 60/64).
In-context answers alone do not beat a cue at the current position. In SWITCH the
new cue is written at the OLD system position (64-75) while every downstream column
(im_end, first query, SET answer, filler turn, HOLD answer, ~360 columns) was
computed attending to the old cue and encodes it. all_A SWITCH outputs are clean
ascending sorts of the new list in 28/32; all_B SWITCH is messier (12 "other",
mostly partial or garbled orderings), consistent with a competition between the
new B->A cue and stale B-encoded history rather than a null write. Which of
(i) stale downstream K/V or (ii) the model discounting a system-position cue
against recent same-format answers dominates cannot be decided from these records
(no attention captured); both are consistent with all rows. CLEAR is simpler: with
no cue anywhere in the final turn, two prior sorted answers are a two-shot pattern
and sorting is the expected continuation; it is not evidence that the restore failed.

Confound to note in the retained design: the HOLD filler is a user turn with no
assistant reply, so the SWITCH/BACK/CLEAR queries follow two consecutive user turns.
all_B HOLD drift (23/32, vs 32/32 for A) partly reflects this malformed structure;
SWITCH B->A success is not strongly conditioned on HOLD success ((HOLD ok, SWITCH
ok): 10; (ok, fail): 13; (fail, ok): 7; (fail, fail): 2).

### F5 (low): the bitwise HOLD/CLEAR checks are cache-implementation facts.
The cache is append-only (torch.cat in Attention.forward); nothing in a forward pass
can modify earlier columns, so HOLD retention 64/64 is guaranteed by construction.
CLEAR restoration is a real check of the copy. README line 110 is careful but should
say the retention check verifies the harness, not the model.

### F6 (low): Part 2 isolates a different question from Part 1's SWITCH.
Part 2 varies history content with the cue re-stated at the current position; Part 1
varies the cue at a fixed old position with history held. Part 2 therefore does not
test Part 1's failure mode; it bounds it (see F4). Part 2 also lacks a B_after_B
history-length control, but with a zero difference that omission cannot hide an
effect. Stickiness verdict NOT SUPPORTED is correct as registered; prior turns
184/192 and 178/192 retained unscreened as claimed.

## 3. Plain answers

(a) Is the positive control real and clean? Real and clean as executed: no leak,
correct positions/layers/kinds, denominators right, copy default holds, records
complete. But the headline 59/64 and 60/64 are the text bar by construction (F1),
so "positive" means "the harness can rebuild the text prompt's cache", not "an
instruction was transferred". The non-trivial positives are layers>=12 (58/57) and
the K+V-both-required result.

(b) Content-free in a Miller sense? No. The transplanted object is the instruction's
own token representation at its own positions; it is content-bound, position-bound
(post-RoPE), and context-bound (only tested under a 1-2-token context change). It
shows: the task decision for this prompt is carried by K and V jointly of the 12 cue
columns, and layers 0-11 of those columns are dispensable. It does not show a
compact task state, transfer across different contexts or positions, or any
set/switch/clear control in retained history (3/32, 5/32 joint).

(c) Single cheapest next test: run the SWITCH histories as plain text. Take each
retained episode's recorded token history (recorded per row; audit reconstructs
1088 histories bitwise), replace the system cue text with the SWITCH target's cue,
and re-prefill from scratch, then answer the SWITCH query. By causality this is
identical to "recompute all downstream K/V after the cue write", so one 32+32-row
text run (~1 GPU-minute at this check's rate) decides F4: if the text bar yields the
new task, SWITCH failed because of stale downstream K/V and the fix is to evict or
re-prefill the post-cue columns (KVCache.evict already supports dropping a column
range while keeping absolute positions, qwen3.py:70); if the text bar also yields
the old task, no surgery at the old position can work and the cue must be placed at
the current position (which, for an all-layer same-history donor, is again just the
text). Do this before any current-position transplant, because a current-position
donor must be prefilled on the same history to have valid RoPE and is then the text
bar by F1.

## 4. Requested README edits (no severity block; the numbers stand)

1. State at line 85/87 that all-layer same-episode transplant reconstructs the
   text-arm cache exactly by causality, so token identity is expected.
2. Qualify "shuffled donor" as a 1-2-token context perturbation.
3. Note the two-consecutive-user-turn structure of HOLD.
4. Add the Part 2 vs SWITCH contrast (history + current-position cue: 60/64; old-
   position overwrite with history: 3/32) as the finding that motivates the text-bar
   test above.
