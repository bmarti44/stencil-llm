# Stencil: back-on-track research plan (rev 7.1, 2026-09-11)

Rev 6 = Brian's four directions after rev 5: (1) publish the classifier now, publicly, under
the `bmarti44` HF namespace with a descriptive name (section C, Release 0); (2) clean up ALL of
the code, not just changed files (section C, "Code cleanup"); (3) GPU lock wrapper accepted,
but the default becomes concurrent sharing with the looped-transformer session because both
workloads are small (section E, sized from measured memory); (4) execute autonomously, using
Astra to get unstuck (section D rules 9-10, and the open decisions are resolved with defaults).
Rev 5 = Brian's de-over-engineering pass: `wave_static` arm dropped (five arms), verification no
longer promises an impossible historical re-score, Release 2 made concrete as a text-only
`stencil-reminder` package unless Exp 1 says pins matter, and a program-level stop rule added.

Review trail: Astra repo review (NOVEL 3, IMPACT 4, ITERATION 3); Astra plan round 1 on rev 1:
24/100, 34 findings; Astra plan round 2 on rev 3: 80/100 (on-track 9, success 7, rigor 7.5,
novelty 8.5) with four minimum edits, all applied in this rev 4: full-support WHERE
permutation with gain preserved and `fixed_bias` naming; no causal inference from
nonsignificance and breakage limit inside PASS; honest comment-checker qualification instead
of impossible historical re-scoring; FOCUS-3 scope/overflow mapping and non-vacuous adapter
check in the Exp 3a contract plus frozen two-request/three-input selection in Exp 2a.
Astra's success probabilities: Exp 1 75%, Exp 2a 35%, Exp 3 55% (of a clear answer, not of a
positive result). Review files: scratchpad astra-repo-review.md, astra-plan-review.md,
astra-plan-review2.md (to be copied under results/reviews/ once execution starts).

## Rev 7 (2026-09-11, Brian's reframe): one published model artifact, proven against itself

Brian, mid-execution of rev 6: "your goal is to build and publish a model artifact to
huggingface that is able to focus on the relevant instructions for a task over a long horizon
agentic coding session. first you would clean up the repo, and then you would work towards
that. you would need to prove that your artifact outperforms the same artifact without the
modifications." This section supersedes section C's three-release endpoint (Release 0 stays
published; Releases 1 and 2 are replaced by the artifact below). Sections A-B, D-F stay in
force as evidence machinery and process; nothing already registered changes.

Rev 7.1 applies Astra's round-3 review (results/reviews/2026-09-11-plan-rev7-review-astra.md,
54/100, seven minimum edits): one frozen shipping configuration with an explicit session
interface; token-level prompt matching; applicability frozen before generation with a fixed
denominator; the sentence-window identity defect fixed (CONTRACT.md amendment 2); the
fallback frozen with its two-attempt interpretation; a measured, arithmetically correct
budget; and the existing BFCL multi-turn long-context workload registered as the agentic
check (Exp 5). The wave line and KV pins are off the artifact's critical path.

### G. The artifact: one frozen shipping configuration

- Name (descriptive, Brian may rename): `bmarti44/stencil-focus-qwen3-1.7b`. One HuggingFace
  model repo: the frozen Qwen3-1.7B trunk (weights copied; base attribution and revision on
  the card), a `stencil/` package loaded with `trust_remote_code`, and a config flag
  `stencil_focus` (default `true`). The modification is to inference-time session-memory
  handling, not to the trunk's learned weights; the card says so in its first paragraph.
- Session interface (package-owned, the thing Exp 4 evaluates and the thing users call):
  `StencilFocusModel.from_pretrained(repo, stencil_focus=True)` wraps
  `AutoModelForCausalLM`; `session = model.new_session()`; `session.add_message(role, text)`
  for every message of the conversation in order (user/mentor lines feed the register;
  other roles are stored only); `session.build_prompt(request)` returns the exact prompt
  string; `session.generate(request, **kw)` = build + greedy/`generate`; `session.reset()`
  clears state. Session state is isolated per session object.
- Frozen shipping configuration (decided now, not by later experiments; the classifier
  register is an explicitly UNPROVEN maintenance hypothesis for Exp 4: Exp 1 showed the
  role-echo policy beating the classifier-echo policy on Multi-IF, which is a different
  construction, and does not decide the long-session bundle either way):
  0. AMENDED 2026-09-11 before any LONG generation (Exp 4 registration amendment 1): the
     frozen FOCUS-3 register overflows on 138/144 LONG items in the CPU phase and applies
     no relation on SETUP-LONG, so the PRIMARY policy is the zero-parameter role rule over
     the truncated-away region (newest-first mentor sentences outside the window). The
     register below stays in the package as the OPT-IN maintainer with its error table
     and is evaluated descriptively on SETUP-LONG only. There is one primary policy and
     no fallback rerun.
     Amendment 2 (Astra implementation review, same day) fixes the execution matrix
     (48 + 256 + 16 = 320 generations, no SCREEN oracle), the timeout rule, the excess
     formula, completeness and the enforced prompt equality; see REGISTRATION.md.
  1. Register (opt-in): admission by the published sentence classifier
     (`bmarti44/assistant-memory-sentence-classifier`, frozen) and lifecycle relations by
     the frozen relations-v2 seed0 head (`data/classifier/model/relations-v2/seed0`, sha
     recorded on the card), i.e. the FOCUS-3 runtime `src/stencil/focus3.py` as mapped in
     `results/memorycode-derived/CONTRACT.md` (task scope `MAIN`, 4-sentence windows with
     their own turn index per amendment 2, overflow at 16 rows counted and reported).
  2. Rendering: live rows (status live, scope `MAIN` or global, chronological) rendered as
     `Earlier instructions still in force:` + `- <sentence>` lines, newest-first packing,
     budget E = 256 tokens including the header, inserted immediately before the current
     request. The conversation window is truncated at token boundaries so that the COMPLETE
     prompt (window + reminder + request) has the same token count as the unmodified prompt.
  3. Backend: `transformers` only. No KV pins, no attention controller, no hand-rolled
     runtime in the artifact. The research runtime is used only to run the evaluations
     bitwise-deterministically; the parity gate below ties the two together.
  4. Off switch: `stencil_focus=false` → no register is built, no reminder is rendered, the
     window is the plain recency window at the same token budget, decoding identical.
     Nothing else differs. `tests/test_stencil_focus.py` asserts that with the flag off the
     prompt equals the plain window and the outputs equal `AutoModelForCausalLM`.
- Claim shape: the ARTIFACT AS A BUNDLE beats the same artifact with `stencil_focus=false`
  (Brian's criterion). Component-wise ablations are not claimed; Exp 1 and Exp 3c are
  reported as secondary evidence about the register and the echo machinery.
- Registered fallback (frozen now, before any LONG outcome is seen; clarified after Exp 1
  read, still before any Exp 4 generation): if Exp 4 reads NOT PROVEN, the register policy
  is swapped ONCE to the zero-parameter role rule over the TRUNCATED-AWAY region: every
  mentor sentence that lies outside the recency window, newest-first packing, same renderer
  and budget (the analogue of Exp 1's winning `role_echo_only` arm, which restates the
  evicted region; restating the newest sentences of the whole session would duplicate what
  the window already shows) and Exp 4 is rerun on the same items with base outputs reused. Two fixed policies, each tested at one-sided .025, bound
  the family-wise false-positive rate at .05; both attempts are always reported and the
  selected policy's interval is not presented as a simultaneous 95% interval.
- Parity gate before publication (mirrors Release 0's export verification): on the 16
  SETUP-LONG items the published wrapper must render byte-identical prompts to the research
  runtime and produce identical greedy outputs; with `stencil_focus=false` its outputs must
  equal plain `AutoModelForCausalLM`. A clean-environment example (`pip install`, load, one
  long session) is the release gate. No research number is attributed to the artifact until
  parity holds.
- Off the critical path (parked, not cancelled): KV pins (Exp 1 decides whether a later
  Qwen-only backend is worth registering); the attention controller (Exp 2a/2b remain the
  rev 6 method-claim line, run only when the GPU is otherwise idle and never a component
  of this artifact); `deploy/stencil_wave/` is archived.

### H. Exp 4: the proof, a long-horizon coding-session head-to-head (registered before its GPU spend)

- Workload: MemoryCode-derived LONG items. Enumeration on 2026-09-11: 320 candidate
  (dialogue, session) items with history-regex checks and a prior instruction; 108 fit in
  3,584 tokens (Exp 3 uses them) and 212 do not. Verified quantiles (Astra round 3): all
  candidates min 705 / median 8,364 / P90 30,283 / max 61,046 tokens; the LONG set min 3,693
  / median 15,623 / P90 51,734 / max 61,046. W = 3,584 tokens is the IMPOSED evaluation
  budget (the local base config supports 40,960 positions); under that budget the base sees
  only the newest part of the session, which is the condition the artifact exists for.
  Split by dialogue with `random.Random(1)`: 16 SETUP-LONG (pilot + parity), 128 SCREEN-LONG
  (primary), 68 reserve, never opened in this program. One generation per item (the first
  `history_eval_query`), 512-token cap, deadline 300 s.
- Prompt construction (both arms; native single-message format, CONTRACT.md): the thread is
  the conversation text truncated at a token boundary to keep the NEWEST tokens; the
  modified arm's thread is truncated by exactly the reminder's rendered token count so the
  complete prompts have equal token counts (asserted per item and stored in the record).
  Whole-session packing is NOT used (it makes prompts unequal, Astra round 3).
- Arms:
  | arm | prompt |
  |---|---|
  | `base` | `stencil_focus=false`: recency window at W |
  | `focus` | `stencil_focus=true`: register built by the frozen runtime over ALL mentor lines of sessions 0..s−1 (including the truncated-away ones), reminder rendered, window shortened to match |
  | `oracle` | descriptive ceiling on SETUP-LONG only (and on SCREEN-LONG only if the measured budget allows): the label-derived live set through the same renderer and window |
  Label rule, stated precisely: only `oracle` may use gold labels to construct its
  intervention; selection, scoring and the error table read labels. `tests/test_memorycode.py`
  extends its isolation check through the package's own prompt-building path.
- Outcome and checker: STRICT compliance under the vendored official checker with
  applicability FROZEN from the query before generation (CONTRACT.md amendments 3/3b: a
  required parent object that is omitted scores 0.0; the required structure, class or
  function by whole-word match on the query, must be present or the item is strict-FALSE;
  the primary cohort is fixed before generation; no arm's output changes the denominator). Fractional score reported
  alongside. Convention compliance is the outcome; functional correctness is neither
  measured nor claimed.
- Primary estimand: `focus` − `base` on strict compliance, paired by item, N = 128. Exact
  McNemar on discordant items, two-sided p, and the conservative paired interval (separate
  97.5% Clopper-Pearson bounds on b/N and c/N, union bound). Power, stated: the interval is
  wholly positive first at 10 wins / 0 losses; with 10 losses it needs 29 wins; at
  win/loss probabilities .15/.05 the positive-result probability is about 26%, at .25/.05
  about 91%. N = 128 establishes a large benefit, not a modest one.
- Output-failure guard: invalid (no code fence / unparsable), truncated at the cap, and
  degenerate (4-gram repetition) generations counted per arm as EXCESS over `base`.
- Readings (exhaustive):
  - PROVEN: interval entirely above 0 AND `focus` excess output failures ≤ 5% of items →
    publish the artifact with the table.
  - POSITIVE-WITH-OUTPUT-FAILURE-EXCESS: interval above 0 but excess failures > 5% → not
    PROVEN; published as descriptive with the failure table; the fallback is NOT triggered
    (it is a policy revision, not an output-failure fix).
  - NOT PROVEN: interval covers 0 → the frozen fallback (G) runs once; the second reading is
    final.
  - HARM: interval entirely below 0 → published as demonstrated harm; program ends.
  - `oracle` − `focus` on SETUP-LONG is the reported headroom; it gates nothing.
  - The error table (false admissions, missed instruction sessions, overflow events,
    reminder tokens, empty reminders) is published with every reading and is never read as
    evidence of accurate maintenance: activity is not accuracy.
- Budget, measured: Exp 0 pilot family `memorycode-long` = the 4 longest SETUP-LONG windows
  at W = 3,584 with a 512-token generation (the ≤ 3,584 pilot measured 42-86 s/generation at
  2,446-3,002 tokens, 11.7-12 tok/s, 6.5 GB allocated / 8.0 GB reserved). Ceiling =
  1.5 × t_max × (2 × 144 + 16 [oracle on SETUP-LONG] + 128 [the permitted fallback rerun of
  `focus`]) = 1.5 × t_max × 432 generations, plus the 4-generation pilot and the 32-generation
  parity check (16 items × 2 flag states) = 468 generations; at t_max = 100 s that is 19.5
  GPU-h worst case and roughly 7 GPU-h expected (median generations are far below the cap). `oracle` on
  SCREEN-LONG (+128) is added only if t_max ≤ 60 s. The registration records the measured
  t_max, the ceiling, and the expected value from the pilot's mean; chunks ≤ 50 min; atomic
  per-item records; INCOMPLETE is never rescued.

### H2. Exp 5: the agentic check on the existing BFCL multi-turn long-context workload

Brian's goal names an agentic coding session; MemoryCode supplies conversation history with
mentee replies given, one final generation, no tool feedback. The repo already vendors BFCL
v3 multi-turn (`data/bench/bfcl_v3_mt`, 200 items per category incl. `long_context`) with a
runner (`scripts/bfcl_mt.py`, `--mode free` = the model's own tool calls and real tool
feedback drive the episode, `src/stencil/bfcl.py`). Exp 5 = the same `stencil_focus` toggle
on `multi_turn_long_context` in free-running mode: `base` vs `focus`, per-item pass under the
upstream checker, paired exact test and the same interval, N from the pilot budget (target
the full 200 if ≤ 4 GPU-h, else a `random.Random(2)` subset registered before launch).
Registered in `results/bfcl-long-context/REGISTRATION.md` after Exp 4 reads, with its own
pilot and data-lineage line (nothing in the register or classifier was fit on BFCL:
LEDGER-PLAN.md:634 records the lineage). The card says "coding-session instruction
retention" after Exp 4; it may say "agentic coding session" only if Exp 5 is also positive.

### I. Execution order, rev 7.1, and the program stop rule

1. Cleanup first (in progress): full suites on the pre-cleanup tag and on main agree →
   comment-checker fix → invariants → commit → push → archive the closed scripts with
   `archive/scripts/MAP.md`.
2. Secondary evidence already registered and partly running: Exp 1 (chunks 1-2 done/running),
   Exp 3b/3c (register vs restate-all on the ≤ 3,584 items). Their RESULTS.md files go on
   the card as secondary evidence; they do not change G's frozen configuration.
3. Exp 4: registration (`results/memorycode-long/REGISTRATION.md`, items.json with the seed-1
   split, pilot budget) → run → RESULTS.md → Astra result audit → fallback once if NOT PROVEN.
4. Packaging: `deploy/stencil_focus/` (replaces the archived `deploy/stencil_wave/`), parity
   gate on SETUP-LONG, card with the Exp 4 table, the error table and the secondary
   evidence; push under `bmarti44/`. Release 0's card gains a pointer.
5. Exp 5 registration → pilot → run → RESULTS.md → card upgraded to "agentic" only on a
   positive reading.
6. Only then, if GPU time is idle: Exp 2a (+2b) as the rev 6 method-claim line, research
   artifact only.
Stop rule: PROVEN publishes; NOT PROVEN allows exactly the one frozen fallback and then
publishes whatever the second run says (a second null is a published negative with the
artifact withheld as a claim); HARM publishes the negative. No new arms, workloads, or
components enter without a new registration.

### J. Rev 7.2 (2026-09-12): Exp 4B, the same head-to-head on the Qwen3-4B trunk

Exp 4's SETUP-LONG at 1.7B read a strict floor under a corrected oracle (0/16 on every arm;
per-constraint focus − base −5.2 points [−10.6, −0.4], descriptive, n = 16), so the 128-item
SCREEN at 1.7B was deliberately not run and is reported as "primary not run". Brian chose
the most likely direction from `results/reviews/2026-09-12-options-memo.md`: the SAME
mechanism and control on the Qwen3-4B trunk with a per-constraint primary. Registered as a
NEW registration, `results/memorycode-long/REGISTRATION-4B.md` (rule D9), consuming the
program's second and last policy revision (rule D2): artifact `bmarti44/stencil-focus-
qwen3-4b`; primary = `fraction_required` (denominator frozen from the query's required
families, structure gate), paired focus − base, 95% percentile bootstrap (seed 0, 10,000
draws) + exact sign test, N = 128 SCREEN-LONG; strict alongside; qualification gate on
SETUP-LONG 4B (oracle mean ≥ 0.20, focus-only failure excess ≤ 5%, focus − base upper
bound > 0) before any SCREEN spend; exhaustive readings PROVEN / POSITIVE-WITH-OUTPUT-
FAILURE-EXCESS / NOT PROVEN (final) / HARM / INCOMPLETE. Everything else in G-H is inherited
unchanged. Section I step 3 continues with Exp 4B; step 4's parity gate and card move to
the 4B artifact; the 1.7B SETUP-LONG result is published as a descriptive negative.

### K. Rev 7.3 (2026-09-12): Exp 4C, the Astra-authorized final confirmation, and program close

Exp 4B's qualification FAILED its output-failure gate (one focus-only unparsable output among
16). Brian delegated the D2-override decision to an open-brief Astra consult; its binding
decision (`results/reviews/2026-09-12-unblock-decision-open-astra.md`) authorized ONE final
confirmation, `results/memorycode-long/REGISTRATION-4C.md`: generation through the shipping
package (research-runtime parity had failed), the 128 SCREEN dialogues plus reserve up to
196 under a timing-only N rule, paired-t primary on `fraction_required`, +5-point failure
noninferiority, HF push only on PROVEN-SCOPED after an Astra audit and a clean-environment
reproduction. Astra's implementation review blocked ten findings; all were closed before
launch. Qualification passed (16/16 plain matches, 8/8 replays, t_max 68.7 s → N = 139).
Terminal reading (`RESULTS-4C.md`): **NOT PROVEN, FINAL**, off 0.0845 → on 0.1049, +2.05
points, 95% [−0.07, +4.16], p = .058, 25/17/97, failures 60 vs 61 (guard also not met).
Program outcome: the artifact `bmarti44/stencil-focus-qwen3-4b` stays repo-only with the
table on its card; nothing is pushed to HuggingFace; no further revision is permitted. Owner
rule from 16:50Z, binding on future registrations: interim results may be inspected; early
stop only for futility; a positive claim still needs the full registered N.

## Context

Brian asked for an audit of the Stencil repo: what has actually been proven, whether the
"does not work" claims hold up, what is missing for an honest HuggingFace release, what the
2024-2026 literature already covers, and what experiment would prove something
mechanically interesting. Three read-only audits (positive results, negative results,
engineering/HF readiness), a web-literature pass, an adversarial Astra (gpt-6-astra, xhigh)
review of the repo, and an adversarial Astra review of rev 1 of this plan (24/100, 34
findings) were run. Rev 3 incorporates the findings that add validity and declines the ones
that add machinery without changing a decision (listed at the end). A second researcher
(session "looped-transformer") shares the GB10; the GPU protocol is in section E. Brian's
acceptance criteria for round 2: on track, decent chance of success, aligned with rigorous
published work, novel; over-engineering is a defect.

## Findings (established by the audits; file references are repo-relative)

### What is proven, and how strong it is

| Result | Trunk / data | Numbers | Strength | Gaps |
|---|---|---|---|---|
| Leg B retention under eviction | Qwen3-1.7B, Multi-IF 909 conv = 484 distinct source prompts (public) | full 65.2, evicted 16.7, clf pin-only 57.2, clf pin+echo 59.2, role pin 60.5 (pooled); C1/C3 p~3.7e-85/1.6e-65 conversation-clustered; C2 FAIL: role rule beats trained selector by 3.5 (conv-mean) / 3.3 (pooled) | Only public-benchmark result; 911/911 evidence files tracked | Echo increment given pins IS identified (+2.0); pin-only vs eviction IS identified (83.6% recovery); the pin increment GIVEN echo is not (no echo-only arm); 909 conversations are 425 pairs + 59 singletons sharing first prompts, so clustering must be by source; encoder weights gitignored; registered NOT SUPPORTED on 1 invalid output vs 0 |
| Internal wave | Qwen3-1.7B, synthetic coding sessions, n=96 | 264k-param controller, adherence 25.2->44.8; hand oracle 38.3, proxy 37.4, prose reinsertion 43.0 (+1.7 pts; reinsertion broke 30 works vs 21) | The one plausible method novelty: a learned per-step positional pre-softmax bias field trained through the frozen attention path, with WHERE/WHEN/selectivity ablations | 1 seed, no p-value; the harness re-serializes the generator's exact current ledger every request (src/stencil/t2_sessions.py:295), so it tests attention allocation GIVEN a correct external ledger; W3b readout found the field NOT decodable as "the governing rule now"; w0-ce reduced MMLU 48.05->45.83 and failed GSM8K noninferiority (WORKLOG.md:1586,1613); **the comment-type 0/120 "null" is a checker bug**: `src/stencil/t2_runner.py:91-94` requires the last line of `ast.get_source_segment(code, fn)` to be `# reviewed`, but a function's AST segment ends at its last statement and excludes a trailing comment, and `wave_ref.py:29` generates exactly that form; controller reduces to learned query-key matching plus a scalar gain (wave.py:29); w0-ce.pt untracked |
| SELECTOR | Qwen3-1.7B, synthetic named-query task, N=32, n=128 (5/128 vs 113/128) | 3.9 -> 88.3; reinsertion 84 @ 504 tok from a different block | Clean actuator test, bitwise zero-identity | Task is `current[field]` lookup with the field named (results/selector-review-sol.md:80-88); no retrieval or LoRA baseline; evidence JSON + weights untracked |
| GPT-2 focus cache | GPT-2 small, windowed attention | 100 vs 4.3 zeroed; transplant 28/32 | Clean construction | Gap guaranteed by construction; results/gpt2 0 tracked files |
| larger-test-v2 | Qwen3-30B-A3B, 64 authored episodes | register vs none: delivery 35/0/28 p=3e-11 | Rigorous stats | Prose reminder T ties/beats register on every family; R loses semantic integration 45 vs 52 (p=.0078) |
| FOCUS-3 v8 diagnostic | Qwen3-4B, 64 reused-template episodes | automatic register 57/64 vs none 29/64 vs oracle 63/64 | Encouraging for AUTOMATIC maintenance (Brian's corrected goal) | No verdict assigned; 25 false admissions in 21 episodes are policy failures, not instrument accidents; templates reused |
| W3a | Qwen3-1.7B synthetic, 96 sessions | wave 55.1 vs reinsertion 53.1 vs base 36.6, zero contamination | Qualified clean-format positive | Generalizes to ONE registered unseen rendering only |
| W3 README bullet | | "+42 pts, 73/73 never wrong" | **Misrepresents two FAILED gates** (WORKLOG.md:1326-1337, results/w3-results-sol.md) | Must be rewritten; the W3b readout failure is itself informative |

Cross-cutting, stated precisely: correct request-time restatement of the current rules is the
baseline to beat. No mechanism tried so far has beaten it by more than ~2 points (wave +1.7,
W3a +2.0) and several lost to it (FOCUS-2d 143/256 vs 176/256; larger-test-v2). C2 says nothing
about prose vs structure; it compares two pin-selection policies. Brian has superseded "must
beat manual prose": reliable AUTOMATION of correct reminders at acceptable cost is the win
(results/CURRENT-GOAL.md:3-7).

### Negative claims, re-verified

- Solid (A): static always-on bias (n=196, -4.6 monotone); deficit-gated bias on the
  **synthetic** conf-v45 bank (n=1024, +0.39, p=.389, 8-cell grid; not IFEval,
  WORKLOG.md:2302); mean-difference skill vectors (18 cells, 0 induction, cosines .89-.98);
  MoE router bias harms competence (16/32 -> 7/32, two-sided p=.022); C2; FOCUS-2d;
  cosine-threshold liveness; blind rhythm pressing; hard-threshold abstain.
- Narrow (B), idea not ruled out, no reopen planned: deficit/classifier-gated bias on cache
  columns (check 28: single dose from a single-span calibration applied to ~3.6 spans that
  cannot each hold mass 0.3; n=20; excess degenerate 5/20; 4 wins/1 loss p=.19); function-vector
  residual steering (operating point chosen on 4 examples by non-degeneracy; grid has no
  efficacy field); check43b concept routing (n=8/cell); check32/33 cache transplant (harness
  never qualified; check34 positive control 59/60).
- Process failures (C): x0.25 dosed wave (+1.5 vs +2.0 gate, one item, p=.549); check42
  (A beat C 151/192 vs 131/192; an ancillary arm's cap failures blocked closure); FOCUS-3 v1/v2
  (one sentence template x64); FOCUS-3 v3-v8 six INELIGIBLE on CPU counters; PRESS T1 (92.9%
  leakage reduction vs a bar unreachable at n=17); four source-replay bank stalls on single
  authoring defects under a no-repair protocol.

README.md:69-76 ("every amplification variant ... closed with data") overstates the per-check records.

### Engineering / publication state

- PyTorch only; hand-rolled bitwise-deterministic `src/stencil/qwen3.py` with `bias_hook`
  (line 397) and `return_hidden` (393). The wave evaluator (`scripts/w_seal.py:57`) and trainer
  recompute the full prefix per generated token; `w0_train.py:46` loads the model at import.
  The manual attention path materializes fp32 [16,T,T] scores and [T,151936] fp32 logits:
  2.25 GiB + 3.48 GiB at T=6,144 before other intermediates. Contexts must stay short and
  peaks must be measured, not assumed.
- `score_work` (`src/stencil/t2_runner.py:59`) executes generated programs with the host
  interpreter under a 5 s timeout; acceptable for the synthetic generator, not for public inputs.
- `pytest tests/` collects 2142 tests; bare `pytest`/`make gate-0` break (no `testpaths`);
  `ruff check` has 1,501 findings, so gate-0 cannot pass on testpaths alone.
- 246 review docs vs 181 experiment scripts; plan/PROTOCOL.md archived; AGENTS.md points at absent files.
- License declarations: root GPLv2, deploy/ MIT, model card apache-2.0; the classifier encoder
  is BAAI bge-small derived. An ownership/component inventory is needed before any relicensing.
- 215 unpushed commits. Untracked and NOT gitignored: models/qwen3-30b-a3b-hf (~57 GiB),
  focus-lora-4b, nested `*/seed*/encoder/*.safetensors` under admission-v2, ft-v3, relations-v3;
  results/focus-mechanism-composition-astra.md untracked but load-bearing; the source-replay
  four-file change is uncommitted.
- Untracked headline evidence: results/qwen/s1-oracle.json, s2-selector.json, s3-a0.json,
  s3-a1-oracle.json, s3-a2-selector.json, s3-final-sealed.json, s3-selector-weights.pt,
  w0-ce.pt, w0-proxy.pt; all of results/gpt2/; ft/encoder/model.safetensors (133,462,104 B).
  (b3-ce-s0.pt and w3a-audit.json are already tracked.)
- The classifier corpus reconstruction path yields 20,054 rows but per-source counts differ
  from the frozen manifest (10,576/4,080/4,543 vs 10,555/4,084/4,560); exact identity is not established.
- deploy/stencil_wave/ (last commit 2026-09-01) ships `b3-ce-s0.pt` with top-k at prefill and a
  constant +3 bias (model.py:96,123); it is not the W0 continuous field and cannot reproduce any
  synthetic result; its parity tests keep strict failures as xfails; publishing the retention
  runner is new implementation work.
- GPU: one GB10, 119 GB unified. At plan time the foreign llama-server had exited (114 GB
  available); it may return. Peer session runs Ouro-2.6B bf16 (~6-10 GB).

### Literature position (2024-2026)

- Attention steering: PASTA; **AutoPASTA (2409.10790)** selects the supporting sentence
  automatically then steers (open-book QA); **SpotLight (EACL 2026)** is dynamic
  deficit-triggered bias with multi-turn MT-IFEval evaluation; InstABoost (ICLR 2026); GUIDE;
  **Directer (2603.06745)** adds a trust-region backoff and beats tuned SpotLight/PASTA on
  rewritten IFEval; **Guiding Giants (2505.20309)** is the closest trained controller. None
  trains a per-position, per-step pre-softmax bias field through a frozen trunk from
  completion loss. That, and only that, is Stencil's plausible incremental method novelty.
- Retention/injection: SnapKV, LKV (2605.06676), Memory Inception (2605.06225), Knowledge
  Packs (2604.03270), V-Steer (2607.26228). Stencil's pin+echo is an empirical application;
  its useful finding is that a role/recency rule beat a trained selector at matched columns.
- Memory maintenance: Mem0, MemGPT/Letta, LangMem. Stencil's register is a small-model
  instance; contribution would be measured reliability, error rates and cost.
- Workloads: IFScale (2507.11538), ManyIFEval (2509.21051) show compliance collapses with
  instruction count; MemoryCode (ACL 2025, Apache-2.0, regex-checked conventions with updates
  across sessions; Llama-3.1-8B 71.7% -> 12.5%) is the closest public workload to Brian's goal.
- Steering reliability (2504.04635, 2505.22637, 2602.17881) and GUIDE/SpotLight/Directer all
  document degeneration at strength; matches check 28/30.

Astra repo verdict: NOVEL 3/10, IMPACT 4/10, ITERATION-SPEED 3/10. Recommendation: one
bounded comparison of the learned controller against prose and fixed steering; make
automatic maintenance of correct reminders the practical objective; close the echo-only
attribution cheaply; publish the useful negatives with a complete artifact release.

## Plan

### A. Re-scope: one method claim, one product claim, both narrow

**Method claim (the novelty candidate).** Given a correct external ledger, a frozen
264k-parameter controller (`src/stencil/wave.py`, checkpoint `results/qwen/w0-ce.pt`) that
allocates attention per token improves joint executable-and-adherent success on fresh short
governed-code episodes over (a) correct prose restatement and (b) fixed attention steering
on the same known governing spans; and the gain depends on WHERE the field points, not only
on WHEN/how much it presses. Scope: attention allocation given supplied rule state. No claim
about discovering, maintaining, switching or clearing obligations; no claim that the field
decodes the governing rule (W3b showed it does not under the registered readout).
Closest work: AutoPASTA, SpotLight, Directer, Guiding Giants.

**Product claim (Brian's corrected goal).** On a MemoryCode-derived evaluation with
instruction updates and cancellations, automatically maintaining the live obligation set
and rendering it as prose at request time matches or beats bounded restate-all on
convention compliance, with false-admission and stale-execution rates reported.
Contribution: small-model reliability numbers, not a new memory architecture.
Closest work: Mem0/Letta (mechanism), MemoryCode (workload).

Reuse: `wave.py`, `w_seal.py`, `t2_sessions.py`, `t2_runner.py`, `wave_ref.py`,
`multiif_evict.py` (`run_arm`, `_score_fields`, cluster stats), `ledger.py`, `qwen3.py`
(`bias_hook`, `return_hidden`, `prefill_with_eviction`), `focus3.py` lifecycle policy +
frozen `data/classifier/model/ft` and relation-v2 classifiers (CPU), `deploy/stencil_wave/`.
Parked (not "closed"): S3 dictionary task, GPT-2 focus cache, 30B FOCUS-3 GPU line,
source-replay banks, residual-stream / function-vector / MoE-router steering, cache-column
gated wave, `qwen_cache.py`. "Miller wave" is motivation, never evidence.

### B. Experiments (first pass ~4-5 GPU-h after the pilot; all Qwen3-1.7B; every estimate is replaced by Exp 0 measurements before launch)

**Exp 0 (CPU + <= 15 GPU-min): fix the instruments, measure the budget.**
1. Comment checker: in `t2_runner.py:91-94` extract the function's source span by line range
   including trailing comment lines up to the next top-level statement; add
   `tests/test_t2_runner_comment.py` with compliant and noncompliant fixtures run through
   `score_work`; add a comment branch to `_oracle_moment` (`t2_runner.py:264`). The historical
   seal cannot be re-scored: `w-seal.json` and the audit store code hashes and aggregates, not
   generated code (`w_seal.py:165`, `w_seal_audit.py:55`). Record the qualification instead:
   "comment compliance was unmeasurable under the old checker and cannot be recovered from the
   sealed artifacts; the 0/120 comment rows carry no evidence either way." No GPU reproduction.
2. Evaluator: reuse the layer-20 feature pass via `bias_hook` instead of two prefix
   recomputations per token in `w_seal.py:57` / `w0_train.py:73`; move model load in
   `w0_train.py:46` under `main()`. Qualify on 8 fixed dev sessions: log max-abs logit drift
   and adherence agreement vs the old runner; no bitwise claim.
3. Seeds: reserve block 14,700,000+ (grep-verified unused today) for all new evaluation
   episodes; smoke fixtures use 14,690,000+.
4. Timing and memory pilot at MAXIMUM context length for each arm family (4 items each),
   recording tok/s, seconds/item and peak memory (`torch.cuda.max_memory_allocated`). Each
   experiment below launches only after its pilot writes a budget into its registration.

**Exp 1: pin increment given echo, on 128 distinct source prompts (~1-1.5 GPU-h).**
- Question: once the selected text is echoed, do the selected KV pins add anything? And does
  the arm we would ship (role-rule echo, standalone budget) hold up?
- Sources: from the exposed 909 records (425 pairs + 59 singletons), pick 128 source prompts
  deterministically (seed 0, no outcome use), one conversation per source.
- New arms, same saved histories and eviction coordinates, same 512-token limit:
  `clf_echo_only` = evicted + classifier-selected echo, zero pins (`run_arm(..., keep=[])`);
  `role_echo_only` = evicted + newest-first prior-user SENTENCES rendered by
  `render_text_ledger`, standalone budget E=256 tokens including header (not borrowed from
  the classifier). Existing full / evicted / clf_pinned / clf_pinned_echo / role_pinned outputs
  reused only after a compatibility check: replay 8 of the 128 `clf_pinned_echo` records on
  the current runtime; require identical generated text on all 8, else regenerate the
  compared arms on the 128 subset (adds ~1 GPU-h) rather than mixing runtimes.
- Scoring reuses `_score_fields` with instruction IDs/kwargs looked up from
  `data/bench/multiif_en.jsonl` by `ci`, exactly as the original run did.
- Script `scripts/multiif_echo_only.py` (~200 lines) importing `run_arm`, `_score_fields`,
  `_cluster_values`, `_contrast`, `_one_sided_cluster_p`, `invalid_output`,
  `repeated_4gram_fraction`; writes `results/qwen/multiif-echo-only-128/` (schema 2, atomic
  per-conversation, `--start/--limit`, records saved as each arm completes).
- Estimands (registered before launch): source-level paired aged-adherence difference,
  D1 = clf_pinned_echo − clf_echo_only; D2 = role_pinned − role_echo_only; D3 =
  role_echo_only − clf_echo_only. Paired mean with 95% bootstrap interval over sources plus
  exact sign test on discordant sources. Noninferiority margin 2 points. Safety: invalid /
  degenerate / truncated counts as excess over `full`, reported, no integer kill.
- Readings: D1 interval entirely above +2 → pins earn their place; retention package keeps
  pins. D1 interval entirely below +2 → pins are dispensable at this margin; ship echo-only.
  Interval straddles 2 → insufficient evidence; ship echo-only on cost grounds and say so.
  D2/D3 decide which selector the reminder package defaults to. Labelled a post-hoc ablation
  on an exposed cohort.

**Exp 2a: wave utilization screen, existing checkpoint (~1 GPU-h).**
- 64 fresh episodes from `t2_sessions.generate_t2` (`split="final"`, seeds 14,700,000-063),
  two governed code requests each, contexts <= 512 tokens, 32-token completions (raised to
  64 only if the competence pilot shows the microprograms do not fit; budget recomputed).
- Five arms, all given the identical correct live ledger:
  `base`; `prose` (oracle current-rule restatement); `fixed_bias` (fixed β=2 peak-normalised
  bias on the known governing spans every step; a fixed-bias baseline in the PASTA/SpotLight
  family, NOT a reproduction of published SpotLight); `wave` (w0-ce.pt continuous field);
  `wave_where_shuffled` (at every step the controller computes its field on the arm's own
  prefix exactly as `wave` does, then the bias values are permuted across ALL P prompt
  positions by a fixed per-episode permutation, preserving the bias-value multiset and the
  scalar gain at that step; this is the existing W0 K-perm ablation, `scripts/w0_gates.py:79`,
  applied at evaluation: removes WHERE, keeps WHEN and dose). No sixth arm: the PASS decision
  needs only these three contrasts.
- Registration freezes which two of the generator's scheduled requests are used per episode
  (`t2_sessions.py:123` schedules more), preserving comment-rule coverage, and the three
  executable input pairs per work (`score_work` at `t2_runner.py:65` currently tests one).
- Score per episode: joint functional-and-adherent success (all opportunities adherent AND
  reference tests pass on the 3 frozen inputs via `wave_ref.py`), with the fixed comment
  checker; execution through the existing `score_work` path (synthetic inputs only).
- Primary estimand: per-episode binary joint success; contrasts wave vs prose, wave vs
  fixed_bias, wave vs wave_where_shuffled; exact McNemar, Holm over 3. Secondary: mean
  adherence with paired bootstrap interval; parse rate; paired-broken works as excess over base
  (prospective rule: <= 5% of works; note the original seal's 21/408 = 5.15% would fail it).
- Exhaustive readings: PASS = all three contrasts positive at Holm-adjusted p <= .05 AND the
  breakage limit holds (excess paired-broken <= 5% of works) → Exp 2b. NOT-DEMONSTRATED-WHERE =
  wave vs where_shuffled not positive → "spatial contribution not demonstrated"; method claim
  not advanced; no further wave spend. NOT-DEMONSTRATED-BASELINE = wave not above prose or
  fixed_bias → "advantage over the tested baselines not demonstrated"; method claim not
  advanced; no further wave spend. Any other pattern = INSUFFICIENT EVIDENCE, published as
  descriptive with intervals; no further wave spend. No causal explanation is inferred from a
  nonsignificant contrast. Two-sided p and intervals are always reported so demonstrated harm
  is visible and is labelled as harm, never as inconclusive.
- Competence-harm disclosure travels with every mention of w0-ce: MMLU 48.05 -> 45.83
  (175 degradations / 57 improvements), GSM8K noninferiority failed.

**Exp 2b (only on PASS): replication (~1 GPU-h).** Retrain w0-ce with seeds 1 and 2 (`SEED`
env controlling `torch.manual_seed` at `w0_train.py:109/172/189` AND the shuffle generator at
:196; compare tensors, not file hashes, against `w0-ce.pt`); same 64 episodes and arms.
PASS requires each seed to reproduce all three contrasts. No LoRA arm in this pass: a fair
LoRA protocol (matched budget, seeds, dev-selection allowance, objective) is its own
registration; until then the card states "no fine-tuning baseline" and makes no
superiority claim over adapters (check49 already shows removable adapters can carry SET).

**Exp 3: MemoryCode-derived automatic-maintenance screen (CPU contract first; ~1 GPU-h).**
- 3a (CPU, 1-2 days, no GPU): vendor github.com/Cohere-Labs-Community/MemoryCode into
  `vendor/memorycode`, pin sha in `data/bench/pins-manifest.json`. Write
  `results/memorycode-derived/CONTRACT.md` before any GPU spend, fixing: native prompt
  format vs the derived chat rendering (mentor→user, mentee→assistant; prior mentee answers
  supplied from the dataset, not generated); session/query boundaries; eviction = drop all
  sessions before the current one from the prompt (text truncation, explicitly NOT the
  Multi-IF positional-eviction runner, and named as such); candidate-sentence extraction from
  raw history independent of labels; label isolation (only `oracle` reads applicability /
  update labels); common budget accounting E=256 tokens including header and bullets with
  fixed packing/ordering/overflow rules; split by dialogue template family (not item id);
  checker qualification: for every retained regex family, compliant and violating fixtures
  incl. stale values, conflicting instructions, required text inside strings/comments,
  malformed code; convention compliance is the outcome, functional correctness is neither
  measured nor claimed (no code execution). The contract also maps the FOCUS-3 runtime onto
  ordinary coding conversations: `Runtime.task` starts as `None` and task selection recognizes
  "Work on task A"-style phrases only, so ordinary instructions get scope `None` and are
  rejected by admission (`src/stencil/focus3.py:84,105,496`), and messages with more than four
  sentences are skipped (`focus3.py:303`). Define a label-independent initial scope (one
  default task scope per dialogue), sentence-window handling for long messages, and a
  non-vacuous lifecycle replay check: on the 16 setup dialogues the `auto` arm must admit at
  least one instruction and apply at least one update, else the adapter is INACTIVE and the
  screen does not launch. `tests/test_memorycode.py` covers all of it.
- 3b competence qualification (16 setup items, ~15 GPU-min): `history` arm all-applicable
  compliance >= 6/16 on 1.7B; retention headroom (`oracle` − `history`) reported separately,
  not gated. If 1.7B fails, one retry on Qwen3-4B with the same four arms (no controller arm
  exists in Exp 3, so the 2048-vs-2560 hidden-size mismatch does not arise); else INELIGIBLE,
  64 never opened.
- 3c screen (64 items, ~1 GPU-h): arms `history`, `restate_all` (every instruction seen,
  newest-first, packed to E), `auto` (frozen admission + relation-v2 lifecycle policy from
  `src/stencil/focus3.py` run on CPU over the dialogue; live set rendered identically),
  `oracle` (label-derived live set, same renderer and budget). Primary: `auto` vs
  `restate_all`, exact McNemar with two-sided p and interval. Descriptive: `auto` vs `oracle`,
  false admissions, missed updates, stale-rule executions, tokens.
- Power, stated: N=64 detects only large effects (8 wins/0 losses one-sided p=.0039; 4/0
  p=.0625). This is a SCREEN: a positive triggers a registered N=256 follow-up with power
  computed by the repo's finite-enumeration method; a null is "not demonstrated at N=64".
- Readings: the shipping criterion uses the conservative paired interval from
  results/astra-research-blockers.md:199 (separate 97.5% Clopper-Pearson intervals for b/N and
  c/N, difference by union bound). Ship `auto` if its lower bound on (auto − restate_all) is
  above −2 points AND false admissions are reported; otherwise ship restate_all / role rule and
  publish the admission error table. At N=64 even perfect agreement cannot establish matching
  within 2 points (0.98^64 = 27%), so a "ship auto" outcome is labelled a screen-level decision
  pending the N=256 follow-up.

Not in this pass and why: cache-column gated wave reopen (validity, not novelty; needs a
budget-constrained actuator); BM25 / wave-as-retriever arms (different capability; would
need their own policy definitions); LoRA (own registration); any 30B run.

### C. Publication, in three releases

- **Release 0, the classifier (CPU, first week, public, `bmarti44/` namespace).** The
  sentence classifier in `data/classifier/model/ft` (BAAI/bge-small-en-v1.5 fine-tune, MIT
  base, 3 epochs on 20,054 rows; held-out 89.1% on 1,093 sentences, hard subset 84.2%;
  per-class precision/recall in `metrics.json`) is the one trained model with a public-benchmark
  number, and it is published as-is, before any experiment. Name (descriptive, Brian may
  rename): **`bmarti44/assistant-memory-sentence-classifier`**, card title "Assistant Memory
  Sentence Classifier: does the assistant need to remember this sentence? (rule / fact / none,
  bge-small-en-v1.5 fine-tune)". Format: convert encoder + `head.pt` into one standard
  `BertForSequenceClassification` checkpoint (safetensors, `id2label` rule/fact/none) so
  `pipeline("text-classification")` works with no custom code; the conversion is accepted only
  when it reproduces the original head's argmax on all 1,093 held-out sentences and max-abs
  logit drift is logged (`scripts/export_classifier_hf.py`, `tests/test_export_classifier.py`).
  Card contents: the LABELS.md label spec and three-scope rule; data lineage (kimi-k3 authored,
  sol/Opus enriched, fable-validation author-disjoint) and the two contamination incidents with
  their remediation; the Multi-IF retention numbers stated honestly (clf pin+echo 59.2 vs
  role/recency rule 60.5: the parameter-free rule beat it at matched columns); CPU inference
  example; intended use (write-time selector for reminder/retention, not a safety filter);
  license MIT (matches the base) unless the inventory says otherwise. Push gate: every number on
  the card grep-checked against `metrics.json` / the Multi-IF RESULTS; `huggingface-cli whoami`
  must show `bmarti44` (if not logged in, the one thing Brian must do is `! huggingface-cli
  login`); dry-run file listing, then push. Card is updated (not re-created) after Exp 1 with
  the echo-only numbers.
- **Release 1, evidence (CPU, after the hygiene step):** HF dataset repos
  `stencil-synthetic-sessions` (generators `t2_sessions.py`, `qwen_task.py`, seed manifests,
  sha256 of rendered texts) and `stencil-instruction-salience` (published as a labelled
  RECONSTRUCTION with per-row provenance and the manifest-count discrepancy stated; LLM
  authorship per file; contamination incidents; BFCL lineage from `LEDGER-PLAN.md:634`).
  A model repo `bmarti44/stencil-research-artifacts` holding w0-ce.pt, w0-proxy.pt,
  s3-selector-weights.pt and the relations-v2 seed0 lifecycle classifier (the sentence
  classifier lives only in Release 0 and is linked), with a card whose evidence tables cite
  RESULTS.md files, carry the negative-results table, the C2 result, the Multi-IF safety-gate
  failure as recorded, the w0-ce MMLU/GSM8K harm, and an explicit "research backend numbers;
  no runtime package is qualified" statement.
- **Release 2, the useful published model (after Exp 1 and Exp 3):** the shortest path is
  decided by Exp 1. If pins are dispensable (the likely outcome at a 2-point margin), Release 2
  is a TEXT-ONLY package `stencil-reminder`: the classifier encoder + head (the one trained
  model with a public-benchmark number), the role rule as the zero-parameter default, and the
  FOCUS-3 lifecycle renderer, exposed as a pure-Python pre-processor that rewrites the prompt
  before any HF model call. It needs no attention patching, no model-specific hooks, works with
  any chat model, and is qualified by CPU unit tests plus the Exp 1 / Exp 3 RESULTS.md numbers
  it cites. If pins earn their place, the positional-eviction runner is added as an optional
  Qwen3-only backend, requalified with pre-query eviction parity tests on the current
  transformers major version. The W0 controller ships only as a research artifact in Release 1
  unless Exp 2a passes. No research number is attributed to the package until the matching
  qualification exists; an executable example from a clean environment is the release gate.
- License: first an inventory (`LICENSE-INVENTORY.md`: repo code, vendored bfcl/ifbench,
  BAAI-derived encoder, Qwen trunk, MemoryCode, contributed data) with owner and terms per
  component; then Brian decides. Apache-2.0 for Brian-owned code is the recommendation.
- Repo hygiene (explicit pathspecs only, per AGENTS.md:33): first settle the uncommitted
  source-replay four-file change (default: park on branch `source-replay-prep-v2`, see open
  decisions); `git add -f` the untracked evidence list above and the GPT-2 JSON/txt plus
  `cache-v8-s0-ckpt.pt` and `base-v4-s0-ckpt.pt` (15.8 MB); `git add
  results/focus-mechanism-composition-astra.md scripts/focus_check32.py`; gitignore
  `models/qwen3-30b-a3b-hf/`, `data/classifier/model/focus-lora-4b/`,
  `data/classifier/model/**/encoder/*.safetensors`, `data/classifier/model/**/head.safetensors`,
  `relations-seed*/`, `relations/dev_predictions.npz`; `pyproject.toml` gains
  `testpaths = ["tests"]`.
- **Code cleanup, all of it (Brian, rev 6): behaviour-preserving, in two phases.**
  Inventory today: 77 modules in `src/stencil`, 187 scripts, 25 tools, 144 test files,
  `deploy/stencil_wave`; ruff 1,501 findings (404 auto-fixable), `tools/` excluded from lint.
  - Safety rail for every cleanup commit: tag `pre-cleanup-2026-09-11` first so hash-bound
    audits (`w-seal.json`, `freeze.json` code hashes) can always check out the exact sealed
    code; no cleanup commit may change the output of a scorer or generator, verified by
    (a) the full `uv run pytest -q` (allowed here because no wrapper is running), (b) a CPU
    re-score check: `_score_fields` over the saved Multi-IF 909 records reproduces the recorded
    pooled rates, `t2_runner.score_work` over the wave dev fixtures reproduces the saved
    adherence rows, `generate_t2(split="final", seed=13600000)` text sha256 unchanged, and
    (c) the determinism marker tests. A cleanup commit that fails any of these is reverted,
    not patched forward.
  - Phase 1 (before Exp 0; ~1 day): `src/stencil`, `tests/`, `tools/`, `pyproject.toml`,
    `Makefile`. `ruff check --fix` then manual fixes for the remaining findings; `ruff format`;
    drop `extend-exclude = ["tools"]`; every import-time side effect removed (extend
    `tests/test_no_side_effect_imports.py` to all of `scripts/` and `tools/`); duplicated
    helpers that exist in two or more places (cluster stats, ledger rendering, scoring) moved
    into `src/stencil` with the copies deleted, only where the copies are byte-identical in
    behaviour per the re-score check; type/lint-clean `make gate-0` = `pytest -q` +
    `ruff check .` + `ruff format --check .` passing bare from the repo root.
  - Phase 2 (CPU time while GPU runs execute; done before the Release 1 push; ~2 days):
    `scripts/` and `deploy/`. Each of the 187 scripts is classified LIVE (named by a README
    reproduce command, a RESULTS.md, or this plan) or CLOSED (belongs to a closed program:
    GPT-2 toy phase, SC1, FOCUS-1/2, source-replay banks, check-NN quick checks). CLOSED
    scripts are `git mv`'d to `archive/scripts/` with `archive/scripts/MAP.md` (script → the
    result file it produced), lint-fixed mechanically only. LIVE scripts get the full
    treatment: lint clean, `main()` guard, argparse help, a one-line docstring naming the
    result they produce, and are listed in `README.md`'s repo map. `deploy/stencil_wave/`
    is cleaned or archived depending on Release 2's backend decision (archived if pins are
    dispensable). AGENTS.md pointers to absent files (PLAN.md, plan/PROTOCOL.md) are fixed to
    point at this plan's process rules once they are copied to `plan/PROTOCOL.md`.
  - Not done: rewriting working code for style, adding type annotations everywhere, or
    changing any registered numeric path. The cleanup is judged by "gate-0 passes bare and
    every LIVE script runs `--help`", not by aesthetics.
- README rewrite: delete the W3 bullet (lines 144-148) and keep a one-line pointer to the W3a
  qualified positive and the W3b readout failure; collapse FOCUS-3 v4-v8 to one line; replace
  "every amplification variant ... closed with data" with per-recipe wording; correct the
  deficit-gated result's dataset; new order = retention headline with C2 and Exp 1 → "correct
  request-time restatement is the baseline to beat" → wave as a utilization result with its
  competence-harm line → negatives table → boundaries → repo map with one reproduce command per result.

### D. Process rules (replace the archived protocol for this program; 10 rules)

1. One registration per result, short but SUFFICIENT to implement without new scientific
   choices: data lineage, complete arm definitions, frozen selection/packing rules,
   missingness and timeout handling, intervention budget, artifact schema, stopping rule,
   unit, exact test, N, measured cost, exhaustive readings. One implementation review, one
   result audit. A changed intervention or scorer gets a focused review; nothing else does.
2. Instrument bugs (checker, harness, tooling) are fixed and re-run with a one-line
   disclosure and do not consume any development budget. Policy failures (false admissions,
   refits, threshold changes, model selection) count against a registered development budget
   of at most two revisions per program; the third is a stop.
3. Every result reports the failed-criterion / demonstrated-harm / insufficient-evidence /
   equivalence distinction explicitly, with two-sided p and an interval. "Missed by one item"
   is reported as insufficient evidence only when the interval covers the gate; a
   demonstrated adverse effect is never relabelled inconclusive.
4. Kill and safety rules are excess-over-baseline at matched n, never absolute integer
   clauses; operational eligibility, missingness, efficacy and harm are separate columns.
5. Construction defects are repaired BEFORE the evaluation freeze, with disclosure and
   preserved construct/coverage (the accepted source-replay-preparation-v2 bounded-correction
   rule is the template); sealed outcomes after the freeze are untouchable. An ancillary
   arm's failure never vetoes reporting a complete prespecified primary pair.
6. GPU launches require the Exp 0 pilot's measured budget in the registration; budget
   exhaustion is recorded INCOMPLETE, never rescued.
7. One `results/<name>/RESULTS.md` per result; reviews under `results/reviews/`; no new
   root-level review markdown; per-item records saved as they complete.
8. A claim enters README only from a RESULTS.md with a p-value and interval, or an explicit
   "descriptive" label, stating n, p and the arm it lost to. A reviewer score is never evidence of efficacy.
9. Autonomous execution (Brian, rev 6). The orchestrator runs the execution order end to end
   without blocking questions. The only interrupts are: an HF login that is missing, a push to
   the GitHub remote (never done without Brian), stopping a process this session did not
   launch, and a change to the registered arms or estimands (which is a new registration, not
   a question). Every other choice is made by the most conservative reading, recorded in
   `plan/LEDGER.md`, and flagged in the next result audit. Progress is written ahead to the
   ledger before every long step so a context reset resumes from its STATE line.
10. Getting unstuck with Astra. "Stuck" is defined mechanically: two failed attempts at the
    same test/bug, a registration choice the plan does not cover, a result whose reading is
    not in the exhaustive list, or a review finding the orchestrator cannot refute in one
    pass. Then, and only then, invoke Astra read-only:
    `codex exec --skip-git-repo-check -C /home/bmarti44/stencil-llm -s read-only -m gpt-6-astra
    -c 'model_reasoning_effort="xhigh"' < prompt.md > results/reviews/<date>-<topic>-astra.md`,
    launched detached (`setsid nohup`, `.done` sentinel, Monitor until-loop) so the 10-minute
    Bash timeout cannot kill it. The prompt states the stuck condition, the two attempts made,
    the files involved, and forbids reading `data/bench/`. Astra's answer is adopted only if it
    adds no arm, model, benchmark or review stage; otherwise it is recorded as declined with
    one line of reason. Astra also performs the one implementation review and one result
    audit per registration (rule 1); Opus at maximum effort is the substitute when codex is
    unavailable, recorded in the review header per AGENTS.md.

### E. GPU coordination: share by default, lock only when it does not fit (rev 6)

- Sizing, which decides everything: the GB10 has 119 GB unified memory. Every Stencil run in
  this plan is Qwen3-1.7B (bf16 weights 3.4 GB) at contexts <= 4,096 tokens; the manual
  attention path's transient fp32 tensors at T=4,096 are 1.0 GiB per layer for scores and
  2.3 GiB for logits, so the expected process peak is 8-15 GB (Exp 0 measures it). The peer's
  Ouro-2.6B bf16 work is ~6-10 GB. Both fit together with tens of GB to spare, so the default
  is CONCURRENT use. Bitwise determinism is per-process (`torch.use_deterministic_algorithms`
  + fixed cuBLAS workspace, `determinism.py:13-18`); a co-resident process changes throughput,
  not results. Exp 0 checks this once: the 8-dev-session qualification run is repeated with
  the peer resident (if it is) and must be bitwise identical to the solo run.
- Reservation file, not an exclusive lock: `tools/gpu_reserve.sh <name> <est-minutes>
  <peak-gb> -- <cmd>` (~15 lines) appends `{name, pid, started, eta, peak_gb}` to
  `/home/bmarti44/.gb10-gpu.reservations` under `flock`, appends the pid to
  `.stencil-owned-pids`, removes its line on exit, and refuses to launch when
  `free memory < own peak_gb + sum(other reservations' peak_gb) + 8 GB headroom`. It takes the
  exclusive `flock -n` on `/home/bmarti44/.gb10-gpu.lock` only when called with `--exclusive`,
  which this plan never needs (no 30B, nothing > 40 GB). Offered to the peer as-is; if they do
  not adopt it, their processes are read from `nvidia-smi` with an assumed 12 GB peak.
- Guard change (`src/stencil/determinism.py:34`, `assert_gpu_free_or_owned`): keep the
  exclusive semantics as the default; add shared mode when `STENCIL_GPU_SHARE=1`: foreign pids
  are allowed if they are all listed in the reservations file or in
  `STENCIL_GPU_FOREIGN_PIDS`, and the memory rule above holds. Nothing else changes.
- Etiquette with "looped-transformer": message before any run > 30 min with its peak_gb and
  ETA, and when it ends; message immediately on any OOM either side (the OOM side retries
  after the other finishes; no first-come dispute); chunk runs <= 50 min; never signal a
  foreign process; no `nvidia-smi --gpu-reset`; one Stencil GPU process at a time; contexts
  <= 4,096 tokens.
- Timing budgets are measured under whatever load is present; the pilot summary records the
  co-resident processes, and every registration carries a 1.5x factor on the pilot's
  seconds/item so contention never turns a run into INCOMPLETE.
- Enforceable stopping: per work-arm records saved as they complete; a run stops STARTING new
  items when its reservation has 5 minutes left; `--deadline` is a per-item generation cap,
  not the reservation.

### F. Verification

- Exp 0: `uv run pytest -q tests/test_t2_runner_comment.py tests/test_wave.py
  tests/test_wave_ref.py tests/test_wave_runner_qualification.py`; `python -c "import
  scripts.w0_train"` loads no model; `results/timing-pilot/summary.json` lists tok/s,
  seconds/item and peak memory per arm family at max length; the comment-checker
  qualification note is appended to `results/internal-wave-report.md` (one paragraph).
- Exp 1: `uv run pytest -q tests/test_multiif_evict.py tests/test_multiif_echo_only.py`
  (keep=[] arm, role budget accounting incl. header, schema 2, source selection determinism);
  compatibility replay 8/8 identical or documented regeneration; `--summarize` prints D1/D2/D3
  with bootstrap intervals, sign tests, discordant counts, safety excess, n=128 sources;
  manifest with sha256 of every record.
- Exp 2a/2b: `scripts/w_screen.py --arms base --limit 2` smoke; `results/wave-screen/RESULTS.md`
  with per-arm joint success, McNemar/Holm and two-sided p, intervals, per-type table with the
  fixed comment checker, breakage as excess, the verdict string from the exhaustive readings;
  seed-block exclusion test asserts no 13.6M or dev seeds in the episode manifest.
- Exp 3: `uv run pytest -q tests/test_memorycode.py` (rendering, label isolation, packing and
  overflow, checker fixtures per family, `auto` determinism); `CONTRACT.md` reviewed before the
  GPU registration; `results/memorycode-derived/setup/summary.json` with the eligibility line;
  `results/memorycode-derived/64/RESULTS.md` with McNemar table, intervals, admission error table.
- Publication: dataset/model cards have every number grep-checked against RESULTS.md; the
  `LICENSE-INVENTORY.md` exists before any push; `push_to_hub.py` dry-run lists every file;
  `--push` only with Brian's go.
- Hygiene: `git status --short | grep '^??'` empty under models/ and data/classifier/model/;
  `git ls-files` shows every force-added file; `git diff --check`; README contains no
  "4×10⁻¹²" or "73/73"; `pytest` (bare) collects only tests/.
- Release 0: `uv run pytest -q tests/test_export_classifier.py` (argmax identity on 1,093
  held-out sentences, max-abs logit drift logged); `python -c "from transformers import
  pipeline; print(pipeline('text-classification', model='<local export>')('From now on reply
  in French.'))"` prints `rule`; card numbers grep-checked; `huggingface-cli whoami` =
  bmarti44; after push, a clean-environment `pipeline(..., model=
  'bmarti44/assistant-memory-sentence-classifier')` call reproduces the same label.
- Cleanup: `make gate-0` passes bare from the repo root after Phase 1 (`pytest -q`,
  `ruff check .`, `ruff format --check .`, no `extend-exclude`); the re-score check script
  (`scripts/check_cleanup_invariants.py`) reports Multi-IF pooled rates, wave fixture
  adherence rows and the `generate_t2` sha256 unchanged against `pre-cleanup-2026-09-11`;
  after Phase 2, every script under `scripts/` runs `--help` with exit 0 and
  `archive/scripts/MAP.md` names a result file for every archived script.
- GPU sharing: `tools/gpu_reserve.sh` smoke-invoked with `bash -u` on a `sleep 1` command
  (reservation line appears and disappears, pid registered); the Exp 0 pilot summary lists
  co-resident pids and the shared-vs-solo 8-session outputs are bitwise identical.

### Execution order and program stop rule (about two and a half working weeks)

1. Park the source-replay change on its branch; tag `pre-cleanup-2026-09-11`; hygiene
   (force-adds, gitignores, testpaths); cleanup Phase 1 (`src`, `tests`, `tools`); README
   rewrite; copy the three Astra reviews to `results/reviews/` and rules D1-10 to
   `plan/PROTOCOL.md` (CPU, ~2 days).
2. Release 0: export, verify and push `bmarti44/assistant-memory-sentence-classifier`
   (CPU, ~half a day; runs as soon as step 1's hygiene is committed).
3. Exp 0 instrument fixes + pilot + shared-GPU determinism check (CPU + <= 20 GPU-min, ~1 day).
4. Exp 1 (register with measured budget → run → RESULTS.md → audit, ~1 day); update the
   Release 0 card with the echo-only numbers.
5. Exp 2a (register → run → RESULTS.md → audit, ~1 day); Exp 2b only on PASS (~1 day).
6. Exp 3a contract (CPU, 1-2 days) → 3b qualification → 3c screen → RESULTS.md → audit (~1 day).
   Cleanup Phase 2 (`scripts/`, `deploy/`) runs in the CPU gaps of steps 4-6.
7. Release 1 (evidence) once cleanup Phase 2 is committed; Release 2 (`stencil-reminder`) as
   soon as Exp 1 and Exp 3 have RESULTS.md files, whichever way they read (~2 days).

Stop rule for the whole program: after step 5, if Exp 2a is not PASS, the mechanism line
ends and the published model is the text-reminder package with its measured numbers; if Exp 3
does not reach "ship auto", the package defaults to restate-all / role rule and the automatic
maintainer ships as an opt-in with its error table. Either way something useful and honest is
published; no further arms, banks or wave variants are added without a new registration.

### Astra round-1 findings declined, with reasons

- Full LoRA protocol in this pass (finding 6): a fair adapter comparison is its own
  registration; adding it now doubles author-hours without changing the first decision.
- Universal Bonferroni/estimand debates beyond the stated primary (7): the primary is now a
  single binary per-episode estimand with exhaustive readings; secondary metrics are descriptive.
- Requalifying the HF runtime package before any experiment (21-22): moved to Release 2,
  after the science; Release 1 publishes evidence only.
- Native-protocol MemoryCode comparability (14): not claimed; the evaluation is labelled
  "MemoryCode-derived" and its contract is written before GPU spend.
- Repo-wide Ruff cleanup (32): declined in rev 3 as a gate for science; in rev 6 Brian asked
  for the full cleanup, so it is now scheduled (section C) in two phases that never block a
  GPU step and are guarded by the re-score check.

## Decisions resolved by default (rev 6: no blocking questions; Brian can override any line)

- License: `LICENSE-INVENTORY.md` first; then Apache-2.0 for Brian-owned code, MIT for the
  classifier release (its base is MIT). Vendored components keep their own licenses.
- HF namespace: `bmarti44` (Brian, rev 6). The encoder is published: bge-small-en-v1.5 is MIT
  and the card carries the base-model attribution and revision.
- Uncommitted source-replay-preparation-v2 four-file change: parked on branch
  `source-replay-prep-v2` with its pending review noted in the ledger; main stays clean.
- GPU wrapper: yes, proposed to the looped-transformer session as the shared reservation file
  (section E), with concurrent use as the default.
- Still Brian-only: pushing the 215 commits to the GitHub remote, and the HF login token.
