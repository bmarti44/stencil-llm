# Process Review — plan

**Score:** 89 / 100
**Verdict:** CONDITIONAL PASS (75–89)
**Reviewer model:** codex/gpt-5.6-sol
**Date:** 2026-08-22

## Round log

### Round 15 — 2026-08-22 (codex/gpt-5.6-sol)
- Score: 89 / 100 (delta vs prior round: +0)
- Addressed since prior round:
  - Commit `1e08938` cleanly separates science, process, state, and amendment history into `PLAN.md` plus `plan/{PROTOCOL,LEDGER,AMENDMENTS}.md`, migrates the review/tie-break paths and held session IDs, and updates the wrappers and README to the new authority model (`PLAN.md:5`, `PLAN.md:99-107`; `plan/PROTOCOL.md:1-30`; `plan/LEDGER.md:1-14`; `README.md:5`, `README.md:43`).
  - v1.17 is the first amendment to exercise the binding working-tree review path: the pre-commit amendment review reached 92 after catching two High relocation defects, and `tools/check_acceptance.sh plan` now passes amendment/science/spec at 92 and fails only this process review at 89 (`plan/reviews/plan/amendment.md:10-18`, `plan/LEDGER.md:13`; `tools/check_acceptance.sh:10-27`).
  - Most paths underlying process#39 were normalized to `plan/tiebreaks/`; kimi's registered-cap context now contains all four governing/state/history files, and the machine-local held reviewer IDs exist at the migrated location (`plan/AMENDMENTS.md:9-16`; `tools/run_kimi_review.py:44-50`; `plan/reviews/.sessions/`).
- New or remaining:
  - No High/Critical finding is open. The same substantive tail remains: coder provenance, continuity-loss logging, reusable tie-break validation, kimi artifact coverage, retro-generated AGENTS changes, G3 subordinate contradictions, and adaptive-lens identity.
  - Process#39 remains Low because the binding second human adjudication still points to nonexistent `docs/tiebreaks/`, and the batch-3 ledger entry names only bare `tiebreaks.md`. New Low process#40 records false inherited self-references and the inaccurate “verbatim/content unchanged” provenance claim introduced by the extraction (`plan/tiebreaks/plan.md:92`; `plan/LEDGER.md:7`, `plan/LEDGER.md:17`; `plan/PROTOCOL.md:3`, `plan/PROTOCOL.md:9`; `PLAN.md:101`).

### Round 14 — 2026-08-22 (codex/gpt-5.6-sol)
- Score: 89 / 100 (delta vs prior round: +17)
- Addressed since prior round:
  - Commit `0a28d36` executes the required second human touchpoint, concedes the false amendment-deadlock premise, makes working-tree/draft review binding before every future amendment commit, and gives finding-specific final dispositions for process#17/#22 (`PLAN.md:9`, `PLAN.md:121`, `docs/tiebreaks/plan.md:89-94`).
  - The same commit fixes process#38 at the artifact-classification boundary: tie-break evidence moved to `docs/tiebreaks/`, and acceptance now classifies review files by reviewer frontmatter while rejecting unexpected layouts (`tools/check_acceptance.sh:12-27`; `docs/tiebreaks/plan-prompt-3.md:1-7`). A direct replay no longer sees the prompt and fails only on this process review's prior 72 score.
- New or remaining:
  - No High/Critical finding remains open. Promotion remains conditional because coder provenance, continuity-loss logging, reusable tie-break validation, kimi artifact coverage, retro-generated AGENTS changes, G3 subordinate contradictions, and adaptive-lens identity remain open.
  - New Low regression process#39: v1.16 moved the tie-break evidence but left several governing amendment/ledger entries pointing at the deleted `docs/reviews/plan/tiebreaks.md` and `tiebreak-prompt-3.md` paths (`PLAN.md:14`, `PLAN.md:16`, `PLAN.md:134`, `PLAN.md:138`, `PLAN.md:140`).

### Round 13 — 2026-08-22 (codex/gpt-5.6-sol)
- Score: 72 / 100 (delta vs prior round: -17)
- Addressed since prior round:
  - Commits `9f9f6f5` and `dada4d5` make batch 3 materially auditable: the exact prompt was committed before execution, the verbatim prompt and raw kimi response were preserved, the ruling was ledgered, and the top `STATE:` now carries process 89 with Round 13 as the next command (`docs/reviews/plan/tiebreak-prompt-3.md:1-7`; `docs/reviews/plan/tiebreaks.md:52-87`; `PLAN.md:132`).
  - `build_context` now skips an oversized file and continues considering later files, closing that limb of process#29; process#37 is resolved because the stale Round-11 restart state was explicitly superseded (`tools/run_kimi_review.py:60-79`; `PLAN.md:132-133`).
- New or remaining:
  - New High regression process#38: the committed `tiebreak-prompt-3.md` matches `check_acceptance.sh`'s indiscriminate sol-review glob, so a direct plan-acceptance replay now hard-fails that unscored prompt artifact before Phase 0 can begin (`tools/check_acceptance.sh:5-15`; `docs/reviews/plan/tiebreak-prompt-3.md:1-7`).
  - I do not concur with batch 3's refutations of process#17/#22: the first ruling answers a malicious-owner/pre-commit-hook strawman while the new replay demonstrates the requested exact-artifact failure; the second rests on a false deadlock premise because the amendment rubric expressly reviews a draft or working-tree diff before it takes effect. Under Section 2b, this dispute now requires the human touchpoint (`PLAN.md:114`, `PLAN.md:120`; `tools/codex-prompts/review-amendment.md:3-5`).

### Round 12 — 2026-08-22 (codex/gpt-5.6-sol)
- Score: 89 / 100 (delta vs prior round: +0)
- Addressed since prior round:
  - Commit `4adc7d5` aligns Appendix C's freeze sentence and G3.4 comparator with their governing authorities, identifies the Phase 5 pilot as the primary oscillatory variant at R=32/seed 0, and brings README's transition sentence into line with rule 5 (`PLAN.md:9`, `PLAN.md:440`, `PLAN.md:500`, `PLAN.md:509`; `README.md:58`).
  - v1.15 makes coder-brief sections nonempty, forces registered phase-style kimi topics through `review-phase.md`, and rejects dirty prompt paths in the tie-break runner (`tools/run_codex_agent.sh:44-57`; `tools/run_kimi_review.py:126-136`; `tools/run_tiebreak.py:17-23`).
  - Findings 19, 30, and 33 are now resolved after direct source verification; Finding 35 is narrowed because Appendix C's comparator is fixed, and Finding 36 is narrowed because the wrapper now implements the generic-lens routing for registered phase-style topics.
- New or remaining:
  - No High/Critical finding is open, but the same promotion blockers remain: gate acceptance is not an atomic evidence check, and v1.15 again took effect before the amendment review that the Autonomy policy says must precede the commit.
  - The tie-break runner's prompt check is bypassable for ignored or out-of-repository paths and still lacks transaction/schema/ledger controls; kimi context still omits figures and stops at the first oversized file; AGENTS.md retro changes and review fallback loss remain unaudited.
  - New regression: v1.15 commits the completed Round 11 process review at 89 but leaves the top ledger `STATE:` at process 87 with Round 11 still named as the next command (`PLAN.md:128`, `PLAN.md:132`; `docs/reviews/plan/process.md:22`).

### Round 11 — 2026-08-22 (codex/gpt-5.6-sol)
- Score: 89 / 100 (delta vs prior round: +2)
- Addressed since prior round:
  - Commit `9fea8e5` reconciles operating rule 9 with the mandatory kimi role, completes the governing README transition triggers, relocates continuity-loss disclosure to the wrapper log/ledger, and selects the longest Phase 5 sequence cell for the pilot (`PLAN.md:85`, `PLAN.md:89`, `PLAN.md:115`, `PLAN.md:439`).
  - v1.14 moves result/retro markdown ahead of bulky review history in kimi context, adds a generic-kimi coverage rule for adaptive lenses, adds a runnable tie-break client, and validates the five required coder-brief headings before launch (`PLAN.md:108`; `tools/run_kimi_review.py:40-79`; `tools/run_tiebreak.py:1-33`; `tools/run_codex_agent.sh:44-50`).
  - Rule 3 now names the coder/run write-ahead event, and Appendix D repeats the Phase 3 sole-authority precedence (`PLAN.md:83`, `PLAN.md:517`).
- New or remaining:
  - No High/Critical finding is open, but promotion remains conditional: atomic gate acceptance is still explicitly declined, and v1.14 again took effect without the mandatory pre-commit amendment review.
  - The generic-kimi backstop is prose-only—the wrapper still selects an existing bespoke topic fragment and acceptance checks only kimi-file presence—and the new tie-break runner neither proves the prompt was committed nor validates its target, evidence schema, or verdict.
  - Brief validation accepts empty headings, Appendix C retains the old first-run freeze trigger and M1-only G3.4 comparator, README's own footer/rows remain stale, and Phase 5's pilot still omits the variant.

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

1. **High (refuted 2026-08-22: human override — trust-model constants of a single-user repo; detection via git history and resumed reviewer sessions is the registered control; see tie-break batch 2) — Review acceptance still permits direct-checker threshold lowering and forged closure.** (updated 2026-08-22: Round 15 citations.) “Finding identity and closure” says “A human may override a deadlocked finding; the override is recorded in the ledger with rationale” (`plan/PROTOCOL.md:17`). The named adjudication and matching ledger history remain present (`plan/tiebreaks/plan.md:47-49`; `plan/LEDGER.md:20`). That terminal disposition was expressly limited to process#1/#2/#4/#9 and remains controlling.

2. **High (refuted 2026-08-22: human override — trust-model constants of a single-user repo; detection via git history and resumed reviewer sessions is the registered control; see tie-break batch 2) — The executed process#2 tie-break refutes a strawman while silent finding substitution remains mechanically accepted.** (updated 2026-08-22: Round 15 citations.) “Context carry-over” calls unannotated edits “a protocol violation the next round's reviewer is instructed to flag,” while “Finding identity and closure” permits a recorded human override (`plan/PROTOCOL.md:16-17`). The human specifically closed process#2 (`plan/tiebreaks/plan.md:47-49`; `plan/LEDGER.md:20`); this finding remains refuted.

3. **High (resolved 2026-08-22: stable IDs and reviewer-concurrence closure are explicit in the governing prose) — Refutation was unilateral and had no durable finding identity.** (updated 2026-08-22: Round 15 citations.) “Finding identity and closure” says “a finding's identity is `<topic>#<number>`” and only a subsequent reviewer may close it (`plan/PROTOCOL.md:17`); the reviewer protocol independently says “Never mark a finding resolved on the orchestrator's claim alone” (`tools/codex-prompts/_common-header.md:28`). The prose-level gap stays closed.

4. **High (refuted 2026-08-22: human override — trust-model constants of a single-user repo; detection via git history and resumed reviewer sessions is the registered control; see tie-break batch 2) — The ledger still cannot deliver its promised exact cold restart despite resuming write-ahead.** (updated 2026-08-22: Round 15 citations.) “Work log and ledger” promises “a restarted session must be able to resume from this file alone,” while its reconciliation step consults logs, artifacts, and `git status` (`plan/LEDGER.md:7-9`). The human accepted that ledger/log/git stack (`plan/tiebreaks/plan.md:31-35`, `plan/tiebreaks/plan.md:47-49`); this finding remains refuted. Finding 37 records the narrower STATE-maintenance repair.

5. **High (resolved 2026-08-22: one absolute freeze rule and a tracked baseline exist) — Threshold pre-registration was contradictory and lacked a repository baseline.** (updated 2026-08-22: Round 15 citations.) Operating rule 3 says thresholds are “frozen permanently” at the first coder/run write-ahead (`PLAN.md:88`), commit `18bca48` supplies the tracked baseline, and Appendix C repeats “launching a coder brief or a run ... whichever comes first” (`PLAN.md:467`). The former contradiction stays closed.

6. **High (resolved 2026-08-22: non-G3 gates have a bounded failure procedure) — Rule 4 was impossible to follow for five gates.** (updated 2026-08-22: Round 15 citation.) Operating rule 4 says that after “three failed fix attempts on the same gate, stop and escalate to the human” for G0/G1/G2/G4/G6 (`PLAN.md:89`). G3 uses the sole-authority procedure.

7. **High (resolved 2026-08-22: the M1b fallback is a named alternate gate state) — The G3 fallback authorized proceeding while the written gate remained red.** (updated 2026-08-22: Round 15 citations.) Rule 5 registers “M1b-primary” among the qualification values (`PLAN.md:90`), the sole G3 authority produces that qualification when G3.2b passes (`PLAN.md:386-391`), and Appendix D.3 says to “contribute qualification `M1b-primary`” (`PLAN.md:490`).

8. **High (resolved 2026-08-22: an all-items checklist separates scientific and review status) — Gate, review, commit, ledger, and README state had no atomic acceptance rule.** (updated 2026-08-22: Round 15 citation.) The “Gate acceptance checklist” calls its six items “all items required before a gate commit” and says “No item may be waived” (`plan/PROTOCOL.md:20`). Finding 17 records the final human disposition of mechanical enforcement; the prose-level separation stays closed.

9. **High (refuted 2026-08-22: human override — trust-model constants of a single-user repo; detection via git history and resumed reviewer sessions is the registered control; see tie-break batch 2) — Coder scope and unsuccessful-review containment remain unenforced.** (updated 2026-08-22: Round 15 citations.) “Resolution scope” says the wrapper “refuses to launch” without an allowlist, and the file policy calls uncontained drift “a hard wrapper failure” (`plan/PROTOCOL.md:18`, `plan/PROTOCOL.md:21`). The human-approved middle path remains recorded (`plan/tiebreaks/plan.md:37-49`; `plan/LEDGER.md:20-21`); this finding stays refuted. Finding 11 reviews the narrower brief-contract/provenance residue.

10. **High (resolved 2026-08-22: direct edits are restricted to non-implementation artifacts) — The orchestrator exception contradicted the fixed code-author role.** (updated 2026-08-22: Round 15 citations.) Under “Roles, fixed,” the orchestrator “does not write implementation code directly” (`plan/PROTOCOL.md:9`), and “Resolution scope” routes implementation and tests through coder briefs (`plan/PROTOCOL.md:18`).

11. **Medium — Coder briefs, scope, and model provenance remain assertions rather than a contract.** (updated 2026-08-22: v1.17 moves the contract but does not harden it.) “Resolution scope” requires “the objective, the allowlist, the tests to write first, the acceptance command, and the ledger handoff” (`plan/PROTOCOL.md:18`). The wrapper rejects a literally empty section, but any nonblank comment passes; the external `.allow` file is checked only after `codex exec`, the agent name is unsanitized, and environment model/effort overrides remain unledgered (`tools/run_codex_agent.sh:25-32`, `tools/run_codex_agent.sh:44-70`, `tools/run_codex_agent.sh:76-99`). “Each entry records” still omits brief/allowlist hashes and actor configuration (`plan/LEDGER.md:9`). A cold session cannot prove which substantive brief, scope, or model produced a diff.

12. **High (resolved 2026-08-22: Phase 5/7 review requirements and the Phase 5 dependency are explicit in prose) — Phase 5/7 could escape review and Phase 6 could bypass Phase 5.** (updated 2026-08-22: Round 15 citations.) “Cadence” requires “at minimum one review per phase before its exit commit” (`plan/PROTOCOL.md:19`); Phase 5 exits after an accepted review, Phase 6 is “Only reached” after that tradeoff, and Phase 7 ships only after review (`PLAN.md:409`, `PLAN.md:413`, `PLAN.md:431`).

13. **High (resolved 2026-08-22: Phase 6 now has an aggregate budget and matrix restart contract) — Phase 6 had no budget or restart envelope for the single device.** (updated 2026-08-22: Round 15 citations.) “Budget discipline” requires a pilot projection and a timeout “4x its pilot estimate” (`plan/PROTOCOL.md:22`); Phase 6 registers 120 GPU-hours (`PLAN.md:417`), and the determinism contract requires `DONE`-based recovery (`PLAN.md:119`).

14. **Medium (resolved 2026-08-22: rule 6 now explicitly scopes the Phase 6 exception) — The global determinism rule conflicted with Phase 6.** (updated 2026-08-22: Round 15 citations.) Rule 6 says seed-logged Phase 6 training runs “are not rule-6 regressions” (`PLAN.md:91`), while Phase 6 keeps proof tests fp32 (`PLAN.md:419`).

16. **High (resolved 2026-08-22: Phase 3 now declares one sole outcome authority with complete precedence) — G3's nominally single-valued procedure still had contradictory inputs and authorized rescue after a registered failure.** (updated 2026-08-22: Round 15 citations.) The “G3 outcome — SOLE AUTHORITY” block says it “supersedes every earlier phrasing,” fixes ordering/comparator/qualifications, and makes red terminal after one diagnosed rerun (`PLAN.md:381-391`). Finding 35 covers the remaining duplicate-text hazard.

17. **Medium (resolved 2026-08-22: exact review-artifact classification implemented; final human adjudication accepts the remaining non-atomic checklist as a trust boundary) — The gate checklist is still not mechanically coupled to commits or evidence.** (updated 2026-08-22: Round 15 re-verification.) The checklist still calls its six items “all items required before a gate commit” and says “No item may be waived” (`plan/PROTOCOL.md:20`). `check_acceptance.sh` rejects unexpected review-directory artifacts, score-checks codex-frontmatter files, and requires both codex and kimi identities (`tools/check_acceptance.sh:12-27`), while the final human ruling explicitly “Declined ... the full atomic evidence-parsing transaction beyond the exact-artifact validation now implemented” (`plan/tiebreaks/plan.md:89-94`). That terminal scope remains registered in the v1.16 amendment summary (`plan/AMENDMENTS.md:9`); Finding 36 retains the distinct topic/lens-identity gap.

18. **Medium (resolved 2026-08-22: the amendment prompt fragment exists) — The mandatory amendment-review path was not runnable.** (updated 2026-08-22: Round 15 citations.) The “Autonomy policy” requires a sol@xhigh review with topic `amendment` (`plan/PROTOCOL.md:30`), and `review-amendment.md` instructs the reviewer to inspect “the amendment's diff ... or the draft text” (`tools/codex-prompts/review-amendment.md:3-5`). Finding 22 records the live sequencing verification.

19. **Medium (resolved 2026-08-22: v1.15 makes README's own transition sentence match every rule-5 trigger) — README transition triggers remain incomplete even though v1.9 can encode composite G3 results.** (updated 2026-08-22: Round 15 citations.) Rule 5 says “entering a phase flips its row to in progress” and also names gate, kill, and document-commit transitions (`PLAN.md:90`). README says “Rows update on every state change per PLAN.md rule 5” and repeats all four classes (`README.md:58`). The trigger mismatch stays closed.

20. **Low (refuted 2026-08-22: the Round 11 worktree was clean and the ledger explains the prior serialized sibling state) — Out-of-canonical review drift is again present.** (updated 2026-08-22: Round 15 verification.) The file policy says “never edit repo files while a wrapper is running” (`plan/PROTOCOL.md:21`). Read-only `git status --short` was clean before this canonical edit. No current drift supports this finding.

21. **High (resolved 2026-08-22: v1.9 ports the generic phase-topic fallback to kimi) — The mandatory phase-review cadence was unrunnable for kimi.** (updated 2026-08-22: Round 15 citations.) “Cadence” says kimi “ALWAYS runs the generic `review-phase.md` lens” for a phase (`plan/PROTOCOL.md:19`), and the wrapper unconditionally selects it for topics beginning `phase` plus `tradeoff` and `report` (`tools/run_kimi_review.py:126-136`). Finding 36 covers acceptance binding, not command runnability.

22. **Medium (resolved 2026-08-22: human adjudication concedes the sequencing defect and makes working-tree/draft review binding before future amendment commits) — v1.10 again activated before amendment review and leaves threshold provenance false.** (updated 2026-08-22: v1.17 is the first direct operational proof of the repair.) The “Autonomy policy” says sequencing is “binding without exception since the v1.16 human ruling” and review “must be accepted BEFORE the amendment commit lands” from a working-tree diff or draft (`plan/PROTOCOL.md:30`). The v1.17 amendment review reached 92 before commit `1e08938`, after catching two High path defects in the draft (`plan/reviews/plan/amendment.md:10-18`; `plan/LEDGER.md:13-14`). That verifies the live rule rather than relying only on the human claim; the historical breaches remain auditable in `plan/AMENDMENTS.md`.

23. **High (resolved 2026-08-22: kimi completion/adjudication is now a pre-commit checklist item) — Kimi review could occur after gate acceptance.** (updated 2026-08-22: Round 15 citations.) The checklist requires kimi “before the commit” with confirmed High/Critical findings resolved (`plan/PROTOCOL.md:20`); “Cross-model review” remains advisory but mandatory (`plan/PROTOCOL.md:24`). Finding 17 records the final enforcement-scope disposition.

24. **Low — Fresh-session fallback works, but its promised audit note still cannot be produced.** (updated 2026-08-22: v1.17 migrates held-session paths but leaves fallback behavior unchanged.) “Review-session continuity” requires a fresh fallback to be “noted in the wrapper log and the ledger” (`plan/PROTOCOL.md:26`). The wrapper emits the warning only to stderr, retries with the already-built continuity prompt, overwrites the codex-output log, and performs no ledger update (`tools/run_codex_review.sh:180-193`, `tools/run_codex_review.sh:294-320`). The held IDs exist under `plan/reviews/.sessions/`, but if one becomes unusable the named durable audit surfaces still depend on an unvalidated outer/manual action.

25. **Medium (resolved 2026-08-22: acceptance-tooling retro changes now require amendment review) — Retrospectives could change acceptance tooling without independent review.** (updated 2026-08-22: Round 15 citations.) The “Autonomy policy” review-gates checker, tracker, wrapper, and reviewer/coder prompt changes arising from retros (`plan/PROTOCOL.md:30`). Finding 31 covers the remaining AGENTS.md limb under “Phase retrospectives” (`plan/PROTOCOL.md:28`).

26. **Medium (resolved 2026-08-22: v1.13 excludes rejected candidates from both kimi context and agent metrics) — Rejected kimi sidecars demonstrably contaminate later context and metrics.** (updated 2026-08-22: Round 15 re-verification.) The file policy says reviewers “write only their canonical review file” (`plan/PROTOCOL.md:21`). Kimi still saves a rejected sidecar (`tools/run_kimi_review.py:195-206`), but context skips `*.rejected.md` and metrics excludes rejected/tie-break files (`tools/run_kimi_review.py:60-79`; `tools/agent_metrics.py:88-94`). The contamination defect stays closed.

27. **Medium — The first tie-break was executed through an unauditable path, and the human-trigger conflict is still live.** (updated 2026-08-22: v1.17 normalizes paths but does not harden the reusable transaction.) “Cross-model review” requires kimi to receive “the finding, the fix or refutation evidence, and both arguments,” with the verdict executed and ledgered (`plan/PROTOCOL.md:24`). Batch 3 has a verified precommitted prompt, raw response, and ledgered human disposition (`plan/tiebreaks/plan-prompt-3.md:1-7`; `plan/tiebreaks/plan.md:52-94`; `plan/LEDGER.md:16-17`). The runner still ignores `git status` errors, permits ignored/out-of-repository prompts and arbitrary outputs, takes no repo lock, validates no evidence/verdict schema, and performs no ledger or next-sol verification (`tools/run_tiebreak.py:4-35`). The reusable trigger remains contradictory: “Cross-model review” waits until the next sol round disputes an executed tie-break, while the “Autonomy policy” requires the human after two deadlocked rounds (`plan/PROTOCOL.md:24`, `plan/PROTOCOL.md:30`).

28. **Medium (resolved 2026-08-22: v1.12 explicitly makes `tools/check_acceptance.sh plan` the plan-acceptance and Phase 0 entry condition) — The plan phase has no registered acceptance condition for entering Phase 0.** (updated 2026-08-22: Round 15 citation.) “Cadence” says the plan is accepted when `tools/check_acceptance.sh plan` passes, “after which Phase 0 may begin” (`plan/PROTOCOL.md:19`). Finding 36 covers the remaining lens/topic binding.

29. **Medium — Required kimi phase reviews cannot see all gate-critical artifacts.** (updated 2026-08-22: v1.17 guarantees the four governing/state files but not the phase evidence surface.) “Cross-model review” requires kimi “on the gate-critical work” (`plan/PROTOCOL.md:24`). A direct 400 KB replay now contains PLAN.md, PROTOCOL.md, LEDGER.md, and AMENDMENTS.md, and `build_context` continues after oversized files (`tools/run_kimi_review.py:44-50`, `tools/run_kimi_review.py:60-79`). Figures remain absent from `CONTEXT_GLOBS`, however, and no per-phase manifest declares which result markdown, figure, or rendered description is mandatory (`tools/run_kimi_review.py:40-50`). A structurally incomplete invocation can still produce a qualifying reviewer-frontmatter file under `check_acceptance.sh` (`tools/check_acceptance.sh:18-26`).

30. **Low (resolved 2026-08-22: v1.15 makes Appendix C repeat rule 3's coder-or-run write-ahead trigger) — Rule 3's freeze trigger is undefined for test-gated phases.** (updated 2026-08-22: Round 15 citations.) Rule 3 freezes at “the first write-ahead ledger entry launching either a coder brief or a run” (`PLAN.md:88`), and Appendix C repeats “launching a coder brief or a run ... whichever comes first” (`PLAN.md:467`). The ambiguity stays closed.

31. **Medium — Retrospectives may weaken reviewer/coder instructions without independent review.** (updated 2026-08-22: v1.17 moves but does not close the policy boundary.) “Phase retrospectives and agent evals” requires every optimization to land as an “AGENTS.md entry” or tooling/prompt diff (`plan/PROTOCOL.md:28`). The “Autonomy policy” review-gates tools and prompt fragments but not AGENTS.md (`plan/PROTOCOL.md:30`), and the retro rubric asks whether an optimization landed but not whether an AGENTS change preserves governance (`tools/codex-prompts/review-retro.md:5-11`). Auto-loaded instructions can still change before the next phase without independent process review.

32. **Medium (resolved 2026-08-22: v1.13 puts the binding anti-churn limit directly in kimi's resumed-round prompt) — The kimi wrapper does not implement the binding anti-churn rule.** (updated 2026-08-22: Round 15 citations.) “Review-session continuity” binds kimi to the same anti-churn rule (`plan/PROTOCOL.md:26`), and its resumed-round prompt states that restriction directly (`tools/run_kimi_review.py:149-153`).

33. **Low (resolved 2026-08-22: v1.15 identifies the pilot as the primary oscillatory variant at R=32, seed 0) — Phase 5's pilot is underspecified for a matrix whose sequence lengths vary sixteen-fold.** (updated 2026-08-22: Round 15 citations.) “Budget discipline” requires a pilot-derived projection (`plan/PROTOCOL.md:22`), and Phase 5 selects “the primary oscillatory variant at the longest cell, R = 32, seed 0” (`PLAN.md:407`). The pilot cell stays fully identified by G3's primary-variant outcome.

34. **Low (resolved 2026-08-22: v1.14 names sol as reviewer of record and kimi as the mandatory second reviewer) — Operating rule 9 still contradicts the mandatory second-reviewer role.** (updated 2026-08-22: Round 15 citations.) Rule 9 says sol is reviewer of record and kimi is the “mandatory cross-model second reviewer” (`PLAN.md:94`), matching the checklist and “Cross-model review” (`plan/PROTOCOL.md:20`, `plan/PROTOCOL.md:24`). The contradiction stays closed.

35. **Medium — The G3 sole-authority fix leaves materially contradictory subordinate text in the governing document.** (updated 2026-08-22: v1.17 leaves the science text unchanged.) The sole-authority block says it “supersedes every earlier phrasing” and permits one diagnosed rerun before kill (`PLAN.md:381-391`). The immediately preceding G3.4 bullet still says “M1 within 3 pts of B0-full” rather than the primary variant (`PLAN.md:377`); Appendix D permits a wide-model continuation that “does not retroactively pass” the registered 64-pair spec and gives isolated G3.3 three attempts via rule 4 (`PLAN.md:493-494`). Appendix C is correct (`PLAN.md:476`), but an agent still encounters contradictory comparator, continuation, and retry instructions in live subordinate text.

36. **Medium — Adaptive review lenses are not bound to gate acceptance or independently coverage-checked.** (updated 2026-08-22: v1.17 migrates the artifacts but does not add topic/lens binding.) “Cadence” says a phase's kimi review “ALWAYS runs the generic `review-phase.md` lens” and requires the adaptive sol lens/rationale in the write-ahead entry (`plan/PROTOCOL.md:19`). The wrapper forces the generic lens for `phase*`, `tradeoff`, and `report` (`tools/run_kimi_review.py:126-136`), but acceptance counts any file declaring `kimi/` and any scored file declaring `codex/`; it requires neither the registered phase topic nor the adaptive lens slug/rationale/hash (`tools/check_acceptance.sh:12-26`). Exact artifact classification therefore does not prove the registered coverage command was used.

37. **Medium (resolved 2026-08-22: `dada4d5` supersedes the stale state with process 89 and Round 13 as the next command) — v1.15 leaves the top restart state stale after committing Round 11.** (updated 2026-08-22: Round 15 verification.) “Work log and ledger” requires updates when “finishing a review round” and says the top `STATE:` carries “latest review scores” and “the exact next command” (`plan/LEDGER.md:7-9`). The migrated top entry records process 89 at Round 14 and names this Round 15 command, with the prior state explicitly superseded (`plan/LEDGER.md:13-14`). The minimal STATE convention remains current entering this review.

38. **High (resolved 2026-08-22: v1.16 relocates tie-break evidence and frontmatter-classifies review artifacts; direct acceptance replay no longer sees the prompt) — Batch-3 prompt artifact makes plan acceptance unconditionally fail.** (updated 2026-08-22: Round 15 direct verification.) “Cadence” still makes `tools/check_acceptance.sh plan` the condition “after which Phase 0 may begin” (`plan/PROTOCOL.md:19`). The prompt now lives at `plan/tiebreaks/plan-prompt-3.md`, outside the review namespace (`plan/tiebreaks/plan-prompt-3.md:1-7`), while acceptance frontmatter-classifies codex/kimi reviews and rejects unexpected layouts (`tools/check_acceptance.sh:12-27`). A direct replay after v1.17 produced no path/layout failure and failed only on the process review's prior 89 score. The active pipeline break stays fixed.

39. **Low — v1.16 relocation leaves governing tie-break references pointing to deleted paths.** (updated 2026-08-22: v1.17 fixes most historical paths but leaves two audit references stale or ambiguous.) The v1.17 amendment says “all review/tie-break/session paths moved from docs/ into plan/” (`plan/AMENDMENTS.md:7`), and the current ledger correctly cites `plan/tiebreaks/plan.md` (`plan/LEDGER.md:16`). Most old amendment and ledger paths are now normalized, but the binding second human adjudication still says artifacts moved to nonexistent `docs/tiebreaks/` (`plan/tiebreaks/plan.md:92`), and the batch-3 ledger entry says the raw verdict is in bare `tiebreaks.md` rather than `plan/tiebreaks/plan.md` (`plan/LEDGER.md:17`). Those cold-audit links remain incorrect despite the class-level resolution claim.

40. **Low — v1.17's “content unchanged” extraction leaves active self-references false.** PLAN.md says Section 2b moved with “content unchanged” (`PLAN.md:101`), while the extracted protocol says it was “Extracted verbatim” and defines inherited “this file” as PLAN.md plus the protocol (`plan/PROTOCOL.md:3`). Yet “Roles, fixed” still says the orchestrator “maintains this file's ledger” even though the ledger is now separate (`plan/PROTOCOL.md:9`), and `plan/LEDGER.md` still says “A standalone LEDGER.md is deliberately deferred” inside that very standalone file (`plan/LEDGER.md:7`). The extraction also substantively expanded the direct-edit allowlist to name PLAN.md and the plan directory (`plan/PROTOCOL.md:18`), while `plan/AMENDMENTS.md` repeats that the text was “extracted verbatim” (`plan/AMENDMENTS.md:7`). The top-level authority pointers are usable, so this is Low, but the migration's provenance and self-description are not accurate.

## Recommendations

1. Validate the external allowlist before `codex exec`, validate substantive brief-section contents and the agent slug, hash the brief/allowlist into the ledger, and require ledger authorization for model/effort overrides (`plan/PROTOCOL.md:10`, `plan/PROTOCOL.md:18`; `plan/LEDGER.md:9`; `tools/run_codex_agent.sh:25-32`, `tools/run_codex_agent.sh:44-99`).
2. On resume failure, rebuild the fresh prompt with a continuity-loss flag, append the warning to the persistent wrapper log, and require/validate the matching ledger update (`plan/PROTOCOL.md:26`; `tools/run_codex_review.sh:180-193`, `tools/run_codex_review.sh:294-320`).
3. Give kimi a per-phase artifact manifest including required figures or rendered descriptions; retain the skip-and-continue behavior for individually oversized files (`plan/PROTOCOL.md:20`, `plan/PROTOCOL.md:24`; `tools/run_kimi_review.py:40-79`).
4. Harden `run_tiebreak.py`: lock the repo, constrain paths, require a tracked prompt blob equal to HEAD, validate the finding/evidence/arguments and verdict schema, persist a run ID, and require ledger plus next-sol verification; reconcile the two human triggers (`plan/PROTOCOL.md:19`, `plan/PROTOCOL.md:24`, `plan/PROTOCOL.md:30`; `tools/run_tiebreak.py:4-35`).
5. Extend amendment review to retro-generated AGENTS.md changes (`plan/PROTOCOL.md:28-30`; `tools/codex-prompts/review-retro.md:5-11`).
6. Rewrite the Phase 3 summary bullet and Appendix D to reference the sole-authority block without restating contradictory comparators, retries, or continuation outcomes (`PLAN.md:377`, `PLAN.md:381-391`, `PLAN.md:483-496`).
7. Register exact expected sol/kimi topic identities and the adaptive-lens slug/rationale/hash, then make acceptance verify those fields rather than counting any codex/kimi frontmatter file (`plan/PROTOCOL.md:19`; `tools/check_acceptance.sh:12-26`; `tools/run_kimi_review.py:126-136`).
8. Correct the remaining audit references to the canonical tie-break locations, with dated annotations where append-only history requires them (`plan/tiebreaks/plan.md:92`; `plan/LEDGER.md:17`).
9. Correct the extracted self-references and describe the v1.17 direct-edit allowlist change honestly instead of calling the extraction verbatim/content-unchanged (`PLAN.md:101`; `plan/PROTOCOL.md:3`, `plan/PROTOCOL.md:9`, `plan/PROTOCOL.md:18`; `plan/LEDGER.md:7`; `plan/AMENDMENTS.md:7`).

## Evidence consulted

- `PLAN.md`, read in full, lines 1-527; SHA-256 `6fec00862d786a7e3767eddf7a04e0dbac9edc9edc91f72021041269d8e40f75`.
- `README.md`, read in full, lines 1-66; SHA-256 `3f1c987a755b2ee44a53d766ec2c19b68decd6c69e925d499720f698c42f7dfd`.
- `plan/PROTOCOL.md`, read in full, lines 1-31; SHA-256 `7e37dee11046a5406e7309f1132b2576c18e5d462563692b4eba2aa3ceb21fc2`; `plan/LEDGER.md`, read in full, lines 1-32; SHA-256 `8af9da17602513009d8a17472ed7f8783354d41c71c220b62d2914845a8c694b`; and `plan/AMENDMENTS.md`, read in full, lines 1-25; SHA-256 `c7c748dba4a4be5604e37a7fb6443760a1c1665bc2e2f26399502af8084444de`.
- `plan/reviews/plan/process.md`, the wrapper-supplied Round 1-14 content; `plan/reviews/plan/amendment.md` and its three-round pre-commit review; current science/spec/process sol and kimi files; tracked rejected sidecars; `plan/tiebreaks/plan-prompt-3.md`; and all three tie-break batches plus both human adjudications in `plan/tiebreaks/plan.md`.
- `tools/check_acceptance.sh`, `tools/run_codex_agent.sh`, `tools/run_codex_review.sh`, `tools/run_kimi_review.py`, `tools/run_tiebreak.py`, `tools/review_diff_allowlist.py`, `tools/review_round_tracking.py`, `tools/check_review_scores.py`, `tools/agent_metrics.py`, and the complete tracked prompt inventory.
- `AGENTS.md`, `CLAUDE.md`, `.gitignore`, and the machine-local `plan/reviews/.sessions/` inventory; held IDs exist for amendment, process, science, and spec after the move.
- Read-only `git status`, `git log`, `git diff 0a28d36..1e08938`, `git show`, and `git ls-files`; `1e08938` contains the v1.17 authority split, path migrations, accepted amendment review, and no implementation. The worktree was clean before this canonical edit.
- Direct read-only replay of `tools/check_acceptance.sh plan`: amendment/science/spec passed at 92, process failed at its prior 89, and no unexpected/layout artifact appeared. This verifies the new review layout and Finding 38's continued closure.
- Direct inspection of `plan/reviews/plan/amendment.md:10-18` and the pre-commit history: the working-tree review caught two High relocation defects before `1e08938` landed and accepted the corrected amendment at 92, directly verifying Finding 22's live sequencing repair.
- Direct in-memory replay of kimi's `build_context` at its 400 KB cap: PLAN.md, PROTOCOL.md, LEDGER.md, and AMENDMENTS.md were all present; three oversized files were skipped and traversal continued; figures remain outside `CONTEXT_GLOBS`.
- Static re-verification of coder-brief semantics, reviewer fallback and migrated session inventory, kimi phase-lens routing, retro/AGENTS boundary, tie-break runner and evidence, exact-artifact classification, current ledger STATE, extracted self-references, and G3 subordinate text.
- Read-only inspection of `results/logs/codex-plan-{science,spec,process}.log` and `plan/reviews/.sessions/`; persistent sol logs and session IDs exist. No implementation or gate run has started.
- Matrix arithmetic from PLAN: Phase 3 enumerates 96 runs (66 Task A, 30 Task M); Phase 5 enumerates 27 Task B runs. No pilot exists, so actual GB10 throughput or fit against the 24/72/120 GPU-hour budgets cannot yet be verified.
- No implementation, experiment output, gate artifact, Phase 3/5 pilot, training checkpoint, retrospective, or accepted plan-phase manifest exists; the v1.17 amendment review exists and passed, but no scientific gate or compute projection could be replayed.
