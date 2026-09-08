# Sol xhigh CPU implementation brief

Fit-on none; all six prospective Kimi conversation families are assigned FIT
before authoring. No DEV/withheld generation, evaluation, old cases or adapters.
Read PREP.md and the latest ledger. Astra is reviewing the prep specification;
root will forward any changes. CPU work only: no weights/model load, GPU, HTTP,
authoring, package installation or full pytest suite. No wrappers.

Allowlist only:
- src/stencil/focus/source_interpreter.py
- tests/test_source_interpreter.py

Implement a pure loader/validator, source-only prompt builder, exact nonthinking
prefix/target serializer, right-padding collation and CPU preview function.
Root will call preview through a short Python invocation; no new CLI is needed.
Lazy local-only AutoTokenizer loading is allowed; no AutoModel or training.
Never import old scripts with top-level execution or edit frozen modules. Reuse
record_focus structural validation/schema without invoking its reasoning client.
No prose regex or semantic applicability heuristics.

Validate the full document/family/split set before expanding prefixes. Reject
unknown fields, wrong types, duplicate identities, misplaced checkpoints and
future citations. Preserve original Unicode text, roles, IDs, order and handles.
The final query must anchor the last source message; reject an unqueried tail.
An empty obligations list is valid. The shared schema permits fit/dev/withheld
and prohibits a family crossing splits. Calibration preview requires six FIT
files, three queries each, and all 18 rows. No silent subset or truncation.
Structural validation cannot establish semantic coverage, authority or family
independence. Do not inspect real authored data during implementation.

Fix one generic system prompt before real packet access. Ask for all current
standing constraints and conventions, preserving scope, modality, permissions,
exceptions, changes and retirement under authentic user authority. The current
algorithm need not be repeated. Require exactly the record_focus JSON object,
with no tool wrapper or worked example. One user message contains the current
task handle and full authentic JSON prefix through the query. Targets and future
messages never enter input. Use enable_thinking=False and
add_generation_prompt=True. Canonical target JSON uses unescaped Unicode,
sorted keys and compact separators, followed by exactly one EOS token.
Reject reserved control tokens in natural source/target text through tokenizer
special-token IDs, not semantic regex. Never normalize away source text to pass.

Document a prefix-ID/target-ID construction consistent with later local HF
causal generation. Do not assume whole-concatenation tokenization equals separate
segments; verify actual tokenizer boundary behavior and exact decoding. Labels
mask every prefix/padding position with -100 and supervise all target/EOS tokens.
Padding has attention zero. Reject empty supervision, wrong EOS, shifted loss
positions or truncation. CPU receipts retain all rows, exact IDs/masks or loss
positions, lengths and hashes. Bind source files, prompt/schema/template/tokenizer,
code and actual interpreter/package metadata. Report actual prefix/target/full
length distributions, including maxima by conversation band. Select no future
GPU/output cap or training recipe.

Write meaningful tests first through the actual loader/preview/collation paths:
- Family crossing splits, duplicate IDs, future citations and unqueried tails fail.
- Original Unicode/roles/order survive; targets and future text are absent from input.
- Empty focus is accepted.
- The actual local tokenizer produces the fixed nonthinking prefix, exact decoded
  JSON and one EOS; first target and final EOS receive loss, all prefix/padding do not.
- Reserved-token source text fails; variable lengths receive correct right padding.
- Synthetic six-document preview produces every one of the 18 expected rows.

Use synthetic labels only for format tests; they never become FIT material.
Expected values should be independently constructed rather than calling the
same implementation helper. Test actual token positions and decoded content.
No model weights or authored packet execution in tests.

Acceptance: .venv/bin/pytest -q tests/test_source_interpreter.py; Ruff check and
format on the two files; import has no execution; git diff --check. Commit only
the explicit allowlist. Hand off source/test hashes, exact test results and
red-first evidence, plus any boundary decision. Root owns real data, independent
Astra review, CPU preview and later resource/launch decisions. No trainer,
launcher or model server is needed for this work unit.
