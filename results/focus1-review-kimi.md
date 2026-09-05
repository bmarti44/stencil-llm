# FOCUS-1 draft review — kimi-k3 (2026-09-04)

**File to write: `results/focus1-review-kimi.md`** (content below; CPU-only review, no repo access was available to me — everything relied on is pasted in the brief).

```markdown
# FOCUS-1 DRAFT v1 — cross-model review (kimi-k3, 2026-09-04)

Reviewer: kimi-k3. Scope: FOCUS-1 DRAFT v1 (as pasted), focus1-harness brief, astra-drift-assessment,
astra-path summaries, quick-check 30. HARD RULES honored: no shell, no model/GPU, no repo edits; this
file is the only output.

## What I could NOT check (explicit)
- No shell/repo access: all references below are to paragraphs of the pasted draft, not repo file:line.
- `scripts/function_vectors.py` / `src/stencil/function_vectors.py`: that `mean_difference` computes fp32
  final-prompt-token mean differences at layer INPUT, and `make_residual_hook` injects at the same
  layer-input/last position with OFF/alpha-0 identity. A layer off-by-one here would silently change the
  science; harness fixtures must prove it.
- `src/stencil/qwen3.py`: KVCache deep-clone independence, `prefill_with_eviction` pre-query semantics,
  hook behavior on cloned caches.
- `sc1_episodes.parse_json`/`json_equal` strictness (floats like 3.0, unicode, nesting); the repeated-4gram
  helper's exact definition.
- `generate_injected(clear_after=...)` actually rebuilding KV (relied on as stated).
- Qwen3-1.7B tokenizer facts: EOS IDs 151645/151643, token counts of the delay string and integer arrays
  (delay is truncated in token space, so this is benign).
- The repo's "under-120-line registration" rule and "2x allowance" protocol; WORKLOG/wrapper exclusion
  machinery; archive/PLAN.md Phase 4 text; INTERNAL-WAVE-PLAN.md contents. Taken as given.
- Whether Qwen3-1.7B actually performs asc/desc sorts ≥29/32 (the competence gate exists precisely for this).
- All arithmetic below was recomputed by hand (no Python); marked where approximate.

## Recomputed and verified OK
- P(Bin(64,.10)=0) = 0.9^64 = 0.0011790184577738583 ✓ (verified by exact squaring chain).
- P(Bin(64,.90)>=63) = 7.3·0.9^63 = 0.0095631497130546 ✓; P(X>=62) = 0.0389 > 1/60, so 63 is exactly the
  minimal passing count — the count floor and the binomial test are aligned (redundant but consistent).
- P(McNemar b=8,c=0) = 2^-8 = 1/256 = 0.0039 ≤ 1/60 ✓ feasibility.
- alpha_f = 0.05/3 = 1/60 = 0.016667 ✓. 29/32 = 0.90625 ✓. 21,600 s = 6 h ✓.
- Floor-chain consistency: SET 48 = 24+24 strata ✓; CLEAR: C≥63 with KEEP impositions ≥8 ⇒ K≤56, and
  net(C−K)≥8 ⇒ K≤55 — jointly satisfiable but tight (see L4).
- McNemar is NOT redundant with the net≥16 floor (e.g., b=36,c=20 gives exact one-sided p ≈ 0.018–0.022
  > 1/60, hand-computed normal/exact approximation). The exact tests do real work. Good design.
- Budget plausibility (rough model, flagged approximate): per test episode ≈ 26 short decodes (~20 tok)
  + ~1,000–2,800 prefill tokens incl. 2×128-delay×5 arms; worst-case selection ≈ 9 cells × ~20k tokens;
  total ≈ 300–500k forward tokens; at batch-1 1.7B this is tens of minutes even at pessimistic rates.
  The 6 GPU-h cap has order-of-magnitude headroom; the timing-smoke gate remains the right single source
  of truth.

---

## 1. FIDELITY

**Bottom line:** the design genuinely tests SET/HOLD/SWITCH/CLEAR with a content-free signal under the
engineering restriction in astra-drift-assessment ("permits a task address while excluding task answers or
arbitrary memory values"). No operand/answer smuggling found. Pin+echo is explicitly banned ("no ... text
echo, retrieval, or pin"). The run-time signal is enum A/B/OFF; vectors are operand-averaged on balanced
extraction triples; the cue is removed before tokenization; transplant moves only the enum; arm symmetry
is enforced by prompt/KV/position/initial-logit equality checks at decision start.

Control sufficiency against trivial explanations — adequate:
- "Model sorts anyway": OFF arm + net≥16 floors + exact McNemar ✓.
- "Any dose-matched perturbation works": shuffled Gaussian directions at rho_L, complete-schedule R_i,
  sum(R)=0 plus the (redundant but correct) equivalence test at the predeclared 10% margin ✓.
- "Vector carries operand content": mean over 64 balanced lists, fresh test operands, exact-match scoring ✓.
- "Cue leakage into KV/prompt": pre-tokenization removal, canonical clone, hash/equality checks ✓.
- "Hook-removal alone certifies CLEAR": retained contaminated fork + KEEP contrast + nonempty-cache and
  nonzero-dose counters ✓.

**F1 (low) — actuation is continuous, latch is external, and the draft says so.** alpha·u is injected at
every decode position of a reply; the "transient, content-free" property lives entirely in the externally
maintained enum. The claim ceiling ("content-free oracle controllability ... externally latched delay")
is honest about this. No change, but a PASS must not be narrated as anything stronger.

**F2 (low) — CLEAR is sound and mostly non-vacuous; one clause is near-vacuous in the dominant regime.**
CLEAR and KEEP forks share identical contaminated KV and differ only in hook-on during the neutral replies.
So "ZERO old-task impositions after CLEAR" can only be violated via residual-KV attention leakage (hook off),
while KEEP's ≥8-imposition floor is driven by ongoing injection. The genuinely informative parts — exact
copy on the contaminated fork (≥63/64), KEEP interference floor, and the residual audit — are sound; the
audit is descriptive-only, which the ceiling ("behavioral release on these queries, not bitwise erasure")
already caps. Acceptable.

**F3 (low) — transplant ≡ swapped by construction.** Enum-only state + greedy determinism make the
transplant arm the same computation as swapped (the setup sham check exists to verify that bit-identity).
It adds no evidential weight; the draft already says "not two independent replications." Keep as a
determinism witness or subsample it (see item 5); do not count it twice anywhere (draft doesn't).

**F4 (low) — shuffled gates only COMPLETE schedules.** A shuffled direction that sorts only at SET is
reported descriptively, not gated. Acceptable: task-specific A-vs-B selection is already demonstrated by
the swapped arm; but note in analysis, not as a gate.

## 2. VALIDITY

**H1 (HIGH) — gates/selection admit configurations that cannot plausibly pass the registered endpoints;
CLEAR is near-unreachable even under a perfect release mechanism.** Hand-computed, direction is fail-closed
(no false-PASS risk), but the screen can burn its one 6-GPU-h shot producing an uninformative FAIL:

- CLEAR as drafted: C_i conjoins retained-KV CLEAR (2 copies) AND clean replay (2 copies) ≈ q^4 per
  episode. The copy gate admits a trunk with complete-pair rate 31/32 = 0.96875 ⇒ per-query q ≈ 0.984.
  P(sum(C)≥63 | q=0.984, perfect release) ≈ 0.09–0.10. Even at q=0.99, P ≈ 0.28; at q=0.995, P ≈ 0.64.
  So the CLEAR family fails with high probability from trunk copy noise unrelated to clearance.
- SET: S_i = 2 conjunctive decisions; sum(S)≥48/64 needs per-decision p ≥ 0.866. Selection admits cells
  at 24/32 = 0.75 per task. A cell at p=0.90625 passes SET with ~0.95 probability ✓ but —
- SWITCH: W_i = swapped AND transplant arms each complete all four decisions; with transplant
  bit-identical to swapped (the design's own determinism requirement) the effective requirement is p^4
  ≥ 0.75 ⇒ p ≥ 0.931 (up to ≥0.965 if GPU nondeterminism decorrelates the arms). At the competence-floor
  rate p=0.90625, P(sum(W)≥48) ≈ 0.12. Selection's 24/32 floor is far below what the endpoints imply.
- n=32 setup trials cannot certify p≥0.93 regardless (one-sided 95% lower bound for 32/32 ≈ 0.91); that is
  inherent — so the registration must at least SAY that eligibility ≠ certified reliability and that a
  reliability FAIL is FAIL for this actuator/dose, with per-decision/per-query reliabilities reported.

Fixes in replacement text R1–R4 below (raise selection sort floor 24/32→29/32, copy gate 31/32→32/32,
remove the replay conjunct from C_i, add the registered power sentence).

**M2 (MEDIUM) — replay is simultaneously "diagnostic, not a matched treatment arm" and a conjunct of C_i.**
These two characterizations conflict; the conjunct makes a diagnostic able to veto PASS on copy noise.
R3 makes replay audit-only (mandatory for every episode, fully reported).

**M1 (MEDIUM, fidelity-validity seam) — HOLD/delay semantics are two-readable.** "Processed while the latch
survives SET->HOLD" never says whether the 128 delay tokens enter subsequent decisions' canonical prefixes.
Under the harness reading ("only an enum persists across the delays"), HOLD = re-engagement of an external
latch on a rebuilt prefix — no model-side state spans the gap — and "survive a delay" in the Question
sentence invites a stronger reading than the datum supports. Either reading is defensible; the draft must
pin one. R5 pins the enum-only reading with honest wording (matches harness); the stronger alternative
(delay tokens retained in later prefixes) is a legitimate upgrade if preferred, and costs nothing at this
budget.

**M3 (MEDIUM, conditional) — registration-text binding.** The harness says the handoff sits "outside the
under-120-line registration"; DRAFT v1 is far longer than 120 lines. I could not verify the repo rule. If
registration requires compression, there is a real risk of silent semantic drift between the reviewed text
and the registered text. R7 hash-binds the reviewed protocol text into the manifest and requires explicit
delta listing — harmless even if the rule doesn't exist.

**L1 (low):** "McNemar win" never restated as p≤alpha_f at use sites; fixed centrally (R4).
**L2 (low):** selection breakage floor says "each evaluated arm" without enumerating setup arms (swapped/
shuffled/transplant first appear at test); fixed in R2.
**L3 (low):** at C=63 exactly, net≥8 forces a 9th KEEP failure beyond the registered "impose ≥8" floor;
satisfiable but the sentence should read "at least 9" for boundary coherence (optional; left as note).
**L4 (low):** no way to PASS without answering the question was found. Nearest conceptual gap: PASS
certifies oracle-scheduled steering of two frozen directions — exactly and only what the ceiling claims.
Collinearity degeneration produces FAIL (sensitivity), never false PASS. Statistical construction (paired
per-episode indicators, Bonferroni 1/60, conjunctive families, fail-closed stop rules, FAIL/INCOMPLETE/
INVALID/INELIGIBLE/FAIL-ACTUATOR partition) is coherent; "any failed requirement ⇒ FAIL for this
actuator/dose/trunk" and "no claim that internal focus is impossible" are the right readings.

## 3. SKILLS/COMPETENCE

**S1 (low) — asc/desc sort of 5–8 distinct integers in [−9,9] is a fair first pair.** Identical output
format/length distribution, symmetric difficulty, maximal circuit overlap (which matches Miller's
"overlapping ensembles" and makes the swapped control interpretable); both gated ≥29/32 with visible cue
on shared operands; fully operand-sensitive; rejection law guarantees identity ≠ asc ≠ desc so old-task
imposition in CLEAR/KEEP is detectable. Risks are all fail-closed: default-sort bias inflates the OFF
baseline (net floors catch it); near-collinearity of u_A/u_B causes SWITCH FAIL, not false PASS (see L/actuator
flag R6). Alternative pairs (copy-vs-sort, sort-vs-reverse) have asymmetric OFF baselines and weaker
imposition detection. No better first pair; keep. Competence arithmetic (29/32 = 90.625% ≥ 90%) ✓, but
see H1: the gates admit trunks the endpoints will fail. Addressed via R1.

## 4. ACTUATOR/SELECTION

**A1 (low) — extraction/actuation construction is sound as specified.** Operand-balanced triples, fp32,
rho_L equal-dose normalization across tasks (removes dose-as-confound), grid (alpha,L) lexicographic with
first-eligible on setup only, manifest freeze before test — all appropriate. Given check-30 (alpha 2.0/L12
truncated 14/20), lowest-alpha-first ordering, the 64-token cap with T-breakage, and ≤1/64 breakage floors
with second-breakage stop are the right mitigations; degeneration fails the actuator rather than producing
a false claim. FAIL-ACTUATOR is the modal outcome given history and is an acceptable screen result.

**A2 (low) — cos(u_A,u_B) collinearity is only "reported," not flagged.** R6 adds a predeclared
HIGH-COLLINEARITY manifest marker at cos>0.9 (no retuning permitted).

**A3 (low) — selection→test leakage: none found.** Setup-only selection, seeded law + cross-split
unordered-set collision rejection (stronger than seed-disjoint), predetermined cell order, no setup
statistical claims. Unchecked code dependency flagged at top: `mean_difference`/`make_residual_hook`
layer-input and last-position semantics must be proven by the harness fixtures; this is the place a silent
layer off-by-one would live.

## 5. COST/SIMPLICITY

**C1 (low) — budget is not at risk.** Recomputed rough accounting above: order 10^5 forward tokens total,
well under 6 GPU-h even with 5–10× overhead and reloads; the smoke + 1.25 multiplier + full next-attempt
reservation is proportionate; "never relax to 2×" is conservative and fine.

**C2 (low) — cuts that do not lose the answer (optional, none required):**
1. Transplant arm at test: subsample to a determinism audit (it is provably the same computation as
   swapped under the design's own sham-identity requirement); saves ~1/5 of sorting generations.
2. Within-cell sequential gating at selection: evaluate cue-absent sorts first, skip the CLEAR/KEEP/replay
   evaluation on cells failing the sort floor (eligibility is conjunctive; first-eligible semantics
   unchanged) — this is the single biggest selection cost saver given the fork-heavy CLEAR procedure.
3. If M1/R5 keeps delays out of later prefixes, note the delay processing is compute-only (it still
   exercises hook-off/on transitions; that is its entire function).
4. Extraction bank 64→32 lists would suffice for a mean-difference at layer granularity; marginal.

**C3 (low) — no framework-building detected.** Every heavy clause maps to a past failure mode (check-30
degeneracy → T/R; drift → lineage walls; pin+echo → explicit ban; CLEAR vacuity → retained-KV fork + audit).
Harness brief mirrors the draft faithfully; CLI stage order, refuse-before-load evidence gates, append-only
ledger, and the "wave scripts execute GPU at import — never import" guard are all correct. No
contradictions with the draft found except items folded into findings above (setup-arm enumeration,
replay's dual role).

**C4 — verified closed forms** listed at top; all match the draft to the digits given.

---

VERDICT: SOUND-WITH-FIXES

Zero critical findings. One open HIGH (H1) plus MEDIUMs M1–M3 must be closed (adopted or refuted with
evidence) before registration, per the draft's own "zero open high/critical" rule. All fixes below are
fail-closed or definitional; none weakens the science.

## EXACT REPLACEMENT TEXT

R1 — replace:
  "Before extraction/selection, require >=29/32 (90.625%, hence >=90%) exact answers for EACH skill with
  its cue visible on the 32-episode setup slice, using the same operands for A/B; also require >=31/32
  complete two-query neutral-copy pairs with OFF."
with:
  "Before extraction/selection, require >=29/32 (90.625%, hence >=90%) exact answers for EACH skill with
  its cue visible on the 32-episode setup slice, using the same operands for A/B; also require 32/32
  complete two-query neutral-copy pairs with OFF. These gates do not certify the per-decision reliability
  the endpoints imply (SET >=48/64 over two-conjunctive-decision episodes implies per-decision >=0.87;
  SWITCH >=48/64 implies >=0.93, up to >=0.97 if nondeterminism decorrelates the transplant arm; CLEAR
  >=63/64 tolerates at most one episode failure, and n=32 setup trials cannot certify any of these).
  Failure on reliability alone is FAIL for this actuator/dose/trunk, reported with per-decision and
  per-query reliabilities for every verdict."

R2 — replace:
  "Select the FIRST eligible cell on setup only: >=24/32 cue-absent exact sorts per task; >=31/32 complete
  CLEAR/replay neutral pairs per task; >=4/32 KEEP old-task impositions per task; and <=1/32 episodes with
  breakage in each evaluated arm."
with:
  "Select the FIRST eligible cell on setup only: >=29/32 cue-absent exact sorts per task; >=31/32 complete
  CLEAR/replay neutral pairs per task; >=4/32 KEEP old-task impositions per task; and <=1/32 episodes with
  breakage in each evaluated arm. The evaluated setup arms are correct, OFF, CLEAR, KEEP and replay;
  swapped, shuffled and transplant arms are first exercised at test under their own breakage floors.
  Within each cell evaluate the cue-absent sorts first and skip the CLEAR/KEEP/replay evaluation when the
  sort floor fails; eligibility remains conjunctive and the first-eligible rule is unchanged."

R3 — replace:
  "C_i = retained-KV CLEAR AND its clean replay both copy both neutral lists exactly;"
with:
  "C_i = retained-KV CLEAR copies both neutral lists exactly on the contaminated fork; the clean OFF
  replay is run for every episode and reported in full (per-layer K/V max-absolute differences,
  first-decision logit differences, greedy token equality) as a diagnostic audit, and is not a conjunct
  of C_i, not a matched treatment arm, and cannot certify or veto clearance;"

R4 — replace:
  "McNemar p = sum[j=b..b+c] choose(b+c,j)/2^(b+c), b=treatment-only successes, c=control-only; b+c=0
  gives p=1."
with:
  "McNemar p = sum[j=b..b+c] choose(b+c,j)/2^(b+c), b=treatment-only successes, c=control-only; b+c=0
  gives p=1. Everywhere above, 'exact McNemar win' means this one-sided exact p <= alpha_f = 1/60."

R5 — replace (in "Matched episodes, hold and transplant"):
  "Maintain only the enum A/B/OFF between decisions, not activations/answers/KV from prior sorting
  replies; hooks are off during delays. D=128 tokenizer tokens from repeated `The room is quiet. The
  light is steady. `, truncated in token space, processed while the latch survives SET->HOLD and
  SWITCH->BACK; no intervening cue."
with:
  "Maintain only the enum A/B/OFF between decisions, not activations/answers/KV from prior sorting
  replies; hooks are off during delays. D=128 tokenizer tokens from repeated `The room is quiet. The
  light is steady. `, truncated in token space, processed hook-free on each arm's live cache between
  SET and HOLD and between SWITCH and BACK; no intervening cue. Delay tokens, earlier prompts and all
  generated answers are excluded from every later decision's canonical cue-free neutral prefix: the only
  state spanning each delay is the enum. HOLD therefore measures re-engagement of the externally
  maintained latch after an externally processed delay; no model-side persistence across the delay is
  tested, required or claimed."

R6 — replace:
  "Report norms/cosines; only this frozen direction pair can carry the selected task, never
  operand-dependent vectors."
with:
  "Report norms/cosines; if cos(u_A,L, u_B,L) > 0.9 at the selected layer, mark HIGH-COLLINEARITY in the
  selection manifest and surface it in the verdict; no alternative contrast or orthogonalization may be
  substituted in v1. Only this frozen direction pair can carry the selected task, never operand-dependent
  vectors."

R7 — replace:
  "Freeze the selected L, alpha, vector bytes, extraction/setup outcomes, seed law, code/trunk/tokenizer
  hashes, decode settings, prompts, delay and scoring in one manifest before opening test."
with:
  "Freeze the selected L, alpha, vector bytes, extraction/setup outcomes, seed law, code/trunk/tokenizer
  hashes, decode settings, prompts, delay and scoring in one manifest before opening test; the manifest
  also binds the SHA-256 of the reviewed protocol text, and the ledger registration quotes that hash with
  any textual deltas listed explicitly, so no post-review edit can pass silently."

(Notes L3's "at least 9" KEEP-imposition boundary tweak is optional and not required for the verdict.)
```

**Summary for Brian:** The draft faithfully operationalizes your question — content-free A/B/OFF scheduling of two demonstrated skills with real SET/HOLD/SWITCH/CLEAR structure, adequate controls against every trivial explanation I could construct, honest claim ceilings, and coherent fail-closed statistics (all quoted constants recomputed and verified). I could not verify line numbers or the `function_vectors.py`/`qwen3.py` internals (flagged above). The one HIGH finding: the registered endpoint floors are statistically misaligned with the gates that feed them — as drafted, CLEAR passes only ~10–28% of the time even under a *perfect* release mechanism at admitted copy reliability, and SWITCH needs per-decision reliability (≥0.93) far above what selection screens for; the seven exact replacements above close this without weakening any claim.

VERDICT: SOUND-WITH-FIXES