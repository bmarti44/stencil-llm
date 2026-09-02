"""Locate Qwen3 parity drift by decoder layer and residual sub-step.

Run from the repository root, for example::

    uv run --isolated --with transformers==4.51.0 --with accelerate \
      python scripts/qwen3_parity_debug.py --model 4b --device cuda
"""

from __future__ import annotations

import argparse
import gc
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from stencil.qwen3 import Qwen3, Qwen3Config  # noqa: E402

DEFAULT_PROMPT = 'New rule: reply to "cat" with "dog". cat ->\nVariation 0:'
MODEL_PATHS = {
    "1.7b": (ROOT / "models/qwen3-1.7b-hf", ROOT / "models/qwen3-1.7b.pt"),
    "4b": (ROOT / "models/qwen3-4b-hf", ROOT / "models/qwen3-4b.pt"),
}


def _cpu_float(value: torch.Tensor) -> torch.Tensor:
    return value.detach().float().cpu()


def _max_delta(left: torch.Tensor, right: torch.Tensor) -> float:
    if left.shape != right.shape:
        raise ValueError(f"capture shape mismatch: {left.shape} != {right.shape}")
    return float((left - right).abs().max())


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", choices=MODEL_PATHS, default="4b")
    parser.add_argument("--prompt", default=DEFAULT_PROMPT)
    parser.add_argument("--device", choices=("cpu", "cuda"), default="cuda")
    parser.add_argument(
        "--attn-implementation",
        choices=("eager", "sdpa"),
        default="sdpa",
        help="HF attention backend (the parity oracle defaults to SDPA)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=2e-2,
        help="first-layer reporting threshold (default: 0.02, BF16-scale noise)",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    try:
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError as exc:  # pragma: no cover - exercised by CLI environments
        raise SystemExit(
            "transformers is required; use: uv run --isolated --with "
            "transformers==4.51.0 --with accelerate python "
            "scripts/qwen3_parity_debug.py"
        ) from exc

    if args.device == "cuda" and not torch.cuda.is_available():
        raise SystemExit("--device cuda requested but CUDA is unavailable")
    device = torch.device(args.device)
    dtype = torch.bfloat16
    hf_dir, trunk_path = MODEL_PATHS[args.model]
    cfg = Qwen3Config.from_hf(hf_dir / "config.json")
    tokenizer = AutoTokenizer.from_pretrained(hf_dir)
    ids = tokenizer(args.prompt, return_tensors="pt").input_ids.to(device)

    hf_post_attn: list[torch.Tensor | None] = [None] * cfg.n_layer
    hf_post_mlp: list[torch.Tensor | None] = [None] * cfg.n_layer
    hf = AutoModelForCausalLM.from_pretrained(
        hf_dir,
        torch_dtype=dtype,
        attn_implementation=args.attn_implementation,
    ).to(device).eval()
    handles = []
    for layer_index, layer in enumerate(hf.model.layers):
        def capture_hf_post_attn(module, inputs, index=layer_index):
            del module
            hf_post_attn[index] = _cpu_float(inputs[0])

        handles.append(
            layer.post_attention_layernorm.register_forward_pre_hook(
                capture_hf_post_attn
            )
        )
        def capture_hf_post_mlp(module, inputs, output, index=layer_index):
            del module, inputs
            hf_post_mlp[index] = _cpu_float(output[0])

        handles.append(layer.register_forward_hook(capture_hf_post_mlp))
    with torch.no_grad():
        hf_output = hf(ids, output_hidden_states=True, use_cache=False)
    hf_hidden = [_cpu_float(value) for value in hf_output.hidden_states]
    hf_logits = _cpu_float(hf_output.logits[0, -1])
    tied_equal = torch.equal(
        hf.lm_head.weight.detach().cpu(),
        hf.model.embed_tokens.weight.detach().cpu(),
    )
    for handle in handles:
        handle.remove()
    del hf, hf_output
    gc.collect()
    if device.type == "cuda":
        torch.cuda.empty_cache()

    our_post_attn: list[torch.Tensor | None] = [None] * cfg.n_layer
    our_post_mlp: list[torch.Tensor | None] = [None] * cfg.n_layer
    ours = Qwen3(cfg)
    ours.load_state_dict(torch.load(trunk_path, map_location="cpu"), strict=True)
    ours = ours.to(dtype).to(device).eval()
    handles = []
    for layer_index, layer in enumerate(ours.layers):
        def capture_our_post_attn(module, inputs, index=layer_index):
            del module
            our_post_attn[index] = _cpu_float(inputs[0])

        def capture_our_post_mlp(module, inputs, output, index=layer_index):
            del module, inputs
            our_post_mlp[index] = _cpu_float(output)

        handles.extend(
            (
                layer.post_attention_layernorm.register_forward_pre_hook(
                    capture_our_post_attn
                ),
                layer.register_forward_hook(capture_our_post_mlp),
            )
        )
    with torch.no_grad():
        our_logits_full = ours(ids)
    our_logits = _cpu_float(our_logits_full[0, -1])
    for handle in handles:
        handle.remove()

    print(f"prompt: {args.prompt!r}")
    print(f"tokens: {ids.shape[1]}")
    print(f"HF tied lm_head equals embeddings: {tied_equal}")
    embedding_delta = _max_delta(
        hf_hidden[0], _cpu_float(ours.embed_tokens(ids))
    )
    print(f"embedding max|delta|: {embedding_delta:.6g}")
    first = None
    for layer_index in range(cfg.n_layer):
        hf_attn = hf_post_attn[layer_index]
        hf_mlp = hf_post_mlp[layer_index]
        our_attn = our_post_attn[layer_index]
        our_mlp = our_post_mlp[layer_index]
        assert (
            hf_attn is not None
            and hf_mlp is not None
            and our_attn is not None
            and our_mlp is not None
        )
        attn_delta = _max_delta(hf_attn, our_attn)
        mlp_delta = _max_delta(hf_mlp, our_mlp)
        marker = ""
        if first is None and max(attn_delta, mlp_delta) > args.threshold:
            first = layer_index
            marker = "  <-- first above threshold"
        print(
            f"layer {layer_index:02d}: post-attn={attn_delta:.6g} "
            f"post-MLP={mlp_delta:.6g}{marker}"
        )
    logit_delta = _max_delta(hf_logits, our_logits)
    print(f"logits max|delta|: {logit_delta:.6g}")
    print(
        "top-1: "
        f"HF={int(hf_logits.argmax())} ours={int(our_logits.argmax())} "
        f"agree={bool(hf_logits.argmax() == our_logits.argmax())}"
    )
    if first is None:
        print(f"no decoder layer exceeded threshold {args.threshold:g}")
    else:
        print(f"first decoder layer above threshold {args.threshold:g}: {first}")


if __name__ == "__main__":
    main()
