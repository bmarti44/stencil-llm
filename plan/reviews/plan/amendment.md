# Amendment Review — plan

**Score:** 92 / 100
**Verdict:** PASS (≥90)
**Reviewer model:** codex/gpt-5.6-sol
**Date:** 2026-08-22

## Round log

### Round 3 — 2026-08-22 (codex/gpt-5.6-sol)
- Score: 92 / 100 (delta vs prior round: +4)
- Addressed since prior round:
  - Finding 3 is fixed: AGENTS.md, CLAUDE.md, and README.md now identify PLAN.md as science authority, PROTOCOL.md as process authority, and LEDGER.md as operational state (`AGENTS.md:15-21`, `AGENTS.md:34-35`; `CLAUDE.md:3`; `README.md:5`, `README.md:66`).
  - Finding 4 is mostly fixed: the active retro prompt, score-tool examples, and the cited ledger/amendment tie-break paths now use the `plan/` layout (`tools/codex-prompts/review-retro.md:3`; `tools/check_review_scores.py:6-8`; `plan/LEDGER.md:15-22`; `plan/AMENDMENTS.md:14`, `plan/AMENDMENTS.md:16`).
  - Finding 5 is fixed: every compact amendment entry is now a complete summary and the doubled punctuation is gone (`PLAN.md:11-28`).
- New or remaining:
  - No High/Critical finding remains open; the amendment clears the acceptance threshold.
  - Finding 4 remains Medium because one binding audit artifact and one ledger entry still use stale or ambiguous tie-break names. New Finding 6 is Low: the Round 2 allowlist correction makes the amendment's repeated “verbatim/content unchanged” description inaccurate.

### Round 2 — 2026-08-22 (codex/gpt-5.6-sol)
- Score: 88 / 100 (delta vs prior round: +10)
- Addressed since prior round:
  - Finding 1 is fixed: the no-tool kimi context now places PLAN.md, PROTOCOL.md, LEDGER.md, and AMENDMENTS.md first, and a direct 400,000-byte-cap replay contains all four (`tools/run_kimi_review.py:40-50`).
  - Finding 2 is fixed: the direct-edit rule now explicitly authorizes PLAN.md and the standalone PROTOCOL/LEDGER/AMENDMENTS files while reviewer ownership remains separately protected (`plan/PROTOCOL.md:17-21`).
  - Finding 3 is partly addressed by an explicit governing-set and science/process precedence rule in PLAN.md (`PLAN.md:5`); Finding 4 is partly addressed by moving the active retro/spec prompt directory references to `plan/` (`tools/codex-prompts/review-retro.md:3`; `tools/codex-prompts/review-spec.md:15`).
- New or remaining:
  - No High/Critical finding remains open.
  - Findings 3 and 4 remain Medium because dependent authority prose, the retro ledger pointer, score-tool examples, and migrated audit links are still stale; Finding 5's truncated index remains Low.

### Round 1 — 2026-08-22 (codex/gpt-5.6-sol)
- Score: 78 / 100 (delta vs prior round: +78)
- Addressed since prior round:
  - Initial round. The draft preserves the scientific body and Appendix C thresholds, relocates the tracked review/tie-break artifacts, updates the primary wrapper and acceptance paths, and records the pre-Phase-0 motivation and review-before-commit sequence (`PLAN.md:99-107`, `PLAN.md:149-162`, `plan/LEDGER.md:13`; `tools/check_acceptance.sh:3-10`).
- New or remaining:
  - Two High protocol regressions remain: the no-tool kimi reviewer cannot see the extracted governing files, and the orchestrator's direct-edit allowlist no longer clearly permits the mandatory standalone ledger.
  - The authority wording, active review prompts, audit references, and compact amendment index are not fully reconciled with the new layout.

## Findings

1. **High (resolved 2026-08-22: `CONTEXT_GLOBS` now includes all three extracted governing files and the registered-cap replay contains them) — The no-tool kimi reviewer no longer receives the extracted governing files.** Round 2 re-verification found PLAN.md, PROTOCOL.md, LEDGER.md, and AMENDMENTS.md at the front of the no-tool context inventory (`tools/run_kimi_review.py:40-50`). A direct `build_context` replay at 400,000 bytes returned all four file blocks, so the generic phase and retro rubrics can inspect the protocol and ledger they require (`tools/codex-prompts/review-phase.md:3`; `tools/codex-prompts/review-retro.md:3`).

2. **High (resolved 2026-08-22: the Resolution scope now explicitly authorizes direct edits to PLAN.md and the standalone PROTOCOL/LEDGER/AMENDMENTS files) — The extraction puts mandatory ledger writes outside the orchestrator's explicit direct-edit allowlist.** Round 2 re-verification confirms the allowlist now names `PLAN.md` and the three standalone governed/operational files (`plan/PROTOCOL.md:18`), while the next rules continue to reserve canonical reviews for reviewers and require serialization (`plan/PROTOCOL.md:19-21`). Mandatory write-ahead ledger updates can therefore occur before coder/run launch (`plan/LEDGER.md:9`).

3. **Medium (resolved 2026-08-22: all dependent authority prose now names the split science/process authorities and standalone operational ledger) — The governing-authority description contradicts the split layout.** (updated 2026-08-22: Round 3 re-verification.) PLAN.md defines the governing set and science/process precedence (`PLAN.md:5`); AGENTS.md repeats the same split and routes ambiguity records to the standalone ledger (`AGENTS.md:15-21`, `AGENTS.md:34-35`); CLAUDE.md gives the same cold-start instruction (`CLAUDE.md:3`); and README.md now distinguishes the science specification, process rules, and live state (`README.md:5`, `README.md:66`). The former contradiction is gone.

4. **Medium — The path migration is incomplete in active prompts and audit references.** (updated 2026-08-22: Round 3 re-verification.) The active retro/spec prompts and score-tool examples are fixed (`tools/codex-prompts/review-retro.md:3`; `tools/codex-prompts/review-spec.md:15`; `tools/check_review_scores.py:6-8`), and the formerly broken ledger/amendment references now name `plan/tiebreaks/plan.md` and `plan/tiebreaks/plan-prompt-3.md` (`plan/LEDGER.md:15-22`; `plan/AMENDMENTS.md:14`, `plan/AMENDMENTS.md:16`). Two audit residues remain: the binding Human adjudication 2 record still says artifacts moved to nonexistent `docs/tiebreaks/` (`plan/tiebreaks/plan.md:89-94`), and the batch-3 ledger entry identifies the raw verdict only as bare `tiebreaks.md` instead of `plan/tiebreaks/plan.md` (`plan/LEDGER.md:16`). That leaves the v1.17 statement that residual stragglers were fixed overstated (`plan/AMENDMENTS.md:7`).

5. **Low (resolved 2026-08-22: all index entries are complete one-line summaries and the doubled punctuation was removed) — The compact amendment index is truncated rather than summarized.** (updated 2026-08-22: Round 3 re-verification.) PLAN.md labels the index as orientation-only and now gives a complete summary for every v1.0-v1.17 entry (`PLAN.md:9-28`).

6. **Low — The amendment inaccurately calls the extracted protocol verbatim and content-unchanged.** The Round 2 fix necessarily changed the inherited Resolution-scope rule by adding PLAN.md and the three standalone `plan/` files to the direct-edit allowlist (`plan/PROTOCOL.md:18`), yet both the protocol preamble and PLAN.md still call the extraction “verbatim” or “content unchanged” (`plan/PROTOCOL.md:3`; `PLAN.md:101`), and the full v1.17 entry repeats “extracted verbatim” (`plan/AMENDMENTS.md:7`). The change is legitimate and restores intended operability, but the provenance claim should describe the reviewed normalization instead of denying it occurred.

## Recommendations

1. Add dated relocation annotations to the binding Human adjudication 2 line and the batch-3 ledger entry, naming `plan/tiebreaks/plan.md` exactly (`plan/tiebreaks/plan.md:92`; `plan/LEDGER.md:16`), then narrow the v1.17 completeness claim accordingly if any historical text is intentionally preserved (`plan/AMENDMENTS.md:7`).
2. Replace “extracted verbatim/content unchanged” with an accurate statement such as “extracted with path normalization and the review-required direct-edit clarification” (`PLAN.md:101`; `plan/PROTOCOL.md:3`, `plan/PROTOCOL.md:18`; `plan/AMENDMENTS.md:7`).

## Evidence consulted

- `PLAN.md`, read in full again; `plan/PROTOCOL.md`, `plan/LEDGER.md`, `plan/AMENDMENTS.md`, `README.md`, `AGENTS.md`, `CLAUDE.md`, `plan/tiebreaks/plan.md`, and the complete prior amendment review.
- Full working-tree and staged diffs against `0a28d36`, with focused re-verification of every existing finding and the Round 2 fixes.
- Repository-wide reference scans for stale `docs/` paths, authority wording, PLAN-ledger wording, and relocated tie-break names; historical reviewer-authored logs were distinguished from live instructions and governed audit records.
- Read-only syntax checks for `tools/check_acceptance.sh` and `tools/run_codex_review.sh`.
- Direct `build_context` replay with the registered 400,000 maximum argument: PLAN.md, PROTOCOL.md, LEDGER.md, and AMENDMENTS.md are all present.
- Direct read-only replay of `bash tools/check_acceptance.sh plan`: amendment, science, and spec pass at 92 after this round; process remains 89, with no artifact-layout failure.
- Ledger launch audit: the top state remains pre-Phase-0 and review-before-commit (`plan/LEDGER.md:13`); no phase threshold is frozen and the amendment changes no threshold.
