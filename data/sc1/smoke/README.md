# Disposable SC1 harness fixtures

These eight fictional sources were written for this implementation by an informed
harness session. They are not isolated production authoring and must never be
reused for setup or final. The recorded author/factor draws exercise the sampler;
they do not claim those providers authored these fixtures. Independent semantic
review, author construction effort, and model determinism are not certified here.

CPU commands:

```
uv run pytest -q tests/test_sc1.py tests/test_eval_data_separation.py tests/test_sealed_guard.py tests/test_no_side_effect_imports.py
uv run python scripts/sc1.py validate data/sc1/smoke
uv run python scripts/sc1.py smoke
```

`smoke` validates all eight sources, writes the expanded episodes and validation
report, exports the original source/API grammar and exact power enumeration, and
writes an executable manifest. It loads a tokenizer and hashes checkpoint bytes;
it never instantiates a model. Code must be committed before manifest creation.
`manifest_id` hashes canonical manifest content excluding that field; the file's
ordinary SHA-256 additionally covers the field and trailing newline.

The original grammar is exported as `grammar.json` from `SCHEMA` in
`src/stencil/sc1_episodes.py`. Record operations are create/update/delete/get/list;
editing supports object-only JSON-pointer patches or complete raw text. Patch
arrays are bounded to 40 operations and 40 output lines; text has 40 output lines.
References use the same parser, executor, complete-result checker and explicit
protected predicates as generated outputs. Source-provided attack witnesses are
compiled with deterministic, ordered substitutes for inapplicable slots.

The renderer writes Qwen message delimiters directly and derives token boundaries
from one encoding's offsets. Tool results retain semantic tool roles even inside
the native user wrapper. SC1's bare JSON call requirement is stated in the system
block; native XML function-call framing is not accepted by this grammar. Final
message indices refer to zero-based public history messages, excluding the system
prefix. Irrelevant filler expands one explicitly designated non-evidence message
to the fixed 4,608-token target; it cannot move causal events or relabel age.

For future production use, `validate BANK --freeze --stage1 FILE
--executable-freeze FILE --out DIR` creates a manifest after all 288 sources and
independent source reviews exist. Exact served author versions/settings and
retained transcript hashes are mandatory. Pairwise review keys use source IDs in
lexical order. Signatures bind `source_spec_hash` (content excluding review and
provenance metadata); the manifest separately hashes full source bytes, avoiding
circular signatures between reviews. The `commission` command exports a neutral
request envelope for an external fresh-session provider transport; it makes no
provider requests and cannot attest to provider-side context isolation.

`setup` requires the frozen production manifest and a separate model-determinism
certificate (two fresh processes, two smoke sources, two arms, eight outputs).
It generates only full/evicted outputs and measures clf/rule CPU paths. Its
certificate must be committed before `final` or `analyze` can read final outcomes.
`final` writes each arm durably, then its pair, and publishes a complete seal only
at 256 pairs. `analyze` refuses incomplete, changed, ungated or over-budget runs.

An external interruption is not an ordinary timeout or a failed response. Resume
uses `--interruption-evidence FILE`: allocation_id, infrastructure reason
(host_loss/process_loss/device_loss/resource_loss), total elapsed allocation,
external evidence, and an attempts array with episode_id/arm/attempt_id/elapsed.
Previously accounted time cannot decrease; completed arm bytes cannot change.
Unknown harness exceptions invalidate the bank. No locks are waited on and no
process is signalled. The allocation ledger charges initialization, selector work,
checking, persistence and idle time while the allocation is held.

`--trunk 4b` is the default; `--trunk 1.7b` selects the separately hashed deployment.
Neither production source commissioning nor model execution is authorized by this
CPU implementation handoff. Stage 1 is still prospective text; this directory is
an executable-freeze candidate, not a registration or a production setup pass.
