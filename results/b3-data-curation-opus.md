# v4.2 synthetic data — manual curation (Opus 5)

**Verdict: DO NOT FREEZE.** Four required changes below. The v4.2 rewrite genuinely
fixed the word-salad problem — the 12 body sentences are clean, plausible English —
but it did not fix the thing that actually broke the last fleet. Two of the four
required changes are new instances of the *same* failure mode: the training signal
still tells the controller "when any constraint is present, everything is on."

Method: enumerated all 178 distinct sentence surface forms in the corpus and read
every one; read 211 stratified full rows (every constraint key × every combo size ×
both files) end to end; re-ran the official IFEval checkers (`instructions.py`,
repo venv) over all 2,200 canonicals and all 4,473 mutations to test targeting.

## What holds up

- **Machine verification is real.** 0/2200 canonicals fail their registered checkers;
  4473/4473 mutations do fail their target constraint. No vacuous passes found.
- **The 12-sentence natural pool is genuinely natural.** "The tools were laid out on
  a clean cloth within easy reach." reads like model prose. This is a large
  improvement over the previous filler.
- **Four mutation types are exemplary** — minimal, targeted, plausible:
  `placeholders` (`[tool name]` → `(tool name)`), `title` (strips `<<>>`),
  `kw_exist`/`kw_freq` (keyword → `item`), `postscript` (`P.P.S.` → `PS`),
  `two_resp` (`******` → `---`). 0% collateral damage on all of them.
- **No train/dev prompt leakage** (0/199 dev prompts appear in train).

## Required change 1 — 20% of mutations are not targeted (HIGH)

This is the finding that should block the freeze. Running every mutation against
*all* of its row's checkers:

| mutation | rows where it also breaks another constraint |
|---|---|
| `n_words_min` | 312/450 = **69.3%** |
| `n_sent` | 274/403 = **68.0%** |
| `bullets` | 163/277 = **58.8%** |
| `lower` | 41/221 = 18.6% |
| `caps` | 27/214 = 12.6% |
| `n_words_max` | 30/275 = 10.9% |
| `kw_forbid` | 48/472 = 10.2% |
| everything else | 0% |

**895/4473 mutations (20.0%), touching 713/2200 rows (32.4%).**

The cause is that the three big offenders are implemented as *truncation*, not as
violation. `mutations['n_sent']` for a row with combo `[n_sent, kw_freq, postscript]`
is literally just the opening sentence:

> `'Here is a short account of storing winter firewood for the neighborhood newsletter.'`

That fails `n_sent` — and also `kw_freq`, and also `postscript`, and also
`n_words_min` if present. `mutations['bullets']` is the first bullet alone.
`mutations['n_words_min']` is the response chopped mid-sentence, which additionally
flattens the newlines and so destroys the bullet count too.

Why this matters specifically: the controller's contrastive signal is
"canonical passes / this mutation fails constraint X." When a third of rows deliver a
mutation that fails X *and* Y *and* Z, the model cannot attribute the failure to X.
The gradient it sees is "any deviation breaks everything" — which is the
maximum-firing prior that cost the last fleet 11pts of dev adherence. The previous
dataset taught fire-everywhere through its canonicals; this one teaches it through
its negatives.

Fix: make each a minimal edit that holds all other constraints.
- `n_words_min`: delete one mid-document sentence to land just under the threshold.
- `n_sent`: merge two sentences (or drop one) to land at n−1, keeping keywords,
  postscript, title, placeholders intact.
- `bullets`: emit n−1 or n+1 bullets carrying the same content.

The four clean mutation types already prove the builder can do this. Also note the
secondary collisions are cheap to fix and worth fixing at the same time: `caps`
prepends a literal `x` before `*` (breaks bullets, 27 rows), `lower` substitutes `T`
for the leading `*` (breaks bullets, 41 rows), `n_words_max` appends lowercase filler
to an ALL-CAPS response (breaks caps, 30 rows), and `kw_forbid` appends a
capitalized "The harbor waits." to a lowercase-only response (breaks lower, 48 rows).

## Required change 2 — every bullets row is topic-blind (HIGH)

Overall topic-groundedness is 87.4% (1923/2200), and that number is entirely
structural: the topic appears only in the opener "Here is a short account of {topic}
for the neighborhood newsletter." The builder drops that opener whenever the format
is bullets. So:

| constraint | rows mentioning the prompt topic |
|---|---|
| `bullets` | **0 / 277 = 0%** |
| `n_sent`, `n_words_max`, `postscript`, `title`, `two_resp`, `json_fmt` | 100% |
| all others | 81–90% |

A complete v4.2 bullets row (dev key 7, prompt: *maintaining a community greenhouse*):

```
* The work began early in the morning while the street was still quiet.
* The tools were laid out on a clean cloth within easy reach.
* The weather held steady which made the whole task easier.
* Everyone agreed the effort was worth it once the results were visible.
* A few neighbors stopped by to watch and offered a hand where they could.
* In the end the small details made the biggest difference.
* By midday the hardest part was finished and the rest went quickly.
```

Nothing about a greenhouse. This is an equally valid target for all 30 prompts, and
in fact identical bullet bags appear under unrelated prompts. 12.6% of the corpus
teaches "constraint present → emit the generic bag," which is a formatting reflex
rather than a topic-conditioned response. Add a topic-bearing first bullet.

## Required change 3 — the wrappers are single memorizable literals (HIGH)

| wrapper | rows | distinct strings |
|---|---|---|
| title | 399 | **2** (`<<Notes From the Workshop>>` + its ALL-CAPS variant) |
| postscript | 367 | **1** (`P.P.S. the paint needs a second coat.`) |
| placeholder sentence | 469 | **1** (`Bring [tool name] and [location] and [time of day] and [helper name].`) |
| word-cap filler | 275 | **1** (`the quiet work continues through the morning …`) |

Three of the fourteen constraints can be satisfied by memorizing one literal string.
That is precisely a degenerate shortcut: the controller never has to learn *when* the
title constraint is active in a way that generalizes, only to reproduce eleven fixed
tokens. It is also a naturalness problem — a newsletter piece about a milk delivery
round titled "Notes From the Workshop", ending with a P.P.S. about paint, is a
non-sequitur in 100% of cases. Generate 20–30 topic-derived variants per wrapper.

## Required change 4 — the corpus has a 274-word vocabulary (HIGH)

The headline "2000/2000 distinct canonicals" is an artifact of shuffling a 12-item
bag. Real numbers:

- **178 distinct sentence surface forms in the entire 2,200-row corpus.**
- **12** natural body sentences, each appearing **861–934 times**.
- Those 12 sentences are **67.5% of all word tokens**.
- **189,025 word tokens carry 274 word types** (TTR 0.0014). Natural text of that
  length would have 8–15k types.
- Order-insensitively there are 1,177 distinct pool subsets, not 2,200 distinct texts.

The permutation shuffle is doing real work — 1,449 distinct openings in train, only
30 rows (1.4%) have an order-insensitive twin, so the model can't literally
memorize row→text. But it can trivially memorize the *pool*: at 900 repetitions per
sentence, next-token prediction inside a body sentence is free, and the only thing
carrying gradient is the wrapper/formatting decision. That is a narrow, brittle
signal for a controller whose whole job is selective firing on free generation.
Expand the pool to 60–100+ sentences, preferably topic-specific.

## Recommended (naturalness / structure)

- **`a awning` — 36 rows.** The carrier template hardcodes `a`:
  *"Someone had left a awning nearby, which saved a trip back home."*
- **Mass-noun countability — ~284 rows.** *"An old gravel from the shed…"*,
  *"a tallow"*, *"an old mortar"*. `gravel`, `tallow`, `mortar` are mass nouns; they
  need their own carrier templates.
- **Keyword-carrier non-sequitur — 724+ rows.** All four carriers use one
  shed/workshop frame regardless of topic. *Cleaning a telescope mirror* →
  *"An old tallow from the shed turned out to be surprisingly useful."* This is
  exactly the "keyword-carrier sentence that clashes with the topic" pattern. It's
  the single largest remaining naturalness defect by row count.
- **Lowercase postscript body — 367 rows.** `P.P.S. the paint needs a second coat.`
- **Run-on final bullet — 59 rows.** The placeholder sentence is appended to the last
  bullet: *"* Everyone agreed the effort was worth it once the results were visible.
  Bring [tool name] and [location] and [time of day] and [helper name]."* Two
  sentences in one bullet. The placeholder sentence itself ("and…and…and") is stilted.
- **`n_words_max` mutation is degenerate — 275 rows.** It pads with the same 24-word
  clause repeated 6–7× (~170 junk words). A minimal violation lands a few words over.
- **Casing mutations are typo artifacts — 394 rows.** `Tere is a short account…`,
  `x<<NOTES FROM THE WORKSHOP>>`, `hERE IS A SHORT ACCOUNT`. A plausible casing
  failure capitalizes a word or a sentence, not one character mid-token.
- **`and the steady pace holds` — 14 rows.** Word-count padding grafted onto a
  finished sentence: *"The final touches took longer than expected but came out well
  and the steady pace holds."*
- **`json_fmt` and `two_resp` are orphans.** 55/55 and 49/49 rows appear with no
  other constraint, and both are undersampled ~8× against the other twelve. The
  controller gets zero composition signal for them. JSON keys are positional
  `part_0`…`part_3` rather than semantic. The `two_resp` second reply is a bare
  two-sentence fragment with no opener — not the "complete reply" the prompt asks for.
- **Dev is not a generalization holdout.** Prompts don't overlap, but dev shares the
  identical 30 topics, the identical 12-sentence pool and the identical wrappers with
  train. Dev adherence will measure pool memorization. Hold out topics and/or pool
  sentences, or the metric that caught the last regression won't catch the next one.

## Bottom line

The naturalness rewrite worked at the sentence level and failed at the corpus level.
Required changes 1 and 2 are the ones I'd insist on before any GPU time: a 20%
non-targeted mutation rate and a 12.6% slice of topic-blind targets are both direct
routes back to the fire-everywhere controller. Changes 3 and 4 are what stop the
model from solving the task by memorization instead of by learning to fire
selectively. Changes 1, 2 and 3 look like small, mechanical builder edits.
