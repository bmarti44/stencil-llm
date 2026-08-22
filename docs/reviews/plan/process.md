# Process Review — plan

**Score:** 74 / 100
**Verdict:** FAIL (<75)
**Reviewer model:** codex/gpt-5.6-sol
**Date:** 2026-08-22

## Round log

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

1. **High — Review acceptance still permits direct-checker threshold lowering and forged closure.** (updated 2026-08-22: Round 8 re-verification.) Section 2b, “Finding identity and closure,” says “`tools/check_review_scores.py` treats any unmarked high/critical finding as open and fails regardless of score” and requires reviewer concurrence (`PLAN.md:103`). The hardcoded 90-point milestone path removes the direct-threshold limb (`PLAN.md:106`; `tools/check_acceptance.sh:1-15`), but the closure parser is still forgeable: it treats any same-line closure-shaped token as closure regardless of position and accepts an empty rationale (`tools/check_review_scores.py:18-22`). Fresh replays hid both an open title that merely mentioned a dated resolved token and a dated resolved marker with no evidence text. Because `check_acceptance.sh` delegates severity detection to this parser (`tools/check_acceptance.sh:9-12`), the batch-2 claim that exploitation would require editing the checker or reviewer file is false (`docs/reviews/plan/tiebreaks.md:19-23`): malformed reviewer output alone can erase an open blocker mechanically. I do not concur with the refutation.

2. **High — The executed process#2 tie-break refutes a strawman while silent finding substitution remains mechanically accepted.** (updated 2026-08-22: Round 8 re-verification.) Section 2b requires that “any other change to prior content MUST carry a dated `(updated ...)` annotation” (`PLAN.md:102`). The tracker still checks only prior round numbers/scores, High/Critical numbers, and a title prefix found anywhere; it never binds the full title/body/status to the same finding number or enforces an annotation (`tools/review_round_tracking.py:92-146`). A fresh replay silently replaced process#2's entire body while retaining its title and returned `passed=True`. Batch 2 again calls this a demand for body immutability and says no cheaper compatible mechanism was requested (`docs/reviews/plan/tiebreaks.md:25-29`), although this finding explicitly asks for keyed status transitions plus annotation enforcement, not byte identity. I do not concur: process#2 remains open, and the disputed tie-break triggers Section 2b's human touchpoint (`PLAN.md:110`).

3. **High (resolved 2026-08-22: stable IDs and reviewer-concurrence closure are explicit in the governing prose) — Refutation was unilateral and had no durable finding identity.** (updated 2026-08-22: current citations.) Section 2b says “a finding's identity is `<topic>#<number>`” and “only a subsequent reviewer round may mark a finding `(resolved ...)` or `(refuted ...)`” (`PLAN.md:103`); the reviewer protocol says not to close on an orchestrator claim alone (`tools/codex-prompts/_common-header.md:28`). Findings 1-2 cover enforcement, not this resolved prose-level gap.

4. **High — The ledger still cannot deliver its promised exact cold restart despite resuming write-ahead.** (updated 2026-08-22: Round 8 re-verification.) “Work log and ledger” promises both “a restarted session must be able to resume from this file alone” and a topmost `STATE:` carrying “the exact next command” (`PLAN.md:122`). The Round 8 state supplies only “sol spec + sol process + kimi spec + kimi process, serialized, absolute paths”—not one executable command, per-topic lifecycle, exact logs/artifacts, session/PID, branch/HEAD/dirty state, open-finding inventory, or matrix-cell/checkpoint/retry state (`PLAN.md:128`). The schema still instructs recovery through external logs, artifacts, and `git status` (`PLAN.md:124`). The batch-2 assertion that the state contains exact commands/log paths is therefore contradicted by the governed entry itself (`docs/reviews/plan/tiebreaks.md:31-35`); successful informal recovery does not satisfy the stronger registered “from this file alone” guarantee. I do not concur with the refutation.

5. **High (resolved 2026-08-22: one absolute freeze rule and a tracked baseline exist) — Threshold pre-registration was contradictory and lacked a repository baseline.** (updated 2026-08-22: current citations.) Operating rule 3 says thresholds are “frozen permanently” after the affected phase's first run (`PLAN.md:80`), and commit `18bca48` supplies the tracked baseline. Findings 22 and 30 cover current amendment provenance and trigger ambiguity without reopening this resolved contradiction.

6. **High (resolved 2026-08-22: non-G3 gates have a bounded failure procedure) — Rule 4 was impossible to follow for five gates.** (updated 2026-08-22: current citations.) Operating rule 4 bounds G0/G1/G2/G4/G6 diagnosis and escalation after three failed fixes (`PLAN.md:81`); G3 uses the sole-authority rule in Finding 16.

7. **High (resolved 2026-08-22: the M1b fallback is a named alternate gate state) — The G3 fallback authorized proceeding while the written gate remained red.** (updated 2026-08-22: current citations.) Rule 5 registers the `M1b-primary` qualification (`PLAN.md:82`), and the sole G3 authority plus Appendix D.3 apply it (`PLAN.md:412-417`, `PLAN.md:516`).

8. **High (resolved 2026-08-22: an all-items checklist separates scientific and review status) — Gate, review, commit, ledger, and README state had no atomic acceptance rule.** (updated 2026-08-22: current citations.) The checklist says “all items required before a gate commit” and “No item may be waived” (`PLAN.md:106`), separating science, sol, kimi, ledger, README, and commit state. Finding 17 covers its incomplete enforcement.

9. **High — Coder scope and unsuccessful-review containment remain unenforced.** (updated 2026-08-22: Round 8 re-verification.) Section 2b now says every coder brief “MUST ship a scope allowlist”, the wrapper “refuses to launch without one,” and uncontained drift is a hard failure (`PLAN.md:104`, `PLAN.md:107`). The implementation checks for the allowlist only after `codex exec` has already run and mutated the repository (`tools/run_codex_agent.sh:47-69`); it compares the entire dirty worktree rather than a launch baseline, accepts an unsanitized agent name, bypasses the sandbox, and logs only to `/tmp` (`tools/run_codex_agent.sh:25-55`, `tools/run_codex_agent.sh:70-86`). On failed sol review, v1.11 still skips the canonical review and every path under `docs/reviews/`, so a truncated canonical file or unauthorized review sidecar survives; it restores/deletes only other paths (`tools/run_codex_review.sh:321-340`). The batch-2 middle path's claim that the existing diff report provides containment is thus false (`docs/reviews/plan/tiebreaks.md:37-41`). Mandatory-after-launch matching and intentional preservation do not enforce the advertised pre-launch scope or review recovery boundary.

10. **High (resolved 2026-08-22: direct edits are restricted to non-implementation artifacts) — The orchestrator exception contradicted the fixed code-author role.** (updated 2026-08-22: current citations.) The orchestrator does not write implementation code (`PLAN.md:95`), and resolution scope sends implementation/tests through coder briefs while limiting direct edits to non-implementation files (`PLAN.md:104`).

11. **Medium — Coder briefs, scope, and model provenance remain assertions rather than a contract.** (updated 2026-08-22: Round 8 re-verification.) The coder role fixes model, effort, and brief path (`PLAN.md:96`), and v1.11 makes a sibling allowlist mandatory (`PLAN.md:104`). No brief schema still requires objective, forbidden paths, dependencies, acceptance tests, finding IDs, artifacts, stop conditions, or handoff; the wrapper accepts unledgered model/effort overrides and an unsanitized name (`tools/run_codex_agent.sh:25-35`, `tools/run_codex_agent.sh:47-52`). The ledger schema requires neither brief hash nor actor configuration (`PLAN.md:124`). A glob allowlist alone cannot prove which authorized brief/model produced a diff.

12. **High (resolved 2026-08-22: Phase 5/7 review requirements and the Phase 5 dependency are explicit in prose) — Phase 5/7 could escape review and Phase 6 could bypass Phase 5.** (updated 2026-08-22: current citations.) Cadence names `tradeoff` and `report` (`PLAN.md:105`); Phase 5 exits only after review, Phase 6 requires that reviewed document, and Phase 7 repeats review-before-shipment (`PLAN.md:435`, `PLAN.md:439`, `PLAN.md:457`).

13. **High (resolved 2026-08-22: Phase 6 now has an aggregate budget and matrix restart contract) — Phase 6 had no budget or restart envelope for the single device.** (updated 2026-08-22: current citations.) Budget discipline requires pilot projection, timeout, and 2x escalation (`PLAN.md:108`); Phase 6 has a 120 GPU-hour budget (`PLAN.md:443`) and the run contract has `DONE`-based recovery (`PLAN.md:150`). Actual GB10 fit remains pilot-dependent, but the denominator and restart rule now exist.

14. **Medium (resolved 2026-08-22: rule 6 now explicitly scopes the Phase 6 exception) — The global determinism rule conflicted with Phase 6.** (updated 2026-08-22: current citations.) Rule 6 binds Phases 0-5/fp32 proofs and exempts seed-logged Phase 6 training (`PLAN.md:83`); Phase 6 repeats that split (`PLAN.md:445`).

16. **High (resolved 2026-08-22: Phase 3 now declares one sole outcome authority with complete precedence) — G3's nominally single-valued procedure still had contradictory inputs and authorized rescue after a registered failure.** (updated 2026-08-22: current citations.) The “G3 outcome — SOLE AUTHORITY” block supersedes earlier phrasing, fixes evaluation order/comparator/qualifications, and makes all other misses red with one diagnosed rerun or kill (`PLAN.md:407-417`). That precedence closes the bypass; Finding 35 retains the maintenance hazard from contradictory subordinate text.

17. **Medium — The gate checklist is still not mechanically coupled to commits or evidence.** (updated 2026-08-22: Round 8 re-verification.) Section 2b calls six items “all items required before a gate commit” and routes sol acceptance through `tools/check_acceptance.sh <phase>` (`PLAN.md:106`). v1.11 correctly makes an empty sol set fail, but the script still scores every incidental non-kimi markdown and checks kimi only by `*-kimi.md` presence (`tools/check_acceptance.sh:5-15`). It never maps the exact registered topic, validates kimi structure/adjudication, or binds gate artifacts, ledger state, README row, and proposed commit. README remains bare statuses (`README.md:47-58`). The command is a score/presence check, not an atomic gate manifest.

18. **Medium (resolved 2026-08-22: the amendment prompt fragment exists) — The mandatory amendment-review path was not runnable.** (updated 2026-08-22: current citations.) The Autonomy policy requires a sol@xhigh `amendment` review (`PLAN.md:116`), and `review-amendment.md` supplies its rubric (`tools/codex-prompts/review-amendment.md:1-12`). Finding 22 covers sequencing.

19. **Medium — README transition triggers remain incomplete even though v1.9 can encode composite G3 results.** (updated 2026-08-22: Round 8 re-verification.) Rule 5 defines a vocabulary but only mandates one commit per green gate; it never says when `in progress`, non-G3 `red`, or `killed` is persisted (`PLAN.md:82`). README says only “Every green gate flips its row” (`README.md:58`). Phase 5/7 exits still do not require row updates (`PLAN.md:435`, `PLAN.md:457`; `README.md:54-56`), and rows have no evidence path, date, review round, or SHA. The restart surface can therefore remain `not started` through active or terminal work.

20. **Low — Out-of-canonical review drift is again present.** (updated 2026-08-22: Round 8 observation.) Section 2b says “never edit repo files while a wrapper is running” (`PLAN.md:107`). Read-only `git status --short` showed modified `docs/reviews/plan/spec.md:1` outside this canonical process review. It was left untouched; the dirty sibling prevents clean-state attestation even though status alone cannot prove wrapper overlap.

21. **High (resolved 2026-08-22: v1.9 ports the generic phase-topic fallback to kimi) — The mandatory phase-review cadence was unrunnable for kimi.** (updated 2026-08-22: current citations.) Cadence registers generic phase/tradeoff/report topics (`PLAN.md:105`); kimi routes those to `review-phase.md` (`tools/run_kimi_review.py:122-130`), matching sol (`tools/run_codex_review.sh:121-135`).

22. **Medium — v1.10 again activated before amendment review and leaves threshold provenance false.** (updated 2026-08-22: v1.11 repeats the breach.) The Autonomy policy says an amendment review “must be accepted BEFORE the amendment commit lands” and the ledger records “review-accepted-then-committed order” (`PLAN.md:116`). Commit `a2f8a67` activates v1.11—including governed proof tolerances and process tooling—without a tracked `docs/reviews/plan/amendment.md`; the Round 8 review is post-commit, not the registered amendment review. The ledger again relies on its extra-textual initial-loop interpretation (`PLAN.md:128-132`). Appendix C still says “last amended v1.7” (`PLAN.md:493`) after v1.8-v1.11 changed thresholds/decision semantics. Amendment entries omit accepting review file/round/score, affected-phase launch evidence, exact old/new values, and activation SHA (`PLAN.md:7-19`). Git reveals the edits only after effect and cannot prove approval-before-effect.

23. **High (resolved 2026-08-22: kimi completion/adjudication is now a pre-commit checklist item) — Kimi review could occur after gate acceptance.** (updated 2026-08-22: current citations.) The checklist requires kimi before commit and confirmed High/Critical adjudication (`PLAN.md:106`); kimi remains advisory (`PLAN.md:110`). Finding 34 covers rule 9.

24. **Low — Fresh-session fallback works, but its promised audit note still cannot be produced.** (updated 2026-08-22: v1.11/9b2eb7d fix SID loading but not fallback disclosure.) Review-session continuity promises an unusable-session fallback “noted in the round log” (`PLAN.md:112`). SID is now loaded before prompt construction (`tools/run_codex_review.sh:180-193`), fixing the missing resume preamble. But a failed resume retries fresh with the already-built prompt, which still says the session context is intact and carries no fallback flag (`tools/run_codex_review.sh:294-320`). The resulting round cannot distinguish a successful resume from continuity loss.

25. **Medium (resolved 2026-08-22: acceptance-tooling retro changes now require amendment review) — Retrospectives could change acceptance tooling without independent review.** (updated 2026-08-22: current citations.) Acceptance-tool changes arising from retros require amendment review (`PLAN.md:116`); Finding 31 covers prompt/AGENTS changes (`PLAN.md:114`).

26. **Medium — Rejected kimi sidecars demonstrably contaminate later context and metrics.** (updated 2026-08-22: v1.11 adds a third tracked instance.) The file policy says reviewers write “only their canonical review file” (`PLAN.md:107`), yet kimi writes `<topic>-kimi.rejected.md` on validation failure (`tools/run_kimi_review.py:11-12`, `tools/run_kimi_review.py:183-191`). Commit `a2f8a67` now also tracks `docs/reviews/plan/process-kimi.rejected.md:1` alongside the science/spec sidecars. The context builder ingests every `docs/reviews/**/*.md` (`tools/run_kimi_review.py:40-45`), and metrics treat every recursive markdown as a review topic (`tools/agent_metrics.py:86-94`). Rejected prose therefore remains persistent reviewer input and bogus retrospective data.

27. **Medium — The first tie-break was executed through an unauditable path, and the human-trigger conflict is still live.** (updated 2026-08-22: batch 2 repeats and worsens the defect.) Cross-model review requires kimi to receive the finding, evidence, and both arguments, then have its verdict executed and ledgered (`PLAN.md:110`). Batch 2 again stores only free-form verdict prose, with no command, prompt/mode, supplied evidence/arguments, raw response/log, run ID, or verification (`docs/reviews/plan/tiebreaks.md:13-41`); the kimi tool still has only scored topic-review mode (`tools/run_kimi_review.py:94-130`). Its final sentence purports to forbid further resolve-or-refute rounds (`docs/reviews/plan/tiebreaks.md:43-45`), contradicting reviewer concurrence (`PLAN.md:103`) and both human triggers (`PLAN.md:110`, `PLAN.md:116`). Findings 1/2/4/9 dispute the verdicts, but the ledger records no human escalation command (`PLAN.md:128`).

28. **Medium — The plan phase has no registered acceptance condition for entering Phase 0.** (updated 2026-08-22: Round 8 re-verification.) Cadence begins with Phase 0 and never registers plan acceptance (`PLAN.md:105`); the ledger merely calls this a “plan-acceptance loop” (`PLAN.md:128`). `check_acceptance.sh plan` happens to score whatever sol markdown currently exists, but PLAN does not name mandatory science/spec/process topics, kimi/tie-break adjudication, an acceptance commit, or the ledger transition authorizing Phase 0 (`tools/check_acceptance.sh:5-16`). The immediate dependency remains filesystem-dependent behavior or orchestrator judgment.

29. **Medium — Required kimi phase reviews cannot see all gate-critical artifacts.** (updated 2026-08-22: Round 8 re-verification.) Section 2b requires kimi on “the gate-critical work” (`PLAN.md:106`, `PLAN.md:110`), but its inventory omits `results/*.md` and figures (`tools/run_kimi_review.py:40-45`), despite the generic rubric and Phase 5/7 deliverables (`tools/codex-prompts/review-phase.md:3`; `PLAN.md:433-435`, `PLAN.md:457`). The builder stops entirely at the first 400 KB overflow (`tools/run_kimi_review.py:56-75`). A structurally partial invocation can still satisfy the checklist's run/presence test.

30. **Low — Rule 3's freeze trigger is undefined for test-gated phases.** (updated 2026-08-22: current citation.) Rule 3 freezes when “the affected phase's first run” launches and speaks specifically of Appendix C (`PLAN.md:80`). Phases 0-2 are primarily test/fixture governed and Phase 1 has no training run; neither first pytest nor first `make gate-N` is registered as the freeze event.

31. **Medium — Retrospectives may weaken reviewer/coder instructions without independent review.** (updated 2026-08-22: Round 8 re-verification.) Retros require optimizations to land in AGENTS.md or tooling/prompts (`PLAN.md:114`), while the Autonomy policy review-gates only checker/tracker/wrapper changes (`PLAN.md:116`). The retro rubric checks attribution and whether a diff landed, not whether prompt/AGENTS changes preserve governance (`tools/codex-prompts/review-retro.md:5-11`). Such changes can govern the next phase without sol process review.

32. **Medium — The kimi wrapper does not implement the binding anti-churn rule.** (updated 2026-08-22: Round 8 re-verification.) Review continuity gives kimi “the same anti-churn rule” (`PLAN.md:112`), but its preamble only preserves prior findings and directs it to find what sol missed; it never limits new findings to regressions/original-scope misses (`tools/run_kimi_review.py:143-163`). Confirmed kimi High/Critical claims create mandatory adjudication (`PLAN.md:110`), so stateless scope can still grow indefinitely.

33. **Low — Phase 5's pilot is underspecified for a matrix whose sequence lengths vary sixteen-fold.** (updated 2026-08-22: Round 8 re-verification.) Budget discipline requires a pilot-derived projection (`PLAN.md:108`), but Phase 5 names only “one pilot cell” for 27 runs over `R in {2,8,32}` and 24 GPU-hours (`PLAN.md:433`). Task B contains R segments with 32-256-token delays (`PLAN.md:310-315`), so R=32 has about sixteen times R=2's segments. Without a named worst-case pilot or per-R scaling measurements, the single-Spark projection is not defensible ex ante.

34. **Low — Operating rule 9 still contradicts the mandatory second-reviewer role.** (updated 2026-08-22: current citations.) Rule 9 says “all reviews are sol adversarial reviews” (`PLAN.md:86`), while Section 2b calls kimi the “second, independent reviewer” and requires it before commit (`PLAN.md:106`, `PLAN.md:110`). The specific checklist prevents a skip, but the global rule should say “reviews of record.”

35. **Medium — The G3 sole-authority fix leaves materially contradictory subordinate text in the governing document.** (updated 2026-08-22: Round 8 re-verification.) The authoritative block says it “supersedes every earlier phrasing” (`PLAN.md:407`), resolving Finding 16's bypass. Yet rule 5 first lists only green/M1b/red before the broader enum (`PLAN.md:82`); Appendix C still says “B0-full minus M1” rather than the primary variant (`PLAN.md:502`); Appendix D still says “stop at the first match,” invokes rule 4's three-attempt procedure for G3, and permits a wider model that “does not retroactively pass” after amendment (`PLAN.md:511`, `PLAN.md:519-521`). These dead contradictions remain a cold-start and future-edit hazard and should be diagnostics-only references to the sole authority.

## Recommendations

1. Require closure markers immediately after severity with a valid date and nonempty reviewer-evidence text; make `check_acceptance.sh` reject any marker the stricter grammar rejects (`PLAN.md:103-106`; `tools/check_review_scores.py:18-22`; `tools/check_acceptance.sh:9-12`).
2. Key every prior High/Critical invariant to the same finding number and compare severity, full title, body hash, and status transition; require dated annotations for permitted body edits and unique descending rounds. Do not search a 40-character title prefix anywhere in the candidate (`PLAN.md:102-103`; `tools/review_round_tracking.py:92-146`).
3. Turn `STATE:` into a validated schema for work ID/state, phase/gate, branch/HEAD/dirty paths, brief hash/scope, actor/session/PID/model/effort, exact commands/logs/tests, finding inventory, matrix cells/checkpoints/retries, blockers, and exact next command; reject prose in place of an executable command (`PLAN.md:120-139`).
4. Check the mandatory coder allowlist before `codex exec`, validate the agent slug, persist logs, sandbox by default, and compare post-run changes with a launch baseline. On review failure restore the canonical file from `PRIOR_SNAPSHOT` and contain unauthorized review-tree additions as well as other drift (`PLAN.md:104`, `PLAN.md:107`; `tools/run_codex_agent.sh:20-86`; `tools/run_codex_review.sh:294-340`).
5. Define and validate the coder-brief schema before Phase 0, and require explicit ledger authorization for actor-model/effort overrides (`PLAN.md:95-104`, `PLAN.md:124`).
6. Rewrite rule 5, Appendix C G3.4, and Appendix D to reference the Phase 3 sole-authority block without restating contradictory states, comparators, retry counts, or continuation outcomes (`PLAN.md:82`, `PLAN.md:407-417`, `PLAN.md:502`, `PLAN.md:509-522`).
7. Make `check_acceptance.sh` map each phase to exact registered sol/kimi topics and validate canonical structure/adjudication; bind gate evidence, ledger `STATE`, README row, and proposed commit in one manifest (`PLAN.md:105-110`; `tools/check_acceptance.sh:1-16`; `README.md:45-58`).
8. Define status triggers for `in progress`, `red`, `killed`, and Phase 5/7 completion; add evidence path, accepted review round/score, date, and commit SHA to README (`PLAN.md:82`, `PLAN.md:431-457`; `README.md:45-58`).
9. Obey review-before-commit for the next amendment; correct Appendix C provenance through v1.11 and require amendment records to name review file/round/score, affected phase, launch/freeze evidence, exact old/new values, and activation commit (`PLAN.md:7-19`, `PLAN.md:116`, `PLAN.md:491-507`).
10. When resume fails, rebuild the fresh prompt with an explicit continuity-loss flag and require the new round to record it (`PLAN.md:112`; `tools/run_codex_review.sh:180-193`, `tools/run_codex_review.sh:294-320`).
11. Store rejected kimi output outside `docs/reviews`, exclude it from context and metrics, and include required result documents/figures through an explicit artifact manifest before applying the context cap (`tools/run_kimi_review.py:40-75`, `tools/run_kimi_review.py:183-194`; `tools/agent_metrics.py:86-94`).
12. Implement a runnable tie-break command/prompt that persists the finding, both arguments, evidence bundle, raw response/log, model, and verification; remove any artifact text purporting to prohibit reviewer concurrence (`PLAN.md:103`, `PLAN.md:110`; `docs/reviews/plan/tiebreaks.md:13-45`).
13. Record the triggered human escalation for process#1/#2/#4/#9 and reconcile the Autonomy policy's two-round trigger with Section 2b's post-tie-break trigger before another disposition (`PLAN.md:110`, `PLAN.md:116`, `PLAN.md:128`).
14. Register plan-phase acceptance—exact required sol/kimi topics/scores, tie-break adjudication, acceptance commit, and ledger event—and first-test freeze triggers for Phases 0-2 before Phase 0 (`PLAN.md:80`, `PLAN.md:105-106`, `PLAN.md:128`).
15. Extend amendment review to retro-generated reviewer/coder prompt and AGENTS changes, and put the binding anti-churn clause directly in kimi's prompt (`PLAN.md:112-116`; `tools/codex-prompts/review-retro.md:5-11`; `tools/run_kimi_review.py:143-163`).
16. Name the Phase 5 pilot cell and require separate measured or registered scaling projections for R=2, 8, and 32 before accepting the 24 GPU-hour estimate (`PLAN.md:108`, `PLAN.md:310-315`, `PLAN.md:433`).
17. Change operating rule 9 to “all reviews of record are sol” so it no longer contradicts mandatory kimi cross-review (`PLAN.md:86`, `PLAN.md:106-110`).

## Evidence consulted

- `PLAN.md`, read in full, lines 1-553; SHA-256 `9dc0063d30412d16b11ac8c51433c2063c17a9424d90ff6d53c9b62c0851a536`.
- `README.md`, read in full, lines 1-66; SHA-256 `9a4a79b70be89eb584ee563fefd6160bf0d5f374cb77a7bd158f1777d3212430`.
- `docs/reviews/plan/process.md`, the wrapper-supplied Round 1-7 content, `docs/reviews/plan/process-kimi.md` through Round 5, all three tracked `*-kimi.rejected.md` sidecars, and both tie-break batches in `docs/reviews/plan/tiebreaks.md`.
- `tools/check_acceptance.sh`, `tools/run_codex_agent.sh`, `tools/run_codex_review.sh`, `tools/run_kimi_review.py`, `tools/review_diff_allowlist.py`, `tools/review_round_tracking.py`, `tools/check_review_scores.py`, `tools/agent_metrics.py`, and the complete tracked prompt inventory.
- `AGENTS.md`, `CLAUDE.md`, `.gitignore`, and the machine-local `docs/reviews/.sessions/` inventory.
- Read-only `git status`, `git log`, `git diff 58ef452..a2f8a67`, `git show`, `git blame`, and `git ls-files`; commits `a2f8a67`/`9b2eb7d` contain v1.11 and the wrapper-order hotfix, while the sibling spec Round 8 review was modified and left untouched.
- Read-only inspection of `results/logs/codex-plan-{science,spec,process}.log` and `.sessions`; persistent sol logs/session IDs exist, and commit `9b2eb7d` records that v1.11's variable-order bug killed the first Round 8 sol launches. The top ledger state still supplies no exact commands, per-topic artifacts, or session IDs.
- In-memory replays with bytecode disabled: `review_round_tracking.validate` accepted a silent process#2 body rewrite; the closure regex hid both an incidental dated token in an open title and a dated marker with an empty rationale.
- Direct read-only replay of `tools/check_acceptance.sh plan`: science passed at 92 while process/spec remained below 90, and source inspection confirmed the script checks incidental sol files plus kimi presence rather than a registered acceptance manifest.
- Static/diff verification of the v1.11 mandatory-allowlist placement, resume prompt, failed-review cleanup, empty-glob check, second tie-break batch, and unchanged G3 sole-authority/subordinate text. The resume and empty-glob fixes work; Findings 1, 2, 4, 9, and 17 describe the remaining mechanical gaps.
- Matrix arithmetic from the plan: Phase 3 enumerates 96 runs (66 Task A and 30 Task M); Phase 5 enumerates 27 Task B runs, and its R=32 sequences contain sixteen times as many full segments as R=2. No pilot exists, so actual GB10 throughput or fit against the 24/72/120 GPU-hour budgets cannot be verified.
- No implementation, experiment output, gate artifact, Phase 3/5 pilot, training checkpoint, retrospective, plan-phase acceptance artifact, or tracked amendment review exists; no scientific gate or compute projection could be replayed.
