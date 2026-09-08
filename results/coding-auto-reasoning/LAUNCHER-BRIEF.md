# Sol xhigh: thin owned launcher for the automatic reasoning pilot

Fit-on none; DEV-on two wholly new Kimi/Ollama projects; evaluated-on none.
CPU implementation only; never launch Docker, load a model or execute a semantic
bank as part of this coding task. Read accepted DESIGN.md, RESOURCE-PLAN.md,
RUNTIME-BRIEF.md and latest ledger state. Root owns artifacts and launch decisions.

Allowlist:
- tools/run_coding_auto_reasoning.py
- tests/test_run_coding_auto_reasoning.py

Implement the smallest thin launcher around unchanged
tools.run_coding_competence.run_lifecycle and its process/deadline/ownership
helpers. Reuse the tested reasoning smoke's exact container command generator
unchanged; it already provides the pinned image, local mount, qwen3 reasoning,
Hermes named tools and 32768 context. No copied lifecycle framework and no edits
to frozen predecessor modules. No mutable global monkeypatching to repurpose
their main functions. Coordinate the new driver's exact CLI and preview keys
with /root/coding_focus_impl before consuming them; write down that contract in
your handoff. Only the two named files are yours.

Fixed result base results/coding-auto-reasoning, driver
scripts/coding_auto_reasoning.py, default dry-run, explicit --execute for actual
launch. New run directory must be a previously absent run-* direct child of that
base. Reservation 3000 seconds total, startup 600 and cleanup reserve 60; the
prior audited smoke's actual 516.914703271992 seconds also counts toward the
existing 3600 candidate ceiling. Bind the smoke lifecycle/audit evidence and
recompute that combined charge before permitting execution. No extra calls or
pre-run inference, fallback model, cap, deadline extension or new budget.

Validate both final reviewed one-project input receipts, zero-call CPU preflight
and preview PASS, six reference edit/focus capacities (1021 final allowance,
128 spare), fixed18max generations/2048total/1024thinking/32768context/settings,
provisional known-cold context fit, and exact source/data/tokenizer metadata
hashes. Each final input is a separate root-owned author-NN/reviewed.json; no
selection from multiple alternate banks. Do not interpret unknown future history
envelopes as a universal capacity proof. Review artifact hash presence/binding is
mechanical; root verifies actual review acceptance before freeze. No brittle
parsing of prose scores, and no claim that this launcher decides semantic truth.

Final bound paths include the new client/driver/launcher and all three targeted
test files; reused transport/data/consumer/sandbox/lifecycle/tokenizer sources;
accepted design/data contract, resource plan, preview, reviewed data and review
reports. Root will provide final reports when stable. Reject dirty/untracked
bound files and stale preview hashes. Preserve current trunk manifest size/mtime
plus metadata qualification without claiming to rehash all weights.

Recheck flags, wrapper lock, containers, GPU occupancy, local image availability,
exact Git head and frozen inputs before launch. Register every process this
launcher creates through existing helpers. Preserve PID/command/freeze records
and hard lifecycle receipts. Hold the experiment lock and its own exclusive flag
only for the owned run; do not treat a native coder as its own wrapper. Clean up
only newly created resources. A failed attempt to reserve an existing run must
not overwrite any old file, including lifecycle.json. A failure before a directory
is created cannot write receipts into someone else's directory.

Write targeted tests first through actual main/consumer paths with synthetic
artifacts and mocked process interfaces: dry-run does not launch; stale bindings
and combined-budget violation reject; prior-run sentinel survives failed reserve;
exact driver/container plan and remaining-deadline forwarding use unchanged
run_lifecycle; only owned flag is removed on failure. No full pytest suite or
new daemon. Acceptance: .venv/bin/pytest -q tests/test_run_coding_auto_reasoning.py,
Ruff on the two files, help and dry-run smoke by absolute path from /tmp.
Stop when stable; explicit two-path commit and source hashes/test/CLI handoff to
root. Final independent Astra readiness review remains necessary before --execute.
