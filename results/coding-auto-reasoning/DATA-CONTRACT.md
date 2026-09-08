# Fresh automatic-reasoning DEV authoring contract, version 1

Read [DESIGN.md](DESIGN.md) for the prospective automatic pilot. Author semantics and all code with Kimi K3 via
Ollama, not with the implementation or review agents. Each generation creates
one complete original project. Do not provide earlier bank prompts, cases,
outputs or failure-specific paraphrases to the author. Two accepted documents
form the bank; independent Astra review and executable preflight precede freezing.

Each JSON document has EXACT top-level keys:
`schema_version` (1), `split` ("dev"), `author` ({"name":"kimi", "model":"kimi-k3:cloud"}),
`lineage` ({"fit_on":"none", "development_on":"new original coding competence DEV", "evaluated_on":"none"}),
`public`, `private`.

`public` has exactly `episode_id`, `project`, `task_handles`, `initial_file`,
`initial_checks`, `rounds`. episode_id/project are nonempty strings; task_handles
is a nonempty unique string list. initial_file is {"path":safe basename ending
.py, "text":full module}. Include one or more functional initial helper(s) and
exactly three future target function stubs (each just `return None`). All
functions are synchronous with one positional argument. Use the existing safe
pure-Python subset; JSON only at callable boundaries. Each round targets a
DISTINCT stub and builds on actual prior functions. No imports, file/network
access, decorators, top-level execution or function nesting. Local comprehensions
and lambdas are allowed if the existing consumer permits them.

`public.rounds` is exactly three objects, indices 0,1,2. Each has exactly:
`index`, `source_messages`, `request`, `target`, `public_checks`.
source_messages is a list of {message_id,role,text}; roles are user or assistant.
request is {message_id,role:"user",task_handle,text}; target is {path,symbol}.
Message IDs are unique within the episode across all sources/requests. Only
actual user directions or explicit user adoption establish obligations; quotations
and assistant suggestions alone do not. Natural requests completely specify
behavior, including input rejection and all observable outputs. Each project
has meaningful dependent work, stable initial obligations, and a real scoped
change followed by use. Three steps need not cover the entire future interpreter
lifecycle; do not turn this into disconnected trivial functions.

`private` has exactly `rounds`, three objects with matching indices. Each has
exactly `index`, `manual_recap`, `oracle`, `reference_patch`, `functional_checks`,
`obligation_checks`, `negative_controls`. manual_recap is correct complete current
prose, including scope/modality/exceptions and permissions. oracle is
{effective_rules:[{rule_id,scope,strength,text,source_ids}],inactive_rule_ids:[...]};
scope is "global" or an existing task_handle; strength is required, prohibited,
permitted or optional. Source IDs cite visible genuine antecedents including
any necessary adoption/change. Rule IDs are unique identities within a project;
use consistent lifecycle identities. No fabricated source is allowed.

reference_patch is the complete target function source string, not a fence.
It must operate with previously applied references and actual initial helpers,
without redefining, repairing or bypassing dependencies. Reference code and
checks must implement exactly the natural source requirements, not unstated
conventions. Functional checks are stable under later permitted rule changes;
current obligation checks can change, and must not demand old behavior from
new edits or new behavior from untouched functions without explicit authority.

Every check object has exactly {check_id,symbol,input,expected_values,rule_ids}.
expected_values is a nonempty JSON list of permissible complete outputs, using
type-sensitive equality (true is not 1). input is the single JSON argument.
Initial/public/functional checks have empty rule_ids; obligation checks cite
current rule IDs. Check IDs are unique across the episode. At least two initial
helper checks; each round at least two public cases, two private functional
cases, and two private obligation cases. Include positive, rejection and boundary
coverage; a small case count is a minimum, not a adequacy claim. A permission
must allow all valid choices rather than force one style. No artificial alternative
is required when behavior is already uniquely specified.

Public checks are separately authored stable functionality examples whose full
outputs are invariant to the standing-rule distinctions under study. Empty
rule_ids and disjoint inputs alone do not establish that property. Choose
valid, unambiguous functional cases; keep rule-sensitive tie, formatting or
rejection cases private. If a convention changes every possible full output,
it cannot support this public-check interface unchanged; choose another
meaningful obligation, rather than leak its answer through feedback. All
private functional/obligation symbol+input pairs are disjoint from ALL public
initial/round cases; do not reveal hidden cases through public result messages.
Use independent edge combinations and direct-source review for private coverage,
not just duplicates with renamed IDs. Private functional and obligation checks
may share an input if they test the same specified full output consistently.

Exactly two negative_controls per round, one kind "functional" and one
"obligation"; each has exactly {control_id,kind,patch,expected_failing_check_ids}.
The patch is a valid complete replacement of the current target, based on the
correct current reference and changing one meaningful behavior. At least one
listed private check of the corresponding kind must actually reject it through
the same native-source consumer. The functional mutant changes an algorithmic requirement while preserving
the declared rule policy; full-output obligation checks may also fail because
they contain functional results, and that overlap must be recorded. Do not
require their full outputs to pass. The obligation mutant must preserve all
private stable functionality, including earlier cumulative checks. Do not use invalid syntax/stubs as negative controls. All IDs
are locally scoped by episode_id. No test/check result appears in source messages.

The loader must physically expose a public projection and an explicit current
manual reminder. No generic serialization of the full document enters the
model prompt. Preflight applies references and mutants using the future exact
action consumer, verifies cumulative/current check semantics and disjointness,
and records every result with hashes. Author review checks source semantics,
coverage, allowed-language validity and actual dependencies before any worker
inference. Parent mechanically assembles accepted JSON bytes, preserving raw
Kimi request/response provenance. Corrections return to Kimi with exact scope;
reviewers and coders do not silently author replacement semantics.

For this new bank, keep exactly the established per-document schema so the
unchanged loader can validate each project separately. The literal lineage
string is the existing schema category; these are wholly new automatic-reasoning
DEV projects, with their specific provenance in authoring-plan.json. Neither
manual_recap nor oracle reaches the automatic worker: both are private audit and
offline capacity references. Kimi authors them independently before model output.
The selector sees only original source messages/current request, never tests.
Use genuine scoped changes and nonauthoritative suggestions or quotations, with
complete natural source authority and scope. Public checks must not teach the
standing-rule answers. Preserve all earlier interface and dependency requirements.
