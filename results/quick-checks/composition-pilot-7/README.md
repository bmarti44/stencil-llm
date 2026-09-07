# Composition pilot 7 — INELIGIBLE

Fit-on: none. Evaluated-on: eight authored DEV episodes; no benchmark or larger-bank model execution.

Failing items: compact delivery=ready>2/34 or missing. The larger test is not authorized by this re-pilot.

Fixed pilot-6 compact control: R delivery=ready **4/34** (limit 2), format adherence **30/34** (minimum 26). These are the same 34 cells, without outcome-dependent rematching. CPU re-render control: contradiction removed on all 34 matched and all 35 scheduled compact registers.

Remaining R delivery=ready cells: slab2-dev-06 round 12, slab2-dev-06 round 13, slab2-dev-06 round 14, slab2-dev-06 round 15. Literal trailers are retained in summary.json and report-audit.json.

| Arm | Written | Round0 written | Executing lanes | Caps | All35 compact format | All35 ready emissions | Joint final (descriptive) | Breakage episodes (descriptive) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Q | 128/128 | 8/8 | 8/8 | 0/128 | 1/35 | 34/35 | 0/8 | 3/8 |
| R | 127/128 | 8/8 | 8/8 | 0/128 | 30/35 | 4/35 | 3/8 | 3/8 |
| N | 128/128 | 8/8 | 8/8 | 0/128 | 32/35 | 3/35 | 2/8 | 3/8 |
| T | 128/128 | 8/8 | 8/8 | 0/128 | 19/35 | 12/35 | 2/8 | 3/8 |

Primary: per-obligation change-round adherence conditional on paired parsed writes. Changes within an episode are averaged before one episode sign enters the exact one-sided R>N test; Holm across three families. The arm-count columns include each arm's written change events; the exact test uses common R/N events within each episode. Nonwrites are reported, with failed-attempt sensitivity in summary.json. DEV significance is descriptive and does not gate eligibility.

| Obligation | R adhered/written changes | N | T | Q | Paired episodes | R wins / N wins | One-sided p | Holm p |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| indent | 10/15 | 11/16 | 12/16 | 5/16 | 8 | 1 / 1 | 0.750000 | 1.000000 |
| format | 7/8 | 8/8 | 4/8 | 0/8 | 8 | 0 / 1 | 1.000000 | 1.000000 |
| delivery | 8/8 | 1/8 | 7/8 | 8/8 | 8 | 7 / 0 | 0.007812 | 0.023438 |

Computable endpoint: 3/3 families in >=6 episodes; 8/8 episodes each have >=2 measured families.

| Strict T floor | Satisfied/applicable | Eligible | Retirement-opportunity episodes |
|---|---:|---|---:|
| language | 128/128 | True | 0 |
| indent | 29/39 | True | 8 |
| format | 19/35 | True | 8 |
| delivery | 48/49 | True | 8 |

Floor uses all scheduled T attempts, nonwrites as failures; indent counts at/after first supersede including reinstatement. Style and language adherence are independent of runtime/semantic breakage. delivery_scope is removed from every arm. Joint final uses the same four traits for all arms and is descriptive only.

Q is a **fresh-context reference**, using gold prerequisite files without feedback, not a capability ceiling. O is omitted: its rendering is byte-identical to R; pilot6 already recorded 128/128 identical outputs. That replication cost 0.587 projected GPU-h.

Measured larger-test projection: **6.99 GPU-h** (limit 12). Formula `(load+1.25*(64*(R+N+Q)+16*T))/3600`; fixed same-arm C4 lane allocations, startup once. Pilot6's identical R/O timing spread suggests roughly 4% timing noise; unrounded measurements decide the gate.

Actual GPU-held: 3533.4/5400s including startup, determinism and cleanup. Startup 497.5s. Determinism D=0/8, exact body IDs/EOS/cap under forward/reverse C4. Max prompt+cap: 10994+2048 <=32768.

Pinned CPU-green SHA: `24ed80a49edcea3359d0c45d361daf7fdf761745`; isolated `/tmp/stencil-pilot7-pinned`. Required CPU suite and CLI smoke passed before GPU launch. Saved-response audit verifies all 512 prompts/payloads and record fields; own container and flag removed. No host process signals or push.

Artifacts: [summary](summary.json), [records](main-records.jsonl), [saved-response audit](audit.json), [registration](registration.md), [CPU validation](cpu-validation.log), [determinism](determinism.json), [lifecycle](lifecycle.json), [local hashes](local-hashes.json), [composition control](composition-control.json), [report audit](report-audit.json). Records are below 10 MB; full HTTP and loop journals are local and hash-indexed.
