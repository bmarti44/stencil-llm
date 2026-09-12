"""Config for stencil-focus: a Qwen3 config plus the session-memory switches."""

from transformers.models.qwen3.configuration_qwen3 import Qwen3Config


class StencilFocusConfig(Qwen3Config):
    model_type = "stencil_focus"

    def __init__(
        self,
        stencil_focus: bool = True,
        focus_window: int = 3584,
        focus_budget: int = 256,
        **kwargs,
    ) -> None:
        self.stencil_focus = stencil_focus
        self.focus_window = focus_window
        self.focus_budget = focus_budget
        super().__init__(**kwargs)
