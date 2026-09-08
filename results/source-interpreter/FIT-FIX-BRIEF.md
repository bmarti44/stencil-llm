# FIT implementation corrections — round2 findings1–3

Fit-on remains only the eighteen frozen Kimi FIT rows. No new semantic data,
model call, training, generation, preview or old evaluation access is authorized.
The accepted FIT.md recipe remains unchanged. This is a correction of its
implementation, not a new experiment or an outcome-driven repair.

Use the same native Sol xhigh session. Allowed edits/commit only:
- scripts/source_interpreter_fit.py
- tests/test_source_interpreter_fit.py

Keep FIT.md, FIT-CODE-BRIEF.md, frozen mechanics/preparation code and artifacts,
review files and root ledger unchanged. Reuse existing primitives and keep the
correction focused. Canonical fit-review-astra.md round2 is84/100, not accepted, with
findings1high/2medium/3medium. Its SHA256 is
0ad1904bb9d4b54b04d2d11d8f4c5144e71aeae30c8152fb9801a8a2be75810e.
This brief authorizes focused corrections and CPU checks, never a model run. Starting code is16d4d976ab3ebb8f7d650e5a9ce0ded134475344;
runner SHA a405a9d045eecf90de4974b0c5415025e2418a512eed3f24536a897a36ad67d0,
test SHA7b38c1bf4a9e4b901b5daa91de8b6806af7dd7d77ceff786da7fbe86b8fb8a8e.

## Findings and required corrections

1. HIGH — Stage success currently uses a timestamp sampled before required
completion-record writes. Root independently reproduced the actual pair
consumer using the review's CPU fakes: delay only base COMPLETE publication to
simulated301seconds, with a300second reservation; current code reports COMPLETE,
executes both calls and records base elapsed0/deadline_reachedfalse. Correct
training and generation deadline enforcement through required completion
publication. Use observed post-write timing and a completion protocol that keeps
the stage deadline effective while publication is unresolved. Do not let a
premature COMPLETE marker disarm supervision. A slow/hung publication must stop
the fixed job, preserve completed/unknown work and not start the next model call.
Also make the initial1,220second training bound effective from supervisor launch
through pre-child qualification; a2,400second whole-only guard is insufficient.
Root can enforce this initial bound in its outer observer: specify that exact
required launch contract in the dry plan if using this ownership split. Do not
claim the runner alone provides enforcement supplied by the outer observer.
Do not invent an elaborate transaction service. Use a minimal explicit protocol
and regression tests through real stage/pair/supervisor consumers.

2. MEDIUM — The manually overlaid resolved_generation_config is not native
resolved configuration. Omitted checkpoint fields remainNone there although HF
fills defaults (e.g. min_length0 and repetition_penalty1.0) and derives this
call's max_length5014. Preserve explicit greedy/EOS settings; capture native
configuration actually consumed and distinguish model/control arguments from
generation-config fields. Do not tune settings or infer them from outputs.
Exercise unset checkpoint fields and derived prompt-plus-cap length through
consumer tests; pure fake echoing of the same overlay would miss this defect.
Read-only installed primary code is available; no model/GPU/runtime experiment
or package change. Keep recording observational, without altering decoding.

3. MEDIUM — Missing output currently always becomes UNAVAILABLE, even when
known unstarted. Derive attempt state from durable generation intent and fixed
ordering: training failure means both calls NOT_ATTEMPTED; hard timeout during
base means base in-flight output UNAVAILABLE and adapter NOT_ATTEMPTED. Preserve
uncertainty for an actually started or unresolved call; never invent zero tokens.
Test these through actual failure/lifecycle consumers, not a producer-only helper.

## Verification and handoff

First add focused regressions reproducing these findings; preserve the existing
consumer coverage. Run only tests/test_source_interpreter_fit.py, Ruffcheck and
format on the two allowed files, diffcheck, import/dry checks, and actual direct
absolute-file /tmp unsetPYTHONPATH --_qualify-only. No fullsuite or unchanged
mechanics-suite rerun. No model/weights/CUDA/network/newdata. Required checks
passing means proceed to stable commit and handoff; broaden only for a concrete
new defect or regression.

Commit only the two allowed files. Report actual Sol model/effort/native handle,
commit/hashes, exact test results, reproduced-before/fixed-after evidence, the
minimal stage-completion protocol and any outer-observer requirement, with
confirmation no model execution. Same Astra FIT review topic will independently
check the correction before any prospective launch. Full goal remains active;
this correction alone proves no instruction-tracking or coding benefit.
