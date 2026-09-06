# Composition design review (fable, one round, 2026-09-06)

Scope: `results/focus-mechanism-composition-astra.md` (gpt-6-astra, 2026-09-06) checked against
the artifacts it cites — check40c/40h/40i/42/43b/41b/44b READMEs, RESULTS and summaries, my own
reviews of 40h/40i/42/43/40e and the FOCUS-3 diagnostic, `check43b/magnitude.json` — and against
the freshly landed `results/quick-checks/check40g/README.md` (INVALID) plus its raw
`records.jsonl` and `control-comparison.json`. CPU only; no model launched; no sealed input or
`data/bench` file opened. Every number below was recomputed (exact-enumeration power, cost
arithmetic, CP bound, norms, ratios) or re-read from the cited artifact. Only this file was written.

## 1. Are the cited numbers correct and correctly labeled?

Yes, every number I could trace reproduces, and the diagnostic/registered labels are honest.

| Design claim | Source | Recomputed | Label check |
|---|---|---|---|
| 40c JS 32/32, 0 broken at alpha 3 | 40c README table | 32/32, 0/32 | "exploratory alpha3" — correct; the frozen cell was alpha 2 (25/32), alpha 3 chosen post hoc, later 32/32 on a fresh same-family bank |
| 40i Z: BACK 23/24, SWITCH/CLEAR 24/24, 0 broken; matches 40h-Z | 40i/40h README, my reviews | 23/24, 24/24, 24/24; 40h-Z 23/24/24/24 | correct; both unregistered, arithmetic surface syntax, one pair |
| HOLD does not isolate maintenance | 40h/40i README | stated in both | correct |
| 43b PRODUCT 0/8, both doses; dispatch changed strongly | 43b README | 0/8 at 6.81 and 10.21; 63-78% decode top-8 change | correct; "closed" = operational stop, as the design says |
| 41/41b no reliable dense-neuron control | 41b README | MARGINAL 14/32 JS, 7/32 broken, first token ` moduleId` 23/32 | correct |
| FOCUS-3 diag O 63, C 57, N 29, T 31, C register-exact 38 | my diag review | 63/57/29/31, 38 | correctly labeled ineligible diagnostic |
| 42: every-request 151/192 vs recap 131/192; masking harms facts/constraints | 42 README + review | 151 vs 131 (39/19, p .006); BOTH 78/124 with 15 constraint failures, 41/41 assistant-fact losses | correct, but note this is the descriptive 192-pair coverage diagnostic; the frozen common-sample view is 99 vs 88 on 124 and the formal label is MASKING NOT CLOSED (guard only) |
| 44b NO-GO: overlap P 151/152 = 99.34%, R 151/207 = 72.95% vs 85%; SETUP 2/96; template 0/96 | 44b RESULTS/summary | 0.99342, 0.72947, 2/96, 0/96 | correct; correctly flagged "run's reported result, not an independent review" |
| Norms: full 15.659565; band 7-34 10.208735; alpha-2 band 6.805823 | 43b magnitude.json | 15.659565, 10.208735, 6.805823 | correct |
| 40i cost 21.99 GPU-min for 480 gens incl. load | 40i summary | 1319.3 s | correct (the "9 min" brief figure was wrong, as my 40i review said) |
| 40b review: incompatible installed router APIs | check40b-review-fable.md lines 43-44, 77-78 | stale transformers 5.2.0 in ~/.local returns softmax in slot 0 | correct |
| Power (.25,.05) 82.69%, (.30,.05) 93.56%, (.20,.05) 61.80%, (.15,.05) 33.40%; joint lower bound 65.38% | exact enumeration | 82.69 / 93.56 / 61.80 / 33.40; 1-2(.1731) = 65.38 | correct |
| 0/64 one-sided 95% upper bound 4.57% | 1-.05^(1/64) | 4.573% | correct |
| 6,400 calls; 184,320 tokens; 20,460 s = 5.68 h | arithmetic | 6,400; 184,320; 20,460 s = 5.683 h | correct as conditional arithmetic; realism questioned in section 3 |

Two labeling notes, both low: (i) line 9 still says 40g's "outcome remains pending" — it is now
INVALID and the document must be revised (section 2 below); (ii) line 7 should say the 151/192
figure is the descriptive full-coverage diagnostic and cite 99/88 on the frozen 124 as the
registered view, per the 42 review's overclaim list (c)(i).

## 2. What 40g changes (the actuator is prompt-prior sensitive)

**The facts from the raw 40g records.** The control bias hash is `bda3d63e…`, the identical
tensor used as the JS bias in 40h and 40i (0.75 x 40b `correct` = 1.5 x 40c `selected-bias` =
alpha 3, Frobenius 15.6596). The system message is byte-identical between 40c and 40g
("Answer the request concisely. Default to a code block defining the requested function unless
the user specifies another format…"); the cache-prefix sha256 is the same
(`4f53cda1…`). The only difference is the user sentence:

- 40c/40h/40i/43b form: `For the arithmetic expression EXPR, provide a solution. If writing a function, name it X.`
- 40e/40g form: `Write a zero-argument function named X that returns EXPR.`

On the first form the same tensor is 88/88 at SET from empty history (40c 32/32, 43b sanity 8/8,
40h SET 24/24, 40i SET 24/24). On the second form it is 3/8, with 5/8 clean Python, 0 broken,
while dispatch changed on 69.5% of prefill and 80.4% of decode layer-token observations with
zero consumer mismatches. This is the 43b signature again: routing moved substantially, the
decision did not. The expression values also differ (two-digit vs mixed), so 40g does not by
itself isolate "phrasing", but the phrasing is the only structural change and the direction is
exactly what a prior-strength account predicts: "Write a … function … that returns" fixes the
form and pulls the Python default harder than "provide a solution. If writing a function".

**Consequences for the design (medium, must-fix before implementation).**

1. Section 3's table has no row for what actually happened. Its three branches all presuppose
   that the JS positive control passes in the new harness. Add the fourth, actual branch:
   *"Positive control fails in the new request form → no family evidence either way; the JS
   actuator is certified only for the 40c request form; every profile/edge certificate must be
   indexed by request template (or a registered template distribution), and the actuator is
   diagnostic-only on any request form it has not been certified on."* The nearest existing
   row ("Nothing beyond JS passes → freeze a JS-only experimental actuator") is not adequate,
   because JS itself is now uncertified on the request form closest to natural agentic requests.
2. The profile-library entry already has `cue template` and `supported request kinds` fields
   (section 2, line 43); the certification rule (line 57) must consume them: certification on
   "fresh uncued executable tasks" is not enough when the tasks share one template. Require the
   certification bank to span the request-form distribution the larger test will use, and
   report per-form counts. Otherwise the C arm in section 4 carries an actuator whose measured
   operating envelope (one sentence template, one-line arithmetic bodies) has no overlap with
   the requests it will see ("Requests name artifacts naturally").
3. The dose rule "choose the lowest dose with >=7/8 executable target replies on DEV" (line 55)
   repeats the 40c alpha-2 mistake: alpha 2 was 25/32 on the exploratory screen and 6/32 on the
   fresh bank; alpha 3 was the robust cell. Eight DEV tasks cannot distinguish a dose on the
   edge of the prior from a robust one. Use the lowest dose that clears the bar with margin on
   >=24 DEV tasks across >=2 request forms, or keep alpha 3 and test only downward.

**Correct claim boundary for the skill lever now.** "On Qwen3-30B-A3B (this build), the alpha-3
JS routing bias flips the Python default to executable JavaScript on the 40c open-form
arithmetic request (88/88 SET across four runs) and supports the Z release schedule on that
form (40h/40i, ~23/24 BACK, 24/24 SWITCH/CLEAR, 0 broken). On an explicit 'write a function
that returns' request it flips 3/8 (40g). No other family, dose, request form or body length
is certified; TS is NOT at alpha 3 (40e), SQL/Go are unmeasured (40g INVALID), concept routing
is closed at the tested doses (43b). The lever moves a weak default prior, not a strong one, and
its added value on top of a rendered text cue has never been measured." The last clause is the
one that matters for section 4: text cues alone were 32/32 (40c/40e/41b) on every form tested.

## 3. Is the decisive question right, and is the section 3-4 test fair, powered, benchmark-free?

**The question is right; the arms do not isolate it.** "Does routing plus masking improve
executable work when the same live obligations are already rendered correctly" is the only
question left whose answer changes the ship decision (42 already settled rendering, 40g/43b/40e
settled that the actuator is not general). But:

- **HIGH — C vs R does not isolate the actuator.** C and R run frozen classifiers on their own
  divergent histories ("do not replay C's trace"). Any classifier decision that differs between
  the two histories changes the register, so C-R = (bias + mask) + (register divergence noise).
  With 44b's C at 72.95% recall and supersede recall the dominant FOCUS-3 miss, divergence is
  expected, not hypothetical. The clean contrast is **O vs O_off** (gold events into the
  register in both; bias+mask on vs OFF+no-mask), which differs by the actuator only. That arm
  does not exist in the design. It is also the arm that is *eligible now*: it needs no
  admission classifier, so 44b's NO-GO does not block it. Make O vs O_off the single primary
  test; C becomes a diagnostic arm if a qualified admission candidate appears.
- **HIGH — the token budget is inconsistent with the episode design.** 16 rounds with a 512-token
  episode cap is 32 generated tokens per round on average, and 64 per call, for read/edit/test
  tool calls that must carry file paths, replacement text and JSON framing. A cap breach fails
  the episode for every remaining round. Cap-induced failures will be arm-agnostic, collapse
  final success in all arms toward the floor, and destroy the discordance the power calculation
  assumes. Either measure a DEV pilot's per-round token need and set caps from it, or cut the
  per-episode total cap and keep only the per-call cap.
- **HIGH — the absolute breakage bar (C breakage <=2/64) is unlikely to be meetable by any arm.**
  Breakage includes any malformed tool call, any invalid program, any capped generation, across
  16-32 rounds per episode. 40e's OFF baseline broke 7/32 on single-turn JSON. A FAIL produced
  by an arm-invariant breakage floor says nothing about the actuator. Keep the paired clause
  ("no more than one episode above R") and drop the absolute clause, or pilot it first.
- **MEDIUM — mask/tool asymmetry confounds C (or O) against R.** C masks its own prior code
  bodies; when the agent must edit that code, C has to re-read the file through a tool that R
  can skip, spending tokens and rounds. Under the caps above this converts the mask into an
  episode-failure mechanism. At minimum record per-arm tool-call and token counts as a
  pre-registered covariate, and give the mask policy a DEV pilot with a stale/wrong-skill
  witness before the bank is opened.
- **MEDIUM — internal contradiction in the mask policy** (line 30): "Never mask … tool
  observations" and, two sentences later, "Only typed code/tool-output spans qualify." Resolve
  before implementation: the 40i certificate covers assistant code bodies only.
- **MEDIUM — priors say the actuator's channel is already closed by the C-arm design.** C
  renders the family cue in text ("Family cues are rendered in the composed arm too"). Text
  cues are 32/32 at SET on every form tested; 40g shows the bias is weaker than a mild prompt
  prior. So the bias can add nothing measurable at SET; the only remaining channel is the mask
  against retired-epoch imitation, and 42 showed masking is dominated by rendering on the one
  family where both were measured (A 99 vs BOTH 78 with 15 constraint failures). The design's
  own reading "C beats N but not R → cut actuator" is therefore the expected outcome. A 6 GPU-h
  run to confirm the expected null is not the quick-test-first order: run the ~20-minute
  version first (below).
- **MEDIUM — N is a co-primary that is already known.** C > N is established on two banks
  (FOCUS-3 diag 57 vs 29; check42 A vs neither 151 vs 0). Spending half the alpha and a fifth of
  the GPU budget on it buys nothing; drop N or run it on a 16-episode subset as a sanity check
  and give the actuator contrast the full alpha .05.
- **LOW — power is stated honestly** ("powered for a large benefit"). With the expected
  discordance for the actuator contrast closer to (.10,.10) than (.25,.05), power is well under
  33%; the design should say that a null here is uninformative below a ~15-20 point effect.
- **LOW — post hoc risks are mostly closed** (pre-written reading, frozen witnesses, episode as
  unit, exact tests, Bonferroni, seeds pinned, no rescue). Two remaining: "final success = hidden
  integration tests plus all still-live obligations" needs a frozen per-obligation checker list
  per episode, and "wrong skill … checked by parser/compiler plus task context" needs a frozen
  per-round gold family label (the event oracle can supply it; say so).
- **Benchmark-free:** yes. All banks are fresh-authored, lineage line present (line 45), no
  data/bench input at any stage. Correct.

**Cost realism (<=6 GPU-h).** The 20,460 s figure reproduces but rests on 15 tok/s decode
(consistent with 40i's 29.5 tokens/1.92 s on ~600-token contexts) and a 0.3 s per-call overhead
for prefill of multi-file repos plus tool outputs at 16-32 rounds with a sustained router hook
and a 2D key mask on every forward, all unmeasured. The design admits this. Two harder
problems: (a) the 2,700 s allowance is meant to cover load (374 s), a 16/32-round DEV pilot and
"profile qualification"; one family certification by section 2's own rule (24-task competence
+ 4 arms + Z/Zc/S transitions) is a 40e+40i-sized run, ~35 GPU-min, so any family beyond JS —
and JS recertification on the new request forms, which 40g now requires — does not fit;
budget it separately (~1-1.5 GPU-h). (b) Authoring 64 independent multi-file repos with hidden
integration tests, discriminating witnesses and gold event schedules across four domains in
days 1-4, alongside the implementation, is the actual bottleneck; the FOCUS-3 bank needed eight
revisions. Neither is a GPU-hour problem, but both make the "one week" framing unrealistic.

**Cheaper first test of the decisive question (~20 GPU-min, fits Brian's quick-test rule).**
Fresh arithmetic-style or short-function bank, two request forms (40c and 40e), 24 tasks each,
empty history: arms {text cue only, text cue + alpha-3 bias, bias only, OFF}. If "text + bias"
does not exceed "text" on executable target success by >=4/24 on either form (paired), the
bias has no incremental value over rendered cues at SET and the larger test's actuator arm
should be reduced to mask-only. Then, if warranted, a 40i-style Z schedule with the family cue
rendered at every step: Z-with-cue vs cue-only (no bias, no mask) at BACK/CLEAR. That is the
whole decisive question at 1/15 the cost.

## 4. Over-engineered relative to the evidence — cut from the first implementation

- **D, task-type classifier head** (lines 24-26, 65): no data, no training, no DEV split exists;
  explicit entry sets the family; a one-shot exception is a request-local field. Cut; the
  register's family field is the input to F.
- **Discovery/clustering** (lines 61-63): motivated by two papers, no in-repo evidence, no
  family beyond JS has passed. Cut.
- **Multi-family profile library, norm matching, Holm across families, per-edge certificates**
  (lines 41-59): there is exactly one certified family on one template. Keep the JS tensor as
  a frozen experimental flag on the 40c form; write the library schema only as far as needed to
  tag that one profile with its template and hashes.
- **`reinstates` relation and generalized precedence** (B, C): FOCUS-3 v8 has supersedes,
  cancels, completes; supersede recall is the open problem. Do not add a fourth relation before
  the third works; precedence beyond the sort-specific consumer "needs its own fixtures" by the
  design's own admission.
- **Prefix caching, cross-session sharing, cache reload replay, deep-fork** (line 37, H):
  serving concerns; the test runs fresh episodes with per-session state. Cut; keep the 40i
  research path (persistent 2D keep mask, absolute positions).
- **HF repository packaging** (line 17): premature.
- **Fact-preserving mask extension** (line 30-31): see section 5.
- **Five arms**: as argued, O vs O_off primary; T as the text-oracle comparator; R and C only if
  a qualified admission candidate exists; N as a small sanity subset.

Keep: explicit-entry register (task family + obligations, versions, retire-by-mask never delete);
every-request renderer with request-kind matching (42's B lesson); the 40i JS bias + whole-body
mask behind a flag; one-generate loop with `finally` hook restore; same-run per-round journal
with dry-asserted fields (AGENTS.md rule); fail-safe abstention = OFF + render only.

## 5. Fact-preserving mask: keep 40i's whole-code-body mask in v1

Do not include the extension. Reasons: (i) the only certificate that exists is for whole-body
eviction of assistant code turns (40h/40i, 216 mask events audited); (ii) deciding which spans
hold an "unresolved needed fact" is a relevance prediction, which the same paragraph forbids
("future relevance is never predicted by a salience head") — the policy is internally
inconsistent; (iii) 42 showed masking's harm is fact loss (BOTH 41/41 assistant-fact losses),
and the design already has the right remedy in E: durable facts and artifact references live in
the register and are re-rendered every request, so they never depend on masked KV. Ship that:
mask assistant code bodies only, never tool observations or user turns, and carry facts through
the register. If a body must stay visible, the correct v1 behavior is the design's fallback
(disable that transition's bias/mask pair, render only, record it), not partial-span masking.
Test the whole-body policy on the DEV pilot with a fact-survival probe before the bank opens.

## 6. Findings (graded)

- HIGH: C vs R does not isolate the actuator (classifier divergence); the eligible-now and
  clean contrast is O vs O_off, which the design lacks.
- HIGH: per-episode token caps (512/16 rounds, 768/32) are incompatible with tool-using rounds
  and will produce arm-agnostic cap failures that void the power calculation.
- HIGH: absolute breakage <=2/64 is almost certainly unmeetable by any arm over 16-32 tool
  rounds; a FAIL on it is uninformative.
- MEDIUM: section 3 lacks the actual 40g branch; certificates must be indexed by request form;
  the JS actuator is uncertified on the request form the larger test will use.
- MEDIUM: "lowest dose with 7/8 on DEV" repeats the 40c alpha-2 selection error.
- MEDIUM: mask/tool re-read asymmetry confounds the actuator contrast under the caps.
- MEDIUM: mask policy contradicts itself on tool-output spans.
- MEDIUM: the composed arm renders the family cue, and text cues saturate SET (32/32); the
  expected C-R effect is ~0; run the ~20-minute text-vs-text+bias test first.
- MEDIUM: N as co-primary wastes alpha and GPU on a known result.
- MEDIUM: certification/recertification GPU cost and 64-repo authoring do not fit the stated
  2,700 s allowance or the one-week window; the 5.68 h covers the five-arm run only.
- LOW: line 9 "40g pending" is stale; line 7 should cite 99/88 (124) as the frozen 42 view.
- LOW: power realism note; per-obligation checkers and per-round gold family labels should be
  named as frozen artifacts.
- LOW: fact-preserving mask — exclude from v1 (section 5).

Verdict: the evidence base is cited accurately and every number reproduces; the design's
decisive question is the right one; the proposed test as written cannot answer it (arm
structure, caps, breakage bar) and is not launchable this week (44b NO-GO, uncertified JS
actuator on the new request form). Reduce to: explicit-entry register + every-request render
now; a 20-minute text-vs-text+bias check; then, if the bias earns it, an O vs O_off run with
piloted caps and a paired-only breakage bar.
