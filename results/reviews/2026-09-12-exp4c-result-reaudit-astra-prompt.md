# Exp 4C result re-audit after repairs (Astra, read-only, maximum reasoning effort)

Your first audit (`results/reviews/2026-09-12-exp4c-result-audit-astra.md`) returned REJECT /
INCOMPLETE on two grounds. The owner has directed that bugs be fixed and the process tuned
rather than the result left in limbo, so this is a second audit of the CORRECTED evidence.

Since your audit: (1) the provenance metadata defect (finding 1) was repaired from unchanged
outputs by `scripts/memorycode_4c_reprovenance.py` (base-window boundary; byte-identical
prompt and reminder asserted per item; previous values retained; `reprovenance-4c.json`); the
runner self-checks and the validator requires that kept spans reproduce the reminder; the
summary was recomputed (`summary-4c.json`; superseded summaries retained beside it). (2) The
interim looks (finding 2) are an owner-directed procedural deviation, disclosed in
RESULTS-4C.md; they cannot be undone. The owner's standing rule for all future work is:
interim looks allowed, early stop only for futility, positive claims need the full N.
(3) RESULTS-4C.md wording and chronology were corrected per findings 4 and 8.

Same constraints as before: no `data/bench/`, no writes, no models, no GPU. Verify the repair
(spans reproduce reminders on 139/139; boundaries equal the package's base-window cut; no
output, score or statistic changed), re-derive the mechanical reading, and state whether the
evidence is now technically valid and complete. Then give ONE of: `VERDICT: ACCEPT` (the
reading NOT PROVEN, FINAL is the mechanically prescribed reading on valid, complete evidence,
with the interim-look deviation disclosed) or `VERDICT: REJECT` with the decisive reason.
Begin the report with the verdict line and `READING: <row>`; number findings with severity.
