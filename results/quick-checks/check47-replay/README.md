# Check 47 CPU settling replay — registration (2026-09-06)

Registered before implementation and replay. User-authorized record correction;
check 47's registered STAY verdict and SLAB-2 remain unchanged.
Fit-on: nothing. Evaluated-on: only the 32 saved dense and 32 saved MoE R replies
for SLAB DEV00/01 already exposed by check 47; no model calls or benchmark reads.

The replay-only SLAB v1 tolerance set is `trailing_closer`, `lift_report`,
`test_path`, plus the fourth sibling `strip_leading_fence`. After outer whitespace,
accept exactly one leading line of ```json or ``` followed by a newline and a
complete envelope. Remove an optional final standalone ``` line (outer whitespace
allowed). An absent closing fence is accepted only when the JSON envelope is
complete; never complete JSON, extract a prefix, accept prose or multiple blocks.
The frozen parser still validates the interior with its three existing tolerances.
Journal `strip_leading_fence` once per accepted reply, with `closed` true/false;
retain the existing per-call tolerance journal. Apply identically to both trunks.
No live parser or SLAB-2 edit: enable the fourth tolerance in an isolated copy of
SLAB v1 from freeze `184cb321`, shared by its Executor and checker.

Replay literal saved outputs in round order on a fresh persistent workspace per
trunk/episode, using frozen `materialize`, `Executor.run`, and `check` (the exact
consumer sequence in `PilotJournal.finish`). Preserve original caps. First verify
untolerated replay reproduces saved execution, outcomes and artifact hashes;
then enable the tolerance and replay all 64 replies. Pin source/input hashes.
Report executed-response counts, caps, breakage, final-turn success, all seven
violation kinds, round-0 indent compliance, and per-reply/per-event tolerance use.
Compare saved rendered prompts to identify truly matched pairs. All 32-round totals
are descriptive only: 2 round-0 pairs match, the other 30 answer divergent histories;
CPU execution cannot generate the replies that corrected feedback would elicit.
Test accepted/rejected fence boundaries through the frozen Executor and checker.
CPU only, foreground, no container, process signals, GPU, model rerun or push.

## Corrected record

**The check 47 harness comparison is INELIGIBLE as run.** The original dense
0/32 measured fence rejection, not execution competence. Registration committed
at `97ca5c5b` before `replay.py` was written. With the registered tolerance:

| Frozen-consumer replay; all 32 rounds, descriptive only | Dense FP8/vLLM | MoE bf16/HF |
|---|---:|---:|
| Executed responses | 32/32 | 32/32 |
| Caps | 0/32 | 0/32 |
| Breakage | 0/32 | 0/32 |
| Final success (last round of each episode) | 0/2 | 0/2 |
| Successful rounds (all kinds jointly compliant) | 22/32 | 0/32 |
| Language violations | 0/32 | 0/32 |
| Style violations | 0/32 | 30/32 |
| Format violations | 6/32 | 10/32 |
| Process violations | 4/32 | 17/32 |
| Wrong-family violations | 0/32 | 0/32 |
| Semantic violations | 0/32 | 0/32 |
| Round-0 indent compliance, nonempty executed edits | 2/2 | 0/2 |

| Tolerance fired (replies; event counts are identical here) | Dense | MoE |
|---|---:|---:|
| `trailing_closer` | 0/32 | 0/32 |
| `lift_report` | 0/32 | 0/32 |
| `test_path` | 0/32 | **32/32 (100%)** |
| `strip_leading_fence` | **32/32 (100%)** | 0/32 |

Dense fences: 13 closed and 19 unclosed, with complete JSON in all 32. Tolerances
are counted once per reply in the table; all event details are journaled in records.
The checker re-parses with the same tolerance but does not duplicate journal events.

| Scope | Dense | MoE |
|---|---:|---:|
| Genuinely matched round-0 pairs: executed | 2/2 | 2/2 |
| Matched pairs: jointly compliant | 2/2 | 0/2 |
| Matched pairs: style / format / process violations | 0 / 0 / 0 | 2 / 0 / 2 |
| Matched pairs: language / wrong-family / breakage / semantic | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 |
| Unmatched rounds 1–15: executed, descriptive only | 30/30 | 30/30 |
| Unmatched rounds: jointly compliant, descriptive only | 20/30 | 0/30 |
| Unmatched rounds: style / format / process violations | 0 / 6 / 4 | 28 / 10 / 15 |
| Unmatched rounds: language / wrong-family / breakage / semantic | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 |

On the **two genuinely matched pairs**, the direction of observed compliance
favors dense: it satisfies every checked kind, while MoE violates indentation and
delivery scope on both. Two pairs do not establish a general trunk advantage.
Across the **32-round histories**, dense also has fewer observed style, format and
process violations, with equally successful execution and zero semantic violations;
these totals are **descriptive only**. Precisely 30/32 prompt pairs are unmatched,
not 32/32: from round 1 the dense model answered envelope-error feedback while MoE
answered real tool receipts. The CPU replay executes fixed text sequentially with
corrected receipts/state; it cannot recover model responses to that corrected history.
Round-0 success is per reply, not final-episode success; both final-turn scores fail.

**STAY on the MoE remains unchanged.** Check 47's switch rule is conjunctive and
the registered ≤12-hour bf16-equivalent cost clause fails every projected row:
12.12 hours even in the optimistic 16-round cross-workload row, 45.61 hours in the
conservative 32-round DEV row. Those remain projections with an unmeasured 2× bf16
serving multiplier. The dense architecture has **48 GatedDeltaNet + 16 full-attention
layers**; per-token attention masking cannot evict contributions already folded into
the 48 recurrent states without recomputation. This is a separate structural limit
on the registered release mechanism. This replay corrects the record, not the decision,
and does not change SLAB-2, whose prompt already requires one fenced block.

## Reproduction and validation

Run from the repository root:

```sh
CUDA_VISIBLE_DEVICES='' .venv/bin/python results/quick-checks/check47-replay/replay.py
```

[replay.py](replay.py) extracts committed `src/` and `scripts/` at `184cb321` into
a temporary directory and verifies all 25 registered source hashes under those paths.
It imports only the frozen SLAB consumer; no model weights/tokenizer, generation,
container or network call is needed. The frozen sandbox runs CPU Python children
that self-exit; the parent sends no signals. An audit guard rejects benchmark opens,
network connections, and process-signal calls.

Validation passed: **64/64 untolerated exact replays** match saved outcomes,
executed calls, tool results, tolerance journals and artifact hashes; **64/64 corrected
replays** complete; **8/8 consumer boundary cases** pass (plain JSON, open/closed
fences, CRLF, incomplete JSON, leading/trailing prose, multiple blocks). All 32 MoE
records remain identical under the added tolerance. Saved prompt text compares equal
on exactly two pairs. No original check47 artifacts or verdict fields were overwritten.

[summary.json](summary.json) pins inputs, frozen sources, replay script and records,
with aggregates for all rounds, matched pairs and unmatched rounds separately.
[records.jsonl](records.jsonl) is 186,564 bytes (<10 MB), 64 records containing source
file/line, literal output and hash, saved-prompt hash and match flag, original cap/EOS,
executed calls, receipts, per-reply tolerances, all checker outcomes, artifact hashes
and non-vacuous indent evidence. Original records retain full prompt/token journals.
See [Opus review](../../check47-review-opus.md) and the
[original addendum](../check47/README.md#orchestrator-addendum-after-the-opus-maximum-reasoning-review-2026-09-06-resultscheck47-review-opusmd).
