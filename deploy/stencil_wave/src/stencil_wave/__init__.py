# ruff: noqa: E501
"""stencil_wave: Qwen3-1.7B with an instruction ledger and selective attention amplification."""
from .attention import WAVE_LAYERS, ColumnBias, StepBias, wave_attention
from .controller import WaveController
from .ledger import Entry, Ledger, build_ledger, render_text_ledger, select
from .model import MODEL_ID, REVISION, TMPL, Generation, WaveModel

__version__ = "0.1.0"
__all__ = ["WaveModel", "Generation", "Ledger", "Entry", "WaveController", "StepBias", "ColumnBias",
           "wave_attention", "build_ledger", "select", "render_text_ledger", "WAVE_LAYERS", "MODEL_ID",
           "REVISION", "TMPL", "__version__"]
