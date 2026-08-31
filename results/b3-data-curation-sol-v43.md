# v4.3 manual curation report

## Verdict

**Freeze-ready.** The edited streams are materially cleaner than the staged
versions and pass the repository's full v4.3 canonical, targeted-mutation,
and span checks. The remaining stylistic roughness is predominantly in the
frozen trunk's own greedy base prose, which I intentionally did not rewrite:
doing so would defeat the minimal-edit/low-perplexity premise of this dataset.

## Review performed

I inspected the generator and frozen base-text source, exhaustively reviewed
the finite inserted surface-form families (titles, keyword carriers,
postscript lines, placeholders, word/sentence padding, JSON, bullets, and the
two-response separator), searched every row for systematic seam patterns, and
read a broad train/dev sample stratified across topics, styles, constraints,
and combinations. I then repeated the searches and spot review on the edited
streams.

The important findings were:

- **High — exact-value contradiction:** 68 train rows and 4 dev rows combined
  `english_capital` with an exact mixed-case title or named placeholders. The
  vendored checker accepted the uppercase rendering, but the prompt's exact
  value was not present. These rows were deleted rather than cosmetically
  patched, and keys were renumbered sequentially.
- **High — semantically arbitrary keyword carriers:** randomized obligations
  produced constructions such as an old awning, a fetched cistern, or a
  cleaned windmill. All 1,746 train and 170 dev keyword-carrier occurrences
  were replaced with short, explicit requested-term sentences. The required
  keyword substrings and their frequencies remain unchanged.
- **Medium — placeholder seam:** the generated imperative (“Bring ... to ...”)
  is nonsensical for arbitrary placeholder types. All 450 retained train and
  49 dev occurrences now frame that exact, unchanged sentence as a quoted
  fill-in template.
- **Medium — sanitization artifacts:** markdown headings were flattened into
  the first prose sentence, stripped bracket fields left holes such as
  “located at the heart of ,” and “serviced ... on ,”, and two event-style
  bases retained empty `Date: Time: Location:` labels. These seams were
  removed or repaired while retaining the trunk-generated prose.
- **Medium — repeated padding pathology:** 492 train and 53 dev generated
  `ladder` anecdotes used only to meet word/sentence floors were replaced with
  grammatical neutral continuation sentences.
- **High — incomplete `two_resp` targets:** the staged implementation divided
  one response in half around `******`; neither half was reliably a complete
  reply. All 56 train and 6 dev targets now contain two complete frozen-trunk
  replies in different task styles for the same topic.
- **Medium — duplicate-input target ambiguity:** six retained train rows had
  byte-identical prompts but different stochastic target arrangements. Their
  targets were unified so identical inputs no longer supervise conflicting
  outputs.

## Row counts and final identities

| Stream | Staged | Deleted | Final | SHA-256 |
|---|---:|---:|---:|---|
| `v43-train-2000.jsonl` | 2,000 | 68 | 1,932 | `8a5b083cfa2df0a7dfd3418faaf20a8c4adbf8dc996599be3d3530c728517b71` |
| `v43-dev-200.jsonl` | 200 | 4 | 196 | `4ca868810e169de85658b25805559e0d11a30ec1d38d45dcead249065b391944` |

The final keys are contiguous (`0..1931`, `0..195`). Schema field order and
field set are unchanged.

## Mechanical verification

- `stencil.b3_gen43.verify43`: **0 failures** on 1,932 train rows and **0
  failures** on 196 dev rows. Thus every canonical passes every requested
  constraint, and every regenerated mutation fails only its named target.
- Every obligation span is nonempty and in bounds; spans and mutations were
  regenerated after edits.
- Exact title and placeholder values have **0 case-sensitive misses**.
- Known empty-field and old-carrier patterns have **0 residual hits**.
- Duplicate prompts have exactly one canonical target.
- Train/dev remain disjoint: 30 versus 10 topics, with **0 topic overlap** and
  **0 prompt overlap**.

## Residual caveats

- Exact title values retain generator-authored title casing such as “Notes on
  Mapping A Small Orchard.” They are mildly editorially awkward, but changing
  them would alter a prompt-specified obligation value rather than repair a
  seam.
- Some frozen-trunk replies contain clumsy inline numbered lists or factual
  simplifications. They are not introduced by constraint insertion, and broad
  rewriting would replace the very base distribution this experiment is
  designed to preserve.
- Random keyword requirements remain necessarily conspicuous. The new
  metalinguistic sentences make that conspicuousness grammatical and ensure
  the value is still prompt-dependent; they do not pretend that an arbitrary
  noun always belongs naturally in the topic prose.

