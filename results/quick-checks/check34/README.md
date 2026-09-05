# Quick check 34 — cue-column positive control and stickiness isolation

UNREGISTERED, disclosed exploratory check, authorized 2026-09-05; seed 34034; Qwen3-4B only.
Lineage: fit-on=none; donor extraction=operand/answer-free text; evaluated-on=fresh synthetic
lists from this seed, unique by unordered set across the single-shot, retained, and stickiness
banks. No fitting, training, benchmark inputs, or benchmark responses. Earlier checks motivate
the design; these outcomes are not registered FOCUS-1 evidence.

## Fixed design and readings (written before GPU execution)

A = ascending sort; B = DESCENDING sort. Lists contain 5–8 distinct integers in -20..20,
excluding inputs already sorted either way. Reuse check-32 cache plumbing and format-lenient
value parser, changing B's expected values from reversal to descending; also record strict JSON
exactness, A/B/copy/other labels, and breakage (cap, repetition, or unparseable answer).
Greedy bf16/hf_compatible inference, at most 64 generated tokens, frozen weights.

Part 1: 64 paired fresh lists. Each episode has an operand-free neutral context, padded to
64 tokens before the cue. Cue A and cue B each occupy eight columns, as does the neutral
filler sentence; all have the same four-token suffix. Capture the actual donor K/V at columns
64–75, all layers, without averaging. Recipient prefill ends at the suffix; edit before the
system closing token and user list/request are processed. Thus no recipient operand is in a
donor and all donor and recipient positions match. Different episodes have different neutral
prefix text, with no task or numeric content. Shuffled donor is episode (e+1) mod 64, same task.
Arms: all-layer A and B; shuffled A and B; filler-only OFF; real-text A and B bars; layers >=12
A and B; K-only A/B and V-only A/B. Diagnostics get both targets to expose asymmetry.
Every edit asserts exact copied columns; record donor/prefix IDs and changes against filler.

**POSITIVE** if all-layer A and B each induce their task >=40/64, each has breakage <=2/64,
and OFF induces either task <=4/64. **NEGATIVE** if both all-layer arms induce their own task
<=8/64: the task decision is not carried by cue-column K/V alone at these positions; close
this transplant family as tested (attention-side, not evidence for transferable state-side
control). Anything else is **PARTIAL**, including asymmetric effects or incomplete runs.
A negative result cannot exclude every possible cache position/layout. Text bars are reported.

For each all-layer direction independently, if single-shot induction >=24/64, run 32 fresh
retained episodes: SET -> HOLD (no reapply, 128 neutral filler-body tokens) -> SWITCH (other
donor) -> BACK -> CLEAR (restore that recipient's original filler columns). Same initial
context and positions throughout; retain generated answers and EOS. CLEAR uses the same
cue-absent "Process" request, with copy as OFF target; no explicit copy instruction masks
residual task effects. Record bitwise HOLD retention and CLEAR column restoration; restoring
columns is not erasing downstream history. Report all five steps and joint first-four success.

Part 2: 64 paired final lists: (i) fresh B; (ii) B after three actual completed A user turns;
(iii) A after three actual completed B user turns. System text specifies JSON format only;
all task cues occur in USER turns. Prior answers are the model's own outputs, including
failures, and prior success is recorded. No screening or answer substitution. Each episode
has three additional fresh prior lists shared between (ii)/(iii).
Stickiness = exact-follow rate (i) minus (ii). **REAL** iff >=15 percentage points and
(i)>=48/64; otherwise **NOT SUPPORTED** (incomplete data = PARTIAL). Report 95% Wilson
intervals for each rate. The difference gets a conservative nominal 95% Wilson-based interval:
subtract endpoints of two 97.5% Wilson intervals (Bonferroni; no independence assumption for
paired observations); also report paired discordances. This interval is not a single-binomial
Wilson interval, since a difference of rates is not binomial.

Foreground only; no process signals or background launches. Abort if initial GPU compute
query is nonempty, cooperatively stop if foreign compute appears or at 45 cumulative minutes.
Run single-shot, then stickiness, then conditional retained work so the small second part
cannot be crowded out. Preserve every completed record immediately; no outcome-driven tuning.
## Results

Completed on Qwen3-4B in **21.44 GPU-minutes** (45-minute cap); 1,728 scored records. No fitting or training.

### Part 1 — **POSITIVE**

| Arm | n | Target exact | Strict exact | A | B | Copy | Other | Breakage |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| off | 64 | 64 | 64 | 0 | 0 | 64 | 0 | 0 |
| all_A | 64 | 59 | 59 | 59 | 0 | 0 | 5 | 1 |
| all_B | 64 | 60 | 60 | 0 | 60 | 0 | 4 | 0 |
| shuffled_A | 64 | 60 | 60 | 60 | 0 | 0 | 4 | 1 |
| shuffled_B | 64 | 60 | 60 | 0 | 60 | 0 | 4 | 0 |
| text_A | 64 | 59 | 59 | 59 | 0 | 0 | 5 | 1 |
| text_B | 64 | 60 | 60 | 0 | 60 | 0 | 4 | 0 |
| layers_ge12_A | 64 | 58 | 58 | 58 | 0 | 0 | 6 | 1 |
| layers_ge12_B | 64 | 57 | 57 | 1 | 57 | 0 | 6 | 1 |
| k_only_A | 64 | 0 | 0 | 0 | 0 | 64 | 0 | 0 |
| k_only_B | 64 | 0 | 0 | 0 | 0 | 64 | 0 | 0 |
| v_only_A | 64 | 0 | 0 | 0 | 0 | 64 | 0 | 0 |
| v_only_B | 64 | 0 | 0 | 0 | 0 | 64 | 0 | 0 |

A/B/copy/other are mutually exclusive; breakage is an additional flag, so its count overlaps those categories.

The transplanted cue columns induced ascending in **59/64** and descending in **60/64**, with 1/0 broken outputs. Filler-only OFF induced either task in **0/64**.

The cache-transplant route is alive: the model can use its own operand-free cue representation when the actual cue and suffix columns are transplanted. The earlier final-token/four-column packets failed as representations; they did not establish that instruction transfer through the cache is impossible. This result uses cached representations of the actual instruction tokens; it does not establish a compact task-state representation or erase instruction history.

All-layer transplant and same-context real-text bar generated identical token sequences in 64/64 A and 64/64 B pairs. Shuffled donors contain the same cue at the same positions after another episode’s neutral context; they are a transfer diagnostic, not a task-free null.

Conditional retained histories:

| Initial direction | Step | n | Target exact | Strict exact | A | B | Copy | Other | Breakage |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| all_A | SET | 32 | 31 | 30 | 31 | 0 | 0 | 1 | 0 |
| all_A | HOLD | 32 | 32 | 31 | 32 | 0 | 0 | 0 | 0 |
| all_A | SWITCH | 32 | 3 | 3 | 28 | 3 | 0 | 1 | 0 |
| all_A | BACK | 32 | 32 | 31 | 32 | 0 | 0 | 0 | 0 |
| all_A | CLEAR | 32 | 0 | 0 | 30 | 0 | 0 | 2 | 0 |
| all_B | SET | 32 | 31 | 31 | 0 | 31 | 0 | 1 | 0 |
| all_B | HOLD | 32 | 23 | 23 | 1 | 23 | 2 | 6 | 0 |
| all_B | SWITCH | 32 | 17 | 17 | 17 | 1 | 2 | 12 | 0 |
| all_B | BACK | 32 | 19 | 19 | 8 | 19 | 1 | 4 | 0 |
| all_B | CLEAR | 32 | 0 | 0 | 8 | 19 | 0 | 5 | 1 |

all_A: joint SET/HOLD/SWITCH/BACK = **3/32**. HOLD without reapplication = 32/32; SWITCH = 3/32; CLEAR copied the input = 0/32, and still imposed a sort in 30/32.

all_B: joint SET/HOLD/SWITCH/BACK = **5/32**. HOLD without reapplication = 23/32; SWITCH = 17/32; CLEAR copied the input = 0/32, and still imposed a sort in 27/32.

The successful single-shot positive control does not establish reliable set/switch/clear control in retained history; the complete step counts above measure that limitation.

All 64 HOLD checks retained edited columns bitwise through the filler, and all 64 CLEAR checks restored the original filler columns bitwise. These checks measure those columns only. Previously generated answers and downstream K/V remain in history; continued sorting after CLEAR is behavioral persistence despite local restoration, not evidence that the restoration write failed.

### Part 2 — **NOT SUPPORTED**

| Final-turn arm | Exact / 64 | Strict / 64 | 95% Wilson interval | A | B | Copy | Other | Breakage |
|---|---:|---:|---|---:|---:|---:|---:|---:|
| B_fresh | 60 | 60 | 85.0%–97.5% | 0 | 60 | 0 | 4 | 0 |
| B_after_A | 60 | 57 | 85.0%–97.5% | 0 | 60 | 0 | 4 | 1 |
| A_after_B | 60 | 60 | 85.0%–97.5% | 60 | 0 | 0 | 4 | 1 |

Stickiness (fresh B minus B after three A turns) = **0.00 percentage points**; conservative nominal 95% Wilson-based difference interval **[-14.53, 14.53] points** (Bonferroni combination of 97.5% marginal Wilson intervals). Paired discordances: fresh-only success 3, history-only success 3.

The observed difference does not meet the fixed rule for a meaningful stickiness effect. This check does not support a follow-up on that basis; it does not prove that all history effects are absent.

Actual preceding turns in B_after_A: 184/192 followed their cue; 0 broken outputs. These answers were retained as generated; none were replaced or screened.

Actual preceding turns in A_after_B: 178/192 followed their cue; 1 broken outputs. These answers were retained as generated; none were replaced or screened.

### Validation and provenance

CPU audit recomputed every score, summary, operand-bank assignment, generated-text decode, and all 1088 history token counts/hashes. CPU generation tests cover batched retained EOS handling, writes, HOLD/CLEAR, scorer and verdict boundaries; lint and import-side-effect checks passed. The fixed-reading hash and executed-script hash are verified. The prewritten section above is byte-preserved.

Single-shot evaluation: 4.43 min; stickiness evaluation including all 384 generated prior answers: 11.25 min. Remaining runtime covers loading, donor extraction and conditional retained episodes.

Artifacts: [summary](4b/summary.json), [records](4b/records.jsonl), [operand banks](4b/episodes.json), [layout](4b/layout.json), [donor token IDs and tensor hashes](4b/donors.jsonl), [validation](4b/validation.json), [CPU audit](audit.py), [foreground log](4b/run.log). Donor tensors were captured in memory; their raw bf16-byte SHA-256 hashes and exact input tokens are recorded, not a persisted tensor archive.
