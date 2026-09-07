# Pilot-5 Amendment 3 screen — SCREEN-NOT-PASS (budget-limited)

**The eight round-0 format checks passed, but the 16-round screen is incomplete.**
All8 lanes wrote files; only4 lanes completed16 rounds. DEV00 completed16 rounds
per arm; DEV01 completed2 per arm before the registered stop-new-work boundary.
There are72/128 saved replies, all parsed and written, with zero caps. The56
remaining rounds were unattempted, not model failures. No pilot6 or larger test ran.

Pinned green code: `4ab3e21884e0e5decd6d4fd78607abd6a69cf95d`.
[Registration](../../../tests/fixtures/slab2_cpu_report.md) is SLAB-2 Amendment3,
written before code. [Validation](validation.json):121 passed,1 expected xfail
from the isolated pinned checkout,96.43s. No fitting; authored DEV00/01 only for
model calls. No benchmark reads. Existing automated CPU manifest tests regenerate
hashes without inspecting evaluation text; episode content/schedule hashes are unchanged.

| Arm | Round-0 fence failures | Executing lanes | Written / completed rounds | Caps | Model/reference x | Largest reply |
|---|---:|---:|---:|---:|---:|---:|
| R | 0/2 | 2/2 | 18/18 | 0/18 | 1.085 | 473 |
| N | 0/2 | 2/2 | 18/18 | 0/18 | 1.066 | 465 |
| T | 0/2 | 2/2 | 18/18 | 0/18 | 1.065 | 465 |
| Q | 0/2 | 2/2 | 18/18 | 0/18 | 1.010 | 430 |

Execution is a parsed trailer plus actual file write; runtime test failures still
count as execution. Each lane counts once if any round writes, so the lane count
is8/8 despite only4/8 full trajectories. Every arm completed18/32 scheduled rounds
(56.25% coverage), and wrote18/18 observed replies. Conditional on clean round0,
the descriptive per-round result is also18/18 per arm. Missing rounds prevent the
registered >=90% per-round screen requirement from being established over32 rounds.
Q's round0 DEV00 public-test breakage is retained; execution is not task success.

The x-factors use the same convention as pilot5: model output including EOS divided
by reference tokens excluding EOS (reference3546 tokens per arm for these18 rounds).
The runner's untouched summary uses EOS on both sides: R1.079,N1.061,T1.060,Q1.005;
[audit.json](audit.json) records both. These are measured partial-trajectory factors,
not a full-run verbosity or cost estimate. No new T floor was frozen from this screen.

## Budget and pre-written reading

GPU held **856.627/900s (14.28min)**: startup439.215s; DEV00 mixed C4 group393.650s;
DEV01 partial mixed C4 group13.739s; remaining overhead/cleanup10.023s. Each fixed
group contains one episode's R/N/T/Q. The cooperative boundary refused further
requests with<55s left, and cleanup stopped/removed only the owned container.
No host process was signaled. The owned RUNNING.flag is absent. The prior check49
reservation was respected before launch. Startup consumed nearly half the total
budget; the complete requested128-call screen did not fit in the remaining time.

PRE-WRITTEN READING: SCREEN-PASS requires all128 records, zero round-0 fence failures,
executing lanes8/8, and >=90% strict per-round execution in EACH arm. It authorizes
full pilot6 (8 DEV episodes,R/N/T/Q,16 rounds), whose ELIGIBLE reading authorizes64.
Any round-0 fence failure is SCREEN-FAIL: publish literal failures and do not enlarge.
Other incomplete/low-execution cases are SCREEN-NOT-PASS; no enlargement.
**Observed: SCREEN-NOT-PASS for incompleteness.** Zero round-0 fence failures0/8
supports the format repair in this small sample; it does not supply the missing56
rounds or a full eligibility result. No automatic retry, pilot6, or larger run.

## Corrected historical floor and cost

[Saved pilot5 T-floor recomputation](pilot5-corrected-floor.json), from all128 T records:

| Trait | Satisfied / applicable | Qualifies at50% |
|---|---:|---|
| language |72/128|yes|
| indent |13/39|no|
| format |22/35|yes|
| delivery |42/49|yes|
| delivery_scope |0/44|no|

Indent counts only rounds at/after each episode's actual supersede (turns10–12),
including later reinstatement; failed/missing attempts stay in the denominator.
Language, format and delivery qualify; among the registered primary substitution
kinds (indent/style and delivery/process), **only process qualifies**. The historical
pilot5 remains INELIGIBLE. Prior64-fence-failure plus1-syntax-error R non-executions
are an instrument deficit; these records do not establish a register execution effect.

Historical Q-exclusive measured projection7.774h; estimated repair range6.6–7.8h.
Mandatory Q at N-like cost adds2.613h, giving~10.4h at the upper endpoint. That Q
cost was an estimate. Full cost formula is
`(load + 1.25*(64*(R+N+Q)+16*(O+T)))/3600`.
This mixed-arm, incomplete screen cannot replace a full same-arm-C4 cost measurement;
no new registered-run cost projection is claimed.

## Artifacts and audit

[Records](records.jsonl):72 same-run records,193,003 bytes (<10MB), including literal
outputs, token IDs/EOS/caps, executor results and checks. [Summary](summary.json),
[launch](launch.json), [lifecycle](lifecycle.json), [cleanup](cleanup.json),
[server log](server.log), [HTTP index](journals-index.jsonl), and
[local hashes](local-hashes.json). Raw HTTP payloads and loop journals remain local,
out of git, with hashes. The launch records the user-authorized Brian-server exception.

[CPU audit](audit.json) via [audit.py](audit.py) replays all72 saved responses through
the pinned R/N/T/Q loop and executor: **zero request-payload mismatches and zero
record-field mismatches**. It verifies token accounting, reading, budget, and removal
of the owned container/flag. No additional inference was used for the audit. No push.
