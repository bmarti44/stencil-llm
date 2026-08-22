# Process Review — plan

**Score:** 89 / 100
**Verdict:** CONDITIONAL PASS (75–89)
**Reviewer model:** codex/gpt-5.6-sol
**Date:** 2026-08-22

## Round log

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

1. **High (refuted 2026-08-22: human override — trust-model constants of a single-user repo; detection via git history and resumed reviewer sessions is the registered control; see tie-break batch 2) — Review acceptance still permits direct-checker threshold lowering and forged closure.** (updated 2026-08-22: Round 12 citations.) “Finding identity and closure” says “A human may override a deadlocked finding; the override is recorded in the ledger with rationale” (PLAN.md:107). The named adjudication and ledger history remain present (docs/reviews/plan/tiebreaks.md:47-49; PLAN.md:134). The terminal human disposition remains controlling.

2. **High (refuted 2026-08-22: human override — trust-model constants of a single-user repo; detection via git history and resumed reviewer sessions is the registered control; see tie-break batch 2) — The executed process#2 tie-break refutes a strawman while silent finding substitution remains mechanically accepted.** (updated 2026-08-22: Round 12 citations.) “Context carry-over” calls an unannotated edit “a protocol violation the next round's reviewer is instructed to flag,” while “Finding identity and closure” permits a recorded human override (PLAN.md:106-107). The human specifically closed process#2 (docs/reviews/plan/tiebreaks.md:47-49; PLAN.md:134); this finding remains refuted.

3. **High (resolved 2026-08-22: stable IDs and reviewer-concurrence closure are explicit in the governing prose) — Refutation was unilateral and had no durable finding identity.** (updated 2026-08-22: Round 12 citations.) “Finding identity and closure” says “a finding's identity is `<topic>#<number>`” and only a subsequent reviewer may close it (PLAN.md:107); the reviewer protocol independently forbids closure from an orchestrator claim alone (tools/codex-prompts/_common-header.md:28). The prose-level gap stays closed.

4. **High (refuted 2026-08-22: human override — trust-model constants of a single-user repo; detection via git history and resumed reviewer sessions is the registered control; see tie-break batch 2) — The ledger still cannot deliver its promised exact cold restart despite resuming write-ahead.** (updated 2026-08-22: Round 12 citations.) “Work log and ledger” promises “a restarted session must be able to resume from this file alone,” while its own reconciliation step consults logs, artifacts, and `git status` (PLAN.md:126-128). The human accepted that ledger/log/git stack (docs/reviews/plan/tiebreaks.md:31-35, docs/reviews/plan/tiebreaks.md:47-49); this finding remains refuted. Finding 37 covers a new, narrower failure to update even the accepted STATE convention.

5. **High (resolved 2026-08-22: one absolute freeze rule and a tracked baseline exist) — Threshold pre-registration was contradictory and lacked a repository baseline.** (updated 2026-08-22: Round 12 citations.) Operating rule 3 says thresholds are “frozen permanently” at the first coder/run write-ahead (PLAN.md:84), commit `18bca48` supplies the tracked baseline, and Appendix C now repeats the same trigger (PLAN.md:500). The former contradiction stays closed.

6. **High (resolved 2026-08-22: non-G3 gates have a bounded failure procedure) — Rule 4 was impossible to follow for five gates.** (updated 2026-08-22: Round 12 citation.) Operating rule 4 says that after “three failed fix attempts on the same gate, stop and escalate to the human” for G0/G1/G2/G4/G6 (PLAN.md:85). G3 uses the sole-authority procedure.

7. **High (resolved 2026-08-22: the M1b fallback is a named alternate gate state) — The G3 fallback authorized proceeding while the written gate remained red.** (updated 2026-08-22: Round 12 citations.) Rule 5 registers `M1b-primary` (PLAN.md:86), and the sole G3 authority produces that qualification when G3.2b passes (PLAN.md:419-424); Appendix D.3 feeds that result (PLAN.md:523).

8. **High (resolved 2026-08-22: an all-items checklist separates scientific and review status) — Gate, review, commit, ledger, and README state had no atomic acceptance rule.** (updated 2026-08-22: Round 12 citation.) The “Gate acceptance checklist” calls its six items “all items required before a gate commit” and says “No item may be waived” (PLAN.md:110). Finding 17 covers incomplete mechanical enforcement, not this resolved prose-level separation.

9. **High (refuted 2026-08-22: human override — trust-model constants of a single-user repo; detection via git history and resumed reviewer sessions is the registered control; see tie-break batch 2) — Coder scope and unsuccessful-review containment remain unenforced.** (updated 2026-08-22: Round 12 citations.) “Resolution scope” says the wrapper “refuses to launch” without an allowlist, and the file policy calls uncontained drift “a hard wrapper failure” (PLAN.md:108, PLAN.md:111). The human-approved middle path remains recorded (docs/reviews/plan/tiebreaks.md:37-49; PLAN.md:134); this finding stays refuted. Finding 11 reviews the narrower brief-contract/provenance residue.

10. **High (resolved 2026-08-22: direct edits are restricted to non-implementation artifacts) — The orchestrator exception contradicted the fixed code-author role.** (updated 2026-08-22: Round 12 citations.) Under “Roles, fixed,” the orchestrator “does not write implementation code directly” (PLAN.md:99), and “Resolution scope” routes implementation and tests through coder briefs (PLAN.md:108).

11. **Medium — Coder briefs, scope, and model provenance remain assertions rather than a contract.** (updated 2026-08-22: v1.15 rejects empty sections but still does not validate their semantics or provenance.) “Resolution scope” requires “the objective, the allowlist, the tests to write first, the acceptance command, and the ledger handoff” (PLAN.md:108). The wrapper now rejects a literally empty section, but any nonblank line—including a comment—passes; the external `.allow` file is still checked only after `codex exec`, the agent name is unsanitized, and environment model/effort overrides remain unledgered (tools/run_codex_agent.sh:25-32, tools/run_codex_agent.sh:44-70, tools/run_codex_agent.sh:76-99). “Each entry records” still omits a brief/allowlist hash and actor configuration (PLAN.md:128). A cold session cannot prove which substantive brief, scope, or model produced a diff.

12. **High (resolved 2026-08-22: Phase 5/7 review requirements and the Phase 5 dependency are explicit in prose) — Phase 5/7 could escape review and Phase 6 could bypass Phase 5.** (updated 2026-08-22: Round 12 citations.) “Cadence” requires “at minimum one review per phase before its exit commit” (PLAN.md:109); Phase 5, Phase 6, and Phase 7 retain the reviewed-artifact dependency (PLAN.md:442, PLAN.md:446, PLAN.md:464).

13. **High (resolved 2026-08-22: Phase 6 now has an aggregate budget and matrix restart contract) — Phase 6 had no budget or restart envelope for the single device.** (updated 2026-08-22: Round 12 citations.) “Budget discipline” requires a pilot projection and 4x timeout (PLAN.md:112); Phase 6 registers 120 GPU-hours (PLAN.md:450), and the determinism contract requires `DONE`-based recovery (PLAN.md:157).

14. **Medium (resolved 2026-08-22: rule 6 now explicitly scopes the Phase 6 exception) — The global determinism rule conflicted with Phase 6.** (updated 2026-08-22: Round 12 citations.) Rule 6 exempts seed-logged Phase 6 training from the bitwise contract (PLAN.md:87), while Phase 6 keeps proof tests fp32 (PLAN.md:452).

16. **High (resolved 2026-08-22: Phase 3 now declares one sole outcome authority with complete precedence) — G3's nominally single-valued procedure still had contradictory inputs and authorized rescue after a registered failure.** (updated 2026-08-22: Round 12 citations.) The “G3 outcome — SOLE AUTHORITY” block says it “supersedes every earlier phrasing,” fixes ordering/comparator/qualifications, and makes red terminal after one diagnosed rerun (PLAN.md:414-424). Finding 35 covers the remaining duplicate-text hazard.

17. **Medium — The gate checklist is still not mechanically coupled to commits or evidence.** (updated 2026-08-22: v1.15 explicitly retains the decline.) The checklist says “all items required before a gate commit” and “No item may be waived” (PLAN.md:110). `check_acceptance.sh` still scores every incidental non-kimi markdown and checks kimi only by `*-kimi.md` presence; it does not bind exact topics/lenses, validate kimi structure or adjudication, or bind scientific artifacts, ledger/README state, and the proposed commit (tools/check_acceptance.sh:5-15). Current kimi files even retain open High/Critical markers while presence alone satisfies item (c). The v1.15 amendment calls atomic enforcement a “Standing decline” (PLAN.md:9). Acceptance is not one replayable decision.

18. **Medium (resolved 2026-08-22: the amendment prompt fragment exists) — The mandatory amendment-review path was not runnable.** (updated 2026-08-22: Round 12 citations.) The “Autonomy policy” requires a sol@xhigh review with topic `amendment` (PLAN.md:120), and `review-amendment.md` provides the rubric (tools/codex-prompts/review-amendment.md:1-12). Finding 22 covers failure to use it before activation.

19. **Medium (resolved 2026-08-22: v1.15 makes README's own transition sentence match every rule-5 trigger) — README transition triggers remain incomplete even though v1.9 can encode composite G3 results.** (updated 2026-08-22: Round 12 verification.) Rule 5 requires `in progress` on entry, exact gate states, `killed` on project termination, and Phase 5/7 updates on reviewed-artifact commits (PLAN.md:86). README now repeats all four transition classes (README.md:58). Evidence binding remains Finding 17, but the trigger mismatch named here is closed.

20. **Low (refuted 2026-08-22: the Round 11 worktree was clean and the ledger explains the prior serialized sibling state) — Out-of-canonical review drift is again present.** (updated 2026-08-22: Round 12 verification.) The file policy says “never edit repo files while a wrapper is running” (PLAN.md:111). Read-only `git status --short` was again clean before this canonical edit. No current drift supports this finding.

21. **High (resolved 2026-08-22: v1.9 ports the generic phase-topic fallback to kimi) — The mandatory phase-review cadence was unrunnable for kimi.** (updated 2026-08-22: Round 12 citations.) “Cadence” retains `review-phase.md` as the phase backstop (PLAN.md:109), and kimi now unconditionally selects it for topics beginning `phase` plus `tradeoff` and `report` (tools/run_kimi_review.py:126-136). Finding 36 covers acceptance binding, not command runnability.

22. **Medium — v1.10 again activated before amendment review and leaves threshold provenance false.** (updated 2026-08-22: v1.15 again violates the absolute sequence while documenting an extra-textual exception.) The “Autonomy policy” says an amendment review “must be accepted BEFORE the amendment commit lands” and requires review-accepted-then-committed order (PLAN.md:120). Commit `4adc7d5` activates v1.15's governed PLAN/README/tool changes with no tracked or historical `docs/reviews/plan/amendment.md`; the amendment log labels it “orchestrator-executed under the Autonomy policy” while separately declaring an initial-loop sequencing decline (PLAN.md:7-10). A post-commit process round is not the registered amendment review, so post-hoc edits remain detectable in git but not approved before effect.

23. **High (resolved 2026-08-22: kimi completion/adjudication is now a pre-commit checklist item) — Kimi review could occur after gate acceptance.** (updated 2026-08-22: Round 12 citations.) The checklist requires kimi “before the commit” with confirmed High/Critical findings resolved (PLAN.md:110); “Cross-model review” remains advisory but mandatory (PLAN.md:114). Finding 17 covers enforcement.

24. **Low — Fresh-session fallback works, but its promised audit note still cannot be produced.** (updated 2026-08-22: v1.15 leaves the implementation unchanged.) “Review-session continuity” requires a fresh fallback to be “noted in the wrapper log and the ledger” (PLAN.md:116). The wrapper emits the warning only to its own stderr, retries with the already-built prompt that claims continuity, overwrites the codex-output log, and performs no ledger update (tools/run_codex_review.sh:180-193, tools/run_codex_review.sh:294-320). Continuity loss is still absent from the durable surfaces the rule names unless an outer caller acts manually.

25. **Medium (resolved 2026-08-22: acceptance-tooling retro changes now require amendment review) — Retrospectives could change acceptance tooling without independent review.** (updated 2026-08-22: Round 12 citations.) The “Autonomy policy” review-gates checker, tracker, wrapper, and reviewer/coder prompt changes from retros (PLAN.md:120). Finding 31 covers the remaining AGENTS.md limb under “Phase retrospectives” (PLAN.md:118).

26. **Medium (resolved 2026-08-22: v1.13 excludes rejected candidates from both kimi context and agent metrics) — Rejected kimi sidecars demonstrably contaminate later context and metrics.** (updated 2026-08-22: Round 12 citations.) Kimi still saves a rejected sidecar (tools/run_kimi_review.py:195-203), but context skips `*.rejected.md` and metrics excludes rejected/tie-break files (tools/run_kimi_review.py:60-79; tools/agent_metrics.py:86-94). The contamination defect stays closed.

27. **Medium — The first tie-break was executed through an unauditable path, and the human-trigger conflict is still live.** (updated 2026-08-22: v1.15 adds a dirty-path check but still lacks a trustworthy transaction.) “Cross-model review” requires kimi to receive “the finding, the fix or refutation evidence, and both arguments,” with the verdict executed and ledgered (PLAN.md:114). `run_tiebreak.py` now rejects a dirty path, but it ignores `git status`'s return code and permits ignored or out-of-repository prompt paths, accepts any output path, takes no repo lock, validates no prompt/verdict schema, and performs no ledger or next-sol verification (tools/run_tiebreak.py:4-35). Section 2b triggers the human after a disputed tie-break while the Autonomy policy triggers after two deadlocked rounds (PLAN.md:114, PLAN.md:120). The runner still does not implement one reproducible disposition protocol.

28. **Medium (resolved 2026-08-22: v1.12 explicitly makes `tools/check_acceptance.sh plan` the plan-acceptance and Phase 0 entry condition) — The plan phase has no registered acceptance condition for entering Phase 0.** (updated 2026-08-22: Round 12 citation.) “Cadence” says the plan is accepted when `tools/check_acceptance.sh plan` passes, “after which Phase 0 may begin” (PLAN.md:109). Findings 17 and 36 cover the command's incomplete binding.

29. **Medium — Required kimi phase reviews cannot see all gate-critical artifacts.** (updated 2026-08-22: v1.15 does not change artifact coverage.) “Cross-model review” requires kimi “on the gate-critical work” (PLAN.md:114). Result and retro markdown have priority, but figures are absent, no per-phase artifact manifest exists, and `build_context` returns at the first oversized file rather than skipping it (tools/run_kimi_review.py:40-49, tools/run_kimi_review.py:60-79). A current 400 KB replay truncated during review history; the ordering fix works, but a required oversized artifact or figure can still be invisible while Finding 17's presence check passes.

30. **Low (resolved 2026-08-22: v1.15 makes Appendix C repeat rule 3's coder-or-run write-ahead trigger) — Rule 3's freeze trigger is undefined for test-gated phases.** (updated 2026-08-22: Round 12 verification.) Rule 3 freezes at “the first write-ahead ledger entry launching either a coder brief or a run” (PLAN.md:84), and Appendix C now repeats “launching a coder brief or a run ... whichever comes first” (PLAN.md:500). The test-gated-phase ambiguity is gone.

31. **Medium — Retrospectives may weaken reviewer/coder instructions without independent review.** (updated 2026-08-22: Round 12 re-verification.) “Phase retrospectives and agent evals” requires each optimization to land as an “AGENTS.md entry” or tooling/prompt diff (PLAN.md:118). The Autonomy policy review-gates tools and prompt fragments but not AGENTS.md (PLAN.md:120), and the retro rubric does not test whether an AGENTS change preserves governance (tools/codex-prompts/review-retro.md:5-11). Auto-loaded instructions can still change before the next phase without independent process review.

32. **Medium (resolved 2026-08-22: v1.13 puts the binding anti-churn limit directly in kimi's resumed-round prompt) — The kimi wrapper does not implement the binding anti-churn rule.** (updated 2026-08-22: Round 12 citations.) “Review-session continuity” binds kimi to the same anti-churn rule (PLAN.md:116), and its resumed-round prompt states that restriction directly (tools/run_kimi_review.py:149-153).

33. **Low (resolved 2026-08-22: v1.15 identifies the pilot as the primary oscillatory variant at R=32, seed 0) — Phase 5's pilot is underspecified for a matrix whose sequence lengths vary sixteen-fold.** (updated 2026-08-22: Round 12 verification.) “Budget discipline” requires a pilot-derived projection (PLAN.md:112), and Phase 5 now selects “the primary oscillatory variant at the longest cell, R = 32, seed 0” (PLAN.md:440). The pilot cell is fully identified before launch by G3's primary-variant outcome.

34. **Low (resolved 2026-08-22: v1.14 names sol as reviewer of record and kimi as the mandatory second reviewer) — Operating rule 9 still contradicts the mandatory second-reviewer role.** (updated 2026-08-22: Round 12 citations.) Rule 9 says sol is reviewer of record and kimi is the mandatory cross-model second reviewer (PLAN.md:90), matching the checklist and cross-model section (PLAN.md:110, PLAN.md:114). The contradiction stays closed.

35. **Medium — The G3 sole-authority fix leaves materially contradictory subordinate text in the governing document.** (updated 2026-08-22: v1.15 fixes Appendix C's comparator but leaves other live restatements.) The sole-authority block says it “supersedes every earlier phrasing” and permits one diagnosed rerun before kill (PLAN.md:414-424). The immediately preceding G3.4 bullet still says “M1 within 3 pts of B0-full” rather than the primary variant (PLAN.md:410); Appendix D still permits an amendment-based wide-model continuation that “does not retroactively pass” the registered 64-pair spec and gives isolated G3.3 three attempts via rule 4 (PLAN.md:526-527). Appendix C is now correct (PLAN.md:509), but an agent still encounters contradictory comparator, continuation, and retry instructions before applying the supersession disclaimer.

36. **Medium — Adaptive review lenses are not bound to gate acceptance or independently coverage-checked.** (updated 2026-08-22: v1.15 fixes generic routing for registered phase-style topics but not acceptance binding.) “Cadence” says a phase's kimi review “ALWAYS runs the generic `review-phase.md` lens” (PLAN.md:109), and the wrapper now forces that lens for `phase*`, `tradeoff`, and `report` topics (tools/run_kimi_review.py:126-136). `check_acceptance.sh` still accepts any `*-kimi.md` presence and neither requires the registered phase-style topic nor records the adaptive sol lens/rationale/hash (tools/check_acceptance.sh:9-15). The generic backstop works when the registered command is used, but gate acceptance does not prove it was used.

37. **Medium — v1.15 leaves the top restart state stale after committing Round 11.** “Work log and ledger” requires updates when “finishing a review round” and says the top `STATE:` carries “latest review scores” and “the exact next command” (PLAN.md:126-128). Commit `4adc7d5` includes the completed Round 11 process review at 89 (docs/reviews/plan/process.md:22), yet the top ledger still says “process 87” and “next command: sol process round 11” (PLAN.md:132). This is not the human-refuted demand for a maximal schema: it is a direct failure to maintain the minimal STATE convention the human accepted, leaving a cold session one round behind.

## Recommendations

1. Validate the external allowlist before `codex exec`, validate substantive brief-section contents and the agent slug, hash the brief/allowlist into the ledger, and require ledger authorization for model/effort overrides (PLAN.md:100, PLAN.md:108, PLAN.md:128; tools/run_codex_agent.sh:25-32, tools/run_codex_agent.sh:44-99).
2. Add one gate manifest binding the reviewed diff, adaptive-lens slug/rationale/hash, mandatory generic kimi topic, exact sol/kimi artifacts, scientific evidence, adjudication, ledger/README state, and proposed commit; make `check_acceptance.sh` validate it (PLAN.md:109-110; tools/check_acceptance.sh:1-16; README.md:45-58).
3. Obey review-before-commit for the next amendment and require every amendment entry to name the accepted amendment review/round/score, affected-phase freeze evidence, exact old/new values, and activation SHA (PLAN.md:7-10, PLAN.md:120, PLAN.md:500).
4. On resume failure, rebuild the fresh prompt with a continuity-loss flag, append the warning to the persistent wrapper log, and require/validate the matching ledger update (PLAN.md:116; tools/run_codex_review.sh:180-193, tools/run_codex_review.sh:294-320).
5. Give kimi a per-phase artifact manifest including required figures or rendered descriptions, and skip individual oversized files instead of returning at the first overflow (PLAN.md:110, PLAN.md:114; tools/run_kimi_review.py:40-79).
6. Harden `run_tiebreak.py`: lock the repo, constrain paths, require a tracked prompt blob equal to HEAD, validate the finding/evidence/arguments and verdict schema, persist a run ID, and require ledger plus next-sol verification; reconcile the two human triggers (PLAN.md:109, PLAN.md:114, PLAN.md:120; tools/run_tiebreak.py:4-35).
7. Extend amendment review to retro-generated AGENTS.md changes (PLAN.md:118-120; tools/codex-prompts/review-retro.md:5-11).
8. Rewrite the Phase 3 summary bullet and Appendix D to reference the sole-authority block without restating contradictory comparators, retries, or continuation outcomes (PLAN.md:410, PLAN.md:414-424, PLAN.md:518-529).
9. Update the ledger immediately after every review completion and before each new launch; make the top STATE score and next command executable and current (PLAN.md:126-132; docs/reviews/plan/process.md:22).

## Evidence consulted

- PLAN.md, read in full, lines 1-560; SHA-256 `f8d1e37ee894a99ba70e65a2bbf968260ae2d352a9b95926e77af7324de73ab3`.
- README.md, read in full, lines 1-66; SHA-256 `19db53a1f1e652cb391914b76b157011716fbf1f76dfc0b1d957f46472f098d4`.
- docs/reviews/plan/process.md, the wrapper-supplied Round 1-11 content; current science/spec/process sol and kimi files; all tracked `*-kimi.rejected.md` sidecars; and the tie-break batches plus human adjudication in docs/reviews/plan/tiebreaks.md.
- tools/check_acceptance.sh, tools/run_codex_agent.sh, tools/run_codex_review.sh, tools/run_kimi_review.py, tools/run_tiebreak.py, tools/review_diff_allowlist.py, tools/review_round_tracking.py, tools/check_review_scores.py, tools/agent_metrics.py, and the complete tracked prompt inventory.
- AGENTS.md, CLAUDE.md, .gitignore, and the machine-local docs/reviews/.sessions/ inventory.
- Read-only `git status`, `git log`, `git diff 9fea8e5..4adc7d5`, `git show`, `git blame`, and `git ls-files`; commit `4adc7d5` contains v1.15 and the committed Round 11 process review. The worktree was clean before this canonical edit.
- Read-only inspection of results/logs/codex-plan-{science,spec,process}.log and docs/reviews/.sessions/; persistent sol logs/session IDs exist. No tracked or historical docs/reviews/plan/amendment.md exists.
- Static and replay verification of v1.15: `bash -n` passed for run_codex_agent.sh; both changed Python files parsed; the brief awk rejects an empty body but accepts any nonblank comment; kimi phase-style routing is unconditional; and run_tiebreak.py's dirty check ignores git errors and treats an ignored prompt path as clean.
- Direct in-memory replay of kimi's `build_context` at 400 KB: governing docs/tools were present and truncation occurred during review history; no results/retro markdown exists yet, figures remain outside the inventory, and the builder still returns at the first oversized file.
- Direct inspection of `tools/check_acceptance.sh plan`: it remains filesystem/presence based rather than an evidence/lens manifest; science/spec are 92 and this process round is 89, so plan acceptance remains red.
- Matrix arithmetic from PLAN: Phase 3 enumerates 96 runs (66 Task A, 30 Task M); Phase 5 enumerates 27 Task B runs. v1.15 now identifies the longest-sequence primary-variant pilot, but no pilot exists, so actual GB10 throughput or fit against the 24/72/120 GPU-hour budgets cannot be verified.
- No implementation, experiment output, gate artifact, Phase 3/5 pilot, training checkpoint, retrospective, accepted plan-phase manifest, or tracked amendment review exists; no scientific gate or compute projection could be replayed.
