# Coding competence run 01 — source and result audit

Reviewer: Astra xhigh, `/root/competence_readiness_review`, 2026-09-08.
Author-disjoint source review under the user's selected model allocation.
Only this new report was written. Frozen preparation, bank, runtime, launcher
and readiness review remain untouched. No generated/authored program was
executed, no test suite or experiment was rerun, and no server/model/API call
was made. Checks below reconcile preserved JSON, hashes, source ASTs and native
token receipts; static witnesses are explicitly not executed tests.

**Decision: NO-GO; preserve and park this operating point.** The recorded
experiment is technically complete and auditable. It fails the registered
12/12 endpoint and 4/4 project prerequisites. Independent source inspection
also finds defects in both projects that passed their finite checks, so none
of the four projects qualifies as fully correct under the source criterion.
This is not evidence of automatic-focus parity, nor a reason to alter this
run's prompts, cap, attempts, data, results or success gate.

## Recorded outcome

All 12 requests completed with 18 native generations and 18 authoritative
render requests. Nine requests passed on their first and terminal attempts;
the other three each exhausted three attempts. There were no successful
repairs. Three actions were structurally rejected; 15 were applied. All 18
native generations ended with `stop`, with no cap, transport, grammar,
context or token-accounting failure recorded.

The following terminal-check counts include the registered initial helper and
cumulative stable checks as well as current obligation checks. They are finite
observations, not counts of generally correct programs.

| Project | Request 0 | Request 1 | Request 2 | Recorded project result |
| --- | --- | --- | --- | --- |
| Outline | 16/16, 1 attempt | 12/19, 3 attempts | 15/26, 3 attempts | FAIL |
| Laboratory | 9/9, 1 attempt | 13/13, 1 attempt | 15/15, 1 attempt | PASS |
| Inventory | 11/11, 1 attempt | 18/18, 1 attempt | 24/24, 1 attempt | PASS |
| Route | 15/15, 1 attempt | 19/19, 1 attempt | 19/24, 3 attempts | FAIL |

Totals reconcile to 185 public check results and 209 terminal check results.
Recorded native usage is 95,528 prompt tokens plus 5,777 completion tokens,
101,305 total. Completion lengths range from 152 to 675 tokens under the
unchanged 1,024 cap. The largest actual prompt is 13,345 tokens; adding its
1,024 allowance gives 14,369, below 32,768. Actual cold native counts are
1,232 / 1,967 / 1,760 / 1,987, and their exact request hashes match the
four previously frozen cold payloads. The earlier provisional serialized-JSON
counts were not claimed to be these native counts.

## Source findings

Severity labels below describe defects in the frozen worker result and limits
on its interpretation. They are not requests to repair or rerun spent cases.

1. **high — outline indexing fails both the action consumer and the algorithm.**
   Calls 1, 2 and 3 submit identical function-source bytes, SHA256
   `e2babb48160c1a550c44b4eea9dcba6fe84819ed27c4f44b18a8b8a96d7ff567`.
   Each defines a nested `traverse` function and receives the exact rejection
   `response patch must not define nested callables or classes`. The actual
   `index_sections` therefore remains its `return None` stub; request 1's
   terminal module hash equals request 0's. Independently of that rejection,
   `current_path = path + [str(len(path) + 1)]` uses depth rather than original
   sibling position: every top-level node would be numbered `1`, and the first
   child would get `1.2`. This contradicts the explicit source and recap.
   That algorithmic diagnosis is a static derivation, not an executed retry.

2. **high — outline query inherits the failed dependency and adds a rejection
   error.** Calls 4, 5 and 6 apply identical source, SHA256
   `bd2c06de465bfd4e49b07534ad69bc050802224c7f60748a6c4c54d5ff6e5394`.
   They correctly call the actual `index_sections`, whose `None` result is then
   iterated, matching the saved `TypeError` results. No gold replacement hides
   that dependency failure. Separately, the query's own invalid-`lines` branch
   returns `{"error":"invalid query"}`; the source requires the downstream
   index error to pass through, yielding `{"error":"invalid input"}` for
   that invalid line-list input. Saved check `pf-q4` records this exact mismatch.
   The implementation uses `text in entry["title"]`, which is case-sensitive.
   Failed case-sensitivity checks here are downstream execution failures, not
   evidence that the worker retained the superseded case-insensitive rule.

3. **high — route itinerary returns quote records where final leg records are
   required.** Calls 15, 16 and 17 apply identical source, SHA256
   `8e9cd1d1a69f5df7e9d95537b1de4168e9bec329f46767eb29f8548d1370aecf`.
   The code builds `folded_legs` but returns `priced_legs` in the `legs` field.
   `price_segment` returns `quote_cents` and omits `fare_cents`, whereas the
   requested final leg dictionaries retain `fare_cents`. Both public failures
   and all five terminal failures show this exact field substitution. Saved
   values demonstrate the correct 7-minute cross-mode transfer and quote totals
   on those cases. They therefore do not support attributing failure to stale
   no-cross-mode behavior. The dependency calls and propagation of `None` are
   present; the returned object is wrong.

4. **high — laboratory source accepts boolean dilution despite finite passes.**
   Calls 7, 8 and 9 each validate dilution using `isinstance(dilution,
   (int, float))` and positivity without excluding `bool`. The genuine setup
   states that booleans are not numbers, and the accepted reference's
   `normalize_batch` explicitly excludes boolean dilution. Since `True` is an
   instance of Python `int` and is greater than zero, the generated functions
   accept it. Later functions call the actual earlier dependencies, which share
   this omission. A static, unexecuted witness is a valid one-sample payload with
   `dilution: true`; it takes the success branch instead of returning `"invalid"`.
   The registered private inputs contain no boolean-dilution case. The three
   recorded passing endpoints remain passing finite observations, but they
   cannot establish source compliance. On the exercised scope-change cases,
   `build_report` does pass `include_flagged: True` and direct aggregation
   preserves its opt-in/default policy.

5. **high — inventory source accepts two explicitly invalid inputs despite
   finite passes.** Call 11's `reconcile_stock` checks opening quantities with
   `isinstance(qty, int)` and `qty < 0`, admitting booleans even though both
   request and recap explicitly exclude them. Its `payload.get("allow_backorder")`
   followed by validation only when the result is not `None` also treats an
   explicitly present JSON `null` as omission; the request says a present value
   must be a list. Static, unexecuted witnesses are an otherwise valid payload
   with boolean opening stock, and `{opening: {}, movements: [],
   allow_backorder: null}`. Both reach success rather than their required error.
   Call 12's audit correctly delegates to the actual reconciliation function
   and consequently inherits these validation defects. The recorded scope
   change allowing listed backorders is implemented; these are additional
   input-contract defects, not evidence of reverting that rule.

No source defect was identified in the outline builder, inventory summarizer,
route pricer or route combiner under this bounded inspection. That statement
does not certify correctness on every possible input. All actual dependency
calls were inspected; saved module transitions modify only the authenticated
target, preserving the earlier functions rather than bypassing or resetting
them. The two mechanically passing projects both have demonstrated source
defects, so the independent source criterion fails beyond the recorded 9/12.

## Interface and causal limits

6. **medium — the initial worker prompt does not disclose the nested-callable
   restriction.** The frozen system message requires a complete synchronous
   target function and pure Python; the tool description only says to replace
   the authenticated target. Neither enumerates the consumer's prohibition on
   nested functions. A nested helper is valid pure Python, so the first rejection
   is partly an interface limitation and is not a clean measure of ordinary
   Python coding ability. The restriction is explicitly disclosed by the first
   tool error, however, and the remaining two attempts still repeat the same
   source. The independent wrong-numbering algorithm also survives this caveat.
   This omission does not rescue the registered worker/environment recipe.

All 12 manual reminders were read against their genuine visible source prefix.
They preserve the current contracts and scoped changes and do not falsely
assert that earlier generated implementations already work. Exact reconstruction
of every outgoing message list confirms the current reminder is present at
every attempt and removed before the next request. Actual modules, original
source roles, native assistant calls and matching tool results remain in order.
No private checks, expected values, private pass/fail, reference patches, mutants,
oracle objects or future source messages were added beyond the expressly
authorized current manual-reminder text and visible public cases.

I also decoded saved authoritative prompt IDs with the pinned local tokenizer,
without generating anything. Calls 2/3 contain the nested-callable rejection;
calls 5/6 contain the query `TypeError` feedback; calls 16/17 contain the genuine
earlier tool results. These are not merely messages written to a client-side
log: the feedback appears in the actual rendered prompt. The three repair
groups repeat function-source bytes despite that history and the visible public
cases. Outer native argument serialization and token counts need not be identical;
the verified identity claim is specifically the submitted function source.

The supported diagnosis is failure of this coding-and-feedback operating point,
including incomplete validation and an initially underspecified consumer
restriction. It is not a transport, missing-reminder, missing-history, output-cap
or actual-context-limit failure. Why this worker repeats wrong source despite
available feedback is not causally identified by this run. The next research
question is whether the worker's ability to revise a function from explicit
consumer/public feedback has been established under the intended interface,
before interpreting an automatic-versus-manual focus comparison. This report
does not authorize a new experiment or prescribe a rescue on these cases.

## Independent receipt and lifecycle reconciliation

- Reconstructed all 18 message lists from the accepted visible source prefixes,
  current recap, prior actual module and authentic public action/results;
  compared exactly with the outgoing native JSON. Verified the public-only
  stopping rule: no early stop on a failed public attempt, no extra attempt
  after a successful public attempt, and no private-based selection.
- Verified all 18 render/completion request-byte pairs, recorded raw response
  body hashes/sizes, HTTP 200 statuses, forced tool/schema settings, matching
  prompt IDs, completion-ID counts, exact usage sums and actual context limits.
  Native call IDs are unique within projects and match tool responses.
- Reconciled all 394 saved check rows with their registered check identity,
  input, expected values and exact actual-module hash; recomputed pass flags
  from the saved result using type-sensitive equality without executing code.
  The observed failure expectations agree with the natural source requirements.
  The additional source findings demonstrate coverage gaps; they do not alter
  any frozen expected value or recorded score.
- Verified every applied target AST equals the submitted source AST and every
  other top-level definition is unchanged; rejected actions preserve the exact
  prior module. Request-start/terminal hashes and terminal workspace bytes match
  the actual chain. All 12 records are complete, with no unattempted requests.
- Verified all 16 freeze-bound file hashes remain unchanged, including readiness
  SHA256 `67be720256fb0d7bdcc4e343c727447e51199cfe1a3a49d53072fe7834862603`.
  Twenty trunk-file size/mtime pairs match the existing hash receipt; this is
  metadata verification, not a newly computed 61 GB weight hash.
- Lifecycle elapsed 816.136678 seconds under 2700: 491.128890 seconds from
  lifecycle start to driver launch, 319.395647 seconds for the driver process,
  and 5.612142 seconds afterward. The driver received 2148 seconds and exited 1.
  Registered launcher, launch-client, driver and cleanup PIDs were confirmed in
  the ownership registry. Logs, stop and remove receipts all exit 0 for exactly
  the owned container; lifecycle records `cleaned:true` and complete cleanup
  evidence, and the run flag is absent. No process was signalled by this audit.
  The parent's independent terminal resource check additionally reported no
  remaining container/GPU compute; this reviewer did not issue a fresh API query.

Evidence pins:

| Artifact | SHA256 |
| --- | --- |
| Freeze at commit `c35d6a377e4c1cd42b9770f4e0bc3d4fa81925ce` | `4c218ea71036c185eec1da4d24e36e6f3ea0b00a52f8bd483243746b14c49f17` |
| `calls/manifest.json` | `fdfa06d79ea92e7fb010623fa297865e2d69a658875afb34108cd79a4907cc01` |
| `lifecycle.json` | `fdd530fa8d53d3c466ef8f3d67d122062fca46dbcf4cec968fe3ce7263aee1c9` |
| `driver-exit.json` | `0ccbfc958017914a71fee91d81c0f1085f24196b09c82e8f88a3a6a40bbf36bc` |
| `cleanup-receipts.json` | `91cbc9e181852a5ec07c94bf5c1b5f6b268b05add1cc91eec3d8ddcd63bfcebb` |
| Aggregate 12 request + 18 call + manifest receipt mapping | `f5cc87ef85978936475ab46d802b43734b7e2aca031a0501fc766027d7cc4b58` |

The aggregate digest hashes compact sorted UTF-8 JSON mapping each receipt's
run-relative path to its SHA256. This audit accepts the recorded technical
accounting and the NO-GO interpretation; it does not accept the generated source
as satisfying the registered competence prerequisite.
