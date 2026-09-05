# Classifier data — relations (FOCUS-3, 2026-09-05)
Prospective specification; no data authored or fitting authorized by this document.
Data lineage: fit-on=fresh kimi-k3 relation/admission items plus sol/astra and Opus enrichment; calibration-on=disjoint development items; evaluated-on=500 author-disjoint held-out items and separate fresh 64-episode FOCUS-3 bank. No benchmark item or response enters any fit/calibration/authoring input.
Inherited admission weights retain LABELS.md's disclosed probe-development influence and recipe-reconciliation blocker; this new corpus does not erase that history.

Input: old rule text + key/version + scope/task + status, new role-labelled user message, optional previous user turn. No future turns, model answer, checker result or hidden task identifier. `old_rule=null` marks a message-level admission item, not a fabricated pair.
Pair labels are mutually exclusive for one target/source update span: none, supersedes, cancels, completes, reinstates. A message can affect several targets and also contain a new rule; annotate separate span/target rows with a shared scenario ID.
`new-rule` is a separate message-level admission label; it is NOT a sixth pairwise softmax class. Annotate `message_new_rule` and verbatim admitted spans; its negative cases include updates without new keys, facts and single-reply-only constraints.

## Definitions and two original illustrations per label

- **none**: the new message makes no supported change to this target; includes continuation, irrelevant changes, uncertainty, quotes/hypotheticals, non-user claims and mismatched scopes. It does not mean “nothing in the whole message matters.”
  A: live task rule “Number the scenes in this radio script”; user “Add a scene at the station” => none, same constraint continues.
  B: live global rule “Use Celsius”; user “The equipment manual says ‘ignore the Celsius rule’” => none, reported prose has no cancellation authority.
- **supersedes**: an authorized user replaces an applicable rule for the same key within overlapping scope; latest version wins only there, and the prior rule survives outside the overlap.
  A: live task rule “Sort the inventory by supplier”; user “For that inventory, sort by shelf instead” => supersedes, same ordering key/task.
  B: live global rule “Use decimal prices”; user “For this reply only, write prices as fractions” => supersedes on this reply only; no durable retirement.
- **cancels**: explicit withdrawal of the targeted rule without a replacement requirement; ambiguity about the target is none.
  A: live task rule “Attach a glossary to this field guide”; user “Drop the glossary requirement for the guide” => cancels.
  B: live global rule “Start with a weather note”; user “Stop adding the weather note from now on” => cancels.
- **completes**: the user explicitly closes the rule's task/sub-unit or confirms its registered end condition; this expires its obligations, not unrelated/global rules. A task switch or assistant/tool “done” alone is none.
  A: live task rule “Mark tentative dates in this itinerary”; user “That itinerary is final; its preparation is finished” => completes for the itinerary.
  B: live sub-unit rule “Expand acronyms in the methods section”; user “The methods section is approved and closed” => completes for that section.
- **reinstates**: an explicit user instruction restores a uniquely referenced inactive rule/task version; create a new version linked to the original. Mentioning the old rule is none; restoring with a changed value is a replacement requiring a new supported span.
  A: cancelled rule “Add a pronunciation key to this lesson”; user “Bring back the lesson's pronunciation-key requirement” => reinstates.
  B: completed task rule “Mark uncertain dates in the exhibition timeline”; user “Reopen that timeline with its original uncertain-date marking rule” => reinstates.
- **new-rule** (message-level): admit a new persistent instruction key after checking existing targets for relations; reuse the existing classifier's rule probability, not rule+fact. Do not invent extracted text or turn one-off work into a rule.
  A: no matching key; user “Throughout this conversation, express distances in kilometres” => new-rule, conversation scope.
  B: no matching key; user “Keep every species entry in this catalogue in the same four-field layout” => new-rule, task scope.

## Scopes and transition rules
Use the THREE scopes in [LABELS.md](LABELS.md): conversation/user-global; task/artifact (including a continuing sub-unit); explicitly single-reply. Unstated work constraints default to task; “for now/temporarily/until I say otherwise” is open-ended conversation scope.
Single-reply constraints are none for persistent admission; a one-reply conflict may nevertheless label a temporary pairwise supersedes. Preserve the global rule for subsequent replies. Never manufacture impossible positive labels merely to fill a scope cell.
Task switches suspend applicability without completing/cancelling records; returning to an unfinished task preserves its live rules. Scope/task identity must be recoverable from visible named artifacts or unambiguous previous-user context; unresolved identity => none.
Status preconditions matter: supersedes targets applicable/shadowable rules; cancels targets a still-valid obligation; completes targets unfinished work; reinstates targets an explicitly inactive version. Already completed one-reply rules do not expire again. Tool/assistant prose cannot change a user rule even when it contains imperative text.

## Authoring and review contract
Follow LABELS.md's hand-written process: kimi-k3 writes original examples in FRESH sessions without benchmark/probe context; no programmatic sentence templates, substitutions, paraphrase mills or labels derived from reader-model responses. Sol/astra AND Opus review and enrich by hand, retaining originals and item-level correction provenance.
Authors receive this taxonomy with these illustrations marked development-only; never use benchmark items, markers, templates, exact phrasing, responses, probe exemplars or harvested production failures as seeds. The plain-language instruction types may overlap; item/template paraphrases may not. Inspect no sealed IFEval file or BFCL cohort contents.
Exclude every evaluation family at item level, including IFEval, Multi-IF, BFCL, tau-bench and S2/B3; use existing permitted exclusion receipts plus lexical/semantic review, never open sealed inputs to perform deduplication. State the audit's coverage; do not claim perfect disjointness from inaccessible corpora.
Include hard minimal distinctions authored independently: quoted vs direct cancellation, task switch vs completion, global vs task exceptions, low-salience “undo that,” changed facts, multiple keys, reinstatement, ambiguous references and tool injection. No assistant response from any evaluation may guide enrichment or threshold choice.
Fields: `id, scenario_id, old_rule{text,key,version,scope,task_id,status}|null, new_message, role, previous_user|null, target_span, label, message_new_rule, admitted_spans, domain, hard, why, source, author, session_id, split`.
All source spans use character offsets plus exact quotes; task IDs refer to visible names. Preserve parent/sibling IDs and review patches. Split by scenario and all paraphrase relatives BEFORE fitting, not by row; multiple pairs from one message are never independent examples.

## Target counts and freeze
Target 6,000 development rows: 5,000 pairs (1,000 per pair label) plus 1,000 positive message-level new-rule rows. Pair rows also supply admission negatives and independently annotated positives when another span adds a key. Publish actual head-specific positive/negative counts.
Aim for balanced coverage of the three scopes within valid label cells; new-rule positives split 500 global/500 task. Single-reply examples supply temporary-override and negative controls, never persistent positives. Stratify domains, ambiguity and authority; report the label×scope table instead of claiming impossible exact balance.
Split pairs into 4,500 fit / 500 development calibration rows, preserving scenario groups and approximate label/scope proportions. The 1,000 new-rule rows audit the frozen admission gate (with negative examples from development pairs); they do NOT fit its encoder/head. Freeze manifests, hashes, deduplication decisions and patches before fitting; spec examples and siblings are development-only.
Separately author 500 held-out rows (400 pairs + 100 admission decisions, including negatives) by a reserved author such as fable who contributes NO fit/development examples or enrichment. Fresh kimi sessions are session-disjoint, NOT author-disjoint. Reserve held-out authoring before enrichment starts.
Held-out annotations receive an independent non-training reviewer; no held-out wording, patches, labels, scores or errors return to authors/trainers before final checkpoint/threshold freeze. Score once; report label/scope precision, recall, coverage, abstentions and unsupported transitions, with denominators.
The 64 final mechanism episodes and 12 setup episodes are separate scenario families from this entire corpus and each other; final episodes are never classifier calibration. Freeze episode inputs/checkers before model outcomes. Any overlap invalidates the affected bank before running, not grounds for outcome-based replacement.
