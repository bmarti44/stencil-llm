# Handoff rewrite for gpt-6-astra (CPU only, DOCS ONLY) — apply your own audit's Section 6 (2026-09-07)

Your full-program audit (results/full-program-review-astra.md) concludes the handoff is "stale and unsafe to follow
literally" and lists 15 numbered corrections in Section 6. Apply ALL of them.
PROTECTED: the registered 64-episode larger test is RUNNING. Do not touch the GPU, any RUNNING.flag, any container,
anything under results/larger-test/, any check README, any code under src/ or scripts/, or anything under
data/bench. Docs only. Never signal any process.
Deliverables:
1. Rewrite results/HANDOFF-astra.md end to end, applying Section 6 items 1-15 exactly: correct queue state and next
   decisions; the real larger-test description (arms R/N/T x64 + Q x16, no O, 16 rounds, delivery primary, no
   12-round fallback, 3,328 records, projection and ceilings, exact gate, frozen SHA/hash manifest, group schedule,
   and the command that reads the final result); both exact flag paths and the warning that a missing flag is not
   evidence of an idle GPU; a corrected WHAT IS PROVEN (check 42 is a reused-bank diagnostic, not closed under its
   own rule; label the oracle figure by version; the package is a scaffold; scope 40i to its measured envelope);
   the qualified backend statement (4/48 distinct HF differences; 156/166 cross-container identity; drop
   "near-ties"; distinguish same-container replay, score replay and new-generation replication); a rewritten
   closed/parked section (parked by evidence/budget, not mathematically closed; check 49 does not close dense
   weight control; check 46 is six-shot in-context, not zero-shot; correct the 69/22 figures); a per-bank EXPOSURE
   TABLE replacing "held-out-4 UNTOUCHED" (authors, metadata reads, content/audit reads, model looks, error-driven
   development use, allowed future role) and quarantine the 90 evaluation-derived enrichment relatives; reconciled
   review instructions (Opus at maximum effort is the standing rule; fable is the documented fallback; record
   Brian's explicit selection of you as self-auditor as a role override); a corrected stop rule (respect missing
   authorization, contamination boundaries, failed eligibility and stop-loss; fixes need new hypotheses and
   prospective amendments, never automatic re-pilots); authorization separated from capability; the current
   implementation limitations with source lines; adoption statuses marked build vs run vs evaluated; an authority
   map (AGENTS points at archived PLAN/PROTOCOL; the current task instruction and frozen Amendment 5 govern);
   artifact portability and recovery (pinned worktree, source/image/model hashes, which journals and weights are
   untracked, sizes, what can be recreated versus only verified, and that scratchpad resurrection must never re-run
   completed jobs); and precise post-run acceptance steps.
2. Write results/CLAIMS-CORRECTIONS.md: a single table of every claim your audit marked OVERSTATED, UNSUPPORTED or
   CONTRADICTED, with the file that still reads wrong, the corrected wording, and whether the correction has been
   applied or is DEFERRED-UNTIL-AFTER-THE-RUN (individual check READMEs are deferred: do not edit them now).
3. Correct results/astra-assessment-adoption.md in place to mark each row build / implemented / mock-tested /
   evaluated, with receipts or an explicit "unmeasured".
Commit those three files with explicit pathspecs (git add -f); no push. CPU only. Report back a 10-line summary.
