# Resource plan — final CPU evidence, pending launch readiness

2026-09-08. No new worker run is authorized by this draft. Fit-on none;
development-on two fresh Kimi/Ollama projects; evaluated-on none. Kimi cloud
authoring uses the already authorized local Ollama endpoint and is recorded
separately. No new model, paid API or external compute is acquired.

The complete candidate ceiling is 3600 seconds of owned GPU reservation. Its
completed technical smoke consumed 516.914703271992 seconds, established by
the audited lifecycle in ../coding-reasoning-smoke/run-01/lifecycle.json.
The prospective automatic pilot reserves at most 3000 seconds, including a
600-second startup limit and 60-second cleanup reserve, using the unchanged
owned lifecycle. Combined ceiling charge: 3516.914703271992 seconds. Remaining
headroom to 3600: 83.085296728008 seconds. No later run is assumed to fit.

Two projects x three requests x (one selection + at most two editing calls)
gives at most 18 native render/generation pairs. All calls use a 2048 total
completion cap and 1024 thinking allowance, with context 32768. At the maximum
reasoning span, two reasoning delimiters and one terminal EOS leave 1021 tokens
for final arguments. Accepted reference edits and complete focus objects must
each leave at least 128 of these tokens unused. All six accepted reference pairs
passed the CPU preview; task simplification is not a capacity remedy.

Offline reference focus includes oracle entries whose typed scope is global or
the exact current task handle, preserving their text, source IDs and order,
including permissions and exceptions. This projection does not prove semantic
completeness; the independent data review checks it against authentic sources.
Reference capacity does not require the selector to repeat the task's algorithm.

The previous richer-context worker produced 5777 completion tokens over
307.08357315306785 generation HTTP seconds: 18.812468347567442 effective tokens/s.
The tiny technical smoke is not substituted as an optimistic throughput estimate.
At this historical rate, 18 x 2048 tokens require 1959.551469744624 seconds.
Adding 600 startup + 60 cleanup + 120 for other work gives 2739.551469744624
seconds, leaving 260.448530255376 inside the reservation. This is a feasibility
estimate, not a bound on growing prompts or future performance.

The one final CPU preview completed with zero model calls in 8.343103285995312
seconds. Its nested preflight passed all 465 checks in 8.286304591980297 seconds;
the standalone preflight is extracted from that same receipt, not another run.
The live batch permits at most 262 sandbox checks, 18 native renders and 18
generations. The observed CPU cost fits inside the 120-second other-work estimate;
that allowance remains an estimate and the shared deadline is authoritative.

| Project | Request | Current focus argument tokens | Edit argument tokens | Cold request serialization + output reserve |
| --- | ---: | ---: | ---: | ---: |
| Classroom | 0 | 189 | 170 | 2942 |
| Classroom | 1 | 193 | 105 | 3284 |
| Classroom | 2 | 261 | 334 | 3717 |
| Playlist | 0 | 141 | 585 | 3060 |
| Playlist | 1 | 222 | 323 | 3644 |
| Playlist | 2 | 327 | 687 | 4433 |

Minimum reference headroom is 334 tokens. Cold request counts tokenize the local
request JSON and are not native rendered prompt counts. Up to five earlier
worker action/result pairs and six repeated module observations can accumulate;
their future generated contents are unknown. Every actual call still requires
the same-byte native render and full output reserve check.

Final CPU evidence binds these exact bytes:

- `author-00/reviewed.json`: `1a5f91d4e0fac8ee467741bbcafd581a11a40e04ddcdb384b41a49e8d54617b0`
- `author-01/reviewed.json`: `9e866c8ada769e6371615d509000ff02fd3d3dc6056e64e73213183417ee1dc8`
- `data-review-astra.md`: `e287b5de9c44f1d26f78dd8ed92906a6dd44d72e31b818388b3e381e1998dbce` (96, all six findings resolved)
- `preview.json`: `86fbc268dfc44fc21f741c7cdc6200d5d1d8147112c10aa1072a48048ff977de`
- `preflight.json`: `7df5934ac42445a02f3d1549ba54dcf1d83c4dc09925ce1308cb411ca41547f4`

The preview binds the settled runtime SHA
`4e11075af871ce8bad7d0d9e85005a407f6ebd422da29468e08271cf1f1770cb`,
accepted client, reused execution sources and tokenizer metadata. The launcher
checks those bindings and snapshots every named source, test, input, review and
resource artifact against the clean tracked freeze before starting the server.

The hard shared monotonic deadline bounds actual startup, native rendering,
generation, sandbox checks, receipt writes and cleanup. The driver receives the
remaining allowance after startup minus cleanup reserve. Before every decode,
the actual same-byte render must pass native schema/settings/ID/context checks
with the full output reserve. Unknown future focus/module/history cannot be
claimed to fit from a local preview; overflow or technical failure terminates
the batch as INCOMPLETE. No prompt truncation, retry, cap increase or deadline
extension is available after the freeze.

Reuse the already present Qwen3-30B-A3B model and pinned local image
vllm/vllm-openai@sha256:3dbe092ec5b2cef63b6104d33fa75d6ce53a7870962529ada69f78bbbc38e776,
with the tested qwen3 reasoning/Hermes tool configuration. Preserve the accepted
weight size/mtime manifest and metadata hash qualification without claiming a
new full-weight hash pass. Final source/data/preview/review hashes and exact
container/driver commands will be bound before execution. No wrapper, other
run flag, container or GPU process may be active at launch. Register every
owned process immediately and clean up only resources this invocation creates.

Status: CPU READY; the final launcher's actual artifact and smoke-budget validators
pass on these bytes. Launch remains pending independent combined readiness
acceptance, tracked freeze and exclusivity checks.
The exact intended root invocation is `.venv/bin/python
tools/run_coding_auto_reasoning.py --run-dir
/home/bmarti44/stencil-llm/results/coding-auto-reasoning/run-01 --execute` from the
repository root; actual execution records its fully expanded driver/container
commands and unique container name in `run-01/freeze.json`. The run directory
must not already exist. The broader automatic-focus goal and fresh larger paired proof remain
outstanding regardless of this pilot's result.
