# Check 38 review (fable, one round, CPU-only) — commit 1d99598

Scope: results/quick-checks/check38/README.md, 4b/ (summary.json, records.jsonl,
prewritten-reading.md, audit.json), scripts/focus_check38.py; my proposal in
results/check36-review-fable.md section 2.5 (arms 1-4 = T1..T4, R3 replicate).
Cross-reads (raw records only): check36 histories/R3 records, check35 S1 and TEXT
records, check34 all_B/off/text_B/B_fresh records. No model launched; no sealed
IFEval/BFCL content read; no repo edits besides this file.

## Verdict: ACCURATE (all numbers reproduce); interpretation needs two additions

The README's fixed reading was applied mechanically and its text is honest
("NONE of the three fixed thresholds met"; failing a threshold is not absence of
effect). The orchestrator's paraphrase "PATTERN dominates; role no effect;
recency partial" is NOT the README's reading and over-reads it: PATTERN was NOT
met (T2 B 12/32 < 24), and RECENCY is a real paired effect (10 gains / 0 losses,
conservative interval [0.4, 53.7] pp) that simply falls under a 12/32 bar.

## 1. Bookkeeping — verified from raw records, independently of audit.json

- 320 records, 10 (arm, step) cells x 32, no duplicate (arm, step, episode).
- Independent relabel of every output text (json parse -> A/B/copy/other):
  0 mismatches with the stored value-exact labels; all 10 value-exact rows and
  all 10 strict rows in the README match; breakage 1/320 (T4 BACK ep 24,
  repeated -2) matches.
- Wilson 95% intervals recomputed for all 40 category cells: equal to 1e-12.
  Difference intervals recomputed (97.5% marginal bounds subtracted):
  ROLE [-22.4, 17.0] pp, RECENCY [0.4, 53.7] pp — as reported.
- Paired sets (SWITCH value-exact B): T1 {12}; R3 {7, 12}; T2 {5,7,11,12,17,21,
  22,24,27,28,29,30}; T4 {1,2,5,6,12,14,17,18,22,24,29}. ROLE gains/losses 0/1,
  RECENCY 10/0 — as reported.
- R3 replicate: 64/64 generated token sequences and EOS ids equal to check-36 R3
  (recomputed here). R3 SWITCH prefills are bitwise the check-36 histories with
  tokens 64-71 replaced by the B cue.
- Layouts (all 320 prefills decoded and checked):
  every request equals the check-36 query token ids and contains no cue; the A
  cue occurs in no SWITCH prefill, the B cue in no BACK prefill, and the OFF
  sentence nowhere; the S1 SET and HOLD generated token ids occur as exact
  subsequences in every non-T2 prefill and in no T2 prefill; assistant turns are
  2/3 (SWITCH/BACK) in T1/T3/T4/R3 and 0/1 in T2. Cue placement: T1 = sole cue
  in turn 1 (user, token 73) after a cue-free system; T2/R3 = system slot;
  T3 SWITCH = no cue anywhere, T3 BACK = system slot; T4 = sole cue in the last
  turn (user), 10 tokens before the request, after the last assistant answer.
  BACK prefills contain each arm's own SWITCH exchange verbatim; T4 BACK drops
  the SWITCH-time B user turn (as the reading says: "replacing the prior cue
  event").
- Reading: prewritten-reading.md sha256 == summary.reading_sha256, and the
  README begins with it verbatim. Thresholds applied mechanically: ROLE -1 < 12;
  PATTERN 31 >= 24 but 12 < 24; RECENCY 10 < 12.
- (low) The reading was fixed by the script copying README.md at run start, not
  by a commit: README.md does not exist at source_commit 2ea04e9; script, README
  and results were committed together in 1d99598. Self-attested pre-fixing with
  a hash is adequate for a disclosed quick check but is not a git-timestamped
  anchor; say so in the README.

## 2. Substantive findings

### 2.1 (high, interpretive) Most of the old cue's loss happens BEFORE any demonstration exists.

Check34 all_B SET is the same B cue in the same system slot (cache-copied, but
check34 text_B == B_fresh 60/64 and check36 R2 == R3 64/64 make text/cache
immaterial) followed directly by a list request: 31/32 B. Check38 T2 is the same
system B cue followed by ONE unanswered neutral user turn (the recorded filler,
~130 tokens) and then the request, with no prior answers anywhere: 12/32 B,
12 A, 5 copy, 3 other. Demonstrations then take 12 -> 2 (paired T2 vs R3: R3's
{7, 12} is a subset of T2's twelve; 10 gains / 0 losses).

So on this trunk/task the deficit of an old standing instruction splits roughly
19/32 "decays across one intervening neutral turn with no answers at all" plus
10/32 "contrary own answers". "The model's own prior answers dominate a standing
instruction" attributes the whole deficit to the answers; the records attribute
at most a third of it to them. Caveats: all_B SET used SET lists, T2 used SWITCH
lists (direction should not depend on the list); the comparison is across
checks, not paired; the filler is an unanswered user turn (see 2.4).

### 2.2 (medium) "Ascending default prior" is a sort-present default, not a cue-free default.

With no cue and no demonstrations the trunk copies (check34 off: 64/64 copy).
T2's 12 A (+5 copy, +3 other) appear once a sort instruction is present but
weakly bound; check36 R4's 14/32 A with no A content in the cache is the same
phenomenon. Consequently T3's 31/32 A (demos, no cue) is genuinely the
demonstrations (the no-demo, no-cue outcome would be copy), but T3 cannot say
whether demos beat a live instruction; only the T2 -> R3 paired 10/32 does.
The README's caveat that T3 "cannot distinguish imitation from an ascending
default" is right in spirit but the stronger statement is available: the
cue-free, demo-free default is copy, so T3 is not the default.

### 2.3 (high, interpretive) Same-turn vs previous-turn: it is turn structure, not age.

Check35 TEXT is the in-request form of T4: I verified all 32 SWITCH lists are
identical to check38's, TEXT's SET/HOLD requests carry no cue text (the A cue
was cache-transplanted), so its demonstrations are cue-free requests answered A
exactly like T4's, and its SWITCH request is the B sentence + the list request
in ONE user turn. TEXT 27/32 B vs T4 11/32 B, and T4's eleven are a subset of
TEXT's 27 (16 TEXT-only, 0 T4-only). T4's cue is 10 tokens before the request;
age cannot explain a 16/32 one-directional gap. Residual differences: TEXT's
demo answers are its own (29/32, 31/32 A) rather than S1's (60/64 A); TEXT's
history was built with cache ops; T4's cue turn is an unanswered user turn.

### 2.4 (medium) Consecutive user turns are a structural confound in T1, T2, T4 and the filler.

T1's cue turn is immediately followed by the SET user turn; T4's cue turn
immediately precedes the request user turn; T2 is system + unanswered filler +
request; and every arm's filler is an unanswered user turn (inherited from
S1). Qwen's chat template has no user-user adjacency, so "separate user turn"
may partly be "malformed turn". This does not disturb the within-check38
contrasts (all arms share the filler; T1 and R3 both give ~0), but it means
T4's 11/32 may be depressed by structure rather than by "previous turn", and
T2's 12/32 decay (2.1) is measured under an odd history. The clean forms are:
cue as a user turn with an assistant acknowledgment, and cue + request in one
turn (= TEXT). Age proper (tokens since the cue, after the demonstrations) is
untested: T1 differs from T4 in age AND in being before vs after the
demonstrations; a cue placed after the demos with one neutral pair before the
request would separate them.

### 2.5 (low) Minor observations

- T2 BACK: after the 12 B SWITCH answers, BACK (old-slot A cue, one contrary B
  demo) gives A 6 / B 3 / other 3 — one fresh contrary answer already halves an
  old cue; n = 12, descriptive only.
- T4 B episodes intersect the four malformed-demo episodes {1, 6, 9, 13} at
  {1, 6}: 2/4 vs 9/28 overall; nothing to read.
- R3 and T2 produce the identical copy output at episode 10 with and without
  the demonstrations — the copy fallback is list-driven, not history-driven.

## 3. Plain answers

(a) Not established as worded. What the paired records establish for Qwen3-4B
on this task: (i) an instruction placed before two contrary own answers loses
whether it is in the system or the user role and at equal age (2/32, 1/32);
(ii) the same instruction as a separate user turn immediately before the
request recovers only 11/32 (paired +10/0 over T1); (iii) the same instruction
inside the request turn recovers 27/32 (check35 TEXT, same lists, cue-free
demos; T4 subset of TEXT, 16/0). But "own prior answers dominate" over-
attributes: with NO prior answers the system instruction followed by one
neutral turn already falls 31/32 -> 12/32. Defensible sentence: "a standing
sort instruction is weakly bound as soon as one turn intervenes (31 -> 12/32
with no answers at all); contrary own answers finish it off (12 -> 2/32)
regardless of the instruction's role or age; only an instruction inside the
request turn restores it (27/32); a separate immediately-preceding user turn
does not (11/32)". "Reliably" means 27/32 (84%), not the 60/64 of a fresh cue.

(b) Confounded: same-turn vs previous-turn is a cross-check comparison (T4 vs
check35 TEXT), unpaired within one run, with slightly different demo answers
and a cache-built history on the TEXT side; the previous-turn form is an
unanswered user turn, so turn structure and "separate turn" are entangled;
age after the demonstrations is untested (2.4). "Pattern" is not the ascending
default (the cue-free, demo-free default is copy, 64/64), but the demo effect
is bounded to ~10/32 of a ~29/32 deficit, the rest being pre-demo decay
measured across checks (2.1); and nothing separates "imitate own answers" from
"infer the old A rule from the answers". T2's whole-turn deletion is not the
FOCUS-2 repair policy (body replacement with closure), so T2 does not certify
that primitive.

(c) Yes, three design consequences for the FOCUS-2 draft (LEDGER-PLAN.md 1835ff):
1. Define placement-only as the live rule INSIDE the current request user
   message (cue + request, one turn), never as an adjacent user turn; check38 T4
   vs check35 TEXT is the evidence (11/32 vs 27/32, 16/0 paired). The draft's
   "current user turn" wording should say this explicitly; the text-restate arm
   already does it by construction.
2. Pre-register the expected size of eviction's added value: with a current-
   turn instruction alone at 27/32, and the demonstration effect bounded at
   ~10/32 in the old-slot configuration, both-minus-placement-only cannot
   exceed ~5/32 on this task and is likely smaller; the >=13/256 net bar vs
   text-restate is a 5-point bar. Eviction remains a plausible release
   primitive for the demo-attributable third, not for the pre-demo decay, which
   only placement addresses. Keep the both-correct stratum as the mechanism
   estimate; add "pre-demo decay" (a no-answer, one-neutral-pair control) as a
   descriptive readout if cheap, since FOCUS-2's neither arm with 512-delay and
   no prior answers is the paired version of 2.1.
3. The draft's "no unanswered user turns" rule is now evidence-backed (2.4);
   keep complete neutral pairs and never render the moved rule as its own
   user turn. Also update the draft's prior-ordering paragraph: role is
   isolated (no effect), before-vs-after-demonstrations is isolated (+10/0),
   the ascending default prior with an explicit B cue and no demos is 12/32,
   and current-cue-vs-old-cue-alone is now T2 (12/32) vs check34 all_B (31/32).

## 4. Requested README edits (numbers stand)

1. Add the T2 vs check34 all_B SET line (12/32 vs 31/32; same slot, one
   intervening neutral turn, no answers) and the paired T2 vs R3 line (10/0).
2. Add the T4 vs check35 TEXT line (same lists; T4 subset of TEXT; 16/0) and
   state that the same-turn/previous-turn contrast is cross-check, unpaired.
3. State that T1's, T4's and the filler's user turns are unanswered
   (consecutive user turns) and that age after the demonstrations is untested.
4. Replace "cannot distinguish imitation from an ascending default" with the
   check34 off fact (cue-free, demo-free default is copy 64/64).
5. Note the reading was fixed by run-time copy + hash, not a prior commit.
6. Do not let "RECENCY threshold not met" be relayed as "no recency effect":
   paired 10/0 with a conservative interval excluding zero.

**Correction (astra full review, 2026-09-05)**: (F2) Check38’s T1/T4 cue events and inherited filler are unanswered consecutive user turns. Role, recency, turn structure and prior demonstrations were not isolated. The 19/32 “decay” plus 10/32 “answers” comparison is not an identified additive decomposition: it compares different lists/histories across checks. The paired T2/R3 contrast does not identify the cause of the whole deficit.
