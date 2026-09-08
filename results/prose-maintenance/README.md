# Prose-memory maintenance trial

Purpose: test whether automatically maintained prose preserves active rules across a changing conversation, following the positive two-source cold extraction diagnostic. Full long-session coding usefulness remains unproven.

Kimi K3 via Ollama authored two new8turn DEV conversations. Independent Astra data review96 accepted after Kimi-only corrections to9label/rationale fields; all16source messages are unchanged. Structural and semantic48view gold checks pass. Sol xhigh implemented the own-notes runner; independent Astra code review95 accepted. No expected notes, labels or gold resets enter prompts. See [registered reading](PROTOCOL.md), [data review](data-review-astra.md) and [code review](code-review-astra.md).

The two cold prompts use321/304tokens; later prompts depend on actualgeneratednotes and cannot be frozen in advance. Sixteen single-attempt calls,900seconds total including startup/cleanup, no worker. The previous two full maintenance failures remain and this trial counts toward the registered stop-loss. Runtime results will be preserved under results/quick-checks/prose-maintenance-01. This preparation is not a model-maintenance result.
