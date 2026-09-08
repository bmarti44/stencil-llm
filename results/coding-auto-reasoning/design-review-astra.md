# Independent automatic-focus design review — Astra

2026-09-08. Reviewer: native Astra, xhigh, as explicitly selected by the user;
author-disjoint from the design and implementation. Review scope is the
prospective engineering direction, with a trusted but fallible author, selector,
worker and orchestrator. It covers semantic authority, scope, the continuation
decision, finite-check limitations and resource feasibility. It does not assess
malicious same-user interference or the moving implementation. No model calls,
generated-code execution, semantic replay, training or data edits were performed.

## Round 1 — 94/100; direction accepted, launch not reviewed

One open medium finding; zero open high or critical findings. The proposed fresh
automatic pilot is a concrete, reasonable next engineering step. Finding 1 needs
explicit prospective wording before the data/runner freeze. This review accepts
neither a particular implementation nor an experiment launch.

Reviewed `DESIGN.md` SHA-256:
`1abb4a283d241fa8010378da3cdf2b196e7178dd385f1f12cb4e51a84b578478`.

Supporting local source snapshots:

- `results/coding-competence/DATA-CONTRACT.md`:
  `d107a5077bb88854ef816dbd93cd5cf94a6b5f365e46c2a5d0b8f650b6837796`.
- `results/coding-self-cue/research-reset/report-source.md`:
  `2366f03e82823949c33242926eed54e18996c046595bd6260cd657dabf5cce5f`.
- `results/coding-reasoning-smoke/run-01/audit-astra.md`:
  `100bfa17a70dbcb2e03581e087de9f1cdb9163e72b99e0246cb99005c95a2182`.

The governing process, current ledger state, parked source-reader and self-cue
protocols, and frozen competence protocol also informed the review. No earlier
project cases were reopened.

### Finding 1 — medium, open: define the focus's semantic domain and authority

The draft requires “complete” current focus but does not explicitly distinguish
the standing constraints/conventions being selected from the current request's
algorithm. Nor does “not an authoritative mutable summary” fully specify the
authority of the generated block when presented to the worker. Without that
definition, authoring and final semantic review could use different completeness
criteria, or the generated block could appear to adopt a quoted or suggested
instruction that the authentic user never adopted.

Add one narrow prospective paragraph establishing that the focus covers all
currently applicable standing constraints and conventions for the current task,
including permissions and optional behavior, preserving modality, scope,
exceptions and retirement. The authentic current request continues to supply
the algorithm; repeating its entire specification is not the focus completeness
criterion. Only authentic user directions or explicit user adoption establish
obligations. Quotes and assistant suggestions alone do not. Label the worker's
generated block as fallible guidance: authentic source directions govern, and
the block is not new user adoption. Apply these same meanings to the independent
semantic continuation review, including unsupported additions and stale rules.

The parent's clarification during review states exactly this intended runtime
behavior. The finding is the missing frozen design contract, not a demonstrated
implementation defect. Prose in the existing `text` field can express these
distinctions; additional schema fields or a rule language are unnecessary.

### Direction and scientific limits

This remains a disposable cold source-reader architecture: immutable originals
are retained, a current view is regenerated, and generated focus is not carried
forward as authoritative memory. Its prospective operating point differs from
the parked nonthinking reader through native reasoning and the typed tool
interface, and from the parked same-response self-cue through a separate
selector and a worker with actual edit/public-feedback history. Several factors
change together. A result cannot isolate a reasoning-mode effect or overturn
either earlier failure. The new bank must remain fresh; no retry or prompt rescue
of the completed recipes follows from this acceptance.

The accepted earlier research direction was conditional supervised interpreter
preparation after a worker screen. This pilot is an untrained automatic baseline
under the subsequently adopted direct-path decision, not execution or validation
of that supervised plan. The failed frozen manual screen remains failed. A
trained interpreter remains a distinct later candidate requiring its own data,
resource and evaluation decisions. Neither a perfect manual comparator nor
superiority over useful manual prose is necessary for the user's eventual
automatic-parity benefit.

Two projects can establish an engineering example, not a reliable population
rate. Requiring one whole project with all three actual endpoints, no identified
material source/dependency defect, and three complete accurate focus views is
non-vacuous for that narrow purpose. Finite checks alone are insufficient, as the
earlier source audit showed. Report the other project and every failed endpoint;
complete batch accounting and the prohibition on human correction remain
conditions of this fixed recipe. An INCOMPLETE batch cannot become a successful
pilot merely because an earlier project passed.

Even a passing project does not establish that the worker relied on its reminder:
the worker also sees the original conversation. The draft correctly disclaims
causation, parity, noninferiority and larger proof. A later fresh paired evaluation
must measure the eventual claim. Another manual-only qualification is not a
necessary detour before this engineering attempt.

### Native contract, shape and resources

Visible-ID enumeration checks citation membership, not support, completeness,
authority or scope. Independent semantic review remains necessary. Disposable
selection, unchanged focus across the two allowed attempts, actual code/tool
history, public-only stopping, terminal private checks, and no private fallback
preserve the intended test. The final implementation must enforce the exact
tool shape and same-byte native render/generation contract; these are prospective
requirements, not code findings in this review.

The completed smoke establishes the recorded original-model/native-tool path at
thinking allowance 512, including cold and post-tool requests. It does not
establish the new selector schema or allowance 1024. Those remain final readiness
and actual-call checks. Raw completion IDs, exact reasoning/final decoding,
rendered sampling fields, full output reserve before decode and final-only tool
history are appropriate evidence. A count reaching an allowance does not alone
prove that budget forcing caused termination. Any actual-call failure must stop
and remain accounted for, without an unregistered extra qualification call.

Arithmetic independently recomputed:

| Quantity | Result |
| --- | ---: |
| Maximum selector + worker generations | 6 + 12 = 18 |
| Maximum total output tokens | 36,864 |
| Output / prior rich-context rate | 1,959.551469745 s |
| Plus the proposed 780 s allowance | 2,739.551469745 s |
| Margin inside 3,000 s reservation | 260.448530255 s |
| Actual smoke plus full reservation | 3,516.914703272 s |
| Remaining within 3,600 s candidate ceiling | 83.085296728 s |

The 780-second estimate consists of 600 startup, 60 cleanup and 120 for other
work. It is planning arithmetic, not a throughput or completion guarantee.
Growing contexts, renders, execution and durable receipts must fit the same hard
deadline; no further paired arm or additional reservation is implicitly funded.
Use the prior rich-context rate 18.812468347567442, not the smaller smoke's rate.

With 1,024 reasoning tokens, two delimiters and one terminal EOS inside the
2,048 total cap, 1,021 final argument tokens remain. Requiring 128 spare means
each complete reference argument serialization is at most 893 tokens, counting
JSON escaping and source IDs. This is a prospective capacity eligibility check,
not knowledge of future generated length or semantic success. Preserve the
actual full-cap per-call context check and INCOMPLETE behavior.

There is no demonstrated budget or architectural blocker to this direction.
Accepted fresh data, complete reference-focus capacity checks, final native
consumer tests, preview, ownership/deadline evidence and an independent stable
implementation review remain prerequisites for a concrete launch decision.

## Round 2 — 96/100; direction accepted, launch not reviewed

2026-09-08. Narrow documentation delta only. Reviewed revised `DESIGN.md`
SHA-256 `6891d83ad2f6aac7d88bbec3d88a7c6337dd9337d011a1a95c9ccb3c3f9be1dc`.

**Finding 1 — medium, resolved 2026-09-08.** The design now explicitly defines
the focus as all currently applicable standing constraints and conventions,
preserving permissions, optional behavior, modality, scope and exceptions while
respecting change and retirement. The authentic current request supplies the
algorithm. User directions and explicit user adoption establish authority;
assistant suggestions and quotations alone do not. The same semantic definition
governs review for omissions, unsupported additions, wrong authority/scope/
modality and stale rules. Fixed worker instructions must label generated focus
as fallible advisory guidance, subordinate to authentic source directions and
incapable of establishing new adoption. These clauses resolve the recorded
ambiguity without changing the schema or adding a mechanism.

Zero open findings, including zero open high or critical findings. Round 1 and
its source bindings remain historical evidence. This is acceptance of the
prospective design direction only; final data, implementation, native contract,
preview, resource and lifecycle readiness remain outside this narrow delta and
must be established before launch. No code, data or model checks were performed.
