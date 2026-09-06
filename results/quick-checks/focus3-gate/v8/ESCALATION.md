# Brian escalation — final FOCUS-3 iteration, 2026-09-06

**V8 is INELIGIBLE and the registered iteration budget is exhausted.** The CPU
replay passes36/36 admissions and11/12 transitions but retains12 unauthorized
actions (required zero). The five-arm GPU gate was not launched. No further
iteration, corrective replay or tuning was performed or is scheduled.

All three authorized changes were implemented and tested: 300 hand-written
request/rule examples across10domains plus one refit per seed0/1/2; completion
scope restriction; and reinstatement admission/own-key/status/cancellation guards.
The relation model, thresholds, banks, renderer and readings remained fixed.

| Remaining problem | v7 | v8 |
|---|---:|---:|
| One-shot payload requests falsely admitted |10|8|
| Inert quotes falsely admitted |4|3|
| Generic replies reinstating cancelled sorting rows |4|0|
| Completion retiring an extra polluted same-task row |1|1|
| Total unauthorized actions |19|12|

The reinstatement key guard addresses the traced failure, including three spans
that still pass rule admission. The completion guard preserves global rows but
cannot distinguish a wrongly admitted row already assigned to the completed task.
Admission remains the limiting failure: new-family DEV negatives show0/21,0/20,
0/18 admissions across the three seeds, yet eight bank payload sentences and
three inert quotes still enter the runtime register. Those small DEV samples do
not certify the bank's request family. One new payload error appeared while
three previous ones disappeared; no isolated causal improvement is claimed.

The author-disjoint Fable diagnostic has unchanged accuracy318/363 (87.60%)
and rule admissions111/124, with non-rule admissions worsening5→8/239.
The unchanged relation miss remains P(supersedes)=.570806 below the frozen .90.

122 tests pass, one existing expected failure; saved-record and independent
accounting audits pass. Actual GPU use269.749111seconds of the three-hour cap.
All96CPU records and16traces are preserved. No gate efficacy/safety result exists
for v8. Brian's decision is the next program step; the agent has stopped this gate.

[Full registration and evidence](RESULTS.md)
