# Coding self-cue screen — fixed recipe parked

Recorded 2026-09-08. **No SCREEN-GO.** The run saved all 72 scheduled calls,
but four responses exhausted the output allowance. Technical evidence is
therefore **INCOMPLETE / CAPACITY-INELIGIBLE**, with complete accounting.
Completed responses also contain coding, submission and recap failures.
The fixed recipe receives no prompt repair, parser relaxation, larger-cap
retry or larger validation launch.

This was a development screen of four original Kimi-authored Python projects,
six dependent requests each, using the same pinned Qwen worker in three arms.
H used ordinary retained history. C added an automatic applicable-rule recap
before code in the same response. M received independently correct manual
reminders. Each arm retained its own actual code; rejected submissions left
its prior code in place. No retries, human corrections or test feedback were
introduced. The [frozen protocol](../../coding-self-cue/PROTOCOL.md) defines
the complete conjunction and stop rule; [freeze.json](freeze.json) binds the
accepted inputs at commit `cf33e861b5651bee87e0671055407e4a93110c69`.

| Recorded measure | H: history | C: automatic recap | M: manual recap |
| --- | ---: | ---: | ---: |
| Passing submission plus all registered checks | 10/24 | 2/24 | 12/24 |
| Entire six-step projects passing | 0/4 | 0/4 | 0/4 |
| Valid code submissions | 22/24 | 8/24 | 23/24 |
| Submission-format failures | 1 | 14 | 0 |
| Output-cap failures | 1 | 2 | 1 |
| Prompt tokens | 57,986 | 37,433 | 62,500 |
| Completion tokens | 8,297 | 10,293 | 8,332 |
| Summed HTTP call seconds | 372.330 | 428.570 | 377.875 |

These are finite-check outcomes on actual retained code, not a claim that every
natural-language requirement was satisfied. The independent semantic audit
identified additional source-level defects beyond those checks. C's smaller
input total partly reflects rejected code never entering its history; it does
not demonstrate useful-work efficiency. All three final responses in the last
project were capped, so their requested upgrades remain incomplete evidence.

Across all 24 visible C recap prefixes, independent Astra xhigh review found
**12 complete and unambiguous, 2 contextually ambiguous, 7 omissions, and 3
definite incorrect claims**. A charitable reading counts 14 complete/correct.
Permission omissions are recorded separately from false claims. The two capped
C responses have visible recap prefixes, but receive no executable or capacity
credit. These observations do not identify a single cause of the poor coding
results, and fixing serialization alone has not been shown sufficient.

The manual arm did not establish a competent positive control. This screen
therefore cannot establish automatic/manual parity, equivalence, general
coding benefit or human-time saving. Matching competent manual prose through
automation remains a valuable target; outperforming ideal manual prose is
not required. Four exposed development projects are not adequate larger proof.

The [mechanical summary](summary.json) is derived from the original saved
records without rerunning worker code or tests. Independent
[integrity review](../../coding-self-cue/result-integrity-astra.md) accepted
receipt accuracy at **96/100**, with zero open high/critical integrity findings:
all 72 exchanges, 1,203 check verdicts, native token counts, state transitions
and frozen hashes reconcile. The separate
[semantic review](../../coding-self-cue/result-semantics-astra.md) preserves
all per-project findings and all recap assessments. Receipt acceptance does
not change the failed scientific screen.

Total usage was **157,919 prompt + 26,922 completion = 184,841 tokens**.
Driver duration was 1,212.160 seconds; GPU reservation including startup and
cleanup was **1,714.459 seconds (28.57 minutes)**, below the 3,600-second limit.
The launcher exited 2, captured logs and removed its owned server. The owned
container, launcher process and RUNNING.flag were independently confirmed
absent. See [lifecycle.json](lifecycle.json) and
[terminal manifest](calls/manifest.json).

Fit-on: none. Development-on: this new Kimi bank, now exposed. No frozen
larger benchmark was rerun or rescored. Next: primary-source research on a
materially different automatic instruction mechanism and a competent coding
comparison. Prior failed updater and reader recipes remain parked. The broader
goal is active and unproved.
