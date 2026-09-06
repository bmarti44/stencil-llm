# FOCUS-3 gate — RESULTS v2 (2026-09-06): FAIL

The authorized renderer correction passed setup **16/16** (required15/16),
so all **64 fresh gate episodes / four arms / 1,536 gate answers** ran.
The gate **FAILS**: C final success27/64 versus O61/64, stale executions27/64
versus O2/64, and exact rendered-register agreement0/64 (required48/64).
The failed prerequisite is initial ordering-rule admission: **0/64 admitted**.
This is a failed end-to-end package, not a measurement of relation-transition
recall on correctly admitted ordering rules.

The register now emits the plain live obligation
**“Ordering: return the list in the given order.”** when no applicable ordering
row survives, including after cancellation/completion and on a fresh task.
Defaults are derived after precedence, so a surviving global ordering wins;
they are scoped to sort requests and never become classifier candidate rows.
C/O use the identical renderer; N/T and all classifier decisions are unchanged.
Supported ordering vocabulary is recorded in the [v2 ruling](README.md).
No “no longer applies” commentary or masking was added.

| Setup family | Final success | Post-change stale episodes | Breakage |
|---|---:|---:|---:|
| Override | 4/4 | 0/4 | 0/4 |
| Cancel | 4/4 | 0/4 | 0/4 |
| Complete-and-move-on | 4/4 | 0/4 | 0/4 |
| Switch-and-return | 4/4 | 0/4 | 0/4 |
| Total | 16/16 | 0/16 | 0/16 |

Setup uses O rendering; C processes messages only for timing/diagnostics.
There were76/80 successful task replies and80/80 correct tags. All96 answers
are retained, including four hard-none cancellation-family ordering errors.
V1 setup was8/16 with cancellation/completion0/4 each; its full evidence is in
[v1/](v1/RESULTS.md). **Seed30302 was already used in v1**: the explicitly
requested seed was reused, not replaced or claimed fresh. The entire bank is
byte-identical to8f0c550b; the seed30301 gate had no previous outputs.

| Arm | Final success /64 | Stale episodes /64 | False retirements /64 | Breakage /64 | Register-exact /64 |
|---|---:|---:|---:|---:|---:|
| C: classifier register | 27 | 27 | 64 | 0 | 0 |
| O: oracle register | 61 | 2 | 0 | 0 | 64 |
| N: no register/rendering | 25 | 38 | — | 0 | — |
| T: all prior rules restated | 31 | 32 | — | 0 | — |

| Family (16 each) | C/O final success | C/O stale episodes | C exact | C false retirements |
|---|---:|---:|---:|---:|
| Override | 11/15 | 4/0 | 0 | 16 |
| Cancel | 7/14 | 7/2 | 0 | 16 |
| Complete-and-move-on | 3/16 | 14/0 | 0 | 16 |
| Switch-and-return | 6/16 | 2/0 | 0 | 16 |

All frozen PASS terms were applied: stale distance25>4, final-success
distance34>4, false retirements64>2, exact agreement0<48 and0<12 in every
family fail. Breakage0<=2, contradictory recaps0, and C stale27<T32 pass.
The conjunction remains FAIL. Counts describe this fixed synthetic cohort;
no statistical superiority or general shipping-readiness claim follows.

“False retirement” was pre-defined to include missing initial admissions.
C admitted every initial global tag (64/64), but no initial ordering rule
(0/64; P(rule) range0.009522–0.045400, below the frozen0.95 threshold).
Across gate C traces the only applied events were64 tag admissions: no
supersession, cancellation, completion or reinstatement occurred. All480
available relation pairs were gold-none and applied-none, involving admitted
tag rows. Forty-eight gold change events had no target pair (16 each
in override/cancel/complete), so none-only pair accuracy is not transition
competence. Hard-none messages changed no C state; admitted_beside_live and
overflow counts are zero. Missing order admissions cause defaults to render
even while an ordering should govern; the agreement metric catches this.
See [diagnostic audit](diagnostic-audit.json) and [independent audit](independent-audit.json).

O's remaining failures are two stale ascending cancellations and one override
reply containing an incorrect payload value; all have correct tags and valid
schema. They remain failures, with no replacement or exclusion. The setup
repair therefore improves the tested cue behavior without making O perfect.

Switch-back is separate: final success **C6/16, O16/16, N16/16, T16/16**.
Each arm has16 recorded return requests; previously generated output-column
counts are C/O/T960 and N964. These are provenance counts, not masked-column
counts: masking and mask-un-release are zero throughout. This run provides
no evidence about lifting attention masks.

Freeze commit **27003fda** precedes all v2 outputs. Projection3504.527s selected
64 before gate inference; no48-episode reduction. Charged GPU-held time was
**2965.079/10800s (49.418min)**, including v1's181.012s; v2 alone2784.067s.
There were43,831 gate tokens plus2,216 setup tokens including EOS; peak trunk
allocation8,795,689,472 bytes. Gate C classification took60.343s in total,
per-message median0.139s and observed p95 0.262s; setup classification14.525s.

Validation: **19 applicable targeted tests pass; Ruff and whitespace checks
clean**. Two sealed-byte hash tests were excluded under the explicit no-read
instruction; all other requested tests ran. Both raw-record audits PASS on
**1,632 records /272 complete episode-arms**: token decoding, full own-answer
prompt histories, provenance, oracle states, C live sets, agreement, endpoint
counts and frozen source/model/input hashes. All131 archived v1 files were
verified byte-for-byte against8f0c550b. Classifier/runtime decisions, episode
builder, decoder, renderer function and checkers remain AST-identical to v1;
the changed register supplies the explicit default and audits recognize it.

[summary.json](summary.json) includes the complete endpoints, setup and
diagnostics; [run-summary.json](run-summary.json) preserves the original runner
summary. [setup/](setup/) and [gate/](gate/) hold all same-run records/traces;
[audit.json](audit.json), [independent-audit.json](independent-audit.json),
[audit_records.py](audit_records.py), and [cpu.json](cpu.json) carry verification.

No fitting, training, threshold tuning, sealed input read, process signal or
push occurred. Admission retains its disclosed development influence; there
is no development-independent package claim. The foreground process exited
naturally and removed its own RUNNING.flag. The completed failed gate is closed;
no outcome-based repair, additional fitting or rerun was performed.
