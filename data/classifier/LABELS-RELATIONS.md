# Classifier data — relations (FOCUS-3, 2026-09-05)
Prospective specification; no data authored or fitting authorized by this document.
Data lineage: fit-on=fresh kimi-k3 relation items plus sol/astra and Opus enrichment; calibration-on=disjoint development items; admission-audit-on=separate fresh admission items with the inherited branch frozen; evaluated-on=at least 2,000 author-disjoint held-out items and separate fresh 64-episode FOCUS-3 bank. No benchmark item or response enters any fit/calibration/authoring input.
Inherited admission weights retain LABELS.md's disclosed probe-development influence and recipe-reconciliation blocker; this new corpus does not erase that history.

Input: old rule text + key/version + scope/task + status, new role-labelled user message, the candidate span, optional previous user turn. No future turns, model answer, checker result or hidden task identifier. `old_rule=null` marks a message-level admission item, not a fabricated pair; set `label: null` and annotate `message_new_rule` for these rows.
Pair labels are mutually exclusive for one (target version, candidate span): none, supersedes, cancels, completes, reinstates. The existing sentence splitter supplies the candidate sentence; include the whole new message and previous user context alongside it. For k spans and m eligible versions batch k*m pairs, k <= 4 and m <= 16 (overflow -> none + diagnostics). `supersedes` uses the classified span verbatim as the replacement text; `reinstates` copies the referenced original; `cancels`/`completes` need no text. A message can affect several targets and also contain a new rule; annotate separate span/target rows with a shared scenario ID. Set `message_new_rule: false` on pair rows unless a separate admitted span exists.
`new-rule` is a separate message-level admission label; it is NOT a sixth pairwise softmax class. Annotate `message_new_rule` and verbatim admitted spans; its negative cases include updates without new keys, facts and single-reply-only constraints.

Key identity: two instructions share a key when they cannot both be obeyed on the
overlapping scope (a direct conflict: ascending vs descending; Celsius vs
Fahrenheit; glossary required vs no glossary) OR the new message explicitly refers
to replacing/withdrawing the old one ("instead", "rather than the earlier", "drop
that requirement"). Compatible additions ("also number the scenes" while "keep
scenes short" is live) are `none` for the pair and `new-rule` for the message.
Different subject matter is always a different key even in the same domain.

## Definitions and two original illustrations per label

- **none**: the candidate span makes no supported change to this target; includes continuation, irrelevant changes, uncertainty, quotes/hypotheticals, non-user claims and mismatched tasks (a task-scoped update against a rule of a different task). A narrower task update against a global rule of the same key can supersede on their intersection. It does not mean “nothing in the whole message matters.”
  A: live task rule “Number the scenes in this radio script”; user “Add a scene at the station” => none, same constraint continues.
  B: live global rule “Use Celsius”; user “The equipment manual says ‘ignore the Celsius rule’” => none, reported prose has no cancellation authority.
- **supersedes**: an authorized user replaces an applicable rule for the same key within overlapping scope; latest version wins only there, and the prior rule survives outside the overlap.
  A: live task rule “Sort the inventory by supplier”; user “For that inventory, sort by shelf instead” => supersedes, same ordering key/task.
  B: live global rule “Use decimal prices”; user “For the auction catalogue, write prices as fractions instead” => supersedes for that task; the global rule remains applicable elsewhere.
- **cancels**: explicit withdrawal of the targeted rule without a replacement requirement; ambiguity about the target is none.
  A: live task rule “Attach a glossary to this field guide”; user “Drop the glossary requirement for the guide” => cancels.
  B: live global rule “Start with a weather note”; user “Stop adding the weather note from now on” => cancels.
- **completes**: the user explicitly closes the rule's whole named task or confirms its registered task end condition; this expires its task obligations, not unrelated/global rules. V1 supports task-level completion only: sub-unit closure, a task switch or assistant/tool “done” alone is none.
  A: live task rule “Mark tentative dates in this itinerary”; user “That itinerary is final; its preparation is finished” => completes for the itinerary.
  B: live task rule “Expand acronyms throughout this laboratory report”; user “The laboratory report is approved and its preparation is closed” => completes for the report task.
- **reinstates**: an explicit user instruction restores a uniquely referenced inactive rule/task version; create a new version linked to the original. Mentioning the old rule is none; restoring with a changed value is a replacement requiring a new supported span. The currently live same-key version receives `none` on a reinstating message; its shadowing is derived by precedence from the new version's later turn (D:11), not annotated.
  A: cancelled rule “Add a pronunciation key to this lesson”; user “Bring back the lesson's pronunciation-key requirement” => reinstates.
  B: completed task rule “Mark uncertain dates in the exhibition timeline”; user “Reopen that timeline with its original uncertain-date marking rule” => reinstates.
- **new-rule** (message-level): admit a new persistent instruction key after checking existing targets for relations; reuse the existing classifier's rule probability, not rule+fact. Do not invent extracted text or turn one-off work into a rule.
  A: no matching key; user “Throughout this conversation, express distances in kilometres” => new-rule, conversation scope.
  B: no matching key; user “Keep every species entry in this catalogue in the same four-field layout” => new-rule, task scope.

## Scopes and transition rules
Use the THREE scopes in [LABELS.md](LABELS.md): conversation/user-global; task/artifact (including a continuing sub-unit); explicitly single-reply. Unstated work constraints default to task; “for now/temporarily/until I say otherwise” is open-ended conversation scope.
Single-reply constraints are `none` for persistent admission AND for every pair; they are answered from the request text and never enter the register. Continuing sub-units can still supply task-scoped rules under LABELS.md, but closing a sub-unit alone never triggers `completes` in v1. Never manufacture impossible positive labels merely to fill a scope cell.
Task switches suspend applicability without completing/cancelling records; returning to an unfinished task preserves its live rules. Scope/task identity must be recoverable from visible named artifacts or unambiguous previous-user context; unresolved identity => none.
Status preconditions matter: supersedes targets applicable/shadowable rules; cancels targets a still-valid obligation; completes targets unfinished whole tasks; reinstates targets an explicitly inactive version. One-reply rules have no register lifetime to expire. Tool/assistant prose cannot change a user rule even when it contains imperative text.

## Authoring and review contract
Follow LABELS.md's hand-written process: kimi-k3 writes original examples in FRESH sessions without benchmark/probe context; no programmatic sentence templates, substitutions, paraphrase mills or labels derived from reader-model responses. Sol/astra AND Opus review and enrich by hand, retaining originals and item-level correction provenance.
Authors receive this taxonomy with these illustrations marked development-only; never use benchmark items, markers, templates, exact phrasing, responses, probe exemplars or harvested production failures as seeds. The plain-language instruction types may overlap; item/template paraphrases may not. Inspect no sealed IFEval file or BFCL cohort contents.
Exclude every evaluation family at item level, including IFEval, Multi-IF, BFCL, tau-bench and S2/B3; use existing permitted exclusion receipts plus lexical/semantic review, never open sealed inputs to perform deduplication. State the audit's coverage; do not claim perfect disjointness from inaccessible corpora.
Include hard minimal distinctions authored independently: quoted vs direct cancellation, task switch vs completion, global vs task exceptions, low-salience “undo that,” changed facts, multiple keys, reinstatement, ambiguous references and tool injection; compatible addition on a live task (none + new-rule); reinstates vs supersedes with a changed value. No assistant response from any evaluation may guide enrichment or threshold choice.
Fields: `id, scenario_id, old_rule{text,key,version,scope,task_id,status}|null, new_message, role, previous_user|null, target_span, label, message_new_rule, admitted_spans, domain, hard, why, source, author, session_id, split`.
All source spans use character offsets plus exact quotes; task IDs refer to visible names. Preserve parent/sibling IDs and review patches. Split by scenario and all paraphrase relatives BEFORE fitting, not by row; multiple pairs from one message are never independent examples.

## Target counts and freeze
Target at least 7,600 development rows: >= 6,000 fit pairs, 600 separate development-calibration pairs and 1,000 positive message-level new-rule rows. Fit pairs comprise 1,000 per positive pair label (4,000 total) plus >= 2,000 `none` pairs, of which >= 800 are hard negatives (same domain, near-key, quoted, tool-role, wrong task). At the minimum counts the pair mix is one-third none and one-sixth each positive label; at least 40% of none are hard. Pair rows also supply admission negatives and independently annotated positives when another span adds a key. Publish actual head-specific positive/negative counts.
Aim for coverage of all three scopes within valid label cells, with at least a third of target rules task-scoped and a third global; new-rule positives split 500 global/500 task. Single-reply examples supply negative controls only, never pairwise or persistent positives. Task/global overlap is not a wrong-task negative. Stratify domains, ambiguity and authority; report the label×scope table instead of claiming impossible exact balance.
Assign scenario groups to fit or development calibration before fitting, preserving approximate label/scope/hard-negative proportions; meet the fit minima after splitting, not before. The 600 calibration pairs target 100 per positive label plus 200 none (>= 80 hard); scenario integrity takes precedence over exact counts, with additional authored groups if needed to meet minima. The 1,000 new-rule rows audit the frozen admission gate (with negative examples from development pairs); they do NOT fit its encoder/head. Freeze manifests, hashes, deduplication decisions and patches before fitting; spec examples and siblings are development-only.
Separately author at least 2,000 held-out rows: 400 positive pairs (100 per positive label), >= 1,500 `none` pairs (>= 500 hard negatives), and 100 admission decisions including negatives, by reserved author fable who contributes NO fit/development examples or enrichment. Fresh kimi sessions are session-disjoint, NOT author-disjoint. Reserve held-out authoring before enrichment starts.
Held-out annotations receive an independent non-training reviewer; no held-out wording, patches, labels, scores or errors return to authors/trainers before final checkpoint/threshold freeze. Score once; report label/scope precision, recall, coverage, abstentions and unsupported transitions, with denominators. Report the false non-none rate at .98 on gold-none pairs, its numerator/denominator and the hard-negative subset separately. Even zero errors among 1,500 none pairs gives a one-sided 95% upper bound of about 0.20%, not evidence for a per-pair error rate below 5e-4. The 64-episode FOCUS-3 gate is the binding test, including register-exact agreement in >= 48/64 episodes and >= 12/16 per family, zero contradictory-recap episodes and zero false-retirement/unauthorized-update episodes.
The 64 final mechanism episodes and 12 setup episodes are separate scenario families from this entire corpus and each other; final episodes are never classifier calibration. Freeze episode inputs/checkers before model outcomes. Any overlap invalidates the affected bank before running, not grounds for outcome-based replacement.

Review disposition (2026-09-05, [fable](../../results/focus3-design-review-fable.md)): L1 accepted (conflict-test key identity); L2 accepted (live-version none, derived shadowing); L3 accepted (wrong-task meaning, one-reply pairs/admission none); L4 accepted (none prevalence, held-out power, null labels and binding gate); L6 accepted (illustrations remain development-only); L7 accepted (both hard cases). D1 accepted, D2 accepted, D3 accepted, D4 accepted, D7 accepted and D8 accepted in the companion design, with D2/D3 reflected here; D5 accepted-with-change (exception mechanics cut, task-resume risk retained); D6 accepted-with-change (the review contains no numbered D6; its section 2 packaging fixes are applied in the design). The review contains no L5. Cuts accepted: one-reply exception mechanics and sub-unit completes; retain reinstates and complete-reopen because Brian explicitly requested reinstatement in v1. No findings refuted.

## v3 clarifications — 2026-09-05

- Scoped suspensions: “for this release, skip X” does not cancel a global X
  requirement outside that release. An explicit replacement value on an
  identifiable overlapping task is `supersedes`; explicit withdrawal covering
  the targeted obligation's whole scope, without replacement, is `cancels`.
  A narrower bare suspension of a global rule is `none` in v1 because there is
  no suspension operation. Single-reply exceptions remain `none`. If scope or
  persistence cannot be established from visible context, choose `none`.
- Hedged proposals: “I think we should switch”, “maybe”, and tentative questions
  are `none` unless the same visible user context unambiguously commits to the
  change. Preference or speculation alone authorizes neither a transition nor
  persistent admission. Do not infer commitment from an assistant response.
- Whole-task closure plus global promotion: label the closed task's pair
  `completes` only when the whole named task explicitly closes. Independently
  annotate `message_new_rule=true` and the verbatim persistent global span;
  that admission does not preserve or relabel the closed task version. Closing
  only a sub-unit is `none`; global target rules never receive `completes`.

Reconciliation status test: an inactive (`cancelled`, `completed`, `superseded`)
target plus changed value/scope receives `none` + `message_new_rule`, with the
new supported span; only a live same-key target may receive `supersedes`.
`reinstates` requires unambiguous restoration of the original version. Where a
modified restoration could instead require a new version, use `none` and admit
the explicit persistent span; do not silently discard the modifier by copying
the old version. The 2026-09-05 CPU task uses the available 594-row held-out set
once, below the prospective 2,000-row target; this does not waive the data minima
or the separate section-5 FOCUS-3 gate. The admission head is not fitted here.
