# Build brief (CPU only) for gpt-6-astra: SLAB-1 bank fixes after fable's review (2026-09-06)

Fable's review results/slab-bank-review-fable.md found the bank cannot run the registered test as built. Read it
fully (file:line cited) and fix ALL four HIGHs and the MEDIUMs in src/stencil/focus/slab.py (+ loop.py transport
where named), then re-freeze manifests/goldens. Use the REAL Qwen3 tokenizer for all token accounting from now on
(models/qwen3-30b-a3b-hf tokenizer files only; CPU; no weights).
H1 Context overflow: R's 32-round prompt reaches 48,322 model tokens (N 38,478) — tool results serialised twice per
   envelope (slab.py:936-937 via loop.py:220-229) and a full-file read excerpt every round. Dedupe the serialisation,
   bound read excerpts by a fixed identical-across-arms excerpt policy with artifact refs, and make the whole 32-round
   episode fit <= 32,768 tokens for EVERY arm with margin (report the max per arm from a tokenizer dry run of all 64
   + 8 DEV episodes); overflow must be symmetric by construction (same policy, same budget).
H2 Own-body length: trunk-token own bodies are 59-82, registered band 100-300. Make the reference/expected bodies
   (and the tasks that elicit them) naturally 100-300 model tokens (larger functions, docstrings allowed, small
   helper) without inflating context beyond H1's budget; report the distribution from the tokenizer dry run.
H3 Interpreter breakage: the restricted expression interpreter + append-only edits make docstrings/annotations/
   abs/max/in/genexp permanent unrepairable breakage. Replace with real Python execution in a subprocess sandbox
   (resource-limited, no network, timeout) for both public tests and hidden checkers; allow file rewrite edits
   (replace-range or whole-file) so repair is possible; keep breakage = malformed tool call / invalid program /
   empty-capped generation only.
H4 Template sharing: one lifecycle schedule in 48/64 episodes; 18/36 request scaffolds byte-shared across
   DEV/eval. Generate lifecycle schedules from a seeded sampler over >= 6 schedule shapes and vary keys/values;
   make DEV and eval template-disjoint by construction (test that no request scaffold string, schedule tuple or
   rule text is shared; keep the disjointness test strict).
M1 The post-completion default (`ready`) must appear in text every arm can see (the initial system/user setup),
   so the process witness is not information-rigged against N; ensure >= 3 delayed process opportunities per episode.
M2 Freeze a system prompt and include TOOL_SCHEMA / execution policy text in what the model sees and in the
   manifest hashes.
M3 Add a should-pass set beside the mutants (reference variants that must pass); add the prior-own-body trait field
   for relapse counting; separate post-reinstatement style relapse from PEP-8 prior by requiring the trait to be
   present in a prior own body.
LOW: vary the process witness script; drop vacuous public tests; bound T's tombstones to the same 3-window as R;
   add the data-lineage line to the manifest and WORKLOG.
Then re-run the full CPU dry run (all 72 episodes, stub decoder), regenerate goldens/manifests, and report: per-arm
max context tokens, own-body token distribution, relapse opportunity denominators per kind, and a GPU cost
projection at 15.4 decode tok/s with a stated prefill assumption (KV retained within an episode) for the 4 arms x 64
episodes + DEV pilot, against the 12 GPU-h budget.
Commit only src/stencil/focus/**, tests/test_focus_*.py, tests/fixtures/slab_*, tests/fixtures/focus_*, WORKLOG
(<= 6 lines) with explicit pathspecs; run all tests/test_focus_*.py + tests/test_no_side_effect_imports.py; no push;
no GPU (check 40k is running); never terminate or signal any process; never read anything under data/bench.
