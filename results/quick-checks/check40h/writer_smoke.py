#!/usr/bin/env python3
"""CPU-only integration fixture; dummy replies never enter scientific results."""


def main():
    import importlib.util
    import json
    import shutil
    import sys
    import tempfile
    import time
    from pathlib import Path

    repo = Path(__file__).resolve().parents[3]
    sys.path.insert(0, str(repo / "scripts"))
    import focus_check40h as h
    import torch
    from transformers import AutoTokenizer, Qwen3MoeConfig, Qwen3MoeForCausalLM

    torch.set_num_threads(2)
    real_out = h.OUT
    scratch = Path(tempfile.mkdtemp(prefix="check40h-writer-"))
    h.ROOT = scratch
    h.OUT = scratch / "outputs"
    h.OUT.mkdir()
    for name in ("freeze.json", "tasks.json", "biases.pt", "prewritten-reading.md"):
        shutil.copyfile(real_out / name, h.OUT / name)
    tok = AutoTokenizer.from_pretrained(h.base.MODEL, local_files_only=True)
    eot = tok.convert_tokens_to_ids("<|im_end|>")
    oks = tok.encode("OK", add_special_tokens=False)
    assert len(oks) == 1
    cfg = Qwen3MoeConfig(
        vocab_size=len(tok),
        hidden_size=16,
        intermediate_size=32,
        moe_intermediate_size=8,
        num_hidden_layers=2,
        num_attention_heads=2,
        num_key_value_heads=1,
        head_dim=8,
        num_experts=4,
        num_experts_per_tok=2,
    )
    cfg._attn_implementation = "sdpa"
    original_generation = h.generation
    original_engine = h.base.Engine

    def engine_factory(start):
        engine = original_engine.__new__(original_engine)
        engine.torch, engine.device, engine.tokenizer = torch, torch.device("cpu"), tok
        engine.model = Qwen3MoeForCausalLM(cfg).eval()
        engine.hooks = h.base.RouterHooks(
            [layer.mlp.gate for layer in engine.model.model.layers]
        )
        engine.eos, engine.deadline, engine.load_seconds = (
            {eot},
            time.monotonic() + 600,
            0,
        )
        engine.verify_kernel = lambda: dict(adopted=True, cpu_fixture_only=True)
        return engine

    # Same metadata/writer/cache/mask/score pipeline, two forced dummy output tokens.
    # Bias schedule uses identical full-size recorded digests, projected to2x4 only
    # inside the toy gate hook. No scientific inference or fitting.
    original_hooks = h.base.RouterHooks

    class ToyHooks(original_hooks):
        @property
        def bias(self):
            return getattr(self, "_toy_bias", None)

        @bias.setter
        def bias(self, value):
            self._toy_bias = None if value is None else value[:2, :4].float()

    h.base.RouterHooks = ToyHooks

    def dummy_generation(engine, messages, bias, session, cap=64):
        forwards = 0

        def force(model, args, output):
            nonlocal forwards
            output.logits.fill_(-1e6)
            output.logits[..., oks[0] if forwards == 0 else eot] = 1e6
            forwards += 1
            return output

        handle = engine.model.register_forward_hook(force)
        try:
            return original_generation(engine, messages, bias, session, cap)
        finally:
            handle.remove()

    h.base.Engine = engine_factory
    h.generation = dummy_generation
    h.prior.resources = lambda: dict(ready=True, cpu_fixture_only=True)
    h.run()
    h.audit()
    summary = json.loads((h.OUT / "summary.json").read_text())
    assert summary["records"] == 528 and summary["generations"] == 480
    assert summary["complete"] and not torch.cuda.is_initialized()
    spec = importlib.util.spec_from_file_location("report40h", real_out / "report.py")
    report = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(report)
    report.OUT = h.OUT
    report.main()
    result = dict(
        cpu_dummy_writer_consumer=True,
        records=528,
        generations=480,
        every_mask_and_cue_span_audited=True,
        report_rendered=True,
        cuda_initialized=False,
        scratch=str(scratch),
    )
    (real_out / "writer-smoke.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
