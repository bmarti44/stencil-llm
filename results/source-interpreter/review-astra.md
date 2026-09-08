# Source-interpreter preparation — independent Astra review

2026-09-08. Native Astra xhigh, as explicitly selected by the user; author-disjoint from the root-authored specification. This review concerns a small FIT-only label and length preparation packet, its semantic target domain, and the specified local token/loss consumer. It assumes trusted but fallible authors, implementers and orchestration. It does not assess malicious same-user interference, a training result, or implementation that has not yet been handed off. Earlier research, pilot audits and frozen readiness reports remain untouched.

## Round 1 — specification 94/100; final preparation PENDING

Historical disposition on the initial specification: one open medium finding, zero high or critical findings. The preparation direction is coherent; the relationship between conversation length and actual queried prefixes needs one clarification. Code, authored data and actual-token CPU evidence are not accepted in this round.

Bindings inspected for this specification review:

| Artifact | SHA-256 |
| --- | --- |
| Initial `results/source-interpreter/PREP.md` | `4018713ad6dd57db0efd083a3428e4c895aae0c3283bc7951c2751b928af9525` |
| Accepted `results/coding-auto-reasoning/research-next/research-astra.md` | `879f1ece8e7a8b5cd5fef63cb3808073e870d7255c0cfec8c1038ae451c71bdc` |
| `results/coding-auto-reasoning/research-next/base-assets.json` | `4987d6eec20a7628d45d64799cb8b7fc7250870be2e868755880e70b7e2b5227` |

### Finding 1 — medium: a long conversation need not produce a long queried prefix

**Open in round 1; resolved in round 2 below.** The initial specification constrains the number of messages in each whole conversation and orders three distinct queries, but does not constrain the last query's position. All three checkpoints could occur near the start of a 32–48-message conversation, followed by a long unqueried tail. That document would satisfy the longer-conversation band while supplying only short FIT prefixes. It would misrepresent the packet's intended history-length calibration and the later longest-sequence mechanics input.

The narrow correction is to require the final query to be the final source message and report actual prefix token lengths separately from whole-conversation message bands. This needs no new token quota, extra checkpoints, larger packet or task simplification. Message counts still do not guarantee token lengths; the real tokenizer's measurements remain authoritative. Independent semantic review must also check that the discussion is meaningful rather than filler.

### Lineage and semantic-domain assessment

The six conversations and their scenario families are assigned FIT before authoring or prefix expansion. Their eighteen prefixes are correlated checkpoints, not eighteen independent conversations or transfer cases. Future DEV and withheld conversations/families remain wholly new, and their labels, lengths and outputs cannot select this packet's format or future training hyperparameters. Excluding exposed earlier examples and benchmark-derived rows is appropriate. Family names alone cannot establish semantic independence; source review is explicitly required.

The target is all currently applicable standing constraints and conventions, including permissions, exceptions, modality, adoption, scope and retirement. The original request supplies its programming algorithm. A correct target need not restate that entire algorithm or every fixed task-API detail. Accurate current scope sometimes requires prose synthesized across messages; verbatim text and valid citation IDs cannot by themselves establish complete, correctly scoped meaning. The stated Kimi authorship and independent source-to-label review provide an appropriate boundary without root-authored semantic replacement or a gold fallback.

One empty-current-focus checkpoint is within this domain when prior standing rules have ceased to apply and the current programming request introduces no applicable standing convention. Its target remains a nonempty serialized JSON object plus EOS, so an empty obligations list must not be confused with empty target supervision. Its legitimacy requires source review rather than a structural special case.

Complete gold labels are appropriate preparation evidence. They do not establish a universal perfect-selector or perfect-manual prerequisite for later utility comparisons. Six FIT conversations can expose label, boundary and length problems; they cannot establish transfer, reliability, downstream code utility or the broader goal. The frozen failed pilots retain their original gates and outcomes.

### Required consuming behavior and remaining evidence

The proposed pure helper and targeted consumer tests are a proportionate implementation. Each input must preserve source IDs, roles, text, order and task handles through its inclusive query boundary, excluding future events, target annotations and earlier generated focus. Query identity and the correspondence between handles and queries must be validated before expansion. A reusable validator's support for other split names must not admit them into this six-document FIT invocation.

The explicit local HF nonthinking path is coherent with the accepted research direction. It should use the selected repository environment and verified original tokenizer without loading weights. The literal instruction and causal prefix construction are fixed before real packet tokenization. Positive-reasoning native-client behavior is outside this protocol.

Canonical compact JSON with unescaped Unicode, followed by exactly one EOS, gives a concrete supervised target. The actual tokenizer and consumer must demonstrate the exact generation prefix, target decoding and causal boundary; separately encoded segments need not equal a whole-text encoding. Tests must consume the constructed token/label arrays, confirming the first supervised target position, every target/EOS label, masked prefix and padding, and padding attention. A valid empty obligations object still supplies target and EOS labels. These are future acceptance checks, not claims that unwritten code already passes them.

Rejecting reserved role/control-token strings defines a limited natural-text domain; it does not claim arbitrary special-token robustness. Silent source mutation, truncation and task simplification are correctly excluded. No sequence or output cap is selected from this preparation. Actual per-prefix lengths and explicit failures must expose a capacity problem rather than hide it.

The original base-byte inventory supports local asset availability. It does not qualify a future training environment, long-context memory use, runtime or transfer. The selected repository environment must be bound separately from the environment that performed the historical hash job. A later bounded FIT-only mechanics measurement can use the real longest sequence; a native 4B LoRA server is not a prerequisite for this label/format preparation or a later isolated base-versus-adapter HF probe.

### Scope of verification

Read the specification and operational context, checked its alignment with the accepted research, and bound the research and base-asset receipts. No authoring, target inference, training, server, generated-code execution or tests were run. Final preparation acceptance requires stable helper/tests, preserved semantic authoring and guarded-correction provenance, independent review of all eighteen labels, and the actual-token eighteen-row CPU receipt with source, target, tokenizer/template, code and environment bindings.

## Round 2 — specification 96/100; final preparation PENDING

2026-09-08. Independently read the revised specification and rehashed it:

`results/source-interpreter/PREP.md` SHA-256 `5a8536453e52a9427aae02e8a32d6671b9968bc667e483d80f09b2a3be01898e`.

**Finding 1 — medium, resolved 2026-09-08.** The specification now explicitly requires the final query to be the conversation's final source message and separately reports actual prefix token lengths from whole-conversation message bands. This closes the precise unqueried-tail gap without changing packet size, quotas or semantic difficulty. The claimed future consumer regression is not treated as tested implementation evidence in this round.

**Specification disposition: accepted, 96/100; zero open findings, including zero open high or critical findings.** The concrete direction is ready for its planned preparation work. Final preparation acceptance remains **PENDING** stable implementation, independently reviewed authored data and complete actual-token CPU evidence in this same review topic. This score establishes neither a training result nor permission for a later training, inference or serving experiment.
