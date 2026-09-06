"""Greedy retained-KV decoder for the custom_generate injected-decoder contract.

Batch lanes have independent attention masks and logical positions. Padding is
retained physically but never visible. No actuator, retries or output selection.
Layer numbers are one-based post-block residuals (hidden_states[L]).
"""

import time

from .loop import DecodeResult


class RetainedDecoder:
    def __init__(
        self,
        model,
        tokenizer,
        lanes=1,
        layers=(8, 16, 24, 32, 40),
        cap=512,
        deadline=float("inf"),
    ):
        import torch

        self.torch, self.model, self.tokenizer = torch, model, tokenizer
        self.lanes, self.layers, self.cap, self.deadline = lanes, layers, cap, deadline
        self.cache = None
        self.mask = torch.zeros((lanes, 0), dtype=torch.long, device=model.device)
        self.consumed = [() for _ in range(lanes)]
        self.eos = model.generation_config.eos_token_id
        self.eos = {self.eos} if isinstance(self.eos, int) else set(self.eos or ())
        self.pad = model.generation_config.pad_token_id or tokenizer.pad_token_id or 0
        self.captured = {}
        self.handles = [
            model.model.layers[layer - 1].register_forward_hook(self._hook(layer))
            for layer in layers
        ]

    def _hook(self, layer):
        def capture(module, inputs, output):
            hidden = output[0] if isinstance(output, tuple) else output
            # Keep only the last position: no full-context hidden-state allocation.
            self.captured[layer] = hidden[:, -1, :].detach().clone()

        return capture

    def close(self):
        for handle in self.handles:
            handle.remove()
        self.handles = []
        self.cache = None

    def _sync(self):
        if self.model.device.type == "cuda":
            self.torch.cuda.synchronize()

    def _forward(self, ids, visible, positions):
        torch = self.torch
        self.mask = torch.cat((self.mask, visible), dim=1)
        started = time.monotonic()
        with torch.inference_mode():
            out = self.model(
                input_ids=ids,
                attention_mask=self.mask,
                position_ids=positions,
                past_key_values=self.cache,
                use_cache=True,
                logits_to_keep=1,
            )
        self.cache = out.past_key_values
        self._sync()
        return out.logits[:, -1, :].argmax(-1), time.monotonic() - started

    def __call__(self, rendered):
        torch = self.torch
        assert len(rendered) == self.lanes
        started = time.monotonic()
        suffixes = []
        for old, req in zip(self.consumed, rendered, strict=True):
            prompt = tuple(req.prompt_ids)
            if prompt[: len(old)] != old:
                raise ValueError("retained KV prefix mismatch")
            suffixes.append(prompt[len(old) :])
        width = max(map(len, suffixes))
        ids = torch.full(
            (self.lanes, width), self.pad, device=self.model.device, dtype=torch.long
        )
        visible = torch.zeros_like(ids)
        positions = torch.zeros_like(ids)
        for i, suffix in enumerate(suffixes):
            if not suffix:
                raise ValueError("empty prefill")
            ids[i, -len(suffix) :] = torch.tensor(suffix, device=ids.device)
            visible[i, -len(suffix) :] = 1
            positions[i, -len(suffix) :] = torch.arange(
                len(self.consumed[i]),
                len(self.consumed[i]) + len(suffix),
                device=ids.device,
            )
        next_ids, prefill_seconds = self._forward(ids, visible, positions)
        prompt_hidden = torch.stack(
            [self.captured[layer] for layer in self.layers], dim=1
        )
        sums = torch.zeros_like(prompt_hidden, dtype=torch.float32)
        counts = [0] * self.lanes
        bodies = [[] for _ in range(self.lanes)]
        eos = [None] * self.lanes
        active = [True] * self.lanes
        decode_seconds, decode_steps, deadline_hit = 0.0, 0, False
        for step in range(self.cap):
            sampled = next_ids.tolist()
            for i in range(self.lanes):
                if active[i]:
                    if sampled[i] in self.eos:
                        eos[i], active[i] = sampled[i], False
                    else:
                        bodies[i].append(sampled[i])
            if not any(active) or step == self.cap - 1:
                break
            if time.monotonic() >= self.deadline:
                deadline_hit = True
                break
            valid = torch.tensor(active, device=ids.device, dtype=torch.long)[:, None]
            positions = torch.tensor(
                [
                    len(req.prompt_ids) + len(body) - 1
                    for req, body in zip(rendered, bodies, strict=True)
                ],
                device=ids.device,
            )[:, None]
            next_ids, seconds = self._forward(next_ids[:, None], valid, positions)
            decode_seconds += seconds
            decode_steps += 1
            hidden = torch.stack([self.captured[layer] for layer in self.layers], dim=1)
            sums += hidden.float() * valid[:, :, None]
            for i in range(self.lanes):
                counts[i] += active[i]
        elapsed = time.monotonic() - started
        results, measurements = [], []
        for i, body in enumerate(bodies):
            # At a cap/deadline the final sampled token has no forward activation.
            # Never fabricate it or spend an extra forward to collect it.
            self.consumed[i] = tuple(rendered[i].prompt_ids) + tuple(body[: counts[i]])
            mean = (
                sums[i] / counts[i]
                if counts[i]
                else torch.full_like(sums[i], float("nan"))
            )
            text = self.tokenizer.decode(body, skip_special_tokens=False)
            results.append(
                DecodeResult(
                    text,
                    tuple(body),
                    eos[i],
                    eos[i] is None,
                    gpu_held_seconds=elapsed / self.lanes,
                )
            )
            measurements.append(
                dict(
                    prefill_tokens=len(suffixes[i]),
                    prefill_seconds=prefill_seconds,
                    decode_seconds=decode_seconds,
                    decode_steps=decode_steps,
                    generated_forward_tokens=counts[i],
                    hidden_complete=counts[i] == len(body),
                    deadline_hit=deadline_hit,
                    batch_size=self.lanes,
                    batch_wall_seconds=elapsed,
                    cache_physical_tokens=self.mask.shape[1],
                    cache_logical_tokens=len(self.consumed[i]),
                    prompt_hidden=prompt_hidden[i].to(torch.float16).cpu().numpy(),
                    generated_mean=mean.to(torch.float16).cpu().numpy(),
                )
            )
        return results, measurements
