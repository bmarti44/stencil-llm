Fit-on: none. Development-on: the two exposed, audited Kimi DEV conversations and synthetic CPU HTTP replies only. Evaluated-on: none. No network, GPU, model, worker, benchmark, held-out or frozen-run-record access.

# Automatic-maintenance DEV driver — independent code review

2026-09-07 · Round 1 · Reviewer: gpt-6-astra, xhigh reasoning. Explicit user-requested Astra xhigh replaces the historical Opus assignment. Author-disjoint from Sol's driver/tests; only this review file is written. Purpose: trustworthy execution and receipts for the registered two eight-turn DEV trajectories. Threat model: trusted-but-fallible operators and ordinary protocol/transport failures. Updater internals and the independently accepted lifecycle owner are outside this review, except their actual driver interfaces.

**Score: 83/100. Not accepted: one open high finding; no critical findings.**

### driver-code#1 — high (resolved 2026-09-07, Round 2): malformed response bytes are silently changed and can mutate state; interrupted reads lose available bytes

`scripts/maintenance_dev_check.py:147–179` stores only `response_body.decode("utf-8", errors="replace")`, then parses that substituted text. The raw-byte evidence is discarded. Through actual `run`, `ChatCompletionDecoder`, and updater execution, a fake HTTP reply containing byte `0xff` inside an otherwise valid add-operation value produced **COMPLETE**, `accepted=true`, `error=null`, and accepted value `VALUE_�`. The saved HTTP body also contained the replacement character, so neither the protocol defect nor the exact received bytes survived. This makes a malformed reply look like an ordinary accepted model proposal and violates the registered raw-response/error boundary.

The same transport path discards available partial responses. A mocked real `response.read()` raising `IncompleteRead(b'{"choices":[{"message":', 100)` produced a rejected turn, but its receipt had `http.response=null`; the 23 received bytes and already available response status/headers were lost. The text exception retained only byte counts.

Retain exact received body bytes using a JSON-safe encoding plus a byte hash, decode UTF-8 strictly before parsing or applying a proposal, and preserve available partial bytes/status/headers on read failures. Keep the rejection and one-call schedule; do not retry. Add regressions through the actual 16-turn driver showing malformed encoding cannot change state, the next turn sees unchanged predicted state, and every available normal/error/partial body round-trips exactly from its receipt.

## Evidence and qualified behavior

Four independent disposable-directory CPU simulations each exercised actual `run` for all 16 turns, with every HTTP operation replaced locally. Two reproduced finding #1. A gold-boundary poison simulation replaced loaded annotations with unusable objects and marked metadata/rationales with a sentinel: all 16 serialized requests still completed, the sentinel was absent, both tool turns were called, and natural-history lengths were exactly 0–7 independently in each episode. Inspection confirms only source ID/role/text, declared handles/request kind, and actual predicted register state cross the driver/updater boundary; there is no gold-state reset or worker invocation.

A fourth simulation proposed its own arbitrary rule, then exercised wrong targets, stale hashes, unauthorized tool operations, a mixed valid/invalid transaction, replacement, cancellation and reinstatement. Both episodes had acceptance pattern `[true,false,false,false,false,true,true,true]` and event counts `[1,1,1,1,1,2,3,4]`. Every rejected transaction retained the exact pre-state. Each following pre-state matched the preceding actual post-state except the host-owned scheduled generation increment; the second episode started empty. All 16 request/prompt/receipt IDs, raw outputs and reported token counts matched their own turns. A separate reused-decoder check confirmed a pre-HTTP deadline refusal clears `last_http`; the suspected previous-call receipt carryover is refuted by code and execution.

The authored tests cover the real CLI with fake HTTP, exact `temperature=0`, seed `20260907`, `max_tokens=1024`, and `chat_template_kwargs={"enable_thinking":false}`, plus DEV/nonempty-output refusal, cooperative deadlines, transport errors, malformed choices and length truncation. They do not cover finding #1. The reviewed code has one sequential call per scheduled turn, no retry or worker path, and an incomplete manifest when scheduled execution or deadline completion fails. `COMPLETE` means the trajectory was recorded, not semantic success; empty/rejected/wrong proposals remain available for the separately registered semantic review. Saved full states permit that later 48-view audit, which this driver does not itself score.

## Reviewed SHA256 bindings

- Driver: `c6eb7de41acfecba8643ee8de7fea51969a2a71e6782605ffb76cb6953ba4e5e`
- Driver tests: `9915f996886b8503b334a8eb3c325fedc6bf9b9cbc6dd96e32af6e223151719f`
- Bank adapter: `be51237f9b407bdab55a27c064c3f2bede3f51fd3cabb88c8012192fe1862ca0`
- Audited DEV input: `e4f5d954841edea17d76f0cef6f2ee68333019321a23c29d4ba53624441b1553`
- DEV contract: `6dc38e379238cb7b7c9c993b38886b506f0efdc8e17fa0e72c33458f86871f26`

The updater author concurrently repaired its separately reviewed implementation. Finding #1 and the gold-boundary simulations used updater `19c07be092a9d0e40f238b690d41fec805d2df5b17fb886a8d1a338d91808514`; the later state/transaction simulation used `c5123d20bba37b996bdb431ce0145e7790abc7f2bf41b86895204f482b657685`. Driver/test bytes stayed fixed. Final integration must bind the subsequently accepted updater and repaired driver; this review does not authorize inference or certify maintenance quality.

## Round 2 — 2026-09-07

Same independent Astra xhigh reviewer; scope remains finding #1 and its repair. **Score: 95/100. Accepted for the registered DEV driver purpose; no open high/critical findings.** Prior finding text and score are retained, with only the explicit closure marker added above.

**driver-code#1 resolved.** The transport now saves exact received bytes as base64, their SHA256 and byte count before parsing. UTF-8 decoding is strict; malformed encoding produces a rejected turn with no state mutation. `IncompleteRead` preserves available partial bytes, response status/headers and the exception's expected remaining-byte count. Full and partial HTTP-error bodies use the same exact-byte receipt path. No retry was introduced.

Independent CPU re-verification exercised actual `run`, HTTP decoding and the accepted updater in one complete 16-turn trajectory. It first accepted an arbitrary Unicode-valued rule, then injected invalid UTF-8, an interrupted success response, an HTTP 503 body containing invalid UTF-8, and an HTTP 502 whose error-body read was interrupted. All four failures were rejected; all subsequent turns retained their own correct state, and the second episode started empty. Every one of the 16 response bodies round-tripped byte-for-byte through its saved base64, hash and length; partial/error status, headers and available remaining-byte counts matched. Request/prompt/turn receipts and normal token counts also matched. Separately, `.venv/bin/python -m pytest -q tests/test_maintenance_dev_check.py` passed **6 tests**. All HTTP operations were local mocks; no network, GPU or model call occurred.

Final verified SHA256: driver `08afbff47368f35b9b55e3a10ea4e29eec80118c2b5d1cdef3d7a4fc3ead00ff`; tests `1931971f6c09895bb1e2e367e065daaa22553a901c66d51f0d27fbcb45285f2c`; integrated updater `151b114351de2d062adac0327acb37cdce568460473d18cd99e4cc8f02af0594`. Acceptance concerns implementation and receipts for this exposed DEV check, not semantic maintenance accuracy or permission to enlarge the experiment.
