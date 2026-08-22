# Amendment Review — plan

**Score:** 90 / 100
**Verdict:** PASS (≥90)
**Reviewer model:** codex/gpt-5.6-sol
**Date:** 2026-08-22

## Round log

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

4. **Low — The path migration is incomplete in active prompts and audit references.** (updated 2026-08-22: Round 8 citation shift; Round 4 severity reduction remains unchanged.) Commit `3f15625` corrects Human adjudication 2 to `plan/tiebreaks/` (`plan/tiebreaks/plan.md:89-94`), and the active prompts, tools, and other governed audit references use the current layout. The sole residue is the historical batch-3 ledger entry's bare `tiebreaks.md` instead of `plan/tiebreaks/plan.md` (`plan/LEDGER.md:25`), which also makes the v1.17 statement that residual stragglers were fixed slightly overstated (`plan/AMENDMENTS.md:11`). This is an audit-navigation nit, not an active-path defect.

5. **Low (resolved 2026-08-22: all index entries are complete one-line summaries and the doubled punctuation was removed) — The compact amendment index is truncated rather than summarized.** (updated 2026-08-22: Round 3 re-verification.) PLAN.md labels the index as orientation-only and now gives a complete summary for every v1.0-v1.17 entry (`PLAN.md:9-28`).

6. **Low — The amendment inaccurately calls the extracted protocol verbatim and content-unchanged.** (updated 2026-08-22: Round 8 citation shift.) Commit `3f15625` makes PLAN.md and the protocol preamble accurate by saying the substance was preserved while inherited self-references were re-scoped (`PLAN.md:105`; `plan/PROTOCOL.md:3`). The full v1.17 history entry alone still says PROTOCOL.md was “extracted verbatim” (`plan/AMENDMENTS.md:11`), despite the reviewed direct-edit clarification now present in the extracted rule (`plan/PROTOCOL.md:18`).

7. **High (resolved 2026-08-22: `--tree-id` now avoids alternate-index/object writes, runs successfully in the reviewer sandbox, and returns a stable nonempty identifier) — The mandatory tree-id binding is neither read-only nor runnable.** (updated 2026-08-22: Round 5 re-verification.) The replacement invokes only `rev-parse`, `diff`, and `ls-files`, then reads working-tree bytes in Python; it creates no alternate index and requests no Git object write (`tools/amend.sh:15-43`). Two exact invocations returned `fa564e8ce227751629d29c9f9a3e0cedd4113ced` with exit 0, while the cached diff remained empty and repository status was unchanged. The original runtime blocker is therefore resolved; Finding 8 separately addresses whether the returned identifier fully binds the tree and sequence claimed by the protocol.

8. **High (resolved 2026-08-22: tracked changes now use a checked full-index binary diff and the STATE parser selects and validates the first amendment command) — The rebuilt binding can certify a different Git tree and the wrong next action.** (updated 2026-08-22: Round 10 artifact-binding re-verification.) The content identity remains fail-closed for the relevant Git state: tracked changes use `git diff --binary --full-index --no-textconv --no-ext-diff` with `check=True`, while untracked names are NUL-delimited and framed with `lstat` type, symlink payload, regular-file bytes, and Git-significant executable state (`tools/amend.sh:23-54`; `plan/PROTOCOL.md:30`). v1.21 uses a tree-bound declaration that this version lands in this commit and a nonempty first post-commit command that must not name `amend.sh` (`tools/amend.sh:73-84`). The top STATE declares v1.21 and names process Round 19 as the next action (`plan/LEDGER.md:13`). Two mandatory `--tree-id` runs returned `02f1a93225b7374010f4a4ce2eccc2989ba6fc78` with exit 0 and no index/status mutation. The outside-canonical `plan/reviews/plan/process.md` modification will be staged by `git add -A` (`tools/amend.sh:86`; `plan/reviews/plan/process.md:1-21`), but it is included in this content id and was inspected; the binding defect stays closed.

9. **Low — The coder-provenance fix violates its own ledger and handoff contracts.** (updated 2026-08-22: Round 10 re-verification and severity reduction after the second fix.) The wrapper now checks the mandatory allowlist before launch (`tools/run_codex_agent.sh:59-64`), installs a finalizer before `codex exec` so successful, failed, and scope-violating launched runs all reach provenance (`tools/run_codex_agent.sh:66-86`, `tools/run_codex_agent.sh:97-137`), keeps the JSON log under `results/logs/`, rejects unexplained model/effort overrides, inserts newest-first, and passes untrusted record fields as quoted Python arguments under a literal heredoc (`tools/run_codex_agent.sh:73-94`). Those changes close every normal-path defect from Rounds 8-9. Two robustness residues remain. The protocol requires the codex session id actually used, but a missing or unparsable event is accepted as `MISSING-SESSION-EVENT` rather than failing the launched run (`plan/PROTOCOL.md:18`; `tools/run_codex_agent.sh:70-75`). Also, the EXIT trap preserves the original exit status even when `provenance` fails, so a successful coder can still return 0 without the mandatory ledger handoff if the Python append fails (`tools/run_codex_agent.sh:73-86`); a direct shell replay of a failing EXIT trap after `exit 0` returned 0. The stale header still advertises `/tmp` despite the persistent log path (`tools/run_codex_agent.sh:7-10`, `tools/run_codex_agent.sh:88-89`). These are fail-closedness/documentation edges, not a normal-path scope or provenance break, so the remaining severity is Low.

## Recommendations

1. Make provenance fail closed for launched runs: require a parsed `thread.started` session id, propagate a ledger-append failure to the wrapper's final status without losing the coder/scope status, and update the header to name `results/logs/` (`plan/PROTOCOL.md:18`; `tools/run_codex_agent.sh:7-10`, `tools/run_codex_agent.sh:66-89`).
2. Replace the historical ledger's bare `tiebreaks.md` with `plan/tiebreaks/plan.md`, using a dated correction annotation (`plan/LEDGER.md:25`).
3. Add a dated correction to the v1.17 history entry replacing “extracted verbatim” with the already-adopted “substance preserved; self-references re-scoped” wording (`plan/AMENDMENTS.md:11`; `PLAN.md:105`; `plan/PROTOCOL.md:3`).

## Evidence consulted

- `PLAN.md`, read in full again (SHA-256 `2a9774a861b30c6424376dc4e7427c0515b545a8bdc72d316c59fd3826d972ad`); `plan/PROTOCOL.md` (SHA-256 `87484fc6f8c85820779ecda1df2e51fa662a3a5bc4907c15763017b4efc79761`), `plan/LEDGER.md`, `plan/AMENDMENTS.md`, `README.md`, `AGENTS.md`, `CLAUDE.md`, the complete prior amendment review, and process Round 18 with Findings 11, 42, and 44.
- Complete revised v1.21 working-tree diff against `46e17e2`, plus status, cached-diff, untracked-file, and path inventories. Seven noncanonical tracked paths are modified: the six amendment/governance/tool paths plus `plan/reviews/plan/process.md`; there is no staged or untracked content. Appendix C, every scientific/phase threshold, and README's component map are untouched.
- Mandatory direct runs of `bash tools/amend.sh --tree-id`: both printed `02f1a93225b7374010f4a4ce2eccc2989ba6fc78` and exited 0; the cached diff remained empty and status was unchanged.
- Independent reconstruction of the landed v1.20 identity from parent `95ce6cd8da8a0ad71be606ee1937d88e0672ae4b` plus the full-index binary `46e17e2^..46e17e2` diff excluding only the canonical amendment review: `a9397066cb8407f3a4b97a38c30ed4a31d2616db`, exactly Round 7's accepted id.
- Source-level audit of `tools/amend.sh`, `tools/run_codex_agent.sh`, the governing handoff/STATE rules, and the revised v1.21 index/history/ledger entries; `bash -n` passes for both scripts. Direct `bash tools/amend.sh v1x21 summary` remains verified from Round 8 as rejecting the malformed version with exit 2 before lock acquisition.
- Read-only control-flow audit of the corrected coder wrapper: allowlist discovery precedes `codex exec`; the EXIT trap covers the run and scope scan; record fields use `sys.argv` under a quoted heredoc; the session parser retains a missing-event marker; and the wrapper's own log/ledger paths remain exempt from coder scope (`tools/run_codex_agent.sh:59-137`).
- Direct in-memory EXIT-trap replays: a failing finalizer after `exit 0` returned 0, while the same finalizer after `exit 7` returned 7, confirming that provenance failure does not alter the wrapper's coder/scope status (`tools/run_codex_agent.sh:66-86`). Compact `thread.started` JSON parsed to its UUID; a whitespace-formatted equivalent did not match the shell parser.
- Repository-wide scans for the two remaining relocation/provenance residues, distinguishing historical reviewer prose from governed audit records (`plan/LEDGER.md:25`; `plan/AMENDMENTS.md:11`).
- Direct read-only replay of `bash tools/check_acceptance.sh plan` before this canonical write: amendment and process were 88, while science/spec passed at 92.
- Ledger launch audit: the top state is pre-Phase-0, declares v1.21 as the current amendment transaction, and names process Round 19 as the post-commit next action (`plan/LEDGER.md:13`); no phase threshold has frozen and v1.21 changes no threshold.
- Post-write replay of `bash tools/check_acceptance.sh plan`: amendment passes at 90 with zero open High/Critical findings; process remains 88, while science/spec remain accepted at 92.
