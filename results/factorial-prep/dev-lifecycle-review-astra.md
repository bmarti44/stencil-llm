Fit-on: none. Development-on: synthetic CPU lifecycle simulations only. Evaluated-on: none. No Docker, GPU, network, model, benchmark, held-out or frozen-result access; full model weights were not reopened.

# DEV serving lifecycle — independent review

2026-09-07 · Round 1 · Reviewer: gpt-6-astra, xhigh reasoning. Explicit user-requested Astra xhigh replaces the historical Opus assignment. Author-disjoint from the parent-authored `tools/run_maintenance_dev.py`; only this review file is written. Threat model: trusted-but-fallible operators. Purpose: safe ownership, bounded reservation, source/receipt binding, pre-inference freeze and honest cleanup for the prospective 16-call DEV check. Updater/driver integration remains pending and is not required to exist for this process review.

**Score: 80/100. Not accepted: two open high findings; no critical findings.** Reviewed script SHA256: `05a9e3e282ef0664b5ed71df1819c6e3cd0827c2abbad8dab695e5d94c67049a`.

### dev-lifecycle#1 — high (resolved 2026-09-07, Round 2): the 900-second ceiling has no parent-side enforcement

At lines 125–126, `subprocess.run(driver, ...)` has no timeout. Passing `--deadline-seconds` cannot protect against a blocked request or defective cooperative deadline in the child. Cleanup is consequently unreachable while that call remains blocked. A CPU simulation through actual `main` allowed a 950-second driver, then returned **0** with `gpu_held_seconds=955.0`, despite the registered 900-second ceiling.

Give this directly owned child a bounded outer timeout that preserves the cleanup reserve. Record deadline exhaustion as incomplete, return nonzero, retain partial artifacts, and execute cleanup without retrying inference. The parent's proposed `timeout=remaining+5` preserves approximately 55 seconds of the existing 60-second reserve; confirm it against actual driver integration and cleanup timeouts.

### dev-lifecycle#2 — high (resolved 2026-09-07, Round 2): cleanup failure can report a successful exit while resources remain reserved

The return at line 128 is already selected before `finally` executes. If `docker stop` and non-forced `docker rm` fail, lines 140–154 record `cleaned=false` and retain the flag, but still return the child's **0** and leave status `DRIVER_EXITED`. Actual-main mocks reproduced exactly that result. A failed stop followed by removal of a still-running container can leave the GPU occupied beyond the stated ceiling. `gpu_held_seconds` then measures only time until the parent exits, not completed resource release.

Use a bounded cleanup fallback directed only at the container this invocation attempted to create, such as force removal after failed graceful cleanup. If removal cannot be confirmed, retain the reservation, return nonzero and identify cleanup failure explicitly; label elapsed time as incomplete rather than final GPU-held usage. No unrelated process or container should be stopped.

## CPU evidence and qualified behavior

The unmodified default CLI dry run returned its plan without launching or creating a run directory. Six independent disposable-directory simulations called actual `main` with every subprocess and HTTP operation mocked: normal success, nonzero child, child-launch error, startup timeout, child overrun and cleanup failure. Freeze existed before the simulated Docker launch, and the exact driver command existed before its call. Normal/error paths reached own-container logs, stop and remove; child errors were not retried. Startup failure invoked zero driver calls. The two counterexamples above are the only failing properties identified in those simulations.

Preflight checks reject existing reservations/containers/GPU compute users, the script reserves its own run directory and records its PID, and cleanup addresses its generated container name rather than searching for processes by name. The container uses the pinned local image and a read-only model mount. Required source and receipt paths must be tracked and clean; their bytes and Git HEAD enter the same-run freeze before launch. Weight freshness is a size/mtime check against the separately computed hash receipt, not an independent full-weight rehash. Receipt completeness and actual driver dependency/settings coverage still require final integration verification before inference.

This is a development feasibility check on exposed DEV seeds. Successful lifecycle review would neither authorize a clean evaluation nor establish updater quality.

## Round 2 — 2026-09-07

Same independent Astra xhigh reviewer; scope remains the two findings and their fixes. **Score: 95/100. Accepted for this bounded process-tooling purpose; no open high/critical findings.** Prior score and finding text are retained; only explicit closure markers were added above.

**dev-lifecycle#1 resolved.** The actual driver call now has `timeout=remaining+5`; `TimeoutExpired` records `INCOMPLETE_DEADLINE`, returns 124 and proceeds through cleanup without inference retry. A separate measured overrun produces `BUDGET_EXCEEDED`/124 even when the simulated child returns zero. CPU checks verified the timeout equals the supplied cooperative deadline plus five seconds. With a two-second synthetic launch, expiration places cleanup at elapsed 845 seconds; spending all four cleanup allowances (10+15+10+10 seconds) finishes at 890 seconds. These subprocess timeouts provide the operational backstop; they cannot guarantee recovery from an unresponsive Docker daemon or host.

**dev-lifecycle#2 resolved.** Graceful cleanup failures reach a bounded `docker rm -f` fallback for this invocation's exact generated container name. Confirmed removal releases the flag; failed or exceptional removal sets `CLEANUP_FAILED`, preserves the prior status and phase errors, retains the flag and overrides success with exit 125. When `cleaned=false`, the elapsed receipt is necessarily a lower bound on the ongoing reservation, not proof of completed GPU release. The revised resource paragraph identifies the measurement as reservation time and expressly documents owned-child termination, cleanup failure and overrun handling.

Eleven disposable-directory CPU scenarios exercised actual `main`, with all subprocess/network calls mocked and assertions on exit status, flag state, one-or-zero driver calls, timeout values, freeze ordering and exact cleanup target: normal return; nonzero child; child launch error; startup timeout; child timeout; measured overrun; successful forced cleanup; failed forced cleanup; combined child timeout/cleanup failure; exceptions in every cleanup phase; and the full cleanup-time allowance. All assertions passed. Individual cleanup errors remained visible and did not skip later cleanup phases. No real container, process termination, model request or full-weight read occurred.

Reviewed SHA256: script `b2fd2be6c744812b74c66f5c575de1036e505fc4fe46443af7a780e5c9207c11`; resource contract `6dc38e379238cb7b7c9c993b38886b506f0efdc8e17fa0e72c33458f86871f26`. Final updater/driver integration, committed receipt completeness and input/settings qualification remain pending outside this review; this acceptance alone is not a launch or accuracy verdict.
