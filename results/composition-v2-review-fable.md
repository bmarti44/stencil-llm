# Composition design v2 review (fable, one round, 2026-09-06)

Scope: `results/focus-mechanism-composition-v2-astra.md` including its orchestrator addendum
(check 40k), checked against my v1 review (`composition-design-review-fable.md`), my 40j review
(`check40j-review-fable.md`), both reuse memos (`reuse-research-{astra,fable}.md`), the 40g/40j/42
READMEs, the raw 40i/40j `records.jsonl` and `summary.json`, the 40k brief
(scratchpad `check40k-brief.md`, `chain40k.sh`), the 44c README and relations-v3 brief, and the
code the design says it reuses (`src/stencil/focus3.py`). CPU only; no model launched; nothing under
`data/bench` read; only this file written. Every number was recomputed from the raw records or by
exact enumeration.

## 1. Numbers, power, cost projections — all reproduce; labels are honest

| v2 claim | Recomputed from | Result |
|---|---|---|
| 40g: JS 3/8, 5 valid Python, 0 broken | 40g README | 3/8, 5/8, 0/8. Correct; "wording and operands changed together" matches the README's own caveat |
| 40j: text-only 16/16 both phases; bias-only 0/16 | 40j README/records | correct |
| 40j review: 4-space indent 16/16 vs 0/16; bare replies 10/16 | my review | correct |
| 42: frozen common sample 99/124 vs 88/124; 151/192 vs 131/192 descriptive; MASKING NOT CLOSED | 42 README lines 57-59, 182-183, 22 | correct, and this fixes my v1 LOW (ii) |
| 40i: 480 calls after de-aliasing, 14,152 tokens, 923.5505 s, 15.3235 tok/s, 29.48 tok / 1.9241 s, allocation 1,319.3006 s | records.jsonl: 672 rows, 192 with `shared_from_generation`, 480 unique generation ids; summary.json | 480 / 14,152 / 923.5505 / 15.3235 / 29.48 / 1.9241 / 1,319.3006. Exact. (Naive sum over all 672 rows would give 19,856 tokens / 1,294.3 s — v2 correctly de-aliases) |
| 40j: 224 calls, 6,439 tokens, 417.1094 s, 15.4372 tok/s, 28.75 / 1.8621, allocation 827.2215 s; P2 prefix 519 | records/summary | all exact; P2 prefix 519 on every record; largest context 584 tokens |
| 100-300-token body = 6.48-19.43 s | 100/15.4372, 300/15.4372 | 6.48 / 19.43 |
| 3,200 calls; 1,638,400 token cap; history 160,000-480,000 tokens = 2.88-8.64 h; four full arms 256,000 = 4.61 h; 90 s per arm-episode | arithmetic | all exact |
| Power (exact enumeration, n=64, one-sided .05): (.30,.05) 96.95/96.84; (.25,.05) 90.09/89.19; (.20,.05) 73.89/69.85; (.15,.05) 46.15/36.93; (.10,.10) 2.76/1.73; n=32 (.25,.05) 56.25 | independent enumeration | all five rows and the n=32 figure reproduce to two decimals |
| +/-23.96 pp conservative gain interval (40j) | 1-.0125^(1/16) | 23.96 |

Labels: "short-answer measured effective generation rates, not isolated decode benchmarks or
long-context forecasts" is the right label for the 15.3-15.4 tok/s figures (contexts <= 584
tokens). The power rows are correctly labeled as iid discordance assumptions, and the design says
outright that it "cannot truthfully certify six-hour feasibility". No number is mislabeled.

## 2. Were my three HIGH findings fixed? Yes, each by explicit text

- **C-vs-R isolation.** Fixed. v2 section 2: "R–N is the single primary contrast. R–T is
  descriptive. O–R measures perception/validation/state binding under the frozen input mode, not
  actuator benefit." The actuator contrast is now the oracle-held pair: "O_on receives the identical
  gold event schedule and renderer, differing only by the preregistered actuator flag", and section 3:
  "This optional comparison cleanly identifies the selected mask policy's total effect ... because
  perception/events are held to the same oracle." The C arm is gone. Correct.
- **Token caps.** Fixed. "Use 512 new tokens per generation ... There is no separate 512-token
  episode cap: 20 rounds permit up to 10,240 generated tokens per arm-episode", plus a pilot gate:
  "if ... the 512-token cap truncates more than 2% of scheduled calls, stop as cost/cap-ineligible;
  do not shrink caps to buy a misleading success." Correct; the cap is now measured, not assumed.
- **Absolute breakage bar.** Fixed. "The only breakage acceptance clause is paired: `B_R - B_N <= 1
  episode` ... No absolute `B_R<=2/64` bar." Correct. (But see finding M2: an absolute floor came
  back in another clause.)

The MEDIUM items also landed: the 40g branch is the actuator's "exploratory operating envelope, not a
general production certificate ... Store its exact template ID"; the dose rule is gone (frozen alpha-3
tensor, "No profile library"); the mask/tool-output contradiction is resolved ("Do not mask tool
observations or free prose"); the fact-preserving extension is cut; N is no longer a co-primary
(it is the comparator for the rendering-only question, which is the right use after 40j).

## 3. The larger test — fair and benchmark-free, but not runnable in 6 GPU-h as written

Fair: same authentic entries and workspaces in R and N; own histories retained; no shared prefix;
arm order randomized; greedy and seeds frozen; R's mode fixed by GO receipts before the bank
opens; oracle events scheduled at fixed boundaries independent of arm success; episode as the
statistical unit; one exact test; practical bar and readings prewritten. Benchmark-free: yes — the
lineage line is present and explicit (fit-on classifier sources; DEV-on separately authored specs;
evaluate-on a frozen fresh SLAB-1 bank), StaminaBench/ReBIND/Snowball/NLSI are design ideas only,
and v2 explicitly rejects my own memo's NLSI-fit suggestion, which is the correct reading of
Brian's rule. Powered: yes for a 20-25 pp effect on final success at n=64 (89-97%), honestly
labeled as unpowered below ~15 pp.

Concrete defects:

- **H1 (HIGH) — the cost gate fails by v2's own arithmetic; it should be resolved on CPU now, not
  discovered by a pilot that reads INELIGIBLE.** Per arm-episode: ten history bodies of 100-300
  tokens = 65-195 s at 15.4 tok/s, plus ten challenge rounds carrying tool JSON/edits/tests (say
  80-250 tokens each = 52-162 s), plus prefill of a context that grows to 5-10k tokens (unmeasured;
  MoE decode at that length on GB10 will be slower, not faster, than the 584-token measurements),
  plus tool execution while the GPU is held. That is 120-360 s per arm-episode before prefill. The
  budget after a one-hour pilot is 14,400/1.25 = 11,520 s over 160 arm-episodes = 72 s each, or
  90 s each with no reserve. The primary alone (128 arm-episodes) needs 4.3-12.8 h. So the 64-pair
  x 20-round x 100-300-token design is infeasible at every point of its own pressure envelope, and
  the design's stated "40%" preflight odds is generous — the honest number is near zero unless
  long-context throughput is materially better than short-context throughput, which is the wrong
  direction. Something must give and the choice belongs to Brian, in advance: (a) raise the budget
  to ~12-15 GPU-h for the primary; or (b) keep 6 h and cut pressure to 6-8 history rounds at the
  100-150-token floor with a stated (weaker) pressure claim; or (c) drop the nested O/T (saves 20%)
  and accept (b). Do not leave this to "the pilot is the only cost authority" — the pilot will
  simply confirm the arithmetic above at the cost of an hour.
- **M1 (MEDIUM) — the pilot itself does not fit its cap.** 4 episodes x 4 arms = 16 full
  arm-episodes in 3,600 s including load (~370 s) = ~200 s each, which is inside the estimate above
  only at the very floor. Restructure: 4 episodes x R/N (the primary's cost driver) + 1-2 episodes x
  O/T, or accept a 2-hour pilot charged outside the 6 h. Note the DEV contingent trigger needs "at
  least two different episodes" showing relapse and O relapse in two episodes, so cutting O to one
  episode makes the trigger unreachable — say which you prefer.
- **M2 (MEDIUM) — an absolute floor returned: PASS clause 4 requires R success >= 48/64 (75%).**
  This is not breakage but it has the same property: it is arm-invariant and untied to any
  measurement. A run with R 40/64, N 12/64, p < .001, no excess breakage, no relapse would FAIL on
  the register's behalf for a model-competence reason. Either label 48/64 a separate product gate
  ("ship-quality") that does not decide the scientific PASS, or derive the bar from the pilot's O/T
  competence (e.g., R >= O_pilot - 1 episode-equivalent). Clause 3 already handles the pure
  competence-ceiling case, so the extra floor only bites in the informative middle.
- **M3 (MEDIUM) — "own body" is undefined where it matters most.** SLAB-1's history bodies will be
  produced mostly through edit/write tool calls, i.e. tool-call JSON envelopes containing code. v2
  section 1 says "Do not split mixed tool-call JSON into supposedly fact-free subspans: unsupported
  body types remain visible", which means the 40i whole-body mask cannot touch them. Consequences:
  (i) the achieved-pressure count ("ten prior 100-300-token own bodies") must state whether tool-call
  envelopes count; (ii) the mask contingency is vacuous in the agentic test unless code answers are
  produced as assistant code blocks that the caller applies. Decide one of: history rounds elicit
  fenced code answers applied by the harness (maskable, matches 40i certificate), or tool-call edits
  (unmaskable, mask contingency cut). Not both silently.
- **M4 (MEDIUM) — the process rule "test-before-final receipt" needs a public test surface.**
  Hidden checkers "never enter tool feedback", so the model needs a visible, runnable test set to
  produce the receipt. v2 does not say there are public tests distinct from hidden ones, nor that
  the public set is frozen and lineage-separated from the hidden one. Specify it.
- **M5 (MEDIUM) — "R has no more relapse episodes than N" is confounded by completion.** N breaks
  earlier and reaches fewer post-retirement witnesses, so an episode-level relapse count favors N by
  construction. Compare relapse on applicable opportunities (which section 2 already records per
  kind), or on episodes where both arms reached the witness.
- **L1 (LOW) — the 20-minute mask screen cannot hold full-length episodes.** 1,200 s is one to four
  arm-episodes at the estimate above. Either cut it (my preference this week; 40j already says the
  mask is the useful half and 42 says it costs facts) or scope it to a single episode pair as a
  smoke, never a screen.
- **L2 (LOW) — T's text should be generated procedurally from the gold state** by an
  evaluator-authored template, not hand-written per request (16 x 20 = 320 requests). Say so.
- **L3 (LOW) — tool-execution wall time.** Node/Python execution of model-written code needs
  timeouts and a sandbox; a runaway test holds the GPU. Bound it and journal it separately from
  generation seconds (the journal already separates CPU/GPU-held time; add the timeout policy).

## 4. First-ship scope against Brian's requirements

- **No string matching in the register — NOT yet satisfied by "use the existing register
  machinery".** `src/stencil/focus3.py` binds scope, kind, request kind, task handle and the
  reinstatement veto with regexes/keyword lists: `scope_of` (lines 84-94, "this reply only",
  "conversation", `Task X`), `kind_of` (98, `sort|payload|tag|JSON`), `request_kind` (102),
  `selected_task`/`task_switch_only` (105-127, "Work on|Return to|Continue|Switch to task"),
  `relation_key` (60-66), and `cancellation_message` (152-160, `cancel|revok|rescind|withdraw`).
  v2's explicit `{action,key,scope,kind,value,target_version}` with caller-supplied handles makes all
  of these unnecessary — but v2 never says they are removed, and "Use the existing register
  machinery" plus "retain the small structured operation" for reinstatement will pull
  `cancellation_message` along by default. Also `Register.retire` mutates `status` in place (line
  201-202) with no immutable event log or version links, so v2's "immutable source events ... derive
  a live-view bit mask" is a rewrite of `Register`, not a reuse. **Required (HIGH for the build
  week):** strip or fence the regex binding layer out of the explicit path, add a test that the
  explicit transaction path never calls `re`, and budget Day 1 as a rewrite of `Register`/binding
  with `Runtime.update`'s classifier path kept only behind the post-GO flag.
- **Masking never deletion:** satisfied ("Retirement changes eligibility; it never deletes source
  text, transcript messages, historical records or workspace history"; register masks and attention
  masks explicitly distinguished).
- **One HF download:** satisfied in form (trunk shards + tokenizer + classifier + controller +
  tensor + manifests + `custom_generate/generate.py` in one repo). Note what it entails: re-hosting
  ~60 GB of Qwen3-30B-A3B shards in a new repo (Apache-2.0; `models/qwen3-30b-a3b-hf/LICENSE` is
  present), pinning the source revision hash in the manifest. Say it explicitly so nobody expects a
  pointer to the Qwen org repo.
- **Classifier-driven where learned judgments are used:** satisfied, and the abstention/pending
  semantics are right ("If semantic interpretation is needed and the classifier abstains, the
  transaction is left pending with no mutation"). One simplification: in explicit mode the
  classifier only journals ("A contrary classifier prediction is journaled"), so it should be an
  optional component of the load path, not a hard dependency (LOW).
- **Explicit entry until admission GO:** satisfied ("proposals do not enter the register without
  explicit adoption until the independent admission GO passes"). Consistent with the 44c README ("NO-GO;
  explicit entry remains first ship") and with relations-v3's GO bar (held-out-3 supersedes recall
  >= 90%, accuracy >= 94%).
- **Minimal:** the cut list is applied (task-type head, discovery, library, prefix sharing,
  fact-preserving mask, serving backend, extra judges all gone). Two items are still not first-ship
  work: the `create_masks_for_generate` adapter (Day 4) for a mask that is OFF by default, and the
  mask screen. Defer both; keep the verified 40i 2D path behind the flag (LOW).
- **Complete:** missing for a usable ship: the session-state contract is only "document session
  arguments/returns" — name the fields (KV handle, register event log, live mask, journal path,
  request-kind table); and a CPU stub-model dry run of a full 20-round episode (fixed scripted
  replies) through the real loop, executor, checkers, caps and writer before any GPU minute (Day 4
  lists an executor smoke and writer dry-assert, not a whole-episode replay) (MEDIUM, build-week).

## 5. The 40k contingency

Fit: the addendum is clean in principle — v2 already indexes the actuator certificate by request
template and gates eligibility "from declared template metadata, never inferred by a string
matcher", so a 40k R1 would add a second certified template (the 40e-like "Write a function named
X that ..." with hidden node tests and ~512-token bodies) beside the 40c one. But v2's manifest text
must be amended to hold both templates, and section 1's "40c open-form arithmetic request, short
bodies" envelope sentence is stale on an R1.

Defects in the contingency as written:

- **M6 (MEDIUM) — 40k's R1 is not a significance bar.** "wins - losses >= 5 of 32 AND losses <= 2"
  admits (w,l) = (7,2) with exact one-sided p = 46/512 = .090 and (6,1) with p = 8/128 = .0625; only
  (5,0) p=.031, (6,0) .016, (7,1) .035 are at .05. A default-on shipping decision should require the
  exact p <= .05 in addition to the margin, and the shuffled control's own exact p reported. Fix
  the 40k README before it runs (it is queued behind relations v3 in `chain40k.sh`; nothing has
  launched).
- **What the larger test must include if 40k reads R1:** (i) the shipped default becomes
  R+bias, so the primary must be the shipped package vs N — keep R (bias off) as the full-64
  paired diagnostic against R+bias for breakage/format (`B_{R+bias} - B_R <= 1`, plus the
  code-block-default/fence checker from the 40j review, since bias produced 10/16 bare replies);
  v2's "no co-primary, no split alpha" rule then applies to R+bias vs N only; (ii) per-round bias
  eligibility from the request-kind table: bias ON only for code-answer requests matching a
  certified template, OFF on tool-call envelopes and edit continuations (uncertified; 40j showed
  the bias moves presentation), and journal the flag per call; (iii) bias without mask (R1 certifies
  the bias alone; the mask stays OFF); (iv) the bias hash and dose in every record as in 40j;
  (v) cost: +64 arm-episodes (+50% on the primary), which makes H1 worse — an R1 branch cannot fit
  6 GPU-h on the v2 design under any pressure setting, so the budget ruling in H1 must cover this
  branch too.

## 6. Still over-engineered / still missing (build-week bites)

Over-engineered: the `create_masks_for_generate` adapter and mask-consumer fixtures (Day 4) for an
OFF-by-default mask; the 20-minute mask screen; the 4-arm x 4-episode pilot (M1). Cut or shrink.

Missing: the regex removal and `Register` rewrite (section 4, HIGH); the own-body definition (M3);
public vs hidden tests (M4); tool sandbox/timeouts (L3); stub-model whole-episode CPU dry run;
deterministic style checkers (indent/semicolon/naming via a formatter or tokenizer-level check, not
regex on prose — the oracle side may use string ops, the register side may not; state the boundary);
the two-template actuator manifest if 40k reads R1; and the budget ruling itself (H1).

## Findings (graded)

- HIGH — H1: the 64-pair x 20-round x 100-300-token design needs ~4-13 GPU-h for the primary alone
  at the measured 15.4 tok/s; the 6 h gate fails at every point of its own pressure envelope. Get
  Brian's ruling now (budget up, or pressure/rounds down, or O/T cut) rather than a pilot verdict.
- HIGH — the "existing register machinery" (`focus3.py`) binds scope/kind/task/request-kind and the
  reinstatement veto by regex; v2 never says these are removed. Brian's no-string-matching rule is
  violated unless Day 1 strips them and a test enforces it; `Register` needs the immutable
  event-log rewrite v2 describes.
- MEDIUM — M1 pilot cap unrealistic for 16 full arm-episodes; M2 R >= 48/64 absolute floor inside
  PASS; M3 own-body/tool-call definition (mask contingency may be vacuous); M4 public test surface
  for the process rule; M5 relapse episode-count confounded by completion; M6 40k R1 admits p = .09.
- LOW — L1 mask screen cannot hold full episodes; L2 T text procedural; L3 tool timeouts; classifier
  optional in explicit mode; defer mask adapter; state the 60 GB re-host; stub-model dry run.

Verdict: every number reproduces and every one of my v1 HIGH findings is fixed by explicit text;
the arm structure, caps, breakage clause, lineage and prewritten readings are now correct. Two
things block launch as written: the design is not runnable inside 6 GPU-h by its own arithmetic, and
the first-ship "reuse" of `focus3.py` would ship regex binding unless the build explicitly removes
it. Fix H1 by ruling, fix the regex layer on Day 1, tighten 40k's R1 to an exact p, and the rest is
medium/low polish.
