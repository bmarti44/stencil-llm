# Original-source replay: implementation feasibility inventory

2026-09-08. Static inspection at `f24cf731`; no code was imported or run, no
test or model/server/tokenizer/network path was exercised, and no bank, response
or label was opened. The accepted research report/review hashes are respectively
`a7e7cb46c51734ad3600fbad78714fe2c02aa62b8a592bf9ee94b979ec7ae220`
and `9f8a31a005eab372dcaa38e5ae02717c78fdcc530c607b798af501081ecbfa6a`.
All implementation statements below are source-level inferences, not current
behavior qualifications.

## Smallest reuse boundary

| Existing surface | Reuse | Boundary |
| --- | --- | --- |
| `scripts/coding_competence_run.py::NativeToolClient` | Use unchanged for all three workers. Its static payload is the original Qwen3-30B-A3B nonthinking, temperature-0, seed-20260908, forced `replace_function` path with a 1,024-token output allowance and 32,768-token context check. `_json_bytes`, request/response receipts, render-before-generation, token-ID accounting and `TechnicalError` categories are also suitable. | Do not reuse `run`, `_planned_records`, or `build_issued_messages`: they require four projects, three rounds and 36 calls, and the builder always reads private `manual_recap`. |
| `scripts/coding_competence_dev.py::consume_action` and `scripts/coding_worker_dev.py::{splice_function,run_checks,_fresh_execute}` | Use the exact function replacement and check path for a small single-module Python screen; retain its exact submitted bytes and 65,536-byte source/module bounds. | `active_check_sets` and `coding_competence_run.py::_private_checks` accumulate stable functional checks but retain only the current round's obligation checks. They cannot define this screen's still-active coverage. |
| `src/stencil/focus/slab_sandbox.py` | Reuse through `run_checks`: a fresh isolated CPython child per check is the existing narrow execution primitive. | This does not provide persistent state itself. The controller must own each arm's evolving module and snapshot it before/after every attempt. |
| `results/coding-competence/DATA-CONTRACT.md` | Reuse the public shapes `initial_file`, `{message_id,role,text}`, request, target and executable check. | Its mandatory complete `manual_recap`, oracle rule lists, two mutants per round, exactly four projects/three rounds and three distinct future stubs are avoidable semantic-gold authoring/review burdens here. They are unused by an IDs-only utility test and should not be copied into its runtime contract. A reference implementation remains necessary for preflight, but a perfect focus target does not. |
| `src/stencil/focus/native_reasoning_tool.py` | Reuse only its design precedent for parameterized schemas and strict render/usage receipts. | `NativeRequestSpec` accepts only `replace_function` or `record_focus`; `record_focus` requires generated obligation prose; its client requires a positive reasoning budget, loads reasoning-token helpers, and always sets `enable_thinking:true`. Extending or disguising that frozen semantic consumer would test the wrong intervention. |

The old worker's accepted native contract remains the compatibility basis, not
a new qualification. Its existing main guard makes future reuse possible without
editing it. The prospective runner must also be main-guarded.

## Narrow new contract and interface

Add a source-replay-specific public/private loader rather than weakening the old
exact validator. The public runtime projection needs only a project ID, initial
module, ordered rounds, original source messages, current request, target and
public checks. Store every original message once as UTF-8 text with a unique ID,
role and sequence index. Put hidden checks and per-round reference patches in a
separate private/preflight object. Do not author manual recaps, effective-rule
lists, inactive-rule labels or negative controls.

Each hidden check should carry `check_id`, exact executable case fields,
`active_from_round`, inclusive `active_through_round` (or null), source IDs and
one coverage tag (`new`, `still_active`, or `retirement`). At round `r`, execute
every check whose interval contains `r`; reject a project if the active set lacks
all three required coverage classes where they are applicable. Version a check
when its expected output changes. This small interval contract makes retention
and retirement explicit without an oracle prose layer. Independently reviewed
reference patches must pass every active set in sequence before freezing, but
their bytes and all hidden cases must be absent from worker and selector inputs.
The run package can bind only their preflight receipt hashes.

Add one narrow nonthinking client, for example
`src/stencil/focus/native_source_selector.py::NativeSourceSelectorClient`:

```text
select(eligible_messages, current_request, max_ids) -> tuple[message_id, ...]
tool select_source_ids({source_ids: unique array of enum(eligible IDs), maxItems=max_ids})
```

Its request contains only immutable public original messages strictly preceding
the current request, with IDs/roles/order, plus that request as the relevance
query. It has no persistent generated state. It uses the original 30B server,
nonthinking named-tool mode, an independently frozen small output cap, and the
same authoritative render/token-ID/usage receipt checks as the worker. Validate
the decoded object again: exactly `source_ids`, no unknown or duplicate ID, and
within the frozen whole-message evidence allowance. An empty selection may be
valid only if the prospective specification explicitly permits it.

A deterministic renderer maps IDs back to the public source table, sorts by
recorded source order, and inserts one ephemeral historical-evidence block into
the automatic arm's current work request. Copy each complete text string without
normalization or truncation and carry its ID and original role as evidence
metadata; record source/render UTF-8 hashes and assert round-trip equality. The
recent arm chooses the most recent whole eligible messages under the identical
allowance and uses the same renderer. The ordinary arm has no evidence block.
All arms otherwise receive byte-identical task/module/public-check envelopes.
The specification must decide whole-message overflow before exposure; runtime
must never trim a message or silently drop IDs to fit.

The minimum production footprint is one small public/private validator and
renderer (`src/stencil/source_replay.py`), the narrow selector client above, and
one main-guarded coordinator (`scripts/source_replay_run.py`) that reuses the
unchanged worker client/consumer/sandbox. Focused CPU tests should cover contract
rejection, byte/role/order round trips, private-key exclusion, arm aliasing,
active-check intervals, selector schema/errors, and partial-record accounting.
No 4B model, trained adapter, semantic-control consumer, index or framework is
needed.

## Paired state, visibility and outcomes

Key histories, module states, tool-call-ID sets and output directories by
`(project_id, arm)` from initialization. Deep-copy the same initial module into
each arm; never copy a later workspace, generated assistant call, tool result,
public result or retry from another arm. Persist each arm's authentic original
source/request history and its own actual assistant/tool feedback. Selector
output is an ephemeral intervention record, not worker-authored history and not
a replacement for the selected originals. Use disjoint paths such as
`projects/<project>/<arm>/{calls,requests,workspaces}` and bind every state/history
transition by hash.

Message builders accept only the public projection. The selector cannot receive
workspace contents, public execution results, hidden checks, references or
another arm's trajectory. The worker may receive cumulative public results from
its own attempts; hidden results never affect prompts, stopping or retries.

Keep these outcome classes separate:

- selector transport/render/schema/token-accounting/malformed/cap failure, or
  worker transport/render/token-accounting/context/`finish_reason:length`
  failure: technical `INCOMPLETE`; preserve partial records, do not substitute
  recency/empty IDs, retry the selector, change a cap, or silently remove a pair;
- well-formed selector IDs whose complete evidence exceeds the frozen allowance:
  selector capacity failure (prefer rejecting such projects at preflight);
- well-formed worker tool call rejected by `consume_action`: authentic failed
  attempt eligible for ordinary public feedback/retry within `A`;
- applied but behaviorally wrong source: authentic outcome and retry within
  `A`; exhaustion is a completed failed request, not a technical failure;
- whole deadline, planned-call cap or cleanup interruption: `INCOMPLETE` with
  remaining work explicitly unattempted. A valid `stop` response using exactly
  its allowance is not capped merely because its token count equals the limit.

## Calls and planning cost

For `P` projects, `R` rounds and at most `A` worker attempts, planned worker
generations are at most `3PRA`. There is one selector generation per automatic
arm request, not per worker attempt, so selector generations are `PR` and total
generations are

```text
G_max = 3PRA + PR = PR(3A + 1).
```

With one authoritative render before each generation, render requests also
equal `G_max`, and maximum HTTP posts are `2G_max`. If `a[p,r,h] <= A` is the
realized attempt count, actual worker generations are `sum(a)` and actual total
generations are `PR + sum(a)` for a complete schedule. With `Cpub[p,r]` visible
cumulative checks and `Cactive[p,r]` hidden checks active at that round, a coarse
all-patches-applied runtime maximum is
`3 * sum_p,r(A*Cpub[p,r] + Cactive[p,r])` sandbox executions, excluding the
separate reference preflight.

Record selector and worker prompt/completion tokens separately. Exact total
tokens are the sums over the `PR` selector calls and every realized worker
attempt; no fixed per-call token assumption belongs in the freeze. The historical
original-30B competence artifact reports 18 generations plus 18 renders, 95,528
prompt tokens, 5,777 completion tokens, 394 sandbox checks and 816.137 seconds
including startup/cleanup. A deliberately coarse historical-ratio estimate is

```text
prompt tokens ~= 5,307.11 * G
completion tokens ~= 320.94 * G
whole-reservation seconds ~= 45.341 * G.
```

Those ratios mix worker generation, rendering, old check density, startup and
cleanup; selector outputs should be shorter and the new histories/check schedule
will differ. They are planning inputs only, neither a current measurement nor a
runtime bound or model-success claim. The required separately scoped local
qualification must measure the frozen selector/worker configuration before the
one-GPU-hour screen is registered.
