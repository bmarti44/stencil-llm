# Prose-memory maintenance trial

Purpose: test whether automatically maintained prose preserves active rules across a changing conversation, following the positive two-source cold extraction diagnostic. Full long-session coding usefulness remains unproven.

Kimi K3 via Ollama authored two new8turn DEV conversations. Independent Astra data review96 accepted after Kimi-only corrections to9label/rationale fields; all16source messages are unchanged. Structural and semantic48view gold checks pass. Sol xhigh implemented the own-notes runner; independent Astra code review95 accepted. No expected notes, labels or gold resets enter prompts. See [registered reading](PROTOCOL.md), [data review](data-review-astra.md) and [code review](code-review-astra.md).

The two cold prompts use321/304tokens; later prompts depend on actualgeneratednotes and cannot be frozen in advance. Sixteen single-attempt calls,900seconds total including startup/cleanup, no worker. The previous two full maintenance failures remain and this trial counts toward the registered stop-loss. Runtime results are preserved under results/quick-checks/prose-maintenance-01.

The run is complete and fails the registered maintenance bar: Rust global rules were explicitly narrowed to named tasks. All16calls and integrity checks completed;12,283tokens,90.13seconds of calls,546.21seconds total with successful cleanup. [Result](../quick-checks/prose-maintenance-01/RESULTS.md) and [independent audit](../quick-checks/prose-maintenance-01/accuracy-review-astra.md) preserve the evidence. This third failure parks the small single-updater recipe line; no further prompt repair or inference is authorized by this result. A substantially different hypothesis requires evidence and separate prospective review.
