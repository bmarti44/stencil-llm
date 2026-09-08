# Coding competence resource qualification

Prospective DEV estimate, 2026-09-08; no new worker calls. This binds the
accepted bank and initial stable runtime preview, pending full readiness review.

- Bank SHA256: `c9feaa9370244ccc4a84221ecb5b3db3ea85d11f9abd210536e78fd25cd6cdaa`.
- Accepted CPU receipt SHA256: `552baba5438c530b8dfb88724e18d4d5f5d0b3d20c5a1a8df3fbcd2e4f4b45fd`.
- Preview SHA256: `ebd333a108947d15f3ffbe6d1da3e1d371012b8bba369a48920f0f42b99e2fa9`.
- Runtime SHA256: `5a06b47db19d6acc5915fb308e73b80bc92d2abd80afda9e4c119c1166966b3a`.

The exact assembled bank passed 851 CPU checks in 15.713863611
seconds. Runtime bounds allow 617 sandbox checks, 36 render requests and
36 generation requests. Scaling the measured CPU average to that check count
gives 11.393 seconds, versus the registered 120-second execution allowance.
That is an estimate from reference/control work, not a guarantee about future
generated code. Pathological checks and larger render/prefill work can consume
more time; the single hard reservation controls the actual run.

The 12 compact reference argument responses plus one EOS use between
155 and
624 local
tokens; minimum output headroom is
400, above 128
within the unchanged 1024 cap. Four actual known cold request JSON serializations
use 1343, 2082, 1871, 2121
local tokens. These are provisional serialized-JSON counts, not authoritative
native prompt token counts. Every actual native request still requires exact
render validation before decode. All 36 generic accepted-size history envelopes
are disclosed and do not certify universal fit of unknown future history.

The accepted research report's prior whole-HTTP completion rate is
26922 / 1178.774697 = 22.8389700496 tokens/second. At the full 36 × 1024 output
ceiling, the illustrative generation/HTTP estimate is 1614.083294 seconds.
Adding startup 600, execution 120 and cleanup 60 gives 2394.083294
seconds, leaving 305.916706 seconds within the 2700-second total
reservation (existing absolute authorization ceiling 3600). The prior rate is
not a throughput guarantee for the new native loop. Auxiliary render and changed
prefill overhead count against that same hard reservation and its margin; they
do not create additional budget. The launcher must retain 60 seconds for cleanup
and pass only the remaining deadline to the driver after startup.

No later token-cap, prompt, attempt-count, data or budget rescue is permitted
after worker output. Technical/context/deadline failure ends the whole run as
incomplete/ineligible with all partial work recorded. Mechanical 12/12 and 4/4
success still requires independent source/dependency and lifecycle review.
