# Check40e — does router bias generalize beyond languages?

Unregistered user-authorized quick check, 2026-09-05, seed40050. Fit/train: none.
Profile-on: 16 synthetic competence tasks per pair, each cued both ways, all replies
used without success filtering. Evaluate-on: 32 new tasks per pair, disjoint input
values/statements from competence; no benchmark/sealed IFEval/BFCL inputs read.
P1 Python vs TypeScript: Go/gofmt absent on CPU, so use requested TS fallback.
P2 JSON rows vs SQL: tiny table and filter, both outputs semantically executable.
P1 inherits check40 system prompt; P2 uses its format-neutral concise counterpart
because the inherited system explicitly requests a function. Uncued P2 asks for
matching rows as a list (no JSON language cue); text cue explicitly overrides format.
OFF distribution is generated and reported first per pair, without prompt selection.

Frozen before outcomes: Qwen3-30B-A3B bf16, same loader, tuple-aware raw-router
hook, greedy fresh KV, thinking disabled, cap64, alpha3 sustained on all prefill
and decode positions/all48 layers. No grid, cap rescue, retries or outcome tuning.
Competence16 per side requires >=14 semantically correct unbroken addressed replies;
otherwise pair INELIGIBLE and no bias screen. Profiles are token-weighted mean raw
router logits at generated non-EOS own positions via teacher forcing of exactly
those32 replies. Bias=3*(side profile - two-side mean); swapped opposite direction;
shuffled expert-index permutation per layer seed40052 with matched per-layer norms.
Report all layer top8 IDs/intersection fractions. Inherit 40b same-experts gate:
if overlap>90% in EVERY layer, pair INELIGIBLE; no alternative profile selection.
Screen32 uncued tasks: OFF first, then correct/swapped/shuffled/text-cue per task.
P1 target TypeScript; P2 target SQL. Text cue visible, no bias. Other arms uncued.

Executable checkers: P1 Python AST or installed TS parser plus type-annotation
presence, transpile to JS, JS parser and execution of one arithmetic-only named
zero-argument function. Allowed arithmetic: integers, parentheses, unary +/- and
binary +,-,*. Require exact requested name and numeric answer; no fence-label
credit. Untyped valid JS is recorded separately and outside the paired checker.
P2 parse JSON list of objects with exactly integer id/value fields, or restrict SQL
to SELECT * / id,value FROM items WHERE one numeric comparison (optional ORDER BY
id, optional semicolon), then execute via in-memory SQLite. Compare row multisets
to an independently computed Python reference. No arbitrary generated-code exec.
Breakage = truncation, fence error, invalid/out-of-pair syntax, or wrong semantics.
This stronger semantic bar is deliberate; raw identity and semantic counts separate.
GENERALIZES iff correct addressed AND semantically correct >=20/32, correct
breakage<=2/32, shuffled addressed AND semantically correct<=4/32. Else MARGINAL
iff correct>=12/32, else NOT. Ineligible/incomplete are reported literally. If
resource-only projection requires16 tasks, thresholds scale to10/16,1/16,2/16;
MARGINAL6/16; label any such reading reduced exploratory screen. No data selection.
OFF default fails descriptively if expected side<20/32; report absence of a clear
default and paired flips, do not redesign prompts or claim paired flips from target
outputs already present OFF. Non-language transfer is stated independently of P1.

Cost: 64 competence +320 screen generations and64 teacher-forced profiles.
Prior measured conservative15.05 tokens/s; cap-based total with load600s,
1s per generation/profile and25% reserve: (600+384*64/15.05+448)*1.25=3351.196s
(<3600s). Both32-task screens provisioned; after competence use measured slowest
capped generation estimate (including prefill) for resource-only reduction before
any screen. Cooperative per-token deadline reserves cleanup; never signal/terminate.
Charge model load, kernel checks, profiles, checkers and cleanup to one GPU hour.
Foreground only; coordinate all quick-check RUNNING.flag files under review lock,
wait for other compute users; Brian pid2705 exempt and never touched. No push.
