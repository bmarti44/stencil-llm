# Staged source-replay preparation stopped

2026-09-08. **INELIGIBLE; preparation stopped.** The frozen one-shot job ended
at its first reference-code checkpoint. It produced no eligible complete bank
and no scientific coding comparison. Automatic reminder usefulness remains
unmeasured by this attempt.

The four instruction schedules passed structural validation. In the first
reference/check round, three projects passed their recorded checks (10, 11 and 9).
The fourth, staged-04, failed all 8 checks with InvalidProgram: AttributeError.
These counts describe reference execution only; they do not establish semantic
validity of the other three projects or justify a reduced-bank comparison.

The concrete failure is a test-input packaging mismatch. Its sources describe
summarize_window(events), where events is a list of event dictionaries. All eight
authored check inputs instead add one outer list around that event list. For
example, the source-described empty window uses input=[[]] with the expected
empty-window summary. The actual worker passes the entire input value as the
function's one argument; it does not unpack an argument array. The reference
therefore iterates a list as an event and event.get raises AttributeError.
Root checked the saved source, checks, reference, execution records and actual
worker/sandbox call path. No input was unwrapped, no code/check was repaired,
and no execution on corrected data was attempted or inferred as a result.

The registered stop applies to the whole bank. Stages 2/3 were never requested;
there is no correction, retry, replacement, extra stage, reduced-bank scoring or
repeat-bank authority. The earlier stopped source-replay bank also stays closed.
Accepted preparation code and the separate historical two-call technical trial
remain limited evidence; neither is a utility result. The parked scientific
runner remains unaccepted as a whole and was not launched.

## Measured run and preserved evidence

- Frozen launch: b3ac8035; freeze SHA-256 d198d9462ba4577615d89ea41a1139dc4d018d8d7895fc0132d4c79404916302.
- Exact exec session 61895 ended with exit 1; driver PID 268799 is absent.
- Active job time: 326.575991960999 seconds; terminal publication:
  326.579981029994 seconds after original start.
- Eight author requests completed, eight later slots remained UNATTEMPTED.
- Service-reported tokens: 19241 prompt and 77119 generated.
  These are Ollama response counters, not an independent billing measurement.
- Recorded reference checks: 38 total, 30 passed, 8 failed. No model worker answered
  a scientific coding task and no final scientific preflight ran.
- All 28 run files (939100 bytes) are preserved with hashes in
  preparation-root-audit.json; each is under 10 MB.

Root verified every exact request against its frozen template, domain/project
and immutable same-project scaffold inputs; every raw response and parsed author
value against saved bytes/hashes; all reference/module hashes; normal service
completion; and terminal/slot consistency. Stage 1 requests had no prior packets,
validator feedback or other-project content. This audit does not certify all
source/check semantics or predict that unwrapped checks would all pass.

The immutable preparation-code-review-at-acceptance.md is the exact accepted
Astra Round 3 snapshot (96/100). The next canonical review is scoped to this
stopped-run report, its failure diagnosis and the enforced stop. No additional
bank-wide semantic approval or scientific code work is justified by this bank.
