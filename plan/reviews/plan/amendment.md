# Amendment Review — plan

**Score:** 72 / 100
**Verdict:** FAIL (<75)
**Reviewer model:** codex/gpt-5.6-sol
**Date:** 2026-08-22

## Round log

### Round 15 — 2026-08-22 (codex/gpt-5.6-sol)
- Score: 72 / 100 (delta vs prior round: +4)
- Reviewed tree: 2a6c01eab22a77c25fed5fd9994cddf4bcd43568
- Addressed since prior round:
  - Finding 11 is narrowed: acceptance now parses the topic token separately from its optional `kimi` flag, and a direct `bash tools/check_acceptance.sh plan` replay no longer emits the three false manifest-layout failures (`tools/check_acceptance.sh:17-32`; `plan/reviews/plan/topics.txt:1-4`).
  - The tie-break runner can now compare quoted prompt lines against a supplied review file, and kimi's artifact inventory adds byte counts and content hashes for present paths (`tools/run_tiebreak.py:4-8`, `tools/run_tiebreak.py:41-50`; `tools/run_kimi_review.py:82-100`). The v1.22 draft remains pre-Phase-0 and changes no Appendix C threshold (`PLAN.md:11`; `PLAN.md:92`, `PLAN.md:470-486`; `plan/LEDGER.md:13`).
- New or remaining:
  - High Finding 11 remains open: the review-file argument is optional, even the review heading can satisfy its exact-line check, neither argument is source-verified, and arbitrary output paths/run handoffs remain; `artifacts.txt` is still optional and absent, with no rendered-description contract for binaries (`tools/run_tiebreak.py:4-8`, `tools/run_tiebreak.py:41-82`; `plan/PROTOCOL.md:19`, `plan/PROTOCOL.md:24`; `tools/run_kimi_review.py:82-100`). The claim that all five process Mediums are complete therefore remains false (`PLAN.md:11`; `plan/AMENDMENTS.md:7`; `plan/LEDGER.md:13`).
  - Finding 9 remains Medium and unchanged; Findings 4 and 6 remain Low (`tools/run_codex_agent.sh:66-72`, `tools/run_codex_agent.sh:95-101`, `tools/run_codex_agent.sh:125-146`; `plan/LEDGER.md:31`; `plan/AMENDMENTS.md:12`). Twelve outside-canonical paths remain modified, including the process/tie-break artifacts and untracked topic manifest; all are included in the reviewed tree id and were not modified by this reviewer.

### Round 14 — 2026-08-22 (codex/gpt-5.6-sol)
- Score: 68 / 100 (delta vs prior round: +0)
- Reviewed tree: 57f880ddc3d44db6f0e60431022225fe24d7b126
- Addressed since prior round:
  - Finding 11 is partly addressed: process#31 is now genuinely fixed because retro-originated AGENTS.md changes require an accepted amendment review, and the topic/artifact/tie-break paths gained explicit protocol text plus wrapper checks (`plan/PROTOCOL.md:19`, `plan/PROTOCOL.md:30`; `tools/run_codex_review.sh:121-126`; `tools/run_kimi_review.py:82-95`, `tools/run_kimi_review.py:142-148`; `tools/run_tiebreak.py:22-68`).
  - The v1.22 draft remains pre-Phase-0, changes no Appendix C threshold, and preserves Finding 10's batch-4 vacatur and direct G3 repairs (`PLAN.md:11`, `PLAN.md:379`, `PLAN.md:470-486`, `PLAN.md:497-498`; `plan/tiebreaks/plan.md:140-142`).
- New or remaining:
  - High Finding 11 remains open: the new `<topic> kimi` syntax makes `check_acceptance.sh` reject every flagged codex review, while #27's marker check and #29's optional existence-only artifact list still do not establish the claimed complete records (`tools/check_acceptance.sh:17-32`; `plan/reviews/plan/topics.txt:1-4`; `tools/run_tiebreak.py:36-68`; `plan/PROTOCOL.md:19`; `tools/run_kimi_review.py:82-95`).
  - Finding 9 remains Medium and unchanged; Findings 4 and 6 remain Low (`tools/run_codex_agent.sh:66-72`, `tools/run_codex_agent.sh:95-101`, `tools/run_codex_agent.sh:125-146`; `plan/LEDGER.md:31`; `plan/AMENDMENTS.md:12`). Twelve outside-canonical paths remain modified, including the process/tie-break artifacts and untracked topic manifest; all are included in the reviewed tree id and were not modified by this reviewer.

### Round 13 — 2026-08-22 (codex/gpt-5.6-sol)
- Score: 68 / 100 (delta vs prior round: +10)
- Reviewed tree: dd43637c648a239bc55b41e097227a3502223df8
- Addressed since prior round:
  - Finding 10 is fixed: batch 4 is explicitly VACATED, its false closures are withdrawn, the tie-break rule now requires verbatim finding/argument text, and the three cited G3 contradictions were corrected directly (`plan/tiebreaks/plan.md:140-142`; `plan/AMENDMENTS.md:7`; `plan/PROTOCOL.md:24`; `PLAN.md:379`, `PLAN.md:497-498`).
  - The v1.22 draft also makes partial, useful repairs to the tie-break runner, kimi context disclosure, and sol-topic acceptance checks; it remains pre-Phase-0 and changes no Appendix C threshold (`tools/run_tiebreak.py:18-54`; `tools/run_kimi_review.py:60-86`; `tools/check_acceptance.sh:12-30`; `PLAN.md:92`, `PLAN.md:470-486`).
- New or remaining:
  - New High Finding 11 blocks acceptance: the replacement claim that all five process Mediums were fixed omits #31 entirely and does not finish #27, #29, or #36; only #35 is actually closed by the current tree (`PLAN.md:11`; `plan/AMENDMENTS.md:7`; `plan/LEDGER.md:13`; `plan/reviews/plan/process.md:266-284`).
  - Finding 9 remains Medium because the coder baseline is still not Git-semantic or set-complete and session provenance remains fail-open (`tools/run_codex_agent.sh:66-72`, `tools/run_codex_agent.sh:95-101`, `tools/run_codex_agent.sh:125-146`). Findings 4 and 6 remain Low historical nits (`plan/LEDGER.md:29`; `plan/AMENDMENTS.md:12`). Eleven outside-canonical paths remain modified, including the process/tie-break artifacts and untracked `plan/reviews/plan/topics.txt`; all are included in the reviewed tree id and were not modified by this reviewer.

### Round 12 — 2026-08-22 (codex/gpt-5.6-sol)
- Score: 58 / 100 (delta vs prior round: -26)
- Reviewed tree: e1b3ab155a2b934450ce661bec63ad2b17692111
- Addressed since prior round:
  - Finding 9's normal-workflow false failure is fixed: the wrapper now snapshots pre-launch dirty regular-file content and exempts byte-identical baseline paths, so the mandatory uncommitted write-ahead ledger entry no longer fails an otherwise in-scope coder run (`plan/LEDGER.md:9`; `tools/run_codex_agent.sh:95-101`, `tools/run_codex_agent.sh:125-146`). The stale `/tmp` header is also corrected and a provenance-append failure still forces exit 8 (`tools/run_codex_agent.sh:7-10`, `tools/run_codex_agent.sh:66-89`).
  - The v1.22 draft remains pre-Phase-0, changes no scientific threshold or Appendix C row, and corrects the prior STATE's amendment score to the accepted v1.21 score of 90 (`PLAN.md:11`; `plan/LEDGER.md:13`; `plan/AMENDMENTS.md:7`).
- New or remaining:
  - New Critical Finding 10 blocks acceptance: batch 4 was explicitly launched to move a process review stuck at 89 to acceptance, but its prompt replaces all five live Medium findings with materially narrower strawmen and falsely says the reviewer never enumerated the G3 contradictions (`plan/tiebreaks/plan-prompt-4.md:1-7`; `plan/reviews/plan/process.md:266-284`). The resulting verdicts do not adjudicate the evidence that the protocol requires kimi to receive.
  - Finding 9 remains Medium: the baseline is not Git-semantic or set-complete, so mode-only changes, same-content symlink retargets, fixed-string path-prefix collisions, and deletion of pre-existing untracked files can escape the scope check; the actual-session-id requirement also remains fail-open (`plan/PROTOCOL.md:18`, `plan/PROTOCOL.md:21`; `tools/run_codex_agent.sh:66-72`, `tools/run_codex_agent.sh:95-101`, `tools/run_codex_agent.sh:125-146`). Findings 4 and 6 remain Low historical nits (`plan/LEDGER.md:27`; `plan/AMENDMENTS.md:12`).

### Round 11 — 2026-08-22 (codex/gpt-5.6-sol)
- Score: 84 / 100 (delta vs prior round: -6)
- Reviewed tree: 3377e10374f72be6238ba03f75674da0051942e3
- Addressed since prior round:
  - Commit `1ad6581` landed the exact v1.21 tree accepted in Round 10: independently hashing parent `46e17e2` plus the landed full-index binary diff while excluding only this canonical review reconstructs `02f1a93225b7374010f4a4ce2eccc2989ba6fc78` (`plan/reviews/plan/amendment.md:10-18`; `tools/amend.sh:23-54`).
  - The v1.22 draft fixes one Finding 9 limb by turning a failed provenance append into exit 8, and it corrects the prior STATE's amendment score from 92 to 90 (`tools/run_codex_agent.sh:66-86`; `plan/LEDGER.md:13`; `plan/AMENDMENTS.md:7`). It changes no scientific threshold and remains before Phase 0 (`PLAN.md:11`; `PLAN.md:92`; `PLAN.md:471`).
- New or remaining:
  - Finding 9 is Medium again: v1.22 removes the ledger exemption without baselining pre-launch state, so the mandatory uncommitted write-ahead ledger edit is attributed to the coder and hard-fails an otherwise in-scope run (`plan/LEDGER.md:9`; `tools/run_codex_agent.sh:118-134`). The missing-session tolerance and stale `/tmp` header also remain.
  - No High/Critical finding is open, but v1.22 does not clear 90. Findings 4 and 6 remain Low historical nits (`plan/LEDGER.md:27`; `plan/AMENDMENTS.md:12`). Outside-canonical process Round 19 and tie-break batch-4 artifacts remain modified at `plan/reviews/plan/process.md:1-17` and `plan/tiebreaks/plan.md:97-138`; both are included in the reviewed tree id and were not modified by this reviewer.

### Round 10 — 2026-08-22 (codex/gpt-5.6-sol)
- Score: 90 / 100 (delta vs prior round: +2)
- Reviewed tree: 02f1a93225b7374010f4a4ce2eccc2989ba6fc78
- Addressed since prior round:
  - Finding 9 is reduced to Low: the mandatory allowlist is now validated before `codex exec`; an EXIT finalizer records successful, failed, and scope-violating launched runs; and every ledger field is passed as a quoted Python argument rather than interpolated into code (`tools/run_codex_agent.sh:59-86`, `tools/run_codex_agent.sh:97-131`).
  - The v1.21 draft still uses the accepted tree-bound amendment transaction, changes no scientific threshold, and remains before Phase 0 (`PLAN.md:11`; `plan/PROTOCOL.md:30`; `plan/LEDGER.md:13`; `tools/amend.sh:56-86`).
- New or remaining:
  - No High/Critical finding remains open; v1.21 clears the amendment threshold. Finding 9 retains a Low tail because a missing session event is accepted as a marker rather than the required actual id, and a failed provenance append does not change the wrapper's exit status (`plan/PROTOCOL.md:18`; `tools/run_codex_agent.sh:66-86`). Findings 4 and 6 remain Low historical nits (`plan/LEDGER.md:25`; `plan/AMENDMENTS.md:11`).
  - Outside-canonical process Round 18 drift remains at `plan/reviews/plan/process.md:1-21`; it is included in the reviewed tree id, was inspected, and was not modified by this reviewer.

### Round 9 — 2026-08-22 (codex/gpt-5.6-sol)
- Score: 88 / 100 (delta vs prior round: +4)
- Reviewed tree: 56c3753dea6e9f37a4f0654e4d43da363323a84a
- Addressed since prior round:
  - Finding 9 is materially narrowed: coder output now goes to persistent `results/logs/`, overrides without a reason are rejected, codex runs in JSON mode, the wrapper-owned ledger/log paths no longer trip the coder allowlist, and the provenance record is inserted newest-first after a successful scope scan (`tools/run_codex_agent.sh:59-77`, `tools/run_codex_agent.sh:83-125`).
  - The v1.21 history candidly records that the first provenance implementation failed this review and was corrected within the still-uncommitted tree (`plan/AMENDMENTS.md:7`). The amendment still changes no threshold and remains pre-Phase-0 (`PLAN.md:11`; `plan/LEDGER.md:13`).
- New or remaining:
  - Finding 9 remains Medium: the mandatory allowlist is still checked only after `codex exec`; missing-allowlist and scope-violation exits occur before provenance insertion; a missing session event is silently recorded as `unknown`; and unescaped environment/user text is interpolated into executable Python (`tools/run_codex_agent.sh:68-77`, `tools/run_codex_agent.sh:83-125`).
  - No High/Critical finding is open, but the amendment remains below 90. Findings 4 and 6 remain Low (`plan/LEDGER.md:25`; `plan/AMENDMENTS.md:11`). The outside-canonical process Round 18 artifact at `plan/reviews/plan/process.md:1-21` remains part of the bound tree and was not modified by this reviewer.

### Round 8 — 2026-08-22 (codex/gpt-5.6-sol)
- Score: 84 / 100 (delta vs prior round: -8)
- Reviewed tree: 240834e852a4fadb5469fc5bfd1eb08e692380b1
- Addressed since prior round:
  - Commit `46e17e2` landed v1.20 through the accepted pre-commit path: independently hashing its parent plus the full-index binary commit diff while excluding only the canonical amendment review reconstructs Round 7's exact id `a9397066cb8407f3a4b97a38c30ed4a31d2616db` (`tools/amend.sh:23-54`; `plan/reviews/plan/amendment.md:10-18`).
  - The v1.21 draft fixes the structurally stale post-amendment STATE and the version-namespace Low: the reviewed entry declares that v1.21 lands in this commit, names the first pending post-commit action, and `amend.sh` rejects a non-`vX.Y` argument before taking the lock (`plan/LEDGER.md:13`; `plan/PROTOCOL.md:30`; `tools/amend.sh:56-59`, `tools/amend.sh:73-84`).
- New or remaining:
  - New Medium Finding 9 keeps the amendment below acceptance: the coder-provenance append omits the mandatory session id and override rationale, is written at the oldest end of a newest-first ledger, and becomes an undeclared scope violation unless every coder allowlist includes the wrapper's own ledger mutation (`plan/PROTOCOL.md:18`; `plan/LEDGER.md:7-9`; `tools/run_codex_agent.sh:74-103`).
  - No High/Critical finding is open. Findings 4 and 6 remain Low (`plan/LEDGER.md:25`; `plan/AMENDMENTS.md:11`). The outside-canonical process Round 18 artifact remains modified at `plan/reviews/plan/process.md:1-21`; it is included in the reviewed tree id and was not modified by this reviewer.

### Round 7 — 2026-08-22 (codex/gpt-5.6-sol)
- Score: 92 / 100 (delta vs prior round: +10)
- Reviewed tree: a9397066cb8407f3a4b97a38c30ed4a31d2616db
- Addressed since prior round:
  - Finding 8 is fixed: tracked changes are now hashed from a checked full-index binary diff with text conversion and external diff drivers disabled, closing the remaining content-identity gap (`tools/amend.sh:30-32`).
  - The STATE parser now selects the first literal backticked `next command:` field and requires it to start with the exact `bash tools/amend.sh v1.20` invocation; adversarial replays reject an earlier review command followed by a later amendment clause and reject a prefixed fake command (`tools/amend.sh:73-81`). The top ledger entry now states the review round generically and names the correct v1.20 commit command (`plan/LEDGER.md:13`).
- New or remaining:
  - No High/Critical finding remains open; the amendment clears the acceptance threshold. Findings 4 and 6 remain Low historical-provenance nits (`plan/LEDGER.md:23`; `plan/AMENDMENTS.md:10`).
  - Outside-canonical drift remains at `plan/reviews/plan/process.md:1-21`; it is included in the quoted tree id and was inspected, so it no longer creates an artifact-binding mismatch. It was not modified by this reviewer.

### Round 6 — 2026-08-22 (codex/gpt-5.6-sol)
- Score: 82 / 100 (delta vs prior round: +10)
- Reviewed tree: abdca92083e79d8cd049de6ba98a64127539a156
- Addressed since prior round:
  - Finding 8 is materially narrowed: the untracked-path stream is now NUL-delimited, uses `lstat`, hashes symlink payloads and executable state, and makes every Git query fail closed with `check=True` (`tools/amend.sh:23-54`). The mandatory command succeeds twice with the same id and no index/status mutation.
  - The current top STATE now names `bash tools/amend.sh v1.20 ...` as its actual next command after acceptance, and the v1.20 draft still changes no scientific threshold before Phase 0 (`plan/LEDGER.md:13`; `PLAN.md:11`; `plan/PROTOCOL.md:30`).
- New or remaining:
  - High Finding 8 remains open: tracked binary content is still represented by Git's default non-binary patch rather than full bytes, and the supposed first-command parser actually selects the last matching clause and accepts any command containing `amend.sh v1.20` (`tools/amend.sh:30-32`, `tools/amend.sh:76-77`).
  - The top ledger falsely says amendment review Round 7 is running while this canonical round is Round 6, and the unrelated process-review drift remains in the repo-wide amendment transaction (`plan/LEDGER.md:13`; `plan/reviews/plan/process.md:1-21`). Findings 4 and 6 also remain Low.

### Round 5 — 2026-08-22 (codex/gpt-5.6-sol)
- Score: 72 / 100 (delta vs prior round: +4)
- Reviewed tree: fa564e8ce227751629d29c9f9a3e0cedd4113ced
- Addressed since prior round:
  - Finding 7's execution failure is fixed: `--tree-id` now uses read-only Git queries and byte reads rather than an alternate index, returns a nonempty 40-hex identifier with exit 0 in the reviewer sandbox, and leaves the real index/status unchanged (`tools/amend.sh:15-43`).
  - The revised tree continues to acknowledge the v1.18/v1.19 sequencing violations, changes no scientific threshold, and remains pre-Phase-0 (`PLAN.md:11`; `plan/AMENDMENTS.md:7`; `plan/PROTOCOL.md:30`; `plan/LEDGER.md:13`).
- New or remaining:
  - New High Finding 8 blocks acceptance: the digest omits Git-significant properties of untracked paths, and the advertised exact-next-command check passes the current STATE even though that STATE says another review is next.
  - Findings 4 and 6 remain Low: the historical bare tie-break filename and “extracted verbatim” history claim are unchanged (`plan/LEDGER.md:21`; `plan/AMENDMENTS.md:10`).

### Round 4 — 2026-08-22 (codex/gpt-5.6-sol)
- Score: 68 / 100 (delta vs prior round: -24)
- Reviewed tree:
- Addressed since prior round:
  - Commit `3f15625` fixes the binding Human adjudication 2 path and makes the PLAN/PROTOCOL extraction description honest, narrowing Findings 4 and 6 (`plan/tiebreaks/plan.md:89-94`; `PLAN.md:104`; `plan/PROTOCOL.md:3`).
  - Commits `3f15625` and `95ce6cd` preserve the v1.18/v1.19 history slips instead of silently rewriting them, and the v1.20 draft admits that both commits violated the binding pre-commit sequence (`PLAN.md:11-14`; `plan/AMENDMENTS.md:7-10`; `plan/PROTOCOL.md:30`; `plan/LEDGER.md:13-17`).
  - The revised v1.20 draft adds score/severity, version, tree-identity, lock, and exact-top-STATE checks in principle (`plan/PROTOCOL.md:30`; `tools/amend.sh:28-46`).
- New or remaining:
  - New High Finding 7 blocks acceptance: the mandatory `bash tools/amend.sh --tree-id` command emitted no output and exited 128 because its supposedly read-only alternate-index operation writes Git objects into the reviewer's read-only `.git` area.
  - Finding 4 is reduced to Low because only one ambiguous historical ledger filename remains. Finding 6 remains Low because the v1.17 full-history entry still says “extracted verbatim.”

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

4. **Low — The path migration is incomplete in active prompts and audit references.** (updated 2026-08-22: Round 14 citation shift; Round 4 severity reduction remains unchanged.) Commit `3f15625` corrects Human adjudication 2 to `plan/tiebreaks/` (`plan/tiebreaks/plan.md:89-94`), and the active prompts, tools, and other governed audit references use the current layout. The sole residue is the historical batch-3 ledger entry's bare `tiebreaks.md` instead of `plan/tiebreaks/plan.md` (`plan/LEDGER.md:31`), which also makes the v1.17 statement that residual stragglers were fixed slightly overstated (`plan/AMENDMENTS.md:12`). This is an audit-navigation nit, not an active-path defect.

5. **Low (resolved 2026-08-22: all index entries are complete one-line summaries and the doubled punctuation was removed) — The compact amendment index is truncated rather than summarized.** (updated 2026-08-22: Round 3 re-verification.) PLAN.md labels the index as orientation-only and now gives a complete summary for every v1.0-v1.17 entry (`PLAN.md:9-28`).

6. **Low — The amendment inaccurately calls the extracted protocol verbatim and content-unchanged.** (updated 2026-08-22: Round 11 citation shift.) Commit `3f15625` makes PLAN.md and the protocol preamble accurate by saying the substance was preserved while inherited self-references were re-scoped (`PLAN.md:106`; `plan/PROTOCOL.md:3`). The full v1.17 history entry alone still says PROTOCOL.md was “extracted verbatim” (`plan/AMENDMENTS.md:12`), despite the reviewed direct-edit clarification now present in the extracted rule (`plan/PROTOCOL.md:18`).

7. **High (resolved 2026-08-22: `--tree-id` now avoids alternate-index/object writes, runs successfully in the reviewer sandbox, and returns a stable nonempty identifier) — The mandatory tree-id binding is neither read-only nor runnable.** (updated 2026-08-22: Round 5 re-verification.) The replacement invokes only `rev-parse`, `diff`, and `ls-files`, then reads working-tree bytes in Python; it creates no alternate index and requests no Git object write (`tools/amend.sh:15-43`). Two exact invocations returned `fa564e8ce227751629d29c9f9a3e0cedd4113ced` with exit 0, while the cached diff remained empty and repository status was unchanged. The original runtime blocker is therefore resolved; Finding 8 separately addresses whether the returned identifier fully binds the tree and sequence claimed by the protocol.

8. **High (resolved 2026-08-22: tracked changes now use a checked full-index binary diff and the STATE parser selects and validates the first amendment command) — The rebuilt binding can certify a different Git tree and the wrong next action.** (updated 2026-08-22: Round 15 artifact-binding re-verification.) The content identity remains fail-closed for the relevant Git state: tracked changes use `git diff --binary --full-index --no-textconv --no-ext-diff` with `check=True`, while untracked names are NUL-delimited and framed with `lstat` type, symlink payload, regular-file bytes, and Git-significant executable state (`tools/amend.sh:23-54`; `plan/PROTOCOL.md:30`). The declared-intent rule binds v1.22 to this commit and requires a nonempty first post-commit command that does not name `amend.sh` (`tools/amend.sh:77-84`). The top STATE declares v1.22 and names process Round 20 next (`plan/LEDGER.md:13`). Two mandatory `--tree-id` runs returned `2a6c01eab22a77c25fed5fd9994cddf4bcd43568` with exit 0 and no index/status mutation. The twelve outside-canonical changes, including the untracked topic manifest, will be staged by `git add -A` (`tools/amend.sh:86`; `plan/reviews/plan/topics.txt:1-4`), but they are included in this content id and were inspected; the binding defect stays closed.

9. **Medium — The coder-provenance fix violates its own ledger and handoff contracts.** (updated 2026-08-22: Round 12 re-verification after the pre-launch-baseline fix.) The wrapper now snapshots dirty regular-file bytes before launch and its post-run matcher exempts an exactly matching ledger entry, closing the Round 11 false failure for the normal write-ahead path (`plan/LEDGER.md:9`; `tools/run_codex_agent.sh:95-101`, `tools/run_codex_agent.sh:125-146`). The scope boundary is still not the promised hard contract. The manifest records only `sha256sum` plus a newline-delimited path for existing dereferenced regular files, and the skip uses unanchored fixed-string search (`tools/run_codex_agent.sh:98-101`, `tools/run_codex_agent.sh:132-136`). Consequently a coder can change only a pre-dirty tracked file's executable bit, retarget a pre-dirty symlink to a same-content referent, or exploit a same-hash path-prefix record and still be classified as baseline; deletion of a pre-existing untracked file vanishes from the post-run `git diff`/`ls-files` inventory and is never examined (`tools/run_codex_agent.sh:125-146`). Direct predicate replays confirmed the mode-only and path-prefix cases are skipped and the deleted-untracked path is absent. The manifest also remains in `/tmp` after every run. Separately, the protocol requires the codex session id actually used, but the wrapper accepts a missing/unparsable compact event as `MISSING-SESSION-EVENT` (`plan/PROTOCOL.md:18`; `tools/run_codex_agent.sh:66-72`). These are real containment/provenance gaps, so the v1.22 history still overclaims that process #11 is closed (`plan/AMENDMENTS.md:7`).

10. **Critical (resolved 2026-08-22: batch 4 was explicitly vacated, its false closures withdrawn, the verbatim-record rule adopted, and the cited G3 contradictions repaired directly) — Batch-4 tie-break rescues a failing process score by adjudicating strawmen.** (updated 2026-08-22: Round 13 source verification.) The raw prompt and verdict remain preserved for audit, but a dated marker now says the batch is VACATED and “closes nothing” (`plan/tiebreaks/plan.md:140-142`); the v1.22 history expressly withdraws both the arbiter's closure and the earlier amendment claim (`plan/AMENDMENTS.md:7`). The protocol now requires the finding text and both arguments verbatim (`plan/PROTOCOL.md:24`), and the exact contradictions that batch 4 falsely called unenumerated are repaired in the governing science text (`PLAN.md:379`, `PLAN.md:497-498`). Those changes independently verify that the dishonest adjudication is no longer being used as authority. Finding 11 separately reviews whether the replacement claim that all five findings were fixed on their merits is true.

11. **High — The replacement “five fixes” claim omits one finding and only partially repairs three others.** (updated 2026-08-22: Round 15 re-verification after the second completeness fix; the immutable title records the Round-13 state.) The former omission remains fixed: retro-originated AGENTS.md edits now require an accepted amendment review, resolving process#31 (`plan/PROTOCOL.md:30`), and process#35 remains fully fixed (`PLAN.md:379`, `PLAN.md:497-498`). The Round-14 acceptance regression is also fixed: the checker accepts the registered `<topic> kimi` grammar and a direct plan replay reports only the expected amendment/process score failures (`tools/check_acceptance.sh:17-34`; `plan/reviews/plan/topics.txt:1-4`). But #27 and #29 remain materially incomplete, and #36 is not as complete as claimed. For #27, supplying a review file is optional; without it the old marker-only prompt still passes local validation, and even with it a prompt quoting only the review's `## Findings` heading passes because the tool verifies that every quoted fragment is some review line, not that the full finding and evidence were quoted. The `Reviewer` and `Orchestrator` arguments remain unstructured substrings with no source comparison; output and rejection paths remain caller-controlled; and the ledger line has neither a stable run id nor the exact next-sol command (`plan/PROTOCOL.md:24`; `tools/run_tiebreak.py:4-8`, `tools/run_tiebreak.py:41-82`). Direct predicate replays confirmed both bypasses. For #29, `artifacts.txt` remains optional, no plan-phase file exists, and a present artifact receives only size/hash metadata: required figures/binaries still have no textual rendering or description presented to kimi (`plan/PROTOCOL.md:19`; `tools/run_kimi_review.py:82-100`; `plan/reviews/plan/process.md:270`). For #36, acceptance is now topic-aware, but the new manifest is still absent from README's component map, and both wrappers permit launch when the manifest itself is absent rather than proving the promised write-ahead registration (`README.md:64-66`; `tools/run_codex_review.sh:121-126`; `tools/run_kimi_review.py:148-154`). PLAN.md, the amendment history, and STATE nevertheless call all five complete (`PLAN.md:11`; `plan/AMENDMENTS.md:7`; `plan/LEDGER.md:13`). The central completeness claim remains materially false, and the optional tie-break verification preserves the same strawman-rescue path that caused Finding 10.

## Recommendations

1. Make the tie-break review-file argument mandatory and validate a structured, complete record: the full finding text and cited evidence, plus separately delimited verbatim Reviewer and Orchestrator arguments. Constrain output and rejection paths to `plan/tiebreaks/`, assign a stable run id, and ledger the exact next sol command (`plan/PROTOCOL.md:24`; `tools/run_tiebreak.py:4-8`, `tools/run_tiebreak.py:41-82`).
2. Make `artifacts.txt` mandatory for gate phases, define its grammar, require every gate-critical text/binary/figure input, and require a textual rendering or description path for non-text entries rather than reporting only size/hash. Add the plan manifest and update README's component map (`plan/PROTOCOL.md:19`; `tools/run_kimi_review.py:82-100`; `README.md:64-66`).
3. Require both review wrappers to fail when `topics.txt` is absent, validate the manifest grammar, and bind its registered topic/lens identity to the write-ahead ledger rather than trusting an independently editable file (`plan/PROTOCOL.md:19`; `tools/run_codex_review.sh:121-126`; `tools/run_kimi_review.py:148-154`; `plan/reviews/plan/topics.txt:1-4`).
4. Withdraw the “all five completely fixed” wording until the current process reviewer verifies the full closures; retain the accurate process#31/#35 repairs and the repaired acceptance parser, and describe #27/#29/#36 as partial (`PLAN.md:11`; `plan/AMENDMENTS.md:7`; `plan/LEDGER.md:13`; `plan/reviews/plan/process.md:266-284`).
5. Replace the coder's line-based byte manifest with an exact keyed pre/post inventory over NUL-delimited paths, Git type/mode, symlink payload, and regular-file bytes; compare the union of both path sets, clean temporary state on every exit, and require a parsed `thread.started` id before success (`plan/PROTOCOL.md:18`, `plan/PROTOCOL.md:21`; `tools/run_codex_agent.sh:66-72`, `tools/run_codex_agent.sh:95-101`, `tools/run_codex_agent.sh:125-146`).
6. Replace the historical ledger's bare `tiebreaks.md` with `plan/tiebreaks/plan.md`, using a dated correction annotation (`plan/LEDGER.md:31`), and correct v1.17's “extracted verbatim” history claim (`plan/AMENDMENTS.md:12`; `PLAN.md:106`; `plan/PROTOCOL.md:3`).

## Evidence consulted

- `PLAN.md`, read in full again (532 lines; SHA-256 `e1bf72289c795dece2fe6d0f906c9e81e4d7c038c88005fa3cb22764518b120f`); `plan/PROTOCOL.md` (SHA-256 `cac3eb7838c5f0f8471a3541ef301383e69dab6bc4f711d94a83e9ad8d03e5e6`), `plan/LEDGER.md`, `plan/AMENDMENTS.md`, `README.md` (read in full; SHA-256 `3f1c987a755b2ee44a53d766ec2c19b68decd6c69e925d499720f698c42f7dfd`), `AGENTS.md`, `CLAUDE.md`, the complete prior amendment review, process Round 19, batch 4, and its vacatur.
- Complete v1.22 working-tree diff against `f5ccb8d`, plus status, cached-diff, untracked-file, and path inventories. Twelve outside-canonical paths are modified: four governed documents, process review, tie-break record, five tools, and untracked `plan/reviews/plan/topics.txt`; there is no staged content. Appendix C and every scientific threshold are untouched, and README remains unchanged.
- Mandatory direct runs of `bash tools/amend.sh --tree-id`: both printed `2a6c01eab22a77c25fed5fd9994cddf4bcd43568` and exited 0; the cached diff remained empty and status was unchanged.
- Side-by-side re-verification of process#27/#29/#31/#35/#36 (`plan/reviews/plan/process.md:266-284`) against the Round-15 changes. The AGENTS governance and G3 repairs satisfy #31/#35; the repaired manifest parser no longer breaks #36 acceptance, but #27/#29 remain partial and topic registration is still not write-ahead-bound mechanically.
- Direct read-only replay of `bash tools/check_acceptance.sh plan`: the Round-14 `science`/`spec`/`process` manifest-layout failures are gone. Amendment still failed at 68 and process at 89; science and spec passed at 92 (`tools/check_acceptance.sh:17-34`; `plan/reviews/plan/topics.txt:1-4`).
- Source-level audits of `tools/amend.sh`, `tools/run_codex_agent.sh`, `tools/run_codex_review.sh`, `tools/run_kimi_review.py`, `tools/run_tiebreak.py`, `tools/check_acceptance.sh`, and `plan/reviews/plan/topics.txt`. Shell syntax checks passed for all edited shell tools, Python AST parses passed for both edited Python tools, and `git diff --check` passed.
- Direct in-memory tie-break predicate replays: without the optional review argument, `Reviewer and Orchestrator disagree >` still passes all local markers; with the review argument, `> ## Findings` plus arbitrary Reviewer/Orchestrator lines passes the exact-line check. This confirms that neither mode establishes the required full finding/evidence/two-argument record (`plan/PROTOCOL.md:24`; `tools/run_tiebreak.py:41-56`). Source inspection also confirmed caller-controlled output/rejection paths and the non-specific ledger continuation (`tools/run_tiebreak.py:68-82`).
- Required-artifact audit: `plan/reviews/plan/artifacts.txt` does not exist, the protocol makes it optional, and present paths receive size plus a 16-hex hash but no textual rendering/description; binaries remain explicitly unavailable to kimi (`plan/PROTOCOL.md:19`; `tools/run_kimi_review.py:82-100`).
- Prior direct coder-baseline replays remain applicable because `tools/run_codex_agent.sh:95-146` is unchanged: mode-only and fixed-string prefix changes can be skipped, deleted pre-existing untracked paths disappear, and a missing session event remains accepted.
- Ledger launch audit: the top state is pre-Phase-0, declares v1.22 as the current amendment transaction, and names process Round 20 next (`plan/LEDGER.md:13`); no phase threshold has frozen and v1.22 changes no threshold.
- Post-write validation: `check_review_scores.py` parses this canonical file at 72 with one open High finding and no open Critical finding; `git diff --check` passes. `bash tools/check_acceptance.sh plan` rejects amendment 72 and process 89 while science/spec remain accepted at 92, with no manifest-layout failure.
