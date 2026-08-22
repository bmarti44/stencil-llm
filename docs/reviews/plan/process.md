# Process Review — plan

**Score:** 84 / 100
**Verdict:** CONDITIONAL PASS (75–89)
**Reviewer model:** codex/gpt-5.6-sol
**Date:** 2026-08-22

## Round log

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

1. **High (refuted 2026-08-22: human override — trust-model constants of a single-user repo; detection via git history and resumed reviewer sessions is the registered control; see tie-break batch 2) — Review acceptance still permits direct-checker threshold lowering and forged closure.** (updated 2026-08-22: Round 9 human disposition.) Section 2b, “Finding identity and closure,” says “A human may override a deadlocked finding; the override is recorded in the ledger with rationale” (`PLAN.md:103`). I verified the named human adjudication, its rationale, and the matching ledger state (`docs/reviews/plan/tiebreaks.md:47-49`; `PLAN.md:128`). The parser behavior reported through Round 8 is unchanged, but the human explicitly accepted it as a trust-model constant; under the governing override path, this finding is refuted and no longer blocks acceptance.

2. **High (refuted 2026-08-22: human override — trust-model constants of a single-user repo; detection via git history and resumed reviewer sessions is the registered control; see tie-break batch 2) — The executed process#2 tie-break refutes a strawman while silent finding substitution remains mechanically accepted.** (updated 2026-08-22: Round 9 human disposition.) Section 2b, “Context carry-over,” still says an unannotated edit “is a protocol violation the next round's reviewer is instructed to flag,” while “Finding identity and closure” authorizes a recorded human override (`PLAN.md:102-103`). I verified that the human considered the disputed tie-break and overruled sol, specifically closing process#2 (`docs/reviews/plan/tiebreaks.md:47-49`; `PLAN.md:128`). The tracker remains less strict than the prose, but the registered terminal authority accepted git history plus resumed reviewer detection as the control; this finding is refuted.

3. **High (resolved 2026-08-22: stable IDs and reviewer-concurrence closure are explicit in the governing prose) — Refutation was unilateral and had no durable finding identity.** (updated 2026-08-22: current citations.) Section 2b says “a finding's identity is `<topic>#<number>`” and “only a subsequent reviewer round may mark a finding `(resolved ...)` or `(refuted ...)`” (`PLAN.md:103`); the reviewer protocol says not to close on an orchestrator claim alone (`tools/codex-prompts/_common-header.md:28`). Findings 1-2 cover enforcement, not this resolved prose-level gap.

4. **High (refuted 2026-08-22: human override — trust-model constants of a single-user repo; detection via git history and resumed reviewer sessions is the registered control; see tie-break batch 2) — The ledger still cannot deliver its promised exact cold restart despite resuming write-ahead.** (updated 2026-08-22: Round 9 human disposition.) “Work log and ledger” still promises “a restarted session must be able to resume from this file alone,” while its reconciliation step explicitly consults logs, artifacts, and `git status` (`PLAN.md:122-124`). The top state still gives prose rather than an executable command (`PLAN.md:128`). I verified, however, that the human adjudication expressly closes process#4 and accepts the existing ledger/persistent-log/git-reconciliation stack as the registered control (`docs/reviews/plan/tiebreaks.md:31-35`, `docs/reviews/plan/tiebreaks.md:47-49`). That terminal override refutes this finding despite the literal mismatch.

5. **High (resolved 2026-08-22: one absolute freeze rule and a tracked baseline exist) — Threshold pre-registration was contradictory and lacked a repository baseline.** (updated 2026-08-22: current citations.) Operating rule 3 says thresholds are “frozen permanently” after the affected phase's first run (`PLAN.md:80`), and commit `18bca48` supplies the tracked baseline. Findings 22 and 30 cover current amendment provenance and trigger ambiguity without reopening this resolved contradiction.

6. **High (resolved 2026-08-22: non-G3 gates have a bounded failure procedure) — Rule 4 was impossible to follow for five gates.** (updated 2026-08-22: Round 9 citations.) “Operating rules for the agent” now says that on G0/G1/G2/G4/G6 the agent diagnoses, records, fixes only the defect, and “after three failed fix attempts on the same gate, stop and escalate to the human” (`PLAN.md:81`); G3 uses the sole-authority procedure in Finding 16.

7. **High (resolved 2026-08-22: the M1b fallback is a named alternate gate state) — The G3 fallback authorized proceeding while the written gate remained red.** (updated 2026-08-22: Round 9 citations.) Operating rule 5 registers `M1b-primary` among the qualification values (`PLAN.md:82`), and the sole G3 authority says G3.2 may produce “qualification `M1b-primary` when G3.2b passes” (`PLAN.md:413-418`); Appendix D.3 applies that result (`PLAN.md:517`).

8. **High (resolved 2026-08-22: an all-items checklist separates scientific and review status) — Gate, review, commit, ledger, and README state had no atomic acceptance rule.** (updated 2026-08-22: current citations.) The checklist says “all items required before a gate commit” and “No item may be waived” (`PLAN.md:106`), separating science, sol, kimi, ledger, README, and commit state. Finding 17 covers its incomplete enforcement.

9. **High (refuted 2026-08-22: human override — trust-model constants of a single-user repo; detection via git history and resumed reviewer sessions is the registered control; see tie-break batch 2) — Coder scope and unsuccessful-review containment remain unenforced.** (updated 2026-08-22: Round 9 human disposition.) Section 2b says the coder wrapper “refuses to launch” without an allowlist and calls uncontained drift “a hard wrapper failure” (`PLAN.md:104`, `PLAN.md:107`), while source still performs the allowlist check only after `codex exec` and deliberately preserves failed coder work (`tools/run_codex_agent.sh:47-85`). The human adjudication explicitly closes process#9 after considering batch 2's mandatory-allowlist middle path and diagnostic-preservation rationale (`docs/reviews/plan/tiebreaks.md:37-41`, `docs/reviews/plan/tiebreaks.md:47-49`; `PLAN.md:128`). The residual containment weakness is therefore an accepted trust-model risk, not an open blocker.

10. **High (resolved 2026-08-22: direct edits are restricted to non-implementation artifacts) — The orchestrator exception contradicted the fixed code-author role.** (updated 2026-08-22: Round 9 citations.) Under “Roles, fixed,” the orchestrator “does not write implementation code directly” (`PLAN.md:95`), and “Resolution scope” says implementation/test fixes “go through a coder brief” while direct edits are limited to non-implementation files (`PLAN.md:104`).

11. **Medium — Coder briefs, scope, and model provenance remain assertions rather than a contract.** (updated 2026-08-22: Round 9 re-verification.) Section 2b, “Roles, fixed,” says the coder runs `gpt-5.6-sol` at medium effort with a brief under `tools/codex-agents/`, and “Resolution scope” says every brief “MUST ship a scope allowlist” (`PLAN.md:96`, `PLAN.md:104`). No brief schema requires objective, forbidden paths, dependencies, acceptance tests, finding IDs, artifacts, stop conditions, or handoff; the wrapper still accepts environment model/effort overrides and an unsanitized name (`tools/run_codex_agent.sh:25-35`, `tools/run_codex_agent.sh:47-52`). The ledger's “Each entry records” schema requires neither brief hash nor actor configuration (`PLAN.md:124`). A glob allowlist alone cannot prove which authorized brief/model produced a diff.

12. **High (resolved 2026-08-22: Phase 5/7 review requirements and the Phase 5 dependency are explicit in prose) — Phase 5/7 could escape review and Phase 6 could bypass Phase 5.** (updated 2026-08-22: Round 9 citations.) “Cadence” names topics `tradeoff` and `report` (`PLAN.md:105`); Phase 5 says “after a sol review ... is accepted,” Phase 6 is “Only reached” after the reviewed tradeoff, and Phase 7 says the report “ships only after” review (`PLAN.md:436`, `PLAN.md:440`, `PLAN.md:458`).

13. **High (resolved 2026-08-22: Phase 6 now has an aggregate budget and matrix restart contract) — Phase 6 had no budget or restart envelope for the single device.** (updated 2026-08-22: Round 9 citations.) “Budget discipline” requires a pilot projection, a 4x timeout, and human escalation beyond 2x (`PLAN.md:108`); Phase 6 registers an “Aggregate phase budget 120 GPU-hours” (`PLAN.md:444`), and the run contract says a run writes a `DONE` marker and interrupted cells restart identically (`PLAN.md:151`). Actual GB10 fit remains pilot-dependent, but the denominator and restart rule exist.

14. **Medium (resolved 2026-08-22: rule 6 now explicitly scopes the Phase 6 exception) — The global determinism rule conflicted with Phase 6.** (updated 2026-08-22: Round 9 citations.) Operating rule 6 says “Phase 6 training runs are seed-logged ... and are not rule-6 regressions” (`PLAN.md:83`); Phase 6 repeats “determinism relaxed to seed-logged” while keeping proof tests fp32 (`PLAN.md:446`).

16. **High (resolved 2026-08-22: Phase 3 now declares one sole outcome authority with complete precedence) — G3's nominally single-valued procedure still had contradictory inputs and authorized rescue after a registered failure.** (updated 2026-08-22: Round 9 citations.) The “G3 outcome — SOLE AUTHORITY” block says it “supersedes every earlier phrasing,” fixes evaluation order/comparator/qualifications, and makes every red step terminal after one diagnosed rerun (`PLAN.md:408-418`). That precedence closes the bypass; Finding 35 retains the maintenance hazard from contradictory subordinate text.

17. **Medium — The gate checklist is still not mechanically coupled to commits or evidence.** (updated 2026-08-22: Round 9 re-verification.) Section 2b calls six items “all items required before a gate commit” and routes sol acceptance through `tools/check_acceptance.sh <phase>` (`PLAN.md:106`). The script still scores every incidental non-kimi markdown in a phase directory and checks kimi only by `*-kimi.md` presence (`tools/check_acceptance.sh:5-15`). It does not map exact registered topics, validate kimi structure or adjudication, or bind scientific gate artifacts, the ledger entry, README row, and proposed commit. README remains a bare status table (`README.md:47-58`). v1.12 now makes this same incomplete command the plan-phase authority (`PLAN.md:105`), increasing the impact of the gap.

18. **Medium (resolved 2026-08-22: the amendment prompt fragment exists) — The mandatory amendment-review path was not runnable.** (updated 2026-08-22: Round 9 citations.) The “Autonomy policy” says “a sol@xhigh review of it is run (topic `amendment`),” and the tracked `review-amendment.md` supplies the runnable rubric (`PLAN.md:116`; `tools/codex-prompts/review-amendment.md:1-12`). Finding 22 covers failure to use that path before activation.

19. **Medium — README transition triggers remain incomplete even though v1.9 can encode composite G3 results.** (updated 2026-08-22: Round 9 re-verification.) Operating rule 5 says “One commit per green gate” and defines status vocabulary, but never says when `in progress`, non-G3 `red`, or `killed` must be persisted (`PLAN.md:82`). README says only “Every green gate flips its row” (`README.md:58`). Phase 5 and Phase 7 exits still do not require their rows to change (`PLAN.md:436`, `PLAN.md:458`; `README.md:54-56`), and rows carry no evidence path, date, accepted review, or commit SHA. The governed restart surface can remain `not started` through active or terminal work.

20. **Low — Out-of-canonical review drift is again present.** (updated 2026-08-22: Round 9 observation.) Section 2b says “never edit repo files while a wrapper is running” (`PLAN.md:107`). Read-only `git status --short` again showed modified `docs/reviews/plan/spec.md:1` outside this canonical process review. It was left untouched; the dirty sibling prevents clean-state attestation even though status alone cannot prove wrapper overlap.

21. **High (resolved 2026-08-22: v1.9 ports the generic phase-topic fallback to kimi) — The mandatory phase-review cadence was unrunnable for kimi.** (updated 2026-08-22: Round 9 citations.) “Cadence” says Phase 0-4/6 and `tradeoff`/`report` use the generic `review-phase.md` fragment (`PLAN.md:105`); kimi now routes those missing literal topic fragments to that file (`tools/run_kimi_review.py:122-130`), matching sol (`tools/run_codex_review.sh:121-135`).

22. **Medium — v1.10 again activated before amendment review and leaves threshold provenance false.** (updated 2026-08-22: v1.12 fixes the stale Appendix-C sentence but repeats and worsens the audit breach.) The Autonomy policy says an amendment review “must be accepted BEFORE the amendment commit lands” and the ledger records “review-accepted-then-committed order” (`PLAN.md:116`). Commit `e7034af` activates v1.12—changing governed dtype/test semantics, Phase 4 optimizer details, and plan acceptance—without a tracked `docs/reviews/plan/amendment.md`. Worse, the “Amendment log” has no v1.12 entry at all: its newest entry is v1.11 (`PLAN.md:7-9`), even though Appendix C now calls that log “the sole provenance authority” (`PLAN.md:494`). The stale-version wording is resolved, but the operative amendment is absent from the authority that is supposed to expose post-hoc edits; git alone does not prove review-before-effect.

23. **High (resolved 2026-08-22: kimi completion/adjudication is now a pre-commit checklist item) — Kimi review could occur after gate acceptance.** (updated 2026-08-22: Round 9 citations.) The “Gate acceptance checklist” requires “the phase's kimi cross-review run before the commit with its confirmed high/critical findings resolved” (`PLAN.md:106`). That closes the timing bypass even though “Cross-model review” calls kimi advisory (`PLAN.md:110`); Finding 34 covers rule 9's wording.

24. **Low — Fresh-session fallback works, but its promised audit note still cannot be produced.** (updated 2026-08-22: Round 9 re-verification.) “Review-session continuity” promises that a fresh fallback is “noted in the round log” (`PLAN.md:112`). SID is loaded before prompt construction, but a failed resume retries with the already-built prompt that still says “your session context is intact” and carries no fallback flag (`tools/run_codex_review.sh:180-193`, `tools/run_codex_review.sh:294-320`). The generated round still cannot distinguish successful resume from continuity loss.

25. **Medium (resolved 2026-08-22: acceptance-tooling retro changes now require amendment review) — Retrospectives could change acceptance tooling without independent review.** (updated 2026-08-22: Round 9 citations.) The “Autonomy policy” says changes to the checker, tracker, or wrappers arising from retros “take effect only after an amendment review accepts them” (`PLAN.md:116`). That closes the acceptance-tooling limb; Finding 31 covers the remaining prompt/AGENTS limb under “Phase retrospectives” (`PLAN.md:114`).

26. **Medium — Rejected kimi sidecars demonstrably contaminate later context and metrics.** (updated 2026-08-22: Round 9 re-verification.) The wrapper file policy says reviewers write “only their canonical review file” (`PLAN.md:107`), yet kimi writes `<topic>-kimi.rejected.md` on validation failure (`tools/run_kimi_review.py:183-191`). All three tracked plan sidecars remain present. The context builder ingests every `docs/reviews/**/*.md` (`tools/run_kimi_review.py:40-45`), and metrics treat every recursive markdown as a review (`tools/agent_metrics.py:86-94`). Rejected prose therefore remains persistent reviewer input and bogus retrospective data.

27. **Medium — The first tie-break was executed through an unauditable path, and the human-trigger conflict is still live.** (updated 2026-08-22: the specific human escalation occurred, but the reusable tie-break path remains unauditable and the two trigger rules remain inconsistent.) “Cross-model review” requires kimi to receive “the finding, the fix or refutation evidence, and both arguments” and requires its verdict to be ledgered (`PLAN.md:110`). Both tie-break batches still store only verdict prose—no invocation command, prompt/mode, supplied evidence, raw response/log, run ID, or verification (`docs/reviews/plan/tiebreaks.md:3-45`); the tool still implements only scored topic review (`tools/run_kimi_review.py:94-130`). The human adjudication is now durably recorded (`docs/reviews/plan/tiebreaks.md:47-49`; `PLAN.md:128`), resolving this instance, but Section 2b triggers the human only after a disputed tie-break while the Autonomy policy says the mandatory touchpoint occurs after two deadlocked rounds (`PLAN.md:110`, `PLAN.md:116`). Future deadlocks still have conflicting triggers and no reproducible tie-break command.

28. **Medium (resolved 2026-08-22: v1.12 explicitly makes `tools/check_acceptance.sh plan` the plan-acceptance and Phase 0 entry condition) — The plan phase has no registered acceptance condition for entering Phase 0.** (updated 2026-08-22: Round 9 verification.) Section 2b, “Cadence,” now says “the plan itself is accepted when `tools/check_acceptance.sh plan` passes ... after which Phase 0 may begin” (`PLAN.md:105`). That supplies the previously absent governed transition. Finding 17 separately covers the command's incomplete exact-topic and evidence semantics; those limitations do not reopen this narrower no-condition finding.

29. **Medium — Required kimi phase reviews cannot see all gate-critical artifacts.** (updated 2026-08-22: Round 9 re-verification.) The checklist and “Cross-model review” require kimi on “the gate-critical work” (`PLAN.md:106`, `PLAN.md:110`), but its context inventory omits `results/*.md` and figures (`tools/run_kimi_review.py:40-45`), despite the phase rubric's “generated artifacts” requirement and Phase 5/7 deliverables (`tools/codex-prompts/review-phase.md:3`; `PLAN.md:434-436`, `PLAN.md:458`). The builder returns at the first 400 KB overflow, omitting every later file (`tools/run_kimi_review.py:56-75`). A structurally partial invocation can still satisfy the presence-only gate check.

30. **Low — Rule 3's freeze trigger is undefined for test-gated phases.** (updated 2026-08-22: Round 9 re-verification.) Operating rule 3 freezes thresholds when “the affected phase's first run has been launched” (`PLAN.md:80`). Phases 0-2 are primarily test/fixture governed and Phase 1 has no training run; neither the first pytest nor the first `make gate-N` is registered as that event, so a restart cannot determine whether prose-level test tolerances are frozen.

31. **Medium — Retrospectives may weaken reviewer/coder instructions without independent review.** (updated 2026-08-22: Round 9 re-verification.) “Phase retrospectives and agent evals” requires every optimization to land as an “AGENTS.md entry” or tooling/prompt diff (`PLAN.md:114`), while the Autonomy policy specifically review-gates only changes to the checker, tracker, and wrappers (`PLAN.md:116`). The retro rubric asks whether blame follows evidence and whether an optimization landed, not whether prompt/AGENTS changes preserve governance (`tools/codex-prompts/review-retro.md:5-11`). Such changes can govern the next phase without an independent sol process review.

32. **Medium — The kimi wrapper does not implement the binding anti-churn rule.** (updated 2026-08-22: Round 9 re-verification.) “Review-session continuity” gives kimi “the same anti-churn rule” limiting new findings to regressions or clear original-scope misses (`PLAN.md:112`). Its actual preamble preserves findings but instead emphasizes “finding what [sol] missed” and never states that limit (`tools/run_kimi_review.py:143-163`). Because confirmed kimi High/Critical claims require adjudication (`PLAN.md:110`), stateless review scope can still grow indefinitely.

33. **Low — Phase 5's pilot is underspecified for a matrix whose sequence lengths vary sixteen-fold.** (updated 2026-08-22: Round 9 re-verification.) “Budget discipline” requires a pilot-derived projection (`PLAN.md:108`), but Phase 5 names only “one pilot cell first” for 27 runs over `R in {2, 8, 32}` and 24 GPU-hours (`PLAN.md:434`). Task B contains R segments with 32-256-token delays (`PLAN.md:311-316`), so R=32 has about sixteen times R=2's segments. Without a named worst-case pilot or per-R scaling measurements, the single-Spark projection is not defensible ex ante.

34. **Low — Operating rule 9 still contradicts the mandatory second-reviewer role.** (updated 2026-08-22: Round 9 re-verification.) Operating rule 9 says “all reviews are sol adversarial reviews” (`PLAN.md:86`), while Section 2b calls kimi “the second, independent reviewer” and requires its cross-review before commit (`PLAN.md:106`, `PLAN.md:110`). The more specific checklist prevents a practical skip, but the global rule still denies the category it later mandates.

35. **Medium — The G3 sole-authority fix leaves materially contradictory subordinate text in the governing document.** (updated 2026-08-22: Round 9 re-verification.) The authoritative block says it “supersedes every earlier phrasing” (`PLAN.md:408`), resolving Finding 16's bypass. Yet rule 5 first lists only green/M1b/red before its broader enum (`PLAN.md:82`); Appendix C still says “B0-full minus M1” instead of the primary variant (`PLAN.md:503`); Appendix D says “stop at the first match,” invokes rule 4's three-attempt procedure for G3, and permits a wider model that “does not retroactively pass” after amendment (`PLAN.md:512`, `PLAN.md:520-521`). These dead contradictions remain a cold-start and future-edit hazard and should be diagnostic references to the sole authority, not competing instructions.

## Recommendations

1. Define and validate a coder-brief schema before Phase 0, including objective, forbidden paths, dependencies, acceptance tests, finding IDs, artifacts, stop conditions, handoff, brief hash, and explicit authorization for model/effort overrides (`PLAN.md:95-104`, `PLAN.md:124`; `tools/run_codex_agent.sh:25-52`).
2. Make `check_acceptance.sh` map each phase to exact registered sol/kimi topics, validate canonical structure and adjudication, and bind gate evidence, ledger state, README row, and proposed commit in one manifest (`PLAN.md:105-110`; `tools/check_acceptance.sh:1-16`; `README.md:45-58`).
3. Define README transition triggers for `in progress`, `red`, `killed`, and Phase 5/7 completion; add evidence path, accepted review round/score, date, and commit SHA (`PLAN.md:82`, `PLAN.md:432-458`; `README.md:45-58`).
4. Obey review-before-commit for the next amendment, add the missing v1.12 amendment-log entry, and require every entry to name the accepted amendment review/round/score, affected-phase launch evidence, exact old/new values, and activation SHA (`PLAN.md:7-9`, `PLAN.md:116`, `PLAN.md:494`).
5. When resume fails, rebuild the fresh prompt with an explicit continuity-loss flag and require the new round to record it (`PLAN.md:112`; `tools/run_codex_review.sh:180-193`, `tools/run_codex_review.sh:294-320`).
6. Store rejected kimi output outside `docs/reviews`, exclude it from context and metrics, and include required result documents/figures through an explicit artifact manifest before applying the context cap (`tools/run_kimi_review.py:40-75`, `tools/run_kimi_review.py:183-194`; `tools/agent_metrics.py:86-94`).
7. Implement a runnable tie-break command/prompt that persists the finding, both arguments, evidence bundle, raw response/log, model, and verification; reconcile Section 2b's post-tie-break human trigger with the Autonomy policy's two-round trigger (`PLAN.md:110`, `PLAN.md:116`; `docs/reviews/plan/tiebreaks.md:3-49`).
8. Register first-test freeze triggers for Phases 0-2 before Phase 0 begins (`PLAN.md:80`).
9. Extend amendment review to retro-generated reviewer/coder prompt and AGENTS changes, and put the binding anti-churn clause directly in kimi's prompt (`PLAN.md:112-116`; `tools/codex-prompts/review-retro.md:5-11`; `tools/run_kimi_review.py:143-163`).
10. Name the Phase 5 pilot cell and require measured or registered scaling projections for R=2, 8, and 32 before accepting the 24 GPU-hour estimate (`PLAN.md:108`, `PLAN.md:311-316`, `PLAN.md:434`).
11. Change operating rule 9 to “all reviews of record are sol” so it no longer contradicts mandatory kimi cross-review (`PLAN.md:86`, `PLAN.md:106-110`).
12. Rewrite rule 5, Appendix C G3.4, and Appendix D to reference the Phase 3 sole-authority block without restating contradictory states, comparators, retries, or continuation outcomes (`PLAN.md:82`, `PLAN.md:408-418`, `PLAN.md:503`, `PLAN.md:510-523`).

## Evidence consulted

- `PLAN.md`, read in full, lines 1-554; SHA-256 `e771d1eb8b8b8459adbcc4adef9a1cbe31ea3abded71b319047cc64087cafee3`.
- `README.md`, read in full, lines 1-66; SHA-256 `9a4a79b70be89eb584ee563fefd6160bf0d5f374cb77a7bd158f1777d3212430`.
- `docs/reviews/plan/process.md`, the wrapper-supplied Round 1-8 content; current science/spec/process sol and kimi headers; all three tracked `*-kimi.rejected.md` sidecars; and both tie-break batches plus the human adjudication in `docs/reviews/plan/tiebreaks.md`.
- `tools/check_acceptance.sh`, `tools/run_codex_agent.sh`, `tools/run_codex_review.sh`, `tools/run_kimi_review.py`, `tools/review_diff_allowlist.py`, `tools/review_round_tracking.py`, `tools/check_review_scores.py`, `tools/agent_metrics.py`, and the complete tracked prompt inventory.
- `AGENTS.md`, `CLAUDE.md`, `.gitignore`, and the machine-local `docs/reviews/.sessions/` inventory.
- Read-only `git status`, `git log`, `git diff 9b2eb7d..e7034af`, `git show`, `git blame`, and `git ls-files`; commit `e7034af` changes PLAN/AGENTS/review artifacts but no tool or README file, while the sibling `docs/reviews/plan/spec.md` remained modified and was left untouched.
- Read-only inspection of `results/logs/codex-plan-{science,spec,process}.log` and `docs/reviews/.sessions/`; persistent sol logs and session IDs exist, while the top ledger state still supplies prose rather than exact commands, per-topic artifacts, or session IDs.
- Static re-verification of the unchanged score parser, round tracker, coder/reviewer failure paths, acceptance script, kimi context/sidecar behavior, metrics discovery, prompts, and G3 subordinate text. The human override closes process#1/#2/#4/#9 as accepted trust-model risks; it does not change the source behavior.
- Direct inspection of `tools/check_acceptance.sh plan` semantics: it checks incidental sol markdown plus kimi-file presence rather than an exact registered plan manifest; the current science score is 92, spec is 89, and this process round remains below 90.
- Matrix arithmetic from the plan: Phase 3 enumerates 96 runs (66 Task A and 30 Task M); Phase 5 enumerates 27 Task B runs, and its R=32 sequences contain sixteen times as many full segments as R=2. No pilot exists, so actual GB10 throughput or fit against the 24/72/120 GPU-hour budgets cannot be verified.
- No implementation, experiment output, gate artifact, Phase 3/5 pilot, training checkpoint, retrospective, accepted plan-phase manifest, v1.12 amendment-log entry, or tracked amendment review exists; no scientific gate or compute projection could be replayed.
