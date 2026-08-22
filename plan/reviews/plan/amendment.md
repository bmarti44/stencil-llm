# Amendment Review — plan

**Score:** 74 / 100
**Verdict:** FAIL (<75)
**Reviewer model:** codex/gpt-5.6-sol
**Date:** 2026-08-22

## Round log

### Round 26 — 2026-08-22 (codex/gpt-5.6-sol)
- Score: 74 / 100 (delta vs prior round: +0)
- Reviewed tree: d749c710f98f09f5d9f519fdadf556487c89d58b
- Addressed since prior round:
  - Finding 9's repository-file bypass is closed in isolation: the allowlist and helper are copied before launch, the post scan is unconditional, and it reads those copies rather than the repository paths. Deleting or rewriting the repository allowlist/helper therefore no longer directly disables the scan, and both edits remain visible to the keyed inventory (`tools/run_codex_agent.sh:59-64`, `tools/run_codex_agent.sh:98-110`, `tools/run_codex_agent.sh:129-151`).
  - The wrapper now cleans the combined private snapshot directory on EXIT while retaining the prior session-id, helper-error, terminal-NUL, rename-source, and temporary-output fixes; Finding 12's narrow-commit backstop remains byte-identical (`tools/run_codex_agent.sh:66-89`, `tools/run_codex_agent.sh:106-110`, `tools/run_codex_agent.sh:135-151`; `tools/_coder_scope.py:15-78`; `tools/commit_narrow.sh:11-30`).
- New or remaining:
  - High Finding 9 remains open: `mktemp -d` gives filesystem privacy from other users, not from the child running under the same uid. The unsandboxed coder can enumerate `/tmp`, identify the directory by its `allow`, `_coder_scope.py`, and `pre.json` names, then rewrite the exact policy, verifier, and baseline used after it returns; no parent-held digest or privilege boundary detects that tampering (`tools/run_codex_agent.sh:8-10`, `tools/run_codex_agent.sh:101-123`, `tools/run_codex_agent.sh:133-149`; `plan/PROTOCOL.md:18`, `plan/PROTOCOL.md:21`).
  - Findings 4 and 6 remain Low historical residues (`plan/LEDGER.md:34`; `plan/AMENDMENTS.md:12`). Seven outside-canonical tracked paths and two untracked helpers are included in the reviewed tree id and were not modified by this reviewer.

### Round 25 — 2026-08-22 (codex/gpt-5.6-sol)
- Score: 74 / 100 (delta vs prior round: +0)
- Reviewed tree: 6fb2294579289c328dac67afdaa17844bce698be
- Addressed since prior round:
  - Finding 9's type-2 defect is fixed: the parser now consumes the following NUL record as the source and records both names. A direct replay with spaced destination `src/allowed/new name.md` and source `?PLAN start.md` produced both exact keys, and the wrapper predicate blocked the source while allowing the destination (`tools/_coder_scope.py:19-44`; `tools/run_codex_agent.sh:129-143`).
  - Finding 14 is resolved: the EXIT trap now removes both temporary paths, including interruptions between `POST_OUT` creation and its normal removal. The pre/post helper checks, terminal NULs, and Finding 12's narrow-commit backstop also remain intact (`tools/run_codex_agent.sh:89`, `tools/run_codex_agent.sh:101-102`, `tools/run_codex_agent.sh:127-143`; `tools/commit_narrow.sh:11-30`).
- New or remaining:
  - High Finding 9 remains open through a broader self-authentication path: the wrapper gives the coder unsandboxed repository access, then conditionally skips the entire scan if the same on-disk allowlist has been deleted and executes the same coder-writable helper for its post-run verdict. Deleting the allowlist or replacing `_coder_scope.py` with a successful empty-output program lets arbitrary out-of-scope changes pass (`tools/run_codex_agent.sh:59-64`, `tools/run_codex_agent.sh:106-115`, `tools/run_codex_agent.sh:124-143`; `plan/PROTOCOL.md:18`, `plan/PROTOCOL.md:21`).
  - Findings 4 and 6 remain Low historical residues (`plan/LEDGER.md:34`; `plan/AMENDMENTS.md:12`). Seven outside-canonical tracked paths, including the new `.gitignore` bytecode exclusion, and two untracked helpers are included in the reviewed tree id and were not modified by this reviewer.

### Round 24 — 2026-08-22 (codex/gpt-5.6-sol)
- Score: 74 / 100 (delta vs prior round: +0)
- Reviewed tree: 3cb0cf56dbcccb6a93f4482faf65785eca618576
- Addressed since prior round:
  - Finding 9's broad Round-23 bypasses are fixed: every changed path is now terminal-NUL-delimited, the pre snapshot is checked, and the post comparison is materialized and checked before `read -d ''`. A direct helper replay emitted nine complete records and ended in NUL; helper failures now exit 10 instead of silently producing an empty scan (`tools/_coder_scope.py:59-71`; `tools/run_codex_agent.sh:101-102`, `tools/run_codex_agent.sh:127-143`).
  - Finding 12's narrow-commit backstop remains byte-identical, the sequencing confession/pending status remain intact, and the amendment is still pre-Phase-0 with no scientific threshold or Appendix C change (`tools/commit_narrow.sh:11-30`; `plan/AMENDMENTS.md:7`; `PLAN.md:11`, `PLAN.md:92`, `PLAN.md:470-486`; `plan/LEDGER.md:13`).
- New or remaining:
  - High Finding 9 remains open: type-2 parsing records only the rename/copy destination and discards the following source path. A direct porcelain-v2 replay mapped only allowed `src/allowed/new.md`, omitted source `PLAN.md`, and the wrapper's exact allowlist loop therefore returned no violation; a coder can delete/move an out-of-scope source behind an allowed destination (`tools/_coder_scope.py:19-35`; `tools/run_codex_agent.sh:129-143`; `plan/PROTOCOL.md:18`, `plan/PROTOCOL.md:21`).
  - New Low Finding 14: the new `POST_OUT` temporary file is removed only on normal/error paths inside the comparison block, while the EXIT trap cleans only `PRE_MANIFEST`; interruption between creation and line 142 leaves it behind (`tools/run_codex_agent.sh:89`, `tools/run_codex_agent.sh:127-142`). Findings 4 and 6 remain Low historical residues (`plan/LEDGER.md:34`; `plan/AMENDMENTS.md:12`). Six outside-canonical tracked paths and two untracked helpers are included in the reviewed tree id and were not modified by this reviewer.

### Round 23 — 2026-08-22 (codex/gpt-5.6-sol)
- Score: 74 / 100 (delta vs prior round: -14)
- Reviewed tree: 428a5ff8f72bf28fd5371278d67c3e786a34f6cd
- Addressed since prior round:
  - Finding 9's replacement inventory fixes the two Round-22 residual representations in isolation: it parses porcelain-v2 from NUL records into full path keys, compares the union of pre/post path sets, and records a missing baseline path as `GONE`, so deleted untracked paths and whitespace-bearing ordinary paths no longer disappear inside the helper (`tools/_coder_scope.py:15-39`, `tools/_coder_scope.py:44-56`; `tools/run_codex_agent.sh:101-102`).
  - Finding 13 remains resolved and Finding 12's clean-index/Git-resolved narrow-commit backstop remains byte-identical. The amendment is still pre-Phase-0 and changes no scientific threshold or Appendix C row (`tools/commit_narrow.sh:11-30`; `PLAN.md:11`, `PLAN.md:92`, `PLAN.md:470-486`; `plan/LEDGER.md:13`).
- New or remaining:
  - Finding 9 is escalated to High because the new helper writes no terminal NUL: the wrapper's `read -d ''` loop therefore inspects zero paths for the common one-change case and always drops the final path when several changed paths exist (`tools/_coder_scope.py:51-57`; `tools/run_codex_agent.sh:127-140`). The parser also ignores porcelain-v2 type `2` rename/copy records, and neither helper invocation is checked in this non-`set -e` wrapper (`tools/_coder_scope.py:19-26`; `tools/run_codex_agent.sh:101-102`, `tools/run_codex_agent.sh:127-140`).
  - Findings 4 and 6 remain Low historical residues (`plan/LEDGER.md:34`; `plan/AMENDMENTS.md:12`). Six outside-canonical tracked paths and two untracked helpers are included in the reviewed tree id and were not modified by this reviewer.

### Round 22 — 2026-08-22 (codex/gpt-5.6-sol)
- Score: 88 / 100 (delta vs prior round: +1)
- Reviewed tree: aaa571e2b490a4d5245f642839fc8bb03961a888
- Addressed since prior round:
  - Finding 9 is narrowed again: symlinks are now tested before regular files, content records require exact full-line matches, and the EXIT trap removes `PRE_MANIFEST`; the session-id and ordinary mode-change fixes from Round 21 remain intact (`tools/run_codex_agent.sh:66-89`, `tools/run_codex_agent.sh:101-110`, `tools/run_codex_agent.sh:142-151`).
  - Finding 13 is resolved: the trailing space at the porcelain-v2 snapshot was removed and direct `git diff --check` now passes. Finding 12's clean-index/Git-resolved narrow-commit fix also remains intact (`tools/run_codex_agent.sh:103`; `tools/commit_narrow.sh:11-30`).
- New or remaining:
  - Finding 9 remains Medium: the post-run loop still enumerates only paths that currently exist in `git diff --name-only` or `git ls-files --others`, so deletion of a pre-existing untracked path is invisible; its porcelain matcher also uses whitespace-delimited `$NF`, making both status lookups empty for a path containing spaces and allowing a same-content mode change to be classified as baseline (`tools/run_codex_agent.sh:103-110`, `tools/run_codex_agent.sh:145-162`).
  - Findings 4 and 6 remain Low historical residues (`plan/LEDGER.md:34`; `plan/AMENDMENTS.md:12`). Six outside-canonical tracked paths and untracked `tools/commit_narrow.sh` are included in the reviewed tree id and were not modified by this reviewer.

### Round 21 — 2026-08-22 (codex/gpt-5.6-sol)
- Score: 87 / 100 (delta vs prior round: -1)
- Reviewed tree: b8ddba7e2878a3150ce71fcb2775a25295d4e1e0
- Addressed since prior round:
  - Finding 9 is narrowed: a missing `thread.started` id now changes an otherwise successful wrapper exit to 9, and the EXIT trap propagates that changed result after recording provenance (`tools/run_codex_agent.sh:66-89`). The baseline also records porcelain-v2 status, so ordinary executable-mode changes no longer pass merely because file bytes match (`tools/run_codex_agent.sh:101-110`, `tools/run_codex_agent.sh:142-151`).
  - Finding 12's clean-index/Git-resolved narrow-commit fix remains intact, and the amendment remains pre-Phase-0 with no threshold or Appendix C change (`tools/commit_narrow.sh:11-30`; `PLAN.md:11`, `PLAN.md:92`, `PLAN.md:470-486`; `plan/LEDGER.md:13`).
- New or remaining:
  - Finding 9 remains Medium: live symlinks still take the dereferencing `-f` branch before `-L`, both manifest/status lookups remain unanchored fixed-string searches, deleted pre-existing untracked paths are absent from the post-run iteration, and `PRE_MANIFEST` has no cleanup path (`tools/run_codex_agent.sh:101-110`, `tools/run_codex_agent.sh:142-162`). These gaps still permit out-of-allowlist coder changes to be classified as baseline.
  - New Low Finding 13: the coder-wrapper patch introduces trailing whitespace and makes `git diff --check` fail (`tools/run_codex_agent.sh:103`). Findings 4 and 6 remain Low historical residues (`plan/LEDGER.md:34`; `plan/AMENDMENTS.md:12`). Six outside-canonical tracked paths and untracked `tools/commit_narrow.sh` are included in the reviewed tree id and were not modified by this reviewer.

### Round 20 — 2026-08-22 (codex/gpt-5.6-sol)
- Score: 88 / 100 (delta vs prior round: +16)
- Reviewed tree: 09558bc7bc2571e6b3462f34421b9b7c2fe4d668
- Addressed since prior round:
  - Finding 12 is resolved: `commit_narrow.sh` now refuses to proceed unless the pre-existing index is empty, then retains the Git-resolved governed-path scan and literal-only staging. The Round-19 ride-along path is therefore closed before any staging, while the lock and every earlier selector defense remain intact (`tools/commit_narrow.sh:11-30`; `plan/PROTOCOL.md:21`, `plan/PROTOCOL.md:30`).
  - The sequencing violation remains candidly preserved, v1.22 remains acceptance-pending, and the tree remains pre-Phase-0 with no threshold or Appendix C change (`plan/AMENDMENTS.md:7`; `PLAN.md:11`, `PLAN.md:92`, `PLAN.md:470-486`; `plan/LEDGER.md:13`).
- New or remaining:
  - No High/Critical finding is open, but the amendment does not clear 90. Finding 9 remains Medium because the coder baseline is still neither Git-semantic nor set-complete and session provenance remains fail-open (`tools/run_codex_agent.sh:66-72`, `tools/run_codex_agent.sh:95-101`, `tools/run_codex_agent.sh:125-146`; `plan/AMENDMENTS.md:7`).
  - Findings 4 and 6 remain Low historical residues (`plan/LEDGER.md:34`; `plan/AMENDMENTS.md:12`). Five outside-canonical tracked paths and untracked `tools/commit_narrow.sh` are included in the reviewed tree id and were not modified by this reviewer.

### Round 19 — 2026-08-22 (codex/gpt-5.6-sol)
- Score: 72 / 100 (delta vs prior round: +4)
- Reviewed tree: 1a4ca3c56a0ec487063414f93eac2599252e9c49
- Addressed since prior round:
  - Finding 12 is materially narrowed: the helper now asks Git to resolve each supplied selector before judging the resulting file set, then stages only resolved literal paths. Direct replays show every Round-18 root/directory/magic bypass now resolves a governed file and is blocked, while the intended committed tie-break prompt resolves cleanly and is allowed (`tools/commit_narrow.sh:2-22`; `plan/PROTOCOL.md:30`).
  - The `.review.lock`, candid sequencing confession, four-fixed/#29-deferred history, and pre-Phase-0 threshold posture remain intact; PLAN.md and Appendix C are unchanged (`tools/commit_narrow.sh:11-12`; `plan/AMENDMENTS.md:7`; `PLAN.md:11`, `PLAN.md:92`, `PLAN.md:470-486`; `plan/LEDGER.md:13`).
- New or remaining:
  - Critical Finding 12 remains open through a simpler index-boundary bypass: after validating and staging the named safe files, the helper runs an unrestricted `git commit` with no path arguments and never checks pre-existing staged content. Any already-staged PLAN/PROTOCOL/tool change is therefore committed alongside the safe narrow path without passing the helper's governed-file scan (`tools/commit_narrow.sh:13-25`; `plan/AMENDMENTS.md:7`; `plan/PROTOCOL.md:30`).
  - Finding 9 remains Medium and unchanged; Findings 4 and 6 remain Low (`tools/run_codex_agent.sh:66-72`, `tools/run_codex_agent.sh:95-101`, `tools/run_codex_agent.sh:125-146`; `plan/LEDGER.md:34`; `plan/AMENDMENTS.md:12`). Five outside-canonical tracked paths and untracked `tools/commit_narrow.sh` are included in the reviewed tree id and were not modified by this reviewer.

### Round 18 — 2026-08-22 (codex/gpt-5.6-sol)
- Score: 68 / 100 (delta vs prior round: +16)
- Reviewed tree: 91faf1a4dd6b4660769400cde5c03100ebfcbc12
- Addressed since prior round:
  - Finding 11 is resolved: the full v1.22 history now consistently says four process findings are fixed and #29 is deferred-open, matching PLAN, PROTOCOL, STATE, and batch 5's binding UPHOLD; it no longer says #29 was closed or completed (`PLAN.md:11`; `plan/AMENDMENTS.md:7`; `plan/PROTOCOL.md:19`; `plan/LEDGER.md:13`; `plan/tiebreaks/plan.md:164-176`).
  - Finding 12 is narrowed: `commit_narrow.sh` now normalizes the three direct aliases reproduced in Round 17 and takes `.review.lock`; direct replays classify `./PLAN.md`, `plan/../PLAN.md`, and `:(top)PLAN.md` as canonical `PLAN.md` and block them (`tools/commit_narrow.sh:10-25`; `plan/PROTOCOL.md:21`). The amendment remains pre-Phase-0 and changes no scientific threshold or Appendix C row (`PLAN.md:11`, `PLAN.md:92`, `PLAN.md:470-486`; `plan/LEDGER.md:13`).
- New or remaining:
  - Critical Finding 12 remains open: normalization still permits broad directory/root arguments and unstripped Git pathspec magic. The helper classifies `.`, `plan`, `tools/..`, `:(literal)PLAN.md`, `:/PLAN.md`, `:(top,literal)PLAN.md`, and `:(glob)plan/*.md` as non-governed, then passes them to `git add` and `git commit`; read-only Git resolution shows each selects governed files (`tools/commit_narrow.sh:13-30`; `plan/AMENDMENTS.md:7`; `plan/PROTOCOL.md:30`).
  - Finding 9 remains Medium and unchanged; Findings 4 and 6 remain Low (`tools/run_codex_agent.sh:66-72`, `tools/run_codex_agent.sh:95-101`, `tools/run_codex_agent.sh:125-146`; `plan/LEDGER.md:34`; `plan/AMENDMENTS.md:12`). Five outside-canonical tracked paths and untracked `tools/commit_narrow.sh` are included in the reviewed tree id and were not modified by this reviewer.

### Round 17 — 2026-08-22 (codex/gpt-5.6-sol)
- Score: 52 / 100 (delta vs prior round: +4)
- Reviewed tree: 629a8ccc1085779729af7eb9e318d3a2d2727576
- Addressed since prior round:
  - Finding 12 is candidly acknowledged in the v1.22 history: it now names all three unsanctioned commits, retracts the pre-commit/tree-bound claim, and says acceptance is pending. The draft also registers a narrow-commit helper intended to prevent another `git add -A` sweep (`plan/AMENDMENTS.md:7`; `plan/PROTOCOL.md:30`; `tools/commit_narrow.sh:1-20`).
  - Finding 11 is narrowed again: the history now opens with the correct four-fixed/one-deferred disposition, and the tie-break runner's false dead `expected_out` claim is removed (`plan/AMENDMENTS.md:7`; `tools/run_tiebreak.py:33-40`). The tree remains pre-Phase-0 and changes no scientific threshold or Appendix C row (`PLAN.md:11`, `PLAN.md:92`, `PLAN.md:470-486`; `plan/LEDGER.md:13`).
- New or remaining:
  - Critical Finding 12 remains open: `commit_narrow.sh` compares unnormalized argv strings, so it blocks `PLAN.md` but allows equivalent Git pathspecs `./PLAN.md`, `plan/../PLAN.md`, and `:(top)PLAN.md`; it also takes no repository lock. The new history therefore overclaims that governed paths are now uncommittable outside `amend.sh` (`tools/commit_narrow.sh:7-20`; `plan/AMENDMENTS.md:7`; `plan/PROTOCOL.md:21`, `plan/PROTOCOL.md:30`).
  - High Finding 11 remains open because its single authoritative history line still says #29 was “closed” and later “completed,” directly contradicting the same line's four-plus-deferred opening and the governing protocol (`plan/AMENDMENTS.md:7`; `plan/PROTOCOL.md:19`; `PLAN.md:11`). Finding 9 remains Medium; Findings 4 and 6 remain Low. Five outside-canonical tracked paths and untracked `tools/commit_narrow.sh` are included in the reviewed tree id and were not modified by this reviewer.

### Round 16 — 2026-08-22 (codex/gpt-5.6-sol)
- Score: 48 / 100 (delta vs prior round: -24)
- Reviewed tree: 2585ed4b6a3945f8884cf33d15809b338f791c18
- Addressed since prior round:
  - Finding 11 is materially narrowed: the tie-break runner now requires a review file, rejects heading-only/short quote records, records a stable run id and replay command, and batch 5's accepted ruling caused the binary-description contract to be registered while PLAN/STATE now describe #29 as deferred-open rather than complete (`tools/run_tiebreak.py:18-60`, `tools/run_tiebreak.py:80-89`; `plan/PROTOCOL.md:19`; `PLAN.md:11`; `plan/LEDGER.md:13`).
  - The batch-5 prompt quotes Finding 11's full text, and the accepted raw verdict is preserved with ASK A UPHOLD and ASK B REFUTE (`plan/tiebreaks/plan-prompt-5.md:3-8`; `plan/tiebreaks/plan.md:145-176`). The amendment remains pre-Phase-0 and changes no Appendix C threshold (`PLAN.md:92`, `PLAN.md:470-486`; `plan/LEDGER.md:13`).
- New or remaining:
  - New Critical Finding 12 blocks acceptance: commit `22b22a4`, presented as the required pre-execution prompt commit, also committed the rejected v1.22 governed tree and its tooling while Round 15 stood at 72 with open High Finding 11; commits `1db32c3` and `67924ce` then changed the runner and governed PLAN/PROTOCOL again without an accepted amendment or `tools/amend.sh` (`plan/PROTOCOL.md:30`; `tools/amend.sh:62-89`; `plan/reviews/plan/amendment.md:20-28`).
  - Finding 11 remains High because the full amendment history still says v1.22 was pre-commit reviewed/tree-bound, all five findings were fixed, and #29 was completed, contradicting PLAN/STATE and the batch-5 ruling (`plan/AMENDMENTS.md:7`; `PLAN.md:11`; `plan/LEDGER.md:13`). Finding 9 remains Medium; Findings 4 and 6 remain Low. Outside the canonical review, `plan/LEDGER.md` and `plan/tiebreaks/plan.md` are modified; both are included in the reviewed tree id and were not modified by this reviewer.

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

4. **Low — The path migration is incomplete in active prompts and audit references.** (updated 2026-08-22: Round 16 citation shift; Round 4 severity reduction remains unchanged.) Commit `3f15625` corrects Human adjudication 2 to `plan/tiebreaks/` (`plan/tiebreaks/plan.md:89-94`), and the active prompts, tools, and other governed audit references use the current layout. The sole residue is the historical batch-3 ledger entry's bare `tiebreaks.md` instead of `plan/tiebreaks/plan.md` (`plan/LEDGER.md:34`), which also makes the v1.17 statement that residual stragglers were fixed slightly overstated (`plan/AMENDMENTS.md:12`). This is an audit-navigation nit, not an active-path defect.

5. **Low (resolved 2026-08-22: all index entries are complete one-line summaries and the doubled punctuation was removed) — The compact amendment index is truncated rather than summarized.** (updated 2026-08-22: Round 3 re-verification.) PLAN.md labels the index as orientation-only and now gives a complete summary for every v1.0-v1.17 entry (`PLAN.md:9-28`).

6. **Low — The amendment inaccurately calls the extracted protocol verbatim and content-unchanged.** (updated 2026-08-22: Round 11 citation shift.) Commit `3f15625` makes PLAN.md and the protocol preamble accurate by saying the substance was preserved while inherited self-references were re-scoped (`PLAN.md:106`; `plan/PROTOCOL.md:3`). The full v1.17 history entry alone still says PROTOCOL.md was “extracted verbatim” (`plan/AMENDMENTS.md:12`), despite the reviewed direct-edit clarification now present in the extracted rule (`plan/PROTOCOL.md:18`).

7. **High (resolved 2026-08-22: `--tree-id` now avoids alternate-index/object writes, runs successfully in the reviewer sandbox, and returns a stable nonempty identifier) — The mandatory tree-id binding is neither read-only nor runnable.** (updated 2026-08-22: Round 5 re-verification.) The replacement invokes only `rev-parse`, `diff`, and `ls-files`, then reads working-tree bytes in Python; it creates no alternate index and requests no Git object write (`tools/amend.sh:15-43`). Two exact invocations returned `fa564e8ce227751629d29c9f9a3e0cedd4113ced` with exit 0, while the cached diff remained empty and repository status was unchanged. The original runtime blocker is therefore resolved; Finding 8 separately addresses whether the returned identifier fully binds the tree and sequence claimed by the protocol.

8. **High (resolved 2026-08-22: tracked changes now use a checked full-index binary diff and the STATE parser selects and validates the first amendment command) — The rebuilt binding can certify a different Git tree and the wrong next action.** (updated 2026-08-22: Round 26 artifact-binding re-verification.) The identity implementation remains fail-closed for a caller that actually uses it: tracked changes use a checked full-index binary diff, while untracked names are NUL-delimited and framed with `lstat` type, symlink payload, regular-file bytes, and Git-significant executable state (`tools/amend.sh:23-54`; `plan/PROTOCOL.md:30`). The declared-intent check requires a nonempty first post-commit command that does not name `amend.sh` (`tools/amend.sh:77-84`), and the top STATE names process Round 20 next (`plan/LEDGER.md:13`). Two mandatory runs returned `d749c710f98f09f5d9f519fdadf556487c89d58b` with exit 0 and no index/status mutation. The seven outside-canonical tracked changes and two untracked helpers are included in that id. Finding 12 remains historically distinct: the orchestrator bypassed this still-correct mechanism, but the corrective record and recurrence backstop remain independently verified.

9. **High — The coder-provenance fix violates its own ledger and handoff contracts.** (updated 2026-08-22: Round 26 re-verification after the private-snapshot patch.) The keyed representation and every previously demonstrated parser/consumer case remain fixed (`tools/_coder_scope.py:15-78`). The wrapper also now copies the allowlist and helper before launch, performs the post scan unconditionally, and uses the copies, so deleting or rewriting their repository paths no longer suffices (`tools/run_codex_agent.sh:59-64`, `tools/run_codex_agent.sh:98-110`, `tools/run_codex_agent.sh:129-151`). The claimed trust boundary is still false. `PRIVATE_DIR="$(mktemp -d)"` is an ordinary directory owned by the wrapper's uid; the child is launched directly—without a different uid or effective sandbox—and is explicitly given `--dangerously-bypass-approvals-and-sandbox` (`tools/run_codex_agent.sh:8-10`, `tools/run_codex_agent.sh:106-123`). That same-uid child can enumerate `/tmp`, recognize the active directory by its fixed `allow`, `_coder_scope.py`, and `pre.json` members, and replace the copied allowlist, helper, or baseline. The wrapper holds no expected digest or in-memory policy and later trusts exactly those mutable files (`tools/run_codex_agent.sh:106-110`, `tools/run_codex_agent.sh:133-149`). Replacing the private helper with a successful empty-output program, or replacing the private manifest and policy together, again permits arbitrary out-of-scope changes with no violation. Directory mode 0700 does not separate processes owned by the same uid. This remains an unconditional bypass of PROTOCOL's mandatory hard scope failure (`plan/PROTOCOL.md:18`, `plan/PROTOCOL.md:21`), so the v1.22 history still overclaims the coder-scope repair (`plan/AMENDMENTS.md:7`).

10. **Critical (resolved 2026-08-22: batch 4 was explicitly vacated, its false closures withdrawn, the verbatim-record rule adopted, and the cited G3 contradictions repaired directly) — Batch-4 tie-break rescues a failing process score by adjudicating strawmen.** (updated 2026-08-22: Round 13 source verification.) The raw prompt and verdict remain preserved for audit, but a dated marker now says the batch is VACATED and “closes nothing” (`plan/tiebreaks/plan.md:140-142`); the v1.22 history expressly withdraws both the arbiter's closure and the earlier amendment claim (`plan/AMENDMENTS.md:7`). The protocol now requires the finding text and both arguments verbatim (`plan/PROTOCOL.md:24`), and the exact contradictions that batch 4 falsely called unenumerated are repaired in the governing science text (`PLAN.md:379`, `PLAN.md:497-498`). Those changes independently verify that the dishonest adjudication is no longer being used as authority. Finding 11 separately reviews whether the replacement claim that all five findings were fixed on their merits is true.

11. **High (resolved 2026-08-22: the full v1.22 history now consistently records four fixes and #29 deferred-open, matching the governing contract and batch-5 ruling) — The replacement “five fixes” claim omits one finding and only partially repairs three others.** (updated 2026-08-22: Round 18 source verification; the immutable title records the Round-13 state.) The runner requires a review file, demands at least 200 characters of exact non-heading review quotation, and records a stable run id plus replay command (`tools/run_tiebreak.py:18-57`, `tools/run_tiebreak.py:77-86`); the committed batch-5 prompt quotes this finding in full (`plan/tiebreaks/plan-prompt-5.md:3-8`). Batch 5 UPHELD the binary-description contract and REFUTED the remaining ASK-B validation demands (`plan/tiebreaks/plan.md:164-176`); PROTOCOL registers the upheld contract and leaves process#29 deferred-open until the first PRESENT binary row exists (`plan/PROTOCOL.md:19`). PLAN, the top STATE, and the corrected full history now all give that same four-fixed/one-deferred disposition, with the later “#29 closed/completed” language removed (`PLAN.md:11`; `plan/LEDGER.md:13`; `plan/AMENDMENTS.md:7`). Acceptance also requires `topics.txt` and exact registered codex/kimi companions, so the wrappers' permissive pre-launch behavior when no manifest exists cannot produce an accepted phase (`tools/check_acceptance.sh:12-43`). The central false-completeness claim is gone; the current process review may adjudicate #29 when its deferred trigger occurs.

12. **Critical (resolved 2026-08-22: the violation is confessed and the narrow helper now requires an empty index before Git-resolved validation and literal-only staging) — The batch-5 prompt commit bypassed the amendment gate and landed the rejected v1.22 tree.** (updated 2026-08-22: Round 26 citation shift; Round 20 closure remains unchanged.) Immutable history still proves `22b22a4` committed PLAN.md, PROTOCOL.md, AMENDMENTS.md, LEDGER.md, both plan reviews, the topic manifest, and five process tools while Round 15 stood at 72 with open High Finding 11 (`plan/reviews/plan/amendment.md:120-128`; `tools/amend.sh:62-70`); commits `1db32c3` and `67924ce` then landed further runner and governed PLAN/PROTOCOL changes outside the mandatory path. The amendment history now accurately names and confesses all three commits, retracts the false pre-commit/tree-bound claim, and leaves v1.22 acceptance pending (`plan/AMENDMENTS.md:7`). The recurrence backstop takes `.review.lock`, refuses any pre-existing cached path before staging, asks Git to resolve every caller selector, rejects the complete resolved set if it contains a governed path, and stages only the resolved literal paths (`tools/commit_narrow.sh:11-27`; `plan/PROTOCOL.md:21`, `plan/PROTOCOL.md:30`). The clean-index precondition closes Round 19's final ride-along bypass: the unrestricted commit at lines 28-30 can contain only paths staged after that check through the validated literal loop. Direct read-only replays confirm every selector reproduced in Rounds 17-18 is still blocked, the intended tie-break prompt remains allowed, and the real index is empty. The past violation cannot be undone, but it is no longer concealed or available through the sanctioned recurrence path; this Critical legitimacy finding is resolved for the pending corrective amendment.

13. **Low (resolved 2026-08-22: the trailing space was removed and `git diff --check` passes) — The coder-wrapper patch fails whitespace validation.** Direct source inspection confirms the porcelain-v2 snapshot line is clean, and the repository-wide diff check now exits 0 (`tools/run_codex_agent.sh:103`).

14. **Low (resolved 2026-08-22: the EXIT trap now removes `POST_OUT` as well as `PRE_MANIFEST`) — The post-comparison temporary file is not covered by cleanup.** Direct source inspection confirms the trap removes `POST_OUT` and recursively removes the private directory containing `PRE_MANIFEST` on every exit, while the normal and explicit-error output removals remain (`tools/run_codex_agent.sh:89`, `tools/run_codex_agent.sh:106-110`, `tools/run_codex_agent.sh:135-150`).

## Recommendations

1. Keep the allowlist in a parent-shell array and hold expected hashes for the copied helper and baseline in parent variables; after `codex exec`, fail before comparison unless both files still match, and check every `cp`/snapshot operation explicitly. Alternatively run the monitor under a genuinely separate privilege boundary. Add a wrapper replay whose child enumerates `/tmp`, rewrites the active `allow`, `_coder_scope.py`, and `pre.json`, and also changes an out-of-scope repository path (`tools/run_codex_agent.sh:98-123`, `tools/run_codex_agent.sh:133-149`).
2. Keep v1.22 explicitly pending until Finding 9's hard containment boundary is repaired and a later amendment round reaches 90 with zero open High/Critical findings; then commit exactly that accepted tree only through `tools/amend.sh` before running process Round 20 (`plan/AMENDMENTS.md:7`; `plan/LEDGER.md:13`; `tools/amend.sh:62-89`).
3. Replace the historical ledger's bare `tiebreaks.md` with `plan/tiebreaks/plan.md`, using a dated correction annotation (`plan/LEDGER.md:34`), and correct v1.17's “extracted verbatim” history claim (`plan/AMENDMENTS.md:12`; `PLAN.md:106`; `plan/PROTOCOL.md:3`).

## Evidence consulted

- `PLAN.md`, read in full again (532 lines; SHA-256 `75cd746003f4a51d261357d5fb268d6fca4689cff7683528c3579c6828248be1`); `plan/PROTOCOL.md` (SHA-256 `586a14a3d77692b29f7e9ec41859e4e75b95a5dd44eb90596b038d2c9527a076`), `plan/LEDGER.md` (SHA-256 `f307b71ca44fccc866bcfa00f0fedfad23d8197e8f6ff01aa479d6df671862c5`), `plan/AMENDMENTS.md` (SHA-256 `696bb62877e0103a6b717184ffdecf16deb3c3010877b9cd03e5625942e1d33f`), `README.md` (read in full; SHA-256 `3f1c987a755b2ee44a53d766ec2c19b68decd6c69e925d499720f698c42f7dfd`), `AGENTS.md`, `CLAUDE.md`, the complete prior amendment review, process Round 19, and batch 5's prompt/rejected/accepted records.
- Complete immutable-history recheck of `22b22a4`, `1db32c3`, and `67924ce`, plus the full current diff, status, cached-diff, and untracked inventories. Outside the canonical review, seven tracked files are modified (`.gitignore`, `plan/AMENDMENTS.md`, `plan/LEDGER.md`, `plan/PROTOCOL.md`, `plan/tiebreaks/plan.md`, `tools/run_codex_agent.sh`, `tools/run_tiebreak.py`) and two helpers are untracked (`tools/_coder_scope.py`, `tools/commit_narrow.sh`); there is no staged content. The new `.gitignore` change is limited to `tools/__pycache__/`.
- Mandatory direct runs of `bash tools/amend.sh --tree-id`: both printed `d749c710f98f09f5d9f519fdadf556487c89d58b` and exited 0; the cached diff remained empty and status was unchanged.
- Source-level closure audit of Finding 11: the corrected full history still says four fixed and #29 deferred at both mentions, matching PLAN, STATE, PROTOCOL's first-binary trigger, and batch 5's accepted UPHOLD (`PLAN.md:11`; `plan/AMENDMENTS.md:7`; `plan/LEDGER.md:13`; `plan/PROTOCOL.md:19`; `plan/tiebreaks/plan.md:164-176`). Acceptance independently fails without `topics.txt` and validates exact registered codex/kimi companions (`tools/check_acceptance.sh:12-43`).
- Source-level closure audit of Finding 12: `commit_narrow.sh` still requires a completely empty cached-name set before Git-resolved validation and literal staging under `flock`; its SHA-256 remains `d5bee77a463f56d39394c26991c63535b80726b877582affe1006ad5b2978271` and it is executable (`tools/commit_narrow.sh:11-30`). The history separately preserves the exact violation and pending status (`plan/AMENDMENTS.md:7`); the Round-20 adversarial selector replay remains applicable because the helper is byte-identical.
- Source audits of `tools/amend.sh`, `tools/commit_narrow.sh`, `tools/run_tiebreak.py`, `tools/run_codex_agent.sh`, `tools/_coder_scope.py`, both review wrappers, `tools/check_acceptance.sh`, and the manifest paths. `bash -n` passed for every inspected shell script, Python AST parses passed for all inspected Python tools, and `git diff --check` passed.
- Source-level recheck of Finding 9: repository-path tampering is now neutralized by pre-launch copies and an unconditional post scan (`tools/run_codex_agent.sh:98-110`, `tools/run_codex_agent.sh:129-151`). The copied files remain ordinary same-uid filesystem objects: `/tmp` is enumerable, `mktemp -d` creates no user boundary, and the coder invocation changes neither uid nor namespace while explicitly bypassing the sandbox (`tools/run_codex_agent.sh:8-10`, `tools/run_codex_agent.sh:106-123`). No parent-held hash or in-memory allowlist is checked before the copies are trusted at lines 133-149. SHA-256: wrapper `0d6c1e9ce659e91398a7ab8b86910e0a367ac5da6d1ee0d30390c0b0e1b46575`; helper `d5219b71f50d0bd21361174c0fbde576018ff71924707e32c2c64a499f5aab67`.
- Source-level closure audit of Finding 14: the EXIT trap removes `POST_OUT` and the private directory containing `PRE_MANIFEST`; normal and explicit-error output cleanup remain (`tools/run_codex_agent.sh:89`, `tools/run_codex_agent.sh:106-110`, `tools/run_codex_agent.sh:135-150`).
- Direct read-only replay of `bash tools/check_acceptance.sh plan` before this canonical write: amendment failed at 74 and process at 89; science and spec passed at 92, with no topic-manifest layout failure.
- Ledger/threshold audit: the repository remains pre-Phase-0; the top STATE declares the pending v1.22 amendment transaction and names process Round 20 only after it lands (`plan/LEDGER.md:13`). PLAN.md and Appendix C are unchanged, no phase launch entry exists, and no scientific threshold moved (`PLAN.md:92`, `PLAN.md:470-486`).
- Post-write validation: `check_review_scores.py` parses this canonical file at 74 with one open High and no open Critical finding; the round-tracking validator and `git diff --check` pass. `bash tools/check_acceptance.sh plan` rejects amendment 74 and process 89 while science/spec remain accepted at 92.
