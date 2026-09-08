# Automatic reasoning pilot — terminal observations, audit pending

2026-09-08. Fit-on none; development-on the two fresh Kimi/Ollama projects in
this run; evaluated-on none. Both projects are now exposed DEV, never FIT.

The fixed pilot is **INCOMPLETE**. Its final worker response reached the 2048
completion-token cap. No partial edit was applied or repaired, and no retry was
made. This batch cannot pass the registered continuation rule. The broader
focus goal and adequate fresh larger proof remain unestablished.

| Project | Request 0 | Request 1 | Request 2 |
| --- | --- | --- | --- |
| Classroom | Finite checks pass | Finite checks pass | Finite checks pass |
| Playlist | Private duplicate-permission check fails | Finite checks pass | Technical incomplete: length cap |

Five of six scheduled requests completed; four of six passed their finite checks.
The classroom project's three finite passes are a narrow observation awaiting
independent source/code/focus review, not an accepted usable-workflow result.
No failed or unfinished endpoint is removed from the denominator. All six focus
calls returned, but structural validity does not establish accurate reminders.

The normal public-only stopping rule selected the first worker edit for each of
the first five requests. They passed all 59 executed public checks. The terminal
private checks ran 86 times across those five endpoints, with one failed check:
playlist normalization rejected repeated tracks despite allow_duplicates=true.
The last capped response received no endpoint checks. Independent static source
review is pending and can identify additional defects missed by finite checks.

There were 12 native renders and 12 generations: six selectors and six workers.
Raw response usage totals 39,193 prompt + 14,141 completion = **53,334 tokens**,
including the capped call's 10,774 prompt + 2,048 completion = 12,822 tokens.
The runtime's validated-call aggregates omit that failing call and mark accounting
incomplete. The separate parent observation restores raw-response cost only; it
does not validate capped arguments or complete the unfinished work.

Generation HTTP time totaled 666.2795095319743 seconds; native render HTTP time
0.9065805140126031 seconds. The entire owned reservation used
**1195.4825121320027 seconds**, including startup and cleanup. Adding the earlier
technical smoke's 516.914703271992 seconds gives 1712.3972154039948 actual seconds
for this candidate. Unspent time does not authorize a retry or revised cap.

The launcher terminated with exit 2. Its lifecycle records successful cleanup
and complete cleanup evidence; root's Docker and GPU compute queries were empty.
All 28 frozen tracked-file hashes and four model metadata hashes still match.
The frozen commit was 9d40e0d11fb0f8ec760096b1d3e051c10f10b42b. The accepted
readiness report remains unchanged. Human interventions in the run: zero.

Parent measurement artifact: `parent-observation.json`, SHA-256
`3ff11807a630595c0be5f622a1f6ed15188a5a7c41513f632ab79dfaaa55f17a`. Every raw call, source view, actual code state, check receipt and
lifecycle record is preserved. Astra xhigh is independently auditing these
observations in `audit-astra.md`; append its accepted result below when complete.
No empirical success claim or new experiment follows from these observations.
