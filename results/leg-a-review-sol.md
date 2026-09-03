# LEG A (BFCL V3 multi-turn) registration-draft review — sol, 2026-09-03

Scope: the last `WORKLOG.md` section, “LEG A (BFCL) registration DRAFT”, the companion coder brief
`tools/codex-agents/bfcl-evict-v2.md`, `LEDGER-PLAN.md` LEG B plus Amendments 1–2, the cited prior reviews and quick
checks 25–27, the pre-build BFCL harness, the BFCL metadata, and the vendored checker. I reviewed the registration,
not the concurrently built implementation committed as `c09549f`. All local checks were foreground CPU-only static
reads or arithmetic. I launched no model or GPU process, did not signal any process, did not read
`data/bench/ifeval_input_data.jsonl`, and did not open any sealed BFCL case content. I read only `cohorts.json`'s
top-level metadata/counts: seed 20260902, 32 dev IDs, 64 sealed IDs, 8/16 per category, file SHA-256
`22cf69afea1d7711a47af9e787dddeebb0a2485b3f32f4759236ba4d8ad919da`.

## Bottom line

Three high-level choices are right: protect the tool contract in every arm, evict before the semantic current turn
is prefilled, and concentrate inference on `long_context`. They are not yet an executable, uniquely interpretable
registration. The draft simultaneously promises end-to-end agent rollouts and identical per-turn contexts; compares
a pin-plus-echo treatment with controls lacking the echo channel; leaves the `K=8192` trigger/target and semantic
turn boundary unresolved; and gives a tool-specific interpretation to a contrast that changes selection, source
roles, and delivery mode together. A positive result could therefore mean targeted retention, generic re-injection,
or trajectory divergence. A negative result could mean no native pressure, no tool-span coverage, or inadequate
base competence. Those are different scientific outcomes.

## Independent numeric checks

1. The sealed primary stratum is only 16 `long_context` cases, not 64. The 32-case dev competence floor of 15%
   means at least 5/32 passes (15.625%) and permits 0/8 `long_context` passes. Applying 15% to the primary dev stratum
   itself would require 2/8 (25%).
2. The earlier non-cohort audit reports 97/176 `long_context` final prompts over 8192 tokens: 55.114%. I recomputed
   that arithmetic but did not replay any BFCL item. It is planning evidence that even the named primary category
   mixes pressure-exposed and no-eviction cases; it is not evidence about the sealed 16.
3. Under the repository's continuity-corrected clustered lower bound, at `n=16` the tightest Holm cutoff
   (`0.05/3 = 0.016667`) requires at least 6 favorable and 0 unfavorable binary case differences: mean +37.5 points,
   corrected lower bound +1.963 points. At alpha 0.025 it still requires 6/16 (LB +4.607); at alpha 0.05 it requires
   5/16 (LB +4.020). This is a high-effect screen. The draft supplies neither that interpretation nor a power/MDE
   calculation.
4. The cited literal-provenance table is arithmetically inconsistent as written. With denominator 4535, the counts
   are current user 1918 = 42.293%, earlier user 891 = 19.647%, earlier tool 752 = 16.582%, earlier assistant
   116 = 2.558%, and claimed “not found” 1673 = 36.891%. They sum to 5350 = 117.971%. If the first four are mutually
   exclusive under the stated precedence, their residual is 858 = 18.920%, not 1673. The 20% earlier-user and 17%
   earlier-tool facts remain individually useful, but the 37% “derived/not found” claim must not enter the
   registration or model card until its unit/overlap is audited.

## Findings

### LEG-A-1 — CRITICAL — the experimental trajectory and unit are contradictory

“Arms on identical context ids per turn” cannot hold for an end-to-end BFCL episode. Once two arms emit different
calls, their tool outputs, environment state, later messages, and token IDs legitimately diverge. Running every arm
from the same initial case is a paired end-to-end policy comparison; forcing a common history is instead a
teacher-forced or branch-at-one-decision retention assay. Either is defensible, but they answer different questions.

For an **agentic** test, register fresh arm-local rollouts from byte-identical initial case/environment state, pair
only by case, and delete the identical-context claim. Record the first divergence and per-arm pressure events. The
common-history alternative may be a secondary mechanism assay, not an interchangeable implementation choice.

### LEG-A-2 — CRITICAL — protected-prefix and pre-query intent is right, but the actual eviction intervention is not frozen

The draft does not define:

- whether `K` is tested on history already prefetched, the projected no-echo prompt, or each arm's echo-expanded
  prompt;
- whether eviction flushes the whole eligible range or removes only the oldest unpinned columns needed to return
  the physical cache to `K`;
- whether the four sink columns are a union with, or four additional columns after, the system/tool prefix;
- whether the protected prefix ends at `</tools>` or at the end of the complete system turn, including the required
  tool-call output-format contract;
- how much room is reserved for the current-turn suffix and echo, or what happens when protected + pinned + suffix
  alone exceeds `K`;
- what “current user turn” means after BFCL has rendered same-turn tool results inside user-role wrappers.

The last point is load-bearing. The split must be tracked from the semantic BFCL turn index; searching for the last
serialized user marker can put same-turn query/tool material on the evictable side. At every generation sub-step,
the entire current semantic turn (user request plus its assistant/tool sub-steps and the new assistant opener) must
be prefetched only after eviction. `full` must use the same two-stage schedule without deletion, as LEG B Amendment
2 established.

Protecting the complete system/tool turn in every arm is correct. The range should be the union
`[0, max(4, system_turn_end))`; schema additions in `missing_functions` must move `system_turn_end` on the next
serialization. The primary finite-cache rule should be deterministic LRU-like removal: reserve current-suffix
capacity, then remove the oldest eligible unpinned columns until physical cache columns after suffix prefill are at
most 8192. If that is not the intended rule, call the alternative a threshold-triggered history flush—not native
capacity eviction.

### LEG-A-3 — CRITICAL — A1 and A2 do not identify their stated mechanisms

`clf_pinned_echo` versus the draft's pin-only `clf_control` changes semantic selection **and** adds a text channel,
source labels, prompt tokens, and possibly extra eviction. A1 can pass through generic re-injection even if the
selector's columns are useless. “Same-role-pool exact-column” is necessary but is not a complete null: the control
must also echo its own matched spans through the identical renderer with the identical added-token budget.

`clf_pinned_echo` versus `role_pinned` is still more confounded: learned selection, tool eligibility, and echo are
all changed together. The current “all prior user, no tool, no echo” comparator is not the right parameter-free
comparator for a selector whose universe is user + tool. Use a role-and-resource-matched recency rule over the same
user/tool candidates and echo its chosen spans identically. The old user-only role rule can remain descriptive.
A2 may then mean “learned ranking beats within-role recency”; it cannot mean “tool-output retention matters”. A
tool-specific causal claim needs an additional arm that replaces only selected tool spans with matched tool spans
while holding selected user spans and all resource counts fixed. Without that arm, explicitly make no
tool-source-specific causal claim.

The matched control also needs a frozen seed, disjointness, same-role quotas, length and turn-age matching, and a
fail-closed rule when an exact match is impossible. Repeating or cyclically rotating a small pool is not an
independent control.

### LEG-A-4 — HIGH — newline-only tool segmentation and verbatim echo are not safe or fully specified

The coder brief adds “cap 40 lines per message, longest first”, but the registration does not. That is a substantive
selection policy, and longest-first preferentially admits bulk payload rather than durable facts. A newline may be
an entire huge JSON/list/file payload or half of a multi-line record. The classifier's paired encoding is registered
for short sentence-like inputs; an unbounded second sequence is not covered by the current `max_length=192`,
`truncation="only_first"` path. Whole-span admission versus partial clipping at the 25% budget is also undefined.

Use newline-first segmentation, then the registered sentence splitter within each nonempty line, then consecutive
token chunks that fit the classifier's second-sequence limit. Preserve source order; process all chunks. If this is
too expensive, the preflight stops—do not introduce a BFCL-content-dependent longest-line cap. Rank thresholded
chunks by probability, then recency, then stable source order; greedily admit whole chunks and leave unused budget
rather than partially pinning a chunk whose full text is echoed.

Raw tool output must not be copied unescaped into a current user message. It can contain chat-control strings,
`<tool_call>` syntax, previous calls, or user-authored file content. A `tool:` prefix does not prevent prompt-role
injection or valid-but-unwanted call replay. Render source-labelled JSON-quoted data under a neutral header (not the
current “Earlier user instructions” header), fail closed on tokenizer chat-control tokens, and use exactly the same
renderer in treatment and controls. Generic literal copying is expected—correct tool arguments often must copy an
identifier—so the useful safety measure is structural replay: an unexpected normalized call duplicated from an
earlier call/echo. BFCL's checker can accept extra idempotent reads because it checks final state and response
containment, so final pass and syntactic validity alone do not close this hazard.

### LEG-A-5 — HIGH — the primary cohort/inference and A3 manipulation check are incomplete

`long_context` is the right predeclared category, but category membership is not equivalent to actual eviction. A
no-eviction case measures echo selection, not retention. Define a pressure-exposed primary subset by an
outcome-independent, predeclared prompt-length rule (for example, a no-echo `full` rollout prompt over 8192 before
checker results are read), retain all 16 in a secondary category table, and register a minimum exposed cluster
count. If fewer than the minimum are exposed, the leg is inconclusive rather than an echo-only “retention” result.

The statistical test is also underspecified: “cluster robust” does not name a p-value method, continuity correction,
or zero/tie treatment. With at most 16 clusters, use an exact one-sided paired sign-flip test over case differences
(enumeration is at most 65,536 flips), then Holm step-down over A1–A3; report the continuity-corrected t bound only
as descriptive continuity with LEG B.

A3 can pass vacuously when `full - evicted <= 0`, because half of a negative gap is an easier target. Add a
manipulation check: `full - evicted` must be positive under the predeclared one-sided case-paired test; otherwise A3
is automatically ineligible and the result is “no measurable eviction opportunity”. `full` is a reference, not a
ceiling.

### LEG-A-6 — HIGH — safety and preflights permit ambiguous or vacuous outcomes

The safety units are absent. Counts must be case-level on the primary set: a case is counted once if any generation
sub-step times out, truncates, degenerates, emits an invalid call, or unexpectedly replays a prior call. Define
`degenerate` exclusive of truncation so the two clauses are not redundant. LEG B used `invalid <= full`; this draft
silently changes it to `full + 1`. At `n=16`, one case is 6.25 points and is incompatible with the earlier “at most
2 points” safety reading. Restore `invalid <= full` (and apply it to cases, not a variable number of calls) unless a
new rationale is registered.

The preflights need the following fail-closed conditions, none of which may trigger selector or harness tuning:

- Competence is measured on `full`, not the arm currently named `base`: at least 5/32 overall **and** 2/8
  `long_context`; try 1.7B, then the precommitted 4B fallback once, and stop if 4B fails. Record that BFCL dev selected
  the trunk.
- Bitwise determinism uses four fixed IDs (one per category) and compares the complete generated-ID, normalized-call,
  tool-output, and checker trace across fresh environments, not only final text.
- On every dev generation: the complete system/tool prefix survives; no current-semantic-turn ID is in cache at
  eviction; physical cache accounting is exact; candidate spans are only from earlier semantic turns; treatment,
  matched control, and recency comparator have exact per-role pinned-column and echo-token equality; all match
  fallbacks are recorded. Any invariant failure stops.
- Feasibility is gated, not merely reported: at least 4/8 dev `long_context` cases must be pressure-exposed, and at
  least four exposed case-turns must select a tool chunk. Otherwise the sealed run is not an agentic/tool-retention
  test at this selector and stops without refitting.
- Coverage reports selected/eligible spans by source role, actual versus nominal 25% budget, number rejected by
  capacity, and exposed/no-pressure cases. There is no accuracy/recall tuning on BFCL.
- Project sealed cost from the selected trunk and all registered arms with the 32-case category mix. The 12 GPU-h
  cap is a sound operational precommitment. A timing-only amendment may occur before sealed contents/results are
  opened, but it may change only the cap—not cohort, arms, segmentation, selection, renderer, controls, statistics,
  or safety. Hash the final harness, selector, trunk, tokenizer, data manifest, checker, and registration before the
  sealed authorization.

### LEG-A-7 — MEDIUM — lineage is mostly honest, but BFCL influenced more than the draft admits

BFCL is a development benchmark for at least five independent reasons:

1. Its vendored schemas, Qwen tool template, executors, and checkers were already inspected and implemented.
2. Its 100 dev-derived finder labels were scored; the 1/23 user-span failure rejected the prior finder.
3. The 704 non-cohort-case audit established schema-first geometry, overflow concentration, tiny user pools, and
   user/tool literal provenance; those observations directly motivated protected roles, the tool candidate pool,
   primary stratum, and controls.
4. The classifier specification/data were authored after that audit. `data/classifier/kimi_gen_data.py` explicitly
   names BFCL and instructs that tool-output identifiers are `fact`, so “no BFCL item or paraphrase entered
   training” can be true while **BFCL family feedback still shaped the label/policy family**.
5. The 32 dev cases will select 1.7B versus 4B and measure feasibility/cost.

After registration, BFCL text legitimately reaches the frozen selector at inference, including model-produced tool
outputs. It must not reach weights, threshold, role eligibility, splitter/chunker, budget, renderer, controls,
statistics, safety, or trunk choice except through the single precommitted 1.7B→4B rule. Enforce read-only artifact
hashes before/after every run and prohibit any fit/optimizer/import path in the harness. A preflight failure is a
reported development failure, not permission to add BFCL-inspired tool examples and rerun the same sealed family.

The sentence “The no-contact family is registered after this leg regardless of outcome” is too late: the family
choice could still be conditioned on the BFCL result. Freeze the shortlist, priority rule, contact screen, selector,
and mechanism now, before any LEG A outcome.

### LEG-A-8 — MEDIUM — the cited provenance percentages need an audit

The 117.971% total above contradicts the prior report's claimed precedence/exhaustiveness. This does not refute the
observed need for earlier user and tool material, but it does refute the current “37% not found/derived” reading.
Preserve the raw extraction records and publish a mutually exclusive table with one denominator and explicit units
(literal occurrence, argument, or call) before using those percentages as motivation.

## No-contact candidates and screen

Immediately before writing this review, at repository HEAD `c09549fb27c91bbccef65cc882657afcf899291f`, a
case-insensitive current-worktree and all-Git-history search returned zero files/commits for each candidate name,
alias, and repository URL below. I inspected only public project-level metadata/landing pages, not any benchmark
item, checker, template, response, label, trajectory, or task file.

Candidate priority (metadata-screen order, not three datasets to inspect):

1. **APIFlow-Bench v1.0** — long chain API workflows, local deterministic mocks and validators; strongest first
   candidate for reproducible long-horizon retention. Project metadata: <https://github.com/postmanlabs/APIFlow-Bench>.
2. **Toolathlon / The Tool Decathlon** — long-horizon multi-application tool execution with dedicated execution
   checks; feasibility/local-state dependencies must clear the screen. Project metadata:
   <https://github.com/hkust-nlp/Toolathlon>.
3. **ToolTalk** — a small handcrafted multi-turn tool-conversation family with ground-truth tool sequences; useful
   fallback if it has enough native pressure and item-level headroom. Project metadata:
   <https://github.com/microsoft/ToolTalk>.

The screen must be executed in this order:

1. Before acquisition, commit the selector/trunk hashes and a benchmark-agnostic adapter contract fixing candidate
   roles, chunking, `K`, budget, echo renderer, controls, safety, outcome, and statistics. Project-level metadata may
   decide feasibility; benchmark items may not decide design.
2. Record a pre-contact ledger search over the worktree, untracked files, full Git history, prompts, reviews,
   caches/manifests, and prior result names for the candidate's name/aliases, repository URL, paper ID, task IDs,
   checker names, and canaries. The current zero-hit search is the starting record, not a substitute for the later
   machine-wide/data-cache screen.
3. Select the first metadata-eligible candidate only; download a pinned archive and hash it without rendering item
   contents. Do not open all three. Eligibility requires a usable license, local/replayable environment, no ranking
   LLM judge, no live-state dependence in the scored slice, enough clusters for the frozen test, and natural context
   pressure at the already-frozen `K`—no synthetic padding or K tuning.
4. After selection and freeze, an adapter-only worker may inspect the chosen protocol/checker/template. It may make
   mechanical compatibility changes covered by outcome-blind synthetic tests, but cannot change the mechanism. If
   the frozen eligibility rule fails, record the family as contacted-and-rejected and move to the next candidate
   without learning from its items.
5. After opening, run exact/normalized n-gram and semantic-nearest-neighbour overlap against classifier rows,
   b3/S2/Multi-IF/BFCL/IFEval material, prompts, and prior model outputs. Any item/template/checker overlap or evidence
   of prior response use disqualifies the family; never delete overlapping training rows and retrain to rescue it.
6. Do not consult public model responses, trajectories, labels, leaderboards, or per-item difficulty to choose a
   subset or trunk. Freeze IDs by public order + seed before the first model response, retain all records, and allow
   only the already-registered competence fallback.
7. Call the eventual claim **repo-level no-contact zero-shot transfer**. Public benchmarks may have appeared in the
   trunk's pretraining; a repository contact screen cannot prove global training-data absence. Run/report any
   available canary or recitation check, but do not upgrade the claim to contamination-free.

## Exact registration changes

Replace the draft's harness, selector, arms, contrasts, safety, preflight, outcome, and lineage paragraphs with the
following text before any BFCL preflight or sealed run. This is deliberately executable rather than leaving choices
to the coder:

> **LEG A REVISED REGISTRATION (2026-09-03; effective only after review and before any BFCL preflight outcome).**
> **Lineage.** The selector is the frozen LEG B seed-0 artifact and threshold, with all registered hashes. No BFCL
> item or item-level paraphrase entered its training rows. BFCL is nevertheless a DEVELOPMENT family: its dev finder
> labels, schemas/template/checkers, non-cohort geometry/provenance audit, and failures preceded and influenced the
> tool-fact label concept, protected roles, candidate roles, primary stratum, and controls. The 32-case dev split may
> choose the trunk only by the fixed 1.7B→4B competence rule below. This is post-development within-family evidence,
> never zero-shot evidence.
>
> **Experimental unit.** Each arm is a fresh deterministic end-to-end rollout from a byte-identical case and
> environment initial state. Arms are paired by case; after the first differing action their histories may diverge
> and are not claimed token-identical. Record each arm's first divergence and every pressure/eviction event.
>
> **Layout and eviction.** The never-evictable prefix is `[0,max(4,system_turn_end))`, where `system_turn_end` is the
> token boundary after the complete serialized system/tool turn, including schemas and tool-call format contract.
> At every generation sub-step of semantic user turn `t>=2`, track `history_end` from the BFCL turn structure: the
> whole current semantic turn, including its user request, same-turn assistant/tool sub-steps, and new assistant
> opener, is the suffix. Let `K=8192` physical KV columns. Reserve the suffix, prefill history only, and remove the
> oldest eligible unpinned columns in `[protected_end,history_end)` until suffix prefill will leave at most K physical
> columns; then prefill the suffix and generate. If protected + pinned + suffix cannot fit, drop lowest-ranked pins;
> if protected + suffix alone cannot fit, mark the case-arm infeasible and fail safety. `full` uses the identical
> two-stage schedule without deletion. Pressure eligibility is computed from the no-echo full-arm prompt length, so
> echo-induced overflow is recorded separately and cannot create primary eligibility.
>
> **Candidates and budget.** Candidates come only from semantic turns before the current user turn. Prior user text
> uses the registered sentence splitter. Prior tool output is split newline-first, then by that splitter, then into
> consecutive chunks fitting the classifier's second-sequence token limit; empty chunks are dropped, source order is
> retained, and there is no longest-line cap. Score without context using the true `user`/`tool` role. Keep iff
> `P(rule)+P(fact)>=0.5`; rank by probability, recency, then stable source order. The nominal pin budget is
> `floor(0.25 * eligible_columns)`; greedily admit whole chunks, then capacity-clamp from lowest rank. Never partially
> pin while echoing a whole chunk. Report nominal and actual budgets.
>
> **Echo and controls.** Echoes use a source-labelled, JSON-quoted neutral data renderer and fail closed on any chat
> control token; the treatment and both controls use byte-identical framing. Arms are `full | evicted | clf_pinned |
> clf_pinned_echo | matched_control_echo | role_recency_echo`. `matched_control_echo` uses a frozen seeded draw of
> disjoint nonselected spans matched per selected span on role, token width, and source-turn age; it matches actual
> pinned columns and added echo tokens exactly, with no repetition/rotation. `role_recency_echo` draws the most recent
> spans from the same user/tool candidate universe under the treatment's per-role column quota and exact echo-token
> budget, without reading text scores. An impossible exact match is a recorded method failure, never a fallback.
> The prior-user-only role arm is reported only. No tool-output-specific causal claim is made without a separate
> source ablation that changes only selected tool spans.
>
> **Primary and statistics.** The fixed primary population is sealed `long_context` cases for which the no-echo
> full-arm rollout has at least one `t>=2` prompt over K before checker results are read. All 16 long-context cases and
> other categories are reported; nonexposed cases are explicitly echo-only. Fewer than 8 exposed primary clusters
> makes the leg INCONCLUSIVE. Per-case final pass is binary. Use exact one-sided paired sign-flip p-values and Holm
> step-down alpha 0.05 over: A1 `clf_pinned_echo-matched_control_echo>0`; A2
> `clf_pinned_echo-role_recency_echo>0`; A3
> `clf_pinned_echo-evicted > 0.5*(full-evicted)`. A3 is automatically ineligible unless the one-sided paired
> manipulation check `full-evicted>0` passes. Report effects and continuity-corrected t lower bounds descriptively.
> `full` is a reference, not a ceiling. A2 supports learned ranking over within-role recency, not a tool-source claim.
>
> **Safety.** Count cases, not calls: any sub-step makes a case timeout/truncated/nontruncation-degenerate/invalid/
> unexpected-duplicate-call for that arm. Required per arm versus full on the primary set: timeouts=0; truncated<=
> full+1; nontruncation-degenerate<=full; invalid<=full; unexpected duplicate calls<=full; chat-control echo events=0.
> Literal identifier copying is reported and is not itself failure. Every registered arm must be safety-intact.
>
> **Preflight.** On dev, `full` competence must be >=5/32 overall and >=2/8 long-context; test 1.7B then 4B once,
> stopping if 4B fails. Four fixed cases (one/category) must reproduce complete ID/call/tool-output/checker traces.
> All layout/cache/control invariants above must hold in 100% of invocations; >=4/8 long-context cases must be
> pressure-exposed and >=4 exposed case-turns must select a tool chunk, else stop without refitting. Report coverage
> by role and budget use. Project the selected trunk and all arms to the 64 cases; run sealed only at <=12 GPU-h. A
> timing-only cap amendment before any sealed content/result is viewed cannot change scientific choices. Freeze and
> record hashes of registration, harness, selector, trunk, tokenizer, BFCL manifest, template, and checker before
> sealed authorization.
>
> **Outcome.** Pressure manipulation + A1 + A3 + safety support an end-to-end pin-and-reinjection benefit on this
> post-development BFCL family. If A2 alone fails, within-role recency is the preferred simpler selector and no
> learned-ranking advantage is claimed. Failure of A1/A3 is “not detected at this selector and high-effect screen”,
> not proof of no smaller effect. Preflight failure or too few exposed clusters is INCONCLUSIVE, not a negative.
> Nothing from BFCL may update the selector or rerun this sealed family. The no-contact shortlist/priority and screen
> in this review are frozen before LEG A outcomes.

Replace the eventual model-card sentence with this exact paragraph:

> The selector was fit on 20,054 hand-written, item-disjoint rows; no BFCL item or item-level paraphrase was used.
> BFCL was not untouched: its dev labels, schemas/template/checkers, and aggregate non-cohort analyses preceded the
> final selector and influenced tool-fact labels, protected roles, candidate roles, and harness choices; its dev
> split also selected the 1.7B/4B trunk by a frozen rule. The 64-case cohort was hashed in advance and its sealed item
> contents were not opened or executed before the final freeze. LEG A is a post-development, end-to-end comparison
> of KV retention plus source-labelled text reinjection, not a pure-KV or zero-shot result. Inference-time scoring of
> BFCL user/tool text applies the frozen selector and performs no fitting. “Repo-level no-contact zero-shot” is
> reserved for the separately frozen family, and does not assert absence from trunk pretraining.

## VERDICT

**UNSOUND.** Three CRITICAL, three HIGH, and two MEDIUM findings. The protected prefix, `long_context` focus, and
pre-query ordering are directionally correct, but the current controls and rollout language cannot identify the
registered claims, and the small-n/safety/coverage rules allow incompatible readings. Apply the replacement text
above and bind it to the final harness hash before any BFCL preflight or sealed outcome.
