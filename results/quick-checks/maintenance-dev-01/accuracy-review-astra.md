Fit-on: none. Development-on: the two exposed, independently audited Kimi conversations and this frozen updater attempt. Evaluated-on: none. The author rationale caveat remains excluded from verified supervision.

# Independent DEV accuracy review — Astra

2026-09-07 · Round 1 · Reviewer: gpt-6-astra, xhigh, native session `/root/maintenance_dev_result_review`. Explicit user-requested Astra xhigh replaces the historical Opus assignment. Author-disjoint from Sol's implementation, Kimi's data and the parent's execution/report. Purpose: audit the actual predicted-state maintenance result under the prewritten DEV reading; threat model: trusted but fallible model and operators. Source/design review preceded output access. Actual receipts were opened only after the parent confirmed terminal exit and cleanup. Only this review file was written; no inference, network/GPU access, source edits, old-result/benchmark reads or commits.

**Result: NOT PERFECT ON DEV. Complete semantic views: 0/48; entirely correct turns: 0/16; whole trajectories: 0/2.** Both episodes fail their first standing instruction and remain wrong. This is a substantive maintenance failure of the frozen recipe on these easy exposed seeds. The run completed within its resource envelope, and independent CPU replay verifies the recorded failures. Transport completion and legal transactions do not establish correct maintenance.

## All scheduled turns

Indices are zero-based, matching `calls/rows.jsonl`; call receipts are `calls/calls/call-NNNN.json`. Every row below independently checks GLOBAL and both declared task views for `code_answer`. “0/3” means none of those complete views agrees semantically, including the unchanged obligations.

| Episode / turn (call) | Required maintenance | Actual proposal and resulting state | Correct views |
|---|---|---|---:|
| ETL 0 (0000) | Global Python 3.11 and contextual ETLError; never bare except | Accepts one ingest-only `research_register` process entry. Both real obligations absent. | 0/3 |
| ETL 1 (0001) | Hold through explicitly one-off pandas request | Re-adds the same ingest entry; duplicate key/scope rejected. Wrong state retained. | 0/3 |
| ETL 2 (0002) | Hold through explicitly unadopted Polars quote | Re-adds the same entry; duplicate rejected. Wrong state retained. | 0/3 |
| ETL 3 (0003) | Tool text cannot change rules | Proposes the same add; host rejects non-user authority. Wrong state retained. | 0/3 |
| ETL 4 (0004) | Global standard-library-only policy; ingest requests permission | Re-adds the irrelevant entry; duplicate rejected. Neither dependency scope created. | 0/3 |
| ETL 5 (0005) | Python 3.12 across the project | Accepts a new process key, value `3.12`, with a Python reminder, but only ingest scope. Global/report still lack Python; other obligations remain absent. | 0/3 |
| ETL 6 (0006) | Cancel the ETL error rule; retain language/dependencies | Re-adds the Python entry; duplicate rejected. The error rule had never been stored, so its absence is not evidence of successful cancellation. | 0/3 |
| ETL 7 (0007) | Restore the error rule and permit optional Polars in report; preserve other scopes | Accepts another `research_register` entry under a new report-only key. No error restoration or Polars permission. | 0/3 |
| TypeScript 0 (0008) | Global TypeScript with strict mode | Accepts the project description as a parser-only format entry. Language/strict obligation absent. | 0/3 |
| TypeScript 1 (0009) | Global Result errors and function/type naming | Repeats the project-description add with evidence end 185 against 169 source characters; rejected. Both new conventions absent. | 0/3 |
| TypeScript 2 (0010) | Hold through explicit one-spike request | Repeats that add with evidence end 185 against 155 source characters; rejected. Wrong state retained. | 0/3 |
| TypeScript 3 (0011) | Tool text cannot change rules | Repeats the project-description add; host rejects non-user authority. Its span also exceeds this source, but authority is checked first. | 0/3 |
| TypeScript 4 (0012) | Hold through rejected anti-Result quotation | Repeats the project-description add; duplicate rejected. Wrong state retained. | 0/3 |
| TypeScript 5 (0013) | Add I-prefixed interfaces to the standing naming convention | Repeats the project-description add; duplicate rejected. Naming remains absent. | 0/3 |
| TypeScript 6 (0014) | Restore the earlier naming convention | Repeats the project-description add; duplicate rejected. Neither naming version exists to restore. | 0/3 |
| TypeScript 7 (0015) | Emit failures must throw EmitError; outside emit retain Results, strict TypeScript and naming | Accepts the same project-description key in emit scope. No required error behavior or other standing conventions. | 0/3 |

## Findings

### maintenance-dev-accuracy#1 — high, observed: accepted state does not represent the governing obligations

All five accepted operations are wrong overall. ETL's cold value/text describe the updater's own transaction rather than either user rule. TypeScript's cold value describes the project rather than the explicit standing language requirement. Both also invent task-local scope for global instructions. Their final accepted adds repeat those irrelevant contents in the other task. The two GLOBAL views stay empty throughout all eight turns of their respective episodes.

The one partial extraction is ETL turn 5: `auto-key-bc2b16970ba17f5705d0a80b` has value `3.12` and text “Target Python 3.12 instead of 3.11 across the whole project.” That is recognizable Python-version content despite the arbitrary key and `process` kind. It receives semantic credit as relevant content for ingest, but the actual typed scope excludes GLOBAL/report; the reminder's words cannot repair which views receive it. With the other obligations absent and the spurious entry still active, ingest's complete view also fails.

There is no gold counterpart for ETL's `auto-key-7aca96df21ab8e1963e47d92` and `auto-key-35a08f29691bd2f62f03b1af`, or TypeScript's `auto-key-7ddb0d0da6b1e9af6d513432`. This identification follows their value/text, not their opaque names. Alternative decomposition and equivalent paraphrases would be acceptable; none can turn a project description into strict TypeScript, separate naming and error obligations, or dependency permissions. ETL's optional Polars permission and TypeScript's required EmitError behavior are both missing, so no permission/requirement ambiguity rescues either last turn. The previously reviewed false TypeScript rationale about a pre-existing EmitError naming rule is not used.

### maintenance-dev-accuracy#2 — high, observed: the trajectory repeats additions instead of maintaining lifecycle state

Every response proposes exactly one `add`: 16 adds, zero empty transactions, replacements, cancellations or reinstatements. Eleven transactions are rejected. Their **first recorded reasons** are seven duplicate key/scope additions, two out-of-range evidence spans and two non-user proposals. Other defects can coexist in a rejected proposal.

All six authored hold/negative turns produce nonempty proposals, including both tool turns. Host validation prevents those six mutations and retains the exact previous state, but that state is already semantically wrong. None of the ten authored change turns reaches a correct complete state. No accepted tool-source operation, gold reset, retry or human correction occurs; these integrity properties do not repair the missed obligations.

The actual final ETL inventory contains three live versions and zero retirements; TypeScript contains two live versions and zero retirements. Audited gold replay contains seven/two and six/two stored/retired versions respectively. The mismatch is semantic, not a penalty for a different number of keys: actual histories contain the irrelevant additions above, while the language/error and naming replacement/restoration histories never exist. Earlier missed admissions prevent isolating cancellation or reinstatement competence from a correct starting state. This run establishes failure of the complete self-carried trajectories, not a separate estimate for each lifecycle action.

These empirical defects remain true of this frozen attempt. They do not call for changing its outputs or loosening the registered reading.

## Independent integrity and cost audit

A CPU-only audit reconstructed each source/history prompt, decoded the saved response bytes through the actual HTTP decoder using a local fake opener, and replayed the actual updater/compiler. It separately rebuilt all 32 pre/post snapshots with `Register.replay` from recorded events and append generations, then called `Register.live` for all 48 task/global views. All recorded prompts, accepted entries, rejections, hashes, snapshots and subsequent state handoffs matched. Each episode starts empty; history lengths are exactly 0–7; only the scheduled generation changes between one post-state and the next pre-state. Gold annotations/rationales never enter the reconstructed updater inputs. Independent gold replay also agrees with all 48 audited expectations.

All 11 frozen source/data/recipe/receipt hashes match both current bytes and commit `5d499362eb4e7537631a06b10201b6e52e2c1f8e`; all five driver-recorded code hashes match that freeze. This verifies the bound pre-run model-hash receipt, not an additional rehash of the weight shards. Exact serialized request bodies match the reconstructed HTTP payloads; every response body round-trips from base64 with its stored SHA256 and byte count. All 16 saved assistant contents match the raw HTTP JSON, row and call receipt. The server log independently contains 16 completion POSTs, all HTTP 200.

There are **zero HTTP/decoder failures, length finishes, output-cap failures or missing scheduled calls**. Every response finishes `stop`, using 173–196 completion tokens against the 1024 cap. Prompts use 1,759–2,836 tokens, far below the 32,768 server context. Largest prompt/output strings are 10,843/499 characters, within the frozen character limits. Thus truncation or deadline loss does not explain this observed failure. Full preserved body totals are 161,146 request bytes and 17,285 response bytes.

| Cost/accounting measure | Verified result |
|---|---:|
| Prompt / completion / total tokens | 36,185 / 2,937 / 39,122 |
| Sum of 16 call latencies | 132.412 seconds |
| Mean / maximum call latency | 8.276 / 9.079 seconds |
| Driver elapsed / granted deadline | 132.450 / 354 seconds |
| Conservative reservation / ceiling | 620.472 / 900 seconds |
| Recorded stop / remove exit codes | 0 / 0 |

Lifecycle records `cleaned=true`, and the coordination flag is absent. Reservation includes startup, metadata and cleanup; it is not measured GPU compute time. No worker or prose comparator ran, so this cost demonstrates budget eligibility only. There is no measured automation benefit, manual-time saving, equivalence, worker competence or held-out statistical conclusion. The 48 views are correlated observations within two exposed episodes.

Evidence anchors: [frozen recipe](../../factorial-prep/DEV-UPDATER-CHECK.md), [freeze](freeze.json), [manifest](calls/manifest.json), [rows](calls/rows.jsonl), [lifecycle](lifecycle.json). Rows SHA256: `292545097de622a1633b6b3a3687e748d7fc4153bce430be342d1ebba4e3b13d`.

The parent's [RESULTS.md](RESULTS.md), including its independent-accuracy addendum and first-rejection clarification, agrees with this audit. Its semantic-prompt explanation is explicitly a future hypothesis; this one attempt does not isolate the cause. The prewritten rule requires the reported DEV failure and supports preserving the complete attempt before any separately frozen revision.
