# Source replay project data, schema 1 (prospective)

One JSON object per independently Kimi-authored project. No prose outside JSON.
No old examples or model responses are authoring inputs. Exact keys below;
reject extra keys, duplicate IDs, nonfinite numbers and invalid types.

Top level: schema_version (1), author ("kimi-k3:cloud"), lineage (nonempty
description of fresh independent authorship; no fit or benchmark reuse), public,
private. Public/private are separate projections in the consumer; runtime
builders take public only. Never include private objects in serialized prompts.

public:
- project_id: fixed by the independent authoring request, e.g. replay-01.
- description: brief project purpose.
- initial_file: {path: "module.py", text: complete Python module}.
- rounds: exactly three objects {index, source_messages, request, target,
  public_checks}. index is 1,2,3 in order.

source_messages: exactly four {message_id, role, text} per round. role is "user".
request: {message_id, role: "user", text}. IDs are unique m01 through m15 in
conversation order; four source messages then one request per round. Each text
is nonempty and at most 640 UTF-8 bytes. Array order defines chronology.
target: {path: "module.py", symbol: existing top-level function name}.
At least one target is revisited. Do not include assistant/tool transcripts.

Initial module contains only ordinary synchronous pure Python functions, with
one positional argument each; optional module docstring is allowed. No imports,
file/network access, decorators, nesting, annotations or top-level computation.
The existing action/sandbox restrictions remain authoritative. At most 65536
UTF-8 bytes for initial module, each replacement function and each evolving
module. References should comfortably fit the fixed 1024-token worker allowance;
preflight measures native encoding with at least 128 output tokens of headroom.
Helpers may call one another; target names and non-target code must survive edits.

public_checks: list of check objects first introduced at this round. Checks do
not require future functions to be implemented. Public checks are visible to
workers when introduced; all active public checks accompany later work.
The runtime projection contains only check_id, symbol, input, expected_values.
All other check fields are controller/audit metadata, never model-visible or
included in public tool feedback. In particular, future interval endpoints and
author-written source rationales must not leak through the public projection.
The reused sandbox receives those four executable fields plus internal rule_ids=[];
this is a compatibility adapter, not an authored obligation list.

private: {rounds, obsolete_mutant}.
private.rounds: exactly three {index, reference_patch, checks} objects.
reference_patch is one complete replacement function for the corresponding
public target. Sequential reference application must pass all active public and
private checks at every round via the actual worker consumer/sandbox.
checks are hidden cases first introduced at that round.
obsolete_mutant: {source, failing_check_id}; source replaces the final target in
the reference final workspace, compiles and is accepted by the action consumer,
but incorrectly preserves a retired rule. It must fail the named private
retirement check while the correct final reference passes it. This is a
counterexample to test vacuity, not a fitted worker or a gold source selection.

Every public/private check has exact fields:
{check_id, symbol, input, expected_values, active_from_round,
 active_through_round, source_ids, behavior, rationale}.
check_id is globally unique within a project. symbol is an existing function.
input and every expected_values element are finite JSON values. expected_values
is a nonempty list of all accepted outputs for that case, compared using the
existing strict JSON equality. No implementation-string/style assertions.
active_from_round equals its introduction index; active_through_round is null
(through round 3) or an integer from active_from_round through 3, inclusive.
source_ids are nonempty unique source/request IDs visible at introduction.
behavior is "functionality", "retained", or "retirement". rationale explains
why these sources require or permit the accepted behavior for this input.
An initial functionality check remaining active becomes retained coverage on
later rounds; coverage is derived from introduction and current round as well
as the tag. Tags alone do not prove a retained rule or a retirement was tested.

Each round introduces at least two private cases, with at least one new
functionality case. Each round has at least two active private cases for retained
behavior (round 1 may derive these from the starting module's specified behavior
and initial source instructions). Rounds 2 and 3 have at least two active private
retirement cases. Across each project's three rounds, include genuine unseen
inputs, conditional interactions and boundary cases. A case changing expected
behavior has a new check ID and interval. Conflicting active expected outputs
for the same (symbol,input) are invalid. Independent source review must check
whether a check is justified, whether a permitted choice is incorrectly forced,
and whether an allegedly retired condition actually ceased to apply.

No manual recap, oracle obligation list, effective-rule label, gold selected ID,
model answer or benchmark field exists. The preflight receipt binds exact public,
private, reference execution, mutant failure and source-review hashes. It grants
no post-exposure repair authority.

## Existing input calling convention, explicit for this new registration

For every check the executable call is the named function(check["input"]): the
whole JSON value in input is passed as the single positional argument, unchanged.
The runner does not unpack an argument array, coerce the value, add a wrapper or
remove a wrapper. Construct input as the value the function itself expects.
This describes the existing consumer and does not change its behavior.
