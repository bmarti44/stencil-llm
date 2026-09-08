Fit-on: none. Development-on: the same two audited Kimi conversations, exposed attempt-01 responses and synthetic CPU controls. Evaluated-on: none. This is deliberate DEV reuse; the reviewed rationale caveat remains excluded from verified supervision.

# Independent DEV accuracy review — attempt 02

2026-09-07 · Round 1 · Reviewer: gpt-6-astra, xhigh, native session `/root/maintenance_dev_result_review`. Explicit user-requested Astra xhigh replaces the historical Opus assignment. Author-disjoint from Sol's semantic revision, Kimi's data and the parent's execution/report. Purpose: audit actual maintenance under the unchanged prewritten reading; threat model: trusted but fallible model and operators. Source-only preparation preceded output access; responses were opened only after confirmed terminal exit and cleanup. Only this file was written. No inference, network/GPU access, old evaluation/benchmark reads, source/output edits or commits.

**Result: NOT PERFECT ON DEV — 0/48 complete semantic views, 0/16 entirely correct turns, 0/2 whole trajectories.** Each view lacks its required language/version obligation, independently of how partial dependency prose is interpreted. Both episodes fail their first standing instruction and never recover complete state. Some outputs contain more relevant content than attempt 01, but complete maintenance remains unsuccessful. Independent CPU replay verifies the receipts and actual state transitions; resource eligibility is satisfied.

## All 16 turns and 48 views

Indices are zero-based. Receipt `NNNN` means `calls/calls/call-NNNN.json`. Each row audits GLOBAL and both declared task views for `code_answer`; 0/3 is complete-view agreement, not a claim that every fragment is meaningless.

| Episode / turn (receipt) | Required maintenance | Actual transaction and resulting state | Correct views |
|---|---|---|---:|
| ETL 0 (0000) | Global Python 3.11 and contextual ETLError; never bare except | Accepts an empty transaction. Both standing obligations missing. | 0/3 |
| ETL 1 (0001) | Hold through explicit one-off pandas request | Accepts an ingest-scoped CSV-sniffing code snippet as a persistent process rule. | 0/3 |
| ETL 2 (0002) | Hold through explicitly unadopted Polars quote | Correctly proposes no change; preserves the already incorrect state. | 0/3 |
| ETL 3 (0003) | Tool text cannot change rules | Re-adds the snippet; rejected for non-user authority. | 0/3 |
| ETL 4 (0004) | Global standard-library-only policy with ingest requests permission | Accepts one global entry containing both conditional dependency policies in prose. Relevant content is present; language/error obligations remain absent and the one-off snippet persists. | 0/3 |
| ETL 5 (0005) | Python 3.12 across the project | Proposes relevant version text as an ingest-only add to the existing snippet key. Duplicate key/scope rejected; no language update applied. | 0/3 |
| ETL 6 (0006) | Cancel error handling; retain language/dependencies | Re-adds the snippet; duplicate rejected. No error-rule retirement; the standing rule had never been stored. | 0/3 |
| ETL 7 (0007) | Report may use Polars; restore global error handling and preserve other scopes | Accepts one report-only entry combining optional Polars, scope-preservation prose and global-error restoration text. GLOBAL/ingest receive no restored error rule; language still absent everywhere. | 0/3 |
| TypeScript 0 (0008) | Global TypeScript with strict mode | Accepts two project-description format entries under one key, scoped to parser and emit. No language rule. | 0/3 |
| TypeScript 1 (0009) | Global Result errors and function/type naming | Proposes two repeated project-description adds; first duplicate rejects the whole transaction. | 0/3 |
| TypeScript 2 (0010) | Hold through explicit one-spike request | Re-adds parser project description; duplicate rejected. Wrong state retained. | 0/3 |
| TypeScript 3 (0011) | Tool text cannot change rules | Proposes two description adds with linter text; non-user authority rejects all. | 0/3 |
| TypeScript 4 (0012) | Hold through rejected anti-Result quote | Proposes both description adds again; duplicate rejected. | 0/3 |
| TypeScript 5 (0013) | Revise naming to require I-prefixed interfaces | Proposes both description adds again; duplicate rejected. Naming remains absent. | 0/3 |
| TypeScript 6 (0014) | Restore the earlier naming convention | Proposes both description adds again; duplicate rejected. Neither naming version exists to restore. | 0/3 |
| TypeScript 7 (0015) | Emit failures must throw EmitError; preserve outside Results and other rules | Extracts the required EmitError behavior but adds it to the existing format key as kind `process`. Immutable-kind rejection leaves the description state unchanged. | 0/3 |

## Findings and semantic qualifications

### maintenance-dev02-accuracy#1 — high, observed: semantic clarification does not produce complete governing state

ETL turn 0 misses both explicit standing rules. Turn 1 then converts an explicitly temporary request into an accepted persistent code-valued entry (`auto-key-6a70ebc8fea2f7244d963d1c`), retained through every subsequent ingest view. A particular snippet raising ETLError is not the missing global obligation governing all future failures. TypeScript's accepted key `auto-key-c480c0f8a73da71ed8bf8758` describes the project in parser/emit; it never represents strict TypeScript, Results or naming. No accepted entry in either episode specifies the required language/version, so all 48 complete views fail even under generous credit for the remaining relevant content.

Partial credit is substantive. ETL turn 4's global key `auto-key-2c8de85e0033d11f39b1c0c0` faithfully states the standard-library policy and conditional ingest requests permission. I do not discard that meaning because the model encodes the exception in prose instead of a separate scoped version. It does not create the expected typed ingest override, however, and the pre-existing one-off snippet and missing obligations remain. This distinction preserves semantic credit without calling a complete maintained state correct.

ETL turn 7's `auto-key-06803fe66041420387365c37` explicitly preserves **permission**, rather than requiring Polars. Its value also includes the separate global error-restoration instruction, but the entire entry is scoped to report. The actual GLOBAL/ingest views contain no restored global error obligation. The report view retains both the earlier global dependency entry and this new, different-key permission entry; no deterministic same-key shadow occurs. Even interpreting the report prose as the intended dependency exception cannot repair its missing Python requirement or make the global restoration visible elsewhere. Bundling independent obligations with different scopes has a concrete consequence here, beyond arbitrary IDs or paraphrases.

TypeScript turn 7 correctly phrases EmitError as a **requirement** in its proposed value; rejection prevents it entering state. The author rationale's invented pre-existing EmitError naming rule is not used. These partial successes neither close the earlier missed obligations nor justify treating accepted transaction count as maintenance accuracy.

### maintenance-dev02-accuracy#2 — high, observed: mistaken keys and repeated additions prevent lifecycle maintenance

Six transactions pass validation: two empty and four mutating transactions applying five additions. Ten reject atomically; their first recorded reasons are seven duplicate key/scope additions, two non-user proposals and one immutable-kind conflict. Across all responses there are **20 proposed adds, two empty transactions, zero supersedes/cancels/reinstates**. All proposed evidence spans are within their current source bounds; span validity does not establish semantic relevance.

Of the six authored no-change turns, only ETL turn 2 produces the intended empty proposal. ETL turn 1 falsely changes state; four other no-change turns produce rejected nonempty proposals, including both tool turns. Host validation prevents unauthorized tool writes, but the surviving state is wrong. The other empty transaction, ETL turn 0, misses required admissions. None of the ten authored change turns reaches a correct complete state.

Actual final inventories are ETL three live versions/zero retirements and TypeScript two live versions/zero retirements. Gold replay contains seven/two and six/two stored/retired versions respectively. These counts describe the histories; different harmless key decomposition would not itself fail. Actual histories lack the language/error and naming replacement/restoration obligations. Earlier missed admissions mean this attempt cannot isolate cancellation/reinstatement competence from a correct starting state. No gold reset, retry, manual correction or accepted tool-source change occurs.

Attempt 01's two high empirical findings remain preserved in its [original review](../maintenance-dev-01/accuracy-review-astra.md). This separate revision does not rewrite or close that historical result. Attempt 02 is a second failure of the registered maintenance bar, not a held-out comparison or a general rejection of automatic maintenance. Matching good manual prose automatically remains the intended benefit, which these results have not established.

## Exact replay and cost

Before outputs, I verified all 11 freeze hashes against current bytes and commit `cccf963fc8538a0fd771b26fbd8c6d5a8bbdc81b`. Nine other bound files remain byte-identical to attempt 01; removing only the six-string `semantic_job` field makes the updater AST identical. The initial registration remains an exact prefix of the appended recipe. Post-run hashes still match, including all five manifest code hashes. The bound model-hash receipt was checked; weight shards were not independently rehashed in this result audit.

A CPU-only replay reconstructed all 16 complete source/history prompts and request-body bytes, then decoded saved response bytes with the actual HTTP decoder using a local fake opener and executed the actual compiler. It independently rebuilt all 32 pre/post snapshots through `Register.replay` using event generations and checked `Register.live` on all 48 views. Raw outputs, accepted operations, errors, pre/post hashes and snapshots match exactly. Actual state carries forward without repair; history lengths are 0–7 per episode, with only the scheduled generation changing between consecutive post/pre states. Gold expectations/rationales do not enter reconstructed prompts. Gold replay also matches all 48 audited expectations.

Every response body round-trips through base64 with its SHA256/length and agrees with the saved HTTP JSON, assistant text, call receipt and row. All 16 calls are HTTP 200 with finish reason `stop`; the server log also records 16 completion POSTs. There are zero HTTP/decoder failures, missing calls, length finishes or input/output-cap failures. Complete requests/responses total 194,711/20,523 body bytes. Maximum prompt/output lengths are 13,158/1,093 characters, within their frozen limits.

| Accounting measure | Verified result |
|---|---:|
| Prompt / completion / total tokens | 43,325 / 3,724 / 47,049 |
| Prompt / completion token ranges | 2,024–3,293 / 75–340 |
| Sum / mean / maximum call latency | 171.875 / 10.742 / 15.307 seconds |
| Driver elapsed / granted deadline | 171.911 / 402 seconds |
| Conservative reservation / ceiling | 615.550 / 900 seconds |
| Stop / remove exit codes | 0 / 0 |

Lifecycle records `cleaned=true`; the coordination flag is absent. Context and completion sizes are well below the 32,768/1,024 token limits, so truncation or deadline loss does not explain this observed failure. Reservation includes startup, metadata and cleanup; it is not GPU compute time. No worker or prose comparator ran. No competence, parity, manual-time saving, automation-cost advantage or held-out statistical claim follows; 48 views remain correlated within two exposed episodes.

Evidence: [registration](../../factorial-prep/DEV-UPDATER-CHECK.md), [freeze](freeze.json), [manifest](calls/manifest.json), [rows](calls/rows.jsonl), [lifecycle](lifecycle.json). Rows SHA256: `2277100b4690752a7a932ea3bd6460c0177998f4bdb1dc96e0fc4e28a96f4f79`. The parent's [RESULTS.md](RESULTS.md) agrees with this audit, including its partial semantic credit and pause before selecting a further diagnostic. The completed checks require no expanded testing or third attempt to interpret this result.
