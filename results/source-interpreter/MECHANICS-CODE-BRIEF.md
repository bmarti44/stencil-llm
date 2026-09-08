# Sol xhigh implementation brief — training mechanics

Implementation authority begins with root's acceptance handoff binding the
canonical review and specification hash. Native agent, no wrapper.

Fit-on: only the already accepted FIT row specified in MECHANICS.md.
Development-on/evaluated-on: none. CPU tests use synthetic tensors/temporary
fixtures, never an evaluation bank or recorded response. The mechanics adapter
is disposable and cannot initialize later full FIT training.

Read the latest appended STATE in plan/LEDGER.md, MECHANICS.md and its accepted
mechanics-review-astra.md round. Implement the exact accepted four-step local
measurement and owning timeout supervisor with minimal code. No trainer
framework, model server, package change or semantic heuristic. No GPU/model
weight loading, real training run or data authoring during implementation.

Allowlist:
- scripts/source_interpreter_mechanics.py
- tests/test_source_interpreter_mechanics.py

Use one main-guarded script with explicit dry-run/default behavior and an
explicit execution option; an internal child mode may share that script.
Heavy imports are lazy. Expose small functions only where needed by meaningful
consumer tests. Use absolute paths in subprocess launches. The child loads
one original base and performs the measured work; the supervisor owns the
whole-job deadline, PID registration, exclusivity and durable terminal receipt.
The existing frozen launchers can be read for ownership/flag conventions;
do not import an old experiment or reproduce its unrelated validation stack.

Consume the frozen preview row directly after checking its exact binding to
the accepted source/target and original tokenizer. Preserve the accepted helper;
reuse its pure operations if appropriate without rerunning the full preview.
Input/spec/code/package/base hashes, exact settings, work stage and terminal
status must be recorded. Do not silently retokenize into a changed row.

Implement every numerical, frozen-parameter, resource and save/reload check in
the accepted mechanics spec. Save standard FP32 PEFT weights, byte-part archive,
reconstruct and reload a temporary adapter on the same trunk, compare exact
state and run the one registered post-reload forward. Report missing/unexpected
adapter keys correctly; legitimate base-key reporting by PEFT is not an adapter
corruption. Never claim all gradients nonzero or bitwise preservation without
measuring the exact claim. Ordinary runtime cache changes are not weight changes.
Use the installed model's native causal-loss shift; do not pre-shift labels.
Activate reload with `set_adapter('roundtrip', inference_mode=True)`, then
evaluation mode and no gradients. Root independently verified these installed
APIs in PEFT peft_model.py:1591 and transformers loss/loss_utils.py:49.

Start and per-stage/per-step evidence must survive a forced child termination;
terminal supervisor evidence must preserve partial work and incomplete status.
No automatic retry or settings fallback. Existing output evidence is immutable:
refuse an occupied run directory rather than overwrite it. Clear this job's
RUNNING.flag only after confirmed child exit. Dry-run loads no model, creates
no CUDA context and starts no training job.

Write targeted tests first against the actual consuming paths:
- Exact synthetic target/EOS causal-loss positions; reject all-masked, wrong
  boundary, wrong input binding and shortened rows before model loading.
- Frozen original parameters and optimizer membership; fail detached/absent
  gradients and no updates, while allowing a zero individual LoRA-factor
  gradient when the aggregate/update is valid. Use tiny CPU tensors/modules.
- Standard adapter-state comparison catches changed values, dtype and keys;
  byte archive reconstruction detects corruption and preserves exact bytes.
- Supervisor happy exit, failing child and forced timeout with a tiny temporary
  child: retain durable partial records, count warm-up, reject incomplete pass,
  stop only the child it owns, preserve foreign flags and clear its own only
  after exit. Inject short bounds in tests, not production settings.
- Import and dry-run start no weights/CUDA/training; all registered receipt
  fields are exercised with small synthetic fixtures before real execution.

Use tests that would fail on the actual error; avoid extensive duplicate schema
tests or implementation mirrors. Do not run the full suite or unchanged helper
tests. Acceptance: `.venv/bin/pytest -q tests/test_source_interpreter_mechanics.py`,
Ruff check/format on these two files, dry-run smoke, import check and
`git diff --check`. Commit only explicit allowlisted paths. Return exact commit,
hashes, commands/results, red-first evidence and unresolved implementation
decisions. Root records handoff in the ledger and obtains independent Astra
implementation review before any real GPU launch.
