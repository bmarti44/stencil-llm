# Handoff kit (2026-09-06)

Everything an incoming orchestrator needs that otherwise lived only in the session scratchpad (/tmp, wiped on
reboot). Read ../HANDOFF-astra.md first.

- `briefs/` — every check/build/research brief exactly as issued, including the ones still queued
  (check47-brief.md running; pilot5-brief.md, check48/49/50-brief.md, larger-test-brief.md queued;
  adoption-brief.md and driverfix-brief.md in flight). `post-reboot-common.md` is PREPENDED to every GPU brief
  (RUNNING.flag protocol, never signal, foreground only).
- `chains/` — the bash chain scripts that sequence them. Each waits on a sentinel string in a previous chain's log
  and on `results/quick-checks/*/RUNNING.flag` before taking the GPU. After a reboot the logs are gone: re-create
  the chain you need from the brief, register the pid (`echo $! >> .stencil-owned-pids`), and keep the same
  flag protocol.
- Reviewer note: "fable" is a Claude subagent reviewer. On 2026-09-06 it hit a model rate limit mid-review; the
  standing fallback is to re-launch the same review prompt with a different model (opus) and keep the same output
  filename, noting the substitution in the file header.
