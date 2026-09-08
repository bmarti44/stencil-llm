# Fixed FIT runner — implementation brief

Specification accepted by Astra xhigh round1 at96/100 with zero findings.
FIT.md SHA256: f1f306e9ccac968013568dd6f0ed46a42d6df7297105c7a2531a83b7caa541a7.
Accepted review SHA256: a7b9309c7bb22b0ffb0002f6761251212e3f55275c19432e9983fb548bb3bb10.
This brief authorizes implementation and CPU checks only, never a model run. User roles: Sol xhigh implements; independent Astra xhigh
reviews; Kimi K3 via Ollama authors semantic data. This task authors no data.

Fit-on: only the eighteen exact accepted source-interpreter FIT preview rows,
from six families assigned FIT before Kimi authoring. Generation timing uses
only existing FIT row14. Development-on/evaluated-on: none. Never use spent DEV,
benchmarks, old responses, old adapters, or withheld sources. The actual fresh
semantic comparison and larger coding validation remain separate later work.

## Objective and allowed changes

Implement the accepted FIT.md faithfully with a small separate main-guarded
runner, reusing safe frozen mechanics primitives where they fit. Do not create a
training framework or modify frozen mechanics code/settings/artifacts. Allowed:

- scripts/source_interpreter_fit.py
- tests/test_source_interpreter_fit.py

No wrapper: use this native Sol session. No model/GPU/network/data authoring,
package change, preview regeneration, or actual training/generation in this
implementation task. Read-only CPU artifact qualification is allowed, provided
it never imports ML runtimes or reads weight payloads. Do not touch unrelated
untracked files. Root writes ledger/launch manifests and archives the handoff.

Read FIT.md, accepted preparation/mechanics reports, source_interpreter.py, and
scripts/source_interpreter_mechanics.py. The latter has a main guard and lazy
ML imports; safe import is permitted. Its pure row, numerical, optimizer-step,
archive, parameter identity and partial-accounting helpers can be reused
without changing globals or invoking its fixed four-update measurement body.
Use reliable imports for BOTH direct absolute-file execution from /tmp with
PYTHONPATH unset and test/module import. The earlier direct-file src.stencil
import defect was real; do not reintroduce it or mask it with test sys.path.

## Concrete contract

FIT.md governs exact recipe, row order, generation calls and deadline semantics.
Bind its accepted hash, current code/helper hashes, accepted inputs/preview,
original base asset receipt, environment/tokenizer and independent reviews in
receipts. Avoid a current-review hash cycle in code: root's prospective launch
manifest pins the final review; record dynamic hashes at qualification/runtime.
Reject changed bound inputs, unexpected run directories and foreign live flags.

Consume all eighteen exact rows and validate every row through the existing
actual source-binding/causal-label consumer. Execute the fixed54-row schedule,
with ordinal/epoch/row/conversation/query and label positions durably bound to
each update. No dropped rows, truncation, extra optimizer updates or checkpoint
selection. Reuse confirmed/unknown update accounting; retain the distinction
between optimizer completion and later validation failure. The first update
may retain the helper's warm-up label, but it is already part of54, never extra.

Use original model initialization/settings and standard FP32 save/byte archive/
reconstruct/reload equality checks from the qualified runner. The final adapter
is fresh for this full FIT run. Do not load the four-update mechanics adapter.
Do not add the mechanics runner's post-reload target loss forward: this recipe
requires reload equality followed by the two registered prefix-only calls.
Original parameter identity and before/after byte checks cover the whole job,
including generation. No claims of per-step original byte verification.

Use one original trunk, native HF/PEFT generation and exact prefix IDs. Each
call receives a fresh cache, no target/labels. Verify actual disabled/enabled
adapter state; record IDs, exact payload bytes/hash, resolved generation config,
all stop facts, strict full-document structural/citation validation, timing and
resources. Strict parsing does not compare to or repair from FIT gold. Output
syntax/cap failure does not erase the response or block the second fixed call;
technical exception/deadline stops the job. Never force grammar, extract an inner
JSON object, retry, or render another prompt. Whole-call synchronized monotonic
time suffices; no per-token instrumentation framework is needed.

One owning supervisor enforces stage and overall deadlines, with durable stage
intent/completion so a stuck child is still bounded. Register processes on launch
and stop/reap only owned descendants. Whole-process outer observation remains a
root launch responsibility and includes final publication/exit; record its
contract in the dry plan. Partial or timed-out output that cannot be recovered
is unknown/unavailable, never a fabricated zero. Preserve completed and pending
work, flag ownership and terminal status on every exit path. A missing output
or failed validation cannot become success because the exit code is zero.

Keep per-step and per-call records, not only aggregates. Standard checkpoint
files larger than10,000,000 bytes remain local; exact archive parts are at most
9,000,000 bytes. Avoid embedding complete repeated records in many summaries;
use explicit path/hash references where appropriate. Dry-plan and artifact-only
qualification modes must be non-executing and reject incompatible live flags.

## Meaningful targeted verification and handoff

Write consumer-level tests for new risks before implementation: complete exact
54-row schedule and wrong-row rejection; both actual generator invocations
receive prefix-only IDs and disabled/enabled modes with explicit kwargs; all
EOS/cap/deadline facts and strict trailing-text rejection retain raw output;
first returned-invalid response still permits second fixed call; exception or
deadline does not; hung-stage and final-publication accounting preserve unknown
work and stop/reap only owned child. Use CPU fakes for model execution and a
small owned dummy process where needed. Do not repeat the full frozen mechanics
test suite or write tests that merely echo configuration constants. Direct-file
artifact qualification must exercise the actual production consumer from /tmp.

Acceptance commands: .venv/bin/python -m pytest -q tests/test_source_interpreter_fit.py;
.venv/bin/ruff check scripts/source_interpreter_fit.py tests/test_source_interpreter_fit.py;
.venv/bin/ruff format --check on those two files; git diff --check. Use no shell
pipeline that hides a failing exit. Also confirm import/dry/qualification avoid
heavy ML imports and no existing artifact is modified. No full pytest suite.

Commit only the two allowlisted files after targeted checks. Handoff: actual
model/effort/native session, commit and both SHA256s, exact tests/results, direct
qualification/dry results, reused helpers, any unresolved concern and confirmation
of no model/GPU/data generation. Do not edit root ledger or reviewer files. Root
will request independent code review before freezing or launching one actual job.
