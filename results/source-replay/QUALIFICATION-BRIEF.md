# Two-call native source replay qualification (draft pending spec review)

This is the first implementation stage, not the four-project utility runner.
Fit-on none. Test fixture: one new Kimi K3/Ollama mechanical fixture, disjoint
from all previous data and future scored projects. No tuning or candidate
selection on its answers. Read SPEC.md for exact prompts, caps and evidence
semantics. Do not launch anything from this draft.

Implement the narrow IDs-only nonthinking client, original-source renderer,
and a main-guarded two-call qualification driver with targeted CPU tests first.
Reuse the worker NativeToolClient unchanged. Its perform method has hardcoded
worker schema/cap/tool validation, so do not call that method with disguised
selector inputs. Reuse transport/receipt helpers where their semantics fit;
keep a small explicit selector validator instead of a generic client framework.
Use the existing owned run_lifecycle with a new exact plan, rather than writing
another supervisor. No changes to frozen existing implementation files.

Fixture schema: {schema_version: 1, author: "kimi-k3:cloud", lineage,
initial_file: {path: "module.py", text},
source_messages: [{message_id: "m01", role: "user", text}],
request: {message_id: "m02", role: "user", text},
target: {path: "module.py", symbol}, reference_patch,
checks: [{check_id, symbol, input, expected_values}]}.
Each message is nonempty and at most 640 UTF-8 bytes. One source, one direct
request, one pure one-argument function and at least two simple JSON-valued test
cases. Reference patch follows the existing consume_action restrictions. This
fixture tests delivery and integration only; do not add changing-rule challenges.
Private reference/checks stay outside selector/worker prompts. CPU reference
consumer execution precedes native qualification; report behavior separately.

Qualification runs exactly one selector call (eligible m01; current query m02)
then one worker call with the original full history, original current module,
target, and ephemeral selected original-source evidence. No reference solution
or expected results go to either model. Preserve every raw request, authoritative
render and response, selector IDs, byte/order checks, actual worker action,
workspace before/after and CPU check results. No retries or hand-edited outputs.

Technical eligibility requires both calls delivered through the actual runtime
consumers without transport/schema/render/token/context/cap/action error, exact
source rendering, and clean timely shutdown. Worker hidden-check success is a
separate observation; it is not a source-selection utility result. A fixture
source/test defect stops preparation, rather than repairing it after answers.

Whole GPU reservation 600 seconds including startup and cleanup; retain a
60-second cleanup reserve and source-replay SPEC call limits. Persist partial
records and terminal status on failure. The planned screen remains 3000 seconds,
so total reservations are at most 3600. Freeze code/configuration/fixture/review
hashes and exact command before launch. Existing local assets only. Native CPU
tokenizer validation is allowed in actual preflight after implementation review;
no packages/weights/server/GPU loading during implementation/tests.

Root owns the prospective spec, exact authoring request and launch decision.
Sol xhigh owns code/tests, Astra xhigh reviews author-disjoint. An accepted
technical qualification permits authoring the four prospective projects and
implementing the small paired consumer; it never constitutes scientific proof.
