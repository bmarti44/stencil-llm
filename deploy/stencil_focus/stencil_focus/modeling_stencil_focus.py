"""stencil-focus: frozen Qwen3-1.7B trunk + inference-time session memory.

The learned weights are the unmodified base trunk. The modification is how the
conversation is turned into a prompt under a token budget (``focus_session``).
``stencil_focus=False`` disables it entirely: the prompt is the plain newest-token
window at the same budget and generation is ordinary greedy ``generate``.
"""

from __future__ import annotations

from transformers import AutoTokenizer
from transformers.models.qwen3.modeling_qwen3 import Qwen3ForCausalLM

from .configuration_stencil_focus import StencilFocusConfig
from .focus_session import Session, default_format


class StencilFocusForCausalLM(Qwen3ForCausalLM):
    config_class = StencilFocusConfig

    def __init__(self, config: StencilFocusConfig) -> None:
        super().__init__(config)
        self._focus_tokenizer = None

    # -- session interface ----------------------------------------------------
    @property
    def focus_tokenizer(self):
        if self._focus_tokenizer is None:
            self._focus_tokenizer = AutoTokenizer.from_pretrained(
                self.config._name_or_path
            )
        return self._focus_tokenizer

    def new_session(
        self,
        tokenizer=None,
        stencil_focus: bool | None = None,
        window: int | None = None,
        budget: int | None = None,
        format=default_format,
        instruction_roles=("user",),
    ) -> FocusSession:
        focus = self.config.stencil_focus if stencil_focus is None else stencil_focus
        return FocusSession(
            self,
            tokenizer or self.focus_tokenizer,
            focus=focus,
            window=window or self.config.focus_window,
            budget=budget or self.config.focus_budget,
            format=format,
            instruction_roles=instruction_roles,
        )


class FocusSession(Session):
    """A ``Session`` bound to a model: ``generate(request)`` = build + greedy."""

    def __init__(self, model, tokenizer, **kw) -> None:
        super().__init__(tokenizer, **kw)
        self.model = model

    def generate(
        self,
        request: str,
        head: str = "",
        separator: str = "\n\n",
        max_new_tokens: int = 512,
        **kw,
    ) -> str:
        import torch

        prompt = self.build_prompt(request, head=head, separator=separator)
        ids = torch.tensor([self.encode(prompt)], device=self.model.device)
        kw.setdefault("do_sample", False)
        kw.setdefault("eos_token_id", self.model.config.eos_token_id)
        with torch.no_grad():
            out = self.model.generate(
                ids,
                attention_mask=torch.ones_like(ids),
                max_new_tokens=max_new_tokens,
                **kw,
            )
        new = out[0, ids.shape[1] :].tolist()
        self.last["generated_token_ids"] = new
        return self.tokenizer.decode(new, skip_special_tokens=True)
