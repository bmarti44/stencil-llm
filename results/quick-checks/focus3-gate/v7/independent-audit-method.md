# Independent saved-record checks

No inference or evaluation-input reread. Load the96 saved CPU record files.
For every record compare before/after rows by provenance ID: no prior row may
vanish; every new row must match one admit/supersedes/reinstates action's exact
turn and span offset; every changed old row must be an action's target. Require
the union of accounted new/changed IDs to equal the actual changed-ID set.
Totals:66actions,57new rows,12changed old rows, zero unexplained mutations.

Recompute softmax from every non-overflow admission/relation logit vector and
compare saved probabilities at absolute/relative1e-12. Normalize each saved
relation input with train_relations.normalize_row and compare render_pair to
the saved model_input. No new model scoring is involved.

Replay each episode with SavedClassifier and assert exact record identity.
Track Runtime.key_slugs across steps, using its pre-turn value when classifying
each cross-key proposal. Do not infer the key from raw payload text: payload
admissions have the registered prose-only instruction slug, even though the
unchanged relation-input metadata detects the word tag in the full request.
Ten rejected proposals are7sort-order→tag/3sort-order→instruction,5supersedes/
5cancels. Every rejected proposal has applied=none. Unauthorized detail comes
from exact action/gold-event matching, with admission scores attached by span.
