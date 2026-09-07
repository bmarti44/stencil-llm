## SLAB-2 Amendment 4 — registered 2026-09-07 BEFORE code

STATE: CPU repair and endpoint implementation next; this report is the task write-ahead
ledger, following Amendment 2's archived-protocol disposition. User authorizes this
repair and DEV pilot 7. Source: results/composition-pilot-6-review-opus.md (fully read)
and pilot-6 README addendum. Fit-on=none; evaluated-on=eight authored DEV episodes;
saved DEV pilot-6 registers/responses are diagnostic controls, never fitting data.
No data/bench or evaluation-bank content is read or generated in this task.

Renderer: suppress the delivery row in the live rendered view when the applicable
format value is literally compact; retain register state/value and verbose rendering.
Composition is independent of arm and applies wherever that live view is rendered,
including fresh-context Q. Preserve literal values; no inference from user prose.
Remove live-row provenance/scope metadata and redundant style gloss; retirement text
identifies the retired version and reason only, never retargets to a current version.
Control: re-render saved pilot-6 registers on the exact 34 R/N/T/Q matched compact
cells (the 35th compact cell was an unwritten T attempt), asserting no delivery
imperative remains. Also check all 35 scheduled compact cells, other values/scopes,
unchanged register state, and O/R byte identity. Old results/reading stand.

PRIMARY: per-obligation change-round adherence, R versus N, episode as the unit.
Families fixed: indent/style, format/format, delivery/process. For each key's
supersedes/completes/cancels/reinstates event, select the first applicable scheduled
round at/after the event and before the next effective change; coalesce same-key
same-round events (cancel+reinstate is one effective change). Never substitute a
later successful execution. A paired event is measured only when both R and N
parse and write at that scheduled round; report missing events explicitly and
strict failed-attempt sensitivity (missing write=0) alongside conditional adherence.
Per episode/family compare the mean adherence over common measured events; the
sign of that difference contributes ONE win/loss/tie. Exact one-sided binomial sign
test on discordant episodes, H1 R>N, alpha .05, Holm across the three fixed families;
zero discordances p=1, zero paired episodes unmeasured, never PASS. Larger-test
primary family PASS requires Holm-adjusted p<=.05 and positive mean paired gain;
report each family separately, no joint-final or Q-qualified-subset gate. Overall
primary evidence requires >=1 family PASS; execution/caps/floor/cost remain separate.
Language and style are conditional on parsed file writes, independent of semantic
or runtime breakage; indent requires nonempty measured widths. Breakage remains a
separate episode-paired descriptive outcome. Joint final success is DESCRIPTIVE only.
Drop delivery_scope from every arm's trait set; Q uses the same four traits and is
a FRESH-CONTEXT REFERENCE (gold prerequisites, no feedback), never a ceiling.
O is byte-identical to R by construction; pilot6 provides 128/128 output-hash
replication. DROP O from pilot7 and larger test: another duplicate would consume
0.587 GPU-h projected without new science. Keep compatibility rendering and its test.
New measured projection: (load+1.25*(64*(R+N+Q)+16*T))/3600, four-worker same-arm
lane allocations, startup once. Historical five-arm functions/results remain legacy.

Pilot7: only after explicit-path CPU commit, required tests green, and a separately
recorded pinned SHA; isolated clean checkout and source resolution verified before
GPU. Eight DEV x16 rounds x Q/R/N/T, same-arm C4 groups 00..03 then04..07; Q first.
Qualified invariant bf16 image/flags from pilot6; cap2048; determinism replay first,
eight round0 R prompts forward/reverse C4, exact body IDs/EOS/cap D=0 required.
Budget <=5400 GPU-held seconds including startup/replay/cleanup; own RUNNING.flag,
wait for other Stencil flags/compute; never signal a host process or touch Brian's
server. Only stop/rm this run's container. No 12-round fallback in this bounded task.
PRE-WRITTEN READING: ELIGIBLE iff complete 512 records, D=0, R compact delivery=ready
emissions<=2/34 AND format adherence>=26/34 on the FIXED pilot6 34-cell control set
(no outcome-dependent rematching), zero round0 nonwrites, 8/8 executing lanes and
>=90% written rounds in each arm, caps<=2% per arm, context+2048<=32768, both
indent/style and delivery/process pass strict T floor>=50% with retirement
opportunities in >=2 episodes (Amendment3 indent denominator), primary endpoint
nonzero paired denominators for >=2 families in >=6 episodes each, measured larger
projection<=12GPU-h, and actual budget<=5400s. Report all35 compact cells too.
ELIGIBLE authorizes the larger64 test on this endpoint; do not launch it in this
task. Otherwise INELIGIBLE naming failed items (INCOMPLETE for interrupted records).
No significance or joint final success requirement gates DEV eligibility.
Validation: tests/test_focus_slab2*.py + tests/test_no_side_effect_imports.py;
regressions for every item, saved-register composition control, CPU driver smoke.

Amendment 4 CPU verification: required selection **135 passed, 1 expected xfail,
70.45s**; full 512-call DEV CPU-stub driver and artifact consumer pass. Saved
register versions/live views reproduce exactly on all35 compact cells; all34
matched cells lose the contradictory delivery imperative. Two historical tests
were corrected because they relied on empty-diff indent passing. Lint/whitespace
pass. Episode schedules/manifests are unchanged; only source/dependency hashes
and Amendment4 metadata were refreshed. The requested existing CPU suite includes
automated synthetic reference/manifest checks; no benchmark files or evaluation
prompts/results were inspected, and no model evaluation-bank execution occurred.
Conservative denominator clarification before GPU: additionally require >=6 episodes
each with >=2 nonzero paired family denominators (not merely separate six-episode
sets). No threshold is selected using new model output.

Amendment-4 **pinned CPU-green SHA: `24ed80a49edcea3359d0c45d361daf7fdf761745`**.
Isolated `/tmp/stencil-pilot7-pinned`, tracked tree clean; required post-commit suite:
**135 passed, 1 expected xfail, 70.80s**; pinned CLI CPU smoke PASS. Initial isolated
validation failed solely because its gitignored tokenizer was absent (105 failed,
30 passed, 1 xfail); linking the existing local model directory repaired the setup,
with no source changes. Final log: composition-pilot-7/cpu-validation.log. All35 saved
compact rule blocks:17126 old tokens ->8412 new tokens; zero delivery imperatives.
Pilot7 launches next from this SHA; determinism first, <=5400 GPU-held seconds.

Launcher: scripts/composition_pilot7.py from the pinned checkout.
