# SC1 draft review — kimi-k3 (2026-09-04)

# SC1 draft registration — cross-model review (kimi-k3, 2026-09-04)

Intended file: `results/sc1-review-kimi.md`. **I could not write the file**: this session has no shell and no file tools. No repo edits were made; the text below is the complete document, ready to be saved verbatim. No processes were launched or signalled; no GPU work was done; the sealed IFEval input and sealed BFCL cohort were never accessed (nothing to check by design).

**What I could not check**
1. No code execution existed in this review environment. The required power recomputation (item 4) was done analytically (normal approximation with continuity correction over the registered double-binomial construction), not by integer enumeration — see P1.
2. No repo access: all file:line citations in the pasted material (e.g. `scripts/multiif_evict.py:271-287`, `src/stencil/bfcl.py:1592-1625`, `LEDGER-PLAN.md:715-721`) and the classifier sha256 records could not be verified against files. I cite evidence below by document + section + quoted clause instead of line numbers.
3. `data/classifier/` artifacts, the dev probe, and the actual eviction/selector source were not pasted; relied on their descriptions.
4. GPU-hour extrapolation is from Leg B unit costs only; no SC1 smoke timing exists yet.

---

## 1. VALIDITY

The core is correct. The estimand (D = P(Y_clf=1) − P(Y_rule=1) under the frozen mixture), the exact one-sided McNemar (`p = Σ_{j=b}^{b+c} C(b+c,j) 2^{-(b+c)}`, p=1 at b+c=0, no mid-p/asymptotics), D_hat=(b−c)/N with N=all pairs, and the conservative [L_b−U_c, U_b−L_c] Clopper-Pearson construction all match design source §5 exactly. b−c≥13 ⟺ D_hat≥5.08 pts, so "(>= 5 points)" is accurate. The setup gate (full ≥24/32 AND full−evicted ≥8/32, run before final outcomes) is non-vacuous and reachable — Leg B showed full−evicted ≈48 pts of headroom on a comparable instrument. On the G1 worry: the registration **cannot** be satisfied without answering the question — ties/low discordance force "no worthwhile learned advantage demonstrated," which is the answer; the rule is independently deployable with its own budget (the Leg B borrowed-budget defect is fixed). Findings, however:

- **V1 (MEDIUM)** — Draft, "Adoption rule": *"clf-only invalid/truncated/repetitive episodes (vs rule) <= 2"* is readable two ways: 2 per flag (up to 6) vs 2 episode-level union; "(vs rule)" does not state the differential explicitly. This is the same brittleness class that sank Leg B's claim. Fix: **R1**.
- **V2 (MEDIUM)** — Draft, "Adoption rule": *"repetitive = a normalized 4-token block repeated >= 8 times"* drops "consecutive" from the source sketch (results/astra-research-blockers.md §3: "repeated at least eight **consecutive** times") and leaves "normalized" undefined. A scattered 4-gram would be flagged under the draft, not under the source. Fix: **R1**.
- **V3 (MEDIUM)** — Draft, "Cost cap": overrun behaviour unspecified. The source sketch has the rule ("defer the test without shrinking its final cohort"); without it, a mid-run overrun invites ad hoc choices after outcomes are partially produced. Fix: **R3**.
- **V4 (MEDIUM)** — Draft, "Freeze sequence": registration is binding at step (3) but amendable "by dated amendment before step (5)", while setup outcomes are opened at step (4). A late amendment window with partial (setup) outcomes visible is a real, if bounded, abuse channel. Fix: **R4**.
- **V5 (LOW)** — The source sketch's operational limit "mean total latency ≤ 1.25× rule" is silently dropped (draft has latency only as reported-not-gated). Defensible either way, but the decision must be registered. Fix: **R5**.
- **V6 (LOW)** — `B = min(256, floor(0.25·C))` is inert under the contract: histories ≥4,096 tokens ⇒ C ≥ 3,072 ⇒ floor(0.25·C) ≥ 768, so B=256 de facto for all 288 episodes. Harmless (identical both arms) but record it so reviewers don't expect the adaptive branch to engage.
- **V7 (LOW)** — The power paragraph omits the source's key honest-expectation figure: the joint adoption gate has ~49.7% probability at true δ=5pts, q=0.20, and inconclusive is a legitimate outcome. Fix: **R6**.
- **V8 (LOW)** — No arm-execution-order rule; the design source (§5) notes order randomization addresses runtime effects. Fix: **R7** (and M8 below).

## 2. FAIRNESS

Ceilings are identical (B, E, 1,024 recent window, protected prefix, decoding, ≤256 tokens, one output each); the rule reads no classifier scores/quotas/counts/echo lengths; nothing is borrowed — the Leg B/G1 defect is closed. Both arms share admission (whole-span, skip-oversize, continue) and chronological echo. B=256/E=256 are defensible: continuity with Leg B-era budgets, and Leg B's echo arm used a mean 48.77 echo tokens, so E=256 rarely binds; actual pin/echo use is reported-not-gated.

- **F1 (MEDIUM)** — Draft, "Arms": clf ranks *"user sentences + 128-token tool chunks"*; the rule takes *"prior-user spans newest-first, then prior-tool spans newest-first"* — the rule's span unit is never defined. If implemented as whole turns vs the classifier's sentences/chunks, granularity differs by arm structurally. Fix: **R2** (same frozen candidate set, different ranking).
- **F2 (LOW)** — Echo behaviour when admitted spans exceed E is unspecified (which spans get emitted). Identical for both arms, but it is an unfrozen coder degree of freedom. Fix: **R8**.
- **F3 (INFO)** — The rule's user-before-tool ordering structurally deprioritizes tool-origin facts (50% of the mixture). That is the predeclared parameter-free comparator itself (and Leg B's rule beat the classifier by 3.5 pts), not a rigged handicap. No fix; registered as intended.

## 3. CONTAMINATION

Lineage is strong: authors receive only the contract; no benchmark item/diagnostic/selector score/repo example shown; authors blind to expected winner; contract explicitly forbids benchmark imitation and repo `data/`/`results/` reuse; smoke episodes never reused; episodes hashed before any run.

- **C1 (MEDIUM)** — "No sibling stories / semantically distinct" is enforced only by unlogged reviewer judgment (contract: "changing names or numbers does not make a new scenario"). Not auditable after the fact. Fix: recorded `scenario_gist` + pairwise-distinctness sign-off + realized factor counts (**R9**).
- **C2 (LOW)** — The six mutations cover stale-ID/cancelled/wrong-entity/wrong-scope/empty/collateral, but "not passable by a generic answer" and "age=old episodes truly require pre-window info" remain judgmental. Add two reviewer-run failing constructs: a generic safe response, and a recency-only answer for age=old episodes (**R9**). Also require an explicit protected set per episode (both styles) so the zero-corruption adoption clause can never be vacuous.
- **C3 (LOW)** — Contract: *"Setup episodes (32, separate authors' pool…)"* is ambiguous — separate authors, or a separate episode pool? Cost and contamination implications differ. Fix: **R9**.
- **C4 (LOW)** — The author pool (kimi-k3, fable, gpt-6-astra, Opus) overlaps with the models that produced the design source and program review. Fine **only** if authoring sessions are fresh contexts containing solely the contract, with no repo access; record session provenance and per-record attestation that nothing benchmark-derived was consulted or imitated. (**R9**.)

## 4. POWER / COST

- **P1 (verified by approximation; enumeration not run)** — Required cell N=256, δ=0.05, q=0.20: M~Bin(256,0.2) (mean 51.2, sd 6.4); reject when b≥k(m) with k from the exact Bin(m,0.5) tail; under H1 b|m~Bin(m,0.625). My hand computation (normal approx w/ continuity correction): m=45→≈0.45; m=51 (k=32)→≈0.54; m=52 (k=33)→≈0.50; m=57 (k=36)→≈0.51; weighted over M ⇒ **≈0.50–0.52, consistent with the registered 50.9%/51%**. Spot checks: q=0.10 cell ⇒ ≈0.78–0.82 (registered 78.2%); δ=0.10, q=0.20 ⇒ ≈0.97 (registered 97.4%). Joint-gate check at m=51: b−c≥13 ⟺ b≥32 = k(51) — consistent with the source's 49.7%. **Caveat:** this is an analytic cross-check, not the registered integer enumeration; attach the enumeration script + output hash at registration.
- **P2 (MEDIUM)** — 40–64 author-hours is achievable only with a spec-driven toolchain. 288 executable checkers + 1,728 validated mutations hand-rolled will overrun. Cheapest independence-preserving cut: authors write a structured episode spec (scenario skeleton, obligations, invariants, protected set, indispensable-fact pointers) and checkers + six mutations are **code-generated from that single source of truth** (correct-by-construction), reviewer validates the generator per family plus spot-checks; entities/distractors procedurally sampled from the pinned seed. Note: procedural generation of whole scenarios from a small template set would violate the contract — skeletons must remain individually authored and distinct. Do **not** cut N (power is already ~51% at q=0.20) or the mutation count.
- **P3 (LOW)** — 8 GPU-h is plausible: Leg B cost 75,124 s for 909×7 ≈ 6,363 arm-runs ⇒ ≈11.8 s/arm-run; SC1 ≈ 656 runs (288×2 + 32×2 + 16 smoke) ⇒ ≈2–4.5 GPU-h at 15–25 s/run. Keep the defer clause (R3) and re-measure at the setup gate.

## 5. MISSING PIECES — harness coder brief must pin (REQUIRED)

- **M1** Renderer & token accounting: frozen renderer/template + tokenizer; define what counts toward the 4,096–8,192 history tokens, the 1,024 recent window, C, B (columns), E (header + role/turn labels + quoted facts included).
- **M2** Eviction core reuse from `src/stencil/bfcl.py` / `scripts/multiif_evict.py`: pre-query eviction, pin-mask persistence through eviction, protected prefix handling; freeze one-shot vs two-stage prefill (the recorded ~8e-5 equivalence permits either; pick and record one).
- **M3** The frozen segmenter (user sentences + 128-token tool chunks), hash-verified identical to the classifier's segmentation.
- **M4** Echo builder incl. the R8 emission rule; deterministic.
- **M5** Run-time verification of `data/classifier/model/ft` sha256, threshold 0.5; scope resolver OFF, digest OFF, amplification/steering OFF with per-run intervention counter logged (required 0).
- **M6** Checker runner: editing schema/content rules; tool-work full resulting-state diff incl. protected records; binary verdict + cause; invalid/truncated/repetitive detectors implementing R1's exact definitions (normalization spec).
- **M7** In-memory DB executor: deterministic, per-arm isolated state, full-state serialization for the checker.
- **M8** Arm-order alternation/randomization per episode (R7); provably stateless runs (no KV/logit carryover).
- **M9** Hash manifest before step (4): contract, registration, all 288 episode JSONs, classifier files, segmenter, renderer, checker code, harness commit; completed-output immutability log.
- **M10** Predeclared interruption classes; resume = rerun the missing attempt from identical inputs; completed outputs never changed; unresolved defect invalidates the run without dropping pairs.
- **M11** Setup-gate automation with sealing: final outcomes cannot be opened until the gate passes; cumulative GPU-hour meter vs the 8-h cap with the R3 defer action.
- **M12** Paired per-run rows: pinned columns, echo tokens, latency split, flag union, checker verdict + causes — backing every "reported, not gated" item.

---

## VERDICT: SOUND-WITH-FIXES

The estimand, test, intervals, gates, budget symmetry, and contamination controls are fundamentally correct and faithfully carry the design source; every finding above is a pre-registration textual fix, none requires re-derivation. V1–V4/F1 must land before step (2); C1/P2 before authoring.

### Exact replacement text

**R1 — replace the adoption-rule sentence:**
> "Adoption rule (engineering, on the estimate): keep the learned selector only if (i) p <= 0.05 AND b - c >= 13 (D_hat >= 5.08 points) AND (ii) the number of episodes on which the clf arm carries any flag in {invalid, truncated, repetitive} while the rule arm carries none of them on the same episode is <= 2, counting each episode at most once, AND (iii) the number of episodes with checker-detected collateral state corruption (any protected-set invariant violation) on the clf arm and none on the rule arm is zero. Definitions, frozen: invalid = final output fails the episode's parser/schema; truncated = decoding stops at the 256-token cap without a complete parseable output; repetitive = after normalization (Unicode NFKC, case-folded, whitespace-collapsed decoded text), some 4-token block repeats >= 8 consecutive times. All three flags and their union are recorded per arm per episode."

**R2 — replace the rule arm line:**
> "rule — ranks the SAME frozen candidate-span set as clf (user sentences and 128-token tool chunks from the frozen segmentation): all prior-user spans newest-first, then all prior-tool spans newest-first; deterministic tie-breaks by source offset; identical admission (whole spans while they fit B, skip-oversize-and-continue) and echo procedure; it reads no classifier scores, quotas, selected counts, or echo lengths; its budget is exactly the registered B and E, nothing borrowed from or scaled to any classifier quantity."

**R3 — append to "Cost cap":**
> "If measured or projected cumulative runtime exceeds 8 GPU-h, the run halts before any further outcome is opened and the test is deferred with its cohort intact; N is never reduced, and any material change is a new registration with new sources."

**R4 — replace the final freeze-sequence sentence:**
> "Registration becomes binding at step (3): after episode hashes are recorded, text here changes only by dated amendment before step (5); after step (4) (setup outcomes open), amendments may fix typos or clarify wording only and may not alter the estimand, test, gates, budgets, definitions, or adoption rule — any such change requires new setup and final sources and a new registration."

**R5 — append to the adoption rule:**
> "AND (iv) mean total per-episode latency of the clf arm, including selector scoring, admission, and echo construction, is at most 1.25x the rule arm's mean. If this sub-clause is dropped, the dated rationale must be recorded in this registration before step (3); latency is reported regardless."

**R6 — append to the Power paragraph:**
> "The joint adoption gate (p <= 0.05 AND b - c >= 13) has probability about 49.7% at a true 5-point gain with q = 0.20; SC1 is credible for a substantial (about 10-point) advantage, and an inconclusive result is a legitimate registered outcome, reported as 'no worthwhile learned advantage demonstrated', never 'equivalent'."

**R7 — new sentence in the Arms block:**
> "Arm order alternates by episode index (clf-first on odd, rule-first on even, or randomized from the recorded episode seed); every run starts from fresh harness state with no KV cache, logits, or mutable state carried across arms or episodes."

**R8 — new sentence in the Arms block (echo):**
> "Echo emission: a fixed header (with role/turn labels and quoted tool facts) is always emitted and counts against E; admitted spans are then walked oldest-first, each emitted only if it fits the remaining E, skipped otherwise, until the list is exhausted. Identical in both arms; frozen in the harness."

**R9 — contract additions:**
> New record field `"scenario_gist"` (one line). New reviewer paragraph: "The independent reviewer additionally (a) signs off from the 288 scenario_gists that all episodes are pairwise semantically distinct (a shared task+setting+governing-rule skeleton with changed names/values is a sibling, not a new scenario) and that setup and final share no story/entity/task; (b) constructs and runs, per episode, two further constructs that must FAIL the checker: a generic safe response with no episode-specific content, and, for age=old episodes, a best-effort answer using only the most recent 1,024 tokens; (c) confirms every episode declares a protected set (forbidden keys/lines for editing; protected records for tool-work); (d) records realized factor counts." Replace "separate authors' pool" with "a separate pool of episodes from the same authors under this contract, sharing no story, entity, identifier, or task with the 256 final episodes". Add: "Each author attests per episode that no public benchmark item or derivative was consulted or imitated, that authoring ran in a fresh context containing only this contract, and that all entities are fictional and seed-sampled."