# Astra unstuck request: root-cause the focal-delivery pilot failures (read-only, xhigh)

Owner instruction (verbatim): "you need to fix the obvious issues and bugs before we write this off - push through and don't just simply give up. find the root cause and resolve it. ask astra as well"

Context: `results/reviews/2026-09-12-direction-proposal-rev2.md` (direction D, focal delivery) and your round-2 review (`2026-09-12-direction-adversarial-rev2-astra.md`, D NOT DISPROVED). Runtime: `src/stencil/focal.py`, `src/stencil/focal_runtime.py` (rollback-to-line-start insertion, croppable DynamicCache, header-keyword re-feed), pilot script `scripts/focal_quicklook.py`. Do not read `data/bench/`. Do not write files or run models. Read the code and the pilot records `results/focal/quicklook-v2.json` and `results/focal/quicklook.json` (v3; may be partial) — each record has per-arm `text`, `events`, `score`.

## What happened (4 SETUP-LONG items, Qwen3-4B bf16 greedy, label-derived live rules given to every intervention arm, 1,200-token cap)

v2 (cue = one `# Convention: <rule>` line per rule, inserted above the governed unit; no keyword re-feed):
```
[352-99] base identity=True tokens=560 pkg 73.2s loop 71.5s
[352-99] base           fraction=0.020 regex=0.00 pair=0.00 bool=0.11 tokens=560 s=73
[352-99] oracle_before  fraction=0.000 regex=0.00 pair=0.00 bool=0.00 tokens=1200 s=153
[352-99] oracle_focal_first fraction=0.000 regex=0.00 pair=0.00 bool=0.00 tokens=1200 s=156 ins=2/182tok echo=2 eos=False
[352-99] oracle_focal_every fraction=0.000 regex=0.00 pair=0.00 bool=0.00 tokens=1200 s=140 ins=2/182tok echo=2 eos=False
[352-99] oracle_periodic fraction=0.000 regex=0.00 pair=0.00 bool=0.00 tokens=1200 s=187 ins=10/8230tok echo=45 eos=False
[314-49] base identity=True tokens=216 pkg 29.5s loop 29.5s
[314-49] base           fraction=0.136 regex=0.00 pair=0.11 bool=0.29 tokens=216 s=29
[314-49] oracle_before  fraction=0.364 regex=0.17 pair=0.44 bool=0.43 tokens=393 s=52
[314-49] oracle_focal_first fraction=0.227 regex=0.17 pair=0.11 bool=0.43 tokens=278 s=39 ins=2/158tok echo=2 eos=True
[314-49] oracle_focal_every fraction=0.227 regex=0.17 pair=0.11 bool=0.43 tokens=433 s=63 ins=6/454tok echo=11 eos=True
[314-49] oracle_periodic fraction=0.000 regex=0.00 pair=0.00 bool=0.00 tokens=1200 s=191 ins=26/9152tok echo=51 eos=False
[186-14] base identity=True tokens=517 pkg 68.5s loop 68.2s
[186-14] base           fraction=0.222 regex=0.20 pair=0.00 bool=0.33 tokens=517 s=68
[186-14] oracle_before  fraction=0.556 regex=0.40 pair=1.00 bool=0.67 tokens=168 s=23
[186-14] oracle_focal_first fraction=0.111 regex=0.20 pair=0.00 bool=0.00 tokens=909 s=123 ins=3/115tok echo=3 eos=True
[186-14] oracle_focal_every fraction=0.667 regex=0.60 pair=1.00 bool=0.67 tokens=423 s=59 ins=6/237tok echo=0 eos=True
[186-14] oracle_periodic fraction=0.000 regex=0.00 pair=0.00 bool=0.00 tokens=1200 s=163 ins=12/1404tok echo=30 eos=False
[184-14] base identity=True tokens=447 pkg 59.4s loop 59.0s
[184-14] base           fraction=0.000 regex=0.00 pair=0.00 bool=0.00 tokens=447 s=59
[184-14] oracle_before  fraction=0.222 regex=0.00 pair=1.00 bool=0.25 tokens=422 s=56
[184-14] oracle_focal_first fraction=0.111 regex=0.00 pair=1.00 bool=0.00 tokens=451 s=61 ins=3/118tok echo=1 eos=True
[184-14] oracle_focal_every fraction=0.000 regex=0.00 pair=0.00 bool=0.00 tokens=1200 s=163 ins=6/255tok echo=57 eos=False
[184-14] oracle_periodic fraction=0.000 regex=0.00 pair=0.00 bool=0.00 tokens=1200 s=165 ins=14/1666tok echo=0 eos=False
```
v3 (same, plus the unit's header keyword re-fed after the cue so the model must complete the unit):
```
[352-99] base identity=True tokens=560 pkg 73.4s loop 72.0s
[352-99] base           fraction=0.020 regex=0.00 pair=0.00 bool=0.11 tokens=560 s=73
[352-99] oracle_before  fraction=0.000 regex=0.00 pair=0.00 bool=0.00 tokens=1200 s=154
[352-99] oracle_focal_first fraction=0.000 regex=0.00 pair=0.00 bool=0.00 tokens=1200 s=150 ins=2/131tok echo=44 eos=False
[352-99] oracle_focal_every fraction=0.000 regex=0.00 pair=0.00 bool=0.00 tokens=1200 s=159 ins=2/131tok echo=0 eos=False
[352-99] oracle_periodic fraction=0.000 regex=0.00 pair=0.00 bool=0.00 tokens=1200 s=163 ins=1/823tok echo=41 eos=False
[314-49] base identity=True tokens=216 pkg 29.3s loop 29.6s
[314-49] base           fraction=0.136 regex=0.00 pair=0.11 bool=0.29 tokens=216 s=29
[314-49] oracle_before  fraction=0.364 regex=0.17 pair=0.44 bool=0.43 tokens=393 s=53
[314-49] oracle_focal_first fraction=0.000 regex=0.00 pair=0.00 bool=0.00 tokens=1200 s=161 ins=2/158tok echo=0 eos=False
[314-49] oracle_focal_every fraction=0.182 regex=0.00 pair=0.11 bool=0.43 tokens=308 s=42 ins=1/27tok echo=0 eos=True
[314-49] oracle_periodic fraction=0.000 regex=0.00 pair=0.00 bool=0.00 tokens=1200 s=161 ins=1/352tok echo=50 eos=False
[186-14] base identity=True tokens=517 pkg 68.5s loop 68.8s
[186-14] base           fraction=0.222 regex=0.20 pair=0.00 bool=0.33 tokens=517 s=69
[186-14] oracle_before  fraction=0.556 regex=0.40 pair=1.00 bool=0.67 tokens=168 s=23
[186-14] oracle_focal_first fraction=0.444 regex=0.40 pair=0.00 bool=0.67 tokens=324 s=45 ins=2/79tok echo=0 eos=True
[186-14] oracle_focal_every fraction=0.444 regex=0.40 pair=0.00 bool=0.67 tokens=325 s=45 ins=3/135tok echo=0 eos=True
[186-14] oracle_periodic fraction=0.000 regex=0.00 pair=0.00 bool=0.00 tokens=1200 s=160 ins=1/117tok echo=0 eos=False
```

Observed failure modes (my diagnosis so far):

1. The `# Convention:` list is an attractor: the model continues it with hallucinated rules (`'gn_' prefix`, `use a set for quick lookups`), copies the block, and later self-imitates inside bodies (`# Convention: always include a try block` repeated until the cap) → greedy degeneration. Keyword re-feed stops continuation at the cue site but not later self-imitation.
2. Bug: re-fed keyword carried a trailing space → `from  pedantic` (fixed: no trailing space).
3. Bug: per-unit cooldown marked the FIRST function unit as delivered when the cooldown was unmet, so function rules were never delivered in `focal_every` on 314-49 (fixed: cooldown applies to repeat deliveries only).
4. Bug: the periodic control's line counter was not string-aware and inserted the block inside a docstring (fixed).
5. Even with correct delivery the model follows a subset (e.g. `a_` prefix, annotations, docstring: yes; `_b` suffix, `chx`, `@retry`/`@require_kwargs`, try: no) when 9 rules arrive at one function; the before-request arm on the same item stacked 13 decorators on one function and followed more rules.
6. Item 352-99 has 51 live rules; every arm including `before` scores 0 and degenerates (repetition of `self.chx = "chx"`).
7. Planned format change: one compact line `# Apply here: r1; r2; ...` instead of a list, to remove the list attractor.

## Questions (answer each concretely, with citations where literature exists)

A. Root cause of the comment-imitation/degeneration: is it the list format, the comment channel itself, greedy decoding, the 4B model, or the in-code position? What is the strongest evidence-based fix that keeps the shipped decoding (greedy) identical across arms? Consider: single-line cue; cue as a docstring-like string; cue phrased as an instruction to the reader vs a statement; delivering the cue in the *prompt side* as an interjected user turn (`<|im_end|>...<|im_start|>user ... <|im_start|>assistant` continuation) versus inside the assistant's code; terminators; repetition-blocking constraints (no-repeat n-gram) applied equally to all arms; and anything else from the literature on mid-generation intervention formats (Thinking Intervention variants, SafeRemind, Answer Engineering's candidate phrases, Hydra's diagnostic comments).

B. Rule load at one unit: 9-14 rules per function/import. What delivery policy do prospective-memory / checklist / stacking-collapse results recommend (split by sub-kind such as name vs decorator vs body; deliver name rules at the header and body rules after the docstring; cap per cue; prioritise rules the model is currently violating)?

C. Is there a design flaw in rolling back to the line start? For decorators the cue lands above the first `@` (right). For names the model chooses the name after the keyword (right). For `try`/`assert`/docstring rules the point of action is inside the body: should those be delivered at the first body line instead of the header?

D. Any other bug you can see in `focal_runtime.py` / `focal.py` (offset arithmetic after rollback, delivered-set bookkeeping, echo stripping, keep-piece handling, periodic control) — cite line numbers.

E. What would you run next as the single most informative pilot (arms, items, cap), before deciding the direction is futile on this model? Give a kill criterion.

Output: Markdown, findings numbered, each with a one-line recommended change; end with a ranked list of fixes to apply first.
