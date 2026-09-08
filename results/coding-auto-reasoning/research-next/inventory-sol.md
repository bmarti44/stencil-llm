# Sol xhigh read-only local implementation inventory

2026-09-08. Reported by the existing native Sol xhigh coding author; no files,
models, data, weights or GPU state modified or executed. These are feasibility
observations, not a selected training recipe or resource guarantee.

A local `models/qwen3-4b-hf` base has all three shards. Its index declares
8,044,936,192 tensor bytes; config is Qwen3ForCausalLM,36layers,hidden2560,BF16.
The historical Check49 freeze records base/tokenizer hashes, but current large
assets were not rehashed. The old untracked focus-lora-4b adapter is scientifically
NO-GO and excluded. Freeze-time clean asset/revision qualification is still needed.

Installed metadata: torch2.13.0,transformers5.16.1,PEFT0.20.0,accelerate1.14.0.
PEFT/accelerate are absent from the project lock. Exact environment pinning is
needed; no installation or dependency change was made by this inventory.

Smallest proposed reuse: pure source-event/record_focus serialization and
whole-conversation split validator; one new main-guarded fit script; a thin owned
launcher after sizing. Reuse only inspected Check49 training mechanics, never
import its top-level script or reuse its data/adapters. Its historical rank8q/v
adapter had2,949,120trainable parameters; seq<=256,batch8,two-adapter fitting took
14.14s with peak allocated13.351GB. Conversation lengths differ, so those numbers
cannot size this candidate.

Training mechanics to audit: local-only loading, exact tokenizer chat-template
prefix, target-only loss with prefix/padding masked, frozen BF16trunk+SDPA+LoRA,
finite/nonzero loss and gradients, no trunk gradients, fresh exclusive output,
atomic per-step receipts and base tensor identity. Hyperparameters/data volume
remain unselected. Prefix expansion must happen only after whole-conversation
FIT/DEV/heldout splitting. Source IDs and JSON shape do not certify semantics;
Kimi labels still need independent source review. No spent examples enter FIT.

Required measurements: exact untruncated input/target token distribution;
longest-bucket step time and peak allocated/reserved memory; model load/hash/save
time; adapter parameters; projected whole FIT cost; unchanged-base and trained
selector inference cost on heldout; actual native4B+LoRArecord_focus compatibility.
Current accepted native reasoning client requires positive reasoning/delimiters;
final-JSON-only SFT labels need a separately qualified nonthinking path, unless a
different target protocol is deliberately selected and supported. Existing30B
reasoning smoke does not establish4BLoRAserving.

This inventory supplies an implementation option, not a recommendation to train.
Astra's bounded primary-source research and root synthesis choose whether the
next local feasibility measurement is warranted. No new framework is needed.
