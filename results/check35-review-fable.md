# Check 35 review (fable, one round, CPU-only) — commit 3df60fd

Scope: results/quick-checks/check35/README.md, 4b/{summary.json, records.jsonl,
operations.jsonl, donors.jsonl, layout.json, episodes.json, validation.json,
run.log}, audit.py, report.py, scripts/focus_check35.py, and the reused
src/stencil/qwen3.py cache/RoPE/attention code. No model launched. Every number
below was recomputed from records.jsonl/operations.jsonl with an independent
script; audit.py was also re-run and reproduced validation.json byte-for-byte.

## 1. Bookkeeping — verified, no discrepancies

- Denominators: 48 (arm, variant, step) cells, every cell n=32; 1536 records =
  6 arms x 4 shared steps x 32 + 12 variants x 2 CLEAR steps x 32. Every per-step
  count in summary.json (exact, strict, A/B/copy/other, breakage) recomputed
  identically for all 12 arm/variant rows; no record is exact for two targets.
  Targets: SWITCH=B, BACK=A, CLEAR/NEUTRAL=OFF, as registered. 1600 operations
  (864 write, 320 evict_answers, 224 append, 192 hold_check); 286 donors.
- Eviction really removed the answer columns: for all 320 evict ops the evicted
  positions equal exactly the retained answer positions of the lineage (generated
  tokens + EOS, or forced im_end when capped), all 36 layers, both K and V,
  `absolute_next` equals the preceding record's cache_length_after (RoPE index
  not reduced, per KVCache.evict, qwen3.py:70-85), survivors contain no answer
  position. Every c2 CLEAR cache holds zero prior-answer columns (0/32 for each of
  S2/S3/S4/S5). Downstream tokens still get RoPE at cache.length (qwen3.py:404)
  and the causal mask is built from the physical column count (qwen3.py:302), so
  a sparse cache is attended correctly.
- S2/S5 appended columns are at the recent position with matched RoPE: every
  append starts at the recipient's cache_length (224/224), physical indices
  correct after eviction, and the donor for slot p was prefilled with
  cache.length = p-64 (prefix_rope_offset = p-64 for all 286 donors), so the
  donor's columns 64-75 received positions p..p+11 before capture; the recipient
  query is then rotated at p+12 onward. Same (episode, task) donors at different
  starts have distinct packet hashes (K really rotated). This is NOT a RoPE
  position mismatch. It is a context mismatch (section 2, F2).
- Hashes/provenance: script, reused-script and prewritten-reading hashes verify;
  every write/append after_sha256 equals the donor packet hash; CLEAR restores
  equal the stored filler hashes; HOLD checks record zero writes. Run 27.52 min,
  no foreign compute, source commit d3e3ee5 (the run preceded the artifact
  commit; the script hash matches the committed file).

## 2. Substantive findings

### F1 (real, paired, large): evicting the model's own answers restores copying.
Paired McNemar within arm (c2 vs c1 on identical post-BACK caches): S2 25 vs 0
(p=6e-8), S3 17 vs 1 (p=1e-4), S5 26 vs 0 (p=3e-8) at CLEAR; the same at
NEUTRAL. S4/c2 27/26 and S3/c2 27/28 copy. This is not noise and the bookkeeping
is clean. But what it shows is narrower than "release of the old task": the
history's answers are few-shot demonstrations, and the model continues the
last visible answer's pattern. Direct evidence: S3 BACK copied in 11 episodes and
S3/c1 CLEAR copied in exactly those 11 episodes (identical sets); S4 BACK copied
in 10 of the same 11. Remove the demonstrations (c2) and the cue-absent default
(copy, 64/64 in check 34) reappears. Residual impositions (3-6/32) and the
CLEAR->NEUTRAL flips (S2/c2 3 other->A, S5/c2 2 other->A and 1 copy->A; S3/c2
only 1 A persists) come from surviving columns computed under A.

### F2 (medium, interpretive): S2's 0/32 is a context/competition result, not a position result.
RoPE is matched (section 1). What differs from the text bar: (i) the packet's K/V
were computed attending to a phantom system prompt at p-64..p-1, not to the real
history at those positions; (ii) it sits after a user turn's im_end with no role
marker; (iii) it competes against an in-context A cue at 64 AND four/two A
answers. The packet is not inert: S5 vs S4 (only difference = appended packets)
gives SWITCH B 9 vs 0 (p=0.004) and BACK A 30 vs 17 (p=2e-4, S5-only 13,
S4-only 0), i.e. the recent packet raises the agreeing task and partially
imposes the disagreeing one. So "a recent address alone switched 0/32" (README
conclusion) is true of S2 but should not be read as "recent out-of-context
packets do nothing": they lose to an in-context cue plus history. The clean
test (evict answers, restore filler at 64, append B) was not run; and the
text-equivalent control (the literal 12 cue tokens processed in context at the
same place, by causality = recompute) is what would separate "out-of-context
K/V" from "cue at that place".

### F3 (real, partial): S3's 12/32 is a release effect, not noise.
S3 vs S4 SWITCH (paired; identical except B vs A at 64 after the same eviction):
12 vs 0 B, p=5e-4. S3 vs S1 (eviction vs none): 11 vs 2 discordant, p=0.02.
Both cache SWITCH gains (S1 3 -> S3 12; S2 0 -> S5 9) are eviction-enabled.
Still 17/32 A in S3 with NO A cue anywhere except the surviving non-answer
columns (im_end, SET/HOLD queries with assistant headers and think tokens, HOLD
filler turn, newlines; ~410 columns computed under A). That is direct evidence
that stale downstream non-answer K/V carry the task, which is the check-34 F4
stale-columns hypothesis; check 36 (recompute after overwrite) is the right
decider and my check-34 prediction stands: re-prefilled text should give B.

### F4 (medium): eviction is a lossy, cumulative operation, not a clean primitive.
S4 (A at 64 untouched throughout, answers evicted at SWITCH and again at BACK):
SWITCH 27 A / 3 copy / 2 other, BACK 17 A / 10 copy / 5 other. With the cue
intact, a second eviction drops A adherence 28 -> 17. Each eviction leaves a
malformed turn (assistant header + empty think block + "\n", no content, no
im_end); after two, the context is four unanswered requests and the model drifts
to copy/other. S3 BACK (18 A, 11 copy) equals S4 BACK (p=1), so BACK's A write
in S3 did nothing beyond what the eviction structure dictated. S5 BACK 30 A shows
the appended A packet compensates (F2). The README reports S4 SWITCH 27/32 as
"control valid" (correct under the fixed rule) but does not flag the 17/32 BACK,
which is the number that limits eviction as a reusable release op.

### F5 (medium, fairness): "TEXT CLEAR 32/32 impositions" is not a text-can't-do-it bar.
TEXT/text CLEAR keeps four sorted answers in history and adds a neutral sentence
in the user turn; 32/32 A is the expected few-shot continuation (as I noted for
check 34 CLEAR). The text analog of c2 is editing the history (re-prefill without
the answers), which any prompt controller can do; that was not run, so "text
cannot release, eviction can" is not established. What IS established: eviction
is the only way to remove demonstrations WITHOUT recomputing the remaining
~400 columns, and it costs 3-6/32 residual impositions plus the F4 damage. Also
note TEXT's SET is itself the cache write (all arms share it), i.e. the text
prompt by check-34 F1; only SWITCH/BACK/CLEAR of TEXT use real user-turn text.
TEXT SWITCH "other" 4/32 are partial/garbled orderings, not A; BACK break 1/32
(ep 24, a duplicated element) — the 27/29 pass is genuine.

### F6 (low): carried-over confounds and wording.
HOLD is still a user filler turn with no assistant reply, so every SWITCH/BACK
query follows two consecutive user turns (check-34 F4). All arms batch
identically at SET (texts identical across arms), so the shared 29/32 is one
measurement, not six. "Recent address" packets carry a system-prompt-flavoured
context and are placed outside any role; the README's scope sentence ("does not
rule out every possible address layout") is correct but understates that the
in-role, in-context version of the same packet is, by causality, the text bar.

## 3. Plain answers

(a) Is "eviction of the model's own prior answers releases the old task" real and
clean? Real: paired, large, bookkeeping verified, the evicted columns are exactly
the answers with positions/layers/RoPE preserved, and zero answer columns remain.
Clean as a measurement, not as a mechanism claim: it removes in-context
demonstrations (the last answer's pattern is what the model continues, F1),
leaves 3-6/32 impositions from stale non-answer columns, fails the registered
two-request rule, and is cumulative damage (F4: 17/32 A with the cue intact after
two evictions). "Release" = "delete the few-shot examples without recompute".

(b) Is the SWITCH failure consistent with stale downstream columns and with a
position-mismatched transplant for S2? Stale columns: yes, and now directly
supported — after answer eviction, B at the old address gives 12/32 (vs 0/32 for
the S4 control) while 17/32 remain A with no A cue anywhere except stale
query/header/filler K/V. Check 36's recompute-after-overwrite is the decisive
test. S2: NOT a RoPE mismatch (offsets verified). It is an out-of-context packet
(computed against a phantom prefix, placed role-less) competing with an in-
context cue plus answers; S5 vs S4 shows the packet does act (9 vs 0 B; 30 vs 17
A) but cannot beat the in-context cue. The 0/32 is a precedence/context result
with two untested controls (F2).

(c) Miller-style set/hold/switch/clear on a frozen trunk — what works via which
channel: SET works via text or via same-history state transplant at the original
address (which is text by construction; K+V jointly, layers>=12 suffice, check
34). HOLD is free (append-only cache). SWITCH works via text at the current user
position (27/32) and via nothing else tested: overwrite at the old address 3/32
(stale downstream), overwrite after answer eviction 12/32, out-of-context recent
packet 0/32 (9/32 after eviction). CLEAR does not work via text-in-context
(32/32 continuation) nor via filler restore (30-32/32) nor via a neutral packet
(c3, 22-32/32); it works partially via eviction of own answers (25-28/32 copy,
1-6 residual, cumulative damage). Net: on this trunk the task is carried by
in-context columns (cue + its downstream + answers), so every operation that
works is one that changes what the next query attends to in context — text, or
deletion. No operation yet acts through a compact transplanted state; a
current-position in-context packet is the text bar, and an out-of-context packet
loses to history. If check 36 shows recompute-after-overwrite switches, the
consistent model is "address write + downstream recompute" = re-prefill, i.e.
the cache route collapses to text editing with eviction as its only recompute-
free primitive.

## 4. Requested README edits (numbers stand; no severity block)

1. Add the S5-vs-S4 paired contrast (SWITCH B 9 vs 0; BACK A 30 vs 17) so the
   recent-address packet is not described as inert.
2. Report S4 BACK 17/32 A next to "control valid" and name eviction as cumulative.
3. State that S2's failure is not a RoPE-position mismatch (offsets matched) and
   list the two missing controls (evict+restore+append; in-context text at the
   same place).
4. Qualify the TEXT CLEAR 32/32 as few-shot continuation, and that the text
   analog of c2 (history edit + re-prefill) was not run.
5. Note the S3 BACK copy set == S3/c1 CLEAR copy set (11 = 11) as the evidence
   that CLEAR/NEUTRAL outputs track the last visible answer.
