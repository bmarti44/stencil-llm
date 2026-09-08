# Root evidence and provenance

Accessed 2026-09-08. Official web pages have no visible update date. This is
provider/document evidence, not a runtime capability probe or causal diagnosis.

- Ollama, [Structured Outputs](https://docs.ollama.com/capabilities/structured-outputs):
  explicitly says cloud currently does not support structured outputs. Generic
  JSON/schema examples on the same page cannot establish a cloud guarantee.
  Confidence high for documented limitation; exact cloud implementation untested.
- Ollama, [Generate a response](https://docs.ollama.com/api/generate): generic API
  accepts format=json or a schema, stream, think and options; response contains
  text separately from done/done_reason. Endpoint syntax does not establish that
  all backends implement it. Confidence high for published API shape.
- Ollama, [Cloud](https://docs.ollama.com/cloud): local tools can access models
  offloaded to Ollama's cloud. Its broad same-capabilities wording is qualified
  by the specific structured-output page. No new account/endpoint/model is needed
  or proposed. Confidence high; already-used local service is archived evidence.
- Ollama, [Thinking](https://docs.ollama.com/capabilities/thinking): thinking and
  final content are distinct fields; support and controls are model-dependent.
  No exact Kimi K3 output ceiling or support for disabling thinking is inferred.
- Ollama, [Streaming](https://docs.ollama.com/api/streaming): stream=false returns
  one application/json envelope instead of newline-delimited response chunks.
  Inference: this transport choice does not guarantee valid JSON inside response,
  or correct source requirements/tests. No streaming rewrite is justified here.

Local read-only inspection of four original request.json and response.json files
under results/source-replay/project-authoring/author-00 through author-03:

| Author | Prompt characters | Final-content characters | Thinking characters | Service eval_count |
| --- | ---: | ---: | ---: | ---: |
| 00 | 8967 | 20546 | 72666 | 24954 |
| 01 | 8969 | 5396 | 53573 | 16776 |
| 02 | 8967 | 27674 | 99581 | 32113 |
| 03 | 8979 | 16812 | 41931 | 15365 |

Every request has exactly model, prompt, stream=false, think=true; no format or
options override. Every envelope has done=true and done_reason=stop. Character
counts use Python len on decoded strings, not bytes or tokenizer estimates.
The service eval_count is retained as reported, not attributed solely to visible
final content. Existing PREPARATION-RESULTS.md establishes two invalid inner JSON
objects and one incomplete project despite these successful envelopes. Four
observations do not identify output length, thinking mode or a provider cap as
the cause. The helper preserves raw bytes and then parses the response string;
HTTP completion and inner project validity are distinct consuming steps.

Decision implication (engineering inference): do not depend on cloud schema
enforcement, change providers, strip reasoning into output, append missing braces,
or rerun the stopped bank. Consider smaller immutable authoring units assembled
mechanically, with actual validation before spending on dependent stages. This
may reduce preparation burden; reliability must be measured prospectively.

Search record: direct official structured-outputs/generate opens, unsuccessful
guessed capabilities/cloud URL, one discovery search locating /cloud, then direct
cloud/thinking/streaming opens. Search returned community cap claims incidentally;
they were not opened or used. No benchmark data or model outputs acquired.
Root provider discovery stops: another generic provider search would not change
the unsupported-schema decision or establish semantic authoring reliability.
