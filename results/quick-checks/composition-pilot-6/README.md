# Composition pilot 6 — INELIGIBLE

**Failing gates:** R final<5/8.

R final failures: all8 fail the indent check,6 fail format, and3 also have breakage/integration failures. These checker categories overlap; an indent failure does not by itself identify its cause. The single non-write is T DEV04 turn12 (syntax_error). All round0 replies parsed and wrote files.

Completed phase: main, 16 rounds, 640 saved records. Q qualified 0/8. DEV diagnostics only; no fitting or larger-bank execution.

| Arm | Round0 not written | Lanes executing | Written rounds | Caps | Final success | Model/reference x |
|---|---:|---:|---:|---:|---:|---:|
| R | 0/8 | 8/8 | 128/128 | 0/128 | 0/8 | 1.066 |
| N | 0/8 | 8/8 | 128/128 | 0/128 | 4/8 | 1.061 |
| T | 0/8 | 8/8 | 127/128 | 0/128 | 3/8 | 0.997 |
| Q | 0/8 | 8/8 | 128/128 | 0/128 | 2/8 | 1.016 |
| O | 0/8 | 8/8 | 128/128 | 0/128 | 0/8 | 1.066 |

A lane executes when at least one round parses its trailer and writes its file. Per-round execution remains separately reported and gated at90% by this task. Caps, syntax/depth errors and failed writes do not execute. Final success uses the complete frozen T floor; Q qualification instead requires every fresh task to pass all traits. Q final-row success in the table is not Q qualification. Model output includes EOS, reference denominator excludes EOS, matching pilot5 reporting.

| T trait / kind | Pinned satisfied/applicable | Strict written satisfied/applicable | Qualifies (both) | Opportunity episodes |
|---|---:|---:|---|---:|
| language / language | 111/128 | 111/128 | True | 0 |
| indent / style | 23/39 | 23/39 | True | 8 |
| format / format | 23/35 | 22/35 | True | 8 |
| delivery / process | 48/49 | 48/49 | True | 8 |
| delivery_scope / process | 0/44 | 0/44 | False | 0 |

Indent floor counts applicable rounds at/after the registered first supersede, including reinstatement. Other denominators retain Amendment3 semantics. The pinned checker marks the syntax-error T reply observed and counts its format satisfaction:23/35. Strict written accounting treats that attempt as a failure:22/35. Both pass; all other counts and the eligible-trait set are identical. The gate reading is unchanged under strict accounting. Only indent/style and delivery/process count toward the two-substitution-kind gate.

**Matched-cell diagnostic.** Pilot5 prior post-change indent: R0/9 vs N8/9 vs T8/9. Matching conditions on execution and is descriptive, not a causal estimate.

| Matching arms / scope | Cells | Trait | R satisfied/applicable | N | T |
|---|---:|---|---:|---:|---:|
| RNTQ / all_matched | 127 | language | 80/127 | 80/127 | 111/127 |
| RNTQ / all_matched | 127 | indent | 7/127 | 20/127 | 23/127 |
| RNTQ / all_matched | 127 | format | 9/34 | 34/34 | 22/34 |
| RNTQ / all_matched | 127 | delivery | 49/49 | 40/49 | 48/49 |
| RNTQ / all_matched | 127 | delivery_scope | 0/44 | 0/44 | 0/44 |
| RNTQ / post_indent_change | 38 | language | 23/38 | 23/38 | 32/38 |
| RNTQ / post_indent_change | 38 | indent | 7/38 | 20/38 | 23/38 |
| RNTQ / post_indent_change | 38 | format | 7/31 | 31/31 | 19/31 |
| RNTQ / post_indent_change | 38 | delivery | 7/7 | 3/7 | 7/7 |
| RNTQ / post_indent_change | 38 | delivery_scope | 0/0 | 0/0 | 0/0 |
| RNT / all_matched | 127 | language | 80/127 | 80/127 | 111/127 |
| RNT / all_matched | 127 | indent | 7/127 | 20/127 | 23/127 |
| RNT / all_matched | 127 | format | 9/34 | 34/34 | 22/34 |
| RNT / all_matched | 127 | delivery | 49/49 | 40/49 | 48/49 |
| RNT / all_matched | 127 | delivery_scope | 0/44 | 0/44 | 0/44 |
| RNT / post_indent_change | 38 | language | 23/38 | 23/38 | 32/38 |
| RNT / post_indent_change | 38 | indent | 7/38 | 20/38 | 23/38 |
| RNT / post_indent_change | 38 | format | 7/31 | 31/31 | 19/31 |
| RNT / post_indent_change | 38 | delivery | 7/7 | 3/7 | 7/7 |
| RNT / post_indent_change | 38 | delivery_scope | 0/0 | 0/0 | 0/0 |

All-five-arm matched cells also appear in summary.json. Post-change scope uses each DEV episode’s actual first indent supersede; per-trait applicability is then applied. Zero denominators are unmeasured.

| Arm | Kind | Relapse / executed-trait opportunities | Prior trait present |
|---|---|---:|---:|
| R | format | 25/35 | 35 |
| R | language | 0/0 | 0 |
| R | process | 0/11 | 11 |
| R | style | 19/39 | 19 |
| N | format | 0/35 | 35 |
| N | language | 0/0 | 0 |
| N | process | 9/11 | 11 |
| N | style | 6/39 | 24 |
| T | format | 12/34 | 34 |
| T | language | 0/0 | 0 |
| T | process | 1/11 | 11 |
| T | style | 6/38 | 21 |
| Q | format | 0/35 | 0 |
| Q | language | 0/0 | 0 |
| Q | process | 0/11 | 0 |
| Q | style | 0/39 | 0 |
| O | format | 25/35 | 35 |
| O | language | 0/0 | 0 |
| O | process | 0/11 | 11 |
| O | style | 19/39 | 19 |

Kind totals sum trait-opportunity cells; each denominator requires a written file and the checker’s retirement opportunity. The numerator additionally requires the prior trait to have appeared. Trait-level counts and original raw checks remain in summary and records. Q has fresh gold prerequisite files, so its prior-history witness can differ from trajectory arms.

**Measured larger-test projection: 7.651751 GPU-h.**
GPU held 4414.921/9000s; startup 488.424s. Formula `(load + 1.25*(64*(R+N+Q)+16*(O+T)))/3600`. All five costs measured from fixed same-arm C4 groups, with phase overhead allocated equally. Startup charged once; all pilot replay and cleanup time is included in the9000s actual budget. Prior development cost is excluded from this task’s registered projection.

The (12,15]h fresh12-round fallback was not triggered.

Determinism: D=0/8, exact body token IDs/EOS/cap across forward/reverse C4. Saved-response CPU audit: 640 replies, zero payload or record mismatches. Own container and flag absent; no host process signals or push.

Artifacts: [summary](summary.json), [records](main-records.jsonl), [audit](audit.json), [HTTP hash index](journals-index.jsonl), [local hashes](local-hashes.json), [server log](server.log), [launcher](run.py). HTTP bodies and workspace/loop journals are local, out of git. Compact records are below10MB.

---

# Composition pilot 6 — registered before GPU execution

Fit-on: none. Evaluated-on: eight authored SLAB-2 DEV episodes only; no benchmarks or sealed evaluation content. User explicitly authorizes full pilot after the budget-limited screen; no screen rerun.
Pinned CPU-green SHA: `4ab3e21884e0e5decd6d4fd78607abd6a69cf95d`, isolated `/tmp/stencil-pilot6-pinned`; HEAD, tracked cleanliness and source resolution verified before GPU access. Cap2048, qualified invariant bf16 vLLM image and flags copied exactly from vllm-qual, own container/port18087. Budget9000s includes startup, replay, all phases and cleanup. Only own Docker stop/rm; no process signals.

Pre-run determinism: eight DEV round0 R prompts, C4 forward0..7 then reverse7..0; exact body IDs/EOS/cap, D=0 required. Fixed trajectory schedule: Q,R,N,T,O in that order, DEV00..03 then04..07 in each arm, four workers with group barriers; 16 dependent rounds/lane. O is measured cost only. Q precedes all trajectories. Same-run HTTP/loop journals remain outside git with hashes; compact records retain output hashes.

PRE-WRITTEN READINGS: ELIGIBLE requires complete eight episodes, zero round0 format failures, per-lane8/8 and strict per-round execution>=90% in each R/N/T/Q arm, caps<=2% per arm, both primary substitution kinds (indent/style and delivery/process) passing corrected T floor with nonzero retirement denominators in >=2 episodes, R final>=5/8, and measured Q-inclusive64 projection<=12GPU-h. Missing/capped/failed T attempts remain failures; indent denominator uses applicable post-supersede rounds including reinstatement. Other floors unchanged by Amendment3. We conservatively require the same execution checks for cost-only O too.
Cost=(load+1.25*(64*(R+N+Q)+16*(O+T)))/3600; lane mean=group wall/4 with intergroup overhead allocated. Replay is charged to pilot budget; startup load is charged once in projection. In (12,15], frozen fresh12-round DEV fallback, all five arms retained, if budget permits; insufficient remaining budget => INCOMPLETE, never partial pass. >15 => stop. INELIGIBLE lists failing items; interrupted/incomplete work => INCOMPLETE.
Diagnostics frozen: matched episode/turn cells where every R/N/T/Q arm wrote, per-trait R/N/T satisfied/applicable and post-change counts; also report R/N/T-only matched cells to compare pilot5 prior post-change indent R0/9,N8/9,T8/9. Per-kind relapse uses executed-trait retirement denominators. No larger64 run in this task.

## Orchestrator addendum after the Opus maximum-reasoning review (2026-09-07; results/composition-pilot-6-review-opus.md)
Every number reproduces; INELIGIBLE on `R final<5/8` is correctly applied. Five decisive corrections:
1. FORMAT IS A RENDERER DEFECT, proven by a control already inside this run: the fresh-context arm Q renders the
   SAME block with no history, tombstones or context and reproduces R's failure (Q 11/34, R 9/34) while the
   block-free arm N is 34/34. Named bytes: register.py:437-449 sorts the task-scoped `delivery` row LAST, right
   before "Apply the active rules..."; renderer.py:90-106 never composes it with `format=compact`; slab2.py:107
   renders it as the actionable imperative "trailer delivery=ready...". R prints `delivery=ready` in 25/34 compact
   rounds; N never does.
2. INDENT IS NOT A BLOCK-CONTENT DEFECT: Q with the same block is the BEST arm (59/127 vs R 7, N 20, T 23). It is
   context accumulation (loop.py:363 re-appends the whole block every turn; R 13.2k tokens vs N 6.4k) plus genuine
   model behaviour (PEP-8 default; copying the file's existing style; T even emitted an indentation error trying to
   obey "indent 3"). Episode-paired, indent R 7/127 vs N 20/127 gives p = 0.125 — NOT significant; the round-level
   appearance was pseudo-replication.
3. JOINT FINAL SUCCESS IS NOT A MEASURABLE ENDPOINT FOR ANY ARM. Q qualified 0/8 under both rubrics; the 4-trait
   per-round conjunction is Q 48/128, N 18, T 16, R 4, with all-arms-agree 0/128 and the 16-round conjunction 0/8
   everywhere. The registered larger test on this endpoint would be a foregone FAIL.
4. AT THE CORRECTED ENDPOINT THE REGISTER ARM ALREADY WINS WHERE IT SHOULD: per-obligation adherence at the
   obligation's change round, episode-paired — delivery R 8/8 vs N 1/8 (p = 0.0156) and R 49/49 vs N 40/49
   (p = 0.0156); format R 2/8 vs N 8/8 (p = 0.0312, the defect above); indent R 4/16 vs N 9/16 (p = 0.125).
5. Free receipt: the O arm is byte-identical to R across 128/128 output hashes (renderer.py:136 treats O as R) —
   a 128-round determinism replication, and 0.587 GPU-h of the projection buying a duplicate. Cost confirmed at
   7.651751 GPU-h INCLUDING Q at x64 (Q adds 1.836; 7.064 without O).
REGISTERED CONSEQUENCE: the 64-episode larger test must NOT run on joint final success. It IS authorized at
7.65 GPU-h on the PER-OBLIGATION CHANGE-ROUND endpoint with episode-level pairing, after (a) the delivery x format
composition defect is fixed and (b) a ~1.2 GPU-h DEV re-pilot confirms it. Pre-registration changes required:
swap the primary endpoint, declare the episode the unit, drop `delivery_scope` (0/44 in all five arms, and scored
only against Q), de-conjoin style/language from breakage, fix the vacuous `widths==[]` pass, re-label Q as a
fresh-context reference rather than a ceiling, and declare O.
