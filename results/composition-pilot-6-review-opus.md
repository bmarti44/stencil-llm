# Composition pilot 6 — independent accuracy review (Opus, max effort)

Reviewer: independent accuracy reviewer under Brian's 2026-09-06 ruling. One round, no code
edits, CPU only. No GPU, container, flag or process was touched; nothing under `data/bench`
or any evaluation-bank episode content was read. Every count below was **re-derived from the
records**, not copied from the report.

Artifacts reviewed: `results/quick-checks/composition-pilot-6/{README.md, registration.md,
main-records.jsonl, main-summary.json, scored-outcomes.jsonl, summary.json, determinism.json,
audit.json, report-audit.json, lifecycle.json, launch.json, server.log, run.py, report.py,
audit.py}`, the local loop journals under `local/main/*/*/loop.jsonl` (literal rendered
prompts), the pinned tree `/tmp/stencil-pilot6-pinned` at
`4ab3e21884e0e5decd6d4fd78607abd6a69cf95d`, `src/stencil/focus/renderer.py`,
`src/stencil/focus/slab2.py`, `src/stencil/focus/register.py`, `src/stencil/focus/loop.py`,
`scripts/composition_pilot5.py`, `tests/fixtures/slab2_cpu_report.md`.

## 0. Verification receipts (what I reproduced independently)

Pinned tree `git rev-parse HEAD` = `4ab3e21884e0e5decd6d4fd78607abd6a69cf95d`, `git diff HEAD`
clean; `renderer.py` and `slab2.py` in the pinned tree are byte-identical to the live tree.

I re-ran the saved outputs through the pinned `run_lane`/`run_q` with an injected decoder
(no HTTP, no GPU) and recomputed every reported figure:

| Claim in README | Re-derived | Verdict |
|---|---|---|
| 640 records, 128/arm, 5 arms | 640, 128 each | confirmed |
| Round-0 not written 0/8 all arms | 0 | confirmed |
| Lanes executing 8/8 all arms | 8/8 | confirmed |
| Written rounds 128/128 (T 127) | only non-write = `T slab2-dev-04 turn 12`, `syntax_error` | confirmed |
| Caps 0/640 | 0 | confirmed |
| Determinism D=0/8 | forward-i == reverse-i for all 8; `mismatches: []` | confirmed |
| Corrected indent floor 23/39 | post-supersede applicable rounds = 5+5+6+4+4+4+6+5 = **39**; T satisfied 23 | confirmed |
| delivery floor 48/49 | 48/49 | confirmed |
| Matched cells 127 | 127 for RNTQ **and** RNTQO | confirmed |
| Matched per-trait R/N/T (all 20 rows) | every row reproduced exactly | confirmed |
| R final 0/8, N 4/8, T 3/8, Q 2/8, O 0/8 | identical | confirmed |
| "all 8 R final failures fail indent, 6 fail format, 3 breakage/integration" | indent 8/8; format dev-00,01,02,03,06,07 = 6; breakage+integration dev-02,04,06 = 3 | confirmed |
| Projection 7.652 GPU-h | 7.651750699083010 | confirmed |
| GPU held 4414.921/9000 s | 73.582 min = 1.2264 GPU-h | confirmed |
| Max prompt 13,916 (+2,048 < 32,768) | 13,916 | confirmed |
| 656 HTTP requests vs 640 records | difference = the 16 determinism-gate calls | confirmed |

**The report is numerically honest.** I found no arithmetic error, no mis-stated count and no
overclaim in the README. Everything below is about what the numbers *mean*.

---

## 1. THE RENDERING QUESTION

**Verdict: split, and the split is decisive.**
The **format** deficit *is* a renderer defect, and I can prove it with a control that is
already in the run. The **indent** deficit is *not* a defect of the block's content — the same
block, rendered without history, is the **best** arm on indent — it is context accumulation
plus genuine model behaviour, and the headline `0/8` overstates it.

The two rule-out checks you asked for first:

* **Is R's block rendered on tool continuations?** Yes, on every single request. There is no
  separate tool turn: `composition_pilot5.py:130` bundles the feedback as a `tool` message
  inside the *same* user envelope, and `loop.py:244-268` renders it as `compact([tool, user])`
  *after* the rules block. Confirmed in the literal bytes of all 128 R renders. **Not a defect.**
* **Does the indent obligation appear after a competing format instruction?** Yes, twice.
  `register.live()` sorts `(scope-specificity, key, version)` (`register.py:437-449`), so the
  global rows render alphabetically — `format`, then `indent` — and the **task-scoped `delivery`
  row always renders LAST**, immediately before `Apply the active rules while answering the
  request below.` And the whole block sits *after* `SYSTEM_PROMPT`, whose worked example is a
  literal **2-space body** (`slab2.py:69`) followed by a **delivery-bearing trailer**
  (`slab2.py:70`). Those are the exact two behaviours R defaults to.

### Paired example 1 — dev-00 round 13 (cancel + reinstate). Both clauses flip at once.

R's rendered live row (literal bytes, `local/main/slab2-dev-00/R/loop.jsonl` record 13):

```
{"default":false,"key":"indent","kind":"style","provenance":{"message_id":"m13","role":"user",
"span":null},"scope":{"request_kinds":[],"task_handle":null},"text":"Workshop obligation: indent
must be 3. indent 3 = block bodies indented by exactly 3 spaces per level indent 3 = block
bodies indented by exactly 3 spaces.","value":"3","version":3}
```

R's tombstone block, same request:

```
Retired rules (not binding):
Retired: indent v1; no longer binding in {"request_kinds":[],"task_handle":null}; replaced by indent v3; reason supersedes; reinstated as a new version.
Retired: format v1; no longer binding in {"request_kinds":[],"task_handle":null}; replaced by default "compact"; reason completes.
Retired: indent v2; no longer binding in {"request_kinds":[],"task_handle":null}; replaced by indent v3; reason cancels.
```

T's whole rule text for the same round:

```
Effective obligations: delivery ready = trailer delivery=ready when verbose and scoped; format compact = trailer omits delivery; indent 3 = block bodies indented by exactly 3 spaces per level; language Python = executable Python file; test_record test-after-edit = harness runs public tests after file write. Not binding: format=verbose; indent=2
```

The user message is **byte-identical in R, N and T** (`cancels indent: … indent must be 2 …
reinstates indent: … indent must be 3 …`). Replies:

| arm | body indent | trailer |
|---|---|---|
| R | `def step_13(x):` + **2 spaces** | `report: task=A status=ok delivery=ready` |
| N | `def step_13(x):` + **3 spaces** | `report: task=A status=ok` |
| T | `def step_13(x):` + **3 spaces** | `report: task=A status=ok` |

Live rules: indent 3, format compact. R fails both; N and T pass both. N sees **no rule block
at all**.

### Paired example 2 — dev-03 round 11 (compact round). The Q control.

R's block ends with these two rows, in this order, and nothing else between the last row and
the request:

```
… {"default":true,"key":"format",…,"text":"Workshop obligation: format must be compact. format compact = trailer omits delivery","value":"compact","version":0},
   {"default":false,"key":"indent",…},{"default":false,"key":"language",…},{"default":false,"key":"validation",…},
   {"default":true,"key":"delivery","kind":"process",…,"task_handle":"B"},"text":"Workshop obligation: delivery must be ready. delivery ready = trailer delivery=ready when verbose and scoped","value":"ready","version":0}]
Retired rules (not binding):
Retired: delivery v1; … replaced by default "ready"; reason completes.
Retired: format v1; … replaced by default "compact"; reason completes.
Apply the active rules while answering the request below.
```

T's line for the same round puts `delivery` first and `format compact = trailer omits delivery`
**second**. Q renders the **identical row order to R** (`format, indent, language, validation,
delivery`) with **no history, no tombstones, and a 1,431-token prompt**. Replies:

| arm | trailer | context |
|---|---|---|
| R | `report: task=B status=ok delivery=ready` | block + 8,902-token prompt |
| **Q** | `report: task=B status=ok delivery=ready` | **same block, no history, 1,431-token prompt** |
| T | `report: task=B status=ok` | prose line, format after delivery |
| N | `report: task=B status=ok` | no block |

This repeats for **every** compact round of dev-03 (t11–t15): R `delivery=ready` ×5, Q
`delivery=ready` ×5, N clean ×5.

### Paired example 3 — dev-06 rounds 12–15 (compact). T is not immune.

R `report: task=B status=ok delivery=ready` ×4; **T `report: task=B status=ok delivery=ready`
×4**; N `report: task=B status=ok` ×4; Q `delivery=ready` ×4. Whenever the delivery obligation
is *rendered*, the model prints it; when it is not rendered (N), the model stops.

### What this proves

Aggregate, matched cells (127), format trait: **R 9/34, Q 11/34, T 22/34, N 34/34.**
Q has the same rendered block as R and **none** of R's history, tombstones, stale copies or
context length — and Q reproduces R's failure. N has no block and is perfect. **The format
deficit is caused by the rendered block itself, not by history, not by the tombstones, and not
by scoring.** That is a renderer defect, and these are the responsible bytes:

* `register.py:437-449` — `live()` sorts task-scoped rows into the **last** bucket, so the
  `delivery` obligation is always the final rule text the model reads before the request.
* `renderer.py:90-106` — rows are emitted in that order verbatim; **no composition step**
  removes or re-guards `delivery` when the live `format` is `compact`.
* `slab2.py:107` — `literal("delivery", v)` renders as `"delivery ready = trailer
  delivery=ready when verbose and scoped"`: a directly actionable imperative with its guard as a
  trailing subordinate clause. The suppressing rule (`format compact = trailer omits delivery`)
  is a *different row*, rendered first, and the interaction is never stated.

The fix is small and local: when `format == "compact"`, either omit the `delivery` row from the
live view or render it guard-first (`"delivery: not reported under the current compact format;
value ready applies only when format is verbose"`), and stop putting the most specific
obligation last.

### The indent clause is a different story

Matched cells, indent trait: **R 7/127, N 20/127, T 23/127, Q 59/127.** Q — *same block* —
is by far the best. So the block's *content* does not break indent. What does:

1. **Context accumulation.** `loop.py:363` appends `rendered.prefix_ids` — the *entire* rules
   block — into `history_ids` every turn. R's mean prompt reaches 13,186 tokens at round 15 vs N
   6,435, T 7,314, Q 1,706, and R's context carries 14 stale copies of a block headed
   `Active rules for this request`. Indent adherence tracks that: Q (1.7k) 59, T (7.3k) 23,
   N (6.4k) 20, R (13.2k) 7.
2. **Renderer dead weight inside that accumulation.** 23.1% of R's rule-block tokens are
   `"provenance":{…}` and `"scope":{…}` metadata that no obligation depends on
   (`renderer.py:101-102`): 2,295 of 9,944 accumulated envelope tokens in dev-00's R lane.
3. **Inertia, not repeated failure.** R's changed-code indent width at rounds 14 and 15 equals
   its round-13 width in **8/8** episodes. Each episode contains ~2 independent indent
   decisions, not 5–6 rounds (see §3).
4. **Genuine model behaviour, shared by all arms.** The model defaults to PEP-8 4 spaces at
   round 0 in every arm, and thereafter copies the style of the most recent function in the
   file it is editing — including Q, which copies the *gold* file's most recent 2-space
   functions at dev-00 t13 while the live rule says 3. T at dev-04 t12 tried to satisfy
   "indent 3" by indenting the top-level `def`s and produced
   `syntax error in core.py at line 6: unindent does not match any outer indentation level`.
   Even under perfect information Q is only 59/127 (46%).

Three real but **secondary** renderer defects sit on top of this, all with named bytes; none is
proven causal by the data, and each is cheap to fix:

* `renderer.py:19-23` + `renderer.py:96-100` — the style gloss is concatenated to a text that
  already ends in `literal()`, with **no separator**, producing the run-on
  `"…indented by exactly 3 spaces per level indent 3 = block bodies indented by exactly 3 spaces."`
  — two subtly different definitions of the same rule (`per level` vs not). It fires on
  `kind == "style"` **only**, i.e. only on the failing trait. 224 tokens per dev-00 R lane.
* `renderer.py:70-89` — tombstones carry **no value** and are retargeted to the *current* live
  version rather than the replacement at retirement time. At the reinstatement round this emits
  `Retired: indent v1; no longer binding …; replaced by indent v3; reason supersedes; reinstated
  as a new version.` while v1's value *is* the value now required. R fails the indent decision at
  the reinstatement round in 8/8 episodes. **Hypothesis, not proof:** the line drops out by round
  14 and R still fails, because R is inertial after the decision round.
* `renderer.py:108` — the header `Active rules for this request (subject to system/developer
  instructions)` explicitly subordinates the live rules to `SYSTEM_PROMPT`, whose worked example
  is a 2-space body (`slab2.py:69`) with a delivery trailer (`slab2.py:70`). Only R/O/Q carry this
  subordination clause; N and T do not.
* `renderer.py:110-111` — the `Retired rules (not binding):` header is emitted unconditionally,
  so every Q request and R rounds 0–9 contain a dangling header and a blank line. Cosmetic.

---

## 2. THE CAPABILITY QUESTION

**Q's construction is valid in the ways that matter, its 0/8 is real, and the premise you state
is correct: joint final success is not a measurable endpoint for any arm.** But the *reason* is
not the one in the brief, and one part of Q's rubric is defective. Both must be said.

**Q construction, verified** (`composition_pilot5.py:186-266`): fresh `Session` per round;
workspace re-materialised from `episode.initial` and overwritten with accumulated **gold**
reference files; `executor.last_parsable` set to those gold files; `Register` rebuilt from the
live versions as version-0 defaults (`replace(v.entry, action="add", target_version=None,
evidence=None)`), so no retirements and no tombstones; the lifecycle prose is stripped
(`composition_pilot5.py:227`, `turn.request.split("\n",1)[-1]`); no conversation history, no
tool feedback. Q runs before every trajectory arm. All 128 Q rounds written, 0 caps. **This is
a faithful "correct rules, fresh context, correct prerequisites" probe.**

**Q qualified 0/8 — confirmed, and it survives the rubric correction.** Under the as-run rubric
(all five traits, `composition_pilot5.py:253`) Q is 0/8. Under the R/N/T rubric (the four
floor-eligible traits) Q is **still 0/8**. Best episode: dev-04 with 13/16 rounds passing.

**But one trait in Q's rubric is unsatisfiable by construction.** `delivery_scope` is
**0/44 in all five arms** — R, N, T, Q **and** O. Zero variance, zero information. It is
correctly excluded from the frozen T floor (`eligible: false`), but `composition_pilot5.py:253`
scores Q against `tuple(s.TRAITS)`, i.e. **including** it, so Q alone is graded on a strictly
harder rubric than R/N/T. That is a real defect (finding H3) even though it is not what makes
Q 0/8.

**The endpoint is unreachable — here is the direct evidence.** Per-round joint pass of the four
floor-eligible traits, over 128 rounds:

| arm | joint pass |
|---|---|
| R | 4/128 |
| T | 16/128 |
| N | 18/128 |
| **Q (perfect information)** | **48/128** |
| any arm on the same cell | 63/128 |
| **all arms on the same cell** | **0/128** |

Sixteen-round conjunction: **0/8 in every arm**. Final-round conjunction: R 0/8, Q 2/8, T 3/8,
**N 4/8 — the maximum observed anywhere**. The registered gate is R ≥ 5/8. **No arm, including
the perfect-information probe, reaches it.** The registered full-bank PASS additionally demands
a positive R-minus-N gain of ≥ ceil(n/8) = 8 episodes at 64; DEV shows R behind N 4–0 in
discordant episodes. **The registered primary cannot succeed. Running it at 64 episodes buys a
foregone FAIL.**

**So yes — plainly: joint final success is not a measurable endpoint for any arm, and the larger
test as registered cannot succeed.**

### Recommended corrected primary endpoint

**Per-obligation adherence, scored at the obligation's change round, paired at the episode
level.** Not "per applicable round" — see §3: applicable rounds after a change are deterministic
repeats of the decision round (R's indent width at t14/t15 equals its t13 width in 8/8
episodes), so per-round pairing is pseudo-replication. Score the **first applicable round at or
after each supersede / complete / cancel / reinstate event**: one observation per obligation
change per episode.

Computed on this pilot (8 episodes; exact two-sided sign test on discordant episodes):

| obligation change | R | N | T | Q | R vs N |
|---|---|---|---|---|---|
| delivery completion (8 events) | **8/8** | 1/8 | 7/8 | 8/8 | R+7 N+0, **p = 0.0156** |
| format change (8 events) | 2/8 | **8/8** | 5/8 | 2/8 | R+0 N+6, **p = 0.0312** |
| indent supersede + reinstate (16 events) | 4/16 | 9/16 | 10/16 | 7/16 | R+0 N+4, p = 0.125 |

Two significant, opposite-signed effects at **n = 8**. The register arm updates the completed
delivery obligation in 8/8 episodes while plain history keeps emitting the retired value in 7/8
— that is the register's genuine, measurable win, and it is currently invisible because the
joint endpoint swallows it. At 64 episodes this design yields 64 paired observations per
obligation family; power is ample.

### Pre-registration changes required

1. **Replace the primary.** Primary = per-obligation change-round adherence, R vs N, paired at
   the episode level, exact one-sided sign test / McNemar, α = .05, one test per obligation
   family (style, format, process) with Holm across the three. Joint final success is retained
   **descriptively only**, explicitly not a PASS criterion.
2. **Declare the episode the unit of analysis.** Round-level matched-cell counts are reported as
   descriptive only.
3. **Drop `delivery_scope`** as an endpoint (0/44 in all five arms) or redesign it; it must not
   appear in Q's rubric. Score Q on the same trait set as R/N/T.
4. **De-conjoin style/language adherence from breakage** (`slab2.py:623-625`) — report adherence
   conditional on a parsable write, and breakage as a separate, pre-registered outcome.
5. **Re-label Q.** Q is a *fresh-context reference condition*, not a capability ceiling: it has
   no tool feedback and edits gold files it did not author. State this.
6. **Register the renderer fix and its ablation** (see §5) before, not after, the 64 run.
7. **Declare O.** O is byte-identical to R (see §4); either drop it or register it as a
   duplicate-cost probe.

---

## 3. IS `INELIGIBLE` CORRECT, AND IS THE R DEFICIT REAL?

**`INELIGIBLE` is correctly applied.** I re-ran `pilot5_reading` semantics against the records:
complete 8×16×4 ✓; executing lanes 8/8 in every arm ✓; caps 0/128 per arm ✓; two primary
substitution kinds (`style`, `process`) eligible with 8 opportunity episodes each ✓; cost
7.6518 ≤ 12 ✓; **R final = 0 < 5 ✗**. `failures: ["R final<5/8"]` is exact and complete. The
stricter user gates (round-0 fence failures 0/8 per arm, per-round execution ≥90%: R/N/Q
128/128 = 100%, T 127/128 = 99.2%) also pass. The reading is right.

### Matched-cell comparison — cells where all four arms wrote a file (127 of 128)

| trait | R | N | T | Q | R vs N, exact paired sign test on 8 episodes |
|---|---|---|---|---|---|
| language | 80/127 | 80/127 | 111/127 | 123/127 | R+0 N+0 — tie, p = 1.0 |
| indent | **7/127** | 20/127 | 23/127 | **59/127** | R+0 N+4, one-sided p = 0.0625, **two-sided p = 0.125** |
| format | **9/34** | **34/34** | 22/34 | 11/34 | R+0 N+6, one-sided p = 0.0156, **two-sided p = 0.0312** |
| delivery | **49/49** | 40/49 | 48/49 | 49/49 | **R+7 N+0**, one-sided p = 0.0078, **two-sided p = 0.0156** |
| delivery_scope | 0/44 | 0/44 | 0/44 | 0/44 | unmeasurable |

Per-episode vectors (the paired data):

```
indent    R [2/16 2/16 0/16 0/16 0/15 1/16 0/16 2/16]   N [5 5 0 4 0 4 0 2]   T [5 5 6 4 0 1 0 2]
format    R [0/4 0/4 0/4 0/5 4/4 5/5 0/4 0/4]           N [4 4 4 5 4 5 4 4]   T [4 4 0 5 4 5 0 0]
delivery  R [8/8 6/6 7/7 4/4 6/6 5/5 7/7 6/6]           N [6 4 6 3 5 4 6 6]   T [8 6 7 4 6 4 7 6]
```

### Real or instrument? Trait by trait.

**format — real behaviour, caused by a renderer defect.** Episode-paired p = 0.0312. Not a
scoring artifact: R literally prints `delivery=ready` in 25 of 34 compact rounds and N never
does. But the cause is inside the rendered block, proven by the Q control (§1): same block, no
history, 11/34. **This deficit is fixable in the renderer and must be fixed before it is
attributed to the register idea.**

**indent — real in direction, over-stated by two instrument effects, and not significant.**
- *Instrument effect 1 — breakage conjunction.* `slab2.py:624-625` makes `satisfied["indent"]`
  require `not breakage`, and `breakage` is set by a **semantic** failure anywhere in the
  workspace (`slab2.py:558-562`). Nine of R's 32 post-change indent failures had **correct
  widths** and were failed only because an unrelated wrong-answer poisoned the lane —
  the nine are dev-02 t10-12, dev-04 t13-15 and dev-06 t10-12, each at **exactly the required
  2 spaces**. dev-04 R answers round 0 with `return x * 6 + 6` where `x` is a list
  (`InvalidProgram`), and from that round on *every* round in the lane carries
  `breakage=True`, so indent is forced False for the whole lane regardless of indentation.
- *Instrument effect 2 — pseudo-replication.* Post-decision rounds are deterministic repeats.
  Collapsing to the 16 indent decision rounds gives R 4/16, N 9/16, T 10/16.
- *Test.* Episode-paired exact sign test: R vs N **two-sided p = 0.125** (one-sided 0.0625);
  R vs T identical. The round-level 7/127-vs-20/127 gap looks like p ≈ 10⁻⁴ only because 39
  correlated rounds are counted as 39 independent trials. **The honest reading is: suggestive,
  under-powered, not established at n = 8.**

**delivery — real, significant, and in R's favour.** R and Q are 49/49; N 40/49; episode-paired
two-sided p = 0.0156. At the delivery-completion round specifically, R 8/8 vs N 1/8. This is the
one place the pilot shows the register doing exactly what it is supposed to do, and it is not an
artifact: N is emitting the *retired* value (`delivery=staged`) after the completion event.

**language — identical (80/127) in R and N**, driven entirely by semantic breakage in dev-02,
dev-04, dev-06. Not a rendering effect.

---

## 4. TRUNK, BACKEND, COST, HARNESS

**Trunk: unchanged.** Nothing here touches trunk conclusions. The instrument under test is
`renderer.py` + `register.live()`, not the trunk.

**Backend: unchanged and clean.** Qualified batch-invariant bf16 vLLM image (digest pinned in
`launch.json`), `TRITON_ATTN`, `--max-num-seqs 4`, `--max-num-batched-tokens 2048`,
`--enable-prefix-caching`, cap 2048. Determinism D = 0/8 exact (body token IDs, EOS, cap) under
forward-C4 then reverse-C4. **A second, stronger receipt exists that the report does not claim:**
the O arm's 128 outputs are **byte-identical to R's** (`output_sha256` matches 128/128, prompt
token counts identical round by round), i.e. a full 128-round exact replication across different
scheduling positions in the same container. `server.log` contains no error, no preemption, and
only benign startup warnings. Max prompt 13,916 + 2,048 = 15,964 < 32,768; no context-gate risk.
**Backend conclusions stand.**

**Cost: confirmed, including Q.** `measured_projection` (`slab2.py:895-916`) implements the
registered formula exactly. Recomputing from `main-summary.json` lane seconds
(Q 82.606, R 110.303, N 95.720, T 92.650, O 105.729; load 488.424 s):

```
(488.42369842529297 + 1.25*(64*(110.30254362225533+95.71997491717339+82.60629294514656)
                          + 16*(105.7290561914444+92.64963878393174))) / 3600
= 7.651750699083010 GPU-h
```

**The stated 7.652 GPU-h already includes the Q arm at ×64.** Decomposition:

| variant | GPU-h |
|---|---|
| **registered, Q-inclusive (Q,R,N,T,O)** | **7.651751** |
| Q-exclusive (R,N,T,O) | 5.816055 — **Q adds 1.835695** |
| without O (Q,R,N,T) | 7.064367 — **O adds 0.587384** |
| without Q and O | 5.228672 |
| pilot actual GPU held | 1.226367 (73.582 min of a 9000 s budget) |

Two caveats on precision. (a) **The estimator's noise is ~4%.** R and O performed
byte-identical work and measured 110.303 vs 105.729 s/lane — a 4.15% spread. Read the
projection as 7.65 ± ~0.3 GPU-h, not to six decimals. (b) **0.587 GPU-h of it buys a
duplicate**: `renderer.py:136` treats `rule_mode == "O"` as `"R"`, so O renders exactly like R
and, being deterministic, produces the same tokens. Either drop O (7.064 GPU-h) or register it
as the replication probe it actually is.

Either way the ≤12 GPU-h cost gate passes with wide margin, and the (12,15] 12-round fallback
correctly did not trigger.

**Harness: sound execution, four scoring defects.** The harness ran cleanly (640/640 replayed,
0 payload mismatches, 0 record-field mismatches, 1,200 local files hash-verified, container
stopped and removed, no flag left). The defects are in the *checker*, listed in §5.

---

## 5. BOTTOM LINE FOR BRIAN — five lines

1. **The pilot is honest and the `INELIGIBLE` reading is right, but the registered endpoint is
   dead: R 0/8, N 4/8, T 3/8, and the perfect-information probe Q 2/8 — no arm reaches 5/8, and
   16-round conjunction is 0/8 in every arm, so the 64-episode test as registered cannot pass.**
2. **There is one proven renderer defect and it must be fixed before any 64 run:** the
   task-scoped `delivery` obligation renders last, unguarded, and is never composed with
   `format = compact` (`register.py:437-449`, `renderer.py:90-106`, `slab2.py:107`) — proven by
   the Q control, which has the same block and no history and reproduces R's failure 11/34 while
   the no-block arm N is 34/34.
3. **The indent story is not a block defect** — Q with the same block is the best arm (59/127) —
   it is context accumulation (R 13.2k tokens vs N 6.4k, of which 23% of the block is dead
   `provenance`/`scope` metadata at `renderer.py:101-102`) plus genuine model behaviour; and the
   0/8-vs-23/39 headline over-states it, because `slab2.py:624-625` fails 9 correct-width rounds
   on unrelated breakage and 39 "rounds" contain only 16 independent decisions (episode-paired
   p = 0.125, not significant).
4. **The larger test CAN run and CAN succeed on a corrected endpoint:** per-obligation adherence
   at the obligation's change round, paired at the episode level, already gives two significant
   effects at n = 8 — R beats N on delivery 8/8 vs 1/8 (p = 0.0156) and loses on format 2/8 vs
   8/8 (p = 0.0312) — at 7.652 GPU-h Q-inclusive (7.064 without the duplicate O arm), well
   inside the 12 h gate.
5. **My recommendation: fix the delivery×format composition and strip the provenance/scope dead
   weight, re-pilot the 8 DEV episodes at ~1.2 GPU-h to confirm the fix moved R's format from
   9/34, then authorize the 64-episode run on the per-obligation change-round endpoint — do not
   spend 7.65 GPU-h on the joint final-success endpoint, which is a foregone FAIL.**

---

## Findings

| # | Sev | Finding | Location |
|---|---|---|---|
| C1 | **critical** | Registered primary endpoint is unattainable. Joint final success: R 0/8, N 4/8, T 3/8, Q 2/8; 16-round conjunction 0/8 in every arm; per-round 4-trait conjunction 48/128 even for Q and 0/128 for all arms simultaneously. The registered full-bank PASS additionally requires R to gain ≥8 episodes over N; DEV shows R behind 4–0. A 64-episode run on this endpoint is a foregone FAIL. | `registration.md` PRE-WRITTEN READINGS; `slab2.py:835-893`; re-derived from `main-records.jsonl` |
| H1 | **high** | Renderer never composes `format=compact` with the `delivery` obligation, and `live()` renders the task-scoped `delivery` row **last**, immediately before "Apply the active rules…". R 9/34; the Q control (same block, zero history, 1,431-token prompt) reproduces it at 11/34 while block-free N is 34/34. Episode-paired p = 0.0312. This, not the register idea, is what the format clause currently measures. | `register.py:437-449`; `renderer.py:90-106`; `slab2.py:107` |
| H2 | **high** | `satisfied["indent"]` and `satisfied["language"]` are conjoined with `breakage`, and `breakage` is set by a semantic error anywhere in the workspace. 9 of R's 32 post-change indent failures had **correct** widths — dev-02 t10-12, dev-04 t13-15, dev-06 t10-12, all at exactly the required 2 spaces, all failed only because the lane was poisoned by a semantic error (dev-04 R from round 0: `return x * 6 + 6` on a list). Style adherence is not separable from program correctness. Width-only post-change: R 16/39, N 30/39, T 26/39, Q 19/39. | `slab2.py:623-625`, `slab2.py:552-562` |
| H3 | **high** | `delivery_scope` is 0/44 in **all five arms** — zero variance, no information — yet it is included in Q's rubric only (`eligible_traits=tuple(s.TRAITS)`), grading Q on a strictly harder rubric than R/N/T. It is correctly excluded from the frozen T floor. Q is still 0/8 under the corrected rubric, so this is not the cause of Q's 0/8, but it invalidates any cross-arm reading of Q qualification. | `composition_pilot5.py:253`; `slab2.py:619-620`, `slab2.py:632`; `main-summary.json` floor |
| H4 | **high** | Pseudo-replication in the headline diagnostic. Post-decision rounds are deterministic repeats — R's indent width at t14/t15 equals its t13 width in 8/8 episodes — so the 127-cell matched table counts ~16 independent indent decisions as 39–127 trials. Episode-paired exact tests: indent p = 0.125 (n.s.), format p = 0.0312, delivery p = 0.0156. The README's matched table is labelled descriptive, which is correct, but the pilot has no registered inferential test at all. | `report.py:30-68`; `README.md` matched-cell table |
| M1 | medium | 23.1% of R's rule-block tokens are `provenance`/`scope` JSON that no obligation depends on (2,295 of 9,944 accumulated envelope tokens in dev-00 R). This is the renderer's direct contribution to the context inflation that tracks the indent deficit (R 13,186 tokens vs N 6,435, T 7,314, Q 1,706). | `renderer.py:101-102`; `loop.py:363` |
| M2 | medium | Duplicated, run-on style gloss: `value_gloss` is appended with **no separator** to a text already ending in `literal()`, giving `"…indented by exactly 3 spaces per level indent 3 = block bodies indented by exactly 3 spaces."` — two subtly different definitions of the same rule. Fires on `kind=="style"` **only**, i.e. only on the failing trait. | `renderer.py:19-23`, `renderer.py:96-100` |
| M3 | medium | Tombstones carry **no value** and are retargeted to the *current* live version rather than the replacement at retirement. At reinstatement this emits `Retired: indent v1; no longer binding …; replaced by indent v3; reason supersedes; reinstated as a new version.` while v1's value is the value now required. R fails the indent decision at the reinstatement round in 8/8 episodes. Hypothesis, not proven — the line is gone by t14 and R still fails (inertia). | `renderer.py:60-89` |
| M4 | medium | `rule_mode == "O"` falls through to the `"R"` branch, so O is byte-identical to R: 128/128 identical `output_sha256`, identical prompt-token series. It consumes 0.587384 GPU-h of the 7.651751 projection for zero additional science. (Its silver lining: a free 128-round exact-determinism replication the report does not claim.) | `renderer.py:136`; `main-records.jsonl` |
| M5 | medium (latent) | `all(w == int(rules["indent"]) for w in widths)` is vacuously **True** when `widths == []`, i.e. when a reply's changed-code diff is empty. It did not fire in this pilot (the one empty case, `T dev-04 t12`, failed on `syntax_error` anyway) but at 64 episodes a model that re-emits a file unchanged scores a free indent pass. | `slab2.py:625`, `slab.py:889-919` |
| M6 | medium | The lane-second cost estimator has ~4% noise: R and O did byte-identical work and measured 110.303 vs 105.729 s/lane. The projection should be quoted as 7.65 ± ~0.3 GPU-h, not to six decimals. Does not affect the ≤12 h gate. | `main-summary.json` `lane_seconds`; `slab2.py:895-916` |
| L1 | low | `Active rules for this request (subject to system/developer instructions)` explicitly subordinates the live rules to a system prompt whose worked example is a 2-space body with a delivery-bearing trailer — the exact two behaviours R defaults to. Only R/O/Q carry the subordination clause. | `renderer.py:108`; `slab2.py:69-70` |
| L2 | low | `Retired rules (not binding):` is emitted unconditionally, so every Q request and R rounds 0–9 contain a dangling header followed by a blank line. | `renderer.py:110-111` |
| L3 | low | The pilot-5 prior comparison row (R 0/9, N 8/9, T 8/9) is a hard-coded literal in the reporter, not recomputed from pilot-5 records. It is labelled as a prior, so this is presentational only. | `report.py:69-75` |

## Not findings — checked and cleared

* Every number in `README.md` reproduces exactly from the records. No arithmetic error found.
* R's rules block **is** rendered on every request including tool continuations; the tool result
  is inside the same envelope, after the block (`composition_pilot5.py:130`, `loop.py:244-268`).
* Determinism, caps, round-0 execution, lane execution, context gate, container lifecycle,
  local-hash integrity and the saved-response replay audit all verify.
* The cost formula matches the registration byte for byte and the Q arm is charged at ×64.
* No fitting, selection or tuning on evaluation content is visible anywhere in this pilot; the
  data-lineage line (`fit-on: none; evaluated-on: eight authored DEV episodes`) is accurate.
