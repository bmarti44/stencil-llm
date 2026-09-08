Fit-on: none. Development-on: two original Kimi-authored conversations and synthetic CPU controls. Evaluated-on: none. Prior aggregate reports motivated the question; no old evaluation examples or responses were reused.

# Automated maintenance preparation

Brian's correction governs: automated upkeep that matches good manually maintained prose can be valuable. Superiority over the manual oracle is not required. See [current goal](../CURRENT-GOAL.md) and [the correction](USER-CORRECTION.md).

Completed: Kimi K3 via Ollama authored two eight-turn DEV trajectories; a separately retained Kimi patch clarified two permission-versus-requirement ambiguities. Independent Astra xhigh review accepted the corrected source/operation/view data (93/100) and the revised hypothesis (94/100). Sol xhigh implemented an annotation adapter through the existing register; its 12 targeted tests and lint pass, and independent Astra code review accepts this bounded adapter (93/100). CPU replay matches 48 effective views and 15 gold operations. These are annotation checks, not automatic-updater results.

Receipts: [CPU validation](cpu-validation.json), [design/data review](automation-design-review-astra.md), [code review](maintenance-code-review-astra.md), [original data](kimi-dev-authored.json), [Kimi patch](kimi-dev-patch.json), [corrected data](kimi-dev-reviewed.json), [canonical adapter output](kimi-dev-canonical.json). Prompts, complete provider responses and timing receipts are preserved beside them. Rationales are excluded from verified supervision: the TypeScript patch's explanation invents a pre-existing error-name rule, although its source and state labels are correct.

Two code-review medium findings are deferred for this bounded raw-JSON adapter: exact integer/child-type validation in the public typed API, and user-role binding for completion evidence. The raw authoring path supplies schema/index types and excludes completion, so neither affects these DEV fixtures. Completion remains untested. No claim of general implicit-admission coverage follows from these explicit-cue seeds.

The isolated one-call updater and minimal 16-call DEV driver are implemented: 32 targeted tests pass. Independent reviews accept updater 94, driver 95 and lifecycle 95, with no open high/critical findings. Next is the registered 16-call DEV run with a 900-second total reservation ceiling. [Updater contract](UPDATER-CONTRACT.md) and [DEV check draft](DEV-UPDATER-CHECK.md) describe the component check; the DEV recipe is now registered before model responses. No model updater response, worker task result, clean screen, or deployment qualification exists yet. The optional larger factorial is deferred.

## Completed DEV attempt

The registered run completed all 16 calls in a 620.47-second total reservation and cleaned up successfully. It failed semantic maintenance: the updater substituted project descriptions or prompt wording for standing obligations and repeatedly attempted duplicate additions. Five transactions were structurally accepted and eleven rejected; acceptance is not semantic correctness. See [the preserved result](../quick-checks/maintenance-dev-01/RESULTS.md) and its independent Astra audit. The paragraph above describes the pre-run state. No worker, clean screen, or larger factorial has run. Matching manually maintained prose automatically remains the target.


## Second DEV attempt and research

Attempt02 kept the same data/model/settings and added reviewed semantic guidance. It also failed complete maintenance:0/48views and0/2trajectories, with partial useful content credited by independent Astra. All16calls completed;615.55seconds including successful cleanup. [Preserved result](../quick-checks/maintenance-dev-02/RESULTS.md).

Two user-authorized research agents examined primary protocol and memory-system sources. Their synthesis recommends a small diagnostic separating plain-language rule extraction from transaction handling, keeping automated prose as a valid candidate. [Research brief](research/research-brief.md). No third maintenance attempt or diagnostic inference has run. Exact diagnostic prompts/registration still need preparation.
