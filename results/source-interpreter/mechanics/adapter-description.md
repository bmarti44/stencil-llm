# Mechanics adapter binary description

This disposable rank-8 q/v LoRA adapter was produced by the single registered
four-update FIT mechanics run. It is not a trained production focus mechanism,
is not evaluated for transfer, and must not initialize later full training.
The original local Qwen3-4B trunk stayed frozen under the recorded checks.

The standard PEFT `adapter_model.safetensors` is 11,815,504 bytes, SHA-256
`8c9331c334031f38192e34ac3f07321aeab4eb35c7b9dd8755fbada65cc518d9`.
Its 144 FP32 tensors contain 2,949,120 parameters (11,796,480 payload bytes):
72 tensors of shape [8,2560], 36 of [4096,8], and 36 of [1024,8]. Names identify
q_proj/v_proj LoRA A/B weights across the 36 original layers. Standard adapter
configuration SHA-256 is
`45f10d86fd18dc5d5f4c748b1b9c59f292f7fc92f6f6334e21dff9255f9a70b2`.

The full original and reconstructed standard files remain local because each
exceeds the repository's 10,000,000-byte commit limit. Git archives their exact
bytes as two ordered parts, 9,000,000 and 2,815,504 bytes. The
[archive manifest](run-01/archive-manifest.json) supplies names, order, sizes,
individual hashes and the full hash. Concatenating the parts in that order
reconstructs the standard safetensors file; no new tensor format or precision
conversion is involved. The unchanged configuration is also archived.

The run reconstructed the file, loaded it through standard PEFT on the same base
under adapter name `roundtrip`, checked complete adapter-state equality, activated
it in inference mode, and performed one no-gradient loss computation on the same
FIT row. Root independently checked the safetensors header and all archive/full/
reconstructed hashes without loading a model. The independent result audit is
pending; the full measured runtime records are in [RESULTS](RESULTS.md).
