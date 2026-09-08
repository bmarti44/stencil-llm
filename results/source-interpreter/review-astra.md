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

## Round 3 — original authored data 70/100; NOT ACCEPTED

2026-09-08. This is one review round over six unchanged original documents, supplied in three completed pairs. Scope expanded only as each pair became terminal and its exact hashes were handed off. All six sources and all eighteen targets have now been read. There are **six open high findings (#2, #3, #6, #8, #9, #10), three open medium findings (#4, #5, #7), and zero critical findings**. Specification finding #1 remains resolved. The specification's earlier acceptance is unchanged; these gold labels are not accepted. Final preparation also remains pending stable implementation review and actual-token CPU evidence.

### Exact input and provenance bindings

Frozen specification/request commit: `79f08bc2`. PREP remains bound to `5a8536453e52a9427aae02e8a32d6671b9968bc667e483d80f09b2a3be01898e`. Paths below are under `results/source-interpreter/`.

| Document | Authored SHA-256 | Adjacent receipt SHA-256 |
| --- | --- | --- |
| `author-00/authored.json` | `4db3442589b88765f29fc9393150a0f2a27fc310ffd8f9b11efa7bd432612fb1` | `116b245dd75ccc1e78038492d8535ec67ebaf0fd1a45f814bf3effac04468a01` |
| `author-01/authored.json` | `b3975357ce54d5d40f4e50252b22b02318d647254c19dfef4447409fe84b877e` | `59e88ee13f34a20f0e34ce29e540bbe0805c65df548b8e3712f4d40ed594225d` |
| `author-02/authored.json` | `e914f3f59bfa4ef9b460386ab1e4d080017c039d1f7444c83faf1abbb91b66e0` | `0d76336b7d1fe3cc02e75006dbaaf05797640c89f6bbc25595f914d3dd638ed8` |
| `author-03/authored.json` | `cad40b35a3f8f8a80e48f0a486622969b655deeca4648c45d3bc8799115432f6` | `b2f7f7655edb8a9c9856532ff9aa95bbdbbff7f346b0f9d779b12cd4f4697c92` |
| `author-04/authored.json` | `3603763508be712f44327d42ae7450fc27a5029d2e40869b698902d5c96e54c5` | `c148596b12d6ed01f135a4df0b5354b82391ad361740323cfdaf4319a5d93c34` |
| `author-05/authored.json` | `285f4e2b4446f8f5455276a925083d726c1fcd1f35af47ae2504d9a5bf3b3514` | `97e6de2465440eb01ba57a69eb8bbd03fae5e31f953e9a6516bbca6d6345de8c` |

Independently verified for each document: request bytes equal the request in the frozen commit; request, raw response, response-text and authored-document hashes match the receipt; the raw response is terminal `done=true`/`done_reason=stop`; parsing its response text produces exactly the saved authored document, with no semantic transformation. The FIT receipt purpose is explicit and the legacy helper's former DEV purpose is disclosed separately. These checks support this authoring lineage; they do not prove originality against all possible external material or establish that any fictional tool output actually occurred.

Basic document checks also passed: exact top-level and message/query/obligation fields, fixed FIT identities, unique source IDs, three distinct ordered user queries with task handles, no extra handled checkpoint, final query at the final source message, and all nonempty citations inside their inclusive prefixes. This is an independent read/structure check, not a claim that the production helper has passed.

| Author / family | Whole messages | Queried prefix message counts | Obligation counts |
| --- | ---: | --- | --- |
| 00 / observatory reservations | 12 | 1, 5, 12 | 3, 7, 0 |
| 01 / city tree inspections | 11 | 3, 7, 11 | 7, 8, 8 |
| 02 / museum object loans | 20 | 1, 8, 20 | 4, 9, 13 |
| 03 / makerspace checkout | 21 | 6, 13, 21 | 7, 10, 14 |
| 04 / bird-survey export | 40 | 12, 24, 40 | 6, 11, 14 |
| 05 / ceramics kiln log | 38 | 5, 22, 38 | 3, 11, 15 |

The two-per-band requirement is satisfied. Actual token lengths and loss boundaries have not yet been measured in this review.

### Finding 2 — high, open: author-00 turns a domain-error restriction into a ban on every catch

Path: `author-00/authored.json`, `/queries/1/target/obligations/3/text` (m05 checkpoint; all array paths are zero-based).

The label says the sole permitted catch is the CLI catch and that “no catches may appear anywhere else.” Authentic m03 forbids broad `Exception` catches and says domain errors propagate. In m04 the assistant asks about catching `ReservationError` at the CLI boundary; m05 authorizes exactly that catch there and nowhere else. This does not prohibit every unrelated, specific exception catch everywhere in the project. The target broadens the user's prohibition and would teach false permission scope.

Correction direction: have Kimi restore the exact class/domain and location scope, including the CLI exception, without weakening the actual broad-Exception ban or ordinary domain-error propagation. Preserve the sources and both substantive service tasks. The other m05 conventions are present: runtime/test dependency distinction, UTC, duration units and boundary rounding, logging identifiers, and doctest retirement with annotations and pytest replacement.

### Finding 3 — high, open: author-01's final target distorts write and audit permissions

Paths: `author-01/authored.json`, `/queries/2/target/obligations/1/text` and `/queries/2/target/obligations/6/text` (m-11).

The first label makes shadow bookings and tentative holds the **only** permitted writes. Yet m-01 and m-11 require auditing the storm-emergency bypass, and m-09 requires `request_id` in audit entries. The target separately requires that audit too, leaving its supposedly exhaustive write permission inconsistent. The second path says the bypass **plus** the required audit entry must include `request_id`; the source establishes that field requirement for audit entries, not an additional input precondition for allowing the bypass. The actual bypass conditions are `incident_id` and supervisor approval, with mandatory auditing.

Correction direction: preserve all required audit behavior and its field scope, the non-production storage restriction, role restrictions, and conflict-implies-no-write priority. Do not repair this by dropping auditing or by adding new request prerequisites. The source does not establish that every active wildlife hold is necessarily a validation conflict, so this review does not invent that equivalence. The existing target's separate conflict/no-write clause matters when reading its tentative-hold language; any corrected permission statement must preserve that conditional interaction rather than become an unconditional instruction to write holds for every wildlife-held tree.

### Finding 4 — medium, open: unrelated command contracts enter current-task focus

Affected paths:

- `author-01/authored.json`, m-07 `/queries/1/target/obligations/1` (the schedule-validation/no-saving portion) and `/queries/1/target/obligations/3` (POST HTTP-200 contract).
- `author-05/authored.json`, m22 `/queries/1/target/obligations/3`, `/4`, `/5` (importer-only handling).
- `author-05/authored.json`, m38 `/queries/2/target/obligations/3`, `/4` (importer handling), `/6` (show atmosphere display), and `/12` (list filter/totals contract).

These are generally accurate historical clauses and explicitly retain their original endpoint/command names. That limits the defect: they do not simply order GET to use POST semantics or report to behave as show. They nevertheless belong to other tasks, with no source-established call dependency that makes those detailed command contracts applicable to the current preview, add/list/show, or report work. The target domain is current standing focus, not an inventory of all still-existing command behavior.

Correction direction: Kimi should project to the actual current task while retaining global conventions and applicable domain/dependency rules. In author-05, money units, nullable `loaded_by`, database conventions, gas/oos semantics relevant to report counts, the path/force rule, and the **show-only exception bounding the otherwise global timezone rule** should remain. This finding neither requires restating a whole algorithm nor licenses deleting constraints just because they originated during an earlier task.

### Finding 5 — medium, open: author-02 narrows the naming convention without source authority

Paths: `author-02/authored.json`, `/queries/0/target/obligations/1/text`, `/queries/1/target/obligations/1/text`, `/queries/2/target/obligations/1/text`.

m01 introduces conventions holding throughout the project, separately says public functions need specified docstrings, and says “names stay snake_case.” Every target turns the naming convention into public-function names only. The source does not grant an exemption for other otherwise covered names. Explicitly prescribed identifiers such as `LoanError` must of course retain their given spelling; that is not permission to narrow the whole convention to public functions.

Correction direction: preserve the original naming scope and explicit prescribed names, rather than silently choosing the narrower target or making the source requirement easier. The rest of this author's state transitions are substantially faithful: dicts over the rejected dataclass, cents/rounding, TOML replacement while retaining startup loading, audit requirements, malformed-input versus real-conflict behavior, JSON CLI output, network scope with three total attempts, and non-overridable high-risk/manual-review handling.

### Finding 6 — high, open: author-03 drops the database-only state invariant

Paths: `author-03/authored.json`, the obligation lists at `/queries/1/target/obligations` (m13) and `/queries/2/target/obligations` (m21); compare `/queries/0/target/obligations/2`.

m03 explicitly requires holds **and every other bit of state** to live in the application database. This is correctly present at the first checkpoint and absent at both later checkpoints, where fee ledgers, holds and waivers make it directly relevant. A ban on external services does not prohibit local files or in-memory state and therefore does not replace this invariant. m11 approves staging Postgres; it does not retire the application-database requirement.

Correction direction: restore the persistent invariant, with the actual SQLite dev/test and approved staging-Postgres scope. The later target already has an explicit Postgres-approval obligation, so this is **not** an additional finding that the entire target omits that approval. Any rewrite of the generic external-service wording must remain consistent with that specific approval and continue rejecting unapproved Redis/services.

### Finding 7 — medium, open: author-03's adopted-layout citations omit the originating proposal

Paths: `author-03/authored.json`, `/queries/0/target/obligations/4/source_ids`, `/queries/1/target/obligations/3/source_ids`, `/queries/2/target/obligations/3/source_ids`.

These labels describe `app/` with `routers/`, `models/`, `schemas/`, `services/` as part of the adopted layout, but cite only m04 and m05. That directory proposal appears in m02; m04 supplies the refined model/router split and migration proposal, and m05 supplies user adoption with the table-name correction. The source/adoption chain for the full label is incomplete in its citations.

Correction direction: Kimi must make the exact claimed layout and its provenance agree, preserving the authentic proposal/refinement/adoption chain rather than treating any assistant suggestion as authority by itself. m04's Alembic proposal and m05's adoption must be interpreted in that context; the generic ask-before-new-dependency policy must not silently revoke something actually adopted. This review does not require the target to repeat every one-off migration DDL operation or automatically promote every assistant implementation detail into a standing rule.

### Finding 8 — high, open: author-03 loses an explicit pending user decision

Path: `author-03/authored.json`, `/queries/1/target/obligations` (m13); authentic m12–m13.

The assistant raises the treatment of pre-fee-era checkouts, and the current user request says to leave that edge flagged until the user rules on it. The gold focus omits that unresolved decision entirely. This is a current authority/deferral constraint, not an algorithm that the selector must reproduce. A complete target cannot silently treat the outstanding policy as settled. The later assistant's accrual-with-TODO statement is not a user ruling, and m16's grandfathering decision is future information at this checkpoint.

Correction direction: retain the unresolved user-decision status at m13, without importing the later exemption or inventing a current legacy policy. At m21, the actual m16 grandfathering instruction is correctly present and should remain.

### Finding 9 — high, open: author-04 converts qualified permissions and an assistant claim into established authorization/state

Path: `author-04/authored.json`, `/queries/2/target/obligations/10/text` (m40), with citations to m16, m17, m29, m30.

The label says optional `--dry-run` and `--summary` “are in place.” No source reports that dry-run was implemented; m16–m17 grant only an optional testing feature under an effort cap. For summary, m29 imposes both “if it costs you nothing” and no delay to GeoJSON. The target drops the former qualifier and declares the condition met based on the assistant's m30 no-delay implementation claim. That does not establish satisfaction of both user conditions, and a fallible assistant status statement is not new user authorization.

Correction direction: retain exact optionality, effort/no-cost and no-delay conditions, distinguishing permission from reported implementation. The newer m39 stdout-only-written-paths convention must continue to govern the current batch; older optional display permissions cannot override it. Do not drop either optional feature merely to avoid representing its qualifications. The actual CSV-to-GeoJSON authorization, sensitive-species exception, Nightjar exclusion then retirement, zero-count preservation, deterministic output, and parked OAuth scope are otherwise represented meaningfully.

### Finding 10 — high, open: author-05 weakens the adopted storage contract

Paths: `author-05/authored.json`, missing layout convention in `/queries/1/target/obligations` and `/queries/2/target/obligations`; narrowed trigger ban at `/queries/1/target/obligations/8/text` and `/queries/2/target/obligations/9/text`.

m14 proposes the `batches`/`entries` table split and m15 explicitly adopts it. Neither later target states that adopted split. Mentioning an `entries.loaded_by` property and a database filename is not a complete statement of the adopted storage layout. Also, m15 says “no triggers” and substitutes `bump_rev()` on every write path. Both targets narrow this to no triggers **for revision tracking**, allowing other trigger purposes that the user did not authorize. These are continuing storage conventions, directly relevant to the add/query/report code, rather than a demand to restate those commands' algorithms.

Correction direction: retain the adopted split with the proposal/adoption provenance and the original unqualified trigger prohibition, alongside integer cents, nullable `loaded_by`, the explicit revision helper and WAL/no-custom-locking rules. Do not narrow the original source ban to match the defective target.

### Packet assessment and bounded correction disposition

The packet contains meaningful original scenario development rather than a repeated rule list: reservation planning and retirement, role-controlled tree scheduling, loan validation and approval policy, material checkout and fee decisions, export-format/embargo changes, and kiln storage/reporting. Some common coding conventions recur across families, which is expected in a small calibration packet; differing IDs alone are not my basis for assessing their distinct scenario structures. Within the inspected request/source evidence I found no supplied old example or obvious copied scenario. That is a bounded lineage/originality assessment, not proof about Kimi's pretraining or every external source.

Coverage is substantively present for global versus task-scoped rules, permission conditions, exceptions, explicit adoption/rejection, replacement/retirement, and irrelevant future work. Examples include the museum retry-count clarification, makerspace postponed SSO, exporter OAuth deferral and embargo retirement, and kiln's unbuilt export delimiter. These are useful interpretation challenges and should not be simplified away during correction.

Exactly one target is empty: author-00 m12. This is legitimate. User m10 retires **every** session convention; m12 explicitly starts a separate substantive analysis task with its own algorithm and no new standing convention. All seventeen other targets are nonempty. Neither the empty target nor the absence of full algorithm summaries is a defect. The authored tool-result narratives are source events in fictional conversations, not execution evidence for the described software.

Proceed, within the parent's existing authoring authorization, to a single guarded Kimi semantic correction round addressing the exact findings while preserving the original conversations, families, query identities, substantive work and meaningful scope changes. Root must not author replacement gold semantics. Preserve originals, raw correction output and exact guarded patches; re-review the changed labels and their consequences. If a source ambiguity actually requires clarification, make it explicit for independent review rather than quietly narrowing the task or adding authority to justify a desired label.

No implementation was inspected in this data round; no generated code, model, server or training was run. The only local execution was read-only JSON/hash/structure verification. Label correction is not a permission to tune on future evaluation, select a cap, simplify long examples, or claim useful transfer. **Original-data disposition: NOT ACCEPTED, 70/100. Final preparation remains PENDING corrected accepted labels, stable helper review and all eighteen actual-token CPU rows.**

## Round 4 — stable CPU helper code 94/100; two medium contract findings

2026-09-08. Independent code review of Sol's stable pure helper and targeted tests. This code-only score is separate from round 3's unaccepted original labels. **Code scope: two open medium findings (#11–#12), zero high or critical.** Core serialization and collation are sound on the inspected default path, but the authoritative preview should await the two narrow contract corrections below. No final preparation acceptance is issued. Gold findings #2–#10 remain open until their separate guarded correction review; #1 remains resolved.

| Binding | SHA-256 |
| --- | --- |
| `src/stencil/focus/source_interpreter.py` (commit `cbab0734`) | `be992787732292cccbaef4879f20eaba454249c329f8832927180f0d5da31afe` |
| `tests/test_source_interpreter.py` (padding correction `57c5bb33`) | `eb9764a403d0dbae565c30ba010409a924bdc7bbee4dd44fbd3228b7e730c035` |
| `results/source-interpreter/CODE-BRIEF.md` | `ae9bfa6a37b5ecafcace4408f8c6a3462387714aeb7f94ae71d8bbfa67667427` |
| `results/source-interpreter/PREP.md` | `5a8536453e52a9427aae02e8a32d6671b9968bc667e483d80f09b2a3be01898e` |

### Finding 11 — medium, open: the reserved-token check misses native controls marked special=false

Affected consumers: `_assert_natural_text()` and the final target-ID check in `prepare_row()`.

Both use only `tokenizer.all_special_ids`. The exact local Qwen tokenizer's added-token inventory contains 26 dedicated control tokens, IDs 151643–151668; only 14 are marked special. Native thinking and tool delimiters are among the other twelve. Consequently the existing im_start/im_end controls exercise a narrower set than the registered reserved role/control-token domain.

Independent actual-tokenizer controls through `prepare_row()` accepted each of `<think>`, `</think>`, `<tool_call>`, `</tool_call>` in both source and target, supervising the dedicated IDs 151667, 151668, 151657 and 151658 respectively. These are not ordinary multibyte spellings accidentally resembling controls. Inspection of the pinned tokenizer JSON also confirms the remaining special=false FIM, repository/file and tool-response controls.

Correction direction: derive and bind the reserved control-ID inventory from the original tokenizer's added-token assets, covering all native control markers rather than only these four probes or only the special=true subset. Reject their occurrence through the real natural-source/target serializer, without semantic regex, text rewriting or a new interpreter mechanism. Keep the legitimately inserted nonthinking template controls masked in the prefix and append the real EOS only at the target boundary. This is a domain-enforcement defect; this review neither tokenized the real authored packet nor claims its documents contain these markers.

### Finding 12 — medium, open: preview binds reference files but not the tokenizer state actually used

Affected consumer: `preview(paths, tokenizer=...)`, including its `_asset_hashes()` receipt and the cached mutable object returned by `load_tokenizer()`.

The preview accepts a caller-supplied tokenizer and unconditionally reports/hashes the files under `MODEL_PATH`. It records class, name/path, template and special-ID metadata, but does not establish that the tokenizer's actual vocabulary/backend state still corresponds to those original files. A same-path tokenizer can be changed in memory without changing any recorded asset file.

Independent bounded reproduction: load the original local tokenizer; add one ordinary synthetic token in memory; invoke the actual preview on six temporary synthetic FIT documents in the prescribed bands. It returns PASS and all 18 rows, reports the original path/name and original asset hashes, but supervises newly added token ID 151669. The original tokenizer encoded that synthetic marker as eleven different IDs. No actual tokenizer-state/backend hash is recorded. No asset file was edited and no model was loaded.

This is a plausible trusted-caller configuration mismatch, not an adversarial same-user attack. The normal fresh default loader path remains consistent with the inspected assets, which limits severity. Nevertheless a receipt claiming original-tokenizer preparation must establish the identity of the object that produced the IDs; hashing nearby files does not do so.

Correction direction: narrowly require and bind the verified original tokenizer state for the authoritative preview, rejecting altered or mismatched state, or restrict that consumer so an override cannot masquerade as original-asset evidence. Path/name equality alone is insufficient for the reproduced same-path mutation. Keep any future measured training/generation consumer on the same exact prefix/tokenizer construction; no server or new training framework is needed.

### What the consuming paths establish

The loader rejects duplicate JSON keys and invalid constants, unknown schema fields, wrong types, repeated conversation/message/query identities, cross-split families, future citations and unqueried tails. It validates the complete corpus before prefix expansion. Calibration additionally requires six FIT documents, two in each message band and all eighteen rows. Selecting the six accepted file hashes and establishing semantic family independence remain the parent's/data-review boundary; a shape validator cannot prove that arbitrary six FIT inputs are the reviewed packet.

Each prepared row copies the inclusive authentic prefix with original roles, IDs, text and handles. The prompt has a fixed generic system instruction and one source-event user message. Targets, future events and previous generated focus do not enter that prompt. Unicode and spacing survive the source JSON round trip. Empty obligations serialize to a real JSON target, rather than empty supervision. There is no positive-reasoning client or tool wrapper in this path.

The chosen causal construction is explicit: the local template's nonthinking generation prefix IDs, separately encoded compact sorted JSON target IDs, then one tokenizer EOS. Text-template and direct-token-template results must agree; both segments and the combined sequence must decode exactly. Joint text encoding equality is measured, not silently assumed as the construction rule. Decoding and length checks prevent unnoticed truncation. The target's EOS is exactly one; template EOS/control tokens in the prefix remain masked and are not counted as target supervision.

For ordinary causal-LM training, placing the first target label at index `prefix_length` is correct: the model's standard internal causal shift trains the preceding prefix position to predict it. Every target and EOS position is supervised, every prefix position is -100, and right padding adds attention zero and label -100. `collate()` rejects inconsistent lengths, reordered/truncated inputs, altered label positions and wrong target EOS rather than trusting a `PreparedRow` blindly.

The preview retains every row's exact prefix, target, IDs, labels, attention and loss positions; aggregate padding can be reconstructed from those rows and the recorded pad/width. It reports actual length distributions and maxima by whole-conversation band without selecting an output or sequence cap. It binds source files, code, prompt, schema, template and interpreter/package metadata. Finding #12 qualifies the claim about actual tokenizer assets. The base-asset receipt hash is contextual evidence, not a fresh model-weight check or training qualification.

### Independent validation and limits

Ran `.venv/bin/pytest -q tests/test_source_interpreter.py`: **7 passed in 2.08s**. Ruff check, Ruff format check and `git diff --check` passed. Inspected the actual eight-line padding-test delta: later query positions now produce unequal row lengths, and explicit positive-padding assertions precede checks of pad IDs, attention and labels. The formerly vacuous no-padding fixture is not the basis of this acceptance assessment.

A fresh process import left both transformers and torch unimported and the lazy tokenizer cache empty. The bounded additional controls used only the actual local tokenizer, temporary synthetic documents and read-only asset metadata. They exercised the two concrete findings through `prepare_row()` and `preview()`. No real original or corrected packet was tokenized; no weights, generated code, GPU, model, HTTP, training or serving operation ran. No other implementation or data file was edited.

**Current disposition:** code-only 94/100 with #11 and #12 open medium, pending narrow correction verification. Across the preparation topic the six high gold findings and three medium gold findings also remain open. Final preparation remains **PENDING** accepted corrected labels, corrected authoritative-tokenizer consumer evidence and the complete eighteen-row real CPU preview.

## Round 5 — guarded corrected labels 96/100; labels ACCEPTED

2026-09-08. Re-reviewed the exact twelve Kimi-authored target replacements and their consequences against the unchanged source conversations. All nine original-data findings #2–#10 are resolved below. **Labels-only disposition: accepted, 96/100, zero open label findings and zero open high or critical findings.** This does not accept the moving code correction or constitute final preparation acceptance; code findings #11 and #12 remain open medium pending their own stable handoff and review.

### Guarded lineage and exact accepted inputs

Correction plan SHA-256: `9cabf65f1ac50eb370c66040df3bdf535785c1380daafd7e9086e3690c12a689`. Exact differences artifact `results/source-interpreter/correction-01/changes.json` SHA-256: `127e3848f566fd23c43d89eca554449b48de47cd69de3ebc744b45cf77907c23`. It binds each original, corrected document and immutable-source guard; independently rehashed all those bindings.

The six correction requests equal their frozen bytes in commit `0fb6a29a`. Their plan binds the original-data review through Git commit `7e85790b62ab4e6da2d515c80c6519317400b015`; independently verified that archived review blob has SHA `aea791fad383cc2efdd767bed595becd8d867d1d57ea886661ad6d0ff8239f93`. The canonical review's later append operations therefore do not change the correction request's governing evidence.

Independently reconstructed every guarded replacement from its exact `expected_old` and `value`, obtaining the corresponding corrected document. For each author, request/raw-response/response-text/document receipt hashes match, the raw response is terminal with `done=true` and reason `stop`, and parsing its response text yields exactly the saved corrected document. Duplicate JSON keys were rejected during this verification. All source-message values, text and order, top-level metadata, query anchors and unallowlisted targets remain unchanged. Exactly twelve targets changed and six did not; there was no semantic edit by this reviewer.

Accepted paths below are under `results/source-interpreter/correction-01/`:

| Corrected document | SHA-256 | Changed query indices |
| --- | --- | --- |
| `author-00/authored.json` | `8b9765feb169632874d357cda45f000ddf460f013b100a45790e5e8c4462196f` | 1 |
| `author-01/authored.json` | `99d9c054b52be7c4cda07dc53a394b5bf82d6273584505ce64ff299336cc8c58` | 1, 2 |
| `author-02/authored.json` | `2c2ecc9868b9a65592a3295788a93944b1a87fd1732864da076953405f128e34` | 0, 1, 2 |
| `author-03/authored.json` | `82dced3eeaa4046badc83509e6570fce34f19fdba7745cf343a8ac7cab29530a` | 0, 1, 2 |
| `author-04/authored.json` | `bf064b0d385479abc3dddcf6f2de8f9b85734a8157621faeed6312cb247051a5` | 2 |
| `author-05/authored.json` | `ee0f327dbe1957170a99f93e9d25c4edf4fb6c6ed059765504aaea06d034ecb3` | 1, 2 |

### Finding closures and consequence review

**Finding 2 — high, resolved 2026-09-08.** Author-00 m05 now scopes the location limit to `ReservationError` catches and retains domain-error propagation, while distinguishing unrelated specific catches from the still-forbidden broad `Exception` catch. It no longer invents a ban on every exception handler. Its citation to m05 anchors the CLI permission; the adjacent unchanged obligation already cites m03 for the repeated global broad-Exception rule. Read as the complete target, the source/adoption chain remains visible and supported. Adding m03/m04 to the repeated clause could make citation granularity more explicit, but the current target does not introduce unsupported authority or lose the governing source, so no new label defect is recorded.

**Finding 3 — high, resolved 2026-09-08.** Author-01 m-11 now includes the mandatory emergency-bypass audit writes rather than excluding them from an exhaustive booking/hold-only permission. `request_id` is required in every audit entry, not promoted into a new bypass-input condition. The actual incident/supervisor conditions, role restrictions, no-production boundary and conflict-implies-no-write rule remain. The tentative-hold wording explicitly retains validation priority; it does not establish the unsupported equivalence between every wildlife hold and a validation conflict.

**Finding 4 — medium, resolved 2026-09-08.** Author-01's preview focus removes the unrelated POST no-saving and response-status contracts. Author-05's later targets remove the old importer-only and unrelated show/list contracts identified in round 3. The correction retains applicable global and domain constraints: nullable `loaded_by`, cents, storage and revision rules, gas/oos semantics relevant to report counts, output restrictions, and the path/force condition. The show-only UTC exception correctly remains as a qualification on the otherwise global display convention, without adding that flag to report.

**Finding 5 — medium, resolved 2026-09-08.** All three author-02 targets now retain the source's project-wide naming scope while preserving explicitly prescribed identifiers such as `LoanError`. Public-function docstring requirements remain separately scoped. No source convention was narrowed to make this correction easier.

**Finding 6 — high, resolved 2026-09-08.** Both later author-03 targets restore every bit of application state to the application database and explicitly preserve SQLite dev/test versus approved staging Postgres. The same clause retains no unapproved external services and no daemon/cron computation. Its parenthetical examples include waivers even at m13; this illustrates the already universal state-location rule and does not instruct creating a waiver feature before it is requested. The correction's governing statement is the source-grounded universal invariant, not an added future-task instruction.

**Finding 7 — medium, resolved 2026-09-08.** All three author-03 layout labels now cite m02, m04 and m05, preserving the originating directory proposal, refined layout and user adoption with the plural-table correction. The layout text is unchanged. This fixes the recorded provenance gap without claiming that arbitrary assistant suggestions have user authority or requiring repetition of every migration operation.

**Finding 8 — high, resolved 2026-09-08.** Author-03 m13 now explicitly retains the unresolved pre-fee-era policy and the instruction to leave that edge flagged until the user rules. It cites m12–m13 and does not import the future grandfathering decision. At m21 the actual later grandfathering instruction remains intact.

**Finding 9 — high, resolved 2026-09-08.** Author-04 m40 now distinguishes optional permission from an unsupported implementation-state assertion, preserves dry-run's effort cap, and preserves both summary conditions: no cost and no GeoJSON delay. It treats m30 as a fallible implementation report, not a new user authorization or proof that both conditions held. It also explicitly gives the newer stdout-only-written-paths convention priority for the current batch. The label is verbose but faithful; verbosity alone does not justify shortening semantic difficulty or choosing a capacity limit before the CPU measurement.

**Finding 10 — high, resolved 2026-09-08.** Both later author-05 targets retain the adopted `batches`/`entries` split with m14/m15 provenance and restore the unqualified no-database-triggers rule. `bump_rev()` on every write, cents, nullable `loaded_by` and WAL/no-custom-locking remain. The correction changes labels rather than retroactively weakening the source contract.

### Resulting label boundary

The source families, meaningful project development, scope changes, algorithms and whole-conversation length bands are unchanged. All eighteen targets retain valid visible citations and the expected shape. The sole empty focus, author-00 m12 after total retirement, remains unchanged and legitimate; the other seventeen targets remain nonempty. No material consequence or regression was found in the changed labels or their interaction with unchanged obligations. The retained format, permission and domain constraints are accepted as current standing focus; this is not a requirement to repeat the full current programming algorithm.

This acceptance qualifies these exact FIT labels for the specified preparation, not learned transfer, code usefulness, representation superiority or a perfect-selector prerequisite for later utility work. The six families and their eighteen correlated prefixes remain FIT-only. All original and correction provenance must remain preserved when the parent copies these exact accepted bytes to canonical preparation inputs.

No moving code was inspected in this round, and no code tests, real-packet tokenization, model, GPU or HTTP calls were run. Final preparation remains **PENDING** verification of the stable fixes for code findings #11–#12 and the complete eighteen-row actual-token CPU receipt. **Current open findings: #11 and #12, both medium; zero open high or critical.**
