# Admission v2 — check44c BIO tagger

BGE-small-en-v1.5 encoder (pinned revision in manifest.json) plus dropout0.1 /
linear hidden-size384 → 3 BIO logits, fp32; fully fine-tuned for three epochs.
Seeds0/1/2 have independent encoder and head safetensors; seed0 is designated.
Weights are local and excluded from git. manifest.json and check44c/model-freeze.json
record their SHA256 hashes along with tokenizer, split, thresholds and training
metadata. O/B/I probabilities and offsets are saved in the results records.

Training sources, audit patch semantics, source-batch split, decoding and
C-then-B union are specified in results/quick-checks/check44c/README.md and
implemented in scripts/focus_check44c.py. No runtime deployment is implied by
this model directory: check44c/summary.json supplies the frozen GO/NO-GO decision.

Reproduction from the registered corpus requires the local pinned base model;
fresh fitting is intentionally guarded and is not authorized by this README.
Verification is CPU-only using the script's audit command and saved records.
