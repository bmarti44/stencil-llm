# Tie-break verdicts — plan review, 2026-08-22 (kimi-k3:cloud, PLAN.md 2b)

## Finding A (sol spec#9)
**Verdict: REFUTE.** In a solo-agent repo the literal ask — a second implementer — is unattainable, so the operative question is whether the fixtures are falsifiable against an authority independent of the generator, and they are: the registered constructions are specified to mechanical hand-execution, fixtures are committed and frozen before the generator exists, and mismatches are adjudicated against the registered text rather than by regenerating. That protocol makes the registered text, not the implementer's choices, the certifying authority. The phase-1 reviewer's hand-verification of committed fixtures against that text is the independent check the finding seeks; imposing this verdict also presumes that hand-verification is actually performed and recorded at phase-1 review.

## Finding B (sol spec#10)
**Verdict: REFUTE.** With commit-pinned reference code, a pinned jax version, registered dimensions/dtype/length/seeds, and the named streams `fixtures:a` and `fixtures:input` fixing A and the inputs, the oracle cases are a pure function of frozen plan text — no authorial discretion remains at generation time, and any later change to those choices is a visible plan diff. Literal arrays in PLAN.md would not add independence either, since the author could only produce them by running the same pinned pipeline; they would add bulk and transcription risk without adding determinism. The phase-2 regenerate-and-diff against the committed npz metadata is an effective independent verification, which closes the self-selection concern the finding raised.

## Finding C (sol process#2)
**Verdict: REFUTE.** The ask is internally inconsistent with the reviewer's own closure protocol: byte-identity of prior rounds forbids the "(resolved DATE: …)" markers that reviewer-authored closure requires, so the rule as stated cannot be enforced without breaking closures. The enforced invariants — immutable round headings and scores, high/critical findings never vanishing, mandatory dated annotations for any other change, validator-checked — preserve the audit trail that byte-identity exists to protect, and the git history of the review file supplies byte-level forensics at zero marginal cost. The finding is closed as refuted: the annotated-history contract is the coherent form of the intent behind the ask.


# Tie-break batch 2 — process review, 2026-08-22 (kimi-k3:cloud)

# TIE-BREAK Verdicts — Process-Review Batch 2 (PLAN.md §2b)

Binding dispositions below. UPHOLD = orchestrator implements the ask; REFUTE = finding closed as refuted; MIDDLE PATH invoked only where strictly cheaper than both poles.

## FINDING 1 (process#1): Direct-checker threshold lowering and forged closure

**Verdict: REFUTE.**

The acceptance path is definitionally wrapper-mediated: `check_acceptance.sh` hardcodes the floor at 90, so no acceptance invocation exists that carries a lowered threshold — a direct call to `check_review_scores.py` produces output, not acceptance, and presenting it as acceptance is already a protocol violation, not an accepted path. Against a principal willing to edit the checker or a reviewer-owned file itself, "mechanical impossibility" is unattainable in a single-user repo, because every enforcement bit is writable by that same principal; ACLs or sandboxing are outside what this environment can express. The residual control is the standing detection architecture of this protocol — git history plus the resumed reviewer round that sees its own file and can demand the wrapper transcript — which is the same trust model every other gate already operates under. The finding restates a threat-model constant as a closable gap.

## FINDING 2 (process#2): Silent finding substitution via body edits

**Verdict: REFUTE.**

Batch 1 already REFUTED byte-identity immutability, and body immutability is that same claim re-scoped — it directly conflicts with the header-mandated `(updated ...)` annotation workflow, which requires bodies to remain editable. The substitution risk is controlled by immutable titles, dated closure markers, and the next reviewer round's standing instruction to diff bodies against its own in-context prior text; unannotated edits are protocol violations the protocol already names, not behavior it accepts. No request for a cheaper mechanism that preserves the mandated annotation workflow has been made, and none is apparent.

## FINDING 3 (process#4): Ledger cannot deliver exact cold restart

**Verdict: REFUTE.**

The ledger's promise is a capability, and that capability has now been exercised: the registered stack (topmost STATE line with exact next command, write-ahead entries with log paths, persistent logs, git status reconciliation, DONE-marker matrix resume) has cold-restarted this project across multiple sessions without a cited failure attributable to the prose format. A finding that concedes the capability but prescribes a different mechanism is an implementation preference, not a gap. The proposed parallel schema would hold the same facts in a second source of truth and drift from the prose, recreating exactly the inconsistency risk the write-ahead discipline currently avoids. If a future cold restart demonstrably fails because of the format, a new finding may be filed against that concrete failure.

## FINDING 4 (process#9): Coder scope allowlists and restore-on-failure

**Verdict: MIDDLE PATH — UPHOLD on mandatory per-brief allowlists; REFUTE on coder restore-on-failure.**

Mandatory allowlists are the orchestrator's own offered concession: the artifacts are implemented and already ship with every Phase 0+ brief, so converting "always shipped" to "mandatory" is a one-line rule change — strictly cheaper than the reviewer's full ask (which includes restore machinery) and a de-minimis delta from the orchestrator's nominal stance that it itself concedes. Restore-on-failure for coders is rejected on correctness, not cost: a coder's interrupted dirty state is the primary diagnostic and salvage artifact, and auto-reverting it would destroy exactly what the root-cause rule exists to examine, whereas the reviewer wrapper restores precisely because reviewer runs mutate nothing worth keeping. The existing full dirty-diff failure report provides containment without evidence destruction; orchestrator shall mark allowlists mandatory in the brief schema and close the restore half as refuted.

---

All four findings are hereby disposed. The process-review score hold at 74 is released for the affected items per their verdicts, and no further resolve-or-refute rounds on these findings are permitted.

# Human adjudication — 2026-08-22

Sol's process round 8 disputed the executed batch-2 tie-breaks. Under Autonomy-policy touchpoint (1) the human (Brian Martin) ruled: OVERRULE SOL. Process findings #1, #2, #4, #9 close as `(refuted 2026-08-22: human override — trust-model constants of a single-user repo; detection via git history and resumed reviewer sessions is the registered control; see tie-break batch 2)`. This adjudication is final for these four findings; subsequent rounds re-score on the remaining substance.


# Tie-break — 2026-08-22 12:26 UTC (kimi-k3:cloud)

## Prompt (verbatim)

```
You are kimi-k3 acting as TIE-BREAK arbiter under PLAN.md Section 2b of the Stencil project (batch 3). Two long-standing orchestrator declines are the process review's explicitly named remaining promotion blockers (score capped at 89, zero open high/critical findings, ~6 rounds of exchange). Render binding verdicts: UPHOLD (orchestrator implements) or REFUTE (closes as refuted).

DECLINE A: Atomic gate-acceptance enforcement. Reviewer's ask: one mechanical transaction that verifies gate tests, review scores, kimi presence, ledger entry, and README row before a gate commit can exist (e.g., enforced pre-commit hook). Orchestrator's rationale: the checklist is registered procedure whose every item leaves git-visible evidence; check_acceptance.sh mechanizes the review-score item (hardcoded thresholds); a hook enforcing the rest must parse prose artifacts (ledger, README) and would be gameable by the same principal that runs it, adding brittleness without adding trust; violations are detectable post-hoc by reviewers, which is this protocol's general trust model (cf. batch-2 finding-1 REFUTE: "mechanical impossibility is unattainable when every enforcement bit is writable by the same principal").

DECLINE B: The initial-loop amendment-sequencing exception. Rule: amendments take effect only after an accepted amendment review. Exception (ledger-recorded, rule-7 conservative interpretation): while the plan itself is still in its acceptance loop, each amendment batch is reviewed by the very next round of the same held reviewer sessions — the loop IS the review — and requiring pre-commit acceptance would deadlock (reviewers review committed state). The exception self-extinguishes at plan acceptance, after which the pre-commit rule binds unconditionally. Reviewer holds each batch "again took effect before the mandatory review."

Answer in markdown: per decline, heading, verdict, 2-4 sentence rationale.

```

## Raw verdict

# TIE-BREAK RULINGS — Stencil Batch 3 (PLAN.md §2b)

Arbiter: kimi-k3. Verdicts are binding; both rulings close their respective findings.

## Decline A — Atomic Gate-Acceptance Enforcement

**Verdict: REFUTE** (finding closed; decline stands)

The proposed hook is not an independent control: every enforcement bit — the hook itself, its prose-parsing heuristics, and the artifacts it inspects — is writable by the same principal it constrains, and git offers trivial bypass (`--no-verify`), so it adds friction and brittleness without adding assurance. This was settled as process precedent in batch-2 finding-1 ("mechanical impossibility is unattainable when every enforcement bit is writable by the same principal"), and no distinguishing factor has been shown here. The one mechanically decidable item — review scores against thresholds — is already enforced by check_acceptance.sh, while the remainder (ledger prose, README rows) is satisfiable by pattern-matching without substance. The protocol's actual control remains post-hoc reviewer audit of git-visible evidence, and that control is intact; the finding therefore does not identify implementable assurance.

## Decline B — Initial-Loop Amendment-Sequencing Exception

**Verdict: REFUTE** (finding closed; decline stands)

Applied to the bootstrap phase, the unqualified rule deadlocks: reviewers review committed state, so no amendment could ever reach an accepted review without first taking effect — the exception is the minimal reading that preserves reviewability rather than evading it. It is tightly scoped: ledger-recorded, grounded in a rule-7 conservative interpretation, confined to the plan's own acceptance loop, and self-extinguishing at acceptance, after which the pre-commit rule binds without exception. Substantively, no amendment escaped review — each batch was examined by the very next round of the same held sessions, and the acceptance gate guarantees that nothing attains accepted status without cumulative reviewer assent, which is the invariant the sequencing rule exists to protect. The objection is formal sequencing with no showing of unreviewed or harmful substance, and is closed as refuted.

---

**Promotion status:** Both named blockers are closed by binding refutation. The score cap's basis is removed; the orchestrator may proceed under Section 2b with the ledger updated to record these two rulings.

# Human adjudication 2 — 2026-08-22 (batch-3 dispute)

Sol's process round 13 disputed both batch-3 refutations. The human ruled: PARTIAL CONCESSION.
- Conceded, with credit to the reviewer: (1) finding #38's demonstrated failure class — tie-break artifacts moved to docs/tiebreaks/, and check_acceptance.sh now validates the exact registered artifact layout (frontmatter-declared reviewer identity; unexpected files are violations, not skips). (2) The batch-3 deadlock premise on sequencing was FALSE — review-amendment.md reviews a draft or working-tree diff, so pre-commit amendment review was always operationally possible. Pre-commit amendment review is binding from this ruling forward, mechanism: working-tree diff review before the amendment commit lands.
- Declined: re-litigation of the already-run initial loop (its substance was reviewed round-by-round; no unreviewed amendment reached accepted status), and the full atomic evidence-parsing transaction beyond the exact-artifact validation now implemented.
This adjudication is final. Process findings #17/#22 close as (resolved 2026-08-22: partial concession implemented — exact-artifact acceptance validation + binding pre-commit amendment review) rather than refuted, reflecting that the reviewer was substantially right.
