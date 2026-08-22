# Process Review — plan

**Score:** 87 / 100
**Verdict:** CONDITIONAL PASS (75–89)
**Reviewer model:** codex/gpt-5.6-sol
**Date:** 2026-08-22

## Round log

### Round 10 — 2026-08-22 (codex/gpt-5.6-sol)
- Score: 87 / 100 (delta vs prior round: +3)
- Addressed since prior round:
  - Commit `505ca63` excludes rejected kimi candidates from both reviewer context and metrics, adds the binding anti-churn clause to kimi rounds after round 1, and includes root result/retro markdown in its context inventory (`tools/run_kimi_review.py:41-75`, `tools/run_kimi_review.py:143-174`; `tools/agent_metrics.py:86-90`).
  - v1.13 registers a coder-brief contract, red/qualified README transitions, prompt-fragment amendment review, pre-call tie-break prompt capture, and qualification-producing Appendix D wording (`PLAN.md:84`, `PLAN.md:106`, `PLAN.md:118`, `PLAN.md:520-526`).
  - The amendment log now contains v1.13 and a candid retroactive v1.12 entry, and both successful and failed sol-review cleanup paths restore tracked drift and remove unauthorized new files (`PLAN.md:7-10`; `tools/run_codex_review.sh:321-342`, `tools/run_codex_review.sh:383-424`).
- New or remaining:
  - Acceptance remains conditional: v1.13 explicitly declines atomic checklist enforcement and again lands before the mandatory amendment review; README still lacks `in progress`/`killed` and document-phase triggers.
  - Kimi's new result globs remain unreachable once the 400 KB context cap is consumed by earlier review files, and future tie-breaks still lack a runnable mode, evidence bundle, raw response, and reconciled human trigger.
  - The new adaptive-lens cadence leaves lens sufficiency and canonical topic identity to orchestrator discretion without a pre-commit coverage validator; Appendix C/D contradictions and Phase 5 pilot scaling remain open.

### Round 9 — 2026-08-22 (codex/gpt-5.6-sol)
- Score: 84 / 100 (delta vs prior round: +10)
- Addressed since prior round:
  - Commit `e7034af` records the mandatory human touchpoint and the human's final override of process#1/#2/#4/#9 in both the ledger and tie-break artifact; Section 2b expressly permits that disposition, so the four High findings are now refuted rather than silently dropped (`PLAN.md:103`, `PLAN.md:128`; `docs/reviews/plan/tiebreaks.md:47-49`).
  - v1.12 defines plan-phase acceptance and the Phase 0 entry condition through `tools/check_acceptance.sh plan`, resolving the prior absence of any governed transition, and replaces Appendix C's stale version claim with amendment-log provenance (`PLAN.md:105`, `PLAN.md:494`).
- New or remaining:
  - No High/Critical finding remains open, but acceptance remains conditional: the acceptance script still does not bind exact topics, valid/adjudicated kimi artifacts, scientific evidence, ledger/README state, or the proposed commit.
  - v1.12 itself is absent from the amendment log and landed without the mandatory pre-commit amendment review; README failure/progress transitions, tie-break provenance, kimi context hygiene, and several prompt/brief contracts remain incomplete.
  - The human override accepts the parser, history-tracker, ledger, and containment limitations as trust-model constants; it does not mechanically fix them, and this round does not reopen them.

### Round 8 — 2026-08-22 (codex/gpt-5.6-sol)
- Score: 74 / 100 (delta vs prior round: +0)
- Addressed since prior round:
  - Commit `a2f8a67` makes coder allowlists mandatory in governing prose, loads sol session IDs before prompt construction, removes some newly-created files after failed sol reviews, and makes empty sol-review globs fail acceptance (`PLAN.md:104`, `tools/run_codex_agent.sh:61-85`, `tools/run_codex_review.sh:180-193`, `tools/run_codex_review.sh:321-340`, `tools/check_acceptance.sh:7-15`).
  - Commit `9b2eb7d` repairs the `set -u` variable-order regression introduced by v1.11 that killed the first Round 8 sol launches; `SESSION_FILE` and the persistent log variables are now initialized before they are read (`tools/run_codex_review.sh:180-193`).
  - The slash-form reviewer ID and prior-title immutability wording now agree between the common header and PLAN.md (`tools/codex-prompts/_common-header.md:14-28`, `PLAN.md:102-103`).
- New or remaining:
  - Four High findings remain open: forged closure still passes the severity parser; annotated finding-body integrity is still unenforced; the ledger still lacks the exact restart state it promises; and coder/reviewer failure containment remains materially incomplete.
  - Tie-break batch 2 does not refute those mechanical facts: its premises conflict with direct parser/tracker replays, the coder allowlist is checked only after launch, and its attempt to bar further reviewer adjudication conflicts with Section 2b's reviewer-concurrence and human-escalation rules.
  - Gate/README evidence is not atomic, v1.11 again bypassed amendment review and retains false Appendix C provenance, and plan-phase acceptance remains undefined.

### Round 7 — 2026-08-22 (codex/gpt-5.6-sol)
- Score: 74 / 100 (delta vs prior round: +0)
- Addressed since prior round:
  - Commit `58ef452` makes Phase 3's fixed-order G3 block the sole outcome authority, adds a non-parameterizable 90-point milestone score check, introduces a top-ledger `STATE:` convention, attempts failure-path review restoration, and adds prior High/Critical title checks (`PLAN.md:105`, `PLAN.md:121-127`, `PLAN.md:405-415`; `tools/check_acceptance.sh:1-13`; `tools/run_codex_review.sh:321-333`; `tools/review_round_tracking.py:116-146`).
  - Finding 16's red-gate rationalization path is closed by the explicit precedence rule: the sole-authority block now defines every clause, qualification, primary-variant comparator, retry, and red outcome (`PLAN.md:405-415`).
- New or remaining:
  - Title checking is not identity enforcement: silent body edits still pass, and a replacement title passes when its old 40-character prefix is copied anywhere else in the candidate.
  - The ledger's new `STATE:` entry still gives no exact command, work IDs, per-topic state, sessions, or matrix-cell/checkpoint inventory; coder containment remains unchanged, and review failure restoration still leaves new drift and a clean canonical file damaged.
  - `check_acceptance.sh` hardens the score path but accepts any sol markdown set and any kimi-file presence; it does not bind the registered topic, gate evidence, adjudication, ledger, README, or commit.
  - v1.10 again landed without its required amendment review, Appendix C still falsely says “last amended v1.7,” and plan-phase acceptance remains undefined.

### Round 6 — 2026-08-22 (codex/gpt-5.6-sol)
- Score: 74 / 100 (delta vs prior round: +0)
- Addressed since prior round:
  - Commit `e872754` enforces the registered threshold floors in both review wrappers, requires a dated closure token, routes kimi's generic phase/tradeoff/report topics, resumes ledger write-ahead, and unifies rule 5's allowed README G3 status vocabulary (`tools/run_codex_review.sh:105-109`, `tools/check_review_scores.py:22`, `tools/run_kimi_review.py:103-110`, `tools/run_kimi_review.py:122-130`, `PLAN.md:80`, `PLAN.md:126`).
  - The mandatory kimi phase-review command is now runnable, Phase 3 has a fixed clause-evaluation order, and Phase 6 admits any registered green G3 state (`tools/run_kimi_review.py:122-130`, `PLAN.md:406-407`, `PLAN.md:430`).
- New or remaining:
  - The process#2 tie-break is invalid: it refutes a byte-identity demand the current finding does not make and says dated annotations are validator-checked, while a replay still accepts an unannotated replacement finding under the same number.
  - Exact restart state, coder scope, failed-review containment, and gate/README evidence coupling remain unenforced; five High findings remain open.
  - G3's fixed-order/composition language still conflicts with Appendix C, Appendix D's stop-at-first-match rule, retry limits, and amendment-based rescue after the registered mechanism fails.
  - v1.9 again took effect without the required pre-commit amendment review; its threshold change leaves Appendix C's “last amended v1.7” provenance false, and plan-phase acceptance remains undefined.

### Round 5 — 2026-08-22 (codex/gpt-5.6-sol)
- Score: 74 / 100 (delta vs prior round: +0)
- Addressed since prior round:
  - Commit `e028c90` makes sol's generic phase rubric reachable for `phase*`, `tradeoff`, and `report`, adds optional coder allowlists, and corrects the ledger's unilateral “all resolved” claim (`tools/run_codex_review.sh:116-129`, `tools/run_codex_agent.sh:61-80`, `PLAN.md:125`).
  - G3 qualifications now compose, G3.4 follows M1b when it becomes primary, Phase 6 accepts any registered green G3 state, and Appendix D adds a bounded trained-stability branch (`PLAN.md:396-402`, `PLAN.md:424`, `PLAN.md:500`).
  - v1.8 also tightens the Phase 3 sanity-failure diagnosis and carries the stability validity check into Phase 5 evidence (`PLAN.md:499`, `PLAN.md:418`).
- New or remaining:
  - Score checking still accepts arbitrary lowered thresholds and malformed closure markers, while round tracking still accepts finding substitution and unannotated prior-content rewrites.
  - The ledger has no Round 5 write-ahead or exact restart schema; coder allowlists are optional, and failed reviewer runs still bypass containment.
  - Sol topic fallback works, but the mandatory kimi reviewer still exits on every generic phase, `tradeoff`, or `report` topic because its routing was not changed.
  - Composed G3 state names violate rule 5's restricted enum and Appendix D still permits amendment-based continuation after the registered-width mechanism fails.
  - v1.8 again landed before amendment review, changed Appendix C while leaving its “last amended v1.7” provenance line stale, and the plan phase still has no acceptance event.

### Round 4 — 2026-08-22 (codex/gpt-5.6-sol)
- Score: 74 / 100 (delta vs prior round: +4)
- Addressed since prior round:
  - Commit `bebbea8` bounds scores and validates verdict bands, registers the two missing qualified G3 states, puts the kimi cross-review on the gate checklist, and scopes rule 6's bitwise contract away from Phase 6 training (`tools/check_review_scores.py:25-40`, `PLAN.md:78-79`, `PLAN.md:102`).
  - Phase 6 now has a 120 GPU-hour aggregate budget, and the global run contract adds `DONE` markers plus skip/restart behavior for interrupted matrix cells (`PLAN.md:141`, `PLAN.md:423-428`).
  - Generic phase/retro prompt fragments, persistent sol-review logs, and a fresh-session retry were added (`tools/codex-prompts/review-phase.md:1-13`, `tools/codex-prompts/review-retro.md:1-13`, `tools/run_codex_review.sh:227-229`, `tools/run_codex_review.sh:282-315`).
- New or remaining:
  - Acceptance still permits an arbitrary low wrapper threshold and malformed closure markers; prior rounds and finding bodies can still be rewritten without the required dated annotation.
  - The ledger has no Round 4 write-ahead and falsely says all Round 3 High/Critical findings were resolved, while deferring several that remain open; coder scope and failed-review drift remain unenforced.
  - The new generic phase prompt is not actually routed for topics `phase0`/`tradeoff`/`report`, so mandatory phase reviews still fail preflight.
  - Appendix D still permits a post-failure wide-variant amendment, has no total treatment of simultaneous failures, and Phase 6 excludes two registered qualified-green G3 states.
  - Amendment v1.7 again landed before its own required amendment review; the tie-break, plan-phase acceptance bar, kimi artifact coverage, and README transition protocol remain underspecified.

### Round 3 — 2026-08-22 (codex/gpt-5.6-sol)
- Score: 70 / 100 (delta vs prior round: +1)
- Addressed since prior round:
  - Commit `e943c9f` makes a missing Findings section fail, preserves prior High/Critical finding numbers and prior round scores, adds the coder-side repository lock, and supplies the amendment prompt (`tools/check_review_scores.py:25-33`, `tools/review_round_tracking.py:92-126`, `tools/run_codex_agent.sh:37-42`, `tools/codex-prompts/review-amendment.md:1-12`).
  - The ledger now records Round 2 completion and a Round 3 write-ahead launch; Phase 5 now inherits the Phase 3 run configuration and has a 24 GPU-hour budget (`PLAN.md:123-124`, `PLAN.md:409-413`).
  - The Phase 3 matrix now includes the M1b/B2 sanity cells, and Appendix D now names isolated G3.3, G3.4, and G3.6 branches (`PLAN.md:377-395`, `PLAN.md:497-499`).
- New or remaining:
  - Review acceptance still permits out-of-range scores, contradictory verdicts, wholesale prior-round rewrites, and substitution of unrelated text under a preserved finding number.
  - The ledger remains insufficient for exact cold restart; coder scope and failed-review drift are not enforced; Phase 6 remains unbudgeted and conflicts with the global determinism rule.
  - Appendix D now introduces an unregistered `green-with-efficiency-miss` state and explicitly permits continuation after a red G3.6 result or a failed registered-width mechanism.
  - Required phase reviews have no runnable prompt fragments, kimi can run after a gate commit despite later-confirmed blockers, amendment sequencing is not auditable, and corrupt reviewer sessions have no implemented fallback.

### Round 2 — 2026-08-22 (codex/gpt-5.6-sol)
- Score: 69 / 100 (delta vs prior round: +15)
- Addressed since prior round:
  - Commit `18bca48` establishes the tracked pre-registration baseline for PLAN.md, README.md, the round-1 reviews, and the review tooling; operating rule 3 and Appendix C now use the same first-run freeze rule (`PLAN.md:74`, `PLAN.md:445-460`).
  - Finding identity, reviewer-concurrence closure, a severity-aware score check, the gate acceptance checklist, explicit non-G3 retry limits, and the named `green-with-M1b-primary` state were added (`PLAN.md:75-76`, `PLAN.md:97-102`, `PLAN.md:363-372`; `tools/check_review_scores.py:18-83`).
  - Direct orchestrator implementation edits are now prohibited, and Phase 5/7 reviews plus the Phase 5-to-6 dependency are explicit (`PLAN.md:89-100`, `PLAN.md:386-412`).
  - Phase 3 now has a pilot, a 72 GPU-hour planning budget, measured-throughput projection, and per-run timeout rule; README's guessing-ceiling language was corrected (`PLAN.md:102`, `PLAN.md:352-361`; `README.md:17`, `README.md:33`).
- New or remaining:
  - The acceptance tools still allow a prior open high/critical finding, or the entire Findings section, to disappear and then report PASS.
  - Round history preservation checks headings only; prior round text can be rewritten wholesale despite the append-only rule.
  - The ledger is already stale and still lacks the structured state required to resume agents and matrices exactly after abrupt interruption.
  - The coder wrapper neither takes the repository lock nor checks its diff against brief scope, so review serialization and role boundaries are not enforced.
  - Appendix D remains non-exhaustive and internally contradictory; Phase 5/6 budgets and the Phase 6 determinism contract remain non-executable.
  - Gate/README completion state is not mechanically coupled, and the required amendment-review topic has no prompt fragment.

### Round 1 — 2026-08-22 (codex/gpt-5.6-sol)
- Score: 54 / 100 (delta vs prior round: +0; initial review)
- Addressed since prior round:
  - None; this is the initial review.
- New or remaining:
  - Review acceptance is not mechanically conditioned on zero open high/critical findings, and prior review rounds can be removed.
  - The refutation path, ledger schema, gate state machine, and amendment controls do not support exact or auditable restart.
  - Several operating rules conflict with later exceptions, especially direct orchestrator edits, non-G3 failures, G3.2 fallback, and Phase 6 determinism.
  - Phase 5/7 review and dependency requirements are bypassable; the single-device run budgets are not operationally specified.
  - PLAN.md, README.md, and tools/ are currently untracked, so the claimed pre-registration has no repository baseline yet.

## Findings

1. **High (refuted 2026-08-22: human override — trust-model constants of a single-user repo; detection via git history and resumed reviewer sessions is the registered control; see tie-break batch 2) — Review acceptance still permits direct-checker threshold lowering and forged closure.** (updated 2026-08-22: Round 10 citations.) Section 2b, “Finding identity and closure,” says “A human may override a deadlocked finding; the override is recorded in the ledger with rationale” (`PLAN.md:105`). The named human adjudication, rationale, and matching ledger state remain present (`docs/reviews/plan/tiebreaks.md:47-49`; `PLAN.md:130`). The human accepted the parser behavior as a trust-model constant; this finding remains refuted.

2. **High (refuted 2026-08-22: human override — trust-model constants of a single-user repo; detection via git history and resumed reviewer sessions is the registered control; see tie-break batch 2) — The executed process#2 tie-break refutes a strawman while silent finding substitution remains mechanically accepted.** (updated 2026-08-22: Round 10 citations.) Section 2b, “Context carry-over,” says an unannotated edit “is a protocol violation the next round's reviewer is instructed to flag,” while “Finding identity and closure” authorizes a recorded human override (`PLAN.md:104-105`). The human adjudication specifically closes process#2 (`docs/reviews/plan/tiebreaks.md:47-49`; `PLAN.md:130`). The registered terminal authority accepted git history plus resumed-reviewer detection as the control; this finding remains refuted.

3. **High (resolved 2026-08-22: stable IDs and reviewer-concurrence closure are explicit in the governing prose) — Refutation was unilateral and had no durable finding identity.** (updated 2026-08-22: Round 10 citations.) Section 2b says “a finding's identity is `<topic>#<number>`” and “only a subsequent reviewer round may mark a finding `(resolved ...)` or `(refuted ...)`” (`PLAN.md:105`); the reviewer protocol says not to close on an orchestrator claim alone (`tools/codex-prompts/_common-header.md:28`). Findings 1-2 cover enforcement, not this resolved prose-level gap.

4. **High (refuted 2026-08-22: human override — trust-model constants of a single-user repo; detection via git history and resumed reviewer sessions is the registered control; see tie-break batch 2) — The ledger still cannot deliver its promised exact cold restart despite resuming write-ahead.** (updated 2026-08-22: Round 10 citations.) “Work log and ledger” still promises “a restarted session must be able to resume from this file alone,” while its reconciliation step consults logs, artifacts, and `git status` (`PLAN.md:124-126`). The top state still gives prose rather than an executable command (`PLAN.md:130`). The human adjudication accepts that ledger/persistent-log/git-reconciliation stack as the registered control (`docs/reviews/plan/tiebreaks.md:31-35`, `docs/reviews/plan/tiebreaks.md:47-49`); this finding remains refuted.

5. **High (resolved 2026-08-22: one absolute freeze rule and a tracked baseline exist) — Threshold pre-registration was contradictory and lacked a repository baseline.** (updated 2026-08-22: Round 10 citations.) Operating rule 3 says thresholds are “frozen permanently” after the affected phase's first run (`PLAN.md:82`), and commit `18bca48` supplies the tracked baseline. Findings 22 and 30 cover amendment sequencing and trigger ambiguity without reopening this resolved contradiction.

6. **High (resolved 2026-08-22: non-G3 gates have a bounded failure procedure) — Rule 4 was impossible to follow for five gates.** (updated 2026-08-22: Round 10 citations.) “Operating rules for the agent” says that on G0/G1/G2/G4/G6 the agent diagnoses, records, fixes only the defect, and “after three failed fix attempts on the same gate, stop and escalate to the human” (`PLAN.md:83`); G3 uses the sole-authority procedure in Finding 16.

7. **High (resolved 2026-08-22: the M1b fallback is a named alternate gate state) — The G3 fallback authorized proceeding while the written gate remained red.** (updated 2026-08-22: Round 10 citations.) Operating rule 5 registers `M1b-primary` among the qualification values (`PLAN.md:84`), and the sole G3 authority says G3.2 may produce “qualification `M1b-primary` when G3.2b passes” (`PLAN.md:416-421`); Appendix D.3 applies that result (`PLAN.md:520`).

8. **High (resolved 2026-08-22: an all-items checklist separates scientific and review status) — Gate, review, commit, ledger, and README state had no atomic acceptance rule.** (updated 2026-08-22: Round 10 citations.) The checklist says “all items required before a gate commit” and “No item may be waived” (`PLAN.md:108`), separating science, sol, kimi, ledger, README, and commit state. Finding 17 covers incomplete mechanical enforcement.

9. **High (refuted 2026-08-22: human override — trust-model constants of a single-user repo; detection via git history and resumed reviewer sessions is the registered control; see tie-break batch 2) — Coder scope and unsuccessful-review containment remain unenforced.** (updated 2026-08-22: Round 10 verification.) Section 2b says the coder wrapper “refuses to launch” without an allowlist and calls uncontained drift “a hard wrapper failure” (`PLAN.md:106`, `PLAN.md:109`). The coder still deliberately preserves failed work, as the human-approved middle path requires; v1.13 additionally restores tracked drift and deletes unauthorized new files on both sol-review paths (`tools/run_codex_review.sh:321-342`, `tools/run_codex_review.sh:383-424`). The human adjudication remains controlling (`docs/reviews/plan/tiebreaks.md:37-49`; `PLAN.md:130`); this finding stays refuted.

10. **High (resolved 2026-08-22: direct edits are restricted to non-implementation artifacts) — The orchestrator exception contradicted the fixed code-author role.** (updated 2026-08-22: Round 10 citations.) Under “Roles, fixed,” the orchestrator “does not write implementation code directly” (`PLAN.md:97`), and “Resolution scope” says implementation/test fixes “go through a coder brief” while direct edits are limited to non-implementation files (`PLAN.md:106`).

11. **Medium — Coder briefs, scope, and model provenance remain assertions rather than a contract.** (updated 2026-08-22: v1.13 adds a prose contract but not validation or provenance.) Section 2b, “Resolution scope,” now says every brief states “the objective, the allowlist, the tests to write first, the acceptance command, and the ledger handoff” (`PLAN.md:106`). That materially improves the specification. The wrapper still validates only that the brief and allowlist files exist; it does not parse those required fields, accepts environment model/effort overrides, and accepts an unsanitized agent name (`tools/run_codex_agent.sh:25-35`, `tools/run_codex_agent.sh:47-68`). The ledger's “Each entry records” schema still requires neither brief hash nor actor configuration (`PLAN.md:126`). A cold session therefore cannot prove which validated brief/model produced a diff.

12. **High (resolved 2026-08-22: Phase 5/7 review requirements and the Phase 5 dependency are explicit in prose) — Phase 5/7 could escape review and Phase 6 could bypass Phase 5.** (updated 2026-08-22: Round 10 citations.) “Cadence” requires “at minimum one review per phase before its exit commit” (`PLAN.md:107`); Phase 5 says “after a sol review ... is accepted,” Phase 6 is “Only reached” after the reviewed tradeoff, and Phase 7 says the report “ships only after” review (`PLAN.md:439`, `PLAN.md:443`, `PLAN.md:461`).

13. **High (resolved 2026-08-22: Phase 6 now has an aggregate budget and matrix restart contract) — Phase 6 had no budget or restart envelope for the single device.** (updated 2026-08-22: Round 10 citations.) “Budget discipline” requires a pilot projection, a 4x timeout, and human escalation beyond 2x (`PLAN.md:110`); Phase 6 registers an “Aggregate phase budget 120 GPU-hours” (`PLAN.md:447`), and the run contract says a run writes a `DONE` marker and interrupted cells restart identically (`PLAN.md:154`). Actual GB10 fit remains pilot-dependent, but the denominator and restart rule exist.

14. **Medium (resolved 2026-08-22: rule 6 now explicitly scopes the Phase 6 exception) — The global determinism rule conflicted with Phase 6.** (updated 2026-08-22: Round 10 citations.) Operating rule 6 says “Phase 6 training runs are seed-logged ... and are not rule-6 regressions” (`PLAN.md:85`); Phase 6 repeats “determinism relaxed to seed-logged” while keeping proof tests fp32 (`PLAN.md:449`).

16. **High (resolved 2026-08-22: Phase 3 now declares one sole outcome authority with complete precedence) — G3's nominally single-valued procedure still had contradictory inputs and authorized rescue after a registered failure.** (updated 2026-08-22: Round 10 citations.) The “G3 outcome — SOLE AUTHORITY” block says it “supersedes every earlier phrasing,” fixes evaluation order/comparator/qualifications, and makes every red step terminal after one diagnosed rerun (`PLAN.md:411-421`). That precedence closes the bypass; Finding 35 retains the maintenance hazard from contradictory subordinate text.

17. **Medium — The gate checklist is still not mechanically coupled to commits or evidence.** (updated 2026-08-22: v1.13 explicitly declines this fix.) Section 2b calls six items “all items required before a gate commit” and says “No item may be waived” (`PLAN.md:108`). `check_acceptance.sh` still scores every incidental non-kimi markdown and checks kimi only by `*-kimi.md` presence (`tools/check_acceptance.sh:5-15`); it binds neither adaptive-lens selection, scientific artifacts, adjudication, ledger state, README state, nor the proposed commit. The ledger records the refusal: “mechanical commit-checklist coupling ... cost exceeds residual risk” (`PLAN.md:130`). That rationale contradicts the checklist's no-waiver language and leaves acceptance dependent on orchestrator assertion.

18. **Medium (resolved 2026-08-22: the amendment prompt fragment exists) — The mandatory amendment-review path was not runnable.** (updated 2026-08-22: Round 10 citations.) The “Autonomy policy” says “a sol@xhigh review of it is run (topic `amendment`),” and the tracked `review-amendment.md` supplies the runnable rubric (`PLAN.md:118`; `tools/codex-prompts/review-amendment.md:1-12`). Finding 22 covers failure to use that path before activation.

19. **Medium — README transition triggers remain incomplete even though v1.9 can encode composite G3 results.** (updated 2026-08-22: v1.13 fixes red/qualified transitions but not the full status surface.) Operating rule 5 now says “Every gate-state CHANGE — including to red or a qualified state — updates” README in the same commit (`PLAN.md:84`). That closes the red/qualified limb. It still does not define transitions to `in progress` or `killed`, and Phase 5/7 document exits do not require row updates (`PLAN.md:439`, `PLAN.md:461`; `README.md:54-58`). Rows also carry no evidence path, date, accepted review, or SHA. The governed restart surface can still remain `not started` through active work or document-phase completion.

20. **Low — Out-of-canonical review drift is again present.** (updated 2026-08-22: Round 10 observation.) Section 2b says “never edit repo files while a wrapper is running” (`PLAN.md:109`). Read-only `git status --short` again showed modified `docs/reviews/plan/spec.md:1` outside this canonical process review. It was left untouched; the dirty sibling prevents clean-state attestation even though status alone cannot prove wrapper overlap.

21. **High (resolved 2026-08-22: v1.9 ports the generic phase-topic fallback to kimi) — The mandatory phase-review cadence was unrunnable for kimi.** (updated 2026-08-22: Round 10 citations.) “Cadence” retains `review-phase.md` as the fallback (`PLAN.md:107`); kimi routes phase/tradeoff/report topics without literal fragments to that file (`tools/run_kimi_review.py:122-130`), matching sol (`tools/run_codex_review.sh:121-135`). Finding 36 covers the new adaptive-lens governance gap, not command runnability.

22. **Medium — v1.10 again activated before amendment review and leaves threshold provenance false.** (updated 2026-08-22: v1.13 repairs log completeness but deliberately repeats the sequencing breach.) The “Autonomy policy” says an amendment review “must be accepted BEFORE the amendment commit lands” and requires “review-accepted-then-committed order” (`PLAN.md:118`). The amendment log now contains v1.13 and a candid retroactive v1.12 entry (`PLAN.md:7-10`), resolving missing provenance. But commit `505ca63` activates v1.13's governed review cadence, tooling, and test semantics without any tracked `docs/reviews/plan/amendment.md`; the ledger expressly declines the rule via its unregistered “initial-loop amendment sequencing” interpretation (`PLAN.md:130`). Auditability is not satisfied by documenting a known violation after effect, and no governing exception authorizes the orchestrator to waive the absolute pre-commit order.

23. **High (resolved 2026-08-22: kimi completion/adjudication is now a pre-commit checklist item) — Kimi review could occur after gate acceptance.** (updated 2026-08-22: Round 10 citations.) The “Gate acceptance checklist” requires “the phase's kimi cross-review run before the commit with its confirmed high/critical findings resolved” (`PLAN.md:108`). That closes the timing bypass even though “Cross-model review” calls kimi advisory (`PLAN.md:112`); Finding 34 covers rule 9's wording.

24. **Low — Fresh-session fallback works, but its promised audit note still cannot be produced.** (updated 2026-08-22: Round 10 re-verification.) “Review-session continuity” promises that a fresh fallback is “noted in the round log” (`PLAN.md:114`). A failed resume still retries with the already-built prompt that says “your session context is intact” and carries no fallback flag (`tools/run_codex_review.sh:180-193`, `tools/run_codex_review.sh:294-320`). The generated round cannot distinguish successful resume from continuity loss.

25. **Medium (resolved 2026-08-22: acceptance-tooling retro changes now require amendment review) — Retrospectives could change acceptance tooling without independent review.** (updated 2026-08-22: Round 10 citations.) The “Autonomy policy” says changes to the checker, tracker, wrappers, or reviewer/coder prompts arising from retros “take effect only after an amendment review accepts them” (`PLAN.md:118`). That closes the tooling/prompt limbs; Finding 31 covers the remaining AGENTS limb under “Phase retrospectives” (`PLAN.md:116`).

26. **Medium (resolved 2026-08-22: v1.13 excludes rejected candidates from both kimi context and agent metrics) — Rejected kimi sidecars demonstrably contaminate later context and metrics.** (updated 2026-08-22: Round 10 verification.) Kimi still saves a rejected candidate beside the canonical file (`tools/run_kimi_review.py:189-194`), but the context builder now explicitly skips `*.rejected.md` and metrics excludes those files and `tiebreaks.md` (`tools/run_kimi_review.py:56-75`; `tools/agent_metrics.py:86-94`). I verified the three legacy sidecars remain tracked but no longer enter either named consumer, closing the contamination defect.

27. **Medium — The first tie-break was executed through an unauditable path, and the human-trigger conflict is still live.** (updated 2026-08-22: Round 10 re-verification.) “Cross-model review” requires kimi to receive “the finding, the fix or refutation evidence, and both arguments” and requires its verdict to be ledgered (`PLAN.md:112`). v1.13 now requires a reusable tie-break prompt to be committed before a future invocation (`PLAN.md:118`), but there is still no runnable tie-break mode, evidence bundle, raw response/log, run ID, or verification record; the existing batches contain only verdict prose and `run_kimi_review.py` implements only scored topic reviews (`docs/reviews/plan/tiebreaks.md:3-49`; `tools/run_kimi_review.py:94-130`). Section 2b still triggers the human only after a disputed tie-break while the Autonomy policy triggers after two deadlocked rounds (`PLAN.md:112`, `PLAN.md:118`). The one completed adjudication is durable; the reusable path and trigger remain non-reproducible and inconsistent.

28. **Medium (resolved 2026-08-22: v1.12 explicitly makes `tools/check_acceptance.sh plan` the plan-acceptance and Phase 0 entry condition) — The plan phase has no registered acceptance condition for entering Phase 0.** (updated 2026-08-22: Round 10 citation.) Section 2b, “Cadence,” says “the plan itself is accepted when `tools/check_acceptance.sh plan` passes ... after which Phase 0 may begin” (`PLAN.md:107`). That supplies the previously absent governed transition. Findings 17 and 36 separately cover the command's incomplete evidence and lens-selection semantics; those limitations do not reopen this narrower no-condition finding.

29. **Medium — Required kimi phase reviews cannot see all gate-critical artifacts.** (updated 2026-08-22: v1.13 adds result globs but leaves them unreachable under the current cap.) The checklist and “Cross-model review” require kimi on “the gate-critical work” (`PLAN.md:108`, `PLAN.md:112`). v1.13 adds `results/*.md` and retros to the context inventory, but places them after the entire recursive review tree and still omits figures (`tools/run_kimi_review.py:40-46`). The builder returns at the first 400 KB overflow (`tools/run_kimi_review.py:56-75`); a direct current-tree replay reached the cap before `docs/reviews/plan/spec-kimi.md` and contained no result or retro marker, so the newly listed gate artifacts remain invisible in practice. A structurally partial invocation can still satisfy the presence-only gate check in Finding 17.

30. **Low — Rule 3's freeze trigger is undefined for test-gated phases.** (updated 2026-08-22: Round 10 re-verification.) Operating rule 3 freezes thresholds when “the affected phase's first run has been launched” (`PLAN.md:82`). Phases 0-2 are primarily test/fixture governed and Phase 1 has no training run; neither the first pytest nor the first `make gate-N` is registered as that event, so a restart cannot determine whether prose-level test tolerances are frozen.

31. **Medium — Retrospectives may weaken reviewer/coder instructions without independent review.** (updated 2026-08-22: v1.13 closes the prompt limb but not AGENTS.md.) “Phase retrospectives and agent evals” still requires every optimization to land as an “AGENTS.md entry” or tooling/prompt diff (`PLAN.md:116`). The Autonomy policy now review-gates checker, tracker, wrapper, and reviewer/coder prompt changes, but does not include AGENTS.md (`PLAN.md:118`); the retro rubric still checks attribution and whether an optimization landed, not whether an AGENTS edit preserves governance (`tools/codex-prompts/review-retro.md:5-11`). An instruction automatically loaded by later coders/reviewers can therefore govern the next phase without independent process review.

32. **Medium (resolved 2026-08-22: v1.13 puts the binding anti-churn limit directly in kimi's resumed-round prompt) — The kimi wrapper does not implement the binding anti-churn rule.** (updated 2026-08-22: Round 10 verification.) “Review-session continuity” gives kimi the same anti-churn rule (`PLAN.md:114`), and `run_kimi_review.py` now tells every round after Round 1 to re-verify existing findings and add new ones “ONLY for regressions introduced by fixes or clear in-scope misses” (`tools/run_kimi_review.py:143-147`). The formerly missing enforcement instruction is present before the general independent-review language.

33. **Low — Phase 5's pilot is underspecified for a matrix whose sequence lengths vary sixteen-fold.** (updated 2026-08-22: Round 10 re-verification.) “Budget discipline” requires a pilot-derived projection (`PLAN.md:110`), but Phase 5 names only “one pilot cell first” for 27 runs over `R in {2, 8, 32}` and 24 GPU-hours (`PLAN.md:437`). Task B contains R segments with 32-256-token delays (`PLAN.md:313-318`), so R=32 has about sixteen times R=2's segments. Without a named worst-case pilot or per-R scaling measurements, the single-Spark projection is not defensible ex ante.

34. **Low — Operating rule 9 still contradicts the mandatory second-reviewer role.** (updated 2026-08-22: Round 10 re-verification.) Operating rule 9 says “all reviews are sol adversarial reviews” (`PLAN.md:88`), while Section 2b calls kimi “the second, independent reviewer” and requires its cross-review before commit (`PLAN.md:108`, `PLAN.md:112`). The more specific checklist prevents a practical skip, but the global rule still denies the category it later mandates.

35. **Medium — The G3 sole-authority fix leaves materially contradictory subordinate text in the governing document.** (updated 2026-08-22: v1.13 fixes qualification grammar but leaves the material conflicts.) The authoritative block says it “supersedes every earlier phrasing” (`PLAN.md:411`), resolving Finding 16's bypass. Yet rule 5 first lists only green/M1b/red before its broader enum (`PLAN.md:84`); Appendix C still says “B0-full minus M1” instead of the primary variant (`PLAN.md:506`); Appendix D still says “stop at the first match,” permits a wider model that “does not retroactively pass” after amendment, and invokes rule 4's three-attempt procedure for G3 (`PLAN.md:515`, `PLAN.md:523-524`). v1.13's “contribute qualification” wording repairs D.3/D.6/D.7 composition (`PLAN.md:520`, `PLAN.md:525-526`), but the dead comparator, retry, and continuation contradictions remain a cold-start and future-edit hazard.

36. **Medium — Adaptive review lenses are not bound to gate acceptance or independently coverage-checked.** Section 2b, “Cadence,” now lets the orchestrator “writes a purpose-built prompt fragment” using “whatever lens best matches that artifact,” or selects the generic fallback when “no bespoke lens is warranted” (`PLAN.md:107`). The gate checklist then accepts the resulting sol review through `check_acceptance.sh`, which neither identifies a required lens/topic nor validates a prompt hash or coverage rationale; it scores every incidental sol markdown and checks only for some kimi-file presence (`PLAN.md:108`; `tools/check_acceptance.sh:5-15`). Because the orchestrator authors and selects the lens whose adequacy is evaluated only by a post-exit retrospective, it can omit a gate-critical concern or choose the generic fallback and still pass the same gate. This is a new governance bypass introduced by v1.13's adaptive-lens replacement.

## Recommendations

1. Validate the v1.13 coder-brief contract before launch, including required fields, forbidden paths, dependencies, finding IDs, artifact/handoff data, and a brief hash; validate the agent slug and require ledger authorization for model/effort overrides (`PLAN.md:98`, `PLAN.md:106`, `PLAN.md:126`; `tools/run_codex_agent.sh:25-68`).
2. Bind every adaptive lens to the reviewed diff: register its slug, rationale, prompt hash, required coverage, exact sol/kimi artifacts, and independent adequacy check before acceptance. Make `check_acceptance.sh` validate that manifest plus scientific evidence, adjudication, ledger state, README row, and proposed commit (`PLAN.md:107-108`; `tools/check_acceptance.sh:1-16`; `README.md:45-58`).
3. Define README transitions for `in progress`, `killed`, and Phase 5/7 completion; add evidence path, accepted review round/score, date, and commit SHA (`PLAN.md:84`, `PLAN.md:437-461`; `README.md:45-58`).
4. Obey review-before-commit for the next amendment and require every amendment entry to name the accepted amendment review/round/score, affected-phase launch evidence, exact old/new values, and activation SHA (`PLAN.md:7-10`, `PLAN.md:118`, `PLAN.md:497`).
5. When resume fails, rebuild the fresh prompt with an explicit continuity-loss flag and require the new round to record it (`PLAN.md:114`; `tools/run_codex_review.sh:180-193`, `tools/run_codex_review.sh:294-320`).
6. Put an explicit gate-artifact manifest—including required result markdown and figures—ahead of the recursive review inventory, and skip individual oversized files instead of returning at the first overflow (`PLAN.md:108`, `PLAN.md:112`; `tools/run_kimi_review.py:40-75`).
7. Implement a runnable tie-break command/prompt that persists the finding, both arguments, evidence bundle, raw response/log, model, and verification; reconcile Section 2b's post-tie-break human trigger with the Autonomy policy's two-round trigger (`PLAN.md:112`, `PLAN.md:118`; `docs/reviews/plan/tiebreaks.md:3-49`).
8. Register first-test freeze triggers for Phases 0-2 before Phase 0 begins (`PLAN.md:82`).
9. Extend amendment review to retro-generated AGENTS.md changes (`PLAN.md:116-118`; `tools/codex-prompts/review-retro.md:5-11`).
10. Name the Phase 5 pilot cell and require measured or registered scaling projections for R=2, 8, and 32 before accepting the 24 GPU-hour estimate (`PLAN.md:110`, `PLAN.md:316`, `PLAN.md:437`).
11. Change operating rule 9 to “all reviews of record are sol” so it no longer contradicts mandatory kimi cross-review (`PLAN.md:88`, `PLAN.md:108-112`).
12. Rewrite rule 5, Appendix C G3.4, and Appendix D to reference the Phase 3 sole-authority block without restating contradictory states, comparators, retries, or continuation outcomes (`PLAN.md:84`, `PLAN.md:411-421`, `PLAN.md:506`, `PLAN.md:513-526`).

## Evidence consulted

- `PLAN.md`, read in full, lines 1-557; SHA-256 `7b743075c121c086318099d9401509f502f50339467937ca7b1ec7a8479cac41`.
- `README.md`, read in full, lines 1-66; SHA-256 `9a4a79b70be89eb584ee563fefd6160bf0d5f374cb77a7bd158f1777d3212430`.
- `docs/reviews/plan/process.md`, the wrapper-supplied Round 1-9 content; current science/spec/process sol and kimi headers; all three tracked `*-kimi.rejected.md` sidecars; and both tie-break batches plus the human adjudication in `docs/reviews/plan/tiebreaks.md`.
- `tools/check_acceptance.sh`, `tools/run_codex_agent.sh`, `tools/run_codex_review.sh`, `tools/run_kimi_review.py`, `tools/review_diff_allowlist.py`, `tools/review_round_tracking.py`, `tools/check_review_scores.py`, `tools/agent_metrics.py`, and the complete tracked prompt inventory.
- `AGENTS.md`, `CLAUDE.md`, `.gitignore`, and the machine-local `docs/reviews/.sessions/` inventory.
- Read-only `git status`, `git log`, `git diff e7034af..505ca63`, `git show`, `git blame`, and `git ls-files`; commit `505ca63` contains v1.13 and no README change, while the sibling `docs/reviews/plan/spec.md` remained modified and was left untouched.
- Read-only inspection of `results/logs/codex-plan-{science,spec,process}.log` and `docs/reviews/.sessions/`; persistent sol logs and session IDs exist. No tracked `docs/reviews/plan/amendment.md` exists in current or historical inventory.
- Static and diff verification of v1.13's amendment log, adaptive cadence, brief contract, README trigger, prompt-review rule, tie-break commitment, Appendix D grammar, sol cleanup, kimi exclusions/anti-churn/context globs, and metric exclusions. Findings 11, 17, 19, 22, 27, 29, 31, 35, and 36 identify the remaining or partial gaps.
- Direct in-memory replay of kimi's current `build_context` at its 400 KB default: the cap was reached before `docs/reviews/plan/spec-kimi.md`, and neither a result nor retrospective marker was present; adding their globs after `docs/reviews/**/*.md` did not make them visible.
- Direct inspection of `tools/check_acceptance.sh plan`: it checks incidental sol markdown plus kimi-file presence rather than a registered evidence/lens manifest; science is 92, the concurrently modified spec round is 92, and this process round is 87, so plan acceptance remains red.
- Matrix arithmetic from the plan: Phase 3 enumerates 96 runs (66 Task A and 30 Task M); Phase 5 enumerates 27 Task B runs, and its R=32 sequences contain sixteen times as many full segments as R=2. No pilot exists, so actual GB10 throughput or fit against the 24/72/120 GPU-hour budgets cannot be verified.
- No implementation, experiment output, gate artifact, Phase 3/5 pilot, training checkpoint, retrospective, accepted plan-phase manifest, or tracked amendment review exists; no scientific gate or compute projection could be replayed.
