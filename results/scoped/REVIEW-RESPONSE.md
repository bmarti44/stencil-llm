# Disposition of Astra's implementation review (2026-09-13)

Review: `results/reviews/2026-09-13-scoped-instrument-astra.md` —
**VERDICT — REPAIR — 28% artifact-success forecast.** Six high findings, three
medium, one low. Every finding is applied; none is negotiated. No GPU was used
before, during or after the review, and no generation has occurred, so no repair
is fitted to an outcome.

| # | severity | finding | disposition |
|---|---|---|---|
| 1 | high | Two wrong resolvers pass 16/16: reinstatement restoring the first policy at a scope, and treating every obligation as package-wide. The oracle's expectation came from the same `resolve()` the gold did, so agreement validated nothing | **Applied.** R1 rebuilt to Astra's specification (earlier DEFAULT policy at the same scope; reinstatement references the *second* statement); R3's obligation scoped to `compat/` in its own wording with cases straddling the boundary. Both policies registered as rivals and now defeated. Per-case `expect_value`/`expect_note` frozen by hand; the gate checks `resolve()` against them. The claim that the oracle "never consults the history" was false and is withdrawn |
| 1b | high | Requiring each rival to *survive* somewhere is not a soundness argument | **Applied — rule deleted.** A correct fixture may legitimately defeat a wrong policy everywhere; the positive control is the independently spelled valid implementations |
| 2 | high | The oracle accepts materially wrong behaviour: a bulk gather returning `[None]`; a function rebinding an existing one to a broken lambda; a function logging after table access and never on failure; a raise naming the wrong key; a tuple return failing an unstated contract | **Applied.** `observe()` uses a mixed batch and checks present entries, order and length; the exception payload must name the missing key; preservation checks present-key behaviour as well as classification; the obligation is checked on both paths and for ordering via an instrumented mapping; the list contract is now stated in the request. All five are regression tests. Astra's confirmation that preserving `block.precedent` is the correct target under prospective semantics is accepted |
| 3 | high | The model does not receive the contract the oracle enforces — C4/core is told to follow documentation it is never shown; histories name `compat.py` when the request names `compat/__init__.py`; R3's text says package-wide while its metadata says compat; G1/G2 say "whole package" while an operation exception survives; the conventions live only in `SEMANTICS.md` | **Applied.** Both prompts now carry the package `__init__.py` and a conventions block; all wording corrected to real paths and real scopes; G1/G2 say explicitly that the narrower rule stands. Isolation assertions moved onto the actual prompt strings, not the serializer the runner does not consume |
| 4 | high | "Thinking disabled" is registered but never implemented — the runner tokenized raw text with no chat template and no assistant boundary | **Applied.** The shipped non-thinking chat template is applied in both conditions and in the token counter, and asserted on CPU |
| 5 | high | A 48-record prefix printed `RESCUED`; missing cases silently became failures. Plus resume identity, duplicates, `timed_out` counting as success, a scorer timeout losing the generation receipt, and overstated atomicity | **Applied.** 64 unique records from one configuration are required before any reading; duplicates, mixed configurations and stub records refuse; `timed_out` can never be a success; a scorer timeout still records the generation; partial trailing lines are skipped and reported; every record carries a configuration fingerprint and a resume across configurations exits 3 |
| 6 | high | The pilot and the 0.5 GPU-hour ceiling are prose, not behaviour; the launch command reserved 30 minutes and allowed 45 | **Applied.** `--pilot` selects the four longest-prompt cases, projects `1.5 × mean × 64`, and exits 4 above the ceiling. The budget check reserves the worst case of the next generation before starting it. The launch command is now two commands with coherent reservations |
| 7 | medium | The reminder is an answer key for applicability; the "cannot be attributed to length" claim is wrong | **Applied.** That claim is withdrawn as wrong — duplication changes length, repetition, position and salience, and the header adds authority. The attribution is narrowed: a rescue is attributable to that bundle, never to applicability resolution alone, and never to be presented as evidence that a compiler can find the instruction |
| 7b | medium | A negative result is not a proof of impossibility | **Applied.** Section 1 now says a failure justifies the registered spending stop and nothing stronger |
| 8 | medium | Semantics: the "only way an earlier value returns" claim is false; `clears` is undocumented; depth-over-operation is a stipulation; one support per obligation; `resolve_events()` selected supports by name and returned released ones | **Applied.** Statement-versus-value distinguished; `clears` documented as exact-scope; the stipulation labelled and stated in the public prompt; the single-support limit recorded; `live_state` now keys obligations by `(name, scope)` and `resolve_events` returns only surviving applicable supports, with a unit test on the multi-support case the blocks do not contain |
| 9 | medium | Register the remaining limits; the "existing sandboxed path" claim is inaccurate; the line-based extractor damages a multiline signature | **Applied.** A "What these blocks are not" section records single-function additions, append-only edits, one package and 16 authored contrasts rather than independent samples, the runner using `revised` histories only, and crash-separation-not-a-sandbox. Extraction is syntax-aware and the multiline signature is a regression test |
| — | low | Descriptive arithmetic and decision wording | **Applied.** All numbers re-measured through the chat template after the repairs; the sign test is printed; the ceiling has one consistent explanation |

## What did not change

The 16 blocks, two conditions, frozen trunk, prespecified thresholds and the
registered N. No arm, model, benchmark or review stage was added — Astra's
adopt-only-if-it-adds-nothing constraint.

## What this does not buy

Astra's forecast stays at **28%**. A sound construction gate was already assumed
in that number; achieving one earns nothing extra. The repairs remove reasons to
disbelieve the instrument; they supply no evidence about the model.
