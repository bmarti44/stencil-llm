# Admission v1 — check 44b

Message-level contextual sentence tagger from base BAAI/bge-small-en-v1.5,
revision 5c38ec7c405ec4b44b94cc5a9bb96e735b38267a. Each final encoder has a
384-to-2 linear head with dropout .1 during training. Binary labels: none, rule.
Encoder and head safetensors are local and ignored by git; exact weight hashes
are in results/quick-checks/check44b/model-freeze.json. Tokenizer/configuration,
DEV predictions, thresholds, split IDs and per-seed metadata are committed.

Fit lineage: Kimi's 2872 messages with 53 audited Opus label replacements,
plus 231 Opus enrichment messages. No benchmark or held-out fitting.
Same whole-domain partition for seeds 0/1/2: marketing and travel reserved for
DEV (309/3103 messages); all matched adoption/non-adoption variants stay together.
No explicit author scenario IDs exist; whole-domain grouping is the conservative
proxy. All seeds use three epochs, AdamW 3e-5, batch32, fp32, full encoder tuning.

Consumer: stencil.admission.Detector(path).infer({"message": ..., "role": ...}).
Segment A = [role] plus full message; segment B = exact frozen sentence span.
No truncation: >512-token pairs abstain. Non-user roles always reject. The
returned probabilities retain raw model values; the threshold comes from the
seed's threshold.json. Scope and semantic-key predictions are not implemented.
This model is not a complete rule-register runtime.

Seed0 is designated for the one-shot new Fable bank. Seeds1/2 measure DEV stability
only. The GO/NO-GO decision, frozen recipe, complete prediction records and CPU
latency are reported under results/quick-checks/check44b/. Runtime replacement is
conditional on the pre-written GO bar, not DEV performance.
