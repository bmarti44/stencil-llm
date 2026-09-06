"""HF custom-generation scaffold. Imports never load a model or weights."""

from dataclasses import replace

from stencil.focus import DecodeResult, generate_once


def generate(
    model=None,
    input_ids=None,
    *,
    session,
    inputs=None,
    generation_config=None,
    logits_processor=None,
    stopping_criteria=None,
    prefix_allowed_tokens_fn=None,
    synced_gpus=None,
    assistant_model=None,
    streamer=None,
    negative_prompt_ids=None,
    negative_prompt_attention_mask=None,
    use_model_defaults=None,
    local_files_only=True,
    new_messages=(),
    decoder=None,
    tokenizer=None,
    tools=None,
    actuator="off",
    max_new_tokens=256,
    **kwargs,
):
    """Return (literal output, session); session owns rendered input/history.

    Supply an injected decoder for CPU tests, or a caller-loaded HF model and
    its tokenizer. input_ids is deliberately unsupported: it would bypass the
    authoritative renderer. This custom entry has a session-oriented return.
    """
    # HF forwards its named parameters even when unset. Contract:
    # https://huggingface.co/docs/transformers/en/generation_strategies#creating-a-custom-generation-method
    # Config is forwarded; use_model_defaults is ignored (removed in HF 5.16.1).
    # Optional generation extensions are unsupported.
    unsupported = (
        logits_processor,
        stopping_criteria,
        prefix_allowed_tokens_fn,
        synced_gpus,
        assistant_model,
        streamer,
        negative_prompt_ids,
        negative_prompt_attention_mask,
    )
    if any(option is not None for option in unsupported) or kwargs:
        raise ValueError("unsupported generation options")
    if not local_files_only:
        raise ValueError("assets must be loaded locally")
    if input_ids is not None or inputs is not None:
        raise ValueError(
            "use session.request; externally prepared input_ids bypass rendering"
        )
    if decoder is None:
        if model is None or tokenizer is None:
            raise ValueError("provide decoder or model and tokenizer")
        if max_new_tokens < 1:
            raise ValueError("max_new_tokens must be positive")
        session.request = replace(
            session.request,
            encode=lambda text: tokenizer.encode(text, add_special_tokens=False),
        )

        def decoder(rendered):
            import time

            import torch

            ids = torch.tensor(
                [rendered.prompt_ids], dtype=torch.long, device=model.device
            )
            start = time.monotonic()
            with torch.inference_mode():
                output = model.generate(
                    input_ids=ids,
                    generation_config=generation_config,
                    return_dict_in_generate=False,
                    max_new_tokens=max_new_tokens,
                    do_sample=False,
                    num_beams=1,
                    num_return_sequences=1,
                    custom_generate=None,
                )
            generated = tuple(output[0, ids.shape[1] :].tolist())
            eos_ids = (generation_config or model.generation_config).eos_token_id
            eos_ids = (eos_ids,) if isinstance(eos_ids, int) else tuple(eos_ids or ())
            eos = generated[-1] if generated and generated[-1] in eos_ids else None
            body = generated[:-1] if eos is not None else generated
            return DecodeResult(
                tokenizer.decode(body, skip_special_tokens=False),
                body,
                eos,
                eos is None and len(generated) >= max_new_tokens,
                gpu_held_seconds=time.monotonic() - start
                if ids.device.type == "cuda"
                else 0.0,
            )

    return generate_once(session, new_messages, decoder, tools=tools, actuator=actuator)
