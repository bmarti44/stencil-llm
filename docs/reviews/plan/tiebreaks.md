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
