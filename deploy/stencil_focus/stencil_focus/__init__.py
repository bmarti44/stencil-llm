"""stencil-focus: Qwen3-1.7B with inference-time session memory under a token budget."""

from .configuration_stencil_focus import StencilFocusConfig
from .focus_session import Session, chat_prompt, pack_newest_first, render_reminder
from .modeling_stencil_focus import FocusSession, StencilFocusForCausalLM

__all__ = [
    "FocusSession",
    "Session",
    "StencilFocusConfig",
    "StencilFocusForCausalLM",
    "chat_prompt",
    "pack_newest_first",
    "render_reminder",
]
