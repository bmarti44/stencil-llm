# Adversarial self-audit of the PASSING rerun for gpt-6-astra (CPU only) — 2026-09-07

You built and ran this. Audit it as an adversary of your own work, exactly as you did in
results/full-program-review-astra.md where you correctly catalogued your own errors. THIS IS THE PROGRAM'S FIRST
PASS ON A LARGER IMPLEMENTATION, which means it will receive less scrutiny than it deserves unless you supply it.
An Opus maximum-reasoning reviewer is auditing the same run independently; do not read
results/larger-test-v2-review-opus.md if it appears, and do not coordinate. THE RESULT IS FROZEN: nothing you find
may change, rerun or reinterpret it. The original FAIL at results/larger-test/ is likewise untouchable.

Subject: results/larger-test-v2/ (RESULTS.md, REGISTRATION.md, records, episode-tables.json, cost-audit.json,
receipts.json, summary, server log); contract SLAB-2 Amendment 6/6b; pinned code
e20c3f9bb9979ba95b9cc797115b742507a3803c; DEV pilots composition-pilot-8 and -9.
Reported PASS with no failed items: 3,328 records, 2.1314 GPU-h; executing lanes 64/64 in every arm; zero round-zero
rejections; register arm 5 initial and 5 surviving syntax errors, 5 repairs, 1 broken episode; N and T 0 broken.
Delivery 35/0/28 over 63 paired episodes, p = 2.91e-11, Holm 8.73e-11; format 25/4/34, p = 5.19e-05, Holm 1.04e-04;
indent 17/15/32, p = 0.430. Final semantic integration R 45 / N 48 / T 52 / Q 16.

Answer with file:line and recomputed numbers:
1. Where could this PASS be wrong? Apply your own audit's lesson list to it. Name every place the RESULTS prose
   asserts more than the records support, any denominator that differs between arms, any metric that is not
   arm-neutral, any pseudo-replication, and anything that changed between the FAIL and this run that could have
   produced a pass for a reason other than the mechanism working.
2. THE PROTOCOL CHANGE IS THE OBVIOUS THREAT. Scoped edits plus a repair turn removed the failure mode that sank
   the first run. Did they also make the task EASIER in a way that inflates the primary, or make the harm clause
   easier to satisfy? Compare the two runs on everything comparable and state honestly whether the primary effect
   is the same phenomenon at the same size, or a different, easier measurement.
3. Explain the missing 64th paired episode in delivery and format, and prove its exclusion is not outcome-dependent.
4. The 5 surviving syntax errors with 5 repairs used and 1 broken episode: quote them; why did the repair not work;
   does the repair mechanism have any demonstrated efficacy?
5. FINAL SEMANTIC INTEGRATION R 45 < N 48 < T 52. The register arm wins adherence decisively and is LAST on
   producing semantically correct work. Test it at the episode unit with an exact paired test. Is this the
   compliance-versus-competence pattern from results/open-problem-5-compliance-competence-astra.md surviving into a
   passing run? Say so plainly if it is, and quantify it. Do not let a PASS bury it.
6. Rewrite the claim sentences with the final numbers: exactly what a write-up may say and may not, reconciled with
   Section 4 of your full-program audit and the registration's pre-declared confounds. Answer directly whether this
   constitutes adequate proof of the mechanism on a larger implementation or proof of something narrower.
7. The single most informative successor, with a cost and honest lineage.
Grade findings low/medium/high/critical. Write ONLY results/larger-test-v2-review-astra.md; commit with an explicit
pathspec (git add -f); no push. CPU only; do not touch the GPU, any flag, container or process; never read anything
under data/bench. Report back a 12-line summary whose last line is your honest headline for this run.
