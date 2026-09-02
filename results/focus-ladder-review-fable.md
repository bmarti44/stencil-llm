# Focus ladder (H1/H2/H3) — accuracy review (fable, CPU-only, 2026-09-02)

Reviewed: scratchpad `focus-h1-h2.md` against `results/research-synthesis.md`, `results/research-fable.md`,
`LEDGER-PLAN.md` (LEDGER-KV, KV PROBE v2 VERIFICATION, ROUND 7, RE-SCOPE v2), `scripts/ledger_kv_probe.py`
(current working copy, under coder edit — not touched), `src/stencil/bench.py`, `src/stencil/qwen3.py`,
`src/stencil/ledger.py`, `scripts/ledger_eval.py`, and the on-disk artifact `results/qwen/ledger-kv-probe-v2/`
(20 session records + summary, recomputed here without any model process).

Verdict: the ladder is the right shape (retention first, head existence second, trust-region last) and the
cited numbers are correct. Three findings are HIGH and must be fixed before preregistration: the H2 gate passes
under the global null (448 uncorrected tests), the H3 pilot comparator `pinned_echo` does not exist in the
Multi-IF runner (no eviction regime there), and H1's degeneracy cap (<= 2/20) is failed by the ceiling arm
itself. Everything else is medium/low and mostly cuts.

## 1. Numbers and gates vs artifacts

| Claim in ladder | Artifact | Status |
|---|---|---|
| pinned recovers 0.615 of the gap | v2 summary: (31-15)/(41-15) = 16/26 = 0.6154 | exact |
| 56 aged constraints, 20 sessions | v2: sum n_aged = 56 over sessions 000-019, all 3-turn | exact |
| "pinned+wave(3.0)" degenerates | v2 pinned_wave: 13/20 sessions degenerate, 12 truncations | exact |
| degeneracy "rep4 >= 0.5" | runner: `rep4 > DEGENERATE_REP4` (strict), registered as `truncated or rep4>0.5` | LOW: use the runner's strict form |
| "113/909 Multi-IF ledger runner" | ledger_eval.py REGISTERED_COHORT 909, `--diagnostic-only` 113 | ok |
| H1 gate ">= 0.85 of gap" | R3 in synthesis: ">= 85% ... with zero added truncation" | ladder relaxes to "truncation not above full" — say so |

H1 gate arithmetic (in-job gap of 26/56 assumed): pass needs pinned_echo >= 15 + 0.85*26 = 37.1 -> >= 38/56
(0.679); kill fires at <= 31 + 0.05*26 = 32.3 -> <= 32/56. The band 33-37/56 is undefined. MEDIUM: register the
band as "inconclusive -> pin-only stands" or collapse to one rule. Also: 0.615 is a v2 number at
`--max-new 320`; the current runner default is 512. The reference arms are re-run in the same job, so cite the
in-job gap, never the 0.615 constant, in the H1 gate (LOW, wording).

HIGH (H1 degeneracy cap): the ladder requires "degenerate <= 2/20 sessions", but v2 shows full 7/20, pinned
4/20, evicted 2/20, control 2/20 (degeneracy tracks output length, which tracks passing). The ceiling arm fails
the proposed cap, and a pinned_echo arm that merely equals pinned would fail it. Replace with the ROUND 7 style
already registered for Multi-IF: degenerate sessions and truncations of pinned_echo not above `full` in the
same job (excess-over-reference), which is what "truncation not above full" already says for truncation.

Statistical weight: the H1 metric is 56 paired constraint outcomes clustered in 20 sessions. A 7-constraint
swing separates pass from kill; the session-paired bootstrap (already in the runner for pinned-minus-control)
gives roughly +/-0.15 on a rate difference at n=20. H1 as written is a point-estimate screen. That is fine for
a fast rung, but label it so (falsification-style, like the 113 slice), and reuse
`paired_bootstrap_pinned_minus_control` for pinned_echo-minus-pinned and echo_only-minus-pinned (LOW, reuse).

## 2. H1 echo arm — is it a confound?

Verifier view: `score_row_constraints` (src/stencil/causal_moments.py:193-206) scores the RESPONSE only;
prompt text never reaches the checkers. The echo cannot change the verifier's view. Not a confound there.

Target-blind: in the probe the "focus set" is NOT "the ledger's selected spans" as the ladder says. The probe
pins every aged `Constraint:`-marked span found by `e2.constraint_span_records` (oracle markers in the synthetic
corpus; `keep = all recs with origin_turn < T_last`), with no salience2 selection and no top_k. The echo text
would be those span texts, which never touch `instruction_id_list`/`kwargs`, so target-blind holds in the
registered sense (no verifier access). MEDIUM (wording): say "oracle aged spans" for the probe; on Multi-IF
there are no markers (FIX-ROUND reading (i)) and spans come from salience2 at ~0.88 recall, so the echo arm's
Multi-IF successor is weaker by construction.

Template safety: the span text begins with the literal "Constraint:" and the LAST span of a turn runs to
`<|im_end|>`, so it drags along the corpus boilerplate "Every earlier constraint from this conversation still
applies..." (seen in session 0 turn 2). "Active constraints: Constraint: ... Every earlier constraint ..." is
ugly but harmless to the verifier. The real problem is that it is a SECOND, unregistered template: the
Multi-IF text arm already has a frozen, six-round-verified one — `TEXT_LEDGER_HEADER =
"Earlier user instructions restated verbatim:"` + "- {text}" lines, inserted before the final `<|im_end|>` by
`ledger.text_ledger_context` (src/stencil/ledger.py:27,337-360). HIGH-adjacent (graded MEDIUM because it is a
one-line fix): reuse `text_ledger_context` so H1's echo IS the registered text arm under eviction; otherwise
the H1 result does not transfer to the arm that the 909 actually runs.

Mechanics: the echo is appended inside the last user turn, i.e. after `last_marker`, so `evict_range` and every
`keep` span index are unchanged; `run_arm` takes `ids` per call, so the echo arms only need a second tokenized
context. Compute `constraint_span_records` on the UN-echoed context (the echo contains "Constraint:" and would
otherwise register fresh spans; they would not be aged, so `keep`/`n_aged` are safe, but do it in that order).
The arm dispatch in `run_arm` is by arm-name prefix; `pinned_echo` needs `pins = keep`, `echo_only` needs
`pins = ()` — a two-line addition to the pin selection. Feasible; note the script is being edited (schema 3,
multi-dose arms, max_new 512 default), so H1 arms must be added to `arm_names` and to the summary loop, not
to a stale copy.

Interpretive confound (MEDIUM): pinned_echo differs from pinned in two ways — the constraint is available AND
it is recent (~10-50 tokens from the generation point vs 200-500 for the pinned columns) AND it is represented
twice. So "H1 pass => focus = selection + availability" over-reads: it shows recency/verbatim restatement
closes the gap. The clean text-vs-KV contrast is echo_only vs pinned (same information, different medium);
keep echo_only and phrase the reading on that pair. Family dependence (from the v2 aged set: forbidden_words 7,
keywords 10, case 7, number_words 5 of 56): the echo hands the model the keyword tokens verbatim (helps
keywords:*), and hands it the forbidden words and the mixed-case text verbatim (hurts if parroted). Report
per-family cells; do not let a keyword-family win be read as general.

Horizon: all 20 sessions are 3 turns, max 814 context tokens; the RoPE long-horizon question in LEDGER-KV stays
untested by H1 (LOW, disclose).

## 3. H2 head scan — implementable? right unit?

Plumbing: `_Block.forward` adds `attn_bias.float()` to `att` of shape (b, h, t, T_total). A bias of shape
(h, t, T) or (b, h, t, T) broadcasts with NO change to qwen3.py, passed through the existing `attn_bias={L: ...}`
dict exactly as `run_arm` does today (`bias_hook` is unnecessary for a static bias). Per-head, per-layer
bias is therefore implementable now. Teacher forcing is one forward over context + continuation with the bias
applied only to rows >= continuation start (mask the rows); all continuation logprobs come out of that single
pass. Batching heads along `b` with a (b, h, t, T) bias gives ~8 heads per forward; att is ~100 MB fp32 at
b=8, t=T=450. Cost: 448 (layer, head) x 20 sessions = 8960 forwards, or ~1120 batched, each a ~450-token
prefill — well under 1 GPU-h on this box (v2's 100 full generations took 19.5 min wall-clock). The 1 GPU-h
figure is conservative. OK.

Unit — MEDIUM, change it: "delta-psi 0.02 per head" is a post-softmax quantity; nothing in the current
plumbing produces per-head span mass (`attn_probe` records the head-MEAN mass: `probs[0,:,-1,:][:,pm].sum(-1)
.mean()`, qwen3.py), and the only mass-targeting path (`deficit_gate`) is all-head with a tau target. Getting a
fixed delta-psi per head needs a two-pass scheme plus a per-head probe (an edit to qwen3.py, which re-opens the
hash set). Worse, a fixed delta-psi is not a small fixed perturbation: on a head with natural span mass 0.001
it is a +3-nat bias (20x odds); on a head at 0.30 it is +0.1 nat. It is largest precisely on the
non-contextual heads. The synthesis's R2 specifies the unit as LOGIT units ("alpha on a log grid 0.005-0.05 in
logit units"). Use a fixed pre-softmax bias per head (e.g. b in {0.5, 1.0} nats on the span columns) and
REPORT the realised delta-psi as a side quantity. Drop the "95th pct caps" from the pre-check — that is an R2
deployment detail, not part of the existence question.

Gold continuation — MEDIUM, undefined: the synthetic corpus has no gold last-turn answer, and format
families (title, lowercase, number_sentences, bullets) have no localised "answer tokens". Register the
continuation as the same-session `full`-arm response (already stored as `generated_token_ids` in schema 3) and
the metric as its mean logprob under the pinned cache with vs without the per-head bias; optionally a
constraint-localised sub-metric for the families that have one (keyword tokens, title, postscript marker).
State that whole-response logprob is dominated by fluency, so a head that helps constraint tokens and hurts
fluency nets to ~0.

Gate — HIGH: ">= 8 heads with positive median whose 95% bootstrap CI excludes 0" over 448 uncorrected tests
passes under the global null (expected ~11 heads with a two-sided 95% CI above zero by chance, ~5-6 if only
the positive side is counted, with 20-session bootstrap CIs that are themselves coarse). Fix with either
(a) Holm/BH across the 448, or (b) the R2/Focus-Directions design: select heads on sessions 0-9, confirm on
10-19 with a one-sided test corrected for the number selected, plus a random-head control of the same size
(random heads must not beat the selected set). (b) is cheaper to interpret and matches the cited paper.

## 4. H3 gates vs DIRECTER

DIRECTER (research-fable.md row 7, research-sol.md:47): accept the steered token only if
p_raw(steered top-1) >= beta * p_raw(raw top-1), beta = 0.5; on rejection halve the steered-LAYER set;
fixed-strength variants all lose to the adaptive one; the gate alone rescues PASTA/SpotLight (Fig. 2b).
Ladder: "candidate top-1 raw prob >= 0.5 x raw top-1" — matches. "halve dose / drop a layer pair / emit raw"
is a superset of DIRECTER's backoff (dose halving is Stencil's addition); order must be frozen before the
pilot (sol-web: "Freeze the order and thresholds after development"). The JS budget is sol-web's Wave-TR
addition, not DIRECTER; "dev-calibrated budget" is a tuning loop and the amendment-spiral hazard. MEDIUM:
cut JS for the pilot and keep beta alone (the literature shows beta alone suffices); reintroduce JS only if
beta-only degenerates.

"press-survival >= 5%": undefined in the ladder and only named in the synthesis. Register it: fraction of
generated late-turn tokens on which a nonzero dose was emitted after gating (a press counter, per AGENTS.md
"instrument the exact claim"). LOW.

HIGH (comparator): "late-turn adherence LB > pinned_echo" on a 128-conversation Multi-IF pilot. The Multi-IF
runner (`scripts/ledger_eval.py`) replays FULL history; it has no eviction and no pinning (grep: no `evict` in
the runner; arms = base, text_ledger, neural_ledger, specificity). `pinned_echo` cannot be an arm there
without adding an eviction regime, which is unregistered and re-opens the ROUND 6/7 freeze. The Multi-IF
analogue of pinned_echo under no eviction is `text_ledger`. Either (i) gate the pilot against text_ledger
(honest: on Multi-IF without eviction, "pinned" == "full"), or (ii) register an eviction variant of the
Multi-IF runner as its own rung with its own sol verification before H3 uses it. Do not leave this implicit.

Power (MEDIUM): 128 conversations ~ 256 late turns; the ROUND 3 arithmetic (zero difference at 43 clusters ->
2.33-pt bound) implies a clustered LB > 0 at 128 clusters needs roughly +2 to +2.5 pts observed for an
expected +1 to +3 effect (synthesis/sol-web forecast). Make the pilot's gate a point-estimate + safety
screen with the registered stop rules (truncation excess <= +2, survival >= 5%, no degeneration), and
reserve the clustered LB for the 909, as the re-scope already does.

Sequencing (MEDIUM): "one sealed 909 confirmation under ROUND 7" — the 909 is ALREADY the registered
confirmatory run for the current neural arm (RE-SCOPE v2, P). Adding a Wave-TR arm means either a second
909 or amending the frozen arm set; both re-open verification. Decide this before H3, not after the pilot.

Teacher-forced "CPU gate battery" (LOW): the trust-region rejection rate under teacher forcing excludes the
autoregressive self-reinforcement that the synthesis identifies as the degeneration mechanism (InstABoost
Thm 3.3), so teacher-forced survival OVER-estimates generation survival. It is a sanity check that the gate
math is bitwise-base at beta=1 and that some nonzero dose survives at all; it is not evidence about
degeneration. A 20-session GPU generation smoke (the H1 harness with the H3 controller) answers the real
question for ~20 min.

Falsifier (LOW): "H2 kill AND H3 kill AND H1 pass" is a simplification of the synthesis's four-condition
falsifier (adds mediation and oracle-span UCB < +2). Acceptable for the ladder; say it is the operational
subset, and define what "H1 pass" means under the corrected gate. Note the asymmetric case: H2 pass + H3 kill
is not a falsification under the stated rule — fine, but it then leaves head-selective steering un-tested in
generation; the ladder should say H3 runs on the H2 head set in that case (it does, implicitly).

## 5. Over-engineering — proposed cuts

1. H1: drop the new echo template; reuse `ledger.text_ledger_context`. Drop "<= 2/20"; use "not above full
   in-job". Keep `echo_only` (it is the one clean contrast). Register the 33-37/56 band.
2. H2: drop delta-psi and the 95th-pct caps; fixed logit bias per head, two values at most. Drop per-head
   bootstrap CIs as the gate; use split-half selection + confirmation + random-head control. Batch heads
   along `b`. Nothing in qwen3.py needs to change.
3. H3: drop JS for the pilot; drop the lambda x cap grid to two configs (beta-only with dose {0.5, 1.0} of
   the H2 unit) — the pilot is non-confirmatory and cannot pick a winner anyway; drop the CPU teacher-forced
   battery in favour of the 20-session generation smoke; drop "one sealed 909" from the ladder text and
   point at the RE-SCOPE v2 P registration instead.
4. Whole ladder: every rung already reuses `ledger_kv_probe.py`; make that literal — H1 and the H3 smoke are
   new arm names in `arm_names`, H2 is a separate short script that imports the record schema (no new
   harness). The registered per-record field list (AGENTS.md sealed-jobs rule) should be asserted on a
   2-session smoke before any 20-session run.

## 6. Severity summary

- HIGH: H2 gate has no multiplicity control (passes under the null with 448 tests).
- HIGH: H3 pilot comparator `pinned_echo` does not exist in the Multi-IF runner (no eviction there); use
  text_ledger or register an eviction variant first.
- HIGH: H1 degeneracy cap <= 2/20 is failed by the `full` ceiling (7/20) and by `pinned` (4/20).
- MEDIUM: H1 echo uses a new template instead of the registered `text_ledger_context`; H1 "ledger's selected
  spans" is actually oracle aged spans in the probe; H1 pass/kill band 33-37/56 undefined; pinned_echo
  conflates recency with availability (phrase the reading on echo_only vs pinned).
- MEDIUM: H2 delta-psi unit is unsupported by current plumbing and is head-mass-dependent (use logit units);
  gold continuation undefined (use the stored full-arm response).
- MEDIUM: H3 JS budget is an unfrozen tuning loop; 128-conv LB gate is under-powered for the forecast effect;
  909 sequencing collides with the already-registered confirmatory run.
- LOW: rep4 ">=" vs registered ">"; press-survival undefined; teacher-forced battery over-estimates
  survival; 3-turn/814-token horizon disclosed; cite in-job gap not 0.615.
