# Quick check 40e for gpt-6-astra: does the router bias generalize beyond languages? (2026-09-05)

Source: checks 40b/40c (router bias alpha 3 flips Python -> JavaScript 32/32 with 0 broken; shuffled 0). Question: is
this specific to programming languages, or a general skill selector? Reuse the 40b/40c plumbing (model, hook, profile
extraction, alpha 3 sustained, 64-token caps, shuffled/OFF/text-cue arms, seeds 40050). Two NEW pairs, each with an
executable checker and a clear uncued default:
 P1 (third language): Python vs Go (checker `gofmt -e` / `go vet` if installed — verify on CPU first; else Python vs
    TypeScript via a JS parser + type-annotation detector). Bias direction = the Go (or TS) profile.
 P2 (NON-language skill): a tiny in-prompt table + filter request whose uncued default is a JSON list of rows; bias
    toward the "SQL" expert profile extracted from cued "Answer with a SQL query" generations; checker: parse a
    restricted SELECT/WHERE and execute it against the table, compare with the JSON-rows reference (both arms
    semantically checkable). Report the OFF default distribution first.
Per pair: competence 16/16 cued each side (>= 14/16), profiles + top-8 overlap, then a single-shot SET screen on 32
uncued tasks (correct / swapped / shuffled / OFF / text-cue). READING (fixed before running, per pair): GENERALIZES if
correct induces the addressed skill >= 20/32 with breakage <= 2/32 and shuffled <= 4/32; MARGINAL >= 12/32; else NOT
for that pair. State plainly which pairs flip and whether the non-language pair does. Cost cap 1 GPU-h total (project
first; scale to 16 tasks if needed and record). Outputs under results/quick-checks/check40e/; item 40e in
results/quick-checks/README.md (5 lines); WORKLOG entry (<= 6 lines). Commit with explicit pathspecs (git add -f for
results); no push. Foreground only; never terminate or signal any process; never read the sealed IFEval input file or
the sealed BFCL cohort contents; nothing fit or trained.
