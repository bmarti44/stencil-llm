Author one wholly fresh, tiny mechanical coding fixture. You are Kimi K3,
accessed through the existing Ollama service. Invent its content independently;
do not use a benchmark, remembered evaluation example, previous project,
conversation or model response. This fixture only qualifies a native tool
interface; it is not a performance benchmark or training data.

Return exactly one JSON object, with no Markdown fence or surrounding prose:

{
  "schema_version": 1,
  "author": "kimi-k3:cloud",
  "lineage": "your concise truthful statement of fresh independent authorship",
  "initial_file": {"path": "module.py", "text": "complete module"},
  "source_messages": [{"message_id": "m01", "role": "user", "text": "one instruction"}],
  "request": {"message_id": "m02", "role": "user", "text": "one direct coding request"},
  "target": {"path": "module.py", "symbol": "the function name"},
  "reference_patch": "one complete replacement function",
  "checks": [{"check_id": "your unique ID", "symbol": "the function name", "input": "a JSON value", "expected_values": ["the permitted JSON output"]}]
}

Replace all descriptive placeholders with your own fixture. Include exactly
one original instruction and one direct request, with nonempty message texts
no longer than 640 UTF-8 bytes each. Make the initial module exactly one simple
synchronous Python function of one positional argument. The request asks for a
small straightforward change. The original instruction supplies one relevant
requirement. Avoid ambiguities, conflicting instructions or changing-rule puzzles.

Include at least two distinct executable cases with exact expected outputs
grounded in the messages. Inputs and outputs must be finite JSON values.
reference_patch is one complete replacement function, beginning with def at
byte zero and using LF newlines. No imports, annotations, decorators, nested
definitions, classes, external calls, file/network access, Markdown, globals,
top-level computation or extra keys. Keep the function under 15 lines and the
reference comfortably under 200 tokens. Use only simple built-in operations.
Check your arithmetic and ensure the reference produces all expected outputs.

The selector and worker will never receive the reference or expected test
results. Do not add a desired source-ID answer, manual recap, rule register,
assistant transcript or explanation outside the exact JSON object.
