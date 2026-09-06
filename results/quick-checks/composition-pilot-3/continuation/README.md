# Conditional exact-context continuation registration

This is an orchestration correction, not a change to the user gate, renderer,
controller, checker, model or saved observations. The original helper adds2048
conservative tokens before rendering. That estimate can exceed32256 while the
actual package-rendered prompt remains admissible. If the first runner stops
there, retain its stop/lifecycle and all outputs, then continue the frozen order
with a CPU exact-render preflight. Assert those IDs again against the actual
loop.generate_once renderer before every HTTP call. Actual inputs must remain
<=32256, cap512 and both qualified EOS IDs remain identical in all arms.

Restore each lane on CPU from literal saved outputs, asserting original prompt
IDs, checker outcomes and workspace hashes. Completed GPU calls are never
regenerated, omitted or replaced. Existing rows remain in the denominator.
For an actual overflow, record the exact length and leave that lane incomplete;
continue the other registered lanes/arms. This avoids an unrelated long lane
preventing the requested DEV diagnostics on every other episode. Source events,
feedback, scopes and full history remain unchanged; no sliding context.

Continue groups00/01/06/07 then02/03/04/05; R then N then T per group, fixed
round barriers at up to4 workers. Existing complete rounds simply need no call.
O is optional after required arms, with a measured-rate worst-case512-token
estimate and1000s reserved for the user's conditional style competence fallback.
The same1000s is reserved at required-call boundaries, with any unrun work
reported INCOMPLETE/INELIGIBLE, never deleted. All three starts plus any trait
screen must sum to<=9000 GPU-seconds; no budget extension.

Start the same qualified command/image/env in a new owned container only after
original cleanup. Replay the eight frozen prompts cold/warm/C4 again; require
D=0. Write the shared parent RUNNING.flag so other Stencil checks see it.
Stop/rm only this new owned container. Same v2 same-run records/tolerances and
per-call IDs/timing; no hidden states, eval construction or data/bench reads.
