# Full-FIT adapter archive contents

Fresh final adapter from the single54-update, three-epoch FIT run in RESULTS.md;
independent result audit pending. This is not the earlier four-update mechanics
adapter. Training used only the18 frozen FIT rows; no heldout/development data.

Standard PEFT safetensors:144 FP32 tensors,2,949,120 parameters. Shapes:72 LoRA A
tensors [8,2560],36 q-projection B tensors [4096,8],36 v-projection B tensors
[1024,8]. Targets q_proj/v_proj across36 layers, rank8, alpha16, dropout0, biasnone.
Original4B trunk remains separate and unchanged in the recorded endpoint checks.

The11,815,504-byte standard file SHA256 is
`1f9392f3fa99cb31a010176487a6f37999f02cdbc7be9b9cdb4a9b9380e592e3`.
It and the identical reconstructed copy remain local, uncommitted. Concatenate
run-01/archive/adapter_model.safetensors.part-000 (9,000,000 bytes) then part-001
(2,815,504 bytes) to reconstruct exactly, checking archive-manifest.json hashes.
Pair the reconstructed file with the exact run-01/adapter/adapter_config.json
(SHA25645f10d86fd18dc5d5f4c748b1b9c59f292f7fc92f6f6334e21dff9255f9a70b2).
The run already verified standard PEFT same-trunk reload and complete FP32 state
identity; no reproduction or model call is needed to verify the archive bytes.

The intended consumer is the original local Qwen3-4B through the qualified HF/
PEFT stack, with the loaded adapter explicitly selected for inference. Future
semantic/coding use requires a separate prospective protocol. The recorded
FIT-only adapter generation reached2048 tokens without EOS and produced
incomplete JSON; this archive carries no claim of useful instruction tracking.
