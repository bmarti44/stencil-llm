# Check 40l for gpt-6-astra: would a CORRECT bias help? competence-direction bias + dose response (2026-09-06)

Brian's question after check 40k (R3 harm: text-only 16/32, text+bias 7/32, text+shuffled 11/32): "is the bias just
wrong, or is it really not worth it? if the bias were truly known and correct, would it help?" Read
results/quick-checks/check40k/README.md and results/check40k-review-fable.md (fable's review; follow its dose guidance
if it gives any). Answer with ONE screen on the SAME 32 evaluation tasks and the same harness (text-only rule line
as 40k; greedy; cap 768; same scorer; hidden tests never shown):
- ARM A is CUT per fable's 40k review (a lower-dose JS screen cannot change shipping; alpha 2 is already known to
  induce JS on only 6/32 fresh tasks in 40d). Run ARM B only; R2 below is therefore not reachable — say so.
- ARM B (competence direction): from the 8 DEV tasks + 16 further FRESH dev tasks you author (never the 32 eval
  tasks), generate text-only replies, score them with their own hidden tests, and record per-layer router logits at
  each generated token (own teacher-forced positions, as the profile recipe in results/moe-routing-research-astra.md
  / check40b). Competence profile = mean over passing replies minus mean over failing replies of the across-expert-
  centred router logits, per layer; require >= 6 passing and >= 6 failing dev replies (else INELIGIBLE for B, say so).
  Norm-match to the 40k tensor at two doses (1/3 and 2/3 of alpha-3 norm). Also a shuffled-competence control at the
  larger dose.
- Paired scoring vs text-only (the 40k text-only records are the baseline: same tasks, same recipe — re-run text-only
  only if any harness byte differs). Report wins/losses/ties, exact sign test, CI, per-arm pass counts, breakage.
- PRE-WRITTEN READINGS: R1 "a correct bias helps": any competence arm beats text-only with wins - losses >= 5,
  losses <= 2, exact p <= .05, and its shuffled control does not -> reopen the actuator line as a competence
  actuator (registered follow-up). R2 "dose only": alpha 1 or 1.5 JS bias reaches ties with text-only (|wins-losses|
  <= 1) with no harm -> language bias is harmless at low dose but adds nothing; line parked. R3 "harm persists at all
  doses and competence direction adds nothing" -> the actuator line is CLOSED with the claim "router-logit bias on
  this trunk does not improve task competence beyond a rendered rule; magnitude harms". R4 anything else ->
  INCONCLUSIVE; record; no enlargement.
Cap 45 GPU-minutes; one model load; write results/quick-checks/check40l/RUNNING.flag while on the GPU. Data lineage:
fit-on = the 24 dev tasks' replies (profile only); evaluated-on = the 32 tasks of 40k, second look disclosed (no
selection on them). Outputs under results/quick-checks/check40l/ (README with readings, tasks/dev tasks, records,
summary, freeze); item 40l in results/quick-checks/README.md (5 lines); WORKLOG (<= 6 lines). Commit scripts/
focus_check40l.py + results (git add -f) with explicit pathspecs; no push.
