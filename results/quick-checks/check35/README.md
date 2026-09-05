# Quick check 35 — recent cue addresses and answer release

UNREGISTERED, disclosed exploratory check, authorized 2026-09-05; seed 35035;
Qwen3-4B only. Fit-on=none; donors=operand/answer-free text; evaluation=192 fresh
synthetic lists, unique by unordered set, paired across all arms and CLEAR forks.
No fitting, training, benchmark input or response access. Not registered evidence.

## Fixed readings and implementation choices (written before GPU execution)

Reuse scripts/focus_check34.py: A ascending, B descending, 5–8 distinct integers
in -20..20, excluding already ascending/descending inputs; same lenient scorer,
strict JSON diagnostic, A/B/copy/other taxonomy and breakage (cap/repetition/parse).
Frozen bf16 hf_compatible greedy Qwen3-4B, at most 64 generated tokens per answer.
32 episodes per arm: SET(A), HOLD with 128 filler-body tokens and no reapplication,
SWITCH(B), BACK(A), CLEAR(copy target), NEUTRAL(second fresh copy target).
Both copy targets use check 34's cue-absent "Process these integers" query, so an
explicit copy command cannot conceal residual imposition. All actual outputs remain
in history except the explicitly evicted answer columns; no answer substitution.

S1: overwrite original columns 64–75 with B at SWITCH and A at BACK; CLEAR restores
original filler. S2: append B's 12 cue+suffix columns at SWITCH and A's at BACK,
leaving older addresses intact. S3: evict prior answers then overwrite original
address at SWITCH and BACK; default CLEAR is c2. S4: evict answers at SWITCH and
BACK but keep A (release-only control); CLEAR restores filler and evicts answers.
S5: evict prior answers and append recent address at SWITCH and BACK; default c2.
TEXT: same transplanted SET/HOLD, real B/A sentence in the current user query at
SWITCH/BACK; CLEAR restores original filler and appends the real neutral OFF
sentence in the user query, retaining history. It is the real-text switching bar.

S2/S3/S5 fork the identical post-BACK cache into c1/c2/c3 (32 paired episodes each):
c1 restores filler at ALL previously written address slots, no answer eviction;
c2 does c1 and evicts ALL remaining model-answer columns; c3 only appends the OFF
neutral cue+suffix packet at the current position, leaving old addresses/answers.
S2 default=c1; S3/S5 default=c2. These defaults add no extra runs. No second CLEAR
operation before NEUTRAL: this tests persistence without another intervention.
Eviction includes generated answer tokens and EOS (forced closing EOS if capped),
not prompt/assistant-header tokens or manually added newline. All user prompts,
filler and downstream non-answer columns survive; their cached states may carry
old-task information. Release does not claim a clean reconstruction of history.

Recent addresses occupy a fresh operand-free 12-column slot directly before the
next user request. No model forward processes recipient cue tokens: append actual
donor K/V, all layers, both K/V, then process the normal user-list query. For each
slot at p, extract the same check-34 operand-free 76-token donor prefix with RoPE
offset p-64 and take its last 12 columns. Thus donor cue positions exactly match
p..p+11; no approximate re-rotation of bf16 keys. The donor's preceding neutral
prefix is not inserted. OFF restoration uses the matching operand-free OFF donor;
at the original slot it is the recipient's original filler packet. Virtual slot
history IDs identify OFF placeholders, not recipient-processed text. Every write
and eviction records absolute positions, physical column indices, all layer IDs,
raw-byte equality assertions and donor hashes/tokens. Eviction uses KVCache.evict,
keeps cache.length (the next absolute position), and verifies every survivor byte.
HOLD verifies all address columns unchanged through filler, with zero writes.

An arm SOLVES SWITCH iff SWITCH >=26/32 B and BACK >=26/32 A, with <=1/32
episodes having any broken output across SWITCH/BACK (conservative union).
SOLVES CLEAR iff impositions (exact A or B output) <=3/32 at CLEAR AND <=3/32
at NEUTRAL. This threshold alone does not establish successful copying: report
copy and breakage separately. Report joint exact SET+HOLD+SWITCH+BACK+CLEAR,
and the stricter joint including NEUTRAL. S4 must retain A at SWITCH >=26/32 or
the release interpretation is VOID. S4 joint uses the requested B target at SWITCH
for comparability; separately report its intended A-control success. Always report
A/B/copy/other per step, including when no arm solves SWITCH. No outcome tuning.

Initial nvidia-smi: no compute apps, 0% utilization; no review lock. Foreground
only, no process signals/termination/background jobs. Cooperative 45 GPU-minute
cap (including load/extraction); stop if foreign compute appears. Save every scored
record in the same run and preserve partial outcomes. WORKLOG is the operational
ledger for this quick check (legacy protocol/ledger are archived).

## Results

Completed all 32 paired episodes in **27.52/45 GPU-minutes**; **1,536 scored records**, with CLEAR variants branched from identical post-BACK caches.

### SET through BACK (shared by each arm’s CLEAR variants)

| Arm | Step | n | Target exact | Strict exact | A | B | Copy | Other | Breakage |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| S1 | SET | 32 | 29 | 29 | 29 | 0 | 0 | 3 | 0 |
| S1 | HOLD | 32 | 31 | 31 | 31 | 0 | 0 | 1 | 0 |
| S1 | SWITCH | 32 | 3 | 3 | 28 | 3 | 1 | 0 | 0 |
| S1 | BACK | 32 | 32 | 32 | 32 | 0 | 0 | 0 | 0 |
| S2 | SET | 32 | 29 | 29 | 29 | 0 | 0 | 3 | 0 |
| S2 | HOLD | 32 | 31 | 31 | 31 | 0 | 0 | 1 | 0 |
| S2 | SWITCH | 32 | 0 | 0 | 32 | 0 | 0 | 0 | 0 |
| S2 | BACK | 32 | 32 | 32 | 32 | 0 | 0 | 0 | 0 |
| S3 | SET | 32 | 29 | 29 | 29 | 0 | 0 | 3 | 0 |
| S3 | HOLD | 32 | 31 | 31 | 31 | 0 | 0 | 1 | 0 |
| S3 | SWITCH | 32 | 12 | 12 | 17 | 12 | 1 | 2 | 0 |
| S3 | BACK | 32 | 18 | 18 | 18 | 0 | 11 | 3 | 0 |
| S4 | SET | 32 | 29 | 29 | 29 | 0 | 0 | 3 | 0 |
| S4 | HOLD | 32 | 31 | 31 | 31 | 0 | 0 | 1 | 0 |
| S4 | SWITCH | 32 | 0 | 0 | 27 | 0 | 3 | 2 | 0 |
| S4 | BACK | 32 | 17 | 17 | 17 | 0 | 10 | 5 | 0 |
| S5 | SET | 32 | 29 | 29 | 29 | 0 | 0 | 3 | 0 |
| S5 | HOLD | 32 | 31 | 31 | 31 | 0 | 0 | 1 | 0 |
| S5 | SWITCH | 32 | 9 | 9 | 22 | 9 | 0 | 1 | 0 |
| S5 | BACK | 32 | 30 | 29 | 30 | 0 | 1 | 1 | 0 |
| TEXT | SET | 32 | 29 | 29 | 29 | 0 | 0 | 3 | 0 |
| TEXT | HOLD | 32 | 31 | 31 | 31 | 0 | 0 | 1 | 0 |
| TEXT | SWITCH | 32 | 27 | 27 | 1 | 27 | 0 | 4 | 0 |
| TEXT | BACK | 32 | 29 | 29 | 29 | 0 | 0 | 3 | 1 |

### CLEAR and subsequent neutral request

c1 = restore all address slots; c2 = restore all slots plus answer eviction; c3 = append neutral OFF columns only. TEXT restores the initial slot and adds the real neutral sentence. The NEUTRAL request has no additional operation. All denominators are 32.

| Arm / variant | Step | Copy exact | Strict copy | A | B | Other | Impositions (A+B) | Breakage |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| S1/c1 | CLEAR | 0 | 0 | 30 | 0 | 2 | 30 | 0 |
| S1/c1 | NEUTRAL | 0 | 0 | 31 | 0 | 1 | 31 | 0 |
| S2/c1 | CLEAR | 0 | 0 | 32 | 0 | 0 | 32 | 0 |
| S2/c1 | NEUTRAL | 0 | 0 | 31 | 0 | 1 | 31 | 0 |
| S2/c2 | CLEAR | 25 | 25 | 3 | 0 | 4 | 3 | 1 |
| S2/c2 | NEUTRAL | 25 | 25 | 6 | 0 | 1 | 6 | 0 |
| S2/c3 | CLEAR | 0 | 0 | 32 | 0 | 0 | 32 | 0 |
| S2/c3 | NEUTRAL | 0 | 0 | 32 | 0 | 0 | 32 | 0 |
| S3/c1 | CLEAR | 11 | 11 | 20 | 0 | 1 | 20 | 0 |
| S3/c1 | NEUTRAL | 11 | 11 | 20 | 0 | 1 | 20 | 0 |
| S3/c2 | CLEAR | 27 | 27 | 4 | 0 | 1 | 4 | 0 |
| S3/c2 | NEUTRAL | 28 | 28 | 1 | 0 | 3 | 1 | 0 |
| S3/c3 | CLEAR | 10 | 10 | 22 | 0 | 0 | 22 | 0 |
| S3/c3 | NEUTRAL | 9 | 9 | 23 | 0 | 0 | 23 | 0 |
| S4/c2 | CLEAR | 27 | 27 | 4 | 0 | 1 | 4 | 0 |
| S4/c2 | NEUTRAL | 26 | 26 | 4 | 0 | 2 | 4 | 0 |
| S5/c1 | CLEAR | 1 | 1 | 29 | 0 | 2 | 29 | 0 |
| S5/c1 | NEUTRAL | 1 | 1 | 30 | 0 | 1 | 30 | 0 |
| S5/c2 | CLEAR | 27 | 27 | 3 | 0 | 2 | 3 | 1 |
| S5/c2 | NEUTRAL | 26 | 26 | 5 | 0 | 1 | 5 | 0 |
| S5/c3 | CLEAR | 1 | 1 | 30 | 0 | 1 | 30 | 0 |
| S5/c3 | NEUTRAL | 0 | 0 | 31 | 0 | 1 | 31 | 0 |
| TEXT/text | CLEAR | 0 | 0 | 32 | 0 | 0 | 32 | 0 |
| TEXT/text | NEUTRAL | 0 | 0 | 32 | 0 | 0 | 32 | 0 |

### Fixed readings and joint outcomes

| Arm / variant | SWITCH B | BACK A | Broken SWITCH/BACK episodes | Solves SWITCH | Solves CLEAR | Joint first five | Joint all six |
|---|---:|---:|---:|---|---|---:|---:|
| S1/c1 | 3/32 | 32/32 | 0/32 | NO | NO | 0/32 | 0/32 |
| S2/c1 | 0/32 | 32/32 | 0/32 | NO | NO | 0/32 | 0/32 |
| S2/c2 | 0/32 | 32/32 | 0/32 | NO | NO | 0/32 | 0/32 |
| S2/c3 | 0/32 | 32/32 | 0/32 | NO | NO | 0/32 | 0/32 |
| S3/c1 | 12/32 | 18/32 | 0/32 | NO | NO | 0/32 | 0/32 |
| S3/c2 | 12/32 | 18/32 | 0/32 | NO | NO | 3/32 | 3/32 |
| S3/c3 | 12/32 | 18/32 | 0/32 | NO | NO | 0/32 | 0/32 |
| S4/c2 | 0/32 | 17/32 | 0/32 | NO | NO | 0/32 | 0/32 |
| S5/c1 | 9/32 | 30/32 | 0/32 | NO | NO | 0/32 | 0/32 |
| S5/c2 | 9/32 | 30/32 | 0/32 | NO | NO | 8/32 | 8/32 |
| S5/c3 | 9/32 | 30/32 | 0/32 | NO | NO | 0/32 | 0/32 |
| TEXT/text | 27/32 | 29/32 | 1/32 | YES | NO | 0/32 | 0/32 |

S4 release-only control: **27/32 still A**, 0/32 B, 3/32 copy, 2/32 other. Release interpretation: **VALID under the fixed control rule**.

A/B/copy/other are mutually exclusive; breakage is an overlapping flag. Joint first five requires exact A/A/B/A/copy, even for S4; joint all six also requires the second copy. The CLEAR rule measures absence of exact task imposition; copy and breakage columns expose cases where other outputs would meet that rule.

### Conclusion

**TEXT solves SWITCH; none of the cache arms solves SWITCH, and no arm solves CLEAR.** SET/HOLD remained positive at 29/32 and 31/32 in every arm. The S1 baseline reproduced check 34’s 3/32 SWITCH result, with 28/32 still A. A recent address alone (S2) switched 0/32: all 32 still produced A. Eviction plus original-address overwrite (S3) reached 12/32 SWITCH but only 18/32 BACK. Eviction plus a recent address (S5) reached 9/32 SWITCH and 30/32 BACK. TEXT reached 27/32 SWITCH and 29/32 BACK with one broken SWITCH/BACK episode, meeting the fixed rule. The S4 control retained A in 27/32 SWITCH requests and produced B in zero.

Restoring filler plus evicting answers produced far fewer observed CLEAR impositions than restoration alone, but did not meet the two-request rule. S2/c2 had 3/32 impositions at CLEAR and **6/32 on the next neutral request**; S5/c2 had 3/32 then **5/32**. S3/c2 had **4/32** at CLEAR and 1/32 next, missing the initial limit. Appending OFF alone left 22–32/32 impositions at CLEAR and 23–32/32 next across S2/S3/S5. Joint exact SET+HOLD+SWITCH+BACK+CLEAR was best for S5/c2 at **8/32**, then S3/c2 at **3/32**; every other arm/variant was 0/32. Adding the second copy to the joint criterion leaves those counts unchanged.

These tested cache operations do not provide reliable switch-and-clear control. The observed reduction in sorting after answer eviction is consistent with prior answers contributing to persistence, but deleting answers does not remove every history carrier: retained query, assistant-header and other downstream K/V were computed under the old task. Recurrence on the second copy makes that limitation visible. The recent-slot result applies to the explicitly described operand-free system-prefix donor placed before the next user request; it does not rule out every possible address layout. CLEAR here targets copying through the same cue-absent Process request as check 34, without an explicit copy instruction.

### Validation and scope

The CPU audit recomputed all scores and summaries, checked fresh operand banks and exact prompts, replayed the specified interventions, and reconstructed absolute/physical positions, answer spans, token histories and their hashes for every episode and CLEAR fork. Runtime assertions checked raw bytes of every copied/appended address and every survivor of writes/evictions. HOLD checks made zero writes. Donor extraction tokens, destination-matched RoPE offsets, and raw bf16 packet hashes are recorded; donor tensors were held in memory and are not a persisted tensor archive.

CPU tests covered check 34’s scorer and retained generation plus sparse-cache generation, append and eviction through the actual check-35 consumer. Lint and import-side-effect tests passed. The executed-script and prewritten-reading hashes are verified; the prewritten section is byte-preserved.

Artifacts: [summary](4b/summary.json), [per-step records](4b/records.jsonl), [exact writes and evictions](4b/operations.jsonl), [donor provenance](4b/donors.jsonl), [lists](4b/episodes.json), [layout](4b/layout.json), [validation](4b/validation.json), [CPU audit](audit.py), [foreground log](4b/run.log).
